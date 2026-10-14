# -*- coding: utf-8 -*-
"""PS1 sem BIOS (pedido do Rafael, 14/10/2026: rodar sem baixar BIOS onde
der). Sem a BIOS da Sony, o jogo abre pelo PCSX ReARMed, que imita a BIOS
(o CTR abriu assim, com a pasta de sistema vazia). Aqui: a deteccao da BIOS,
o aviso do cartao, o catalogo e o consoles.json. A BIOS de teste e' falsa:
so os 512 KB e a frase que a BIOS de verdade tem."""
import json
import os
import shutil
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)
import bios  # noqa: E402
import bios_catalogo  # noqa: E402

TAMANHO_PS1 = 524288


class TestPs1SemBios(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_ps1_sem_bios_")

    def tearDown(self):
        shutil.rmtree(self.pasta)

    def gravar(self, nome, conteudo):
        with open(os.path.join(self.pasta, nome), "wb") as f:
            f.write(conteudo)

    def test_pasta_sem_bios_abre_pelo_nucleo_que_imita(self):
        self.assertFalse(bios.tem_bios_de_ps1(self.pasta))
        self.assertFalse(bios.tem_a_bios("ps1", self.pasta))
        aviso = bios.aviso_do_jogo("ps1", "CTR - Crash Team Racing (USA).cue", self.pasta)
        self.assertIn("PCSX ReARMed", aviso)
        self.assertIn("BIOS\\PS1", aviso)

    def test_bios_de_ps1_reconhecida_pelo_conteudo(self):
        frase = b"System ROM Version 2.2 12/04/95 A"
        conteudo = b"\0" * 1000 + frase
        self.gravar("qualquer_nome.bin", conteudo + b"\0" * (TAMANHO_PS1 - len(conteudo)))
        self.assertTrue(bios.tem_bios_de_ps1(self.pasta))
        self.assertTrue(bios.tem_a_bios("ps1", self.pasta))
        self.assertIsNone(bios.aviso_do_jogo("ps1", "CTR - Crash Team Racing (USA).cue", self.pasta))

    def test_arquivo_do_tamanho_certo_sem_a_frase_nao_vale(self):
        self.gravar("scph1001.bin", b"\x55" * TAMANHO_PS1)
        self.assertFalse(bios.tem_bios_de_ps1(self.pasta))

    def test_catalogo_e_consoles(self):
        entradas = [e for e in bios_catalogo.CATALOGO if e["console"] == "ps1"]
        self.assertEqual(len(entradas), 3)
        for entrada in entradas:
            self.assertEqual(entrada["nivel"], "alguns")      # abre sem ela
            self.assertIn("PCSX ReARMed", entrada["sem_ela"])
        consoles = json.load(open(os.path.join(RAIZ, "consoles.json"), encoding="utf-8"))
        lista = consoles if isinstance(consoles, list) else (consoles.get("plataformas") or consoles.get("consoles"))
        ps1 = next(p for p in lista if p.get("id") == "ps1")
        self.assertEqual(ps1["core_sem_bios"], "pcsx_rearmed_libretro.dll")
        self.assertTrue(ps1["sem_bios_aviso"])


if __name__ == "__main__":
    unittest.main()
