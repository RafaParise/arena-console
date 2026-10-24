# -*- coding: utf-8 -*-
"""O PS2 no Android pelo nucleo do RetroArch do app (pedido do Rafael, 24/10/2026: "qualquer emulador
deve rodar dentro do ARENA e nao um aplicativo a parte").

Confere o que da para conferir sem celular: a BIOS do PS2 reconhecida pelo conteudo e levada para a pasta
que o nucleo le (retroarch\\system\\pcsx2\\bios), e o remendo do nucleo (jogadores 2 a 8 e abrir sem jogo)
que o GitHub aplica antes de compilar."""
import os
import re
import sys
import json
import tempfile
import unittest
import zipfile
from unittest import mock

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ = os.path.dirname(PASTA_SERVIDOR)
if PASTA_SERVIDOR not in sys.path:
    sys.path.insert(0, PASTA_SERVIDOR)
sys.path.insert(0, os.path.join(RAIZ, "testes"))

import bios  # noqa: E402
import graficos  # noqa: E402
import limpeza  # noqa: E402
import plataforma  # noqa: E402
import ponte_android  # noqa: E402

TAMANHO_PS2 = 4194304


def bios_de_ps2_de_mentira(regiao="A"):
    """4 MiB com a marca que o catalogo reconhece (ROMVER 0160AC20040614): so serve de teste."""
    dados = bytearray(TAMANHO_PS2)
    marca = b"ROMVER  0160" + regiao.encode() + b"C20040614"
    dados[0x100:0x100 + len(marca)] = marca
    return bytes(dados)


class BiosDoPs2(unittest.TestCase):

    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_ps2_android_")
        self.sistema = os.path.join(self.pasta, "system")
        os.makedirs(self.sistema)

    def tearDown(self):
        limpeza.apagar_pasta(self.pasta)

    def escrever(self, nome, dados):
        caminho = os.path.join(self.sistema, nome)
        with open(caminho, "wb") as arquivo:
            arquivo.write(dados)
        return caminho

    def test_reconhece_pelo_conteudo_e_nao_pelo_nome(self):
        ps2 = self.escrever("PS2 Bios 30004R V6 Pal.BIN", bios_de_ps2_de_mentira("E"))
        self.escrever("qualquer.bin", b"\0" * TAMANHO_PS2)            # 4 MiB que nao e' BIOS
        self.escrever("scph1001.bin", b"\0" * 524288)                  # tamanho de PS1, mas sem a marca
        self.assertEqual(bios.bios_de_playstation("ps2", self.sistema), [ps2])
        self.assertEqual(bios.bios_de_playstation("ps1", self.sistema), [])

    def test_so_ha_bios_original_do_ps2_com_o_arquivo_na_pasta(self):
        self.assertFalse(bios.tem_bios_original("ps2", self.sistema))
        self.escrever("renomeada.bin", bios_de_ps2_de_mentira())
        self.assertTrue(bios.tem_bios_original("ps2", self.sistema))
        self.assertFalse(bios.tem_bios_original("ps2", os.path.join(self.pasta, "nao_existe")))

    def test_leva_as_bios_para_a_pasta_do_nucleo_sem_trocar_nada(self):
        self.escrever("SCPH-70004_BIOS.BIN", bios_de_ps2_de_mentira("E"))
        self.escrever("scph39001.bin", bios_de_ps2_de_mentira("A"))
        levadas = graficos.preparar_bios_do_nucleo_ps2(self.sistema)
        self.assertEqual(sorted(levadas), ["SCPH-70004_BIOS.bin", "scph39001.bin"])       # extensao em minusculas
        destino = os.path.join(self.sistema, "pcsx2", "bios")
        self.assertEqual(sorted(os.listdir(destino)), ["SCPH-70004_BIOS.bin", "scph39001.bin"])
        self.assertEqual(graficos.preparar_bios_do_nucleo_ps2(self.sistema), [])          # a segunda vez nao copia
        # o que o nucleo gravou do lado (a marca do MagicGate, o NVM) e a BIOS que o professor pos la ficam
        with open(os.path.join(destino, "scph39001.bin"), "wb") as arquivo:
            arquivo.write(b"a do professor")
        with open(os.path.join(destino, "scph39001.nvm"), "wb") as arquivo:
            arquivo.write(b"idioma e hora")
        graficos.preparar_bios_do_nucleo_ps2(self.sistema)
        with open(os.path.join(destino, "scph39001.bin"), "rb") as arquivo:
            self.assertEqual(arquivo.read(), b"a do professor")
        self.assertTrue(os.path.isfile(os.path.join(destino, "scph39001.nvm")))

    def test_sem_bios_nao_cria_pasta_nenhuma(self):
        self.assertEqual(graficos.preparar_bios_do_nucleo_ps2(self.sistema), [])
        self.assertFalse(os.path.exists(os.path.join(self.sistema, "pcsx2")))
        self.assertEqual(graficos.preparar_bios_do_nucleo_ps2(os.path.join(self.pasta, "nao_existe")), [])


