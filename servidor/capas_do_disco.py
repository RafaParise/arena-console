# -*- coding: utf-8 -*-
r"""O que da para tirar de DENTRO do arquivo do jogo para achar a capa.

Pedido do Rafael (02/10/2026): capa para os consoles que ainda nao tinham.
O banco de capas do RetroArch (capas_online.py) e' otimo para quase tudo,
mas quase nao tem PS3 (67 capas) nem Xbox 360 (12). O proprio disco ajuda:

  - PS3 e PSP: o disco traz o icone do jogo, PS3_GAME\ICON0.PNG (ou
    PSP_GAME\ICON0.PNG). Sai de dentro do .iso -- sem internet nenhuma.
  - Xbox 360: saiu em 22/10/2026 (achado F4 da auditoria 4). O servidor
    de imagens da Microsoft so responde sem criptografia (http), e a
    capa podia ser trocada no caminho da rede.
  - GameCube e Wii: os 6 primeiros caracteres do disco sao o codigo do jogo
    (Mario Kart Wii = RMCE01). Com ele, a capa vem do GameTDB -- o mesmo
    lugar de onde o proprio Dolphin baixa as capas dele.

So leitura: nada no arquivo do jogo e' mudado.
"""
import os
import re
import struct

SETOR = 2048
LIMITE_ICONE = 2 * 1024 * 1024        # icone de disco nunca passa disso
ASSINATURA_PNG = b"\x89PNG\r\n\x1a\n"


# ---------------------------------------------------------------------------
# ISO 9660 (PS3 e PSP): achar um arquivo numa pasta do disco
# ---------------------------------------------------------------------------

def _registros(dados):
    """Os registros de um diretorio ISO 9660: (nome, setor, tamanho, pasta?)."""
    posicao = 0
    while posicao < len(dados):
        comprimento = dados[posicao]
        if comprimento == 0:
            posicao = ((posicao // SETOR) + 1) * SETOR    # fim deste setor
            continue
        registro = dados[posicao:posicao + comprimento]
        if len(registro) < 34:
            break
        nome = registro[33:33 + registro[32]].split(b";")[0].decode("ascii", "ignore").upper()
        yield (nome, struct.unpack("<I", registro[2:6])[0], struct.unpack("<I", registro[10:14])[0],
               bool(registro[25] & 0x02))
        posicao += comprimento


def arquivo_no_iso(caminho, partes, limite=LIMITE_ICONE):
    """O conteudo de partes[-1], dentro das pastas partes[:-1] do ISO 9660
    (ex.: ["PS3_GAME", "ICON0.PNG"]). None se nao achar."""
    try:
        with open(caminho, "rb") as arquivo:
            arquivo.seek(16 * SETOR)
            descritor = arquivo.read(SETOR)
            if len(descritor) < 190 or descritor[1:6] != b"CD001":
                return None
            raiz = descritor[156:190]
            setor, tamanho = struct.unpack("<I", raiz[2:6])[0], struct.unpack("<I", raiz[10:14])[0]
            for indice, parte in enumerate(partes):
                if not tamanho or tamanho > 8 * 1024 * 1024:
                    return None
                arquivo.seek(setor * SETOR)
                achado = next((r for r in _registros(arquivo.read(tamanho)) if r[0] == parte.upper()), None)
                if not achado:
                    return None
                _nome, setor, tamanho, pasta = achado
                ultima = indice == len(partes) - 1
                if ultima:
                    if pasta or not 0 < tamanho <= limite:
                        return None
                    arquivo.seek(setor * SETOR)
                    return arquivo.read(tamanho)
                if not pasta:
                    return None
    except OSError:
        return None
    return None


def icone_do_disco(caminho, plataforma):
    """O ICON0.PNG do disco de PS3 ou PSP (bytes do PNG), ou None."""
    pasta = {"ps3": "PS3_GAME", "psp": "PSP_GAME"}.get(plataforma)
    if not pasta or not str(caminho).lower().endswith(".iso"):
        return None
    dados = arquivo_no_iso(caminho, [pasta, "ICON0.PNG"])
    return dados if dados and dados.startswith(ASSINATURA_PNG) else None


# ---------------------------------------------------------------------------
# GameCube e Wii: o codigo de 6 letras do disco
# ---------------------------------------------------------------------------

def id_do_disco_nintendo(caminho):
    """O codigo do jogo de GameCube/Wii (ex.: "RMCE01"), ou None.

    .iso/.gcm: os 6 primeiros bytes. .rvz/.wia: o formato guarda uma copia do
    comeco do disco 0x58 bytes depois do inicio (docs/WiaAndRvz.md do
    Dolphin). .wbfs: a copia fica no setor seguinte ao cabecalho (0x200)."""
    extensao = os.path.splitext(str(caminho))[1].lower()
    onde = {".iso": 0, ".gcm": 0, ".rvz": 0x58, ".wia": 0x58, ".wbfs": 0x200}.get(extensao)
    if onde is None:
        return None
    try:
        with open(caminho, "rb") as arquivo:
            arquivo.seek(onde)
            codigo = arquivo.read(6).decode("ascii")
    except (OSError, UnicodeDecodeError):
        return None
    return codigo if re.fullmatch(r"[A-Z0-9]{6}", codigo) else None


def urls_capa_nintendo(codigo):
    """As capas do GameTDB para o codigo, na regiao do disco primeiro (a
    letra 4: E = EUA, J = Japao, K = Coreia; o resto, Europa)."""
    regiao = {"E": "US", "J": "JA", "K": "KO"}.get(codigo[3], "EN")
    regioes = [regiao] + [r for r in ("US", "EN") if r != regiao]
    return ["https://art.gametdb.com/wii/cover/%s/%s.png" % (r, codigo) for r in regioes]
