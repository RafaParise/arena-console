# -*- coding: utf-8 -*-
"""O icone oficial do ARENA, o supercontrole (ferramentas\\gerar_icone.py, docs\\ICONE.md).

Pedido do Rafael de 23/10/2026: um controle que junta todos (o Xbox Duke com tres
pernas do Nintendo 64, dois analogicos a esquerda e um so a direita, os quatro
botoes de sempre e os botoes especiais do Nintendo 64 e do GameCube), como icone
em todas as versoes. O teste confere o que foi pedido, que os arquivos existem
com o tamanho certo, que o SVG do repositorio e' o que o gerador produz hoje e
que cada versao do ARENA liga o icone."""
import ast
import importlib.util
import json
import os
import re
import struct
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ = os.path.dirname(PASTA_SERVIDOR)
FERRAMENTAS = os.path.join(RAIZ, "ferramentas")
if FERRAMENTAS not in sys.path:
    sys.path.insert(0, FERRAMENTAS)
sys.path.insert(0, os.path.join(RAIZ, "testes"))

import gerar_icone  # noqa: E402
import limpeza  # noqa: E402

ICONES = os.path.join(RAIZ, "docs", "imagens", "icone")
SVG_NS = "{http://www.w3.org/2000/svg}"


def caminho(*partes):
    return os.path.join(RAIZ, *partes)


def tamanho_do_png(arquivo):
    with open(arquivo, "rb") as f:
        dados = f.read(33)
    assert dados[:8] == b"\x89PNG\r\n\x1a\n", arquivo
    largura, altura = struct.unpack(">II", dados[16:24])
    return largura, altura


def svg_do_repositorio(*partes):
    with open(caminho(*partes), encoding="utf-8") as f:
        return f.read()


def ids_do_svg(texto):
    return {e.get("id"): e for e in ET.fromstring(texto).iter() if e.get("id")}


class OQueFoiPedido(unittest.TestCase):
    """O desenho tem cada coisa que o Rafael descreveu."""

    def setUp(self):
        self.completo = ids_do_svg(svg_do_repositorio("docs", "imagens", "icone", "arena-icone.svg"))
        self.simples = ids_do_svg(svg_do_repositorio("docs", "imagens", "icone", "arena-icone-pequeno.svg"))

    def test_tres_analogicos_dois_a_esquerda_e_um_so_a_direita(self):
        for versao in (self.completo, self.simples):
            self.assertIn("analogico-esquerdo", versao)
            self.assertIn("analogico-do-meio", versao)       # o do Nintendo 64, na ponta do meio
            self.assertIn("analogico-direito", versao)       # um so
            self.assertEqual([i for i in versao if i.startswith("analogico-")].__len__(), 3)

    def test_os_analogicos_ficam_no_lugar_certo(self):
        def centro(elemento):
            if elemento.tag == SVG_NS + "g":
                achou = re.search(r"translate\(([\d.]+),([\d.]+)\)", elemento.get("transform", ""))
                return float(achou.group(1)), float(achou.group(2))
            return float(elemento.get("cx")), float(elemento.get("cy"))
        for versao in (self.completo, self.simples):
            esquerdo, meio, direito = (centro(versao[i]) for i in ("analogico-esquerdo", "analogico-do-meio", "analogico-direito"))
            self.assertLess(esquerdo[0], meio[0])            # dois a esquerda do centro do corpo (200)...
            self.assertLessEqual(meio[0], 200)
            self.assertGreater(direito[0], 250)              # ...e um so na metade da direita
            self.assertGreater(meio[1], esquerdo[1])         # o do meio fica na ponta de baixo

    def test_quatro_botoes_com_as_cores_do_xbox(self):
        botoes = self.completo["botoes-xyab"].findall(SVG_NS + "circle")
        self.assertEqual(len(botoes), 4)
        self.assertEqual([b.get("fill") for b in botoes], ["url(#ambar)", "url(#azul)", "url(#vermelho)", "url(#verde)"])
        maior = max(botoes, key=lambda b: float(b.get("r")))
        self.assertEqual(maior.get("fill"), "url(#verde)")   # o A, maior, como o do GameCube

    def test_os_botoes_especiais_do_n64_do_gamecube_e_do_duke(self):
        self.assertEqual(len(self.completo["botoes-c-do-n64"].findall(SVG_NS + "circle")), 4)
        for peca in ("start-do-n64", "z-gamecube", "botao-branco-do-duke", "botao-preto-do-duke", "direcional",
                     "joia-do-arena", "gatilho-esquerdo", "gatilho-direito", "corpo-de-tres-pontas"):
            self.assertIn(peca, self.completo)
        self.assertEqual(self.completo["z-gamecube"].get("fill"), "#8a63ff")      # o Z roxo

    def test_a_versao_simples_so_tem_o_que_aparece_pequeno(self):
        for peca in ("start-do-n64", "z-gamecube", "botoes-c-do-n64", "botao-branco-do-duke", "gatilho-esquerdo"):
            self.assertNotIn(peca, self.simples)
        for peca in ("corpo-de-tres-pontas",):
            self.assertNotIn(peca, self.simples)        # a silhueta existe, mas sem id duplicado na simples
        self.assertIn("botoes-xyab", self.simples)
        self.assertIn("joia-do-arena", self.simples)

    def test_o_corpo_tem_tres_pontas(self):
        # o caminho tem tres "lombos" que descem: tres arcos terminando abaixo de y=330
        pontas = re.findall(r"C\d+,\d+ \d+,\d+ (\d+),(3[2-7]\d)", gerar_icone.SILHUETA)
        self.assertGreaterEqual(len(pontas), 3)


