# -*- coding: utf-8 -*-
r"""Inventario do ARENA lido direto do codigo (auditorias 2 e 3).

Nao sobe servidor nem mexe em nada: so le os arquivos. Imprime um resumo e
grava o inventario inteiro em JSON:

  - arquivos: todos os do ARENA (tamanho e linhas) e, das pastas de
    terceiros e de quem usa (RetroArch, emuladores, Python embutido, dados,
    jogos, BIOS), a contagem e o tamanho por subpasta;
  - rotas da API (GET/POST), quem chama cada uma (tela -- e de qual funcao
    --, PARTIDA.bat, outro ARENA pela rede) e quais ficam abertas a rede;
  - a TELA (auditoria 3): cada janela, aba, botao, chave e lista, e a rota
    que cada um usa (seguindo as funcoes do app.js), os botoes que o
    app.js cria sozinho, botao sem acao, acao sem botao e rota pedida pela
    tela que o servidor nao tem;
  - os temporizadores da tela (setInterval, setTimeout, requestAnimationFrame);
  - chaves de configuracao (config_padrao e as opcoes avancadas) e em que
    arquivos sao lidas;
  - linhas de execucao do servidor: onde nascem, a funcao, de quanto em
    quanto tempo acordam e o comentario que explica o motivo;
  - tudo que sai para a internet (enderecos fixos no codigo).

Uso:
    servidor\python\python.exe testes\inventario.py [--saida=<arquivo.json>]
"""
import html.parser
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IGNORAR_TOPO = {"jogos", ".git", "backup"}
PRODUTO_EXT = (".py", ".js", ".html", ".css", ".json", ".bat", ".md")
TEXTO_EXT = (".py", ".js", ".html", ".css", ".json", ".bat", ".ps1", ".md", ".txt", ".ini", ".cfg")
# Pastas que nao sao codigo do ARENA: de terceiros ou de quem usa.
DE_FORA = ("retroarch", "emuladores", "dados", "jogos", "backup", "BIOS", "perfil", ".git")
RE_ROTA_JS = re.compile(r"""["'`](/api/[a-z0-9/_-]+)""")


def ler(rel):
    with open(os.path.join(RAIZ, rel), encoding="utf-8", errors="replace") as f:
        return f.read()


def linha_de(texto, posicao):
    return texto.count("\n", 0, posicao) + 1


# --------------------------------------------------------------------------
# Arquivos
# --------------------------------------------------------------------------

def arquivos_por_pasta():
    saida = {}
    for atual, subs, arquivos in os.walk(RAIZ):
        rel = os.path.relpath(atual, RAIZ)
        topo = rel.split(os.sep)[0] if rel != "." else "(raiz)"
        if topo in IGNORAR_TOPO:
            subs[:] = []
            continue
        info = saida.setdefault(topo, {"arquivos": 0, "mb": 0.0})
        for n in arquivos:
            try:
                info["mb"] += os.path.getsize(os.path.join(atual, n)) / 1024 ** 2
                info["arquivos"] += 1
            except OSError:
                pass
    return {k: {"arquivos": v["arquivos"], "mb": round(v["mb"], 1)}
            for k, v in sorted(saida.items(), key=lambda kv: -kv[1]["mb"])}


def arquivos_do_arena():
    """Todos os arquivos que sao do ARENA (fora: terceiros e quem usa)."""
    saida = []
    for atual, subs, arquivos in os.walk(RAIZ):
        rel_pasta = os.path.relpath(atual, RAIZ)
        partes = [] if rel_pasta == "." else rel_pasta.split(os.sep)
        if partes and partes[0] in DE_FORA:
            subs[:] = []
            continue
        subs[:] = [s for s in subs if s != "__pycache__" and not (partes == ["servidor"] and s == "python")]
        for n in arquivos:
            rel = os.path.normpath(os.path.join(rel_pasta, n))
            caminho = os.path.join(RAIZ, rel)
            try:
                tamanho = os.path.getsize(caminho)
            except OSError:
                continue
            linhas = None
            if n.lower().endswith(TEXTO_EXT):
                with open(caminho, "rb") as f:
                    linhas = f.read().count(b"\n")
            saida.append({"arquivo": rel, "kb": round(tamanho / 1024, 1), "linhas": linhas})
    return sorted(saida, key=lambda a: a["arquivo"].lower())


def pastas_de_fora():
    """Contagem e tamanho das pastas que nao sao codigo do ARENA, por subpasta."""
    saida = {}
    alvos = [p for p in DE_FORA if p != ".git"] + [os.path.join("servidor", "python")]
    for alvo in alvos:
        base = os.path.join(RAIZ, alvo)
        if not os.path.isdir(base):
            continue
        sub = {}
        for atual, _subs, arquivos in os.walk(base):
            rel = os.path.relpath(atual, base)
            chave = rel.split(os.sep)[0] if rel != "." else "(solto)"
            info = sub.setdefault(chave, [0, 0])
            for n in arquivos:
                try:
                    info[1] += os.path.getsize(os.path.join(atual, n))
                    info[0] += 1
                except OSError:
                    pass
        saida[alvo] = {
            "arquivos": sum(v[0] for v in sub.values()),
            "mb": round(sum(v[1] for v in sub.values()) / 1024 ** 2, 1),
            "subpastas": {k: {"arquivos": v[0], "mb": round(v[1] / 1024 ** 2, 1)}
                          for k, v in sorted(sub.items(), key=lambda kv: -kv[1][1])},
        }
    return saida


