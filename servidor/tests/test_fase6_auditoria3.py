# -*- coding: utf-8 -*-
"""Auditoria 3, Fase 6 (docs\\RELATORIO-QUALIDADE.md): pen drive em FAT32.

O FAT32 nao guarda arquivo maior que 4 GB (menos 1 byte). Antes, so o
VERIFICAR.bat avisava -- e o aluno quase nunca roda. Agora:
  - o "Como colocar jogos" marca os consoles de jogo grande (DVD, Blu-ray)
    e a tela avisa ANTES de copiar, se o ARENA esta num disco FAT32;
  - o cartao do jogo cortado exatamente no limite explica o que houve.
"""
import os
import shutil
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

import arena  # noqa: E402
import como_colocar  # noqa: E402
import indexador  # noqa: E402


class TestFat32(unittest.TestCase):

    def test_jogo_cortado_no_limite_do_fat32_tem_aviso(self):
        aviso = indexador.aviso_de_arquivo_cortado(4 * 1024 ** 3 - 1)
        self.assertIsNotNone(aviso)
        self.assertIn("FAT32", aviso["texto"])
        self.assertIn("exFAT", aviso["texto"])

    def test_outros_tamanhos_nao_tem_aviso(self):
        for tamanho in (0, 4 * 1024 ** 3 - 2, 4 * 1024 ** 3, 5 * 1024 ** 3, 700 * 1024 ** 2):
            self.assertIsNone(indexador.aviso_de_arquivo_cortado(tamanho), tamanho)

    def test_consoles_de_jogo_grande_vem_marcados(self):
        pasta = tempfile.mkdtemp(prefix="arena_fat32_teste_")
        try:
            guia = {c["id"]: c for c in como_colocar.guia(arena.carregar_catalogo(), pasta, pasta,
                                                           {"ps2": "", "ps3": ""})}
        finally:
            shutil.rmtree(pasta, ignore_errors=True)
        for console in ("ps2", "ps3", "wii", "xbox360"):
            self.assertTrue(guia[console]["jogo_grande"], console)
        for console in ("snes", "ps1", "megadrive", "gamecube", "psp"):
            if console in guia:
                self.assertFalse(guia[console]["jogo_grande"], console)


if __name__ == "__main__":
    unittest.main()
