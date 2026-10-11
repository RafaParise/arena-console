# -*- coding: utf-8 -*-
"""Auditoria 3, Fase 6 (docs\\RELATORIO-QUALIDADE.md): pen drive em FAT32 e
notebook sem driver de video.

O FAT32 nao guarda arquivo maior que 4 GB (menos 1 byte). Antes, so o
VERIFICAR.bat avisava -- e o aluno quase nunca roda. Agora:
  - o "Como colocar jogos" marca os consoles de jogo grande (DVD, Blu-ray)
    e a tela avisa ANTES de copiar, se o ARENA esta num disco FAT32;
  - o cartao do jogo cortado exatamente no limite explica o que houve.

Notebook sem driver de video (o Windows usa o "Adaptador de Video Basico da
Microsoft"): la so o Direct3D 11 funciona -- o Windows desenha por
processador (WARP). O OpenGL que ele oferece e' o 1.1, e o "glcore" do
RetroArch precisa do 3.2: com ele o jogo abre e fecha. Vulkan nao existe sem
driver. O motor automatico precisa cair no d3d11, nunca no glcore.
"""
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

import arena  # noqa: E402
import como_colocar  # noqa: E402
import indexador  # noqa: E402


class TestFat32(unittest.TestCase):

    def test_jogo_cortado_no_limite_do_fat32_tem_aviso(self):
        aviso = indexador.aviso_de_arquivo_cortado(4 * 1024 ** 3 - 1)
        self.assertIsNotNone(aviso)
        self.assertIn("FAT32", aviso["texto"])
        self.assertIn("exFAT", aviso["texto"])

    def test_outros_tamanhos_nao_tem_aviso(self):
        for tamanho in (0, 4 * 1024 ** 3 - 2, 4 * 1024 ** 3, 5 * 1024 ** 3, 700 * 1024 ** 2):
            self.assertIsNone(indexador.aviso_de_arquivo_cortado(tamanho), tamanho)

    def test_consoles_de_jogo_grande_vem_marcados(self):
        pasta = tempfile.mkdtemp(prefix="arena_fat32_teste_")
        try:
            guia = {c["id"]: c for c in como_colocar.guia(arena.carregar_catalogo(), pasta, pasta,
                                                           {"ps2": "", "ps3": ""})}
        finally:
            shutil.rmtree(pasta, ignore_errors=True)
        for console in ("ps2", "ps3", "wii", "xbox360"):
            self.assertTrue(guia[console]["jogo_grande"], console)
        for console in ("snes", "ps1", "megadrive", "gamecube", "psp"):
            if console in guia:
                self.assertFalse(guia[console]["jogo_grande"], console)


def bibliotecas_que_carregam(*nomes):
    """Imita o Windows: so as bibliotecas de 'nomes' existem."""
    def carregar(nome, *args, **kwargs):
        if nome in nomes:
            return object()
        raise OSError("nao achei %s" % nome)
    return carregar


class TestNotebookSemDriverDeVideo(unittest.TestCase):

    def test_sem_vulkan_o_automatico_vai_para_d3d11(self):
        import hardware
        with mock.patch.object(hardware.ctypes, "CDLL", bibliotecas_que_carregam("d3d11.dll")):
            self.assertEqual(hardware.driver_video(), "d3d11")

    def test_glcore_so_quando_nem_o_d3d11_existe(self):
        import hardware
        with mock.patch.object(hardware.ctypes, "CDLL", bibliotecas_que_carregam()):
            self.assertEqual(hardware.driver_video(), "glcore")

    def test_vulkan_que_sobrou_sem_placa_troca_para_d3d11(self):
        # O vulkan-1.dll carrega (sobra de outra placa), mas o Vulkan nao
        # enxerga placa nenhuma -- o caso do adaptador basico com o arquivo
        # esquecido. Antes do primeiro jogo, o motor vira d3d11.
        antes = arena.MAQUINA.get("driver_video")
        try:
            arena.MAQUINA["driver_video"] = "vulkan"
            with mock.patch.object(arena.hardware, "vulkan_tem_placa", return_value=False), \
                    mock.patch("ctypes.CDLL", bibliotecas_que_carregam("d3d11.dll")):
                arena.conferir_vulkan()
            self.assertEqual(arena.MAQUINA["driver_video"], "d3d11")
        finally:
            arena.MAQUINA["driver_video"] = antes

    def test_vulkan_que_nao_sabe_responder_nao_muda_nada(self):
        antes = arena.MAQUINA.get("driver_video")
        try:
            arena.MAQUINA["driver_video"] = "vulkan"
            with mock.patch.object(arena.hardware, "vulkan_tem_placa", return_value=None):
                arena.conferir_vulkan()
            self.assertEqual(arena.MAQUINA["driver_video"], "vulkan")
        finally:
            arena.MAQUINA["driver_video"] = antes


