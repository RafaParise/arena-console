# -*- coding: utf-8 -*-
r"""Poe em retroarch\system\dolphin-emu os arquivos de apoio do nucleo Dolphin
do RetroArch (o jeito "Dentro do RetroArch" do GameCube e do Wii).

Por que existe (15/10/2026): sem a pasta Sys, o nucleo dolphin_libretro abre
a maioria dos jogos, mas o registro reclama: "Core file codehandler.bin
missing!" (sem os codigos de trapaca), "Post-processing shader not found"
(sem os filtros de imagem) e "Trying to access Windows-1252 fonts but they
are not loaded" (jogo que usa as fontes do console mostra o texto errado).
O libretro publica esses arquivos no Dolphin.zip do buildbot, o mesmo que o
menu do RetroArch baixa em "Online Updater -> Core System Files Downloader".
Licenca: a do Dolphin (GPL-2.0 ou posterior), em dolphin-emu\license.txt; a
das fontes, em dolphin-emu\Sys\GC\font-licenses.txt.

O que faz:
  1. baixa o Dolphin.zip (ou usa o --zip dado) e mostra a marca SHA-256;
  2. confere cada nome dentro dele: so dolphin-emu\Sys\... e
     dolphin-emu\license.txt (nada fora da pasta, nada com "..");
  3. descompacta em retroarch\system, so se a pasta Sys ainda nao existe.
     Nunca toca em dolphin-emu\User (saves e configuracao de quem joga).

Nao precisa de administrador. O montador (ferramentas\montar_versao_alunos.py)
leva a pasta Sys para o pacote.

Uso:
    servidor\python\python.exe ferramentas\preparar_dolphin_sys.py [--zip Dolphin.zip]
"""
import hashlib
import os
import shutil
import sys
import tempfile
import urllib.request
import zipfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SISTEMA = os.path.join(RAIZ, "retroarch", "system")
ENDERECO = "https://buildbot.libretro.com/assets/system/Dolphin.zip"
# O que foi testado em 15/10/2026 (8 jogos de GameCube e Wii). O buildbot
# atualiza o arquivo de tempos em tempos: marca diferente e' so aviso.
TESTADO = "5dae774abf34f31477e82e14811e03c0ee52ea85ebca9e747a14015c1b624d8d"


def marca(caminho):
    resumo = hashlib.sha256()
    with open(caminho, "rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1 << 20), b""):
            resumo.update(bloco)
    return resumo.hexdigest()


def nomes_seguros(zipado):
    """Os nomes do zip, se todos ficam dentro de dolphin-emu\\Sys ou sao a
    licenca. Senao, SystemExit (zip estranho: nao descompacta nada)."""
    nomes = []
    for nome in zipado.namelist():
        partes = nome.replace("\\", "/").split("/")
        if partes[0] != "dolphin-emu" or ".." in partes or os.path.isabs(nome) or ":" in nome:
            raise SystemExit("Nome estranho dentro do zip, nada foi descompactado: %s" % nome)
        if partes[1:2] not in (["Sys"], ["license.txt"], [""]):
            raise SystemExit("Arquivo fora da pasta Sys dentro do zip, nada foi descompactado: %s" % nome)
        nomes.append(nome)
    return nomes


def principal():
    destino = os.path.join(SISTEMA, "dolphin-emu", "Sys")
    if os.path.isdir(destino):
        print("Ja existe: %s. Nada a fazer (para trocar, apague so a pasta Sys)." % destino)
        return 0
    if not os.path.isdir(SISTEMA):
        print("Nao achei a pasta retroarch\\system.")
        return 1
    trabalho = tempfile.mkdtemp(prefix="arena_preparar_dolphin_")
    try:
        if "--zip" in sys.argv:
            arquivo = os.path.abspath(sys.argv[sys.argv.index("--zip") + 1])
        else:
            arquivo = os.path.join(trabalho, "Dolphin.zip")
            print("Baixando %s ..." % ENDERECO, flush=True)
            with urllib.request.urlopen(ENDERECO, timeout=60) as resposta, open(arquivo, "wb") as saida:
                shutil.copyfileobj(resposta, saida, 1 << 20)
        sha = marca(arquivo)
        print("Marca SHA-256: %s%s" % (sha, "" if sha == TESTADO else " (outra versao: a testada era %s)" % TESTADO))
        with zipfile.ZipFile(arquivo) as zipado:
            nomes = nomes_seguros(zipado)
            zipado.extractall(SISTEMA, members=nomes)
        total = sum(len(arquivos) for _atual, _pastas, arquivos in os.walk(os.path.join(SISTEMA, "dolphin-emu")))
        print("Pronto: %d arquivos em %s." % (total, os.path.join(SISTEMA, "dolphin-emu")))
        return 0
    finally:
        shutil.rmtree(trabalho, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(principal())
