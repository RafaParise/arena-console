# -*- coding: utf-8 -*-
r"""Instala o ARENA num celular Android pelo cabo USB (auditoria 4, 22/10/2026).

Pedido do Rafael (22/10/2026): "eu gostaria que depois da auditoria instale no
meu telefone a versao mais atualizada possivel do arena atraves do cabo usbc
[...] e com todas as bios, emuladores e tudo que tenho localmente". O telefone
dele e' um Galaxy A12 (Android 12), que recusou o APK: "Como o app nao e'
compativel com seu smartphone, ele nao foi instalado" (o mais provavel: o
Android de 32 bits, e o APK do ARENA so tem 64 bits).

O que faz, nesta ordem (nada sem mostrar antes):
  1. acha o adb (o do SDK do ARENA, %LOCALAPPDATA%\ARENA-android\sdk, ou o do
     PATH) e o celular ligado no cabo -- sem celular, explica como ligar a
     Depuracao USB (no Samsung, passo a passo);
  2. le o aparelho: modelo, Android, se e' de 32 ou 64 bits (ro.product.cpu.
     abilist), memoria e tela;
  3. aparelho de 32 bits: o APK do ARENA ainda nao serve. Abre a versao web
     no navegador do celular (rafaparise.github.io/arena-console, docs\WEB.md)
     e para;
  4. 64 bits: instala o APK certo (o montado aqui, em
     %LOCALAPPDATA%\ARENA-android\apk, ou o do Release mais novo do GitHub),
     por cima do que houver (os recordes do aparelho ficam: mesma assinatura);
  5. copia para /sdcard/ARENA o que e' do jogador: as BIOS (BIOS\ e as de
     retroarch\system), os saves e os estados (o progresso), e os jogos dos
     consoles que o RetroArch do celular roda (sem PS2, GameCube, Wii, PS3 e
     Xbox 360, que no ARENA sao emuladores de computador). Mostra o tamanho e
     pergunta antes. A configuracao de imagem do computador NAO vai: o ARENA
     do celular escolhe sozinho pelo aparelho (a nota dele e o desempenho que
     aprende);
  6. abre o ARENA no celular.

Uso:
    servidor\python\python.exe ferramentas\instalar_no_celular.py [--sem-jogos] [--sim]
--sem-jogos  so o app, as BIOS e os saves.
--sim        nao pergunta (copia tudo o que listou).
"""
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACOTE = "io.github.rafaparise.arena"
SITE = "https://rafaparise.github.io/arena-console/"
RELEASE = "https://api.github.com/repos/RafaParise/arena-console/releases/latest"
DESTINO = "/sdcard/ARENA"
# No ARENA, estes sao emuladores de computador (PCSX2, Dolphin, RPCS3, Xenia):
# o RetroArch do celular nao os roda.
SO_NO_COMPUTADOR = {"ps2", "gamecube", "wii", "ps3", "xbox360"}


def achar_adb():
    candidatos = [os.path.join(os.environ.get("LOCALAPPDATA", ""), "ARENA-android", "sdk", "platform-tools",
                               "adb.exe" if os.name == "nt" else "adb")]
    no_path = shutil.which("adb")
    if no_path:
        candidatos.append(no_path)
    return next((c for c in candidatos if c and os.path.isfile(c)), None)


def adb(adb_exe, *argumentos, tempo=120):
    feito = subprocess.run([adb_exe] + list(argumentos), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=tempo)
    return feito.returncode, (feito.stdout or "") + (feito.stderr or "")


def aparelhos(adb_exe):
    """[(serial, estado)] dos aparelhos que o adb ve."""
    _codigo, saida = adb(adb_exe, "devices")
    lista = []
    for linha in saida.splitlines()[1:]:
        partes = linha.split()
        if len(partes) >= 2:
            lista.append((partes[0], partes[1]))
    return lista


