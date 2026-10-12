# -*- coding: utf-8 -*-
r"""Internet ruim: as funcoes online falham com frase clara, rapido, sem
deixar arquivo pela metade.

Auditoria 3, Fase 3. O roteiro pede: "DNS que falha, rede lenta, tempo
esgotado e a pagina de login do Wi-Fi da escola devolvendo HTML no lugar dos
dados esperados. As funcoes online (acervo, busca no Internet Archive [...])
precisam falhar com uma mensagem clara, nunca travando nem corrompendo nada."

Achados que este teste prende:
  - a busca do Internet Archive devolvia "nenhum resultado" quando a rede
    tinha falhado (ou chegava a pagina de login), e pedia as fichas dos jogos
    uma de cada vez (ate 30 pedidos de ate 20 s: minutos numa rede lenta);
  - a busca de capa dizia "Nao achei capa" quando o servidor nao tinha
    respondido (rodada de referencia de 07/10: o GameTDB fora do ar).

Um servidor falso, neste computador, faz as vezes da internet:
  /portal/...  a pagina de login do Wi-Fi (200 OK, HTML) para qualquer pedido;
  /lento/...   so responde depois de 30 s;
  /vazio/...   404 para tudo (o "nao existe" de verdade);
  /ia/...      um Internet Archive de mentira: a busca devolve 12 jogos e
               cada ficha demora 1 s (para ver as fichas ao mesmo tempo).
E mais: uma porta fechada (conexao recusada) e um nome que nao existe
(.invalid). Os modulos sao importados (sem subir o ARENA) e so os enderecos
deles sao trocados; tudo grava numa pasta temporaria.

Uso: servidor\python\python.exe testes\teste_internet_ruim.py
"""
import hashlib
import http.server
import json
import os
import socket
import sys
import tempfile
import threading
import time
import urllib.parse
from unittest import mock

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
import limpeza  # noqa: E402
import acervo  # noqa: E402
import capas_online  # noqa: E402
import internet_archive  # noqa: E402

PAGINA_DE_LOGIN = (b"<!DOCTYPE html><html><head><title>Wi-Fi da Escola - entrar</title></head>"
                   b"<body><form>Usuario: <input> Senha: <input type=password></form></body></html>")
JOGOS_FALSOS = 12
CONTEUDO_DO_JOGO = b"PK\x03\x04 jogo de mentira do teste de internet ruim"


class Falso(http.server.BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def responder(self, codigo, corpo, tipo):
        try:
            self.send_response(codigo)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)
        except OSError:
            pass        # quem pediu ja desistiu (o caso "lento"): e' o esperado

    def do_GET(self):
        caminho = urllib.parse.urlparse(self.path).path
        if caminho.startswith("/portal"):
            return self.responder(200, PAGINA_DE_LOGIN, "text/html")
        if caminho.startswith("/lento"):
            time.sleep(30)
            return self.responder(200, b"{}", "application/json")
        if caminho.startswith("/ia/advancedsearch.php"):
            docs = [{"identifier": "jogo-falso-%02d" % n, "title": "Pacman Falso %d" % n}
                    for n in range(JOGOS_FALSOS)]
            return self.responder(200, json.dumps({"response": {"docs": docs}}).encode(), "application/json")
        if caminho.startswith("/ia/metadata/"):
            time.sleep(1.0)
            ficha = {"metadata": {"title": "Pacman Falso", "collection": ["softwarelibrary_msdos_shareware"]},
                     "files": [{"name": "jogo.zip", "size": str(len(CONTEUDO_DO_JOGO)),
                                "sha1": hashlib.sha1(CONTEUDO_DO_JOGO).hexdigest()}]}
            return self.responder(200, json.dumps(ficha).encode(), "application/json")
        if caminho.startswith("/ia/download/"):
            # O download "pega" a pagina de login (o Wi-Fi caiu para o portal).
            return self.responder(200, PAGINA_DE_LOGIN, "text/html")
        return self.responder(404, b"nao existe", "text/plain")


def porta_fechada():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]           # fechada ao sair do "with"


