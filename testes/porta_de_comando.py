# -*- coding: utf-8 -*-
r"""A porta dos comandos de rede do RetroArch nos testes (network_cmd_port).

A padrao do RetroArch e' a 55355. Achado de 16/10/2026: o Windows reserva
faixas de porta para o Hyper-V e o WSL, e elas mudam a cada reinicio (veja com
"netsh interface ipv4 show excludedportrange protocol=udp"). Naquele dia, de
55335 a 55434: com a 55355 dentro, o RetroArch dizia "[NetCMD] Falha em
vincular o soquete" e nao atendia comando nenhum -- nem o SAVE_STATE, nem o
QUIT --, e o teste_cheats_no_jogo falhou sem defeito nenhum no ARENA.

livre() devolve a primeira porta da lista que da para abrir. As de reserva
ficam abaixo de 49152, fora da faixa que o Windows costuma reservar.
"""
import socket

CANDIDATAS = (55355, 45355, 35355, 25355, 15355)


def livre(candidatas=CANDIDATAS):
    for porta in candidatas:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            try:
                s.bind(("127.0.0.1", porta))
            except OSError:
                continue
        return porta
    return candidatas[0]


if __name__ == "__main__":
    print(livre())
