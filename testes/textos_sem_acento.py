# -*- coding: utf-8 -*-
r"""Auditoria 2, Fase 7: frases que o servidor manda para a TELA do aluno e
que estao escritas sem acento ("nao", "esta", "so este computador"...).

Olha so o que chega na tela: self.erro("..."), recados e rotulos
devolvidos em JSON ("rotulo", "motivo", "aviso", "mensagem", "titulo",
"acao"...). Comentario e print da janela preta ficam de fora -- a janela
preta e' ASCII de proposito.

Uso:
    servidor\python\python.exe testes\textos_sem_acento.py
Sai com codigo 1 se achar alguma.
"""
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PALAVRAS = r"(?-i:\besta\b)|\b(nao|endereco|estao|voce|so|ja|tambem|numero|codigo|endereco|conexao|versao|pagina|memoria|" \
           r"atencao|invalido|invalida|possivel|disponivel|ate|ninguem|alguem|voces|entao|sera|audio|video|" \
           r"console nao|informacao|configuracao|funcao|opcao|comeco|proxima|ultima|unico)\b"
PADROES_TELA = [
    r'self\.erro\(\s*"([^"]+)"',                       # erro da API -> tela
    r'self\.erro\(\s*\(\s*"([^"]+)"',
    r'"(?:rotulo|motivo|aviso|mensagem|titulo|acao|erro|motivo_sem_partida|netplay_motivo|netplay_aviso)"\s*:\s*"([^"]+)"',
    r'return\s+"([^"]{12,})",\s*"',                     # pares (tipo, rotulo) em tuplas
]
# Nao sao frases de tela: chave interna de classe de disco (hardware.py)
# e texto da janela preta do PARTIDA.bat (ASCII de proposito).
IGNORAR = {("hardware.py", "nao medido"), ("partida.py", "(versao antiga, sem carimbo)")}


def principal():
    achados = []
    for nome in sorted(os.listdir(os.path.join(RAIZ, "servidor"))):
        if not nome.endswith((".py", ".json")):
            continue
        texto = open(os.path.join(RAIZ, "servidor", nome), encoding="utf-8").read()
        for padrao in PADROES_TELA + [r'\("[a-z_]+",\s*"([^"]+)"\)']:
            for m in re.finditer(padrao, texto):
                frase = m.group(1)
                if re.search(PALAVRAS, frase, re.I) and (nome, frase) not in IGNORAR:
                    linha = texto[:m.start()].count("\n") + 1
                    achados.append((nome, linha, frase))
    vistos = set()
    for nome, linha, frase in achados:
        if (nome, linha) in vistos:
            continue
        vistos.add((nome, linha))
        print("%s:%d  %s" % (nome, linha, frase[:110]))
    print("\n%d frase(s) sem acento que chegam na tela." % len(vistos))
    return 1 if vistos else 0


if __name__ == "__main__":
    sys.exit(principal())
