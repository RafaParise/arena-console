# -*- coding: utf-8 -*-
r"""Metricas do codigo do ARENA, so com a biblioteca padrao (sem pip): mede em vez de opinar.

  - tamanho de cada modulo de servidor\ e de ferramentas\ e as funcoes MAIS LONGAS e de MAIOR complexidade
    (ramos: if/for/while/except/and/or/comprehension; e' a complexidade ciclomatica aproximada de McCabe);
  - codigo morto provavel: funcao ou classe definida no nivel do modulo e que nenhum outro lugar cita pelo nome
    (nem no Python, nem em app.js, index.html, consoles.json, testes). E' PROVAVEL: nome montado em texto (getattr,
    JSON) escapa da busca, entao serve para olhar, nao para apagar;
  - modulos do servidor sem nenhum teste que os cite (servidor\tests, testes);
  - excecoes engolidas: "except ...: pass" e "except:" sem tipo;
  - TODO/FIXME/XXX esquecidos.

Uso: servidor\python\python.exe ferramentas\metricas_de_codigo.py [--saida docs\auditoria5\metricas.json]
"""
import argparse
import ast
import collections
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTAS_DE_CODIGO = ["servidor", "ferramentas"]
PASTAS_DE_TESTE = [os.path.join("servidor", "tests"), "testes"]
IGNORAR = {"__pycache__", "python", "bios_livres", "bancos_de_nomes", "filtros", "toque"}


def arquivos(pasta, extensoes):
    achados = []
    for base, subpastas, nomes in os.walk(os.path.join(RAIZ, pasta)):
        # python, python-linux, python-android...: o Python que vem junto nao e' codigo do ARENA.
        subpastas[:] = [s for s in subpastas if s not in IGNORAR and not s.startswith("python")]
        for nome in nomes:
            if nome.lower().endswith(extensoes):
                achados.append(os.path.join(base, nome))
    return sorted(achados)


def ler(caminho):
    with open(caminho, encoding="utf-8", errors="replace") as arquivo:
        return arquivo.read()


def complexidade(no):
    pontos = 1
    for filho in ast.walk(no):
        if isinstance(filho, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.ExceptHandler, ast.IfExp, ast.Assert,
                              ast.comprehension)):
            pontos += 1
        elif isinstance(filho, ast.BoolOp):
            pontos += len(filho.values) - 1
    return pontos


