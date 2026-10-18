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
import java.security.SecureRandom;
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
    // O segredo desta abertura: so a tela do ARENA o tem (um cookie do
    // WebView), e o servidor recusa o pedido local sem ele. No Android,
    // qualquer app do aparelho alcanca o 127.0.0.1 (servidor/ponte_android.py).
    static final String SEGREDO = sortearSegredo();

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
        pronto = false;
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
            } else if (tipo.equals("abrir_pasta")) {
                responder(numero, "ok", abrirAPasta(pedido.optString("caminho")));
            } else if (tipo.equals("escolher_pasta")) {
                guardado.edit().putString("pasta", pedido.optString("caminho")).apply();
                reabrir();
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
        // baixam por HTTPS): o OpenSSL do Python le a pasta do sistema.
        a.put("SSL_CERT_DIR", "/system/etc/security/cacerts");
        a.put("ARENA_ANDROID_SEGREDO", SEGREDO);
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
