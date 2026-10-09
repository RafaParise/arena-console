# -*- coding: utf-8 -*-
r"""Fase 6 (auditoria 3): o ARENA.bat percebe o Windows de 32 bits ANTES de
tentar o Python embutido (que e' de 64 bits e nem abriria) e explica.

O ARENA.bat roda numa pasta temporaria, sozinho (sem servidor, sem Python
na pasta e com o PATH so do Windows -- nada abre de verdade), com as
variaveis que o Windows poe:
  1. Windows de 32 bits: PROCESSOR_ARCHITECTURE=x86, sem PROCESSOR_ARCHITEW6432
     -> a mensagem "[ERRO] Este Windows e de 32 bits" e saida 1;
  2. controle: cmd de 32 bits num Windows de 64 (x86 + PROCESSOR_ARCHITEW6432)
     -> passa da checagem e chega na busca do Python ("nao foi encontrado").
Antes da auditoria 3 essa checagem existia (auditoria 1, Fase 6), mas nada
conferia que ela funciona.
"""
import os
import shutil
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import limpeza  # noqa: E402


def rodar_bat(pasta, arquitetura, arquitetura_w6432):
    ambiente = dict(os.environ)
    sistema = os.environ.get("SystemRoot", r"C:\Windows")
    ambiente["PATH"] = os.path.join(sistema, "System32")       # sem Python nenhum no caminho
    ambiente["PROCESSOR_ARCHITECTURE"] = arquitetura
    ambiente.pop("PROCESSOR_ARCHITEW6432", None)
    if arquitetura_w6432:
        ambiente["PROCESSOR_ARCHITEW6432"] = arquitetura_w6432
    r = subprocess.run([os.path.join(sistema, "System32", "cmd.exe"), "/c", os.path.join(pasta, "ARENA.bat")],
                       cwd=pasta, env=ambiente, stdin=subprocess.DEVNULL, capture_output=True,
                       timeout=60)
    return r.returncode, r.stdout.decode("cp850", "replace") + r.stderr.decode("cp850", "replace")


def main():
    pasta = tempfile.mkdtemp(prefix="arena_32bits_")
    falhas = []
    try:
        shutil.copy2(os.path.join(RAIZ, "ARENA.bat"), pasta)

        codigo, saida = rodar_bat(pasta, "x86", None)
        ok = codigo == 1 and "Este Windows e de 32 bits" in saida and "Python nao foi encontrado" not in saida
        print("[%s] Windows de 32 bits: para e explica (saida %d)" % ("OK" if ok else "FALHOU", codigo))
        if not ok:
            falhas.append(saida[-600:])

        codigo, saida = rodar_bat(pasta, "x86", "AMD64")
        ok = "32 bits" not in saida and "Python nao foi encontrado" in saida
        print("[%s] cmd de 32 bits num Windows de 64: passa da checagem" % ("OK" if ok else "FALHOU"))
        if not ok:
            falhas.append(saida[-600:])

        codigo, saida = rodar_bat(pasta, "AMD64", None)
        ok = "32 bits" not in saida and "Python nao foi encontrado" in saida
        print("[%s] Windows de 64 bits: passa da checagem" % ("OK" if ok else "FALHOU"))
        if not ok:
            falhas.append(saida[-600:])
    finally:
        limpeza.apagar_pasta(pasta)

    for falha in falhas:
        print("--- saida ---\n" + falha)
    print("RESULTADO:", "PASSOU" if not falhas else "FALHOU")
    return 0 if not falhas else 1


if __name__ == "__main__":
    sys.exit(main())
