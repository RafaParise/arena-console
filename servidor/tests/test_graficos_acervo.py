# -*- coding: utf-8 -*-
"""Testes para servidor/graficos.py"""

import os
import sys
import tempfile
import shutil
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)


class TestGraficos(unittest.TestCase):

    def setUp(self):
        import graficos
        self.mod = graficos
        self.dir = tempfile.mkdtemp(prefix="arena_graf_")
        self._old_raiz = self.mod.RAIZ
        self.mod.RAIZ = self.dir
        # PASTA_RETROARCH tambem: gravar_opcoes_dos_nucleos agora le as
        # opcoes que o aluno mudou (retroarch\config\*\*.opt) para nao
        # apaga-las. Sem isto o teste leria as da maquina de verdade.
        self._old_pasta_ra = self.mod.PASTA_RETROARCH
        self.mod.PASTA_RETROARCH = os.path.join(self.dir, "retroarch")
        self._old_arquivo = getattr(self.mod, "ARQUIVO_OPCOES_CORE", None)
        self.mod.ARQUIVO_OPCOES_CORE = os.path.join(
            self.dir, "retroarch-core-options.cfg")
        # ARQUIVO_GRAFICOS tambem precisa apontar pro json de teste, senao
        # carregar_graficos() le o servidor/graficos.json de verdade (com
        # as centenas de opcoes reais) e os testes abaixo veem dado errado.
        self._old_arquivo_graficos = self.mod.ARQUIVO_GRAFICOS
        self.mod.ARQUIVO_GRAFICOS = os.path.join(self.dir, "graficos.json")
        self._old_cache = graficos._cache.copy()
        graficos._cache = {"graficos": None}
        os.makedirs(os.path.join(self.dir, "retroarch"), exist_ok=True)
        with open(os.path.join(self.dir, "graficos.json"), "w",
                  encoding="utf-8") as f:
            f.write('{"nucleos": {}, "shaders": {}}')

    def tearDown(self):
        self.mod.RAIZ = self._old_raiz
        self.mod.PASTA_RETROARCH = self._old_pasta_ra
        if self._old_arquivo is not None:
            self.mod.ARQUIVO_OPCOES_CORE = self._old_arquivo
        self.mod.ARQUIVO_GRAFICOS = self._old_arquivo_graficos
        self.mod._cache = self._old_cache
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_gravar_opcoes_dos_nucleos_arquivo_vazio(self):
        opcoes = self.mod.gravar_opcoes_dos_nucleos(3)
        self.assertEqual(opcoes, 0)
        # gravar_opcoes_dos_nucleos sempre grava o arquivo, mesmo sem
        # opcoes (fica so com as duas linhas de cabecalho) -- e assim
        # que arena.py espera encontrar o arquivo depois de chamar isto.
        self.assertTrue(os.path.isfile(self.mod.ARQUIVO_OPCOES_CORE))
        with open(self.mod.ARQUIVO_OPCOES_CORE, encoding="utf-8") as f:
            texto = f.read()
        self.assertEqual(texto.count("\n"), 2)

    def test_gravar_opcoes_dos_nucleos_com_dados(self):
        with open(os.path.join(self.dir, "graficos.json"), "w",
                  encoding="utf-8") as f:
            f.write('{"nucleos": {"fbneo": {"sempre": {"x": "1"}}}}')
        n = self.mod.gravar_opcoes_dos_nucleos(3)
        self.assertGreater(n, 0)
        with open(self.mod.ARQUIVO_OPCOES_CORE, encoding="utf-8") as f:
            texto = f.read()
        self.assertIn("x = \"1\"", texto)

    def test_gravar_opcoes_mantem_o_que_o_aluno_mudou(self):
        # Revisao pos-auditoria: com global_core_options ligado, reescrever
        # o arquivo do zero apagaria o que o aluno mudou no menu. O que
        # estava no .opt antigo do nucleo migra; chave do ARENA vence; lixo
        # "duckstation_*" nao entra.
        with open(os.path.join(self.dir, "graficos.json"), "w",
                  encoding="utf-8") as f:
            f.write('{"nucleos": {"fbneo": {"sempre": {"x": "1"}}}}')
        pasta_opt = os.path.join(self.dir, "retroarch", "config", "Nucleo")
        os.makedirs(pasta_opt)
        with open(os.path.join(pasta_opt, "Nucleo.opt"), "w", encoding="utf-8") as f:
            f.write('x = "9"\ndo_aluno = "sim"\nduckstation_BIOS.Path = "a.bin"\n')
        self.mod.gravar_opcoes_dos_nucleos(3)
        with open(self.mod.ARQUIVO_OPCOES_CORE, encoding="utf-8") as f:
            texto = f.read()
        self.assertIn('x = "1"', texto)
        self.assertNotIn('x = "9"', texto)
        self.assertIn('do_aluno = "sim"', texto)
        self.assertNotIn("duckstation_", texto)

    def test_pcsx2_4_jogadores_liga_multitap(self):
        # PCSX2 (Sio.cpp): multitap na porta 1 = Pad1, Pad3, Pad4, Pad5.
        texto = "\n".join(self.mod.controles_pcsx2(4, [0, 2, 3]))
        self.assertIn("MultitapPort1 = true", texto)
        self.assertIn("[Pad3]\nType = DualShock2", texto)
        self.assertIn("Cross = XInput-2/A", texto)       # 2o controle (XInput 2) no Pad3
        self.assertIn("[Pad5]\nType = DualShock2", texto)
        self.assertIn("Start = Keyboard/Return", texto)  # teclado: 4o jogador
        self.assertIn("[Pad2]\nType = None", texto)

    def test_pcsx2_2_jogadores_sem_multitap(self):
        texto = "\n".join(self.mod.controles_pcsx2(2, [0]))
        self.assertIn("MultitapPort1 = false", texto)
        self.assertIn("[Pad1]\nType = DualShock2", texto)
        self.assertIn("Start = Keyboard/Return", texto)  # 1 controle: teclado no 2
        self.assertIn("[Pad3]\nType = None", texto)

    def test_dolphin_portatil_e_controles(self):
        exe = os.path.join(self.dir, "Dolphin", "Dolphin.exe")
        os.makedirs(os.path.dirname(exe))
        config = os.path.join(self.dir, "Dolphin", "User", "Config")
        os.makedirs(config)
        with open(os.path.join(config, "Dolphin.ini"), "w") as f:
            f.write("[Core]\nCPUThread = True\nSIDevice0 = 0\n[Display]\nFullscreen = True\n")
        pasta = self.mod.escrever_config_dolphin(exe, [0, 1, 2], console="gamecube")
        self.assertEqual(pasta, config)
        self.assertTrue(os.path.exists(os.path.join(self.dir, "Dolphin", "portable.txt")))
        gc = open(os.path.join(config, "GCPadNew.ini")).read()
        wii = open(os.path.join(config, "WiimoteNew.ini")).read()
        dolphin = open(os.path.join(config, "Dolphin.ini")).read()
        self.assertIn("[GCPad3]\nDevice = XInput/2/Gamepad", gc)
        self.assertIn("[GCPad4]\nDevice = DInput/0/Keyboard Mouse", gc)   # teclado: 1o livre
        self.assertIn("Buttons/Start = Start", gc)
        self.assertIn("Extension = Nunchuk", wii)
        self.assertIn("Nunchuk/Stick/Up = `Left Y+`", wii)
        for porta in range(4):
            self.assertIn("SIDevice%d = 6" % porta, dolphin)
        self.assertIn("CPUThread = True", dolphin)       # o resto fica
        self.assertIn("Fullscreen = True", dolphin)

    def test_dolphin_wii_liga_so_o_wii_remote(self):
        # Achado 25/09/2026: com os dois ligados, o Mario Kart Wii via o
        # mesmo controle como Wii Remote E como controle de GameCube.
        exe = os.path.join(self.dir, "W", "Dolphin.exe")
        os.makedirs(os.path.dirname(exe))
        pasta = self.mod.escrever_config_dolphin(exe, [0, 1], console="wii")
        wii = open(os.path.join(pasta, "WiimoteNew.ini")).read()
        dolphin = open(os.path.join(pasta, "Dolphin.ini")).read()
        self.assertIn("[Wiimote1]\nSource = 1", wii)
        for porta in range(4):
            self.assertIn("SIDevice%d = 0" % porta, dolphin)
        gc = self.mod.escrever_config_dolphin(exe, [0, 1], console="gamecube")
        self.assertIn("[Wiimote1]\nSource = 0", open(os.path.join(gc, "WiimoteNew.ini")).read())

    def test_console_do_disco_dolphin(self):
        rvz_wii = os.path.join(self.dir, "a.rvz")
        with open(rvz_wii, "wb") as f:
            f.write(b"RVZ\x01" + bytes(0x44) + (2).to_bytes(4, "big"))
        iso_gc = os.path.join(self.dir, "b.iso")
        with open(iso_gc, "wb") as f:
            f.write(bytes(0x1C) + bytes.fromhex("C2339F3D"))
        self.assertEqual(self.mod.console_do_disco_dolphin(rvz_wii), "wii")
        self.assertEqual(self.mod.console_do_disco_dolphin(iso_gc), "gamecube")
        self.assertEqual(self.mod.console_do_disco_dolphin("x.wbfs"), "wii")

    def test_dolphin_sem_controle_teclado_no_jogador_1(self):
        exe = os.path.join(self.dir, "D", "Dolphin.exe")
        os.makedirs(os.path.dirname(exe))
        pasta = self.mod.escrever_config_dolphin(exe, [])
        gc = open(os.path.join(pasta, "GCPadNew.ini")).read()
        dolphin = open(os.path.join(pasta, "Dolphin.ini")).read()
        self.assertIn("[GCPad1]\nDevice = DInput/0/Keyboard Mouse", gc)
        self.assertIn("SIDevice1 = 0", dolphin)

    def test_rpcs3_um_jogador_por_controle_e_teclado_depois(self):
        # Achado 26/09/2026: so o jogador 1 vinha configurado no RPCS3.
        exe = os.path.join(self.dir, "R", "rpcs3.exe")
        os.makedirs(os.path.dirname(exe))
        destino = self.mod.escrever_controles_rpcs3(exe, [0, 2, 1])
        texto = open(destino).read()
        self.assertIn('Player 1 Input:\n  Handler: XInput\n  Device: "XInput Pad #1"', texto)
        self.assertIn('Player 2 Input:\n  Handler: XInput\n  Device: "XInput Pad #3"', texto)
        self.assertIn('Player 3 Input:\n  Handler: XInput\n  Device: "XInput Pad #2"', texto)
        self.assertIn("Player 4 Input:\n  Handler: Keyboard", texto)
        self.assertIn('Player 5 Input:\n  Handler: "Null"', texto)
        self.assertEqual(texto.count("Input:"), 7)

    def test_rpcn_segue_a_chave_nos_dois_sentidos(self):
        # Achado 26/09/2026: RPCN ligado pela tela do RPCS3 quebrava o Minecraft.
        exe = os.path.join(self.dir, "R2", "rpcs3.exe")
        cfg = os.path.join(self.dir, "R2", "config", "config.yml")
        os.makedirs(os.path.dirname(cfg))
        with open(cfg, "w", encoding="utf-8") as f:
            f.write("Net:\n  Internet enabled: Connected\n  PSN status: RPCN\n")
        self.assertTrue(self.mod.escrever_config_rpcn(exe, ligado=False))
        texto = open(cfg, encoding="utf-8").read()
        self.assertIn("Internet enabled: Disconnected", texto)
        self.assertTrue(self.mod.escrever_config_rpcn(exe, ligado=True))
        self.assertIn("Internet enabled: Connected", open(cfg, encoding="utf-8").read())

    def test_xenia_teclado_no_primeiro_jogador_sem_controle(self):
        exe = os.path.join(self.dir, "X", "xenia_canary.exe")
        toml = os.path.join(self.dir, "X", "xenia-canary.config.toml")
        os.makedirs(os.path.dirname(toml))
        base = "keyboard_mode = 0   # x\nkeyboard_user_index = 0   # y\n"
        for ligados, modo, indice in (([0, 1, 2], "1", "3"), ([], "1", "0"),
                                      ([0, 2], "1", "1"), ([0, 1, 2, 3], "0", "0")):
            with open(toml, "w", encoding="utf-8") as f:
                f.write(base)
            self.mod.escrever_config_xenia(exe, 3, controles_xinput=ligados)
            texto = open(toml, encoding="utf-8").read()
            self.assertIn("keyboard_mode = %s   # x" % modo, texto)
            self.assertIn("keyboard_user_index = %s   # y" % indice, texto)

    def test_xenia_placa_do_console(self):
        # Achado 26/09/2026: Direct3D 12 derrubava a placa (L4D2 e Gears).
        self.assertEqual(self.mod.placa_do_xenia({"externo": {"placa": "vulkan"}}), "vulkan")
        self.assertEqual(self.mod.placa_do_xenia({"externo": {}}), "any")
        exe = os.path.join(self.dir, "XV", "xenia_canary.exe")
        toml = os.path.join(self.dir, "XV", "xenia-canary.config.toml")
        os.makedirs(os.path.dirname(toml))
        with open(toml, "w", encoding="utf-8") as f:
            f.write('gpu = "any"   # placa\n')
        self.mod.escrever_config_xenia(exe, 3, placa="vulkan")
        self.assertIn('gpu = "vulkan"   # placa', open(toml, encoding="utf-8").read())

    def test_gravar_atomico(self):
        caminho = os.path.join(self.dir, "teste.txt")
        self.mod.gravar_atomico(caminho, "olá")
        with open(caminho, encoding="utf-8") as f:
            self.assertEqual(f.read(), "olá")

    def test_opcoes_do_nucleo_nao_existe(self):
        with open(os.path.join(self.dir, "graficos.json"), "w",
                  encoding="utf-8") as f:
            f.write('{"nucleos": {"core_ok": {"sempre": {"a": "1"}}}}')
        self.mod.carregar_graficos()  # resetar cache
        self.assertEqual(self.mod.opcoes_do_nucleo("inexistente", 3), {})

    def test_shader_para_nenhum(self):
        with open(os.path.join(self.dir, "graficos.json"), "w",
                  encoding="utf-8") as f:
            f.write('{"nucleos": {}, "shaders": {}}')
        self.mod.carregar_graficos()
        self.assertEqual(self.mod.shader_para(1), "")


