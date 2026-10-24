# -*- coding: utf-8 -*-
r"""
ARENA - o armazenamento do celular: a memoria interna e o cartao SD, juntos.

Pedido do Rafael (23/10/2026): "o ARENA no android deve ser capaz de armazenar
jogos tanto na memoria interna como no cartao SD, e ele deve ser capaz de
gerenciar isso perfeitamente para telefones que quase sempre estao com
armazenamento interno cheio [...] eu ter o arena instalado no armazenamento
interno e poder jogar jogos salvos no cartao sd".

O QUE FICA ONDE (como o app ja era e continua):
  - o programa, o banco de dados (dados\), a configuracao do RetroArch, os
    atalhos e o cache: na pasta PRIVADA do app, no armazenamento interno (rapido
    e que nunca some);
  - a "pasta do ARENA" (BIOS, saves, estados) e os jogos de sempre: onde a
    pessoa escolheu (a memoria do aparelho, em Armazenamento interno > ARENA);
  - os jogos que moram no CARTAO: uma pasta com a mesma arrumacao de
    jogos\pessoais (uma pasta por console) no cartao, que o ARENA liga como uma
    ORIGEM a mais (cartao-<volume>), ao lado de "Meus jogos".

COMO O CARTAO ENTRA NA LISTA: dentro de RAIZ\jogos (uma pasta de verdade, no
app) ha um atalho por origem: livres, turma, pessoais e, agora, um por pasta de
jogos do cartao (cartao-1234-5678...). O indexador varre cada origem; o
caminho do jogo continua relativo a RAIZ (jogos\cartao-1234-5678\PS1\...), e tudo
o que ja funcionava (abrir, mover, capas, saves) segue funcionando. O que a
pessoa escolheu fica em dados\armazenamento.json (nunca em arquivo de jogo).

NUNCA apaga, nunca move e nunca grava nada no cartao: tirar uma pasta da lista
so desfaz o atalho. Gravar no cartao so acontece quando o aluno manda mover um
jogo (e la o proprio fluxo copia, confere e so entao tira o original).

Medidas feitas no Galaxy A12 (leitura sequencial de 256 MB): cartao 59 MB/s,
interno 106 MB/s: jogo de disco roda direto do cartao; a copia para o interno
(cache) e' uma escolha, como no Lemuroid (que copia o jogo para o cache interno
ao jogar, com limite escolhido e limpeza do mais antigo).
"""
import json
import os
import re
import threading
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
PASTA_DADOS = os.path.join(RAIZ, "dados")
ARQUIVO_DE_CONSOLES = os.path.join(AQUI, "consoles.json")
PREFIXO = "cartao-"
LIMITE_DE_PASTAS = 8
JOGAR_DO_CARTAO = ("direto", "copiar")
TRAVA = threading.Lock()

# Pastas de volume que nunca tem jogo do aluno (dados de outros apps, fotos, musica...). O que
# conta e' o NOME da pasta: a busca nunca abre arquivo.
PASTAS_QUE_NAO_SE_ABRE = {"android", "lost.dir", "dcim", "pictures", "movies", "music", "notifications",
                          "ringtones", "alarms", "podcasts", "audiobooks", "recordings", "documents/.thumbnails",
                          "system volume information", "$recycle.bin", ".trash", "whatsapp", "telegram",
                          "miui", "samsung", "bluetooth", "screenshots", "snapchat"}


def arquivo_de_configuracao():
    return os.path.join(PASTA_DADOS, "armazenamento.json")


def _raizes(raizes=None):
    """As raizes dos volumes (a primeira e' a memoria do aparelho)."""
    if raizes is not None:
        return list(raizes)
    import ponte_android
    return list(ponte_android.RAIZES)


# ---------------------------------------------------------------------------
# Os volumes
# ---------------------------------------------------------------------------

def id_do_volume(raiz, indice):
    """"interno" para a memoria do aparelho; "cartao-1234-5678" para o resto."""
    if indice == 0:
        return "interno"
    nome = re.sub(r"[^a-z0-9]+", "-", os.path.basename(os.path.normpath(raiz)).lower()).strip("-")
    return PREFIXO + (nome or str(indice))


