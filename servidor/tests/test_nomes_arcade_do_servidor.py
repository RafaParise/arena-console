# -*- coding: utf-8 -*-
"""No celular nao ha retroarch\\database: o APK leva os bancos pequenos de nomes ao lado do servidor, e o nome de verdade do
jogo de fliperama (Samsho2 -> Samurai Shodown II) sai de la."""
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ = os.path.dirname(PASTA_SERVIDOR)
if PASTA_SERVIDOR not in sys.path:
    sys.path.insert(0, PASTA_SERVIDOR)
sys.path.insert(0, os.path.join(RAIZ, "testes"))

import limpeza  # noqa: E402
import nomes_arcade  # noqa: E402

BANCO = os.path.join(RAIZ, "retroarch", "database", "rdb", "FBNeo - Arcade Games.rdb")


@unittest.skipUnless(os.path.isfile(BANCO), "sem o banco do RetroArch nesta pasta")
class BancoAoLadoDoServidor(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_bancos_de_nomes_")
        shutil.copyfile(BANCO, os.path.join(self.pasta, "FBNeo - Arcade Games.rdb"))

    def tearDown(self):
        limpeza.apagar_pasta(self.pasta)

    def test_acha_o_nome_sem_o_banco_do_retroarch(self):
        with mock.patch.object(nomes_arcade, "PASTA_RDB", os.path.join(self.pasta, "nao_existe")), \
                mock.patch.object(nomes_arcade, "PASTA_RDB_DO_SERVIDOR", self.pasta), \
                mock.patch.dict(nomes_arcade._cache, {}, clear=True), \
                mock.patch.dict(nomes_arcade._nomes, {}, clear=True), \
                mock.patch.dict(nomes_arcade._indices, {}, clear=True), \
                mock.patch.dict(nomes_arcade._consultas, {}, clear=True):
            self.assertIn("Samurai Shodown II", nomes_arcade.nome_do_romset("samsho2.zip", "fbneo"))
            self.assertIn("Metal Slug X", nomes_arcade.nome_do_romset("mslugx.zip", "fbneo"))

    def test_sem_nenhum_dos_dois_bancos_o_nome_fica_vazio(self):
        vazio = os.path.join(self.pasta, "vazio")
        with mock.patch.object(nomes_arcade, "PASTA_RDB", vazio), \
                mock.patch.object(nomes_arcade, "PASTA_RDB_DO_SERVIDOR", vazio), \
                mock.patch.dict(nomes_arcade._cache, {}, clear=True), \
                mock.patch.dict(nomes_arcade._nomes, {}, clear=True):
            self.assertIsNone(nomes_arcade.nome_do_romset("samsho2.zip", "fbneo"))


if __name__ == "__main__":
    unittest.main()
