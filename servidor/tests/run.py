# -*- coding: utf-8 -*-
"""
ARENA - Testes automatizados
============================
Rodar:  python servidor/tests/run.py

Sem 'pip install'. Só stdlib. Cada teste cria seus próprios arquivos
temporários e não toca no banco, catálogo ou configuração reais.
"""

import os
import sys
import tempfile
import shutil
import unittest
import time

# Permite importar os módulos do servidor a partir da raiz.
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def pasta_temp():
    return tempfile.mkdtemp(prefix="arena_test_")


# ============================================================================
# 1. indexador.py
# ============================================================================

class TestIndexador(unittest.TestCase):

    def setUp(self):
        import indexador
        self.mod = indexador
        self.dir = pasta_temp()
        self._old_pj = self.mod.PASTA_JOGOS
        self._old_pd = self.mod.PASTA_DADOS
        self.mod.PASTA_JOGOS = os.path.join(self.dir, "jogos")
        self.mod.PASTA_DADOS = os.path.join(self.dir, "dados")
        os.makedirs(self.mod.PASTA_JOGOS, exist_ok=True)
        os.makedirs(self.mod.PASTA_DADOS, exist_ok=True)

    def tearDown(self):
        self.mod.PASTA_JOGOS = self._old_pj
        self.mod.PASTA_DADOS = self._old_pd
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_limpar_titulo_varios_casos(self):
        casos = [
            ("super_jogo_(Brazil)_[!].sfc", "Super Jogo"),
            ("pokemon_fire_red.gba", "Pokemon Fire Red"),
            ("the_elder_scrolls.nes", "The Elder Scrolls"),
            ("jogo_sem_titulo", "Jogo Sem Titulo"),
            ("ABC.123.xyz", "ABC 123"),
            ("", "Sem titulo"),
            ("minha_coisa---[coisa].zip", "Minha Coisa"),
        ]
        for arquivo, esperado in casos:
            with self.subTest(arquivo=arquivo):
                self.assertEqual(self.mod.limpar_titulo(arquivo), esperado)

    def test_chave_ordenacao(self):
        casos = [
            ("Ácido", "acido"),
            ("Pôr do sol", "por do sol"),
            ("ÃE", "ae"),
            ("nao_acentuado", "nao_acentuado"),
        ]
        for texto, esperado in casos:
            with self.subTest(texto=texto):
                self.assertEqual(self.mod.chave_ordenacao(texto), esperado)

    def test_assinatura_das_pastas(self):
        os.makedirs(os.path.join(self.mod.PASTA_JOGOS, "livres"), exist_ok=True)
        antes = self.mod.assinatura_das_pastas()
        # Força mudança de mtime com os.utime (evita resolução do filesystem).
        caminho_dir = os.path.join(self.mod.PASTA_JOGOS, "livres")
        os.utime(caminho_dir, (time.time() + 60, time.time() + 60))
        depois = self.mod.assinatura_das_pastas()
        self.assertNotEqual(antes, depois)

    def test_ignorar(self):
        self.assertIn("leia.txt", self.mod.IGNORAR)
        self.assertIn("thumbs.db", self.mod.IGNORAR)


# ============================================================================
# 2. cheats.py
# ============================================================================

