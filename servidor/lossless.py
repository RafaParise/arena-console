# -*- coding: utf-8 -*-
r"""Lossless Scaling: o ARENA usa o programa de quem comprou.

Pedido do Rafael (15/10/2026, item 10): integrar o Lossless Scaling ao
ARENA, "assim como o ARENA ja faz, que e' configurar tudo sozinho", e, se
nao der para levar o programa junto, fazer as mesmas tecnicas no ARENA.

O que e' o Lossless Scaling (LS): um programa pago, vendido pela Steam
(numero 993090). Ele pega a janela de um jogo desenhada pequena e estica
para a tela inteira com tecnicas de escala (LS1, FSR, NIS, SGSR, xBR,
Anime4K, pixel nitido...) e pode criar quadros novos entre os do jogo
(LSFG, a "geracao de quadros": de 30 para 60).

O que o ARENA faz, e o que NAO faz:
  - NAO distribui o LS, nem no pacote nem no GitHub: ele e' de quem
    comprou. O proprio LS confere isso: o motor dele (Lossless.dll) olha no
    registro do Windows se a Steam desta conta o tem instalado
    (HKCU\Software\Valve\Steam\Apps\993090, Installed = 1); se nao, mostra
    "Make sure you have installed it through Steam" e nao escala nada.
  - Acha o LS desta maquina: na pasta do ARENA (onde o professor colocou o
    dele), na pasta emuladores\ e nas bibliotecas da Steam.
  - Ajusta o LS para cada jogo: escreve um perfil chamado "ARENA" no
    Settings.xml dele (%LOCALAPPDATA%\Lossless Scaling), e SO com o LS
    FECHADO: ele regrava o arquivo inteiro ao fechar, e o que o ARENA
    escrevesse com ele aberto se perderia. So o perfil "ARENA" muda; os
    perfis do dono ficam como estao. Antes da primeira mudanca, guarda uma
    copia (Settings.xml.antes-do-arena), uma vez so.
  - Abre o LS junto com o jogo (-StartMinimized, o mesmo que ele usa para
    abrir com o Windows) e fecha junto, se foi o ARENA que abriu. O perfil
    "ARENA" liga a escala sozinho (AutoScale) quando a janela do emulador
    aparece -- ninguem precisa apertar Ctrl+Alt+S.

As opcoes e os valores que o LS aceita foram lidos do proprio programa
(LosslessScaling.dll 3.2.2.0, metadados .NET: a ordem dos campos do perfil
e cada lista de valores), em 16/10/2026. Valor fora da lista nao e'
gravado: o LS recusaria o arquivo inteiro ("The settings file is
corrupted") e voltaria ao padrao.
"""
import os
import re
import subprocess
import sys
import threading
import time

NUMERO_NA_STEAM = "993090"
EXECUTAVEL = "LosslessScaling.exe"
TITULO_DO_PERFIL = "ARENA"
COPIA_DE_ANTES = "Settings.xml.antes-do-arena"

# As janelas que o perfil "ARENA" escala (o campo "Filters" do LS: nome do
# programa; varios separados por ";").
PROGRAMAS_DOS_EMULADORES = ("retroarch.exe", "pcsx2-qt.exe", "Dolphin.exe", "rpcs3.exe",
                            "xenia_canary.exe", "xenia.exe")

# Os campos de um perfil, NA ORDEM em que o LS os grava (a ordem da classe
# Profile do LosslessScaling.dll), com o valor que o ARENA usa quando nao
# escolhe outro. Quase todos sao o padrao do proprio LS; os que o ARENA
# muda dizem o porque.
CAMPOS_DO_PERFIL = (
    ("Title", TITULO_DO_PERFIL),
    ("Path", ";".join(PROGRAMAS_DOS_EMULADORES)),
    ("AutoScale", "true"),         # escala sozinho quando a janela aparece
    ("AutoScaleDelay", "1"),       # 1 s: o RetroArch ja abriu a janela no tamanho final
    ("ScalingMode", "Auto"),       # do tamanho da tela
    ("ScalingFitMode", "AspectRatio"),  # sem esticar: o formato do jogo
    ("ScaleFactor", "1.5"),
    ("ResizeBeforeScaling", "false"),
    ("WindowedMode", "false"),
    ("ScalingType", "LS1"),
    ("FSRType", "ORIGINAL"),
    ("LS1Type", "BALANCED"),
    ("LSFG2Mode", "X2"),
    ("LSFG3Mode1", "FIXED"),
    ("LSFG3Multiplier", "2"),
    ("LSFG3Target", "60"),
    ("LSFGFlowScale", "100"),
    ("LSFGSize", "BALANCED"),
    ("Anime4kType", "S"),
    ("Sharpness", "5"),
    ("LS1Sharpness", "1"),
    ("VRS", "false"),
    ("FrameGeneration", "Off"),
    ("ClipCursor", "false"),       # o emulador nao usa o mouse
    ("AdjustCursorSpeed", "false"),
    ("HideCursor", "true"),
    ("ScaleCursor", "false"),
    ("SyncMode", "DEFAULT"),
    ("MaxFrameLatency", "3"),
    ("GsyncSupport", "true"),
    ("HdrSupport", "false"),
    ("DrawFps", "false"),          # sem o contador por cima do jogo
    ("CaptureApi", "DXGI"),
    ("QueueTarget", "1"),
    ("PreferredGpuId", "0"),
    ("OutputDisplayId", "0"),
    ("CropInput", "false"),
    ("CropInputLeft", "0"),
    ("CropInputTop", "0"),
    ("CropInputRight", "0"),
    ("CropInputBottom", "0"),
    ("MultiDisplayMode", "false"),
)

