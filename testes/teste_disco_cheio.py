# -*- coding: utf-8 -*-
r"""Revisao pos-auditoria: disco cheio no meio de uma gravacao.

Pendencia da Fase 6 (so tinha sido conferido lendo o codigo). Nao da para
encher um disco de verdade com seguranca, entao o teste faz o Windows
"responder" o mesmo erro que ele da com disco cheio (ENOSPC, "No space left
on device") no momento de gravar, e confere:
  1. o arquivo antigo continua inteiro e legivel;
  2. nao sobra arquivo temporario;
  3. pela API (/api/config), o aluno recebe mensagem em portugues, sem
     traceback, e o servidor continua de pe.
"""
import errno
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
    destino = tempfile.mkdtemp(prefix="arena_disco_cheio_")
    servidor = None
    try:
        for pasta in ("servidor", "dados", "launcher"):
            shutil.copytree(os.path.join(RAIZ, pasta), os.path.join(destino, pasta),
                            ignore=shutil.ignore_patterns("__pycache__", "tests", "python", "*.log"))
        sys.path.insert(0, os.path.join(destino, "servidor"))
        spec = importlib.util.spec_from_file_location("arena_cheio", os.path.join(destino, "servidor", "arena.py"))
        arena = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(arena)

        cfg = os.path.join(destino, "dados", "config.json")
        antes = open(cfg, encoding="utf-8").read()

        fsync_de_verdade = os.fsync

        def disco_cheio(_fd):
            raise OSError(errno.ENOSPC, "No space left on device")

        # --- 1 e 2: direto na funcao ---
        arena.os.fsync = disco_cheio
        try:
            arena.gravar_texto_atomico(cfg, '{"tema": "escuro"}')
            print("NAO deu erro (inesperado)")
        except OSError as falha:
            print("Gravacao falhou como no disco cheio:", falha)
        finally:
            arena.os.fsync = fsync_de_verdade
        intacto = open(cfg, encoding="utf-8").read() == antes
        json.loads(open(cfg, encoding="utf-8").read())
        sobras = [n for n in os.listdir(os.path.dirname(cfg)) if n.endswith(".tmp")]
        print("Arquivo antigo intacto e legivel:", intacto)
        print("Temporarios que sobraram:", sobras)

        # --- 3: pela API ---
        servidor = arena.Servidor(("127.0.0.1", 8777), arena.Manipulador)
        threading.Thread(target=servidor.serve_forever, daemon=True).start()
        time.sleep(0.5)
        arena.os.fsync = disco_cheio
        try:
            pedido = urllib.request.Request(
                "http://127.0.0.1:8777/api/config", data=b'{"tema": "escuro"}', method="POST",
                headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(pedido, timeout=5) as r:
                    status, corpo = r.status, r.read().decode("utf-8")
            except urllib.error.HTTPError as e:
                status, corpo = e.code, e.read().decode("utf-8")
        finally:
            arena.os.fsync = fsync_de_verdade
        print("API: status %s, resposta %s" % (status, corpo))
        mensagem = json.loads(corpo).get("erro", "")
        crua = "Errno" in mensagem or "No space" in mensagem or "Traceback" in corpo
        with urllib.request.urlopen("http://127.0.0.1:8777/api/estado", timeout=5) as r:
            de_pe = r.status == 200
        intacto_api = open(cfg, encoding="utf-8").read() == antes
        print("Mensagem sem texto cru do sistema:", not crua)
        print("Servidor continua de pe:", de_pe)
        print("Arquivo continua intacto depois da API:", intacto_api)

        ok = intacto and not sobras and status >= 400 and not crua and de_pe and intacto_api
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
