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

RE_DESC = re.compile(r'^overlay(\d)_desc(\d+) = "([^,]+),(-?[\d.]+),(-?[\d.]+),(rect|radial),([\d.]+),([\d.]+)"$', re.M)


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
        self.assertEqual((c["a"], c["b"], c["z"], c["botoes_c"]), ("b", "y", "l2", "analog_right"))

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
                for m in [m for m in achados if m.group(3) != "overlay_next"]:      # o ponteiro fica fora da tela
                    x, y = float(m.group(4)), float(m.group(5))
                    self.assertTrue(0 <= x <= 1 and 0 <= y <= 1, (nome, m.group(0)))
            for botao in ("menu_toggle", "save_state", "load_state", "exit_emulator"):
                self.assertEqual(texto.count('"%s,' % botao), 2, (nome, botao))     # deitado e em pe

    def test_cada_desenho_aponta_para_o_da_outra_orientacao(self):
        # sem o next_target o RetroArch nao troca para o desenho em pe (input_overlay_auto_rotate), visto no A12
        for nome in tc.DESENHOS:
            texto = tc.gerar_cfg(nome)
            self.assertRegex(texto, r'(?m)^overlay0_desc\d+_next_target = "portrait"$', nome)
            self.assertRegex(texto, r'(?m)^overlay1_desc\d+_next_target = "landscape"$', nome)
            # o next_target so vale num botao overlay_next, e ele fica fora da tela (nenhum toque troca o desenho)
            self.assertRegex(texto, r'(?m)^overlay0_desc\d+ = "overlay_next,-1\.00000,-1\.00000,', nome)

    def test_em_pe_vai_para_a_metade_de_baixo_e_cada_lado_na_sua_borda(self):
        self.assertLess(tc.a_partir_do_deitado(0.1, 0.6)[0], 0.5)
        self.assertGreater(tc.a_partir_do_deitado(0.9, 0.6)[0], 0.5)
        for x in (0.0, 0.1, 0.5, 0.9, 1.0):
            for y in (0.0, 0.5, 1.0):
                px, py = tc.a_partir_do_deitado(x, y)
                self.assertTrue(0 <= px <= 1 and 0.5 <= py <= 1, (x, y, px, py))


