# -*- coding: utf-8 -*-
"""Achados da auditoria de 24/10/2026, cada um travado por um teste:
  - a tela tinha DOIS botoes com o mesmo id (chaveDesempenho): o "Modo desempenho" ficou morto e um clique gravava as duas
    configuracoes;
  - recorde e sessao vindos da rede entravam sem faixa (pontos negativos ou gigantes);
  - banco corrompido: o -wal e o -shm eram apagados sem copia;
  - config.json quebrado era regravado com o padrao sem deixar copia;
  - dispositivo_id que nao e' texto derrubava a gravacao dos recordes."""
import json
import os
import re
import sys
import tempfile
import unittest
from unittest import mock

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ = os.path.dirname(PASTA_SERVIDOR)
if PASTA_SERVIDOR not in sys.path:
    sys.path.insert(0, PASTA_SERVIDOR)
sys.path.insert(0, os.path.join(RAIZ, "ferramentas"))
sys.path.insert(0, os.path.join(RAIZ, "testes"))

import arena  # noqa: E402
import auditoria_estatica  # noqa: E402
import limpeza  # noqa: E402


class TelaSemIdRepetido(unittest.TestCase):
    def test_nenhum_id_repetido_no_index(self):
        html = open(os.path.join(RAIZ, "launcher", "index.html"), encoding="utf-8").read()
        ids = re.findall(r'\bid="([^"]+)"', html)
        repetidos = sorted({i for i in ids if ids.count(i) > 1})
        self.assertEqual(repetidos, [], "id repetido: o $('#id') so acha o primeiro e o outro botao fica morto")

    def test_cada_chave_de_desempenho_tem_o_seu_id(self):
        html = open(os.path.join(RAIZ, "launcher", "index.html"), encoding="utf-8").read()
        js = open(os.path.join(RAIZ, "launcher", "app.js"), encoding="utf-8").read()
        self.assertIn('id="chaveAjusteDesempenho"', html)
        self.assertIn('id="chaveDesempenho"', html)
        self.assertIn("salvarConfig({ ajuste_pelo_desempenho: novo })", js.split('$("#chaveAjusteDesempenho").addEventListener')[1][:400])
        self.assertIn("salvarConfig({ modo_desempenho: novo })", js.split('$("#chaveDesempenho").addEventListener')[1][:400])

    def test_a_auditoria_estatica_da_tela_esta_limpa(self):
        problemas, _avisos = auditoria_estatica.auditar_tela()
        self.assertEqual(problemas, [])


class RecebidosDaRede(unittest.TestCase):
    def test_pontos_na_mesma_faixa_do_placar(self):
        self.assertEqual(arena.pontos_validos(0), 0)
        self.assertEqual(arena.pontos_validos("99999999"), 99999999)
        for ruim in (-5, 100000000, 10 ** 12, True, "abc", None, float("inf")):
            with self.assertRaises((ValueError, TypeError, OverflowError)):
                arena.pontos_validos(ruim)

    def test_segundos_da_sessao(self):
        self.assertEqual(arena.segundos_validos(3600), 3600)
        for ruim in (-1, 10 ** 9, False, "x"):
            with self.assertRaises((ValueError, TypeError)):
                arena.segundos_validos(ruim)

    def test_lote_com_registro_ruim_grava_so_os_bons(self):
        pasta = tempfile.mkdtemp(prefix="arena_recebidos_")
        try:
            with mock.patch.object(arena, "ARQUIVO_BANCO", os.path.join(pasta, "arena.db")), \
                    mock.patch.dict(arena._ESQUEMA_CONFERIDO, {}, clear=True):
                arena.preparar_banco()

                def placar(uuid, pontos):
                    return {"uuid": uuid, "apelido": "ana", "jogo_id": "j", "jogo_titulo": "J", "pontos": pontos,
                            "registrado_em": "2026-10-24T10:00:00Z", "dispositivo": "d1"}
                novos = arena.gravar_recebidos([placar("a" * 12, 10), placar("b" * 12, -5), placar("c" * 12, 10 ** 12),
                                                placar("d" * 12, float("inf"))], [])
                self.assertEqual(novos, 1)
        finally:
            limpeza.apagar_pasta(pasta)


