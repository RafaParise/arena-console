/*
 * ARENA no Android (item 14 do plano de 15/10/2026).
 *
 * O APK do ARENA e' o RetroArch 1.22.2 oficial para Android (o mesmo RetroArch
 * do Windows, do Linux e do Chromebook) com esta tela na frente. Ela mostra a
 * tela de sempre do ARENA (launcher/index.html, o mesmo app.js) num WebView,
 * de um destes dois jeitos:
 *
 *   - o de sempre: o SERVIDOR do ARENA, o mesmo do Windows e do Linux, roda
 *     no aparelho (o ArenaServico, com o Python do APK), e a tela fala com
 *     ele em http://127.0.0.1:8777, como no computador. Tudo o que o ARENA
 *     faz vale aqui: o Jogar Junto, os amigos, os recordes, os cheats, as
 *     capas e a biblioteca da internet. So esta tela tem o segredo da
 *     abertura (um cookie): outro app do aparelho nao fala com o servidor;
 *   - o de reserva, se o servidor nao abrir neste aparelho: o "servidor
 *     dentro da pagina" do ARENA do Chromebook (launcher/navegador), com a
 *     ponte "ArenaAndroid" (a classe Ponte, abaixo) para o que so o Android
 *     faz: achar a pasta do ARENA no aparelho, listar e gravar arquivos dela
 *     e abrir o jogo no RetroArch NATIVO, com o nucleo certo (os nucleos vem
 *     dentro do APK e saem para a pasta do app na primeira vez que cada
 *     console abre).
 *
 * Os saves ficam na pasta do ARENA (retroarch/saves e retroarch/states), os
 * mesmos do Windows: o jogo salvo no celular continua salvo no computador.
 *
 * Esta tela roda num processo a parte (":tela", no AndroidManifest.xml): o
 * RetroArch pode fechar o processo dele ao sair do jogo, e a tela continua.
 *
 * Seguranca (revisao de 18/10/2026):
 *   - a pagina so vem de dentro do APK (https://arena.local/launcher/, que
 *     nao existe na internet: quem responde e' o shouldInterceptRequest
 *     daqui), a navegacao fica presa a ela, e link para fora abre no
 *     navegador do aparelho;
 *   - o arquivo da pasta do ARENA (a capa, o manifesto, o jogo) sai so como
 *     imagem ou dado, nunca como pagina ou script (nosniff e sandbox): um
 *     .html posto na pasta nao vira uma pagina com a ponte;
 *   - a ponte so atende quando a pagina da frente e' a tela do ARENA, so le
 *     e grava dentro da pasta do ARENA escolhida (e de tres pastas do app),
 *     so abre nucleo que veio no APK (pelo nome exato da lista dele) e tira
 *     da configuracao que a pagina manda as chaves de caminho e de plugin.
 */
package io.github.rafaparise.arena;

