# -*- coding: utf-8 -*-
"""Testa a rede do PS2 (system link) de ponta a ponta pelo ARENA de
verdade: abre Gran Turismo 4 pelo /api/jogar, confere se veio o aviso
certo, se o Npcap foi detectado e se o [DEV9/Eth] do PCSX2.ini ficou
com os valores esperados (PCAPBridged + adaptador real, ja que o Npcap
esta instalado nesta maquina).

Roda: servidor\\python\\python.exe ferramentas\\teste_rede_ps2_gt4.py
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INI = os.path.join(RAIZ, "emuladores", "PCSX2", "PCSX2", "inis", "PCSX2.ini")


def pedir(caminho, corpo=None):
    url = "http://127.0.0.1:8777%s" % caminho
    dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
    req = urllib.request.Request(url, data=dados,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def ler_bloco(nome_bloco):
    valores, dentro = {}, False
    with open(INI, "r", encoding="utf-8", errors="replace") as f:
        for linha in f:
            limpo = linha.strip()
            if limpo == nome_bloco:
                dentro = True
                continue
            if limpo.startswith("[") and limpo.endswith("]"):
                dentro = False
            if dentro and "=" in limpo:
                chave, valor = limpo.split("=", 1)
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
        estado = pedir("/api/estado")
        rede_ps2 = estado.get("rede_ps2", {})
        print("rede_ps2 no /api/estado:", rede_ps2)
        if "gran turismo 4" not in rede_ps2.get("jogos", []):
            print("FALHOU: gran turismo 4 nao esta na lista de system link.")
            return 1
        if not rede_ps2.get("driver_instalado"):
            print("FALHOU: Npcap deveria estar detectado nesta maquina.")
            return 1

        catalogo = pedir("/api/catalogo")
        jogo = next((j for j in catalogo["jogos"] if "Gran Turismo 4" in j["titulo"]), None)
        if not jogo:
            print("FALHOU: Gran Turismo 4 nao esta no catalogo.")
            return 1

        resp = pedir("/api/jogar", {"jogo_id": jogo["id"], "apelido": "aluno"})
        print("Resposta do /api/jogar:", resp)
        if not resp.get("ok"):
            print("FALHOU ao abrir.")
            return 1
        if "aviso" not in resp or "system link" not in resp["aviso"].lower():
            print("FALHOU: aviso de system link nao veio na resposta.")
            return 1

        time.sleep(6)

        dev9 = ler_bloco("[DEV9/Eth]")
        print("Bloco [DEV9/Eth] gravado:", dev9)
        if dev9.get("EthEnable") != "true":
            print("FALHOU: EthEnable nao ficou true.")
            return 1
        if dev9.get("EthApi") != "PCAPBridged":
            print("FALHOU: esperava EthApi=PCAPBridged com o driver instalado, achei %s"
                 % dev9.get("EthApi"))
            return 1
        if not dev9.get("InterfaceName"):
            print("FALHOU: InterfaceName nao foi preenchido.")
            return 1

        print("OK: rede do PS2 configurada de ponta a ponta pelo ARENA de verdade.")
        return 0
    finally:
        subprocess.run(["taskkill", "/F", "/IM", "pcsx2-qt.exe"], capture_output=True)
        servidor_proc.terminate()
        try:
            servidor_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            servidor_proc.kill()


if __name__ == "__main__":
    sys.exit(main())
