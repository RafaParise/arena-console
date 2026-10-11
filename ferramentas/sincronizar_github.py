# -*- coding: utf-8 -*-
r"""Sincroniza esta pasta com o repositorio do ARENA no GitHub: puxa o que os
outros computadores (e assistentes) enviaram e envia o que foi feito aqui.

Por que existe: o Rafael trabalha no ARENA em mais de um computador, com mais
de um assistente (Claude Code, Hermes) e pela nuvem. O GitHub e' a copia
central: no comeco do trabalho, PUXAR; no fim, ENVIAR. Substitui os tres
scripts de 10/10/2026 (sync_github.py, sincronizador.py e
SINCRONIZAR_ARENA.bat), que tinham dois defeitos:
  - faziam "git add -A" e um commit "Backup automatico" com TUDO o que estava
    na pasta -- inclusive o trabalho que outro assistente ainda estava
    fazendo, misturado num commit que nao diz o que mudou;
  - dois deles procuravam a pasta "Criador De Apps Pedagogicos", sem o
    acento, e por isso nem achavam o projeto.

Regras desta ferramenta (as mesmas do AGENTS.md):
  - NUNCA junta sozinho o que nao tem commit. Commit e' de quem fez o
    trabalho, com uma mensagem que diga o que mudou. Se houver mudanca sem
    commit, ela so mostra a lista. Para mandar tudo mesmo assim, o professor
    pede com --tudo "mensagem" (a mensagem e' obrigatoria).
  - Antes de enviar, confere o que vai junto (ferramentas\
    conferir_antes_de_publicar.py): BIOS, jogo, banco, save, dado de aluno,
    e-mail institucional, senha ou token num commit = NADA e' enviado. O
    repositorio e' publico. (Em 11/10/2026 outro assistente tentou enviar a
    pasta dos alunos inteira, com BIOS e o banco dos recordes; so nao foi
    porque o GitHub recusou os arquivos grandes.)
  - Puxar so avanca a copia daqui (--ff-only). Se os dois lados mudaram, ela
    junta (merge); se os dois mudaram o MESMO trecho, desiste sem estragar
    nada (merge --abort) e explica.
  - O login no GitHub e' o do Git para Windows (Git Credential Manager): na
    primeira vez que enviar, o Windows abre a pagina do GitHub para entrar.
    Ninguem digita senha aqui, e nada de senha ou token fica na pasta.

Uso (ou dois cliques no SINCRONIZAR.bat, que faz "tudo"):
    servidor\python\python.exe ferramentas\sincronizar_github.py [estado|puxar|enviar|tudo]
    servidor\python\python.exe ferramentas\sincronizar_github.py enviar --tudo "o que mudou"
"""
import io
import os
import shutil
import subprocess
import sys
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import conferir_antes_de_publicar  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REMOTO = "origin"
ENDERECO = "https://github.com/RafaParise/arena-console.git"


def git(*argumentos, tempo=120):
    """Roda um comando do git nesta pasta. Devolve (codigo, texto)."""
    try:
        r = subprocess.run(["git", *argumentos], cwd=RAIZ, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=tempo)
    except subprocess.TimeoutExpired:
        return 1, "o git demorou demais (mais de %d s)" % tempo
    return r.returncode, (r.stdout + r.stderr).strip()


def mudancas_sem_commit():
    _, texto = git("status", "--porcelain")
    return [linha for linha in texto.splitlines() if linha.strip()]


def ramo_atual():
    codigo, texto = git("rev-parse", "--abbrev-ref", "HEAD")
    return texto if codigo == 0 else ""


def adiante_e_atras(ramo):
    """Quantos commits so daqui (adiante) e so do GitHub (atras)."""
    codigo, texto = git("rev-list", "--left-right", "--count", "HEAD...%s/%s" % (REMOTO, ramo))
    if codigo != 0:
        return None
    adiante, atras = texto.split()
    return int(adiante), int(atras)


def preparar():
    """Confere o que precisa existir. Devolve o ramo, ou None (ja explicou)."""
    if not shutil.which("git"):
        print("Falta o Git. Instale o Git para Windows (git-scm.com) neste computador;")
        print("ele traz o login do GitHub junto. Depois, rode de novo.")
        return None
    if git("rev-parse", "--is-inside-work-tree")[0] != 0:
        print("Esta pasta nao e' um repositorio do git. Baixe o ARENA com:")
        print("  git clone %s" % ENDERECO)
        return None
    if git("remote", "get-url", REMOTO)[0] != 0:
        print("Esta pasta nao sabe onde fica o GitHub (falta o '%s')." % REMOTO)
        print("  git remote add origin %s" % ENDERECO)
        return None
    ramo = ramo_atual()
    if not ramo or ramo == "HEAD":
        print("A pasta nao esta em nenhum ramo (HEAD solto). Nada foi feito.")
        return None
    return ramo


def estado(ramo):
    print("Ramo: %s" % ramo)
    mudancas = mudancas_sem_commit()
    print("Mudancas sem commit: %d" % len(mudancas))
    for linha in mudancas[:30]:
        print("   ", linha)
    if len(mudancas) > 30:
        print("    ... e mais %d" % (len(mudancas) - 30))
    contas = adiante_e_atras(ramo)
    if contas:
        print("Commits so daqui: %d | so do GitHub: %d (da ultima vez que puxou)" % contas)


