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
    ARENA reconhece para explicar o que muda la;
  - o Android (item 14): o mesmo servidor roda dentro do app do ARENA, com o
    Python do Android; o RetroArch e' uma tela do app, os nucleos vem dentro
    do APK, e o que so o app sabe fazer o servidor pede pela ponte
    (servidor/ponte_android.py).

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
# O Python do Android (o 3.13 do APK) se apresenta como "android" (PEP 738).
ANDROID = sys.platform == "android"

# O RetroArch do Linux (stable 1.22.2 do libretro): um AppImage, um arquivo
# so que roda sem instalar (ver retroarch_que_roda).
APPIMAGE_RETROARCH = "RetroArch-Linux-x86_64.AppImage"
# O nome do programa do RetroArch deste sistema, para as frases da tela, e o
# conferidor do pacote (o VERIFICAR.bat do Windows, o VERIFICAR.sh do Linux).
# No Android, o RetroArch vem dentro do APK: o arquivo da pasta retroarch so
# marca que ele esta la (o servidor/android_inicio.py o escreve).
RETROARCH_DO_ANDROID = "retroarch-android.txt"
NOME_DO_RETROARCH = "retroarch.exe" if WINDOWS else (RETROARCH_DO_ANDROID if ANDROID else APPIMAGE_RETROARCH)
VERIFICAR = "VERIFICAR.bat" if WINDOWS else ("APK do ARENA (instale de novo)" if ANDROID else "VERIFICAR.sh")
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
    """'windows', 'android', 'chromeos' (o Linux do Chromebook) ou 'linux'."""
    if WINDOWS:
        return "windows"
    if ANDROID:
        return "android"
    if no_chromebook():
        return "chromeos"
    return "linux" if LINUX else sys.platform


def descricao():
    """O nome do sistema para a tela ('Windows 11', 'Debian 13 (Linux 6.6)')."""
    if WINDOWS:
        return "%s %s" % (platform.system(), platform.release())
    if ANDROID:
        # O app conta qual Android e qual aparelho ("Android 15 (Google Pixel 6)").
        return os.environ.get("ARENA_ANDROID_SISTEMA") or "Android"
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


# Os nucleos que no Android tem outro nome (o mesmo nucleo, compilado de
# outro jeito): o N64 na versao para a placa dos celulares (OpenGL ES 3) e o
# MAME atual com o nome do Android.
NO_ANDROID_COM_OUTRO_NOME = {"mupen64plus_next_libretro": "mupen64plus_next_gles3_libretro",
                             "mame_libretro": "mamearcade_libretro"}


def arquivo_do_nucleo(nome):
    """'fceumm_libretro.dll' (o nome do consoles.json) -> o arquivo deste
    sistema: o mesmo no Windows, 'fceumm_libretro.so' no Linux,
    'fceumm_libretro_android.so' no Android."""
    if not nome or WINDOWS:
        return nome
    base, extensao = os.path.splitext(nome)
    if extensao.lower() not in (".dll", ".so", ".dylib"):
        return nome
    if ANDROID:
        if base.endswith("_android"):
            return nome
        return NO_ANDROID_COM_OUTRO_NOME.get(base, base) + "_android.so"
    return base + ".so"


CAMPOS_DE_NUCLEO = ("core", "core_netplay", "core_sem_bios")


def nucleos_deste_sistema(plataformas):
    """O catalogo (consoles.json) com o nome dos nucleos deste sistema: no
    Linux, cada "core", "core_netplay" e "core_sem_bios" passa de .dll para
    .so (no Android, para _android.so). No Windows, devolve a mesma lista.
    Quem le o consoles.json chama isto uma vez, e o resto do ARENA nem fica
    sabendo."""
    if WINDOWS:
        return plataformas
    for p in plataformas:
        for campo in CAMPOS_DE_NUCLEO:
            if p.get(campo):
                p[campo] = arquivo_do_nucleo(p[campo])
    return plataformas


def nome_curto_do_nucleo(arquivo):
    """'swanstation_libretro.dll', '.so' ou '_android.so' -> 'swanstation'. O
    nucleo de outro nome no Android volta ao nome de sempre (as opcoes dele
    sao as mesmas)."""
    base = os.path.basename(arquivo or "")
    for fim in ("_libretro.dll", "_libretro.so", "_libretro_android.so", "_libretro.dylib"):
        if base.lower().endswith(fim):
            curto = base[:-len(fim)].lower()
            for de_sempre, do_android in NO_ANDROID_COM_OUTRO_NOME.items():
                if curto + "_libretro" == do_android:
                    return de_sempre[:-len("_libretro")]
            return curto
    return base.lower()


