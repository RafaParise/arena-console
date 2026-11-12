# -*- coding: utf-8 -*-
"""Equipamentos (servidor\\equipamentos.py, 13/11/2026): a lista do que o ARENA tem, o que falta e o botao que
resolve; o MFG Super Motion baixado do autor e conferido; a fila do "Equipar"; a versao para PC escolhida por jogo e
o rar/7z pelo tar do proprio sistema (servidor\\recomps.py)."""
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
import zipfile
from unittest import mock

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PASTA_SERVIDOR not in sys.path:
    sys.path.insert(0, PASTA_SERVIDOR)
import equipamentos  # noqa: E402
import recomps  # noqa: E402

PASTA_TESTES = os.path.join(os.path.dirname(PASTA_SERVIDOR), "testes")
if PASTA_TESTES not in sys.path:
    sys.path.insert(0, PASTA_TESTES)
import limpeza  # noqa: E402

RECOMP = {"id": "zelda64recomp", "nome": "Zelda 64: Recompiled", "repo": "Zelda64Recomp/Zelda64Recomp",
          "licenca": "GPL-3.0", "plataforma": "n64", "sistemas": ["windows", "linux"], "tamanho": "28 MB"}
CATALOGO = {"por_titulo": {"n64|legendofzeldamajorasmask": ["zelda64recomp"]}, "recomps": {"zelda64recomp": RECOMP}}
PLATAFORMAS = [{"id": "snes", "nome": "Super Nintendo", "core": "snes9x_libretro.dll"},
               {"id": "ps2", "nome": "PlayStation 2", "externo": {"nome": "PCSX2"}},
               {"id": "pc", "nome": "PC", "nativo": True, "externo": {"nome": "PC"}}]
JOGOS = [{"titulo": "Legend of Zelda, The - Majora's Mask (USA)", "plataforma": "n64"},
         {"titulo": "Contra", "plataforma": "nes"}]


def por_id(lista):
    return {item["id"]: item for item in lista}