class TestCheats(unittest.TestCase):

    def setUp(self):
        import cheats
        self.mod = cheats
        self.dir = pasta_temp()
        self._old_raiz = self.mod.RAIZ
        self.mod.RAIZ = self.dir
        # As constantes de caminho sao calculadas no import — recalcula para
        # a pasta temporaria.
        self.mod.PASTA_RETROARCH = os.path.join(self.dir, "retroarch")
        self.mod.PASTA_STATES = os.path.join(self.mod.PASTA_RETROARCH, "states")
        self.mod.PASTA_SAVES = os.path.join(self.mod.PASTA_RETROARCH, "saves")
        self.mod.PASTA_CHEATS = os.path.join(self.mod.PASTA_RETROARCH, "cheats")
        self.cheats_pasta = os.path.join(self.mod.PASTA_CHEATS, "PlayStation")
        os.makedirs(self.cheats_pasta, exist_ok=True)
        self.jogo = {
            "arquivo": "jogos/pessoais/PS1/MeuJogo.iso",
            "plataforma_nome": "PlayStation",
            "titulo": "Meu Jogo",
        }

    def tearDown(self):
        self.mod.RAIZ = self._old_raiz
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_validar_codigo_formato_correto(self):
        casos = ["7E0DBE:09", "7E0DBE09 7E0DBF09", "4100:A000:8000:C0DE",
                 "12345678:ABCDEF01"]
        for codigo in casos:
            with self.subTest(codigo=codigo):
                limpo, erro = self.mod.validar_codigo(codigo)
                self.assertIsNone(erro, erro)
                self.assertIsNotNone(limpo)

    def test_validar_codigo_invalido(self):
        casos = [
            ("", "Digite o codigo."),
            ("XYZ", "Codigo invalido."),
            ("7E0DBE:ZZZ", "Codigo invalido."),
        ]
        for codigo, mensagem in casos:
            with self.subTest(codigo=codigo[:40]):
                limpo, erro = self.mod.validar_codigo(codigo)
                self.assertIsNone(limpo)
                self.assertIsNotNone(erro)
                self.assertIn(mensagem.split(".")[0], erro or "")

    def test_gravar_e_ler_cheats(self):
        cheats = [
            {"descricao": "Vidas infinitas", "codigo": "7E0DBE:09", "ligado": True},
            {"descricao": "Invencibilidade", "codigo": "7E0DBF:01", "ligado": False},
        ]
        caminho = self.mod.gravar_cheats(self.jogo, cheats)
        self.assertTrue(caminho.endswith(".cht"))
        self.assertTrue(os.path.isfile(caminho))

        lidos = self.mod.ler_cheats(self.jogo)
        self.assertEqual(len(lidos), 2)
        self.assertEqual(lidos[0]["descricao"], "Vidas infinitas")
        self.assertTrue(lidos[0]["ligado"])
        self.assertFalse(lidos[1]["ligado"])

        with open(caminho, encoding="utf-8") as f:
            texto = f.read()
        self.assertIn("cheats = 2", texto)
        self.assertIn("7E0DBE:09", texto)

    def test_adicionar_cheat(self):
        self.mod.gravar_cheats(self.jogo, [])
        novos, erro = self.mod.adicionar_cheat(
            self.jogo, "Vidas ilimitadas", "7E0DBE:09", ligado=True)
        self.assertIsNone(erro)
        self.assertEqual(len(novos), 1)
        self.assertEqual(novos[0]["descricao"], "Vidas ilimitadas")

    def test_limite_cheat(self):
        cheats = [{"descricao": f"C{i}", "codigo": "7E0DBE:09", "ligado": True}
                 for i in range(60)]
        self.mod.gravar_cheats(self.jogo, cheats)
        _, erro = self.mod.adicionar_cheat(self.jogo, "Extra", "1234:5678")
        self.assertIsNotNone(erro)
        self.assertIn("60", erro)

    def test_apagar_cheat(self):
        cheats = [
            {"descricao": "A", "codigo": "1111:2222", "ligado": True},
            {"descricao": "B", "codigo": "3333:4444", "ligado": False},
        ]
        self.mod.gravar_cheats(self.jogo, cheats)
        resultado, _ = self.mod.alterar_cheat(self.jogo, 0, apagar=True)
        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["descricao"], "B")

    def test_apagar_estado(self):
        states_pasta = os.path.join(self.dir, "retroarch", "states")
        os.makedirs(states_pasta, exist_ok=True)
        base = "MeuJogo"
        open(os.path.join(states_pasta, base + ".state"), "wb").close()
        todos = self.mod.listar_estados(self.jogo)
        self.assertTrue(todos[0]["existe"])
        self.assertTrue(self.mod.apagar_estado(self.jogo, 0))
        self.assertFalse(os.path.isfile(os.path.join(states_pasta,
                                                      base + ".state")))


