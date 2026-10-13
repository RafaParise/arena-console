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


class TestOPacoteLevaALicenca(unittest.TestCase):
    """A GPL pede o texto da licenca junto do programa distribuido; o pacote
    do GitHub ia sem o LICENSE e sem o TERCEIROS.md."""

    def test_licenca_e_terceiros_no_pacote(self):
        for nome in ("LICENSE", "TERCEIROS.md"):
            self.assertIn(nome, montador.ARQUIVOS_DA_RAIZ)
            self.assertTrue(os.path.isfile(os.path.join(montador.RAIZ, nome)), nome)


class TestPacoteDeAtualizacao(unittest.TestCase):
    """O guia 6 manda atualizar copiando por cima: o pacote de atualizacao
    leva so o programa (o completo traz o RetroArch e os emuladores ja
    configurados, e por cima trocaria a configuracao de quem usa)."""

    def test_so_o_programa(self):
        import zipfile
        pasta = tempfile.mkdtemp(prefix="arena_zip_atualizacao_")
        try:
            caminho = os.path.join(pasta, "atualizacao.zip")
            montador.zip_de_atualizacao(caminho)
            with zipfile.ZipFile(caminho) as z:
                nomes = z.namelist()
        finally:
            shutil.rmtree(pasta, ignore_errors=True)
        for esperado in ("ARENA/ARENA.bat", "ARENA/LICENSE", "ARENA/servidor/arena.py",
                         "ARENA/launcher/app.js", "ARENA/ferramentas/coletar_maquina.py"):
            self.assertIn(esperado, nomes)
        for nome in nomes:
            self.assertTrue(nome.startswith("ARENA/"), nome)
            partes = nome.split("/")
            self.assertNotIn(partes[1], ("retroarch", "emuladores", "dados", "jogos", "BIOS", "backup"), nome)
            self.assertNotIn("__pycache__", partes, nome)
            self.assertFalse(nome.startswith("ARENA/servidor/tests/"), nome)


sys.path.insert(0, os.path.join(RAIZ, "testes"))
import protege_cfg  # noqa: E402


class TestProtegeDadosDeQuemJoga(unittest.TestCase):
    """Os testes que ligam jogo mudavam dado de quem joga (o cartao de memoria
    do PS2, o perfil do Xbox 360, os dados do Wii, o historico do RetroArch):
    o protege_cfg guarda e devolve tudo."""

    def setUp(self):
        self.base = tempfile.mkdtemp(prefix="arena_protege_teste_")

    def tearDown(self):
        shutil.rmtree(self.base, ignore_errors=True)

    def escrever(self, caminho, dados):
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, "wb") as arquivo:
            arquivo.write(dados)

    def test_devolve_o_que_mudou_ou_sumiu_e_tira_o_que_nasceu(self):
        cartoes = os.path.join(self.base, "memcards")
        cartao = os.path.join(cartoes, "Mcd001.ps2")
        outro = os.path.join(cartoes, "sub", "Mcd002.ps2")
        avulso = os.path.join(self.base, "PCSX2.ini")
        self.escrever(cartao, b"save antigo")
        self.escrever(outro, b"outro cartao")
        self.escrever(avulso, b"[EmuCore]\n")
        data = 1_500_000_000 * 10 ** 9
        os.utime(cartao, ns=(data, data))
        guarda = protege_cfg.guardar([cartoes, avulso, os.path.join(self.base, "nao-existe")])
        try:
            self.escrever(cartao, b"o historico que a BIOS gravou")
            os.remove(outro)
            self.escrever(avulso, b"[EmuCore]\nmudado = 1\n")
            novo = os.path.join(cartoes, "criado-pelo-teste.ps2")
            self.escrever(novo, b"novo")
            devolvidos, tirados, problemas = protege_cfg.devolver(guarda)
        finally:
            shutil.rmtree(guarda["pasta"], ignore_errors=True)
        self.assertEqual(problemas, [])
        with open(cartao, "rb") as arquivo:
            self.assertEqual(arquivo.read(), b"save antigo")
        self.assertEqual(os.stat(cartao).st_mtime_ns, data)
        self.assertTrue(os.path.isfile(outro))
        with open(avulso, "rb") as arquivo:
            self.assertEqual(arquivo.read(), b"[EmuCore]\n")
        self.assertFalse(os.path.exists(novo))
        self.assertEqual(sorted(map(os.path.basename, devolvidos)), ["Mcd001.ps2", "Mcd002.ps2", "PCSX2.ini"])
        self.assertEqual(tirados, [novo])

    def test_o_que_nao_mudou_fica_como_esta(self):
        arquivo = os.path.join(self.base, "Config", "Dolphin.ini")
        self.escrever(arquivo, b"[Core]\n")
        guarda = protege_cfg.guardar([os.path.dirname(arquivo)])
        try:
            devolvidos, tirados, problemas = protege_cfg.devolver(guarda)
        finally:
            shutil.rmtree(guarda["pasta"], ignore_errors=True)
        self.assertEqual((devolvidos, tirados, problemas), ([], [], []))

    def test_a_copia_escapa_da_limpeza_da_rodada(self):
        # A rodada apaga as pastas arena_* que um teste esquece no Temp: se o
        # teste for morto no meio, a copia tem que continuar la.
        guarda = protege_cfg.guardar([])
        try:
            self.assertFalse(os.path.basename(guarda["pasta"]).startswith("arena_"))
        finally:
            shutil.rmtree(guarda["pasta"], ignore_errors=True)

    def test_os_dados_de_quem_joga_estao_protegidos(self):
        protegidos = [os.path.relpath(c, protege_cfg.RAIZ).replace("\\", "/")
                      for c in protege_cfg.DO_RETROARCH + protege_cfg.DOS_EMULADORES]
        for esperado in ("dados/builtin", "emuladores/PCSX2/PCSX2/memcards",
                         "emuladores/Dolphin/Dolphin-x64/User/Wii", "emuladores/Xenia/Xenia/content",
                         "emuladores/RPCS3/RPCS3/dev_hdd0/home"):
            self.assertIn(esperado, protegidos)


if __name__ == "__main__":
    unittest.main()
