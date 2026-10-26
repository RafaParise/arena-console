/*
 * O servidor do ARENA no Android (item 14 do plano de 15/10/2026).
 *
 * No Windows, o ARENA.bat abre o servidor (servidor/arena.py) e o reabre se
 * ele cair (ate 3 vezes); no Linux, o ARENA.sh. No Android, quem faz isso e'
 * este servico, com o Python do APK (ferramentas/python_android.py):
 *
 *   1. na primeira vez (e quando o APK muda), tira do APK o Python
 *      (assets/arena-python, para files/python) e o programa do ARENA
 *      (assets/arena: servidor, launcher, guias, para files/arena);
 *   2. roda lib/<abi>/libarenapython.so (o lancador, android/python/lancador.c)
 *      com o servidor/android_inicio.py, que monta a pasta do ARENA e entrega
 *      a vez ao arena.py -- o mesmo servidor do Windows e do Linux;
 *   3. atende o que o servidor pede pelo fio (o stdout dele, uma linha JSON
 *      por pedido; a resposta vai pelo stdin): abrir o RetroArch com a linha
 *      de comando inteira (o remendo android/retroarch/arena-args.patch) e
 *      avisar quando o processo dele terminar, contar os controles, abrir
 *      uma pasta, trocar a pasta do ARENA, pedir a permissao de arquivos;
 *   4. grava o que o servidor escreve (o stderr dele) no registro do Android
 *      (o logcat, com a etiqueta ARENA-servidor).
 *
 * Fica "em primeiro plano" (com o aviso na barra do Android) enquanto o
 * ARENA esta aberto: sem isso, o Android poderia fechar o servidor no meio
 * de um jogo, quando a tela do ARENA vai para tras do RetroArch.
 */
package io.github.rafaparise.arena;

import android.app.ActivityManager;
import android.app.ApplicationExitInfo;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.content.res.AssetManager;
import android.net.wifi.WifiManager;
import android.opengl.EGL14;
import android.opengl.EGLConfig;
import android.opengl.EGLContext;
import android.opengl.EGLDisplay;
import android.opengl.EGLSurface;
import android.opengl.GLES20;
import android.os.Build;
import android.os.Environment;
import android.os.IBinder;
import android.provider.Settings;
import android.util.DisplayMetrics;
import android.util.Log;
import android.view.InputDevice;
import android.view.WindowManager;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.lang.ref.WeakReference;
import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import java.security.SecureRandom;
import java.security.cert.Certificate;
import java.security.cert.X509Certificate;
import java.util.Enumeration;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;

public class ArenaServico extends Service {
    static final String TAG = "ARENA";
    static final String TAG_DO_SERVIDOR = "ARENA-servidor";
    static final int PORTA = 8777;
    static final int AVISO = 1;
    // O ARENA.bat reabre o servidor que cai ate 3 vezes; aqui, o mesmo.
    static final int REABERTURAS = 3;

    // Quem esta olhando (a ArenaActivity da frente): recebe o "pronto" e o
    // "nao deu" do servidor. Fraca: a tela que sai nao fica presa aqui.
    static volatile WeakReference<ArenaActivity> tela = new WeakReference<ArenaActivity>(null);
    static volatile boolean pronto = false;
    static volatile boolean desistiu = false;
    static volatile ArenaServico atual;
    // O segredo da abertura do servidor: so a tela do ARENA o tem (um cookie
    // do WebView), e o servidor recusa o pedido local sem ele. No Android,
    // qualquer app do aparelho alcanca o 127.0.0.1 (servidor/ponte_android.py).
    // Um novo a cada abertura do servidor: o de um servidor que caiu nao vale
    // para o seguinte (revisao de seguranca de 18/10/2026).
    static volatile String segredo = "";

    static String sortearSegredo() {
        byte[] sorteado = new byte[32];
        new SecureRandom().nextBytes(sorteado);
        StringBuilder texto = new StringBuilder();
        for (byte b : sorteado) texto.append(String.format("%02x", b & 0xff));
        return texto.toString();
    }

    SharedPreferences guardado;
    Process servidor;
    Writer paraOServidor;
    volatile boolean saindo = false;
    volatile boolean reabrindo = false;
    int quedas = 0;
    WifiManager.MulticastLock rede;
    // As ultimas linhas do servidor, para a tela de erro e o teste.
    final ArrayDeque<String> ultimas = new ArrayDeque<String>();

    @Override
    public IBinder onBind(Intent pedido) {
        return null;
    }

    @Override
    public void onCreate() {
        super.onCreate();
        atual = this;
        guardado = getSharedPreferences("arena", Context.MODE_PRIVATE);
        ficarEmPrimeiroPlano();
        // O Jogar Junto acha os colegas por aviso na rede (UDP 55436): sem a
        // trava, o Wi-Fi do aparelho joga fora esses avisos para poupar bateria.
        try {
            WifiManager wifi = (WifiManager) getApplicationContext().getSystemService(Context.WIFI_SERVICE);
            if (wifi != null) {
                rede = wifi.createMulticastLock("ARENA");
                rede.setReferenceCounted(false);
                rede.acquire();
            }
        } catch (RuntimeException falha) {
            Log.w(TAG, "sem a trava da rede: " + falha);
        }
    }

    @Override
    public int onStartCommand(Intent pedido, int marcas, int numero) {
        if (servidor == null && !desistiu) {
            new Thread(new Runnable() {
                public void run() {
                    abrirOServidor(false);
                }
            }, "arena-servidor").start();
        }
        return START_NOT_STICKY;
    }

    @Override
    public void onTaskRemoved(Intent pedido) {
        // A pessoa fechou o ARENA (tirou da tela dos apps abertos).
        encerrar();
        stopSelf();
    }

    @Override
    public void onDestroy() {
        encerrar();
        if (rede != null && rede.isHeld()) rede.release();
        if (atual == this) atual = null;
        super.onDestroy();
    }

    void encerrar() {
        saindo = true;
        Process p = servidor;
        if (p != null) p.destroy();
        servidor = null;
        pronto = false;
    }

