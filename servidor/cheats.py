# -*- coding: utf-8 -*-
"""
ARENA - Cheats e save states
=============================
Duas coisas que o RetroArch ja faz muito bem, e que o ARENA apenas organiza:

CHEATS
    O RetroArch le arquivos '.cht' e mostra os codigos no menu do jogo,
    com um interruptor para ligar e desligar cada um. Ele aceita codigo de
    Game Genie, GameShark, Action Replay e Pro Action Replay.
    Este modulo escreve e le esses arquivos. A edicao acontece na tela do
    ARENA; quem aplica o codigo no jogo e o RetroArch.

SAVE STATES
    O RetroArch guarda 10 estados por jogo, nos espacos 0 a 9. O espaco 0
    grava em 'jogo.state'; os demais em 'jogo.state1' ate 'jogo.state9'.
    Este modulo apenas LE esses arquivos para mostrar na tela quais espacos
    estao ocupados, de quando sao e quanto ocupam.

ONDE O RETROARCH GUARDA CADA COISA (conferido no RetroArch 1.22.2 desta
pasta, auditoria 3, 09/10/2026). Ate entao o ARENA procurava no lugar
errado, e a gaveta "Saves e cheats" nao funcionava:
  - saves e estados ficam numa subpasta com o nome do NUCLEO
    (retroarch\\states\\Snes9x\\jogo.state), porque o retroarch.cfg separa
    por nucleo (sort_savefiles_enable, sort_savestates_enable). O ARENA
    olhava so a raiz: os espacos apareciam sempre "vazio";
  - os cheats: o RetroArch so procura em retroarch\\cheats\\<nucleo>\\, com
    o nome do arquivo do jogo cortado no ULTIMO ponto (ver nome_do_cht). O
    ARENA gravava em retroarch\\cheats\\<console>\\ e o RetroArch nunca lia;
  - e cada codigo precisa de handler 0 (o do emulador). O ARENA gravava 1,
    que e' o motor de busca de memoria do proprio RetroArch: o codigo nem
    chegava ao emulador. Provado lendo a memoria do jogo dentro do save
    state (testes\\teste_cheats_no_jogo.py).

So biblioteca padrao.
"""

import os
import threading
import re
import time

_TRAVA = threading.Lock()

PASTA_SERVIDOR = os.path.dirname(os.path.abspath(__file__))


def gravar_atomico(caminho, texto):
    """Grava sem deixar meio-termo, mesmo com varias gravacoes ao mesmo tempo.

    Nome de temporario unico por thread: sem isso, duas gravacoes juntas
    disputam o mesmo arquivo e a segunda estoura.
    """
    temporario = "%s.%d.tmp" % (caminho, threading.get_ident())
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with _TRAVA:
        try:
            with open(temporario, "w", encoding="utf-8") as arquivo:
                arquivo.write(texto)
                arquivo.flush()
                os.fsync(arquivo.fileno())
            os.replace(temporario, caminho)
        finally:
            if os.path.exists(temporario):
                try:
                    os.remove(temporario)
                except OSError:
                    pass
RAIZ = os.path.dirname(PASTA_SERVIDOR)

PASTA_RETROARCH = os.path.join(RAIZ, "retroarch")
PASTA_CHEATS = os.path.join(PASTA_RETROARCH, "cheats")
PASTA_STATES = os.path.join(PASTA_RETROARCH, "states")
PASTA_SAVES = os.path.join(PASTA_RETROARCH, "saves")
PASTA_INFO = os.path.join(PASTA_RETROARCH, "info")

TOTAL_ESPACOS = 10

# Codigo valido, bloco por bloco (os blocos sao separados por espaco, quebra
# de linha ou '+'). Cada bloco e':
#  - digitos hexadecimais com ':', '-', '=' ou '?' (GameShark, Action Replay,
#    Pro Action Replay, Game Genie do SNES e do Game Boy: "7E0DBE:09",
#    "DD32-6DAD", "7E0DBE=09");
#  - ou Game Genie do NES: 6 ou 8 letras do alfabeto dele ("SXIOPO");
#  - ou Game Genie do Mega Drive: "ATBT-AA32" (letras e numeros dele).
# Antes (ate a auditoria 3) so valia o hexadecimal: os codigos de Game Genie
# do NES e do Mega Drive, os mais comuns, eram recusados.
RE_BLOCO_HEXA = re.compile(r"^[0-9A-Fa-f][0-9A-Fa-f:\-=?]*$")
RE_BLOCO_GG_NES = re.compile(r"^(?:[APZLGITYEOXUKSVN]{6}|[APZLGITYEOXUKSVN]{8})$", re.I)
RE_BLOCO_GG_MEGA = re.compile(r"^[ABCDEFGHJKLMNPRSTVWXYZ0-9]{4}-[ABCDEFGHJKLMNPRSTVWXYZ0-9]{4}$", re.I)
# Os caracteres que podem existir no codigo. Nada de aspas, barra ou quebra
# de linha: o codigo vai entre aspas numa linha do arquivo .cht.
RE_CODIGO = re.compile(r"^[0-9A-Za-z:\-=?\s\+]+$")


