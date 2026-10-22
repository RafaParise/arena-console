# -*- coding: utf-8 -*-
"""O servidor do ARENA no Android (item 14 do plano de 15/10/2026): o mesmo
servidor, dentro do app (servidor\\plataforma.py, servidor\\ponte_android.py e
servidor\\android_inicio.py).

O Android e' imitado aqui trocando plataforma.ANDROID (e WINDOWS), e o app
pelo outro lado do fio: um leitor que responde como o ArenaServico.java. O
teste de verdade, no aparelho virtual, e' testes\\teste_android.py."""
import http.client
import io
import json
import os
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
import zipfile
from unittest import mock

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PASTA_SERVIDOR not in sys.path:
    sys.path.insert(0, PASTA_SERVIDOR)

import android_inicio  # noqa: E402
import hardware  # noqa: E402
import plataforma  # noqa: E402
import ponte_android  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(PASTA_SERVIDOR), "testes"))
import limpeza  # noqa: E402


def no_android():
    """O servidor como se estivesse no Android."""
    return mock.patch.multiple(plataforma, ANDROID=True, WINDOWS=False, LINUX=False)


def pode_criar_link():
    """O Windows so deixa criar link com o Modo de Desenvolvedor (ou como
    administrador); o Android e o Linux, sempre."""
    pasta = tempfile.mkdtemp(prefix="arena_link_")
    try:
        os.mkdir(os.path.join(pasta, "alvo"))
        os.symlink(os.path.join(pasta, "alvo"), os.path.join(pasta, "link"), target_is_directory=True)
        return True
    except (OSError, NotImplementedError, AttributeError):
        return False
    finally:
        limpeza.apagar_pasta(pasta)


def apk_de_mentira(pasta, nucleos=("fceumm_libretro_android.so",), abi="x86_64", recursos=None):
    """Um APK (e' um zip) com os nucleos e os recursos do RetroArch."""
    caminho = os.path.join(pasta, "base.apk")
    with zipfile.ZipFile(caminho, "w") as apk:
        for nome in nucleos:
            apk.writestr("assets/arena-nucleos/%s/%s" % (abi, nome), b"ELF de mentira " + nome.encode())
        for nome, conteudo in (recursos or {}).items():
            apk.writestr(nome, conteudo)
    return caminho


class AppDeMentira:
    """O outro lado do fio: le os pedidos do servidor e responde como o
    ArenaServico.java (resposta com o mesmo numero; o fim do jogo depois)."""

    def __init__(self, respostas=None, fim_depois=0.05, codigo=0):
        self.pedidos = []
        self.respostas = respostas or {}
        self.fim_depois = fim_depois
        self.codigo = codigo
        self._buffer = ""

    def write(self, texto):
        self._buffer += texto
        while "\n" in self._buffer:
            linha, self._buffer = self._buffer.split("\n", 1)
            pedido = json.loads(linha)
            self.pedidos.append(pedido)
            threading.Thread(target=self._responder, args=(pedido,), daemon=True).start()
        return len(texto)

    def flush(self):
        pass

    def _responder(self, pedido):
        tipo = pedido.get("pedido")
        if tipo == "jogar":
            ponte_android._tratar({"id": pedido["id"], "pid": 4242})
            time.sleep(self.fim_depois)
            ponte_android._tratar({"evento": "fim", "id": pedido["id"], "codigo": self.codigo})
        elif tipo in self.respostas:
            ponte_android._tratar(dict(self.respostas[tipo], id=pedido["id"]))


