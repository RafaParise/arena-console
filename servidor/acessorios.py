# -*- coding: utf-8 -*-
"""Acessorios dos consoles: VMU, Rumble Pak, multitap, pistola de luz, cartuchos de expansao...

Um console de verdade tinha pecas que se encaixavam nele. O ARENA deixa a pessoa ligar ou desligar cada uma
dessas pecas, console por console, e transforma a escolha em algo que o emulador entende:

  1. uma OPCAO do nucleo (por exemplo, reicast_vmu1_screen_display = "enabled": mostra a telinha do VMU);
  2. o TIPO DE CONTROLE de uma porta (input_libretro_device_p2 = "260": uma pistola de luz na porta 2);
  3. o CARTAO do PS2 de cada entrada (PocketStation na entrada 1, cartao grande na entrada 2).

A lista de acessorios fica em servidor\\acessorios.json (dados, nao codigo): para incluir um acessorio novo basta
descreve-lo la. Toda chave e todo valor daquele arquivo foram perguntados ao proprio nucleo
(ferramentas\\levantar_opcoes_dos_nucleos.py); ferramentas\\conferir_acessorios.py confere de novo quando o nucleo muda.

A escolha da pessoa fica em config.json -> acessorios, assim:
    {"dc_vmu_tela_1": {"tela": true, "lugar": "Lower Right", "tamanho": "3x"}}
Controle que a pessoa nunca mexeu NAO e' gravado: o emulador fica como estava (e como o aluno deixou no menu dele).
"""
import copy
import json
import os
import re
import threading

PASTA_SERVIDOR = os.path.dirname(os.path.abspath(__file__))
ARQUIVO = os.path.join(PASTA_SERVIDOR, "acessorios.json")

LETRAS = "ABCDEFGH"
_ID = re.compile(r"^[a-z0-9_]{1,60}$")
_TRAVA = threading.Lock()
_CACHE = {"marca": None, "grupos": []}


def _trocar(valor, n):
    """Troca {n} (numero do jogador) e {letra} (A, B, C...) em todo texto de 'valor', por dentro de listas e dicionarios."""
    if isinstance(valor, str):
        return valor.replace("{n}", str(n)).replace("{letra}", LETRAS[(n - 1) % len(LETRAS)])
    if isinstance(valor, list):
        return [_trocar(item, n) for item in valor]
    if isinstance(valor, dict):
        return {chave: _trocar(item, n) for chave, item in valor.items()}
    return valor


def expandir(acessorio):
    """Um acessorio com "jogadores": 4 vira 4 acessorios, um por jogador (ids dc_vmu_tela_1, _2, _3, _4)."""
    quantos = acessorio.get("jogadores")
    if not isinstance(quantos, int) or isinstance(quantos, bool) or quantos < 1:
        return [acessorio]
    modelo = {chave: valor for chave, valor in acessorio.items() if chave != "jogadores"}
    return [_trocar(copy.deepcopy(modelo), n) for n in range(1, min(quantos, 8) + 1)]


