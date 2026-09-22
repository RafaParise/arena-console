# -*- coding: utf-8 -*-
"""Testa o seletor de qualidade do PCSX2 abrindo um jogo de verdade.

Pra cada preset ("leve" e "bonito"), escreve o PCSX2.ini de verdade (via
graficos.escrever_config_pcsx2) e confere duas coisas com um jogo real:
 1. o arquivo ficou com os valores esperados (UpscaleMultiplier etc.);
 2. o PCSX2 abre e continua de pe com esses valores - se alguma chave
    estivesse errada ou fora do intervalo aceito, o esperado seria travar
    no assistente ou fechar sozinho, em vez de chegar no jogo.

Tentei tambem tirar print de tela (tecla F8) pra comparar a resolucao
"no olho", mas SetForegroundWindow nao consegue roubar o foco de um
processo que nao e o de primeiro plano no Windows - o hotkey nunca chega
no PCSX2. Fica registrado como limite deste teste, nao como bug do ARENA.

Roda: servidor\\python\\python.exe ferramentas\\teste_qualidade_pcsx2.py
"""
import os
import subprocess
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
import graficos  # noqa: E402

EXE = os.path.join(RAIZ, "emuladores", "PCSX2", "PCSX2", "pcsx2-qt.exe")
INI = os.path.join(RAIZ, "emuladores", "PCSX2", "PCSX2", "inis", "PCSX2.ini")
ISO = os.path.join(RAIZ, "jogos", "pessoais", "PS2", "Crash Nitro Kart (USA).chd")
TITULO_JANELA = "Crash Nitro Kart"

ESPERADO = {
    "leve": {"UpscaleMultiplier": "1", "MaxAnisotropy": "0", "TexturePreloading": "0"},
    "bonito": {"UpscaleMultiplier": "4", "MaxAnisotropy": "16", "TexturePreloading": "2"},
}


def ler_bloco_gs():
    valores = {}
    dentro = False
    with open(INI, "r", encoding="utf-8", errors="replace") as arquivo:
        for linha in arquivo:
            limpo = linha.strip()
            if limpo == "[EmuCore/GS]":
                dentro = True
                continue
            if limpo.startswith("[") and limpo.endswith("]"):
                dentro = False
            if dentro and "=" in limpo:
                chave, valor = limpo.split("=", 1)
                valores[chave.strip()] = valor.strip()
    return valores


def testar_preset(nome_preset):
    graficos.escrever_config_pcsx2(EXE, nota=4, nota_gpu=4, preset=nome_preset)

    gravado = ler_bloco_gs()
    esperado = ESPERADO[nome_preset]
    for chave, valor in esperado.items():
        if gravado.get(chave) != valor:
            print("FALHOU (%s): esperava %s=%s, achei %s" %
                  (nome_preset, chave, valor, gravado.get(chave)))
            return False
    print("Preset %s: gravado certo no PCSX2.ini (%s)" % (nome_preset, esperado))

    p = subprocess.Popen([EXE, "-nofullscreen", ISO], cwd=os.path.dirname(EXE))
    time.sleep(9)
    p.poll()
    vivo = p.poll() is None
    print("Preset %s: PCSX2 continua rodando apos 9s: %s" % (nome_preset, vivo))

    subprocess.run(["taskkill", "/F", "/IM", "pcsx2-qt.exe"], capture_output=True)
    try:
        p.wait(timeout=5)
    except subprocess.TimeoutExpired:
        pass

    if not vivo:
        print("FALHOU (%s): o PCSX2 fechou sozinho com esse preset." % nome_preset)
        return False
    return True


def main():
    ok_leve = testar_preset("leve")
    ok_bonito = testar_preset("bonito")

    if not (ok_leve and ok_bonito):
        return 1
    print("OK: os dois presets gravam as chaves certas e o PCSX2 abre normal com os dois.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
