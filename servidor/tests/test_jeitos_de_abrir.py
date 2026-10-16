# -*- coding: utf-8 -*-
"""Os jeitos de abrir um console (servidor\\jeitos_de_abrir.py): o emulador
de fora, o original (a BIOS de verdade) e o livre (o que vem no ARENA).
Pedido do Rafael (15/10/2026): com mais de um, o ARENA pergunta qual usar.
A abertura de verdade, pela rota /api/jogar, esta em
testes\\teste_jeitos_pelo_arena.py."""
import json
import os
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(os.path.dirname(RAIZ), "testes"))
import jeitos_de_abrir as j  # noqa: E402
import limpeza  # noqa: E402  (apaga a pasta mesmo com arquivo somente leitura)


class TestJeitos(unittest.TestCase):
    def setUp(self):
        self.base = tempfile.mkdtemp(prefix="arena_jeitos_")
        self.cores = os.path.join(self.base, "cores")
        self.sistema = os.path.join(self.base, "system")
        os.makedirs(self.cores)
        os.makedirs(self.sistema)
        self.tem_a_bios = j.bios.tem_a_bios
        self.com_bios = set()
        j.bios.tem_a_bios = lambda plataforma, pasta: plataforma in self.com_bios

    def tearDown(self):
        j.bios.tem_a_bios = self.tem_a_bios
        limpeza.apagar_pasta(self.base)

    def nucleo(self, nome):
        open(os.path.join(self.cores, nome), "wb").close()

    def ids(self, plataforma, externo=None):
        return [x["id"] for x in j.jeitos(plataforma, self.cores, self.sistema, externo)]

    def test_ps1_original_e_livre(self):
        ps1 = {"id": "ps1", "core": "swanstation_libretro.dll", "arquivos_sistema": 1,
               "livre": {"nome": "BIOS livre (OpenBIOS)", "pasta": "OpenBIOS", "bios": "openbios.bin",
                         "explica": "x"}}
        self.nucleo("swanstation_libretro.dll")
        self.assertEqual(self.ids(ps1), [])                      # nem a BIOS da Sony, nem a livre
        open(os.path.join(self.sistema, "openbios.bin"), "wb").close()
        self.assertEqual(self.ids(ps1), [])                      # solta na system nao conta: ela mora na pasta dela
        os.makedirs(os.path.join(self.sistema, "OpenBIOS"))
        open(os.path.join(self.sistema, "OpenBIOS", "openbios.bin"), "wb").close()
        self.assertEqual(self.ids(ps1), ["livre"])               # so a livre: abre por ela, sem perguntar
        self.com_bios.add("ps1")
        self.assertEqual(self.ids(ps1), ["original", "livre"])   # as duas: a tela pergunta
        jeito = j.jeitos(ps1, self.cores, self.sistema)[0]
        self.assertEqual(jeito["titulo"], "BIOS original")
        self.assertEqual(jeito["selo"], "mais fiel")

    def test_pasta_do_livre(self):
        """O nucleo recebe a pasta da BIOS livre como a pasta das BIOS so
        quando ela mora numa pasta dela; solta na system, nenhuma troca."""
        self.assertEqual(j.pasta_do_livre({"livre": {"pasta": "OpenBIOS", "bios": "openbios.bin"}}, self.sistema),
                         os.path.join(self.sistema, "OpenBIOS"))
        self.assertIsNone(j.pasta_do_livre({"livre": {"bios": "tos.img"}}, self.sistema))
        self.assertIsNone(j.pasta_do_livre({}, self.sistema))

    def test_livre_com_outro_nucleo(self):
        ps2 = {"id": "ps2", "core": "pcsx2_libretro.dll", "arquivos_sistema": 1,
               "externo": {"nome": "PCSX2", "obrigatorio": True},
               "livre": {"nome": "Play! (BIOS imitada)", "core": "play_libretro.dll"}}
        self.nucleo("pcsx2_libretro.dll")
        self.com_bios.add("ps2")
        # O nucleo de PS2 do RetroArch nao entra: o PCSX2 e' obrigatorio.
        self.assertEqual(self.ids(ps2, "PCSX2"), ["externo"])
        self.nucleo("play_libretro.dll")
        self.assertEqual(self.ids(ps2, "PCSX2"), ["externo", "livre"])

    def test_emulador_de_fora_ou_nucleo(self):
        gc = {"id": "gamecube", "core": "dolphin_libretro.dll", "arquivos_sistema": 0,
              "apoio_do_nucleo": "dolphin-emu/Sys",
              "externo": {"nome": "Dolphin", "obrigatorio": False}}
        self.nucleo("dolphin_libretro.dll")
        self.com_bios.add("gamecube")                            # nao precisa de BIOS
        # Sem a pasta de apoio do nucleo (dolphin-emu\Sys), so o Dolphin de fora.
        self.assertEqual(self.ids(gc, "Dolphin"), ["externo"])
        os.makedirs(os.path.join(self.sistema, "dolphin-emu", "Sys"))
        self.assertEqual(self.ids(gc, "Dolphin"), ["externo", "original"])
        self.assertEqual(self.ids(gc), ["original"])             # sem o Dolphin na pasta
        dentro = j.jeitos(gc, self.cores, self.sistema)[0]
        self.assertEqual(dentro["titulo"], "Dentro do RetroArch")

    def test_escolher(self):
        dois = [{"id": "original"}, {"id": "livre"}]
        self.assertIsNone(j.escolher(dois))                      # perguntar
        self.assertEqual(j.escolher(dois, lembrado="livre"), "livre")
        self.assertEqual(j.escolher(dois, "original", "livre"), "original")   # o pedido agora vence
        self.assertIsNone(j.escolher(dois, "externo"))           # pediu um que nao existe aqui
        self.assertEqual(j.escolher([{"id": "livre"}], lembrado="original"), "livre")
        self.assertIsNone(j.escolher([]))
        self.assertEqual(j.JEITOS, ("externo", "original", "livre"))


