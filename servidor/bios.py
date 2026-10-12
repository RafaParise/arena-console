# -*- coding: utf-8 -*-
r"""
ARENA - as BIOS dos consoles: onde ficam, qual e' a versao certa e como o
ARENA as poe no lugar sozinho.

Por que existe (Rafael, 03/10/2026): "garanta que o ARENA saiba explicar de
forma simples de entender como configurar a BIOS ou o jogo"; "faca o ARENA
criar pastas de todas as BIOS necessarias para ler e organizar"; "A parte de
emuladores do ARENA deve conversar com essas pastas e subpastas onde as bios
vao residir, e quando posicionada corretamente deve constar ativa assim como
e' feito nos emuladores como pcsx2".

Dois lugares, duas funcoes:
  - BIOS\<console>\<regiao>: a PRATELEIRA, para gente. Uma pasta por console
    (o mesmo nome da pasta de jogos dele), com um LEIA.txt dizendo o que vai
    ali e se ja esta ativa; na raiz, "LEIA - O QUE FALTA.txt" conta tudo. O
    arquivo pode ir com qualquer nome, ou no .zip em que veio. O que vai em
    cada prateleira: servidor\bios_catalogo.py.
  - retroarch\system: onde o EMULADOR procura, a BIOS solta e com o nome
    exato (bios_CD_E.bin, dc\dc_boot.bin...). Ninguem precisa mexer aqui.

organizar() liga os dois -- ao abrir o ARENA (em segundo plano) e no botao
Conferir (Ajustes -> Emuladores):
  1. cria as prateleiras que faltam;
  2. reconhece cada arquivo das prateleiras, dos pacotes .zip deixados em
     retroarch\system e das BIOS deixadas junto dos jogos: pela MARCA (MD5)
     das notas dos .info do proprio RetroArch, pelo CONTEUDO no PlayStation
     1 e 2 (a regiao vem gravada dentro) e no neogeo.zip, pelo NOME exato
     quando o ARENA nao conhece marca nenhuma, ou -- so na prateleira certa
     -- pelo tamanho (fica como "outra versao");
  3. instala, com o nome certo, o que falta em retroarch\system (e o
     neogeo.zip tambem na pasta do Arcade, onde o MAME procura). Nunca troca
     uma BIOS que ja esta la, a nao ser a de outra versao pela recomendada
     -- e a antiga vai para backup\bios-trocadas;
  4. copia para a prateleira a BIOS que ja estava instalada (uma vez so:
     quem apaga da prateleira nao ve ela voltar), para a pasta BIOS mostrar
     tudo o que existe;
  5. reescreve os LEIA (so quando muda alguma coisa).
Nunca apaga nada. Cada arquivo e' lido uma vez; a marca fica guardada em
dados\bios_conferidas.json ate o arquivo mudar.
"""
import hashlib
import io
import json
import os
import re
import shutil
import threading
import time
import zipfile

import bios_catalogo as catalogo

PASTA_SERVIDOR = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(PASTA_SERVIDOR)
PASTA_INFO = os.path.join(RAIZ, "retroarch", "info")
NOME_DA_PASTA = "BIOS"
ARQUIVO_LEIA = "LEIA.txt"
ARQUIVO_RESUMO = "LEIA - O QUE FALTA.txt"
ARQUIVO_CONFERIDOS = "bios_conferidas.json"

# Marcas que a documentacao do libretro da e os .info desta pasta nao trazem.
# Conferidas no pacote do Rafael em 03/10/2026: as duas versoes americanas do
# Sega CD (Model 1 v1.10, a do .info do PicoDrive, e Model 2 v2.00w, a da
# documentacao do Genesis Plus GX) estavam la, cada uma com a sua marca.
MARCAS_A_MAIS = {"bios_cd_u.bin": ["854b9150240a198070150e4566ae1290"]}
# Versoes que NAO sao a recomendada, mas foram testadas aqui abrindo jogo de
# verdade: aparecem como ativas, com o que sao.
TESTADAS = {
    # O BS-X que o Rafael trouxe (03/10/2026): "BS-X BIOS (English) [No DRM]
    # [2016 v1.3].sfc". Com ele, os BS F-ZERO ligam pela tela do BS-X
    # (testes\teste_bios_consoles.py); sem ele, "BSX ROM loading failed".
    "96cf17bf589fcbfa6f8de2dc84f19fa2": {"id": "snes-bsx",
                                         "texto": "a tradução em inglês do BS-X, testada: os jogos BS ligam por ela"},
}

# BIOS que dependem da REGIAO do jogo (o emulador escolhe pela regiao do
# disco; o ARENA, pelo nome do arquivo: "Sonic CD (Europe).chd").
POR_REGIAO = {
    "segacd": {"europa": "bios_CD_E.bin", "eua": "bios_CD_U.bin", "japao": "bios_CD_J.bin"},
    "saturn": {"europa": "mpr-17933.bin", "eua": "mpr-17933.bin", "japao": "sega_101.bin"},
}
LISTA_POR_REGIAO = {
    "segacd": "bios_CD_U.bin (EUA), bios_CD_E.bin (Europa) ou bios_CD_J.bin (Japão)",
    "saturn": "mpr-17933.bin (EUA e Europa) ou sega_101.bin (Japão)",
}
NOME_DA_REGIAO = {"europa": "da Europa", "eua": "dos EUA", "japao": "do Japão"}
_REGIOES = (
    ("europa", re.compile(r"^(europe|e|eu|uk|germany|france|spain|italy|brazil|br|pal)$")),
    ("eua", re.compile(r"^(usa|u|us|america|canada)$")),
    ("japao", re.compile(r"^(japan|j|jp|jpn|asia|korea|taiwan)$")),
)
# Os consoles que NAO abrem jogo nenhum sem a BIOS (o emulador recusa:
# "Unable to open CD BIOS", "Cannot open BIOS file" -- visto em 03/10/2026).
SEM_ELA_NAO_ABRE = ("segacd", "saturn")
# Pacote maior que isso nao e' de BIOS (o ni-n-sat.zip do Rafael, de 128 MB,
# era a colecao de 321 jogos do Satellaview).
PACOTE_MAXIMO = 64 * 1024 * 1024
BIOS_MAXIMA = 16 * 1024 * 1024
# A pasta BIOS nao e' lugar de colecao: passou disso, para de procurar.
LIMITE_DE_ARQUIVOS = 3000
_NAO_E_BIOS = (".xml", ".jpg", ".jpeg", ".png", ".gif", ".torrent", ".sqlite", ".txt", ".nfo", ".html",
               ".htm", ".md", ".pdf", ".svg", ".dat", ".url", ".ini", ".cfg", ".db")
# Na pasta de JOGOS so se olha arquivo com tamanho de BIOS daquele console e
# com estas extensoes (e so se aceita pela marca ou pelo conteudo: um jogo de
# Super Nintendo tem o mesmo tamanho do BS-X).
_EXTENSOES_NOS_JOGOS = (".bin", ".rom", ".img", ".bios", ".pce", ".min", ".zip", ".a500", ".a1200",
                        ".cd32", ".ext", ".n64")
# Quando a extensao tambem e' de jogo daquele console e o arquivo nao e'
# pequeno (cartao de PC Engine de 256 KB, cartucho de N64 de 4 MB), so le se
# o NOME parecer de BIOS: ler cada jogo a cada abertura pesaria no Celeron.
_RE_NOME_DE_BIOS = re.compile(r"bios|syscard|system ?card|ipl|64dd|scph|kick|boot|firmware|disksys", re.I)
_PEQUENO = 64 * 1024
# A regiao que o PCSX2 mostra, na ordem de preferencia para o padrao dele.
_ORDEM_PS2 = {"A": 0, "E": 1, "J": 2}

_trava = threading.Lock()
_trava_organizar = threading.Lock()
_cache_marcas = {}       # pasta dos .info -> {nome em minusculas: [md5, ...]}
_cache_reverso = {}      # pasta dos .info -> {md5: {nome em minusculas}}
_cache_md5 = {}          # (caminho, tamanho, data) -> md5
_cache_ps = {}           # (caminho, tamanho, data) -> ("ps1"|"ps2", regiao, versao) ou None
_cache_consoles = {}

ID_DO_PLAYSTATION = {(e["pelo_conteudo"], e["regiao"]): e["id"]
                     for e in catalogo.CATALOGO if e.get("pelo_conteudo") in ("ps1", "ps2")}


# ---------------------------------------------------------------------------
# Marcas (MD5) e leitura
# ---------------------------------------------------------------------------

def _md5(dados):
    return hashlib.md5(dados).hexdigest()


def _ler(caminho):
    with open(caminho, "rb") as arquivo:
        return arquivo.read()


