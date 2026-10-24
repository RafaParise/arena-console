# -*- coding: utf-8 -*-
"""Formato da imagem: esticar ate a borda ou a proporcao do console (22/10/2026).

O pedido do Rafael: "a tela nao mais esta esticando ate a borda da tela como
fazia antes, entao precisa ser verificado". O RetroArch usa a proporcao do
console (o 4:3 com faixas pretas dos lados na tela larga), e o perfil "ARENA"
do Lossless Scaling usava o modo "Aspect ratio". A regra
(graficos.proporcao_da_partida):
  - "automatico": os consoles de TV e de computador (graficos.json ->
    formato_da_imagem) esticam ate a borda; numa tela mais larga que 16:9
    (o celular deitado), so ate 16:9; os portateis de tela quadrada, o
    fliperama e quem tem jogo em pe ficam na proporcao do nucleo;
  - "esticar": todo jogo ate a borda; "console": sempre a do nucleo.
Conferido de verdade no RetroArch 1.22.2 em 22/10/2026 (foto da tela de
1440x900): o 24 enche a tela de borda a borda, o 22 deixa o 4:3 no meio.
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
import lossless  # noqa: E402

PASTA_TESTES = os.path.join(os.path.dirname(PASTA_SERVIDOR), "testes")
if PASTA_TESTES not in sys.path:
    sys.path.insert(0, PASTA_TESTES)
import limpeza  # noqa: E402

MONITOR = (1440, 900)        # 16:10, o computador do professor
CELULAR = (2400, 1080)       # 20:9, deitado


class Regra(unittest.TestCase):
    def indice(self, plataforma, formato, tela):
        return graficos.proporcao_da_partida(plataforma, formato, tela)["aspect_ratio_index"]

    def test_automatico_estica_o_4_3_de_tv_ate_a_borda(self):
        for plataforma in ("nes", "snes", "megadrive", "ps1", "n64", "ps2", "gamecube"):
            with self.subTest(plataforma=plataforma):
                self.assertEqual(self.indice(plataforma, "automatico", MONITOR), graficos.PROPORCAO_TELA_CHEIA)
                self.assertEqual(self.indice(plataforma, "automatico", (1366, 768)), graficos.PROPORCAO_TELA_CHEIA)

    def test_no_celular_deitado_so_ate_16_9(self):
        chaves = graficos.proporcao_da_partida("snes", "automatico", CELULAR)
        self.assertEqual(chaves["aspect_ratio_index"], graficos.PROPORCAO_CONFIG)
        self.assertEqual(chaves["video_aspect_ratio"], "1.7778")

    def test_automatico_nao_deforma_portatil_nem_fliperama(self):
        for plataforma in ("gameboy", "gba", "ngp", "arcade", "wonderswan", "vectrex", "psp", "nds"):
            with self.subTest(plataforma=plataforma):
                self.assertEqual(self.indice(plataforma, "automatico", MONITOR), graficos.PROPORCAO_DO_NUCLEO)

    def test_tela_desconhecida_ou_em_pe_fica_no_formato_do_console(self):
        self.assertEqual(self.indice("snes", "automatico", (0, 0)), graficos.PROPORCAO_DO_NUCLEO)
        self.assertEqual(self.indice("snes", "automatico", None), graficos.PROPORCAO_DO_NUCLEO)
        self.assertEqual(self.indice("snes", "automatico", (1080, 1920)), graficos.PROPORCAO_DO_NUCLEO)

    def test_escolhas_do_aluno(self):
        self.assertEqual(self.indice("gameboy", "esticar", MONITOR), graficos.PROPORCAO_TELA_CHEIA)
        self.assertEqual(self.indice("gameboy", "esticar", CELULAR), graficos.PROPORCAO_TELA_CHEIA)
        self.assertEqual(self.indice("snes", "console", MONITOR), graficos.PROPORCAO_DO_NUCLEO)
        for formato in graficos.FORMATOS:
            with self.subTest(formato=formato):
                chaves = graficos.proporcao_da_partida("snes", formato, MONITOR)
                self.assertEqual(chaves["video_aspect_ratio_auto"], "false",
                                 "com o automatico do RetroArch ligado, o indice nao vale")

    def test_a_lista_so_tem_consoles_que_existem(self):
        import json
        with open(os.path.join(PASTA_SERVIDOR, "consoles.json"), encoding="utf-8") as arquivo:
            ids = {p["id"] for p in json.load(arquivo)["plataformas"]}
        lista = graficos.regra_do_formato()["esticar_no_automatico"]
        self.assertEqual(sorted(set(lista) - ids), [])
        self.assertEqual(len(lista), len(set(lista)), "console repetido na lista")

    def test_emuladores_de_fora_pela_mesma_regra(self):
        self.assertEqual(graficos.formato_de_fora("ps2", "automatico", MONITOR), "esticar")
        self.assertEqual(graficos.formato_de_fora("ps2", "automatico", CELULAR), "16:9")
        self.assertEqual(graficos.formato_de_fora("ps3", "automatico", MONITOR), "console")
        self.assertEqual(graficos.formato_de_fora("ps3", "esticar", MONITOR), "esticar")
        self.assertEqual(graficos.formato_de_fora("gamecube", "console", MONITOR), "console")


class ArquivoDaPartida(unittest.TestCase):
    """O arquivo de opcoes de verdade (gravar_override), numa pasta temporaria."""

    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_teste_formato_")
        pastas = {nome: os.path.join(self.pasta, nome.lower()) for nome in (
            "PASTA_DADOS", "PASTA_SAVES", "PASTA_STATES", "PASTA_CAPTURAS", "PASTA_CHEATS",
            "PASTA_REMAPS", "PASTA_CACHE")}
        pastas["ARQUIVO_OVERRIDE"] = os.path.join(self.pasta, "arena_override.cfg")
        self.tela = mock.patch.object(arena.hardware, "tamanho_da_tela", return_value=MONITOR)
        self.trocas = [mock.patch.multiple(arena, **pastas), self.tela,
                       mock.patch.object(arena.hardware, "altura_da_tela", return_value=900),
                       mock.patch.dict(arena.CAPACIDADE, {"nota": 4, "nota_gpu": 3})]
        for troca in self.trocas:
            troca.start()

    def tearDown(self):
        for troca in reversed(self.trocas):
            troca.stop()
        limpeza.apagar_pasta(self.pasta)

    def opcoes(self, plataforma, nucleo, **config):
        base = arena.config_padrao()
        base.update(config)
        caminho = arena.gravar_override(base, 2, plataforma=plataforma, nucleo=nucleo)
        with open(caminho, encoding="utf-8") as arquivo:
            return dict(re.findall(r'^([a-z0-9_]+) = "([^"]*)"', arquivo.read(), re.M))

    def test_padrao_estica_o_super_nintendo(self):
        opcoes = self.opcoes("snes", "snes9x_libretro.dll")
        self.assertEqual(opcoes["aspect_ratio_index"], graficos.PROPORCAO_TELA_CHEIA)
        self.assertEqual(opcoes["video_aspect_ratio_auto"], "false")
        self.assertEqual(opcoes["video_scale_integer"], "false")

    def test_em_todo_nivel_e_perfil(self):
        for config in ({"ultra_desempenho": True}, {"modo_modesto": True}, {"abaixo_do_original": "minimo"},
                       {"escala_da_tela": "original"}, {"perfil_grafico": "desempenho"}):
            with self.subTest(config=config):
                self.assertEqual(self.opcoes("snes", "snes9x_libretro.dll", **config)["aspect_ratio_index"],
                                 graficos.PROPORCAO_TELA_CHEIA)

    def test_do_console_e_game_boy(self):
        self.assertEqual(self.opcoes("snes", "snes9x_libretro.dll", formato_da_imagem="console")
                         ["aspect_ratio_index"], graficos.PROPORCAO_DO_NUCLEO)
        self.assertEqual(self.opcoes("gameboy", "gambatte_libretro.dll")["aspect_ratio_index"],
                         graficos.PROPORCAO_DO_NUCLEO)

    def test_tela_de_celular(self):
        self.tela.stop()
        with mock.patch.object(arena.hardware, "tamanho_da_tela", return_value=CELULAR):
            opcoes = self.opcoes("snes", "snes9x_libretro.dll")
        self.tela.start()
        self.assertEqual(opcoes["aspect_ratio_index"], graficos.PROPORCAO_CONFIG)
        self.assertEqual(opcoes["video_aspect_ratio"], "1.7778")


class Configuracao(unittest.TestCase):
    def test_padrao_e_lista(self):
        with mock.patch.object(arena.plataforma_do_sistema, "ANDROID", False):
            self.assertEqual(arena.config_padrao()["formato_da_imagem"], "automatico")
        self.assertEqual(graficos.FORMATOS[0], "automatico")

    def test_no_android_o_padrao_e_tela_cheia_de_verdade(self):
        # Pedido de 23/10/2026: "sempre tela cheia, a nao ser que va nas configuracoes".
        with mock.patch.object(arena.plataforma_do_sistema, "ANDROID", True):
            padrao = arena.config_padrao()["formato_da_imagem"]
        self.assertEqual(padrao, "esticar")
        # no celular deitado (20:9), a partida vai ate a borda, sem o limite de 16:9
        for plataforma in ("snes", "gba", "arcade", "psp", "ps1"):
            self.assertEqual(graficos.proporcao_da_partida(plataforma, padrao, CELULAR)["aspect_ratio_index"],
                             graficos.PROPORCAO_TELA_CHEIA, plataforma)
        # e quem escolhe outro nos Ajustes continua tendo o que escolheu
        self.assertEqual(graficos.proporcao_da_partida("snes", "console", CELULAR)["aspect_ratio_index"],
                         graficos.PROPORCAO_DO_NUCLEO)


class EmuladoresDeFora(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_teste_formato_fora_")

    def tearDown(self):
        limpeza.apagar_pasta(self.pasta)

    def test_pcsx2(self):
        os.makedirs(os.path.join(self.pasta, "inis"))
        exe = os.path.join(self.pasta, "pcsx2-qt.exe")
        ini = os.path.join(self.pasta, "inis", "PCSX2.ini")
        for formato, esperado in (("esticar", ["Stretch"]), ("16:9", ["16:9"]), ("console", ["Auto 4:3/3:2"]),
                                  (None, ["10:7"])):
            with self.subTest(formato=formato):
                with open(ini, "w", encoding="utf-8") as arquivo:
                    arquivo.write("[EmuCore/GS]\nAspectRatio = 10:7\n")
                graficos.escrever_config_pcsx2(exe, nota=4, nota_gpu=3, integrada=True, formato=formato)
                with open(ini, encoding="utf-8") as arquivo:
                    self.assertEqual(re.findall(r"^AspectRatio = (.+)$", arquivo.read(), re.M), esperado)

    def test_dolphin(self):
        for formato, esperado in (("esticar", "3"), ("16:9", "1"), ("console", "0")):
            with self.subTest(formato=formato):
                gfx = graficos.opcoes_de_imagem_dolphin(4, 3, formato=formato)["GFX.ini"]["Settings"]
                self.assertEqual(gfx["AspectRatio"], esperado)
        self.assertNotIn("AspectRatio", graficos.opcoes_de_imagem_dolphin(4, 3)["GFX.ini"]["Settings"])

    def test_rpcs3(self):
        os.makedirs(os.path.join(self.pasta, "config"))
        exe = os.path.join(self.pasta, "rpcs3.exe")
        yml = os.path.join(self.pasta, "config", "config.yml")
        for formato, esperado in (("esticar", "true"), ("console", "false"), (None, "false")):
            with self.subTest(formato=formato):
                with open(yml, "w", encoding="utf-8") as arquivo:
                    arquivo.write("Video:\n  Resolution Scale: 100\n  Output Scaling Mode: Bilinear\n"
                                  "  Stretch To Display Area: false\nMiscellaneous:\n"
                                  "  Start games in fullscreen mode: false\n")
                graficos.escrever_config_rpcs3(exe, 4, 3, formato=formato)
                with open(yml, encoding="utf-8") as arquivo:
                    self.assertEqual(re.findall(r"^  Stretch To Display Area: (\w+)$", arquivo.read(), re.M),
                                     [esperado])


class Lossless(unittest.TestCase):
    def test_esticar_vira_tela_cheia_no_perfil(self):
        self.assertEqual(lossless.trocas_para_o_jogo(False, 3)["ScalingFitMode"], "AspectRatio")
        self.assertEqual(lossless.trocas_para_o_jogo(False, 3, esticar=True)["ScalingFitMode"], "Fullscreen")
        for esticar in (False, True):
            valor = lossless.trocas_para_o_jogo(True, 4, esticar=esticar)["ScalingFitMode"]
            self.assertIn(valor, lossless.VALORES_ACEITOS["ScalingFitMode"])


if __name__ == "__main__":
    unittest.main()
