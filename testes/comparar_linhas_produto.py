r"""Fase 8 da auditoria: compara linhas de codigo DO PRODUTO entre dois commits.

"Produto" = o que vai para o aluno: servidor\ (sem tests\ e sem o Python
embutido), launcher\ e os .bat/.md da raiz. Ficam de fora testes\, docs\ e
ferramentas\ -- a auditoria criou muitos scripts de teste e resultados brutos,
e conta-los como "codigo do ARENA" faria o produto parecer mais pesado do que
ficou.

Uso:
    servidor\python\python.exe testes\comparar_linhas_produto.py main auditoria
"""
import subprocess
import sys

EXTENSOES = (".py", ".js", ".html", ".css", ".json", ".bat", ".md")


def e_do_produto(caminho):
    if not caminho.endswith(EXTENSOES):
        return False
    partes = caminho.split("/")
    if partes[0] in ("testes", "docs", "ferramentas", "dados", "jogos",
                     "retroarch", "emuladores", "backup"):
        return False
    if partes[0] == "servidor" and len(partes) > 1 and partes[1] in ("tests", "python"):
        return False
    return True


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, check=True).stdout


def linhas_no_commit(commit):
    arquivos = git("ls-tree", "-r", "--name-only", commit).decode("utf-8").splitlines()
    resultado = {}
    for caminho in arquivos:
        if e_do_produto(caminho):
            conteudo = git("show", f"{commit}:{caminho}")
            resultado[caminho] = conteudo.count(b"\n")
    return resultado


def principal():
    antes_c, depois_c = sys.argv[1], sys.argv[2]
    antes, depois = linhas_no_commit(antes_c), linhas_no_commit(depois_c)
    por_ext = {}
    for nome, tabela in (("antes", antes), ("depois", depois)):
        for caminho, n in tabela.items():
            ext = "." + caminho.rsplit(".", 1)[1]
            por_ext.setdefault(ext, {"antes": 0, "depois": 0})[nome] += n
    print(f"{'extensao':10} {'antes':>8} {'depois':>8} {'diferenca':>10}")
    for ext in sorted(por_ext):
        a, d = por_ext[ext]["antes"], por_ext[ext]["depois"]
        print(f"{ext:10} {a:8} {d:8} {d - a:+10}")
    ta, td = sum(antes.values()), sum(depois.values())
    print(f"{'TOTAL':10} {ta:8} {td:8} {td - ta:+10}")
    print(f"arquivos: {len(antes)} -> {len(depois)}")
    print("\nArquivos que sairam:", sorted(set(antes) - set(depois)))
    print("Arquivos que entraram:", sorted(set(depois) - set(antes)))
    print("\nMaiores mudancas:")
    difs = sorted(((depois.get(c, 0) - antes.get(c, 0), c) for c in set(antes) | set(depois)),
                  key=lambda x: -abs(x[0]))
    for d, c in difs[:12]:
        print(f"  {d:+6}  {c}")


if __name__ == "__main__":
    principal()