def carregar():
    """A lista de grupos {consoles, nucleo, plataformas, acessorios}, ja com os acessorios por jogador repetidos.
    Relida sozinha se o arquivo mudar. Arquivo ausente ou quebrado: lista vazia (o resto do ARENA segue)."""
    try:
        marca = os.stat(ARQUIVO).st_mtime_ns
    except OSError:
        return []
    with _TRAVA:
        if _CACHE["marca"] == marca:
            return _CACHE["grupos"]
        try:
            with open(ARQUIVO, encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
        except (OSError, ValueError):
            return []
        grupos = []
        for grupo in dados.get("grupos", []) if isinstance(dados, dict) else []:
            if not isinstance(grupo, dict) or not isinstance(grupo.get("consoles"), list):
                continue
            acessorios = []
            for bruto in grupo.get("acessorios", []):
                if isinstance(bruto, dict):
                    acessorios.extend(expandir(bruto))
            grupos.append({"consoles": [c for c in grupo["consoles"] if isinstance(c, str)],
                           "nucleo": grupo.get("nucleo", ""),
                           "plataformas": grupo.get("plataformas") or [],
                           "acessorios": acessorios})
        _CACHE["marca"], _CACHE["grupos"] = marca, grupos
        return grupos


def todos_os_acessorios():
    """{id do acessorio: acessorio} de tudo que o catalogo tem."""
    achados = {}
    for grupo in carregar():
        for acessorio in grupo["acessorios"]:
            if _ID.match(str(acessorio.get("id", ""))):
                achados[acessorio["id"]] = acessorio
    return achados


def chaves_de_opcao():
    """Toda chave de opcao de nucleo que algum acessorio do catalogo pode escrever."""
    chaves = set()
    for acessorio in todos_os_acessorios().values():
        for controle in acessorio.get("controles", []):
            chave = (controle.get("alvo") or {}).get("opcao")
            if chave:
                chaves.add(chave)
    return chaves


def _controles(acessorio):
    return {c["id"]: c for c in acessorio.get("controles", []) if isinstance(c, dict) and _ID.match(str(c.get("id", "")))}


def _valores_da_escolha(controle):
    return {str(par[0]) for par in controle.get("escolhas", []) if isinstance(par, list) and par}


def limpar_estado(valor):
    """O que a pessoa escolheu (config.json -> acessorios), so com o que o catalogo conhece e com valores que o
    controle aceita. Chave vira verdadeiro/falso; escolha vira o texto de um dos valores da lista. O resto e' descartado."""
    limpo = {}
    if not isinstance(valor, dict):
        return limpo
    conhecidos = todos_os_acessorios()
    for acessorio_id, escolhas in list(valor.items())[:400]:
        acessorio = conhecidos.get(acessorio_id)
        if acessorio is None or not isinstance(escolhas, dict):
            continue
        controles = _controles(acessorio)
        aceitas = {}
        for controle_id, escolhido in escolhas.items():
            controle = controles.get(controle_id)
            if controle is None:
                continue
            if controle.get("tipo") == "chave":
                if isinstance(escolhido, bool):
                    aceitas[controle_id] = escolhido
            elif controle.get("tipo") == "escolha":
                if isinstance(escolhido, (str, int)) and not isinstance(escolhido, bool) \
                        and str(escolhido) in _valores_da_escolha(controle):
                    aceitas[controle_id] = str(escolhido)
        if aceitas:
            limpo[acessorio_id] = aceitas
    return limpo


def valor_efetivo(controle, escolhas_do_acessorio):
    """O que vale agora para este controle: o que a pessoa escolheu, ou o padrao do catalogo."""
    escolhido = (escolhas_do_acessorio or {}).get(controle.get("id"))
    if escolhido is not None:
        return escolhido
    return controle.get("padrao", False if controle.get("tipo") == "chave" else "")


def _alvo_inteiro(texto):
    try:
        return int(str(texto))
    except ValueError:
        return None


def alvos(estado, console_id, nome_nucleo=None):
    """Tudo que as escolhas da pessoa pedem para UM console: {"opcoes": {chave: valor}, "portas": {numero: tipo},
    "cartoes_ps2": {entrada: valor}}. So entra o controle que a pessoa mexeu e que nao esta em "como o emulador escolhe".
    Se 'nome_nucleo' vier, so valem os grupos daquele nucleo (o PS1 tem mais de um: cada um com os seus codigos)."""
    estado = limpar_estado(estado)
    achado = {"opcoes": {}, "portas": {}, "cartoes_ps2": {}}
    for grupo in carregar():
        if console_id not in grupo["consoles"]:
            continue
        if nome_nucleo and grupo["nucleo"] and grupo["nucleo"] != nome_nucleo:
            continue
        for acessorio in grupo["acessorios"]:
            escolhas = estado.get(acessorio.get("id"))
            if not escolhas:
                continue
            for controle_id, controle in _controles(acessorio).items():
                if controle_id not in escolhas:
                    continue
                escolhido = escolhas[controle_id]
                if controle.get("tipo") == "chave":
                    escolhido = controle.get("ligado") if escolhido else controle.get("desligado")
                if escolhido in (None, ""):
                    continue
                alvo = controle.get("alvo") or {}
                if alvo.get("opcao"):
                    achado["opcoes"][alvo["opcao"]] = str(escolhido)
                elif alvo.get("porta") is not None and _alvo_inteiro(alvo["porta"]):
                    achado["portas"][_alvo_inteiro(alvo["porta"])] = str(escolhido)
                elif alvo.get("cartao_ps2") is not None and _alvo_inteiro(alvo["cartao_ps2"]):
                    achado["cartoes_ps2"][_alvo_inteiro(alvo["cartao_ps2"])] = str(escolhido)
    return achado


def opcoes_do_nucleo(estado, console_id, nome_nucleo):
    """As opcoes do nucleo que os acessorios deste console pedem (entram no arquivo de opcoes do RetroArch)."""
    return alvos(estado, console_id, nome_nucleo)["opcoes"]


def opcoes_de_porta(estado, console_id, nome_nucleo):
    """O tipo de controle de cada porta: {"input_libretro_device_p2": "260"}. Quem grava no .rmp da partida e' o
    ARENA (arena.remapeamento_da_partida): o RetroArch ignora esse valor vindo do --appendconfig."""
    portas = alvos(estado, console_id, nome_nucleo)["portas"]
    return {"input_libretro_device_p%d" % numero: tipo for numero, tipo in portas.items() if 1 <= numero <= 8}


def cartoes_ps2(estado):
    """Os cartoes do PS2 pedidos: {"slot1_tipo": "ps1" ou "ps2", "slot1_mb": 64, "slot2_tipo": ..., "slot2_mb": ...}.
    Sem escolha nenhuma vale o padrao do catalogo: o maior cartao do PS2 (64 MB) na entrada 1 e o PocketStation na 2,
    como no ARENA do computador (decisao do Rafael, 24/10/2026)."""
    estado = limpar_estado(estado)
    resultado = {"slot1_tipo": "ps2", "slot1_mb": 64, "slot2_tipo": "ps1", "slot2_mb": 8}
    acessorio = todos_os_acessorios().get("ps2_cartoes")
    if acessorio is None:
        return resultado
    controles = _controles(acessorio)
    escolhas = estado.get("ps2_cartoes", {})
    padroes = {1: "64", 2: "pocketstation"}
    for entrada in (1, 2):
        controle = controles.get("entrada%d" % entrada, {"id": "entrada%d" % entrada, "padrao": padroes[entrada]})
        valor = str(valor_efetivo(controle, escolhas))
        if valor == "pocketstation":
            resultado["slot%d_tipo" % entrada] = "ps1"
        elif valor.isdigit():
            resultado["slot%d_tipo" % entrada], resultado["slot%d_mb" % entrada] = "ps2", int(valor)
    return resultado


def para_a_tela(estado, sistema, nomes_dos_consoles):
    """O que a tela desenha: uma lista de consoles, cada um com os seus acessorios e o valor de cada controle.

    'sistema' e' "windows", "linux" ou "android" (o catalogo pode limitar um grupo a certos sistemas).
    'nomes_dos_consoles' e' {id: nome}: so aparecem os consoles que o ARENA tem."""
    estado = limpar_estado(estado)
    por_console = {}
    for grupo in carregar():
        if grupo["plataformas"] and sistema not in grupo["plataformas"]:
            continue
        for console_id in grupo["consoles"]:
            if console_id not in nomes_dos_consoles:
                continue
            lista = por_console.setdefault(console_id, [])
            for acessorio in grupo["acessorios"]:
                escolhas = estado.get(acessorio.get("id"), {})
                controles = []
                for controle in acessorio.get("controles", []):
                    if not isinstance(controle, dict):
                        continue
                    item = {"id": controle.get("id"), "tipo": controle.get("tipo"), "rotulo": controle.get("rotulo", ""),
                            "valor": valor_efetivo(controle, escolhas)}
                    if controle.get("tipo") == "escolha":
                        item["escolhas"] = controle.get("escolhas", [])
                    controles.append(item)
                lista.append({"id": acessorio.get("id"), "nome": acessorio.get("nome", ""), "texto": acessorio.get("texto", ""),
                              "so_alguns_jogos": bool(acessorio.get("so_alguns_jogos")), "controles": controles})
    return [{"console": console_id, "nome": nomes_dos_consoles[console_id], "acessorios": lista}
            for console_id, lista in por_console.items()]
