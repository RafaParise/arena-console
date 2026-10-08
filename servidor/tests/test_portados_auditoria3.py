# -*- coding: utf-8 -*-
"""Testes trazidos de ferramentas\\teste_*.py antigos (auditoria 3, Fase 1).

Os antigos subiam o servidor NA PASTA DE VERDADE e mexiam em dado real
(com copia e volta), e a rodada completa nem os rodava. Aqui ficam so as
conferencias que nenhum outro teste fazia, numa pasta temporaria, sem
servidor e sem tocar em emulador de verdade:

  - Xbox 360 pela rede: o Systemlink do Xenia Netplay (network_mode = 1)
    (era ferramentas\\teste_netplay_xbox360.py);
  - PS2 pela rede: o bloco [DEV9/Eth] do PCSX2, com e sem o driver Npcap
    (era ferramentas\\teste_rede_ps2_gt4.py);
  - amigo que mudou de IP: o endereco de agora, pela descoberta de colegas
    (era ferramentas\\teste_amigo_ip_muda.py);
  - controle do Neo Geo: so A/B/C/D + Start/Select, sem L/R
    (era ferramentas\\teste_controle_neogeo.py);
  - rodizio dos registros do RetroArch: ficam os LOGS_MANTIDOS mais novos e
    o que nao e' registro nao e' tocado (era ferramentas\\teste_rodizio_logs.py);
  - foto do perfil: so imagem de verdade, e a antiga so sai depois que a
    nova esta gravada (era ferramentas\\teste_perfil_foto.py).
"""
import base64
import os
import shutil
import sys
import tempfile
import time
import unittest
from unittest import mock

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

import controles  # noqa: E402
import graficos  # noqa: E402


class TestSystemlinkXbox360(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="arena_xbox_rede_")
        self.exe = os.path.join(self.dir, "xenia_canary_netplay.exe")
        self.config = os.path.join(self.dir, "xenia-canary-netplay.config.toml")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_liga_o_systemlink_e_preserva_o_resto(self):
        with open(self.config, "w", encoding="utf-8") as arquivo:
            arquivo.write('[Netplay]\nnetwork_mode = 0                 # 0 = offline, 1 = Systemlink\n'
                          '[GPU]\ngpu = "vulkan"\n')
        self.assertTrue(graficos.escrever_config_netplay_xbox360(self.exe))
        texto = open(self.config, encoding="utf-8").read()
        self.assertIn("network_mode = 1", texto)
        self.assertIn("# 0 = offline, 1 = Systemlink", texto)      # o comentario fica
        self.assertIn('gpu = "vulkan"', texto)

    def test_sem_o_arquivo_do_xenia_nao_inventa_um(self):
        # O Xenia ainda nao rodou: o ARENA nao cria o arquivo do zero (perderia
        # as centenas de opcoes que so o Xenia sabe).
        self.assertFalse(graficos.escrever_config_netplay_xbox360(self.exe))
        self.assertFalse(os.path.exists(self.config))


class TestRedePs2(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="arena_ps2_rede_")
        self.exe = os.path.join(self.dir, "pcsx2-qt.exe")
        self.ini = os.path.join(self.dir, "inis", "PCSX2.ini")
        os.makedirs(os.path.dirname(self.ini))
        with open(self.ini, "w", encoding="utf-8") as arquivo:
            arquivo.write("[UI]\nSettingsVersion = 1\n\n[DEV9/Eth]\nEthEnable = false\nEthApi = Velho\n\n"
                          "[EmuCore/GS]\nupscale_multiplier = 1\n")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def ler(self):
        return open(self.ini, encoding="utf-8").read()

    def test_com_o_driver_hospeda_pelo_adaptador_de_verdade(self):
        with mock.patch.object(graficos, "npcap_instalado", return_value=True), \
                mock.patch.object(graficos, "adaptador_de_rede_real", return_value=r"\Device\NPF_{ABC}"):
            feito = graficos.escrever_config_rede_ps2(self.exe)
        self.assertEqual(feito["modo"], "pcap")
        texto = self.ler()
        self.assertEqual(texto.count("[DEV9/Eth]"), 1)              # o bloco velho saiu
        self.assertIn("EthApi = PCAPBridged", texto)
        self.assertIn(r"InterfaceName = \Device\NPF_{ABC}", texto)
        self.assertNotIn("EthApi = Velho", texto)
        self.assertIn("SettingsVersion = 1", texto)                 # o resto fica
        self.assertIn("upscale_multiplier = 1", texto)

    def test_sem_o_driver_so_entra(self):
        with mock.patch.object(graficos, "npcap_instalado", return_value=False):
            feito = graficos.escrever_config_rede_ps2(self.exe)
        self.assertEqual(feito["modo"], "sockets")
        self.assertFalse(feito["com_driver"])
        self.assertIn("EthApi = Sockets", self.ler())


