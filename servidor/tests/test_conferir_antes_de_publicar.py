# -*- coding: utf-8 -*-
"""ferramentas\\conferir_antes_de_publicar.py num repositorio de mentira
(pasta temporaria, sem internet). Confere que a ultima porta antes do GitHub
publico pega o que importa -- inclusive o que entrou num commit antigo e ja
saiu da pasta -- e nao reclama do texto normal do ARENA."""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, os.path.join(RAIZ, "ferramentas"))
import conferir_antes_de_publicar as conferir  # noqa: E402


def git(pasta, *argumentos):
    r = subprocess.run(["git", *argumentos], cwd=pasta, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise AssertionError("git %s: %s" % (" ".join(argumentos), r.stdout + r.stderr))
    return r.stdout.strip()


def escrever(pasta, nome, texto):
    caminho = os.path.join(pasta, nome)
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8", newline="\n") as arquivo:
        arquivo.write(texto)


@unittest.skipUnless(shutil.which("git"), "precisa do git instalado")
class TestConferirAntesDePublicar(unittest.TestCase):
    def setUp(self):
        self.base = tempfile.mkdtemp(prefix="arena_publicar_")
        self.repo = os.path.join(self.base, "repo")
        os.makedirs(self.repo)
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "config", "user.email", "teste@exemplo.invalid")
        git(self.repo, "config", "user.name", "Teste")
        git(self.repo, "config", "core.autocrlf", "false")
        escrever(self.repo, "LEIA-ME.md", "O ARENA abre com dois cliques.\n")
        git(self.repo, "add", "LEIA-ME.md")
        git(self.repo, "commit", "-q", "-m", "primeiro")

    def tearDown(self):
        conferir.RAIZ = RAIZ
        conferir.DESTINO = os.path.join(tempfile.gettempdir(), "arena_conferir_antes_de_publicar.json")
        shutil.rmtree(self.base, ignore_errors=True)

    def commitar(self, nome, texto, mensagem="mais um"):
        escrever(self.repo, nome, texto)
        git(self.repo, "add", nome)
        git(self.repo, "commit", "-q", "-m", mensagem)

    def rodar(self, *argumentos):
        conferir.RAIZ = self.repo
        conferir.DESTINO = os.path.join(self.base, "achados.json")
        saida = io.StringIO()
        if os.path.exists(conferir.DESTINO):
            os.remove(conferir.DESTINO)
        with redirect_stdout(saida):
            codigo = conferir.principal(list(argumentos) or ["main"])
        achados = {}
        if os.path.exists(conferir.DESTINO):
            with open(conferir.DESTINO, encoding="utf-8") as f:
                achados = json.load(f)
        return codigo, saida.getvalue(), achados

    def tipos(self, achados, nivel):
        return {a["tipo"] for a in achados.get(nivel, [])}

    def test_repositorio_limpo_passa(self):
        codigo, saida, achados = self.rodar()
        self.assertEqual(codigo, 0, saida)
        self.assertEqual(achados["bloqueantes"], [])

    def test_banco_que_saiu_da_pasta_ainda_esta_no_historico(self):
        self.commitar("dados/arena.db", "recordes", "sem querer")
        git(self.repo, "rm", "-q", "dados/arena.db")
        git(self.repo, "commit", "-q", "-m", "tirei")
        self.assertFalse(os.path.exists(os.path.join(self.repo, "dados", "arena.db")))
        codigo, saida, achados = self.rodar()
        self.assertEqual(codigo, 1, saida)
        self.assertIn("caminho proibido", self.tipos(achados, "bloqueantes"))

    def test_leia_das_pastas_vazias_pode(self):
        self.commitar("dados/LEIA.txt", "Aqui ficam os seus dados.\n")
        self.commitar("jogos/pessoais/LEIA.txt", "Coloque os jogos aqui.\n")
        codigo, saida, _ = self.rodar()
        self.assertEqual(codigo, 0, saida)

    def test_bios_e_jogo_pela_extensao(self):
        self.commitar("ferramentas/scph1001.bin", "x")
        codigo, saida, achados = self.rodar()
        self.assertEqual(codigo, 1, saida)
        self.assertIn("jogo ou BIOS pela extensao", self.tipos(achados, "bloqueantes"))

    def test_bios_em_pasta_com_acento(self):
        # O git poe entre aspas o caminho com acento ("BIOS/PS2/Jap\303\243o/...");
        # antes da correcao (11/10/2026), a regra "^BIOS/" nao pegava.
        self.commitar("BIOS/PS2/Japão/scph10000.bin", "x")
        codigo, saida, achados = self.rodar()
        self.assertEqual(codigo, 1, saida)
        caminhos = {a["onde"] for a in achados["bloqueantes"]}
        self.assertIn("BIOS/PS2/Japão/scph10000.bin", caminhos)

    def test_binario_renomeado_para_imagem_nao_passa(self):
        caminho = os.path.join(self.repo, "launcher", "fundo.png")
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, "wb") as arquivo:
            arquivo.write(b"\x00\x01SONY PS2 BIOS" + bytes(range(256)))
        git(self.repo, "add", "launcher/fundo.png")
        git(self.repo, "commit", "-q", "-m", "imagem?")
        codigo, saida, achados = self.rodar()
        self.assertEqual(codigo, 1, saida)
        self.assertIn("arquivo binario (nao e' imagem nem fonte)", self.tipos(achados, "bloqueantes"))

    def test_imagem_de_verdade_passa(self):
        caminho = os.path.join(self.repo, "docs", "fundo.png")
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, "wb") as arquivo:   # cabecalho de PNG + bytes quaisquer
            arquivo.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + bytes(64))
        git(self.repo, "add", "docs/fundo.png")
        git(self.repo, "commit", "-q", "-m", "imagem do README")
        codigo, saida, _ = self.rodar()
        self.assertEqual(codigo, 0, saida)

    def test_email_de_aluno_e_institucional_bloqueiam(self):
        # Montados na hora: este arquivo vai para o GitHub e nao pode "ter" o dado.
        self.commitar("docs/contas.md", "Aluno: fulano123" + "@al.educacao.sp.gov.br\n")
        codigo, saida, achados = self.rodar()
        self.assertEqual(codigo, 1, saida)
        self.assertIn("e-mail de aluno", self.tipos(achados, "bloqueantes"))
        self.commitar("docs/contas.md", "Professor: beltrano" + "@prof.educacao.sp.gov.br\n")
        codigo, saida, achados = self.rodar()
        self.assertIn("e-mail institucional", self.tipos(achados, "bloqueantes"))

    def test_token_na_mensagem_do_commit(self):
        token = "ghp_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"
        self.commitar("x.txt", "nada\n", "configurei o login com %s" % token)
        codigo, saida, achados = self.rodar()
        self.assertEqual(codigo, 1, saida)
        self.assertIn("token do GitHub", self.tipos(achados, "bloqueantes"))
        self.assertNotIn(token, saida, "o token nao pode aparecer inteiro na tela")

    def test_texto_do_arena_com_senha_nao_e_senha(self):
        self.commitar("servidor/x.py", "# a saida que nao pede senha: outro computador abre\n")
        codigo, saida, _ = self.rodar()
        self.assertEqual(codigo, 0, saida)
        self.commitar("servidor/y.py", "senha = " + "'abc12345'\n")
        codigo, saida, achados = self.rodar()
        self.assertIn("senha escrita", self.tipos(achados, "bloqueantes"))

    def test_o_que_ja_esta_no_github_fica_de_fora(self):
        remoto = os.path.join(self.base, "github.git")
        git(self.base, "init", "-q", "--bare", "-b", "main", remoto)
        git(self.repo, "remote", "add", "origin", remoto)
        self.commitar("dados/config.json", "{}", "antigo, ja publicado")
        git(self.repo, "push", "-q", "origin", "main")
        self.commitar("novo.txt", "nada\n")
        codigo, saida, _ = self.rodar()
        self.assertEqual(codigo, 0, saida)
        codigo, saida, achados = self.rodar("main", "--tudo")
        self.assertEqual(codigo, 1, saida)


if __name__ == "__main__":
    unittest.main()
