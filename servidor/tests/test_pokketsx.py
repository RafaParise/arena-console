# -*- coding: utf-8 -*-
"""O PokketSX (servidor\\pokketsx.py): o PlayStation 1 com o PocketStation de verdade, como UM JEITO A MAIS de abrir o
PS1 (consoles.json -> ps1 -> externo_extra). O PS1 continua sendo do RetroArch: nada de "externo" no cadastro dele, que
tiraria o agrupamento de varios discos e o Jogar Junto. A abertura de verdade pela rota esta em
testes\\teste_pokketsx_pelo_arena.py."""
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ = os.path.dirname(PASTA_SERVIDOR)
if PASTA_SERVIDOR not in sys.path:
    sys.path.insert(0, PASTA_SERVIDOR)
sys.path.insert(0, os.path.join(RAIZ, "testes"))

import graficos  # noqa: E402
import jeitos_de_abrir  # noqa: E402
import limpeza  # noqa: E402
import pokketsx  # noqa: E402


def cadastro_do_ps1():
    with open(os.path.join(PASTA_SERVIDOR, "consoles.json"), encoding="utf-8") as arquivo:
        return next(p for p in json.load(arquivo)["plataformas"] if p["id"] == "ps1")


class Cadastro(unittest.TestCase):
    def test_o_ps1_segue_sendo_do_retroarch(self):
        """Com "externo" no cadastro, o PS1 perderia as listas .m3u (indexador), a pasta no celular (android_inicio) e o
        botao de Jogar Junto: o emulador a mais tem a sua propria chave."""
        ps1 = cadastro_do_ps1()
        self.assertNotIn("externo", ps1)
        extra = ps1["externo_extra"]
        self.assertEqual(extra["nome"], "PokketSX")
        self.assertTrue(extra["so_windows"])
        self.assertIn("{jogo}", extra["argumentos"])

    def test_a_linha_de_comando_abre_e_fecha_sozinha(self):
        """-batch: o programa inteiro fecha quando o jogo fecha (senao o ARENA esperaria pela janela dele);
        -fullscreen: tela cheia; '--': o caminho do jogo e' um argumento so, mesmo com espaco e acento."""
        extra = cadastro_do_ps1()["externo_extra"]
        comando = graficos.comando_externo(r"C:\x\pokketsx.exe", extra, r"C:\Jogos\Crash (USA).chd")
        self.assertEqual(comando, [r"C:\x\pokketsx.exe", "-portable", "-batch", "-fullscreen", "--",
                                   r"C:\Jogos\Crash (USA).chd"])

    def test_o_motivo_da_escolha_diz_o_que_ele_nao_faz(self):
        """Ele nao mostra a telinha nem toca o som: o aluno tem que saber antes de escolher (premissa corrigida)."""
        extra = cadastro_do_ps1()["externo_extra"]
        self.assertIn("não mostra a telinha", extra["motivo_escolha"])


