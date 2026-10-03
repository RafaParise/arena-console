# -*- coding: utf-8 -*-
"""Testes do servidor\\bios.py e do bios_catalogo.py: a pasta BIOS do ARENA.

Pedido do Rafael (03/10/2026): uma pasta por console (e por regiao), com o
que vai em cada uma, quantas faltam, e o ARENA pondo a BIOS no lugar certo
sozinho. Cada teste monta um ARENA de mentira numa subpasta do temporario,
com um .info de mentira (as marcas MD5 das BIOS de mentira): nada aqui toca
na pasta de verdade."""

import hashlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
import zipfile

RAIZ_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ_SERVIDOR not in sys.path:
    sys.path.insert(0, RAIZ_SERVIDOR)

import bios  # noqa: E402
import bios_catalogo as catalogo  # noqa: E402

PASTA_INFO_REAL = os.path.join(os.path.dirname(RAIZ_SERVIDOR), "retroarch", "info")


def _md5(dados):
    return hashlib.md5(dados).hexdigest()


# BIOS de mentira, cada uma com o tamanho da de verdade.
SEGACD_E = b"E" * 131072
SEGACD_U = b"U" * 131072
SEGACD_U_OUTRA = b"u" * 131072
PCFX = b"F" * 1048576
COLECO = b"C" * 8192


def ps1_de_mentira(regiao, versao="4.1", data="12/16/97"):
    dados = bytearray(524288)
    texto = ("System ROM Version %s %s %s" % (versao, data, regiao)).encode()
    dados[0x7000:0x7000 + len(texto)] = texto
    return bytes(dados)


def ps2_de_mentira(romver="0160AC20020207"):
    dados = bytearray(4194304)
    dados[0x2000:0x2006] = b"ROMVER"
    dados[0x2700:0x2700 + len(romver)] = romver.encode()
    return bytes(dados)


class ArenaDeMentira(unittest.TestCase):
    """Monta raiz/ARENA com retroarch\\system, jogos\\pessoais e um .info."""

    def setUp(self):
        self.base = tempfile.mkdtemp(prefix="arena_bios_")
        self.raiz = os.path.join(self.base, "ARENA")
        self.sistema = os.path.join(self.raiz, "retroarch", "system")
        os.makedirs(self.sistema)
        os.makedirs(os.path.join(self.raiz, "dados"))
        self.info = os.path.join(self.base, "info")
        os.makedirs(self.info)
        notas = "|".join([
            "(!) bios_CD_E.bin (md5): %s" % _md5(SEGACD_E),
            "(!) bios_CD_U.bin (md5): %s" % _md5(SEGACD_U),
            "(!) pcfx.rom (md5): %s" % _md5(b"pcfx de verdade"),
            "(!) colecovision.rom (md5): %s" % _md5(COLECO),
        ])
        with open(os.path.join(self.info, "nucleo_libretro.info"), "w", encoding="utf-8") as arquivo:
            arquivo.write('display_name = "Nucleo de mentira"\nnotes = "%s"\n' % notas)

    def tearDown(self):
        shutil.rmtree(self.base, ignore_errors=True)

    def organizar(self):
        return bios.organizar(self.raiz, self.info)

    def item(self, feito, id_bios):
        return next(i for i in feito["itens"] if i["id"] == id_bios)

    def gravar(self, caminho, dados):
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, "wb") as arquivo:
            arquivo.write(dados)

    def leia(self, *partes):
        with open(os.path.join(self.raiz, bios.NOME_DA_PASTA, *partes), encoding="utf-8-sig") as arquivo:
            return arquivo.read()