# As listas de valores de cada campo de escolha (enums do LS 3.2.2).
VALORES_ACEITOS = {
    "ScalingMode": ("Auto", "Custom"),
    "ScalingFitMode": ("AspectRatio", "Fullscreen"),
    "ScalingType": ("Off", "LS1", "FSR", "NIS", "SGSR", "BicubicCAS", "Anime4K", "XBR",
                    "SharpBilinear", "Integer", "Nearest"),
    "FSRType": ("ORIGINAL", "OPTIMIZED"),
    "LS1Type": ("BALANCED", "PERFORMANCE"),
    "Anime4kType": ("S", "M", "L", "VL", "UL"),
    "FrameGeneration": ("Off", "LSFG3", "LSFG2", "LSFG1", "LSFI", "LSFI1"),
    "LSFG2Mode": ("X2", "X3", "X4"),
    "LSFGSize": ("BALANCED", "PERFORMANCE"),
    "LSFG3Mode1": ("FIXED", "ADAPTIVE"),
    "SyncMode": ("OFF", "DEFAULT", "VSYNC1", "VSYNC2", "VSYNC3", "VSYNC4"),
    "CaptureApi": ("DXGI", "WGC", "GDI"),
}
SIM_OU_NAO = {nome for nome, valor in CAMPOS_DO_PERFIL if valor in ("true", "false")}
NUMEROS = {"AutoScaleDelay", "ScaleFactor", "LSFG3Multiplier", "LSFG3Target", "LSFGFlowScale",
           "Sharpness", "LS1Sharpness", "MaxFrameLatency", "QueueTarget", "PreferredGpuId",
           "OutputDisplayId", "CropInputLeft", "CropInputTop", "CropInputRight", "CropInputBottom"}

_TRAVA = threading.Lock()
# O LS que o ARENA abriu (para fechar so esse, e nunca o do dono).
_ABERTO_PELO_ARENA = {"processo": None}


# ---------------------------------------------------------------------------
# Onde esta, e se a licenca vale
# ---------------------------------------------------------------------------
def _steam():
    """Pasta da Steam desta conta do Windows (registro, sem administrador)."""
    if os.name != "nt":
        return None
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as chave:
            pasta = winreg.QueryValueEx(chave, "SteamPath")[0]
    except OSError:
        return None
    return os.path.normpath(pasta) if pasta else None


def bibliotecas_da_steam(pasta_steam=None):
    """As pastas de biblioteca da Steam (libraryfolders.vdf), a principal primeiro."""
    pasta_steam = pasta_steam or _steam()
    if not pasta_steam:
        return []
    achadas = [pasta_steam]
    arquivo = os.path.join(pasta_steam, "steamapps", "libraryfolders.vdf")
    try:
        with open(arquivo, encoding="utf-8", errors="replace") as vdf:
            texto = vdf.read()
    except OSError:
        return achadas
    for pasta in re.findall(r'"path"\s+"([^"]+)"', texto):
        pasta = os.path.normpath(pasta.replace("\\\\", "\\"))
        if pasta.lower() not in {p.lower() for p in achadas}:
            achadas.append(pasta)
    return achadas


