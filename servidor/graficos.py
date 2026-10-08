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
import shutil
import subprocess
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
# Auto-conserto do retroarch.cfg (pen drive muda de letra, pasta muda de lugar)
# ---------------------------------------------------------------------------
# O RetroArch grava, ao fechar (config_save_on_exit = true), os caminhos
# absolutos que recebeu. Se a pasta do ARENA for movida - pen drive com
# letra diferente, pasta renomeada, copiada pra outro computador - esses
# caminhos ficam apontando pra um lugar que nao existe mais.
#
# Nao precisa saber qual era a pasta antiga. Toda linha 'chave = "caminho"'
# do retroarch.cfg que aponta pra dentro do ARENA sempre contem uma das
# pastas que sempre existem (dados, retroarch, jogos, launcher,
# emuladores). Acha essa pasta dentro do valor antigo e reconstroi o
# caminho a partir da raiz ATUAL - nao importa qual era a raiz antiga.

PASTAS_CONHECIDAS_ARENA = ("dados", "retroarch", "jogos", "launcher", "emuladores")

_PADRAO_LINHA_CAMINHO = re.compile(
    r'^([a-zA-Z0-9_]+\s*=\s*)"([A-Za-z]:\\[^"]*)"\s*$')


# Chaves que o RetroArch usa por padrao (fora da pasta do ARENA) quando
# ninguem diz o contrario, e que so ganham valor certo depois que um jogo
# abre e fecha pelo menos uma vez. Ex.: cache_directory sem isto vira a
# pasta Temp do Windows - contra a regra de nunca deixar nada fora do
# ARENA. Forcadas sempre, nao so quando "parecem" um caminho velho.
CHAVES_SEMPRE_DENTRO_DO_ARENA = {
    "cache_directory": "retroarch\\cache",
}

# Lugar certo de cada chave quando o caminho gravado aponta para FORA do
# ARENA e nao tem nenhuma pasta conhecida dentro para reaproveitar. Achado
# real (revisao pos-auditoria): um teste abriu o RetroArch com pastas
# temporarias, o RetroArch gravou isso ao fechar, e o retroarch.cfg ficou
# com saves, estados e historico apontando para uma pasta do Temp que ja
# tinha sido apagada. Os mesmos lugares que o ARENA manda em toda partida
# (arena.py, opcoes da partida). "{nome}" = o nome do arquivo antigo.
CHAVES_COM_LUGAR_CERTO = {
    "savefile_directory": "retroarch\\saves",
    "savestate_directory": "retroarch\\states",
    "screenshot_directory": "retroarch\\screenshots",
    "system_directory": "retroarch\\system",
    "playlist_directory": "dados",
    "log_dir": "dados",
    "core_options_path": "retroarch\\retroarch-core-options.cfg",
    "content_favorites_path": "dados\\builtin\\{nome}",
    "content_history_path": "dados\\builtin\\{nome}",
    "content_image_history_path": "dados\\builtin\\{nome}",
    "content_music_history_path": "dados\\builtin\\{nome}",
    "content_video_history_path": "dados\\builtin\\{nome}",
}


# Chaves que NUNCA podem ficar ligadas no retroarch.cfg, nem para quem abrir
# o retroarch.exe direto, fora do ARENA. network_cmd_enable deixava o
# RetroArch aceitar comandos (fechar o jogo, salvar...) de qualquer maquina
# da rede, em 0.0.0.0:55355 -- achado real na revisao pos-auditoria.
VALORES_OBRIGATORIOS = {
    "network_cmd_enable": "false",
}


def corrigir_caminhos_retroarch_cfg():
    """Reescreve, dentro do retroarch.cfg, todo caminho que nao aponta mais
    para a pasta atual do ARENA, e desliga o que nunca pode ficar ligado
    (VALORES_OBRIGATORIOS). Devolve quantas linhas foram trocadas.
    """
    caminho_cfg = os.path.join(PASTA_RETROARCH, "retroarch.cfg")
    try:
        with open(caminho_cfg, "r", encoding="utf-8", errors="replace") as arquivo:
            linhas = arquivo.readlines()
    except OSError:
        return 0

    raiz_baixo = RAIZ.lower()
    trocados = 0
    achadas = set()

    for i, linha in enumerate(linhas):
        chave_da_linha = linha.split("=", 1)[0].strip()
        if chave_da_linha in VALORES_OBRIGATORIOS:
            certo = '%s = "%s"\n' % (chave_da_linha, VALORES_OBRIGATORIOS[chave_da_linha])
            if linha != certo:
                linhas[i] = certo
                trocados += 1
            continue
        if chave_da_linha in CHAVES_SEMPRE_DENTRO_DO_ARENA:
            # Achado de 01/10/2026: ao fechar, o RetroArch regrava esta chave
            # na forma DELE, ":\cache" (a pasta do proprio RetroArch, ja
            # dentro do ARENA). So o caminho C:\... era reconhecido: a
            # chave "nao existia" e ganhava uma linha nova a cada abertura
            # (5 iguais neste PC). Agora a forma ":\" vale, e a repetida sai.
            if chave_da_linha in achadas:
                linhas[i] = ""
                trocados += 1
                continue
            achadas.add(chave_da_linha)
            valor = linha.split("=", 1)[1].strip().strip('"') if "=" in linha else ""
            if valor.startswith((":\\", ":/")):
                continue
            certo = os.path.join(RAIZ, CHAVES_SEMPRE_DENTRO_DO_ARENA[chave_da_linha])
            if valor != certo:
                linhas[i] = '%s = "%s"\n' % (chave_da_linha, certo)
                trocados += 1
            continue
        m = _PADRAO_LINHA_CAMINHO.match(linha.rstrip("\n"))
        if not m:
            continue
        prefixo, caminho_velho = m.group(1), m.group(2)
        chave = prefixo.split("=", 1)[0].strip()

        if caminho_velho.lower().startswith(raiz_baixo):
            continue  # ja aponta pra pasta certa

        velho_baixo = caminho_velho.lower()
        for pasta in PASTAS_CONHECIDAS_ARENA:
            meio = "\\" + pasta + "\\"
            indice = velho_baixo.find(meio)
            if indice == -1 and velho_baixo.endswith("\\" + pasta):
                indice = len(velho_baixo) - len(pasta) - 1
            if indice == -1:
                continue
            resto = caminho_velho[indice + 1:]  # sem a barra inicial
            linhas[i] = '%s"%s"\n' % (prefixo, os.path.join(RAIZ, resto))
            trocados += 1
            break
        else:
            # Nenhuma pasta do ARENA dentro do caminho velho: se a chave
            # tem lugar certo conhecido, volta para ele.
            if chave in CHAVES_COM_LUGAR_CERTO:
                relativo = CHAVES_COM_LUGAR_CERTO[chave].format(
                    nome=os.path.basename(caminho_velho))
                linhas[i] = '%s"%s"\n' % (prefixo, os.path.join(RAIZ, relativo))
                trocados += 1

    # Chave que nem aparece no arquivo (RetroArch novo, nunca rodou): cria.
    for chave, relativo in CHAVES_SEMPRE_DENTRO_DO_ARENA.items():
        if chave in achadas:
            continue
        certo = os.path.join(RAIZ, relativo)
        linhas.append('%s = "%s"\n' % (chave, certo))
        trocados += 1

    if trocados:
        os.makedirs(os.path.join(RAIZ, "retroarch", "cache"), exist_ok=True)
        gravar_atomico(caminho_cfg, "".join(linhas))
    return trocados


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


def tela_4k_vale(nota_gpu, altura_tela):
    """O degrau "tela 4K" (graficos.json -> tela_4k) vale nesta maquina?
    So com placa DEDICADA (a integrada nao passa da nota 3) e tela de 4K de
    verdade. Sem a nota da placa (chamada antiga), nunca."""
    regra = carregar_graficos().get("tela_4k", {})
    if nota_gpu is None or not regra.get("nucleos"):
        return False
    return (nota_gpu >= regra.get("nota_gpu_minima", 4)
            and (altura_tela or 0) >= regra.get("altura_minima", 2000))


# Niveis ABAIXO do grafico original (pedido do Rafael, 02/10/2026: "mesmo que
# o grafico fique muito feio, bonecos de papelao -- a ideia e' que, se
# configurar corretamente, pode rodar em qualquer maquina"). O "minimo"
# inclui tudo do "leve". Valores por emulador: graficos.json ->
# abaixo_do_original (nucleos do RetroArch) e escrever_config_pcsx2,
# opcoes_de_imagem_dolphin e escrever_config_rpcs3 (emuladores de fora).
NIVEIS_ABAIXO = ("leve", "minimo")


def niveis_abaixo_ate(abaixo):
    """("leve",) para "leve", ("leve", "minimo") para "minimo", () fora disso."""
    if abaixo not in NIVEIS_ABAIXO:
        return ()
    return NIVEIS_ABAIXO[:NIVEIS_ABAIXO.index(abaixo) + 1]


def gravar_opcoes_dos_nucleos(nota, extras=None, nota_gpu=None, modesto=False, altura_tela=None,
                              abaixo=""):
    """Monta retroarch-core-options.cfg com o ajuste de todos os emuladores.

    Vale a pena escrever tudo de uma vez, e nao so do jogo que vai abrir:
    o arquivo e pequeno, e assim o aluno pode abrir o RetroArch por fora
    que os ajustes continuam valendo.

    'altura_tela': linhas da tela (hardware.altura_da_tela); sem ela, o
    ARENA mede na hora -- e instantaneo, e pega a TV 4K ligada depois.

    'abaixo': "leve" ou "minimo" -- abaixo do grafico original, por cima do
    bloco modesto (graficos.json -> abaixo_do_original).
    """
    niveis = niveis_abaixo_ate(abaixo)
    if niveis:
        modesto = True    # abaixo do original comeca no original
    if altura_tela is None:
        try:
            import hardware
            altura_tela = hardware.altura_da_tela()
        except Exception:
            altura_tela = 0
    tela_4k = tela_4k_vale(nota_gpu, altura_tela)
    linhas = ["# Gerado pelo ARENA conforme a potencia desta maquina.",
              "# Para mudar, edite servidor/graficos.json - nao este arquivo."]

    dados = carregar_graficos()
    da_placa = set(dados.get("_usa_nota_gpu", []))
    bloco_abaixo = dados.get("abaixo_do_original", {})
    # Nucleos que so aparecem no bloco abaixo do original (o pulo de quadros
    # do Lynx, do 32X...) entram na lista so quando o nivel esta ligado.
    com_abaixo = {nucleo for nivel in niveis for nucleo in bloco_abaixo.get(nivel, {})}

    for nome_curto in sorted(set(dados["nucleos"]) | com_abaixo):
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
            # Abaixo do original: por cima do original, o "minimo" por cima
            # do "leve".
            for nivel in niveis:
                opcoes.update(bloco_abaixo.get(nivel, {}).get(nome_curto, {}))
        else:
            excecao = dados.get("excecoes", {}).get(nome_curto, {})
            for bloco in sorted(excecao.get("por_nota", []),
                                key=lambda b: b.get("nota_minima", 0)):
                if alvo >= bloco.get("nota_minima", 0):
                    opcoes.update(bloco.get("opcoes", {}))
            # Tela 4K com placa dedicada: os 3D leves desenham perto da
            # resolucao da tela (graficos.json -> tela_4k).
            if tela_4k:
                opcoes.update(dados.get("tela_4k", {}).get("nucleos", {}).get(nome_curto, {}))
        if not opcoes:
            continue
        for chave in sorted(opcoes):
            linhas.append('%s = "%s"' % (chave, opcoes[chave]))

    # BIOS escolhida e memory card entram por cima.
    for chave in sorted(extras or {}):
        linhas.append('%s = "%s"' % (chave, extras[chave]))

    # O resto e' do aluno: opcao que ele mudou no menu do RetroArch e que o
    # ARENA nao ajusta. Antes este arquivo era reescrito do zero -- nao fazia
    # mal so porque o RetroArch nem lia este arquivo (ver global_core_options
    # em arena.gravar_override). Agora que le, apagar seria perder o ajuste.
    ja_escritas = {l.split(" = ", 1)[0] for l in linhas if " = " in l}
    do_aluno = {k: v for k, v in opcoes_do_aluno().items() if k not in ja_escritas}
    if do_aluno:
        linhas.append("# Opcoes mudadas no menu do RetroArch (o ARENA mantem):")
        for chave in sorted(do_aluno):
            linhas.append('%s = "%s"' % (chave, do_aluno[chave]))

    os.makedirs(PASTA_RETROARCH, exist_ok=True)
    gravar_atomico(ARQUIVO_OPCOES_CORE, "\n".join(linhas) + "\n")
    return len(linhas) - 2 - (1 if do_aluno else 0) - len(do_aluno)


