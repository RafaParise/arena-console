# -*- coding: utf-8 -*-
"""Fase 4: simulador de rede ruim entre o hospedeiro e um convidado do
Jogar Junto. Python puro (so biblioteca padrao), sem instalar nada.

Fica no meio: o convidado conecta NELE (em vez de conectar direto no
hospedeiro), e ele repassa os bytes pros dois lados, atrasando cada
pedaco em ATRASO_MS milissegundos e, com chance PERDA_PCT, segurando um
pedaco por bem mais tempo antes de repassar -- e assim que perda de
pacote se sente de verdade num protocolo por TCP (o RetroArch usa TCP
pro netplay): nao "some" o dado, ele CHEGA MUITO ATRASADO, como
aconteceria de verdade com uma retransmissao.

Uso:
    python proxy_rede_ruim.py <porta_local> <host_de_verdade> <porta_de_verdade> <atraso_ms> <perda_pct>

Exemplo (proxy na porta 55440, host de verdade em 127.0.0.1:55435,
100ms de atraso, 5% de perda):
    python proxy_rede_ruim.py 55440 127.0.0.1 55435 100 5
"""
import random
import socket
import sys
import threading
import time


def repassar(origem, destino, atraso_s, perda_pct, rotulo, log):
    try:
        while True:
            dado = origem.recv(65536)
            if not dado:
                break
            if random.random() < (perda_pct / 100.0):
                # "perda" num fluxo TCP = atraso bem maior (retransmissao),
                # nao sumico do dado -- TCP nao deixa dado sumir de verdade.
                time.sleep(atraso_s + 0.6 + random.random() * 0.6)
                log.append((time.time(), rotulo, "atraso_extra_por_perda", len(dado)))
            else:
                time.sleep(atraso_s)
            destino.sendall(dado)
    except OSError:
        pass
    finally:
        try:
            destino.shutdown(socket.SHUT_WR)
        except OSError:
            pass


def atender(conexao_cliente, host_real, porta_real, atraso_s, perda_pct, log):
    try:
        conexao_real = socket.create_connection((host_real, porta_real), timeout=5)
    except OSError as falha:
        print("[proxy] nao consegui conectar no destino de verdade:", falha)
        conexao_cliente.close()
        return

    t1 = threading.Thread(target=repassar, args=(conexao_cliente, conexao_real, atraso_s, perda_pct, "cliente->host", log), daemon=True)
    t2 = threading.Thread(target=repassar, args=(conexao_real, conexao_cliente, atraso_s, perda_pct, "host->cliente", log), daemon=True)
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

    log = []
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind(("127.0.0.1", porta_local))
    servidor.listen(4)
    print("[proxy] escutando em 127.0.0.1:%d -> %s:%d, atraso=%.0fms, perda=%.1f%%"
         % (porta_local, host_real, porta_real, atraso_ms, perda_pct))

    try:
        while True:
            cliente, _endereco = servidor.accept()
            print("[proxy] nova conexao aceita")
            threading.Thread(target=atender, args=(cliente, host_real, porta_real, atraso_ms / 1000.0, perda_pct, log), daemon=True).start()
    except KeyboardInterrupt:
        pass
    finally:
        servidor.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
