# -*- coding: utf-8 -*-
"""Auditoria 3, Fase 2 (docs\\RELATORIO-QUALIDADE.md):

  L2 -- a velocidade do disco e' medida uma vez por computador + disco e
        vale por 7 dias (antes: ate 8 MB gravados no pen drive a cada
        abertura, so para medir);
  L3 -- a copia de seguranca so sai quando algo mudou, e sem o que o
        emulador refaz sozinho (antes: copias iguais faziam o rodizio de 3
        jogar fora as de outros momentos).
Tudo em pasta temporaria; nada de disco medido de verdade.
"""
import json
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
import hardware  # noqa: E402

MEDIDA = {"escrita_mbs": 120.0, "leitura_mbs": 300.0, "escrita_ms": 66.7, "amostra_mb": 8.0,
          "confirmacao_ms": 5.0}


class TestMedidaDoDiscoGuardada(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="arena_disco_teste_")
        self.arquivo = os.path.join(self.dir, "dados", "disco_medido.json")
        self.medidas = []
        self.volume = "ABCD1234"
        self.maquina = "maquina-1"

        def medir(pasta, amostras=3):
            self.medidas.append(pasta)
            return dict(MEDIDA)
        self.trocas = [mock.patch.object(hardware, "medir_velocidade", side_effect=medir),
                       mock.patch.object(hardware, "identidade_da_maquina", side_effect=lambda: self.maquina),
                       mock.patch.object(hardware, "numero_do_volume", side_effect=lambda _p: self.volume)]
        for troca in self.trocas:
            troca.start()

    def tearDown(self):
        for troca in self.trocas:
            troca.stop()
        shutil.rmtree(self.dir, ignore_errors=True)

    def medir(self, agora):
        return hardware.medir_velocidade_guardada(self.dir, self.arquivo, agora=agora)

    def test_mede_uma_vez_e_depois_usa_a_guardada(self):
        primeira = self.medir(1000.0)
        segunda = self.medir(5000.0)
        self.assertEqual(len(self.medidas), 1)
        self.assertNotIn("guardada", primeira)
        self.assertTrue(segunda.get("guardada"))
        self.assertEqual(segunda["escrita_mbs"], MEDIDA["escrita_mbs"])

    def test_outro_pen_drive_ou_outro_computador_mede_de_novo(self):
        self.medir(1000.0)
        self.volume = "FFFF0000"                 # outro pen drive
        self.medir(1001.0)
        self.maquina = "maquina-2"               # outro computador
        self.medir(1002.0)
        self.assertEqual(len(self.medidas), 3)
        self.volume, self.maquina = "ABCD1234", "maquina-1"
        self.assertTrue(self.medir(1003.0).get("guardada"))     # o primeiro ficou guardado

    def test_depois_de_7_dias_mede_de_novo(self):
        self.medir(1000.0)
        self.medir(1000.0 + hardware.VALIDADE_DA_MEDIDA_S + 1)
        self.assertEqual(len(self.medidas), 2)

    def test_arquivo_estragado_mede_e_grava_certo(self):
        os.makedirs(os.path.dirname(self.arquivo))
        with open(self.arquivo, "w", encoding="utf-8") as f:
            f.write("{isto nao e json")
        self.assertEqual(self.medir(1000.0)["escrita_mbs"], MEDIDA["escrita_mbs"])
        with open(self.arquivo, encoding="utf-8") as f:
            self.assertIsInstance(json.load(f), dict)

    def test_guarda_no_maximo_as_mais_recentes(self):
        os.makedirs(os.path.dirname(self.arquivo))
        velhas = {"pc-%d|X" % n: {"quando": float(n), "medida": dict(MEDIDA)} for n in range(80)}
        with open(self.arquivo, "w", encoding="utf-8") as f:
            json.dump(velhas, f)
        self.medir(5000.0)
        with open(self.arquivo, encoding="utf-8") as f:
            guardadas = json.load(f)
        self.assertLessEqual(len(guardadas), hardware.MEDIDAS_GUARDADAS)
        self.assertIn("maquina-1|ABCD1234", guardadas)

    def test_sem_numero_do_disco_mede_sempre_e_nao_grava(self):
        self.volume = None
        self.medir(1000.0)
        self.medir(1001.0)
        self.assertEqual(len(self.medidas), 2)
        self.assertFalse(os.path.exists(self.arquivo))


