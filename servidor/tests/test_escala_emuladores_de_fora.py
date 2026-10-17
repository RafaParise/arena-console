# -*- coding: utf-8 -*-
"""Escala da tela nos emuladores de fora (item 10, 17/10/2026).

Jogo desenhado no tamanho do console, numa tela maior, e' esticado pelo
filtro que o proprio emulador traz -- o papel do FSR nos nucleos do
RetroArch (servidor\\filtros):
  - PCSX2 (PS2) em 1x: CAS da AMD, "afiar e redimensionar" (CASMode 2);
  - RPCS3 (PS3) ate 100%: FSR da AMD (Output Scaling Mode);
  - Dolphin (GameCube e Wii) em 1x: Catmull-Rom (OutputResampling 4).
Desenhado maior, ou no nivel minimo: sem filtro. Tudo em arquivos de
mentira numa pasta temporaria.
"""
import os
import re
import sys
import tempfile
import unittest

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PASTA_SERVIDOR not in sys.path:
    sys.path.insert(0, PASTA_SERVIDOR)

import graficos  # noqa: E402

PASTA_TESTES = os.path.join(os.path.dirname(PASTA_SERVIDOR), "testes")
if PASTA_TESTES not in sys.path:
    sys.path.insert(0, PASTA_TESTES)
import limpeza  # noqa: E402

YAML_RPCS3 = "\n".join([
    "Video:", "  Renderer: Vulkan", "  Resolution Scale: 150", "  Output Scaling Mode: Bilinear",
    "  Anisotropic Filter Override: 0", "  MSAA: Auto", "  Frame limit: Auto", "  VSync Mode: Disabled",
    "  Relaxed ZCULL Sync: false", "  Accurate ZCULL stats: true",
    "Miscellaneous:", "  Start games in fullscreen mode: false", ""])


class Dolphin(unittest.TestCase):
    def reamostragem(self, **kwargs):
        return graficos.opcoes_de_imagem_dolphin(**kwargs)["GFX.ini"]["Enhancements"]["OutputResampling"]

    def test_1x_catmull_rom_e_maior_sem_filtro(self):
        self.assertEqual(self.reamostragem(nota=4, nota_gpu=3), "4")
        self.assertEqual(self.reamostragem(nota=5, nota_gpu=5), "0")          # 2x
        self.assertEqual(self.reamostragem(nota=4, nota_gpu=3, abaixo="leve"), "4")
        self.assertEqual(self.reamostragem(nota=4, nota_gpu=3, abaixo="minimo"), "0")


class Rpcs3(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_teste_rpcs3_")
        os.makedirs(os.path.join(self.pasta, "config"))
        self.exe = os.path.join(self.pasta, "rpcs3.exe")

    def tearDown(self):
        limpeza.apagar_pasta(self.pasta)

    def modo(self, **kwargs):
        caminho = os.path.join(self.pasta, "config", "config.yml")
        with open(caminho, "w", encoding="utf-8") as arquivo:
            arquivo.write(YAML_RPCS3)
        graficos.escrever_config_rpcs3(self.exe, **kwargs)
        with open(caminho, encoding="utf-8") as arquivo:
            texto = arquivo.read()
        return (re.search(r"^  Resolution Scale: (\d+)$", texto, re.M).group(1),
                re.search(r"^  Output Scaling Mode: (.+)$", texto, re.M).group(1))

    def test_ate_720p_fsr(self):
        self.assertEqual(self.modo(nota=4, nota_gpu=3), ("100", "FidelityFX Super Resolution"))
        self.assertEqual(self.modo(nota=4, nota_gpu=3, abaixo="leve"), ("50", "FidelityFX Super Resolution"))

    def test_maior_ou_minimo_bilinear(self):
        self.assertEqual(self.modo(nota=5, nota_gpu=5), ("150", "Bilinear"))
        self.assertEqual(self.modo(nota=4, nota_gpu=3, abaixo="minimo"), ("25", "Bilinear"))


class Pcsx2(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_teste_pcsx2_")
        os.makedirs(os.path.join(self.pasta, "inis"))
        self.exe = os.path.join(self.pasta, "pcsx2-qt.exe")

    def tearDown(self):
        limpeza.apagar_pasta(self.pasta)

    def cas(self, **kwargs):
        caminho = os.path.join(self.pasta, "inis", "PCSX2.ini")
        with open(caminho, "w", encoding="utf-8") as arquivo:
            arquivo.write("[EmuCore/GS]\nupscale_multiplier = 2\nCASMode = 1\n")
        graficos.escrever_config_pcsx2(self.exe, **kwargs)
        with open(caminho, encoding="utf-8") as arquivo:
            texto = arquivo.read()
        return (re.findall(r"^upscale_multiplier = (\d+)", texto, re.M),
                re.findall(r"^CASMode = (\d+)", texto, re.M))

    def test_1x_com_cas(self):
        self.assertEqual(self.cas(nota=4, nota_gpu=3, integrada=True), (["1"], ["2"]))

    def test_maior_ou_minimo_sem_cas(self):
        self.assertEqual(self.cas(nota=5, nota_gpu=5, integrada=False), (["4"], ["0"]))
        self.assertEqual(self.cas(nota=4, nota_gpu=3, integrada=True, abaixo="minimo"), (["1"], ["0"]))


if __name__ == "__main__":
    unittest.main()