    void ficarEmPrimeiroPlano() {
        NotificationManager avisos = (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);
        Notification.Builder aviso;
        if (Build.VERSION.SDK_INT >= 26) {
            avisos.createNotificationChannel(new NotificationChannel("arena", "ARENA aberto",
                    NotificationManager.IMPORTANCE_LOW));
            aviso = new Notification.Builder(this, "arena");
        } else {
            aviso = new Notification.Builder(this);
        }
        Intent abrir = new Intent(this, ArenaActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        int tipo = Build.VERSION.SDK_INT >= 23 ? PendingIntent.FLAG_IMMUTABLE : 0;
        aviso.setContentTitle("ARENA aberto")
                .setContentText("Toque para voltar ao ARENA.")
                .setSmallIcon(getApplicationInfo().icon)
                .setOngoing(true)
                .setContentIntent(PendingIntent.getActivity(this, 0, abrir, tipo));
        startForeground(AVISO, aviso.build());
    }

    // ------------------------------------------------------------------
    // O Python e o programa do ARENA, de dentro do APK
    // ------------------------------------------------------------------

    long versaoDoApk() {
        try {
            return getPackageManager().getPackageInfo(getPackageName(), 0).lastUpdateTime;
        } catch (PackageManager.NameNotFoundException falha) {
            return 0;
        }
    }

    File casaDoPython() {
        return new File(getFilesDir(), "python");
    }

    File pastaDoArena() {
        return new File(getFilesDir(), "arena");
    }

    /** Tira o Python e o programa do APK, se este APK ainda nao tirou. O
     *  que e' de quem usa (os atalhos e a pasta retroarch do app) nao se mexe:
     *  saem so o servidor e o launcher antigos, que sao do APK. */
    void prepararOsArquivos() throws IOException {
        String desta = String.valueOf(versaoDoApk());
        if (desta.equals(guardado.getString("programa_do_apk", ""))
                && new File(pastaDoArena(), "servidor/android_inicio.py").isFile()
                && new File(casaDoPython(), "lib/python313.zip").isFile()) {
            return;
        }
        long inicio = System.currentTimeMillis();
        apagarDoApk(casaDoPython());
        apagarDoApk(new File(pastaDoArena(), "servidor"));
        apagarDoApk(new File(pastaDoArena(), "launcher"));
        copiarDoApk("arena-python", casaDoPython());
        copiarDoApk("arena", pastaDoArena());
        guardado.edit().putString("programa_do_apk", desta).apply();
        Log.i(TAG, "programa do ARENA tirado do APK em " + (System.currentTimeMillis() - inicio) + " ms");
    }

    /** Apaga uma pasta que veio do APK. Atalho (link) la dentro sai so o
     *  atalho: o que ele aponta nunca e' tocado. */
    static void apagarDoApk(File pasta) throws IOException {
        if (!pasta.exists()) return;
        File[] itens = pasta.listFiles();
        if (itens != null && pasta.getCanonicalPath().equals(pasta.getAbsolutePath())) {
            for (File item : itens) {
                boolean atalho = !item.getCanonicalPath().equals(new File(pasta.getCanonicalPath(), item.getName()).getPath());
                if (item.isDirectory() && !atalho) apagarDoApk(item);
                else item.delete();
            }
        }
        pasta.delete();
    }

    void copiarDoApk(String origem, File destino) throws IOException {
        AssetManager ativos = getAssets();
        String[] dentro = ativos.list(origem);
        if (dentro != null && dentro.length > 0) {
            destino.mkdirs();
            for (String nome : dentro) copiarDoApk(origem + "/" + nome, new File(destino, nome));
        } else {
            destino.getParentFile().mkdirs();
            ArenaActivity.copiar(ativos.open(origem), destino);
        }
    }

    // ------------------------------------------------------------------
    // O servidor: abrir, reabrir, ler o que ele escreve
    // ------------------------------------------------------------------

    void abrirOServidor(boolean reaberto) {
        segredo = sortearSegredo();
        try {
            prepararOsArquivos();
        } catch (IOException falha) {
            Log.e(TAG, "nao tirei o programa do APK: " + falha);
            desistir("O ARENA não conseguiu se preparar neste aparelho (" + falha.getMessage() + ").");
            return;
        }
        String lancador = new File(getApplicationInfo().nativeLibraryDir, "libarenapython.so").getPath();
        ProcessBuilder construtor = new ProcessBuilder(lancador,
                new File(pastaDoArena(), "servidor/android_inicio.py").getPath());
        construtor.directory(pastaDoArena());
        Map<String, String> ambiente = construtor.environment();
        ambiente.putAll(ambienteDoServidor());
        if (reaberto) ambiente.put("ARENA_REABERTO", "1");
        try {
            final Process p = construtor.start();
            servidor = p;
            paraOServidor = new OutputStreamWriter(p.getOutputStream(), StandardCharsets.UTF_8);
            new Thread(new Runnable() {
                public void run() {
                    lerOsPedidos(p);
                }
            }, "arena-pedidos").start();
            new Thread(new Runnable() {
                public void run() {
                    lerORegistro(p.getErrorStream());
                }
            }, "arena-registro").start();
            int codigo = p.waitFor();
            Log.w(TAG, "o servidor do ARENA terminou (" + codigo + ")");
        } catch (IOException | InterruptedException falha) {
            Log.e(TAG, "nao abri o servidor: " + falha);
        }
        servidor = null;
        semServidor();
        if (saindo) return;
        if (reabrindo) {
            reabrindo = false;
            abrirOServidor(true);
            return;
        }
        quedas++;
        if (quedas > REABERTURAS) {
            desistir("O servidor do ARENA caiu " + REABERTURAS + " vezes.");
            return;
        }
        abrirOServidor(true);
    }

    void desistir(String motivo) {
        desistiu = true;
        ArenaActivity quem = tela.get();
        if (quem != null) quem.servidorNaoAbriu(motivo, ultimasLinhas());
    }

    /** O servidor avisou pelo fio que ja escuta (o "pronto"). So este aviso
     *  vale: ele vem do proprio Python do ARENA, depois que ele abriu a
     *  porta. Conferir so a porta poderia achar outro app que a tomou antes,
     *  e a tela entregaria o segredo a ele. */
    /** O servidor caiu (ou vai reabrir): a tela para de falar com a porta e
     *  esquece o segredo ate o aviso "pronto" do proximo (ArenaActivity). */
    void semServidor() {
        pronto = false;
        ArenaActivity quem = tela.get();
        if (quem != null) quem.servidorFora();
    }

    void marcarPronto() {
        if (pronto) return;
        pronto = true;
        quedas = 0;
        ArenaActivity quem = tela.get();
        if (quem != null) quem.servidorPronto();
    }

    void lerORegistro(InputStream entrada) {
        try (BufferedReader leitor = new BufferedReader(new InputStreamReader(entrada, StandardCharsets.UTF_8))) {
            String linha;
            while ((linha = leitor.readLine()) != null) {
                Log.i(TAG_DO_SERVIDOR, linha);
                synchronized (ultimas) {
                    ultimas.addLast(linha);
                    while (ultimas.size() > 60) ultimas.removeFirst();
                }
            }
        } catch (IOException falha) {
            // o servidor fechou
        }
    }

    String ultimasLinhas() {
        StringBuilder texto = new StringBuilder();
        synchronized (ultimas) {
            for (String linha : ultimas) texto.append(linha).append('\n');
        }
        return texto.toString();
    }

    void lerOsPedidos(Process p) {
        try (BufferedReader leitor = new BufferedReader(new InputStreamReader(p.getInputStream(),
                StandardCharsets.UTF_8))) {
            String linha;
            while ((linha = leitor.readLine()) != null) {
                try {
                    final JSONObject pedido = new JSONObject(linha);
                    new Thread(new Runnable() {
                        public void run() {
                            atender(pedido);
                        }
                    }, "arena-pedido").start();
                } catch (JSONException falha) {
                    Log.w(TAG, "pedido do servidor que nao entendi: " + linha);
                }
            }
        } catch (IOException falha) {
            // o servidor fechou
        }
    }

    synchronized void responder(JSONObject resposta) {
        Writer fio = paraOServidor;
        if (fio == null) return;
        try {
            fio.write(resposta.toString() + "\n");
            fio.flush();
        } catch (IOException falha) {
            Log.w(TAG, "o servidor nao recebeu a resposta: " + falha);
        }
    }

    void responder(int numero, String chave, Object valor) {
        try {
            responder(new JSONObject().put("id", numero).put(chave, valor));
        } catch (JSONException falha) {
            Log.w(TAG, "resposta: " + falha);
        }
    }

    /** Fecha o servidor e abre de novo (a pasta do ARENA mudou, ou a
     *  permissao de arquivos). A tela de sempre se reconecta sozinha. */
    void reabrir() {
        reabrindo = true;
        semServidor();
        Process p = servidor;
        if (p != null) p.destroy();
    }

    // ------------------------------------------------------------------
    // Os pedidos do servidor (servidor/ponte_android.py)
    // ------------------------------------------------------------------

    void atender(JSONObject pedido) {
        int numero = pedido.optInt("id");
        String tipo = pedido.optString("pedido");
        try {
            if (tipo.equals("pronto")) {
                marcarPronto();
            } else if (tipo.equals("jogar")) {
                jogar(numero, pedido.getJSONArray("argumentos"));
            } else if (tipo.equals("fechar_jogo")) {
                fecharORetroArch();
            } else if (tipo.equals("controles")) {
                responder(numero, "quantos", contarControles());
            } else if (tipo.equals("teclado")) {
                responder(numero, "nome", tecladoFisico());
            } else if (tipo.equals("energia")) {
                responder(energia().put("id", numero));
            } else if (tipo.equals("aparelho")) {
                responder(aparelho().put("id", numero));
            } else if (tipo.equals("abrir_pasta")) {
                responder(numero, "ok", abrirAPasta(pedido.optString("caminho")));
            } else if (tipo.equals("escolher_pasta")) {
                guardado.edit().putString("pasta", pedido.optString("caminho")).apply();
                reabrir();
            } else if (tipo.equals("lembrar_pasta")) {
                // A pasta que o proprio servidor criou na primeira vez
                // (servidor/android_inicio.py): fica guardada, sem reabrir.
                guardado.edit().putString("pasta", pedido.optString("caminho")).apply();
            } else if (tipo.equals("permissao")) {
                ArenaActivity quem = tela.get();
                if (quem != null) quem.pedirPermissao(pedido.optBoolean("todos_os_arquivos"));
            } else if (tipo.equals("reabrir")) {
                reabrir();
            } else {
                Log.w(TAG, "pedido que nao conheco: " + tipo);
            }
        } catch (JSONException | RuntimeException falha) {
            Log.w(TAG, "pedido " + tipo + ": " + falha);
            responder(numero, "erro", String.valueOf(falha.getMessage()));
        }
    }

    // O RetroArch de dentro do APK roda no processo principal do app (o do
    // nome do pacote); ao sair do jogo ele encerra o proprio processo (o
    // exit(0) do platform_unix.c). E' assim que se sabe que o jogo fechou.
    static final String RETROARCH = "com.retroarch.browser.retroactivity.RetroActivityFuture";

    int processoDoRetroArch() {
        ActivityManager gerente = (ActivityManager) getSystemService(Context.ACTIVITY_SERVICE);
        List<ActivityManager.RunningAppProcessInfo> processos = gerente.getRunningAppProcesses();
        if (processos == null) return 0;
        for (ActivityManager.RunningAppProcessInfo p : processos) {
            if (getPackageName().equals(p.processName)) return p.pid;
        }
        return 0;
    }

    void fecharORetroArch() {
        int pid = processoDoRetroArch();
        if (pid > 0) android.os.Process.killProcess(pid);
    }

    void jogar(final int numero, JSONArray argumentos) throws JSONException {
        // Um RetroArch que ficou aberto (a pessoa saiu do jogo pelo botao de
        // inicio do aparelho) nao abriria o jogo novo: fecha antes.
        if (processoDoRetroArch() > 0) {
            fecharORetroArch();
            for (int i = 0; i < 20 && processoDoRetroArch() > 0; i++) dormir(150);
        }
        StringBuilder linha = new StringBuilder();
        for (int i = 0; i < argumentos.length(); i++) {
            String parte = argumentos.getString(i);
            if (parte.indexOf('\n') >= 0) {
                responder(numero, "erro", "Um caminho do jogo tem quebra de linha.");
                return;
            }
            if (i > 0) linha.append('\n');
            linha.append(parte);
        }
        Intent retro = new Intent();
        retro.setClassName(getPackageName(), RETROARCH);
        retro.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        retro.putExtra("ARGS", linha.toString());
        retro.putExtra("IME", Settings.Secure.getString(getContentResolver(), Settings.Secure.DEFAULT_INPUT_METHOD));
        retro.putExtra("DATADIR", getApplicationInfo().dataDir);
        retro.putExtra("APK", getApplicationInfo().sourceDir);
        retro.putExtra("SDCARD", Environment.getExternalStorageDirectory().getAbsolutePath());
        File externa = getExternalFilesDir(null);
        retro.putExtra("EXTERNAL", externa != null ? externa.getAbsolutePath() : getFilesDir().getAbsolutePath());
        ArenaActivity quem = tela.get();
        if (quem != null) quem.startActivity(retro);
        else startActivity(retro);
        int pid = 0;
        for (int i = 0; i < 80 && pid == 0; i++) {
            dormir(250);
            pid = processoDoRetroArch();
        }
        if (pid == 0) {
            responder(numero, "erro", "O RetroArch do ARENA não abriu neste aparelho.");
            return;
        }
        responder(numero, "pid", pid);
        while (processoDoRetroArch() == pid) dormir(1000);
        try {
            responder(new JSONObject().put("evento", "fim").put("id", numero).put("codigo", comoTerminou(pid)));
        } catch (JSONException falha) {
            Log.w(TAG, "fim do jogo: " + falha);
        }
    }

    /** O codigo do fim do RetroArch (0 = fechou do jeito normal), como o do
     *  processo no Windows: o Android 11 em diante conta como o processo
     *  terminou; antes dele, 0. */
    int comoTerminou(int pid) {
        if (Build.VERSION.SDK_INT < 30) return 0;
        ActivityManager gerente = (ActivityManager) getSystemService(Context.ACTIVITY_SERVICE);
        for (int i = 0; i < 6; i++) {
            List<ApplicationExitInfo> fins = gerente.getHistoricalProcessExitReasons(getPackageName(), pid, 1);
            if (fins != null && !fins.isEmpty()) {
                ApplicationExitInfo fim = fins.get(0);
                switch (fim.getReason()) {
                    case ApplicationExitInfo.REASON_EXIT_SELF:
                        return fim.getStatus();
                    case ApplicationExitInfo.REASON_SIGNALED:
                        return 128 + fim.getStatus();
                    case ApplicationExitInfo.REASON_CRASH_NATIVE:
                    case ApplicationExitInfo.REASON_CRASH:
                        return 139;
                    case ApplicationExitInfo.REASON_LOW_MEMORY:
                        return 137;
                    default:
                        return 0;
                }
            }
            dormir(200);
        }
        return 0;
    }

    static void dormir(long ms) {
        try {
            Thread.sleep(ms);
        } catch (InterruptedException falha) {
            Thread.currentThread().interrupt();
        }
    }

    /** A bateria e a economia de bateria (o painel do que deixa o jogo
     *  lento, servidor/barreiras.py). */
    JSONObject energia() throws JSONException {
        Intent bateria = registerReceiver(null, new android.content.IntentFilter(Intent.ACTION_BATTERY_CHANGED));
        int nivel = bateria != null ? bateria.getIntExtra(android.os.BatteryManager.EXTRA_LEVEL, -1) : -1;
        int escala = bateria != null ? bateria.getIntExtra(android.os.BatteryManager.EXTRA_SCALE, 100) : 100;
        int tomada = bateria != null ? bateria.getIntExtra(android.os.BatteryManager.EXTRA_PLUGGED, 0) : 0;
        boolean presente = bateria != null && bateria.getBooleanExtra(android.os.BatteryManager.EXTRA_PRESENT, false);
        android.os.PowerManager poder = (android.os.PowerManager) getSystemService(Context.POWER_SERVICE);
        JSONObject saida = new JSONObject();
        saida.put("tem_bateria", presente && nivel >= 0);
        saida.put("bateria_pct", nivel >= 0 && escala > 0 ? nivel * 100 / escala : JSONObject.NULL);
        saida.put("na_tomada", tomada != 0);
        saida.put("economia", poder != null && poder.isPowerSaveMode());
        // O calor do aparelho, como o proprio Android o ve: 0 normal, 1 leve, 2 moderado, 3 forte (ele segura o
        // processador), 4 ou mais, critico. So no Android 10 em diante.
        if (poder != null && Build.VERSION.SDK_INT >= 29) saida.put("termico", poder.getCurrentThermalStatus());
        return saida;
    }

    /** O hardware do aparelho, para o aluno conhecer o celular dele (Ajustes
     *  -> Maquina; pedido do Rafael de 23/10/2026: "mostrar o hardware completo
     *  do android para o aluno saber tudo do celular dele, ate os miliamperes
     *  da bateria [...] e se um dia trocar a bateria poder saber a capacidade
     *  dele"; e de 25/10/2026: "saude da bateria, miliamperes, quanto de energia
     *  esta gastando no momento, temperatura, memoria RAM em tempo real").
     *  So leitura: nada aqui muda o aparelho. O que nao muda (modelo, placa,
     *  sensores, capacidade de fabrica) e' lido uma vez e guardado; o que muda
     *  (bateria, memoria, calor, Wi-Fi, controles) e' lido a cada pedido: a tela
     *  pergunta de novo a cada poucos segundos enquanto o aluno olha. */
    JSONObject estatico = null;

    synchronized JSONObject aparelho() throws JSONException {
        if (estatico == null) estatico = aparelhoQueNaoMuda();
        JSONObject saida = new JSONObject(estatico.toString());
        JSONObject vivo = aoVivo();
        for (java.util.Iterator<String> chaves = vivo.keys(); chaves.hasNext();) {
            String chave = chaves.next();
            saida.put(chave, vivo.get(chave));
        }
        return saida;
    }

    JSONObject aparelhoQueNaoMuda() throws JSONException {
        JSONObject saida = new JSONObject();
        double deFabrica = capacidadeDeFabrica();
        if (deFabrica > 0) saida.put("bateria_capacidade_mah", Math.round(deFabrica));
        DisplayMetrics medidas = new DisplayMetrics();
        WindowManager janelas = (WindowManager) getSystemService(Context.WINDOW_SERVICE);
        janelas.getDefaultDisplay().getRealMetrics(medidas);
        saida.put("tela", medidas.widthPixels + "x" + medidas.heightPixels);
        saida.put("tela_dpi", medidas.densityDpi);
        if (medidas.xdpi > 0 && medidas.ydpi > 0) {
            double polegadas = Math.hypot(medidas.widthPixels / medidas.xdpi, medidas.heightPixels / medidas.ydpi);
            saida.put("tela_polegadas", Math.round(polegadas * 10) / 10.0);
        }
        saida.put("tela_hz", Math.round(janelas.getDefaultDisplay().getRefreshRate()));
        try {
            // Os modos de atualizacao que a tela aceita (60, 90, 120 Hz...), sem repetir.
            java.util.TreeSet<Long> modos = new java.util.TreeSet<Long>();
            for (android.view.Display.Mode modo : janelas.getDefaultDisplay().getSupportedModes()) {
                modos.add(Math.round((double) modo.getRefreshRate()));
            }
            JSONArray lista = new JSONArray();
            for (Long hz : modos) lista.put(hz);
            saida.put("tela_modos_hz", lista);
        } catch (RuntimeException falha) {
            Log.w(TAG, "modos da tela: " + falha);
        }
        saida.put("processador", processador());
        saida.put("hardware", Build.HARDWARE);
        saida.put("placa", Build.BOARD);
        saida.put("nucleos", Runtime.getRuntime().availableProcessors());
        JSONArray frequencias = new JSONArray();
        for (int i = 0; i < Runtime.getRuntime().availableProcessors(); i++) {
            frequencias.put(mhzDe("/sys/devices/system/cpu/cpu" + i + "/cpufreq/cpuinfo_max_freq"));
        }
        saida.put("nucleos_mhz", frequencias);
        saida.put("placa_de_video", placaDeVideo());
        saida.put("vulkan", getPackageManager().hasSystemFeature(PackageManager.FEATURE_VULKAN_HARDWARE_VERSION));
        try {
            for (android.content.pm.FeatureInfo recurso : getPackageManager().getSystemAvailableFeatures()) {
                if ("android.hardware.vulkan.version".equals(recurso.name)) {
                    int v = recurso.version;
                    saida.put("vulkan_versao", ((v >> 22) & 0x7f) + "." + ((v >> 12) & 0x3ff));
                }
            }
            ActivityManager atividades = (ActivityManager) getSystemService(Context.ACTIVITY_SERVICE);
            if (atividades != null) {
                saida.put("opengl_es", atividades.getDeviceConfigurationInfo().getGlEsVersion());
            }
        } catch (RuntimeException falha) {
            Log.w(TAG, "vulkan e opengl: " + falha);
        }
        saida.put("arquiteturas", new JSONArray(java.util.Arrays.asList(Build.SUPPORTED_ABIS)));
        saida.put("fabricante", Build.MANUFACTURER);
        saida.put("modelo", Build.MODEL);
        String nome = Settings.Global.getString(getContentResolver(), "device_name");
        saida.put("nome", nome == null ? "" : nome);
        saida.put("android", Build.VERSION.RELEASE);
        saida.put("android_sdk", Build.VERSION.SDK_INT);
        if (Build.VERSION.SDK_INT >= 23) saida.put("seguranca", Build.VERSION.SECURITY_PATCH);
        saida.put("versao_do_sistema", Build.DISPLAY);
        String nucleo = System.getProperty("os.version");
        if (nucleo != null) saida.put("kernel", nucleo);
        // O que o aparelho tem para jogar com controle (e para o celular virar controle).
        PackageManager pacotes = getPackageManager();
        JSONObject recursos = new JSONObject();
        recursos.put("usb_host", pacotes.hasSystemFeature("android.hardware.usb.host"));
        recursos.put("bluetooth", pacotes.hasSystemFeature(PackageManager.FEATURE_BLUETOOTH));
        recursos.put("bluetooth_le", pacotes.hasSystemFeature(PackageManager.FEATURE_BLUETOOTH_LE));
        recursos.put("giroscopio", pacotes.hasSystemFeature(PackageManager.FEATURE_SENSOR_GYROSCOPE));
        recursos.put("acelerometro", pacotes.hasSystemFeature(PackageManager.FEATURE_SENSOR_ACCELEROMETER));
        recursos.put("multitoque", pacotes.hasSystemFeature(PackageManager.FEATURE_TOUCHSCREEN_MULTITOUCH_DISTINCT));
        android.os.Vibrator vibrador = (android.os.Vibrator) getSystemService(Context.VIBRATOR_SERVICE);
        recursos.put("vibracao", vibrador != null && vibrador.hasVibrator());
        saida.put("recursos", recursos);
        return saida;
    }

    /** O que muda enquanto o aluno olha. Cada leitura que o aparelho nao da
     *  simplesmente fica de fora: nada aqui e' inventado. */
    JSONObject aoVivo() throws JSONException {
        JSONObject saida = energia();
        Intent bateria = registerReceiver(null, new android.content.IntentFilter(Intent.ACTION_BATTERY_CHANGED));
        if (bateria != null) {
            saida.put("bateria_estado", bateria.getIntExtra(android.os.BatteryManager.EXTRA_STATUS, 0));
            saida.put("tomada", bateria.getIntExtra(android.os.BatteryManager.EXTRA_PLUGGED, 0));
            saida.put("bateria_saude", bateria.getIntExtra(android.os.BatteryManager.EXTRA_HEALTH, 0));
            int temperatura = bateria.getIntExtra(android.os.BatteryManager.EXTRA_TEMPERATURE, Integer.MIN_VALUE);
            if (temperatura != Integer.MIN_VALUE) saida.put("bateria_temperatura_c", temperatura / 10.0);
            int voltagem = bateria.getIntExtra(android.os.BatteryManager.EXTRA_VOLTAGE, -1);
            if (voltagem > 0) saida.put("bateria_voltagem_mv", voltagem);
            String tecnologia = bateria.getStringExtra(android.os.BatteryManager.EXTRA_TECHNOLOGY);
            if (tecnologia != null) saida.put("bateria_tecnologia", tecnologia);
            if (Build.VERSION.SDK_INT >= 34) {
                int ciclos = bateria.getIntExtra(android.os.BatteryManager.EXTRA_CYCLE_COUNT, -1);
                if (ciclos >= 0) saida.put("bateria_ciclos", ciclos);
            }
        }
        android.os.BatteryManager gerente = (android.os.BatteryManager) getSystemService(Context.BATTERY_SERVICE);
        if (gerente != null) {
            // Corrente em microampere: o Android diz positivo para carregando e negativo para gastando, mas cada
            // fabricante faz do seu jeito. A tela usa o ESTADO (carregando ou nao), e nao o sinal.
            long corrente = gerente.getLongProperty(android.os.BatteryManager.BATTERY_PROPERTY_CURRENT_NOW);
            if (corrente != Long.MIN_VALUE) saida.put("corrente_ua", corrente);
            long media = gerente.getLongProperty(android.os.BatteryManager.BATTERY_PROPERTY_CURRENT_AVERAGE);
            if (media != Long.MIN_VALUE) saida.put("corrente_media_ua", media);
            // A carga de agora, em microampere-hora (o Android 5 em diante).
            int carga = gerente.getIntProperty(android.os.BatteryManager.BATTERY_PROPERTY_CHARGE_COUNTER);
            if (carga > 0 && carga != Integer.MIN_VALUE) saida.put("bateria_carga_mah", carga / 1000);
            if (Build.VERSION.SDK_INT >= 28) {
                long faltam = gerente.computeChargeTimeRemaining();
                if (faltam > 0) saida.put("falta_para_encher_s", faltam / 1000);
            }
            if (Build.VERSION.SDK_INT >= 34) {
                int saudePct = gerente.getIntProperty(10);          // BATTERY_PROPERTY_STATE_OF_HEALTH (a constante nao vem no android.jar publico)
                if (saudePct > 0 && saudePct != Integer.MIN_VALUE) saida.put("bateria_saude_pct", saudePct);
            }
        }
        ActivityManager.MemoryInfo memoria = new ActivityManager.MemoryInfo();
        ActivityManager atividades = (ActivityManager) getSystemService(Context.ACTIVITY_SERVICE);
        if (atividades != null) {
            atividades.getMemoryInfo(memoria);
            saida.put("memoria_total_mb", memoria.totalMem / 1048576L);
            saida.put("memoria_livre_mb", memoria.availMem / 1048576L);
            saida.put("memoria_baixa", memoria.lowMemory);
            saida.put("memoria_limite_mb", memoria.threshold / 1048576L);
        }
        long[] troca = memoriaVirtual();
        if (troca != null && troca[0] > 0) {
            saida.put("troca_total_mb", troca[0] / 1024);
            saida.put("troca_livre_mb", troca[1] / 1024);
        }
        try {
            android.os.StatFs disco = new android.os.StatFs(Environment.getExternalStorageDirectory().getPath());
            saida.put("armazenamento_total_mb", disco.getTotalBytes() / 1048576L);
            saida.put("armazenamento_livre_mb", disco.getAvailableBytes() / 1048576L);
        } catch (RuntimeException falha) {
            Log.w(TAG, "armazenamento: " + falha);
        }
        JSONArray agora = new JSONArray();
        for (int i = 0; i < Runtime.getRuntime().availableProcessors(); i++) {
            agora.put(mhzDe("/sys/devices/system/cpu/cpu" + i + "/cpufreq/scaling_cur_freq"));
        }
        saida.put("nucleos_agora_mhz", agora);
        android.os.PowerManager poder = (android.os.PowerManager) getSystemService(Context.POWER_SERVICE);
        if (poder != null && Build.VERSION.SDK_INT >= 30) {
            // A margem para esquentar: 1,0 = ja no limite em 10 s. NaN = o aparelho nao diz.
            float margem = poder.getThermalHeadroom(10);
            if (!Float.isNaN(margem)) saida.put("margem_termica", Math.round(margem * 100) / 100.0);
        }
        saida.put("ligado_ha_s", android.os.SystemClock.elapsedRealtime() / 1000L);
        try {
            WifiManager wifi = (WifiManager) getApplicationContext().getSystemService(Context.WIFI_SERVICE);
            if (wifi != null) saida.put("wifi_ligado", wifi.isWifiEnabled());
            if (wifi != null && wifi.isWifiEnabled()) {
                android.net.wifi.WifiInfo info = wifi.getConnectionInfo();
                if (info != null && info.getRssi() > -127 && info.getLinkSpeed() > 0) {
                    JSONObject w = new JSONObject();
                    w.put("sinal_dbm", info.getRssi());
                    w.put("velocidade_mbps", info.getLinkSpeed());
                    w.put("frequencia_mhz", info.getFrequency());
                    saida.put("wifi", w);
                }
            }
        } catch (RuntimeException falha) {
            Log.w(TAG, "wifi: " + falha);
        }
        saida.put("controles", controlesLigados());
        return saida;
    }

    /** Os controles de jogo e o teclado de verdade ligados agora, na ordem em
     *  que o RetroArch os poe nos jogadores (o primeiro ligado e' o jogador 1:
     *  o RetroArch do ARENA registra por numero de aparelho, do menor para o
     *  maior; ver docs/PLANO-CELULAR.md). */
    JSONArray controlesLigados() {
        JSONArray lista = new JSONArray();
        try {
            int[] ids = InputDevice.getDeviceIds();
            java.util.Arrays.sort(ids);
            int jogador = 0;
            for (int id : ids) {
                InputDevice d = InputDevice.getDevice(id);
                if (d == null || d.isVirtual()) continue;
                int fontes = d.getSources();
                boolean controle = (fontes & InputDevice.SOURCE_GAMEPAD) == InputDevice.SOURCE_GAMEPAD
                        || (fontes & InputDevice.SOURCE_JOYSTICK) == InputDevice.SOURCE_JOYSTICK;
                if (!controle) continue;
                jogador++;
                lista.put(new JSONObject().put("nome", String.valueOf(d.getName())).put("jogador", jogador));
            }
            // Os teclados de letras de verdade (com fio ou Bluetooth). O "Consumer Control" de um controle e' teclado,
            // mas nao de letras: fica de fora.
            for (int id : ids) {
                InputDevice d = InputDevice.getDevice(id);
                if (d == null || d.isVirtual()) continue;
                int fontes = d.getSources();
                boolean controle = (fontes & InputDevice.SOURCE_GAMEPAD) == InputDevice.SOURCE_GAMEPAD
                        || (fontes & InputDevice.SOURCE_JOYSTICK) == InputDevice.SOURCE_JOYSTICK;
                if (!controle && d.getKeyboardType() == InputDevice.KEYBOARD_TYPE_ALPHABETIC
                        && (fontes & InputDevice.SOURCE_KEYBOARD) == InputDevice.SOURCE_KEYBOARD) {
                    lista.put(new JSONObject().put("nome", String.valueOf(d.getName())).put("teclado", true));
                }
            }
        } catch (JSONException | RuntimeException falha) {
            Log.w(TAG, "controles: " + falha);
        }
        return lista;
    }

    /** {total, livre} da memoria virtual (o zRAM do Android), em kB, ou null. */
    static long[] memoriaVirtual() {
        long total = -1, livre = -1;
        try (BufferedReader leitor = new BufferedReader(new InputStreamReader(
                new java.io.FileInputStream("/proc/meminfo"), StandardCharsets.UTF_8))) {
            String linha;
            while ((linha = leitor.readLine()) != null) {
                if (linha.startsWith("SwapTotal:")) total = kbDe(linha);
                else if (linha.startsWith("SwapFree:")) livre = kbDe(linha);
            }
        } catch (IOException | RuntimeException falha) {
            return null;
        }
        return total >= 0 && livre >= 0 ? new long[]{total, livre} : null;
    }

    static long kbDe(String linha) {
        String[] partes = linha.trim().split("\\s+");
        return partes.length >= 2 ? Long.parseLong(partes[1]) : -1;
    }

    /** A frequencia de um arquivo do cpufreq (em kHz) em MHz; 0 se nao deu para ler (nucleo desligado). */
    static long mhzDe(String caminho) {
        String texto = lerLinha(caminho).trim();
        try {
            return texto.isEmpty() ? 0 : Long.parseLong(texto) / 1000;
        } catch (NumberFormatException falha) {
            return 0;
        }
    }

    /** A capacidade de fabrica da bateria, em mAh (a do power_profile.xml do
     *  aparelho, a mesma que o Android usa na tela de bateria), ou 0. */
    double capacidadeDeFabrica() {
        try {
            Class<?> perfil = Class.forName("com.android.internal.os.PowerProfile");
            Object objeto = perfil.getConstructor(Context.class).newInstance(this);
            Object capacidade = perfil.getMethod("getBatteryCapacity").invoke(objeto);
            return capacidade instanceof Double ? (Double) capacidade : 0;
        } catch (ReflectiveOperationException | RuntimeException falha) {
            Log.w(TAG, "capacidade da bateria: " + falha);
            return 0;
        }
    }

    static String lerLinha(String caminho) {
        try (BufferedReader leitor = new BufferedReader(new InputStreamReader(
                new java.io.FileInputStream(caminho), StandardCharsets.UTF_8))) {
            String linha = leitor.readLine();
            return linha == null ? "" : linha;
        } catch (IOException | RuntimeException falha) {
            return "";
        }
    }

    int contarControles() {
        int quantos = 0;
        for (int id : InputDevice.getDeviceIds()) {
            InputDevice d = InputDevice.getDevice(id);
            if (d == null || d.isVirtual()) continue;
            int fontes = d.getSources();
            if ((fontes & InputDevice.SOURCE_GAMEPAD) == InputDevice.SOURCE_GAMEPAD
                    || (fontes & InputDevice.SOURCE_JOYSTICK) == InputDevice.SOURCE_JOYSTICK) {
                quantos++;
            }
        }
        return quantos;
    }

    /** O nome do teclado de letras ligado que o RetroArch nao reconhece
     *  sozinho, ou "". O RetroArch do Android so trata como teclado, sozinho,
     *  o aparelho que se diz SO teclado (o teclado de PC comum). O que se diz
     *  teclado e mais alguma coisa (direcional, por exemplo) vira controle, e o
     *  F10, o Esc e o F2 do ARENA param de funcionar: o ARENA diz a ele qual e'
     *  o teclado (input_android_physical_keyboard; visto no emulador, cujo
     *  teclado "qwerty2" se diz teclado e direcional, em 21/10/2026). */
    String tecladoFisico() {
        for (int id : InputDevice.getDeviceIds()) {
            InputDevice d = InputDevice.getDevice(id);
            if (d == null || d.isVirtual()) continue;
            int fontes = d.getSources();
            if (d.getKeyboardType() != InputDevice.KEYBOARD_TYPE_ALPHABETIC
                    || (fontes & InputDevice.SOURCE_KEYBOARD) != InputDevice.SOURCE_KEYBOARD
                    || fontes == InputDevice.SOURCE_KEYBOARD
                    || (fontes & InputDevice.SOURCE_GAMEPAD) == InputDevice.SOURCE_GAMEPAD
                    || (fontes & InputDevice.SOURCE_JOYSTICK) == InputDevice.SOURCE_JOYSTICK) {
                continue;
            }
            String nome = d.getName();
            if (nome != null && !nome.isEmpty() && nome.indexOf('"') < 0 && nome.indexOf('\n') < 0) return nome;
        }
        return "";
    }

    /** Abre a pasta no gerenciador de arquivos do aparelho (o Arquivos do
     *  Android entende o endereco "document" da memoria e do cartao). */
    boolean abrirAPasta(String caminho) {
        try {
            String completo = new File(caminho).getCanonicalPath();
            String memoria = Environment.getExternalStorageDirectory().getCanonicalPath();
            String documento;
            if (completo.equals(memoria) || completo.startsWith(memoria + "/")) {
                documento = "primary:" + completo.substring(memoria.length()).replaceFirst("^/", "");
            } else if (completo.startsWith("/storage/")) {
                String resto = completo.substring("/storage/".length());
                int barra = resto.indexOf('/');
                documento = barra < 0 ? resto + ":" : resto.substring(0, barra) + ":" + resto.substring(barra + 1);
            } else {
                return false;
            }
            Intent ver = new Intent(Intent.ACTION_VIEW);
            ver.setDataAndType(android.provider.DocumentsContract.buildDocumentUri(
                    "com.android.externalstorage.documents", documento), "vnd.android.document/directory");
            ver.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_GRANT_READ_URI_PERMISSION);
            ArenaActivity quem = tela.get();
            if (quem != null) quem.startActivity(ver);
            else startActivity(ver);
            return true;
        } catch (IOException | RuntimeException falha) {
            Log.w(TAG, "abrir pasta: " + falha);
            return false;
        }
    }

