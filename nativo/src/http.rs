//! O pedaco do HTTP/1.1 que o ARENA usa: ler um pedido (linha, cabecalhos e corpo) e escrever uma resposta.
//! So para conversa local (a tela do ARENA e os colegas da rede); nada de HTTPS nem de corpo "chunked" no pedido
//! (o fetch do navegador sempre manda o Content-Length).

use std::io::{self, BufRead, BufReader, Read, Write};
use std::net::TcpStream;

/// O maior cabecalho aceito (o do navegador tem uns 600 bytes).
const LIMITE_CABECALHO: usize = 64 * 1024;
/// O maior corpo aceito: o mesmo teto do servidor em Python (Manipulador.LIMITE_CORPO, 64 MB).
pub const LIMITE_CORPO: usize = 64 * 1024 * 1024;

pub struct Pedido {
    pub metodo: String,
    /// O alvo como veio ("/api/estado?x=1"): o Python recebe igualzinho.
    pub alvo: String,
    pub versao: String,
    /// Cabecalhos na ordem em que vieram (nome como veio, valor sem espacos nas pontas).
    pub cabecalhos: Vec<(String, String)>,
    pub corpo: Vec<u8>,
}

impl Pedido {
    /// O caminho, sem a parte do "?": o mesmo que o urlparse(...).path do Python (sem decodificar o %XX).
    pub fn caminho(&self) -> &str {
        self.alvo.split(['?', '#']).next().unwrap_or("")
    }

    pub fn cabecalho(&self, nome: &str) -> Option<&str> {
        self.cabecalhos
            .iter()
            .find(|(n, _)| n.eq_ignore_ascii_case(nome))
            .map(|(_, v)| v.as_str())
    }

    /// O navegador pediu para manter a conexao aberta (o padrao do HTTP/1.1)?
    pub fn manter_aberta(&self) -> bool {
        match self.cabecalho("Connection") {
            Some(v) if v.eq_ignore_ascii_case("close") => false,
            Some(v) if v.eq_ignore_ascii_case("keep-alive") => true,
            _ => self.versao == "HTTP/1.1",
        }
    }
}

/// Le o proximo pedido da conexao. Ok(None) quando o outro lado fechou sem mandar nada (fim normal).
pub fn ler_pedido(leitor: &mut BufReader<TcpStream>) -> io::Result<Option<Pedido>> {
    let mut linha = String::new();
    let mut lidos = 0usize;
    // Linhas em branco antes do pedido sao toleradas (RFC 9112, 2.2).
    loop {
        linha.clear();
        let n = leitor.read_line(&mut linha)?;
        if n == 0 {
            return Ok(None);
        }
        lidos += n;
        if !linha.trim().is_empty() {
            break;
        }
        if lidos > LIMITE_CABECALHO {
            return Err(invalido("pedido sem a primeira linha"));
        }
    }
    let mut partes = linha.trim_end().splitn(3, ' ');
    let metodo = partes.next().unwrap_or("").to_string();
    let alvo = partes.next().unwrap_or("").to_string();
    let versao = partes.next().unwrap_or("HTTP/1.0").to_string();
    if metodo.is_empty() || !alvo.starts_with('/') {
        return Err(invalido("primeira linha do pedido estranha"));
    }
    let mut cabecalhos = Vec::new();
    loop {
        linha.clear();
        let n = leitor.read_line(&mut linha)?;
        if n == 0 {
            return Err(invalido("conexao fechou no meio dos cabecalhos"));
        }
        lidos += n;
        if lidos > LIMITE_CABECALHO {
            return Err(invalido("cabecalho grande demais"));
        }
        let texto = linha.trim_end_matches(['\r', '\n']);
        if texto.is_empty() {
            break;
        }
        if let Some((nome, valor)) = texto.split_once(':') {
            cabecalhos.push((nome.trim().to_string(), valor.trim().to_string()));
        }
    }
    let mut pedido = Pedido { metodo, alvo, versao, cabecalhos, corpo: Vec::new() };
    if pedido
        .cabecalho("Transfer-Encoding")
        .map(|v| !v.eq_ignore_ascii_case("identity"))
        .unwrap_or(false)
    {
        return Err(invalido("corpo em pedacos (chunked) nao e' aceito"));
    }
    let tamanho: usize = match pedido.cabecalho("Content-Length") {
        Some(v) => v.parse().map_err(|_| invalido("Content-Length estranho"))?,
        None => 0,
    };
    if tamanho > LIMITE_CORPO {
        return Err(invalido("corpo grande demais"));
    }
    if tamanho > 0 {
        let mut corpo = vec![0u8; tamanho];
        leitor.read_exact(&mut corpo)?;
        pedido.corpo = corpo;
    }
    Ok(Some(pedido))
}

