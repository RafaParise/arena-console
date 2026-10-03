# -*- coding: utf-8 -*-
"""As capas que o "Buscar capas que faltam" nao achava (Rafael, 02/10/2026:
"funciona muito bem, mas nao com todas"): 11 de 130 na pasta de
desenvolvimento. Cada teste e' um dos casos de verdade, sem internet."""

import os
import shutil
import sys
import tempfile
import unittest
import zipfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

import capas_online  # noqa: E402


class TestEscolherCapa(unittest.TestCase):

    def test_numero_do_disco_nao_e_parte_do_nome(self):
        # Amiga: "Alien Breed_Disk1.adf" e "Top Gear 2 (AGA)_Disk2.adf".
        nomes = ["Alien Breed (Europe)", "Alien Breed 3D (Europe) (AGA)",
                 "Top Gear 2 (Europe)", "Top Gear 2 (Europe) (AGA)"]
        self.assertEqual(capas_online.escolher_capa(nomes, "Alien Breed Disk1", "Alien Breed_Disk1"),
                         "Alien Breed (Europe)")
        # E o "(AGA)" do arquivo escolhe a versao AGA.
        self.assertEqual(capas_online.escolher_capa(nomes, "Top Gear 2 Disk2", "Top Gear 2 (AGA)_Disk2"),
                         "Top Gear 2 (Europe) (AGA)")
        self.assertEqual(capas_online.sem_disco("Final Fantasy VII (Disc 2 of 3)"), "Final Fantasy VII")
        self.assertEqual(capas_online.sem_disco("Sonic CD (Europe)"), "Sonic CD (Europe)")
        self.assertEqual(capas_online.sem_disco("Alien Breed CD32"), "Alien Breed CD32")

    def test_todas_as_palavras_num_jogo_so_do_banco(self):
        # Satellaview: o nome do banco tem o "Dai-1-shuu" no meio.
        nomes = ["BS F-Zero Grand Prix - Dai-1-shuu - Knight League (Japan) (BS SoundLink)",
                 "BS F-Zero Grand Prix - Dai-3-shuu - King League (Japan) (SoundLink)",
                 "BS F-Zero Grand Prix - Dai-4-shuu - Ace League (Japan) (SoundLink)"]
        self.assertEqual(capas_online.escolher_capa(nomes, "BS F ZERO Grand Prix Knight League",
                                                    "BS F-ZERO Grand Prix Knight League (J)"), nomes[0])
        # Mais de um jogo do banco serve: nenhum (nao chuta).
        self.assertIsNone(capas_online.escolher_capa(nomes, "BS F ZERO", "BS F-ZERO (J)"))

    def test_numero_a_mais_nao_vale_em_titulo_curto(self):
        # "Donkey Kong Country" nunca pega a capa do 2 (nem do 3).
        nomes = ["Donkey Kong Country 2 - Diddy's Kong Quest (USA)"]
        self.assertIsNone(capas_online.escolher_capa(nomes, "Donkey Kong Country", "Donkey Kong Country (U)"))
        self.assertIsNone(capas_online.escolher_capa(["Crash Bandicoot 3 - Warped (USA)"],
                                                     "Crash Bandicoot", "Crash Bandicoot (USA)"))

    def test_lista_de_cada_tipo_tem_arquivo_proprio(self):
        pasta = tempfile.mkdtemp(prefix="arena_capas_listas_")
        antiga = capas_online.PASTA_MINIATURAS
        try:
            capas_online.PASTA_MINIATURAS = pasta
            os.makedirs(os.path.join(pasta, "snes"))
            for nome, linha in (("_lista_Nintendo_-_Satellaview.txt", "Caixa (Japan)"),
                                ("_lista_Nintendo_-_Satellaview_Named_Titles.txt", "Titulo (Japan)")):
                with open(os.path.join(pasta, "snes", nome), "w", encoding="utf-8") as f:
                    f.write(linha + "\n")
            self.assertEqual(capas_online.lista_do_banco("snes", "Nintendo_-_Satellaview"), ["Caixa (Japan)"])
            self.assertEqual(capas_online.lista_do_banco("snes", "Nintendo_-_Satellaview", "Named_Titles"),
                             ["Titulo (Japan)"])
        finally:
            capas_online.PASTA_MINIATURAS = antiga
            shutil.rmtree(pasta, ignore_errors=True)

    def test_ps1_na_pasta_do_ps2_avisa(self):
        self.assertIn("ps2", capas_online.OUTRO_CONSOLE)
        repo, recado = capas_online.OUTRO_CONSOLE["ps2"]
        self.assertEqual(repo, "Sony_-_PlayStation")
        self.assertIn("PCSX2 não abre jogo de PS1", recado)


