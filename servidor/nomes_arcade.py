# -*- coding: utf-8 -*-
"""
ARENA - o nome de verdade de um jogo de fliperama.

Por que existe (tarefa 7 do Rafael, 01/10/2026): jogo de fliperama vem com
o nome curto do "romset" -- mslugx.zip, kof97.zip, tmnt2.zip. O ARENA
mostrava "Mslugx", "Kof97", "Tmnt2": ninguem reconhece o jogo, e a capa
nunca era achada (o banco de capas usa o nome completo).

O nome completo ja esta na pasta do ARENA: o RetroArch traz os bancos de
dados dele em retroarch\\database\\rdb ("FBNeo - Arcade Games.rdb",
"MAME.rdb"). Cada jogo e' um registro com "name" (o nome completo) e
"rom_name" (o arquivo, ex.: "mslugx.zip"), no formato MessagePack.

Como le, sem carregar o banco inteiro (o do MAME tem 7 MB): procura os
bytes de "rom_name" seguido do nome do arquivo, volta ate o "name" do mesmo
registro e confere que entre os dois so ha campos inteiros desse registro.
Nada e' gravado; o resultado fica na memoria enquanto o ARENA esta aberto.
"""

import os
import re
import struct
import threading

PASTA_SERVIDOR = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(PASTA_SERVIDOR)
PASTA_RDB = os.path.join(RAIZ, "retroarch", "database", "rdb")

# Banco de cada nucleo. O primeiro da lista e' o do emulador do console; o
# segundo serve de reserva (muito jogo de Neo Geo esta nos dois).
BANCOS = {
    "fbneo": ("FBNeo - Arcade Games.rdb", "MAME.rdb"),
    "mame": ("MAME.rdb", "FBNeo - Arcade Games.rdb"),
}

# Conjuntos que o FBNeo DESTA pasta conhece e o banco do RetroArch nao lista
# (o banco veio de outra versao do FBNeo). Sem isto, o cartao chamaria o jogo
# de "Kof2k2fd" e mandaria renomear um arquivo que esta certo. So entra nome
# conferido no proprio nucleo (texto dentro do fbneo_libretro.dll) e aberto
# de verdade. 02/10/2026: o KOF 2002 do professor, que era um zip
# "decriptado para emulador antigo", virou este conjunto
# (ferramentas\converter_fliperama_decriptado.py).
NOMES_FORA_DO_BANCO = {
    "fbneo": {"kof2k2fd.zip": "The King of Fighters 2002 (Fully Decrypted)"},
}

_CHAVE_NOME = b"\xa4name"
_CHAVE_ROM = b"\xa8rom_name"

_cache = {}           # nome do arquivo .rdb -> (marca do arquivo, bytes)
_nomes = {}           # (banco, rom) -> nome ou None
_trava = threading.Lock()


def _empacotar_texto(texto):
    """O texto no formato MessagePack (como o banco guarda)."""
    dados = texto.encode("utf-8")
    n = len(dados)
    if n < 32:
        return bytes([0xa0 | n]) + dados
    if n < 256:
        return b"\xd9" + bytes([n]) + dados
    return b"\xda" + struct.pack(">H", n) + dados


def _pular(dados, i):
    """Posicao logo depois do valor MessagePack que comeca em i (so os tipos
    que aparecem num registro do banco). None se for um tipo desconhecido."""
    b = dados[i]
    if b <= 0x7f or b >= 0xe0 or b in (0xc0, 0xc2, 0xc3):
        return i + 1
    if 0xa0 <= b <= 0xbf:
        return i + 1 + (b & 0x1f)
    tamanhos = {0xcc: 1, 0xcd: 2, 0xce: 4, 0xcf: 8, 0xd0: 1, 0xd1: 2, 0xd2: 4, 0xd3: 8}
    if b in tamanhos:
        return i + 1 + tamanhos[b]
    if b in (0xd9, 0xc4):
        return i + 2 + dados[i + 1]
    if b in (0xda, 0xc5):
        return i + 3 + struct.unpack_from(">H", dados, i + 1)[0]
    if b in (0xdb, 0xc6):
        return i + 5 + struct.unpack_from(">I", dados, i + 1)[0]
    return None


def _ler_texto(dados, i):
    """(texto, posicao depois dele) do texto MessagePack em i, ou (None, i)."""
    b = dados[i]
    if 0xa0 <= b <= 0xbf:
        n, inicio = b & 0x1f, i + 1
    elif b == 0xd9:
        n, inicio = dados[i + 1], i + 2
    elif b == 0xda:
        n, inicio = struct.unpack_from(">H", dados, i + 1)[0], i + 3
    else:
        return None, i
    return dados[inicio:inicio + n].decode("utf-8", "replace"), inicio + n


