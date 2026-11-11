# -*- coding: utf-8 -*-
"""O painel do driver da placa (servidor\\driver_video.py): decodificar, interpretar e alinhar."""
import os
import sys
import unittest

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PASTA_SERVIDOR not in sys.path:
    sys.path.insert(0, PASTA_SERVIDOR)
import driver_video  # noqa: E402

# O PC do Rafael em 11/11/2026 (lido do registro).
DO_RAFAEL = {"VSyncControl": "3", "TFQ": "2", "Tessellation_OPTION": "0", "Tessellation": "64", "AnisoType": "0",
             "AntiAlias": "1", "TurboSync": "0", "ShaderCache": "1", "AntiStuttering": "1",
             "KMD_DeLagEnabled": 0, "KMD_USUEnable": 0, "KMD_USUSharpeningDegree": 1050253722,
             "KMD_FRTEnabled": 1, "KMD_MaxFrameRateRequested": 60, "painel_versao": "23.19.25.01", "DvrEnabled": 0}


class Decodificar(unittest.TestCase):
    def test_texto_utf16_dos_valores_da_umd(self):
        self.assertEqual(driver_video.texto_utf16(b"3\x00"), "3")
        self.assertEqual(driver_video.texto_utf16(b"6\x004\x00\x00\x00"), "64")
        self.assertEqual(driver_video.texto_utf16("2"), "2")
        self.assertEqual(driver_video.texto_utf16(None), "")

    def test_float_nos_4_bytes(self):
        self.assertEqual(driver_video.float_de_dword(1050253722), 0.3)
        self.assertIsNone(driver_video.float_de_dword("x"))

    def test_fabricante(self):
        self.assertEqual(driver_video.fabricante_do_provedor("Advanced Micro Devices, Inc."), "amd")
        self.assertEqual(driver_video.fabricante_do_provedor("Intel Corporation"), "intel")
        self.assertEqual(driver_video.fabricante_do_provedor("NVIDIA"), "nvidia")
        self.assertEqual(driver_video.fabricante_do_provedor("MikeTheTech"), "")


class Interpretar(unittest.TestCase):
    def por_chave(self, itens):
        return {i["chave"]: i for i in itens}

    def test_o_pc_do_rafael(self):
        itens = self.por_chave(driver_video.interpretar_amd(DO_RAFAEL, 60))
        self.assertEqual(itens["vsync"]["valor"], "sempre ligado")
        self.assertTrue(itens["vsync"]["certo"])
        # A textura em "desempenho" e' o unico que vale mudar a mao.
        self.assertEqual(itens["textura"]["valor"], "desempenho")
        self.assertFalse(itens["textura"]["certo"])
        self.assertIn("Padrão", itens["textura"]["mude"])
        self.assertEqual(itens["rsr"]["valor"], "desligado")
        self.assertEqual(itens["limite"]["valor"], "ligado, 60 quadros por segundo")
        self.assertTrue(itens["limite"]["certo"])            # igual a tela: nao corta nada
        self.assertEqual(itens["gravacao"]["valor"], "desligada")
        self.assertEqual([i for i in itens.values() if not i["certo"]], [itens["textura"]])

    def test_limite_menor_que_a_tela(self):
        itens = self.por_chave(driver_video.interpretar_amd(DO_RAFAEL, 144))
        self.assertFalse(itens["limite"]["certo"])
        self.assertIn("144", itens["limite"]["mude"])

    def test_rsr_e_filtros_forcados(self):
        brutos = dict(DO_RAFAEL, KMD_USUEnable=1, AnisoType="1", TFQ="1", DvrEnabled=1)
        itens = self.por_chave(driver_video.interpretar_amd(brutos, 60))
        self.assertEqual(itens["rsr"]["valor"], "ligado, nitidez 0.3")
        self.assertFalse(itens["rsr"]["certo"])
        self.assertFalse(itens["filtros"]["certo"])
        self.assertTrue(itens["textura"]["certo"])
        self.assertFalse(itens["gravacao"]["certo"])

    def test_sem_valores(self):
        itens = driver_video.interpretar_amd({}, 60)
        self.assertTrue(itens)
        self.assertTrue(all("bruto" in i and "efeito" in i for i in itens))