COMO_LIGAR = """Nenhum celular pronto no cabo. No celular (Samsung Galaxy):
  1. Configuracoes -> Sobre o telefone -> Informacoes do software;
  2. toque 7 vezes em "Numero de compilacao" (aparece "O modo de desenvolvedor foi ativado");
  3. Configuracoes -> Opcoes do desenvolvedor -> ligue "Depuracao USB";
  4. ligue o cabo; no celular, aparece "Permitir depuracao USB?": marque "Sempre permitir" e toque em Permitir.
Depois rode de novo esta ferramenta."""


def ler_aparelho(adb_exe, serial):
    def prop(nome):
        return adb(adb_exe, "-s", serial, "shell", "getprop", nome)[1].strip()
    memoria = adb(adb_exe, "-s", serial, "shell", "cat", "/proc/meminfo")[1]
    total = next((int(linha.split()[1]) for linha in memoria.splitlines() if linha.startswith("MemTotal:")), 0)
    tela = adb(adb_exe, "-s", serial, "shell", "wm", "size")[1].strip().splitlines()
    return {"modelo": prop("ro.product.model"), "fabricante": prop("ro.product.manufacturer"),
            "android": prop("ro.build.version.release"), "sdk": prop("ro.build.version.sdk"),
            "abis": [a for a in prop("ro.product.cpu.abilist").split(",") if a],
            "abis64": [a for a in prop("ro.product.cpu.abilist64").split(",") if a],
            "processador": prop("ro.soc.model") or prop("ro.board.platform"),
            "memoria_gb": round(total / 1048576.0, 1), "tela": tela[-1] if tela else ""}


def abi_do_apk(aparelho):
    """O APK do ARENA que serve: "arm64-v8a", "x86_64" ou None (32 bits)."""
    for abi in aparelho["abis64"] or aparelho["abis"]:
        if abi in ("arm64-v8a", "x86_64"):
            return abi
    return None


def apk_local(abi):
    pasta = os.path.join(os.environ.get("LOCALAPPDATA", ""), "ARENA-android", "apk")
    achados = sorted(glob.glob(os.path.join(pasta, "*%s*.apk" % abi)), key=os.path.getmtime)
    return [a for a in achados if "teste" not in os.path.basename(a).lower()][-1:] or achados[-1:]


def apk_do_release(abi):
    """Baixa o APK do Release mais novo do GitHub (so https)."""
    with urllib.request.urlopen(RELEASE, timeout=30) as resposta:
        release = json.load(resposta)
    for anexo in release.get("assets", []):
        nome = os.path.basename(str(anexo.get("name", "")))      # so o nome, nunca uma pasta
        if nome.endswith(".apk") and abi in nome and anexo.get("browser_download_url", "").startswith("https://"):
            destino = os.path.join(tempfile.mkdtemp(prefix="arena_apk_"), nome)
            print("Baixando %s (%d MB) do Release %s..." % (nome, anexo.get("size", 0) // 1048576,
                                                           release.get("tag_name", "")))
            urllib.request.urlretrieve(anexo["browser_download_url"], destino)
            return destino
    return None


def o_que_copiar(com_jogos=True):
    """[(pasta do computador, pasta no celular, tamanho em bytes)]."""
    lista = []
    pastas = [os.path.join("BIOS"), os.path.join("retroarch", "system"),
              os.path.join("retroarch", "saves"), os.path.join("retroarch", "states")]
    if com_jogos:
        for pasta in sorted(glob.glob(os.path.join(RAIZ, "jogos", "*", "*"))):
            if os.path.isdir(pasta) and os.path.basename(pasta).lower() not in SO_NO_COMPUTADOR:
                pastas.append(os.path.relpath(pasta, RAIZ))
    for rel in pastas:
        origem = os.path.join(RAIZ, rel)
        if not os.path.isdir(origem):
            continue
        tamanho = sum(os.path.getsize(os.path.join(a, n)) for a, _s, ns in os.walk(origem) for n in ns)
        if tamanho:
            lista.append((origem, DESTINO + "/" + rel.replace("\\", "/"), tamanho))
    return lista


