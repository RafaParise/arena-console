# -*- coding: utf-8 -*-
"""
ARENA - Graficos, controles e partida a dois
=============================================
Tres coisas que dependem de conhecer a maquina:

GRAFICOS
    Cada emulador tem opcoes proprias: resolucao interna, filtro de textura,
    mipmap, correcao de cor. O RetroArch le tudo isso de um arquivo unico,
    'retroarch-core-options.cfg'. Este modulo monta esse arquivo escolhendo,
    para cada emulador, o ajuste que a maquina aguenta.

    Nada aqui pesa em disco. Filtro e resolucao interna custam PLACA DE
    VIDEO. E as opcoes de "carregar para a memoria" fazem o contrario:
    tiram o disco do caminho durante o jogo, deixando o disco livre para o
    servidor do ARENA.

CONTROLES
    Escolhe o driver de entrada que reconhece o maior numero de controles.

PARTIDA A DOIS
    Monta a linha de comando do RetroArch para hospedar ou entrar numa
    partida, definindo quem e o jogador 1 e quem e o 2.

So biblioteca padrao.
"""

import json
import os
import time
import threading

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
ARQUIVO_GRAFICOS = os.path.join(PASTA_SERVIDOR, "graficos.json")
ARQUIVO_OPCOES_CORE = os.path.join(PASTA_RETROARCH, "retroarch-core-options.cfg")

PORTA_PARTIDA = 55435
PASTA_EMULADORES = os.path.join(RAIZ, "emuladores")


# ---------------------------------------------------------------------------
# Graficos
# ---------------------------------------------------------------------------

_cache = {"graficos": None}


def carregar_graficos():
    """Le graficos.json. Se estiver quebrado, segue sem ajuste fino."""
    if _cache["graficos"] is None:
        try:
            with open(ARQUIVO_GRAFICOS, "r", encoding="utf-8") as arquivo:
                _cache["graficos"] = json.load(arquivo)
        except (OSError, ValueError) as falha:
            print("[ARENA] graficos.json ilegivel (%s). Seguindo sem ajuste "
                  "fino de imagem." % falha)
            _cache["graficos"] = {"shaders": {}, "nucleos": {}}
    return _cache["graficos"]


def opcoes_do_nucleo(nome_curto, nota):
    """Junta os ajustes daquele emulador que cabem nesta maquina.

    Os blocos sao aplicados do mais leve para o mais pesado, cada um por
    cima do anterior. Assim uma maquina nota 4 recebe o bloco 1, o 3 e o 4,
    e o que vier depois vence.
    """
    dados = carregar_graficos()["nucleos"].get(nome_curto)
    if not dados:
        return {}

    opcoes = dict(dados.get("sempre", {}))
    for bloco in sorted(dados.get("por_nota", []),
                        key=lambda b: b.get("nota_minima", 0)):
        if nota >= bloco.get("nota_minima", 0):
            opcoes.update(bloco.get("opcoes", {}))
    return opcoes


def gravar_opcoes_dos_nucleos(nota, extras=None, nota_gpu=None):
    """Monta retroarch-core-options.cfg com o ajuste de todos os emuladores.

    Vale a pena escrever tudo de uma vez, e nao so do jogo que vai abrir:
    o arquivo e pequeno, e assim o aluno pode abrir o RetroArch por fora
    que os ajustes continuam valendo.
    """
    linhas = ["# Gerado pelo ARENA conforme a potencia desta maquina.",
              "# Para mudar, edite servidor/graficos.json - nao este arquivo."]

    dados = carregar_graficos()
    da_placa = set(dados.get("_usa_nota_gpu", []))

    for nome_curto in sorted(dados["nucleos"]):
        # Resolucao interna, filtro de textura e anti-serrilhado dependem
        # da PLACA de video. Num PC com placa integrada, esses consoles
        # usam a nota menor mesmo que o processador seja bom.
        alvo = nota_gpu if (nota_gpu is not None and nome_curto in da_placa) else nota
        opcoes = opcoes_do_nucleo(nome_curto, alvo)
        if not opcoes:
            continue
        for chave in sorted(opcoes):
            linhas.append('%s = "%s"' % (chave, opcoes[chave]))

    # BIOS escolhida e pasta do memory card entram por cima.
    for chave in sorted(extras or {}):
        linhas.append('%s = "%s"' % (chave, extras[chave]))

    os.makedirs(PASTA_RETROARCH, exist_ok=True)
    gravar_atomico(ARQUIVO_OPCOES_CORE, "\n".join(linhas) + "\n")
    return len(linhas) - 2


