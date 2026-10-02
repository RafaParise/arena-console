# -*- coding: utf-8 -*-
r"""Modo alvo: o ARENA aberto NESTE computador com os limites do notebook-alvo.

Tarefa 3 do Rafael (pausada em 30/09, feita em 02/10/2026). O notebook-alvo
(docs\MAQUINA-ALVO.md) e' um Celeron N5100: 4 nucleos, cada um com uns 43%
da velocidade de um nucleo do Ryzen 5 5600G daqui (PassMark 1.361 x ~3.150),
e 3,8 GB de memoria livre. Aqui o ARENA roda dentro de uma "caixa" do
Windows (Job Object) com esses limites -- e tudo o que ele abrir (RetroArch,
emuladores, a tela) cai na mesma caixa:
  - so 4 processadores logicos (afinidade da caixa);
  - cada um a ~43% (teto de processador da caixa, "hard cap"): o que e'
    pesado para o processador fica lento como la;
  - memoria: 3,8 GB para tudo, somado (o que sobra livre la);
  - prioridade abaixo do normal (o Windows de la vive ocupado com outras
    coisas).
Tudo pela documentacao oficial da Microsoft (CreateJobObjectW,
SetInformationJobObject, AssignProcessToJobObject) e SEM administrador: o
programa so limita a si mesmo e aos filhos. Nada e' gravado no Windows; ao
fechar, acabou.

O QUE O MODO ALVO NAO IMITA (julgue esses pela coleta de la, o COLETAR.bat):
  - disco lento: o eMMC/pen drive de la e' muito mais lento que o NVMe daqui;
  - placa de video fraca: a Intel UHD de 24 EU de la (o limite aqui e' so de
    processador; a Radeon daqui continua desenhando rapido);
  - falta de AVX: o processador daqui tem AVX; o Xenia (Xbox 360) abre aqui
    e la fecha na hora;
  - o Windows de la: antivirus, programas de inicializacao, memoria em canal
    simples, driver de video de 2021.

Uso:
    servidor\python\python.exe ferramentas\modo_alvo.py              (abre o ARENA)
    servidor\python\python.exe ferramentas\modo_alvo.py <comando...> (outro programa)
Nos testes: import modo_alvo; modo_alvo.entrar() -- a partir dai, este
processo e os filhos estao na caixa.
"""
import ctypes
import os
import subprocess
import sys
from ctypes import wintypes

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# O notebook-alvo (docs\MAQUINA-ALVO.md, maquina D682F0CCEB).
NUCLEOS = 2                   # a especificacao da tarefa 3 (o N5100 tem 4, mas cada um vale ~43%)
VELOCIDADE_PCT = 43          # % de um nucleo DESTE PC (Ryzen 5 5600G)
MEMORIA_MB = 3800
ABAIXO_DO_NORMAL = 0x4000    # BELOW_NORMAL_PRIORITY_CLASS

_JobObjectExtendedLimitInformation = 9
_JobObjectCpuRateControlInformation = 15
_LIMIT_AFFINITY = 0x10
_LIMIT_PRIORITY_CLASS = 0x20
_LIMIT_JOB_MEMORY = 0x200
_CPU_RATE_ENABLE = 0x1
_CPU_RATE_HARD_CAP = 0x4


class _BASICA(ctypes.Structure):
    _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64),
                ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD)]


class _IO(ctypes.Structure):
    _fields_ = [(nome, ctypes.c_ulonglong) for nome in
                ("ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                 "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]


class _ESTENDIDA(ctypes.Structure):
    _fields_ = [("BasicLimitInformation", _BASICA), ("IoInfo", _IO),
                ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]


class _TAXA(ctypes.Structure):
    _fields_ = [("ControlFlags", wintypes.DWORD), ("CpuRate", wintypes.DWORD)]


def _kernel32():
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.CreateJobObjectW.restype = wintypes.HANDLE
    k.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    k.SetInformationJobObject.restype = wintypes.BOOL
    k.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    k.AssignProcessToJobObject.restype = wintypes.BOOL
    k.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    k.GetCurrentProcess.restype = wintypes.HANDLE
    return k


def processadores_deste_pc():
    return os.cpu_count() or 1


def taxa_da_caixa(nucleos, velocidade_pct, total=None):
    """O teto de processador da caixa, na unidade do Windows (ciclos em cada
    10.000 do computador INTEIRO): 4 nucleos a 43% num PC de 12 = 1.433."""
    total = total or processadores_deste_pc()
    return max(1, min(10000, int(round(nucleos * velocidade_pct * 100.0 / total))))


_caixa = {"alca": None, "descricao": ""}


def entrar(nucleos=NUCLEOS, velocidade_pct=VELOCIDADE_PCT, memoria_mb=MEMORIA_MB,
           prioridade=ABAIXO_DO_NORMAL):
    """Poe ESTE processo (e todos os filhos que ele abrir daqui em diante)
    na caixa com os limites do notebook-alvo. Devolve a descricao, ou
    levanta OSError dizendo o que o Windows recusou."""
    if os.name != "nt":
        raise OSError("o modo alvo e' do Windows")
    if _caixa["alca"]:
        return _caixa["descricao"]
    k = _kernel32()
    alca = k.CreateJobObjectW(None, None)
    if not alca:
        raise OSError("o Windows nao criou a caixa (erro %d)" % ctypes.get_last_error())
    total = processadores_deste_pc()
    nucleos = max(1, min(nucleos, total))
    estendida = _ESTENDIDA()
    basica = estendida.BasicLimitInformation
    basica.LimitFlags = _LIMIT_AFFINITY | _LIMIT_PRIORITY_CLASS | _LIMIT_JOB_MEMORY
    basica.Affinity = (1 << nucleos) - 1          # os primeiros N processadores logicos
    basica.PriorityClass = prioridade
    estendida.JobMemoryLimit = int(memoria_mb) * 1024 * 1024
    if not k.SetInformationJobObject(alca, _JobObjectExtendedLimitInformation,
                                     ctypes.byref(estendida), ctypes.sizeof(estendida)):
        raise OSError("o Windows recusou os limites da caixa (erro %d)" % ctypes.get_last_error())
    taxa = _TAXA(_CPU_RATE_ENABLE | _CPU_RATE_HARD_CAP, taxa_da_caixa(nucleos, velocidade_pct, total))
    if not k.SetInformationJobObject(alca, _JobObjectCpuRateControlInformation,
                                     ctypes.byref(taxa), ctypes.sizeof(taxa)):
        raise OSError("o Windows recusou o teto de processador (erro %d)" % ctypes.get_last_error())
    if not k.AssignProcessToJobObject(alca, k.GetCurrentProcess()):
        raise OSError("o Windows nao deixou entrar na caixa (erro %d)" % ctypes.get_last_error())
    _caixa["alca"] = alca
    _caixa["descricao"] = ("modo alvo: %d processadores a ~%d%% (teto %d/10.000 de %d), %d MB de memoria, "
                           "prioridade abaixo do normal" % (nucleos, velocidade_pct, taxa.CpuRate, total,
                                                            memoria_mb))
    return _caixa["descricao"]


def principal():
    descricao = entrar()
    print("ARENA no " + descricao)
    print("NAO imita: disco lento, placa de video fraca, falta de AVX, o Windows de la.")
    comando = sys.argv[1:] or ["cmd.exe", "/d", "/c", os.path.join(RAIZ, "ARENA.bat")]
    return subprocess.call(comando, cwd=RAIZ)


if __name__ == "__main__":
    sys.exit(principal())
