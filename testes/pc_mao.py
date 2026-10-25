# -*- coding: utf-8 -*-
r"""A "mao" e os "olhos" no computador (Windows), so com a biblioteca padrao (ctypes): foto da tela ou de uma janela,
lista das janelas, trazer uma janela para a frente, clicar, apertar tecla, escrever, e o estado dos controles (XInput).

Por que existe (25/10/2026): o Rafael pediu que eu faca sozinho os passos que dependiam dele no computador. Navegador eu ja
guio por CDP (testes\tela_sem_janela.py) e o RetroArch tira foto do proprio jogo (--max-frames-ss); faltava a tela de
fora (janela do emulador, caixa do Windows, o Explorer) e o controle de verdade.

Limites honestos: o controle (G7 HE, T4...) so e' LIDO aqui; nao ha como apertar botao dele sem um driver de controle
virtual (ViGEmBus), e o ARENA nao instala driver. Tecla e clique funcionam como os de uma pessoa (SendInput), em primeiro plano.

Uso:
    servidor\python\python.exe testes\pc_mao.py foto [nome] [--janela TITULO]
    servidor\python\python.exe testes\pc_mao.py janelas [filtro]
    servidor\python\python.exe testes\pc_mao.py frente TITULO
    servidor\python\python.exe testes\pc_mao.py clicar X Y [direito]
    servidor\python\python.exe testes\pc_mao.py tecla ENTER|F10|ESC|A|CTRL+S ...
    servidor\python\python.exe testes\pc_mao.py escrever "texto"
    servidor\python\python.exe testes\pc_mao.py controles [--vigiar SEGUNDOS]
"""
import ctypes
import ctypes.wintypes as wt
import os
import struct
import sys
import tempfile
import time
import zlib

FOTOS = os.path.join(tempfile.gettempdir(), "pc_mao_fotos")
user32 = ctypes.WinDLL("user32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)        # coordenadas em pixels de verdade, sem escala do Windows
except (AttributeError, OSError):
    pass

# ---------------------------------------------------------------------------
# Foto (BitBlt da tela ou PrintWindow da janela) para PNG, sem biblioteca de imagem
# ---------------------------------------------------------------------------


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", wt.DWORD), ("biWidth", wt.LONG), ("biHeight", wt.LONG), ("biPlanes", wt.WORD),
                ("biBitCount", wt.WORD), ("biCompression", wt.DWORD), ("biSizeImage", wt.DWORD),
                ("biXPelsPerMeter", wt.LONG), ("biYPelsPerMeter", wt.LONG), ("biClrUsed", wt.DWORD),
                ("biClrImportant", wt.DWORD)]


def escrever_png(caminho, largura, altura, bgra):
    """PNG RGB de 8 bits a partir dos bytes BGRA (de cima para baixo)."""
    linhas = bytearray()
    for y in range(altura):
        inicio = y * largura * 4
        linha = bgra[inicio:inicio + largura * 4]
        rgb = bytearray(largura * 3)
        rgb[0::3] = linha[2::4]
        rgb[1::3] = linha[1::4]
        rgb[2::3] = linha[0::4]
        linhas += b"\x00" + rgb

    def pedaco(tipo, dados):
        return struct.pack(">I", len(dados)) + tipo + dados + struct.pack(">I", zlib.crc32(tipo + dados) & 0xFFFFFFFF)
    with open(caminho, "wb") as arquivo:
        arquivo.write(b"\x89PNG\r\n\x1a\n" + pedaco(b"IHDR", struct.pack(">IIBBBBB", largura, altura, 8, 2, 0, 0, 0))
                      + pedaco(b"IDAT", zlib.compress(bytes(linhas), 6)) + pedaco(b"IEND", b""))


def foto(nome=None, hwnd=None):
    """Tira a foto da tela inteira (ou da janela 'hwnd') e devolve o caminho do PNG."""
    os.makedirs(FOTOS, exist_ok=True)
    caminho = os.path.join(FOTOS, "%s.png" % (nome or time.strftime("%H%M%S")))
    if hwnd:
        ret = wt.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(ret))
        largura, altura = ret.right - ret.left, ret.bottom - ret.top
        origem = user32.GetWindowDC(hwnd)
    else:
        largura, altura = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        origem = user32.GetDC(0)
    memoria = gdi32.CreateCompatibleDC(origem)
    bitmap = gdi32.CreateCompatibleBitmap(origem, largura, altura)
    gdi32.SelectObject(memoria, bitmap)
    if hwnd:
        user32.PrintWindow(hwnd, memoria, 2)              # 2 = PW_RENDERFULLCONTENT (pega janela de GPU tambem)
    else:
        gdi32.BitBlt(memoria, 0, 0, largura, altura, origem, 0, 0, 0x00CC0020 | 0x40000000)    # SRCCOPY | CAPTUREBLT
    cabeca = BITMAPINFOHEADER(ctypes.sizeof(BITMAPINFOHEADER), largura, -altura, 1, 32, 0, 0, 0, 0, 0, 0)
    dados = ctypes.create_string_buffer(largura * altura * 4)
    gdi32.GetDIBits(memoria, bitmap, 0, altura, dados, ctypes.byref(cabeca), 0)
    gdi32.DeleteObject(bitmap)
    gdi32.DeleteDC(memoria)
    user32.ReleaseDC(hwnd or 0, origem)
    escrever_png(caminho, largura, altura, dados.raw)
    return caminho


