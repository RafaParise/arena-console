# -*- coding: utf-8 -*-
"""O Java ME (celular antigo), ligado em 15/10/2026: o nucleo FreeJ2ME-Plus,
a metade Java dele (freej2me-lr.jar, nas BIOS livres), o Java que vem no
ARENA (emuladores\\Java, servidor\\java_do_arena.py), a ponte sem acento e a
caixa do Windows que fecha o Java que sobrar (servidor\\processos.py). A
abertura de verdade, com o jogo livre Shooter, esta em
testes\\teste_consoles_livres.py."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)
import bios  # noqa: E402
import java_do_arena  # noqa: E402
import ponte_sem_acento as ponte  # noqa: E402
import processos  # noqa: E402

NUCLEO = "freej2me_libretro.dll"


def plataforma_j2me():
    with open(os.path.join(RAIZ, "consoles.json"), encoding="utf-8") as arquivo:
        return next(p for p in json.load(arquivo)["plataformas"] if p["id"] == "j2me")


class TestJavaMeNoCatalogo(unittest.TestCase):
    def test_nucleo_java_e_video_sem_thread(self):
        j2me = plataforma_j2me()
        self.assertEqual(j2me["core"], NUCLEO)
        self.assertEqual(j2me["extensoes"], [".jar", ".kjx"])   # o .jad o FreeJ2ME-Plus nao abre
        self.assertIs(j2me["usa_java"], True)
        # Com o video em thread, o RetroArch travava ao fechar (15/10/2026).
        self.assertEqual(j2me["opcoes_retroarch"], {"video_threaded": "false"})
        self.assertIs(j2me["netplay"], False)
        self.assertIn("Netplay", j2me["netplay_motivo"])
        self.assertNotIn("Precisa do Java instalado", j2me["descricao"])

    def test_a_metade_java_vem_nas_livres_com_a_marca_certa(self):
        lista = bios.livres()
        item = next(i for i in lista["arquivos"] if i["projeto"] == "FreeJ2ME-Plus")
        self.assertEqual(item["destino"], "freej2me-lr.jar")
        caminho = os.path.join(RAIZ, "bios_livres", *item["origem"].split("/"))
        with open(caminho, "rb") as arquivo:
            self.assertEqual(hashlib.sha256(arquivo.read()).hexdigest(), item["sha256"])
        self.assertTrue(os.path.isfile(os.path.join(RAIZ, "bios_livres", "FreeJ2ME-Plus", "LICENSE.txt")))
        self.assertIn("GPL-3.0", lista["projetos"]["FreeJ2ME-Plus"]["licenca"])

    def test_instala_na_system_e_nao_conta_como_bios_que_falta(self):
        sistema = tempfile.mkdtemp(prefix="arena_j2me_system_")
        try:
            bios.instalar_livres(sistema)
            jar = os.path.join(sistema, "freej2me-lr.jar")
            self.assertTrue(os.path.isfile(jar))
            self.assertTrue(bios.e_livre(jar))
            self.assertEqual(bios.falta_para_o_console("j2me", sistema), "")
        finally:
            shutil.rmtree(sistema, ignore_errors=True)


class TestJavaDoArena(unittest.TestCase):
    def setUp(self):
        self.base = tempfile.mkdtemp(prefix="arena_java_")
        self.java = os.path.join(self.base, "Java")
        os.makedirs(os.path.join(self.java, "bin"))

    def tearDown(self):
        shutil.rmtree(self.base, ignore_errors=True)

    def test_o_java_do_arena_vai_na_frente_do_path(self):
        with open(os.path.join(self.java, "bin", "javaw.exe"), "wb") as arquivo:
            arquivo.write(b"MZ")
        # "Path" com letra minuscula: e' assim que muito Windows guarda.
        ambiente = java_do_arena.ambiente({"Path": r"C:\Windows;C:\Program Files\Java\bin", "X": "1"},
                                          pasta=self.java)
        self.assertEqual(ambiente["Path"].split(os.pathsep)[0], os.path.join(self.java, "bin"))
        self.assertIn(r"C:\Program Files\Java\bin", ambiente["Path"])
        self.assertNotIn("PATH", ambiente)
        self.assertEqual(ambiente["X"], "1")

    def test_sem_o_java_do_arena_o_path_fica_como_esta(self):
        self.assertIsNone(java_do_arena.javaw(self.java))
        ambiente = java_do_arena.ambiente({"PATH": r"C:\Windows"}, pasta=self.java)
        self.assertEqual(ambiente, {"PATH": r"C:\Windows"})

    def test_o_java_do_pacote_fica_em_emuladores(self):
        self.assertEqual(java_do_arena.PASTA_JAVA,
                         os.path.join(os.path.dirname(RAIZ), "emuladores", "Java"))


class TestPonteDoJavaMe(unittest.TestCase):
    def setUp(self):
        self.base = tempfile.mkdtemp(prefix="arena_ponte_j2me_")
        self.sistema = os.path.join(self.base, "Pedagógicos", "system")
        os.makedirs(self.sistema)
        with open(os.path.join(self.sistema, "freej2me-lr.jar"), "wb") as arquivo:
            arquivo.write(b"PK" + b"jar" * 100)
        self.temporaria = os.path.join(self.base, "temp")
        os.makedirs(self.temporaria)
        self.antes = tempfile.tempdir
        tempfile.tempdir = self.temporaria

    def tearDown(self):
        tempfile.tempdir = self.antes
        shutil.rmtree(self.base, ignore_errors=True)

    def test_system_com_acento_vai_pela_ponte_com_o_jar(self):
        jogo = os.path.join(self.base, "jogo.jar")
        with open(jogo, "wb") as arquivo:
            arquivo.write(b"PKjogo")
        # O jogo nao tem acento, mas a system tem: o nucleo nao acharia o jar.
        self.assertTrue(ponte.precisa(NUCLEO, self.sistema, jogo))
        caminho, opcoes, devolver = ponte.preparar(NUCLEO, self.sistema, jogo)
        try:
            self.assertEqual(caminho, jogo)
            self.assertTrue(opcoes["system_directory"].isascii())
            with open(os.path.join(opcoes["system_directory"], "freej2me-lr.jar"), "rb") as arquivo:
                self.assertEqual(arquivo.read(), b"PK" + b"jar" * 100)
        finally:
            devolver()
        self.assertFalse(os.path.exists(opcoes["system_directory"]))


class TestMotivoDoErroDoJava(unittest.TestCase):
    """As linhas de verdade do registro (15/10/2026): sem o Java, o nucleo
    'abre' e a tela fica preta, sem o "Falha ao carregar o conteudo"."""

    def test_sem_o_java(self):
        import motivo_do_erro
        texto = ("[libretro INFO] Trying to create process... \n"
                 "[libretro ERROR] Couldn't create process, error: 2\n"
                 "[ERROR] [Environ] SET_MESSAGE_EXT: FreeJ2ME could not start! \n"
                 "Make sure that you have Java 6 or newer installed.\n")
        resultado = motivo_do_erro.analisar(texto, r"C:\ARENA\jogos\J2ME\jogo.jar", NUCLEO)
        self.assertIn("emuladores\\Java", resultado["texto"])

    def test_sem_o_jar_na_system(self):
        import motivo_do_erro
        texto = "[libretro ERROR] Error: freej2me-lr.jar does not exist in the system dir.\n"
        resultado = motivo_do_erro.analisar(texto, r"C:\ARENA\jogos\J2ME\jogo.jar", NUCLEO)
        self.assertIn("freej2me-lr.jar", resultado["texto"])

    def test_abriu_nao_diz_nada(self):
        import motivo_do_erro
        texto = "[libretro INFO] Sent app file and save paths to Java app.\n"
        self.assertIsNone(motivo_do_erro.analisar(texto, r"C:\ARENA\jogos\J2ME\jogo.jar", NUCLEO))


@unittest.skipUnless(sys.platform.startswith("win"), "a caixa (Job Object) e' do Windows")
class TestCaixaQueFechaOsFilhos(unittest.TestCase):
    def test_o_neto_que_sobra_fecha_com_a_caixa(self):
        # Um processo que abre um "neto" (como o RetroArch abre o Java) e
        # diz o numero dele. O pai cai; o neto so fecha com a caixa.
        codigo = ("import subprocess, sys, time\n"
                  "neto = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
                  "print(neto.pid, flush=True)\n"
                  "time.sleep(60)\n")
        pai = subprocess.Popen([sys.executable, "-c", codigo], stdout=subprocess.PIPE, text=True)
        caixa = processos.caixa_que_fecha_os_filhos(pai.pid)
        neto = None
        try:
            self.assertTrue(caixa)
            neto = int(pai.stdout.readline())
            pai.kill()
            pai.wait()
            self.assertTrue(_vivo(neto))            # sem a caixa, ficaria aberto
            processos.fechar_caixa(caixa)
            caixa = None
            for _ in range(50):
                if not _vivo(neto):
                    break
                time.sleep(0.1)
            self.assertFalse(_vivo(neto))
        finally:
            processos.fechar_caixa(caixa)
            if pai.poll() is None:
                pai.kill()
            pai.stdout.close()
            if neto and _vivo(neto):
                subprocess.run(["taskkill", "/F", "/PID", str(neto)], capture_output=True)

    def test_fora_do_windows_ou_sem_processo_nao_quebra(self):
        self.assertIsNone(processos.caixa_que_fecha_os_filhos(0))
        processos.fechar_caixa(None)


def _vivo(pid):
    """O processo ainda esta rodando? (OpenProcess + GetExitCodeProcess)."""
    import ctypes
    import ctypes.wintypes as w
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.OpenProcess.restype = w.HANDLE
    k.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
    k.GetExitCodeProcess.argtypes = [w.HANDLE, ctypes.POINTER(w.DWORD)]
    k.CloseHandle.argtypes = [w.HANDLE]
    h = k.OpenProcess(0x1000, False, pid)        # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return False
    try:
        codigo = w.DWORD()
        return bool(k.GetExitCodeProcess(h, ctypes.byref(codigo))) and codigo.value == 259   # STILL_ACTIVE
    finally:
        k.CloseHandle(h)


if __name__ == "__main__":
    unittest.main()