class SVGDeVerdade(unittest.TestCase):

    ARQUIVOS = ("docs/imagens/icone/arena-icone.svg", "docs/imagens/icone/arena-icone-pequeno.svg",
                "docs/imagens/icone/arena-supercontrole.svg", "launcher/arena-icone.svg",
                "launcher/arena-icone-pequeno.svg")

    def test_bem_formado_e_sem_nada_de_fora(self):
        for arquivo in self.ARQUIVOS:
            texto = svg_do_repositorio(*arquivo.split("/"))
            raiz = ET.fromstring(texto)
            self.assertEqual(raiz.tag, SVG_NS + "svg", arquivo)
            self.assertEqual(raiz.get("viewBox"), "0 0 512 512", arquivo)
            for proibido in ("<script", "onload", "onclick", "foreignObject", "<image", "xlink:href", "http://", "https://"):
                # o unico endereco permitido e' o do namespace do proprio SVG
                self.assertNotIn(proibido, texto.replace('xmlns="http://www.w3.org/2000/svg"', ""), (arquivo, proibido))

    def test_o_gerador_e_a_fonte_o_svg_do_repositorio_e_o_que_ele_produz(self):
        # sem isto, alguem mexe no SVG a mao, ou muda o gerador e esquece de rodar
        self.assertEqual(svg_do_repositorio("docs", "imagens", "icone", "arena-icone.svg"), gerar_icone.svg("completo", 512))
        self.assertEqual(svg_do_repositorio("docs", "imagens", "icone", "arena-icone-pequeno.svg"), gerar_icone.svg("simples", 512))
        self.assertEqual(svg_do_repositorio("docs", "imagens", "icone", "arena-supercontrole.svg"),
                         gerar_icone.svg("so-controle", 512, escala=0.80))
        for nome in ("arena-icone.svg", "arena-icone-pequeno.svg"):
            self.assertEqual(svg_do_repositorio("launcher", nome), svg_do_repositorio("docs", "imagens", "icone", nome))

    def test_o_gerador_so_usa_a_biblioteca_padrao(self):
        with open(caminho("ferramentas", "gerar_icone.py"), encoding="utf-8") as f:
            arvore = ast.parse(f.read())
        usados = set()
        for no in ast.walk(arvore):
            if isinstance(no, ast.Import):
                usados |= {a.name.split(".")[0] for a in no.names}
            elif isinstance(no, ast.ImportFrom) and no.module:
                usados.add(no.module.split(".")[0])
        self.assertLessEqual(usados, set(sys.stdlib_module_names), usados - set(sys.stdlib_module_names))