# ---------------------------------------------------------------------------
# Nomes de arquivo e pastas
# ---------------------------------------------------------------------------

def nome_seguro(texto):
    """Transforma um titulo em nome de arquivo valido no Windows."""
    limpo = re.sub(r'[<>:"/\\|?*]', "", str(texto)).strip()
    limpo = re.sub(r"\s+", " ", limpo)
    return limpo[:100] or "sem_nome"


def base_do_jogo(jogo):
    """Nome do arquivo do jogo, sem pasta e sem extensao.

    E assim que o RetroArch nomeia os saves e os estados: pelo nome do
    arquivo da ROM, nao pelo titulo que aparece na tela do ARENA.
    """
    return os.path.splitext(os.path.basename(jogo["arquivo"]))[0]


_NOMES_DOS_NUCLEOS = {}


def nome_do_nucleo(arquivo_core, pasta_info=None):
    """'Snes9x', de 'snes9x_libretro.dll': o nome que o RetroArch da a pasta
    do nucleo dentro de saves, states e cheats. E' o 'corename' do .info do
    nucleo (o mesmo nome que o nucleo informa ao RetroArch; conferido nas
    pastas que o proprio RetroArch criou aqui). None sem .info -- o
    emulador de fora (PCSX2, Dolphin...) nao usa estas pastas."""
    if not arquivo_core:
        return None
    pasta_info = pasta_info or PASTA_INFO
    chave = (pasta_info, os.path.basename(arquivo_core).lower())
    if chave in _NOMES_DOS_NUCLEOS:
        return _NOMES_DOS_NUCLEOS[chave]
    nome = None
    info = os.path.join(pasta_info, os.path.splitext(os.path.basename(arquivo_core))[0] + ".info")
    try:
        with open(info, encoding="utf-8", errors="replace") as arquivo:
            for linha in arquivo:
                if linha.startswith("corename"):
                    nome = linha.split("=", 1)[1].strip().strip('"').strip() or None
                    break
    except OSError:
        pass
    if nome and (re.search(r'[<>:"/\\|?*]', nome) or nome in (".", "..")):
        nome = None            # nao daria uma pasta valida no Windows
    _NOMES_DOS_NUCLEOS[chave] = nome
    return nome


def _pastas(pasta, nucleo):
    """Onde procurar saves e estados: a subpasta do nucleo, onde o RetroArch
    grava, e depois a propria pasta (o RetroArch com a separacao por nucleo
    desligada, ou arquivos de antes)."""
    return ([os.path.join(pasta, nucleo)] if nucleo else []) + [pasta]


def nome_do_cht(jogo):
    """O nome do arquivo de cheats que o RetroArch procura para este jogo.

    Ele tira a extensao do arquivo do jogo e, ao por o '.cht', corta de novo
    no ultimo ponto que sobrou (fill_pathname, no codigo dele):
      'Sonic The Hedgehog 3 (USA).md'            -> 'Sonic The Hedgehog 3 (USA).cht'
      'Super Bomberman 4 (Japan) [v1.0].sfc'     -> 'Super Bomberman 4 (Japan) [v1.cht'
      'Mr. Driller (USA).chd'                    -> 'Mr.cht'
    Conferido no registro do RetroArch 1.22.2 ("Load game-specific
    cheatfile"). Limite que fica (do RetroArch, nao do ARENA): dois jogos do
    mesmo nucleo cujo nome so muda depois de um ponto dividem o arquivo.
    """
    base = base_do_jogo(jogo)
    if "." in base:
        base = base[:base.rindex(".")]
    return base + ".cht"


def caminho_cht(jogo, nucleo=None):
    """Onde fica o arquivo de cheats deste jogo: retroarch\\cheats\\<nucleo>\\,
    o unico lugar em que o RetroArch procura. Sem nucleo conhecido, o lugar
    antigo do ARENA (so para ler o que ja estava la)."""
    if nucleo:
        return os.path.join(PASTA_CHEATS, nucleo, nome_do_cht(jogo))
    return caminho_cht_antigo(jogo)


def caminho_cht_antigo(jogo):
    """Onde o ARENA gravava ate a auditoria 3: retroarch\\cheats\\<console>\\.
    O RetroArch nunca lia dali. Continua sendo lido quando o arquivo novo
    ainda nao existe, para nao sumir com codigo que alguem ja cadastrou (a
    primeira mudanca grava tudo no lugar novo; o antigo fica como estava)."""
    pasta = os.path.join(PASTA_CHEATS, nome_seguro(jogo["plataforma_nome"]))
    return os.path.join(pasta, nome_seguro(base_do_jogo(jogo)) + ".cht")


