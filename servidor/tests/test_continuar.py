# -*- coding: utf-8 -*-
"""Continuar de onde parou (servidor\\continuar.py): o ponto automatico nunca passa por cima de um save mais novo."""
import os
import sys
import tempfile
import time
import unittest

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PASTA_SERVIDOR)
sys.path.insert(0, os.path.join(os.path.dirname(PASTA_SERVIDOR), "testes"))
import continuar  # noqa: E402
import limpeza  # noqa: E402

JOGO = os.path.join("jogos", "nes", "Contra (USA).nes")


class TesteContinuar(unittest.TestCase):
    def setUp(self):
        self.base = tempfile.mkdtemp(prefix="arena-continuar-")
        self.states = os.path.join(self.base, "states")
        self.saves = os.path.join(self.base, "saves")
        self.sistema = os.path.join(self.base, "system")
        for pasta in (self.states, self.saves, self.sistema):
            os.makedirs(pasta)

    def tearDown(self):
        limpeza.apagar_pasta(self.base)

    def arquivo(self, *partes, idade=0):
        """Cria um arquivo com a hora de 'idade' segundos atras."""
        caminho = os.path.join(self.base, *partes)
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, "wb") as saida:
            saida.write(b"x")
        hora = time.time() - idade
        os.utime(caminho, (hora, hora))
        return caminho

    def decidir(self, plataforma="nes", ligado=True, em_rede=False, jogo=JOGO):
        return continuar.decidir(ligado, em_rede, plataforma, jogo, self.states, self.saves, self.sistema)

    def test_desligado_manda_as_duas_chaves_desligadas(self):
        decisao = self.decidir(ligado=False)
        self.assertEqual(decisao["opcoes"], {"savestate_auto_save": "false", "savestate_auto_load": "false"})
        self.assertFalse(decisao["volta"])

    def test_jogar_junto_nunca_usa_o_ponto(self):
        self.arquivo("states", "FCEUmm", "Contra (USA).state.auto", idade=10)
        decisao = self.decidir(em_rede=True)
        self.assertEqual(decisao["opcoes"]["savestate_auto_load"], "false")
        self.assertEqual(decisao["opcoes"]["savestate_auto_save"], "false")

    def test_primeira_vez_so_grava(self):
        decisao = self.decidir()
        self.assertEqual(decisao["opcoes"], {"savestate_auto_save": "true", "savestate_auto_load": "false"})
        self.assertFalse(decisao["volta"])

    def test_volta_quando_o_save_e_da_mesma_saida(self):
        # Ao fechar: o RetroArch grava o ponto e, um instante depois, a bateria do cartucho.
        self.arquivo("states", "FCEUmm", "Contra (USA).state.auto", idade=100)
        self.arquivo("saves", "FCEUmm", "Contra (USA).srm", idade=99)
        decisao = self.decidir()
        self.assertTrue(decisao["volta"])
        self.assertEqual(decisao["opcoes"]["savestate_auto_load"], "true")

    def test_save_mais_novo_ganha_do_ponto(self):
        # O app foi fechado a forca depois de salvar no jogo: o .srm ficou mais novo que o ponto.
        self.arquivo("states", "FCEUmm", "Contra (USA).state.auto", idade=3600)
        self.arquivo("saves", "FCEUmm", "Contra (USA).srm", idade=60)
        decisao = self.decidir()
        self.assertFalse(decisao["volta"])
        self.assertEqual(decisao["opcoes"]["savestate_auto_load"], "false")
        self.assertEqual(decisao["opcoes"]["savestate_auto_save"], "true")
        self.assertIn("Contra (USA).srm", decisao["motivo"])

    def test_cartao_do_ps2_gravado_por_outro_jogo(self):
        # O cartao do PS2 e' um so: outro jogo gravou nele depois do ponto deste.
        jogo = os.path.join("jogos", "ps2", "Crash of the Titans.iso")
        self.arquivo("states", "LRPS2", "Crash of the Titans.state.auto", idade=7200)
        self.arquivo("system", "pcsx2", "memcards", "Mcd001-64MB.ps2", idade=300)
        decisao = self.decidir(plataforma="ps2", jogo=jogo)
        self.assertFalse(decisao["volta"])
        self.assertIn("Mcd001-64MB.ps2", decisao["motivo"])

    def test_vmu_do_dreamcast_compartilhado(self):
        jogo = os.path.join("jogos", "dc", "Sonic Adventure.chd")
        self.arquivo("states", "Flycast", "Sonic Adventure.state.auto", idade=7200)
        self.arquivo("system", "dc", "vmu_save_A1.bin", idade=10)
        self.assertFalse(self.decidir(plataforma="dreamcast", jogo=jogo)["volta"])

    def test_cartao_de_outro_console_nao_atrapalha(self):
        # O cartao do PS2 mais novo nao impede o ponto de um jogo de NES.
        self.arquivo("states", "FCEUmm", "Contra (USA).state.auto", idade=7200)
        self.arquivo("system", "pcsx2", "memcards", "Mcd001-64MB.ps2", idade=10)
        self.assertTrue(self.decidir()["volta"])

    def test_estados_do_f2_nao_contam_como_save(self):
        self.arquivo("states", "FCEUmm", "Contra (USA).state.auto", idade=7200)
        self.arquivo("saves", "FCEUmm", "Contra (USA).state1", idade=10)
        self.arquivo("saves", "FCEUmm", "Contra (USA).state.png", idade=10)
        self.assertTrue(self.decidir()["volta"])

    def test_outro_jogo_com_nome_parecido_nao_conta(self):
        self.arquivo("states", "FCEUmm", "Contra (USA).state.auto", idade=7200)
        self.arquivo("saves", "FCEUmm", "Contra (USA) (Rev 1).srm", idade=10)
        self.assertTrue(self.decidir()["volta"])

    def test_cartao_do_ps1_por_jogo(self):
        # SwanStation: cartao por jogo com o nome do jogo e _1.
        jogo = os.path.join("jogos", "ps1", "Crash Bandicoot.chd")
        self.arquivo("states", "SwanStation", "Crash Bandicoot.state.auto", idade=7200)
        self.arquivo("saves", "SwanStation", "Crash Bandicoot_1.mcd", idade=10)
        self.assertFalse(self.decidir(plataforma="ps1", jogo=jogo)["volta"])

    def test_nao_apaga_nem_muda_nada(self):
        ponto = self.arquivo("states", "FCEUmm", "Contra (USA).state.auto", idade=3600)
        save = self.arquivo("saves", "FCEUmm", "Contra (USA).srm", idade=60)
        antes = {c: os.path.getmtime(c) for c in (ponto, save)}
        self.decidir()
        self.assertEqual(antes, {c: os.path.getmtime(c) for c in (ponto, save)})

    def test_ponto_mais_novo_entre_dois_nucleos(self):
        self.arquivo("states", "FCEUmm", "Contra (USA).state.auto", idade=7200)
        novo = self.arquivo("states", "Mesen", "Contra (USA).state.auto", idade=100)
        self.assertEqual(continuar.ponto_automatico(self.states, JOGO), novo)


if __name__ == "__main__":
    unittest.main()
