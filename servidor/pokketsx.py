# -*- coding: utf-8 -*-
r"""
ARENA - o PokketSX: o PlayStation 1 com o PocketStation de verdade (so Windows).

O PokketSX (github.com/mentalfoundry/PokketSX, GPLv3) e' um fork do DuckStation que sabe imitar o PocketStation, o
memory card com telinha da Sony. Em cada entrada de cartao ha uma caixinha "PocketStation no lugar do cartao comum", e o
jogo de PS1 conversa com ele pelo protocolo do cartao: e' assim que o jogo baixa o minijogo para o aparelho. Nao
conheco outro programa em que o jogo de PS1 fale com o PocketStation.

O que ele NAO faz (lido no codigo-fonte em 24/10/2026): mostrar a telinha de 32x32, tocar o som ou ligar os cinco
botoes do PocketStation. As funcoes existem no nucleo dele, mas a janela nao as usa; o PocketStation roda "por dentro"
do cartao. Para jogar o minijogo na telinha, o cartao serve ao console PocketStation do ARENA (nucleo Pokket).

No ARENA ele e' um jeito A MAIS de abrir o PlayStation (consoles.json -> ps1 -> externo_extra) e so abre quando a
pessoa o escolhe na pergunta "como ligar o PlayStation". Todo o resto do PS1 (varios discos, Jogar Junto, o
SwanStation) continua pelo RetroArch.

Este modulo deixa o PokketSX pronto para abrir um jogo sem perguntar nada:
  - as BIOS no lugar (a do PlayStation e a do PocketStation, levadas da pasta BIOS do ARENA);
  - o cartao do PocketStation na entrada 2 e a entrada 1 com o cartao comum de cada jogo (a mesma divisao que o ARENA
    faz no PS2). O cartao do PocketStation e' UM ARQUIVO SO, o mesmo que o console PocketStation do ARENA (nucleo
    Pokket) usa: retroarch\saves\Pokket\Meu PocketStation.srm. O que o jogo baixa para o aparelho (PokketSX) aparece
    na telinha (Pokket) e o contrario, sem copiar nada entre os dois, e com copia de seguranca antes de cada uso;
  - o settings.ini sem o assistente de configuracao, sem pedir confirmacao ao fechar, sem atualizador nem Discord,
    com o F10 fechando o jogo (como no resto do ARENA) e o controle de verdade ligado.
"""
import os
import shutil
import time

import bios as bios_do_arena
import graficos

NOME_DO_CARTAO = "PocketStation.mcd"          # o cartao de dentro da pasta do PokketSX (so se nao houver o unico)
NOME_DO_CARTAO_UNICO = "Meu PocketStation"    # o "jogo" do console PocketStation e o save dele (.srm)
PASTA_DO_POKKET = "Pokket"                    # retroarch\saves\<nome do nucleo> (sort_savefiles_enable = true)
COPIAS_GUARDADAS = 5
NOME_DA_BIOS_POCKETSTATION = "pocketstation.bin"
TAMANHO_DA_BIOS_PS1 = 524288          # 512 KB: a BIOS do PlayStation 1
TAMANHO_DA_BIOS_POCKETSTATION = 16384  # 16 KB: o firmware do aparelho
# O numero que o proprio PokketSX grava em [Main] SettingsVersion (SETTINGS_VERSION em qthost.cpp). Se faltar, ele
# joga fora os ajustes e abre o assistente.
VERSAO_DOS_AJUSTES = 3

# Os atalhos de sempre do PokketSX (iguais aos do DuckStation), menos a captura de tela, e com o F10 fechando o jogo.
ATALHOS = {
    "FastForward": "Keyboard/Tab",
    "TogglePause": "Keyboard/Space",
    "PowerOff": "Keyboard/F10",
    "ToggleFullscreen": "Keyboard/F11",
    "OpenPauseMenu": "Keyboard/Escape",
}

