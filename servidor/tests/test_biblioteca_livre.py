# -*- coding: utf-8 -*-
"""A biblioteca de jogos livres de mais consoles (servidor\\biblioteca_livre.py):
a lista curada conferida campo a campo, e a instalacao contra um servidor de
mentira aqui mesmo (127.0.0.1): o arquivo certo entra, o errado nao, a pagina
de login do Wi-Fi e o site fora do ar viram a frase certa, e o aceite do
mamedev.org e' conferido pelo servidor."""
import hashlib
import json
import os
import re
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(os.path.dirname(RAIZ), "testes"))
import biblioteca_livre as b  # noqa: E402
import limpeza  # noqa: E402

JOGO = b"NES\x1a" + bytes(range(256)) * 64


class TestListaCurada(unittest.TestCase):
    def setUp(self):
        self.jogos = b.lista_curada()["jogos"]
        with open(os.path.join(RAIZ, "consoles.json"), encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
        self.consoles = {p["id"]: p for p in (dados["plataformas"] if isinstance(dados, dict) else dados)}

    def test_cada_jogo_tem_tudo(self):
        self.assertGreaterEqual(len(self.jogos), 30)
        ids = [j["id"] for j in self.jogos]
        self.assertEqual(len(ids), len(set(ids)), "id repetido")
        for jogo in self.jogos:
            with self.subTest(jogo=jogo["id"]):
                self.assertIn(jogo["console"], self.consoles)
                extensao = os.path.splitext(jogo["arquivo"])[1].lower()
                self.assertIn(extensao, [e.lower() for e in self.consoles[jogo["console"]]["extensoes"]])
                self.assertNotRegex(jogo["arquivo"], r"[\\/:]")
                self.assertTrue(jogo["baixar"].startswith("https://"))
                self.assertTrue(jogo["pagina"].startswith("https://"))
                self.assertRegex(jogo["sha256"], r"^[0-9a-f]{64}$")
                self.assertGreater(jogo["tamanho"], 0)
                for campo in ("titulo", "autor", "licenca", "descricao"):
                    self.assertTrue(jogo[campo].strip(), campo)

    def test_os_do_mamedev_pedem_o_aceite_e_nada_de_aposta(self):
        mamedev = [j for j in self.jogos if "mamedev.org" in j["baixar"]]
        self.assertEqual(len(mamedev), 20)
        for jogo in mamedev:
            self.assertIn("não comercial", jogo.get("aceite", ""))
            self.assertRegex(jogo["baixar"], r"^https://www\.mamedev\.org/roms/[a-z0-9]+/[a-z0-9]+\.zip$")
        # Os 8 da Video Klein (poquer e aposta) ficaram de fora: turma de menores.
        self.assertFalse([j for j in self.jogos if re.search(r"witch|falcnwld|wupndown|wldwitch", j["id"])])


class Servidor(BaseHTTPRequestHandler):
    respostas = {}

    def do_GET(self):
        codigo, corpo = self.respostas.get(self.path, (404, b"nada"))
        self.send_response(codigo)
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def log_message(self, *_args):
        pass


class TestInstalar(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.servidor = ThreadingHTTPServer(("127.0.0.1", 0), Servidor)
        cls.endereco = "http://127.0.0.1:%d" % cls.servidor.server_address[1]
        threading.Thread(target=cls.servidor.serve_forever, daemon=True).start()
        Servidor.respostas = {"/jogo.nes": (200, JOGO),
                              "/login.nes": (200, b"<!DOCTYPE html><html>Entre na rede da escola</html>"),
                              "/outro.nes": (200, JOGO[:-1] + b"X")}

    @classmethod
    def tearDownClass(cls):
        cls.servidor.shutdown()
        cls.servidor.server_close()

    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_biblioteca_livre_")
        self.antes = b._cache.get("lista")
        marca = hashlib.sha256(JOGO).hexdigest()

        def jogo(ident, caminho, **extra):
            return dict({"id": ident, "titulo": "Jogo " + ident, "console": "nes", "arquivo": ident + ".nes",
                         "baixar": self.endereco + caminho, "tamanho": len(JOGO), "sha256": marca}, **extra)
        b._cache["lista"] = {"jogos": [jogo("certo", "/jogo.nes"), jogo("login", "/login.nes"),
                                       jogo("errado", "/outro.nes"), jogo("sumiu", "/nao-existe.nes"),
                                       jogo("pede", "/jogo.nes", aceite="Entendo que é só para uso não comercial.")]}

    def tearDown(self):
        if self.antes is None:
            b._cache.pop("lista", None)
        else:
            b._cache["lista"] = self.antes
        limpeza.apagar_pasta(self.pasta)

    def sobras(self):
        return [n for _a, _p, nomes in os.walk(self.pasta) for n in nomes if n.endswith(".baixando")]

    def test_o_arquivo_certo_entra_na_pasta_do_console(self):
        feito = b.instalar("certo", pasta_livres=self.pasta)
        self.assertFalse(feito["ja_tinha"])
        caminho = os.path.join(self.pasta, "NES", "certo.nes")
        with open(caminho, "rb") as arquivo:
            self.assertEqual(arquivo.read(), JOGO)
        self.assertTrue(b.instalar("certo", pasta_livres=self.pasta)["ja_tinha"])
        instalados = {j["id"]: j["instalado"] for j in b.jogos(self.pasta)}
        self.assertEqual(instalados, {"certo": True, "login": False, "errado": False, "sumiu": False,
                                      "pede": False})

    def test_marca_errada_nao_instala_nada(self):
        with self.assertRaisesRegex(ValueError, "marca não bate"):
            b.instalar("errado", pasta_livres=self.pasta)
        self.assertFalse(os.path.exists(os.path.join(self.pasta, "NES", "errado.nes")))
        self.assertEqual(self.sobras(), [])

    def test_login_do_wifi_e_site_fora_do_ar(self):
        with self.assertRaisesRegex(b.FalhaDeRede, "pediu login"):
            b.instalar("login", pasta_livres=self.pasta)
        with self.assertRaisesRegex(b.FalhaDeRede, "internet caiu"):
            b.instalar("sumiu", pasta_livres=self.pasta)
        self.assertEqual(self.sobras(), [])

    def test_aceite_conferido_no_servidor(self):
        with self.assertRaisesRegex(ValueError, "marque a caixinha"):
            b.instalar("pede", pasta_livres=self.pasta)
        self.assertFalse(os.path.exists(os.path.join(self.pasta, "NES", "pede.nes")))
        self.assertFalse(b.instalar("pede", aceite=True, pasta_livres=self.pasta)["ja_tinha"])

    def test_jogo_que_nao_esta_na_lista(self):
        with self.assertRaisesRegex(ValueError, "não está na biblioteca"):
            b.instalar("qualquer-coisa", pasta_livres=self.pasta)


if __name__ == "__main__":
    unittest.main()
