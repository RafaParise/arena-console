# -*- coding: utf-8 -*-
"""
ARENA - prioridade e economia de energia dos processos (Windows).

Por que este arquivo existe (achado de 30/09/2026, testando de verdade):

  1. O ultra desempenho dizia "o emulador sobe para prioridade alta e o
     ARENA cai para a mais baixa". NENHUMA das duas acontecia:
       - o emulador era aberto com DUAS prioridades juntas (acima do normal
         + alta); o Windows aplica "acima do normal" -- a mesma de qualquer
         jogo fora do ultra;
       - a chamada que baixava o ARENA usava o ctypes SEM declarar os tipos.
         O "identificador do proprio processo" que o Windows devolve e' um
         numero de 64 bits; sem o tipo, o Python o cortava para 32 bits, o
         Windows recebia um identificador invalido e a chamada falhava em
         silencio (devolvia 0).
  2. O Windows 11 pode por um programa em "economia de energia" (EcoQoS:
     processador mais lento) quando acha que ele nao e' o que a pessoa esta
     usando -- por exemplo, o jogo na TV pelo HDMI e o foco na tela do
     notebook. Da para dizer ao Windows que o emulador NUNCA deve ser freado.

Tudo aqui e' documentado pela Microsoft e vale sem administrador, so para
os processos que o proprio ARENA abriu. Nada e' gravado no Windows: acabou
o processo, acabou o ajuste.
"""

import ctypes
import ctypes.wintypes as w
import os
import signal
import sys

# Classes de prioridade (SetPriorityClass, documentacao da Microsoft).
NORMAL = 0x00000020
ABAIXO_DO_NORMAL = 0x00004000
ACIMA_DO_NORMAL = 0x00008000
ALTA = 0x00000080
NOMES_PRIORIDADE = {0x40: "baixa", ABAIXO_DO_NORMAL: "abaixo do normal",
                    NORMAL: "normal", ACIMA_DO_NORMAL: "acima do normal",
                    ALTA: "alta", 0x100: "tempo real"}

# PROCESS_INFORMATION_CLASS (ordem da documentacao): 0 = memoria, 4 = energia.
_CLASSE_MEMORIA = 0
_CLASSE_ENERGIA = 4
# PROCESS_POWER_THROTTLING_STATE (processthreadsapi.h).
_VERSAO_ENERGIA = 1
_FREIO_VELOCIDADE = 0x1          # EXECUTION_SPEED: EcoQoS (processador mais lento)
_FREIO_RELOGIO = 0x4             # IGNORE_TIMER_RESOLUTION: relogio menos preciso
# MEMORY_PRIORITY_INFORMATION: 2 = baixa, 5 = normal.
MEMORIA_BAIXA = 2
MEMORIA_NORMAL = 5

_ACESSO_CONSULTA = 0x1000        # PROCESS_QUERY_LIMITED_INFORMATION
_ACESSO_AJUSTE = 0x0200          # PROCESS_SET_INFORMATION


class _Energia(ctypes.Structure):
    _fields_ = [("Version", w.ULONG), ("ControlMask", w.ULONG), ("StateMask", w.ULONG)]


class _Memoria(ctypes.Structure):
    _fields_ = [("MemoryPriority", w.ULONG)]


def _kernel32():
    """kernel32 com os tipos DECLARADOS (sem isso, o identificador de 64
    bits e' cortado -- ver o comentario do topo)."""
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.GetCurrentProcess.restype = w.HANDLE
    k.OpenProcess.restype = w.HANDLE
    k.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
    k.CloseHandle.argtypes = [w.HANDLE]
    k.SetPriorityClass.argtypes = [w.HANDLE, w.DWORD]
    k.GetPriorityClass.argtypes = [w.HANDLE]
    k.SetProcessInformation.argtypes = [w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD]
    k.GetProcessInformation.argtypes = [w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD]
    return k


def _no_windows():
    return sys.platform.startswith("win")


