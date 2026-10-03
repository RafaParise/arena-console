# -*- coding: utf-8 -*-
"""
ARENA - Indexador de jogos
===========================
Varre a pasta 'jogos', descobre a qual plataforma cada arquivo pertence
e grava o resultado em 'dados/manifesto.json'.

Otimizacao importante: antes de varrer, o indexador calcula uma assinatura
das pastas (caminho + data de modificacao). Se nada mudou desde a ultima vez,
ele reaproveita o catalogo salvo em vez de ler o disco de novo. Isso importa
muito quando o ARENA roda de pen drive, onde ler pasta e lento.

Modulo da turma do 2o ano:
  - manipulacao de strings: limpar e formatar o titulo do jogo
  - arquivos com open() e context manager: ler pastas e gravar JSON

So biblioteca padrao do Python. Nenhum 'pip install'.
"""

import hashlib
import json
import os
import re
import threading
import unicodedata

import arrumar
import bios
import como_colocar
import graficos
import identificador
import jogadores
import nomes_arcade
import integridade
import zipfile

# ---------------------------------------------------------------------------
# BLOCO 1 - Onde estamos no disco
# ---------------------------------------------------------------------------
# __file__ e o caminho deste proprio arquivo. Subindo um nivel chegamos na
# raiz do ARENA. Nada aqui depende da letra do drive (E:, G:, F:), que muda
# de computador para computador.

PASTA_SERVIDOR = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(PASTA_SERVIDOR)

PASTA_JOGOS = os.path.join(RAIZ, "jogos")
PASTA_DADOS = os.path.join(RAIZ, "dados")
ARQUIVO_CONSOLES = os.path.join(PASTA_SERVIDOR, "consoles.json")
ARQUIVO_MANIFESTO = os.path.join(PASTA_DADOS, "manifesto.json")
ARQUIVO_MANUAIS = os.path.join(PASTA_DADOS, "consoles_manuais.json")

# Subpastas de jogos e o rotulo que cada uma recebe na tela.
ORIGENS = {
    "livres": "Acervo livre",
    "turma": "Feito pela turma",
    "pessoais": "Meus jogos",
}

# Arquivos que nunca sao jogos, mesmo com extensao parecida.
IGNORAR = {"leia.txt", "leia-me.txt", "_console.txt", "readme.txt", "licenca.txt",
           "license.txt", "thumbs.db", "desktop.ini", ".gitkeep"}

# BIOS de fliperama que o aluno costuma deixar junto dos jogos (neogeo.zip,
# neogeo.mame.zip, pgm.zip...): nao e jogo, nao entra na lista. Os nomes sao
# os dos romsets de BIOS do MAME/FBNeo (e o qsound.zip, som do CPS2).
RE_BIOS_NA_PASTA = re.compile(
    r"^(neogeo|pgm|naomi|naomi2|naomigd|awbios|stvbios|skns|cpzn1|cpzn2|hng64|"
    r"nss|playch10|megatech|megaplay|decocass|konamigv|taitogn|isgsm|qsound)"
    r"([ ._-].*)?\.(zip|7z)$", re.I)


# ---------------------------------------------------------------------------
# Jogo de varios discos (ou disquetes) vira um jogo so
# ---------------------------------------------------------------------------
# "Final Fantasy VII (USA) (Disc 1).chd", "(Disc 2)", "(Disc 3)" apareciam
# como tres jogos, e trocar de disco no meio exigia sair. Agora: um cartao
# so, e na hora de abrir o ARENA monta uma lista .m3u (o jeito do RetroArch
# de trocar de disco sem sair: menu -> Controle de disco). So nos consoles
# cujo nucleo aceita .m3u (conferido no .info do nucleo); nos outros, cada
# disco continua sendo um jogo.
# "Disk1", "Disc 2", "(Disco 1 de 3)", "CD 2"; "CD32" e "Sonic CD" nao contam.
RE_DISCO = re.compile(
    r"^(?P<base>.*?)[\s_\-]*[\(\[]?\s*(?:(?:disk|disc|disco)[\s_\-]*|cd[\s_\-]+)(?P<n>[1-9]|1[0-9])"
    r"(?!\d)(?:\s*(?:of|de)\s*\d{1,2})?\s*[\)\]]?(?P<resto>.*)$", re.I)
_m3u_por_nucleo = {}


def nucleo_aceita_m3u(core):
    """O nucleo diz, no proprio .info, que abre lista de discos (.m3u)?"""
    core = (core or "").lower()
    if core not in _m3u_por_nucleo:
        info = os.path.join(RAIZ, "retroarch", "info", os.path.splitext(core)[0] + ".info")
        aceita = False
        try:
            # "with": o "break" no meio deixava o arquivo aberto (achado em
            # 02/10/2026 pelo aviso do Python nos testes).
            with open(info, encoding="utf-8", errors="replace") as arquivo:
                for linha in arquivo:
                    if linha.strip().startswith("supported_extensions"):
                        lista = linha.split("=", 1)[1].strip().strip('"').lower().split("|")
                        aceita = "m3u" in lista
                        break
        except OSError:
            pass
        _m3u_por_nucleo[core] = aceita
    return _m3u_por_nucleo[core]


def agrupar_discos(itens, por_id):
    """Junta, NA MESMA PASTA, os discos do mesmo jogo num cartao so (o do
    menor disco, que passa a ter "discos": a lista). Devolve a lista nova."""
    grupos = {}
    for item in itens:
        plataforma = por_id.get(item["plataforma"]) or {}
        if plataforma.get("externo") or not nucleo_aceita_m3u(plataforma.get("core")):
            continue
        base = os.path.splitext(os.path.basename(item["arquivo"]))[0]
        m = RE_DISCO.match(base)
        if not m:
            continue
        # "Disc 1.chd" dentro da pasta do jogo: nome vazio, o titulo ja veio
        # da pasta (titulo_do_jogo) e continua valendo.
        nome = (m.group("base").strip(" _-.") + " " + m.group("resto").strip()).strip()
        chave = (item["plataforma"], nome.lower(), os.path.splitext(item["arquivo"])[1].lower())
        grupos.setdefault(chave, []).append((int(m.group("n")), item, nome))
    sai = set()
    for membros in grupos.values():
        membros.sort(key=lambda x: x[0])
        numeros = [n for n, _i, _nome in membros]
        _n, primeiro, nome = membros[0]
        titulo = limpar_titulo(nome + ".x") if nome else primeiro["titulo"]
        avisos = primeiro.setdefault("avisos", [])
        if len(membros) >= 2:
            primeiro["discos"] = [i["arquivo"] for _n, i, _m in membros]
            primeiro["titulo"] = titulo
            primeiro["ordenacao"] = chave_ordenacao(titulo)
            primeiro["tamanho_mb"] = round(sum(i.get("tamanho_mb", 0) for _n, i, _m in membros), 1)
            for _n, outro, _m in membros[1:]:
                sai.add(id(outro))
        faltam = [n for n in range(1, max(numeros) + 1) if n not in numeros]
        if faltam:
            avisos.append({"texto": "Falta o disco %s deste jogo na pasta. %s" % (
                ", ".join(str(n) for n in faltam),
                "O jogo começa pelo disco 1." if 1 in faltam else
                "Na hora de trocar de disco, ele não vai estar lá.")})
    return [i for i in itens if id(i) not in sai]


