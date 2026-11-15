# -*- coding: utf-8 -*-
r"""Monta o RASCUNHO da nota da proxima versao do ARENA, em portugues, a partir dos commits desde a ultima etiqueta.

Por que existe (14/11/2026): os blueprints de docs\arena-blueprints\ traziam a ideia de um release.yml (GitHub Actions
que publica a versao), um labeler.yml (etiqueta cada mudanca pela pasta que ela mexeu) e um publish_release.sh. Aqui
fica so a parte util e segura dessa ideia: LER o historico do git e escrever um rascunho que o Rafael revisa.

O que ele faz:
  1. acha a ultima etiqueta (git describe --tags --abbrev=0; as do ARENA sao como v2026.11.14 e v2026.11.13.2);
  2. le os commits dali ate o HEAD (git log --name-only), com a lista de arquivos de cada um;
  3. separa cada commit pela AREA dos arquivos que ele mudou (Servidor, Nativo, Tela, Android, Linux...). Um commit
     que mexe em varias areas entra na principal (a que tem mais arquivos) e cita as outras entre parenteses;
  4. escreve o rascunho em Markdown, com a etiqueta de partida, quantos commits e as datas no topo.

O que ele NUNCA faz: criar etiqueta, enviar (push), publicar no GitHub (gh release) ou juntar arquivo (git add).
So le o git. Publicar continua sendo pelo SINCRONIZAR.bat, que confere o que vai junto.

Uso:
    servidor\python\python.exe ferramentas\rascunho_da_release.py
    servidor\python\python.exe ferramentas\rascunho_da_release.py --saida docs\rascunho.md
    servidor\python\python.exe ferramentas\rascunho_da_release.py --desde v2026.11.13 --ate HEAD
"""
import argparse
import os
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# As areas na ordem em que aparecem na nota. Em caso de empate (mesmo numero de arquivos), vale a que vem antes.
AREAS = [
    "Servidor",
    "Servidor nativo em Rust",
    "Tela",
    "Android",
    "Linux",
    "Windows",
    "Ferramentas",
    "Testes",
    "Documentação",
    "Outros",
]

# Separadores que nunca aparecem num titulo de commit: um antes de cada commit e um entre os campos.
INICIO = "\x1e"
CAMPO = "\x1f"


class ErroDoGit(Exception):
    """O git nao esta instalado, a pasta nao e' um repositorio ou o comando falhou. A mensagem diz o que fazer."""


def area_do_arquivo(caminho):
    """Diz a area de um arquivo pelo caminho (relativo a raiz do repositorio, com barras /)."""
    caminho = caminho.replace("\\", "/")
    primeira = caminho.split("/", 1)[0]
    na_raiz = "/" not in caminho
    if caminho.startswith("servidor/tests/") or primeira == "testes":
        return "Testes"
    if primeira == "servidor":
        return "Servidor"
    if primeira == "nativo":
        return "Servidor nativo em Rust"
    if primeira == "launcher":
        return "Tela"
    if primeira == "android":
        return "Android"
    if primeira == "ferramentas":
        return "Ferramentas"
    if primeira == "docs":
        return "Documentação"
    if na_raiz:
        minusculo = caminho.lower()
        if minusculo.endswith(".md"):
            return "Documentação"
        if minusculo.endswith((".sh", ".desktop")):
            return "Linux"           # ARENA.sh, PARTIDA.sh, VERIFICAR.sh, ARENA.desktop...
        if minusculo.endswith((".bat", ".ps1")):
            return "Windows"         # ARENA.bat, SINCRONIZAR.bat, INICIAR-ARENA.ps1...
    return "Outros"


def areas_do_commit(arquivos):
    """Devolve (principal, [outras]) para a lista de arquivos de um commit.

    A principal e' a area com mais arquivos; no empate, a que vem antes em AREAS. Commit sem arquivo (vazio) vai
    para "Outros"."""
    contagem = {}
    for arquivo in arquivos:
        area = area_do_arquivo(arquivo)
        contagem[area] = contagem.get(area, 0) + 1
    if not contagem:
        return "Outros", []
    ordenadas = sorted(contagem, key=lambda area: (-contagem[area], AREAS.index(area)))
    outras = sorted(ordenadas[1:], key=AREAS.index)
    return ordenadas[0], outras