def filtro_de_tela(plataforma):
    """Caminho do filtro de tela (shader) para este console, ou "".

    So os consoles de desenho 2D (graficos.json -> shaders -> plataformas)
    recebem filtro: o "pixel nitido" (sharp-bilinear), que deixa todo pixel
    do mesmo tamanho em qualquer tela -- 1366x768 ou 4K -- quase sem custo.
    Console 3D ganha definicao pela resolucao interna, sem filtro.

    So entra se o arquivo existir: sem o pacote de shaders, ligar o filtro
    deixaria a tela preta.

    Achado de 01/10/2026: a versao anterior escolhia o filtro pela nota da
    placa e o ARENA o escrevia como video_shader no arquivo extra -- que o
    RetroArch 1.22 IGNORA (o registro dizia "Loading stock shader"). Nenhum
    filtro chegou a aparecer. Agora vai pela linha de comando (--set-shader).
    """
    tabela = carregar_graficos().get("shaders", {})
    if plataforma not in (tabela.get("plataformas") or []):
        return ""
    escolhido = tabela.get("pixel") or ""
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


def falta_para_o_externo(nome_externo, caminho_executavel):
    """O que falta, alem do proprio emulador, para ele abrir um jogo.
    Devolve a frase para o aluno, ou "" se nao falta nada que se saiba.

    RPCS3 (revisao pos-auditoria): sem o firmware oficial do PS3 instalado
    nele, o RPCS3 desiste em 1 segundo ("Missing Firmware" no log dele) e o
    jogo so "pisca e fecha" -- testado com Borderlands 2. O firmware e' o
    arquivo oficial da Sony; o ARENA nao fornece, so avisa.

    PCSX2 (01/10/2026, versao dos alunos, que vem sem BIOS): sem BIOS de
    PS2 o cartao aparecia "pronto" e o PCSX2 abria so para reclamar dela.
    Agora o ARENA avisa antes, e o cartao fica amarelo com este motivo."""
    if nome_externo == "PCSX2" and caminho_executavel and not tem_bios_pcsx2(caminho_executavel):
        return ("O PS2 precisa da BIOS do PlayStation 2 (um arquivo .bin de 4 MB), e ela "
                "ainda não está aqui. Peça ao professor: o arquivo vai na pasta BIOS\\PS2 do "
                "ARENA (Ajustes → Emuladores → BIOS dos consoles), e o ARENA leva para o "
                "PCSX2 sozinho.")
    if nome_externo == "RPCS3" and caminho_executavel:
        firmware = os.path.join(os.path.dirname(caminho_executavel),
                                "dev_flash", "sys", "external", "liblv2.sprx")
        if not os.path.isfile(firmware):
            return ("O PS3 precisa do firmware oficial da Sony instalado no RPCS3, "
                    "e ele ainda não está. Peça ao professor: ponha o PS3UPDAT.PUP (do site "
                    "da PlayStation) na pasta BIOS\\PS3 do ARENA e, no RPCS3, use o menu "
                    "File > Install Firmware com esse arquivo.")
    return ""


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
            "falta": falta_para_o_externo(externo["nome"], caminho),
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

# Chave do RetroArch que escolhe a BIOS, por nucleo. So os nucleos que TEM
# essa chave de verdade -- conferido lendo cada .dll
# (ferramentas\chaves_bios_nucleos.py). Corrigido na revisao pos-auditoria:
# antes a lista tinha "swanstation_BIOS_Path" e "duckstation_BIOS.Path" (nao
# existem), "beetle_saturn_region" (e' a REGIAO do console, nao um arquivo) e
# "reicast_boot_to_bios" (nao existe nesta versao do Flycast). A escolha na
# tela nao fazia nada nesses consoles. Os outros acham a BIOS sozinhos, pelo
# conteudo do arquivo.
CHAVE_BIOS = {
    # Uma chave por regiao; a mesma BIOS escolhida vale para as tres.
    "swanstation": ["swanstation_BIOS_PathNTSCJ", "swanstation_BIOS_PathNTSCU",
                    "swanstation_BIOS_PathPAL"],
    "opera": ["opera_bios"],
}

# Alguns nucleos so aceitam uma lista fechada de nomes de arquivo nessa
# chave. Arquivo com outro nome e' ignorado pelo nucleo -- entao nem oferecer.
BIOS_ACEITAS = {
    "swanstation": ("scph5500.bin", "scph5501.bin", "scph5502.bin",
                    "psxonpsp660.bin", "ps1_rom.bin", "openbios.bin"),
    # 3DO: so os nomes da lista "firmware" do opera_libretro.info (antes a
    # tela oferecia QUALQUER arquivo da pasta -- ate a BIOS do PS2).
    "opera": ("panafz10.bin", "panafz1.bin", "panafz10-norsa.bin", "panafz10e-anvil.bin",
              "panafz10e-anvil-norsa.bin", "goldstar.bin", "sanyotry.bin", "3do_arcade_saot.bin",
              "panafz1j.bin", "panafz1j-norsa.bin"),
}


def bios_que_o_nucleo_aceita(nome_curto_core, arquivos):
    """Dos arquivos da pasta de BIOS, quais este nucleo deixa ESCOLHER.
    Lista vazia = a escolha nao funciona nesse nucleo (ele acha sozinho)."""
    if nome_curto_core not in CHAVE_BIOS:
        return []
    aceitas = BIOS_ACEITAS.get(nome_curto_core)
    if aceitas is None:
        return list(arquivos)
    return [a for a in arquivos if a.lower() in aceitas]


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
    if not arquivo or not bios_que_o_nucleo_aceita(nome_curto_core, [arquivo]):
        return {}
    if nome_curto_core in BIOS_ACEITAS:
        arquivo = arquivo.lower()  # a lista do nucleo e' toda em minusculas
    return {chave: arquivo for chave in CHAVE_BIOS[nome_curto_core]}


# BIOS de PS2 tem sempre 4 MB (4194304 bytes) - tamanho fixo, diferente da
# BIOS de PS1 (512 KB) e do "rom1.bin" que acompanha algumas delas (so o
# modulo de DVD, nao a BIOS principal). Da pra separar sem ler CRC32.
TAMANHO_BIOS_PS2 = 4194304


def tem_bios_pcsx2(caminho_executavel, pasta_sistema=None):
    """Ha uma BIOS de PS2 que o PCSX2 vai achar? Na pasta bios\\ dele, ou
    uma de 4 MB em retroarch\\system (preparar_bios_pcsx2 copia na hora)."""
    pasta_sistema = pasta_sistema or os.path.join(PASTA_RETROARCH, "system")
    propria = os.path.join(os.path.dirname(caminho_executavel), "bios")
    try:
        if os.path.isdir(propria) and any(nome.lower().endswith(EXTENSOES_BIOS)
                                          for nome in os.listdir(propria)):
            return True
        return any(nome.lower().endswith(".bin")
                   and os.path.getsize(os.path.join(pasta_sistema, nome)) == TAMANHO_BIOS_PS2
                   for nome in os.listdir(pasta_sistema))
    except OSError:
        return False


def preparar_bios_pcsx2(caminho_executavel, pasta_sistema):
    """Copia uma BIOS de PS2 de 'pasta_sistema' pra pasta que o PCSX2
    procura sozinho (bios\\, do lado do executavel) - sem isso ele abre
    num assistente pedindo pra escolher a BIOS na tela, e o ARENA nao tem
    como responder por conta do aluno.

    Existem varias BIOS de regioes diferentes possiveis em pasta_sistema;
    sem CRC32 cadastrado pra cada uma (o jeito que o RetroArch resolve
    isso sozinho), o ARENA nao sabe qual e' "a certa" pro jogo - so pega
    a primeira em ordem alfabetica, de forma sempre igual. Nao sobrescreve
    se ja tem alguma BIOS la' dentro (o aluno pode ter colocado a dele).
    """
    destino = os.path.join(os.path.dirname(caminho_executavel), "bios")
    try:
        if os.path.isdir(destino) and any(
                nome.lower().endswith(EXTENSOES_BIOS)
                for nome in os.listdir(destino)):
            return None  # ja tem BIOS la, nao mexe.

        candidatos = sorted(
            nome for nome in os.listdir(pasta_sistema)
            if nome.lower().endswith(".bin") and
            os.path.getsize(os.path.join(pasta_sistema, nome)) == TAMANHO_BIOS_PS2)
        if not candidatos:
            return None

        os.makedirs(destino, exist_ok=True)
        escolhida = candidatos[0]
        shutil.copy2(os.path.join(pasta_sistema, escolhida),
                     os.path.join(destino, escolhida))
        return escolhida
    except OSError:
        return None


def preparar_portatil_pcsx2(caminho_executavel):
    """Liga o modo portatil do PCSX2 e traz os memory cards de Documentos.

    Achado 26/09/2026: sem 'portable.txt' (vazio) ao lado do pcsx2-qt.exe,
    o PCSX2 le e grava em Documentos\\PCSX2 -- aqui, dentro do OneDrive.
    Tudo o que o ARENA escrevia na pasta dele (controles, multitap,
    qualidade) era IGNORADO, e os saves de PS2 ficavam fora do pen drive.
    Regra do codigo do PCSX2 (Pcsx2Config.cpp): portable.ini/portable.txt
    em AppRoot; o conteudo do .txt e' uma subpasta, por isso fica vazio.

    Na primeira vez, COPIA (nao move) os memory cards de Documentos para a
    pasta do PCSX2 no ARENA, para ninguem perder o progresso. Devolve os
    nomes dos cartoes usados (slot 1, slot 2)."""
    pasta = os.path.dirname(caminho_executavel)
    portatil = os.path.join(pasta, "portable.txt")
    if not os.path.exists(portatil):
        with open(portatil, "w", encoding="utf-8"):
            pass
    cartoes = os.path.join(pasta, "memcards")
    nomes = ["Mcd001.ps2", "Mcd002.ps2"]
    antigo = os.path.join(os.path.expanduser("~"), "Documents", "PCSX2")
    try:
        import ctypes.wintypes
        caminho = ctypes.create_unicode_buffer(260)
        if ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, caminho) == 0:
            antigo = os.path.join(caminho.value, "PCSX2")   # 5 = Meus Documentos
    except (AttributeError, OSError):
        pass
    ini_antigo = os.path.join(antigo, "inis", "PCSX2.ini")
    if os.path.isfile(ini_antigo):
        try:
            with open(ini_antigo, encoding="utf-8", errors="replace") as arquivo:
                texto = arquivo.read()
            for i, chave in enumerate(("Slot1_Filename", "Slot2_Filename")):
                achado = re.search(r"^%s\s*=\s*(.+)$" % chave, texto, re.M)
                if achado:
                    nomes[i] = achado.group(1).strip()
        except OSError:
            pass
    if not os.path.isdir(cartoes):
        os.makedirs(cartoes, exist_ok=True)
        for nome in nomes:
            origem = os.path.join(antigo, "memcards", nome)
            if os.path.isfile(origem):
                shutil.copy2(origem, os.path.join(cartoes, nome))
    return nomes


