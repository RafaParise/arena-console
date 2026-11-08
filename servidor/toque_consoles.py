# -*- coding: utf-8 -*-
r"""
ARENA - o controle de toque com a cara de cada console (Android).

Pedido do Rafael (07/11/2026): "os layouts e formas dos botoes e desenhos devem acompanhar os consoles, o GameCube por
exemplo [...] os botoes devem ter o mesmo formato e posicao como no controle, mas tambem deve ser possivel mexer na
posicao dos botoes e precisa ter os dois analogicos para os consoles que tinham o recurso, mas mesmo para os consoles
que nao tem deve ter o recurso ativo, pois no Dreamcast por exemplo nao tem o direito, mas depois alguns jogos foram
adaptados para esse recurso".

COMO FUNCIONA: cada desenho (DESENHOS) diz onde fica cada botao com o celular DEITADO (x e y de 0 a 1 na tela; o
tamanho em fracao da altura, para o redondo continuar redondo). O desenho EM PE sai do deitado (a_partir_do_deitado):
os controles vao para a metade de baixo, com o jogo em cima. O ARENA grava o .cfg de "overlay" do RetroArch a cada
jogo (gerar_cfg), com as posicoes que o aluno mudou na tela "Arrumar os botoes" por cima das de fabrica.

QUE BOTAO MANDA O QUE: o toque manda um botao do RetroPad (o controle padrao do RetroArch) e o nucleo o traduz para o
console. O mapa de cada nucleo foi LIDO dele mesmo (07/11/2026: o RetroArch registra o SET_INPUT_DESCRIPTORS ao abrir
um jogo; o do Dolphin, no codigo dele, Source/Core/DolphinLibretro/Input.cpp). Exemplos: no Mega Drive o A e' o "y",
o B e' o "b" e o C e' o "a"; no Nintendo 64 o A e' o "b", o B e' o "y" e os botoes C sao o analogico direito; no
GameCube o Z e' o "r" e os gatilhos L e R sao o "l2" e o "r2".

ANALOGICOS: "do_console" (os que o controle tinha), "dois" (os dois sempre, para os jogos adaptados) ou "nenhum".

So biblioteca padrao. As imagens (servidor\toque\consoles\*.png) saem de ferramentas\gerar_toque_consoles.py.
"""
import os

PASTA_DAS_IMAGENS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "toque", "consoles")
PASTA_DOS_BOTOES_DO_ARENA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "toque")
ASPECTO_DEITADO = 2.0          # largura / altura do desenho deitado (o RetroArch ajusta a tela de verdade: auto_scale)
ASPECTO_EM_PE = 0.5
ANALOGICOS = ("do_console", "dois", "nenhum")

