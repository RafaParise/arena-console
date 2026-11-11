# -*- coding: utf-8 -*-
"""MFG Super Motion (servidor\\mfg.py): achar, as placas, decidir e as opcoes do motor."""
import os
import sys
import tempfile
import unittest
from unittest import mock

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PASTA_SERVIDOR not in sys.path:
    sys.path.insert(0, PASTA_SERVIDOR)
import mfg  # noqa: E402

PASTA_TESTES = os.path.join(os.path.dirname(PASTA_SERVIDOR), "testes")
if PASTA_TESTES not in sys.path:
    sys.path.insert(0, PASTA_TESTES)
import limpeza  # noqa: E402

RTX = [{"numero": 0, "dlss": True, "memoria_mb": 12000, "nome": "NVIDIA GeForce RTX 3060", "xess": True}]
RADEON = [{"numero": 0, "dlss": False, "memoria_mb": 4079, "nome": "AMD Radeon(TM) Graphics", "xess": True}]


class Placas(unittest.TestCase):
    def test_le_a_saida_do_cards(self):
        texto = "@card 0 0 4079 AMD Radeon(TM) Graphics\n@card 1 1 12288 NVIDIA GeForce RTX 3060\n" \
                "@xess 0 1\n@xess 1 0\nqualquer outra linha\n"
        lista = mfg.ler_placas(texto)
        self.assertEqual([p["numero"] for p in lista], [0, 1])
        self.assertEqual(lista[0]["nome"], "AMD Radeon(TM) Graphics")
        self.assertFalse(lista[0]["dlss"])
        self.assertTrue(lista[0]["xess"])
        self.assertTrue(lista[1]["dlss"])
        self.assertEqual(lista[1]["memoria_mb"], 12288)

    def test_saida_estranha_nao_quebra(self):
        self.assertEqual(mfg.ler_placas(""), [])
        self.assertEqual(mfg.ler_placas("@card x y z\n@xess 9 1\n"), [])


class Decidir(unittest.TestCase):
    ACHADO = {"motor": "x", "pasta": "y", "origem": "instalado", "versao": "1.0.5"}

    def test_desligado_e_sem_programa(self):
        self.assertFalse(mfg.decidir("desligado", self.ACHADO, 5, False, 144, True)[0])
        usar, motivo = mfg.decidir("sempre", None, 5, False, 144, True)
        self.assertFalse(usar)
        self.assertIn("nesta maquina", motivo)

    def test_sempre_liga_ate_na_placa_fraca(self):
        self.assertTrue(mfg.decidir("sempre", self.ACHADO, 1, True, 60, False)[0])

    def test_automatico_na_maquina_alvo_fica_desligado(self):
        # Celeron N5100: integrada, nota da placa 2 ou 3.
        for nota in (1, 2, 3):
            self.assertFalse(mfg.decidir("automatico", self.ACHADO, nota, True, 60, True)[0])

    def test_automatico_liga_no_emulador_de_fora_com_placa_dedicada(self):
        self.assertTrue(mfg.decidir("automatico", self.ACHADO, 3, False, 60, True)[0])
        self.assertTrue(mfg.decidir("automatico", self.ACHADO, 5, False, 60, True)[0])
        # A integrada forte (o Ryzen de mesa com Vega, nota 4) liga: medido em 11/11/2026, o jogo ficou igual.
        self.assertTrue(mfg.decidir("automatico", self.ACHADO, 4, True, 60, True)[0])
        self.assertTrue(mfg.decidir("automatico", self.ACHADO, 4, True, 144, False)[0])
        # A integrada comum (nota 3, o Celeron N5100), nao.
        self.assertFalse(mfg.decidir("automatico", self.ACHADO, 3, True, 60, True)[0])
        # A dedicada fraca (nota 2) tambem nao.
        self.assertFalse(mfg.decidir("automatico", self.ACHADO, 2, False, 60, True)[0])

    def test_qual_programa_por_placa(self):
        rtx = [{"numero": 0, "dlss": True}]
        radeon = [{"numero": 0, "dlss": False}]
        self.assertEqual(mfg.qual_programa(rtx, True, True), "mfg")          # RTX: o DLSS MFG
        self.assertEqual(mfg.qual_programa(radeon, True, True), "lossless")  # AMD/Intel: o Lossless (medido)
        self.assertEqual(mfg.qual_programa(rtx, False, True), "lossless")
        self.assertEqual(mfg.qual_programa(radeon, True, False), "mfg")
        self.assertIsNone(mfg.qual_programa(radeon, False, False))

    def test_console_que_ficou_no_limite_nao_liga_no_automatico(self):
        usar, motivo = mfg.decidir("automatico", self.ACHADO, 5, False, 60, True, degrau=1)
        self.assertFalse(usar)
        self.assertIn("limite", motivo)
        self.assertTrue(mfg.decidir("sempre", self.ACHADO, 5, False, 60, True, degrau=2)[0])

    def test_automatico_no_retroarch_so_com_tela_rapida(self):
        self.assertFalse(mfg.decidir("automatico", self.ACHADO, 5, False, 60, False)[0])
        self.assertTrue(mfg.decidir("automatico", self.ACHADO, 5, False, 144, False)[0])

    def test_modo_desconhecido_vira_automatico(self):
        self.assertEqual(mfg.decidir("qualquer", self.ACHADO, 5, False, 60, True),
                         mfg.decidir("automatico", self.ACHADO, 5, False, 60, True))


