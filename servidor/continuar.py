# -*- coding: utf-8 -*-
r"""Continuar de onde parou (pedido do Rafael, 10/11/2026: "para ser mais facil de voltar, mas revise muito bem os
saves").

Como funciona: ao fechar o jogo, o RetroArch grava sozinho um "ponto automatico" (savestate_auto_save), num arquivo
proprio (`<jogo>.state.auto`, ao lado dos estados do F2), que nao apaga nenhum dos 10 espacos do F2. Ao abrir o mesmo
jogo de novo, ele volta nesse ponto (savestate_auto_load).

O perigo, e a protecao: um estado salvo e' a memoria inteira do console naquele instante, inclusive o que o jogo
"acha" que tem no cartao de memoria ou na bateria do cartucho. Voltar num estado ANTIGO depois que o jogo gravou um
save mais novo faz o jogo trabalhar com a lista antiga do cartao; no proximo save, ele pode escrever por cima do save
novo (no PS2 isso estraga o cartao inteiro: e' a dica antiga dos foruns do PCSX2). Isso acontece quando:
  - o jogo fechou sem gravar o ponto (o Android matou o app, faltou luz): o save do cartao ficou mais novo;
  - o cartao e' um so para todos os jogos do console (PS2, Dreamcast, GameCube, PSP) e OUTRO jogo gravou nele.
Por isso o ARENA so manda voltar ao ponto automatico quando NENHUM save do jogo nem cartao do console foi gravado
depois dele (com uma folga: ao fechar, o RetroArch grava o ponto e logo depois a bateria do cartucho). Se algum for
mais novo, o jogo comeca normal, pelo save, e o ponto velho e' trocado pelo novo na saida.

Nunca no Jogar Junto: as duas maquinas precisam comecar do mesmo ponto.
Este modulo so decide; quem grava e carrega e' o RetroArch. Ele nao apaga nem muda nenhum arquivo.
"""
import os

# Ao fechar, o RetroArch grava o ponto automatico e, logo depois, a bateria do cartucho (.srm) e o cartao. Um save
# so conta como "mais novo" se for gravado mais de FOLGA segundos depois do ponto.
FOLGA_EM_SEGUNDOS = 30
# Teto de arquivos olhados por pasta de cartao (a pasta do Dolphin pode ser grande): o resto e' ignorado.
LIMITE_DE_ARQUIVOS = 5000
EXTENSAO_DO_PONTO = ".state.auto"

# Cartoes que o nucleo grava num lugar so, para todos os jogos do console, fora do nome do jogo.
# ("sistema" | "saves", subpasta). Os saves com o nome do jogo (o .srm do cartucho, o .bkr do Saturn, o .mcd do PS1
# por jogo) ja entram pela busca pelo nome, em qualquer console.
CARTOES_COMPARTILHADOS = {
    # O nucleo do PS2 (LRPS2) usa system\pcsx2\memcards; o PCSX2 de fora e a lista de cartoes, saves\memcards; o
    # Play! (o jeito livre), saves\Play!.
    "ps2": [("sistema", "pcsx2/memcards"), ("saves", "memcards"), ("saves", "Play!")],
    # O Flycast: os VMU de todos os jogos em system\dc (vmu_save_A1.bin...) e os VMU por jogo em saves\Flycast\reicast.
    "dreamcast": [("sistema", "dc"), ("saves", "Flycast/reicast"), ("saves", "DreamPotato")],
    "gamecube": [("sistema", "dolphin-emu/User/GC"), ("saves", "dolphin-emu/User/GC")],
    "wii": [("sistema", "dolphin-emu/User/Wii/title"), ("saves", "dolphin-emu/User/Wii/title")],
    "psp": [("saves", "PPSSPP/PSP/SAVEDATA"), ("sistema", "PPSSPP/PSP/SAVEDATA")],
}
# O PS1 (SwanStation com o cartao 1 no modo "Libretro") e o Saturn (o .bkr do Beetle) gravam com o nome do jogo:
# entram pela busca pelo nome, sem lista aqui.

DESLIGADO = {"savestate_auto_save": "false", "savestate_auto_load": "false"}


def nome_do_jogo(caminho_jogo):
    """O nome que o RetroArch da aos saves e estados: o do arquivo, sem a extensao (Contra (USA).nes -> Contra (USA))."""
    return os.path.splitext(os.path.basename(caminho_jogo or ""))[0]


