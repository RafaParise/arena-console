//! ARENA nativo: o servidor em Rust que vai NA FRENTE do servidor em Python (docs/MIGRACAO-RUST.md, etapa R1).
//!
//! Por que existe (pedido do Rafael, 14/11/2026: "desempenho maximo possivel, mesmo que nao seja mais em Python"):
//! o Python leva ~1 s no PC e ~2 s no Galaxy A12 para nascer, carregar os ~60 modulos e abrir a porta. O nativo
//! nasce em ~30 ms, abre a porta 8777 na hora e:
//!   - entrega sozinho os arquivos da tela (launcher/), sempre;
//!   - entrega a ultima resposta guardada do /api/estado e do /api/catalogo enquanto o Python ainda carrega (a tela
//!     aparece com a lista de jogos antes de o Python terminar; quando ele fica pronto, a tela pede de novo);
//!   - repassa todo o resto ao Python (que escuta so em 127.0.0.1, numa porta sorteada), com o endereco de verdade
//!     de quem pediu, para as regras de seguranca do Python continuarem valendo do mesmo jeito.
//! A cada etapa da migracao, mais rotas passam a ser respondidas aqui; o Python fica atras, como reserva.
//!
//! Uso:  arena-nativo <programa do Python> [argumentos...]
//!   (o ARENA.bat, o ARENA.sh e o app do Android passam o mesmo comando que usavam para abrir o Python)

mod capas;
mod http;
mod sistema;

use std::collections::{HashMap, VecDeque};
use std::io::{self, BufReader, Read, Write};
use std::net::{IpAddr, Shutdown, SocketAddr, TcpListener, TcpStream};
use std::path::{Path, PathBuf};
use std::process::{Command, ExitStatus};
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::{mpsc, Arc, Condvar, Mutex};
use std::time::{Duration, Instant};

/// As rotas que o nativo guarda para a abertura seguinte (o nome do arquivo em dados/nativo).
const GUARDADAS: [(&str, &str); 2] = [("/api/estado", "estado.json"), ("/api/catalogo", "catalogo.json")];
/// Quanto um pedido espera o Python ficar pronto antes de desistir (a primeira abertura depois de atualizar o app,
/// no A12, leva ~3 s; com folga larga para o celular ocupado).
const ESPERA_PELO_PYTHON: Duration = Duration::from_secs(120);
/// Os avisos para a tela (ideia do blueprint events.rs, adaptada; 14/11/2026): quantos ficam guardados para quem
/// reconecta, quantas telas podem ouvir ao mesmo tempo (cada uma prende uma thread daqui) e de quanto em quanto
/// tempo a conexao parada recebe um sinal de vida (e' assim que se descobre uma aba fechada).
const AVISOS_GUARDADOS: usize = 64;
const OUVINTES_NO_MAXIMO: u64 = 8;
const SINAL_DE_VIDA: Duration = Duration::from_secs(20);

/// A fila dos avisos: (numero, tipo, dados em JSON numa linha so). O numero comeca na hora da abertura, em ms, para
/// nunca repetir o de uma abertura anterior (o navegador manda o ultimo que viu, no Last-Event-ID, ao reconectar).
struct Avisos {
    ultimo: u64,
    fila: VecDeque<(u64, String, String)>,
}

struct Arena {
    raiz: PathBuf,
    launcher: PathBuf,
    pasta_guardada: PathBuf,
    porta: u16,
    porta_python: u16,
    /// O segredo entre o nativo e o Python: so com ele o Python acredita no X-Arena-Origem.
    segredo_proxy: String,
    /// No Android, o segredo da tela (o cookie que o app poe no WebView): sem ele, quem pergunta e' outro app.
    segredo_android: Option<String>,
    python_pronto: Mutex<bool>,
    sinal_pronto: Condvar,
    python_saiu: AtomicBool,
    guardadas: Mutex<HashMap<&'static str, Arc<Vec<u8>>>>,
    /// A escuta de agora ("127.0.0.1" ou "0.0.0.0") e a geracao dela (a chave da rede troca a escuta).
    escuta: Mutex<String>,
    geracao: AtomicU64,
    inicio: Instant,
    /// Quantas capas o nativo entregou antes de o Python ficar pronto (a medida da etapa R2).
    capas_antes_do_python: AtomicU64,
    /// Os avisos do Python para a tela (/_nativo/evento entra, /_nativo/eventos sai) e quantas telas ouvem agora.
    avisos: Mutex<Avisos>,
    sinal_aviso: Condvar,
    ouvintes: AtomicU64,
}

