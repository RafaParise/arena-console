"""Confere a correcao da Fase 1 (achado #4): se a copia de seguranca falhar,
'Comecar do zero' (/api/perfil/novo) tem que CANCELAR o apagamento, nao
apagar os arquivos do usuario do mesmo jeito. E o caminho feliz (backup
funciona) continua apagando normalmente.

Monta um ARENA isolado numa pasta temporaria (copia servidor/dados/launcher
-- nao precisa de retroarch/emuladores/jogos para este teste), importa o
arena.py de dentro dela (em processo, nao como servidor externo, para poder
substituir fazer_backup() por uma versao que sempre falha no Caso 2) e
confere o estado dos arquivos antes/depois de cada chamada.

Nao mexe na pasta real do projeto.
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
ARQUIVOS_DE_PERFIL = ("arena.db", "config.json", "controles.json")


def preparar_copia_isolada(destino):
    for pasta in ("servidor", "dados", "launcher"):
        shutil.copytree(os.path.join(RAIZ, pasta), os.path.join(destino, pasta),
                         ignore=shutil.ignore_patterns("__pycache__", "tests"))


def estado_dos_arquivos(destino):
    return {nome: os.path.isfile(os.path.join(destino, "dados", nome))
            for nome in ARQUIVOS_DE_PERFIL}


def chamar_perfil_novo(arena, destino):
    servidor = arena.Servidor(("127.0.0.1", 8777), arena.Manipulador)
    thread = threading.Thread(target=servidor.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.5)
    try:
        corpo = json.dumps({"confirmar": "sim"}).encode("utf-8")
        req = urllib.request.Request(
            "http://127.0.0.1:8777/api/perfil/novo", data=corpo,
            method="POST", headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as erro:
            return erro.code, json.loads(erro.read())
    finally:
        servidor.shutdown()
        servidor.server_close()


def carregar_arena_isolado(destino):
    caminho_arena = os.path.join(destino, "servidor", "arena.py")
    spec = importlib.util.spec_from_file_location("arena_teste_%d" % time.time_ns(), caminho_arena)
    arena = importlib.util.module_from_spec(spec)
    sys.path.insert(0, os.path.join(destino, "servidor"))
    spec.loader.exec_module(arena)
    return arena


def caso_feliz():
    print("--- Caso 1: copia de seguranca funciona (caminho feliz) ---")
    destino = tempfile.mkdtemp(prefix="arena_teste_backup_ok_")
    try:
        preparar_copia_isolada(destino)
        arena = carregar_arena_isolado(destino)

        antes = estado_dos_arquivos(destino)
        print("Arquivos antes:", antes)
        status, resposta = chamar_perfil_novo(arena, destino)
        print("Status HTTP:", status, "| Resposta:", resposta)
        depois = estado_dos_arquivos(destino)
        print("Arquivos depois:", depois)

        # controles.json de verdade fica apagado (nada recria na hora); ja
        # arena.db e config.json voltam a existir DENTRO da mesma chamada,
        # porque o proprio servidor os recria vazios ao montar a resposta
        # (dispositivo_id novo, banco default) -- isso e esperado, nao e o
        # que este teste confere. O que importa aqui e que apagou de
        # verdade (resposta com contagem) e que a copia de seguranca foi
        # criada antes.
        ok = (status == 200 and resposta.get("apagados") == 5
              and depois["controles.json"] is False
              and os.path.isdir(os.path.join(destino, "backup"))
              and len(os.listdir(os.path.join(destino, "backup"))) >= 1)
        return ok
    finally:
        sys.path = [p for p in sys.path if not p.startswith(destino)]
        shutil.rmtree(destino, ignore_errors=True)


def caso_falha():
    print("\n--- Caso 2: copia de seguranca falha (achado #4) ---")
    destino = tempfile.mkdtemp(prefix="arena_teste_backup_falha_")
    try:
        preparar_copia_isolada(destino)
        arena = carregar_arena_isolado(destino)
        # Simula a copia de seguranca falhando -- exatamente o que a
        # correcao precisa detectar e respeitar.
        arena.fazer_backup = lambda: None

        antes = estado_dos_arquivos(destino)
        print("Arquivos antes:", antes)
        status, resposta = chamar_perfil_novo(arena, destino)
        print("Status HTTP:", status, "| Resposta:", resposta)
        depois = estado_dos_arquivos(destino)
        print("Arquivos depois:", depois)

        ok = (status >= 400 and antes == depois and all(depois.values()))
        return ok
    finally:
        sys.path = [p for p in sys.path if not p.startswith(destino)]
        shutil.rmtree(destino, ignore_errors=True)


def main():
    ok1 = caso_feliz()
    ok2 = caso_falha()
    print("\nRESULTADO Caso 1 (apaga quando backup funciona):", "PASSOU" if ok1 else "FALHOU")
    print("RESULTADO Caso 2 (cancela quando backup falha):", "PASSOU" if ok2 else "FALHOU")
    return 0 if (ok1 and ok2) else 1


if __name__ == "__main__":
    sys.exit(main())