def main():
    falhas, total = [], [0]

    def confere(nome, ok, detalhe=""):
        total[0] += 1
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, "" if ok else detalhe), flush=True)
        if not ok:
            falhas.append(nome)

    servidor = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Falso)
    servidor.daemon_threads = True
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    base = "http://127.0.0.1:%d" % servidor.server_address[1]
    fechada = "http://127.0.0.1:%d" % porta_fechada()
    pasta = tempfile.mkdtemp(prefix="arena_internet_ruim_")
    try:
        def busca_ia(endereco, segundos=None):
            inicio = time.monotonic()
            trocas = {"BASE": endereco}
            if segundos:
                trocas["SEGUNDOS_BUSCA"] = segundos
            with mock.patch.multiple(internet_archive, **trocas):
                try:
                    return internet_archive.buscar("pacman"), time.monotonic() - inicio
                except internet_archive.FalhaDeRede as falha:
                    return falha, time.monotonic() - inicio

        print("1. Internet Archive: a busca")
        resultado, segundos = busca_ia(base + "/portal")
        confere("pagina de login do Wi-Fi: a frase diz que a rede pediu login",
                isinstance(resultado, Exception) and "login" in str(resultado), resultado)
        resultado, segundos = busca_ia(fechada)
        confere("conexao recusada: a frase diz que a internet falhou, e rapido (%.1f s)" % segundos,
                isinstance(resultado, Exception) and "internet" in str(resultado) and segundos < 10, resultado)
        resultado, segundos = busca_ia("http://nao-existe.invalid")
        confere("nome que nao existe (DNS): a frase diz que a internet falhou (%.1f s)" % segundos,
                isinstance(resultado, Exception) and "internet" in str(resultado) and segundos < 15, resultado)
        resultado, segundos = busca_ia(base + "/lento", segundos=3)
        confere("servidor que nao responde: desiste no tempo-limite (%.1f s), sem travar" % segundos,
                isinstance(resultado, Exception) and segundos < 8, (resultado, segundos))
        resultado, segundos = busca_ia(base + "/ia")
        confere("%d fichas de 1 s cada chegam ao mesmo tempo (%.1f s; uma de cada vez seriam %d s)"
                % (JOGOS_FALSOS, segundos, JOGOS_FALSOS),
                isinstance(resultado, list) and len(resultado) == JOGOS_FALSOS and segundos < 6,
                (resultado if not isinstance(resultado, list) else len(resultado), segundos))

        print("2. Internet Archive: o download")
        livres = os.path.join(pasta, "livres")
        with mock.patch.multiple(internet_archive, BASE=base + "/ia", PASTA_LIVRES=livres):
            try:
                internet_archive.instalar("jogo-falso-01", "jogo.zip")
                resultado = None
            except ValueError as falha:
                resultado = falha
        confere("a pagina de login no lugar do jogo: recusado, com a frase do login",
                resultado is not None and "login" in str(resultado), resultado)
        sobras = [n for _a, _p, nomes in os.walk(livres) for n in nomes] if os.path.isdir(livres) else []
        confere("e nada fica na pasta de jogos (nem pela metade)", not sobras, sobras)

        print("3. Capas")
        miniaturas = os.path.join(pasta, "miniaturas")

        def busca_capa(endereco):
            inicio = time.monotonic()
            with mock.patch.multiple(capas_online, SERVIDOR_MINIATURAS=endereco, GITHUB_MINIATURAS=endereco,
                                     PASTA_MINIATURAS=miniaturas):
                ok, frase = capas_online.buscar_e_baixar("snes", "Jogo Inventado", "Jogo Inventado (Brazil)")
            return ok, frase or "", time.monotonic() - inicio

        ok, frase, segundos = busca_capa(base + "/portal")
        confere("pagina de login do Wi-Fi: a frase diz que a rede pediu login", not ok and "login" in frase, frase)
        ok, frase, segundos = busca_capa(fechada)
        confere("servidor que nao responde: a frase diz isso, nao 'nao achei' (%.1f s)" % segundos,
                not ok and "não respondeu" in frase and segundos < 20, frase)
        ok, frase, segundos = busca_capa(base + "/vazio")
        confere("o banco respondeu e nao tem: ai sim 'nao achei', com o botao Enviar capa",
                not ok and frase.startswith("Não achei capa") and "Enviar capa" in frase, frase)
        sobras = [n for _a, _p, nomes in os.walk(miniaturas) for n in nomes
                  if n.endswith((".png", ".baixando"))] if os.path.isdir(miniaturas) else []
        confere("e nenhuma capa falsa nem pela metade ficou guardada", not sobras, sobras)

        print("4. Acervo autorizado")
        destino_relativo = os.path.join("jogos", "livres", "MS-DOS", "jogo.zip")
        item = {"id": "jogo-livre", "titulo": "Jogo Livre", "autorizado": True, "licenca": "GPL",
                "url": "https://archive.org/download/jogo-livre/jogo.zip",
                "sha256": hashlib.sha256(CONTEUDO_DO_JOGO).hexdigest(), "destino": destino_relativo}

        class RespostaDoPortal:
            def __init__(self):
                self.partes = [PAGINA_DE_LOGIN, b""]

            def read(self, _tamanho=-1):
                return self.partes.pop(0) if self.partes else b""

            def __enter__(self):
                return self

            def __exit__(self, *_a):
                return False

        with mock.patch.multiple(acervo, RAIZ=pasta, PASTA_LIVRES=os.path.join(pasta, "jogos", "livres"),
                                 _item=lambda _id: dict(item)), \
                mock.patch.object(acervo.urllib.request, "urlopen", return_value=RespostaDoPortal()):
            try:
                acervo.instalar("jogo-livre")
                resultado = None
            except ValueError as falha:
                resultado = falha
        confere("a pagina de login no lugar do jogo: recusado, com a frase do login",
                resultado is not None and "login" in str(resultado), resultado)
        confere("e o jogo nao ficou instalado (nem o temporario)",
                not os.path.exists(os.path.join(pasta, destino_relativo))
                and not os.path.exists(os.path.join(pasta, destino_relativo + ".download")))
    finally:
        servidor.shutdown()
        servidor.server_close()
        limpeza.apagar_pasta(pasta)

    print()
    if falhas:
        print("FALHOU: %d de %d" % (len(falhas), total[0]))
        return 1
    print("Internet ruim: %d de %d certos." % (total[0], total[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