fn main() {
    let inicio = Instant::now();
    let argumentos: Vec<String> = std::env::args().skip(1).collect();
    if argumentos.is_empty() {
        eprintln!("Uso: arena-nativo <programa do Python> [argumentos...]");
        std::process::exit(2);
    }
    sistema::ignorar_ctrl_c();
    let raiz = raiz_do_arena();
    let porta: u16 = std::env::var("ARENA_PORTA").ok().and_then(|p| p.parse().ok()).unwrap_or(8777);
    let porta_python = porta_livre().unwrap_or(porta.wrapping_add(1));
    let segredo_android = std::env::var("ARENA_ANDROID_SEGREDO").ok().filter(|s| !s.is_empty());
    let pasta_guardada = raiz.join("dados").join("nativo");
    let arena = Arc::new(Arena {
        launcher: raiz.join("launcher"),
        raiz: raiz.clone(),
        guardadas: Mutex::new(ler_guardadas(&pasta_guardada)),
        pasta_guardada,
        porta,
        porta_python,
        segredo_proxy: sistema::segredo(),
        segredo_android,
        python_pronto: Mutex::new(false),
        sinal_pronto: Condvar::new(),
        python_saiu: AtomicBool::new(false),
        escuta: Mutex::new(String::new()),
        geracao: AtomicU64::new(0),
        inicio,
        capas_antes_do_python: AtomicU64::new(0),
        avisos: Mutex::new(Avisos { ultimo: agora_em_ms(), fila: VecDeque::new() }),
        sinal_aviso: Condvar::new(),
        ouvintes: AtomicU64::new(0),
    });

    // 1. A porta, ja (a escuta da configuracao: so este computador, ou a rede se a chave estiver ligada).
    let escuta = escuta_da_config(&raiz.join("dados").join("config.json"));
    if let Err(falha) = escutar(&arena, &escuta) {
        if falha.kind() == io::ErrorKind::AddrInUse {
            eprintln!("\n  [ERRO] A porta {} ja esta em uso.", porta);
            eprintln!("  O ARENA provavelmente ja esta aberto. Procure a outra");
            eprintln!("  janela preta, ou abra http://127.0.0.1:{} no navegador.", porta);
        } else {
            eprintln!("\n  [ERRO] Nao foi possivel abrir o servidor: {}", falha);
        }
        std::process::exit(1);
    }
    eprintln!(
        "[ARENA] Nativo: porta {} aberta em {} ms (o Python carrega atras, na porta {}).",
        porta,
        inicio.elapsed().as_millis(),
        porta_python
    );
    // No Android, o app so mostra a tela depois do aviso "pronto" pelo fio (a saida padrao); o nativo e' parte do
    // APK, como o Python, e a porta ja e' dele. O Python avisa de novo quando ficar pronto (o app ignora o segundo).
    if arena.segredo_android.is_some() {
        let linha = format!("{{\"pedido\": \"pronto\", \"endereco\": \"http://127.0.0.1:{}\"}}\n", porta);
        let mut saida = io::stdout().lock();
        let _ = saida.write_all(linha.as_bytes());
        let _ = saida.flush();
    }

    // 2. O Python, atras.
    let mut comando = Command::new(&argumentos[0]);
    comando
        .args(&argumentos[1..])
        .env("ARENA_ATRAS_DO_NATIVO", &arena.segredo_proxy)
        .env("ARENA_PORTA_INTERNA", arena.porta_python.to_string());
    #[cfg(unix)]
    unsafe {
        use std::os::unix::process::CommandExt;
        comando.pre_exec(|| {
            sistema::morrer_com_o_pai();
            Ok(())
        });
    }
    let mut filho = match comando.spawn() {
        Ok(f) => f,
        Err(falha) => {
            eprintln!("\n  [ERRO] Nao consegui abrir o Python do ARENA ({}): {}", argumentos[0], falha);
            eprintln!("  Copie de novo a pasta do ARENA inteira e abra outra vez.");
            std::process::exit(1);
        }
    };
    {
        let arena = Arc::clone(&arena);
        std::thread::spawn(move || esperar_o_python(&arena));
    }

    // 3. Quando o Python fecha, o nativo fecha junto, com o mesmo codigo (o ARENA.bat e o app decidem se reabrem).
    let status = filho.wait();
    arena.python_saiu.store(true, Ordering::SeqCst);
    arena.sinal_pronto.notify_all();
    std::process::exit(codigo_da_saida(status));
}

fn codigo_da_saida(status: io::Result<ExitStatus>) -> i32 {
    match status {
        Ok(s) => {
            if let Some(c) = s.code() {
                return c;
            }
            #[cfg(unix)]
            {
                use std::os::unix::process::ExitStatusExt;
                if let Some(sinal) = s.signal() {
                    return 128 + sinal;
                }
            }
            3
        }
        Err(_) => 3,
    }
}

/// A pasta do ARENA: a de cima do servidor/, quando o nativo esta la (no PC: servidor\arena-nativo.exe); senao, a
/// pasta atual (no Android, o app abre o nativo de dentro do APK, ja na pasta do ARENA). Assim o nativo nunca grava
/// o dados/nativo numa pasta qualquer, mesmo aberto por um atalho com outra pasta de trabalho.
fn raiz_do_arena() -> PathBuf {
    if let Ok(programa) = std::env::current_exe() {
        if let Some(servidor) = programa.parent() {
            let nome = servidor.file_name().and_then(|n| n.to_str()).unwrap_or("");
            if let Some(raiz) = servidor.parent() {
                if nome.eq_ignore_ascii_case("servidor") && raiz.join("launcher").is_dir() {
                    return raiz.to_path_buf();
                }
            }
        }
    }
    std::env::current_dir().unwrap_or_else(|_| PathBuf::from("."))
}

/// Uma porta livre so deste computador, para o Python (o sistema escolhe).
fn porta_livre() -> Option<u16> {
    TcpListener::bind(("127.0.0.1", 0)).ok().and_then(|l| l.local_addr().ok()).map(|a| a.port())
}

/// "0.0.0.0" se a chave "Liberar a rede" estiver ligada na configuracao, senao "127.0.0.1" (o mesmo que o
/// escuta_da_config do Python). Le so o campo permitir_rede, sem precisar de um leitor de JSON inteiro.
fn escuta_da_config(arquivo: &Path) -> String {
    let texto = std::fs::read_to_string(arquivo).unwrap_or_default();
    if let Some(pos) = texto.find("\"permitir_rede\"") {
        let resto = texto[pos + "\"permitir_rede\"".len()..].trim_start();
        if let Some(depois) = resto.strip_prefix(':') {
            if depois.trim_start().starts_with("true") {
                return "0.0.0.0".to_string();
            }
        }
    }
    "127.0.0.1".to_string()
}

fn ler_guardadas(pasta: &Path) -> HashMap<&'static str, Arc<Vec<u8>>> {
    let mut mapa = HashMap::new();
    for (rota, nome) in GUARDADAS {
        if let Ok(corpo) = std::fs::read(pasta.join(nome)) {
            if corpo.first() == Some(&b'{') {
                mapa.insert(rota, Arc::new(corpo));
            }
        }
    }
    mapa
}

