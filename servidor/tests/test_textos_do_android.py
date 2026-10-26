# -*- coding: utf-8 -*-
"""O ARENA do celular nao pode sugerir tecla de teclado, Windows ou programa de PC.

Pedido do Rafael (25/10/2026): "na versao de android ainda sugere os botoes como por exemplo F10 para sair e afins".
A tela e' a mesma no computador e no celular (launcher\\index.html). O que e' so do computador leva
`data-fora-do-android` (some no celular: app.js, estado.sistemaDoComputador === "android") e, quando o celular tem
um jeito equivalente de fazer a mesma coisa, o texto dele vai ao lado, com `data-so-android`.

Este teste le o index.html e acusa todo texto que fala de F2, F4, F8, F9, F10, Esc, Alt+Tab, Windows, Visual C++,
PowerShell, .bat ou "monitor" fora de um bloco `data-fora-do-android`. Para o texto que aparece nas duas versoes
(a explicacao de uma opcao, por exemplo), escreva-o de um jeito que valha para as duas, ou duplique-o: uma versao
`data-fora-do-android`, a outra `data-so-android`.
"""
import os
import re
import sys
import unittest
from html.parser import HTMLParser

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "servidor"))

# O que so existe no teclado ou no computador.
PROIBIDO = re.compile(r"\bF(?:2|4|8|9|10)\b|\bAlt\s*\+\s*Tab\b|\bEsc\b|\bWindows\b|Visual C\+\+|PowerShell|\.bat\b|\bmonitor\b|\bCtrl\b",
                      re.I)
SEM_FECHAMENTO = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


class _Leitor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.pilha = []             # [(tag, atributos)]
        self.achados = []           # (linha, texto, tag)
        self.ignorar = 0            # dentro de <script> e <style>

    def handle_starttag(self, tag, atributos):
        if tag in SEM_FECHAMENTO:
            return
        self.pilha.append((tag, dict(atributos)))
        if tag in ("script", "style"):
            self.ignorar += 1

    def handle_endtag(self, tag):
        for i in range(len(self.pilha) - 1, -1, -1):
            if self.pilha[i][0] == tag:
                del self.pilha[i:]
                break
        if tag in ("script", "style") and self.ignorar:
            self.ignorar -= 1

    def handle_data(self, dados):
        if self.ignorar or not dados.strip():
            return
        # data-so-navegador: so aparece na versao web do Chromebook (launcher\navegador\tela.js), nunca no app do celular.
        if any("data-fora-do-android" in atributos or "data-so-navegador" in atributos for _tag, atributos in self.pilha):
            return
        achou = PROIBIDO.search(dados)
        if achou:
            self.achados.append((self.getpos()[0], " ".join(dados.split())[:110], self.pilha[-1][0] if self.pilha else ""))


class OTextoDoCelular(unittest.TestCase):
    def test_nenhum_texto_de_teclado_ou_de_windows_no_celular(self):
        with open(os.path.join(RAIZ, "launcher", "index.html"), encoding="utf-8") as arquivo:
            leitor = _Leitor()
            leitor.feed(arquivo.read())
        linhas = ["linha %d <%s>: %s" % (linha, tag, texto) for linha, texto, tag in leitor.achados]
        self.assertEqual(linhas, [], "texto de PC visivel no celular (ponha data-fora-do-android, ou escreva uma versao "
                                    "data-so-android):\n  " + "\n  ".join(linhas))


if __name__ == "__main__":
    unittest.main()
