# -*- coding: utf-8 -*-
"""Instalacao de jogos de um manifesto autorizado pelo responsavel.

O Arena nao pesquisa nem escolhe ROMs na internet. Cada item precisa estar
num manifesto local, ter fonte HTTPS permitida, licenca/autorizacao declarada
e SHA-256 conhecido. Isso serve para homebrew, dominio publico e arquivos
proprios autorizados.
"""

import hashlib
import json
import os
import re
import urllib.parse
import urllib.request


RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQUIVO = os.path.join(RAIZ, "dados", "acervo_autorizado.json")
PASTA_LIVRES = os.path.join(RAIZ, "jogos", "livres")
HOSTS_PERMITIDOS = {"archive.org", "www.archive.org", "raw.githubusercontent.com"}
TAMANHO_MAXIMO = 4 * 1024 * 1024 * 1024


def ler_itens():
    try:
        with open(ARQUIVO, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
        return dados if isinstance(dados, list) else []
    except (OSError, ValueError):
        return []


def _salvar_itens(itens):
    os.makedirs(os.path.dirname(ARQUIVO), exist_ok=True)
    temporario = ARQUIVO + ".tmp"
    with open(temporario, "w", encoding="utf-8") as arquivo:
        json.dump(itens, arquivo, ensure_ascii=False, indent=2)
        arquivo.write("\n")
    os.replace(temporario, ARQUIVO)


def _texto(valor, limite, nome, obrigatorio=False):
    texto = str(valor or "").strip()
    if obrigatorio and not texto:
        raise ValueError("%s é obrigatório." % nome)
    if len(texto) > limite:
        raise ValueError("%s é muito longo." % nome)
    return texto


def _validar_item(item):
    if not isinstance(item, dict):
        raise ValueError("O item do acervo precisa ser um objeto.")
    id_item = _texto(item.get("id"), 64, "Identificador", True)
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]*", id_item):
        raise ValueError("O identificador só pode conter letras, números, hífen e sublinhado.")
    titulo = _texto(item.get("titulo"), 120, "Título", True)
    plataforma = _texto(item.get("plataforma"), 80, "Plataforma", True)
    descricao = _texto(item.get("descricao"), 400, "Descrição")
    licenca = _texto(item.get("licenca"), 160, "Licença/autorização", True)
    fonte = _texto(item.get("fonte"), 240, "Fonte", True)
    fonte_nome = _texto(item.get("fonte_nome"), 120, "Nome da fonte") or "Fonte autorizada"
    url = _texto(item.get("url"), 500, "URL", True)
    partes = urllib.parse.urlparse(url)
    if partes.scheme != "https" or partes.hostname not in HOSTS_PERMITIDOS:
        raise ValueError("A URL precisa ser HTTPS e estar em archive.org ou raw.githubusercontent.com.")
    sha256 = _texto(item.get("sha256"), 64, "SHA-256", True).lower()
    if not re.fullmatch(r"[0-9a-f]{64}", sha256):
        raise ValueError("O SHA-256 precisa ter 64 caracteres hexadecimais.")
    destino = _texto(item.get("destino"), 240, "Arquivo de destino", True).replace("/", os.sep)
    caminho = os.path.abspath(os.path.join(RAIZ, destino))
    livres = os.path.abspath(PASTA_LIVRES)
    if os.path.commonpath([caminho, livres]) != livres or os.path.basename(caminho) in ("", ".", ".."):
        raise ValueError("O destino precisa ficar dentro de jogos\\livres.")
    return {
        "id": id_item,
        "titulo": titulo,
        "plataforma": plataforma,
        "descricao": descricao,
        "licenca": licenca,
        "fonte": fonte,
        "fonte_nome": fonte_nome,
        "url": url,
        "sha256": sha256,
        "destino": destino,
        "autorizado": bool(item.get("autorizado")),
        "tamanho": item.get("tamanho"),
    }


def salvar(item):
    validado = _validar_item(item)
    itens = ler_itens()
    encontrado = False
    for indice, atual in enumerate(itens):
        if isinstance(atual, dict) and str(atual.get("id", "")) == validado["id"]:
            itens[indice] = validado
            encontrado = True
            break
    if not encontrado:
        itens.append(validado)
    _salvar_itens(itens)
    return validado