# ============================================================================
# 3. controles.py
# ============================================================================

class TestControles(unittest.TestCase):

    def setUp(self):
        import controles
        self.mod = controles
        self.dir = pasta_temp()
        self._old_raiz = self.mod.RAIZ
        self.mod.RAIZ = self.dir
        self.dados_pasta = os.path.join(self.dir, "dados")
        os.makedirs(self.dados_pasta, exist_ok=True)
        with open(os.path.join(self.dados_pasta, "controles.json"), "w") as f:
            f.write("{}")

    def tearDown(self):
        self.mod.RAIZ = self._old_raiz
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_validar_teclado(self):
        casos = [
            ("x", ("x", None)),
            ("up", ("up", None)),
            ("z", ("z", None)),
            ("tecla_que_nao_existe", (None, "O RetroArch nao conhece")),
        ]
        for valor, esperado in casos:
            with self.subTest(valor=valor):
                limpo, erro = self.mod.validar("teclado", valor)
                if esperado[0] is None:
                    self.assertIsNone(limpo)
                    self.assertIsNotNone(erro)
                else:
                    self.assertIsNone(erro)
                    self.assertEqual(limpo, esperado[0])

    def test_validar_botao(self):
        self.assertEqual(self.mod.validar("botao", "0"), ("0", None))
        self.assertEqual(self.mod.validar("botao", "31"), ("31", None))
        limpo, erro = self.mod.validar("botao", "32")
        self.assertIsNone(limpo)
        self.assertIsNotNone(erro)

    def test_validar_hat(self):
        self.assertEqual(self.mod.validar("hat", "up"), ("h0up", None))
        self.assertEqual(self.mod.validar("hat", "h0down"), ("h0down", None))
        limpo, erro = self.mod.validar("hat", "diagonal")
        self.assertIsNone(limpo)

    def test_validar_eixo(self):
        self.assertEqual(self.mod.validar("eixo", "-0"), ("-0", None))
        self.assertEqual(self.mod.validar("eixo", "+1"), ("+1", None))
        limpo, erro = self.mod.validar("eixo", "0")
        self.assertIsNone(limpo)

    def test_definir_e_ler(self):
        dados, _ = self.mod.definir("1", "b", "teclado", "x")
        self.assertEqual(dados["1"]["b"], {"tipo": "teclado", "valor": "x"})
        dados2, _ = self.mod.definir("1", "a", "botao", "1")
        self.assertEqual(dados2["1"]["a"], {"tipo": "botao", "valor": "1"})
        lido = self.mod.ler()
        self.assertEqual(lido["1"]["b"], {"tipo": "teclado", "valor": "x"})

    def test_limpar(self):
        self.mod.definir("1", "b", "teclado", "x")
        self.mod.definir("2", "a", "botao", "0")
        self.mod.limpar("1")
        lido = self.mod.ler()
        self.assertNotIn("b", lido.get("1", {}))
        self.assertIn("a", lido.get("2", {}))

    def test_opcoes_do_retroarch(self):
        self.mod.definir("1", "b", "teclado", "x")
        self.mod.definir("1", "a", "botao", "1")
        opcoes = self.mod.opcoes_do_retroarch()
        self.assertEqual(opcoes["input_player1_b"], "x")
        self.assertEqual(opcoes["input_player1_a_btn"], "1")

    def test_padrao_teclado(self):
        dados, _ = self.mod.aplicar_padrao("1")
        self.assertEqual(dados["1"]["b"]["valor"], "z")
        self.assertEqual(dados["1"]["a"]["valor"], "x")
        self.assertEqual(dados["1"]["start"]["valor"], "enter")

    def test_padrao_controle(self):
        dados, _ = self.mod.aplicar_padrao_controle("1")
        self.assertEqual(dados["1"]["b"], {"tipo": "botao", "valor": "0"})
        self.assertNotIn("up", dados["1"])


