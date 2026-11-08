# -*- coding: utf-8 -*-
"""Achados da auditoria 6 (08/11/2026) que mexem no banco e na configuracao (docs\\RELATORIO-AUDITORIA-6.md).

Banco e configuracao de mentira numa pasta temporaria: os do ARENA de verdade nunca sao tocados.
"""
import os
import sys
import tempfile
import unittest
from unittest import mock

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(AQUI)), "testes"))
import arena  # noqa: E402
import limpeza  # noqa: E402


class OIdDoJogoLevadoParaOCartao(unittest.TestCase):
    """DAD6-04: o id do jogo e' o caminho dele; levado para o cartao, o placar, o tempo de jogo, os favoritos e os
    recentes seguem o jogo, em vez de sumir da lista."""

    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_auditoria6_")
        self.addCleanup(limpeza.apagar_pasta, self.pasta)
        for remendo in (mock.patch.object(arena, "ARQUIVO_BANCO", os.path.join(self.pasta, "arena.db")),
                        mock.patch.dict(arena._ESQUEMA_CONFERIDO, {}, clear=True)):
            remendo.start()
            self.addCleanup(remendo.stop)
        arena.preparar_banco()
        self.config = {"favoritos": ["jogos/pessoais/snes/zelda.sfc", "outro"],
                       "recentes": ["jogos/pessoais/snes/zelda.sfc"]}
        self.salvo = []
        for remendo in (mock.patch.object(arena, "carregar_config", lambda: dict(self.config)),
                        mock.patch.object(arena, "salvar_config", self.salvo.append)):
            remendo.start()
            self.addCleanup(remendo.stop)

    def test_placar_sessao_favoritos_e_recentes_seguem_o_jogo(self):
        with arena.banco() as conexao:
            conexao.execute("INSERT INTO placar (uuid, apelido, jogo_id, jogo_titulo, pontos, registrado_em, "
                            "dispositivo) VALUES ('a', 'ana', 'jogos/pessoais/snes/zelda.sfc', 'Zelda', 10, 'x', 'd')")
        antigo = os.path.join(arena.RAIZ, "jogos", "pessoais", "SNES", "Zelda.sfc")
        novo = os.path.join(arena.RAIZ, "jogos", "cartao-1234", "SNES", "Zelda.sfc")
        self.assertEqual(arena.trocar_id_dos_jogos([(antigo, novo)]), 1)
        with arena.banco() as conexao:
            ids = [linha[0] for linha in conexao.execute("SELECT jogo_id FROM placar")]
        self.assertEqual(ids, ["jogos/cartao-1234/snes/zelda.sfc"])
        self.assertEqual(self.salvo[-1]["favoritos"], ["jogos/cartao-1234/snes/zelda.sfc", "outro"])
        self.assertEqual(self.salvo[-1]["recentes"], ["jogos/cartao-1234/snes/zelda.sfc"])

    def test_nada_levado_nada_muda(self):
        self.assertEqual(arena.trocar_id_dos_jogos([]), 0)
        self.assertEqual(self.salvo, [])


if __name__ == "__main__":
    unittest.main()