class Nucleos(unittest.TestCase):
    def test_o_nucleo_do_android(self):
        with no_android():
            self.assertEqual(plataforma.arquivo_do_nucleo("fceumm_libretro.dll"), "fceumm_libretro_android.so")
            self.assertEqual(plataforma.arquivo_do_nucleo("fceumm_libretro_android.so"),
                             "fceumm_libretro_android.so")
            # Os de outro nome no Android (o N64 do OpenGL ES 3 e o MAME atual).
            self.assertEqual(plataforma.arquivo_do_nucleo("mupen64plus_next_libretro.dll"),
                             "mupen64plus_next_gles3_libretro_android.so")
            self.assertEqual(plataforma.arquivo_do_nucleo("mame_libretro.dll"), "mamearcade_libretro_android.so")
            catalogo = plataforma.nucleos_deste_sistema([{"id": "nes", "core": "fceumm_libretro.dll"}])
        self.assertEqual(catalogo[0]["core"], "fceumm_libretro_android.so")

    def test_nome_curto_e_info_voltam_ao_de_sempre(self):
        self.assertEqual(plataforma.nome_curto_do_nucleo("fceumm_libretro_android.so"), "fceumm")
        self.assertEqual(plataforma.nome_curto_do_nucleo("mupen64plus_next_gles3_libretro_android.so"),
                         "mupen64plus_next")
        self.assertEqual(plataforma.nome_curto_do_nucleo("mamearcade_libretro_android.so"), "mame")
        self.assertEqual(plataforma.nome_do_info("/x/cores/fceumm_libretro_android.so"), "fceumm_libretro.info")
        self.assertEqual(plataforma.nome_do_info("fceumm_libretro.dll"), "fceumm_libretro.info")

    def test_o_nucleo_sai_do_apk_uma_vez(self):
        pasta = tempfile.mkdtemp(prefix="arena_android_")
        try:
            apk = apk_de_mentira(pasta, ("fceumm_libretro_android.so", "snes9x_libretro_android.so"))
            cores = os.path.join(pasta, "cores")
            with mock.patch.multiple(ponte_android, APK=apk, ABI="x86_64", _NUCLEOS={}), no_android():
                self.assertEqual(plataforma.nucleos_presentes(cores),
                                 {"fceumm_libretro_android.so", "snes9x_libretro_android.so"})
                nucleo = os.path.join(cores, "fceumm_libretro_android.so")
                self.assertFalse(os.path.isfile(nucleo))
                self.assertTrue(plataforma.tem_nucleo(nucleo))       # esta no APK
                self.assertTrue(plataforma.preparar_nucleo(nucleo))  # e sai dele
                with open(nucleo, "rb") as arquivo:
                    self.assertIn(b"fceumm", arquivo.read())
                # O mesmo APK: nao tira de novo (o arquivo trocado fica).
                with open(nucleo, "wb") as arquivo:
                    arquivo.write(b"ja tirado")
                self.assertTrue(plataforma.preparar_nucleo(nucleo))
                with open(nucleo, "rb") as arquivo:
                    self.assertEqual(arquivo.read(), b"ja tirado")
                # APK novo (outra marca): tira de novo.
                with open(nucleo + ".arena", "w", encoding="utf-8") as arquivo:
                    arquivo.write("outro-apk")
                self.assertTrue(plataforma.preparar_nucleo(nucleo))
                with open(nucleo, "rb") as arquivo:
                    self.assertIn(b"fceumm", arquivo.read())
                self.assertFalse(plataforma.tem_nucleo(os.path.join(cores, "nao_veio_libretro_android.so")))
        finally:
            limpeza.apagar_pasta(pasta)


class Motores(unittest.TestCase):
    def test_no_android_vale_o_do_android(self):
        opcoes = {"video_driver": "d3d11", "audio_driver": "wasapi", "input_driver": "dinput",
                  "input_joypad_driver": "xinput", "microphone_driver": "wasapi", "midi_driver": "winmm"}
        with no_android():
            plataforma.motores_deste_sistema(opcoes)
        self.assertEqual(opcoes, plataforma.MOTORES_DO_ANDROID)
        for vindo, fica in (("glcore", "gl"), ("vulkan", "vulkan"), ("gl", "gl"), ("pulse", "opensl")):
            chave = "audio_driver" if vindo == "pulse" else "video_driver"
            with no_android():
                self.assertEqual(plataforma.motores_deste_sistema({chave: vindo})[chave], fica)

    def test_o_do_android_volta_no_windows_e_no_linux(self):
        with mock.patch.multiple(plataforma, ANDROID=False, WINDOWS=True):
            self.assertEqual(plataforma.motores_deste_sistema({"audio_driver": "opensl", "input_joypad_driver":
                                                               "android"}),
                             {"audio_driver": "wasapi", "input_joypad_driver": "xinput"})
        with mock.patch.multiple(plataforma, ANDROID=False, WINDOWS=False), \
                mock.patch.object(plataforma, "motor_de_som_do_linux", return_value="pulse"):
            self.assertEqual(plataforma.motores_deste_sistema({"audio_driver": "opensl", "input_joypad_driver":
                                                               "android"}),
                             {"audio_driver": "pulse", "input_joypad_driver": "udev"})

    def test_ajustes_da_partida_no_android(self):
        pasta = tempfile.mkdtemp(prefix="arena_android_")
        try:
            toque = os.path.join(pasta, "overlays", "gamepads", "neo-retropad", "neo-retropad.cfg")
            os.makedirs(os.path.dirname(toque))
            with open(toque, "w", encoding="utf-8") as arquivo:
                arquivo.write("overlays = 1\n")
            opcoes = {"video_driver": "gl", "audio_latency": "32", "video_shader_enable": "true"}
            self.assertEqual(plataforma.ajustes_do_android(opcoes, pasta, "/x/fsr.slangp"), "")
            self.assertEqual(opcoes["input_overlay"], toque)
            self.assertEqual(opcoes["input_overlay_enable"], "true")
            self.assertEqual(opcoes["audio_latency"], "64")
            self.assertEqual(opcoes["video_shader_enable"], "false")
            # Com o Vulkan, o filtro fica; latencia maior fica como esta.
            opcoes = {"video_driver": "vulkan", "audio_latency": "96"}
            self.assertEqual(plataforma.ajustes_do_android(opcoes, pasta, "/x/fsr.slangp"), "/x/fsr.slangp")
            self.assertEqual(opcoes["audio_latency"], "96")
            self.assertNotIn("input_android_physical_keyboard", opcoes)     # sem teclado ligado, nada
            # O teclado de verdade ligado: o RetroArch passa a trata-lo como
            # teclado (sem isso, o com setas virava controle e o F10 nao fechava).
            plataforma.ajustes_do_android(opcoes, pasta, "", teclado="qwerty2")
            self.assertEqual(opcoes["input_android_physical_keyboard"], "qwerty2")
        finally:
            limpeza.apagar_pasta(pasta)


