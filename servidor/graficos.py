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
import re
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


def gravar_opcoes_dos_nucleos(nota, extras=None, nota_gpu=None, modesto=False):
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

        # Excecoes conhecidas por nucleo: defeito que a nota de hardware
        # nao prevê, porque e conhecimento do emulador, nao da maquina.
        # Modo modesto: resolucao nativa e nada mais, por cima de tudo.
        # Para quando ate o perfil leve ainda esta pesado - o caso do
        # Celeron de dois nucleos com grafico integrado.
        if modesto:
            opcoes.update(dados.get("modesto", {}).get(nome_curto, {}))
        else:
            excecao = dados.get("excecoes", {}).get(nome_curto, {})
            for bloco in sorted(excecao.get("por_nota", []),
                                key=lambda b: b.get("nota_minima", 0)):
                if alvo >= bloco.get("nota_minima", 0):
                    opcoes.update(bloco.get("opcoes", {}))
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

EXTENSOES_COMPACTADO = (".zip", ".7z", ".rar")


def achar_externo(plataforma):
    """Procura o emulador de fora daquela plataforma.

    Devolve (caminho do executavel, dados do cadastro), ou (None, dados).
    Procura na pasta cadastrada e um nivel abaixo, porque quase todo
    programa vem dentro de uma subpasta com o numero da versao.
    """
    caminho, _, externo = achar_externo_detalhado(plataforma)
    return caminho, externo


