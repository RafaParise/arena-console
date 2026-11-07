# -*- coding: utf-8 -*-
"""A funcao pedir(rota, metodo, corpo) da tela (launcher\\app.js): o corpo nunca vai no lugar do metodo.

Achado de 07/11/2026: tres botoes do celular como controle chamavam pedir(rota, {corpo}). O navegador recusa o pedido
("[object Object]" nao e' metodo HTTP) e a tela dizia que o ARENA tinha parado de responder.
"""
import os
import re
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class OPedirDaTela(unittest.TestCase):
    def test_o_segundo_argumento_e_sempre_o_metodo(self):
        erradas = []
        for nome in ("app.js",):
            with open(os.path.join(RAIZ, "launcher", nome), encoding="utf-8") as arquivo:
                for numero, linha in enumerate(arquivo, 1):
                    if re.search(r"function\s+pedir\(", linha):
                        continue                    # a propria definicao
                    for achado in re.finditer(r"\bpedir\(\s*([^,()]+?)\s*,\s*([^,)\s][^,)]*)", linha):
                        metodo = achado.group(2).strip()
                        if not re.fullmatch(r'"(GET|POST|PUT|DELETE)"|metodo|"GET"', metodo):
                            erradas.append("%s:%d: %s" % (nome, numero, linha.strip()[:120]))
        self.assertEqual(erradas, [], "pedir() com o corpo no lugar do metodo")


if __name__ == "__main__":
    unittest.main()
