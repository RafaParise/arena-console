# -*- coding: utf-8 -*-
r"""Experiencia (13/11/2026): o SGSR chega ao RetroArch do celular pelo preset automatico (global.slangp)?

O app Android tira a chave video_shader e nao tem o --set-shader do computador. O RetroArch 1.22.2 carrega sozinho
o global.slangp da pasta do arquivo de configuracao (gfx/video_shader_parse.c, video_shader_load_auto_shader_preset),
que no celular e' a pasta do app (files/arena-partida.cfg). Aqui: com o files/global.slangp ja posto, o motor Vulkan
e a escala SGSR, abre um jogo e le o logcat do RetroArch. Devolve os ajustes como estavam.

Uso (APK de teste no A12): servidor\python\python.exe testes\experiencia_sgsr_celular.py [pedaco do titulo]
"""
import json
import os
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import celular_arena as c  # noqa: E402
import teste_android as t  # noqa: E402


def main(argv):
    pedaco = argv[1] if len(argv) > 1 else "32768 color"
    t.adb("logcat", "-c")
    pagina = c.abrir()
    config = (c.pedir(pagina, "/api/estado") or {}).get("config") or {}
    # O nivel "minimo" (bonecos de papelao) desliga todo filtro de proposito: so durante a experiencia ele sai.
    antes = {"escala_da_tela": config.get("escala_da_tela", "automatico"),
             "abaixo_do_original": config.get("abaixo_do_original") or "",
             "avancado": {"video_driver": (config.get("avancado") or {}).get("video_driver", "automatico")}}
    print("antes:", json.dumps(antes))
    jogo = c.achar_jogo(pagina, pedaco)
    if not jogo:
        print("jogo nao achado:", pedaco)
        return 1
    try:
        # O motor fica no Automatico: e' o ARENA que leva o jogo 2D ao Vulkan quando o filtro e' escolhido
        # (arena.filtro_pede_vulkan_no_android).
        c.pedir(pagina, "/api/config", {"escala_da_tela": "sgsr", "abaixo_do_original": "",
                                         "avancado": {"video_driver": "automatico"}})
        resposta = c.pedir(pagina, "/api/jogar", {"jogo_id": jogo["id"]}) or {}
        print("jogar:", json.dumps(resposta)[:200])
        t.esperar(lambda: "RetroActivityFuture" in t.tela_de_cima(), 60)
        time.sleep(15)
        foto = os.path.join(os.environ.get("TEMP", "."), "sgsr-celular.png")
        with open(foto, "wb") as saida:
            saida.write(t.adb("exec-out", "screencap", "-p", segundos=60).stdout)
        print("foto:", foto)
        log = t.adb_texto("logcat", "-d", "-s", "RetroArch")
        for linha in log.splitlines():
            baixo = linha.lower()
            if any(p in baixo for p in ("shader", "slang", "preset", "vulkan", "video driver", "[vulkan]")):
                print("  ", linha[-170:])
        t.sair_do_jogo()
        t.esperar(lambda: "ArenaActivity" in t.tela_de_cima(), 30)
    finally:
        try:
            pagina.fechar()
        except Exception:  # noqa: BLE001  (a pagina pode ter caido na volta do jogo)
            pass
        pagina = c.abrir()                      # pagina nova: a velha cai as vezes na volta do jogo
        c.pedir(pagina, "/api/config", antes)
        depois = (c.pedir(pagina, "/api/estado") or {}).get("config") or {}
        print("voltou:", depois.get("escala_da_tela"), depois.get("abaixo_do_original"),
              (depois.get("avancado") or {}).get("video_driver"))
        pagina.fechar()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
