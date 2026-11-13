# -*- coding: utf-8 -*-
"""Recomps (servidor\\recomps.py): o casamento com o titulo, o arquivo certo da release, o download conferido e
descompactado, o recomplauncher.json (programa, caminhos, ajustes, conferencia do disco) e a abertura."""
import io
import json
import os
import struct
import sys
import tempfile
import unittest
import zipfile
from unittest import mock

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PASTA_SERVIDOR not in sys.path:
    sys.path.insert(0, PASTA_SERVIDOR)
import recomps  # noqa: E402

PASTA_TESTES = os.path.join(os.path.dirname(PASTA_SERVIDOR), "testes")
if PASTA_TESTES not in sys.path:
    sys.path.insert(0, PASTA_TESTES)
import limpeza  # noqa: E402

CATALOGO = {
    "por_titulo": {"n64|legendofzeldamajorasmask": ["zelda64recomp"], "xbox360|sonicunleashed": ["unleashedrecomp"]},
    "recomps": {
        "zelda64recomp": {"id": "zelda64recomp", "nome": "Zelda 64: Recompiled", "repo": "Zelda64Recomp/Zelda64Recomp",
                          "licenca": "GPL-3.0", "jogo": "The Legend of Zelda: Majora's Mask", "plataforma": "n64",
                          "sistemas": ["windows", "linux"], "tag": "v1.2.2", "tamanho": "28 MB", "marcas": {},
                          "arquivos": {"windows": "Zelda64Recompiled-*-Windows.zip", "linux": "Zelda64Recompiled-*-Linux-X64.zip"}},
        "unleashedrecomp": {"id": "unleashedrecomp", "nome": "Unleashed Recompiled", "repo": "hedge-dev/UnleashedRecomp",
                            "licenca": "GPL-3.0", "jogo": "Sonic Unleashed", "plataforma": "xbox360",
                            "sistemas": ["windows", "linux"], "tag": "v1.0.3", "tamanho": "51 MB", "marcas": {},
                            "arquivos": {"windows": "UnleashedRecomp-Windows.zip", "linux": "UnleashedRecomp-Flatpak.zip"}},
    },
}


class Catalogo(unittest.TestCase):
    def setUp(self):
        self.antigo = recomps._catalogo["dados"]
        recomps._catalogo["dados"] = CATALOGO

    def tearDown(self):
        recomps._catalogo["dados"] = self.antigo

    def test_chave_iguala_o_nome_do_arquivo_ao_do_catalogo(self):
        self.assertEqual(recomps.chave("Legend of Zelda, The - Majora's Mask (USA)"), "legendofzeldamajorasmask")
        self.assertEqual(recomps.chave("The Legend of Zelda: Majora's Mask"), "legendofzeldamajorasmask")
        self.assertEqual(recomps.chave("Pokémon Snap"), "pokemonsnap")
        self.assertEqual(recomps.chave("Banjo & Kazooie"), "banjoandkazooie")

    def test_acha_o_recomp_pelo_titulo_e_pelo_console(self):
        with mock.patch.object(recomps, "sistema", return_value="windows"):
            lista = recomps.para_o_titulo("Legend of Zelda, the Majora's Mask", "n64")
            self.assertEqual([r["id"] for r in lista], ["zelda64recomp"])
            self.assertEqual(recomps.para_o_titulo("Legend of Zelda, the Majora's Mask", "ps1"), [])
            self.assertEqual(recomps.para_o_titulo("Sonic Unleashed", "xbox360")[0]["id"], "unleashedrecomp")

    def test_sem_versao_para_o_sistema_nao_aparece(self):
        with mock.patch.object(recomps, "sistema", return_value=None):      # Android
            self.assertEqual(recomps.para_o_titulo("Sonic Unleashed", "xbox360"), [])

    def test_jeito_de_abrir_diz_se_ja_esta_aqui(self):
        with mock.patch.object(recomps, "sistema", return_value="windows"), \
                mock.patch.object(recomps, "instalado", return_value=None):
            jeitos = recomps.jeitos_para("Sonic Unleashed", "xbox360")
        self.assertEqual(jeitos[0]["id"], "recomp:unleashedrecomp")
        self.assertEqual(jeitos[0]["selo"], "baixar e jogar")
        self.assertIn("hedge-dev/UnleashedRecomp", jeitos[0]["explica"])
        with mock.patch.object(recomps, "sistema", return_value="windows"), \
                mock.patch.object(recomps, "instalado", return_value="x.exe"):
            self.assertEqual(recomps.jeitos_para("Sonic Unleashed", "xbox360")[0]["selo"], "nativo")