class TestAcervo(unittest.TestCase):

    def setUp(self):
        import acervo
        self.mod = acervo
        self.dir = tempfile.mkdtemp(prefix="arena_acervo_")
        self._old_raiz = self.mod.RAIZ
        self.mod.RAIZ = self.dir
        self._old_pasta_livres = getattr(self.mod, "PASTA_LIVRES", None)
        self.mod.PASTA_LIVRES = os.path.join(self.dir, "jogos", "livres")
        acervo_pasta = os.path.join(self.dir, "dados")
        os.makedirs(acervo_pasta, exist_ok=True)
        with open(os.path.join(acervo_pasta, "acervo_autorizado.json"), "w",
                  encoding="utf-8") as f:
            f.write('[]')
        # A constante de verdade em acervo.py se chama ARQUIVO (nao
        # ARQUIVO_ACERVO). Com o nome errado o monkeypatch nao pegava e
        # ler_itens()/_salvar_itens() liam e escreviam no
        # dados/acervo_autorizado.json REAL do projeto.
        self._old_arquivo = self.mod.ARQUIVO
        self.mod.ARQUIVO = os.path.join(acervo_pasta,
                                        "acervo_autorizado.json")

    def tearDown(self):
        self.mod.RAIZ = self._old_raiz
        if self._old_pasta_livres is not None:
            self.mod.PASTA_LIVRES = self._old_pasta_livres
        self.mod.ARQUIVO = self._old_arquivo
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_listar_vazio(self):
        itens = self.mod.listar()
        self.assertIsInstance(itens, list)

    def test_fontes(self):
        fontes = self.mod.fontes()
        self.assertIsInstance(fontes, list)

    def test_acervo_json_ilegivel(self):
        with open(os.path.join(self.dir, "dados",
                               "acervo_autorizado.json"), "w") as f:
            f.write("{quebrado")
        itens = self.mod.listar()
        self.assertIsInstance(itens, list)

    def test_salvar_item(self):
        item = {
            "id": "teste-01",
            "titulo": "Jogo de Teste",
            "plataforma": "nes",
            "descricao": "Um jogo de teste",
            "licenca": "Domínio público",
            "fonte": "archive.org",
            "url": "https://archive.org/details/teste",
            "sha256": "0" * 64,
            "destino": os.path.join("jogos", "livres", "teste.nes"),
        }
        salvo = self.mod.salvar(item)
        self.assertEqual(salvo["id"], "teste-01")
        itens = self.mod.listar()
        self.assertEqual(len(itens), 1)

    def test_remover_item(self):
        item = {
            "id": "remover-01",
            "titulo": "Jogo para remover",
            "plataforma": "snes",
            "descricao": "Vai ser removido",
            "licenca": "Domínio público",
            "fonte": "archive.org",
            "url": "https://archive.org/details/remover",
            "sha256": "0" * 64,
            "destino": os.path.join("jogos", "livres", "remove.nes"),
        }
        self.mod.salvar(item)
        self.mod.remover("remover-01")
        itens = self.mod.listar()
        self.assertEqual(len(itens), 0)
        with self.assertRaises(ValueError):
            self.mod.remover("inexistente")

    def test_salvar_item_invalido(self):
        with self.assertRaises(ValueError):
            self.mod.salvar({"titulo": "Sem ID"})
        with self.assertRaises(ValueError):
            self.mod.salvar({
                "id": "nope!",
                "titulo": "Opa",
                "plataforma": "nes",
                "licenca": "pd",
                "fonte": "archive.org",
                "url": "https://archive.org/details/opa",
                "sha256": "0" * 64,
                "destino": "jogos/livres/opa.nes",
            })

    def test_salvar_item_url_invalida(self):
        with self.assertRaises(ValueError):
            self.mod.salvar({
                "id": "url-bad",
                "titulo": "URL ruim",
                "plataforma": "nes",
                "licenca": "pd",
                "fonte": "google.com",
                "url": "http://google.com/teste",
                "sha256": "0" * 64,
                "destino": "jogos/livres/teste.nes",
            })

    def test_salvar_item_destino_fora_livres(self):
        with self.assertRaises(ValueError):
            self.mod.salvar({
                "id": "dest-bad",
                "titulo": "Destino proibido",
                "plataforma": "nes",
                "licenca": "pd",
                "fonte": "archive.org",
                "url": "https://archive.org/details/proibido",
                "sha256": "0" * 64,
                "destino": os.path.join("jogos", "pessoais", "proibido.nes"),
            })


if __name__ == "__main__":
    unittest.main()