# ---------------------------------------------------------------------------
# Save states e saves: leitura (e apagar um espaco, a pedido)
# ---------------------------------------------------------------------------

def _sufixo(espaco):
    # Espaco 0 nao leva numero no final. Do 1 ao 9, leva.
    return ".state" if espaco == 0 else ".state%d" % espaco


def listar_estados(jogo, nucleo=None):
    """Diz quais dos 10 espacos estao ocupados para este jogo."""
    base = base_do_jogo(jogo)
    espacos = []

    for numero in range(TOTAL_ESPACOS):
        item = {"espaco": numero, "existe": False,
                "quando": None, "tamanho_kb": None}
        for pasta in _pastas(PASTA_STATES, nucleo):
            try:
                dados = os.stat(os.path.join(pasta, base + _sufixo(numero)))
            except OSError:
                continue
            item["existe"] = True
            item["quando"] = time.strftime("%d/%m/%Y %H:%M",
                                           time.localtime(dados.st_mtime))
            item["tamanho_kb"] = round(dados.st_size / 1024, 1)
            break
        espacos.append(item)

    return espacos


def apagar_estado(jogo, espaco, nucleo=None):
    """Apaga um espaco especifico (o que a tela mostra) e a foto dele."""
    if not 0 <= int(espaco) < TOTAL_ESPACOS:
        raise ValueError("Escolha um espaço de 0 a 9.")
    espaco = int(espaco)
    for pasta in _pastas(PASTA_STATES, nucleo):
        caminho = os.path.join(pasta, base_do_jogo(jogo) + _sufixo(espaco))
        try:
            os.remove(caminho)
        except OSError:
            continue
        # A foto do estado (savestate_thumbnail_enable) vai junto: sozinha,
        # ela so ocuparia lugar.
        try:
            os.remove(caminho + ".png")
        except OSError:
            pass
        return True
    return False


def tem_save(jogo, nucleo=None):
    """Diz se o jogo tem save comum (o do proprio jogo, nao o estado)."""
    base = base_do_jogo(jogo)
    for pasta in _pastas(PASTA_SAVES, nucleo):
        for extensao in (".srm", ".sav", ".rtc", ".mcr"):
            if os.path.isfile(os.path.join(pasta, base + extensao)):
                return True
    return False


# ---------------------------------------------------------------------------
# Cheats: leitura
# ---------------------------------------------------------------------------

RE_LINHA = re.compile(r'^\s*cheat(\d+)_(\w+)\s*=\s*"?(.*?)"?\s*$')


def _ler_registros(jogo, nucleo=None):
    """Os cheats do arquivo como estao nele: uma lista de dicionarios com
    TODOS os campos (desc, code, enable, handler e, nos cheats que o aluno
    fez pela busca de memoria do menu do RetroArch, address, value...).
    Guardar todos os campos e' o que deixa o ARENA regravar o arquivo sem
    estragar o que o RetroArch escreveu nele."""
    caminho = caminho_cht(jogo, nucleo)
    antigo = False
    if nucleo and not os.path.isfile(caminho):
        caminho, antigo = caminho_cht_antigo(jogo), True
    if not os.path.isfile(caminho):
        return []

    campos = {}
    try:
        with open(caminho, "r", encoding="utf-8", errors="replace") as arquivo:
            for linha in arquivo:
                achou = RE_LINHA.match(linha)
                if not achou:
                    continue
                indice, campo, valor = achou.groups()
                campos.setdefault(int(indice), {})[campo] = valor
    except OSError:
        return []
    registros = [campos[indice] for indice in sorted(campos)]
    if antigo:
        # Do lugar antigo, todo codigo foi o ARENA que gravou -- com o
        # handler errado (1). Ao ir para o lugar novo, vai certo (0).
        for registro in registros:
            if registro.get("code"):
                registro["handler"] = "0"
    return registros


def _publico(registro):
    return {
        "descricao": registro.get("desc") or "Sem descrição",
        "codigo": registro.get("code", ""),
        "ligado": registro.get("enable", "false").lower() == "true",
    }


def ler_cheats(jogo, nucleo=None):
    """Le o arquivo .cht do jogo e devolve a lista de codigos."""
    return [_publico(registro) for registro in _ler_registros(jogo, nucleo)]


# ---------------------------------------------------------------------------
# Cheats: escrita
# ---------------------------------------------------------------------------

