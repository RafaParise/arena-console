# -*- coding: utf-8 -*-
"""Fase 3: confere que acervo.py recusa de verdade um download cujo
SHA-256 nao bate com o declarado -- item explicito do plano da auditoria.

Monkeypatcha urllib.request.urlopen dentro do modulo acervo para devolver
um conteudo conhecido (sem precisar de rede nem HTTPS de verdade), grava
um item no manifesto com uma URL de host permitido (so pra passar na
validacao de origem) e chama instalar() primeiro com SHA-256 errado
(tem que recusar) e depois certo (tem que aceitar).

Usa uma copia isolada de dados/acervo_autorizado.json -- nao mexe no
manifesto real.
"""
import hashlib
import importlib.util
import io
import os
import shutil
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class RespostaFalsa:
    def __init__(self, conteudo):
        self._buffer = io.BytesIO(conteudo)

    def read(self, n=-1):
        return self._buffer.read(n)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass


def main():
    destino_dados = tempfile.mkdtemp(prefix="arena_acervo_sha_")
    try:
        conteudo = b"conteudo de teste do acervo, nao muda"
        sha_certo = hashlib.sha256(conteudo).hexdigest()
        sha_errado = "0" * 64

        spec = importlib.util.spec_from_file_location(
            "acervo_teste_sha", os.path.join(RAIZ, "servidor", "acervo.py"))
        acervo = importlib.util.module_from_spec(spec)
        sys.path.insert(0, os.path.join(RAIZ, "servidor"))
        spec.loader.exec_module(acervo)

        # isola o manifesto e a pasta de destino (nao mexe no real)
        acervo.RAIZ = destino_dados
        acervo.ARQUIVO = os.path.join(destino_dados, "dados", "acervo_autorizado.json")
        acervo.PASTA_LIVRES = os.path.join(destino_dados, "jogos", "livres")
        os.makedirs(os.path.join(destino_dados, "dados"), exist_ok=True)
        os.makedirs(acervo.PASTA_LIVRES, exist_ok=True)

        # intercepta a rede -- sem isto precisaria de HTTPS de verdade
        acervo.urllib.request.urlopen = lambda req, timeout=30: RespostaFalsa(conteudo)

        item_base = {
            "id": "teste-sha256",
            "titulo": "Jogo de teste SHA-256",
            "plataforma": "nes",
            "licenca": "dominio publico (teste)",
            "fonte": "https://archive.org/details/teste",
            "url": "https://archive.org/download/teste/arquivo.zip",
            "destino": "jogos/livres/arquivo_teste.zip",
            "autorizado": True,
        }

        print("--- Caso 1: SHA-256 ERRADO no manifesto -- tem que recusar ---")
        acervo.salvar(dict(item_base, sha256=sha_errado))
        try:
            acervo.instalar("teste-sha256")
            print("NAO RECUSOU (bug!)")
            caso1_ok = False
        except ValueError as e:
            print("OK, recusado:", e)
            caso1_ok = "sha-256" in str(e).lower() or "seguranca" in str(e).lower()
        destino_arquivo = os.path.join(acervo.PASTA_LIVRES, "arquivo_teste.zip")
        caso1_sem_arquivo = not os.path.isfile(destino_arquivo)
        print("Arquivo NAO foi criado (esperado):", caso1_sem_arquivo)

        print("\n--- Caso 2: SHA-256 CERTO -- tem que aceitar ---")
        acervo.salvar(dict(item_base, sha256=sha_certo))
        acervo.urllib.request.urlopen = lambda req, timeout=30: RespostaFalsa(conteudo)
        try:
            resultado = acervo.instalar("teste-sha256")
            caso2_ok = os.path.isfile(destino_arquivo)
            print("OK, aceito:", resultado, "| arquivo criado:", caso2_ok)
        except ValueError as e:
            print("RECUSOU (bug!):", e)
            caso2_ok = False

        ok = caso1_ok and caso1_sem_arquivo and caso2_ok
        print("\nRESULTADO:", "PASSOU" if ok else "FALHOU")
        return 0 if ok else 1
    finally:
        sys.path = [p for p in sys.path if not p.startswith(destino_dados)]
        shutil.rmtree(destino_dados, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
