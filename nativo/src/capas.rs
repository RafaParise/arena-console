//! As capas dos jogos (/api/capa), entregues pelo nativo (etapa R2 de docs/MIGRACAO-RUST.md, 14/11/2026).
//!
//! Por que: na abertura do Galaxy A12, a lista aparece pelo nativo antes de o Python terminar de abrir, mas as capas
//! ainda esperavam o Python; e, rolando a lista, cada capa custava um pedido ao Python. Aqui vale a MESMA regra do
//! servidor em Python (arena.capa_permitida e arena.miniatura_pronta):
//!   - so imagem (.png, .jpg, .jpeg, .webp) dentro de jogos/ ou de retroarch/thumbnails/;
//!   - com "mini=280" ou "mini=480", a miniatura guardada em dados/miniaturas, se ja existir (o nome dela e' o
//!     SHA-1 de "caminho|tamanho|data|largura", como no Python); senao, a capa cheia (a tela faz a miniatura e o
//!     Python a guarda: o POST /api/capa/miniatura continua no Python).
//! Qualquer pedido fora do caminho simples (nome estranho, "..", arquivo que nao existe) volta como None: o nativo
//! repassa ao Python, que responde o erro de sempre. O nativo so e' mais rigido que o Python, nunca mais solto.

use std::path::{Path, PathBuf};
use std::time::UNIX_EPOCH;

const LARGURAS_MINIATURA: [u32; 2] = [280, 480];

/// (bytes da imagem, tipo) da capa pedida em "alvo" (o "/api/capa?..." inteiro), ou None para o Python responder.
pub fn capa(raiz: &Path, alvo: &str) -> Option<(Vec<u8>, &'static str)> {
    let consulta = alvo.split_once('?').map(|(_, c)| c).unwrap_or("");
    let consulta = consulta.split('#').next().unwrap_or("");
    let arquivo = primeiro_valor(consulta, "arquivo")?;
    let largura: u32 = primeiro_valor(consulta, "mini").and_then(|m| m.trim().parse().ok()).unwrap_or(0);
    let partes = partes_simples(&arquivo)?;
    let dentro = partes[0] == "jogos" && partes.len() >= 2
        || partes.len() >= 3 && partes[0] == "retroarch" && partes[1] == "thumbnails";
    if !dentro {
        return None;
    }
    tipo_da_imagem(partes.last()?)?;
    let mut caminho = raiz.to_path_buf();
    for parte in &partes {
        caminho.push(parte);
    }
    if !caminho.is_file() {
        return None;
    }
    let servido = if LARGURAS_MINIATURA.contains(&largura) {
        miniatura_pronta(raiz, &partes, &caminho, largura).unwrap_or(caminho)
    } else {
        caminho
    };
    let tipo = tipo_da_imagem(servido.file_name()?.to_str()?)?;
    let corpo = std::fs::read(&servido).ok()?;
    Some((corpo, tipo))
}

fn tipo_da_imagem(nome: &str) -> Option<&'static str> {
    let minusculo = nome.to_ascii_lowercase();
    if minusculo.ends_with(".png") {
        Some("image/png")
    } else if minusculo.ends_with(".jpg") || minusculo.ends_with(".jpeg") {
        Some("image/jpeg")
    } else if minusculo.ends_with(".webp") {
        Some("image/webp")
    } else {
        None
    }
}

/// O caminho "jogos/x/y.png" em partes, so se cada parte for um nome simples (sem "..", ".", vazio, barra
/// invertida, dois-pontos ou caractere de controle). Senao None: o Python decide.
fn partes_simples(caminho: &str) -> Option<Vec<String>> {
    let mut partes = Vec::new();
    for parte in caminho.split('/') {
        if parte.is_empty()
            || parte == "."
            || parte == ".."
            || parte.chars().any(|c| c == '\\' || c == ':' || c.is_control())
        {
            return None;
        }
        partes.push(parte.to_string());
    }
    if partes.is_empty() {
        None
    } else {
        Some(partes)
    }
}

/// dados/miniaturas/<24 letras do SHA-1>.<webp|jpg|png>, como o arena.base_da_miniatura do Python: o texto e'
/// "caminho relativo em minusculas|tamanho|data (segundos)|largura", com a barra do sistema (\ no Windows).
fn miniatura_pronta(raiz: &Path, partes: &[String], capa: &Path, largura: u32) -> Option<PathBuf> {
    let estado = std::fs::metadata(capa).ok()?;
    let data = estado.modified().ok()?.duration_since(UNIX_EPOCH).ok()?.as_secs();
    let separador = if cfg!(windows) { "\\" } else { "/" };
    let relativo = partes.join(separador).to_lowercase();
    let texto = format!("{}|{}|{}|{}", relativo, estado.len(), data, largura);
    let codigo: String = sha1_hex(texto.as_bytes()).chars().take(24).collect();
    let pasta = raiz.join("dados").join("miniaturas");
    for extensao in [".webp", ".jpg", ".png"] {
        let candidato = pasta.join(format!("{}{}", codigo, extensao));
        if candidato.is_file() {
            return Some(candidato);
        }
    }
    None
}

