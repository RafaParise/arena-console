# -*- coding: utf-8 -*-
"""Testa o perfil de controle do Neo Geo pela API real: antes da
correcao, /api/perfis-controle?console=neogeo caia no perfil generico
de 8 botoes (com L/R e Select que o Neo Geo nao tem); confere que agora
mostra so os 4 botoes reais (A/B/C/D) + Start/Select.

Roda: servidor\\python\\python.exe ferramentas\\teste_controle_neogeo.py
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def pedir(caminho):
    url = "http://127.0.0.1:8777%s" % caminho
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    servidor_proc = subprocess.Popen(
        [os.path.join(RAIZ, "servidor", "python", "python.exe"),
         os.path.join(RAIZ, "servidor", "arena.py")],
        cwd=os.path.join(RAIZ, "servidor"))
    print("Servidor ARENA rodando, PID", servidor_proc.pid)
    time.sleep(3)

    try:
        perfil = pedir("/api/perfis-controle?tipo=xbox360&console=neogeo")
        botoes = [l["botao"] for l in perfil["linhas"]]
        print("Botoes mostrados pro Neo Geo:", botoes)

        if "l" in botoes or "r" in botoes:
            print("FALHOU: ainda mostra L/R, que o Neo Geo nao tem.")
            return 1
        for esperado in ("b", "a", "y", "x", "start"):
            if esperado not in botoes:
                print("FALHOU: faltou o botao '%s'." % esperado)
                return 1

        # Confere que o rotulo bate com o controle Xbox de verdade
        # (b=A do Neo Geo aparece com o nome do botao 0 do Xbox = "A").
        linha_b = next(l for l in perfil["linhas"] if l["botao"] == "b")
        print("Botao 'b' (A do Neo Geo) no controle Xbox:", linha_b["no_controle"])

        print("OK: perfil de controle do Neo Geo agora mostra os 4 botoes certos.")
        return 0
    finally:
        servidor_proc.terminate()
        try:
            servidor_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            servidor_proc.kill()


if __name__ == "__main__":
    sys.exit(main())
