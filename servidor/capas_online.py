# -*- coding: utf-8 -*-
"""Busca a capa (box art) de um jogo no libretro-thumbnails - o mesmo
banco de miniaturas que o proprio RetroArch usa no "Atualizador Online
-> Miniaturas" do menu dele. E' curado pelo projeto libretro, gratis,
sem chave de API.

So funciona sob pedido (botao "Atualizar capa"), nunca sozinho - a regra
do ARENA e' nao depender de internet no meio da aula (ver comentario em
indexador.py). O aluno clica quando quiser tentar.
"""

import difflib
import os
import re
import subprocess
import time
import urllib.parse

import capas_do_disco


RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_MINIATURAS = os.path.join(RAIZ, "retroarch", "thumbnails")

# Todos os consoles do ARENA que tem banco no libretro-thumbnails. Lista
# oficial dos 131 bancos conferida pela API do GitHub em 02/10/2026 (antes
# eram so 16 consoles; o comentario dizia que PS2, PS3 e Xbox 360 "nao tem
# cobertura boa" -- o banco do PS2 tem 8.501 capas, e a do Crash Nitro Kart
# estava la). Mais de um banco: tenta na ordem (o Game Boy Color, o Master
# System e o Game Gear tem banco proprio). Sem banco nenhum: Uzebox,
# Tamagotchi e Java ME.
REPO_POR_PLATAFORMA = {
    "tic80": "TIC-80",
    "wasm4": "WASM-4",
    "lowresnx": "LowRes_NX",
    "atari2600": "Atari_-_2600",
    "atari5200": "Atari_-_5200",
    "atari7800": "Atari_-_7800",
    "lynx": "Atari_-_Lynx",
    "jaguar": "Atari_-_Jaguar",
    "nes": ("Nintendo_-_Nintendo_Entertainment_System", "Nintendo_-_Family_Computer_Disk_System"),
    "snes": ("Nintendo_-_Super_Nintendo_Entertainment_System", "Nintendo_-_Satellaview",
             "Nintendo_-_Sufami_Turbo"),
    "gameboy": ("Nintendo_-_Game_Boy", "Nintendo_-_Game_Boy_Color"),
    "gba": "Nintendo_-_Game_Boy_Advance",
    "virtualboy": "Nintendo_-_Virtual_Boy",
    "pokemini": "Nintendo_-_Pokemon_Mini",
    "gamewatch": "Handheld_Electronic_Game",
    "n64": ("Nintendo_-_Nintendo_64", "Nintendo_-_Nintendo_64DD"),
    "nds": ("Nintendo_-_Nintendo_DS", "Nintendo_-_Nintendo_DSi"),
    "gamecube": "Nintendo_-_GameCube",
    # Conferido 25/09/2026: Mario Kart Wii (USA) (En,Fr,Es).png -> 200, PNG.
    "wii": "Nintendo_-_Wii",
    "sg1000": "Sega_-_SG-1000",
    "megadrive": ("Sega_-_Mega_Drive_-_Genesis", "Sega_-_Master_System_-_Mark_III", "Sega_-_Game_Gear",
                  "Sega_-_PICO"),
    "sega32x": "Sega_-_32X",
    "segacd": "Sega_-_Mega-CD_-_Sega_CD",
    "saturn": "Sega_-_Saturn",
    "dreamcast": ("Sega_-_Dreamcast", "Sega_-_Naomi", "Sega_-_Naomi_2", "Atomiswave"),
    "ps1": "Sony_-_PlayStation",
    "ps2": "Sony_-_PlayStation_2",
    "psp": "Sony_-_PlayStation_Portable",
    "ps3": ("Sony_-_PlayStation_3", "Sony_-_PlayStation_3_Downloadable"),
    "xbox360": "Microsoft_-_Xbox_360",
    # Fliperama: o banco do FBNeo tem tambem os fliperamas que nao sao Neo
    # Geo (TMNT2...); o nome que vale e' o COMPLETO do banco de dados do
    # RetroArch (servidor\nomes_arcade.py). Conferido 01/10/2026: "Metal Slug
    # X - Super Vehicle-001 (NGM-2500)(NGH-2500).png" -> 200 no FBNeo e no
    # MAME; "Killer Instinct (v1.0).png" -> 200 no MAME.
    "neogeo": ("FBNeo_-_Arcade_Games", "SNK_-_Neo_Geo", "SNK_-_Neo_Geo_CD"),
    "arcade": ("MAME", "FBNeo_-_Arcade_Games"),
    "ngp": ("SNK_-_Neo_Geo_Pocket_Color", "SNK_-_Neo_Geo_Pocket"),
    "pcengine": ("NEC_-_PC_Engine_-_TurboGrafx_16", "NEC_-_PC_Engine_CD_-_TurboGrafx-CD",
                 "NEC_-_PC_Engine_SuperGrafx"),
    "pcfx": "NEC_-_PC-FX",
    "wonderswan": ("Bandai_-_WonderSwan_Color", "Bandai_-_WonderSwan"),
    "threedo": "The_3DO_Company_-_3DO",
    "cdi": "Philips_-_CD-i",
    "odyssey2": ("Magnavox_-_Odyssey2", "Philips_-_Videopac"),
    "colecovision": "Coleco_-_ColecoVision",
    "intellivision": "Mattel_-_Intellivision",
    "vectrex": "GCE_-_Vectrex",
    "msx": ("Microsoft_-_MSX", "Microsoft_-_MSX2"),
    "c64": "Commodore_-_64",
    "amiga": ("Commodore_-_Amiga", "Commodore_-_CD32", "Commodore_-_CDTV"),
    "spectrum": "Sinclair_-_ZX_Spectrum",
    "amstrad": ("Amstrad_-_CPC", "Amstrad_-_GX4000"),
    "dos": "DOS",
    "scummvm": "ScummVM",
}

