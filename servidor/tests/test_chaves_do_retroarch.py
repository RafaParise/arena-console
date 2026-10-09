# -*- coding: utf-8 -*-
"""Toda chave que o ARENA manda para o RetroArch existe no RetroArch.

Achado da auditoria 3 (08/10/2026, Fase 4, docs\\RELATORIO-QUALIDADE.md): o
ARENA escrevia 9 chaves que o RetroArch desta pasta nao conhece -- e ele
ignora em silencio. A mais seria: a porta da partida ia como "netplay_port"
(o nome certo e' "netplay_ip_port"), e o "--port" da linha de comando
tambem e' ignorado; por isso o simulador de rede ruim nunca ficou no
caminho, e as duas partidas do teste de sala caiam na mesma porta. As
outras nao mudavam nada na tela (o RetroArch ja fazia aquilo sozinho), mas
o codigo dizia que fazia: o tema do menu do Esc, o espaco inicial do save
state, o "Importar conteudo" escondido, o atalho de gravar a partida.

O arquivo de opcoes e' gerado de verdade (gravar_override), numa pasta
temporaria, com cada perfil, motor grafico, modo e tipo de partida, e com
todas as opcoes avancadas do recursos.json ligadas. A referencia e' o
proprio RetroArch: as chaves do retroarch.cfg (ele grava todas ao fechar)
e os textos do retroarch.exe. Sem os dois (copia sem o RetroArch, como a
do GitHub), o teste e' pulado.
"""
import os
import re
import shutil
import sys
import tempfile
import unittest
from unittest import mock

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PASTA_SERVIDOR not in sys.path:
    sys.path.insert(0, PASTA_SERVIDOR)

import arena  # noqa: E402
import graficos  # noqa: E402

PASTA_RETROARCH = os.path.join(os.path.dirname(PASTA_SERVIDOR), "retroarch")
CFG = os.path.join(PASTA_RETROARCH, "retroarch.cfg")
EXE = os.path.join(PASTA_RETROARCH, "retroarch.exe")

# Chave com o numero do jogador ou da porta: o RetroArch monta o nome na
# hora ("input_player%u_..."), entao o texto no programa vem sem o numero.
NUMERO_DO_JOGADOR = re.compile(r"(?<=player)\d+(?=_)|(?<=_p)\d+$")


def chaves_que_o_retroarch_conhece():
    conhecidas = set()
    if os.path.isfile(CFG):
        with open(CFG, encoding="utf-8", errors="replace") as arquivo:
            conhecidas |= set(re.findall(r"^([a-z0-9_]+) = ", arquivo.read(), re.M))
    if os.path.isfile(EXE):
        with open(EXE, "rb") as arquivo:
            conhecidas |= {m.group(0).decode("ascii")
                           for m in re.finditer(rb"[a-z][a-z0-9_]{3,}", arquivo.read())}
    return conhecidas


def conhecida(chave, conhecidas):
    candidatas = {chave, NUMERO_DO_JOGADOR.sub("1", chave), NUMERO_DO_JOGADOR.sub("", chave)}
    return bool(candidatas & conhecidas)


@unittest.skipUnless(os.path.isfile(CFG) and os.path.isfile(EXE),
                     "sem o RetroArch nesta copia (retroarch.cfg e retroarch.exe)")
