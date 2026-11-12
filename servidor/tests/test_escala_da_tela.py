# -*- coding: utf-8 -*-
"""Escala da tela: o filtro que estica o jogo ate a tela (item 10, 17/10/2026).

O pedido do Rafael (15/10/2026): todo jogo abre em tela cheia, desenhado no
tamanho que o computador aguenta e "redimensionado, bonito, perfeitamente
desenhado", como o Lossless Scaling. A regra (graficos.jeito_da_escala),
tirada das medicoes de 16/10 (docs\\escala_antes_bruto.json):
  - desenho 2D: pixel nitido, em todo nivel, inclusive o grafico original;
  - 3D desenhado menor que a tela: FSR na placa boa, Catmull-Rom na media e
    so a nitidez (RCAS) na fraca e nos modos de folga;
  - 3D do tamanho da tela ou maior: sem filtro;
  - nivel minimo e a escolha "Original": sem filtro.
"""
import os
import re
import sys
import tempfile
import unittest
from unittest import mock

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PASTA_SERVIDOR not in sys.path:
    sys.path.insert(0, PASTA_SERVIDOR)

import arena  # noqa: E402
import graficos  # noqa: E402

PASTA_TESTES = os.path.join(os.path.dirname(PASTA_SERVIDOR), "testes")
if PASTA_TESTES not in sys.path:
    sys.path.insert(0, PASTA_TESTES)
import limpeza  # noqa: E402

SHADERS = os.path.join(os.path.dirname(PASTA_SERVIDOR), "retroarch", "shaders", "shaders_slang")


class AlturaInterna(unittest.TestCase):
    def test_cada_nucleo(self):
        casos = [
            ("swanstation", {"swanstation_GPU_ResolutionScale": "4"}, 960),
            ("swanstation", {}, 240),
            ("ppsspp", {"ppsspp_internal_resolution": "960x544"}, 544),
            ("mupen64plus_next", {"mupen64plus-EnableNativeResFactor": "2"}, 480),
            ("mupen64plus_next", {"mupen64plus-rdp-plugin": "parallel",
                                  "mupen64plus-parallel-rdp-upscaling": "2x",
                                  "mupen64plus-EnableNativeResFactor": "3"}, 480),
            ("flycast", {"reicast_internal_resolution": "640x480"}, 480),
            ("melonds", {"melonds_opengl_renderer": "enabled",
                         "melonds_opengl_resolution": "2x native (512x384)"}, 768),
            ("melonds", {"melonds_opengl_renderer": "disabled"}, 384),
            ("dolphin", {"dolphin_efb_scale": "x2 (1280 x 1056)"}, 1056),
            ("pcsx2", {"pcsx2_upscale_multiplier": "2"}, 896),
            ("mednafen_saturn", {}, 240),
            ("nao_conhecido", {}, 0),
        ]
        for nucleo, opcoes, esperado in casos:
            with self.subTest(nucleo=nucleo, opcoes=opcoes):
                self.assertEqual(graficos.altura_interna(nucleo, opcoes), esperado)

    def test_opcoes_finais_iguais_as_do_arquivo(self):
        # A conta da escala usa as MESMAS opcoes que o arquivo dos nucleos.
        for nota_gpu in (1, 3, 4, 5):
            opcoes = graficos.opcoes_finais_do_nucleo("ppsspp", 4, nota_gpu, altura_tela=900)
            self.assertIn("ppsspp_internal_resolution", opcoes)


