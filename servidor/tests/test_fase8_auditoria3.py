# -*- coding: utf-8 -*-
"""Auditoria 3, Fase 8 (docs\\RELATORIO-QUALIDADE.md): levar o conserto para a
versao dos alunos.

Em 10/10/2026 a versao dos alunos passou a se chamar ARENA (era ARENA-alunos),
e o "montar_versao_alunos.py --atualizar" so aceitava o nome antigo. Agora
ele reconhece a versao dos alunos pelo que ela e' (a folha de rosto
LEIA-PRIMEIRO.txt, que so o montador escreve) -- e continua recusando a pasta
de desenvolvimento e qualquer pasta com .git (o repositorio).
"""
import os
import shutil
import sys
import tempfile
import unittest

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, os.path.join(RAIZ, "ferramentas"))
import montar_versao_alunos as montador  # noqa: E402


class TestQualPastaOAtualizarAceita(unittest.TestCase):

    def setUp(self):
        self.base = tempfile.mkdtemp(prefix="arena_qual_pasta_")

    def tearDown(self):
        shutil.rmtree(self.base, ignore_errors=True)

    def pasta(self, nome, *arquivos):
        caminho = os.path.join(self.base, nome)
        os.makedirs(caminho)
        for arquivo in arquivos:
            alvo = os.path.join(caminho, arquivo)
            if arquivo.endswith(os.sep) or arquivo == ".git":
                os.makedirs(alvo)
            else:
                open(alvo, "w").close()
        return caminho

    def test_o_nome_de_sempre_vale(self):
        self.assertTrue(montador.parece_versao_dos_alunos(self.pasta("ARENA-alunos")))

    def test_outro_nome_com_a_folha_de_rosto_vale(self):
        self.assertTrue(montador.parece_versao_dos_alunos(self.pasta("ARENA", "LEIA-PRIMEIRO.txt")))

    def test_outro_nome_sem_a_folha_de_rosto_nao(self):
        self.assertFalse(montador.parece_versao_dos_alunos(self.pasta("ARENA")))

    def test_pasta_com_git_nunca(self):
        self.assertFalse(montador.parece_versao_dos_alunos(self.pasta("ARENA-alunos", ".git")))
        self.assertFalse(montador.parece_versao_dos_alunos(self.pasta("ARENA2", "LEIA-PRIMEIRO.txt", ".git")))

    def test_a_pasta_de_desenvolvimento_nunca(self):
        self.assertFalse(montador.parece_versao_dos_alunos(montador.RAIZ))

    def test_pasta_que_nao_existe(self):
        self.assertFalse(montador.parece_versao_dos_alunos(os.path.join(self.base, "nao-existe")))


class TestConferenciaDoPacote(unittest.TestCase):
    """O link de download nos guias leva o nome da conta do GitHub, que pode
    ser o apelido de quem monta: so o endereco do repositorio sai antes de
    procurar o apelido; em qualquer outro lugar ele continua barrado."""

    def test_o_endereco_do_repositorio_nao_conta_como_dado_de_quem_montou(self):
        texto = "baixe em https://github.com/fulanodetal/arena-console/releases/latest".lower()
        self.assertNotIn("fulanodetal", montador.texto_sem_enderecos_publicos(texto))

    def test_o_apelido_em_outro_lugar_continua_aparecendo(self):
        texto = 'apelido = "fulanodetal"; veja github.com/fulanodetal/outro-projeto'.lower()
        self.assertIn("fulanodetal", montador.texto_sem_enderecos_publicos(texto))


if __name__ == "__main__":
    unittest.main()
