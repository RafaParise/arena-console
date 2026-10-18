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
import shutil
import subprocess
import sys
import urllib.parse

WINDOWS = sys.platform.startswith("win")
LINUX = sys.platform.startswith("linux")

# O RetroArch do Linux (stable 1.22.2 do libretro): um AppImage, que o ARENA
# abre direto, sem instalar (ver comando_do_appimage).
APPIMAGE_RETROARCH = "RetroArch-Linux-x86_64.AppImage"


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
    return base + ".so" if extensao.lower() in (".dll", ".so", ".dylib") else nome


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


class SemGerenciadorDeArquivos(OSError):
    """Linux sem nenhum jeito conhecido de abrir uma pasta (sem o xdg-open e
    sem o gio): quem chamou mostra o caminho para a pessoa abrir sozinha."""


def _sem_janela():
    return {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}


def abrir_pasta(pasta):
    """Abre a pasta no gerenciador de arquivos deste sistema: o Explorador
    no Windows; no Linux, o do proprio computador (Arquivos, Dolphin, Nemo,
    Thunar...), pelo xdg-open, o jeito padrao do freedesktop, ou pelo gio."""
    if WINDOWS:
        os.startfile(pasta)
        return
    for programa in (["xdg-open"], ["gio", "open"]):
        if shutil.which(programa[0]):
            subprocess.Popen(programa + [pasta], start_new_session=True, **_sem_janela())
            return
    raise SemGerenciadorDeArquivos("sem xdg-open nem gio")


# Linux: o pedido "mostre estes arquivos" do freedesktop (FileManager1), que
# o Arquivos do GNOME, o Dolphin, o Nemo, o Caja e o Thunar entendem: abrem a
# pasta com o arquivo ja marcado, como o explorer /select do Windows. Pelo
# gdbus (do GLib) ou pelo dbus-send; sem nenhum dos dois (ou sem gerenciador
# que entenda), abre so a pasta. Roda num sh a parte: o servidor nao espera.
_MOSTRAR_NO_LINUX = (
    "gdbus call --session --dest org.freedesktop.FileManager1 --object-path /org/freedesktop/FileManager1"
    " --method org.freedesktop.FileManager1.ShowItems \"['$1']\" \"''\" >/dev/null 2>&1"
    " || dbus-send --session --print-reply --dest=org.freedesktop.FileManager1 --type=method_call"
    " /org/freedesktop/FileManager1 org.freedesktop.FileManager1.ShowItems \"array:string:$1\" string:"
    " >/dev/null 2>&1"
    " || xdg-open \"$2\" >/dev/null 2>&1 || gio open \"$2\"")


def mostrar_arquivo(arquivo):
    """Abre a pasta do arquivo com ele marcado: quem nunca usou computador ve
    qual arquivo levar. No Windows, o explorer /select."""
    if WINDOWS:
        subprocess.Popen(["explorer.exe", "/select,", arquivo])
        return
    if not any(shutil.which(p) for p in ("gdbus", "dbus-send", "xdg-open", "gio")):
        raise SemGerenciadorDeArquivos("sem gdbus, dbus-send, xdg-open nem gio")
    completo = os.path.abspath(arquivo)
    endereco = "file://" + urllib.parse.quote(completo)
    subprocess.Popen(["sh", "-c", _MOSTRAR_NO_LINUX, "sh", endereco, os.path.dirname(completo)],
                     start_new_session=True, **_sem_janela())


# ---------------------------------------------------------------------------
# Os motores do RetroArch de cada sistema
# ---------------------------------------------------------------------------
# O mesmo retroarch.cfg e as mesmas opcoes do ARENA passam pelos dois
# sistemas (o pen drive vai do Windows para o Linux e volta). Alguns motores
# so existem num deles: o som WASAPI e o controle XInput sao do Windows; o
# PulseAudio e o udev, do Linux. O valor que so existe no outro sistema vira
# o equivalente deste; o que existe nos dois (vulkan, glcore, sdl2...) fica
# como esta. Sem isto, o RetroArch do Linux procuraria o "wasapi", nao
# acharia, e abriria o jogo sem som.
MOTORES_SO_DO_WINDOWS = {
    "video_driver": ("d3d9", "d3d10", "d3d11", "d3d12", "gdi"),
    "input_driver": ("dinput", "raw", "winraw"),
    "input_joypad_driver": ("xinput", "dinput"),
    "audio_driver": ("wasapi", "xaudio", "dsound"),
    "microphone_driver": ("wasapi",),
    "midi_driver": ("winmm",),
}
MOTORES_SO_DO_LINUX = {
    "video_driver": ("xvideo", "drm"),
    "input_driver": ("udev", "linuxraw", "x", "wayland"),
    "input_joypad_driver": ("udev", "linuxraw"),
    "audio_driver": ("alsa", "alsathread", "tinyalsa", "pulse", "pipewire", "jack", "oss"),
    "microphone_driver": ("alsa", "alsathread", "pipewire"),
    "midi_driver": ("alsa",),
}
# No Windows, o que o ARENA sempre usou.
MOTORES_DO_WINDOWS = {"video_driver": "d3d11", "input_driver": "dinput", "input_joypad_driver": "xinput",
                      "audio_driver": "wasapi", "microphone_driver": "wasapi", "midi_driver": "winmm"}
# No Linux: o glcore no lugar do d3d11 (o seguro, quando o Vulkan nao
# serve); o teclado pela janela (o "x": o RetroArch troca sozinho pelo do
# Wayland quando a tela e' Wayland); o controle pelo udev (o padrao do Linux,
# que reconhece o controle ligado com o jogo aberto); o som pelo
# motor_de_som_do_linux.
MOTORES_DO_LINUX = {"video_driver": "glcore", "input_driver": "x", "input_joypad_driver": "udev",
                    "microphone_driver": "alsa", "midi_driver": "alsa"}


def motor_de_som_do_linux():
    """pulse quando ha o servidor de som do PulseAudio (ou o do PipeWire, que
    fala como ele: o padrao do Ubuntu, do Fedora e do Mint de agora); senao,
    alsa, direto na placa de som. O RetroArch que nao consegue abrir o som
    nao tenta outro: o jogo abriria mudo."""
    if os.environ.get("PULSE_SERVER"):
        return "pulse"
    pasta = os.environ.get("XDG_RUNTIME_DIR") or ("/run/user/%d" % os.getuid() if hasattr(os, "getuid") else "")
    if pasta and os.path.exists(os.path.join(pasta, "pulse", "native")):
        return "pulse"
    return "alsa"


def motores_deste_sistema(opcoes):
    """As opcoes do RetroArch ({chave: valor}) com os motores deste sistema
    (ver acima). Troca no proprio dicionario e o devolve."""
    estrangeiros = MOTORES_SO_DO_LINUX if WINDOWS else MOTORES_SO_DO_WINDOWS
    for chave, valores in estrangeiros.items():
        if str(opcoes.get(chave, "")).strip().lower() in valores:
            if WINDOWS:
                opcoes[chave] = MOTORES_DO_WINDOWS[chave]
            elif chave == "audio_driver":
                opcoes[chave] = motor_de_som_do_linux()
            else:
                opcoes[chave] = MOTORES_DO_LINUX[chave]
    return opcoes