def prioridade_do_arena(classe):
    """Muda a prioridade do PROPRIO ARENA. Devolve True se o Windows aceitou."""
    if not _no_windows():
        return False
    try:
        k = _kernel32()
        return bool(k.SetPriorityClass(k.GetCurrentProcess(), classe))
    except (OSError, AttributeError):
        return False


def prioridade_de(pid=None):
    """Classe de prioridade de um processo (None = o proprio ARENA)."""
    if not _no_windows():
        return None
    k = _kernel32()
    if pid is None:
        return k.GetPriorityClass(k.GetCurrentProcess()) or None
    h = k.OpenProcess(_ACESSO_CONSULTA, False, pid)
    if not h:
        return None
    try:
        return k.GetPriorityClass(h) or None
    finally:
        k.CloseHandle(h)


def tirar_da_economia_de_energia(pid):
    """Diz ao Windows que este processo nunca deve ser freado para economizar
    energia: nem processador mais lento (EcoQoS), nem relogio impreciso quando
    a janela nao esta a vista. E' o exemplo "HighQoS" da documentacao de
    SetProcessInformation. Devolve True se o Windows aceitou."""
    if not _no_windows():
        return False
    try:
        k = _kernel32()
        h = k.OpenProcess(_ACESSO_AJUSTE, False, pid)
        if not h:
            return False
        try:
            estado = _Energia(_VERSAO_ENERGIA, _FREIO_VELOCIDADE | _FREIO_RELOGIO, 0)
            return bool(k.SetProcessInformation(h, _CLASSE_ENERGIA, ctypes.byref(estado),
                                                ctypes.sizeof(estado)))
        finally:
            k.CloseHandle(h)
    except (OSError, AttributeError):
        return False


def economia_de_energia_de(pid):
    """Como o Windows esta tratando a economia de energia deste processo:
    {'controle': mascara, 'ligado': mascara}, ou None. Serve para conferir."""
    if not _no_windows():
        return None
    k = _kernel32()
    h = k.OpenProcess(_ACESSO_CONSULTA, False, pid)
    if not h:
        return None
    try:
        estado = _Energia(_VERSAO_ENERGIA, 0, 0)
        if not k.GetProcessInformation(h, _CLASSE_ENERGIA, ctypes.byref(estado),
                                       ctypes.sizeof(estado)):
            return None
        return {"controle": estado.ControlMask, "ligado": estado.StateMask}
    finally:
        k.CloseHandle(h)


def memoria_do_arena(prioridade):
    """Prioridade de memoria do PROPRIO ARENA: com BAIXA, se faltar memoria
    durante o jogo, o Windows tira primeiro as paginas do servidor do ARENA,
    e nao as do jogo. Devolve True se o Windows aceitou."""
    if not _no_windows():
        return False
    try:
        k = _kernel32()
        info = _Memoria(prioridade)
        return bool(k.SetProcessInformation(k.GetCurrentProcess(), _CLASSE_MEMORIA,
                                            ctypes.byref(info), ctypes.sizeof(info)))
    except (OSError, AttributeError):
        return False


def memoria_de(pid=None):
    """Prioridade de memoria de um processo (None = o proprio ARENA)."""
    if not _no_windows():
        return None
    k = _kernel32()
    proprio = pid is None
    h = k.GetCurrentProcess() if proprio else k.OpenProcess(_ACESSO_CONSULTA, False, pid)
    if not h:
        return None
    try:
        info = _Memoria(0)
        if not k.GetProcessInformation(h, _CLASSE_MEMORIA, ctypes.byref(info),
                                       ctypes.sizeof(info)):
            return None
        return info.MemoryPriority
    finally:
        if not proprio:
            k.CloseHandle(h)


