# -*- coding: utf-8 -*-
"""Jogar Junto: quem abre a partida espera o jogador 2 (pedido do Rafael,
14/10/2026). Testa a espera (guardar, comecar, cancelar, estado), as rotas
e o aviso "cheguei" de quem entra -- sem RetroArch: executar_jogo vira um
gravador e o anfitriao do outro computador, um servidor falso."""
import json
import os
import socket
import sys
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)
import arena  # noqa: E402


def porta_livre():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    porta = s.getsockname()[1]
    s.close()
    return porta


class BaseDaEspera(unittest.TestCase):
    """Troca o executar_jogo por um gravador e devolve o estado no fim."""

    def setUp(self):
        self.chamadas = []
        self.executar_antes = arena.executar_jogo
        arena.executar_jogo = lambda *argumentos: self.chamadas.append(argumentos)
        self.guardado = (dict(arena.PARTIDA_PENDENTE), arena.PARTIDA_ABERTA["partida"],
                         dict(arena.JOGO_EM_ANDAMENTO))
        arena.PARTIDA_PENDENTE.update({"args": None, "convidado": ""})
        arena.PARTIDA_ABERTA["partida"] = {"jogo": "CTR", "jogo_id": "ps1/ctr.cue", "esperando": True}
        arena.JOGO_EM_ANDAMENTO.update({"ativo": True, "titulo": "CTR"})

    def tearDown(self):
        arena.executar_jogo = self.executar_antes
        pendente, aberta, andamento = self.guardado
        arena.PARTIDA_PENDENTE.clear()
        arena.PARTIDA_PENDENTE.update(pendente)
        arena.PARTIDA_ABERTA["partida"] = aberta
        arena.JOGO_EM_ANDAMENTO.clear()
        arena.JOGO_EM_ANDAMENTO.update(andamento)

    def esperar_chamada(self):
        for _ in range(150):
            if self.chamadas:
                return
            time.sleep(0.02)


class TestEsperaDoJogador2(BaseDaEspera):
    def test_amigo_chega_e_o_jogo_abre_uma_vez(self):
        arena.esperar_o_amigo(("jogo", "Rafa"))
        estado = arena.estado_da_partida()
        self.assertEqual((estado["esperando"], estado["aberto"]), (True, False))
        self.assertTrue(arena.comecar_partida_pendente("Ana"))
        self.esperar_chamada()
        self.assertEqual(self.chamadas, [("jogo", "Rafa")])
        estado = arena.estado_da_partida()
        self.assertEqual((estado["esperando"], estado["aberto"], estado["convidado"]), (False, True, "Ana"))
        self.assertFalse(arena.PARTIDA_ABERTA["partida"]["esperando"])
        self.assertFalse(arena.comecar_partida_pendente("Bia"))   # ja abriu: uma vez so

    def test_cancelar_solta_o_arena(self):
        arena.esperar_o_amigo(("jogo",))
        self.assertTrue(arena.cancelar_partida_pendente())
        self.assertFalse(arena.JOGO_EM_ANDAMENTO["ativo"])
        self.assertIsNone(arena.PARTIDA_ABERTA["partida"])
        self.assertFalse(arena.comecar_partida_pendente("Ana"))
        self.assertFalse(arena.cancelar_partida_pendente())
        self.assertEqual(self.chamadas, [])

    def test_relogio_de_uma_espera_antiga_nao_derruba_a_nova(self):
        arena.esperar_o_amigo(("primeira",))
        vez_antiga = arena.PARTIDA_PENDENTE["vez"]
        arena.cancelar_partida_pendente()
        arena.PARTIDA_ABERTA["partida"] = {"jogo": "CTR"}
        arena.JOGO_EM_ANDAMENTO["ativo"] = True
        arena.esperar_o_amigo(("segunda",))
        self.assertFalse(arena.cancelar_partida_pendente(vez_antiga))
        self.assertTrue(arena.estado_da_partida()["esperando"])


