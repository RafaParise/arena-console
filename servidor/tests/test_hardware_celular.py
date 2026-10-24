# -*- coding: utf-8 -*-
"""A nota do celular (pedido do Rafael, 24/10/2026: "permita o ARENA atingir o auge dos telefones", e de baixo, o
modo batata): a placa de video de celular pela tabela, e a nota pela velocidade medida e pela memoria.

O aparelho de entrada (Galaxy A12: PowerVR GE8320, 3,7 GB, A53) continua na nota 2; o de ponta chega ao 5."""
import os
import sys
import unittest
from unittest import mock

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PASTA_SERVIDOR not in sys.path:
    sys.path.insert(0, PASTA_SERVIDOR)

import graficos  # noqa: E402
import hardware  # noqa: E402


def celular(gpu, relativa, ram, nucleos=8):
    """O que hardware.resumo() entrega no Android (so o que a nota usa)."""
    return {"android": True, "nucleos": nucleos, "ram_total_gb": ram, "driver_video": "gl",
            "disco": {"classe": "rapido"}, "velocidade": {"relativa_ao_alvo": relativa},
            "gpu": {"nome": gpu, "integrada": True, "conhecida": True}, "cpu": "Qualcomm SM8550"}


class PlacasDeCelular(unittest.TestCase):

    def test_a_tabela_por_familia_e_geracao(self):
        esperado = {
            "PowerVR Rogue GE8320": 2, "PowerVR GE8322": 2, "PowerVR GM9446": 3,
            "Adreno (TM) 505": 2, "Adreno (TM) 610": 2, "Adreno (TM) 619": 3, "Adreno (TM) 630": 3,
            "Adreno (TM) 642L": 4, "Adreno (TM) 650": 4, "Adreno (TM) 710": 4, "Adreno (TM) 740": 5,
            "Adreno (TM) 830": 5, "Adreno (TM) 702": 3,
            "Mali-G31": 2, "Mali-G52 MC2": 2, "Mali-G57 MC2": 3, "Mali-G610 MC6": 3, "Mali-G78 MP14": 4,
            "Mali-G710 MC10": 4, "Immortalis-G715": 5, "Mali-G720": 5, "Mali-T830": 1,
            "Samsung Xclipse 940": 5,
        }
        for nome, nota in esperado.items():
            with self.subTest(nome=nome):
                self.assertEqual(hardware.nota_da_placa_de_celular(nome), nota)

    def test_placa_que_a_tabela_nao_conhece(self):
        for nome in ("", None, "llvmpipe (LLVM 15)", "Android Emulator OpenGL ES Translator (NVIDIA GeForce)",
                     "placa de video desconhecida"):
            with self.subTest(nome=nome):
                self.assertIsNone(hardware.nota_da_placa_de_celular(nome))

    def test_o_teto_da_placa_no_android_e_no_pc(self):
        gpu = {"nome": "Adreno (TM) 740", "integrada": True}
        with mock.patch.object(hardware, "NO_ANDROID", True):
            self.assertEqual(hardware.teto_da_placa(gpu), 5)
            self.assertEqual(hardware.teto_da_placa({"nome": "Placa nova", "integrada": True}), 3)   # nao conhece: 3
        with mock.patch.object(hardware, "NO_ANDROID", False):
            self.assertEqual(hardware.teto_da_placa(gpu), 3)       # no PC a integrada continua no 3


