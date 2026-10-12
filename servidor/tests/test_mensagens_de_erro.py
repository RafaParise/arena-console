# -*- coding: utf-8 -*-
"""Toda mensagem de erro que o aluno le diz o que aconteceu E o que fazer.

Auditoria 3, Fase 3 (07/10/2026): das 82 mensagens de erro do servidor, 38
so diziam o que aconteceu ("Limite de 20 amigos.", "O arquivo do jogo nao
esta mais no lugar.", "Pontuacao fora da faixa aceita."...), e na tela mais
4. O roteiro pede as duas partes. Este teste le o codigo (self.erro(...) no
arena.py e recado(..., true) / aviso(...) no app.js) e reprova a frase nova
que nao tenha um verbo de "o que fazer" -- menos as internas, abaixo, que o
aluno nao ve (cada uma com o motivo).
"""
import os
import re
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJETO = os.path.dirname(RAIZ)

ACAO = re.compile(r"\b(clique|abra|feche|confira|tente|coloque|ponha|use|escolha|veja|pe[cç]a|aperte|escreva|"
                  r"digite|espere|ligue|desligue|mande|apague|renomeie|baixe|reabra|atualize|volte|mova|copie|"
                  r"cole|passe|deixe|libere|conecte|v[aá]|procure|rode|pergunte|remova|instale|arraste|plugue|"
                  r"guarde|traga|leve|troque|sincronize|confirme|envie|preencha|encurte|entre|defina)\b", re.I)

# As mensagens dos OUTROS modulos que chegam a tela por excecao (raise
# ValueError("...")) ou por retorno ((None, "...") / (False, "...")) --
# auditoria 3, Fase 3 (08/10/2026). Com as internas de cada um, e o motivo.
MODULOS = ("arena.py", "acervo.py", "barreiras.py", "capas_online.py", "cheats.py", "controles.py",
           "internet_archive.py")
INTERNAS_DOS_MODULOS = {
    "Miniatura inválida.": "miniatura que a propria tela faz; a fila tenta de novo",
    "Miniatura grande demais.": "miniatura que a propria tela faz",
    "Miniatura em formato não aceito.": "miniatura que a propria tela faz",
    "numero invalido: %s": "conversao interna de texto em numero (sincronizacao)",
}

# O aluno nao ve: o motivo de cada uma.
INTERNAS = {
    "Esta parte do ARENA só pode ser usada neste computador, não por outro da rede.":
        "resposta para OUTRO computador que tentou uma rota fechada a rede",
    "Capa não encontrada.": "imagem que a propria tela pede (<img>); sem ela, aparece o molde",
    "Não consegui ler a capa.": "imagem que a propria tela pede (<img>)",
    "Sem foto de perfil ainda.": "imagem; a tela so pede quando o servidor diz tem_foto_perfil",
    "Não consegui ler a foto.": "imagem que a propria tela pede (<img>)",
    "Rota não encontrada.": "endereco que a tela nao usa",
    "Content-Type precisa ser application/json.": "protecao contra pedido de outro site (CSRF)",
    "Formato do lote inválido.": "sincronizacao entre dois ARENAs (programa, nao gente)",
    "Lote grande demais. Sincronize por partes.": "sincronizacao entre dois ARENAs",
    "Largura de miniatura inválida.": "a tela so pede as larguras certas",
    "Não achei ninguém com esse código na rede. Os dois precisam estar na mesma rede e com 'Aceitar "
    "conexões' ligado.": "ja diz o que e' preciso (as duas condicoes)",
}


def frases_do_servidor():
    with open(os.path.join(RAIZ, "arena.py"), encoding="utf-8") as f:
        texto = f.read()
    saida = []
    for m in re.finditer(r'self\.erro\(\s*\(?\s*((?:"(?:[^"\\]|\\.)*"\s*)+)', texto):
        frase = "".join(re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(1)))
        saida.append((texto.count("\n", 0, m.start()) + 1, frase))
    return saida


def frases_dos_modulos():
    """(modulo:linha, frase) de cada raise ValueError("...") e de cada
    return None/False, "..." dos MODULOS."""
    saida = []
    padrao = re.compile(r'(?:raise ValueError\(|return (?:None|False), \(?)\s*((?:"(?:[^"\\]|\\.)*"\s*)+)')
    for nome in MODULOS:
        with open(os.path.join(RAIZ, nome), encoding="utf-8") as f:
            texto = f.read()
        for m in padrao.finditer(texto):
            frase = "".join(re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(1)))
            saida.append(("%s:%d" % (nome, texto.count("\n", 0, m.start()) + 1), frase))
    return saida


def frases_da_tela():
    with open(os.path.join(PROJETO, "launcher", "app.js"), encoding="utf-8") as f:
        texto = f.read()
    saida = []
    for m in re.finditer(r'(recado|aviso)\(\s*(["\'])(.+?)\2\s*(,\s*true)?\s*\)', texto):
        if m.group(1) == "recado" and not m.group(4):
            continue                    # recado sem "true" nao e' erro
        saida.append((texto.count("\n", 0, m.start()) + 1, m.group(3)))
    return saida


class TestMensagensDeErro(unittest.TestCase):

    def test_toda_mensagem_do_servidor_diz_o_que_fazer(self):
        sem = ["arena.py:%d %s" % (linha, frase) for linha, frase in frases_do_servidor()
               if frase not in INTERNAS and not ACAO.search(frase)]
        self.assertEqual(sem, [], "mensagens sem 'o que fazer':\n" + "\n".join(sem))

    def test_toda_mensagem_de_erro_da_tela_diz_o_que_fazer(self):
        sem = ["app.js:%d %s" % (linha, frase) for linha, frase in frases_da_tela()
               if "${" not in frase and not ACAO.search(frase)]
        self.assertEqual(sem, [], "avisos sem 'o que fazer':\n" + "\n".join(sem))

    def test_mensagens_dos_outros_modulos_dizem_o_que_fazer(self):
        sem = ["%s %s" % (onde, frase) for onde, frase in frases_dos_modulos()
               if frase not in INTERNAS_DOS_MODULOS and not ACAO.search(frase)]
        self.assertEqual(sem, [], "mensagens sem 'o que fazer':\n" + "\n".join(sem))

    def test_a_lista_de_internas_dos_modulos_nao_tem_sobra(self):
        existentes = {frase for _onde, frase in frases_dos_modulos()}
        sobras = [frase for frase in INTERNAS_DOS_MODULOS if frase not in existentes]
        self.assertEqual(sobras, [], "mensagens internas que nao existem mais: %s" % sobras)

    def test_a_lista_de_internas_nao_tem_sobra(self):
        existentes = {frase for _linha, frase in frases_do_servidor()}
        sobras = [frase for frase in INTERNAS if frase not in existentes]
        self.assertEqual(sobras, [], "mensagens internas que nao existem mais: %s" % sobras)

    def test_sem_palavra_sem_acento(self):
        sem_acento = re.compile(r"\b(pontuacao|nao|voce|numero|codigo|versao|conexao|tambem|ja|so)\b", re.I)
        ruins = ["arena.py:%d %s" % (l, f) for l, f in frases_do_servidor() if sem_acento.search(f)]
        self.assertEqual(ruins, [], "\n".join(ruins))


if __name__ == "__main__":
    unittest.main()
