# -*- coding: utf-8 -*-
r"""Mais de 4 controles do tipo Xbox (item 7, 10/11/2026).

O XInput do Windows so enxerga 4 controles. Com os 4 lugares cheios e mais de 4 controles do tipo Xbox na lista do
Windows, o ARENA troca o RetroArch para o driver SDL2 e traduz os botoes que o aluno definiu na tela (gravados na
numeracao do XInput). A tabela de traducao e' conferida aqui contra os perfis que o proprio RetroArch traz para o
mesmo controle (retroarch\autoconfig\xinput e retroarch\autoconfig\sdl2). Com ate 4 controles, nada muda.

O teste de verdade, com 5 controles na mao, fica para a sala (docs\PENDENCIAS.md).
"""
import os
import re
import sys
import unittest
from unittest import mock

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ = os.path.dirname(PASTA_SERVIDOR)
if PASTA_SERVIDOR not in sys.path:
    sys.path.insert(0, PASTA_SERVIDOR)

import controles  # noqa: E402

PERFIL_XINPUT = os.path.join(RAIZ, "retroarch", "autoconfig", "xinput", "XBOX Series Controller.cfg")
PERFIL_SDL2 = os.path.join(RAIZ, "retroarch", "autoconfig", "sdl2", "Xbox Series X Controller.cfg")


def ler_perfil(caminho):
    valores = {}
    with open(caminho, encoding="utf-8", errors="replace") as arquivo:
        for linha in arquivo:
            achado = re.match(r'\s*(input_\w+?_(?:btn|axis))\s*=\s*"([^"]*)"', linha)
            if achado:
                valores[achado.group(1)] = achado.group(2)
    return valores


@unittest.skipUnless(os.path.isfile(PERFIL_XINPUT) and os.path.isfile(PERFIL_SDL2), "sem os perfis do RetroArch")
class ATabelaBateComOsPerfisDoRetroArch(unittest.TestCase):
    def test_cada_botao_do_xinput_vira_o_mesmo_botao_no_sdl2(self):
        xinput, sdl2 = ler_perfil(PERFIL_XINPUT), ler_perfil(PERFIL_SDL2)
        conferidos = 0
        for chave, valor in xinput.items():
            if chave not in sdl2 or chave.startswith("input_menu_toggle"):
                continue
            if chave.endswith("_btn"):
                self.assertEqual(controles.DO_XINPUT_PARA_O_SDL2[valor], sdl2[chave], chave)
            else:
                opcoes = {"input_joypad_driver": "xinput", "input_player1_" + chave[len("input_"):]: valor}
                controles.trocar_para_o_sdl2(opcoes)
                self.assertEqual(opcoes["input_player1_" + chave[len("input_"):]], sdl2[chave], chave)
            conferidos += 1
        self.assertGreaterEqual(conferidos, 20)      # botoes, direcional, gatilhos e os dois analogicos


class QuandoTrocaParaOSdl2(unittest.TestCase):
    def test_so_com_os_4_lugares_cheios_e_mais_de_4_na_lista(self):
        self.assertTrue(controles.precisa_do_sdl2(4, 5))
        self.assertTrue(controles.precisa_do_sdl2(4, 8))
        self.assertFalse(controles.precisa_do_sdl2(4, 4))        # 4 controles: o XInput de sempre
        self.assertFalse(controles.precisa_do_sdl2(3, 6))        # lugar sobrando: a lista conta a mais
        self.assertFalse(controles.precisa_do_sdl2(0, 0))

    def test_traduz_o_que_o_aluno_definiu_e_deixa_o_resto(self):
        opcoes = {"input_joypad_driver": "xinput",
                  "input_player1_start_btn": "6", "input_player1_select_btn": "7", "input_player1_l_btn": "4",
                  "input_player2_up_btn": "h0up", "input_player2_l_y_plus_axis": "-1", "input_player2_l2_axis": "+4",
                  "input_player3_a_btn": "nul", "input_player1_a": "x", "input_player1_btn_a": "8"}
        self.assertTrue(controles.trocar_para_o_sdl2(opcoes))
        self.assertEqual(opcoes["input_joypad_driver"], "sdl2")
        self.assertEqual(opcoes["input_player1_start_btn"], "6")
        self.assertEqual(opcoes["input_player1_select_btn"], "4")
        self.assertEqual(opcoes["input_player1_l_btn"], "9")
        self.assertEqual(opcoes["input_player2_up_btn"], "11")
        self.assertEqual(opcoes["input_player2_l_y_plus_axis"], "+1")
        self.assertEqual(opcoes["input_player2_l2_axis"], "+4")
        self.assertEqual(opcoes["input_player3_a_btn"], "nul")    # o reconhecimento automatico, igual
        self.assertEqual(opcoes["input_player1_a"], "x")          # tecla do teclado
        self.assertEqual(opcoes["input_player1_btn_a"], "8")      # remapeamento do RetroPad, nao e' botao do controle

    def test_quem_escolheu_dinput_fica_no_dinput(self):
        opcoes = {"input_joypad_driver": "dinput", "input_player1_l_btn": "4"}
        self.assertFalse(controles.trocar_para_o_sdl2(opcoes))
        self.assertEqual(opcoes, {"input_joypad_driver": "dinput", "input_player1_l_btn": "4"})


class NaAberturaDoJogo(unittest.TestCase):
    def setUp(self):
        if RAIZ not in sys.path:
            sys.path.insert(0, RAIZ)
        import arena
        self.arena = arena
        self.config = dict(arena.config_padrao())

    def abrir(self, contados, xinput, tipo_xbox):
        with mock.patch.object(controles, "controles_xinput", return_value=list(range(xinput))), \
                mock.patch.object(controles, "controles_tipo_xbox", return_value=tipo_xbox):
            return self.arena.opcoes_efetivas(self.config, controles_ligados=contados)

    @unittest.skipUnless(sys.platform == "win32", "o XInput e' do Windows")
    def test_cinco_controles_de_xbox_abrem_no_sdl2(self):
        self.assertEqual(self.abrir(5, 4, 5)["input_joypad_driver"], "sdl2")

    @unittest.skipUnless(sys.platform == "win32", "o XInput e' do Windows")
    def test_ate_quatro_fica_no_xinput(self):
        self.assertEqual(self.abrir(4, 4, 4)["input_joypad_driver"], "xinput")
        self.assertEqual(self.abrir(2, 2, 2)["input_joypad_driver"], "xinput")
        # 5 contados, mas 4 de Xbox e 1 de outro tipo (PlayStation): o XInput ve os 4 e o outro vai pelo DirectInput.
        self.assertEqual(self.abrir(5, 4, 4)["input_joypad_driver"], "xinput")

    def test_sem_contagem_nada_muda(self):
        with mock.patch.object(controles, "controles_tipo_xbox") as contar:
            self.arena.opcoes_efetivas(self.config)
        contar.assert_not_called()       # o /api/estado nao conta controles (alcas do Windows, 02/10/2026)


if __name__ == "__main__":
    unittest.main()