def listar_memory_cards(pasta_saves):
    """Lista os memory cards, como se fossem cartoes fisicos numa caixinha.

    Mostra tamanho e data de cada um. Para o cartao de PlayStation 1, que
    tem formato conhecido e simples, tambem conta quantos blocos estao em
    uso - o mesmo numero que o console mostrava na tela de memory card.
    """
    # Corrigido na revisao pos-auditoria: so olhava saves\memcards, que fica
    # vazia -- os cartoes de verdade sao um por jogo, na pasta de cada
    # nucleo (saves\SwanStation\Crash Bandicoot (USA).srm). A tela dizia
    # "Nenhum cartao ainda" com varios jogos salvos. A subpasta .netplay
    # (cartao temporario de partida a dois) fica de fora.
    candidatos = []
    for pasta in [os.path.join(pasta_saves, "memcards")] + [
            os.path.join(pasta_saves, n) for n in ("SwanStation", "PCSX-ReARMed")]:
        try:
            for nome in sorted(os.listdir(pasta)):
                candidatos.append((pasta, nome))
        except OSError:
            continue
    achados = []

    for pasta, nome in candidatos:
        caminho = os.path.join(pasta, nome)
        if not os.path.isfile(caminho):
            continue
        if not nome.lower().endswith((".mcd", ".mcr", ".srm", ".ps2")):
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
            "arquivo": os.path.splitext(nome)[0] if pasta != os.path.join(
                pasta_saves, "memcards") else nome,
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
    """Memory card do PlayStation 1: um cartao por jogo.

    Corrigido na revisao pos-auditoria. A ideia antiga era um cartao so por
    console ("Shared"), mas a chave nunca chegava ao nucleo (o RetroArch lia
    o .opt do nucleo, nao o arquivo do ARENA) e "..._Directory" /
    "duckstation_*" nem existem no SwanStation. Na pratica, todo save de
    PS1 feito ate hoje esta num cartao POR JOGO (saves\\SwanStation\\<jogo>.srm).
    Ligar "Shared" agora faria esses saves sumirem da tela do jogo (ele
    abriria um cartao novo, vazio). Por isso fica escrito o que ja vale:
    "Libretro", um cartao por jogo, salvo junto com os outros saves.
    """
    if plataforma_id != "ps1":
        return {}
    return {"swanstation_MemoryCards_Card1Type": "Libretro"}


# ---------------------------------------------------------------------------
# Cache de video do PS1 (so no modo economico)
# ---------------------------------------------------------------------------
# Achado da auditoria 2 (testes\cache_pipelines_ps1.py): o SwanStation
# regrava INTEIRO o arquivo retroarch\system\swanstation\vulkan_pipelines.bin
# (15 a 50 MB) toda vez que um jogo de PS1 fecha -- com o conteudo IGUAL. E
# o cache nem acelera a abertura (6,2 s sem ele x 6,4-7,1 s com ele). Num
# pen drive lento sao 5 a 10 s com o jogo "travado" fechando, e desgaste.
# Nao existe opcao do nucleo para isso (ShaderPrecompile=false testado: nao
# muda nada). O que funciona: arquivo somente leitura -- o jogo abre igual e
# o arquivo para de ser regravado (testado).
#
# Regra: depois de uma partida, se o cache NAO cresceu (nada novo
# aprendido), vira somente leitura. Se o pen drive for para outro
# computador (outra placa de video), o cache antigo nao serve la: libera
# e apaga, para o nucleo montar um novo para esta placa.

CACHE_PS1 = os.path.join(PASTA_RETROARCH, "system", "swanstation", "vulkan_pipelines.bin")


def _marca_do_cache_ps1():
    return CACHE_PS1 + ".placa"


def preparar_cache_ps1(placa):
    """Antes de abrir um jogo de PS1. Devolve o tamanho atual do cache
    (ou -1 se nao existe), para comparar depois."""
    try:
        if not os.path.isfile(CACHE_PS1):
            return -1
        try:
            with open(_marca_do_cache_ps1(), encoding="utf-8") as f:
                placa_do_cache = f.read().strip()
        except OSError:
            placa_do_cache = ""
        if placa_do_cache and placa_do_cache != placa:
            # Veio de outro computador: nao serve aqui.
            os.chmod(CACHE_PS1, 0o666)
            os.remove(CACHE_PS1)
            return -1
        return os.path.getsize(CACHE_PS1)
    except OSError:
        return -1


def fixar_cache_ps1(tamanho_antes, placa):
    """Depois do jogo de PS1: se o cache nao cresceu, trava contra regravacao.
    Devolve True se travou agora."""
    try:
        if not os.path.isfile(CACHE_PS1) or tamanho_antes < 0:
            return False
        if os.path.getsize(CACHE_PS1) != tamanho_antes:
            return False                      # aprendeu coisa nova: deixa livre
        if not os.access(CACHE_PS1, os.W_OK):
            return False                      # ja estava travado
        os.chmod(CACHE_PS1, 0o444)
        with open(_marca_do_cache_ps1(), "w", encoding="utf-8") as f:
            f.write(placa)
        return True
    except OSError:
        return False


def chaves_gerenciadas_pelo_arena():
    """Toda chave de opcao de nucleo que o ARENA pode escrever, em qualquer
    nota, modo ou excecao. So estas o ARENA controla; as outras sao do aluno
    (mudadas no menu do RetroArch) e ficam como estao."""
    dados = carregar_graficos()
    chaves = set()
    for nucleo in dados.get("nucleos", {}).values():
        chaves.update(nucleo.get("sempre", {}))
        for bloco in nucleo.get("por_nota", []):
            chaves.update(bloco.get("opcoes", {}))
    for opcoes in dados.get("modesto", {}).values():
        if isinstance(opcoes, dict):          # o "_leia" e' texto
            chaves.update(opcoes)
    for excecao in dados.get("excecoes", {}).values():
        for bloco in excecao.get("por_nota", []):
            chaves.update(bloco.get("opcoes", {}))
    # Achado de 02/10/2026: as chaves da tela 4K e as de abaixo do original
    # nao estavam aqui -- e chave que nao esta aqui conta como "mudada pelo
    # aluno no menu" e FICA no arquivo. Saiu da TV 4K, o N64 continuava em
    # 2x; saiu do minimo, o Dreamcast continuaria em 320x240.
    for opcoes in dados.get("tela_4k", {}).get("nucleos", {}).values():
        chaves.update(opcoes)
    for nivel in NIVEIS_ABAIXO:
        for opcoes in dados.get("abaixo_do_original", {}).get(nivel, {}).values():
            chaves.update(opcoes)
    for lista in CHAVE_BIOS.values():
        chaves.update(lista)
    chaves.add("swanstation_MemoryCards_Card1Type")
    return chaves


_PADRAO_OPCAO = re.compile(r'^([A-Za-z0-9_.\-]+)\s*=\s*"(.*)"\s*$')


def _ler_opcoes(caminho):
    opcoes = {}
    try:
        with open(caminho, "r", encoding="utf-8", errors="replace") as arquivo:
            for linha in arquivo:
                m = _PADRAO_OPCAO.match(linha.strip())
                if m:
                    opcoes[m.group(1)] = m.group(2)
    except OSError:
        pass
    return opcoes


def opcoes_do_aluno():
    """Opcoes de nucleo que NAO sao do ARENA, para nao apagar o que o aluno
    mudou no menu do RetroArch. Le os .opt antigos de cada nucleo (onde o
    RetroArch guardava antes do ARENA ligar global_core_options) e, por
    cima, o arquivo global atual. Chaves "duckstation_*" (lixo antigo, o
    nucleo nao conhece) ficam de fora."""
    juntas = {}
    pasta_config = os.path.join(PASTA_RETROARCH, "config")
    try:
        nucleos = sorted(os.listdir(pasta_config))
    except OSError:
        nucleos = []
    for nucleo in nucleos:
        juntas.update(_ler_opcoes(os.path.join(pasta_config, nucleo, nucleo + ".opt")))
    juntas.update(_ler_opcoes(ARQUIVO_OPCOES_CORE))
    gerenciadas = chaves_gerenciadas_pelo_arena()
    return {k: v for k, v in juntas.items()
            if k not in gerenciadas and not k.startswith("duckstation_")}


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
    ("Xbox 360, One e Series", "xinput", "Plugou, funcionou. Não precisa de nada."),
    ("PlayStation 4 e 5", "xinput",
     "Por cabo USB funciona direto. Por Bluetooth também, depois de parear."),
    ("PlayStation 3", "dinput",
     "Precisa do driver SCP ou DsHidMini no Windows. Depois disso funciona."),
    ("Nintendo Switch Pro", "xinput",
     "Por cabo USB funciona. Por Bluetooth, pareie antes pelo Windows."),
    ("Joy-Con avulso", "dinput",
     "Funciona como controle pequeno. Mapeie os botoes na mao."),
    ("Steam Controller", "xinput",
     "Deixe o Steam aberto: ele converte para XInput sozinho."),
    ("Genericos e arcade stick", "dinput",
     "Quase todos funcionam. Se não aparecer, troque o driver para dinput."),
    ("Teclado", "-", "Sempre funciona como jogador 1, mesmo com controle plugado."),
]




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
    # Wii pelo Dolphin: o que cada botao do controle vira (Wii Remote +
    # Nunchuk), igual a escrever_config_dolphin.
    "wii": {"b": "A", "a": "B (gatilho, no RT)", "y": "1", "x": "2",
            "l": "C (Nunchuk)", "r": "Balançar", "l2": "Z (Nunchuk)",
            "r2": "B (gatilho)", "start": "+", "select": "-"},
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
XInput = true
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


# Controles do PCSX2 por jogo. Conferido no codigo-fonte do PCSX2
# (pcsx2/SIO/Sio.cpp, 25/09/2026): com o multitap na porta 1, os jogadores
# 1 a 4 ficam em 1A, 1B, 1C, 1D = secoes Pad1, Pad3, Pad4, Pad5 (o Pad2 e' a
# porta 2). A chave do adaptador e' [Pad] MultitapPort1 (Pad.cpp).
PCSX2_BOTOES_SDL = [
    ("Up", "DPadUp"), ("Down", "DPadDown"), ("Left", "DPadLeft"), ("Right", "DPadRight"),
    ("Cross", "A"), ("Circle", "B"), ("Square", "X"), ("Triangle", "Y"),
    ("L1", "LeftShoulder"), ("R1", "RightShoulder"),
    ("L2", "+LeftTrigger"), ("R2", "+RightTrigger"),
    ("L3", "LeftStick"), ("R3", "RightStick"), ("Select", "Back"), ("Start", "Start"),
    ("LUp", "-LeftY"), ("LDown", "+LeftY"), ("LLeft", "-LeftX"), ("LRight", "+LeftX"),
    ("RUp", "-RightY"), ("RDown", "+RightY"), ("RLeft", "-RightX"), ("RRight", "+RightX"),
    ("LargeMotor", "LargeMotor"), ("SmallMotor", "SmallMotor"),
]
# Mesmas teclas do resto do ARENA (setas, X, Z, S, A, Q, W, Enter, Shift).
PCSX2_BOTOES_TECLADO = [
    ("Up", "Up"), ("Down", "Down"), ("Left", "Left"), ("Right", "Right"),
    ("Cross", "Z"), ("Circle", "X"), ("Square", "A"), ("Triangle", "S"),
    ("L1", "Q"), ("R1", "W"), ("L2", "E"), ("R2", "R"),
    ("Select", "Shift"), ("Start", "Return"),
]


def controles_pcsx2(jogadores, controles_xinput):
    """Blocos [Pad]/[PadN] do PCSX2 para esta partida.

    Ate 2 jogadores: Pad1 e Pad2, sem adaptador. 3 ou mais: multitap na
    porta 1, jogadores em Pad1, Pad3, Pad4, Pad5. Os controles entram na
    ordem; o teclado e' o primeiro jogador sem controle (regra do ARENA).

    'controles_xinput': numeros (0 a 3) dos controles XInput ligados. Usa a
    fonte XInput do PCSX2 ("XInput-N", N = numero do Windows) e nao a SDL:
    o "SDL-N" muda quando um controle sem fio reconecta, e no Crash Nitro
    Kart (25/09/2026) so o 1o controle funcionou. Nomes dos botoes
    conferidos em pcsx2/Input/XInputSource.cpp (iguais aos da SDL)."""
    controles_xinput = list(controles_xinput or [])
    controles_ligados = len(controles_xinput)
    multitap = int(jogadores or 2) > 2
    secoes = [1, 3, 4, 5] if multitap else [1, 2]
    linhas = ["[Pad]", "MultitapPort1 = %s" % ("true" if multitap else "false"),
              "MultitapPort2 = false", ""]
    teclado_usado = False
    for n in range(1, 9):
        linhas.append("[Pad%d]" % n)
        if n not in secoes:
            linhas += ["Type = None", ""]
            continue
        jogador = secoes.index(n)
        if jogador < controles_ligados:
            fonte = "XInput-%d/" % controles_xinput[jogador]
            botoes = PCSX2_BOTOES_SDL
        elif not teclado_usado:
            teclado_usado = True
            fonte = "Keyboard/"
            botoes = PCSX2_BOTOES_TECLADO
        else:
            linhas += ["Type = None", ""]
            continue
        linhas += ["Type = DualShock2", "Deadzone = 0.10", "AxisScale = 1.33",
                   "LargeMotorScale = 1.00", "SmallMotorScale = 1.00"]
        linhas += ["%s = %s%s" % (botao, fonte, nome) for botao, nome in botoes]
        linhas.append("")
    return linhas


