# -*- coding: utf-8 -*-
"""A descoberta de colegas so escuta a rede com ela liberada ou enquanto a
janela do Jogar Junto procura partida (arena.quer_escutar). Achado de
15/10/2026: escutando desde a abertura, o Firewall do Windows perguntava pelo
Python mesmo com a rede fechada. A porta de verdade abrindo e fechando:
testes\\teste_descoberta_rede_fechada.py."""
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)
import arena  # noqa: E402


class TestEscutaDaDescoberta(unittest.TestCase):
    def setUp(self):
        self.procura = dict(arena.PROCURA_DE_PARTIDA)
        self.vizinhos = dict(arena.VIZINHOS)
        self.falantes = dict(arena._FALANTES)
        arena.PROCURA_DE_PARTIDA["ate"] = 0.0

    def tearDown(self):
        arena.PROCURA_DE_PARTIDA.update(self.procura)
        arena.VIZINHOS.clear()
        arena.VIZINHOS.update(self.vizinhos)
        arena._FALANTES.clear()
        arena._FALANTES.update(self.falantes)
        arena.ESCUTA_MUDOU.clear()

    def test_rede_fechada_sem_procura_nao_escuta(self):
        self.assertFalse(arena.quer_escutar({"permitir_rede": False}))
        self.assertFalse(arena.quer_escutar({}))

    def test_rede_liberada_escuta(self):
        self.assertTrue(arena.quer_escutar({"permitir_rede": True}))

    def test_a_procura_abre_a_escuta_por_dois_minutos(self):
        arena.procurando_partida()
        self.assertTrue(arena.ESCUTA_MUDOU.is_set())        # acorda a descoberta na hora
        agora = arena.time.monotonic()
        fechada = {"permitir_rede": False}
        self.assertTrue(arena.quer_escutar(fechada, agora))
        self.assertTrue(arena.quer_escutar(fechada, agora + arena.TEMPO_DA_PROCURA - 1))
        self.assertFalse(arena.quer_escutar(fechada, agora + arena.TEMPO_DA_PROCURA + 1))

    def test_fechar_a_escuta_solta_tudo_e_esquece_os_colegas(self):
        class SocketDeMentira:
            fechado = False

            def close(self):
                self.fechado = True

        ouvinte, falante = SocketDeMentira(), SocketDeMentira()
        arena._FALANTES["192.168.0.10"] = falante
        with arena.TRAVA_VIZINHOS:
            arena.VIZINHOS["colega"] = {"id": "colega", "apelido": "Colega", "ip": "192.168.0.20",
                                        "porta": 8777, "visto_em": 0.0, "partida": None}
        arena.fechar_a_escuta(ouvinte)
        self.assertTrue(ouvinte.fechado)
        self.assertTrue(falante.fechado)
        self.assertEqual(arena._FALANTES, {})
        self.assertEqual(arena.VIZINHOS, {})


if __name__ == "__main__":
    unittest.main()
