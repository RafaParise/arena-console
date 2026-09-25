# -*- coding: utf-8 -*-
r"""Mostra em qual numero o Windows colocou cada controle.

Le direto do Windows, sem administrador e sem instalar nada:
  - XInput (numeros 0 a 3): e o que o RetroArch usa. Numero 0 = jogador 1,
    1 = jogador 2, e assim por diante.
  - winmm (lista antiga de joysticks): pega tambem controle que NAO esta no
    modo XInput (modo Switch/Android/DirectInput) -- esse o RetroArch com
    XInput nao enxerga.

Aperte UM controle de cada vez; o script escreve qual numero mexeu.
Fica ouvindo pelo tempo pedido (padrao 60 s). Ctrl+C para antes.

Uso: servidor\python\python.exe ferramentas\testar_controles.py [segundos]
"""
import ctypes
import sys
import time
from ctypes import wintypes

BOTOES_XINPUT = [
    (0x0001, "cima"), (0x0002, "baixo"), (0x0004, "esquerda"), (0x0008, "direita"),
    (0x0010, "Start"), (0x0020, "Back/Select"), (0x0040, "L3"), (0x0080, "R3"),
    (0x0100, "LB"), (0x0200, "RB"), (0x1000, "A"), (0x2000, "B"),
    (0x4000, "X"), (0x8000, "Y"),
]


class GAMEPAD(ctypes.Structure):
    _fields_ = [("wButtons", wintypes.WORD), ("bLeftTrigger", ctypes.c_ubyte),
                ("bRightTrigger", ctypes.c_ubyte), ("sThumbLX", ctypes.c_short),
                ("sThumbLY", ctypes.c_short), ("sThumbRX", ctypes.c_short),
                ("sThumbRY", ctypes.c_short)]


class ESTADO(ctypes.Structure):
    _fields_ = [("dwPacketNumber", wintypes.DWORD), ("Gamepad", GAMEPAD)]


class JOYINFOEX(ctypes.Structure):
    _fields_ = [(nome, wintypes.DWORD) for nome in (
        "dwSize", "dwFlags", "dwXpos", "dwYpos", "dwZpos", "dwRpos", "dwUpos",
        "dwVpos", "dwButtons", "dwButtonNumber", "dwPOV", "dwReserved1",
        "dwReserved2")]


def abrir_xinput():
    for nome in ("xinput1_4", "xinput1_3", "xinput9_1_0"):
        try:
            return getattr(ctypes.windll, nome)
        except OSError:
            continue
    return None


def ler_xinput(xinput, numero):
    estado = ESTADO()
    if xinput.XInputGetState(numero, ctypes.byref(estado)) != 0:
        return None
    return estado


def descrever_xinput(estado):
    g = estado.Gamepad
    partes = [nome for bit, nome in BOTOES_XINPUT if g.wButtons & bit]
    if g.bLeftTrigger > 60:
        partes.append("LT")
    if g.bRightTrigger > 60:
        partes.append("RT")
    if abs(g.sThumbLX) > 12000 or abs(g.sThumbLY) > 12000:
        partes.append("analogico esquerdo")
    if abs(g.sThumbRX) > 12000 or abs(g.sThumbRY) > 12000:
        partes.append("analogico direito")
    return partes


def ler_winmm(winmm, numero):
    info = JOYINFOEX()
    info.dwSize = ctypes.sizeof(JOYINFOEX)
    info.dwFlags = 0xFF  # JOY_RETURNALL
    if winmm.joyGetPosEx(numero, ctypes.byref(info)) != 0:
        return None
    return info


def main():
    duracao = float(sys.argv[1]) if len(sys.argv) > 1 else 60.0
    xinput = abrir_xinput()
    winmm = ctypes.windll.winmm

    print("=== Controles que o Windows ve agora ===")
    ligados_x = [n for n in range(4) if xinput and ler_xinput(xinput, n)]
    print("XInput (o que o RetroArch usa): numeros", ligados_x or "nenhum",
          "-> %d controle(s)" % len(ligados_x))
    ligados_w = [n for n in range(16) if ler_winmm(winmm, n)]
    print("winmm (lista antiga, pega qualquer modo): numeros", ligados_w or "nenhum",
          "-> %d controle(s)" % len(ligados_w))
    print("\nAgora aperte UM controle de cada vez (%d s)...\n" % duracao)

    anterior_x = {n: None for n in range(4)}
    anterior_w = {}
    fim = time.time() + duracao
    try:
        while time.time() < fim:
            for n in range(4):
                estado = ler_xinput(xinput, n) if xinput else None
                partes = descrever_xinput(estado) if estado else None
                if partes and partes != anterior_x[n]:
                    print("XInput %d (jogador %d no RetroArch): %s"
                          % (n, n + 1, ", ".join(partes)))
                anterior_x[n] = partes
            for n in ligados_w:
                info = ler_winmm(winmm, n)
                botoes = info.dwButtons if info else 0
                if botoes and botoes != anterior_w.get(n):
                    lista = [str(b) for b in range(32) if botoes & (1 << b)]
                    print("   winmm %d: botao(oes) %s" % (n, ", ".join(lista)))
                anterior_w[n] = botoes
            time.sleep(0.03)
    except KeyboardInterrupt:
        pass
    print("\nFim.")


if __name__ == "__main__":
    main()
