# -*- coding: utf-8 -*-
r"""Como colocar os jogos de cada console: que arquivo serve, onde vai, se pode
ser .zip e se precisa de BIOS.

Pedido do Rafael (02/10/2026): "Preciso por favor de instrucoes claras de
como adicionar os jogos e quais arquivos deve adicionar, se deve colocar
dentro de uma pasta ou um arquivo .zip como exemplo, precisa entender como
o emulador funciona e o que precisa e como fazer para ensinar de uma forma
extremamente simples de entender".

A ideia central: cada console tem a sua PRATELEIRA (a pasta
jogos\pessoais\<console>). O jogo vai na prateleira certa, do jeito que
aquele aparelho "le": cartucho e' um arquivo; CD e' um disco (um .chd, ou
o .cue com os .bin juntos); fliperama e' o .zip inteiro, com o nome curto.

De onde vem cada informacao:
  - pasta e formatos aceitos: servidor\consoles.json (o mesmo que o
    indexador usa -- a tela nunca fica desatualizada);
  - nome das BIOS: as listas "firmware" dos proprios nucleos
    (retroarch\info\*.info), resumidas aqui ao que importa para o aluno;
  - "ja esta na pasta?": conferido na hora em retroarch\system.

Regra de .zip conferida em 02/10/2026: nenhum nucleo desta pasta pede o
.zip intacto ("block_extract") -- o RetroArch abre o zip de cartucho
sozinho; o MAME, o FBNeo e o DOSBox abrem o zip direto. Disco de CD em .zip
NAO abre (o RetroArch tira so um arquivo do zip, e o .cue precisa dos .bin
ao lado). Os emuladores de fora (PCSX2, Dolphin, RPCS3, Xenia) nao abrem zip.
"""
import os

# O tipo do jogo decide a regra do .zip e o jeito de guardar.
TIPOS = {
    "cartucho": {
        "zip": "pode",
        "regra_zip": "Pode ser .zip com UM jogo dentro: o ARENA abre sem descompactar.",
        "como": "Um arquivo por jogo, solto na pasta (ou numa subpasta, para organizar).",
    },
    "computador": {
        "zip": "pode",
        "regra_zip": "Pode ser .zip com UM jogo dentro: o ARENA abre sem descompactar.",
        "como": "Um arquivo por jogo (disquete, fita ou cartucho do computador).",
    },
    "disco": {
        "zip": "nao",
        "regra_zip": "NÃO use .zip: disco de CD dentro de zip não abre. Descompacte antes.",
        "como": ("Um arquivo por disco. O melhor é o .chd (um arquivo só, menor). Se veio como "
                 ".cue + .bin, deixe os dois JUNTOS na mesma pasta — a lista mostra só o .cue. "
                 "Jogo de vários discos: deixe todos na mesma pasta com (Disc 1), (Disc 2) no "
                 "nome; o ARENA junta num jogo só."),
    },
    "fliperama": {
        "zip": "obrigatorio",
        "regra_zip": ("O jogo É o .zip, com o nome curto que o emulador conhece (mslugx.zip, "
                      "kof97.zip). NÃO descompacte e NÃO troque o nome."),
        "como": ("Um .zip por jogo. Jogo com disco (.chd): numa pasta com o mesmo nome do zip, ao "
                 "lado dele (kinst.zip e a pasta kinst com o kinst.chd). Na hora de jogar, a ficha "
                 "é o Select."),
    },
    "externo": {
        "zip": "nao",
        "regra_zip": "NÃO use .zip: este emulador não abre zip. Descompacte antes.",
        "como": "Um arquivo por disco, solto na pasta (ou numa pasta só dele).",
    },
    "dos": {
        "zip": "pode",
        "regra_zip": "Pode: um .zip com o jogo dentro funciona direto (o DOSBox abre o zip).",
        "como": "A pasta do jogo inteira (o ARENA abre o .exe) ou um .zip com o jogo dentro.",
    },
    "scummvm": {
        "zip": "nao",
        "regra_zip": "Não use .zip: a pasta do jogo precisa estar aberta.",
        "como": ("A PASTA do jogo com os arquivos originais e, dentro dela, um arquivo de texto "
                 "chamado <nome>.scummvm com o código do jogo do ScummVM (ex.: monkey)."),
    },
}

