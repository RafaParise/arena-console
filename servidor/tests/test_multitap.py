# -*- coding: utf-8 -*-
"""Testes de graficos.jogadores_do_jogo e da devolucao do retroarch.cfg
(Fase B do multitap), com o mapa de verdade (servidor\\multitap.json)."""

import os
import shutil
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

import graficos  # noqa: E402


class TestJogadoresDoJogo(unittest.TestCase):

    def ligar(self, nucleo, jogadores, config=2):
        return graficos.jogadores_do_jogo(nucleo, jogadores, config)

    def test_um_ou_dois_nao_mudam_nada(self):
        # Regra de ouro: nenhuma chave, conexoes no padrao de sempre.
        for nucleo in ("snes9x_libretro.dll", "pcsx_rearmed_libretro.dll",
                       "ppsspp_libretro.dll", "nao_existe.dll", ""):
            for n in (1, 2, None):
                r = self.ligar(nucleo, n)
                self.assertEqual(r["cfg"], {})
                self.assertEqual(r["nucleo"], {})
                self.assertEqual(r["max_conexoes"], 3)
                self.assertEqual(r["motivo"], "")

    def test_snes_multitap_na_porta_2(self):
        r = self.ligar("snes9x_libretro.dll", 5)
        self.assertEqual(r["jogadores"], 5)
        self.assertEqual(r["cfg"]["input_libretro_device_p2"], "257")
        self.assertEqual(r["cfg"]["input_max_users"], "5")
        self.assertEqual(r["max_conexoes"], 4)
        self.assertEqual(r["nucleo"], {})

    def test_nes_four_score_nas_portas_3_e_4(self):
        r = self.ligar("fceumm_libretro.dll", 4)
        self.assertEqual(r["cfg"]["input_libretro_device_p3"], "513")
        self.assertEqual(r["cfg"]["input_libretro_device_p4"], "513")
        self.assertEqual(r["jogadores"], 4)
        self.assertEqual(r["max_conexoes"], 3)  # 4 - 1 = 3, o padrao ja cabe

    def test_ps1_e_opcao_do_nucleo(self):
        r = self.ligar("pcsx_rearmed_libretro.dll", 4)
        self.assertEqual(r["nucleo"], {"pcsx_rearmed_multitap": "port 1"})
        self.assertNotIn("input_libretro_device_p2", r["cfg"])
        self.assertEqual(r["cfg"]["input_max_users"], "4")
        s = self.ligar("swanstation_libretro.dll", 5)
        self.assertEqual(s["nucleo"], {"swanstation_ControllerPorts_MultitapMode": "Port1Only"})

    def test_saturn_dez_jogadores_liga_os_dois_adaptadores(self):
        r = self.ligar("mednafen_saturn_libretro.dll", 10)
        self.assertEqual(r["nucleo"], {"beetle_saturn_multitap_port1": "enabled",
                                       "beetle_saturn_multitap_port2": "enabled"})
        self.assertEqual(r["jogadores"], 10)
        self.assertEqual(r["max_conexoes"], 9)
        um = self.ligar("mednafen_saturn_libretro.dll", 6)
        self.assertEqual(um["nucleo"], {"beetle_saturn_multitap_port1": "enabled"})

    def test_n64_quatro_de_fabrica_sem_adaptador(self):
        r = self.ligar("mupen64plus_next_libretro.dll", 4)
        self.assertEqual(r["jogadores"], 4)
        self.assertEqual(r["cfg"], {"input_max_users": "4"})
        self.assertEqual(r["nucleo"], {})
        self.assertEqual(r["motivo"], "")

    def test_limite_do_nucleo_vira_motivo(self):
        r = self.ligar("fbneo_libretro.dll", 4)
        self.assertEqual(r["jogadores"], 2)
        self.assertEqual(r["cfg"], {})
        self.assertIn("até 2", r["motivo"])
        s = self.ligar("snes9x_libretro.dll", 8)   # pede mais que o adaptador
        self.assertEqual(s["jogadores"], 5)
        self.assertIn("até 5", s["motivo"])

    def test_nucleo_fora_do_mapa(self):
        r = self.ligar("nao_existe_libretro.dll", 4)
        self.assertEqual(r["jogadores"], 2)
        self.assertTrue(r["motivo"])
        self.assertEqual(r["cfg"], {})

    def test_config_com_mais_controles_nao_diminui(self):
        r = self.ligar("snes9x_libretro.dll", 5, config=8)
        self.assertEqual(r["cfg"]["input_max_users"], "8")

    def test_sem_mapa_continua_ate_dois(self):
        r = graficos.jogadores_do_jogo("snes9x_libretro.dll", 5, mapa={})
        self.assertEqual(r["jogadores"], 2)
        self.assertEqual(r["cfg"], {})


class TestArquivosDaPartida(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="arena_multitap_teste_")
        self._antigos = (graficos.PASTA_RETROARCH, graficos.ARQUIVO_OPCOES_CORE,
                         graficos.ARQUIVO_OPCOES_CORE_PARTIDA)
        graficos.PASTA_RETROARCH = self.dir
        graficos.ARQUIVO_OPCOES_CORE = os.path.join(self.dir, "retroarch-core-options.cfg")
        graficos.ARQUIVO_OPCOES_CORE_PARTIDA = os.path.join(self.dir, "dados", "copia.cfg")

    def tearDown(self):
        (graficos.PASTA_RETROARCH, graficos.ARQUIVO_OPCOES_CORE,
         graficos.ARQUIVO_OPCOES_CORE_PARTIDA) = self._antigos
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_copia_das_opcoes_nao_toca_no_original(self):
        original = 'pcsx_rearmed_multitap = "disabled"\nsnes9x_x = "1"\n'
        open(graficos.ARQUIVO_OPCOES_CORE, "w", encoding="utf-8").write(original)
        caminho = graficos.gravar_opcoes_de_nucleo_da_partida({"pcsx_rearmed_multitap": "port 1"})
        self.assertEqual(open(graficos.ARQUIVO_OPCOES_CORE, encoding="utf-8").read(), original)
        copia = open(caminho, encoding="utf-8").read()
        self.assertIn('pcsx_rearmed_multitap = "port 1"', copia)
        self.assertNotIn('"disabled"', copia)
        self.assertIn('snes9x_x = "1"', copia)

    def test_devolve_portas_ao_valor_de_antes(self):
        cfg = os.path.join(self.dir, "retroarch.cfg")
        open(cfg, "w", encoding="utf-8").write('a = "1"\ninput_libretro_device_p3 = "1"\n')
        antes = graficos.valores_no_retroarch_cfg(["input_libretro_device_p3", "input_libretro_device_p4"])
        # O RetroArch "fechou" e gravou o que veio da partida de 4 no NES:
        open(cfg, "w", encoding="utf-8").write(
            'a = "1"\ninput_libretro_device_p3 = "513"\ninput_libretro_device_p4 = "513"\n')
        self.assertEqual(graficos.devolver_valores_no_retroarch_cfg(antes), 2)
        texto = open(cfg, encoding="utf-8").read()
        self.assertEqual(texto, 'a = "1"\ninput_libretro_device_p3 = "1"\n')


if __name__ == "__main__":
    unittest.main()
