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
     Linux de 2018 para ca).

Cada download confere a marca SHA-256: a do Python, pela lista oficial do
projeto; a do RetroArch (o buildbot nao publica), pela do arquivo baixado em
17/10/2026, gravada aqui. Nao precisa de administrador. Para o .7z, o 7-Zip
(7-zip.org, livre) no computador de quem monta o pacote.

Uso:
    servidor\python\python.exe ferramentas\preparar_linux.py
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


def principal():
    sete = achar_7zip()
    trabalho = tempfile.mkdtemp(prefix="arena_preparar_linux_")
    try:
        print("Preparando o ARENA para Linux...", flush=True)
        preparar_retroarch(sete, os.path.join(trabalho, "ra"))
        faltam = preparar_nucleos(sete, os.path.join(trabalho, "nucleos"))
        preparar_bibliotecas()
        preparar_python(trabalho)
        print("Pronto. No Linux, o ARENA abre pelo ARENA.sh.")
        if faltam:
            print("Estes consoles ficam so no Windows (o libretro nao tem o nucleo para Linux): %s" % ", ".join(faltam))
        return 0
    finally:
        limpeza.apagar_pasta(trabalho)


if __name__ == "__main__":
    sys.exit(principal())
