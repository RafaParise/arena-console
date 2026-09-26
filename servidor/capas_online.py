# -*- coding: utf-8 -*-
"""Busca a capa (box art) de um jogo no libretro-thumbnails - o mesmo
banco de miniaturas que o proprio RetroArch usa no "Atualizador Online
-> Miniaturas" do menu dele. E' curado pelo projeto libretro, gratis,
sem chave de API.

So funciona sob pedido (botao "Atualizar capa"), nunca sozinho - a regra
do ARENA e' nao depender de internet no meio da aula (ver comentario em
indexador.py). O aluno clica quando quiser tentar.
"""

import os
import re
import subprocess
import urllib.parse


RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_MINIATURAS = os.path.join(RAIZ, "retroarch", "thumbnails")

# So os sistemas conferidos de verdade (baixei uma capa real de cada e
# confirmei que chegou). Console que nao esta aqui nao tem essa opcao -
# PS2, PS3 e Xbox 360 nao tem cobertura boa nesse banco (nao sao nucleos
# nativos do RetroArch), entao ficam de fora em vez de fingir que tem.
REPO_POR_PLATAFORMA = {
    "nes": "Nintendo_-_Nintendo_Entertainment_System",
    "snes": "Nintendo_-_Super_Nintendo_Entertainment_System",
    "n64": "Nintendo_-_Nintendo_64",
    "gameboy": "Nintendo_-_Game_Boy",
    "gba": "Nintendo_-_Game_Boy_Advance",
    "nds": "Nintendo_-_Nintendo_DS",
    "gamecube": "Nintendo_-_GameCube",
    # Conferido 25/09/2026: Mario Kart Wii (USA) (En,Fr,Es).png -> 200, PNG.
    "wii": "Nintendo_-_Wii",
    "megadrive": "Sega_-_Mega_Drive_-_Genesis",
    "segacd": "Sega_-_Mega-CD_-_Sega_CD",
    "saturn": "Sega_-_Saturn",
    "dreamcast": "Sega_-_Dreamcast",
    "ps1": "Sony_-_PlayStation",
    "psp": "Sony_-_PlayStation_Portable",
    "neogeo": "SNK_-_Neo_Geo",
    "arcade": "MAME",
}


def _limpar_nome_arquivo(nome):
    """Mesma regra do libretro-thumbnails: troca caractere invalido por
    "_" no nome do arquivo."""
    return re.sub(r'[&*/:`<>?\\|"]', "_", nome)


_ASSINATURA_PNG = b"\x89PNG\r\n\x1a\n"


def _e_png_de_verdade(caminho):
    """Confere os primeiros bytes do arquivo, nao so o nome.

    curl com --fail devolve sucesso (codigo 0) para qualquer resposta
    HTTP 200 -- inclusive a pagina de login de um portal cativo de Wi-Fi,
    que chega como HTML disfarcado de "capa baixada com sucesso" se
    ninguem checar o conteudo de verdade. Achado real na auditoria,
    confirmado simulando um portal cativo local.
    """
    try:
        with open(caminho, "rb") as arquivo:
            return arquivo.read(len(_ASSINATURA_PNG)) == _ASSINATURA_PNG
    except OSError:
        return False


# O libretro-thumbnails nomeia pela regiao do jogo. Quando o nome do
# arquivo da ROM nao tem regiao nenhuma (ou tem uma que o banco nao tem
# exatamente essa revisao), tentar as tags mais comuns aumenta bastante
# a chance de achar sem precisar adivinhar o nome exato.
TAGS_REGIAO = ("(USA)", "(World)", "(Europe)", "(Japan)", "(USA, Europe)")


def buscar_e_baixar(plataforma_id, titulo_limpo, nome_base_arquivo):
    """Tenta achar a capa por varios nomes candidatos, do mais especifico
    (nome do ARQUIVO, com a tag de regiao de verdade) ao mais generico
    (titulo limpo + cada tag de regiao comum). Salva em
    retroarch/thumbnails/<plataforma>/Named_Boxarts/ com o TITULO LIMPO
    (e' o que indexador.capas_do_jogo ja procura).

    Devolve (ok, motivo).
    """
    repo = REPO_POR_PLATAFORMA.get(plataforma_id)
    if not repo:
        return False, "Este console ainda não tem esse banco de capas."

    candidatos = []
    if nome_base_arquivo and nome_base_arquivo != titulo_limpo:
        candidatos.append(nome_base_arquivo)
    candidatos.append(titulo_limpo)
    if "(" not in titulo_limpo:
        for tag in TAGS_REGIAO:
            candidatos.append("%s %s" % (titulo_limpo, tag))

    for nome in candidatos:
        nome_arquivo = _limpar_nome_arquivo(nome) + ".png"
        url = ("https://raw.githubusercontent.com/libretro-thumbnails/%s/"
              "master/Named_Boxarts/%s" %
              (repo, urllib.parse.quote(nome_arquivo)))

        destino_pasta = os.path.join(PASTA_MINIATURAS, plataforma_id, "Named_Boxarts")
        destino = os.path.join(destino_pasta, _limpar_nome_arquivo(titulo_limpo) + ".png")
        temporario = destino + ".baixando"

        try:
            os.makedirs(destino_pasta, exist_ok=True)
            resultado = subprocess.run(
                ["curl.exe", "--fail", "--silent", "--show-error", "--location",
                 "--max-time", "15", "-A", "ARENA/1.0", "-o", temporario, url],
                capture_output=True)
            if resultado.returncode == 0 and os.path.isfile(temporario) and \
                    os.path.getsize(temporario) > 0 and _e_png_de_verdade(temporario):
                os.replace(temporario, destino)
                return True, None
        except (OSError, subprocess.SubprocessError):
            pass
        finally:
            if os.path.exists(temporario):
                try:
                    os.remove(temporario)
                except OSError:
                    pass

    return False, "Não achei capa pra esse jogo nesse banco."
