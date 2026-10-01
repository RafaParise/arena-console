# -*- coding: utf-8 -*-
r"""Miniaturas das capas: a lista abre leve, e a rota nova nao vira brecha.

Achado de 01/10/2026 (testes\tela_sem_janela.py): abrir a tela baixava
67 pedidos e 21 MB -- 49 capas em tamanho cheio (~1000 px) para cartoes de
~220 px; no Celeron isso e' memoria e processador indo embora. Agora a capa
so carrega perto da tela, e o navegador faz uma miniatura (280 px, ou 480 em
4K) que o servidor guarda em dados\miniaturas e entrega dali em diante.
Medido: 2a abertura com 14 pedidos e 584 KB.

Confere, num ARENA isolado (copia temporaria):
  - sem miniatura, mini=280 devolve a capa cheia; com miniatura, ela;
  - capa trocada (tamanho/data) nao reaproveita miniatura velha;
  - abusos: capa fora da pasta, largura inventada, texto no lugar de
    imagem, imagem grande demais, sem capa -- todos recusados, sem 500;
  - o teto de arquivos apaga as miniaturas mais antigas.

Uso: servidor\python\python.exe testes\teste_capas_miniaturas.py
"""
import base64
import importlib.util
import json
import os
import shutil
import struct
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORTA = 8793


def png(largura, altura, cor=(200, 30, 30)):
    linha = b"\x00" + bytes(cor) * largura
    dados = zlib.compress(linha * altura)

    def bloco(tipo, conteudo):
        return struct.pack(">I", len(conteudo)) + tipo + conteudo + struct.pack(">I", zlib.crc32(tipo + conteudo))
    return (b"\x89PNG\r\n\x1a\n" + bloco(b"IHDR", struct.pack(">IIBBBBB", largura, altura, 8, 2, 0, 0, 0))
            + bloco(b"IDAT", dados) + bloco(b"IEND", b""))


