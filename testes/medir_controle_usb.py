# -*- coding: utf-8 -*-
"""Liga o celular como controle PELO CABO USB (servidor\\controle_usb.py) e mede a ida e volta que a pagina informa.

Uso:  servidor\\python\\python.exe testes\\medir_controle_usb.py [segundos]   (padrao 40)
O celular tem que estar no cabo com a Depuracao USB ligada. Abre a pagina do controle nele, espera a conexao e imprime o
tempo de resposta (RTT) que o celular mede a cada 2 s. Nao abre jogo nenhum; desfaz o cabo ao terminar.
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "servidor"))
import controle_remoto as cr  # noqa: E402

segundos = float(sys.argv[1]) if len(sys.argv) > 1 else 40
controle = cr.ControleRemoto()
controle.ligar()
try:
    r = controle.ligar_pelo_cabo(jogador=2)
    print("cabo:", {k: v for k, v in r.items() if k in ("ok", "erro", "dica", "pelo_cabo")}, flush=True)
    medidas = []
    fim = time.monotonic() + segundos
    while time.monotonic() < fim:
        for c in controle.estado().get("conectados", []):
            if c.get("rtt_ms") is not None:
                medidas.append(c["rtt_ms"])
                print("%s  jogador %d  rtt %s ms  pelo_cabo=%s" % (time.strftime("%H:%M:%S"), c["jogador"], c["rtt_ms"], c["pelo_cabo"]), flush=True)
        time.sleep(2)
    print("medidas:", medidas, flush=True)
finally:
    controle.desligar()