def achar_externo_detalhado(plataforma):
    """Como achar_externo(), mas tambem avisa se so achou um .zip/.7z.

    Erro comum: baixar o emulador e largar o arquivo compactado dentro da
    pasta sem extrair. Sem esse aviso, a tela so diz "nao instalado" e o
    aluno nao entende por que, ja que o arquivo esta bem ali.

    Devolve (caminho do executavel ou None, caminho do compactado achado
    ou None, dados do cadastro).
    """
    externo = plataforma.get("externo")
    if not externo:
        return None, None, None

    base = os.path.join(PASTA_EMULADORES, externo["pasta"])
    if not os.path.isdir(base):
        return None, None, externo

    procurados = [n.lower() for n in externo["executaveis"]]
    # Se o nome exato mudar numa versao futura do emulador (ja aconteceu:
    # o proprio cadastro dos nomes nunca foi conferido contra um download
    # real do PCSX2), ainda reconhece por prefixo -- "PCSX2" cadastrado
    # acha "pcsx2-qtx64-avx2.exe" mesmo sem esse nome exato na lista.
    prefixo = externo["nome"].lower()
    compactado = None
    candidato_prefixo = None
    achados = {}  # nome exato encontrado -> caminho completo

    # Primeiro na propria pasta, depois um nivel abaixo.
    for raiz, subpastas, arquivos in os.walk(base):
        for arquivo in arquivos:
            nome_baixo = arquivo.lower()
            if nome_baixo in procurados and nome_baixo not in achados:
                achados[nome_baixo] = os.path.join(raiz, arquivo)
            if (candidato_prefixo is None and nome_baixo.endswith(".exe")
                    and nome_baixo.startswith(prefixo)):
                candidato_prefixo = os.path.join(raiz, arquivo)
            if compactado is None and nome_baixo.endswith(EXTENSOES_COMPACTADO):
                compactado = os.path.join(raiz, arquivo)
        # Nao descer mais que dois niveis: pasta de emulador e cheia de
        # subpastas e varrer tudo seria lento em pen drive.
        if raiz.count(os.sep) - base.count(os.sep) >= 1:
            subpastas[:] = []

    # Quando mais de uma variante esta instalada ao mesmo tempo (ex.: o
    # Xenia Canary normal E a versao com netplay), vence a que vier
    # primeiro na lista do cadastro - "executaveis" fica em ordem de
    # preferencia, nao em ordem alfabetica.
    for nome in procurados:
        if nome in achados:
            return achados[nome], None, externo

    if candidato_prefixo:
        return candidato_prefixo, None, externo
    return None, compactado, externo


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
        caminho, compactado, _ = achar_externo_detalhado(plataforma)
        saida.append({
            "plataforma": plataforma["nome"],
            "id": plataforma["id"],
            "nome": externo["nome"],
            "pasta": "emuladores\\" + externo["pasta"],
            "site": externo.get("site", ""),
            "motivo": externo.get("motivo", ""),
            "instalado": bool(caminho),
            "compactado_pendente": os.path.basename(compactado) if compactado else "",
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


def _trocar_valor_toml(texto, chave, valor):
    """Troca so o VALOR de uma linha 'chave = valor  # comentario' do TOML.

    Preserva o alinhamento e o comentario que vem depois - o arquivo do
    Xenia e feito pra ser lido por gente, com centenas de linhas de
    explicacao, e reescrever tudo do zero jogaria essas explicacoes fora.
    So mexe na primeira ocorrencia da chave no inicio da linha.
    """
    padrao = re.compile(r"^(" + re.escape(chave) + r"\s*=\s*)\S+", re.MULTILINE)
    return padrao.sub(lambda m: m.group(1) + valor, texto, count=1)


def escrever_config_xenia(caminho_executavel, nota, nota_gpu=None, modesto=False,
                          ultra=False):
    """Escreve o bloco de video do Xenia (Xbox 360), preservando o resto.

    NAO escreve mapeamento de controle: o formato dos 'keybind_*' do Xenia
    (codigo de tecla do Windows em hexadecimal, ou letra solta, ou um
    prefixo '^' cujo significado exato nao pude confirmar sem testar de
    verdade) e arriscado demais pra converter as cegas a partir do mapa
    interno do ARENA. Fica pro RetroArch, onde o ARENA ja sabe traduzir
    tecla com confianca.

    So mexe se o Xenia ja rodou pelo menos uma vez e criou o arquivo dele
    - nao inventamos um do zero, pra nao perder as centenas de opcoes que
    so o Xenia sabe o valor certo.
    """
    pasta = os.path.dirname(caminho_executavel)
    nome_exe = os.path.splitext(os.path.basename(caminho_executavel))[0]
    nome_config = nome_exe.replace("_", "-") + ".config.toml"
    destino = os.path.join(pasta, nome_config)

    if not os.path.isfile(destino):
        return None

    try:
        with open(destino, "r", encoding="utf-8") as arquivo:
            texto = arquivo.read()
    except OSError:
        return None

    alvo_nota = nota_gpu if nota_gpu is not None else nota
    forte = alvo_nota >= 4 and not modesto

    ajustes = {
        "fullscreen": "true" if ultra else "false",
        "vsync": "true",
        "framerate_limit": "0",
    }
    if modesto or alvo_nota <= 2:
        # Resolucao nativa do jogo, sem escala nem suavizacao - o mais
        # leve possivel, para quando ate o perfil normal engasga.
        ajustes.update({
            "draw_resolution_scale_x": "1",
            "draw_resolution_scale_y": "1",
            "anisotropic_override": "0",
            "postprocess_antialiasing": '""',
            "postprocess_scaling_and_sharpening": '"bilinear"',
        })
    elif forte:
        # Maquina forte: dobra a resolucao interna e usa o FSR da AMD pra
        # deixar a imagem mais nitida - funciona em qualquer placa, nao
        # so AMD.
        ajustes.update({
            "draw_resolution_scale_x": "2",
            "draw_resolution_scale_y": "2",
            "anisotropic_override": "5",
            "postprocess_antialiasing": '""',
            "postprocess_scaling_and_sharpening": '"fsr"',
        })
    else:
        ajustes.update({
            "draw_resolution_scale_x": "1",
            "draw_resolution_scale_y": "1",
            "anisotropic_override": "2",
            "postprocess_antialiasing": '"fxaa"',
            "postprocess_scaling_and_sharpening": '"bilinear"',
        })

    for chave, valor in ajustes.items():
        texto = _trocar_valor_toml(texto, chave, valor)

    try:
        gravar_atomico(destino, texto)
        return destino
    except OSError:
        return None


def _trocar_valor_yaml(texto, secao, chave, valor):
    """Troca o valor de 'chave: valor' dentro de uma secao do YAML do RPCS3.

    O YAML do RPCS3 usa indentacao (2 espacos por nivel) pra dizer o que
    esta dentro de que secao - por isso nao da pra so procurar a chave em
    qualquer lugar do arquivo: "Renderer:" aparece dentro de "Video:" E
    de "Audio:", com sentidos diferentes. So troca a chave de 2 espacos
    de indentacao que estiver dentro da secao pedida (0 espacos).
    """
    linhas = texto.split("\n")
    prefixo = "  " + chave + ":"
    dentro = False
    for i, linha in enumerate(linhas):
        if linha.startswith(secao + ":"):
            dentro = True
            continue
        if not linha.startswith(" ") and linha.strip():
            dentro = False
        if dentro and linha.startswith(prefixo):
            linhas[i] = "  %s: %s" % (chave, valor)
    return "\n".join(linhas)


def escrever_config_rpcs3(caminho_executavel, nota, nota_gpu=None, modesto=False,
                          ultra=False):
    """Escreve o bloco de video do RPCS3 (PlayStation 3), preservando o resto.

    Mesma logica do Xenia: so mexe se o RPCS3 ja criou o config.yml dele
    (primeira vez que abre, mesmo sem jogo nenhum). O mapeamento de
    controle do RPCS3 fica em arquivos separados dentro de
    config/input_configs/ e o formato deles ainda nao foi conferido -
    fica pra depois.
    """
    pasta = os.path.dirname(caminho_executavel)
    destino = os.path.join(pasta, "config", "config.yml")

    if not os.path.isfile(destino):
        return None

    try:
        with open(destino, "r", encoding="utf-8") as arquivo:
            texto = arquivo.read()
    except OSError:
        return None

    alvo_nota = nota_gpu if nota_gpu is not None else nota
    forte = alvo_nota >= 4 and not modesto

    if modesto or alvo_nota <= 2:
        video = {
            "Resolution Scale": "100",
            "Anisotropic Filter Override": "0",
            "MSAA": "Disabled",
            "Frame limit": "Off",
        }
    elif forte:
        video = {
            "Resolution Scale": "150",
            "Anisotropic Filter Override": "16",
            "MSAA": "Auto",
            "Frame limit": "Auto",
        }
    else:
        video = {
            "Resolution Scale": "100",
            "Anisotropic Filter Override": "4",
            "MSAA": "Auto",
            "Frame limit": "Auto",
        }
    video["VSync Mode"] = "Disabled"  # o RetroArch e o Xenia ja cuidam disso melhor

    for chave, valor in video.items():
        texto = _trocar_valor_yaml(texto, "Video", chave, valor)

    texto = _trocar_valor_yaml(texto, "Miscellaneous",
                               "Start games in fullscreen mode",
                               "true" if ultra else "false")

    try:
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


JOGADORES_PADRAO_NETPLAY = 2
JOGADORES_MAXIMO_NETPLAY = 8  # limite de seguranca; nenhum console cadastrado passa disso


def opcoes_de_partida(apelido, hospedar, atraso=0, assistir=False,
                      pela_internet=False, repasse=REPASSE_PADRAO, jogador=None):
    """Opcoes do RetroArch para hospedar, entrar ou assistir uma partida.

    Assistir e o mesmo caminho de entrar numa partida, so que sem pegar
    nenhum controle. Voce ve a tela do amigo em tempo real - do jeito que
    a Steam deixa acompanhar a partida de alguem - e nao atrapalha o jogo
    dele. E leve porque nao viaja video pela rede: viaja o comando dos
    botoes, e o SEU computador desenha a mesma coisa que o dele.

    Por isso o amigo precisa ter o mesmo jogo para assistir. Sem o jogo,
    nao ha o que desenhar deste lado.

    'jogador' e o numero da posicao (1 a 8) que esta maquina vai ocupar -
    quem hospeda e sempre o 1; quem entra escolhe 2, 3, 4... conforme o
    console permitir (N64 tem 4 entradas de fabrica, por exemplo). Cada
    posicao usa uma chave propria do RetroArch,
    'netplay_request_device_pN' - nao existe uma unica chave "sou o
    jogador X", tem que ligar a certa e deixar as outras desligadas.
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

    posicao = 1 if hospedar else int(jogador or JOGADORES_PADRAO_NETPLAY)
    posicao = max(1, min(posicao, JOGADORES_MAXIMO_NETPLAY))

    for n in range(1, JOGADORES_MAXIMO_NETPLAY + 1):
        # Espectador nao pede controle nenhum: so olha. Todo mundo comeca
        # desligado, e so a posicao escolhida liga - senao o RetroArch
        # pode herdar "true" de uma partida anterior gravada no override.
        opcoes["netplay_request_device_p%d" % n] = (
            "true" if (not assistir and n == posicao) else "false")

    return opcoes


def argumentos_de_partida(hospedar, endereco=None, porta=None):
    """Parametros de linha de comando para abrir o jogo em rede.

    A porta vai explicita aqui, alem de estar no arquivo de configuracao.
    Cinto e suspensorio: se por algum motivo o arquivo de configuracao nao
    for lido a tempo, a porta da linha de comando ainda vale.
    """
    porta = int(porta or PORTA_PARTIDA)
    if hospedar:
        return ["--host", "--port", str(porta)]
    return ["--connect", str(endereco or "127.0.0.1"), "--port", str(porta)]


def repasses_disponiveis():
    return [{"id": chave, "nome": nome} for chave, nome in REPASSES.items()]
