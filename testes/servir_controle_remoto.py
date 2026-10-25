# -*- coding: utf-8 -*-
"""Liga o controle remoto (servidor\\controle_remoto.py) SOZINHO, sem o resto do ARENA, para testar com o celular de
verdade: mostra o endereco e o codigo, e escreve cada datagrama do Network RetroPad que iria para o RetroArch.

Uso:
    servidor\\python\\python.exe testes\\servir_controle_remoto.py [--base=55400] [--segundos=600] [--codigo=1234]
Sem --base, o UDP vai para as portas 55400 a 55403 (onde um RetroArch aberto com as chaves de
controle_remoto.opcoes_do_retroarch estaria escutando). O programa fecha sozinho depois de --segundos.
"""
import os
import struct
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
import controle_remoto as cr  # noqa: E402

NOMES = {0: "B", 1: "Y", 2: "Select", 3: "Start", 4: "Cima", 5: "Baixo", 6: "Esquerda", 7: "Direita", 8: "A", 9: "X",
         10: "L1", 11: "R1", 12: "L2", 13: "R2", 14: "L3", 15: "R3"}


def argumento(nome, padrao):
    for a in sys.argv[1:]:
        if a.startswith("--%s=" % nome):
            return a.split("=", 1)[1]
    return padrao


def main():
    for saida in (sys.stdout, sys.stderr):
        try:
            saida.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass
    base = int(argumento("base", cr.PORTA_BASE_PADRAO))
    segundos = float(argumento("segundos", "600"))
    envio = cr.EnviadorRetroPad(porta_base=base)
    real = envio._enviar

    def mostrar(dados, porta):
        _porta, dispositivo, indice, identificador, valor = struct.unpack("<iiiiH", dados[:18])
        if dispositivo == cr.DISPOSITIVO_JOYPAD:
            print("%s  jogador %d  botao %-8s %s" % (time.strftime("%H:%M:%S"), porta - base + 1, NOMES.get(identificador, identificador),
                                                      "APERTADO" if valor else "solto"), flush=True)
        else:
            if valor > 32767:
                valor -= 65536
            print("%s  jogador %d  analogico %s %s = %d" % (time.strftime("%H:%M:%S"), porta - base + 1, "esq" if indice == 0 else "dir",
                                                            "x" if identificador == 0 else "y", valor), flush=True)
        real(dados, porta)

    envio._enviar = mostrar
    controle = cr.ControleRemoto(enviador=envio)
    codigo = argumento("codigo", None)
    estado = controle.ligar()
    if codigo:
        controle.codigo = codigo
        estado = controle.estado()
    print("Controle remoto ligado. Endereço(s): %s" % ", ".join(estado["enderecos"]), flush=True)
    print("Código: %s   (porta-base do RetroArch: %d)" % (estado["codigo"], base), flush=True)
    fim = time.monotonic() + segundos
    visto = []
    try:
        while time.monotonic() < fim:
            time.sleep(0.5)
            atual = [(c["jogador"], c["apelido"], c["ip"]) for c in controle.estado()["conectados"]]
            if atual != visto:
                print("Conectados: %s" % atual, flush=True)
                visto = atual
    except KeyboardInterrupt:
        pass
    finally:
        controle.desligar()
        envio.parar()
    print("Controle remoto desligado.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
