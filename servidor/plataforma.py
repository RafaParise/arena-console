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
import threading
import urllib.parse

WINDOWS = sys.platform.startswith("win")
LINUX = sys.platform.startswith("linux")

# O RetroArch do Linux (stable 1.22.2 do libretro): um AppImage, um arquivo
# so que roda sem instalar (ver retroarch_que_roda).
APPIMAGE_RETROARCH = "RetroArch-Linux-x86_64.AppImage"
# O nome do programa do RetroArch deste sistema, para as frases da tela, e o
# conferidor do pacote (o VERIFICAR.bat do Windows, o VERIFICAR.sh do Linux).
NOME_DO_RETROARCH = "retroarch.exe" if WINDOWS else APPIMAGE_RETROARCH
VERIFICAR = "VERIFICAR.bat" if WINDOWS else "VERIFICAR.sh"
# As bibliotecas que o RetroArch do Linux pede e que alguns Linux nao trazem
# (ferramentas\preparar_linux.py poe aqui): entram so onde faltam.
PASTA_DAS_BIBLIOTECAS = "bibliotecas-linux"


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
    return os.path.join(pasta_retroarch, "retroarch.exe" if WINDOWS else APPIMAGE_RETROARCH)


# ---------------------------------------------------------------------------
# O RetroArch do Linux, pronto para rodar
# ---------------------------------------------------------------------------
# O AppImage se abre sozinho so com o FUSE 2, que o Ubuntu deixou de trazer
# no 22.04 (o 24.04 tambem nao tem), e o pen drive FAT32 nem deixa executar
# programa nenhum. Entao, na primeira vez, o ARENA tira o RetroArch de dentro
# do AppImage (o proprio AppImage faz isso, com --appimage-extract: sem FUSE
# e sem administrador) para a pasta de cache da conta,
# ~/.cache/arena/retroarch-<tamanho do AppImage>, e dali em diante abre
# direto de la. Tirar de novo so quando o AppImage mudar (outro tamanho).
# Os jogos, os saves e a configuracao continuam no pen drive.
_TRAVA_DO_RETROARCH = threading.Lock()


def pasta_de_cache():
    """Linux: ~/.cache/arena (ou a do XDG_CACHE_HOME), o lugar padrao do
    freedesktop para o que se pode refazer a qualquer hora."""
    base = os.environ.get("XDG_CACHE_HOME") or os.path.join(os.path.expanduser("~"), ".cache")
    return os.path.join(base, "arena")


def _roda(programa):
    return os.path.isfile(programa) and os.access(programa, os.X_OK)


def _apagar(pasta):
    try:
        if os.path.isdir(pasta):
            shutil.rmtree(pasta)
    except OSError as falha:
        print("[ARENA] Nao consegui apagar %s: %s" % (pasta, falha))


def _tirar_do_appimage(appimage, destino):
    """Tira o programa de dentro do AppImage para 'destino'. A copia do
    AppImage vai antes para o cache: no pen drive ele pode nao ter permissao
    de executar. As copias de um AppImage antigo do mesmo programa saem."""
    montando = "%s.montando-%d" % (destino, os.getpid())
    _apagar(montando)
    os.makedirs(montando)
    try:
        copia = os.path.join(montando, "RetroArch.AppImage")
        shutil.copyfile(appimage, copia)
        os.chmod(copia, 0o755)
        resultado = subprocess.run([copia, "--appimage-extract"], cwd=montando, capture_output=True,
                                   timeout=600)
        extraido = os.path.join(montando, "squashfs-root")
        if resultado.returncode != 0 or not _roda(os.path.join(extraido, "AppRun")):
            raise OSError("o AppImage nao se abriu: %s"
                          % (resultado.stderr or resultado.stdout).decode("utf-8", "replace")[-300:].strip())
        _apagar(destino)
        os.replace(extraido, destino)
    finally:
        _apagar(montando)
    prefixo = os.path.basename(destino).rsplit("-", 1)[0] + "-"
    for nome in os.listdir(os.path.dirname(destino)):
        velho = os.path.join(os.path.dirname(destino), nome)
        if nome.startswith(prefixo) and nome[len(prefixo):].isdigit() and velho != destino:
            _apagar(velho)


def _bibliotecas_do_sistema():
    """Os nomes das bibliotecas que este Linux acha sozinho (o ldconfig -p,
    que fica no /sbin: fora do PATH de quem nao e' administrador)."""
    so_64 = platform.machine() == "x86_64"
    for programa in ("/sbin/ldconfig", "/usr/sbin/ldconfig", shutil.which("ldconfig") or ""):
        if not programa or not os.path.isfile(programa):
            continue
        try:
            saida = subprocess.run([programa, "-p"], capture_output=True, text=True, timeout=30).stdout
        except (OSError, subprocess.SubprocessError):
            continue
        return {linha.split()[0] for linha in saida.splitlines()
                if " => " in linha and (not so_64 or "x86-64" in linha)}
    return set()


def _completar_bibliotecas(destino, pasta_bibliotecas):
    """Poe ao lado das bibliotecas do RetroArch (usr/lib, que o AppRun ja
    procura primeiro) so as que este Linux nao tem. A marca guarda a lista:
    com bibliotecas novas no pacote, confere de novo."""
    try:
        nomes = sorted(n for n in os.listdir(pasta_bibliotecas) if ".so" in n)
    except OSError:
        return
    marca = os.path.join(destino, ".arena-bibliotecas")
    try:
        with open(marca, encoding="utf-8") as arquivo:
            if arquivo.read().split() == nomes:
                return
    except OSError:
        pass
    do_sistema = _bibliotecas_do_sistema()
    for nome in nomes:
        alvo = os.path.join(destino, "usr", "lib", nome)
        if nome not in do_sistema and not os.path.exists(alvo):
            shutil.copyfile(os.path.join(pasta_bibliotecas, nome), alvo)
    with open(marca, "w", encoding="utf-8") as arquivo:
        arquivo.write("\n".join(nomes) + "\n")