class TestIndiceAchaACapa(unittest.TestCase):
    """O indice: capa com & no nome, nome do GameBase, disco de fliperama."""

    def setUp(self):
        import indexador
        import jogadores
        self.indexador, self.jogadores = indexador, jogadores
        self.dir = tempfile.mkdtemp(prefix="arena_capas_indice_")
        self.antigos = (indexador.PASTA_JOGOS, indexador.PASTA_DADOS, indexador.ARQUIVO_MANIFESTO,
                        jogadores.ARQUIVO, indexador.RAIZ)
        indexador.RAIZ = self.dir
        indexador.PASTA_JOGOS = os.path.join(self.dir, "jogos")
        indexador.PASTA_DADOS = os.path.join(self.dir, "dados")
        indexador.ARQUIVO_MANIFESTO = os.path.join(self.dir, "dados", "manifesto.json")
        jogadores.ARQUIVO = os.path.join(self.dir, "NAO_DEVIA_EXISTIR.txt")
        self.pessoais = os.path.join(indexador.PASTA_JOGOS, "pessoais")

    def tearDown(self):
        (self.indexador.PASTA_JOGOS, self.indexador.PASTA_DADOS, self.indexador.ARQUIVO_MANIFESTO,
         self.jogadores.ARQUIVO, self.indexador.RAIZ) = self.antigos
        shutil.rmtree(self.dir, ignore_errors=True)

    def criar(self, rel, conteudo=b"x"):
        caminho = os.path.join(self.pessoais, rel)
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, "wb") as f:
            f.write(conteudo)
        return caminho

    def miniatura(self, sistema, nome):
        self.criar(os.path.join("..", "..", "retroarch", "thumbnails", sistema, "Named_Boxarts", nome),
                   b"\x89PNG\r\n\x1a\n")

    def jogos(self):
        return {j["titulo"]: j for j in self.indexador.indexar(forcar=True)["jogos"]}

    def test_capa_baixada_com_e_comercial_trocado(self):
        self.criar(os.path.join("Mega Drive", "Sonic & Knuckles + Sonic The Hedgehog 2 (World).md"))
        self.miniatura("megadrive", "Sonic _ Knuckles + Sonic the Hedgehog 2.png")
        jogo = self.jogos()["Sonic & Knuckles + Sonic the Hedgehog 2"]
        self.assertEqual(len(jogo["capas"]), 1)

    def test_nome_do_gamebase_e_capa_com_o_nome_antigo(self):
        pasta = os.path.join("Commodore 64", "INTKARAT")
        self.criar(os.path.join(pasta, "INTKARAT.D64"))
        self.criar(os.path.join(pasta, "VERSION.NFO"),
                   b"GB-Version:        2\r\nFilename:   i\\INTKARAT_03799_02.zip\r\n"
                   b"Unique-ID:         3799\r\nName:              International Karate\r\n")
        self.criar(os.path.join("Commodore 64", "PRINCEOP", "PRINCEOP.CRT"))
        self.criar(os.path.join("Commodore 64", "PRINCEOP", "VERSION.NFO"),
                   b"GB-Version: 1\nName:    Prince of Persia\n")
        self.miniatura("c64", "PRINCEOP.png")             # baixada antes, com o nome antigo
        jogos = self.jogos()
        self.assertIn("International Karate", jogos)
        self.assertEqual(len(jogos["Prince of Persia"]["capas"]), 1)

    def test_nfo_que_nao_e_do_gamebase_nao_muda_o_nome(self):
        pasta = os.path.join("Commodore 64", "Jogo")
        self.criar(os.path.join(pasta, "JOGO.D64"))
        self.criar(os.path.join(pasta, "leia.nfo"), b"Name: Outro Nome\n")
        jogos = self.jogos()
        self.assertIn("Jogo", jogos)
        self.assertNotIn("Outro Nome", jogos)

    def test_zip_dentro_da_pasta_do_disco_vira_um_cartao_com_aviso(self):
        with zipfile.ZipFile(self.criar(os.path.join("Arcade", "kinst", "kinst.zip"), b""), "w") as z:
            z.writestr("ki-l15d.u98", b"x")
        self.criar(os.path.join("Arcade", "kinst", "kinst.chd"), b"MComprHD")
        jogos = [j for j in self.indexador.indexar(forcar=True)["jogos"] if j["plataforma"] == "arcade"]
        self.assertEqual(len(jogos), 1)                 # o disco nao vira outro cartao
        self.assertTrue(jogos[0]["arquivo"].endswith("kinst.zip"))
        texto = " ".join(a["texto"] for a in jogos[0]["avisos"])
        self.assertIn("Tire o kinst.zip dessa pasta e ponha na pasta de cima (Arcade)", texto)


if __name__ == "__main__":
    unittest.main()
