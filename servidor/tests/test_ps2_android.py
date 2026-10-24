# -*- coding: utf-8 -*-
"""O PS2 no Android pelo nucleo do RetroArch do app (pedido do Rafael, 24/10/2026: "qualquer emulador
deve rodar dentro do ARENA e nao um aplicativo a parte").

Confere o que da para conferir sem celular: a BIOS do PS2 reconhecida pelo conteudo e levada para a pasta
que o nucleo le (retroarch\\system\\pcsx2\\bios), e o remendo do nucleo (jogadores 2 a 8 e abrir sem jogo)
que o GitHub aplica antes de compilar."""
import os
import re
import sys
import tempfile
import unittest

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ = os.path.dirname(PASTA_SERVIDOR)
if PASTA_SERVIDOR not in sys.path:
    sys.path.insert(0, PASTA_SERVIDOR)
sys.path.insert(0, os.path.join(RAIZ, "testes"))

import bios  # noqa: E402
import graficos  # noqa: E402
import limpeza  # noqa: E402

TAMANHO_PS2 = 4194304


def bios_de_ps2_de_mentira(regiao="A"):
    """4 MiB com a marca que o catalogo reconhece (ROMVER 0160AC20040614): so serve de teste."""
    dados = bytearray(TAMANHO_PS2)
    marca = b"ROMVER  0160" + regiao.encode() + b"C20040614"
    dados[0x100:0x100 + len(marca)] = marca
    return bytes(dados)


class BiosDoPs2(unittest.TestCase):

    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_ps2_android_")
        self.sistema = os.path.join(self.pasta, "system")
        os.makedirs(self.sistema)

    def tearDown(self):
        limpeza.apagar_pasta(self.pasta)

    def escrever(self, nome, dados):
        caminho = os.path.join(self.sistema, nome)
        with open(caminho, "wb") as arquivo:
            arquivo.write(dados)
        return caminho

    def test_reconhece_pelo_conteudo_e_nao_pelo_nome(self):
        ps2 = self.escrever("PS2 Bios 30004R V6 Pal.BIN", bios_de_ps2_de_mentira("E"))
        self.escrever("qualquer.bin", b"\0" * TAMANHO_PS2)            # 4 MiB que nao e' BIOS
        self.escrever("scph1001.bin", b"\0" * 524288)                  # tamanho de PS1, mas sem a marca
        self.assertEqual(bios.bios_de_playstation("ps2", self.sistema), [ps2])
        self.assertEqual(bios.bios_de_playstation("ps1", self.sistema), [])

    def test_so_ha_bios_original_do_ps2_com_o_arquivo_na_pasta(self):
        self.assertFalse(bios.tem_bios_original("ps2", self.sistema))
        self.escrever("renomeada.bin", bios_de_ps2_de_mentira())
        self.assertTrue(bios.tem_bios_original("ps2", self.sistema))
        self.assertFalse(bios.tem_bios_original("ps2", os.path.join(self.pasta, "nao_existe")))

    def test_leva_as_bios_para_a_pasta_do_nucleo_sem_trocar_nada(self):
        self.escrever("SCPH-70004_BIOS.BIN", bios_de_ps2_de_mentira("E"))
        self.escrever("scph39001.bin", bios_de_ps2_de_mentira("A"))
        levadas = graficos.preparar_bios_do_nucleo_ps2(self.sistema)
        self.assertEqual(sorted(levadas), ["SCPH-70004_BIOS.bin", "scph39001.bin"])       # extensao em minusculas
        destino = os.path.join(self.sistema, "pcsx2", "bios")
        self.assertEqual(sorted(os.listdir(destino)), ["SCPH-70004_BIOS.bin", "scph39001.bin"])
        self.assertEqual(graficos.preparar_bios_do_nucleo_ps2(self.sistema), [])          # a segunda vez nao copia
        # o que o nucleo gravou do lado (a marca do MagicGate, o NVM) e a BIOS que o professor pos la ficam
        with open(os.path.join(destino, "scph39001.bin"), "wb") as arquivo:
            arquivo.write(b"a do professor")
        with open(os.path.join(destino, "scph39001.nvm"), "wb") as arquivo:
            arquivo.write(b"idioma e hora")
        graficos.preparar_bios_do_nucleo_ps2(self.sistema)
        with open(os.path.join(destino, "scph39001.bin"), "rb") as arquivo:
            self.assertEqual(arquivo.read(), b"a do professor")
        self.assertTrue(os.path.isfile(os.path.join(destino, "scph39001.nvm")))

    def test_sem_bios_nao_cria_pasta_nenhuma(self):
        self.assertEqual(graficos.preparar_bios_do_nucleo_ps2(self.sistema), [])
        self.assertFalse(os.path.exists(os.path.join(self.sistema, "pcsx2")))
        self.assertEqual(graficos.preparar_bios_do_nucleo_ps2(os.path.join(self.pasta, "nao_existe")), [])


