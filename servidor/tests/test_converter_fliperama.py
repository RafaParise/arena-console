# -*- coding: utf-8 -*-
"""A ferramenta que converte o fliperama "decriptado para emulador antigo"
(ferramentas\\converter_fliperama_decriptado.py; o KOF 2002 do Rafael,
02/10/2026). Partes de mentira, com as marcas calculadas na hora, num ARENA
de mentira em pasta temporaria."""

import os
import shutil
import sys
import tempfile
import unittest
import zipfile
import zlib

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FERRAMENTAS = os.path.join(os.path.dirname(RAIZ), "ferramentas")
if FERRAMENTAS not in sys.path:
    sys.path.insert(0, FERRAMENTAS)

import converter_fliperama_decriptado as conv  # noqa: E402


def marca(dados):
    return zlib.crc32(dados) & 0xffffffff


A, B, C, SOM = b"A" * 64, b"B" * 32, b"C" * 32, b"S" * 16


class TestConverter(unittest.TestCase):

    def setUp(self):
        self.raiz = os.path.join(tempfile.mkdtemp(prefix="arena_converter_"), "ARENA")
        self.conversao = {
            "jogo": "Jogo de teste", "conjunto": "jogofd", "pasta": "Neo Geo",
            "partes": [("p-a.p1", (marca(A),), marca(A)),
                       ("p-v.v1", (marca(B), marca(C)), marca(B + C))],
            "correcao": [("p-m1.m1", marca(SOM))],
        }
        arcade = os.path.join(self.raiz, "jogos", "pessoais", "Arcade")
        os.makedirs(arcade)
        os.makedirs(os.path.join(self.raiz, "jogos", "pessoais", "Neo Geo"))
        self.original = os.path.join(arcade, "jogo.zip")
        self.escrever_original({"x_a.rom": A, "x_v1.rom": B, "x_v2.rom": C, "x_m1.rom": SOM, "readme.html": b"oi"})
        self.destino = os.path.join(self.raiz, "jogos", "pessoais", "Neo Geo", "jogofd.zip")
        self.correcao = os.path.join(self.raiz, "retroarch", "system", "fbneo", "patched", "jogofd.zip")
        self.guardado = os.path.join(self.raiz, "backup", "originais", "jogo.zip")

    def tearDown(self):
        shutil.rmtree(os.path.dirname(self.raiz), ignore_errors=True)

    def escrever_original(self, partes):
        with zipfile.ZipFile(self.original, "w", zipfile.ZIP_DEFLATED) as z:
            for nome, dados in partes.items():
                z.writestr(nome, dados)

    def rodar(self, fazer):
        mensagens = []
        achados = conv.achar_originais(self.raiz, self.conversao)
        resultados = [conv.converter(self.raiz, self.conversao, o, fazer, dizer=mensagens.append)
                      for o in achados]
        return achados, resultados, mensagens

    def test_sem_fazer_so_mostra(self):
        achados, resultados, mensagens = self.rodar(False)
        self.assertEqual((achados, resultados), ([self.original], [True]))
        self.assertTrue(any("faria" in m for m in mensagens))
        self.assertTrue(os.path.isfile(self.original))
        self.assertFalse(os.path.exists(self.destino) or os.path.exists(self.correcao))

    def test_converte_pela_marca_e_guarda_o_original(self):
        achados, resultados, _ = self.rodar(True)
        self.assertEqual(resultados, [True])
        with zipfile.ZipFile(self.destino) as z:
            self.assertEqual(sorted(z.namelist()), ["p-a.p1", "p-v.v1"])
            self.assertEqual(z.read("p-v.v1"), B + C)          # as duas partes, juntas na ordem
        with zipfile.ZipFile(self.correcao) as z:
            self.assertEqual(z.namelist(), ["p-m1.m1"])
            self.assertEqual(z.read("p-m1.m1"), SOM)
        self.assertFalse(os.path.exists(self.original))
        with zipfile.ZipFile(self.guardado) as z:                # nada apagado
            self.assertIn("readme.html", z.namelist())
        self.assertTrue(os.path.isfile(os.path.join(self.raiz, "backup", "originais", "LEIA.txt")))
        self.assertTrue(os.path.isfile(os.path.join(os.path.dirname(self.correcao), "LEIA.txt")))

    def test_rodar_de_novo_nao_estraga(self):
        self.rodar(True)
        achados, _, _ = self.rodar(True)
        self.assertEqual(achados, [])                            # o original ja saiu
        # Outro original igual que aparecer depois: o convertido fica, o
        # original vai para o lado do primeiro, com outro nome.
        self.escrever_original({"x_a.rom": A, "x_v1.rom": B, "x_v2.rom": C, "x_m1.rom": SOM})
        _, resultados, mensagens = self.rodar(True)
        self.assertEqual(resultados, [True])
        self.assertTrue(any("ja convertido" in m for m in mensagens))
        self.assertTrue(os.path.isfile(os.path.join(self.raiz, "backup", "originais", "jogo (2).zip")))

    def test_marca_que_nao_bate_para_tudo(self):
        self.conversao["partes"][1] = ("p-v.v1", (marca(C), marca(B)), marca(B + C))   # ordem errada
        _, resultados, mensagens = self.rodar(True)
        self.assertEqual(resultados, [False])
        self.assertTrue(any("PARADO" in m for m in mensagens))
        self.assertTrue(os.path.isfile(self.original))
        self.assertFalse(os.path.exists(self.destino) or os.path.exists(self.correcao))

    def test_parte_faltando_nao_e_o_jogo(self):
        self.escrever_original({"x_a.rom": A, "x_v1.rom": B, "x_m1.rom": SOM})
        self.assertEqual(conv.achar_originais(self.raiz, self.conversao), [])

    def test_zip_estragado_para_com_frase(self):
        # A parte "x_v1.rom" guardada sem compressao e com um byte trocado:
        # a marca do diretorio do zip continua a de antes.
        with zipfile.ZipFile(self.original, "w", zipfile.ZIP_STORED) as z:
            for nome, conteudo in (("x_a.rom", A), ("x_v1.rom", B), ("x_v2.rom", C), ("x_m1.rom", SOM)):
                z.writestr(nome, conteudo)
        with open(self.original, "rb") as f:
            dados = bytearray(f.read())
        dados[dados.index(B)] ^= 0xff
        with open(self.original, "wb") as f:
            f.write(bytes(dados))
        _, resultados, mensagens = self.rodar(True)
        self.assertEqual(resultados, [False])
        self.assertTrue(any("PARADO" in m for m in mensagens), mensagens)
        self.assertTrue(os.path.isfile(self.original))
        self.assertFalse(os.path.exists(self.destino))


class TestTabelaDoKof(unittest.TestCase):
    """A conversao de verdade (KOF 2002 -> kof2k2fd): as marcas que o FBNeo
    pede, conferidas no fbneo_libretro.dll e no registro dele."""

    def test_kof2002(self):
        kof = next(c for c in conv.CONVERSOES if c["conjunto"] == "kof2k2fd")
        self.assertEqual(kof["pasta"], "Neo Geo")
        nomes = [nome for nome, _p, _f in kof["partes"]]
        self.assertEqual(len(nomes), 13)
        self.assertEqual(len(set(nomes)), 13)
        finais = dict((nome, final) for nome, _p, final in kof["partes"])
        self.assertEqual(finais["265-v1d.v1"], 0x0fc9a58d)
        self.assertEqual(finais["265-v2d.v2"], 0xb8c475a4)
        self.assertEqual(kof["correcao"], [("265-m1d.m1", 0xab9d360e)])


if __name__ == "__main__":
    unittest.main()
