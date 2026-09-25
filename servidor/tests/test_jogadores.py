# -*- coding: utf-8 -*-
"""Testes do dados\\jogadores.txt do professor (Fase C do multitap):
leitura, escolha do numero por jogo, criacao pre-preenchida e o indice
usando o arquivo. Tudo em pasta temporaria."""

import os
import shutil
import sys
import tempfile
import time
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

import indexador  # noqa: E402
import jogadores  # noqa: E402


class TestArquivoDeJogadores(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="arena_jogadores_teste_")
        self.arquivo = os.path.join(self.dir, "jogadores.txt")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def escrever(self, texto):
        open(self.arquivo, "w", encoding="utf-8").write(texto)

    def test_sem_arquivo_devolve_none(self):
        self.assertIsNone(jogadores.ler(self.arquivo))

    def test_le_ignora_comentario_e_linha_torta(self):
        self.escrever("# comentario\n\nBomberman = 5\nsem igual\nMario Kart = abc\nGoldenEye=4\nX = 999\n")
        self.assertEqual(jogadores.ler(self.arquivo),
                         [("bomberman", 5), ("goldeneye", 4), ("x", jogadores.MAXIMO)])

    def test_nome_inteiro_ganha_de_pedaco(self):
        regras = [("bomberman", 5), ("saturn bomberman", 10), ("super bomberman 4", 4)]
        self.assertEqual(jogadores.numero_do_jogo("Super Bomberman 4", regras), 4)
        self.assertEqual(jogadores.numero_do_jogo("Saturn Bomberman", regras), 10)
        self.assertEqual(jogadores.numero_do_jogo("Bomberman 64", regras), 5)
        self.assertEqual(jogadores.numero_do_jogo("Contra", regras), 2)
        self.assertEqual(jogadores.numero_do_jogo("Contra", []), 2)

    def test_criar_preenche_e_nunca_sobrescreve(self):
        jogos = [{"titulo": "GoldenEye 007", "plataforma_nome": "Nintendo 64", "jogadores_antes": 4},
                 {"titulo": "Contra", "plataforma_nome": "NES", "jogadores_antes": 2},
                 {"titulo": "Contra", "plataforma_nome": "NES", "jogadores_antes": 2}]
        self.assertTrue(jogadores.criar(jogos, self.arquivo))
        self.assertEqual(sorted(jogadores.ler(self.arquivo)), [("contra", 2), ("goldeneye 007", 4)])
        self.escrever("Contra = 1\n")
        self.assertFalse(jogadores.criar(jogos, self.arquivo))
        self.assertEqual(jogadores.ler(self.arquivo), [("contra", 1)])


class TestIndiceUsaOArquivo(unittest.TestCase):
    """O indice cria o arquivo na primeira vez e depois segue o professor."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="arena_jogadores_indice_")
        self._antigos = (indexador.PASTA_JOGOS, indexador.PASTA_DADOS, indexador.ARQUIVO_MANIFESTO,
                         jogadores.ARQUIVO)
        indexador.PASTA_JOGOS = os.path.join(self.dir, "jogos")
        indexador.PASTA_DADOS = os.path.join(self.dir, "dados")
        indexador.ARQUIVO_MANIFESTO = os.path.join(self.dir, "dados", "manifesto.json")
        # Se algo escapar para o caminho padrao, o teste percebe (ver fim).
        jogadores.ARQUIVO = os.path.join(self.dir, "NAO_DEVIA_EXISTIR.txt")
        for pasta, nome in (("Super Nintendo", "Super Bomberman 4 (Japan).sfc"),
                            ("Super Nintendo", "Super Mario Kart (USA).sfc"),
                            ("Nintendo 64", "GoldenEye 007 (USA).z64"),
                            ("GameCube", "Mario Kart Double Dash (USA).rvz")):
            destino = os.path.join(indexador.PASTA_JOGOS, "pessoais", pasta)
            os.makedirs(destino, exist_ok=True)
            open(os.path.join(destino, nome), "wb").close()

    def tearDown(self):
        (indexador.PASTA_JOGOS, indexador.PASTA_DADOS, indexador.ARQUIVO_MANIFESTO,
         jogadores.ARQUIVO) = self._antigos
        shutil.rmtree(self.dir, ignore_errors=True)

    def numeros(self, manifesto):
        return {j["titulo"]: (j["jogadores_do_jogo"], j["jogadores_max"], j["motivo_jogadores"])
                for j in manifesto["jogos"]}

    def test_primeira_vez_cria_com_os_numeros_de_antes(self):
        m = indexador.indexar(forcar=True)
        arquivo = os.path.join(indexador.PASTA_DADOS, "jogadores.txt")
        self.assertTrue(os.path.isfile(arquivo))
        self.assertFalse(os.path.exists(jogadores.ARQUIVO))
        n = self.numeros(m)
        self.assertEqual(n["Super Bomberman 4"][:2], (5, 5))
        self.assertEqual(n["Super Mario Kart"][:2], (2, 2))
        self.assertEqual(n["GoldenEye 007"][:2], (4, 4))
        self.assertIn(("super bomberman 4", 5), jogadores.ler(arquivo))

    def test_mudar_o_arquivo_muda_a_lista_e_passa_pelo_nucleo(self):
        indexador.indexar(forcar=True)
        arquivo = os.path.join(indexador.PASTA_DADOS, "jogadores.txt")
        time.sleep(1.1)  # data do arquivo tem precisao de 1 s no FAT32
        open(arquivo, "w", encoding="utf-8").write(
            "Super Mario Kart = 10\nGoldenEye = 1\nDouble Dash = 4\n")
        m = indexador.indexar(forcar=False)
        self.assertFalse(m.get("reaproveitado"), "mudar o arquivo tem que refazer a lista")
        n = self.numeros(m)
        self.assertEqual(n["Super Mario Kart"][:2], (10, 5))       # SNES para em 5
        self.assertIn("até 5", n["Super Mario Kart"][2])
        self.assertEqual(n["GoldenEye 007"][:2], (1, 1))
        self.assertEqual(n["Super Bomberman 4"][:2], (2, 2))       # nao listado = 2
        # Emulador externo (Dolphin): vale o numero do professor, sem motivo.
        self.assertEqual(n["Mario Kart Double Dash"], (4, 4, ""))


if __name__ == "__main__":
    unittest.main()