def shader_para(nota):
    """Filtro de tela adequado a maquina, se o arquivo existir.

    Shader e o mais perto de um 'ReShade' que faz sentido aqui: melhora a
    aparencia usando a placa de video, sem tocar no disco. Mas so entra se
    o pacote de shaders do RetroArch estiver instalado - senao o jogo
    abriria com a tela preta.
    """
    tabela = carregar_graficos().get("shaders", {})
    escolhido = ""
    for limite in sorted(k for k in tabela if k.isdigit()):
        if nota >= int(limite):
            escolhido = tabela[limite]

    if not escolhido:
        return ""

    caminho = os.path.join(PASTA_RETROARCH, escolhido.replace("/", os.sep))
    return caminho if os.path.isfile(caminho) else ""


# ---------------------------------------------------------------------------
# Emuladores de fora
# ---------------------------------------------------------------------------
# Alguns nucleos do RetroArch nao dao conta. O de PlayStation 2 e o caso
# mais claro: e pouco mantido e costuma nem abrir o jogo, que foi
# exatamente o sintoma relatado.
#
# Quando existe um emulador de verdade na pasta 'emuladores', o ARENA
# passa a chamar ele para aquela plataforma. Continua sendo tudo dentro
# da pasta do ARENA, sem instalar nada.

def achar_externo(plataforma):
    """Procura o emulador de fora daquela plataforma.

    Devolve (caminho do executavel, dados do cadastro), ou (None, dados).
    Procura na pasta cadastrada e um nivel abaixo, porque quase todo
    programa vem dentro de uma subpasta com o numero da versao.
    """
    externo = plataforma.get("externo")
    if not externo:
        return None, None

    base = os.path.join(PASTA_EMULADORES, externo["pasta"])
    if not os.path.isdir(base):
        return None, externo

    procurados = [n.lower() for n in externo["executaveis"]]

    # Primeiro na propria pasta, depois um nivel abaixo.
    for raiz, subpastas, arquivos in os.walk(base):
        for arquivo in arquivos:
            if arquivo.lower() in procurados:
                return os.path.join(raiz, arquivo), externo
        # Nao descer mais que dois niveis: pasta de emulador e cheia de
        # subpastas e varrer tudo seria lento em pen drive.
        if raiz.count(os.sep) - base.count(os.sep) >= 1:
            subpastas[:] = []

    return None, externo


def comando_externo(caminho_executavel, dados, caminho_jogo):
    """Monta a linha de comando do emulador de fora."""
    argumentos = []
    for parte in dados.get("argumentos", ["{jogo}"]):
        argumentos.append(parte.replace("{jogo}", caminho_jogo)
                          if "{jogo}" in parte else parte)
    return [caminho_executavel] + argumentos


def situacao_dos_externos(plataformas):
    """Diz, para a tela, quais emuladores de fora estao instalados."""
    saida = []
    for plataforma in plataformas:
        externo = plataforma.get("externo")
        if not externo:
            continue
        caminho, _ = achar_externo(plataforma)
        saida.append({
            "plataforma": plataforma["nome"],
            "id": plataforma["id"],
            "nome": externo["nome"],
            "pasta": "emuladores\\" + externo["pasta"],
            "site": externo.get("site", ""),
            "motivo": externo.get("motivo", ""),
            "instalado": bool(caminho),
        })
    return saida


# ---------------------------------------------------------------------------
# BIOS e memory card
# ---------------------------------------------------------------------------
# Por que isso importa: o console guarda a data, a hora e as preferencias
# DENTRO da BIOS. Se cada jogo abrir com um arquivo diferente, o relogio
# volta para 1 de janeiro toda vez e o memory card parece vazio.
#
# Fixando uma BIOS por console, o aluno abre a tela inicial do PlayStation,
# ve a data certa e os iconezinhos dos jogos salvos - do jeito que era no
# aparelho de verdade.

EXTENSOES_BIOS = (".bin", ".rom", ".bios", ".img", ".pup", ".mec", ".nvm")