class Sistema(unittest.TestCase):
    def test_nome_e_descricao(self):
        with no_android(), mock.patch.dict(os.environ, {"ARENA_ANDROID_SISTEMA": "Android 15 (Google Pixel 6)"}):
            self.assertEqual(plataforma.nome_do_sistema(), "android")
            self.assertEqual(plataforma.descricao(), "Android 15 (Google Pixel 6)")

    def test_o_retroarch_do_apk(self):
        with no_android():
            executavel = plataforma.executavel_do_retroarch("/app/arena/retroarch")
            self.assertTrue(executavel.endswith(plataforma.RETROARCH_DO_ANDROID))
            self.assertEqual(plataforma.comando_do_retroarch(executavel, "/app/arena/retroarch/retroarch.cfg"),
                             [executavel, "--config", "/app/arena/retroarch/retroarch.cfg"])

    def test_recursos_da_tela(self):
        import arena
        dados = arena.carregar_recursos()
        chaves = [r["chave"] for r in arena.recursos_deste_sistema(dados, windows=False, android=True)["recursos"]]
        self.assertNotIn("audio_driver", chaves)
        self.assertNotIn("input_joypad_driver", chaves)
        self.assertNotIn("audio_wasapi_exclusive_mode", chaves)
        video = next(r for r in arena.recursos_deste_sistema(dados, windows=False, android=True)["recursos"]
                     if r["chave"] == "video_driver")
        self.assertEqual(video["opcoes"], ["automatico", "gl", "vulkan"])


class Ponte(unittest.TestCase):
    def setUp(self):
        self.antes = ponte_android.CANAL

    def tearDown(self):
        ponte_android.CANAL = self.antes

    def test_sem_o_app_o_pedido_falha_sem_derrubar(self):
        ponte_android.CANAL = None
        with self.assertRaises(OSError):
            ponte_android.avisar({"pedido": "pronto"})
        self.assertEqual(ponte_android.controles(), 0)
        self.assertFalse(ponte_android.abrir_pasta("/sdcard/ARENA"))
        self.assertFalse(ponte_android.tela_pronta("http://127.0.0.1:8777"))

    def test_o_retroarch_se_espera_como_um_processo(self):
        app = AppDeMentira(codigo=0)
        ponte_android.CANAL = app
        with no_android():
            processo = plataforma.abrir_programa(["retroarch-android.txt", "--config", "/a/retroarch.cfg", "-L",
                                                  "/a/cores/fceumm_libretro_android.so", "--host",
                                                  "/a/jogos/NES/x.nes"], cwd="/a", start_new_session=True)
        self.assertEqual(processo.pid, 4242)
        self.assertEqual(processo.wait(5), 0)
        pedido = app.pedidos[0]
        self.assertEqual(pedido["pedido"], "jogar")
        # A linha inteira, menos o programa: a mesma do Windows e do Linux.
        self.assertEqual(pedido["argumentos"], ["--config", "/a/retroarch.cfg", "-L",
                                                "/a/cores/fceumm_libretro_android.so", "--host",
                                                "/a/jogos/NES/x.nes"])

    def test_o_jogo_que_caiu_volta_com_o_codigo(self):
        ponte_android.CANAL = AppDeMentira(codigo=139)
        processo = ponte_android.abrir_retroarch(["x", "-L", "y"])
        self.assertEqual(processo.wait(5), 139)
        self.assertEqual(processo.poll(), 139)

    def test_o_app_que_nao_abre_vira_erro(self):
        ponte_android.CANAL = AppDeMentira(respostas={})
        app = ponte_android.CANAL
        app._responder = lambda pedido: ponte_android._tratar({"id": pedido["id"], "erro": "sem RetroArch"})
        with self.assertRaises(OSError):
            ponte_android.abrir_retroarch(["x", "-L", "y"])

    def test_perguntas_ao_app(self):
        ponte_android.CANAL = AppDeMentira(respostas={"controles": {"quantos": 2}, "abrir_pasta": {"ok": True}})
        self.assertEqual(ponte_android.controles(), 2)
        self.assertTrue(ponte_android.abrir_pasta("/storage/emulated/0/ARENA"))

    def test_o_app_que_nao_responde_nao_prende(self):
        ponte_android.CANAL = AppDeMentira(respostas={})
        inicio = time.monotonic()
        self.assertEqual(ponte_android.perguntar({"pedido": "nada"}, limite=0.2), {})
        self.assertLess(time.monotonic() - inicio, 2)

    def test_o_fio_fechado_encerra_o_servidor(self):
        with mock.patch.object(ponte_android.os, "_exit", side_effect=SystemExit) as sair:
            with self.assertRaises(SystemExit):
                ponte_android.ouvir(io.StringIO('{"evento": "nada"}\nnao e json\n'))
        sair.assert_called_once_with(0)


