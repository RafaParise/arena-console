# -*- coding: utf-8 -*-
r"""Lista os textos de dentro do .dll de um nucleo que batem com um filtro.

O nucleo guarda por escrito, dentro do .dll, o nome de cada tipo de
controle que aceita ("Multitap", "Four Score"...) e o nome de cada opcao
("snes9x_..."). Ler isso do arquivo que esta NA PASTA e' a unica fonte que
bate com a versao que o aluno roda -- lista da internet pode ser de outra
versao.

Uso:
    servidor\python\python.exe ferramentas\textos_do_nucleo.py snes9x "multi|tap"
    servidor\python\python.exe ferramentas\textos_do_nucleo.py snes9x "multi|tap" 12
      (o numero no fim mostra tambem os N textos que vem logo depois de
       cada achado -- e' onde o nucleo costuma guardar os valores da opcao)
"""
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def todos_os_textos(nucleo, minimo=2):
    caminho = os.path.join(RAIZ, "retroarch", "cores", nucleo + "_libretro.dll")
    dados = open(caminho, "rb").read()
    return [m.group(0).decode("ascii")
            for m in re.finditer(rb"[\x20-\x7e]{%d,}" % minimo, dados)]


def textos(nucleo, filtro, depois=0):
    lista = todos_os_textos(nucleo)
    achados = []
    for i, texto in enumerate(lista):
        if len(texto) >= 4 and re.search(filtro, texto, re.I):
            achados.append((texto, lista[i + 1:i + 1 + depois]))
    return achados


if __name__ == "__main__":
    depois = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    for texto, seguintes in textos(sys.argv[1], sys.argv[2], depois):
        print(texto[:160])
        for s in seguintes:
            print("      | " + s[:100])
