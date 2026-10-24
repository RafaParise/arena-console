# -*- coding: utf-8 -*-
"""Os remendos do ARENA para o RetroArch 1.22.2 do Android (android/retroarch/*.patch).

Sao texto escrito (e gerado) a mao, e um erro de conta de linhas so apareceria na hora de compilar o RetroArch, uns
minutos depois. Aqui se confere o formato. O de ordem dos controles nasceu de um achado do Rafael (24/10/2026, dois
GameSir): o RetroArch do Android registrava o controle que mandasse o primeiro evento, e nao o primeiro conectado."""
import os
import re
import sys
import unittest
from unittest import mock

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ = os.path.dirname(PASTA_SERVIDOR)
PASTA = os.path.join(RAIZ, "android", "retroarch")
sys.path.insert(0, os.path.join(RAIZ, "testes"))
sys.path.insert(0, os.path.join(RAIZ, "ferramentas"))

import compilar_retroarch_android as compilador  # noqa: E402


def ler(nome):
    with open(os.path.join(PASTA, nome), "rb") as arquivo:
        bruto = arquivo.read()
    return bruto, bruto.decode("utf-8")


class FormatoDosRemendos(unittest.TestCase):
    NOMES = ["arena-args.patch", "arena-controles.patch"]

    def test_os_remendos_sao_estes_e_nesta_ordem(self):
        self.assertEqual([os.path.basename(r) for r in compilador.remendos()], self.NOMES)

    def test_so_fim_de_linha_do_unix(self):
        for nome in self.NOMES:
            with self.subTest(nome=nome):
                self.assertNotIn(b"\r", ler(nome)[0])

    def test_a_conta_de_linhas_de_cada_trecho_fecha(self):
        for nome in self.NOMES:
            texto = ler(nome)[1]
            trechos = re.split(r"^(?=@@ )", texto, flags=re.M)[1:]
            self.assertGreaterEqual(len(trechos), 1, nome)
            for trecho in trechos:
                cabeca, *linhas = trecho.split("\n")
                # o trecho acaba onde acaba o proximo "diff --git" (arquivo seguinte do mesmo remendo)
                corpo = []
                for linha in linhas:
                    if linha.startswith("diff --git"):
                        break
                    corpo.append(linha)
                while corpo and corpo[-1] == "":
                    corpo.pop()
                achado = re.match(r"@@ -\d+(?:,(\d+))? \+\d+(?:,(\d+))? @@", cabeca)
                self.assertTrue(achado, (nome, cabeca))
                velho = int(achado.group(1) or 1)
                novo = int(achado.group(2) or 1)
                self.assertEqual(sum(1 for l in corpo if l[:1] in (" ", "-")), velho, (nome, cabeca))
                self.assertEqual(sum(1 for l in corpo if l[:1] in (" ", "+")), novo, (nome, cabeca))


class RemendoDosControles(unittest.TestCase):
    def setUp(self):
        self.texto = ler("arena-controles.patch")[1]

    def test_mexe_so_no_driver_de_entrada_do_android(self):
        arquivos = re.findall(r"^(?:---|\+\+\+) (\S+)", self.texto, re.M)
        self.assertEqual(arquivos, ["a/input/drivers/android_input.c", "b/input/drivers/android_input.c"])

    def test_registra_os_controles_ligados_em_ordem_crescente_de_numero(self):
        self.assertIn("getDeviceIds", self.texto)                      # a lista de aparelhos que o Android tem
        self.assertIn("lista[j] > atual", self.texto)                  # em ordem crescente (a ordem de conexao)
        self.assertIn("handle_hotplug(android, android_app, &porta, id, (int)fontes)", self.texto)
        self.assertIn("AINPUT_SOURCE_GAMEPAD", self.texto)             # so controle de jogo
        self.assertIn("AINPUT_SOURCE_JOYSTICK", self.texto)
        self.assertIn("if (id < 0)", self.texto)                       # o "Virtual" (adb, teclado virtual) fica de fora
        self.assertIn('strstr(nome, "Virtual")', self.texto)

    def test_so_roda_uma_vez_e_antes_de_ler_os_eventos(self):
        self.assertIn("if (!android->arena_ordenou)", self.texto)
        self.assertIn("android->arena_ordenou = true;", self.texto)
        self.assertLess(self.texto.index("android->arena_ordenou = true;"), self.texto.index("/* Read all pending events. */"))

    def test_o_compilador_confere_que_a_biblioteca_tem_o_remendo(self):
        with open(os.path.join(RAIZ, "ferramentas", "compilar_retroarch_android.py"), encoding="utf-8") as arquivo:
            codigo = arquivo.read()
        self.assertIn('b"[ARENA] Controles na ordem"', codigo)
        self.assertIn("[ARENA] Controles na ordem em que foram conectados", self.texto)


class MarcaDosRemendos(unittest.TestCase):
    def test_a_marca_muda_quando_um_remendo_muda(self):
        antes = compilador.marca_do_remendo()
        self.assertRegex(antes, r"^[0-9a-f]{64}$")
        with mock.patch.object(compilador.preparar_linux, "marca", return_value="outra"):
            self.assertNotEqual(compilador.marca_do_remendo(), antes)
        self.assertEqual(compilador.marca_do_remendo(), antes)         # sem mexer, a mesma marca


if __name__ == "__main__":
    unittest.main()
