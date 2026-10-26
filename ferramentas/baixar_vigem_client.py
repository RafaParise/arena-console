# -*- coding: utf-8 -*-
r"""Baixa o ViGEmClient.dll para servidor\vigem\ (so para o gamepad Xbox virtual do celular, que e' OPCIONAL).

O repositorio e' publico e nao leva binario: esta ferramenta pega a DLL do pacote vgamepad 0.1.0 do PyPI (MIT; a DLL e' a do
projeto ViGEmClient, tambem MIT), confere a marca SHA-256 do pacote e extrai so a DLL de 64 bits. Nao instala nada: o DRIVER
ViGEmBus e' outra coisa e o ARENA nunca o instala (`winget install ViGEm.ViGEmBus`, com administrador).

Uso:  servidor\python\python.exe ferramentas\baixar_vigem_client.py
"""
import hashlib
import io
import json
import os
import sys
import tarfile
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESTINO = os.path.join(RAIZ, "servidor", "vigem", "ViGEmClient.dll")
PACOTE = "https://pypi.org/pypi/vgamepad/0.1.0/json"
DENTRO = "vgamepad-0.1.0/vgamepad/win/vigem/client/x64/ViGEmClient.dll"


def main():
    with urllib.request.urlopen(PACOTE, timeout=30) as r:
        info = json.load(r)
    arquivo = next(u for u in info["urls"] if u["filename"].endswith(".tar.gz"))
    print("baixando", arquivo["filename"], "...")
    with urllib.request.urlopen(arquivo["url"], timeout=120) as r:
        dados = r.read()
    if hashlib.sha256(dados).hexdigest() != arquivo["digests"]["sha256"]:
        raise SystemExit("A marca SHA-256 do pacote nao confere: nada foi gravado.")
    with tarfile.open(fileobj=io.BytesIO(dados), mode="r:gz") as t:
        dll = t.extractfile(DENTRO).read()
    os.makedirs(os.path.dirname(DESTINO), exist_ok=True)
    with open(DESTINO, "wb") as f:
        f.write(dll)
    print("pronto:", DESTINO, "(%d bytes)" % len(dll))
    return 0


if __name__ == "__main__":
    sys.exit(main())