def aviso_de_nome_de_fliperama(titulo, extensao, nucleo_arcade):
    """Fliperama com nome que o emulador nao conhece. Quase sempre e' o nome
    do titulo no lugar do nome curto do romset; quando o titulo esta no
    banco do RetroArch, o aviso ja diz o nome certo para renomear."""
    emulador = "MAME" if nucleo_arcade == "mame" else "FBNeo"
    certo, exato = nomes_arcade.romset_pelo_titulo(titulo, nucleo_arcade)
    if certo:
        return {"texto": "O %s só reconhece o jogo de fliperama pelo nome curto do romset: "
                         "renomeie este arquivo para %s%s%s." % (
                             emulador, certo, extensao,
                             "" if exato else " (o mais provável pelo título; confira)")}
    return {"texto": "O %s não conhece este nome de arquivo. Jogo de fliperama precisa do nome "
                     "curto do romset (como mslugx.zip ou kof97.zip), e da mesma versão do "
                     "emulador." % emulador}


def discos_de_fliperama_zipados(pasta_atual, arquivos):
    """{romset: arquivo.zip} dos .zip que so tem .chd dentro (kinst-chd.zip
    -> {"kinst": "kinst-chd.zip"}). So abre zip com "chd" no nome: ler o
    indice de um zip e' rapido, mas nao precisa abrir todos."""
    achados = {}
    for nome in arquivos:
        minusculo = nome.lower()
        if not minusculo.endswith(".zip") or "chd" not in minusculo:
            continue
        try:
            with zipfile.ZipFile(os.path.join(pasta_atual, nome)) as compactado:
                dentro = [n for n in compactado.namelist() if not n.endswith("/")]
        except (OSError, zipfile.BadZipFile, ValueError):
            continue
        if dentro and all(n.lower().endswith(".chd") for n in dentro):
            romset = os.path.splitext(os.path.basename(dentro[0]))[0].lower()
            achados[romset] = nome
    return achados


def parece_neo_geo(nomes):
    """Os arquivos de um cartucho de Neo Geo: programa (p1), som (m1) e
    grafico (c1). Vale para o romset do MAME (265-p1.p1) e para copia feita
    para outro emulador (kof2k2_p1.rom)."""
    base = [os.path.basename(n).lower() for n in nomes]

    def tem(parte):
        return any(re.search(r"(^|[-_.])%s([._]|$)" % parte, n) for n in base)
    return tem("p1") and tem("m1") and tem("c1")


def aviso_da_bios_neo_geo(pasta, nucleo):
    """Jogo de Neo Geo precisa da BIOS neogeo.zip. O MAME so procura na pasta
    do jogo e so por esse nome (provado em 02/10/2026: com neogeo.mame.zip ao
    lado, "000-lo.lo NOT FOUND"; renomeado para neogeo.zip, achou). O FBNeo
    tambem acha em retroarch\\system. None se esta tudo certo."""
    try:
        nomes = os.listdir(pasta)
    except OSError:
        return None
    if any(n.lower() == "neogeo.zip" for n in nomes):
        return None
    if nucleo == "fbneo" and os.path.isfile(os.path.join(RAIZ, "retroarch", "system", "neogeo.zip")):
        return None
    errado = next((n for n in sorted(nomes) if re.match(r"^neogeo[ ._-].+\.(zip|7z)$", n, re.I)), None)
    if errado:
        aviso = {"texto": "A BIOS do Neo Geo desta pasta está como %s, e o emulador só procura "
                          "neogeo.zip. Renomeie para neogeo.zip (na mesma pasta)." % errado}
        if errado.lower().endswith(".zip"):
            aviso["arrumar"] = arrumar.conserto("bios_neogeo_nome", atual=errado)
        return aviso
    if nucleo == "mame":
        # Com a BIOS na pasta BIOS do ARENA, o botao Arrumar poe uma copia aqui.
        aviso = {"texto": "Jogo de Neo Geo: o MAME precisa da BIOS neogeo.zip na mesma pasta do "
                          "jogo (ela não aparece na lista)."}
        if neogeo_do_arena():
            aviso["arrumar"] = arrumar.conserto("bios_neogeo")
        return aviso
    return None


def tipo_de_console(id_plataforma, plataforma):
    """'cartucho', 'disco', 'fliperama', 'externo'... (servidor\\como_colocar.py):
    decide se o console abre jogo de dentro de .zip."""
    tipo = (como_colocar.CONSOLES.get(id_plataforma) or {}).get("tipo")
    return tipo or ("externo" if (plataforma or {}).get("externo") else "cartucho")


def neogeo_do_arena():
    """O neogeo.zip que o ARENA ja tem (retroarch\\system ou a pasta BIOS), ou None."""
    for caminho in (os.path.join(RAIZ, "retroarch", "system", "neogeo.zip"),
                    os.path.join(RAIZ, "BIOS", "Neo Geo", "neogeo.zip")):
        if os.path.isfile(caminho):
            return caminho
    return None


def avisos_do_romset(caminho, romset, discos_zipados, nucleo=""):
    """O que impede um romset de fliperama de abrir, que da para ver sem
    abrir o jogo. Cada aviso diz o que fazer."""
    avisos = []
    if romset in discos_zipados:
        avisos.append({"texto": (
            "O disco deste jogo (%s.chd) está dentro de %s, e o emulador não lê "
            "disco de dentro de .zip. Extraia o %s.chd para a pasta %s\\%s\\ "
            "(ao lado do %s)." % (romset, discos_zipados[romset], romset,
                                  os.path.basename(os.path.dirname(caminho)), romset,
                                  os.path.basename(caminho))),
            "arrumar": arrumar.conserto("extrair_disco", disco=romset + ".chd", zip=discos_zipados[romset])})
    if caminho.lower().endswith(".zip"):
        try:
            with zipfile.ZipFile(caminho) as compactado:
                dentro = [n for n in compactado.namelist() if not n.endswith("/")]
        except (OSError, zipfile.BadZipFile, ValueError):
            return avisos + [{"texto": "Este .zip está corrompido (não deu para ler o que tem dentro)."}]
        # Leia-me, imagem e atalho que vem junto nao sao parte do jogo
        # (o kof2002.zip da pasta tem um readme.html solto e os 16 arquivos
        # do jogo dentro da pasta "king"). Quem confere e' o arrumar.py --
        # o mesmo que refaz o zip no botao Arrumar.
        pasta_interna = arrumar.pasta_dentro_do_zip(caminho)
        if pasta_interna:
            avisos.append({"texto": (
                "Os arquivos deste jogo estão dentro da pasta \"%s\" no .zip, e o "
                "emulador procura na raiz do .zip. Compacte de novo só os arquivos, "
                "sem a pasta." % pasta_interna),
                "arrumar": arrumar.conserto("pasta_dentro_do_zip", zip=os.path.basename(caminho))})
        if dentro and parece_neo_geo(dentro):
            aviso = aviso_da_bios_neo_geo(os.path.dirname(caminho), nucleo)
            if aviso:
                avisos.append(aviso)
    # O zip dentro da pasta do proprio disco (Arcade\kinst\kinst.zip, ao lado
    # do kinst.chd): provado com o MAME em 02/10/2026 -- assim ele nao abre
    # ("unknown option: kinst"); com Arcade\kinst.zip + Arcade\kinst\kinst.chd,
    # abre e desenha.
    pasta = os.path.dirname(caminho)
    nome_zip = os.path.basename(caminho)
    if arrumar.zip_na_pasta_do_disco(caminho):
        avisos.append({"texto": (
            "O %s está dentro da pasta %s, junto do disco, e assim o emulador não abre. "
            "Tire o %s dessa pasta e ponha na pasta de cima (%s): dentro da pasta %s fica "
            "só o disco (.chd)." % (nome_zip, os.path.basename(pasta), nome_zip,
                                    os.path.basename(os.path.dirname(pasta)), os.path.basename(pasta))),
            "arrumar": arrumar.conserto("zip_na_pasta_do_disco", zip=nome_zip, pasta=os.path.basename(pasta))})
    # O disco solto AO LADO do zip (Arcade\kinst.chd + Arcade\kinst.zip): o
    # MAME procura o disco numa pasta com o nome do zip.
    solto = arrumar.disco_solto(caminho)
    if solto:
        disco = os.path.basename(solto[0])
        avisos.append({"texto": (
            "O disco deste jogo (%s) está solto, ao lado do %s, e o emulador só procura o disco "
            "dentro de uma pasta com o nome do zip: %s\\%s." % (disco, nome_zip, os.path.basename(pasta),
                                                               os.path.basename(solto[1]))),
            "arrumar": arrumar.conserto("disco_solto", disco=disco, pasta=os.path.basename(solto[1]))})
    return avisos