# Chave do RetroArch que escolhe a BIOS, por nucleo. So os nucleos em que
# faz diferenca escolher entre varias.
CHAVE_BIOS = {
    "swanstation": ["swanstation_BIOS_Path", "duckstation_BIOS.Path"],
    "mednafen_saturn": ["beetle_saturn_region"],
    "opera": ["opera_bios"],
    "flycast": ["reicast_boot_to_bios"],
}


def bios_disponiveis(pasta_sistema):
    """Lista os arquivos que podem ser BIOS, sem julgar quais sao de qual
    console. O ARENA nao nomeia nem sugere arquivo nenhum: so mostra o que
    voce ja colocou na pasta, para poder escolher."""
    achados = []
    try:
        for nome in sorted(os.listdir(pasta_sistema)):
            caminho = os.path.join(pasta_sistema, nome)
            if not os.path.isfile(caminho):
                continue
            if not nome.lower().endswith(EXTENSOES_BIOS):
                continue
            achados.append({
                "arquivo": nome,
                "tamanho_kb": round(os.path.getsize(caminho) / 1024.0),
            })
    except OSError:
        pass
    return achados


def opcoes_de_bios(nome_curto_core, arquivo):
    """Diz ao emulador qual arquivo usar como BIOS."""
    if not arquivo:
        return {}
    chaves = CHAVE_BIOS.get(nome_curto_core, [])
    return {chave: arquivo for chave in chaves}


def listar_memory_cards(pasta_saves):
    """Lista os memory cards, como se fossem cartoes fisicos numa caixinha.

    Mostra tamanho e data de cada um. Para o cartao de PlayStation 1, que
    tem formato conhecido e simples, tambem conta quantos blocos estao em
    uso - o mesmo numero que o console mostrava na tela de memory card.
    """
    pasta = os.path.join(pasta_saves, "memcards")
    achados = []
    try:
        nomes = sorted(os.listdir(pasta))
    except OSError:
        return achados

    for nome in nomes:
        caminho = os.path.join(pasta, nome)
        if not os.path.isfile(caminho):
            continue
        try:
            tamanho = os.path.getsize(caminho)
            quando = time.strftime("%d/%m/%Y %H:%M",
                                   time.localtime(os.path.getmtime(caminho)))
        except OSError:
            continue

        usados = None
        if nome.lower().endswith((".mcd", ".mcr", ".srm")) and tamanho >= 131072:
            usados = _blocos_usados_ps1(caminho)

        achados.append({
            "arquivo": nome,
            "tamanho_kb": round(tamanho / 1024.0),
            "quando": quando,
            "blocos_usados": usados,
            "blocos_total": 15 if usados is not None else None,
        })
    return achados


def _blocos_usados_ps1(caminho):
    """Conta os blocos ocupados num memory card de PlayStation 1.

    O cartao tem 128 KB divididos em 16 blocos de 8 KB. O bloco 0 e o
    indice: 15 fichas de 128 bytes, uma por bloco de save. O primeiro byte
    da ficha diz o estado - 0x51 quer dizer 'em uso'.
    """
    try:
        with open(caminho, "rb") as arquivo:
            indice = arquivo.read(8192)
        if len(indice) < 8192:
            return None
        usados = 0
        for slot in range(1, 16):
            estado = indice[slot * 128]
            if estado in (0x51, 0x52, 0x53):
                usados += 1
        return usados
    except OSError:
        return None


def opcoes_de_memory_card(pasta_saves, plataforma_id):
    """Deixa o memory card num lugar fixo, um por console.

    Assim os saves de PlayStation nao se misturam com os de Sega, e o
    mesmo cartao aparece toda vez que voce abre qualquer jogo daquele
    console - inclusive com os iconezinhos na tela inicial.
    """
    if plataforma_id not in ("ps1", "ps2"):
        return {}

    cartao = os.path.join(pasta_saves, "memcards")
    os.makedirs(cartao, exist_ok=True)
    return {
        "swanstation_MemoryCards_Card1Type": "Shared",
        "swanstation_MemoryCards_Directory": cartao,
        "duckstation_MemoryCards.Card1Type": "Shared",
        "duckstation_MemoryCards.Directory": cartao,
    }


