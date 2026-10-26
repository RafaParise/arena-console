# -*- coding: utf-8 -*-
"""No celular a tela fala de "aparelho" e de "tela", nao de "computador", "PC" e "monitor" (launcher\\app.js, TROCAS_DO_CELULAR).

O JavaScript e' o do proprio launcher\\app.js, rodado no Node.js (so se ele estiver na maquina: sem ele, o teste e' pulado).
"""
import json
import os
import re
import shutil
import subprocess
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NODE = shutil.which("node")


def trocar(textos):
    with open(os.path.join(RAIZ, "launcher", "app.js"), encoding="utf-8") as arquivo:
        fonte = arquivo.read()
    achou = re.search(r"const TROCAS_DO_CELULAR = \[.*?\nfunction trocarComputador\(texto\) \{\n.*?\n\}\n", fonte, re.S)
    if not achou:
        raise AssertionError("a tabela TROCAS_DO_CELULAR sumiu do app.js")
    programa = achou.group(0) + "\nconsole.log(JSON.stringify(%s.map(trocarComputador)));" % json.dumps(textos, ensure_ascii=False)
    saida = subprocess.run([NODE, "-e", programa], capture_output=True, timeout=30)
    if saida.returncode:
        raise AssertionError(saida.stderr.decode("utf-8", "replace"))
    return json.loads(saida.stdout.decode("utf-8"))


@unittest.skipUnless(NODE, "sem o Node.js nesta maquina")
class AsTrocasDoCelular(unittest.TestCase):
    def confere(self, pares):
        self.assertEqual(trocar([antes for antes, _depois in pares]), [depois for _antes, depois in pares])

    def test_computador_vira_aparelho(self):
        self.confere([("Feche o ARENA no seu computador.", "Feche o ARENA no seu aparelho."),
                      ("Computadores da escola", "Aparelhos da escola"),
                      ("este computador", "este aparelho")])

    def test_pc_vira_aparelho_mas_nome_de_console_fica(self):
        self.confere([("Para PC fraco. Feio, mas não trava.", "Para aparelho fraco. Feio, mas não trava."),
                      ("O mais bonito. Só use se o PC aguentar.", "O mais bonito. Só use se o aparelho aguentar."),
                      ("PC Engine (1)", "PC Engine (1)"), ("PC-FX", "PC-FX"), ("PCSX2", "PCSX2")])

    def test_monitor_vira_tela_com_o_artigo_certo(self):
        self.confere([("Sincronizar com o monitor", "Sincronizar com a tela"),
                      ("A cada quantos quadros do monitor", "A cada quantos quadros da tela"),
                      ("Ligue ao monitor", "Ligue à tela"),
                      ("Troque no monitor", "Troque na tela"),
                      ("Um monitor", "Uma tela"),
                      ("Monitor", "Tela")])

    def test_o_que_nao_e_de_pc_nao_muda(self):
        self.confere([("Tela cheia", "Tela cheia"), ("Controle de disco", "Controle de disco")])


if __name__ == "__main__":
    unittest.main()
