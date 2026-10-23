# -*- coding: utf-8 -*-
"""A ferramenta que instala o ARENA no celular pelo cabo (auditoria 4, 22/10/2026).

O Galaxy A12 do Rafael (Android 12) recusou o APK: "Como o app nao e'
compativel com seu smartphone". O mais provavel e' o Android de 32 bits: o APK
do ARENA so tem arm64-v8a e x86_64. A ferramenta escolhe o APK pelas
arquiteturas do aparelho e, no de 32 bits, abre a versao web.
"""
import os
import sys
import tempfile
import unittest
from unittest import mock

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "ferramentas"))
sys.path.insert(0, os.path.join(RAIZ, "testes"))
import instalar_no_celular as instalar  # noqa: E402
import limpeza  # noqa: E402


def aparelho(abis, abis64=()):
    return {"abis": list(abis), "abis64": list(abis64)}


class Arquitetura(unittest.TestCase):
    def test_celular_de_32_bits_nao_recebe_apk(self):
        # O Android de 32 bits (o caso mais provavel do A12): so armeabi.
        self.assertIsNone(instalar.abi_do_apk(aparelho(["armeabi-v7a", "armeabi"])))

    def test_64_bits(self):
        self.assertEqual(instalar.abi_do_apk(aparelho(["arm64-v8a", "armeabi-v7a", "armeabi"], ["arm64-v8a"])),
                         "arm64-v8a")
        self.assertEqual(instalar.abi_do_apk(aparelho(["x86_64", "arm64-v8a"], ["x86_64", "arm64-v8a"])), "x86_64")


class OQueCopiar(unittest.TestCase):
    def setUp(self):
        self.raiz = tempfile.mkdtemp(prefix="arena_teste_celular_")
        for rel, tamanho in ((os.path.join("BIOS", "PS1", "scph1001.bin"), 512),
                             (os.path.join("retroarch", "saves", "jogo.srm"), 64),
                             (os.path.join("jogos", "pessoais", "SNES", "jogo.sfc"), 128),
                             (os.path.join("jogos", "pessoais", "PS2", "jogo.iso"), 256),
                             (os.path.join("jogos", "pessoais", "Gamecube", "jogo.rvz"), 256)):
            caminho = os.path.join(self.raiz, rel)
            os.makedirs(os.path.dirname(caminho), exist_ok=True)
            with open(caminho, "wb") as arquivo:
                arquivo.write(b"\0" * tamanho)

    def tearDown(self):
        limpeza.apagar_pasta(self.raiz)

    def test_bios_saves_e_jogos_que_o_celular_roda(self):
        with mock.patch.object(instalar, "RAIZ", self.raiz):
            destinos = [d for _o, d, _t in instalar.o_que_copiar()]
            sem_jogos = [d for _o, d, _t in instalar.o_que_copiar(com_jogos=False)]
        self.assertIn("/sdcard/ARENA/BIOS", destinos)
        self.assertIn("/sdcard/ARENA/retroarch/saves", destinos)
        self.assertIn("/sdcard/ARENA/jogos/pessoais/SNES", destinos)
        self.assertNotIn("/sdcard/ARENA/jogos/pessoais/PS2", destinos, "PS2 e' emulador de computador")
        self.assertNotIn("/sdcard/ARENA/jogos/pessoais/Gamecube", destinos)
        self.assertEqual([d for d in sem_jogos if "/jogos/" in d], [])


if __name__ == "__main__":
    unittest.main()