def validar_codigo(codigo):
    """Confere se o codigo tem cara de codigo antes de gravar.

    Nao valida se o codigo FUNCIONA - so o RetroArch e o jogo sabem disso.
    Valida se o formato e aceitavel, para nao gravar lixo no arquivo.
    """
    codigo = (codigo or "").strip()
    if not codigo:
        return None, "Digite o código."
    if len(codigo) > 2000:
        return None, "Código grande demais: confira se copiou só o código."
    blocos = [b for b in re.split(r"[\s+]+", codigo) if b]
    if not RE_CODIGO.match(codigo) or not all(
            RE_BLOCO_HEXA.match(b) or RE_BLOCO_GG_NES.match(b) or RE_BLOCO_GG_MEGA.match(b)
            for b in blocos):
        return None, ("Código inválido. Copie o código exatamente como ele aparece (Game Genie, "
                      "GameShark ou Action Replay), sem o nome do cheat, e separe as linhas com "
                      "espaço.")
    # Normaliza: uma linha so, blocos separados por '+', que e o separador
    # que o RetroArch usa para codigo de varias linhas.
    return "+".join(blocos), None


def _texto_simples(texto, limite=120):
    """Texto que vai entre aspas numa linha do .cht: sem quebra de linha nem
    caractere de controle (uma quebra de linha na descricao criaria linhas
    novas no arquivo) e sem aspas."""
    return re.sub(r"[\x00-\x1f\x7f]", " ", str(texto))[:limite].replace('"', "'").strip()


def _gravar_registros(jogo, registros, nucleo=None):
    linhas = ["cheats = %d" % len(registros), ""]
    for indice, registro in enumerate(registros):
        for campo in sorted(registro):
            linhas.append('cheat%d_%s = "%s"' % (indice, campo, registro[campo]))
        linhas.append("")
    caminho = caminho_cht(jogo, nucleo)
    # Grava em arquivo temporario e so depois troca. Se o pen drive for
    # retirado no meio, o arquivo antigo continua intacto.
    gravar_atomico(caminho, "\n".join(linhas))
    return caminho


def _registro_novo(descricao, codigo, ligado):
    # handler 0 = o codigo vai para o EMULADOR (Game Genie, GameShark, Action
    # Replay). O 1 e' a busca de memoria do proprio RetroArch, que ignora o
    # codigo (cheat_manager.h do RetroArch: CHEAT_HANDLER_TYPE_EMU = 0).
    return {"desc": _texto_simples(descricao) or "Sem descrição", "code": codigo,
            "enable": "true" if ligado else "false", "handler": "0"}


def gravar_cheats(jogo, cheats, nucleo=None):
    """Escreve o arquivo .cht no formato que o RetroArch le.

    Formato:
        cheats = 2

        cheat0_code = "7E0DBE:09"
        cheat0_desc = "Vidas infinitas"
        cheat0_enable = "false"
        cheat0_handler = "0"
    """
    return _gravar_registros(jogo, [
        _registro_novo(c.get("descricao", ""), c["codigo"], c.get("ligado")) for c in cheats], nucleo)


def adicionar_cheat(jogo, descricao, codigo, ligado=False, nucleo=None):
    codigo_limpo, erro = validar_codigo(codigo)
    if erro:
        return None, erro

    registros = _ler_registros(jogo, nucleo)
    if len(registros) >= 60:
        return None, "Este jogo já tem 60 códigos, o máximo. Apague um para pôr outro."

    registros.append(_registro_novo(descricao, codigo_limpo, bool(ligado)))
    _gravar_registros(jogo, registros, nucleo)
    return [_publico(r) for r in registros], None


def levar_do_lugar_antigo(jogo, nucleo):
    """Ao abrir o jogo (servidor\\arena.py, executar_jogo): os codigos
    cadastrados antes da auditoria 3, no lugar em que o RetroArch nao
    procura, vao para o lugar certo e com o handler certo -- e passam a
    funcionar ja nesta partida. O arquivo antigo fica como estava. True se
    levou."""
    if (not nucleo or os.path.isfile(caminho_cht(jogo, nucleo))
            or not os.path.isfile(caminho_cht_antigo(jogo))):
        return False
    registros = _ler_registros(jogo, nucleo)
    if not registros:
        return False
    _gravar_registros(jogo, registros, nucleo)
    return True


def alterar_cheat(jogo, indice, ligado=None, apagar=False, nucleo=None):
    registros = _ler_registros(jogo, nucleo)
    if not 0 <= indice < len(registros):
        return None, "Esse código não está mais na lista. Feche e abra a janela de códigos."
    if apagar:
        registros.pop(indice)
    elif ligado is not None:
        registros[indice]["enable"] = "true" if ligado else "false"
    _gravar_registros(jogo, registros, nucleo)
    return [_publico(r) for r in registros], None
