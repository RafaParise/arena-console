# -*- coding: utf-8 -*-
r"""Mostra as chaves de opcao que um nucleo conhece (lidas de dentro do .dll),
filtradas por um pedaco do nome. Serve para achar o nome ATUAL de uma
opcao que mudou de nome numa versao nova do nucleo.

Uso:
    servidor\python\python.exe ferramentas\opcoes_do_nucleo.py ppsspp frame
"""
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
nucleo, filtro = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "")
dados = open(os.path.join(RAIZ, "retroarch", "cores", nucleo + "_libretro.dll"), "rb").read()
prefixo = nucleo.split("_")[0].encode()
achadas = sorted(set(m.decode() for m in re.findall(rb"(?<![\w])" + prefixo + rb"[a-z0-9_]*(?=\x00)", dados)))
for chave in achadas:
    if filtro.lower() in chave.lower():
        print(chave)
