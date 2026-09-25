# -*- coding: utf-8 -*-
"""Teste isolado: host + SO o jogador 5 (pula 2,3,4), pra saber se o
problema e' especifico da 5a vaga de conexao ou de qualquer coisa
relacionada ao jogador 5/porta do multitap. Reusa a mesma logica de
teste_netplay_5_jogadores.py.
"""
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOGO = os.path.join(RAIZ, "jogos", "pessoais", "Super Nintendo",
                    "Super Bomberman 4 (Japan) [T-En by Svambo v1.0].sfc")
RETROARCH = os.path.join(RAIZ, "retroarch", "retroarch.exe")
CORE = os.path.join(RAIZ, "retroarch", "cores", "snes9x_libretro.dll")
PORTA_PARTIDA = 55435

sys.path.insert(0, os.path.join(RAIZ, "servidor"))
spec_a = importlib.util.spec_from_file_location("arena_iso", os.path.join(RAIZ, "servidor", "arena.py"))
arena = importlib.util.module_from_spec(spec_a)
spec_a.loader.exec_module(arena)
graficos = arena.graficos


def montar_override(destino_cfg, pasta_instancia, opcoes_partida):
    config = arena.config_padrao()
    opcoes = arena.opcoes_efetivas(config)
    opcoes.update(opcoes_partida)
    for chave in ("saves", "states", "capturas"):
        os.makedirs(os.path.join(pasta_instancia, chave), exist_ok=True)
    opcoes["savefile_directory"] = os.path.join(pasta_instancia, "saves")
    opcoes["savestate_directory"] = os.path.join(pasta_instancia, "states")
    opcoes["screenshot_directory"] = os.path.join(pasta_instancia, "capturas")
    opcoes["system_directory"] = os.path.join(RAIZ, "retroarch", "system")
    opcoes["cache_directory"] = pasta_instancia
    opcoes["playlist_directory"] = pasta_instancia
    opcoes["log_dir"] = pasta_instancia
    opcoes["log_to_file"] = "true"
    opcoes["log_verbosity"] = "true"
    opcoes["frontend_log_level"] = "0"
    opcoes["video_fullscreen"] = "false"
    opcoes["menu_driver"] = "rgui"
    linhas = ["# teste isolado"] + ['%s = "%s"' % (c, opcoes[c]) for c in sorted(opcoes)]
    with open(destino_cfg, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n")


def abrir(papel, hospedar, jogador, apelido, raiz_teste):
    pasta_instancia = os.path.join(raiz_teste, papel)
    os.makedirs(pasta_instancia, exist_ok=True)
    opcoes_partida = graficos.opcoes_de_partida(apelido=apelido, hospedar=hospedar, jogador=jogador, multitap=True)
    argumentos_partida = graficos.argumentos_de_partida(hospedar, endereco="127.0.0.1", porta=PORTA_PARTIDA)
    cfg = os.path.join(pasta_instancia, "override.cfg")
    montar_override(cfg, pasta_instancia, opcoes_partida)
    comando = [RETROARCH, "-L", CORE, "--appendconfig", cfg] + argumentos_partida + [JOGO]
    log = open(os.path.join(pasta_instancia, "stdout.log"), "w")
    processo = subprocess.Popen(comando, cwd=RAIZ, stdout=log, stderr=subprocess.STDOUT)
    return processo, pasta_instancia, log


def ler_log(pasta):
    candidatos = [n for n in os.listdir(pasta) if n.startswith("retroarch__") and n.endswith(".log")]
    if not candidatos:
        return ""
    with open(os.path.join(pasta, sorted(candidatos)[-1]), "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def main():
    raiz_teste = tempfile.mkdtemp(prefix="arena_netplay_iso_")
    print("Pasta:", raiz_teste)
    processos = []
    try:
        print("Abrindo hospedeiro...")
        p_host, pasta_host, log_host = abrir("hospedeiro", True, 1, "Anfitriao", raiz_teste)
        processos.append((p_host, log_host))
        time.sleep(8)

        print("Abrindo SO o jogador 5 (pulando 2, 3, 4)...")
        p5, pasta5, log5 = abrir("jogador5", False, 5, "Jogador5", raiz_teste)
        processos.append((p5, log5))
        time.sleep(15)

        print("\n--- Log do jogador 5 ---")
        texto5 = ler_log(pasta5)
        for linha in texto5.splitlines():
            if "netplay" in linha.lower() or "erro" in linha.lower() or "error" in linha.lower():
                print(" ", linha.strip())

        print("\n--- Log do hospedeiro (so Netplay) ---")
        texto_host = ler_log(pasta_host)
        for linha in texto_host.splitlines():
            if "netplay" in linha.lower():
                print(" ", linha.strip())

        return 0
    finally:
        for p, log in processos:
            try:
                p.terminate()
            except Exception:
                pass
        time.sleep(2)
        for p, log in processos:
            try:
                if p.poll() is None:
                    p.kill()
            except Exception:
                pass
            try:
                log.close()
            except Exception:
                pass


if __name__ == "__main__":
    # Devolve o retroarch.cfg real como estava (o RetroArch grava ao
    # fechar, e levaria junto as pastas temporarias deste teste).
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "testes"))
    import protege_cfg
    sys.exit(protege_cfg.rodar(main))
