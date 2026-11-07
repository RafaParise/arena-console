# -*- coding: utf-8 -*-
"""O celular vibra como o controle (pedido do Rafael, 07/11/2026): plataforma.ajustes_do_android."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import plataforma  # noqa: E402


class AVibracaoDoCelular(unittest.TestCase):
    def opcoes(self, **chaves):
        opcoes = {}
        plataforma.ajustes_do_android(opcoes, "pasta-que-nao-existe", "", **chaves)
        return opcoes

    def test_desligada_por_padrao(self):
        o = self.opcoes()
        self.assertEqual((o["enable_device_vibration"], o["vibrate_on_keypress"]), ("false", "false"))

    def test_cada_chave_liga_a_sua(self):
        o = self.opcoes(vibrar_celular=True)
        self.assertEqual((o["enable_device_vibration"], o["vibrate_on_keypress"]), ("true", "false"))
        o = self.opcoes(vibrar_ao_tocar=True)
        self.assertEqual((o["enable_device_vibration"], o["vibrate_on_keypress"]), ("false", "true"))

    def test_a_chave_existe_no_retroarch_desta_pasta(self):
        raiz = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        caminho = os.path.join(raiz, "retroarch", "retroarch.cfg")
        if not os.path.isfile(caminho):
            self.skipTest("sem o retroarch.cfg")
        with open(caminho, encoding="utf-8", errors="replace") as arquivo:
            texto = arquivo.read()
        for chave in ("enable_device_vibration", "vibrate_on_keypress"):
            self.assertIn("\n%s = " % chave, texto)


if __name__ == "__main__":
    unittest.main()
