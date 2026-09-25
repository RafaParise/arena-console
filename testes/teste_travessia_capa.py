# -*- coding: utf-8 -*-
"""Fase 3: confere de verdade se /api/capa recusa sair da pasta permitida.

O fuzz generico (fuzz_rotas.py) nao testou isto direito: todo payload de
travessia usado la terminava em ".ini" ou sem extensao, e a rota rejeita
ANTES de checar a pasta, so por nao ser imagem (.png/.jpg/.jpeg/.webp).
Este teste usa um alvo que TERMINA em .png e existe de verdade fora da
pasta permitida, pra provar (ou refutar) que dentro_da_pasta() barra.
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


def main():
    destino = tempfile.mkdtemp(prefix="arena_travessia_")
    try:
        for pasta in ("servidor", "dados", "launcher"):
            shutil.copytree(os.path.join(RAIZ, pasta), os.path.join(destino, pasta),
                             ignore=shutil.ignore_patterns("__pycache__", "tests"))

        # Um "segredo" FORA da pasta jogos/retroarch, mas dentro da copia de
        # teste (pra nao mexer em nada real) -- termina em .png de proposito.
        segredo = os.path.join(destino, "segredo_fora_da_pasta.png")
        with open(segredo, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\nCONTEUDO_SECRETO_DE_TESTE")

        caminho_arena = os.path.join(destino, "servidor", "arena.py")
        spec = importlib.util.spec_from_file_location("arena_travessia", caminho_arena)
        arena = importlib.util.module_from_spec(spec)
        sys.path.insert(0, os.path.join(destino, "servidor"))
        spec.loader.exec_module(arena)

        servidor = arena.Servidor(("127.0.0.1", 8777), arena.Manipulador)
        thread = threading.Thread(target=servidor.serve_forever, daemon=True)
        thread.start()
        time.sleep(0.5)

        payloads = [
            "../segredo_fora_da_pasta.png",
            "../../segredo_fora_da_pasta.png",
            "..\\segredo_fora_da_pasta.png",
            "jogos/../../segredo_fora_da_pasta.png",
            "jogos\\..\\..\\segredo_fora_da_pasta.png",
            os.path.abspath(segredo),  # caminho absoluto direto
        ]

        resultados = []
        for payload in payloads:
            url = "http://127.0.0.1:8777/api/capa?arquivo=" + urllib.request.quote(payload)
            try:
                with urllib.request.urlopen(url, timeout=5) as resp:
                    corpo = resp.read()
                    vazou = b"CONTEUDO_SECRETO_DE_TESTE" in corpo
                    resultados.append((payload, resp.status, vazou))
            except urllib.error.HTTPError as e:
                resultados.append((payload, e.code, False))

        servidor.shutdown()
        servidor.server_close()

        print("Resultado do teste de travessia em /api/capa:\n")
        vazamento = False
        for payload, status, vazou in resultados:
            marca = "VAZOU O SEGREDO!!" if vazou else "bloqueado"
            print("  %-55s status=%s  %s" % (payload, status, marca))
            if vazou:
                vazamento = True

        print("\nRESULTADO:", "FALHOU (vazamento de arquivo fora da pasta)" if vazamento else "PASSOU (nenhuma travessia vazou o segredo)")
        return 1 if vazamento else 0
    finally:
        sys.path = [p for p in sys.path if not p.startswith(destino)]
        shutil.rmtree(destino, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
