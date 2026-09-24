# -*- coding: utf-8 -*-
"""Fase 6: config.json, controles.json e arena.db corrompidos de
proposito (lixo binario/texto invalido) -- confere que o ARENA sobe
mesmo assim, sem travar, usando os padroes.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    destino = tempfile.mkdtemp(prefix="arena_corrompido_")
    print("Pasta de teste:", destino)
    try:
        for pasta in ("servidor", "dados", "launcher"):
            shutil.copytree(os.path.join(RAIZ, pasta), os.path.join(destino, pasta),
                            ignore=shutil.ignore_patterns("__pycache__", "tests"))

        # corrompe de proposito os 3 arquivos
        with open(os.path.join(destino, "dados", "config.json"), "wb") as f:
            f.write(b"\x00\x01LIXO_BINARIO_NAO_E_JSON{{{")
        with open(os.path.join(destino, "dados", "controles.json"), "wb") as f:
            f.write(b"isto nao e JSON valido nem um pouco")
        with open(os.path.join(destino, "dados", "arena.db"), "wb") as f:
            f.write(os.urandom(4096))  # lixo binario aleatorio, nao um banco SQLite

        print("Arquivos corrompidos de proposito. Subindo o ARENA...")
        processo = subprocess.Popen(
            [os.path.join(RAIZ, "servidor", "python", "python.exe"),
             os.path.join(destino, "servidor", "arena.py")],
            cwd=destino, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        subiu = False
        for _ in range(60):
            try:
                with urllib.request.urlopen("http://127.0.0.1:8777/api/estado", timeout=1) as resp:
                    dados = json.loads(resp.read())
                    subiu = True
                    break
            except Exception:
                time.sleep(0.3)

        print("ARENA respondeu apesar dos arquivos corrompidos:", subiu)
        if subiu:
            print("Apelido (deveria ser vazio/padrao, nao travar):", repr(dados["config"].get("apelido")))
            print("Tema (deveria ser o padrao 'claro'):", dados["config"].get("tema"))

        # confere tambem que /api/catalogo e /api/colegas nao quebram com
        # o banco corrompido
        cat_ok = plac_ok = False
        try:
            with urllib.request.urlopen("http://127.0.0.1:8777/api/catalogo", timeout=5) as resp:
                json.loads(resp.read())
                cat_ok = True
        except Exception as e:
            print("catalogo falhou:", e)
        try:
            with urllib.request.urlopen("http://127.0.0.1:8777/api/placar", timeout=5) as resp:
                pass
        except urllib.error.HTTPError as e:
            plac_ok = e.code in (400, 405)  # esperado: GET nao suportado ou precisa de jogo_id, nao 500 cru
        except Exception as e:
            print("placar deu erro inesperado:", e)

        print("catalogo respondeu:", cat_ok)

        processo.terminate()
        try:
            saida, _ = processo.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            processo.kill()
            saida, _ = processo.communicate()

        travou_com_traceback = "Traceback (most recent call last)" in saida and not subiu
        print("Travou com traceback cru (nao deveria):", travou_com_traceback)

        ok = subiu and cat_ok and not travou_com_traceback
        print("\nRESULTADO:", "PASSOU" if ok else "FALHOU")
        if not ok:
            print("\n--- saida do processo (ultimas 40 linhas) ---")
            print("\n".join(saida.splitlines()[-40:]))
        return 0 if ok else 1
    finally:
        shutil.rmtree(destino, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