class Jeitos(unittest.TestCase):
    PS1 = {"id": "ps1", "externo_extra": {"titulo_escolha": "PokketSX (com PocketStation)",
                                          "motivo_escolha": "Liga o PocketStation.", "selo_escolha": "com PocketStation"}}

    def setUp(self):
        self.base = tempfile.mkdtemp(prefix="arena_pokketsx_jeitos_")
        self.tem_a_bios, self.tem_bios_original = jeitos_de_abrir.bios.tem_a_bios, jeitos_de_abrir.bios.tem_bios_original
        jeitos_de_abrir.bios.tem_a_bios = lambda plataforma, pasta: True
        jeitos_de_abrir.bios.tem_bios_original = lambda plataforma, pasta: True
        self.nucleo = os.path.join(self.base, "swanstation_libretro.dll")
        open(self.nucleo, "wb").close()
        self.ps1 = dict(self.PS1, core="swanstation_libretro.dll", arquivos_sistema=1)

    def tearDown(self):
        jeitos_de_abrir.bios.tem_a_bios, jeitos_de_abrir.bios.tem_bios_original = self.tem_a_bios, self.tem_bios_original
        limpeza.apagar_pasta(self.base)

    def jeitos(self, extra=None):
        return jeitos_de_abrir.jeitos(self.ps1, self.base, self.base, None, extra)

    def test_sem_o_programa_nada_muda(self):
        self.assertEqual([j["id"] for j in self.jeitos()], ["original"])

    def test_o_pokketsx_entra_por_ultimo_com_o_id_externo(self):
        lista = self.jeitos("PokketSX")
        self.assertEqual([j["id"] for j in lista], ["original", "externo"])
        self.assertEqual(lista[-1]["titulo"], "PokketSX (com PocketStation)")
        self.assertEqual(lista[-1]["selo"], "com PocketStation")
        self.assertEqual(lista[-1]["explica"], "Liga o PocketStation.")

    def test_com_dois_jeitos_a_tela_pergunta(self):
        lista = self.jeitos("PokketSX")
        self.assertIsNone(jeitos_de_abrir.escolher(lista))
        self.assertEqual(jeitos_de_abrir.escolher(lista, "externo"), "externo")
        self.assertEqual(jeitos_de_abrir.escolher(lista, None, "externo"), "externo")
        self.assertEqual(jeitos_de_abrir.escolher(self.jeitos(), None, "externo"), "original")   # saiu da pasta: nao vale

    def test_o_externo_de_sempre_nao_leva_o_extra_junto(self):
        lista = jeitos_de_abrir.jeitos(self.ps1, self.base, self.base, "Dolphin", "PokketSX")
        self.assertEqual([j["id"] for j in lista].count("externo"), 1)

    def test_jogar_junto_nao_usa_a_escolha_lembrada_do_emulador_a_mais(self):
        vale = jeitos_de_abrir.lembrado_que_vale
        self.assertIsNone(vale("externo", True, True))
        self.assertEqual(vale("externo", False, True), "externo")      # sozinho: vale
        self.assertEqual(vale("livre", True, True), "livre")           # outro jeito: vale
        self.assertEqual(vale("externo", True, False), "externo")      # o externo de sempre (Dolphin) segue como era


class AcharOPrograma(unittest.TestCase):
    def setUp(self):
        self.base = tempfile.mkdtemp(prefix="arena_pokketsx_achar_")
        self.pasta = os.path.join(self.base, "PokketSX")
        self.exe = os.path.join(self.pasta, "pokketsx-qt-x64-Release-MSVC.exe")
        self.ps1 = cadastro_do_ps1()
        for alvo, valor in ((graficos, {"PASTA_EMULADORES": self.base, "NO_WINDOWS": True}),
                            (graficos.plataforma_do_sistema, {"ANDROID": False})):
            for nome, novo in valor.items():
                patcher = mock.patch.object(alvo, nome, novo)
                patcher.start()
                self.addCleanup(patcher.stop)

    def tearDown(self):
        limpeza.apagar_pasta(self.base)

    def instalar(self):
        os.makedirs(self.pasta)
        open(self.exe, "wb").close()

    def test_acha_pelo_extra_e_nunca_pelo_externo_de_sempre(self):
        self.assertEqual(graficos.achar_externo_extra(self.ps1)[0], None)
        self.instalar()
        self.assertEqual(graficos.achar_externo_extra(self.ps1)[0], self.exe)
        self.assertEqual(graficos.achar_externo(self.ps1), (None, None))       # o PS1 nao tem emulador de fora "de sempre"

    def test_console_sem_extra_nao_acha_nada(self):
        self.assertEqual(graficos.achar_externo_extra({"id": "nes"}), (None, None))

    def test_ajustes_lista_como_opcional(self):
        self.instalar()
        with mock.patch.object(graficos, "falta_para_o_externo", return_value=""):
            linha = next(i for i in graficos.situacao_dos_externos([self.ps1]) if i["nome"] == "PokketSX")
        self.assertTrue(linha["extra"])
        self.assertTrue(linha["instalado"])
        self.assertEqual(linha["pasta"], os.path.join("emuladores", "PokketSX"))

    def test_so_windows_nao_aparece_em_outro_sistema(self):
        with mock.patch.object(graficos, "NO_WINDOWS", False):
            self.assertEqual(graficos.situacao_dos_externos([self.ps1]), [])


