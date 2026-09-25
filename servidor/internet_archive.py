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
import subprocess
import urllib.parse
import urllib.error
import urllib.request


RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_LIVRES = os.path.join(RAIZ, "jogos", "livres")
HOST = "archive.org"

# Colecoes do Internet Archive com curadoria editorial de verdade e
# licenca de distribuicao livre conhecida - nao e' so o nome da colecao
# dizer "livre"/"homebrew"/"dominio publico": a maioria dos itens com
# esse rotulo no Internet Archive sao envios de usuario sem checagem
# nenhuma, muitas vezes ROM comercial rotulada errado (Nintendo nao vira
# dominio publico por alguem marcar assim). So entra aqui colecao da
# propria curadoria "Software Library" do Internet Archive, confirmada
# uma por uma - por isso comeca curta. Nunca "mediatype:software"
# sozinho, que pega qualquer coisa.
COLECOES_LIVRES = (
    "softwarelibrary_msdos_shareware",
)

LIMITE = 4 * 1024 * 1024 * 1024
EXTENSOES = (".zip", ".7z", ".lha", ".gz", ".exe", ".com", ".dsk", ".img", ".iso")


def _ler(url):
    resultado = subprocess.run(
        ["curl.exe", "--fail", "--silent", "--show-error", "--location",
         "--max-time", "20", "-A", "ARENA/1.0", url],
        capture_output=True, check=True)
    return json.loads(resultado.stdout.decode("utf-8"))


def _texto(valor):
    if isinstance(valor, list):
        return " ".join(str(parte) for parte in valor)
    return str(valor or "")


def _colecao_permitida(meta):
    """Confere se o item pertence a uma das colecoes livres - a mesma
    checagem vale na busca (query) e de novo aqui, na hora de instalar,
    pra ninguem baixar um item que so apareceu buscando errado."""
    colecoes = meta.get("metadata", {}).get("collection", [])
    if isinstance(colecoes, str):
        colecoes = [colecoes]
    return any(c in COLECOES_LIVRES for c in colecoes)


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
    termo = re.sub(r'[^\w .+\-]', " ", consulta, flags=re.UNICODE).strip()[:80]
    if not termo:
        return []

    filtro_colecoes = " OR ".join("collection:%s" % c for c in COLECOES_LIVRES)
    parametros = urllib.parse.urlencode([
        ("q", '(%s) AND (title:"%s" OR description:"%s")' % (filtro_colecoes, termo, termo)),
        ("fl[]", "identifier"), ("fl[]", "title"), ("fl[]", "description"),
        ("fl[]", "creator"), ("fl[]", "collection"), ("rows", "30"), ("output", "json"),
    ])

    try:
        dados = _ler("https://archive.org/advancedsearch.php?" + parametros)
    except (OSError, ValueError, urllib.error.URLError, subprocess.SubprocessError):
        return []

    resultado = []
    for documento in dados.get("response", {}).get("docs", []):
        identificador = str(documento.get("identifier", ""))
        if not re.fullmatch(r"[A-Za-z0-9_-]{3,100}", identificador):
            continue
        try:
            meta = _ler("https://archive.org/metadata/" + urllib.parse.quote(identificador))
            if not _colecao_permitida(meta):
                continue
            arquivo = _arquivo(meta)
            if not arquivo:
                continue
        except (OSError, ValueError, urllib.error.URLError, subprocess.SubprocessError):
            continue

        resultado.append({
            "id": identificador,
            "titulo": _texto(meta.get("metadata", {}).get("title") or documento.get("title"))[:160],
            "criador": _texto(meta.get("metadata", {}).get("creator") or documento.get("creator"))[:120],
            "descricao": _texto(meta.get("metadata", {}).get("description"))[:300],
            "arquivo": arquivo[0],
            "tamanho": arquivo[2],
            "fonte": "Internet Archive",
        })
    return resultado


def instalar(identificador, nome_arquivo, plataforma=""):
    if not re.fullmatch(r"[A-Za-z0-9_-]{3,100}", str(identificador or "")):
        raise ValueError("Item do Internet Archive inválido.")

    # Achado real na auditoria: sem este try/except, uma falha de rede (sem
    # internet, DNS fora) ou uma pagina de login de Wi-Fi de escola no
    # lugar do JSON esperado vazava como OSError/erro de JSON cru --
    # buscar() ja tinha essa protecao, instalar() nao tinha.
    try:
        meta = _ler("https://archive.org/metadata/" + urllib.parse.quote(identificador))
    except (OSError, ValueError, urllib.error.URLError, subprocess.SubprocessError):
        raise ValueError(
            "Não consegui falar com o Internet Archive agora. Confira a "
            "internet e tente de novo.")

    if not _colecao_permitida(meta):
        raise ValueError("Este item não está numa coleção de distribuição livre.")

    arquivo = next((item for item in meta.get("files", [])
                    if str(item.get("name", "")) == str(nome_arquivo)), None)
    if not arquivo or not str(nome_arquivo).lower().endswith(EXTENSOES):
        raise ValueError("Arquivo não encontrado no item.")

    try:
        tamanho_meta = int(arquivo.get("size", 0) or 0)
    except (TypeError, ValueError):
        tamanho_meta = 0

    if not tamanho_meta or tamanho_meta > LIMITE:
        raise ValueError("Arquivo grande demais para o Arena.")

    nome_seguro = re.sub(r"[^A-Za-z0-9._()\- ]", "_", os.path.basename(str(nome_arquivo)))
    destino = os.path.abspath(os.path.join(PASTA_LIVRES, "Internet Archive", nome_seguro))
    livres = os.path.abspath(PASTA_LIVRES)

    if os.path.commonpath([destino, livres]) != livres:
        raise ValueError("Destino inválido.")

    os.makedirs(os.path.dirname(destino), exist_ok=True)
    temporario = destino + ".download"
    digest = hashlib.sha1()
    tamanho = 0
    url = "https://archive.org/download/%s/%s" % (
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
            subprocess.run(
                ["curl.exe", "--fail", "--silent", "--show-error", "--location",
                 "--max-time", "120", "-A", "ARENA/1.0", "-o", temporario, url],
                check=True)
        except (OSError, subprocess.SubprocessError):
            raise ValueError(
                "O download caiu no meio do caminho. Confira a internet e "
                "tente de novo.")

        with open(temporario, "rb") as entrada:
            while True:
                bloco = entrada.read(1024 * 1024)
                if not bloco:
                    break
                tamanho += len(bloco)
                if tamanho > LIMITE:
                    raise ValueError("Arquivo grande demais para o Arena.")
                digest.update(bloco)

        if sha1_esperado and digest.hexdigest() != sha1_esperado:
            raise ValueError(
                "O arquivo baixado não bate com o esperado (SHA-1 "
                "diferente). Download recusado por segurança.")

        os.replace(temporario, destino)
    finally:
        if os.path.exists(temporario):
            try:
                os.remove(temporario)
            except OSError:
                pass

    return {"titulo": meta.get("metadata", {}).get("title", identificador), "tamanho": tamanho}
