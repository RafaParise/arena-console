# -*- coding: utf-8 -*-
"""Testa o RPCN de ponta a ponta pelo ARENA de verdade (sem criar conta
nenhuma - so confere se liga Internet enabled/PSN status no config.yml
do RPCS3 quando rpcn_ativo esta ligado, e abre Borderlands 2 de
verdade).

Roda: servidor\\python\\python.exe ferramentas\\teste_rpcn.py
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(RAIZ, "emuladores", "RPCS3", "RPCS3", "config", "config.yml")


def pedir(caminho, corpo=None, metodo="GET"):
    url = "http://127.0.0.1:8777%s" % caminho
    dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
    req = urllib.request.Request(url, data=dados, method=metodo,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def ler_net():
    valores, dentro = {}, False
    with open(CONFIG, "r", encoding="utf-8", errors="replace") as f:
        for linha in f:
            if linha.rstrip("\n") == "Net:":
                dentro = True
                continue
            if dentro and linha.startswith((" ", "\t")) is False and linha.strip():
                dentro = False
            if dentro and ":" in linha:
                chave, valor = linha.strip().split(":", 1)
                valores[chave.strip()] = valor.strip()
    return valores


def main():
    servidor_proc = subprocess.Popen(
        [os.path.join(RAIZ, "servidor", "python", "python.exe"),
         os.path.join(RAIZ, "servidor", "arena.py")],
        cwd=os.path.join(RAIZ, "servidor"))
    print("Servidor ARENA rodando, PID", servidor_proc.pid)
    time.sleep(3)

    try:
        antes = ler_net()
        print("Net antes:", antes)
        if antes.get("PSN status") == "RPCN":
            print("FALHOU (falso positivo): ja estava RPCN antes de ligar.")
            return 1

        resp = pedir("/api/config", {"rpcn_ativo": True}, "POST")
        print("Config:", bool(resp.get("config")))

        catalogo = pedir("/api/catalogo")
        jogo = next((j for j in catalogo["jogos"] if "Borderlands" in j["titulo"]), None)
        if not jogo:
            print("FALHOU: Borderlands 2 nao esta no catalogo.")
            return 1

        resp = pedir("/api/jogar", {"jogo_id": jogo["id"], "apelido": "aluno"}, "POST")
        print("Resposta do /api/jogar:", resp)
        if not resp.get("ok"):
            print("FALHOU ao abrir.")
            return 1

        time.sleep(6)

        depois = ler_net()
        print("Net depois:", depois)
        if depois.get("PSN status") != "RPCN":
            print("FALHOU: PSN status nao ficou RPCN.")
            return 1
        if depois.get("Internet enabled") != "Connected":
            print("FALHOU: Internet enabled nao ficou Connected.")
            return 1

        print("OK: RPCN ligado de ponta a ponta pelo ARENA de verdade "
             "(sem criar conta nenhuma - so a configuracao).")
        return 0
    finally:
        subprocess.run(["taskkill", "/F", "/IM", "rpcs3.exe"], capture_output=True)
        try:
            pedir("/api/config", {"rpcn_ativo": False}, "POST")
        except Exception:
            pass
        servidor_proc.terminate()
        try:
            servidor_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            servidor_proc.kill()


if __name__ == "__main__":
    sys.exit(main())