def volumes(raizes=None, nomes=None):
    """[{id, nome, caminho, removivel, montado, total_mb, livre_mb, usado_pct}] de cada volume.
    'nomes': {caminho: nome que o Android da} (o app sabe o nome que a pessoa deu ao cartao)."""
    nomes = nomes or {}
    saida = []
    for indice, raiz in enumerate(_raizes(raizes)):
        info = {"id": id_do_volume(raiz, indice), "caminho": raiz, "removivel": indice > 0,
                "nome": nomes.get(raiz) or ("Armazenamento interno" if indice == 0 else
                                            "Cartão de memória (%s)" % os.path.basename(os.path.normpath(raiz))),
                "montado": os.path.isdir(raiz), "total_mb": 0, "livre_mb": 0, "usado_pct": 0}
        if info["montado"]:
            try:
                uso = os.statvfs(raiz) if hasattr(os, "statvfs") else None
                if uso:
                    total, livre = uso.f_blocks * uso.f_frsize, uso.f_bavail * uso.f_frsize
                else:
                    import shutil
                    resumo = shutil.disk_usage(raiz)
                    total, livre = resumo.total, resumo.free
                info["total_mb"], info["livre_mb"] = int(total / 1048576), int(livre / 1048576)
                info["usado_pct"] = round(100.0 * (total - livre) / total) if total else 0
            except OSError:
                info["montado"] = False
        saida.append(info)
    return saida


def volume_da_pasta(caminho, raizes=None):
    """O indice do volume a que a pasta pertence (pelo caminho de verdade), ou None."""
    real = os.path.realpath(caminho)
    for indice, raiz in enumerate(_raizes(raizes)):
        base = os.path.realpath(raiz)
        if real == base or real.startswith(base + os.sep):
            return indice
    return None


# ---------------------------------------------------------------------------
# O que a pessoa escolheu (dados\armazenamento.json)
# ---------------------------------------------------------------------------

PADRAO = {"jogos_extras": [], "jogar_do_cartao": "direto", "limite_do_cache_mb": 2048}


def _limpar(dados):
    """Dados lidos do arquivo, so com o que vale (o arquivo e' texto de fora)."""
    saida = {"jogos_extras": [], "jogar_do_cartao": PADRAO["jogar_do_cartao"],
             "limite_do_cache_mb": PADRAO["limite_do_cache_mb"]}
    if not isinstance(dados, dict):
        return saida
    lista = dados.get("jogos_extras")
    for item in (lista if isinstance(lista, list) else [])[:LIMITE_DE_PASTAS]:
        if not isinstance(item, dict):
            continue
        identificador, caminho = str(item.get("id") or ""), str(item.get("caminho") or "")
        if not re.fullmatch(PREFIXO + r"[a-z0-9-]{1,40}", identificador) or not caminho or "\x00" in caminho \
                or len(caminho) > 500 or any(e["id"] == identificador for e in saida["jogos_extras"]):
            continue
        nome = re.sub(r"[\x00-\x1f]", "", str(item.get("nome") or "Cartão de memória"))[:40].strip()
        saida["jogos_extras"].append({"id": identificador, "nome": nome or "Cartão de memória", "caminho": caminho})
    if dados.get("jogar_do_cartao") in JOGAR_DO_CARTAO:
        saida["jogar_do_cartao"] = dados["jogar_do_cartao"]
    try:
        limite = int(dados.get("limite_do_cache_mb"))
    except (TypeError, ValueError):
        limite = 0
    if 256 <= limite <= 65536:
        saida["limite_do_cache_mb"] = limite
    return saida


def ler():
    try:
        with open(arquivo_de_configuracao(), encoding="utf-8") as arquivo:
            return _limpar(json.load(arquivo))
    except (OSError, ValueError):
        return _limpar({})


def gravar(dados):
    """Grava de forma atomica (arquivo temporario e troca), como o resto do ARENA."""
    dados = _limpar(dados)
    destino = arquivo_de_configuracao()
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    temporario = "%s.%d.%d.tmp" % (destino, os.getpid(), threading.get_ident())
    with open(temporario, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=1)
        arquivo.write("\n")
    for tentativa in range(20):
        try:
            os.replace(temporario, destino)
            return dados
        except PermissionError:      # no Windows, outra linha esta lendo o arquivo: espera um pouco
            time.sleep(0.05)
    os.replace(temporario, destino)
    return dados


# ---------------------------------------------------------------------------
# As pastas de jogos do cartao
# ---------------------------------------------------------------------------