def chd_de_fliperama(pasta_atual, console_da_pasta=None, por_id=None):
    """True se a pasta e' a do disco (.chd) de um jogo de fliperama: o guia
    do libretro manda por o CHD numa subpasta com o nome do romset, ao lado
    do .zip (ex.: Arcade\\kinst.zip + Arcade\\kinst\\kinst.chd). Esse .chd
    nao e' um jogo sozinho -- e' parte do kinst.zip.

    So nas pastas de fliperama (achado de 03/10/2026, testando o "Arrumar"):
    o jogo de PS1 descompactado em PS1\\Crash, ao lado do PS1\\Crash.zip,
    sumia da lista -- a pasta parecia a do disco de um fliperama."""
    if por_id is not None and tipo_de_console(console_da_pasta, por_id.get(console_da_pasta)) != "fliperama":
        return False
    nome = os.path.basename(pasta_atual)
    pai = os.path.dirname(pasta_atual)
    return any(os.path.isfile(os.path.join(pai, nome + ext)) for ext in (".zip", ".7z"))

# Jogo de CD em varios arquivos: o indice (.cue/.gdi) aponta as trilhas.
# So o indice entra na lista; as trilhas ficam escondidas. E, se o mesmo
# jogo esta em mais de um formato na pasta, fica um so -- o primeiro
# desta ordem (arquivo unico primeiro). Achado 25/09/2026: o Saturn
# Bomberman aparecia 31 vezes (30 trilhas + o .cue), o CTR 3 (.bin, .cue,
# .chd).
PREFERENCIA_DISCO = (".chd", ".gdi", ".cue", ".iso", ".bin")

# Nome de arquivo que nao diz qual e o jogo ("disc.gdi", "track01.bin",
# "Disc 2.chd", "CD1.cue" -- os dois ultimos, comuns em jogo de varios
# discos, entraram em 01/10/2026): o titulo vem da pasta.
RE_NOME_GENERICO = re.compile(r"^(dis[ck]|disco|game|jogo|track|cd) ?\d{0,2}$", re.I)


def trilhas_dos_indices(pasta, arquivos):
    """Nomes (minusculos) dos arquivos que algum .cue/.gdi da pasta usa."""
    trilhas = set()
    for nome in arquivos:
        extensao = os.path.splitext(nome)[1].lower()
        if extensao not in (".cue", ".gdi"):
            continue
        try:
            with open(os.path.join(pasta, nome), "r", encoding="utf-8",
                      errors="replace") as arquivo:
                texto = arquivo.read(65536)
        except OSError:
            continue
        if extensao == ".cue":
            for achado in re.finditer(r'^\s*FILE\s+"?(.+?)"?\s+\S+\s*$', texto, re.M | re.I):
                trilhas.add(os.path.basename(achado.group(1)).lower())
        else:
            # .gdi: "numero inicio tipo tamanho ARQUIVO deslocamento"; o nome
            # pode vir entre aspas quando tem espaco.
            for linha in texto.splitlines()[1:]:
                achado = re.match(r'^\s*\d+\s+\d+\s+\d+\s+\d+\s+("[^"]+"|\S+)', linha)
                if achado:
                    trilhas.add(os.path.basename(achado.group(1).strip('"')).lower())
    return trilhas


def repetido_em_outro_formato(nome, arquivos_por_base):
    """True se o mesmo jogo (mesmo nome) esta na pasta num formato melhor."""
    base, extensao = os.path.splitext(nome)
    extensao = extensao.lower()
    if extensao not in PREFERENCIA_DISCO:
        return False
    irmas = arquivos_por_base.get(base.lower(), set())
    melhores = PREFERENCIA_DISCO[:PREFERENCIA_DISCO.index(extensao)]
    return any(melhor in irmas for melhor in melhores)


def titulo_do_jogo(nome_arquivo, pasta_atual):
    """Titulo pelo nome do arquivo; se o nome for generico, pela pasta."""
    titulo = limpar_titulo(nome_arquivo)
    if RE_NOME_GENERICO.match(titulo):
        # O ".pasta" protege nome de pasta com ponto ("v1.2)"), que o
        # limpar_titulo cortaria achando que e extensao.
        titulo = limpar_titulo(os.path.basename(pasta_atual) + ".pasta")
    return titulo


# ---------------------------------------------------------------------------
# BLOCO 2 - Tratamento de strings
# ---------------------------------------------------------------------------

# Expressoes compiladas uma vez so. Compilar dentro do laco deixaria a
# varredura varias vezes mais lenta em pastas grandes.
RE_PARENTESES = re.compile(r"\([^)]*\)")
RE_COLCHETES = re.compile(r"\[[^\]]*\]")
RE_ESPACOS = re.compile(r"\s+")

LIGACOES = {"de", "da", "do", "dos", "das", "e", "the", "of", "in", "a", "o"}


