# -*- coding: utf-8 -*-
r"""Monta o Android de testes do ARENA neste computador (item 14 do plano).

Pedido do Rafael (15/10/2026, item 14): "antes de implementar o android
baixe o melhor emulador de android de codigo aberto para testes locais na
maquina". O escolhido e' o emulador do proprio Android (o do AOSP, Android
Open Source Project: codigo aberto, o mesmo que o Android Studio usa), com
uma imagem "default" do Android 15: a do AOSP, sem os servicos do Google,
toda de codigo aberto. Ele roda o aparelho virtual de verdade (x86-64, com
o processador do computador pela Plataforma de Hipervisor do Windows) e o
teste fala com ele pelo adb: instalar o APK, abrir, tirar a foto da tela.

Tudo fica FORA do ARENA, em %LOCALAPPDATA%\ARENA-android (nao vai no pacote
nem no git):
  jdk\        o Java que as ferramentas do Android pedem (o mesmo Temurin
              21 do Java ME, ferramentas\preparar_java.py);
  sdk\        as ferramentas de linha de comando do Android, o adb, o
              emulador, a imagem do Android 15 (AOSP), a plataforma 35 e as
              build-tools (para montar o APK sem o Android Studio);
  avd\        o aparelho virtual "ARENA".

As ferramentas de linha de comando vem conferidas pela marca da lista
oficial do Google (repository2-3.xml); o resto, o proprio sdkmanager do
Google baixa e confere. Instalar pelo sdkmanager pede aceitar as licencas
do SDK do Android (a ferramenta responde "sim" por quem a roda).

Precisa da Plataforma de Hipervisor do Windows ligada (o emulador roda ao
lado do WSL por ela): dism /Online /Enable-Feature /FeatureName:HypervisorPlatform
(administrador) e reiniciar.

Uso:
    servidor\python\python.exe ferramentas\preparar_android.py
"""
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "testes"))
sys.path.insert(0, os.path.join(RAIZ, "ferramentas"))
import limpeza  # noqa: E402
import preparar_linux  # noqa: E402  (o cache e o JDK do Windows, com a marca)

BASE = os.path.join(os.environ.get("LOCALAPPDATA") or tempfile.gettempdir(), "ARENA-android")
JDK = os.path.join(BASE, "jdk")
SDK = os.path.join(BASE, "sdk")
AVD = os.path.join(BASE, "avd")
NOME_DO_AVD = "ARENA"
LISTA = "https://dl.google.com/android/repository/repository2-3.xml"
REPOSITORIO = "https://dl.google.com/android/repository/"
IMAGEM = "system-images;android-35;default;x86_64"
PACOTES = ["platform-tools", "emulator", "platforms;android-35", "build-tools;35.0.0", IMAGEM]


def ambiente():
    """As variaveis que as ferramentas do Android usam: o Java e as pastas."""
    return dict(os.environ, JAVA_HOME=JDK, ANDROID_HOME=SDK, ANDROID_SDK_ROOT=SDK, ANDROID_AVD_HOME=AVD,
                PATH=os.pathsep.join([os.path.join(JDK, "bin"), os.environ.get("PATH", "")]))


def preparar_jdk():
    if os.path.isfile(os.path.join(JDK, "bin", "java.exe")):
        return
    print("Preparando o Java das ferramentas do Android...", flush=True)
    montando = JDK + ".montando"
    if os.path.isdir(montando):
        limpeza.apagar_pasta(montando)
    with zipfile.ZipFile(preparar_linux.baixado(preparar_linux.JDK_WINDOWS)) as pacote:
        pacote.extractall(montando)
    dentro = next(os.path.join(montando, n) for n in os.listdir(montando)
                  if os.path.isfile(os.path.join(montando, n, "bin", "java.exe")))
    os.replace(dentro, JDK)
    limpeza.apagar_pasta(montando)


