# -*- coding: utf-8 -*-
"""Testa o perfil com foto de ponta a ponta pela API real: envia um PNG
de verdade (1x1 pixel, minimo valido), confere que /api/estado mostra
tem_foto_perfil, busca a imagem de volta e compara byte a byte, testa
rejeicao de lixo (nao-imagem) e remove no final.

Roda: servidor\\python\\python.exe ferramentas\\teste_perfil_foto.py
"""
import base64
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# PNG minimo valido (1x1, transparente), 68 bytes.
PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42Y"
    "AAAAASUVORK5CYII=")


def pedir(caminho, corpo=None, metodo="GET"):
    url = "http://127.0.0.1:8777%s" % caminho
    dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
    req = urllib.request.Request(url, data=dados, method=metodo,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def pedir_binario(caminho):
    url = "http://127.0.0.1:8777%s" % caminho
    with urllib.request.urlopen(url, timeout=10) as resp:
        return resp.read(), resp.headers.get("Content-Type")


def main():
    servidor_proc = subprocess.Popen(
        [os.path.join(RAIZ, "servidor", "python", "python.exe"),
         os.path.join(RAIZ, "servidor", "arena.py")],
        cwd=os.path.join(RAIZ, "servidor"))
    print("Servidor ARENA rodando, PID", servidor_proc.pid)
    time.sleep(3)

    try:
        estado = pedir("/api/estado")
        print("tem_foto_perfil antes:", estado.get("tem_foto_perfil"))
        if estado.get("tem_foto_perfil"):
            print("FALHOU (ambiente sujo): ja tinha foto antes do teste comecar.")
            return 1

        imagem_base64 = "data:image/png;base64," + base64.b64encode(PNG_1X1).decode("ascii")
        resp = pedir("/api/perfil/foto", {"imagem": imagem_base64}, "POST")
        print("Envio da foto:", resp)
        if not resp.get("ok"):
            print("FALHOU ao enviar a foto.")
            return 1

        estado = pedir("/api/estado")
        if not estado.get("tem_foto_perfil"):
            print("FALHOU: /api/estado nao mostrou a foto depois de enviar.")
            return 1

        binario, tipo = pedir_binario("/api/perfil/foto")
        print("Foto lida de volta: %d bytes, tipo %s" % (len(binario), tipo))
        if binario != PNG_1X1:
            print("FALHOU: os bytes voltaram diferentes do que foi enviado.")
            return 1
        if tipo != "image/png":
            print("FALHOU: tipo errado.")
            return 1

        # Lixo (nao e imagem) tem que ser rejeitado, nao aceito.
        lixo_base64 = base64.b64encode(b"isto nao e uma imagem de verdade").decode("ascii")
        try:
            pedir("/api/perfil/foto", {"imagem": lixo_base64}, "POST")
            print("FALHOU: aceitou um arquivo que nao e imagem.")
            return 1
        except urllib.error.HTTPError:
            print("OK: rejeitou arquivo que nao e imagem de verdade.")

        resp = pedir("/api/perfil/foto", {"remover": True}, "POST")
        print("Remocao:", resp)
        estado = pedir("/api/estado")
        if estado.get("tem_foto_perfil"):
            print("FALHOU: ainda mostra foto depois de remover.")
            return 1

        print("OK: perfil com foto funciona de ponta a ponta pela API real.")
        return 0
    finally:
        servidor_proc.terminate()
        try:
            servidor_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            servidor_proc.kill()


if __name__ == "__main__":
    sys.exit(main())