/// O primeiro valor nao vazio de "nome" na consulta, decodificado como o parse_qs do Python (%XX em UTF-8 e
/// "+" vira espaco). None se faltar ou se a decodificacao der texto invalido.
fn primeiro_valor(consulta: &str, nome: &str) -> Option<String> {
    for par in consulta.split('&') {
        let (chave, valor) = par.split_once('=').unwrap_or((par, ""));
        if decodificar(chave).as_deref() == Some(nome) {
            let valor = decodificar(valor)?;
            if !valor.is_empty() {
                return Some(valor);
            }
        }
    }
    None
}

fn decodificar(texto: &str) -> Option<String> {
    let bytes = texto.as_bytes();
    let mut saida = Vec::with_capacity(bytes.len());
    let mut i = 0;
    while i < bytes.len() {
        match bytes[i] {
            b'+' => {
                saida.push(b' ');
                i += 1;
            }
            b'%' if i + 2 < bytes.len() => {
                let alto = (bytes[i + 1] as char).to_digit(16);
                let baixo = (bytes[i + 2] as char).to_digit(16);
                match (alto, baixo) {
                    (Some(a), Some(b)) => {
                        saida.push((a * 16 + b) as u8);
                        i += 3;
                    }
                    _ => {
                        saida.push(b'%');
                        i += 1;
                    }
                }
            }
            b => {
                saida.push(b);
                i += 1;
            }
        }
    }
    String::from_utf8(saida).ok()
}

/// SHA-1 (FIPS 180-4) em hexadecimal. Aqui nao serve de seguranca: e' so o nome da miniatura, o mesmo que o
/// hashlib.sha1 do Python calcula, para os dois acharem o mesmo arquivo.
pub fn sha1_hex(dados: &[u8]) -> String {
    let mut h: [u32; 5] = [0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476, 0xC3D2E1F0];
    let mut mensagem = dados.to_vec();
    let bits = (dados.len() as u64).wrapping_mul(8);
    mensagem.push(0x80);
    while mensagem.len() % 64 != 56 {
        mensagem.push(0);
    }
    mensagem.extend_from_slice(&bits.to_be_bytes());
    for bloco in mensagem.chunks(64) {
        let mut w = [0u32; 80];
        for (i, palavra) in bloco.chunks(4).enumerate() {
            w[i] = u32::from_be_bytes([palavra[0], palavra[1], palavra[2], palavra[3]]);
        }
        for i in 16..80 {
            w[i] = (w[i - 3] ^ w[i - 8] ^ w[i - 14] ^ w[i - 16]).rotate_left(1);
        }
        let (mut a, mut b, mut c, mut d, mut e) = (h[0], h[1], h[2], h[3], h[4]);
        for (i, valor) in w.iter().enumerate() {
            let (f, k) = match i {
                0..=19 => ((b & c) | (!b & d), 0x5A827999),
                20..=39 => (b ^ c ^ d, 0x6ED9EBA1),
                40..=59 => ((b & c) | (b & d) | (c & d), 0x8F1BBCDC),
                _ => (b ^ c ^ d, 0xCA62C1D6),
            };
            let temp = a.rotate_left(5).wrapping_add(f).wrapping_add(e).wrapping_add(k).wrapping_add(*valor);
            e = d;
            d = c;
            c = b.rotate_left(30);
            b = a;
            a = temp;
        }
        h[0] = h[0].wrapping_add(a);
        h[1] = h[1].wrapping_add(b);
        h[2] = h[2].wrapping_add(c);
        h[3] = h[3].wrapping_add(d);
        h[4] = h[4].wrapping_add(e);
    }
    h.iter().map(|x| format!("{:08x}", x)).collect()
}

#[cfg(test)]
mod testes {
    use super::*;

