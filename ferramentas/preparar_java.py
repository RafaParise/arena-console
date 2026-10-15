# -*- coding: utf-8 -*-
r"""Monta o Java pequeno que vai em emuladores\Java (o do Java ME).

Por que existe (15/10/2026): o emulador do Java ME (FreeJ2ME-Plus) abre o
Java ("javaw") para rodar o jogo. Para ninguem precisar instalar Java, o
pacote do ARENA leva um, reduzido ao que o emulador usa. O que esta
ferramenta faz, passo a passo:

  1. baixa o JDK 21 do Eclipse Temurin (Adoptium), do endereco oficial, e
     confere a marca SHA-256 (a mesma que a Adoptium publica junto);
  2. descompacta numa pasta temporaria;
  3. roda o jlink do proprio JDK com so os modulos que o FreeJ2ME-Plus usa
     (java.base, java.desktop e java.rmi -- o jdeps listou estes tres no
     freej2me-lr.jar), sem simbolos de depuracao, cabecalhos e manuais:
     de uns 300 MB sobram uns 47 MB;
  4. confere que o java.exe novo abre e poe a pasta em emuladores\Java
     (o LEIA.txt da pasta continua la).

Nao mexe em nada do Windows e nao precisa de administrador.

Uso:
    servidor\python\python.exe ferramentas\preparar_java.py [--zip JDK.zip] [--trocar]

--zip     usa um JDK ja baixado (a marca e' conferida do mesmo jeito)
--trocar  troca o Java que ja estiver em emuladores\Java
"""
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESTINO = os.path.join(RAIZ, "emuladores", "Java")

VERSAO = "21.0.12.1+1"
ENDERECO = ("https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.12.1%2B1/"
            "OpenJDK21U-jdk_x64_windows_hotspot_21.0.12.1_1.zip")
SHA256 = "f9d6e191ab098c0d416e7d588a24420a8621cd2f4720dab2459b8b7b2d2d8b4e"
MODULOS = ["java.base", "java.desktop", "java.rmi"]


def marca(caminho):
    resumo = hashlib.sha256()
    with open(caminho, "rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1 << 20), b""):
            resumo.update(bloco)
    return resumo.hexdigest()


def baixar(destino):
    print("Baixando o JDK %s (uns 200 MB)..." % VERSAO, flush=True)
    with urllib.request.urlopen(ENDERECO, timeout=60) as resposta, open(destino, "wb") as arquivo:
        shutil.copyfileobj(resposta, arquivo, 1 << 20)


def tem_java(pasta):
    return os.path.isfile(os.path.join(pasta, "bin", "javaw.exe"))


def principal():
    trocar = "--trocar" in sys.argv
    if tem_java(DESTINO) and not trocar:
        print("Ja existe um Java em %s. Para trocar, rode de novo com --trocar." % DESTINO)
        return 0
    trabalho = tempfile.mkdtemp(prefix="arena_preparar_java_")
    montando = DESTINO + ".montando"
    try:
        if "--zip" in sys.argv:
            jdk_zip = os.path.abspath(sys.argv[sys.argv.index("--zip") + 1])
        else:
            jdk_zip = os.path.join(trabalho, "jdk.zip")
            baixar(jdk_zip)
        if marca(jdk_zip) != SHA256:
            print("A marca do JDK nao confere: o arquivo veio diferente do publicado. Nada foi mudado.")
            return 1
        print("Descompactando...", flush=True)
        with zipfile.ZipFile(jdk_zip) as arquivo_zip:
            arquivo_zip.extractall(trabalho)
        jdk = next(os.path.join(trabalho, nome) for nome in os.listdir(trabalho)
                   if os.path.isfile(os.path.join(trabalho, nome, "bin", "jlink.exe")))
        if os.path.exists(montando):
            shutil.rmtree(montando)
        print("Reduzindo com o jlink (%s)..." % ", ".join(MODULOS), flush=True)
        subprocess.run([os.path.join(jdk, "bin", "jlink.exe"), "--add-modules", ",".join(MODULOS),
                        "--strip-debug", "--no-header-files", "--no-man-pages", "--compress=zip-9",
                        "--output", montando], check=True)
        versao = subprocess.run([os.path.join(montando, "bin", "java.exe"), "-version"],
                                capture_output=True, text=True)
        if versao.returncode != 0 or VERSAO.split("+")[0] not in versao.stderr:
            print("O Java montado nao abriu direito:\n" + versao.stderr)
            return 1
        leia = os.path.join(DESTINO, "LEIA.txt")
        if os.path.isfile(leia):
            shutil.copyfile(leia, os.path.join(montando, "LEIA.txt"))
        if os.path.isdir(DESTINO):
            velho = DESTINO + ".velho"
            if os.path.exists(velho):
                shutil.rmtree(velho)
            os.replace(DESTINO, velho)
            os.replace(montando, DESTINO)
            shutil.rmtree(velho)
        else:
            os.replace(montando, DESTINO)
        tamanho = sum(os.path.getsize(os.path.join(atual, nome))
                      for atual, _pastas, nomes in os.walk(DESTINO) for nome in nomes)
        print("Pronto: %s (%.0f MB)." % (DESTINO, tamanho / 1024.0 / 1024.0))
        return 0
    finally:
        shutil.rmtree(trabalho, ignore_errors=True)
        if os.path.isdir(montando):
            shutil.rmtree(montando, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(principal())