class PastaDoArena(unittest.TestCase):
    """O android_inicio.py: os atalhos para a pasta escolhida, sem apagar nada."""

    def setUp(self):
        if not pode_criar_link():
            self.skipTest("este Windows nao deixa criar link (sem o Modo de Desenvolvedor)")
        self.pasta = tempfile.mkdtemp(prefix="arena_android_")
        self.raiz = os.path.join(self.pasta, "app", "arena")
        self.privada = os.path.join(self.pasta, "app", "arena-dados")
        self.escolhida = os.path.join(self.pasta, "cartao", "ARENA")
        for parte in ("jogos", "retroarch", "launcher"):
            os.makedirs(os.path.join(self.escolhida, parte))
        os.makedirs(self.raiz)
        self.trocas = mock.patch.object(android_inicio, "RAIZ", self.raiz)
        self.trocas.start()
        self.estado = dict(ponte_android.ESTADO)

    def tearDown(self):
        self.trocas.stop()
        ponte_android.ESTADO.clear()
        ponte_android.ESTADO.update(self.estado)
        limpeza.apagar_pasta(self.pasta)

    def alvo(self, relativo):
        return os.path.realpath(os.path.join(self.raiz, *relativo.split("/")))

    def test_os_atalhos_vao_para_a_pasta_escolhida(self):
        self.assertFalse(android_inicio.montar_as_pastas(self.escolhida, self.privada))
        for relativo, onde in android_inicio.PASTAS_DE_QUEM_USA:
            self.assertTrue(os.path.islink(os.path.join(self.raiz, *relativo.split("/"))), relativo)
            base = self.privada if onde == android_inicio.APP else self.escolhida
            self.assertEqual(self.alvo(relativo), os.path.realpath(os.path.join(base, *relativo.split("/"))),
                             relativo)
        self.assertEqual(ponte_android.ESTADO["pasta"], self.escolhida)
        # Um jogo posto pela pasta do app aparece na pasta escolhida.
        with open(os.path.join(self.raiz, "jogos", "x.nes"), "wb") as arquivo:
            arquivo.write(b"NES")
        self.assertTrue(os.path.isfile(os.path.join(self.escolhida, "jogos", "x.nes")))

    def test_o_que_o_servidor_grava_fica_no_app(self):
        """O arquivo da partida, a configuracao, os recordes, as listas com o
        caminho do nucleo e os ajustes do RetroArch: nunca onde outro app do
        aparelho escreve (revisao de seguranca de 18/10/2026)."""
        android_inicio.montar_as_pastas(self.escolhida, self.privada)
        for relativo in ("dados", "backup", "retroarch/config", "retroarch/playlists", "retroarch/controles",
                         "retroarch/shaders"):
            self.assertEqual(self.alvo(relativo), os.path.realpath(os.path.join(self.privada, *relativo.split("/"))),
                             relativo)
            self.assertFalse(os.path.exists(os.path.join(self.escolhida, *relativo.split("/"))), relativo)

    def test_sem_pasta_ou_com_a_pasta_fora_vale_a_do_app(self):
        for escolhida in ("", os.path.join(self.pasta, "pen-drive-que-saiu")):
            android_inicio.montar_as_pastas(escolhida, self.privada)
            self.assertEqual(self.alvo("retroarch/saves"),
                             os.path.realpath(os.path.join(self.privada, "retroarch", "saves")))
            self.assertEqual(ponte_android.ESTADO["pasta"], "")

    def test_pasta_so_de_ler(self):
        with mock.patch.object(android_inicio, "da_para_gravar", return_value=False):
            self.assertTrue(android_inicio.montar_as_pastas(self.escolhida, self.privada))
        self.assertEqual(self.alvo("jogos"), os.path.realpath(os.path.join(self.escolhida, "jogos")))
        self.assertEqual(self.alvo("retroarch/saves"),
                         os.path.realpath(os.path.join(self.privada, "retroarch", "saves")))
        self.assertTrue(ponte_android.ESTADO["so_leitura"])

    def test_pasta_de_verdade_no_lugar_do_atalho_nao_se_perde(self):
        saves = os.path.join(self.raiz, "retroarch", "saves")
        os.makedirs(saves)
        with open(os.path.join(saves, "jogo.srm"), "wb") as arquivo:
            arquivo.write(b"save")
        android_inicio.montar_as_pastas(self.escolhida, self.privada)
        self.assertTrue(os.path.islink(saves))
        guardadas = [n for n in os.listdir(os.path.join(self.raiz, "retroarch")) if n.startswith("saves.antes-")]
        self.assertEqual(len(guardadas), 1)
        self.assertTrue(os.path.isfile(os.path.join(self.raiz, "retroarch", guardadas[0], "jogo.srm")))

    def test_trocar_de_pasta_so_troca_o_atalho(self):
        android_inicio.montar_as_pastas(self.escolhida, self.privada)
        android_inicio.montar_as_pastas("", self.privada)
        self.assertEqual(self.alvo("jogos"), os.path.realpath(os.path.join(self.privada, "jogos")))
        self.assertTrue(os.path.isdir(os.path.join(self.escolhida, "jogos")))   # a escolhida continua la

    def test_recursos_do_retroarch_saem_do_apk_uma_vez(self):
        apk = apk_de_mentira(self.pasta, recursos={
            "assets/autoconfig/android/Xbox.cfg": "input_driver = \"android\"\n",
            "assets/overlays/gamepads/neo-retropad/neo-retropad.cfg": "overlays = 1\n",
            "assets/info/fceumm_libretro.info": "corename = \"FCEUmm\"\n",
            "assets/database/rdb/Nintendo.rdb": "nao vem",
            "assets/../fora.txt": "nunca"})
        with mock.patch.object(ponte_android, "APK", apk):
            self.assertEqual(android_inicio.tirar_do_apk(apk), 3)
            self.assertEqual(android_inicio.tirar_do_apk(apk), 0)      # a mesma versao: nada
        self.assertTrue(os.path.isfile(os.path.join(self.raiz, "retroarch", "autoconfig", "android", "Xbox.cfg")))
        self.assertTrue(os.path.isfile(os.path.join(self.raiz, "retroarch", "overlays", "gamepads",
                                                    "neo-retropad", "neo-retropad.cfg")))
        self.assertFalse(os.path.exists(os.path.join(self.raiz, "retroarch", "database")))

    def test_os_jogos_livres_so_na_pasta_do_app_e_uma_vez(self):
        apk = apk_de_mentira(self.pasta, recursos={
            "assets/arena-livres/MSX/noborunoca.rom": "MSX",
            "assets/arena-livres/MSX/LICENCA - noborunoca.txt": "CC0"})
        android_inicio.montar_as_pastas("", self.privada)
        self.assertEqual(android_inicio.por_os_jogos_livres(apk, ""), 2)
        # Numa origem que a lista procura (o "Acervo livre"): em jogos/MSX, a
        # lista ficava vazia (teste no emulador, 21/10/2026).
        import indexador
        self.assertIn("livres", indexador.ORIGENS)
        jogo = os.path.join(self.raiz, "jogos", "livres", "MSX", "noborunoca.rom")
        self.assertTrue(os.path.isfile(jogo))
        os.remove(jogo)                                         # a pessoa apagou: nao volta
        self.assertEqual(android_inicio.por_os_jogos_livres(apk, ""), 0)
        self.assertFalse(os.path.exists(jogo))
        # Com a pasta escolhida, nada entra nela.
        android_inicio.montar_as_pastas(self.escolhida, self.privada)
        self.assertEqual(android_inicio.por_os_jogos_livres(apk, self.escolhida), 0)
        self.assertFalse(os.path.exists(os.path.join(self.escolhida, "jogos", "livres", "MSX")))

    def test_o_cfg_do_android(self):
        os.makedirs(os.path.join(self.raiz, "retroarch"))
        with open(os.path.join(self.escolhida, "retroarch", "retroarch.cfg"), "w", encoding="utf-8") as arquivo:
            arquivo.write('menu_driver = "rgui"\nbundle_assets_extract_enable = "true"\n')
        android_inicio.preparar_o_cfg(self.escolhida)
        with open(os.path.join(self.raiz, "retroarch", "retroarch.cfg"), encoding="utf-8") as arquivo:
            texto = arquivo.read()
        self.assertIn('menu_driver = "rgui"', texto)
        self.assertIn('bundle_assets_extract_enable = "false"', texto)
        self.assertNotIn('"true"', texto)
        # O do app ja existe: nao volta a copiar o da pasta (o do app e' o que o RetroArch gravou).
        with open(os.path.join(self.escolhida, "retroarch", "retroarch.cfg"), "w", encoding="utf-8") as arquivo:
            arquivo.write('menu_driver = "xmb"\n')
        android_inicio.preparar_o_cfg(self.escolhida)
        with open(os.path.join(self.raiz, "retroarch", "retroarch.cfg"), encoding="utf-8") as arquivo:
            self.assertIn('menu_driver = "rgui"', arquivo.read())

    def test_acha_as_pastas_do_arena_no_aparelho(self):
        outra = os.path.join(self.pasta, "cartao", "Download", "ARENA-2")
        for parte in ("Jogos", "retroarch"):
            os.makedirs(os.path.join(outra, parte))
        os.makedirs(os.path.join(self.pasta, "cartao", "Fotos"))
        with mock.patch.object(ponte_android, "RAIZES", [os.path.join(self.pasta, "cartao")]):
            achadas = [a["caminho"] for a in ponte_android.pastas_do_arena()]
        self.assertEqual(sorted(achadas), sorted([self.escolhida, outra]))
        self.assertFalse(ponte_android.parece_arena(os.path.join(self.pasta, "cartao", "Fotos")))