# O controle do jogador 1 no teclado (o padrao dele) e no controle de verdade (SDL-0: o primeiro controle ligado).
# Nomes conferidos no codigo-fonte (sdl_input_source.cpp, Pad do analogico); o controle real fica para o teste do Rafael.
TECLADO = (
    ("Up", "Up"), ("Right", "Right"), ("Down", "Down"), ("Left", "Left"),
    ("Triangle", "I"), ("Circle", "L"), ("Cross", "K"), ("Square", "J"),
    ("Select", "Backspace"), ("Start", "Return"),
    ("L1", "Q"), ("R1", "E"), ("L2", "1"), ("R2", "3"), ("L3", "2"), ("R3", "4"),
    ("LLeft", "A"), ("LRight", "D"), ("LDown", "S"), ("LUp", "W"),
    ("RLeft", "F"), ("RRight", "H"), ("RDown", "G"), ("RUp", "T"),
)
CONTROLE = (
    ("Up", "DPadUp"), ("Right", "DPadRight"), ("Down", "DPadDown"), ("Left", "DPadLeft"),
    ("Triangle", "Y"), ("Circle", "B"), ("Cross", "A"), ("Square", "X"),
    ("Select", "Back"), ("Start", "Start"),
    ("L1", "LeftShoulder"), ("R1", "RightShoulder"), ("L2", "+LeftTrigger"), ("R2", "+RightTrigger"),
    ("L3", "LeftStick"), ("R3", "RightStick"),
    ("LLeft", "-LeftX"), ("LRight", "+LeftX"), ("LDown", "+LeftY"), ("LUp", "-LeftY"),
    ("RLeft", "-RightX"), ("RRight", "+RightX"), ("RDown", "+RightY"), ("RUp", "-RightY"),
    ("SmallMotor", "SmallMotor"), ("LargeMotor", "LargeMotor"),
)


def _ler(caminho):
    try:
        with open(caminho, encoding="utf-8", errors="replace") as arquivo:
            return arquivo.read()
    except OSError:
        return ""


def _por_tamanho(pasta, tamanho):
    """Os arquivos da pasta com exatamente este tamanho (o PokketSX reconhece as BIOS assim)."""
    try:
        return sorted(nome for nome in os.listdir(pasta)
                      if os.path.getsize(os.path.join(pasta, nome)) == tamanho
                      and os.path.isfile(os.path.join(pasta, nome)))
    except OSError:
        return []


def _pasta_de_bios(caminho_executavel):
    return os.path.join(os.path.dirname(caminho_executavel), "bios")


def _bios_do_arena(pasta_sistema):
    """(as BIOS de PS1 de retroarch\\system, a do PocketStation ou "")."""
    ps1 = bios_do_arena.bios_de_playstation("ps1", pasta_sistema)
    poc = os.path.join(pasta_sistema, NOME_DA_BIOS_POCKETSTATION)
    valido = os.path.isfile(poc) and os.path.getsize(poc) == TAMANHO_DA_BIOS_POCKETSTATION
    return ps1, (poc if valido else "")


def falta(caminho_executavel, pasta_sistema=None):
    """O que falta, alem do proprio PokketSX, para ele abrir um jogo. Devolve a frase para o aluno, ou "" se nao
    falta nada. As BIOS contam se ja estao na pasta bios\\ dele ou se o ARENA as tem (e as leva sozinho)."""
    pasta_sistema = pasta_sistema or os.path.join(graficos.PASTA_RETROARCH, "system")
    proprias = _pasta_de_bios(caminho_executavel)
    ps1, poc = _bios_do_arena(pasta_sistema)
    if not _por_tamanho(proprias, TAMANHO_DA_BIOS_PS1) and not ps1:
        return ("O PokketSX precisa da BIOS do PlayStation (um arquivo .bin de 512 KB), e ela ainda não está aqui. "
                "Peça ao professor: o arquivo vai na pasta BIOS\\PS1 do ARENA (Ajustes → Emuladores → BIOS dos "
                "consoles), e o ARENA leva para o PokketSX sozinho.")
    if not _por_tamanho(proprias, TAMANHO_DA_BIOS_POCKETSTATION) and not poc:
        return ("O PokketSX só serve para o PocketStation, e ele precisa da BIOS do aparelho (um arquivo de 16 KB, "
                "tirado do seu PocketStation). Ponha-o na pasta BIOS\\PocketStation do ARENA; o ARENA leva para o "
                "PokketSX sozinho.")
    return ""


