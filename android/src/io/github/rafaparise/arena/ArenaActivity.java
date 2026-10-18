/*
 * ARENA no Android (item 14 do plano de 15/10/2026).
 *
 * O APK do ARENA e' o RetroArch 1.22.2 oficial para Android (o mesmo RetroArch
 * do Windows, do Linux e do Chromebook) com esta tela na frente:
 *
 *   - a tela de sempre do ARENA (launcher/index.html, o mesmo app.js), num
 *     WebView, com o "servidor dentro da pagina" do ARENA do Chromebook
 *     (launcher/navegador): a lista de jogos, os ajustes, os recordes;
 *   - a ponte "ArenaAndroid" (a classe Ponte, abaixo), que a pagina chama
 *     para o que so o Android faz: achar a pasta do ARENA no aparelho (no
 *     cartao SD, no pen drive ligado no cabo OTG ou na memoria interna),
 *     listar e gravar arquivos dela e abrir o jogo no RetroArch NATIVO, com o
 *     nucleo certo (os nucleos vem dentro do APK e saem para a pasta do app
 *     na primeira vez que cada console abre).
 *
 * Os saves ficam na pasta do ARENA (retroarch/saves e retroarch/states), os
 * mesmos do Windows: o jogo salvo no celular continua salvo no computador.
 *
 * Esta tela roda num processo a parte (":tela", no AndroidManifest.xml): o
 * RetroArch pode fechar o processo dele ao sair do jogo, e a tela continua.
 *
 * Seguranca: a pagina so vem de dentro do APK (https://arena.local/, que nao
 * existe na internet: quem responde e' o shouldInterceptRequest daqui). Link
 * para fora abre no navegador do aparelho, nunca dentro desta tela, e a
 * ponte so le e grava dentro da pasta do ARENA escolhida e da pasta do app.
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
import android.webkit.JavascriptInterface;
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
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

public class ArenaActivity extends Activity {
    static final String CASA = "arena.local";
    static final String ENDERECO = "https://" + CASA + "/launcher/index.html?navegador=1&android=1";
    static final String TAG = "ARENA";
    static final int PEDIDO_DE_PERMISSAO = 7;
    // O RetroArch de dentro do APK (o mesmo codigo do RetroArch oficial).
    static final String RETROARCH = "com.retroarch.browser.retroactivity.RetroActivityFuture";

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
        tela.loadUrl(ENDERECO);
    }

    @Override
    protected void onResume() {
        super.onResume();
        esconderAsBarras();
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
        avisarAPagina("window.ARENA_ANDROID_VOLTAR ? window.ARENA_ANDROID_VOLTAR() : 0");
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
        if (pedido == PEDIDO_DE_PERMISSAO) {
            avisarAPagina("window.ARENA_ANDROID_PERMISSAO && window.ARENA_ANDROID_PERMISSAO(" + temPermissao() + ")");
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
        WebResourceResponse r = new WebResourceResponse(tipo, "utf-8", dados);
        Map<String, String> cabecalhos = new HashMap<String, String>();
        cabecalhos.put("Cache-Control", "no-store");
        try {
            r.setStatusCodeAndReasonPhrase(codigo, codigo == 200 ? "OK" : "Not Found");
        } catch (IllegalArgumentException falha) {
            // codigo invalido: fica o padrao
        }
        r.setResponseHeaders(cabecalhos);
        return r;
    }

    class Cliente extends WebViewClient {
        @Override
        public WebResourceResponse shouldInterceptRequest(WebView vista, WebResourceRequest pedido) {
            Uri endereco = pedido.getUrl();
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
            //    o dados/manifesto.json, os jogos que a pagina le)
            File arquivo = dentroDaPasta(relativo);
            if (arquivo != null && arquivo.isFile()) {
                try {
                    return resposta(tipoDe(relativo), new FileInputStream(arquivo), 200);
                } catch (IOException falha) {
                    Log.w(TAG, "nao li " + arquivo + ": " + falha);
                }
            }
            return resposta("text/plain", null, 404);
        }

        @Override
        public boolean shouldOverrideUrlLoading(WebView vista, WebResourceRequest pedido) {
            Uri endereco = pedido.getUrl();
            if (CASA.equals(endereco.getHost())) return false;
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
        List<File> lista = new ArrayList<File>();
        lista.add(Environment.getExternalStorageDirectory());
        File[] doApp = getExternalFilesDirs(null);
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

    /** O nucleo, na pasta de nucleos do app (de onde o RetroArch carrega). */
    File nucleo(String nome) throws IOException {
        File pasta = new File(getApplicationInfo().dataDir, "cores");
        pasta.mkdirs();
        File destino = new File(pasta, nome);
        String origem = "arena-nucleos/" + abiDoApk() + "/" + nome;
        long tamanho = -1;
        try {
            tamanho = getAssets().openFd(origem).getLength();
        } catch (IOException falha) {
            // compactado no APK: o tamanho so se sabe lendo
        }
        if (destino.isFile() && (tamanho < 0 || destino.length() == tamanho)) return destino;
        copiar(getAssets().open(origem), destino);
        return destino;
    }

    /** Poe as BIOS livres (as do ARENA, de licenca livre) na pasta system,
     *  so as que faltam: nunca troca a que ja esta la. */
    void biosLivres(File sistema) {
        try {
            String[] nomes = getAssets().list("arena-bios");
            if (nomes == null) return;
            for (String nome : nomes) copiarArvore("arena-bios/" + nome, new File(sistema, nome));
        } catch (IOException falha) {
            Log.w(TAG, "BIOS livres: " + falha);
        }
    }

    void copiarArvore(String origem, File destino) throws IOException {
        String[] dentro = getAssets().list(origem);
        if (dentro != null && dentro.length > 0) {
            destino.mkdirs();
            for (String nome : dentro) copiarArvore(origem + "/" + nome, new File(destino, nome));
        } else if (!destino.exists()) {
            destino.getParentFile().mkdirs();
            copiar(getAssets().open(origem), destino);
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
        gravarTexto(opcoes, pedido.optString("opcoes", ""));
        StringBuilder cfg = new StringBuilder(pedido.optString("configuracao", ""));
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
            return ArenaActivity.this.temPermissao();
        }

        @JavascriptInterface
        public void pedirPermissao() {
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
            File pasta = new File(caminho);
            if (!pareceArena(pasta)) return false;
            guardado.edit().putString("pasta", pasta.getAbsolutePath()).apply();
            return true;
        }

        @JavascriptInterface
        public void esquecerPasta() {
            guardado.edit().remove("pasta").apply();
        }

        /** [{nome, pasta, tamanho}] de uma pasta (caminho relativo a pasta do ARENA). */
        @JavascriptInterface
        public String listar(String relativo) {
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
            File alvo = dentroDaPasta(relativo);
            return alvo != null ? alvo.getAbsolutePath() : "";
        }

        /** Grava (base64) na pasta do ARENA (relativo) ou, com "app:" na
         *  frente, na pasta do app (o jogo livre que vem no APK). Devolve o
         *  caminho inteiro, ou "". */
        @JavascriptInterface
        public String gravar(String relativo, String base64) {
            File alvo;
            if (relativo.startsWith("app:")) {
                alvo = new File(getFilesDir(), relativo.substring(4));
                if (!permitido(alvo)) return "";
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
            File alvo = dentroDaPasta(relativo);
            return alvo != null && alvo.isFile() && alvo.delete();
        }

        /** Abre o jogo: {"nucleo", "rom", "configuracao", "opcoes"}. Devolve
         *  "" (abriu) ou a frase do erro. Os nucleos grandes saem do APK
         *  numa linha de execucao a parte; o fim do jogo vem pelo
         *  ARENA_ANDROID_FIM (onResume). */
        @JavascriptInterface
        public String jogar(String texto) {
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
            runOnUiThread(new Runnable() {
                public void run() {
                    finish();
                }
            });
        }
    }
}