def limpar_titulo(nome_arquivo):
    """Transforma o nome cru do arquivo em um titulo legivel.

    Exemplo:
        'super_jogo_(Brazil)_[!].sfc'  ->  'Super Jogo'

    Passo a passo:
      1. separa o nome da extensao
      2. remove o que estiver entre parenteses ou colchetes
      3. troca '_', '.' e '-' por espaco
      4. junta espacos repetidos e limpa as pontas
      5. coloca a inicial de cada palavra em maiuscula
    """
    titulo = os.path.splitext(nome_arquivo)[0]

    titulo = RE_PARENTESES.sub(" ", titulo)
    titulo = RE_COLCHETES.sub(" ", titulo)
    titulo = titulo.replace("_", " ").replace(".", " ").replace("-", " ")
    titulo = RE_ESPACOS.sub(" ", titulo).strip()

    if not titulo:
        return "Sem titulo"

    palavras = []
    for posicao, palavra in enumerate(titulo.split(" ")):
        if posicao > 0 and palavra.lower() in LIGACOES:
            palavras.append(palavra.lower())
        else:
            palavras.append(palavra[:1].upper() + palavra[1:])
    return " ".join(palavras)


def chave_ordenacao(texto):
    """Versao sem acento e em minusculas, usada so para ordenar a lista.

    'Acido' e 'Ácido' precisam ficar lado a lado na tela.
    """
    sem_acento = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return sem_acento.lower()


# ---------------------------------------------------------------------------
# BLOCO 3 - Leitura do catalogo de plataformas
# ---------------------------------------------------------------------------

def carregar_plataformas():
    """Le o catalogo de consoles e devolve dois dicionarios prontos para uso.

    - por_id:       id da plataforma -> dados completos
    - por_extensao: '.sfc' -> lista de ids que aceitam essa extensao
    """
    # 'with' fecha o arquivo sozinho, mesmo se der erro no meio da leitura.
    with open(ARQUIVO_CONSOLES, "r", encoding="utf-8") as arquivo:
        catalogo = json.load(arquivo)

    por_id = {}
    por_extensao = {}

    for plataforma in catalogo["plataformas"]:
        por_id[plataforma["id"]] = plataforma
        for extensao in plataforma["extensoes"]:
            por_extensao.setdefault(extensao, []).append(plataforma["id"])

    # Ordem de preferencia para extensao que serve a varias plataformas.
    # Sem isso valia a ordem do catalogo, e como o Sega CD vinha primeiro,
    # TODO arquivo .iso, .chd e .cue virava Sega CD - inclusive jogo de
    # PlayStation 2 de 3 GB.
    preferencia = catalogo.get("preferencia", {})
    for extensao, ordem in preferencia.items():
        if extensao not in por_extensao:
            continue
        atuais = por_extensao[extensao]
        por_extensao[extensao] = ([p for p in ordem if p in atuais] +
                                  [p for p in atuais if p not in ordem])

    return por_id, por_extensao


# ---------------------------------------------------------------------------
# BLOCO 4 - Assinatura das pastas (evita varredura desnecessaria)
# ---------------------------------------------------------------------------

def arquivo_de_jogadores():
    """O dados\\jogadores.txt do professor, na MESMA pasta de dados do indice
    (calculado na hora: teste que troca PASTA_DADOS nunca toca no real)."""
    return os.path.join(PASTA_DADOS, jogadores.NOME)


# Muda quando o indexador passa a montar a lista de outro jeito. Achado de
# 01/10/2026: a assinatura so olhava as pastas -- correcao nova do indexador
# (ex.: o jogo de CD em trilhas virar um jogo so) nao valia num ARENA que ja
# tinha a lista salva, ate alguma pasta mudar. 2 = nomes de fliperama pelos
# bancos do RetroArch + avisos do jogo.
VERSAO_INDICE = 8     # 8 = jogadores dos jogos testados vem com o programa


def assinatura_das_pastas():
    """Resume o estado atual das pastas de jogos em um texto curto.

    Se nenhuma pasta foi criada, apagada ou teve arquivo alterado, a
    assinatura continua a mesma e a varredura inteira pode ser pulada.
    Tambem entram a versao do indexador e o consoles.json (extensao nova,
    console novo): mudou um dos dois, a lista e' refeita.
    """
    partes = ["indice|%d" % VERSAO_INDICE]
    try:
        partes.append("consoles|%d" % os.path.getmtime(ARQUIVO_CONSOLES))
    except OSError:
        pass
    for origem in ORIGENS:
        caminho = os.path.join(PASTA_JOGOS, origem)
        if not os.path.isdir(caminho):
            continue
        for pasta_atual, subpastas, _arquivos in os.walk(caminho):
            subpastas.sort()
            try:
                partes.append("%s|%d" % (pasta_atual, os.path.getmtime(pasta_atual)))
            except OSError:
                continue
    # O arquivo de jogadores do professor e o mapa do multitap tambem mudam
    # a lista (numero de jogadores de cada jogo).
    partes.append(jogadores.assinatura(arquivo_de_jogadores()))
    try:
        partes.append("mapa|%d" % os.path.getmtime(graficos.ARQUIVO_MAPA_MULTITAP))
    except OSError:
        pass
    texto = "\n".join(sorted(partes))
    return hashlib.md5(texto.encode("utf-8")).hexdigest()


def ler_manifesto_salvo():
    """A lista salva, ou None. So vale se tiver o formato certo: um
    manifesto.json que virou [] ou "texto" (pen drive arrancado, mexido a
    mao) derrubava a lista de jogos inteira (achado de 01/10/2026)."""
    try:
        with open(ARQUIVO_MANIFESTO, "r", encoding="utf-8") as arquivo:
            salvo = json.load(arquivo)
    except (OSError, ValueError):
        return None
    if not isinstance(salvo, dict) or not isinstance(salvo.get("jogos"), list):
        return None
    if not all(isinstance(j, dict) for j in salvo["jogos"]):
        return None
    return salvo


# ---------------------------------------------------------------------------
# BLOCO 5 - Varredura
# ---------------------------------------------------------------------------

ARQUIVO_MARCACAO = "_console.txt"

# Onde procurar a capa de um jogo. Tudo local: a escola trabalha offline, e
# baixar imagem da internet no meio da aula nao e opcao.
CAPAS_EXTENSOES = (".png", ".jpg", ".jpeg", ".webp")
PASTA_CAPAS = "capas"


# Capa com nome generico que vem dentro da pasta de um jogo (pacote de
# jogo de PS3 e Xbox 360, por exemplo: "Gears Of War - Judgment\Cover.jpg").
CAPAS_DA_PASTA = ("cover", "folder", "boxart", "capa", "front")