/// Abre a escuta em "endereco" e poe uma thread aceitando as conexoes. A escuta antiga (se houver) ja foi fechada.
fn escutar(arena: &Arc<Arena>, endereco: &str) -> io::Result<()> {
    let ouvinte = TcpListener::bind((endereco, arena.porta))?;
    let minha = arena.geracao.fetch_add(1, Ordering::SeqCst) + 1;
    *arena.escuta.lock().unwrap() = endereco.to_string();
    let arena = Arc::clone(arena);
    std::thread::spawn(move || {
        for conexao in ouvinte.incoming() {
            if arena.geracao.load(Ordering::SeqCst) != minha {
                break; // a chave da rede trocou a escuta: esta sai e solta a porta
            }
            if let Ok(conexao) = conexao {
                let arena = Arc::clone(&arena);
                std::thread::spawn(move || {
                    let _ = atender(&arena, conexao);
                });
            }
        }
        drop(ouvinte);
    });
    Ok(())
}

/// A chave da rede mudou (o Python avisa): fecha a escuta de agora e abre a nova. Se a nova nao abrir, volta a
/// escutar so neste computador, para a tela nunca ficar sem servidor (o mesmo que o Python fazia).
fn trocar_escuta(arena: &Arc<Arena>, nova: &str) -> String {
    let atual = arena.escuta.lock().unwrap().clone();
    if atual == nova {
        return atual;
    }
    // Acorda a thread da escuta antiga com uma conexao vazia: ela ve a geracao nova e solta a porta.
    let (pronto, esperar) = mpsc::channel::<()>();
    arena.geracao.fetch_add(1, Ordering::SeqCst);
    let porta = arena.porta;
    std::thread::spawn(move || {
        let _ = TcpStream::connect_timeout(&SocketAddr::from(([127, 0, 0, 1], porta)), Duration::from_secs(2));
        let _ = pronto.send(());
    });
    let _ = esperar.recv_timeout(Duration::from_secs(3));
    // A porta sai do sistema logo depois do drop; tenta por pouco tempo.
    for tentativa in 0..20 {
        match escutar(arena, nova) {
            Ok(()) => return nova.to_string(),
            Err(_) if tentativa < 19 => std::thread::sleep(Duration::from_millis(25)),
            Err(falha) => {
                eprintln!("[ARENA] Nao consegui abrir para a rede ({}). Continuo so neste computador.", falha);
            }
        }
    }
    for _ in 0..20 {
        if escutar(arena, "127.0.0.1").is_ok() {
            break;
        }
        std::thread::sleep(Duration::from_millis(25));
    }
    "127.0.0.1".to_string()
}

/// Bate na porta do Python ate ele abrir (so na abertura; termina sozinha) e avisa quem estava esperando.
fn esperar_o_python(arena: &Arc<Arena>) {
    let endereco = SocketAddr::from(([127, 0, 0, 1], arena.porta_python));
    while !arena.python_saiu.load(Ordering::SeqCst) {
        if TcpStream::connect_timeout(&endereco, Duration::from_millis(200)).is_ok() {
            *arena.python_pronto.lock().unwrap() = true;
            arena.sinal_pronto.notify_all();
            eprintln!(
                "[ARENA] Nativo: o Python ficou pronto em {} ms ({} capas ja tinham saido daqui).",
                arena.inicio.elapsed().as_millis(),
                arena.capas_antes_do_python.load(Ordering::SeqCst)
            );
            return;
        }
        std::thread::sleep(Duration::from_millis(25));
    }
}

/// Espera o Python ficar pronto. false se ele fechou ou passou do tempo.
fn esperar_pronto(arena: &Arena, limite: Duration) -> bool {
    let fim = Instant::now() + limite;
    let mut pronto = arena.python_pronto.lock().unwrap();
    while !*pronto {
        if arena.python_saiu.load(Ordering::SeqCst) {
            return false;
        }
        let agora = Instant::now();
        if agora >= fim {
            return false;
        }
        pronto = arena.sinal_pronto.wait_timeout(pronto, fim - agora).unwrap().0;
    }
    true
}

fn atender(arena: &Arc<Arena>, conexao: TcpStream) -> io::Result<()> {
    let ip = conexao.peer_addr()?.ip();
    let _ = conexao.set_nodelay(true);
    let mut escrita = conexao.try_clone()?;
    let mut leitor = BufReader::new(conexao);
    loop {
        let pedido = match http::ler_pedido(&mut leitor) {
            Ok(Some(p)) => p,
            Ok(None) => return Ok(()),
            Err(falha) => {
                if falha.kind() == io::ErrorKind::InvalidData {
                    let _ = http::responder_erro(
                        &mut escrita,
                        400,
                        "Pedido que o ARENA nao entendeu. Recarregue a tela do ARENA (F5).",
                    );
                }
                return Ok(());
            }
        };
        let manter = pedido.manter_aberta();
        let caminho = pedido.caminho().to_string();

        // O aviso do Python de que a chave da rede mudou.
        if caminho == "/_nativo/rede" {
            responder_rede(arena, &pedido, ip, &mut escrita)?;
            return Ok(());
        }
        // A tela pergunta, depois de mostrar o que estava guardado, quando o Python ficou pronto.
        if caminho == "/_nativo/pronto" && pedido.metodo == "GET" {
            let pronto = esperar_pronto(arena, Duration::from_secs(60));
            let corpo = format!("{{\"ok\": {}}}", pronto);
            http::responder(
                &mut escrita,
                if pronto { 200 } else { 503 },
                "application/json; charset=utf-8",
                &[("Cache-Control", "no-store")],
                corpo.as_bytes(),
                manter,
            )?;
            if manter {
                continue;
            }
            return Ok(());
        }
        // O Python conta que algo mudou (a lista de jogos, o jogo que fechou); o nativo repassa a tela.
        if caminho == "/_nativo/evento" {
            receber_aviso(arena, &pedido, ip, &mut escrita)?;
            return Ok(());
        }
        // A tela fica ouvindo os avisos (Server-Sent Events): uma conexao parada, sem perguntar de novo.
        if caminho == "/_nativo/eventos" && pedido.metodo == "GET" {
            if !local_confiavel(arena, ip, &pedido) || !da_propria_tela(&pedido, arena.porta) {
                http::responder_erro(&mut escrita, 403, "Os avisos do ARENA sao so para a tela do ARENA neste aparelho.")?;
                return Ok(());
            }
            return ouvir_avisos(arena, &pedido, &mut escrita);
        }

        let confiavel = local_confiavel(arena, ip, &pedido);
        if confiavel && pedido.metodo == "GET" {
            // Os arquivos da tela: sempre daqui.
            if let Some(arquivo) = arquivo_da_tela(&arena.launcher, &caminho) {
                if let Ok(corpo) = std::fs::read(&arquivo) {
                    http::responder(&mut escrita, 200, tipo_do_arquivo(&arquivo), &[("Cache-Control", "no-cache")],
                                    &corpo, manter)?;
                    if manter {
                        continue;
                    }
                    return Ok(());
                }
            }
            // As capas (etapa R2): a mesma regra do Python; o que nao for o caminho simples vai a ele.
            if caminho == "/api/capa" {
                if let Some((corpo, tipo)) = capas::capa(&arena.raiz, &pedido.alvo) {
                    if !*arena.python_pronto.lock().unwrap() {
                        arena.capas_antes_do_python.fetch_add(1, Ordering::SeqCst);
                    }
                    http::responder(&mut escrita, 200, tipo, &[("Cache-Control", "max-age=86400")], &corpo, manter)?;
                    if manter {
                        continue;
                    }
                    return Ok(());
                }
            }
            // O que estava guardado, so enquanto o Python ainda carrega.
            if !*arena.python_pronto.lock().unwrap() {
                let guardada = arena.guardadas.lock().unwrap().get(caminho.as_str()).cloned();
                if let Some(corpo) = guardada {
                    http::responder(
                        &mut escrita,
                        200,
                        "application/json; charset=utf-8",
                        &[("Cache-Control", "no-store"), ("X-Arena-Guardado", "1"), ("X-Arena-Nativo", "1")],
                        &corpo,
                        manter,
                    )?;
                    if manter {
                        continue;
                    }
                    return Ok(());
                }
            }
        }
        // Todo o resto: o Python responde (e a conexao fecha depois, como no proxy mais simples).
        repassar(arena, &pedido, ip, &mut escrita)?;
        let _ = escrita.shutdown(Shutdown::Both);
        return Ok(());
    }
}

