# -*- coding: utf-8 -*-
"""Fase 3: mede o tempo real de /api/partida/testar com endereco invalido
(depois da correcao -- resolve uma vez so, em vez de duas) e confere que o
caminho feliz (endereco alcancavel, ele mesmo) continua funcionando com a
mensagem de diagnostico certa.
"""
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def requisicao(caminho, corpo):
    dados = json.dumps(corpo).encode("utf-8")
    req = urllib.request.Request("http://127.0.0.1:8777" + caminho, data=dados,
                                  method="POST", headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def main():
    destino = tempfile.mkdtemp(prefix="arena_partida_timing_")
    try:
        for pasta in ("servidor", "dados", "launcher"):
            shutil.copytree(os.path.join(RAIZ, pasta), os.path.join(destino, pasta),
                             ignore=shutil.ignore_patterns("__pycache__", "tests"))

        spec = importlib.util.spec_from_file_location(
            "arena_partida_timing", os.path.join(destino, "servidor", "arena.py"))
        arena = importlib.util.module_from_spec(spec)
        sys.path.insert(0, os.path.join(destino, "servidor"))
        spec.loader.exec_module(arena)

        servidor = arena.Servidor(("127.0.0.1", 8777), arena.Manipulador)
        thread = threading.Thread(target=servidor.serve_forever, daemon=True)
        thread.start()
        time.sleep(0.5)

        print("--- Endereco invalido (numero solto, sem sentido de rede) ---")
        inicio = time.monotonic()
        status, resp = requisicao("/api/partida/testar", {"endereco": "12345"})
        duracao = time.monotonic() - inicio
        print("Status=%s tempo=%.2fs" % (status, duracao))
        print("Resposta:", resp)
        caso1_ok = status == 200 and resp.get("arena") is False and "confira o endereço" in resp.get("diagnostico", "").lower()

        print("\n--- Endereco alcancavel (o proprio localhost) ---")
        inicio = time.monotonic()
        status, resp = requisicao("/api/partida/testar", {"endereco": "127.0.0.1"})
        duracao2 = time.monotonic() - inicio
        print("Status=%s tempo=%.2fs" % (status, duracao2))
        print("Resposta:", resp)
        caso2_ok = status == 200 and resp.get("arena") is True

        servidor.shutdown()
        servidor.server_close()

        # antes da correcao, media ~5,3s (duas resolucoes de DNS
        # sequenciais); depois, deveria ficar perto de UMA resolucao so.
        melhorou = duracao < 4.0
        print("\nTempo com endereco invalido: %.2fs (antes da correcao: ~5,3s medido)" % duracao)
        ok = caso1_ok and caso2_ok and melhorou
        print("RESULTADO:", "PASSOU" if ok else "FALHOU")
        return 0 if ok else 1
    finally:
        sys.path = [p for p in sys.path if not p.startswith(destino)]
        shutil.rmtree(destino, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
