# -*- coding: utf-8 -*-
"""O "Mostrar na pasta" dos pacotes de progresso (observacao da Fase 7 da
auditoria 3: um "Abrir a pasta dos pacotes" ajudaria quem nunca usou
computador). A rota /api/pacote/mostrar abre o Explorador com o pacote
marcado, e so pacote da lista: nome de outro arquivo, ou com caminho, volta
404 sem abrir nada. O Explorador nao abre de verdade aqui: o Popen vira um
gravador.

No Linux (item 13, 17/10/2026), o mesmo pedido vai ao gerenciador de
arquivos pelo FileManager1 do freedesktop (servidor\plataforma.py), com o
xdg-open de reserva; sem nenhum deles, a resposta diz onde o pacote esta."""
import json
import os
import shutil
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
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
                                         side_effect=lambda comando, *a, **k: self.chamadas.append(comando)),
                       # Linux: o gdbus, o xdg-open... existem (o de verdade nao roda).
                       mock.patch.object(arena.plataforma_do_sistema.shutil, "which",
                                         side_effect=lambda nome, *a, **k: "/usr/bin/" + nome)]
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
        pacote = os.path.join(self.backup, "meu-progresso_2026-10-16_0700.zip")
        if os.name == "nt":
            self.assertEqual(self.chamadas, [["explorer.exe", "/select,", pacote]])
        else:
            self.assertEqual(len(self.chamadas), 1)
            self.assertEqual(self.chamadas[0][:3], ["sh", "-c", arena.plataforma_do_sistema._MOSTRAR_NO_LINUX])
            self.assertEqual(self.chamadas[0][4:], ["file://" + urllib.parse.quote(os.path.abspath(pacote)),
                                                    os.path.dirname(os.path.abspath(pacote))])
            self.assertIn("org.freedesktop.FileManager1.ShowItems", self.chamadas[0][2])

    @unittest.skipIf(os.name == "nt", "o Windows sempre tem o Explorador")
    def test_linux_sem_gerenciador_de_arquivos_diz_onde_esta(self):
        with mock.patch.object(arena.plataforma_do_sistema.shutil, "which", return_value=None):
            status, resposta = self.pedir("meu-progresso_2026-10-16_0700.zip")
        self.assertEqual(status, 400, resposta)
        self.assertIn(self.backup, resposta["erro"])
        self.assertEqual(self.chamadas, [])

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
