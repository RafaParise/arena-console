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


class TestJogosConhecidos(unittest.TestCase):
    """O que o ARENA ja sabe vem com o PROGRAMA (consoles.json ->
    jogadores_por_jogo). Achado de 02/10/2026: o Crash Nitro Kart com 4 so
    existia no dados\\jogadores.txt de quem montou; na versao dos alunos o
    jogo ficou com 2 e o multitap do PCSX2 era desligado a cada abertura."""

    PS2 = {"id": "ps2", "jogadores_por_jogo": {"Crash Nitro Kart": 4, "Marvel Ultimate Alliance": 4}}

    def test_nome_sem_pontuacao_e_palavra_inteira(self):
        self.assertEqual(jogadores.numero_conhecido(self.PS2, "Crash Nitro Kart (USA)"), 4)
        self.assertEqual(jogadores.numero_conhecido(self.PS2, "Marvel - Ultimate Alliance (Europe)"), 4)
        self.assertIsNone(jogadores.numero_conhecido(self.PS2, "Crash Twinsanity"))
        c64 = {"jogadores_por_jogo": {"Mule": 4}}
        self.assertEqual(jogadores.numero_conhecido(c64, "Mule (1983)"), 4)
        self.assertIsNone(jogadores.numero_conhecido(c64, "Formule 1"))     # nao e' palavra inteira
        gc = {"jogadores_por_jogo": {"F Zero GX": 4, "Mario Party": 4}}
        self.assertEqual(jogadores.numero_conhecido(gc, "F-Zero GX (USA)"), 4)
        self.assertEqual(jogadores.numero_conhecido(gc, "Mario Party 4 (USA)"), 4)

    def test_mais_comprido_ganha_e_romset_vale(self):
        lista = {"jogadores_por_jogo": {"Bomberman": 5, "Saturn Bomberman": 10, "tmnt2": 4}}
        self.assertEqual(jogadores.numero_conhecido(lista, "Saturn Bomberman (USA)"), 10)
        self.assertEqual(jogadores.numero_conhecido(lista, "Mega Bomberman"), 5)
        self.assertEqual(jogadores.numero_conhecido(
            lista, "Teenage Mutant Ninja Turtles - Turtles in Time", outros_nomes=("tmnt2",)), 4)

    def test_numero_torto_na_lista_nao_derruba(self):
        self.assertIsNone(jogadores.numero_conhecido({"jogadores_por_jogo": {"Jogo": "muitos"}}, "Jogo"))
        self.assertEqual(jogadores.numero_conhecido({"jogadores_por_jogo": {"Jogo": 999}}, "Jogo"),
                         jogadores.MAXIMO)
        self.assertIsNone(jogadores.numero_conhecido({}, "Jogo"))
        self.assertIsNone(jogadores.numero_conhecido(None, "Jogo"))

    def test_sem_regra_conhecido_multitap_console_e_dois(self):
        snes = {"jogos_multitap": ["Super Bomberman"]}
        self.assertEqual(jogadores.numero_sem_regra(self.PS2, "Crash Nitro Kart"), 4)
        self.assertEqual(jogadores.numero_sem_regra(snes, "Super Bomberman 4"), jogadores.MULTITAP)
        self.assertEqual(jogadores.numero_sem_regra({"jogadores_max": 4}, "Contra 64"), 4)
        self.assertEqual(jogadores.numero_sem_regra(self.PS2, "God of War"), 2)
        self.assertEqual(jogadores.numero_sem_regra({"jogadores_max": "x"}, "Jogo"), 2)

    def test_multitap_igual_ao_do_graficos(self):
        import graficos
        self.assertEqual(jogadores.MULTITAP, graficos.JOGADORES_MULTITAP)

    def test_o_catalogo_de_verdade_tem_os_jogos_testados(self):
        import json
        caminho = os.path.join(RAIZ, "consoles.json")
        with open(caminho, encoding="utf-8") as arquivo:
            por_id = {p["id"]: p for p in json.load(arquivo)["plataformas"]}
        for console, titulo, numero in (
                ("ps2", "Crash Nitro Kart (USA)", 4),
                ("ps2", "Champions of Norrath (USA)", 4),
                ("ps1", "CTR - Crash Team Racing (USA)", 4),
                ("megadrive", "Micro Machines 2 - Turbo Tournament (Europe) (J-Cart)", 4),
                ("gamecube", "Mario Kart - Double Dash!! (USA)", 4),
                ("wii", "Mario Kart Wii (USA)", 4),
                ("ps3", "Minecraft - PlayStation 3 Edition", 4),
                ("saturn", "Saturn Bomberman (USA)", 10)):
            self.assertEqual(jogadores.numero_sem_regra(por_id[console], titulo), numero,
                             "%s: %s" % (console, titulo))


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
        # Nao listado: antes era 2; desde 02/10/2026 vale o que o ARENA ja
        # sabe (lista de Multitap do Super Nintendo = 5). Para limitar, o
        # professor escreve o numero.
        self.assertEqual(n["Super Bomberman 4"][:2], (5, 5))
        # Emulador externo (Dolphin): vale o numero do professor, sem motivo.
        self.assertEqual(n["Mario Kart Double Dash"], (4, 4, ""))

    def test_jogo_que_entrou_depois_do_arquivo_usa_o_que_o_arena_sabe(self):
        """O caso da versao dos alunos (02/10/2026): o arquivo nasceu antes de
        os jogos de PS2 entrarem; o Crash Nitro Kart ficava com 2."""
        indexador.indexar(forcar=True)
        arquivo = os.path.join(indexador.PASTA_DADOS, "jogadores.txt")
        self.assertNotIn("crash nitro kart", [nome for nome, _ in jogadores.ler(arquivo)])
        pasta_ps2 = os.path.join(indexador.PASTA_JOGOS, "pessoais", "PS2")
        os.makedirs(pasta_ps2, exist_ok=True)
        for nome in ("Crash Nitro Kart (USA).iso", "God of War (USA).iso"):
            open(os.path.join(pasta_ps2, nome), "wb").close()
        n = self.numeros(indexador.indexar(forcar=True))
        self.assertEqual(n["Crash Nitro Kart"][:2], (4, 4))
        self.assertEqual(n["God of War"][:2], (2, 2))
        # E e' com esse numero que o ARENA escreve o PCSX2: multitap ligado,
        # 3 controles + o teclado como jogador 4 (com 2, desligava o multitap
        # que o Rafael tinha ligado pelo menu do PCSX2).
        import graficos
        blocos = graficos.controles_pcsx2(n["Crash Nitro Kart"][1], [0, 1, 2])
        texto = blocos if isinstance(blocos, str) else "\n".join(blocos)
        self.assertIn("MultitapPort1 = true", texto)
        self.assertIn("Keyboard", texto)
        blocos = graficos.controles_pcsx2(n["God of War"][1], [0, 1, 2])
        texto = blocos if isinstance(blocos, str) else "\n".join(blocos)
        self.assertIn("MultitapPort1 = false", texto)
        # O professor continua mandando: escreveu 2, fica 2.
        time.sleep(1.1)
        with open(arquivo, "a", encoding="utf-8") as saida:
            saida.write("\nCrash Nitro Kart = 2\n")
        n = self.numeros(indexador.indexar(forcar=False))
        self.assertEqual(n["Crash Nitro Kart"][:2], (2, 2))

    def test_arquivo_novo_ja_nasce_com_os_jogos_testados(self):
        pasta_ps2 = os.path.join(indexador.PASTA_JOGOS, "pessoais", "PS2")
        os.makedirs(pasta_ps2, exist_ok=True)
        open(os.path.join(pasta_ps2, "Crash Nitro Kart (USA).iso"), "wb").close()
        n = self.numeros(indexador.indexar(forcar=True))
        self.assertEqual(n["Crash Nitro Kart"][:2], (4, 4))
        arquivo = os.path.join(indexador.PASTA_DADOS, "jogadores.txt")
        self.assertIn(("crash nitro kart", 4), jogadores.ler(arquivo))


if __name__ == "__main__":
    unittest.main()
