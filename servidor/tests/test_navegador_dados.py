# -*- coding: utf-8 -*-
"""O ARENA no navegador (o Chromebook, item 12 do plano de 15/10/2026).

Aqui so o que se confere sem abrir navegador: os dados que a versao do
navegador tira do servidor (launcher\\navegador\\dados.js) estao em dia e nao
levam nada desta maquina; cada nucleo do navegador tem a pasta de saves do
Windows; o indexador grava a lista tambem para o navegador (dados\\manifesto.js);
a conversao dos nucleos do libretro para abrir de file://. O teste de verdade,
com a tela e os jogos rodando no Edge, no Chrome e no Firefox, e'
testes\\teste_chromebook.py.
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ = os.path.dirname(PASTA_SERVIDOR)
if PASTA_SERVIDOR not in sys.path:
    sys.path.insert(0, PASTA_SERVIDOR)
FERRAMENTAS = os.path.join(RAIZ, "ferramentas")
if FERRAMENTAS not in sys.path:
    sys.path.insert(0, FERRAMENTAS)

import montar_navegador  # noqa: E402
import preparar_nucleos_navegador  # noqa: E402

DADOS_JS = os.path.join(RAIZ, "launcher", "navegador", "dados.js")


def ler_dados():
    # O git do Windows pode trocar o fim de linha no checkout (LF -> CRLF):
    # para o navegador e para a comparacao, tanto faz.
    with open(DADOS_JS, encoding="utf-8") as arquivo:
        texto = arquivo.read().replace("\r\n", "\n")
    return texto, json.loads(texto[texto.index("= ") + 2:texto.rindex(";")])


class DadosDoNavegador(unittest.TestCase):
    def test_em_dia_com_o_servidor(self):
        texto, _dados = ler_dados()
        self.assertEqual(texto, montar_navegador.montar(),
                         "launcher\\navegador\\dados.js desatualizado: rode ferramentas\\montar_navegador.py")

    def test_nada_desta_maquina(self):
        texto, _dados = ler_dados()
        for proibido in (RAIZ, RAIZ.replace("\\", "\\\\"), "C:\\\\Users", "AppData", os.environ.get("USERNAME") or "#"):
            self.assertNotIn(proibido, texto)

    def test_opcoes_do_retroarch_sem_as_do_windows(self):
        base = ler_dados()[1]["base_retroarch"]
        for chave in montar_navegador.FORA_DO_NAVEGADOR:
            self.assertNotIn(chave, base)
        # As mesmas do Windows: o menu em portugues (7) e as teclas do ARENA;
        # a gravacao e a transmissao desligadas (os dados dos alunos).
        self.assertEqual(base["user_language"], "7")
        self.assertEqual(base["input_exit_emulator"], "f10")
        self.assertEqual(base["input_menu_toggle"], "escape")
        self.assertEqual(base["quick_menu_show_start_recording"], "false")
        self.assertEqual(base["quick_menu_show_start_streaming"], "false")

    def test_todo_nucleo_do_navegador_tem_a_pasta_de_saves(self):
        dados = ler_dados()[1]
        nucleos = {p["core_navegador"] for p in dados["consoles"] if p.get("core_navegador")}
        self.assertTrue(nucleos)
        self.assertEqual(sorted(nucleos - set(dados["pasta_do_nucleo"])), [])

    def test_a_pasta_e_o_corename_do_info(self):
        pasta_info = os.path.join(RAIZ, "retroarch", "info")
        if not os.path.isdir(pasta_info):
            self.skipTest("sem retroarch\\info nesta copia")
        import cheats
        for nucleo, pasta in montar_navegador.PASTA_DO_NUCLEO.items():
            info = os.path.join(pasta_info, nucleo + "_libretro.info")
            if os.path.isfile(info):
                self.assertEqual(cheats.nome_do_nucleo(nucleo + "_libretro.dll", pasta_info), pasta, nucleo)

    def test_livres_conferem_e_tem_nucleo(self):
        jogos = json.loads(montar_navegador.montar_livres().split("= ", 1)[1].rstrip().rstrip(";"))
        self.assertEqual(sorted(j["plataforma"] for j in jogos),
                         ["arduboy", "chip8", "microw8", "plus4", "vic20"])
        for jogo in jogos:
            self.assertTrue(jogo["licenca"])
            self.assertTrue(jogo["dados"])


class ManifestoDoNavegador(unittest.TestCase):
    """O indexador grava a lista tambem como script (dados\\manifesto.js):
    a pagina aberta do pen drive le sem permissao nenhuma."""

    def setUp(self):
        import indexador
        import jogadores
        self.indexador, self.jogadores = indexador, jogadores
        self.dir = tempfile.mkdtemp(prefix="arena_manifesto_js_")
        self.antigos = (indexador.PASTA_JOGOS, indexador.PASTA_DADOS, indexador.ARQUIVO_MANIFESTO,
                        jogadores.ARQUIVO, indexador.RAIZ)
        indexador.RAIZ = self.dir
        indexador.PASTA_JOGOS = os.path.join(self.dir, "jogos")
        indexador.PASTA_DADOS = os.path.join(self.dir, "dados")
        indexador.ARQUIVO_MANIFESTO = os.path.join(self.dir, "dados", "manifesto.json")
        jogadores.ARQUIVO = os.path.join(self.dir, "NAO_DEVIA_EXISTIR.txt")
        jogo = os.path.join(indexador.PASTA_JOGOS, "pessoais", "NES", "Aventura Livre (USA).nes")
        os.makedirs(os.path.dirname(jogo))
        with open(jogo, "wb") as arquivo:
            arquivo.write(b"NES\x1a" + bytes(40))

    def tearDown(self):
        (self.indexador.PASTA_JOGOS, self.indexador.PASTA_DADOS, self.indexador.ARQUIVO_MANIFESTO,
         self.jogadores.ARQUIVO, self.indexador.RAIZ) = self.antigos
        shutil.rmtree(self.dir, ignore_errors=True)

    def ler(self, nome):
        with open(os.path.join(self.dir, "dados", nome), encoding="utf-8") as arquivo:
            return arquivo.read()

    def test_mesma_lista_embrulhada(self):
        self.indexador.indexar(forcar=True)
        self.assertEqual(self.ler("manifesto.js"), "window.ARENA_MANIFESTO = %s;\n" % self.ler("manifesto.json"))
        lista = json.loads(self.ler("manifesto.js")[len("window.ARENA_MANIFESTO = "):-2])
        self.assertEqual([j["titulo"] for j in lista["jogos"]], ["Aventura Livre"])

    def test_volta_quando_some(self):
        self.indexador.indexar(forcar=True)
        os.remove(os.path.join(self.dir, "dados", "manifesto.js"))
        resultado = self.indexador.indexar()          # nada mudou: reaproveita a lista
        self.assertTrue(resultado.get("reaproveitado"))
        self.assertIn('"Aventura Livre"', self.ler("manifesto.js"))


class ConversaoDosNucleos(unittest.TestCase):
    """O nucleo do libretro vem como modulo ES; vira script comum."""
    MODULO = ("// To work around a bug\nvar setImmediate;\n\nvar libretro_fceumm = (() => {\n"
              "  var _scriptDir = import.meta.url;\n  return (function(moduleArg = {}) {\n"
              "wasmBinaryFile=new URL(\"fceumm_libretro.wasm\",import.meta.url).href; return moduleArg; });\n"
              "})();\nexport default libretro_fceumm;\n")

    def test_vira_script_comum(self):
        texto = preparar_nucleos_navegador.script_comum(self.MODULO, "fceumm")
        self.assertNotIn("import.meta", texto)
        self.assertNotIn("export default", texto)
        self.assertIn('(window.ARENA_NUCLEOS = window.ARENA_NUCLEOS || {})["fceumm"] = libretro_fceumm;', texto)
        self.assertIn("document.currentScript", texto)

    def test_para_se_o_libretro_mudar_o_formato(self):
        with self.assertRaises(ValueError):
            preparar_nucleos_navegador.script_comum(self.MODULO.replace("var _scriptDir = import.meta.url;", ""), "x")
        with self.assertRaises(ValueError):
            preparar_nucleos_navegador.script_comum(self.MODULO.replace("export default libretro_fceumm;", ""), "x")

    def test_wasm_compactado_volta_igual(self):
        import base64
        import gzip
        dados = bytes(range(256)) * 50
        texto, _tamanho = preparar_nucleos_navegador.wasm_em_script(dados, "fceumm")
        codigo = texto.split('= "', 1)[1].rsplit('"', 1)[0]
        self.assertEqual(gzip.decompress(base64.b64decode(codigo)), dados)


class TelaDoNavegador(unittest.TestCase):
    def test_servidor_do_navegador_carrega_antes_da_tela(self):
        with open(os.path.join(RAIZ, "launcher", "index.html"), encoding="utf-8") as arquivo:
            html = arquivo.read()
        self.assertLess(html.index('<script src="navegador/servidor.js">'), html.index('<script src="app.js">'))

    def test_no_windows_o_servidor_do_navegador_nao_faz_nada(self):
        with open(os.path.join(RAIZ, "launcher", "navegador", "servidor.js"), encoding="utf-8") as arquivo:
            texto = arquivo.read()
        self.assertIn('location.protocol === "file:" || busca.get("navegador") === "1"', texto)
        self.assertIn("if (!noNavegador) return;", texto)

    def test_entrada_do_chromebook(self):
        with open(os.path.join(RAIZ, "ARENA-CHROMEBOOK.html"), encoding="utf-8") as arquivo:
            self.assertIn('url=launcher/index.html', arquivo.read())


if __name__ == "__main__":
    unittest.main()
