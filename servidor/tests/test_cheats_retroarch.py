# -*- coding: utf-8 -*-
r"""A gaveta "Saves e cheats" no lugar em que o RetroArch guarda e procura.

Auditoria 3, Fase 5 (09/10/2026). Provado com o RetroArch 1.22.2 desta pasta
(testes\teste_cheats_no_jogo.py, que le a memoria do jogo dentro do save
state), tres defeitos que deixavam a gaveta sem funcionar:
  1. os estados (F2) e o save do jogo ficam em retroarch\states\<nucleo>\ e
     retroarch\saves\<nucleo>\ (o retroarch.cfg separa por nucleo); o ARENA
     olhava so a raiz: todos os espacos "vazio" e "voce ainda nao salvou";
  2. o RetroArch so le os cheats de retroarch\cheats\<nucleo>\, com o nome
     do jogo cortado no ultimo ponto; o ARENA gravava em
     retroarch\cheats\<console>\ e o RetroArch nunca achava;
  3. o ARENA gravava handler "1" (a busca de memoria do RetroArch, que
     ignora o codigo); o do emulador e' "0".
E dois a mais, achados no caminho: o validador recusava o Game Genie do NES
e do Mega Drive (letras fora de A-F), e uma quebra de linha na descricao
criava linhas novas no arquivo.
"""
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PASTA_SERVIDOR)

import cheats  # noqa: E402

JOGO_COM_PONTO = "Super Bomberman 4 (Japan) [T-En by Svambo v1.0]"


