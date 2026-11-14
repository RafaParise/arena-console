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

mod http;
mod sistema;

use std::collections::HashMap;
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

struct Arena {
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
}

fn main() {
    let inicio = Instant::now();
    let argumentos: Vec<String> = std::env::args().skip(1).collect();
    if argumentos.is_empty() {
        eprintln!("Uso: arena-nativo <programa do Python> [argumentos...]");
        std::process::exit(2);
    }
    sistema::ignorar_ctrl_c();
    let raiz = std::env::current_dir().unwrap_or_else(|_| PathBuf::from("."));
    let porta: u16 = std::env::var("ARENA_PORTA").ok().and_then(|p| p.parse().ok()).unwrap_or(8777);
    let porta_python = porta_livre().unwrap_or(porta.wrapping_add(1));
    let segredo_android = std::env::var("ARENA_ANDROID_SEGREDO").ok().filter(|s| !s.is_empty());
    let pasta_guardada = raiz.join("dados").join("nativo");
    let arena = Arc::new(Arena {
        launcher: raiz.join("launcher"),
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
                "[ARENA] Nativo: o Python ficou pronto em {} ms.",
                arena.inicio.elapsed().as_millis()
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
            // O que estava guardado, so enquanto o Python ainda carrega.
            if !*arena.python_pronto.lock().unwrap() {
                let guardada = arena.guardadas.lock().unwrap().get(caminho.as_str()).cloned();
                if let Some(corpo) = guardada {
                    http::responder(
                        &mut escrita,
                        200,
                        "application/json; charset=utf-8",
                        &[("Cache-Control", "no-store"), ("X-Arena-Guardado", "1")],
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
    saida_cabeca.push_str("Connection: close\r\n\r\n");
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
}