def ponto_automatico(pasta_states, caminho_jogo):
    """O arquivo do ponto automatico deste jogo (states\\<Nucleo>\\<jogo>.state.auto) ou None. Se houver mais de um
    (o mesmo jogo aberto por dois nucleos), o mais novo."""
    alvo = nome_do_jogo(caminho_jogo) + EXTENSAO_DO_PONTO
    achados = []
    for pasta in [pasta_states] + _subpastas(pasta_states):
        caminho = os.path.join(pasta, alvo)
        if os.path.isfile(caminho):
            achados.append(caminho)
    return max(achados, key=os.path.getmtime) if achados else None


def save_mais_novo(caminho_jogo, plataforma, pasta_saves, pasta_sistema):
    """(hora, caminho) do save mais novo deste jogo: os arquivos com o nome do jogo em saves\\ e saves\\<Nucleo>\\,
    mais os cartoes compartilhados do console. None se nao houver nenhum."""
    nome = nome_do_jogo(caminho_jogo)
    mais_novo = None
    if nome:
        for pasta in [pasta_saves] + _subpastas(pasta_saves):
            try:
                arquivos = os.listdir(pasta)
            except OSError:
                continue
            for arquivo in arquivos:
                if _e_save_do_jogo(arquivo, nome):
                    mais_novo = _o_mais_novo(mais_novo, os.path.join(pasta, arquivo))
    raizes = {"saves": pasta_saves, "sistema": pasta_sistema}
    for raiz, subpasta in CARTOES_COMPARTILHADOS.get(plataforma or "", []):
        pasta = os.path.join(raizes[raiz], *subpasta.split("/"))
        vistos = 0
        for atual, _, arquivos in os.walk(pasta):
            for arquivo in arquivos:
                mais_novo = _o_mais_novo(mais_novo, os.path.join(atual, arquivo))
                vistos += 1
            if vistos >= LIMITE_DE_ARQUIVOS:
                break
    return mais_novo


def decidir(ligado, em_rede, plataforma, caminho_jogo, pasta_states, pasta_saves, pasta_sistema):
    """O que vai para o RetroArch nesta partida. Devolve {"opcoes": {...}, "volta": bool, "motivo": texto}.
    'volta' diz se o jogo volta ao ponto automatico; 'motivo' explica a escolha (vai para o registro)."""
    if not ligado:
        return {"opcoes": dict(DESLIGADO), "volta": False, "motivo": ""}
    if em_rede:
        return {"opcoes": dict(DESLIGADO), "volta": False,
                "motivo": "desligado no Jogar Junto (as duas maquinas comecam do mesmo ponto)"}
    opcoes = {"savestate_auto_save": "true", "savestate_auto_load": "false"}
    ponto = ponto_automatico(pasta_states, caminho_jogo)
    if not ponto:
        return {"opcoes": opcoes, "volta": False, "motivo": "primeira vez: o ponto automatico e' gravado ao sair"}
    save = save_mais_novo(caminho_jogo, plataforma, pasta_saves, pasta_sistema)
    try:
        hora_do_ponto = os.path.getmtime(ponto)
    except OSError:
        return {"opcoes": opcoes, "volta": False, "motivo": "não consegui ler o ponto automático"}
    if save and save[0] > hora_do_ponto + FOLGA_EM_SEGUNDOS:
        return {"opcoes": opcoes, "volta": False,
                "motivo": "o save %s e' mais novo que o ponto automatico: o jogo comeca pelo save (o ponto velho "
                          "e' trocado na saida)" % os.path.basename(save[1])}
    opcoes["savestate_auto_load"] = "true"
    return {"opcoes": opcoes, "volta": True, "motivo": "volta ao ponto automatico (%s)" % os.path.basename(ponto)}


def _subpastas(pasta):
    try:
        return [os.path.join(pasta, nome) for nome in sorted(os.listdir(pasta))
                if os.path.isdir(os.path.join(pasta, nome))]
    except OSError:
        return []


def _e_save_do_jogo(arquivo, nome):
    """Contra (USA).srm, Contra (USA).bkr, Crash_1.mcd... sim. Estados (.state, .state1, .auto, .png) nao: eles nao
    sao save do jogo."""
    if not arquivo.startswith(nome):
        return False
    resto = arquivo[len(nome):]
    if not resto or resto[0] not in "._":
        return False
    return ".state" not in resto.lower()


def _o_mais_novo(atual, caminho):
    try:
        hora = os.path.getmtime(caminho)
    except OSError:
        return atual
    return (hora, caminho) if atual is None or hora > atual[0] else atual
