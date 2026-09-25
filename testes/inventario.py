# -*- coding: utf-8 -*-
r"""Auditoria 2, Fase 0: inventario do ARENA lido direto do codigo.

Nao sobe servidor nem mexe em nada: so le os arquivos. Gera
docs\inventario_bruto.json e imprime um resumo.

  - arquivos e tamanho por pasta de topo (sem jogos\, .git\, backup\);
  - linhas do produto por arquivo (servidor sem testes, tela, .bat, guias);
  - rotas da API (GET/POST), quem chama cada uma (tela, PARTIDA.bat,
    outro ARENA pela rede) e quais ficam abertas a rede;
  - chaves de configuracao (config_padrao) e em que arquivos sao lidas;
  - linhas de execucao e temporizadores que ficam rodando;
  - tudo que sai para a internet (enderecos fixos no codigo).

Uso:
    servidor\python\python.exe testes\inventario.py
"""
import json
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IGNORAR_TOPO = {"jogos", ".git", "backup"}
PRODUTO_EXT = (".py", ".js", ".html", ".css", ".json", ".bat", ".md")


def ler(rel):
    with open(os.path.join(RAIZ, rel), encoding="utf-8", errors="replace") as f:
        return f.read()


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


def e_do_produto(rel):
    partes = rel.replace("\\", "/").split("/")
    if not rel.endswith(PRODUTO_EXT):
        return False
    if partes[0] in ("testes", "docs", "ferramentas", "dados", "jogos", "retroarch",
                     "emuladores", "backup", "perfil", ".git"):
        return False
    if partes[0] == "servidor" and len(partes) > 1 and partes[1] in ("tests", "python", "__pycache__"):
        return False
    return True


def linhas_do_produto():
    saida = {}
    for atual, subs, arquivos in os.walk(RAIZ):
        rel_pasta = os.path.relpath(atual, RAIZ)
        if rel_pasta.split(os.sep)[0] in IGNORAR_TOPO | {"retroarch", "emuladores", "perfil"}:
            subs[:] = []
            continue
        for n in arquivos:
            rel = os.path.normpath(os.path.join(rel_pasta, n))
            if e_do_produto(rel):
                with open(os.path.join(RAIZ, rel), "rb") as f:
                    saida[rel] = f.read().count(b"\n")
    return dict(sorted(saida.items(), key=lambda kv: -kv[1]))


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
    tela = ler(os.path.join("launcher", "app.js"))
    partida = ler(os.path.join("servidor", "partida.py"))
    saida = []
    vistas = set()
    for rota, metodo in achadas:
        if (rota, metodo) in vistas:
            continue
        vistas.add((rota, metodo))
        base = rota.rstrip("*")
        chamadores = []
        if re.search(r'["`\']' + re.escape(base), tela):
            chamadores.append("tela")
        if base in partida:
            chamadores.append("PARTIDA.bat")
        if re.search(r'falar_com\([^)]*"' + re.escape(base), arena) or base in ("/api/sinc/receber", "/api/sinc/ola"):
            chamadores.append("outro ARENA")
        saida.append({"rota": rota, "metodo": metodo, "chamada_por": chamadores or ["ninguem achado"],
                      "aberta_a_rede": base in externas})
    return sorted(saida, key=lambda r: (r["rota"], r["metodo"]))


def chaves_de_config():
    arena = ler(os.path.join("servidor", "arena.py"))
    ini = arena.find("def config_padrao(")
    fim = arena.find("\ndef ", ini + 10)
    bloco = arena[ini:fim]
    chaves = sorted(set(re.findall(r'^\s{8}"([a-z_0-9]+)":', bloco, re.M)))
    fontes = {rel: ler(rel) for rel in (os.path.join("servidor", n) for n in os.listdir(os.path.join(RAIZ, "servidor"))
                                        if n.endswith(".py"))}
    fontes[os.path.join("launcher", "app.js")] = ler(os.path.join("launcher", "app.js"))
    saida = {}
    for chave in chaves:
        onde = [rel for rel, texto in fontes.items()
                if texto.count('"%s"' % chave) + texto.count(".%s" % chave) > (1 if rel.endswith("arena.py") else 0)]
        saida[chave] = onde
    return saida


def linhas_de_execucao():
    saida = []
    for n in os.listdir(os.path.join(RAIZ, "servidor")):
        if not n.endswith(".py"):
            continue
        texto = ler(os.path.join("servidor", n))
        for m in re.finditer(r"threading\.(Thread|Timer)\(([^)]*)\)", texto):
            alvo = re.search(r"target=([\w.]+)", m.group(2)) or re.search(r"lambda[^:]*:\s*([\w.]+)", m.group(2))
            linha = texto[:m.start()].count("\n") + 1
            saida.append({"arquivo": n, "linha": linha, "tipo": m.group(1),
                          "alvo": alvo.group(1) if alvo else m.group(2)[:60]})
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


def principal():
    dados = {
        "pastas": arquivos_por_pasta(),
        "linhas_do_produto": linhas_do_produto(),
        "rotas": rotas(),
        "chaves_de_config": chaves_de_config(),
        "linhas_de_execucao": linhas_de_execucao(),
        "internet": internet(),
    }
    dados["resumo"] = {
        "linhas_do_produto": sum(dados["linhas_do_produto"].values()),
        "arquivos_do_produto": len(dados["linhas_do_produto"]),
        "rotas": len(dados["rotas"]),
        "rotas_abertas_a_rede": sum(r["aberta_a_rede"] for r in dados["rotas"]),
        "rotas_sem_chamador": [r["rota"] + " " + r["metodo"] for r in dados["rotas"]
                               if r["chamada_por"] == ["ninguem achado"]],
        "chaves_de_config": len(dados["chaves_de_config"]),
        "chaves_nao_lidas": [c for c, onde in dados["chaves_de_config"].items() if not onde],
    }
    with open(os.path.join(RAIZ, "docs", "inventario_bruto.json"), "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    print(json.dumps(dados["resumo"], ensure_ascii=False, indent=2))
    print("linhas de execucao:", [(t["arquivo"], t["alvo"]) for t in dados["linhas_de_execucao"]])
    print("internet:", dados["internet"])


if __name__ == "__main__":
    principal()