def lugares_para_procurar(raiz):
    """Onde o LS pode estar, na ordem: a pasta do ARENA, emuladores\\ e a Steam."""
    lugares = [("pasta do ARENA", os.path.join(raiz, "Lossless Scaling")),
               ("pasta emuladores", os.path.join(raiz, "emuladores", "Lossless Scaling"))]
    for biblioteca in bibliotecas_da_steam():
        lugares.append(("Steam", os.path.join(biblioteca, "steamapps", "common", "Lossless Scaling")))
    return lugares


def licenca_na_steam():
    """A Steam desta conta tem o LS instalado? E' o que o proprio LS confere."""
    if os.name != "nt":
        return False
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Valve\Steam\Apps\%s" % NUMERO_NA_STEAM) as chave:
            return int(winreg.QueryValueEx(chave, "Installed")[0]) == 1
    except (OSError, ValueError):
        return False


def versao_do_arquivo(caminho):
    """"3.2.2.0", ou "" se o Windows nao disser."""
    if os.name != "nt":
        return ""
    import ctypes
    from ctypes import wintypes
    try:
        versao = ctypes.WinDLL("version")
        versao.GetFileVersionInfoSizeW.argtypes = [wintypes.LPCWSTR, ctypes.c_void_p]
        versao.GetFileVersionInfoW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                               ctypes.c_void_p]
        versao.VerQueryValueW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR,
                                          ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(wintypes.UINT)]
        tamanho = versao.GetFileVersionInfoSizeW(caminho, None)
        if not tamanho:
            return ""
        memoria = ctypes.create_string_buffer(tamanho)
        if not versao.GetFileVersionInfoW(caminho, 0, tamanho, memoria):
            return ""
        ponteiro, comprimento = ctypes.c_void_p(), wintypes.UINT()
        if not versao.VerQueryValueW(memoria, "\\", ctypes.byref(ponteiro), ctypes.byref(comprimento)):
            return ""
        info = (ctypes.c_uint32 * 13).from_address(ponteiro.value)
        return "%d.%d.%d.%d" % (info[2] >> 16, info[2] & 0xFFFF, info[3] >> 16, info[3] & 0xFFFF)
    except (OSError, AttributeError, ValueError):
        return ""


def achar(raiz):
    """O LS desta maquina: {"executavel", "origem", "versao", "licenca"} ou None.
    No Linux, None: o Lossless Scaling e' um programa do Windows (o mesmo pen
    drive pode trazer a pasta dele, mas la ele nao abre), e o jogo fica com
    a escala do proprio ARENA (item 13, 18/10/2026)."""
    if os.name != "nt":
        return None
    for origem, pasta in lugares_para_procurar(raiz):
        executavel = os.path.join(pasta, EXECUTAVEL)
        if os.path.isfile(executavel):
            return {"executavel": executavel, "origem": origem,
                    "versao": versao_do_arquivo(executavel), "licenca": licenca_na_steam()}
    return None


# ---------------------------------------------------------------------------
# Esta aberto?
# ---------------------------------------------------------------------------
def processos_abertos(nome=EXECUTAVEL):
    """PIDs dos processos com este nome (fotografia dos processos do Windows)."""
    if os.name != "nt":
        return []
    import ctypes
    from ctypes import wintypes

    class ENTRADA(ctypes.Structure):
        _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
                    ("th32ProcessID", wintypes.DWORD), ("th32DefaultHeapID", ctypes.c_size_t),
                    ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
                    ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", ctypes.c_long),
                    ("dwFlags", wintypes.DWORD), ("szExeFile", wintypes.WCHAR * 260)]

    nucleo = ctypes.WinDLL("kernel32", use_last_error=True)
    nucleo.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    nucleo.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    nucleo.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ENTRADA)]
    nucleo.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ENTRADA)]
    nucleo.CloseHandle.argtypes = [wintypes.HANDLE]
    foto = nucleo.CreateToolhelp32Snapshot(0x2, 0)          # TH32CS_SNAPPROCESS
    if not foto or foto == wintypes.HANDLE(-1).value:
        return []
    achados = []
    try:
        entrada = ENTRADA()
        entrada.dwSize = ctypes.sizeof(ENTRADA)
        tem = nucleo.Process32FirstW(foto, ctypes.byref(entrada))
        while tem:
            if entrada.szExeFile.lower() == nome.lower():
                achados.append(entrada.th32ProcessID)
            tem = nucleo.Process32NextW(foto, ctypes.byref(entrada))
    finally:
        nucleo.CloseHandle(foto)
    return achados


# ---------------------------------------------------------------------------
# O perfil "ARENA" no Settings.xml do LS
# ---------------------------------------------------------------------------
def pasta_da_configuracao():
    return os.path.join(os.environ.get("LOCALAPPDATA", ""), "Lossless Scaling")


