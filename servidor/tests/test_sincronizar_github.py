# -*- coding: utf-8 -*-
"""ferramentas\\sincronizar_github.py com um "GitHub" de mentira: um
repositorio vazio numa pasta temporaria e dois clones (dois computadores).
Sem internet. Confere as regras da ferramenta: puxar avanca, enviar manda, o
que nao tem commit NAO vai (nem entra em commit sozinho), os dois lados
mudando se juntam, e o conflito desiste sem estragar nada."""
import io
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
import sincronizar_github as sinc  # noqa: E402


def git(pasta, *argumentos):
    r = subprocess.run(["git", *argumentos], cwd=pasta, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise AssertionError("git %s: %s" % (" ".join(argumentos), r.stdout + r.stderr))
    return r.stdout.strip()


def escrever(pasta, nome, texto):
    with open(os.path.join(pasta, nome), "w", encoding="utf-8", newline="\n") as arquivo:
        arquivo.write(texto)


@unittest.skipUnless(shutil.which("git"), "precisa do git instalado")
class TestSincronizarGithub(unittest.TestCase):
    def setUp(self):
        self.base = tempfile.mkdtemp(prefix="arena_sinc_")
        self.remoto = os.path.join(self.base, "github.git")
        git(self.base, "init", "-q", "--bare", "-b", "auditoria", self.remoto)
        self.a = self.clone("computador_a")
        escrever(self.a, "LEIA.txt", "linha 1\nlinha 2\n")
        git(self.a, "add", "LEIA.txt")
        git(self.a, "commit", "-q", "-m", "primeiro")
        git(self.a, "push", "-q", "-u", "origin", "auditoria")
        self.b = self.clone("computador_b")

    def tearDown(self):
        sinc.RAIZ = RAIZ
        shutil.rmtree(self.base, ignore_errors=True)

    def clone(self, nome):
        pasta = os.path.join(self.base, nome)
        git(self.base, "clone", "-q", self.remoto, pasta)
        git(pasta, "config", "user.email", "teste@exemplo.invalid")
        git(pasta, "config", "user.name", "Teste")
        git(pasta, "config", "core.autocrlf", "false")
        if git(pasta, "branch", "-r"):
            git(pasta, "checkout", "-q", "-B", "auditoria", "origin/auditoria")
        else:
            # O "GitHub" ainda vazio: o primeiro commit ja nasce no ramo certo.
            git(pasta, "symbolic-ref", "HEAD", "refs/heads/auditoria")
        return pasta

    def rodar(self, pasta, *argumentos):
        sinc.RAIZ = pasta
        saida = io.StringIO()
        with redirect_stdout(saida):
            codigo = sinc.main(list(argumentos))
        return codigo, saida.getvalue()

    def test_enviar_e_puxar(self):
        escrever(self.a, "novo.txt", "de A\n")
        git(self.a, "add", "novo.txt")
        git(self.a, "commit", "-q", "-m", "de A")
        codigo, saida = self.rodar(self.a, "enviar")
        self.assertEqual(codigo, 0, saida)
        codigo, saida = self.rodar(self.b, "puxar")
        self.assertEqual(codigo, 0, saida)
        self.assertTrue(os.path.exists(os.path.join(self.b, "novo.txt")))

    def test_sem_commit_nao_vai_nem_vira_commit(self):
        escrever(self.b, "trabalho_pela_metade.txt", "outro assistente ainda mexendo\n")
        antes = git(self.b, "rev-parse", "HEAD")
        codigo, saida = self.rodar(self.b, "tudo")
        self.assertEqual(codigo, 0, saida)
        self.assertIn("SEM commit", saida)
        self.assertEqual(git(self.b, "rev-parse", "HEAD"), antes, "fez commit sozinho")
        self.assertNotIn("trabalho_pela_metade.txt", git(self.remoto, "ls-tree", "-r", "--name-only", "auditoria"))
        self.assertTrue(os.path.exists(os.path.join(self.b, "trabalho_pela_metade.txt")))

    def test_tudo_com_mensagem_faz_o_commit(self):
        escrever(self.b, "pedido.txt", "o professor pediu\n")
        codigo, saida = self.rodar(self.b, "enviar", "--tudo", "pedido do professor")
        self.assertEqual(codigo, 0, saida)
        self.assertIn("pedido.txt", git(self.remoto, "ls-tree", "-r", "--name-only", "auditoria"))
        self.assertEqual(git(self.remoto, "log", "-1", "--format=%s", "auditoria"), "pedido do professor")

    def test_tudo_sem_mensagem_recusa(self):
        codigo, saida = self.rodar(self.b, "enviar", "--tudo")
        self.assertEqual(codigo, 2)
        self.assertIn("Faltou a mensagem", saida)

    def test_os_dois_mudaram_arquivos_diferentes(self):
        escrever(self.a, "de_a.txt", "A\n")
        git(self.a, "add", "de_a.txt")
        git(self.a, "commit", "-q", "-m", "A")
        self.assertEqual(self.rodar(self.a, "enviar")[0], 0)
        escrever(self.b, "de_b.txt", "B\n")
        git(self.b, "add", "de_b.txt")
        git(self.b, "commit", "-q", "-m", "B")
        codigo, saida = self.rodar(self.b, "tudo")
        self.assertEqual(codigo, 0, saida)
        nomes = git(self.remoto, "ls-tree", "-r", "--name-only", "auditoria")
        self.assertIn("de_a.txt", nomes)
        self.assertIn("de_b.txt", nomes)

    def test_conflito_desiste_sem_estragar(self):
        escrever(self.a, "LEIA.txt", "linha 1 de A\nlinha 2\n")
        git(self.a, "commit", "-q", "-am", "A muda a linha 1")
        self.assertEqual(self.rodar(self.a, "enviar")[0], 0)
        escrever(self.b, "LEIA.txt", "linha 1 de B\nlinha 2\n")
        git(self.b, "commit", "-q", "-am", "B muda a linha 1")
        meu = git(self.b, "rev-parse", "HEAD")
        codigo, saida = self.rodar(self.b, "puxar")
        self.assertEqual(codigo, 1, saida)
        self.assertIn("MESMO trecho", saida)
        self.assertEqual(git(self.b, "rev-parse", "HEAD"), meu)
        self.assertEqual(git(self.b, "status", "--porcelain"), "", "deixou a junção pela metade")
        with open(os.path.join(self.b, "LEIA.txt"), encoding="utf-8") as arquivo:
            self.assertIn("de B", arquivo.read())

    def test_enviar_com_github_na_frente_pede_para_puxar(self):
        escrever(self.a, "de_a.txt", "A\n")
        git(self.a, "add", "de_a.txt")
        git(self.a, "commit", "-q", "-m", "A")
        self.assertEqual(self.rodar(self.a, "enviar")[0], 0)
        escrever(self.b, "de_b.txt", "B\n")
        git(self.b, "add", "de_b.txt")
        git(self.b, "commit", "-q", "-m", "B")
        codigo, saida = self.rodar(self.b, "enviar")
        self.assertEqual(codigo, 1, saida)
        self.assertIn("Puxe primeiro", saida)


if __name__ == "__main__":
    unittest.main()