# As imagens: nome -> (forma, cor, texto, cor do texto). Pedido do Rafael (07/11/2026, depois do primeiro desenho):
# "os icones de botoes do controle de cada console devem ter o mesmo desenho, formato e cor dos originais (...) p2 com
# triangulo, cruz azul, bola vermelha e quadrado rosa". Por isso cada botao tem o volume do de verdade (sombra, brilho
# e a letra gravada na cor do proprio botao), o direcional tem o formato de cada console (a cruz da Nintendo, o disco
# da Sega, as quatro setas soltas do PlayStation, a alavanca do fliperama) e os C do Nintendo 64 sao os quatro botoes
# amarelos. Formas: circulo, pilula, feijao_deitado, feijao_vertical (botoes); simbolo (PlayStation: botao preto com o
# simbolo colorido); base_redonda e base_octogono (onde o analogico anda); pino (a ponta do analogico); botoes_c (N64);
# dpad_cruz, dpad_sega, dpad_ps, dpad_alavanca (o fundo do direcional); marca e seta_ps (cada braco do direcional).
# Cor do texto vazia = a letra gravada (a cor do botao, mais escura).
CINZA, CINZA_CLARO, PRETO = "#5a5f66", "#9aa0a6", "#2b2d31"
IMAGENS = {
    # o direcional de cada console: o fundo (sem botao) e os quatro bracos (cada um manda a sua direcao)
    "dpad_cruz": ("dpad_cruz", "#2b2d31", "", ""),             # Nintendo: a cruz preta
    "dpad_cruz_cinza": ("dpad_cruz", "#6b6f78", "", ""),       # Nintendo 64 e Dreamcast
    "dpad_cruz_gc": ("dpad_cruz", "#a3a8b0", "", ""),          # GameCube: a cruz pequena cinza clara
    "dpad_sega": ("dpad_sega", "#2b2d31", "", ""),             # Mega Drive e Saturn: o disco com a cruz
    "dpad_ps": ("dpad_ps", "#1f2024", "", ""),                 # PlayStation e PSP: o buraco das quatro setas
    "dpad_alavanca": ("dpad_alavanca", "#d03a3a", "", ""),     # fliperama: a bola vermelha
    "dpad_alavanca_neo": ("dpad_alavanca", "#2b2d31", "", ""),  # Neo Geo: a bola preta
    "marca_cima": ("marca", "#ffffff", "cima", ""), "marca_baixo": ("marca", "#ffffff", "baixo", ""),
    "marca_esq": ("marca", "#ffffff", "esquerda", ""), "marca_dir": ("marca", "#ffffff", "direita", ""),
    "seta_ps_cima": ("seta_ps", "#3a3c42", "cima", ""), "seta_ps_baixo": ("seta_ps", "#3a3c42", "baixo", ""),
    "seta_ps_esq": ("seta_ps", "#3a3c42", "esquerda", ""), "seta_ps_dir": ("seta_ps", "#3a3c42", "direita", ""),
    # os analogicos
    "base_analogico": ("base_redonda", CINZA, "", ""), "pino": ("pino", CINZA_CLARO, "", ""),
    "base_ps": ("base_redonda", "#1f2024", "", ""), "pino_ps": ("pino", "#2b2d31", "", ""),
    "base_octogono": ("base_octogono", "#7d828a", "", ""),
    "pino_n64": ("pino", "#8c9098", "", ""), "pino_gc": ("pino", "#9aa0a6", "", ""),
    "pino_c": ("pino", "#f2c418", "C", ""),
    "base_dc": ("base_redonda", "#c9ccd1", "", ""), "pino_dc": ("pino", "#d9dce0", "", ""),
    "pino_psp": ("pino", "#b9bdc4", "", ""),
    "botoes_c": ("botoes_c", "#f2c418", "", ""),
    # start, select e os ombros
    "start": ("pilula", PRETO, "START", "#d9dce0"), "select": ("pilula", PRETO, "SELECT", "#d9dce0"),
    "start_cinza": ("pilula", "#8a8f99", "START", "#2b2d31"), "select_cinza": ("pilula", "#8a8f99", "SELECT", "#2b2d31"),
    "mode": ("pilula", PRETO, "MODE", "#d9dce0"), "coin": ("pilula", PRETO, "COIN", "#d9dce0"),
    "run": ("pilula", PRETO, "RUN", "#d9dce0"),
    "start_vermelho": ("circulo", "#d0242c", "START", "#ffd9d9"), "start_redondo": ("circulo", "#b9bdc4", "START", "#3a3c42"),
    "start_dc": ("circulo", "#c9ccd1", "START", "#3a3c42"),
    "l": ("pilula", "#7d828a", "L", "#ffffff"), "r": ("pilula", "#7d828a", "R", "#ffffff"),
    "l1": ("pilula", "#3a3c42", "L1", "#d9dce0"), "r1": ("pilula", "#3a3c42", "R1", "#d9dce0"),
    "l2": ("pilula", "#3a3c42", "L2", "#d9dce0"), "r2": ("pilula", "#3a3c42", "R2", "#d9dce0"),
    "l3": ("circulo", "#2b2d31", "L3", "#d9dce0"), "r3": ("circulo", "#2b2d31", "R3", "#d9dce0"),
    "z_n64": ("pilula", "#6b6f78", "Z", "#ffffff"), "z_gc": ("pilula", "#5246b8", "Z", "#ffffff"),
    # Super Nintendo (o colorido do Super Famicom e do Super Nintendo brasileiro)
    "snes_a": ("circulo", "#d0242c", "A", ""), "snes_b": ("circulo", "#f0c419", "B", ""),
    "snes_x": ("circulo", "#2a4fc8", "X", ""), "snes_y": ("circulo", "#239b48", "Y", ""),
    # NES (vermelho), Game Boy (vinho), Game Boy Advance (lilas), PC Engine (preto)
    "nes_a": ("circulo", "#c8202a", "A", ""), "nes_b": ("circulo", "#c8202a", "B", ""),
    "gb_a": ("circulo", "#9c2259", "A", ""), "gb_b": ("circulo", "#9c2259", "B", ""),
    "gba_a": ("circulo", "#b8b4cc", "A", ""), "gba_b": ("circulo", "#b8b4cc", "B", ""),
    "pce_1": ("circulo", PRETO, "I", "#c9ccd1"), "pce_2": ("circulo", PRETO, "II", "#c9ccd1"),
    # Nintendo 64: A azul grande, B verde
    "n64_a": ("circulo", "#2851c8", "A", ""), "n64_b": ("circulo", "#1d8a3a", "B", ""),
    # GameCube: A grande verde, B pequeno vermelho, X e Y em feijao cinza claro, gatilhos cinza
    "gc_a": ("circulo", "#1fa35b", "A", ""), "gc_b": ("circulo", "#d0242c", "B", ""),
    "gc_x": ("feijao_vertical", "#c4c8ce", "X", ""), "gc_y": ("feijao_deitado", "#c4c8ce", "Y", ""),
    "gc_l": ("pilula", "#9aa0a6", "L", "#ffffff"), "gc_r": ("pilula", "#9aa0a6", "R", "#ffffff"),
    # Mega Drive e Saturn (os pretos da Tec Toy) e o fliperama
    "md_a": ("circulo", PRETO, "A", "#9aa0a6"), "md_b": ("circulo", PRETO, "B", "#9aa0a6"),
    "md_c": ("circulo", PRETO, "C", "#9aa0a6"), "md_x": ("circulo", "#3a3c42", "X", "#9aa0a6"),
    "md_y": ("circulo", "#3a3c42", "Y", "#9aa0a6"), "md_z": ("circulo", "#3a3c42", "Z", "#9aa0a6"),
    "sat_a": ("circulo", "#3a3c42", "A", "#b9bdc4"), "sat_b": ("circulo", "#3a3c42", "B", "#b9bdc4"),
    "sat_c": ("circulo", "#3a3c42", "C", "#b9bdc4"), "sat_x": ("circulo", "#4a4d54", "X", "#b9bdc4"),
    "sat_y": ("circulo", "#4a4d54", "Y", "#b9bdc4"), "sat_z": ("circulo", "#4a4d54", "Z", "#b9bdc4"),
    "arc_1": ("circulo", "#d0242c", "1", ""), "arc_2": ("circulo", "#f0c419", "2", ""),
    "arc_3": ("circulo", "#239b48", "3", ""), "arc_4": ("circulo", "#2a4fc8", "4", ""),
    "arc_5": ("circulo", "#e07a1e", "5", ""), "arc_6": ("circulo", "#7a3fc2", "6", ""),
    # Neo Geo: A vermelho, B amarelo, C verde, D azul
    "neo_a": ("circulo", "#d0242c", "A", ""), "neo_b": ("circulo", "#f0c419", "B", ""),
    "neo_c": ("circulo", "#239b48", "C", ""), "neo_d": ("circulo", "#2a4fc8", "D", ""),
    # Dreamcast: A vermelho, B azul, X amarelo, Y verde
    "dc_a": ("circulo", "#d0242c", "A", ""), "dc_b": ("circulo", "#2a4fc8", "B", ""),
    "dc_x": ("circulo", "#f0c419", "X", ""), "dc_y": ("circulo", "#239b48", "Y", ""),
    # PlayStation: botao preto com o simbolo colorido (triangulo verde, bola vermelha, xis azul, quadrado rosa)
    "ps_triangulo": ("simbolo", "#3ec7a0", "triangulo", ""), "ps_circulo": ("simbolo", "#f0484e", "circulo", ""),
    "ps_x": ("simbolo", "#6f9be8", "x", ""), "ps_quadrado": ("simbolo", "#e77fc9", "quadrado", ""),
    # Nintendo DS: botoes cinza claro com a letra
    "nds_a": ("circulo", "#c4c8ce", "A", "#3a3c42"), "nds_b": ("circulo", "#c4c8ce", "B", "#3a3c42"),
    "nds_x": ("circulo", "#c4c8ce", "X", "#3a3c42"), "nds_y": ("circulo", "#c4c8ce", "Y", "#3a3c42"),
}

