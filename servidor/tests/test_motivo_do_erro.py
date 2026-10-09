# -*- coding: utf-8 -*-
"""Testes do servidor\\motivo_do_erro.py: por que o jogo nao abriu, lido do
registro do RetroArch. Achado de 02/10/2026: o KOF 2002 nao abria (zip de
outro emulador + BIOS com o nome neogeo.mame.zip) e o ARENA nao dizia nada.
Os registros abaixo sao trechos do registro DE VERDADE daquela tentativa."""

import os
import shutil
import sys
import tempfile
import time
import unittest
import zipfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

import motivo_do_erro  # noqa: E402

MAME_KOF2002 = """\
[libretro INFO] MAME 0.289 (4fc9a931)
[libretro INFO] Starting game: "C:\\ARENA\\jogos\\pessoais\\Arcade\\kof2002.zip"
[libretro INFO] Game name: kof2002
[libretro ERROR] 265-p2.sp2 NOT FOUND (tried in kof2002 neogeo)\r
000-lo.lo NOT FOUND (tried in kof2002 neogeo)\r
sfix.sfix NOT FOUND (tried in kof2002 neogeo)\r
sp-s2.sp1 NOT FOUND (tried in kof2002 neogeo)\r
sm1.sm1 NOT FOUND (tried in kof2002 neogeo)\r
265-m1.m1 NOT FOUND (tried in kof2002 neogeo)\r
265-v1.v1 NOT FOUND (tried in kof2002 neogeo)\r
265-v2.v2 NOT FOUND (tried in kof2002 neogeo)\r
265-c1.c1 NOT FOUND (tried in kof2002 neogeo)\r
265-c2.c2 NOT FOUND (tried in kof2002 neogeo)\r
265-c3.c3 NOT FOUND (tried in kof2002 neogeo)\r
265-c4.c4 NOT FOUND (tried in kof2002 neogeo)\r
265-c5.c5 NOT FOUND (tried in kof2002 neogeo)\r
265-c6.c6 NOT FOUND (tried in kof2002 neogeo)\r
265-c7.c7 NOT FOUND (tried in kof2002 neogeo)\r
265-c8.c8 NOT FOUND (tried in kof2002 neogeo)\r
[libretro ERROR] Fatal error: Required files are missing, the machine cannot be run.
[ERROR] [Content] Falha ao carregar o conteúdo.
"""

FBNEO_KOF2002 = """\
[libretro INFO] [FBNeo] Using ROM with known crc 0x5a86cff2 and name 000-lo.lo from archive neogeo
[libretro ERROR] [FBNeo] ROM at index 1 with name 265-p2.sp2 and CRC 0x327266b8 is required
[libretro ERROR] [FBNeo] ROM at index 2 with name 265-c1.c1 and CRC 0x2b65a656 is required
[libretro ERROR] [FBNeo] ROM at index 10 with name 265-m1.m1 and CRC 0x85aaa632 is required
[INFO] [Runtime] Content ran for a total of: 00 hours, 00 minutes, 14 seconds.
"""

ABRIU = """\
[libretro INFO] [FBNeo] Running v1.0.0.03
[INFO] [Runtime] Content ran for a total of: 00 hours, 05 minutes, 03 seconds.
"""


def zip_com(caminho, nomes):
    with zipfile.ZipFile(caminho, "w") as z:
        for nome in nomes:
            z.writestr(nome, b"x" * 64)


