# -*- coding: utf-8 -*-
r"""Auditoria 2, Fase 2: toda chave de opcao que o graficos.json manda para um
nucleo existe de verdade nesse nucleo?

Chave que o nucleo nao conhece nao faz nada -- so engorda o arquivo de
opcoes que o ARENA grava a cada jogo, e da a falsa impressao de que um
ajuste esta valendo. Confere lendo o texto de dentro de cada
retroarch\cores\<nucleo>_libretro.dll (as chaves de opcao ficam escritas la).

Uso:
    servidor\python\python.exe testes\chaves_graficos_vs_nucleos.py
Sai com codigo 1 se achar chave inexistente.
"""
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORES = os.path.join(RAIZ, "retroarch", "cores")


def chaves_por_nucleo(dados):
    """{nucleo: {chave: [onde aparece no graficos.json]}}"""
    saida = {}

    def anotar(nucleo, opcoes, onde):
        for chave in opcoes:
            saida.setdefault(nucleo, {}).setdefault(chave, []).append(onde)

    for nucleo, info in dados.get("nucleos", {}).items():
        anotar(nucleo, info.get("sempre", {}), "sempre")
        for bloco in info.get("por_nota", []):
            anotar(nucleo, bloco.get("opcoes", {}), "nota %s" % bloco.get("nota_minima"))
    for nucleo, opcoes in dados.get("modesto", {}).items():
        if isinstance(opcoes, dict):
            anotar(nucleo, opcoes, "modesto")
    for nucleo, excecao in dados.get("excecoes", {}).items():
        for bloco in excecao.get("por_nota", []) if isinstance(excecao, dict) else []:
            anotar(nucleo, bloco.get("opcoes", {}), "excecao nota %s" % bloco.get("nota_minima"))
    # Degrau "tela 4K" (01/10/2026): chave errada ali nao faria nada, calada.
    for nucleo, opcoes in dados.get("tela_4k", {}).get("nucleos", {}).items():
        anotar(nucleo, opcoes, "tela 4K")
    return saida


def principal():
    dados = json.load(open(os.path.join(RAIZ, "servidor", "graficos.json"), encoding="utf-8"))
    total, inexistentes, sem_nucleo = 0, {}, []
    for nucleo, chaves in sorted(chaves_por_nucleo(dados).items()):
        dll = os.path.join(CORES, nucleo + "_libretro.dll")
        if not os.path.isfile(dll):
            sem_nucleo.append(nucleo)
            continue
        conteudo = open(dll, "rb").read()
        for chave, onde in chaves.items():
            total += 1
            if chave.encode("ascii", "ignore") + b"\x00" not in conteudo:
                inexistentes.setdefault(nucleo, []).append((chave, onde))
    print("%d chaves conferidas." % total)
    print("Nucleos sem .dll na pasta (nao deu para conferir): %s" % (", ".join(sem_nucleo) or "nenhum"))
    if not inexistentes:
        print("Todas as chaves existem nos nucleos.")
        return 0
    n = sum(len(v) for v in inexistentes.values())
    print("%d CHAVES QUE O NUCLEO NAO CONHECE:" % n)
    for nucleo, lista in sorted(inexistentes.items()):
        print("  %s (%d):" % (nucleo, len(lista)))
        for chave, onde in lista:
            print("     %-45s  em: %s" % (chave, ", ".join(sorted(set(onde)))))
    return 1


if __name__ == "__main__":
    sys.exit(principal())