class Lista(unittest.TestCase):
    def setUp(self):
        self.antigo = recomps._catalogo["dados"]
        recomps._catalogo["dados"] = CATALOGO
        self.pasta = tempfile.mkdtemp(prefix="arena_equip_")
        self.recomps_antes = recomps.PASTA_RECOMPS
        recomps.PASTA_RECOMPS = os.path.join(self.pasta, "Recomps")
        equipamentos._CACHE_WSL["valor"] = False

    def tearDown(self):
        recomps._catalogo["dados"] = self.antigo
        recomps.PASTA_RECOMPS = self.recomps_antes
        equipamentos._CACHE_WSL.clear()
        limpeza.apagar_pasta(self.pasta)

    def _listar(self, android=False, mfg_achado=None, lossless_achado=None):
        with mock.patch.object(equipamentos.mfg, "achar", return_value=mfg_achado), \
                mock.patch.object(equipamentos.lossless, "achar", return_value=lossless_achado), \
                mock.patch.object(recomps, "sistema", return_value="windows"), \
                mock.patch.object(equipamentos.os, "name", "nt"):
            return equipamentos.listar(self.pasta, PLATAFORMAS, JOGOS,
                                       lambda p: "C:/PCSX2/pcsx2.exe" if p["id"] == "ps2" else None,
                                       nucleos_prontos=40, android=android)

    def test_sem_nada_o_mfg_baixa_e_o_lossless_vai_a_loja(self):
        itens = por_id(self._listar())
        self.assertEqual(itens["consoles"]["estado"], "pronto")
        self.assertEqual(itens["emulador:ps2"]["estado"], "pronto")
        self.assertNotIn("emulador:pc", itens)                 # o console PC nao e' emulador
        self.assertEqual(itens["mfg"]["estado"], "falta")
        self.assertEqual(itens["mfg"]["acao"]["tipo"], "baixar")
        self.assertEqual(itens["lossless"]["estado"], "pago")
        self.assertEqual(itens["lossless"]["acao"]["tipo"], "loja")
        self.assertIn("não é obrigatório", itens["lossless"]["para_que"])
        # So o jogo que a pessoa TEM: o Zelda (o Contra nao tem versao para PC).
        self.assertEqual([s["jogo"] for s in itens["recomps"]["itens"]], ["Legend of Zelda, The - Majora's Mask (USA)"])

    def test_com_tudo_pronto_nada_para_baixar(self):
        itens = self._listar(mfg_achado={"versao": "1.0.5"}, lossless_achado={"licenca": True})
        mapa = por_id(itens)
        self.assertEqual(mapa["mfg"]["estado"], "pronto")
        self.assertEqual(mapa["lossless"]["estado"], "pronto")
        self.assertEqual(equipamentos.ids_para_equipar_tudo(itens), ["recomp:zelda64recomp"])

    def test_equipar_tudo_e_o_tamanho(self):
        itens = self._listar()
        ids = equipamentos.ids_para_equipar_tudo(itens)
        self.assertEqual(ids, ["mfg", "recomp:zelda64recomp"])
        self.assertEqual(equipamentos.tamanho_aproximado(itens, ids), "cerca de 128 MB")
        self.assertEqual(equipamentos._megas("1,5 GB"), 1536)
        self.assertEqual(equipamentos._megas("sem tamanho"), 0)

    def test_estado_sempre_com_palavra_conhecida(self):
        for item in self._listar():
            self.assertIn(item["estado"], ("pronto", "falta", "opcional", "pago"), item["id"])
            self.assertTrue(item["para_que"], item["id"])

    def test_no_linux_as_versoes_para_pc_sem_mfg_nem_lossless(self):
        with mock.patch.object(recomps, "sistema", return_value="linux"), \
                mock.patch.object(equipamentos.os, "name", "posix"), \
                mock.patch.object(equipamentos.plataforma_do_sistema, "WINDOWS", False):
            itens = por_id(equipamentos.listar(self.pasta, PLATAFORMAS, JOGOS, lambda p: None, 40, android=False))
        self.assertIn("recomps", itens)
        for so_do_windows in ("mfg", "lossless", "wsl"):
            self.assertNotIn(so_do_windows, itens)

    def test_no_celular_so_o_que_existe_la(self):
        itens = por_id(self._listar(android=True))
        self.assertIn("jogos_android", itens)
        for de_computador in ("mfg", "lossless", "recomps", "wsl", "emulador:ps2"):
            self.assertNotIn(de_computador, itens)