fn invalido(texto: &str) -> io::Error {
    io::Error::new(io::ErrorKind::InvalidData, texto.to_string())
}

/// Escreve uma resposta inteira (cabecalhos e corpo) de uma vez.
pub fn responder(
    saida: &mut impl Write,
    codigo: u16,
    tipo: &str,
    extras: &[(&str, &str)],
    corpo: &[u8],
    manter_aberta: bool,
) -> io::Result<()> {
    let mut cabeca = format!(
        "HTTP/1.1 {} {}\r\nContent-Type: {}\r\nContent-Length: {}\r\n",
        codigo,
        frase_do_codigo(codigo),
        tipo,
        corpo.len()
    );
    for (nome, valor) in extras {
        cabeca.push_str(nome);
        cabeca.push_str(": ");
        cabeca.push_str(valor);
        cabeca.push_str("\r\n");
    }
    cabeca.push_str(if manter_aberta { "Connection: keep-alive\r\n\r\n" } else { "Connection: close\r\n\r\n" });
    // Cabecalho e corpo num envio so: menos pacotes na rede local.
    let mut tudo = Vec::with_capacity(cabeca.len() + corpo.len());
    tudo.extend_from_slice(cabeca.as_bytes());
    tudo.extend_from_slice(corpo);
    saida.write_all(&tudo)?;
    saida.flush()
}

/// Resposta de erro no mesmo formato do servidor em Python ({"ok": false, "erro": "..."}), sempre dizendo o que
/// fazer (regra do ARENA: toda mensagem de erro explica a saida).
pub fn responder_erro(saida: &mut impl Write, codigo: u16, mensagem: &str) -> io::Result<()> {
    let corpo = format!("{{\"ok\": false, \"erro\": \"{}\"}}", escapar_json(mensagem));
    responder(
        saida,
        codigo,
        "application/json; charset=utf-8",
        &[("Cache-Control", "no-store")],
        corpo.as_bytes(),
        false,
    )
}

pub fn escapar_json(texto: &str) -> String {
    let mut saida = String::with_capacity(texto.len() + 8);
    for c in texto.chars() {
        match c {
            '"' => saida.push_str("\\\""),
            '\\' => saida.push_str("\\\\"),
            '\n' => saida.push_str("\\n"),
            '\r' => saida.push_str("\\r"),
            '\t' => saida.push_str("\\t"),
            c if (c as u32) < 0x20 => saida.push_str(&format!("\\u{:04x}", c as u32)),
            c => saida.push(c),
        }
    }
    saida
}

fn frase_do_codigo(codigo: u16) -> &'static str {
    match codigo {
        200 => "OK",
        204 => "No Content",
        304 => "Not Modified",
        400 => "Bad Request",
        403 => "Forbidden",
        404 => "Not Found",
        405 => "Method Not Allowed",
        413 => "Payload Too Large",
        500 => "Internal Server Error",
        502 => "Bad Gateway",
        503 => "Service Unavailable",
        504 => "Gateway Timeout",
        _ => "OK",
    }
}

#[cfg(test)]
mod testes {
    use super::*;

    #[test]
    fn escapa_aspas_barra_e_controle() {
        assert_eq!(escapar_json("a\"b\\c\nd\u{1}"), "a\\\"b\\\\c\\nd\\u0001");
    }

    #[test]
    fn caminho_sem_consulta() {
        let p = Pedido {
            metodo: "GET".into(),
            alvo: "/api/capa?id=3#x".into(),
            versao: "HTTP/1.1".into(),
            cabecalhos: vec![("connection".into(), "Close".into())],
            corpo: vec![],
        };
        assert_eq!(p.caminho(), "/api/capa");
        assert!(!p.manter_aberta());
        assert_eq!(p.cabecalho("CONNECTION"), Some("Close"));
    }
}