/// So o Python (do mesmo computador, com o segredo) troca a escuta.
fn responder_rede(arena: &Arc<Arena>, pedido: &http::Pedido, ip: IpAddr, saida: &mut TcpStream) -> io::Result<()> {
    let segredo_ok = pedido
        .cabecalho("X-Arena-Proxy")
        .map(|s| iguais_em_tempo_constante(s.as_bytes(), arena.segredo_proxy.as_bytes()))
        .unwrap_or(false);
    if pedido.metodo != "POST" || !ip.is_loopback() || !segredo_ok {
        return http::responder_erro(saida, 403, "So o proprio ARENA troca a escuta. Use a chave Liberar a rede nos Ajustes.");
    }
    let corpo = String::from_utf8_lossy(&pedido.corpo);
    let nova = if corpo.contains("0.0.0.0") { "0.0.0.0" } else { "127.0.0.1" };
    let ficou = trocar_escuta(arena, nova);
    let resposta = format!("{{\"ok\": true, \"escuta\": \"{}\"}}", ficou);
    http::responder(saida, 200, "application/json; charset=utf-8", &[("Cache-Control", "no-store")],
                    resposta.as_bytes(), false)
}

/// O aviso do Python (do mesmo computador, com o segredo): entra na fila e acorda quem esta ouvindo.
/// POST /_nativo/evento?tipo=catalogo com o corpo {"geracao": 123} (JSON numa linha so).
fn receber_aviso(arena: &Arena, pedido: &http::Pedido, ip: IpAddr, saida: &mut TcpStream) -> io::Result<()> {
    let segredo_ok = pedido
        .cabecalho("X-Arena-Proxy")
        .map(|s| iguais_em_tempo_constante(s.as_bytes(), arena.segredo_proxy.as_bytes()))
        .unwrap_or(false);
    if pedido.metodo != "POST" || !ip.is_loopback() || !segredo_ok {
        return http::responder_erro(saida, 403, "So o proprio ARENA manda avisos para a tela.");
    }
    let tipo = valor_da_consulta(&pedido.alvo, "tipo").unwrap_or("").to_string();
    let corpo = String::from_utf8_lossy(&pedido.corpo).trim().to_string();
    let dados = if corpo.is_empty() { "{}".to_string() } else { corpo };
    if !tipo_de_aviso_valido(&tipo) || !dados_de_aviso_validos(&dados) {
        return http::responder_erro(saida, 400, "Aviso que o servidor nativo nao entendeu. Atualize o ARENA inteiro.");
    }
    let numero = {
        let mut avisos = arena.avisos.lock().unwrap();
        avisos.ultimo += 1;
        let numero = avisos.ultimo;
        avisos.fila.push_back((numero, tipo, dados));
        while avisos.fila.len() > AVISOS_GUARDADOS {
            avisos.fila.pop_front();
        }
        numero
    };
    arena.sinal_aviso.notify_all();
    let resposta = format!("{{\"ok\": true, \"numero\": {}}}", numero);
    http::responder(saida, 200, "application/json; charset=utf-8", &[("Cache-Control", "no-store")],
                    resposta.as_bytes(), false)
}

/// Solta a vaga de ouvinte quando a conexao acaba, de qualquer jeito (aba fechada, erro de escrita).
struct VagaDeOuvinte<'a>(&'a AtomicU64);

impl Drop for VagaDeOuvinte<'_> {
    fn drop(&mut self) {
        self.0.fetch_sub(1, Ordering::SeqCst);
    }
}

