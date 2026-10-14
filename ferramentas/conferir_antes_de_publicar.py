# -*- coding: utf-8 -*-
r"""Confere, ANTES de enviar ao GitHub (que e' publico), tudo o que vai junto:
cada arquivo de cada commit do historico, nao so o que esta na pasta hoje.

Por que existe: o repositorio do ARENA e' publico. Um arquivo que entrou num
commit antigo e saiu depois continua no historico, e quem baixa o
repositorio leva junto. O ARENA e' usado por alunos menores de idade e roda
com BIOS e jogos que sao de empresas (Sony, Sega, SNK...): nada disso pode ir
para a internet. Em 10/10/2026 um "git pull" trocou o .gitignore do ARENA
pelo modelo generico do GitHub, e um script de sincronizacao faria
"git add -A" em seguida: a BIOS do PS2 e o banco dos recordes teriam ido
juntos. Esta ferramenta e' a ultima porta antes do envio.

O que ela procura (em todo commit que ainda nao esta no GitHub):
  1. caminho proibido: dados\ (fora o LEIA.txt), perfil\, BIOS\, backup\,
     o conteudo de jogos\, retroarch\ e emuladores\ (fora os LEIA.txt),
     banco de dados, save, memory card, conta do RPCN;
  2. extensao de jogo ou de BIOS (.iso, .bin, .rom, .sfc, .chd, .zip...);
  3. arquivo binario que nao seja imagem ou fonte DE VERDADE (conferida pelos
     primeiros bytes: uma BIOS renomeada para .png nao passa) e arquivo
     grande (mais de 1 MB, so aviso);
  4. no texto dos arquivos e nas mensagens dos commits: chave/token/senha,
     e-mail (o de aluno e o institucional sao bloqueantes), CPF, telefone,
     numero de RA, nome de computador e endereco de rede.

A unica excecao das regras 2 e 3: os arquivos LIVRES conferidos (as BIOS
livres do ARENA, em servidor\bios_livres, e os jogos livres dos testes, em
testes\jogos_livres). Passam so com o caminho E o conteudo (SHA-256) que a
lista.json da pasta deles registra; com um byte trocado, voltam a barrar.

Resultado: BLOQUEANTE (nao envie), AVISO (confira) ou nada. Sai com codigo 1
se houver bloqueante. Os achados vao so para a tela e para um arquivo na
pasta temporaria do Windows: nunca para dentro do repositorio (seriam
publicados junto).

Uso:
    servidor\python\python.exe ferramentas\conferir_antes_de_publicar.py [ramo ...]
    (sem ramo: main e o ramo atual; o que ja esta no origin fica de fora)
    --tudo     confere tambem o que ja esta no GitHub (para comparar)
"""
import collections
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Onde a lista completa dos achados fica (fora do repositorio). O teste troca.
DESTINO = os.path.join(tempfile.gettempdir(), "arena_conferir_antes_de_publicar.json")

# Caminhos que nunca podem estar no git. Os LEIA.txt das pastas vazias podem.
PERMITIDOS = re.compile(r"(^|/)LEIA\.txt$", re.I)
PROIBIDOS = [
    (re.compile(r"^dados/", re.I), "pasta dados\\ (dados de quem usa)"),
    (re.compile(r"^perfil/", re.I), "pasta perfil\\ (coletas do COLETAR, dados de maquina)"),
    (re.compile(r"^BIOS/", re.I), "pasta BIOS\\ (BIOS sao das empresas)"),
    (re.compile(r"^backup/", re.I), "pasta backup\\ (copias dos dados de quem usa)"),
    (re.compile(r"^jogos/", re.I), "pasta jogos\\"),
    (re.compile(r"^retroarch/", re.I), "pasta retroarch\\ (saves, BIOS, nucleos)"),
    (re.compile(r"^emuladores/", re.I), "pasta emuladores\\ (BIOS, firmware, contas)"),
    (re.compile(r"\.(db|sqlite3?|db-journal)$", re.I), "banco de dados"),
    (re.compile(r"(^|/)rpcn\.yml$", re.I), "conta do RPCN (PS3)"),
    (re.compile(r"\.(srm|sav|state\d*|mcd|mcr|mc[0-9]|ps2|brm|fs|eep|fla|sra|dsv)$", re.I),
     "save ou memory card"),
]
# Jogo e BIOS (sem .md, que aqui e' Markdown).
EXT_JOGO_OU_BIOS = re.compile(
    r"\.(iso|bin|img|rom|chd|cue|gdi|cdi|cso|pbp|rvz|wbfs|gcm|nkit|xex|xiso|pkg|"
    r"sfc|smc|nes|fds|gb|gbc|gba|nds|3ds|n64|z64|v64|gen|smd|sms|gg|32x|pce|sgx|"
    r"ws|wsc|ngp|ngc|a26|a52|a78|lnx|j64|col|int|vec|vb|min|tic|zip|7z|rar)$", re.I)
