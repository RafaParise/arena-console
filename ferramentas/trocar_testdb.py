r"""Troca a classe TestDB de servidor\tests\run.py: os testes de banco passam a
testar o codigo que roda de verdade (arena.py), e nao a copia servidor\db.py,
que o ARENA nunca importava (removida com aprovacao do Rafael em 25/09/2026).
Roda uma vez so.
"""
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQUIVO = os.path.join(RAIZ, "servidor", "tests", "run.py")

NOVA = '''# ============================================================================
# 5. Banco (arena.py)
# ============================================================================
# Ate 25/09/2026 esta classe testava servidor\\db.py, uma COPIA das funcoes de
# banco que o ARENA nunca importava -- a bateria passava mesmo com o codigo de
# verdade diferente. Agora testa o arena.py, pelas mesmas funcoes que ele usa
# para gravar (inserir_placar...), e a marca de sincronizacao por numero de
# chegada ("seq:N"), nao por data.

class TestDB(unittest.TestCase):

    def setUp(self):
        import arena
        self.mod = arena
        self.dir = pasta_temp()
        self._old_pd = self.mod.PASTA_DADOS
        self._old_ab = self.mod.ARQUIVO_BANCO
        self.mod.PASTA_DADOS = self.dir
        self.mod.ARQUIVO_BANCO = os.path.join(self.dir, "arena.db")
        self.mod.preparar_banco()

    def tearDown(self):
        self.mod.PASTA_DADOS = self._old_pd
        self.mod.ARQUIVO_BANCO = self._old_ab
        shutil.rmtree(self.dir, ignore_errors=True)

    def placar(self, uuid, apelido, pontos, dispositivo="d1", enviado=0):
        with self.mod.banco() as c:
            return self.mod.inserir_placar(
                c, uuid, apelido, "j1", "Jogo", pontos,
                "2026-01-01T00:00:00Z", dispositivo, enviado)

    def test_schema(self):
        with self.mod.banco() as c:
            tabelas = {l[0] for l in c.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
            colunas = {l[1] for l in c.execute("PRAGMA table_info(placar)")}
        self.assertTrue({"placar", "sessao", "contador"} <= tabelas)
        self.assertIn("seq", colunas)

    def test_insert_e_select(self):
        self.placar("abc", "pedro", 1000)
        with self.mod.banco() as c:
            row = c.execute(
                "SELECT * FROM placar WHERE apelido='pedro'").fetchone()
        self.assertEqual(row["pontos"], 1000)
        self.assertIsNotNone(row["seq"])

    def test_insert_or_ignore(self):
        self.assertEqual(self.placar("abc", "ana", 500, enviado=1), 1)
        self.assertEqual(self.placar("abc", "ana", 500, enviado=1), 0)
        with self.mod.banco() as c:
            n = c.execute(
                "SELECT COUNT(*) FROM placar WHERE uuid='abc'").fetchone()[0]
        self.assertEqual(n, 1)

    def test_marcar_enviados(self):
        self.placar("x1", "bia", 300)
        self.mod.marcar_enviados([{"uuid": "x1"}], [])
        with self.mod.banco() as c:
            row = c.execute(
                "SELECT enviado FROM placar WHERE uuid='x1'").fetchone()
        self.assertEqual(row["enviado"], 1)

    def test_registros_desde(self):
        self.placar("r1", "carlos", 900, "d3")
        _p, _s, marca = self.mod.registros_desde("")
        self.assertTrue(marca.startswith("seq:"))
        self.placar("r2", "daniel", 1200, "d3")
        placares, sessoes, _ = self.mod.registros_desde(marca)
        self.assertEqual([p["apelido"] for p in placares], ["daniel"])

    def test_integrity(self):
        with self.mod.banco() as c:
            self.assertEqual(c.execute(
                "PRAGMA integrity_check").fetchone()[0], "ok")


'''

with open(ARQUIVO, encoding="utf-8") as f:
    texto = f.read()
padrao = re.compile(r"# =+\n# 5\. db\.py\n# =+\n\nclass TestDB\(unittest\.TestCase\):.*?(?=\n# =+\n)",
                    re.S)
novo, n = padrao.subn(lambda _m: NOVA.rstrip("\n") + "\n", texto)
if n != 1:
    raise SystemExit("Bloco TestDB nao encontrado do jeito esperado (achados: %d). Nada mudou." % n)
with open(ARQUIVO, "w", encoding="utf-8", newline="") as f:
    f.write(novo)
print("TestDB trocado.")