class TestCatalogo(unittest.TestCase):

    def test_ids_e_destinos_unicos(self):
        ids = [e["id"] for e in catalogo.CATALOGO]
        self.assertEqual(len(ids), len(set(ids)))
        destinos = [e["destino"].lower() for e in catalogo.CATALOGO if e.get("destino")]
        self.assertEqual(len(destinos), len(set(destinos)), "duas BIOS com o mesmo destino")

    def test_consoles_existem_no_consoles_json(self):
        conhecidos = bios.consoles()
        for entrada in catalogo.CATALOGO:
            self.assertIn(entrada["console"], conhecidos, entrada["id"])
            self.assertIn(entrada["nivel"], catalogo.NIVEIS, entrada["id"])
            self.assertTrue(entrada["o_que"])

    def test_pastas_validas_no_windows(self):
        for entrada in catalogo.CATALOGO:
            for parte in (entrada["pasta"], entrada.get("sub", "")):
                self.assertFalse(set(parte) & set('<>:"/\\|?*'), parte)

    def test_nomes_sao_os_que_os_nucleos_procuram(self):
        """Cada destino esta numa lista "firmware" de um .info do RetroArch
        (o nome exato que o emulador procura)."""
        if not os.path.isdir(PASTA_INFO_REAL):
            self.skipTest("sem retroarch\\info")
        caminhos = set()
        for nome in os.listdir(PASTA_INFO_REAL):
            if nome.endswith(".info"):
                with open(os.path.join(PASTA_INFO_REAL, nome), encoding="utf-8", errors="replace") as arquivo:
                    for linha in arquivo:
                        if linha.startswith("firmware") and "_path" in linha:
                            caminhos.add(linha.split("=", 1)[1].strip().strip('"').lower())
        for entrada in catalogo.CATALOGO:
            if entrada.get("destino") and not entrada.get("e_pasta"):
                destino = entrada["destino"].lower()
                self.assertTrue(destino in caminhos or ("fbneo/" + destino) in caminhos,
                                "%s: %s nao esta em nenhum .info" % (entrada["id"], destino))

    def test_regiao_e_versao_do_ps1(self):
        dados = ps1_de_mentira("E", "4.1", "12/16/97")
        self.assertEqual(catalogo.regiao_ps1(dados), "E")
        self.assertEqual(catalogo.versao_ps1(dados), "versão 4.1, de 16/12/1997")
        self.assertIsNone(catalogo.regiao_ps1(dados[:-1]))          # tamanho errado

    def test_regiao_e_versao_do_ps2(self):
        dados = ps2_de_mentira("0160EC20011004")
        self.assertEqual(catalogo.regiao_ps2(dados), "E")
        self.assertEqual(catalogo.versao_ps2(dados), "v01.60, de 04/10/2001")   # como o PCSX2 mostra
        self.assertEqual(catalogo.regiao_ps2(ps2_de_mentira("0200HC20040614")), "J")
        self.assertIsNone(catalogo.regiao_ps2(b"\0" * 4194304))


