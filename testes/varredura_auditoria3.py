# -*- coding: utf-8 -*-
r"""Auditoria 3, Fase 1: varredura de codigo morto e de codigo errado.

So le os arquivos; nao muda nada. Junta o que a varredura da auditoria 1
(testes\varredura_fase1.py) e a de funcoes de JavaScript faziam separadas, e
acrescenta o que o roteiro pede agora. Gera PISTAS, nao veredito: cada
candidato ainda e' conferido a mao antes de entrar na lista de remocao, com
a prova (quem chama, onde aparece, o que quebra se sair).

  1. funcoes de Python nunca chamadas (pela arvore do codigo, nao por texto)
     -- separando as que so os testes usam;
  2. funcoes de JavaScript nunca chamadas;
  3. chaves dos arquivos .json do servidor que nenhum codigo le;
  4. arquivos do ARENA que ninguem cita (codigo, guias, .bat) e arquivos
     repetidos (mesmo conteudo);
  5. guias que citam arquivo que nao existe;
  6. restos de funcoes que sairam (gravacao de video, transmissao, "so
     assistir", DuckStation, Scroll Lock...);
  7. codigo errado: excecao engolida sem aviso, arquivo aberto sem fechar,
     gravacao que nao e' atomica, caminho absoluto, texto em ingles na tela.

Uso:
    servidor\python\python.exe testes\varredura_auditoria3.py [--saida=<arquivo.json>]
"""
import ast
import hashlib
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVIDOR = os.path.join(RAIZ, "servidor")
LAUNCHER = os.path.join(RAIZ, "launcher")
DE_FORA = {"retroarch", "emuladores", "dados", "jogos", "backup", "BIOS", "perfil", ".git"}


def ler(caminho):
    with open(caminho, encoding="utf-8", errors="ignore") as f:
        return f.read()


def rel(caminho):
    return os.path.relpath(caminho, RAIZ)


def arquivos(pasta, extensoes, pular=("python", "__pycache__")):
    saida = []
    for atual, subs, nomes in os.walk(pasta):
        subs[:] = [s for s in subs if s not in pular]
        saida += [os.path.join(atual, n) for n in nomes if n.lower().endswith(extensoes)]
    return sorted(saida)


PY_PRODUTO = [c for c in arquivos(SERVIDOR, (".py",), ("python", "__pycache__", "tests"))]
PY_TESTES = arquivos(os.path.join(RAIZ, "testes"), (".py",)) + arquivos(os.path.join(SERVIDOR, "tests"), (".py",))
PY_FERRAMENTAS = arquivos(os.path.join(RAIZ, "ferramentas"), (".py",))
JS = arquivos(LAUNCHER, (".js",))
HTML = arquivos(LAUNCHER, (".html",))
CSS = arquivos(LAUNCHER, (".css",))
GUIAS = sorted(os.path.join(RAIZ, n) for n in os.listdir(RAIZ) if n.lower().endswith((".md", ".txt")))
BATS = sorted(os.path.join(RAIZ, n) for n in os.listdir(RAIZ) if n.lower().endswith(".bat"))
TEXTO = {c: ler(c) for c in PY_PRODUTO + PY_TESTES + PY_FERRAMENTAS + JS + HTML + CSS + GUIAS + BATS}


# --------------------------------------------------------------------------
# 1. Funcoes de Python nunca chamadas
# --------------------------------------------------------------------------

# Chamados pelo proprio Python ou pelo servidor HTTP, nao pelo ARENA.
CHAMADOS_DE_FORA = re.compile(r"^(__\w+__|do_[A-Z]+|log_message|log_request|log_error|handle\w*|setUp|tearDown|"
                              r"setUpClass|tearDownClass|test\w*|run|main|principal)$")


def nomes_usados(caminhos):
    """Todo nome lido (variavel, atributo) e todo texto que parece nome, nos arquivos."""
    usados = {}
    for caminho in caminhos:
        texto = TEXTO[caminho]
        try:
            arvore = ast.parse(texto)
        except SyntaxError:
            continue
        for no in ast.walk(arvore):
            if isinstance(no, ast.Name) and isinstance(no.ctx, ast.Load):
                usados.setdefault(no.id, set()).add(rel(caminho))
            elif isinstance(no, ast.Attribute):
                usados.setdefault(no.attr, set()).add(rel(caminho))
            elif isinstance(no, ast.Constant) and isinstance(no.value, str) and re.fullmatch(r"\w+", no.value):
                usados.setdefault(no.value, set()).add(rel(caminho))     # getattr(modulo, "nome")
    return usados