def nomes_de_pastas_de_console():
    """Os nomes (minusculos) das pastas de console do ARENA (consoles.json)."""
    try:
        with open(ARQUIVO_DE_CONSOLES, encoding="utf-8") as arquivo:
            plataformas = json.load(arquivo).get("plataformas", [])
    except (OSError, ValueError):
        return set()
    nomes = set()
    for plataforma in plataformas:
        pasta = str(plataforma.get("pasta") or "")
        if pasta:
            nomes.add(re.split(r"[\\/]", pasta)[-1].lower())
    return nomes


def _consoles_dentro(pasta, consoles):
    """Quantas subpastas desta pasta tem nome de console do ARENA."""
    try:
        with os.scandir(pasta) as itens:
            return sum(1 for item in itens if item.is_dir() and item.name.lower() in consoles)
    except OSError:
        return 0


def validar_pasta_de_jogos(caminho, raizes=None, consoles=None, proprias=None):
    """(caminho de verdade, None) se a pasta serve como pasta de jogos do cartao;
    (None, "o que fazer") se nao. 'proprias': as pastas de jogos do proprio ARENA
    (para nao listar de novo o que ja esta em Meus jogos)."""
    if not isinstance(caminho, str) or not caminho.strip() or "\x00" in caminho:
        return None, "Escolha uma pasta de jogos da lista."
    caminho = os.path.abspath(os.path.normpath(caminho.strip()))
    if not os.path.isdir(caminho):
        return None, "Essa pasta não está no aparelho agora. Confira se o cartão está encaixado e escolha de novo."
    real = os.path.realpath(caminho)
    lista = _raizes(raizes)
    indice = volume_da_pasta(real, lista)
    if indice is None:
        return None, "Escolha uma pasta que esteja na memória do aparelho ou no cartão de memória."
    base = os.path.realpath(lista[indice])
    if real == base:
        return None, "Escolha a pasta dos jogos dentro do cartão, e não o cartão inteiro."
    relativo = os.path.relpath(real, base).split(os.sep)
    if relativo[0].lower() == "android":
        return None, "Essa pasta é de dados de outros aplicativos. Escolha a pasta onde você guardou os jogos."
    for propria in (proprias or []):
        propria = os.path.realpath(propria)
        if real == propria or real.startswith(propria + os.sep) or propria.startswith(real + os.sep):
            return None, "Essa pasta já é a de Meus jogos do ARENA. Escolha uma do cartão."
    consoles = nomes_de_pastas_de_console() if consoles is None else consoles
    if _consoles_dentro(real, consoles) < 1:
        return None, ("Essa pasta não tem nenhuma pasta de console do ARENA dentro (Super Nintendo, PS1, "
                      "Dreamcast...). Escolha a pasta de cima: a que tem as pastas dos consoles dentro.")
    return real, None


def adicionar(caminho, raizes=None, nome=None, consoles=None, proprias=None):
    """Poe a pasta de jogos do cartao na lista. (dados, None) ou (None, "o que fazer")."""
    real, erro = validar_pasta_de_jogos(caminho, raizes, consoles, proprias)
    if erro:
        return None, erro
    with TRAVA:
        dados = ler()
        if any(os.path.realpath(e["caminho"]) == real for e in dados["jogos_extras"]):
            return None, "Essa pasta já está na lista. Escolha outra."
        if len(dados["jogos_extras"]) >= LIMITE_DE_PASTAS:
            return None, "A lista já tem %d pastas. Tire uma antes de pôr outra." % LIMITE_DE_PASTAS
        lista = _raizes(raizes)
        indice = volume_da_pasta(real, lista)
        if indice is None:       # (o validar_pasta_de_jogos ja conferiu; so por seguranca)
            return None, "Escolha uma pasta que esteja na memória do aparelho ou no cartão de memória."
        base = id_do_volume(lista[indice], indice)
        usados = {e["id"] for e in dados["jogos_extras"]}
        identificador, numero = base, 2
        while identificador in usados:
            identificador, numero = "%s-%d" % (base, numero), numero + 1
        dados["jogos_extras"].append({"id": identificador, "nome": (nome or "Cartão de memória")[:40],
                                      "caminho": real})
        return gravar(dados), None


def remover(identificador):
    """Tira a pasta da lista (so desfaz o atalho: nenhum jogo e' tocado)."""
    with TRAVA:
        dados = ler()
        antes = len(dados["jogos_extras"])
        dados["jogos_extras"] = [e for e in dados["jogos_extras"] if e["id"] != identificador]
        if len(dados["jogos_extras"]) == antes:
            return None, "Essa pasta não está na lista."
        return gravar(dados), None