def remover(item_id):
    item_id = _texto(item_id, 64, "Identificador", True)
    itens = ler_itens()
    restantes = [item for item in itens
                 if not (isinstance(item, dict) and str(item.get("id", "")) == item_id)]
    if len(restantes) == len(itens):
        raise ValueError("Jogo autorizado não encontrado no manifesto.")
    _salvar_itens(restantes)
    return {"id": item_id}


def listar():
    itens = []
    for item in ler_itens():
        if not isinstance(item, dict):
            continue
        destino = str(item.get("destino", ""))
        caminho = os.path.abspath(os.path.join(RAIZ, destino))
        itens.append({
            "id": str(item.get("id", "")),
            "titulo": str(item.get("titulo", "")),
            "plataforma": str(item.get("plataforma", "")),
            "descricao": str(item.get("descricao", "")),
            "licenca": str(item.get("licenca", "")),
            "fonte": str(item.get("fonte", "")),
            "fonte_nome": str(item.get("fonte_nome", "Fonte autorizada")),
            "url": str(item.get("url", "")),
            "sha256": str(item.get("sha256", "")),
            "destino": str(item.get("destino", "")),
            "autorizado": bool(item.get("autorizado")),
            "tamanho": item.get("tamanho"),
            "instalado": caminho.startswith(os.path.abspath(PASTA_LIVRES))
                        and os.path.isfile(caminho),
        })
    return itens


def fontes():
    resultado = []
    vistos = set()
    for item in ler_itens():
        if not isinstance(item, dict):
            continue
        fonte = str(item.get("fonte", "")).strip()
        if not fonte or fonte in vistos:
            continue
        vistos.add(fonte)
        resultado.append({
            "nome": str(item.get("fonte_nome", "Fonte autorizada")),
            "url": fonte,
            "licenca": str(item.get("licenca", "")),
        })
    return resultado


def _item(item_id):
    return next((item for item in ler_itens()
                 if str(item.get("id", "")) == str(item_id)), None)


def instalar(item_id):
    item = _item(item_id)
    if not item:
        raise ValueError("Jogo autorizado nao encontrado no manifesto.")
    if not item.get("autorizado") or not item.get("licenca"):
        raise ValueError("O item nao declara autorizacao/licenca.")

    url = str(item.get("url", ""))
    partes = urllib.parse.urlparse(url)
    if partes.scheme != "https" or partes.hostname not in HOSTS_PERMITIDOS:
        raise ValueError("A fonte precisa ser HTTPS e estar numa origem permitida.")

    sha256 = str(item.get("sha256", "")).lower()
    if not re.fullmatch(r"[0-9a-f]{64}", sha256):
        raise ValueError("O item precisa ter SHA-256 valido antes do download.")

    destino_relativo = str(item.get("destino", ""))
    destino = os.path.abspath(os.path.join(RAIZ, destino_relativo))
    livres = os.path.abspath(PASTA_LIVRES)
    if os.path.commonpath([destino, livres]) != livres:
        raise ValueError("O destino precisa ficar dentro de jogos\\livres.")
    os.makedirs(os.path.dirname(destino), exist_ok=True)

    temporario = destino + ".download"
    tamanho = 0
    digest = hashlib.sha256()
    try:
        requisicao = urllib.request.Request(url, headers={"User-Agent": "ARENA/1.0"})
        with urllib.request.urlopen(requisicao, timeout=30) as resposta:
            with open(temporario, "wb") as arquivo:
                while True:
                    bloco = resposta.read(1024 * 1024)
                    if not bloco:
                        break
                    tamanho += len(bloco)
                    if tamanho > TAMANHO_MAXIMO:
                        raise ValueError("O arquivo excede o limite de 4 GB.")
                    digest.update(bloco)
                    arquivo.write(bloco)
        if digest.hexdigest() != sha256:
            raise ValueError("SHA-256 diferente: download recusado por seguranca.")
        os.replace(temporario, destino)
    finally:
        if os.path.exists(temporario):
            try:
                os.remove(temporario)
            except OSError:
                pass

    return {"titulo": item.get("titulo", "jogo"), "tamanho": tamanho}
