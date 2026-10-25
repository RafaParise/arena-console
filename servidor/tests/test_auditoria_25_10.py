# -*- coding: utf-8 -*-
"""Os consertos da auditoria 5 (25/10/2026): REDE-01 (a rota de testar o colega nao varre portas a pedido de fora), REDE-02
(o codigo de aparelho nao troca a cada pedido de fora), DAD-01 (cartao de PS2 que falha nao deixa .tmp), COR-01 (o laco
das origens nao quebra se a lista muda) e os pequenos. Os pedidos sao feitos direto na rota, com um 'self' de mentira."""
import os
import socket
import sys
import tempfile
import unittest
from unittest import mock

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ = os.path.dirname(PASTA_SERVIDOR)
if PASTA_SERVIDOR not in sys.path:
    sys.path.insert(0, PASTA_SERVIDOR)
sys.path.insert(0, os.path.join(RAIZ, "testes"))

import arena  # noqa: E402
import graficos  # noqa: E402
import indexador  # noqa: E402
import limpeza  # noqa: E402


class FalsoManipulador:
    """So o que as duas rotas usam do manipulador de pedidos."""

    def __init__(self, local, origem="10.1.2.3"):
        self._local = local
        self.client_address = (origem, 50000)
        self.respostas = []

    def pedido_e_local(self):
        return self._local

    def responder_json(self, corpo, *_):
        self.respostas.append(("json", corpo))

    def erro(self, mensagem, codigo=400):
        self.respostas.append(("erro", mensagem, codigo))


def rota(manipulador, caminho, dados):
    return arena.Manipulador.api_post(manipulador, caminho, dados)


class TestarOColega(unittest.TestCase):
    def conexoes(self, local, endereco):
        alvos = []

        def recusar(alvo, timeout=None):
            alvos.append(alvo)
            raise OSError("recusada")

        falso = FalsoManipulador(local)
        with mock.patch.object(arena.socket, "gethostbyname", side_effect=lambda nome: nome), \
                mock.patch.object(arena.socket, "create_connection", side_effect=recusar):
            rota(falso, "/api/partida/testar", {"endereco": endereco})
        return alvos

    def test_pedido_de_fora_so_testa_quem_pediu_na_porta_de_sempre(self):
        alvos = self.conexoes(False, "10.9.9.9:22")
        self.assertTrue(alvos)
        self.assertEqual({a[0] for a in alvos}, {"10.1.2.3"})                       # nunca o 10.9.9.9
        self.assertEqual({a[1] for a in alvos} - {arena.PORTA, graficos.PORTA_PARTIDA}, set())

    def test_pedido_da_tela_deste_computador_testa_o_endereco_digitado(self):
        alvos = self.conexoes(True, "192.168.0.22:9999")
        self.assertEqual(alvos[0], ("192.168.0.22", 9999))


class TrocaDeCodigo(unittest.TestCase):
    def pedir_a_troca(self, origem):
        falso = FalsoManipulador(False, origem)
        config = {"dispositivo_id": "abc123abc123", "codigo_proprio": False}
        salvos = []
        with mock.patch.object(arena, "carregar_config", return_value=dict(config)), \
                mock.patch.object(arena, "salvar_config", side_effect=salvos.append), \
                mock.patch.object(arena, "enderecos_locais", return_value=[]):
            rota(falso, "/api/sinc/receber", {"placares": [], "sessoes": [], "dispositivo": "abc123abc123"})
            return falso, salvos

    def test_so_troca_uma_vez_por_hora(self):
        with mock.patch.dict(arena._TROCA_DE_CODIGO, {"em": 0.0}):
            primeiro, salvos = self.pedir_a_troca("10.1.2.3")
            self.assertEqual(len(salvos), 1)                                        # o caso real: dois PCs da mesma imagem
            self.assertNotEqual(salvos[0]["dispositivo_id"], "abc123abc123")
            self.assertEqual(primeiro.respostas[0][0], "erro")
            self.assertGreater(arena._TROCA_DE_CODIGO["em"], 0)
            segundo, salvos2 = self.pedir_a_troca("10.1.2.4")                       # o colega repete: nao troca de novo
            self.assertEqual(salvos2, [])
            self.assertIn("daqui a uma hora", segundo.respostas[0][1])


class CartaoDePs2(unittest.TestCase):
    def test_falha_no_meio_nao_deixa_o_temporario(self):
        pasta = tempfile.mkdtemp(prefix="arena_cartao_")
        self.addCleanup(limpeza.apagar_pasta, pasta)
        real_open = open

        def abrir_e_falhar(caminho, modo="r", *a, **k):
            arquivo = real_open(caminho, modo, *a, **k)
            if str(caminho).endswith(".tmp"):
                escrever = arquivo.write

                def escrever_e_falhar(dados):
                    escrever(dados[:10])
                    raise OSError(28, "disco cheio")
                arquivo.write = escrever_e_falhar
            return arquivo

        with mock.patch("builtins.open", abrir_e_falhar):
            graficos.preparar_cartoes_do_ps2(pasta, {"slot1_tipo": "ps2", "slot1_mb": 8, "slot2_tipo": "ps1", "slot2_mb": 8})
        self.assertEqual([n for n in os.listdir(pasta) if n.endswith(".tmp")], [])


class Pequenos(unittest.TestCase):
    def test_nome_com_quebra_de_linha_no_fim_nao_passa(self):
        self.assertIsNone(graficos._NOME_DE_NUCLEO.match("flycast\n"))
        self.assertIsNotNone(graficos._NOME_DE_NUCLEO.match("flycast"))
        self.assertIsNone(graficos._CHAVE_DE_OPCAO.match("reicast_x\n"))

    def test_o_laco_das_origens_aguenta_a_lista_mudar(self):
        copia = dict(indexador.ORIGENS)
        try:
            indexador.ORIGENS["cartao-teste"] = "x"
            for origem in list(indexador.ORIGENS):
                indexador.ORIGENS.pop("cartao-teste", None)            # muda durante o laco: com a copia nao quebra
        finally:
            indexador.ORIGENS.clear()
            indexador.ORIGENS.update(copia)


if __name__ == "__main__":
    unittest.main()
