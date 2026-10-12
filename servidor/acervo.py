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
        # So os itens que sao objeto: um [1, "x"] no arquivo nao derruba a aba.
        return [i for i in dados if isinstance(i, dict)] if isinstance(dados, list) else []
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
        raise ValueError("Preencha o campo %s." % nome)
    if len(texto) > limite:
        raise ValueError("%s ficou longo demais: encurte e tente de novo." % nome)
    return texto


def _validar_item(item):
    if not isinstance(item, dict):
        raise ValueError("O cadastro do jogo veio torto. Preencha o formulário de novo.")
    id_item = _texto(item.get("id"), 64, "Identificador", True)
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]*", id_item):
        raise ValueError("O identificador só pode ter letras, números, hífen e sublinhado: troque os outros sinais e tente de novo.")
    # O tamanho e declarado por quem cadastra, e o download confere na
    # hora. Mas vale barrar o absurdo aqui: um item de 99 GB entupiria o
    # pen drive antes de alguem perceber.
    tamanho = item.get("tamanho")
    if tamanho is not None:
        try:
            tamanho = int(tamanho)
        except (TypeError, ValueError):
            raise ValueError("Escreva o tamanho em bytes, só com números.")
        if tamanho < 0 or tamanho > TAMANHO_MAXIMO:
            raise ValueError("Escreva um tamanho entre 0 e %d GB (em bytes)."
                             % (TAMANHO_MAXIMO // (1024 ** 3)))

    titulo = _texto(item.get("titulo"), 120, "Título", True)
    plataforma = _texto(item.get("plataforma"), 80, "Plataforma", True)
    descricao = _texto(item.get("descricao"), 400, "Descrição")
    licenca = _texto(item.get("licenca"), 160, "Licença/autorização", True)
    fonte = _texto(item.get("fonte"), 240, "Fonte", True)
    fonte_nome = _texto(item.get("fonte_nome"), 120, "Nome da fonte") or "Fonte autorizada"
    url = _texto(item.get("url"), 500, "URL", True)
    partes = urllib.parse.urlparse(url)
    if partes.scheme != "https" or partes.hostname not in HOSTS_PERMITIDOS:
        raise ValueError("Use um endereço https:// do archive.org ou do raw.githubusercontent.com (são as fontes que o ARENA aceita).")
    sha256 = _texto(item.get("sha256"), 64, "SHA-256", True).lower()
    if not re.fullmatch(r"[0-9a-f]{64}", sha256):
        raise ValueError("Confira o SHA-256: são 64 letras e números (de 0 a 9 e de a a f).")
    destino = _texto(item.get("destino"), 240, "Arquivo de destino", True).replace("/", os.sep)
    caminho = os.path.abspath(os.path.join(RAIZ, destino))
    livres = os.path.abspath(PASTA_LIVRES)
    if os.path.commonpath([caminho, livres]) != livres or os.path.basename(caminho) in ("", ".", ".."):
        raise ValueError("Escolha um destino dentro de jogos\\livres.")
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
        "tamanho": tamanho,
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
        raise ValueError("Esse jogo não está mais na lista do acervo. Clique em Atualizar lista e escolha de novo.")
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
        raise ValueError("Esse jogo não está mais na lista do acervo. Clique em Atualizar lista e escolha de novo.")
    if not item.get("autorizado") or not item.get("licenca"):
        raise ValueError("Esse jogo não diz qual é a licença dele. Peça ao professor para completar o cadastro.")

    url = str(item.get("url", ""))
    partes = urllib.parse.urlparse(url)
    if partes.scheme != "https" or partes.hostname not in HOSTS_PERMITIDOS:
        raise ValueError("O endereço desse jogo não é de uma fonte que o ARENA aceita. Peça ao professor para conferir o cadastro.")

    sha256 = str(item.get("sha256", "")).lower()
    if not re.fullmatch(r"[0-9a-f]{64}", sha256):
        raise ValueError("Esse jogo está sem o código de conferência (SHA-256). Peça ao professor para completar o cadastro.")

    destino_relativo = str(item.get("destino", ""))
    destino = os.path.abspath(os.path.join(RAIZ, destino_relativo))
    livres = os.path.abspath(PASTA_LIVRES)
    if os.path.commonpath([destino, livres]) != livres:
        raise ValueError("Escolha um destino dentro de jogos\\livres.")
    os.makedirs(os.path.dirname(destino), exist_ok=True)

    temporario = destino + ".download"
    tamanho = 0
    digest = hashlib.sha256()
    comeco = b""
    try:
        requisicao = urllib.request.Request(url, headers={"User-Agent": "ARENA/1.0"})
        with urllib.request.urlopen(requisicao, timeout=30) as resposta:
            with open(temporario, "wb") as arquivo:
                while True:
                    bloco = resposta.read(1024 * 1024)
                    if not bloco:
                        break
                    if not comeco:
                        comeco = bloco[:512]
                    tamanho += len(bloco)
                    if tamanho > TAMANHO_MAXIMO:
                        raise ValueError("O arquivo passa de 4 GB, o limite do ARENA. Escolha outro jogo.")
                    digest.update(bloco)
                    arquivo.write(bloco)
        # A pagina de login do Wi-Fi da escola chega com "200 OK" no lugar do
        # jogo (auditoria 3, Fase 3): o SHA-256 ja recusaria, mas a frase
        # certa diz o que fazer.
        if digest.hexdigest() != sha256 and comeco.lstrip().lower().startswith(
                (b"<!doctype", b"<html", b"<head", b"<meta", b"<script")):
            raise ValueError("A rede pediu login: chegou a página do Wi-Fi no lugar do jogo. Abra o "
                             "navegador, entre na rede e tente de novo.")
        if digest.hexdigest() != sha256:
            raise ValueError("O arquivo baixado não confere com o cadastro (SHA-256 diferente) e foi recusado. Ele pode ter chegado cortado: tente de novo. Se repetir, peça ao professor para conferir o cadastro.")
        os.replace(temporario, destino)
    finally:
        if os.path.exists(temporario):
            try:
                os.remove(temporario)
            except OSError:
                pass

    return {"titulo": item.get("titulo", "jogo"), "tamanho": tamanho}
