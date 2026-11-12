# -*- coding: utf-8 -*-
r"""Partida entre casas pelo RETRANSMISSOR PUBLICO do RetroArch, com dois RetroArch de verdade (13/11/2026).

Para a casa com CGNAT (servidor\internet_de_casa.py): o anfitriao fala com a ponte local do ARENA
(servidor\repasse_publico.py), que repassa ao tunel de Sao Paulo da libretro e le o codigo da sessao; o convidado
recebe o codigo de 20 letras, devolve os 12 bytes ao RetroArch dele e entra direto no tunel. Sem lista publica.
Passa se o anfitriao registrar o convidado como jogador 2 pelo tunel e os dois seguirem jogando.

Precisa de internet (o tunel e' de verdade). Uso:
    servidor\python\python.exe testes\teste_repasse_publico_retroarch.py
"""
import os
import sys
import tempfile
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
import limpeza  # noqa: E402
import protege_cfg  # noqa: E402
import repasse_publico as rpub  # noqa: E402
from teste_cenarios_sala import JOGO, graficos, ler_log, matar  # noqa: E402
from teste_repasse_proprio_retroarch import abrir_retroarch  # noqa: E402


def main():
    if not os.path.isfile(JOGO):
        print("Falta o jogo do teste: %s" % JOGO)
        return 1
    if not rpub.tunel_responde():
        print("Sem internet ou o tunel de Sao Paulo fora do ar: nada a testar agora.")
        return 1
    raiz = tempfile.mkdtemp(prefix="arena_repasse_pub_")
    abertos, falhas = [], []

    def confere(nome, ok, detalhe=None):
        print("  %-6s %s%s" % ("ok" if ok else "FALHOU", nome, (" (%s)" % detalhe) if detalhe else ""), flush=True)
        if not ok:
            falhas.append(nome)

    ponte = rpub.abrir_ponte()
    try:
        opcoes_host = graficos.opcoes_de_partida("Anfitriao", True, pela_internet=True, jogador=1)
        opcoes_host.update({"netplay_use_mitm_server": "true", "netplay_mitm_server": "custom",
                            "netplay_custom_mitm_server": "127.0.0.1|%d" % ponte.porta,
                            "netplay_nat_traversal": "false", "netplay_public_announce": "false"})
        abertos.append(abrir_retroarch(os.path.join(raiz, "host"), opcoes_host, ["--host"]))
        codigo = ponte.esperar_codigo(25)
        confere("a ponte leu o codigo da sala no tunel", bool(codigo), codigo)
        if not codigo:
            for linha in [l for l in ler_log(os.path.join(raiz, "host")).splitlines()
                          if "netplay" in l.lower() or "mitm" in l.lower() or "tunnel" in l.lower()][-15:]:
                print("    " + linha[:170])
            return 1
        sessao = rpub.sessao_do_codigo(codigo.lower().replace("-", " "))     # como o colega cola: de qualquer jeito
        confere("o codigo de 20 letras volta aos 12 bytes", sessao == ponte.sessao)

        opcoes_conv = graficos.opcoes_de_partida("Convidado", False, pela_internet=True, jogador=2)
        opcoes_conv.update({"netplay_ip_port": str(rpub.TUNEL[1]), "netplay_use_mitm_server": "false",
                            "netplay_nat_traversal": "false"})
        abertos.append(abrir_retroarch(os.path.join(raiz, "conv"), opcoes_conv,
                                       ["--connect", rpub.TUNEL[0], "--port", str(rpub.TUNEL[1]),
                                        "--mitm-session=" + rpub.para_o_retroarch(sessao)]))
        entrou = False
        limite = time.monotonic() + 45
        while time.monotonic() < limite and not entrou:
            time.sleep(2)
            entrou = "se juntou como o jogador 2" in ler_log(os.path.join(raiz, "host")).lower()
        texto_host = ler_log(os.path.join(raiz, "host"))
        texto_conv = ler_log(os.path.join(raiz, "conv"))
        confere("o convidado entrou como jogador 2", entrou)
        confere("o anfitriao passou pelo tunel", "tunnel link connection completed" in texto_host.lower())
        for linha in [l for l in (texto_host + texto_conv).splitlines() if "[netplay]" in l.lower()][-10:]:
            print("    " + linha[:170])
        if entrou:
            time.sleep(8)
            confere("os dois continuam jogando 8 s depois", all(p.poll() is None for p, _log in abertos))
    finally:
        for processo, log in abertos:
            matar(processo, log)
        rpub.fechar_ponte()
        time.sleep(1)
        limpeza.apagar_pasta(raiz)
    print()
    if falhas:
        print("FALHOU: %s" % ", ".join(falhas))
        return 1
    print("Retransmissor publico com dois RetroArch: tudo certo.")
    return 0


if __name__ == "__main__":
    sys.exit(protege_cfg.rodar(main))
