# -*- coding: utf-8 -*-
r"""
ARENA - em que sistema o ARENA esta rodando, e os nomes que mudam de um para
o outro.

Pedido do Rafael (15/10/2026, item 13 do plano): "uma versao do ARENA para
linux perfeitamente identico sem alterar nada". O ARENA e' o mesmo programa
no Windows e no Linux: o mesmo servidor, a mesma tela, os mesmos jogos e saves
no mesmo pen drive. O que muda e' pouco, e mora aqui:

  - o nome dos programas: retroarch.exe no Windows; no Linux, o AppImage do
    RetroArch (um arquivo so, que roda sem instalar);
  - a extensao dos nucleos: .dll no Windows, .so no Linux (o consoles.json
    guarda o nome do Windows, "fceumm_libretro.dll"; no Linux vira
    "fceumm_libretro.so");
  - o Python que vem junto: servidor\python (Windows) ou servidor/python-linux;
  - o Linux de dentro do Chromebook (o ChromeOS deixa a marca dele), que o
    ARENA reconhece para explicar o que muda la.

O resto do ARENA pergunta aqui, em vez de cada modulo testar o sistema do
seu jeito.
"""
import os
import platform
import sys

WINDOWS = sys.platform.startswith("win")
LINUX = sys.platform.startswith("linux")

# O RetroArch do Linux (stable 1.22.2 do libretro): um AppImage, que o ARENA
# abre direto, sem instalar (ver comando_do_appimage).
APPIMAGE_RETROARCH = "RetroArch-Linux-x86_64.AppImage"
EXTENSAO_DO_NUCLEO = ".dll" if WINDOWS else ".so"


def no_chromebook():
    """O Linux de dentro do Chromebook (Crostini ou o Baguette novo)? O
    ChromeOS deixa a versao dele em /dev/.cros_milestone e as ferramentas da
    ponte (garcon, sommelier) em /opt/google/cros-containers."""
    if not LINUX:
        return False
    return os.path.exists("/dev/.cros_milestone") or os.path.isdir("/opt/google/cros-containers")


def nome_do_sistema():
    """'windows', 'chromeos' (o Linux do Chromebook) ou 'linux'."""
    if WINDOWS:
        return "windows"
    if no_chromebook():
        return "chromeos"
    return "linux" if LINUX else sys.platform


def descricao():
    """O nome do sistema para a tela ('Windows 11', 'Debian 13 (Linux 6.6)')."""
    if WINDOWS:
        return "%s %s" % (platform.system(), platform.release())
    nome = ""
    try:
        with open("/etc/os-release", encoding="utf-8") as arquivo:
            campos = dict(linha.rstrip("\n").split("=", 1) for linha in arquivo if "=" in linha)
        nome = campos.get("PRETTY_NAME", "").strip('"')
    except (OSError, ValueError):
        nome = ""
    nucleo = platform.release().split("-")[0]
    base = "%s (Linux %s)" % (nome, nucleo) if nome else "Linux %s" % nucleo
    return ("ChromeOS, " + base) if no_chromebook() else base


def arquivo_do_nucleo(nome):
    """'fceumm_libretro.dll' (o nome do consoles.json) -> o arquivo deste
    sistema: o mesmo no Windows, 'fceumm_libretro.so' no Linux."""
    if not nome or WINDOWS:
        return nome
    base, extensao = os.path.splitext(nome)
    return base + EXTENSAO_DO_NUCLEO if extensao.lower() in (".dll", ".so", ".dylib") else nome


CAMPOS_DE_NUCLEO = ("core", "core_netplay", "core_sem_bios")


def nucleos_deste_sistema(plataformas):
    """O catalogo (consoles.json) com o nome dos nucleos deste sistema: no
    Linux, cada "core", "core_netplay" e "core_sem_bios" passa de .dll para
    .so. No Windows, devolve a mesma lista. Quem le o consoles.json chama
    isto uma vez, e o resto do ARENA nem fica sabendo."""
    if WINDOWS:
        return plataformas
    for p in plataformas:
        for campo in CAMPOS_DE_NUCLEO:
            if p.get(campo):
                p[campo] = arquivo_do_nucleo(p[campo])
    return plataformas


def nome_curto_do_nucleo(arquivo):
    """'swanstation_libretro.dll' ou '.so' -> 'swanstation'."""
    base = os.path.basename(arquivo or "")
    for fim in ("_libretro.dll", "_libretro.so", "_libretro.dylib"):
        if base.lower().endswith(fim):
            return base[:-len(fim)].lower()
    return base.lower()


def executavel_do_retroarch(pasta_retroarch):
    """O programa do RetroArch deste sistema, dentro da pasta retroarch."""
    if WINDOWS:
        return os.path.join(pasta_retroarch, "retroarch.exe")
    return os.path.join(pasta_retroarch, APPIMAGE_RETROARCH)


def python_que_veio_junto(pasta_servidor):
    """O Python que vem no pacote para este sistema (pode nao existir)."""
    if WINDOWS:
        return os.path.join(pasta_servidor, "python", "python.exe")
    return os.path.join(pasta_servidor, "python-linux", "bin", "python3.13")
