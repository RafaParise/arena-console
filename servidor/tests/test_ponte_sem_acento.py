# -*- coding: utf-8 -*-
"""A ponte sem acento (servidor\\ponte_sem_acento.py). O Hatari (Atari ST)
nao abre caminho com acento: com o ARENA em "...Pedagógicos\\...", a BIOS e
o disquete vao por uma pasta sem acento, e o disquete volta se o jogo gravou
nele. A abertura de verdade, com o "ó" no caminho, esta em
testes\\teste_consoles_livres.py.

No Linux (item 13) a ponte nao existe (todo nucleo abre caminho com acento):
aqui ela fica ligada nos testes da logica, que valem nos dois sistemas, e um
teste so do Linux confere que la ela fica desligada."""
import os
import shutil
import stat
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)
import ponte_sem_acento as ponte  # noqa: E402

HATARI = "hatari_libretro.dll"


class TestPonteSemAcento(unittest.TestCase):
    def setUp(self):
        self.base = tempfile.mkdtemp(prefix="arena_ponte_")
        self.com_acento = os.path.join(self.base, "Pedagógicos")
        self.sistema = os.path.join(self.com_acento, "system")
        os.makedirs(self.sistema)
        with open(os.path.join(self.sistema, "tos.img"), "wb") as arquivo:
            arquivo.write(b"TOS" * 1000)
        self.jogo = os.path.join(self.com_acento, "Jogo Ação.st")
        with open(self.jogo, "wb") as arquivo:
            arquivo.write(b"disquete" * 100)
        # A ponte trabalha numa pasta temporaria sem acento: aqui, uma do teste.
        self.temporaria = os.path.join(self.base, "temp")
        os.makedirs(self.temporaria)
        self.antes = tempfile.tempdir
        tempfile.tempdir = self.temporaria
        self.ponte_antes = ponte.PRECISA_DA_PONTE
        ponte.PRECISA_DA_PONTE = True

    def tearDown(self):
        ponte.PRECISA_DA_PONTE = self.ponte_antes
        tempfile.tempdir = self.antes
        shutil.rmtree(self.base, ignore_errors=True)

    @unittest.skipIf(os.name == "nt", "no Windows a ponte existe")
    def test_no_linux_a_ponte_fica_desligada(self):
        ponte.PRECISA_DA_PONTE = self.ponte_antes
        self.assertFalse(ponte.PRECISA_DA_PONTE)
        self.assertFalse(ponte.precisa("hatari_libretro.so", self.sistema, self.jogo))
        self.assertIsNone(ponte.pasta_sistema_relativa("vice_x64_libretro.so", self.sistema, self.com_acento))

    def test_o_java_me_vai_pela_ponte_tambem_fora_do_windows(self):
        # O FreeJ2ME-Plus le o caminho em Latin-1 em qualquer sistema
        # (conferido no conteiner Linux em 20/10/2026).
        ponte.PRECISA_DA_PONTE = False
        jogo = os.path.join(self.com_acento, "Jogo Ação.jar")
        self.assertTrue(ponte.precisa("/arena/retroarch/cores/freej2me_libretro.so", self.sistema, jogo))
        self.assertFalse(ponte.precisa("/arena/retroarch/cores/hatari_libretro.so", self.sistema, self.jogo))
        sem = os.path.join(self.base, "sem", "jogo.jar")
        self.assertFalse(ponte.precisa("freej2me_libretro.so", os.path.join(self.base, "sem"), sem))

    def test_o_nucleo_do_linux_tem_o_nome_do_windows_nas_listas(self):
        self.assertEqual(ponte._nome_do_nucleo("/arena/retroarch/cores/hatari_libretro.so"), "hatari_libretro.dll")
        self.assertEqual(ponte._nome_do_nucleo("C:\\x\\cores\\Hatari_Libretro.DLL"), "hatari_libretro.dll")
        self.assertTrue(ponte.precisa("/arena/retroarch/cores/hatari_libretro.so", self.sistema, self.jogo))

    def test_so_o_nucleo_que_nao_aceita_acento_e_so_com_acento(self):
        self.assertTrue(ponte.precisa(HATARI, self.sistema, self.jogo))
        self.assertTrue(ponte.precisa("C:\\x\\cores\\hatari_libretro.dll", self.sistema, "C:\\jogo.st"))
        self.assertFalse(ponte.precisa(HATARI, "C:\\ARENA\\retroarch\\system", "C:\\ARENA\\jogo.st"))
        self.assertFalse(ponte.precisa("bluemsx_libretro.dll", self.sistema, self.jogo))
        self.assertFalse(ponte.precisa(None, self.sistema, self.jogo))

    def test_leva_a_bios_e_o_jogo_e_devolve_o_disquete_gravado(self):
        caminho, opcoes, devolver = ponte.preparar(HATARI, self.sistema, self.jogo)
        self.assertTrue(caminho.isascii() and opcoes["system_directory"].isascii())
        self.assertTrue(caminho.startswith(self.temporaria))
        self.assertTrue(caminho.endswith(".st"))
        with open(os.path.join(opcoes["system_directory"], "tos.img"), "rb") as arquivo:
            self.assertEqual(arquivo.read(), b"TOS" * 1000)
        with open(caminho, "ab") as arquivo:               # o jogo gravou o recorde
            arquivo.write(b"recorde")
        self.assertTrue(devolver())
        with open(self.jogo, "rb") as arquivo:
            self.assertEqual(arquivo.read(), b"disquete" * 100 + b"recorde")
        self.assertFalse(os.path.exists(os.path.dirname(caminho)))      # a pasta da ponte some

    def test_a_copia_guarda_o_nome_do_jogo(self):
        # O estado (F2) do RetroArch leva o nome do jogo: ate 15/10/2026 todo
        # jogo da ponte virava "jogo.st", e um estado ficava por cima do outro.
        outro = os.path.join(self.com_acento, "Rayoid.st")
        shutil.copyfile(self.jogo, outro)
        primeiro, _o1, devolver1 = ponte.preparar(HATARI, self.sistema, self.jogo)
        segundo, _o2, devolver2 = ponte.preparar(HATARI, self.sistema, outro)
        self.assertEqual(os.path.basename(primeiro), "Jogo Acao.st")
        self.assertEqual(os.path.basename(segundo), "Rayoid.st")    # sem acento no nome: o mesmo nome
        devolver1()
        devolver2()

    def test_nome_sem_acento(self):
        self.assertEqual(ponte.nome_sem_acento("Ação Ñandú.ST"), "Acao Nandu.st")
        self.assertEqual(ponte.nome_sem_acento("Rayoid.st"), "Rayoid.st")
        self.assertEqual(ponte.nome_sem_acento("ドラゴン.st"), "jogo.st")      # nenhuma letra do ASCII
        self.assertEqual(ponte.nome_sem_acento("Café ..dsk"), "Cafe.dsk")
        self.assertEqual(ponte.nome_sem_acento("disco.dsé"), "disco")
        self.assertEqual(ponte.nome_sem_acento("system"), "system")

    def test_nome_com_barra_de_largura_dupla_nao_sai_da_ponte(self):
        # Revisao de seguranca de 16/10/2026: o NFKD troca a barra de largura
        # dupla ("＼" e "／") pela barra de verdade, e o "：" pelos dois-pontos.
        # Sem a troca por "_", "＼..＼..＼x.st" ia para C:\x.st.
        esperados = {
            "\uff3c..\uff3c..\uff3cx.st": "_.._.._x.st",
            "C\uff1a\uff3cUsers\uff3cx.st": "C__Users_x.st",
            "\uff0f..\uff0fx.st": "_.._x.st",
            "a\uff1fb\uff0ac\uff02.st": "a_b_c_.st",
            "\uff23\uff2f\uff2e.st": "jogo.st",                  # CON: a tela, nao um arquivo
            "\uff2c\uff30\uff34\uff11.st": "jogo.st",           # LPT1: a impressora
        }
        for nome, limpo in esperados.items():
            self.assertEqual(ponte.nome_sem_acento(nome), limpo)
            jogo = os.path.join(self.com_acento, nome)
            shutil.copyfile(self.jogo, jogo)
            caminho, _opcoes, devolver = ponte.preparar(HATARI, self.sistema, jogo)
            self.assertTrue(caminho.startswith(self.temporaria), caminho)
            self.assertEqual(os.path.basename(os.path.dirname(caminho)), "jogo")
            self.assertTrue(os.path.isfile(caminho))
            devolver()
        self.assertFalse(os.path.exists(os.path.join(os.path.splitdrive(self.base)[0] + os.sep, "x.st")))

    def test_conferencia_final_barra_o_nome_que_sairia_da_ponte(self):
        original = ponte.nome_sem_acento
        ponte.nome_sem_acento = lambda nome: os.path.join("..", "..", "fora.st")
        try:
            with self.assertRaises(OSError):
                ponte.preparar(HATARI, self.sistema, self.jogo)
        finally:
            ponte.nome_sem_acento = original
        self.assertFalse(os.path.exists(os.path.join(self.temporaria, "fora.st")))
        self.assertEqual([n for n in os.listdir(self.temporaria) if n.startswith(ponte.PREFIXO)], [])

    def test_jogo_chamado_system_nao_bate_na_pasta_das_bios(self):
        jogo = os.path.join(self.com_acento, "system.st")
        shutil.copyfile(self.jogo, jogo)
        semext = os.path.join(self.com_acento, "jogos", "system")
        os.makedirs(os.path.dirname(semext))
        shutil.copyfile(self.jogo, semext)
        for caminho_jogo in (jogo, semext):
            caminho, opcoes, devolver = ponte.preparar(HATARI, self.sistema, caminho_jogo)
            self.assertTrue(os.path.isfile(caminho))
            self.assertTrue(os.path.isfile(os.path.join(opcoes["system_directory"], "tos.img")))
            devolver()

    def test_n64_e_vice_recebem_a_pasta_system_relativa(self):
        # Eles abrem o jogo com acento, mas gravam na system pelo caminho em
        # ANSI (o "ó" virava "Ã³", numa pasta fora do ARENA).
        retroarch = self.com_acento
        for nucleo in ("mupen64plus_next_libretro.dll", "C:\\x\\cores\\vice_x64_libretro.dll",
                       "vice_xplus4_libretro.dll"):
            self.assertEqual(ponte.pasta_sistema_relativa(nucleo, self.sistema, retroarch), "system")
        # Os outros nucleos, a pasta sem acento e a system fora da pasta de trabalho: nada muda.
        self.assertIsNone(ponte.pasta_sistema_relativa(HATARI, self.sistema, retroarch))
        self.assertIsNone(ponte.pasta_sistema_relativa("snes9x_libretro.dll", self.sistema, retroarch))
        self.assertIsNone(ponte.pasta_sistema_relativa(None, self.sistema, retroarch))
        self.assertIsNone(ponte.pasta_sistema_relativa("vice_x64_libretro.dll", "C:\\ARENA\\retroarch\\system",
                                                       "C:\\ARENA\\retroarch"))
        self.assertIsNone(ponte.pasta_sistema_relativa("vice_x64_libretro.dll", self.sistema, self.temporaria))
        self.assertIsNone(ponte.pasta_sistema_relativa("vice_x64_libretro.dll", self.sistema, self.sistema))
        self.assertIsNone(ponte.pasta_sistema_relativa("vice_x64_libretro.dll", "E:\\Pedagógicos\\system",
                                                       "C:\\ARENA\\retroarch"))
        acento_dentro = os.path.join(self.com_acento, "pasta ç", "system")
        self.assertIsNone(ponte.pasta_sistema_relativa("vice_x64_libretro.dll", acento_dentro, retroarch))

    def test_sem_gravar_nada_volta_e_a_pasta_some(self):
        caminho, _opcoes, devolver = ponte.preparar(HATARI, self.sistema, self.jogo)
        self.assertFalse(devolver())
        with open(self.jogo, "rb") as arquivo:
            self.assertEqual(arquivo.read(), b"disquete" * 100)
        self.assertFalse(os.path.exists(os.path.dirname(caminho)))

    def test_cada_jogo_tem_pasta_nova_e_nunca_a_public(self):
        primeiro, _o1, devolver1 = ponte.preparar(HATARI, self.sistema, self.jogo)
        segundo, _o2, devolver2 = ponte.preparar(HATARI, self.sistema, self.jogo)
        self.assertNotEqual(os.path.dirname(primeiro), os.path.dirname(segundo))
        publica = os.environ.get("PUBLIC", "C:\\Users\\Public").lower()
        self.assertFalse(primeiro.lower().startswith(publica))
        devolver1()
        devolver2()

    def test_nucleo_sem_bios_so_leva_o_jogo(self):
        # O AppleWin (Apple II) nao usa a pasta system: a ponte so entra com
        # acento no JOGO e nao troca a pasta system do ARENA.
        applewin = "applewin_libretro.dll"
        self.assertTrue(ponte.precisa(applewin, "C:\\ARENA\\retroarch\\system", self.jogo))
        self.assertFalse(ponte.precisa(applewin, self.sistema, "C:\\ARENA\\jogo.dsk"))
        caminho, opcoes, devolver = ponte.preparar(applewin, self.sistema, self.jogo)
        self.assertTrue(caminho.isascii())
        self.assertEqual(opcoes, {})
        self.assertFalse(devolver())

    def test_atari_8bit_leva_so_as_roms_originais_que_existem(self):
        # O atari800 liga pelo AltirraOS embutido; a ROM original, quando a
        # pessoa poe, tem que chegar a ele mesmo com acento na pasta system.
        atari800 = "atari800_libretro.dll"
        with open(os.path.join(self.sistema, "ATARIXL.ROM"), "wb") as arquivo:
            arquivo.write(b"XL" * 8192)
        self.assertTrue(ponte.precisa(atari800, self.sistema, "C:\\ARENA\\jogo.xex"))
        self.assertFalse(ponte.precisa(atari800, "C:\\ARENA\\retroarch\\system", "C:\\ARENA\\jogo.xex"))
        caminho, opcoes, devolver = ponte.preparar(atari800, self.sistema, self.jogo)
        self.assertEqual(sorted(os.listdir(opcoes["system_directory"])), ["ATARIXL.ROM"])
        self.assertFalse(devolver())

    def test_jogo_sem_acento_abre_direto(self):
        jogo = os.path.join(self.base, "jogo.st")
        shutil.copyfile(self.jogo, jogo)
        caminho, opcoes, devolver = ponte.preparar(HATARI, self.sistema, jogo)
        self.assertEqual(caminho, jogo)
        self.assertTrue(opcoes["system_directory"].isascii())
        self.assertFalse(devolver())
        self.assertFalse(os.path.exists(os.path.dirname(opcoes["system_directory"])))

    def test_sobras_velhas_somem_e_a_de_agora_fica(self):
        velha = os.path.join(self.temporaria, ponte.PREFIXO + "velha")
        nova = os.path.join(self.temporaria, ponte.PREFIXO + "nova")
        for pasta in (velha, nova):
            os.makedirs(os.path.join(pasta, "system"))
        dois_dias = 2 * 24 * 3600
        os.utime(velha, (os.path.getatime(velha) - dois_dias, os.path.getmtime(velha) - dois_dias))
        ponte.limpar_sobras(self.temporaria)
        self.assertFalse(os.path.exists(velha))
        self.assertTrue(os.path.exists(nova))

    def test_a_limpeza_nao_segue_atalho(self):
        # Um atalho com o nome da ponte, plantado na temporaria, apontando
        # para uma pasta do aluno com um arquivo somente leitura.
        do_aluno = os.path.join(self.base, "do_aluno")
        os.makedirs(do_aluno)
        protegido = os.path.join(do_aluno, "recorde.txt")
        with open(protegido, "w", encoding="utf-8") as arquivo:
            arquivo.write("100")
        os.chmod(protegido, stat.S_IREAD)
        atalho = os.path.join(self.temporaria, ponte.PREFIXO + "atalho")
        # E um atalho direto para o arquivo: o chmod da limpeza o seguiria.
        atalho_do_arquivo = os.path.join(self.temporaria, ponte.PREFIXO + "arquivo")
        try:
            os.symlink(do_aluno, atalho, target_is_directory=True)
            os.symlink(protegido, atalho_do_arquivo)
        except OSError:
            os.chmod(protegido, stat.S_IWRITE)
            self.skipTest("este sistema nao deixa criar link")
        try:
            # idade=-1: toda sobra conta como velha.
            ponte.limpar_sobras(self.temporaria, idade=-1)
            ponte._apagar(atalho)
            ponte._apagar(atalho_do_arquivo)
            self.assertTrue(os.path.isfile(protegido))
            self.assertFalse(os.access(protegido, os.W_OK))
        finally:
            os.chmod(protegido, stat.S_IWRITE)
            for caminho in (atalho, atalho_do_arquivo):
                if os.path.lexists(caminho):
                    os.unlink(caminho) if os.path.islink(caminho) else os.rmdir(caminho)

    def test_sem_pasta_sem_acento_avisa(self):
        tempfile.tempdir = self.com_acento
        guardada = os.environ.get("ProgramData")
        os.environ["ProgramData"] = self.com_acento
        try:
            self.assertIsNone(ponte.pasta_da_ponte())
            with self.assertRaises(OSError):
                ponte.preparar(HATARI, self.sistema, self.jogo)
        finally:
            if guardada is None:
                os.environ.pop("ProgramData", None)
            else:
                os.environ["ProgramData"] = guardada


