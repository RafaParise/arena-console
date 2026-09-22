# -*- coding: utf-8 -*-
"""Confere rapido, pra varios nucleos de uma vez, se o RetroArch aceita
netplay ou recusa com "nucleo nao tem suporte para Netplay" - o mesmo
jeito que foi descoberto pro SwanStation (PS1) e Mupen64Plus-Next (N64).

So abre cada um sozinho como host por alguns segundos e le o log - nao
testa conexao de verdade ainda (isso fica pra depois, so pros que
passarem aqui).

Roda: servidor\\python\\python.exe ferramentas\\teste_netplay_suporte_nucleos.py
"""
import os
import subprocess
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_DADOS = os.path.join(RAIZ, "dados")
EXE = os.path.join(RAIZ, "retroarch", "retroarch.exe")

CASOS = [
    ("Mega Drive (Genesis Plus GX)", "genesis_plus_gx_libretro.dll",
     os.path.join(RAIZ, "jogos", "pessoais", "Mega Drive", "Sonic The Hedgehog 3 (USA).md")),
    ("Dreamcast (Flycast)", "flycast_libretro.dll",
     os.path.join(RAIZ, "jogos", "pessoais", "Dreamcast", "Marvel vs. Capcom 2 (USA).cue")),
    ("PSP (PPSSPP)", "ppsspp_libretro.dll",
     os.path.join(RAIZ, "jogos", "pessoais", "PSP",
                  "Killzone - Liberation (USA) (En,Fr,De,Es,It,Nl,Pl,Ru).iso")),
]


def log_mais_recente_apos(momento):
    candidatos = []
    for nome in os.listdir(PASTA_DADOS):
        if nome.endswith(".log"):
            caminho = os.path.join(PASTA_DADOS, nome)
            if os.path.getmtime(caminho) >= momento - 1:
                candidatos.append(caminho)
    if not candidatos:
        return None
    candidatos.sort(key=os.path.getmtime)
    return candidatos[-1]


def testar(nome, nucleo, rom):
    if not os.path.isfile(rom):
        print("%s: ROM nao encontrada (%s) - pulando." % (nome, rom))
        return None

    core = os.path.join(RAIZ, "retroarch", "cores", nucleo)
    if not os.path.isfile(core):
        print("%s: nucleo %s nao instalado - pulando." % (nome, nucleo))
        return None

    momento = time.time()
    comando = [EXE, "-L", core, "--host", "--port", "55435", rom]
    p = subprocess.Popen(comando, cwd=os.path.join(RAIZ, "retroarch"))
    time.sleep(6)
    p.terminate()
    try:
        p.wait(timeout=5)
    except subprocess.TimeoutExpired:
        p.kill()

    log = log_mais_recente_apos(momento)
    if not log:
        print("%s: sem log gerado." % nome)
        return None
    with open(log, "r", encoding="utf-8", errors="replace") as f:
        texto = f.read()

    recusou = ("não tem suporte para Netplay" in texto or
               "nao tem suporte para Netplay" in texto or
               "does not support netplay" in texto.lower())
    print("%s: %s" % (nome, "RECUSOU netplay" if recusou else "aceitou (nao recusou)"))
    return not recusou


def main():
    subprocess.run(["taskkill", "/F", "/IM", "retroarch.exe"], capture_output=True)
    resultados = {}
    for nome, nucleo, rom in CASOS:
        resultados[nome] = testar(nome, nucleo, rom)
        subprocess.run(["taskkill", "/F", "/IM", "retroarch.exe"], capture_output=True)
        time.sleep(1)

    print()
    print("Resumo:")
    for nome, ok in resultados.items():
        print("  %s: %s" % (nome, ok))
    return 0


if __name__ == "__main__":
    sys.exit(main())
