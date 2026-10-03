# -*- coding: utf-8 -*-
"""Testes do servidor\\arrumar.py: o botao "Arrumar" do cartao do jogo.

Pedido do Rafael (03/10/2026): o ARENA saber como cada jogo deve ser
posicionado -- o exemplo dele foi o Killer Instinct, que precisa do kinst.zip
na pasta Arcade e do kinst.chd numa pasta kinst ao lado. Cada teste monta
uma pasta de jogos de mentira no temporario: nenhum jogo de verdade e'
tocado."""

import os
import shutil
import sys
import tempfile
import unittest
import zipfile

RAIZ_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ_SERVIDOR not in sys.path:
    sys.path.insert(0, RAIZ_SERVIDOR)

import arrumar  # noqa: E402
import indexador  # noqa: E402
import motivo_do_erro  # noqa: E402


class PastaDeJogos(unittest.TestCase):

    def setUp(self):
        self.base = tempfile.mkdtemp(prefix="arena_arrumar_")
        self.raiz = os.path.join(self.base, "ARENA")
        self.jogos = os.path.join(self.raiz, "jogos")
        self.arcade = os.path.join(self.jogos, "pessoais", "Arcade")
        os.makedirs(self.arcade)

    def tearDown(self):
        shutil.rmtree(self.base, ignore_errors=True)

    def criar(self, *partes, dados=b"x"):
        caminho = os.path.join(self.arcade, *partes)
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, "wb") as arquivo:
            arquivo.write(dados)
        return caminho

    def criar_zip(self, *partes, itens=None):
        caminho = os.path.join(self.arcade, *partes)
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with zipfile.ZipFile(caminho, "w") as z:
            for nome, dados in (itens or {"rom.bin": b"rom"}).items():
                z.writestr(nome, dados)
        return caminho

    def aplicar(self, acao, caminho, bios_do_arena=None):
        return arrumar.aplicar(acao, caminho, self.jogos, self.raiz, bios_do_arena)


class TestKillerInstinct(PastaDeJogos):

    def test_zip_dentro_da_pasta_do_disco_sobe(self):
        zipado = self.criar_zip("kinst", "kinst.zip")
        self.criar("kinst", "kinst.chd")
        self.assertEqual(arrumar.zip_na_pasta_do_disco(zipado), os.path.join(self.arcade, "kinst.zip"))
        mensagem, novo = self.aplicar("zip_na_pasta_do_disco", zipado)
        self.assertTrue(os.path.isfile(os.path.join(self.arcade, "kinst.zip")))
        self.assertTrue(os.path.isfile(os.path.join(self.arcade, "kinst", "kinst.chd")))
        self.assertFalse(os.path.exists(zipado))
        self.assertEqual(novo, os.path.join(self.arcade, "kinst.zip"))
        self.assertIn("Pronto", mensagem)
        with self.assertRaises(arrumar.NaoDa):          # ja arrumado
            self.aplicar("zip_na_pasta_do_disco", novo)

    def test_disco_solto_vai_para_a_pasta_do_zip(self):
        zipado = self.criar_zip("kinst.zip")
        self.criar("kinst.chd")
        self.aplicar("disco_solto", zipado)
        self.assertTrue(os.path.isfile(os.path.join(self.arcade, "kinst", "kinst.chd")))
        self.assertFalse(os.path.exists(os.path.join(self.arcade, "kinst.chd")))

    def test_disco_em_pasta_com_outro_nome(self):
        self.criar_zip("kinst.zip")
        disco = self.criar("Killer Instinct", "kinst.chd")
        self.assertIsNotNone(arrumar.conserto_do_disco(disco))
        self.aplicar("disco_em_outra_pasta", disco)
        self.assertTrue(os.path.isfile(os.path.join(self.arcade, "kinst", "kinst.chd")))

    def test_nunca_passa_por_cima(self):
        zipado = self.criar_zip("kinst", "kinst.zip")
        self.criar("kinst", "kinst.chd")
        self.criar_zip("kinst.zip", itens={"outra.bin": b"outra"})       # ja tem um em cima
        with self.assertRaises(arrumar.NaoDa):
            self.aplicar("zip_na_pasta_do_disco", zipado)
        self.assertTrue(os.path.isfile(zipado))                         # nada mudou
        with zipfile.ZipFile(os.path.join(self.arcade, "kinst.zip")) as z:
            self.assertEqual(z.namelist(), ["outra.bin"])

    def test_so_dentro_da_pasta_de_jogos(self):
        fora = os.path.join(self.base, "fora", "kinst", "kinst.zip")
        os.makedirs(os.path.dirname(fora))
        with zipfile.ZipFile(fora, "w") as z:
            z.writestr("rom.bin", b"rom")
        open(os.path.join(self.base, "fora", "kinst", "kinst.chd"), "wb").close()
        with self.assertRaises(arrumar.NaoDa):
            self.aplicar("zip_na_pasta_do_disco", fora)
        self.assertTrue(os.path.isfile(fora))

    def test_pasta_do_disco_que_falta(self):
        zipado = self.criar_zip("sfiii.zip")
        pasta = arrumar.pasta_do_disco(zipado, ["cap-33s-1.chd"], self.jogos)
        self.assertEqual(pasta, os.path.join(self.arcade, "sfiii"))
        with open(os.path.join(pasta, "LEIA.txt"), encoding="utf-8-sig") as arquivo:
            self.assertIn("cap-33s-1.chd", arquivo.read())
        # O zip dentro da pasta de mesmo nome: a pasta e' ela mesma, nao cria outra.
        dentro = self.criar_zip("kinst", "kinst.zip")
        self.assertIsNone(arrumar.pasta_do_disco(dentro, ["kinst.chd"], self.jogos))


