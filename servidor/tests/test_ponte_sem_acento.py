# -*- coding: utf-8 -*-
"""A ponte sem acento (servidor\\ponte_sem_acento.py). O Hatari (Atari ST)
nao abre caminho com acento: com o ARENA em "...Pedagógicos\\...", a BIOS e
o disquete vao por uma pasta sem acento, e o disquete volta se o jogo gravou
nele. A abertura de verdade, com o "ó" no caminho, esta em
testes\\teste_consoles_livres.py."""
import os
import shutil
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)
import ponte_sem_acento as ponte  # noqa: E402

HATARI = "hatari_libretro.dll"


class TestPonteSemAcento(unittest.TestCase):
    def setUp(self):
        self.base = tempfile.mkdtemp(prefix="arena_ponte_")
        self.com_acento = os.path.join(self.base, "Pedagógicos")
        self.sistema = os.path.join(self.com_acento, "system")
        os.makedirs(self.sistema)
        with open(os.path.join(self.sistema, "tos.img"), "wb") as arquivo:
            arquivo.write(b"TOS" * 1000)
        self.jogo = os.path.join(self.com_acento, "Jogo Ação.st")
        with open(self.jogo, "wb") as arquivo:
            arquivo.write(b"disquete" * 100)
        # A ponte trabalha numa pasta temporaria sem acento: aqui, uma do teste.
        self.temporaria = os.path.join(self.base, "temp")
        os.makedirs(self.temporaria)
        self.antes = tempfile.tempdir
        tempfile.tempdir = self.temporaria

    def tearDown(self):
        tempfile.tempdir = self.antes
        shutil.rmtree(self.base, ignore_errors=True)

    def test_so_o_nucleo_que_nao_aceita_acento_e_so_com_acento(self):
        self.assertTrue(ponte.precisa(HATARI, self.sistema, self.jogo))
        self.assertTrue(ponte.precisa("C:\\x\\cores\\hatari_libretro.dll", self.sistema, "C:\\jogo.st"))
        self.assertFalse(ponte.precisa(HATARI, "C:\\ARENA\\retroarch\\system", "C:\\ARENA\\jogo.st"))
        self.assertFalse(ponte.precisa("bluemsx_libretro.dll", self.sistema, self.jogo))
        self.assertFalse(ponte.precisa(None, self.sistema, self.jogo))

    def test_leva_a_bios_e_o_jogo_e_devolve_o_disquete_gravado(self):
        caminho, opcoes, devolver = ponte.preparar(HATARI, self.sistema, self.jogo)
        self.assertTrue(caminho.isascii() and opcoes["system_directory"].isascii())
        self.assertTrue(caminho.startswith(self.temporaria))
        self.assertTrue(caminho.endswith(".st"))
        with open(os.path.join(opcoes["system_directory"], "tos.img"), "rb") as arquivo:
            self.assertEqual(arquivo.read(), b"TOS" * 1000)
        self.assertFalse(devolver())                       # nao gravou: nada volta
        with open(caminho, "ab") as arquivo:               # o jogo gravou o recorde
            arquivo.write(b"recorde")
        self.assertTrue(devolver())
        with open(self.jogo, "rb") as arquivo:
            self.assertEqual(arquivo.read(), b"disquete" * 100 + b"recorde")

    def test_jogo_sem_acento_abre_direto(self):
        jogo = os.path.join(self.base, "jogo.st")
        shutil.copyfile(self.jogo, jogo)
        caminho, opcoes, devolver = ponte.preparar(HATARI, self.sistema, jogo)
        self.assertEqual(caminho, jogo)
        self.assertTrue(opcoes["system_directory"].isascii())
        self.assertFalse(devolver())

    def test_sem_pasta_sem_acento_avisa(self):
        tempfile.tempdir = self.com_acento
        publica = os.environ.get("PUBLIC")
        os.environ["PUBLIC"] = self.com_acento
        try:
            self.assertIsNone(ponte.pasta_da_ponte())
            with self.assertRaises(OSError):
                ponte.preparar(HATARI, self.sistema, self.jogo)
        finally:
            if publica is None:
                os.environ.pop("PUBLIC", None)
            else:
                os.environ["PUBLIC"] = publica


CFG = os.path.join(os.path.dirname(RAIZ), "retroarch", "retroarch.cfg")


@unittest.skipUnless(os.path.isfile(CFG), "sem o RetroArch nesta copia (retroarch.cfg)")
class TestPonteNoArquivoDaPartida(unittest.TestCase):
    """O arquivo da partida (arena.gravar_override) leva a pasta system da
    ponte: antes da correcao de 14/10/2026, ele escrevia a do ARENA por cima
    e o Hatari continuava sem achar a BIOS."""

    def setUp(self):
        from unittest import mock
        import arena
        self.arena = arena
        self.dir = tempfile.mkdtemp(prefix="arena_ponte_override_")
        pastas = {nome: os.path.join(self.dir, nome.lower()) for nome in (
            "PASTA_DADOS", "PASTA_SAVES", "PASTA_STATES", "PASTA_CAPTURAS", "PASTA_SISTEMA",
            "PASTA_CHEATS", "PASTA_REMAPS", "PASTA_CONTROLES", "PASTA_CACHE", "PASTA_PERFIS_CONTROLE")}
        pastas["ARQUIVO_OVERRIDE"] = os.path.join(pastas["PASTA_DADOS"], "arena_override.cfg")
        self.sistema = pastas["PASTA_SISTEMA"]
        self.troca = mock.patch.multiple(arena, **pastas)
        self.troca.start()

    def tearDown(self):
        self.troca.stop()
        shutil.rmtree(self.dir, ignore_errors=True)

    def pasta_system(self, extras):
        caminho = self.arena.gravar_override(self.arena.config_padrao(), extras=extras)
        with open(caminho, encoding="utf-8") as arquivo:
            linha = next(l for l in arquivo if l.startswith("system_directory "))
        return linha.split("=", 1)[1].strip().strip('"')

    def test_a_pasta_da_ponte_chega_ao_retroarch(self):
        self.assertEqual(self.pasta_system({"system_directory": "C:\\Temp\\ARENA-sem-acento\\system"}),
                         "C:\\Temp\\ARENA-sem-acento\\system")

    def test_sem_a_ponte_vale_a_pasta_do_arena(self):
        self.assertEqual(os.path.normcase(self.pasta_system({})), os.path.normcase(self.sistema))
        self.assertEqual(os.path.normcase(self.pasta_system(None)), os.path.normcase(self.sistema))


if __name__ == "__main__":
    unittest.main()
