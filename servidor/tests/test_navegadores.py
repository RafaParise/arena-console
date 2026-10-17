# -*- coding: utf-8 -*-
"""Em que navegador a tela do ARENA abre (servidor\\navegadores.py, item 11).

Pedido do Rafael (15/10/2026): "rodar em qualquer navegador padrao que o
aluno tenha". Aqui so a logica (a escolha e o comando), sem abrir navegador:
o teste de verdade, com a tela aberta em cada navegador, e'
testes\\teste_navegadores.py.
"""
import os
import sys
import unittest

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PASTA_SERVIDOR not in sys.path:
    sys.path.insert(0, PASTA_SERVIDOR)

import navegadores  # noqa: E402

EDGE = {"codigo": "edge", "nome": "Microsoft Edge", "familia": "chromium", "programa": r"C:\E\msedge.exe"}
FIREFOX = {"codigo": "firefox", "nome": "Mozilla Firefox", "familia": "firefox", "programa": r"C:\F\firefox.exe"}
OPERA = {"codigo": "opera", "nome": "Opera", "familia": "opera", "programa": r"C:\O\opera.exe"}


class Leitura(unittest.TestCase):
    def test_programa_do_comando(self):
        self.assertEqual(navegadores.programa_do_comando(
            '"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --single-argument %1'),
            "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe")
        self.assertEqual(navegadores.programa_do_comando(
            "C:\\Program Files\\Mozilla Firefox\\firefox.exe -osint -url \"%1\""),
            "C:\\Program Files\\Mozilla Firefox\\firefox.exe")

    def test_codigo_do_programa(self):
        self.assertEqual(navegadores.codigo_do_programa(r"C:\x\Google\Chrome\Application\chrome.exe"), "chrome")
        self.assertEqual(navegadores.codigo_do_programa(r"C:\x\Chromium\Application\chrome.exe"), "chromium")
        self.assertEqual(navegadores.codigo_do_programa(r"C:\x\Mozilla Firefox\firefox.exe"), "firefox")
        self.assertEqual(navegadores.codigo_do_programa("/usr/bin/firefox-esr"), "firefox")
        self.assertIsNone(navegadores.codigo_do_programa(r"C:\x\navegador_novo.exe"))

    def test_progid_do_padrao(self):
        casos = {"MSEdgeHTM": "edge", "ChromeHTML": "chrome", "FirefoxURL-308046B0AF4A39CB": "firefox",
                 "BraveHTML": "brave", "VivaldiHTM.AB12CD": "vivaldi", "OperaStable": "opera",
                 "AppXq0fevzme2pys62n3e0fbqa7peapykr8v": None}
        for progid, esperado in casos.items():
            with self.subTest(progid=progid):
                self.assertEqual(navegadores.codigo_do_progid(progid), esperado)


class Escolha(unittest.TestCase):
    def test_o_escolhido_vence_o_padrao(self):
        self.assertEqual(navegadores.escolher("firefox", [EDGE, FIREFOX], padrao="edge")["codigo"], "firefox")

    def test_sem_escolha_vale_o_padrao_do_computador(self):
        self.assertEqual(navegadores.escolher("automatico", [EDGE, FIREFOX], padrao="firefox")["codigo"],
                         "firefox")

    def test_escolhido_que_sumiu_vale_o_padrao(self):
        self.assertEqual(navegadores.escolher("brave", [EDGE, FIREFOX], padrao="firefox")["codigo"], "firefox")

    def test_padrao_desconhecido_vale_o_primeiro_da_lista(self):
        self.assertEqual(navegadores.escolher("automatico", [EDGE, FIREFOX], padrao=None)["codigo"], "edge")

    def test_nenhum_navegador(self):
        self.assertIsNone(navegadores.escolher("automatico", [], padrao=None))


class Comando(unittest.TestCase):
    def test_chromium_em_janela_de_aplicativo(self):
        linha = navegadores.comando(EDGE, "http://127.0.0.1:8777/")
        self.assertEqual(linha[:2], [EDGE["programa"], "--app=http://127.0.0.1:8777/"])
        self.assertIn("--window-size=1180,760", linha)

    def test_firefox_em_janela_nova(self):
        self.assertEqual(navegadores.comando(FIREFOX, "http://127.0.0.1:8777/"),
                         [FIREFOX["programa"], "-new-window", "http://127.0.0.1:8777/"])

    def test_opera_em_janela_nova(self):
        self.assertEqual(navegadores.comando(OPERA, "http://x/")[1:], ["--new-window", "http://x/"])


class Configuracao(unittest.TestCase):
    def test_a_configuracao_aceita_os_conhecidos(self):
        import arena
        self.assertEqual(arena.config_padrao()["navegador"], "automatico")
        for codigo in ("automatico", "edge", "chrome", "firefox", "brave"):
            self.assertIn(codigo, arena.NAVEGADORES_ACEITOS)
        self.assertNotIn("qualquer", arena.NAVEGADORES_ACEITOS)


if __name__ == "__main__":
    unittest.main()