# O direcional de cada estilo: (o fundo, desenhado atras e sem botao; os bracos cima, baixo, esquerda, direita).
# O fundo vai de ponta a ponta (FUNDO_DO_DIRECIONAL bracos); cada braco e' um quadrado de 2 * MEIO_BRACO.
MEIO_BRACO = 0.55
FUNDO_DO_DIRECIONAL = 1.55
_MARCAS = ("marca_cima", "marca_baixo", "marca_esq", "marca_dir")
DIRECIONAIS = {
    "cruz": ("dpad_cruz", _MARCAS),
    "cruz_cinza": ("dpad_cruz_cinza", _MARCAS),
    "cruz_gc": ("dpad_cruz_gc", _MARCAS),
    "sega": ("dpad_sega", _MARCAS),
    "ps": ("dpad_ps", ("seta_ps_cima", "seta_ps_baixo", "seta_ps_esq", "seta_ps_dir")),
    "alavanca": ("dpad_alavanca", _MARCAS),
    "alavanca_neo": ("dpad_alavanca_neo", _MARCAS),
}


# ---------------------------------------------------------------------------
# Pecas (posicoes no desenho DEITADO; tamanhos em fracao da altura)
# ---------------------------------------------------------------------------

def botao(ident, comando, x, y, raio, imagem):
    return {"id": ident, "comando": comando, "x": x, "y": y, "forma": "radial", "rw": raio, "rh": raio, "imagem": imagem}


def pilula(ident, comando, x, y, largura, altura, imagem):
    return {"id": ident, "comando": comando, "x": x, "y": y, "forma": "rect", "rw": largura, "rh": altura,
            "imagem": imagem}


def direcional(x, y, braco=0.10, ident="direcional", estilo="cruz"):
    """O fundo com o formato do console (DIRECIONAIS), as quatro setas e as quatro diagonais. Mexe junto: um "id" so."""
    return {"id": ident, "grupo": "direcional", "x": x, "y": y, "braco": braco, "estilo": estilo}


def analogico(ident, comando, x, y, raio=0.12, pino="pino", base="base_analogico"):
    return {"id": ident, "comando": comando, "x": x, "y": y, "forma": "analogico", "rw": raio, "rh": raio,
            "imagem": base, "pino": pino}


def botoes_c(x, y, raio=0.10):
    """Os quatro botoes C amarelos do Nintendo 64. No Mupen64Plus-Next eles sao o analogico direito (C Buttons X/Y):
    a area manda o analogico direito todo para o lado do C tocado (sem o pino que anda). Nao some com "nenhum"."""
    return {"id": "botoes_c", "comando": "analog_right", "x": x, "y": y, "forma": "analogico", "rw": raio, "rh": raio,
            "imagem": "botoes_c", "pino": None, "fixo": True}


def losango(x, y, cima, direita, baixo, esquerda, raio=0.075, distancia=0.115):
    """Quatro botoes em cruz (Super Nintendo, PlayStation, Dreamcast...): (id, comando, imagem) de cada lado."""
    dx = distancia / ASPECTO_DEITADO
    return [botao(cima[0], cima[1], x, y - distancia, raio, cima[2]),
            botao(direita[0], direita[1], x + dx, y, raio, direita[2]),
            botao(baixo[0], baixo[1], x, y + distancia, raio, baixo[2]),
            botao(esquerda[0], esquerda[1], x - dx, y, raio, esquerda[2])]


def start_select(start="start", select="select", com_select=True, x=0.5, y=0.93):
    pecas = [pilula("start", "start", x + 0.06, y, 0.10, 0.045, start)]
    if com_select:
        pecas.append(pilula("select", "select", x - 0.06, y, 0.10, 0.045, select))
    return pecas


