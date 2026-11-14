# -*- coding: utf-8 -*-
r"""Compila o servidor nativo do ARENA (Rust, pasta nativo\) para todos os sistemas e poe cada um no lugar.

Por que existe (14/11/2026, docs\MIGRACAO-RUST.md): o nativo vai na frente do servidor em Python no Windows, no Linux
(x86-64 e ARM64) e no Android. Quem compila e' o PC de quem monta o pacote; o aluno nunca compila nada.

  Windows       x86_64-pc-windows-gnullvm   -> servidor\arena-nativo.exe
  Linux x86-64  x86_64-unknown-linux-musl   -> servidor\arena-nativo-linux-x86_64   (e o APK x86_64)
  Linux ARM64   aarch64-unknown-linux-musl  -> servidor\arena-nativo-linux-aarch64  (e o APK arm64-v8a)

Os do Linux sao estaticos (musl): rodam em qualquer Linux e no Android sem depender das bibliotecas do sistema. O do
Windows usa so as DLLs que ja vem no Windows 10 e 11 (a UCRT). Ferramentas, todas gratuitas e sem administrador:
o Rust (rustup, com os tres alvos) e o llvm-mingw portatil (github.com/mstorsjo/llvm-mingw) em C:\Projetos\ferramentas,
que faz o papel do linker do Windows (sem o Visual Studio). Os do Linux ligam com o rust-lld, que vem com o Rust.

Uso:  servidor\python\python.exe ferramentas\compilar_nativo.py [--sem-testes]
"""
import glob
import os
import shutil
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA = os.path.join(RAIZ, "nativo")
ALVOS = [
    ("x86_64-pc-windows-gnullvm", "arena-nativo.exe", "arena-nativo.exe"),
    ("x86_64-unknown-linux-musl", "arena-nativo", "arena-nativo-linux-x86_64"),
    ("aarch64-unknown-linux-musl", "arena-nativo", "arena-nativo-linux-aarch64"),
]


def achar_cargo():
    for lugar in (shutil.which("cargo"), os.path.join(os.path.expanduser("~"), ".cargo", "bin", "cargo.exe")):
        if lugar and os.path.isfile(lugar):
            return lugar
    raise SystemExit("Falta o Rust neste computador (rustup.rs, gratuito). Instale e rode de novo.")


def achar_llvm_mingw():
    """A pasta bin do llvm-mingw mais novo em C:\\Projetos\\ferramentas (ou no LLVM_MINGW)."""
    candidatos = [os.environ.get("LLVM_MINGW", "")]
    candidatos += sorted(glob.glob(os.path.join(os.path.dirname(RAIZ), "ferramentas", "llvm-mingw-*")), reverse=True)
    for pasta in candidatos:
        clang = os.path.join(pasta, "bin", "x86_64-w64-mingw32-clang.exe")
        if pasta and os.path.isfile(clang):
            return clang
    raise SystemExit("Falta o llvm-mingw (github.com/mstorsjo/llvm-mingw, o zip ucrt-x86_64) em C:\\Projetos\\ferramentas."
                     " Ele faz o papel do linker do Windows; baixe, extraia la e rode de novo.")


def ambiente(alvo, clang):
    extra = dict(os.environ)
    if "windows" in alvo:
        extra["CARGO_TARGET_X86_64_PC_WINDOWS_GNULLVM_LINKER"] = clang
    else:
        extra["CARGO_TARGET_%s_LINKER" % alvo.upper().replace("-", "_")] = "rust-lld"
    return extra


def rodar(comando, extra):
    feito = subprocess.run(comando, cwd=PASTA, env=extra, capture_output=True, text=True, encoding="utf-8",
                           errors="replace")
    if feito.returncode != 0:
        raise SystemExit("Falhou: %s\n%s" % (" ".join(comando), (feito.stdout + feito.stderr)[-3000:]))
    return feito.stdout + feito.stderr


def principal():
    cargo = achar_cargo()
    clang = achar_llvm_mingw()
    instalados = subprocess.run(["rustup", "target", "list", "--installed"], capture_output=True, text=True).stdout
    for alvo, _, _ in ALVOS:
        if alvo not in instalados:
            rodar(["rustup", "target", "add", alvo], dict(os.environ))
    if "--sem-testes" not in sys.argv:
        saida = rodar([cargo, "test", "--release", "--target", ALVOS[0][0]], ambiente(ALVOS[0][0], clang))
        resumo = [linha for linha in saida.splitlines() if linha.startswith("test result")]
        print("  testes do nativo: %s" % ("; ".join(resumo) or "?"), flush=True)
    for alvo, nome, destino in ALVOS:
        rodar([cargo, "build", "--release", "--target", alvo], ambiente(alvo, clang))
        origem = os.path.join(PASTA, "target", alvo, "release", nome)
        final = os.path.join(RAIZ, "servidor", destino)
        shutil.copyfile(origem, final + ".parcial")
        os.replace(final + ".parcial", final)
        print("  %-28s -> servidor\\%s (%d KB)" % (alvo, destino, os.path.getsize(final) // 1024), flush=True)
    print("Pronto. O ARENA.bat, o ARENA.sh e o APK (montar_android.py) passam a abrir pelo nativo.")
    return 0


if __name__ == "__main__":
    sys.exit(principal())