class TestMotivoDoErro(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="arena_motivo_")
        self.jogo = os.path.join(self.dir, "kof2002.zip")
        zip_com(self.jogo, ["kof2k2_c%d.rom" % n for n in range(1, 9)]
                + ["kof2K2_M1.ROM", "kof2k2_p1.rom", "kof2k2_p2.rom", "kof2k2_s1.rom",
                   "kof2K2_V1.ROM", "kof2K2_V2.ROM", "readme.html"])

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def bios(self, nome):
        zip_com(os.path.join(self.dir, nome), ["000-lo.lo", "sfix.sfix", "sm1.sm1", "sp-s2.sp1"])

    def test_kof2002_do_rafael_bios_com_nome_errado_e_zip_de_outro_emulador(self):
        self.bios("neogeo.mame.zip")
        r = motivo_do_erro.analisar(MAME_KOF2002, self.jogo, "mame_libretro.dll")
        self.assertEqual(r["renomear"], ("neogeo.mame.zip", "neogeo.zip"))
        self.assertTrue(r["texto"].startswith("MAME não abriu este jogo."))
        self.assertIn("renomeie neogeo.mame.zip para neogeo.zip", r["texto"])
        self.assertIn("Faltam 12 arquivos do jogo dentro do kof2002.zip", r["texto"])
        self.assertIn("265-p2.sp2, 265-m1.m1, 265-v1.v1 e mais 9", r["texto"])
        self.assertIn("outra versão ou feito para outro emulador", r["texto"])
        self.assertIn("kof2k2_c1.rom", r["texto"])
        self.assertNotIn("readme", r["texto"])           # leia-me do zip nao e' parte do jogo
        self.assertEqual(len(r["faltando"]), 16)

    def test_sem_bios_nenhuma_na_pasta(self):
        r = motivo_do_erro.analisar(MAME_KOF2002, self.jogo, "mame_libretro.dll")
        self.assertIsNone(r["renomear"])
        # Os 4 da BIOS nao contam como "do jogo" (separados pelo nome).
        self.assertIn("Falta a BIOS neogeo.zip: ela vai na mesma pasta do jogo", r["texto"])
        self.assertIn("Faltam 12 arquivos do jogo", r["texto"])

    def test_bios_certa_mas_de_outra_versao(self):
        zip_com(os.path.join(self.dir, "neogeo.zip"), ["000-lo.lo", "sfix.sfix", "sm1.sm1", "sp-s2.sp1"])
        r = motivo_do_erro.analisar(MAME_KOF2002, self.jogo, "mame_libretro.dll")
        self.assertIsNone(r["renomear"])                 # o nome ja esta certo
        self.assertIn("A BIOS neogeo.zip desta pasta é de outra versão (o emulador não achou nela:", r["texto"])
        self.assertIn("Faltam 12 arquivos do jogo", r["texto"])

    def test_fbneo_diz_o_que_falta(self):
        r = motivo_do_erro.analisar(FBNEO_KOF2002, self.jogo, "fbneo_libretro.dll")
        self.assertTrue(r["texto"].startswith("FBNeo não abriu este jogo."))
        self.assertIn("Faltam 3 arquivos do jogo", r["texto"])

    def test_fbneo_sem_o_jogo(self):
        r = motivo_do_erro.analisar("[libretro ERROR] [FBNeo] Romset is unknown\n",
                                    os.path.join(self.dir, "kinst.zip"), "fbneo_libretro.dll")
        self.assertIn("não conhece este jogo (kinst.zip)", r["texto"])
        self.assertIn("pasta Arcade (MAME)", r["texto"])

    def test_jogo_que_abriu_nao_tem_motivo(self):
        self.assertIsNone(motivo_do_erro.analisar(ABRIU, self.jogo, "fbneo_libretro.dll"))
        self.assertIsNone(motivo_do_erro.analisar("", self.jogo, "fbneo_libretro.dll"))
        # MAME com arquivo de conteudo diferente, mas rodando: nao e' "nao abriu".
        self.assertIsNone(motivo_do_erro.analisar(
            "x.p1 WRONG CHECKSUMS:\nWARNING: the machine might not run correctly.\n",
            self.jogo, "mame_libretro.dll"))

    def test_falha_generica_conta_o_que_o_emulador_disse(self):
        r = motivo_do_erro.analisar(
            "[libretro ERROR] [Core] Unsupported ROM format\n[ERROR] [Content] Falha ao carregar o conteúdo.\n",
            os.path.join(self.dir, "jogo.sfc"), "snes9x_libretro.dll")
        # 03/10/2026: "<emulador> nao abriu este jogo. O arquivo pode estar..."
        # (antes repetia o nome do emulador nas duas frases).
        self.assertTrue(r["texto"].startswith("O emulador do Super Nintendo não abriu este jogo. O arquivo pode "
                                              "estar danificado"), r["texto"])
        self.assertIn("Unsupported ROM format", r["texto"])

    def test_registro_da_partida_e_o_mais_novo_depois_de_abrir(self):
        dados = os.path.join(self.dir, "dados")
        os.makedirs(dados)
        self.assertIsNone(motivo_do_erro.registro_da_partida(dados, time.time()))
        velho = os.path.join(dados, "retroarch__2026_10_02__16_45_26.log")
        open(velho, "w").close()
        self.assertEqual(motivo_do_erro.registro_da_partida(dados, time.time() - 60), velho)
        # Registro de antes de abrir este jogo nao serve.
        self.assertIsNone(motivo_do_erro.registro_da_partida(dados, time.time() + 60))
        time.sleep(0.05)
        novo = os.path.join(dados, "retroarch__2026_10_02__16_50_30.log")
        open(novo, "w").close()
        open(os.path.join(dados, "outro.log"), "w").close()
        self.assertEqual(motivo_do_erro.registro_da_partida(dados, time.time() - 60), novo)