# ---------------------------------------------------------------------------
# Controles
# ---------------------------------------------------------------------------
# O Windows enxerga controle de duas formas:
#
#   XInput   - Xbox 360, Xbox One, Xbox Series e a maioria dos genericos
#              modernos. Reconhecimento automatico, gatilhos analogicos,
#              vibracao. E o caminho mais direto.
#   DirectInput - o formato antigo. Cobre PlayStation 3, alguns Switch Pro
#              por cabo, arcade sticks e controles genericos mais velhos,
#              que o XInput simplesmente nao ve.
#
# O RetroArch escolhe um driver por vez. 'xinput' cobre a maioria das
# maquinas de escola; 'dinput' e a rede de seguranca para controle antigo.

DRIVERS_CONTROLE = ["xinput", "dinput"]

CONTROLES_CONHECIDOS = [
    ("Xbox 360, One e Series", "xinput", "Plugou, funcionou. Nao precisa de nada."),
    ("PlayStation 4 e 5", "xinput",
     "Por cabo USB funciona direto. Por Bluetooth tambem, depois de parear."),
    ("PlayStation 3", "dinput",
     "Precisa do driver SCP ou DsHidMini no Windows. Depois disso funciona."),
    ("Nintendo Switch Pro", "xinput",
     "Por cabo USB funciona. Por Bluetooth, pareie antes pelo Windows."),
    ("Joy-Con avulso", "dinput",
     "Funciona como controle pequeno. Mapeie os botoes na mao."),
    ("Steam Controller", "xinput",
     "Deixe o Steam aberto: ele converte para XInput sozinho."),
    ("Genericos e arcade stick", "dinput",
     "Quase todos funcionam. Se nao aparecer, troque o driver para dinput."),
    ("Teclado", "-", "Sempre funciona como jogador 1, mesmo com controle plugado."),
]


# ---------------------------------------------------------------------------
# Dizer ao console que o controle tem analogico
# ---------------------------------------------------------------------------
# Faltava isto, e era o motivo de o analogico nao funcionar no PlayStation
# por mais que o controle estivesse certo.
#
# O console nao adivinha que controle esta plugado. O PlayStation 1 saiu de
# fabrica com um controle SEM analogico; o DualShock veio depois. O
# emulador comeca imitando o controle antigo, e ai os dois analogicos nao
# fazem nada - nem o esquerdo, nem o direito.
#
# 513 = controle comum (so direcional)
# 517 = controle com dois analogicos (DualShock e equivalentes)

CONTROLE_ANALOGICO = 517
CONTROLE_COMUM = 513

# Consoles cujo controle padrao tem dois analogicos.
COM_ANALOGICO = {
    "ps1": CONTROLE_ANALOGICO,       # DualShock
    "ps2": CONTROLE_ANALOGICO,       # DualShock 2
    "dreamcast": CONTROLE_ANALOGICO,
    "saturn": CONTROLE_ANALOGICO,    # 3D Control Pad
    "gamecube": CONTROLE_ANALOGICO,
    "n64": CONTROLE_ANALOGICO,       # o N64 tem um analogico so, mas o
                                     # nucleo aceita o mesmo codigo
}


def opcoes_de_controle(plataforma_id, quantos_jogadores=2):
    """Diz ao nucleo que tipo de controle cada jogador esta usando.

    Sem isto, o analogico fica mudo em PlayStation, Dreamcast e Saturn -
    o console acha que o controle e o velho, sem analogico nenhum.
    """
    tipo = COM_ANALOGICO.get(plataforma_id)
    if not tipo:
        return {}

    opcoes = {}
    for jogador in range(1, max(1, min(quantos_jogadores, 4)) + 1):
        opcoes["input_libretro_device_p%d" % jogador] = str(tipo)
        # O analogico esquerdo tambem anda como direcional, e o direcional
        # continua funcionando. O analogico direito fica livre para o que
        # o jogo quiser - camera, mira.
        opcoes["input_player%d_analog_dpad_mode" % jogador] = "1"
    return opcoes


# ---------------------------------------------------------------------------
# Nome dos botoes em cada console
# ---------------------------------------------------------------------------
# O RetroArch fala em "botao A", "botao B", que sao os nomes do Super
# Nintendo. Quem esta configurando um controle para PlayStation 2 quer
# saber onde fica o X, o quadrado e o triangulo.
#
# A tabela abaixo traduz. O nome tecnico continua sendo o do RetroArch,
# porque e o que aparece na tela dele; ao lado vai o nome do console.

