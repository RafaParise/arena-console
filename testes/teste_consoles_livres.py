# -*- coding: utf-8 -*-
r"""Consoles livres: cada jogo de testes\jogos_livres abre no nucleo de
verdade com SO as BIOS livres do ARENA (servidor\bios_livres) na pasta
system -- nenhuma BIOS das empresas.

Pedido do Rafael (12/10/2026): todos os consoles possiveis, "integrar
emuladores sem precisar baixar BIOS". Para cada jogo da lista.json:
  1. ABRE: o RetroArch roda alguns segundos com as opcoes do ARENA e tira a
     foto da tela (--max-frames-ss). A foto tem que ter imagem de verdade:
     mais de uma cor, e a cor mais comum cobrindo menos de 99,5% da tela (o
     tamanho do arquivo nao serve: a tela do CHIP-8 tem 128x64 pontos).
  2. O REGISTRO prova o caminho livre, quando o console tem um (no MSX:
     "falling back to 'MSX2+ - C-BIOS'").
  3. COM ACENTO: o mesmo jogo, com a pasta system e o jogo numa pasta com
     "ó" no nome (o ARENA do Rafael mora em "...Pedagógicos\...").
  4. Com --junto: hospedeiro e convidado de verdade em 127.0.0.1 (o Jogar
     Junto), para conferir o que o consoles.json diz do console.

Seis consoles nao tem jogo livre publicado que sirva (Atari 8-bit,
Commodore PET e 128, Watara Supervision, Thomson e Vircon32, cujo menor jogo
oficial tem 18 MB): para eles o teste
escreve na hora um programinha (GERADOS, sem binario novo no git), e a foto
tem que mostrar a cor que o programa pinta -- a tela de partida do console
nao tem essa cor, entao a cor prova que o programa rodou.

Uso:
    servidor\python\python.exe testes\teste_consoles_livres.py [pedaco do console] [--junto]
"""
import collections
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
sys.path.insert(0, os.path.join(RAIZ, "ferramentas"))
import bios  # noqa: E402
import limpeza  # noqa: E402
import ponte_sem_acento  # noqa: E402
import protege_cfg  # noqa: E402
import teste_matriz_multitap as base  # noqa: E402
from gravar_fundo_gif import ler_png  # noqa: E402

PASTA_JOGOS = os.path.join(AQUI, "jogos_livres")
RETROARCH = os.path.join(RAIZ, "retroarch", "retroarch.exe")


