# -*- coding: utf-8 -*-
"""O armazenamento do celular: memoria interna e cartao SD juntos (servidor\\armazenamento.py).

Pedido do Rafael de 23/10/2026: jogos no cartao e no interno ao mesmo tempo, e o ARENA
cuidando disso quando o interno esta cheio. Aqui os volumes sao pastas temporarias (a
memoria do aparelho e o cartao); o teste de verdade, com o cartao do A12, e' o da
rodada no aparelho."""
import json
import os
import sys
import tempfile
import threading
import unittest
from unittest import mock

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PASTA_SERVIDOR not in sys.path:
    sys.path.insert(0, PASTA_SERVIDOR)
sys.path.insert(0, os.path.join(os.path.dirname(PASTA_SERVIDOR), "testes"))

import armazenamento  # noqa: E402
import limpeza  # noqa: E402

CONSOLES = {"ps1", "ps2", "dreamcast", "super nintendo", "psp", "nes"}


class Base(unittest.TestCase):
    """Dois volumes de mentira (a memoria do aparelho e o cartao) e uma pasta de dados."""

    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_armazenamento_")
        self.memoria = os.path.join(self.pasta, "emulated", "0")
        self.cartao = os.path.join(self.pasta, "1234-5678")
        self.dados = os.path.join(self.pasta, "dados")
        for pasta in (self.memoria, self.cartao, self.dados):
            os.makedirs(pasta)
        self.raizes = [self.memoria, self.cartao]
        self.troca = mock.patch.object(armazenamento, "PASTA_DADOS", self.dados)
        self.troca.start()

    def tearDown(self):
        self.troca.stop()
        limpeza.apagar_pasta(self.pasta)

    def criar(self, *partes, **conteudo):
        caminho = os.path.join(self.pasta, *partes)
        os.makedirs(caminho, exist_ok=True)
        return caminho

    def jogos_no_cartao(self, *onde, consoles=("PS1", "Dreamcast", "Super Nintendo")):
        raiz = self.criar("1234-5678", *onde)
        for console in consoles:
            os.makedirs(os.path.join(raiz, console), exist_ok=True)
        return raiz


class Volumes(Base):

    def test_a_memoria_e_o_cartao(self):
        v = armazenamento.volumes(self.raizes, nomes={self.cartao: "Meu Cartão SD"})
        self.assertEqual([x["id"] for x in v], ["interno", "cartao-1234-5678"])
        self.assertEqual([x["removivel"] for x in v], [False, True])
        self.assertEqual(v[0]["nome"], "Armazenamento interno")
        self.assertEqual(v[1]["nome"], "Meu Cartão SD")
        for volume in v:
            self.assertTrue(volume["montado"])
            self.assertGreater(volume["total_mb"], 0)
            self.assertLessEqual(volume["livre_mb"], volume["total_mb"])
            self.assertTrue(0 <= volume["usado_pct"] <= 100)

    def test_cartao_sem_nome_do_android_tem_nome_pelo_codigo(self):
        self.assertEqual(armazenamento.volumes(self.raizes)[1]["nome"], "Cartão de memória (1234-5678)")

    def test_cartao_que_saiu_aparece_como_ausente(self):
        v = armazenamento.volumes([self.memoria, os.path.join(self.pasta, "8765-4321")])
        self.assertFalse(v[1]["montado"])
        self.assertEqual(v[1]["total_mb"], 0)

    def test_de_que_volume_e_a_pasta(self):
        pasta = self.criar("1234-5678", "Jogos", "PS1")
        self.assertEqual(armazenamento.volume_da_pasta(pasta, self.raizes), 1)
        self.assertEqual(armazenamento.volume_da_pasta(self.memoria, self.raizes), 0)
        self.assertIsNone(armazenamento.volume_da_pasta(self.dados, self.raizes))
        # "1234-5678-outro" nao e' o volume "1234-5678": compara pasta por pasta
        self.assertIsNone(armazenamento.volume_da_pasta(self.criar("1234-5678-outro", "x"), self.raizes))