# ---------------------------------------------------------------------------
# Janelas
# ---------------------------------------------------------------------------

def janelas(filtro=""):
    """[(hwnd, titulo, pid, (esq, topo, dir, base))] das janelas de cima, visiveis e com titulo."""
    achadas = []
    fun = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)

    def ver(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        n = user32.GetWindowTextLengthW(hwnd)
        if n == 0:
            return True
        texto = ctypes.create_unicode_buffer(n + 1)
        user32.GetWindowTextW(hwnd, texto, n + 1)
        if filtro.lower() in texto.value.lower():
            pid = wt.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            r = wt.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(r))
            achadas.append((hwnd, texto.value, pid.value, (r.left, r.top, r.right, r.bottom)))
        return True
    user32.EnumWindows(fun(ver), 0)
    return achadas


def trazer_para_frente(hwnd):
    user32.ShowWindow(hwnd, 9)                         # SW_RESTORE
    # o Windows so deixa trazer para a frente quem acabou de receber tecla: o "Alt" solto destrava
    user32.keybd_event(0x12, 0, 0, 0)
    user32.keybd_event(0x12, 0, 2, 0)
    return bool(user32.SetForegroundWindow(hwnd))


# ---------------------------------------------------------------------------
# Mouse e teclado (SendInput)
# ---------------------------------------------------------------------------

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wt.LONG), ("dy", wt.LONG), ("mouseData", wt.DWORD), ("dwFlags", wt.DWORD), ("time", wt.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wt.WORD), ("wScan", wt.WORD), ("dwFlags", wt.DWORD), ("time", wt.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]


class _ENTRADA(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wt.DWORD), ("u", _ENTRADA)]


TECLAS = {"ENTER": 0x0D, "ESC": 0x1B, "TAB": 0x09, "ESPACO": 0x20, "BACKSPACE": 0x08, "DELETE": 0x2E,
          "CIMA": 0x26, "BAIXO": 0x28, "ESQUERDA": 0x25, "DIREITA": 0x27, "CTRL": 0x11, "SHIFT": 0x10, "ALT": 0x12,
          "WIN": 0x5B, "HOME": 0x24, "END": 0x23, "PGUP": 0x21, "PGDN": 0x22}
TECLAS.update({"F%d" % n: 0x6F + n for n in range(1, 13)})                      # F1 = 0x70
TECLAS.update({chr(ord("A") + n): 0x41 + n for n in range(26)})
TECLAS.update({str(n): 0x30 + n for n in range(10)})
ESTENDIDAS = {0x26, 0x28, 0x25, 0x27, 0x2E, 0x24, 0x23, 0x21, 0x22, 0x5B}


def _enviar(*entradas):
    vetor = (INPUT * len(entradas))(*entradas)
    user32.SendInput(len(entradas), vetor, ctypes.sizeof(INPUT))


def _tecla(vk, solta):
    flags = (0x0002 if solta else 0) | (0x0001 if vk in ESTENDIDAS else 0)
    return INPUT(1, _ENTRADA(ki=KEYBDINPUT(vk, user32.MapVirtualKeyW(vk, 0), flags, 0, None)))


def apertar(combinacao, segurar=0.08):
    """'ENTER', 'F10', 'A', 'CTRL+S': aperta, segura um pouco e solta, na ordem inversa."""
    codigos = [TECLAS[parte.upper()] for parte in combinacao.split("+")]
    _enviar(*[_tecla(vk, False) for vk in codigos])
    time.sleep(segurar)
    _enviar(*[_tecla(vk, True) for vk in reversed(codigos)])