class Alinhar(unittest.TestCase):
    def test_hz_efetivo(self):
        self.assertEqual(driver_video.hz_efetivo(144, {"hz_limite": 60}), 60)
        self.assertEqual(driver_video.hz_efetivo(60, {"hz_limite": 60}), 60)
        self.assertEqual(driver_video.hz_efetivo(144, {"hz_limite": None}), 144)
        self.assertEqual(driver_video.hz_efetivo(144, None), 144)

    def test_escala_com_o_rsr(self):
        com = {"rsr": True}
        self.assertEqual(driver_video.escala_com_o_driver("nitido", com), "rcas")
        self.assertEqual(driver_video.escala_com_o_driver("catmull", com), "rcas")
        self.assertEqual(driver_video.escala_com_o_driver("pixel", com), "pixel")
        self.assertEqual(driver_video.escala_com_o_driver("", com), "")
        self.assertEqual(driver_video.escala_com_o_driver("nitido", {"rsr": False}), "nitido")


class Android(unittest.TestCase):
    # O Galaxy A12 em 11/11/2026 (o que o app conta e o que o getprop e o /sys dizem).
    A12 = {"placa_de_video": "PowerVR Rogue GE8320", "opengl_es": "3.2", "vulkan": True, "vulkan_versao": "1.1",
           "tela_hz": 60, "tela_modos_hz": [60], "animacoes": [0.0, 0.0, 0.0], "hz_escolhido_max": 0.0,
           "economia": False}
    PROPS = {"ro.hardware.egl": "meow", "ro.opengles.version": "196610", "ro.gfx.driver.0": "",
             "ro.hardware.vulkan": "", "debug.egl.force_msaa": ""}

    def por_chave(self, itens):
        return {i["chave"]: i for i in itens}

    def test_versao_do_gles(self):
        self.assertEqual(driver_video.versao_do_gles("196610"), "3.2")
        self.assertEqual(driver_video.versao_do_gles("196608"), "3.0")
        self.assertEqual(driver_video.versao_do_gles(""), "")

    def test_o_a12_esta_todo_certo(self):
        itens = self.por_chave(driver_video.itens_android(self.A12, self.PROPS, "PowerVR Rogue GE8320",
                                                          "Default", "680000", "0"))
        self.assertEqual([c for c, i in itens.items() if not i["certo"]], [])
        self.assertIn("PowerVR Rogue GE8320", itens["driver"]["valor"])
        self.assertIn("veio com o Android", itens["driver"]["valor"])
        self.assertEqual(itens["motor"]["valor"], "OpenGL ES 3.2 · Vulkan 1.1")
        self.assertEqual(itens["msaa"]["valor"], "desligado")
        self.assertEqual(itens["animacoes"]["valor"], "0×0×0")
        self.assertIn("até 680 MHz", itens["clock"]["valor"])

    def test_o_que_vale_mudar(self):
        aparelho = dict(self.A12, economia=True, tela_hz=60, tela_modos_hz=[60, 90], animacoes=[1.5, 1.5, 1.5])
        props = dict(self.PROPS, **{"debug.egl.force_msaa": "1", "ro.gfx.driver.0": "com.google.android.gpu"})
        itens = self.por_chave(driver_video.itens_android(aparelho, props))
        self.assertEqual(sorted(c for c, i in itens.items() if not i["certo"]), ["animacoes", "economia", "hz", "msaa"])
        self.assertIn("Play Store", itens["driver"]["valor"])
        self.assertIn("aceita até 90", itens["hz"]["valor"])
        self.assertIn("Forçar MSAA 4x", itens["msaa"]["mude"])
        self.assertIn("Desligada", itens["economia"]["mude"])

    def test_sem_nada_do_app(self):
        itens = driver_video.itens_android({}, {})
        self.assertTrue(all("valor" in i for i in itens))
        self.assertNotIn("animacoes", [i["chave"] for i in itens])


@unittest.skipUnless(os.name == "nt", "o registro do Windows")
class NestaMaquina(unittest.TestCase):
    def test_situacao_roda_e_tem_a_forma(self):
        driver_video._CACHE.clear()
        s = driver_video.situacao("", 60)
        for chave in ("fabricante", "placa", "driver", "painel", "itens", "le_as_opcoes", "hz_limite", "rsr"):
            self.assertIn(chave, s)
        if s["fabricante"] == "amd":
            self.assertTrue(s["le_as_opcoes"])
            self.assertTrue(s["itens"])
        # A segunda leitura vem do cache (mesmo objeto).
        self.assertIs(driver_video.situacao("", 60), s)


if __name__ == "__main__":
    unittest.main()