# Motor de video do PCSX2: chave "Renderer" de [EmuCore/GS], com os numeros
# do proprio PCSX2 (enum GSRendererType, pcsx2/Config.h: Auto = -1,
# DX11 = 3, VK = 14, DX12 = 15). No automatico, o PCSX2 2.8 escolhe
# DirectX 12 em placa Intel ou AMD com nivel de recurso 12_0
# (D3D::GetPreferredRenderer, conferido no codigo-fonte em 01/10/2026) --
# suspeito dos graficos piscando no Celeron (Intel UHD, driver de 2021):
# a escolha fica na tela do ARENA para testar em um clique.
MOTORES_PCSX2 = {"automatico": "-1", "d3d11": "3", "d3d12": "15", "vulkan": "14"}


# Os valores-padrao do PCSX2 para o que ele mesmo avisa que "pode quebrar a
# renderizacao" quando muda (ver escrever_config_pcsx2): mipmapping ligado,
# trilinear automatico, filtro bilinear do PS2, leitura da placa "Precisa".
PCSX2_SEGUROS = {"hw_mipmap": "true", "TriFilter": "-1", "filter": "2", "HWDownloadMode": "0"}


def aviso_sem_gravar(emulador, falha):
    """A configuracao do emulador nao gravou (pasta somente leitura, disco
    cheio...): ele abre com a que ja tinha, e a janela preta diz por que.
    Antes o ARENA ficava calado -- e o controle ou a imagem do jogo
    "nao obedeciam" sem ninguem saber o motivo (auditoria 3, 07/10/2026)."""
    print("[ARENA] AVISO: nao consegui gravar a configuracao do %s (%s). "
          "Ele abre com a que ja tinha." % (emulador, falha))


def escrever_config_pcsx2(caminho_executavel, ultra=False, nota=None,
                          nota_gpu=None, modesto=False, preset=None,
                          jogadores=2, controles_xinput=(0, 1),
                          cartoes=("Mcd001.ps2", "Mcd002.ps2"), integrada=None,
                          motor="automatico", abaixo=""):
    """Escreve o bloco de controle, teclas e qualidade grafica do PCSX2.

    Preserva tudo o que ja estiver no arquivo fora desses blocos - em
    especial a BIOS, que o aluno configura uma vez pela tela do programa.

    O PCSX2 so grava [EmuCore/GS] no arquivo quando a pessoa muda algo pela
    tela de Configuracoes - abrir um jogo sozinho, mesmo rodando de
    verdade, nao cria o bloco (confirmado testando: 20s de corrida real
    sem nenhuma linha nova). Por isso este bloco e' escrito do zero, com
    as mesmas chaves que o PCSX2 2.8 usa por dentro (upscale_multiplier,
    MaxAnisotropy, texture_preloading - conferidas no PCSX2.ini que ele gera; os nomes antigos do
    PCSX2, nao inventadas), em vez de so completar um arquivo existente
    como e' feito com o Xenia/RPCS3.

    'preset': "leve", "bonito" ou None/"automatico" (decide pela nota da
    placa de video, mesma logica do Xenia/RPCS3). Passe 'nota' e/ou
    'nota_gpu' pra habilitar o ajuste automatico; sem nenhuma nota, so
    grava controle e teclas (comportamento antigo).
    """
    pasta = os.path.dirname(caminho_executavel)
    destino = os.path.join(pasta, "inis", "PCSX2.ini")

    nossos = {"[Pad]", "[InputSources]", "[Hotkeys]", "[UI]"}
    nossos |= {"[Pad%d]" % n for n in range(1, 9)}
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

    linhas_gs = []
    alvo_nota = nota_gpu if nota_gpu is not None else nota
    if alvo_nota is not None:
        if preset == "leve":
            fraco, forte = True, False
        elif preset == "bonito":
            fraco, forte = False, True
        else:
            fraco = modesto or alvo_nota <= 2
            forte = alvo_nota >= 4 and not modesto
        if abaixo in NIVEIS_ABAIXO:
            fraco, forte = True, False      # abaixo do original comeca no mais leve

        # Placa INTEGRADA no automatico (decisao do Rafael, 30/09/2026): o
        # Celeron otimizado roda PS2 com 4 jogadores, mas com graficos
        # piscando/distorcendo -- e a placa integrada recebia 2x de
        # resolucao, filtro 4x e a mistura de cores que estivesse no
        # arquivo (estava "Maxima", 5, escolhida na tela do PCSX2). Agora:
        # resolucao nativa e mistura "Basica" (o padrao do proprio PCSX2).
        # Placa dedicada e o preset "Mais bonito" continuam como eram.
        integrada_auto = (integrada is True and preset not in ("leve", "bonito")
                          and not fraco and not forte)

        # Pre-carga de texturas sempre "Completa" (2), o padrao do PCSX2.
        # Ate 02/10/2026 o "Mais leve" gravava 0 ("Nenhuma"), achando que
        # aliviava -- e o proprio PCSX2 descreve a completa assim: "Melhora o
        # desempenho na maioria dos jogos" (avisa "Texture Preloading is not
        # Full, this may reduce performance").
        pre_carga = "2"
        if fraco:
            # Resolucao nativa do PS2, sem suavizar nada - o mais leve
            # possivel, para quando ate o perfil normal engasga.
            escala, aniso = "1", "0"
        elif forte:
            escala, aniso = "4", "16"
        elif integrada_auto:
            escala, aniso = "1", "0"
        else:
            escala, aniso = "2", "4"

        # Nomes do PCSX2 2.8 (conferidos no PCSX2.ini que ele mesmo gera,
        # 26/09/2026). Antes o ARENA escrevia "UpscaleMultiplier" e
        # "TexturePreloading", que nao existem: o seletor nunca teve efeito.
        linhas_gs += ["upscale_multiplier = " + escala,
                      "MaxAnisotropy = " + aniso,
                      "texture_preloading = " + pre_carga]
        # Mistura de cores (accurate_blending_unit: 0 minima, 1 basica --
        # padrao do PCSX2 --, 2 media, 3 alta, 4 total, 5 maxima): "Basica" no
        # leve, no grafico original e na placa integrada automatica. Fora
        # disso o ARENA nao mexe: vale o que estiver na tela do PCSX2.
        if fraco or integrada_auto:
            linhas_gs.append("accurate_blending_unit = 1")

    # Valores que o PROPRIO PCSX2 chama de seguros, gravados sempre, em
    # qualquer qualidade. Achado de 02/10/2026 (Rafael, Crash Nitro Kart a
    # 3: o mapa do quarto quadro coberto de lixo e o "P1" em cima do kart
    # virando blocos vermelhos e pretos). Mipmapping e trilinear tinham sido
    # mudados na tela do PCSX2, e o registro dele avisava a cada jogo: "O
    # mapeamento de mip esta desativado. Isso pode prejudicar a
    # renderizacao em alguns jogos" e "A filtragem trilinear nao esta
    # definida como automatica. Isto pode quebrar a renderizacao". O Crash
    # Nitro Kart e' "perfeito" no banco de jogos do PCSX2 -- com estes
    # valores. Os avisos que o PCSX2 da' estao em testes\teste_pcsx2_seguro.py.
    linhas_gs += ["%s = %s" % par for par in PCSX2_SEGUROS.items()]
    if abaixo == "minimo":
        # Bonecos de papelao: a mistura de cores "Minima" (0) erra efeitos de
        # transparencia, mas e' a que menos pesa na placa.
        linhas_gs.append("accurate_blending_unit = 0")
    elif "accurate_blending_unit = 1" not in linhas_gs and re.search(
            r"^accurate_blending_unit = 0\s*$", "\n".join(guardar), re.M):
        # "Minima" (0): "Blending Accuracy is below Basic, this may break
        # effects in some games". Fora do minimo, abaixo da basica nunca.
        linhas_gs.append("accurate_blending_unit = 1")
    # Quadro repetido nao e' redesenhado (so no minimo; o padrao e' desligado).
    linhas_gs.append("SkipDuplicateFrames = %s" % ("true" if abaixo == "minimo" else "false"))

    if ultra:
        linhas_gs += ["VsyncEnable = true", "OsdShowSpeed = false"]
    # O ARENA manda no motor de video: "automatico" grava -1 (o PCSX2
    # escolhe), para a volta ao automatico pela tela do ARENA valer.
    linhas_gs.append("Renderer = " + MOTORES_PCSX2.get(motor, "-1"))

    # [EmuCore/GS] nao e' mais apagado inteiro: so as chaves do ARENA mudam,
    # o resto do que o PCSX2 guarda ali fica.
    chaves_gs = dict(l.split(" = ", 1) for l in linhas_gs)
    extra = []
    # SetupWizardIncomplete = false sempre: no modo portatil, sem isto o
    # PCSX2 abre o assistente de primeira vez e fica esperando cliques.
    # SettingsVersion = 1: sem ela o PCSX2 acha que a configuracao e' de
    # outra versao e VOLTA TUDO AO PADRAO ao abrir (pcsx2/VMManager.cpp,
    # CheckSettingsVersion, SETTINGS_VERSION = 1) -- era por isso que o
    # teclado virava o jogador 1 e os controles sumiam (26/09/2026).
    extra += ["", "[UI]", "SettingsVersion = 1", "SetupWizardIncomplete = false"]
    if ultra:
        extra += ["StartFullscreen = true", "ConfirmShutdown = false"]

    # Os [Pad1]/[Pad2] fixos do BLOCO_PCSX2 dao lugar aos gerados por jogo.
    fixo = BLOCO_PCSX2[BLOCO_PCSX2.index("[InputSources]"):]
    texto = "\n".join(guardar + [""] + controles_pcsx2(jogadores, controles_xinput)
                      + fixo.splitlines() + extra) + "\n"
    # Pastas que o modo portatil precisa. A BIOS NAO e' escolhida pelo ARENA:
    # com [Filenames] BIOS vazio o PCSX2 acha sozinho uma que serve. Forcar a
    # primeira em ordem alfabetica (achado 26/09/2026, por eliminacao com
    # fotos -- testes\teste_pcsx2_bissecao.py) pegava uma v1.60 com a qual o
    # Crash Nitro Kart ficava em tela preta, "Velocidade 0%".
    texto = _trocar_chaves_ini(texto, "Folders", {"Bios": "bios", "MemoryCards": "memcards"})
    if chaves_gs:
        texto = _trocar_chaves_ini(texto, "EmuCore/GS", chaves_gs)
    # Abaixo do original: o processador do PS2 emulado anda mais devagar
    # (EECycleRate -1 = 75%, -2 = 60%; EECycleSkip 1 e 2 = "subclock" leve e
    # moderado). O computador fraco aguenta; em cena pesada o JOGO pode ficar
    # mais lento (nao a imagem). Fora disso, sempre o padrao (0), para a
    # volta ao normal valer -- e o aviso do PCSX2 ("pode travar ou deixar o
    # jogo lento") so fica desligado nesses dois niveis, que a tela do ARENA
    # ja explica.
    ciclos = {"leve": ("-1", "1"), "minimo": ("-2", "2")}.get(abaixo, ("0", "0"))
    texto = _trocar_chaves_ini(texto, "EmuCore/Speedhacks",
                               {"EECycleRate": ciclos[0], "EECycleSkip": ciclos[1]})
    texto = _trocar_chaves_ini(texto, "EmuCore", {
        "WarnAboutUnsafeSettings": "false" if abaixo in NIVEIS_ABAIXO else "true"})
    texto = _trocar_chaves_ini(texto, "MemoryCards", {
        "Slot1_Enable": "true", "Slot1_Filename": cartoes[0],
        "Slot2_Enable": "true", "Slot2_Filename": cartoes[1]})

    try:
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        gravar_atomico(destino, texto)
        return destino
    except OSError as falha:
        aviso_sem_gravar("PCSX2", falha)
        return None