class Configuracao(Base):

    def test_sem_arquivo_vale_o_padrao(self):
        self.assertEqual(armazenamento.ler(), {"jogos_extras": [], "jogar_do_cartao": "direto",
                                               "limite_do_cache_mb": 2048})

    def test_arquivo_estragado_ou_com_lixo_nao_derruba(self):
        arquivo = armazenamento.arquivo_de_configuracao()
        for texto in ("", "{", "[1,2]", "null", '{"jogos_extras": 5}', '{"jogos_extras": [1, "a", null]}'):
            with open(arquivo, "w", encoding="utf-8") as f:
                f.write(texto)
            self.assertEqual(armazenamento.ler()["jogos_extras"], [], texto)

    def test_so_entra_o_que_vale(self):
        bom = {"id": "cartao-1234-5678", "nome": "Meu cartão", "caminho": self.cartao}
        ruins = [{"id": "interno", "nome": "x", "caminho": self.cartao},               # id fora do formato
                 {"id": "cartao-../x", "nome": "x", "caminho": self.cartao},
                 {"id": "cartao-1234-5678", "nome": "repetido", "caminho": self.cartao},
                 {"id": "cartao-a", "nome": "x", "caminho": ""},
                 {"id": "cartao-b", "nome": "x", "caminho": "a\x00b"},
                 {"id": "cartao-c", "nome": "x", "caminho": "/" + "a" * 600},
                 "texto", 5, None]
        dados = armazenamento._limpar({"jogos_extras": [bom] + ruins, "jogar_do_cartao": "lixo",
                                       "limite_do_cache_mb": "10"})
        self.assertEqual(dados["jogos_extras"], [bom])
        self.assertEqual((dados["jogar_do_cartao"], dados["limite_do_cache_mb"]), ("direto", 2048))

    def test_nome_com_controle_e_muito_longo(self):
        dados = armazenamento._limpar({"jogos_extras": [
            {"id": "cartao-a", "nome": "Ca\nrtão\x00" + "x" * 100, "caminho": self.cartao}]})
        nome = dados["jogos_extras"][0]["nome"]
        self.assertNotIn("\n", nome)
        self.assertNotIn("\x00", nome)
        self.assertLessEqual(len(nome), 40)

    def test_grava_e_le_de_volta_sem_deixar_temporario(self):
        armazenamento.gravar({"jogos_extras": [{"id": "cartao-a", "nome": "A", "caminho": self.cartao}],
                              "jogar_do_cartao": "copiar", "limite_do_cache_mb": 4096})
        lido = armazenamento.ler()
        self.assertEqual((lido["jogar_do_cartao"], lido["limite_do_cache_mb"]), ("copiar", 4096))
        self.assertEqual([n for n in os.listdir(self.dados) if n.endswith(".tmp")], [])
        with open(armazenamento.arquivo_de_configuracao(), encoding="utf-8") as f:
            json.load(f)

    def test_varias_linhas_gravando_ao_mesmo_tempo(self):
        def trabalho(i):
            for _ in range(15):
                armazenamento.definir_jogo_do_cartao("copiar" if i % 2 else "direto", 512 + i)
        fios = [threading.Thread(target=trabalho, args=(i,)) for i in range(6)]
        for fio in fios:
            fio.start()
        for fio in fios:
            fio.join(30)
        with open(armazenamento.arquivo_de_configuracao(), encoding="utf-8") as f:
            self.assertIn(json.load(f)["jogar_do_cartao"], ("direto", "copiar"))
        self.assertEqual([n for n in os.listdir(self.dados) if n.endswith(".tmp")], [])

    def test_escolha_do_aluno_jogar_direto_ou_copiar(self):
        dados, erro = armazenamento.definir_jogo_do_cartao("copiar", 3072)
        self.assertIsNone(erro)
        self.assertEqual((dados["jogar_do_cartao"], dados["limite_do_cache_mb"]), ("copiar", 3072))
        self.assertEqual(armazenamento.definir_jogo_do_cartao("lixo")[0]["jogar_do_cartao"], "copiar")
        for ruim in (10, 70000, "abc", None, -5):
            if ruim is None:
                continue
            dados, erro = armazenamento.definir_jogo_do_cartao(None, ruim)
            self.assertIsNone(dados, ruim)
            self.assertIn("256 MB", erro)


