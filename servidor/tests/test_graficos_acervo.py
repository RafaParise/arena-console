# -*- coding: utf-8 -*-
"""Testes para servidor/graficos.py"""

import os
import sys
import tempfile
import shutil
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)


class TestGraficos(unittest.TestCase):

    def setUp(self):
        import graficos
        self.mod = graficos
        self.dir = tempfile.mkdtemp(prefix="arena_graf_")
        self._old_raiz = self.mod.RAIZ
        self.mod.RAIZ = self.dir
        # PASTA_RETROARCH tambem: gravar_opcoes_dos_nucleos agora le as
        # opcoes que o aluno mudou (retroarch\config\*\*.opt) para nao
        # apaga-las. Sem isto o teste leria as da maquina de verdade.
        self._old_pasta_ra = self.mod.PASTA_RETROARCH
        self.mod.PASTA_RETROARCH = os.path.join(self.dir, "retroarch")
        self._old_arquivo = getattr(self.mod, "ARQUIVO_OPCOES_CORE", None)
        self.mod.ARQUIVO_OPCOES_CORE = os.path.join(
            self.dir, "retroarch-core-options.cfg")
        # ARQUIVO_GRAFICOS tambem precisa apontar pro json de teste, senao
        # carregar_graficos() le o servidor/graficos.json de verdade (com
        # as centenas de opcoes reais) e os testes abaixo veem dado errado.
        self._old_arquivo_graficos = self.mod.ARQUIVO_GRAFICOS
        self.mod.ARQUIVO_GRAFICOS = os.path.join(self.dir, "graficos.json")
        self._old_cache = graficos._cache.copy()
        graficos._cache = {"graficos": None}
        os.makedirs(os.path.join(self.dir, "retroarch"), exist_ok=True)
        with open(os.path.join(self.dir, "graficos.json"), "w",
                  encoding="utf-8") as f:
            f.write('{"nucleos": {}, "shaders": {}}')

    def tearDown(self):
        self.mod.RAIZ = self._old_raiz
        self.mod.PASTA_RETROARCH = self._old_pasta_ra
        if self._old_arquivo is not None:
            self.mod.ARQUIVO_OPCOES_CORE = self._old_arquivo
        self.mod.ARQUIVO_GRAFICOS = self._old_arquivo_graficos
        self.mod._cache = self._old_cache
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_gravar_opcoes_dos_nucleos_arquivo_vazio(self):
        opcoes = self.mod.gravar_opcoes_dos_nucleos(3)
        self.assertEqual(opcoes, 0)
        # gravar_opcoes_dos_nucleos sempre grava o arquivo, mesmo sem
        # opcoes (fica so com as duas linhas de cabecalho) -- e assim
        # que arena.py espera encontrar o arquivo depois de chamar isto.
        self.assertTrue(os.path.isfile(self.mod.ARQUIVO_OPCOES_CORE))
        with open(self.mod.ARQUIVO_OPCOES_CORE, encoding="utf-8") as f:
            texto = f.read()
        self.assertEqual(texto.count("\n"), 2)

    def test_gravar_opcoes_dos_nucleos_com_dados(self):
        with open(os.path.join(self.dir, "graficos.json"), "w",
                  encoding="utf-8") as f:
            f.write('{"nucleos": {"fbneo": {"sempre": {"x": "1"}}}}')
        n = self.mod.gravar_opcoes_dos_nucleos(3)
        self.assertGreater(n, 0)
        with open(self.mod.ARQUIVO_OPCOES_CORE, encoding="utf-8") as f:
            texto = f.read()
        self.assertIn("x = \"1\"", texto)

    def test_gravar_opcoes_mantem_o_que_o_aluno_mudou(self):
        # Revisao pos-auditoria: com global_core_options ligado, reescrever
        # o arquivo do zero apagaria o que o aluno mudou no menu. O que
        # estava no .opt antigo do nucleo migra; chave do ARENA vence; lixo
        # "duckstation_*" nao entra.
        with open(os.path.join(self.dir, "graficos.json"), "w",
                  encoding="utf-8") as f:
            f.write('{"nucleos": {"fbneo": {"sempre": {"x": "1"}}}}')
        pasta_opt = os.path.join(self.dir, "retroarch", "config", "Nucleo")
        os.makedirs(pasta_opt)
        with open(os.path.join(pasta_opt, "Nucleo.opt"), "w", encoding="utf-8") as f:
            f.write('x = "9"\ndo_aluno = "sim"\nduckstation_BIOS.Path = "a.bin"\n')
        self.mod.gravar_opcoes_dos_nucleos(3)
        with open(self.mod.ARQUIVO_OPCOES_CORE, encoding="utf-8") as f:
            texto = f.read()
        self.assertIn('x = "1"', texto)
        self.assertNotIn('x = "9"', texto)
        self.assertIn('do_aluno = "sim"', texto)
        self.assertNotIn("duckstation_", texto)

    def test_gravar_atomico(self):
        caminho = os.path.join(self.dir, "teste.txt")
        self.mod.gravar_atomico(caminho, "olá")
        with open(caminho, encoding="utf-8") as f:
            self.assertEqual(f.read(), "olá")

    def test_opcoes_do_nucleo_nao_existe(self):
        with open(os.path.join(self.dir, "graficos.json"), "w",
                  encoding="utf-8") as f:
            f.write('{"nucleos": {"core_ok": {"sempre": {"a": "1"}}}}')
        self.mod.carregar_graficos()  # resetar cache
        self.assertEqual(self.mod.opcoes_do_nucleo("inexistente", 3), {})

    def test_shader_para_nenhum(self):
        with open(os.path.join(self.dir, "graficos.json"), "w",
                  encoding="utf-8") as f:
            f.write('{"nucleos": {}, "shaders": {}}')
        self.mod.carregar_graficos()
        self.assertEqual(self.mod.shader_para(1), "")