class BiosDaRegiaoEMotor(unittest.TestCase):
    """A mesma BIOS toda vez (idioma, data e hora do PS2 ficam iguais) e da regiao do jogo; o motor do video."""

    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_ps2_regiao_")
        self.sistema = os.path.join(self.pasta, "system")
        self.bios = os.path.join(self.sistema, "pcsx2", "bios")
        os.makedirs(self.bios)

    def tearDown(self):
        limpeza.apagar_pasta(self.pasta)

    def bios_de(self, nome, regiao):
        with open(os.path.join(self.bios, nome), "wb") as arquivo:
            arquivo.write(bios_de_ps2_de_mentira(regiao))

    def test_a_regiao_do_jogo_vem_do_nome_do_arquivo(self):
        casos = {"Mortal Kombat - Deadly Alliance (USA).chd": "A", "bully (br).chd": "A",
                 "Naruto (Europe) (De,Es,It).iso": "E", "Gran Turismo 4 (USA) (v2.00).iso": "A",
                 "Dragon Quest VIII (Japan).chd": "J", "Jogo (Asia).iso": "J", "SemMarca.iso": None,
                 "jogos/cartao-1234-5678/PS2/God of War (Europe).chd": "E"}
        for nome, esperado in casos.items():
            self.assertEqual(graficos.regiao_do_jogo_ps2(nome), esperado, nome)
        self.assertIsNone(graficos.regiao_do_jogo_ps2(None))

    def test_escolhe_a_bios_da_mesma_regiao_do_jogo(self):
        self.bios_de("PS2 Bios 30004R V6 Pal.bin", "E")
        self.bios_de("scph39001.bin", "A")
        self.assertEqual(graficos.bios_do_ps2_para_o_jogo("MK (USA).chd", self.bios), "scph39001.bin")
        self.assertEqual(graficos.bios_do_ps2_para_o_jogo("Naruto (Europe).iso", self.bios), "PS2 Bios 30004R V6 Pal.bin")

    def test_sem_bios_da_regiao_ou_sem_regiao_o_nucleo_escolhe(self):
        self.bios_de("scph39001.bin", "A")
        self.assertEqual(graficos.bios_do_ps2_para_o_jogo("Dragon (Japan).chd", self.bios), "auto")
        self.assertEqual(graficos.bios_do_ps2_para_o_jogo("SemMarca.iso", self.bios), "auto")
        self.assertEqual(graficos.bios_do_ps2_para_o_jogo("MK (USA).chd", os.path.join(self.pasta, "nao_existe")), "auto")

    def test_o_motor_automatico_e_opengl_e_o_vulkan_so_se_pedirem(self):
        self.bios_de("scph39001.bin", "A")
        for motor, nucleo in (("automatico", "OpenGL"), ("d3d11", "OpenGL"), ("vulkan", "Vulkan"), ("software", "OpenGL")):
            opcoes = graficos.opcoes_do_armsx2(motor, "MK (USA).chd", self.sistema)
            self.assertEqual(opcoes, {"armsx2_renderer": nucleo, "armsx2_bios": "scph39001.bin"}, motor)


class TemaDoJogo(unittest.TestCase):
    """O piscar claro ao abrir o jogo (Rafael, 24/10/2026): no Android 12 o sistema desenha uma tela de abertura
    (o icone num fundo claro) quando o jogo abre numa tarefa nova. O tema do jogo deixa ela preta e sem icone."""

    def setUp(self):
        sys.path.insert(0, os.path.join(RAIZ, "ferramentas"))
        import montar_android
        self.montador = montar_android

    def estilo(self, extras):
        import xml.etree.ElementTree as ET
        raiz = ET.fromstring(self.montador.ESTILO_DO_JOGO % extras)
        estilo = raiz.find("style")
        return estilo.get("name"), {i.get("name"): i.text for i in estilo.findall("item")}

    def test_o_estilo_de_cada_familia_do_android(self):
        nome, base = self.estilo("")
        self.assertEqual(nome, "ArenaJogo")
        self.assertEqual(base, {"android:windowBackground": "@android:color/black"})                   # nunca o branco do tema
        _, v28 = self.estilo(self.montador.ESTILO_V28)
        self.assertEqual(v28["android:windowLayoutInDisplayCutoutMode"], "shortEdges")                # ocupa o furo da camera
        _, v31 = self.estilo(self.montador.ESTILO_V31)
        self.assertEqual(v31["android:windowSplashScreenBackground"], "@android:color/black")         # a abertura do Android 12
        self.assertEqual(v31["android:windowSplashScreenAnimatedIcon"], "@android:color/transparent")
        self.assertIn("android:windowLayoutInDisplayCutoutMode", v31)

    def test_o_manifesto_troca_o_tema_so_da_tela_do_jogo(self):
        with open(os.path.join(RAIZ, "ferramentas", "montar_android.py"), encoding="utf-8") as arquivo:
            codigo = arquivo.read()
        self.assertIn('android:theme="@style/ArenaJogo"', codigo)
        self.assertEqual(codigo.count('android:theme="@style/ArenaJogo"'), 1)


