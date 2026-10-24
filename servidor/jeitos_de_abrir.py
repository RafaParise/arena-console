# -*- coding: utf-8 -*-
r"""
ARENA - os jeitos de abrir um console: o de fora, o original e o livre.

Pedido do Rafael (15/10/2026): "se tiver dois emuladores, seja os
convencionais que tenho na pasta do diretorio e outro de codigo aberto que
ja vem do download do github, o ARENA saiba disso e pergunte qual dos dois
ele quer usar para rodar o jogo, tanto a BIOS como emuladores".

Um console pode ter ate tres jeitos de abrir:

  - "externo":  o emulador de fora (PCSX2, Dolphin...), quando ele esta na
                pasta emuladores;
  - "original": o nucleo do RetroArch com a BIOS de verdade, a que o
                professor pos na pasta BIOS (ou sem BIOS nenhuma, quando o
                console nao precisa de uma);
  - "livre":    o que vem no pacote do ARENA e nao depende de nada das
                empresas (consoles.json -> livre): uma BIOS livre, como a
                OpenBIOS do PlayStation, ou um nucleo que imita a BIOS.

Com um jeito so, o ARENA abre por ele. Com dois ou mais, a tela pergunta
qual usar e pode lembrar a resposta (config.json -> jeito_de_abrir).

Alguns consoles ainda tem um emulador de fora A MAIS (consoles.json ->
externo_extra: o PokketSX do PlayStation, que liga o PocketStation de
verdade). Ele entra na lista como o jeito "externo", por ultimo, e so abre
quando a pessoa o escolhe: o console segue sendo do RetroArch.
"""
import os

import bios
import plataforma as plataforma_do_sistema  # "plataforma", aqui, e' o console

JEITOS = ("externo", "original", "livre")


def pasta_do_livre(plataforma, pasta_sistema):
    """A pasta das BIOS que o nucleo recebe no jeito livre, quando a BIOS
    livre mora numa pasta so dela (consoles.json -> livre.pasta, dentro de
    retroarch\\system); None quando ela fica solta na system.

    A OpenBIOS do PlayStation mora em retroarch\\system\\OpenBIOS: solta na
    system, o SwanStation a escolheria ate no jeito original. Ele procura a
    BIOS em ordem alfabetica, e "openbios.bin" vem antes de "SCPH1001.BIN"
    (testado em 15/10/2026, com as duas na pasta)."""
    pasta = (plataforma.get("livre") or {}).get("pasta")
    return os.path.join(pasta_sistema, *pasta.split("/")) if pasta else None


def _livre_pronto(plataforma, pasta_cores, pasta_sistema):
    """O jeito livre do console existe aqui? O nucleo dele na pasta cores e,
    se ele usa uma BIOS livre, o arquivo dela na pasta dela."""
    livre = plataforma.get("livre") or {}
    if not livre:
        return False
    nucleo = livre.get("core") or plataforma.get("core")
    if not nucleo or not plataforma_do_sistema.tem_nucleo(os.path.join(pasta_cores, nucleo)):
        return False
    arquivo = livre.get("bios")
    pasta = pasta_do_livre(plataforma, pasta_sistema) or pasta_sistema
    return not arquivo or os.path.isfile(os.path.join(pasta, arquivo))


def _original_pronto(plataforma, pasta_cores, pasta_sistema, externo):
    """O nucleo de sempre do RetroArch abre o console aqui? Precisa estar na
    pasta cores, nao ser um console que so abre pelo emulador de fora (o PS2:
    o nucleo dele "costuma nem abrir o jogo") e ter a BIOS de verdade, quando
    o console pede uma (as livres nao contam: elas sao o jeito "livre")."""
    nucleo = plataforma.get("core")
    if not nucleo or not plataforma_do_sistema.tem_nucleo(os.path.join(pasta_cores, nucleo)):
        return False
    if externo and (plataforma.get("externo") or {}).get("obrigatorio"):
        return False
    # Os arquivos de apoio que o nucleo pede (consoles.json -> apoio_do_nucleo):
    # o Dolphin do RetroArch sem a pasta dolphin-emu\Sys abre quase tudo, mas
    # sem as fontes do console e sem os codigos de trapaca (15/10/2026).
    apoio = plataforma.get("apoio_do_nucleo")
    if apoio and not os.path.isdir(os.path.join(pasta_sistema, *apoio.split("/"))):
        return False
    # Com um jeito livre, o original e' o da BIOS de verdade: so conta com ela
    # na pasta. No Dreamcast a BIOS e' opcional, e sem isto o ARENA
    # perguntaria entre a imitacao e... a mesma imitacao.
    if plataforma.get("livre"):
        return bios.tem_bios_original(plataforma["id"], pasta_sistema)
    return bios.tem_a_bios(plataforma["id"], pasta_sistema)