def levar_as_bios(caminho_executavel, pasta_sistema):
    """Copia as BIOS do ARENA para a pasta bios\\ do PokketSX, que as acha sozinho pelo tamanho. So copia o que falta
    (se a pessoa ja pos a dela la, nada muda). Devolve os nomes copiados."""
    destino = _pasta_de_bios(caminho_executavel)
    ps1, poc = _bios_do_arena(pasta_sistema)
    copiadas = []
    os.makedirs(destino, exist_ok=True)
    if ps1 and not _por_tamanho(destino, TAMANHO_DA_BIOS_PS1):
        for origem in ps1:
            shutil.copy2(origem, os.path.join(destino, os.path.basename(origem)))
            copiadas.append(os.path.basename(origem))
    if poc and not _por_tamanho(destino, TAMANHO_DA_BIOS_POCKETSTATION):
        shutil.copy2(poc, os.path.join(destino, NOME_DA_BIOS_POCKETSTATION))
        copiadas.append(NOME_DA_BIOS_POCKETSTATION)
    return copiadas


def _gravar_bytes(caminho, dados):
    """Grava sem deixar o arquivo pela metade (um temporario, depois a troca)."""
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    temporario = caminho + ".tmp"
    with open(temporario, "wb") as arquivo:
        arquivo.write(dados)
        arquivo.flush()
        os.fsync(arquivo.fileno())
    os.replace(temporario, caminho)


def garantir_o_cartao(caminho_executavel):
    """O cartao do PocketStation de dentro da pasta do PokketSX (128 KB, o formato do cartao do PS1). Se ainda nao
    existe, nasce formatado e vazio; nunca se troca um que ja exista. Devolve o caminho se criou, senao ""."""
    cartao = os.path.join(os.path.dirname(caminho_executavel), "memcards", NOME_DO_CARTAO)
    if os.path.exists(cartao):
        return ""
    _gravar_bytes(cartao, graficos.cartao_ps1_vazio())
    return cartao


# ---------------------------------------------------------------------------
# O cartao unico: o mesmo arquivo no PokketSX (entrada 2) e no console PocketStation (Pokket)
# ---------------------------------------------------------------------------

def caminho_do_cartao_unico(pasta_saves):
    """retroarch\\saves\\Pokket\\Meu PocketStation.srm: o save que o RetroArch guarda do conteudo "Meu PocketStation"
    (a pasta leva o nome do nucleo, Pokket). Um .srm do Pokket e' o cartao inteiro, byte a byte (128 KB)."""
    return os.path.join(pasta_saves, PASTA_DO_POKKET, NOME_DO_CARTAO_UNICO + ".srm")


def conteudo_do_cartao_unico(pasta_jogos):
    """O "jogo" que aparece no console PocketStation do ARENA: um cartao vazio, so para o Pokket ter o que abrir (o que
    vale e' o .srm dele, que o RetroArch poe por cima assim que existe)."""
    return os.path.join(pasta_jogos, "pessoais", "PocketStation", NOME_DO_CARTAO_UNICO + ".mcd")


def e_o_cartao_unico(caminho_do_jogo):
    """Este jogo do console PocketStation e' o "Meu PocketStation"?"""
    return os.path.splitext(os.path.basename(caminho_do_jogo))[0] == NOME_DO_CARTAO_UNICO


def caminho_do_cartao_para_o_pokketsx(caminho_executavel, pasta_saves):
    """O que vai em Card2Path: o caminho do cartao unico RELATIVO a pasta memcards do PokketSX (ele junta os dois e
    resolve os ".."; o caminho absoluto sairia do pen drive). Em outro disco nao ha caminho relativo: fica o
    cartao de dentro da pasta dele."""
    try:
        return os.path.relpath(caminho_do_cartao_unico(pasta_saves),
                               os.path.join(os.path.dirname(caminho_executavel), "memcards"))
    except ValueError:
        return NOME_DO_CARTAO


