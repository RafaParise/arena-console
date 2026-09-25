# -*- coding: utf-8 -*-
r"""Auditoria 2: o VERIFICAR.bat acusa a falta de um modulo sem o qual o
ARENA nem abre?

Antes, a lista de arquivos obrigatorios tinha so 5 dos 11 modulos que o
arena.py importa na abertura. Numa copia isolada, apaga um modulo que ficava
de fora (controles.py) e confere que o verificador acusa -- e que o ARENA,
de fato, nao abre sem ele (prova de que o arquivo e' mesmo obrigatorio).
"""
import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON = os.path.join(RAIZ, "servidor", "python", "python.exe")


def main():
    destino = tempfile.mkdtemp(prefix="arena_verif_arquivos_")
    try:
        shutil.copytree(os.path.join(RAIZ, "servidor"), os.path.join(destino, "servidor"),
                        ignore=shutil.ignore_patterns("__pycache__", "tests", "python"))
        shutil.copytree(os.path.join(RAIZ, "launcher"), os.path.join(destino, "launcher"))
        for n in ("ARENA.bat", "LEIA-ME.md"):
            shutil.copy2(os.path.join(RAIZ, n), destino)
        for pasta in ("dados", "backup", "retroarch", "jogos"):
            os.makedirs(os.path.join(destino, pasta), exist_ok=True)
        os.remove(os.path.join(destino, "servidor", "controles.py"))

        # 1. O ARENA abre sem ele? (nao deveria: e' importado na abertura)
        # O python embutido ja poe a pasta servidor REAL no caminho de busca
        # (linha '..' do python313._pth): tira ela, senao o import acharia o
        # controles.py de verdade e o teste nao provaria nada.
        real = os.path.normcase(os.path.join(RAIZ, "servidor"))
        script = ("import os, sys; sys.path = [p for p in sys.path if os.path.normcase(os.path.abspath(p)) != %r]; "
                  "sys.path.insert(0, %r); import arena" % (real, os.path.join(destino, "servidor")))
        r = subprocess.run([PYTHON, "-c", script], cwd=destino, capture_output=True, text=True, timeout=60)
        nao_abre = r.returncode != 0 and "controles" in (r.stderr or "")
        print("Sem controles.py o ARENA nao abre (importa na abertura):", nao_abre)
        if not nao_abre:
            print("   codigo de saida %s; ultimas linhas do erro:" % r.returncode)
            for linha in (r.stderr or "").strip().splitlines()[-4:]:
                print("   ", linha)

        # 2. O verificador acusa?
        caminho = os.path.join(destino, "servidor", "diagnostico.py")
        codigo = open(caminho, encoding="utf-8").read()
        sys.argv = ["diagnostico.py", "--so-ver", "--sem-barreiras"]
        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            try:
                exec(compile(codigo, caminho, "exec"), {"__name__": "__main__", "__file__": caminho})
            except SystemExit:
                pass
        texto = saida.getvalue()
        acusou = "controles.py" in texto
        print("O verificador acusou a falta de controles.py:", acusou)
        ok = nao_abre and acusou
        print("\nRESULTADO:", "PASSOU" if ok else "FALHOU")
        return 0 if ok else 1
    finally:
        shutil.rmtree(destino, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
