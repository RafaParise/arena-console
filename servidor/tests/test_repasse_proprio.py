# -*- coding: utf-8 -*-
"""O repasse proprio (servidor\\repasse_proprio.py, 10/11/2026): o protocolo do tunel do RetroArch 1.22.2 e o codigo de
6 numeros, com o repasse de verdade aberto neste computador e "anfitriao" e "convidado" de mentira falando byte a byte."""
import asyncio
import base64
import os
import socket
import sys
import threading
import time
import unittest

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PASTA_SERVIDOR not in sys.path:
    sys.path.insert(0, PASTA_SERVIDOR)

import repasse_proprio as rp  # noqa: E402


def receber(sock, tamanho, espera=5.0):
    sock.settimeout(espera)
    dados = b""
    while len(dados) < tamanho:
        pedaco = sock.recv(tamanho - len(dados))
        if not pedaco:
            break
        dados += pedaco
    return dados


class RepasseDeVerdade(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ping_original = rp.INTERVALO_DO_PING
        rp.INTERVALO_DO_PING = 0.3
        cls.loop = asyncio.new_event_loop()
        pronto = threading.Event()

        def ao_abrir(servidor, repasse):
            cls.porta = servidor.sockets[0].getsockname()[1]
            cls.repasse = repasse
            pronto.set()

        def rodar():
            asyncio.set_event_loop(cls.loop)
            cls.tarefa = cls.loop.create_task(rp.servir(0, "127.0.0.1", porta_publica=55440, pronto=ao_abrir))
            try:
                cls.loop.run_until_complete(cls.tarefa)
            except asyncio.CancelledError:
                pass

        cls.fio = threading.Thread(target=rodar, daemon=True)
        cls.fio.start()
        assert pronto.wait(10), "o repasse nao abriu"
        cls.endereco = "127.0.0.1:%d" % cls.porta

    @classmethod
    def tearDownClass(cls):
        cls.loop.call_soon_threadsafe(cls.tarefa.cancel)
        cls.fio.join(10)
        rp.INTERVALO_DO_PING = cls.ping_original

    def setUp(self):
        # Cada teste comeca sem salas e sem contagem de pedidos (todos vem de 127.0.0.1).
        def zerar():
            self.repasse.salas.clear()
            self.repasse.por_sessao.clear()
            self.repasse.reservas.vezes.clear()
            self.repasse.consultas.vezes.clear()
        self.loop.call_soon_threadsafe(zerar)
        time.sleep(0.05)
        self.abertos = []

    def tearDown(self):
        for sock in self.abertos:
            sock.close()

    def ligar(self):
        sock = socket.create_connection(("127.0.0.1", self.porta), timeout=5)
        self.abertos.append(sock)
        return sock

    def abrir_sala(self):
        codigo, erro = rp.reservar_sala(self.endereco)
        self.assertIsNone(erro)
        controle = self.ligar()
        controle.sendall(rp.SESSAO + bytes(12))
        resposta = receber(controle, 16)
        self.assertEqual(resposta[:4], rp.SESSAO)
        self.assertNotEqual(resposta[4:], bytes(12))
        return codigo, controle, resposta[4:]

    def test_partida_inteira_pelo_codigo(self):
        codigo, controle, sessao = self.abrir_sala()
        self.assertRegex(codigo, r"^\d{6}$")
        achado, erro = rp.procurar_sala(self.endereco, codigo, tentativas=1)
        self.assertIsNone(erro)
        self.assertEqual(base64.b64decode(achado[0]), sessao)
        self.assertEqual(achado[1], 55440)                         # a porta que o roteador abre, nao a interna

        convidado = self.ligar()
        convidado.sendall(rp.SESSAO + sessao + b"ola do convidado")
        aviso = receber(controle, 16)
        self.assertEqual(aviso[:4], rp.LIGACAO)
        ligacao = aviso[4:]

        controle.sendall(rp.ENDERECO + ligacao)
        endereco = receber(controle, 32)
        self.assertEqual(endereco[:16], rp.ENDERECO + ligacao)
        self.assertEqual(endereco[16:], bytes(10) + b"\xff\xff" + bytes([127, 0, 0, 1]))

        lado_do_anfitriao = self.ligar()
        lado_do_anfitriao.sendall(rp.LIGACAO + ligacao)
        self.assertEqual(receber(lado_do_anfitriao, 16), b"ola do convidado")
        lado_do_anfitriao.sendall(b"resposta do anfitriao")
        self.assertEqual(receber(convidado, 21), b"resposta do anfitriao")

        grande = os.urandom(300000)                               # um estado de jogo inteiro passa sem estragar
        lado_do_anfitriao.sendall(grande)
        self.assertEqual(receber(convidado, len(grande), 10), grande)

        convidado.close()
        self.assertEqual(receber(lado_do_anfitriao, 1, 5), b"")   # o convidado saiu: o anfitriao fica sabendo

    def test_o_anfitriao_responde_ao_ainda_esta_ai(self):
        _codigo, controle, _sessao = self.abrir_sala()
        self.assertEqual(receber(controle, 4, 3), rp.PING)
        controle.sendall(rp.PING)
        self.assertEqual(receber(controle, 4, 3), rp.PING)

    def test_retroarch_sem_reserva_e_recusado(self):
        estranho = self.ligar()
        estranho.sendall(rp.SESSAO + bytes(12))
        self.assertEqual(receber(estranho, 16), b"")

    def test_sessao_inventada_nao_entra(self):
        self.abrir_sala()
        intruso = self.ligar()
        intruso.sendall(rp.SESSAO + os.urandom(12))
        self.assertEqual(receber(intruso, 1), b"")

    def test_sala_fecha_quando_o_anfitriao_sai(self):
        codigo, controle, _sessao = self.abrir_sala()
        controle.close()
        time.sleep(0.3)
        achado, erro = rp.procurar_sala(self.endereco, codigo, tentativas=1)
        self.assertIsNone(achado)
        self.assertIn("Nao ha sala", erro)

    def test_sala_reservada_ainda_abrindo(self):
        codigo, erro = rp.reservar_sala(self.endereco)
        self.assertIsNone(erro)
        achado, erro = rp.procurar_sala(self.endereco, codigo, tentativas=1)
        self.assertIsNone(achado)
        self.assertIn("abrindo", erro)
        # Outra sala da mesma internet espera esta abrir (senao o repasse nao saberia de quem e' cada RetroArch).
        outro, erro = rp.reservar_sala(self.endereco)
        self.assertIsNone(outro)
        self.assertIn("mesma internet", erro)

    def test_codigos_errados(self):
        for codigo in ("12345", "abcdef", "1234567", ""):
            achado, erro = rp.procurar_sala(self.endereco, codigo, tentativas=1)
            self.assertIsNone(achado)
            self.assertIn("6 numeros", erro)
        achado, erro = rp.procurar_sala(self.endereco, "000000", tentativas=1)
        self.assertIsNone(achado)

    def test_limite_de_consultas(self):
        respostas = [rp._pedir(self.endereco, "GET", "/sala/123456")[0] for _ in range(rp.LIMITE_CONSULTAS[0] + 2)]
        self.assertIn(429, respostas)

    def test_saude_e_pedido_desconhecido(self):
        self.assertTrue(rp.saude(self.endereco))
        self.assertEqual(rp._pedir(self.endereco, "GET", "/lista")[0], 404)   # nao existe lista de salas

    def test_quem_nao_fala_nada_e_desligado(self):
        original = rp.ESPERA_DO_COMECO
        rp.ESPERA_DO_COMECO = 0.3
        try:
            mudo = self.ligar()
            self.assertEqual(receber(mudo, 1, 3), b"")
        finally:
            rp.ESPERA_DO_COMECO = original


class Pedacos(unittest.TestCase):
    def test_endereco_de_16_bytes(self):
        self.assertEqual(rp.endereco_de_16_bytes("10.0.0.5"), bytes(10) + b"\xff\xff" + bytes([10, 0, 0, 5]))
        self.assertEqual(rp.endereco_de_16_bytes("::1"), bytes(15) + b"\x01")
        self.assertEqual(rp.endereco_de_16_bytes("lixo"), bytes(16))

    def test_mesmo_ipv4_pelos_dois_jeitos(self):
        self.assertEqual(rp.chave_do_endereco("::ffff:200.1.2.3"), "200.1.2.3")
        self.assertEqual(rp.chave_do_endereco("200.1.2.3"), "200.1.2.3")

    def test_separar_endereco(self):
        self.assertEqual(rp.separar_endereco("bancada.exemplo.net"), ("bancada.exemplo.net", 55440))
        self.assertEqual(rp.separar_endereco("200.1.2.3:6000"), ("200.1.2.3", 6000))
        self.assertEqual(rp.separar_endereco("[2804::1]:7000"), ("2804::1", 7000))
        for ruim in ("", "a b", "x:0", "x:99999", "http://x", "x:porta"):
            self.assertIsNone(rp.separar_endereco(ruim), ruim)

    def test_formato_do_retroarch(self):
        # netplay_custom_mitm_server separa pela barra vertical; "host:porta" da "Failed to resolve host" (10/11/2026).
        self.assertEqual(rp.para_o_retroarch("200.1.2.3:6000"), "200.1.2.3|6000")
        self.assertEqual(rp.para_o_retroarch("bancada.exemplo.net"), "bancada.exemplo.net|55440")
        self.assertIsNone(rp.para_o_retroarch("a b"))

    def test_limitador(self):
        limite = rp.Limitador(2, 10)
        self.assertTrue(limite.pode("a", 0))
        self.assertTrue(limite.pode("a", 1))
        self.assertFalse(limite.pode("a", 2))
        self.assertTrue(limite.pode("b", 2))
        self.assertTrue(limite.pode("a", 11))

    def test_repasse_fora_do_ar(self):
        livre = socket.socket()
        livre.bind(("127.0.0.1", 0))
        porta = livre.getsockname()[1]
        livre.close()
        self.assertFalse(rp.saude("127.0.0.1:%d" % porta, 1))
        codigo, erro = rp.reservar_sala("127.0.0.1:%d" % porta)
        self.assertIsNone(codigo)
        self.assertIn("Nao consegui", erro)


if __name__ == "__main__":
    unittest.main()
