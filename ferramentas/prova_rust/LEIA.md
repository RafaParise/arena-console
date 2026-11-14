# Prova em Rust (Fase 3 do `docs/PLANO-DE-ACAO-RUST.md`)

Não faz parte do ARENA, que continua em Python puro. É uma ferramenta de medida: o mesmo trabalho da
`indexador.assinatura_das_pastas` (percorrer as pastas de jogos e anotar a data de cada uma), escrito em Rust só com a
biblioteca padrão, e o gêmeo em Python (`medir_python.py`), para separar o que é da linguagem e o que é do jeito de
fazer. Os números e a conclusão estão em `docs/DESEMPENHO-SERVIDOR.md` (seção "Fase 3").

Compilar para o celular ou a TV Box (ARM de 64 bits, programa estático, sem precisar do NDK):

    rustup target add aarch64-unknown-linux-musl
    set RUSTFLAGS=-C linker=rust-lld
    cargo build --release --target aarch64-unknown-linux-musl

Rodar (no `adb shell`, no Termux ou no Linux):

    conferir_pastas seq 5 1 /storage/XXXX-XXXX/ARENA-jogos      (uma pasta de cada vez)
    conferir_pastas par 5 8 /storage/XXXX-XXXX/ARENA-jogos      (8 pastas ao mesmo tempo)
    python medir_python.py walk 5 1 <pasta>                     (o jeito antigo do ARENA)
    python medir_python.py par 5 8 <pasta>                      (o jeito novo, com threads)

O "resumo" impresso tem que sair igual nos quatro: é a prova de que todos viram as mesmas pastas.
