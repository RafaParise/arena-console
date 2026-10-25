# -*- coding: utf-8 -*-
"""Os testes do Android que mexem a fundo no aparelho (desinstalar o app, Monkey, girar a tela, desligar Wi-Fi e dados,
adb root) so podem rodar no EMULADOR. Achado de 25/10/2026: a rodada final rodou o teste de estresse no celular de
verdade do professor, porque o adb manda o pedido sem '-s' para o unico aparelho ligado. Aqui fica a trava:
  * cada principal() prende o adb ao emulador (ANDROID_SERIAL) antes de ligar qualquer coisa;
  * e confere, depois de ligar, que o aparelho que responde e' um emulador (ro.kernel.qemu = 1)."""
import os
import sys
import unittest
from unittest import mock

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ = os.path.dirname(PASTA_SERVIDOR)
for pasta in (os.path.join(RAIZ, "testes"), os.path.join(RAIZ, "ferramentas")):
    if pasta not in sys.path:
        sys.path.insert(0, pasta)

import teste_android  # noqa: E402

TESTES_DE_EMULADOR = ("teste_android.py", "teste_android_estresse.py")


class OsTestesDoAndroidSoRodamNoEmulador(unittest.TestCase):

    def test_principal_prende_o_adb_ao_emulador_antes_de_ligar(self):
        for nome in TESTES_DE_EMULADOR:
            with open(os.path.join(RAIZ, "testes", nome), encoding="utf-8") as arquivo:
                texto = arquivo.read()
            principal = texto[texto.index("def principal"):]
            antes_de_ligar = principal.split("ligar_emulador()")[0]
            self.assertIn("so_o_emulador()", antes_de_ligar, "%s: falta prender o adb ao emulador antes de ligar" % nome)
            depois = principal.split("ligar_emulador()", 1)[1]
            self.assertIn("conferir_que_e_emulador()", depois.split("adb(")[0] + depois[:400],
                          "%s: falta conferir que o aparelho e' um emulador logo depois de ligar" % nome)

    def test_so_o_emulador_poe_a_variavel_do_adb(self):
        with mock.patch.dict(os.environ, {"ANDROID_SERIAL": "RQ8R2008ADZ"}):
            teste_android.so_o_emulador()
            self.assertEqual(os.environ["ANDROID_SERIAL"], teste_android.SERIE_DO_EMULADOR)
        self.assertTrue(teste_android.SERIE_DO_EMULADOR.startswith("emulator-"))

    def test_celular_de_verdade_para_o_teste(self):
        with mock.patch.object(teste_android, "adb_texto", return_value="\n"):       # celular: ro.kernel.qemu vazio
            with self.assertRaises(SystemExit):
                teste_android.conferir_que_e_emulador()
        with mock.patch.object(teste_android, "adb_texto", return_value="1\n"):
            teste_android.conferir_que_e_emulador()                                 # emulador: passa

    def test_o_emulador_sobe_numa_porta_so_dele(self):
        with open(os.path.join(RAIZ, "testes", "teste_android.py"), encoding="utf-8") as arquivo:
            texto = arquivo.read()
        self.assertIn('"-port"', texto)


if __name__ == "__main__":
    unittest.main()