def garantir_o_cartao_unico(caminho_executavel, pasta_saves, pasta_jogos):
    """Deixa os dois lados com o que abrir: o save (o cartao) e o "jogo" do console PocketStation. Nunca troca o que ja
    existe. Se havia um cartao so do PokketSX (memcards\\PocketStation.mcd) com coisa dentro, ele vira o unico: nada
    se perde. Devolve os caminhos criados."""
    criados = []
    vazio = graficos.cartao_ps1_vazio()
    cartao = caminho_do_cartao_unico(pasta_saves)
    if not os.path.exists(cartao):
        dados = vazio
        antigo = os.path.join(os.path.dirname(caminho_executavel), "memcards", NOME_DO_CARTAO)
        try:
            if os.path.getsize(antigo) == len(vazio):
                with open(antigo, "rb") as arquivo:
                    dados = arquivo.read()
        except OSError:
            pass
        _gravar_bytes(cartao, dados)
        criados.append(cartao)
    conteudo = conteudo_do_cartao_unico(pasta_jogos)
    if not os.path.exists(conteudo):
        _gravar_bytes(conteudo, vazio)
        criados.append(conteudo)
    return criados


def copia_de_seguranca(pasta_saves, quantas=COPIAS_GUARDADAS):
    """Guarda uma copia do cartao unico em saves\\Pokket\\copias antes de um programa mexer nele (o PokketSX ou o Pokket).
    So copia se o cartao mudou desde a ultima copia, e guarda as 'quantas' mais novas. Devolve o caminho da copia ou ""."""
    cartao = caminho_do_cartao_unico(pasta_saves)
    pasta = os.path.join(os.path.dirname(cartao), "copias")
    try:
        with open(cartao, "rb") as arquivo:
            atual = arquivo.read()
        antigas = sorted(n for n in os.listdir(pasta) if n.startswith(NOME_DO_CARTAO_UNICO) and n.endswith(".srm")) \
            if os.path.isdir(pasta) else []
        if antigas:
            with open(os.path.join(pasta, antigas[-1]), "rb") as arquivo:
                if arquivo.read() == atual:
                    return ""
        copia = os.path.join(pasta, "%s-%s.srm" % (NOME_DO_CARTAO_UNICO, time.strftime("%Y%m%d-%H%M%S")))
        _gravar_bytes(copia, atual)
        for velha in sorted(antigas + [os.path.basename(copia)])[:-quantas]:
            try:
                os.remove(os.path.join(pasta, velha))
            except OSError:
                pass
        return copia
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# O settings.ini
# ---------------------------------------------------------------------------

def _limites_da_secao(linhas, secao):
    """(onde a secao comeca, onde ela acaba depois da ultima linha com texto), ou (None, None)."""
    inicio = next((i for i, linha in enumerate(linhas) if linha.strip() == "[%s]" % secao), None)
    if inicio is None:
        return None, None
    fim = next((i for i in range(inicio + 1, len(linhas)) if linhas[i].strip().startswith("[")), len(linhas))
    while fim > inicio + 1 and not linhas[fim - 1].strip():
        fim -= 1
    return inicio, fim


def _garantir_ligacao(linhas, secao, chave, valor):
    """Garante a linha 'chave = valor' na secao como UMA ligacao a mais da mesma tecla (o PokketSX guarda varias
    ligacoes repetindo a chave). Nao repete a que ja existe."""
    inicio, fim = _limites_da_secao(linhas, secao)
    if inicio is None or fim is None:
        return
    ultima = None
    for i in range(inicio + 1, fim):
        nome, _, atual = linhas[i].partition("=")
        if nome.strip() == chave:
            if atual.strip() == valor:
                return
            ultima = i
    linhas.insert((ultima + 1) if ultima is not None else fim, "%s = %s" % (chave, valor))


def _com_o_controle(texto):
    """O jogador 1 com teclado e com o controle de verdade (SDL-0). Sem a secao, nasce com o teclado padrao."""
    linhas = texto.splitlines()
    if _limites_da_secao(linhas, "Pad1")[0] is None:
        linhas += ["", "[Pad1]", "Type = AnalogController"] + ["%s = Keyboard/%s" % par for par in TECLADO]
    for chave, botao in CONTROLE:
        _garantir_ligacao(linhas, "Pad1", chave, "SDL-0/" + botao)
    return "\n".join(linhas) + "\n"


