# -*- coding: utf-8 -*-
r"""Recomps: o jogo de console que virou programa de PC (12/11/2026).

Um recomp (de "recompilacao") pega o codigo de maquina de um jogo de console
(N64, PS1, PS2, Xbox 360...) e o traduz para codigo de computador. O jogo
passa a rodar DIRETO, sem emulador: resolucao da tela, 60 quadros ou mais,
tela larga, controle moderno. O recomp traz so o codigo novo; os dados do
jogo (texturas, sons, mapas) continuam vindo da COPIA que a pessoa ja tem
(a ROM ou a imagem do disco). Quase todos sao de codigo aberto e saem nas
releases do GitHub de quem os fez.

O que este modulo faz, do jeito do ARENA ("baixar e jogar", sem instalar):

  1. Casa cada jogo da biblioteca com o catalogo (servidor\recomps.json, os
     fatos do catalogo publico do RecompLauncher; ferramentas\atualizar_recomps.py):
     o titulo do arquivo e o console dizem qual recomp serve.
  2. Baixa o recomp da release oficial do GitHub (a API publica diz os
     arquivos; o nome certo para este sistema vem do catalogo ou das
     palavras do nome), confere a marca SHA-256 quando o GitHub a publica
     e descompacta em emuladores\Recomps\<id>. Nada se instala.
  3. Abre o recomp com a copia do jogo. Quando o recomp traz o
     recomplauncher.json (o arquivo que descreve como ele e' aberto: o
     programa, os argumentos com {game}, a conferencia da copia, o preparo),
     o ARENA le e segue; sem ele, acha o programa sozinho e avisa que o
     jogo vai pedir a copia na primeira vez.

Tudo o que o RecompLauncher faz aqui foi reimplementado em Python puro, na
regra do projeto: programa de codigo fechado nao entra no ARENA; a tecnica
sim. As conferencias de disco (ISO 9660 do PS2, XDVDFS do Xbox 360) leem a
imagem direto, sem programa de fora.
"""
import fnmatch
import hashlib
import json
import os
import platform
import re
import shutil
import stat
import struct
import subprocess
import tarfile
import threading
import time
import unicodedata
import zipfile

import baixar
import plataforma as plataforma_do_sistema

PASTA_SERVIDOR = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(PASTA_SERVIDOR)
ARQUIVO_CATALOGO = os.path.join(PASTA_SERVIDOR, "recomps.json")
PASTA_RECOMPS = os.path.join(RAIZ, "emuladores", "Recomps")
# Em cada recomp baixado: de onde veio, a versao e a marca do arquivo.
MARCA = "arena-recomp.json"
# O arquivo que o proprio recomp traz dizendo como abrir (padrao do RecompLauncher SDK).
DESCRITOR = "recomplauncher.json"
API_RELEASE = "https://api.github.com/repos/%s/releases/%s"
SEGUNDOS_API = 40
SEGUNDOS_DOWNLOAD = 1800

# Palavras que tiram um arquivo da release da disputa (nunca sao o jogo).
RE_NUNCA = re.compile(r"debug|symbols|\bpdb\b|source|\.sha256$|\.sha512$|\.sig$|\.asc$|\.txt$|\.md$|\.json$|\.pdb$",
                      re.IGNORECASE)
RE_OUTRO_SISTEMA = {
    "windows": re.compile(r"linux|appimage|mac|macos|osx|darwin|\.dmg$|android|\.apk$|flatpak|steamdeck|deck",
                          re.IGNORECASE),
    "linux": re.compile(r"win(dows|64|32)?\b|\.exe$|\.msi$|mac|macos|osx|darwin|\.dmg$|android|\.apk$",
                        re.IGNORECASE),
}
RE_ARM = re.compile(r"arm64|aarch64|\barm\b", re.IGNORECASE)
EXTENSOES = {"windows": (".zip", ".7z", ".rar", ".exe", ".msi"),
             "linux": (".appimage", ".tar.gz", ".tgz", ".tar.xz", ".tar.zst", ".zip", ".tar", ".flatpak")}
# Programas que aparecem na pasta de um jogo de PC e nunca sao o jogo.
RE_NAO_E_O_JOGO = re.compile(r"unins|uninstall|crash|redist|vcredist|dxsetup|dxwebsetup|setup|updater|update|dotnet|"
                             r"7z|unrar|python|java\b|node\b|ffmpeg|launcherhelper", re.IGNORECASE)

_catalogo = {"dados": None}
_TRAVA = threading.Lock()
# O andamento de cada download, para a tela acompanhar: {id: {"estado", "etapa", "feito", "total", "mensagem"}}.
PROGRESSO = {}


class NaoDaParaInstalar(Exception):
    """O que impede de baixar ou descompactar, em frase para o aluno."""


# ---------------------------------------------------------------------------
# O catalogo e o casamento com os jogos da biblioteca
# ---------------------------------------------------------------------------

