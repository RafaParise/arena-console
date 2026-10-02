# -*- coding: utf-8 -*-
r"""Biblioteca online: busca pelo NOME e jogo baixado no console certo.

Achado de 02/10/2026. O Rafael: "o sistema da biblioteca nao funciona, eu
pesquisei Mario para console de super nintendo, ele achou um monte de coisa
aleatoria". Duas causas:
  - a busca olhava o titulo OU A DESCRICAO: voltava jogo de DOS que so
    citava a palavra no texto;
  - o jogo baixado ia para jogos\livres\Internet Archive, e la um .zip de
    DOS virava "Precisa escolher o console" (o indexador decide pela pasta).
E a tela nao dizia que a biblioteca so tem MS-DOS (as unicas colecoes com
licenca livre conferida); Mario e' da Nintendo, nao e' livre.

  1. a consulta e' so no titulo, com todas as palavras, e so nas colecoes
     livres; resultado sem a palavra no titulo e' descartado;
  2. o jogo baixado vai para jogos\livres\MS-DOS e o indexador de verdade o
     reconhece como MS-DOS;
  3. com internet: "Mario" so traz titulos com Mario, "mario super
     nintendo" nao traz nada, "keen" traz o Commander Keen (de DOS).

Uso: servidor\python\python.exe testes\teste_biblioteca_busca.py
"""
import hashlib
import importlib.util
import json
import os
import socket
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
import limpeza  # noqa: E402


def carregar_ia(pasta_livres):
    spec = importlib.util.spec_from_file_location(
        "ia_busca_%d" % os.getpid(), os.path.join(RAIZ, "servidor", "internet_archive.py"))
    ia = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ia)
    ia.PASTA_LIVRES = pasta_livres
    return ia


def tem_internet():
    try:
        socket.create_connection(("archive.org", 443), timeout=4).close()
        return True
    except OSError:
        return False


def main():
    falhas, total = [], [0]

    def confere(nome, ok, detalhe=""):
        total[0] += 1
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, "" if ok else detalhe), flush=True)
        if not ok:
            falhas.append(nome)

    pasta = tempfile.mkdtemp(prefix="arena_biblioteca_")
    try:
        livres = os.path.join(pasta, "jogos", "livres")
        ia = carregar_ia(livres)

        print("1. A consulta")
        consulta = ia.consulta_do_archive(ia.palavras_da_busca("Mario super-nintendo!!"), ia.COLECOES_LIVRES)
        confere("so no titulo, com todas as palavras",
                "title:(mario AND super AND nintendo)" in consulta and "description" not in consulta, consulta)
        confere("so nas colecoes livres", "collection:softwarelibrary_msdos_shareware" in consulta, consulta)
        confere("simbolos e comandos (OR) nao viram parte da consulta",
                ia.palavras_da_busca('a"; OR *') == ["a", "or"], ia.palavras_da_busca('a"; OR *'))

        conteudo = b"PK\x05\x06" + b"\x00" * 18
        respostas = {
            "advancedsearch": {"response": {"docs": [{"identifier": "jogo_com_mario"},
                                                      {"identifier": "so_cita_na_descricao"}]}},
            "jogo_com_mario": {"metadata": {"title": "Mario VGA", "collection": ["softwarelibrary_msdos_shareware"]},
                               "files": [{"name": "mario.zip", "size": str(len(conteudo)),
                                          "sha1": hashlib.sha1(conteudo).hexdigest()}]},
            "so_cita_na_descricao": {"metadata": {"title": "Outro Jogo", "description": "melhor que Mario",
                                                  "collection": ["softwarelibrary_msdos_shareware"]},
                                     "files": [{"name": "outro.zip", "size": "10"}]},
        }

        def ler_falso(url):
            chave = "advancedsearch" if "advancedsearch" in url else url.rsplit("/", 1)[-1]
            return json.loads(json.dumps(respostas[chave]))
        ia._ler = ler_falso
        itens = ia.buscar("Mario")
        confere("resultado sem a palavra no titulo e' descartado",
                [i["titulo"] for i in itens] == ["Mario VGA"], [i["titulo"] for i in itens])
        confere("cada resultado diz o console (MS-DOS)",
                itens and itens[0].get("plataforma") == "dos" and itens[0].get("plataforma_nome") == "MS-DOS", itens)

        print("2. O jogo baixado vai para o console certo")
        real_run = ia.subprocess.run

        def curl_falso(comando, **kwargs):
            destino = comando[comando.index("-o") + 1]
            open(destino, "wb").write(conteudo)
            return subprocess.CompletedProcess(comando, 0)
        ia.subprocess.run = curl_falso
        try:
            resultado = ia.instalar("jogo_com_mario", "mario.zip", "snes")   # a tela nao manda no console
        finally:
            ia.subprocess.run = real_run
        baixado = os.path.join(livres, "MS-DOS", "mario.zip")
        confere("baixado em jogos\\livres\\MS-DOS (nao em 'Internet Archive', nem no console pedido)",
                os.path.isfile(baixado) and not os.path.exists(os.path.join(livres, "Internet Archive")),
                os.listdir(livres))
        confere("a resposta diz o console", resultado.get("plataforma_nome") == "MS-DOS", resultado)

        import indexador
        guardado = (indexador.PASTA_JOGOS, indexador.PASTA_DADOS, indexador.ARQUIVO_MANIFESTO,
                    indexador.ARQUIVO_MANUAIS, indexador.arquivo_de_jogadores)
        dados = os.path.join(pasta, "dados")
        os.makedirs(dados)
        try:
            indexador.PASTA_JOGOS = os.path.join(pasta, "jogos")
            indexador.PASTA_DADOS = dados
            indexador.ARQUIVO_MANIFESTO = os.path.join(dados, "manifesto.json")
            indexador.ARQUIVO_MANUAIS = os.path.join(dados, "consoles_manuais.json")
            indexador.arquivo_de_jogadores = lambda: os.path.join(dados, "jogadores.txt")
            jogos = indexador.indexar(forcar=True).get("jogos", [])
        finally:
            (indexador.PASTA_JOGOS, indexador.PASTA_DADOS, indexador.ARQUIVO_MANIFESTO,
             indexador.ARQUIVO_MANUAIS, indexador.arquivo_de_jogadores) = guardado
        console = next((j.get("plataforma") for j in jogos if j["arquivo"].endswith("mario.zip")), None)
        confere("o indexador de verdade reconhece como MS-DOS (antes: 'Precisa escolher o console')",
                console == "dos", console)

        print("3. Com internet (Internet Archive de verdade)")
        if not tem_internet():
            print("  (sem internet agora: pulado)")
        else:
            ia_real = carregar_ia(livres)
            mario = ia_real.buscar("Mario")
            confere("'Mario': so titulos com Mario (%d)" % len(mario),
                    all("mario" in i["titulo"].casefold() for i in mario), [i["titulo"] for i in mario])
            confere("'mario super nintendo': nada (nao ha Super Nintendo livre aqui)",
                    ia_real.buscar("mario super nintendo") == [])
            keen = ia_real.buscar("keen")
            confere("'keen': acha o Commander Keen, de MS-DOS",
                    any("keen" in i["titulo"].casefold() and i["plataforma"] == "dos" for i in keen),
                    [i["titulo"] for i in keen])
    finally:
        limpeza.apagar_pasta(pasta)

    print()
    if falhas:
        print("FALHOU: %d de %d" % (len(falhas), total[0]))
        return 1
    print("Biblioteca: %d de %d certos." % (total[0], total[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