class TestRotasDaEspera(BaseDaEspera):
    @classmethod
    def setUpClass(cls):
        cls.servidor = arena.Servidor(("127.0.0.1", 0), arena.Manipulador)
        cls.porta = cls.servidor.server_address[1]
        threading.Thread(target=cls.servidor.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.servidor.shutdown()
        cls.servidor.server_close()

    def pedir(self, caminho, corpo=None):
        dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
        pedido = urllib.request.Request("http://127.0.0.1:%d%s" % (self.porta, caminho), data=dados,
                                        headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(pedido, timeout=10) as resposta:
                return resposta.status, json.loads(resposta.read() or b"{}")
        except urllib.error.HTTPError as erro:
            return erro.code, json.loads(erro.read() or b"{}")

    def test_so_o_cheguei_aceita_pedido_de_fora(self):
        self.assertIn("/api/partida/cheguei", arena.ROTAS_REDE_EXTERNA)
        for local in ("/api/partida/comecar", "/api/partida/cancelar", "/api/partida/estado"):
            self.assertNotIn(local, arena.ROTAS_REDE_EXTERNA)

    def test_cheguei_abre_o_jogo_que_esperava(self):
        arena.PARTIDA_ABERTA["partida"] = None
        status, _ = self.pedir("/api/partida/cheguei", {"apelido": "Ana"})
        self.assertEqual(status, 404)                    # nada aberto aqui
        arena.PARTIDA_ABERTA["partida"] = {"jogo": "CTR", "esperando": True}
        arena.esperar_o_amigo(("jogo",))
        status, dados = self.pedir("/api/partida/cheguei", {"apelido": "Ana"})
        self.assertEqual((status, dados.get("abrindo")), (200, True))
        self.esperar_chamada()
        self.assertEqual(len(self.chamadas), 1)
        _, dados = self.pedir("/api/partida/cheguei", {"apelido": "Bia"})
        self.assertIs(dados.get("abrindo"), False)       # ja aberto: o 3o so conecta
        _, estado = self.pedir("/api/partida/estado")
        self.assertEqual((estado["aberto"], estado["convidado"]), (True, "Ana"))

    def test_pre_teste_reconhece_quem_esta_esperando(self):
        # A porta da partida (RetroArch) fica fechada durante a espera; o
        # pre-teste pergunta ao ARENA dele e diz para clicar em Comecar. Aqui o
        # mesmo servidor faz o papel dos dois computadores.
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", arena.graficos.PORTA_PARTIDA)) == 0:
                self.skipTest("a porta da partida esta ocupada nesta maquina")
        arena.PARTIDA_ABERTA["partida"] = {"jogo": "CTR", "jogo_id": "ps1/ctr.cue", "esperando": True}
        _, dados = self.pedir("/api/partida/testar", {"endereco": "127.0.0.1:%d" % self.porta})
        self.assertTrue(dados.get("arena"))
        self.assertTrue(dados.get("esperando"))
        self.assertIn("esperando você", dados.get("diagnostico", ""))

    def test_comecar_sem_esperar_e_cancelar(self):
        arena.esperar_o_amigo(("jogo",))
        _, dados = self.pedir("/api/partida/comecar", {})
        self.assertIs(dados.get("abrindo"), True)
        self.esperar_chamada()
        _, dados = self.pedir("/api/partida/cancelar", {})
        self.assertIs(dados.get("cancelada"), False)    # o jogo ja abriu


class TestPartidaRecebida(unittest.TestCase):
    def test_esperando_so_passa_como_verdadeiro_ou_falso(self):
        # Vem da rede: qualquer um pode mandar qualquer coisa.
        self.assertIs(arena.limpar_partida_recebida({"jogo": "CTR", "esperando": True})["esperando"], True)
        self.assertIs(arena.limpar_partida_recebida({"jogo": "CTR", "esperando": "sim"})["esperando"], False)
        self.assertIs(arena.limpar_partida_recebida({"jogo": "CTR"})["esperando"], False)
        self.assertIsNone(arena.limpar_partida_recebida({"esperando": True}))   # sem jogo, nada


class TestQuemEntraAvisa(unittest.TestCase):
    def anfitriao_falso(self, resposta, bruto=None):
        class Atende(BaseHTTPRequestHandler):
            recebido = None

            def do_POST(self):
                tamanho = int(self.headers.get("Content-Length") or 0)
                Atende.recebido = json.loads(self.rfile.read(tamanho) or b"{}")
                corpo = bruto if bruto is not None else json.dumps(resposta).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(corpo)))
                self.end_headers()
                self.wfile.write(corpo)

            def log_message(self, *_):
                pass

        servidor = HTTPServer(("127.0.0.1", 0), Atende)
        threading.Thread(target=servidor.serve_forever, daemon=True).start()
        self.addCleanup(servidor.server_close)
        self.addCleanup(servidor.shutdown)
        return "http://127.0.0.1:%d" % servidor.server_address[1], Atende

    def test_espera_a_porta_da_partida_do_anfitriao_abrir(self):
        url, atende = self.anfitriao_falso({"ok": True, "abrindo": True})
        porta = porta_livre()
        escuta = socket.socket()
        self.addCleanup(escuta.close)

        def abrir_depois():
            time.sleep(0.8)          # o RetroArch do anfitriao demorando a abrir
            escuta.bind(("127.0.0.1", porta))
            escuta.listen(1)

        threading.Thread(target=abrir_depois, daemon=True).start()
        inicio = time.monotonic()
        self.assertTrue(arena.chegar_na_partida(url, "Ana", porta=porta, limite=8))
        self.assertGreaterEqual(time.monotonic() - inicio, 0.8)
        self.assertEqual(atende.recebido, {"apelido": "Ana"})

    def test_anfitriao_que_nao_esperava_segue_na_hora(self):
        url, _ = self.anfitriao_falso({"ok": True, "abrindo": False})
        inicio = time.monotonic()
        self.assertFalse(arena.chegar_na_partida(url, "Ana", porta=porta_livre(), limite=8))
        self.assertLess(time.monotonic() - inicio, 2)

    def test_resposta_torta_do_outro_computador_nao_trava_quem_entra(self):
        # Revisao de seguranca (14/10/2026): uma lista ou um texto qualquer no
        # lugar do JSON derrubava o aviso antes de soltar a trava do jogo.
        for resposta, bruto in (([1, 2, 3], None), (None, b"isso nao e json"),
                                ({"abrindo": "sim"}, None)):
            url, _ = self.anfitriao_falso(resposta, bruto)
            self.assertFalse(arena.chegar_na_partida(url, "Ana", porta=porta_livre(), limite=8))

    def test_anfitriao_fora_do_ar_segue_na_hora(self):
        inicio = time.monotonic()
        self.assertFalse(arena.chegar_na_partida("http://127.0.0.1:%d" % porta_livre(), "Ana", limite=8))
        self.assertLess(time.monotonic() - inicio, 4)


if __name__ == "__main__":
    unittest.main()