def disquete_st(destino, programas):
    """Um disquete de Atari ST (720 KB, FAT12) com os programas na pasta AUTO:
    o TOS (aqui, o EmuTOS) roda sozinho o que esta nela, ao ligar. O setor de
    boot nao e' executavel (a soma dele nao da 0x1234)."""
    bps, spc, reservados, fats, entradas, total, spf, spt, lados = 512, 2, 1, 2, 112, 1440, 3, 9, 2
    imagem = bytearray(total * bps)
    struct.pack_into("<HBHBHHBHHHH", imagem, 11, bps, spc, reservados, fats, entradas, total, 0xF9,
                     spf, spt, lados, 0)
    imagem[0:2] = b"\x60\x38"
    imagem[2:8] = b"ARENA "
    tamanho_cluster = bps * spc
    inicio_dados = (reservados + fats * spf + entradas * 32 // bps) * bps
    tabela = {0: 0xFF9, 1: 0xFFF}
    proximo = [2]

    def alocar(quantos):
        primeiro = proximo[0]
        for i in range(quantos):
            tabela[primeiro + i] = primeiro + i + 1 if i < quantos - 1 else 0xFFF
        proximo[0] += quantos
        return primeiro

    def gravar(cluster, dados):
        posicao = inicio_dados + (cluster - 2) * tamanho_cluster
        imagem[posicao:posicao + len(dados)] = dados

    def entrada(nome, extensao, atributo, cluster, tamanho):
        bloco = bytearray(32)
        bloco[0:8] = nome.ljust(8).encode("ascii")
        bloco[8:11] = extensao.ljust(3).encode("ascii")
        bloco[11] = atributo
        struct.pack_into("<HHHI", bloco, 22, 0, 0x5A21, cluster, tamanho)
        return bytes(bloco)

    auto = alocar(1)
    pasta = bytearray(tamanho_cluster)
    pasta[0:32] = entrada(".", "", 0x10, auto, 0)
    pasta[32:64] = entrada("..", "", 0x10, 0, 0)
    for i, caminho in enumerate(programas):
        with open(caminho, "rb") as arquivo:
            dados = arquivo.read()
        quantos = -(-len(dados) // tamanho_cluster)
        primeiro = alocar(quantos)
        for k in range(quantos):
            gravar(primeiro + k, dados[k * tamanho_cluster:(k + 1) * tamanho_cluster])
        nome, extensao = os.path.splitext(os.path.basename(caminho).upper())
        pasta[64 + 32 * i:96 + 32 * i] = entrada(nome, extensao[1:], 0x20, primeiro, len(dados))
    gravar(auto, pasta)
    raiz = (reservados + fats * spf) * bps
    imagem[raiz:raiz + 32] = entrada("AUTO", "", 0x10, auto, 0)
    fat = bytearray(spf * bps)
    for c in range(0, max(tabela) + 2, 2):
        a, b = tabela.get(c, 0), tabela.get(c + 1, 0)
        fat[c * 3 // 2:c * 3 // 2 + 3] = bytes([a & 0xFF, ((a >> 8) & 0x0F) | ((b & 0x0F) << 4), (b >> 4) & 0xFF])
    for k in range(fats):
        posicao = (reservados + k * spf) * bps
        imagem[posicao:posicao + len(fat)] = fat
    with open(destino, "wb") as arquivo:
        arquivo.write(imagem)


# ---------------------------------------------------------------------------
# Programas escritos pelo proprio teste (15/10/2026), em codigo de maquina ou
# em BASIC ja convertido em fichas (tokens), byte a byte.
# ---------------------------------------------------------------------------

def basic_commodore(endereco, linhas):
    """Um programa BASIC da Commodore como o LOAD o le: o endereco de carga e,
    em cada linha, o endereco da linha seguinte, o numero da linha, o texto
    (com as palavras do BASIC ja trocadas por fichas) e um zero. Dois zeros
    no fim."""
    corpo = bytearray()
    for numero, texto in linhas:
        linha = struct.pack("<H", numero) + texto + b"\x00"
        proxima = endereco + len(corpo) + 2 + len(linha)
        corpo += struct.pack("<H", proxima) + linha
    return struct.pack("<H", endereco) + bytes(corpo) + b"\x00\x00"


def prg_pet():
    """PET (BASIC 4.0, que comeca em $0401): enche a tela de espacos
    invertidos (o 160), e a tela inteira acende em verde. O 34767 cobre a
    tela de 80 colunas; na de 40, a memoria de video se repete."""
    return basic_commodore(0x0401, [
        (10, b"\x81I\xb232768\xa434767:\x97I,160:\x82"),   # FOR I=32768 TO 34767:POKE I,160:NEXT
        (20, b"\x8920"),                                   # GOTO 20
    ])


def prg_c128():
    """C128 (BASIC 7.0, que comeca em $1C01): o COLOR so existe no BASIC do
    128, entao o fundo vermelho prova que ele ligou no modo 128."""
    return basic_commodore(0x1C01, [
        (10, b"\xe70,3:\xe74,1:\xe75,2"),     # COLOR 0,3:COLOR 4,1:COLOR 5,2 (fundo vermelho, borda preta)
        (20, b"\x99\"ARENA\""),               # PRINT "ARENA"
        (30, b"\x8930"),                      # GOTO 30
    ])


def xex_atari():
    """Atari 8-bit: um executavel .xex (FF FF, depois os trechos com o
    endereco de inicio e de fim). Pinta o fundo de laranja escuro e escreve
    ARENA direto na memoria da tela. Quem roda e' o AltirraOS, o sistema
    livre que vem dentro do emulador."""
    inicio = 0x3000
    codigo = bytearray([
        0xA9, 0x34, 0x8D, 0xC6, 0x02,   # LDA #$34 / STA COLOR2 (fundo)
        0xA9, 0x00, 0x8D, 0xC8, 0x02,   # LDA #$00 / STA COLOR4 (borda preta)
        0xA9, 0x0E, 0x8D, 0xC5, 0x02,   # LDA #$0E / STA COLOR1 (letra clara)
        0xA0, 0x00,                     # LDY #0
        0xB9, 0x00, 0x00,               # LDA texto,Y (o endereco entra abaixo)
        0x91, 0x58,                     # STA (SAVMSC),Y: a memoria da tela
        0xC8, 0xC0, 0x05, 0xD0, 0xF6,   # INY / CPY #5 / BNE (volta ao LDA)
        0x4C, 0x00, 0x00,               # JMP para si mesmo (o endereco entra abaixo)
    ])
    codigo[18:20] = struct.pack("<H", inicio + len(codigo))
    codigo[28:30] = struct.pack("<H", inicio + len(codigo) - 3)
    codigo += bytes([0x21, 0x32, 0x25, 0x2E, 0x21])   # ARENA no codigo de tela do Atari
    trecho = struct.pack("<HH", inicio, inicio + len(codigo) - 1) + bytes(codigo)
    partida = struct.pack("<HHH", 0x02E0, 0x02E1, inicio)   # RUNAD: onde comecar
    return b"\xFF\xFF" + trecho + partida


def rom_supervision():
    """Watara Supervision: ROM de 32 KB (o potator pede multiplo de 16 KB).
    Os ultimos 16 KB ficam em $C000-$FFFF, com os enderecos de partida no
    fim. A tela (160x160, 4 pontos por byte, 48 bytes por linha) fica em
    $4000, e so aparece depois de gravar a largura dela em $2000. O programa
    enche 20 paginas de pontos pretos: os 2/3 de cima da tela."""
    codigo = bytes([
        0x78, 0xD8, 0xA2, 0xFF, 0x9A,           # SEI / CLD / LDX #$FF / TXS
        0xA9, 0xA0, 0x8D, 0x00, 0x20,           # LDA #160 / STA $2000 (largura da tela)
        0x8D, 0x01, 0x20,                       # STA $2001 (altura)
        0xA9, 0x00, 0x8D, 0x02, 0x20,           # LDA #0 / STA $2002 (rolagem X)
        0x8D, 0x03, 0x20,                       # STA $2003 (rolagem Y)
        0x85, 0x00, 0xA9, 0x40, 0x85, 0x01,     # ponteiro em $00/$01 = $4000
        0xA2, 0x14, 0xA9, 0xFF, 0xA0, 0x00,     # LDX #20 paginas / LDA #$FF (preto) / LDY #0
        0x91, 0x00, 0xC8, 0xD0, 0xFB,           # STA ($00),Y / INY / BNE
        0xE6, 0x01, 0xCA, 0xD0, 0xF6,           # INC $01 / DEX / BNE
        0x4C, 0x2B, 0xC0,                       # JMP para si mesmo ($C02B)
        0x40,                                   # RTI ($C02E), para as interrupcoes
    ])
    rom = bytearray(b"\xFF" * 0x8000)
    rom[0x4000:0x4000 + len(codigo)] = codigo
    rom[0x7FFA:0x8000] = struct.pack("<HHH", 0xC02E, 0xC000, 0xC02E)   # NMI, partida, IRQ
    return bytes(rom)


def cartucho_mo5():
    """Thomson MO5: cartucho de 16 KB, que o MO5 liga sozinho, em $B000-$EFFF.
    O endereco de partida vai nos 2 ultimos bytes ($EFFE; sem ele, visto em
    15/10/2026, o cartucho nao roda). O programa (6809) enche a memoria de
    cor ($0000, com a cor da frente e a do fundo em cada byte) de vermelho.
    O final .m5 faz o emulador escolher o MO5."""
    codigo = bytes([
        0x1A, 0x50,                 # ORCC #$50 (sem interrupcao)
        0x10, 0xCE, 0x9F, 0x00,     # LDS #$9F00 (a pilha)
        0x86, 0x00,                 # LDA #0
        0xB7, 0xA7, 0xC0,           # STA $A7C0: memoria de cor, borda preta
        0x8E, 0x00, 0x00,           # LDX #$0000
        0x86, 0x11,                 # LDA #$11 (frente e fundo vermelhos)
        0xA7, 0x80,                 # STA ,X+
        0x8C, 0x1F, 0x40,           # CMPX #$1F40 (fim da tela)
        0x25, 0xF9,                 # BLO (volta ao STA)
        0x20, 0xFE,                 # BRA para si mesmo
    ])
    cartucho = bytearray(0x4000)
    cartucho[:len(codigo)] = codigo
    cartucho[0x3FFE:0x4000] = b"\xB0\x00"
    return bytes(cartucho)


def cartucho_vircon32():
    """Vircon32: cartucho .v32 (o cabecalho "V32-CART" de 128 bytes e o programa,
    "V32-VBIN", em palavras de 32 bits), sem textura nem som. Cada instrucao e'
    uma palavra: o codigo nos 6 bits de cima, o "usa valor imediato" no bit 25
    e a porta nos 14 de baixo; o valor imediato vem na palavra seguinte. O
    programa escolhe a textura da BIOS (-1, que vem no emulador), limpa a tela
    de vermelho e desenha a textura inteira por cima, a cada quadro."""
    def instrucao(codigo, porta=0, imediato=None):
        palavra = (codigo << 26) | ((1 << 25) if imediato is not None else 0) | porta
        return [palavra] + ([imediato] if imediato is not None else [])
    OUT, WAIT, JMP = 24, 1, 2
    preparo = (instrucao(OUT, 0x205, 0xFFFFFFFF)      # textura escolhida: -1, a da BIOS
               + instrucao(OUT, 0x206, 0)             # regiao 0 dela
               + instrucao(OUT, 0x20C, 0) + instrucao(OUT, 0x20D, 0)        # canto de cima
               + instrucao(OUT, 0x20E, 479) + instrucao(OUT, 0x20F, 327)    # canto de baixo (480 x 328)
               + instrucao(OUT, 0x210, 0) + instrucao(OUT, 0x211, 0))       # ponto de apoio
    laco = 0x20000000 + len(preparo)           # o cartucho comeca em $20000000
    programa = (preparo
                + instrucao(OUT, 0x202, 0xFF0000FF)   # cor de limpar: vermelho (R, G, B, A)
                + instrucao(OUT, 0x200, 0x10)         # comando da GPU: limpar a tela
                + instrucao(OUT, 0x207, 80) + instrucao(OUT, 0x208, 16)     # onde desenhar
                + instrucao(OUT, 0x200, 0x11)         # comando da GPU: desenhar a regiao
                + instrucao(WAIT)                     # espera o proximo quadro
                + instrucao(JMP, 0, laco))            # e de novo
    binario = b"V32-VBIN" + struct.pack("<I", len(programa)) + struct.pack("<%dI" % len(programa), *programa)
    fim = 128 + len(binario)
    cabecalho = (b"V32-CART" + struct.pack("<II", 1, 0) + b"ARENA - programa de teste".ljust(64, b"\0")
                 + struct.pack("<IIII", 1, 0, 0, 0)                       # versao 1.0, 0 texturas, 0 sons
                 + struct.pack("<IIIIII", 128, len(binario), fim, 0, fim, 0)   # onde fica cada parte
                 + b"\0" * 8)
    return cabecalho + binario


# A cor que cada programa pinta, conferida na cor mais comum da foto.
COR = {
    "avermelhada": lambda r, g, b: r > 60 and r > 1.6 * g and r > 1.6 * b,
    "verde": lambda r, g, b: g > 120 and g > r and g > b,
    "preta": lambda r, g, b: r + g + b < 60,
}

GERADOS = [
    {"console": "atari800", "jogo": "programa de teste (AltirraOS)", "arquivo": "teste.xex",
     "gerar": xex_atari, "cor": "avermelhada"},
    {"console": "pet", "jogo": "programa de teste (BASIC 4.0)", "arquivo": "teste.prg",
     "gerar": prg_pet, "cor": "verde"},
    {"console": "c128", "jogo": "programa de teste (BASIC 7.0)", "arquivo": "teste.prg",
     "gerar": prg_c128, "cor": "avermelhada"},
    {"console": "supervision", "jogo": "programa de teste", "arquivo": "teste.sv",
     "gerar": rom_supervision, "cor": "preta"},
    {"console": "thomson", "jogo": "programa de teste (cartucho do MO5)", "arquivo": "teste.m5",
     "gerar": cartucho_mo5, "cor": "avermelhada"},
    {"console": "vircon32", "jogo": "programa de teste (BIOS livre)", "arquivo": "teste.v32",
     "gerar": cartucho_vircon32, "cor": "avermelhada"},
]


# O que cada console precisa a mais: quantos quadros rodar antes da foto, o
# que o registro tem que dizer e, quando o jogo livre nao e' o arquivo que o
# nucleo abre, como montar esse arquivo.
POR_CONSOLE = {
    "msx": {"quadros": 900, "registro": r"falling back to 'MSX2\+ - C-BIOS'"},
    "atarist": {"quadros": 1500, "montar": (".st", lambda destino, origem: disquete_st(destino, [origem]))},
    "zx81": {"quadros": 1500},
    "vic20": {"quadros": 1500},
    "plus4": {"quadros": 1200},
    "chip8": {"quadros": 600},
    "apple2": {"quadros": 1800},
    "arduboy": {"quadros": 900},
    "microw8": {"quadros": 600},
    "atari800": {"quadros": 600},
    "pet": {"quadros": 1500},       # o FOR do BASIC leva uns segundos para encher a tela
    "c128": {"quadros": 1500},
    "supervision": {"quadros": 300},
    "thomson": {"quadros": 600},
    "vircon32": {"quadros": 600},   # a abertura da BIOS leva uns 3 s; o RetroArch troca para OpenGL sozinho
}


def plataformas():
    with open(os.path.join(RAIZ, "servidor", "consoles.json"), encoding="utf-8") as arquivo:
        return {p["id"]: p for p in json.load(arquivo)["plataformas"]}


def imagem_de_verdade(foto, cor=None):
    """(sim/nao, detalhe): a foto tem mais de uma cor e nenhuma cobre 99,5%? (A tela de
    texto do Apple II e o Arduboy ficam pretos em 97%: imagem de verdade.) Com 'cor'
    (do COR), a mais comum tambem tem que ser dessa cor."""
    if not os.path.isfile(foto):
        return False, "sem foto"
    with open(foto, "rb") as arquivo:
        largura, altura, pontos = ler_png(arquivo.read())
    cores = collections.Counter(p[:3] for p in pontos)
    (rgb, quantos), = cores.most_common(1)
    maior = quantos / float(len(pontos))
    ok = len(cores) > 1 and maior < 0.995
    detalhe = "%dx%d, %d cores, a mais comum em %.0f%%" % (largura, altura, len(cores), maior * 100)
    if cor:
        ok = ok and COR[cor](*rgb)
        detalhe += ", %s%s" % (rgb, "" if COR[cor](*rgb) else " (o programa pinta de " + cor + ")")
    return ok, detalhe


def abrir(jogo, nucleo, pasta, sistema, quadros):
    """Roda o jogo e devolve (foto, texto do registro, travou, usou a ponte).
    O nucleo que nao abre caminho com acento (o Hatari) vai pela MESMA ponte
    que o ARENA usa (servidor\\ponte_sem_acento.py)."""
    os.makedirs(pasta)
    cfg = base.config_base(pasta, {})
    opcoes = {"system_directory": sistema}
    jogo_do_nucleo, devolver = jogo, None
    ponte = ponte_sem_acento.precisa(nucleo, sistema, jogo)
    if ponte:
        jogo_do_nucleo, opcoes_da_ponte, devolver = ponte_sem_acento.preparar(nucleo, sistema, jogo)
        opcoes.update(opcoes_da_ponte)
    # A pasta system so com as BIOS livres (o --appendconfig aceita varios
    # arquivos separados por "|"; o ultimo vale).
    extra = os.path.join(pasta, "system.cfg")
    with open(extra, "w", encoding="utf-8") as arquivo:
        arquivo.write("".join('%s = "%s"\n' % par for par in sorted(opcoes.items())))
    foto = os.path.join(pasta, "foto.png")
    registro = os.path.join(pasta, "ra.log")
    try:
        subprocess.run([RETROARCH, "-L", os.path.join(RAIZ, "retroarch", "cores", nucleo),
                        "--appendconfig", cfg + "|" + extra, "--verbose", "--log-file", registro,
                        "--max-frames=%d" % quadros, "--max-frames-ss", "--max-frames-ss-path=" + foto,
                        jogo_do_nucleo],
                       cwd=os.path.dirname(RETROARCH), timeout=150,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        travou = False
    except subprocess.TimeoutExpired:
        travou = True
    if devolver:
        devolver()          # como o ARENA faz quando o jogo fecha: a pasta da ponte some
    texto = open(registro, encoding="utf-8", errors="ignore").read() if os.path.exists(registro) else ""
    return foto, texto, travou, ponte


def jogar_junto(jogo, nucleo, pasta, sistema):
    """O Jogar Junto de verdade (teste_matriz_multitap), com a pasta system
    das livres em cada um dos dois RetroArch."""
    original = base.config_base

    def com_sistema(sub, extras):
        # Troca a linha (nao acrescenta): com a chave repetida no mesmo
        # arquivo, o RetroArch fica com a PRIMEIRA (visto em 14/10/2026).
        cfg = original(sub, extras)
        with open(cfg, encoding="utf-8") as arquivo:
            linhas = [l for l in arquivo.read().splitlines() if not l.startswith("system_directory ")]
        with open(cfg, "w", encoding="utf-8") as arquivo:
            arquivo.write("\n".join(linhas + ['system_directory = "%s"' % sistema]) + "\n")
        return cfg

    base.config_base = com_sistema
    try:
        return base.jogar_junto(jogo, nucleo.replace("_libretro.dll", ""), pasta)
    finally:
        base.config_base = original


def main():
    filtro = " ".join(a for a in sys.argv[1:] if not a.startswith("--")).lower()
    junto = "--junto" in sys.argv
    with open(os.path.join(PASTA_JOGOS, "lista.json"), encoding="utf-8") as arquivo:
        jogos = json.load(arquivo)["arquivos"]
    todas = plataformas()
    falhas = []
    fotos = tempfile.mkdtemp(prefix="arena_livres_fotos_")
    for item in jogos + GERADOS:
        if filtro and filtro not in item["console"] and filtro not in item["jogo"].lower():
            continue
        plataforma = todas.get(item["console"])
        if not plataforma:
            falhas.append("%s: console %s nao esta no consoles.json" % (item["jogo"], item["console"]))
            continue
        regras = POR_CONSOLE.get(item["console"], {})
        print("== %s (%s, %s)" % (plataforma["nome"], item["jogo"], plataforma["core"]))
        for rotulo, prefixo in (("pasta comum", "arena_livres_"), ("pasta com acento", "arena_livres_Pedagógicos_")):
            trabalho = tempfile.mkdtemp(prefix=prefixo)
            try:
                sistema = os.path.join(trabalho, "system")
                os.makedirs(sistema)
                bios.instalar_livres(sistema)
                if item.get("gerar"):
                    jogo = os.path.join(trabalho, item["arquivo"])
                    with open(jogo, "wb") as arquivo:
                        arquivo.write(item["gerar"]())
                else:
                    origem = os.path.join(PASTA_JOGOS, *item["origem"].split("/"))
                    if regras.get("montar"):
                        extensao, montar = regras["montar"]
                        jogo = os.path.join(trabalho, os.path.splitext(os.path.basename(origem))[0].lower() + extensao)
                        montar(jogo, origem)
                    else:
                        jogo = os.path.join(trabalho, os.path.basename(origem))
                        shutil.copyfile(origem, jogo)
                foto, texto, travou, ponte = abrir(jogo, plataforma["core"], os.path.join(trabalho, "rodada"),
                                                   sistema, regras.get("quadros", 600))
                ok, detalhe = imagem_de_verdade(foto, item.get("cor"))
                if os.path.isfile(foto):
                    shutil.copyfile(foto, os.path.join(fotos, "%s - %s.png" % (item["console"], rotulo)))
                print("   %-17s imagem: %-3s (%s)%s%s" % (rotulo, "sim" if ok else "NAO", detalhe,
                                                         " TRAVOU" if travou else "",
                                                         " [pela ponte sem acento]" if ponte else ""))
                if not ok or travou:
                    falhas.append("%s, %s: sem imagem (%s)" % (plataforma["nome"], rotulo, detalhe))
                if regras.get("registro"):
                    achou = bool(re.search(regras["registro"], texto))
                    print("   %-17s registro: %s" % ("", "confere" if achou else "NAO confere"))
                    if not achou:
                        falhas.append("%s, %s: o registro nao diz %r" % (plataforma["nome"], rotulo,
                                                                        regras["registro"]))
                if junto and rotulo == "pasta comum":
                    resultado = jogar_junto(jogo, plataforma["core"], os.path.join(trabalho, "junto"), sistema)
                    print("   %-17s Jogar Junto: %s %s" % ("", "conectou" if resultado.get("conectou") else
                                                          "NAO conectou", resultado.get("recusa_do_nucleo", "")))
                    if bool(resultado.get("conectou")) != plataforma.get("netplay", True):
                        falhas.append("%s: o consoles.json diz netplay=%s, mas o Jogar Junto %s" % (
                            plataforma["nome"], plataforma.get("netplay", True),
                            "conectou" if resultado.get("conectou") else "nao conectou"))
            finally:
                time.sleep(1)
                limpeza.apagar_pasta(trabalho)
    print("\nFotos: %s" % fotos)
    if falhas:
        print("\nFALHAS:\n  " + "\n  ".join(falhas))
        return 1
    print("\nTudo certo.")
    return 0


if __name__ == "__main__":
    sys.exit(protege_cfg.rodar(main))