class TestFichasDeVerdade(unittest.TestCase):
    """O consoles.json e a lista das BIOS livres de verdade combinam."""

    def test_a_bios_livre_de_cada_console_vem_no_arena(self):
        """Cada consoles.json -> livre.bios e' um arquivo que o ARENA instala
        (um destino da servidor\\bios_livres\\lista.json): o jeito livre nao
        pode pedir um arquivo que nao vem no pacote."""
        with open(os.path.join(RAIZ, "consoles.json"), encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
        lista = dados["plataformas"] if isinstance(dados, dict) else dados
        destinos = {item["destino"] for item in j.bios.livres()["arquivos"]}
        com_livre = [p for p in lista if p.get("livre")]
        self.assertIn("ps1", [p["id"] for p in com_livre])
        for plataforma in com_livre:
            livre = plataforma["livre"]
            for chave in ("nome", "explica"):
                self.assertTrue(livre.get(chave), (plataforma["id"], chave))
            if livre.get("bios"):
                caminho = "/".join(p for p in (livre.get("pasta"), livre["bios"]) if p)
                self.assertIn(caminho, destinos, plataforma["id"])

    def test_a_openbios_nao_passa_pela_bios_da_sony(self):
        """A OpenBIOS e' livre (marca da lista) e nao e' tomada pela BIOS da
        Sony: com ela sozinha, o jeito original nao aparece."""
        caminho = os.path.join(RAIZ, "bios_livres", "OpenBIOS", "openbios.bin")
        self.assertTrue(j.bios.e_livre(caminho))
        self.assertIsNone(j.bios.playstation(caminho))


class TestPS1NoJeitoLivre(unittest.TestCase):
    """O que muda no PS1 quando ele abre pelo jeito livre (o SwanStation com
    a OpenBIOS): o cartao de memoria e o cache de video."""

    def setUp(self):
        import graficos
        self.graficos = graficos
        self.base = tempfile.mkdtemp(prefix="arena_jeito_ps1_")
        self.saves = os.path.join(self.base, "saves")
        self.jogo = os.path.join(self.base, "jogos", "Crash Bandicoot (USA).chd")

    def tearDown(self):
        limpeza.apagar_pasta(self.base)

    def cartao(self, nucleo, conteudo, tamanho=131072):
        pasta = os.path.join(self.saves, nucleo)
        os.makedirs(pasta, exist_ok=True)
        with open(os.path.join(pasta, "Crash Bandicoot (USA).srm"), "wb") as arquivo:
            arquivo.write((conteudo * tamanho)[:tamanho])

    def ler(self, nucleo):
        with open(os.path.join(self.saves, nucleo, "Crash Bandicoot (USA).srm"), "rb") as arquivo:
            return arquivo.read()

    def test_o_cartao_do_pcsx_rearmed_vai_junto(self):
        """O save feito sem BIOS (pelo PCSX ReARMed) aparece no SwanStation:
        uma copia, e o original fica."""
        self.assertFalse(self.graficos.levar_cartao_do_ps1(self.saves, self.jogo))   # nao ha cartao
        self.cartao("PCSX-ReARMed", b"R")
        self.assertTrue(self.graficos.levar_cartao_do_ps1(self.saves, self.jogo))
        self.assertEqual(self.ler("SwanStation"), self.ler("PCSX-ReARMed"))
        self.assertFalse(self.graficos.levar_cartao_do_ps1(self.saves, self.jogo))   # so uma vez
        self.assertEqual(os.listdir(os.path.join(self.saves, "SwanStation")), ["Crash Bandicoot (USA).srm"])

    def test_nunca_troca_o_cartao_do_swanstation(self):
        self.cartao("PCSX-ReARMed", b"R")
        self.cartao("SwanStation", b"S")
        self.assertFalse(self.graficos.levar_cartao_do_ps1(self.saves, self.jogo))
        self.assertEqual(self.ler("SwanStation")[:1], b"S")

    def test_arquivo_que_nao_e_cartao_fica(self):
        self.cartao("PCSX-ReARMed", b"R", tamanho=1000)
        self.assertFalse(self.graficos.levar_cartao_do_ps1(self.saves, self.jogo))
        self.assertFalse(os.path.exists(os.path.join(self.saves, "SwanStation")))

    def test_cache_de_video_na_pasta_da_openbios(self):
        """O cache do SwanStation fica na pasta das BIOS que ele recebe; o
        cuidado do modo economico vale tambem la."""
        pasta = os.path.join(self.base, "system", "OpenBIOS")
        cache = self.graficos.cache_ps1(pasta)
        self.assertEqual(cache, os.path.join(pasta, "swanstation", "vulkan_pipelines.bin"))
        self.assertEqual(self.graficos.cache_ps1(None), self.graficos.CACHE_PS1)
        os.makedirs(os.path.dirname(cache))
        with open(cache, "wb") as arquivo:
            arquivo.write(b"x" * 100)
        antes = self.graficos.preparar_cache_ps1("Placa A", cache)
        self.assertEqual(antes, 100)
        self.assertTrue(self.graficos.fixar_cache_ps1(antes, "Placa A", cache))
        self.assertFalse(os.access(cache, os.W_OK))
        self.assertTrue(os.path.isfile(cache + ".placa"))
        self.assertEqual(self.graficos.preparar_cache_ps1("Placa B", cache), -1)   # outra placa: apaga
        self.assertFalse(os.path.exists(cache))


class TestJeitoNaConfiguracao(unittest.TestCase):
    def test_so_os_tres_jeitos_ficam(self):
        import arena
        pasta = tempfile.mkdtemp(prefix="arena_jeitos_cfg_")
        antes = arena.ARQUIVO_CONFIG
        try:
            arena.ARQUIVO_CONFIG = os.path.join(pasta, "config.json")
            with open(arena.ARQUIVO_CONFIG, "w", encoding="utf-8") as arquivo:
                arquivo.write('{"jeito_de_abrir": {"ps1": "livre", "saturn": "qualquer", "gamecube": 3}}')
            config = arena.ler_config_do_disco()
            self.assertEqual(config["jeito_de_abrir"], {"ps1": "livre"})
            self.assertEqual(arena.config_padrao()["jeito_de_abrir"], {})
        finally:
            arena.ARQUIVO_CONFIG = antes
            limpeza.apagar_pasta(pasta)


if __name__ == "__main__":
    unittest.main()