def _carregar(nome_rdb):
    caminho = os.path.join(PASTA_RDB, nome_rdb)
    try:
        estado = os.stat(caminho)
    except OSError:
        return None
    marca = (estado.st_size, int(estado.st_mtime))
    salvo = _cache.get(nome_rdb)
    if salvo and salvo[0] == marca:
        return salvo[1]
    try:
        with open(caminho, "rb") as arquivo:
            dados = arquivo.read()
    except OSError:
        return None
    if not dados.startswith(b"RARCHDB\x00"):
        return None
    _cache[nome_rdb] = (marca, dados)
    # Banco novo (o RetroArch atualizou): o indice velho nao vale mais.
    _indices.pop(nome_rdb, None)
    _consultas.pop(nome_rdb, None)
    return dados


def _procurar(dados, rom):
    """Nome completo do registro cujo rom_name e' 'rom', ou None.

    Do fim do "name" ate o "rom_name" so pode haver pares chave/valor
    inteiros (outros campos do MESMO registro): se a conta nao fechar, o
    "name" achado era de outro registro (ver _procurar_em)."""
    alvo = _CHAVE_ROM + _empacotar_texto(rom)
    posicao = dados.find(alvo)
    while posicao != -1:
        nome = _procurar_em(dados, posicao, rom)
        if nome:
            return nome
        posicao = dados.find(alvo, posicao + 1)
    return None


_RE_ROM = re.compile(rb"\xa8rom_name([\xa0-\xbf])")
_indices = {}         # nome do .rdb -> {rom: nome}, so para colecao grande
_consultas = {}       # nome do .rdb -> quantas buscas soltas ja fez
LIMITE_SOLTAS = 40    # passou disso, vale ler o banco inteiro de uma vez


def _indexar(dados):
    """{rom: nome} de todos os registros, numa passada so pelo banco.
    Medido em 01/10/2026: 3.000 buscas soltas no banco do MAME custavam
    2,3 s no Ryzen; o indice inteiro sai mais barato que isso."""
    indice = {}
    for m in _RE_ROM.finditer(dados):
        tamanho = m.group(1)[0] & 0x1f
        inicio = m.end()
        rom = dados[inicio:inicio + tamanho].decode("utf-8", "replace")
        if rom not in indice:
            indice[rom] = None
            nome = _procurar_em(dados, m.start(), rom)
            if nome:
                indice[rom] = nome
    return indice


def _procurar_em(dados, posicao, rom):
    """O "name" do registro cujo rom_name comeca em 'posicao' (ou None).
    Registro cortado (banco pela metade) tambem vira None."""
    inicio = dados.rfind(_CHAVE_NOME, max(0, posicao - 4096), posicao)
    if inicio == -1:
        return None
    try:
        nome, i = _ler_texto(dados, inicio + len(_CHAVE_NOME))
        while nome is not None and i is not None and i < posicao:
            i = _pular(dados, i)
            i = _pular(dados, i) if i is not None and i < posicao else None
    except (IndexError, struct.error):
        return None
    return nome if (nome and i == posicao) else None


def nome_do_romset(arquivo, nucleo):
    """Nome completo do jogo de fliperama pelo arquivo (ex.: "mslugx.zip"),
    ou None. 'nucleo': "fbneo" ou "mame" (decide qual banco vem primeiro).
    Banco quebrado ou cortado nunca derruba a lista: vira None."""
    base = os.path.splitext(os.path.basename(arquivo or ""))[0].lower()
    if not base or not re.match(r"^[a-z0-9_]+$", base):
        return None          # romset tem nome curto, sem espaco nem acento
    rom = base + ".zip"      # o banco guarda .zip, mesmo para .7z
    with _trava:
        for nome_rdb in BANCOS.get(nucleo, BANCOS["fbneo"]):
            chave = (nome_rdb, rom)
            if chave not in _nomes:
                try:
                    dados = _carregar(nome_rdb)
                    if not dados:
                        _nomes[chave] = None
                    elif nome_rdb in _indices:
                        _nomes[chave] = _indices[nome_rdb].get(rom)
                    else:
                        _consultas[nome_rdb] = _consultas.get(nome_rdb, 0) + 1
                        if _consultas[nome_rdb] > LIMITE_SOLTAS:
                            _indices[nome_rdb] = _indexar(dados)
                            _nomes[chave] = _indices[nome_rdb].get(rom)
                        else:
                            _nomes[chave] = _procurar(dados, rom)
                except (IndexError, ValueError, struct.error, UnicodeError):
                    _nomes[chave] = None
            if _nomes[chave]:
                return _nomes[chave]
    return NOMES_FORA_DO_BANCO.get(nucleo, {}).get(rom)


def nucleo_de(core):
    """"fbneo" ou "mame" pelo nome do .dll do nucleo; None se nao for
    fliperama."""
    core = (core or "").lower()
    if core.startswith("fbneo") or core.startswith("fbalpha"):
        return "fbneo"
    if core.startswith("mame"):
        return "mame"
    return None