class Segredo(unittest.TestCase):
    """No Android, qualquer app do aparelho alcanca o 127.0.0.1: so a tela do
    ARENA tem o segredo (o cookie que o app poe no WebView)."""

    def test_so_o_cookie_certo_confere(self):
        with mock.patch.object(ponte_android, "SEGREDO", "a1b2c3"):
            self.assertTrue(ponte_android.segredo_confere("arena_segredo=a1b2c3"))
            self.assertTrue(ponte_android.segredo_confere("outro=1; arena_segredo=a1b2c3"))
            for errado in ("arena_segredo=a1b2c4", "arena_segredo=", "outro=a1b2c3", "", None, "=;;=\"x"):
                self.assertFalse(ponte_android.segredo_confere(errado), errado)
        with mock.patch.object(ponte_android, "SEGREDO", ""):
            self.assertFalse(ponte_android.segredo_confere("arena_segredo="))


class RotasDoAndroid(unittest.TestCase):
    """O servidor de verdade (numa porta qualquer), com o Android imitado."""

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
        self.pasta = tempfile.mkdtemp(prefix="arena_android_")
        self.arena_do_cartao = os.path.join(self.pasta, "ARENA")
        for parte in ("jogos", "retroarch"):
            os.makedirs(os.path.join(self.arena_do_cartao, parte))
        self.escolhas = []
        self.trocas = [mock.patch.object(plataforma, "ANDROID", True),
                       mock.patch.object(ponte_android, "SEGREDO", "segredo-da-tela"),
                       mock.patch.object(ponte_android, "RAIZES", [self.pasta]),
                       mock.patch.object(ponte_android, "escolher_pasta", side_effect=self.escolhas.append)]
        for troca in self.trocas:
            troca.start()

    def tearDown(self):
        for troca in self.trocas:
            troca.stop()
        limpeza.apagar_pasta(self.pasta)

    def pedir(self, rota, dados=None, cookie=None):
        cabecalhos = {"Content-Type": "application/json"}
        if cookie is not None:
            cabecalhos["Cookie"] = cookie
        pedido = urllib.request.Request("http://127.0.0.1:%d%s" % (self.porta, rota), headers=cabecalhos,
                                        data=json.dumps(dados).encode("utf-8") if dados is not None else None,
                                        method="POST" if dados is not None else "GET")
        try:
            with urllib.request.urlopen(pedido, timeout=10) as resposta:
                return resposta.status, json.loads(resposta.read() or b"{}")
        except urllib.error.HTTPError as erro:
            return erro.code, json.loads(erro.read() or b"{}")

    def test_sem_o_segredo_outro_app_nao_entra(self):
        for cookie in (None, "arena_segredo=chute", "outro=segredo-da-tela"):
            self.assertEqual(self.pedir("/api/android/pastas", cookie=cookie)[0], 403, cookie)
            # Ate as rotas abertas a rede: do proprio aparelho, so com o segredo.
            for rota in ("/api/ranking", "/api/colegas"):
                self.assertEqual(self.pedir(rota, cookie=cookie)[0], 403, (rota, cookie))
            self.assertEqual(self.pedir("/api/sinc/receber", {"placares": [], "sessoes": []}, cookie=cookie)[0],
                             403, cookie)
            self.assertEqual(self.pedir("/api/android/pasta", {"caminho": self.arena_do_cartao},
                                        cookie=cookie)[0], 403, cookie)
        self.assertEqual(self.escolhas, [])

    def test_outro_app_por_outro_127_nao_escapa_do_segredo(self):
        # Achado F3 da auditoria 4 (Claude Security): o app que liga o
        # proprio soquete em 127.0.0.2 e conecta no 127.0.0.1 passava por
        # "outro computador" e chegava sem o segredo as rotas abertas a rede.
        for rota, dados in (("/api/ranking", None), ("/api/colegas", None),
                            ("/api/sinc/receber", {"placares": [], "sessoes": []})):
            conexao = http.client.HTTPConnection("127.0.0.1", self.porta, timeout=10,
                                                 source_address=("127.0.0.2", 0))
            try:
                corpo = json.dumps(dados).encode("utf-8") if dados is not None else None
                conexao.request("POST" if dados is not None else "GET", rota, body=corpo,
                                headers={"Content-Type": "application/json"})
                self.assertEqual(conexao.getresponse().status, 403, rota)
            finally:
                conexao.close()

    def test_todo_loopback_e_deste_aparelho(self):
        for endereco in ("127.0.0.1", "127.0.0.2", "127.255.255.254", "::1", "::ffff:127.0.0.2"):
            self.assertTrue(self.arena.endereco_de_loopback(endereco), endereco)
        for endereco in ("192.168.0.10", "10.0.2.15", "::ffff:192.168.0.10", "", None, "nao-e-ip"):
            self.assertFalse(self.arena.endereco_de_loopback(endereco), endereco)

    def test_a_tela_do_arena_entra(self):
        self.assertNotEqual(self.pedir("/api/ranking", cookie="arena_segredo=segredo-da-tela")[0], 403)
        estado, resposta = self.pedir("/api/android/pastas", cookie="arena_segredo=segredo-da-tela")
        self.assertEqual(estado, 200, resposta)
        self.assertEqual([p["caminho"] for p in resposta["pastas"]], [self.arena_do_cartao])
        estado, resposta = self.pedir("/api/android/pasta", {"caminho": self.arena_do_cartao},
                                      cookie="arena_segredo=segredo-da-tela")
        self.assertEqual((estado, resposta.get("reabrindo")), (200, True), resposta)
        # A troca vem depois da resposta: o app fecha este servidor para abrir
        # o da pasta nova, e antes a resposta as vezes nao chegava a tela.
        fim = time.monotonic() + 5
        while not self.escolhas and time.monotonic() < fim:
            time.sleep(0.05)
        self.assertEqual(self.escolhas, [self.arena_do_cartao])

    def test_pasta_que_nao_e_arena_nao_entra(self):
        estado, resposta = self.pedir("/api/android/pasta", {"caminho": self.pasta},
                                      cookie="arena_segredo=segredo-da-tela")
        self.assertEqual(estado, 400, resposta)
        self.assertEqual(self.escolhas, [])

    def test_fora_do_android_a_rota_nao_existe(self):
        with mock.patch.object(plataforma, "ANDROID", False):
            self.assertEqual(self.pedir("/api/android/pastas")[0], 404)