class TestAcervo(unittest.TestCase):

    def setUp(self):
        import acervo
        self.mod = acervo
        self.dir = tempfile.mkdtemp(prefix="arena_acervo_")
        self._old_raiz = self.mod.RAIZ
        self.mod.RAIZ = self.dir
        self._old_pasta_livres = getattr(self.mod, "PASTA_LIVRES", None)
        self.mod.PASTA_LIVRES = os.path.join(self.dir, "jogos", "livres")
        acervo_pasta = os.path.join(self.dir, "dados")
        os.makedirs(acervo_pasta, exist_ok=True)
        with open(os.path.join(acervo_pasta, "acervo_autorizado.json"), "w",
                  encoding="utf-8") as f:
            f.write('[]')
        # A constante de verdade em acervo.py se chama ARQUIVO (nao
        # ARQUIVO_ACERVO). Com o nome errado o monkeypatch nao pegava e
        # ler_itens()/_salvar_itens() liam e escreviam no
        # dados/acervo_autorizado.json REAL do projeto.
        self._old_arquivo = self.mod.ARQUIVO
        self.mod.ARQUIVO = os.path.join(acervo_pasta,
                                        "acervo_autorizado.json")

    def tearDown(self):
        self.mod.RAIZ = self._old_raiz
        if self._old_pasta_livres is not None:
            self.mod.PASTA_LIVRES = self._old_pasta_livres
        self.mod.ARQUIVO = self._old_arquivo
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_listar_vazio(self):
        itens = self.mod.listar()
        self.assertIsInstance(itens, list)

    def test_fontes(self):
        fontes = self.mod.fontes()
        self.assertIsInstance(fontes, list)

    def test_acervo_json_ilegivel(self):
        with open(os.path.join(self.dir, "dados",
                               "acervo_autorizado.json"), "w") as f:
            f.write("{quebrado")
        itens = self.mod.listar()
        self.assertIsInstance(itens, list)

    def test_salvar_item(self):
        item = {
            "id": "teste-01",
            "titulo": "Jogo de Teste",
            "plataforma": "nes",
            "descricao": "Um jogo de teste",
            "licenca": "Domínio público",
            "fonte": "archive.org",
            "url": "https://archive.org/details/teste",
            "sha256": "0" * 64,
            "destino": os.path.join("jogos", "livres", "teste.nes"),
        }
        salvo = self.mod.salvar(item)
        self.assertEqual(salvo["id"], "teste-01")
        itens = self.mod.listar()
        self.assertEqual(len(itens), 1)

    def test_remover_item(self):
        item = {
            "id": "remover-01",
            "titulo": "Jogo para remover",
            "plataforma": "snes",
            "descricao": "Vai ser removido",
            "licenca": "Domínio público",
            "fonte": "archive.org",
            "url": "https://archive.org/details/remover",
            "sha256": "0" * 64,
            "destino": os.path.join("jogos", "livres", "remove.nes"),
        }
        self.mod.salvar(item)
        self.mod.remover("remover-01")
        itens = self.mod.listar()
        self.assertEqual(len(itens), 0)
        with self.assertRaises(ValueError):
            self.mod.remover("inexistente")

    def test_salvar_item_invalido(self):
        with self.assertRaises(ValueError):
            self.mod.salvar({"titulo": "Sem ID"})
        with self.assertRaises(ValueError):
            self.mod.salvar({
                "id": "nope!",
                "titulo": "Opa",
                "plataforma": "nes",
                "licenca": "pd",
                "fonte": "archive.org",
                "url": "https://archive.org/details/opa",
                "sha256": "0" * 64,
                "destino": "jogos/livres/opa.nes",
            })

    def test_salvar_item_url_invalida(self):
        with self.assertRaises(ValueError):
            self.mod.salvar({
                "id": "url-bad",
                "titulo": "URL ruim",
                "plataforma": "nes",
                "licenca": "pd",
                "fonte": "google.com",
                "url": "http://google.com/teste",
                "sha256": "0" * 64,
                "destino": "jogos/livres/teste.nes",
            })

    def test_salvar_item_destino_fora_livres(self):
        with self.assertRaises(ValueError):
            self.mod.salvar({
                "id": "dest-bad",
                "titulo": "Destino proibido",
                "plataforma": "nes",
                "licenca": "pd",
                "fonte": "archive.org",
                "url": "https://archive.org/details/proibido",
                "sha256": "0" * 64,
                "destino": os.path.join("jogos", "pessoais", "proibido.nes"),
            })


if __name__ == "__main__":
    unittest.main()
