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


class AchadosDaAuditoria6(Base):
    """Os defeitos de dados achados na auditoria 6 (08/11/2026): nenhum pode apagar jogo ou save do aluno."""

    def setUp(self):
        super().setUp()
        self.console = os.path.join(self.interno, "Super Nintendo")
        self.destino = os.path.join(self.cartao, "ARENA-jogos", "Super Nintendo")

    def test_save_de_mesmo_tamanho_mas_outro_progresso_nao_apaga_o_do_aluno(self):     # DAD6-01
        escrever(os.path.join(self.console, "Zelda.sfc"), b"rom")
        escrever(os.path.join(self.console, "Zelda.srm"), b"AAAA")                      # o progresso do aluno
        escrever(os.path.join(self.destino, "Zelda.srm"), b"BBBB")                      # outro, do mesmo tamanho
        with self.assertRaises(cj.NaoPode):
            cj.levar_jogo(os.path.join(self.console, "Zelda.sfc"), self.console, self.destino)
        with open(os.path.join(self.console, "Zelda.srm"), "rb") as arquivo:
            self.assertEqual(arquivo.read(), b"AAAA")
        self.assertTrue(os.path.exists(os.path.join(self.console, "Zelda.sfc")))

    def test_copia_igual_ja_no_cartao_continua_a_mudanca(self):
        escrever(os.path.join(self.console, "Zelda.sfc"), b"rom")
        escrever(os.path.join(self.destino, "Zelda.sfc"), b"rom")                       # mudanca cortada no meio
        cj.levar_jogo(os.path.join(self.console, "Zelda.sfc"), self.console, self.destino)
        self.assertFalse(os.path.exists(os.path.join(self.console, "Zelda.sfc")))

    def test_trilha_com_maiuscula_diferente_e_as_trilhas_do_m3u(self):                 # DAD6-03
        ps1 = os.path.join(self.interno, "PS1")
        escrever(os.path.join(ps1, "FF.m3u"), b"FF (Disc 1).cue\nFF (Disc 2).cue\n")
        escrever(os.path.join(ps1, "FF (Disc 1).cue"), b'FILE "FF (Disc 1).BIN" BINARY\n')
        escrever(os.path.join(ps1, "FF (Disc 2).cue"), b'FILE "FF (Disc 2).bin" BINARY\n')
        escrever(os.path.join(ps1, "FF (Disc 1).bin"))
        escrever(os.path.join(ps1, "FF (Disc 2).bin"))
        _pasta, nomes = cj.arquivos_do_jogo(os.path.join(ps1, "FF.m3u"), ps1)
        self.assertEqual(nomes, ["FF (Disc 1).bin", "FF (Disc 1).cue", "FF (Disc 2).bin", "FF (Disc 2).cue", "FF.m3u"])

    def test_trilha_que_falta_nao_leva_nada(self):
        ps1 = os.path.join(self.interno, "PS1")
        escrever(os.path.join(ps1, "Crash.cue"), b'FILE "Crash (Track 9).bin" BINARY\n')
        destino = os.path.join(self.cartao, "ARENA-jogos", "PS1")
        with self.assertRaises(cj.NaoPode):
            cj.levar_jogo(os.path.join(ps1, "Crash.cue"), ps1, destino)
        self.assertTrue(os.path.exists(os.path.join(ps1, "Crash.cue")))
        self.assertEqual(cj.bytes_do_jogo(os.path.join(ps1, "Crash.cue"), ps1), 0)

    def test_pasta_com_outros_jogos_leva_so_o_marcado(self):                          # DAD6-06
        ps1 = os.path.join(self.interno, "PS1")
        for nome in ("A.cue", "A.bin", "B.cue", "B.bin"):
            escrever(os.path.join(ps1, "Coletanea", nome), b'FILE "%s.bin" BINARY\n' % nome[0].encode()
                     if nome.endswith(".cue") else b"x")
        _pasta, nomes = cj.arquivos_do_jogo(os.path.join(ps1, "Coletanea", "A.cue"), ps1)
        self.assertEqual(sorted(n.replace("\\", "/") for n in nomes), ["Coletanea/A.bin", "Coletanea/A.cue"])

    def test_a_copia_que_sumiu_antes_de_apagar_deixa_o_original(self):              # DAD6-02
        escrever(os.path.join(self.console, "Zelda.sfc"), b"rom")
        original = cj._copiar

        def copiar_e_perder(origem, destino, progresso):
            original(origem, destino, progresso)
            os.remove(destino)                                                          # o cartao "saiu"
        with mock.patch.object(cj, "_copiar", copiar_e_perder):
            with self.assertRaises(cj.NaoPode):
                cj.levar_jogo(os.path.join(self.console, "Zelda.sfc"), self.console, self.destino)
        self.assertTrue(os.path.exists(os.path.join(self.console, "Zelda.sfc")))

    def test_a_mudanca_guarda_o_que_levou_e_sobrevive_a_erro_estranho(self):         # DAD6-04 e DAD6-08
        escrever(os.path.join(self.console, "Zelda.sfc"), b"rom")
        escrever(os.path.join(self.destino, "Velho.sfc.arena-parcial"), b"sobra")
        mudanca, terminou = cj.Mudanca(), []
        itens = [{"titulo": "Zelda", "caminho": os.path.join(self.console, "Zelda.sfc"),
                  "pasta_do_console": self.console, "destino_do_console": self.destino, "bytes": 3},
                 {"titulo": "Estranho", "caminho": None, "pasta_do_console": self.console,
                  "destino_do_console": self.destino, "bytes": 0}]
        self.assertTrue(mudanca.comecar(itens, lambda: terminou.append(True)))
        limite = time.time() + 10
        while mudanca.rodando() and time.time() < limite:
            time.sleep(0.05)
        self.assertEqual(mudanca.levados(), [(os.path.join(self.console, "Zelda.sfc"),
                                              os.path.join(self.destino, "Zelda.sfc"))])
        self.assertEqual(len(mudanca.estado()["erros"]), 1)
        self.assertFalse(os.path.exists(os.path.join(self.destino, "Velho.sfc.arena-parcial")))
        self.assertEqual(terminou, [True])


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
