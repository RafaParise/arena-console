# -*- coding: utf-8 -*-
"""A internet conferida na hora (arena.ha_internet_agora). Achado de
16/10/2026: a vigia so confere a internet depois do primeiro intervalo (20 s;
60 s no modo economico), e logo ao abrir o ARENA a busca da biblioteca, o
download dos jogos livres e a busca de capas diziam "sem internet" COM
internet."""
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)
import arena  # noqa: E402


class TestInternetNaHora(unittest.TestCase):
    def setUp(self):
        self.vigia = arena.VIGIA["internet"]
        self.original = arena.internet_disponivel
        self.perguntas = 0

    def tearDown(self):
        arena.VIGIA["internet"] = self.vigia
        arena.internet_disponivel = self.original

    def responde(self, valor):
        def conferir():
            self.perguntas += 1
            return valor
        arena.internet_disponivel = conferir

    def test_a_vigia_ainda_nao_conferiu(self):
        arena.VIGIA["internet"] = False
        self.responde(True)
        self.assertTrue(arena.ha_internet_agora())
        self.assertEqual(self.perguntas, 1)
        self.responde(False)
        self.assertFalse(arena.ha_internet_agora())

    def test_a_vigia_ja_viu_internet(self):
        arena.VIGIA["internet"] = True
        self.responde(False)
        self.assertTrue(arena.ha_internet_agora())
        self.assertEqual(self.perguntas, 0)          # nem pergunta de novo


if __name__ == "__main__":
    unittest.main()