def nome_do_info(arquivo):
    """O arquivo de informacoes do nucleo (retroarch/info): o nome dele sem a
    extensao e, no Android, sem o "_android" ('fceumm_libretro.info')."""
    base = os.path.splitext(os.path.basename(arquivo or ""))[0]
    if base.endswith("_android"):
        base = base[:-len("_android")]
    return base + ".info"


def nucleos_presentes(pasta_cores):
    """Os nucleos deste sistema (nomes em minusculas): os da pasta e, no
    Android, tambem os que vieram no APK e ainda nao sairam dele (saem na
    primeira vez que o console abre: preparar_nucleo)."""
    try:
        nomes = {e.name.lower() for e in os.scandir(pasta_cores) if e.is_file()}
    except OSError:
        nomes = set()
    if ANDROID:
        import ponte_android
        nomes |= {n.lower() for n in ponte_android.nucleos_do_apk()}
    return nomes


def tem_nucleo(caminho):
    """O nucleo esta aqui? No Android, vale tambem o que esta no APK."""
    if os.path.isfile(caminho):
        return True
    if ANDROID:
        import ponte_android
        return os.path.basename(caminho) in ponte_android.nucleos_do_apk()
    return False


def preparar_nucleo(caminho):
    """Antes de abrir o jogo: no Android, o nucleo sai do APK para a pasta de
    nucleos do app (uma vez por APK). No Windows e no Linux, ja esta la."""
    if ANDROID:
        import ponte_android
        return ponte_android.preparar_nucleo(caminho)
    return os.path.isfile(caminho)


