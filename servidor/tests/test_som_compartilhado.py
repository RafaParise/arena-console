# -*- coding: utf-8 -*-
"""Nenhum perfil toma a placa de som so para o jogo (16/10/2026).

Achado do item 10 dos pedidos de 15/10: o perfil Qualidade (o que o
automatico escolhe para quase todo console, no Celeron e no Ryzen) e o Ultra
ligavam o modo exclusivo do WASAPI. Medido no Ryzen do professor com um fone
sem fio, o mesmo jogo de Super Nintendo, 4.300 quadros: exclusivo, 51,97
quadros/s e 21,3% de variacao no tempo de cada quadro; compartilhado, 59,89
e 2,2%. O fone consome o som no relogio dele, e a sincronia pelo som segura
o jogo nesse ritmo.

Aqui: o arquivo de opcoes de verdade (gravar_override), numa pasta
temporaria, com cada perfil e com o Ultra. O exclusivo so liga se o aluno
pedir (Ajustes -> Avancado -> "Som so para o jogo"), e a escolha dele vale
tambem no Ultra.
"""
import os
import re
import sys
import tempfile
import unittest
from unittest import mock

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PASTA_SERVIDOR not in sys.path:
    sys.path.insert(0, PASTA_SERVIDOR)

import arena  # noqa: E402

PASTA_TESTES = os.path.join(os.path.dirname(PASTA_SERVIDOR), "testes")
if PASTA_TESTES not in sys.path:
    sys.path.insert(0, PASTA_TESTES)
import limpeza  # noqa: E402


class SomCompartilhado(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_teste_som_")
        pastas = {nome: os.path.join(self.pasta, nome.lower()) for nome in (
            "PASTA_DADOS", "PASTA_SAVES", "PASTA_STATES", "PASTA_CAPTURAS", "PASTA_CHEATS",
            "PASTA_REMAPS", "PASTA_CACHE")}
        pastas["ARQUIVO_OVERRIDE"] = os.path.join(self.pasta, "arena_override.cfg")
        self.trocas = mock.patch.multiple(arena, **pastas)
        self.trocas.start()

    def tearDown(self):
        self.trocas.stop()
        limpeza.apagar_pasta(self.pasta)

    def exclusivo(self, perfil, **extra):
        config = arena.config_padrao()
        config["perfil_grafico"] = perfil
        config.update(extra)
        with open(arena.gravar_override(config, 2), encoding="utf-8") as arquivo:
            achado = re.findall(r'^audio_wasapi_exclusive_mode = "(\w+)"', arquivo.read(), re.M)
        self.assertEqual(len(achado), 1, "a chave tem que ir uma vez so")
        return achado[0]

    def test_nenhum_perfil_liga_sozinho(self):
        for perfil in list(arena.PERFIS_GRAFICOS) + ["automatico"]:
            with self.subTest(perfil=perfil):
                self.assertEqual(self.exclusivo(perfil), "false")

    def test_nem_o_ultra(self):
        self.assertEqual(self.exclusivo("qualidade", ultra_desempenho=True), "false")
        self.assertNotIn("audio_wasapi_exclusive_mode", arena.ULTRA_DESEMPENHO)

    def test_a_escolha_do_aluno_vale_ate_no_ultra(self):
        pedido = {"avancado": {"audio_wasapi_exclusive_mode": "true"}}
        self.assertEqual(self.exclusivo("qualidade", **pedido), "true")
        self.assertEqual(self.exclusivo("qualidade", ultra_desempenho=True, **pedido), "true")


if __name__ == "__main__":
    unittest.main()
