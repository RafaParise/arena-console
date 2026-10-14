# -*- coding: utf-8 -*-
r"""
ARENA - o catalogo de todas as BIOS que os consoles do ARENA usam.

Pedido do Rafael (03/10/2026): "faca o ARENA criar pastas de todas as BIOS
necessarias para ler e organizar, assim qualquer um pode saber quantas BIOS
precisam baixar no total para jogar todos os emuladores que o ARENA
possibilita (...) lembre-se que o ARENA tem que ser tudo facil, simples de
entender e intuitivo".

Cada linha do CATALOGO e' uma BIOS: em que prateleira da pasta BIOS\ ela
fica (BIOS\<pasta>\<sub>), para onde o ARENA a copia para o emulador achar
(destino, dentro de retroarch\system), e o que acontece sem ela (nivel):

  precisa - os jogos do console (ou daquela regiao) nao abrem;
  alguns  - so alguns jogos precisam dela (Satellaview, Disk System, CD...);
  melhor  - o console abre sem ela; com ela, mais fiel.

De onde veio cada nome: das listas "firmware" dos .info dos nucleos que o
ARENA usa (retroarch\info), conferidas uma a uma em 03/10/2026. A marca da
versao certa (MD5) vem das notas desses mesmos .info (servidor\bios.py).
Ficaram de fora, de proposito: arquivos que so mudam a abertura (bios_MD.bin,
a do Master System), os de outro modelo do aparelho (c52.bin, frances), as
BIOS de placa de fliperama (pgm.zip, naomi.zip... sao parte do romset e o
cartao do jogo avisa qual falta) e o que nao e' BIOS (paleta, Game Genie).

PlayStation 1 e 2: o emulador acha a BIOS pelo CONTEUDO (qualquer nome
serve) e uma de qualquer regiao abre os jogos de todas (testado em
03/10/2026: o Crash 3 europeu abre com a americana) -- grupo "uma".
A regiao vem gravada dentro do arquivo.
"""
import io
import re
import zipfile

# A pasta de cada console tem o MESMO nome da pasta de jogos dele
# (jogos\pessoais\PS1 <-> BIOS\PS1); entre parenteses, a parte do console
# que precisa dela (o Satellaview e' um acessorio do Super Nintendo).
# Sem a BIOS do PS1, o ARENA abre os jogos pelo PCSX ReARMed, que imita a
# BIOS (consoles.json -> core_sem_bios; o CTR abriu assim em 14/10/2026).
SEM_ELA_PS1 = ("a maioria dos jogos abre com a imitação da BIOS (o ARENA usa o PCSX ReARMed), "
               "mas alguns travam; com ela, o ARENA usa o SwanStation, mais fiel")