def e_do_produto(rel):
    partes = rel.replace("\\", "/").split("/")
    if not rel.endswith(PRODUTO_EXT):
        return False
    if partes[0] in ("testes", "docs", "ferramentas", "dados", "jogos", "retroarch",
                     "emuladores", "backup", "perfil", ".git", "BIOS"):
        return False
    if partes[0] == "servidor" and len(partes) > 1 and partes[1] in ("tests", "python", "__pycache__"):
        return False
    return True


def linhas_do_produto(arquivos):
    saida = {a["arquivo"]: a["linhas"] for a in arquivos if e_do_produto(a["arquivo"]) and a["linhas"] is not None}
    return dict(sorted(saida.items(), key=lambda kv: -kv[1]))


# --------------------------------------------------------------------------
# Funcoes do JavaScript (para seguir de um botao ate a rota)
# --------------------------------------------------------------------------

def fim_do_parenteses(texto, inicio, profundidade=1):
    """Posicao logo depois do ')' que fecha o '(' ja aberto antes de 'inicio'.
    Pula textos entre aspas (inclusive `...`) para nao contar parenteses deles."""
    i, n = inicio, len(texto)
    while i < n:
        c = texto[i]
        if c in "\"'`":
            j = i + 1
            while j < n and texto[j] != c:
                j += 2 if texto[j] == "\\" else 1
            i = j + 1
            continue
        if c == "/" and texto[i:i + 2] == "//":
            fim = texto.find("\n", i)
            i = n if fim < 0 else fim
            continue
        if c == "(":
            profundidade += 1
        elif c == ")":
            profundidade -= 1
            if profundidade == 0:
                return i + 1
        i += 1
    return n


def funcoes_js(texto):
    """Funcoes de primeiro nivel: nome -> (inicio, fim) no texto."""
    marcas = [(m.start(), m.group(2)) for m in re.finditer(r"^(async\s+)?function\s+(\w+)\s*\(", texto, re.M)]
    return {nome: (inicio, marcas[i + 1][0] if i + 1 < len(marcas) else len(texto))
            for i, (inicio, nome) in enumerate(marcas)}


def funcao_em(funcoes, posicao):
    for nome, (inicio, fim) in funcoes.items():
        if inicio <= posicao < fim:
            return nome
    return "(fora de funcao)"


def tirar_ligacoes(corpo):
    """O corpo sem o que so roda num clique futuro: o segundo argumento de
    cada addEventListener e cada .onclick = ... Uma funcao que desenha uma
    lista e prende um clique em cada item nao pede, ela mesma, as rotas
    desses cliques."""
    pedacos, i = [], 0
    for m in re.finditer(r"""\.addEventListener\(\s*["']\w+["']\s*,|\.on\w+\s*=(?!=)""", corpo):
        if m.start() < i:
            continue
        pedacos.append(corpo[i:m.end()])
        if m.group(0).startswith(".addEventListener"):
            fim = fim_do_parenteses(corpo, m.end())
            i = fim - 1
        else:
            fim = corpo.find(";", m.end())
            i = len(corpo) if fim < 0 else fim
    pedacos.append(corpo[i:])
    return "".join(pedacos)


def info_das_funcoes(texto, funcoes):
    """Para cada funcao: rotas que ela pede direto e funcoes que ela chama
    (sem contar o que ela so prende para um clique futuro)."""
    nomes = set(funcoes)
    info = {}
    for nome, (inicio, fim) in funcoes.items():
        corpo = tirar_ligacoes(texto[inicio:fim])
        chama = {c for c in re.findall(r"\b([A-Za-z_]\w*)\s*\(", corpo[corpo.find("{"):]) if c in nomes and c != nome}
        info[nome] = {"rotas": set(RE_ROTA_JS.findall(corpo)), "chama": chama}
    return info


def corpo_do_laco(texto, posicao):
    """Se 'posicao' esta na lista de um for (... of [...]), devolve o corpo
    do laco; senao, None."""
    inicio = texto.rfind("for (", max(0, posicao - 400), posicao)
    if inicio < 0:
        return None
    fim_cabeca = fim_do_parenteses(texto, inicio + len("for ("))
    if not (inicio < posicao < fim_cabeca):
        return None
    chave = texto.find("{", fim_cabeca)
    if chave < 0 or texto[fim_cabeca:chave].strip():
        return None
    nivel = 0
    for j in range(chave, len(texto)):
        if texto[j] == "{":
            nivel += 1
        elif texto[j] == "}":
            nivel -= 1
            if nivel == 0:
                return texto[chave:j + 1]
    return None


