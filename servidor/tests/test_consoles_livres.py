# -*- coding: utf-8 -*-
"""Os consoles novos de 14/10/2026 (pedido do Rafael: "todos os consoles de
codigo aberto"), conferidos pelos dados -- sem abrir emulador (isso fica em
testes\\teste_consoles_livres.py, com o nucleo de verdade):
  - cada jogo livre dos testes aponta para um console que aceita o final
    dele (ou o do arquivo que o teste monta, o disquete do Atari ST);
  - o final repetido (.d64, .prg, .tap, .tzx...) continua sendo do C64 e do
    ZX Spectrum fora das pastas: quem decide e' a pasta;
  - o Jogar Junto dito no consoles.json e' o que o teste viu;
  - os cinco consoles sem jogo livre publicado (15/10/2026), que o teste
    abre com um programa escrito por ele mesmo, aceitam o final desse
    programa."""
import json
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)
import indexador  # noqa: E402

PASTA_JOGOS_LIVRES = os.path.join(os.path.dirname(RAIZ), "testes", "jogos_livres")
MONTADOS = {"atarist": ".st"}       # o teste monta o disquete com o programa dentro
# Os programas que testes\teste_consoles_livres.py escreve (GERADOS).
GERADOS = {"atari800": ".xex", "pet": ".prg", "c128": ".prg", "supervision": ".sv", "thomson": ".m5"}


class TestConsolesLivres(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(os.path.join(RAIZ, "consoles.json"), encoding="utf-8") as arquivo:
            cls.plataformas = {p["id"]: p for p in json.load(arquivo)["plataformas"]}

    def test_cada_jogo_livre_tem_o_console_certo(self):
        with open(os.path.join(PASTA_JOGOS_LIVRES, "lista.json"), encoding="utf-8") as arquivo:
            jogos = json.load(arquivo)["arquivos"]
        self.assertGreaterEqual(len(jogos), 6)
        for jogo in jogos:
            plataforma = self.plataformas.get(jogo["console"])
            self.assertIsNotNone(plataforma, jogo["origem"])
            extensao = MONTADOS.get(jogo["console"]) or os.path.splitext(jogo["origem"])[1].lower()
            self.assertIn(extensao, [e.lower() for e in plataforma["extensoes"]], jogo["origem"])
            for campo in ("autor", "licenca", "fonte", "baixado_de", "sha256"):
                self.assertTrue(jogo.get(campo), (jogo["origem"], campo))

    def test_cada_programa_gerado_tem_o_console_certo(self):
        for console, extensao in GERADOS.items():
            plataforma = self.plataformas.get(console)
            self.assertIsNotNone(plataforma, console)
            self.assertIn(extensao, plataforma["extensoes"], console)
            self.assertEqual(plataforma.get("arquivos_sistema"), 0, console)   # liga sem BIOS de empresa

    def test_final_repetido_fica_com_o_c64_e_o_spectrum_fora_das_pastas(self):
        _por_id, por_extensao = indexador.carregar_plataformas()
        for extensao in (".prg", ".d64", ".t64", ".crt"):
            self.assertEqual(por_extensao[extensao][0], "c64", extensao)
            self.assertIn("vic20", por_extensao[extensao])
            self.assertIn("c128", por_extensao[extensao])
        for extensao in (".prg", ".d64", ".t64", ".tap"):
            self.assertIn("pet", por_extensao[extensao], extensao)
        self.assertEqual(por_extensao[".tap"][0], "spectrum")
        self.assertEqual(por_extensao[".tzx"][0], "spectrum")
        self.assertIn("zx81", por_extensao[".tzx"])
        # O .xex continua do Xbox 360 e o .cas do MSX; o Atari 8-bit, so pela pasta.
        self.assertEqual(por_extensao[".xex"], ["xbox360", "atari800"])
        self.assertEqual(por_extensao[".cas"], ["msx", "atari800"])

    def test_jogar_junto_como_o_teste_viu(self):
        # 14 e 15/10/2026, hospedando de verdade: o RetroArch recusa nestes...
        for console in ("msx", "atarist", "zx81", "vic20", "plus4", "apple2", "pet", "c128", "thomson"):
            self.assertIs(self.plataformas[console].get("netplay"), False, console)
            self.assertIn("Netplay", self.plataformas[console]["netplay_motivo"])
        # ...e o CHIP-8 (JAXE), o Arduboy (Ardens), o MicroW8, o Atari 8-bit
        # (atari800) e o Supervision (potator) conectaram.
        for console in ("chip8", "arduboy", "microw8", "atari800", "supervision"):
            self.assertTrue(self.plataformas[console].get("netplay", True), console)


if __name__ == "__main__":
    unittest.main()