# O servidor de miniaturas do proprio RetroArch (o "Atualizador Online"
# dele) publica a LISTA de capas de cada banco. Com ela o ARENA acha a capa
# pelo nome PARECIDO -- "Crash Nitro Kart.iso" acha "Crash Nitro Kart
# (USA).png" -- em vez de adivinhar o nome exato. A lista fica guardada em
# thumbnails\<console>\_lista_<banco>.txt por 30 dias (a de PS2 tem 8.501
# nomes; baixar de novo a cada capa seria 2 MB por clique).
SERVIDOR_MINIATURAS = "https://thumbnails.libretro.com"
VALIDADE_DA_LISTA = 30 * 24 * 3600
# Quando ha capa de varias regioes e o arquivo nao diz a dele.
PREFERENCIA_DE_REGIAO = ("(usa", "(world", "(europe", "(brazil", "(japan")


def sistema_do_banco(repo):
    """Nome do banco no servidor de miniaturas: "Sony_-_PlayStation_2" vira
    "Sony - PlayStation 2"."""
    return repo.replace("_-_", " - ").replace("_", " ")


def _baixar(url, destino, segundos=15):
    """Baixa com o curl do Windows (sem instalar nada). True se chegou."""
    try:
        resultado = subprocess.run(
            ["curl.exe", "--fail", "--silent", "--show-error", "--location",
             "--max-time", str(segundos), "-A", "ARENA/1.0", "-o", destino, url],
            capture_output=True)
        return resultado.returncode == 0 and os.path.isfile(destino) and os.path.getsize(destino) > 0
    except (OSError, subprocess.SubprocessError):
        return False


def _apagar(caminho):
    try:
        os.remove(caminho)
    except OSError:
        pass


def _ler_lista(caminho):
    try:
        with open(caminho, encoding="utf-8") as arquivo:
            return [linha.rstrip("\n") for linha in arquivo if linha.strip()]
    except OSError:
        return []


def lista_do_banco(plataforma_id, repo):
    """Os nomes das capas do banco (sem o .png), da lista oficial guardada
    por 30 dias. Sem internet, a lista velha ainda serve; sem nenhuma, []."""
    pasta = os.path.join(PASTA_MINIATURAS, plataforma_id)
    guardada = os.path.join(pasta, "_lista_%s.txt" % repo)
    try:
        if time.time() - os.path.getmtime(guardada) < VALIDADE_DA_LISTA:
            return _ler_lista(guardada)
    except OSError:
        pass
    url = "%s/%s/Named_Boxarts/" % (SERVIDOR_MINIATURAS, urllib.parse.quote(sistema_do_banco(repo)))
    temporario = guardada + ".baixando"
    try:
        os.makedirs(pasta, exist_ok=True)
        if _baixar(url, temporario, 60):
            with open(temporario, encoding="utf-8", errors="replace") as arquivo:
                pagina = arquivo.read()
            nomes = sorted({urllib.parse.unquote(href)[:-4]
                            for href in re.findall(r'href="([^"/?]+\.png)"', pagina)})
            if nomes:
                with open(temporario, "w", encoding="utf-8") as arquivo:
                    arquivo.write("\n".join(nomes) + "\n")
                os.replace(temporario, guardada)
                return nomes
    except OSError:
        pass
    finally:
        _apagar(temporario)
    return _ler_lista(guardada)


def _chave(nome):
    """O nome so com o que identifica o jogo: sem regiao/versao entre
    parenteses ou colchetes, sem pontuacao, sem "the", tudo junto e em
    minusculas. "The Legend of Zelda - A Link to the Past (USA)" e
    "Legend of Zelda, The - A Link to the Past" viram a mesma chave."""
    nome = re.sub(r"\([^)]*\)|\[[^\]]*\]", " ", str(nome or ""))
    nome = nome.casefold().replace("&", " and ")
    palavras = [p for p in re.split(r"[\W_]+", nome) if p and p != "the"]
    return "".join(palavras)