/// A tela ouvindo os avisos: a resposta nunca termina; cada aviso novo sai na hora, e a cada SINAL_DE_VIDA sem
/// aviso sai um comentario (": vivo"), que o navegador ignora. Parada, a thread dorme na Condvar (0% de CPU).
fn ouvir_avisos(arena: &Arena, pedido: &http::Pedido, saida: &mut TcpStream) -> io::Result<()> {
    if arena.ouvintes.fetch_add(1, Ordering::SeqCst) >= OUVINTES_NO_MAXIMO {
        arena.ouvintes.fetch_sub(1, Ordering::SeqCst);
        return http::responder_erro(saida, 503, "Ha telas demais abertas no ARENA. Feche as abas repetidas.");
    }
    let _vaga = VagaDeOuvinte(&arena.ouvintes);
    // Quem para de ler (aba congelada) nao prende a thread para sempre.
    let _ = saida.set_write_timeout(Some(Duration::from_secs(10)));
    saida.write_all(
        b"HTTP/1.1 200 OK\r\nContent-Type: text/event-stream; charset=utf-8\r\nCache-Control: no-store\r\n\
          X-Content-Type-Options: nosniff\r\nX-Arena-Nativo: 1\r\nConnection: close\r\n\r\nretry: 3000\n\n",
    )?;
    saida.flush()?;
    let mut visto = {
        let avisos = arena.avisos.lock().unwrap();
        desde_onde(pedido.cabecalho("Last-Event-ID"), avisos.ultimo)
    };
    loop {
        let novos: Vec<(u64, String, String)> = {
            let mut avisos = arena.avisos.lock().unwrap();
            if avisos.ultimo <= visto {
                avisos = arena.sinal_aviso.wait_timeout(avisos, SINAL_DE_VIDA).unwrap().0;
            }
            let novos = avisos.fila.iter().filter(|aviso| aviso.0 > visto).cloned().collect();
            visto = visto.max(avisos.ultimo);
            novos
        };
        let texto = if novos.is_empty() { ": vivo\n\n".to_string() } else { texto_dos_avisos(&novos) };
        saida.write_all(texto.as_bytes())?;
        saida.flush()?;
    }
}

/// De que aviso a tela continua. O navegador manda, ao reconectar, o numero do ultimo que viu (Last-Event-ID): se
/// ele e' desta abertura ou de uma anterior (numero menor), a tela recebe os guardados depois dele; sem ele, ou com
/// um numero do futuro (relogio que voltou), so os avisos que vierem daqui em diante.
fn desde_onde(ultimo_visto: Option<&str>, ultimo: u64) -> u64 {
    match ultimo_visto.and_then(|valor| valor.trim().parse::<u64>().ok()) {
        Some(numero) if numero <= ultimo => numero,
        _ => ultimo,
    }
}

/// O pedido veio da propria pagina do ARENA, e nao de outro site aberto no mesmo navegador? (Achado da revisao de
/// 14/11/2026: sem isto, um site qualquer no PC do laboratorio podia abrir conexoes aqui e ocupar as vagas de
/// ouvinte.) O navegador avisa quem pediu: o Sec-Fetch-Site ("same-origin" na pagina do ARENA, "none" quando a
/// pessoa digita o endereco) e, num pedido de outro site, o Origin. Sem esses cabecalhos, nao e' navegador.
fn da_propria_tela(pedido: &http::Pedido, porta: u16) -> bool {
    if let Some(site) = pedido.cabecalho("Sec-Fetch-Site") {
        let site = site.trim().to_ascii_lowercase();
        if site != "same-origin" && site != "none" {
            return false;
        }
    }
    match pedido.cabecalho("Origin") {
        None => true,
        Some(origem) => {
            let origem = origem.trim().to_ascii_lowercase();
            [format!("http://127.0.0.1:{}", porta), format!("http://localhost:{}", porta), format!("http://[::1]:{}", porta)]
                .iter()
                .any(|propria| *propria == origem)
        }
    }
}

/// Os avisos no formato do Server-Sent Events: "id", "event" e "data", com uma linha em branco no fim de cada um.
fn texto_dos_avisos(avisos: &[(u64, String, String)]) -> String {
    let mut texto = String::new();
    for (numero, tipo, dados) in avisos {
        texto.push_str(&format!("id: {}\nevent: {}\ndata: {}\n\n", numero, tipo, dados));
    }
    texto
}

/// O tipo do aviso: so letras minusculas e _, ate 24 (vira o nome do evento na tela).
fn tipo_de_aviso_valido(tipo: &str) -> bool {
    !tipo.is_empty() && tipo.len() <= 24 && tipo.bytes().all(|b| b.is_ascii_lowercase() || b == b'_')
}

/// Os dados: um objeto JSON pequeno e numa linha so (quebra de linha no meio cortaria o aviso em dois).
fn dados_de_aviso_validos(dados: &str) -> bool {
    dados.len() <= 2048 && dados.starts_with('{') && dados.ends_with('}') && !dados.contains(['\r', '\n'])
}

/// O valor de um parametro simples da consulta (?tipo=catalogo), sem decodificar: quem chama confere o formato.
fn valor_da_consulta<'a>(alvo: &'a str, nome: &str) -> Option<&'a str> {
    let consulta = alvo.split_once('?')?.1;
    consulta.split('&').find_map(|parte| match parte.split_once('=') {
        Some((chave, valor)) if chave == nome => Some(valor),
        _ => None,
    })
}

/// Milissegundos desde 1970 (o comeco da numeracao dos avisos).
fn agora_em_ms() -> u64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_millis() as u64)
        .unwrap_or(0)
}

/// O pedido veio da tela do ARENA neste mesmo aparelho? So para esses o nativo responde sozinho; qualquer outro
/// caso (outro computador da rede, nome estranho no Host, outro app do celular) vai ao Python, que decide pelas
/// regras de sempre (checar_acesso_de_rede: loopback, Host contra DNS rebinding, segredo do Android).
fn local_confiavel(arena: &Arena, ip: IpAddr, pedido: &http::Pedido) -> bool {
    let loopback = match ip {
        IpAddr::V4(v4) => v4.is_loopback(),
        IpAddr::V6(v6) => v6.is_loopback() || v6.to_ipv4_mapped().map(|v4| v4.is_loopback()).unwrap_or(false),
    };
    if !loopback || !host_confiavel(pedido.cabecalho("Host")) {
        return false;
    }
    match &arena.segredo_android {
        None => true,
        Some(segredo) => cookie_confere(pedido.cabecalho("Cookie"), segredo),
    }
}

