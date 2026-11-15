# -*- coding: utf-8 -*-
r"""Testes do ferramentas\rascunho_da_release.py (rascunho da nota da proxima versao).

Monta um repositorio git de mentira numa pasta temporaria: commits em pastas diferentes, uma etiqueta e mais
commits depois dela. Confere a area de cada arquivo, o agrupamento dos commits e o texto do rascunho. Sem o git
instalado, os testes que precisam dele se pulam.
"""
import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "ferramentas"))
sys.path.insert(0, os.path.join(RAIZ, "testes"))
import limpeza  # noqa: E402
import rascunho_da_release as rr  # noqa: E402


class TesteDasAreas(unittest.TestCase):
    """Nao precisa do git: so a regra de qual area cada caminho e' cada commit pertence."""

    def test_cada_pasta_cai_na_area_certa(self):
        casos = {
            "servidor/arena.py": "Servidor",
            "servidor/tests/test_x.py": "Testes",
            "testes/limpeza.py": "Testes",
            "nativo/src/main.rs": "Servidor nativo em Rust",
            "launcher/app.js": "Tela",
            "android/app/build.gradle": "Android",
            "ARENA.sh": "Linux",
            "ARENA.desktop": "Linux",
            "ARENA.bat": "Windows",
            "ferramentas/compilar_nativo.py": "Ferramentas",
            "docs/PENDENCIAS.md": "Documentação",
            "LEIA-ME.md": "Documentação",
            "jogos/lista.json": "Outros",
        }
        for caminho, area in casos.items():
            self.assertEqual(rr.area_do_arquivo(caminho), area, caminho)

    def test_principal_e_a_area_com_mais_arquivos_e_as_outras_ficam_citadas(self):
        principal, outras = rr.areas_do_commit(["launcher/app.js", "launcher/estilo.css", "servidor/arena.py",
                                                "docs/x.md"])
        self.assertEqual(principal, "Tela")
        self.assertEqual(outras, ["Servidor", "Documentação"])

    def test_empate_vale_a_area_que_vem_antes_e_commit_vazio_e_outros(self):
        self.assertEqual(rr.areas_do_commit(["docs/a.md", "servidor/a.py"]), ("Servidor", ["Documentação"]))
        self.assertEqual(rr.areas_do_commit([]), ("Outros", []))