class Lentidao(unittest.TestCase):
    """O que deixa o jogo lento, no aparelho (servidor\\barreiras.py): a memoria
    pelo /proc, a bateria e a economia de bateria pelo app."""

    MEMINFO = "MemTotal:        3891200 kB\nMemFree:          100000 kB\nMemAvailable:     307200 kB\n"

    def setUp(self):
        self.antes = ponte_android.CANAL

    def tearDown(self):
        ponte_android.CANAL = self.antes

    def test_os_achados_do_aparelho(self):
        import barreiras
        fatos = {"sistema": "android", "memoria_total_mb": 3800, "memoria_livre_mb": 300, "memoria_em_uso_pct": 92,
                 "tem_bateria": True, "bateria_pct": 15, "na_tomada": False, "economia_de_bateria": True,
                 "disco_livre_gb": 0.5}
        ids = [b["id"] for b in barreiras.avaliar_do_sistema(fatos)]
        self.assertEqual(sorted(ids), ["bateria", "disco_cheio", "economia_bateria", "memoria"])
        # Na tomada, com a bateria boa e sem economia: nada.
        tranquilo = dict(fatos, memoria_livre_mb=2500, memoria_em_uso_pct=40, bateria_pct=80, na_tomada=True,
                         economia_de_bateria=False, disco_livre_gb=20)
        self.assertEqual(barreiras.avaliar_do_sistema(tranquilo), [])

    def test_a_checagem_rapida_com_o_app(self):
        import barreiras
        ponte_android.CANAL = AppDeMentira(respostas={"energia": {"tem_bateria": True, "bateria_pct": 12,
                                                                  "na_tomada": False, "economia": True}})
        lidos = {"/proc/meminfo": self.MEMINFO, "/proc/uptime": "3600.5 1000.0\n"}
        with mock.patch.object(barreiras, "_ler_linux", side_effect=lambda c: lidos.get(c, "")):
            fatos = barreiras.coletar_fatos_android(rapido=True)
            self.assertEqual(fatos["memoria_livre_mb"], 300)
            self.assertEqual(fatos["bateria_pct"], 12)
            rapidos = sorted(b["id"] for b in barreiras.avaliar_rapido(fatos))
        self.assertEqual(rapidos, ["bateria", "economia_bateria", "memoria"])

    def test_sem_o_app_so_a_memoria(self):
        import barreiras
        ponte_android.CANAL = None
        with mock.patch.object(barreiras, "_ler_linux", side_effect=lambda c: self.MEMINFO if "meminfo" in c else ""):
            fatos = barreiras.coletar_fatos_android(rapido=True)
        self.assertNotIn("bateria_pct", fatos)
        self.assertEqual([b["id"] for b in barreiras.avaliar_android(fatos)], ["memoria"])


