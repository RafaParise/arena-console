# -*- coding: utf-8 -*-
"""Fase 3: confere as correcoes em internet_archive.instalar():
  1. download que cai no meio (curl falha) -- erro claro, nao crash.
  2. SHA-1 errado (nao bate com o que o Internet Archive declarou) --
     recusado, arquivo nao fica instalado.
  3. caminho feliz -- baixa normal quando tudo bate.

Monkeypatcha _ler() e baixar.rodar() (o download passa por ele desde
17/10/2026: o curl quando ha, senao o proprio Python) -- nao depende de rede
de verdade. Usa uma pasta isolada, nao mexe em jogos\\livres real.
"""
import hashlib
import importlib.util
import os
import shutil
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def carregar(destino_livres):
    spec = importlib.util.spec_from_file_location(
        "ia_teste_download", os.path.join(RAIZ, "servidor", "internet_archive.py"))
    ia = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ia)
    ia.PASTA_LIVRES = destino_livres
    return ia


def baixar_que_grava(dados):
    """O falso do baixar.rodar que grava 'dados' no arquivo de destino."""
    def rodar(url, segundos, destino=None, **_extras):
        if destino:
            with open(destino, "wb") as arquivo:
                arquivo.write(dados)
            return 0, b""
        return 0, dados
    return rodar


def meta_falsa(conteudo, nome_arquivo="jogo.zip"):
    sha1 = hashlib.sha1(conteudo).hexdigest()
    return {
        "metadata": {"title": "Jogo de Teste", "collection": ["softwarelibrary_msdos_shareware"]},
        "files": [{"name": nome_arquivo, "size": str(len(conteudo)), "sha1": sha1}],
    }, sha1


def main():
    destino_livres = tempfile.mkdtemp(prefix="arena_ia_download_")
    try:
        conteudo = b"conteudo de teste do internet archive, fixo"
        meta, sha1_certo = meta_falsa(conteudo)

        # ---- Caso 1: download cai no meio (curl falha) ----
        print("--- Caso 1: curl falha no meio do download ---")
        ia = carregar(destino_livres)
        ia._ler = lambda url: meta

        def baixar_falha(url, segundos, destino=None, **_extras):
            return 56, b""      # o codigo do curl para a conexao que caiu no meio
        ia.baixar.rodar = baixar_falha

        try:
            ia.instalar("item-teste", "jogo.zip")
            print("NAO RECUSOU (bug!)")
            caso1_ok = False
        except ValueError as e:
            print("OK, recusado com mensagem clara:", e)
            caso1_ok = "internet" in str(e).lower() or "download" in str(e).lower()
        except Exception as e:
            print("NAO TRATADO:", type(e).__name__, e)
            caso1_ok = False

        # ---- Caso 2: SHA-1 nao bate (download adulterado/incompleto) ----
        print("\n--- Caso 2: SHA-1 nao bate com o declarado ---")
        ia = carregar(destino_livres)
        ia._ler = lambda url: meta

        conteudo_errado = b"CONTEUDO TROCADO, NAO E O DECLARADO NO METADADO"
        ia.baixar.rodar = baixar_que_grava(conteudo_errado)

        try:
            ia.instalar("item-teste", "jogo.zip")
            print("NAO RECUSOU (bug!)")
            caso2_ok = False
        except ValueError as e:
            print("OK, recusado:", e)
            caso2_ok = "sha-1" in str(e).lower() or "seguranca" in str(e).lower()
        alvo_final = os.path.join(destino_livres, "MS-DOS", "jogo.zip")   # a pasta do console da colecao (02/10/2026)
        caso2_sem_arquivo = not os.path.isfile(alvo_final)
        print("Arquivo NAO instalado (esperado):", caso2_sem_arquivo)

        # ---- Caso 3: caminho feliz, tudo bate ----
        print("\n--- Caso 3: conteudo certo -- tem que instalar ---")
        ia = carregar(destino_livres)
        ia._ler = lambda url: meta

        ia.baixar.rodar = baixar_que_grava(conteudo)

        try:
            resultado = ia.instalar("item-teste", "jogo.zip")
            caso3_ok = os.path.isfile(alvo_final)
            print("OK, instalado:", resultado, "| arquivo existe:", caso3_ok)
        except ValueError as e:
            print("RECUSOU (bug!):", e)
            caso3_ok = False

        ok = caso1_ok and caso2_ok and caso2_sem_arquivo and caso3_ok
        print("\nRESULTADO:", "PASSOU" if ok else "FALHOU")
        return 0 if ok else 1
    finally:
        shutil.rmtree(destino_livres, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