def git(pasta, *argumentos, tempo=60):
    """Roda um comando do git (so leitura) na pasta e devolve o texto. Lista de argumentos, sem shell."""
    try:
        r = subprocess.run(["git", "-c", "core.quotepath=off", *argumentos], cwd=pasta, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=tempo)
    except FileNotFoundError:
        raise ErroDoGit("O git nao esta instalado neste computador. Instale o Git para Windows (git-scm.com, "
                        "gratuito) e rode de novo.")
    except subprocess.TimeoutExpired:
        raise ErroDoGit("O git demorou mais de %d s para responder. Feche outros programas que usam o git e "
                        "tente de novo." % tempo)
    if r.returncode != 0:
        raise ErroDoGit((r.stderr or r.stdout).strip() or "o git terminou com erro %d" % r.returncode)
    return r.stdout


def conferir_repositorio(pasta):
    """Confere que a pasta e' um repositorio git. Sem git ou fora de um, explica o que fazer."""
    try:
        git(pasta, "rev-parse", "--is-inside-work-tree")
    except ErroDoGit as erro:
        if "not a git repository" in str(erro).lower():
            raise ErroDoGit("A pasta %s nao e' um repositorio git. Rode este script de dentro da pasta do ARENA "
                            "baixada pelo git (git clone), nao de uma copia solta." % pasta)
        raise


def ultima_etiqueta(pasta, ate="HEAD"):
    """A ultima etiqueta alcancavel a partir de `ate`, ou None se o repositorio nao tem nenhuma."""
    try:
        return git(pasta, "describe", "--tags", "--abbrev=0", ate).strip() or None
    except ErroDoGit as erro:
        texto = str(erro).lower()
        if "no names found" in texto or "no tags" in texto or "cannot describe" in texto:
            return None
        raise


def conferir_ref(pasta, ref, papel):
    """Confere que a etiqueta/ref existe, para o erro sair claro em vez do texto cru do git."""
    try:
        git(pasta, "rev-parse", "--verify", "--quiet", ref + "^{commit}")
    except ErroDoGit:
        raise ErroDoGit("Nao achei %s '%s' neste repositorio. Confira o nome com: git tag  (ou git log --oneline)."
                        % (papel, ref))


def ler_commits(pasta, desde, ate):
    """Le os commits de `desde` (exclusive) ate `ate`. Sem `desde`, le o historico inteiro ate `ate`.

    Devolve uma lista de dicionarios {hash, data, titulo, arquivos}, do mais novo para o mais velho. Os commits de
    junção (merge) ficam de fora: eles so juntam o que os outros commits ja contam."""
    intervalo = "%s..%s" % (desde, ate) if desde else ate
    # %s e' so o titulo (a primeira linha): as linhas Co-Authored-By e Claude-Session ficam no corpo e nao entram.
    formato = "--format=" + INICIO + "%h" + CAMPO + "%ad" + CAMPO + "%s"
    saida = git(pasta, "log", "--no-merges", "--date=short", "--name-only", formato, intervalo)
    commits = []
    for bloco in saida.split(INICIO):
        if not bloco.strip():
            continue
        linhas = bloco.split("\n")
        partes = linhas[0].split(CAMPO)
        if len(partes) < 3:
            continue
        arquivos = [linha.strip() for linha in linhas[1:] if linha.strip()]
        commits.append({"hash": partes[0], "data": partes[1], "titulo": partes[2].strip(), "arquivos": arquivos})
    return commits


