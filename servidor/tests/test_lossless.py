# -*- coding: utf-8 -*-
"""O perfil "ARENA" do Lossless Scaling (servidor\\lossless.py, item 10).

Tudo com um Settings.xml de mentira numa pasta temporaria: o do dono
(%LOCALAPPDATA%\\Lossless Scaling) nunca e' tocado, e o Lossless Scaling
nunca e' aberto aqui.
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

import lossless  # noqa: E402

PASTA_TESTES = os.path.join(os.path.dirname(PASTA_SERVIDOR), "testes")
if PASTA_TESTES not in sys.path:
    sys.path.insert(0, PASTA_TESTES)
import limpeza  # noqa: E402

# Como o Lossless Scaling 3.2.2 grava (sem BOM, CRLF), com o perfil do dono.
EXEMPLO = "\r\n".join([
    '<?xml version="1.0" encoding="utf-8"?>',
    '<Settings xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
    'xmlns:xsd="http://www.w3.org/2001/XMLSchema">',
    "  <Hotkey>S</Hotkey>",
    "  <GameProfiles>",
    "    <Profile>",
    "      <Title>Padrão</Title>",
    "      <AutoScale>false</AutoScale>",
    "      <ScalingType>Off</ScalingType>",
    "    </Profile>",
    "    <Profile>",
    "      <Title>Do dono</Title>",
    "      <Path>jogo.exe</Path>",
    "      <ScalingType>FSR</ScalingType>",
    "    </Profile>",
    "  </GameProfiles>",
    "</Settings>",
]) + "\r\n"


class Perfil(unittest.TestCase):
    def test_campos_na_ordem_do_lossless(self):
        bloco = lossless.montar_perfil()
        nomes = re.findall(r"<(\w+)>", bloco)[1:]      # tira o <Profile>
        self.assertEqual(nomes, [nome for nome, _ in lossless.CAMPOS_DO_PERFIL])
        self.assertIn("<Title>ARENA</Title>", bloco)
        self.assertIn("<Path>retroarch.exe;pcsx2-qt.exe;Dolphin.exe;", bloco)

    def test_recusa_campo_e_valor_que_o_lossless_nao_tem(self):
        with self.assertRaises(ValueError):
            lossless.montar_perfil({"Nitidez": "5"})
        with self.assertRaises(ValueError):
            lossless.montar_perfil({"ScalingType": "LS2"})
        with self.assertRaises(ValueError):
            lossless.montar_perfil({"AutoScale": "sim"})
        with self.assertRaises(ValueError):
            lossless.montar_perfil({"LSFG3Target": "sessenta"})

    def test_verdadeiro_e_falso_do_python_viram_os_do_lossless(self):
        bloco = lossless.montar_perfil({"DrawFps": True, "HideCursor": False})
        self.assertIn("<DrawFps>true</DrawFps>", bloco)
        self.assertIn("<HideCursor>false</HideCursor>", bloco)

    def test_escolhas_por_jogo(self):
        self.assertEqual(lossless.trocas_para_o_jogo(True, 3)["ScalingType"], "SharpBilinear")
        tres_d = lossless.trocas_para_o_jogo(False, 3)
        self.assertEqual((tres_d["ScalingType"], tres_d["LS1Type"]), ("LS1", "PERFORMANCE"))
        self.assertEqual(lossless.trocas_para_o_jogo(False, 5)["LS1Type"], "BALANCED")
        self.assertNotIn("FrameGeneration", tres_d)
        quadros = lossless.trocas_para_o_jogo(False, 3, mais_quadros=True, hz=75)
        self.assertEqual((quadros["FrameGeneration"], quadros["LSFG3Mode1"], quadros["LSFG3Target"]),
                         ("LSFG3", "ADAPTIVE", "75"))
        lossless.montar_perfil(quadros)          # tudo dentro das listas do LS


class Arquivo(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_teste_lossless_")
        self.arquivo = os.path.join(self.pasta, "Settings.xml")
        with open(self.arquivo, "wb") as saida:
            saida.write(EXEMPLO.encode("utf-8"))
        self.fechado = mock.patch.object(lossless, "processos_abertos", return_value=[])
        self.fechado.start()

    def tearDown(self):
        self.fechado.stop()
        limpeza.apagar_pasta(self.pasta)

    def ler(self):
        with open(self.arquivo, "rb") as entrada:
            return entrada.read()

    def test_so_o_perfil_do_arena_muda(self):
        self.assertEqual(lossless.gravar_perfil({"ScalingType": "LS1"}, self.arquivo)[0], True)
        texto = self.ler().decode("utf-8")
        self.assertIn("<Title>Padrão</Title>", texto)
        self.assertIn("<Title>Do dono</Title>\r\n      <Path>jogo.exe</Path>", texto)
        self.assertEqual(texto.count("<Title>ARENA</Title>"), 1)
        # De novo, com outra escolha: continua um perfil "ARENA" so.
        lossless.gravar_perfil({"ScalingType": "SharpBilinear"}, self.arquivo)
        texto = self.ler().decode("utf-8")
        self.assertEqual(texto.count("<Title>ARENA</Title>"), 1)
        self.assertIn("<ScalingType>SharpBilinear</ScalingType>", texto)
        self.assertEqual(texto.count("<Profile>"), 3)

    def test_jeito_do_lossless_preservado(self):
        lossless.gravar_perfil({}, self.arquivo)
        bruto = self.ler()
        self.assertFalse(bruto.startswith(b"\xef\xbb\xbf"))
        self.assertEqual(bruto.count(b"\n"), bruto.count(b"\r\n"))
        self.assertTrue(bruto.startswith(b'<?xml version="1.0" encoding="utf-8"?>\r\n'))

    def test_copia_de_antes_uma_vez_so(self):
        lossless.gravar_perfil({"ScalingType": "LS1"}, self.arquivo)
        copia = os.path.join(self.pasta, lossless.COPIA_DE_ANTES)
        with open(copia, "rb") as entrada:
            self.assertEqual(entrada.read(), EXEMPLO.encode("utf-8"))
        lossless.gravar_perfil({"ScalingType": "FSR"}, self.arquivo)
        with open(copia, "rb") as entrada:
            self.assertEqual(entrada.read(), EXEMPLO.encode("utf-8"), "a copia e' a de ANTES do ARENA")

    def test_com_o_lossless_aberto_nao_grava(self):
        antes = self.ler()
        with mock.patch.object(lossless, "processos_abertos", return_value=[1234]):
            gravou, motivo = lossless.gravar_perfil({"ScalingType": "LS1"}, self.arquivo)
        self.assertFalse(gravou)
        self.assertIn("aberto", motivo)
        self.assertEqual(self.ler(), antes)

    def test_sem_configuracao_avisa(self):
        os.remove(self.arquivo)
        gravou, motivo = lossless.gravar_perfil({}, self.arquivo)
        self.assertFalse(gravou)
        self.assertIn("abra-o uma vez", motivo)

    def test_lista_de_perfis_vazia(self):
        with open(self.arquivo, "wb") as saida:
            saida.write(EXEMPLO.replace(EXEMPLO[EXEMPLO.index("  <GameProfiles>"):
                                                EXEMPLO.index("</Settings>")],
                                        "  <GameProfiles />\r\n").encode("utf-8"))
        lossless.gravar_perfil({}, self.arquivo)
        self.assertEqual(self.ler().decode("utf-8").count("<Title>ARENA</Title>"), 1)


class Janela(unittest.TestCase):
    """A janela do RetroArch que o Lossless Scaling estica."""

    def test_3d_do_tamanho_do_desenho_no_meio_da_tela(self):
        opcoes = lossless.janela_para_o_lossless("psp", False, 544, (1440, 900))
        self.assertEqual((opcoes["video_windowed_position_width"], opcoes["video_windowed_position_height"]),
                         ("960", "544"))
        self.assertEqual((opcoes["video_windowed_position_x"], opcoes["video_windowed_position_y"]),
                         ("240", "178"))
        # Achado de 17/10/2026: o tamanho exato so vale com "lembrar posicao e tamanho".
        self.assertEqual(opcoes["video_window_save_positions"], "true")
        self.assertEqual((opcoes["video_fullscreen"], opcoes["video_shader_enable"]), ("false", "false"))

    def test_3d_maior_que_3_quartos_da_tela_para_ali(self):
        opcoes = lossless.janela_para_o_lossless("ps1", False, 960, (1440, 900))
        self.assertEqual(opcoes["video_windowed_position_height"], "675")

    def test_2d_em_escala_inteira(self):
        opcoes = lossless.janela_para_o_lossless("snes", True, 240, (1366, 768))
        self.assertEqual((opcoes["video_scale"], opcoes["video_window_save_positions"]), ("2", "false"))


class Partida(unittest.TestCase):
    """arena.preparar_lossless: quando o jogo vai pelo Lossless Scaling."""

    def setUp(self):
        import arena
        self.arena = arena
        self.jogo = {"plataforma": "psp", "core": "ppsspp_libretro.dll"}
        self.achado = {"executavel": "C:\\LS\\LosslessScaling.exe", "origem": "Steam",
                       "versao": "3.2.2.0", "licenca": True}
        self.trocas = [mock.patch.object(lossless, "achar", return_value=self.achado),
                       mock.patch.object(lossless, "gravar_perfil", return_value=(True, "perfil gravado")),
                       mock.patch.object(lossless, "tamanho_da_tela", return_value=(1440, 900)),
                       mock.patch.object(arena.hardware, "altura_da_tela", return_value=900),
                       mock.patch.dict(arena.CAPACIDADE, {"nota": 4, "nota_gpu": 3})]
        for troca in self.trocas:
            troca.start()

    def tearDown(self):
        for troca in reversed(self.trocas):
            troca.stop()

    def config(self, **mudancas):
        base = self.arena.config_padrao()
        base.update({"lossless_scaling": True}, **mudancas)
        return base

    def test_desligado_ou_jogo_de_fora(self):
        self.assertIsNone(self.arena.preparar_lossless(self.jogo, self.config(lossless_scaling=False)))
        self.assertIsNone(self.arena.preparar_lossless(dict(self.jogo, externo={"x": 1}), self.config()))

    def test_sem_o_programa_ou_sem_licenca(self):
        with mock.patch.object(lossless, "achar", return_value=None):
            self.assertIsNone(self.arena.preparar_lossless(self.jogo, self.config()))
        with mock.patch.object(lossless, "achar", return_value=dict(self.achado, licenca=False)):
            self.assertIsNone(self.arena.preparar_lossless(self.jogo, self.config()))

    def test_aberto_pelo_dono_o_jogo_abre_normal(self):
        with mock.patch.object(lossless, "gravar_perfil", return_value=(False, "o Lossless Scaling esta aberto")):
            self.assertIsNone(self.arena.preparar_lossless(self.jogo, self.config()))

    def test_o_caminho_certo(self):
        pronto = self.arena.preparar_lossless(self.jogo, self.config(lossless_mais_quadros=True))
        self.assertEqual(pronto["executavel"], self.achado["executavel"])
        self.assertEqual(pronto["opcoes"]["video_windowed_position_height"], "544")   # PSP 2x na nota 3
        trocas = lossless.gravar_perfil.call_args[0][0]
        self.assertEqual((trocas["ScalingType"], trocas["FrameGeneration"]), ("LS1", "LSFG3"))


class Steam(unittest.TestCase):
    def test_bibliotecas_do_libraryfolders(self):
        pasta = tempfile.mkdtemp(prefix="arena_teste_steam_")
        try:
            os.makedirs(os.path.join(pasta, "steamapps"))
            with open(os.path.join(pasta, "steamapps", "libraryfolders.vdf"), "w", encoding="utf-8") as vdf:
                vdf.write('"libraryfolders"\n{\n\t"0"\n\t{\n\t\t"path"\t\t"%s"\n\t}\n'
                          '\t"1"\n\t{\n\t\t"path"\t\t"D:\\\\Jogos\\\\Steam"\n\t}\n}\n'
                          % pasta.replace("\\", "\\\\"))
            achadas = lossless.bibliotecas_da_steam(pasta)
            self.assertEqual(achadas[0], pasta)
            self.assertIn(os.path.normpath("D:\\Jogos\\Steam"), achadas)
            self.assertEqual(len(achadas), 2, "a principal nao repete")
        finally:
            limpeza.apagar_pasta(pasta)


class SoNoWindows(unittest.TestCase):
    """O Lossless Scaling e' programa do Windows: no Linux (item 13), mesmo
    com a pasta dele no pen drive, o ARENA nao o oferece."""

    @unittest.skipIf(os.name == "nt", "no Windows o Lossless Scaling abre")
    def test_no_linux_nao_acha(self):
        pasta = tempfile.mkdtemp(prefix="arena_teste_ls_linux_")
        try:
            os.makedirs(os.path.join(pasta, "Lossless Scaling"))
            open(os.path.join(pasta, "Lossless Scaling", lossless.EXECUTAVEL), "wb").close()
            self.assertIsNone(lossless.achar(pasta))
            self.assertEqual(lossless.situacao(pasta), {"achado": False})
        finally:
            limpeza.apagar_pasta(pasta)


if __name__ == "__main__":
    unittest.main()