def marcas_dos_info(pasta_info=None):
    """{nome do arquivo em minusculas: [md5, ...]} de todas as notas dos .info
    da pasta (e as MARCAS_A_MAIS no fim). Lido uma vez por pasta."""
    pasta_info = pasta_info or PASTA_INFO
    with _trava:
        if pasta_info in _cache_marcas:
            return _cache_marcas[pasta_info]
    marcas = {}
    try:
        nomes = sorted(os.listdir(pasta_info))
    except OSError:
        nomes = []
    for nome in nomes:
        if not nome.lower().endswith(".info"):
            continue
        try:
            with open(os.path.join(pasta_info, nome), encoding="utf-8", errors="replace") as arquivo:
                texto = arquivo.read()
        except OSError:
            continue
        notas = re.search(r'^notes\s*=\s*"(.*)"', texto, re.M)
        for arquivo, marca in re.findall(r"\(!\)\s*([^|(]+?)\s*\(md5\):\s*([0-9a-fA-F]{32})",
                                         notas.group(1) if notas else ""):
            lista = marcas.setdefault(os.path.basename(arquivo.strip()).lower(), [])
            if marca.lower() not in lista:
                lista.append(marca.lower())
    for arquivo, extras in MARCAS_A_MAIS.items():
        lista = marcas.setdefault(arquivo, [])
        lista.extend(m for m in extras if m not in lista)
    with _trava:
        _cache_marcas[pasta_info] = marcas
    return marcas


def _reverso(pasta_info=None):
    """{md5: {nomes}}: de que BIOS e' uma marca."""
    pasta_info = pasta_info or PASTA_INFO
    with _trava:
        if pasta_info in _cache_reverso:
            return _cache_reverso[pasta_info]
    reverso = {}
    for nome, marcas in marcas_dos_info(pasta_info).items():
        for marca in marcas:
            reverso.setdefault(marca, set()).add(nome)
    with _trava:
        _cache_reverso[pasta_info] = reverso
    return reverso


def marcas_aceitas(relativo, pasta_info=None):
    """As marcas da versao certa de uma BIOS ("dc/dc_boot.bin"), da mais
    recomendada para a menos; [] se o ARENA nao conhece nenhuma."""
    return list(marcas_dos_info(pasta_info).get(os.path.basename(relativo).lower(), []))


def _marcas_da_entrada(entrada, pasta_info=None):
    marcas = []
    for nome in catalogo.nomes_aceitos(entrada):
        marcas += [m for m in marcas_dos_info(pasta_info).get(nome, []) if m not in marcas]
    return marcas


def _chave(caminho):
    try:
        info = os.stat(caminho)
    except OSError:
        return None
    return (caminho, info.st_size, info.st_mtime_ns)


def md5_do_arquivo(caminho):
    """Marca do arquivo, guardada enquanto ele nao muda (BIOS e' pequena)."""
    chave = _chave(caminho)
    if not chave or chave[1] > BIOS_MAXIMA:
        return None
    with _trava:
        if chave in _cache_md5:
            return _cache_md5[chave]
    try:
        marca = _md5(_ler(caminho))
    except OSError:
        return None
    with _trava:
        _cache_md5[chave] = marca
    return marca


def _playstation_dos_bytes(dados):
    regiao = catalogo.regiao_ps1(dados)
    if regiao:
        return ("ps1", regiao, catalogo.versao_ps1(dados))
    regiao = catalogo.regiao_ps2(dados)
    if regiao:
        return ("ps2", regiao, catalogo.versao_ps2(dados))
    return None


def playstation(caminho):
    """("ps1"|"ps2", regiao A/E/J, versao) se o arquivo e' BIOS de PlayStation."""
    chave = _chave(caminho)
    if not chave or chave[1] not in (524288, 4194304):
        return None
    with _trava:
        if chave in _cache_ps:
            return _cache_ps[chave]
    try:
        dados = _ler(caminho)
    except OSError:
        return None
    resultado = _playstation_dos_bytes(dados)
    with _trava:
        _cache_ps[chave] = resultado
        _cache_md5[chave] = _md5(dados)
    return resultado


# ---------------------------------------------------------------------------
# Onde as coisas ficam
# ---------------------------------------------------------------------------

def caminhos(raiz=None):
    raiz = raiz or RAIZ
    info = os.path.join(raiz, "retroarch", "info")
    return {"raiz": raiz, "bios": os.path.join(raiz, NOME_DA_PASTA),
            "sistema": os.path.join(raiz, "retroarch", "system"),
            "dados": os.path.join(raiz, "dados"),
            "jogos": os.path.join(raiz, "jogos", "pessoais"),
            "info": info if os.path.isdir(info) else PASTA_INFO}


def prateleira(raiz, entrada):
    """A pasta onde a BIOS fica na prateleira (BIOS\\Sega CD\\Europa)."""
    partes = [raiz, NOME_DA_PASTA, entrada["pasta"]]
    if entrada.get("sub"):
        partes.append(entrada["sub"])
    return os.path.join(*partes)


def prateleira_relativa(entrada):
    return "\\".join([NOME_DA_PASTA, entrada["pasta"]] + ([entrada["sub"]] if entrada.get("sub") else []))


