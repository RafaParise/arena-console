# -*- coding: utf-8 -*-
"""
ARENA - Mapear teclas e botoes
===============================
Deixa o aluno dizer, com as palavras do console dele, qual tecla ou botao
faz cada coisa: "o X do PlayStation e a tecla Z", "o B do Nintendo e o
botao 1 do meu controle".

Como isso chega ao emulador: o RetroArch guarda o mapeamento em chaves
como 'input_player1_a'. O nome delas vem do Super Nintendo, entao 'a' num
jogo de PlayStation e o Circulo. A tela do ARENA traduz; este modulo
escreve.

Regra importante: o TECLADO e' o primeiro jogador sem controle (3
controles ligados -> teclado no jogador 4; nenhum -> jogador 1), com as
teclas padrao do RetroArch e o que o aluno mudou por cima.
BOTAO DE CONTROLE que o aluno nao definiu vai como "nul",
e ai o reconhecimento automatico do RetroArch decide. Sem isso, numeros
velhos esquecidos no retroarch.cfg (de outro tipo de controle) passavam
por cima: o Start virava o R3.

So biblioteca padrao.
"""

import json
import os
import threading

import plataforma

PASTA_SERVIDOR = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(PASTA_SERVIDOR)
PASTA_DADOS = os.path.join(RAIZ, "dados")
ARQUIVO = os.path.join(PASTA_DADOS, "controles.json")
ARQUIVO_PERFIS = os.path.join(PASTA_SERVIDOR, "perfis_controle.json")

_TRAVA = threading.Lock()

# Ate 8 jogadores com botoes proprios na tela (pedido do Rafael, 14/10/2026:
# o PS1 com o adaptador nas duas portas chega a 8).
JOGADORES = ("1", "2", "3", "4", "5", "6", "7", "8")

# Quantos jogadores tem os botoes de controle zerados em toda partida (o
# Saturn com dois adaptadores chega a 10; o RetroArch aceita ate 16).
JOGADORES_NO_CONTROLE = 16

# Botoes que o RetroArch conhece, na ordem em que ficam bonitos na tela.
BOTOES = ["up", "down", "left", "right",
          "b", "a", "y", "x", "l", "r", "l2", "r2", "l3", "r3",
          "start", "select"]

# Teclas que o RetroArch aceita. Fora desta lista, nao grava.
TECLAS = set(
    list("abcdefghijklmnopqrstuvwxyz0123456789") +
    ["up", "down", "left", "right", "enter", "kp_enter", "space", "tab",
     "backspace", "escape", "shift", "rshift", "ctrl", "rctrl", "alt",
     "ralt", "insert", "del", "home", "end", "pageup", "pagedown",
     "comma", "period", "semicolon", "quote", "slash", "backslash",
     "minus", "equals", "leftbracket", "rightbracket", "backquote"] +
    ["f%d" % n for n in range(1, 13)] +
    ["num%d" % n for n in range(0, 10)] +
    ["keypad%d" % n for n in range(0, 10)]
)

TIPOS = ("teclado", "botao", "eixo", "hat")

# Direcoes validas do direcional quando ele e um "chapeu" (hat switch).
DIRECOES_HAT = ("up", "down", "left", "right")

# Como cada tipo vira chave do RetroArch.
#   teclado -> input_player1_a          = "x"
#   botao   -> input_player1_a_btn      = "0"
#   eixo    -> input_player1_left_axis  = "-0"   (direcional analogico)
#   hat     -> input_player1_up_btn      = "h0up"
#
# O direcional do Xbox e da maioria dos controles modernos NAO e um botao
# comum. Ele e um "chapeu": um controle de quatro posicoes que o driver
# reporta como h0up, h0down, h0left, h0right. Escrever "12" ali faz o
# RetroArch procurar um botao 12 que nao existe, e o direcional fica mudo.
SUFIXO = {"teclado": "", "botao": "_btn", "eixo": "_axis", "hat": "_btn"}


# ---------------------------------------------------------------------------
# Perfis: o controle que voce tem x o console que voce vai jogar
# ---------------------------------------------------------------------------

_perfis = {"dados": None}


def carregar_perfis():
    if _perfis["dados"] is None:
        try:
            with open(ARQUIVO_PERFIS, "r", encoding="utf-8") as arquivo:
                _perfis["dados"] = json.load(arquivo)
        except (OSError, ValueError) as falha:
            print("[ARENA] perfis_controle.json ilegivel (%s)." % falha)
            _perfis["dados"] = {"tipos": {}, "consoles": {}}
    return _perfis["dados"]