# ============================================================================
# 4. hardware.py
# ============================================================================

class TestHardware(unittest.TestCase):

    def _caps(self, nucleos=2, ram=4, driver="vulkan", disco_classe="rapido",
              gpu_integrada=True):
        return {
            "nucleos": nucleos,
            "ram_total_gb": ram,
            "driver_video": driver,
            "disco": {"classe": disco_classe},
            "gpu": {"integrada": gpu_integrada, "nome": "fake",
                    "conhecida": True},
        }

    def test_capacidade_leve(self):
        import hardware
        caps = self._caps(nucleos=2, ram=4, disco_classe="lento")
        resultado = hardware.capacidade(caps)
        self.assertLessEqual(resultado["nota"], 2)

    def test_capacidade_forte(self):
        import hardware
        caps = self._caps(nucleos=8, ram=16, driver="vulkan",
                          disco_classe="muito_rapido", gpu_integrada=False)
        resultado = hardware.capacidade(caps)
        self.assertEqual(resultado["nota"], 5)
        self.assertEqual(resultado["nota_gpu"], 5)

    def test_gpu_integrada_limitada(self):
        import hardware
        caps = self._caps(nucleos=8, ram=16, gpu_integrada=True)
        resultado = hardware.capacidade(caps)
        self.assertLessEqual(resultado["nota_gpu"], 3)

    def test_classificar(self):
        import arena
        # classificar() lê CAPACIDADE["nota"] global — mock temporário.
        original = arena.CAPACIDADE
        try:
            arena.CAPACIDADE = {"nota": 5}
            c = arena.classificar(1)
            self.assertEqual(c["chave"], "otimo")
            arena.CAPACIDADE = {"nota": 3}
            c = arena.classificar(3)
            self.assertEqual(c["chave"], "bom")
            arena.CAPACIDADE = {"nota": 1}
            c = arena.classificar(3)
            self.assertEqual(c["chave"], "ruim")
        finally:
            arena.CAPACIDADE = original

    def test_driver_video(self):
        import hardware
        driver = hardware.driver_video()
        self.assertIn(driver, ("vulkan", "d3d11", "glcore"))


# ============================================================================
# 5. db.py
# ============================================================================

