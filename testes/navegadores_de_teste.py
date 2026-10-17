# -*- coding: utf-8 -*-
r"""Navegadores de teste (item 11 dos pedidos de 15/10/2026): o Chrome for
Testing e o Firefox, de fonte oficial, numa pasta de testes FORA do ARENA,
sem instalar nada no Windows.

  - Chrome for Testing (Google): o .zip da versao estavel, a que o proprio
    Google publica para testes automaticos
    (googlechromelabs.github.io/chrome-for-testing), descompactado.
  - Firefox (Mozilla): o instalador oficial em portugues, conferido pela
    lista SHA-256 da propria Mozilla (SHA256SUMS), e so EXTRAIDO
    (/ExtractDir): nada vai para o registro, para o menu Iniciar nem para a
    lista de navegadores do Windows.
  - O Firefox so roda depois que a assinatura digital do Windows confirma
    quem o fez (Get-AuthenticodeSignature: Mozilla Corporation). O Chrome
    for Testing NAO vem assinado (conferido em 17/10/2026: NotSigned) e o
    Google nao publica a lista SHA-256 dele: a confianca vem da origem --
    so o endereco oficial (storage.googleapis.com/chrome-for-testing-public),
    tirado da lista do proprio Google, por HTTPS.

Pasta: %LOCALAPPDATA%\ARENA-testes\navegadores (reaproveitada entre rodadas;
o ARENA nunca usa estes navegadores, so os testes).

Uso: servidor\python\python.exe testes\navegadores_de_teste.py
     (baixa o que faltar e lista os navegadores prontos)
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
import zipfile

PASTA = os.path.join(os.environ.get("LOCALAPPDATA") or tempfile.gettempdir(), "ARENA-testes", "navegadores")
LISTA_CHROME = "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json"
VERSOES_FIREFOX = "https://product-details.mozilla.org/1.0/firefox_versions.json"
ARQUIVO_FIREFOX = "https://archive.mozilla.org/pub/firefox/releases/%s/"
EDGE = (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe")


def _baixar(url, destino):
    temporario = destino + ".baixando"
    with urllib.request.urlopen(url, timeout=120) as resposta, open(temporario, "wb") as saida:
        shutil.copyfileobj(resposta, saida, 1 << 20)
    os.replace(temporario, destino)
    return destino


def _ler(url):
    with urllib.request.urlopen(url, timeout=60) as resposta:
        return resposta.read().decode("utf-8")


def assinatura(programa):
    """(status, quem assinou) pela assinatura digital do Windows."""
    comando = ("$a = Get-AuthenticodeSignature -LiteralPath '%s'; "
               "$a.Status.ToString() + '|' + $a.SignerCertificate.Subject" % programa.replace("'", "''"))
    saida = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", comando],
                           capture_output=True, text=True, timeout=60).stdout.strip()
    status, _, quem = saida.partition("|")
    return status, quem


def _conferir(programa, empresa):
    status, quem = assinatura(programa)
    if status != "Valid" or empresa.lower() not in quem.lower():
        raise OSError("assinatura de %s: %s (%s) -- esperado %s" % (programa, status, quem, empresa))


def chrome_for_testing():
    """O chrome.exe do Chrome for Testing estavel (baixa na primeira vez)."""
    lista = json.loads(_ler(LISTA_CHROME))
    estavel = lista["channels"]["Stable"]
    versao = estavel["version"]
    pasta = os.path.join(PASTA, "chrome-for-testing-%s" % versao)
    programa = os.path.join(pasta, "chrome-win64", "chrome.exe")
    if not os.path.isfile(programa):
        url = next(b["url"] for b in estavel["downloads"]["chrome"] if b["platform"] == "win64")
        if not url.startswith("https://storage.googleapis.com/chrome-for-testing-public/"):
            raise OSError("endereco do Chrome for Testing fora do oficial: %s" % url)
        os.makedirs(pasta, exist_ok=True)
        pacote = _baixar(url, os.path.join(pasta, "chrome-win64.zip"))
        with zipfile.ZipFile(pacote) as arquivo:
            for nome in arquivo.namelist():
                destino = os.path.normpath(os.path.join(pasta, nome))
                if not destino.startswith(os.path.normpath(pasta) + os.sep):
                    raise OSError("caminho fora da pasta no zip: %s" % nome)
            arquivo.extractall(pasta)
        os.remove(pacote)
    return programa, versao


def firefox():
    """O firefox.exe da versao estavel atual, so extraido (baixa na primeira vez)."""
    versao = json.loads(_ler(VERSOES_FIREFOX))["LATEST_FIREFOX_VERSION"]
    pasta = os.path.join(PASTA, "firefox-%s" % versao)
    programa = os.path.join(pasta, "core", "firefox.exe")
    if not os.path.isfile(programa):
        nome = "Firefox Setup %s.exe" % versao
        relativo = "win64/pt-BR/" + nome
        somas = _ler(ARQUIVO_FIREFOX % versao + "SHA256SUMS")
        esperado = next((linha.split()[0] for linha in somas.splitlines()
                         if linha.endswith("  " + relativo)), None)
        if not esperado:
            raise OSError("a Mozilla nao lista %s no SHA256SUMS" % relativo)
        os.makedirs(pasta, exist_ok=True)
        instalador = _baixar(ARQUIVO_FIREFOX % versao + urllib.parse.quote(relativo),
                             os.path.join(pasta, "instalador.exe"))
        with open(instalador, "rb") as arquivo:
            marca = hashlib.sha256(arquivo.read()).hexdigest()
        if marca != esperado:
            os.remove(instalador)
            raise OSError("o instalador do Firefox nao confere com o SHA256SUMS da Mozilla")
        _conferir(instalador, "Mozilla Corporation")
        # So extrai: /ExtractDir abre os arquivos numa pasta e sai, sem instalar.
        subprocess.run([instalador, "/ExtractDir=" + pasta], timeout=300, check=True)
        os.remove(instalador)
    _conferir(programa, "Mozilla Corporation")
    return programa, versao


def edge():
    for caminho in EDGE:
        if os.path.isfile(caminho):
            return caminho
    return None


def prontos(baixar=True):
    """[(codigo, nome, programa, protocolo)] dos navegadores para o teste."""
    lista = []
    caminho = edge()
    if caminho:
        lista.append(("edge", "Microsoft Edge", caminho, "cdp"))
    if baixar:
        for codigo, nome, achar, protocolo in (("chrome", "Chrome for Testing", chrome_for_testing, "cdp"),
                                               ("firefox", "Mozilla Firefox", firefox, "bidi")):
            try:
                programa, versao = achar()
                lista.append((codigo, "%s %s" % (nome, versao), programa, protocolo))
            except (OSError, ValueError, KeyError, StopIteration, subprocess.SubprocessError) as falha:
                print("[navegadores de teste] %s: %s" % (nome, falha))
    return lista


if __name__ == "__main__":
    for item in prontos():
        print("%-8s %-28s %s (%s)" % item)
    sys.exit(0)
