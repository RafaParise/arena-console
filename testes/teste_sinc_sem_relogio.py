# -*- coding: utf-8 -*-
r"""Revisao pos-auditoria: a sincronizacao nao pode depender do relogio.

Dois defeitos reais, os dois por causa do mesmo desenho (o cursor de "o que
ja mandei" era a DATA do registro):

1. Relogio errado: um notebook com o relogio em 2020 grava recorde com data
   de 2020. Quem ja sincronizou hoje pede "o que ha de novo desde hoje" --
   e o recorde de "2020" nunca aparece. Fica invisivel para sempre.
2. Partida longa: a sessao de jogo e' gravada no COMECO da partida e so
   fica "encerrada" no fim. Se houver uma sincronizacao no meio (o vigia
   tenta a cada 90 s), o cursor passa da hora de inicio, e a sessao, quando
   fecha, nunca mais e' enviada.

O teste roda num banco isolado e usa as funcoes de verdade do arena.py.
"""
import importlib.util
import os
import shutil
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    destino = tempfile.mkdtemp(prefix="arena_sinc_relogio_")
    try:
        for pasta in ("servidor", "dados"):
            shutil.copytree(os.path.join(RAIZ, pasta), os.path.join(destino, pasta),
                            ignore=shutil.ignore_patterns("__pycache__", "tests", "python", "arena.db*"))
        sys.path.insert(0, os.path.join(destino, "servidor"))
        spec = importlib.util.spec_from_file_location("arena_sinc", os.path.join(destino, "servidor", "arena.py"))
        arena = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(arena)
        arena.preparar_banco()

        # Um colega ja sincronizou com este computador: o cursor dele e' o
        # "ate" que recebeu (o que o arena.py devolve de verdade).
        _p, _s, cursor = arena.registros_desde("")

        # --- caso 1: recorde gravado com o relogio errado (2020) ---
        with arena.banco() as c:
            arena.inserir_placar(c, "relogio-errado-1", "Aluno", "jogo", "Jogo", 999,
                                 "2020-01-01T10:00:00Z", "outro-aparelho")
        # --- caso 2: partida longa, com uma sincronizacao no meio ---
        with arena.banco() as c:
            arena.abrir_sessao(c, "sessao-longa-1", "Aluno", "jogo", "Jogo",
                               arena.agora_utc(), "outro-aparelho")
        _p, _s, cursor_meio = arena.registros_desde(cursor)  # sinc. no meio da partida
        with arena.banco() as c:
            arena.encerrar_sessao(c, "sessao-longa-1", 600)

        placares, sessoes, _ = arena.registros_desde(cursor_meio)
        todos_placares, _, _ = arena.registros_desde(cursor)
        viu_relogio = any(p["uuid"] == "relogio-errado-1" for p in todos_placares)
        viu_sessao = any(s["uuid"] == "sessao-longa-1" for s in sessoes)
        print("Recorde gravado com relogio em 2020 chega ao colega:", viu_relogio)
        print("Partida longa (sinc. no meio) chega ao colega quando fecha:", viu_sessao)
        ok = viu_relogio and viu_sessao
        print("\nRESULTADO:", "PASSOU" if ok else "FALHOU")
        return 0 if ok else 1
    finally:
        sys.path = [p for p in sys.path if not p.startswith(destino)]
        shutil.rmtree(destino, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
