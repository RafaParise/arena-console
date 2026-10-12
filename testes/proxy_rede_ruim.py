# -*- coding: utf-8 -*-
"""Fase 4: simulador de rede ruim entre o hospedeiro e um convidado do
Jogar Junto. Python puro (so biblioteca padrao), sem instalar nada.

Fica no meio: o convidado conecta NELE (em vez de conectar direto no
hospedeiro), e ele repassa os bytes pros dois lados. Cada pedaco que chega
sai do outro lado ATRASO_MS milissegundos depois -- e na ordem, como no
TCP (o RetroArch usa TCP para a partida). Com a chance PERDA_PCT, o pedaco
"se perde": no TCP o dado nao some, ele e' reenviado, e chega uma volta
inteira (ida e volta) + 200 ms mais tarde -- e tudo o que vem atras dele
espera junto (o TCP entrega em ordem). E' assim que perda de pacote se
sente de verdade numa partida pela rede.

Auditoria 3 (08/10/2026): a versao anterior dormia o atraso a cada leitura,
na mesma linha que lia -- o atraso de verdade ia de 1 a 2 vezes o pedido,
conforme o vai e vem. E o convidado nem passava por aqui: o RetroArch
ignora o "--port" da linha de comando (testes\\teste_rede_ruim.py).

Uso:
    python proxy_rede_ruim.py <porta_local> <host_de_verdade> <porta_de_verdade> <atraso_ms> <perda_pct>

Exemplo (proxy na porta 55440, host de verdade em 127.0.0.1:55435,
100ms de atraso, 5% de perda):
    python proxy_rede_ruim.py 55440 127.0.0.1 55435 100 5
"""
import queue
import random
import socket
import sys
import threading
import time


def repassar(origem, destino, atraso_s, perda_pct, rotulo, contagem):
    """Le de um lado e entrega do outro no instante chegada + atraso, em
    ordem. Uma linha le, outra entrega: ler nunca espera a entrega."""
    fila = queue.Queue()

    def entregar():
        while True:
            item = fila.get()
            if item is None:
                break
            hora, dado = item
            espera = hora - time.monotonic()
            if espera > 0:
                time.sleep(espera)
            try:
                destino.sendall(dado)
            except OSError:
                break
        try:
            destino.shutdown(socket.SHUT_WR)
        except OSError:
            pass

    entregador = threading.Thread(target=entregar, daemon=True)
    entregador.start()
    ultima = 0.0
    try:
        while True:
            dado = origem.recv(65536)
            if not dado:
                break
            hora = time.monotonic() + atraso_s
            contagem[rotulo] = contagem.get(rotulo, 0) + 1
            if random.random() < (perda_pct / 100.0):
                hora += 2 * atraso_s + 0.2       # o reenvio do TCP
                contagem["perdidos"] = contagem.get("perdidos", 0) + 1
            hora = max(hora, ultima)             # em ordem, como o TCP
            ultima = hora
            fila.put((hora, dado))
    except OSError:
        pass
    finally:
        fila.put(None)
        entregador.join(timeout=atraso_s + 5)


def atender(conexao_cliente, host_real, porta_real, atraso_s, perda_pct, contagem):
    try:
        conexao_real = socket.create_connection((host_real, porta_real), timeout=5)
    except OSError as falha:
        print("[proxy] nao consegui conectar no destino de verdade:", falha, flush=True)
        conexao_cliente.close()
        return
    for lado in (conexao_cliente, conexao_real):
        lado.settimeout(None)
        lado.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    t1 = threading.Thread(target=repassar, args=(conexao_cliente, conexao_real, atraso_s, perda_pct,
                                                  "cliente->host", contagem), daemon=True)
    t2 = threading.Thread(target=repassar, args=(conexao_real, conexao_cliente, atraso_s, perda_pct,
                                                  "host->cliente", contagem), daemon=True)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    conexao_cliente.close()
    conexao_real.close()


def main():
    if len(sys.argv) != 6:
        print(__doc__)
        return 1
    porta_local = int(sys.argv[1])
    host_real = sys.argv[2]
    porta_real = int(sys.argv[3])
    atraso_ms = float(sys.argv[4])
    perda_pct = float(sys.argv[5])

    contagem = {}
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind(("127.0.0.1", porta_local))
    servidor.listen(4)
    print("[proxy] escutando em 127.0.0.1:%d -> %s:%d, atraso=%.0fms, perda=%.1f%%"
          % (porta_local, host_real, porta_real, atraso_ms, perda_pct), flush=True)

    def relatar():
        # A cada 2 s, quantos pedacos passaram em cada sentido e quantos
        # "se perderam" -- quem roda o simulador le isso do registro.
        while True:
            time.sleep(2)
            print("[proxy] pedacos: %s" % dict(contagem), flush=True)
    threading.Thread(target=relatar, daemon=True).start()

    try:
        while True:
            cliente, _endereco = servidor.accept()
            print("[proxy] nova conexao aceita", flush=True)
            threading.Thread(target=atender, args=(cliente, host_real, porta_real, atraso_ms / 1000.0,
                                                   perda_pct, contagem), daemon=True).start()
    except KeyboardInterrupt:
        pass
    finally:
        servidor.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