def preparar_ferramentas():
    """As ferramentas de linha de comando (sdkmanager, avdmanager), da lista
    oficial, com a marca SHA-1 que o Google publica nela."""
    if os.path.isfile(os.path.join(SDK, "cmdline-tools", "latest", "bin", "sdkmanager.bat")):
        return
    with urllib.request.urlopen(LISTA, timeout=60) as resposta:
        raiz = ET.fromstring(resposta.read())
    pacote = next(p for p in raiz.findall("remotePackage") if p.get("path") == "cmdline-tools;latest")
    arquivo = next(a for a in pacote.iter("archive") if (a.findtext("host-os") or "windows") == "windows")
    nome, marca = arquivo.findtext("complete/url"), arquivo.findtext("complete/checksum")
    print("Baixando %s..." % nome, flush=True)
    destino = os.path.join(BASE, nome)
    os.makedirs(BASE, exist_ok=True)
    with urllib.request.urlopen(REPOSITORIO + nome, timeout=60) as resposta, open(destino + ".baixando", "wb") as saida:
        shutil.copyfileobj(resposta, saida, 1 << 20)
    os.replace(destino + ".baixando", destino)
    resumo = hashlib.sha1()
    with open(destino, "rb") as entrada:
        for bloco in iter(lambda: entrada.read(1 << 20), b""):
            resumo.update(bloco)
    if resumo.hexdigest() != marca:
        raise SystemExit("A marca de %s nao confere com a lista do Google. Nada foi mudado." % nome)
    trabalho = os.path.join(BASE, "ferramentas.montando")
    if os.path.isdir(trabalho):
        limpeza.apagar_pasta(trabalho)
    with zipfile.ZipFile(destino) as pacote_zip:
        pacote_zip.extractall(trabalho)
    os.makedirs(os.path.join(SDK, "cmdline-tools"), exist_ok=True)
    os.replace(os.path.join(trabalho, "cmdline-tools"), os.path.join(SDK, "cmdline-tools", "latest"))
    limpeza.apagar_pasta(trabalho)
    os.remove(destino)


def linha_do_bat(programa, argumentos):
    """A linha de comando para um .bat com cada argumento entre aspas: o cmd
    que roda o .bat parte "platforms;android-35" no ponto e virgula."""
    return " ".join('"%s"' % parte for parte in [programa] + list(argumentos))


def sdkmanager(*argumentos, respostas=""):
    programa = os.path.join(SDK, "cmdline-tools", "latest", "bin", "sdkmanager.bat")
    return subprocess.run(linha_do_bat(programa, ["--sdk_root=" + SDK] + list(argumentos)), input=respostas,
                          text=True, env=ambiente(), capture_output=True)


def preparar_pacotes():
    print("Aceitando as licencas do SDK do Android e baixando o emulador e a imagem (uns 1,5 GB)...", flush=True)
    sdkmanager("--licenses", respostas="y\n" * 20)
    feito = sdkmanager(*PACOTES, respostas="y\n" * 20)
    faltam = [p for p in PACOTES if not os.path.isdir(os.path.join(SDK, *p.split(";")))]
    if feito.returncode != 0 or faltam:
        raise SystemExit("O sdkmanager nao instalou %s:\n%s" % (", ".join(faltam) or "tudo",
                                                               (feito.stdout + feito.stderr)[-2000:]))


def preparar_avd():
    if os.path.isfile(os.path.join(AVD, NOME_DO_AVD + ".ini")):
        return
    os.makedirs(AVD, exist_ok=True)
    programa = os.path.join(SDK, "cmdline-tools", "latest", "bin", "avdmanager.bat")
    feito = subprocess.run(linha_do_bat(programa, ["create", "avd", "-n", NOME_DO_AVD, "-k", IMAGEM, "-d", "pixel_6",
                                                   "--force"]), input="no\n", text=True, env=ambiente(),
                           capture_output=True)
    if feito.returncode != 0:
        raise SystemExit("O avdmanager nao criou o aparelho:\n%s" % (feito.stdout + feito.stderr)[-2000:])
    # Um aparelho modesto, como o tablet da escola: 2 GB de memoria, 2
    # nucleos, tela de celular, e a placa de video pelo processador
    # (SwiftShader: roda sem janela, para o teste automatico).
    config = os.path.join(AVD, NOME_DO_AVD + ".avd", "config.ini")
    with open(config, encoding="utf-8") as arquivo:
        linhas = [l for l in arquivo.read().splitlines()
                  if not l.split("=", 1)[0].strip() in ("hw.ramSize", "hw.cpu.ncore", "hw.gpu.enabled",
                                                       "hw.gpu.mode", "hw.keyboard", "hw.gamepad")]
    linhas += ["hw.ramSize=2048", "hw.cpu.ncore=2", "hw.gpu.enabled=yes", "hw.gpu.mode=swiftshader_indirect",
               "hw.keyboard=yes"]
    with open(config, "w", encoding="utf-8") as arquivo:
        arquivo.write("\n".join(linhas) + "\n")


def principal():
    os.makedirs(BASE, exist_ok=True)
    preparar_jdk()
    preparar_ferramentas()
    preparar_pacotes()
    preparar_avd()
    emulador = os.path.join(SDK, "emulator", "emulator.exe")
    adb = os.path.join(SDK, "platform-tools", "adb.exe")
    print("Pronto. O Android de testes fica em %s." % BASE)
    print("Abrir o aparelho (sem janela):")
    print('  set ANDROID_AVD_HOME=%s' % AVD)
    print('  "%s" -avd %s -no-window -no-audio -no-snapshot -gpu swiftshader_indirect' % (emulador, NOME_DO_AVD))
    print('  "%s" wait-for-device' % adb)
    return 0


if __name__ == "__main__":
    sys.exit(principal())
