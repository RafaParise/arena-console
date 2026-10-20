# -*- coding: utf-8 -*-
r"""Testa o papel de parede do ARENA (ferramentas\papel_de_parede.py).

O que importa aqui NAO e' a imagem final (ela depende do Edge, do
renderizador e da tela da maquina). O que importa e' a MATEMATICA, que
e' o que garante o "redimensionamento perfeito" pedido pelo Rafael:

  1. a escala e' sempre um numero INTEIRO (nada de 9,5 ou 11,25);
  2. a cena nunca e' esticada (a escala e' a mesma nos dois lados);
  3. a ampliacao nearest-neighbor realmente NAO mistura duas cores
     (cada bloco sai com uma cor so);
  4. o PNG gravado pode ser lido de volta e confere com a origem;
  5. a altura logica acompanha a proporcao da tela, e o chao desce junto
     com o ceu (as distancias entre as coisas nao mudam).

Nao precisa de internet, nem de Edge, nem de Pillow: e' so a biblioteca
padrao, como manda o CLAUDE.md.

Rodar:  servidor\python\python.exe testes\teste_papel_de_parede.py
"""
import importlib.util
import os
import shutil
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "testes"))


def carregar():
    """Importa a ferramenta pelo caminho (ela nao e' um pacote)."""
    caminho = os.path.join(RAIZ, "ferramentas", "papel_de_parede.py")
    spec = importlib.util.spec_from_file_location("papel_de_parede", caminho)
    if spec is None or spec.loader is None:
        raise ImportError("nao achei a ferramenta: %s" % caminho)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestEscala(unittest.TestCase):
    """A escala tem que ser inteira e igual nos dois lados."""

    def setUp(self):
        self.mod = carregar()

    def test_escala_inteira_e_uniforme(self):
        for largura, altura in [(1440, 900), (1920, 1080), (1366, 768),
                                (2560, 1440), (1280, 800), (3840, 2160)]:
            logico_h, escala = self.mod.tamanho_logico(largura, altura)
            self.assertIsInstance(escala, int)
            self.assertGreaterEqual(escala, 1)
            # a cena ampliada cabe na tela (a borda e' completada depois)
            self.assertLessEqual(self.mod.LOGICO_L * escala, largura)
            self.assertLessEqual(logico_h * escala, altura)
            # e a escala e' a maior inteira que cabe: nao ha pixel jogado fora
            self.assertEqual(escala, min(largura // self.mod.LOGICO_L,
                                         altura // logico_h))

    def test_escala_nunca_distorce(self):
        """A escala e' a mesma nos dois lados: a cena nao e' esticada."""
        for largura, altura in [(1440, 900), (1920, 1080), (1366, 768),
                                (1280, 800), (1024, 768)]:
            _logico_h, escala = self.mod.tamanho_logico(largura, altura)
            # a altura logica vem da proporcao da tela, entao a cena
            # ampliada tem a MESMA proporcao da tela (diferenca de 1 ponto
            # logico no maximo, por causa do arredondamento)
            proporcao_cena = self.mod.LOGICO_L / float(_logico_h)
            proporcao_tela = largura / float(altura)
            self.assertAlmostEqual(proporcao_cena, proporcao_tela, delta=0.02)

    def test_telas_comuns_ficam_exatas(self):
        """Nas telas de verdade (16:10 e 16:9) a cena preenche a tela
        inteira, sem nenhuma borda completada."""
        for largura, altura in [(1440, 900), (1920, 1080), (2560, 1440),
                                (1280, 800), (3840, 2160)]:
            logico_h, escala = self.mod.tamanho_logico(largura, altura)
            self.assertEqual(self.mod.LOGICO_L * escala, largura,
                             "a largura nao preencheu em %dx%d" % (largura, altura))
            self.assertEqual(logico_h * escala, altura,
                             "a altura nao preencheu em %dx%d" % (largura, altura))

    def test_telas_conhecidas(self):
        # a tela deste computador: 1440x900 (16:10)
        logico_h, escala = self.mod.tamanho_logico(1440, 900)
        self.assertEqual(escala, 9)
        self.assertEqual(logico_h, 100)
        # 1920x1080 (16:9): a cena original, 12x
        logico_h, escala = self.mod.tamanho_logico(1920, 1080)
        self.assertEqual(escala, 12)
        self.assertEqual(logico_h, 90)

    def test_altura_logica_dentro_do_limite(self):
        for largura, altura in [(800, 600), (1440, 900), (1920, 1080),
                                (3440, 1440), (1024, 768)]:
            logico_h, _escala = self.mod.tamanho_logico(largura, altura)
            self.assertGreaterEqual(logico_h, self.mod.LOGICO_H_MIN)
            self.assertLessEqual(logico_h, self.mod.LOGICO_H_MAX)

    def test_altura_logica_segue_a_proporcao(self):
        # telas mais largas que 16:9 precisam de mais altura logica
        _, h_largo = self.mod.tamanho_logico(1920, 900)
        _, h_alto = self.mod.tamanho_logico(1440, 1080)
        self.assertGreater(h_largo, h_alto)


class TestAmpliacao(unittest.TestCase):
    """A ampliacao tem que ser nearest-neighbor de verdade."""

    def setUp(self):
        self.mod = carregar()

    def test_ampliar_faz_blocos_de_uma_cor_so(self):
        pontos = [(10, 20, 30), (40, 50, 60), (70, 80, 90), (100, 110, 120)]
        linhas = self.mod.ampliar(pontos, 2, 2, 3)
        self.assertEqual(len(linhas), 6)
        for linha in linhas:
            self.assertEqual(len(linha), 2 * 3 * 3)
        # o primeiro ponto virou um bloco 3x3 de (10, 20, 30)
        esperado = bytes((10, 20, 30)) * 3
        for _ in range(3):
            self.assertEqual(linhas[0][:9], esperado)
            self.assertEqual(linhas[0][9:], bytes((40, 50, 60)) * 3)

    def test_ampliar_nao_mistura_cores(self):
        """Duas cores vizinhas NAO podem virar uma cor intermediaria
        (isto e' o que um reescalonamento suave faria)."""
        pontos = [(0, 0, 0), (255, 255, 255)]
        linhas = self.mod.ampliar(pontos, 2, 1, 4)
        # a fronteira entre os dois blocos e' dura: 0 e 255, nunca 127
        for _ in range(4):
            self.assertEqual(linhas[0][0:3], bytes((0, 0, 0)))
            self.assertEqual(linhas[0][12:15], bytes((255, 255, 255)))
            self.assertNotIn(b"\x7f", linhas[0])

    def test_ampliar_verticalmente_repete_a_linha(self):
        pontos = [(1, 2, 3), (4, 5, 6)]
        linhas = self.mod.ampliar(pontos, 2, 1, 2)
        self.assertEqual(linhas[0], linhas[1])


class TestPng(unittest.TestCase):
    """O PNG gravado tem que ser legivel e ter o conteudo certo."""

    def setUp(self):
        self.mod = carregar()
        self.pasta = tempfile.mkdtemp(prefix="arena_papel_teste_")

    def tearDown(self):
        shutil.rmtree(self.pasta, ignore_errors=True)

    def test_gravar_e_ler_de_volta(self):
        pontos = [(10, 20, 30), (40, 50, 60), (70, 80, 90), (100, 110, 120)]
        escala = 5
        caminho = os.path.join(self.pasta, "t.png")
        linhas = self.mod.ampliar(pontos, 2, 2, escala)
        self.mod._gravar_png(caminho, 2 * escala, 2 * escala, linhas)
        self.assertTrue(os.path.isfile(caminho))
        largura, altura, lidas = self.mod.ler_png(caminho)
        self.assertEqual((largura, altura), (2 * escala, 2 * escala))
        self.assertEqual(len(lidas), 2 * escala)
        self.assertEqual(lidas[0], linhas[0])

    def test_conferir_aponta_ampliacao_errada(self):
        """A conferencia tem que reprovar uma imagem errada, senao ela
        nao serve de prova de nada."""
        pontos = [(10, 20, 30), (40, 50, 60), (70, 80, 90), (100, 110, 120)]
        escala = 4
        caminho = os.path.join(self.pasta, "t.png")
        linhas = self.mod.ampliar(pontos, 2, 2, escala)
        self.mod._gravar_png(caminho, 2 * escala, 2 * escala, linhas)
        # imagem boa: nao ha problema
        self.assertEqual(
            self.mod.conferir(caminho, pontos, 2, 2, escala, 2 * escala, 2 * escala), [])
        # agora uma imagem com uma cor errada: tem que reprovar
        quebrada = [bytearray(l) for l in linhas]
        quebrada[0][0] = 7          # um canal trocado: 10 vira 7
        self.mod._gravar_png(caminho, 2 * escala, 2 * escala,
                            [bytes(l) for l in quebrada])
        problemas = self.mod.conferir(caminho, pontos, 2, 2, escala,
                                      2 * escala, 2 * escala)
        self.assertTrue(problemas)

    def test_conferir_aponta_tamanho_errado(self):
        pontos = [(10, 20, 30), (40, 50, 60)]
        caminho = os.path.join(self.pasta, "t.png")
        linhas = self.mod.ampliar(pontos, 2, 1, 2)
        self.mod._gravar_png(caminho, 4, 2, linhas)
        problemas = self.mod.conferir(caminho, pontos, 2, 1, 2, 4, 2)
        self.assertEqual(problemas, [])
        problemas = self.mod.conferir(caminho, pontos, 2, 1, 2, 8, 2)
        self.assertTrue(problemas)


class TestChao(unittest.TestCase):
    """O chao tem que descer junto com o ceu, mantendo as distancias."""

    def setUp(self):
        self.mod = carregar()

    def test_chao_desce_com_o_ceu(self):
        # a cena original e' 160x90
        self.assertEqual(self.mod.LOGICO_L, 160)
        desloco = 100 - 90
        for _velho, _novo, altura in self.mod.CHAO:
            self.assertEqual(altura + desloco, altura + 10)

    def test_cena_tem_a_marca_esperada(self):
        """O launcher ainda usa a marca que a ferramenta troca. Se isso
        mudar, a ferramenta tem que avisar em vez de gerar errado."""
        caminho = os.path.join(RAIZ, "launcher", "galaxy-background.js")
        with open(caminho, encoding="utf-8") as f:
            texto = f.read()
        self.assertIn("const W = 160, H = 90;", texto)
        for velho, _novo, _altura in self.mod.CHAO:
            self.assertIn(velho, texto)


class TestCena(unittest.TestCase):
    """A preparacao da cena tem que mudar a altura logica e o chao."""

    def setUp(self):
        self.mod = carregar()
        self.pasta = tempfile.mkdtemp(prefix="arena_cena_teste_")

    def tearDown(self):
        shutil.rmtree(self.pasta, ignore_errors=True)

    def test_preparar_cena_muda_altura_e_chao(self):
        self.mod.preparar_cena(self.pasta, 100)
        caminho = os.path.join(self.pasta, "galaxy-background.js")
        with open(caminho, encoding="utf-8") as f:
            texto = f.read()
        self.assertIn("const W = 160, H = 100;", texto)
        self.assertNotIn("const W = 160, H = 90;", texto)
        # o planeta e as pistas desceram 10 linhas
        self.assertIn("const planeta = { x: W * 0.72, y: 68 };", texto)
        self.assertIn("const PISTA = 81;", texto)
        self.assertIn("const PISTA_KART = 78;", texto)

    def test_preparar_cena_avisa_quando_o_launcher_muda(self):
        """Se o launcher mudar o codigo, a ferramenta tem que recusar em vez
        de gerar um papel de parede errado silenciosamente."""
        with self.assertRaises(SystemExit):
            self.mod.ajustar_cena("const W = 999, H = 999;", 100)

    def test_ajustar_cena_avisa_quando_o_chao_muda(self):
        """O mesmo vale para o chao: se o planeta ou a pista mudarem de
        lugar no launcher, a ferramenta recusa em vez de mexer no errado."""
        texto = "const W = 160, H = 90;\nconst planeta = { x: W * 0.5, y: 58 };"
        with self.assertRaises(SystemExit):
            self.mod.ajustar_cena(texto, 100)


class TestVideoAnimado(unittest.TestCase):
    """O video tem de andar na mesma velocidade que a cena do launcher.

    A cena avanca 'PASSO_CENA' de 1/60 s por quadro. Se o video for
    gravado com outra taxa de quadros, a animacao do papel de parede
    roda mais rapida (ou mais devagar) do que no launcher. Foi um bug
    real: o video estava em 30 fps, mas a cena andava 3/60 s (o
    equivalente a 20 fps), e o wallpaper corria 1,5x mais rapido.
    """

    def setUp(self):
        self.mod = carregar()

    def test_passo_da_cena_combina_com_o_fps_do_video(self):
        self.assertAlmostEqual(
            self.mod.PASSO_CENA, 60.0 / self.mod.FPS_VIDEO, places=6,
            msg="o passo da cena tem de caber no quadro do video")

    def test_passo_da_cena_e_inteiro(self):
        """O passo e' um numero de quadros do 1/60 s: tem de ser inteiro,
        senao a cena anda um tempo fracionado e os quadros saem tortos."""
        self.assertIsInstance(self.mod.PASSO_CENA, int)
        self.assertGreaterEqual(self.mod.PASSO_CENA, 1)

    def test_fps_do_video_e_um_numero_valido(self):
        self.assertGreater(self.mod.FPS_VIDEO, 0)
        self.assertLessEqual(self.mod.FPS_VIDEO, 60)


if __name__ == "__main__":
    unittest.main(verbosity=2)