def ombros(l="l", r="r", l_img="l", r_img="r", y=0.25, largura=0.14, altura=0.065):
    return [pilula("l", l, 0.09, y, largura, altura, l_img), pilula("r", r, 0.91, y, largura, altura, r_img)]


# Onde entram os analogicos que o console nao tinha ("dois"): perto do meio, embaixo, sem cobrir os outros.
ANALOGICO_ESQ_EXTRA = (0.30, 0.80)
ANALOGICO_DIR_EXTRA = (0.70, 0.80)

DESENHOS = {
    "snes": {"nome": "Super Nintendo", "pecas": [
        direcional(0.13, 0.60, estilo="cruz"),
        *losango(0.87, 0.60, ("x", "x", "snes_x"), ("a", "a", "snes_a"), ("b", "b", "snes_b"), ("y", "y", "snes_y")),
        *ombros(), *start_select()]},
    "nes": {"nome": "NES", "pecas": [
        direcional(0.13, 0.62, estilo="cruz"),
        botao("b", "b", 0.80, 0.66, 0.08, "nes_b"), botao("a", "a", 0.915, 0.66, 0.08, "nes_a"),
        *start_select()]},
    "gameboy": {"nome": "Game Boy", "pecas": [
        direcional(0.13, 0.62, estilo="cruz"),
        botao("b", "b", 0.81, 0.70, 0.08, "gb_b"), botao("a", "a", 0.915, 0.57, 0.08, "gb_a"),
        *start_select(start="start_cinza", select="select_cinza")]},
    "gba": {"nome": "Game Boy Advance", "pecas": [
        direcional(0.13, 0.62, estilo="cruz"),
        botao("b", "b", 0.81, 0.70, 0.08, "gba_b"), botao("a", "a", 0.915, 0.57, 0.08, "gba_a"),
        *ombros(), *start_select()]},
    "pcengine": {"nome": "PC Engine", "pecas": [
        direcional(0.13, 0.62, estilo="cruz"),
        botao("ii", "b", 0.80, 0.66, 0.08, "pce_2"), botao("i", "a", 0.915, 0.66, 0.08, "pce_1"),
        *start_select(start="run")]},
    "n64": {"nome": "Nintendo 64", "analogicos": ("esq", "dir"), "pecas": [
        analogico("analogico_esq", "analog_left", 0.13, 0.55, pino="pino_n64", base="base_octogono"),
        direcional(0.10, 0.86, braco=0.06, estilo="cruz_cinza"),
        botao("a", "b", 0.85, 0.72, 0.085, "n64_a"), botao("b", "y", 0.765, 0.60, 0.07, "n64_b"),
        # os quatro botoes C amarelos: no Mupen64Plus-Next eles sao o analogico direito (C Buttons X/Y)
        botoes_c(0.925, 0.43, raio=0.10),
        *ombros(), pilula("z", "l2", 0.09, 0.37, 0.14, 0.065, "z_n64"),
        botao("start", "start", 0.50, 0.90, 0.055, "start_vermelho")]},
    "gamecube": {"nome": "GameCube", "analogicos": ("esq", "dir"), "pecas": [
        analogico("analogico_esq", "analog_left", 0.13, 0.52, pino="pino_gc", base="base_octogono"),
        direcional(0.10, 0.86, braco=0.055, estilo="cruz_gc"),
        botao("a", "a", 0.86, 0.62, 0.10, "gc_a"),
        botao("b", "b", 0.765, 0.76, 0.055, "gc_b"),
        pilula("x", "x", 0.945, 0.57, 0.055, 0.14, "gc_x"),
        pilula("y", "y", 0.85, 0.45, 0.12, 0.055, "gc_y"),
        analogico("analogico_dir", "analog_right", 0.80, 0.895, raio=0.075, pino="pino_c", base="base_octogono"),
        pilula("l", "l2", 0.09, 0.25, 0.14, 0.07, "gc_l"), pilula("r", "r2", 0.91, 0.22, 0.14, 0.07, "gc_r"),
        pilula("z", "r", 0.94, 0.335, 0.10, 0.05, "z_gc"),
        botao("start", "start", 0.50, 0.90, 0.05, "start_redondo")]},
    "megadrive": {"nome": "Mega Drive", "pecas": [
        direcional(0.13, 0.62, estilo="sega"),
        botao("a", "y", 0.735, 0.72, 0.072, "md_a"), botao("b", "b", 0.83, 0.70, 0.072, "md_b"),
        botao("c", "a", 0.925, 0.68, 0.072, "md_c"),
        botao("x", "l", 0.725, 0.53, 0.06, "md_x"), botao("y", "x", 0.815, 0.51, 0.06, "md_y"),
        botao("z", "r", 0.905, 0.49, 0.06, "md_z"),
        *start_select(select="mode")]},
    "saturn": {"nome": "Sega Saturn", "pecas": [
        direcional(0.13, 0.62, estilo="sega"),
        botao("a", "b", 0.735, 0.72, 0.072, "sat_a"), botao("b", "a", 0.83, 0.70, 0.072, "sat_b"),
        botao("c", "r", 0.925, 0.68, 0.072, "sat_c"),
        botao("x", "y", 0.725, 0.53, 0.06, "sat_x"), botao("y", "x", 0.815, 0.51, 0.06, "sat_y"),
        botao("z", "l", 0.905, 0.49, 0.06, "sat_z"),
        *ombros(l="l2", r="r2"), *start_select(com_select=False)]},
    "dreamcast": {"nome": "Dreamcast", "analogicos": ("esq",), "pecas": [
        analogico("analogico_esq", "analog_left", 0.13, 0.52, pino="pino_dc", base="base_dc"),
        direcional(0.10, 0.86, braco=0.06, estilo="cruz_cinza"),
        *losango(0.87, 0.60, ("y", "x", "dc_y"), ("b", "a", "dc_b"), ("a", "b", "dc_a"), ("x", "y", "dc_x")),
        *ombros(l="l2", r="r2"), botao("start", "start", 0.50, 0.90, 0.05, "start_dc")]},
    "playstation": {"nome": "PlayStation", "analogicos": ("esq", "dir"), "pecas": [
        direcional(0.12, 0.50, braco=0.075, estilo="ps"),
        *losango(0.88, 0.50, ("triangulo", "x", "ps_triangulo"), ("circulo", "a", "ps_circulo"),
                 ("xis", "b", "ps_x"), ("quadrado", "y", "ps_quadrado"), raio=0.07, distancia=0.105),
        analogico("analogico_esq", "analog_left", 0.30, 0.80, raio=0.11, pino="pino_ps", base="base_ps"),
        analogico("analogico_dir", "analog_right", 0.70, 0.80, raio=0.11, pino="pino_ps", base="base_ps"),
        botao("l3", "l3", 0.41, 0.70, 0.045, "l3"), botao("r3", "r3", 0.59, 0.70, 0.045, "r3"),
        pilula("l1", "l", 0.09, 0.26, 0.14, 0.06, "l1"), pilula("r1", "r", 0.91, 0.26, 0.14, 0.06, "r1"),
        pilula("l2", "l2", 0.09, 0.15, 0.14, 0.06, "l2"), pilula("r2", "r2", 0.91, 0.15, 0.14, 0.06, "r2"),
        *start_select(y=0.93)]},
    "psp": {"nome": "PSP", "analogicos": ("esq",), "pecas": [
        direcional(0.12, 0.52, braco=0.075, estilo="ps"),
        *losango(0.88, 0.55, ("triangulo", "x", "ps_triangulo"), ("circulo", "a", "ps_circulo"),
                 ("xis", "b", "ps_x"), ("quadrado", "y", "ps_quadrado"), raio=0.07, distancia=0.105),
        analogico("analogico_esq", "analog_left", 0.13, 0.86, raio=0.08, pino="pino_psp", base="base_ps"),
        *ombros(), *start_select()]},
    "neogeo": {"nome": "Neo Geo", "pecas": [
        direcional(0.13, 0.62, braco=0.11, estilo="alavanca_neo"),
        botao("a", "b", 0.71, 0.74, 0.07, "neo_a"), botao("b", "a", 0.795, 0.64, 0.07, "neo_b"),
        botao("c", "y", 0.88, 0.60, 0.07, "neo_c"), botao("d", "x", 0.955, 0.64, 0.07, "neo_d"),
        *start_select(select="coin")]},
    "fliperama": {"nome": "Fliperama", "pecas": [
        direcional(0.13, 0.62, braco=0.11, estilo="alavanca"),
        botao("1", "b", 0.725, 0.74, 0.07, "arc_1"), botao("2", "a", 0.82, 0.74, 0.07, "arc_2"),
        botao("3", "r", 0.915, 0.74, 0.07, "arc_3"),
        botao("4", "y", 0.74, 0.55, 0.07, "arc_4"), botao("5", "x", 0.835, 0.55, 0.07, "arc_5"),
        botao("6", "l", 0.93, 0.55, 0.07, "arc_6"),
        *start_select(select="coin")]},
    "nds": {"nome": "Nintendo DS", "pecas": [
        direcional(0.10, 0.62, estilo="cruz"),
        *losango(0.90, 0.60, ("x", "x", "nds_x"), ("a", "a", "nds_a"), ("b", "b", "nds_b"), ("y", "y", "nds_y"),
                 raio=0.065, distancia=0.10),
        *ombros(), *start_select()]},
}