class MfgDoAutor(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_mfg_")
        self.origem = os.path.join(self.pasta, "origem.zip")
        with zipfile.ZipFile(self.origem, "w") as z:
            z.writestr("Mfg Super Motion/Engine/nvngx.dll", b"motor")
            z.writestr("Mfg Super Motion/Engine/engine-version.txt", "1.0.5")
            z.writestr("Mfg Super Motion/Mfg Super Motion.exe", b"tela")
        self.marca = recomps._sha256(self.origem)

    def tearDown(self):
        limpeza.apagar_pasta(self.pasta)

    def _release(self, nome="Mfg.Super.Motion1.0.6.rar", marca=None):
        return {"tag": "1.0.6", "arquivos": [
            {"nome": "mfg-super-motion-linux-x64.tar.gz", "url": "https://github.com/x/l.tar.gz", "tamanho": 5, "sha256": "aa"},
            {"nome": nome, "url": "https://github.com/x/" + nome, "tamanho": 100,
             "sha256": self.marca if marca is None else marca}]}

    def _baixar(self, url, segundos, destino=None, agente=None):
        with open(self.origem, "rb") as de, open(destino, "wb") as para:
            para.write(de.read())
        return 0, b""

    def _descompactar_zip(self, arquivo, destino):
        os.makedirs(destino, exist_ok=True)
        with zipfile.ZipFile(arquivo) as z:
            z.extractall(destino)
        recomps._desembrulhar(destino)

    def _instalar(self, release):
        with mock.patch.object(equipamentos.os, "name", "nt"), \
                mock.patch.object(recomps, "tar_do_sistema", return_value="tar.exe"), \
                mock.patch.object(equipamentos.baixar, "rodar", side_effect=self._baixar), \
                mock.patch.object(recomps, "descompactar", side_effect=self._descompactar_zip):
            return equipamentos.instalar_mfg(self.pasta, release=release)

    def test_baixa_o_rar_confere_e_poe_na_pasta_que_o_mfg_procura(self):
        pasta = self._instalar(self._release())
        self.assertEqual(pasta, os.path.join(self.pasta, "emuladores", "MFG SUPER MOTION"))
        self.assertTrue(os.path.isfile(os.path.join(pasta, "Engine", "nvngx.dll")))
        with open(os.path.join(pasta, equipamentos.MARCA_MFG), encoding="utf-8") as arquivo:
            marca = json.load(arquivo)
        self.assertEqual(marca["sha256"], self.marca)
        self.assertIn("PolyForm", marca["licenca"])
        self.assertEqual(equipamentos.andamento("mfg")["estado"], "pronto")
        self.assertFalse(os.listdir(os.path.join(self.pasta, "emuladores", ".baixando")))   # o .rar foi embora

    def test_marca_diferente_nao_instala(self):
        with self.assertRaises(recomps.NaoDaParaInstalar):
            self._instalar(self._release(marca="0" * 64))
        self.assertFalse(os.path.exists(os.path.join(self.pasta, "emuladores", "MFG SUPER MOTION")))
        self.assertEqual(equipamentos.andamento("mfg")["estado"], "erro")

    def test_sem_marca_nenhuma_nao_baixa(self):
        with self.assertRaises(recomps.NaoDaParaInstalar) as erro:
            self._instalar(self._release(marca=""))
        self.assertIn("segurança", str(erro.exception))

    def test_a_marca_guardada_no_arena_manda_no_arquivo_conhecido(self):
        # O GitHub diz uma marca, o ARENA guarda outra para o 1.0.5: as duas tem de bater, entao nao instala.
        with self.assertRaises(recomps.NaoDaParaInstalar):
            self._instalar(self._release(nome="Mfg.Super.Motion1.0.5.rar"))

    def test_sem_o_motor_nao_instala(self):
        with zipfile.ZipFile(self.origem, "w") as z:
            z.writestr("outra coisa.txt", "x")
        self.marca = recomps._sha256(self.origem)
        with self.assertRaises(recomps.NaoDaParaInstalar) as erro:
            self._instalar(self._release())
        self.assertIn("motor", str(erro.exception))

    def test_versao_nova_troca_a_velha(self):
        self._instalar(self._release())
        velho = os.path.join(self.pasta, "emuladores", "MFG SUPER MOTION", "sobra.txt")
        open(velho, "w").close()
        self._instalar(self._release())
        self.assertFalse(os.path.exists(velho))
        self.assertFalse(os.path.exists(os.path.join(self.pasta, "emuladores", "MFG SUPER MOTION.velha")))


class Fila(unittest.TestCase):
    def test_um_de_cada_vez_e_a_fila_termina(self):
        feitos = []
        with mock.patch.object(equipamentos, "instalar_mfg", side_effect=lambda: feitos.append("mfg")), \
                mock.patch.object(recomps, "instalar", side_effect=lambda i: feitos.append(i)):
            entraram = equipamentos.equipar(["mfg", "recomp:zelda64recomp", "mfg"])
            self.assertEqual(entraram, ["mfg", "recomp:zelda64recomp"])        # o repetido nao entra duas vezes
            for _ in range(100):
                if not equipamentos.trabalhando():
                    break
                time.sleep(0.02)
        self.assertEqual(feitos, ["mfg", "zelda64recomp"])
        self.assertFalse(equipamentos.trabalhando())

    def test_um_erro_nao_para_a_fila(self):
        feitos = []

        def falha():
            raise recomps.NaoDaParaInstalar("sem internet")
        with mock.patch.object(equipamentos, "instalar_mfg", side_effect=falha), \
                mock.patch.object(recomps, "instalar", side_effect=lambda i: feitos.append(i)):
            equipamentos.equipar(["mfg", "recomp:zelda64recomp"])
            for _ in range(100):
                if not equipamentos.trabalhando():
                    break
                time.sleep(0.02)
        self.assertEqual(feitos, ["zelda64recomp"])


class VersaoParaPCEscolhida(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_recomp_usar_")
        self.antigo = (recomps._catalogo["dados"], recomps.PASTA_RECOMPS)
        recomps._catalogo["dados"] = CATALOGO
        recomps.PASTA_RECOMPS = os.path.join(self.pasta, "Recomps")

    def tearDown(self):
        recomps._catalogo["dados"], recomps.PASTA_RECOMPS = self.antigo
        limpeza.apagar_pasta(self.pasta)

    def _baixado(self, marca=None):
        pasta = recomps.pasta_do("zelda64recomp")
        os.makedirs(pasta)
        open(os.path.join(pasta, "Zelda64Recompiled.exe"), "wb").close()
        with open(os.path.join(pasta, recomps.MARCA), "w", encoding="utf-8") as saida:
            json.dump(marca or {"id": "zelda64recomp"}, saida)

    def test_baixada_abre_sozinha_e_desliga_sem_apagar(self):
        with mock.patch.object(recomps, "sistema", return_value="windows"):
            titulo = JOGOS[0]["titulo"]
            self.assertIsNone(recomps.escolhido_para(titulo, "n64"))       # nao baixada: o Jogar segue como sempre
            self._baixado()
            self.assertEqual(recomps.escolhido_para(titulo, "n64"), "zelda64recomp")
            self.assertFalse(recomps.preferir("zelda64recomp", False))
            self.assertIsNone(recomps.escolhido_para(titulo, "n64"))
            self.assertTrue(os.path.isfile(os.path.join(recomps.pasta_do("zelda64recomp"), "Zelda64Recompiled.exe")))
            self.assertTrue(recomps.preferir("zelda64recomp", True))
            self.assertTrue(recomps.resumo_para_a_tela(RECOMP)["em_uso"])

    def test_no_celular_nunca(self):
        self._baixado()
        with mock.patch.object(recomps, "sistema", return_value=None):
            self.assertIsNone(recomps.escolhido_para(JOGOS[0]["titulo"], "n64"))

    def test_preferir_sem_baixar_explica(self):
        with self.assertRaises(recomps.NaoDaParaInstalar):
            recomps.preferir("zelda64recomp", True)


@unittest.skipUnless(recomps.tar_do_sistema(), "sem o tar do sistema (bsdtar)")
class SeteZipPeloTarDoSistema(unittest.TestCase):
    def test_abre_7z_e_desembrulha(self):
        pasta = tempfile.mkdtemp(prefix="arena_7z_")
        try:
            origem = os.path.join(pasta, "origem", "Jogo-v1")
            os.makedirs(origem)
            with open(os.path.join(origem, "Jogo.exe"), "wb") as arquivo:
                arquivo.write(b"MZ")
            sete = os.path.join(pasta, "jogo.7z")
            extra = {"creationflags": 0x08000000} if os.name == "nt" else {}
            feito = subprocess.run([recomps.tar_do_sistema(), "--format", "7zip", "-cf", sete, "-C",
                                    os.path.join(pasta, "origem"), "Jogo-v1"], capture_output=True, **extra)
            if feito.returncode != 0:
                self.skipTest("este tar nao grava 7z")
            destino = os.path.join(pasta, "destino")
            recomps.descompactar(sete, destino)
            self.assertTrue(os.path.isfile(os.path.join(destino, "Jogo.exe")))      # a pasta de cima sumiu
        finally:
            limpeza.apagar_pasta(pasta)


if __name__ == "__main__":
    unittest.main()


class JogoDeUmSistemaNoOutro(unittest.TestCase):
    """O Wine portatil (Linux) e o WSL com o Linux do ARENA (Windows), 13/11/2026."""

    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_camadas_")
        equipamentos._CACHE_WSL.clear()

    def tearDown(self):
        equipamentos._CACHE_WSL.clear()
        limpeza.apagar_pasta(self.pasta)

    def _situacao(self, ativo, do_arena=False):
        return mock.patch.object(equipamentos, "situacao_do_wsl",
                                 return_value={"ativo": ativo, "do_arena": do_arena, "outras": []})

    def test_wsl_desligado_pede_administrador_com_aviso(self):
        with self._situacao(False):
            item = equipamentos._item_do_wsl()
        self.assertEqual(item["acao"]["tipo"], "admin")
        self.assertIn("administrador", item["acao"]["rotulo"])
        self.assertIn("administrador", item["acao"]["aviso"])
        self.assertEqual(item["estado"], "opcional")          # nunca entra no "Equipar tudo"
        self.assertEqual(equipamentos.ids_para_equipar_tudo([item]), [])

    def test_wsl_ligado_prepara_o_linux_do_arena_sem_administrador(self):
        with self._situacao(True):
            item = equipamentos._item_do_wsl()
        self.assertEqual((item["id"], item["acao"]["tipo"]), ("linux", "baixar"))
        with self._situacao(True, do_arena=True):
            self.assertEqual(equipamentos._item_do_wsl()["estado"], "pronto")

    def test_administrador_negado_ou_aceito(self):
        import ctypes
        if os.name != "nt":
            self.skipTest("so no Windows")
        with mock.patch.object(ctypes.windll.shell32, "ShellExecuteW", return_value=5):
            with self.assertRaises(recomps.NaoDaParaInstalar) as erro:
                equipamentos.ligar_o_wsl_com_administrador()
            self.assertIn("não foi dada", str(erro.exception))
        with mock.patch.object(ctypes.windll.shell32, "ShellExecuteW", return_value=42) as chamada:
            frase = equipamentos.ligar_o_wsl_com_administrador()
        self.assertIn("reinicie", frase)
        self.assertEqual(chamada.call_args[0][1:4], ("runas", "wsl.exe", "--install --no-distribution"))

    def test_linux_do_arena_baixa_confere_importa_e_poe_as_pecas(self):
        imagem = b"imagem do ubuntu"
        import hashlib
        marca = hashlib.sha256(imagem).hexdigest()

        def baixar_falso(url, segundos, destino=None, agente=None):
            with open(destino, "wb") as saida:
                saida.write(("%s *%s\n" % (marca, equipamentos.ARQUIVO_UBUNTU_WSL)).encode() if url.endswith("SHA256SUMS")
                            else imagem)
            return 0, b""
        chamadas = []
        with self._situacao(True), mock.patch.object(equipamentos.baixar, "rodar", side_effect=baixar_falso), \
                mock.patch.object(equipamentos, "_rodar_wsl", side_effect=lambda a, s=30: chamadas.append(a) or (0, "")):
            equipamentos.preparar_linux(self.pasta)
        self.assertEqual(chamadas[0][:2], ["--import", "ARENA-Linux"])
        self.assertEqual(chamadas[0][2], os.path.join(self.pasta, "emuladores", "Linux"))
        self.assertIn("apt-get install", chamadas[1][-1])
        self.assertEqual(chamadas[1][:4], ["-d", "ARENA-Linux", "-u", "root"])
        self.assertEqual(equipamentos.andamento("linux")["estado"], "pronto")
        self.assertFalse(os.listdir(os.path.join(self.pasta, "emuladores", ".baixando")))   # a imagem foi embora

    def test_linux_do_arena_com_marca_errada_nao_importa(self):
        def baixar_falso(url, segundos, destino=None, agente=None):
            with open(destino, "wb") as saida:
                saida.write(("%s *%s\n" % ("0" * 64, equipamentos.ARQUIVO_UBUNTU_WSL)).encode()
                            if url.endswith("SHA256SUMS") else b"outra coisa")
            return 0, b""
        with self._situacao(True), mock.patch.object(equipamentos.baixar, "rodar", side_effect=baixar_falso), \
                mock.patch.object(equipamentos, "_rodar_wsl", return_value=(0, "")) as wsl:
            with self.assertRaises(recomps.NaoDaParaInstalar):
                equipamentos.preparar_linux(self.pasta)
        wsl.assert_not_called()

    def test_arena_levado_para_outro_computador_so_registra_o_disco(self):
        pasta = os.path.join(self.pasta, "emuladores", "Linux")
        os.makedirs(pasta)
        open(os.path.join(pasta, "ext4.vhdx"), "wb").close()
        chamadas = []
        with self._situacao(True), mock.patch.object(equipamentos.baixar, "rodar") as baixar, \
                mock.patch.object(equipamentos, "_rodar_wsl", side_effect=lambda a, s=30: chamadas.append(a) or (0, "")):
            equipamentos.preparar_linux(self.pasta)
        baixar.assert_not_called()
        self.assertEqual(chamadas[0][:2], ["--import-in-place", "ARENA-Linux"])

    def test_sem_wsl_ligado_explica(self):
        with self._situacao(False):
            with self.assertRaises(recomps.NaoDaParaInstalar) as erro:
                equipamentos.preparar_linux(self.pasta)
        self.assertIn("administrador", str(erro.exception))

    def test_wine_portatil_baixa_e_abre_em_emuladores(self):
        import io
        import tarfile
        origem = os.path.join(self.pasta, "wine.tar.xz")
        with tarfile.open(origem, "w:xz") as tar:
            for nome, conteudo in (("wine-11.21-amd64-wow64/bin/wine", b"#!/bin/sh\n"),
                                   ("wine-11.21-amd64-wow64/lib/wine/x86_64-windows/kernel32.dll", b"MZ")):
                info = tarfile.TarInfo(nome)
                info.size = len(conteudo)
                info.mode = 0o755
                tar.addfile(info, io.BytesIO(conteudo))
        marca = recomps._sha256(origem)
        release = {"tag": "11.21", "arquivos": [
            {"nome": "wine-11.21-staging-amd64-wow64.tar.xz", "url": "https://x/s.tar.xz", "tamanho": 9, "sha256": "aa"},
            {"nome": "wine-11.21-amd64-wow64.tar.xz", "url": "https://x/w.tar.xz", "tamanho": 9, "sha256": marca}]}

        def baixar_falso(url, segundos, destino=None, agente=None):
            self.assertTrue(url.endswith("/w.tar.xz"))             # o sem "staging"
            with open(origem, "rb") as de, open(destino, "wb") as para:
                para.write(de.read())
            return 0, b""
        with mock.patch.object(equipamentos.os, "name", "posix"), \
                mock.patch.object(equipamentos.baixar, "rodar", side_effect=baixar_falso):
            pasta = equipamentos.instalar_wine(self.pasta, release=release)
        self.assertTrue(os.path.isfile(os.path.join(pasta, "bin", "wine")))
        self.assertEqual(equipamentos.andamento("wine")["estado"], "pronto")

    def test_jogo_de_linux_no_windows_usa_o_linux_do_arena(self):
        import jogos_pc
        with mock.patch.object(jogos_pc, "wsl", return_value="wsl.exe"), \
                mock.patch.dict(jogos_pc._WSL_DO_ARENA, {"tem": True}):
            comando, _aviso = jogos_pc.comando_para(os.path.join("C:" + os.sep, "Jogos", "jogo"), "", "windows", "linux")
        self.assertEqual(comando[:3], ["wsl.exe", "-d", "ARENA-Linux"])