class TestCaminhosDoRetroarchCfgDepoisDeMudarDeLugar(unittest.TestCase):
    """graficos.corrigir_caminhos_retroarch_cfg com a pasta mudando de lugar.

    Achado de 11/10/2026: a versao dos alunos subiu de ...\\ARENA\\ARENA-alunos
    para ...\\ARENA; 7 linhas do retroarch.cfg (historico, favoritos,
    playlists, log) continuaram em ...\\ARENA\\ARENA-alunos\\dados, porque o
    caminho velho "comeca com" o novo."""

    def setUp(self):
        import graficos
        self.graficos = graficos
        self.antes = (graficos.RAIZ, graficos.PASTA_RETROARCH)
        self.base = tempfile.mkdtemp(prefix="arena_cfg_lugar_")
        self.raiz = os.path.join(self.base, "ARENA")
        os.makedirs(os.path.join(self.raiz, "retroarch"))
        os.makedirs(os.path.join(self.raiz, "BIOS"))
        graficos.RAIZ = self.raiz
        graficos.PASTA_RETROARCH = os.path.join(self.raiz, "retroarch")

    def tearDown(self):
        self.graficos.RAIZ, self.graficos.PASTA_RETROARCH = self.antes
        shutil.rmtree(self.base, ignore_errors=True)

    def corrigir(self, linhas):
        cfg = os.path.join(self.raiz, "retroarch", "retroarch.cfg")
        with open(cfg, "w", encoding="utf-8") as f:
            for chave, valor in linhas.items():
                f.write('%s = "%s"\n' % (chave, valor))
        self.graficos.corrigir_caminhos_retroarch_cfg()
        valores = {}
        with open(cfg, encoding="utf-8") as f:
            for linha in f:
                if "=" in linha:
                    chave, valor = linha.split("=", 1)
                    valores[chave.strip()] = valor.strip().strip('"')
        return valores

    def test_pasta_que_subiu_um_nivel(self):
        r = self.raiz
        valores = self.corrigir({
            "content_favorites_path": os.path.join(r, "ARENA-alunos", "dados", "builtin", "content_favorites.lpl"),
            "playlist_directory": os.path.join(r, "ARENA-alunos", "dados"),
        })
        self.assertEqual(valores["content_favorites_path"],
                         os.path.join(r, "dados", "builtin", "content_favorites.lpl"))
        self.assertEqual(valores["playlist_directory"], os.path.join(r, "dados"))

    def test_pasta_irma_com_o_comeco_do_nome_igual(self):
        valores = self.corrigir({"log_dir": os.path.join(self.base, "ARENA-velho", "dados")})
        self.assertEqual(valores["log_dir"], os.path.join(self.raiz, "dados"))

    def test_pasta_de_cima_com_nome_de_pasta_do_arena(self):
        valores = self.corrigir({
            "savestate_directory": "D:\\dados\\ARENA\\retroarch\\states",
            "content_history_path": "D:\\jogos\\ARENA\\dados\\builtin\\content_history.lpl",
        })
        self.assertEqual(valores["savestate_directory"], os.path.join(self.raiz, "retroarch", "states"))
        self.assertEqual(valores["content_history_path"],
                         os.path.join(self.raiz, "dados", "builtin", "content_history.lpl"))

    def test_o_que_ja_esta_certo_nao_muda(self):
        certos = {
            "savefile_directory": os.path.join(self.raiz, "retroarch", "saves"),
            "rgui_browser_directory": os.path.join(self.raiz, "BIOS"),   # existe, nao e' da lista
            "system_directory": ":\\system",                              # forma do proprio RetroArch
        }
        valores = self.corrigir(certos)
        for chave, valor in certos.items():
            self.assertEqual(valores[chave], valor, chave)


if __name__ == "__main__":
    unittest.main()
