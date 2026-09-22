# -*- coding: utf-8 -*-
"""Teste de aceite: ARENA copiado pra outra pasta se conserta sozinho.

Roda: servidor\\python\\python.exe ferramentas\\teste_aceite_pasta_movida.py

Copia o ARENA (sem jogos, sem cores/BIOS/assets pesados - nao precisa
disso pra este teste) pra uma pasta nova dentro de
C:\\Projetos\\Criador De Apps Pedagogicos\\ARENA\\, sobe o servidor de la
por alguns segundos (o que dispara a correcao de caminhos sozinha, do
jeito que o ARENA.bat faria), derruba, e confere que o retroarch.cfg
resultante nao tem nenhum caminho fora da pasta de teste.
"""
import os
import re
import shutil
import subprocess
import sys
import time

ORIGEM = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ_TESTES = os.path.dirname(ORIGEM)
DESTINO = os.path.join(RAIZ_TESTES, "ARENA-teste-pasta-movida")

PASTAS_PESADAS_IGNORADAS = {
    os.path.join(ORIGEM, "jogos"),
    os.path.join(ORIGEM, "retroarch", "cores"),
    os.path.join(ORIGEM, "retroarch", "system"),
    os.path.join(ORIGEM, "retroarch", "shaders"),
    os.path.join(ORIGEM, "retroarch", "assets"),
    os.path.join(ORIGEM, "retroarch", "database"),
    os.path.join(ORIGEM, "retroarch", "overlays"),
    os.path.join(ORIGEM, "retroarch", "autoconfig"),
    os.path.join(ORIGEM, "retroarch", "info"),
    os.path.join(ORIGEM, "retroarch", "saves"),
    os.path.join(ORIGEM, "retroarch", "states"),
    os.path.join(ORIGEM, "emuladores"),
    os.path.join(ORIGEM, "backup"),
    os.path.join(ORIGEM, ".git"),
}


def deve_ignorar(caminho, nomes):
    ignorados = []
    for nome in nomes:
        completo = os.path.join(caminho, nome)
        if completo in PASTAS_PESADAS_IGNORADAS:
            ignorados.append(nome)
        if nome == "__pycache__":
            ignorados.append(nome)
    return ignorados


def main():
    if os.path.isdir(DESTINO):
        shutil.rmtree(DESTINO)

    print("Copiando (sem jogos/cores/BIOS/assets) para:\n  %s" % DESTINO)
    shutil.copytree(ORIGEM, DESTINO, ignore=deve_ignorar)

    python_exe = os.path.join(DESTINO, "servidor", "python", "python.exe")
    arena_py = os.path.join(DESTINO, "servidor", "arena.py")
    if not os.path.isfile(python_exe):
        print("FALHOU: python embutido nao foi copiado.")
        return 1

    print("Abrindo o ARENA da pasta nova por alguns segundos...")
    processo = subprocess.Popen(
        [python_exe, arena_py],
        cwd=os.path.join(DESTINO, "servidor"),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    time.sleep(6)
    processo.terminate()
    try:
        processo.wait(timeout=5)
    except subprocess.TimeoutExpired:
        processo.kill()

    cfg = os.path.join(DESTINO, "retroarch", "retroarch.cfg")
    with open(cfg, "r", encoding="utf-8", errors="replace") as f:
        texto = f.read()

    destino_baixo = DESTINO.lower()
    fora = []
    for m in re.finditer(r'^[a-zA-Z0-9_]+\s*=\s*"([A-Za-z]:\\[^"]*)"\s*$',
                          texto, re.MULTILINE):
        valor = m.group(1)
        if not valor.lower().startswith(destino_baixo):
            fora.append(valor)

    if fora:
        print("FALHOU: %d caminho(s) fora da pasta de teste:" % len(fora))
        for v in fora[:10]:
            print("  " + v)
        return 1

    print("OK: nenhum caminho absoluto do retroarch.cfg aponta pra fora de\n  %s" % DESTINO)
    return 0


if __name__ == "__main__":
    sys.exit(main())