class ACaraDoOriginal(unittest.TestCase):
    """Pedido do Rafael (07/11/2026): "o mesmo desenho, formato e cor dos originais (...) triangulo [verde], cruz azul,
    bola vermelha e quadrado rosa"."""

    @staticmethod
    def matiz(cor):
        import colorsys
        r, g, b = (int(cor.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4))
        return colorsys.rgb_to_hsv(r, g, b)[0] * 360

    def test_as_cores_do_playstation(self):
        faixas = {"ps_triangulo": (140, 175), "ps_x": (205, 235), "ps_circulo": (345, 375), "ps_quadrado": (300, 340)}
        for nome, (de, ate) in faixas.items():
            forma, cor, simbolo, _ = tc.IMAGENS[nome]
            m = self.matiz(cor)
            m = m + 360 if m < 30 else m                            # o vermelho dá a volta no zero
            self.assertEqual(forma, "simbolo")
            self.assertTrue(de <= m <= ate, (nome, cor, m))

    def test_as_cores_da_nintendo_e_da_sega(self):
        self.assertEqual([tc.IMAGENS["snes_" + b][1] for b in "abxy"], ["#d0242c", "#f0c419", "#2a4fc8", "#239b48"])
        self.assertEqual([tc.IMAGENS["dc_" + b][1] for b in "abxy"], ["#d0242c", "#2a4fc8", "#f0c419", "#239b48"])
        self.assertEqual(tc.IMAGENS["gc_a"][1], "#1fa35b")              # o A verde grande do GameCube
        self.assertEqual(tc.IMAGENS["gc_x"][0], "feijao_vertical")
        self.assertEqual(tc.IMAGENS["botoes_c"][1], "#f2c418")          # os C amarelos do Nintendo 64

    def test_o_direcional_de_cada_console(self):
        estilo = {nome: next(p["estilo"] for p in d["pecas"] if p.get("grupo") == "direcional")
                  for nome, d in tc.DESENHOS.items()}
        self.assertEqual((estilo["playstation"], estilo["psp"]), ("ps", "ps"))              # as quatro setas soltas
        self.assertEqual((estilo["megadrive"], estilo["saturn"]), ("sega", "sega"))         # o disco
        self.assertEqual((estilo["fliperama"], estilo["neogeo"]), ("alavanca", "alavanca_neo"))
        self.assertEqual(estilo["snes"], "cruz")
        texto = tc.gerar_cfg("playstation")
        fundo = re.search(r'^overlay0_desc(\d+) = "nul,', texto, re.M)
        self.assertIsNotNone(fundo)                                    # o fundo vai sem botao
        self.assertIn('overlay0_desc%s_overlay = "img/dpad_ps.png"' % fundo.group(1), texto)
        self.assertIn('img/seta_ps_cima.png', texto)

    def test_os_botoes_c_ficam_mesmo_sem_analogico(self):
        pecas = {p["id"]: p for p in tc.pecas_do_desenho("n64", "nenhum")}
        self.assertIn("botoes_c", pecas)
        self.assertNotIn("analogico_esq", pecas)
        texto = tc.gerar_cfg("n64")
        self.assertIn("img/botoes_c.png", texto)
        self.assertNotIn("pino_c.png", texto)                          # os C nao tem o pino que anda

    def test_a_tela_de_arrumar_recebe_a_imagem_de_cada_peca(self):
        for nome, desenho in tc.resumo_para_a_tela("dois").items():
            for peca in desenho["pecas"]:
                self.assertTrue(os.path.isfile(os.path.join(tc.PASTA_DAS_IMAGENS, peca["imagem"])), (nome, peca["id"]))
                if peca.get("pino"):
                    self.assertTrue(os.path.isfile(os.path.join(tc.PASTA_DAS_IMAGENS, peca["pino"])), (nome, peca))

    def test_a_imagem_nova_troca_a_velha_mesmo_com_o_mesmo_tamanho(self):
        pasta = tempfile.mkdtemp(prefix="arena_toque_img_")
        self.addCleanup(limpeza.apagar_pasta, pasta)
        self.assertTrue(tc.gravar_controle("snes", pasta))
        alvo = os.path.join(pasta, "overlays", "arena", "img", "snes_a.png")
        with open(alvo, "rb") as arquivo:
            certo = arquivo.read()
        with open(alvo, "wb") as arquivo:
            arquivo.write(b"x" * len(certo))                          # a velha, do mesmo tamanho
        tc.gravar_controle("snes", pasta)
        with open(alvo, "rb") as arquivo:
            self.assertEqual(arquivo.read(), certo)


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


class ARotaDasImagens(unittest.TestCase):
    """GET /toque/<nome>.png: as imagens para a tela de arrumar; so nome simples, nada fora da pasta."""

    @classmethod
    def setUpClass(cls):
        import threading
        import arena
        cls.servidor = arena.Servidor(("127.0.0.1", 0), arena.Manipulador)
        cls.porta = cls.servidor.server_address[1]
        threading.Thread(target=cls.servidor.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.servidor.shutdown()
        cls.servidor.server_close()

    def pedir(self, rota):
        import http.client
        conexao = http.client.HTTPConnection("127.0.0.1", self.porta, timeout=10)
        conexao.request("GET", rota)
        resposta = conexao.getresponse()
        corpo = resposta.read()
        conexao.close()
        return resposta.status, resposta.getheader("Content-Type"), corpo

    def test_entrega_a_imagem(self):
        for nome in ("ps_x.png", "dpad_ps_tela.png", "arena-salvar.png"):
            status, tipo, corpo = self.pedir("/toque/" + nome)
            self.assertEqual((status, tipo, corpo[1:4]), (200, "image/png", b"PNG"), nome)

    def test_recusa_o_que_nao_e_nome_simples(self):
        for rota in ("/toque/../arena.py", "/toque/..%2Farena.py", "/toque/consoles/ps_x.png", "/toque/PS_X.png",
                     "/toque/nao_existe.png", "/toque/toque_consoles.py"):
            self.assertEqual(self.pedir(rota)[0], 404, rota)


if __name__ == "__main__":
    unittest.main()
