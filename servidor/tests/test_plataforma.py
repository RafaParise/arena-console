# -*- coding: utf-8 -*-
"""O que muda entre o Windows e o Linux (servidor\\plataforma.py, item 13 do
plano de 15/10/2026: "uma versao do ARENA para linux perfeitamente identico").

Cada teste roda nos dois sistemas: o lado do outro sistema e' imitado
trocando plataforma.WINDOWS, para a logica dos dois ficar conferida em
qualquer computador. O teste de verdade no Linux (o RetroArch abrindo o
jogo) e' testes\\teste_linux.py, no conteiner."""
import os
import sys
import tempfile
import unittest
from unittest import mock

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PASTA_SERVIDOR not in sys.path:
    sys.path.insert(0, PASTA_SERVIDOR)

import graficos  # noqa: E402
import plataforma  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(PASTA_SERVIDOR), "testes"))
import limpeza  # noqa: E402


def no_windows(sim):
    return mock.patch.object(plataforma, "WINDOWS", sim)


class Nucleos(unittest.TestCase):
    def test_o_nucleo_do_linux_e_o_so(self):
        with no_windows(False):
            self.assertEqual(plataforma.arquivo_do_nucleo("fceumm_libretro.dll"), "fceumm_libretro.so")
            self.assertEqual(plataforma.arquivo_do_nucleo("fceumm_libretro.so"), "fceumm_libretro.so")
            self.assertEqual(plataforma.arquivo_do_nucleo(""), "")
        with no_windows(True):
            self.assertEqual(plataforma.arquivo_do_nucleo("fceumm_libretro.dll"), "fceumm_libretro.dll")

    def test_o_catalogo_troca_os_tres_campos(self):
        catalogo = [{"id": "ps1", "core": "swanstation_libretro.dll", "core_netplay": "pcsx_rearmed_libretro.dll",
                     "core_sem_bios": "pcsx_rearmed_libretro.dll"}, {"id": "sem_nucleo"}]
        with no_windows(False):
            linux = plataforma.nucleos_deste_sistema([dict(p) for p in catalogo])
        self.assertEqual(linux[0]["core"], "swanstation_libretro.so")
        self.assertEqual(linux[0]["core_netplay"], "pcsx_rearmed_libretro.so")
        self.assertEqual(linux[1], {"id": "sem_nucleo"})
        with no_windows(True):
            self.assertEqual(plataforma.nucleos_deste_sistema(catalogo), catalogo)

    def test_nome_curto_nos_dois(self):
        for arquivo in ("swanstation_libretro.dll", "/arena/retroarch/cores/swanstation_libretro.so",
                        "SwanStation_Libretro.DLL"):
            self.assertEqual(plataforma.nome_curto_do_nucleo(arquivo), "swanstation")

    def test_programas_de_cada_sistema(self):
        with no_windows(False):
            self.assertTrue(plataforma.executavel_do_retroarch("/a/retroarch").endswith(".AppImage"))
            self.assertTrue(plataforma.python_que_veio_junto("/a/servidor").endswith(
                os.path.join("python-linux", "bin", "python3.13")))
        with no_windows(True):
            self.assertTrue(plataforma.executavel_do_retroarch("r").endswith("retroarch.exe"))


class TirarDoAppImage(unittest.TestCase):
    """O AppImage sai para o cache sem FUSE (plataforma._tirar_do_appimage)."""

    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_appimage_")

    def tearDown(self):
        limpeza.apagar_pasta(self.pasta)

    def extrair(self, com_atalho):
        appimage = os.path.join(self.pasta, "Programa.AppImage")
        with open(appimage, "wb") as arquivo:
            arquivo.write(b"AppImage de mentira")

        def tirar(comando, cwd, **_):
            base = os.path.join(cwd, "AppDir" if com_atalho else "squashfs-root")
            os.makedirs(os.path.join(base, "usr"))
            with open(os.path.join(base, "AppRun"), "w", encoding="utf-8") as arquivo:
                arquivo.write("#!/bin/sh\n")
            if com_atalho:
                os.symlink("./AppDir", os.path.join(cwd, "squashfs-root"), target_is_directory=True)
            return mock.Mock(returncode=0, stdout=b"", stderr=b"")

        destino = os.path.join(self.pasta, "cache", "programa-19")
        os.makedirs(os.path.dirname(destino))
        with mock.patch.object(plataforma.subprocess, "run", side_effect=tirar), \
                mock.patch.object(plataforma, "_roda", side_effect=os.path.isfile), \
                mock.patch.object(plataforma.os, "chmod"):
            plataforma._tirar_do_appimage(appimage, destino)
        return destino

    def test_a_pasta_squashfs_root(self):
        destino = self.extrair(com_atalho=False)
        self.assertTrue(os.path.isfile(os.path.join(destino, "AppRun")))

    def test_o_atalho_para_appdir_leva_a_pasta_de_verdade(self):
        try:
            destino = self.extrair(com_atalho=True)
        except OSError as falha:
            if getattr(falha, "winerror", None) == 1314:      # Windows sem o Modo de Desenvolvedor
                self.skipTest("este Windows nao deixa criar link")
            raise
        self.assertFalse(os.path.islink(destino))
        self.assertTrue(os.path.isfile(os.path.join(destino, "AppRun")))