def funcoes_python_mortas():
    produto = nomes_usados(PY_PRODUTO)
    testes = nomes_usados(PY_TESTES + PY_FERRAMENTAS)
    mortas, so_testes = [], []
    for caminho in PY_PRODUTO:
        arvore = ast.parse(TEXTO[caminho])
        for no in ast.walk(arvore):
            if not isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef)) or CHAMADOS_DE_FORA.match(no.name):
                continue
            item = {"funcao": no.name, "arquivo": rel(caminho), "linha": no.lineno}
            if no.name not in produto:
                (so_testes if no.name in testes else mortas).append(dict(item, usada_por=sorted(testes.get(no.name, [])))
                                                                    if no.name in testes else item)
    return mortas, so_testes


# --------------------------------------------------------------------------
# 2. Funcoes de JavaScript nunca chamadas
# --------------------------------------------------------------------------

def funcoes_js_mortas():
    todo_js = "\n".join(TEXTO[c] for c in JS + HTML)
    mortas = []
    for caminho in JS:
        for m in re.finditer(r"\bfunction\s+([A-Za-z_]\w*)\s*\(", TEXTO[caminho]):
            nome = m.group(1)
            if len(re.findall(r"\b%s\b" % re.escape(nome), todo_js)) <= 1:
                mortas.append({"funcao": nome, "arquivo": rel(caminho),
                               "linha": TEXTO[caminho].count("\n", 0, m.start()) + 1})
    return mortas


# --------------------------------------------------------------------------
# 3. Chaves dos .json do servidor que nenhum codigo le
# --------------------------------------------------------------------------

def chaves(dados, caminho=""):
    if isinstance(dados, dict):
        for k, v in dados.items():
            yield k, caminho
            yield from chaves(v, caminho + "/" + k)
    elif isinstance(dados, list):
        for v in dados:
            yield from chaves(v, caminho + "[]")


def chaves_json_sem_leitor():
    codigo = "\n".join(TEXTO[c] for c in PY_PRODUTO + JS)
    saida = {}
    for nome in sorted(os.listdir(SERVIDOR)):
        if not nome.endswith(".json"):
            continue
        with open(os.path.join(SERVIDOR, nome), encoding="utf-8") as f:
            dados = json.load(f)
        sem = {}
        for chave, onde in chaves(dados):
            # So chave com cara de nome de campo (as de dados -- titulos de
            # jogo, ids de console, opcoes de nucleo -- nao se leem pelo nome).
            if not re.fullmatch(r"[a-z][a-z0-9_]{2,40}", chave) or "_libretro" in chave:
                continue
            if re.search(r"""["'.]%s["'\]\s,:)]""" % re.escape(chave), codigo):
                continue
            sem.setdefault(chave, onde or "/")
        if sem:
            saida[nome] = sem
    return saida


# --------------------------------------------------------------------------
# 4. Arquivos que ninguem cita e arquivos repetidos
# --------------------------------------------------------------------------

def arquivos_do_arena():
    saida = []
    for atual, subs, nomes in os.walk(RAIZ):
        r = os.path.relpath(atual, RAIZ)
        partes = [] if r == "." else r.split(os.sep)
        if partes and partes[0] in DE_FORA:
            subs[:] = []
            continue
        subs[:] = [s for s in subs if s != "__pycache__" and not (partes == ["servidor"] and s == "python")]
        saida += [os.path.join(atual, n) for n in nomes]
    return sorted(saida)


def citacoes():
    todos = arquivos_do_arena()
    textos = {}
    for c in todos:
        if c.lower().endswith((".py", ".js", ".html", ".css", ".md", ".txt", ".bat", ".ps1", ".json")):
            textos[c] = ler(c)
    sem_citacao, repetidos, por_hash = [], [], {}
    for c in todos:
        nome = os.path.basename(c)
        base = os.path.splitext(nome)[0]
        if rel(c).split(os.sep)[0] in ("docs",) and nome.endswith(".json"):
            continue                       # numeros brutos das auditorias
        citado = any(o != c and (nome in t or (c.endswith(".py") and re.search(r"\bimport\s+%s\b|\bfrom\s+%s\b"
                                                                                 % (base, base), t)))
                     for o, t in textos.items())
        if not citado:
            sem_citacao.append(rel(c))
        with open(c, "rb") as f:
            por_hash.setdefault(hashlib.sha256(f.read()).hexdigest(), []).append(rel(c))
    repetidos = [grupo for grupo in por_hash.values() if len(grupo) > 1]
    return sem_citacao, repetidos


