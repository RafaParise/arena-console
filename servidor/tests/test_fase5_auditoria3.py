# -*- coding: utf-8 -*-
r"""Fase 5 da auditoria 3 (matriz de jogos, 09/10/2026): o que mudou no
programa por causa do que a matriz mediu.

1. O perfil de imagem automatico escolhe "Qualidade" para todo console de
   custo ate 3 numa maquina de nota 4 -- e o Celeron N5100 da escola tira
   nota 4, igual ao Ryzen. O Qualidade ligava "Voltar no tempo" e "Resposta
   instantanea". Medido no Ryzen com o jogo aberto: o N64 caia de 60 para
   30 quadros/s (voltar no tempo); o ZX Spectrum gastava 12x o processador
   (resposta instantanea); o PS1, 5x (as duas). Agora nenhum perfil liga as
   duas sozinho; o aluno continua podendo ligar em Ajustes -> Avancado.
(Os outros consertos da fase tem testes proprios: test_bios.py, a BIOS que
falta; test_cheats_retroarch.py, a gaveta "Saves e cheats".)
"""
import os
import sys
import unittest
from unittest import mock

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PASTA_SERVIDOR)

import arena  # noqa: E402


class TestPerfilQualidadeSemExtrasPesados(unittest.TestCase):

    def test_nenhum_perfil_liga_sozinho_voltar_no_tempo_nem_resposta_instantanea(self):
        for nome, perfil in arena.PERFIS_GRAFICOS.items():
            with self.subTest(perfil=nome):
                self.assertEqual(perfil["opcoes"].get("rewind_enable"), "false")
                self.assertEqual(perfil["opcoes"].get("run_ahead_enabled"), "false")

    def test_automatico_na_maquina_de_nota_4_nao_liga(self):
        config = arena.config_padrao()
        with mock.patch.dict(arena.CAPACIDADE, {"nota": 4}):
            for custo in (1, 2, 3):
                with self.subTest(custo=custo):
                    self.assertEqual(arena.perfil_para(config, custo), "qualidade")
                    opcoes = arena.opcoes_efetivas(config, custo)
                    self.assertEqual(opcoes["rewind_enable"], "false")
                    self.assertEqual(opcoes["run_ahead_enabled"], "false")

    def test_o_aluno_ainda_liga_pelo_avancado(self):
        config = arena.config_padrao()
        config["avancado"] = dict(config["avancado"], rewind_enable="true", run_ahead_enabled="true")
        with mock.patch.dict(arena.CAPACIDADE, {"nota": 4}):
            opcoes = arena.opcoes_efetivas(config, 1)
        self.assertEqual(opcoes["rewind_enable"], "true")
        self.assertEqual(opcoes["run_ahead_enabled"], "true")


if __name__ == "__main__":
    unittest.main()
