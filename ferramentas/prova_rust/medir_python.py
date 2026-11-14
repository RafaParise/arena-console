# -*- coding: utf-8 -*-
"""O gemeo em Python da prova em Rust (ferramentas/prova_rust/src/main.rs, Fase 3 do docs/PLANO-DE-ACAO-RUST.md).

Faz o mesmo trabalho da indexador.assinatura_das_pastas (percorrer as pastas de jogos e anotar a data de cada uma)
de dois jeitos: em sequencia, como o ARENA faz hoje (os.walk + getmtime), e em paralelo, por niveis, com threads
(o os.scandir e o os.stat soltam a trava do Python enquanto esperam o disco, entao as threads perguntam juntas).
So a biblioteca padrao; roda no Windows, no Linux, no Termux e no Python do APK.

Uso:  python medir_python.py <seq|walk|par> <vezes> <threads> <pasta> [<pasta> ...]
"""
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

ESCONDIDAS = {"$recycle.bin", "system volume information", "lost.dir"}


def escondida(nome):
    return nome.startswith(".") or nome.lower() in ESCONDIDAS


def ler_pasta(pasta):
    """(linha "caminho|data" ou None, subpastas em ordem): um stat e um scandir, como o Rust."""
    try:
        linha = "%s|%d" % (pasta, os.stat(pasta).st_mtime)
    except OSError:
        linha = None
    subpastas = []
    try:
        with os.scandir(pasta) as itens:
            for item in itens:
                try:
                    if item.is_dir() and not escondida(item.name):
                        subpastas.append(item.path)
                except OSError:
                    pass
    except OSError:
        pass
    subpastas.sort()
    return linha, subpastas


def com_walk(raizes):
    """O jeito de hoje do ARENA (indexador.assinatura_das_pastas)."""
    linhas = []
    for raiz in raizes:
        for pasta_atual, subpastas, _arquivos in os.walk(raiz):
            subpastas[:] = sorted(p for p in subpastas if not escondida(p))
            try:
                linhas.append("%s|%d" % (pasta_atual, os.path.getmtime(pasta_atual)))
            except OSError:
                continue
    return linhas


def sequencial(raizes):
    linhas, pilha = [], list(reversed(raizes))
    while pilha:
        linha, subpastas = ler_pasta(pilha.pop())
        if linha:
            linhas.append(linha)
        pilha.extend(reversed(subpastas))
    return linhas


def paralelo(raizes, threads):
    linhas, nivel = [], list(raizes)
    with ThreadPoolExecutor(max_workers=threads) as grupo:
        while nivel:
            proximo = []
            for linha, subpastas in grupo.map(ler_pasta, nivel):
                if linha:
                    linhas.append(linha)
                proximo.extend(subpastas)
            nivel = proximo
    return linhas


def resumo(linhas):
    """FNV-1a de 64 bits, igual ao do Rust (para conferir que viram as mesmas pastas)."""
    h = 0xcbf29ce484222325
    for linha in sorted(linhas):
        for b in linha.encode("utf-8") + b"\n":
            h = ((h ^ b) * 0x100000001b3) & 0xFFFFFFFFFFFFFFFF
    return h


def principal():
    if len(sys.argv) < 5:
        print(__doc__)
        return 2
    modo, vezes, threads = sys.argv[1], int(sys.argv[2]), max(1, int(sys.argv[3]))
    raizes = [p for p in sys.argv[4:] if os.path.isdir(p)]
    for rodada in range(1, vezes + 1):
        inicio = time.perf_counter()
        if modo == "par":
            linhas = paralelo(raizes, threads)
        elif modo == "walk":
            linhas = com_walk(raizes)
        else:
            linhas = sequencial(raizes)
        ms = (time.perf_counter() - inicio) * 1000
        print("python %s t=%d rodada %d: %.1f ms, %d pastas, resumo %016x"
              % (modo, threads, rodada, ms, len(linhas), resumo(linhas)), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(principal())
