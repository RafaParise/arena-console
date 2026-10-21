# -*- coding: utf-8 -*-
"""BIOS livres (pedido do Rafael, 12/10/2026: "integrar emuladores sem
precisar baixar BIOS"). O C-BIOS (MSX) vem com o ARENA em
servidor\\bios_livres e so ocupa o lugar vazio: a BIOS de verdade, quando
chega, passa na frente. Aqui: a lista.json confere com os arquivos, a
instalacao so poe o que falta, a livre nao conta como a de verdade e o
aviso do jogo de disquete do MSX. A abertura no nucleo de verdade fica em
testes\\teste_consoles_livres.py."""
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)
import bios  # noqa: E402
import bios_catalogo  # noqa: E402
import como_colocar  # noqa: E402

MAQUINAS_CBIOS = ("MSX - C-BIOS", "MSX2 - C-BIOS", "MSX2+ - C-BIOS")


def _sha(caminho):
    with open(caminho, "rb") as arquivo:
        return hashlib.sha256(arquivo.read()).hexdigest()


class TestBiosLivres(unittest.TestCase):
    def setUp(self):
        self.base = tempfile.mkdtemp(prefix="arena_bios_livres_")
        self.sistema = os.path.join(self.base, "system")
        os.makedirs(self.sistema)

    def tearDown(self):
        shutil.rmtree(self.base, ignore_errors=True)
        bios._cache_livres.clear()

    def gravar(self, relativo, dados=b"x"):
        caminho = os.path.join(self.sistema, *relativo.split("/"))
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, "wb") as arquivo:
            arquivo.write(dados)
        return caminho

    def test_lista_confere_com_os_arquivos(self):
        lista = bios.livres()
        self.assertIn("C-BIOS", lista["projetos"])
        self.assertTrue(lista["arquivos"])
        for item in lista["arquivos"]:
            origem = os.path.join(bios.PASTA_LIVRES, *item["origem"].split("/"))
            self.assertTrue(os.path.isfile(origem), item["origem"])
            self.assertEqual(_sha(origem), item["sha256"], item["origem"])
            self.assertIn(item["projeto"], lista["projetos"])
        # A licenca BSD do C-BIOS pede o aviso de direitos junto.
        self.assertTrue(os.path.isfile(os.path.join(bios.PASTA_LIVRES, "C-BIOS", "doc", "cbios.txt")))
        destinos = {i["destino"] for i in lista["arquivos"]}
        for maquina in MAQUINAS_CBIOS:       # os nomes que o blueMSX procura
            self.assertIn("Machines/%s/config.ini" % maquina, destinos)

    def test_instala_so_o_que_falta(self):
        meu = self.gravar("Machines/MSX2+ - C-BIOS/config.ini", b"o meu config")
        copiados = bios.instalar_livres(self.sistema)
        self.assertGreater(copiados.get("C-BIOS", 0), 0)
        with open(meu, "rb") as arquivo:
            self.assertEqual(arquivo.read(), b"o meu config")      # nunca troca o que ja esta la
        for maquina in MAQUINAS_CBIOS:
            self.assertTrue(os.path.isfile(os.path.join(self.sistema, "Machines", maquina, "cbios.txt")))
        self.assertTrue(os.path.isfile(os.path.join(self.sistema, "Machines", "MSX2+ - C-BIOS",
                                                    "cbios_main_msx2+.rom")))
        self.assertEqual(bios.instalar_livres(self.sistema), {})   # na segunda vez, nada

    def test_caminhos_das_maquinas_com_barra(self):
        """No Linux e no Android, o blueMSX so acha a ROM pelo caminho com "/";
        com "\\", dava a maquina por incompleta (achado de 21/10/2026)."""
        for maquina in MAQUINAS_CBIOS:
            caminho = os.path.join(bios.PASTA_LIVRES, "C-BIOS", "configs", "blueMSX", maquina, "config.ini")
            with open(caminho, "rb") as arquivo:
                texto = arquivo.read().decode("ascii")
            self.assertIn('"Machines/%s/' % maquina, texto)
            self.assertNotIn("\\", texto, maquina)

    def test_troca_so_a_copia_antiga_da_livre(self):
        """O config.ini antigo do C-BIOS (o do pacote, com "\\") continua
        contando como livre e o ARENA o troca pelo novo. O que nao e' copia
        antiga (o config de outra origem) fica: test_instala_so_o_que_falta."""
        mudados = [i for i in bios.livres()["arquivos"] if i.get("sha256_antigos")]
        self.assertEqual({i["destino"] for i in mudados},
                         {"Machines/MSX - C-BIOS/config.ini", "Machines/MSX2+ - C-BIOS/config.ini"})
        destinos = {}
        for item in mudados:
            with open(os.path.join(bios.PASTA_LIVRES, *item["origem"].split("/")), "rb") as arquivo:
                novo = arquivo.read()
            antigo = re.sub(rb'"Machines/[^"]*"', lambda m: m.group().replace(b"/", b"\\"), novo)
            self.assertIn(hashlib.sha256(antigo).hexdigest(), item["sha256_antigos"], item["destino"])
            destinos[item["destino"]] = self.gravar(item["destino"], antigo)
            self.assertTrue(bios.e_livre(destinos[item["destino"]]))
        bios.instalar_livres(self.sistema)
        for item in mudados:
            self.assertEqual(_sha(destinos[item["destino"]]), item["sha256"], item["destino"])
        self.assertEqual(bios.instalar_livres(self.sistema), {})

    def test_arquivo_mexido_na_pasta_do_arena_nao_instala(self):
        copia = os.path.join(self.base, "bios_livres")
        shutil.copytree(bios.PASTA_LIVRES, copia)
        with open(os.path.join(copia, "C-BIOS", "roms", "cbios_music.rom"), "r+b") as arquivo:
            arquivo.write(b"\xff")
        original = bios.PASTA_LIVRES
        bios.PASTA_LIVRES = copia
        bios._cache_livres.clear()
        try:
            bios.instalar_livres(self.sistema)
        finally:
            bios.PASTA_LIVRES = original
            bios._cache_livres.clear()
        self.assertFalse(os.path.exists(os.path.join(self.sistema, "Machines", "MSX2+ - C-BIOS", "cbios_music.rom")))
        self.assertTrue(os.path.exists(os.path.join(self.sistema, "Machines", "MSX2+ - C-BIOS", "cbios_sub.rom")))

    def test_a_livre_nao_conta_como_a_de_verdade(self):
        bios.instalar_livres(self.sistema)
        rom = os.path.join(self.sistema, "Machines", "MSX - C-BIOS", "cbios_main_msx1.rom")
        self.assertTrue(bios.e_livre(rom))
        self.assertFalse(bios.e_livre(self.gravar("outra.rom", b"\0" * 32768)))
        self.assertEqual(bios.estado(self.sistema, "Machines"), "falta")
        # O Machines de verdade (uma maquina a mais, com a BIOS dela) conta.
        self.gravar("Machines/MSX2+/config.ini", b"[Board]\ntype=MSX\n")
        self.assertEqual(bios.estado(self.sistema, "Machines"), "presente")

    def test_msx_abre_cartucho_e_avisa_disquete(self):
        bios.instalar_livres(self.sistema)
        self.assertEqual(bios.falta_para_o_console("msx", self.sistema), "")
        self.assertIsNone(bios.aviso_do_jogo("msx", "Jogo.rom", self.sistema))
        for jogo in ("Jogo.dsk", "Jogo.CAS"):
            aviso = bios.aviso_do_jogo("msx", jogo, self.sistema)
            self.assertIn("C-BIOS", aviso)
            self.assertIn("Machines", aviso)
            self.assertIn("BIOS\\MSX", aviso)
        self.gravar("Machines/MSX2+/config.ini", b"[Board]\ntype=MSX\n")
        self.assertIsNone(bios.aviso_do_jogo("msx", "Jogo.dsk", self.sistema))

    def test_como_colocar_jogos_do_msx(self):
        bios.instalar_livres(self.sistema)
        plataformas = [{"id": "msx", "nome": "MSX", "pasta": "MSX", "extensoes": [".rom", ".dsk", ".cas"]}]
        guia = como_colocar.guia(plataformas, self.sistema, os.path.join(self.base, "jogos"))[0]
        self.assertTrue(guia["bios"]["so_para_alguns"])
        self.assertFalse(guia["bios"]["tem"])            # o C-BIOS nao e' o Machines de verdade
        self.assertIn("C-BIOS", guia["bios"]["texto"])
        self.gravar("Machines/MSX2+/config.ini", b"[Board]\ntype=MSX\n")
        guia = como_colocar.guia(plataformas, self.sistema, os.path.join(self.base, "jogos"))[0]
        self.assertTrue(guia["bios"]["tem"])

    def test_emutos_do_atari_st_nao_e_o_tos_original(self):
        bios.instalar_livres(self.sistema)
        tos = os.path.join(self.sistema, "tos.img")
        self.assertTrue(bios.e_livre(tos))                  # o EmuTOS, instalado como tos.img
        self.assertEqual(bios.estado(self.sistema, "tos.img"), "falta")
        entrada = next(e for e in bios_catalogo.CATALOGO if e["id"] == "atarist-tos")
        self.assertEqual(entrada["nivel"], "melhor")
        self.assertIn("EmuTOS", entrada["sem_ela"])
        self.assertIsNone(bios._instalada(self.sistema, entrada))
        self.assertEqual(bios.falta_para_o_console("atarist", self.sistema), "")
        with open(os.path.join(RAIZ, "consoles.json"), encoding="utf-8") as arquivo:
            plataforma = next(p for p in json.load(arquivo)["plataformas"] if p["id"] == "atarist")
        self.assertEqual(plataforma["core"], "hatari_libretro.dll")
        self.assertIs(plataforma["netplay"], False)       # o Hatari recusa (testado em 14/10/2026)

    def test_catalogo_e_consoles_do_msx(self):
        msx = {e["id"]: e for e in bios_catalogo.CATALOGO if e["console"] == "msx"}
        self.assertEqual(msx["msx-machines"]["nivel"], "alguns")
        self.assertEqual(msx["msx-machines"]["extensoes"], [".dsk", ".cas"])
        self.assertEqual(msx["msx-databases"]["nivel"], "melhor")
        with open(os.path.join(RAIZ, "consoles.json"), encoding="utf-8") as arquivo:
            plataforma = next(p for p in json.load(arquivo)["plataformas"] if p["id"] == "msx")
        self.assertEqual(plataforma["arquivos_sistema"], 0)
        self.assertIs(plataforma["netplay"], False)       # o blueMSX recusa (testado em 14/10/2026)