# ---------------------------------------------------------------------------
# Dolphin (GameCube e Wii): pasta portatil e controles
# ---------------------------------------------------------------------------
# Nomes conferidos no codigo-fonte do Dolphin (25/09/2026), nao inventados:
#   XInput.cpp  -> "Button A", "Pad N", "Start", "Back", "Shoulder L",
#                  "Trigger L", "Thumb L", "Guide", eixos "Left X"/"Left Y"
#   GCPadEmu.h  -> grupos "Buttons", "Main Stick", "C-Stick", "Triggers",
#                  "D-Pad"; botoes "A","B","X","Y","Z","Start"; "L","R",
#                  "L-Analog","R-Analog"
#   WiimoteEmu.h/Nunchuk.h -> "Buttons" A,B,1,2,-,+,Home; "D-Pad"; "Shake";
#                  "IR"; Nunchuk "Buttons" C,Z e "Stick"
#   Attachments.cpp -> "Extension = Nunchuk" e "Nunchuk/<grupo>/<botao>"
#   SI_Device.h -> SIDEVICE_GC_CONTROLLER = 6, SIDEVICE_NONE = 0
# Sem o portable.txt o Dolphin grava configuracao e saves em Documentos,
# FORA da pasta do ARENA -- contra a regra do pen drive.

DOLPHIN_ENTRADA_XINPUT = {
    "A": "`Button A`", "B": "`Button B`", "X": "`Button X`", "Y": "`Button Y`",
    "Start": "Start", "Back": "Back", "Guide": "Guide",
    "LB": "`Shoulder L`", "RB": "`Shoulder R`", "LT": "`Trigger L`", "RT": "`Trigger R`",
    "cima": "`Pad N`", "baixo": "`Pad S`", "esquerda": "`Pad W`", "direita": "`Pad E`",
    "esq_cima": "`Left Y+`", "esq_baixo": "`Left Y-`",
    "esq_esquerda": "`Left X-`", "esq_direita": "`Left X+`",
    "dir_cima": "`Right Y+`", "dir_baixo": "`Right Y-`",
    "dir_esquerda": "`Right X-`", "dir_direita": "`Right X+`",
}

# Mesmas teclas do resto do ARENA (setas, X, Z, S, A, Q, W, Enter, Shift).
DOLPHIN_ENTRADA_TECLADO = {
    "A": "X", "B": "Z", "X": "S", "Y": "A", "Start": "RETURN", "Back": "RSHIFT",
    "Guide": "", "LB": "Q", "RB": "W", "LT": "E", "RT": "R",
    "cima": "UP", "baixo": "DOWN", "esquerda": "LEFT", "direita": "RIGHT",
    "esq_cima": "UP", "esq_baixo": "DOWN", "esq_esquerda": "LEFT", "esq_direita": "RIGHT",
    "dir_cima": "I", "dir_baixo": "K", "dir_esquerda": "J", "dir_direita": "L",
}


def _linhas_gcpad(entrada):
    """Controle de GameCube num controle comum (formato Xbox)."""
    e = entrada
    return [
        "Buttons/A = " + e["A"], "Buttons/B = " + e["B"],
        "Buttons/X = " + e["X"], "Buttons/Y = " + e["Y"],
        "Buttons/Z = " + e["RB"], "Buttons/Start = " + e["Start"],
        "Main Stick/Up = " + e["esq_cima"], "Main Stick/Down = " + e["esq_baixo"],
        "Main Stick/Left = " + e["esq_esquerda"], "Main Stick/Right = " + e["esq_direita"],
        "C-Stick/Up = " + e["dir_cima"], "C-Stick/Down = " + e["dir_baixo"],
        "C-Stick/Left = " + e["dir_esquerda"], "C-Stick/Right = " + e["dir_direita"],
        "Triggers/L = " + e["LT"], "Triggers/R = " + e["RT"],
        "Triggers/L-Analog = " + e["LT"], "Triggers/R-Analog = " + e["RT"],
        "D-Pad/Up = " + e["cima"], "D-Pad/Down = " + e["baixo"],
        "D-Pad/Left = " + e["esquerda"], "D-Pad/Right = " + e["direita"],
    ]


def _linhas_wiimote(entrada):
    """Wii Remote + Nunchuk num controle comum. O analogico esquerdo e' o
    Nunchuk; o direito aponta (cursor dos menus); RB balanca o controle.
    Serve para Mario Kart Wii, Smash Brawl e New Super Mario Bros. Wii --
    os tres aceitam Wii Remote + Nunchuk, sem precisar apontar de verdade."""
    e = entrada
    return [
        "Buttons/A = " + e["A"], "Buttons/B = " + e["RT"],
        "Buttons/1 = " + e["X"], "Buttons/2 = " + e["Y"],
        "Buttons/- = " + e["Back"], "Buttons/+ = " + e["Start"],
        "Buttons/Home = " + e["Guide"],
        "D-Pad/Up = " + e["cima"], "D-Pad/Down = " + e["baixo"],
        "D-Pad/Left = " + e["esquerda"], "D-Pad/Right = " + e["direita"],
        "IR/Up = " + e["dir_cima"], "IR/Down = " + e["dir_baixo"],
        "IR/Left = " + e["dir_esquerda"], "IR/Right = " + e["dir_direita"],
        "Shake/X = " + e["RB"], "Shake/Y = " + e["RB"], "Shake/Z = " + e["RB"],
        "Extension = Nunchuk",
        "Nunchuk/Buttons/C = " + e["LB"], "Nunchuk/Buttons/Z = " + e["LT"],
        "Nunchuk/Stick/Up = " + e["esq_cima"], "Nunchuk/Stick/Down = " + e["esq_baixo"],
        "Nunchuk/Stick/Left = " + e["esq_esquerda"], "Nunchuk/Stick/Right = " + e["esq_direita"],
    ]


def _trocar_chaves_ini(texto, secao, chaves):
    """Troca (ou acrescenta) chaves numa secao de um .ini, mantendo o resto."""
    linhas = texto.splitlines()
    inicio = next((i for i, l in enumerate(linhas) if l.strip() == "[%s]" % secao), None)
    if inicio is None:
        linhas += ["", "[%s]" % secao] + ["%s = %s" % kv for kv in chaves.items()]
        return "\n".join(linhas) + "\n"
    fim = next((i for i in range(inicio + 1, len(linhas))
                if linhas[i].strip().startswith("[")), len(linhas))
    faltam = dict(chaves)
    for i in range(inicio + 1, fim):
        chave = linhas[i].split("=", 1)[0].strip()
        if chave in faltam:
            linhas[i] = "%s = %s" % (chave, faltam.pop(chave))
    linhas[fim:fim] = ["%s = %s" % kv for kv in faltam.items()]
    return "\n".join(linhas) + "\n"


def console_do_disco_dolphin(caminho_jogo):
    """'wii' ou 'gamecube', lido de dentro do arquivo (None se nao der).

    .rvz/.wia: o tipo do disco fica no byte 0x48 (1 = GameCube, 2 = Wii),
    conforme docs/WiaAndRvz.md do Dolphin -- conferido nos 5 jogos da pasta.
    .iso/.gcm: a marca do Wii fica em 0x18, a do GameCube em 0x1C.
    .wbfs: so existe para Wii."""
    extensao = os.path.splitext(caminho_jogo)[1].lower()
    if extensao == ".wbfs":
        return "wii"
    try:
        with open(caminho_jogo, "rb") as arquivo:
            cabeca = arquivo.read(0x50)
    except OSError:
        return None
    if cabeca[:3] in (b"RVZ", b"WIA") and len(cabeca) >= 0x4C:
        return {1: "gamecube", 2: "wii"}.get(int.from_bytes(cabeca[0x48:0x4C], "big"))
    if cabeca[0x18:0x1C] == bytes.fromhex("5D1C9EA3"):
        return "wii"
    if cabeca[0x1C:0x20] == bytes.fromhex("C2339F3D"):
        return "gamecube"
    return None


def opcoes_de_imagem_dolphin(nota=None, nota_gpu=None, modesto=False, ultra=False,
                             preset=None, abaixo=""):
    """O que o ARENA ajusta no Dolphin, por arquivo e secao.

    Achado de 30/09/2026: o Dolphin externo (GameCube e Wii) so recebia
    controles -- o GFX.ini estava VAZIO, e o modo grafico original e o ultra
    nao chegavam nele. Nomes conferidos no codigo-fonte do Dolphin
    (Config/GraphicsSettings.cpp, Config/MainSettings.cpp e
    VideoCommon/VideoConfig.h) e no Dolphin.exe da pasta (5.0-12188):
      - ShaderCompilationMode: 0 sincrono (PADRAO do Dolphin: trava a cada
        efeito novo, enquanto compila), 1 so ubershaders, 2 hibrido
        (ubershader enquanto compila o definitivo), 3 pula o desenho. Vai o
        2, a mesma decisao ja tomada para o nucleo do Dolphin no RetroArch
        ("async_uber, nao sync_uber" -- CLAUDE.md, secao 5).
      - InternalResolution: 1 = nativa do console; 2 = 2x.
      - MaxAnisotropy: 0 = 1x (sem filtro); 2 = 4x.
      - CPUThread ("Dual Core"): ligado. Ja era o padrao desta versao, mas o
        Dolphin 2509 (setembro de 2025) passou a vir DESLIGADO no computador;
        fixar aqui impede que uma atualizacao deixe o GameCube com um nucleo
        so no Celeron. Os jogos que precisam de um nucleo so continuam
        protegidos: as regras por jogo do proprio Dolphin valem por cima.
    Mesma escolha por placa do PCSX2/Xenia/RPCS3: 'preset' da aba
    Emuladores ("leve"/"bonito") ou, no automatico, a nota da placa.

    'abaixo' ("leve"/"minimo", 02/10/2026), nomes conferidos no Dolphin.exe:
      - Core/OverclockEnable + Overclock: o processador do GameCube emulado
        a 80% (leve) ou 60% (minimo). O computador aguenta; em cena pesada o
        JOGO pode ficar mais lento.
      - minimo: Settings/DisableFog (sem neblina), Hacks/EFBAccessEnable =
        False (pula a leitura da imagem pelo processador -- erra mira e
        efeitos em alguns jogos) e ShaderCompilationMode 3 (o objeto ainda
        sem desenho pronto nao aparece, em vez de travar).
    Fora desses niveis, sempre os padroes do Dolphin, para a volta valer."""
    niveis = niveis_abaixo_ate(abaixo)
    gfx_settings = {"ShaderCompilationMode": "3" if "minimo" in niveis else "2",
                    "DisableFog": "True" if "minimo" in niveis else "False"}
    gfx_melhorias = {}
    gfx_truques = {"EFBAccessEnable": "False" if "minimo" in niveis else "True"}
    alvo = nota_gpu if nota_gpu is not None else nota
    if niveis:
        modesto = True
    if alvo is not None or modesto or preset in ("leve", "bonito"):
        if niveis:
            forte = False
        elif preset == "leve":
            forte = False
        elif preset == "bonito":
            forte = True
        else:
            forte = (alvo or 0) >= 4 and not modesto
        gfx_settings["InternalResolution"] = "2" if forte else "1"
        gfx_settings["MSAA"] = "1"
        gfx_settings["SSAA"] = "False"
        gfx_melhorias["MaxAnisotropy"] = "2" if forte else "0"
    # Ultra: tela cheia e sem a pergunta "parar o jogo?". Sem ultra, nada
    # aqui: o que a pessoa escolheu na tela do Dolphin fica (a volta do que
    # o ultra mudou e' feita em escrever_config_dolphin, pela anotacao).
    principal = {"Core": {"CPUThread": "True",
                          "OverclockEnable": "True" if niveis else "False",
                          "Overclock": {"leve": "0.8", "minimo": "0.6"}.get(abaixo, "1.0")}}
    if ultra:
        principal["Display"] = {"Fullscreen": "True"}
        principal["Interface"] = {"ConfirmStop": "False"}
    gfx = {"Settings": gfx_settings, "Hacks": gfx_truques}
    if gfx_melhorias:
        gfx["Enhancements"] = gfx_melhorias
    return {"GFX.ini": gfx, "Dolphin.ini": principal}