CATALOGO = [
    # ---- PlayStation 1: basta uma, de qualquer regiao ----------------------
    {"id": "ps1-eua", "console": "ps1", "pasta": "PS1", "sub": "EUA", "regiao": "A",
     "nome": "scph5501.bin", "pelo_conteudo": "ps1", "grupo": "uma", "nivel": "alguns", "tamanho": 524288,
     "o_que": "a BIOS do PlayStation americano (ex.: scph5501.bin, SCPH1001.BIN)", "sem_ela": SEM_ELA_PS1},
    {"id": "ps1-europa", "console": "ps1", "pasta": "PS1", "sub": "Europa", "regiao": "E",
     "nome": "scph5502.bin", "pelo_conteudo": "ps1", "grupo": "uma", "nivel": "alguns", "tamanho": 524288,
     "o_que": "a BIOS do PlayStation europeu (ex.: scph5502.bin)", "sem_ela": SEM_ELA_PS1},
    {"id": "ps1-japao", "console": "ps1", "pasta": "PS1", "sub": "Japão", "regiao": "J",
     "nome": "scph5500.bin", "pelo_conteudo": "ps1", "grupo": "uma", "nivel": "alguns", "tamanho": 524288,
     "o_que": "a BIOS do PlayStation japonês (ex.: scph5500.bin)", "sem_ela": SEM_ELA_PS1},
    # ---- PlayStation 2: basta uma; o ARENA passa ao PCSX2 ------------------
    {"id": "ps2-eua", "console": "ps2", "pasta": "PS2", "sub": "EUA", "regiao": "A",
     "nome": "scph39001.bin", "pelo_conteudo": "ps2", "grupo": "uma", "nivel": "precisa", "tamanho": 4194304,
     "o_que": "a BIOS do PlayStation 2 americano (um .bin de 4 MB, ex.: scph39001.bin)"},
    {"id": "ps2-europa", "console": "ps2", "pasta": "PS2", "sub": "Europa", "regiao": "E",
     "nome": "scph70004.bin", "pelo_conteudo": "ps2", "grupo": "uma", "nivel": "precisa", "tamanho": 4194304,
     "o_que": "a BIOS do PlayStation 2 europeu (um .bin de 4 MB, ex.: SCPH-70004)"},
    {"id": "ps2-japao", "console": "ps2", "pasta": "PS2", "sub": "Japão", "regiao": "J",
     "nome": "scph10000.bin", "pelo_conteudo": "ps2", "grupo": "uma", "nivel": "precisa", "tamanho": 4194304,
     "o_que": "a BIOS do PlayStation 2 japonês (um .bin de 4 MB, ex.: scph10000.bin)"},
    # ---- PlayStation 3: o firmware, instalado uma vez pelo RPCS3 -----------
    {"id": "ps3-firmware", "console": "ps3", "pasta": "PS3", "sub": "", "especial": "ps3",
     "nivel": "precisa", "o_que": "o firmware oficial do PS3 (o arquivo PS3UPDAT.PUP, do site da Sony)",
     "sem_ela": "os jogos de PS3 não abrem. Ponha o PS3UPDAT.PUP na pasta e instale pelo RPCS3 "
                "(menu File → Install Firmware)"},
    # ---- Sega CD e Saturn: uma por regiao (o jogo so abre com a da regiao dele)
    {"id": "segacd-eua", "console": "segacd", "pasta": "Sega CD", "sub": "EUA", "destino": "bios_CD_U.bin",
     "nivel": "precisa", "tamanho": 131072, "o_que": "a BIOS do Sega CD americano",
     "sem_ela": "os jogos americanos do Sega CD não abrem"},
    {"id": "segacd-europa", "console": "segacd", "pasta": "Sega CD", "sub": "Europa", "destino": "bios_CD_E.bin",
     "nivel": "precisa", "tamanho": 131072, "o_que": "a BIOS do Mega-CD europeu",
     "sem_ela": "os jogos europeus do Sega CD não abrem"},
    {"id": "segacd-japao", "console": "segacd", "pasta": "Sega CD", "sub": "Japão", "destino": "bios_CD_J.bin",
     "nivel": "precisa", "tamanho": 131072, "o_que": "a BIOS do Mega-CD japonês",
     "sem_ela": "os jogos japoneses do Sega CD não abrem"},
    {"id": "saturn-eua-europa", "console": "saturn", "pasta": "Sega Saturn", "sub": "EUA e Europa",
     "destino": "mpr-17933.bin", "nivel": "precisa", "tamanho": 524288,
     "o_que": "a BIOS do Saturn americano e europeu",
     "sem_ela": "os jogos americanos e europeus do Saturn não abrem"},
    {"id": "saturn-japao", "console": "saturn", "pasta": "Sega Saturn", "sub": "Japão", "destino": "sega_101.bin",
     "nivel": "precisa", "tamanho": 524288, "o_que": "a BIOS do Saturn japonês",
     "sem_ela": "os jogos japoneses do Saturn não abrem"},
    {"id": "saturn-kof95", "console": "saturn", "pasta": "Sega Saturn", "sub": "Cartuchos",
     "destino": "mpr-18811-mx.ic1", "nivel": "alguns", "tamanho": 2097152,
     "o_que": "o cartucho que acompanha The King of Fighters '95",
     "sem_ela": "só esse jogo não abre"},
    {"id": "saturn-ultraman", "console": "saturn", "pasta": "Sega Saturn", "sub": "Cartuchos",
     "destino": "mpr-19367-mx.ic1", "nivel": "alguns", "tamanho": 2097152,
     "o_que": "o cartucho que acompanha Ultraman: Hikari no Kyojin Densetsu",
     "sem_ela": "só esse jogo não abre"},
    # ---- Dreamcast (o dc_flash.bin, a memoria do aparelho, fica de fora: o
    # emulador cria e guarda a dele em dc\dc_nvmem.bin; um flash de outro
    # aparelho trocaria o idioma e a regiao) --------------------------------
    {"id": "dreamcast-boot", "console": "dreamcast", "pasta": "Dreamcast", "sub": "", "destino": "dc/dc_boot.bin",
     "nivel": "alguns", "tamanho": 2097152, "o_que": "a BIOS do Dreamcast",
     "sem_ela": "a maioria dos jogos abre com a imitação do emulador, mas alguns travam (ex.: Marvel vs. Capcom 1)"},
    # ---- Neo Geo: o MESMO neogeo.zip serve ao FBNeo e ao MAME (as 34 partes
    # sao iguais nas duas versoes, conferido em 03/10/2026). O MAME so procura
    # na pasta do jogo: o ARENA poe uma copia em jogos\pessoais\Arcade.
    {"id": "neogeo", "console": "neogeo", "pasta": "Neo Geo", "sub": "", "destino": "neogeo.zip",
     "tambem_na_pasta_de": ["arcade"], "pelo_conteudo": "neogeo", "nivel": "precisa",
     "o_que": "a BIOS do Neo Geo (o neogeo.zip inteiro, sem descompactar); serve ao FBNeo e ao MAME"},
    # ---- Acessorios: so os jogos deles precisam -----------------------------
    {"id": "snes-bsx", "console": "snes", "pasta": "Super Nintendo (Satellaview)", "sub": "",
     "destino": "BS-X.bin", "alternativas": ["BS-X.bios"], "nivel": "alguns", "tamanho": 1048576,
     "o_que": "o cartucho BS-X (\"BS-X - Sore wa Namae o Nusumareta Machi no Monogatari\")",
     "sem_ela": "os jogos de Satellaview (o \"BS\" no nome) não abrem"},
    {"id": "snes-sufami", "console": "snes", "pasta": "Super Nintendo (Sufami Turbo)", "sub": "",
     "destino": "STBIOS.bin", "nivel": "alguns", "tamanho": 262144, "o_que": "a BIOS do Sufami Turbo",
     "sem_ela": "os jogos de Sufami Turbo não abrem"},
    {"id": "nes-fds", "console": "nes", "pasta": "NES (Famicom Disk System)", "sub": "", "destino": "disksys.rom",
     "nivel": "alguns", "tamanho": 8192, "o_que": "a BIOS do Famicom Disk System",
     "sem_ela": "os jogos de disquete (.fds) não abrem"},
    {"id": "pce-cd", "console": "pcengine", "pasta": "PC Engine (CD)", "sub": "", "destino": "syscard3.pce",
     "nivel": "alguns", "tamanho": 262144, "o_que": "o System Card 3 do PC Engine",
     "sem_ela": "os jogos em CD do PC Engine não abrem (os de cartão abrem)"},
    {"id": "n64-64dd", "console": "n64", "pasta": "Nintendo 64 (64DD)", "sub": "", "destino": "Mupen64plus/IPL.n64",
     "nivel": "alguns", "tamanho": 4194304, "o_que": "a BIOS do 64DD (o leitor de disco do Nintendo 64)",
     "sem_ela": "os jogos de disco do 64DD não abrem (os de cartucho abrem)"},
    # ---- Consoles que nao abrem nada sem a BIOS -----------------------------
    {"id": "pcfx", "console": "pcfx", "pasta": "PC-FX", "sub": "", "destino": "pcfx.rom", "nivel": "precisa",
     "tamanho": 1048576, "o_que": "a BIOS do PC-FX"},
    {"id": "3do", "console": "threedo", "pasta": "3DO", "sub": "", "destino": "panafz10.bin", "nivel": "precisa",
     "tamanho": 1048576, "alternativas": ["panafz1.bin", "panafz10-norsa.bin", "panafz10e-anvil.bin",
                                          "panafz10e-anvil-norsa.bin", "goldstar.bin", "sanyotry.bin",
                                          "panafz1j.bin", "panafz1j-norsa.bin"],
     "o_que": "a BIOS do 3DO (panafz10.bin é a mais comum; serve qualquer uma)"},
    {"id": "cdi", "console": "cdi", "pasta": "CD-i", "sub": "", "destino": "same_cdi/bios/cdimono1.zip",
     "nivel": "precisa", "o_que": "a BIOS do CD-i (o cdimono1.zip inteiro, sem descompactar)"},
    {"id": "odyssey2", "console": "odyssey2", "pasta": "Odyssey 2", "sub": "", "destino": "o2rom.bin",
     "nivel": "precisa", "tamanho": 1024, "o_que": "a BIOS do Odyssey 2"},
    {"id": "odyssey2-g7400", "console": "odyssey2", "pasta": "Odyssey 2", "sub": "Videopac+", "destino": "g7400.bin",
     "nivel": "alguns", "tamanho": 1024, "o_que": "a BIOS do Videopac+ (G7400)",
     "sem_ela": "os jogos do Videopac+ não abrem"},
    # coleco.rom: o outro nome que o Gearcoleco aceita (o registro dele, na
    # matriz da auditoria 3: "BIOS not found: colecovision.rom or coleco.rom").
    {"id": "colecovision", "console": "colecovision", "pasta": "ColecoVision", "sub": "", "destino": "colecovision.rom",
     "nivel": "precisa", "tamanho": 8192, "alternativas": ["coleco.rom"], "o_que": "a BIOS do ColecoVision"},
    {"id": "intv-exec", "console": "intellivision", "pasta": "Intellivision", "sub": "", "destino": "exec.bin",
     "nivel": "precisa", "tamanho": 8192, "o_que": "a Executive ROM do Intellivision (exec.bin)"},
    {"id": "intv-grom", "console": "intellivision", "pasta": "Intellivision", "sub": "", "destino": "grom.bin",
     "nivel": "precisa", "tamanho": 2048, "o_que": "a Graphics ROM do Intellivision (grom.bin)"},
    # MSX: os cartuchos abrem pelo C-BIOS, a BIOS livre que vem no ARENA
    # (servidor\bios_livres; o NOBORUNOCA abriu assim em 14/10/2026, sem o
    # Machines e sem o Databases). O C-BIOS nao tem o MSX-BASIC nem o leitor
    # de disquete: disquete e fita ainda pedem o Machines de verdade.
    # 'extensoes': o jogo com esse final ganha o 'aviso' no cartao.
    {"id": "msx-machines", "console": "msx", "pasta": "MSX", "sub": "", "destino": "Machines", "e_pasta": True,
     "nivel": "alguns", "o_que": "a pasta Machines do blueMSX (a pasta inteira)", "extensoes": [".dsk", ".cas"],
     "sem_ela": ("os jogos de disquete (.dsk) e de fita (.cas) não abrem; os de cartucho (.rom) abrem pelo "
                 "C-BIOS, a BIOS livre que já vem no ARENA"),
     "aviso": ("Jogo de disquete ou de fita: ele só abre com a BIOS de verdade do MSX, a pasta Machines do "
               "blueMSX. Os jogos de cartucho (.rom) abrem sem ela, pelo C-BIOS, a BIOS livre que já vem no "
               "ARENA.")},
    {"id": "msx-databases", "console": "msx", "pasta": "MSX", "sub": "", "destino": "Databases", "e_pasta": True,
     "nivel": "melhor", "o_que": "a pasta Databases do blueMSX (a pasta inteira)",
     "sem_ela": ("o console abre do mesmo jeito: o emulador adivinha o tipo de cada cartucho; com ela, o tipo vem "
                 "da lista do blueMSX e acerta também os cartuchos grandes mais difíceis")},
    {"id": "amiga-a500", "console": "amiga", "pasta": "Amiga", "sub": "A500", "destino": "kick34005.A500",
     "nivel": "precisa", "tamanho": 262144, "o_que": "o Kickstart 1.3 do Amiga 500 (serve para a maioria dos jogos)"},
    {"id": "amiga-a1200", "console": "amiga", "pasta": "Amiga", "sub": "A1200", "destino": "kick40068.A1200",
     "nivel": "alguns", "tamanho": 524288, "o_que": "o Kickstart 3.1 do Amiga 1200",
     "sem_ela": "os jogos de Amiga 1200 (AGA) não abrem"},
    {"id": "amiga-cd32", "console": "amiga", "pasta": "Amiga", "sub": "CD32", "destino": "kick40060.CD32",
     "nivel": "alguns", "tamanho": 524288, "o_que": "o Kickstart do Amiga CD32",
     "sem_ela": "os jogos de CD32 não abrem"},
    {"id": "amiga-cd32-ext", "console": "amiga", "pasta": "Amiga", "sub": "CD32", "destino": "kick40060.CD32.ext",
     "nivel": "alguns", "tamanho": 524288, "o_que": "a ROM estendida do Amiga CD32",
     "sem_ela": "os jogos de CD32 não abrem"},
    # ---- Abrem sem; com a BIOS, ficam mais fieis ----------------------------
    # Atari ST: sem o TOS original, liga pelo EmuTOS, a BIOS livre que vem no
    # ARENA (servidor\bios_livres; o Rayoid abriu assim em 14/10/2026). O TOS
    # de verdade, posto na prateleira, entra no lugar dele.
    {"id": "atarist-tos", "console": "atarist", "pasta": "Atari ST", "sub": "", "destino": "tos.img",
     "nivel": "melhor", "tamanho": 196608, "o_que": "o TOS original do Atari ST",
     "sem_ela": ("o Atari ST liga do mesmo jeito, pelo EmuTOS, a BIOS livre que já vem no ARENA: a maioria dos "
                 "jogos abre; com o TOS original, os poucos que não abrem passam a abrir")},
    {"id": "atari5200", "console": "atari5200", "pasta": "Atari 5200", "sub": "", "destino": "5200.rom",
     "nivel": "melhor", "tamanho": 2048, "o_que": "a BIOS do Atari 5200"},
    {"id": "atari7800", "console": "atari7800", "pasta": "Atari 7800", "sub": "", "destino": "7800 BIOS (U).rom",
     "nivel": "melhor", "tamanho": 4096, "o_que": "a BIOS do Atari 7800"},
    {"id": "lynx", "console": "lynx", "pasta": "Atari Lynx", "sub": "", "destino": "lynxboot.img",
     "nivel": "melhor", "tamanho": 512, "o_que": "a BIOS do Atari Lynx"},
    {"id": "gba", "console": "gba", "pasta": "Game Boy Advance", "sub": "", "destino": "gba_bios.bin",
     "nivel": "melhor", "tamanho": 16384, "o_que": "a BIOS do Game Boy Advance"},
    {"id": "gb", "console": "gameboy", "pasta": "Game Boy", "sub": "", "destino": "gb_bios.bin",
     "nivel": "melhor", "tamanho": 256, "o_que": "a BIOS do Game Boy (a abertura do aparelho)"},
    {"id": "gbc", "console": "gameboy", "pasta": "Game Boy", "sub": "", "destino": "gbc_bios.bin",
     "nivel": "melhor", "tamanho": 2304, "o_que": "a BIOS do Game Boy Color (a abertura do aparelho)"},
    {"id": "nds-bios7", "console": "nds", "pasta": "Nintendo DS", "sub": "", "destino": "bios7.bin",
     "nivel": "melhor", "tamanho": 16384, "o_que": "a BIOS ARM7 do Nintendo DS"},
    {"id": "nds-bios9", "console": "nds", "pasta": "Nintendo DS", "sub": "", "destino": "bios9.bin",
     "nivel": "melhor", "tamanho": 4096, "o_que": "a BIOS ARM9 do Nintendo DS"},
    {"id": "nds-firmware", "console": "nds", "pasta": "Nintendo DS", "sub": "", "destino": "firmware.bin",
     "nivel": "melhor", "tamanho": 262144, "o_que": "o firmware do Nintendo DS"},
    {"id": "pokemini", "console": "pokemini", "pasta": "Pokemon mini", "sub": "", "destino": "bios.min",
     "nivel": "melhor", "tamanho": 4096, "o_que": "a BIOS do Pokémon mini"},
]

