# -*- coding: utf-8 -*-
"""Testa a rede do Xbox 360 (Xenia Netplay, Systemlink) de ponta a ponta
pelo ARENA de verdade: abre Gears of War pelo /api/jogar, confere se veio
o aviso certo, se trocou pro build de netplay e se network_mode ficou 1
(Systemlink) no config.toml certo.

Roda: servidor\\python\\python.exe ferramentas\\teste_netplay_xbox360.py
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_NETPLAY = os.path.join(RAIZ, "emuladores", "Xenia", "Xenia",
                              "xenia-canary-netplay.config.toml")


def pedir(caminho, corpo=None):
    url = "http://127.0.0.1:8777%s" % caminho
    dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
    req = urllib.request.Request(url, data=dados,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def ler_network_mode():
    with open(CONFIG_NETPLAY, "r", encoding="utf-8", errors="replace") as f:
        for linha in f:
            if linha.strip().startswith("network_mode"):
                return linha.strip()
    return None


def main():
    servidor_proc = subprocess.Popen(
        [os.path.join(RAIZ, "servidor", "python", "python.exe"),
         os.path.join(RAIZ, "servidor", "arena.py")],
        cwd=os.path.join(RAIZ, "servidor"))
    print("Servidor ARENA rodando, PID", servidor_proc.pid)
    time.sleep(3)

    try:
        catalogo = pedir("/api/catalogo")
        jogo = next((j for j in catalogo["jogos"] if "Gears of War" in j["titulo"]), None)
        if not jogo:
            print("FALHOU: Gears of War nao esta no catalogo.")
            return 1

        resp = pedir("/api/jogar", {"jogo_id": jogo["id"], "apelido": "aluno"})
        print("Resposta do /api/jogar:", resp)
        if not resp.get("ok"):
            print("FALHOU ao abrir.")
            return 1
        if "aviso" not in resp or "systemlink" not in resp["aviso"].lower():
            print("FALHOU: aviso de rede nao veio na resposta.")
            return 1

        time.sleep(8)

        modo = ler_network_mode()
        print("network_mode gravado:", modo)
        if not modo or "network_mode = 1" not in modo:
            print("FALHOU: network_mode nao ficou 1.")
            return 1

        vivo = False
        saida = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq xenia_canary_netplay.exe"],
            capture_output=True, text=True)
        vivo = "xenia_canary_netplay.exe" in saida.stdout
        print("Xenia Netplay rodando:", vivo)
        if not vivo:
            print("FALHOU: o build de netplay nao ficou de pe.")
            return 1

        print("OK: rede do Xbox 360 configurada de ponta a ponta pelo ARENA de verdade.")
        return 0
    finally:
        subprocess.run(["taskkill", "/F", "/IM", "xenia_canary_netplay.exe"],
                       capture_output=True)
        subprocess.run(["taskkill", "/F", "/IM", "xenia_canary.exe"],
                       capture_output=True)
        servidor_proc.terminate()
        try:
            servidor_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            servidor_proc.kill()


if __name__ == "__main__":
    sys.exit(main())