class ArquivoDaRelease(unittest.TestCase):
    NOMES = ["Zelda64Recompiled-v1.2.2-Windows.zip", "Zelda64Recompiled-v1.2.2-Linux-X64.zip",
             "Zelda64Recompiled-v1.2.2-Linux-ARM64.zip", "Zelda64Recompiled-v1.2.2-macOS.zip",
             "Zelda64Recompiled-v1.2.2-Windows-debug.zip", "Zelda64Recompiled-v1.2.2-Windows.zip.sha256"]

    def test_pelo_padrao_do_catalogo(self):
        self.assertEqual(recomps.escolher_arquivo(self.NOMES, "Zelda64Recompiled-*-Windows.zip", "windows"),
                         "Zelda64Recompiled-v1.2.2-Windows.zip")
        self.assertEqual(recomps.escolher_arquivo(self.NOMES, "Zelda64Recompiled-*-Linux-X64.zip", "linux"),
                         "Zelda64Recompiled-v1.2.2-Linux-X64.zip")

    def test_pelas_palavras_do_nome_quando_nao_ha_padrao(self):
        self.assertEqual(recomps.escolher_arquivo(self.NOMES, None, "windows"), "Zelda64Recompiled-v1.2.2-Windows.zip")
        self.assertEqual(recomps.escolher_arquivo(self.NOMES, None, "linux"), "Zelda64Recompiled-v1.2.2-Linux-X64.zip")
        self.assertEqual(recomps.escolher_arquivo(self.NOMES, None, "linux", "arm64"), "Zelda64Recompiled-v1.2.2-Linux-ARM64.zip")

    def test_debug_marca_e_mac_ficam_de_fora(self):
        self.assertIsNone(recomps.escolher_arquivo(["x-debug.zip", "x.sha256", "x-macOS.zip"], None, "windows"))

    def test_zip_antes_de_instalador_e_appimage_antes_de_tar(self):
        self.assertEqual(recomps.escolher_arquivo(["Jogo-Setup.exe", "Jogo-win64.zip"], None, "windows"), "Jogo-win64.zip")
        self.assertEqual(recomps.escolher_arquivo(["Jogo-linux.tar.gz", "Jogo-x86_64.AppImage"], None, "linux"), "Jogo-x86_64.AppImage")

    def test_padrao_sem_par_cai_nas_palavras(self):
        self.assertEqual(recomps.escolher_arquivo(["SoH-Win64.zip", "SoH.appimage"], "SoH-*-Windows.zip", "windows"), "SoH-Win64.zip")


class Release(unittest.TestCase):
    def test_le_os_arquivos_e_a_marca_da_api(self):
        resposta = json.dumps({"tag_name": "v1.2.2", "assets": [
            {"name": "A-Windows.zip", "browser_download_url": "https://github.com/x/a/releases/download/v1.2.2/A-Windows.zip",
             "size": 123, "digest": "sha256:abc"}]}).encode("utf-8")
        with mock.patch.object(recomps.baixar, "rodar", return_value=(0, resposta)):
            rel = recomps.release("x/a", "v1.2.2")
        self.assertEqual(rel["tag"], "v1.2.2")
        self.assertEqual(rel["arquivos"][0]["sha256"], "abc")

    def test_sem_resposta_explica_o_limite_do_github(self):
        with mock.patch.object(recomps.baixar, "rodar", return_value=(22, b"")):
            with self.assertRaises(recomps.NaoDaParaInstalar) as erro:
                recomps.release("x/a", "v1")
        self.assertIn("60 por hora", str(erro.exception))