class TestOrganizar(ArenaDeMentira):

    def test_cria_prateleiras_e_resumo(self):
        feito = self.organizar()
        for entrada in catalogo.CATALOGO:
            self.assertTrue(os.path.isfile(os.path.join(bios.prateleira(self.raiz, entrada), bios.ARQUIVO_LEIA)),
                            entrada["id"])
        resumo = self.leia(bios.ARQUIVO_RESUMO)
        self.assertIn("FALTAM", resumo)
        self.assertIn("NÃO PRECISAM DE BIOS", resumo)
        self.assertEqual(feito["resumo"]["precisa"][0], 0)
        # PS1 e PS2 contam uma vez cada (basta uma regiao).
        precisa = {e["console"] if e.get("grupo") == "uma" else e["id"]
                   for e in catalogo.CATALOGO if e["nivel"] == "precisa"}
        self.assertEqual(feito["resumo"]["precisa"][1], len(precisa))

    def test_pacote_zip_dentro_de_zip_em_system(self):
        """O pacote do Rafael: um zip com outro zip dentro, nomes de catalogo."""
        interno = io.BytesIO()
        with zipfile.ZipFile(interno, "w") as z:
            z.writestr("Mega-CD (E) - Model 1 v1.00.bin", SEGACD_E)
            z.writestr("leia-me.txt", "nada")
        with zipfile.ZipFile(os.path.join(self.sistema, "segamegacdbios.zip"), "w") as z:
            z.writestr("Sega Mega CD BIOS.zip", interno.getvalue())
        feito = self.organizar()
        self.assertTrue(os.path.isfile(os.path.join(self.sistema, "bios_CD_E.bin")))
        with open(os.path.join(self.sistema, "bios_CD_E.bin"), "rb") as arquivo:
            self.assertEqual(arquivo.read(), SEGACD_E)
        self.assertEqual(self.item(feito, "segacd-europa")["estado"], "certa")
        # A copia vai para a prateleira, e o LEIA diz que esta ativa.
        self.assertTrue(os.path.isfile(os.path.join(self.raiz, "BIOS", "Sega CD", "Europa", "bios_CD_E.bin")))
        self.assertIn("ATIVA", self.leia("Sega CD", "Europa", bios.ARQUIVO_LEIA))
        self.assertIn("FALTA", self.leia("Sega CD", "Japão", bios.ARQUIVO_LEIA))

    def test_qualquer_nome_na_prateleira(self):
        self.gravar(os.path.join(self.raiz, "BIOS", "ColecoVision", "Coleco BIOS (1982).rom"), COLECO)
        feito = self.organizar()
        self.assertTrue(os.path.isfile(os.path.join(self.sistema, "colecovision.rom")))
        self.assertTrue(self.item(feito, "colecovision")["ativa"])

    def test_pelo_tamanho_so_na_prateleira_certa(self):
        """Marca desconhecida, tamanho certo, prateleira certa: instala como
        "outra versao". Na prateleira errada: nao instala e o LEIA avisa."""
        self.gravar(os.path.join(self.raiz, "BIOS", "PC-FX", "pcfx v1.00.bin"), PCFX)
        self.gravar(os.path.join(self.raiz, "BIOS", "3DO", "nao sei.bin"), b"Z" * 3000)
        feito = self.organizar()
        self.assertTrue(os.path.isfile(os.path.join(self.sistema, "pcfx.rom")))
        self.assertEqual(self.item(feito, "pcfx")["estado"], "outra")
        self.assertIn("outra versão", self.leia("PC-FX", bios.ARQUIVO_LEIA))
        self.assertFalse(os.path.isfile(os.path.join(self.sistema, "panafz10.bin")))
        self.assertIn("NÃO reconheceu", self.leia("3DO", bios.ARQUIVO_LEIA))
        self.assertIn("nao sei.bin", self.leia("3DO", bios.ARQUIVO_LEIA))

    def test_nunca_troca_a_que_ja_esta_a_nao_ser_pela_recomendada(self):
        self.gravar(os.path.join(self.sistema, "bios_CD_U.bin"), SEGACD_U_OUTRA)
        feito = self.organizar()
        self.assertEqual(self.item(feito, "segacd-eua")["estado"], "outra")
        with open(os.path.join(self.sistema, "bios_CD_U.bin"), "rb") as arquivo:
            self.assertEqual(arquivo.read(), SEGACD_U_OUTRA)
        # A recomendada chegou na prateleira: troca, e a antiga vai para o backup.
        self.gravar(os.path.join(self.raiz, "BIOS", "Sega CD", "EUA", "a boa.bin"), SEGACD_U)
        feito = self.organizar()
        with open(os.path.join(self.sistema, "bios_CD_U.bin"), "rb") as arquivo:
            self.assertEqual(arquivo.read(), SEGACD_U)
        self.assertEqual(self.item(feito, "segacd-eua")["estado"], "certa")
        trocadas = os.path.join(self.raiz, "backup", "bios-trocadas")
        guardadas = [os.path.join(atual, n) for atual, _s, nomes in os.walk(trocadas) for n in nomes]
        self.assertEqual(len(guardadas), 1)
        with open(guardadas[0], "rb") as arquivo:
            self.assertEqual(arquivo.read(), SEGACD_U_OUTRA)

    def test_reinstala_e_nao_ressuscita_na_prateleira(self):
        self.gravar(os.path.join(self.sistema, "bios_CD_E.bin"), SEGACD_E)
        self.organizar()
        na_prateleira = os.path.join(self.raiz, "BIOS", "Sega CD", "Europa", "bios_CD_E.bin")
        self.assertTrue(os.path.isfile(na_prateleira))
        # Apagou de retroarch\system: volta, da prateleira.
        os.remove(os.path.join(self.sistema, "bios_CD_E.bin"))
        self.organizar()
        self.assertTrue(os.path.isfile(os.path.join(self.sistema, "bios_CD_E.bin")))
        # Apagou da prateleira: NAO volta (quem tirou quis tirar).
        os.remove(na_prateleira)
        self.organizar()
        self.assertFalse(os.path.isfile(na_prateleira))

    def test_playstation_pelo_conteudo_e_basta_uma_regiao(self):
        self.gravar(os.path.join(self.raiz, "BIOS", "PS1", "Japão", "psx jp.bin"), ps1_de_mentira("J"))
        feito = self.organizar()
        self.assertTrue(os.path.isfile(os.path.join(self.sistema, "scph5500.bin")))
        self.assertTrue(self.item(feito, "ps1-japao")["ativa"])
        self.assertFalse(self.item(feito, "ps1-eua")["ativa"])
        self.assertIn("não faz falta", self.leia("PS1", "EUA", bios.ARQUIVO_LEIA))
        self.assertNotIn("PS1: uma BIOS de qualquer região", self.leia(bios.ARQUIVO_RESUMO))

    def test_ps1_na_prateleira_errada_vai_pela_regiao_de_dentro(self):
        """A regiao vem gravada no arquivo: a europeia na pasta EUA e' europeia."""
        self.gravar(os.path.join(self.raiz, "BIOS", "PS1", "EUA", "bios.bin"), ps1_de_mentira("E"))
        feito = self.organizar()
        self.assertTrue(self.item(feito, "ps1-europa")["ativa"])
        self.assertTrue(os.path.isfile(os.path.join(self.sistema, "scph5502.bin")))

    def test_segunda_vez_nao_grava_nada(self):
        self.gravar(os.path.join(self.raiz, "BIOS", "ColecoVision", "x.rom"), COLECO)
        self.organizar()
        conferidos = os.path.join(self.raiz, "dados", bios.ARQUIVO_CONFERIDOS)
        antes = os.stat(conferidos).st_mtime_ns
        feito = self.organizar()
        self.assertEqual(feito["leias"], 0)
        self.assertEqual(feito["instaladas"], [])
        self.assertEqual(feito["copiadas"], [])
        self.assertEqual(os.stat(conferidos).st_mtime_ns, antes)

    def test_msx_pastas_do_zip_sem_sair_da_pasta(self):
        os.makedirs(os.path.join(self.raiz, "BIOS", "MSX"))
        with zipfile.ZipFile(os.path.join(self.raiz, "BIOS", "MSX", "blueMSX.zip"), "w") as z:
            z.writestr("blueMSX/Machines/MSX/config.ini", "ok")
            z.writestr("blueMSX/Databases/msxromdb.xml", "<db/>")
            z.writestr("blueMSX/Machines/../../fora.txt", "nao")
            z.writestr("blueMSX/Machines/C:/fora2.txt", "nao")
        self.organizar()
        self.assertTrue(os.path.isfile(os.path.join(self.sistema, "Machines", "MSX", "config.ini")))
        self.assertTrue(os.path.isfile(os.path.join(self.sistema, "Databases", "msxromdb.xml")))
        self.assertFalse(os.path.exists(os.path.join(self.raiz, "retroarch", "fora.txt")))
        self.assertFalse(os.path.exists(os.path.join(self.sistema, "fora.txt")))
        espalhados = [n for atual, _s, nomes in os.walk(self.base) for n in nomes if n.startswith("fora")]
        self.assertEqual(espalhados, [])

    def test_bios_deixada_na_pasta_de_jogos(self):
        pasta_ps1 = os.path.join(self.raiz, "jogos", "pessoais", bios.consoles()["ps1"]["pasta"])
        self.gravar(os.path.join(pasta_ps1, "SCPH1001.BIN"), ps1_de_mentira("A"))
        self.gravar(os.path.join(pasta_ps1, "Jogo (Track 1).bin"), b"\0" * 4096)
        self.assertTrue(bios.e_bios_na_pasta_de_jogos(os.path.join(pasta_ps1, "SCPH1001.BIN"), "ps1", self.info))
        self.assertFalse(bios.e_bios_na_pasta_de_jogos(os.path.join(pasta_ps1, "Jogo (Track 1).bin"), "ps1",
                                                       self.info))
        feito = self.organizar()
        self.assertTrue(self.item(feito, "ps1-eua")["ativa"])
        self.assertTrue(os.path.isfile(os.path.join(self.sistema, "scph5501.bin")))

    def test_cartao_de_pc_engine_nao_e_lido_a_toa(self):
        """Um jogo de 256 KB do PC Engine tem o tamanho do System Card: sem
        nome de BIOS, nem e' aberto (ler cada jogo pesaria no Celeron)."""
        self.assertFalse(bios._vale_ler_na_pasta_de_jogos("Bonk's Adventure (USA).pce", "pcengine", 262144))
        self.assertTrue(bios._vale_ler_na_pasta_de_jogos("syscard3.pce", "pcengine", 262144))

    def test_neogeo_tambem_na_pasta_do_arcade(self):
        catalogo_partes = catalogo.PARTES_NEOGEO
        partes = {"000-lo.lo": b"lo", "sfix.sfix": b"sfix", "sm1.sm1": b"sm1"}
        try:
            import zlib
            catalogo.PARTES_NEOGEO = {zlib.crc32(d) for d in partes.values()}
            with zipfile.ZipFile(os.path.join(self.sistema, "neogeo.zip"), "w") as z:
                for nome, dados in partes.items():
                    z.writestr(nome, dados)
            arcade = os.path.join(self.raiz, "jogos", "pessoais", bios.consoles()["arcade"]["pasta"])
            os.makedirs(arcade)
            feito = self.organizar()
            self.assertTrue(os.path.isfile(os.path.join(arcade, "neogeo.zip")))
            self.assertTrue(self.item(feito, "neogeo")["ativa"])
            self.assertTrue(os.path.isfile(os.path.join(self.raiz, "BIOS", "Neo Geo", "neogeo.zip")))
        finally:
            catalogo.PARTES_NEOGEO = catalogo_partes