class TestNeoGeo(PastaDeJogos):

    def test_bios_com_outro_nome_vira_neogeo_zip(self):
        jogo = self.criar_zip("mslug.zip", itens={"201-p1.p1": b"p", "201-m1.m1": b"m", "201-c1.c1": b"c"})
        self.criar_zip("neogeo.mame.zip")
        self.aplicar("bios_neogeo_nome", jogo)
        self.assertTrue(os.path.isfile(os.path.join(self.arcade, "neogeo.zip")))
        self.assertFalse(os.path.exists(os.path.join(self.arcade, "neogeo.mame.zip")))

    def test_copia_a_bios_do_arena(self):
        jogo = self.criar_zip("Neo Geo", "mslug.zip")
        bios_do_arena = os.path.join(self.raiz, "BIOS", "Neo Geo", "neogeo.zip")
        os.makedirs(os.path.dirname(bios_do_arena))
        with zipfile.ZipFile(bios_do_arena, "w") as z:
            z.writestr("sm1.sm1", b"bios")
        self.aplicar("bios_neogeo", jogo, bios_do_arena)
        self.assertTrue(os.path.isfile(os.path.join(self.arcade, "Neo Geo", "neogeo.zip")))
        self.assertTrue(os.path.isfile(bios_do_arena))                 # copia, nao move


class TestZipComPastaDentro(PastaDeJogos):

    def test_refaz_sem_a_pasta_e_guarda_o_original(self):
        jogo = self.criar_zip("kof2002.zip", itens={"king/265-p1.p1": b"p1", "king/265-m1.m1": b"m1",
                                                    "readme.html": b"oi", "king/../../fora.txt": b"nao"})
        self.assertEqual(arrumar.pasta_dentro_do_zip(jogo), "king")
        mensagem, _novo = self.aplicar("pasta_dentro_do_zip", jogo)
        with zipfile.ZipFile(jogo) as z:
            self.assertEqual(sorted(z.namelist()), ["265-m1.m1", "265-p1.p1"])
            self.assertEqual(z.read("265-p1.p1"), b"p1")
        guardados = os.listdir(os.path.join(self.raiz, "backup", "originais"))
        self.assertEqual(len(guardados), 1)
        self.assertIn("backup", mensagem)