def definir_jogo_do_cartao(modo=None, limite_mb=None):
    with TRAVA:
        dados = ler()
        if modo in JOGAR_DO_CARTAO:
            dados["jogar_do_cartao"] = modo
        if limite_mb is not None:
            try:
                limite = int(limite_mb)
            except (TypeError, ValueError):
                return None, "Escolha um tamanho de cache entre 256 MB e 64 GB."
            if not 256 <= limite <= 65536:
                return None, "Escolha um tamanho de cache entre 256 MB e 64 GB."
            dados["limite_do_cache_mb"] = limite
        return gravar(dados), None


def rotulos_das_origens(extras=None):
    """{id da origem: o nome que a tela mostra} para juntar ao indexador.ORIGENS."""
    extras = ler()["jogos_extras"] if extras is None else extras
    return {e["id"]: e["nome"] for e in extras}


def ligar_extras(pasta_dos_jogos, extras=None):
    """Poe, dentro de RAIZ\\jogos, um atalho por pasta de jogos do cartao e tira os atalhos de
    cartao que nao estao mais na lista. So mexe em atalho com o prefixo cartao-: nunca em
    pasta de verdade, nunca em jogo. Devolve {id: situacao} (ligado, ausente, ja_estava, erro)."""
    extras = ler()["jogos_extras"] if extras is None else extras
    situacao = {}
    ids = {e["id"] for e in extras}
    try:
        nomes = os.listdir(pasta_dos_jogos)
    except OSError:
        return situacao
    for nome in nomes:
        caminho = os.path.join(pasta_dos_jogos, nome)
        if nome.startswith(PREFIXO) and nome not in ids and os.path.islink(caminho):
            try:
                os.remove(caminho)            # so o atalho
            except OSError:
                pass
    for extra in extras:
        atalho = os.path.join(pasta_dos_jogos, extra["id"])
        if not os.path.isdir(extra["caminho"]):
            # o cartao nao esta no aparelho agora: o atalho que sobrou apontaria para o nada
            if os.path.islink(atalho):
                try:
                    os.remove(atalho)
                except OSError:
                    pass
            situacao[extra["id"]] = "ausente"
            continue
        try:
            if os.path.islink(atalho):
                if os.path.realpath(atalho) == os.path.realpath(extra["caminho"]):
                    situacao[extra["id"]] = "ja_estava"
                    continue
                os.remove(atalho)
            elif os.path.lexists(atalho):
                situacao[extra["id"]] = "erro: ja existe uma pasta de verdade com esse nome"
                continue
            os.symlink(extra["caminho"], atalho, target_is_directory=True)
            situacao[extra["id"]] = "ligado"
        except (OSError, NotImplementedError) as falha:
            situacao[extra["id"]] = "erro: %s" % (getattr(falha, "strerror", None) or falha)
    return situacao


# ---------------------------------------------------------------------------
# Procurar pastas de jogos num volume (so olha nomes de pasta, nunca abre arquivo)
# ---------------------------------------------------------------------------

def procurar_pastas_de_jogos(raiz, consoles=None, limite_s=8.0, profundidade=5, relogio=time.monotonic):
    """{candidatas: [{caminho, consoles, onde}], completo, pastas_vistas}: as pastas do volume com
    pelo menos 2 pastas de console do ARENA dentro. Para no tempo limite (completo=False)."""
    consoles = nomes_de_pastas_de_console() if consoles is None else consoles
    inicio = relogio()
    fila = [(raiz, 0)]
    candidatas, vistas, completo = [], 0, True
    while fila:
        if relogio() - inicio > limite_s:
            completo = False
            break
        atual, nivel = fila.pop(0)
        vistas += 1
        achados = _consoles_dentro(atual, consoles)
        if achados >= 2:
            relativo = os.path.relpath(atual, raiz)
            candidatas.append({"caminho": atual, "consoles": achados,
                               "onde": " › ".join(p for p in relativo.split(os.sep) if p and p != ".")})
            continue
        if nivel >= profundidade:
            continue
        try:
            with os.scandir(atual) as itens:
                filhas = sorted(i.name for i in itens if i.is_dir(follow_symlinks=False))
        except OSError:
            continue
        for nome in filhas:
            if nome.startswith(".") or nome.lower() in PASTAS_QUE_NAO_SE_ABRE:
                continue
            fila.append((os.path.join(atual, nome), nivel + 1))
    candidatas.sort(key=lambda c: (-c["consoles"], c["onde"].lower()))
    return {"candidatas": candidatas[:12], "completo": completo, "pastas_vistas": vistas}