CFG = os.path.join(os.path.dirname(RAIZ), "retroarch", "retroarch.cfg")


@unittest.skipUnless(os.path.isfile(CFG), "sem o RetroArch nesta copia (retroarch.cfg)")
class TestPonteNoArquivoDaPartida(unittest.TestCase):
    """O arquivo da partida (arena.gravar_override) leva a pasta system da
    ponte: antes da correcao de 14/10/2026, ele escrevia a do ARENA por cima
    e o Hatari continuava sem achar a BIOS."""

    def setUp(self):
        from unittest import mock
        import arena
        self.arena = arena
        self.dir = tempfile.mkdtemp(prefix="arena_ponte_override_")
        pastas = {nome: os.path.join(self.dir, nome.lower()) for nome in (
            "PASTA_DADOS", "PASTA_SAVES", "PASTA_STATES", "PASTA_CAPTURAS", "PASTA_SISTEMA",
            "PASTA_CHEATS", "PASTA_REMAPS", "PASTA_CONTROLES", "PASTA_CACHE", "PASTA_PERFIS_CONTROLE")}
        pastas["ARQUIVO_OVERRIDE"] = os.path.join(pastas["PASTA_DADOS"], "arena_override.cfg")
        self.sistema = pastas["PASTA_SISTEMA"]
        self.troca = mock.patch.multiple(arena, **pastas)
        self.troca.start()

    def tearDown(self):
        self.troca.stop()
        shutil.rmtree(self.dir, ignore_errors=True)

    def pasta_system(self, extras):
        caminho = self.arena.gravar_override(self.arena.config_padrao(), extras=extras)
        with open(caminho, encoding="utf-8") as arquivo:
            linha = next(l for l in arquivo if l.startswith("system_directory "))
        return linha.split("=", 1)[1].strip().strip('"')

    def test_a_pasta_da_ponte_chega_ao_retroarch(self):
        self.assertEqual(self.pasta_system({"system_directory": "C:\\Temp\\ARENA-sem-acento\\system"}),
                         "C:\\Temp\\ARENA-sem-acento\\system")

    def test_a_pasta_relativa_do_n64_chega_ao_retroarch(self):
        self.assertEqual(self.pasta_system({"system_directory": "system"}), "system")

    def test_sem_a_ponte_vale_a_pasta_do_arena(self):
        self.assertEqual(os.path.normcase(self.pasta_system({})), os.path.normcase(self.sistema))
        self.assertEqual(os.path.normcase(self.pasta_system(None)), os.path.normcase(self.sistema))


if __name__ == "__main__":
    unittest.main()
