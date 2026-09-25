# -*- coding: utf-8 -*-
r"""Revisao pos-auditoria: download REAL do acervo, com internet.

Pendencia antiga do CLAUDE.md ("Testar o download real do acervo -- nunca
foi exercitado com internet"). O acervo desta pasta esta vazio (nenhum jogo
cadastrado), entao o teste cadastra, numa COPIA isolada, um arquivo pequeno
de uma origem permitida (raw.githubusercontent.com) e usa o codigo de
verdade (acervo.salvar + acervo.instalar):
  1. SHA-256 certo -> instala em jogos\livres, conteudo identico;
  2. SHA-256 errado -> recusa, e nao sobra arquivo nenhum;
  3. origem fora da lista -> recusa no cadastro.
Sem internet, avisa e sai sem reprovar (nao ha o que testar).
"""
import hashlib
import importlib.util
import os
import shutil
import sys
import tempfile
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "https://raw.githubusercontent.com/libretro/RetroArch/master/COPYING"


def main():
    try:
        with urllib.request.urlopen(urllib.request.Request(URL, headers={"User-Agent": "ARENA/1.0"}),
                                    timeout=20) as r:
            conteudo = r.read()
    except Exception as falha:
        print("Sem internet ou origem fora do ar (%s). Nada a testar." % falha)
        return 0
    certo = hashlib.sha256(conteudo).hexdigest()
    print("Arquivo de teste: %s (%d bytes)" % (URL, len(conteudo)))

    destino = tempfile.mkdtemp(prefix="arena_acervo_real_")
    try:
        shutil.copytree(os.path.join(RAIZ, "servidor"), os.path.join(destino, "servidor"),
                        ignore=shutil.ignore_patterns("__pycache__", "tests", "python"))
        os.makedirs(os.path.join(destino, "dados"))
        os.makedirs(os.path.join(destino, "jogos", "livres"))
        sys.path.insert(0, os.path.join(destino, "servidor"))
        spec = importlib.util.spec_from_file_location("acervo_real", os.path.join(destino, "servidor", "acervo.py"))
        acervo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(acervo)

        base = {"titulo": "Arquivo de teste", "plataforma": "Teste", "licenca": "GPL-3.0",
                "fonte": "https://github.com/libretro/RetroArch", "url": URL,
                "autorizado": True, "tamanho": len(conteudo)}
        ok = True

        acervo.salvar(dict(base, id="certo", sha256=certo, destino="jogos/livres/certo.txt"))
        resultado = acervo.instalar("certo")
        arquivo = os.path.join(destino, "jogos", "livres", "certo.txt")
        igual = os.path.isfile(arquivo) and open(arquivo, "rb").read() == conteudo
        print("1. SHA certo: instalado %s, conteudo identico: %s" % (resultado, igual))
        ok = ok and igual

        acervo.salvar(dict(base, id="errado", sha256="0" * 64, destino="jogos/livres/errado.txt"))
        try:
            acervo.instalar("errado")
            print("2. SHA errado: INSTALOU (bug!)")
            ok = False
        except ValueError as falha:
            sobrou = [n for n in os.listdir(os.path.join(destino, "jogos", "livres")) if n.startswith("errado")]
            print("2. SHA errado: recusado (%s); sobrou: %s" % (falha, sobrou))
            ok = ok and not sobrou

        try:
            acervo.salvar(dict(base, id="fora", sha256=certo, destino="jogos/livres/fora.txt",
                               url="https://exemplo.com/jogo.zip"))
            print("3. Origem fora da lista: ACEITO (bug!)")
            ok = False
        except ValueError as falha:
            print("3. Origem fora da lista: recusado (%s)" % falha)

        print("\nRESULTADO:", "PASSOU" if ok else "FALHOU")
        return 0 if ok else 1
    finally:
        sys.path = [p for p in sys.path if not p.startswith(destino)]
        shutil.rmtree(destino, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
