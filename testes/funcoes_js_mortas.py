# -*- coding: utf-8 -*-
r"""Auditoria 2, Fase 1: funcoes do app.js definidas e nunca usadas.

Conta, para cada 'function nome(' do launcher\app.js, quantas vezes o nome
aparece no app.js e no index.html. Nome que so aparece na propria
definicao e' candidato -- ainda precisa de conferencia manual (pode ser
chamado por texto montado, o que aqui nao da para ver).

Uso:
    servidor\python\python.exe testes\funcoes_js_mortas.py
"""
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
js = open(os.path.join(RAIZ, "launcher", "app.js"), encoding="utf-8").read()
html = open(os.path.join(RAIZ, "launcher", "index.html"), encoding="utf-8").read()
nomes = re.findall(r"(?:async\s+)?function\s+([A-Za-z_]\w*)\s*\(", js)
candidatas = []
for nome in sorted(set(nomes)):
    usos = len(re.findall(r"\b%s\b" % re.escape(nome), js)) + len(re.findall(r"\b%s\b" % re.escape(nome), html))
    if usos <= 1:
        candidatas.append(nome)
print("%d funcoes definidas, %d candidatas a mortas:" % (len(set(nomes)), len(candidatas)))
for nome in candidatas:
    print("  -", nome)
