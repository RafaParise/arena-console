# -*- coding: utf-8 -*-
r"""Converte um jogo de fliperama "decriptado para emulador antigo" para o
formato que o FBNeo do ARENA abre.

Por que existe (Rafael, 02/10/2026): o KOF 2002 dele nao abria nem no MAME
nem no FBNeo. O kof2002.zip tinha as partes kof2k2_*.rom -- o conjunto ja
DECRIPTADO, do tempo do Kawaks e do Nebula. O MAME e o FBNeo de hoje pedem
o original codificado (265-c1.c1...) e recusavam. Mas o FBNeo tem um
conjunto "Fully Decrypted" (kof2k2fd) feito das MESMAS partes:
  - 13 iguais, so com outro nome (o FBNeo confere pela marca, o CRC);
  - o som em 4 pedacos de 4 MB, que juntos dois a dois sao os 2 de 8 MB dele;
  - o programa de som (M1) e' de outra versao -- a que o proprio FBNeo usa
    no hack kof2k2omg, com estas mesmas partes de som. Vai como "correcao"
    na pasta que o FBNeo tem para isso (retroarch\system\fbneo\patched\
    kof2k2fd.zip): ali ele aceita a parte pelo nome e tamanho, sem conferir
    a marca (opcao "Allow patched romsets", ligada por padrao).
Conferido abrindo de verdade: demonstracao e tela de titulo, cores certas
(testes\teste_kof2002_convertido.py).

Como funciona: cada parte e' achada pela MARCA (nao pelo nome), juntada se
for o caso, e a marca do resultado e' conferida antes de gravar. Faltou ou
nao bateu alguma parte: nada e' mexido. O zip original vai para
backup\originais\ (nada e' apagado). Rodar de novo nao estraga nada: o que
ja foi convertido e' pulado.

Uso:
    servidor\python\python.exe ferramentas\converter_fliperama_decriptado.py [--pasta <ARENA>] [--fazer]
Sem --fazer: so mostra o que faria.
"""
import os
import sys
import zipfile
import zlib

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Cada conversao: as partes do conjunto do FBNeo -- (nome, marcas das partes
# de origem, juntadas nessa ordem; marca do resultado) -- e as partes que vao
# como correcao (nome, marca da parte de origem). Marcas conferidas no proprio
# fbneo_libretro.dll e no registro dele ("ROM ... with name ... and CRC ...").
CONVERSOES = [
    {
        "jogo": "The King of Fighters 2002",
        "conjunto": "kof2k2fd",
        "pasta": "Neo Geo",
        "partes": [
            ("265-p1.p1", (0x9ede7323,), 0x9ede7323),
            ("265-p2d.sp2", (0x432fdf53,), 0x432fdf53),
            ("265-s1d.s1", (0xe0eaaba3,), 0xe0eaaba3),
            ("265-c1d.c1", (0x7efa6ef7,), 0x7efa6ef7),
            ("265-c2d.c2", (0xaa82948b,), 0xaa82948b),
            ("265-c3d.c3", (0x959fad0b,), 0x959fad0b),
            ("265-c4d.c4", (0xefe6a468,), 0xefe6a468),
            ("265-c5d.c5", (0x74bba7c6,), 0x74bba7c6),
            ("265-c6d.c6", (0xe20d2216,), 0xe20d2216),
            ("265-c7d.c7", (0x8a5b561c,), 0x8a5b561c),
            ("265-c8d.c8", (0xbef667a3,), 0xbef667a3),
            ("265-v1d.v1", (0x13d98607, 0x9cf74677), 0x0fc9a58d),
            ("265-v2d.v2", (0x8e9448b5, 0x067271b5), 0xb8c475a4),
        ],
        "correcao": [("265-m1d.m1", 0xab9d360e)],
    },
]

LEIA_CORRECAO = """\
CORREÇÕES DE JOGOS DE FLIPERAMA (FBNeo)

O FBNeo confere cada parte de um jogo pela marca (CRC). Nesta pasta ficam
partes que ele aceita pelo nome e pelo tamanho, sem conferir a marca (opção
"Allow patched romsets" do FBNeo, ligada por padrão).

kof2k2fd.zip -- o programa de som (M1) do The King of Fighters 2002 que
estava no zip do professor. É de outra versão da que o FBNeo espera para
este conjunto; o próprio FBNeo usa esta versão em outro conjunto do mesmo
jogo. Sem este arquivo, o jogo da pasta Neo Geo (kof2k2fd.zip) não abre.

Feito pelo ARENA (ferramentas\\converter_fliperama_decriptado.py).
"""

LEIA_ORIGINAIS = """\
JOGOS ORIGINAIS GUARDADOS

Quando o ARENA converte um jogo para o formato que o emulador abre, o
arquivo de antes fica guardado aqui (nada é apagado). Esta pasta não entra
no rodízio das cópias de segurança.

O jogo convertido já tem tudo o que estava aqui. Pode apagar esta pasta
quando tiver certeza de que o convertido funciona.

Feito pelo ARENA (ferramentas\\converter_fliperama_decriptado.py).
"""


def marcas_do_zip(caminho):
    """{marca: ZipInfo} de um zip; {} se nao abre."""
    try:
        with zipfile.ZipFile(caminho) as z:
            return {i.CRC: i for i in z.infolist() if not i.is_dir()}
    except (OSError, zipfile.BadZipFile, ValueError):
        return {}


def origens(conversao):
    """Todas as marcas que o zip de origem precisa ter."""
    marcas = {m for _nome, partes, _final in conversao["partes"] for m in partes}
    return marcas | {m for _nome, m in conversao["correcao"]}


def achar_originais(raiz, conversao):
    """Os zips de jogos\\pessoais com TODAS as partes de origem."""
    precisa = origens(conversao)
    achados = []
    pessoais = os.path.join(raiz, "jogos", "pessoais")
    for atual, subpastas, arquivos in os.walk(pessoais):
        subpastas.sort()
        for nome in sorted(arquivos):
            if nome.lower().endswith(".zip"):
                caminho = os.path.join(atual, nome)
                if precisa <= set(marcas_do_zip(caminho)):
                    achados.append(caminho)
    return achados


def ja_convertido(caminho, conversao):
    """O zip do conjunto ja existe com as marcas certas?"""
    marcas = set(marcas_do_zip(caminho))
    return bool(marcas) and {final for _nome, _partes, final in conversao["partes"]} <= marcas


def gravar_zip(destino, partes):
    """Grava (nome, dados) num zip ao lado do destino e troca no fim."""
    temporario = destino + ".convertendo"
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    try:
        with zipfile.ZipFile(temporario, "w", zipfile.ZIP_DEFLATED) as saida:
            for nome, dados in partes:
                saida.writestr(nome, dados() if callable(dados) else dados)
        os.replace(temporario, destino)
    finally:
        if os.path.exists(temporario):
            os.remove(temporario)


def nome_livre(pasta, nome):
    """'nome.zip' ou, se ja existir, 'nome (2).zip'..."""
    base, extensao = os.path.splitext(nome)
    candidato, n = nome, 2
    while os.path.exists(os.path.join(pasta, candidato)):
        candidato = "%s (%d)%s" % (base, n, extensao)
        n += 1
    return os.path.join(pasta, candidato)


def converter(raiz, conversao, original, fazer, dizer=print):
    """Converte um zip. Devolve True se ficou tudo certo (ou daria certo).
    Parte estragada no zip (marca que nao confere ao descompactar), disco
    cheio...: para com uma frase, sem deixar nada pela metade."""
    try:
        return _converter(raiz, conversao, original, fazer, dizer)
    except (OSError, zipfile.BadZipFile, ValueError) as falha:
        dizer("  PARADO: %s. Nada foi mexido no original." % falha)
        return False


def _converter(raiz, conversao, original, fazer, dizer):
    destino =os.path.join(raiz, "jogos", "pessoais", conversao["pasta"], conversao["conjunto"] + ".zip")
    correcao = os.path.join(raiz, "retroarch", "system", "fbneo", "patched", conversao["conjunto"] + ".zip")
    guardar = os.path.join(raiz, "backup", "originais")
    relativo = lambda c: os.path.relpath(c, raiz)  # noqa: E731
    dizer("%s: %s" % (conversao["jogo"], relativo(original)))

    with zipfile.ZipFile(original) as z:
        por_marca = {i.CRC: i for i in z.infolist() if not i.is_dir()}

        def ler(marcas):
            # z.read confere a marca de cada parte: parte estragada para tudo.
            return b"".join(z.read(por_marca[m]) for m in marcas)

        # Confere TUDO antes de gravar qualquer coisa.
        for nome, partes, final in conversao["partes"]:
            marca = zlib.crc32(ler(partes)) & 0xffffffff
            if marca != final:
                dizer("  PARADO: %s daria a marca %08x (o FBNeo pede %08x). Nada foi mexido." % (nome, marca, final))
                return False
        dizer("  as %d partes do conjunto %s conferem" % (len(conversao["partes"]), conversao["conjunto"]))
        if not fazer:
            dizer("  faria: %s" % relativo(destino))
            dizer("  faria: %s (o programa de som, como correcao)" % relativo(correcao))
            dizer("  faria: guardar o original em %s" % relativo(guardar))
            return True
        if ja_convertido(destino, conversao):
            dizer("  ja convertido: %s" % relativo(destino))
        else:
            gravar_zip(destino, [(nome, (lambda p=partes: ler(p))) for nome, partes, _final in conversao["partes"]])
            if not ja_convertido(destino, conversao):
                dizer("  PARADO: o zip gravado nao confere (%s)." % relativo(destino))
                return False
            dizer("  gravado: %s" % relativo(destino))
        gravar_zip(correcao, [(nome, ler((marca,))) for nome, marca in conversao["correcao"]])
        dizer("  gravado: %s" % relativo(correcao))

    leia = os.path.join(os.path.dirname(correcao), "LEIA.txt")
    if not os.path.exists(leia):
        with open(leia, "w", encoding="utf-8-sig", newline="\r\n") as f:
            f.write(LEIA_CORRECAO)
    os.makedirs(guardar, exist_ok=True)
    leia = os.path.join(guardar, "LEIA.txt")
    if not os.path.exists(leia):
        with open(leia, "w", encoding="utf-8-sig", newline="\r\n") as f:
            f.write(LEIA_ORIGINAIS)
    para = nome_livre(guardar, os.path.basename(original))
    os.replace(original, para)
    dizer("  original guardado: %s" % relativo(para))
    return True


def principal(argumentos):
    raiz = RAIZ
    if "--pasta" in argumentos:
        raiz = os.path.abspath(argumentos[argumentos.index("--pasta") + 1])
    fazer = "--fazer" in argumentos
    if not os.path.isdir(os.path.join(raiz, "jogos", "pessoais")):
        print("Nao achei jogos\\pessoais em %s." % raiz)
        return 1
    print("ARENA: %s%s" % (raiz, "" if fazer else "  (so mostrando; para converter: --fazer)"))
    achou, falhou = 0, 0
    for conversao in CONVERSOES:
        for original in achar_originais(raiz, conversao):
            achou += 1
            if not converter(raiz, conversao, original, fazer):
                falhou += 1
    if not achou:
        print("Nenhum jogo para converter.")
    return 1 if falhou else 0


if __name__ == "__main__":
    sys.exit(principal(sys.argv[1:]))
