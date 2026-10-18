# -*- coding: utf-8 -*-
r"""Prepara o ARENA para Linux: o RetroArch, os nucleos e o Python (item 13).

Por que existe (17/10/2026, item 13 do plano de 15/10): o mesmo pen drive do
ARENA abre no Linux, pelo ARENA.sh. O servidor, a tela, os jogos e os saves
sao os mesmos; mudam tres programas, que vem prontos no pacote e esta
ferramenta poe no lugar:

  1. o RetroArch 1.22.2 para Linux (o mesmo do Windows), o AppImage oficial
     do libretro, em retroarch\RetroArch-Linux-x86_64.AppImage (um arquivo
     so, que roda sem instalar), e os perfis de controle do Linux (udev e
     linuxraw) em retroarch\autoconfig, ao lado dos do Windows;
  2. os nucleos do Linux (.so), so os que o ARENA usa (os mesmos .dll do
     Windows, pelo consoles.json), em retroarch\cores, ao lado dos .dll;
  3. o Python 3.13 portatil para Linux (o python-build-standalone, o mesmo
     que o uv usa), em servidor\python-linux. So os arquivos de verdade: o
     pacote traz atalhos (links) que pen drive exFAT nao aceita, e o ARENA
     chama o python3.13 pelo nome;
  4. as bibliotecas que o RetroArch do Linux pede e que alguns Linux nao
     trazem, em retroarch\bibliotecas-linux (o ARENA so as usa onde faltam,
     ver servidor\plataforma.py): a libjack.so.0 vazia (o Ubuntu 24.04 nao
     tem o JACK; ferramentas\jack_vazio.py) e a libgomp.so.1 do GCC, que o
     nucleo do Dreamcast (Flycast) pede, a do Debian 10 (funciona em todo
     Linux de 2018 para ca);
  5. os emuladores de fora do Linux, nas MESMAS versoes dos do Windows e nas
     mesmas pastas (o ARENA usa a mesma pasta de dados nos dois sistemas,
     servidor\plataforma.py): o PCSX2 2.8.2 (PS2), o RPCS3 0.0.42-20058
     (PS3) e o Xenia Canary 0bd090d (Xbox 360), os AppImage oficiais. O
     GameCube e o Wii vao pelo nucleo do Dolphin (o Dolphin nao publica
     versao portatil para Linux);
  6. os dois nucleos que o 1.22.2 do Linux nao tem: o do Java ME, o .so do
     mesmo FreeJ2ME-Plus 1.52 do .dll do Windows (o zip do projeto traz os
     dois), e o do Apple II (AppleWin), o "nightly" do libretro (so ele tem
     o do Linux). O nightly muda de um dia para o outro no mesmo endereco:
     vale o conferido em 18/10/2026 (a marca fica aqui, e o arquivo, no
     cache de quem monta). Um nightly diferente so entra se alguem conferir
     e confirmar a marca nova (--aceitar-applewin=<marca>); e o Java do Java
     ME para Linux em emuladores\Java\linux, o mesmo Temurin 21 do Windows,
     reduzido com o jlink: o jlink do JDK do Windows monta o Java do Linux
     quando recebe os modulos (jmods) do JDK do Linux da mesma versao.

Cada download confere a marca SHA-256: a do Python, pela lista oficial do
projeto; a do RetroArch (o buildbot nao publica), pela do arquivo baixado em
17/10/2026, gravada aqui. Nao precisa de administrador. Para o .7z, o 7-Zip
(7-zip.org, livre) no computador de quem monta o pacote.

Uso:
    servidor\python\python.exe ferramentas\preparar_linux.py [--sem-externos] [--aceitar-applewin=<marca>]
"""
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "testes"))
sys.path.insert(0, os.path.join(RAIZ, "ferramentas"))
import limpeza  # noqa: E402

CACHE = os.path.join(os.environ.get("LOCALAPPDATA") or tempfile.gettempdir(), "ARENA-montagem")
LUGARES_DO_7ZIP = [r"C:\Program Files\7-Zip\7z.exe", r"C:\Program Files (x86)\7-Zip\7z.exe"]