def escrever(texto, intervalo=0.01):
    for letra in texto:
        unidade = ord(letra)
        for solta in (False, True):
            _enviar(INPUT(1, _ENTRADA(ki=KEYBDINPUT(0, unidade, 0x0004 | (0x0002 if solta else 0), 0, None))))   # KEYEVENTF_UNICODE
        time.sleep(intervalo)


def clicar(x, y, direito=False):
    user32.SetCursorPos(int(x), int(y))
    time.sleep(0.05)
    baixo, cima = (0x0008, 0x0010) if direito else (0x0002, 0x0004)
    _enviar(INPUT(0, _ENTRADA(mi=MOUSEINPUT(0, 0, 0, baixo, 0, None))))
    time.sleep(0.06)
    _enviar(INPUT(0, _ENTRADA(mi=MOUSEINPUT(0, 0, 0, cima, 0, None))))


# ---------------------------------------------------------------------------
# Controles (XInput): so leitura
# ---------------------------------------------------------------------------

class XINPUT_GAMEPAD(ctypes.Structure):
    _fields_ = [("wButtons", wt.WORD), ("bLeftTrigger", ctypes.c_ubyte), ("bRightTrigger", ctypes.c_ubyte),
                ("sThumbLX", ctypes.c_short), ("sThumbLY", ctypes.c_short), ("sThumbRX", ctypes.c_short),
                ("sThumbRY", ctypes.c_short)]


class XINPUT_STATE(ctypes.Structure):
    _fields_ = [("dwPacketNumber", wt.DWORD), ("Gamepad", XINPUT_GAMEPAD)]


BOTOES_XINPUT = {0x0001: "Cima", 0x0002: "Baixo", 0x0004: "Esquerda", 0x0008: "Direita", 0x0010: "Start", 0x0020: "Back",
                 0x0040: "L3", 0x0080: "R3", 0x0100: "LB", 0x0200: "RB", 0x1000: "A", 0x2000: "B", 0x4000: "X", 0x8000: "Y"}


def controles_xinput():
    """[{'jogador': 1..4, 'botoes': [...], 'gatilhos': (l, r), 'esq': (x, y), 'dir': (x, y)}] dos 4 lugares do XInput (so os ligados)."""
    dll = None
    for nome in ("xinput1_4", "xinput1_3", "xinput9_1_0"):
        try:
            dll = ctypes.WinDLL(nome)
            break
        except OSError:
            continue
    if dll is None:
        return []
    ligados = []
    for numero in range(4):
        estado = XINPUT_STATE()
        if dll.XInputGetState(numero, ctypes.byref(estado)) == 0:
            g = estado.Gamepad
            ligados.append({"jogador": numero + 1, "botoes": [n for b, n in BOTOES_XINPUT.items() if g.wButtons & b],
                            "gatilhos": (g.bLeftTrigger, g.bRightTrigger), "esq": (g.sThumbLX, g.sThumbLY),
                            "dir": (g.sThumbRX, g.sThumbRY), "pacote": estado.dwPacketNumber})
    return ligados


def main(argv):
    for saida in (sys.stdout, sys.stderr):
        try:
            saida.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass
    if len(argv) < 2:
        print(__doc__)
        return 2
    verbo, resto = argv[1].lower(), argv[2:]
    if verbo == "foto":
        titulo = resto[resto.index("--janela") + 1] if "--janela" in resto else None
        nome = resto[0] if resto and not resto[0].startswith("--") else None
        hwnd = None
        if titulo:
            achadas = janelas(titulo)
            if not achadas:
                print("Nao achei janela com %r." % titulo)
                return 1
            hwnd = achadas[0][0]
        print(foto(nome, hwnd))
    elif verbo == "janelas":
        for hwnd, titulo, pid, caixa in janelas(resto[0] if resto else ""):
            print("%8d  pid %-6d %-44s %s" % (hwnd, pid, titulo[:44], caixa))
    elif verbo == "frente":
        achadas = janelas(" ".join(resto))
        print("trouxe" if achadas and trazer_para_frente(achadas[0][0]) else "nao consegui")
    elif verbo == "clicar":
        clicar(resto[0], resto[1], "direito" in resto)
    elif verbo == "tecla":
        for combinacao in resto:
            apertar(combinacao)
            time.sleep(0.1)
    elif verbo == "escrever":
        escrever(" ".join(resto))
    elif verbo == "controles":
        fim = time.monotonic() + (float(resto[resto.index("--vigiar") + 1]) if "--vigiar" in resto else 0)
        while True:
            atual = controles_xinput()
            print(time.strftime("%H:%M:%S"), atual if atual else "nenhum controle XInput ligado", flush=True)
            if time.monotonic() >= fim:
                break
            time.sleep(0.5)
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
