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


class BuscaAmpliada(unittest.TestCase):
    """10/11/2026: as pastas escolhidas (3 niveis), a pasta do ARENA pulada e as BIOS a parte."""

    def setUp(self):
        self.pasta = os.path.realpath(tempfile.mkdtemp(prefix="arena_busca_"))
        self.download = os.path.join(self.pasta, "Download")
        self.outra = os.path.join(self.pasta, "D", "Jogos")
        self.arena = os.path.join(self.outra, "ARENA")
        os.makedirs(self.download)
        criar(os.path.join(self.outra, "nes", "antigos", "fundo", "Contra.nes"))         # 3 niveis abaixo
        criar(os.path.join(self.outra, "a", "b", "c", "d", "Longe.nes"))                 # 4 niveis: fica de fora
        criar(os.path.join(self.arena, "jogos", "NES", "JaNoArena.nes"))                 # a pasta do ARENA: pulada
        criar(os.path.join(self.outra, "Android", "data", "Escondido.nes"))              # pasta do sistema: pulada
        criar(os.path.join(self.outra, "neogeo.zip"), tamanho=2048)                      # a BIOS do Neo Geo
        self.bios = os.path.join(self.pasta, "ARENA-BIOS")

    def tearDown(self):
        limpeza.apagar_pasta(self.pasta)

    def procurar(self):
        bios_achadas = []
        jogos = baixados.procurar(CONSOLES, [self.download], escolhidas=[self.outra], ignorar=[self.arena],
                                  bios_achadas=bios_achadas)
        return {j["nome"] for j in jogos}, bios_achadas

    def test_acha_na_pasta_escolhida_ate_tres_niveis(self):
        nomes, _ = self.procurar()
        self.assertIn("Contra.nes", nomes)
        self.assertNotIn("Longe.nes", nomes)

    def test_pula_a_pasta_do_arena_e_as_do_sistema(self):
        nomes, _ = self.procurar()
        self.assertNotIn("JaNoArena.nes", nomes)
        self.assertNotIn("Escondido.nes", nomes)

    def test_a_bios_do_neo_geo_vem_a_parte(self):
        nomes, bios_achadas = self.procurar()
        self.assertEqual([b["bios"] for b in bios_achadas], ["neogeo.zip"])
        self.assertNotIn("neogeo.zip", nomes)

    def test_levar_a_bios_nao_apaga_a_que_ja_esta_la(self):
        criar(os.path.join(self.bios, "neogeo.zip"), dados=b"a de antes" * 10)
        destino = baixados.levar_bios(os.path.join(self.outra, "neogeo.zip"), self.bios, [self.outra])
        self.assertEqual(os.path.basename(destino), "neogeo (2).zip")
        with open(os.path.join(self.bios, "neogeo.zip"), "rb") as arquivo:
            self.assertTrue(arquivo.read().startswith(b"a de antes"))
        self.assertFalse(os.path.exists(os.path.join(self.outra, "neogeo.zip")))

    def test_so_move_de_onde_procurou(self):
        with self.assertRaises(baixados.NaoPode):
            baixados.levar_bios(os.path.join(self.outra, "neogeo.zip"), self.bios, [self.download])
        with self.assertRaises(baixados.NaoPode):
            baixados.levar(os.path.join(self.outra, "nes", "antigos", "fundo", "Contra.nes"), "nes", CONSOLES,
                           os.path.join(self.pasta, "jogos"), [self.download])

    def test_conferir_pasta_escolhida(self):
        self.assertEqual(baixados.conferir_pasta_escolhida(self.outra, os.path.join(self.pasta, "X")), self.outra)
        with self.assertRaises(baixados.NaoPode):
            baixados.conferir_pasta_escolhida(os.path.join(self.pasta, "nao-existe"), self.pasta)
        with self.assertRaises(baixados.NaoPode):
            baixados.conferir_pasta_escolhida(self.arena, self.arena)        # a pasta do proprio ARENA
        with self.assertRaises(baixados.NaoPode):
            baixados.conferir_pasta_escolhida("", self.pasta)


class ReconhecerBios(unittest.TestCase):
    """bios.reconhecer_arquivo_solto: pela marca (md5 da nota do .info), pelo nome, ou nada."""

    def setUp(self):
        import hashlib
        import bios
        self.bios = bios
        self.pasta = os.path.realpath(tempfile.mkdtemp(prefix="arena_bios_solta_"))
        self.info = os.path.join(self.pasta, "info")
        conteudo = b"BIOS DE TESTE" * 100
        marca = hashlib.md5(conteudo).hexdigest()
        criar(os.path.join(self.info, "teste_libretro.info"),
              dados=('notes = "(!) bios_teste.bin (md5): %s"\n' % marca).encode())
        criar(os.path.join(self.pasta, "baixou_com_outro_nome.bin"), dados=conteudo)     # nome sem cara de BIOS
        criar(os.path.join(self.pasta, "bios do console.bin"), dados=conteudo)           # cara de BIOS e marca certa
        criar(os.path.join(self.pasta, "bios_teste.bin"), dados=b"outra versao" * 50)   # nome certo, marca errada
        criar(os.path.join(self.pasta, "foto bios.jpg"), dados=conteudo)                 # imagem nunca e' BIOS

    def tearDown(self):
        limpeza.apagar_pasta(self.pasta)

    def ver(self, nome):
        return self.bios.reconhecer_arquivo_solto(os.path.join(self.pasta, nome), self.info)

    def test_pela_marca(self):
        self.assertEqual(self.ver("bios do console.bin"), {"bios": "bios_teste.bin", "certeza": "marca"})

    def test_pelo_nome(self):
        self.assertEqual(self.ver("bios_teste.bin"), {"bios": "bios_teste.bin", "certeza": "nome"})

    def test_arquivo_sem_cara_de_bios_nem_e_lido(self):
        self.assertIsNone(self.ver("baixou_com_outro_nome.bin"))
        self.assertIsNone(self.ver("foto bios.jpg"))


if __name__ == "__main__":
    unittest.main()