NIVEIS = ("precisa", "alguns", "melhor")
TITULO_DO_NIVEL = {"precisa": "OS JOGOS PRECISAM (sem ela, não abrem)", "alguns": "SÓ PARA ALGUNS JOGOS",
                   "melhor": "OPCIONAIS (o console abre sem; com ela, fica mais fiel)"}
SEM_ELA = {"precisa": "os jogos deste console não abrem", "alguns": "alguns jogos não abrem",
           "melhor": "o console abre do mesmo jeito; com ela, fica mais fiel ao aparelho de verdade"}
NOME_DA_REGIAO_PS = {"A": "EUA", "E": "Europa", "J": "Japão"}

# Partes do neogeo.zip que provam que ele e' a BIOS do Neo Geo (CRC32 de
# 000-lo.lo, sfix.sfix e sm1.sm1, iguais nas versoes do MAME e do FBNeo).
PARTES_NEOGEO = {0x5A86CFF2, 0xC2EA0CFD, 0x94416D67}


def por_id():
    return {e["id"]: e for e in CATALOGO}


def do_console(console):
    return [e for e in CATALOGO if e["console"] == console]


def nome_de_instalacao(entrada):
    """O nome do arquivo em retroarch\\system ("dc_boot.bin" de "dc/dc_boot.bin")."""
    return (entrada.get("destino") or entrada.get("nome") or "").split("/")[-1]