ANOTACAO_ULTRA_DOLPHIN = "arena_ultra_antes.json"
CHAVES_ULTRA_DOLPHIN = (("Display", "Fullscreen", "False"),
                        ("Interface", "ConfirmStop", "True"))   # padrao do Dolphin


def _anotar_ou_devolver_ultra_dolphin(pasta_config, ultra, secoes):
    """Ultra liga a tela cheia do Dolphin; desligado, devolve o que a pessoa
    tinha antes -- nem fica grudado, nem apaga escolha feita na tela dele.

    Ao ligar, anota os valores de antes (so na primeira vez: ligado de novo,
    a anotacao original continua). Ao desligar, se houver anotacao, poe os
    valores anotados em 'secoes' e apaga a anotacao."""
    anotacao = os.path.join(pasta_config, ANOTACAO_ULTRA_DOLPHIN)
    if ultra:
        if os.path.exists(anotacao):
            return
        try:
            with open(os.path.join(pasta_config, "Dolphin.ini"), encoding="utf-8",
                      errors="replace") as arquivo:
                texto = arquivo.read()
        except OSError:
            texto = ""
        antes = {}
        for secao, chave, padrao in CHAVES_ULTRA_DOLPHIN:
            antes[chave] = _valor_ini(texto, secao, chave) or padrao
        gravar_atomico(anotacao, json.dumps(antes, ensure_ascii=False))
        return
    try:
        with open(anotacao, encoding="utf-8") as arquivo:
            antes = json.load(arquivo)
    except (OSError, ValueError):
        return
    for secao, chave, padrao in CHAVES_ULTRA_DOLPHIN:
        secoes.setdefault(secao, {})[chave] = str(antes.get(chave) or padrao)
    try:
        os.remove(anotacao)
    except OSError:
        pass


def _valor_ini(texto, secao, chave):
    """Valor de uma chave numa secao de um .ini (ou None)."""
    dentro = False
    for linha in texto.splitlines():
        limpo = linha.strip()
        if limpo.startswith("[") and limpo.endswith("]"):
            dentro = limpo == "[%s]" % secao
        elif dentro and "=" in limpo and limpo.split("=", 1)[0].strip() == chave:
            return limpo.split("=", 1)[1].strip()
    return None


def escrever_config_dolphin(caminho_executavel, controles_xinput, teclado=True,
                            console="gamecube", nota=None, nota_gpu=None,
                            modesto=False, ultra=False, preset=None, abaixo=""):
    """Deixa o Dolphin portatil e escreve os controles de GameCube e Wii,
    e a imagem (ver opcoes_de_imagem_dolphin).

    'controles_xinput': numeros (0 a 3) dos controles XInput ligados.
    Cada um vira um jogador, na ordem; o teclado e' o primeiro jogador sem
    controle (a mesma regra do resto do ARENA). Devolve a pasta de
    configuracao, ou None se nao deu para gravar.

    'console': 'wii' liga so os Wii Remotes; 'gamecube', so os controles de
    GameCube. Os dois juntos NAO: achado com o Mario Kart Wii (25/09/2026),
    que aceita controle de GameCube -- cada controle virava DOIS jogadores
    (o G7 mexia o jogador 1 e o 3)."""
    wii = console == "wii"
    pasta_exe = os.path.dirname(caminho_executavel)
    pasta_config = os.path.join(pasta_exe, "User", "Config")
    try:
        portatil = os.path.join(pasta_exe, "portable.txt")
        if not os.path.exists(portatil):
            with open(portatil, "w", encoding="utf-8") as arquivo:
                arquivo.write("Criado pelo ARENA: guarda tudo do Dolphin nesta pasta.\n")
        os.makedirs(pasta_config, exist_ok=True)

        jogadores = [("XInput/%d/Gamepad" % n, DOLPHIN_ENTRADA_XINPUT)
                     for n in list(controles_xinput)[:4]]
        if teclado and len(jogadores) < 4:
            jogadores.append(("DInput/0/Keyboard Mouse", DOLPHIN_ENTRADA_TECLADO))

        gcpad, wiimote, portas = [], [], {}
        for porta in range(4):
            gcpad.append("[GCPad%d]" % (porta + 1))
            wiimote.append("[Wiimote%d]" % (porta + 1))
            if porta < len(jogadores):
                dispositivo, entrada = jogadores[porta]
                gcpad += ["Device = " + dispositivo] + _linhas_gcpad(entrada)
                wiimote += (["Source = %d" % (1 if wii else 0), "Device = " + dispositivo]
                            + _linhas_wiimote(entrada))
                # 6 = controle de GameCube; 0 = porta vazia (no Wii).
                portas["SIDevice%d" % porta] = "0" if wii else "6"
            else:
                wiimote.append("Source = 0")          # sem Wii Remote
                portas["SIDevice%d" % porta] = "0"   # porta vazia
            gcpad.append("")
            wiimote.append("")

        cabecalho = ["# Gerado pelo ARENA a cada jogo (servidor\\graficos.py).", ""]
        gravar_atomico(os.path.join(pasta_config, "GCPadNew.ini"),
                       "\n".join(cabecalho + gcpad) + "\n")
        gravar_atomico(os.path.join(pasta_config, "WiimoteNew.ini"),
                       "\n".join(cabecalho + wiimote) + "\n")

        imagem = opcoes_de_imagem_dolphin(nota, nota_gpu, modesto, ultra, preset, abaixo)
        imagem["Dolphin.ini"].setdefault("Core", {}).update(portas)
        _anotar_ou_devolver_ultra_dolphin(pasta_config, ultra, imagem["Dolphin.ini"])
        for nome_arquivo, secoes in imagem.items():
            caminho = os.path.join(pasta_config, nome_arquivo)
            try:
                with open(caminho, "r", encoding="utf-8", errors="replace") as arquivo:
                    texto = arquivo.read()
            except OSError:
                texto = ""
            # So as chaves do ARENA mudam; o resto do arquivo fica.
            for secao, chaves in secoes.items():
                texto = _trocar_chaves_ini(texto, secao, chaves)
            gravar_atomico(caminho, texto)
        return pasta_config
    except OSError as falha:
        aviso_sem_gravar("Dolphin", falha)
        return None


# ---------------------------------------------------------------------------
# PS2 pela rede: "system link" original, via PCSX2 (DEV9)
# ---------------------------------------------------------------------------
# Diferente do RetroArch, o PS2 nao tem netplay generico: o PCSX2 emula a
# placa de rede de verdade (DEV9) e e' o proprio JOGO que conversa pela
# rede, do jeito que faria em dois PS2 fisicos ligados por cabo ou num
# mesmo roteador. So vale pros jogos que ja saiam com essa funcao (existem
# uns 56 titulos conhecidos - a lista em consoles.json comeca curta, com
# so o que foi testado de verdade, e cresce aos poucos).
#
# O modo que funciona pros dois lados (hospedar OU entrar) precisa do
# driver Npcap ou WinPcap - instalar pede administrador do Windows, contra
# a regra do ARENA de nunca pedir isso sozinho. Por isso e' opcional: o
# ARENA so DETECTA se ja esta instalado (isso nao pede admin nenhum, so
# confere se o arquivo do driver existe) e configura o PCSX2 de acordo.
# Sem o driver, ainda da pra ENTRAR (nao hospedar) numa partida de outra
# maquina que ja tenha o driver, ou de um PS2 de verdade - modo "Sockets"
# do proprio PCSX2, documentado assim pela comunidade dele.

ADAPTADORES_VIRTUAIS_PS2 = (
    "virtualbox", "vmware", "hyper-v", "wsl", "loopback", "tap-windows",
    "npcap loopback", "wi-fi direct", "bluetooth",
)


def jogo_tem_system_link_ps2(plataforma, titulo):
    """Confere se o jogo esta na lista de PS2 com 'system link' de
    verdade (consoles.json -> externo.jogos_system_link). Lista curta de
    proposito: so cresce testando com jogo real, nunca por suposicao."""
    lista = (plataforma.get("externo") or {}).get("jogos_system_link", [])
    titulo_normalizado = (titulo or "").lower()
    return any(nome.lower() in titulo_normalizado for nome in lista)


def npcap_instalado():
    """Confere se o Npcap (ou WinPcap) esta instalado - so olha se os
    arquivos do driver existem, sem precisar de administrador pra isso."""
    raiz_windows = os.environ.get("WINDIR", "C:\\Windows")
    candidatos = [
        os.path.join(raiz_windows, "System32", "Npcap", "wpcap.dll"),
        os.path.join(raiz_windows, "System32", "wpcap.dll"),
    ]
    return any(os.path.isfile(c) for c in candidatos)


def adaptador_de_rede_real():
    """Acha o nome do primeiro adaptador de rede de verdade (Wi-Fi,
    Ethernet) que estiver ligado, ignorando os virtuais - pro PCSX2 saber
    por onde sair pra rede de verdade em vez de um adaptador que nenhum
    colega alcanca (mesma ideia da lista de adaptadores virtuais que a
    descoberta de colegas ja usa, so que aqui por nome, nao por IP)."""
    try:
        saida = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
             "Get-NetAdapter | Where-Object Status -eq 'Up' | "
             "Sort-Object ifIndex | Select-Object -ExpandProperty Name"],
            capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    for linha in saida.stdout.splitlines():
        nome = linha.strip()
        if nome and not any(v in nome.lower() for v in ADAPTADORES_VIRTUAIS_PS2):
            return nome
    return None