class Regra(unittest.TestCase):
    def jeito(self, plataforma, **resto):
        return graficos.jeito_da_escala(plataforma, **resto)

    def test_2d_e_sempre_pixel_nitido(self):
        for folga in (False, True):
            for nota in (1, 3, 5):
                self.assertEqual(self.jeito("snes", nota_gpu=nota, folga=folga), "pixel")
        self.assertEqual(self.jeito("j2me"), "pixel")

    def test_3d_menor_que_a_tela_pela_placa(self):
        psp = {"nome_curto": "ppsspp", "opcoes_nucleo": {"ppsspp_internal_resolution": "960x544"},
               "altura_tela": 900}
        self.assertEqual(self.jeito("psp", nota_gpu=5, **psp), "nitido")
        self.assertEqual(self.jeito("psp", nota_gpu=4, **psp), "nitido")
        self.assertEqual(self.jeito("psp", nota_gpu=3, **psp), "catmull")
        self.assertEqual(self.jeito("psp", nota_gpu=2, **psp), "rcas")
        self.assertEqual(self.jeito("psp", nota_gpu=5, folga=True, **psp), "rcas")

    def test_3d_do_tamanho_da_tela_fica_sem_filtro(self):
        ps1_4x = {"nome_curto": "swanstation",
                  "opcoes_nucleo": {"swanstation_GPU_ResolutionScale": "4"}}
        self.assertEqual(self.jeito("ps1", altura_tela=900, nota_gpu=4, **ps1_4x), "")
        # Na tela 4K, o mesmo 4x e' pequeno: estica.
        self.assertEqual(self.jeito("ps1", altura_tela=2160, nota_gpu=4, **ps1_4x), "nitido")

    def test_escolhas_do_aluno(self):
        self.assertEqual(self.jeito("snes", escolha="original"), "")
        self.assertEqual(self.jeito("snes", escolha="nitido"), "nitido")
        self.assertEqual(self.jeito("snes", escolha="suave"), "suave")
        self.assertEqual(self.jeito("ps1", escolha="suave"), "nitido")
        self.assertEqual(self.jeito("ps1", escolha="pixel"), "pixel")
        # Console que o nucleo ja desenha grande (Vectrex): nada, nem pedido.
        self.assertEqual(self.jeito("vectrex", escolha="nitido"), "")
        self.assertEqual(self.jeito(None), "")
        # As funcoes do Lossless que faltavam (22/10/2026): o Anime4K e o
        # Inteiro (este sem filtro: e' a escala inteira do RetroArch).
        self.assertEqual(self.jeito("snes", escolha="anime4k"), "anime4k")
        self.assertEqual(self.jeito("ps1", escolha="anime4k"), "anime4k")
        self.assertEqual(self.jeito("snes", escolha="inteiro"), "")


class Presets(unittest.TestCase):
    @unittest.skipUnless(os.path.isdir(SHADERS), "sem o pacote de shaders do RetroArch")
    def test_todo_preset_do_arena_acha_o_shader(self):
        for jeito in graficos.ARQUIVOS_DOS_FILTROS:
            with self.subTest(jeito=jeito):
                self.assertTrue(graficos.caminho_do_filtro(jeito), jeito)

    def test_fsr_sem_grao_de_filme(self):
        with open(os.path.join(graficos.PASTA_FILTROS, "fsr.slangp"), encoding="utf-8") as preset:
            self.assertIn('FSR_FILMGRAIN = "0.000000"', preset.read())

    def test_jeito_desconhecido(self):
        self.assertEqual(graficos.caminho_do_filtro("crt"), "")
        self.assertEqual(graficos.caminho_do_filtro(""), "")