class Catalogo(unittest.TestCase):
    """Os consoles no Android: os nucleos do APK contam, e o console sem
    versao para Android diz que fica no computador."""

    def test_os_consoles_no_android(self):
        import arena
        nucleos = ["fceumm_libretro_android.so", "snes9x_libretro_android.so"]
        antes = (arena._cache["catalogo"], arena._cache["plataformas"])
        try:
            with no_android(), mock.patch.object(ponte_android, "_NUCLEOS", {"lista": nucleos}), \
                    mock.patch.object(arena.graficos, "achar_externo", return_value=(None, None)):
                arena._cache["catalogo"] = None
                arena._cache["plataformas"] = (0.0, None)
                consoles = {p["id"]: p for p in arena.avaliar_plataformas(forcar=True)}
        finally:
            arena._cache["catalogo"], arena._cache["plataformas"] = antes
        self.assertNotIn(consoles["nes"]["estado"], ("sem_core", "falta_externo"))
        for console in ("ps3", "j2me"):
            self.assertIn(consoles[console]["estado"], ("sem_core", "falta_externo"), console)
            self.assertIn("não tem versão para Android", consoles[console]["motivo"], console)
            self.assertNotIn("emuladores", consoles[console]["motivo"], console)


class Hardware(unittest.TestCase):
    def test_o_que_o_app_conta(self):
        ambiente = {"ARENA_ANDROID_GPU": "Adreno (TM) 610", "ARENA_ANDROID_PROCESSADOR": "Qualcomm SM6125",
                    "ARENA_ANDROID_TELA": "2400x1080", "ARENA_ANDROID_ID": "sorteado-na-instalacao"}
        with mock.patch.object(hardware, "NO_ANDROID", True), mock.patch.dict(os.environ, ambiente):
            placa = hardware.placa_video()
            self.assertEqual(placa["nome"], "Adreno (TM) 610")
            self.assertTrue(placa["integrada"])
            self.assertEqual(hardware.processador(), "Qualcomm SM6125")
            self.assertEqual(hardware.altura_da_tela(), 1080)
            self.assertEqual(hardware.driver_video(), "gl")
            self.assertEqual(hardware.motor_sem_vulkan(), "gl")
            um = hardware.identidade_da_maquina()
        with mock.patch.object(hardware, "NO_ANDROID", True), \
                mock.patch.dict(os.environ, dict(ambiente, ARENA_ANDROID_ID="outro-aparelho")):
            self.assertNotEqual(hardware.identidade_da_maquina(), um)

    def test_celular_de_oito_nucleos_nao_vira_pc(self):
        info = {"nucleos": 8, "ram_total_gb": 8.0, "driver_video": "gl", "disco": {"classe": "muito_rapido"},
                "gpu": {"nome": "Mali-G52", "integrada": True}, "cpu": "MediaTek MT6769", "android": True}
        for relativa, teto in ((0.6, 2), (1.2, 3), (2.0, 4)):
            nota = hardware.capacidade(dict(info, velocidade={"relativa_ao_alvo": relativa}))
            self.assertLessEqual(nota["nota"], teto)
            self.assertLessEqual(nota["nota_gpu"], 3)


if __name__ == "__main__":
    unittest.main()