BOTOES_RETROARCH = ["b", "a", "y", "x", "l", "r", "l2", "r2", "l3", "r3",
                    "start", "select", "up", "down", "left", "right"]

NOMES_DOS_BOTOES = {
    "ps1": {"b": "X", "a": "Circulo", "y": "Quadrado", "x": "Triangulo",
            "l": "L1", "r": "R1", "l2": "L2", "r2": "R2",
            "l3": "L3 (apertar o analogico)", "r3": "R3 (apertar o analogico)",
            "start": "Start", "select": "Select"},
    "ps2": {"b": "X", "a": "Circulo", "y": "Quadrado", "x": "Triangulo",
            "l": "L1", "r": "R1", "l2": "L2", "r2": "R2",
            "l3": "L3 (apertar o analogico)", "r3": "R3 (apertar o analogico)",
            "start": "Start", "select": "Select"},
    "psp": {"b": "X", "a": "Circulo", "y": "Quadrado", "x": "Triangulo",
            "l": "L", "r": "R", "start": "Start", "select": "Select"},
    "snes": {"b": "B", "a": "A", "y": "Y", "x": "X", "l": "L", "r": "R",
             "start": "Start", "select": "Select"},
    "nes": {"b": "B", "a": "A", "start": "Start", "select": "Select"},
    "n64": {"b": "A", "a": "B", "y": "C-esquerda", "x": "C-cima",
            "l": "L", "r": "R", "l2": "Z", "start": "Start"},
    "gamecube": {"b": "A", "a": "B", "y": "Y", "x": "X",
                 "l": "L", "r": "R", "r2": "Z", "start": "Start"},
    "megadrive": {"b": "A", "a": "B", "y": "X", "x": "Y",
                  "l": "Z", "r": "C", "start": "Start", "select": "Mode"},
    "dreamcast": {"b": "A", "a": "B", "y": "X", "x": "Y",
                  "l2": "Gatilho esquerdo", "r2": "Gatilho direito",
                  "start": "Start"},
    "saturn": {"b": "A", "a": "B", "y": "X", "x": "Y",
               "l": "L", "r": "R", "start": "Start"},
    "gameboy": {"b": "B", "a": "A", "start": "Start", "select": "Select"},
    "gba": {"b": "B", "a": "A", "l": "L", "r": "R",
            "start": "Start", "select": "Select"},
    "nds": {"b": "B", "a": "A", "y": "Y", "x": "X", "l": "L", "r": "R",
            "start": "Start", "select": "Select"},
    "neogeo": {"b": "A", "a": "B", "y": "C", "x": "D",
               "start": "Start", "select": "Select"},
}

DIRECIONAL = {"up": "para cima", "down": "para baixo",
              "left": "para a esquerda", "right": "para a direita"}


def botoes_do_console(plataforma_id):
    """Diz como cada botao do RetroArch se chama naquele console."""
    tabela = NOMES_DOS_BOTOES.get(plataforma_id)
    if not tabela:
        return []

    saida = []
    for chave in BOTOES_RETROARCH:
        if chave in DIRECIONAL:
            saida.append({"retroarch": chave.upper(),
                          "console": "Direcional " + DIRECIONAL[chave]})
        elif chave in tabela:
            saida.append({"retroarch": "Botao " + chave.upper(),
                          "console": tabela[chave]})
    return saida


def consoles_com_botoes():
    return sorted(NOMES_DOS_BOTOES)


# ---------------------------------------------------------------------------
# Configurar o PCSX2 a partir do ARENA
# ---------------------------------------------------------------------------
# O PCSX2 tem tela propria e o ARENA nao consegue trocar isso. Mas ele le
# um arquivo de configuracao antes de abrir - e esse arquivo o ARENA
# escreve. Assim o aluno acha o controle ja pronto: dois analogicos,
# direcional funcionando junto, vibracao ligada, tela cheia.
#
# Escreve so os blocos que interessam e preserva o resto do arquivo, para
# nao apagar a BIOS que o aluno ja configurou.