/// O Host e' um nome deste aparelho para a tela (127.0.0.1, localhost ou ::1)? Sem Host, nao e' navegador.
fn host_confiavel(host: Option<&str>) -> bool {
    let host = match host {
        None => return true,
        Some(h) => h.trim().to_ascii_lowercase(),
    };
    if host.is_empty() {
        return true;
    }
    let nome = if let Some(resto) = host.strip_prefix('[') {
        resto.split(']').next().unwrap_or("").to_string()
    } else {
        host.rsplit_once(':').map(|(n, _)| n.to_string()).unwrap_or(host.clone())
    };
    matches!(nome.as_str(), "127.0.0.1" | "localhost" | "::1")
}

/// O cookie arena_segredo bate com o segredo desta abertura (comparacao em tempo constante)?
fn cookie_confere(cookie: Option<&str>, segredo: &str) -> bool {
    let cookie = match cookie {
        Some(c) => c,
        None => return false,
    };
    for parte in cookie.split(';') {
        if let Some((nome, valor)) = parte.trim().split_once('=') {
            if nome.trim() == "arena_segredo" {
                let valor = valor.trim().trim_matches('"');
                return iguais_em_tempo_constante(valor.as_bytes(), segredo.as_bytes());
            }
        }
    }
    false
}

fn iguais_em_tempo_constante(a: &[u8], b: &[u8]) -> bool {
    if a.len() != b.len() {
        return false;
    }
    a.iter().zip(b).fold(0u8, |acc, (x, y)| acc | (x ^ y)) == 0
}

/// O arquivo da tela para o caminho pedido, so dentro de launcher/ e so com nome simples (letras, numeros, ponto,
/// traco, sublinhado e barra; nada de "..", de "\" nem de ":"). O resto vai ao Python, que responde 404 ou a rota.
fn arquivo_da_tela(launcher: &Path, caminho: &str) -> Option<PathBuf> {
    let caminho = if caminho == "/" { "/index.html" } else { caminho };
    if caminho.starts_with("/api/") || caminho.starts_with("/toque/") || caminho.starts_with("/_nativo/") {
        return None;
    }
    let relativo = caminho.strip_prefix('/')?;
    if relativo.is_empty()
        || relativo.split('/').any(|parte| parte.is_empty() || parte == "." || parte == "..")
        || !relativo.bytes().all(|b| b.is_ascii_alphanumeric() || b"._-/".contains(&b))
    {
        return None;
    }
    let arquivo = launcher.join(relativo);
    if arquivo.is_file() {
        Some(arquivo)
    } else {
        None
    }
}

/// O mesmo dicionario TIPOS do servidor em Python.
fn tipo_do_arquivo(arquivo: &Path) -> &'static str {
    match arquivo.extension().and_then(|e| e.to_str()).map(|e| e.to_ascii_lowercase()).as_deref() {
        Some("html") => "text/html; charset=utf-8",
        Some("css") => "text/css; charset=utf-8",
        Some("js") => "application/javascript; charset=utf-8",
        Some("json") => "application/json; charset=utf-8",
        Some("svg") => "image/svg+xml",
        Some("png") => "image/png",
        Some("ico") => "image/x-icon",
        _ => "application/octet-stream",
    }
}

/// Cabecalhos que valem so para um trecho da conversa (RFC 9110, 7.6.1) e os que so o nativo pode escrever.
fn fica_de_fora(nome: &str) -> bool {
    ["connection", "keep-alive", "proxy-connection", "te", "trailer", "upgrade", "x-arena-origem", "x-arena-proxy"]
        .iter()
        .any(|n| nome.eq_ignore_ascii_case(n))
}

/// Repassa o pedido ao Python e devolve a resposta dele, com "Connection: close". Guarda o corpo do /api/estado e
/// do /api/catalogo para a proxima abertura.
fn repassar(arena: &Arc<Arena>, pedido: &http::Pedido, ip: IpAddr, cliente: &mut TcpStream) -> io::Result<()> {
    if !esperar_pronto(arena, ESPERA_PELO_PYTHON) {
        return http::responder_erro(
            cliente,
            503,
            "O servidor do ARENA ainda nao abriu (ou fechou). Espere uns segundos e recarregue a tela; se nao voltar, feche e abra o ARENA de novo.",
        );
    }
    let mut python = match TcpStream::connect_timeout(
        &SocketAddr::from(([127, 0, 0, 1], arena.porta_python)),
        Duration::from_secs(10),
    ) {
        Ok(c) => c,
        Err(_) => {
            return http::responder_erro(
                cliente,
                502,
                "O servidor do ARENA nao respondeu. Espere uns segundos: ele costuma voltar sozinho. Se nao voltar, feche e abra o ARENA de novo.",
            )
        }
    };
    let _ = python.set_nodelay(true);
    let mut cabeca = format!("{} {} HTTP/1.1\r\n", pedido.metodo, pedido.alvo);
    for (nome, valor) in &pedido.cabecalhos {
        if !fica_de_fora(nome) {
            cabeca.push_str(&format!("{}: {}\r\n", nome, valor));
        }
    }
    // O endereco de quem pediu: so o nativo escreve (os que vieram de fora foram tirados acima).
    let origem = match ip {
        IpAddr::V6(v6) => v6.to_ipv4_mapped().map(IpAddr::V4).unwrap_or(ip),
        _ => ip,
    };
    cabeca.push_str(&format!(
        "X-Arena-Origem: {}\r\nX-Arena-Proxy: {}\r\nConnection: close\r\n\r\n",
        origem, arena.segredo_proxy
    ));
    let mut tudo = cabeca.into_bytes();
    tudo.extend_from_slice(&pedido.corpo);
    python.write_all(&tudo)?;

    let guardar_como = if pedido.metodo == "GET" {
        GUARDADAS.iter().find(|(rota, _)| *rota == pedido.caminho()).copied()
    } else {
        None
    };
    // A cabeca da resposta do Python, trocando o Connection por "close" (a conexao fecha depois desta resposta).
    let (cabeca_resposta, inicio_do_corpo) = ler_cabeca_da_resposta(&mut python)?;
    let mut saida_cabeca = String::new();
    for (i, linha) in cabeca_resposta.split("\r\n").enumerate() {
        if i > 0 && linha.split(':').next().map(|n| n.trim().eq_ignore_ascii_case("connection")).unwrap_or(false) {
            continue;
        }
        saida_cabeca.push_str(linha);
        saida_cabeca.push_str("\r\n");
    }
    // A marca de que o nativo esta na frente: com ela, a tela passa a ouvir os avisos (/_nativo/eventos).
    saida_cabeca.push_str("X-Arena-Nativo: 1\r\nConnection: close\r\n\r\n");
    cliente.write_all(saida_cabeca.as_bytes())?;

    match guardar_como {
        Some((rota, nome)) if cabeca_resposta.starts_with("HTTP/1.1 200") || cabeca_resposta.starts_with("HTTP/1.0 200") => {
            // Le inteiro (para guardar), manda e grava.
            let mut corpo = inicio_do_corpo;
            python.read_to_end(&mut corpo)?;
            cliente.write_all(&corpo)?;
            cliente.flush()?;
            guardar(arena, rota, nome, corpo);
        }
        _ => {
            cliente.write_all(&inicio_do_corpo)?;
            io::copy(&mut python, cliente)?;
            cliente.flush()?;
        }
    }
    Ok(())
}