def escrever_config_rede_ps2(caminho_executavel):
    """Escreve o bloco [DEV9/Eth] do PCSX2 pra habilitar a rede do PS2 de
    verdade (system link), preservando o resto do arquivo.

    Com o driver instalado: modo 'PCAPBridged', que funciona pros dois
    lados, ligado ao primeiro adaptador de rede de verdade que achar.
    Sem o driver: modo 'Sockets', que so serve pra ENTRAR numa partida
    hospedada por outra maquina com o driver (ou um PS2 de verdade).

    Retorna um dicionario dizendo o que foi configurado, pra tela poder
    avisar certo (com ou sem driver, qual adaptador) - ou None se nao deu
    pra escrever.
    """
    pasta = os.path.dirname(caminho_executavel)
    destino = os.path.join(pasta, "inis", "PCSX2.ini")

    nosso_bloco = "[DEV9/Eth]"
    guardar, bloco_atual = [], None
    try:
        with open(destino, "r", encoding="utf-8", errors="replace") as arquivo:
            for linha in arquivo:
                limpo = linha.strip()
                if limpo.startswith("[") and limpo.endswith("]"):
                    bloco_atual = limpo
                if bloco_atual != nosso_bloco:
                    guardar.append(linha.rstrip("\n"))
    except OSError:
        guardar = []

    com_driver = npcap_instalado()
    adaptador = adaptador_de_rede_real() if com_driver else None

    linhas = ["", "[DEV9/Eth]", "EthEnable = true"]
    if com_driver and adaptador:
        linhas += ["EthApi = PCAPBridged", "InterfaceName = %s" % adaptador]
        modo = "pcap"
    else:
        linhas += ["EthApi = Sockets"]
        modo = "sockets"

    texto = "\n".join(guardar + linhas) + "\n"
    try:
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        gravar_atomico(destino, texto)
    except OSError:
        return None

    return {"modo": modo, "adaptador": adaptador, "com_driver": bool(com_driver)}


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
                          ultra=False, preset=None, controles_xinput=None,
                          placa="any"):
    """Escreve o bloco de video do Xenia (Xbox 360), preservando o resto.

    'preset' deixa a pessoa escolher na mao em vez de confiar na nota da
    maquina: "leve" (o mais leve possivel), "bonito" (o melhor que a
    placa aguentar) ou None/"automatico" (decide pela nota, o padrao).

    'controles_xinput': numeros (0 a 3) dos controles ligados. Os controles
    o Xenia ja aceita sozinho (jogador = numero do XInput); o ARENA so liga
    o teclado no primeiro jogador sem controle (regra do ARENA). Sem
    controle livre (4 ligados), o teclado fica desligado.

    NAO troca as teclas: o formato dos 'keybind_*' do Xenia
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
    if preset == "leve":
        modo_fraco, forte = True, False
    elif preset == "bonito":
        modo_fraco, forte = False, True
    else:
        modo_fraco = modesto or alvo_nota <= 2
        forte = alvo_nota >= 4 and not modesto

    ajustes = {
        "gpu": '"%s"' % placa,  # ver placa_do_xenia
        "fullscreen": "true" if ultra else "false",
        "vsync": "true",
        "framerate_limit": "0",
    }
    if modo_fraco:
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

    if controles_xinput is not None:
        livres = [n for n in range(4) if n not in set(controles_xinput)]
        ajustes["keyboard_mode"] = "1" if livres else "0"
        ajustes["keyboard_user_index"] = str(livres[0] if livres else 0)

    for chave, valor in ajustes.items():
        texto = _trocar_valor_toml(texto, chave, valor)

    try:
        gravar_atomico(destino, texto)
        return destino
    except OSError as falha:
        aviso_sem_gravar("Xenia", falha)
        return None


# ---------------------------------------------------------------------------
# Xbox 360 pela rede: Xenia Netplay, "Systemlink" - sem driver nenhum
# ---------------------------------------------------------------------------
# Diferente do PS2, aqui nao precisa de driver: o Xenia Netplay (um build
# separado, xenia_canary_netplay.exe, feito por uma comunidade dedicada a
# isso) tem um modo "Systemlink" que e' rede local pura, em software -
# so muda a chave network_mode no config.toml dele (0 = offline, 1 =
# systemlink, 2 = Xbox Live, que usa um servidor de terceiros pra
# partida pela internet - esse sim teria a mesma ressalva de privacidade
# do RPCN do RPCS3, por isso nao ligado aqui).
#
# Igual ao core_netplay do PS1: o build normal (xenia_canary.exe) continua
# sendo o de sempre pra jogar sozinho, mais atualizado; o build de
# netplay so entra quando for Jogar Junto.

def jogo_tem_netplay_xbox360(plataforma, titulo):
    """Confere se o jogo esta na lista com netplay testado de verdade
    (consoles.json -> externo.jogos_netplay). Lista curta de proposito."""
    lista = (plataforma.get("externo") or {}).get("jogos_netplay", [])
    titulo_normalizado = (titulo or "").lower()
    return any(nome.lower() in titulo_normalizado for nome in lista)


def placa_do_xenia(plataforma, titulo=None):
    """Modo de video do Xenia: consoles.json -> externo.placa ("vulkan"),
    ou "any" (o Xenia escolhe; no Windows, Direct3D 12) se nao houver.

    Achado 26/09/2026, na Radeon integrada: no Direct3D 12 a placa "caia"
    ("Graphics device lost", "Failed to create a command allocator") no
    Left 4 Dead 2 e, na segunda abertura, no Gears of War - tela preta e o
    Xenia travado, so saia pelo Gerenciador de Tarefas. No Vulkan os dois
    rodaram estaveis. 'titulo' fica para uma excecao por jogo no futuro."""
    return (plataforma.get("externo") or {}).get("placa") or "any"


def escrever_config_netplay_xbox360(caminho_executavel):
    """Liga o modo Systemlink (network_mode = 1) do Xenia Netplay - rede
    local de verdade, sem precisar de driver nenhum.

    So mexe se o Xenia Netplay ja rodou pelo menos uma vez e criou o
    config.toml dele - mesma regra do escrever_config_xenia, pra nao
    inventar um arquivo do zero e perder as centenas de opcoes que so o
    Xenia sabe o valor certo.
    """
    pasta = os.path.dirname(caminho_executavel)
    nome_exe = os.path.splitext(os.path.basename(caminho_executavel))[0]
    nome_config = nome_exe.replace("_", "-") + ".config.toml"
    destino = os.path.join(pasta, nome_config)

    if not os.path.isfile(destino):
        return False

    try:
        with open(destino, "r", encoding="utf-8") as arquivo:
            texto = arquivo.read()
    except OSError:
        return False

    texto = _trocar_valor_toml(texto, "network_mode", "1")

    try:
        gravar_atomico(destino, texto)
        return True
    except OSError:
        return False


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
                          ultra=False, preset=None, abaixo=""):
    """Escreve o bloco de video do RPCS3 (PlayStation 3), preservando o resto.

    Mesma logica do Xenia: so mexe se o RPCS3 ja criou o config.yml dele
    (primeira vez que abre, mesmo sem jogo nenhum). Os controles ficam em
    outro arquivo: ver escrever_controles_rpcs3.

    'preset': "leve", "bonito" ou None/"automatico" (decide pela nota).
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
    if preset == "leve":
        modo_fraco, forte = True, False
    elif preset == "bonito":
        modo_fraco, forte = False, True
    else:
        modo_fraco = modesto or alvo_nota <= 2
        forte = alvo_nota >= 4 and not modesto

    if modo_fraco:
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
    # Abaixo do original (02/10/2026): o PS3 desenhado a 50% (leve) ou 25%
    # (minimo) dos 720p dele -- o RPCS3 aceita de 25 a 800 (system_config.h,
    # cfg::uint<25, 800>) -- e a contagem de pixels escondidos (ZCULL)
    # relaxada. Fora disso, os padroes do RPCS3, para a volta valer.
    niveis = niveis_abaixo_ate(abaixo)
    if niveis:
        video.update({"Resolution Scale": "25" if "minimo" in niveis else "50",
                      "Anisotropic Filter Override": "0", "MSAA": "Disabled"})
    video["Relaxed ZCULL Sync"] = "true" if niveis else "false"
    video["Accurate ZCULL stats"] = "false" if niveis else "true"

    for chave, valor in video.items():
        texto = _trocar_valor_yaml(texto, "Video", chave, valor)

    texto = _trocar_valor_yaml(texto, "Miscellaneous",
                               "Start games in fullscreen mode",
                               "true" if ultra else "false")

    try:
        gravar_atomico(destino, texto)
        return destino
    except OSError as falha:
        aviso_sem_gravar("RPCS3", falha)
        return None


# Controles do RPCS3. O PS3 aceita 7 controles sem adaptador nenhum, entao
# nao ha multitap: cada controle XInput ligado vira um jogador, na ordem, e
# o teclado e' o primeiro jogador sem controle (regra do ARENA). O arquivo
# e' config/input_configs/global/Default.yml (o que o proprio RPCS3 grava
# quando se configura pela tela "Pads"). Achado 26/09/2026: so o jogador 1
# vinha configurado; os outros estavam "Null" - nenhum 2o controle entrava.
# Nomes dos botoes: os mesmos que o RPCS3 gravou para o XInput. O aparelho
# "XInput Pad #N" conta de 1 (N = numero do Windows + 1).
RPCS3_BOTOES_XINPUT = [
    ("Left Stick Left", "LS X-"), ("Left Stick Down", "LS Y-"),
    ("Left Stick Right", "LS X+"), ("Left Stick Up", "LS Y+"),
    ("Right Stick Left", "RS X-"), ("Right Stick Down", "RS Y-"),
    ("Right Stick Right", "RS X+"), ("Right Stick Up", "RS Y+"),
    ("Start", "Start"), ("Select", "Back"), ("PS Button", '"Back&Start,Guide"'),
    ("Square", "X"), ("Cross", "A"), ("Circle", "B"), ("Triangle", "Y"),
    ("Left", "Left"), ("Down", "Down"), ("Right", "Right"), ("Up", "Up"),
    ("R1", "RB"), ("R2", "RT"), ("R3", "RS"), ("L1", "LB"), ("L2", "LT"), ("L3", "LS"),
]
# Zonas mortas iguais as que o RPCS3 grava para um controle XInput.
RPCS3_AJUSTES_XINPUT = [
    ("Left Stick Deadzone", "7849"), ("Right Stick Deadzone", "8689"),
    ("Left Stick Anti-Deadzone", "4259"), ("Right Stick Anti-Deadzone", "4259"),
    ("Left Trigger Threshold", "30"), ("Right Trigger Threshold", "30"),
    ("Left Pad Squircling Factor", "4000"), ("Right Pad Squircling Factor", "4000"),
    ("Vibration Threshold", "63"),
]
# Mesmas teclas do resto do ARENA (setas, Z, X, A, S, Q, W, E, R, Enter, Shift).
RPCS3_BOTOES_TECLADO = [
    ("Up", "Up"), ("Down", "Down"), ("Left", "Left"), ("Right", "Right"),
    ("Cross", "Z"), ("Circle", "X"), ("Square", "A"), ("Triangle", "S"),
    ("L1", "Q"), ("R1", "W"), ("L2", "E"), ("R2", "R"),
    ("Select", "Shift"), ("Start", "Return"),
]
RPCS3_JOGADORES = 7


def controles_rpcs3(controles_xinput, teclado=True):
    """Texto do Default.yml do RPCS3: um jogador por controle XInput ligado,
    depois o teclado; o resto fica "Null" (sem nada)."""
    controles_xinput = list(controles_xinput or [])[:RPCS3_JOGADORES]
    linhas = []
    teclado_usado = not teclado
    for jogador in range(RPCS3_JOGADORES):
        linhas.append("Player %d Input:" % (jogador + 1))
        if jogador < len(controles_xinput):
            linhas += ["  Handler: XInput",
                       '  Device: "XInput Pad #%d"' % (controles_xinput[jogador] + 1),
                       "  Config:"]
            linhas += ["    %s: %s" % par for par in RPCS3_BOTOES_XINPUT + RPCS3_AJUSTES_XINPUT]
        elif not teclado_usado:
            teclado_usado = True
            linhas += ["  Handler: Keyboard", "  Device: Keyboard", "  Config:"]
            linhas += ["    %s: %s" % par for par in RPCS3_BOTOES_TECLADO]
        else:
            linhas += ['  Handler: "Null"', '  Device: "Null"']
        linhas.append('  Buddy Device: ""')
    return "\n".join(linhas) + "\n"


def escrever_controles_rpcs3(caminho_executavel, controles_xinput):
    """Grava os controles do RPCS3 (todos os jogos usam o perfil "Default")."""
    pasta = os.path.join(os.path.dirname(caminho_executavel), "config", "input_configs")
    destino = os.path.join(pasta, "global", "Default.yml")
    try:
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        gravar_atomico(destino, controles_rpcs3(controles_xinput))
        ativo = os.path.join(pasta, "active_input_configurations.yml")
        if not os.path.isfile(ativo):
            gravar_atomico(ativo, "Active Configurations:\n  global: Default\n")
        return destino
    except OSError:
        return None


# ---------------------------------------------------------------------------
# PS3 online de verdade: RPCN
# ---------------------------------------------------------------------------
# O RPCN e' um servidor comunitario (nao e' da Sony, nao e' do ARENA) que
# devolve matchmaking, salas e trocas online pra jogos de PS3 compativeis,
# direto pelo RPCS3 - sem driver, sem admin. So que precisa de uma conta
# feita pela PROPRIA tela do RPCS3 (Toolbar -> RPCN -> Account -> Create
# Account: usuario, e-mail, senha, confirma por token que chega no
# e-mail). O ARENA NUNCA cria essa conta sozinho - e' dado de gente (nome,
# e-mail, senha) indo pra um servico de terceiros que a escola nao
# administra. O que o ARENA faz e' so ligar a opcao quando o professor
# decidir usar (desligado por padrao), depois que a conta ja existir.

