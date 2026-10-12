# -*- coding: utf-8 -*-
r"""Revisao pos-auditoria: a troca da marca de sincronizacao (data -> numero
de chegada) nao pode perder nada.

1. Migracao: numa COPIA do arena.db real (o original nao e' tocado), o banco
   antigo ganha a coluna nova e continua com exatamente os mesmos recordes
   e sessoes; todos os registros encerrados ganham numero.
2. Lotes: com mais registros do que cabe num envio (LIMITE_LOTE), pedir
   lote atras de lote, sempre com a marca devolvida, traz TODOS -- nenhum
   pulado, nenhum repetido.
"""
import contextlib
import importlib.util
import os
import shutil
import sqlite3
import sys
import tempfile
import uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "testes"))
import limpeza  # noqa: E402


def carregar_arena(destino):
    sys.path.insert(0, os.path.join(destino, "servidor"))
    spec = importlib.util.spec_from_file_location("arena_migra", os.path.join(destino, "servidor", "arena.py"))
    arena = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(arena)
    return arena


def main():
    destino = tempfile.mkdtemp(prefix="arena_sinc_migra_")
    ok = True
    try:
        shutil.copytree(os.path.join(RAIZ, "servidor"), os.path.join(destino, "servidor"),
                        ignore=shutil.ignore_patterns("__pycache__", "tests", "python"))
        shutil.copytree(os.path.join(RAIZ, "dados"), os.path.join(destino, "dados"),
                        ignore=shutil.ignore_patterns("*.log"))
        banco = os.path.join(destino, "dados", "arena.db")

        # --- 1. migracao de um banco real antigo ---
        # (contextlib.closing: o 'with' do sqlite3 so confirma a transacao, nao
        # fecha -- o arena.db ficava preso e a pasta nao saia do Temp.)
        if os.path.isfile(banco):
            with contextlib.closing(sqlite3.connect(banco)) as c:
                antes_p = c.execute("SELECT COUNT(*) FROM placar").fetchone()[0]
                antes_s = c.execute("SELECT COUNT(*) FROM sessao").fetchone()[0]
                tinha_seq = "seq" in {r[1] for r in c.execute("PRAGMA table_info(placar)")}
            arena = carregar_arena(destino)
            arena.preparar_banco()
            with contextlib.closing(sqlite3.connect(banco)) as c:
                depois_p = c.execute("SELECT COUNT(*) FROM placar").fetchone()[0]
                depois_s = c.execute("SELECT COUNT(*) FROM sessao").fetchone()[0]
                sem_numero = c.execute("SELECT COUNT(*) FROM placar WHERE seq IS NULL").fetchone()[0] + \
                    c.execute("SELECT COUNT(*) FROM sessao WHERE seq IS NULL AND encerrada = 1").fetchone()[0]
            print("Banco real (copia): tinha 'seq' antes? %s" % tinha_seq)
            print("  recordes %d -> %d, sessoes %d -> %d, encerrados sem numero: %d"
                  % (antes_p, depois_p, antes_s, depois_s, sem_numero))
            ok = ok and antes_p == depois_p and antes_s == depois_s and sem_numero == 0
            todos, _, _ = arena.registros_desde("")
            print("  registros_desde('') devolve %d recordes" % len(todos))
        else:
            arena = carregar_arena(destino)
            arena.preparar_banco()
            print("Sem arena.db real para migrar; so o teste de lotes.")

        # --- 2. lotes: 2,5 lotes de recordes novos ---
        total = int(arena.LIMITE_LOTE * 2.5)
        criados = set()
        _p, _s, marca = arena.registros_desde("")
        with arena.banco() as c:
            for i in range(total):
                u = "lote-%s" % uuid.uuid4().hex
                criados.add(u)
                arena.inserir_placar(c, u, "Aluno", "jogo", "Jogo", i, "2026-01-01T00:00:00Z", "outro")
        recebidos = []
        for _ in range(10):
            placares, _s, marca = arena.registros_desde(marca)
            if not placares:
                break
            recebidos += [p["uuid"] for p in placares]
        faltaram = criados - set(recebidos)
        repetidos = len(recebidos) - len(set(recebidos))
        print("Lotes: criados %d, recebidos %d, faltaram %d, repetidos %d"
              % (total, len(recebidos), len(faltaram), repetidos))
        ok = ok and not faltaram and repetidos == 0
        print("\nRESULTADO:", "PASSOU" if ok else "FALHOU")
        return 0 if ok else 1
    finally:
        sys.path = [p for p in sys.path if not p.startswith(destino)]
        # shutil.rmtree calado desistia de arquivo somente leitura ou preso (a rodada da auditoria 3 achava esta pasta no Temp).
        limpeza.apagar_pasta(destino)


if __name__ == "__main__":
    sys.exit(main())