class TestMotivoDaBios(unittest.TestCase):
    """03/10/2026: as linhas que cada emulador escreveu de verdade quando
    faltava a BIOS (antes de as BIOS do Rafael irem para o lugar)."""

    FALHOU = "[ERROR] [Content] Falha ao carregar o conteúdo.\n"

    def test_sega_cd(self):
        texto = ('[libretro ERROR] Unable to open CD BIOS: "C:\\Projetos\\ARENA\\retroarch\\system\\bios_CD_E.bin".\n'
                 + self.FALHOU)
        r = motivo_do_erro.analisar(texto, "C:\\jogos\\Sonic CD (Europe).chd", "genesis_plus_gx_libretro.dll")
        self.assertIn("falta a BIOS bios_CD_E.bin (a do Sega CD da Europa).", r["texto"])
        # Onde por: a prateleira dela na pasta BIOS do ARENA (servidor\bios.py).
        self.assertIn("pasta BIOS\\Sega CD\\Europa", r["texto"])
        self.assertIn(".zip em que ele veio", r["texto"])

    def test_saturn(self):
        texto = ('[libretro ERROR] Cannot open BIOS file "C:\\Projetos\\ARENA\\retroarch\\system\\mpr-17933.bin".\n'
                 + self.FALHOU)
        r = motivo_do_erro.analisar(texto, "C:\\jogos\\Saturn Bomberman (USA) (1S).cue", "mednafen_saturn_libretro.dll")
        self.assertTrue(r["texto"].startswith("O emulador do Saturn não abriu este jogo: falta a BIOS mpr-17933.bin"))
        self.assertIn("(a do Saturn dos EUA e da Europa)", r["texto"])
        self.assertIn("pasta BIOS\\Sega Saturn\\EUA e Europa", r["texto"])

    def test_naomi_no_flycast(self):
        texto = "[libretro ERROR] [BOOT] Erro: Não foi possível carregar a Bios da naomi.zip\n" + self.FALHOU
        r = motivo_do_erro.analisar(texto, "C:\\jogos\\jogo.zip", "flycast_libretro.dll")
        self.assertIn("naomi.zip, dentro da pasta retroarch\\system\\dc", r["texto"])

    def test_satellaview(self):
        texto = "[libretro ERROR] ROM loading failed...\n" + self.FALHOU
        r = motivo_do_erro.analisar(texto, "C:\\jogos\\BS F-ZERO (J).smc", "snes9x_libretro.dll")
        self.assertIn("Satellaview", r["texto"])
        self.assertIn("BS-X.bin", r["texto"])
        self.assertIn("pasta BIOS\\Super Nintendo (Satellaview)", r["texto"])
        # Jogo comum que nao abriu: nao fala de BIOS.
        r = motivo_do_erro.analisar(texto, "C:\\jogos\\Contra (USA).sfc", "snes9x_libretro.dll")
        self.assertNotIn("BS-X", r["texto"])


