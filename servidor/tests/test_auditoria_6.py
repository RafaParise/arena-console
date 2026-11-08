# -*- coding: utf-8 -*-
"""Achados da auditoria 6 (08/11/2026) que mexem no banco e na configuracao (docs\\RELATORIO-AUDITORIA-6.md).

Banco e configuracao de mentira numa pasta temporaria: os do ARENA de verdade nunca sao tocados.
"""
import os
import sys
import tempfile
import unittest
from unittest import mock

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(AQUI)), "testes"))
import arena  # noqa: E402
import limpeza  # noqa: E402


class OIdDoJogoLevadoParaOCartao(unittest.TestCase):
    """DAD6-04: o id do jogo e' o caminho dele; levado para o cartao, o placar, o tempo de jogo, os favoritos e os
    recentes seguem o jogo, em vez de sumir da lista."""

    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_auditoria6_")
        self.addCleanup(limpeza.apagar_pasta, self.pasta)
        for remendo in (mock.patch.object(arena, "ARQUIVO_BANCO", os.path.join(self.pasta, "arena.db")),
                        mock.patch.dict(arena._ESQUEMA_CONFERIDO, {}, clear=True)):
            remendo.start()
            self.addCleanup(remendo.stop)
        arena.preparar_banco()
        self.config = {"favoritos": ["jogos/pessoais/snes/zelda.sfc", "outro"],
                       "recentes": ["jogos/pessoais/snes/zelda.sfc"]}
        self.salvo = []
        for remendo in (mock.patch.object(arena, "carregar_config", lambda: dict(self.config)),
                        mock.patch.object(arena, "salvar_config", self.salvo.append)):
            remendo.start()
            self.addCleanup(remendo.stop)

    def test_placar_sessao_favoritos_e_recentes_seguem_o_jogo(self):
        with arena.banco() as conexao:
            conexao.execute("INSERT INTO placar (uuid, apelido, jogo_id, jogo_titulo, pontos, registrado_em, "
                            "dispositivo) VALUES ('a', 'ana', 'jogos/pessoais/snes/zelda.sfc', 'Zelda', 10, 'x', 'd')")
        antigo = os.path.join(arena.RAIZ, "jogos", "pessoais", "SNES", "Zelda.sfc")
        novo = os.path.join(arena.RAIZ, "jogos", "cartao-1234", "SNES", "Zelda.sfc")
        self.assertEqual(arena.trocar_id_dos_jogos([(antigo, novo)]), 1)
        with arena.banco() as conexao:
            ids = [linha[0] for linha in conexao.execute("SELECT jogo_id FROM placar")]
        self.assertEqual(ids, ["jogos/cartao-1234/snes/zelda.sfc"])
        self.assertEqual(self.salvo[-1]["favoritos"], ["jogos/cartao-1234/snes/zelda.sfc", "outro"])
        self.assertEqual(self.salvo[-1]["recentes"], ["jogos/cartao-1234/snes/zelda.sfc"])

    def test_nada_levado_nada_muda(self):
        self.assertEqual(arena.trocar_id_dos_jogos([]), 0)
        self.assertEqual(self.salvo, [])


class OsBotoesTrocadosVaoNoRemapeamento(unittest.TestCase):
    """08/11/2026: o Saturn do Android (YabaSanshiro) pede o C e o Z trocados; a troca vai no .rmp da partida, por cima
    do remapeamento que o aluno salvou, sem perder o resto dele, e sai das opcoes do --appendconfig."""

    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_remap6_")
        self.addCleanup(limpeza.apagar_pasta, self.pasta)
        retroarch = os.path.join(self.pasta, "retroarch")
        os.makedirs(os.path.join(retroarch, "info"))
        with open(os.path.join(retroarch, "info", "yabasanshiro_libretro.info"), "w", encoding="utf-8") as arquivo:
            arquivo.write('corename = "YabaSanshiro"\n')
        os.makedirs(os.path.join(retroarch, "remaps", "YabaSanshiro"))
        with open(os.path.join(retroarch, "remaps", "YabaSanshiro", "YabaSanshiro.rmp"), "w",
                  encoding="utf-8") as arquivo:
            arquivo.write('input_player1_btn_a = "8"\ninput_player1_btn_l = "4"\ninput_libretro_device_p1 = "1"\n')
        for remendo in (mock.patch.object(arena, "PASTA_RETROARCH", retroarch),
                        mock.patch.object(arena, "PASTA_REMAPS", os.path.join(retroarch, "remaps")),
                        mock.patch.object(arena, "PASTA_REMAP_PARTIDA", os.path.join(self.pasta, "remap_partida"))):
            remendo.start()
            self.addCleanup(remendo.stop)

    def test_troca_do_l_e_do_r_no_rmp(self):
        opcoes = {"input_libretro_device_p1": "5", "input_player1_btn_l": "11", "input_player1_btn_r": "10",
                  "input_player1_analog_dpad_mode": "1"}
        pasta = arena.remapeamento_da_partida(opcoes, "yabasanshiro_libretro_android.so", "/jogos/Bomberman.chd")
        with open(os.path.join(pasta, "YabaSanshiro", "Bomberman.rmp"), encoding="utf-8") as arquivo:
            linhas = arquivo.read().splitlines()
        self.assertIn('input_player1_btn_a = "8"', linhas)          # o que o aluno salvou fica
        self.assertIn('input_player1_btn_l = "11"', linhas)         # a troca do nucleo vale mais
        self.assertNotIn('input_player1_btn_l = "4"', linhas)
        self.assertIn('input_player1_btn_r = "10"', linhas)
        self.assertIn('input_libretro_device_p1 = "5"', linhas)
        self.assertEqual(len([l for l in linhas if l.startswith("input_player1_btn_l")]), 1)

    def test_o_que_e_do_rmp(self):
        for chave in ("input_libretro_device_p3", "input_player1_btn_l", "input_player12_btn_r2"):
            self.assertTrue(arena.chave_do_remapeamento(chave), chave)
        for chave in ("input_player1_analog_dpad_mode", "input_player1_a", "input_player_btn_l", "video_driver"):
            self.assertFalse(arena.chave_do_remapeamento(chave), chave)


if __name__ == "__main__":
    unittest.main()
