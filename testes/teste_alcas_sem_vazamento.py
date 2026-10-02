# -*- coding: utf-8 -*-
r"""O servidor nao deixa alcas (handles) do Windows abertas a cada pedido.

Achado de 02/10/2026 (teste_longa_duracao): as alcas do servidor subiam de
420 para 181.570 em 3 minutos de pedidos -- 24 por /api/estado e 48 por
ajuste salvo. Causa: opcoes_efetivas() contava os controles ligados em
TODA chamada (nao so na hora de abrir o jogo), e a contagem usava o
joyGetPosEx do Windows, que deixa alcas abertas quando o controle esta
desligado (os GameSir sem fio, de madrugada). Num dia de aula, horas de
tela aberta = centenas de milhares de alcas -- ate o Windows recusar.

  1. controles.contar_controles() 100 vezes: quase nenhuma alca nova;
  2. num ARENA isolado (copia temporaria, no mesmo processo): 200 pedidos
     de /api/estado e 200 de POST /api/config: quase nenhuma alca nova.
     (O teste_longa_duracao mede o mesmo por 3 minutos.)

Uso: servidor\python\python.exe testes\teste_alcas_sem_vazamento.py
"""
import ctypes
import json
import os
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from ctypes import wintypes

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
import fuzz_rotas  # noqa: E402
import limpeza  # noqa: E402

PORTA = 18878
_k = ctypes.WinDLL("kernel32")
_k.GetCurrentProcess.restype = wintypes.HANDLE
_k.GetProcessHandleCount.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]


def alcas():
    n = wintypes.DWORD(0)
    _k.GetProcessHandleCount(_k.GetCurrentProcess(), ctypes.byref(n))
    return n.value


def pedir(metodo, caminho, corpo=None):
    dados = json.dumps(corpo).encode() if corpo is not None else None
    req = urllib.request.Request("http://127.0.0.1:%d%s" % (PORTA, caminho), data=dados, method=metodo,
                                 headers={"Content-Type": "application/json", "Host": "127.0.0.1:%d" % PORTA})
    try:
        with urllib.request.urlopen(req, timeout=20) as resposta:
            resposta.read()
    except urllib.error.HTTPError as erro:
        erro.read()
        erro.close()


def main():
    falhas, total = [], [0]

    def confere(nome, ok, detalhe=""):
        total[0] += 1
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, "" if ok else detalhe))
        if not ok:
            falhas.append(nome)

    sys.path.insert(0, os.path.join(RAIZ, "servidor"))
    import controles
    # O XInput abre umas 40 alcas UMA vez, na primeira carga (medido): nao e'
    # vazamento. Aquece antes de contar.
    for _ in range(50):
        controles.contar_controles()
    time.sleep(0.5)
    antes = alcas()
    for _ in range(100):
        controles.contar_controles()
    novas = alcas() - antes
    confere("contar os controles 100 vezes: quase nenhuma alca nova (eram 2.400)", novas < 20, novas)

    pasta = os.path.join(tempfile.mkdtemp(prefix="arena_alcas_"), "ARENA")
    os.makedirs(pasta)
    servidor = None
    try:
        fuzz_rotas.preparar_ambiente(pasta)
        arena = fuzz_rotas.carregar_arena_isolado(pasta)
        servidor = arena.Servidor(("127.0.0.1", PORTA), arena.Manipulador)
        threading.Thread(target=servidor.serve_forever, daemon=True).start()
        time.sleep(0.5)
        for metodo, caminho, corpo, era in (("GET", "/api/estado", None, 24),
                                            ("POST", "/api/config", {"tema": "escuro"}, 48)):
            for _ in range(20):
                pedir(metodo, caminho, corpo)        # aquece (cache, primeiras alocacoes)
            time.sleep(0.5)
            antes = alcas()
            for _ in range(200):
                pedir(metodo, caminho, corpo)
            time.sleep(1.0)
            novas = alcas() - antes
            confere("%s %s 200 vezes: quase nenhuma alca nova (eram ~%d por pedido)" % (metodo, caminho, era),
                    novas < 50, novas)
    finally:
        if servidor:
            servidor.shutdown()
            servidor.server_close()
        sys.path = [p for p in sys.path if not p.startswith(pasta)]
        limpeza.apagar_pasta(os.path.dirname(pasta))

    print()
    if falhas:
        print("FALHOU: %d de %d" % (len(falhas), total[0]))
        return 1
    print("Alcas sem vazamento: %d de %d certos." % (total[0], total[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
