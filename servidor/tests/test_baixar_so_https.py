# -*- coding: utf-8 -*-
"""Todo download do ARENA vai por HTTPS (achado F4 da auditoria 4, pelo
Claude Security, 22/10/2026): o que vem sem criptografia, qualquer um no
caminho da rede da escola le e troca."""
import os
import sys
import tempfile
import unittest
import urllib.error
import urllib.request
from unittest import mock

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
import baixar  # noqa: E402
import capas_online  # noqa: E402


class SoHttps(unittest.TestCase):

    def test_o_curl_so_aceita_https_tambem_no_redirecionamento(self):
        with mock.patch.object(baixar, "curl", return_value="curl"), \
                mock.patch.object(baixar.subprocess, "run") as rodar:
            rodar.return_value = mock.Mock(returncode=0, stdout=b"")
            baixar.rodar("https://exemplo.org/capa.png", 5)
        comando = rodar.call_args[0][0]
        self.assertEqual(comando[comando.index("--proto") + 1], "=https")
        self.assertEqual(comando[comando.index("--proto-redir") + 1], "=https")

    def test_sem_curl_o_endereco_sem_https_nem_e_tentado(self):
        with mock.patch.object(baixar, "curl", return_value=None), \
                mock.patch.object(baixar._ABRIR, "open", side_effect=AssertionError("nao devia abrir")):
            self.assertEqual(baixar.rodar("http://download.xbox.com/capa.jpg", 5), (1, b""))
            self.assertEqual(baixar.rodar("ftp://exemplo.org/jogo.zip", 5), (1, b""))

    def test_http_so_no_proprio_computador(self):
        # O que nao sai do computador ninguem le no caminho da rede: e' assim
        # que os testes servem os "sites" de mentira.
        for endereco in ("http://127.0.0.1:8080/jogo.nes", "http://localhost/x", "http://[::1]:9/x"):
            self.assertTrue(baixar._protocolo_aceito(endereco), endereco)
        for endereco in ("http://download.xbox.com/capa.jpg", "http://192.168.0.10/x", "ftp://127.0.0.1/x",
                         "http://127.0.0.1.exemplo.org/x"):
            self.assertFalse(baixar._protocolo_aceito(endereco), endereco)
        with mock.patch.object(baixar, "curl", return_value="curl"), \
                mock.patch.object(baixar.subprocess, "run") as rodar:
            rodar.return_value = mock.Mock(returncode=0, stdout=b"")
            baixar.rodar("http://127.0.0.1:8080/jogo.nes", 5)
            local = rodar.call_args[0][0]
            baixar.rodar("http://download.xbox.com/capa.jpg", 5)
            de_fora = rodar.call_args[0][0]
        self.assertEqual(local[local.index("--proto") + 1], "=http,https")
        self.assertEqual(de_fora[de_fora.index("--proto") + 1], "=https")
        self.assertEqual(local[local.index("--proto-redir") + 1], "=https")

    def test_redirecionamento_para_http_e_recusado(self):
        tratador = baixar._SoHttps()
        pedido = urllib.request.Request("https://exemplo.org/a")
        with self.assertRaises(urllib.error.URLError):
            tratador.redirect_request(pedido, None, 302, "Found", {}, "http://exemplo.org/b")
        novo = tratador.redirect_request(pedido, None, 302, "Found", {}, "https://exemplo.org/b")
        self.assertEqual(novo.full_url, "https://exemplo.org/b")

    def test_redirecionamento_recusado_vira_o_codigo_1(self):
        with mock.patch.object(baixar, "curl", return_value=None), \
                mock.patch.object(baixar._ABRIR, "open", side_effect=baixar._SemHttps("redirecionamento sem HTTPS")):
            self.assertEqual(baixar.rodar("https://exemplo.org/a", 5), (1, b""))

    def test_a_capa_do_xbox360_nao_vem_mais_pelo_disco(self):
        with tempfile.NamedTemporaryFile(suffix=".iso", delete=False) as disco:
            disco.write(b"\0" * 4096)
        try:
            with mock.patch.object(capas_online, "_baixar_imagem", side_effect=AssertionError("nao devia baixar")):
                self.assertIsNone(capas_online.capa_pelo_disco("xbox360", "Halo 3", disco.name))
        finally:
            os.remove(disco.name)


if __name__ == "__main__":
    unittest.main()