def principal():
    adb_exe = achar_adb()
    if not adb_exe:
        print("Nao achei o adb. Instale o 'Android SDK Platform-Tools' (gratuito, do Google) ou rode "
              "ferramentas\\preparar_android.py.")
        return 2
    prontos = [s for s, estado in aparelhos(adb_exe) if estado == "device"]
    nao_autorizados = [s for s, estado in aparelhos(adb_exe) if estado == "unauthorized"]
    if nao_autorizados and not prontos:
        print("O celular esta no cabo, mas ainda nao deixou: na tela dele, toque em Permitir "
              "(\"Permitir depuracao USB?\") e rode de novo.")
        return 3
    if len(prontos) != 1:
        print(COMO_LIGAR if not prontos else "Mais de um aparelho no cabo: deixe so o celular.")
        return 3
    serial = prontos[0]
    aparelho = ler_aparelho(adb_exe, serial)
    print("Aparelho: %(fabricante)s %(modelo)s, Android %(android)s, %(memoria_gb)s GB, tela %(tela)s, "
          "processador %(processador)s" % aparelho)
    print("  arquiteturas: %s" % (", ".join(aparelho["abis"]) or "?"))
    abi = abi_do_apk(aparelho)
    if not abi:
        print("\nEste Android e' de 32 bits (%s): o APK do ARENA ainda so tem a versao de 64 bits, e e' por"
              " isso que o Android diz que o app nao e' compativel." % ", ".join(aparelho["abis"]))
        print("Abrindo a versao web no navegador do celular (roda sem instalar; docs\\WEB.md): %s" % SITE)
        adb(adb_exe, "-s", serial, "shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", SITE)
        print("No Chrome do celular: menu -> 'Adicionar a tela inicial' deixa o ARENA como app.")
        return 0
    apk = (apk_local(abi) or [None])[0] or apk_do_release(abi)
    if not apk:
        print("Nao achei o APK %s (nem aqui, nem no Release do GitHub)." % abi)
        return 4
    print("\nInstalando %s ..." % os.path.basename(apk))
    codigo, saida = adb(adb_exe, "-s", serial, "install", "-r", apk, tempo=600)
    print(saida.strip().splitlines()[-1] if saida.strip() else "")
    if codigo != 0 or "Success" not in saida:
        print("O Android recusou a instalacao. Se for 'verificacao do desenvolvedor', veja docs\\ANDROID.md.")
        return 5
    copias = o_que_copiar(com_jogos="--sem-jogos" not in sys.argv)
    total = sum(t for _o, _d, t in copias)
    print("\nPara copiar para %s (%.1f GB):" % (DESTINO, total / 1073741824.0))
    for origem, destino, tamanho in copias:
        print("  %-60s %8.1f MB" % (os.path.relpath(origem, RAIZ), tamanho / 1048576.0))
    if copias and ("--sim" in sys.argv or input("Copiar? [s/N] ").strip().lower().startswith("s")):
        for origem, destino, _tamanho in copias:
            adb(adb_exe, "-s", serial, "shell", "mkdir", "-p", destino.rsplit("/", 1)[0])
            codigo, saida = adb(adb_exe, "-s", serial, "push", origem, destino.rsplit("/", 1)[0] + "/", tempo=3600)
            print("  %s %s" % ("ok " if codigo == 0 else "ERRO", os.path.relpath(origem, RAIZ)))
    adb(adb_exe, "-s", serial, "shell", "monkey", "-p", PACOTE, "-c", "android.intent.category.LAUNCHER", "1")
    print("\nPronto: o ARENA abriu no celular. Na primeira vez, toque em Continuar e permita os arquivos;"
          " a pasta %s aparece sozinha." % DESTINO)
    return 0


if __name__ == "__main__":
    sys.exit(principal())