def tipos_de_controle():
    """Lista os controles que o aluno pode ter, para escolher na tela."""
    dados = carregar_perfis()
    saida = []
    for identificacao, tipo in dados.get("tipos", {}).items():
        saida.append({
            "id": identificacao,
            "nome": tipo["nome"],
            "botoes": tipo.get("botoes", 0),
            "analogicos": tipo.get("analogicos", 0),
            "direcional": tipo.get("direcional", True),
            "vibracao": tipo.get("vibracao", False),
            "paletas": tipo.get("paletas", 0),
            "nota": tipo.get("_nota", ""),
        })
    return sorted(saida, key=lambda t: t["nome"])


def perfil_do_console(console_id):
    """O que aquele console entende de controle."""
    dados = carregar_perfis()
    return dict(dados.get("consoles", {}).get(
        console_id, dados.get("_padrao_console", {})))


def montar_perfil(tipo_id, console_id, usar_direcional=True,
                  usar_analogico_esq=True, usar_analogico_dir=True,
                  vibracao=True):
    """Cruza o controle com o console e devolve a lista do que faz sentido.

    So aparece o que existe dos DOIS lados. Nao adianta oferecer o
    analogico direito num jogo de NES, nem prometer vibracao num controle
    generico que nao vibra.
    """
    dados = carregar_perfis()
    tipo = dados.get("tipos", {}).get(tipo_id)
    console = perfil_do_console(console_id)
    if not tipo:
        return None, "Escolha o tipo de controle na lista."

    rotulos = tipo.get("rotulos", {})
    botoes_do_console = console.get("botoes", [])

    # Direcional: so se os dois tiverem, e so se estiver ligado.
    tem_direcional = (tipo.get("direcional") and console.get("direcional")
                      and usar_direcional)

    # Analogicos: limitado pelo menor dos dois.
    quantos_analogicos = min(tipo.get("analogicos", 0),
                             console.get("analogicos", 0))
    esquerdo = quantos_analogicos >= 1 and usar_analogico_esq
    direito = quantos_analogicos >= 2 and usar_analogico_dir

    linhas = []
    for botao in botoes_do_console:
        numero = NUMERO_NO_NAVEGADOR.get(botao)
        linhas.append({
            "botao": botao,
            "no_controle": rotulos.get(numero, "botao %s" % numero)
                           if numero else "",
            "numero": numero,
        })

    if tem_direcional:
        for botao in ("up", "down", "left", "right"):
            numero = NUMERO_NO_NAVEGADOR.get(botao)
            linhas.append({
                "botao": botao,
                "no_controle": rotulos.get(numero, "direcional"),
                "numero": numero,
            })

    return {
        "tipo": tipo["nome"],
        "console": console_id,
        "direcional": tem_direcional,
        "direcional_possivel": bool(tipo.get("direcional")
                                    and console.get("direcional")),
        "analogico_esquerdo": esquerdo,
        "analogico_direito": direito,
        "analogicos_possiveis": quantos_analogicos,
        "vibracao": bool(tipo.get("vibracao") and console.get("vibracao")
                         and vibracao),
        "vibracao_possivel": bool(tipo.get("vibracao")
                                  and console.get("vibracao")),
        "paletas": tipo.get("paletas", 0),
        "aceita_mouse": bool(console.get("mouse")),
        "aceita_teclado": bool(console.get("teclado")),
        "nota_controle": tipo.get("_nota", ""),
        "nota_console": console.get("_nota", ""),
        "linhas": linhas,
    }, None


def opcoes_do_console(console_id, jogadores=2, usar_analogico=True,
                      vibracao=True, dispositivo_extra=None):
    """Diz ao emulador o que cada jogador esta usando.

    'dispositivo_extra' troca o jogador 2 por mouse ou teclado nos consoles
    que aceitavam - PlayStation 2, Dreamcast, MSX, ScummVM.
    """
    console = perfil_do_console(console_id)
    opcoes = {}

    codigo = console.get("dispositivo", 1)
    if not usar_analogico and console.get("dispositivo_sem_analogico"):
        codigo = console["dispositivo_sem_analogico"]

    for jogador in range(1, max(1, min(jogadores, 4)) + 1):
        opcoes["input_libretro_device_p%d" % jogador] = str(codigo)
        opcoes["input_player%d_analog_dpad_mode" % jogador] = (
            "1" if usar_analogico else "0")

    if dispositivo_extra == "mouse" and console.get("mouse"):
        opcoes["input_libretro_device_p2"] = str(console["mouse"])
    elif dispositivo_extra == "teclado" and console.get("teclado"):
        opcoes["input_libretro_device_p2"] = str(console["teclado"])

    opcoes["input_rumble_gain"] = "100" if (
        vibracao and console.get("vibracao")) else "0"

    return opcoes


