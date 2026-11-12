# -*- coding: utf-8 -*-
"""O console PC (servidor\\jogos_pc.py): o tipo do programa pelo cabecalho, o programa principal da pasta, os jogos
das lojas e a linha de comando em cada sistema (Wine, WSL, atalho da loja)."""
import json
import os
import struct
import sys
import tempfile
import unittest
from unittest import mock

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PASTA_SERVIDOR not in sys.path:
    sys.path.insert(0, PASTA_SERVIDOR)
import jogos_pc  # noqa: E402

PASTA_TESTES = os.path.join(os.path.dirname(PASTA_SERVIDOR), "testes")
if PASTA_TESTES not in sys.path:
    sys.path.insert(0, PASTA_TESTES)
import limpeza  # noqa: E402


def pe(caminho, tamanho=200):
    """Um programa do Windows de mentira: MZ, o ponteiro no byte 60 e a marca PE."""
    cabecalho = bytearray(b"MZ" + b"\0" * 62)
    cabecalho[60:64] = struct.pack("<I", 128)
    with open(caminho, "wb") as arquivo:
        arquivo.write(bytes(cabecalho).ljust(128, b"\0") + b"PE\0\0" + b"\0" * tamanho)


def mz(caminho):
    with open(caminho, "wb") as arquivo:
        arquivo.write(b"MZ" + b"\x90" * 62 + b"\0" * 64)


def elf(caminho):
    with open(caminho, "wb") as arquivo:
        arquivo.write(b"\x7fELF" + b"\0" * 60)