/// Le ate o fim dos cabecalhos ("\r\n\r\n"). Devolve a cabeca (sem a linha em branco) e o que ja veio do corpo.
fn ler_cabeca_da_resposta(python: &mut TcpStream) -> io::Result<(String, Vec<u8>)> {
    let mut lido = Vec::with_capacity(4096);
    let mut pedaco = [0u8; 8192];
    loop {
        let n = python.read(&mut pedaco)?;
        if n == 0 {
            return Err(io::Error::new(io::ErrorKind::UnexpectedEof, "o Python fechou sem responder"));
        }
        lido.extend_from_slice(&pedaco[..n]);
        if let Some(pos) = lido.windows(4).position(|j| j == b"\r\n\r\n") {
            let cabeca = String::from_utf8_lossy(&lido[..pos]).to_string();
            let resto = lido[pos + 4..].to_vec();
            return Ok((cabeca, resto));
        }
        if lido.len() > 256 * 1024 {
            return Err(io::Error::new(io::ErrorKind::InvalidData, "cabecalho da resposta grande demais"));
        }
    }
}

/// Guarda a resposta para a proxima abertura (gravacao atomica: temporario e troca). O estado so e' guardado sem
/// jogo aberto: na abertura seguinte nao ha jogo, e a tela mostraria a barra do jogo por engano.
fn guardar(arena: &Arena, rota: &'static str, nome: &str, corpo: Vec<u8>) {
    if corpo.first() != Some(&b'{') {
        return;
    }
    if rota == "/api/estado" && !sem_jogo_aberto(&corpo) {
        return;
    }
    let corpo = Arc::new(corpo);
    {
        let mut guardadas = arena.guardadas.lock().unwrap();
        if guardadas.get(rota).map(|c| c.as_slice() == corpo.as_slice()).unwrap_or(false) {
            return; // igual ao que ja estava: nada a gravar
        }
        guardadas.insert(rota, Arc::clone(&corpo));
    }
    let _ = std::fs::create_dir_all(&arena.pasta_guardada);
    let destino = arena.pasta_guardada.join(nome);
    let temporario = arena.pasta_guardada.join(format!("{}.{}.tmp", nome, sistema::sorteio()));
    if std::fs::write(&temporario, corpo.as_slice()).is_ok() && std::fs::rename(&temporario, &destino).is_err() {
        let _ = std::fs::remove_file(&temporario);
    }
}

fn sem_jogo_aberto(corpo: &[u8]) -> bool {
    let texto = String::from_utf8_lossy(corpo);
    match texto.find("\"jogo_em_andamento\"") {
        None => true,
        Some(pos) => {
            let resto = texto[pos + "\"jogo_em_andamento\"".len()..].trim_start();
            let valor = resto.strip_prefix(':').unwrap_or("").trim_start();
            if valor.starts_with("null") || valor.starts_with("false") || valor.starts_with("{}") {
                return true;
            }
            // O formato do servidor em Python: {"ativo": false, "titulo": "", "id": ""}.
            let objeto = valor.split('}').next().unwrap_or("");
            objeto.starts_with('{') && objeto.replace(' ', "").contains("\"ativo\":false")
        }
    }
}

#[cfg(test)]
mod testes {
    use super::*;

    #[test]
    fn host_so_nomes_deste_aparelho() {
        assert!(host_confiavel(None));
        assert!(host_confiavel(Some("127.0.0.1:8777")));
        assert!(host_confiavel(Some("LOCALHOST:8777")));
        assert!(host_confiavel(Some("[::1]:8777")));
        assert!(!host_confiavel(Some("site-malvado.com:8777")));
        assert!(!host_confiavel(Some("127.0.0.1.site.com")));
    }

    #[test]
    fn cookie_do_android() {
        assert!(cookie_confere(Some("a=1; arena_segredo=abc123"), "abc123"));
        assert!(cookie_confere(Some("arena_segredo=\"abc123\""), "abc123"));
        assert!(!cookie_confere(Some("arena_segredo=abc124"), "abc123"));
        assert!(!cookie_confere(Some("outro=abc123"), "abc123"));
        assert!(!cookie_confere(None, "abc123"));
    }

    #[test]
    fn arquivo_da_tela_so_dentro_do_launcher() {
        let pasta = std::env::temp_dir().join(format!("arena_nativo_teste_{}", sistema::sorteio()));
        std::fs::create_dir_all(pasta.join("img")).unwrap();
        std::fs::write(pasta.join("index.html"), "x").unwrap();
        std::fs::write(pasta.join("img").join("a.png"), "x").unwrap();
        assert_eq!(arquivo_da_tela(&pasta, "/"), Some(pasta.join("index.html")));
        assert_eq!(arquivo_da_tela(&pasta, "/img/a.png"), Some(pasta.join("img").join("a.png")));
        assert_eq!(arquivo_da_tela(&pasta, "/../segredo.txt"), None);
        assert_eq!(arquivo_da_tela(&pasta, "/img/../index.html"), None);
        assert_eq!(arquivo_da_tela(&pasta, "/img\\a.png"), None);
        assert_eq!(arquivo_da_tela(&pasta, "/%2e%2e/x"), None);
        assert_eq!(arquivo_da_tela(&pasta, "/api/estado"), None);
        assert_eq!(arquivo_da_tela(&pasta, "/nao-existe.js"), None);
        let _ = std::fs::remove_dir_all(&pasta);
    }