# Console -> desenho. O que nao esta aqui segue com o controle de toque de sempre (neo-retropad).
DESENHO_DO_CONSOLE = {
    "snes": "snes", "nes": "nes", "gameboy": "gameboy", "gba": "gba", "pcengine": "pcengine", "pcfx": "pcengine",
    "n64": "n64", "gamecube": "gamecube", "megadrive": "megadrive", "sega32x": "megadrive", "segacd": "megadrive",
    "sg1000": "nes", "saturn": "saturn", "dreamcast": "dreamcast", "ps1": "playstation", "ps2": "playstation",
    "psp": "psp", "neogeo": "neogeo", "arcade": "fliperama", "nds": "nds", "ngp": "nes", "wonderswan": "gameboy",
    "virtualboy": "snes", "lynx": "nes",
}

# Os botoes do ARENA (menu, salvar, carregar, sair) no alto, no meio: os cantos ficam para L e R.
BOTOES_DO_ARENA = [
    # (comando, x deitado, y deitado, x em pe, y em pe, imagem)
    ("menu_toggle", 0.26, 0.075, 0.14, 0.47, "arena-menu.png"),
    ("save_state", 0.42, 0.075, 0.38, 0.47, "arena-salvar.png"),
    ("load_state", 0.58, 0.075, 0.62, 0.47, "arena-carregar.png"),
    ("exit_emulator", 0.74, 0.075, 0.86, 0.47, "arena-sair.png"),
]