    // ------------------------------------------------------------------
    // O que o servidor nao consegue saber sozinho (hardware.py)
    // ------------------------------------------------------------------

    Map<String, String> ambienteDoServidor() {
        Map<String, String> a = new java.util.HashMap<String, String>();
        String bibliotecas = getApplicationInfo().nativeLibraryDir;
        a.put("PYTHONHOME", casaDoPython().getPath());
        a.put("PYTHONUNBUFFERED", "1");
        a.put("PYTHONNOUSERSITE", "1");
        a.put("LD_LIBRARY_PATH", bibliotecas);
        a.put("HOME", getFilesDir().getPath());
        a.put("TMPDIR", getCacheDir().getPath());
        // Os certificados do proprio Android (as capas e a biblioteca livre
        // baixam por HTTPS), num arquivo so (certificados()).
        File certificados = certificados();
        if (certificados != null) a.put("SSL_CERT_FILE", certificados.getPath());
        a.put("ARENA_ANDROID_SEGREDO", segredo);
        a.put("ARENA_ANDROID_PERMISSAO", Build.VERSION.SDK_INT < 23 || checkSelfPermission(
                android.Manifest.permission.WRITE_EXTERNAL_STORAGE) == PackageManager.PERMISSION_GRANTED ? "1" : "0");
        String pasta = guardado.getString("pasta", "");
        a.put("ARENA_PASTA", pasta);
        a.put("ARENA_ANDROID_DADOS", new File(getFilesDir(), "arena-dados").getPath());
        a.put("ARENA_ANDROID_APK", getApplicationInfo().sourceDir);
        a.put("ARENA_ANDROID_ABI", abiDoApk());
        a.put("ARENA_ANDROID_CACHE", getCacheDir().getPath());
        a.put("ARENA_ANDROID_SISTEMA", "Android " + Build.VERSION.RELEASE + " (" + Build.MANUFACTURER + " "
                + Build.MODEL + ")");
        a.put("ARENA_ANDROID_PROCESSADOR", processador());
        a.put("ARENA_ANDROID_GPU", placaDeVideo());
        a.put("ARENA_ANDROID_VULKAN", getPackageManager().hasSystemFeature(
                PackageManager.FEATURE_VULKAN_HARDWARE_VERSION, 0x400003) ? "1" : "");
        a.put("ARENA_ANDROID_TELA", tela());
        a.put("ARENA_ANDROID_ID", codigoDoAparelho());
        StringBuilder raizes = new StringBuilder();
        for (File raiz : ArenaActivity.raizes(this)) raizes.append(raiz.getAbsolutePath()).append('\n');
        a.put("ARENA_ANDROID_RAIZES", raizes.toString());
        if (pasta.length() > 0) {
            try {
                a.put("ARENA_ANDROID_PASTA_REMOVIVEL", Environment.isExternalStorageRemovable(new File(pasta)) ? "1" : "0");
            } catch (IllegalArgumentException falha) {
                // pasta fora de um armazenamento conhecido
            }
        }
        return a;
    }