RE_PARENTESES = re.compile(r"\s*[\(\[][^\)\]]*[\)\]]")
_RE_NAO_ALFANUMERICO = re.compile(r"[^a-z0-9]+")
# Copia que nao e' o jogo original: na duvida entre parecidos, fica o original.
_COPIAS = ("bootleg", "hack", "prototype", "demo", "alt", "set 2", "set 3")


def _normalizar(nome):
    """'The King of Fighters 2002 (NGM-2650)' -> 'thekingoffighters2002'."""
    return _RE_NAO_ALFANUMERICO.sub("", titulo_para_a_tela(nome or "").lower())


def _palavras(nome):
    """'Metal Slug X - Super Vehicle-001' -> ['metal', 'slug', 'x', 'super', ...]."""
    return re.findall(r"[a-z0-9]+", titulo_para_a_tela(nome or "").lower())


def romset_pelo_titulo(titulo, nucleo):
    """(nome curto do romset, exato) pelo TITULO do jogo -- ("kof2002", True)
    --, ou (None, False).

    Achado de 02/10/2026 (tarefa 7, "o fliperama nao e' reconhecido"): o
    jogo chega com o nome do titulo ("The King Of Fighters 2002.zip"), e o
    MAME e o FBNeo so reconhecem o nome curto do romset (kof2002.zip). O
    titulo e' procurado nos mesmos bancos do RetroArch:
      - so registros de romset (.zip): o banco do MAME tambem lista arquivos
        soltos de dentro dos romsets ("256.p2", "201-c4.c4");
      - vale o titulo igual e tambem o titulo do banco que COMECA com as
        mesmas palavras ("Metal Slug X" -> "Metal Slug X - Super
        Vehicle-001"), este como palpite ('exato' False);
      - entre os parecidos, fica o original: sem "bootleg"/"hack" no nome,
        o igual antes do palpite, e o nome curto mais curto.
    Uma busca so no banco, sem guardar indice: a primeira versao guardava os
    37 mil titulos do MAME e custava 13 MB ao servidor -- o orcamento de
    memoria do notebook-alvo estourou no modo alvo (02/10/2026)."""
    palavras = _palavras(titulo)
    alvo = "".join(palavras)
    if not alvo:
        return None, False
    # O inicio do "name" no banco com as mesmas palavras, sem diferenciar
    # maiuscula; entre as palavras, qualquer pontuacao ou espaco.
    padrao = re.compile(rb"\xa4name(?:[\xa0-\xbf]|\xd9.)" + rb"[^a-z0-9]*".join(
        re.escape(p.encode("utf-8")) for p in palavras) + rb"(?![a-z0-9])", re.I | re.S)
    with _trava:
        for nome_rdb in BANCOS.get(nucleo, BANCOS["fbneo"]):
            try:
                dados = _carregar(nome_rdb)
                if not dados:
                    continue
                candidatos = []
                for achado in padrao.finditer(dados):
                    nome, fim_nome = _ler_texto(dados, achado.start() + len(_CHAVE_NOME))
                    if not nome:
                        continue
                    posicao = dados.find(_CHAVE_ROM, fim_nome, fim_nome + 4096)
                    if posicao == -1:
                        continue
                    rom, _depois = _ler_texto(dados, posicao + len(_CHAVE_ROM))
                    # O rom_name tem de ser do MESMO registro (a mesma conta
                    # da busca pelo romset, de tras para frente).
                    if not rom or not rom.lower().endswith(".zip") or _procurar_em(dados, posicao, rom) != nome:
                        continue
                    candidatos.append((rom, nome, _normalizar(nome) == alvo))
            except (IndexError, ValueError, struct.error, UnicodeError):
                continue
            if candidatos:
                candidatos.sort(key=lambda c: (any(x in c[1].lower() for x in _COPIAS), not c[2],
                                               len(c[0]), c[0]))
                rom, _nome, exato = candidatos[0]
                return os.path.splitext(rom)[0], exato
    return None, False


def liberar():
    """Solta os bancos da memoria (7,8 MB) e os indices; fica so o que ja
    foi respondido. A lista de jogos chama no fim de cada montagem: o banco
    so e' preciso enquanto ela procura os nomes (orcamento de memoria do
    notebook-alvo, 02/10/2026). Na proxima montagem, le de novo do disco."""
    with _trava:
        _cache.clear()
        _indices.clear()
        _consultas.clear()


def titulo_para_a_tela(nome):
    """"Metal Slug X - Super Vehicle-001 (NGM-2500)" -> sem o codigo da
    placa entre parenteses (o nome completo fica guardado para a capa)."""
    limpo = RE_PARENTESES.sub("", nome or "").strip(" -")
    return limpo or (nome or "").strip()