def desenho_do_console(plataforma):
    return DESENHO_DO_CONSOLE.get(str(plataforma or ""))


# ---------------------------------------------------------------------------
# Deitado -> em pe
# ---------------------------------------------------------------------------

ENCOLHER_EM_PE = 0.70          # o tamanho das pecas em pe (a tela em pe e' mais estreita)
AFASTAR_EM_PE = 0.65           # a distancia de cada peca ate a borda dela, em pe


def a_partir_do_deitado(x, y):
    """A posicao em pe (0 a 1) de uma peca, a partir da deitada: o lado esquerdo continua preso a borda esquerda, o
    direito a direita, o meio no meio, e tudo desce para a metade de baixo da tela (o jogo fica em cima)."""
    unidades = x * ASPECTO_DEITADO                      # de 0 a 2 alturas da tela deitada
    if x < 0.4:
        px = unidades * AFASTAR_EM_PE
    elif x > 0.6:
        px = 1 - (ASPECTO_DEITADO - unidades) * AFASTAR_EM_PE
    else:
        px = 0.5 + (unidades - 1) * 1.6                 # o meio (start, select): perto do centro, sem amontoar
    py = (0.97 + y * 1.0) / 2                           # a tela em pe tem 2 larguras de altura
    return round(min(max(px, 0.02), 0.98), 4), round(min(max(py, 0.5), 0.98), 4)


def posicoes_de_fabrica(nome, analogicos="do_console"):
    """{"deitado": {id: [x, y]}, "em_pe": {id: [x, y]}} das pecas do desenho (o que a tela de arrumar mostra)."""
    saida = {"deitado": {}, "em_pe": {}}
    for peca in pecas_do_desenho(nome, analogicos):
        saida["deitado"][peca["id"]] = [peca["x"], peca["y"]]
        saida["em_pe"][peca["id"]] = list(a_partir_do_deitado(peca["x"], peca["y"]))
    return saida


def pecas_do_desenho(nome, analogicos="do_console"):
    """As pecas do desenho com os analogicos pedidos: os do console, os dois sempre ou nenhum."""
    desenho = DESENHOS[nome]
    pecas = [dict(p) for p in desenho["pecas"]]
    if analogicos == "nenhum":
        return [p for p in pecas if p.get("forma") != "analogico" or p.get("fixo")]
    if analogicos == "dois":
        ids = {p["id"] for p in pecas}
        if "analogico_esq" not in ids:
            pecas.append(analogico("analogico_esq", "analog_left", *ANALOGICO_ESQ_EXTRA, raio=0.10))
        if "analogico_dir" not in ids:
            pecas.append(analogico("analogico_dir", "analog_right", *ANALOGICO_DIR_EXTRA, raio=0.10))
    return pecas


def resumo_para_a_tela(analogicos="do_console"):
    """O que a tela "Arrumar os botoes" precisa: cada desenho com as pecas (id, rotulo, forma, tamanho, cor) e as
    posicoes de fabrica deitado e em pe."""
    saida = {}
    for nome, desenho in DESENHOS.items():
        pecas = []
        do_console = {p["id"] for p in pecas_do_desenho(nome, "do_console")}
        for peca in pecas_do_desenho(nome, analogicos):
            if peca.get("grupo") == "direcional":
                fundo = DIRECIONAIS[peca.get("estilo", "cruz")][0]
                pecas.append({"id": peca["id"], "rotulo": "✚", "forma": "direcional",
                              "rw": peca["braco"] * FUNDO_DO_DIRECIONAL, "rh": peca["braco"] * FUNDO_DO_DIRECIONAL,
                              "cor": CINZA, "extra": False, "imagem": fundo + "_tela.png"})
                continue
            imagem = IMAGENS.get(peca["imagem"], ("circulo", CINZA, "", ""))
            rotulo = imagem[2] if imagem[0] not in ("simbolo", "seta", "base") else \
                {"triangulo": "△", "circulo": "○", "x": "✕", "quadrado": "□"}.get(imagem[2], "")
            if peca.get("forma") == "analogico":
                rotulo = "C" if peca.get("pino") in ("pino_c", None) else ("L" if peca["comando"] == "analog_left" else "R")
            item = {"id": peca["id"], "rotulo": rotulo, "forma": peca["forma"], "rw": peca["rw"], "rh": peca["rh"],
                    "cor": imagem[1], "extra": peca["id"] not in do_console, "imagem": peca["imagem"] + ".png"}
            if peca.get("pino"):
                item["pino"] = peca["pino"] + ".png"
            pecas.append(item)
        saida[nome] = {"nome": desenho["nome"], "pecas": pecas, "fabrica": posicoes_de_fabrica(nome, analogicos)}
    return saida


# ---------------------------------------------------------------------------
# O .cfg do RetroArch
# ---------------------------------------------------------------------------

def _tamanho(peca, em_pe, escala):
    """(metade da largura, metade da altura) normalizadas na tela."""
    rw, rh = peca["rw"] * escala, peca["rh"] * escala
    if em_pe:
        return rw * ENCOLHER_EM_PE, rh * ENCOLHER_EM_PE * ASPECTO_EM_PE
    return rw / ASPECTO_DEITADO, rh