class TesteComRepositorio(unittest.TestCase):
    """Repositorio git temporario de verdade (nome e e-mail falsos, so dentro dele)."""

    def setUp(self):
        if shutil.which("git") is None:
            self.skipTest("o git nao esta instalado neste computador")
        self.pasta = tempfile.mkdtemp(prefix="arena_rascunho_release_")
        self.addCleanup(limpeza.apagar_pasta, self.pasta)
        self.git("init", "-q")
        self.git("config", "user.name", "Teste")
        self.git("config", "user.email", "teste@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        self.git("config", "tag.gpgsign", "false")

    def git(self, *argumentos, data=None):
        ambiente = dict(os.environ)
        if data:
            ambiente["GIT_AUTHOR_DATE"] = ambiente["GIT_COMMITTER_DATE"] = data + "T12:00:00"
        r = subprocess.run(["git", *argumentos], cwd=self.pasta, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=60, env=ambiente)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout

    def commit(self, titulo, arquivos, data):
        for caminho in arquivos:
            completo = os.path.join(self.pasta, *caminho.split("/"))
            os.makedirs(os.path.dirname(completo), exist_ok=True)
            with open(completo, "a", encoding="utf-8") as arquivo:
                arquivo.write(titulo + "\n")
            self.git("add", "--", caminho)
        # O corpo traz as linhas de assinatura: elas nunca podem aparecer no rascunho.
        mensagem = titulo + "\n\nCorpo do commit.\n\nCo-Authored-By: Teste <teste@example.invalid>\n" \
                            "Claude-Session: https://example.invalid/sessao\n"
        self.git("commit", "-q", "-m", mensagem, data=data)

    def test_sem_etiqueta_usa_o_historico_todo_e_avisa(self):
        self.commit("Primeiro commit da tela", ["launcher/app.js"], "2026-11-01")
        texto, aviso = rr.gerar(self.pasta)
        self.assertIsNotNone(aviso)
        self.assertIn("nenhuma etiqueta", texto)
        self.assertIn("- Commits: 1", texto)
        self.assertIn("Primeiro commit da tela", texto)

    def test_agrupa_os_commits_depois_da_etiqueta(self):
        self.commit("Antigo do servidor", ["servidor/velho.py"], "2026-11-01")
        self.git("tag", "v2026.11.01")
        self.commit("Busca nova na tela", ["launcher/app.js", "launcher/estilo.css", "servidor/arena.py"],
                    "2026-11-02")
        self.commit("Rota de capas no nativo", ["nativo/src/main.rs"], "2026-11-03")
        self.commit("Teste da limpeza", ["servidor/tests/test_a.py", "testes/b.py"], "2026-11-03")
        self.commit("Guia atualizado", ["LEIA-ME.md"], "2026-11-04")
        texto, aviso = rr.gerar(self.pasta)
        self.assertIsNone(aviso)
        self.assertIn("- Etiqueta de partida: `v2026.11.01`", texto)
        self.assertIn("- Commits: 4", texto)
        self.assertIn("- Datas: de 2026-11-02 a 2026-11-04", texto)
        self.assertNotIn("Antigo do servidor", texto)          # e' de antes da etiqueta
        self.assertNotIn("Co-Authored-By", texto)
        self.assertNotIn("Claude-Session", texto)
        self.assertNotIn("Corpo do commit", texto)
        self.assertIn("## Tela (1)", texto)
        self.assertIn("## Servidor nativo em Rust (1)", texto)
        self.assertIn("## Testes (1)", texto)
        self.assertIn("## Documentação (1)", texto)
        self.assertNotIn("## Servidor (", texto)               # o commit da tela so cita o servidor
        linha = [l for l in texto.splitlines() if "Busca nova na tela" in l][0]
        self.assertIn("(também: Servidor)", linha)
        # As secoes seguem a ordem de AREAS: a Tela vem antes dos Testes, que vem antes da Documentacao.
        self.assertLess(texto.index("## Tela"), texto.index("## Testes"))
        self.assertLess(texto.index("## Testes"), texto.index("## Documentação"))

    def test_desde_e_ate_escolhem_o_intervalo(self):
        self.commit("Um", ["android/a.kt"], "2026-11-01")
        self.git("tag", "v1")
        self.commit("Dois", ["android/b.kt"], "2026-11-02")
        self.git("tag", "v2")
        self.commit("Tres", ["ferramentas/c.py"], "2026-11-03")
        texto, _ = rr.gerar(self.pasta, desde="v1", ate="v2")
        self.assertIn("- Commits: 1", texto)
        self.assertIn("Dois", texto)
        self.assertNotIn("Tres", texto)
        self.assertIn("## Android (1)", texto)

    def test_etiqueta_que_nao_existe_da_erro_claro(self):
        self.commit("Um", ["docs/a.md"], "2026-11-01")
        with self.assertRaises(rr.ErroDoGit) as caso:
            rr.gerar(self.pasta, desde="v9999")
        self.assertIn("git tag", str(caso.exception))

    def test_saida_em_arquivo(self):
        self.commit("Um", ["docs/a.md"], "2026-11-01")
        destino = os.path.join(self.pasta, "rascunho.md")
        conversa = io.StringIO()   # o aviso e a confirmacao nao sujam a saida dos testes
        with contextlib.redirect_stdout(conversa), contextlib.redirect_stderr(conversa):
            self.assertEqual(rr.main(["--pasta", self.pasta, "--saida", destino]), 0)
        self.assertIn("Rascunho gravado", conversa.getvalue())
        with open(destino, encoding="utf-8") as arquivo:
            self.assertIn("## Documentação (1)", arquivo.read())

    def test_fora_de_um_repositorio_explica_o_que_fazer(self):
        solta = tempfile.mkdtemp(prefix="arena_rascunho_solta_")
        self.addCleanup(limpeza.apagar_pasta, solta)
        with self.assertRaises(rr.ErroDoGit) as caso:
            rr.conferir_repositorio(solta)
        self.assertIn("git clone", str(caso.exception))


if __name__ == "__main__":
    unittest.main()