# Nome "de cena" (arquivo baixado de grupo): "Metal Gear Solid Peace Walker
# V2 00 USA MULTi3 PSP PUSSYCAT". Do primeiro marcador de regiao, versao ou
# formato em diante e' lixo para achar a capa.
MARCADOR_DE_CENA = re.compile(r"\s(?:V\d+(?:\s\d+)?|USA|EUR|EUROPE|JPN|JAP|JAPAN|PAL|NTSC|MULTI\d*|"
                              r"PSP|ISO|CSO|RIP|BRAZIL|PT-?BR)(?:\s|$)", re.I)


def limpar_nome_de_cena(titulo):
    """O titulo antes do primeiro marcador de cena (ou ele mesmo)."""
    achado = MARCADOR_DE_CENA.search(" " + str(titulo or ""))
    return str(titulo or "")[:max(achado.start() - 1, 0)].strip() if achado else str(titulo or "")


def _prefixo_seguro(curta, longa):
    """'longa' e' 'curta' + subtitulo SEM numero ("Street Fighter II Turbo" +
    "Hyper Fighting")? Com numero no resto, nao: "Crash Bandicoot" nao e'
    capa do "Crash Bandicoot 3"."""
    if not curta or not longa.startswith(curta) or len(curta) < 0.55 * len(longa):
        return False
    resto = longa[len(curta):]
    return not re.search(r"\d|^(?:i|ii|iii|iv|v|vi|vii|viii|ix|x)", resto)


def escolher_capa(nomes, titulo, nome_base=""):
    """Das capas do banco, a deste jogo (ou None). Primeiro a chave igual
    (do nome do arquivo, do titulo e do titulo sem o lixo de cena); depois
    o mesmo nome com ou sem subtitulo (sem numero); por ultimo, a mais
    parecida (90% ou mais). Entre varias regioes: a do arquivo, se ele
    disser; senao EUA, Mundo, Europa, Brasil, Japao."""
    por_chave = {}
    for nome in nomes:
        por_chave.setdefault(_chave(nome), []).append(nome)
    alvos = [c for c in (_chave(nome_base), _chave(titulo), _chave(limpar_nome_de_cena(titulo))) if c]
    candidatos = next((por_chave[c] for c in alvos if c in por_chave), None)
    if not candidatos and alvos:
        for alvo in alvos:
            parecidos = [c for c in por_chave if _prefixo_seguro(c, alvo) or _prefixo_seguro(alvo, c)]
            if parecidos:
                candidatos = por_chave[min(parecidos, key=lambda c: abs(len(c) - len(alvo)))]
                break
    if not candidatos and alvos:
        perto = difflib.get_close_matches(alvos[-1], list(por_chave), n=1, cutoff=0.9)
        candidatos = por_chave.get(perto[0]) if perto else None
    if not candidatos:
        return None
    for nome in candidatos:
        if nome_base and nome.casefold() == str(nome_base).casefold():
            return nome
    regiao = re.search(r"\(([^),]+)", str(nome_base or ""))
    if regiao:
        mesma = [n for n in candidatos if ("(" + regiao.group(1).casefold()) in n.casefold()]
        if mesma:
            return sorted(mesma, key=len)[0]

    def ordem(nome):
        baixo = nome.casefold()
        return (next((i for i, r in enumerate(PREFERENCIA_DE_REGIAO) if r in baixo),
                     len(PREFERENCIA_DE_REGIAO)), len(nome))
    return sorted(candidatos, key=ordem)[0]


def _baixar_capa(repo, nome, destino):
    """Baixa a capa 'nome' do banco para 'destino' (PNG de verdade ou nada):
    do servidor de miniaturas e, se ele falhar, do GitHub do libretro."""
    arquivo = urllib.parse.quote(nome + ".png")
    temporario = destino + ".baixando"
    try:
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        for url in ("%s/%s/Named_Boxarts/%s" % (SERVIDOR_MINIATURAS,
                                                 urllib.parse.quote(sistema_do_banco(repo)), arquivo),
                    "https://raw.githubusercontent.com/libretro-thumbnails/%s/master/Named_Boxarts/%s"
                    % (repo, arquivo)):
            if _baixar(url, temporario) and _e_png_de_verdade(temporario):
                os.replace(temporario, destino)
                return True
            _apagar(temporario)
    except OSError:
        pass
    finally:
        _apagar(temporario)
    return False


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


def _guardar(dados, destino):
    """Grava os bytes de uma capa (atomico)."""
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    temporario = destino + ".gravando"
    with open(temporario, "wb") as arquivo:
        arquivo.write(dados)
    os.replace(temporario, destino)