    #[test]
    fn estado_com_jogo_nao_e_guardado() {
        assert!(sem_jogo_aberto(b"{\"jogo_em_andamento\": null, \"x\": 1}"));
        assert!(sem_jogo_aberto(b"{\"x\": 1}"));
        assert!(!sem_jogo_aberto(b"{\"jogo_em_andamento\": {\"titulo\": \"Mario\"}}"));
        assert!(sem_jogo_aberto(b"{\"jogo_em_andamento\": {\"ativo\": false, \"titulo\": \"\", \"id\": \"\"}}"));
        assert!(!sem_jogo_aberto(b"{\"jogo_em_andamento\": {\"ativo\": true, \"titulo\": \"Mario\", \"id\": \"3\"}}"));
    }

    #[test]
    fn config_da_rede() {
        let arquivo = std::env::temp_dir().join(format!("arena_nativo_cfg_{}.json", sistema::sorteio()));
        std::fs::write(&arquivo, "{\"tema\": \"x\", \"permitir_rede\" : true}").unwrap();
        assert_eq!(escuta_da_config(&arquivo), "0.0.0.0");
        std::fs::write(&arquivo, "{\"permitir_rede\": false}").unwrap();
        assert_eq!(escuta_da_config(&arquivo), "127.0.0.1");
        let _ = std::fs::remove_file(&arquivo);
        assert_eq!(escuta_da_config(Path::new("nao-existe.json")), "127.0.0.1");
    }

    #[test]
    fn cabecalhos_que_o_nativo_controla_saem() {
        assert!(fica_de_fora("X-Arena-Origem"));
        assert!(fica_de_fora("x-arena-proxy"));
        assert!(fica_de_fora("Connection"));
        assert!(!fica_de_fora("Host"));
        assert!(!fica_de_fora("Cookie"));
    }

    #[test]
    fn avisos_no_formato_do_server_sent_events() {
        let avisos = vec![
            (10, "catalogo".to_string(), "{\"geracao\":5}".to_string()),
            (11, "jogo".to_string(), "{}".to_string()),
        ];
        assert_eq!(
            texto_dos_avisos(&avisos),
            "id: 10\nevent: catalogo\ndata: {\"geracao\":5}\n\nid: 11\nevent: jogo\ndata: {}\n\n"
        );
        assert_eq!(texto_dos_avisos(&[]), "");
    }

    #[test]
    fn so_aviso_bem_formado_entra() {
        assert!(tipo_de_aviso_valido("catalogo"));
        assert!(tipo_de_aviso_valido("jogo_fechou"));
        assert!(!tipo_de_aviso_valido(""));
        assert!(!tipo_de_aviso_valido("Catalogo"));
        assert!(!tipo_de_aviso_valido("catalogo\nevent: x"));
        assert!(!tipo_de_aviso_valido(&"a".repeat(25)));
        assert!(dados_de_aviso_validos("{}"));
        assert!(dados_de_aviso_validos("{\"geracao\":1763140000000}"));
        assert!(!dados_de_aviso_validos("{\"a\":1}\ndata: {}"));
        assert!(!dados_de_aviso_validos("[1, 2]"));
        assert!(!dados_de_aviso_validos(&format!("{{\"a\":\"{}\"}}", "x".repeat(2100))));
    }

    #[test]
    fn so_a_propria_tela_ouve_os_avisos() {
        let pedido = |cabecalhos: &[(&str, &str)]| http::Pedido {
            metodo: "GET".to_string(),
            alvo: "/_nativo/eventos".to_string(),
            versao: "HTTP/1.1".to_string(),
            cabecalhos: cabecalhos.iter().map(|(n, v)| (n.to_string(), v.to_string())).collect(),
            corpo: Vec::new(),
        };
        assert!(da_propria_tela(&pedido(&[]), 8777));
        assert!(da_propria_tela(&pedido(&[("Sec-Fetch-Site", "same-origin")]), 8777));
        assert!(da_propria_tela(&pedido(&[("Origin", "http://127.0.0.1:8777")]), 8777));
        assert!(!da_propria_tela(&pedido(&[("Sec-Fetch-Site", "cross-site")]), 8777));
        assert!(!da_propria_tela(&pedido(&[("Origin", "https://site-malvado.com")]), 8777));
        assert!(!da_propria_tela(&pedido(&[("Origin", "http://127.0.0.1:9999")]), 8777));
    }

    #[test]
    fn de_onde_a_tela_continua() {
        assert_eq!(desde_onde(None, 500), 500);
        assert_eq!(desde_onde(Some("498"), 500), 498);
        assert_eq!(desde_onde(Some(" 500 "), 500), 500);
        // Numero do futuro (relogio que voltou) ou lixo: so os avisos novos.
        assert_eq!(desde_onde(Some("900"), 500), 500);
        assert_eq!(desde_onde(Some("abc"), 500), 500);
    }

    #[test]
    fn parametro_simples_da_consulta() {
        assert_eq!(valor_da_consulta("/_nativo/evento?tipo=catalogo", "tipo"), Some("catalogo"));
        assert_eq!(valor_da_consulta("/_nativo/evento?x=1&tipo=jogo", "tipo"), Some("jogo"));
        assert_eq!(valor_da_consulta("/_nativo/evento", "tipo"), None);
        assert_eq!(valor_da_consulta("/_nativo/evento?tipos=jogo", "tipo"), None);
    }

    #[test]
    fn numeracao_dos_avisos_comeca_na_hora() {
        // Setembro de 2026 em ms: a numeracao de uma abertura nova sempre passa a de uma anterior.
        assert!(agora_em_ms() > 1_790_000_000_000);
    }
}