def capas_do_jogo(caminho_absoluto, pasta_atual, titulo, nome_banco=None, sozinho_na_pasta=False,
                  outros_titulos=()):
    """Procura a arte do jogo em quatro lugares, do mais especifico ao geral.

    1. Um arquivo com o MESMO nome do jogo, na mesma pasta:
         Mario Kart 64.z64  ->  Mario Kart 64.png
    2. Uma subpasta 'capas' ao lado:
         capas/Mario Kart 64.png
    3. Se o jogo esta SOZINHO numa pasta dele: Cover.jpg, folder.png...
       (02/10/2026: o Gears of War Judgment veio assim e ficava sem capa).
    4. As miniaturas que o proprio RetroArch baixa, se existirem.

    Devolve caminhos que a tela pede ao servidor, nunca ao disco direto.
    """
    base = os.path.splitext(os.path.basename(caminho_absoluto))[0]
    achados = []

    for onde in (pasta_atual, os.path.join(pasta_atual, PASTA_CAPAS)):
        for extensao in CAPAS_EXTENSOES:
            candidato = os.path.join(onde, base + extensao)
            if os.path.isfile(candidato):
                achados.append(candidato)
    if sozinho_na_pasta and not achados:
        try:
            nomes = {nome.casefold(): nome for nome in os.listdir(pasta_atual)}
        except OSError:
            nomes = {}
        for generico in CAPAS_DA_PASTA:
            nome = next((nomes[generico + e] for e in CAPAS_EXTENSOES if generico + e in nomes), None)
            if nome:
                achados.append(os.path.join(pasta_atual, nome))
                break

    # Miniatura do RetroArch: thumbnails/<sistema>/Named_Boxarts/<titulo>.png
    # Fliperama: o RetroArch nomeia pelo nome COMPLETO do banco ("Metal Slug
    # X - Super Vehicle-001 (NGM-2500)(NGH-2500)"), com & * / : ` < > ? \ |
    # " trocados por _ -- a mesma regra do capas_online.
    # O titulo tambem com os caracteres trocados: a busca de capa grava
    # "Sonic _ Knuckles + Sonic the Hedgehog 2.png" (achado de 02/10/2026: a
    # capa estava baixada e a lista nao achava).
    nomes = [titulo, re.sub(r'[&*/:`<>?\\|"]', "_", titulo)]
    # O titulo de antes (do nome do arquivo), quando o .nfo do GameBase deu
    # um melhor: a capa ja baixada com o nome antigo continua valendo.
    nomes += [n for n in outros_titulos if n]
    if nome_banco:
        nomes.append(re.sub(r'[&*/:`<>?\\|"]', "_", nome_banco))
    miniaturas = os.path.join(RAIZ, "retroarch", "thumbnails")
    if os.path.isdir(miniaturas):
        # .jpg tambem: a capa oficial do Xbox 360 vem assim (02/10/2026).
        for sistema in os.listdir(miniaturas):
            arte = next((os.path.join(miniaturas, sistema, "Named_Boxarts", n + extensao)
                         for n in nomes for extensao in (".png", ".jpg")
                         if os.path.isfile(os.path.join(miniaturas, sistema, "Named_Boxarts", n + extensao))),
                        None)
            if arte:
                achados.append(arte)
                break

    return [os.path.relpath(a, RAIZ).replace("\\", "/") for a in achados[:3]]


RE_NOME_DO_GAMEBASE = re.compile(r"^Name:[ \t]*(\S.*?)\s*$", re.M)


def nome_do_gamebase(pasta_atual, arquivos):
    """O nome do jogo no VERSION.NFO da colecao GameBase (C64, Amiga,
    Spectrum...): "INTKARAT.D64" e' o "International Karate" (achado de
    02/10/2026: com o nome cortado em 8 letras, a capa nunca era achada).
    So o .nfo que e' mesmo do GameBase (tem a linha "GB-Version:")."""
    for nome in arquivos:
        if not nome.lower().endswith(".nfo"):
            continue
        try:
            with open(os.path.join(pasta_atual, nome), "rb") as arquivo:
                texto = arquivo.read(8192).decode("latin-1")
        except OSError:
            continue
        achado = RE_NOME_DO_GAMEBASE.search(texto)
        if "GB-Version:" in texto and achado:
            return achado.group(1).strip()[:80]
    return None


def sozinho_na_pasta(pasta_atual, caminho_pasta, nome_arquivo, arquivos):
    """O jogo esta numa pasta SO DELE (abaixo da pasta do console, sem outro
    arquivo do mesmo tipo)? So ai a Cover.jpg generica e' dele."""
    if os.path.normcase(os.path.abspath(pasta_atual)) == os.path.normcase(os.path.abspath(caminho_pasta)):
        return False
    extensao = os.path.splitext(nome_arquivo)[1].lower()
    return sum(1 for nome in arquivos if nome.lower().endswith(extensao)) == 1