RETROARCH = {
    "endereco": "https://buildbot.libretro.com/stable/1.22.2/linux/x86_64/RetroArch.7z",
    "arquivo": os.path.join("linux-1.22.2", "RetroArch.7z"),
    "sha256": "7d62da9a21397d6e1b9490785cedbeafd262781b50115076736fbe8a77ef30e9",
    "tamanho": 179361448,
}
NUCLEOS = {
    "endereco": "https://buildbot.libretro.com/stable/1.22.2/linux/x86_64/RetroArch_cores.7z",
    "arquivo": os.path.join("linux-1.22.2", "RetroArch_cores.7z"),
    "sha256": "4b7ed8dc97d4bf035fce182c64b5658c7662e2e9e5d42129538afbd4b6096307",
    "tamanho": 274237400,
}
PYTHON = {
    "endereco": ("https://github.com/astral-sh/python-build-standalone/releases/download/20261013/"
                 "cpython-3.13.16%2B20261013-x86_64-unknown-linux-gnu-install_only_stripped.tar.gz"),
    "arquivo": os.path.join("python-linux", "python-x86_64.tar.gz"),
    # A da lista oficial (SHA256SUMS do lancamento 20261013).
    "sha256": "d0080766b6b74aeb81e1949ef0d9a20e6c17f7b160fb295a69b936ccb17660be",
}
# A libgomp do GCC 8 (Debian 10): o pacote oficial, com a marca da lista do
# proprio Debian (dists/buster/main/binary-amd64/Packages, conferida em
# 17/10/2026). Licenca: GPL 3 com a excecao das bibliotecas do GCC, que
# deixa levar junto de qualquer programa.
LIBGOMP = {
    "endereco": "https://archive.debian.org/debian/pool/main/g/gcc-8/libgomp1_8.3.0-6_amd64.deb",
    "arquivo": os.path.join("linux-bibliotecas", "libgomp1_8.3.0-6_amd64.deb"),
    "sha256": "909fcd28491d7ebecf44ee2e8d0269b600271b0b6d236b19f2c0469cde162d21",
    "tamanho": 75824,
    "dentro": "./usr/lib/x86_64-linux-gnu/libgomp.so.1.0.0",
    "nome": "libgomp.so.1",
}
# Os emuladores de fora do Linux: as mesmas versoes dos do Windows, com a
# marca SHA-256 que o proprio GitHub publica de cada arquivo (conferida em
# 18/10/2026). (pasta dentro de emuladores, endereco, marca, tamanho)
EXTERNOS = [
    (os.path.join("PCSX2", "PCSX2"),
     "https://github.com/PCSX2/pcsx2/releases/download/v2.8.2/pcsx2-v2.8.2-linux-appimage-x64-Qt.AppImage",
     "0c46bb6a88aa2782b10853a7b07cf3387ba99cbef2b966372cd2315b8571abea", 60119544),
    (os.path.join("RPCS3", "RPCS3"),
     "https://github.com/RPCS3/rpcs3-binaries-linux/releases/download/"
     "build-4514ad6216f61ac309f970f29c75fd7d586830dc/rpcs3-v0.0.42-20058-4514ad62_linux64.AppImage",
     "691d017e7b566eb4d4745f2f58dce3dd895467df2c0f1c9be17af3f65b3aa0fa", 94026641),
    (os.path.join("Xenia", "Xenia"),
     "https://github.com/xenia-canary/xenia-canary/releases/download/0bd090d/xenia_canary_linux.AppImage",
     "046bb14ae1a4130eeb237a365706fb6aa6df77323494894f7189e2b7d2cbdaad", 17832440),
]
# Os nucleos que faltam no 1.22.2 do Linux (ver o topo, item 6).
FREEJ2ME = {
    "endereco": "https://github.com/TASEmulators/freej2me-plus/releases/download/1.52/freej2me_libretro-v1.52.zip",
    "arquivo": os.path.join("linux-nucleos", "freej2me_libretro-v1.52.zip"),
    "sha256": "454ca45b0e19e630624f54f9f35ae2e7a0d69df0981bab0d251440eaa8ad9cef",
    "tamanho": 83399,
}
APPLEWIN = {
    "endereco": "https://buildbot.libretro.com/nightly/linux/x86_64/latest/applewin_libretro.so.zip",
    "arquivo": os.path.join("linux-nucleos", "applewin_libretro.so.zip"),
    # O nightly de 17/10/2026 (04:49 GMT), o que foi aberto no ARENA do Linux.
    "sha256": "57fb09796e4316cb238b1c124589de77a9846da2d2f053fb9033fc010e6de063",
    "tamanho": 1508030,
}
# O Java do Java ME (o mesmo de ferramentas\preparar_java.py, 21.0.12.1+1).
JDK_WINDOWS = {
    "endereco": ("https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.12.1%2B1/"
                 "OpenJDK21U-jdk_x64_windows_hotspot_21.0.12.1_1.zip"),
    "arquivo": os.path.join("java", "OpenJDK21U-jdk_x64_windows_hotspot_21.0.12.1_1.zip"),
    "sha256": "f9d6e191ab098c0d416e7d588a24420a8621cd2f4720dab2459b8b7b2d2d8b4e",
    "tamanho": 205073461,
}
JDK_LINUX = {
    "endereco": ("https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.12.1%2B1/"
                 "OpenJDK21U-jdk_x64_linux_hotspot_21.0.12.1_1.tar.gz"),
    "arquivo": os.path.join("java", "OpenJDK21U-jdk_x64_linux_hotspot_21.0.12.1_1.tar.gz"),
    "sha256": "ce79869e1307ed8ee1e2baa86a412b1eb5b75d10a01006d788a6f968bcfaee94",
    "tamanho": 207473347,
}
MODULOS_JAVA = ["java.base", "java.desktop", "java.rmi"]
DENTRO_DO_7Z = "RetroArch-Linux-x86_64"
APPIMAGE = "RetroArch-Linux-x86_64.AppImage"
PERFIS_DE_CONTROLE = ("udev", "linuxraw")
# Do Python, fica de fora o que o ARENA nunca usa: os testes da propria
# linguagem, a tela do IDLE e do Tk, o pip, os cabecalhos de compilar e os
# manuais (uns 40 MB a menos no pen drive).
FORA_DO_PYTHON = ("python/include/", "python/share/", "python/lib/pkgconfig/", "python/lib/python3.13/test/",
                  "python/lib/python3.13/idlelib/", "python/lib/python3.13/tkinter/",
                  "python/lib/python3.13/turtledemo/", "python/lib/python3.13/ensurepip/",
                  "python/lib/python3.13/lib2to3/", "python/lib/python3.13/config-3.13-x86_64-linux-gnu/",
                  "python/lib/libtcl", "python/lib/libtk", "python/lib/tcl", "python/lib/tk", "python/lib/itcl",
                  "python/lib/thread", "python/bin/idle", "python/bin/pydoc", "python/bin/python3-config",
                  "python/bin/python3.13-config")