# Por console: o tipo, um exemplo e a BIOS (quando precisa). "uma": basta
# uma das da lista; "todas": precisa de todas. Nomes conferidos nas listas
# "firmware" dos nucleos (retroarch\info).
CONSOLES = {
    "ps1": {"tipo": "disco", "exemplo": "Crash Bandicoot (USA).chd",
            "bios": ("uma", ["scph5501.bin", "scph5500.bin", "scph5502.bin", "scph1001.bin"],
                     "Uma BIOS de PlayStation (qualquer região serve).")},
    "segacd": {"tipo": "disco", "exemplo": "Sonic CD (USA).chd",
               "bios": ("uma", ["bios_CD_U.bin", "bios_CD_E.bin", "bios_CD_J.bin"],
                        "A BIOS da região do jogo: _U = EUA, _E = Europa, _J = Japão.")},
    "saturn": {"tipo": "disco", "exemplo": "Saturn Bomberman (USA).chd",
               "bios": ("uma", ["sega_101.bin", "mpr-17933.bin"],
                        "sega_101.bin (Japão) ou mpr-17933.bin (EUA e Europa).")},
    "dreamcast": {"tipo": "disco", "exemplo": "Marvel vs. Capcom 2 (USA).chd",
                  "bios": ("uma", ["dc/dc_boot.bin"],
                           "Recomendada: dc_boot.bin dentro de uma pasta dc (retroarch\\system\\dc). "
                           "Sem ela alguns jogos travam (ex.: Marvel vs. Capcom 1)."),
                  "dica": "Também abre .gdi (com as trilhas na mesma pasta) e .cdi."},
    "pcfx": {"tipo": "disco", "bios": ("todas", ["pcfx.rom"], "pcfx.rom.")},
    "threedo": {"tipo": "disco", "bios": ("uma", ["panafz10.bin", "panafz1.bin", "goldstar.bin"],
                                          "Uma BIOS de 3DO (panafz10.bin é a mais comum).")},
    "cdi": {"tipo": "disco", "bios": ("todas", ["same_cdi/bios/cdimono1.zip"],
                                      "cdimono1.zip dentro de retroarch\\system\\same_cdi\\bios.")},
    "psp": {"tipo": "disco", "exemplo": "Burnout Legends (Europe).iso",
            "dica": "O .cso é o .iso comprimido (menor). PSP não precisa de BIOS."},
    "arcade": {"tipo": "fliperama", "exemplo": "kinst.zip",
               "dica": ("O romset precisa ser da mesma versão do MAME do ARENA: se faltar arquivo, o "
                        "cartão avisa qual. Placas com BIOS própria (ex.: neogeo.zip) vão na mesma pasta.")},
    "neogeo": {"tipo": "fliperama", "exemplo": "mslugx.zip",
               "bios": ("todas", ["neogeo.zip"],
                        "neogeo.zip, na mesma pasta dos jogos (ou em retroarch\\system).")},
    "ps2": {"tipo": "externo", "exemplo": "Crash Nitro Kart (USA).iso",
            "bios": ("ps2", [], "Uma BIOS de PS2 (um arquivo .bin de 4 MB) em retroarch\\system: o "
                               "ARENA copia para o PCSX2 sozinho."),
            "dica": "Também abre .chd."},
    "gamecube": {"tipo": "externo", "exemplo": "Super Smash Bros. Melee (USA).rvz",
                 "dica": "O .rvz é o melhor (comprimido, sem perder nada). GameCube não precisa de BIOS."},
    "wii": {"tipo": "externo", "exemplo": "Mario Kart Wii (USA).rvz",
            "dica": "Também .wbfs e .iso. Wii não precisa de BIOS."},
    "ps3": {"tipo": "externo", "exemplo": "Borderlands 2 (USA).iso",
            "bios": ("ps3", [], "O firmware oficial do PS3 (PS3UPDAT.PUP), instalado UMA vez pelo próprio "
                               "RPCS3: menu File, Install Firmware."),
            "dica": "Jogo digital: o .pkg. Precisa de computador forte (o PS3 pesa muito)."},
    "xbox360": {"tipo": "externo", "exemplo": "Halo 3 (USA).iso",
                "dica": ("Também .xex. Precisa de processador com AVX (o Celeron N5100 da escola não "
                         "tem: lá o Xbox 360 não abre).")},
    "dos": {"tipo": "dos", "exemplo": "Commander Keen 1.zip"},
    "scummvm": {"tipo": "scummvm", "exemplo": "Monkey Island\\monkey.scummvm"},
    "msx": {"tipo": "computador", "exemplo": "Nome do Jogo.rom",
            "bios": ("todas", ["Machines", "Databases"],
                     "As pastas Machines e Databases do blueMSX dentro de retroarch\\system.")},
    "amiga": {"tipo": "computador", "exemplo": "Alien Breed.adf",
              "bios": ("uma", ["kick34005.A500", "kick40068.A1200"],
                       "Um Kickstart (kick34005.A500 serve para a maioria dos jogos).")},
    "c64": {"tipo": "computador", "exemplo": "Nome do Jogo.d64"},
    "spectrum": {"tipo": "computador", "exemplo": "Nome do Jogo.tzx"},
    "amstrad": {"tipo": "computador", "exemplo": "Nome do Jogo.dsk"},
    "megadrive": {"tipo": "cartucho", "exemplo": "Sonic The Hedgehog 3 (USA).md",
                  "dica": "Master System (.sms) e Game Gear (.gg) também vão nesta pasta."},
    "atari5200": {"tipo": "cartucho", "bios": ("uma", ["5200.rom"], "Recomendada: 5200.rom.")},
    "lynx": {"tipo": "cartucho", "bios": ("uma", ["lynxboot.img"], "Recomendada: lynxboot.img.")},
    "odyssey2": {"tipo": "cartucho", "bios": ("todas", ["o2rom.bin"], "o2rom.bin.")},
    "colecovision": {"tipo": "cartucho", "bios": ("todas", ["colecovision.rom"], "colecovision.rom.")},
    "intellivision": {"tipo": "cartucho", "bios": ("todas", ["exec.bin", "grom.bin"], "exec.bin e grom.bin.")},
    "nes": {"tipo": "cartucho", "exemplo": "Contra (USA).nes"},
    "snes": {"tipo": "cartucho", "exemplo": "Donkey Kong Country (USA).sfc"},
    "gameboy": {"tipo": "cartucho", "exemplo": "Tetris (World).gb",
                "dica": "Game Boy Color (.gbc) também vai nesta pasta."},
    "gba": {"tipo": "cartucho", "exemplo": "Nome do Jogo (USA).gba"},
    "n64": {"tipo": "cartucho", "exemplo": "GoldenEye 007 (USA).z64"},
    "nds": {"tipo": "cartucho", "exemplo": "Nome do Jogo (USA).nds"},
    "j2me": {"tipo": "cartucho", "exemplo": "Nome do Jogo.jar"},
}