def chave(texto):
    """A chave de comparacao de um titulo: minusculas, sem acento, sem 'the', so letras e numeros. 'Legend of Zelda,
    The - Majora's Mask' (nome de arquivo) e "The Legend of Zelda: Majora's Mask" (catalogo) dao a mesma chave.
    A mesma conta de ferramentas\\atualizar_recomps.py."""
    texto = unicodedata.normalize("NFKD", texto or "")
    texto = "".join(c for c in texto if not unicodedata.combining(c)).lower()
    texto = re.sub(r"\([^)]*\)|\[[^\]]*\]", " ", texto)   # (USA), [!]: a regiao e as marcas do arquivo
    texto = re.sub(r"\b(the|a|an)\b", " ", texto)
    texto = texto.replace("&", "and")
    return re.sub(r"[^a-z0-9]+", "", texto)


def carregar():
    """O catalogo (servidor\\recomps.json), lido uma vez. Sem o arquivo: vazio."""
    if _catalogo["dados"] is None:
        try:
            with open(ARQUIVO_CATALOGO, "r", encoding="utf-8") as arquivo:
                _catalogo["dados"] = json.load(arquivo)
        except (OSError, ValueError):
            _catalogo["dados"] = {"recomps": {}, "por_titulo": {}}
    return _catalogo["dados"]


def sistema():
    """'windows' ou 'linux' (o Linux do Chromebook conta como Linux); None onde recomp nao roda (Android)."""
    nome = plataforma_do_sistema.nome_do_sistema()
    if nome == "windows":
        return "windows"
    if nome in ("linux", "chromeos"):
        return "linux"
    return None


def arquitetura():
    """'x64' ou 'arm64' (a maquina em que o ARENA esta)."""
    maquina = platform.machine().lower()
    return "arm64" if maquina in ("arm64", "aarch64") else "x64"


def recomp(recomp_id):
    return carregar().get("recomps", {}).get(recomp_id)


def para_o_titulo(titulo, plataforma_id, so_deste_sistema=True):
    """Os recomps do jogo 'titulo' do console 'plataforma_id', na ordem de preferencia do catalogo. Com
    'so_deste_sistema', so os que tem versao para o sistema em que o ARENA esta."""
    dados = carregar()
    ids = dados.get("por_titulo", {}).get("%s|%s" % (plataforma_id, chave(titulo)), [])
    lista = [dados["recomps"][i] for i in ids if i in dados.get("recomps", {})]
    if so_deste_sistema:
        atual = sistema()
        lista = [r for r in lista if atual and atual in r.get("sistemas", [])]
    return lista


def pasta_do(recomp_id):
    return os.path.join(PASTA_RECOMPS, re.sub(r"[^a-z0-9_-]", "", recomp_id.lower()))


