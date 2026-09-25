# -*- coding: utf-8 -*-
r"""Auditoria 2, Fase 1: os ids que o app.js procura existem no index.html?

  - id procurado no JS e ausente no HTML = a tela quebra naquele ponto
    (o $() devolve null e o JS para ali). E' DEFEITO.
  - id no HTML que ninguem usa (nem JS, nem CSS, nem label for=, nem
    aria-*) = candidato a sobra.

Uso:
    servidor\python\python.exe testes\ids_da_tela.py
"""
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
js = open(os.path.join(RAIZ, "launcher", "app.js"), encoding="utf-8").read()
html = open(os.path.join(RAIZ, "launcher", "index.html"), encoding="utf-8").read()
css = open(os.path.join(RAIZ, "launcher", "estilo.css"), encoding="utf-8").read()

ids_html = set(re.findall(r'\bid="([^"]+)"', html))
# $("#x"), document.getElementById("x"), querySelector("#x ...")
ids_js = set(re.findall(r'\$\(\s*["\']#([\w-]+)', js))
ids_js |= set(re.findall(r'getElementById\(\s*["\']([\w-]+)', js))
ids_js |= set(re.findall(r'querySelector(?:All)?\(\s*["\']#([\w-]+)', js))
# ids passados como texto para funcoes (ex.: abrirModal("modalPartida"), data-fechar="x")
texto_js = set(re.findall(r'["\']([\w-]+)["\']', js))

faltando = sorted(i for i in ids_js if i not in ids_html)
sem_uso = sorted(i for i in ids_html
                 if i not in ids_js and i not in texto_js
                 and not re.search(r"#%s\b" % re.escape(i), css)
                 and not re.search(r'(?:for|aria-[a-z]+|data-[a-z-]+)="%s"' % re.escape(i), html))
print("ids no HTML: %d; procurados pelo JS: %d" % (len(ids_html), len(ids_js)))
print("PROCURADOS PELO JS E AUSENTES NO HTML (defeito): %s" % (faltando or "nenhum"))
print("NO HTML E SEM USO APARENTE (candidatos): %s" % (sem_uso or "nenhum"))
sys.exit(1 if faltando else 0)
