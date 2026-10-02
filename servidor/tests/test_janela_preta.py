# -*- coding: utf-8 -*-
"""Janela preta que nao trava o servidor e verificador que confere tudo.

Achados de 02/10/2026 (o servidor que "parava sem motivo"): a escrita na
janela preta podia prender o servidor, e o VERIFICAR.bat nao conferia 5 dos
modulos sem os quais o ARENA nem abre (integridade, janela_preta,
jogadores, nomes_arcade e processos).
"""
import ast
import os
import sys
import threading
import time
import unittest

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PASTA_SERVIDOR not in sys.path:
    sys.path.insert(0, PASTA_SERVIDOR)

import janela_preta  # noqa: E402


def modulos_que_o_arena_precisa():
    """Os modulos do servidor que o arena.py importa, direta ou indiretamente."""
    locais = {nome[:-3] for nome in os.listdir(PASTA_SERVIDOR) if nome.endswith(".py")}
    vistos, fila = set(), ["arena"]
    while fila:
        modulo = fila.pop()
        if modulo in vistos:
            continue
        vistos.add(modulo)
        arvore = ast.parse(open(os.path.join(PASTA_SERVIDOR, modulo + ".py"), encoding="utf-8").read())
        for no in ast.walk(arvore):
            if isinstance(no, ast.Import):
                nomes = [a.name.split(".")[0] for a in no.names]
            elif isinstance(no, ast.ImportFrom) and no.module:
                nomes = [no.module.split(".")[0]]
            else:
                continue
            fila += [n for n in nomes if n in locais]
    return vistos


def lista_do_verificar():
    """A lista PROGRAMA do diagnostico.py, lida sem importar o modulo."""
    arvore = ast.parse(open(os.path.join(PASTA_SERVIDOR, "diagnostico.py"), encoding="utf-8").read())
    for no in arvore.body:
        if isinstance(no, ast.Assign) and any(getattr(a, "id", "") == "PROGRAMA" for a in no.targets):
            return set(ast.literal_eval(no.value))
    return set()


class _JanelaTravada:
    """Janela preta com selecao ativa: escrever nao termina ate soltar."""

    def __init__(self):
        self.solta = threading.Event()
        self.recebido = []

    def write(self, texto):
        self.solta.wait()
        self.recebido.append(texto)
        return len(texto)

    def flush(self):
        pass


class TestJanelaPreta(unittest.TestCase):

    def test_verificar_confere_todos_os_modulos_do_servidor(self):
        faltando = sorted("servidor/%s.py" % m for m in modulos_que_o_arena_precisa()
                          if "servidor/%s.py" % m not in lista_do_verificar())
        self.assertEqual(faltando, [], "o VERIFICAR.bat diria que esta tudo presente sem estes")

    def test_escrever_na_janela_travada_nao_prende_o_servidor(self):
        janela = _JanelaTravada()
        recados = janela_preta._Recados()
        saida = janela_preta.SaidaSemTravar(janela, recados)
        inicio = time.monotonic()
        for numero in range(janela_preta.LIMITE_DA_FILA + 50):
            saida.write("recado %d\n" % numero)
        self.assertLess(time.monotonic() - inicio, 1.0, "escrever esperou a janela")
        inicio = time.monotonic()
        saida.flush()                              # espera no maximo ~1 s, nunca para sempre
        self.assertLess(time.monotonic() - inicio, 2.0)
        janela.solta.set()                         # a selecao acabou: os recados andam
        self.assertTrue(recados.esperar(5.0))
        texto = "".join(janela.recebido)
        self.assertIn("recado 0\n", texto)
        self.assertIn("nao couberam", texto)       # os que passaram do limite foram contados
        self.assertLess(texto.index("recado 0\n"), texto.index("recado 1\n"))


if __name__ == "__main__":
    unittest.main()