def marca(caminho):
    resumo = hashlib.sha256()
    with open(caminho, "rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1 << 20), b""):
            resumo.update(bloco)
    return resumo.hexdigest()


def baixado(item):
    """O arquivo do cache, baixado se faltar, com a marca conferida."""
    caminho = os.path.join(CACHE, item["arquivo"])
    if not os.path.isfile(caminho):
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        print("Baixando %s..." % item["endereco"].rsplit("/", 1)[-1], flush=True)
        parcial = caminho + ".baixando"
        with urllib.request.urlopen(item["endereco"], timeout=60) as resposta, open(parcial, "wb") as saida:
            shutil.copyfileobj(resposta, saida, 1 << 20)
        os.replace(parcial, caminho)
    if ("tamanho" in item and os.path.getsize(caminho) != item["tamanho"]) or marca(caminho) != item["sha256"]:
        raise SystemExit("A marca de %s nao confere: o arquivo veio diferente do publicado. Nada foi mudado."
                         % os.path.basename(caminho))
    return caminho


def achar_7zip():
    for lugar in [shutil.which("7z"), shutil.which("7za")] + LUGARES_DO_7ZIP:
        if lugar and os.path.isfile(lugar):
            return lugar
    raise SystemExit("Falta o 7-Zip neste computador (7-zip.org, livre). Instale e rode de novo.")


def tirar_do_7z(sete, arquivo_7z, nomes, destino):
    """Extrai so 'nomes' (com o caminho de dentro do .7z) para 'destino'."""
    r = subprocess.run([sete, "x", arquivo_7z, "-o" + destino, "-y"] + nomes, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("O 7-Zip nao conseguiu abrir %s:\n%s" % (os.path.basename(arquivo_7z),
                                                                    (r.stdout + r.stderr)[-1500:]))


def nucleos_usados():
    """Os .so do Linux dos nucleos que o ARENA usa (os .dll do consoles.json)."""
    with open(os.path.join(RAIZ, "servidor", "consoles.json"), encoding="utf-8") as arquivo:
        plataformas = json.load(arquivo)["plataformas"]
    nomes = set()
    for p in plataformas:
        for campo in ("core", "core_netplay", "core_sem_bios"):
            if p.get(campo):
                nomes.add(os.path.splitext(p[campo])[0] + ".so")
    return sorted(nomes)


def preparar_retroarch(sete, trabalho):
    arquivo_7z = baixado(RETROARCH)
    base = DENTRO_DO_7Z + "/"
    config = base + APPIMAGE + ".home/.config/retroarch/autoconfig/"
    tirar_do_7z(sete, arquivo_7z, [base + APPIMAGE] + [config + p for p in PERFIS_DE_CONTROLE], trabalho)
    pasta_ra = os.path.join(RAIZ, "retroarch")
    shutil.copyfile(os.path.join(trabalho, DENTRO_DO_7Z, APPIMAGE), os.path.join(pasta_ra, APPIMAGE))
    for perfil in PERFIS_DE_CONTROLE:
        origem = os.path.join(trabalho, *config.split("/"), perfil)
        destino = os.path.join(pasta_ra, "autoconfig", perfil)
        if os.path.isdir(destino):
            limpeza.apagar_pasta(destino)
        shutil.copytree(origem, destino)
    quantos = sum(len(os.listdir(os.path.join(pasta_ra, "autoconfig", p))) for p in PERFIS_DE_CONTROLE)
    print("  RetroArch: %s (%.1f MB) e %d perfis de controle do Linux"
          % (APPIMAGE, os.path.getsize(os.path.join(pasta_ra, APPIMAGE)) / 1048576, quantos), flush=True)


def preparar_nucleos(sete, trabalho):
    arquivo_7z = baixado(NUCLEOS)
    usados = nucleos_usados()
    dentro = DENTRO_DO_7Z + "/" + APPIMAGE + ".home/.config/retroarch/cores/"
    tirar_do_7z(sete, arquivo_7z, [dentro + n for n in usados], trabalho)
    origem = os.path.join(trabalho, *dentro.split("/"))
    destino = os.path.join(RAIZ, "retroarch", "cores")
    copiados, faltam = 0, []
    for nome in usados:
        if os.path.isfile(os.path.join(origem, nome)):
            shutil.copyfile(os.path.join(origem, nome), os.path.join(destino, nome))
            copiados += 1
        else:
            faltam.append(nome)
    print("  nucleos do Linux: %d de %d%s" % (copiados, len(usados),
                                             (" (sem versao Linux no 1.22.2: %s)" % ", ".join(faltam)) if faltam else ""),
          flush=True)
    return faltam


def preparar_python(trabalho):
    arquivo = baixado(PYTHON)
    destino = os.path.join(RAIZ, "servidor", "python-linux")
    montando = destino + ".montando"
    if os.path.isdir(montando):
        limpeza.apagar_pasta(montando)
    with tarfile.open(arquivo, "r:gz") as pacote:
        for item in pacote.getmembers():
            nome = item.name
            if not nome.startswith("python/") or any(nome.startswith(f) for f in FORA_DO_PYTHON):
                continue
            if item.issym() or item.islnk():
                continue                    # atalho: pen drive exFAT nao aceita
            alvo = os.path.join(montando, *nome[len("python/"):].split("/"))
            if item.isdir():
                os.makedirs(alvo, exist_ok=True)
            elif item.isfile():
                os.makedirs(os.path.dirname(alvo), exist_ok=True)
                with pacote.extractfile(item) as origem, open(alvo, "wb") as saida:
                    shutil.copyfileobj(origem, saida, 1 << 20)
    for essencial in (("bin", "python3.13"), ("lib", "libpython3.13.so.1.0"), ("lib", "python3.13", "os.py")):
        if not os.path.isfile(os.path.join(montando, *essencial)):
            raise SystemExit("O Python para Linux veio sem %s. Nada foi mudado." % "/".join(essencial))
    if os.path.isdir(destino):
        limpeza.apagar_pasta(destino)
    os.replace(montando, destino)
    total = sum(os.path.getsize(os.path.join(a, n)) for a, _s, ns in os.walk(destino) for n in ns)
    print("  Python 3.13 para Linux: servidor\\python-linux (%.0f MB)" % (total / 1048576), flush=True)


def tirar_do_deb(arquivo_deb, dentro):
    """Os bytes de um arquivo de dentro de um pacote .deb. O .deb e' um
    arquivo "ar" (o formato mais simples que existe: um cabecalho de 60
    bytes antes de cada parte) com os arquivos num data.tar.xz."""
    with open(arquivo_deb, "rb") as arquivo:
        if arquivo.read(8) != b"!<arch>\n":
            raise SystemExit("%s nao e' um pacote .deb." % os.path.basename(arquivo_deb))
        while True:
            cabecalho = arquivo.read(60)
            if len(cabecalho) < 60:
                break
            nome = cabecalho[:16].decode("ascii").strip().rstrip("/")
            tamanho = int(cabecalho[48:58].decode("ascii").strip())
            conteudo = arquivo.read(tamanho)
            if tamanho % 2:
                arquivo.read(1)                 # cada parte comeca em posicao par
            if nome.startswith("data.tar"):
                with tarfile.open(fileobj=io.BytesIO(conteudo)) as pacote:
                    return pacote.extractfile(dentro).read()
    raise SystemExit("%s veio sem %s." % (os.path.basename(arquivo_deb), dentro))


def preparar_bibliotecas():
    import jack_vazio
    pasta = os.path.join(RAIZ, "retroarch", "bibliotecas-linux")
    os.makedirs(pasta, exist_ok=True)
    _caminho, tamanho_jack = jack_vazio.escrever(os.path.join(pasta, "libjack.so.0"))
    dados = tirar_do_deb(baixado(LIBGOMP), LIBGOMP["dentro"])
    with open(os.path.join(pasta, LIBGOMP["nome"]), "wb") as saida:
        saida.write(dados)
    print("  bibliotecas de reserva: libjack.so.0 vazia (%d bytes) e %s (%d KB)"
          % (tamanho_jack, LIBGOMP["nome"], len(dados) // 1024), flush=True)


def preparar_nucleos_que_faltam():
    """O freej2me_libretro.so (do zip do projeto, com a marca) e o
    applewin_libretro.so (o nightly do libretro, conferido como programa do
    Linux)."""
    import zipfile
    cores = os.path.join(RAIZ, "retroarch", "cores")
    with zipfile.ZipFile(baixado(FREEJ2ME)) as pacote:
        dados = pacote.read("freej2me_libretro.so")
    with open(os.path.join(cores, "freej2me_libretro.so"), "wb") as saida:
        saida.write(dados)
    print("  nucleo do Java ME para Linux: freej2me_libretro.so (FreeJ2ME-Plus 1.52)", flush=True)
    applewin = dict(APPLEWIN)
    aceita = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--aceitar-applewin=")), None)
    if aceita:
        # Quem monta conferiu o nightly novo e confirma a marca dele.
        applewin["sha256"] = aceita.lower()
        applewin.pop("tamanho")
    caminho_zip = os.path.join(CACHE, applewin["arquivo"])
    if os.path.isfile(caminho_zip) and marca(caminho_zip) != applewin["sha256"]:
        print("O applewin_libretro.so.zip do cache tem outra marca (%s): baixando de novo." % marca(caminho_zip))
        os.remove(caminho_zip)
    try:
        caminho_zip = baixado(applewin)
    except SystemExit:
        novo = os.path.join(CACHE, applewin["arquivo"])
        raise SystemExit("O nightly do AppleWin mudou desde 18/10/2026 (marca nova: %s). Confira o arquivo\n"
                         "  %s\nantes de usar e, se estiver certo, rode de novo com --aceitar-applewin=<marca nova>.\n"
                         "Nada foi mudado." % (marca(novo) if os.path.isfile(novo) else "?", novo))
    with zipfile.ZipFile(caminho_zip) as pacote:
        dados = pacote.read("applewin_libretro.so")
    if dados[:4] != b"\x7fELF" or b"retro_api_version" not in dados:
        raise SystemExit("O applewin_libretro.so que chegou nao e' um nucleo do Linux. Nada foi mudado.")
    with open(os.path.join(cores, "applewin_libretro.so"), "wb") as saida:
        saida.write(dados)
    print("  nucleo do Apple II para Linux: applewin_libretro.so (nightly de 17/10/2026, marca %s)"
          % hashlib.sha256(dados).hexdigest(), flush=True)


def preparar_java_linux(trabalho):
    """O Java do Java ME para Linux, em emuladores\\Java\\linux (ver o topo)."""
    import zipfile
    jdk_windows = os.path.join(trabalho, "jdk-windows")
    print("  montando o Java do Linux (jlink)...", flush=True)
    with zipfile.ZipFile(baixado(JDK_WINDOWS)) as pacote:
        pacote.extractall(jdk_windows)
    jlink = next(os.path.join(atual, "jlink.exe") for atual, _s, nomes in os.walk(jdk_windows) if "jlink.exe" in nomes)
    jmods = os.path.join(trabalho, "jmods-linux")
    os.makedirs(jmods)
    with tarfile.open(baixado(JDK_LINUX), "r:gz") as pacote:
        for item in pacote.getmembers():
            if item.isfile() and "/jmods/" in item.name and item.name.endswith(".jmod"):
                with pacote.extractfile(item) as origem, open(os.path.join(jmods, os.path.basename(item.name)),
                                                              "wb") as saida:
                    shutil.copyfileobj(origem, saida, 1 << 20)
    destino = os.path.join(RAIZ, "emuladores", "Java", "linux")
    montando = destino + ".montando"
    if os.path.isdir(montando):
        limpeza.apagar_pasta(montando)
    subprocess.run([jlink, "--module-path", jmods, "--add-modules", ",".join(MODULOS_JAVA), "--strip-debug",
                    "--no-header-files", "--no-man-pages", "--compress=zip-9", "--output", montando], check=True)
    with open(os.path.join(montando, "release"), encoding="utf-8") as arquivo:
        release = arquivo.read()
    cabecas = []
    for programa in (("bin", "java"), ("lib", "server", "libjvm.so")):
        with open(os.path.join(montando, *programa), "rb") as arquivo:
            cabecas.append(arquivo.read(4))
    # O release do jlink de outro sistema so diz a versao e os modulos; o
    # que prova que e' do Linux e' o formato dos programas (ELF).
    if 'JAVA_VERSION="21.0.12.1"' not in release or cabecas != [b"\x7fELF"] * 2:
        raise SystemExit("O Java do Linux nao saiu como devia (release: %s). Nada foi mudado." % release[:200])
    if os.path.isdir(destino):
        limpeza.apagar_pasta(destino)
    os.replace(montando, destino)
    total = sum(os.path.getsize(os.path.join(a, n)) for a, _s, ns in os.walk(destino) for n in ns)
    print("  Java do Java ME para Linux: emuladores\\Java\\linux (%.0f MB)" % (total / 1048576), flush=True)


def preparar_externos():
    """Os AppImage dos emuladores de fora, ao lado dos .exe do Windows."""
    for pasta, endereco, sha256, tamanho in EXTERNOS:
        nome = endereco.rsplit("/", 1)[-1]
        origem = baixado({"endereco": endereco, "arquivo": os.path.join("linux-externos", nome),
                          "sha256": sha256, "tamanho": tamanho})
        destino = os.path.join(RAIZ, "emuladores", pasta, nome)
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        if not (os.path.isfile(destino) and os.path.getsize(destino) == tamanho and marca(destino) == sha256):
            shutil.copyfile(origem, destino)
        print("  emulador de fora: emuladores\\%s\\%s (%.0f MB)" % (pasta, nome, tamanho / 1048576), flush=True)


def principal():
    sete = achar_7zip()
    trabalho = tempfile.mkdtemp(prefix="arena_preparar_linux_")
    try:
        print("Preparando o ARENA para Linux...", flush=True)
        preparar_retroarch(sete, os.path.join(trabalho, "ra"))
        faltam = preparar_nucleos(sete, os.path.join(trabalho, "nucleos"))
        preparar_nucleos_que_faltam()
        faltam = [n for n in faltam if not os.path.isfile(os.path.join(RAIZ, "retroarch", "cores", n))]
        preparar_bibliotecas()
        preparar_python(trabalho)
        if "--sem-externos" not in sys.argv:
            preparar_externos()
        preparar_java_linux(trabalho)
        print("Pronto. No Linux, o ARENA abre pelo ARENA.sh.")
        if faltam:
            print("Estes consoles ficam so no Windows (o libretro nao tem o nucleo para Linux): %s" % ", ".join(faltam))
        return 0
    finally:
        limpeza.apagar_pasta(trabalho)


if __name__ == "__main__":
    sys.exit(principal())
