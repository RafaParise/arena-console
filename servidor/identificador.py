# -*- coding: utf-8 -*-
"""
ARENA - Identificar o console pelo conteudo do arquivo
=======================================================
Quando a extensao serve a varios consoles, adivinhar pelo tamanho nao
resolve: o PlayStation 2 tambem lancou jogos em CD, entao um .iso de 700 MB
pode ser PS1 ou PS2. O jeito certo e abrir o arquivo e olhar.

E barato. Um disco de PlayStation guarda a receita de como iniciar num
arquivinho chamado SYSTEM.CNF, sempre no diretorio raiz:

    PS1:  BOOT  = cdrom:\\SLUS_007.77;1
    PS2:  BOOT2 = cdrom0:\\SLUS_204.88;1

Ler isso custa quatro leituras de 2 KB. Nao importa se o jogo tem 700 MB
ou 8 GB - o ARENA le so o comecinho.

Para GameCube e Wii existe assinatura fixa no cabecalho, mais simples ainda.

So biblioteca padrao.
"""

import os
import struct

SETOR = 2048
LIMITE_BUSCA = 8 * 1024 * 1024      # ate onde varrer no plano B


# ---------------------------------------------------------------------------
# ISO 9660: achar um arquivo no diretorio raiz
# ---------------------------------------------------------------------------

def _descritor_primario(arquivo):
    """Le o descritor de volume do ISO 9660 (setor 16) e confere a marca."""
    arquivo.seek(16 * SETOR)
    bloco = arquivo.read(SETOR)
    if len(bloco) < 190 or bloco[1:6] != b"CD001":
        return None
    return bloco


def _raiz(descritor):
    """Posicao e tamanho do diretorio raiz, do registro do descritor."""
    registro = descritor[156:190]
    setor = struct.unpack("<I", registro[2:6])[0]
    tamanho = struct.unpack("<I", registro[10:14])[0]
    return setor, tamanho