def ler_marca(pasta):
    try:
        with open(os.path.join(pasta, MARCA), "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except (OSError, ValueError):
        return None


def instalado(recomp_id):
    """O programa do recomp ja baixado, ou None."""
    pasta = pasta_do(recomp_id)
    if not os.path.isdir(pasta) or not ler_marca(pasta):
        return None
    return programa_na_pasta(pasta)


def resumo_para_a_tela(r):
    """O que a tela mostra de um recomp: nome, de quem, licenca, tamanho e se ja esta aqui."""
    programa = instalado(r["id"])
    return {"id": r["id"], "nome": r["nome"], "repo": r.get("repo", ""), "licenca": r.get("licenca", ""),
            "versao": r.get("versao", ""), "tamanho": r.get("tamanho", ""), "instalado": bool(programa),
            "sistemas": r.get("sistemas", []), "estrelas": r.get("estrelas", 0)}


def jeitos_para(titulo, plataforma_id):
    """Os recomps do jogo como 'jeitos de abrir' (servidor\\jeitos_de_abrir.py): id 'recomp:<id>'."""
    jeitos = []
    for r in para_o_titulo(titulo, plataforma_id):
        pronto = instalado(r["id"]) is not None
        licenca = r.get("licenca") or "licença não informada"
        jeitos.append({
            "id": "recomp:" + r["id"],
            "titulo": "%s · versão para PC" % r["nome"],
            "explica": ("O jogo recompilado para rodar direto no computador, sem emulador: resolução alta, 60 quadros "
                        "ou mais e controle moderno (%s, %s). %s"
                        % (licenca, r.get("tamanho") or "tamanho não informado",
                           "Já está no ARENA." if pronto else
                           "O ARENA baixa da release oficial no GitHub (%s) e abre com a sua cópia do jogo."
                           % (r.get("repo") or "o repositório do autor"))),
            "selo": "nativo" if pronto else "baixar e jogar",
            "recomp": r["id"],
        })
    return jeitos


# ---------------------------------------------------------------------------
# A release no GitHub e o arquivo certo para este sistema
# ---------------------------------------------------------------------------

def escolher_arquivo(nomes, padrao, sistema_alvo, arq="x64"):
    """Qual arquivo da release baixar. Primeiro o padrao do catalogo ('Zelda64Recompiled-*-Windows.zip'); sem ele
    ou sem par, pelas palavras do nome (as mesmas regras do RecompLauncher: o sistema e o processador no nome; zip
    antes de instalador; nada de debug, symbols, source nem marcas .sha256/.sig). None se nenhum serve."""
    candidatos = [n for n in nomes if not RE_NUNCA.search(n)]
    if padrao:
        for n in candidatos:
            if fnmatch.fnmatch(n.lower(), padrao.lower()):
                return n
    outro = RE_OUTRO_SISTEMA.get(sistema_alvo)
    extensoes = EXTENSOES.get(sistema_alvo, ())

    def serve(nome):
        baixo = nome.lower()
        if outro and outro.search(baixo):
            return False
        if arq != "arm64" and RE_ARM.search(baixo):
            return False
        if arq == "arm64" and not RE_ARM.search(baixo):
            return False
        return any(baixo.endswith(e) for e in extensoes)

    def nota(nome):
        baixo = nome.lower()
        pontos = 0
        if sistema_alvo == "windows":
            pontos += 4 if re.search(r"win(dows|64)?\b|windows", baixo) else 0
            pontos += 2 if re.search(r"x64|x86_64|amd64|64", baixo) else 0
            pontos += 3 if baixo.endswith(".zip") else (1 if baixo.endswith((".7z", ".rar")) else 0)
        else:
            pontos += 2 if "linux" in baixo else 0
            pontos += 5 if baixo.endswith(".appimage") else (3 if baixo.endswith((".tar.gz", ".tgz", ".tar.xz")) else
                                                             (1 if baixo.endswith(".zip") else 0))
            pontos += 1 if re.search(r"x86_64|x64|amd64", baixo) else 0
        return pontos

    bons = [n for n in candidatos if serve(n)]
    if not bons:
        return None
    bons.sort(key=lambda n: (-nota(n), n.lower()))
    return bons[0]


def _api(url):
    codigo, bruto = baixar.rodar(url, SEGUNDOS_API)
    if codigo != 0 or not bruto:
        return None
    try:
        return json.loads(bruto.decode("utf-8"))
    except ValueError:
        return None


def release(repo, tag=""):
    """A release do GitHub: {"tag", "arquivos": [{"nome", "url", "tamanho", "sha256"}]}. A do 'tag' do catalogo;
    sem ela, a mais nova. A API publica do GitHub deixa 60 consultas por hora sem conta: a mensagem avisa."""
    dados = None
    if tag:
        dados = _api(API_RELEASE % (repo, "tags/" + tag))
    if not dados:
        dados = _api(API_RELEASE % (repo, "latest"))
    if not dados or not isinstance(dados, dict) or "assets" not in dados:
        raise NaoDaParaInstalar(
            "Não consegui ler a release de %s no GitHub. Sem internet não dá; com internet, o GitHub limita as "
            "consultas (60 por hora por computador): espere um pouco e tente de novo." % repo)
    arquivos = []
    for a in dados.get("assets") or []:
        marca = str(a.get("digest") or "")
        arquivos.append({"nome": a.get("name") or "", "url": a.get("browser_download_url") or "",
                         "tamanho": int(a.get("size") or 0),
                         "sha256": marca.split(":", 1)[1].lower() if marca.startswith("sha256:") else ""})
    return {"tag": dados.get("tag_name") or tag, "arquivos": arquivos}


# ---------------------------------------------------------------------------
# Baixar e descompactar (nada se instala)
# ---------------------------------------------------------------------------

def _anotar(recomp_id, **campos):
    with _TRAVA:
        atual = PROGRESSO.setdefault(recomp_id, {"estado": "rodando", "etapa": "", "feito": 0, "total": 0,
                                                 "mensagem": ""})
        atual.update(campos)


def progresso(recomp_id):
    with _TRAVA:
        return dict(PROGRESSO.get(recomp_id) or {})


def _sha256(caminho):
    resumo = hashlib.sha256()
    with open(caminho, "rb") as arquivo:
        for pedaco in iter(lambda: arquivo.read(1024 * 1024), b""):
            resumo.update(pedaco)
    return resumo.hexdigest()


def _seguro(nome):
    """Um caminho de dentro de um zip/tar que pode ser gravado: relativo, sem '..' e sem unidade."""
    nome = nome.replace("\\", "/")
    if not nome or nome.startswith("/") or ".." in nome.split("/") or ":" in nome.split("/")[0]:
        return False
    return True


def _descompactar(arquivo, destino):
    """Descompacta 'arquivo' em 'destino' (que nao existe ainda). Zip e tar (gz, xz) pelo Python; o AppImage e
    copiado e marcado como executavel. 7z, rar, exe e msi: o ARENA nao abre sozinho (avisa)."""
    baixo = arquivo.lower()
    os.makedirs(destino, exist_ok=True)
    if baixo.endswith(".zip"):
        with zipfile.ZipFile(arquivo) as zip_:
            for info in zip_.infolist():
                if not _seguro(info.filename):
                    continue
                zip_.extract(info, destino)
                # O zip do Linux guarda a permissao de executar nos bits altos: devolve-a.
                modo = (info.external_attr >> 16) & 0o777
                if modo and not info.is_dir():
                    try:
                        os.chmod(os.path.join(destino, info.filename), modo | stat.S_IRUSR | stat.S_IWUSR)
                    except OSError:
                        pass
    elif baixo.endswith((".tar.gz", ".tgz", ".tar.xz", ".tar")):
        with tarfile.open(arquivo) as tar:
            membros = [m for m in tar.getmembers() if _seguro(m.name) and (m.isfile() or m.isdir())]
            tar.extractall(destino, members=membros, filter="data")
    elif baixo.endswith(".appimage"):
        copia = os.path.join(destino, os.path.basename(arquivo))
        shutil.copyfile(arquivo, copia)
        try:
            os.chmod(copia, os.stat(copia).st_mode | 0o755)
        except OSError:
            pass
    else:
        extensao = os.path.splitext(baixo)[1] or "esse formato"
        raise NaoDaParaInstalar(
            "O autor publica este recomp como %s, que o ARENA não descompacta sozinho (só zip, tar e AppImage). "
            "Baixe do GitHub, descompacte em emuladores\\Recomps\\%s e clique em Jogar de novo."
            % (extensao, os.path.basename(destino)))
    _desembrulhar(destino)


def _desembrulhar(destino):
    """Zip com uma pasta so por cima ('MyRecomp-v1.2.0/...'): o conteudo sobe para 'destino'."""
    itens = [n for n in os.listdir(destino) if n != MARCA]
    if len(itens) != 1 or not os.path.isdir(os.path.join(destino, itens[0])):
        return
    de = os.path.join(destino, itens[0])
    for nome in os.listdir(de):
        shutil.move(os.path.join(de, nome), os.path.join(destino, nome))
    os.rmdir(de)


def instalar(recomp_id, sistema_alvo=None, arq=None):
    """Baixa e descompacta o recomp em emuladores\\Recomps\\<id>. Devolve o caminho do programa. Lanca
    NaoDaParaInstalar com a frase para o aluno; o andamento fica em PROGRESSO[recomp_id]."""
    r = recomp(recomp_id)
    if not r:
        raise NaoDaParaInstalar("Esse recomp não está no catálogo do ARENA.")
    sistema_alvo = sistema_alvo or sistema()
    arq = arq or arquitetura()
    if not sistema_alvo or sistema_alvo not in r.get("sistemas", []):
        raise NaoDaParaInstalar("%s não tem versão para este sistema (só %s)." % (r["nome"], ", ".join(r.get("sistemas") or [])))
    _anotar(recomp_id, estado="rodando", etapa="release", feito=0, total=0, mensagem="Lendo a release no GitHub...")
    pasta = pasta_do(recomp_id)
    baixando = os.path.join(PASTA_RECOMPS, ".baixando")
    try:
        rel = release(r.get("repo", ""), r.get("tag", ""))
        nome = escolher_arquivo([a["nome"] for a in rel["arquivos"]], (r.get("arquivos") or {}).get(sistema_alvo),
                                sistema_alvo, arq)
        if not nome:
            raise NaoDaParaInstalar("A release %s de %s não tem arquivo para %s %s." % (rel["tag"], r["nome"], sistema_alvo, arq))
        arquivo = next(a for a in rel["arquivos"] if a["nome"] == nome)
        if not arquivo["url"].lower().startswith("https://"):
            raise NaoDaParaInstalar("O arquivo da release não vem por https; o ARENA não baixa assim.")
        _anotar(recomp_id, etapa="baixando", total=arquivo["tamanho"],
                mensagem="Baixando %s (%s)..." % (nome, _legivel(arquivo["tamanho"])))
        os.makedirs(baixando, exist_ok=True)
        caminho = os.path.join(baixando, "%s-%s" % (recomp_id, re.sub(r"[^A-Za-z0-9._-]", "_", nome)))
        codigo, _ = baixar.rodar(arquivo["url"], SEGUNDOS_DOWNLOAD, destino=caminho)
        if codigo != 0 or not os.path.isfile(caminho):
            raise NaoDaParaInstalar("O download de %s falhou (código %s). Confira a internet e tente de novo." % (nome, codigo))
        _anotar(recomp_id, etapa="conferindo", feito=arquivo["tamanho"], mensagem="Conferindo a marca do arquivo...")
        marca = _sha256(caminho)
        # Duas marcas: a do catalogo (guardada a parte, vale para o mesmo nome de arquivo) e a que o GitHub publica.
        # A do catalogo manda; as duas tem que bater com o arquivo. Sem nenhuma, o download vale pelo https da
        # release oficial que a pessoa confirmou na tela (risco aceito, anotado em docs\PENDENCIAS.md, 12/11/2026).
        do_catalogo = (r.get("marcas") or {}).get(sistema_alvo) or {}
        esperadas = [m.lower() for m in (do_catalogo.get("sha256") if do_catalogo.get("nome") == nome else "",
                                         arquivo["sha256"]) if m]
        if any(marca.lower() != m for m in esperadas):
            os.remove(caminho)
            raise NaoDaParaInstalar("A marca SHA-256 de %s não bate com a publicada: o download veio errado ou foi "
                                    "trocado. Nada foi instalado; tente de novo." % nome)
        esperada = esperadas[0] if esperadas else ""
        _anotar(recomp_id, etapa="descompactando", mensagem="Descompactando em emuladores\\Recomps\\%s..." % os.path.basename(pasta))
        nova = pasta + ".nova"
        if os.path.isdir(nova):
            shutil.rmtree(nova)
        _descompactar(caminho, nova)
        with open(os.path.join(nova, MARCA), "w", encoding="utf-8") as saida:
            json.dump({"id": recomp_id, "nome": r["nome"], "repo": r.get("repo", ""), "tag": rel["tag"],
                       "arquivo": nome, "sha256": marca, "conferido": bool(esperada),
                       "conferido_pelo_catalogo": do_catalogo.get("nome") == nome,
                       "instalado_em": time.strftime("%Y-%m-%d %H:%M")}, saida, ensure_ascii=False, indent=1)
        if os.path.isdir(pasta):
            # Versao nova por cima da antiga: o que o jogo gravou (saves, ajustes) fica, como manda o padrao.
            for atual, _subpastas, nomes in os.walk(nova):
                relativo = os.path.relpath(atual, nova)
                os.makedirs(os.path.join(pasta, relativo), exist_ok=True)
                for n in nomes:
                    shutil.move(os.path.join(atual, n), os.path.join(pasta, relativo, n))
            shutil.rmtree(nova)
        else:
            os.replace(nova, pasta)
        os.remove(caminho)
        programa = programa_na_pasta(pasta)
        if not programa:
            raise NaoDaParaInstalar("Baixei %s, mas não achei o programa dentro da pasta emuladores\\Recomps\\%s."
                                    % (r["nome"], os.path.basename(pasta)))
        _anotar(recomp_id, estado="pronto", etapa="pronto", mensagem="%s pronto." % r["nome"])
        return programa
    except NaoDaParaInstalar as falha:
        _anotar(recomp_id, estado="erro", mensagem=str(falha))
        raise
    except (OSError, zipfile.BadZipFile, tarfile.TarError) as falha:
        _anotar(recomp_id, estado="erro", mensagem="Não consegui instalar %s: %s" % (r["nome"], falha))
        raise NaoDaParaInstalar("Não consegui instalar %s: %s" % (r["nome"], falha))


def _legivel(tamanho):
    if tamanho >= 1024 ** 3:
        return "%.1f GB" % (tamanho / 1024 ** 3)
    if tamanho >= 1024 ** 2:
        return "%d MB" % (tamanho / 1024 ** 2)
    return "%d KB" % max(1, tamanho // 1024)


# ---------------------------------------------------------------------------
# O programa dentro da pasta e o recomplauncher.json
# ---------------------------------------------------------------------------

def ler_descritor(pasta):
    """O recomplauncher.json do recomp (na pasta ou um nivel abaixo), ou None."""
    for base in [pasta] + [os.path.join(pasta, n) for n in sorted(os.listdir(pasta))
                           if os.path.isdir(os.path.join(pasta, n))]:
        caminho = os.path.join(base, DESCRITOR)
        if os.path.isfile(caminho):
            try:
                with open(caminho, "r", encoding="utf-8-sig") as arquivo:
                    dados = json.load(arquivo)
                if isinstance(dados, dict):
                    dados["_pasta"] = base
                    return dados
            except (OSError, ValueError):
                return None
    return None


def _e_elf(caminho):
    try:
        with open(caminho, "rb") as arquivo:
            return arquivo.read(4) == b"\x7fELF"
    except OSError:
        return False


def programa_na_pasta(pasta, sistema_alvo=None):
    """O programa que abre o recomp. Pelo recomplauncher.json (start.program, o primeiro que existe); sem ele, o
    maior .exe (Windows) ou o AppImage / programa ELF (Linux) que nao seja instalador, desinstalador ou ajudante."""
    sistema_alvo = sistema_alvo or sistema() or "windows"
    descritor = ler_descritor(pasta)
    if descritor:
        base = descritor.get("_pasta", pasta)
        programas = (descritor.get("start") or {}).get("program") or []
        if isinstance(programas, str):
            programas = [programas]
        for p in programas:
            candidato = os.path.normpath(os.path.join(base, preencher(p, {"install": base})))
            if os.path.isfile(candidato):
                return candidato
    candidatos = []
    for atual, subpastas, nomes in os.walk(pasta):
        profundidade = os.path.relpath(atual, pasta).count(os.sep) + (0 if atual == pasta else 1)
        if profundidade > 2:
            subpastas[:] = []
            continue
        for n in nomes:
            caminho = os.path.join(atual, n)
            baixo = n.lower()
            if RE_NAO_E_O_JOGO.search(baixo) or n == MARCA:
                continue
            if sistema_alvo == "windows":
                if baixo.endswith(".exe"):
                    candidatos.append((profundidade, -os.path.getsize(caminho), caminho))
            else:
                if baixo.endswith(".appimage"):
                    candidatos.append((profundidade - 1, -os.path.getsize(caminho), caminho))
                elif not os.path.splitext(baixo)[1] and _e_elf(caminho):
                    candidatos.append((profundidade, -os.path.getsize(caminho), caminho))
                elif baixo.endswith(".sh"):
                    candidatos.append((profundidade + 1, -os.path.getsize(caminho), caminho))
    if not candidatos:
        return None
    candidatos.sort()
    return candidatos[0][2]


def variaveis(pasta, caminho_jogo=""):
    """Os lugares que o recomplauncher.json escreve entre chaves: {install}, {game}, {documents}, {local},
    {config}, {home} e {pad}."""
    casa = os.path.expanduser("~")
    if plataforma_do_sistema.WINDOWS:
        local = os.environ.get("LOCALAPPDATA") or os.path.join(casa, "AppData", "Local")
        config = os.environ.get("APPDATA") or os.path.join(casa, "AppData", "Roaming")
        documentos = os.path.join(casa, "Documents")
    else:
        local = os.environ.get("XDG_DATA_HOME") or os.path.join(casa, ".local", "share")
        config = os.environ.get("XDG_CONFIG_HOME") or os.path.join(casa, ".config")
        documentos = os.path.join(casa, "Documents")
    return {"install": pasta, "game": caminho_jogo, "documents": documentos, "local": local, "config": config,
            "home": casa, "pad": "xbox"}


def preencher(valor, vars_):
    """Troca {install}, {game}... por seus valores. Lista e dicionario sao preenchidos por dentro."""
    if isinstance(valor, str):
        for nome, caminho in vars_.items():
            valor = valor.replace("{%s}" % nome, caminho)
        return valor
    if isinstance(valor, list):
        return [preencher(v, vars_) for v in valor]
    if isinstance(valor, dict):
        return {k: preencher(v, vars_) for k, v in valor.items()}
    return valor


def _primeiro_caminho(entrada, vars_):
    """Um campo de arquivo do descritor: string, ou lista de {"path", "if"} (vale o primeiro cujo 'if' existe; sem
    'if' e' o de reserva)."""
    if isinstance(entrada, str):
        return preencher(entrada, vars_)
    if isinstance(entrada, list):
        reserva = None
        for item in entrada:
            if not isinstance(item, dict):
                continue
            caminho = preencher(item.get("path", ""), vars_)
            if "if" in item:
                if os.path.exists(preencher(item["if"], vars_)):
                    return caminho
            elif reserva is None:
                reserva = caminho
        return reserva
    return None


# ---------------------------------------------------------------------------
# A copia do jogo: e' a certa? (as conferencias do descritor)
# ---------------------------------------------------------------------------

def nomes_na_raiz_iso9660(caminho):
    """Os nomes da pasta de cima de uma imagem ISO 9660 (o disco do PS2, do PS1, do PSP). Le o Descritor
    Primario do Volume (setor 16) e a pasta raiz que ele aponta. Vazio se nao for ISO 9660."""
    nomes = []
    try:
        with open(caminho, "rb") as disco:
            disco.seek(16 * 2048)
            pvd = disco.read(2048)
            if pvd[1:6] != b"CD001":
                # Imagem com cabecalho de setor bruto (2352 bytes por setor, o .bin de CD): tenta de novo.
                disco.seek(16 * 2352 + 16)
                pvd = disco.read(2048)
                if pvd[1:6] != b"CD001":
                    return []
                setor = 2352
            else:
                setor = 2048
            raiz = pvd[156:190]
            extensao, tamanho = struct.unpack("<I", raiz[2:6])[0], struct.unpack("<I", raiz[10:14])[0]
            disco.seek(extensao * setor + (16 if setor == 2352 else 0))
            dados = b""
            lidos = 0
            while lidos < tamanho:
                dados += disco.read(2048)
                lidos += 2048
                if setor == 2352:
                    disco.seek(disco.tell() + 304)
            posicao = 0
            while posicao < len(dados):
                comprimento = dados[posicao]
                if comprimento == 0:
                    # Fim do setor: pula para o proximo.
                    posicao = (posicao // 2048 + 1) * 2048
                    continue
                tamanho_nome = dados[posicao + 32]
                nome = dados[posicao + 33:posicao + 33 + tamanho_nome].decode("ascii", "replace")
                if nome not in ("\x00", "\x01"):
                    nomes.append(nome.split(";")[0])
                posicao += comprimento
    except (OSError, struct.error, IndexError):
        return []
    return nomes


def nomes_na_raiz_xdvdfs(caminho):
    """Os nomes da pasta de cima de uma imagem de disco de Xbox 360 (XDVDFS). O volume comeca num dos
    deslocamentos conhecidos; a marca 'MICROSOFT*XBOX*MEDIA' fica no setor 32 a partir dele."""
    nomes = []
    try:
        tamanho_total = os.path.getsize(caminho)
        with open(caminho, "rb") as disco:
            base = None
            for inicio in (0, 0xFD90000, 0x2080000, 0x18300000):
                if inicio + 0x10000 + 2048 > tamanho_total:
                    continue
                disco.seek(inicio + 32 * 2048)
                cabecalho = disco.read(2048)
                if cabecalho[:20] == b"MICROSOFT*XBOX*MEDIA":
                    base = inicio
                    break
            if base is None:
                return []
            setor_raiz, tamanho_raiz = struct.unpack("<II", cabecalho[20:28])
            disco.seek(base + setor_raiz * 2048)
            dados = disco.read(max(2048, min(tamanho_raiz, 1024 * 1024)))
        posicao = 0
        while posicao + 14 <= len(dados):
            if dados[posicao:posicao + 4] == b"\xff\xff\xff\xff":
                posicao = (posicao // 2048 + 1) * 2048    # fim do setor
                continue
            tamanho_nome = dados[posicao + 13]
            nome = dados[posicao + 14:posicao + 14 + tamanho_nome].decode("ascii", "replace")
            if not nome:
                break
            nomes.append(nome)
            posicao += 14 + tamanho_nome
            posicao = (posicao + 3) & ~3
    except (OSError, struct.error, IndexError):
        return []
    return nomes


def conferir_copia(game, caminho):
    """A copia do jogo passa na conferencia do descritor ('game.check')? Devolve "" se sim, ou a frase do que esta
    errado. Sem 'check', passa."""
    if not game or not isinstance(game, dict):
        return ""
    tipo = game.get("kind") or "iso_or_folder"
    e_pasta = os.path.isdir(caminho)
    if tipo == "iso" and e_pasta:
        return "Este recomp precisa da imagem do disco (um arquivo .iso), não de uma pasta."
    if tipo == "folder" and not e_pasta:
        return "Este recomp precisa da pasta do jogo extraída, não da imagem do disco."
    check = game.get("check") or {}
    if "file" in check:
        if e_pasta and not os.path.isfile(os.path.join(caminho, check["file"])):
            return "A pasta não tem o arquivo %s que este jogo precisa." % check["file"]
    if "iso9660" in check and not e_pasta:
        nomes = [n.lower() for n in nomes_na_raiz_iso9660(caminho)]
        if not nomes:
            return "Não consegui ler esta imagem como disco ISO 9660 (é .chd ou .cue? este recomp quer o .iso)."
        if check["iso9660"].lower() not in nomes:
            return ("Este disco não é o que o recomp espera (ele procura %s na raiz). %s"
                    % (check["iso9660"], game.get("label") or ""))
    if "xdvdfs" in check and not e_pasta:
        nomes = [n.lower() for n in nomes_na_raiz_xdvdfs(caminho)]
        if not nomes:
            return "Não consegui ler esta imagem como disco de Xbox 360 (XDVDFS); este recomp quer o .iso do disco."
        if check["xdvdfs"].lower() not in nomes:
            return ("Este disco não é o que o recomp espera (ele procura %s na raiz). %s"
                    % (check["xdvdfs"], game.get("label") or ""))
    return ""


# ---------------------------------------------------------------------------
# Os ajustes do recomp (nivel 2 do descritor: 'config')
# ---------------------------------------------------------------------------

def _valor_toml(texto):
    return json.dumps(texto)   # string TOML basica = string JSON (as mesmas aspas e barras)


def escrever_configuracao(descritor, vars_):
    """Escreve nos arquivos de ajuste do recomp o que o descritor manda antes de abrir: 'game_path' (a copia do
    jogo, sempre), 'always' (sempre), 'ensure' (so quando falta) e 'new' (so se o arquivo nao existe). TOML e INI
    linha a linha, para os comentarios e o resto ficarem como estao; JSON pelo json. Devolve os arquivos escritos."""
    escritos = []
    configs = descritor.get("config") or []
    if isinstance(configs, dict):
        configs = [configs]
    for cfg in configs:
        if not isinstance(cfg, dict):
            continue
        caminho = _primeiro_caminho(cfg.get("file"), vars_)
        if not caminho:
            continue
        formato = (cfg.get("format") or os.path.splitext(caminho)[1].lstrip(".") or "toml").lower()
        existia = os.path.isfile(caminho)
        novos = dict(cfg.get("new") or {}) if not existia else {}
        sempre = dict(cfg.get("always") or {})
        garantir = dict(cfg.get("ensure") or {})
        chave_jogo = cfg.get("game_path")
        if chave_jogo and vars_.get("game"):
            sempre[chave_jogo] = _valor_toml(vars_["game"]) if formato == "toml" else vars_["game"]
        if not (novos or sempre or garantir):
            continue
        os.makedirs(os.path.dirname(caminho) or ".", exist_ok=True)
        if formato == "json":
            try:
                with open(caminho, "r", encoding="utf-8") as arquivo:
                    dados = json.load(arquivo) if existia else {}
            except (OSError, ValueError):
                dados = {}
            if not isinstance(dados, dict):
                dados = {}
            for k, v in novos.items():
                dados.setdefault(k, v)
            for k, v in garantir.items():
                if dados.get(k) in (None, ""):
                    dados[k] = v
            dados.update(sempre)
            texto = json.dumps(dados, ensure_ascii=False, indent=2) + "\n"
        else:
            try:
                with open(caminho, "r", encoding="utf-8") as arquivo:
                    linhas = arquivo.read().splitlines() if existia else []
            except OSError:
                linhas = []
            linhas = _escrever_chaves(linhas, novos, so_se_falta=True)
            linhas = _escrever_chaves(linhas, garantir, so_se_falta=True, tambem_vazia=True)
            linhas = _escrever_chaves(linhas, sempre, so_se_falta=False)
            texto = "\n".join(linhas) + "\n"
        temporario = caminho + ".arena-tmp"
        with open(temporario, "w", encoding="utf-8", newline="\n") as saida:
            saida.write(texto)
        os.replace(temporario, caminho)
        escritos.append(caminho)
    return escritos


def _escrever_chaves(linhas, chaves, so_se_falta, tambem_vazia=False):
    """Linha a linha (TOML e INI): troca o valor de cada chave que existe, acrescenta no fim a que falta."""
    linhas = list(linhas)
    for chave_, valor in chaves.items():
        padrao = re.compile(r"^(\s*)%s(\s*)=(\s*)(.*)$" % re.escape(chave_))
        achou = False
        for n, linha in enumerate(linhas):
            par = padrao.match(linha)
            if not par:
                continue
            achou = True
            vazia = par.group(4).strip().strip('"').strip("'") == ""
            if not so_se_falta or (tambem_vazia and vazia):
                linhas[n] = "%s%s%s=%s%s" % (par.group(1), chave_, par.group(2) or " ", par.group(3) or " ", valor)
            break
        if not achou:
            linhas.append("%s = %s" % (chave_, valor))
    return linhas


# ---------------------------------------------------------------------------
# O preparo (nivel 3: 'prepare') e a abertura
# ---------------------------------------------------------------------------

def _marca_de_preparo(pasta, caminho_jogo):
    return os.path.join(pasta, ".arena-preparado-%s" % hashlib.sha1(caminho_jogo.encode("utf-8", "replace")).hexdigest()[:12])


def preparar(descritor, pasta, caminho_jogo, recomp_id, avisar=print):
    """O passo de preparo do proprio recomp (tirar fontes e arte do disco, montar cache), sem janela, lendo as
    linhas 'progress 0.4 Texto' que ele imprime. Roda uma vez por copia do jogo. Devolve "" ou o erro."""
    prep = descritor.get("prepare")
    if not prep or not isinstance(prep, dict):
        return ""
    marca = _marca_de_preparo(pasta, caminho_jogo)
    if os.path.isfile(marca):
        return ""
    vars_ = variaveis(pasta, caminho_jogo)
    programas = prep.get("program") or []
    if isinstance(programas, str):
        programas = [programas]
    programa = next((os.path.normpath(os.path.join(pasta, preencher(p, vars_))) for p in programas
                     if os.path.isfile(os.path.normpath(os.path.join(pasta, preencher(p, vars_))))), None)
    if not programa:
        return "O passo de preparo do recomp aponta para um programa que não está na pasta."
    comando = [plataforma_do_sistema.programa_que_roda(programa, "recomp-" + recomp_id)] + list(preencher(prep.get("args") or [], vars_))
    limite = int(prep.get("timeout") or 300)
    _anotar(recomp_id, estado="rodando", etapa="preparando", feito=0, total=100,
            mensagem=prep.get("label") or "Preparando o jogo...")
    extras = {}
    if plataforma_do_sistema.WINDOWS:
        extras["creationflags"] = 0x08000000   # CREATE_NO_WINDOW
    try:
        processo = subprocess.Popen(comando, cwd=pasta, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True, encoding="utf-8", errors="replace", **extras)
        inicio = time.monotonic()
        for linha in processo.stdout:
            par = re.match(r"\s*progress\s+([0-9.]+)\s*(.*)", linha)
            if par:
                try:
                    _anotar(recomp_id, feito=int(float(par.group(1)) * 100), mensagem=par.group(2).strip() or prep.get("label") or "")
                except ValueError:
                    pass
            if time.monotonic() - inicio > limite:
                processo.kill()
                return "O preparo do recomp passou de %d s e foi interrompido." % limite
        codigo = processo.wait()
    except OSError as falha:
        return "Não consegui rodar o preparo do recomp: %s" % falha
    if codigo != 0:
        return "O preparo do recomp terminou com erro (código %s)." % codigo
    try:
        with open(marca, "w", encoding="utf-8") as saida:
            saida.write(caminho_jogo + "\n")
    except OSError:
        pass
    _anotar(recomp_id, estado="pronto", etapa="pronto", feito=100, mensagem="Pronto.")
    avisar("[ARENA] Preparo do recomp %s feito." % recomp_id)
    return ""


def externo_para(recomp_id, caminho_jogo, avisar=print):
    """Como o /api/jogar abre um recomp: o mesmo dicionario do emulador de fora (jogo["externo"]), com o programa,
    os argumentos (a copia do jogo no lugar de {game}) e o ambiente do descritor. Antes, confere a copia, escreve
    os ajustes e roda o preparo. Devolve (externo, aviso) ou lanca NaoDaParaInstalar com o motivo."""
    r = recomp(recomp_id) or {"nome": recomp_id}
    pasta = pasta_do(recomp_id)
    programa = instalado(recomp_id)
    if not programa:
        raise NaoDaParaInstalar("%s ainda não foi baixado." % r["nome"])
    descritor = ler_descritor(pasta) or {}
    base = descritor.get("_pasta", pasta)
    vars_ = variaveis(base, caminho_jogo)
    aviso = ""
    argumentos = []
    ambiente = {}
    if descritor:
        erro = conferir_copia(descritor.get("game"), caminho_jogo)
        if erro:
            raise NaoDaParaInstalar(erro)
        falha = preparar(descritor, base, caminho_jogo, recomp_id, avisar)
        if falha:
            raise NaoDaParaInstalar(falha)
        try:
            escritos = escrever_configuracao(descritor, vars_)
            if escritos:
                avisar("[ARENA] Ajustes do recomp escritos: %s" % ", ".join(os.path.basename(e) for e in escritos))
        except OSError as falha_cfg:
            avisar("[ARENA] Nao consegui escrever os ajustes do recomp: %s" % falha_cfg)
        inicio = descritor.get("start") or {}
        argumentos = list(preencher(inicio.get("args") or [], vars_))
        ambiente = {k: str(v) for k, v in preencher(inicio.get("env") or {}, vars_).items()
                    if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", k) and k.upper() not in ("PATH", "LD_PRELOAD", "LD_LIBRARY_PATH")}
    else:
        aviso = ("%s não diz como receber o jogo: se ele pedir a sua cópia na primeira vez, ela está em %s."
                 % (r["nome"], caminho_jogo))
    return ({"caminho": programa,
             "dados": {"nome": r["nome"], "argumentos": argumentos, "ambiente": ambiente, "recomp": recomp_id}},
            aviso)