class TestAvisos(unittest.TestCase):

    def test_aviso_aponta_a_prateleira(self):
        vazia = tempfile.mkdtemp(prefix="arena_bios_aviso_")
        try:
            aviso = bios.aviso_do_jogo("segacd", "Sonic CD (Europe).chd", vazia, "Sega CD")
            self.assertIn("bios_CD_E.bin", aviso)
            self.assertIn("BIOS\\Sega CD\\Europa", aviso)
            self.assertIn("BIOS\\Super Nintendo (Satellaview)",
                          bios.aviso_do_jogo("snes", "BS F-ZERO Grand Prix 2.bs", vazia, "Super Nintendo"))
            self.assertIn("BIOS\\Sega Saturn", bios.falta_para_o_console("saturn", vazia))
        finally:
            shutil.rmtree(vazia, ignore_errors=True)

    def test_prateleira_da_bios_pelo_nome(self):
        self.assertEqual(bios.prateleira_da_bios("mpr-17933.bin"), "BIOS\\Sega Saturn\\EUA e Europa")
        self.assertEqual(bios.prateleira_da_bios("BS-X.bin"), "BIOS\\Super Nintendo (Satellaview)")
        self.assertEqual(bios.prateleira_do_console("snes", ["BS-X.bin"]), "BIOS\\Super Nintendo (Satellaview)")
        self.assertEqual(bios.prateleira_da_bios("nao-existe.bin"), "BIOS")


if __name__ == "__main__":
    unittest.main()