class BancoCorrompido(unittest.TestCase):
    def test_o_wal_e_o_shm_ficam_guardados_junto(self):
        pasta = tempfile.mkdtemp(prefix="arena_banco_quebrado_")
        try:
            banco = os.path.join(pasta, "arena.db")
            with open(banco, "wb") as f:
                f.write(b"isto nao e um banco sqlite" * 50)
            with open(banco + "-wal", "wb") as f:
                f.write(b"recordes ainda no wal")
            original = arena.banco
            chamadas = []

            def banco_que_falha_na_primeira():
                # O SQLite sozinho apaga um -wal curto ao abrir: para provar SO o que o ARENA faz com o -wal, a
                # primeira abertura falha sem mexer em arquivo nenhum.
                chamadas.append(1)
                if len(chamadas) == 1:
                    raise arena.sqlite3.DatabaseError("file is not a database")
                return original()
            with mock.patch.object(arena, "ARQUIVO_BANCO", banco), \
                    mock.patch.dict(arena._ESQUEMA_CONFERIDO, {}, clear=True), \
                    mock.patch.object(arena, "banco", banco_que_falha_na_primeira):
                arena.preparar_banco()
            nomes = sorted(os.listdir(pasta))
            quebrados = [n for n in nomes if ".corrompido-" in n]
            self.assertTrue(any(n.endswith("-wal") for n in quebrados), nomes)      # o -wal foi guardado, nao apagado
            conteudo = [open(os.path.join(pasta, n), "rb").read() for n in quebrados if n.endswith("-wal")]
            self.assertEqual(conteudo, [b"recordes ainda no wal"])
            self.assertIn("arena.db", nomes)                                          # e um banco novo nasceu
        finally:
            limpeza.apagar_pasta(pasta)

    def test_esquema_so_vale_como_conferido_depois_de_aplicado(self):
        pasta = tempfile.mkdtemp(prefix="arena_esquema_")
        try:
            banco = os.path.join(pasta, "arena.db")
            with mock.patch.object(arena, "ARQUIVO_BANCO", banco), \
                    mock.patch.dict(arena._ESQUEMA_CONFERIDO, {}, clear=True):
                with mock.patch.object(arena, "aplicar_esquema", side_effect=RuntimeError("falhou")):
                    with self.assertRaises(RuntimeError):
                        with arena.banco():
                            pass
                self.assertIsNot(arena._ESQUEMA_CONFERIDO.get(banco), True)           # a proxima conexao tenta de novo
                with arena.banco():
                    pass
                self.assertIs(arena._ESQUEMA_CONFERIDO.get(banco), True)
        finally:
            limpeza.apagar_pasta(pasta)


class ConfigQuebrado(unittest.TestCase):
    def test_guarda_uma_copia_uma_vez_so(self):
        pasta = tempfile.mkdtemp(prefix="arena_config_quebrado_")
        try:
            arquivo = os.path.join(pasta, "config.json")
            with open(arquivo, "w", encoding="utf-8") as f:
                f.write('{"apelido": "ana", ')                   # cortado no meio
            with mock.patch.object(arena, "ARQUIVO_CONFIG", arquivo), \
                    mock.patch.object(arena, "_CONFIG_QUEBRADA_GUARDADA", set()):
                arena.ler_config_do_disco()
                arena.ler_config_do_disco()
            copias = [n for n in os.listdir(pasta) if ".corrompido-" in n]
            self.assertEqual(len(copias), 1)
            self.assertEqual(open(os.path.join(pasta, copias[0]), encoding="utf-8").read(), '{"apelido": "ana", ')
        finally:
            limpeza.apagar_pasta(pasta)

    def test_dispositivo_id_que_nao_e_texto_vira_vazio(self):
        pasta = tempfile.mkdtemp(prefix="arena_config_id_")
        try:
            arquivo = os.path.join(pasta, "config.json")
            with open(arquivo, "w", encoding="utf-8") as f:
                json.dump({"dispositivo_id": ["a", "b"], "codigo_proprio": True}, f)
            with mock.patch.object(arena, "ARQUIVO_CONFIG", arquivo):
                config = arena.ler_config_do_disco()
            self.assertIsInstance(config["dispositivo_id"], str)
            self.assertTrue(config["dispositivo_id"])
        finally:
            limpeza.apagar_pasta(pasta)


if __name__ == "__main__":
    unittest.main()