class ArquivosGerados(unittest.TestCase):

    def test_os_png_tem_o_tamanho_do_nome(self):
        esperados = {"launcher/arena-icone-64.png": 64, "launcher/arena-icone-192.png": 192,
                     "ferramentas/site/icone-192.png": 192, "ferramentas/site/icone-512.png": 512,
                     "docs/imagens/icone/arena-icone-512.png": 512, "docs/imagens/icone/arena-icone-1024.png": 1024,
                     "docs/imagens/icone/arena-supercontrole-512.png": 512}
        for pasta, comum, frente in (("mipmap-mdpi", 48, 108), ("mipmap-hdpi", 72, 162), ("mipmap-xhdpi", 96, 216),
                                     ("mipmap-xxhdpi", 144, 324), ("mipmap-xxxhdpi", 192, 432)):
            esperados["docs/imagens/icone/android/%s/ic_launcher.png" % pasta] = comum
            esperados["docs/imagens/icone/android/%s/ic_launcher_foreground.png" % pasta] = frente
        for arquivo, lado in esperados.items():
            self.assertEqual(tamanho_do_png(caminho(*arquivo.split("/"))), (lado, lado), arquivo)

    def test_o_ico_do_windows_tem_os_sete_tamanhos_em_png(self):
        with open(caminho("launcher", "arena.ico"), "rb") as f:
            dados = f.read()
        reservado, tipo, quantas = struct.unpack("<HHH", dados[:6])
        self.assertEqual((reservado, tipo, quantas), (0, 1, 7))
        lados = []
        for i in range(quantas):
            lado, _, _, _, _, bits, tamanho, deslocamento = struct.unpack("<BBBBHHII", dados[6 + 16 * i:22 + 16 * i])
            lado = lado or 256
            self.assertEqual(bits, 32)
            self.assertEqual(dados[deslocamento:deslocamento + 8], b"\x89PNG\r\n\x1a\n")
            self.assertEqual(struct.unpack(">II", dados[deslocamento + 16:deslocamento + 24]), (lado, lado))
            lados.append(lado)
        self.assertEqual(lados, [16, 24, 32, 48, 64, 128, 256])

    def test_transparencia_onde_tem_que_ter(self):
        def pixel(arquivo, x, y):
            largura, _altura, rgba = gerar_icone.ler_png(caminho(*arquivo.split("/")))
            return tuple(rgba[(y * largura + x) * 4:(y * largura + x) * 4 + 4])
        # a frente do icone adaptavel e o controle sozinho: o canto e' transparente e o meio tem cor
        frente = "docs/imagens/icone/android/mipmap-xxxhdpi/ic_launcher_foreground.png"
        self.assertEqual(pixel(frente, 0, 0)[3], 0)
        self.assertEqual(pixel(frente, 216, 200)[3], 255)
        # o icone comum e' o quadradinho de cantos redondos: canto transparente
        self.assertEqual(pixel("docs/imagens/icone/android/mipmap-xxxhdpi/ic_launcher.png", 0, 0)[3], 0)
        # o do site/Chromebook e' a tela inteira (o sistema recorta o formato): sem canto transparente
        self.assertEqual(pixel("ferramentas/site/icone-512.png", 0, 0)[3], 255)
        self.assertEqual(pixel("ferramentas/site/icone-192.png", 0, 0)[3], 255)

    def test_o_controle_nao_sai_da_zona_segura_do_icone_adaptavel(self):
        # No Android, so o circulo do meio (uns 61% do quadro) aparece em todo formato de icone.
        largura, altura, rgba = gerar_icone.ler_png(caminho("docs", "imagens", "icone", "android", "mipmap-xxxhdpi",
                                                            "ic_launcher_foreground.png"))
        zona = 0.61 * largura / 2
        centro = largura / 2.0
        for y in range(0, altura, 3):
            for x in range(0, largura, 3):
                if rgba[(y * largura + x) * 4 + 3] > 200:
                    self.assertLessEqual(((x - centro) ** 2 + (y - centro) ** 2) ** 0.5, zona + 4, (x, y))

    def test_o_manifest_do_site_aponta_para_icones_do_tamanho_que_diz(self):
        with open(caminho("ferramentas", "site", "manifest.webmanifest"), encoding="utf-8") as f:
            manifest = json.load(f)
        self.assertTrue(manifest["icons"])
        for icone in manifest["icons"]:
            lado = int(icone["sizes"].split("x")[0])
            self.assertEqual(tamanho_do_png(caminho("ferramentas", "site", icone["src"])), (lado, lado))


