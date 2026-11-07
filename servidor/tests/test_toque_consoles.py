# -*- coding: utf-8 -*-
"""O controle de toque com a cara de cada console (servidor\\toque_consoles.py), pedido do Rafael em 07/11/2026."""
import json
import os
import re
import sys
import tempfile
import unittest

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(AQUI)), "testes"))
import limpeza  # noqa: E402
import plataforma  # noqa: E402
import toque_consoles as tc  # noqa: E402

RE_DESC = re.compile(r'^overlay(\d)_desc(\d+) = "([^,]+),([\d.]+),([\d.]+),(rect|radial),([\d.]+),([\d.]+)"$', re.M)


def comandos(nome, ajustes=None):
    """{id da peca: comando} pelo desenho (o que o .cfg manda)."""
    return {p["id"]: p.get("comando") for p in tc.pecas_do_desenho(nome, (ajustes or {}).get("analogicos", "do_console"))}


class OMapaDeCadaNucleo(unittest.TestCase):
    """Lido dos proprios nucleos em 07/11/2026 (SET_INPUT_DESCRIPTORS no registro do RetroArch; o do Dolphin no codigo
    dele). Se este teste falhar, alguem trocou um botao: confira no nucleo antes de mudar o teste."""

    def test_mega_drive(self):
        self.assertEqual({k: v for k, v in comandos("megadrive").items() if k in "abcxyz"},
                         {"a": "y", "b": "b", "c": "a", "x": "l", "y": "x", "z": "r"})

    def test_saturn(self):
        c = comandos("saturn")
        self.assertEqual((c["a"], c["b"], c["c"], c["x"], c["y"], c["z"], c["l"], c["r"]),
                         ("b", "a", "r", "y", "x", "l", "l2", "r2"))

    def test_nintendo_64(self):
        c = comandos("n64")
        self.assertEqual((c["a"], c["b"], c["z"], c["analogico_dir"]), ("b", "y", "l2", "analog_right"))

    def test_gamecube(self):
        c = comandos("gamecube")
        self.assertEqual((c["a"], c["b"], c["x"], c["y"], c["z"], c["l"], c["r"]),
                         ("a", "b", "x", "y", "r", "l2", "r2"))

    def test_dreamcast_e_playstation(self):
        dc = comandos("dreamcast")
        self.assertEqual((dc["a"], dc["b"], dc["x"], dc["y"], dc["l"], dc["r"]), ("b", "a", "y", "x", "l2", "r2"))
        ps = comandos("playstation")
        self.assertEqual((ps["xis"], ps["circulo"], ps["quadrado"], ps["triangulo"], ps["l1"], ps["l2"]),
                         ("b", "a", "y", "x", "l", "l2"))

    def test_neo_geo(self):
        c = comandos("neogeo")
        self.assertEqual((c["a"], c["b"], c["c"], c["d"]), ("b", "a", "y", "x"))


class ODesenho(unittest.TestCase):
    def test_todo_console_do_mapa_existe_e_todo_desenho_tem_imagens(self):
        with open(os.path.join(os.path.dirname(AQUI), "consoles.json"), encoding="utf-8") as arquivo:
            ids = {p["id"] for p in json.load(arquivo)["plataformas"]}
        for console, desenho in tc.DESENHO_DO_CONSOLE.items():
            self.assertIn(console, ids)
            self.assertIn(desenho, tc.DESENHOS)
        for nome in tc.DESENHOS:
            for imagem in tc.imagens_usadas(nome):
                self.assertTrue(os.path.isfile(os.path.join(tc.PASTA_DAS_IMAGENS, imagem)), "%s: %s" % (nome, imagem))

    def test_o_cfg_tem_deitado_e_em_pe_com_as_contas_certas(self):
        for nome in tc.DESENHOS:
            texto = tc.gerar_cfg(nome)
            self.assertIn("overlays = 2", texto)
            self.assertIn('overlay0_name = "landscape"', texto)
            self.assertIn('overlay1_name = "portrait"', texto)
            for o in (0, 1):
                declarado = int(re.search(r"^overlay%d_descs = (\d+)$" % o, texto, re.M).group(1))
                achados = [m for m in RE_DESC.finditer(texto) if m.group(1) == str(o)]
                self.assertEqual(len(achados), declarado, nome)
                self.assertEqual(sorted(int(m.group(2)) for m in achados), list(range(declarado)), nome)
                for m in achados:
                    x, y = float(m.group(4)), float(m.group(5))
                    self.assertTrue(0 <= x <= 1 and 0 <= y <= 1, (nome, m.group(0)))
            for botao in ("menu_toggle", "save_state", "load_state", "exit_emulator"):
                self.assertEqual(texto.count('"%s,' % botao), 2, (nome, botao))     # deitado e em pe

    def test_em_pe_vai_para_a_metade_de_baixo_e_cada_lado_na_sua_borda(self):
        self.assertLess(tc.a_partir_do_deitado(0.1, 0.6)[0], 0.5)
        self.assertGreater(tc.a_partir_do_deitado(0.9, 0.6)[0], 0.5)
        for x in (0.0, 0.1, 0.5, 0.9, 1.0):
            for y in (0.0, 0.5, 1.0):
                px, py = tc.a_partir_do_deitado(x, y)
                self.assertTrue(0 <= px <= 1 and 0.5 <= py <= 1, (x, y, px, py))


