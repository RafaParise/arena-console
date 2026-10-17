# -*- coding: utf-8 -*-
r"""
ARENA - a biblioteca de jogos livres, para mais consoles alem do MS-DOS.

Pedido do Rafael (15/10/2026): "biblioteca de jogos livres para mais
consoles, como a do MS-DOS", com os jogos homebrew de licenca aberta e os
jogos de fliperama que a equipe do MAME liberou (mamedev.org).

A lista e' curada a mao (servidor\biblioteca_livre.json): cada jogo com o
endereco de quem publicou, o tamanho, a marca SHA-256 e a licenca, e cada um
foi aberto no nucleo do ARENA antes de entrar. Nenhum destes arquivos vai no
pacote: o ARENA baixa do site de quem publicou quando a pessoa pede, confere
a marca e poe em jogos\livres\<pasta do console> -- a pasta decide o console.

Os do mamedev.org so podem vir de la ("approved for free distribution on
this site only") e sao para uso nao comercial: a tela pede a mesma
confirmacao que o site pede (o "aceite" do jogo), e o servidor confere de
novo, para ninguem baixar sem ela.
"""
import hashlib
import json
import os
import threading

import baixar
from internet_archive import FalhaDeRede, parece_pagina_de_login

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_LIVRES = os.path.join(RAIZ, "jogos", "livres")
ARQUIVO_LISTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "biblioteca_livre.json")
ARQUIVO_CONSOLES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "consoles.json")
SEGUNDOS = 180               # o maior jogo da lista tem uns 16 MB

MENSAGEM_REDE = ("Não consegui baixar o jogo agora: a internet caiu ou o site de quem publicou não "
                 "respondeu. Tente de novo daqui a pouco.")
MENSAGEM_PORTAL = ("A rede pediu login: chegou a página do Wi-Fi no lugar do jogo. Abra o navegador, "
                   "entre na rede e tente de novo.")

_trava = threading.Lock()
_cache = {}


def lista_curada():
    """A biblioteca_livre.json, lida uma vez ({"jogos": [...]})."""
    with _trava:
        if "lista" not in _cache:
            try:
                with open(ARQUIVO_LISTA, encoding="utf-8") as arquivo:
                    _cache["lista"] = json.load(arquivo)
            except (OSError, ValueError):
                _cache["lista"] = {"jogos": []}
        return _cache["lista"]


def consoles():
    """{id: {"nome", "pasta"}} do consoles.json."""
    with _trava:
        if "consoles" in _cache:
            return _cache["consoles"]
    try:
        with open(ARQUIVO_CONSOLES, encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
        lista = dados["plataformas"] if isinstance(dados, dict) else dados
        saida = {p["id"]: {"nome": p.get("nome", p["id"]), "pasta": p.get("pasta", p["id"])} for p in lista}
    except (OSError, ValueError, KeyError, TypeError):
        saida = {}
    with _trava:
        _cache["consoles"] = saida
    return saida


def destino(jogo, pasta_livres=None):
    """Onde o jogo fica instalado: jogos\\livres\\<pasta do console>\\<arquivo>."""
    pasta = consoles().get(jogo["console"], {}).get("pasta", jogo["console"])
    return os.path.join(pasta_livres or PASTA_LIVRES, pasta, jogo["arquivo"])


def jogos(pasta_livres=None):
    """Os jogos da lista, para a tela: cada um com o nome do console e se ja
    esta instalado."""
    nomes = consoles()
    saida = []
    for jogo in lista_curada().get("jogos", []):
        item = {chave: jogo.get(chave, "") for chave in ("id", "titulo", "console", "autor", "ano", "licenca",
                                                          "descricao", "pagina", "aceite")}
        item["tamanho"] = jogo.get("tamanho", 0)
        item["console_nome"] = nomes.get(jogo["console"], {}).get("nome", jogo["console"])
        item["instalado"] = os.path.isfile(destino(jogo, pasta_livres))
        saida.append(item)
    return saida


def _marca(caminho):
    resumo = hashlib.sha256()
    with open(caminho, "rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1 << 20), b""):
            resumo.update(bloco)
    return resumo.hexdigest()


def instalar(ident, aceite=False, pasta_livres=None):
    """Baixa o jogo do site de quem publicou, confere o tamanho e a marca e
    poe na pasta do console. Devolve {"titulo", "arquivo", "console",
    "ja_tinha"}. ValueError com a frase para a tela; FalhaDeRede se a rede
    falhou ou pediu login."""
    jogo = next((j for j in lista_curada().get("jogos", []) if j.get("id") == ident), None)
    if not jogo:
        raise ValueError("Este jogo não está na biblioteca livre do ARENA: feche e abra a Biblioteca de novo "
                         "para ver a lista de agora.")
    if jogo.get("aceite") and not aceite:
        raise ValueError("Para baixar este jogo, marque a caixinha: " + jogo["aceite"])
    final = destino(jogo, pasta_livres)
    resposta = {"titulo": jogo["titulo"], "arquivo": os.path.relpath(final, RAIZ), "console": jogo["console"]}
    if os.path.isfile(final):
        return dict(resposta, ja_tinha=True)
    os.makedirs(os.path.dirname(final), exist_ok=True)
    temporario = "%s.%d.baixando" % (final, threading.get_ident())
    try:
        try:
            codigo, _nada = baixar.rodar(jogo["baixar"], SEGUNDOS, destino=temporario)
        except OSError:
            raise FalhaDeRede(MENSAGEM_REDE)
        if codigo != 0 or not os.path.isfile(temporario):
            raise FalhaDeRede(MENSAGEM_REDE)
        with open(temporario, "rb") as arquivo:
            comeco = arquivo.read(512)
        if parece_pagina_de_login(comeco):
            raise FalhaDeRede(MENSAGEM_PORTAL)
        if os.path.getsize(temporario) != jogo["tamanho"] or _marca(temporario) != jogo["sha256"]:
            raise ValueError("O arquivo que chegou não é o esperado (a marca não bate), então nada foi "
                             "instalado. O site de quem publicou pode ter trocado o jogo: peça ao professor "
                             "para conferir a lista.")
        os.replace(temporario, final)
    finally:
        if os.path.exists(temporario):
            try:
                os.remove(temporario)
            except OSError:
                pass
    return dict(resposta, ja_tinha=False)