# ---------------------------------------------------------------------------
# Guardar e ler
# ---------------------------------------------------------------------------

def _vazio():
    return {jogador: {} for jogador in JOGADORES}


def ler():
    """Le o mapeamento salvo. Nunca estoura: se o arquivo quebrar, comeca do zero."""
    try:
        with open(ARQUIVO, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except (OSError, ValueError):
        return _vazio()
    if not isinstance(dados, dict):
        return _vazio()      # [] ou "texto" no lugar de {...}

    limpo = _vazio()
    for jogador in JOGADORES:
        atribuicoes = dados.get(jogador)
        if not isinstance(atribuicoes, dict):
            continue
        for botao, valor in atribuicoes.items():
            if botao not in BOTOES or not isinstance(valor, dict):
                continue
            if valor.get("tipo") not in TIPOS:
                continue
            limpo[jogador][botao] = {"tipo": valor["tipo"],
                                     "valor": str(valor.get("valor", ""))[:16]}
    return limpo


def _gravar(dados):
    os.makedirs(PASTA_DADOS, exist_ok=True)
    temporario = "%s.%d.tmp" % (ARQUIVO, threading.get_ident())
    with _TRAVA:
        try:
            with open(temporario, "w", encoding="utf-8") as arquivo:
                json.dump(dados, arquivo, ensure_ascii=False, indent=1)
                arquivo.flush()
                os.fsync(arquivo.fileno())
            os.replace(temporario, ARQUIVO)
        finally:
            if os.path.exists(temporario):
                try:
                    os.remove(temporario)
                except OSError:
                    pass


def validar(tipo, valor):
    """Confere se dá para gravar aquilo. Devolve (valor limpo, erro)."""
    valor = str(valor or "").strip().lower()

    if tipo == "teclado":
        if valor not in TECLAS:
            return None, ("O RetroArch não conhece a tecla '%s'. Escolha outra tecla." % valor)
        return valor, None

    if tipo == "botao":
        if not valor.isdigit() or not 0 <= int(valor) <= 31:
            return None, "Número de botão inválido. Use de 0 a 31."
        return str(int(valor)), None

    if tipo == "hat":
        if valor.startswith("h") and valor[1:2].isdigit():
            return valor, None          # ja veio pronto: h0up
        if valor in DIRECOES_HAT:
            return "h0" + valor, None
        return None, "Direção do direcional que o ARENA não conhece: aperte a direção de novo."

    if tipo == "eixo":
        # Formato do RetroArch: sinal e o numero do eixo, tipo '-0' ou '+1'.
        if len(valor) < 2 or valor[0] not in "+-" or not valor[1:].isdigit():
            return None, "Eixo inválido. Use algo como -0 ou +1."
        if not 0 <= int(valor[1:]) <= 15:
            return None, "Número de eixo inválido. Use de 0 a 15."
        return valor, None

    return None, "Comando que o ARENA não conhece: clique em Definir e aperte de novo."


def definir(jogador, botao, tipo, valor):
    """Guarda uma atribuicao. Com tipo vazio, apaga."""
    if jogador not in JOGADORES:
        return None, "Escolha o jogador na lista (de 1 a 5)."
    if botao not in BOTOES:
        return None, "Botão que o ARENA não conhece: escolha o botão na lista."

    dados = ler()

    if not tipo:
        dados[jogador].pop(botao, None)
        _gravar(dados)
        return dados, None

    limpo, erro = validar(tipo, valor)
    if erro:
        return None, erro

    dados[jogador][botao] = {"tipo": tipo, "valor": limpo}
    _gravar(dados)
    return dados, None


def limpar(jogador=None):
    """Apaga o mapeamento de um jogador, ou de todos."""
    dados = ler()
    for chave in ([jogador] if jogador in JOGADORES else JOGADORES):
        dados[chave] = {}
    _gravar(dados)
    return dados


# ---------------------------------------------------------------------------
# Virar configuracao do RetroArch
# ---------------------------------------------------------------------------

# Teclado padrao do RetroArch para o jogador 1 (o mesmo do retroarch.cfg de
# fabrica). Fica aqui, fixo, porque o RetroArch reescreve o retroarch.cfg ao
# fechar com o que veio da partida: se o teclado foi para o jogador 4 numa
# partida, o retroarch.cfg passaria a dizer "jogador 1 sem teclado".
TECLADO_PADRAO = {
    "up": "up", "down": "down", "left": "left", "right": "right",
    "a": "x", "b": "z", "x": "s", "y": "a", "l": "q", "r": "w",
    "start": "enter", "select": "rshift",
}

# As direcoes do teclado movem tambem o analogico esquerdo (pedido do
# Rafael, 14/10/2026: sem controle, o Diddy Kong Racing, do N64, nao andava
# pelas setas -- o jogo so le o analogico). Em console sem analogico o
# nucleo nem pergunta pelo eixo, entao nada muda. Cima e' o eixo Y negativo.
ANALOGICO_DO_TECLADO = (("l_y_minus", "up"), ("l_y_plus", "down"),
                        ("l_x_minus", "left"), ("l_x_plus", "right"))


# Uma contagem por vez. Raw Input e XInput aguentam chamadas juntas, mas a
# contagem antiga (joyGetPosEx) era a principal suspeita das quedas do
# servidor de 26/09/2026 -- chamada por varios pedidos ao mesmo tempo, com
# controle sem fio ligando e desligando. Fila de um custa nada.
_TRAVA_CONTAGEM = threading.Lock()


def contar_controles():
    """Quantos controles de jogo estao ligados agora, de qualquer tipo.

    Controle XInput (Xbox, GameSir e parecidos) pelo proprio XInput; os
    outros (PlayStation, fliperama, generico) pela lista de dispositivos do
    Windows (Raw Input), sem contar duas vezes os XInput -- o nome deles
    tem "IG_", o jeito que a Microsoft documenta para separar os dois. Sem
    administrador. Fora do Windows, ou se der erro, responde 0.

    Achado de 02/10/2026 (teste de longa duracao): a versao anterior usava o
    joyGetPosEx do winmm, 16 vezes por contagem -- e ele DEIXA ALCAS DO
    WINDOWS ABERTAS quando o controle esta desligado (24 por contagem;
    181.570 em 3 minutos de pedidos). Raw Input nao abre nada.

    No Android (item 14), quem conta e' o app, pelo proprio Android."""
    if plataforma.ANDROID:
        import ponte_android
        return ponte_android.controles()
    try:
        with _TRAVA_CONTAGEM:
            return controles_sem_xinput() + len(controles_xinput())
    except (AttributeError, OSError, ValueError):
        return 0


def controles_sem_xinput():
    """Controles de jogo HID (joystick ou gamepad) que NAO sao XInput."""
    import ctypes
    from ctypes import wintypes

    class LISTA(ctypes.Structure):
        _fields_ = [("hDevice", wintypes.HANDLE), ("dwType", wintypes.DWORD)]

    class HID(ctypes.Structure):
        _fields_ = [("dwVendorId", wintypes.DWORD), ("dwProductId", wintypes.DWORD),
                    ("dwVersionNumber", wintypes.DWORD), ("usUsagePage", wintypes.USHORT),
                    ("usUsage", wintypes.USHORT)]

    class QUALQUER(ctypes.Union):
        _fields_ = [("hid", HID), ("_espaco", ctypes.c_byte * 24)]   # mouse/teclado ocupam 24

    class INFO(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.DWORD), ("dwType", wintypes.DWORD), ("u", QUALQUER)]

    user32 = ctypes.WinDLL("user32")
    lista_de = user32.GetRawInputDeviceList
    lista_de.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.UINT), wintypes.UINT]
    lista_de.restype = wintypes.UINT
    info_de = user32.GetRawInputDeviceInfoW
    info_de.argtypes = [wintypes.HANDLE, wintypes.UINT, ctypes.c_void_p, ctypes.POINTER(wintypes.UINT)]
    info_de.restype = wintypes.UINT
    RIM_TYPEHID, RIDI_DEVICENAME, RIDI_DEVICEINFO = 2, 0x20000007, 0x2000000B

    quantos = wintypes.UINT(0)
    if lista_de(None, ctypes.byref(quantos), ctypes.sizeof(LISTA)) == 0xFFFFFFFF or not quantos.value:
        return 0
    dispositivos = (LISTA * quantos.value)()
    lidos = lista_de(dispositivos, ctypes.byref(quantos), ctypes.sizeof(LISTA))
    if lidos == 0xFFFFFFFF:
        return 0
    contagem = 0
    for dispositivo in dispositivos[:lidos]:
        if dispositivo.dwType != RIM_TYPEHID:
            continue
        info = INFO()
        info.cbSize = ctypes.sizeof(INFO)
        tamanho = wintypes.UINT(ctypes.sizeof(INFO))
        if info_de(dispositivo.hDevice, RIDI_DEVICEINFO, ctypes.byref(info), ctypes.byref(tamanho)) in (0, 0xFFFFFFFF):
            continue
        if info.u.hid.usUsagePage != 1 or info.u.hid.usUsage not in (4, 5):    # joystick ou gamepad
            continue
        letras = wintypes.UINT(0)
        info_de(dispositivo.hDevice, RIDI_DEVICENAME, None, ctypes.byref(letras))
        nome = ctypes.create_unicode_buffer(letras.value + 1)
        info_de(dispositivo.hDevice, RIDI_DEVICENAME, nome, ctypes.byref(letras))
        if "IG_" in nome.value.upper():
            continue                     # e' XInput: o XInput ja conta
        contagem += 1
    return contagem


