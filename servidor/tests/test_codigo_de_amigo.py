# -*- coding: utf-8 -*-
"""O codigo de amigo curto (ideia de um aluno, 16/10/2026): ARENA-XXXX-XXXX no
lugar das 12 letras do codigo do aparelho. A rota /api/amigo/codigo aceita o
curto (do jeito que a pessoa digitar) e o inteiro, de antes.

A rota grava na lista de amigos: o teste troca o config.json por um da pasta
temporaria e confere, no fim, que o de verdade nao mudou."""
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)
import arena  # noqa: E402

LUCAS = "3f9a1c0b7d2e"          # o codigo curto dele: ARENA-7YD1-R2VX


class TestCodigoCurto(unittest.TestCase):
    def test_o_codigo_curto(self):
        self.assertEqual(arena.codigo_de_amigo(LUCAS), "ARENA-7YD1-R2VX")
        self.assertEqual(arena.codigo_de_amigo("000000000000"), "ARENA-0000-0000")
        self.assertEqual(arena.codigo_de_amigo("ffffffffffff"), "ARENA-ZZZZ-ZZZZ")
        self.assertEqual(arena.codigo_de_amigo(LUCAS.upper()), "ARENA-7YD1-R2VX")

    def test_sem_as_letras_que_se_confundem(self):
        for numero in range(0, 1 << 20, 997):
            curto = arena.codigo_de_amigo("%010x00" % (numero * 1048573))
            self.assertFalse(set(curto[6:]) & set("ILOU"), curto)

    def test_codigo_fora_do_padrao_fica_como_esta(self):
        for antigo in ("", "abc", "xyz123456789", "codigo-antigo"):
            self.assertEqual(arena.codigo_de_amigo(antigo), antigo)

    def test_do_jeito_que_a_pessoa_digitar(self):
        for digitado in ("ARENA-7YD1-R2VX", "arena-7yd1-r2vx", "ARENA7YD1R2VX", "7YD1-R2VX",
                         " 7yd1 r2vx ", "ARENA-7YDI-R2VX", "ARENA-7YDL-R2VX", LUCAS, LUCAS.upper()):
            self.assertTrue(arena.mesmo_codigo(digitado, LUCAS), digitado)
        for errado in ("", "ARENA-7YD1-R2V", "ARENA-7YD1-R2VY", "7YD1", "ARENA", None):
            self.assertFalse(arena.mesmo_codigo(errado, LUCAS), errado)
        self.assertFalse(arena.mesmo_codigo("ARENA-7YD1-R2VX", ""))

    def test_a_lista_de_amigos_ganha_o_codigo_so_para_a_tela(self):
        amigos = [{"apelido": "Lucas", "url": "http://192.168.0.22:8777", "id": LUCAS},
                  {"apelido": "Servidor", "url": "http://10.0.0.5:8777", "id": ""}]
        tela = arena.amigos_para_a_tela(amigos)
        self.assertEqual(tela[0]["codigo_amigo"], "ARENA-7YD1-R2VX")
        self.assertNotIn("codigo_amigo", tela[1])            # adicionado pelo endereco, sem codigo
        self.assertNotIn("codigo_amigo", amigos[0])          # a lista guardada nao muda


class TestRotaDoCodigo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.servidor = arena.Servidor(("127.0.0.1", 0), arena.Manipulador)
        cls.porta = cls.servidor.server_address[1]
        threading.Thread(target=cls.servidor.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.servidor.shutdown()
        cls.servidor.server_close()

    def setUp(self):
        self.real = arena.ARQUIVO_CONFIG
        self.marca_real = os.path.getmtime(self.real) if os.path.isfile(self.real) else None
        self.pasta = tempfile.mkdtemp(prefix="arena_codigo_amigo_")
        with arena.TRAVA_CACHE:
            self.cache = dict(arena._config_cache)
            arena._config_cache["valor"] = None
        arena.ARQUIVO_CONFIG = os.path.join(self.pasta, "config.json")
        self.vizinhos = dict(arena.VIZINHOS)
        arena.VIZINHOS.clear()
        self.ver("Lucas", LUCAS, "192.168.0.22")

    def tearDown(self):
        arena.ARQUIVO_CONFIG = self.real
        with arena.TRAVA_CACHE:
            arena._config_cache.clear()
            arena._config_cache.update(self.cache)
            arena._config_cache["valor"] = None
        arena.VIZINHOS.clear()
        arena.VIZINHOS.update(self.vizinhos)
        shutil.rmtree(self.pasta, ignore_errors=True)
        # O config.json de verdade nao foi tocado.
        self.assertEqual(os.path.getmtime(self.real) if os.path.isfile(self.real) else None, self.marca_real)

    def ver(self, apelido, identificacao, ip):
        """Um colega gritando na rede (como se a descoberta o tivesse ouvido)."""
        with arena.TRAVA_VIZINHOS:
            arena.VIZINHOS[identificacao] = {"id": identificacao, "apelido": apelido, "ip": ip,
                                             "porta": 8777, "visto_em": time.monotonic(), "partida": None}

    def pedir(self, codigo):
        pedido = urllib.request.Request("http://127.0.0.1:%d/api/amigo/codigo" % self.porta,
                                        data=json.dumps({"codigo": codigo}).encode("utf-8"), method="POST",
                                        headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(pedido, timeout=10) as resposta:
                return resposta.status, json.loads(resposta.read())
        except urllib.error.HTTPError as erro:
            return erro.code, json.loads(erro.read() or b"{}")

    def test_adiciona_pelo_codigo_curto(self):
        status, resposta = self.pedir("7yd1 r2vx")
        self.assertEqual(status, 200, resposta)
        lucas = next(a for a in resposta["servidores"] if a["apelido"] == "Lucas")
        self.assertEqual(lucas["id"], LUCAS)                         # guardado o codigo inteiro
        self.assertEqual(lucas["codigo_amigo"], "ARENA-7YD1-R2VX")   # e a tela mostra o curto
        with open(arena.ARQUIVO_CONFIG, encoding="utf-8") as arquivo:
            guardado = json.load(arquivo)["servidores"]
        self.assertEqual([a.get("id") for a in guardado], [LUCAS])
        self.assertNotIn("codigo_amigo", guardado[0])

    def test_o_codigo_inteiro_de_antes_ainda_vale(self):
        status, resposta = self.pedir(LUCAS)
        self.assertEqual(status, 200, resposta)

    def test_codigo_que_ninguem_tem(self):
        status, resposta = self.pedir("ARENA-0000-0000")
        self.assertEqual(status, 404)
        self.assertIn("Não achei ninguém", resposta.get("erro", ""))

    def test_dois_colegas_com_o_mesmo_codigo_curto_nao_escolhe_no_chute(self):
        # So os 10 primeiros caracteres contam no codigo curto.
        self.ver("Outro", LUCAS[:10] + "ff", "192.168.0.23")
        status, resposta = self.pedir("ARENA-7YD1-R2VX")
        self.assertEqual(status, 409)
        self.assertIn("Mais de um colega", resposta.get("erro", ""))
        status, _ = self.pedir(LUCAS)                    # o inteiro desempata
        self.assertEqual(status, 200)


if __name__ == "__main__":
    unittest.main()
