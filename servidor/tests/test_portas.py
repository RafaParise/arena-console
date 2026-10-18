# -*- coding: utf-8 -*-
"""As faixas de porta que o Windows reserva a cada reinicio (servidor\\portas.py,
achado de 16/10/2026): a porta do ARENA que cai numa delas nao abre, e o
VERIFICAR.bat, o PARTIDA.bat e a janela preta avisam."""
import os
import sys
import unittest
from unittest import mock

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PASTA_SERVIDOR not in sys.path:
    sys.path.insert(0, PASTA_SERVIDOR)

import portas  # noqa: E402

EM_PORTUGUES = """
Protocolo udp Intervalos de Exclusão de Porta

Porta Inicial    Porta Final
----------    --------
     49210       49309
     50000       50059     *
     55335       55434

* - Exclusões de porta administradas.
"""
EM_INGLES = """
Protocol tcp Port Exclusion Ranges

Start Port    End Port
----------    --------
      5357        5357
     55400       55499

* - Administered port exclusions.
"""


class Faixas(unittest.TestCase):
    def test_le_o_netsh_nos_dois_idiomas(self):
        self.assertEqual(portas.ler_faixas(EM_PORTUGUES), [(49210, 49309), (50000, 50059), (55335, 55434)])
        self.assertEqual(portas.ler_faixas(EM_INGLES), [(5357, 5357), (55400, 55499)])

    def test_o_achado_de_16_10_nao_bloqueia_por_uma(self):
        """De 55335 a 55434 (UDP): a 55435 ficou de fora por uma."""
        self.assertEqual(portas.portas_bloqueadas({"udp": portas.ler_faixas(EM_PORTUGUES), "tcp": []}), [])

    def test_porta_dentro_da_faixa(self):
        achadas = portas.portas_bloqueadas({"tcp": portas.ler_faixas(EM_INGLES),
                                            "udp": [(55436, 55500)]})
        self.assertEqual([(a["porta"], a["protocolo"]) for a in achadas], [(55435, "tcp"), (55436, "udp")])
        frase = portas.frase(achadas[0])
        self.assertIn("55435", frase)
        self.assertIn("de 55400 a 55499", frase)
        self.assertIn("partida a dois", frase)
        self.assertIn("Reinicie", portas.O_QUE_FAZER)

    def test_fora_do_windows_nao_pergunta(self):
        with mock.patch.object(portas.os, "name", "posix"):
            self.assertEqual(portas.faixas_reservadas("tcp"), [])

    def test_o_servidor_avisa_na_janela_preta(self):
        import arena
        avisos = []
        with mock.patch.object(portas, "portas_bloqueadas",
                               return_value=[{"porta": 55435, "protocolo": "tcp", "para": "a partida a dois",
                                              "faixa": (55400, 55499)}]), \
                mock.patch("builtins.print", side_effect=lambda texto, *a, **k: avisos.append(texto)):
            arena.avisar_portas_reservadas()
        self.assertEqual(len(avisos), 1)
        self.assertIn("55435", avisos[0])


if __name__ == "__main__":
    unittest.main()