class TipoDoPrograma(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_pc_")

    def tearDown(self):
        limpeza.apagar_pasta(self.pasta)

    def test_pe_mz_elf_e_script(self):
        pe(os.path.join(self.pasta, "w.exe"))
        mz(os.path.join(self.pasta, "d.exe"))
        elf(os.path.join(self.pasta, "l"))
        open(os.path.join(self.pasta, "r.sh"), "w").close()
        open(os.path.join(self.pasta, "x.AppImage"), "w").close()
        open(os.path.join(self.pasta, "t.txt"), "w").close()
        self.assertEqual(jogos_pc.tipo_do_programa(os.path.join(self.pasta, "w.exe")), "windows")
        self.assertEqual(jogos_pc.tipo_do_programa(os.path.join(self.pasta, "d.exe")), "dos")
        self.assertEqual(jogos_pc.tipo_do_programa(os.path.join(self.pasta, "l")), "linux")
        self.assertEqual(jogos_pc.tipo_do_programa(os.path.join(self.pasta, "r.sh")), "script")
        self.assertEqual(jogos_pc.tipo_do_programa(os.path.join(self.pasta, "x.AppImage")), "linux")
        self.assertEqual(jogos_pc.tipo_do_programa(os.path.join(self.pasta, "t.txt")), "")
        self.assertTrue(jogos_pc.e_jogo_de_windows(os.path.join(self.pasta, "w.exe")))
        self.assertFalse(jogos_pc.e_jogo_de_windows(os.path.join(self.pasta, "d.exe")))

    def test_programa_principal_da_pasta(self):
        pasta = os.path.join(self.pasta, "Meu Jogo")
        os.makedirs(pasta)
        pe(os.path.join(pasta, "MeuJogo.exe"), 100)
        pe(os.path.join(pasta, "unins000.exe"), 900)
        pe(os.path.join(pasta, "UnityCrashHandler64.exe"), 900)
        pe(os.path.join(pasta, "Ajudante.exe"), 2000)
        arquivos = ["MeuJogo.exe", "unins000.exe", "UnityCrashHandler64.exe", "Ajudante.exe", "dados.pak"]
        self.assertEqual(jogos_pc.programa_principal(pasta, arquivos), ["MeuJogo.exe"])   # o nome da pasta vence o maior
        self.assertEqual(jogos_pc.so_o_jogo(pasta, arquivos), ["MeuJogo.exe", "dados.pak"])
        os.remove(os.path.join(pasta, "MeuJogo.exe"))
        self.assertEqual(jogos_pc.programa_principal(pasta, arquivos[1:]), ["Ajudante.exe"])   # senao, o maior
        self.assertEqual(jogos_pc.programa_principal(pasta, ["so.exe"]), ["so.exe"])


class Lojas(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_pc_")

    def tearDown(self):
        limpeza.apagar_pasta(self.pasta)

    def test_steam(self):
        steamapps = os.path.join(self.pasta, "steamapps")
        os.makedirs(steamapps)
        with open(os.path.join(steamapps, "appmanifest_220.acf"), "w", encoding="utf-8") as arquivo:
            arquivo.write('"AppState"\n{\n\t"appid"\t\t"220"\n\t"name"\t\t"Half-Life 2"\n\t"installdir"\t\t"Half-Life 2"\n}\n')
        with open(os.path.join(steamapps, "appmanifest_1493710.acf"), "w", encoding="utf-8") as arquivo:
            arquivo.write('"AppState"\n{\n\t"appid"\t\t"1493710"\n\t"name"\t\t"Proton Experimental"\n\t"installdir"\t\t"Proton"\n}\n')
        with open(os.path.join(steamapps, "appmanifest_993090.acf"), "w", encoding="utf-8") as arquivo:
            arquivo.write('"AppState"\n{\n\t"appid"\t\t"993090"\n\t"name"\t\t"Lossless Scaling"\n\t"installdir"\t\t"Lossless Scaling"\n}\n')
        jogos = jogos_pc.jogos_da_steam([steamapps])
        self.assertEqual([j["titulo"] for j in jogos], ["Half-Life 2"])   # o Proton e o Lossless Scaling nao sao jogos
        self.assertEqual(jogos[0]["abrir"], "steam://rungameid/220")
        self.assertEqual(jogos[0]["pasta"], os.path.join(steamapps, "common", "Half-Life 2"))

    def test_gog(self):
        pasta = os.path.join(self.pasta, "GOG Games", "Jogo")
        os.makedirs(pasta)
        with open(os.path.join(pasta, "goggame-123.info"), "w", encoding="utf-8") as arquivo:
            json.dump({"name": "Jogo da GOG", "gameId": "123", "playTasks": [
                {"isPrimary": True, "path": "bin/jogo.exe", "arguments": "-tela"}, {"path": "manual.pdf"}]}, arquivo)
        jogos = jogos_pc.jogos_da_gog([os.path.join(self.pasta, "GOG Games")])
        self.assertEqual(jogos[0]["titulo"], "Jogo da GOG")
        self.assertEqual(jogos[0]["abrir"], os.path.join(pasta, "bin", "jogo.exe"))
        self.assertEqual(jogos[0]["argumentos"], "-tela")

    def test_epic(self):
        pasta = os.path.join(self.pasta, "Manifests")
        os.makedirs(pasta)
        with open(os.path.join(pasta, "a.item"), "w", encoding="utf-8") as arquivo:
            json.dump({"DisplayName": "Jogo da Epic", "AppName": "Abc", "InstallLocation": "C:\\J"}, arquivo)
        with open(os.path.join(pasta, "b.item"), "w", encoding="utf-8") as arquivo:
            json.dump({"DisplayName": "Pela metade", "AppName": "Def", "bIsIncompleteInstall": True}, arquivo)
        jogos = jogos_pc.jogos_da_epic(pasta)
        self.assertEqual([j["titulo"] for j in jogos], ["Jogo da Epic"])
        self.assertTrue(jogos[0]["abrir"].startswith("com.epicgames.launcher://apps/Abc"))

    def test_heroic(self):
        pasta = os.path.join(self.pasta, "heroic", "gog_store")
        os.makedirs(pasta)
        with open(os.path.join(pasta, "installed.json"), "w", encoding="utf-8") as arquivo:
            json.dump({"installed": [{"appName": "1", "title": "Jogo", "install_path": "/j", "executable": "jogo.sh"}]}, arquivo)
        jogos = jogos_pc.jogos_do_heroic(os.path.join(self.pasta, "heroic"))
        self.assertEqual(jogos[0]["abrir"], os.path.join("/j", "jogo.sh"))

    def test_entradas_do_manifesto(self):
        with mock.patch.object(jogos_pc, "instalados_no_computador", return_value=[
                {"titulo": "Half-Life 2", "loja": "steam", "chave": "220", "pasta": "P", "abrir": "steam://rungameid/220"}]):
            entradas = jogos_pc.entradas_do_manifesto({"id": "pc", "nome": "PC"})
        self.assertEqual(entradas[0]["id"], "computador/steam/220")
        self.assertEqual(entradas[0]["origem"], "computador")
        self.assertEqual(entradas[0]["origem_rotulo"], "Instalado pela Steam")
        self.assertEqual(entradas[0]["arquivo"], "steam://rungameid/220")

    def test_no_android_nada(self):
        with mock.patch.object(jogos_pc.plataforma_do_sistema, "ANDROID", True):
            self.assertEqual(jogos_pc.entradas_do_manifesto({"id": "pc", "nome": "PC"}), [])


class ComoAbrir(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_pc_")
        self.exe = os.path.join(self.pasta, "j.exe")
        pe(self.exe)
        self.bin = os.path.join(self.pasta, "j")
        elf(self.bin)

    def tearDown(self):
        limpeza.apagar_pasta(self.pasta)

    def test_windows_no_windows_e_linux_no_linux(self):
        self.assertEqual(jogos_pc.comando_para(self.exe, "-x", "windows"), ([self.exe, "-x"], ""))
        with mock.patch.object(jogos_pc.plataforma_do_sistema, "programa_que_roda", side_effect=lambda c, n: c):
            self.assertEqual(jogos_pc.comando_para(self.bin, "", "linux"), ([self.bin], ""))

    def test_windows_no_linux_pelo_wine_ou_explica(self):
        with mock.patch.object(jogos_pc, "wine", return_value=["/usr/bin/wine"]):
            comando, aviso = jogos_pc.comando_para(self.exe, "", "linux")
        self.assertEqual(comando, ["/usr/bin/wine", self.exe])
        self.assertIn("Wine", aviso)
        with mock.patch.object(jogos_pc, "wine", return_value=None):
            with self.assertRaises(jogos_pc.NaoDaParaAbrir) as erro:
                jogos_pc.comando_para(self.exe, "", "linux")
        self.assertIn("Wine", str(erro.exception))

    def test_linux_no_windows_pelo_wsl_ou_explica(self):
        with mock.patch.object(jogos_pc, "wsl", return_value="C:\\Windows\\wsl.exe"):
            comando, aviso = jogos_pc.comando_para("C:\\Jogos\\j", "", "windows", tipo="linux")
        self.assertEqual(comando[0], "C:\\Windows\\wsl.exe")
        self.assertIn("/mnt/c/Jogos/j", comando)
        self.assertIn("WSL", aviso)
        with mock.patch.object(jogos_pc, "wsl", return_value=None):
            with self.assertRaises(jogos_pc.NaoDaParaAbrir):
                jogos_pc.comando_para("C:\\Jogos\\j", "", "windows", tipo="linux")

    def test_atalho_da_loja_e_android(self):
        comando, aviso = jogos_pc.comando_para("steam://rungameid/220", "", "windows")
        self.assertEqual(comando[-1], "steam://rungameid/220")
        self.assertIn("Steam", aviso)
        with self.assertRaises(jogos_pc.NaoDaParaAbrir):
            jogos_pc.comando_para(self.exe, "", "android")

    def test_dos_vai_para_o_dosbox(self):
        dos = os.path.join(self.pasta, "d.exe")
        mz(dos)
        with self.assertRaises(jogos_pc.NaoDaParaAbrir) as erro:
            jogos_pc.comando_para(dos, "", "windows")
        self.assertIn("MS-DOS", str(erro.exception))

    def test_caminho_no_wsl(self):
        self.assertEqual(jogos_pc.caminho_no_wsl("C:\\Jogos\\Meu Jogo\\j"), "/mnt/c/Jogos/Meu Jogo/j")

    def test_externo_para_leva_a_pasta_do_jogo(self):
        externo, aviso = jogos_pc.externo_para({"pasta_do_jogo": self.pasta, "argumentos_do_jogo": "-a"}, self.exe) \
            if jogos_pc.plataforma_do_sistema.WINDOWS else (None, "")
        if externo:
            self.assertEqual(externo["caminho"], self.exe)
            self.assertEqual(externo["dados"]["argumentos"], ["-a"])
            self.assertEqual(externo["dados"]["pasta_trabalho"], self.pasta)


if __name__ == "__main__":
    unittest.main()
