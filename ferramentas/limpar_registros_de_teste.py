# -*- coding: utf-8 -*-
r"""Registros que TESTES deixaram no dados\arena.db de verdade.

Achado de 01/10/2026 (so leitura): o banco desta maquina tem
  - 2 recordes de teste ("Ana" e "Bruno", aparelhos "maquina-certa" e
    "maquina-relogio-errado") -- do teste do relogio errado de 24/09;
  - sessoes com apelido "hospedeiro" e "teste" (21 a 26/09) -- das
    ferramentas antigas que abrem jogo pelo ARENA de verdade
    (ferramentas\teste_netplay_*.py, teste_memory_card_ps1.py; tirados
    na auditoria 3 -- o que eles conferiam esta em testes\ e na bateria,
    numa copia isolada);
  - sessoes com apelido "aluno" (22/09) -- podem ser de teste OU do roteiro
    com conta de aluno: so saem com --com-aluno.
A bateria atual nao grava no banco de verdade (os testes usam copia).

Sem opcao, SO LISTA. Com --apagar: guarda uma copia do banco em backup\
e apaga so esses registros. E' dado do professor: so ele decide.

Uso:
    servidor\python\python.exe ferramentas\limpar_registros_de_teste.py
    servidor\python\python.exe ferramentas\limpar_registros_de_teste.py --apagar [--com-aluno]
"""
import os
import shutil
import sqlite3
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANCO = os.path.join(RAIZ, "dados", "arena.db")
APARELHOS_DE_TESTE = ("maquina-certa", "maquina-relogio-errado")
APELIDOS_DE_TESTE = ["hospedeiro", "teste"]


def main():
    apagar = "--apagar" in sys.argv
    apelidos = APELIDOS_DE_TESTE + (["aluno"] if "--com-aluno" in sys.argv else [])
    if not os.path.isfile(BANCO):
        print("Sem dados\\arena.db: nada a fazer.")
        return 0
    marcas = ",".join("?" * len(apelidos))
    filtros = {
        "placar": ("dispositivo IN (?, ?)", APARELHOS_DE_TESTE),
        "sessao": ("apelido IN (%s)" % marcas, tuple(apelidos)),
    }
    conexao = sqlite3.connect(BANCO if apagar else "file:%s?mode=ro" % BANCO, uri=not apagar)
    try:
        achados = 0
        for tabela, (onde, valores) in filtros.items():
            linhas = conexao.execute("SELECT apelido, jogo_titulo FROM %s WHERE %s" % (tabela, onde),  # auditoria: ok (tabela fixa; valores por parametro)
                                     valores).fetchall()
            achados += len(linhas)
            print("%s: %d registro(s) de teste" % ("recordes" if tabela == "placar" else "sessoes", len(linhas)))
            for apelido, titulo in linhas[:8]:
                print("   %-12s %s" % (apelido, titulo))
        if "--com-aluno" not in sys.argv:
            n = conexao.execute("SELECT COUNT(*) FROM sessao WHERE apelido = 'aluno'").fetchone()[0]
            if n:
                print("(%d sessao(oes) com apelido 'aluno' ficam: so saem com --com-aluno)" % n)
        if not apagar or not achados:
            print("\nNada foi apagado." + ("" if not achados else " Para apagar: --apagar"))
            return 0
        copia = os.path.join(RAIZ, "backup", "arena.db.antes-de-limpar-testes-%s" % time.strftime("%Y%m%d-%H%M%S"))
        os.makedirs(os.path.dirname(copia), exist_ok=True)
        conexao.close()
        shutil.copy2(BANCO, copia)
        conexao = sqlite3.connect(BANCO)
        with conexao:
            for tabela, (onde, valores) in filtros.items():
                conexao.execute("DELETE FROM %s WHERE %s" % (tabela, onde), valores)  # auditoria: ok (tabela fixa; valores por parametro)
        print("\nApagados %d registro(s). Copia do banco antes: %s" % (achados, copia))
        return 0
    finally:
        conexao.close()


if __name__ == "__main__":
    sys.exit(main())