def _linhas_da_peca(o, n, peca, x, y, em_pe, escala):
    """As linhas desc de uma peca no overlay 'o', a partir do numero 'n'. Devolve (linhas, quantas descs)."""
    linhas = []
    if peca.get("grupo") == "direcional":
        braco = peca["braco"] * escala
        fx = (ENCOLHER_EM_PE if em_pe else 1 / ASPECTO_DEITADO)
        fy = (ENCOLHER_EM_PE * ASPECTO_EM_PE if em_pe else 1.0)
        dx, dy = braco * fx, braco * fy
        meio_w, meio_h = braco * MEIO_BRACO * fx, braco * MEIO_BRACO * fy
        fundo, bracos = DIRECIONAIS[peca.get("estilo", "cruz")]
        # o fundo (a cruz, o disco...) vem primeiro, para ficar atras; "nul" = so a imagem, nao manda botao
        linhas.append('overlay%d_desc%d = "nul,%.5f,%.5f,rect,%.5f,%.5f"' % (o, n, x, y, braco * FUNDO_DO_DIRECIONAL * fx,
                                                                            braco * FUNDO_DO_DIRECIONAL * fy))
        linhas.append('overlay%d_desc%d_overlay = "img/%s.png"' % (o, n, fundo))
        n += 1
        setas = [("up", x, y - dy, bracos[0]), ("down", x, y + dy, bracos[1]),
                 ("left", x - dx, y, bracos[2]), ("right", x + dx, y, bracos[3])]
        for comando, sx, sy, imagem in setas:
            linhas.append('overlay%d_desc%d = "%s,%.5f,%.5f,rect,%.5f,%.5f"' % (o, n, comando, sx, sy, meio_w, meio_h))
            linhas.append('overlay%d_desc%d_overlay = "img/%s.png"' % (o, n, imagem))
            n += 1
        for comando, sx, sy in (("up|left", x - dx, y - dy), ("up|right", x + dx, y - dy),
                                ("down|left", x - dx, y + dy), ("down|right", x + dx, y + dy)):
            linhas.append('overlay%d_desc%d = "%s,%.5f,%.5f,rect,%.5f,%.5f"' % (o, n, comando, sx, sy, meio_w, meio_h))
            n += 1
        return linhas, 9
    w, h = _tamanho(peca, em_pe, escala)
    if peca.get("forma") == "analogico":
        linhas.append('overlay%d_desc%d = "%s,%.5f,%.5f,radial,%.5f,%.5f"' % (o, n, peca["comando"], x, y, w, h))
        linhas.append('overlay%d_desc%d_overlay = "img/%s.png"' % (o, n, peca.get("imagem") or "base_analogico"))
        linhas.append("overlay%d_desc%d_saturate_pct = 1000000.0" % (o, n))
        n += 1
        if not peca.get("pino"):                     # os botoes C: a area inteira, sem o pino que anda
            return linhas, 1
        linhas.append('overlay%d_desc%d = "%s,%.5f,%.5f,radial,%.5f,%.5f"' % (o, n, peca["comando"], x, y,
                                                                              w * 0.55, h * 0.55))
        linhas.append('overlay%d_desc%d_overlay = "img/%s.png"' % (o, n, peca.get("pino", "pino")))
        linhas.append("overlay%d_desc%d_movable = true" % (o, n))
        linhas.append("overlay%d_desc%d_reach_x = 1.75" % (o, n))
        linhas.append("overlay%d_desc%d_reach_y = 1.75" % (o, n))
        return linhas, 2
    linhas.append('overlay%d_desc%d = "%s,%.5f,%.5f,%s,%.5f,%.5f"' % (o, n, peca["comando"], x, y,
                                                                      "rect" if peca["forma"] == "rect" else "radial",
                                                                      w, h))
    linhas.append('overlay%d_desc%d_overlay = "img/%s.png"' % (o, n, peca["imagem"]))
    return linhas, 1


def _numero(valor, padrao, minimo, maximo):
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return padrao
    return min(max(numero, minimo), maximo) if numero == numero else padrao


