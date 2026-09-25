# -*- coding: utf-8 -*-
"""Testes do cuidado com o cache de video do PS1 (graficos.preparar_cache_ps1
e fixar_cache_ps1), num arquivo de mentira numa pasta temporaria."""

import os
import shutil
import stat
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

import graficos  # noqa: E402


class TestCachePS1(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="arena_cache_teste_")
        self._antigo = graficos.CACHE_PS1
        graficos.CACHE_PS1 = os.path.join(self.dir, "vulkan_pipelines.bin")

    def tearDown(self):
        for n in os.listdir(self.dir):
            os.chmod(os.path.join(self.dir, n), stat.S_IWRITE | stat.S_IREAD)
        graficos.CACHE_PS1 = self._antigo
        shutil.rmtree(self.dir, ignore_errors=True)

    def escrever(self, tamanho):
        with open(graficos.CACHE_PS1, "wb") as f:
            f.write(b"x" * tamanho)

    def travado(self):
        return not os.access(graficos.CACHE_PS1, os.W_OK)

    def test_sem_cache_nao_faz_nada(self):
        self.assertEqual(graficos.preparar_cache_ps1("Placa A"), -1)
        self.assertFalse(graficos.fixar_cache_ps1(-1, "Placa A"))

    def test_cache_que_cresceu_fica_livre(self):
        self.escrever(100)
        antes = graficos.preparar_cache_ps1("Placa A")
        self.escrever(200)                       # o jogo aprendeu algo novo
        self.assertFalse(graficos.fixar_cache_ps1(antes, "Placa A"))
        self.assertFalse(self.travado())

    def test_cache_estavel_trava(self):
        self.escrever(100)
        antes = graficos.preparar_cache_ps1("Placa A")
        self.assertTrue(graficos.fixar_cache_ps1(antes, "Placa A"))
        self.assertTrue(self.travado())
        # Na partida seguinte, na mesma placa: continua travado e intacto.
        self.assertEqual(graficos.preparar_cache_ps1("Placa A"), 100)
        self.assertTrue(self.travado())

    def test_outra_placa_apaga_o_cache_travado(self):
        self.escrever(100)
        antes = graficos.preparar_cache_ps1("Placa A")
        graficos.fixar_cache_ps1(antes, "Placa A")
        self.assertEqual(graficos.preparar_cache_ps1("Placa B"), -1)
        self.assertFalse(os.path.exists(graficos.CACHE_PS1))


if __name__ == "__main__":
    unittest.main()