class TestGavetaNoLugarDoRetroArch(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="arena_cheats_ra_")
        retroarch = os.path.join(self.dir, "retroarch")
        self.pastas = {nome: os.path.join(retroarch, sub) for nome, sub in (
            ("PASTA_CHEATS", "cheats"), ("PASTA_STATES", "states"), ("PASTA_SAVES", "saves"),
            ("PASTA_INFO", "info"))}
        for pasta in self.pastas.values():
            os.makedirs(pasta)
        self.remendo = mock.patch.multiple(cheats, **self.pastas)
        self.remendo.start()
        cheats._NOMES_DOS_NUCLEOS.clear()
        with open(os.path.join(self.pastas["PASTA_INFO"], "snes9x_libretro.info"), "w") as arquivo:
            arquivo.write('display_name = "Nintendo - SNES / SFC (Snes9x - Current)"\ncorename = "Snes9x"\n')
        self.jogo = {"arquivo": "jogos/pessoais/Super Nintendo/%s.sfc" % JOGO_COM_PONTO,
                     "plataforma_nome": "Super Nintendo", "titulo": "Super Bomberman 4"}

    def tearDown(self):
        self.remendo.stop()
        cheats._NOMES_DOS_NUCLEOS.clear()
        shutil.rmtree(self.dir, ignore_errors=True)

    def ler(self, caminho):
        with open(caminho, encoding="utf-8") as arquivo:
            return arquivo.read()

    def test_nome_do_nucleo_pelo_info(self):
        self.assertEqual(cheats.nome_do_nucleo("snes9x_libretro.dll"), "Snes9x")
        self.assertIsNone(cheats.nome_do_nucleo("nao_existe_libretro.dll"))
        self.assertIsNone(cheats.nome_do_nucleo(None))

    def test_nome_do_cht_corta_no_ultimo_ponto_como_o_retroarch(self):
        casos = {
            "Sonic The Hedgehog 3 (USA).md": "Sonic The Hedgehog 3 (USA).cht",
            JOGO_COM_PONTO + ".sfc": "Super Bomberman 4 (Japan) [T-En by Svambo v1.cht",
            "Mr. Driller (USA).chd": "Mr.cht",
        }
        for arquivo, esperado in casos.items():
            with self.subTest(arquivo=arquivo):
                self.assertEqual(cheats.nome_do_cht({"arquivo": "jogos/x/" + arquivo}), esperado)

    def test_cheat_vai_para_a_pasta_do_nucleo_com_handler_0(self):
        lista, erro = cheats.adicionar_cheat(self.jogo, "Vidas", "7E0DBE:09", True, "Snes9x")
        self.assertIsNone(erro)
        self.assertEqual(lista, [{"descricao": "Vidas", "codigo": "7E0DBE:09", "ligado": True}])
        caminho = os.path.join(self.pastas["PASTA_CHEATS"], "Snes9x",
                               "Super Bomberman 4 (Japan) [T-En by Svambo v1.cht")
        self.assertEqual(cheats.caminho_cht(self.jogo, "Snes9x"), caminho)
        texto = self.ler(caminho)
        self.assertIn('cheat0_handler = "0"', texto)
        self.assertIn('cheat0_enable = "true"', texto)
        self.assertNotIn('"1"', texto)
        self.assertFalse(os.path.exists(os.path.join(self.pastas["PASTA_CHEATS"], "Super Nintendo")))

    def test_le_e_respeita_o_arquivo_que_o_retroarch_regrava(self):
        """O RetroArch regrava o .cht ao fechar o jogo, com mais campos. O
        ARENA le e, ao mudar um codigo, mantem os campos dele: um cheat feito
        pela busca de memoria do menu do RetroArch nao pode estragar."""
        pasta = os.path.join(self.pastas["PASTA_CHEATS"], "Snes9x")
        os.makedirs(pasta)
        with open(os.path.join(pasta, cheats.nome_do_cht(self.jogo)), "w", encoding="utf-8") as arquivo:
            arquivo.write(
                'cheats = "2"\n\ncheat0_address = "0"\ncheat0_code = "7E0DBE09"\ncheat0_desc = "Vidas"\n'
                'cheat0_enable = "true"\ncheat0_handler = "0"\n\n'
                'cheat1_address = "8126"\ncheat1_cheat_type = "1"\ncheat1_code = ""\ncheat1_desc = "Busca"\n'
                'cheat1_enable = "false"\ncheat1_handler = "1"\ncheat1_value = "99"\n')
        lidos = cheats.ler_cheats(self.jogo, "Snes9x")
        self.assertEqual([c["descricao"] for c in lidos], ["Vidas", "Busca"])
        self.assertTrue(lidos[0]["ligado"])
        cheats.alterar_cheat(self.jogo, 0, ligado=False, nucleo="Snes9x")
        texto = self.ler(os.path.join(pasta, cheats.nome_do_cht(self.jogo)))
        for linha in ('cheat0_enable = "false"', 'cheat1_handler = "1"', 'cheat1_address = "8126"',
                      'cheat1_value = "99"', 'cheat1_cheat_type = "1"'):
            self.assertIn(linha, texto)

    def test_codigo_do_lugar_antigo_continua_e_vai_certo_para_o_novo(self):
        antigo = cheats.caminho_cht_antigo(self.jogo)
        os.makedirs(os.path.dirname(antigo))
        with open(antigo, "w", encoding="utf-8") as arquivo:
            arquivo.write('cheats = 1\n\ncheat0_desc = "Antigo"\ncheat0_code = "7E0DBE:09"\n'
                          'cheat0_enable = true\ncheat0_handler = "1"\n')
        self.assertEqual([c["descricao"] for c in cheats.ler_cheats(self.jogo, "Snes9x")], ["Antigo"])
        lista, _ = cheats.adicionar_cheat(self.jogo, "Novo", "7E0DBF:01", False, "Snes9x")
        self.assertEqual([c["descricao"] for c in lista], ["Antigo", "Novo"])
        texto = self.ler(cheats.caminho_cht(self.jogo, "Snes9x"))
        self.assertIn('cheat0_desc = "Antigo"', texto)
        self.assertIn('cheat0_handler = "0"', texto)       # o antigo, consertado
        self.assertNotIn('handler = "1"', texto)
        self.assertTrue(os.path.isfile(antigo))             # o arquivo antigo fica como estava

    def test_ao_abrir_o_jogo_o_codigo_antigo_vai_para_o_lugar_certo(self):
        self.assertFalse(cheats.levar_do_lugar_antigo(self.jogo, "Snes9x"))      # nada para levar
        antigo = cheats.caminho_cht_antigo(self.jogo)
        os.makedirs(os.path.dirname(antigo))
        with open(antigo, "w", encoding="utf-8") as arquivo:
            arquivo.write('cheats = 1\n\ncheat0_desc = "Antigo"\ncheat0_code = "7E0DBE:09"\n'
                          'cheat0_enable = true\ncheat0_handler = "1"\n')
        self.assertFalse(cheats.levar_do_lugar_antigo(self.jogo, None))          # sem nucleo, nao mexe
        self.assertTrue(cheats.levar_do_lugar_antigo(self.jogo, "Snes9x"))
        texto = self.ler(cheats.caminho_cht(self.jogo, "Snes9x"))
        self.assertIn('cheat0_handler = "0"', texto)
        self.assertIn('cheat0_enable = "true"', texto)
        self.assertTrue(os.path.isfile(antigo))
        # Ja levado: o RetroArch e o aluno mandam no arquivo novo, nao leva de novo.
        self.assertFalse(cheats.levar_do_lugar_antigo(self.jogo, "Snes9x"))

    def test_estados_na_pasta_do_nucleo_e_na_raiz(self):
        pasta = os.path.join(self.pastas["PASTA_STATES"], "Snes9x")
        os.makedirs(pasta)
        for nome in (".state", ".state.png", ".state3"):
            open(os.path.join(pasta, JOGO_COM_PONTO + nome), "wb").close()
        self.assertEqual([e["espaco"] for e in cheats.listar_estados(self.jogo, "Snes9x") if e["existe"]], [0, 3])
        # Sem o nucleo (como era ate a auditoria 3): nada aparecia.
        self.assertEqual([e["espaco"] for e in cheats.listar_estados(self.jogo) if e["existe"]], [])
        self.assertTrue(cheats.apagar_estado(self.jogo, 0, "Snes9x"))
        self.assertFalse(os.path.exists(os.path.join(pasta, JOGO_COM_PONTO + ".state")))
        self.assertFalse(os.path.exists(os.path.join(pasta, JOGO_COM_PONTO + ".state.png")))   # a foto junto
        self.assertTrue(os.path.exists(os.path.join(pasta, JOGO_COM_PONTO + ".state3")))
        # Com a separacao por nucleo desligada no RetroArch, o estado fica na raiz.
        open(os.path.join(self.pastas["PASTA_STATES"], JOGO_COM_PONTO + ".state1"), "wb").close()
        self.assertEqual([e["espaco"] for e in cheats.listar_estados(self.jogo, "Snes9x") if e["existe"]], [1, 3])
        self.assertFalse(cheats.apagar_estado(self.jogo, 5, "Snes9x"))

    def test_save_do_jogo_na_pasta_do_nucleo(self):
        self.assertFalse(cheats.tem_save(self.jogo, "Snes9x"))
        pasta = os.path.join(self.pastas["PASTA_SAVES"], "Snes9x")
        os.makedirs(pasta)
        open(os.path.join(pasta, JOGO_COM_PONTO + ".srm"), "wb").close()
        self.assertTrue(cheats.tem_save(self.jogo, "Snes9x"))
        self.assertFalse(cheats.tem_save(self.jogo))         # o jeito antigo nao achava

    def test_game_genie_do_nes_e_do_mega_drive(self):
        for codigo in ("SXIOPO", "aaeaeapa", "ATBT-AA32", "DD32-6DAD", "7E0DBE=09", "SXIOPO+AAEAEAPA",
                       "7E0DBE:09 7E0DBF:01", "80012345 1234"):
            with self.subTest(codigo=codigo):
                limpo, erro = cheats.validar_codigo(codigo)
                self.assertIsNone(erro)
                self.assertNotIn(" ", limpo)
        for codigo in ("XYZ", "7E0DBE:ZZZ", 'SXIOPO"', "abc\ncheat1_code = 1", "SXIOP", "<script>"):
            with self.subTest(codigo=codigo):
                limpo, erro = cheats.validar_codigo(codigo)
                self.assertIsNone(limpo)
                self.assertIn("Copie", erro)

    def test_descricao_nao_cria_linha_nova_no_arquivo(self):
        cheats.adicionar_cheat(self.jogo, 'Vidas"\ncheat0_handler = "1', "7E0DBE:09", True, "Snes9x")
        linhas = self.ler(cheats.caminho_cht(self.jogo, "Snes9x")).splitlines()
        self.assertEqual([l for l in linhas if l.startswith("cheat0_handler")], ['cheat0_handler = "0"'])
        self.assertEqual(len([l for l in linhas if l.startswith("cheat0_desc")]), 1)


