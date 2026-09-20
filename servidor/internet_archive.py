# -*- coding: utf-8 -*-
"""Catalogo de software do Internet Archive (Busca Geral).

Removida a restrição de coleções de shareware e validação de licenças.
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
# Removido o filtro de coleção específica para permitir busca geral
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
    # Ordenação prioritária para arquivos compactados
    candidatos.sort(key=lambda item: (0 if item[0].lower().endswith(".zip") else 1, item[0].lower()))
    return candidatos[0] if candidatos else None


def buscar(consulta):
    consulta = str(consulta or "").strip()
    if len(consulta) < 2:
        return []
    termo = re.sub(r'[^\w .+\-]', " ", consulta, flags=re.UNICODE).strip()[:80]
    if not termo:
        return []
    
    # Alterado os parâmetros de busca para remover o filtro 'collection:softwarelibrary_msdos_shareware'
    # Agora ele busca por mediatype:software e o termo nos títulos/descrições
    parametros = urllib.parse.urlencode([
        ("q", f'mediatype:software AND (title:"{termo}" OR description:"{termo}")'),
        ("fl[]", "identifier"), ("fl[]", "title"), ("fl[]", "description"),
        ("fl[]", "creator"), ("rows", "20"), ("output", "json"),
    ])
    
    dados = _ler("https://archive.org/advancedsearch.php?" + parametros)
    resultado = []
    for documento in dados.get("response", {}).get("docs", []):
        identificador = str(documento.get("identifier", ""))
        if not re.fullmatch(r"[A-Za-z0-9_-]{3,100}", identificador):
            continue
        try:
            meta = _ler("https://archive.org/metadata/" + urllib.parse.quote(identificador))
            arquivo = _arquivo(meta)
            # Removida a chamada da função _autorizado
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
    
    meta = _ler("https://archive.org/metadata/" + urllib.parse.quote(identificador))
    
    # Removida a validação de licença aqui também
    
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
    digest = hashlib.sha256()
    tamanho = 0
    url = "https://archive.org/download/%s/%s" % (
        urllib.parse.quote(str(identificador)), urllib.parse.quote(str(nome_arquivo), safe="/"))
    
    try:
        subprocess.run(
            ["curl.exe", "--fail", "--silent", "--show-error", "--location",
             "--max-time", "120", "-A", "ARENA/1.0", "-o", temporario, url],
            check=True)
        with open(temporario, "rb") as entrada:
            while True:
                bloco = entrada.read(1024 * 1024)
                if not bloco:
                    break
                tamanho += len(bloco)
                if tamanho > LIMITE:
                    raise ValueError("Arquivo grande demais para o Arena.")
                digest.update(bloco)
                
        os.replace(temporario, destino)
    finally:
        if os.path.exists(temporario):
            try:
                os.remove(temporario)
            except OSError:
                pass
                
    return {"titulo": meta.get("metadata", {}).get("title", identificador), "tamanho": tamanho}