import android.Manifest;
import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.content.res.AssetManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.os.SystemClock;
import android.provider.Settings;
import android.util.Base64;
import android.util.Log;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.webkit.ConsoleMessage;
import android.webkit.CookieManager;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.lang.ref.WeakReference;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class ArenaActivity extends Activity {
    static final String CASA = "arena.local";
    static final String ENDERECO = "https://" + CASA + "/launcher/index.html?navegador=1&android=1";
    static final String TAG = "ARENA";
    static final int PEDIDO_DE_PERMISSAO = 7;
    static final int PERMISSAO_DA_ABERTURA = 8;
    static final int TODOS_OS_ARQUIVOS = 9;
    // O servidor do ARENA no aparelho (ArenaServico), como no computador.
    static final String SERVIDOR = "http://127.0.0.1:" + ArenaServico.PORTA + "/";
    // Enquanto o servidor abre (na primeira vez ele tira o programa do APK).
    static final String ABRINDO = "<!doctype html><html><head><meta name=viewport content='width=device-width'>"
            + "<style>body{margin:0;height:100vh;display:flex;align-items:center;justify-content:center;"
            + "background:#0b0f1a;color:#e8ecf5;font:20px sans-serif}</style></head>"
            + "<body>Abrindo o ARENA...</body></html>";
    // O RetroArch de dentro do APK (o mesmo codigo do RetroArch oficial).
    static final String RETROARCH = "com.retroarch.browser.retroactivity.RetroActivityFuture";

    // O nome de um nucleo do Android ("fceumm_libretro_android.so").
    static final Pattern NOME_DE_NUCLEO = Pattern.compile("[A-Za-z0-9_]+_libretro_android\\.so");
    // Uma linha do retroarch.cfg: chave = "valor".
    static final Pattern LINHA_CFG = Pattern.compile("^\\s*([a-z0-9_]+)\\s*=\\s*\"([^\"\\r\\n]*)\"\\s*$");
    // O que da pasta do ARENA a pagina pode ler, e com que tipo (o resto vai
    // como dado: nunca roda).
    static final Set<String> TIPOS_DA_PASTA = new HashSet<String>(Arrays.asList("png", "jpg", "jpeg", "gif", "webp",
            "json", "txt"));
    // As pastas do app onde a pagina pode gravar (o jogo livre que vem no APK,
    // o guardado no aparelho e a lista dos discos).
    static final String[] PASTAS_DO_APP = {"livres/", "guardados/", "listas/"};
    static final Map<String, String> TIPOS = new HashMap<String, String>();
    static {
        TIPOS.put("html", "text/html");
        TIPOS.put("js", "application/javascript");
        TIPOS.put("css", "text/css");
        TIPOS.put("json", "application/json");
        TIPOS.put("png", "image/png");
        TIPOS.put("jpg", "image/jpeg");
        TIPOS.put("jpeg", "image/jpeg");
        TIPOS.put("gif", "image/gif");
        TIPOS.put("webp", "image/webp");
        TIPOS.put("svg", "image/svg+xml");
        TIPOS.put("ico", "image/x-icon");
        TIPOS.put("woff2", "font/woff2");
        TIPOS.put("txt", "text/plain");
        TIPOS.put("md", "text/plain");
        TIPOS.put("wasm", "application/wasm");
    }

    WebView tela;
    SharedPreferences guardado;
    // A tela de reserva (o servidor nao abriu neste aparelho).
    volatile boolean modoNavegador = false;
    // A tela do servidor ja foi carregada (o servidor reaberto nao recarrega:
    // a pagina se reconecta sozinha, como no computador).
    boolean telaDoServidor = false;
    // O endereco da pagina da frente (o onPageStarted o atualiza): a ponte so
    // atende a tela do ARENA.
    volatile String paginaAtual = "";

    boolean paginaDoArena() {
        return paginaAtual.startsWith("https://" + CASA + "/launcher/");
    }

    @Override
    protected void onCreate(Bundle estado) {
        super.onCreate(estado);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        guardado = getSharedPreferences("arena", Context.MODE_PRIVATE);
        // O APK de teste (ferramentas/montar_android.py --teste) deixa o
        // teste ler o que a pagina escreve no console (chrome://inspect).
        WebView.setWebContentsDebuggingEnabled(existeNoApk("arena/android/depurar"));

        tela = new WebView(this);
        WebSettings ajustes = tela.getSettings();
        ajustes.setJavaScriptEnabled(true);
        ajustes.setDomStorageEnabled(true);
        ajustes.setDatabaseEnabled(true);
        ajustes.setMediaPlaybackRequiresUserGesture(false);
        ajustes.setAllowFileAccess(false);
        ajustes.setAllowContentAccess(false);
        ajustes.setUseWideViewPort(true);
        ajustes.setLoadWithOverviewMode(true);
        ajustes.setTextZoom(100);
        tela.setWebViewClient(new Cliente());
        tela.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onConsoleMessage(ConsoleMessage mensagem) {
                Log.i(TAG, mensagem.message() + " (" + mensagem.sourceId() + ":" + mensagem.lineNumber() + ")");
                return true;
            }
        });
        tela.addJavascriptInterface(new Ponte(), "ArenaAndroid");
        setContentView(tela);
        esconderAsBarras();
        ArenaServico.tela = new WeakReference<ArenaActivity>(this);
        if (ArenaServico.desistiu) {
            abrirModoNavegador();
        } else if (ArenaServico.pronto) {
            servidorPronto();
        } else {
            tela.loadDataWithBaseURL(null, ABRINDO, "text/html", "utf-8", null);
            // Na primeira abertura, a permissao de arquivos (para achar a
            // pasta do ARENA no aparelho); depois, so quando a pessoa pede.
            if (Build.VERSION.SDK_INT >= 23 && !temPermissao() && !guardado.getBoolean("pediu_permissao", false)) {
                guardado.edit().putBoolean("pediu_permissao", true).apply();
                requestPermissions(new String[]{Manifest.permission.READ_EXTERNAL_STORAGE,
                        Manifest.permission.WRITE_EXTERNAL_STORAGE}, PERMISSAO_DA_ABERTURA);
            } else {
                comecar();
            }
        }
    }

    /** Abre o servidor (o ArenaServico). Sem pasta escolhida e com uma pasta
     *  do ARENA so no aparelho, ela vale sozinha: baixar e ja usar. */
    void comecar() {
        if (guardado.getString("pasta", "").length() == 0 && temPermissao()) {
            List<File> achadas = new ArrayList<File>();
            for (File c : candidatas(this)) if (pareceArena(c)) achadas.add(c);
            if (achadas.size() == 1) guardado.edit().putString("pasta", achadas.get(0).getAbsolutePath()).apply();
        }
        Intent servico = new Intent(this, ArenaServico.class);
        if (Build.VERSION.SDK_INT >= 26) startForegroundService(servico);
        else startService(servico);
    }

    /** O servidor avisou que ja escuta (ArenaServico.marcarPronto): a tela
     *  ganha o segredo desta abertura e abre (ou recarrega) a pagina. */
    void servidorPronto() {
        runOnUiThread(new Runnable() {
            public void run() {
                if (modoNavegador || !ArenaServico.pronto) return;
                telaDoServidor = true;
                CookieManager biscoitos = CookieManager.getInstance();
                biscoitos.setAcceptCookie(true);
                biscoitos.setCookie(SERVIDOR, "arena_segredo=" + ArenaServico.segredo
                        + "; Path=/; HttpOnly; SameSite=Strict");
                biscoitos.flush();
                tela.loadUrl(SERVIDOR);
            }
        });
    }

    /** O servidor caiu ou vai reabrir: o segredo sai ja. Ate o proximo
     *  "pronto", nada da tela vai para a porta (shouldInterceptRequest):
     *  um app que a tomasse no intervalo nao recebe nada. */
    void servidorFora() {
        runOnUiThread(new Runnable() {
            public void run() {
                CookieManager.getInstance().removeAllCookies(null);
                CookieManager.getInstance().flush();
            }
        });
    }

    /** O servidor nao abriu neste aparelho: a tela de reserva, com o motivo
     *  no registro do Android. */
    void servidorNaoAbriu(final String motivo, final String ultimas) {
        Log.e(TAG, motivo + "\n" + ultimas);
        runOnUiThread(new Runnable() {
            public void run() {
                abrirModoNavegador();
            }
        });
    }

    void abrirModoNavegador() {
        modoNavegador = true;
        tela.loadUrl(ENDERECO);
    }

    /** O servidor pediu a permissao de arquivos (Ajustes, a pasta do ARENA).
     *  Com todosOsArquivos, a do Android 11 em diante que deixa gravar no
     *  cartao e no pen drive (a tela do sistema, "Acesso a todos os
     *  arquivos"). Na volta, o servidor abre de novo, enxergando a pasta. */
    void pedirPermissao(final boolean todosOsArquivos) {
        runOnUiThread(new Runnable() {
            public void run() {
                if (todosOsArquivos && Build.VERSION.SDK_INT >= 30) {
                    try {
                        startActivityForResult(new Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION,
                                Uri.parse("package:" + getPackageName())), TODOS_OS_ARQUIVOS);
                        return;
                    } catch (RuntimeException falha) {
                        Log.w(TAG, "sem a tela de todos os arquivos: " + falha);
                    }
                }
                if (Build.VERSION.SDK_INT >= 23) {
                    requestPermissions(new String[]{Manifest.permission.READ_EXTERNAL_STORAGE,
                            Manifest.permission.WRITE_EXTERNAL_STORAGE}, PEDIDO_DE_PERMISSAO);
                }
            }
        });
    }

    @Override
    protected void onActivityResult(int pedido, int resultado, Intent dados) {
        super.onActivityResult(pedido, resultado, dados);
        if (pedido == TODOS_OS_ARQUIVOS && ArenaServico.atual != null) ArenaServico.atual.reabrir();
    }

    @Override
    protected void onDestroy() {
        if (ArenaServico.tela.get() == this) ArenaServico.tela = new WeakReference<ArenaActivity>(null);
        super.onDestroy();
    }

    @Override
    protected void onResume() {
        super.onResume();
        esconderAsBarras();
        ArenaServico.tela = new WeakReference<ArenaActivity>(this);
        // Com o servidor, quem conta o tempo do jogo e' ele (como no computador).
        if (!modoNavegador) return;
        // Voltou do jogo: quanto tempo durou (o RetroArch roda noutro
        // processo; a hora de abrir fica guardada, para valer mesmo se esta
        // tela tiver sido refeita no meio).
        long inicio = guardado.getLong("inicio_do_jogo", 0);
        if (inicio > 0) {
            long segundos = Math.max(0, (SystemClock.elapsedRealtime() - inicio) / 1000);
            guardado.edit().remove("inicio_do_jogo").apply();
            if (segundos > 3 * 3600 || SystemClock.elapsedRealtime() < inicio) segundos = 0;   // o aparelho reiniciou
            avisarAPagina("window.ARENA_ANDROID_FIM && window.ARENA_ANDROID_FIM(" + segundos + ")");
        }
    }

    @Override
    public void onBackPressed() {
        if (modoNavegador) {
            avisarAPagina("window.ARENA_ANDROID_VOLTAR ? window.ARENA_ANDROID_VOLTAR() : 0");
            return;
        }
        // A tela fecha o que estiver aberto (uma janela, um ajuste); sem nada
        // aberto, o ARENA vai para tras, como o botao de inicio do aparelho.
        tela.evaluateJavascript("window.ARENA_ANDROID_VOLTAR ? String(window.ARENA_ANDROID_VOLTAR()) : 'nao'",
                new ValueCallback<String>() {
                    public void onReceiveValue(String resposta) {
                        if (!"\"sim\"".equals(resposta)) moveTaskToBack(true);
                    }
                });
    }

    void esconderAsBarras() {
        View decor = getWindow().getDecorView();
        decor.setSystemUiVisibility(View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY | View.SYSTEM_UI_FLAG_FULLSCREEN
                | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION | View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN);
    }

    void avisarAPagina(final String codigo) {
        runOnUiThread(new Runnable() {
            public void run() {
                if (tela != null) tela.evaluateJavascript(codigo, null);
            }
        });
    }

    @Override
    public void onRequestPermissionsResult(int pedido, String[] permissoes, int[] respostas) {
        if (pedido == PERMISSAO_DA_ABERTURA) {
            comecar();
        } else if (pedido == PEDIDO_DE_PERMISSAO) {
            if (modoNavegador) {
                avisarAPagina("window.ARENA_ANDROID_PERMISSAO && window.ARENA_ANDROID_PERMISSAO(" + temPermissao()
                        + ")");
            } else if (ArenaServico.atual != null) {
                ArenaServico.atual.reabrir();
            }
        }
    }

    boolean temPermissao() {
        return Build.VERSION.SDK_INT < 23
                || checkSelfPermission(Manifest.permission.WRITE_EXTERNAL_STORAGE) == PackageManager.PERMISSION_GRANTED;
    }

    // ------------------------------------------------------------------
    // A pagina (de dentro do APK) e a pasta do ARENA
    // ------------------------------------------------------------------

    boolean existeNoApk(String caminho) {
        try {
            getAssets().open(caminho).close();
            return true;
        } catch (IOException falha) {
            return false;
        }
    }

    static String tipoDe(String caminho) {
        int ponto = caminho.lastIndexOf('.');
        String extensao = ponto < 0 ? "" : caminho.substring(ponto + 1).toLowerCase(Locale.ROOT);
        String tipo = TIPOS.get(extensao);
        return tipo != null ? tipo : "application/octet-stream";
    }

    static WebResourceResponse resposta(String tipo, InputStream dados, int codigo) {
        return resposta(tipo, dados, codigo, false);
    }

    static WebResourceResponse resposta(String tipo, InputStream dados, int codigo, boolean daPasta) {
        WebResourceResponse r = new WebResourceResponse(tipo, "utf-8", dados);
        Map<String, String> cabecalhos = new HashMap<String, String>();
        cabecalhos.put("Cache-Control", "no-store");
        cabecalhos.put("X-Content-Type-Options", "nosniff");
        if (daPasta) cabecalhos.put("Content-Security-Policy", "sandbox; default-src 'none'");
        try {
            r.setStatusCodeAndReasonPhrase(codigo, codigo == 200 ? "OK"
                    : codigo == 503 ? "Service Unavailable" : "Not Found");
        } catch (IllegalArgumentException falha) {
            // codigo invalido: fica o padrao
        }
        r.setResponseHeaders(cabecalhos);
        return r;
    }

    class Cliente extends WebViewClient {
        @Override
        public void onPageStarted(WebView vista, String endereco, android.graphics.Bitmap icone) {
            paginaAtual = endereco == null ? "" : endereco;
        }

        @Override
        public WebResourceResponse shouldInterceptRequest(WebView vista, WebResourceRequest pedido) {
            Uri endereco = pedido.getUrl();
            if (!modoNavegador && endereco.toString().startsWith(SERVIDOR) && !ArenaServico.pronto) {
                // O servidor do ARENA ainda nao avisou que abriu: nada vai
                // para a porta (outro app pode estar nela); a tela espera.
                return resposta("text/html", new java.io.ByteArrayInputStream(
                        ABRINDO.getBytes(java.nio.charset.StandardCharsets.UTF_8)), 503);
            }
            if (!CASA.equals(endereco.getHost())) return null;          // capa da internet: segue normal
            String caminho = endereco.getPath() == null ? "/" : endereco.getPath();
            if (caminho.contains("..")) return resposta("text/plain", null, 404);
            String relativo = caminho.replaceFirst("^/+", "");
            // 1. a tela e o servidor da pagina, de dentro do APK
            try {
                return resposta(tipoDe(relativo), getAssets().open("arena/" + relativo), 200);
            } catch (IOException falha) {
                // nao e' do APK: pode ser da pasta do ARENA (capa, manifesto)
            }
            // 2. a pasta do ARENA escolhida (as capas em retroarch/thumbnails,
            //    o dados/manifesto.json, os jogos que a pagina le): so como
            //    imagem ou dado, e nunca como a pagina da frente.
            File arquivo = pedido.isForMainFrame() ? null : dentroDaPasta(relativo);
            if (arquivo != null && arquivo.isFile()) {
                int ponto = relativo.lastIndexOf('.');
                String extensao = ponto < 0 ? "" : relativo.substring(ponto + 1).toLowerCase(Locale.ROOT);
                String tipo = TIPOS_DA_PASTA.contains(extensao) ? tipoDe(relativo) : "application/octet-stream";
                try {
                    return resposta(tipo, new FileInputStream(arquivo), 200, true);
                } catch (IOException falha) {
                    Log.w(TAG, "nao li " + arquivo + ": " + falha);
                }
            }
            return resposta("text/plain", null, 404);
        }

        @Override
        public boolean shouldOverrideUrlLoading(WebView vista, WebResourceRequest pedido) {
            Uri endereco = pedido.getUrl();
            if (!modoNavegador && endereco.toString().startsWith(SERVIDOR)) {
                return false;                                    // a tela do servidor do ARENA
            }
            if (CASA.equals(endereco.getHost())) {
                // So a tela do ARENA abre aqui (a ponte e' dela).
                String caminho = endereco.getPath() == null ? "" : endereco.getPath();
                return !caminho.startsWith("/launcher/");
            }
            // Link para fora: no navegador do aparelho, nunca nesta tela
            // (a ponte so vale para a pagina do ARENA).
            try {
                startActivity(new Intent(Intent.ACTION_VIEW, endereco));
            } catch (RuntimeException falha) {
                Log.w(TAG, "sem navegador para " + endereco);
            }
            return true;
        }
    }

    /** A pasta do ARENA escolhida (guardada), ou null. */
    File pastaDoArena() {
        String caminho = guardado.getString("pasta", "");
        if (caminho.length() == 0) return null;
        File pasta = new File(caminho);
        return pasta.isDirectory() ? pasta : null;
    }

    /** O arquivo 'relativo' dentro da pasta do ARENA (sem sair dela), ou null. */
    File dentroDaPasta(String relativo) {
        File pasta = pastaDoArena();
        if (pasta == null) return null;
        try {
            File alvo = new File(pasta, relativo).getCanonicalFile();
            String base = pasta.getCanonicalPath() + File.separator;
            return alvo.getPath().startsWith(base) ? alvo : null;
        } catch (IOException falha) {
            return null;
        }
    }

    /** O caminho pode ser lido e gravado pela pagina? Dentro da pasta do
     *  ARENA ou da pasta do proprio app. */
    boolean permitido(File alvo) {
        try {
            String caminho = alvo.getCanonicalPath();
            List<String> bases = new ArrayList<String>();
            File pasta = pastaDoArena();
            if (pasta != null) bases.add(pasta.getCanonicalPath());
            bases.add(getFilesDir().getCanonicalPath());
            for (String base : bases) {
                if (caminho.equals(base) || caminho.startsWith(base + File.separator)) return true;
            }
        } catch (IOException falha) {
            return false;
        }
        return false;
    }

    /** As raizes de armazenamento: a memoria interna e cada cartao SD ou
     *  pen drive (do getExternalFilesDirs, cortando o "/Android/data/..."). */
    List<File> raizes() {
        return raizes(this);
    }

    static List<File> raizes(Context contexto) {
        List<File> lista = new ArrayList<File>();
        lista.add(Environment.getExternalStorageDirectory());
        File[] doApp = contexto.getExternalFilesDirs(null);
        for (File pasta : doApp) {
            if (pasta == null) continue;
            String caminho = pasta.getAbsolutePath();
            int corte = caminho.indexOf("/Android/");
            if (corte > 0) {
                File raiz = new File(caminho.substring(0, corte));
                if (!lista.contains(raiz)) lista.add(raiz);
            }
        }
        return lista;
    }

    /** Onde uma pasta do ARENA pode estar: cada raiz e as pastas ate dois
     *  niveis dentro dela (DCIM/ARENA, Download/ARENA...). */
    static List<File> candidatas(Context contexto) {
        List<File> candidatas = new ArrayList<File>();
        for (File raiz : raizes(contexto)) {
            candidatas.add(raiz);
            File[] dentro = raiz.listFiles();
            if (dentro == null) continue;
            for (File f : dentro) {
                if (f.isDirectory() && !f.getName().startsWith(".") && !f.getName().equals("Android")) {
                    candidatas.add(f);
                    File[] netos = f.listFiles();
                    if (netos != null) for (File n : netos) if (n.isDirectory()) candidatas.add(n);
                }
            }
        }
        return candidatas;
    }

    static File filhoSemMaiusculas(File pasta, String nome) {
        String[] nomes = pasta.list();
        if (nomes == null) return null;
        for (String n : nomes) {
            if (n.equalsIgnoreCase(nome)) return new File(pasta, n);
        }
        return null;
    }

    static boolean pareceArena(File pasta) {
        return pasta != null && pasta.isDirectory() && filhoSemMaiusculas(pasta, "jogos") != null
                && (filhoSemMaiusculas(pasta, "launcher") != null || filhoSemMaiusculas(pasta, "ARENA-CHROMEBOOK.html") != null
                    || filhoSemMaiusculas(pasta, "retroarch") != null);
    }

    // ------------------------------------------------------------------
    // Os nucleos e as BIOS livres (de dentro do APK)
    // ------------------------------------------------------------------

    String abiDoApk() {
        AssetManager ativos = getAssets();
        for (String abi : Build.SUPPORTED_ABIS) {
            try {
                String[] nomes = ativos.list("arena-nucleos/" + abi);
                if (nomes != null && nomes.length > 0) return abi;
            } catch (IOException falha) {
                // segue
            }
        }
        return "";
    }

    static void copiar(InputStream de, File para) throws IOException {
        File parcial = new File(para.getPath() + ".parcial");
        OutputStream saida = new FileOutputStream(parcial);
        try {
            byte[] bloco = new byte[1 << 16];
            int lidos;
            while ((lidos = de.read(bloco)) > 0) saida.write(bloco, 0, lidos);
        } finally {
            saida.close();
            de.close();
        }
        if (!parcial.renameTo(para)) {
            parcial.delete();
            throw new IOException("nao consegui gravar " + para);
        }
    }

    /** A hora em que este APK foi instalado (ou atualizado). */
    long instalacao() {
        try {
            return getPackageManager().getPackageInfo(getPackageName(), 0).lastUpdateTime;
        } catch (PackageManager.NameNotFoundException falha) {
            return 0;
        }
    }

    static String lerTexto(File arquivo) {
        try {
            InputStream entrada = new FileInputStream(arquivo);
            try {
                byte[] dados = new byte[(int) Math.min(arquivo.length(), 4096)];
                int lidos = entrada.read(dados);
                return lidos > 0 ? new String(dados, 0, lidos, "UTF-8") : "";
            } finally {
                entrada.close();
            }
        } catch (IOException falha) {
            return "";
        }
    }

    /** O nucleo, na pasta de nucleos do app (de onde o RetroArch carrega).
     *  So o que veio no APK, pelo nome exato da lista dele; o ja tirado do
     *  APK vale so se foi tirado desta instalacao (a marca ao lado). */
    File nucleo(String nome) throws IOException {
        String abi = abiDoApk();
        String[] doApk = getAssets().list("arena-nucleos/" + abi);
        if (!NOME_DE_NUCLEO.matcher(nome).matches() || doApk == null || !Arrays.asList(doApk).contains(nome)) {
            throw new IOException("Este console nao tem nucleo neste APK.");
        }
        File pasta = new File(getApplicationInfo().dataDir, "cores");
        pasta.mkdirs();
        File destino = new File(pasta, nome);
        if (!destino.getCanonicalPath().equals(new File(pasta.getCanonicalPath(), nome).getPath())) {
            throw new IOException("Nome de nucleo invalido.");
        }
        File marca = new File(pasta, nome + ".arena");
        String desta = String.valueOf(instalacao());
        if (destino.isFile() && marca.isFile() && desta.equals(lerTexto(marca))) return destino;
        copiar(getAssets().open("arena-nucleos/" + abi + "/" + nome), destino);
        gravarTexto(marca, desta);
        return destino;
    }

    /** A configuracao que a pagina manda, so com o que e' ajuste: sem as
     *  chaves de caminho (as pastas quem diz e' o ARENA, abaixo) e sem as de
     *  plugin ou filtro (carregariam programa de fora). */
    static String semCaminhos(String texto) {
        StringBuilder saida = new StringBuilder();
        for (String linha : texto.split("\n")) {
            Matcher m = LINHA_CFG.matcher(linha);
            if (!m.matches()) continue;
            String chave = m.group(1);
            if (chave.endsWith("_directory") || chave.endsWith("_path") || chave.endsWith("_dir")
                    || chave.endsWith("_plugin") || chave.endsWith("_filter") || chave.startsWith("libretro_")
                    || chave.startsWith("network_cmd") || chave.equals("video_shader")) {
                continue;
            }
            saida.append(linha(chave, m.group(2)));
        }
        return saida.toString();
    }

    /** Poe as BIOS livres (as do ARENA, de licenca livre) na pasta system,
     *  so as que faltam: nunca troca a que ja esta la, salvo a copia antiga
     *  de um arquivo livre que mudou (igual ao bios.instalar_livres). */
    void biosLivres(File sistema) {
        try {
            String[] nomes = getAssets().list("arena-bios");
            if (nomes == null) return;
            Map<String, Set<String>> antigas = biosAntigas();
            for (String nome : nomes) copiarArvore("arena-bios/" + nome, new File(sistema, nome), antigas);
        } catch (IOException falha) {
            Log.w(TAG, "BIOS livres: " + falha);
        }
    }

    /** {caminho em arena-bios: marcas SHA-256 das copias antigas}. Vem da
     *  lista.json ("sha256_antigos"), que o montar_android.py poe em
     *  arena-bios-antigas.txt: caminho, tab e marca, uma por linha. Exemplo:
     *  o config.ini do C-BIOS com "\" (o blueMSX do Android nao achava as
     *  ROMs; trocado por "/" em 21/10/2026). */
    Map<String, Set<String>> biosAntigas() {
        Map<String, Set<String>> antigas = new HashMap<>();
        try (java.io.BufferedReader texto = new java.io.BufferedReader(new java.io.InputStreamReader(
                getAssets().open("arena-bios-antigas.txt"), "UTF-8"))) {
            String linha;
            while ((linha = texto.readLine()) != null) {
                String[] partes = linha.split("\t");
                if (partes.length != 2) continue;
                String caminho = "arena-bios/" + partes[0];
                if (!antigas.containsKey(caminho)) antigas.put(caminho, new HashSet<String>());
                antigas.get(caminho).add(partes[1].trim().toLowerCase(Locale.ROOT));
            }
        } catch (IOException falha) {
            // APK sem a lista: nada a trocar
        }
        return antigas;
    }

    void copiarArvore(String origem, File destino, Map<String, Set<String>> antigas) throws IOException {
        String[] dentro = getAssets().list(origem);
        if (dentro != null && dentro.length > 0) {
            destino.mkdirs();
            for (String nome : dentro) copiarArvore(origem + "/" + nome, new File(destino, nome), antigas);
        } else if (!destino.exists() || copiaAntiga(destino, antigas.get(origem))) {
            destino.getParentFile().mkdirs();
            copiar(getAssets().open(origem), destino);
        }
    }

    /** O arquivo tem a marca de uma copia antiga (e' do ARENA: pode trocar)? */
    static boolean copiaAntiga(File arquivo, Set<String> marcas) {
        if (marcas == null || !arquivo.isFile()) return false;
        try (InputStream entrada = new FileInputStream(arquivo)) {
            java.security.MessageDigest resumo = java.security.MessageDigest.getInstance("SHA-256");
            byte[] bloco = new byte[1 << 16];
            int lidos;
            while ((lidos = entrada.read(bloco)) > 0) resumo.update(bloco, 0, lidos);
            StringBuilder marca = new StringBuilder();
            for (byte b : resumo.digest()) marca.append(String.format(Locale.ROOT, "%02x", b));
            return marcas.contains(marca.toString());
        } catch (IOException | java.security.NoSuchAlgorithmException falha) {
            return false;
        }
    }

    static String linha(String chave, String valor) {
        return chave + " = \"" + valor.replace("\"", "'") + "\"\n";
    }

    static void gravarTexto(File arquivo, String texto) throws IOException {
        arquivo.getParentFile().mkdirs();
        copiar(new java.io.ByteArrayInputStream(texto.getBytes("UTF-8")), arquivo);
    }

    /** Abre o jogo no RetroArch (o pedido vem da pagina, rotas.js). */
    void abrirJogo(JSONObject pedido) throws IOException, JSONException {
        File rom = new File(pedido.getString("rom"));
        if (!rom.isFile() || !permitido(rom)) throw new IOException("O arquivo do jogo nao esta mais no lugar.");
        File nucleo = nucleo(pedido.getString("nucleo"));
        File pasta = pastaDoArena();
        File base = pasta != null ? new File(pasta, "retroarch") : getFilesDir();
        File sistema = new File(base, "system");
        File saves = new File(base, "saves");
        File estados = new File(base, "states");
        File fotos = new File(base, "screenshots");
        for (File f : new File[]{sistema, saves, estados, fotos}) f.mkdirs();
        biosLivres(sistema);

        File opcoes = new File(getFilesDir(), "arena-opcoes-do-nucleo.opt");
        gravarTexto(opcoes, semCaminhos(pedido.optString("opcoes", "")));
        StringBuilder cfg = new StringBuilder(semCaminhos(pedido.optString("configuracao", "")));
        cfg.append(linha("savefile_directory", saves.getPath()));
        cfg.append(linha("savestate_directory", estados.getPath()));
        cfg.append(linha("system_directory", sistema.getPath()));
        cfg.append(linha("screenshot_directory", fotos.getPath()));
        cfg.append(linha("libretro_directory", nucleo.getParent()));
        cfg.append(linha("core_options_path", opcoes.getPath()));
        cfg.append(linha("global_core_options", "true"));
        cfg.append(linha("config_save_on_exit", "false"));
        cfg.append(linha("network_cmd_enable", "false"));
        File arquivoCfg = new File(getFilesDir(), "arena-partida.cfg");
        gravarTexto(arquivoCfg, cfg.toString());

        Intent retro = new Intent();
        retro.setClassName(getPackageName(), RETROARCH);
        retro.putExtra("ROM", rom.getPath());
        retro.putExtra("LIBRETRO", nucleo.getPath());
        retro.putExtra("CONFIGFILE", arquivoCfg.getPath());
        retro.putExtra("IME", Settings.Secure.getString(getContentResolver(), Settings.Secure.DEFAULT_INPUT_METHOD));
        retro.putExtra("DATADIR", getApplicationInfo().dataDir);
        retro.putExtra("APK", getApplicationInfo().sourceDir);
        File externa = getExternalFilesDir(null);
        retro.putExtra("SDCARD", Environment.getExternalStorageDirectory().getAbsolutePath());
        retro.putExtra("EXTERNAL", externa != null ? externa.getAbsolutePath() : getFilesDir().getAbsolutePath());
        guardado.edit().putLong("inicio_do_jogo", SystemClock.elapsedRealtime()).apply();
        startActivity(retro);
    }

    // ------------------------------------------------------------------
    // A ponte: o que a pagina (launcher/navegador/android.js) chama
    // ------------------------------------------------------------------

    class Ponte {
        @JavascriptInterface
        public String sistema() {
            if (!paginaDoArena()) return "{}";
            JSONObject saida = new JSONObject();
            try {
                saida.put("android", Build.VERSION.RELEASE);
                saida.put("sdk", Build.VERSION.SDK_INT);
                saida.put("abi", abiDoApk());
                saida.put("modelo", Build.MANUFACTURER + " " + Build.MODEL);
                saida.put("permissao", temPermissao());
                JSONArray nucleos = new JSONArray();
                String[] nomes = getAssets().list("arena-nucleos/" + abiDoApk());
                if (nomes != null) for (String nome : nomes) nucleos.put(nome);
                saida.put("nucleos", nucleos);
                File pasta = pastaDoArena();
                saida.put("pasta", pasta != null ? pasta.getPath() : "");
            } catch (JSONException | IOException falha) {
                Log.w(TAG, "sistema: " + falha);
            }
            return saida.toString();
        }

        @JavascriptInterface
        public boolean temPermissao() {
            if (!paginaDoArena()) return false;
            return ArenaActivity.this.temPermissao();
        }

        @JavascriptInterface
        public void pedirPermissao() {
            if (!paginaDoArena()) return;
            runOnUiThread(new Runnable() {
                public void run() {
                    if (Build.VERSION.SDK_INT >= 23) {
                        requestPermissions(new String[]{Manifest.permission.READ_EXTERNAL_STORAGE,
                                Manifest.permission.WRITE_EXTERNAL_STORAGE}, PEDIDO_DE_PERMISSAO);
                    }
                }
            });
        }

        /** As pastas do ARENA achadas no aparelho: [{caminho, nome}]. */
        @JavascriptInterface
        public String pastasDoArena() {
            if (!paginaDoArena()) return "[]";
            JSONArray saida = new JSONArray();
            for (File raiz : raizes()) {
                List<File> candidatas = new ArrayList<File>();
                candidatas.add(raiz);
                File[] dentro = raiz.listFiles();
                if (dentro != null) {
                    for (File f : dentro) {
                        if (f.isDirectory() && !f.getName().startsWith(".") && !f.getName().equals("Android")) {
                            candidatas.add(f);
                            File[] netos = f.listFiles();
                            if (netos != null) for (File n : netos) if (n.isDirectory()) candidatas.add(n);
                        }
                    }
                }
                for (File c : candidatas) {
                    if (pareceArena(c)) {
                        try {
                            JSONObject item = new JSONObject();
                            item.put("caminho", c.getAbsolutePath());
                            item.put("nome", c.getName() + (raiz.equals(Environment.getExternalStorageDirectory())
                                    ? " (memória do aparelho)" : " (cartão ou pen drive)"));
                            saida.put(item);
                        } catch (JSONException falha) {
                            Log.w(TAG, "pastas: " + falha);
                        }
                    }
                }
            }
            return saida.toString();
        }

        @JavascriptInterface
        public boolean escolherPasta(String caminho) {
            if (!paginaDoArena()) return false;
            File pasta = new File(caminho);
            if (!pareceArena(pasta)) return false;
            guardado.edit().putString("pasta", pasta.getAbsolutePath()).apply();
            return true;
        }

        @JavascriptInterface
        public void esquecerPasta() {
            if (!paginaDoArena()) return;
            guardado.edit().remove("pasta").apply();
        }

        /** [{nome, pasta, tamanho}] de uma pasta (caminho relativo a pasta do ARENA). */
        @JavascriptInterface
        public String listar(String relativo) {
            if (!paginaDoArena()) return "[]";
            JSONArray saida = new JSONArray();
            File pasta = relativo.length() == 0 ? pastaDoArena() : dentroDaPasta(relativo);
            File[] itens = pasta != null ? pasta.listFiles() : null;
            if (itens == null) return saida.toString();
            for (File f : itens) {
                try {
                    JSONObject item = new JSONObject();
                    item.put("nome", f.getName());
                    item.put("pasta", f.isDirectory());
                    item.put("tamanho", f.isFile() ? f.length() : 0);
                    saida.put(item);
                } catch (JSONException falha) {
                    Log.w(TAG, "listar: " + falha);
                }
            }
            return saida.toString();
        }

        /** O caminho inteiro de um arquivo da pasta do ARENA, ou "". */
        @JavascriptInterface
        public String caminho(String relativo) {
            if (!paginaDoArena()) return "";
            File alvo = dentroDaPasta(relativo);
            return alvo != null ? alvo.getAbsolutePath() : "";
        }

        /** Grava (base64) na pasta do ARENA (relativo) ou, com "app:" na
         *  frente, na pasta do app (o jogo livre que vem no APK). Devolve o
         *  caminho inteiro, ou "". */
        @JavascriptInterface
        public String gravar(String relativo, String base64) {
            if (!paginaDoArena()) return "";
            File alvo;
            if (relativo.startsWith("app:")) {
                String dentro = relativo.substring(4);
                boolean pastaCerta = false;
                for (String pasta : PASTAS_DO_APP) pastaCerta |= dentro.startsWith(pasta);
                alvo = new File(getFilesDir(), dentro);
                try {
                    if (!pastaCerta || dentro.contains("..")
                            || !alvo.getCanonicalPath().startsWith(getFilesDir().getCanonicalPath() + File.separator)) {
                        return "";
                    }
                } catch (IOException falha) {
                    return "";
                }
            } else {
                alvo = dentroDaPasta(relativo);
            }
            if (alvo == null) return "";
            try {
                alvo.getParentFile().mkdirs();
                copiar(new java.io.ByteArrayInputStream(Base64.decode(base64, Base64.DEFAULT)), alvo);
                return alvo.getAbsolutePath();
            } catch (IOException | IllegalArgumentException falha) {
                Log.w(TAG, "gravar " + relativo + ": " + falha);
                return "";
            }
        }

        @JavascriptInterface
        public boolean apagar(String relativo) {
            if (!paginaDoArena()) return false;
            File alvo = dentroDaPasta(relativo);
            return alvo != null && alvo.isFile() && alvo.delete();
        }

        /** Abre o jogo: {"nucleo", "rom", "configuracao", "opcoes"}. Devolve
         *  "" (abriu) ou a frase do erro. Os nucleos grandes saem do APK
         *  numa linha de execucao a parte; o fim do jogo vem pelo
         *  ARENA_ANDROID_FIM (onResume). */
        @JavascriptInterface
        public String jogar(String texto) {
            if (!paginaDoArena()) return "So a tela do ARENA abre jogo.";
            final JSONObject pedido;
            try {
                pedido = new JSONObject(texto);
            } catch (JSONException falha) {
                return "Pedido de jogo estragado.";
            }
            new Thread(new Runnable() {
                public void run() {
                    try {
                        abrirJogo(pedido);
                    } catch (IOException | JSONException | RuntimeException falha) {
                        Log.w(TAG, "jogar: " + falha);
                        avisarAPagina("window.ARENA_ANDROID_ERRO && window.ARENA_ANDROID_ERRO("
                                + JSONObject.quote(String.valueOf(falha.getMessage())) + ")");
                    }
                }
            }).start();
            return "";
        }

        @JavascriptInterface
        public void sair() {
            if (!paginaDoArena()) return;
            runOnUiThread(new Runnable() {
                public void run() {
                    finish();
                }
            });
        }
    }
}