class Pasta(unittest.TestCase):
    """Uma pasta do PokketSX de mentira, com a BIOS do ARENA (retroarch\\system) ao lado."""

    def setUp(self):
        self.base = tempfile.mkdtemp(prefix="arena_pokketsx_pasta_")
        self.pasta = os.path.join(self.base, "emuladores", "PokketSX")
        self.exe = os.path.join(self.pasta, "pokketsx-qt-x64-Release-MSVC.exe")
        self.sistema = os.path.join(self.base, "retroarch", "system")
        os.makedirs(self.pasta)
        os.makedirs(self.sistema)
        open(self.exe, "wb").close()
        self.ps1 = os.path.join(self.sistema, "SCPH1001.BIN")
        self.poc = os.path.join(self.sistema, "pocketstation.bin")
        patcher = mock.patch.object(pokketsx.bios_do_arena, "bios_de_playstation",
                                    side_effect=lambda console, pasta: [self.ps1] if os.path.isfile(self.ps1) else [])
        patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        limpeza.apagar_pasta(self.base)

    def dar_as_bios(self, ps1=True, pocketstation=True):
        if ps1:
            with open(self.ps1, "wb") as arquivo:
                arquivo.write(bytes(pokketsx.TAMANHO_DA_BIOS_PS1))
        if pocketstation:
            with open(self.poc, "wb") as arquivo:
                arquivo.write(bytes(pokketsx.TAMANHO_DA_BIOS_POCKETSTATION))

    def ini(self):
        with open(os.path.join(self.pasta, "settings.ini"), encoding="utf-8") as arquivo:
            return arquivo.read()


class BiosECartao(Pasta):
    def test_sem_as_bios_diz_qual_falta_primeiro(self):
        self.assertIn("BIOS do PlayStation", pokketsx.falta(self.exe, self.sistema))
        self.dar_as_bios(ps1=True, pocketstation=False)
        self.assertIn("BIOS do aparelho", pokketsx.falta(self.exe, self.sistema))
        self.dar_as_bios()
        self.assertEqual(pokketsx.falta(self.exe, self.sistema), "")

    def test_a_bios_que_ja_esta_na_pasta_dele_conta(self):
        os.makedirs(os.path.join(self.pasta, "bios"))
        for nome, tamanho in (("meu_ps1.bin", pokketsx.TAMANHO_DA_BIOS_PS1), ("meu_pocket.bin", pokketsx.TAMANHO_DA_BIOS_POCKETSTATION)):
            with open(os.path.join(self.pasta, "bios", nome), "wb") as arquivo:
                arquivo.write(bytes(tamanho))
        self.assertEqual(pokketsx.falta(self.exe, self.sistema), "")

    def test_leva_so_o_que_falta(self):
        self.dar_as_bios()
        self.assertEqual(sorted(pokketsx.levar_as_bios(self.exe, self.sistema)), ["SCPH1001.BIN", "pocketstation.bin"])
        self.assertEqual(pokketsx.levar_as_bios(self.exe, self.sistema), [])          # ja estao la

    def test_nao_mexe_na_bios_que_a_pessoa_pos(self):
        os.makedirs(os.path.join(self.pasta, "bios"))
        dela = os.path.join(self.pasta, "bios", "dela.bin")
        with open(dela, "wb") as arquivo:
            arquivo.write(bytes(pokketsx.TAMANHO_DA_BIOS_PS1))
        self.dar_as_bios()
        self.assertEqual(pokketsx.levar_as_bios(self.exe, self.sistema), ["pocketstation.bin"])
        self.assertFalse(os.path.exists(os.path.join(self.pasta, "bios", "SCPH1001.BIN")))

    def test_o_cartao_nasce_formatado_e_nunca_e_trocado(self):
        criado = pokketsx.garantir_o_cartao(self.exe)
        self.assertEqual(criado, os.path.join(self.pasta, "memcards", "PocketStation.mcd"))
        with open(criado, "rb") as arquivo:
            conteudo = arquivo.read()
        self.assertEqual(len(conteudo), 131072)
        self.assertEqual(conteudo[:2], b"MC")
        with open(criado, "wb") as arquivo:
            arquivo.write(b"MC" + b"saves da pessoa" * 8)
        self.assertEqual(pokketsx.garantir_o_cartao(self.exe), "")
        with open(criado, "rb") as arquivo:
            self.assertTrue(arquivo.read().startswith(b"MCsaves da pessoa"))


