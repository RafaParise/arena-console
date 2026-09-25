# -*- coding: utf-8 -*-
"""Fase 8: o PARTIDA.bat ainda confere a versao e o codigo do aparelho do
colega depois da trava de rede da Fase 3?

Achado real: partida.py lia /api/estado do colega, que desde a Fase 3 so
responde ao proprio computador -- as duas checagens sumiam em silencio.

Truque para ter "um colega" num computador so: um ARENA isolado que trata
como OUTRA MAQUINA todo pedido feito pelo nome "localhost" (e como local o
que vem por 127.0.0.1). Roda `partida.py localhost` e confere a saida.
"""
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON = os.path.join(RAIZ, "servidor", "python", "python.exe")


def main():
    destino = tempfile.mkdtemp(prefix="arena_partida_colega_")
    servidor = None
    try:
        for pasta in ("servidor", "dados", "launcher"):
            shutil.copytree(os.path.join(RAIZ, pasta), os.path.join(destino, pasta),
                            ignore=shutil.ignore_patterns("__pycache__", "tests", "python"))
        spec = importlib.util.spec_from_file_location(
            "arena_partida_colega", os.path.join(destino, "servidor", "arena.py"))
        arena = importlib.util.module_from_spec(spec)
        sys.path.insert(0, os.path.join(destino, "servidor"))
        spec.loader.exec_module(arena)

        class ManipuladorColega(arena.Manipulador):
            def pedido_e_local(self):
                return not (self.headers.get("Host") or "").startswith("localhost")

        servidor = arena.Servidor(("127.0.0.1", 8777), ManipuladorColega)
        threading.Thread(target=servidor.serve_forever, daemon=True).start()
        time.sleep(0.5)

        saida = subprocess.run([PYTHON, os.path.join(destino, "servidor", "partida.py"), "localhost"],
                               capture_output=True, timeout=60).stdout.decode("utf-8", "replace")
        trecho = saida[saida.find("4. O computador"):saida.find("5. Os arquivos")]
        print(trecho)

        # O "colega" aqui e' o proprio ARENA, entao o esperado e': mesma
        # versao, e o MESMO codigo de aparelho (acusado como problema).
        viu_versao = "mesma versao dos dois lados" in trecho
        viu_codigo = "MESMO codigo de aparelho" in trecho
        print("Conferiu a versao do colega:", viu_versao)
        print("Conferiu o codigo do aparelho do colega:", viu_codigo)
        ok = viu_versao and viu_codigo
        print("\nRESULTADO:", "PASSOU" if ok else "FALHOU")
        return 0 if ok else 1
    finally:
        if servidor:
            servidor.shutdown()
            servidor.server_close()
        sys.path = [p for p in sys.path if not p.startswith(destino)]
        shutil.rmtree(destino, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