class Motores(unittest.TestCase):
    """O som, o controle e o video que so existem num dos sistemas."""

    def test_no_linux_o_do_windows_vira_o_do_linux(self):
        opcoes = {"audio_driver": "wasapi", "input_joypad_driver": "xinput", "video_driver": "d3d11",
                  "input_driver": "dinput", "microphone_driver": "wasapi", "menu_driver": "rgui"}
        with no_windows(False), mock.patch.object(plataforma, "motor_de_som_do_linux", return_value="pulse"):
            plataforma.motores_deste_sistema(opcoes)
        self.assertEqual(opcoes, {"audio_driver": "pulse", "input_joypad_driver": "udev", "video_driver": "glcore",
                                  "input_driver": "x", "microphone_driver": "alsa", "menu_driver": "rgui"})

    def test_no_windows_o_do_linux_vira_o_do_windows(self):
        opcoes = {"audio_driver": "pulse", "input_joypad_driver": "udev", "input_driver": "x"}
        with no_windows(True):
            plataforma.motores_deste_sistema(opcoes)
        self.assertEqual(opcoes, {"audio_driver": "wasapi", "input_joypad_driver": "xinput", "input_driver": "dinput"})

    def test_o_que_existe_nos_dois_fica(self):
        for sim in (True, False):
            opcoes = {"video_driver": "vulkan", "input_joypad_driver": "sdl2", "audio_driver": "sdl2"}
            with no_windows(sim):
                self.assertEqual(plataforma.motores_deste_sistema(dict(opcoes)), opcoes)
            opcoes = {"video_driver": "glcore"}
            with no_windows(sim):
                self.assertEqual(plataforma.motores_deste_sistema(dict(opcoes)), opcoes)

    def test_som_do_linux_pelo_servidor_de_som(self):
        pasta = tempfile.mkdtemp(prefix="arena_som_")
        try:
            sem = {"XDG_RUNTIME_DIR": pasta}
            with mock.patch.dict(os.environ, sem, clear=False):
                os.environ.pop("PULSE_SERVER", None)
                self.assertEqual(plataforma.motor_de_som_do_linux(), "alsa")
                os.makedirs(os.path.join(pasta, "pulse"))
                with open(os.path.join(pasta, "pulse", "native"), "w"):
                    pass
                self.assertEqual(plataforma.motor_de_som_do_linux(), "pulse")
            with mock.patch.dict(os.environ, {"XDG_RUNTIME_DIR": os.path.join(pasta, "nada"),
                                              "PULSE_SERVER": "unix:/x"}):
                self.assertEqual(plataforma.motor_de_som_do_linux(), "pulse")
        finally:
            limpeza.apagar_pasta(pasta)


class CfgDosDoisSistemas(unittest.TestCase):
    """O retroarch.cfg que um sistema gravou, aberto no outro."""

    def setUp(self):
        self.antes = (graficos.RAIZ, graficos.PASTA_RETROARCH)
        self.base = tempfile.mkdtemp(prefix="arena_cfg_sistemas_")
        graficos.RAIZ = self.base
        graficos.PASTA_RETROARCH = os.path.join(self.base, "retroarch")
        os.makedirs(graficos.PASTA_RETROARCH)

    def tearDown(self):
        graficos.RAIZ, graficos.PASTA_RETROARCH = self.antes
        limpeza.apagar_pasta(self.base)

    def corrigir(self, linhas, windows):
        cfg = os.path.join(graficos.PASTA_RETROARCH, "retroarch.cfg")
        with open(cfg, "w", encoding="utf-8") as arquivo:
            arquivo.writelines('%s = "%s"\n' % par for par in linhas.items())
        with no_windows(windows), mock.patch.object(plataforma, "motor_de_som_do_linux", return_value="alsa"):
            graficos.corrigir_caminhos_retroarch_cfg()
        with open(cfg, encoding="utf-8") as arquivo:
            return {c.strip(): v.strip().strip('"') for c, v in (l.split("=", 1) for l in arquivo if "=" in l)}

    def test_cfg_do_windows_no_linux(self):
        valores = self.corrigir({"audio_driver": "wasapi", "input_joypad_driver": "xinput",
                                 "video_driver": "vulkan", "menu_driver": "rgui"}, windows=False)
        self.assertEqual((valores["audio_driver"], valores["input_joypad_driver"]), ("alsa", "udev"))
        self.assertEqual((valores["video_driver"], valores["menu_driver"]), ("vulkan", "rgui"))

    def test_cfg_do_linux_no_windows(self):
        valores = self.corrigir({"audio_driver": "pulse", "input_joypad_driver": "udev", "input_driver": "x"},
                                windows=True)
        self.assertEqual(valores["audio_driver"], "wasapi")
        self.assertEqual(valores["input_joypad_driver"], "xinput")
        self.assertEqual(valores["input_driver"], "dinput")


