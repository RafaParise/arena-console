# -*- coding: utf-8 -*-
r"""Compila o RetroArch 1.22.2 do Android com o remendo do ARENA (item 14).

O APK do ARENA e' o RetroArch.apk oficial (ferramentas\montar_android.py)
com uma troca so: a biblioteca do RetroArch (lib\<abi>\libretroarch-activity.so)
sai do codigo oficial da mesma versao com os remendos de android\retroarch\
(em ordem de nome):
  - arena-args.patch: o RetroArch do Android recebe a mesma linha de comando do
    Windows e do Linux, e com ela o jogo em rede (--host e --connect): o oficial
    do Android so le alguns extras da intent (ROM, LIBRETRO, CONFIGFILE...) e nao
    tem como pedir partida em rede;
  - arena-controles.patch: os controles ja ligados entram na ordem em que foram
    CONECTADOS (o primeiro conectado e' o jogador 1); o oficial registra quem
    apertar primeiro.

Do codigo oficial ate a biblioteca:
  1. o codigo da etiqueta v1.22.2 do GitHub do libretro, conferido pela
     marca, sai para %LOCALAPPDATA%\ARENA-android\retroarch-1.22.2 (sem a
     pasta pkg\apple, a unica com links, que o Android nao usa);
  2. o remendo entra com o git apply, so se encaixar inteiro;
  3. o NDK 22.0.7026061 compila, com o Android.mk do proprio RetroArch, como
     o build.gradle dele faz. E' o mesmo NDK da biblioteca oficial (a nota
     .note.android.ident dela diz r22, 7026061), para a mesma versao minima
     do Android (21) e com a versao do git da etiqueta (69a4f0e), mais
     "-arena": a tela de Informacoes do RetroArch mostra que e' a remendada.

A biblioteca pronta fica guardada com a marca do codigo e do remendo: so
compila de novo quando um dos dois muda. Fora do git e do pacote, como o
SDK (ferramentas\preparar_android.py, que tambem instala o NDK).

Uso:
    servidor\python\python.exe ferramentas\compilar_retroarch_android.py [--abi x86_64]
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "testes"))
sys.path.insert(0, os.path.join(RAIZ, "ferramentas"))
import limpeza  # noqa: E402
import preparar_android as sdk  # noqa: E402  (o SDK e o NDK, em %LOCALAPPDATA%\ARENA-android)
import preparar_linux  # noqa: E402  (o cache e o download com a marca)

FONTE = {
    "endereco": "https://github.com/libretro/RetroArch/archive/refs/tags/v1.22.2.tar.gz",
    "arquivo": os.path.join("android", "RetroArch-1.22.2.tar.gz"),
    "sha256": "245ef18c8fa8fbd9fbb5eb25cf43e17c6aace2f95c1ed99873cbd794012bb232",   # baixado em 18/10/2026
    "tamanho": 71629881,
}
DENTRO_DO_TAR = "RetroArch-1.22.2/"
PASTA_DOS_REMENDOS = os.path.join(RAIZ, "android", "retroarch")


def remendos():
    """Os remendos do ARENA para o RetroArch, em ordem de nome."""
    return [os.path.join(PASTA_DOS_REMENDOS, n) for n in sorted(os.listdir(PASTA_DOS_REMENDOS)) if n.endswith(".patch")]
NDK = os.path.join(sdk.SDK, *sdk.NDK.split(";"))
VERSAO_DO_GIT = "69a4f0e-arena"     # a etiqueta v1.22.2 e' o commit 69a4f0ea1e8a...
CODIGO = os.path.join(sdk.BASE, "retroarch-1.22.2")
OBJETOS = os.path.join(sdk.BASE, "retroarch-obj")
PRONTAS = os.path.join(sdk.BASE, "retroarch-lib")
ABIS = ["arm64-v8a", "x86_64"]
# O que a biblioteca oficial pede ao Android (llvm-readelf -d): a remendada
# tem de pedir o mesmo, nem mais nem menos.
BIBLIOTECAS_DO_ANDROID = {"libandroid.so", "libEGL.so", "libGLESv2.so", "liblog.so", "libdl.so",
                          "libOpenSLES.so", "libz.so", "libc.so", "libm.so"}


def marca_do_remendo():
    """Uma marca so para todos os remendos (nome e conteudo de cada um, em ordem)."""
    juntas = "|".join("%s=%s" % (os.path.basename(r), preparar_linux.marca(r)) for r in remendos())
    return hashlib.sha256(juntas.encode("utf-8")).hexdigest()


def marca_esperada():
    return {"fonte": FONTE["sha256"], "remendo": marca_do_remendo(), "ndk": sdk.NDK, "git": VERSAO_DO_GIT}


def ler_marca(arquivo):
    try:
        with open(arquivo, encoding="utf-8") as entrada:
            return json.load(entrada)
    except (OSError, ValueError):
        return None


def gravar_marca(arquivo, marca):
    with open(arquivo, "w", encoding="utf-8") as saida:
        json.dump(marca, saida, indent=1)


def codigo_remendado():
    """A pasta com o codigo da v1.22.2 e o remendo aplicado (refeita so se
    o codigo ou o remendo mudarem)."""
    marca = {"fonte": FONTE["sha256"], "remendo": marca_do_remendo()}
    arquivo_da_marca = os.path.join(CODIGO, ".arena-remendo.json")
    if ler_marca(arquivo_da_marca) == marca:
        return CODIGO
    pacote = preparar_linux.baixado(FONTE)
    montando = CODIGO + ".montando"
    for velha in (montando, CODIGO):
        if os.path.isdir(velha):
            limpeza.apagar_pasta(velha)
    print("  tirando o codigo do RetroArch 1.22.2...", flush=True)
    with tarfile.open(pacote) as tar:
        membros = []
        for membro in tar.getmembers():
            if not membro.name.startswith(DENTRO_DO_TAR) or membro.issym() or membro.islnk():
                continue
            membro.name = membro.name[len(DENTRO_DO_TAR):]
            if not membro.name or membro.name.startswith("pkg/apple/"):
                continue
            membros.append(membro)
        tar.extractall(montando, members=membros, filter="data")
    # O git apply sem repositorio em volta: o GIT_CEILING_DIRECTORIES impede
    # que ele ache um repositorio numa pasta de cima.
    ambiente = dict(os.environ, GIT_CEILING_DIRECTORIES=os.path.dirname(montando))
    for remendo in remendos():
        for passo in (["--check"], []):
            feito = subprocess.run(["git", "apply"] + passo + ["--verbose", remendo], cwd=montando, env=ambiente,
                                   capture_output=True, text=True)
            if feito.returncode != 0:
                raise SystemExit("O remendo %s do ARENA nao encaixa no RetroArch 1.22.2:\n%s"
                                 % (os.path.basename(remendo), (feito.stdout + feito.stderr)[-2000:]))
    gravar_marca(os.path.join(montando, ".arena-remendo.json"), marca)
    os.replace(montando, CODIGO)
    return CODIGO


def ferramenta_do_ndk(nome):
    return os.path.join(NDK, "toolchains", "llvm", "prebuilt", "windows-x86_64", "bin", nome)


def bibliotecas_pedidas(biblioteca):
    """As bibliotecas do Android que o .so pede (as linhas NEEDED)."""
    feito = subprocess.run([ferramenta_do_ndk("llvm-readelf.exe"), "-d", biblioteca], capture_output=True,
                           text=True, check=True)
    return {linha.split("[", 1)[1].split("]", 1)[0] for linha in feito.stdout.splitlines() if "(NEEDED)" in linha}


def conferir(biblioteca):
    """A biblioteca compilada tem o remendo e pede ao Android o mesmo que a
    oficial."""
    with open(biblioteca, "rb") as arquivo:
        dados = arquivo.read()
    if (b"[ENV] Command line (ARGS)" not in dados or b"[ARENA] Controles na ordem" not in dados
            or VERSAO_DO_GIT.encode() not in dados):
        raise SystemExit("A biblioteca compilada nao tem os remendos do ARENA: %s" % biblioteca)
    pedidas = bibliotecas_pedidas(biblioteca)
    if pedidas != BIBLIOTECAS_DO_ANDROID:
        raise SystemExit("A biblioteca compilada pede ao Android outras bibliotecas que a oficial: %s"
                         % ", ".join(sorted(pedidas ^ BIBLIOTECAS_DO_ANDROID)))


def compilar(abi):
    codigo = codigo_remendado()
    jni = os.path.join(codigo, "pkg", "android", "phoenix-common", "jni")
    objetos = os.path.join(OBJETOS, abi)
    saida = os.path.join(OBJETOS, abi + "-lib")
    for velha in (objetos, saida):
        if os.path.isdir(velha):
            limpeza.apagar_pasta(velha)
    print("  compilando o RetroArch remendado para %s (uns minutos)..." % abi, flush=True)
    inicio = time.monotonic()
    # Os mesmos parametros que o plugin do Android passa ao ndk-build a partir
    # do build.gradle do RetroArch (o -j dele e' o numero de processadores).
    argumentos = ["NDK_PROJECT_PATH=null", "APP_BUILD_SCRIPT=" + os.path.join(jni, "Android.mk"),
                  "NDK_APPLICATION_MK=" + os.path.join(jni, "Application.mk"), "APP_ABI=" + abi,
                  "APP_PLATFORM=android-21", "NDK_OUT=" + objetos, "NDK_LIBS_OUT=" + saida,
                  "NDK_DEBUG=0", "GIT_VERSION=" + VERSAO_DO_GIT, "-j%d" % (os.cpu_count() or 2)]
    registro = os.path.join(OBJETOS, "compilar-%s.txt" % abi)
    os.makedirs(OBJETOS, exist_ok=True)
    with open(registro, "w", encoding="utf-8", errors="replace") as saida_do_registro:
        feito = subprocess.run(sdk.linha_do_bat(os.path.join(NDK, "ndk-build.cmd"), argumentos), cwd=jni,
                               stdout=saida_do_registro, stderr=subprocess.STDOUT, env=sdk.ambiente())
    biblioteca = os.path.join(saida, abi, "libretroarch-activity.so")
    if feito.returncode != 0 or not os.path.isfile(biblioteca):
        with open(registro, encoding="utf-8", errors="replace") as entrada:
            final = entrada.read()[-3000:]
        raise SystemExit("O NDK nao compilou o RetroArch para %s (registro em %s):\n%s" % (abi, registro, final))
    conferir(biblioteca)
    print("  compilado em %.0f s (%.1f MB)" % (time.monotonic() - inicio, os.path.getsize(biblioteca) / 1048576),
          flush=True)
    return biblioteca


def biblioteca(abi):
    """O libretroarch-activity.so remendado desta ABI, compilado so se o
    codigo, o remendo, o NDK ou a versao mudaram."""
    if not os.path.isfile(os.path.join(NDK, "ndk-build.cmd")):
        raise SystemExit("Falta o NDK do Android: rode antes o ferramentas\\preparar_android.py.")
    pronta = os.path.join(PRONTAS, abi, "libretroarch-activity.so")
    arquivo_da_marca = pronta + ".arena.json"
    if os.path.isfile(pronta) and ler_marca(arquivo_da_marca) == marca_esperada():
        return pronta
    compilada = compilar(abi)
    os.makedirs(os.path.dirname(pronta), exist_ok=True)
    shutil.copyfile(compilada, pronta + ".parcial")
    os.replace(pronta + ".parcial", pronta)
    gravar_marca(arquivo_da_marca, marca_esperada())
    limpeza.apagar_pasta(os.path.join(OBJETOS, abi))
    limpeza.apagar_pasta(os.path.join(OBJETOS, abi + "-lib"))
    return pronta


def principal():
    abis = [sys.argv[sys.argv.index("--abi") + 1]] if "--abi" in sys.argv else ABIS
    for abi in abis:
        print("%s: %s" % (abi, biblioteca(abi)), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(principal())