class RecursosDoNucleo(unittest.TestCase):
    """O resources do PS2 (13 MB, 117 arquivos) vai dentro do APK e sai para system/pcsx2/resources: o nucleo
    nem liga sem ele, e a instalacao tem de continuar sendo um arquivo so."""

    PREFIXO = "assets/arena-recursos/pcsx2/resources/"

    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_recursos_")
        self.sistema = os.path.join(self.pasta, "system")
        os.makedirs(self.sistema)
        self.apk = os.path.join(self.pasta, "base.apk")
        with zipfile.ZipFile(self.apk, "w") as apk:
            apk.writestr(self.PREFIXO + "GameIndex.yaml", b"jogos")
            apk.writestr(self.PREFIXO + "shaders/vk/tfx.glsl", b"sombra")
            apk.writestr(self.PREFIXO + "../../../../fora.txt", b"isto nao pode sair da pasta system")
            apk.writestr("assets/arena-nucleos/arm64-v8a/x_libretro_android.so", b"nao e' recurso")
        self.resources = os.path.join(self.sistema, "pcsx2", "resources")

    def tearDown(self):
        limpeza.apagar_pasta(self.pasta)

    def preparar(self):
        with mock.patch.multiple(ponte_android, APK=self.apk, ABI="arm64-v8a"), \
                mock.patch.object(plataforma, "ANDROID", True):
            return plataforma.preparar_recursos(self.sistema)

    def test_sai_do_apk_para_a_pasta_do_nucleo_e_so_uma_vez(self):
        self.assertEqual(self.preparar(), 2)
        with open(os.path.join(self.resources, "GameIndex.yaml"), "rb") as arquivo:
            self.assertEqual(arquivo.read(), b"jogos")
        self.assertTrue(os.path.isfile(os.path.join(self.resources, "shaders", "vk", "tfx.glsl")))
        self.assertFalse(os.path.exists(os.path.join(self.pasta, "fora.txt")))           # o ".." nao escapa
        self.assertFalse(os.path.exists(os.path.join(os.path.dirname(self.pasta), "fora.txt")))
        self.assertEqual(self.preparar(), 0)                                             # mesma marca: nada a fazer

    def test_a_pasta_apagada_volta_e_o_apk_novo_troca(self):
        self.preparar()
        limpeza.apagar_pasta(self.resources)
        self.assertEqual(self.preparar(), 2)                                             # a marca ia junto com a pasta
        with open(os.path.join(self.resources, ".arena"), "w", encoding="utf-8") as arquivo:
            arquivo.write("outro-apk")
        self.assertEqual(self.preparar(), 2)                                             # APK de outra marca

    def test_fora_do_android_nao_faz_nada(self):
        with mock.patch.multiple(ponte_android, APK=self.apk), mock.patch.object(plataforma, "ANDROID", False):
            self.assertEqual(plataforma.preparar_recursos(self.sistema), 0)
        self.assertFalse(os.path.exists(self.resources))

    def test_apk_sem_recursos_ou_ilegivel_nao_derruba(self):
        with mock.patch.multiple(ponte_android, APK=os.path.join(self.pasta, "nao_existe.apk")), \
                mock.patch.object(plataforma, "ANDROID", True):
            self.assertEqual(plataforma.preparar_recursos(self.sistema), 0)