class TestAmigoQueMudouDeIp(unittest.TestCase):

    def setUp(self):
        import arena
        self.arena = arena
        with arena.TRAVA_VIZINHOS:
            self.guardados = dict(arena.VIZINHOS)
            arena.VIZINHOS.clear()

    def tearDown(self):
        with self.arena.TRAVA_VIZINHOS:
            self.arena.VIZINHOS.clear()
            self.arena.VIZINHOS.update(self.guardados)

    def test_usa_o_endereco_de_agora_e_corrige_o_salvo(self):
        with self.arena.TRAVA_VIZINHOS:
            self.arena.VIZINHOS["abc123"] = {"id": "abc123", "apelido": "Marina", "ip": "192.168.0.99",
                                             "porta": 8777, "visto_em": time.monotonic(), "partida": None}
        amigo = {"apelido": "Marina", "id": "abc123", "url": "http://192.168.0.50:8777"}
        self.assertEqual(self.arena.resolver_endereco_amigo(amigo), "http://192.168.0.99:8777")
        self.assertEqual(amigo["url"], "http://192.168.0.99:8777")

    def test_fora_da_rede_local_fica_o_endereco_salvo(self):
        amigo = {"apelido": "Lucas", "id": "zzz999", "url": "http://201.10.20.30:8777"}
        self.assertEqual(self.arena.resolver_endereco_amigo(amigo), "http://201.10.20.30:8777")

    def test_amigo_sem_codigo_fica_o_endereco_salvo(self):
        amigo = {"apelido": "Ana", "url": "http://192.168.0.7:8777"}
        self.assertEqual(self.arena.resolver_endereco_amigo(amigo), "http://192.168.0.7:8777")


class TestRodizioDosRegistros(unittest.TestCase):

    def setUp(self):
        import arena
        self.arena = arena
        self.dir = tempfile.mkdtemp(prefix="arena_logs_teste_")
        self.dados_de_verdade = arena.PASTA_DADOS
        arena.PASTA_DADOS = self.dir

    def tearDown(self):
        self.arena.PASTA_DADOS = self.dados_de_verdade
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_ficam_os_mais_novos_e_o_resto_nao_e_tocado(self):
        nomes = ["retroarch__2026_09_22__%02d_00_00.log" % i for i in range(16)]
        for nome in nomes + ["config.json"]:
            with open(os.path.join(self.dir, nome), "w", encoding="utf-8") as arquivo:
                arquivo.write("x")
        apagados = self.arena.limpar_logs_antigos()
        mantidos = self.arena.LOGS_MANTIDOS
        restantes = sorted(os.listdir(self.dir))
        self.assertEqual(apagados, 16 - mantidos)
        self.assertEqual([n for n in restantes if n.startswith("retroarch__")], sorted(nomes)[-mantidos:])
        self.assertIn("config.json", restantes)


class TestControleDoNeoGeo(unittest.TestCase):

    def test_so_os_botoes_que_o_neo_geo_tem(self):
        perfil, erro = controles.montar_perfil("xbox360", "neogeo")
        self.assertFalse(erro)
        botoes = [linha["botao"] for linha in perfil["linhas"]]
        for esperado in ("b", "a", "y", "x", "start"):
            self.assertIn(esperado, botoes)
        self.assertNotIn("l", botoes)
        self.assertNotIn("r", botoes)


# Um PNG de verdade de 1x1 pixel (o menor valido) e um JPEG minimo de cabecalho.
PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")
JPEG_MINIMO = b"\xff\xd8\xff\xe0" + b"\x00" * 60 + b"\xff\xd9"


class TestFotoDoPerfil(unittest.TestCase):
    """Era ferramentas\\teste_perfil_foto.py (pela API, na pasta de verdade)."""

    def setUp(self):
        import arena
        self.arena = arena
        self.dir = tempfile.mkdtemp(prefix="arena_foto_teste_")
        self.troca = mock.patch.object(arena, "PASTA_PERFIL", self.dir)
        self.troca.start()

    def tearDown(self):
        self.troca.stop()
        shutil.rmtree(self.dir, ignore_errors=True)

    def enviar(self, brutos, prefixo="data:image/png;base64,"):
        return self.arena.gravar_foto_perfil(prefixo + base64.b64encode(brutos).decode("ascii"))

    def test_png_de_verdade_vai_e_volta_igual(self):
        destino = self.enviar(PNG_1X1)
        self.assertEqual(os.path.basename(destino), "foto.png")
        self.assertEqual(self.arena.foto_perfil_caminho(), destino)
        with open(destino, "rb") as arquivo:
            self.assertEqual(arquivo.read(), PNG_1X1)

    def test_o_que_nao_e_imagem_e_recusado(self):
        for lixo in (b"nao sou imagem", b"GIF89a" + b"\x00" * 20):
            with self.assertRaises(ValueError):
                self.enviar(lixo)
        with self.assertRaises(ValueError):
            self.arena.gravar_foto_perfil("isto nao e base64 %%%")
        self.assertIsNone(self.arena.foto_perfil_caminho())

    def test_trocar_a_foto_deixa_so_a_nova(self):
        self.enviar(PNG_1X1)
        destino = self.enviar(JPEG_MINIMO, "data:image/jpeg;base64,")
        self.assertEqual(sorted(os.listdir(self.dir)), ["foto.jpg"])
        self.assertEqual(self.arena.foto_perfil_caminho(), destino)

    def test_falha_ao_gravar_a_nova_nao_perde_a_antiga(self):
        # Achado da auditoria 3: a antiga saia ANTES de a nova estar gravada.
        self.enviar(PNG_1X1)
        with mock.patch.object(self.arena.os, "replace", side_effect=OSError(28, "disco cheio")):
            with self.assertRaises(OSError):
                self.enviar(JPEG_MINIMO, "data:image/jpeg;base64,")
        self.assertEqual(sorted(os.listdir(self.dir)), ["foto.png"])

    def test_temporario_esquecido_nao_passa_por_foto(self):
        with open(os.path.join(self.dir, "foto.png.1234.tmp"), "wb") as arquivo:
            arquivo.write(b"meia foto")
        self.assertIsNone(self.arena.foto_perfil_caminho())

    def test_apagar(self):
        self.enviar(PNG_1X1)
        self.assertTrue(self.arena.apagar_foto_perfil())
        self.assertIsNone(self.arena.foto_perfil_caminho())
        self.assertFalse(self.arena.apagar_foto_perfil())


if __name__ == "__main__":
    unittest.main()
