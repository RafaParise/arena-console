# -*- coding: utf-8 -*-
"""A conferencia das pastas de jogos em paralelo (indexador.pastas_com_data, 14/11/2026).

Achado da prova em Rust da Fase 3 (docs/PLANO-DE-ACAO-RUST.md): o que acelera a conferencia no cartao SD do
Android e' perguntar ao disco em paralelo, nao a linguagem. A troca so vale se a assinatura sair IGUAL a de antes
(os.walk + getmtime): senao, todo ARENA atualizado varreria os jogos de novo na primeira abertura."""
import os
import sys
import tempfile
import time
import unittest

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PASTA_SERVIDOR not in sys.path:
    sys.path.insert(0, PASTA_SERVIDOR)
import indexador  # noqa: E402

PASTA_TESTES = os.path.join(os.path.dirname(PASTA_SERVIDOR), "testes")
if PASTA_TESTES not in sys.path:
    sys.path.insert(0, PASTA_TESTES)
import limpeza  # noqa: E402


def como_antes(raizes):
    """O jeito de antes da indexador.assinatura_das_pastas (ate 14/11/2026), para comparar."""
    partes = []
    for caminho in raizes:
        for pasta_atual, subpastas, _arquivos in os.walk(caminho):
            subpastas[:] = sorted(p for p in subpastas if not indexador.pasta_escondida(p))
            try:
                partes.append("%s|%d" % (pasta_atual, os.path.getmtime(pasta_atual)))
            except OSError:
                continue
    return partes


class ConferenciaParalela(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_conferir_")
        self.raizes = []
        for origem in ("pendrive", "cartao"):
            raiz = os.path.join(self.pasta, origem)
            self.raizes.append(raiz)
            for console in ("snes", "ps1", "Mega Drive", "ação"):
                for sub in ("", "RPG", os.path.join("RPG", "Japão"), os.path.join("Corrida", "2 jogadores")):
                    os.makedirs(os.path.join(raiz, console, sub), exist_ok=True)
                with open(os.path.join(raiz, console, "jogo.zip"), "wb") as saida:
                    saida.write(b"x")
            for escondida in (".git", "$RECYCLE.BIN", "System Volume Information", ".Trashes"):
                os.makedirs(os.path.join(raiz, escondida, "dentro"))

    def tearDown(self):
        limpeza.apagar_pasta(self.pasta)

    def test_mesma_lista_de_antes(self):
        novas = indexador.pastas_com_data(self.raizes)
        self.assertEqual(sorted(novas), sorted(como_antes(self.raizes)))
        self.assertEqual(len(novas), 2 * (1 + 4 * 5))       # 2 raizes, 4 consoles com 5 pastas cada
        self.assertFalse([linha for linha in novas if ".git" in linha or "RECYCLE" in linha or "Trashes" in linha])

    def test_pasta_nova_la_no_fundo_muda_a_lista(self):
        antes = sorted(indexador.pastas_com_data(self.raizes))
        os.makedirs(os.path.join(self.raizes[1], "ps1", "RPG", "Japão", "Disco 2"))
        depois = sorted(indexador.pastas_com_data(self.raizes))
        self.assertNotEqual(antes, depois)
        self.assertEqual(depois, sorted(como_antes(self.raizes)))

    def test_raiz_que_sumiu_nao_quebra(self):
        sumida = os.path.join(self.pasta, "pen-drive-arrancado")
        self.assertEqual(sorted(indexador.pastas_com_data(self.raizes + [sumida])),
                         sorted(como_antes(self.raizes + [sumida])))
        self.assertEqual(indexador.pastas_com_data([]), [])

    def test_nao_e_mais_lento_que_antes(self):
        """Nem no PC (disco rapido, onde o paralelo quase nao ajuda) a troca pode pesar: com folga larga."""
        inicio = time.perf_counter()
        for _ in range(5):
            como_antes(self.raizes)
        antes = time.perf_counter() - inicio
        inicio = time.perf_counter()
        for _ in range(5):
            indexador.pastas_com_data(self.raizes)
        agora = time.perf_counter() - inicio
        self.assertLess(agora, antes * 3 + 0.05)


class AssinaturaPeloConteudo(unittest.TestCase):
    """Cada APK novo regrava os arquivos do servidor (data nova, conteudo igual): a assinatura nao pode mudar, ou o
    Galaxy A12 varre os 2699 jogos de novo (9,9 s, medido em 14/11/2026 com o multitap.json)."""

    def setUp(self):
        from unittest import mock
        self.pasta = tempfile.mkdtemp(prefix="arena_assinatura_")
        self.mapa = os.path.join(self.pasta, "multitap.json")
        self.consoles = os.path.join(self.pasta, "consoles.json")
        for caminho in (self.mapa, self.consoles):
            with open(caminho, "w", encoding="utf-8") as saida:
                saida.write('{"a": 1}')
        os.makedirs(os.path.join(self.pasta, "jogos", "pessoais", "snes"))
        self.trocas = [mock.patch.object(indexador.graficos, "ARQUIVO_MAPA_MULTITAP", self.mapa),
                       mock.patch.object(indexador, "ARQUIVO_CONSOLES", self.consoles),
                       mock.patch.object(indexador, "PASTA_JOGOS", os.path.join(self.pasta, "jogos")),
                       mock.patch.object(indexador, "PASTA_DADOS", os.path.join(self.pasta, "dados"))]
        for troca in self.trocas:
            troca.start()

    def tearDown(self):
        for troca in self.trocas:
            troca.stop()
        limpeza.apagar_pasta(self.pasta)

    def regravar(self, caminho, texto):
        with open(caminho, "w", encoding="utf-8") as saida:
            saida.write(texto)
        futuro = time.time() + 120
        os.utime(caminho, (futuro, futuro))       # data nova, como o APK novo deixa

    def test_regravar_igual_nao_muda_e_mudar_muda(self):
        antes = indexador.assinatura_das_pastas()
        self.regravar(self.mapa, '{"a": 1}')
        self.regravar(self.consoles, '{"a": 1}')
        self.assertEqual(indexador.assinatura_das_pastas(), antes)
        self.regravar(self.mapa, '{"a": 2}')
        self.assertNotEqual(indexador.assinatura_das_pastas(), antes)


if __name__ == "__main__":
    unittest.main()