class SgsrENitidez(unittest.TestCase):
    """12/11/2026: o SGSR da Qualcomm (so por escolha) e a nitidez ajustavel (50 = a de sempre)."""

    def test_sgsr_so_por_escolha(self):
        self.assertEqual(graficos.jeito_da_escala("ps1", "sgsr", "swanstation", {}, 900, 3), "sgsr")
        self.assertEqual(graficos.jeito_da_escala("snes", "sgsr"), "sgsr")
        for nota in (1, 2, 3, 4, 5):   # o automatico nao mudou: nunca escolhe o SGSR sozinho
            self.assertNotEqual(graficos.jeito_da_escala("ps1", "automatico", "swanstation", {}, 900, nota), "sgsr")
        preset = os.path.join(graficos.PASTA_FILTROS, "sgsr.slangp")
        shader = os.path.join(graficos.PASTA_FILTROS, "sgsr", "sgsr1.slang")
        self.assertTrue(os.path.isfile(shader) and os.path.isfile(os.path.join(graficos.PASTA_FILTROS, "sgsr", "LICENSE.txt")))
        self.assertEqual(graficos.caminho_do_filtro("sgsr"), preset)
        texto = open(shader, encoding="utf-8").read()
        self.assertIn("BSD-3-Clause", texto)
        self.assertIn("#pragma parameter SGSR_NITIDEZ", texto)

    def test_conta_da_nitidez(self):
        conta = graficos.valor_da_nitidez

        def arredondado(jeito, nitidez):
            nome, valor = conta(jeito, nitidez)
            return nome, round(valor, 6)
        graficos_valor = arredondado
        self.assertEqual(graficos_valor("rcas", 50), ("RCAS_STRENGTH", 0.5))     # o padrao do RCAS
        self.assertEqual(graficos_valor("nitido", 50), ("FSR_SHARPENING", 0.2))  # o fsr.slangp de sempre
        self.assertEqual(graficos_valor("sgsr", 50), ("SGSR_NITIDEZ", 2.0))      # o padrao do SGSR
        self.assertEqual(graficos_valor("rcas", 100), ("RCAS_STRENGTH", 1.0))
        self.assertEqual(graficos_valor("nitido", 100), ("FSR_SHARPENING", 0.0))  # no FSR, menor afia mais
        self.assertEqual(graficos_valor("nitido", 0), ("FSR_SHARPENING", 2.0))
        self.assertEqual(graficos_valor("sgsr", 250), ("SGSR_NITIDEZ", 3.0))     # fora da faixa: o limite
        self.assertIsNone(graficos.valor_da_nitidez("pixel", 80))

    def test_nitidez_de_sempre_nao_muda_nada(self):
        fsr = os.path.join(graficos.PASTA_FILTROS, "fsr.slangp")
        for n in (50, "x", None):
            self.assertEqual(graficos.filtro_com_nitidez(fsr, "nitido", n, tempfile.gettempdir()), fsr)
        pixel = os.path.join(graficos.PASTA_FILTROS, "pixel-nitido.slangp")
        self.assertEqual(graficos.filtro_com_nitidez(pixel, "pixel", 90, tempfile.gettempdir()), pixel)
        self.assertEqual(graficos.filtro_com_nitidez("", "rcas", 90, tempfile.gettempdir()), "")

    def test_copia_com_a_nitidez(self):
        raiz = tempfile.mkdtemp(prefix="arena_nitidez_")
        try:
            filtros, dados = os.path.join(raiz, "servidor", "filtros"), os.path.join(raiz, "dados", "filtros")
            os.makedirs(filtros)
            citado = os.path.join(raiz, "retroarch", "fsr.slangp")
            os.makedirs(os.path.dirname(citado))
            open(citado, "w").close()
            preset = os.path.join(filtros, "fsr.slangp")
            with open(preset, "w", encoding="utf-8") as arquivo:
                arquivo.write('#reference "../../retroarch/fsr.slangp"\nFSR_SHARPENING = "0.200000"\n')
            copia = graficos.filtro_com_nitidez(preset, "nitido", 100, dados)
            self.assertEqual(copia, os.path.join(dados, "fsr-nitidez-100.slangp"))
            texto = open(copia, encoding="utf-8").read()
            self.assertIn('FSR_SHARPENING = "0.000000"', texto)
            self.assertNotIn("0.200000", texto)
            self.assertIn('#reference "../../retroarch/fsr.slangp"', texto)
            # Pasta de dados em outra altura (o caminho relativo nao acharia o shader): vale o preset de sempre.
            self.assertEqual(graficos.filtro_com_nitidez(preset, "nitido", 100, os.path.join(raiz, "a", "b", "c")), preset)
        finally:
            limpeza.apagar_pasta(raiz)


