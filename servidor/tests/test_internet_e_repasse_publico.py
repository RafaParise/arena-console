# -*- coding: utf-8 -*-
"""A internet de casa para partidas (servidor\\internet_de_casa.py) e o retransmissor publico pela ponte local
(servidor\\repasse_publico.py), 13/11/2026. Sem internet: um "tunel" de mentira no 127.0.0.1."""
import os
import socket
import sys
import threading
import unittest
from unittest import mock

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PASTA_SERVIDOR not in sys.path:
    sys.path.insert(0, PASTA_SERVIDOR)
import internet_de_casa as idc  # noqa: E402
import repasse_publico as rpub  # noqa: E402


class Saltos(unittest.TestCase):
    def test_dois_roteadores_e_rede_da_operadora(self):
        lido = idc.ler_saltos(["10.0.20.1", "192.168.18.1", "172.29.0.7", "172.29.2.221", "8.8.8.8"])
        self.assertEqual(lido["roteadores"], ["10.0.20.1", "192.168.18.1"])
        self.assertTrue(lido["operadora_privada"])
        self.assertFalse(lido["cgnat"])

    def test_salto_na_faixa_do_cgnat_decide(self):
        self.assertTrue(idc.ler_saltos(["192.168.0.1", "100.70.1.1", "200.1.1.1"])["cgnat"])

    def test_um_roteador_e_internet(self):
        lido = idc.ler_saltos(["192.168.0.1", "*", "200.1.1.1"])
        self.assertEqual(lido["roteadores"], ["192.168.0.1"])
        self.assertFalse(lido["operadora_privada"] or lido["cgnat"])


class Conclusao(unittest.TestCase):
    def _conferir(self, publico, saltos, roteador_ip):
        roteador = {"controle": "http://192.168.18.1:1/c", "servico": "x"} if roteador_ip else None
        with mock.patch.object(idc, "ip_publico", return_value=publico), \
                mock.patch.object(idc, "saltos", return_value=saltos), \
                mock.patch.object(idc, "achar_roteador_upnp", return_value=roteador), \
                mock.patch.object(idc, "ip_do_roteador", return_value=roteador_ip):
            return idc.conferir()

    def test_roteador_na_faixa_do_cgnat_e_cgnat_mesmo_com_dois_roteadores(self):
        # O caso da casa do Rafael (13/11/2026): a ONT disse 100.66.29.193 pelo UPnP.
        r = self._conferir("177.185.40.174", ["10.0.20.1", "192.168.18.1", "172.29.0.7"], "100.66.29.193")
        self.assertEqual(r["conclusao"], "cgnat")
        self.assertIn("repasse", r["explica"])

    def test_roteador_com_o_mesmo_ip_da_internet_esta_pronto(self):
        r = self._conferir("200.1.2.3", ["192.168.0.1", "200.1.2.1"], "200.1.2.3")
        self.assertEqual(r["conclusao"], "pronto")

    def test_roteador_de_dentro_nao_decide_e_pede_a_conferencia(self):
        r = self._conferir("200.1.2.3", ["10.0.20.1", "192.168.18.1", "200.1.2.1"], "192.168.18.40")
        self.assertEqual(r["conclusao"], "dois_roteadores")
        self.assertEqual(len(r["passos"]), 3)
        self.assertEqual(r["pagina_do_roteador"], "http://192.168.18.1/")

    def test_sem_internet(self):
        self.assertEqual(self._conferir(None, [], None)["conclusao"], "sem_internet")

    def test_comparar_o_que_a_pessoa_digitou(self):
        self.assertEqual(idc.comparar("100.66.29.193", "177.185.40.174")["conclusao"], "cgnat")
        self.assertEqual(idc.comparar("177.185.40.174", "177.185.40.174")["conclusao"], "sem_cgnat")
        self.assertEqual(idc.comparar("abc", "177.185.40.174")["conclusao"], "invalido")

    def test_upnp_so_na_rede_de_casa(self):
        self.assertTrue(idc._so_da_rede_de_casa("http://192.168.18.1:49652/desc.xml"))
        self.assertFalse(idc._so_da_rede_de_casa("http://8.8.8.8/desc.xml"))
        self.assertFalse(idc._so_da_rede_de_casa("http://127.0.0.1/desc.xml"))
        self.assertFalse(idc._so_da_rede_de_casa("https://192.168.0.1/"))


class CodigoDaSala(unittest.TestCase):
    def test_ida_e_volta_de_qualquer_jeito(self):
        sessao = bytes(range(1, 13))
        codigo = rpub.codigo_da_sessao(sessao)
        self.assertRegex(codigo, r"^[A-Z2-7]{4}(-[A-Z2-7]{4}){4}$")
        for digitado in (codigo, codigo.lower(), codigo.replace("-", ""), " " + codigo.replace("-", " ") + " "):
            self.assertEqual(rpub.sessao_do_codigo(digitado), sessao)

    def test_codigo_curto_zero_ou_lixo_nao_vale(self):
        self.assertIsNone(rpub.sessao_do_codigo("123456"))
        self.assertIsNone(rpub.sessao_do_codigo(rpub.codigo_da_sessao(bytes(12))))
        self.assertFalse(rpub.parece_codigo_publico("ABC"))


class PonteLocal(unittest.TestCase):
    """Um tunel de mentira: responde RATS + 12 bytes ao pedido de sessao e devolve (eco) o resto."""

    def setUp(self):
        self.sessao = bytes(range(20, 32))
        self.escuta = socket.socket()
        self.escuta.bind(("127.0.0.1", 0))
        self.escuta.listen(4)
        threading.Thread(target=self._tunel, daemon=True).start()

    def tearDown(self):
        rpub.fechar_ponte()
        self.escuta.close()

    def _tunel(self):
        while True:
            try:
                ligacao, _ = self.escuta.accept()
            except OSError:
                return
            pedido = ligacao.recv(16)
            if pedido == rpub.PEDIDO_DE_SESSAO:
                ligacao.sendall(b"RATS" + self.sessao)
            while True:
                dados = ligacao.recv(4096)
                if not dados:
                    break
                ligacao.sendall(dados)
            ligacao.close()

    def test_a_ponte_le_a_sessao_e_passa_os_bytes(self):
        ponte = rpub.abrir_ponte(self.escuta.getsockname())
        with socket.create_connection(("127.0.0.1", ponte.porta), timeout=5) as retroarch:
            retroarch.sendall(rpub.PEDIDO_DE_SESSAO)
            self.assertEqual(retroarch.recv(16), b"RATS" + self.sessao)
            codigo = ponte.esperar_codigo(5)
            self.assertEqual(rpub.sessao_do_codigo(codigo), self.sessao)
            retroarch.sendall(b"jogo")
            self.assertEqual(retroarch.recv(4), b"jogo")

    def test_a_ponte_so_escuta_neste_computador(self):
        ponte = rpub.abrir_ponte(self.escuta.getsockname())
        self.assertEqual(ponte.escuta.getsockname()[0], "127.0.0.1")

    def test_sem_pedido_de_sessao_nao_inventa_codigo(self):
        ponte = rpub.abrir_ponte(self.escuta.getsockname())
        with socket.create_connection(("127.0.0.1", ponte.porta), timeout=5) as outro:
            outro.sendall(b"RATL" + bytes(range(12)))
            self.assertIsNone(ponte.esperar_codigo(1))


if __name__ == "__main__":
    unittest.main()