    /** Os certificados em que o Android confia, num arquivo PEM para o
     *  OpenSSL do Python. A pasta do sistema (/system/etc/security/cacerts)
     *  nao serve direto: os nomes dos arquivos la sao do jeito antigo do
     *  OpenSSL, e o OpenSSL 3 do Python nao os acha. Vao os do sistema e os
     *  que a pessoa (ou a escola) instalou no aparelho, como no Windows, que
     *  confia nos certificados instalados no computador. Feito a cada
     *  abertura do servico (leva uma fracao de segundo). */
    File certificados() {
        File arquivo = new File(getFilesDir(), "certificados.pem");
        try {
            KeyStore loja = KeyStore.getInstance("AndroidCAStore");
            loja.load(null, null);
            StringBuilder pem = new StringBuilder();
            for (Enumeration<String> nomes = loja.aliases(); nomes.hasMoreElements(); ) {
                Certificate c = loja.getCertificate(nomes.nextElement());
                if (!(c instanceof X509Certificate)) continue;
                pem.append("-----BEGIN CERTIFICATE-----\n")
                        .append(android.util.Base64.encodeToString(c.getEncoded(), android.util.Base64.DEFAULT))
                        .append("-----END CERTIFICATE-----\n");
            }
            ArenaActivity.copiar(new java.io.ByteArrayInputStream(pem.toString().getBytes(StandardCharsets.US_ASCII)),
                    arquivo);
            return arquivo;
        } catch (Exception falha) {
            Log.w(TAG, "sem os certificados do Android: " + falha);
            return arquivo.isFile() ? arquivo : null;
        }
    }

