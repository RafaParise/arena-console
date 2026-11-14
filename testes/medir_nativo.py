# -*- coding: utf-8 -*-
r"""Quanto custa cada pedido com o servidor nativo na frente (docs\MIGRACAO-RUST.md): o mesmo pedido direto no Python
(a porta interna) e pelo nativo, N vezes, numa COPIA do ARENA. Mostra a mediana de cada rota, para decidir quais rotas
valem passar para o Rust primeiro.

Uso:  servidor\python\python.exe testes\medir_nativo.py [vezes]
"""
import http.client
import os
import re
import statistics
import subprocess
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
import copia_do_arena as copia  # noqa: E402
import limpeza  # noqa: E402
import teste_nativo  # noqa: E402

ROTAS = ["/app.js", "/index.html", "/api/estado", "/api/catalogo", "/api/ranking", "/api/bios"]


def tempo_de(porta, rota, vezes):
    medidas = []
    conexao = http.client.HTTPConnection("127.0.0.1", porta, timeout=30)
    for _ in range(vezes):
        inicio = time.perf_counter()
        try:
            conexao.request("GET", rota, headers={"Host": "127.0.0.1:%d" % porta})
            resposta = conexao.getresponse()
            resposta.read()
            fechou = resposta.getheader("Connection", "").lower() == "close"
        except (OSError, http.client.HTTPException):
            conexao.close()
            conexao = http.client.HTTPConnection("127.0.0.1", porta, timeout=30)
            continue
        medidas.append((time.perf_counter() - inicio) * 1000)
        if fechou:
            conexao.close()
            conexao = http.client.HTTPConnection("127.0.0.1", porta, timeout=30)
    conexao.close()
    return statistics.median(medidas) if medidas else float("nan")


def principal():
    vezes = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    trabalho, pasta = copia.nova_pasta()
    porta = copia._porta_da_copia(8795)
    try:
        livres = os.path.join(RAIZ, "testes", "jogos_livres")
        jogos = {c: [os.path.join(livres, c, n) for n in os.listdir(os.path.join(livres, c))
                     if not n.endswith((".txt", ".md"))]
                 for c in ("nes", "snes", "gba") if os.path.isdir(os.path.join(livres, c))}
        copia.montar(pasta, [], jogos)
        registro = os.path.join(trabalho, "servidor.txt")
        processo, saida, _ = teste_nativo.abrir(pasta, porta, teste_nativo.NATIVO_PADRAO, registro)
        teste_nativo.esperar_porta(porta)
        time.sleep(3)   # o Python pronto e as threads da abertura terminadas
        with open(registro, encoding="utf-8", errors="replace") as arquivo:
            interna = int(re.search(r"na porta (\d+)", arquivo.read()).group(1))
        print("Mediana de %d pedidos (ms):         direto no Python   pelo nativo" % vezes)
        for rota in ROTAS:
            direto = tempo_de(interna, rota, vezes)
            nativo = tempo_de(porta, rota, vezes)
            print("  %-16s %18.2f %13.2f" % (rota, direto, nativo))
        teste_nativo.fechar(processo, saida, pasta)
    finally:
        copia.derrubar(pasta)
        limpeza.apagar_pasta(trabalho)
    return 0


if __name__ == "__main__":
    sys.exit(principal())
