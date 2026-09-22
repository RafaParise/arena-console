# -*- coding: utf-8 -*-
"""Testa o PCSX ReARMed sozinho (sem partida em rede) com o Metal Slug X:
BIOS certa? Controle reconhecido? Abre sem travar?

Roda: servidor\\python\\python.exe ferramentas\\teste_pcsx_rearmed_basico.py
"""
import os
import subprocess
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(RAIZ, "retroarch", "cores", "pcsx_rearmed_libretro.dll")
ROM = os.path.join(RAIZ, "jogos", "pessoais", "PS1", "Metal Slug X (USA).cue")
EXE = os.path.join(RAIZ, "retroarch", "retroarch.exe")
PASTA_DADOS = os.path.join(RAIZ, "dados")


def log_mais_recente():
    candidatos = [f for f in os.listdir(PASTA_DADOS) if f.endswith(".log")]
    if not candidatos:
        return None
    candidatos.sort(key=lambda f: os.path.getmtime(os.path.join(PASTA_DADOS, f)))
    return os.path.join(PASTA_DADOS, candidatos[-1])


def main():
    antes = set(os.listdir(PASTA_DADOS))
    comando = [EXE, "-L", CORE, ROM]
    proc = subprocess.Popen(comando, cwd=os.path.join(RAIZ, "retroarch"))
    print("PID:", proc.pid)
    time.sleep(6)
    vivo = proc.poll() is None
    print("vivo apos 6s:", vivo)
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()

    time.sleep(1)
    logs_novos = set(os.listdir(PASTA_DADOS)) - antes
    logs_novos = [f for f in logs_novos if f.endswith(".log")]
    if not logs_novos:
        print("Nenhum log novo apareceu.")
        return 1

    caminho_log = os.path.join(PASTA_DADOS, sorted(logs_novos)[-1])
    with open(caminho_log, "r", encoding="utf-8", errors="replace") as f:
        texto = f.read()

    print("--- trechos relevantes do log ---")
    for linha in texto.splitlines():
        baixo = linha.lower()
        if any(p in baixo for p in
               ("bios", "error", "netplay", "input_descriptor",
                "controller", "warn")):
            print(linha)
    return 0


if __name__ == "__main__":
    sys.exit(main())