def ler_manuais():
    """Consoles que o aluno corrigiu na tela, jogo por jogo.

    Tem prioridade sobre tudo: se voce disse que aquele arquivo e PSP, e
    PSP, e o ARENA nao discute mais. Fica guardado, entao vale para sempre
    e viaja junto com a pasta.
    """
    try:
        with open(ARQUIVO_MANUAIS, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
        return dados if isinstance(dados, dict) else {}
    except (OSError, ValueError):
        return {}


def gravar_manual(jogo_id, plataforma):
    """Guarda (ou apaga, com plataforma vazia) a correcao de um jogo."""
    manuais = ler_manuais()
    if plataforma:
        manuais[jogo_id] = plataforma
    else:
        manuais.pop(jogo_id, None)
    os.makedirs(PASTA_DADOS, exist_ok=True)
    gravar_atomico(ARQUIVO_MANUAIS,
                   json.dumps(manuais, ensure_ascii=False, indent=1))
    return manuais


def ler_marcacao(pasta, por_id):
    """Le o arquivo _console.txt, se existir na pasta.

    E a palavra final: se o aluno escreveu 'ps2' nesse arquivo, tudo o que
    estiver na pasta e PlayStation 2, sem discussao. Serve para o caso raro
    em que os outros sinais erram.
    """
    try:
        caminho = os.path.join(pasta, ARQUIVO_MARCACAO)
        with open(caminho, "r", encoding="utf-8", errors="replace") as arquivo:
            escrito = arquivo.read().strip().lower()
    except OSError:
        return None
    return escrito if escrito in por_id else None


def plataforma_pelo_nome(texto, por_id, candidatos):
    """Procura o apelido de alguma plataforma dentro do nome da pasta.

    Compara apelido por apelido, do mais longo para o mais curto, para
    'playstation 2' vencer 'playstation' quando os dois servem.
    """
    texto = texto.lower()
    melhor, tamanho = None, 0
    for identificador in candidatos:
        for apelido in por_id[identificador].get("apelidos", [identificador]):
            if apelido in texto and len(apelido) > tamanho:
                melhor, tamanho = identificador, len(apelido)
    return melhor


SEM_PASTA = "indefinido"


def escolher_plataforma(candidatos, por_id, nome_pasta, marcado, tamanho_mb,
                        caminho_absoluto=None):
    """Decide de qual console e o arquivo. A PASTA manda.

    Quando a extensao serve a um console so (.nes, .sfc, .gba...), nao ha
    o que decidir. Quando serve a varios (.iso, .chd, .cue, .zip), quem
    decide e a pasta em que o arquivo esta - do mesmo jeito que o
    RetroArch faz.

    Por que parei de adivinhar: o Half-Life de PlayStation 2 foi lancado
    em CD, com a mesma estrutura de um jogo de PlayStation 1. Nenhuma
    pista de tamanho ou de cabecalho separa os dois. Chutar so gerava jogo
    abrindo no emulador errado, e o aluno sem entender por que.

    Sem pasta que diga o console, o jogo fica marcado como indefinido e
    aparece no topo da lista, esperando um clique.
    """
    if len(candidatos) == 1:
        return candidatos[0], None

    if marcado and marcado in candidatos:
        return marcado, None

    # A pasta manda, e manda mesmo. Se o arquivo esta dentro da pasta de
    # um console, e daquele console - ainda que aquela extensao nao esteja
    # cadastrada nele. Voce colocou ali de proposito.
    pela_pasta = plataforma_pelo_nome(nome_pasta, por_id, candidatos)
    if not pela_pasta:
        pela_pasta = plataforma_pelo_nome(nome_pasta, por_id, list(por_id))
    if pela_pasta:
        return pela_pasta, None

    # Sem pasta: nao decide. Mas deixa uma sugestao pronta, para o aluno
    # so confirmar em vez de escolher entre 47 consoles.
    sugestao = None
    if caminho_absoluto:
        try:
            sugestao = identificador.identificar(caminho_absoluto, candidatos, palpite=True)
        except Exception:
            sugestao = None
    if not sugestao and tamanho_mb:
        cabem = [c for c in candidatos
                 if tamanho_mb <= por_id[c].get("tamanho_max_mb", 10 ** 6)]
        sugestao = (cabem or candidatos)[0]

    return SEM_PASTA, sugestao


def varrer_pasta(caminho_pasta, origem, por_extensao, por_id, manuais=None,
                 regras=None):
    """Percorre uma pasta e devolve a lista de jogos encontrados.

    os.walk entra tambem nas subpastas, entao o aluno pode organizar os
    arquivos em pastas por console que continua funcionando.
    """
    encontrados = []
    mapa_multitap = graficos.carregar_mapa_multitap()

    if not os.path.isdir(caminho_pasta):
        return encontrados

    for pasta_atual, subpastas, arquivos in os.walk(caminho_pasta):
        subpastas.sort()
        # O caminho inteiro conta, nao so a ultima pasta: quem organiza em
        # 'Sony\PlayStation 2\Corrida' tambem e atendido.
        caminho_relativo_pasta = os.path.relpath(pasta_atual, caminho_pasta)
        marcado = ler_marcacao(pasta_atual, por_id)
        console_da_pasta = marcado or plataforma_pelo_nome(caminho_relativo_pasta, por_id, list(por_id))
        if chd_de_fliperama(pasta_atual, console_da_pasta, por_id):
            continue   # disco de um romset de fliperama, nao um jogo
        trilhas = trilhas_dos_indices(pasta_atual, arquivos)
        inicio_da_pasta = len(encontrados)
        # Disco (.chd) de fliperama zipado: kinst-chd.zip com o kinst.chd
        # dentro. Nao e' um jogo -- e o MAME nao le .chd de dentro de .zip.
        # Sai da lista e vira aviso no jogo dele (o kinst.zip).
        discos_zipados = discos_de_fliperama_zipados(pasta_atual, arquivos)
        arquivos_por_base = {}
        for nome in arquivos:
            base, extensao = os.path.splitext(nome)
            arquivos_por_base.setdefault(base.lower(), set()).add(extensao.lower())

        for nome_arquivo in arquivos:

            if nome_arquivo.lower() in IGNORAR or RE_BIOS_NA_PASTA.match(nome_arquivo):
                continue
            if nome_arquivo.lower() in trilhas:
                continue   # trilha de um .cue/.gdi desta pasta
            if nome_arquivo in discos_zipados.values():
                continue   # disco de fliperama dentro de zip: vira aviso
            if repetido_em_outro_formato(nome_arquivo, arquivos_por_base):
                continue

            extensao = os.path.splitext(nome_arquivo)[1].lower()
            candidatos = por_extensao.get(extensao)
            if not candidatos:
                continue

            caminho_absoluto = os.path.join(pasta_atual, nome_arquivo)
            try:
                tamanho = os.path.getsize(caminho_absoluto)
            except OSError:
                continue
            tamanho_mb = tamanho / (1024.0 * 1024.0)

            caminho_relativo = os.path.relpath(caminho_absoluto, RAIZ)
            identificacao = caminho_relativo.replace("\\", "/").lower()

            # Correcao feita na tela vence tudo.
            sugestao = None
            corrigido = (manuais or {}).get(identificacao)
            if corrigido in por_id:
                id_plataforma = corrigido
                incerto = False
            else:
                id_plataforma, sugestao = escolher_plataforma(
                    candidatos, por_id, caminho_relativo_pasta, marcado,
                    tamanho_mb, caminho_absoluto)
                incerto = (id_plataforma == SEM_PASTA)
            # A BIOS deixada junto dos jogos (o SCPH1001.BIN na pasta do PS1)
            # nao e' jogo: sai da lista, e o ARENA a leva para a pasta BIOS e
            # para onde o emulador procura (servidor\bios.py). So pela marca
            # ou pelo conteudo -- um jogo de Super Nintendo tem o tamanho do BS-X.
            if id_plataforma != SEM_PASTA and bios.e_bios_na_pasta_de_jogos(caminho_absoluto, id_plataforma):
                continue
            # A pasta decide, sempre. Mas quando da para abrir o arquivo e
            # ele diz outra coisa, vale avisar: Gran Turismo 2 de 660 MB na
            # pasta do Magnavox Odyssey 2 e arquivo arrastado errado, nao
            # escolha consciente. O ARENA nao muda nada sozinho - so conta.
            discorda = None
            if (id_plataforma != SEM_PASTA and extensao in (".iso", ".chd",
                                                            ".cue", ".bin",
                                                            ".rvz", ".wia")):
                try:
                    conteudo = identificador.identificar(
                        caminho_absoluto, list(por_id))
                except Exception:
                    conteudo = None
                if conteudo and conteudo != id_plataforma:
                    discorda = conteudo

            if id_plataforma == SEM_PASTA:
                plataforma = {"nome": "Precisa escolher o console",
                              "pede_placar": False}
            else:
                plataforma = por_id[id_plataforma]
            titulo = titulo_do_jogo(nome_arquivo, pasta_atual)
            titulo_do_arquivo = titulo
            if sozinho_na_pasta(pasta_atual, caminho_pasta, nome_arquivo, arquivos):
                titulo = nome_do_gamebase(pasta_atual, arquivos) or titulo

            # Fliperama: o nome do arquivo e' o do romset ("mslugx"). O nome
            # de verdade vem dos bancos do RetroArch (servidor\nomes_arcade.py).
            romset = nome_banco = None
            avisos = []
            nucleo_arcade = nomes_arcade.nucleo_de(plataforma.get("core"))
            if nucleo_arcade and extensao in (".zip", ".7z"):
                romset = os.path.splitext(nome_arquivo)[0].lower()
                nome_banco = nomes_arcade.nome_do_romset(nome_arquivo, nucleo_arcade)
                if nome_banco:
                    titulo = nomes_arcade.titulo_para_a_tela(nome_banco)
                else:
                    avisos.append(aviso_de_nome_de_fliperama(titulo, extensao, nucleo_arcade))
                avisos += avisos_do_romset(caminho_absoluto, romset, discos_zipados, nucleo_arcade)
                # Zip com parte danificada (o mslugx.zip: personagens com cor
                # estranha). A lista so LE o resultado ja conferido -- quem
                # descompacta e' a conferencia de fundo (arena.py) ou o Jogar.
                ruim = integridade.parte_danificada(caminho_absoluto, conferir=False)
                if ruim:
                    avisos.append({"texto": integridade.texto_do_aviso(ruim)})
            elif nucleo_arcade and extensao == ".chd":
                # Disco de fliperama sem o .zip do romset ao lado (o Kinst
                # da pasta): sozinho ele nao abre (achado de 02/10/2026).
                pasta_do_disco = os.path.basename(pasta_atual).lower()
                base_do_disco = os.path.splitext(nome_arquivo)[0].lower()
                if any(n.lower() in (pasta_do_disco + ".zip", pasta_do_disco + ".7z") for n in arquivos):
                    # O zip esta AQUI, junto do disco (kinst\kinst.zip): o
                    # cartao e' o do zip, e e' nele que vai o aviso do arranjo.
                    continue
                if any(n.lower() in (base_do_disco + ".zip", base_do_disco + ".7z") for n in arquivos):
                    # O disco solto AO LADO do zip dele (kinst.chd + kinst.zip):
                    # o cartao e' o do zip, com o aviso e o botao Arrumar.
                    continue
                em_outra_pasta = arrumar.disco_em_outra_pasta(caminho_absoluto)
                if em_outra_pasta:
                    # Arcade\Killer Instinct\kinst.chd com o Arcade\kinst.zip.
                    zip_irmao, pasta_certa = em_outra_pasta
                    nome_banco = nomes_arcade.nome_do_romset(os.path.basename(zip_irmao), nucleo_arcade)
                    if nome_banco:
                        titulo = nomes_arcade.titulo_para_a_tela(nome_banco)
                    avisos.append({"texto": "Este disco (%s) é do %s, mas está na pasta %s: o emulador só "
                                            "procura o disco numa pasta com o nome do zip (%s), ao lado dele."
                                            % (nome_arquivo, os.path.basename(zip_irmao),
                                               os.path.basename(pasta_atual), os.path.basename(pasta_certa)),
                                   "arrumar": arrumar.conserto_do_disco(caminho_absoluto)})
                elif os.sep not in os.path.relpath(pasta_atual, caminho_pasta):
                    # Solto na pasta do console, sem o zip: nao da para saber de
                    # que jogo e' (achado de 03/10/2026: o aviso dizia "falta o
                    # arcade.zip", o nome da PASTA do console).
                    avisos.append({"texto": "Este é o disco (.chd) de um jogo de fliperama, e ele não abre "
                                            "sozinho: o jogo abre pelo .zip dele (o nome curto, o romset), e "
                                            "o disco vai numa pasta com o mesmo nome do zip, ao lado dele "
                                            "(ex.: kinst.zip e a pasta kinst com o kinst.chd dentro). Falta o "
                                            ".zip deste jogo."})
                else:
                    nome_banco = nomes_arcade.nome_do_romset(pasta_do_disco + ".zip", nucleo_arcade)
                    if nome_banco:
                        titulo = nomes_arcade.titulo_para_a_tela(nome_banco)
                    avisos.append({"texto": "Este é o disco (.chd) de um jogo de fliperama: o emulador abre "
                                            "o jogo pelo %s.zip (o romset), com este disco numa subpasta %s "
                                            "ao lado dele. Falta o %s.zip na pasta."
                                            % (pasta_do_disco, pasta_do_disco, pasta_do_disco)})
            # A BIOS que ESTE jogo usa e que nao esta na pasta (servidor\bios.py):
            # Sega CD e Saturn pela regiao do jogo, Dreamcast (sem ela, alguns
            # travam) e Satellaview (o "BS" do nome). Achados: em 02/10/2026 os
            # 5 BS F-ZERO nao abriam e o cartao nao dizia nada; em 03/10, o Sega
            # CD e o Saturn apareciam "prontos" sem BIOS nenhuma.
            aviso_bios = bios.aviso_do_jogo(id_plataforma, nome_arquivo,
                                            os.path.join(RAIZ, "retroarch", "system"),
                                            plataforma.get("nome", ""), caminho_absoluto)
            if aviso_bios:
                avisos.append({"texto": aviso_bios})
            # Jogo de CD dentro de .zip (o emulador nao abre CD de dentro de
            # zip): o cartao explica, e o botao Arrumar descompacta numa pasta
            # com o nome do jogo (servidor\arrumar.py). Ja descompactado, o
            # jogo e' o da pasta: o zip que ficou nao entra na lista de novo.
            tipo_do_console = tipo_de_console(id_plataforma, plataforma)
            if extensao in (".zip", ".7z") and tipo_do_console in ("disco", "externo"):
                if extensao == ".7z":
                    avisos.append({"texto": "Este .7z precisa ser descompactado: o emulador não abre jogo de "
                                            "CD de dentro de arquivo compactado. Descompacte com o 7-Zip (ou o "
                                            "Explorador do Windows) numa pasta com o nome do jogo, aqui mesmo, "
                                            "e clique em Atualizar lista."})
                elif os.path.isdir(arrumar.pasta_do_descompactado(caminho_absoluto)) \
                        and arrumar.discos_do_zip(caminho_absoluto):
                    continue
                elif arrumar.precisa_descompactar(caminho_absoluto, tipo_do_console):
                    dentro = [os.path.basename(i.filename) for i in arrumar.discos_do_zip(caminho_absoluto)]
                    avisos.append({"texto": "Este .zip tem um jogo de CD dentro (%s), e o emulador não abre "
                                            "CD de dentro de .zip. Ele precisa ser descompactado numa pasta "
                                            "com o nome do jogo: o botão Arrumar faz isso (o .zip fica)."
                                            % (", ".join(dentro[:2]) + (" e mais %d" % (len(dentro) - 2)
                                                                        if len(dentro) > 2 else "")),
                                   "arrumar": arrumar.conserto("descompactar", zip=nome_arquivo),
                                   "descompactar": True})
            if discorda:
                avisos.append({
                    "texto": "O conteúdo deste arquivo é de %s, mas ele está na pasta de %s. "
                             "Assim ele não abre: mova para a pasta certa."
                             % (por_id[discorda]["nome"] if discorda in por_id else discorda,
                                plataforma.get("nome", "outro console")),
                    "mover_para": discorda})

            # Quantos jogadores ESTE jogo aceita: quem diz e' o professor,
            # no dados\jogadores.txt (servidor\jogadores.py). Jogo que nao
            # esta no arquivo (ou antes de o ARENA cria-lo): o que o ARENA
            # ja sabe -- jogos testados (consoles.json -> jogadores_por_jogo),
            # lista de Multitap (5), numero do console (N64: 4). E' com isso
            # que o arquivo nasce preenchido. O nome curto do romset tambem
            # vale ("Tmnt2 = 4" continua valendo depois que o titulo virou o
            # nome completo).
            outros_nomes = tuple(n for n in (romset, titulo_do_arquivo if titulo_do_arquivo != titulo else None)
                                 if n)
            do_jogo = jogadores.regra_do_arquivo(titulo, regras, outros_nomes)
            if do_jogo is None:
                do_jogo = jogadores.numero_sem_regra(plataforma, titulo, outros_nomes)
            # O que o jogo aceita, limitado ao que o nucleo permite
            # (servidor\multitap.json). O mesmo calculo do /api/jogar.
            ligacao = graficos.jogadores_do_jogo(
                plataforma.get("core", ""), do_jogo, mapa=mapa_multitap,
                arquivo=caminho_absoluto)
            # Console de emulador externo (Dolphin, Xenia, PCSX2, RPCS3): o
            # adaptador e o limite do RetroArch nao se aplicam, quem cuida
            # dos controles e' o proprio emulador. Vale o numero do
            # professor (achado na revisao: GameCube mostrava "ate 2").
            if plataforma.get("externo") and id_plataforma in mapa_multitap.get("externos", {}):
                ligacao = {"jogadores": do_jogo, "motivo": ""}

            encontrados.append({
                "id": identificacao,
                "titulo": titulo,
                "ordenacao": chave_ordenacao(titulo),
                "plataforma": id_plataforma,
                "plataforma_nome": plataforma["nome"],
                "arquivo": caminho_relativo,
                "origem": origem,
                "origem_rotulo": ORIGENS.get(origem, origem),
                "pede_placar": plataforma.get("pede_placar", False),
                # O que o jogo aceita (arquivo do professor) e o que da
                # para jogar de verdade neste console (limitado ao nucleo).
                "jogadores_do_jogo": do_jogo,
                "jogadores_max": ligacao["jogadores"],
                # Jogo com rede PROPRIA (System Link do PS2/Xbox 360): a tela
                # do Jogar Junto explica que da para ligar 2 computadores
                # pelo menu de dentro do jogo.
                "rede_propria": bool(graficos.jogo_tem_system_link_ps2(plataforma, titulo)
                                     or graficos.jogo_tem_netplay_xbox360(plataforma, titulo)),
                # Frase para o aluno quando o jogo aceita mais do que o
                # emulador deste console permite (vazio no resto).
                "motivo_jogadores": ligacao["motivo"],
                # Jogo pequeno (Atari, Commodore: poucos KB) com mais casas,
                # senao a tela mostrava "0 MB".
                "tamanho_mb": round(tamanho_mb, 1) if tamanho_mb >= 1 else round(tamanho_mb, 4),
                # Quando houve desempate, a tela oferece a correcao.
                "ambiguo": incerto,
                # Console que o conteudo do arquivo indica, quando difere
                # da pasta. A tela mostra como sugestao de conferir.
                "discorda": discorda,
                "discorda_nome": (por_id[discorda]["nome"]
                                  if discorda in por_id else None),
                "corrigido": bool(corrigido),
                # Console que o ARENA acha provavel. Serve so para deixar
                # a lista ja marcada na opcao mais util - quem decide e voce.
                "sugestao": sugestao,
                # Artes encontradas na pasta. A tela usa a primeira que
                # carregar; sem nenhuma, ela desenha as iniciais do titulo.
                "capas": capas_do_jogo(caminho_absoluto, pasta_atual, titulo, nome_banco,
                                       sozinho_na_pasta=sozinho_na_pasta(pasta_atual, caminho_pasta,
                                                                         nome_arquivo, arquivos),
                                       outros_titulos=(titulo_do_arquivo,) if titulo_do_arquivo != titulo
                                       else ()),
                # Fliperama: o nome curto do arquivo e o nome completo do
                # banco (a busca de capa usa o completo).
                "romset": romset,
                "nome_banco": nome_banco,
                # Avisos para o aluno, na tela do jogo: disco na pasta errada,
                # romset montado de um jeito que o emulador nao le.
                "avisos": avisos,
            })

        # Discos do mesmo jogo, nesta pasta: um cartao so.
        encontrados[inicio_da_pasta:] = agrupar_discos(encontrados[inicio_da_pasta:], por_id)

    return encontrados


# ---------------------------------------------------------------------------
# BLOCO 6 - Montar e gravar o manifesto
# ---------------------------------------------------------------------------

_TRAVA = threading.Lock()


def gravar_atomico(caminho, texto):
    """Grava sem deixar arquivo pela metade.

    Escreve num temporario com nome unico por thread e so entao renomeia.
    Se o pen drive for retirado no meio da gravacao, o catalogo antigo
    continua inteiro em vez de virar um arquivo cortado ao meio.
    """
    temporario = "%s.%d.tmp" % (caminho, threading.get_ident())
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


def indexar(forcar=False):
    """Funcao principal. Devolve o manifesto e grava em disco.

    Com forcar=False, reaproveita o catalogo salvo se nada mudou nas pastas.
    """
    assinatura = assinatura_das_pastas()

    if not forcar:
        salvo = ler_manifesto_salvo()
        if salvo and salvo.get("assinatura") == assinatura:
            salvo["reaproveitado"] = True
            return salvo

    por_id, por_extensao = carregar_plataformas()

    manuais = ler_manuais()
    regras = jogadores.ler(arquivo_de_jogadores())
    jogos = []
    try:
        for origem in ORIGENS:
            jogos.extend(
                varrer_pasta(os.path.join(PASTA_JOGOS, origem), origem,
                             por_extensao, por_id, manuais, regras)
            )
    finally:
        # Os bancos de nomes de fliperama (7,8 MB) so servem enquanto a lista
        # procura os nomes: soltos aqui, o servidor volta a caber no
        # orcamento de memoria do notebook-alvo (02/10/2026).
        nomes_arcade.liberar()

    # Primeira vez: cria o dados\jogadores.txt com os jogos da pasta e o
    # numero que cada um aceitava ate aqui (nada muda para ninguem).
    if regras is None and jogos:
        try:
            if jogadores.criar([{"titulo": j["titulo"], "plataforma_nome": j["plataforma_nome"],
                                 "jogadores_antes": j["jogadores_do_jogo"]} for j in jogos],
                               arquivo_de_jogadores()):
                # O arquivo novo mudou a assinatura; guarda a de agora para
                # nao refazer a lista a toa na proxima vez.
                assinatura = assinatura_das_pastas()
        except OSError:
            pass  # pen drive protegido etc.: segue com os numeros de antes

    # Ordena por plataforma e depois por titulo, sem acento atrapalhar.
    jogos.sort(key=lambda j: (j["plataforma_nome"], j["ordenacao"]))

    manifesto = {
        "assinatura": assinatura,
        "total": len(jogos),
        "jogos": jogos,
        "reaproveitado": False,
    }

    os.makedirs(PASTA_DADOS, exist_ok=True)
    # separators sem espaco extra deixa o arquivo menor e a leitura mais rapida.
    texto = json.dumps(manifesto, ensure_ascii=False, separators=(",", ":"))
    gravar_atomico(ARQUIVO_MANIFESTO, texto)

    return manifesto


# Executado direto pelo terminal: roda a varredura e mostra um resumo.
if __name__ == "__main__":
    resultado = indexar(forcar=True)
    print("Jogos encontrados: %d" % resultado["total"])

    contagem = {}
    for jogo in resultado["jogos"]:
        nome = jogo["plataforma_nome"]
        contagem[nome] = contagem.get(nome, 0) + 1

    for nome in sorted(contagem):
        print("  %-45s %d" % (nome, contagem[nome]))

    if resultado["total"] == 0:
        print("")
        print("Nenhum jogo na pasta 'jogos'.")
        print("Coloque seus arquivos em jogos\\pessoais e rode de novo.")