def consoles():
    """{id: {"nome", "pasta"}} do consoles.json (o mesmo do indexador)."""
    with _trava:
        if "lista" in _cache_consoles:
            return _cache_consoles["lista"]
    try:
        with open(os.path.join(PASTA_SERVIDOR, "consoles.json"), encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
        lista = dados["plataformas"] if isinstance(dados, dict) else dados
        saida = {p["id"]: {"nome": p.get("nome", p["id"]), "pasta": p.get("pasta", p["id"]),
                           "extensoes": [e.lower() for e in p.get("extensoes", [])]} for p in lista}
    except (OSError, ValueError, KeyError, TypeError):
        saida = {}
    with _trava:
        _cache_consoles["lista"] = saida
    return saida


def _achar(pasta_sistema, relativo):
    """O caminho do arquivo de BIOS em retroarch\\system (sem diferenca de
    maiuscula e minuscula, como o Windows), ou None."""
    caminho = os.path.join(pasta_sistema, *relativo.split("/"))
    if os.path.isfile(caminho):
        return caminho
    pasta, nome = os.path.split(caminho)
    try:
        for existente in os.listdir(pasta):
            if existente.lower() == nome.lower() and os.path.isfile(os.path.join(pasta, existente)):
                return os.path.join(pasta, existente)
    except OSError:
        pass
    return None


def tem(pasta_sistema, relativo):
    return _achar(pasta_sistema, relativo) is not None


def _instalada(pasta_sistema, entrada):
    """O caminho da BIOS instalada (com o nome certo ou um aceito), ou None."""
    destino = entrada.get("destino") or ""
    pasta = os.path.dirname(destino)
    for nome in [catalogo.nome_de_instalacao(entrada)] + list(entrada.get("alternativas", [])):
        caminho = _achar(pasta_sistema, (pasta + "/" + nome) if pasta else nome)
        if caminho:
            return caminho
    return None


def _pasta_do_pcsx2(raiz):
    """A pasta bios\\ ao lado do pcsx2-qt.exe (emuladores\\PCSX2\\PCSX2\\bios), ou None."""
    base = os.path.join(raiz, "emuladores", "PCSX2")
    for atual, subpastas, arquivos in os.walk(base):
        if os.path.relpath(atual, base).count(os.sep) >= 1:
            subpastas[:] = []
        if any(a.lower().startswith("pcsx2") and a.lower().endswith(".exe") for a in arquivos):
            return os.path.join(atual, "bios")
    return None


def _bios_de_ps(raiz, tipo):
    """[(caminho, regiao, versao)] das BIOS de PlayStation instaladas: em
    retroarch\\system (e, no PS2, na pasta do PCSX2), em ordem de nome."""
    pastas = [caminhos(raiz)["sistema"]]
    if tipo == "ps2":
        pcsx2 = _pasta_do_pcsx2(raiz)
        if pcsx2:
            pastas.append(pcsx2)
    achadas = []
    for pasta in pastas:
        try:
            nomes = sorted(os.listdir(pasta), key=str.lower)
        except OSError:
            continue
        for nome in nomes:
            caminho = os.path.join(pasta, nome)
            if not os.path.isfile(caminho):
                continue
            achado = playstation(caminho)
            if achado and achado[0] == tipo:
                achadas.append((caminho, achado[1], achado[2]))
    return achadas


def bios_em_uso_no_pcsx2(raiz=None):
    """O arquivo com que o PCSX2 liga: o escolhido na tela dele ([Filenames]
    BIOS do PCSX2.ini) ou, sem escolha, o primeiro da pasta bios\\ dele em
    ordem de nome (o registro dele confirma: "Searching for a BIOS image...
    Using BIOS 'PS2 Bios 30004R V6 Pal.bin'"). None se nao tem nenhum."""
    pasta = _pasta_do_pcsx2(raiz or RAIZ)
    if not pasta:
        return None
    escolhida = ""
    try:
        with open(os.path.join(os.path.dirname(pasta), "inis", "PCSX2.ini"), encoding="utf-8",
                  errors="replace") as arquivo:
            secao = ""
            for linha in arquivo:
                linha = linha.strip()
                if linha.startswith("["):
                    secao = linha
                elif secao == "[Filenames]" and linha.lower().startswith("bios") and "=" in linha:
                    escolhida = linha.split("=", 1)[1].strip()
    except OSError:
        pass
    if escolhida and os.path.isfile(os.path.join(pasta, escolhida)):
        return os.path.join(pasta, escolhida)
    try:
        nomes = sorted(os.listdir(pasta), key=str.lower)
    except OSError:
        return None
    for nome in nomes:
        achado = playstation(os.path.join(pasta, nome))
        if achado and achado[0] == "ps2":
            return os.path.join(pasta, nome)
    return None


def _pasta_com_algo(caminho):
    """A pasta existe e tem alguma coisa dentro (o Machines do MSX)?"""
    try:
        with os.scandir(caminho) as itens:
            return any(True for _item in itens)
    except OSError:
        return False


def _e_neogeo_no_disco(caminho):
    """O .zip e' a BIOS do Neo Geo? Le so o indice do zip (nao o arquivo inteiro)."""
    try:
        with zipfile.ZipFile(caminho) as z:
            return catalogo.PARTES_NEOGEO <= {i.CRC for i in z.infolist()}
    except (OSError, zipfile.BadZipFile, ValueError, RuntimeError):
        return False


def _firmware_do_ps3(raiz):
    """O firmware do PS3 esta instalado no RPCS3 (o mesmo teste do graficos)?"""
    base = os.path.join(raiz, "emuladores", "RPCS3")
    alvos = [base]
    try:
        alvos += [os.path.join(base, n) for n in os.listdir(base) if os.path.isdir(os.path.join(base, n))]
    except OSError:
        return False
    return any(os.path.isfile(os.path.join(a, "dev_flash", "sys", "external", "liblv2.sprx")) for a in alvos)


# ---------------------------------------------------------------------------
# Estado de cada BIOS
# ---------------------------------------------------------------------------

def estado(pasta_sistema, relativo, pasta_info=None):
    """'certa' (esta la, com a marca da versao certa), 'testada' (outra
    versao, testada aqui), 'outra' (esta la, com outra marca: pode funcionar,
    mas nao e' a recomendada), 'presente' (esta la; o ARENA nao conhece a
    marca) ou 'falta'."""
    caminho = _achar(pasta_sistema, relativo)
    if not caminho:
        return "falta"
    return _estado_do_arquivo(caminho, marcas_aceitas(relativo, pasta_info))


def _estado_do_arquivo(caminho, aceitas):
    if not aceitas:
        return "presente"
    marca = md5_do_arquivo(caminho)
    if marca in aceitas:
        return "certa"
    return "testada" if marca in TESTADAS else "outra"


ATIVA = ("certa", "testada", "presente", "outra")


def situacao(raiz=None, pasta_info=None):
    """Cada BIOS do catalogo, como esta agora (para a tela e os LEIA):
    [{id, console, nome_console, rotulo, pasta, o_que, nivel, grupo, estado,
      ativa, arquivo, detalhe, em_uso, sem_ela, recomendada}]."""
    raiz = raiz or RAIZ
    lugar = caminhos(raiz)
    pasta_info = pasta_info or lugar["info"]
    sistema = lugar["sistema"]
    nomes = consoles()
    instaladas_ps = {"ps1": _bios_de_ps(raiz, "ps1"), "ps2": _bios_de_ps(raiz, "ps2")}
    em_uso_ps2 = bios_em_uso_no_pcsx2(raiz)
    saida = []
    for entrada in catalogo.CATALOGO:
        item = {"id": entrada["id"], "console": entrada["console"],
                "nome_console": nomes.get(entrada["console"], {}).get("nome", entrada["pasta"]),
                "rotulo": catalogo.rotulo(entrada), "pasta": prateleira_relativa(entrada),
                "sub": entrada.get("sub", ""), "o_que": entrada["o_que"], "nivel": entrada["nivel"],
                "grupo": entrada.get("grupo", ""), "estado": "falta", "arquivo": "", "detalhe": "",
                "em_uso": False, "sem_ela": entrada.get("sem_ela") or catalogo.SEM_ELA[entrada["nivel"]],
                "recomendada": "", "nome_certo": catalogo.nome_de_instalacao(entrada)}
        tipo = entrada.get("pelo_conteudo")
        if tipo in ("ps1", "ps2"):
            da_regiao = [b for b in instaladas_ps[tipo] if b[1] == entrada["regiao"]]
            if da_regiao:
                def e_a_do_pcsx2(caminho):
                    return bool(em_uso_ps2) and os.path.normcase(caminho) == os.path.normcase(em_uso_ps2)
                usada = next((b for b in da_regiao if e_a_do_pcsx2(b[0])), da_regiao[0])
                item.update(estado="certa", arquivo=os.path.relpath(usada[0], raiz), detalhe=usada[2],
                            em_uso=e_a_do_pcsx2(usada[0]))
                # Todas as da regiao, como a lista de BIOS do PCSX2 (a mesma
                # BIOS em retroarch\system e na pasta do PCSX2 conta uma vez).
                marcas, todas = set(), []
                for caminho, _regiao, versao in da_regiao:
                    marca = md5_do_arquivo(caminho)
                    if marca in marcas:
                        continue
                    marcas.add(marca)
                    todas.append({"arquivo": os.path.basename(caminho), "versao": versao,
                                  "em_uso": e_a_do_pcsx2(caminho) or any(
                                      e_a_do_pcsx2(c) and md5_do_arquivo(c) == marca for c, _r, _v in da_regiao)})
                item["todas"] = todas
        elif entrada.get("especial") == "ps3":
            if _firmware_do_ps3(raiz):
                item.update(estado="presente", arquivo="emuladores\\RPCS3", detalhe="instalado no RPCS3")
        elif entrada.get("e_pasta"):
            caminho = os.path.join(sistema, entrada["destino"])
            if _pasta_com_algo(caminho):
                item.update(estado="presente", arquivo=os.path.relpath(caminho, raiz))
        else:
            caminho = _instalada(sistema, entrada)
            aceitas = _marcas_da_entrada(entrada, pasta_info)
            item["recomendada"] = aceitas[0] if aceitas else ""
            if caminho:
                situacao_do_arquivo = _estado_do_arquivo(caminho, aceitas)
                if entrada.get("pelo_conteudo") == "neogeo" and situacao_do_arquivo in ("outra", "presente"):
                    situacao_do_arquivo = "certa" if _e_neogeo_no_disco(caminho) else "outra"
                item.update(estado=situacao_do_arquivo, arquivo=os.path.relpath(caminho, raiz))
                marca = md5_do_arquivo(caminho)
                if situacao_do_arquivo == "testada":
                    item["detalhe"] = TESTADAS[marca]["texto"]
                elif situacao_do_arquivo == "certa":
                    item["detalhe"] = "versão conferida"
        item["ativa"] = item["estado"] in ATIVA
        saida.append(item)
    return saida


def resumo(itens):
    """{"precisa": [ativas, total], "alguns": [...], "melhor": [...]}: o
    grupo "uma" (PS1, PS2) conta uma vez -- basta uma regiao."""
    contas = {n: [0, 0] for n in catalogo.NIVEIS}
    vistos = set()
    for item in itens:
        if item["grupo"] == "uma":
            if item["console"] in vistos:
                continue
            vistos.add(item["console"])
            ativa = any(i["ativa"] for i in itens if i["console"] == item["console"] and i["grupo"] == "uma")
        else:
            ativa = item["ativa"]
        contas[item["nivel"]][1] += 1
        contas[item["nivel"]][0] += 1 if ativa else 0
    return contas


def grupo_satisfeito(itens, item):
    """No grupo "uma" (PS1, PS2), outra regiao ja ativa basta."""
    return item["grupo"] == "uma" and any(i["ativa"] for i in itens
                                          if i["console"] == item["console"] and i["grupo"] == "uma")


# ---------------------------------------------------------------------------
# Avisos do cartao do jogo e do console
# ---------------------------------------------------------------------------

def regiao_do_nome(nome_arquivo):
    """'europa', 'eua', 'japao' ou None (sem regiao, ou de varias) pelo nome
    do arquivo: "Sonic CD (Europe).chd", "Jogo (U) [!].bin"."""
    achadas = set()
    for grupo in re.findall(r"\(([^)]*)\)", os.path.basename(nome_arquivo or "")):
        for parte in re.split(r"\s*,\s*|\s*/\s*", grupo.strip().lower()):
            for regiao, padrao in _REGIOES:
                if padrao.match(parte):
                    achadas.add(regiao)
        if achadas:
            break           # so o primeiro grupo com regiao (o resto e' versao, idioma...)
    return achadas.pop() if len(achadas) == 1 else None


def _cabecalho_de_bs(cabecalho):
    """A regra do proprio Snes9x (bsx.cpp, is_bsx), sobre os 32 bytes do
    cabecalho do cartucho: 1 = jogo de Satellaview."""
    p = cabecalho
    if len(p) < 32:
        return 0
    if p[26] in (0x33, 0xFF) and (not p[21] or (p[21] & 131) == 128) and p[24] in (32, 33, 48, 49):
        mes = p[22]
        if not mes and not p[23]:
            return 2
        if (mes == 0xFF and p[23] == 0xFF) or (not (mes & 0xF) and ((mes >> 4) - 1) < 12):
            return 1
    return 0


def e_satellaview(nome_arquivo, caminho=None):
    """Jogo de Satellaview (cartucho "BS")? Pelo nome ("BS ..." ou .bs) e,
    com o arquivo a mao, confirmado pelo cabecalho, do jeito do Snes9x
    (S9xInitBSX: is_bsx em 0x7FC0 ou 0xFFC0, depois do cabecalho de 512 bytes
    das copias .smc). Achado de 03/10/2026: o "BS F-Zero Deluxe" e' uma versao
    feita para abrir sozinha, sem o BS-X (testado: abre) -- pelo nome, o
    cartao pedia a BIOS a toa. So le arquivo com nome de BS (ler o cabecalho
    de todo jogo de Super Nintendo a cada lista pesaria no Celeron)."""
    nome = os.path.basename(nome_arquivo or "")
    pelo_nome = nome.startswith("BS ") or nome.lower().endswith(".bs")
    if not pelo_nome or not caminho or not nome.lower().endswith((".sfc", ".smc", ".bs", ".fig", ".swc")):
        return pelo_nome
    try:
        tamanho = os.path.getsize(caminho)
        with open(caminho, "rb") as arquivo:
            inicio = 512 if tamanho % 1024 == 512 else 0
            dados = arquivo.read(inicio + 0x10000)
    except OSError:
        return pelo_nome
    return any(_cabecalho_de_bs(dados[inicio + base:inicio + base + 32]) == 1 for base in (0x7FC0, 0xFFC0))


def _prateleira_do_arquivo(plataforma_id, arquivo):
    """"BIOS\\Sega CD\\Europa" da BIOS 'bios_CD_E.bin' do console."""
    for entrada in catalogo.do_console(plataforma_id):
        if arquivo.lower() in catalogo.nomes_aceitos(entrada):
            return prateleira_relativa(entrada)
    return NOME_DA_PASTA


def prateleira_do_console(plataforma_id, arquivos=None):
    """A pasta do console na pasta BIOS ("BIOS\\Sega CD"). Com 'arquivos', a
    do primeiro deles (no Super Nintendo, BS-X.bin -> a do Satellaview)."""
    entradas = catalogo.do_console(plataforma_id)
    for arquivo in arquivos or []:
        baixo = os.path.basename(arquivo).lower()
        for entrada in entradas:
            if baixo in catalogo.nomes_aceitos(entrada):
                return NOME_DA_PASTA + "\\" + entrada["pasta"]
    return NOME_DA_PASTA + "\\" + entradas[0]["pasta"] if entradas else NOME_DA_PASTA


def prateleira_da_bios(nome_arquivo):
    """A prateleira de uma BIOS pelo nome do arquivo, de qualquer console
    ("bios_CD_E.bin" -> "BIOS\\Sega CD\\Europa"); "BIOS" se nao conhece."""
    baixo = os.path.basename(nome_arquivo or "").lower()
    for entrada in catalogo.CATALOGO:
        if baixo in catalogo.nomes_aceitos(entrada) or baixo == (entrada.get("nome") or "").lower():
            return prateleira_relativa(entrada)
    return NOME_DA_PASTA


def como_colocar_a_bios(prateleira_rel):
    return ("Ponha o arquivo na pasta %s do ARENA (com qualquer nome, ou o .zip em que ele veio) e "
            "clique em Conferir, em Ajustes → Emuladores (ou abra o ARENA de novo): ele reconhece a "
            "versão e instala sozinho." % prateleira_rel)


def aviso_do_jogo(plataforma_id, nome_arquivo, pasta_sistema, nome_console="", caminho=None):
    """O aviso do cartao quando falta a BIOS que ESTE jogo usa, ou None.
    'caminho': o arquivo do jogo (o Satellaview confere o cabecalho)."""
    if plataforma_id in POR_REGIAO:
        mapa = POR_REGIAO[plataforma_id]
        regiao = regiao_do_nome(nome_arquivo)
        if regiao:
            if tem(pasta_sistema, mapa[regiao]):
                return None
            return ("Este jogo é %s: ele só abre com a BIOS %s, e ela ainda não está no ARENA. %s"
                    % (NOME_DA_REGIAO[regiao], mapa[regiao],
                       como_colocar_a_bios(_prateleira_do_arquivo(plataforma_id, mapa[regiao]))))
        if any(tem(pasta_sistema, arquivo) for arquivo in set(mapa.values())):
            return None
        return ("Este console só abre jogo com a BIOS da região do jogo: %s. Nenhuma está no ARENA. %s"
                % (LISTA_POR_REGIAO[plataforma_id],
                   como_colocar_a_bios(NOME_DA_PASTA + "\\" + catalogo.do_console(plataforma_id)[0]["pasta"])))
    if plataforma_id == "dreamcast" and not tem(pasta_sistema, "dc/dc_boot.bin"):
        return ("Sem a BIOS do Dreamcast (dc_boot.bin), o emulador usa uma imitação dela: a maioria dos "
                "jogos abre, mas alguns travam (ex.: Marvel vs. Capcom 1). %s"
                % como_colocar_a_bios(NOME_DA_PASTA + "\\Dreamcast"))
    # BS-X.bios: o nome das versoes antigas do Snes9x (vale tambem).
    if (plataforma_id == "snes" and not (tem(pasta_sistema, "BS-X.bin") or tem(pasta_sistema, "BS-X.bios"))
            and e_satellaview(nome_arquivo, caminho)):
        return ("Jogo de Satellaview (o \"BS\" do nome): o Super Nintendo só abre esse tipo com a BIOS "
                "BS-X.bin, que é o cartucho \"BS-X - Sore wa Namae o Nusumareta Machi no Monogatari "
                "(Japan)\"; ela não vem na coleção de jogos do Satellaview. %s"
                % como_colocar_a_bios(NOME_DA_PASTA + "\\Super Nintendo (Satellaview)"))
    if plataforma_id not in COM_AVISO_PROPRIO:
        return frase_da_bios_que_falta(bios_obrigatorias_que_faltam(plataforma_id, pasta_sistema)) or None
    return None


# Os consoles que ja tem aviso proprio de BIOS (acima e no indexador) e o
# Amiga, cujo nucleo (PUAE) tem um substituto embutido da BIOS: muitos jogos
# abrem sem ela (o Alien Breed abriu na matriz da auditoria 3).
COM_AVISO_PROPRIO = {"ps1", "ps2", "ps3", "dreamcast", "snes", "neogeo", "arcade", "amiga"} | set(POR_REGIAO)


def bios_obrigatorias_que_faltam(plataforma_id, pasta_sistema):
    """As BIOS de nivel "precisa" deste console que nao estao instaladas.
    Achado da auditoria 3 (Fase 5): o ColecoVision sem a BIOS abria com a
    tela preta, e o cartao nao dizia nada -- o aviso de BIOS so cobria os
    consoles por regiao, o Dreamcast e o Satellaview. Grupo "uma": basta
    uma do grupo."""
    def instalada(entrada):
        if entrada.get("e_pasta"):          # o Machines e o Databases do MSX
            return _pasta_com_algo(os.path.join(pasta_sistema, *entrada["destino"].split("/")))
        return bool(_instalada(pasta_sistema, entrada))
    precisas = [e for e in catalogo.do_console(plataforma_id) if e.get("nivel") == "precisa"]
    faltam = [e for e in precisas if not instalada(e)]
    if any(e.get("grupo") == "uma" for e in precisas) and len(faltam) < len(precisas):
        return []
    return faltam


def _descricao_da_bios(entrada):
    """"a BIOS do ColecoVision (colecovision.rom)": o 'o_que' do catalogo,
    com o nome do arquivo quando ele ainda nao aparece."""
    nome = catalogo.nome_de_instalacao(entrada)
    o_que = entrada.get("o_que") or ("a BIOS " + nome)
    return o_que if nome.lower() in o_que.lower() else "%s (%s)" % (o_que, nome)


def frase_da_bios_que_falta(faltam):
    """A frase do cartao e do console quando falta BIOS obrigatoria (a lista
    de bios_obrigatorias_que_faltam), ou "". Duas partes: o que acontece e o
    que fazer."""
    if not faltam:
        return ""
    prateleira = prateleira_relativa(faltam[0])
    if any(e.get("e_pasta") for e in faltam):
        fazer = ("Ponha as pastas na pasta %s do ARENA (soltas, ou o .zip em que vieram) e clique em "
                 "Conferir, em Ajustes → Emuladores (ou abra o ARENA de novo)." % prateleira)
    else:
        fazer = como_colocar_a_bios(prateleira)
    return ("Falta a BIOS deste console (o programa de fábrica dele): %s. Sem ela, os jogos não abrem "
            "ou ficam com a tela preta. %s" % (" e ".join(_descricao_da_bios(e) for e in faltam), fazer))


def falta_para_o_console(plataforma_id, pasta_sistema):
    """Frase do que falta para o console abrir QUALQUER jogo, ou "": os de
    SEM_ELA_NAO_ABRE (pela regiao) e os que so abrem com a BIOS de nivel
    "precisa" do catalogo (ColecoVision, MSX, 3DO, Intellivision...: ate a
    auditoria 3 eles apareciam "prontos" e o jogo abria com a tela preta)."""
    if plataforma_id not in SEM_ELA_NAO_ABRE:
        if plataforma_id in COM_AVISO_PROPRIO:
            return ""
        return frase_da_bios_que_falta(bios_obrigatorias_que_faltam(plataforma_id, pasta_sistema))
    arquivos = set(POR_REGIAO[plataforma_id].values())
    if any(tem(pasta_sistema, a) for a in arquivos):
        return ""
    return ("Falta a BIOS da região do jogo: %s. Ponha na pasta %s do ARENA (pode ser o pacote .zip "
            "inteiro) e clique em Conferir, em Ajustes → Emuladores." % (
                LISTA_POR_REGIAO[plataforma_id],
                NOME_DA_PASTA + "\\" + catalogo.do_console(plataforma_id)[0]["pasta"]))


def _vale_ler_na_pasta_de_jogos(caminho, plataforma_id, tamanho):
    """Vale abrir este arquivo da pasta de jogos para ver se e' BIOS? So com
    o tamanho de uma BIOS do console e -- se a extensao tambem e' de jogo e o
    arquivo nao e' pequeno -- com nome de BIOS (scph1001.bin, syscard3.pce)."""
    if tamanho not in {e.get("tamanho") for e in catalogo.do_console(plataforma_id)}:
        return False
    extensao = os.path.splitext(caminho)[1].lower()
    de_jogo = extensao in consoles().get(plataforma_id, {}).get("extensoes", [])
    return not de_jogo or tamanho <= _PEQUENO or bool(_RE_NOME_DE_BIOS.search(os.path.basename(caminho)))


def e_bios_na_pasta_de_jogos(caminho, plataforma_id, pasta_info=None):
    """O arquivo que esta na pasta de JOGOS do console e' uma BIOS dele (pela
    marca ou pelo conteudo, nunca so pelo tamanho)? O aluno costuma deixar a
    BIOS junto dos jogos: aí ela nao aparece como jogo, e organizar() a leva
    para a prateleira e para retroarch\\system."""
    entradas = catalogo.do_console(plataforma_id)
    if not entradas or not caminho.lower().endswith(_EXTENSOES_NOS_JOGOS):
        return False
    try:
        tamanho = os.path.getsize(caminho)
    except OSError:
        return False
    if not _vale_ler_na_pasta_de_jogos(caminho, plataforma_id, tamanho):
        return False
    if any(e.get("pelo_conteudo") in ("ps1", "ps2") for e in entradas):
        achado = playstation(caminho)
        if achado and achado[0] == plataforma_id:
            return True
    marca = md5_do_arquivo(caminho)
    nomes = _reverso(pasta_info).get(marca, set())
    return any(n in nomes for e in entradas for n in catalogo.nomes_aceitos(e))


# ---------------------------------------------------------------------------
# Reconhecer um arquivo
# ---------------------------------------------------------------------------

def _reconhecer(dados, nome, folha, pasta_info=None):
    """(md5, [{"id", "como", "nome"}]): o que este arquivo e'.

    como: "marca" (a marca bate com a de um .info), "testada", "conteudo"
    (PlayStation e neogeo.zip), "nome" (nome exato de uma BIOS de que o
    ARENA nao conhece marca nenhuma) ou "tamanho" (so na prateleira certa).
    'nome': o nome com que deve ser instalada (o da marca), ou ""."""
    md5 = _md5(dados)
    achados = []
    nomes = _reverso(pasta_info).get(md5, set())
    baixo = os.path.basename(nome).lower()
    for entrada in catalogo.CATALOGO:
        if entrada.get("pelo_conteudo") in ("ps1", "ps2") or entrada.get("e_pasta") or entrada.get("especial"):
            continue
        aceitos = catalogo.nomes_aceitos(entrada)
        casou = next((n for n in aceitos if n in nomes), None)
        if casou:
            achados.append({"id": entrada["id"], "como": "marca", "nome": casou})
        elif TESTADAS.get(md5, {}).get("id") == entrada["id"]:
            achados.append({"id": entrada["id"], "como": "testada", "nome": ""})
        elif baixo in aceitos and not _marcas_da_entrada(entrada, pasta_info) \
                and not entrada.get("pelo_conteudo"):
            achados.append({"id": entrada["id"], "como": "nome", "nome": baixo})
    if len(dados) in (524288, 4194304):
        achado = _playstation_dos_bytes(dados)
        if achado and (achado[0], achado[1]) in ID_DO_PLAYSTATION:
            achados.append({"id": ID_DO_PLAYSTATION[(achado[0], achado[1])], "como": "conteudo", "nome": "",
                            "versao": achado[2]})
    if baixo.endswith(".zip") and catalogo.e_neogeo_zip(dados):
        achados.append({"id": "neogeo", "como": "conteudo", "nome": "neogeo.zip"})
    if not achados and folha:
        mesmos = {e["id"] for e in folha if e.get("tamanho") == len(dados)
                  and not e.get("pelo_conteudo") and not e.get("e_pasta")}
        if len(mesmos) == 1:
            achados.append({"id": mesmos.pop(), "como": "tamanho", "nome": ""})
    return md5, achados


def _itens_do_zip(z, lugar, profundidade=0):
    """(nome, caminho dentro, dados) de cada arquivo com cara de BIOS dentro
    do zip -- e dentro de um zip que esteja dentro dele (o pacote do Sega CD
    do Rafael: "Sega Mega CD BIOS.zip" dentro de segamegacdbios.zip).
    'caminho dentro' e' a lista de nomes ate o arquivo."""
    for item in z.infolist():
        if item.is_dir():
            continue
        nome = os.path.basename(item.filename)
        baixo = nome.lower()
        if baixo.endswith(".zip") and profundidade == 0 and item.file_size <= PACOTE_MAXIMO:
            try:
                dados_zip = z.read(item)
            except (zipfile.BadZipFile, ValueError, RuntimeError, OSError, zipfile.LargeZipFile):
                continue
            # O proprio zip pode ser a BIOS (neogeo.zip, cdimono1.zip)...
            yield nome, lugar + [item.filename], dados_zip
            # ... ou um pacote com BIOS dentro.
            try:
                with zipfile.ZipFile(io.BytesIO(dados_zip)) as interno:
                    yield from _itens_do_zip(interno, lugar + [item.filename], profundidade + 1)
            except (zipfile.BadZipFile, ValueError, RuntimeError, OSError):
                pass
            continue
        if item.file_size > BIOS_MAXIMA or baixo.endswith(_NAO_E_BIOS):
            continue
        try:
            yield nome, lugar + [item.filename], z.read(item)
        except (zipfile.BadZipFile, ValueError, RuntimeError, OSError):
            continue


def _ler_de_dentro(caminho, dentro):
    """Os bytes de um arquivo (dentro = [] ) ou de um item de zip (dentro =
    ["pacote interno.zip", "bios.bin"])."""
    if not dentro:
        return _ler(caminho)
    with zipfile.ZipFile(caminho) as z:
        dados = z.read(dentro[0])
    for nome in dentro[1:]:
        with zipfile.ZipFile(io.BytesIO(dados)) as z:
            dados = z.read(nome)
    return dados


# ---------------------------------------------------------------------------
# Organizar
# ---------------------------------------------------------------------------

def _gravar(destino, dados):
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    temporario = destino + ".instalando"
    with open(temporario, "wb") as arquivo:
        arquivo.write(dados)
    os.replace(temporario, destino)


def _ler_conferidos(caminho):
    try:
        with open(caminho, encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except (OSError, ValueError):
        return {}
    if not isinstance(dados, dict) or dados.get("versao") != 2:
        return {}       # o formato de antes (so pacotes) e' lido de novo
    return dados


def _gravar_json(caminho, dados):
    try:
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        temporario = caminho + ".tmp"
        with open(temporario, "w", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, ensure_ascii=False, indent=1, sort_keys=True)
        os.replace(temporario, caminho)
    except OSError:
        pass


def _folhas(raiz):
    """{pasta da prateleira (normcase): [entradas]}."""
    folhas = {}
    for entrada in catalogo.CATALOGO:
        folhas.setdefault(os.path.normcase(prateleira(raiz, entrada)), []).append(entrada)
    return folhas


def criar_prateleiras(raiz=None):
    """Cria BIOS\\<console>[\\<regiao>] que faltam. Devolve quantas criou."""
    raiz = raiz or RAIZ
    criadas = 0
    for entrada in catalogo.CATALOGO:
        pasta = prateleira(raiz, entrada)
        if not os.path.isdir(pasta):
            try:
                os.makedirs(pasta, exist_ok=True)
                criadas += 1
            except OSError:
                pass
    return criadas


def _candidatos(raiz, conferidos, pasta_info, avisos):
    """Os arquivos que podem ser BIOS, ja reconhecidos (lendo so o que mudou):
    [{"arquivo": caminho, "dentro": [...], "md5", "achados": [...],
      "origem": "prateleira"|"sistema"|"jogos", "folha": pasta}]."""
    lugar = caminhos(raiz)
    folhas = _folhas(raiz)
    raiz_bios = os.path.normcase(lugar["bios"])
    vistos = {}
    fontes = []      # (caminho, origem, folha)
    contados = 0
    for atual, subpastas, arquivos in os.walk(lugar["bios"]):
        subpastas.sort()
        # A folha mais perto (o pacote numa subpasta da regiao vale pela regiao).
        folha, subindo = None, os.path.normcase(atual)
        while subindo.startswith(raiz_bios):
            if subindo in folhas:
                folha = subindo
                break
            pai = os.path.dirname(subindo)
            if pai == subindo:
                break
            subindo = pai
        for nome in sorted(arquivos):
            contados += 1
            if contados > LIMITE_DE_ARQUIVOS:
                avisos.append("A pasta BIOS tem arquivos demais (mais de %d): o ARENA conferiu só os "
                              "primeiros. Deixe lá só as BIOS." % LIMITE_DE_ARQUIVOS)
                break
            if nome in (ARQUIVO_LEIA, ARQUIVO_RESUMO) or nome.endswith((".instalando", ".tmp")):
                continue
            fontes.append((os.path.join(atual, nome), "prateleira", folha))
        if contados > LIMITE_DE_ARQUIVOS:
            break
    # Pacotes .zip (e arquivos soltos com outro nome) deixados em retroarch\system.
    try:
        for nome in sorted(os.listdir(lugar["sistema"])):
            caminho = os.path.join(lugar["sistema"], nome)
            if os.path.isfile(caminho) and not nome.lower().endswith(_NAO_E_BIOS):
                fontes.append((caminho, "sistema", None))
    except OSError:
        pass
    # BIOS deixada junto dos jogos (so a raiz da pasta do console e um nivel
    # abaixo; so arquivo com tamanho de BIOS daquele console).
    pastas = consoles()
    for console in sorted({e["console"] for e in catalogo.CATALOGO}):
        pasta = os.path.join(lugar["jogos"], pastas.get(console, {}).get("pasta", "\0"))
        for atual, subpastas, arquivos in os.walk(pasta):
            if os.path.relpath(atual, pasta) != ".":
                subpastas[:] = []
            for nome in arquivos:
                baixo = nome.lower()
                if not baixo.endswith(_EXTENSOES_NOS_JOGOS):
                    continue
                caminho = os.path.join(atual, nome)
                if console == "neogeo":      # o neogeo.zip nao tem tamanho fixo
                    if baixo == "neogeo.zip":
                        fontes.append((caminho, "jogos", None))
                    continue
                try:
                    if _vale_ler_na_pasta_de_jogos(caminho, console, os.path.getsize(caminho)):
                        fontes.append((caminho, "jogos", None))
                except OSError:
                    pass
    novos = {}
    for caminho, origem, folha in fontes:
        try:
            info = os.stat(caminho)
        except OSError:
            continue
        relativo = os.path.relpath(caminho, raiz).replace("\\", "/")
        marca = "%d|%d" % (info.st_size, info.st_mtime_ns)
        registro = conferidos.get(relativo)
        if not (isinstance(registro, dict) and registro.get("marca") == marca):
            registro = {"marca": marca, "itens": []}
            e_zip = caminho.lower().endswith(".zip")
            if os.path.basename(caminho).lower() == "ps3updat.pup":
                # O firmware do PS3 (200 MB): quem instala e' o RPCS3; nao precisa ler.
                registro["itens"].append({"dentro": [], "md5": None,
                                          "achados": [{"id": "ps3-firmware", "como": "nome", "nome": ""}]})
            elif (e_zip and info.st_size > PACOTE_MAXIMO) or (not e_zip and info.st_size > BIOS_MAXIMA):
                registro["grande"] = True
                registro["itens"].append({"dentro": [], "md5": None, "achados": []})
            else:
                try:
                    dados = _ler(caminho)
                except OSError:
                    continue
                folha_entradas = folhas.get(folha) if folha else None
                md5, achados = _reconhecer(dados, caminho, folha_entradas, pasta_info)
                registro["itens"].append({"dentro": [], "md5": md5, "achados": achados})
                if e_zip and not any(a["id"] == "neogeo" for a in achados):
                    try:
                        with zipfile.ZipFile(io.BytesIO(dados)) as z:
                            for nome_item, dentro, dados_item in _itens_do_zip(z, []):
                                md5_item, achados_item = _reconhecer(dados_item, nome_item, folha_entradas,
                                                                     pasta_info)
                                if achados_item:
                                    registro["itens"].append({"dentro": dentro, "md5": md5_item,
                                                              "achados": achados_item})
                    except (zipfile.BadZipFile, ValueError, RuntimeError, OSError):
                        registro["zip_ruim"] = True
                del dados
        novos[relativo] = registro
        for item in registro.get("itens", []):
            vistos.setdefault(relativo, []).append(dict(item, arquivo=caminho, origem=origem, folha=folha,
                                                        relativo=relativo))
    conferidos.clear()
    conferidos.update(novos)
    return [c for lista in vistos.values() for c in lista]


PRIORIDADE = {"marca": 0, "testada": 1, "conteudo": 2, "nome": 3, "tamanho": 4}


def _melhor_candidato(entrada, candidatos, pasta_info, so_recomendada=False):
    """O melhor arquivo para esta BIOS: a marca mais recomendada primeiro."""
    aceitas = _marcas_da_entrada(entrada, pasta_info)
    melhores = []
    for candidato in candidatos:
        for achado in candidato["achados"]:
            if achado["id"] != entrada["id"]:
                continue
            if so_recomendada and achado["como"] != "marca":
                continue
            ordem = aceitas.index(candidato["md5"]) if candidato["md5"] in aceitas else len(aceitas)
            # Prateleira primeiro (e' onde a pessoa pos), depois o resto.
            lugar = {"prateleira": 0, "jogos": 1, "sistema": 2}.get(candidato["origem"], 3)
            melhores.append(((PRIORIDADE[achado["como"]], ordem, lugar, candidato["relativo"]), candidato, achado))
    if not melhores:
        return None, None
    melhores.sort(key=lambda m: m[0])
    return melhores[0][1], melhores[0][2]


def _nome_livre(pasta, nome):
    """O nome, ou "nome (2).ext" se ja existe um arquivo com ele."""
    if not os.path.exists(os.path.join(pasta, nome)):
        return nome
    base, extensao = os.path.splitext(nome)
    for numero in range(2, 100):
        tentativa = "%s (%d)%s" % (base, numero, extensao)
        if not os.path.exists(os.path.join(pasta, tentativa)):
            return tentativa
    return None


def _instalar(raiz, candidatos, pasta_info, feito):
    """Poe em retroarch\\system o que falta (passo 3)."""
    lugar = caminhos(raiz)
    sistema = lugar["sistema"]
    for entrada in catalogo.CATALOGO:
        if entrada.get("especial") or entrada.get("e_pasta"):
            continue
        tipo = entrada.get("pelo_conteudo")
        if tipo in ("ps1", "ps2"):
            if any(b[1] == entrada["regiao"] for b in _bios_de_ps(raiz, tipo)):
                continue
            candidato, achado = _melhor_candidato(entrada, candidatos, pasta_info)
            if not candidato or candidato["origem"] == "sistema" and not candidato["dentro"]:
                continue        # ja esta solta em retroarch\system (com outro nome): ja conta
            nome = _nome_livre(sistema, entrada["nome"])
            if not nome:
                continue
            try:
                _gravar(os.path.join(sistema, nome), _ler_de_dentro(candidato["arquivo"], candidato["dentro"]))
            except (OSError, zipfile.BadZipFile, KeyError, ValueError, RuntimeError):
                continue
            feito["instaladas"].append({"id": entrada["id"], "arquivo": "retroarch\\system\\" + nome,
                                        "de": _de_onde(raiz, candidato)})
            continue
        instalada = _instalada(sistema, entrada)
        destino_rel = entrada["destino"]
        if instalada:
            # So troca a de OUTRA versao pela recomendada (a antiga vai para o backup).
            aceitas = _marcas_da_entrada(entrada, pasta_info)
            if not aceitas or _estado_do_arquivo(instalada, aceitas) != "outra":
                continue
            candidato, achado = _melhor_candidato(entrada, candidatos, pasta_info, so_recomendada=True)
            if not candidato or candidato["md5"] == md5_do_arquivo(instalada):
                continue
            guarda = os.path.join(raiz, "backup", "bios-trocadas", time.strftime("%Y-%m-%d_%H%M%S"))
            try:
                os.makedirs(guarda, exist_ok=True)
                shutil.copy2(instalada, os.path.join(guarda, os.path.basename(instalada)))
            except OSError:
                continue     # sem a copia da antiga, nao troca
            destino = instalada
        else:
            candidato, achado = _melhor_candidato(entrada, candidatos, pasta_info)
            if not candidato:
                continue
            pasta_destino = os.path.dirname(destino_rel)
            nome = achado["nome"] if achado.get("nome") in catalogo.nomes_aceitos(entrada) else ""
            # O nome do .info em minusculas ("bios_cd_e.bin") volta ao jeito do catalogo.
            nome = next((n for n in [catalogo.nome_de_instalacao(entrada)] + list(entrada.get("alternativas", []))
                         if n.lower() == nome), "") or catalogo.nome_de_instalacao(entrada)
            destino = os.path.join(sistema, *(pasta_destino.split("/") if pasta_destino else []), nome)
            if candidato["origem"] == "sistema" and not candidato["dentro"] and \
                    os.path.normcase(candidato["arquivo"]) == os.path.normcase(destino):
                continue
        try:
            _gravar(destino, _ler_de_dentro(candidato["arquivo"], candidato["dentro"]))
        except (OSError, zipfile.BadZipFile, KeyError, ValueError, RuntimeError):
            continue
        feito["instaladas"].append({"id": entrada["id"], "arquivo": os.path.relpath(destino, raiz),
                                    "de": _de_onde(raiz, candidato)})


def _de_onde(raiz, candidato):
    texto = os.path.relpath(candidato["arquivo"], raiz)
    if candidato["dentro"]:
        texto += " > " + " > ".join(os.path.basename(n) for n in candidato["dentro"])
    return texto


def _copias_extras(raiz, feito):
    """O neogeo.zip tambem na pasta do Arcade (o MAME so procura na pasta do jogo)."""
    lugar = caminhos(raiz)
    pastas = consoles()
    for entrada in catalogo.CATALOGO:
        if not entrada.get("tambem_na_pasta_de"):
            continue
        instalada = _instalada(lugar["sistema"], entrada)
        if not instalada:
            continue
        for console in entrada["tambem_na_pasta_de"]:
            pasta = os.path.join(lugar["jogos"], pastas.get(console, {}).get("pasta", "\0"))
            if not os.path.isdir(pasta):
                continue
            nome = catalogo.nome_de_instalacao(entrada)
            if any(n.lower() == nome.lower() for n in os.listdir(pasta)):
                continue
            try:
                shutil.copy2(instalada, os.path.join(pasta, nome))
            except OSError:
                continue
            feito["instaladas"].append({"id": entrada["id"], "arquivo": os.path.relpath(os.path.join(pasta, nome), raiz),
                                        "de": os.path.relpath(instalada, raiz)})


def _instalar_pastas(raiz, feito):
    """MSX: as pastas Machines e Databases da prateleira (soltas, ou dentro
    de um .zip) vao para retroarch\\system, sem trocar arquivo que ja existe."""
    lugar = caminhos(raiz)
    for entrada in catalogo.CATALOGO:
        if not entrada.get("e_pasta"):
            continue
        destino = os.path.join(lugar["sistema"], entrada["destino"])
        if _pasta_com_algo(destino):
            continue
        origem = prateleira(raiz, entrada)
        alvo = entrada["destino"].lower()
        copiados = 0
        for atual, subpastas, arquivos in os.walk(origem):
            subpastas.sort()
            partes = os.path.relpath(atual, origem).split(os.sep)
            if alvo in [p.lower() for p in partes]:
                indice = [p.lower() for p in partes].index(alvo)
                for nome in arquivos:
                    final = os.path.join(destino, *partes[indice + 1:], nome)
                    if not os.path.exists(final):
                        try:
                            os.makedirs(os.path.dirname(final), exist_ok=True)
                            shutil.copy2(os.path.join(atual, nome), final)
                            copiados += 1
                        except OSError:
                            pass
            for nome in arquivos:
                if not nome.lower().endswith(".zip"):
                    continue
                try:
                    with zipfile.ZipFile(os.path.join(atual, nome)) as z:
                        for item in z.infolist():
                            pedacos = item.filename.replace("\\", "/").split("/")
                            baixos = [p.lower() for p in pedacos]
                            if item.is_dir() or alvo not in baixos[:-1]:
                                continue
                            resto = pedacos[baixos.index(alvo) + 1:]
                            if any(p in ("", ".", "..") or ":" in p for p in resto):
                                continue
                            final = os.path.join(destino, *resto)
                            if not os.path.exists(final):
                                os.makedirs(os.path.dirname(final), exist_ok=True)
                                with z.open(item) as de, open(final + ".instalando", "wb") as para:
                                    shutil.copyfileobj(de, para)
                                os.replace(final + ".instalando", final)
                                copiados += 1
                except (OSError, zipfile.BadZipFile, ValueError, RuntimeError):
                    continue
        if copiados:
            feito["instaladas"].append({"id": entrada["id"], "arquivo": os.path.relpath(destino, raiz),
                                        "de": "%s (%d arquivos)" % (prateleira_relativa(entrada), copiados)})


def _copiar_para_as_prateleiras(raiz, candidatos, copiadas, feito):
    """A BIOS que ja estava instalada vai para a prateleira dela (passo 4) --
    uma vez por arquivo: quem apaga da prateleira nao ve ela voltar.
    'copiadas': {arquivo instalado: marca} do que ja foi copiado."""
    # So conta o que esta na pasta DAQUELA BIOS: o pacote com as 3 regioes do
    # Sega CD, deixado em BIOS\Sega CD, nao poe a europeia em BIOS\Sega CD\Europa
    # -- a copia solta vai para la (a pasta de cada regiao mostra a dela).
    entradas = catalogo.por_id()
    na_prateleira = {}
    for candidato in candidatos:
        if candidato["origem"] != "prateleira":
            continue
        for achado in candidato["achados"]:
            entrada = entradas.get(achado["id"])
            if entrada and candidato["folha"] == os.path.normcase(prateleira(raiz, entrada)):
                na_prateleira.setdefault(achado["id"], set()).add(candidato["md5"])
    lugar = caminhos(raiz)
    pares = []
    for entrada in catalogo.CATALOGO:
        if entrada.get("especial") or entrada.get("e_pasta"):
            continue
        tipo = entrada.get("pelo_conteudo")
        if tipo in ("ps1", "ps2"):
            for caminho, regiao, _versao in _bios_de_ps(raiz, tipo):
                if regiao == entrada["regiao"]:
                    pares.append((entrada, caminho))
        else:
            instalada = _instalada(lugar["sistema"], entrada)
            if instalada:
                pares.append((entrada, instalada))
    for entrada, caminho in pares:
        marca = md5_do_arquivo(caminho) if os.path.getsize(caminho) <= BIOS_MAXIMA else None
        if not marca or marca in na_prateleira.get(entrada["id"], set()):
            continue
        relativo = os.path.relpath(caminho, raiz).replace("\\", "/")
        if copiadas.get(relativo) == marca:
            continue        # ja foi copiada uma vez (e alguem tirou da prateleira)
        pasta = prateleira(raiz, entrada)
        nome = _nome_livre(pasta, os.path.basename(caminho))
        if not nome:
            continue
        try:
            os.makedirs(pasta, exist_ok=True)
            shutil.copy2(caminho, os.path.join(pasta, nome))
        except OSError:
            continue
        copiadas[relativo] = marca
        na_prateleira.setdefault(entrada["id"], set()).add(marca)
        feito["copiadas"].append({"id": entrada["id"], "arquivo": os.path.relpath(os.path.join(pasta, nome), raiz),
                                  "de": os.path.relpath(caminho, raiz)})


def _gravar_texto(caminho, texto):
    """Grava o LEIA so se mudou (pen drive e cartao SD gastam com gravacao)."""
    conteudo = texto.replace("\r\n", "\n").replace("\n", "\r\n")
    try:
        with open(caminho, encoding="utf-8-sig", newline="") as arquivo:
            if arquivo.read() == conteudo:
                return False
    except OSError:
        pass
    try:
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho + ".tmp", "w", encoding="utf-8-sig", newline="") as arquivo:
            arquivo.write(conteudo)
        os.replace(caminho + ".tmp", caminho)
        return True
    except OSError:
        return False


def _frase_do_estado(item, itens):
    estado_item = item["estado"]
    if estado_item == "falta":
        if grupo_satisfeito(itens, item):
            return "não está (não faz falta: a de outra região já serve)"
        return "FALTA"
    if estado_item == "outra":
        return ("ATIVA, mas de outra versão: pode funcionar; se algum jogo der problema, troque pela "
                "recomendada")
    texto = "ATIVA"
    if item["detalhe"]:
        texto += " (%s)" % item["detalhe"]
    if item.get("em_uso"):
        texto += " — é com esta que o PCSX2 liga"
    return texto


COMO_COLOCAR = ("Para colocar ou trocar: ponha o arquivo nesta pasta — o nome não importa, e pode ser o\n"
                ".zip em que ele veio — e abra o ARENA (ou clique em Conferir, em Ajustes → Emuladores).\n"
                "O ARENA confere a versão e instala no lugar certo, com o nome certo. Não precisa\n"
                "mexer em retroarch\\system.")


def _texto_da_folha(raiz, folha_entradas, itens, nao_reconhecidos, subpastas):
    por_id = {i["id"]: i for i in itens}
    primeira = folha_entradas[0]
    linhas = ["%s — BIOS do %s" % (prateleira_relativa(primeira), por_id[primeira["id"]]["nome_console"]), ""]
    for entrada in folha_entradas:
        item = por_id[entrada["id"]]
        linhas.append("O que vai aqui: %s." % entrada["o_que"])
        if entrada.get("especial") == "ps3":
            if item["ativa"]:
                situacao_ps3 = "ATIVA (instalado no RPCS3)"
            elif _achar(prateleira(raiz, entrada), "PS3UPDAT.PUP"):
                situacao_ps3 = "FALTA INSTALAR (o arquivo já está nesta pasta)"
            else:
                situacao_ps3 = "FALTA"
            linhas.append("Situação: %s." % situacao_ps3)
            linhas += ["", "Como instalar: ponha o PS3UPDAT.PUP nesta pasta, abra o RPCS3",
                       "(emuladores\\RPCS3) e use o menu File → Install Firmware, escolhendo este arquivo.",
                       "É uma vez só; depois, todos os jogos de PS3 abrem."]
            continue
        linhas.append("Situação: %s." % _frase_do_estado(item, itens))
        if item["arquivo"]:
            linhas.append("O emulador usa: %s" % item["arquivo"])
        linhas.append("Sem ela: %s." % item["sem_ela"])
        if not item["ativa"] and not entrada.get("pelo_conteudo") and not entrada.get("e_pasta"):
            linhas.append("O arquivo: %s (o nome não importa: o ARENA reconhece pelo conteúdo)."
                          % item["nome_certo"])
        if item["recomendada"] and item["estado"] in ("falta", "outra"):
            linhas.append("Versão recomendada (marca MD5, para conferir): %s" % item["recomendada"])
        linhas.append("")
    if any(e.get("grupo") == "uma" for e in folha_entradas):
        linhas += ["Basta UMA BIOS deste console, de qualquer região: com ela, os jogos de todas as",
                   "regiões abrem. As outras regiões são opcionais.", ""]
    if subpastas:
        linhas.append("Pastas aqui dentro: %s." % ", ".join(subpastas))
        linhas.append("")
    if nao_reconhecidos:
        linhas.append("Arquivos desta pasta que o ARENA NÃO reconheceu como BIOS deste console:")
        for nome in nao_reconhecidos:
            linhas.append("  - %s" % nome)
        linhas.append("  (pode ser de outro console, de outra região, ou uma versão que o ARENA não conhece)")
        linhas.append("")
    if not any(e.get("especial") for e in folha_entradas):
        linhas.append(COMO_COLOCAR)
    return "\n".join(linhas).rstrip() + "\n"


def _texto_do_console(pasta, entradas, itens):
    """O LEIA da pasta do console quando a BIOS fica nas subpastas (regioes)."""
    por_id = {i["id"]: i for i in itens}
    nome = por_id[entradas[0]["id"]]["nome_console"]
    linhas = ["BIOS\\%s — as BIOS do %s" % (pasta, nome), ""]
    if any(e.get("grupo") == "uma" for e in entradas):
        linhas += ["Basta UMA, de qualquer região: com ela, os jogos de todas as regiões abrem.", ""]
    else:
        linhas += ["Cada pasta é de uma região (ou de uma parte do console). Ponha cada BIOS na pasta dela.", ""]
    largura = max(len(e.get("sub") or pasta) for e in entradas)
    for entrada in entradas:
        item = por_id[entrada["id"]]
        nome_da_pasta = entrada.get("sub") or "(nesta pasta)"
        linhas.append("  %s  %s" % (nome_da_pasta.ljust(largura + 2, "."), _frase_do_estado(item, itens)))
    linhas += ["", COMO_COLOCAR]
    return "\n".join(linhas) + "\n"


def _texto_do_resumo(itens, contas, sem_bios):
    linhas = ["BIOS DO ARENA  (o ARENA atualiza este arquivo sozinho)", "",
              "BIOS é o programinha que vem de fábrica dentro do console e liga ele por dentro.",
              "Alguns consoles não abrem jogo nenhum sem ela; outros só precisam dela para",
              "alguns jogos; e em outros ela é opcional.", "",
              "Cada console tem a sua pasta aqui (o mesmo nome da pasta de jogos dele). Ponha a",
              "BIOS na pasta do console — com qualquer nome, ou o .zip em que ela veio — e abra o",
              "ARENA (ou clique em Conferir, em Ajustes → Emuladores). Ele confere a versão e",
              "instala onde o emulador procura.", "",
              "RESUMO"]
    total_ativas = sum(c[0] for c in contas.values())
    total = sum(c[1] for c in contas.values())
    linhas.append("  Já estão ativas: %d de %d." % (total_ativas, total))
    for nivel in catalogo.NIVEIS:
        linhas.append("  %-62s %d de %d" % (catalogo.TITULO_DO_NIVEL[nivel] + ":", contas[nivel][0],
                                            contas[nivel][1]))
    linhas.append("  (PS1 e PS2 contam uma vez cada: basta uma BIOS de qualquer região.)")
    for nivel in catalogo.NIVEIS:
        faltam = [i for i in itens if i["nivel"] == nivel and not i["ativa"] and not grupo_satisfeito(itens, i)]
        vistos, nomes = set(), []
        for item in faltam:
            if item["grupo"] == "uma":
                if item["console"] in vistos:
                    continue
                vistos.add(item["console"])
                nomes.append("  - %s: uma BIOS de qualquer região → pasta BIOS\\%s (EUA, Europa ou Japão)"
                             % (item["nome_console"], item["pasta"].split("\\")[1]))
            else:
                nome = "" if item["nome_certo"].lower() in item["o_que"].lower() else " (%s)" % item["nome_certo"]
                nomes.append("  - %s: %s%s → pasta %s" % (item["nome_console"], item["o_que"], nome,
                                                         item["pasta"]))
        if nomes:
            linhas += ["", "FALTAM — %s" % catalogo.TITULO_DO_NIVEL[nivel]] + nomes
    ativas = [i for i in itens if i["ativa"]]
    if ativas:
        linhas += ["", "JÁ ESTÃO ATIVAS"]
        for item in ativas:
            detalhe = (" — " + item["detalhe"]) if item["detalhe"] else ""
            outra = " (outra versão)" if item["estado"] == "outra" else ""
            linhas.append("  - %s%s%s" % (item["rotulo"], outra, detalhe))
    if sem_bios:
        linhas += ["", "NÃO PRECISAM DE BIOS: %s." % ", ".join(sem_bios)]
    linhas += ["", "Fliperama (MAME e FBNeo): cada placa tem a sua BIOS em .zip (neogeo.zip, pgm.zip,",
               "naomi.zip...), que vai na mesma pasta dos jogos dela. O cartão do jogo avisa qual falta.",
               "", "O ARENA não baixa BIOS: ela vem do console de verdade."]
    return "\n".join(linhas) + "\n"


def consoles_sem_bios():
    """Os nomes dos consoles do ARENA que nao usam BIOS nenhuma."""
    com = {e["console"] for e in catalogo.CATALOGO} | {"arcade"}
    return [info["nome"] for cid, info in consoles().items() if cid not in com]


def escrever_leias(raiz, itens, candidatos):
    """Passo 5: o LEIA de cada prateleira e o resumo da raiz."""
    gravados = 0
    folhas = {}
    for entrada in catalogo.CATALOGO:
        folhas.setdefault(prateleira(raiz, entrada), []).append(entrada)
    # Nao reconhecido: o arquivo da prateleira em que nada (nem ele, nem o
    # que esta dentro dele, se e' zip) e' BIOS conhecida.
    reconhecidos = {c["arquivo"] for c in candidatos if c["achados"]}
    estranhos = {}
    for candidato in candidatos:
        if candidato["origem"] == "prateleira" and not candidato["dentro"] \
                and candidato["arquivo"] not in reconhecidos:
            estranhos.setdefault(os.path.normcase(os.path.dirname(candidato["arquivo"])), []).append(
                os.path.basename(candidato["arquivo"]))
    por_console = {}
    for entrada in catalogo.CATALOGO:
        por_console.setdefault(entrada["pasta"], []).append(entrada)
    for pasta, entradas in folhas.items():
        subpastas = []
        if os.path.normcase(os.path.dirname(pasta)) == os.path.normcase(os.path.join(raiz, NOME_DA_PASTA)):
            subpastas = sorted({e["sub"] for e in por_console[entradas[0]["pasta"]] if e.get("sub")})
        texto = _texto_da_folha(raiz, entradas, itens, estranhos.get(os.path.normcase(pasta), []), subpastas)
        gravados += _gravar_texto(os.path.join(pasta, ARQUIVO_LEIA), texto)
    for pasta, entradas in por_console.items():
        caminho = os.path.join(raiz, NOME_DA_PASTA, pasta)
        if caminho in folhas:
            continue        # a pasta do console tambem e' folha: o LEIA dela ja foi
        texto = _texto_do_console(pasta, entradas, itens)
        if estranhos.get(os.path.normcase(caminho)):
            texto += ("\nArquivos desta pasta que o ARENA NÃO reconheceu: %s. Ponha cada BIOS na pasta "
                      "da região dela.\n" % ", ".join(estranhos[os.path.normcase(caminho)]))
        gravados += _gravar_texto(os.path.join(caminho, ARQUIVO_LEIA), texto)
    contas = resumo(itens)
    gravados += _gravar_texto(os.path.join(raiz, NOME_DA_PASTA, ARQUIVO_RESUMO),
                              _texto_do_resumo(itens, contas, consoles_sem_bios()))
    return gravados


def organizar(raiz=None, pasta_info=None):
    """Arruma as BIOS (os 5 passos do topo deste arquivo). Devolve
    {"instaladas": [...], "copiadas": [...], "avisos": [...], "leias": n,
     "itens": situacao(), "resumo": {...}}."""
    raiz = raiz or RAIZ
    lugar = caminhos(raiz)
    pasta_info = pasta_info or lugar["info"]
    with _trava_organizar:
        feito = {"instaladas": [], "copiadas": [], "avisos": []}
        pasta_nova = not os.path.isdir(lugar["bios"])
        criar_prateleiras(raiz)
        arquivo_conferidos = os.path.join(lugar["dados"], ARQUIVO_CONFERIDOS)
        conferidos = _ler_conferidos(arquivo_conferidos)
        antes = json.dumps(conferidos, sort_keys=True)
        arquivos = conferidos.setdefault("arquivos", {})
        copiadas = conferidos.setdefault("copiadas", {})
        if pasta_nova:
            # A pasta BIOS acabou de nascer (ARENA copiado sem ela, ou a
            # primeira vez): o "ja copiei" de antes era de outra pasta.
            copiadas.clear()
        candidatos = _candidatos(raiz, arquivos, pasta_info, feito["avisos"])
        _instalar(raiz, candidatos, pasta_info, feito)
        _instalar_pastas(raiz, feito)
        _copias_extras(raiz, feito)
        _copiar_para_as_prateleiras(raiz, candidatos, copiadas, feito)
        if feito["instaladas"] or feito["copiadas"]:
            # O que acabou de chegar (em retroarch\system e na prateleira)
            # entra na conta dos LEIA -- e na lista dos ja lidos, para a
            # proxima abertura nao ter nada novo para ler nem para gravar.
            candidatos = _candidatos(raiz, arquivos, pasta_info, [])
        conferidos["versao"] = 2
        if json.dumps(conferidos, sort_keys=True) != antes:
            _gravar_json(arquivo_conferidos, conferidos)
        itens = situacao(raiz, pasta_info)
        feito["leias"] = escrever_leias(raiz, itens, candidatos)
        feito["itens"] = itens
        feito["resumo"] = resumo(itens)
        return feito
