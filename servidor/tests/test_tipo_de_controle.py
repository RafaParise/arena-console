# -*- coding: utf-8 -*-
"""O tipo de controle de cada porta (input_libretro_device_pN) e' um numero do NUCLEO, nao do console.

Achado no A12 em 07/11/2026 (o registro do Saturn dizia "Controller 1: Arcade Racer"): o ARENA mandava 517 a todo
console com analogico. Os numeros abaixo foram lidos dos proprios nucleos (a lista que cada um declara ao RetroArch,
SET_CONTROLLER_INFO) e conferidos abrindo o Beetle Saturn com cada um. Se este teste falhar, confira no nucleo antes
de mudar o numero.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import controles  # noqa: E402


def tipo(console, nucleo=None, analogico=True, extra=None, jogador=1):
    opcoes = controles.opcoes_do_console(console, jogadores=4, usar_analogico=analogico, dispositivo_extra=extra,
                                         nucleo=nucleo)
    return opcoes["input_libretro_device_p%d" % jogador]


class OTipoDeCadaNucleo(unittest.TestCase):
    def test_saturn_3d_control_pad_e_nunca_o_volante(self):
        self.assertEqual(tipo("saturn", "mednafen_saturn"), "261")          # 3D Control Pad (517 = Arcade Racer)
        self.assertEqual(tipo("saturn", "mednafen_saturn", analogico=False), "1")      # Control Pad (513 nao existe)
        self.assertEqual(tipo("saturn", "mednafen_saturn", extra="mouse", jogador=2), "258")

    def test_playstation_dualshock_nos_dois_nucleos(self):
        self.assertEqual(tipo("ps1", "swanstation"), "261")                 # DualShock (517 = Analog Joystick)
        self.assertEqual(tipo("ps1", "pcsx_rearmed"), "517")                # DualShock no PCSX ReARMed (a partida)
        self.assertEqual(tipo("ps1", "swanstation", analogico=False), "1")
        self.assertEqual(tipo("ps1", "pcsx_rearmed", analogico=False), "1")
        self.assertEqual(tipo("ps1", "swanstation", extra="mouse", jogador=2), "258")

    def test_dreamcast_o_controle_comum(self):
        self.assertEqual(tipo("dreamcast", "flycast"), "1")                 # Controller (517 nao existe; 513 = Twin Stick)
        self.assertEqual(tipo("dreamcast", "flycast", analogico=False), "1")
        self.assertEqual(tipo("dreamcast", "flycast", extra="teclado", jogador=2), "3")

    def test_teclado_do_c64_e_do_amiga(self):
        self.assertEqual(tipo("c64", "vice_x64", extra="teclado", jogador=2), "259")
        self.assertEqual(tipo("amiga", "puae", extra="teclado", jogador=2), "259")

    def test_sem_nucleo_vale_o_do_console(self):
        self.assertEqual(tipo("ps1"), "261")
        self.assertEqual(tipo("snes"), "1")


if __name__ == "__main__":
    unittest.main()