def pedir(caminho, corpo=None):
    dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
    req = urllib.request.Request("http://127.0.0.1:%d%s" % (PORTA, caminho), data=dados,
                                 method="POST" if dados is not None else "GET",
                                 headers={"Content-Type": "application/json", "Host": "127.0.0.1:%d" % PORTA})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def main():
    falhas, total = [], [0]

    def confere(nome, ok, detalhe=""):
        total[0] += 1
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, detalhe if not ok else ""))
        if not ok:
            falhas.append(nome)

    destino = tempfile.mkdtemp(prefix="arena_miniaturas_")
    servidor = None
    try:
        for pasta in ("servidor", "launcher"):
            shutil.copytree(os.path.join(RAIZ, pasta), os.path.join(destino, pasta),
                            ignore=shutil.ignore_patterns("__pycache__", "tests", "python"))
        os.makedirs(os.path.join(destino, "dados"))
        pasta_jogo = os.path.join(destino, "jogos", "pessoais", "Super Nintendo")
        os.makedirs(pasta_jogo)
        capa = os.path.join(pasta_jogo, "Teste.png")
        cheia = png(900, 1200)
        open(capa, "wb").write(cheia)
        spec = importlib.util.spec_from_file_location("arena_mini_teste",
                                                      os.path.join(destino, "servidor", "arena.py"))
        arena = importlib.util.module_from_spec(spec)
        sys.path.insert(0, os.path.join(destino, "servidor"))
        spec.loader.exec_module(arena)
        servidor = arena.Servidor(("127.0.0.1", PORTA), arena.Manipulador)
        threading.Thread(target=servidor.serve_forever, daemon=True).start()
        time.sleep(0.4)

        rel = "jogos/pessoais/Super Nintendo/Teste.png"
        url = "/api/capa?arquivo=%s&mini=280" % urllib.parse.quote(rel)
        status, corpo = pedir(url)
        confere("sem miniatura: mini=280 devolve a capa cheia", status == 200 and corpo == cheia)

        pequena = png(280, 373)
        status, corpo = pedir("/api/capa/miniatura", {"arquivo": rel, "largura": 280,
                                                      "imagem": "data:image/png;base64," + base64.b64encode(pequena).decode()})
        confere("o servidor guarda a miniatura", status == 200, corpo[:120])
        status, corpo = pedir(url)
        confere("com miniatura: mini=280 devolve ELA", status == 200 and corpo == pequena)
        status, corpo = pedir("/api/capa?arquivo=%s" % urllib.parse.quote(rel))
        confere("sem mini=, continua a capa cheia (painel, quem pedir)", corpo == cheia)
        status, corpo = pedir("/api/capa?arquivo=%s&mini=480" % urllib.parse.quote(rel))
        confere("mini=480 ainda sem miniatura propria: capa cheia", corpo == cheia)

        time.sleep(1.1)
        open(capa, "wb").write(png(901, 1200))           # capa trocada
        status, corpo = pedir(url)
        confere("capa trocada nao reaproveita miniatura velha", corpo != pequena and status == 200)

        abusos = [
            ({"arquivo": "../dados/config.json", "largura": 280, "imagem": base64.b64encode(pequena).decode()}, "fora da pasta"),
            ({"arquivo": "jogos/pessoais/Super Nintendo/naoexiste.png", "largura": 280, "imagem": "x"}, "capa que nao existe"),
            ({"arquivo": rel, "largura": 999, "imagem": base64.b64encode(pequena).decode()}, "largura inventada"),
            ({"arquivo": rel, "largura": "280", "imagem": base64.b64encode(pequena).decode()}, "largura como texto"),
            ({"arquivo": rel, "largura": 280, "imagem": base64.b64encode(b"<html>oi</html>").decode()}, "texto no lugar de imagem"),
            ({"arquivo": rel, "largura": 280, "imagem": base64.b64encode(png(1600, 1600, (1, 2, 3)) + os.urandom(260000)).decode()}, "imagem grande demais"),
            ({"arquivo": rel, "largura": 280, "imagem": "@@@nao-e-base64@@@"}, "base64 quebrado"),
            ({"arquivo": [1, 2], "largura": [280], "imagem": {"a": 1}}, "tipos trocados"),
            ({}, "pedido vazio"),
        ]
        for corpo_abuso, nome in abusos:
            status, _resposta = pedir("/api/capa/miniatura", corpo_abuso)
            confere("recusa: %s (sem erro 500)" % nome, status in (400, 404), str(status))
        status, _ = pedir("/api/capa?arquivo=..%2F..%2Fdados%2Fconfig.json&mini=280")
        confere("capa fora da pasta continua 404 com mini=", status == 404)

        # Teto de arquivos.
        pasta_mini = arena.PASTA_MINIATURAS_CAPA
        os.makedirs(pasta_mini, exist_ok=True)
        arena.MAXIMO_MINIATURAS = 20
        for i in range(30):
            caminho = os.path.join(pasta_mini, "velha%02d.webp" % i)
            open(caminho, "wb").write(b"x")
            os.utime(caminho, (1000000 + i, 1000000 + i))
        apagadas = arena.limpar_miniaturas_antigas()
        restantes = sorted(os.listdir(pasta_mini))
        confere("passou do teto: apaga as mais antigas (fica 90%)",
                apagadas > 0 and len(restantes) <= 20 and "velha00.webp" not in restantes,
                "%d apagadas, %d restantes" % (apagadas, len(restantes)))
    finally:
        if servidor:
            servidor.shutdown()
            servidor.server_close()
        sys.path = [p for p in sys.path if not p.startswith(destino)]
        shutil.rmtree(destino, ignore_errors=True)

    print()
    if falhas:
        print("FALHOU: %d de %d" % (len(falhas), total[0]))
        return 1
    print("Miniaturas das capas: %d de %d certos." % (total[0], total[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