class Pastas(unittest.TestCase):
    """Abrir a pasta e mostrar o arquivo no gerenciador de arquivos."""

    def test_linux_abre_pela_xdg_open(self):
        chamadas = []
        with no_windows(False), mock.patch.object(plataforma.shutil, "which", side_effect=lambda n: "/usr/bin/" + n), \
                mock.patch.object(plataforma.subprocess, "Popen", side_effect=lambda c, **k: chamadas.append(c)):
            plataforma.abrir_pasta("/media/aluno/PEN/ARENA/jogos")
        self.assertEqual(chamadas, [["xdg-open", "/media/aluno/PEN/ARENA/jogos"]])

    def test_linux_sem_xdg_open_usa_o_gio(self):
        chamadas = []
        with no_windows(False), \
                mock.patch.object(plataforma.shutil, "which", side_effect=lambda n: "/usr/bin/gio" if n == "gio" else None), \
                mock.patch.object(plataforma.subprocess, "Popen", side_effect=lambda c, **k: chamadas.append(c)):
            plataforma.abrir_pasta("/x")
        self.assertEqual(chamadas, [["gio", "open", "/x"]])

    def test_linux_sem_nada_avisa(self):
        with no_windows(False), mock.patch.object(plataforma.shutil, "which", return_value=None):
            with self.assertRaises(plataforma.SemGerenciadorDeArquivos):
                plataforma.abrir_pasta("/x")
            with self.assertRaises(plataforma.SemGerenciadorDeArquivos):
                plataforma.mostrar_arquivo("/x/pacote.zip")

    @unittest.skipIf(os.name == "nt", "o caminho do Linux so se monta no Linux")
    def test_linux_mostra_o_arquivo_marcado_com_acento_no_caminho(self):
        chamadas = []
        with no_windows(False), mock.patch.object(plataforma.shutil, "which", side_effect=lambda n: "/usr/bin/" + n), \
                mock.patch.object(plataforma.subprocess, "Popen", side_effect=lambda c, **k: chamadas.append(c)):
            plataforma.mostrar_arquivo("/media/aluno/Pedagógicos/backup/meu progresso.zip")
        comando = chamadas[0]
        self.assertEqual(comando[:2], ["sh", "-c"])
        # O endereco vai codificado (o "ó" e o espaco) e como argumento, nunca
        # dentro do texto do sh: nome de arquivo nao vira comando.
        self.assertEqual(comando[4], "file:///media/aluno/Pedag%C3%B3gicos/backup/meu%20progresso.zip")
        self.assertEqual(comando[5], "/media/aluno/Pedagógicos/backup")
        self.assertNotIn("Pedag", comando[2])