LEGENDA_ZIP = {"pode": "Pode ser .zip", "nao": "Não pode ser .zip", "obrigatorio": "Tem que ser .zip"}


def _tem(pasta_sistema, relativo):
    """O arquivo (ou pasta) de BIOS existe em retroarch\\system? Sem
    diferenca de maiuscula e minuscula, como o Windows."""
    caminho = os.path.join(pasta_sistema, *relativo.split("/"))
    if os.path.exists(caminho):
        return True
    pasta, nome = os.path.split(caminho)
    try:
        return nome.lower() in {n.lower() for n in os.listdir(pasta)}
    except OSError:
        return False


def guia(plataformas, pasta_sistema, pasta_jogos, falta_externo=None):
    """O guia de cada console, na ordem do consoles.json.

    'falta_externo': {id: frase do que falta} dos emuladores de fora (BIOS
    do PS2, firmware do PS3), calculado por quem chama (graficos)."""
    falta_externo = falta_externo or {}
    saida = []
    for plataforma in plataformas:
        info = CONSOLES.get(plataforma["id"], {})
        tipo = info.get("tipo") or ("externo" if plataforma.get("externo") else "cartucho")
        regras = TIPOS[tipo]
        formatos = list(plataforma.get("extensoes") or [])
        exemplo = info.get("exemplo") or "Nome do Jogo%s" % (formatos[0] if formatos else "")
        bios = None
        if info.get("bios"):
            regra, arquivos, texto = info["bios"]
            if regra in ("ps2", "ps3"):
                presentes = [] if falta_externo.get(plataforma["id"]) else ["ok"]
                bios = {"texto": texto, "arquivos": [], "tem": bool(presentes)}
            else:
                lista = [{"arquivo": a.replace("/", "\\"), "tem": _tem(pasta_sistema, a)} for a in arquivos]
                tem = (any if regra == "uma" else all)(item["tem"] for item in lista)
                bios = {"texto": texto, "arquivos": lista, "tem": tem, "regra": regra}
        saida.append({
            "id": plataforma["id"],
            "nome": plataforma.get("nome", plataforma["id"]),
            "pasta": "jogos\\pessoais\\" + plataforma.get("pasta", plataforma["id"]),
            "pasta_existe": os.path.isdir(os.path.join(pasta_jogos, "pessoais", plataforma.get("pasta", ""))),
            "tipo": tipo,
            "formatos": formatos,
            "zip": regras["zip"],
            "zip_titulo": LEGENDA_ZIP[regras["zip"]],
            "zip_texto": regras["regra_zip"],
            "como": regras["como"],
            "exemplo": "jogos\\pessoais\\%s\\%s" % (plataforma.get("pasta", plataforma["id"]), exemplo),
            "bios": bios,
            "dica": info.get("dica", ""),
            "emulador": (plataforma.get("externo") or {}).get("nome", ""),
        })
    return saida
