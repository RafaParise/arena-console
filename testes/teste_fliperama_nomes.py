# -*- coding: utf-8 -*-
r"""Fliperama reconhecido pelo nome, avisos do jogo e identificador sem chute.

Tarefa 7 do Rafael (01/10/2026): "o arcade FBNeo ou MAME nao e'
reconhecido". O ARENA mostrava "Mslugx", "Kof97", "Tmnt2", "Kinst" e
nunca achava capa. Agora o nome vem dos bancos do RetroArch que ja estao
na pasta (retroarch\database\rdb), e a lista avisa o que impede um romset
de abrir: disco (.chd) dentro de .zip, arquivos dentro de uma pasta no zip.

No caminho, dois achados conferidos aqui:
  - o identificador dizia "PlayStation 1" para 19 jogos de PS2 (CHD feito
    com o createcd antigo diz "CD" mesmo com 5 GB) e para o Sonic CD (CD de
    varios consoles: chutava o primeiro da lista);
  - o aviso de "disco na pasta errada" nunca chegava a tela.

Uso: servidor\python\python.exe testes\teste_fliperama_nomes.py
"""
import os
import shutil
import struct
import sys
import tempfile
import zipfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
import identificador  # noqa: E402
import indexador  # noqa: E402
import jogadores  # noqa: E402
import nomes_arcade  # noqa: E402


def texto_mp(s):
    return nomes_arcade._empacotar_texto(s)


def registro(campos):
    """Um registro MessagePack (mapa de textos) como o banco do RetroArch."""
    saida = bytes([0x80 | len(campos)])
    for chave, valor in campos:
        saida += texto_mp(chave) + (texto_mp(valor) if isinstance(valor, str)
                                    else b"\xc4" + bytes([len(valor)]) + valor)
    return saida


def chd_falso(caminho, compressor, megabytes, unidade):
    """Cabecalho de CHD v5 (so o que o identificador le) + enchimento."""
    cabeca = bytearray(124)
    cabeca[0:8] = b"MComprHD"
    struct.pack_into(">I", cabeca, 8, 124)
    struct.pack_into(">I", cabeca, 12, 5)
    cabeca[16:20] = compressor
    struct.pack_into(">Q", cabeca, 32, int(megabytes * 1024 * 1024))
    struct.pack_into(">Q", cabeca, 48, 0)
    struct.pack_into(">I", cabeca, 60, unidade)
    with open(caminho, "wb") as f:
        f.write(bytes(cabeca) + b"\x00" * (70 * 1024))


