# -*- coding: utf-8 -*-
"""Fase 4: mede o Jogar Junto (PS1, SwanStation nao serve netplay -- usa
SNES, ja confirmado funcionando desde antes) passando pelo simulador de
rede ruim (proxy_rede_ruim.py), em varios niveis de atraso/perda, e olha
o que o RetroArch REPORTA sozinho (ping visto pelo host, avisos de
"stall"/dessincronia) -- prova real, nao suposicao, do que o jogador
sentiria.
"""
import importlib.util
import os
import re
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
PYTHON = os.path.join(RAIZ, "servidor", "python", "python.exe")
PORTA_HOST = 55435

sys.path.insert(0, os.path.join(RAIZ, "servidor"))
spec_a = importlib.util.spec_from_file_location("arena_rede_ruim", os.path.join(RAIZ, "servidor", "arena.py"))
arena = importlib.util.module_from_spec(spec_a)
spec_a.loader.exec_module(arena)
graficos = arena.graficos


def montar_override(destino_cfg, pasta_instancia, opcoes_partida):
    config = arena.config_padrao()
    opcoes = arena.opcoes_efetivas(config)
    opcoes.update(opcoes_partida)
    for chave in ("saves", "states"):
        os.makedirs(os.path.join(pasta_instancia, chave), exist_ok=True)
    opcoes["savefile_directory"] = os.path.join(pasta_instancia, "saves")
    opcoes["savestate_directory"] = os.path.join(pasta_instancia, "states")
    opcoes["system_directory"] = os.path.join(RAIZ, "retroarch", "system")
    opcoes["cache_directory"] = pasta_instancia
    opcoes["playlist_directory"] = pasta_instancia
    opcoes["log_dir"] = pasta_instancia
    opcoes["log_to_file"] = "true"
    opcoes["log_verbosity"] = "true"
    opcoes["frontend_log_level"] = "0"
    opcoes["video_fullscreen"] = "false"
    opcoes["menu_driver"] = "rgui"
    linhas = ["# teste rede ruim"] + ['%s = "%s"' % (c, opcoes[c]) for c in sorted(opcoes)]
    with open(destino_cfg, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n")


def abrir(pasta_instancia, hospedar, jogador, apelido, porta_conexao):
    os.makedirs(pasta_instancia, exist_ok=True)
    opcoes_partida = graficos.opcoes_de_partida(apelido=apelido, hospedar=hospedar, jogador=jogador)
    argumentos_partida = graficos.argumentos_de_partida(hospedar, endereco="127.0.0.1", porta=porta_conexao)
    cfg = os.path.join(pasta_instancia, "override.cfg")
    montar_override(cfg, pasta_instancia, opcoes_partida)
    comando = [RETROARCH, "-L", CORE, "--appendconfig", cfg] + argumentos_partida + [JOGO]
    log = open(os.path.join(pasta_instancia, "stdout.log"), "w")
    processo = subprocess.Popen(comando, cwd=RAIZ, stdout=log, stderr=subprocess.STDOUT)
    return processo, log


def ler_log(pasta):
    candidatos = [n for n in os.listdir(pasta) if n.startswith("retroarch__") and n.endswith(".log")]
    if not candidatos:
        return ""
    with open(os.path.join(pasta, sorted(candidatos)[-1]), "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def rodar_cenario(nome, atraso_ms, perda_pct, porta_proxy):
    print("\n=== Cenario: %s (atraso=%dms, perda=%.0f%%) ===" % (nome, atraso_ms, perda_pct))
    raiz_teste = tempfile.mkdtemp(prefix="arena_rede_ruim_")
    proxy = None
    processos = []
    try:
        proxy = subprocess.Popen(
            [PYTHON, os.path.join(RAIZ, "testes", "proxy_rede_ruim.py"),
             str(porta_proxy), "127.0.0.1", str(PORTA_HOST), str(atraso_ms), str(perda_pct)],
            cwd=RAIZ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)

        pasta_host = os.path.join(raiz_teste, "host")
        p_host, log_host = abrir(pasta_host, True, 1, "Anfitriao", PORTA_HOST)
        processos.append((p_host, log_host))
        time.sleep(6)

        pasta_convidado = os.path.join(raiz_teste, "convidado")
        p_conv, log_conv = abrir(pasta_convidado, False, 2, "Convidado", porta_proxy)
        processos.append((p_conv, log_conv))
        time.sleep(14)

        texto_host = ler_log(pasta_host)
        conectou = "se juntou como o jogador 2" in texto_host.lower()
        ping_m = re.search(r"ping:\s*(\d+)\s*ms", texto_host.lower())
        ping = ping_m.group(1) if ping_m else None
        avisos_stall = len(re.findall(r"stall|travad|desconect|timeout", texto_host, re.I))

        print("  conectou:", conectou, "| ping reportado:", ping, "ms | avisos de travada/timeout:", avisos_stall)
        return {"cenario": nome, "atraso_ms": atraso_ms, "perda_pct": perda_pct,
                "conectou": conectou, "ping_reportado_ms": ping, "avisos_travada": avisos_stall}
    finally:
        for p, log in processos:
            try:
                p.terminate()
            except Exception:
                pass
        time.sleep(1.5)
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
        if proxy:
            proxy.terminate()
            try:
                proxy.wait(timeout=5)
            except Exception:
                proxy.kill()
        shutil.rmtree(raiz_teste, ignore_errors=True)


def main():
    if not os.path.isfile(JOGO):
        print("[ERRO] jogo nao encontrado")
        return 1

    cenarios = [
        ("so atraso 50ms", 50, 0),
        ("so atraso 100ms", 100, 0),
        ("so atraso 200ms", 200, 0),
        ("perda 1% (com 50ms de base)", 50, 1),
        ("perda 5% (com 50ms de base)", 50, 5),
    ]
    resultados = []
    for i, (nome, atraso, perda) in enumerate(cenarios):
        resultados.append(rodar_cenario(nome, atraso, perda, 55440 + i))

    print("\n\n--- RESUMO ---")
    for r in resultados:
        print(" ", r)

    import json
    with open(os.path.join(RAIZ, "docs", "rede_ruim_bruto.json"), "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    # Devolve o retroarch.cfg real como estava (o RetroArch grava ao
    # fechar, e levaria junto as pastas temporarias deste teste).
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "testes"))
    import protege_cfg
    sys.exit(protege_cfg.rodar(main))
