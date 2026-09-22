# -*- coding: utf-8 -*-
"""Testa a busca automatica de capa de ponta a ponta pela API real:
pede pra atualizar a capa do Sonic 3 (Mega Drive), confere que baixou de
verdade e que o catalogo passa a mostrar essa capa.

Roda: servidor\\python\\python.exe ferramentas\\teste_capa_online.py
"""
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_MINIATURAS = os.path.join(RAIZ, "retroarch", "thumbnails")
ARQUIVO_MANIFESTO = os.path.join(RAIZ, "dados", "manifesto.json")


def pedir(caminho, corpo=None, metodo="GET"):
    url = "http://127.0.0.1:8777%s" % caminho
    dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
    req = urllib.request.Request(url, data=dados, method=metodo,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    if os.path.isdir(PASTA_MINIATURAS):
        shutil.rmtree(PASTA_MINIATURAS)
    if os.path.isfile(ARQUIVO_MANIFESTO):
        os.remove(ARQUIVO_MANIFESTO)

    servidor_proc = subprocess.Popen(
        [os.path.join(RAIZ, "servidor", "python", "python.exe"),
         os.path.join(RAIZ, "servidor", "arena.py")],
        cwd=os.path.join(RAIZ, "servidor"))
    print("Servidor ARENA rodando, PID", servidor_proc.pid)
    time.sleep(3)

    try:
        catalogo = pedir("/api/catalogo")
        jogo = next((j for j in catalogo["jogos"] if "Sonic" in j["titulo"]), None)
        if not jogo:
            print("FALHOU: Sonic 3 nao esta no catalogo.")
            return 1
        print("Antes:", jogo.get("capa_urls"))
        if jogo.get("capa_urls"):
            print("FALHOU (ambiente sujo): ja tinha capa antes do teste.")
            return 1

        # A checagem de internet do vigia so fica pronta depois do primeiro
        # ciclo - o endpoint real exige isso, entao esperamos aqui tambem
        # (nao e' bug, e' o comportamento real que o aluno tambem verá).
        for _ in range(15):
            estado = pedir("/api/estado")
            if estado.get("internet"):
                break
            time.sleep(2)
        else:
            print("AVISO: vigia nao confirmou internet em 30s - tentando mesmo assim.")

        resp = pedir("/api/capa/atualizar", {"jogo_id": jogo["id"]}, "POST")
        print("Resposta:", resp)
        if not resp.get("ok"):
            print("FALHOU ao atualizar a capa.")
            return 1

        catalogo = pedir("/api/catalogo")
        jogo = next((j for j in catalogo["jogos"] if j["id"] == jogo["id"]), None)
        print("Depois:", jogo.get("capa_urls"))
        if not jogo.get("capa_urls"):
            print("FALHOU: catalogo nao mostra a capa nova.")
            return 1

        query = urllib.parse.urlsplit(jogo["capa_urls"][0]).query
        caminho_relativo = urllib.parse.parse_qs(query)["arquivo"][0]
        caminho_arquivo = os.path.join(RAIZ, caminho_relativo.replace("/", os.sep))
        if not os.path.isfile(caminho_arquivo) or os.path.getsize(caminho_arquivo) < 1000:
            print("FALHOU: arquivo da capa nao existe ou esta vazio de verdade.")
            return 1

        print("OK: capa baixada de verdade (%d bytes) e aparece no catalogo."
             % os.path.getsize(caminho_arquivo))
        return 0
    finally:
        servidor_proc.terminate()
        try:
            servidor_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            servidor_proc.kill()
        if os.path.isdir(PASTA_MINIATURAS):
            shutil.rmtree(PASTA_MINIATURAS)


if __name__ == "__main__":
    sys.exit(main())