class TestServidorGuardaOMotivo(unittest.TestCase):
    """O arena.py guarda o motivo depois do jogo, o cartao mostra, e some
    quando o jogo abre ou quando o arquivo e' trocado."""

    def setUp(self):
        import arena
        self.arena = arena
        self.dir = tempfile.mkdtemp(prefix="arena_motivo_servidor_")
        self.antigos = (arena.PASTA_DADOS, arena.ARQUIVO_PROBLEMAS, arena.RAIZ)
        arena.PASTA_DADOS = os.path.join(self.dir, "dados")
        arena.ARQUIVO_PROBLEMAS = os.path.join(arena.PASTA_DADOS, "problemas_dos_jogos.json")
        arena.RAIZ = self.dir
        os.makedirs(arena.PASTA_DADOS)
        pasta = os.path.join(self.dir, "jogos", "pessoais", "Arcade")
        os.makedirs(pasta)
        zip_com(os.path.join(pasta, "kof2002.zip"), ["kof2k2_c1.rom", "kof2K2_M1.ROM", "kof2k2_p1.rom"])
        zip_com(os.path.join(pasta, "neogeo.mame.zip"), ["000-lo.lo", "sfix.sfix", "sm1.sm1", "sp-s2.sp1"])
        self.jogo = {"id": "kof", "titulo": "The King of Fighters 2002", "core": "mame_libretro.dll",
                     "arquivo": os.path.join("jogos", "pessoais", "Arcade", "kof2002.zip")}

    def tearDown(self):
        self.arena.PASTA_DADOS, self.arena.ARQUIVO_PROBLEMAS, self.arena.RAIZ = self.antigos
        self.arena.ULTIMO_PROBLEMA.clear()
        shutil.rmtree(self.dir, ignore_errors=True)

    def registro(self, texto):
        nome = "retroarch__%s.log" % time.strftime("%Y_%m_%d__%H_%M_%S")
        with open(os.path.join(self.arena.PASTA_DADOS, nome), "w", encoding="utf-8") as f:
            f.write(texto)

    def test_guarda_mostra_e_apaga(self):
        desde = time.time()
        self.registro(MAME_KOF2002)
        self.assertIsNotNone(self.arena.anotar_motivo_do_erro(self.jogo, desde))
        self.assertEqual(self.arena.ULTIMO_PROBLEMA["jogo_id"], "kof")
        self.assertIn("renomeie neogeo.mame.zip", self.arena.ULTIMO_PROBLEMA["texto"])
        guardado = self.arena.ler_problemas()["kof"]
        self.assertEqual(guardado["assinatura"], self.arena.assinatura_do_arquivo(
            os.path.join(self.dir, self.jogo["arquivo"])))
        # Abriu da proxima vez: o motivo antigo sai.
        time.sleep(1.1)
        desde = time.time()
        self.registro(ABRIU)
        self.arena.anotar_motivo_do_erro(self.jogo, desde)
        self.assertNotIn("kof", self.arena.ler_problemas())

    def test_arquivo_torto_nao_derruba(self):
        with open(self.arena.ARQUIVO_PROBLEMAS, "w", encoding="utf-8") as f:
            f.write("[1, 2")
        self.assertEqual(self.arena.ler_problemas(), {})
        with open(self.arena.ARQUIVO_PROBLEMAS, "w", encoding="utf-8") as f:
            f.write('{"a": 1, "b": {"texto": "ok"}}')
        self.assertEqual(list(self.arena.ler_problemas()), ["b"])
        # Sem registro nenhum: nada a dizer, nada gravado.
        self.assertIsNone(self.arena.anotar_motivo_do_erro(self.jogo, time.time() + 60))