class TestIndexadorMostraOBotao(PastaDeJogos):
    """O cartao recebe o aviso com o botao, e o disco solto nao vira um jogo."""

    def setUp(self):
        super().setUp()
        self.raiz_original = indexador.RAIZ
        indexador.RAIZ = self.raiz
        self.por_id, self.por_extensao = indexador.carregar_plataformas()

    def tearDown(self):
        indexador.RAIZ = self.raiz_original
        super().tearDown()

    def cartoes(self):
        jogos = indexador.varrer_pasta(os.path.join(self.jogos, "pessoais"), "pessoais",
                                       self.por_extensao, self.por_id)
        return {os.path.relpath(os.path.join(self.raiz, j["arquivo"]), self.arcade): j for j in jogos}

    def test_zip_na_pasta_do_disco(self):
        self.criar_zip("kinst", "kinst.zip")
        self.criar("kinst", "kinst.chd")
        cartoes = self.cartoes()
        acoes = [a.get("arrumar", {}).get("acao") for a in cartoes[os.path.join("kinst", "kinst.zip")]["avisos"]]
        self.assertIn("zip_na_pasta_do_disco", acoes)

    def test_disco_solto_nao_e_jogo_e_o_zip_avisa(self):
        self.criar_zip("kinst.zip")
        self.criar("kinst.chd")
        cartoes = self.cartoes()
        self.assertNotIn("kinst.chd", cartoes)
        acoes = [a.get("arrumar", {}).get("acao") for a in cartoes["kinst.zip"]["avisos"]]
        self.assertIn("disco_solto", acoes)

    def test_disco_sozinho_na_pasta_do_console(self):
        self.criar("kinst.chd")
        cartao = self.cartoes()["kinst.chd"]
        texto = " ".join(a["texto"] for a in cartao["avisos"])
        self.assertNotIn("arcade.zip", texto.lower())      # o nome da PASTA do console nao e' romset
        self.assertIn("kinst.zip e a pasta kinst", texto)


def _esperar(tarefa, segundos=20):
    import time
    fim = time.monotonic() + segundos
    while time.monotonic() < fim:
        situacao = arrumar.progresso(tarefa)
        if situacao and situacao["estado"] != "rodando":
            return situacao
        time.sleep(0.05)
    return arrumar.progresso(tarefa)


