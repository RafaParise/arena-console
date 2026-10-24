# -*- coding: utf-8 -*-
"""Auditoria estatica do ARENA, so com a biblioteca padrao (sem pip): confere o que se acha lendo o codigo.

  Python : arquivos que nao compilam; chamadas perigosas (eval, exec, os.system, shell=True, pickle, mktemp);
           SQL montado com texto (f-string, %, +, .format) em vez de parametros; argumento mutavel; import sem uso.
  Tela   : app.js sem erro de sintaxe (node --check, se houver node); todo #id que o app.js procura existe no
           index.html (ou e' criado por ele); toda rota /api/... que o app.js chama existe no servidor.
Uso:  servidor\\python\\python.exe ferramentas\\auditoria_estatica.py     (sai com 1 se achar problema de verdade)
"""
import ast
import glob
import os
import re
import shutil
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAMADAS_PERIGOSAS = {"eval", "exec", "system", "popen", "mktemp", "loads_inseguro"}


def arquivos_python():
    achados = []
    for pasta in ("servidor", "ferramentas"):          # os testes fingem erros de proposito (exec, shell=True)
        achados += glob.glob(os.path.join(RAIZ, pasta, "*.py"))
    return sorted(a for a in achados if os.sep + "python" + os.sep not in a)


def nome_da_chamada(no):
    f = no.func
    return f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")


def texto_montado(no):
    """True se o argumento e' um texto montado na hora (f-string, "..." % x, "..." + x, "...".format())."""
    if isinstance(no, ast.JoinedStr):
        return True
    if isinstance(no, ast.BinOp) and isinstance(no.op, (ast.Mod, ast.Add)):
        return True
    return isinstance(no, ast.Call) and nome_da_chamada(no) == "format"


def auditar_python():
    problemas, avisos = [], []
    for caminho in arquivos_python():
        rel = os.path.relpath(caminho, RAIZ)
        try:
            fonte = open(caminho, encoding="utf-8").read()
            arvore = ast.parse(fonte, caminho)
        except (SyntaxError, UnicodeDecodeError) as erro:
            problemas.append("%s: nao compila (%s)" % (rel, erro))
            continue
        importados = {}
        for no in ast.walk(arvore):
            if isinstance(no, (ast.Import, ast.ImportFrom)):
                for a in no.names:
                    importados[(a.asname or a.name).split(".")[0]] = no.lineno
            if isinstance(no, ast.Call):
                nome = nome_da_chamada(no)
                if nome in ("eval", "exec") and isinstance(no.func, ast.Name):
                    problemas.append("%s:%d: %s()" % (rel, no.lineno, nome))
                if nome in ("system", "popen") and isinstance(no.func, ast.Attribute) and \
                        getattr(no.func.value, "id", "") == "os":
                    problemas.append("%s:%d: os.%s()" % (rel, no.lineno, nome))
                if nome == "mktemp":
                    problemas.append("%s:%d: tempfile.mktemp (corrida de arquivo temporario)" % (rel, no.lineno))
                for palavra in no.keywords:
                    if palavra.arg == "shell" and isinstance(palavra.value, ast.Constant) and palavra.value.value is True:
                        problemas.append("%s:%d: subprocess com shell=True" % (rel, no.lineno))
                if nome in ("load", "loads") and getattr(no.func, "value", None) is not None and \
                        getattr(no.func.value, "id", "") in ("pickle", "marshal"):
                    problemas.append("%s:%d: %s.%s (executa codigo de quem escreveu o arquivo)" % (rel, no.lineno, no.func.value.id, nome))
                if nome in ("execute", "executemany", "executescript") and no.args and texto_montado(no.args[0])                         and "auditoria: ok" not in fonte.splitlines()[no.lineno - 1]:
                    problemas.append("%s:%d: SQL montado com texto (use parametros ?)" % (rel, no.lineno))
            if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for padrao in no.args.defaults + [d for d in no.args.kw_defaults if d is not None]:
                    if isinstance(padrao, (ast.List, ast.Dict, ast.Set)):
                        avisos.append("%s:%d: %s() tem argumento mutavel como padrao" % (rel, no.lineno, no.name))
        usados = {n.id for n in ast.walk(arvore) if isinstance(n, ast.Name)} | \
                 {n.value.id for n in ast.walk(arvore) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)}
        for nome, linha in importados.items():
            if nome not in usados and "noqa" not in fonte.splitlines()[linha - 1] and not rel.endswith("__init__.py"):
                avisos.append("%s:%d: import sem uso: %s" % (rel, linha, nome))
    return problemas, avisos


def auditar_tela():
    problemas, avisos = [], []
    app = os.path.join(RAIZ, "launcher", "app.js")
    html = open(os.path.join(RAIZ, "launcher", "index.html"), encoding="utf-8").read()
    js = open(app, encoding="utf-8").read()
    node = shutil.which("node")
    if node:
        feito = subprocess.run([node, "--check", app], capture_output=True, text=True)
        if feito.returncode:
            problemas.append("app.js: erro de sintaxe: " + feito.stderr.strip().splitlines()[-1][:160])
    else:
        avisos.append("sem node: app.js nao foi conferido por sintaxe")
    todos_os_ids = re.findall(r'\bid="([^"]+)"', html)
    for ident in sorted({i for i in todos_os_ids if todos_os_ids.count(i) > 1}):
        problemas.append("index.html tem o id %s repetido (o $('#id') acha so o primeiro)" % ident)
    ids_html = set(todos_os_ids)
    ids_criados = set(re.findall(r'\bid="([^"$\{]+)"', js)) | set(re.findall(r'\.id\s*=\s*["\']([^"\']+)', js))
    procurados = set(re.findall(r'\$\("#([A-Za-z0-9_\-]+)"\)', js)) | \
        set(re.findall(r'getElementById\("([A-Za-z0-9_\-]+)"\)', js)) | \
        set(re.findall(r'querySelector\("#([A-Za-z0-9_\-]+)"\)', js))
    for ident in sorted(procurados - ids_html - ids_criados):
        problemas.append("app.js procura #%s, que nao existe no index.html" % ident)
    servidor = open(os.path.join(RAIZ, "servidor", "arena.py"), encoding="utf-8").read()
    rotas = set(re.findall(r'caminho == "(/api/[^"]+)"', servidor))
    for grupo in re.findall(r'caminho in \(([^)]*)\)', servidor):          # if caminho in ("/api/a", "/api/b"):
        rotas |= set(re.findall(r'"(/api/[^"]+)"', grupo))
    for m in re.finditer(r'\b(?:pedir|fetch)\(\s*["`](/api/[A-Za-z0-9_\-/]+)', js):
        if m.group(1) not in rotas and m.group(1).rstrip("/") not in rotas:
            problemas.append("app.js chama %s, que o servidor nao tem" % m.group(1))
    return problemas, avisos


def principal():
    todos_problemas = 0
    for titulo, funcao in (("Python", auditar_python), ("Tela", auditar_tela)):
        problemas, avisos = funcao()
        print("== %s: %d problema(s), %d aviso(s)" % (titulo, len(problemas), len(avisos)))
        for p in problemas:
            print("  PROBLEMA:", p)
        for a in avisos[:40]:
            print("  aviso:", a)
        if len(avisos) > 40:
            print("  ... e mais %d avisos" % (len(avisos) - 40))
        todos_problemas += len(problemas)
    return 1 if todos_problemas else 0


if __name__ == "__main__":
    sys.exit(principal())