def controles_xinput():
    """Numeros (0 a 3) dos controles XInput ligados agora -- Xbox, GameSir e
    parecidos. E' o que o Dolphin chama de "XInput/N/Gamepad"."""
    try:
        import ctypes
        estado = (ctypes.c_ubyte * 16)()
        for nome in ("xinput1_4", "xinput1_3", "xinput9_1_0"):
            try:
                xinput = getattr(ctypes.windll, nome)
            except OSError:
                continue
            return [n for n in range(4)
                    if xinput.XInputGetState(n, ctypes.byref(estado)) == 0]
    except (AttributeError, OSError, ValueError):
        pass
    return []


def opcoes_do_teclado(dados, controles_ligados):
    """Em qual jogador o teclado fica, e com quais teclas.

    Regra (aprovada pelo Rafael): o teclado e' o PRIMEIRO jogador sem
    controle. 3 controles -> teclado no jogador 4; nenhum -> jogador 1
    (quem nao tem controle continua jogando). Escreve o teclado de todos os
    jogadores explicitamente, para nada velho do retroarch.cfg valer. As
    direcoes movem tambem o analogico esquerdo (ANALOGICO_DO_TECLADO)."""
    teclas = dict(TECLADO_PADRAO)
    for botao, atribuicao in (dados.get("1") or {}).items():
        if atribuicao.get("tipo") == "teclado":
            teclas[botao] = atribuicao.get("valor", "")

    dono = min(max(controles_ligados, 0) + 1, JOGADORES_NO_CONTROLE)
    opcoes = {}
    for jogador in range(1, JOGADORES_NO_CONTROLE + 1):
        for botao in BOTOES:
            opcoes["input_player%d_%s" % (jogador, botao)] = "nul"
        for eixo, _direcao in ANALOGICO_DO_TECLADO:
            opcoes["input_player%d_%s" % (jogador, eixo)] = "nul"
    for botao, tecla in teclas.items():
        if tecla:
            opcoes["input_player%d_%s" % (dono, botao)] = tecla
    for eixo, direcao in ANALOGICO_DO_TECLADO:
        if teclas.get(direcao):
            opcoes["input_player%d_%s" % (dono, eixo)] = teclas[direcao]
    # Teclas que o aluno pos em outro jogador na tela (hoje, o jogador 2)
    # continuam la, e as direcoes dele tambem movem o analogico.
    for jogador in JOGADORES[1:]:
        for botao, atribuicao in (dados.get(jogador) or {}).items():
            if atribuicao.get("tipo") == "teclado" and atribuicao.get("valor"):
                opcoes["input_player%s_%s" % (jogador, botao)] = atribuicao["valor"]
                for eixo, direcao in ANALOGICO_DO_TECLADO:
                    if direcao == botao:
                        opcoes["input_player%s_%s" % (jogador, eixo)] = atribuicao["valor"]
    return opcoes


