# -*- coding: utf-8 -*-
r"""
ARENA - zip de fliperama danificado.

Por que existe (tarefa 7 do Rafael, "Metal Slug X com cores erradas",
achado em 02/10/2026): o mslugx.zip da pasta tinha uma parte danificada --
MSX_C3.rom, grafico dos personagens -- que nao confere com a assinatura
(CRC) que o proprio zip guarda dela. O FBNeo acha as partes pela lista do
zip e carrega a estragada: o jogo abre com personagens de cor estranha. O
MAME recusa ("NOT FOUND"). Nada na tela dizia o motivo.

Conferir um zip e' descompactar tudo (~0,3 s por 50 MB no Ryzen; mais num
Celeron). Por isso cada zip e' conferido UMA vez e o resultado fica em
dados\zips_conferidos.json, pelo tamanho e pela data do arquivo: copiou de
novo, confere de novo. Nada do jogo e' alterado -- so lido.
"""

import json
import os
import threading
import zipfile
import zlib

PASTA_SERVIDOR = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(PASTA_SERVIDOR)
ARQUIVO = os.path.join(RAIZ, "dados", "zips_conferidos.json")
LIMITE_DE_ENTRADAS = 20000      # colecao de fliperama gigante nao enche o arquivo sem fim

_trava = threading.Lock()
_memoria = {"arquivo": None, "marca": None, "dados": {}}   # a lista le muitas vezes seguidas


def _ler():
    """O que ja foi conferido. Em memoria: a lista de jogos pergunta uma vez
    por zip de fliperama, e reler o arquivo a cada um pesa numa colecao
    grande. Rele so se o arquivo mudou."""
    try:
        estado = os.stat(ARQUIVO)
        marca = (estado.st_size, estado.st_mtime_ns)
    except OSError:
        return {}
    if _memoria["arquivo"] == ARQUIVO and _memoria["marca"] == marca:
        return _memoria["dados"]
    try:
        with open(ARQUIVO, encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except (OSError, ValueError):
        return {}
    dados = dados if isinstance(dados, dict) else {}
    _memoria.update(arquivo=ARQUIVO, marca=marca, dados=dados)
    return dados


def _gravar(dados):
    os.makedirs(os.path.dirname(ARQUIVO), exist_ok=True)
    provisorio = "%s.%d.%d.tmp" % (ARQUIVO, os.getpid(), threading.get_ident())
    with open(provisorio, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, separators=(",", ":"))
    os.replace(provisorio, ARQUIVO)
    _memoria["marca"] = None             # a proxima leitura pega o novo


def _chave(caminho):
    return os.path.relpath(caminho, RAIZ).replace("\\", "/").lower()


def descompactar_tudo(caminho):
    """Nome da primeira parte que nao confere, "" se o zip esta inteiro.
    Compressao que o Python nao sabe abrir (deflate64, de alguns
    compactadores do Windows) nao conta como defeito: nao da para saber."""
    try:
        with zipfile.ZipFile(caminho) as pacote:
            for parte in pacote.infolist():
                if parte.is_dir():
                    continue
                try:
                    with pacote.open(parte) as dentro:
                        while dentro.read(1 << 20):
                            pass
                except NotImplementedError:
                    continue
                except (zipfile.BadZipFile, zlib.error, EOFError, OSError):
                    return parte.filename
    except (zipfile.BadZipFile, OSError):
        return "(o zip inteiro)"
    return ""


def parte_danificada(caminho, conferir=True):
    """A parte danificada do zip ("MSX_C3.rom"), "" se esta inteiro, ou None
    se nao da para dizer (nao e' .zip, sumiu, ou conferir=False e ainda nao
    foi conferido)."""
    if not str(caminho).lower().endswith(".zip"):
        return None
    try:
        estado = os.stat(caminho)
    except OSError:
        return None
    marca = [estado.st_size, int(estado.st_mtime)]
    chave = _chave(caminho)
    with _trava:
        salvo = _ler().get(chave)
    if isinstance(salvo, list) and len(salvo) == 3 and salvo[:2] == marca:
        return salvo[2]
    if not conferir:
        return None
    ruim = descompactar_tudo(caminho)
    with _trava:
        dados = _ler()
        if len(dados) >= LIMITE_DE_ENTRADAS:
            dados = {}
        dados[chave] = marca + [ruim]
        try:
            _gravar(dados)
        except OSError:
            pass          # pen drive cheio ou so leitura: so nao guarda
    return ruim


def texto_do_aviso(parte):
    """A frase para o aluno (cartao do jogo e "Abrindo...")."""
    return ("O arquivo deste jogo está danificado: a parte %s não confere. Ele pode abrir "
            "com gráficos errados (personagens com cor estranha) ou nem abrir. Copie o jogo "
            "de novo, de uma cópia boa." % parte)
