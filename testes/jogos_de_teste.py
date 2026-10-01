# -*- coding: utf-8 -*-
r"""Acha um jogo de teste na pasta do console, mesmo dentro de subpasta.

Achado de 01/10/2026: o professor reorganizou a biblioteca (o CTR passou a
morar em jogos\pessoais\PS1\CTR - Crash Team Racing (USA)\), e tres testes
que apontavam para o arquivo solto na pasta do console passaram a PULAR o
jogo calados -- "passavam" sem testar o PS1 com 4 jogadores.
"""
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def achar(pasta_console, nome_arquivo):
    """Caminho do jogo em jogos\\pessoais\\<pasta_console>, direto ou em
    qualquer subpasta. None se nao estiver."""
    base = os.path.join(RAIZ, "jogos", "pessoais", pasta_console)
    direto = os.path.join(base, nome_arquivo)
    if os.path.isfile(direto):
        return direto
    for atual, subpastas, arquivos in os.walk(base):
        subpastas.sort()
        if nome_arquivo in arquivos:
            return os.path.join(atual, nome_arquivo)
    return None