def _baixar_imagem(urls, destino, assinatura):
    """A primeira das 'urls' que chegar com a 'assinatura' de imagem certa."""
    temporario = destino + ".baixando"
    try:
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        for url in urls:
            if _baixar(url, temporario):
                with open(temporario, "rb") as arquivo:
                    comeco = arquivo.read(len(assinatura))
                if comeco == assinatura and os.path.getsize(temporario) > 1024:
                    os.replace(temporario, destino)
                    return True
            _apagar(temporario)
    except OSError:
        pass
    finally:
        _apagar(temporario)
    return False


def capa_pelo_disco(plataforma_id, titulo_limpo, caminho_jogo, com_internet=True):
    """Capa tirada do proprio disco (servidor/capas_do_disco.py), quando o
    banco do RetroArch nao tem. Devolve o nome da fonte, ou None."""
    if not caminho_jogo or not os.path.isfile(caminho_jogo):
        return None
    pasta = os.path.join(PASTA_MINIATURAS, plataforma_id, "Named_Boxarts")
    nome = _limpar_nome_arquivo(titulo_limpo)
    if plataforma_id in ("ps3", "psp"):
        icone = capas_do_disco.icone_do_disco(caminho_jogo, plataforma_id)
        if icone:
            _guardar(icone, os.path.join(pasta, nome + ".png"))
            return "o ícone que vem no disco"
    if not com_internet:
        return None
    if plataforma_id == "xbox360":
        title_id = capas_do_disco.title_id_do_xbox360(caminho_jogo)
        if title_id and _baixar_imagem([capas_do_disco.url_capa_xbox360(title_id)],
                                       os.path.join(pasta, nome + ".jpg"), b"\xff\xd8\xff"):
            return "a capa oficial do Xbox 360 (Microsoft)"
    if plataforma_id in ("gamecube", "wii"):
        codigo = capas_do_disco.id_do_disco_nintendo(caminho_jogo)
        if codigo and _baixar_imagem(capas_do_disco.urls_capa_nintendo(codigo),
                                     os.path.join(pasta, nome + ".png"), _ASSINATURA_PNG):
            return "o GameTDB (a fonte de capas do Dolphin)"
    return None


def buscar_e_baixar(plataforma_id, titulo_limpo, nome_base_arquivo, caminho_jogo=None, com_internet=True):
    """Tenta achar a capa por varios nomes candidatos, do mais especifico
    (nome do ARQUIVO, com a tag de regiao de verdade) ao mais generico
    (titulo limpo + cada tag de regiao comum). Salva em
    retroarch/thumbnails/<plataforma>/Named_Boxarts/ com o TITULO LIMPO
    (e' o que indexador.capas_do_jogo ja procura).

    Devolve (ok, motivo).
    """
    repos = REPO_POR_PLATAFORMA.get(plataforma_id)
    if not repos:
        return False, "Este console não tem banco de capas (nem no RetroArch). Envie a capa à mão."
    if isinstance(repos, str):
        repos = (repos,)

    destino = os.path.join(PASTA_MINIATURAS, plataforma_id, "Named_Boxarts",
                           _limpar_nome_arquivo(titulo_limpo) + ".png")
    if not com_internet:
        fonte = capa_pelo_disco(plataforma_id, titulo_limpo, caminho_jogo, com_internet=False)
        return (True, fonte) if fonte else (False, "Sem internet agora. Essa busca precisa de conexão.")
    # Pela lista oficial de cada banco (nome parecido, regiao certa).
    achou_lista = False
    for repo in repos:
        nomes = lista_do_banco(plataforma_id, repo)
        achou_lista = achou_lista or bool(nomes)
        escolhido = escolher_capa(nomes, titulo_limpo, nome_base_arquivo) if nomes else None
        if escolhido and _baixar_capa(repo, escolhido, destino):
            return True, None
    # PS3 e Xbox 360 quase nao tem no banco; GameCube e Wii, nem tudo: o
    # proprio disco ajuda.
    fonte = capa_pelo_disco(plataforma_id, titulo_limpo, caminho_jogo)
    if fonte:
        return True, fonte
    if achou_lista:
        return False, "Não achei capa pra esse jogo nesse banco."

    # Sem lista nenhuma (servidor de miniaturas fora do ar): o jeito antigo,
    # tentando o nome exato no GitHub do libretro.
    candidatos = []
    if nome_base_arquivo and nome_base_arquivo != titulo_limpo:
        candidatos.append(nome_base_arquivo)
    candidatos.append(titulo_limpo)
    if "(" not in titulo_limpo:
        for tag in TAGS_REGIAO:
            candidatos.append("%s %s" % (titulo_limpo, tag))

    for repo, nome in ((r, n) for r in repos for n in candidatos):
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
