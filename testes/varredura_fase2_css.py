"""Fase 2 da auditoria: candidatos a CSS nao usado.

So aponta candidatos -- cada um precisa ser conferido a mao antes de
qualquer remocao (mesma regra da Fase 1: nada por suposicao de regex).
Classe usada so via JavaScript dinamico (template literal, concatenacao)
pode dar falso positivo aqui.
"""
import json
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAUNCHER = os.path.join(RAIZ, "launcher")


def ler(nome):
    with open(os.path.join(LAUNCHER, nome), "r", encoding="utf-8") as f:
        return f.read()


def main():
    css = ler("estilo.css")
    html = ler("index.html")
    js = ler("app.js")
    todo_o_resto = html + "\n" + js

    seletores = sorted(set(re.findall(r"\.([a-zA-Z_][a-zA-Z0-9_-]*)\s*[\{,:.\[]", css)))
    candidatos = []
    for nome in seletores:
        # conta ocorrencias fora do proprio CSS -- em HTML (class="...")
        # ou em JS (classList.add('nome'), template literal, etc.)
        padrao = re.compile(r"\b" + re.escape(nome) + r"\b")
        usos = len(padrao.findall(todo_o_resto))
        if usos == 0:
            candidatos.append(nome)

    print("Seletores de classe no CSS:", len(seletores))
    print("Candidatos sem nenhuma ocorrencia fora do CSS:", len(candidatos))
    for c in candidatos:
        print(" -", c)

    destino = os.path.join(RAIZ, "docs", "varredura_fase2_css_bruta.json")
    with open(destino, "w", encoding="utf-8") as f:
        json.dump({"total_seletores": len(seletores), "candidatos": candidatos}, f, ensure_ascii=False, indent=2)
    print("\nSalvo em", destino)


if __name__ == "__main__":
    main()