class TestAvisoDaBiosNoCartao(unittest.TestCase):
    """Antes de abrir: a lista ja avisa a BIOS do Neo Geo com o nome que o
    emulador nao procura (o neogeo.mame.zip da pasta Arcade do Rafael)."""

    def setUp(self):
        import indexador
        import jogadores
        self.indexador, self.jogadores = indexador, jogadores
        self.dir = tempfile.mkdtemp(prefix="arena_bios_cartao_")
        self.antigos = (indexador.PASTA_JOGOS, indexador.PASTA_DADOS, indexador.ARQUIVO_MANIFESTO,
                        jogadores.ARQUIVO)
        indexador.PASTA_JOGOS = os.path.join(self.dir, "jogos")
        indexador.PASTA_DADOS = os.path.join(self.dir, "dados")
        indexador.ARQUIVO_MANIFESTO = os.path.join(self.dir, "dados", "manifesto.json")
        jogadores.ARQUIVO = os.path.join(self.dir, "NAO_DEVIA_EXISTIR.txt")
        self.arcade = os.path.join(indexador.PASTA_JOGOS, "pessoais", "Arcade")
        os.makedirs(self.arcade)
        zip_com(os.path.join(self.arcade, "kof2002.zip"), ["kof2k2_c1.rom", "kof2K2_M1.ROM", "kof2k2_p1.rom"])
        zip_com(os.path.join(self.arcade, "kinst.zip"), ["ki-l15d.u98", "u10-l1"])
        zip_com(os.path.join(self.arcade, "neogeo.mame.zip"), ["000-lo.lo", "sfix.sfix"])

    def tearDown(self):
        (self.indexador.PASTA_JOGOS, self.indexador.PASTA_DADOS, self.indexador.ARQUIVO_MANIFESTO,
         self.jogadores.ARQUIVO) = self.antigos
        shutil.rmtree(self.dir, ignore_errors=True)

    def avisos(self):
        manifesto = self.indexador.indexar(forcar=True)
        return {os.path.basename(j["arquivo"]): " ".join(a["texto"] for a in j.get("avisos") or [])
                for j in manifesto["jogos"]}

    def test_bios_com_nome_errado_so_no_jogo_de_neo_geo(self):
        avisos = self.avisos()
        self.assertNotIn("neogeo.mame.zip", avisos)       # a BIOS nao vira jogo
        self.assertIn("está como neogeo.mame.zip", avisos["kof2002.zip"])
        self.assertIn("Renomeie para neogeo.zip", avisos["kof2002.zip"])
        self.assertNotIn("neogeo", avisos["kinst.zip"])   # Killer Instinct nao e' Neo Geo

    def test_com_o_nome_certo_o_aviso_some(self):
        os.replace(os.path.join(self.arcade, "neogeo.mame.zip"), os.path.join(self.arcade, "neogeo.zip"))
        self.assertNotIn("neogeo", self.avisos()["kof2002.zip"].lower())

    def test_sem_bios_nenhuma_o_mame_avisa(self):
        os.remove(os.path.join(self.arcade, "neogeo.mame.zip"))
        self.assertIn("o MAME precisa da BIOS neogeo.zip na mesma pasta", self.avisos()["kof2002.zip"])


# Trecho do registro DE VERDADE do sexto jogador tentando entrar numa partida
# de 5 (testes\teste_netplay_sexto_jogador.py, 08/10/2026).
SEXTO_JOGADOR = """\
[INFO] [Playlist] Written to file: "C:\\Temp\\sexto\\builtin\\content_history.lpl".
[ERROR] [Netplay] Falha ao conectar ao host.
[INFO] [Netplay] Desconectado da Netplay
"""


class TestMotivoDaPartida(unittest.TestCase):
    """Jogar Junto: quem nao conseguiu entrar ve o porque (auditoria 3)."""

    def test_partida_cheia_ou_rede(self):
        frase = motivo_do_erro.motivo_da_partida(SEXTO_JOGADOR, 5)
        self.assertIn("Não deu para entrar na partida", frase)
        self.assertIn("até 5 jogadores", frase)
        self.assertIn("PARTIDA.bat", frase)

    def test_em_ingles_tambem(self):
        self.assertTrue(motivo_do_erro.motivo_da_partida("[ERROR] [Netplay] Failed to connect to host.", 2))

    def test_sem_falha_nao_diz_nada(self):
        self.assertIsNone(motivo_do_erro.motivo_da_partida(
            "[INFO] [Netplay] Jogador2 se juntou como o jogador 2 (ping: 16 ms)", 2))


if __name__ == "__main__":
    unittest.main()