def montar_rascunho(commits, desde, ate, sem_etiqueta=False):
    """Escreve o rascunho em Markdown (texto). Nao le nada do git: recebe os commits ja lidos."""
    linhas = ["# Rascunho da próxima versão do ARENA", ""]
    if sem_etiqueta:
        linhas.append("> Aviso: este repositório não tem nenhuma etiqueta de versão, então o rascunho usa o "
                      "histórico inteiro.")
        linhas.append("")
    linhas.append("- Etiqueta de partida: %s" % (("`%s`" % desde) if desde else "nenhuma (histórico inteiro)"))
    linhas.append("- Até: `%s`" % ate)
    linhas.append("- Commits: %d" % len(commits))
    if commits:
        datas = sorted(c["data"] for c in commits)
        if datas[0] == datas[-1]:
            linhas.append("- Datas: %s" % datas[0])
        else:
            linhas.append("- Datas: de %s a %s" % (datas[0], datas[-1]))
    linhas.append("")
    if not commits:
        linhas.append("Nenhum commit novo desde a etiqueta de partida.")
        return "\n".join(linhas) + "\n"
    linhas.append("Rascunho para revisar antes de publicar: nada foi etiquetado nem enviado.")
    linhas.append("")
    grupos = {area: [] for area in AREAS}
    for commit in commits:
        principal, outras = areas_do_commit(commit["arquivos"])
        grupos[principal].append((commit, outras))
    for area in AREAS:
        if not grupos[area]:
            continue
        linhas.append("## %s (%d)" % (area, len(grupos[area])))
        linhas.append("")
        for commit, outras in grupos[area]:
            texto = "- %s" % commit["titulo"]
            if outras:
                texto += " (também: %s)" % ", ".join(outras)
            texto += " `%s`" % commit["hash"]
            linhas.append(texto)
        linhas.append("")
    return "\n".join(linhas)


def gerar(pasta, desde=None, ate="HEAD"):
    """Faz o trabalho todo e devolve (texto, aviso). `aviso` diz quando nao havia etiqueta nenhuma."""
    conferir_repositorio(pasta)
    conferir_ref(pasta, ate, "a referencia")
    aviso = None
    if desde:
        conferir_ref(pasta, desde, "a etiqueta")
    else:
        desde = ultima_etiqueta(pasta, ate)
        if desde is None:
            aviso = "Aviso: nenhuma etiqueta de versao no repositorio; usei o historico inteiro."
    commits = ler_commits(pasta, desde, ate)
    return montar_rascunho(commits, desde, ate, sem_etiqueta=aviso is not None), aviso


def main(argumentos=None):
    leitor = argparse.ArgumentParser(description="Rascunho da nota da proxima versao do ARENA (so le o git).")
    leitor.add_argument("--desde", help="etiqueta de partida (padrao: a ultima etiqueta)")
    leitor.add_argument("--ate", default="HEAD", help="ate onde ler (padrao: HEAD)")
    leitor.add_argument("--saida", help="arquivo .md onde gravar (padrao: mostrar na tela)")
    leitor.add_argument("--pasta", default=RAIZ, help="repositorio a ler (padrao: a pasta do ARENA)")
    opcoes = leitor.parse_args(argumentos)
    try:
        texto, aviso = gerar(opcoes.pasta, opcoes.desde, opcoes.ate)
    except ErroDoGit as erro:
        print("Erro: %s" % erro, file=sys.stderr)
        return 1
    if aviso:
        print(aviso, file=sys.stderr)
    if opcoes.saida:
        # Grava num temporario e troca, para nao deixar um rascunho pela metade se algo cair no meio.
        temporario = opcoes.saida + ".tmp"
        try:
            with open(temporario, "w", encoding="utf-8", newline="\n") as arquivo:
                arquivo.write(texto)
            os.replace(temporario, opcoes.saida)
        except OSError as erro:
            print("Erro: nao consegui gravar %s (%s). Confira se a pasta existe e se o arquivo nao esta aberto "
                  "em outro programa." % (opcoes.saida, erro), file=sys.stderr)
            return 1
        print("Rascunho gravado em %s." % opcoes.saida)
    else:
        # O console do Windows nem sempre entende os acentos: forca UTF-8 na saida.
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
        sys.stdout.write(texto)
    return 0


if __name__ == "__main__":
    sys.exit(main())