# --------------------------------------------------------------------------
# 5. Guias que citam arquivo que nao existe
# --------------------------------------------------------------------------

def citacoes_quebradas():
    existentes = {os.path.basename(c).lower() for c in arquivos_do_arena()}
    for pasta in ("retroarch", "emuladores"):
        for atual, _subs, nomes in os.walk(os.path.join(RAIZ, pasta)):
            existentes |= {n.lower() for n in nomes}
            if atual.count(os.sep) - RAIZ.count(os.sep) > 3:
                break
    saida = []
    padrao = re.compile(r"[\w.-]+\.(?:bat|py|json|md|ps1|exe)\b")
    for c in GUIAS + [x for x in arquivos_do_arena() if x.endswith(".md") and os.sep + "docs" + os.sep not in x]:
        for m in padrao.finditer(TEXTO.get(c) or ler(c)):
            nome = m.group(0).strip(".").lower()
            if nome not in existentes and not nome.startswith(("http", "www")):
                saida.append({"guia": rel(c), "cita": m.group(0)})
    vistos, unicos = set(), []
    for item in saida:
        chave = (item["guia"], item["cita"].lower())
        if chave not in vistos:
            vistos.add(chave)
            unicos.append(item)
    return unicos


# --------------------------------------------------------------------------
# 6. Restos de funcoes que sairam
# --------------------------------------------------------------------------

REMOVIDAS = {
    "gravacao de video / transmissao": r"grava[cç][aã]o de v[ií]deo|gravar_video|video_record|record_driver|"
                                       r"streaming|stream_|transmiss|twitch|youtube|ffmpeg",
    "so assistir": r"s[oó] assistir|assistir|spectat",
    "DuckStation": r"duckstation",
    "Scroll Lock": r"scroll.?lock|scrolllock",
}


def restos():
    saida = {}
    for rotulo, padrao in REMOVIDAS.items():
        achados = []
        for c in PY_PRODUTO + JS + HTML + GUIAS + BATS + [os.path.join(SERVIDOR, n) for n in os.listdir(SERVIDOR)
                                                           if n.endswith(".json")]:
            texto = TEXTO.get(c) or ler(c)
            for numero, linha in enumerate(texto.splitlines(), 1):
                if re.search(padrao, linha, re.I):
                    achados.append("%s:%d: %s" % (rel(c), numero, linha.strip()[:140]))
        saida[rotulo] = achados
    return saida


# --------------------------------------------------------------------------
# 7. Codigo errado
# --------------------------------------------------------------------------

def excecoes_engolidas():
    """except que so faz pass/continue/return (sem aviso nenhum)."""
    saida = []
    for c in PY_PRODUTO:
        arvore = ast.parse(TEXTO[c])
        linhas = TEXTO[c].splitlines()
        for no in ast.walk(arvore):
            if not isinstance(no, ast.ExceptHandler):
                continue
            corpo = no.body
            calado = all(isinstance(x, (ast.Pass, ast.Continue)) or
                         (isinstance(x, ast.Return) and (x.value is None or isinstance(x.value, ast.Constant)))
                         for x in corpo)
            if not calado:
                continue
            tipo = ast.unparse(no.type) if no.type is not None else "(tudo)"
            largo = no.type is None or tipo in ("Exception", "BaseException") or "Exception" in tipo
            saida.append({"arquivo": rel(c), "linha": no.lineno, "captura": tipo, "largo": largo,
                          "faz": ast.unparse(corpo[0])[:40],
                          "trecho": linhas[no.lineno - 2].strip()[:100] if no.lineno >= 2 else ""})
    return saida


def abertos_sem_fechar():
    """open(...) fora de um with (o arquivo fica aberto ate o coletor passar)."""
    saida = []
    for c in PY_PRODUTO:
        arvore = ast.parse(TEXTO[c])
        dentro_de_with = set()
        for no in ast.walk(arvore):
            if isinstance(no, (ast.With, ast.AsyncWith)):
                for item in no.items:
                    dentro_de_with.add(id(item.context_expr))
        for no in ast.walk(arvore):
            # So o open() do Python (zipfile.open, webbrowser.open... sao outros).
            if isinstance(no, ast.Call) and isinstance(no.func, ast.Name) and no.func.id == "open" \
                    and id(no) not in dentro_de_with:
                saida.append({"arquivo": rel(c), "linha": no.lineno,
                              "trecho": TEXTO[c].splitlines()[no.lineno - 1].strip()[:110]})
    return saida


