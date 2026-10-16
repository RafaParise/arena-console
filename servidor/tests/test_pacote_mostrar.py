# -*- coding: utf-8 -*-
"""O "Mostrar na pasta" dos pacotes de progresso (observacao da Fase 7 da
auditoria 3: um "Abrir a pasta dos pacotes" ajudaria quem nunca usou
computador). A rota /api/pacote/mostrar abre o Explorador com o pacote
marcado, e so pacote da lista: nome de outro arquivo, ou com caminho, volta
404 sem abrir nada. O Explorador nao abre de verdade aqui: o Popen vira um
gravador."""
import json
import os
import shutil
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from unittest import mock

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)
import arena  # noqa: E402


class TestMostrarPacote(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.servidor = arena.Servidor(("127.0.0.1", 0), arena.Manipulador)
        cls.porta = cls.servidor.server_address[1]
        threading.Thread(target=cls.servidor.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.servidor.shutdown()
        cls.servidor.server_close()

    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_pacotes_")
        self.backup = os.path.join(self.pasta, "backup")
        os.makedirs(self.backup)
        for nome in ("meu-progresso_2026-10-16_0700.zip", "copia de seguranca.txt"):
            with open(os.path.join(self.backup, nome), "wb") as arquivo:
                arquivo.write(b"PK\x05\x06" + b"\0" * 18)
        with open(os.path.join(self.pasta, "fora.zip"), "wb") as arquivo:
            arquivo.write(b"PK\x05\x06" + b"\0" * 18)
        self.chamadas = []
        self.trocas = [mock.patch.object(arena, "PASTA_BACKUP", self.backup),
                       mock.patch.object(arena.subprocess, "Popen",
                                         side_effect=lambda comando, *a, **k: self.chamadas.append(comando))]
        for troca in self.trocas:
            troca.start()

    def tearDown(self):
        for troca in self.trocas:
            troca.stop()
        shutil.rmtree(self.pasta, ignore_errors=True)

    def pedir(self, arquivo):
        pedido = urllib.request.Request("http://127.0.0.1:%d/api/pacote/mostrar" % self.porta,
                                        data=json.dumps({"arquivo": arquivo}).encode("utf-8"), method="POST",
                                        headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(pedido, timeout=10) as resposta:
                return resposta.status, json.loads(resposta.read())
        except urllib.error.HTTPError as erro:
            return erro.code, json.loads(erro.read() or b"{}")

    def test_abre_o_explorador_com_o_pacote_marcado(self):
        status, resposta = self.pedir("meu-progresso_2026-10-16_0700.zip")
        self.assertEqual(status, 200, resposta)
        self.assertEqual(self.chamadas, [["explorer.exe", "/select,",
                                          os.path.join(self.backup, "meu-progresso_2026-10-16_0700.zip")]])

    def test_so_pacote_da_lista_nunca_caminho(self):
        for arquivo in ("copia de seguranca.txt", "..\\fora.zip", "../fora.zip", "nao-existe.zip", "", None,
                        os.path.join(self.pasta, "fora.zip")):
            status, resposta = self.pedir(arquivo)
            self.assertEqual(status, 404, (arquivo, resposta))
        self.assertEqual(self.chamadas, [])

    def test_nao_aceita_pedido_de_outro_computador(self):
        self.assertNotIn("/api/pacote/mostrar", arena.ROTAS_REDE_EXTERNA)


if __name__ == "__main__":
    unittest.main()
