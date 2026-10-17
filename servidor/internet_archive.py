# -*- coding: utf-8 -*-
"""Catalogo de jogos livres do Internet Archive.

So busca em colecoes de shareware/freeware/dominio publico - programas
que a propria colecao ja garante que podem ser distribuidos de graca.
"Mediatype:software" sozinho pega qualquer coisa, jogo comercial
incluido; isso e' risco legal real pra um projeto de escola. Uma versao
anterior deste arquivo removeu esse filtro (ver historico do git) - foi
revertido.

A busca em si e' ampla dentro dessas colecoes: titulo, descricao,
varias colecoes ao mesmo tempo. "Aberto" e' o alcance da busca, nao a
seguranca legal.
"""

import hashlib
import json
import os
import re
import urllib.parse
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import baixar


RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_LIVRES = os.path.join(RAIZ, "jogos", "livres")
HOST = "archive.org"
# O endereco de onde tudo vem (os testes de internet ruim apontam para um
# servidor falso aqui: testes\teste_internet_ruim.py).
BASE = "https://archive.org"

# Internet ruim (auditoria 3, Fase 3). Antes, a busca devolvia "nenhum
# resultado" quando, na verdade, a rede tinha falhado -- ou quando a rede da
# escola devolvia a PAGINA DE LOGIN do Wi-Fi no lugar dos dados -- e pedia
# as fichas dos jogos uma de cada vez, ate 30 pedidos de ate 20 s (numa
# rede lenta, minutos com a tela esperando).
MENSAGEM_REDE = ("Não consegui falar com o Internet Archive agora (a internet caiu ou está muito "
                 "lenta). Confira a internet e tente de novo daqui a pouco.")
MENSAGEM_PORTAL = ("A rede pediu login: chegou a página do Wi-Fi no lugar da resposta do Internet "
                   "Archive. Abra o navegador, entre na rede e tente de novo.")
SEGUNDOS_BUSCA = 20          # o pedido da busca
SEGUNDOS_FICHA = 10          # cada ficha de jogo (pedidas ao mesmo tempo)
FICHAS_AO_MESMO_TEMPO = 10


class FalhaDeRede(ValueError):
    """A rede falhou (nao e' "nao achei"). A mensagem diz o que fazer."""


def parece_pagina_de_login(bruto):
    """O comeco da resposta e' uma pagina HTML (o login do Wi-Fi da escola)
    no lugar dos dados esperados?"""
    comeco = bytes(bruto[:512]).lstrip().lower()
    return comeco.startswith((b"<!doctype", b"<html", b"<head", b"<meta", b"<script"))

# Colecoes do Internet Archive com curadoria editorial de verdade e
# licenca de distribuicao livre conhecida - nao e' so o nome da colecao
# dizer "livre"/"homebrew"/"dominio publico": a maioria dos itens com
# esse rotulo no Internet Archive sao envios de usuario sem checagem
# nenhuma, muitas vezes ROM comercial rotulada errado (Nintendo nao vira
# dominio publico por alguem marcar assim). So entra aqui colecao da
# propria curadoria "Software Library" do Internet Archive, confirmada
# uma por uma - por isso comeca curta. Nunca "mediatype:software"
# sozinho, que pega qualquer coisa.
#
# Cada colecao diz o console dos jogos dela e a PASTA onde o jogo baixado
# fica. Achado de 02/10/2026: tudo ia para jogos\livres\Internet Archive,
# e la um .zip de DOS virava "Precisa escolher o console" -- o indexador
# decide o console pela pasta ("a pasta manda"), e a pasta nao dizia nada.
COLECOES_LIVRES = {
    "softwarelibrary_msdos_shareware": {"plataforma": "dos", "nome": "MS-DOS", "pasta": "MS-DOS"},
}

LIMITE = 4 * 1024 * 1024 * 1024
EXTENSOES = (".zip", ".7z", ".lha", ".gz", ".exe", ".com", ".dsk", ".img", ".iso")


