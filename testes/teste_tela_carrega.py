# -*- coding: utf-8 -*-
r"""Confere que a TELA do ARENA carrega de verdade (o app.js roda inteiro).

Nesta maquina nao tem Node para checar a sintaxe do JavaScript. Em vez
disso, sobe o ARENA e pede ao Edge, sem janela (--headless), para abrir a
tela, rodar o JavaScript por alguns segundos e devolver a pagina ja
montada. Se o app.js tiver erro de sintaxe, nada e' desenhado -- o bug mais
embaracoso do projeto foi esse (tela vazia, "lendo..." para sempre).

Uso:
    servidor\python\python.exe testes\teste_tela_carrega.py [texto que tem que aparecer ...]
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON = os.path.join(RAIZ, "servidor", "python", "python.exe")
EDGES = [os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
         os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe")]


def main():
    edge = next((e for e in EDGES if os.path.isfile(e)), None)
    if not edge:
        print("Edge nao encontrado.")
        return 1
    servidor = subprocess.Popen([PYTHON, os.path.join(RAIZ, "servidor", "arena.py")], cwd=RAIZ,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    perfil = tempfile.mkdtemp(prefix="arena_tela_")
    try:
        for _ in range(100):
            try:
                urllib.request.urlopen("http://127.0.0.1:8777/", timeout=0.5)
                break
            except Exception:
                time.sleep(0.2)
        r = subprocess.run([edge, "--headless=new", "--disable-gpu", "--no-first-run",
                            "--user-data-dir=" + perfil, "--virtual-time-budget=10000",
                            "--dump-dom", "http://127.0.0.1:8777/"],
                           capture_output=True, timeout=90)
        dom = r.stdout.decode("utf-8", "replace")
    finally:
        subprocess.run(["taskkill", "/PID", str(servidor.pid), "/T", "/F"], capture_output=True)
        time.sleep(1)
        shutil.rmtree(perfil, ignore_errors=True)

    exigidos = sys.argv[1:] or []
    # Sinal de que o app.js rodou: a lista de jogos saiu do "lendo..." e o
    # carimbo de versao foi preenchido pelo JavaScript.
    rodou = "lendo…" not in dom.split("<body", 1)[-1][:20000] and len(dom) > 20000
    print("Tamanho da pagina montada:", len(dom), "caracteres")
    print("JavaScript rodou (a tela saiu do 'lendo...'):", rodou)
    ok = rodou
    for texto in exigidos:
        achou = texto in dom
        ok = ok and achou
        print("Aparece na tela: %r -> %s" % (texto, achou))
    print("\nRESULTADO:", "PASSOU" if ok else "FALHOU")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