class TestDB(unittest.TestCase):

    def setUp(self):
        import db
        self.mod = db
        self.dir = pasta_temp()
        self._old_pd = self.mod.PASTA_DADOS
        self._old_ab = self.mod.ARQUIVO_BANCO
        self.mod.PASTA_DADOS = self.dir
        os.makedirs(self.mod.PASTA_DADOS, exist_ok=True)
        self.mod.ARQUIVO_BANCO = os.path.join(self.dir, "arena.db")
        self.mod.preparar_banco()

    def tearDown(self):
        self.mod.PASTA_DADOS = self._old_pd
        self.mod.ARQUIVO_BANCO = self._old_ab
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_schema(self):
        with self.mod.banco() as c:
            t1 = c.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='placar'"
            ).fetchone()
            t2 = c.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='sessao'"
            ).fetchone()
            self.assertIsNotNone(t1)
            self.assertIsNotNone(t2)

    def test_insert_e_select(self):
        with self.mod.banco() as c:
            c.execute(
                "INSERT INTO placar (uuid, apelido, jogo_id, jogo_titulo, "
                "pontos, registrado_em, dispositivo) VALUES (?,?,?,?,?,?,?)",
                ("abc", "pedro", "j1", "Super Jogo", 1000,
                 "2026-01-01T00:00:00.000Z", "dev1"))
            row = c.execute(
                "SELECT * FROM placar WHERE apelido='pedro'").fetchone()
            self.assertEqual(row["pontos"], 1000)

    def test_insert_or_ignore(self):
        reg = ("abc", "ana", "j1", "Jogo", 500, "2026-01-01T00:00:00Z", "d1")
        with self.mod.banco() as c:
            c.execute(
                "INSERT OR IGNORE INTO placar "
                "(uuid, apelido, jogo_id, jogo_titulo, pontos, registrado_em, "
                "dispositivo, enviado) VALUES (?,?,?,?,?,?,?,1)",
                reg)
            c.execute(
                "INSERT OR IGNORE INTO placar "
                "(uuid, apelido, jogo_id, jogo_titulo, pontos, registrado_em, "
                "dispositivo, enviado) VALUES (?,?,?,?,?,?,?,1)",
                reg)
        with self.mod.banco() as c:
            n = c.execute(
                "SELECT COUNT(*) FROM placar WHERE uuid='abc'").fetchone()[0]
            self.assertEqual(n, 1)

    def test_marcar_enviados(self):
        with self.mod.banco() as c:
            c.execute(
                "INSERT INTO placar (uuid, apelido, jogo_id, jogo_titulo, "
                "pontos, registrado_em, dispositivo) VALUES (?,?,?,?,?,?,?)",
                ("x1", "bia", "j2", "J2", 300, "2026-01-02T00:00:00Z", "d2"))
        self.mod.marcar_enviados([{"uuid": "x1"}], [])
        with self.mod.banco() as c:
            row = c.execute(
                "SELECT enviado FROM placar WHERE uuid='x1'").fetchone()
            self.assertEqual(row["enviado"], 1)

    def test_registros_desde(self):
        with self.mod.banco() as c:
            c.execute(
                "INSERT INTO placar (uuid, apelido, jogo_id, jogo_titulo, "
                "pontos, registrado_em, dispositivo) VALUES (?,?,?,?,?,?,?)",
                ("r1", "carlos", "j3", "J3", 900,
                 "2026-03-01T00:00:00.000Z", "d3"))
            c.execute(
                "INSERT INTO placar (uuid, apelido, jogo_id, jogo_titulo, "
                "pontos, registrado_em, dispositivo) VALUES (?,?,?,?,?,?,?)",
                ("r2", "daniel", "j3", "J3", 1200,
                 "2026-04-01T00:00:00.000Z", "d3"))
        desde = "2026-03-15T00:00:00.000Z"
        placares, sessoes, ate = self.mod.registros_desde(desde)
        self.assertEqual(len(placares), 1)
        self.assertEqual(placares[0]["apelido"], "daniel")

    def test_integrity(self):
        with self.mod.banco() as c:
            self.assertEqual(c.execute(
                "PRAGMA integrity_check").fetchone()[0], "ok")


# ============================================================================
# Runner
# ============================================================================

def main():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    pasta_testes = os.path.dirname(os.path.abspath(__file__))
    for nome in sorted(os.listdir(pasta_testes)):
        if not nome.startswith("test_") or not nome.endswith(".py"):
            continue
        if nome == "run.py":
            continue
        modulo = __import__(nome[:-3], fromlist=[""])
        suite.addTests(loader.loadTestsFromModule(modulo))

    suite.addTests(loader.loadTestsFromTestCase(TestIndexador))
    suite.addTests(loader.loadTestsFromTestCase(TestCheats))
    suite.addTests(loader.loadTestsFromTestCase(TestControles))
    suite.addTests(loader.loadTestsFromTestCase(TestHardware))
    suite.addTests(loader.loadTestsFromTestCase(TestDB))

    if suite.countTestCases() == 0:
        print("Nenhum teste encontrado.")
        return 1

    runner = unittest.TextTestRunner(verbosity=2)
    resultado = runner.run(suite)
    return 0 if resultado.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
