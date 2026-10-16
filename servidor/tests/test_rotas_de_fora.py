# -*- coding: utf-8 -*-
"""As rotas que outro computador da rede pode chamar (arena.ROTAS_REDE_EXTERNA).
O pedido de fora de verdade, recusado com 403: testes\\teste_acesso_de_rede.py."""
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)
import arena  # noqa: E402


class TestRotasDeFora(unittest.TestCase):
    def test_a_lista_de_amigos_so_muda_deste_computador(self):
        # Revisao de 16/10/2026: com o /api/amigo/codigo aberto a rede, outro
        # computador se punha como amigo do aluno e passava a receber os
        # recordes dele na sincronizacao.
        for rota in ("/api/amigo/codigo", "/api/amigo/testar", "/api/amigo/adicionar",
                     "/api/amigo/remover"):
            self.assertNotIn(rota, arena.ROTAS_REDE_EXTERNA)

    def test_so_o_que_a_partida_e_a_sincronizacao_precisam(self):
        self.assertEqual(arena.ROTAS_REDE_EXTERNA, frozenset((
            "/api/colegas", "/api/ranking", "/api/jogo/impressao", "/api/partida/testar",
            "/api/partida/cheguei", "/api/sinc/ola", "/api/sinc/receber")))


if __name__ == "__main__":
    unittest.main()
