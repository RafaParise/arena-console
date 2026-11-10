# -*- coding: utf-8 -*-
r"""Partida entre casas pelo REPASSE PROPRIO, com dois RetroArch de verdade (10/11/2026).

Abre o repasse do ARENA (servidor\repasse_proprio.py) neste computador, reserva um codigo de sala e abre:
  - o anfitriao, com o repasse "custom" apontando para ele (netplay_mitm_server = custom);
  - o convidado, que acha a sessao pelo codigo de 6 numeros e entra com --mitm-session.
Passa se o anfitriao registrar o convidado entrando como jogador 2 e o registro mostrar a ligacao pelo tunel.

Uso:
    servidor\python\python.exe testes\teste_repasse_proprio_retroarch.py
"""
import asyncio
import os
import subprocess
import sys
import tempfile
import threading
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
import limpeza  # noqa: E402
import protege_cfg  # noqa: E402
import repasse_proprio as rp  # noqa: E402
from teste_cenarios_sala import CORE, JOGO, RETROARCH, graficos, ler_log, matar, montar_override  # noqa: E402


def abrir_repasse():
    pronto, guardado = threading.Event(), {}
    loop = asyncio.new_event_loop()

    def ao_abrir(servidor, _repasse):
        guardado["porta"] = servidor.sockets[0].getsockname()[1]
        pronto.set()

    def rodar():
        asyncio.set_event_loop(loop)
        guardado["tarefa"] = loop.create_task(rp.servir(0, "127.0.0.1", pronto=ao_abrir))
        try:
            loop.run_until_complete(guardado["tarefa"])
        except asyncio.CancelledError:
            pass

    fio = threading.Thread(target=rodar, daemon=True)
    fio.start()
    if not pronto.wait(10):
        raise RuntimeError("o repasse nao abriu")
    return guardado["porta"], lambda: (loop.call_soon_threadsafe(guardado["tarefa"].cancel), fio.join(10))


def abrir_retroarch(pasta, opcoes, argumentos):
    os.makedirs(pasta, exist_ok=True)
    cfg = os.path.join(pasta, "override.cfg")
    montar_override(cfg, pasta, opcoes)
    log = open(os.path.join(pasta, "stdout.log"), "w")
    comando = [RETROARCH, "-L", CORE, "--appendconfig", cfg] + argumentos + [JOGO]
    return subprocess.Popen(comando, cwd=RAIZ, stdout=log, stderr=subprocess.STDOUT), log


def main():
    if not os.path.isfile(JOGO):
        print("Falta o jogo do teste: %s" % JOGO)
        return 1
    de_fora = os.environ.get("ARENA_REPASSE")
    if de_fora:
        # Um repasse que ja esta no ar (o do A12 da bancada, por exemplo): ARENA_REPASSE=192.168.0.10:55440
        endereco = de_fora
        maquina, porta = rp.separar_endereco(de_fora)
        fechar_repasse = lambda: None  # noqa: E731
    else:
        porta, fechar_repasse = abrir_repasse()
        maquina = "127.0.0.1"
        endereco = "127.0.0.1:%d" % porta
    raiz = tempfile.mkdtemp(prefix="arena_repasse_ra_")
    abertos = []
    falhas = []

    def confere(nome, ok, detalhe=None):
        print("  %-6s %s%s" % ("ok" if ok else "FALHOU", nome, (" (%s)" % detalhe) if detalhe else ""), flush=True)
        if not ok:
            falhas.append(nome)

    try:
        print("Repasse aberto em %s" % endereco, flush=True)
        codigo, erro = rp.reservar_sala(endereco)
        confere("o repasse deu o codigo da sala", bool(codigo), codigo or erro)
        if not codigo:
            return 1

        opcoes_host = graficos.opcoes_de_partida("Anfitriao", True, pela_internet=True, jogador=1)
        opcoes_host.update({"netplay_use_mitm_server": "true", "netplay_mitm_server": "custom",
                            "netplay_custom_mitm_server": rp.para_o_retroarch(endereco), "netplay_nat_traversal": "false",
                            "netplay_public_announce": "false"})
        abertos.append(abrir_retroarch(os.path.join(raiz, "host"), opcoes_host, ["--host"]))

        achado, erro = rp.procurar_sala(endereco, codigo, tentativas=15, intervalo=1.0)
        confere("o convidado achou a sala pelo codigo", bool(achado), erro)
        if not achado:
            for linha in [l for l in ler_log(os.path.join(raiz, "host")).splitlines()
                          if "netplay" in l.lower() or "mitm" in l.lower() or "tunnel" in l.lower()][-15:]:
                print("    " + linha[:170])
            return 1
        sessao, porta_publica = achado

        opcoes_conv = graficos.opcoes_de_partida("Convidado", False, pela_internet=True, jogador=2)
        opcoes_conv.update({"netplay_ip_port": str(porta), "netplay_use_mitm_server": "false",
                            "netplay_nat_traversal": "false"})
        abertos.append(abrir_retroarch(os.path.join(raiz, "conv"), opcoes_conv,
                                       ["--connect", maquina, "--port", str(porta), "--mitm-session=" + sessao]))
        entrou = False
        limite = time.monotonic() + 40
        while time.monotonic() < limite and not entrou:
            time.sleep(2)
            entrou = "se juntou como o jogador 2" in ler_log(os.path.join(raiz, "host")).lower()
        texto_host = ler_log(os.path.join(raiz, "host"))
        texto_conv = ler_log(os.path.join(raiz, "conv"))
        confere("o convidado entrou como jogador 2", entrou)
        confere("o anfitriao passou pelo tunel", "tunnel link connection completed" in texto_host.lower())
        linhas = [l for l in (texto_host + texto_conv).splitlines() if "[netplay]" in l.lower()]
        for linha in linhas[-12:]:
            print("    " + linha[:170])
        if entrou:
            time.sleep(8)
            vivos = all(p.poll() is None for p, _log in abertos)
            confere("os dois continuam jogando 8 s depois", vivos)
    finally:
        for processo, log in abertos:
            matar(processo, log)
        fechar_repasse()
        time.sleep(1)
        limpeza.apagar_pasta(raiz)
    print()
    if falhas:
        print("FALHOU: %s" % ", ".join(falhas))
        return 1
    print("Repasse proprio com dois RetroArch: tudo certo.")
    return 0


if __name__ == "__main__":
    sys.exit(protege_cfg.rodar(main))