def nomes_aceitos(entrada):
    """Os nomes que valem como esta BIOS em retroarch\\system, em minusculas."""
    nomes = [nome_de_instalacao(entrada)] + list(entrada.get("alternativas", []))
    return [n.lower() for n in nomes if n]


def rotulo(entrada):
    """"Sega CD — Europa", "Dreamcast": como a BIOS aparece na lista e no LEIA."""
    return entrada["pasta"] + (" — " + entrada["sub"] if entrada.get("sub") else "")


def regiao_ps1(dados):
    """'A', 'E' ou 'J' da BIOS de PS1 ("System ROM Version 2.2 12/04/95 A"),
    ou None se nao e' uma BIOS de PS1."""
    if not dados or len(dados) != 524288:
        return None
    achado = re.search(rb"System ROM Version (\d\.\d) (\d\d/\d\d/\d\d) ([AEJ])", dados)
    return achado.group(3).decode() if achado else None


def versao_ps1(dados):
    """'versão 2.2, de 04/12/1995' da BIOS de PS1 (a data vem em mes/dia/ano
    americano: "12/04/95" e' 4 de dezembro), ou ''."""
    achado = re.search(rb"System ROM Version (\d\.\d) (\d\d)/(\d\d)/(\d\d)", dados or b"")
    if not achado:
        return ""
    versao, mes, dia, ano = (x.decode() for x in achado.groups())
    return "versão %s, de %s/%s/%s" % (versao, dia, mes, ("19" if int(ano) >= 90 else "20") + ano)


