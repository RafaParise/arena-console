# -*- coding: utf-8 -*-
"""Entrar numa partida sem escolher o numero: "o proximo lugar livre" (graficos.opcoes_de_partida, proximo_livre).
Medido em 26/10/2026 com o celular hospedando e o RetroArch do computador entrando: sem pedido de dispositivo, o anfitriao
poe o convidado no jogador 2 sozinho (testes\teste_jogar_junto_pc_celular.py --auto)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import graficos  # noqa: E402


def pedidos(**opcoes):
    o = graficos.opcoes_de_partida("Teste", **opcoes)
    return [n for n in range(1, graficos.JOGADORES_MAXIMO_NETPLAY + 1) if o["netplay_request_device_p%d" % n] == "true"]


class OProximoLivre(unittest.TestCase):
    def test_quem_entra_sem_escolher_nao_pede_lugar(self):
        self.assertEqual(pedidos(hospedar=False, jogador=2, proximo_livre=True), [])

    def test_quem_escolhe_continua_pedindo_o_seu(self):
        self.assertEqual(pedidos(hospedar=False, jogador=3), [3])

    def test_o_anfitriao_e_sempre_o_jogador_1(self):
        self.assertEqual(pedidos(hospedar=True, jogador=5, proximo_livre=True), [1])

    def test_espectador_nao_pede_nada(self):
        self.assertEqual(pedidos(hospedar=False, assistir=True, proximo_livre=False), [])


if __name__ == "__main__":
    unittest.main()
