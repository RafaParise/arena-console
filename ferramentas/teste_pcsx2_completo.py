# -*- coding: utf-8 -*-
"""Testa o PCSX2 de ponta a ponta pelo ARENA de verdade: abre um jogo de
PS2 pelo /api/jogar (sem BIOS pre-colocada, pra confirmar que o ARENA
copia sozinho) e confere se o PCSX2 chega no jogo com a qualidade grafica
esperada pro perfil "automatico" desta maquina.

Roda: servidor\\python\\python.exe ferramentas\\teste_pcsx2_completo.py
"""
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_PCSX2 = os.path.join(RAIZ, "emuladores", "PCSX2", "PCSX2")
PASTA_BIOS_PCSX2 = os.path.join(PASTA_PCSX2, "bios")
INI = os.path.join(PASTA_PCSX2, "inis", "PCSX2.ini")
PORTA_ARENA = 8777


def pedir(caminho, corpo=None):
    url = "http://127.0.0.1:%d%s" % (PORTA_ARENA, caminho)
    dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
    req = urllib.request.Request(url, data=dados,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def ler_bloco_gs():
    valores, dentro = {}, False
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


def main():
    if os.path.isdir(PASTA_BIOS_PCSX2):
        shutil.rmtree(PASTA_BIOS_PCSX2)

    servidor_proc = subprocess.Popen(
        [os.path.join(RAIZ, "servidor", "python", "python.exe"),
         os.path.join(RAIZ, "servidor", "arena.py")],
        cwd=os.path.join(RAIZ, "servidor"))
    print("Servidor ARENA rodando, PID", servidor_proc.pid)
    time.sleep(3)

    try:
        catalogo = pedir("/api/catalogo")
        jogo = next((j for j in catalogo["jogos"]
                    if "Crash Nitro Kart" in j["titulo"]), None)
        if not jogo:
            print("FALHOU: Crash Nitro Kart nao esta no catalogo.")
            return 1

        resp = pedir("/api/jogar", {"jogo_id": jogo["id"], "apelido": "aluno"})
        print("Resposta do /api/jogar:", resp)
        if not resp.get("ok"):
            print("FALHOU ao abrir.")
            return 1

        time.sleep(9)

        if not os.path.isdir(PASTA_BIOS_PCSX2) or not os.listdir(PASTA_BIOS_PCSX2):
            print("FALHOU: o ARENA nao copiou nenhuma BIOS de PS2 sozinho.")
            return 1
        print("BIOS copiada sozinha:", os.listdir(PASTA_BIOS_PCSX2))

        gs = ler_bloco_gs()
        print("Bloco [EmuCore/GS] gravado:", gs)
        if gs.get("upscale_multiplier") not in ("1", "2", "4"):
            print("FALHOU: upscale_multiplier ausente ou fora do esperado.")
            return 1

        vivo = False
        try:
            saida = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq pcsx2-qt.exe"],
                capture_output=True, text=True)
            vivo = "pcsx2-qt.exe" in saida.stdout
        except OSError:
            pass
        print("PCSX2 rodando depois de abrir pelo ARENA:", vivo)

        if not vivo:
            print("FALHOU: o PCSX2 nao ficou de pe.")
            return 1

        print("OK: BIOS copiada sozinha, qualidade grafica escrita, PCSX2 rodando.")
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