def _procurar_no_raiz(arquivo, descritor, nomes):
    """Procura arquivos ou pastas pelo nome dentro do diretorio raiz.

    Devolve {nome maiusculo: (setor, tamanho)}.
    """
    setor, tamanho = _raiz(descritor)
    if not tamanho or tamanho > 4 * 1024 * 1024:
        return {}

    arquivo.seek(setor * SETOR)
    dados = arquivo.read(min(tamanho, 512 * 1024))

    procurados = {n.upper() for n in nomes}
    achados = {}
    posicao = 0

    while posicao < len(dados):
        comprimento = dados[posicao]
        if comprimento == 0:
            # Fim dos registros deste setor: pula para o proximo.
            posicao = ((posicao // SETOR) + 1) * SETOR
            if posicao >= len(dados):
                break
            continue
        registro = dados[posicao:posicao + comprimento]
        if len(registro) < 33:
            break
        tamanho_nome = registro[32]
        nome = registro[33:33 + tamanho_nome].split(b";")[0]
        try:
            nome = nome.decode("ascii", "ignore").upper().strip()
        except Exception:
            nome = ""
        if nome in procurados:
            achados[nome] = (struct.unpack("<I", registro[2:6])[0],
                             struct.unpack("<I", registro[10:14])[0])
        posicao += comprimento

    return achados


# ---------------------------------------------------------------------------
# Regras por console
# ---------------------------------------------------------------------------

def _por_system_cnf(arquivo, descritor):
    """PS1 x PS2: quem manda e a linha de boot do SYSTEM.CNF."""
    achados = _procurar_no_raiz(arquivo, descritor, ["SYSTEM.CNF"])
    if "SYSTEM.CNF" not in achados:
        return None

    setor, tamanho = achados["SYSTEM.CNF"]
    if not tamanho or tamanho > 64 * 1024:
        return None

    arquivo.seek(setor * SETOR)
    texto = arquivo.read(min(tamanho, 8192)).upper()

    if b"BOOT2" in texto:
        return "ps2"
    if b"BOOT" in texto:
        return "ps1"
    return None


def _por_pasta(arquivo, descritor):
    """PSP e 3DO se entregam por uma pasta caracteristica no raiz."""
    achados = _procurar_no_raiz(
        arquivo, descritor, ["PSP_GAME", "UMD_DATA.BIN", "LAUNCHME"])
    if "PSP_GAME" in achados or "UMD_DATA.BIN" in achados:
        return "psp"
    if "LAUNCHME" in achados:
        return "threedo"
    return None


def _por_assinatura(arquivo):
    """GameCube e Wii tem numero magico fixo no cabecalho."""
    arquivo.seek(0x18)
    wii = arquivo.read(4)
    if wii == b"\x5d\x1c\x9e\xa3":
        return "gamecube"
    arquivo.seek(0x1C)
    gc = arquivo.read(4)
    if gc == b"\xc2\x33\x9f\x3d":
        return "gamecube"
    return None


def _busca_bruta(arquivo, tamanho_arquivo):
    """Plano B: varrer o comeco do arquivo atras da linha de boot.

    Usado quando o ISO nao segue o padrao a risca, o que acontece em copia
    feita com programa antigo. Le em pedacos de 1 MB, ate 8 MB, e para no
    primeiro achado.
    """
    arquivo.seek(0)
    lido = 0
    sobra = b""
    while lido < min(tamanho_arquivo, LIMITE_BUSCA):
        pedaco = arquivo.read(1024 * 1024)
        if not pedaco:
            break
        janela = (sobra + pedaco).upper()
        if b"BOOT2" in janela:
            return "ps2"
        if b"UMD_DATA.BIN" in janela or b"PSP_GAME" in janela:
            return "psp"
        # 'BOOT' sozinho e fraco demais: so vale se vier na cara do CNF.
        if b"BOOT = CDROM" in janela or b"BOOT=CDROM" in janela:
            return "ps1"
        sobra = janela[-32:]
        lido += len(pedaco)
    return None


# ---------------------------------------------------------------------------
# CHD: descobrir se e disco de CD ou de DVD sem descompactar nada
# ---------------------------------------------------------------------------
# O CHD e compactado, entao nao da para abrir e ler o SYSTEM.CNF de dentro.
# Mas o proprio cabecalho ja entrega o formato do disco, e isso resolve a
# maior parte dos enganos:
#
#   CD  -> trilhas 'CHT2'/'CHTR', unidade de 2448 bytes, compressor 'cdlz'
#          PlayStation 1, Sega CD, Saturn, Dreamcast, PC-FX, CD-i, 3DO
#   DVD -> marca 'DVD', unidade de 2048 bytes
#          PlayStation 2, PSP, GameCube
#
# Um CD nao passa de 700 MB. Entao um CHD de disco de CD nunca e PS2.

CD = "cd"
DVD = "dvd"


def formato_do_chd(caminho):
    """Le o cabecalho do CHD e diz se o disco original era CD ou DVD.

    Devolve (formato, tamanho original em MB) ou (None, None).
    """
    try:
        with open(caminho, "rb") as arquivo:
            cabecalho = arquivo.read(124)
            if len(cabecalho) < 124 or cabecalho[:8] != b"MComprHD":
                return None, None

            versao = struct.unpack(">I", cabecalho[12:16])[0]
            if versao != 5:
                return None, None

            compressores = [cabecalho[16 + i * 4:20 + i * 4] for i in range(4)]
            logico = struct.unpack(">Q", cabecalho[32:40])[0]
            meta = struct.unpack(">Q", cabecalho[48:56])[0]
            unidade = struct.unpack(">I", cabecalho[60:64])[0]
            megabytes = logico / (1024.0 * 1024.0)

            # Compressor proprio de CD ja e resposta.
            if any(c in (b"cdlz", b"cdzl", b"cdfl") for c in compressores):
                return CD, megabytes

            # Senao, percorre a lista de metadados atras da marca do formato.
            posicao, voltas = meta, 0
            while posicao and voltas < 40:
                arquivo.seek(posicao)
                entrada = arquivo.read(16)
                if len(entrada) < 16:
                    break
                marca = entrada[0:4]
                if marca in (b"CHT2", b"CHTR", b"CHCD"):
                    return CD, megabytes
                if marca == b"DVD ":
                    return DVD, megabytes
                posicao = struct.unpack(">Q", entrada[8:16])[0]
                voltas += 1

            # Ultimo recurso: o tamanho da unidade. CD guarda 2448 bytes por
            # setor (2048 de dados mais correcao de erro); DVD guarda 2048.
            if unidade == 2448:
                return CD, megabytes
            if unidade == 2048:
                return DVD, megabytes
    except (OSError, struct.error):
        pass
    return None, None


def _por_chd(caminho, candidatos):
    """Escolhe a plataforma de um CHD pelo formato do disco original."""
    formato, megabytes = formato_do_chd(caminho)
    if not formato:
        return None

    DE_CD = ["ps1", "segacd", "saturn", "dreamcast", "pcfx", "cdi", "threedo"]
    DE_DVD = ["ps2", "psp", "gamecube"]

    permitidos = [c for c in (DE_CD if formato == CD else DE_DVD)
                  if c in candidatos]
    if not permitidos:
        return None
    if len(permitidos) == 1:
        return permitidos[0]

    # Sobrando mais de um, o tamanho do disco original ajuda: UMD de PSP
    # para em 1,8 GB, DVD de PlayStation 2 vai ate 8,5 GB.
    if formato == DVD and megabytes and megabytes > 1900 and "ps2" in permitidos:
        return "ps2"

    return permitidos[0]


# ---------------------------------------------------------------------------
# Porta de entrada
# ---------------------------------------------------------------------------

def identificar(caminho, candidatos):
    """Diz de qual console e o arquivo, olhando dentro dele.

    Devolve o id da plataforma, ou None quando nao deu para afirmar.
    So responde algo que esteja entre os candidatos: se a extensao nem
    serve para PS2, nao adianta o arquivo parecer PS2.
    """
    if not candidatos:
        return None

    try:
        tamanho = os.path.getsize(caminho)
    except OSError:
        return None

    # Arquivo pequeno demais para ser um disco: nem tenta.
    if tamanho < 64 * 1024:
        return None

    # CHD e compactado: nao da para abrir por dentro, mas o cabecalho
    # entrega o formato do disco, o que ja resolve quase tudo.
    if caminho.lower().endswith(".chd"):
        return _por_chd(caminho, candidatos)

    try:
        with open(caminho, "rb") as arquivo:
            assinatura = _por_assinatura(arquivo)
            if assinatura in candidatos:
                return assinatura

            descritor = _descritor_primario(arquivo)
            if descritor:
                for regra in (_por_system_cnf, _por_pasta):
                    achado = regra(arquivo, descritor)
                    if achado in candidatos:
                        return achado

            achado = _busca_bruta(arquivo, tamanho)
            if achado in candidatos:
                return achado
    except OSError:
        return None

    return None