class Config(Pasta):
    def test_do_zero_nasce_pronto_para_abrir_sem_perguntar(self):
        texto = pokketsx.montar_config("", True)
        for linha in ("SetupWizardIncomplete = false", "SettingsVersion = 3", "ConfirmPowerOff = false",
                      "EnableDiscordPresence = false", "CheckAtStartup = false", "Card1PocketStation = false",
                      "Card2Type = Shared", "Card2Path = PocketStation.mcd", "Card2PocketStation = true",
                      "PocketStationBiosPath = pocketstation.bin", "PowerOff = Keyboard/F10",
                      "OpenPauseMenu = Keyboard/Escape", "Up = Keyboard/Up", "Up = SDL-0/DPadUp",
                      "Cross = SDL-0/A", "L2 = SDL-0/+LeftTrigger", "LLeft = SDL-0/-LeftX"):
            self.assertIn(linha, texto.splitlines(), linha)

    def test_sem_a_bios_do_pocketstation_o_cartao_fica_comum(self):
        texto = pokketsx.montar_config("", False)
        self.assertIn("Card2PocketStation = false", texto.splitlines())
        self.assertNotIn("PocketStationBiosPath", texto)

    def test_repetir_nao_muda_nada(self):
        uma_vez = pokketsx.montar_config("", True)
        self.assertEqual(pokketsx.montar_config(uma_vez, True), uma_vez)

    def test_o_que_a_pessoa_mexeu_fica(self):
        antes = ("[Main]\nSettingsVersion = 3\nSetupWizardIncomplete = true\nEmulationSpeed = 2\n\n[GPU]\nResolutionScale = 3\n"
                 "Renderer = Vulkan\n\n[Pad1]\nType = AnalogController\nCross = Keyboard/Z\n\n[Hotkeys]\nPowerOff = Keyboard/F9\n")
        depois = pokketsx.montar_config(antes, True).splitlines()
        for linha in ("EmulationSpeed = 2", "ResolutionScale = 3", "Renderer = Vulkan", "Cross = Keyboard/Z",
                      "PowerOff = Keyboard/F9"):
            self.assertIn(linha, depois)
        self.assertIn("SetupWizardIncomplete = false", depois)          # esta o ARENA governa
        self.assertNotIn("PowerOff = Keyboard/F10", depois)             # o atalho da pessoa vale
        self.assertIn("Cross = SDL-0/A", depois)                        # e o controle entra ao lado do teclado

    def test_atalhos_que_ja_existem_ganham_so_o_que_falta(self):
        antes = "[Hotkeys]\nFastForward = Keyboard/F5\n"
        depois = pokketsx.montar_config(antes, True).splitlines()
        self.assertIn("FastForward = Keyboard/F5", depois)
        self.assertIn("PowerOff = Keyboard/F10", depois)
        self.assertNotIn("OpenPauseMenu = Keyboard/Escape", depois)     # quem tem a secao ja decidiu os outros

    def test_cada_ligacao_do_controle_entra_uma_vez_so(self):
        texto = pokketsx.montar_config(pokketsx.montar_config("", True), True)
        self.assertEqual(texto.splitlines().count("Up = SDL-0/DPadUp"), 1)
        self.assertEqual(texto.splitlines().count("Up = Keyboard/Up"), 1)

    def test_escrever_so_grava_quando_muda(self):
        self.dar_as_bios()
        pokketsx.levar_as_bios(self.exe, self.sistema)
        self.assertTrue(pokketsx.escrever_config(self.exe))
        primeiro = self.ini()
        self.assertFalse(pokketsx.escrever_config(self.exe))
        self.assertEqual(self.ini(), primeiro)
        self.assertIn("Card2PocketStation = true", primeiro)

    def test_preparar_deixa_tudo_no_lugar_e_repetir_nao_mexe(self):
        self.dar_as_bios()
        feito = pokketsx.preparar(self.exe, self.sistema)
        self.assertEqual(feito["erro"], "")
        self.assertEqual(sorted(feito["bios"]), ["SCPH1001.BIN", "pocketstation.bin"])
        self.assertTrue(feito["cartao"])
        self.assertTrue(feito["config"])
        self.assertTrue(os.path.isfile(os.path.join(self.pasta, "portable.txt")))
        de_novo = pokketsx.preparar(self.exe, self.sistema)
        self.assertEqual((de_novo["bios"], de_novo["cartao"], de_novo["config"]), ([], "", False))

    def test_erro_de_disco_volta_como_texto_e_nao_derruba(self):
        with mock.patch.object(pokketsx, "levar_as_bios", side_effect=PermissionError("somente leitura")):
            feito = pokketsx.preparar(self.exe, self.sistema)
        self.assertIn("somente leitura", feito["erro"])


if __name__ == "__main__":
    unittest.main()