def zip_de_teste(caminho, com_pasta_por_cima=True, nome_exe="Jogo.exe"):
    with zipfile.ZipFile(caminho, "w") as zip_:
        base = "MeuRecomp-v1/" if com_pasta_por_cima else ""
        zip_.writestr(base + nome_exe, b"MZ" + b"\0" * 100)
        zip_.writestr(base + "unins000.exe", b"MZ" + b"\0" * 500)
        zip_.writestr(base + "leia.txt", "oi")
        zip_.writestr("../fora.txt", "nao pode sair da pasta")


class Instalar(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_recomps_")
        self.antigo = (recomps._catalogo["dados"], recomps.PASTA_RECOMPS)
        recomps._catalogo["dados"] = CATALOGO
        recomps.PASTA_RECOMPS = os.path.join(self.pasta, "Recomps")

    def tearDown(self):
        recomps._catalogo["dados"], recomps.PASTA_RECOMPS = self.antigo
        limpeza.apagar_pasta(self.pasta)

    def _release_falsa(self, nome, marca=""):
        return {"tag": "v1.2.2", "arquivos": [{"nome": nome, "url": "https://github.com/x/y/releases/download/v1.2.2/" + nome,
                                               "tamanho": 10, "sha256": marca}]}

    def test_baixa_confere_descompacta_e_desembrulha(self):
        origem = os.path.join(self.pasta, "origem.zip")
        zip_de_teste(origem)
        marca = recomps._sha256(origem)

        def baixar_falso(url, segundos, destino=None, agente=None):
            with open(origem, "rb") as de, open(destino, "wb") as para:
                para.write(de.read())
            return 0, b""
        with mock.patch.object(recomps, "release", return_value=self._release_falsa("Zelda64Recompiled-v1.2.2-Windows.zip", marca)), \
                mock.patch.object(recomps.baixar, "rodar", side_effect=baixar_falso):
            programa = recomps.instalar("zelda64recomp", "windows", "x64")
        pasta = recomps.pasta_do("zelda64recomp")
        self.assertEqual(programa, os.path.join(pasta, "Jogo.exe"))          # a pasta de cima do zip sumiu
        self.assertTrue(os.path.isfile(os.path.join(pasta, recomps.MARCA)))
        self.assertFalse(os.path.exists(os.path.join(self.pasta, "fora.txt")))   # o '../' nao sai da pasta
        self.assertEqual(recomps.progresso("zelda64recomp")["estado"], "pronto")
        self.assertEqual(recomps.instalado("zelda64recomp"), programa)
        self.assertFalse(os.listdir(os.path.join(recomps.PASTA_RECOMPS, ".baixando")))   # o zip baixado foi embora

    def test_marca_errada_nao_instala(self):
        origem = os.path.join(self.pasta, "origem.zip")
        zip_de_teste(origem)

        def baixar_falso(url, segundos, destino=None, agente=None):
            with open(origem, "rb") as de, open(destino, "wb") as para:
                para.write(de.read())
            return 0, b""
        with mock.patch.object(recomps, "release", return_value=self._release_falsa("Zelda64Recompiled-v1.2.2-Windows.zip", "0" * 64)), \
                mock.patch.object(recomps.baixar, "rodar", side_effect=baixar_falso):
            with self.assertRaises(recomps.NaoDaParaInstalar) as erro:
                recomps.instalar("zelda64recomp", "windows", "x64")
        self.assertIn("SHA-256", str(erro.exception))
        self.assertFalse(os.path.isdir(recomps.pasta_do("zelda64recomp")))
        self.assertEqual(recomps.progresso("zelda64recomp")["estado"], "erro")

    def _com_marca_no_catalogo(self, marca, nome="Zelda64Recompiled-v1.2.2-Windows.zip"):
        catalogo = json.loads(json.dumps(CATALOGO))
        catalogo["recomps"]["zelda64recomp"]["marcas"] = {"windows": {"nome": nome, "sha256": marca}}
        recomps._catalogo["dados"] = catalogo

    def _instalar_com(self, marca_do_github=""):
        origem = os.path.join(self.pasta, "origem.zip")
        zip_de_teste(origem)

        def baixar_falso(url, segundos, destino=None, agente=None):
            with open(origem, "rb") as de, open(destino, "wb") as para:
                para.write(de.read())
            return 0, b""
        with mock.patch.object(recomps, "release", return_value=self._release_falsa("Zelda64Recompiled-v1.2.2-Windows.zip",
                                                                                     marca_do_github)), \
                mock.patch.object(recomps.baixar, "rodar", side_effect=baixar_falso):
            return recomps.instalar("zelda64recomp", "windows", "x64"), recomps._sha256(origem)

    def test_marca_do_catalogo_manda(self):
        """Revisao de seguranca de 12/11/2026: a marca guardada no catalogo (outra fonte) confere o download."""
        origem = os.path.join(self.pasta, "o.zip")
        zip_de_teste(origem)
        self._com_marca_no_catalogo(recomps._sha256(origem))
        self._instalar_com("")
        self.assertTrue(recomps.ler_marca(recomps.pasta_do("zelda64recomp"))["conferido_pelo_catalogo"])

    def test_catalogo_e_github_discordam_nao_instala(self):
        origem = os.path.join(self.pasta, "o.zip")
        zip_de_teste(origem)
        self._com_marca_no_catalogo("f" * 64)
        with self.assertRaises(recomps.NaoDaParaInstalar):
            self._instalar_com(recomps._sha256(origem))     # o GitHub "concorda" com o arquivo, o catalogo nao
        self.assertFalse(os.path.isdir(recomps.pasta_do("zelda64recomp")))

    def test_marca_de_outro_arquivo_so_com_a_do_github(self):
        """A marca do catalogo e' de outra versao (outro nome): instala so se o GitHub publica a marca desta; sem
        nenhuma das duas, recusa (revisao de seguranca de 12/11/2026)."""
        self._com_marca_no_catalogo("f" * 64, nome="Zelda64Recompiled-v1.0-Windows.zip")
        with self.assertRaises(recomps.NaoDaParaInstalar) as erro:
            self._instalar_com("")
        self.assertIn("catálogo", str(erro.exception))
        self.assertFalse(os.path.isdir(recomps.pasta_do("zelda64recomp")))
        origem = os.path.join(self.pasta, "o.zip")
        zip_de_teste(origem)
        self._instalar_com(recomps._sha256(origem))
        self.assertFalse(recomps.ler_marca(recomps.pasta_do("zelda64recomp"))["conferido_pelo_catalogo"])

    def test_o_arquivo_marcado_no_catalogo_vem_primeiro(self):
        """Na release ha dois arquivos que servem; o marcado no catalogo e' o baixado."""
        origem = os.path.join(self.pasta, "o.zip")
        zip_de_teste(origem)
        self._com_marca_no_catalogo(recomps._sha256(origem), nome="Zelda64-Windows-pinado.zip")
        rel = {"tag": "v1", "arquivos": [
            {"nome": n, "url": "https://github.com/x/y/releases/download/v1/" + n, "tamanho": 10, "sha256": ""}
            for n in ("Zelda64Recompiled-v1.2.2-Windows.zip", "Zelda64-Windows-pinado.zip")]}
        baixados = []

        def baixar_falso(url, segundos, destino=None, agente=None):
            baixados.append(url)
            with open(origem, "rb") as de, open(destino, "wb") as para:
                para.write(de.read())
            return 0, b""
        with mock.patch.object(recomps, "release", return_value=rel), \
                mock.patch.object(recomps.baixar, "rodar", side_effect=baixar_falso):
            recomps.instalar("zelda64recomp", "windows", "x64")
        self.assertTrue(baixados[0].endswith("/Zelda64-Windows-pinado.zip"))

    def test_formato_que_o_arena_nao_abre_explica(self):
        with mock.patch.object(recomps, "release", return_value=self._release_falsa("Jogo-Setup.exe")), \
                mock.patch.object(recomps.baixar, "rodar", side_effect=lambda url, s, destino=None, agente=None: (open(destino, "wb").close() or (0, b""))):
            with self.assertRaises(recomps.NaoDaParaInstalar) as erro:
                recomps.instalar("unleashedrecomp", "windows", "x64")
        self.assertIn(".exe", str(erro.exception))

    def test_sem_versao_para_o_sistema(self):
        with mock.patch.object(recomps, "sistema", return_value=None):     # o Android
            with self.assertRaises(recomps.NaoDaParaInstalar):
                recomps.instalar("zelda64recomp", None, "x64")

    def test_versao_nova_por_cima_guarda_o_que_o_jogo_gravou(self):
        origem = os.path.join(self.pasta, "origem.zip")
        zip_de_teste(origem)
        marca = recomps._sha256(origem)

        def baixar_falso(url, segundos, destino=None, agente=None):
            with open(origem, "rb") as de, open(destino, "wb") as para:
                para.write(de.read())
            return 0, b""
        with mock.patch.object(recomps, "release", return_value=self._release_falsa("Zelda64Recompiled-v1.2.2-Windows.zip", marca)), \
                mock.patch.object(recomps.baixar, "rodar", side_effect=baixar_falso):
            recomps.instalar("zelda64recomp", "windows", "x64")
            save = os.path.join(recomps.pasta_do("zelda64recomp"), "saves", "jogo.sav")
            os.makedirs(os.path.dirname(save))
            open(save, "w").close()
            recomps.instalar("zelda64recomp", "windows", "x64")
        self.assertTrue(os.path.isfile(save))


class ProgramaEDescritor(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_recomps_")

    def tearDown(self):
        limpeza.apagar_pasta(self.pasta)

    def _arquivo(self, nome, conteudo=b"MZ" + b"\0" * 10):
        caminho = os.path.join(self.pasta, nome)
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, "wb") as arquivo:
            arquivo.write(conteudo if isinstance(conteudo, bytes) else conteudo.encode("utf-8"))
        return caminho

    def test_sem_descritor_o_maior_exe_que_nao_e_ajudante(self):
        self._arquivo("Jogo.exe", b"MZ" + b"\0" * 300)
        self._arquivo("unins000.exe", b"MZ" + b"\0" * 900)
        self._arquivo("UnityCrashHandler64.exe", b"MZ" + b"\0" * 900)
        self.assertEqual(recomps.programa_na_pasta(self.pasta, "windows"), os.path.join(self.pasta, "Jogo.exe"))

    def test_no_linux_o_appimage_ou_o_elf(self):
        self._arquivo("Jogo-x86_64.AppImage", b"\x7fELF" + b"\0" * 10)
        self.assertEqual(recomps.programa_na_pasta(self.pasta, "linux"), os.path.join(self.pasta, "Jogo-x86_64.AppImage"))
        os.remove(os.path.join(self.pasta, "Jogo-x86_64.AppImage"))
        self._arquivo("jogo", b"\x7fELF" + b"\0" * 10)
        self._arquivo("leia.txt", "nada")
        self.assertEqual(recomps.programa_na_pasta(self.pasta, "linux"), os.path.join(self.pasta, "jogo"))

    def test_descritor_manda_no_programa_e_nos_argumentos(self):
        self._arquivo("bin/game.exe")
        self._arquivo("recomplauncher.json", json.dumps({"format": 1, "start": {"program": ["bin/game.exe", "game.exe"],
                                                                                 "args": ["--iso", "{game}"],
                                                                                 "env": {"MYGAME_DATA": "{install}/dados", "PATH": "x"}}}))
        self.assertEqual(recomps.programa_na_pasta(self.pasta, "windows"), os.path.normpath(os.path.join(self.pasta, "bin", "game.exe")))
        with mock.patch.object(recomps, "recomp", return_value={"nome": "Meu", "id": "meu"}), \
                mock.patch.object(recomps, "pasta_do", return_value=self.pasta), \
                mock.patch.object(recomps, "instalado", return_value=os.path.join(self.pasta, "bin", "game.exe")):
            externo, aviso = recomps.externo_para("meu", os.path.join(self.pasta, "disco.iso"))
        self.assertEqual(externo["dados"]["argumentos"], ["--iso", os.path.join(self.pasta, "disco.iso")])
        self.assertEqual(externo["dados"]["ambiente"], {"MYGAME_DATA": self.pasta + "/dados"})   # o PATH nao passa
        self.assertEqual(aviso, "")

    def test_sem_descritor_avisa_onde_esta_a_copia(self):
        self._arquivo("Jogo.exe")
        with mock.patch.object(recomps, "recomp", return_value={"nome": "Meu", "id": "meu"}), \
                mock.patch.object(recomps, "pasta_do", return_value=self.pasta), \
                mock.patch.object(recomps, "instalado", return_value=os.path.join(self.pasta, "Jogo.exe")):
            externo, aviso = recomps.externo_para("meu", "C:/jogos/rom.z64")
        self.assertEqual(externo["dados"]["argumentos"], [])
        self.assertIn("rom.z64", aviso)

    def test_preencher_as_variaveis(self):
        self.assertEqual(recomps.preencher(["{install}/x", {"a": "{game}"}], {"install": "P", "game": "J"}), ["P/x", {"a": "J"}])
        v = recomps.variaveis("P", "J")
        self.assertEqual((v["install"], v["game"]), ("P", "J"))
        self.assertTrue(v["documents"] and v["local"] and v["config"] and v["home"])

    def test_arquivo_de_ajuste_com_lista_de_lugares(self):
        self._arquivo("portable.txt", "")
        entrada = [{"path": "{install}/game.toml", "if": "{install}/portable.txt"}, {"path": "{documents}/My Game/game.toml"}]
        self.assertEqual(recomps._primeiro_caminho(entrada, {"install": self.pasta, "documents": "D"}), self.pasta + "/game.toml")
        os.remove(os.path.join(self.pasta, "portable.txt"))
        self.assertEqual(recomps._primeiro_caminho(entrada, {"install": self.pasta, "documents": "D"}), "D/My Game/game.toml")


class Ajustes(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_recomps_")

    def tearDown(self):
        limpeza.apagar_pasta(self.pasta)

    def test_toml_linha_a_linha_guarda_comentarios(self):
        caminho = os.path.join(self.pasta, "game.toml")
        with open(caminho, "w", encoding="utf-8") as arquivo:
            arquivo.write("# ajustes\nresolution_scale = \"1\"   # 720p\nfullscreen = \"\"\n")
        descritor = {"config": [{"format": "toml", "file": "{install}/game.toml", "game_path": "game_path",
                                 "always": {"launcher": "\"true\""}, "ensure": {"fullscreen": "\"true\"", "resolution_scale": "\"2\""},
                                 "new": {"nunca": "1"}}]}
        recomps.escrever_configuracao(descritor, recomps.variaveis(self.pasta, "C:\\x\\disco.iso"))
        texto = open(caminho, encoding="utf-8").read()
        self.assertIn("# ajustes\n", texto)
        self.assertIn("resolution_scale = \"1\"   # 720p", texto)        # 'ensure' nao mexe no que ja tem valor
        self.assertIn("fullscreen = \"true\"", texto)                   # 'ensure' preenche o vazio
        self.assertIn("launcher = \"true\"", texto)                     # 'always' acrescenta
        self.assertIn('game_path = "C:\\\\x\\\\disco.iso"', texto)       # a copia do jogo, como string TOML
        self.assertNotIn("nunca", texto)                                # 'new' so em arquivo novo

    def test_arquivo_novo_recebe_os_padroes(self):
        caminho = os.path.join(self.pasta, "x", "game.ini")
        descritor = {"config": {"format": "ini", "file": caminho, "new": {"width": "1280"}, "game_path": "iso"}}
        recomps.escrever_configuracao(descritor, {"game": "D:\\d.iso"})
        texto = open(caminho, encoding="utf-8").read()
        self.assertIn("width = 1280", texto)
        self.assertIn("iso = D:\\d.iso", texto)      # INI: sem aspas

    def test_json(self):
        caminho = os.path.join(self.pasta, "cfg.json")
        with open(caminho, "w", encoding="utf-8") as arquivo:
            json.dump({"a": 1, "vazio": ""}, arquivo)
        descritor = {"config": [{"format": "json", "file": caminho, "ensure": {"vazio": "x", "a": 2}, "always": {"b": 3}}]}
        recomps.escrever_configuracao(descritor, {})
        self.assertEqual(json.load(open(caminho, encoding="utf-8")), {"a": 1, "vazio": "x", "b": 3})


def iso9660_de_teste(caminho, nomes):
    """Uma imagem ISO 9660 minima: o descritor primario no setor 16 e a pasta raiz no setor 18."""
    setor = bytearray(2048)
    setor[0] = 1
    setor[1:6] = b"CD001"
    raiz = bytearray(34)
    raiz[0] = 34
    raiz[2:6] = struct.pack("<I", 18)
    raiz[10:14] = struct.pack("<I", 2048)
    raiz[32] = 1
    raiz[33] = 0
    setor[156:190] = raiz
    pasta = bytearray()
    for nome in [b"\x00", b"\x01"] + [n.encode("ascii") + b";1" for n in nomes]:
        registro = bytearray(33 + len(nome))
        registro[0] = len(registro) + (len(registro) % 2)
        registro[32] = len(nome)
        registro[33:] = nome
        pasta += registro + (b"\0" if len(registro) % 2 else b"")
    with open(caminho, "wb") as disco:
        disco.write(b"\0" * (16 * 2048) + bytes(setor) + b"\0" * 2048 + bytes(pasta).ljust(2048, b"\0"))


def xdvdfs_de_teste(caminho, nomes):
    """Uma imagem XDVDFS minima (deslocamento 0): a marca no setor 32 e a pasta raiz no setor 33."""
    cabecalho = bytearray(2048)
    cabecalho[:20] = b"MICROSOFT*XBOX*MEDIA"
    cabecalho[20:28] = struct.pack("<II", 33, 2048)
    pasta = bytearray()
    for nome in nomes:
        b = nome.encode("ascii")
        entrada = struct.pack("<HHIIB", 0, 0, 40, 100, 0x20) + bytes([len(b)]) + b
        pasta += entrada + b"\0" * ((4 - len(entrada) % 4) % 4)
    pasta += b"\xff" * 4
    with open(caminho, "wb") as disco:
        disco.write(b"\0" * (32 * 2048) + bytes(cabecalho) + bytes(pasta).ljust(2048, b"\0"))


class ConferenciaDoDisco(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_recomps_")

    def tearDown(self):
        limpeza.apagar_pasta(self.pasta)

    def test_iso9660_le_a_raiz(self):
        iso = os.path.join(self.pasta, "d.iso")
        iso9660_de_teste(iso, ["SYSTEM.CNF", "SLUS_206.51"])
        self.assertEqual(recomps.nomes_na_raiz_iso9660(iso), ["SYSTEM.CNF", "SLUS_206.51"])
        self.assertEqual(recomps.conferir_copia({"kind": "iso", "check": {"iso9660": "SLUS_206.51"}}, iso), "")
        erro = recomps.conferir_copia({"kind": "iso", "check": {"iso9660": "SLES_123.45"}, "label": "Precisa da versão USA."}, iso)
        self.assertIn("SLES_123.45", erro)
        self.assertIn("versão USA", erro)

    def test_xdvdfs_le_a_raiz(self):
        iso = os.path.join(self.pasta, "x.iso")
        xdvdfs_de_teste(iso, ["default.xex", "game"])
        self.assertEqual(recomps.nomes_na_raiz_xdvdfs(iso), ["default.xex", "game"])
        self.assertEqual(recomps.conferir_copia({"kind": "iso", "check": {"xdvdfs": "DEFAULT.XEX"}}, iso), "")

    def test_arquivo_que_nao_e_disco(self):
        nada = os.path.join(self.pasta, "nada.iso")
        open(nada, "wb").close()
        self.assertIn("ISO 9660", recomps.conferir_copia({"kind": "iso", "check": {"iso9660": "X"}}, nada))
        self.assertIn("Xbox 360", recomps.conferir_copia({"kind": "iso", "check": {"xdvdfs": "X"}}, nada))

    def test_pasta_e_arquivo_no_tipo_errado(self):
        self.assertIn("pasta", recomps.conferir_copia({"kind": "iso"}, self.pasta))
        arquivo = os.path.join(self.pasta, "a.bin")
        open(arquivo, "wb").close()
        self.assertIn("pasta", recomps.conferir_copia({"kind": "folder"}, arquivo))
        self.assertIn("default.xex", recomps.conferir_copia({"kind": "folder", "check": {"file": "default.xex"}}, self.pasta))
        self.assertEqual(recomps.conferir_copia(None, arquivo), "")


class Preparo(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_recomps_")

    def tearDown(self):
        limpeza.apagar_pasta(self.pasta)

    def test_roda_o_preparo_uma_vez_e_le_o_andamento(self):
        preparo = os.path.join(self.pasta, "preparo.py")
        with open(preparo, "w", encoding="utf-8") as arquivo:
            arquivo.write("import sys\nprint('progress 0.5 Metade')\nprint('progress 1 Fim')\nopen('feito.txt','w').write(sys.argv[-1])\n")
        descritor = {"prepare": {"program": ["preparo.py"], "args": ["{game}"], "label": "Arte do disco", "timeout": 60}}
        python, popen = sys.executable, recomps.subprocess.Popen
        with mock.patch.object(recomps.subprocess, "Popen", side_effect=lambda cmd, **kw: popen([python] + cmd, **kw)):
            self.assertEqual(recomps.preparar(descritor, self.pasta, "D:\\disco.iso", "meu", avisar=lambda m: None), "")
        self.assertEqual(open(os.path.join(self.pasta, "feito.txt")).read(), "D:\\disco.iso")
        self.assertEqual(recomps.progresso("meu")["feito"], 100)
        os.remove(os.path.join(self.pasta, "feito.txt"))
        # Segunda vez, mesma copia: nao roda de novo.
        self.assertEqual(recomps.preparar(descritor, self.pasta, "D:\\disco.iso", "meu"), "")
        self.assertFalse(os.path.exists(os.path.join(self.pasta, "feito.txt")))

    def test_preparo_que_falha_explica(self):
        preparo = os.path.join(self.pasta, "preparo.py")
        with open(preparo, "w", encoding="utf-8") as arquivo:
            arquivo.write("raise SystemExit(3)\n")
        descritor = {"prepare": {"program": ["preparo.py"], "args": []}}
        popen = recomps.subprocess.Popen
        with mock.patch.object(recomps.subprocess, "Popen", side_effect=lambda cmd, **kw: popen([sys.executable] + cmd, **kw)):
            self.assertIn("código 3", recomps.preparar(descritor, self.pasta, "x.iso", "meu2", avisar=lambda m: None))



class TestDesempenhoPorMaquina(unittest.TestCase):
    """O perfil do motor RT64 por maquina (13/11/2026): so chaves conferidas, so o que falta, nada na placa forte."""

    def test_placa_forte_nao_muda_nada(self):
        self.assertIsNone(recomps.ajuste_da_maquina("zelda64recomp", 5))
        self.assertIsNone(recomps.ajuste_da_maquina("recomp-que-nao-tem-perfil", 1))

    def test_placa_fraca_no_windows(self):
        perfil = recomps.ajuste_da_maquina("zelda64recomp", 2, windows=True)
        self.assertEqual(perfil["file"], "{local}/Zelda64Recompiled/graphics.json")
        self.assertEqual(perfil["ensure"]["res_option"], "Original")
        self.assertEqual(perfil["ensure"]["msaa_option"], "None")
        self.assertEqual(perfil["ensure"]["hpfb_option"], "Off")

    def test_mario_kart_nao_tem_hpfb_e_linux_usa_o_home(self):
        perfil = recomps.ajuste_da_maquina("mariokart64recomp", 3, windows=False)
        self.assertNotIn("hpfb_option", perfil["ensure"])
        self.assertEqual(perfil["file"], "{home}/.config/MarioKart64Recompiled/graphics.json")
        self.assertEqual(perfil["ensure"]["rr_option"], "Manual")

    def test_so_grava_o_que_falta(self):
        pasta = tempfile.mkdtemp(prefix="arena_rt64_")
        self.addCleanup(limpeza.apagar_pasta, pasta)
        arquivo = os.path.join(pasta, "Zelda64Recompiled", "graphics.json")
        os.makedirs(os.path.dirname(arquivo))
        with open(arquivo, "w", encoding="utf-8") as saida:
            json.dump({"res_option": "Auto"}, saida)       # a escolha da pessoa dentro do jogo
        perfil = recomps.ajuste_da_maquina("zelda64recomp", 1, windows=True)
        recomps.escrever_configuracao({"config": [perfil]}, {"local": pasta})
        with open(arquivo, encoding="utf-8") as entrada:
            dados = json.load(entrada)
        self.assertEqual(dados["res_option"], "Auto")          # ficou a dela
        self.assertEqual(dados["msaa_option"], "None")         # o que faltava entrou


if __name__ == "__main__":
    unittest.main()