def escrever_config_rpcn(caminho_executavel, ligado=True):
    """Liga ou desliga a internet do RPCS3 (e com ela o RPCN), seguindo a
    chave 'rpcn_ativo' do ARENA. So mexe se o RPCS3 ja rodou uma vez.

    Desligar tambem e' tarefa do ARENA. Achado 26/09/2026: o RPCN tinha
    sido ligado pela tela do RPCS3 e ficou ligado para todos os jogos; o
    Minecraft dava "falhou no carregamento" ao criar o mundo e funcionou
    com 4 jogadores assim que a internet do RPCS3 foi desligada. A conta
    (rpcn.yml) nao e' tocada: religar a chave volta a usa-la."""
    pasta = os.path.dirname(caminho_executavel)
    destino = os.path.join(pasta, "config", "config.yml")

    if not os.path.isfile(destino):
        return False

    try:
        with open(destino, "r", encoding="utf-8") as arquivo:
            texto = arquivo.read()
    except OSError:
        return False

    texto = _trocar_valor_yaml(texto, "Net", "Internet enabled",
                               "Connected" if ligado else "Disconnected")
    if ligado:
        texto = _trocar_valor_yaml(texto, "Net", "PSN status", "RPCN")

    try:
        gravar_atomico(destino, texto)
        return True
    except OSError:
        return False


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

# Device ID do libretro para "Multitap" (nucleo snes9x: RETRO_DEVICE_JOYPAD_MULTITAP
# = (1 << 8) | RETRO_DEVICE_JOYPAD = 257 -- conferido no codigo-fonte do
# nucleo, nao inventado). Ligado na porta 2, o multitap abre mais 4 encaixes
# de controle (portas 2 a 5) -- porta 1 continua sendo o jogador 1 normal.
# E' assim que o adaptador de verdade funciona: pluga na porta 2 do
# Super Nintendo, nao substitui a porta 1.
DISPOSITIVO_MULTITAP_SNES = 257
JOGADORES_MULTITAP = 5          # jogador 1 na porta 1 + 4 no adaptador da porta 2
NETPLAY_CONEXOES_PADRAO = 3     # o mesmo padrao do RetroArch (netplay_max_connections)


def opcoes_de_partida(apelido, hospedar, atraso=0, assistir=False,
                      pela_internet=False, repasse=REPASSE_PADRAO, jogador=None,
                      multitap=False):
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

    if multitap:
        # Liga o adaptador na porta 2 do console (nao na 1 - e assim que o
        # Multitap de verdade pluga). Isso abre 4 encaixes (jogadores 2 a
        # 5); jogador 1 continua na porta normal. Precisa estar igual em
        # TODAS as maquinas da partida (quem hospeda e quem entra) para o
        # estado do nucleo bater nos dois lados.
        opcoes["input_libretro_device_p2"] = str(DISPOSITIVO_MULTITAP_SNES)

    # Quantas maquinas podem se conectar em quem hospeda. O padrao do
    # RetroArch e' 3 (= 4 jogadores contando o hospedeiro) -- era por isso
    # que, com o Multitap, o 4o convidado (jogador 5) sempre era recusado
    # (achado na Fase 4 da auditoria, causa confirmada depois). So sobe no
    # Multitap; o resto continua no padrao, que ja sobra para 2 jogadores.
    opcoes["netplay_max_connections"] = str(
        JOGADORES_MULTITAP - 1 if multitap else NETPLAY_CONEXOES_PADRAO)

    return opcoes


# ---------------------------------------------------------------------------
# Mais de dois jogadores: o mapa de cada nucleo (servidor\multitap.json).
#
# Cada nucleo liga o adaptador de um jeito: uns por TIPO DE CONTROLE numa
# porta (SNES: "Multitap" = 257), outros por OPCAO DO NUCLEO (PS1: "port 1";
# Saturn: "enabled"). O mapa foi conferido contra o .dll desta pasta
# (ferramentas\conferir_mapa_multitap.py) -- nada aqui e' de memoria.
# ---------------------------------------------------------------------------

ARQUIVO_MAPA_MULTITAP = os.path.join(PASTA_SERVIDOR, "multitap.json")
# Copia do arquivo de opcoes de nucleo, SO para a partida de 3+ jogadores
# que precisa de uma opcao a mais (PS1, Saturn). O arquivo de sempre nao e'
# tocado: a proxima partida sozinho sai igualzinha (decisao do Rafael,
# 25/09/2026). Fica em dados\ porque o RetroArch grava nele ao fechar.
ARQUIVO_OPCOES_CORE_PARTIDA = os.path.join(RAIZ, "dados", "opcoes_nucleo_partida.cfg")


def carregar_mapa_multitap():
    try:
        with open(ARQUIVO_MAPA_MULTITAP, encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except (OSError, ValueError):
        # Sem o mapa, o ARENA continua como sempre: ate 2 jogadores.
        return {}


def cabecalho_mega_drive(caminho):
    """Serie e acessorios que o cartucho de Mega Drive declara no proprio
    cabecalho (0x180 e 0x190). None se o arquivo nao e' um cartucho de Mega
    Drive legivel (Master System, Game Gear, .zip, .smd intercalado...)."""
    try:
        with open(caminho, "rb") as arquivo:
            topo = arquivo.read(0x200)
    except (OSError, TypeError):
        return None
    if len(topo) < 0x1A0 or b"SEGA" not in topo[0x100:0x110]:
        return None
    return {"serie": topo[0x180:0x18E].decode("latin-1").strip(),
            "acessorios": topo[0x190:0x1A0].decode("latin-1").strip()}


def jogadores_do_jogo(nucleo, jogadores, jogadores_da_config=2, mapa=None, arquivo=None):
    """Diz o que escrever para ESTE nucleo aceitar 'jogadores' controles.

    Devolve um dicionario:
      jogadores   - quantos o nucleo aceita de verdade (pode ser menos que o
                    pedido, se o nucleo nao tem adaptador);
      cfg         - chaves para o arquivo temporario da partida
                    (--appendconfig): tipo de controle das portas e
                    input_max_users;
      nucleo      - opcoes do nucleo (vao numa copia do arquivo de opcoes);
      max_conexoes - netplay_max_connections para o Jogar Junto;
      motivo      - frase para o aluno quando o nucleo nao chega ao pedido.

    REGRA DE OURO: com 1 ou 2 jogadores nao devolve chave nenhuma -- o
    arquivo da partida sai exatamente como antes desta funcao existir.
    """
    resultado = {"jogadores": max(1, int(jogadores or 2)), "cfg": {}, "nucleo": {},
                 "max_conexoes": NETPLAY_CONEXOES_PADRAO, "motivo": ""}
    pedido = resultado["jogadores"]
    if pedido <= 2:
        return resultado

    mapa = carregar_mapa_multitap() if mapa is None else mapa
    info = mapa.get("nucleos", {}).get(os.path.basename(nucleo or ""))
    if not info:
        resultado["jogadores"] = 2
        resultado["motivo"] = ("Este console ainda não foi conferido para mais "
                               "de 2 jogadores no ARENA.")
        return resultado

    aceitos = min(pedido, int(info.get("jogadores_sem_adaptador", 2)))
    adaptador = info.get("adaptador", {})
    motivo_cartucho = ""
    exigido = adaptador.get("so_se_o_cartucho_declarar")
    automatico = info.get("automatico")
    if (exigido or automatico) and pedido > aceitos:
        # Mega Drive: cada jogo usa um adaptador diferente, e o nucleo nao
        # escolhe sozinho. Quem diz e' o proprio cartucho (ver o mapa).
        cabecalho = cabecalho_mega_drive(arquivo)
        serie = (cabecalho or {}).get("serie", "")
        if automatico and any(s in serie for s in automatico.get("series", [])):
            # O cartucho tem as entradas extras; o nucleo liga sozinho.
            aceitos = min(pedido, int(automatico.get("jogadores", aceitos)))
            adaptador = {}
        elif not cabecalho or exigido not in cabecalho.get("acessorios", ""):
            adaptador = {}
            motivo_cartucho = ("Este cartucho não declara adaptador para mais "
                               "de %d jogadores." % aceitos)
    if pedido > aceitos and adaptador.get("tipo") in ("dispositivo", "opcao_do_nucleo"):
        chaves = dict(adaptador.get("chaves", {}))
        aceitos = min(pedido, int(adaptador.get("jogadores", aceitos)))
        segundo = adaptador.get("segundo_adaptador")
        if segundo and pedido > aceitos:
            chaves.update(segundo.get("chaves", {}))
            aceitos = min(pedido, int(segundo.get("jogadores", aceitos)))
        destino = "cfg" if adaptador["tipo"] == "dispositivo" else "nucleo"
        resultado[destino].update(chaves)

    if aceitos < pedido:
        resultado["motivo"] = motivo_cartucho or (
            "Neste console o emulador aceita até %d jogadores." % aceitos)
    resultado["jogadores"] = aceitos
    if aceitos > 2:
        # Sem isto o RetroArch so le os 2 primeiros controles (o ARENA vem
        # com input_max_users = 2): o 3o em diante fica mudo.
        try:
            da_config = int(jogadores_da_config or 2)
        except (TypeError, ValueError):
            da_config = 2  # config torta nao derruba a partida
        resultado["cfg"]["input_max_users"] = str(max(aceitos, da_config))
        # O padrao do RetroArch (3 conexoes) recusava o 5o jogador mesmo com
        # o adaptador certo. Nunca abaixo do padrao de hoje.
        resultado["max_conexoes"] = max(NETPLAY_CONEXOES_PADRAO, aceitos - 1)
    return resultado


def gravar_opcoes_de_nucleo_da_partida(extras):
    """Copia o arquivo de opcoes de nucleo de sempre, acrescenta 'extras'
    (ex.: pcsx_rearmed_multitap = "port 1") e devolve o caminho da copia,
    para a partida apontar core_options_path para ela."""
    try:
        with open(ARQUIVO_OPCOES_CORE, encoding="utf-8", errors="replace") as arquivo:
            linhas = arquivo.read().splitlines()
    except OSError:
        linhas = []
    linhas = [l for l in linhas if l.split("=", 1)[0].strip() not in extras]
    linhas += ['%s = "%s"' % (chave, valor) for chave, valor in sorted(extras.items())]
    os.makedirs(os.path.dirname(ARQUIVO_OPCOES_CORE_PARTIDA), exist_ok=True)
    temporario = "%s.%d.tmp" % (ARQUIVO_OPCOES_CORE_PARTIDA, threading.get_ident())
    with open(temporario, "w", encoding="utf-8", newline="\n") as arquivo:
        arquivo.write("\n".join(linhas) + "\n")
    os.replace(temporario, ARQUIVO_OPCOES_CORE_PARTIDA)
    return ARQUIVO_OPCOES_CORE_PARTIDA


def valores_no_retroarch_cfg(chaves):
    """Le do retroarch.cfg o valor atual de cada chave (None se nao existe)."""
    valores = dict.fromkeys(chaves)
    try:
        with open(os.path.join(PASTA_RETROARCH, "retroarch.cfg"), encoding="utf-8",
                  errors="replace") as arquivo:
            for linha in arquivo:
                chave, _, valor = linha.partition("=")
                chave = chave.strip()
                if chave in valores:
                    valores[chave] = valor.strip().strip('"')
    except OSError:
        pass
    return valores


def devolver_valores_no_retroarch_cfg(antes):
    """O RetroArch grava no retroarch.cfg, ao fechar, o que veio no arquivo
    temporario da partida (ver testes\\protege_cfg.py). Depois de uma partida
    de 3+ jogadores, devolve SO as chaves que o ARENA mudou para ela ao
    valor de antes -- senao o tipo de controle das portas 3/4 (ex.: 513 no
    NES) vazaria para a proxima partida de 2, que nao reescreve essas portas.
    Devolve quantas linhas mudaram."""
    caminho = os.path.join(PASTA_RETROARCH, "retroarch.cfg")
    try:
        with open(caminho, encoding="utf-8", errors="replace") as arquivo:
            linhas = arquivo.readlines()
    except OSError:
        return 0
    novas, trocadas = [], 0
    for linha in linhas:
        chave = linha.split("=", 1)[0].strip()
        if chave in antes:
            valor = antes[chave]
            certo = None if valor is None else '%s = "%s"\n' % (chave, valor)
            if certo != linha:
                trocadas += 1
            if certo:
                novas.append(certo)
            continue
        novas.append(linha)
    if trocadas:
        temporario = "%s.%d.tmp" % (caminho, threading.get_ident())
        with open(temporario, "w", encoding="utf-8", newline="") as arquivo:
            arquivo.writelines(novas)
        os.replace(temporario, caminho)
    return trocadas


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