def main():
    falhas, total = [], [0]

    def confere(nome, ok, detalhe=""):
        total[0] += 1
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, detalhe if not ok else ""))
        if not ok:
            falhas.append(nome)

    # 1. Banco de verdade (se o RetroArch da pasta tiver os bancos).
    if os.path.isfile(os.path.join(nomes_arcade.PASTA_RDB, "FBNeo - Arcade Games.rdb")):
        nome = nomes_arcade.nome_do_romset("mslugx.zip", "fbneo")
        confere("mslugx.zip = Metal Slug X (banco do FBNeo)",
                nome == "Metal Slug X - Super Vehicle-001 (NGM-2500)(NGH-2500)", str(nome))
        confere("titulo na tela sem o codigo da placa",
                nomes_arcade.titulo_para_a_tela(nome) == "Metal Slug X - Super Vehicle-001")
        confere(".7z acha o mesmo nome", nomes_arcade.nome_do_romset("MSLUGX.7z", "fbneo") == nome)
        confere("romset que nao existe = None", nomes_arcade.nome_do_romset("naoexiste123.zip", "fbneo") is None)
    if os.path.isfile(os.path.join(nomes_arcade.PASTA_RDB, "MAME.rdb")):
        confere("kinst.zip = Killer Instinct (banco do MAME)",
                nomes_arcade.nome_do_romset("kinst.zip", "mame") == "Killer Instinct (v1.0)")
    confere("nome com espaco nao e' romset (nem procura)",
            nomes_arcade.nome_do_romset("Super Mario World (USA).zip", "fbneo") is None)
    confere("nucleo de fliperama pelo .dll",
            nomes_arcade.nucleo_de("fbneo_libretro.dll") == "fbneo"
            and nomes_arcade.nucleo_de("mame_libretro.dll") == "mame"
            and nomes_arcade.nucleo_de("snes9x_libretro.dll") is None)

    # 2. Banco falso: o "name" tem de ser do MESMO registro do rom_name.
    pasta = tempfile.mkdtemp(prefix="arena_fliperama_")
    try:
        banco = (b"RARCHDB\x00" + b"\x00" * 8
                 + registro([("name", "Jogo A"), ("rom_name", "a.zip"), ("crc", b"\x01\x02\x03\x04")])
                 + registro([("name", "Jogo B"), ("description", "x" * 40), ("rom_name", "b.zip")])
                 + registro([("rom_name", "c.zip"), ("size", "123")]))
        dados = banco
        confere("registro simples", nomes_arcade._procurar(dados, "a.zip") == "Jogo A")
        confere("campo comprido entre o name e o rom_name",
                nomes_arcade._procurar(dados, "b.zip") == "Jogo B")
        confere("registro sem name nao pega o name do vizinho",
                nomes_arcade._procurar(dados, "c.zip") is None)

        # 3. Avisos do romset.
        arcade = os.path.join(pasta, "Arcade")
        os.makedirs(arcade)
        with zipfile.ZipFile(os.path.join(arcade, "kinst-chd.zip"), "w") as z:
            z.writestr("kinst.chd", b"x" * 100)
        with zipfile.ZipFile(os.path.join(arcade, "kinst.zip"), "w") as z:
            z.writestr("u10-l1", b"x")
        with zipfile.ZipFile(os.path.join(arcade, "kof2002.zip"), "w") as z:
            z.writestr("king/kof2k2_p1.rom", b"x")
            z.writestr("king/kof2k2_c1.rom", b"x")
            z.writestr("readme.html", b"<html>")
        with zipfile.ZipFile(os.path.join(arcade, "mslugx.zip"), "w") as z:
            z.writestr("268-p1cr.p1", b"x")
        open(os.path.join(arcade, "quebrado.zip"), "wb").write(b"nao e zip")
        arquivos = os.listdir(arcade)
        discos = indexador.discos_de_fliperama_zipados(arcade, arquivos)
        confere("kinst-chd.zip reconhecido como disco do kinst", discos == {"kinst": "kinst-chd.zip"},
                str(discos))
        avisos = indexador.avisos_do_romset(os.path.join(arcade, "kinst.zip"), "kinst", discos)
        confere("kinst ganha o aviso de extrair o .chd",
                len(avisos) == 1 and "Extraia o kinst.chd" in avisos[0]["texto"]
                and "Arcade\\kinst\\" in avisos[0]["texto"], str(avisos))
        avisos = indexador.avisos_do_romset(os.path.join(arcade, "kof2002.zip"), "kof2002", discos)
        confere("kof2002 com os arquivos dentro da pasta 'king' (readme solto nao conta)",
                len(avisos) == 1 and '"king"' in avisos[0]["texto"], str(avisos))
        confere("romset certo nao tem aviso",
                indexador.avisos_do_romset(os.path.join(arcade, "mslugx.zip"), "mslugx", discos) == [])
        avisos = indexador.avisos_do_romset(os.path.join(arcade, "quebrado.zip"), "quebrado", discos)
        confere("zip corrompido avisa (sem derrubar a lista)",
                len(avisos) == 1 and "corrompido" in avisos[0]["texto"], str(avisos))

        # 4. Identificador: certeza x palpite.
        todos = ["ps1", "ps2", "psp", "segacd", "saturn", "dreamcast", "gamecube"]
        chd_ps2 = os.path.join(pasta, "ps2_createcd.chd")
        chd_falso(chd_ps2, b"cdlz", 5347, 2448)
        confere("CHD 'de CD' com 5 GB = PS2 (era 'PlayStation 1')",
                identificador.identificar(chd_ps2, todos) == "ps2",
                str(identificador.identificar(chd_ps2, todos)))
        chd_cd = os.path.join(pasta, "sonic_cd.chd")
        chd_falso(chd_cd, b"cdlz", 579, 2448)
        confere("CD de 579 MB com varios consoles possiveis: sem certeza = None",
                identificador.identificar(chd_cd, todos) is None,
                str(identificador.identificar(chd_cd, todos)))
        confere("... e como palpite (tela de escolher o console) continua sugerindo",
                identificador.identificar(chd_cd, todos, palpite=True) == "ps1")
        confere("CD com um console so possivel = esse console",
                identificador.identificar(chd_cd, ["segacd", "ps2"]) == "segacd")

        # 5. Jogadores pelo nome curto do romset.
        regras = [("tmnt2", 4), ("bomberman", 5)]
        confere("'Tmnt2 = 4' vale com o titulo novo, pelo romset",
                jogadores.numero_do_jogo("Teenage Mutant Ninja Turtles - Turtles in Time", regras,
                                         outros_nomes=("tmnt2",)) == 4)
        confere("sem o romset, o titulo novo cai no padrao 2",
                jogadores.numero_do_jogo("Teenage Mutant Ninja Turtles - Turtles in Time", regras) == 2)
        confere("o titulo continua valendo como antes",
                jogadores.numero_do_jogo("Super Bomberman 4", regras, outros_nomes=(None,)) == 5)
    finally:
        shutil.rmtree(pasta, ignore_errors=True)

    # 6. A tela mostra os avisos (antes o 'discorda' nunca aparecia).
    js = open(os.path.join(RAIZ, "launcher", "app.js"), encoding="utf-8").read()
    html = open(os.path.join(RAIZ, "launcher", "index.html"), encoding="utf-8").read()
    confere("a tela desenha os avisos do jogo", "desenharAvisosDoJogo(jogo)" in js and 'id="detalhesAviso"' in html)
    confere("o botao de mover usa o mesmo moverJogo da gaveta",
            "moverJogo(jogo.id, mover.mover_para)" in js)

    print()
    if falhas:
        print("FALHOU: %d de %d" % (len(falhas), total[0]))
        return 1
    print("Fliperama e avisos: %d de %d certos." % (total[0], total[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