def executavel_do_retroarch(pasta_retroarch):
    """O programa do RetroArch deste sistema, dentro da pasta retroarch (no
    Android, a marca de que ele veio no APK)."""
    if ANDROID:
        return os.path.join(pasta_retroarch, RETROARCH_DO_ANDROID)
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
    freedesktop para o que se pode refazer a qualquer hora. Android: a pasta
    de cache do app (o app conta qual e')."""
    if ANDROID and os.environ.get("ARENA_ANDROID_CACHE"):
        return os.path.join(os.environ["ARENA_ANDROID_CACHE"], "arena")
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
        # O AppImage feito com as ferramentas novas (o do RPCS3) tira o
        # programa para "AppDir" e deixa "squashfs-root" como atalho para
        # ela (./AppDir): vai a pasta de verdade, senao o atalho movido
        # apontaria para o nada (achado do testes/teste_linux.py, 20/10/2026).
        if os.path.islink(extraido):
            extraido = os.path.realpath(extraido)
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
    manda usar a do ARENA, a mesma do Windows, no pen drive. No Android, o
    app abre o RetroArch do APK com o resto da linha (ponte_android)."""
    if WINDOWS:
        return [executavel]
    if ANDROID:
        return [executavel, "--config", arquivo_cfg]
    return [retroarch_que_roda(executavel), "--config", arquivo_cfg]


def abrir_programa(comando, **extras):
    """subprocess.Popen(comando, **extras). No Android, o RetroArch e' uma
    tela do app: quem abre e' o app, e o que volta se espera igual (wait)."""
    if ANDROID:
        import ponte_android
        return ponte_android.abrir_retroarch(comando, **extras)
    return subprocess.Popen(comando, **extras)


def python_que_veio_junto(pasta_servidor):
    """O Python que vem no pacote para este sistema (pode nao existir). No
    Android, o do APK, que ja esta rodando."""
    if ANDROID:
        return sys.executable
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
    Thunar...), pelo xdg-open, o jeito padrao do freedesktop, ou pelo gio. No
    Android, o gerenciador de arquivos do aparelho, pelo app."""
    if WINDOWS:
        os.startfile(pasta)
        return
    if ANDROID:
        import ponte_android
        if not ponte_android.abrir_pasta(pasta):
            raise SemGerenciadorDeArquivos("o aparelho nao abriu a pasta")
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
    if ANDROID:
        abrir_pasta(os.path.dirname(os.path.abspath(arquivo)))
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
# Android (item 14): o RetroArch do Android tem poucos motores, e cada chave
# so aceita os dele (MOTORES_QUE_O_ANDROID_TEM); o resto vira o padrao dele.
# O video pelo OpenGL ES ("gl") ou pelo Vulkan; o som pelo OpenSL ES; o
# teclado e o controle pelo proprio Android. Os que so o Android tem
# (MOTORES_SO_DO_ANDROID) voltam ao de cada sistema no Windows e no Linux.
MOTORES_SO_DO_ANDROID = {
    "video_driver": (),
    "input_driver": ("android",),
    "input_joypad_driver": ("android",),
    "audio_driver": ("opensl", "aaudio"),
    "microphone_driver": ("sl", "aaudio"),
    "midi_driver": (),
}
MOTORES_QUE_O_ANDROID_TEM = {
    "video_driver": ("gl", "vulkan", "null"),
    "input_driver": ("android", "null"),
    "input_joypad_driver": ("android", "null"),
    "audio_driver": ("opensl", "null"),
    "microphone_driver": ("null",),
    "midi_driver": ("null",),
}
MOTORES_DO_ANDROID = {"video_driver": "gl", "input_driver": "android", "input_joypad_driver": "android",
                      "audio_driver": "opensl", "microphone_driver": "null", "midi_driver": "null"}


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


def ajustes_do_android(opcoes, pasta_retroarch, filtro):
    """O arquivo da partida no Android: ganha a tela de toque (o controle
    desenhado na tela, que some quando um controle de verdade e' ligado) e
    uma folga no som (o celular barato estala com menos de 64 ms; o padrao
    do RetroArch do Android e' 128). Os filtros de tela do ARENA (.slangp) so
    rodam no Vulkan: no OpenGL ES ("gl"), ficam de fora. Devolve o filtro que
    vale ("" sem nenhum)."""
    toque = os.path.join(pasta_retroarch, "overlays", "gamepads", "neo-retropad", "neo-retropad.cfg")
    if os.path.isfile(toque):
        opcoes["input_overlay_enable"] = "true"
        opcoes["input_overlay"] = toque
        opcoes["input_overlay_hide_when_gamepad_connected"] = "true"
    try:
        if int(str(opcoes.get("audio_latency") or 0)) < 64:
            opcoes["audio_latency"] = "64"
    except ValueError:
        opcoes["audio_latency"] = "64"
    if str(opcoes.get("video_driver", "")).strip().lower() != "vulkan":
        filtro = ""
        opcoes["video_shader_enable"] = "false"
    return filtro


def motores_deste_sistema(opcoes):
    """As opcoes do RetroArch ({chave: valor}) com os motores deste sistema
    (ver acima). Troca no proprio dicionario e o devolve."""
    if ANDROID:
        for chave, valores in MOTORES_QUE_O_ANDROID_TEM.items():
            if chave in opcoes and str(opcoes[chave]).strip().lower() not in valores:
                opcoes[chave] = MOTORES_DO_ANDROID[chave]
        return opcoes
    outro = MOTORES_SO_DO_LINUX if WINDOWS else MOTORES_SO_DO_WINDOWS
    estrangeiros = {chave: outro[chave] + MOTORES_SO_DO_ANDROID[chave] for chave in outro}
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


def pasta_que_roda(pasta, nome, executavel):
    """Linux: a pasta de um programa (o Java do Java ME, por exemplo) pronta
    para rodar, e devolve o caminho do 'executavel' (relativo a ela) que
    roda. Do zip sem a permissao de executar, numa pasta que aceita: so
    marca. No pen drive que nao deixa (FAT32): a pasta vai inteira para
    ~/.cache/arena/<nome>-<tamanho do executavel>, uma vez so. No Windows,
    o proprio caminho."""
    original = os.path.join(pasta, executavel)
    if WINDOWS or _roda(original):
        return original
    try:
        os.chmod(original, os.stat(original).st_mode | 0o100)
    except OSError:
        pass
    if _roda(original):
        return original
    try:
        destino = os.path.join(pasta_de_cache(), "%s-%d" % (nome, os.path.getsize(original)))
        copia = os.path.join(destino, executavel)
        with _TRAVA_DO_RETROARCH:
            if not _roda(copia):
                montando = "%s.montando-%d" % (destino, os.getpid())
                _apagar(montando)
                shutil.copytree(pasta, montando)
                for atual, _subpastas, nomes in os.walk(os.path.join(montando, "bin")):
                    for nome_arquivo in nomes:
                        os.chmod(os.path.join(atual, nome_arquivo), 0o755)
                for atual, _subpastas, nomes in os.walk(os.path.join(montando, "lib")):
                    for nome_arquivo in nomes:
                        if not nome_arquivo.endswith((".so", ".jsa", "modules")) and "." not in nome_arquivo:
                            os.chmod(os.path.join(atual, nome_arquivo), 0o755)    # jspawnhelper e parecidos
                _apagar(destino)
                os.replace(montando, destino)
        return copia
    except OSError as falha:
        print("[ARENA] Nao consegui preparar o %s do Linux: %s" % (nome, falha))
        return original
