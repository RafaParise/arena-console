# -*- coding: utf-8 -*-
"""Os jogos baixados, levados para a prateleira (servidor/baixados.py,
auditoria 4, 22/10/2026)."""
import os
import sys
import tempfile
import unittest
import zipfile

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(AQUI)), "testes"))
import baixados  # noqa: E402
import limpeza  # noqa: E402

CONSOLES = [
    {"id": "nes", "nome": "Nintendo (NES)", "extensoes": [".nes"], "pasta": "NES"},
    {"id": "snes", "nome": "Super Nintendo", "extensoes": [".sfc", ".zip"], "pasta": "SNES"},
    {"id": "gb", "nome": "Game Boy", "extensoes": [".gb", ".zip"], "pasta": "GB"},
    {"id": "gba", "nome": "Game Boy Advance", "extensoes": [".gba"], "pasta": "GBA"},
]


def criar(caminho, tamanho=1024, dados=None):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "wb") as arquivo:
        arquivo.write(dados if dados is not None else b"\x01" * tamanho)


class Baixados(unittest.TestCase):

    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_baixados_")
        self.download = os.path.realpath(os.path.join(self.pasta, "Download"))
        self.jogos = os.path.join(self.pasta, "ARENA", "jogos")
        criar(os.path.join(self.download, "Mario.nes"))
        criar(os.path.join(self.download, "foto.jpg"))
        criar(os.path.join(self.download, "pequeno.nes"), tamanho=10)
        criar(os.path.join(self.download, "jogos", "Zelda.sfc"))
        criar(os.path.join(self.download, "jogos", "fundo", "Metroid.gba"))
        with zipfile.ZipFile(os.path.join(self.download, "Tetris.zip"), "w") as pacote:
            pacote.writestr("Tetris.gb", b"\x02" * 2048)

    def tearDown(self):
        limpeza.apagar_pasta(self.pasta)

    def test_acha_so_jogos_e_sugere_o_console(self):
        achados = {j["nome"]: j for j in baixados.procurar(CONSOLES, [self.download])}
        self.assertEqual(sorted(achados), ["Mario.nes", "Tetris.zip", "Zelda.sfc"])
        self.assertEqual(achados["Mario.nes"]["sugestao"], "nes")
        self.assertEqual(achados["Zelda.sfc"]["sugestao"], "snes")
        # O .zip serve ao Super Nintendo e ao Game Boy: decide o arquivo de dentro.
        self.assertEqual(achados["Tetris.zip"]["sugestao"], "gb")
        self.assertEqual(sorted(o["id"] for o in achados["Tetris.zip"]["opcoes"]), ["gb", "snes"])

    def test_tamanho_para_gente(self):
        self.assertEqual(baixados.tamanho_legivel(2482), "2 KB")
        self.assertEqual(baixados.tamanho_legivel(100), "1 KB")
        self.assertEqual(baixados.tamanho_legivel(7864320), "7,5 MB")
        self.assertEqual(baixados.tamanho_legivel(1503238554), "1,4 GB")

    def test_leva_para_a_prateleira_certa(self):
        origem = os.path.join(self.download, "Mario.nes")
        destino = baixados.levar(origem, "nes", CONSOLES, self.jogos, [self.download])
        self.assertEqual(destino, os.path.join(self.jogos, "pessoais", "NES", "Mario.nes"))
        self.assertTrue(os.path.isfile(destino))
        self.assertFalse(os.path.exists(origem))

    def test_recusa_o_que_nao_deve(self):
        de_fora = os.path.join(self.pasta, "documento.nes")
        criar(de_fora)
        casos = [
            (de_fora, "nes"),                                              # fora dos downloads
            (os.path.join(self.download, "..", "documento.nes"), "nes"),   # subindo de pasta
            (os.path.join(self.download, "Mario.nes"), "gba"),             # extensao de outro console
            (os.path.join(self.download, "Mario.nes"), "nao-existe"),      # console desconhecido
            (os.path.join(self.download, "sumiu.nes"), "nes"),             # arquivo que nao esta la
        ]
        for caminho, console in casos:
            with self.assertRaises(baixados.NaoPode, msg=(caminho, console)):
                baixados.levar(caminho, console, CONSOLES, self.jogos, [self.download])
        self.assertTrue(os.path.isfile(de_fora))

    def test_nao_apaga_jogo_que_ja_esta_la(self):
        criar(os.path.join(self.jogos, "pessoais", "NES", "Mario.nes"), dados=b"o de antes" * 50)
        with self.assertRaises(baixados.NaoPode):
            baixados.levar(os.path.join(self.download, "Mario.nes"), "nes", CONSOLES, self.jogos, [self.download])
        with open(os.path.join(self.jogos, "pessoais", "NES", "Mario.nes"), "rb") as arquivo:
            self.assertTrue(arquivo.read().startswith(b"o de antes"))
        self.assertTrue(os.path.isfile(os.path.join(self.download, "Mario.nes")))


if __name__ == "__main__":
    unittest.main()
