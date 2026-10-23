# -*- coding: utf-8 -*-
r"""Monta a versao do ARENA para a internet (GitHub Pages) -- auditoria 4.

Pedido do Rafael (22/10/2026): o APK nao instalou no celular de um aluno (a
verificacao de desenvolvedor do Google, no Brasil desde 30/09/2026, e/ou um
celular de 32 bits). A versao web roda no Chrome de qualquer Android, antigo
ou novo, sem instalar nada: a mesma tela do Windows, com o servidor dentro
da pagina (o modo do Chromebook, launcher\navegador) e o controle de toque
(launcher\navegador\toque.js). "Adicionar a tela inicial" deixa como app: o
manifesto e o service worker (ferramentas\site) guardam a tela no aparelho.

Uso:
    servidor\python\python.exe ferramentas\montar_site.py [pasta de saida]

A pasta de saida (padrao: %LOCALAPPDATA%\ARENA-site) pode ser o ramo
gh-pages aberto como worktree: a pasta .git dela fica intacta. Publicar:
docs\WEB.md.
"""
import hashlib
import json
import os
import re
import shutil
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
MODELOS = os.path.join(AQUI, "site")
LIMITE_DO_PAGES = 95 * 1024 * 1024      # o GitHub Pages recusa arquivo de 100 MB ou mais
FORA = ("__pycache__",)

INJETADO = """<meta name="theme-color" content="#12121a">
<link rel="manifest" href="../manifest.webmanifest">
<!-- A versao da internet (ferramentas\\montar_site.py): sempre o servidor
     dentro da pagina, e o service worker que a guarda no aparelho. -->
<script>
window.ARENA_SEMPRE_NAVEGADOR = true;
if ("serviceWorker" in navigator) {
  addEventListener("load", function () {
    navigator.serviceWorker.register("../sw.js", { scope: "../" }).catch(function () {});
  });
}
</script>
</head>"""


def versao():
    with open(os.path.join(RAIZ, "servidor", "arena.py"), encoding="utf-8") as arquivo:
        return re.search(r'^VERSAO = "([^"]+)"', arquivo.read(), re.M).group(1)


def esvaziar(pasta):
    """Apaga o que a montagem anterior deixou, menos o .git (o worktree)."""
    for nome in os.listdir(pasta):
        if nome == ".git":
            continue
        caminho = os.path.join(pasta, nome)
        if os.path.isdir(caminho) and not os.path.islink(caminho):
            shutil.rmtree(caminho)
        else:
            os.remove(caminho)


def montar(saida):
    os.makedirs(saida, exist_ok=True)
    esvaziar(saida)
    shutil.copytree(os.path.join(RAIZ, "launcher"), os.path.join(saida, "launcher"),
                    ignore=shutil.ignore_patterns(*FORA))
    for nome in ("index.html", "manifest.webmanifest", "icone-192.png", "icone-512.png"):
        shutil.copyfile(os.path.join(MODELOS, nome), os.path.join(saida, nome))
    with open(os.path.join(saida, ".nojekyll"), "w", encoding="utf-8"):
        pass

    tela = os.path.join(saida, "launcher", "index.html")
    with open(tela, encoding="utf-8") as arquivo:
        html = arquivo.read()
    if html.count("</head>") != 1:
        raise SystemExit("A launcher\\index.html mudou: nao achei um </head> so para pôr o manifesto.")
    with open(tela, "w", encoding="utf-8", newline="\n") as arquivo:
        arquivo.write(html.replace("</head>", INJETADO, 1))

    # O que o service worker guarda ja na instalacao: tudo, menos os nucleos
    # (92 MB; cada um fica guardado quando abre o primeiro jogo dele).
    # A "impressao digital" (sha256) do conteudo vai no nome da guarda: com o
    # mesmo numero de versao, qualquer arquivo mudado ja faz o celular buscar
    # a tela nova; e os nucleos tem guarda propria, que so troca quando um
    # nucleo muda (sem baixar 92 MB de novo a cada conserto da tela).
    basicos, total, maior = ["./"], 0, ("", 0)
    digital_tela, digital_nucleos = hashlib.sha256(), hashlib.sha256()
    for atual, pastas, arquivos in os.walk(saida):
        pastas.sort()
        if ".git" in os.path.relpath(atual, saida).split(os.sep):
            continue
        for nome in sorted(arquivos):
            caminho = os.path.join(atual, nome)
            relativo = os.path.relpath(caminho, saida).replace(os.sep, "/")
            tamanho = os.path.getsize(caminho)
            total += tamanho
            if tamanho > maior[1]:
                maior = (relativo, tamanho)
            if tamanho >= LIMITE_DO_PAGES:
                raise SystemExit("%s tem %d MB: o GitHub Pages nao aceita." % (relativo, tamanho // 1048576))
            nucleo = relativo.startswith("launcher/navegador/nucleos/")
            digital = digital_nucleos if nucleo else digital_tela
            digital.update(relativo.encode("utf-8") + b"\0")
            with open(caminho, "rb") as arquivo:
                digital.update(arquivo.read())
            if not nucleo and relativo != ".nojekyll":
                basicos.append(relativo)
    with open(os.path.join(MODELOS, "sw.js"), encoding="utf-8") as arquivo:
        servico = arquivo.read()
    servico = (servico.replace("__VERSAO__", versao() + "-" + digital_tela.hexdigest()[:10])
               .replace("__NUCLEOS__", digital_nucleos.hexdigest()[:10])
               .replace("__BASICOS__", json.dumps(sorted(basicos), indent=1)))
    with open(os.path.join(saida, "sw.js"), "w", encoding="utf-8", newline="\n") as arquivo:
        arquivo.write(servico)
    return {"saida": saida, "arquivos": len(basicos), "total_mb": round(total / 1048576.0, 1),
            "maior": maior[0], "maior_mb": round(maior[1] / 1048576.0, 1), "versao": versao()}


if __name__ == "__main__":
    destino = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "ARENA-site")
    resultado = montar(os.path.abspath(destino))
    print("Versao web do ARENA %(versao)s montada em %(saida)s" % resultado)
    print("  %(arquivos)d arquivos guardados na instalacao; %(total_mb)s MB no total;"
          " o maior: %(maior)s (%(maior_mb)s MB)" % resultado)
