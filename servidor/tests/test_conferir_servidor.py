# -*- coding: utf-8 -*-
"""O conferidor de um ARENA aberto (ferramentas\\conferir_servidor.py), contra um servidor FALSO.

O servidor falso (http.server numa thread, porta 0 = uma livre que o sistema escolhe) imita quatro jeitos de
responder: o ARENA com o nativo na frente, so o Python, um ARENA inseguro (aceita o que devia recusar) e o
Android sem o cookie (tudo 403). O teste confere se o relatorio marca OK, FALHA e aviso nos lugares certos."""
import io
import json
import os
import sys
import threading
import unittest
import urllib.parse
from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ = os.path.dirname(PASTA_SERVIDOR)
sys.path.insert(0, os.path.join(RAIZ, "ferramentas"))

import conferir_servidor as cs  # noqa: E402

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 20
CATALOGO = {"plataformas": [{"id": "nes"}, {"id": "snes"}],
            "jogos": [{"id": "a", "plataforma": "nes"},
                      {"id": "b", "plataforma": "snes", "capa_urls": ["/api/capa?arquivo=jogos%2Fb.png"]}]}


class Falso(BaseHTTPRequestHandler):
    """Responde conforme self.server.modo: 'nativo', 'python', 'inseguro' ou 'android'."""
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def responder(self, codigo, corpo=b"", tipo="text/plain", extras=()):
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        for nome, valor in extras:
            self.send_header(nome, valor)
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self):
        modo = self.server.modo
        partes = urllib.parse.urlsplit(self.path)
        host = (self.headers.get("Host") or "").split(":")[0]
        if modo == "android":
            if partes.path == "/_nativo/pronto":
                return self.responder(200, b'{"ok": true}', "application/json")
            return self.responder(403, b'{"ok": false}', "application/json")
        if host == "exemplo.com" and modo != "inseguro":
            return self.responder(403, b'{"ok": false}', "application/json")
        if ".." in partes.path or ".." in urllib.parse.unquote(partes.query):
            if modo == "inseguro":
                return self.responder(200, b"def principal(): pass")
            return self.responder(404)
        guardado = [("X-Arena-Guardado", "1")] if modo == "nativo" else []
        if partes.path == "/":
            return self.responder(200, b"<!doctype html><html></html>", "text/html")
        if partes.path == "/app.js":
            return self.responder(200, b"// tela", "text/javascript")
        if partes.path == "/api/estado":
            return self.responder(200, json.dumps({"versao": "9.9"}).encode(), "application/json", guardado)
        if partes.path == "/api/catalogo":
            return self.responder(200, json.dumps(CATALOGO).encode(), "application/json", guardado)
        if partes.path == "/api/capa":
            if modo == "inseguro":
                return self.responder(200, PNG, "text/plain")      # tipo errado e sem Cache-Control
            return self.responder(200, PNG, "image/png", [("Cache-Control", "max-age=86400")])
        if partes.path == "/_nativo/pronto" and modo == "nativo":
            return self.responder(200, b'{"ok": true}', "application/json")
        return self.responder(404)

    def do_POST(self):
        tamanho = int(self.headers.get("Content-Length") or 0)
        self.rfile.read(tamanho)
        self.server.posts += 1
        if self.server.modo == "android":
            return self.responder(403)
        if self.server.modo == "inseguro":
            return self.responder(200, b'{"ok": true}', "application/json")
        return self.responder(415, b'{"ok": false}', "application/json")


class ConferirServidor(unittest.TestCase):
    def subir(self, modo):
        servidor = ThreadingHTTPServer(("127.0.0.1", 0), Falso)
        servidor.modo = modo
        servidor.posts = 0
        servidor.daemon_threads = True
        threading.Thread(target=servidor.serve_forever, daemon=True).start()
        self.addCleanup(servidor.server_close)
        self.addCleanup(servidor.shutdown)
        return servidor, "http://127.0.0.1:%d" % servidor.server_address[1]

    def estados(self, itens):
        return {titulo: estado for estado, titulo, _ in itens}

    def test_nativo_tudo_ok(self):
        _, endereco = self.subir("nativo")
        itens = cs.conferir(endereco, espera=5)
        self.assertTrue(all(e == cs.OK for e, _, _ in itens), itens)
        texto = cs.relatorio(itens, endereco)
        self.assertIn("2 plataformas, 2 jogos", texto)
        self.assertIn("guardado pelo nativo", texto)
        self.assertIn("servidor nativo (Rust)", texto)
        self.assertIn("RESULTADO: tudo OK", texto)
        self.assertIn(" ms", texto)

    def test_so_python_ok(self):
        _, endereco = self.subir("python")
        itens = cs.conferir(endereco, espera=5)
        self.assertTrue(all(e == cs.OK for e, _, _ in itens), itens)
        texto = cs.relatorio(itens, endereco)
        self.assertIn("só o Python", texto)
        self.assertIn("veio na hora", texto)
        saida = io.StringIO()
        with redirect_stdout(saida):
            self.assertEqual(cs.principal(["--endereco", endereco, "--espera", "5"]), 0)

    def test_inseguro_marca_falha_de_seguranca(self):
        servidor, endereco = self.subir("inseguro")
        itens = cs.conferir(endereco, espera=5)
        estados = self.estados(itens)
        self.assertEqual(estados["Host falso (Host: exemplo.com) no /api/estado"], cs.FALHA_SEGURANCA)
        self.assertEqual(estados["POST /api/config sem Content-Type: application/json"], cs.FALHA_SEGURANCA)
        self.assertEqual(estados["Caminho com .. (GET /../servidor/arena.py)"], cs.FALHA_SEGURANCA)
        self.assertEqual(estados["Capa fora da pasta (GET /api/capa?arquivo=../../servidor/arena.py)"],
                         cs.FALHA_SEGURANCA)
        self.assertTrue(any(e == cs.FALHA and t.startswith("Uma capa") for e, t, _ in itens))
        texto = cs.relatorio(itens, endereco)
        self.assertIn("!!! FALHA DE SEGURANÇA", texto)
        saida = io.StringIO()
        with redirect_stdout(saida):
            self.assertEqual(cs.principal(["--endereco", endereco, "--espera", "5"]), 1)
        self.assertEqual(servidor.posts, 2)       # so o POST que devia ser recusado (uma vez por conferencia)

    def test_android_e_aviso_nao_falha(self):
        _, endereco = self.subir("android")
        itens = cs.conferir(endereco, espera=5)
        self.assertFalse([i for i in itens if i[0] in (cs.FALHA, cs.FALHA_SEGURANCA)], itens)
        texto = cs.relatorio(itens, endereco)
        self.assertIn("Parece o ARENA de um Android", texto)
        self.assertIn("adb forward tcp:8777 tcp:8777", texto)

    def test_ninguem_escutando(self):
        servidor, endereco = self.subir("python")
        servidor.shutdown()
        servidor.server_close()
        itens = cs.conferir(endereco, espera=2)
        self.assertEqual(len(itens), 1)
        self.assertEqual(itens[0][0], cs.FALHA)
        self.assertIn("ARENA.bat", itens[0][2])

    def test_endereco(self):
        self.assertEqual(cs.ler_endereco("http://127.0.0.1:8777"), ("127.0.0.1", 8777))
        self.assertEqual(cs.ler_endereco("localhost:9000"), ("localhost", 9000))
        with self.assertRaises(ValueError):
            cs.ler_endereco("https://127.0.0.1:8777")


if __name__ == "__main__":
    unittest.main()
