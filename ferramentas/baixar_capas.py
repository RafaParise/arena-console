# -*- coding: utf-8 -*-
r"""Baixa a capa de TODOS os jogos da lista que ainda nao tem capa.

E' o mesmo que clicar em "Buscar capa" em cada jogo (servidor\capas_online,
banco libretro-thumbnails, o do proprio RetroArch), so que de uma vez --
util para preparar o ARENA antes de levar para a sala, onde a internet e'
incerta. So baixa para quem nao tem capa nenhuma; nao apaga nada.

Escrito em 01/10/2026 para devolver as capas baixadas que a ferramenta
antiga ferramentas\teste_capa_online.py apagava (ela comecava apagando a
pasta retroarch\thumbnails inteira).

Uso:
    servidor\python\python.exe ferramentas\baixar_capas.py
"""
import os
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
import capas_online  # noqa: E402
import indexador  # noqa: E402


def principal():
    manifesto = indexador.indexar(forcar=True)
    alvo = [j for j in manifesto["jogos"]
            if j["plataforma"] in capas_online.REPO_POR_PLATAFORMA and not j.get("capas")]
    print("%d jogos sem capa, em consoles com banco de capas. Baixando..." % len(alvo), flush=True)
    achadas, inicio = 0, time.time()
    for n, jogo in enumerate(alvo, 1):
        nome_base = jogo.get("nome_banco") or os.path.splitext(os.path.basename(jogo["arquivo"]))[0]
        ok, motivo = capas_online.buscar_e_baixar(jogo["plataforma"], jogo["titulo"], nome_base)
        achadas += bool(ok)
        print("  [%d/%d] %s %s%s" % (n, len(alvo), "OK " if ok else "-- ", jogo["titulo"][:60],
                                    "" if ok else "  (%s)" % motivo), flush=True)
    indexador.indexar(forcar=True)
    print("\n%d de %d capas baixadas em %.0f s." % (achadas, len(alvo), time.time() - inicio))
    return 0


if __name__ == "__main__":
    sys.exit(principal())