class TestCopiaSoQuandoMuda(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="arena_copia_teste_")
        self.retroarch = os.path.join(self.dir, "retroarch")
        self.saves = os.path.join(self.retroarch, "saves")
        self.troca = mock.patch.multiple(
            arena, PASTA_BACKUP=os.path.join(self.dir, "backup"), PASTA_SAVES=self.saves,
            PASTA_DADOS=os.path.join(self.dir, "dados"), PASTA_RETROARCH=self.retroarch)
        self.troca.start()
        os.makedirs(os.path.join(self.saves, "Snes9x"))
        os.makedirs(os.path.join(self.dir, "dados"))
        with open(os.path.join(self.dir, "dados", "config.json"), "w", encoding="utf-8") as f:
            f.write("{}")
        self.escrever_save(b"S" * 64)
        self.carimbos = iter("2026-10-08_10%04d" % n for n in range(100))

    def tearDown(self):
        self.troca.stop()
        shutil.rmtree(self.dir, ignore_errors=True)

    def escrever_save(self, conteudo, adiantar=0.0):
        caminho = os.path.join(self.saves, "Snes9x", "Jogo.srm")
        with open(caminho, "wb") as f:
            f.write(conteudo)
        if adiantar:
            info = os.stat(caminho)
            os.utime(caminho, (info.st_atime + adiantar, info.st_mtime + adiantar))

    def copia(self):
        # Um carimbo novo a cada copia (o de verdade tem segundos).
        with mock.patch.object(arena.time, "strftime", side_effect=lambda *_a: next(self.carimbos)):
            return arena.fazer_backup()

    def test_sem_mudanca_devolve_a_ultima(self):
        primeira = self.copia()
        segunda = self.copia()
        self.assertEqual(primeira, segunda)
        self.assertEqual(len(os.listdir(arena.PASTA_BACKUP)), 1)

    def test_com_mudanca_sai_copia_nova(self):
        primeira = self.copia()
        self.escrever_save(b"T" * 64, adiantar=10)
        segunda = self.copia()
        self.assertNotEqual(primeira, segunda)
        with open(os.path.join(segunda, "saves", "Snes9x", "Jogo.srm"), "rb") as f:
            self.assertEqual(f.read(), b"T" * 64)

    def test_save_do_mesmo_tamanho_mudado_logo_depois_sai_copia_nova(self):
        # Save de cartucho tem sempre o mesmo tamanho; com uma folga de 2 s na
        # hora (FAT32), duas versoes salvas em seguida pareciam iguais (o
        # teste_backup_rodizio pegou na primeira versao do L3).
        primeira = self.copia()
        self.escrever_save(b"U" * 64, adiantar=1)
        segunda = self.copia()
        self.assertNotEqual(primeira, segunda)

    def test_mesma_data_diferente_mas_mesmo_conteudo_e_igual(self):
        # FAT32: a copia fica com outra hora (de 2 em 2 s) sem nada ter mudado.
        primeira = self.copia()
        guardado = os.path.join(primeira, "saves", "Snes9x", "Jogo.srm")
        info = os.stat(guardado)
        os.utime(guardado, (info.st_atime, info.st_mtime + 1.5))
        self.assertEqual(self.copia(), primeira)

    def test_cache_e_netplay_ficam_fora(self):
        for pasta in (os.path.join("PPSSPP", "PSP", "SYSTEM", "CACHE"), ".netplay"):
            os.makedirs(os.path.join(self.saves, pasta))
            with open(os.path.join(self.saves, pasta, "x.bin"), "wb") as f:
                f.write(b"x")
        destino = self.copia()
        self.assertTrue(os.path.isfile(os.path.join(destino, "saves", "Snes9x", "Jogo.srm")))
        self.assertFalse(os.path.exists(os.path.join(destino, "saves", "PPSSPP", "PSP", "SYSTEM", "CACHE")))
        self.assertFalse(os.path.exists(os.path.join(destino, "saves", ".netplay")))


class TestAvisoDaRedePublica(unittest.TestCase):
    """Fase 4: quem ABRE a partida numa rede Publica ve o aviso, com as saidas
    que nao pedem senha (e a tela nunca espera o PowerShell para isso)."""

    def setUp(self):
        self.guardado = dict(arena._CATEGORIA_DA_REDE)

    def tearDown(self):
        arena._CATEGORIA_DA_REDE.clear()
        arena._CATEGORIA_DA_REDE.update(self.guardado)

    def test_rede_publica_avisa_com_a_saida(self):
        arena._CATEGORIA_DA_REDE.update(valor="Public", quando=1000.0)
        aviso = arena.aviso_da_rede_para_quem_hospeda(agora=1010.0)
        self.assertIn("Pública", aviso)
        self.assertIn("outro computador abre a partida e este entra", aviso)
        # Revisao da Fase 4: com o repasse ligado o convidado NAO entra
        # (testado com o RetroArch de verdade) -- nao e' saida.
        self.assertNotIn("casas diferentes", aviso)

    def test_resposta_velha_nao_vale(self):
        # A rede pode ter mudado de categoria (o professor trocou para
        # Privada) ou de lugar desde a ultima pergunta.
        arena._CATEGORIA_DA_REDE.update(valor="Public", quando=1000.0)
        self.assertEqual(arena.aviso_da_rede_para_quem_hospeda(agora=1000.0 + 3 * arena.VALIDADE_DA_CATEGORIA), "")

    def test_rede_privada_ou_sem_resposta_nao_avisa(self):
        for valor in ("Private", "DomainAuthenticated", None):
            arena._CATEGORIA_DA_REDE.update(valor=valor, quando=1000.0)
            self.assertEqual(arena.aviso_da_rede_para_quem_hospeda(agora=1001.0), "")

    def test_preparar_nao_pergunta_de_novo_antes_de_5_minutos(self):
        arena._CATEGORIA_DA_REDE.update(valor="Private", quando=__import__("time").monotonic(), perguntando=False)
        with mock.patch.object(arena.threading, "Thread") as linha:
            arena.preparar_categoria_da_rede()
        linha.assert_not_called()


if __name__ == "__main__":
    unittest.main()