def rotas_alcancadas(trecho, info, profundidade=4):
    """Rotas que um trecho de codigo pede: direto e pelas funcoes que chama."""
    rotas = set(RE_ROTA_JS.findall(trecho))
    # Com ou sem parenteses: addEventListener("click", enviarRecordes) passa
    # a propria funcao.
    fila = [(c, 1) for c in re.findall(r"\b([A-Za-z_]\w*)\b", trecho) if c in info]
    vistas, funcoes = set(), set()
    while fila:
        nome, nivel = fila.pop()
        if nome in vistas or nivel > profundidade:
            continue
        vistas.add(nome)
        funcoes.add(nome)
        rotas |= info[nome]["rotas"]
        fila.extend((c, nivel + 1) for c in info[nome]["chama"])
    return sorted(rotas), sorted(funcoes)


# --------------------------------------------------------------------------
# A tela: janelas, abas, botoes e chaves do index.html
# --------------------------------------------------------------------------

VAZIOS = {"input", "img", "br", "hr", "meta", "link", "source", "area", "base", "col", "embed", "wbr"}
INTERESSA = {"button", "input", "select", "textarea", "details"}


class LeitorDaTela(html.parser.HTMLParser):
    """Le o index.html guardando, para cada controle, a janela (gaveta ou
    modal) e a aba em que ele mora."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.pilha = []          # (tag, atributos)
        self.controles = []
        self.janelas = {}
        self.texto_do = None     # controle (button/details) cujo texto esta sendo lido
        self.titulo_da = None    # janela cujo titulo (h2/h3) esta sendo lido

    def contexto(self):
        janela = aba = ""
        for _tag, a in self.pilha:
            classes = (a.get("class") or "").split()
            if ("gaveta" in classes or "modal" in classes) and a.get("id"):
                janela = a["id"]
            if a.get("data-painel"):
                aba = a["data-painel"]
        return janela, aba

    def handle_starttag(self, tag, attrs):
        a = {k: (v or "") for k, v in attrs}
        classes = (a.get("class") or "").split()
        if ("gaveta" in classes or "modal" in classes) and a.get("id"):
            self.janelas[a["id"]] = {"tipo": "gaveta" if "gaveta" in classes else "modal", "titulo": ""}
        if tag in ("h2", "h3"):
            janela, _aba = self.contexto()
            if janela and not self.janelas.get(janela, {}).get("titulo"):
                self.titulo_da = janela
        if tag in INTERESSA:
            janela, aba = self.contexto()
            item = {"tag": tag, "id": a.get("id", ""), "tipo": a.get("type", ""), "classe": a.get("class", ""),
                    "aba_alvo": a.get("data-aba", ""), "fecha": a.get("data-fechar", ""),
                    "rotulo": a.get("aria-label") or a.get("title") or a.get("placeholder") or "",
                    "janela": janela or "(tela principal)", "aba": aba, "texto": "",
                    "atributos_data": sorted(k for k in a if k.startswith("data-")
                                             and k not in ("data-aba", "data-fechar", "data-painel")),
                    "linha": self.getpos()[0]}
            self.controles.append(item)
            if tag in ("button", "details"):
                self.texto_do = item
        if tag not in VAZIOS:
            self.pilha.append((tag, a))

    def handle_endtag(self, tag):
        if tag in ("button", "summary") and self.texto_do is not None:
            self.texto_do["texto"] = " ".join(self.texto_do["texto"].split())[:80]
            if tag == "button":
                self.texto_do = None
        if tag in ("h2", "h3"):
            self.titulo_da = None
        for i in range(len(self.pilha) - 1, -1, -1):
            if self.pilha[i][0] == tag:
                del self.pilha[i:]
                break

    def handle_data(self, dados):
        if self.texto_do is not None:
            self.texto_do["texto"] += dados
        if self.titulo_da:
            janela = self.janelas[self.titulo_da]
            janela["titulo"] = (janela["titulo"] + " " + dados).strip()[:80]


def ligacoes_por_id(texto, info):
    """$("#id").addEventListener("evento", ...) e getElementById: o que cada
    elemento faz e as rotas que pede."""
    saida = {}
    padrao = re.compile(r"""(?:\$\(\s*["']#([\w-]+)["']\s*\)|document\.getElementById\(\s*["']([\w-]+)["']\s*\))"""
                        r"""\s*\.addEventListener\(\s*["'](\w+)["']\s*,""")
    funcoes = funcoes_js(texto)
    for m in padrao.finditer(texto):
        ident = m.group(1) or m.group(2)
        fim = fim_do_parenteses(texto, m.end())
        trecho = texto[m.end():fim - 1]
        rotas, chamadas = rotas_alcancadas(trecho, info)
        saida.setdefault(ident, []).append({"evento": m.group(3), "rotas": rotas, "funcoes": chamadas,
                                           "ligado_em": funcao_em(funcoes, m.start()),
                                           "linha": linha_de(texto, m.start())})
    # $("#id").onclick = funcao  e  const x = $("#id"); x.onclick/addEventListener
    for m in re.finditer(r"""\$\(\s*["']#([\w-]+)["']\s*\)\.on(\w+)\s*=\s*([^;\n]+)""", texto):
        rotas, chamadas = rotas_alcancadas(m.group(3), info)
        saida.setdefault(m.group(1), []).append({"evento": m.group(2), "rotas": rotas, "funcoes": chamadas,
                                                "ligado_em": funcao_em(funcoes, m.start()),
                                                "linha": linha_de(texto, m.start())})
    for nome, (inicio, fim) in funcoes.items():
        corpo = texto[inicio:fim]
        for m in re.finditer(r"""(?:const|let)\s+(\w+)\s*=\s*\$\(\s*["']#([\w-]+)["']\s*\)\s*;""", corpo):
            var, ident = m.group(1), m.group(2)
            for c in re.finditer(r"\b%s\.(?:addEventListener\(\s*[\"'](\w+)[\"']\s*,|on(\w+)\s*=)" % re.escape(var),
                                 corpo):
                fim_c = fim_do_parenteses(corpo, c.end()) if c.group(1) else corpo.find("\n", c.end())
                rotas, chamadas = rotas_alcancadas(corpo[c.end():fim_c], info)
                saida.setdefault(ident, []).append({"evento": c.group(1) or c.group(2), "rotas": rotas,
                                                    "funcoes": chamadas, "ligado_em": nome,
                                                    "linha": linha_de(texto, inicio + c.start())})
    return saida


def ligacoes_indiretas(texto, info, ids, atributos):
    """O que nao foi ligado pelo id direto: o id aparece numa lista do
    app.js (ex.: [["btnFavoritos", "favoritos"], ...] num laco) ou o
    elemento e' achado pelo atributo (querySelectorAll("[data-papel]"))."""
    funcoes = funcoes_js(texto)
    saida = {}
    for ident in ids:
        achados = list(re.finditer(r"""["']%s["']""" % re.escape(ident), texto))
        # Prefere a lista de um laco que prende clique em cada id.
        escolhido, corpo = None, None
        for m in achados:
            laco = corpo_do_laco(texto, m.start())
            if laco and re.search(r"addEventListener|\.on\w+\s*=", laco):
                escolhido, corpo = m, laco
                break
        if escolhido is None and achados:
            escolhido = achados[0]
        if escolhido is not None:
            nome = funcao_em(funcoes, escolhido.start())
            rotas, chamadas = rotas_alcancadas(corpo, info) if corpo else ([], [])
            saida[ident] = {"como": "ligado num laco do app.js (linha %d, em %s)" % (linha_de(texto, escolhido.start()),
                                                                                       nome) if corpo else
                            "o id aparece no app.js (linha %d, em %s)" % (linha_de(texto, escolhido.start()), nome),
                            "rotas": rotas, "funcoes": chamadas}
    for atributo in atributos:
        m = re.search(r"\[%s\]|dataset\.%s\b" % (re.escape(atributo), re.escape(
            re.sub(r"-(\w)", lambda x: x.group(1).upper(), atributo[5:]))), texto)
        if m:
            saida["[%s]" % atributo] = {"como": "achado pelo atributo %s (linha %d)" % (atributo, linha_de(texto, m.start())),
                                        "rotas": [], "funcoes": []}
    return saida


def botoes_criados_pelo_js(texto, info):
    """Botoes que o app.js cria sozinho (createElement("button")): texto,
    funcao que cria e a rota do clique."""
    saida = []
    funcoes = funcoes_js(texto)
    for nome, (inicio, fim) in funcoes.items():
        corpo = texto[inicio:fim]
        for m in re.finditer(r"""(?:const|let|var)\s+(\w+)\s*=\s*document\.createElement\(\s*["']button["']\s*\)""",
                             corpo):
            var = m.group(1)
            textos = re.findall(r"\b%s\.(?:textContent|innerText)\s*=\s*([^;\n]+)" % re.escape(var), corpo)
            cliques = []
            for c in re.finditer(r"\b%s\.addEventListener\(\s*[\"'](\w+)[\"']\s*," % re.escape(var), corpo):
                fim_c = fim_do_parenteses(corpo, c.end())
                rotas, chamadas = rotas_alcancadas(corpo[c.end():fim_c - 1], info)
                cliques.append({"evento": c.group(1), "rotas": rotas, "funcoes": chamadas})
            saida.append({"funcao": nome, "variavel": var, "texto": [t.strip()[:60] for t in textos][:3],
                          "linha": linha_de(texto, inicio + m.start()), "acoes": cliques})
    return saida


def tela(rotas_do_servidor):
    html_texto = ler(os.path.join("launcher", "index.html"))
    js = ler(os.path.join("launcher", "app.js"))
    leitor = LeitorDaTela()
    leitor.feed(html_texto)
    funcoes = funcoes_js(js)
    info = info_das_funcoes(js, funcoes)
    por_id = ligacoes_por_id(js, info)
    # Abas: o clique e' tratado num lugar so (grupo .abas); algumas abas
    # montam o conteudo na primeira vez (montarAbaControles, carregarBios).
    abas_especiais = {}
    for m in re.finditer(r'aba\.dataset\.aba === "(\w+)"[^;\n]*?(\w+)\(\)', js):
        abas_especiais[m.group(1)] = rotas_alcancadas(m.group(2) + "()", info)[0]
    sem_ligacao = [c["id"] for c in leitor.controles if c["id"] and c["id"] not in por_id]
    atributos = sorted(set(re.findall(r"\b(data-[a-z-]+)=", html_texto)) - {"data-aba", "data-fechar", "data-painel"})
    indiretas = ligacoes_indiretas(js, info, sem_ligacao, atributos)
    controles = []
    for c in leitor.controles:
        ligacoes = por_id.get(c["id"], []) if c["id"] else []
        rotas = sorted({r for l in ligacoes for r in l["rotas"]})
        funcoes_usadas = sorted({f for l in ligacoes for f in l["funcoes"]})
        if c["fecha"]:
            acao = "fecha a janela %s" % c["fecha"]
        elif c["aba_alvo"]:
            acao = "abre a aba %s" % c["aba_alvo"]
            rotas = abas_especiais.get(c["aba_alvo"], [])
        elif ligacoes:
            acao = ", ".join(sorted({l["evento"] for l in ligacoes}))
        elif c["id"] in indiretas:
            acao = indiretas[c["id"]]["como"]
            rotas, funcoes_usadas = indiretas[c["id"]]["rotas"], indiretas[c["id"]]["funcoes"]
        elif c.get("atributos_data") and any("[%s]" % a in indiretas for a in c["atributos_data"]):
            acao = "; ".join(indiretas["[%s]" % a]["como"] for a in c["atributos_data"] if "[%s]" % a in indiretas)
        elif c["tag"] == "details":
            acao = "abre e fecha (sem rota)"
        else:
            acao = ""
        controles.append(dict(c, acao=acao, rotas=rotas, funcoes=funcoes_usadas))
    ids_da_tela = {c["id"] for c in leitor.controles if c["id"]}
    ids_do_html = set(re.findall(r'\bid="([\w-]+)"', html_texto))
    rotas_da_tela = sorted(set(RE_ROTA_JS.findall(js)))
    return {
        "janelas": leitor.janelas,
        "controles": controles,
        "botoes_criados_pelo_js": botoes_criados_pelo_js(js, info),
        "sem_acao": [c["id"] or c["texto"] for c in controles
                     if not c["acao"] and c["tag"] == "button"],
        "acao_sem_elemento": sorted(i for i in por_id if i not in ids_do_html),
        "rotas_que_a_tela_pede": rotas_da_tela,
        "rotas_pedidas_que_nao_existem": [r for r in rotas_da_tela if r not in rotas_do_servidor],
        "controles_com_id": len(ids_da_tela),
    }


def temporizadores_da_tela():
    saida = []
    for n in sorted(os.listdir(os.path.join(RAIZ, "launcher"))):
        if not n.endswith(".js"):
            continue
        texto = ler(os.path.join("launcher", n))
        funcoes = funcoes_js(texto)
        for m in re.finditer(r"\b(setInterval|setTimeout|requestAnimationFrame)\s*\(", texto):
            fim = fim_do_parenteses(texto, m.end())
            argumentos = texto[m.end():fim - 1]
            espera = ""
            if m.group(1) != "requestAnimationFrame":
                # O ultimo argumento de primeiro nivel e' a espera.
                nivel, ultimo = 0, 0
                for i, c in enumerate(argumentos):
                    if c in "([{":
                        nivel += 1
                    elif c in ")]}":
                        nivel -= 1
                    elif c == "," and nivel == 0:
                        ultimo = i + 1
                espera = argumentos[ultimo:].strip()[:40] if ultimo else ""
            saida.append({"arquivo": n, "linha": linha_de(texto, m.start()), "tipo": m.group(1),
                          "espera": espera, "funcao": funcao_em(funcoes, m.start())})
    return saida


# --------------------------------------------------------------------------
# Servidor: rotas, configuracao, linhas de execucao, internet
# --------------------------------------------------------------------------

def rotas():
    arena = ler(os.path.join("servidor", "arena.py"))
    inicio_get = arena.find("def api_get(")
    inicio_post = arena.find("def api_post(")
    achadas = []
    for m in re.finditer(r'caminho == "(/api/[a-z0-9/_-]+)"', arena):
        pos = m.start()
        if pos > inicio_post:
            metodo = "POST"
        elif pos > inicio_get:
            metodo = "GET"
        else:
            continue
        achadas.append((m.group(1), metodo))
    # Tambem o formato 'caminho in ("/api/a", "/api/b")' (ex.: /api/ranking)
    for m in re.finditer(r'caminho in \(([^)]*)\)', arena):
        if m.start() < inicio_get:
            continue
        metodo = "POST" if m.start() > inicio_post else "GET"
        for rota in re.findall(r'"(/api/[a-z0-9/_-]+)"', m.group(1)):
            achadas.append((rota, metodo))
    externas = set(re.findall(r'"(/api/[a-z0-9/_-]+)",\s*#', arena[arena.find("ROTAS_REDE_EXTERNA"):
                                                               arena.find("ROTAS_REDE_EXTERNA") + 1500]))
    tela_js = ler(os.path.join("launcher", "app.js"))
    funcoes = funcoes_js(tela_js)
    partida = ler(os.path.join("servidor", "partida.py"))
    fontes_py = {rel: t for rel, t in fontes_do_servidor().items() if rel.endswith(".py")}
    saida = []
    vistas = set()
    for rota, metodo in achadas:
        if (rota, metodo) in vistas:
            continue
        vistas.add((rota, metodo))
        base = rota.rstrip("*")
        chamadores, funcoes_da_tela = [], set()
        for m in re.finditer(r'["`\']' + re.escape(base) + r'(?![a-z0-9/_-])', tela_js):
            funcoes_da_tela.add(funcao_em(funcoes, m.start()))
        if funcoes_da_tela:
            chamadores.append("tela")
        # Endereco montado pelo servidor e usado pela tela (ex.: as capas do
        # catalogo vem como "/api/capa?arquivo=...").
        elif any(re.search(r'["\']%s\?' % re.escape(base), linha) and "caminho" not in linha
                 for texto in fontes_py.values() for linha in texto.splitlines()):
            chamadores.append("tela (endereco que vem do servidor)")
        if base in partida:
            chamadores.append("PARTIDA.bat")
        if re.search(r'falar_com\([^)]*"' + re.escape(base), arena) or base in ("/api/sinc/receber", "/api/sinc/ola"):
            chamadores.append("outro ARENA")
        saida.append({"rota": rota, "metodo": metodo, "chamada_por": chamadores or ["ninguem achado"],
                      "funcoes_da_tela": sorted(funcoes_da_tela), "aberta_a_rede": base in externas})
    return sorted(saida, key=lambda r: (r["rota"], r["metodo"]))


def fontes_do_servidor():
    fontes = {os.path.join("servidor", n): ler(os.path.join("servidor", n))
              for n in os.listdir(os.path.join(RAIZ, "servidor")) if n.endswith(".py")}
    fontes[os.path.join("launcher", "app.js")] = ler(os.path.join("launcher", "app.js"))
    return fontes


def chaves_do_bloco(arena, comeco, indentacao):
    ini = arena.find(comeco)
    fim = arena.find("\n}", ini) if comeco.startswith("AVANCADO") else arena.find("\ndef ", ini + 10)
    return sorted(set(re.findall(r'^\s{%d}"([a-z_0-9]+)":' % indentacao, arena[ini:fim], re.M)))


def chaves_de_config():
    arena = ler(os.path.join("servidor", "arena.py"))
    fontes = fontes_do_servidor()
    # As opcoes avancadas viram, TODAS de uma vez, opcoes do RetroArch
    # (opcoes.update(config.get("avancado", {}))): a chave nao aparece pelo
    # nome, mas e' lida.
    em_bloco = re.search(r'\.update\(\s*config\.get\(\s*"avancado"', arena)
    lida_em_bloco = ("servidor\\arena.py:%d (todas de uma vez: viram opcoes do RetroArch)"
                     % linha_de(arena, em_bloco.start())) if em_bloco else None
    saida = {}
    for grupo, chaves in (("config", chaves_do_bloco(arena, "def config_padrao(", 8)),
                          ("avancado", chaves_do_bloco(arena, "AVANCADO_PADRAO = {", 4))):
        for chave in chaves:
            onde = [rel for rel, texto in fontes.items()
                    if texto.count('"%s"' % chave) + texto.count(".%s" % chave) + texto.count("'%s'" % chave)
                    > (1 if rel.endswith("arena.py") else 0)]
            if grupo == "avancado" and lida_em_bloco:
                onde.append(lida_em_bloco)
            saida["%s.%s" % (grupo, chave) if grupo == "avancado" else chave] = onde
    return saida


def arquivos_de_dados():
    """Arquivos de dados\\ que o servidor le ou grava, e quem."""
    saida = {}
    for rel, texto in fontes_do_servidor().items():
        if not rel.endswith(".py"):
            continue
        for nome in re.findall(r'(?:DADOS|PASTA_DADOS|"dados")\s*,\s*"([^"]+\.(?:json|txt|db|log))"', texto):
            saida.setdefault(nome, set()).add(rel)
    return {k: sorted(v) for k, v in sorted(saida.items())}


def corpo_da_funcao(fontes, nome):
    """O texto de 'def nome(' em qualquer modulo do servidor."""
    for rel, texto in fontes.items():
        m = re.search(r"^(\s*)def %s\(" % re.escape(nome.split(".")[-1]), texto, re.M)
        if m:
            recuo = len(m.group(1))
            resto = texto[m.end():]
            fim = re.search(r"^\s{0,%d}(def |class )" % recuo, resto, re.M)
            return rel, resto[:fim.start()] if fim else resto
    return None, ""


def comentario_acima(texto, posicao):
    """As linhas de comentario logo acima de 'posicao' (o motivo)."""
    linhas = texto[:posicao].splitlines()
    if linhas and not linhas[-1].strip().startswith("#"):
        linhas = linhas[:-1]     # a propria linha do threading.Thread(...)
    pedaco = []
    for linha in reversed(linhas):
        limpa = linha.strip()
        if limpa.startswith("#"):
            pedaco.append(limpa.lstrip("# "))
        else:
            break
    return " ".join(reversed(pedaco))[:300]


def linhas_de_execucao():
    fontes = {rel: t for rel, t in fontes_do_servidor().items() if rel.endswith(".py")}
    saida = []
    for rel, texto in sorted(fontes.items()):
        for m in re.finditer(r"threading\.(Thread|Timer)\(", texto):
            fim = fim_do_parenteses(texto, m.end())
            argumentos = texto[m.end():fim - 1]
            alvo = re.search(r"target=([\w.]+)", argumentos) or re.search(r"lambda[^:]*:\s*([\w.]+)", argumentos)
            if not alvo and m.group(1) == "Timer":
                alvo = re.search(r"^\s*[\w.]+\s*,\s*([\w.]+)", argumentos)
            nome_alvo = alvo.group(1) if alvo else argumentos[:60]
            _onde, corpo = corpo_da_funcao(fontes, nome_alvo)
            esperas = sorted(set(re.findall(r"(?:time\.sleep|\.wait)\(([^()]*(?:\([^()]*\))?[^()]*)\)", corpo)))
            # A funcao de primeiro nivel (ou o metodo da classe) onde a linha nasce;
            # uma funcao de dentro (def perguntar() la dentro) nao conta.
            funcoes, em_classe = [], False
            for mm in re.finditer(r"^(class |def |    def )(\w+)", texto, re.M):
                if mm.group(1) != "    def ":
                    em_classe = mm.group(1) == "class "
                if mm.group(1) == "def " or (mm.group(1) == "    def " and em_classe):
                    funcoes.append((mm.start(), mm.group(2)))
            dentro = [nome for pos, nome in funcoes if pos < m.start()]
            saida.append({"arquivo": rel, "linha": linha_de(texto, m.start()), "tipo": m.group(1),
                          "alvo": nome_alvo, "nasce_em": dentro[-1] if dentro else "(modulo)",
                          "em_laco": bool(re.search(r"^\s*while\b", corpo, re.M)),
                          "esperas": esperas[:6], "daemon": "daemon=True" in argumentos,
                          "motivo_no_codigo": comentario_acima(texto, m.start())})
    return saida


def internet():
    saida = []
    for pasta in ("servidor", "launcher"):
        for n in os.listdir(os.path.join(RAIZ, pasta)):
            if not n.endswith((".py", ".js", ".html", ".json")):
                continue
            texto = ler(os.path.join(pasta, n))
            hosts = sorted(set(h for h in re.findall(r"https?://([a-z0-9.-]+\.[a-z]{2,})", texto)
                               if not h.startswith(("127.", "localhost"))))
            if hosts:
                saida.append({"arquivo": os.path.join(pasta, n), "enderecos": hosts})
    return saida


def celula(texto):
    return str(texto).replace("|", "/").replace("\n", " ").strip() or "—"


def em_markdown(dados):
    """O mesmo inventario, para ler: uma tabela por assunto."""
    t = dados["tela"]
    linhas = ["# Inventário do ARENA", "",
              "Gerado por `testes\\inventario.py --md=...` direto do código (não editar à mão).", "",
              "## Rotas do servidor", "",
              "| Rota | Método | Aberta à rede | Quem chama | Funções da tela |", "|---|---|---|---|---|"]
    for r in dados["rotas"]:
        linhas.append("| `%s` | %s | %s | %s | %s |" % (r["rota"], r["metodo"], "sim" if r["aberta_a_rede"] else "não",
                                                     celula(", ".join(r["chamada_por"])),
                                                     celula(", ".join(r["funcoes_da_tela"]))))
    linhas += ["", "## A tela", ""]
    por_janela = {}
    for c in t["controles"]:
        por_janela.setdefault(c["janela"], []).append(c)
    for janela, controles in por_janela.items():
        titulo = t["janelas"].get(janela, {}).get("titulo", "") if janela != "(tela principal)" else ""
        linhas += ["### %s%s" % (janela, " — " + titulo if titulo else ""), "",
                   "| Controle | Texto | Aba | O que faz | Rotas |", "|---|---|---|---|---|"]
        for c in controles:
            nome = "%s `%s`" % (c["tag"], c["id"]) if c["id"] else c["tag"]
            linhas.append("| %s | %s | %s | %s | %s |" % (nome, celula(c["texto"] or c["rotulo"]), celula(c["aba"]),
                                                       celula(c["acao"]), celula(", ".join(c["rotas"]))))
        linhas.append("")
    linhas += ["### Botões que o app.js cria sozinho", "", "| Função | Texto | Rotas do clique |", "|---|---|---|"]
    for b in t["botoes_criados_pelo_js"]:
        rotas = sorted({r for a in b["acoes"] for r in a["rotas"]})
        linhas.append("| `%s` | %s | %s |" % (b["funcao"], celula(" / ".join(b["texto"])), celula(", ".join(rotas))))
    linhas += ["", "## Temporizadores da tela", "", "| Arquivo:linha | Tipo | Espera | Função |", "|---|---|---|---|"]
    for x in dados["temporizadores_da_tela"]:
        linhas.append("| %s:%d | %s | %s | %s |" % (x["arquivo"], x["linha"], x["tipo"], celula(x["espera"]),
                                                    celula(x["funcao"])))
    linhas += ["", "## Linhas de execução do servidor", "",
               "| Arquivo:linha | Função | Nasce em | Em laço | Esperas |", "|---|---|---|---|---|"]
    for x in dados["linhas_de_execucao"]:
        linhas.append("| %s:%d | `%s` | `%s` | %s | %s |" % (x["arquivo"], x["linha"], x["alvo"], x["nasce_em"],
                                                          "sim" if x["em_laco"] else "não",
                                                          celula(", ".join(e for e in x["esperas"] if e))))
    linhas += ["", "## Chaves de configuração e onde são lidas", "", "| Chave | Lida em |", "|---|---|"]
    for chave, onde in dados["chaves_de_config"].items():
        linhas.append("| `%s` | %s |" % (chave, celula(", ".join(onde))))
    linhas += ["", "## Internet (endereços fixos no código)", "", "| Arquivo | Endereços |", "|---|---|"]
    for x in dados["internet"]:
        linhas.append("| %s | %s |" % (x["arquivo"], ", ".join(x["enderecos"])))
    linhas += ["", "## Pastas", "", "| Pasta | Arquivos | MB |", "|---|---|---|"]
    for pasta, info in dados["pastas"].items():
        linhas.append("| %s | %d | %.1f |" % (pasta, info["arquivos"], info["mb"]))
    linhas += ["", "## Arquivos do ARENA (%d)" % len(dados["arquivos_do_arena"]), "",
               "| Arquivo | KB | Linhas |", "|---|---|---|"]
    for a in dados["arquivos_do_arena"]:
        linhas.append("| %s | %.1f | %s |" % (a["arquivo"], a["kb"], "" if a["linhas"] is None else a["linhas"]))
    return "\n".join(linhas) + "\n"


def principal():
    destino = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--saida=")),
                   os.path.join(RAIZ, "docs", "inventario_bruto.json"))
    if not os.path.isabs(destino):
        destino = os.path.join(RAIZ, destino)
    todos = arquivos_do_arena()
    lista_de_rotas = rotas()
    dados = {
        "pastas": arquivos_por_pasta(),
        "pastas_de_fora": pastas_de_fora(),
        "arquivos_do_arena": todos,
        "linhas_do_produto": linhas_do_produto(todos),
        "rotas": lista_de_rotas,
        "tela": tela({r["rota"] for r in lista_de_rotas}),
        "temporizadores_da_tela": temporizadores_da_tela(),
        "chaves_de_config": chaves_de_config(),
        "arquivos_de_dados": arquivos_de_dados(),
        "linhas_de_execucao": linhas_de_execucao(),
        "internet": internet(),
    }
    t = dados["tela"]
    dados["resumo"] = {
        "arquivos_do_arena": len(todos),
        "linhas_do_produto": sum(dados["linhas_do_produto"].values()),
        "arquivos_do_produto": len(dados["linhas_do_produto"]),
        "rotas": len(dados["rotas"]),
        "rotas_abertas_a_rede": sum(r["aberta_a_rede"] for r in dados["rotas"]),
        "rotas_sem_chamador": [r["rota"] + " " + r["metodo"] for r in dados["rotas"]
                               if r["chamada_por"] == ["ninguem achado"]],
        "janelas_da_tela": len(t["janelas"]),
        "controles_da_tela": len(t["controles"]),
        "botoes_criados_pelo_js": len(t["botoes_criados_pelo_js"]),
        "botoes_sem_acao": t["sem_acao"],
        "acao_para_elemento_que_nao_existe": t["acao_sem_elemento"],
        "rotas_pedidas_que_nao_existem": t["rotas_pedidas_que_nao_existem"],
        "temporizadores_da_tela": len(dados["temporizadores_da_tela"]),
        "chaves_de_config": len(dados["chaves_de_config"]),
        "chaves_nao_lidas": [c for c, onde in dados["chaves_de_config"].items() if not onde],
        "linhas_de_execucao": len(dados["linhas_de_execucao"]),
    }
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(destino, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    print(json.dumps(dados["resumo"], ensure_ascii=False, indent=2))
    print("Inventario salvo em", destino)
    legivel = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--md=")), "")
    if legivel:
        if not os.path.isabs(legivel):
            legivel = os.path.join(RAIZ, legivel)
        with open(legivel, "w", encoding="utf-8") as f:
            f.write(em_markdown(dados))
        print("Para ler:", legivel)


if __name__ == "__main__":
    principal()