GRANDE = 1024 * 1024

# Conteudo. Cada regra: (nome, expressao, nivel).
SEGREDOS = [
    ("token do GitHub", re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})")),
    ("chave privada", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("chave da AWS", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("token do Slack", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}")),
    ("chave de API", re.compile(r"\bsk-(ant-)?[A-Za-z0-9_-]{24,}")),
    # Com cara de senha: tem algarismo, ou vem entre aspas. "a saida que nao pede
    # senha: outro computador abre" (texto do ARENA) nao conta.
    ("senha escrita", re.compile(r"(?i)\b(senha|password|passwd)\s*[:=]\s*"
                                 r"(['\"][^'\"\s]{4,}['\"]|(?=[^\s'\"<>{}]*\d)[^\s'\"<>{}]{6,})")),
]
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
# E-mails que podem aparecer: o da coautoria do Claude, os privados do
# GitHub e os de exemplo.
EMAIL_LIVRE = re.compile(r"(?i)^(noreply@anthropic\.com|noreply@github\.com|[^@]+@users\.noreply\.github\.com|"
                         r"[^@]+@(example\.(com|org|net)|exemplo\.com(\.br)?)|"
                         r"[^@]+@[^@]+\.(invalid|test|example|localhost))$")   # dominios reservados (RFC 2606)
EMAIL_ALUNO = re.compile(r"(?i)@al\.educacao\.sp\.gov\.br$")
EMAIL_INSTITUCIONAL = re.compile(r"(?i)@([a-z0-9-]+\.)*educacao\.sp\.gov\.br$")
PESSOAIS = [
    ("CPF", re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")),
    ("RA de aluno", re.compile(r"(?i)\bRA\s*[:=nº.]*\s*\d{6,}")),
    ("telefone", re.compile(r"\(\d{2}\)\s?9?\d{4}-\d{4}\b")),
]
NOME_DE_COMPUTADOR = re.compile(r"\b(DESKTOP|LAPTOP|NOTEBOOK)-[A-Z0-9]{5,}\b")
USUARIO_DO_WINDOWS = re.compile(r"(?i)[A-Z]:[\\/]{1,2}Users[\\/]{1,2}([^\\/\s\"'<>:]+)")
MAC = re.compile(r"\b([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b")
IPV4 = re.compile(r"\b(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\b")
# Pastas de usuario do Windows que nao identificam ninguem.
USUARIOS_GENERICOS = {"public", "default", "fulano", "aluno", "seunome", "voce", "usuario",
                      "<usuario>", "%username%", "nome", "%s", "...", "alguem"}


def git(*argumentos, entrada=None, binario=False):
    r = subprocess.run(["git", *argumentos], cwd=RAIZ, input=entrada, capture_output=True)
    if r.returncode != 0:
        raise SystemExit("git %s falhou: %s" % (" ".join(argumentos), r.stderr.decode("utf-8", "replace")[:400]))
    # O git fala UTF-8 (nome de arquivo com acento); o Windows, por padrao, nao.
    return r.stdout if binario else r.stdout.decode("utf-8", "replace")


# Binario que pode ir: imagem e fonte -- conferidos pelos primeiros bytes, para
# que uma BIOS renomeada para .png nao passe.
ASSINATURAS = {
    ".png": (b"\x89PNG\r\n\x1a\n",),
    ".jpg": (b"\xff\xd8\xff",), ".jpeg": (b"\xff\xd8\xff",),
    ".gif": (b"GIF87a", b"GIF89a"),
    ".ico": (b"\x00\x00\x01\x00",),
    ".webp": (b"RIFF",),
    ".woff": (b"wOFF",), ".woff2": (b"wOF2",),
    ".ttf": (b"\x00\x01\x00\x00", b"true"), ".otf": (b"OTTO",),
}


def binario_permitido(caminho, dados):
    extensao = os.path.splitext(caminho)[1].lower()
    assinaturas = ASSINATURAS.get(extensao)
    if not assinaturas or not any(dados.startswith(a) for a in assinaturas):
        return False
    return extensao != ".webp" or dados[8:12] == b"WEBP"


# Os arquivos livres conferidos: a pasta e a lista que registra cada um.
LISTAS_DE_LIVRES = {
    "servidor/bios_livres/": "servidor/bios_livres/lista.json",
    "testes/jogos_livres/": "testes/jogos_livres/lista.json",
}


def livres_conferidos():
    """{caminho no git: sha256} de cada arquivo que as listas de livres registram."""
    saida = {}
    for pasta, lista in LISTAS_DE_LIVRES.items():
        try:
            with open(os.path.join(RAIZ, *lista.split("/")), encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
        except (OSError, ValueError):
            continue
        for item in dados.get("arquivos", []):
            saida[pasta + item["origem"]] = item["sha256"]
    return saida


# Enderecos publicos que nao identificam ninguem: os DNS que o ARENA usa para
# ver se ha internet, e os de teste e de documentacao.
IPS_CONHECIDOS = {"1.1.1.1", "1.0.0.1", "8.8.8.8", "8.8.4.4", "9.9.9.9", "1.2.3.4", "4.3.2.1"}


def ip_publico(m):
    partes = [int(x) for x in m.groups()]
    if any(p > 255 for p in partes):
        return False
    if m.group(0) in IPS_CONHECIDOS:
        return False
    if (partes[0], partes[1], partes[2]) in ((192, 0, 2), (198, 51, 100), (203, 0, 113)):
        return False   # faixas de documentacao (RFC 5737)
    a, b = partes[0], partes[1]
    if a in (0, 10, 127) or a >= 224:
        return False
    if a == 169 and b == 254:
        return False
    if a == 172 and 16 <= b <= 31:
        return False
    if a == 192 and b == 168:
        return False
    if a == 100 and 64 <= b <= 127:   # CGNAT
        return False
    # Numeros de versao e de documentacao (1.2.3.4, 192.0.2.x...) passam a ser
    # so aviso: a lista mostra e quem confere decide.
    return True


def mascarar(texto):
    if len(texto) <= 8:
        return texto[:2] + "***"
    return texto[:6] + "***" + texto[-2:]


def refs_remotas():
    return [r for r in git("for-each-ref", "--format=%(refname)", "refs/remotes").split()
            if not r.endswith("/HEAD")]


def commits_a_publicar(ramos, tudo):
    argumentos = ["rev-list"] + ramos
    remotos = [] if tudo else refs_remotas()
    if remotos:
        argumentos += ["--not"] + remotos
    return [c for c in git(*argumentos).split() if c]


def arquivos_ja_publicados(tudo):
    """Os blobs que o GitHub ja tem. O "git push" so manda o que falta, entao
    o que ja esta la nao "vai junto" (a conferencia completa e' com --tudo)."""
    remotos = [] if tudo else refs_remotas()
    if not remotos:
        return set()
    return {linha.split()[0] for linha in git("rev-list", "--objects", *remotos).splitlines() if linha}


def principal(argumentos):
    if hasattr(sys.stdout, "reconfigure"):   # no teste, a saida e' um StringIO
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    tudo = "--tudo" in argumentos
    ramos = [a for a in argumentos if not a.startswith("--")]
    if not ramos:
        atual = git("rev-parse", "--abbrev-ref", "HEAD").strip()
        ramos = sorted({"main", atual} - {"HEAD"})
    commits = commits_a_publicar(ramos, tudo)
    print("Ramos: %s | commits a conferir: %d%s" % (", ".join(ramos), len(commits),
                                                    " (inclui o que ja esta no GitHub)" if tudo else ""))
    if not commits:
        print("Nada novo para enviar.")
        return 0

    # Cada arquivo (blob) de cada commit que o GitHub ainda nao tem: caminhos
    # e tamanho.
    publicados = arquivos_ja_publicados(tudo)
    caminhos = collections.defaultdict(set)
    tamanho = {}
    primeiro_commit = {}
    for commit in commits:
        # -z: o caminho vem cru. Sem ele, o git poe entre aspas o caminho com
        # acento ("BIOS/PS2/Jap\303\243o/...") e a regra "^BIOS/" nao pegava.
        for linha in git("ls-tree", "-r", "-l", "-z", "--full-tree", commit).split("\0"):
            if not linha:
                continue
            meta, caminho = linha.split("\t", 1)
            modo, tipo, sha, tam = meta.split()
            if tipo != "blob" or sha in publicados:
                continue
            caminhos[sha].add(caminho)
            tamanho[sha] = int(tam) if tam.isdigit() else 0
            primeiro_commit.setdefault(caminho, commit)

    bloqueantes, avisos = [], []

    def achado(lista, tipo, onde, detalhe):
        lista.append({"tipo": tipo, "onde": onde, "detalhe": detalhe})

    # Livre conferido: a extensao nao barra; o conteudo e' conferido abaixo.
    livres = livres_conferidos()
    todos_os_caminhos = sorted({c for cs in caminhos.values() for c in cs})
    for caminho in todos_os_caminhos:
        if PERMITIDOS.search(caminho):
            continue
        for regra, motivo in PROIBIDOS:
            if regra.search(caminho):
                achado(bloqueantes, "caminho proibido", caminho,
                       "%s (commit %s)" % (motivo, primeiro_commit[caminho][:7]))
                break
        else:
            if EXT_JOGO_OU_BIOS.search(caminho) and caminho not in livres:
                achado(bloqueantes, "jogo ou BIOS pela extensao", caminho,
                       "commit %s" % primeiro_commit[caminho][:7])

    # Conteudo: le cada blob uma vez.
    shas = sorted(caminhos)
    entrada = "".join(s + "\n" for s in shas).encode()
    bruto = git("cat-file", "--batch", entrada=entrada, binario=True)
    posicao = 0
    conteudo = {}
    while posicao < len(bruto):
        fim = bruto.index(b"\n", posicao)
        cabecalho = bruto[posicao:fim].decode().split()
        tam = int(cabecalho[2])
        conteudo[cabecalho[0]] = bruto[fim + 1:fim + 1 + tam]
        posicao = fim + 1 + tam + 1

    emails = collections.defaultdict(set)
    usuarios = collections.defaultdict(set)
    for sha in shas:
        dados = conteudo.get(sha, b"")
        nome = sorted(caminhos[sha])[0]
        conferidos = set()
        if any(c in livres for c in caminhos[sha]):
            marca = hashlib.sha256(dados).hexdigest()
            for caminho in sorted(c for c in caminhos[sha] if c in livres):
                if livres[caminho] == marca:
                    conferidos.add(caminho)
                else:
                    achado(bloqueantes, "arquivo livre diferente do conferido", caminho,
                           "o conteudo nao bate com a marca da lista.json")
        if b"\0" in dados[:8000]:
            # O codigo do ARENA e' todo texto. Binario so imagem/fonte de
            # verdade; qualquer outro pode ser BIOS, jogo ou save renomeado.
            for caminho in sorted(caminhos[sha]):
                if caminho in conferidos:
                    continue
                if not binario_permitido(caminho, dados):
                    achado(bloqueantes, "arquivo binario (nao e' imagem nem fonte)", caminho,
                           "%d bytes" % len(dados))
            if len(dados) > GRANDE:
                achado(avisos, "arquivo grande", nome, "%.1f MB" % (len(dados) / GRANDE))
            continue
        if len(dados) > GRANDE:
            achado(avisos, "arquivo grande", nome, "%.1f MB" % (len(dados) / GRANDE))
        texto = dados.decode("utf-8", "replace")
        for rotulo, regra in SEGREDOS:
            for m in regra.finditer(texto):
                achado(bloqueantes, rotulo, nome, mascarar(m.group(0)))
        for m in EMAIL.finditer(texto):
            emails[m.group(0).lower()].add(nome)
        for rotulo, regra in PESSOAIS:
            for m in regra.finditer(texto):
                achado(avisos, rotulo, nome, mascarar(m.group(0)))
        for m in NOME_DE_COMPUTADOR.finditer(texto):
            achado(avisos, "nome de computador", nome, m.group(0))
        for m in USUARIO_DO_WINDOWS.finditer(texto):
            usuario = m.group(1)
            if usuario.lower() not in USUARIOS_GENERICOS:
                usuarios[usuario].add(nome)
        for m in MAC.finditer(texto):
            achado(avisos, "endereco MAC", nome, mascarar(m.group(0)))
        for m in IPV4.finditer(texto):
            if ip_publico(m):
                achado(avisos, "endereco IP publico (ou numero de versao)", nome, m.group(0))

    # Mensagens e autores dos commits.
    # --stdin: com centenas de commits, a linha de comando passaria do limite
    # do Windows.
    mensagens = git("log", "--no-walk", "--stdin", "--format=%H%x00%ae%x00%ce%x00%B%x01",
                    entrada="".join(c + "\n" for c in commits).encode())
    for bloco in mensagens.split("\x01"):
        partes = bloco.strip("\n").split("\x00")
        if len(partes) < 4:
            continue
        commit, autor, quem_fez, mensagem = partes
        for endereco in (autor, quem_fez):
            emails[endereco.lower()].add("autor do commit %s" % commit[:7])
        for rotulo, regra in SEGREDOS:
            for m in regra.finditer(mensagem):
                achado(bloqueantes, rotulo, "mensagem do commit %s" % commit[:7], mascarar(m.group(0)))
        for m in EMAIL.finditer(mensagem):
            emails[m.group(0).lower()].add("mensagem do commit %s" % commit[:7])

    for endereco, onde in sorted(emails.items()):
        lista = sorted(onde)
        resumo = "%s (%d lugar(es): %s%s)" % (endereco, len(lista), ", ".join(lista[:3]),
                                              "..." if len(lista) > 3 else "")
        if EMAIL_LIVRE.match(endereco):
            continue
        if EMAIL_ALUNO.search(endereco):
            achado(bloqueantes, "e-mail de aluno", lista[0], resumo)
        elif EMAIL_INSTITUCIONAL.search(endereco):
            achado(bloqueantes, "e-mail institucional", lista[0], resumo)
        else:
            achado(avisos, "e-mail", lista[0], resumo)
    for usuario, onde in sorted(usuarios.items()):
        lista = sorted(onde)
        achado(avisos, "pasta de usuario do Windows", lista[0],
               "C:\\Users\\%s (%d arquivo(s): %s%s)" % (usuario, len(lista), ", ".join(lista[:3]),
                                                        "..." if len(lista) > 3 else ""))

    # Resumo na tela, por tipo.
    def mostrar(titulo, lista):
        print("\n%s: %d" % (titulo, len(lista)))
        por_tipo = collections.defaultdict(list)
        for a in lista:
            por_tipo[a["tipo"]].append(a)
        for tipo, itens in sorted(por_tipo.items()):
            print("  - %s: %d" % (tipo, len(itens)))
            for a in itens[:12]:
                print("      %s  ->  %s" % (a["onde"], a["detalhe"]))
            if len(itens) > 12:
                print("      ... e mais %d (veja o arquivo)" % (len(itens) - 12))

    print("Arquivos diferentes no historico conferido: %d (%d caminhos)" % (len(shas), len(todos_os_caminhos)))
    mostrar("BLOQUEANTES (nao envie antes de resolver)", bloqueantes)
    mostrar("AVISOS (confira um a um)", avisos)
    with open(DESTINO, "w", encoding="utf-8") as f:
        json.dump({"ramos": ramos, "commits": len(commits), "bloqueantes": bloqueantes, "avisos": avisos},
                  f, ensure_ascii=False, indent=1)
    print("\nLista completa (fora do repositorio): %s" % DESTINO)
    return 1 if bloqueantes else 0


if __name__ == "__main__":
    sys.exit(principal(sys.argv[1:]))
