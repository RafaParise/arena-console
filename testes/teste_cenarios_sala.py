# -*- coding: utf-8 -*-
"""Fase 4: cenarios reais de sala de aula, com RetroArch de verdade.

1. Convidado cai e volta: conecta, mata o processo, sobe de novo apontando
   pro mesmo host -- confere se reconecta.
2. Hospedeiro sai no meio: convidado conectado, mata o host -- confere que
   o convidado registra a queda (nao trava, nao acha que ainda esta
   conectado).
3. Duas partidas diferentes na mesma rede ao mesmo tempo: dois pares
   host+convidado, em portas de partida DIFERENTES, rodando juntos --
   confere que nao se misturam. (Num computador so, as duas partidas
   precisam de portas diferentes; em computadores diferentes, cada
   hospedeiro tem o seu endereco e a mesma porta 55435 serve.)

Auditoria 3 (08/10/2026): o cenario 3 NUNCA tinha passado ("misturou")
e o teste saia com 0 assim mesmo. Causa: o RetroArch ignora o "--port" da
linha de comando, e a chave do arquivo ia com o nome errado
("netplay_port"): os dois hospedeiros escutavam na 55435 (o Windows deixa
dois programas na mesma porta) e os dois convidados caiam no mesmo. Agora
a porta vai na chave certa (netplay_ip_port), e o teste reprova quando um
cenario falha.
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

sys.path.insert(0, os.path.join(RAIZ, "servidor"))
spec_a = importlib.util.spec_from_file_location("arena_cenarios", os.path.join(RAIZ, "servidor", "arena.py"))
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
    linhas = ["# teste cenarios de sala"] + ['%s = "%s"' % (c, opcoes[c]) for c in sorted(opcoes)]
    with open(destino_cfg, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n")


def abrir(pasta_instancia, hospedar, jogador, apelido, porta):
    os.makedirs(pasta_instancia, exist_ok=True)
    opcoes_partida = graficos.opcoes_de_partida(apelido=apelido, hospedar=hospedar, jogador=jogador)
    # A porta vale pelo arquivo (o "--port" da linha de comando e' ignorado).
    opcoes_partida["netplay_ip_port"] = str(porta)
    argumentos_partida = graficos.argumentos_de_partida(hospedar, endereco="127.0.0.1", porta=porta)
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


def matar(processo, log):
    try:
        processo.terminate()
    except Exception:
        pass
    time.sleep(1.5)
    try:
        if processo.poll() is None:
            processo.kill()
    except Exception:
        pass
    try:
        log.close()
    except Exception:
        pass


def cenario_1_reconexao():
    print("\n=== Cenario 1: convidado cai e volta ===")
    raiz = tempfile.mkdtemp(prefix="arena_cen1_")
    try:
        p_host, l_host = abrir(os.path.join(raiz, "host"), True, 1, "Anfitriao", 55435)
        time.sleep(6)

        p_c1, l_c1 = abrir(os.path.join(raiz, "conv_v1"), False, 2, "Convidado", 55435)
        time.sleep(8)
        conectou1 = "se juntou como o jogador 2" in ler_log(os.path.join(raiz, "host")).lower()
        print("  1a conexao:", conectou1)
        matar(p_c1, l_c1)  # "cai"
        time.sleep(3)

        p_c2, l_c2 = abrir(os.path.join(raiz, "conv_v2"), False, 2, "Convidado", 55435)
        time.sleep(8)
        texto_host = ler_log(os.path.join(raiz, "host"))
        # conta quantas vezes "Convidado se juntou" aparece -- 2 = reconectou
        reconexoes = texto_host.lower().count("convidado se juntou como o jogador 2")
        print("  reconectou depois de cair:", reconexoes >= 2, "(entradas registradas:", reconexoes, ")")
        matar(p_c2, l_c2)
        matar(p_host, l_host)
        return {"cenario": "convidado_cai_e_volta", "conectou_primeira_vez": conectou1, "reconectou": reconexoes >= 2}
    finally:
        shutil.rmtree(raiz, ignore_errors=True)


def cenario_2_host_sai():
    print("\n=== Cenario 2: hospedeiro sai no meio ===")
    raiz = tempfile.mkdtemp(prefix="arena_cen2_")
    try:
        p_host, l_host = abrir(os.path.join(raiz, "host"), True, 1, "Anfitriao", 55436)
        time.sleep(6)
        p_conv, l_conv = abrir(os.path.join(raiz, "conv"), False, 2, "Convidado", 55436)
        time.sleep(8)
        conectou = "se juntou como o jogador 2" in ler_log(os.path.join(raiz, "host")).lower()
        print("  conectou antes do host sair:", conectou)

        matar(p_host, l_host)  # host cai
        time.sleep(6)

        texto_conv = ler_log(os.path.join(raiz, "conv"))
        registrou_queda = bool(re.search(r"desconect|disconnect|perdeu a conexao|lost connection", texto_conv, re.I))
        conv_ainda_vivo = p_conv.poll() is None
        print("  convidado registrou a queda no log:", registrou_queda, "| convidado ainda de pe (nao travou):", conv_ainda_vivo)
        matar(p_conv, l_conv)
        return {"cenario": "host_sai_no_meio", "conectou_antes": conectou,
               "convidado_registrou_queda": registrou_queda, "convidado_nao_travou": conv_ainda_vivo}
    finally:
        shutil.rmtree(raiz, ignore_errors=True)


def cenario_3_duas_partidas():
    print("\n=== Cenario 3: duas partidas diferentes na mesma rede (portas diferentes) ===")
    raiz = tempfile.mkdtemp(prefix="arena_cen3_")
    try:
        # Duas portas so porque e' um computador so (ver o topo do arquivo).
        pA_host, lA_host = abrir(os.path.join(raiz, "A_host"), True, 1, "TurmaA_Anfitriao", 55437)
        pB_host, lB_host = abrir(os.path.join(raiz, "B_host"), True, 1, "TurmaB_Anfitriao", 55438)
        time.sleep(6)

        pA_conv, lA_conv = abrir(os.path.join(raiz, "A_conv"), False, 2, "TurmaA_Convidado", 55437)
        pB_conv, lB_conv = abrir(os.path.join(raiz, "B_conv"), False, 2, "TurmaB_Convidado", 55438)
        time.sleep(10)

        texto_A = ler_log(os.path.join(raiz, "A_host")).lower()
        texto_B = ler_log(os.path.join(raiz, "B_host")).lower()
        A_ok = "turmaa_convidado se juntou" in texto_A
        B_ok = "turmab_convidado se juntou" in texto_B
        # confere que NAO se misturaram (convidado errado no host errado)
        vazou_A_em_B = "turmaa_convidado" in texto_B
        vazou_B_em_A = "turmab_convidado" in texto_A
        print("  Partida A conectou certo:", A_ok, "| Partida B conectou certo:", B_ok)
        print("  Misturou (nao deveria):", vazou_A_em_B or vazou_B_em_A)

        for p, log in ((pA_conv, lA_conv), (pB_conv, lB_conv), (pA_host, lA_host), (pB_host, lB_host)):
            matar(p, log)
        return {"cenario": "duas_partidas_simultaneas", "partida_A_ok": A_ok, "partida_B_ok": B_ok,
               "misturou": vazou_A_em_B or vazou_B_em_A}
    finally:
        shutil.rmtree(raiz, ignore_errors=True)


def main():
    if not os.path.isfile(JOGO):
        print("[ERRO] jogo nao encontrado")
        return 1
    resultados = [cenario_1_reconexao(), cenario_2_host_sai(), cenario_3_duas_partidas()]
    print("\n\n--- RESUMO ---")
    for r in resultados:
        print(" ", r)
    import json
    with open(os.path.join(RAIZ, "docs", "cenarios_sala_bruto.json"), "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    reconexao, saida, duas = resultados
    certos = [reconexao["conectou_primeira_vez"] and reconexao["reconectou"],
              saida["conectou_antes"] and saida["convidado_registrou_queda"] and saida["convidado_nao_travou"],
              duas["partida_A_ok"] and duas["partida_B_ok"] and not duas["misturou"]]
    print("\nCenarios certos: %d de 3" % sum(certos))
    print("RESULTADO:", "PASSOU" if all(certos) else "FALHOU")
    return 0 if all(certos) else 1


if __name__ == "__main__":
    # Devolve o retroarch.cfg real como estava (o RetroArch grava ao
    # fechar, e levaria junto as pastas temporarias deste teste).
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "testes"))
    import protege_cfg
    sys.exit(protege_cfg.rodar(main))