class TestNucleoDoJogoNoServidor(unittest.TestCase):
    """O servidor acha o nucleo de cada console pelo consoles.json e pelo
    .info de verdade (pulado sem a pasta retroarch\\info, na copia do GitHub)."""

    def test_nucleo_das_pastas(self):
        info = os.path.join(os.path.dirname(PASTA_SERVIDOR), "retroarch", "info", "snes9x_libretro.info")
        if not os.path.isfile(info):
            self.skipTest("sem retroarch\\info")
        import arena
        self.assertEqual(arena.nucleo_das_pastas({"plataforma": "snes"}), "Snes9x")
        self.assertIsNone(arena.nucleo_das_pastas({"plataforma": "nao-existe"}))

    def test_jogo_aberto_nao_deixa_mudar_os_codigos(self):
        import arena
        antes = dict(arena.JOGO_EM_ANDAMENTO)
        try:
            arena.JOGO_EM_ANDAMENTO.update(ativo=True, titulo="X", id="abc")
            self.assertTrue(arena.jogo_aberto_agora({"id": "abc"}))
            self.assertFalse(arena.jogo_aberto_agora({"id": "outro"}))
            arena.JOGO_EM_ANDAMENTO.update(ativo=False)
            self.assertFalse(arena.jogo_aberto_agora({"id": "abc"}))
            self.assertIn("Feche o jogo", arena.MENSAGEM_CHEAT_COM_JOGO_ABERTO)
        finally:
            arena.JOGO_EM_ANDAMENTO.clear()
            arena.JOGO_EM_ANDAMENTO.update(antes)


if __name__ == "__main__":
    unittest.main()