class TestDescompactar(PastaDeJogos):
    """O jogo de CD baixado em .zip (o emulador nao abre CD de dentro de zip)."""

    def setUp(self):
        super().setUp()
        self.ps1 = os.path.join(self.jogos, "pessoais", "PS1")
        os.makedirs(self.ps1)

    def zip_de_cd(self, nome, itens):
        caminho = os.path.join(self.ps1, nome)
        with zipfile.ZipFile(caminho, "w") as z:
            for item, dados in itens.items():
                z.writestr(item, dados)
        return caminho

    def test_descompacta_numa_pasta_com_o_nome_do_jogo(self):
        jogo = self.zip_de_cd("Crash (USA).zip", {"Crash (USA).cue": b"FILE", "Crash (USA).bin": b"B" * 5000,
                                                  "../../fora.txt": b"nao", "C:/fora2.txt": b"nao"})
        self.assertTrue(arrumar.precisa_descompactar(jogo, "disco"))
        self.assertFalse(arrumar.precisa_descompactar(jogo, "cartucho"))     # cartucho abre de zip
        tarefa, _mensagem = arrumar.iniciar("descompactar", jogo, self.jogos)
        situacao = _esperar(tarefa)
        self.assertEqual(situacao["estado"], "pronto", situacao)
        pasta = os.path.join(self.ps1, "Crash (USA)")
        self.assertEqual(sorted(os.listdir(pasta)), ["Crash (USA).bin", "Crash (USA).cue"])
        self.assertTrue(os.path.isfile(jogo))                                  # o zip fica
        espalhados = [n for atual, _s, nomes in os.walk(self.base) for n in nomes if n.startswith("fora")]
        self.assertEqual(espalhados, [])
        self.assertFalse(arrumar.precisa_descompactar(jogo, "disco"))
        with self.assertRaises(arrumar.NaoDa):
            arrumar.iniciar("descompactar", jogo, self.jogos)

    def test_sem_pasta_dentro_de_pasta(self):
        jogo = self.zip_de_cd("Spyro.zip", {"Spyro (USA)/Spyro (USA).cue": b"FILE",
                                            "Spyro (USA)/Spyro (USA).bin": b"B"})
        _esperar(arrumar.iniciar("descompactar", jogo, self.jogos)[0])
        self.assertTrue(os.path.isfile(os.path.join(self.ps1, "Spyro", "Spyro (USA).cue")))

    def test_sem_espaco_nao_comeca(self):
        jogo = self.zip_de_cd("Grande.zip", {"Grande.cue": b"FILE", "Grande.bin": b"B" * 1000})
        original = shutil.disk_usage
        try:
            shutil.disk_usage = lambda _p: shutil._ntuple_diskusage(10, 9, 1)
            with self.assertRaises(arrumar.NaoDa) as erro:
                arrumar.iniciar("descompactar", jogo, self.jogos)
            self.assertIn("Não cabe", str(erro.exception))
        finally:
            shutil.disk_usage = original
        self.assertFalse(os.path.exists(os.path.join(self.ps1, "Grande")))

    def test_disco_de_fliperama_zipado(self):
        jogo = self.criar_zip("kinst.zip")
        zipado = self.criar_zip("kinst-chd.zip", itens={"kinst/kinst.chd": b"C" * 3000})
        tarefa, _m = arrumar.iniciar("extrair_disco", jogo, self.jogos, disco_zipado=zipado)
        self.assertEqual(_esperar(tarefa)["estado"], "pronto")
        self.assertTrue(os.path.isfile(os.path.join(self.arcade, "kinst", "kinst.chd")))
        self.assertTrue(os.path.isfile(zipado))

    def test_o_cartao_mostra_e_some_depois(self):
        jogo = self.zip_de_cd("Crash (USA).zip", {"Crash (USA).cue": b"FILE", "Crash (USA).bin": b"B"})
        raiz_original = indexador.RAIZ
        indexador.RAIZ = self.raiz
        try:
            por_id, por_extensao = indexador.carregar_plataformas()

            def cartoes():
                lista = indexador.varrer_pasta(os.path.join(self.jogos, "pessoais"), "pessoais", por_extensao, por_id)
                return {os.path.basename(j["arquivo"]): j for j in lista}
            antes = cartoes()
            avisos = antes["Crash (USA).zip"]["avisos"]
            self.assertTrue(any(a.get("descompactar") and a["arrumar"]["acao"] == "descompactar" for a in avisos))
            _esperar(arrumar.iniciar("descompactar", jogo, self.jogos)[0])
            depois = cartoes()
            self.assertNotIn("Crash (USA).zip", depois)          # o jogo agora e' o da pasta
            self.assertIn("Crash (USA).cue", depois)
        finally:
            indexador.RAIZ = raiz_original


class TestMotivoDoDiscoQueFalta(unittest.TestCase):

    def test_mame_sem_o_chd(self):
        texto = ("[libretro ERROR] kinst.chd NOT FOUND (tried in kinst)\n"
                 "Required files are missing, the machine cannot be run.\n"
                 "[ERROR] [Content] Falha ao carregar o conteúdo.\n")
        r = motivo_do_erro.analisar(texto, "C:\\ARENA\\jogos\\pessoais\\Arcade\\kinst.zip", "mame_libretro.dll")
        self.assertEqual(r["discos"], ["kinst.chd"])
        self.assertIn("Arcade\\kinst", r["texto"])
        self.assertNotIn("dentro do kinst.zip", r["texto"])    # o disco nao fica dentro do zip


if __name__ == "__main__":
    unittest.main()