class OsAnalogicos(unittest.TestCase):
    def test_os_dois_sempre_e_nenhum(self):
        snes = {p["id"] for p in tc.pecas_do_desenho("snes", "dois")}
        self.assertTrue({"analogico_esq", "analogico_dir"} <= snes)          # console sem analogico ganha os dois
        dc = {p["id"] for p in tc.pecas_do_desenho("dreamcast", "dois")}
        self.assertIn("analogico_dir", dc)                                   # o Dreamcast ganha o direito
        ps = [p for p in tc.pecas_do_desenho("playstation", "nenhum") if p.get("forma") == "analogico"]
        self.assertEqual(ps, [])
        self.assertIn('"analog_right,', tc.gerar_cfg("dreamcast", {"analogicos": "dois"}))
        self.assertNotIn('"analog_right,', tc.gerar_cfg("dreamcast"))

    def test_a_tela_sabe_quais_sao_extras(self):
        resumo = tc.resumo_para_a_tela("dois")
        extras = {p["id"] for p in resumo["dreamcast"]["pecas"] if p["extra"]}
        self.assertEqual(extras, {"analogico_dir"})


class OQueOAlunoArrumou(unittest.TestCase):
    def test_a_posicao_mudada_entra_no_cfg(self):
        texto = tc.gerar_cfg("snes", {"deitado": {"a": [0.5, 0.5]}})
        self.assertIn('overlay0_desc', texto)
        self.assertRegex(texto, r'overlay0_desc\d+ = "a,0\.50000,0\.50000,radial')
        self.assertNotRegex(texto, r'overlay1_desc\d+ = "a,0\.50000,0\.50000')   # em pe continua o de fabrica

    def test_o_tamanho(self):
        normal = re.search(r'"a,[\d.]+,[\d.]+,radial,([\d.]+)', tc.gerar_cfg("snes")).group(1)
        grande = re.search(r'"a,[\d.]+,[\d.]+,radial,([\d.]+)', tc.gerar_cfg("snes", {"tamanho": 1.5})).group(1)
        self.assertAlmostEqual(float(grande) / float(normal), 1.5, places=2)

    def test_limpar_joga_fora_o_que_nao_presta(self):
        limpo = tc.limpar_ajustes({
            "snes": {"deitado": {"a": [0.3, 2], "nao_existe": [0.1, 0.1], "b": ["x", 0.1], "x": [float("nan"), 0.1]},
                     "tamanho": 9, "analogicos": "talvez"},
            "console_inventado": {"tamanho": 1}, "nes": "texto"})
        self.assertEqual(limpo, {"snes": {"deitado": {"a": [0.3, 1.0]}, "tamanho": 1.5}})


class NoJogo(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_toque_")
        self.addCleanup(limpeza.apagar_pasta, self.pasta)
        neo = os.path.join(self.pasta, "overlays", "gamepads", "neo-retropad", "neo-retropad.cfg")
        os.makedirs(os.path.dirname(neo))
        with open(neo, "w", encoding="utf-8") as arquivo:
            arquivo.write('overlays = 1\noverlay0_name = "landscape-digital"\noverlay0_descs = 1\n'
                          'overlay0_desc0 = "a,0.9,0.5,radial,0.03,0.05"\n')

    def test_console_com_desenho_usa_o_dele(self):
        opcoes = {"video_driver": "gl"}
        plataforma.ajustes_do_android(opcoes, self.pasta, "", console="gamecube", toque={"desenhos": {}})
        self.assertTrue(opcoes["input_overlay"].endswith(os.path.join("overlays", "arena", "gamecube.cfg")))
        self.assertEqual(opcoes["input_overlay_auto_scale"], "true")
        img = os.path.join(self.pasta, "overlays", "arena", "img")
        for imagem in ("gc_a.png", "gc_x.png", "pino_c.png", "arena-salvar.png"):
            self.assertTrue(os.path.isfile(os.path.join(img, imagem)), imagem)

    def test_sem_desenho_ou_com_a_chave_desligada_fica_o_de_sempre(self):
        for console, toque in (("atari2600", None), ("snes", {"por_console": False})):
            opcoes = {"video_driver": "gl"}
            plataforma.ajustes_do_android(opcoes, self.pasta, "", console=console, toque=toque)
            self.assertTrue(opcoes["input_overlay"].endswith("neo-retropad-arena.cfg"), console)


if __name__ == "__main__":
    unittest.main()