class EscolherAPasta(Base):

    def validar(self, caminho, **extra):
        return armazenamento.validar_pasta_de_jogos(caminho, self.raizes, CONSOLES, **extra)

    def test_pasta_boa(self):
        pasta = self.jogos_no_cartao("Projetos", "arena-console", "jogos", "pessoais")
        real, erro = self.validar(pasta)
        self.assertIsNone(erro)
        self.assertEqual(real, os.path.realpath(pasta))

    def test_o_que_fazer_em_cada_recusa(self):
        cartao_inteiro = self.cartao
        pasta_de_apps = self.criar("1234-5678", "Android", "data", "com.x")
        vazia = self.criar("1234-5678", "Videos")
        fora = self.criar("fora", "PS1")
        casos = [(None, "Escolha uma pasta"), ("", "Escolha uma pasta"), ("a\x00b", "Escolha uma pasta"),
                 (os.path.join(self.cartao, "nao_existe"), "cartão está encaixado"),
                 (fora, "memória do aparelho ou no cartão"),
                 (cartao_inteiro, "e não o cartão inteiro"),
                 (pasta_de_apps, "dados de outros aplicativos"),
                 (vazia, "nenhuma pasta de console")]
        for caminho, esperado in casos:
            real, erro = self.validar(caminho)
            self.assertIsNone(real, caminho)
            self.assertIn(esperado, erro, caminho)

    def test_nao_aceita_a_pasta_de_meus_jogos_do_proprio_arena(self):
        propria = self.criar("emulated", "0", "ARENA", "jogos", "pessoais")
        os.makedirs(os.path.join(propria, "PS1"))
        real, erro = self.validar(propria, proprias=[propria])
        self.assertIsNone(real)
        self.assertIn("Meus jogos", erro)
        # nem uma pasta de dentro dela, nem a de cima
        self.assertIsNotNone(self.validar(os.path.join(propria, "PS1"), proprias=[propria])[1])
        self.assertIsNotNone(self.validar(os.path.dirname(propria), proprias=[propria])[1])

    def test_um_atalho_para_fora_nao_passa_pela_conferencia(self):
        # a conferencia olha o caminho de VERDADE, nao o nome do atalho
        alvo = self.criar("fora", "PS1")
        atalho = os.path.join(self.cartao, "atalho")
        try:
            os.symlink(os.path.dirname(alvo), atalho, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("sem permissao para criar atalho")
        self.assertIsNone(self.validar(atalho)[0])


class ListaDePastas(Base):

    def test_poe_o_cartao_na_lista(self):
        pasta = self.jogos_no_cartao("jogos")
        dados, erro = armazenamento.adicionar(pasta, self.raizes, consoles=CONSOLES)
        self.assertIsNone(erro)
        extra = dados["jogos_extras"][0]
        self.assertEqual((extra["id"], extra["nome"]), ("cartao-1234-5678", "Cartão de memória"))
        self.assertEqual(os.path.realpath(extra["caminho"]), os.path.realpath(pasta))
        self.assertEqual(armazenamento.ler()["jogos_extras"][0]["id"], "cartao-1234-5678")

    def test_nao_repete_e_a_segunda_do_mesmo_cartao_ganha_numero(self):
        a = self.jogos_no_cartao("jogos")
        b = self.jogos_no_cartao("outros")
        self.assertIsNone(armazenamento.adicionar(a, self.raizes, consoles=CONSOLES)[1])
        self.assertIn("já está na lista", armazenamento.adicionar(a, self.raizes, consoles=CONSOLES)[1])
        dados, erro = armazenamento.adicionar(b, self.raizes, nome="Segunda", consoles=CONSOLES)
        self.assertIsNone(erro)
        self.assertEqual([e["id"] for e in dados["jogos_extras"]], ["cartao-1234-5678", "cartao-1234-5678-2"])

    def test_tem_limite(self):
        for i in range(armazenamento.LIMITE_DE_PASTAS):
            self.assertIsNone(armazenamento.adicionar(self.jogos_no_cartao("p%d" % i), self.raizes, consoles=CONSOLES)[1])
        erro = armazenamento.adicionar(self.jogos_no_cartao("a_mais"), self.raizes, consoles=CONSOLES)[1]
        self.assertIn("Tire uma", erro)

    def test_tirar_da_lista_nao_toca_nos_jogos(self):
        pasta = self.jogos_no_cartao("jogos")
        jogo = os.path.join(pasta, "PS1", "Crash.chd")
        with open(jogo, "wb") as f:
            f.write(b"x")
        armazenamento.adicionar(pasta, self.raizes, consoles=CONSOLES)
        dados, erro = armazenamento.remover("cartao-1234-5678")
        self.assertIsNone(erro)
        self.assertEqual(dados["jogos_extras"], [])
        self.assertTrue(os.path.isfile(jogo))
        self.assertIn("não está na lista", armazenamento.remover("cartao-1234-5678")[1])
        self.assertIn("não está na lista", armazenamento.remover("../../x")[1])

    def test_o_nome_das_origens_para_o_indexador(self):
        armazenamento.adicionar(self.jogos_no_cartao("jogos"), self.raizes, nome="Meu SD", consoles=CONSOLES)
        self.assertEqual(armazenamento.rotulos_das_origens(), {"cartao-1234-5678": "Meu SD"})


class Atalhos(Base):

    def setUp(self):
        super().setUp()
        self.jogos = self.criar("app", "jogos")
        self.pasta_do_cartao = self.jogos_no_cartao("jogos")
        self.extra = {"id": "cartao-1234-5678", "nome": "SD", "caminho": self.pasta_do_cartao}

    def ligar(self, extras):
        try:
            return armazenamento.ligar_extras(self.jogos, extras)
        except (OSError, NotImplementedError):
            self.skipTest("sem permissao para criar atalho")

    def test_liga_o_cartao_como_uma_origem(self):
        situacao = self.ligar([self.extra])
        if situacao.get(self.extra["id"], "").startswith("erro"):
            self.skipTest("sem permissao para criar atalho: " + situacao[self.extra["id"]])
        self.assertEqual(situacao, {"cartao-1234-5678": "ligado"})
        atalho = os.path.join(self.jogos, "cartao-1234-5678")
        self.assertTrue(os.path.islink(atalho))
        self.assertEqual(sorted(os.listdir(atalho)), ["Dreamcast", "PS1", "Super Nintendo"])
        self.assertEqual(self.ligar([self.extra]), {"cartao-1234-5678": "ja_estava"})

    def test_cartao_que_saiu_nao_deixa_atalho_no_ar(self):
        if self.ligar([self.extra]).get(self.extra["id"], "").startswith("erro"):
            self.skipTest("sem permissao para criar atalho")
        limpeza.apagar_pasta(self.pasta_do_cartao)
        self.assertEqual(self.ligar([self.extra]), {"cartao-1234-5678": "ausente"})
        self.assertFalse(os.path.lexists(os.path.join(self.jogos, "cartao-1234-5678")))

    def test_tirar_da_lista_desfaz_so_o_atalho(self):
        if self.ligar([self.extra]).get(self.extra["id"], "").startswith("erro"):
            self.skipTest("sem permissao para criar atalho")
        self.ligar([])
        self.assertFalse(os.path.lexists(os.path.join(self.jogos, "cartao-1234-5678")))
        self.assertTrue(os.path.isdir(os.path.join(self.pasta_do_cartao, "PS1")))      # os jogos ficam

    def test_nunca_mexe_em_pasta_de_verdade_nem_em_atalho_de_outro_nome(self):
        verdadeira = self.criar("app", "jogos", "cartao-1234-5678", "PS1")
        self.assertIn("erro", self.ligar([self.extra])["cartao-1234-5678"])
        self.assertTrue(os.path.isdir(verdadeira))
        # uma pasta "pessoais" (que nao e' de cartao) fica como esta, mesmo fora da lista
        pessoais = self.criar("app", "jogos", "pessoais")
        self.ligar([])
        self.assertTrue(os.path.isdir(pessoais))
        self.assertTrue(os.path.isdir(verdadeira))


class AcharPastasDeJogos(Base):

    def test_acha_a_pasta_de_jogos_funda_do_cartao(self):
        pasta = self.jogos_no_cartao("Projetos", "Criador", "arena-console", "jogos", "pessoais")
        achado = armazenamento.procurar_pastas_de_jogos(self.cartao, CONSOLES)
        self.assertTrue(achado["completo"])
        self.assertEqual([c["caminho"] for c in achado["candidatas"]], [pasta])
        self.assertEqual(achado["candidatas"][0]["consoles"], 3)
        self.assertEqual(achado["candidatas"][0]["onde"], "Projetos › Criador › arena-console › jogos › pessoais")

    def test_nao_entra_em_android_nem_em_foto_e_nao_conta_pasta_de_uma_so(self):
        self.jogos_no_cartao("Android", "data", "com.x", "jogos")
        self.jogos_no_cartao("DCIM", "Camera", "jogos")
        self.jogos_no_cartao("umas", "so", consoles=("PS1",))                  # so uma pasta de console: nao conta
        achado = armazenamento.procurar_pastas_de_jogos(self.cartao, CONSOLES)
        self.assertEqual(achado["candidatas"], [])

    def test_pasta_escondida_e_muito_funda_ficam_de_fora(self):
        self.jogos_no_cartao(".oculta", "jogos")
        self.jogos_no_cartao("a", "b", "c", "d", "e", "f", "g", "jogos")      # 8 niveis: passa do limite
        self.assertEqual(armazenamento.procurar_pastas_de_jogos(self.cartao, CONSOLES, profundidade=5)["candidatas"], [])
        achou = armazenamento.procurar_pastas_de_jogos(self.cartao, CONSOLES, profundidade=9)["candidatas"]
        self.assertEqual(len(achou), 1)

    def test_para_no_tempo_limite_e_avisa(self):
        for i in range(10):
            self.criar("1234-5678", "d%d" % i, "x")
        passos = iter(range(0, 1000))
        achado = armazenamento.procurar_pastas_de_jogos(self.cartao, CONSOLES, limite_s=3, relogio=lambda: next(passos))
        self.assertFalse(achado["completo"])
        self.assertLessEqual(achado["pastas_vistas"], 5)

    def test_a_melhor_vem_primeiro(self):
        poucas = self.jogos_no_cartao("a", consoles=("PS1", "PS2"))
        muitas = self.jogos_no_cartao("b", consoles=("PS1", "PS2", "NES", "PSP"))
        achado = armazenamento.procurar_pastas_de_jogos(self.cartao, CONSOLES)["candidatas"]
        self.assertEqual([c["caminho"] for c in achado], [muitas, poucas])

    def test_cada_pasta_e_listada_uma_vez_so(self):
        """No cartao de verdade, listar pasta e' o que custa: uma listagem por pasta (antes eram duas)."""
        self.jogos_no_cartao("jogos")
        listagens = []
        original = os.scandir

        def contando(caminho):
            listagens.append(os.path.normcase(os.path.abspath(str(caminho))))
            return original(caminho)

        with mock.patch.object(armazenamento.os, "scandir", side_effect=contando):
            armazenamento.procurar_pastas_de_jogos(self.cartao, CONSOLES)
        self.assertEqual(len(listagens), len(set(listagens)))

    def test_vai_primeiro_pelos_nomes_que_levam_a_jogos(self):
        """Num cartao cheio de pastas, a busca acha 'ARENA/jogos' antes de abrir as outras, mesmo com
        poucos segundos: o que se mede no celular e' o tempo para listar pasta."""
        for i in range(40):
            self.criar("1234-5678", "pasta%02d" % i, "dentro%d" % i)
        procurada = self.jogos_no_cartao("Projetos", "ARENA", "jogos")
        passos = iter(x * 0.5 for x in range(0, 10000))          # 0,5 s por pasta listada; limite de 4 s
        achado = armazenamento.procurar_pastas_de_jogos(self.cartao, CONSOLES, limite_s=4, relogio=lambda: next(passos))
        self.assertEqual([c["caminho"] for c in achado["candidatas"]], [procurada])
        self.assertFalse(achado["completo"])

    def test_a_prioridade_do_nome(self):
        self.assertEqual([armazenamento._prioridade_do_nome(n) for n in ("ARENA", "Jogos", "Meus Jogos", "DCIM2", "roms")],
                         [0, 0, 1, 2, 0])


class EscolherPassoAPasso(Base):

    def test_lista_as_subpastas_e_diz_se_serve(self):
        jogos = self.jogos_no_cartao("Projetos", "ARENA", "jogos")
        self.criar("1234-5678", "Projetos", "ARENA", "BIOS")
        self.criar("1234-5678", "Projetos", ".oculta")
        dados, erro = armazenamento.listar_subpastas(os.path.join(self.cartao, "Projetos", "ARENA"), self.raizes, CONSOLES)
        self.assertIsNone(erro)
        self.assertEqual([p["nome"] for p in dados["pastas"]], ["BIOS", "jogos"])
        self.assertEqual((dados["consoles"], dados["serve"]), (0, False))
        self.assertEqual(os.path.realpath(dados["pai"]), os.path.realpath(os.path.join(self.cartao, "Projetos")))
        dentro, erro = armazenamento.listar_subpastas(jogos, self.raizes, CONSOLES)
        self.assertEqual((dentro["consoles"], dentro["serve"]), (3, True))
        self.assertEqual(dentro["volume"], "cartao-1234-5678")

    def test_na_raiz_do_volume_nao_ha_para_onde_subir(self):
        dados, _ = armazenamento.listar_subpastas(self.cartao, self.raizes, CONSOLES)
        self.assertEqual(dados["pai"], "")

    def test_nao_deixa_sair_do_aparelho_nem_entrar_nos_dados_dos_apps(self):
        for pedido in ("", None, "   ", self.dados, os.path.join(self.pasta, "fora"), self.cartao + "\x00"):
            dados, erro = armazenamento.listar_subpastas(pedido, self.raizes, CONSOLES)
            self.assertIsNone(dados, pedido)
            self.assertTrue(erro, pedido)
        apps = self.criar("1234-5678", "Android", "data", "com.x")
        dados, erro = armazenamento.listar_subpastas(apps, self.raizes, CONSOLES)
        self.assertIsNone(dados)
        self.assertIn("dados de outros aplicativos", erro)

    def test_lista_enorme_e_cortada(self):
        for i in range(armazenamento.MAXIMO_DE_PASTAS_NA_LISTA + 5):
            os.makedirs(os.path.join(self.cartao, "p%04d" % i))
        dados, _ = armazenamento.listar_subpastas(self.cartao, self.raizes, CONSOLES)
        self.assertEqual(len(dados["pastas"]), armazenamento.MAXIMO_DE_PASTAS_NA_LISTA)
        self.assertTrue(dados["cortado"])


class Velocidade(Base):

    def test_acha_o_maior_arquivo_sem_gravar_nada(self):
        pasta = self.criar("1234-5678", "jogos", "PS1")
        for nome, mb in (("a.bin", 1), ("b.chd", 3), ("c.cue", 0)):
            with open(os.path.join(pasta, nome), "wb") as f:
                f.write(b"\0" * (mb * 1048576 + (7 if mb else 0)))
        self.assertEqual(os.path.basename(armazenamento.maior_arquivo(self.cartao, minimo_mb=1)), "b.chd")
        self.assertIsNone(armazenamento.maior_arquivo(self.cartao, minimo_mb=64))

    def test_mede_a_leitura(self):
        arquivo = os.path.join(self.pasta, "grande.bin")
        with open(arquivo, "wb") as f:
            f.write(os.urandom(3 * 1048576))
        velocidade = armazenamento.medir_leitura(arquivo, mb=2)
        self.assertGreater(velocidade, 0)
        # com um relogio fingido: 2 MB em 0,5 s = 4 MB/s
        tempos = iter([0.0, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5])
        self.assertEqual(armazenamento.medir_leitura(arquivo, mb=2, relogio=lambda: next(tempos)), 4.0)
        with open(os.path.join(self.pasta, "vazio.bin"), "wb"):
            pass
        self.assertIsNone(armazenamento.medir_leitura(os.path.join(self.pasta, "vazio.bin")))

    def test_mede_o_interno_e_apaga_o_temporario(self):
        medida = armazenamento.medir_gravacao_e_leitura(self.dados, mb=2)
        self.assertGreater(medida["gravacao_mb_s"], 0)
        self.assertGreater(medida["leitura_mb_s"], 0)
        self.assertEqual(os.listdir(self.dados), [])


class OQueATelaMostra(Base):

    def test_o_estado_tem_volumes_pastas_e_a_escolha(self):
        pasta = self.jogos_no_cartao("jogos")
        armazenamento.adicionar(pasta, self.raizes, nome="Meu SD", consoles=CONSOLES)
        estado = armazenamento.estado(self.raizes, consoles=CONSOLES)
        self.assertEqual([v["id"] for v in estado["volumes"]], ["interno", "cartao-1234-5678"])
        extra = estado["extras"][0]
        self.assertEqual((extra["id"], extra["existe"], extra["consoles"], extra["volume"]),
                         ("cartao-1234-5678", True, 3, "cartao-1234-5678"))
        self.assertEqual((estado["jogar_do_cartao"], estado["limite_do_cache_mb"]), ("direto", 2048))

    def test_cartao_que_saiu_aparece_como_ausente_sem_apagar_da_lista(self):
        pasta = self.jogos_no_cartao("jogos")
        armazenamento.adicionar(pasta, self.raizes, consoles=CONSOLES)
        limpeza.apagar_pasta(pasta)
        extra = armazenamento.estado(self.raizes, consoles=CONSOLES)["extras"][0]
        self.assertFalse(extra["existe"])
        self.assertEqual(extra["consoles"], 0)
        self.assertEqual(len(armazenamento.ler()["jogos_extras"]), 1)       # volta sozinho quando o cartao voltar


class RotasDoServidor(Base):
    """O servidor de verdade (numa porta qualquer), com o Android imitado e os volumes de mentira."""

    @classmethod
    def setUpClass(cls):
        import arena
        cls.arena = arena
        cls.servidor = arena.Servidor(("127.0.0.1", 0), arena.Manipulador)
        cls.porta = cls.servidor.server_address[1]
        threading.Thread(target=cls.servidor.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.servidor.shutdown()
        cls.servidor.server_close()

    def setUp(self):
        super().setUp()
        import plataforma
        import ponte_android
        # as pastas de jogos do ARENA ficam na memoria do aparelho (e' onde a pessoa as ve e poe os jogos)
        self.jogos = self.criar("emulated", "0", "ARENA", "jogos")
        for origem in ("livres", "turma", "pessoais"):
            os.makedirs(os.path.join(self.jogos, origem))
        self.antigas = dict(self.arena.indexador.ORIGENS)
        self.trocas = [mock.patch.object(plataforma, "ANDROID", True),
                       mock.patch.object(ponte_android, "SEGREDO", "segredo-da-tela"),
                       mock.patch.object(ponte_android, "RAIZES", self.raizes),
                       mock.patch.object(self.arena, "PASTA_JOGOS", self.jogos),
                       mock.patch.object(self.arena, "PASTA_DADOS", self.dados),
                       mock.patch.object(self.arena, "manifesto", return_value={"total": 7}),
                       mock.patch.object(self.arena, "limpar_caches"),
                       mock.patch.object(armazenamento, "nomes_de_pastas_de_console", return_value=CONSOLES)]
        for troca in self.trocas:
            troca.start()
        self.cartao_com_jogos = self.jogos_no_cartao("Projetos", "arena-console", "jogos", "pessoais")

    def tearDown(self):
        for troca in reversed(self.trocas):
            troca.stop()
        self.arena.indexador.ORIGENS.clear()
        self.arena.indexador.ORIGENS.update(self.antigas)
        super().tearDown()

    def pedir(self, rota, dados=None, cookie="arena_segredo=segredo-da-tela"):
        import urllib.error
        import urllib.request
        pedido = urllib.request.Request("http://127.0.0.1:%d%s" % (self.porta, rota),
                                        data=json.dumps(dados).encode("utf-8") if dados is not None else None,
                                        headers={"Content-Type": "application/json", "Cookie": cookie},
                                        method="POST" if dados is not None else "GET")
        try:
            with urllib.request.urlopen(pedido, timeout=20) as resposta:
                return resposta.status, json.loads(resposta.read() or b"{}")
        except urllib.error.HTTPError as erro:
            return erro.code, json.loads(erro.read() or b"{}")

    def pode_ligar(self):
        try:
            os.symlink(self.memoria, os.path.join(self.pasta, "teste_de_atalho"), target_is_directory=True)
            os.remove(os.path.join(self.pasta, "teste_de_atalho"))
            return True
        except (OSError, NotImplementedError):
            return False

    def test_o_estado_para_a_tela(self):
        estado, resposta = self.pedir("/api/armazenamento")
        self.assertEqual(estado, 200)
        self.assertEqual([v["id"] for v in resposta["volumes"]], ["interno", "cartao-1234-5678"])
        self.assertEqual((resposta["jogar_do_cartao"], resposta["extras"]), ("direto", []))

    def test_procurar_a_pasta_de_jogos_no_cartao(self):
        estado, resposta = self.pedir("/api/armazenamento/procurar", {"volume": "cartao-1234-5678"})
        self.assertEqual(estado, 200)
        self.assertEqual([os.path.realpath(c["caminho"]) for c in resposta["candidatas"]],
                         [os.path.realpath(self.cartao_com_jogos)])
        for ruim in ("", "nao-existe", "../x", None, 5):
            estado, resposta = self.pedir("/api/armazenamento/procurar", {"volume": ruim})
            self.assertEqual(estado, 400, ruim)
            self.assertIn("Escolha um dos volumes", resposta["erro"])

    def test_escolher_a_pasta_passo_a_passo(self):
        estado, resposta = self.pedir("/api/armazenamento/listar", {"volume": "cartao-1234-5678"})
        self.assertEqual(estado, 200)
        self.assertEqual((resposta["pai"], resposta["raiz"] == os.path.realpath(self.cartao)), ("", True))
        self.assertEqual([p["nome"] for p in resposta["pastas"]], ["Projetos"])        # do cartao de mentira
        estado, resposta = self.pedir("/api/armazenamento/listar", {"caminho": self.cartao_com_jogos})
        self.assertEqual((estado, resposta["serve"], resposta["consoles"]), (200, True, 3))
        estado, resposta = self.pedir("/api/armazenamento/listar", {"caminho": self.dados})
        self.assertEqual(estado, 400)
        self.assertIn("memória do aparelho ou no cartão", resposta["erro"])
        estado, resposta = self.pedir("/api/armazenamento/listar", {"volume": "nao-existe"})
        self.assertEqual(estado, 400)

    def test_pondo_e_tirando_o_cartao_da_lista(self):
        if not self.pode_ligar():
            self.skipTest("sem permissao para criar atalho")
        estado, resposta = self.pedir("/api/armazenamento/usar", {"caminho": self.cartao_com_jogos, "nome": "Meu SD"})
        self.assertEqual(estado, 200, resposta)
        self.assertEqual(resposta["total"], 7)
        self.assertEqual(resposta["situacao"], {"cartao-1234-5678": "ligado"})
        self.assertEqual(resposta["extras"][0]["nome"], "Meu SD")
        self.assertEqual(self.arena.indexador.ORIGENS["cartao-1234-5678"], "Meu SD")
        self.assertTrue(os.path.islink(os.path.join(self.jogos, "cartao-1234-5678")))
        estado, resposta = self.pedir("/api/armazenamento/tirar", {"id": "cartao-1234-5678"})
        self.assertEqual(estado, 200)
        self.assertNotIn("cartao-1234-5678", self.arena.indexador.ORIGENS)
        self.assertFalse(os.path.lexists(os.path.join(self.jogos, "cartao-1234-5678")))
        self.assertTrue(os.path.isdir(os.path.join(self.cartao_com_jogos, "PS1")))           # os jogos ficam

    def test_cada_recusa_diz_o_que_fazer(self):
        casos = [({"caminho": self.cartao}, "e não o cartão inteiro"),
                 ({"caminho": os.path.join(self.cartao, "nao_existe")}, "cartão está encaixado"),
                 ({"caminho": os.path.join(self.jogos, "pessoais")}, "Meus jogos"),
                 ({"caminho": ""}, "Escolha uma pasta"), ({}, "Escolha uma pasta")]
        for dados, esperado in casos:
            estado, resposta = self.pedir("/api/armazenamento/usar", dados)
            self.assertEqual(estado, 400, dados)
            self.assertIn(esperado, resposta["erro"], dados)
        estado, resposta = self.pedir("/api/armazenamento/tirar", {"id": "cartao-nao-tem"})
        self.assertEqual(estado, 400)
        self.assertIn("Atualize", resposta["erro"])

    def test_jogar_direto_ou_pelo_interno(self):
        estado, resposta = self.pedir("/api/armazenamento/ajustar", {"jogar_do_cartao": "copiar", "limite_do_cache_mb": 4096})
        self.assertEqual((estado, resposta["jogar_do_cartao"], resposta["limite_do_cache_mb"]), (200, "copiar", 4096))
        estado, resposta = self.pedir("/api/armazenamento/ajustar", {"limite_do_cache_mb": 5})
        self.assertEqual(estado, 400)
        self.assertIn("256 MB", resposta["erro"])

    def test_medir_o_interno_e_o_cartao(self):
        with mock.patch.object(armazenamento, "medir_gravacao_e_leitura",
                               return_value={"gravacao_mb_s": 80.0, "leitura_mb_s": 106.0}) as medir:
            estado, resposta = self.pedir("/api/armazenamento/medir", {"volume": "interno"})
        self.assertEqual((estado, resposta["leitura_mb_s"], resposta["gravacao_mb_s"]), (200, 106.0, 80.0))
        medir.assert_called_once_with(self.dados)           # a pasta do app, no interno
        # o cartao: so le um jogo da pasta que esta na lista; sem a pasta, explica o que fazer
        estado, resposta = self.pedir("/api/armazenamento/medir", {"volume": "cartao-1234-5678"})
        self.assertEqual(estado, 400)
        self.assertIn("Ponha primeiro a pasta de jogos", resposta["erro"])
        armazenamento.adicionar(self.cartao_com_jogos, self.raizes, consoles=CONSOLES)
        estado, resposta = self.pedir("/api/armazenamento/medir", {"volume": "cartao-1234-5678"})
        self.assertEqual(estado, 400)
        self.assertIn("nenhum jogo grande", resposta["erro"])
        jogo = os.path.join(self.cartao_com_jogos, "PS1", "Crash.chd")
        with open(jogo, "wb") as f:
            f.write(os.urandom(2 * 1048576))
        with mock.patch.object(armazenamento, "maior_arquivo", return_value=jogo) as achar:
            estado, resposta = self.pedir("/api/armazenamento/medir", {"volume": "cartao-1234-5678"})
        self.assertEqual(estado, 200)
        self.assertGreater(resposta["leitura_mb_s"], 0)
        self.assertEqual(achar.call_args.kwargs["minimo_mb"], 64)

    def test_so_o_android_e_so_com_o_segredo_da_tela(self):
        import plataforma
        import ponte_android
        for rota, dados in (("/api/armazenamento", None), ("/api/armazenamento/usar", {"caminho": self.cartao}),
                            ("/api/armazenamento/tirar", {"id": "x"}), ("/api/armazenamento/medir", {"volume": "interno"})):
            self.assertEqual(self.pedir(rota, dados, cookie="arena_segredo=chute")[0], 403, rota)
        with mock.patch.object(plataforma, "ANDROID", False), mock.patch.object(ponte_android, "SEGREDO", ""):
            for rota, dados in (("/api/armazenamento", None), ("/api/armazenamento/usar", {"caminho": self.cartao})):
                estado, resposta = self.pedir(rota, dados, cookie="")
                self.assertEqual(estado, 404, rota)
                self.assertIn("ponha os jogos na pasta jogos", resposta["erro"])
        self.assertEqual(self.pedir("/api/armazenamento/coisa-que-nao-existe", {})[0], 404)
        for rota in ("/api/armazenamento", "/api/armazenamento/usar", "/api/armazenamento/tirar",
                     "/api/armazenamento/medir", "/api/armazenamento/procurar", "/api/armazenamento/ajustar"):
            self.assertNotIn(rota, self.arena.ROTAS_REDE_EXTERNA)

    def test_atualizar_a_lista_pega_o_cartao_que_foi_encaixado(self):
        with mock.patch.object(self.arena, "ligar_o_cartao") as ligar:
            self.assertEqual(self.pedir("/api/indexar", {})[0], 200)
        ligar.assert_called_once()

    def test_o_registro_da_ultima_partida(self):
        """So leitura, so no Android: o que o nucleo disse na ultima partida (as ultimas linhas)."""
        estado, resposta = self.pedir("/api/android/registro")
        self.assertEqual((estado, resposta["linhas"], resposta["arquivo"]), (200, [], ""))     # nenhuma partida ainda
        os.makedirs(self.dados, exist_ok=True)
        with open(os.path.join(self.dados, "retroarch__2026_10_24__00_06_14.log"), "w", encoding="utf-8") as f:
            f.write("\n".join("[INFO] linha %d" % n for n in range(1, 501)) + "\n")
        estado, resposta = self.pedir("/api/android/registro?linhas=50")
        self.assertEqual(estado, 200)
        self.assertEqual((resposta["total"], len(resposta["linhas"]), resposta["linhas"][-1]), (500, 50, "[INFO] linha 500"))
        self.assertEqual(len(self.pedir("/api/android/registro?linhas=abc")[1]["linhas"]), 300)   # texto vira o padrao
        self.assertEqual(len(self.pedir("/api/android/registro?linhas=99999")[1]["linhas"]), 500)  # no maximo 2000
        self.assertEqual(self.pedir("/api/android/registro", cookie="")[0], 403)                  # sem o segredo da tela
        import plataforma
        with mock.patch.object(plataforma, "ANDROID", False):
            self.assertEqual(self.pedir("/api/android/registro", cookie="")[0], 404)


class OrigensDoIndexador(Base):

    def setUp(self):
        super().setUp()
        import arena
        import plataforma
        self.arena = arena
        self.jogos = self.criar("app", "jogos")
        self.antigas = dict(arena.indexador.ORIGENS)
        self.trocas = [mock.patch.object(arena, "PASTA_JOGOS", self.jogos),
                       mock.patch.object(plataforma, "ANDROID", True)]
        for troca in self.trocas:
            troca.start()
        self.pasta_do_cartao = self.jogos_no_cartao("jogos")
        self.extra = {"id": "cartao-1234-5678", "nome": "Meu SD", "caminho": self.pasta_do_cartao}

    def tearDown(self):
        for troca in reversed(self.trocas):
            troca.stop()
        self.arena.indexador.ORIGENS.clear()
        self.arena.indexador.ORIGENS.update(self.antigas)
        super().tearDown()

    def com_extras(self, extras):
        return mock.patch.object(armazenamento, "ler", return_value={"jogos_extras": extras, "jogar_do_cartao": "direto",
                                                                      "limite_do_cache_mb": 2048})

    def test_o_cartao_vira_origem_so_enquanto_esta_no_aparelho(self):
        with self.com_extras([self.extra]):
            situacao = self.arena.ligar_o_cartao()
            if situacao.get(self.extra["id"], "").startswith("erro"):
                self.skipTest("sem permissao para criar atalho")
            self.assertEqual(self.arena.indexador.ORIGENS["cartao-1234-5678"], "Meu SD")
            limpeza.apagar_pasta(self.pasta_do_cartao)                    # o cartao saiu
            self.assertEqual(self.arena.ligar_o_cartao(), {"cartao-1234-5678": "ausente"})
            self.assertNotIn("cartao-1234-5678", self.arena.indexador.ORIGENS)
        # as de sempre ficam
        self.assertIn("pessoais", self.arena.indexador.ORIGENS)

    def test_fora_do_android_nenhuma_origem_do_cartao(self):
        import plataforma
        self.arena.indexador.ORIGENS["cartao-velho"] = "sobrou"
        with mock.patch.object(plataforma, "ANDROID", False), self.com_extras([self.extra]):
            self.assertEqual(self.arena.ligar_o_cartao(), {})
        self.assertNotIn("cartao-velho", self.arena.indexador.ORIGENS)

    def test_o_indexador_acha_os_jogos_do_cartao_pelo_atalho(self):
        import indexador
        with self.com_extras([self.extra]):
            if self.arena.ligar_o_cartao().get(self.extra["id"], "").startswith("erro"):
                self.skipTest("sem permissao para criar atalho")
        os.makedirs(os.path.join(self.pasta_do_cartao, "PS1"), exist_ok=True)
        with open(os.path.join(self.pasta_do_cartao, "PS1", "Crash Bandicoot (USA).chd"), "wb") as f:
            f.write(b"MComprHD" + b"\0" * 64)
        por_id, por_extensao = indexador.carregar_plataformas()
        # o indexador conta o caminho a partir da raiz do ARENA: aqui, a pasta "app" de mentira
        with mock.patch.object(indexador, "RAIZ", os.path.dirname(self.jogos)):
            achados = indexador.varrer_pasta(os.path.join(self.jogos, "cartao-1234-5678"), "cartao-1234-5678",
                                             por_extensao, por_id)
        self.assertEqual([(j["titulo"], j["origem"], j["origem_rotulo"]) for j in achados],
                         [("Crash Bandicoot", "cartao-1234-5678", "Meu SD")])
        # o caminho do jogo continua relativo a RAIZ, passando pelo atalho: tudo o que ja funcionava segue
        self.assertEqual(achados[0]["arquivo"].replace("\\", "/").split("/")[0], "jogos")


class Pacote(unittest.TestCase):

    def test_o_modulo_so_usa_a_biblioteca_padrao_e_esta_na_lista_do_pacote(self):
        import ast
        raiz = os.path.dirname(PASTA_SERVIDOR)
        with open(os.path.join(PASTA_SERVIDOR, "armazenamento.py"), encoding="utf-8") as f:
            arvore = ast.parse(f.read())
        usados = set()
        for no in ast.walk(arvore):
            if isinstance(no, ast.Import):
                usados |= {a.name.split(".")[0] for a in no.names}
            elif isinstance(no, ast.ImportFrom) and no.module:
                usados.add(no.module.split(".")[0])
        # ponte_android e' do ARENA (so e' importado dentro da funcao que le as raizes do aparelho)
        self.assertLessEqual(usados - {"ponte_android"}, set(sys.stdlib_module_names))
        with open(os.path.join(PASTA_SERVIDOR, "diagnostico.py"), encoding="utf-8") as f:
            self.assertIn('"servidor/armazenamento.py"', f.read())
        self.assertTrue(os.path.isfile(os.path.join(raiz, "servidor", "armazenamento.py")))


if __name__ == "__main__":
    unittest.main()
