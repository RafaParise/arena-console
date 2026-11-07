# -*- coding: utf-8 -*-
"""A pasta ARENA-jogos no cartao SD e levar para ela os jogos da memoria do aparelho (servidor\\cartao_de_jogos.py).

Pastas temporarias fazem o papel da memoria interna e do cartao: nada toca em celular de verdade.
"""
import os
import sys
import tempfile
import time
import unittest
from unittest import mock

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(AQUI)), "testes"))
import armazenamento  # noqa: E402
import baixados  # noqa: E402
import cartao_de_jogos as cj  # noqa: E402
import limpeza  # noqa: E402


def escrever(caminho, conteudo=b"x"):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "wb") as arquivo:
        arquivo.write(conteudo)


class Base(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_cartao_")
        self.addCleanup(limpeza.apagar_pasta, self.pasta)
        self.interno = os.path.join(self.pasta, "interno")
        self.cartao = os.path.join(self.pasta, "cartao")
        os.makedirs(self.interno)
        os.makedirs(self.cartao)
        self.raizes = [self.interno, self.cartao]
        configuracao = os.path.join(self.pasta, "dados", "armazenamento.json")
        remendo = mock.patch.object(armazenamento, "arquivo_de_configuracao", return_value=configuracao)
        remendo.start()
        self.addCleanup(remendo.stop)
        self.consoles = ["Super Nintendo", "PS1"]


class OsArquivosDoJogo(Base):
    def test_jogo_solto_leva_os_do_mesmo_nome_e_as_trilhas_do_cue(self):
        console = os.path.join(self.interno, "PS1")
        escrever(os.path.join(console, "Crash.cue"), b'FILE "Crash (Track 1).bin" BINARY\nFILE "Crash (Track 2).bin" BINARY\n')
        for nome in ("Crash (Track 1).bin", "Crash (Track 2).bin", "Crash.srm", "Outro.bin"):
            escrever(os.path.join(console, nome))
        pasta, nomes = cj.arquivos_do_jogo(os.path.join(console, "Crash.cue"), console)
        self.assertEqual(pasta, console)
        self.assertEqual(nomes, ["Crash (Track 1).bin", "Crash (Track 2).bin", "Crash.cue", "Crash.srm"])

    def test_jogo_numa_pasta_so_dele_leva_a_pasta(self):
        console = os.path.join(self.interno, "PS1")
        escrever(os.path.join(console, "Crash", "Crash.cue"))
        escrever(os.path.join(console, "Crash", "Crash.bin"))
        escrever(os.path.join(console, "Outro.bin"))
        pasta, nomes = cj.arquivos_do_jogo(os.path.join(console, "Crash", "Crash.cue"), console)
        self.assertEqual(pasta, console)
        self.assertEqual(sorted(n.replace("\\", "/") for n in nomes), ["Crash/Crash.bin", "Crash/Crash.cue"])


class LevarUmJogo(Base):
    def test_copia_confere_e_so_depois_apaga(self):
        console = os.path.join(self.interno, "Super Nintendo")
        escrever(os.path.join(console, "Zelda.sfc"), b"z" * 5000)
        escrever(os.path.join(console, "Zelda.srm"), b"s" * 10)
        destino = os.path.join(self.cartao, "ARENA-jogos", "Super Nintendo")
        andou = []
        novo = cj.levar_jogo(os.path.join(console, "Zelda.sfc"), console, destino, andou.append)
        self.assertEqual(novo, os.path.join(destino, "Zelda.sfc"))
        self.assertEqual(os.path.getsize(novo), 5000)
        self.assertTrue(os.path.isfile(os.path.join(destino, "Zelda.srm")))
        self.assertFalse(os.path.exists(os.path.join(console, "Zelda.sfc")))
        self.assertEqual(sum(andou), 5010)
        self.assertEqual([n for n in os.listdir(destino) if n.endswith(".arena-parcial")], [])

    def test_pasta_do_jogo_vai_inteira_e_a_vazia_sai(self):
        console = os.path.join(self.interno, "PS1")
        escrever(os.path.join(console, "Crash", "Crash.cue"))
        escrever(os.path.join(console, "Crash", "faixas", "Crash.bin"))
        destino = os.path.join(self.cartao, "ARENA-jogos", "PS1")
        cj.levar_jogo(os.path.join(console, "Crash", "Crash.cue"), console, destino)
        self.assertTrue(os.path.isfile(os.path.join(destino, "Crash", "faixas", "Crash.bin")))
        self.assertFalse(os.path.exists(os.path.join(console, "Crash")))
        self.assertTrue(os.path.isdir(console))                        # a pasta do console nunca sai

    def test_arquivo_diferente_no_cartao_nao_mexe_em_nada(self):
        console = os.path.join(self.interno, "Super Nintendo")
        escrever(os.path.join(console, "Zelda.sfc"), b"z" * 50)
        destino = os.path.join(self.cartao, "ARENA-jogos", "Super Nintendo")
        escrever(os.path.join(destino, "Zelda.sfc"), b"outro")
        with self.assertRaises(cj.NaoPode):
            cj.levar_jogo(os.path.join(console, "Zelda.sfc"), console, destino)
        self.assertEqual(os.path.getsize(os.path.join(console, "Zelda.sfc")), 50)

    def test_copia_que_falha_deixa_o_original(self):
        console = os.path.join(self.interno, "Super Nintendo")
        escrever(os.path.join(console, "Zelda.sfc"), b"z" * 50)
        destino = os.path.join(self.cartao, "ARENA-jogos", "Super Nintendo")
        with mock.patch.object(cj.os, "replace", side_effect=OSError(28, "No space left on device")):
            with self.assertRaises(OSError):
                cj.levar_jogo(os.path.join(console, "Zelda.sfc"), console, destino)
        self.assertTrue(os.path.isfile(os.path.join(console, "Zelda.sfc")))
        self.assertEqual(os.listdir(destino), [])                       # nem o pedaco copiado sobra

    def test_a_mudanca_em_segundo_plano(self):
        console = os.path.join(self.interno, "Super Nintendo")
        escrever(os.path.join(console, "A.sfc"), b"a" * 100)
        escrever(os.path.join(console, "B.sfc"), b"b" * 100)
        destino = os.path.join(self.cartao, "ARENA-jogos", "Super Nintendo")
        escrever(os.path.join(destino, "B.sfc"), b"diferente")
        terminou = []
        mudanca = cj.Mudanca()
        itens = [{"titulo": n, "caminho": os.path.join(console, n + ".sfc"), "pasta_do_console": console,
                  "destino_do_console": destino, "bytes": 100} for n in ("A", "B")]
        self.assertTrue(mudanca.comecar(itens, lambda: terminou.append(True)))
        fim = time.monotonic() + 10
        while mudanca.estado()["rodando"] and time.monotonic() < fim:
            time.sleep(0.05)
        estado = mudanca.estado()
        self.assertEqual((estado["feitos"], estado["total"]), (2, 2))
        self.assertEqual(len(estado["erros"]), 1)
        self.assertIn("B", estado["erros"][0])
        self.assertEqual(terminou, [True])
        self.assertTrue(os.path.isfile(os.path.join(destino, "A.sfc")))
        self.assertTrue(os.path.isfile(os.path.join(console, "B.sfc")))     # o que deu erro fica


class APastaNoCartao(Base):
    def test_criar_poe_as_pastas_dos_consoles_e_entra_na_lista(self):
        caminho = cj.criar_no_cartao(self.cartao, self.consoles, raizes=self.raizes)
        self.assertEqual(sorted(os.listdir(caminho)), ["LEIA.txt", "PS1", "Super Nintendo"])
        extras = armazenamento.ler()["jogos_extras"]
        self.assertEqual(len(extras), 1)
        self.assertEqual(extras[0]["nome"], cj.NOME_NA_LISTA)
        self.assertEqual(cj.pasta_no_cartao(), extras[0]["caminho"])
        # de novo: nao duplica
        cj.criar_no_cartao(self.cartao, self.consoles, raizes=self.raizes)
        self.assertEqual(len(armazenamento.ler()["jogos_extras"]), 1)

    def test_sem_cartao_explica(self):
        with self.assertRaises(cj.NaoPode) as falha:
            cj.criar_no_cartao(os.path.join(self.pasta, "nao-existe"), self.consoles, raizes=self.raizes)
        self.assertIn("Encaixe", str(falha.exception))

    def test_os_jogos_da_memoria(self):
        pessoais = os.path.join(self.interno, "ARENA", "jogos", "pessoais")
        escrever(os.path.join(pessoais, "Super Nintendo", "Zelda.sfc"), b"z" * 2048)
        jogos = [{"id": "jogos/pessoais/Super Nintendo/Zelda.sfc", "titulo": "Zelda", "origem": "pessoais",
                  "arquivo": "jogos/pessoais/Super Nintendo/Zelda.sfc"},
                 {"id": "livre", "titulo": "Livre", "origem": "livres", "arquivo": "jogos/livres/NES/x.nes"},
                 {"id": "cartao", "titulo": "No cartao", "origem": "cartao-1234", "arquivo": "jogos/cartao-1234/x.sfc"}]
        achados = cj.jogos_na_memoria(jogos, os.path.join(self.interno, "ARENA"),
                                      os.path.join(self.interno, "ARENA", "jogos"), raizes=self.raizes)
        self.assertEqual(achados, [{"id": "jogos/pessoais/Super Nintendo/Zelda.sfc", "titulo": "Zelda",
                                    "console": "Super Nintendo", "bytes": 2048}])


class OsBaixadosVaoParaOCartao(Base):
    def test_levar_com_prateleira(self):
        downloads = os.path.join(self.interno, "Download")
        escrever(os.path.join(downloads, "Zelda.sfc"))
        plataformas = [{"id": "snes", "nome": "Super Nintendo", "pasta": "Super Nintendo", "extensoes": [".sfc"]}]
        prateleira = os.path.join(self.cartao, "ARENA-jogos")
        destino = baixados.levar(os.path.join(downloads, "Zelda.sfc"), "snes", plataformas,
                                 os.path.join(self.interno, "ARENA", "jogos"), pastas=[os.path.realpath(downloads)],
                                 prateleira=prateleira)
        self.assertEqual(destino, os.path.join(prateleira, "Super Nintendo", "Zelda.sfc"))
        self.assertTrue(os.path.isfile(destino))


if __name__ == "__main__":
    unittest.main()
