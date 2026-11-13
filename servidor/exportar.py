# -*- coding: utf-8 -*-
r"""
ARENA - exportar jogos para o cartao SD (ou pen drive), no computador. Pedido do Rafael (13/11/2026): "deve ter a
opcao tambem de exportar jogos para o cartao SD".

O cartao SD no leitor do computador (ou um pen drive) recebe a pasta ARENA-jogos, com a mesma arrumacao que o ARENA do
celular cria no cartao (uma pasta por console: cartao_de_jogos.NOME_DA_PASTA). Encaixado no celular, o ARENA de la
acha a pasta em Ajustes -> Maquina -> Procurar jogos no cartao. A copia e' a do "Levar para o cartao" do celular
(cartao_de_jogos.levar_jogo), conferida arquivo por arquivo, mas aqui o original FICA no computador.

Aqui so a lista dos destinos possiveis: no Windows, as unidades removiveis (GetDriveTypeW = 2, o cartao no leitor e o
pen drive); no Linux, o que esta montado em /media e /run/media. A pasta do proprio ARENA nunca e' destino (ARENA
rodando do pen drive: exportar para ele mesmo nao faz sentido). So biblioteca padrao.
"""
import os
import shutil
import sys

import cartao_de_jogos

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)


def _livre_mb(caminho):
    try:
        return int(shutil.disk_usage(caminho).free / 1048576)
    except OSError:
        return None


def _windows():
    import ctypes
    from ctypes import wintypes
    k32 = ctypes.windll.kernel32
    k32.GetLogicalDrives.restype = wintypes.DWORD
    k32.GetDriveTypeW.argtypes = [wintypes.LPCWSTR]
    k32.GetDriveTypeW.restype = ctypes.c_uint
    k32.GetVolumeInformationW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD, ctypes.c_void_p,
                                          ctypes.c_void_p, ctypes.c_void_p, wintypes.LPWSTR, wintypes.DWORD]
    k32.GetVolumeInformationW.restype = wintypes.BOOL
    mascara = k32.GetLogicalDrives()
    saida = []
    for i in range(26):
        if not mascara & (1 << i):
            continue
        raiz = "%s:\\" % chr(ord("A") + i)
        if k32.GetDriveTypeW(raiz) != 2:          # DRIVE_REMOVABLE: o cartao no leitor e o pen drive
            continue
        nome = ctypes.create_unicode_buffer(261)
        sistema = ctypes.create_unicode_buffer(261)
        if not k32.GetVolumeInformationW(raiz, nome, 261, None, None, None, sistema, 261):
            continue                              # leitor vazio (sem cartao)
        saida.append({"raiz": raiz, "nome": nome.value or "Disco removível", "sistema": sistema.value})
    return saida


def _linux():
    usuario = os.environ.get("USER") or ""
    pastas = [os.path.join("/media", usuario), os.path.join("/run/media", usuario), "/media"]
    saida, vistos = [], set()
    for base in pastas:
        try:
            nomes = sorted(os.listdir(base))
        except OSError:
            continue
        for nome in nomes:
            raiz = os.path.join(base, nome)
            if raiz in vistos or not os.path.ismount(raiz):
                continue
            vistos.add(raiz)
            saida.append({"raiz": raiz, "nome": nome, "sistema": ""})
    return saida


def destinos():
    """[{raiz, nome, sistema, livre_mb, tem_pasta, pasta}] dos cartoes e pen drives ligados agora (sem o do ARENA)."""
    try:
        achados = _windows() if sys.platform.startswith("win") else _linux()
    except (OSError, AttributeError):
        achados = []
    proprio = os.path.normcase(os.path.splitdrive(RAIZ)[0] + "\\") if sys.platform.startswith("win") else None
    saida = []
    for d in achados:
        if proprio and os.path.normcase(d["raiz"]) == proprio:
            continue
        if not sys.platform.startswith("win") and os.path.realpath(RAIZ).startswith(os.path.realpath(d["raiz"]) + os.sep):
            continue
        pasta = os.path.join(d["raiz"], cartao_de_jogos.NOME_DA_PASTA)
        saida.append(dict(d, livre_mb=_livre_mb(d["raiz"]), tem_pasta=os.path.isdir(pasta), pasta=pasta))
    return saida


def destino_valido(raiz):
    """A pasta ARENA-jogos do destino pedido, se ele ainda esta na lista; senao None."""
    for d in destinos():
        if os.path.normcase(os.path.abspath(d["raiz"])) == os.path.normcase(os.path.abspath(str(raiz or ""))):
            return d["pasta"]
    return None
