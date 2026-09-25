r"""Lista as chaves de opcao ligadas a BIOS/regiao que cada nucleo declara
de verdade (lendo o texto de dentro do .dll), para conferir se as chaves
que o ARENA escreve (graficos.CHAVE_BIOS) existem.

Uso:
    servidor\python\python.exe ferramentas\chaves_bios_nucleos.py
"""
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NUCLEOS = ("swanstation", "mednafen_saturn", "opera", "flycast")
PREFIXOS = (b"swanstation_", b"duckstation_", b"beetle_saturn_", b"opera_", b"reicast_", b"flycast_")

for nucleo in NUCLEOS:
    caminho = os.path.join(RAIZ, "retroarch", "cores", nucleo + "_libretro.dll")
    if not os.path.isfile(caminho):
        print("==", nucleo, ": nucleo nao esta na pasta")
        continue
    with open(caminho, "rb") as f:
        dados = f.read()
    chaves = set()
    for m in re.finditer(rb"[a-z_]*(?:bios|region)[a-zA-Z_]*(?=\x00)", dados, re.I):
        valor = m.group(0)
        if valor.startswith(PREFIXOS):
            chaves.add(valor.decode())
    print("==", nucleo, ":", ", ".join(sorted(chaves)) or "(nenhuma)")
