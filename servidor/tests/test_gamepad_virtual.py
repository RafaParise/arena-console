# -*- coding: utf-8 -*-
"""O gamepad XInput virtual (servidor\\gamepad_virtual.py). A conversao e' testada sempre; o driver de verdade, so se o
ViGEmBus estiver instalado nesta maquina (o teste le o gamepad de volta pelo XInput do Windows)."""
import ctypes
import os
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import gamepad_virtual as gv  # noqa: E402


class AConversao(unittest.TestCase):
    def test_botoes_por_posicao(self):
        r = gv.converter(1 << 0, [0, 0, 0, 0])          # B do RetroPad (embaixo) = A do Xbox
        self.assertEqual(r.botoes, 0x1000)
        self.assertEqual(gv.converter((1 << 4) | (1 << 3), [0, 0, 0, 0]).botoes, 0x0001 | 0x0010)

    def test_gatilhos_e_eixos(self):
        r = gv.converter(1 << 13, [32767, 32767, -32767, 0])
        self.assertEqual((r.gatilho_e, r.gatilho_d), (0, 255))
        self.assertEqual((r.lx, r.ly, r.rx, r.ry), (32767, -32767, -32767, 0))     # o Y se inverte


class ODriverDeVerdade(unittest.TestCase):
    def setUp(self):
        self.pad = gv.GamepadVirtual()
        ok, motivo = self.pad.disponivel()
        if not ok:
            self.skipTest(motivo)

    def test_o_windows_ve_o_gamepad(self):
        xinput = ctypes.WinDLL("xinput1_4.dll")

        class Estado(ctypes.Structure):
            _fields_ = [("pacote", ctypes.c_uint), ("botoes", ctypes.c_ushort), ("lt", ctypes.c_ubyte), ("rt", ctypes.c_ubyte),
                        ("lx", ctypes.c_short), ("ly", ctypes.c_short), ("rx", ctypes.c_short), ("ry", ctypes.c_short)]
        try:
            self.pad.atualizar(1, (1 << 8) | (1 << 7), [20000, -10000, 0, 0])
            achou = None
            for _ in range(100):
                # o Windows demora a enumerar o gamepad novo: o relatorio mandado antes disso se perde (no uso de verdade o
                # celular manda o estado muitas vezes por segundo)
                self.pad.atualizar(1, (1 << 8) | (1 << 7), [20000, -10000, 0, 0])
                for n in range(4):
                    e = Estado()
                    if xinput.XInputGetState(n, ctypes.byref(e)) == 0 and e.botoes & 0x2000:
                        achou = e
                if achou:
                    break
                time.sleep(0.1)
            self.assertIsNotNone(achou, "o Windows nao enxergou o gamepad virtual")
            self.assertTrue(achou.botoes & 0x0008)           # direita
            self.assertAlmostEqual(achou.lx, 20000, delta=300)
            self.assertAlmostEqual(achou.ly, 10000, delta=300)
        finally:
            self.pad.fechar()


if __name__ == "__main__":
    unittest.main()
