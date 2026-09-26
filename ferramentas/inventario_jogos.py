# -*- coding: utf-8 -*-
r"""Lista, por console, os jogos que o ARENA reconhece agora: titulo,
arquivo e quantos jogadores. Serve para conferir jogo novo antes de testar
(console certo? trilha de CD aparecendo como jogo solto?).

Usa o indexador de verdade (o mesmo da tela). Grava so o cache normal dele
(dados\manifesto.json), como a tela faria.

Uso: servidor\python\python.exe ferramentas\inventario_jogos.py
"""
import collections
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
import indexador  # noqa: E402


def main():
    resultado = indexador.indexar(forcar=True)
    jogos = resultado["jogos"] if isinstance(resultado, dict) else resultado
    por_console = collections.defaultdict(list)
    for jogo in jogos:
        por_console[jogo.get("plataforma_nome") or jogo.get("plataforma")].append(jogo)
    for console in sorted(por_console, key=str):
        print("\n== %s (%d)" % (console, len(por_console[console])))
        for jogo in sorted(por_console[console], key=lambda j: j["titulo"]):
            print("   %-55s %s jog.  %s" % (jogo["titulo"][:55], jogo.get("jogadores_max", "?"),
                                          os.path.relpath(os.path.join(RAIZ, jogo["arquivo"]),
                                                          os.path.join(RAIZ, "jogos"))))
    print("\nTotal: %d jogos" % len(jogos))


if __name__ == "__main__":
    main()