class RemendoDoNucleo(unittest.TestCase):
    """O remendo e' texto escrito a mao: confere o formato (um erro de conta de linhas so apareceria no
    GitHub, depois de baixar o ARMSX2 inteiro)."""

    CAMINHO = os.path.join(RAIZ, "ferramentas", "remendos", "armsx2-libretro-jogadores.patch")

    def setUp(self):
        with open(self.CAMINHO, "rb") as arquivo:
            self.bruto = arquivo.read()
        self.texto = self.bruto.decode("utf-8")

    def test_so_tem_fim_de_linha_do_unix_e_mexe_so_no_nucleo_libretro(self):
        self.assertNotIn(b"\r", self.bruto)
        arquivos = re.findall(r"^(?:---|\+\+\+) (\S+)", self.texto, re.M)
        self.assertEqual(arquivos, ["a/pcsx2-libretro/Main.cpp", "b/pcsx2-libretro/Main.cpp"])

    def test_a_conta_de_linhas_de_cada_trecho_fecha(self):
        trechos = re.split(r"^(?=@@ )", self.texto, flags=re.M)[1:]
        self.assertGreaterEqual(len(trechos), 4)
        for trecho in trechos:
            cabeca, *linhas = trecho.split("\n")
            if linhas and linhas[-1] == "":
                linhas.pop()
            achado = re.match(r"@@ -\d+(?:,(\d+))? \+\d+(?:,(\d+))? @@", cabeca)
            self.assertTrue(achado, cabeca)
            velho = int(achado.group(1) or 1)
            novo = int(achado.group(2) or 1)
            self.assertEqual(sum(1 for l in linhas if l[:1] in (" ", "-")), velho, cabeca)
            self.assertEqual(sum(1 for l in linhas if l[:1] in (" ", "+")), novo, cabeca)

    def test_faz_o_que_o_pedido_diz(self):
        self.assertIn('"Pad2", "Type", "DualShock2"', self.texto)                  # o jogador 2 ligado no PS2
        self.assertIn("MultitapPort0_Enabled", self.texto)                          # o multitap da porta 1
        self.assertIn("input_state_cb(jogador, RETRO_DEVICE_JOYPAD", self.texto)    # uma porta do libretro por jogador
        self.assertNotIn("+				pad->Set(m.ds2, input_state_cb(0,", self.texto)
        self.assertIn("+	bool support_no_game = true;", self.texto)                 # abrir sem jogo: o menu da BIOS

    def test_o_fluxo_do_github_confere_e_aplica_o_remendo_antes_de_compilar(self):
        with open(os.path.join(RAIZ, ".github", "workflows", "nucleo-ps2-android.yml"), encoding="utf-8") as arquivo:
            fluxo = arquivo.read()
        self.assertIn("git apply --check", fluxo)
        self.assertIn("ferramentas/remendos", fluxo)
        self.assertLess(fluxo.index("Aplicar os remendos"), fluxo.index("Compilar as dependencias"))
        self.assertIn("-march=armv8-a -moutline-atomics", fluxo)                    # roda no Cortex-A53
        self.assertIn("ARMSX2_COMMIT: 90126bdfea7a3ffb1fd288b2f7f0ae0b033af2d6", fluxo)


if __name__ == "__main__":
    unittest.main()
