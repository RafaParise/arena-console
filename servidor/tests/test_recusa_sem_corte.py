# -*- coding: utf-8 -*-
"""A recusa de um POST (tipo errado, acesso negado) chega inteira, sem "conexao abortada" (13/11/2026).

O servidor recusava ANTES de ler o corpo; no Windows, fechar a ligacao com dados nao lidos manda um "reset", e o
cliente as vezes recebia WinError 10053 no lugar da resposta (2 vezes nos testes do Android). Agora toda resposta de
erro a um POST esvazia antes o corpo nao lido (arena.Manipulador._descartar_corpo_nao_lido)."""
import json
import os
import socket
import sys
import threading
import unittest

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PASTA_SERVIDOR not in sys.path:
    sys.path.insert(0, PASTA_SERVIDOR)


class RecusaSemCorte(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import arena
        cls.servidor = arena.Servidor(("127.0.0.1", 0), arena.Manipulador)
        cls.porta = cls.servidor.server_address[1]
        threading.Thread(target=cls.servidor.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.servidor.shutdown()
        cls.servidor.server_close()

    def _post_cru(self, tipo, corpo):
        """Manda o POST inteiro e le a resposta inteira por um socket cru (sem as tentativas do urllib)."""
        cabeca = ("POST /api/config HTTP/1.1\r\nHost: 127.0.0.1:%d\r\nContent-Type: %s\r\nContent-Length: %d\r\n"
                  "Connection: close\r\n\r\n" % (self.porta, tipo, len(corpo))).encode("ascii")
        with socket.create_connection(("127.0.0.1", self.porta), timeout=10) as ligacao:
            ligacao.sendall(cabeca + corpo)
            resposta = b""
            while True:
                pedaco = ligacao.recv(65536)
                if not pedaco:
                    break
                resposta += pedaco
        return resposta

    def test_recusa_de_tipo_errado_com_corpo_grande_chega_inteira(self):
        corpo = json.dumps({"x": "a" * 200000}).encode("utf-8")
        for _ in range(40):
            resposta = self._post_cru("text/plain", corpo)        # 415: recusado antes de ler o corpo
            self.assertTrue(resposta.startswith(b"HTTP/1.") and b" 415 " in resposta.split(b"\r\n", 1)[0],
                            resposta[:80])
            self.assertIn(b'"ok": false', resposta.split(b"\r\n\r\n", 1)[1])

    def test_o_que_passa_do_limite_fecha_sem_ler_tudo(self):
        import arena
        manipulador = arena.Manipulador.__new__(arena.Manipulador)
        manipulador.command = "POST"
        manipulador._corpo_lido = False
        manipulador.headers = {"Content-Length": str(arena.Manipulador.LIMITE_CORPO + 1)}
        manipulador.close_connection = False
        manipulador._descartar_corpo_nao_lido()
        self.assertTrue(manipulador.close_connection)


if __name__ == "__main__":
    unittest.main()
