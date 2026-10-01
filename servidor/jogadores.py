# -*- coding: utf-8 -*-
"""Quantos jogadores cada JOGO aceita -- quem diz e' o professor.

O numero vem do arquivo dados\\jogadores.txt, que o professor edita num
bloco de notas:

    Super Bomberman 4 = 5
    GoldenEye = 4

Basta um pedaco do nome (sem diferenca de maiuscula). Jogo que nao aparece
no arquivo aceita 2. Linha que comeca com # e' comentario.

O ARENA cria o arquivo sozinho na primeira vez, ja com todos os jogos da
pasta e o numero que cada um aceitava antes deste arquivo existir (decisao
do Rafael, 25/09/2026): assim nada do que funcionava muda, e daqui para a
frente a fonte e' ele.

Por que em dados\\: e' a pasta do usuario. Nao vai no git e a atualizacao
do ARENA nao sobrescreve -- o que o professor escreveu fica.

O numero daqui e' o que o JOGO aceita. O que chega na tela passa ainda pelo
que o emulador do console permite (graficos.jogadores_do_jogo): escrever 10
num jogo de Super Nintendo mostra "ate 5", com o motivo no botao.
"""
import os
import re
import time

PASTA_SERVIDOR = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(PASTA_SERVIDOR)
NOME = "jogadores.txt"
# Caminho padrao. O indexador passa o dele (a mesma pasta dados\ do indice),
# para teste que troca a pasta de dados nunca escrever no dados\ real.
ARQUIVO = os.path.join(RAIZ, "dados", NOME)

PADRAO = 2
MAXIMO = 16  # ninguem precisa de mais; barra numero absurdo digitado errado

CABECALHO = """\
# QUANTOS JOGADORES CADA JOGO ACEITA
#
# Uma linha por jogo:   nome do jogo = número
# Basta um pedaço do nome. Exemplo:  Bomberman = 5
# Jogo que não estiver aqui aceita 2.
# Linha que começa com # é só comentário.
#
# O ARENA liga sozinho o adaptador de controles (multitap) quando o número
# passa de 2 e o console permite. Se o console não permitir tanto, o cartão
# mostra o máximo possível e o botão Jogar Junto explica o motivo.
#
# Criado pelo ARENA em {data}, com os jogos que estavam na pasta.
# Jogo novo que entrar depois: acrescente uma linha aqui.
"""


def ler(caminho=None):
    """Devolve a lista de regras [(pedaco_do_nome_em_minusculas, numero)],
    na ordem do arquivo; None se o arquivo ainda nao existe."""
    caminho = caminho or ARQUIVO
    try:
        with open(caminho, encoding="utf-8-sig", errors="replace") as arquivo:
            linhas = arquivo.read().splitlines()
    except FileNotFoundError:
        return None
    except OSError:
        return []
    regras = []
    for linha in linhas:
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        nome, _, numero = linha.rpartition("=")
        nome = nome.strip().lower()
        m = re.match(r"^\s*(\d+)\s*$", numero)
        if not nome or not m:
            continue  # linha torta nao derruba nada: e' ignorada
        regras.append((nome, max(1, min(int(m.group(1)), MAXIMO))))
    return regras


def numero_do_jogo(titulo, regras, outros_nomes=()):
    """O numero do jogo pelo arquivo. Nome inteiro igual ganha; senao, o
    pedaco de nome mais comprido que aparece no titulo (o mais especifico);
    senao, 2.

    'outros_nomes': outros nomes do MESMO jogo que tambem valem -- o nome
    curto do romset de fliperama ("tmnt2"), para a linha "Tmnt2 = 4" que o
    arquivo ja tem continuar valendo depois que o titulo virou o nome
    completo ("Teenage Mutant Ninja Turtles - Turtles in Time")."""
    nomes = [(titulo or "").lower()] + [(n or "").lower() for n in outros_nomes if n]
    melhor = None
    for nome, numero in regras or []:
        if nome in nomes:
            return numero
        if any(nome in n for n in nomes) and (melhor is None or len(nome) > len(melhor[0])):
            melhor = (nome, numero)
    return melhor[1] if melhor else PADRAO


def criar(jogos, caminho=None):
    """Cria o arquivo com todos os jogos da pasta, agrupados por console.
    'jogos': lista de dicionarios com 'titulo', 'plataforma_nome' e
    'jogadores_antes' (o numero que o jogo aceitava antes do arquivo).
    Nunca sobrescreve um arquivo que ja existe."""
    caminho = caminho or ARQUIVO
    if os.path.exists(caminho):
        return False
    linhas = [CABECALHO.format(data=time.strftime("%d/%m/%Y"))]
    console = None
    vistos = set()
    for jogo in sorted(jogos, key=lambda j: (j.get("plataforma_nome", ""), j["titulo"].lower())):
        if jogo["titulo"].lower() in vistos:
            continue
        vistos.add(jogo["titulo"].lower())
        if jogo.get("plataforma_nome") != console:
            console = jogo.get("plataforma_nome")
            linhas.append("\n# %s" % console)
        linhas.append("%s = %d" % (jogo["titulo"], int(jogo.get("jogadores_antes") or PADRAO)))
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    temporario = caminho + ".tmp"
    # utf-8 com BOM: o Bloco de Notas antigo do Windows abre certo os acentos.
    with open(temporario, "w", encoding="utf-8-sig", newline="\r\n") as arquivo:
        arquivo.write("\n".join(linhas) + "\n")
    os.replace(temporario, caminho)
    return True


def assinatura(caminho=None):
    """Para a lista de jogos se refazer quando o professor muda o arquivo."""
    caminho = caminho or ARQUIVO
    try:
        return "%s|%d" % (caminho, os.path.getmtime(caminho))
    except OSError:
        return "sem-jogadores"