@unittest.skipUnless(os.path.isdir(SHADERS), "sem o pacote de shaders do RetroArch")
class ArquivoDaPartida(unittest.TestCase):
    """O arquivo de opcoes de verdade (gravar_override), numa pasta temporaria."""

    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_teste_escala_")
        pastas = {nome: os.path.join(self.pasta, nome.lower()) for nome in (
            "PASTA_DADOS", "PASTA_SAVES", "PASTA_STATES", "PASTA_CAPTURAS", "PASTA_CHEATS",
            "PASTA_REMAPS", "PASTA_CACHE")}
        pastas["ARQUIVO_OVERRIDE"] = os.path.join(self.pasta, "arena_override.cfg")
        self.trocas = [mock.patch.multiple(arena, **pastas),
                       mock.patch.object(arena.hardware, "altura_da_tela", return_value=900),
                       mock.patch.dict(arena.CAPACIDADE, {"nota": 4, "nota_gpu": 3})]
        for troca in self.trocas:
            troca.start()

    def tearDown(self):
        for troca in reversed(self.trocas):
            troca.stop()
        limpeza.apagar_pasta(self.pasta)

    def partida(self, plataforma, nucleo, em_partida=False, **config):
        base = arena.config_padrao()
        base.update(config)
        caminho, filtro = arena.gravar_override(base, 2, plataforma=plataforma, devolver_filtro=True,
                                                nucleo=nucleo, em_partida=em_partida)
        with open(caminho, encoding="utf-8") as arquivo:
            opcoes = dict(re.findall(r'^([a-z0-9_]+) = "([^"]*)"', arquivo.read(), re.M))
        return os.path.basename(filtro) if filtro else "", opcoes

    def test_snes_com_pixel_nitido_em_todo_nivel(self):
        for config in ({}, {"perfil_grafico": "desempenho"}, {"ultra_desempenho": True},
                       {"modo_modesto": True}, {"abaixo_do_original": "leve"}):
            with self.subTest(config=config):
                filtro, opcoes = self.partida("snes", "snes9x_libretro.dll", **config)
                self.assertEqual(filtro, "pixel-nitido.slangp")
                self.assertEqual(opcoes["video_shader_enable"], "true")

    def test_psp_na_placa_media_e_no_ultra(self):
        self.assertEqual(self.partida("psp", "ppsspp_libretro.dll")[0], "catmull-rom.slangp")
        filtro, opcoes = self.partida("psp", "ppsspp_libretro.dll", ultra_desempenho=True)
        self.assertEqual(filtro, "rcas.slangp")
        self.assertEqual(opcoes["video_smooth"], "true", "o RCAS estica pelo bilinear")
        self.assertEqual(self.partida("psp", "ppsspp_libretro.dll", em_partida=True)[0], "rcas.slangp")

    def test_ps1_com_rcas_sem_video_em_thread(self):
        # Achado de 22/10/2026: o SwanStation fechava sozinho com o RCAS e a
        # thread (graficos.NUCLEOS_RCAS_SEM_THREAD). O PSP continua com ela.
        filtro, opcoes = self.partida("ps1", "swanstation_libretro.dll", modo_modesto=True)
        self.assertEqual(filtro, "rcas.slangp")       # no modesto, o PS1 desenha 1x e estica
        self.assertEqual(opcoes["video_threaded"], "false")
        filtro, opcoes = self.partida("psp", "ppsspp_libretro.dll", em_partida=True)
        self.assertEqual(filtro, "rcas.slangp")
        self.assertEqual(opcoes["video_threaded"], "true")

    def test_ps1_ja_do_tamanho_da_tela(self):
        filtro, opcoes = self.partida("ps1", "swanstation_libretro.dll")
        self.assertEqual(filtro, "")             # 4x = 960 linhas, a tela tem 900
        self.assertEqual(opcoes["video_shader_enable"], "false")

    def test_minimo_e_original_sem_filtro(self):
        for config in ({"abaixo_do_original": "minimo"}, {"escala_da_tela": "original"}):
            with self.subTest(config=config):
                filtro, opcoes = self.partida("snes", "snes9x_libretro.dll", **config)
                self.assertEqual(filtro, "")
                self.assertEqual(opcoes["video_shader_enable"], "false")

    def test_o_filtro_de_tela_antigo_nao_manda_mais(self):
        # O "Filtro de tela" saiu dos Ajustes avancados: quem ficou com ele
        # desligado (o computador do professor) ganha a escala do mesmo jeito.
        filtro, _ = self.partida("snes", "snes9x_libretro.dll", avancado={"video_shader_enable": "false"})
        self.assertEqual(filtro, "pixel-nitido.slangp")

    def test_anime4k_e_inteiro(self):
        # Conferidos de verdade em 22/10/2026 (MSX, 1440x900): o Anime4K
        # compila sem erro e enche a tela; o Inteiro deixa a borda preta.
        filtro, opcoes = self.partida("snes", "snes9x_libretro.dll", escala_da_tela="anime4k")
        self.assertEqual(filtro, "anime4k.slangp")
        self.assertEqual(opcoes["video_scale_integer"], "false")
        filtro, opcoes = self.partida("snes", "snes9x_libretro.dll", escala_da_tela="inteiro")
        self.assertEqual(filtro, "")
        self.assertEqual(opcoes["video_scale_integer"], "true")
        self.assertEqual(opcoes["video_shader_enable"], "false")


class Configuracao(unittest.TestCase):
    def test_padrao_e_lista(self):
        self.assertEqual(arena.config_padrao()["escala_da_tela"], "automatico")
        self.assertEqual(graficos.ESCALAS[0], "automatico")
        self.assertNotIn("video_shader_enable", {r["chave"] for r in arena.carregar_recursos()["recursos"]})


if __name__ == "__main__":
    unittest.main()