class NotaDoCelular(unittest.TestCase):

    def capacidade(self, **dados):
        with mock.patch.object(hardware, "NO_ANDROID", True):
            return hardware.capacidade(celular(**dados))

    def test_o_aparelho_de_entrada_fica_no_2(self):
        # o Galaxy A12 do Rafael: PowerVR GE8320, 3,7 GB, Cortex-A53
        c = self.capacidade(gpu="PowerVR Rogue GE8320", relativa=0.5, ram=3.7)
        self.assertEqual((c["nota"], c["nota_gpu"]), (2, 2))

    def test_o_aparelho_de_ponta_chega_ao_5(self):
        c = self.capacidade(gpu="Adreno (TM) 740", relativa=3.0, ram=12.0)
        self.assertEqual((c["nota"], c["nota_gpu"]), (5, 5))

    def test_a_placa_fraca_segura_a_nota_da_imagem_mas_nao_a_do_resto(self):
        c = self.capacidade(gpu="Mali-G52 MC2", relativa=2.5, ram=8.0)
        self.assertEqual((c["nota"], c["nota_gpu"]), (5, 2))

    def test_placa_desconhecida_fica_no_3(self):
        c = self.capacidade(gpu="Placa Nova 9000", relativa=3.0, ram=12.0)
        self.assertEqual((c["nota"], c["nota_gpu"]), (5, 3))

    def test_a_memoria_pouca_segura_o_aparelho(self):
        self.assertEqual(self.capacidade(gpu="Adreno (TM) 740", relativa=3.0, ram=2.0)["nota"], 2)
        self.assertEqual(self.capacidade(gpu="Adreno (TM) 740", relativa=3.0, ram=4.0)["nota"], 3)
        self.assertEqual(self.capacidade(gpu="Adreno (TM) 740", relativa=3.0, ram=6.0)["nota"], 4)

    def test_a_velocidade_medida_manda_nos_degraus(self):
        notas = [self.capacidade(gpu="Adreno (TM) 740", relativa=r, ram=12.0)["nota"] for r in (0.9, 1.2, 2.0, 2.3)]
        self.assertEqual(notas, [2, 3, 4, 5])

    def test_o_pc_nao_mudou(self):
        info = celular("Adreno (TM) 740", 3.0, 12.0)
        info["android"] = False
        with mock.patch.object(hardware, "NO_ANDROID", False):
            c = hardware.capacidade(info)
        self.assertEqual(c["nota_gpu"], min(c["nota"], 3))         # integrada: 3, como sempre


class Ladeira(unittest.TestCase):
    """O que a escada grafica faz nas notas altas no Android."""

    def test_o_n64_nao_pede_o_parallel_rdp_no_android(self):
        com = graficos.opcoes_finais_do_nucleo("mupen64plus_next", 5, 5)
        self.assertEqual(com.get("mupen64plus-rdp-plugin"), "parallel")                # no PC vale
        with mock.patch.object(graficos.plataforma_do_sistema, "ANDROID", True):
            sem = graficos.opcoes_finais_do_nucleo("mupen64plus_next", 5, 5)
        self.assertEqual(sem.get("mupen64plus-rdp-plugin"), "gliden64")                # no Android, o video e GL

    def test_o_ps2_do_android_sobe_com_a_nota_da_placa(self):
        up = {n: graficos.opcoes_finais_do_nucleo("armsx2", n, n)["armsx2_upscale"] for n in (1, 2, 3, 4, 5)}
        self.assertEqual(up, {1: "1x", 2: "1x", 3: "2x", 4: "3x", 5: "4x"})
        modesto = graficos.opcoes_finais_do_nucleo("armsx2", 5, 5, modesto=True)
        self.assertEqual(modesto["armsx2_upscale"], "1x")                             # modo batata: o console original
        minimo = graficos.opcoes_finais_do_nucleo("armsx2", 5, 5, abaixo="minimo")
        self.assertEqual(minimo["armsx2_ee_cycle_skip"], "moderate")                  # abaixo do original

    def test_o_padrao_do_ini_do_ps2_tem_a_pre_carga_parcial(self):
        # medido no A12: com a completa, o filme de abertura ia a 5-9 quadros; com a parcial, a ~54
        self.assertEqual(graficos.ini_padrao_do_armsx2("OpenGL")["EmuCore/GS"]["texture_preloading"], "1")
        self.assertEqual(graficos.ini_padrao_do_armsx2("Vulkan")["EmuCore/GS"]["texture_preloading"], "1")


if __name__ == "__main__":
    unittest.main()
