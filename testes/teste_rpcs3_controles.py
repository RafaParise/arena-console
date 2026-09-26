# -*- coding: utf-8 -*-
r"""O RPCS3 aceita os controles que o ARENA escreve?

Achado 26/09/2026: so o jogador 1 vinha configurado no RPCS3. Grava os
controles como o ARENA faz, abre o jogo sem a tela do RPCS3 por ~40 s e
mostra o que o registro diz sobre os controles; no fim confere se o
Default.yml continua com os 7 jogadores (o RPCS3 nao apagou).

Uso: servidor\python\python.exe testes\teste_rpcs3_controles.py [parte do nome do jogo]
"""
import glob
import os
import subprocess
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
import controles  # noqa: E402
import graficos  # noqa: E402

EXE = os.path.join(RAIZ, "emuladores", "RPCS3", "RPCS3", "rpcs3.exe")
LOG = os.path.join(os.path.dirname(EXE), "log", "RPCS3.log")
YML = os.path.join(os.path.dirname(EXE), "config", "input_configs", "global", "Default.yml")


def main():
    nome = (sys.argv[1:] or ["Rayman"])[0].lower()
    jogos = [j for j in glob.glob(os.path.join(RAIZ, "jogos", "pessoais", "PS3", "*.iso"))
             if nome in os.path.basename(j).lower()]
    if not jogos:
        print("Jogo nao encontrado:", nome)
        return 1
    xinput = controles.controles_xinput()
    print("controles XInput ligados:", xinput)
    graficos.escrever_controles_rpcs3(EXE, xinput)
    processo = subprocess.Popen([EXE, "--no-gui", jogos[0]], cwd=os.path.dirname(EXE))
    time.sleep(40)
    ainda = processo.poll() is None
    processo.kill()
    subprocess.run(["taskkill", "/F", "/IM", "rpcs3.exe"], capture_output=True)
    time.sleep(2)
    print("jogo rodando depois de 40 s:", ainda)
    try:
        texto = open(LOG, encoding="utf-8", errors="ignore").read()
    except OSError:
        texto = ""
    for linha in texto.splitlines():
        baixa = linha.lower()
        if ("input:" in baixa or "pad" in baixa or "xinput" in baixa or "keyboard" in baixa) \
                and ("error" in baixa or "warning" in baixa or "bound" in baixa
                     or "handler" in baixa or "device" in baixa):
            print("  ", linha.strip()[:160])
    yml = open(YML, encoding="utf-8").read()
    print("Default.yml: %d jogadores, teclado=%s, xinput=%d" % (
        yml.count(" Input:"), "Handler: Keyboard" in yml, yml.count("Handler: XInput")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
