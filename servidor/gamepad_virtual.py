# -*- coding: utf-8 -*-
r"""
ARENA - o celular como gamepad XInput (Xbox 360) VIRTUAL no Windows, para qualquer jogo (como o DroidJoy).

AUTORIZADO PELO RAFAEL em 26/10/2026 ("eu autorizo por gentileza a realizar") como EXCECAO a regra "sem driver" do
projeto. Por isso e' OPCIONAL e fica de fora do que o ARENA faz sozinho:
  * precisa do driver ViGEmBus (de kernel, assinado; instalado com administrador: `winget install ViGEm.ViGEmBus`);
    o ARENA nunca o instala. Sem ele, tudo aqui diz "nao esta instalado" e o resto do ARENA segue igual;
  * usa o ViGEmClient.dll (MIT, do projeto ViGEm; vai em servidor\vigem\), pelo ctypes;
  * so liga com o professor marcando, e some quando o controle remoto desliga.
O ViGEmBus foi aposentado pelo autor em 2023 (nao recebe mais atualizacao): serve, mas e' um risco que o professor
escolhe correr. Nao vale para a maquina da escola sem administrador.
"""
import ctypes
import os
import sys
import threading

DLL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vigem", "ViGEmClient.dll")

# RetroPad (bit) -> botao do XUSB_REPORT
XUSB = {4: 0x0001, 5: 0x0002, 6: 0x0004, 7: 0x0008,        # cima baixo esquerda direita
        3: 0x0010, 2: 0x0020, 14: 0x0040, 15: 0x0080,      # start select(back) L3 R3
        10: 0x0100, 11: 0x0200,                            # L1 R1
        0: 0x1000, 8: 0x2000, 1: 0x4000, 9: 0x8000}        # B->A, A->B, Y->X, X->Y (posicao, nao letra)


class Relatorio(ctypes.Structure):
    _fields_ = [("botoes", ctypes.c_ushort), ("gatilho_e", ctypes.c_ubyte), ("gatilho_d", ctypes.c_ubyte),
                ("lx", ctypes.c_short), ("ly", ctypes.c_short), ("rx", ctypes.c_short), ("ry", ctypes.c_short)]


def converter(botoes, eixos):
    """(botoes do RetroPad, [lx, ly, rx, ry]) -> Relatorio do Xbox 360. O Y do RetroPad cresce para baixo; o do XInput, para cima."""
    r = Relatorio()
    for bit, valor in XUSB.items():
        if botoes & (1 << bit):
            r.botoes |= valor
    r.gatilho_e = 255 if botoes & (1 << 12) else 0
    r.gatilho_d = 255 if botoes & (1 << 13) else 0
    lx, ly, rx, ry = (max(-32767, min(32767, int(v))) for v in eixos)
    r.lx, r.ly, r.rx, r.ry = lx, -ly, rx, -ry
    return r


class GamepadVirtual:
    def __init__(self, dll=DLL):
        self._dll = dll
        self._lib = None
        self._cliente = None
        self._alvos = {}
        self._trava = threading.Lock()   # cada jogador roda numa linha de execucao: o fechar nao pode cruzar com o atualizar
        self._fechado = False

    def disponivel(self):
        """(ok, motivo): o driver e a DLL estao ai?"""
        if not sys.platform.startswith("win"):
            return False, "O gamepad virtual só existe no Windows."
        if not os.path.isfile(self._dll):
            return False, "Falta o ViGEmClient.dll em servidor\\vigem."
        try:
            lib = ctypes.WinDLL(self._dll)
            lib.vigem_alloc.restype = ctypes.c_void_p
            cliente = lib.vigem_alloc()
            lib.vigem_connect.argtypes = [ctypes.c_void_p]
            erro = lib.vigem_connect(cliente) if cliente else -1
            lib.vigem_disconnect.argtypes = [ctypes.c_void_p]
            lib.vigem_free.argtypes = [ctypes.c_void_p]
            if cliente:
                if erro == 0x20000000:
                    lib.vigem_disconnect(cliente)
                lib.vigem_free(cliente)
            if erro != 0x20000000:
                return False, "O driver ViGEmBus não está instalado (instale com: winget install ViGEm.ViGEmBus, como administrador)."
        except OSError as falha:
            return False, "Não consegui abrir o ViGEmClient.dll (%s)." % falha
        return True, ""

    def _ligar(self):
        if self._cliente:
            return
        lib = ctypes.WinDLL(self._dll)
        lib.vigem_alloc.restype = ctypes.c_void_p
        for nome in ("vigem_connect", "vigem_disconnect", "vigem_free", "vigem_target_x360_alloc"):
            getattr(lib, nome).argtypes = [ctypes.c_void_p] if nome != "vigem_target_x360_alloc" else []
        lib.vigem_target_x360_alloc.restype = ctypes.c_void_p
        lib.vigem_target_add.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        lib.vigem_target_remove.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        lib.vigem_target_free.argtypes = [ctypes.c_void_p]
        lib.vigem_target_x360_update.argtypes = [ctypes.c_void_p, ctypes.c_void_p, Relatorio]
        cliente = lib.vigem_alloc()
        if lib.vigem_connect(cliente) != 0x20000000:
            raise OSError("O driver ViGEmBus não respondeu.")
        self._lib, self._cliente = lib, cliente

    def atualizar(self, jogador, botoes, eixos):
        """Cria o gamepad do jogador na primeira vez e manda o estado. Depois de fechar(), nao faz nada (nao religa o driver)."""
        with self._trava:
            if not self._fechado:
                self._atualizar(jogador, botoes, eixos)

    def _atualizar(self, jogador, botoes, eixos):
        self._ligar()
        alvo = self._alvos.get(jogador)
        if alvo is None:
            alvo = self._lib.vigem_target_x360_alloc()
            if self._lib.vigem_target_add(self._cliente, alvo) != 0x20000000:
                self._lib.vigem_target_free(alvo)
                raise OSError("O Windows não deixou criar o gamepad virtual.")
            self._alvos[jogador] = alvo
        self._lib.vigem_target_x360_update(self._cliente, alvo, converter(botoes, eixos))

    def soltar(self, jogador):
        with self._trava:
            if jogador in self._alvos and not self._fechado:
                self._atualizar(jogador, 0, [0, 0, 0, 0])

    def remover(self, jogador):
        with self._trava:
            self._remover(jogador)

    def _remover(self, jogador):
        alvo = self._alvos.pop(jogador, None)
        if alvo is not None and self._cliente:
            self._lib.vigem_target_remove(self._cliente, alvo)
            self._lib.vigem_target_free(alvo)

    def fechar(self):
        with self._trava:
            self._fechado = True
            for jogador in list(self._alvos):
                self._remover(jogador)
            if self._cliente:
                self._lib.vigem_disconnect(self._cliente)
                self._lib.vigem_free(self._cliente)
                self._cliente = None
