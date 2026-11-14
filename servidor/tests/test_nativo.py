# -*- coding: utf-8 -*-
"""O servidor em Python atras do nativo (Rust, nativo\\, docs\\MIGRACAO-RUST.md, 14/11/2026).

O nativo repassa os pedidos de 127.0.0.1 e conta quem pediu de verdade no X-Arena-Origem. O Python so acredita nisso
com o segredo da abertura (X-Arena-Proxy): sem ele, um programa qualquer do aparelho poderia se passar por "outro
computador" e pular o segredo da tela do Android, ou se passar por local estando na rede."""
import http.client
import os
import sys
import threading
import unittest
from unittest import mock

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PASTA_SERVIDOR not in sys.path:
    sys.path.insert(0, PASTA_SERVIDOR)
import arena  # noqa: E402

SEGREDO = "0123456789abcdef0123456789abcdef"


class AtrasDoNativo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.troca = mock.patch.object(arena, "SEGREDO_DO_NATIVO", SEGREDO)
        cls.troca.start()
        cls.servidor = arena.Servidor(("127.0.0.1", 0), arena.Manipulador)
        cls.porta = cls.servidor.server_address[1]
        threading.Thread(target=cls.servidor.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.servidor.shutdown()
        cls.servidor.server_close()
        cls.troca.stop()

    def pedir(self, rota, cabecalhos):
        conexao = http.client.HTTPConnection("127.0.0.1", self.porta, timeout=30)
        conexao.request("GET", rota, headers=dict({"Host": "127.0.0.1:8777"}, **cabecalhos))
        resposta = conexao.getresponse()
        resposta.read()
        conexao.close()
        return resposta.status

    def test_com_o_segredo_vale_a_origem_de_verdade(self):
        # Um colega da rede (10.1.2.3) pedindo uma rota so deste computador: barrado, como sem o nativo.
        self.assertEqual(self.pedir("/api/estado", {"X-Arena-Origem": "10.1.2.3", "X-Arena-Proxy": SEGREDO}), 403)
        # A rota aberta a rede continua aberta para ele.
        self.assertEqual(self.pedir("/api/ranking", {"X-Arena-Origem": "10.1.2.3", "X-Arena-Proxy": SEGREDO}), 200)

    def test_sem_o_segredo_a_origem_e_ignorada(self):
        # Segredo errado: o pedido continua sendo de 127.0.0.1 (local, passa pelas regras de sempre).
        self.assertEqual(self.pedir("/api/estado", {"X-Arena-Origem": "10.1.2.3", "X-Arena-Proxy": "chute"}), 200)
        self.assertEqual(self.pedir("/api/estado", {"X-Arena-Origem": "10.1.2.3"}), 200)

    def test_host_estranho_continua_barrado(self):
        conexao = http.client.HTTPConnection("127.0.0.1", self.porta, timeout=30)
        conexao.request("GET", "/api/estado", headers={"Host": "site-malvado.com",
                                                        "X-Arena-Origem": "127.0.0.1", "X-Arena-Proxy": SEGREDO})
        self.assertEqual(conexao.getresponse().status, 403)
        conexao.close()


class SemONativo(unittest.TestCase):
    def test_escuta_e_aviso_como_antes(self):
        with mock.patch.object(arena, "SEGREDO_DO_NATIVO", ""):
            self.assertEqual(arena.endereco_de_escuta("0.0.0.0"), ("0.0.0.0", arena.PORTA))
            self.assertEqual(arena.avisar_o_nativo("0.0.0.0"), "0.0.0.0")      # nao pergunta a ninguem
        with mock.patch.object(arena, "SEGREDO_DO_NATIVO", SEGREDO), mock.patch.object(arena, "PORTA_INTERNA", 45678):
            self.assertEqual(arena.endereco_de_escuta("0.0.0.0"), ("127.0.0.1", 45678))   # a rede e' do nativo


if __name__ == "__main__":
    unittest.main()