def _ler(url, segundos=None):
    """O JSON de 'url', ou FalhaDeRede com a frase certa (rede ou login)."""
    segundos = segundos or SEGUNDOS_BUSCA
    try:
        codigo, dados = baixar.rodar(url, segundos)
    except OSError:
        raise FalhaDeRede(MENSAGEM_REDE)
    if codigo != 0:
        raise FalhaDeRede(MENSAGEM_REDE)
    if parece_pagina_de_login(dados):
        raise FalhaDeRede(MENSAGEM_PORTAL)
    try:
        return json.loads(dados.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        raise FalhaDeRede(MENSAGEM_REDE)


def _texto(valor):
    if isinstance(valor, list):
        return " ".join(str(parte) for parte in valor)
    return str(valor or "")


def _colecao_permitida(meta):
    """A colecao livre a que o item pertence (o nome dela), ou None. A
    mesma checagem vale na busca (query) e de novo aqui, na hora de
    instalar, pra ninguem baixar um item que so apareceu buscando errado."""
    colecoes = meta.get("metadata", {}).get("collection", [])
    if isinstance(colecoes, str):
        colecoes = [colecoes]
    return next((c for c in colecoes if c in COLECOES_LIVRES), None)


def consoles_da_biblioteca():
    """Os consoles que a busca online cobre hoje (para a tela dizer)."""
    vistos = []
    for info in COLECOES_LIVRES.values():
        if info["nome"] not in vistos:
            vistos.append(info["nome"])
    return vistos


def palavras_da_busca(consulta):
    """As palavras que o titulo do jogo precisa ter (no maximo 6), em
    minusculas: "OR", "AND" e "NOT" so viram comando da busca do Internet
    Archive em maiusculas -- assim nada que o aluno digita vira comando."""
    return [p.lower() for p in re.findall(r"\w+", str(consulta or ""), flags=re.UNICODE)[:6]]


def consulta_do_archive(palavras, colecoes):
    """O texto de busca do Internet Archive: so dentro das colecoes livres e
    so no TITULO, com TODAS as palavras. Achado de 02/10/2026 (Rafael
    procurou "Mario"): a busca tambem olhava a descricao, e voltava jogo de
    DOS que so citava o Mario no texto -- "um monte de coisa aleatoria"."""
    filtro_colecoes = " OR ".join("collection:%s" % c for c in colecoes)
    return "(%s) AND title:(%s)" % (filtro_colecoes, " AND ".join(palavras))


def _arquivo(meta):
    candidatos = []
    for arquivo in meta.get("files", []):
        nome = str(arquivo.get("name", ""))
        if nome.lower().endswith(EXTENSOES) and not nome.startswith("__"):
            try:
                tamanho = int(arquivo.get("size", 0) or 0)
            except (TypeError, ValueError):
                tamanho = 0
            if 0 < tamanho <= LIMITE:
                candidatos.append((nome, arquivo, tamanho))
    # .zip primeiro - mais facil de identificar o console pela extensao
    # de dentro, e menor que um .iso solto na maioria dos casos.
    candidatos.sort(key=lambda item: (0 if item[0].lower().endswith(".zip") else 1, item[0].lower()))
    return candidatos[0] if candidatos else None


def buscar(consulta):
    consulta = str(consulta or "").strip()
    if len(consulta) < 2:
        return []
    palavras = palavras_da_busca(consulta[:80])
    if not palavras:
        return []

    parametros = urllib.parse.urlencode([
        ("q", consulta_do_archive(palavras, COLECOES_LIVRES)),
        ("fl[]", "identifier"), ("fl[]", "title"), ("fl[]", "description"),
        ("fl[]", "creator"), ("fl[]", "collection"), ("rows", "30"), ("output", "json"),
    ])

    # Rede que falha ou pagina de login do Wi-Fi: FalhaDeRede, com a frase
    # para a tela (antes virava "nenhum resultado").
    dados = _ler(BASE + "/advancedsearch.php?" + parametros)
    documentos = [d for d in ((dados.get("response") or {}).get("docs") or []) if isinstance(d, dict)]
    documentos = [d for d in documentos if re.fullmatch(r"[A-Za-z0-9_-]{3,100}", str(d.get("identifier", "")))]

    def ficha(documento):
        try:
            return _ler(BASE + "/metadata/" + urllib.parse.quote(str(documento["identifier"])),
                        SEGUNDOS_FICHA)
        except FalhaDeRede as falha:
            return falha

    # As fichas ao mesmo tempo (antes, uma de cada vez): numa rede lenta, a
    # busca inteira leva o tempo de umas poucas fichas, nao de 30.
    with ThreadPoolExecutor(max_workers=FICHAS_AO_MESMO_TEMPO) as grupo:
        fichas = list(grupo.map(ficha, documentos))
    if documentos and all(isinstance(f, FalhaDeRede) for f in fichas):
        raise fichas[0]          # a rede caiu no meio: diz isso, nao "nenhum resultado"

    resultado = []
    for documento, meta in zip(documentos, fichas):
        identificador = str(documento.get("identifier", ""))
        if isinstance(meta, FalhaDeRede) or not isinstance(meta, dict):
            continue
        # Ficha torta (vinda da rede) nao derruba a busca: o item fica de fora.
        try:
            colecao = _colecao_permitida(meta)
            arquivo = _arquivo(meta) if colecao else None
            if not arquivo:
                continue
            metadados = meta.get("metadata") or {}
            titulo = _texto(metadados.get("title") or documento.get("title"))[:160]
            criador = _texto(metadados.get("creator") or documento.get("creator"))[:120]
            descricao = _texto(metadados.get("description"))[:300]
        except (AttributeError, TypeError, ValueError):
            continue
        # Confere aqui tambem: toda palavra pedida precisa estar no titulo.
        if not all(palavra.casefold() in titulo.casefold() for palavra in palavras):
            continue
        info = COLECOES_LIVRES[colecao]
        resultado.append({
            "id": identificador,
            "titulo": titulo,
            "plataforma": info["plataforma"],
            "plataforma_nome": info["nome"],
            "criador": criador,
            "descricao": descricao,
            "arquivo": arquivo[0],
            "tamanho": arquivo[2],
            "fonte": "Internet Archive",
        })
    return resultado


def instalar(identificador, nome_arquivo, plataforma=""):
    if not re.fullmatch(r"[A-Za-z0-9_-]{3,100}", str(identificador or "")):
        raise ValueError("Esse item do Internet Archive não serve. Faça a busca de novo e escolha da lista.")

    # Achado real na auditoria: uma falha de rede (sem internet, DNS fora) ou
    # uma pagina de login de Wi-Fi de escola no lugar do JSON esperado vazava
    # como OSError/erro de JSON cru. Agora _ler devolve FalhaDeRede com a
    # frase certa (rede ou login), e ela chega a tela como esta.
    meta = _ler(BASE + "/metadata/" + urllib.parse.quote(identificador))

    try:
        colecao = _colecao_permitida(meta)
    except (AttributeError, TypeError):
        colecao = None
    if not colecao:
        raise ValueError("Esse item não está numa coleção de jogos liberados pelos autores, e o ARENA só baixa esses. Escolha outro da lista.")
    info = COLECOES_LIVRES[colecao]

    arquivo = next((item for item in (meta.get("files") or [])
                    if isinstance(item, dict) and str(item.get("name", "")) == str(nome_arquivo)), None)
    if not arquivo or not str(nome_arquivo).lower().endswith(EXTENSOES):
        raise ValueError("O arquivo do jogo não está mais nesse item do Internet Archive. Escolha outro da lista.")

    try:
        tamanho_meta = int(arquivo.get("size", 0) or 0)
    except (TypeError, ValueError):
        tamanho_meta = 0

    if not tamanho_meta or tamanho_meta > LIMITE:
        raise ValueError("O arquivo passa de 4 GB, o limite do ARENA. Escolha outro jogo.")

    nome_seguro = re.sub(r"[^A-Za-z0-9._()\- ]", "_", os.path.basename(str(nome_arquivo)))
    # Na pasta do console da colecao (jogos\livres\MS-DOS): e' a pasta que
    # diz o console. O 'plataforma' que vem da tela nao manda aqui.
    destino = os.path.abspath(os.path.join(PASTA_LIVRES, info["pasta"], nome_seguro))
    livres = os.path.abspath(PASTA_LIVRES)

    if os.path.commonpath([destino, livres]) != livres:
        raise ValueError("Nome de arquivo estranho: o ARENA não baixou. Escolha outro jogo.")

    os.makedirs(os.path.dirname(destino), exist_ok=True)
    temporario = destino + ".download"
    digest = hashlib.sha1()
    tamanho = 0
    url = BASE + "/download/%s/%s" % (
        urllib.parse.quote(str(identificador)), urllib.parse.quote(str(nome_arquivo), safe="/"))
    # O Internet Archive nao declara SHA-256 por arquivo, so md5/sha1/crc32
    # -- confirmado na propria API (/metadata devolve isto pra cada item de
    # "files"). sha1 e' o mais forte dos tres que eles tem. Sem isto, um
    # download incompleto (queda de rede no meio) ou adulterado no caminho
    # virava jogo instalado sem ninguem perceber.
    sha1_esperado = str(arquivo.get("sha1") or "").lower()

    try:
        # Achado real na auditoria: sem tratar o erro do curl aqui, uma
        # queda de rede NO MEIO DO DOWNLOAD (diferente da busca de
        # metadados, ja tratada acima) vazava como CalledProcessError cru.
        try:
            codigo, _nada = baixar.rodar(url, 120, destino=temporario)
        except OSError:
            codigo = -1
        if codigo != 0:
            raise FalhaDeRede(
                "O download caiu no meio do caminho. Confira a internet e "
                "tente de novo.")

        comeco = b""
        with open(temporario, "rb") as entrada:
            while True:
                bloco = entrada.read(1024 * 1024)
                if not bloco:
                    break
                if not comeco:
                    comeco = bloco[:512]
                tamanho += len(bloco)
                if tamanho > LIMITE:
                    raise ValueError("O arquivo passa de 4 GB, o limite do ARENA. Escolha outro jogo.")
                digest.update(bloco)

        # A pagina de login do Wi-Fi chega com "200 OK" e o curl acha que deu
        # certo: no lugar do jogo, um HTML.
        if parece_pagina_de_login(comeco):
            raise FalhaDeRede(MENSAGEM_PORTAL)
        if sha1_esperado and digest.hexdigest() != sha1_esperado:
            raise ValueError(
                "O arquivo baixado não confere com o esperado (SHA-1 diferente) e foi recusado, "
                "por segurança. Ele pode ter chegado cortado: tente de novo.")

        os.replace(temporario, destino)
    finally:
        if os.path.exists(temporario):
            try:
                os.remove(temporario)
            except OSError:
                pass

    return {"titulo": meta.get("metadata", {}).get("title", identificador), "tamanho": tamanho,
            "plataforma_nome": info["nome"]}