def arquivo_da_configuracao():
    return os.path.join(pasta_da_configuracao(), "Settings.xml")


def _escapar(texto):
    return (str(texto).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def montar_perfil(trocas=None):
    """O bloco <Profile> do ARENA, com as trocas pedidas por cima do padrao.

    Recusa (ValueError) campo que o LS nao tem e valor fora da lista dele.
    """
    trocas = dict(trocas or {})
    nomes = [nome for nome, _ in CAMPOS_DO_PERFIL]
    desconhecidos = sorted(set(trocas) - set(nomes))
    if desconhecidos:
        raise ValueError("o Lossless Scaling nao tem estes campos: %s" % ", ".join(desconhecidos))
    valores = dict(CAMPOS_DO_PERFIL)
    valores.update({c: str(v).lower() if isinstance(v, bool) else str(v) for c, v in trocas.items()})
    for campo, valor in valores.items():
        if campo in VALORES_ACEITOS and valor not in VALORES_ACEITOS[campo]:
            raise ValueError("%s = %s: o Lossless Scaling so aceita %s"
                             % (campo, valor, ", ".join(VALORES_ACEITOS[campo])))
        if campo in SIM_OU_NAO and valor not in ("true", "false"):
            raise ValueError("%s = %s: tem que ser true ou false" % (campo, valor))
        if campo in NUMEROS and not re.fullmatch(r"\d+(\.\d+)?", valor):
            raise ValueError("%s = %s: tem que ser numero" % (campo, valor))
    linhas = ["    <Profile>"]
    linhas += ["      <%s>%s</%s>" % (nome, _escapar(valores[nome]), nome) for nome in nomes]
    linhas.append("    </Profile>")
    return "\r\n".join(linhas)


_PERFIL = re.compile(r"[ \t]*<Profile>.*?</Profile>[ \t]*(?:\r?\n)?", re.S)


def trocar_perfil_no_texto(texto, bloco):
    """O Settings.xml com o perfil "ARENA" novo (os outros perfis intactos)."""
    if "</GameProfiles>" not in texto:
        if "<GameProfiles />" in texto:
            texto = texto.replace("<GameProfiles />", "<GameProfiles>\r\n  </GameProfiles>")
        else:
            raise ValueError("o Settings.xml do Lossless Scaling nao tem a lista de perfis")
    sem_o_nosso = _PERFIL.sub(
        lambda m: "" if re.search(r"<Title>%s</Title>" % re.escape(TITULO_DO_PERFIL), m.group(0))
        else m.group(0), texto)
    return sem_o_nosso.replace("  </GameProfiles>", bloco + "\r\n  </GameProfiles>", 1) \
        if "  </GameProfiles>" in sem_o_nosso \
        else sem_o_nosso.replace("</GameProfiles>", bloco + "\r\n</GameProfiles>", 1)


def frequencia_da_tela():
    """Quantas vezes por segundo a tela principal se redesenha (60 se nao der para saber)."""
    if os.name != "nt":
        return 60
    import ctypes
    try:
        usuario, gdi = ctypes.WinDLL("user32"), ctypes.WinDLL("gdi32")
        usuario.GetDC.restype = ctypes.c_void_p
        usuario.GetDC.argtypes = [ctypes.c_void_p]
        usuario.ReleaseDC.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        gdi.GetDeviceCaps.argtypes = [ctypes.c_void_p, ctypes.c_int]
        dc = usuario.GetDC(None)
        try:
            hz = int(gdi.GetDeviceCaps(dc, 116))          # VREFRESH
        finally:
            usuario.ReleaseDC(None, dc)
    except (OSError, AttributeError, ValueError):
        return 60
    return hz if 24 <= hz <= 500 else 60


def gravar_perfil(trocas=None, arquivo=None):
    """Escreve o perfil "ARENA" no Settings.xml. Devolve (gravou, motivo).

    So com o LS fechado. A copia de antes fica ao lado, uma vez so.
    """
    arquivo = arquivo or arquivo_da_configuracao()
    if processos_abertos():
        return False, "o Lossless Scaling esta aberto (ele regrava o arquivo ao fechar)"
    bloco = montar_perfil(trocas)
    with _TRAVA:
        try:
            with open(arquivo, "rb") as entrada:
                bruto = entrada.read()
        except FileNotFoundError:
            return False, "o Lossless Scaling ainda nao criou o Settings.xml (abra-o uma vez)"
        bom = b"\xef\xbb\xbf" if bruto.startswith(b"\xef\xbb\xbf") else b""
        texto = bruto[len(bom):].decode("utf-8")
        novo = trocar_perfil_no_texto(texto, bloco)
        if novo == texto:
            return True, "ja estava assim"
        copia = os.path.join(os.path.dirname(arquivo), COPIA_DE_ANTES)
        if not os.path.exists(copia):
            with open(copia, "wb") as saida:
                saida.write(bruto)
        temporario = "%s.%d.arena.tmp" % (arquivo, threading.get_ident())
        try:
            with open(temporario, "wb") as saida:
                saida.write(bom + novo.encode("utf-8"))
                saida.flush()
                os.fsync(saida.fileno())
            os.replace(temporario, arquivo)
        finally:
            if os.path.exists(temporario):
                try:
                    os.remove(temporario)
                except OSError:
                    pass
    return True, "perfil gravado"


# ---------------------------------------------------------------------------
# O que o ARENA escolhe para cada jogo
# ---------------------------------------------------------------------------
def trocas_para_o_jogo(desenho_2d, nota_gpu, mais_quadros=False, hz=60, esticar=False):
    """As trocas do perfil "ARENA" para este jogo, nesta maquina.

    - Esticar (o Formato da imagem do ARENA, graficos.proporcao_da_partida,
      pedido de 22/10/2026): o LS enche a tela inteira (ScalingFitMode
      Fullscreen); senao, o formato do jogo (AspectRatio).

    - Jogo de pixel (2D): o pixel nitido do LS (SharpBilinear), o mesmo do
      ARENA. Jogo 3D: o LS1, a escala propria do LS, e na placa fraca o
      modo rapido dele (LS1 PERFORMANCE).
    - Mais quadros (geracao de quadros): o LSFG 3 no modo que segue a tela
      (ADAPTIVE, ate o numero de quadros da tela), so se pedido. Na placa
      fraca, o tamanho rapido (LSFGSize PERFORMANCE) e o fluxo menor.
    """
    trocas = {"ScalingType": "SharpBilinear" if desenho_2d else "LS1",
              "LS1Type": "BALANCED" if (nota_gpu or 0) >= 4 else "PERFORMANCE",
              "ScalingFitMode": "Fullscreen" if esticar else "AspectRatio"}
    if mais_quadros:
        trocas.update({"FrameGeneration": "LSFG3", "LSFG3Mode1": "ADAPTIVE",
                       "LSFG3Target": str(int(hz or 60)),
                       "LSFGSize": "BALANCED" if (nota_gpu or 0) >= 4 else "PERFORMANCE",
                       "LSFGFlowScale": "100" if (nota_gpu or 0) >= 4 else "75"})
    return trocas


# ---------------------------------------------------------------------------
# A janela do RetroArch que o LS estica
# ---------------------------------------------------------------------------
# O LS escala JANELA, nao tela cheia: o RetroArch abre numa janela do tamanho
# em que o jogo e' desenhado, e o LS estica ate a tela com a tecnica dele. E'
# o "desenhar menor e redimensionar" do pedido, feito pelo programa do dono.
# Formato da imagem de cada console (largura / altura); o resto e' 4:3.
FORMATO = {"psp": 480 / 272, "nds": 256 / 384, "gba": 3 / 2, "gameboy": 10 / 9,
           "gamegear": 10 / 9, "ngp": 20 / 19, "wonderswan": 224 / 144, "lynx": 160 / 102,
           "virtualboy": 384 / 224, "pokemini": 96 / 64, "j2me": 240 / 320}
ALTURA_DO_2D = 240        # o tamanho de quase todo console 2D (224 a 240 linhas)


def tamanho_da_tela():
    """(largura, altura) da tela principal em pixels de verdade, ou (1366, 768)."""
    if os.name != "nt":
        return 1366, 768
    import ctypes
    try:
        usuario, gdi = ctypes.WinDLL("user32"), ctypes.WinDLL("gdi32")
        usuario.GetDC.restype = ctypes.c_void_p
        usuario.GetDC.argtypes = [ctypes.c_void_p]
        usuario.ReleaseDC.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        gdi.GetDeviceCaps.argtypes = [ctypes.c_void_p, ctypes.c_int]
        dc = usuario.GetDC(None)
        try:
            largura, altura = int(gdi.GetDeviceCaps(dc, 118)), int(gdi.GetDeviceCaps(dc, 117))
        finally:
            usuario.ReleaseDC(None, dc)
    except (OSError, AttributeError, ValueError):
        return 1366, 768
    return (largura, altura) if largura > 0 and altura > 0 else (1366, 768)


def janela_para_o_lossless(plataforma, desenho_2d, altura_interna, tela):
    """As opcoes do RetroArch para abrir na janela que o LS vai esticar.

    - Jogo 2D: a janela e' o desenho do console vezes um numero inteiro
      (video_scale), para cada pixel virar um quadrado certo; o LS estica o
      resto com o pixel nitido dele. Ate 3/4 da tela.
    - Jogo 3D: a janela e' a resolucao interna (desenhada 1 por 1, sem
      esticar dentro do RetroArch), ate 3/4 da tela -- acima disso o LS nao
      teria o que esticar -- e no meio dela.

    Achado de 17/10/2026, com o RetroArch 1.22 desta pasta: o tamanho exato da
    janela so vale com "lembrar posicao e tamanho" ligado
    (video_window_save_positions + video_windowed_position_*). Com o
    "video_window_custom_size_enable", o PSP abria em 1920x1080 (o PPSSPP diz
    que o quadro dele e' desse tamanho, e o RetroArch multiplica pela escala).
    """
    largura_tela, altura_tela = (int(tela[0] or 1366), int(tela[1] or 768)) if tela else (1366, 768)
    opcoes = {"video_fullscreen": "false", "video_windowed_fullscreen": "false",
              "video_window_custom_size_enable": "false", "video_shader_enable": "false"}
    if desenho_2d:
        vezes = max(1, int(altura_tela * 0.75) // ALTURA_DO_2D)
        opcoes.update({"video_window_save_positions": "false", "video_scale": str(vezes)})
        return opcoes
    altura = min(int(altura_interna or 480), int(altura_tela * 0.75))
    largura = min(int(round(altura * FORMATO.get(plataforma, 4 / 3))), int(largura_tela * 0.9))
    opcoes.update({"video_window_save_positions": "true",
                   "video_windowed_position_width": str(largura),
                   "video_windowed_position_height": str(altura),
                   "video_windowed_position_x": str(max(0, (largura_tela - largura) // 2)),
                   "video_windowed_position_y": str(max(0, (altura_tela - altura) // 2))})
    return opcoes


# ---------------------------------------------------------------------------
# Abrir junto com o jogo, fechar junto
# ---------------------------------------------------------------------------
def abrir(executavel):
    """Abre o LS minimizado, se ainda nao estiver aberto. Devolve se o ARENA abriu."""
    if processos_abertos():
        return False
    processo = subprocess.Popen([executavel, "-StartMinimized"], cwd=os.path.dirname(executavel),
                                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
    _ABERTO_PELO_ARENA["processo"] = processo
    return True


def fechar_o_que_o_arena_abriu(espera=8.0):
    """Fecha o LS que o ARENA abriu (o do dono, aberto antes, fica).

    Depois de fechado, o perfil "ARENA" fica com a escala sozinha DESLIGADA:
    se o dono abrir o LS por conta propria, ele nao estica o jogo normal do
    ARENA (que ja e' em tela cheia e so ganharia atraso). A proxima partida
    pelo LS liga de novo."""
    processo = _ABERTO_PELO_ARENA.get("processo")
    _ABERTO_PELO_ARENA["processo"] = None
    if processo is None:
        return False
    if processo.poll() is None:
        # Primeiro pedindo (o taskkill sem /F manda o "fechar" a janela dele,
        # e o LS guarda a configuracao como sempre); se nao fechar, a forca.
        subprocess.run(["taskkill", "/PID", str(processo.pid)], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        limite = time.monotonic() + espera
        while time.monotonic() < limite and processo.poll() is None:
            time.sleep(0.2)
        if processo.poll() is None:
            processo.kill()
            processo.wait(5)
    try:
        gravar_perfil({"AutoScale": "false"})
    except (OSError, ValueError):
        pass
    return True


def situacao(raiz):
    """Para a tela dos Ajustes: achou, de onde, a versao, se a licenca vale."""
    achado = achar(raiz)
    if not achado:
        return {"achado": False}
    return {"achado": True, "origem": achado["origem"], "versao": achado["versao"],
            "licenca": achado["licenca"], "aberto": bool(processos_abertos()),
            "configuracao": os.path.isfile(arquivo_da_configuracao())}


if __name__ == "__main__":
    import json
    print(json.dumps(situacao(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                     ensure_ascii=False, indent=1))
    sys.exit(0)