def gerar_cfg(nome, ajustes=None, botoes_do_arena=True):
    """O texto do .cfg de overlay do desenho 'nome', com os ajustes do aluno:
    {"analogicos": "do_console"|"dois"|"nenhum", "tamanho": 0.7..1.4, "deitado": {id: [x, y]}, "em_pe": {...}}."""
    ajustes = ajustes if isinstance(ajustes, dict) else {}
    analogicos = ajustes.get("analogicos") if ajustes.get("analogicos") in ANALOGICOS else "do_console"
    escala = _numero(ajustes.get("tamanho"), 1.0, 0.6, 1.5)
    pecas = pecas_do_desenho(nome, analogicos)
    saida = ["# Gerado pelo ARENA (servidor/toque_consoles.py): o controle de toque do %s." % DESENHOS[nome]["nome"],
             "overlays = 2"]
    for o, (rotulo, em_pe) in enumerate((("landscape", False), ("portrait", True))):
        chave = "em_pe" if em_pe else "deitado"
        mudadas = ajustes.get(chave) if isinstance(ajustes.get(chave), dict) else {}
        linhas, n = [], 0
        for peca in pecas:
            if em_pe:
                x, y = a_partir_do_deitado(peca["x"], peca["y"])
            else:
                x, y = peca["x"], peca["y"]
            posicao = mudadas.get(peca["id"])
            if isinstance(posicao, (list, tuple)) and len(posicao) == 2:
                x, y = _numero(posicao[0], x, 0.0, 1.0), _numero(posicao[1], y, 0.0, 1.0)
            novas, quantas = _linhas_da_peca(o, n, peca, x, y, em_pe, escala)
            linhas += novas
            n += quantas
        # O RetroArch so troca sozinho para o desenho da outra orientacao (input_overlay_auto_rotate) se algum botao
        # apontar para ele (next_target): sem isto, o celular em pe mostrava o desenho deitado, encolhido no meio
        # (visto no A12 em 07/11/2026). O RetroArch so le o next_target de um botao "overlay_next" (task_overlay.c):
        # ele fica FORA da tela (posicao negativa, que o RetroArch aceita), onde nenhum dedo alcanca.
        linhas.append('overlay%d_desc%d = "overlay_next,-1.00000,-1.00000,rect,0.00500,0.00500"' % (o, n))
        linhas.append('overlay%d_desc%d_next_target = "%s"' % (o, n, "landscape" if em_pe else "portrait"))
        n += 1
        if botoes_do_arena:
            for comando, xd, yd, xp, yp, imagem in BOTOES_DO_ARENA:
                x, y = (xp, yp) if em_pe else (xd, yd)
                w, h = (0.11, 0.022) if em_pe else (0.065, 0.05)
                linhas.append('overlay%d_desc%d = "%s,%.5f,%.5f,rect,%.5f,%.5f"' % (o, n, comando, x, y, w, h))
                linhas.append('overlay%d_desc%d_overlay = "img/%s"' % (o, n, imagem))
                n += 1
        saida += ["", 'overlay%d_name = "%s"' % (o, rotulo), "overlay%d_full_screen = true" % o,
                  "overlay%d_normalized = true" % o,
                  "overlay%d_aspect_ratio = %.4f" % (o, ASPECTO_EM_PE if em_pe else ASPECTO_DEITADO),
                  "overlay%d_range_mod = 1.5" % o, "overlay%d_alpha_mod = 2.0" % o, "overlay%d_descs = %d" % (o, n)]
        saida += linhas
    return "\n".join(saida) + "\n"


def imagens_usadas(nome, analogicos="dois"):
    """Os nomes de arquivo das imagens que o desenho usa (para copiar ao lado do .cfg)."""
    usadas = set()
    for peca in pecas_do_desenho(nome, analogicos):
        if peca.get("grupo") == "direcional":
            fundo, bracos = DIRECIONAIS[peca.get("estilo", "cruz")]
            usadas.update(i + ".png" for i in (fundo,) + tuple(bracos))
        if peca.get("imagem"):
            usadas.add(peca["imagem"] + ".png")
        if peca.get("pino"):
            usadas.add(peca["pino"] + ".png")
    return sorted(usadas)


def gravar_controle(nome, pasta_retroarch, ajustes=None):
    """Grava overlays/arena/<nome>.cfg (com as imagens em overlays/arena/img) e devolve o caminho, ou None se nao
    deu (o jogo segue com o controle de toque de sempre)."""
    if nome not in DESENHOS:
        return None
    pasta = os.path.join(pasta_retroarch, "overlays", "arena")
    img = os.path.join(pasta, "img")
    try:
        os.makedirs(img, exist_ok=True)
        copiar = [(os.path.join(PASTA_DAS_IMAGENS, n), os.path.join(img, n)) for n in imagens_usadas(nome)]
        copiar += [(os.path.join(PASTA_DOS_BOTOES_DO_ARENA, b[5]), os.path.join(img, b[5])) for b in BOTOES_DO_ARENA]
        for origem, destino in copiar:
            with open(origem, "rb") as arquivo:
                dados = arquivo.read()
            try:
                with open(destino, "rb") as arquivo:
                    igual = arquivo.read() == dados
            except OSError:
                igual = False
            if not igual:                    # imagem nova do ARENA (o desenho mudou): troca a velha
                with open(destino, "wb") as arquivo:
                    arquivo.write(dados)
        destino = os.path.join(pasta, nome + ".cfg")
        temporario = destino + ".%d.tmp" % os.getpid()
        with open(temporario, "w", encoding="utf-8", newline="\n") as arquivo:
            arquivo.write(gerar_cfg(nome, ajustes))
        os.replace(temporario, destino)
        return destino
    except OSError:
        return None


def limpar_ajustes(dados):
    """Os ajustes vindos da tela, so com o que vale: {desenho: {analogicos, tamanho, deitado, em_pe}}."""
    saida = {}
    if not isinstance(dados, dict):
        return saida
    for nome, ajuste in dados.items():
        if nome not in DESENHOS or not isinstance(ajuste, dict):
            continue
        ids = {p["id"] for p in pecas_do_desenho(nome, "dois")}
        limpo = {}
        if ajuste.get("analogicos") in ANALOGICOS:
            limpo["analogicos"] = ajuste["analogicos"]
        if "tamanho" in ajuste:
            limpo["tamanho"] = round(_numero(ajuste.get("tamanho"), 1.0, 0.6, 1.5), 2)
        for chave in ("deitado", "em_pe"):
            posicoes = ajuste.get(chave)
            if not isinstance(posicoes, dict):
                continue
            boas = {}
            for ident, par in posicoes.items():
                if ident in ids and isinstance(par, (list, tuple)) and len(par) == 2:
                    x, y = _numero(par[0], None, 0.0, 1.0), _numero(par[1], None, 0.0, 1.0)
                    if x is not None and y is not None:
                        boas[ident] = [round(x, 4), round(y, 4)]
            if boas:
                limpo[chave] = boas
        if limpo:
            saida[nome] = limpo
    return saida