    String abiDoApk() {
        for (String abi : Build.SUPPORTED_ABIS) {
            try {
                String[] nomes = getAssets().list("arena-nucleos/" + abi);
                if (nomes != null && nomes.length > 0) return abi;
            } catch (IOException falha) {
                // segue
            }
        }
        return Build.SUPPORTED_ABIS.length > 0 ? Build.SUPPORTED_ABIS[0] : "";
    }

    static String processador() {
        if (Build.VERSION.SDK_INT >= 31 && !Build.SOC_MODEL.equals(Build.UNKNOWN)) {
            return (Build.SOC_MANUFACTURER + " " + Build.SOC_MODEL).trim();
        }
        return Build.HARDWARE;
    }

    String tela() {
        DisplayMetrics medidas = new DisplayMetrics();
        WindowManager janelas = (WindowManager) getSystemService(Context.WINDOW_SERVICE);
        janelas.getDefaultDisplay().getRealMetrics(medidas);
        return medidas.widthPixels + "x" + medidas.heightPixels;
    }

    String codigoDoAparelho() {
        // Sorteado na instalacao (nao e' nenhum numero do aparelho): sai junto
        // se o app for desinstalado.
        String codigo = guardado.getString("codigo", "");
        if (codigo.length() == 0) {
            codigo = UUID.randomUUID().toString();
            guardado.edit().putString("codigo", codigo).apply();
        }
        return codigo;
    }