def opcoes_do_retroarch(dados=None, controles_ligados=0):
    """Transforma o mapeamento nas chaves que o RetroArch entende.

    Botao e eixo de controle que o aluno nao mexeu vao como "nul": o
    RetroArch entao usa o reconhecimento automatico, e nao um numero velho
    do retroarch.cfg. O teclado vai para o primeiro jogador sem controle
    (ver opcoes_do_teclado).
    """
    dados = dados if dados is not None else ler()
    opcoes = {}

    for jogador in range(1, JOGADORES_NO_CONTROLE + 1):
        for botao in BOTOES:
            opcoes["input_player%d_%s_btn" % (jogador, botao)] = "nul"
            opcoes["input_player%d_%s_axis" % (jogador, botao)] = "nul"
    opcoes.update(opcoes_do_teclado(dados, controles_ligados))

    for jogador in JOGADORES:
        for botao, atribuicao in (dados.get(jogador) or {}).items():
            tipo = atribuicao.get("tipo")
            if tipo not in SUFIXO or tipo == "teclado":
                continue   # teclado: ja resolvido em opcoes_do_teclado
            chave = "input_player%s_%s%s" % (jogador, botao, SUFIXO[tipo])
            opcoes[chave] = atribuicao.get("valor", "")

    return opcoes