def jeitos(plataforma, pasta_cores, pasta_sistema, externo=None, extra=None):
    """Os jeitos de abrir que existem agora, o recomendado primeiro. Cada um:
    {"id", "titulo", "explica", "selo"}. 'externo' e' o nome do emulador de
    fora achado na pasta emuladores (ou None); 'extra', o do emulador de
    fora A MAIS do console (externo_extra), tambem achado na pasta."""
    lista = []
    dados_externo = plataforma.get("externo") or {}
    if externo:
        lista.append({
            "id": "externo",
            "titulo": "%s (programa próprio)" % externo,
            "explica": ("Abre no %s, o programa feito só para este console. %s"
                        % (externo, dados_externo.get("motivo_escolha") or
                           "Costuma ser o mais completo e o mais rápido.")).strip(),
            "selo": "mais completo",
        })
    if _original_pronto(plataforma, pasta_cores, pasta_sistema, externo):
        precisa = bool(plataforma.get("arquivos_sistema")) or bool(plataforma.get("livre"))
        lista.append({
            "id": "original",
            "titulo": "BIOS original" if precisa else "Dentro do RetroArch",
            "explica": ("Liga com a BIOS do console de verdade, a que você pôs na pasta BIOS: "
                        "é a mais fiel, todos os jogos abrem." if precisa else
                        "Abre pelo núcleo do RetroArch, dentro do ARENA: os mesmos controles, saves "
                        "e teclas de sempre."),
            "selo": "mais fiel" if precisa else "",
        })
    if _livre_pronto(plataforma, pasta_cores, pasta_sistema):
        livre = plataforma["livre"]
        lista.append({
            "id": "livre",
            "titulo": livre.get("nome", "Livre"),
            "explica": livre.get("explica", ""),
            "selo": "já vem no ARENA",
        })
    if extra and not externo:
        # Por ultimo: o recomendado e' o de sempre. Usa o mesmo id "externo" (nenhum console tem os dois).
        dados_extra = plataforma.get("externo_extra") or {}
        lista.append({
            "id": "externo",
            "titulo": dados_extra.get("titulo_escolha") or "%s (programa próprio)" % extra,
            "explica": dados_extra.get("motivo_escolha") or "Abre no %s, o programa feito para isto." % extra,
            "selo": dados_extra.get("selo_escolha", ""),
        })
    return lista


def escolher(lista, pedido=None, lembrado=None):
    """Qual jeito usar: o que a pessoa pediu agora, senao o que ela pediu
    para lembrar, senao o unico que existe. None = perguntar (ha mais de um
    e nenhum escolhido). Escolha que nao existe mais (a BIOS saiu da pasta)
    nao vale."""
    ids = [jeito["id"] for jeito in lista]
    for escolha in (pedido, lembrado):
        if escolha in ids:
            return escolha
    if len(ids) == 1:
        return ids[0]
    return None


def lembrado_que_vale(lembrado, partida, tem_extra):
    """A escolha lembrada, ou None se ela nao vale agora. O emulador de fora A MAIS (consoles.json -> externo_extra)
    nao vale no Jogar Junto: partida a dois e' coisa do RetroArch, e quem lembrou o PokketSX nao deve levar um erro
    ao pedir uma partida."""
    if partida and tem_extra and lembrado == "externo":
        return None
    return lembrado