def appimage_que_roda(appimage, nome, pasta_bibliotecas=None):
    """Linux: o programa que abre o AppImage 'appimage' (o AppRun da copia
    tirada dele em ~/.cache/arena/<nome>-<tamanho>, ver acima), preparando a
    copia na primeira vez. Se nao der, o proprio AppImage (com o FUSE 2,
    ele ainda abre). 'pasta_bibliotecas': as de reserva (so o RetroArch)."""
    try:
        tamanho = os.path.getsize(appimage)
    except OSError:
        return appimage
    destino = os.path.join(pasta_de_cache(), "%s-%d" % (nome, tamanho))
    programa = os.path.join(destino, "AppRun")
    with _TRAVA_DO_RETROARCH:
        if not _roda(programa):
            try:
                _tirar_do_appimage(appimage, destino)
            except (OSError, subprocess.SubprocessError) as falha:
                print("[ARENA] Nao consegui preparar o %s do Linux (%s). Abrindo o AppImage direto."
                      % (nome, falha))
                return appimage
        if pasta_bibliotecas:
            try:
                _completar_bibliotecas(destino, pasta_bibliotecas)
            except OSError as falha:
                print("[ARENA] Nao consegui completar as bibliotecas do %s: %s" % (nome, falha))
    return programa


def retroarch_que_roda(appimage):
    """Linux: o programa que abre o RetroArch (appimage_que_roda, com as
    bibliotecas de reserva). No Windows, o mesmo."""
    if WINDOWS:
        return appimage
    return appimage_que_roda(appimage, "retroarch",
                             os.path.join(os.path.dirname(appimage), PASTA_DAS_BIBLIOTECAS))


def comando_do_retroarch(executavel, arquivo_cfg):
    """O comeco da linha de comando do RetroArch. No Windows, so o
    retroarch.exe: ele le o retroarch.cfg da propria pasta. No Linux, o
    RetroArch procuraria a configuracao em ~/.config/retroarch; o --config
    manda usar a do ARENA, a mesma do Windows, no pen drive."""
    if WINDOWS:
        return [executavel]
    return [retroarch_que_roda(executavel), "--config", arquivo_cfg]


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


# ---------------------------------------------------------------------------
# Os emuladores de fora no Linux
# ---------------------------------------------------------------------------
# O programa do Linux fica na MESMA pasta do de Windows (emuladores\PCSX2\
# PCSX2, emuladores\RPCS3\RPCS3...) e le e grava os MESMOS arquivos: a BIOS,
# os memory cards, a configuracao que o ARENA completa e os saves. No
# Windows, cada um faz isso pelo modo portatil (o portable.txt ao lado do
# .exe). No Linux:
#   - o PCSX2 e o RPCS3 guardam tudo em $XDG_CONFIG_HOME/PCSX2 e
#     $XDG_CONFIG_HOME/rpcs3: o ARENA aponta o XDG_CONFIG_HOME para a pasta
#     de cima (emuladores\PCSX2), e a pasta de dados vira a mesma do Windows
#     (no pen drive FAT32, exFAT ou NTFS, "rpcs3" e "RPCS3" sao a mesma
#     pasta);
#   - o Xenia recebe a pasta pelo --storage_root, e o Dolphin pelo -u (a
#     pasta User, a mesma do Windows).

def dados_do_externo(nome, caminho):
    """(caminho para a configuracao, variaveis do ambiente, argumentos a mais)
    do emulador de fora 'nome' cujo programa esta em 'caminho'. A pasta do
    "caminho para a configuracao" e' onde o emulador le e grava (o
    graficos.py escreve la). No Windows: (caminho, {}, [])."""
    if WINDOWS or not caminho:
        return caminho, {}, []
    pasta = os.path.dirname(caminho)
    acima = os.path.dirname(pasta)
    programa = os.path.basename(caminho)
    if nome == "PCSX2":
        return os.path.join(acima, "PCSX2", programa), {"XDG_CONFIG_HOME": acima}, []
    if nome == "RPCS3":
        return os.path.join(acima, "rpcs3", programa), {"XDG_CONFIG_HOME": acima}, []
    if nome == "Xenia":
        return caminho, {}, ["--storage_root=" + pasta]
    if nome == "Dolphin":
        return caminho, {}, ["-u", os.path.join(pasta, "User")]
    return caminho, {}, []


def programa_que_roda(caminho, nome):
    """Linux: o que executar para abrir o programa do emulador de fora. O
    AppImage sai para o cache na primeira vez (appimage_que_roda); o
    programa comum, no pen drive que nao deixa executar, vai para o cache
    com a permissao de executar. No Windows, o mesmo caminho."""
    if WINDOWS or not caminho:
        return caminho
    if caminho.lower().endswith(".appimage"):
        return appimage_que_roda(caminho, nome.lower())
    if _roda(caminho):
        return caminho
    try:
        destino = os.path.join(pasta_de_cache(), "%s-%d" % (nome.lower(), os.path.getsize(caminho)))
        copia = os.path.join(destino, os.path.basename(caminho))
        with _TRAVA_DO_RETROARCH:
            if not _roda(copia):
                os.makedirs(destino, exist_ok=True)
                shutil.copyfile(caminho, copia + ".copiando")
                os.chmod(copia + ".copiando", 0o755)
                os.replace(copia + ".copiando", copia)
        return copia
    except OSError as falha:
        print("[ARENA] Nao consegui preparar o %s do Linux: %s" % (nome, falha))
        return caminho
