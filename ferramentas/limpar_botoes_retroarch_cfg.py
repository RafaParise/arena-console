# -*- coding: utf-8 -*-
r"""Troca por "nul" os botoes e eixos de CONTROLE que ficaram gravados no
retroarch.cfg (input_playerN_..._btn / _axis). Teclas do teclado ficam.

Por que: numeros de outro tipo de controle esquecidos ali passavam por cima
do reconhecimento automatico do RetroArch -- no XInput, o Start ficava no
R3. Guarda uma copia antes (retroarch.cfg.antes-limpeza-<data>).

Uso: servidor\python\python.exe ferramentas\limpar_botoes_retroarch_cfg.py
"""
import os
import re
import shutil
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = os.path.join(RAIZ, "retroarch", "retroarch.cfg")
CHAVE = re.compile(r'^(input_player\d+_[a-z0-9_]+_(?:btn|axis)) = "(.*)"\s*$')


def main():
    copia = CFG + ".antes-limpeza-" + time.strftime("%Y%m%d-%H%M%S")
    shutil.copy2(CFG, copia)
    with open(CFG, "r", encoding="utf-8") as arquivo:
        linhas = arquivo.readlines()
    trocadas = 0
    for i, linha in enumerate(linhas):
        achado = CHAVE.match(linha)
        if achado and achado.group(2) not in ("nul", ""):
            linhas[i] = '%s = "nul"\n' % achado.group(1)
            trocadas += 1
    temporario = CFG + ".tmp"
    with open(temporario, "w", encoding="utf-8", newline="") as arquivo:
        arquivo.writelines(linhas)
    os.replace(temporario, CFG)
    print("Copia guardada em:", copia)
    print("Botoes/eixos de controle trocados por nul:", trocadas)


if __name__ == "__main__":
    main()
