# -*- coding: utf-8 -*-
"""Os 60 quadros de verdade do GameCube e do Wii (servidor\\quadros_dolphin.py)."""
import os
import sys
import tempfile
import unittest

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PASTA_SERVIDOR not in sys.path:
    sys.path.insert(0, PASTA_SERVIDOR)
import quadros_dolphin  # noqa: E402

PASTA_TESTES = os.path.join(os.path.dirname(PASTA_SERVIDOR), "testes")
if PASTA_TESTES not in sys.path:
    sys.path.insert(0, PASTA_TESTES)
import limpeza  # noqa: E402

SYS_INI = ("# G3RP52 - Shrek 2\n\n[Core]\n# nada\n\n[Gecko]\n$16:9 Widescreen\n04002FE0 3D208026\n$60fps\n"
           "041ED160 28000001\n\n[ActionReplay]\n$Infinite Lives\n00000000 00000000\n")


class LerId(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_dolphin_id_")

    def tearDown(self):
        limpeza.apagar_pasta(self.pasta)

    def _arquivo(self, nome, conteudo):
        caminho = os.path.join(self.pasta, nome)
        with open(caminho, "wb") as arquivo:
            arquivo.write(conteudo)
        return caminho

    def test_iso_wbfs_e_rvz(self):
        self.assertEqual(quadros_dolphin.ler_id(self._arquivo("a.iso", b"GM4P01\x00\x02" + b"\x00" * 100)), ("GM4P01", 2))
        self.assertEqual(quadros_dolphin.ler_id(self._arquivo("b.wbfs", b"WBFS" + b"\x00" * 0x1FC + b"RMCE01\x00\x00" + b"\x00" * 8)),
                         ("RMCE01", 0))
        rvz = b"RVZ\x01" + b"\x00" * 0x54 + b"GFZE01\x00\x00"
        self.assertEqual(quadros_dolphin.ler_id(self._arquivo("c.rvz", rvz)), ("GFZE01", 0))

    def test_arquivo_que_nao_e_disco(self):
        self.assertIsNone(quadros_dolphin.ler_id(self._arquivo("x.bin", b"\x00" * 64)))
        self.assertIsNone(quadros_dolphin.ler_id(os.path.join(self.pasta, "nao_existe.iso")))


class Codigos(unittest.TestCase):
    def test_le_as_secoes(self):
        achados = quadros_dolphin.codigos(SYS_INI)
        self.assertEqual(achados["Gecko"], ["$16:9 Widescreen", "$60fps"])
        self.assertEqual(achados["ActionReplay"], ["$Infinite Lives"])
        self.assertNotIn("Core", achados)


class Aplicar(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_dolphin_60_")
        self.dolphin = os.path.join(self.pasta, "Dolphin-x64")
        self.dados = os.path.join(self.pasta, "dados")
        os.makedirs(os.path.join(self.dolphin, "Sys", "GameSettings"))
        with open(os.path.join(self.dolphin, "Sys", "GameSettings", "G3RP52.ini"), "w", encoding="utf-8") as arquivo:
            arquivo.write(SYS_INI)
        self.ini = os.path.join(self.dolphin, "User", "GameSettings", "G3RP52.ini")

    def tearDown(self):
        limpeza.apagar_pasta(self.pasta)

    def _ler(self):
        with open(self.ini, encoding="utf-8") as arquivo:
            return arquivo.read()

    def test_acha_o_codigo_de_60(self):
        self.assertEqual(quadros_dolphin.codigo_de_60(self.dolphin, "G3RP52"), ("Gecko", "$60fps"))
        self.assertIsNone(quadros_dolphin.codigo_de_60(self.dolphin, "GFZE01"))

    def test_liga_e_tira_criando_o_arquivo(self):
        self.assertEqual(quadros_dolphin.aplicar(self.dolphin, "G3RP52", 0, True, self.dados), "$60fps")
        texto = self._ler()
        self.assertIn("[Core]\nEnableCheats = True\n", texto)
        self.assertIn("[Gecko_Enabled]\n$60fps\n", texto)
        quadros_dolphin.aplicar(self.dolphin, "G3RP52", 0, True, self.dados)
        self.assertEqual(self._ler().count("$60fps"), 1)
        self.assertEqual(quadros_dolphin.aplicar(self.dolphin, "G3RP52", 0, False, self.dados), "")
        self.assertFalse(os.path.exists(self.ini))

    def test_o_ajuste_da_pessoa_fica(self):
        os.makedirs(os.path.dirname(self.ini))
        with open(self.ini, "w", encoding="utf-8") as arquivo:
            arquivo.write("[Core]\nEnableCheats = True\nCPUThread = False\n\n[Gecko_Enabled]\n$16:9 Widescreen\n")
        quadros_dolphin.aplicar(self.dolphin, "G3RP52", 0, True, self.dados)
        texto = self._ler()
        self.assertEqual(texto.count("EnableCheats = True"), 1)
        self.assertIn("$60fps", texto)
        quadros_dolphin.aplicar(self.dolphin, "G3RP52", 0, False, self.dados)
        texto = self._ler()
        self.assertNotIn("$60fps", texto)
        # A pessoa ja tinha ligado as trapacas e o widescreen: ficam.
        self.assertIn("EnableCheats = True", texto)
        self.assertIn("$16:9 Widescreen", texto)
        self.assertIn("CPUThread = False", texto)

    def test_jogo_sem_codigo(self):
        self.assertEqual(quadros_dolphin.aplicar(self.dolphin, "GFZE01", 0, True, self.dados), "")
        self.assertFalse(os.path.isdir(os.path.join(self.dolphin, "User", "GameSettings")))


if __name__ == "__main__":
    unittest.main()
