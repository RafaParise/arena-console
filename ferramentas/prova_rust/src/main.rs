//! Prova da Fase 3 do docs/PLANO-DE-ACAO-RUST.md (14/11/2026): o mesmo trabalho da
//! `indexador.assinatura_das_pastas` do ARENA (percorrer as pastas de jogos e anotar a data de cada
//! uma), em Rust, para medir se a linguagem muda alguma coisa no trecho que a medicao apontou.
//! NAO faz parte do ARENA: e' uma ferramenta de medida (o ARENA continua em Python puro).
//!
//! Uso:  conferir_pastas <seq|par> <vezes> <threads> <pasta> [<pasta> ...]
//!   seq     = uma pasta de cada vez, como o os.walk do Python
//!   par     = por niveis: as pastas de um mesmo nivel divididas entre <threads> threads
//! Imprime, por rodada, o tempo em ms, quantas pastas viu e um resumo (para conferir que os dois modos
//! viram as mesmas pastas).

use std::fs;
use std::path::PathBuf;
use std::time::{Instant, UNIX_EPOCH};

/// As pastas que o ARENA pula (indexador.pasta_escondida): ocultas e as do sistema.
fn escondida(nome: &str) -> bool {
    nome.starts_with('.')
        || nome.eq_ignore_ascii_case("$RECYCLE.BIN")
        || nome.eq_ignore_ascii_case("System Volume Information")
        || nome.eq_ignore_ascii_case("LOST.DIR")
}

/// Le uma pasta: (a linha "caminho|data", as subpastas). Uma pergunta da data (stat) e uma leitura
/// da lista (readdir), igual ao Python: o tipo de cada item vem junto com a lista (d_type).
fn ler_pasta(pasta: &PathBuf) -> (Option<String>, Vec<PathBuf>) {
    let linha = fs::metadata(pasta)
        .and_then(|m| m.modified())
        .ok()
        .and_then(|t| t.duration_since(UNIX_EPOCH).ok())
        .map(|d| format!("{}|{}", pasta.display(), d.as_secs()));
    let mut subpastas = Vec::new();
    if let Ok(itens) = fs::read_dir(pasta) {
        for item in itens.flatten() {
            let eh_pasta = item.file_type().map(|t| t.is_dir()).unwrap_or(false);
            if eh_pasta && !escondida(&item.file_name().to_string_lossy()) {
                subpastas.push(item.path());
            }
        }
    }
    subpastas.sort();
    (linha, subpastas)
}

fn sequencial(raizes: &[PathBuf]) -> Vec<String> {
    let mut linhas = Vec::new();
    let mut pilha: Vec<PathBuf> = raizes.iter().rev().cloned().collect();
    while let Some(pasta) = pilha.pop() {
        let (linha, subpastas) = ler_pasta(&pasta);
        linhas.extend(linha);
        pilha.extend(subpastas.into_iter().rev());
    }
    linhas
}

fn paralelo(raizes: &[PathBuf], threads: usize) -> Vec<String> {
    let mut linhas = Vec::new();
    let mut nivel: Vec<PathBuf> = raizes.to_vec();
    while !nivel.is_empty() {
        let tamanho = nivel.len().div_ceil(threads).max(1);
        let resultados: Vec<(Vec<String>, Vec<PathBuf>)> = std::thread::scope(|s| {
            let tarefas: Vec<_> = nivel
                .chunks(tamanho)
                .map(|pedaco| {
                    s.spawn(move || {
                        let mut l = Vec::new();
                        let mut sub = Vec::new();
                        for pasta in pedaco {
                            let (linha, subpastas) = ler_pasta(pasta);
                            l.extend(linha);
                            sub.extend(subpastas);
                        }
                        (l, sub)
                    })
                })
                .collect();
            tarefas.into_iter().map(|t| t.join().unwrap()).collect()
        });
        nivel = Vec::new();
        for (l, sub) in resultados {
            linhas.extend(l);
            nivel.extend(sub);
        }
    }
    linhas
}

/// FNV-1a de 64 bits das linhas em ordem: so para ver que os dois modos viram o mesmo.
fn resumo(linhas: &mut Vec<String>) -> u64 {
    linhas.sort();
    let mut h: u64 = 0xcbf29ce484222325;
    for l in linhas.iter() {
        for b in l.bytes().chain(std::iter::once(b'\n')) {
            h ^= b as u64;
            h = h.wrapping_mul(0x100000001b3);
        }
    }
    h
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 5 {
        eprintln!("uso: conferir_pastas <seq|par> <vezes> <threads> <pasta> [<pasta> ...]");
        std::process::exit(2);
    }
    let modo = args[1].as_str();
    let vezes: usize = args[2].parse().unwrap_or(5);
    let threads: usize = args[3].parse().unwrap_or(4).max(1);
    let raizes: Vec<PathBuf> = args[4..].iter().map(PathBuf::from).filter(|p| p.is_dir()).collect();
    for rodada in 1..=vezes {
        let inicio = Instant::now();
        let mut linhas = if modo == "par" { paralelo(&raizes, threads) } else { sequencial(&raizes) };
        let ms = inicio.elapsed().as_secs_f64() * 1000.0;
        let r = resumo(&mut linhas);
        println!("rust {} t={} rodada {}: {:.1} ms, {} pastas, resumo {:016x}", modo, threads, rodada, ms,
                 linhas.len(), r);
    }
}
