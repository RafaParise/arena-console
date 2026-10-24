# -*- coding: utf-8 -*-
"""Programas que abrem JUNTO com o jogo e fecham com ele.

O primeiro e' o DreamPotato (github.com/RikkiGibson/DreamPotato, licenca MIT): um VMU do Dreamcast de verdade numa janela
a parte. Com o encaixe "DreamPotato" ligado em Acessorios, o Flycast fala com ele pela rede do proprio computador
(127.0.0.1): a telinha, os botoes, o som e a MEMORIA do VMU passam a ser os do jogo, e o que se faz de um lado vale do outro.

O ARENA nao leva o DreamPotato no pacote: o zip dele traz a BIOS do VMU da Sega (american_v1.05.bin), que nao se distribui.
Quem quer usar baixa o zip e poe em emuladores\\DreamPotato (o ARENA procura ali). Sem a pasta, nada acontece e o jogo abre
do mesmo jeito.

Mesmo desenho do Lossless Scaling (servidor\\lossless.py): abre antes do jogo, fecha no fim, e so fecha o que o ARENA abriu."""
import os
import subprocess
import sys
import threading
import time

PASTA_SERVIDOR = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(PASTA_SERVIDOR)

# id -> onde procurar. "exe": o arquivo do programa, por sistema; "pasta": a pasta dele dentro de emuladores\.
PROGRAMAS = {
    "dreampotato": {"nome": "DreamPotato", "pasta": "DreamPotato",
                    "exe": {"windows": "DreamPotato.exe", "linux": "DreamPotato"}},
}

_TRAVA = threading.Lock()
_ABERTOS = {}          # id -> processo que o ARENA abriu


def _sistema():
    return "windows" if os.name == "nt" else "linux"


def achar(programa, raiz=None):
    """O caminho do programa em emuladores\\<pasta>, ou None se nao estiver la (ou se o id nao existir)."""
    ficha = PROGRAMAS.get(programa)
    if not ficha:
        return None
    nome = ficha["exe"].get(_sistema())
    caminho = os.path.join(raiz or RAIZ, "emuladores", ficha["pasta"], nome or "")
    return caminho if nome and os.path.isfile(caminho) else None


def abrir(programa, raiz=None):
    """Abre o programa (se achar e se ainda nao estiver aberto por aqui). Devolve True se o ARENA abriu agora."""
    caminho = achar(programa, raiz)
    if not caminho:
        return False
    with _TRAVA:
        antigo = _ABERTOS.get(programa)
        if antigo is not None and antigo.poll() is None:
            return False
        try:
            _ABERTOS[programa] = subprocess.Popen([caminho], cwd=os.path.dirname(caminho),
                                                  stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                                  stderr=subprocess.DEVNULL)
        except OSError as falha:
            print("[ARENA] Nao consegui abrir o %s: %s" % (PROGRAMAS[programa]["nome"], falha))
            return False
    return True


def abrir_todos(programas, raiz=None):
    """Abre cada programa da lista; devolve os ids que o ARENA abriu agora."""
    return [p for p in programas if abrir(p, raiz)]


def fechar_os_que_o_arena_abriu(espera=6.0):
    """Fecha o que o ARENA abriu (o que a pessoa ja tinha aberto antes fica). Pede com educacao e, se nao fechar, forca."""
    with _TRAVA:
        abertos = dict(_ABERTOS)
        _ABERTOS.clear()
    fechados = []
    for programa, processo in abertos.items():
        if processo.poll() is None:
            try:
                processo.terminate()
                limite = time.monotonic() + espera
                while time.monotonic() < limite and processo.poll() is None:
                    time.sleep(0.2)
                if processo.poll() is None:
                    processo.kill()
                    processo.wait(5)
            except OSError:
                pass
        fechados.append(programa)
    return fechados


if __name__ == "__main__":
    for programa in PROGRAMAS:
        print(programa, "->", achar(programa) or "nao esta em emuladores\\" + PROGRAMAS[programa]["pasta"], file=sys.stderr)
