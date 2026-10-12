# -*- coding: utf-8 -*-
"""Fase 7: conquistas com varios jogadores (bug do sorted em sqlite3.Row) e
mensagens de erro em duas partes. Roda numa copia isolada."""
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "testes"))
import limpeza  # noqa: E402
URL = "http://127.0.0.1:8777"


def chamar(caminho, corpo=None):
    dados = json.dumps(corpo).encode() if corpo is not None else None
    req = urllib.request.Request(URL + caminho, data=dados,
                                 method="POST" if corpo is not None else "GET",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def main():
    destino = tempfile.mkdtemp(prefix="arena_f7_")
    processo = None
    try:
        for pasta in ("servidor", "dados", "launcher"):
            shutil.copytree(os.path.join(RAIZ, pasta), os.path.join(destino, pasta),
                            ignore=shutil.ignore_patterns("__pycache__", "tests", "python"))
        processo = subprocess.Popen(
            [os.path.join(RAIZ, "servidor", "python", "python.exe"),
             os.path.join(destino, "servidor", "arena.py")],
            cwd=destino, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(40):
            try:
                chamar("/api/estado")
                break
            except Exception:
                time.sleep(0.3)

        banco = sqlite3.connect(os.path.join(destino, "dados", "arena.db"))
        for apelido in ("Ana", "Pedro", "Lucas"):
            for i in range(2):
                banco.execute(
                    "INSERT INTO placar (uuid, apelido, jogo_id, jogo_titulo, pontos, "
                    "registrado_em, dispositivo) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    ("%s-%d" % (apelido, i), apelido, "jogo%d" % i, "Jogo %d" % i,
                     100 + i, "2026-09-24T10:00:00", "teste"))
        banco.commit()
        banco.close()

        falhas = 0

        def conferir(nome, ok, extra=""):
            nonlocal falhas
            print(("OK    " if ok else "FALHA ") + nome, extra)
            if not ok:
                falhas += 1

        status, resp = chamar("/api/conquistas")
        conferir("conquistas com 3 jogadores", status == 200, str(status))

        status, resp = chamar("/api/jogo/console", {"jogo_id": "nao-existe"})
        conferir("jogo inexistente tem 2 partes",
                 status == 404 and "Atualizar lista" in resp.get("erro", ""), resp.get("erro", ""))

        status, resp = chamar("/api/cheat/alterar", {"jogo_id": "nao-existe", "indice": "x"})
        conferir("cheat em jogo inexistente", status == 404, resp.get("erro", ""))

        status, resp = chamar("/api/capa/enviar", {"jogo_id": "nao-existe", "imagem": "!!"})
        conferir("capa em jogo inexistente", status == 404, resp.get("erro", ""))

        print("\nRESULTADO:", "PASSOU" if not falhas else "FALHOU")
        return 1 if falhas else 0
    finally:
        if processo:
            processo.kill()
        time.sleep(0.5)
        # shutil.rmtree calado desistia de arquivo somente leitura ou preso (a rodada da auditoria 3 achava esta pasta no Temp).
        limpeza.apagar_pasta(destino)


if __name__ == "__main__":
    sys.exit(main())