class CadaVersaoLigaOIcone(unittest.TestCase):

    def test_a_tela_do_arena(self):
        html = svg_do_repositorio("launcher", "index.html")
        for arquivo in re.findall(r'<link rel="(?:icon|apple-touch-icon)" href="([^"]+)"', html):
            self.assertTrue(os.path.isfile(caminho("launcher", arquivo)), arquivo)
        self.assertIn('href="arena-icone-pequeno.svg"', html)
        self.assertIn('href="arena.ico"', html)
        self.assertIn('href="arena-icone-192.png"', html)
        cabecalho = re.search(r'<img class="marca-icone" src="([^"]+)"', html)
        self.assertIsNotNone(cabecalho)
        self.assertTrue(os.path.isfile(caminho("launcher", cabecalho.group(1) if cabecalho else "")))
        self.assertIn(".marca-icone", svg_do_repositorio("launcher", "estilo.css"))

    def test_o_chromebook(self):
        html = svg_do_repositorio("ARENA-CHROMEBOOK.html")
        achados = re.findall(r'<link rel="(?:icon|apple-touch-icon)" href="([^"]+)"', html)
        self.assertGreaterEqual(len(achados), 2)
        for arquivo in achados:
            self.assertTrue(os.path.isfile(caminho(*arquivo.split("/"))), arquivo)

    def test_o_servidor_serve_os_tipos_do_icone(self):
        import arena
        for extensao, tipo in ((".svg", "image/svg+xml"), (".png", "image/png"), (".ico", "image/x-icon")):
            self.assertEqual(arena.TIPOS.get(extensao), tipo)

    def test_o_apk_copia_os_icones_e_poe_o_fundo(self):
        especificacao = importlib.util.spec_from_file_location("montar_android_do_teste", caminho("ferramentas", "montar_android.py"))
        montar = importlib.util.module_from_spec(especificacao)
        especificacao.loader.exec_module(montar)
        pasta = tempfile.mkdtemp(prefix="arena_icone_")
        try:
            os.makedirs(os.path.join(pasta, "values"))
            with open(os.path.join(pasta, "values", "colors.xml"), "w", encoding="utf-8") as f:
                f.write('<resources>\n<color name="ic_launcher_background">#123456</color>\n</resources>\n')
            montar.gerar_icones(pasta)
            for mipmap, _comum, _frente in montar.TAMANHOS_DO_ICONE:
                for nome in ("ic_launcher.png", "ic_launcher_foreground.png"):
                    with open(os.path.join(pasta, mipmap, nome), "rb") as copiado, \
                            open(os.path.join(ICONES, "android", mipmap, nome), "rb") as original:
                        self.assertEqual(copiado.read(), original.read(), (mipmap, nome))
            with open(os.path.join(pasta, "values", "colors.xml"), encoding="utf-8") as f:
                self.assertIn('>%s</color>' % montar.COR_DO_FUNDO_DO_ICONE, f.read())
        finally:
            limpeza.apagar_pasta(pasta)


@unittest.skipUnless(os.name == "nt", "o atalho .lnk e' do Windows")
class AtalhoDoWindows(unittest.TestCase):

    def test_o_atalho_leva_ao_arena_bat_com_o_icone(self):
        import subprocess
        pasta = tempfile.mkdtemp(prefix="arena_atalho_")
        try:
            feito = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                                    caminho("ferramentas", "criar_atalho.ps1"), pasta],
                                   capture_output=True, text=True, timeout=60, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            self.assertEqual(feito.returncode, 0, feito.stderr)
            atalho = os.path.join(pasta, "ARENA.lnk")
            self.assertTrue(os.path.isfile(atalho))
            # o PowerShell escreve na pagina de codigo do console: pede UTF-8 para o "Pedagogicos" voltar certo
            lido = subprocess.run(["powershell", "-NoProfile", "-Command",
                                   "[Console]::OutputEncoding=[Text.Encoding]::UTF8;"
                                   "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%s');"
                                   "$s.TargetPath;$s.WorkingDirectory;$s.IconLocation" % atalho.replace("'", "''")],
                                  capture_output=True, text=True, encoding="utf-8", timeout=60,
                                  creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            alvo, trabalho, icone = (linha.strip() for linha in lido.stdout.strip().splitlines()[:3])
            self.assertEqual(os.path.normcase(alvo), os.path.normcase(caminho("ARENA.bat")))
            self.assertEqual(os.path.normcase(trabalho), os.path.normcase(RAIZ))
            self.assertEqual(os.path.normcase(icone), os.path.normcase(caminho("launcher", "arena.ico") + ",0"))
        finally:
            limpeza.apagar_pasta(pasta)

    def test_pasta_que_nao_existe_da_erro_claro(self):
        import subprocess
        feito = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                                caminho("ferramentas", "criar_atalho.ps1"), os.path.join(tempfile.gettempdir(), "nao_existe_arena_xyz")],
                               capture_output=True, text=True, errors="replace",       # o "Pedagógicos" do caminho vem na página do console, não em UTF-8 (com python -X utf8, sem isto, o stderr vinha None)
                               timeout=60, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        self.assertNotEqual(feito.returncode, 0)
        self.assertIn("nao existe", feito.stderr)

    def test_o_bat_chama_o_script_e_e_so_ascii(self):
        with open(caminho("CRIAR-ATALHO.bat"), "rb") as f:
            dados = f.read()
        dados.decode("ascii")                      # o cmd do Windows nao entende acento em .bat sem chcp
        self.assertIn(b"ferramentas\\criar_atalho.ps1", dados)
        with open(caminho("ferramentas", "criar_atalho.ps1"), "rb") as f:
            f.read().decode("ascii")               # o PowerShell 5 le arquivo sem BOM como ANSI


if __name__ == "__main__":
    unittest.main()