# ---------------------------------------------------------------------------
# Medir a velocidade (para o painel e para a escolha de jogar direto ou pelo interno)
# ---------------------------------------------------------------------------

def maior_arquivo(pasta, minimo_mb=64, profundidade=3):
    """O maior arquivo (>= minimo_mb) das primeiras pastas, ou None. Serve para medir a leitura do
    cartao sem gravar nada nele."""
    melhor, tamanho_melhor = None, minimo_mb * 1048576 - 1
    pilha = [(pasta, 0)]
    while pilha:
        atual, nivel = pilha.pop()
        try:
            with os.scandir(atual) as itens:
                for item in itens:
                    if item.is_file(follow_symlinks=False):
                        tamanho = item.stat().st_size
                        if tamanho > tamanho_melhor:
                            melhor, tamanho_melhor = item.path, tamanho
                    elif item.is_dir(follow_symlinks=False) and nivel < profundidade:
                        pilha.append((item.path, nivel + 1))
        except OSError:
            continue
    return melhor


def medir_leitura(arquivo, mb=32, limite_s=10.0, relogio=time.monotonic):
    """MB/s lendo 'mb' MB do MEIO de um arquivo (longe do comeco, que o sistema ja pode ter guardado)."""
    tamanho = os.path.getsize(arquivo)
    quantos = min(mb * 1048576, tamanho)
    if quantos <= 0:
        return None
    with open(arquivo, "rb", buffering=0) as f:
        f.seek(max(0, (tamanho - quantos) // 2))
        inicio, lidos = relogio(), 0
        while lidos < quantos and relogio() - inicio < limite_s:
            bloco = f.read(min(1048576, quantos - lidos))
            if not bloco:
                break
            lidos += len(bloco)
        gasto = max(relogio() - inicio, 1e-6)
    return round(lidos / 1048576.0 / gasto, 1)


def medir_gravacao_e_leitura(pasta, mb=16, relogio=time.monotonic):
    """{gravacao_mb_s, leitura_mb_s} de uma pasta nossa (a pasta do app, no interno): grava um
    arquivo temporario, confirma no disco, le de volta e apaga o temporario."""
    arquivo = os.path.join(pasta, "arena-medida-%d.tmp" % os.getpid())
    bloco = os.urandom(1048576)
    try:
        inicio = relogio()
        with open(arquivo, "wb") as f:
            for _ in range(mb):
                f.write(bloco)
            f.flush()
            os.fsync(f.fileno())
        gravacao = mb / max(relogio() - inicio, 1e-6)
        if hasattr(os, "posix_fadvise"):
            try:
                descritor = os.open(arquivo, os.O_RDONLY)
                try:
                    os.posix_fadvise(descritor, 0, 0, os.POSIX_FADV_DONTNEED)   # esquece o que o sistema guardou
                finally:
                    os.close(descritor)
            except OSError:
                pass
        inicio = relogio()
        with open(arquivo, "rb", buffering=0) as f:
            while f.read(1048576):
                pass
        leitura = mb / max(relogio() - inicio, 1e-6)
        return {"gravacao_mb_s": round(gravacao, 1), "leitura_mb_s": round(leitura, 1)}
    finally:
        try:
            os.remove(arquivo)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# O que a tela mostra
# ---------------------------------------------------------------------------

def estado(raizes=None, nomes=None, consoles=None):
    """Tudo o que o painel Armazenamento precisa."""
    dados = ler()
    consoles = nomes_de_pastas_de_console() if consoles is None else consoles
    extras = []
    for extra in dados["jogos_extras"]:
        existe = os.path.isdir(extra["caminho"])
        indice = volume_da_pasta(extra["caminho"], raizes) if existe else None
        extras.append({"id": extra["id"], "nome": extra["nome"], "caminho": extra["caminho"], "existe": existe,
                       "consoles": _consoles_dentro(extra["caminho"], consoles) if existe else 0,
                       "volume": id_do_volume(_raizes(raizes)[indice], indice) if indice is not None else ""})
    return {"volumes": volumes(raizes, nomes), "extras": extras, "jogar_do_cartao": dados["jogar_do_cartao"],
            "limite_do_cache_mb": dados["limite_do_cache_mb"]}