class TestOrganizarComLivres(unittest.TestCase):
    def setUp(self):
        self.base = tempfile.mkdtemp(prefix="arena_organizar_livres_")
        self.raiz = os.path.join(self.base, "ARENA")
        self.sistema = os.path.join(self.raiz, "retroarch", "system")
        os.makedirs(self.sistema)
        os.makedirs(os.path.join(self.raiz, "dados"))
        self.info = os.path.join(self.base, "info")
        os.makedirs(self.info)

    def tearDown(self):
        shutil.rmtree(self.base, ignore_errors=True)

    def test_organizar_poe_a_livre_e_nao_a_leva_para_a_prateleira(self):
        feito = bios.organizar(self.raiz, self.info)
        livres = [i for i in feito["instaladas"] if i["id"] == "livre-c-bios"]
        self.assertEqual(len(livres), 1)
        self.assertIn("C-BIOS", livres[0]["arquivo"])
        self.assertTrue(os.path.isdir(os.path.join(self.sistema, "Machines", "MSX2+ - C-BIOS")))
        prateleira = os.path.join(self.raiz, bios.NOME_DA_PASTA, "MSX")
        self.assertFalse(any(n.lower().endswith(".rom") for n in os.listdir(prateleira)))
        item = next(i for i in feito["itens"] if i["id"] == "msx-machines")
        self.assertFalse(item["ativa"])
        segunda = bios.organizar(self.raiz, self.info)
        self.assertFalse([i for i in segunda["instaladas"] if i["id"].startswith("livre-")])

    def test_o_tos_de_verdade_entra_no_lugar_do_emutos(self):
        bios.organizar(self.raiz, self.info)
        tos = os.path.join(self.sistema, "tos.img")
        self.assertTrue(bios.e_livre(tos))
        prateleira = os.path.join(self.raiz, bios.NOME_DA_PASTA, "Atari ST")
        self.assertFalse(os.path.exists(os.path.join(prateleira, "tos.img")))    # o EmuTOS nao vai para la
        with open(os.path.join(prateleira, "TOS 1.04 (Europe).img"), "wb") as arquivo:
            arquivo.write((b"\x60\x2e" + b"TOS de verdade" * 14100)[:196608])     # o tamanho do TOS 1.x
        feito = bios.organizar(self.raiz, self.info)
        self.assertIn("atarist-tos", [i["id"] for i in feito["instaladas"]])
        self.assertFalse(bios.e_livre(tos))
        item = next(i for i in feito["itens"] if i["id"] == "atarist-tos")
        self.assertTrue(item["ativa"])


if __name__ == "__main__":
    unittest.main()