    /** O nome da placa de video, como o OpenGL ES do aparelho diz ("Adreno
     *  (TM) 610"). Guardado por versao do APK: a placa nao muda. */
    String placaDeVideo() {
        String chave = "placa_" + versaoDoApk();
        String guardada = guardado.getString(chave, null);
        if (guardada != null) return guardada;
        String nome = "";
        EGLDisplay tela = EGL14.eglGetDisplay(EGL14.EGL_DEFAULT_DISPLAY);
        int[] versao = new int[2];
        if (tela != EGL14.EGL_NO_DISPLAY && EGL14.eglInitialize(tela, versao, 0, versao, 1)) {
            int[] pedido = {EGL14.EGL_RENDERABLE_TYPE, EGL14.EGL_OPENGL_ES2_BIT, EGL14.EGL_SURFACE_TYPE,
                    EGL14.EGL_PBUFFER_BIT, EGL14.EGL_NONE};
            EGLConfig[] configuracoes = new EGLConfig[1];
            int[] achadas = new int[1];
            if (EGL14.eglChooseConfig(tela, pedido, 0, configuracoes, 0, 1, achadas, 0) && achadas[0] > 0) {
                EGLContext contexto = EGL14.eglCreateContext(tela, configuracoes[0], EGL14.EGL_NO_CONTEXT,
                        new int[]{EGL14.EGL_CONTEXT_CLIENT_VERSION, 2, EGL14.EGL_NONE}, 0);
                EGLSurface superficie = EGL14.eglCreatePbufferSurface(tela, configuracoes[0],
                        new int[]{EGL14.EGL_WIDTH, 1, EGL14.EGL_HEIGHT, 1, EGL14.EGL_NONE}, 0);
                if (contexto != EGL14.EGL_NO_CONTEXT && superficie != EGL14.EGL_NO_SURFACE
                        && EGL14.eglMakeCurrent(tela, superficie, superficie, contexto)) {
                    String placa = GLES20.glGetString(GLES20.GL_RENDERER);
                    nome = placa != null ? placa : "";
                    EGL14.eglMakeCurrent(tela, EGL14.EGL_NO_SURFACE, EGL14.EGL_NO_SURFACE, EGL14.EGL_NO_CONTEXT);
                }
                if (superficie != EGL14.EGL_NO_SURFACE) EGL14.eglDestroySurface(tela, superficie);
                if (contexto != EGL14.EGL_NO_CONTEXT) EGL14.eglDestroyContext(tela, contexto);
            }
            EGL14.eglTerminate(tela);
        }
        guardado.edit().putString(chave, nome).apply();
        return nome;
    }
}