def puxar(ramo):
    print("Puxando do GitHub...")
    codigo, texto = git("fetch", REMOTO, tempo=600)
    if codigo != 0:
        print("Nao deu para falar com o GitHub (sem internet, ou sem login).")
        print("  " + texto.splitlines()[-1] if texto else "")
        return False
    contas = adiante_e_atras(ramo)
    if contas is None:
        print("O ramo '%s' ainda nao existe no GitHub: nada para puxar." % ramo)
        return True
    adiante, atras = contas
    if atras == 0:
        print("Nada novo no GitHub.")
        return True
    if adiante == 0:
        codigo, texto = git("merge", "--ff-only", "%s/%s" % (REMOTO, ramo))
        if codigo != 0:
            print("Nao deu para avancar: uma mudanca sem commit daqui esta no caminho.")
            print(texto)
            return False
        print("Atualizado: %d commit(s) novo(s) do GitHub." % atras)
        return True
    # Os dois lados mudaram: junta. Se o mesmo trecho mudou dos dois lados,
    # desiste sem estragar nada.
    codigo, texto = git("merge", "--no-edit", "%s/%s" % (REMOTO, ramo))
    if codigo != 0:
        git("merge", "--abort")
        print("Os dois lados mudaram o MESMO trecho de algum arquivo. Nada foi mudado aqui.")
        print("Peca ao assistente (Claude ou Hermes) para juntar com cuidado: nunca")
        print("apagar o trabalho do outro para o seu passar.")
        return False
    print("Juntado: %d commit(s) do GitHub com %d daqui." % (atras, adiante))
    return True


def conferido_para_publicar(ramo):
    """A ultima porta antes do GitHub publico: confere cada arquivo novo dos
    commits que o GitHub ainda nao tem. Se houver bloqueante, explica e
    devolve False -- e nada e' enviado."""
    conferir_antes_de_publicar.RAIZ = RAIZ
    saida = io.StringIO()
    with redirect_stdout(saida):
        codigo = conferir_antes_de_publicar.principal([ramo])
    if codigo == 0:
        return True
    print(saida.getvalue())
    print("NADA FOI ENVIADO: algum commit leva um arquivo que nao pode ir para o GitHub")
    print("(o repositorio e' publico). Peca ao assistente para tirar esse arquivo do commit.")
    return False


def enviar(ramo, mensagem_para_tudo=None):
    mudancas = mudancas_sem_commit()
    if mudancas and mensagem_para_tudo:
        git("add", "-A")
        codigo, texto = git("commit", "-m", mensagem_para_tudo)
        if codigo != 0:
            print("O commit nao deu certo:")
            print(texto)
            return False
        print("Commit feito com %d arquivo(s): %s" % (len(mudancas), mensagem_para_tudo))
    elif mudancas:
        print("Ha %d mudanca(s) SEM commit. Elas NAO vao para o GitHub:" % len(mudancas))
        for linha in mudancas[:15]:
            print("   ", linha)
        print("O commit e' de quem fez o trabalho: peca ao assistente para fazer o commit")
        print('com uma mensagem que diga o que mudou, ou rode: SINCRONIZAR.bat enviar --tudo "o que mudou"')
    contas = adiante_e_atras(ramo)
    if contas is not None and contas[0] == 0:
        print("Nada daqui para enviar.")
        return True
    if not conferido_para_publicar(ramo):
        return False
    print("Enviando para o GitHub (na primeira vez, o Windows abre a pagina do GitHub para entrar)...")
    codigo, texto = git("push", "-u", REMOTO, ramo, tempo=900)
    if codigo != 0:
        if "rejected" in texto or "non-fast-forward" in texto or "fetch first" in texto:
            print("O GitHub tem coisa nova que esta copia nao tem. Puxe primeiro (SINCRONIZAR.bat).")
        else:
            print("Nao deu para enviar:")
            print(texto)
        return False
    print("Enviado.")
    return True


def main(argumentos):
    modo = argumentos[0].lower() if argumentos and not argumentos[0].startswith("--") else "tudo"
    mensagem = None
    if "--tudo" in argumentos:
        posicao = argumentos.index("--tudo")
        if posicao + 1 >= len(argumentos) or not argumentos[posicao + 1].strip():
            print('Faltou a mensagem: --tudo "o que mudou".')
            return 2
        mensagem = argumentos[posicao + 1].strip()
    if modo not in ("estado", "puxar", "enviar", "tudo"):
        print(__doc__)
        return 2
    ramo = preparar()
    if not ramo:
        return 1
    if modo == "estado":
        estado(ramo)
        return 0
    if modo == "puxar":
        return 0 if puxar(ramo) else 1
    if modo == "enviar":
        return 0 if enviar(ramo, mensagem) else 1
    certo = puxar(ramo)
    if certo:
        certo = enviar(ramo, mensagem)
    print()
    estado(ramo)
    return 0 if certo else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