    #[test]
    fn sha1_dos_vetores_oficiais() {
        assert_eq!(sha1_hex(b""), "da39a3ee5e6b4b0d3255bfef95601890afd80709");
        assert_eq!(sha1_hex(b"abc"), "a9993e364706816aba3e25717850c26c9cd0d89d");
        assert_eq!(
            sha1_hex(b"abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq"),
            "84983e441c3bd26ebaae4aa1f95129e5e54670f1"
        );
        // O mesmo que o Python: hashlib.sha1("jogos/snes/capas/ação.png|1|2|280".encode("utf-8")).hexdigest()
        assert_eq!(sha1_hex("jogos/snes/capas/ação.png|1|2|280".as_bytes()), "079619a2b3c3d77d6d59c0416ce6c4d8bee6b086");
        // Mais de um bloco de 64 bytes (o texto da miniatura de um caminho comprido).
        assert_eq!(sha1_hex(&[b'a'; 1000]), "291e9a6c66994949b57ba5e650361e98fc36b1ba");
    }

    #[test]
    fn consulta_como_o_parse_qs() {
        assert_eq!(primeiro_valor("arquivo=jogos/a%20b%C3%A7.png&mini=280", "arquivo").as_deref(),
                   Some("jogos/a bç.png"));
        assert_eq!(primeiro_valor("arquivo=jogos/a+b.png", "arquivo").as_deref(), Some("jogos/a b.png"));
        assert_eq!(primeiro_valor("arquivo=&arquivo=jogos/x.png", "arquivo").as_deref(), Some("jogos/x.png"));
        assert_eq!(primeiro_valor("mini=280", "arquivo"), None);
        assert_eq!(primeiro_valor("arquivo=%FF", "arquivo"), None); // UTF-8 invalido: o Python decide
        assert_eq!(decodificar("100%").as_deref(), Some("100%"));
    }

    #[test]
    fn so_caminho_simples_dentro_das_pastas() {
        let raiz = std::env::temp_dir().join(format!("arena_capas_{}", crate::sistema::sorteio()));
        std::fs::create_dir_all(raiz.join("jogos").join("snes").join("capas")).unwrap();
        std::fs::create_dir_all(raiz.join("dados")).unwrap();
        std::fs::write(raiz.join("jogos").join("snes").join("capas").join("Mario.png"), b"png").unwrap();
        std::fs::write(raiz.join("dados").join("config.json"), b"{}").unwrap();
        let (corpo, tipo) = capa(&raiz, "/api/capa?arquivo=jogos/snes/capas/Mario.png&mini=280").unwrap();
        assert_eq!((corpo.as_slice(), tipo), (&b"png"[..], "image/png"));
        assert!(capa(&raiz, "/api/capa?arquivo=dados/config.json").is_none());
        assert!(capa(&raiz, "/api/capa?arquivo=jogos/../dados/config.json").is_none());
        assert!(capa(&raiz, "/api/capa?arquivo=jogos%2F..%2Fdados%2Fconfig.json").is_none());
        assert!(capa(&raiz, "/api/capa?arquivo=jogos\\snes\\capas\\Mario.png").is_none());
        assert!(capa(&raiz, "/api/capa?arquivo=C:/Windows/win.ini").is_none());
        assert!(capa(&raiz, "/api/capa?arquivo=jogos/snes/capas/nao-existe.png").is_none());
        assert!(capa(&raiz, "/api/capa").is_none());
        let _ = std::fs::remove_dir_all(&raiz);
    }

    #[test]
    fn miniatura_guardada_pelo_mesmo_nome_do_python() {
        let raiz = std::env::temp_dir().join(format!("arena_mini_{}", crate::sistema::sorteio()));
        let pasta = raiz.join("jogos").join("snes");
        std::fs::create_dir_all(&pasta).unwrap();
        std::fs::create_dir_all(raiz.join("dados").join("miniaturas")).unwrap();
        let capa_cheia = pasta.join("Mario.png");
        std::fs::write(&capa_cheia, b"capa cheia").unwrap();
        let estado = std::fs::metadata(&capa_cheia).unwrap();
        let data = estado.modified().unwrap().duration_since(UNIX_EPOCH).unwrap().as_secs();
        let separador = if cfg!(windows) { "\\" } else { "/" };
        let texto = format!("jogos{}snes{}mario.png|{}|{}|280", separador, separador, estado.len(), data);
        let codigo: String = sha1_hex(texto.as_bytes()).chars().take(24).collect();
        std::fs::write(raiz.join("dados").join("miniaturas").join(format!("{}.webp", codigo)), b"mini").unwrap();
        let (corpo, tipo) = capa(&raiz, "/api/capa?arquivo=jogos/snes/Mario.png&mini=280").unwrap();
        assert_eq!((corpo.as_slice(), tipo), (&b"mini"[..], "image/webp"));
        let (corpo, _) = capa(&raiz, "/api/capa?arquivo=jogos/snes/Mario.png&mini=480").unwrap();
        assert_eq!(corpo.as_slice(), b"capa cheia"); // sem a de 480 guardada, a cheia
        let _ = std::fs::remove_dir_all(&raiz);
    }
}