def montar_config(texto, com_pocketstation=True, cartao=NOME_DO_CARTAO):
    """O settings.ini que o ARENA quer, a partir do que ja existe (ou do texto vazio). O que a pessoa mexeu e o ARENA
    nao governa (qualidade da imagem, som...) fica como estava."""
    texto = graficos._trocar_chaves_ini(texto, "Main", {
        "SettingsVersion": (graficos._valor_ini(texto, "Main", "SettingsVersion") or VERSAO_DOS_AJUSTES),
        "SetupWizardIncomplete": "false",       # o assistente pergunta coisas que o ARENA ja resolveu
        "EnableDiscordPresence": "false",
        "ConfirmPowerOff": "false",             # F10 fecha na hora, sem caixa de confirmacao
        "SaveStateOnExit": "false",             # nao regrava um estado inteiro a cada fechamento (pen drive)
        "PauseOnFocusLoss": "false",
    })
    texto = graficos._trocar_chaves_ini(texto, "AutoUpdater", {"CheckAtStartup": "false"})
    texto = graficos._trocar_chaves_ini(texto, "BIOS", {"SearchDirectory": "bios"})
    cartoes = {"Card1PocketStation": "false", "Card2Type": "Shared", "Card2Path": cartao,
               "Card2PocketStation": "true" if com_pocketstation else "false"}
    if com_pocketstation:
        cartoes["PocketStationBiosPath"] = NOME_DA_BIOS_POCKETSTATION
    texto = graficos._trocar_chaves_ini(texto, "MemoryCards", cartoes)
    if _limites_da_secao(texto.splitlines(), "Hotkeys")[0] is None:
        texto = graficos._trocar_chaves_ini(texto, "Hotkeys", ATALHOS)
    elif graficos._valor_ini(texto, "Hotkeys", "PowerOff") is None:
        texto = graficos._trocar_chaves_ini(texto, "Hotkeys", {"PowerOff": ATALHOS["PowerOff"]})
    return _com_o_controle(texto)


def escrever_config(caminho_executavel, cartao=NOME_DO_CARTAO):
    """Grava o settings.ini do PokketSX (do lado do .exe: o modo portatil). True se mudou alguma coisa. 'cartao' e' o
    Card2Path: o cartao do PocketStation, relativo a pasta memcards dele."""
    arquivo = os.path.join(os.path.dirname(caminho_executavel), "settings.ini")
    antes = _ler(arquivo)
    com_pocketstation = bool(_por_tamanho(_pasta_de_bios(caminho_executavel), TAMANHO_DA_BIOS_POCKETSTATION))
    depois = montar_config(antes, com_pocketstation, cartao)
    if depois.splitlines() == antes.splitlines():
        return False
    graficos.gravar_atomico(arquivo, depois)
    return True


def preparar(caminho_executavel, pasta_sistema, pasta_saves=None, pasta_jogos=None):
    """Deixa o PokketSX pronto para abrir um jogo agora: modo portatil, as BIOS, o cartao e o settings.ini. Com
    'pasta_saves' e 'pasta_jogos' o cartao do PocketStation e' o UNICO (o mesmo do console PocketStation), com uma copia
    de seguranca antes. Devolve {"bios": [nomes copiados], "cartao": [caminhos criados], "copia": caminho ou "",
    "config": True se gravou, "erro": texto}."""
    resultado = {"bios": [], "cartao": [], "copia": "", "config": False, "erro": ""}
    try:
        portatil = os.path.join(os.path.dirname(caminho_executavel), "portable.txt")
        if not os.path.exists(portatil):
            with open(portatil, "w", encoding="utf-8"):
                pass
        resultado["bios"] = levar_as_bios(caminho_executavel, pasta_sistema)
        cartao = NOME_DO_CARTAO
        if pasta_saves and pasta_jogos:
            cartao = caminho_do_cartao_para_o_pokketsx(caminho_executavel, pasta_saves)
        if cartao == NOME_DO_CARTAO:
            criado = garantir_o_cartao(caminho_executavel)
            resultado["cartao"] = [criado] if criado else []
        else:
            resultado["cartao"] = garantir_o_cartao_unico(caminho_executavel, pasta_saves, pasta_jogos)
            if caminho_do_cartao_unico(pasta_saves) not in resultado["cartao"]:     # o recem-criado nao tem o que guardar
                resultado["copia"] = copia_de_seguranca(pasta_saves)
        resultado["config"] = escrever_config(caminho_executavel, cartao)
    except OSError as falha:
        resultado["erro"] = str(falha)
    return resultado