class TestChavesDoRetroArch(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="arena_chaves_teste_")
        pastas = {nome: os.path.join(self.dir, nome.lower()) for nome in (
            "PASTA_DADOS", "PASTA_SAVES", "PASTA_STATES", "PASTA_CAPTURAS", "PASTA_SISTEMA",
            "PASTA_CHEATS", "PASTA_REMAPS", "PASTA_CONTROLES", "PASTA_CACHE", "PASTA_PERFIS_CONTROLE")}
        pastas["ARQUIVO_OVERRIDE"] = os.path.join(pastas["PASTA_DADOS"], "arena_override.cfg")
        self.troca = mock.patch.multiple(arena, **pastas)
        self.troca.start()

    def tearDown(self):
        self.troca.stop()
        shutil.rmtree(self.dir, ignore_errors=True)

    def chaves_do_arquivo(self, config, **kwargs):
        caminho = arena.gravar_override(config, **kwargs)
        with open(caminho, encoding="utf-8") as arquivo:
            return set(re.findall(r"^([a-z0-9_]+) = ", arquivo.read(), re.M))

    def todas_as_chaves(self):
        base = arena.config_padrao()
        avancado = dict(base.get("avancado") or {})
        avancado.update({r["chave"]: "1" for r in arena.carregar_recursos()["recursos"]})
        variantes = []
        for perfil in list(arena.PERFIS_GRAFICOS) + ["automatico"]:
            for driver in arena.DRIVERS_VIDEO:
                config = dict(base, perfil_grafico=perfil)
                config["avancado"] = dict(avancado, video_driver=driver)
                variantes.append((config, {}))
        for extra in ({"modo_modesto": True}, {"abaixo_do_original": "minimo"},
                      {"ultra_desempenho": True}, {"travar_teclas": True}):
            variantes.append((dict(base, avancado=avancado, **extra), {}))
        partidas = [graficos.opcoes_de_partida("x", hospedar, pela_internet=internet, assistir=assistir,
                                               multitap=multitap, jogador=3)
                    for hospedar in (True, False) for internet in (True, False)
                    for assistir in (False, True) for multitap in (False, True)]
        for extras in partidas:
            variantes.append((dict(base, avancado=avancado), {"em_partida": True, "extras": extras}))
        chaves = set()
        for config, kwargs in variantes:
            for ligados in (0, 4):
                chaves |= self.chaves_do_arquivo(config, controles_ligados=ligados, **kwargs)
        return chaves

    def test_toda_chave_existe_no_retroarch(self):
        conhecidas = chaves_que_o_retroarch_conhece()
        chaves = self.todas_as_chaves()
        self.assertGreater(len(chaves), 200)
        desconhecidas = sorted(c for c in chaves if not conhecida(c, conhecidas))
        self.assertEqual(desconhecidas, [],
                         "O RetroArch ignora estas chaves (nome errado ou que nao existe mais): %s"
                         % ", ".join(desconhecidas))

    def test_a_porta_da_partida_vai_no_nome_certo(self):
        # O "--port" da linha de comando e' ignorado pelo RetroArch desta
        # pasta (provado em 08/10/2026: os dois hospedeiros escutavam na
        # 55435 pedindo 55437 e 55438); quem manda e' a chave do arquivo.
        opcoes = graficos.opcoes_de_partida("x", True)
        self.assertEqual(opcoes.get("netplay_ip_port"), str(graficos.PORTA_PARTIDA))
        self.assertNotIn("netplay_port", opcoes)


class TestSemChaveRepetida(unittest.TestCase):
    """Dicionario escrito a mao com a mesma chave duas vezes: o Python fica
    com a ultima, calado. O BASE_COMUM tinha 9 chaves repetidas (blocos
    inteiros colados duas vezes) -- iguais, mas a proxima mudanca numa das
    copias nao valeria."""

    def test_nenhum_dicionario_do_servidor_repete_chave(self):
        import ast
        repetidas = []
        for nome in sorted(os.listdir(PASTA_SERVIDOR)):
            if not nome.endswith(".py"):
                continue
            with open(os.path.join(PASTA_SERVIDOR, nome), encoding="utf-8") as arquivo:
                arvore = ast.parse(arquivo.read(), nome)
            for no in ast.walk(arvore):
                if isinstance(no, ast.Dict):
                    vistas = set()
                    for chave in no.keys:
                        if isinstance(chave, ast.Constant) and isinstance(chave.value, str):
                            if chave.value in vistas:
                                repetidas.append("%s:%d %s" % (nome, chave.lineno, chave.value))
                            vistas.add(chave.value)
        self.assertEqual(repetidas, [])


if __name__ == "__main__":
    unittest.main()
