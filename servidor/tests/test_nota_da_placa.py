# -*- coding: utf-8 -*-
"""Ate que nota a placa de video vai (hardware.teto_da_placa, 17/10/2026).

- Integrada comum: 3.
- Ryzen de mesa com Vega (serie G e GE) e Ryzen 8000G: 4 nos nucleos do
  RetroArch. Medido no Ryzen 5 5600G (ferramentas\\medir_escala.py
  --nota-placa=4, docs\\escala_nota4_bruto.json): PS1 53,6% da placa, PSP
  16,6%, N64 10,0%, Dreamcast 12,2%, todos a 60 quadros.
- Os emuladores de fora ficam no 3 em toda integrada (nota_gpu_de_fora): com
  a nota 4, o PCSX2 desenharia o PS2 em 4x e o RPCS3 o PS3 a 150%, e isso
  nao foi medido.
- Dedicada antiga e fraca (GeForce 210, GT 710, Radeon HD 5450...): 2.
"""
import os
import sys
import unittest

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PASTA_SERVIDOR not in sys.path:
    sys.path.insert(0, PASTA_SERVIDOR)

import hardware  # noqa: E402

INTEGRADA_AMD = {"nome": "AMD Radeon(TM) Graphics", "integrada": True}


def maquina(gpu, cpu, nucleos=12, ram=16.0):
    return {"nucleos": nucleos, "ram_total_gb": ram, "driver_video": "vulkan",
            "disco": {"classe": "muito_rapido"}, "gpu": gpu, "cpu": cpu}


class Teto(unittest.TestCase):
    def test_casos(self):
        casos = [
            (INTEGRADA_AMD, "AMD Ryzen 5 5600G with Radeon Graphics", 4),
            (INTEGRADA_AMD, "AMD Ryzen 7 5700GE with Radeon Graphics", 4),
            (INTEGRADA_AMD, "AMD Ryzen 5 PRO 4650G with Radeon Graphics", 4),
            ({"nome": "AMD Radeon 780M Graphics", "integrada": True}, "AMD Ryzen 7 8700G w/ Radeon 780M Graphics", 4),
            (INTEGRADA_AMD, "AMD Ryzen 7 5700U with Radeon Graphics", 3),     # notebook: nao medido
            (INTEGRADA_AMD, "AMD Ryzen 5 7600 6-Core Processor", 3),          # a de 2 nucleos de video
            ({"nome": "Intel(R) UHD Graphics", "integrada": True}, "Intel(R) Celeron(R) N5100 @ 1.10GHz", 3),
            ({"nome": "NVIDIA GeForce 210", "integrada": False}, "Intel(R) Core(TM) i5", 2),
            ({"nome": "NVIDIA GeForce GT 710", "integrada": False}, "x", 2),
            ({"nome": "AMD Radeon HD 5450", "integrada": False}, "x", 2),
            ({"nome": "NVIDIA GeForce GTX 1050 Ti", "integrada": False}, "x", 5),
            ({"nome": "NVIDIA GeForce RTX 3060", "integrada": False}, "x", 5),
        ]
        for gpu, cpu, esperado in casos:
            with self.subTest(gpu=gpu["nome"], cpu=cpu):
                self.assertEqual(hardware.teto_da_placa(gpu, cpu), esperado)


class Capacidade(unittest.TestCase):
    def test_apu_de_mesa_4_nos_nucleos_3_nos_de_fora(self):
        # Como o Ryzen 5 5600G do professor: 12 nucleos logicos e 11,8 GB.
        nota = hardware.capacidade(maquina(INTEGRADA_AMD, "AMD Ryzen 5 5600G with Radeon Graphics",
                                           ram=11.8))
        self.assertEqual((nota["nota"], nota["nota_gpu"], nota["nota_gpu_de_fora"]), (4, 4, 3))

    def test_celeron_continua_igual(self):
        celeron = maquina({"nome": "Intel(R) UHD Graphics", "integrada": True},
                          "Intel(R) Celeron(R) N5100 @ 1.10GHz", nucleos=4, ram=7.7)
        nota = hardware.capacidade(celeron)
        self.assertEqual((nota["nota_gpu"], nota["nota_gpu_de_fora"]), (3, 3))

    def test_dedicada_boa_igual_nos_dois(self):
        nota = hardware.capacidade(maquina({"nome": "NVIDIA GeForce RTX 3060", "integrada": False}, "x"))
        self.assertEqual(nota["nota_gpu"], nota["nota_gpu_de_fora"])
        self.assertEqual(nota["nota_gpu"], nota["nota"])


if __name__ == "__main__":
    unittest.main()