BLOCO_PCSX2 = """[Pad1]
Type = DualShock2
Deadzone = 0.10
AxisScale = 1.33
LargeMotorScale = 1.00
SmallMotorScale = 1.00
InvertL = 0
InvertR = 0
Up = SDL-0/DPadUp
Down = SDL-0/DPadDown
Left = SDL-0/DPadLeft
Right = SDL-0/DPadRight
Cross = SDL-0/A
Circle = SDL-0/B
Square = SDL-0/X
Triangle = SDL-0/Y
L1 = SDL-0/LeftShoulder
R1 = SDL-0/RightShoulder
L2 = SDL-0/+LeftTrigger
R2 = SDL-0/+RightTrigger
L3 = SDL-0/LeftStick
R3 = SDL-0/RightStick
Select = SDL-0/Back
Start = SDL-0/Start
LUp = SDL-0/-LeftY
LDown = SDL-0/+LeftY
LLeft = SDL-0/-LeftX
LRight = SDL-0/+LeftX
RUp = SDL-0/-RightY
RDown = SDL-0/+RightY
RLeft = SDL-0/-RightX
RRight = SDL-0/+RightX
LargeMotor = SDL-0/LargeMotor
SmallMotor = SDL-0/SmallMotor

[Pad2]
Type = DualShock2
Deadzone = 0.10
AxisScale = 1.33
LargeMotorScale = 1.00
SmallMotorScale = 1.00
Up = SDL-1/DPadUp
Down = SDL-1/DPadDown
Left = SDL-1/DPadLeft
Right = SDL-1/DPadRight
Cross = SDL-1/A
Circle = SDL-1/B
Square = SDL-1/X
Triangle = SDL-1/Y
L1 = SDL-1/LeftShoulder
R1 = SDL-1/RightShoulder
L2 = SDL-1/+LeftTrigger
R2 = SDL-1/+RightTrigger
L3 = SDL-1/LeftStick
R3 = SDL-1/RightStick
Select = SDL-1/Back
Start = SDL-1/Start
LUp = SDL-1/-LeftY
LDown = SDL-1/+LeftY
LLeft = SDL-1/-LeftX
LRight = SDL-1/+LeftX
RUp = SDL-1/-RightY
RDown = SDL-1/+RightY
RLeft = SDL-1/-RightX
RRight = SDL-1/+RightX
LargeMotor = SDL-1/LargeMotor
SmallMotor = SDL-1/SmallMotor

[InputSources]
SDL = true
SDLControllerEnhancedMode = true
XInput = false
RawInput = false

[Hotkeys]
OpenPauseMenu = Keyboard/Escape
SaveStateToSlot = Keyboard/F1
LoadStateFromSlot = Keyboard/F3
NextSaveStateSlot = Keyboard/F2
ToggleFullscreen = Keyboard/F11
Screenshot = Keyboard/F8
ShutdownVM = Keyboard/F10
"""


def escrever_config_pcsx2(caminho_executavel, ultra=False):
    """Escreve o bloco de controle e teclas do PCSX2.

    Preserva tudo o que ja estiver no arquivo fora desses blocos - em
    especial a BIOS, que o aluno configura uma vez pela tela do programa.
    """
    pasta = os.path.dirname(caminho_executavel)
    destino = os.path.join(pasta, "inis", "PCSX2.ini")

    nossos = {"[Pad1]", "[Pad2]", "[InputSources]", "[Hotkeys]"}
    guardar, bloco_atual = [], None

    try:
        with open(destino, "r", encoding="utf-8", errors="replace") as arquivo:
            for linha in arquivo:
                limpo = linha.strip()
                if limpo.startswith("[") and limpo.endswith("]"):
                    bloco_atual = limpo
                if bloco_atual not in nossos:
                    guardar.append(linha.rstrip("\n"))
    except OSError:
        guardar = []

    extra = []
    if ultra:
        extra = ["", "[EmuCore/GS]", "VsyncEnable = 1",
                 "OsdShowMessages = false", "OsdShowSpeed = false",
                 "", "[UI]", "StartFullscreen = true",
                 "ConfirmShutdown = false"]

    texto = "\n".join(guardar + [""] + BLOCO_PCSX2.splitlines() + extra) + "\n"

    try:
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        gravar_atomico(destino, texto)
        return destino
    except OSError:
        return None


