# -*- coding: utf-8 -*-
r"""A tela continua respondendo enquanto o ARENA rele 5.000 jogos.

Auditoria 3 (o roteiro, Fase 2: "gere 5.000 arquivos de jogo falsos [...]
Meca o tempo de indexacao e confirme que a tela continua respondendo").

Achado (08/10/2026): a releitura dos jogos ("Atualizar lista") segurava,
do comeco ao fim, a mesma trava que a leitura da configuracao usa -- e
quase toda rota le a configuracao. Enquanto o ARENA relia os jogos (7 s com
5.000 no Ryzen; ~16 s no Celeron da escola), a tela inteira ficava parada
esperando.

Numa copia isolada do ARENA (servidor de verdade, porta livre), com 5.000
jogos falsos (arquivos vazios em 3 consoles): pede "Atualizar lista" e, ao
mesmo tempo, pede o estado da tela a cada 0,2 s. Confere que nenhum pedido
do estado demora mais que 1 s, e que a releitura achou os 5.000.

Uso: servidor\python\python.exe testes\teste_tela_responde_indexando.py
"""
import json
import os
import socket
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import limpeza  # noqa: E402
import teste_servidor_que_cai as servidor_de_teste  # noqa: E402

JOGOS_FALSOS = 5000
CONSOLES = (("NES", ".nes"), ("Super Nintendo", ".sfc"), ("Game Boy", ".gb"))
LIMITE_S = 1.0


def porta_livre():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def pedir(porta, metodo, caminho, espera=120):
    dados = b"{}" if metodo == "POST" else None
    req = urllib.request.Request("http://127.0.0.1:%d%s" % (porta, caminho), data=dados, method=metodo,
                                 headers={"Content-Type": "application/json"})
    inicio = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=espera) as resposta:
            corpo = json.loads(resposta.read() or b"{}")
            return resposta.status, corpo, time.monotonic() - inicio
    except (urllib.error.URLError, OSError, ValueError):
        return None, {}, time.monotonic() - inicio


def main():
    falhas, total = [], [0]

    def confere(nome, ok, detalhe=""):
        total[0] += 1
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, "" if ok else detalhe), flush=True)
        if not ok:
            falhas.append(nome)

    base = tempfile.mkdtemp(prefix="arena_tela_indexando_")
    processo = None
    try:
        copia = os.path.join(base, "ARENA")
        servidor_de_teste.preparar_copia(copia)
        for n in range(JOGOS_FALSOS):
            pasta, extensao = CONSOLES[n % len(CONSOLES)]
            destino = os.path.join(copia, "jogos", "pessoais", pasta, "_estresse")
            os.makedirs(destino, exist_ok=True)
            with open(os.path.join(destino, "Jogo Falso %05d%s" % (n, extensao)), "wb"):
                pass
        porta = porta_livre()
        processo = servidor_de_teste.subir(copia, porta, False, os.path.join(base, "sem-trava"))
        if not servidor_de_teste.esperar_servidor(porta, segundos=120):
            print("FALHOU: o servidor da copia nao abriu.")
            return 1
        pedir(porta, "GET", "/api/catalogo")            # a primeira leitura (fria) fica de fora

        resultado = {}

        def reindexar():
            status, corpo, segundos = pedir(porta, "POST", "/api/indexar")
            resultado.update(status=status, total=corpo.get("total"), segundos=segundos)

        linha = threading.Thread(target=reindexar)
        linha.start()
        tempos = []
        time.sleep(0.1)
        while linha.is_alive():
            status, _corpo, segundos = pedir(porta, "GET", "/api/estado", espera=60)
            tempos.append((status, segundos))
            time.sleep(0.2)
        linha.join()

        print("Releitura: %s jogos em %.1f s; %d pedidos do estado no meio, o mais lento em %.2f s"
              % (resultado.get("total"), resultado.get("segundos", 0), len(tempos),
                 max((s for _st, s in tempos), default=0)))
        confere("a releitura achou os %d jogos falsos" % JOGOS_FALSOS,
                resultado.get("status") == 200 and (resultado.get("total") or 0) >= JOGOS_FALSOS, resultado)
        confere("a tela foi atendida durante a releitura (%d pedidos)" % len(tempos),
                len(tempos) >= 3 and all(st == 200 for st, _s in tempos), tempos[:5])
        lento = max((s for _st, s in tempos), default=0)
        confere("nenhum pedido do estado esperou mais de %.0f s (o mais lento: %.2f s)" % (LIMITE_S, lento),
                lento <= LIMITE_S, lento)
    finally:
        if processo:
            servidor_de_teste.derrubar(processo)
        limpeza.apagar_pasta(base)

    print()
    if falhas:
        print("FALHOU: %d de %d" % (len(falhas), total[0]))
        return 1
    print("A tela responde durante a releitura: %d de %d certos." % (total[0], total[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