def resumo(dados=None):
    """Quantos botoes cada jogador tem definidos."""
    dados = dados if dados is not None else ler()
    return {jogador: len(dados.get(jogador) or {}) for jogador in JOGADORES}


# ---------------------------------------------------------------------------
# Sugestao de teclado
# ---------------------------------------------------------------------------
# O mapeamento de fabrica do RetroArch para o teclado. Serve de ponto de
# partida: o aluno clica em "usar o padrao" e ajusta so o que incomoda.

PADRAO_TECLADO = {
    "1": {
        "up": "up", "down": "down", "left": "left", "right": "right",
        "b": "z", "a": "x", "y": "a", "x": "s",
        "l": "q", "r": "w", "start": "enter", "select": "rshift",
    },
    "2": {
        "up": "t", "down": "g", "left": "f", "right": "h",
        "b": "k", "a": "l", "y": "j", "x": "i",
        "l": "u", "r": "o", "start": "p", "select": "semicolon",
    },
}


# Numeracao do NAVEGADOR ("Standard Gamepad"). Serve SO para achar o nome
# do botao nos rotulos de perfis_controle.json e mostrar na tela ("A",
# "Cruz"...). NUNCA escrever estes numeros no RetroArch: no XInput dele o
# Start e' 6, nao 9 (ver aplicar_padrao_controle).
NUMERO_NO_NAVEGADOR = {
    "b": "0", "a": "1", "y": "2", "x": "3",
    "l": "4", "r": "5", "l2": "6", "r2": "7",
    "select": "8", "start": "9", "l3": "10", "r3": "11",
    "up": "12", "down": "13", "left": "14", "right": "15",
}


def aplicar_padrao_controle(jogador):
    """Volta o controle daquele jogador ao reconhecimento automatico.

    Apaga os botoes de CONTROLE definidos a mao (o teclado fica). Ai o
    RetroArch usa o perfil pronto do controle (~380 em retroarch\\autoconfig).

    Antes, este botao ("Mapear meu controle sozinho") gravava a numeracao
    do NAVEGADOR (Start 9, Select 8, gatilhos 6/7...). No XInput do
    RetroArch esses numeros sao outros botoes: o Start caia no R3. Achado
    com os GameSir do Rafael (25/09/2026); era a origem dos numeros sujos
    no retroarch.cfg.
    """
    if jogador not in JOGADORES:
        return None, "Escolha o jogador na lista (de 1 a 5)."
    dados = ler()
    dados[jogador] = {botao: atribuicao for botao, atribuicao in dados[jogador].items()
                      if atribuicao.get("tipo") == "teclado"}
    _gravar(dados)
    return dados, None


def aplicar_padrao(jogador):
    """Coloca o mapeamento de fabrica do teclado para aquele jogador."""
    if jogador not in JOGADORES:
        return None, "Escolha o jogador na lista (de 1 a 5)."
    if jogador not in PADRAO_TECLADO:
        return None, ("O teclado padrão existe para os jogadores 1 e 2. "
                      "Para este jogador, defina as teclas uma a uma.")
    dados = ler()
    dados[jogador] = {botao: {"tipo": "teclado", "valor": tecla}
                      for botao, tecla in PADRAO_TECLADO[jogador].items()}
    _gravar(dados)
    return dados, None