# ---------------------------------------------------------------------------
# Partida a dois
# ---------------------------------------------------------------------------
# O RetroArch tem rede propria, do mesmo tipo que Mortal Kombat 3 e os
# arcades da epoca usavam: os dois lados rodam o MESMO jogo e trocam apenas
# os comandos dos botoes. Nao vai video pela rede - vai "o jogador 2 apertou
# soco". Por isso funciona bem ate em rede fraca.
#
# Quem hospeda e o jogador 1. Quem entra e o jogador 2. Os dois precisam do
# mesmo jogo e do mesmo emulador; se um arquivo for diferente, a partida
# nem comeca.

# Servidores de repasse do RetroArch. Servem para quando os dois estao em
# casas diferentes: em vez de um tentar alcancar o outro direto - o que a
# internet residencial brasileira nao permite, por causa do CGNAT - os dois
# se conectam a um mesmo ponto no meio do caminho.
#
# Pelo repasse trafega SO o comando dos botoes. Nao vai video, nao vai som,
# nao vai arquivo de jogo. O que aparece do outro lado e o apelido.
REPASSES = {
    "saopaulo": "Sao Paulo (o mais perto do Brasil)",
    "nyc": "Nova York",
    "madrid": "Madri",
    "montreal": "Montreal",
}
REPASSE_PADRAO = "saopaulo"


def opcoes_de_partida(apelido, hospedar, atraso=0, assistir=False,
                      pela_internet=False, repasse=REPASSE_PADRAO):
    """Opcoes do RetroArch para hospedar, entrar ou assistir uma partida.

    Assistir e o mesmo caminho de entrar numa partida, so que sem pegar
    nenhum controle. Voce ve a tela do amigo em tempo real - do jeito que
    a Steam deixa acompanhar a partida de alguem - e nao atrapalha o jogo
    dele. E leve porque nao viaja video pela rede: viaja o comando dos
    botoes, e o SEU computador desenha a mesma coisa que o dele.

    Por isso o amigo precisa ter o mesmo jogo para assistir. Sem o jogo,
    nao ha o que desenhar deste lado.
    """
    # Na rede local os dois se alcancam direto, e e sempre melhor: menos
    # atraso e nada sai da escola. Pela internet, o repasse e o unico
    # caminho que funciona de casa para casa.
    opcoes = {
        "netplay_nickname": (apelido or "jogador")[:24],
        "netplay_port": str(PORTA_PARTIDA),
        # Nunca anunciar a partida na lista publica: quem entra e quem foi
        # convidado, e ninguem mais.
        "netplay_public_announce": "false",
        "netplay_use_mitm_server": "true" if pela_internet else "false",
        "netplay_mitm_server": repasse if repasse in REPASSES else REPASSE_PADRAO,
        "netplay_start_as_spectator": "true" if assistir else "false",
        "netplay_allow_slaves": "true",
        "netplay_require_slaves": "false",
        # Quantos quadros de folga antes de sincronizar. Na rede local,
        # zero. Pela internet, uma folga evita o jogo travar a cada
        # oscilacao - e melhor um atraso constante que um soluco.
        "netplay_input_latency_frames_min": str(3 if pela_internet else int(atraso)),
        "netplay_input_latency_frames_range": "6" if pela_internet else "0",
        "netplay_check_frames": "900" if pela_internet else "600",
        "netplay_nat_traversal": "true" if pela_internet else "false",
        "netplay_stateless_mode": "false",
    }

    if assistir:
        # Espectador nao pede controle nenhum: so olha.
        opcoes["netplay_request_device_p1"] = "false"
        opcoes["netplay_request_device_p2"] = "false"
    elif hospedar:
        # Quem hospeda fica com o controle do jogador 1.
        opcoes["netplay_request_device_p1"] = "true"
        opcoes["netplay_request_device_p2"] = "false"
    else:
        # Quem entra fica com o jogador 2.
        opcoes["netplay_request_device_p1"] = "false"
        opcoes["netplay_request_device_p2"] = "true"

    return opcoes


def argumentos_de_partida(hospedar, endereco=None):
    """Parametros de linha de comando para abrir o jogo em rede."""
    if hospedar:
        return ["--host"]
    return ["--connect", str(endereco or "127.0.0.1")]


def repasses_disponiveis():
    return [{"id": chave, "nome": nome} for chave, nome in REPASSES.items()]