class Opcoes(unittest.TestCase):
    def test_rtx_usa_o_dlss_na_placa_certa(self):
        opcoes = mfg.escolher_opcoes([RADEON[0], dict(RTX[0], numero=1)], 5, False, 60, False)
        self.assertEqual(opcoes["generator"], "0")
        self.assertEqual(opcoes["gpu"], "1")
        self.assertNotIn("msm_search", opcoes)

    def test_sem_rtx_usa_o_msm_fg(self):
        integrada = mfg.escolher_opcoes(RADEON, 4, True, 144, False)
        self.assertEqual(integrada["generator"], "2")
        self.assertEqual(integrada["msm_search"], "1")
        self.assertEqual(integrada["multiplier"], "2")
        dedicada = mfg.escolher_opcoes(RADEON, 5, False, 144, False)
        self.assertEqual(dedicada["msm_search"], "0")
        self.assertEqual(dedicada["multiplier"], "4")

    def test_maximo_segue_a_tela(self):
        self.assertEqual(mfg.escolher_opcoes(RTX, 5, False, 60, False)["multiplier"], "2")
        self.assertEqual(mfg.escolher_opcoes(RTX, 5, False, 120, False)["multiplier"], "4")
        self.assertEqual(mfg.escolher_opcoes(RTX, 5, False, 240, False)["multiplier"], "4")

    def test_o_que_o_arena_nunca_liga(self):
        opcoes = mfg.escolher_opcoes(RTX, 5, False, 60, True)
        # Transmissao fica desligada de proposito no ARENA; nada desenhado por cima do jogo.
        for chave in ("spout", "counter", "aml", "link", "hdr", "log", "delay", "upscaler"):
            self.assertEqual(opcoes[chave], "0", chave)
        self.assertEqual(opcoes["screen_limit"], "1")
        self.assertEqual(opcoes["game"], "1")
        self.assertEqual(mfg.escolher_opcoes(RTX, 5, False, 60, False)["game"], "0")

    def test_arquivo_da_partida(self):
        texto = mfg.texto_da_partida({"mfg": "1", "aml_say0": "um # dois"}, 1234, 99)
        self.assertIn("mfg=1\n", texto)
        self.assertIn("hwnd=1234\n", texto)
        self.assertIn("owner=99\n", texto)
        self.assertNotIn("#", texto)
        self.assertTrue(texto.endswith("\n"))

    def test_descrever(self):
        self.assertIn("MSM FG rapido", mfg.descrever(mfg.escolher_opcoes(RADEON, 3, True, 60, False)))
        self.assertIn("rápido", mfg.descrever(mfg.escolher_opcoes(RADEON, 3, True, 60, False), True))
        self.assertIn("DLSS MFG", mfg.descrever(mfg.escolher_opcoes(RTX, 5, False, 60, False)))


@unittest.skipUnless(os.name == "nt", "o MFG Super Motion e' so do Windows")
class Achar(unittest.TestCase):
    def setUp(self):
        self.raiz = tempfile.mkdtemp(prefix="arena_mfg_")
        self.vazia = tempfile.mkdtemp(prefix="arena_mfg_vazia_")

    def tearDown(self):
        limpeza.apagar_pasta(self.raiz)
        limpeza.apagar_pasta(self.vazia)

    def _ambiente(self):
        return mock.patch.dict(os.environ, {"LOCALAPPDATA": self.vazia, "ProgramFiles": self.vazia,
                                            "ProgramFiles(x86)": self.vazia})

    def _criar(self, pasta, com_sinal=True):
        os.makedirs(os.path.join(pasta, "Engine"))
        open(os.path.join(pasta, "Engine", "nvngx.dll"), "wb").close()
        if com_sinal:
            with open(os.path.join(pasta, "Engine", "engine-version.txt"), "w") as arquivo:
                arquivo.write("1.0.5\n")

    def test_acha_na_pasta_emuladores(self):
        self._criar(os.path.join(self.raiz, "emuladores", mfg.PASTA_DO_PROGRAMA))
        with self._ambiente():
            achado = mfg.achar(self.raiz)
        self.assertEqual(achado["origem"], "arena")
        self.assertEqual(achado["versao"], "1.0.5")
        self.assertTrue(achado["motor"].endswith(os.path.join("Engine", "nvngx.dll")))

    def test_acha_o_instalado(self):
        self._criar(os.path.join(self.vazia, "Programs", mfg.PASTA_DO_PROGRAMA))
        with self._ambiente():
            achado = mfg.achar(self.raiz)
        self.assertEqual(achado["origem"], "instalado")

    def test_nvngx_solto_nao_e_o_motor(self):
        # A biblioteca da NVIDIA de algum jogo, sem a tela nem a versao do motor.
        self._criar(os.path.join(self.raiz, "emuladores", mfg.PASTA_DO_PROGRAMA), com_sinal=False)
        with self._ambiente():
            self.assertIsNone(mfg.achar(self.raiz))

    def test_situacao_sem_programa(self):
        with self._ambiente():
            situacao = mfg.situacao(self.raiz)
        self.assertFalse(situacao["achado"])
        self.assertTrue(situacao["pagina"].startswith("https://github.com/NODIX-TECH/"))


if __name__ == "__main__":
    unittest.main()