# ---------------------------------------------------------------------------
# A caixa que fecha os filhos (Job Object)
# ---------------------------------------------------------------------------
# Achado de 15/10/2026: o emulador do Java ME abre o Java ("javaw") como um
# processo separado. Fechando o jogo do jeito normal, o proprio nucleo encerra
# o Java. Mas se o RetroArch cai, ou e' fechado a forca, o Java do jogo fica
# aberto, escondido, gastando processador -- conferido: 40 s depois ainda
# estava la (num Celeron, o computador inteiro ficaria lento).
#
# A saida e' uma "caixa" do Windows (Job Object): o RetroArch entra nela, e
# tudo o que ele abrir entra junto. Quando o jogo acaba, o ARENA fecha a
# caixa, e o Windows encerra o que tiver sobrado dentro. Sem administrador.

_JOB_INFORMACAO_ESTENDIDA = 9         # JobObjectExtendedLimitInformation
_JOB_FECHA_TUDO_AO_FECHAR = 0x2000    # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
_ACESSO_CAIXA = 0x0100 | 0x0001       # PROCESS_SET_QUOTA | PROCESS_TERMINATE


class _JobBasica(ctypes.Structure):
    _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64),
                ("LimitFlags", w.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", w.DWORD),
                ("Affinity", ctypes.c_size_t), ("PriorityClass", w.DWORD),
                ("SchedulingClass", w.DWORD)]


class _JobIO(ctypes.Structure):
    _fields_ = [(nome, ctypes.c_ulonglong) for nome in
                ("ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                 "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]


class _JobEstendida(ctypes.Structure):
    _fields_ = [("BasicLimitInformation", _JobBasica), ("IoInfo", _JobIO),
                ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]


def _kernel32_caixa():
    k = _kernel32()
    k.CreateJobObjectW.restype = w.HANDLE
    k.CreateJobObjectW.argtypes = [ctypes.c_void_p, w.LPCWSTR]
    k.SetInformationJobObject.restype = w.BOOL
    k.SetInformationJobObject.argtypes = [w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD]
    k.AssignProcessToJobObject.restype = w.BOOL
    k.AssignProcessToJobObject.argtypes = [w.HANDLE, w.HANDLE]
    return k


def caixa_que_fecha_os_filhos(pid):
    """Poe o processo numa caixa que, quando fechada (fechar_caixa), encerra
    tudo o que ainda estiver dentro dela: os filhos que ele abriu e que
    ficaram para tras. Devolve a alca da caixa, ou None (se o sistema
    recusar: o jogo abre do mesmo jeito).

    No Linux (item 13), a caixa e' o grupo de processos do emulador: o ARENA
    o abre numa sessao propria (start_new_session, ver arena.py), e tudo o
    que ele abrir fica no mesmo grupo. So vale se o processo for o chefe do
    grupo: senao, fechar a caixa derrubaria o proprio ARENA."""
    if not _no_windows():
        try:
            return ("grupo", pid) if os.getpgid(pid) == pid else None
        except (OSError, AttributeError):
            return None
    try:
        k = _kernel32_caixa()
        caixa = k.CreateJobObjectW(None, None)
        if not caixa:
            return None
        estendida = _JobEstendida()
        estendida.BasicLimitInformation.LimitFlags = _JOB_FECHA_TUDO_AO_FECHAR
        h = k.OpenProcess(_ACESSO_CAIXA, False, pid)
        dentro = False
        if h:
            try:
                dentro = (k.SetInformationJobObject(caixa, _JOB_INFORMACAO_ESTENDIDA, ctypes.byref(estendida),
                                                    ctypes.sizeof(estendida))
                          and k.AssignProcessToJobObject(caixa, h))
            finally:
                k.CloseHandle(h)
        if not dentro:
            k.CloseHandle(caixa)
            return None
        return caixa
    except (OSError, AttributeError):
        return None


def fechar_caixa(caixa):
    """Fecha a caixa: o sistema encerra o que tiver sobrado dentro dela."""
    if isinstance(caixa, tuple) and caixa[0] == "grupo":
        try:
            os.killpg(caixa[1], signal.SIGKILL)
        except (OSError, AttributeError):
            pass                   # o grupo ja acabou: nada sobrou
        return
    if caixa:
        try:
            _kernel32().CloseHandle(caixa)
        except (OSError, AttributeError):
            pass