def gravacoes_nao_atomicas():
    """open(..., "w"/"wb"/"a") direto no destino, sem temporario + os.replace."""
    saida = []
    for c in PY_PRODUTO:
        linhas = TEXTO[c].splitlines()
        for numero, linha in enumerate(linhas, 1):
            if re.search(r"""open\([^)]*,\s*["'](w|wb|a|ab|w\+)["']""", linha) or "write_text(" in linha:
                perto = "\n".join(linhas[max(0, numero - 8):numero + 8])
                atomica = "os.replace" in perto or "temporario" in perto or ".tmp" in perto
                saida.append({"arquivo": rel(c), "linha": numero, "atomica_perto": atomica,
                              "trecho": linha.strip()[:110]})
    return saida


def caminhos_absolutos():
    saida = []
    padrao = re.compile(r"""["'](?:[A-Za-z]:[\\/]|\\\\\\\\|/Users/|/home/)[^"']*["']""")
    for c in PY_PRODUTO + JS + BATS:
        for numero, linha in enumerate(TEXTO[c].splitlines(), 1):
            for m in padrao.finditer(linha):
                saida.append({"arquivo": rel(c), "linha": numero, "texto": m.group(0)[:100]})
    return saida


INGLES = re.compile(r"\b(loading|error|failed|warning|success|settings|cancel|close|open|save|load|delete|"
                    r"remove|update|download|upload|search|click|please|not found|unknown|invalid|"
                    r"retry|done|next|back|yes|no|ok|submit)\b", re.I)


def ingles_na_tela():
    """Texto visivel em ingles: no index.html (fora das etiquetas) e nas
    frases que o app.js poe na tela (recado, aviso, textContent...)."""
    saida = []
    for c in HTML:
        texto = re.sub(r"<script.*?</script>|<style.*?</style>", "", TEXTO[c], flags=re.S)
        for numero, linha in enumerate(texto.splitlines(), 1):
            visivel = re.sub(r"<[^>]+>", " ", linha)
            atributos = " ".join(re.findall(r'(?:title|aria-label|placeholder|alt)="([^"]*)"', linha))
            for pedaco in (visivel, atributos):
                if INGLES.search(pedaco) and not re.search(r"[áéíóúãõçâêô]", pedaco):
                    saida.append("%s:%d: %s" % (rel(c), numero, pedaco.strip()[:120]))
    frases = re.compile(r"""(?:recado|aviso|textContent\s*=|innerText\s*=|title\s*=|alert)\s*\(?\s*["'`]([^"'`]{3,})""")
    for c in JS:
        for numero, linha in enumerate(TEXTO[c].splitlines(), 1):
            for m in frases.finditer(linha):
                if INGLES.search(m.group(1)) and not re.search(r"[áéíóúãõçâêô]", m.group(1)):
                    saida.append("%s:%d: %s" % (rel(c), numero, m.group(1)[:120]))
    return saida


def principal():
    destino = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--saida=")),
                   os.path.join(RAIZ, "docs", "auditoria3", "varredura_fase1.json"))
    if not os.path.isabs(destino):
        destino = os.path.join(RAIZ, destino)
    mortas, so_testes = funcoes_python_mortas()
    sem_citacao, repetidos = citacoes()
    resultado = {
        "funcoes_python_mortas": mortas,
        "funcoes_python_so_dos_testes": so_testes,
        "funcoes_js_mortas": funcoes_js_mortas(),
        "chaves_json_sem_leitor": chaves_json_sem_leitor(),
        "arquivos_sem_citacao": sem_citacao,
        "arquivos_repetidos": repetidos,
        "guias_citando_o_que_nao_existe": citacoes_quebradas(),
        "restos_de_funcoes_removidas": restos(),
        "excecoes_engolidas": excecoes_engolidas(),
        "abertos_sem_fechar": abertos_sem_fechar(),
        "gravacoes_nao_atomicas": gravacoes_nao_atomicas(),
        "caminhos_absolutos": caminhos_absolutos(),
        "ingles_na_tela": ingles_na_tela(),
    }
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(destino, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    for chave, valor in resultado.items():
        quantos = sum(len(v) for v in valor.values()) if isinstance(valor, dict) else len(valor)
        print("%-34s %d" % (chave, quantos))
    print("Pistas salvas em", destino)


if __name__ == "__main__":
    principal()