class NucleoCompiladoNoGithub(unittest.TestCase):
    """O PS2 do Android e' compilado no GitHub (ARMv8.0) e conferido pela marca do .so e da pasta de apoio."""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, os.path.join(RAIZ, "ferramentas"))
        import montar_android
        cls.montador = montar_android
        with open(montar_android.ARQUIVO_DOS_NUCLEOS, encoding="utf-8") as arquivo:
            cls.ficha = json.load(arquivo)["arm64-v8a"]["armsx2_libretro_android.so"]

    def test_o_registro_diz_de_onde_vem_e_qual_a_marca(self):
        self.assertEqual(self.ficha["construido_por"]["fluxo"], "nucleo-ps2-android.yml")
        self.assertRegex(self.ficha["sha256_so"], r"^[0-9a-f]{64}$")
        self.assertRegex(self.ficha["recursos"]["sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(self.ficha["recursos"]["destino"], "pcsx2/resources")
        self.assertTrue(os.path.isfile(os.path.join(RAIZ, ".github", "workflows", self.ficha["construido_por"]["fluxo"])))

    def test_o_remendo_que_o_registro_cita_e_o_do_repositorio(self):
        import hashlib
        pasta = os.path.join(RAIZ, "ferramentas", "remendos")
        remendos = sorted(n for n in os.listdir(pasta) if n.endswith(".patch"))
        self.assertEqual(len(remendos), 3)
        pendentes = set(self.ficha.get("remendos_pendentes", []))     # no repositorio, ainda fora do .so fixado
        self.assertLessEqual(pendentes, set(remendos))
        for nome in remendos:                                   # o .so fixado foi compilado COM todos os remendos
            with open(os.path.join(pasta, nome), "rb") as arquivo:
                marca = hashlib.sha256(arquivo.read()).hexdigest()
            if nome in pendentes:
                self.assertNotIn(marca[:12], self.ficha["origem"], nome)
            else:
                self.assertIn(marca[:12], self.ficha["origem"], nome)

    def test_a_marca_da_pasta_muda_com_o_nome_e_com_o_conteudo(self):
        pasta = tempfile.mkdtemp(prefix="arena_arvore_")
        try:
            os.makedirs(os.path.join(pasta, "a"))
            with open(os.path.join(pasta, "a", "x.txt"), "w", encoding="utf-8") as arquivo:
                arquivo.write("um")
            antes = self.montador.marca_da_arvore(pasta)
            self.assertEqual(self.montador.marca_da_arvore(pasta), antes)
            os.replace(os.path.join(pasta, "a", "x.txt"), os.path.join(pasta, "a", "y.txt"))
            self.assertNotEqual(self.montador.marca_da_arvore(pasta), antes)           # outro nome
            with open(os.path.join(pasta, "a", "y.txt"), "w", encoding="utf-8") as arquivo:
                arquivo.write("dois")
            self.assertNotEqual(self.montador.marca_da_arvore(pasta), antes)           # outro conteudo
        finally:
            limpeza.apagar_pasta(pasta)

    def test_com_o_cache_em_ordem_nao_chama_o_github(self):
        pasta = tempfile.mkdtemp(prefix="arena_cache_")
        try:
            so = os.path.join(pasta, "nucleo_libretro_android.so")
            with open(so, "wb") as arquivo:
                arquivo.write(b"ELF de mentira")
            apoio = self.montador.recursos_do_cache("nucleo_libretro_android.so", pasta)
            os.makedirs(apoio)
            with open(os.path.join(apoio, "dado.txt"), "w", encoding="utf-8") as arquivo:
                arquivo.write("apoio")
            ficha = {"construido_por": {"fluxo": "x.yml", "artefato": "y"},
                     "sha256_so": self.montador.marca(so),
                     "recursos": {"pasta": "resources", "destino": "p/r", "sha256": self.montador.marca_da_arvore(apoio)}}
            with mock.patch.object(self.montador.subprocess, "run", side_effect=AssertionError("chamou o gh")):
                self.assertEqual(self.montador.nucleo_do_github("nucleo_libretro_android.so", ficha, pasta), so)
            # com o .so adulterado, tenta o GitHub (aqui sem o gh): nao devolve o arquivo ruim
            with open(so, "wb") as arquivo:
                arquivo.write(b"adulterado")
            with mock.patch.object(self.montador.shutil, "which", return_value=None):
                self.assertIsNone(self.montador.nucleo_do_github("nucleo_libretro_android.so", ficha, pasta))
        finally:
            limpeza.apagar_pasta(pasta)


class AjusteFinoDosNucleos(unittest.TestCase):
    def test_limpa_o_que_nao_serve(self):
        entrada = {"armsx2": {"armsx2_upscale": "2x", "ligado": True, "n": 3, "ruim": 'a"b', "x y": "1",
                              "longa": "z" * 200, "lista": [1]},
                   "Nome Ruim": {"a": "1"}, "outro": "texto", "vazio": {"x y": "1"}}
        self.assertEqual(graficos.limpar_ajustes_dos_nucleos(entrada),
                         {"armsx2": {"armsx2_upscale": "2x", "ligado": "true", "n": "3"}})
        self.assertEqual(graficos.limpar_ajustes_dos_nucleos(None), {})
        self.assertEqual(graficos.ajustes_finos_do_nucleo(entrada, "armsx2")["ligado"], "true")
        self.assertEqual(graficos.ajustes_finos_do_nucleo(entrada, "fceumm"), {})


class IniDoPs2(unittest.TestCase):
    """O que o ARENA grava no armsx2-libretro.ini (o que o nucleo nao mostra como opcao)."""

    INI = ("[UI]\nSettingsVersion = 1\n\n[EmuCore/GS]\nRenderer = 14\ntexture_preloading = 2\n"
           "HWDownloadMode = 0\n\n[EmuCore]\nAutoTune = false\n")

    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_ini_ps2_")
        self.sistema = os.path.join(self.pasta, "system")
        self.caminho = graficos.arquivo_ini_do_armsx2(self.sistema)

    def tearDown(self):
        limpeza.apagar_pasta(self.pasta)

    def criar(self, texto=None):
        os.makedirs(os.path.dirname(self.caminho))
        with open(self.caminho, "w", encoding="utf-8", newline="\n") as arquivo:
            arquivo.write(self.INI if texto is None else texto)

    def ler(self):
        with open(self.caminho, encoding="utf-8") as arquivo:
            return arquivo.read()

    def test_limpa_o_que_nao_tem_cara_de_ini(self):
        entrada = {"armsx2": {"EmuCore/GS": {"texture_preloading": 1, "GSBackThreadMode": True,
                                             "ruim": "a\nb", "com espaco": "1", "longo": "x" * 200},
                              "Secao Ruim": {"a": "1"}, "[": {"a": "1"}},
                   "Nome Ruim": {"EmuCore": {"a": "1"}}, "outro": [1]}
        self.assertEqual(graficos.limpar_ajustes_ini(entrada),
                         {"armsx2": {"EmuCore/GS": {"texture_preloading": "1", "GSBackThreadMode": "true"}}})
        self.assertEqual(graficos.limpar_ajustes_ini(None), {})

    def test_o_padrao_vem_do_graficos_json_por_motor_e_nivel(self):
        self.assertEqual(graficos.ini_padrao_do_armsx2("OpenGL")["EmuCore/GS"]["GSBackThreadMode"], "0")   # explicito
        self.assertEqual(graficos.ini_padrao_do_armsx2("Vulkan")["EmuCore/GS"]["GSBackThreadMode"], "1")
        self.assertEqual(graficos.ini_padrao_do_armsx2(None), graficos.ini_padrao_do_armsx2("OpenGL"))

    def test_sem_o_arquivo_do_nucleo_nao_cria_nada(self):
        self.assertEqual(graficos.aplicar_ini_do_armsx2(self.sistema, {"EmuCore": {"AutoTune": "true"}}), [])
        self.assertFalse(os.path.exists(self.caminho))                  # so a partir da segunda abertura

    def test_troca_acrescenta_e_mantem_o_resto(self):
        self.criar()
        mudou = graficos.aplicar_ini_do_armsx2(self.sistema, {
            "EmuCore/GS": {"texture_preloading": "1", "GSBackThreadMode": "1"}, "EmuCore": {"AutoTune": "true"},
            "Novo/Secao": {"x": "y"}})
        self.assertEqual(len(mudou), 4)
        texto = self.ler()
        self.assertIn("texture_preloading = 1", texto)
        self.assertNotIn("texture_preloading = 2", texto)
        self.assertIn("GSBackThreadMode = 1", texto)
        self.assertIn("Renderer = 14", texto)                             # o resto fica
        self.assertIn("HWDownloadMode = 0", texto)
        self.assertIn("SettingsVersion = 1", texto)
        self.assertIn("[Novo/Secao]\nx = y", texto)
        self.assertEqual(graficos._valor_ini(texto, "EmuCore", "AutoTune"), "true")

    def test_nao_regrava_o_que_ja_esta_igual(self):
        self.criar()
        ajustes = {"EmuCore/GS": {"texture_preloading": "2"}}
        antes = os.stat(self.caminho).st_mtime_ns
        self.assertEqual(graficos.aplicar_ini_do_armsx2(self.sistema, ajustes), [])
        self.assertEqual(os.stat(self.caminho).st_mtime_ns, antes)

    def test_arquivo_com_marca_de_ordem_de_bytes_e_aceito(self):
        self.criar()
        with open(self.caminho, "rb") as arquivo:
            dados = arquivo.read()
        with open(self.caminho, "wb") as arquivo:
            arquivo.write(b"\xef\xbb\xbf" + dados)
        self.assertEqual(len(graficos.aplicar_ini_do_armsx2(self.sistema, {"EmuCore": {"AutoTune": "true"}})), 1)
        self.assertEqual(graficos._valor_ini(self.ler(), "EmuCore", "AutoTune"), "true")


class EeDoPs2PelaNota(unittest.TestCase):
    """A desaceleracao do processador do PS2 (EE) vem da nota do aparelho, do nivel abaixo do original e do degrau."""

    def test_o_passo_pela_nota(self):
        self.assertEqual([graficos.passo_do_ee_do_ps2(n) for n in (1, 2, 3, 4, 5)], [1, 1, 0, 0, 0])

    def test_abaixo_do_original_e_o_degrau_empurram_para_baixo(self):
        self.assertEqual(graficos.passo_do_ee_do_ps2(5, "leve"), 2)
        self.assertEqual(graficos.passo_do_ee_do_ps2(5, "minimo"), 3)
        self.assertEqual(graficos.passo_do_ee_do_ps2(3, "leve"), 2)
        self.assertEqual(graficos.passo_do_ee_do_ps2(1, "leve"), 2)           # nunca mais fiel do que a nota pede
        self.assertEqual([graficos.passo_do_ee_do_ps2(4, degrau=d) for d in (0, 1, 2, 3, 4)], [0, 1, 2, 3, 3])
        self.assertEqual(graficos.passo_do_ee_do_ps2(2, degrau=3), 3)         # teto: o ultimo passo
        self.assertEqual(graficos.passo_do_ee_do_ps2(2, degrau=-5), 1)

    def test_as_opcoes_do_nucleo_levam_a_taxa_e_o_salto(self):
        opcoes = graficos.opcoes_do_armsx2("automatico", "x.chd", "/nao/existe", nota=2)
        self.assertEqual((opcoes["armsx2_ee_cycle_rate"], opcoes["armsx2_ee_cycle_skip"]), ("75%", "disabled"))
        opcoes = graficos.opcoes_do_armsx2("automatico", "x.chd", "/nao/existe", nota=2, degrau=2)
        self.assertEqual((opcoes["armsx2_ee_cycle_rate"], opcoes["armsx2_ee_cycle_skip"]), ("50%", "disabled"))
        opcoes = graficos.opcoes_do_armsx2("automatico", "x.chd", "/nao/existe", nota=5)
        self.assertEqual((opcoes["armsx2_ee_cycle_rate"], opcoes["armsx2_ee_cycle_skip"]), ("100%", "disabled"))
        self.assertNotIn("armsx2_ee_cycle_rate", graficos.opcoes_do_armsx2("automatico", "x.chd", "/nao/existe"))

    def test_so_o_vulkan_pedido_vai_para_o_vulkan(self):
        for motor, esperado in (("automatico", "OpenGL"), ("opengl", "OpenGL"), ("vulkan", "Vulkan"),
                                ("d3d11", "OpenGL")):
            self.assertEqual(graficos.opcoes_do_armsx2(motor, "x.chd", "/nao/existe")["armsx2_renderer"], esperado)

    def test_o_automatico_vai_para_o_vulkan_so_se_o_aparelho_tem(self):
        com = graficos.opcoes_do_armsx2("automatico", "x.chd", "/nao/existe", vulkan=True)
        self.assertEqual(com["armsx2_renderer"], "Vulkan")
        self.assertEqual(graficos.opcoes_do_armsx2("automatico", "x.chd", "/nao/existe", vulkan=False)["armsx2_renderer"],
                         "OpenGL")
        # quem escolheu o OpenGL na mao fica no OpenGL, mesmo num aparelho com Vulkan
        self.assertEqual(graficos.opcoes_do_armsx2("opengl", "x.chd", "/nao/existe", vulkan=True)["armsx2_renderer"],
                         "OpenGL")

    def test_o_renderizador_por_software_nao_e_oferecido(self):
        # no A12 o "Software" nao liga (o registro diz "Failed to initialize GS" e a tela fica preta)
        self.assertEqual(graficos.opcoes_do_armsx2("software", "x.chd", "/nao/existe")["armsx2_renderer"], "OpenGL")

    def test_a_escada_do_json_nao_tem_mais_o_ee_do_abaixo_do_original(self):
        # o EE sai do codigo (passo_do_ee_do_ps2): duas fontes para a mesma opcao se contradiriam
        dados = graficos.carregar_graficos()["abaixo_do_original"]
        for nivel in ("leve", "minimo"):
            self.assertNotIn("armsx2_ee_cycle_rate", dados[nivel].get("armsx2", {}))
            self.assertNotIn("armsx2_ee_cycle_skip", dados[nivel].get("armsx2", {}))


class StatusDoPs2(unittest.TestCase):
    """arena-status.json: a velocidade de verdade, gravada pelo nucleo."""

    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_status_ps2_")
        self.caminho = graficos.arquivo_de_status_do_armsx2(self.pasta)
        os.makedirs(os.path.dirname(self.caminho))

    def tearDown(self):
        limpeza.apagar_pasta(self.pasta)

    def escrever(self, texto):
        with open(self.caminho, "w", encoding="utf-8") as arquivo:
            arquivo.write(texto)

    def test_le_a_linha_que_o_nucleo_grava(self):
        linha = json.dumps({chave: 1 for chave in graficos.CHAVES_DO_STATUS_DO_ARMSX2}).replace(
            '"velocidade": 1', '"velocidade": 73.4')
        self.escrever(linha + "\n")
        status = graficos.ler_status_do_armsx2(self.pasta)
        self.assertEqual(status["velocidade"], 73.4)

    def test_arquivo_ausente_ou_pela_metade_ou_sem_velocidade_devolve_none(self):
        self.assertIsNone(graficos.ler_status_do_armsx2(os.path.join(self.pasta, "outra")))
        self.escrever('{"sequencia": 3, "velocid')
        self.assertIsNone(graficos.ler_status_do_armsx2(self.pasta))
        self.escrever('{"sequencia": 3}')
        self.assertIsNone(graficos.ler_status_do_armsx2(self.pasta))
        self.escrever('{"velocidade": true}')
        self.assertIsNone(graficos.ler_status_do_armsx2(self.pasta))
        self.escrever("[1, 2]")
        self.assertIsNone(graficos.ler_status_do_armsx2(self.pasta))


class PreparoDoPs2NoAndroid(unittest.TestCase):
    """arena.preparar_o_ps2_do_android: o que o ARENA faz antes de abrir o PS2 (jogo ou menu da BIOS)."""

    @classmethod
    def setUpClass(cls):
        import arena
        cls.arena = arena

    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_preparo_ps2_")
        self.sistema = os.path.join(self.pasta, "system")
        os.makedirs(os.path.join(self.sistema, "pcsx2", "inis"))
        self.trocas = [mock.patch.object(self.arena, "PASTA_SISTEMA", self.sistema),
                       mock.patch.object(self.arena.plataforma_do_sistema, "preparar_recursos", return_value=0)]
        for troca in self.trocas:
            troca.start()
        self.ini = graficos.arquivo_ini_do_armsx2(self.sistema)

    def tearDown(self):
        for troca in reversed(self.trocas):
            troca.stop()
        limpeza.apagar_pasta(self.pasta)

    def com_ini(self):
        with open(self.ini, "w", encoding="utf-8", newline="\n") as arquivo:
            arquivo.write("[UI]\nSettingsVersion = 1\n\n[EmuCore/GS]\ntexture_preloading = 2\n")

    def ler_ini(self):
        with open(self.ini, encoding="utf-8") as arquivo:
            return arquivo.read()

    def test_primeira_abertura_devolve_as_opcoes_e_ainda_nao_cria_o_ini(self):
        with mock.patch.dict(self.arena.CAPACIDADE, {"nota": 2}):                  # o aparelho de entrada
            opcoes = self.arena.preparar_o_ps2_do_android(self.arena.config_padrao(), {"arquivo": "jogos/x (USA).chd"})
        self.assertEqual(opcoes, {"armsx2_renderer": "OpenGL", "armsx2_bios": "auto",
                                  "armsx2_ee_cycle_rate": "75%", "armsx2_ee_cycle_skip": "disabled"})
        self.assertFalse(os.path.exists(self.ini))

    def test_o_automatico_com_vulkan_liga_a_thread_de_fundo_do_video(self):
        self.com_ini()
        with mock.patch.dict(self.arena.MAQUINA, {"vulkan": True}):
            opcoes = self.arena.preparar_o_ps2_do_android(self.arena.config_padrao(), {"arquivo": "x.chd"})
        self.assertEqual(opcoes["armsx2_renderer"], "Vulkan")
        self.assertEqual(graficos._valor_ini(self.ler_ini(), "EmuCore/GS", "GSBackThreadMode"), "1")
        with mock.patch.dict(self.arena.MAQUINA, {"vulkan": False}):
            opcoes = self.arena.preparar_o_ps2_do_android(self.arena.config_padrao(), {"arquivo": "x.chd"})
        self.assertEqual(opcoes["armsx2_renderer"], "OpenGL")
        self.assertEqual(graficos._valor_ini(self.ler_ini(), "EmuCore/GS", "GSBackThreadMode"), "0")

    def test_o_degrau_do_desempenho_que_aprende_desacelera_mais_o_ee(self):
        with mock.patch.dict(self.arena.CAPACIDADE, {"nota": 2}):
            opcoes = self.arena.preparar_o_ps2_do_android(self.arena.config_padrao(), {"arquivo": "x.chd"}, degrau=1)
        self.assertEqual((opcoes["armsx2_ee_cycle_rate"], opcoes["armsx2_ee_cycle_skip"]), ("60%", "disabled"))
        with mock.patch.dict(self.arena.CAPACIDADE, {"nota": 5}):
            opcoes = self.arena.preparar_o_ps2_do_android(self.arena.config_padrao(), {"arquivo": "x.chd"})
        self.assertEqual((opcoes["armsx2_ee_cycle_rate"], opcoes["armsx2_ee_cycle_skip"]), ("100%", "disabled"))

    def test_com_o_ini_do_nucleo_poe_a_pre_carga_parcial(self):
        self.com_ini()
        self.arena.preparar_o_ps2_do_android(self.arena.config_padrao(), {"arquivo": "x.chd"})
        self.assertEqual(graficos._valor_ini(self.ler_ini(), "EmuCore/GS", "texture_preloading"), "1")
        self.assertEqual(graficos._valor_ini(self.ler_ini(), "EmuCore/GS", "GSBackThreadMode"), "0")  # OpenGL: sem a thread

    def test_o_menu_da_bios_passa_pela_abertura_do_ps2(self):
        opcoes = self.arena.preparar_o_ps2_do_android(self.arena.config_padrao(), None, sem_jogo=True)
        self.assertEqual(opcoes["armsx2_fast_boot"], "disabled")
        jogo = self.arena.preparar_o_ps2_do_android(self.arena.config_padrao(), {"arquivo": "x.chd"})
        self.assertNotIn("armsx2_fast_boot", jogo)                       # no jogo vale o da escada (graficos.json)

    def test_o_vulkan_pedido_liga_a_thread_de_fundo(self):
        self.com_ini()
        config = self.arena.config_padrao()
        config["ajustes_dos_nucleos"] = {"armsx2": {"armsx2_renderer": "Vulkan"}}
        opcoes = self.arena.preparar_o_ps2_do_android(config, {"arquivo": "x.chd"})
        self.assertEqual(opcoes["armsx2_renderer"], "Vulkan")
        self.assertEqual(graficos._valor_ini(self.ler_ini(), "EmuCore/GS", "GSBackThreadMode"), "1")

    def test_o_ajuste_ini_da_pessoa_vale_por_cima(self):
        self.com_ini()
        config = self.arena.config_padrao()
        config["ajustes_ini_dos_nucleos"] = {"armsx2": {"EmuCore/GS": {"texture_preloading": "2"}}}
        self.arena.preparar_o_ps2_do_android(config, {"arquivo": "x.chd"})
        self.assertEqual(graficos._valor_ini(self.ler_ini(), "EmuCore/GS", "texture_preloading"), "2")

    def test_a_bios_da_regiao_do_jogo(self):
        bios_dir = os.path.join(self.sistema, "pcsx2", "bios")
        os.makedirs(bios_dir)
        for nome, regiao in (("americana.bin", "A"), ("europeia.bin", "E")):
            with open(os.path.join(bios_dir, nome), "wb") as arquivo:
                arquivo.write(bios_de_ps2_de_mentira(regiao))
        opcoes = self.arena.preparar_o_ps2_do_android(self.arena.config_padrao(), {"arquivo": "jogo (Europe).chd"})
        self.assertEqual(opcoes["armsx2_bios"], "europeia.bin")


class ArquivoDeAjustesDoPs2(unittest.TestCase):
    """arena-overrides.ini: o que o nucleo remendado le a cada abertura, inclusive a primeira."""

    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_ajustes_ps2_")
        self.sistema = os.path.join(self.pasta, "system")
        self.caminho = graficos.arquivo_de_ajustes_do_armsx2(self.sistema)

    def tearDown(self):
        limpeza.apagar_pasta(self.pasta)

    def test_grava_a_secao_overrides_com_secao_barra_chave(self):
        self.assertTrue(graficos.gravar_ajustes_do_armsx2(self.sistema, {
            "EmuCore/GS": {"texture_preloading": "1", "GSBackThreadMode": "1"}, "EmuCore": {"AutoTune": "true"}}))
        with open(self.caminho, encoding="utf-8") as arquivo:
            linhas = [l for l in arquivo.read().splitlines() if l and not l.startswith("#")]
        self.assertEqual(linhas, ["[Overrides]", "EmuCore/AutoTune = true", "EmuCore/GS/GSBackThreadMode = 1",
                                  "EmuCore/GS/texture_preloading = 1"])

    def test_vale_na_primeira_abertura_e_so_regrava_se_mudou(self):
        self.assertFalse(os.path.exists(os.path.join(self.sistema, "pcsx2", "inis", "armsx2-libretro.ini")))
        ajustes = {"EmuCore/GS": {"texture_preloading": "1"}}
        self.assertTrue(graficos.gravar_ajustes_do_armsx2(self.sistema, ajustes))
        antes = os.stat(self.caminho).st_mtime_ns
        self.assertFalse(graficos.gravar_ajustes_do_armsx2(self.sistema, ajustes))
        self.assertEqual(os.stat(self.caminho).st_mtime_ns, antes)
        self.assertTrue(graficos.gravar_ajustes_do_armsx2(self.sistema, {"EmuCore/GS": {"texture_preloading": "0"}}))

    def test_o_preparo_do_ps2_grava_o_arquivo_mesmo_sem_o_ini_do_nucleo(self):
        import arena
        with mock.patch.object(arena, "PASTA_SISTEMA", self.sistema), \
                mock.patch.object(arena.plataforma_do_sistema, "preparar_recursos", return_value=0):
            arena.preparar_o_ps2_do_android(arena.config_padrao(), {"arquivo": "x.chd"})
        with open(self.caminho, encoding="utf-8") as arquivo:
            texto = arquivo.read()
        self.assertIn("EmuCore/GS/texture_preloading = 1", texto)
        self.assertIn("EmuCore/GS/GSBackThreadMode = 0", texto)


class RemendoDoNucleo(unittest.TestCase):
    """Os remendos sao texto escrito a mao: confere o formato (um erro de conta de linhas so apareceria no
    GitHub, depois de baixar o ARMSX2 inteiro). Os dois se aplicam em ordem alfabetica: primeiro os jogadores, e o
    da sobreposicao (feito sobre o resultado do primeiro) depois."""

    PASTA = os.path.join(RAIZ, "ferramentas", "remendos")
    CAMINHO = os.path.join(PASTA, "armsx2-libretro-jogadores.patch")
    CAMINHO_DA_SOBREPOSICAO = os.path.join(PASTA, "armsx2-libretro-sobreposicao-do-arena.patch")
    CAMINHO_DO_STATUS = os.path.join(PASTA, "armsx2-libretro-status-do-arena.patch")

    def setUp(self):
        with open(self.CAMINHO, "rb") as arquivo:
            self.bruto = arquivo.read()
        self.texto = self.bruto.decode("utf-8")
        with open(self.CAMINHO_DA_SOBREPOSICAO, "rb") as arquivo:
            self.bruto2 = arquivo.read()
        self.texto2 = self.bruto2.decode("utf-8")
        with open(self.CAMINHO_DO_STATUS, "rb") as arquivo:
            self.bruto3 = arquivo.read()
        self.texto3 = self.bruto3.decode("utf-8")

    def remendos(self):
        return [(self.bruto, self.texto), (self.bruto2, self.texto2), (self.bruto3, self.texto3)]

    def test_so_tem_fim_de_linha_do_unix_e_mexe_so_no_nucleo_libretro(self):
        for bruto, texto in self.remendos():
            self.assertNotIn(b"\r", bruto)
            arquivos = re.findall(r"^(?:---|\+\+\+) (\S+)", texto, re.M)
            self.assertEqual(arquivos, ["a/pcsx2-libretro/Main.cpp", "b/pcsx2-libretro/Main.cpp"])

    def test_a_conta_de_linhas_de_cada_trecho_fecha(self):
        for bruto, texto in self.remendos():
            trechos = re.split(r"^(?=@@ )", texto, flags=re.M)[1:]
            self.assertGreaterEqual(len(trechos), 1)
            for trecho in trechos:
                cabeca, *linhas = trecho.split("\n")
                if linhas and linhas[-1] == "":
                    linhas.pop()
                achado = re.match(r"@@ -\d+(?:,(\d+))? \+\d+(?:,(\d+))? @@", cabeca)
                self.assertTrue(achado, cabeca)
                velho = int(achado.group(1) or 1)
                novo = int(achado.group(2) or 1)
                self.assertEqual(sum(1 for l in linhas if l[:1] in (" ", "-")), velho, cabeca)
                self.assertEqual(sum(1 for l in linhas if l[:1] in (" ", "+")), novo, cabeca)
        self.assertGreaterEqual(len(re.findall(r"^@@ ", self.texto, re.M)), 4)

    def test_o_remendo_dos_jogadores_faz_o_que_o_pedido_diz(self):
        self.assertIn('"Pad2", "Type", "DualShock2"', self.texto)                  # o jogador 2 ligado no PS2
        self.assertIn("MultitapPort0_Enabled", self.texto)                          # o multitap da porta 1
        self.assertIn("input_state_cb(jogador, RETRO_DEVICE_JOYPAD", self.texto)    # uma porta do libretro por jogador
        self.assertNotIn("+				pad->Set(m.ds2, input_state_cb(0,", self.texto)
        self.assertIn("+	bool support_no_game = true;", self.texto)                 # abrir sem jogo: o menu da BIOS

    def test_o_remendo_da_sobreposicao_le_o_arquivo_que_o_arena_escreve(self):
        # o mesmo nome, a mesma secao e o mesmo formato (Secao/Chave) de graficos.gravar_ajustes_do_armsx2
        self.assertIn('"arena-overrides.ini"', self.texto2)
        self.assertIn('GetKeyValueList("Overrides")', self.texto2)
        self.assertIn("rfind('/')", self.texto2)
        self.assertEqual(os.path.basename(graficos.arquivo_de_ajustes_do_armsx2("x")), "arena-overrides.ini")
        # entra DEPOIS dos ajustes proprios do nucleo e ANTES de salvar o .ini
        self.assertIn('+	// ARENA: os ajustes do servidor do ARENA, por cima do .ini do nucleo', self.texto2)
        self.assertIn(" 	Error save_error;", self.texto2)

    def test_o_remendo_do_status_grava_o_que_o_arena_le(self):
        # o nome do arquivo e as chaves sao os de graficos.ler_status_do_armsx2 (ARENA do Android)
        self.assertIn('"arena-status.json"', self.texto3)
        self.assertIn("Host::OnPerformanceMetricsUpdated", self.texto3)
        self.assertIn("TryGetWindowSnapshot", self.texto3)
        for chave in graficos.CHAVES_DO_STATUS_DO_ARMSX2:
            self.assertIn('\\"%s\\":' % chave, self.texto3, chave)

    def test_a_ordem_alfabetica_poe_os_jogadores_primeiro(self):
        nomes = sorted(n for n in os.listdir(self.PASTA) if n.endswith(".patch"))
        self.assertEqual(nomes, ["armsx2-libretro-jogadores.patch", "armsx2-libretro-sobreposicao-do-arena.patch",
                                 "armsx2-libretro-status-do-arena.patch"])

    def test_o_fluxo_do_github_confere_e_aplica_o_remendo_antes_de_compilar(self):
        with open(os.path.join(RAIZ, ".github", "workflows", "nucleo-ps2-android.yml"), encoding="utf-8") as arquivo:
            fluxo = arquivo.read()
        self.assertIn("git apply --check", fluxo)
        self.assertIn("ferramentas/remendos", fluxo)
        self.assertLess(fluxo.index("Aplicar os remendos"), fluxo.index("Compilar as dependencias"))
        self.assertIn("-march=armv8-a -moutline-atomics", fluxo)                    # roda no Cortex-A53
        self.assertIn("ARMSX2_COMMIT: 90126bdfea7a3ffb1fd288b2f7f0ae0b033af2d6", fluxo)


if __name__ == "__main__":
    unittest.main()
