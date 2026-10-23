# -*- coding: utf-8 -*-
"""Desempenho que aprende (servidor/desempenho.py, auditoria 4, 22/10/2026).

O pedido do Rafael: o ARENA "deve saber identificar queda de desempenho [...]
para entender as melhores configuracoes no automatico, e deve ter a opcao
personalizada". O emulador no limite (a thread do jogo ou a placa perto de
100%) faz o console descer um degrau na proxima partida, so no Automatico;
tres partidas folgadas devolvem um degrau.
"""
import os
import subprocess
import sys
import tempfile
import time
import unittest

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PASTA_SERVIDOR not in sys.path:
    sys.path.insert(0, PASTA_SERVIDOR)

import desempenho  # noqa: E402

PASTA_TESTES = os.path.join(os.path.dirname(PASTA_SERVIDOR), "testes")
if PASTA_TESTES not in sys.path:
    sys.path.insert(0, PASTA_TESTES)
import limpeza  # noqa: E402


def medida(processador, placa=()):
    return {"amostras": len(processador), "processador": list(processador), "placa": list(placa)}


FOLGADO = medida([60.0] * 20, [40.0] * 20)
NO_LIMITE_PROCESSADOR = medida([99.0] * 10 + [70.0] * 10)
NO_LIMITE_PLACA = medida([50.0] * 20, [98.0] * 8 + [80.0] * 12)


class Medida(unittest.TestCase):
    def test_thread_mais_ocupada(self):
        self.assertEqual(desempenho.thread_mais_ocupada({1: 10.0, 2: 3.0}, {1: 11.5, 2: 3.2}, 2.0), 75.0)
        self.assertEqual(desempenho.thread_mais_ocupada({}, {1: 5.0}, 2.0), 0.0, "thread nova nao conta")
        self.assertEqual(desempenho.thread_mais_ocupada({1: 0.0}, {1: 9.0}, 2.0), 100.0, "teto de um nucleo")

    def test_no_limite(self):
        self.assertIsNone(desempenho.ficou_no_limite(medida([99.0] * 5)), "jogo curto: nao da para saber")
        self.assertFalse(desempenho.ficou_no_limite(FOLGADO))
        self.assertTrue(desempenho.ficou_no_limite(NO_LIMITE_PROCESSADOR))
        self.assertTrue(desempenho.ficou_no_limite(NO_LIMITE_PLACA))
        self.assertIsNone(desempenho.ficou_no_limite(None))

    def test_mede_um_emulador_ocupado_de_verdade(self):
        # Outro processo, como o RetroArch: um laco que nao para (num thread
        # deste mesmo Python, o laco disputaria a trava do interpretador com
        # o medidor, o que nao acontece com o emulador de verdade).
        ocupado = subprocess.Popen([sys.executable, "-c", "while True: pass"])
        try:
            medidor = desempenho.Medidor(ocupado.pid, intervalo=0.3, descartar_antes=0.1, com_placa=False).comecar()
            time.sleep(1.6)
            resultado = medidor.parar()
        finally:
            ocupado.kill()
            ocupado.wait(5)
        self.assertGreaterEqual(resultado["amostras"], 3)
        self.assertGreater(max(resultado["processador"]), 50.0, resultado)


class Degraus(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_teste_desempenho_")
        self.arquivo = os.path.join(self.pasta, "desempenho.json")

    def tearDown(self):
        limpeza.apagar_pasta(self.pasta)

    def test_desce_ate_tres_e_sobe_com_tres_folgadas(self):
        for esperado in (1, 2, 3, 3):
            self.assertEqual(desempenho.registrar("ps1", NO_LIMITE_PROCESSADOR, self.arquivo)[1], esperado)
        self.assertEqual(desempenho.registrar("ps1", FOLGADO, self.arquivo), (3, 3))
        self.assertEqual(desempenho.registrar("ps1", FOLGADO, self.arquivo), (3, 3))
        self.assertEqual(desempenho.registrar("ps1", FOLGADO, self.arquivo), (3, 2))
        self.assertEqual(desempenho.degrau("ps1", self.arquivo), 2)
        self.assertEqual(desempenho.degrau("snes", self.arquivo), 0)

    def test_jogo_curto_nao_muda_nada(self):
        self.assertEqual(desempenho.registrar("n64", medida([99.0] * 3), self.arquivo), (0, 0))
        self.assertFalse(os.path.exists(self.arquivo), "nada a guardar")

    def test_zerar(self):
        desempenho.registrar("ps1", NO_LIMITE_PROCESSADOR, self.arquivo)
        desempenho.registrar("n64", NO_LIMITE_PLACA, self.arquivo)
        desempenho.zerar("ps1", self.arquivo)
        self.assertEqual(sorted(desempenho.ler(self.arquivo)), ["n64"])
        desempenho.zerar(arquivo=self.arquivo)
        self.assertEqual(desempenho.ler(self.arquivo), {})

    def test_so_o_automatico_muda(self):
        for _ in range(3):
            desempenho.registrar("ps1", NO_LIMITE_PROCESSADOR, self.arquivo)
        base = {"perfil_grafico": "automatico", "preset_grafico_externo": "automatico"}
        mudada = desempenho.config_da_partida(base, "ps1", self.arquivo)
        self.assertEqual((mudada["perfil_grafico"], mudada["preset_grafico_externo"], mudada.get("modo_modesto"),
                          mudada.get("abaixo_do_original")), ("desempenho", "leve", True, "leve"))
        self.assertEqual(base["perfil_grafico"], "automatico", "a configuracao de quem usa nao muda")
        for manual in ({"perfil_grafico": "qualidade"}, {"perfil_grafico": "automatico", "abaixo_do_original": "minimo"},
                       {"perfil_grafico": "automatico", "ajuste_pelo_desempenho": False}):
            with self.subTest(manual=manual):
                self.assertIs(desempenho.config_da_partida(manual, "ps1", self.arquivo), manual)
        self.assertIs(desempenho.config_da_partida(base, "snes", self.arquivo), base, "console sem degrau")

    def test_degrau_um_so_muda_o_perfil(self):
        desempenho.registrar("n64", NO_LIMITE_PLACA, self.arquivo)
        mudada = desempenho.config_da_partida({"perfil_grafico": "automatico"}, "n64", self.arquivo)
        self.assertEqual(mudada["perfil_grafico"], "desempenho")
        self.assertNotIn("modo_modesto", mudada)
        self.assertNotIn("abaixo_do_original", mudada)


if __name__ == "__main__":
    unittest.main()
