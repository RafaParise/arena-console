# -*- coding: utf-8 -*-
"""Testa a busca e o download da biblioteca online de verdade.

Chama internet_archive.buscar()/instalar() direto (nao pela API HTTP) -
o /api/biblioteca-online exige VIGIA["internet"] == True, que so fica
pronto depois do primeiro ciclo do vigia (ate 60s numa maquina normal);
esperar isso so pra testar seria lento sem motivo, ja que o que muda
neste commit e' dentro do internet_archive.py e na chamada que o
arena.py faz pra ele - dá pra testar os dois direto.

Roda: servidor\\python\\python.exe ferramentas\\teste_biblioteca_online.py
"""
import os
import shutil
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
import internet_archive  # noqa: E402

PASTA_BAIXADA = os.path.join(RAIZ, "jogos", "livres", "MS-DOS")   # desde 02/10/2026 (era "Internet Archive")


def arquivos_baixados():
    """Os arquivos que ja estavam na pasta da biblioteca online."""
    achados = set()
    for pasta, _sub, nomes in os.walk(PASTA_BAIXADA):
        achados.update(os.path.join(pasta, n) for n in nomes)
    return achados


# Corrigido em 01/10/2026: a versao anterior APAGAVA a pasta
# jogos\livres\Internet Archive inteira, no comeco e no fim -- os jogos
# que o aluno baixou pela biblioteca online iam junto. Agora apaga so o que
# ESTE teste baixou.
ANTES = set()


def main():
    ANTES.update(arquivos_baixados())

    itens = internet_archive.buscar("game")
    print("Achou %d item(ns) buscando 'game'." % len(itens))
    if not itens:
        print("FALHOU: busca nao trouxe nada (pode ser rede indisponivel "
             "neste ambiente).")
        return 1

    for item in itens[:5]:
        print(" -", item["titulo"], "|", item["arquivo"], "|", item["fonte"])

    item = itens[0]
    print("Baixando:", item["titulo"], "-", item["arquivo"])

    # Mesma chamada que o handler /api/biblioteca-online/instalar faz
    # (dados.get("id"), dados.get("arquivo"), dados.get("plataforma")) -
    # e' exatamente a assinatura que estava quebrada antes desta correcao.
    resultado = internet_archive.instalar(item["id"], item["arquivo"], "")
    print("Resultado do download:", resultado)

    caminho_esperado = os.path.join(PASTA_BAIXADA, item["arquivo"])
    if not os.path.isfile(caminho_esperado):
        print("FALHOU: arquivo nao apareceu em", caminho_esperado)
        return 1
    print("OK: busca e download funcionam de ponta a ponta, com a colecao "
         "livre restaurada.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    finally:
        for caminho in arquivos_baixados() - ANTES:
            try:
                os.remove(caminho)
            except OSError:
                pass
        if os.path.isdir(PASTA_BAIXADA) and not os.listdir(PASTA_BAIXADA) and not ANTES:
            shutil.rmtree(PASTA_BAIXADA, ignore_errors=True)