class EmuladoresDeFora(unittest.TestCase):
    """PS2, PS3, Xbox 360 (e o Dolphin, se houver): no Linux, o programa de
    la fica na mesma pasta do de Windows e usa a mesma pasta de dados."""

    def test_dados_no_linux(self):
        base = os.path.join(os.sep, "pen", "ARENA", "emuladores")
        with no_windows(False):
            pcsx2 = plataforma.dados_do_externo("PCSX2", os.path.join(base, "PCSX2", "PCSX2", "pcsx2.AppImage"))
            rpcs3 = plataforma.dados_do_externo("RPCS3", os.path.join(base, "RPCS3", "RPCS3", "rpcs3.AppImage"))
            xenia = plataforma.dados_do_externo("Xenia", os.path.join(base, "Xenia", "Xenia", "xenia_canary"))
            dolphin = plataforma.dados_do_externo("Dolphin", os.path.join(base, "Dolphin", "D", "dolphin-emu"))
        self.assertEqual(pcsx2, (os.path.join(base, "PCSX2", "PCSX2", "pcsx2.AppImage"),
                                 {"XDG_CONFIG_HOME": os.path.join(base, "PCSX2")}, []))
        self.assertEqual(rpcs3[0], os.path.join(base, "RPCS3", "rpcs3", "rpcs3.AppImage"))
        self.assertEqual(rpcs3[1], {"XDG_CONFIG_HOME": os.path.join(base, "RPCS3")})
        self.assertEqual(xenia[2], ["--storage_root=" + os.path.join(base, "Xenia", "Xenia")])
        self.assertEqual(dolphin[2], ["-u", os.path.join(base, "Dolphin", "D", "User")])

    def test_no_windows_nada_muda(self):
        with no_windows(True):
            self.assertEqual(plataforma.dados_do_externo("PCSX2", "C:\\a\\pcsx2-qt.exe"),
                             ("C:\\a\\pcsx2-qt.exe", {}, []))
            self.assertEqual(plataforma.programa_que_roda("C:\\a\\pcsx2-qt.exe", "PCSX2"), "C:\\a\\pcsx2-qt.exe")

    def test_acha_o_appimage_do_linux_pela_versao_no_nome(self):
        catalogo = {"externo": {"nome": "PCSX2", "pasta": "PCSX2", "executaveis": ["pcsx2-qt.exe"],
                                "executaveis_linux": ["pcsx2*.appimage", "pcsx2-qt"]}}
        pasta = tempfile.mkdtemp(prefix="arena_externo_linux_")
        try:
            programa = os.path.join(pasta, "PCSX2", "PCSX2")
            os.makedirs(programa)
            for nome in ("pcsx2-qt.exe", "pcsx2-v2.8.1-linux-appimage-x64-Qt.AppImage"):
                open(os.path.join(programa, nome), "wb").close()
            with mock.patch.object(graficos, "PASTA_EMULADORES", pasta):
                with mock.patch.object(graficos, "NO_WINDOWS", False):
                    linux, _c, _d = graficos.achar_externo_detalhado(catalogo)
                with mock.patch.object(graficos, "NO_WINDOWS", True):
                    windows, _c, _d = graficos.achar_externo_detalhado(catalogo)
            self.assertEqual(os.path.basename(linux), "pcsx2-v2.8.1-linux-appimage-x64-Qt.AppImage")
            self.assertEqual(os.path.basename(windows), "pcsx2-qt.exe")
        finally:
            limpeza.apagar_pasta(pasta)

    def test_o_catalogo_tem_o_programa_do_linux_de_cada_externo(self):
        import json
        with open(os.path.join(PASTA_SERVIDOR, "consoles.json"), encoding="utf-8") as arquivo:
            externos = [p["externo"] for p in json.load(arquivo)["plataformas"] if p.get("externo")]
        self.assertTrue(externos)
        for externo in externos:
            self.assertTrue(externo.get("executaveis_linux"), externo["nome"])


class RecursosDaTela(unittest.TestCase):
    """O recursos.json no Linux: as opcoes de la ("no_linux") e sem o que
    so existe no Windows ("so_windows")."""

    def setUp(self):
        import json
        with open(os.path.join(PASTA_SERVIDOR, "recursos.json"), encoding="utf-8") as arquivo:
            self.dados = json.load(arquivo)

    def por_chave(self, windows):
        import arena
        return {r["chave"]: r for r in arena.recursos_deste_sistema(self.dados, windows=windows)["recursos"]}

    def test_no_linux(self):
        linux = self.por_chave(False)
        self.assertEqual(linux["input_joypad_driver"]["opcoes"], ["udev", "sdl2"])
        self.assertEqual(linux["audio_driver"]["opcoes"], ["pulse", "alsa"])
        self.assertNotIn("d3d11", linux["video_driver"]["opcoes"])
        self.assertNotIn("audio_wasapi_exclusive_mode", linux)
        self.assertIn("udev", linux["input_joypad_driver"]["explica"])

    def test_no_windows_fica_como_esta(self):
        windows = self.por_chave(True)
        self.assertEqual(windows["input_joypad_driver"]["opcoes"], ["xinput", "dinput"])
        self.assertIn("d3d11", windows["video_driver"]["opcoes"])
        self.assertIn("audio_wasapi_exclusive_mode", windows)

    def test_o_padrao_do_arena_vale_nos_dois(self):
        """O valor que o ARENA grava por padrao, traduzido para o sistema,
        tem que estar entre as opcoes que a tela mostra nele."""
        import arena
        padrao = dict(arena.BASE_COMUM, **arena.AVANCADO_PADRAO)
        for windows in (True, False):
            recursos = self.por_chave(windows)
            with no_windows(windows), mock.patch.object(plataforma, "motor_de_som_do_linux", return_value="pulse"):
                traduzido = plataforma.motores_deste_sistema(dict(padrao))
            for chave in ("audio_driver", "input_joypad_driver"):
                self.assertIn(traduzido[chave], recursos[chave]["opcoes"], (windows, chave))


class Sistema(unittest.TestCase):
    def test_nome_do_sistema(self):
        self.assertIn(plataforma.nome_do_sistema(), ("windows", "linux", "chromeos"))
        self.assertTrue(plataforma.descricao())

    def test_chromebook_so_no_linux(self):
        with mock.patch.object(plataforma, "LINUX", False):
            self.assertFalse(plataforma.no_chromebook())


if __name__ == "__main__":
    unittest.main()