# ROMVER da BIOS de PS2: "0160EC20011004" = versao 01.60, E (Europa), C
# (console), 2001-10-04. E' o que o PCSX2 mostra ("Europe v01.60(04/10/2001)
# Console"). Letras de regiao do PCSX2: A EUA, E Europa, J Japao, C China,
# H Hong Kong, T (T10K), R Russia, U Reino Unido.
_RE_ROMVER = re.compile(rb"(\d{2})(\d{2})([AEJCHTRU])([CDTXP])(\d{4})(\d{2})(\d{2})")


def _romver(dados):
    if not dados or len(dados) != 4194304:
        return None
    posicao = dados.find(b"ROMVER", 0, 0x100000)
    if posicao < 0:
        return None
    return (_RE_ROMVER.search(dados, posicao, posicao + 0x40000)
            or _RE_ROMVER.search(dados, 0, 0x100000))


def regiao_ps2(dados):
    """'A', 'E' ou 'J' da BIOS de PS2, ou None se nao e' uma."""
    achado = _romver(dados)
    if not achado:
        return None
    letra = achado.group(3).decode()
    return {"C": "J", "H": "J", "T": "J", "R": "E", "U": "E"}.get(letra, letra)


def versao_ps2(dados):
    """'v01.60, de 04/10/2001' -- o mesmo que o PCSX2 mostra --, ou ''."""
    achado = _romver(dados)
    if not achado:
        return ""
    g = [x.decode() for x in achado.groups()]
    return "v%s.%s, de %s/%s/%s" % (g[0], g[1], g[6], g[5], g[4])


def e_neogeo_zip(dados):
    """Os bytes sao de um .zip que e' a BIOS do Neo Geo (tem 000-lo, sfix e sm1)?"""
    try:
        with zipfile.ZipFile(io.BytesIO(dados)) as z:
            return PARTES_NEOGEO <= {i.CRC for i in z.infolist()}
    except (zipfile.BadZipFile, ValueError, RuntimeError, OSError):
        return False