def main():
    analise = argparse.ArgumentParser(description="Metricas do codigo do ARENA")
    analise.add_argument("--saida", default=os.path.join(RAIZ, "docs", "auditoria5", "metricas.json"))
    argumentos = analise.parse_args()

    codigo = [c for pasta in PASTAS_DE_CODIGO for c in arquivos(pasta, (".py",))
              if not any(os.sep + p + os.sep in c for p in ("tests",))]
    testes = [c for pasta in PASTAS_DE_TESTE for c in arquivos(pasta, (".py",))]
    textos_de_busca = {c: ler(c) for c in codigo + testes}
    for extra in ("launcher/app.js", "launcher/index.html", "servidor/consoles.json", "servidor/graficos.json",
                  "servidor/acessorios.json", "servidor/recursos.json"):
        caminho = os.path.join(RAIZ, extra)
        if os.path.isfile(caminho):
            textos_de_busca[caminho] = ler(caminho)
    for caminho in arquivos("launcher", (".js",)):
        textos_de_busca.setdefault(caminho, ler(caminho))

    modulos, funcoes, engolidas, pendencias, mortos = [], [], [], [], []
    palavra = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
    contagem_total = collections.Counter()
    contagem_do_arquivo = {}
    for caminho, texto in textos_de_busca.items():
        contagem_do_arquivo[caminho] = collections.Counter(palavra.findall(texto))
        contagem_total.update(contagem_do_arquivo[caminho])
    for caminho in codigo:
        texto = textos_de_busca[caminho]
        relativo = os.path.relpath(caminho, RAIZ).replace("\\", "/")
        try:
            arvore = ast.parse(texto)
        except SyntaxError as falha:
            modulos.append({"arquivo": relativo, "erro": "sintaxe: %s" % falha})
            continue
        linhas = texto.count("\n") + 1
        modulos.append({"arquivo": relativo, "linhas": linhas})
        for no in ast.walk(arvore):
            if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef)):
                fim = getattr(no, "end_lineno", no.lineno)
                funcoes.append({"arquivo": relativo, "funcao": no.name, "linha": no.lineno, "linhas": fim - no.lineno + 1,
                                "complexidade": complexidade(no)})
            if isinstance(no, ast.ExceptHandler):
                so_pass = len(no.body) == 1 and isinstance(no.body[0], ast.Pass)
                if no.type is None:
                    engolidas.append({"arquivo": relativo, "linha": no.lineno, "tipo": "except sem tipo"})
                elif so_pass and isinstance(no.type, ast.Name) and no.type.id in ("Exception", "BaseException"):
                    engolidas.append({"arquivo": relativo, "linha": no.lineno, "tipo": "except %s: pass" % no.type.id})
        for numero, linha in enumerate(texto.splitlines(), 1):
            if re.search(r"#.*\b(TODO|FIXME|XXX|HACK)\b", linha):
                pendencias.append({"arquivo": relativo, "linha": numero, "texto": linha.strip()[:100]})
        # Nivel do modulo: funcoes e classes que ninguem cita por fora.
        for no in arvore.body:
            if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                nome = no.name
                if nome.startswith("__") or nome in ("main",) or nome.startswith("test"):
                    continue
                citacoes = contagem_total[nome]
                proprias = contagem_do_arquivo[caminho][nome]
                fora = citacoes - proprias
                if fora == 0 and proprias <= 1:
                    mortos.append({"arquivo": relativo, "nome": nome, "linha": no.lineno})

    servidor = [m for m in modulos if m["arquivo"].startswith("servidor/") and "linhas" in m]
    sem_teste = []
    palavras_dos_testes = collections.Counter()
    for c in testes:
        palavras_dos_testes.update(contagem_do_arquivo[c])
    for m in servidor:
        nome = os.path.splitext(os.path.basename(m["arquivo"]))[0]
        if not palavras_dos_testes[nome]:
            sem_teste.append(m["arquivo"])

    resultado = {
        "modulos_maiores": sorted(modulos, key=lambda m: -m.get("linhas", 0))[:15],
        "total_de_linhas_do_servidor": sum(m["linhas"] for m in servidor),
        "funcoes_mais_longas": sorted(funcoes, key=lambda f: -f["linhas"])[:20],
        "funcoes_mais_complexas": sorted(funcoes, key=lambda f: -f["complexidade"])[:20],
        "funcoes_acima_de_150_linhas": sum(1 for f in funcoes if f["linhas"] > 150),
        "funcoes_com_complexidade_acima_de_30": sum(1 for f in funcoes if f["complexidade"] > 30),
        "codigo_morto_provavel": sorted(mortos, key=lambda m: (m["arquivo"], m["linha"])),
        "modulos_do_servidor_sem_teste_que_os_cite": sem_teste,
        "excecoes_engolidas": engolidas,
        "pendencias_no_codigo": pendencias,
    }
    os.makedirs(os.path.dirname(argumentos.saida), exist_ok=True)
    with open(argumentos.saida, "w", encoding="utf-8") as arquivo:
        json.dump(resultado, arquivo, ensure_ascii=False, indent=1)
    print("Servidor: %d linhas em %d modulos. Funcoes >150 linhas: %d; complexidade >30: %d." % (
        resultado["total_de_linhas_do_servidor"], len(servidor), resultado["funcoes_acima_de_150_linhas"],
        resultado["funcoes_com_complexidade_acima_de_30"]))
    print("Codigo morto provavel: %d; excecoes engolidas: %d; modulos sem teste que os cite: %d; TODO/FIXME: %d" % (
        len(mortos), len(engolidas), len(sem_teste), len(pendencias)))
    for f in resultado["funcoes_mais_complexas"][:5]:
        print("  complexidade %3d  %4d linhas  %s:%d %s" % (f["complexidade"], f["linhas"], f["arquivo"], f["linha"], f["funcao"]))
    print("-> %s" % argumentos.saida)
    return 0


if __name__ == "__main__":
    sys.exit(main())
