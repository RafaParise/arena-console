# -*- coding: utf-8 -*-
"""
Banco de dados e estado compartilhado do ARENA.
================================================
Operacoes com o SQLite, caminhos, constantes e funcoes utilitarias
usadas por todos os outros modulos do servidor.

So biblioteca padrao do Python:
  sqlite3         -> banco de recordes
  threading       -> travas compartilhadas
  urllib.parse    -> normalizacao de URLs
"""

import contextlib
import json
import os
import sqlite3
import threading
import urllib.parse
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# BLOCO 1 - Caminhos (tudo relativo, nada preso a letra de drive)
# ---------------------------------------------------------------------------

PASTA_SERVIDOR = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(PASTA_SERVIDOR)

PASTA_LAUNCHER = os.path.join(RAIZ, "launcher")
PASTA_DADOS = os.path.join(RAIZ, "dados")
PASTA_JOGOS = os.path.join(RAIZ, "jogos")
PASTA_RETROARCH = os.path.join(RAIZ, "retroarch")
PASTA_CORES = os.path.join(PASTA_RETROARCH, "cores")
PASTA_SISTEMA = os.path.join(PASTA_RETROARCH, "system")
PASTA_SAVES = os.path.join(PASTA_RETROARCH, "saves")
PASTA_STATES = os.path.join(PASTA_RETROARCH, "states")
PASTA_CAPTURAS = os.path.join(PASTA_RETROARCH, "screenshots")
PASTA_CHEATS = os.path.join(PASTA_RETROARCH, "cheats")
PASTA_REMAPS = os.path.join(PASTA_RETROARCH, "remaps")
PASTA_CONTROLES = os.path.join(PASTA_RETROARCH, "controles")
PASTA_BACKUP = os.path.join(RAIZ, "backup")

EXECUTAVEL_RETROARCH = os.path.join(PASTA_RETROARCH, "retroarch.exe")
ARQUIVO_CONSOLES = os.path.join(PASTA_SERVIDOR, "consoles.json")
ARQUIVO_BANCO = os.path.join(PASTA_DADOS, "arena.db")
ARQUIVO_CONFIG = os.path.join(PASTA_DADOS, "config.json")
ARQUIVO_OVERRIDE = os.path.join(PASTA_DADOS, "arena_override.cfg")

PORTA = 8777

# Porta usada quando o aluno digita so o IP do servidor, sem ":porta".
PORTA_PADRAO = 8777

# ---------------------------------------------------------------------------
# Travas compartilhadas
# ---------------------------------------------------------------------------

TRAVA_BANCO = threading.Lock()
TRAVA_JOGO = threading.Lock()
TRAVA_CACHE = threading.Lock()
TRAVA_ARQUIVO = threading.Lock()

# ---------------------------------------------------------------------------
# Mapeamento de cores por familia de console
# ---------------------------------------------------------------------------

CONSOLES_CORES = {
    # Nintendo
    "nes": "#c62828", "snes": "#6a1b9a", "n64": "#4527a0",
    "gameboy": "#2e7d32", "gba": "#388e3c", "nds": "#1b5e20",
    "gamecube_wii": "#4a148c", "nintendo": "#c62828",
    # Sega
    "megadrive": "#1565c0", "mastersystem": "#0d47a1",
    "gamegear": "#00838f", "saturn": "#283593",
    "sega": "#1565c0",
    # Sony PlayStation
    "ps1": "#424242", "ps2": "#616161", "psx": "#424242",
    "playstation": "#424242",
    # Microsoft
    "xbox": "#1b5e20", "xbox360": "#2e7d32",
    "microsoft": "#1b5e20",
    # Arcade
    "arcade_mame": "#e65100", "neogeo": "#bf360c", "arcade": "#e65100",
    # Outros
    "atari": "#795548", "commodore": "#4e342e",
    "msdos": "#37474f", "msx": "#455a64",
}

# ---------------------------------------------------------------------------
# Funcoes utilitarias
# ---------------------------------------------------------------------------


def gravar_texto_atomico(caminho, texto):
    """Grava um arquivo sem deixar meio-termo, mesmo com varios pedidos juntos.

    Duas protecoes empilhadas:
      1. Nome de arquivo temporario UNICO por gravacao. Sem isso, duas
         gravacoes simultaneas disputam o mesmo temporario e a segunda
         estoura porque a primeira ja renomeou o arquivo.
      2. Uma trava, para que a ordem final seja sempre a da ultima
         gravacao - e nao a de quem terminou primeiro por acaso.

    O os.replace no final e atomico: ou o arquivo antigo continua inteiro,
    ou o novo aparece inteiro. Nunca um pedaco dos dois. E o que salva o
    pen drive retirado no meio da gravacao.
    """
    temporario = "%s.%d.tmp" % (caminho, threading.get_ident())
    with TRAVA_ARQUIVO:
        try:
            with open(temporario, "w", encoding="utf-8") as arquivo:
                arquivo.write(texto)
                arquivo.flush()
                os.fsync(arquivo.fileno())
            os.replace(temporario, caminho)
        finally:
            if os.path.exists(temporario):
                try:
                    os.remove(temporario)
                except OSError:
                    pass

# Guarda contra abrir dois jogos ao mesmo tempo. Sem isso, um duplo clique
# apressado sobe duas janelas do RetroArch disputando o mesmo controle.
JOGO_EM_ANDAMENTO = {"ativo": False, "titulo": ""}


def agora_utc():
    """Data e hora em UTC, no formato ISO, COM microssegundos.

    UTC porque os recordes viajam entre computadores com relogios e fusos
    diferentes: ordenar por hora local daria bagunca na hora de juntar.

    Os microssegundos nao sao capricho. A sincronizacao pergunta ao amigo
    "o que voce tem de novo depois deste instante". Com resolucao de
    segundo, todo registro criado no MESMO segundo da ultima troca ficava
    de fora e nunca mais era enviado. Numa sala inteira jogando ao mesmo
    tempo, isso acontece o tempo todo.
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def dentro_da_pasta(caminho, pasta):
    """Confere se o caminho esta mesmo dentro da pasta permitida.

    startswith deixaria passar '/launcher-outro'. commonpath compara pasta
    por pasta, que e o correto.
    """
    try:
        alvo = os.path.abspath(caminho)
        base = os.path.abspath(pasta)
        return os.path.commonpath([alvo, base]) == base
    except ValueError:
        return False


def normalizar_url(url):
    """Aceita '192.168.0.15', '192.168.0.15:8777' ou o endereco completo."""
    url = (url or "").strip().rstrip("/")
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    partes = urllib.parse.urlsplit(url)
    if ":" not in partes.netloc:
        url = "%s://%s:%d" % (partes.scheme, partes.netloc, PORTA_PADRAO)
    return url


# ---------------------------------------------------------------------------
# BLOCO 2 - Banco de dados
# ---------------------------------------------------------------------------
# Privacidade: guarda APELIDO, nunca nome completo. Sao dados de estudantes
# menores de idade (LGPD, art. 14).
#
# Decisao de modelagem: 'placar' e 'sessao' sao registros de evento,
# autossuficientes (carregam apelido e titulo dentro). Isso e proposital:
# um recorde precisa poder viajar sozinho de um ARENA para outro, sem
# depender de tabelas que talvez nao existam do outro lado. Cada registro
# tem um 'uuid' proprio, entao enviar o mesmo recorde duas vezes nao cria
# duplicata.

ESQUEMA = """
CREATE TABLE IF NOT EXISTS placar (
    uuid          TEXT PRIMARY KEY,
    apelido       TEXT    NOT NULL,
    jogo_id       TEXT    NOT NULL,
    jogo_titulo   TEXT    NOT NULL,
    pontos        INTEGER NOT NULL,
    registrado_em TEXT    NOT NULL,
    dispositivo   TEXT    NOT NULL,
    enviado       INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS sessao (
    uuid          TEXT PRIMARY KEY,
    apelido       TEXT    NOT NULL,
    jogo_id       TEXT    NOT NULL,
    jogo_titulo   TEXT    NOT NULL,
    inicio        TEXT    NOT NULL,
    segundos      INTEGER NOT NULL DEFAULT 0,
    encerrada     INTEGER NOT NULL DEFAULT 0,
    dispositivo   TEXT    NOT NULL,
    enviado       INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_placar_jogo   ON placar(jogo_id);
CREATE INDEX IF NOT EXISTS idx_placar_envio  ON placar(enviado);
CREATE INDEX IF NOT EXISTS idx_sessao_jogo   ON sessao(jogo_id);
CREATE INDEX IF NOT EXISTS idx_sessao_envio  ON sessao(enviado);
"""


@contextlib.contextmanager
def banco():
    """Abre a conexao, confirma a transacao e FECHA de verdade no final.

    Detalhe que causa vazamento se ignorado: 'with sqlite3.connect(...)'
    sozinho confirma a transacao mas NAO fecha a conexao.
    """
    conexao = sqlite3.connect(ARQUIVO_BANCO, timeout=15)
    conexao.row_factory = sqlite3.Row
    try:
        # WAL: leitura e escrita ao mesmo tempo sem travar uma na outra.
        # synchronous NORMAL: menos gravacoes fisicas, o que importa muito
        # quando o banco esta em pen drive.
        conexao.execute("PRAGMA journal_mode = WAL")
        conexao.execute("PRAGMA synchronous = NORMAL")
        yield conexao
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def preparar_banco():
    with banco() as conexao:
        conexao.executescript(ESQUEMA)


def fechar_banco():
    """Junta o arquivo WAL ao banco principal antes de encerrar.

    Sem isso, tirar o pen drive logo depois de fechar pode deixar recordes
    presos no arquivo temporario.
    """
    try:
        with banco() as conexao:
            conexao.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    except sqlite3.Error:
        pass


# RANK() numera as posicoes dentro de cada jogo separadamente, por causa do
# PARTITION BY. Empate recebe a mesma posicao.
SQL_RANKING_PLACAR = """
SELECT * FROM (
    SELECT  jogo_titulo   AS jogo,
            jogo_id       AS jogo_id,
            apelido       AS apelido,
            MAX(pontos)   AS pontos,
            RANK() OVER (
                PARTITION BY jogo_id
                ORDER BY MAX(pontos) DESC
            )             AS posicao
    FROM placar
    GROUP BY jogo_id, apelido
)
WHERE posicao <= 5
ORDER BY jogo, posicao;
"""

SQL_RANKING_TEMPO = """
SELECT * FROM (
    SELECT  jogo_titulo     AS jogo,
            apelido         AS apelido,
            SUM(segundos)   AS segundos,
            COUNT(*)        AS partidas,
            RANK() OVER (
                PARTITION BY jogo_id
                ORDER BY SUM(segundos) DESC
            )               AS posicao
    FROM sessao
    WHERE encerrada = 1 AND segundos > 30
    GROUP BY jogo_id, apelido
)
WHERE posicao <= 5
ORDER BY jogo, posicao;
"""


def ler_ranking():
    with banco() as conexao:
        try:
            return {
                "placar": [dict(l) for l in conexao.execute(SQL_RANKING_PLACAR)],
                "tempo": [dict(l) for l in conexao.execute(SQL_RANKING_TEMPO)],
            }
        except sqlite3.DatabaseError as falha:
            # Pode ser SQLite muito antigo (sem funcao de janela) ou banco
            # danificado por retirada do pen drive no meio de uma gravacao.
            # Nos dois casos: nao derrubar o ARENA, avisar e seguir.
            print("[ARENA] Nao consegui montar o ranking: %s" % falha)
            print("[ARENA] Se o banco estiver danificado, restaure de backup\\.")
            return {"placar": [], "tempo": [], "erro_banco": str(falha)[:120]}


# ---------------------------------------------------------------------------
# Funcoes de CRUD para sincronizacao
# ---------------------------------------------------------------------------

LIMITE_LOTE = 500


def registros_pendentes(limite=LIMITE_LOTE):
    with banco() as conexao:
        placares = [dict(l) for l in conexao.execute(
            "SELECT uuid, apelido, jogo_id, jogo_titulo, pontos, registrado_em, "
            "dispositivo FROM placar WHERE enviado = 0 LIMIT ?", (limite,))]
        sessoes = [dict(l) for l in conexao.execute(
            "SELECT uuid, apelido, jogo_id, jogo_titulo, inicio, segundos, "
            "dispositivo FROM sessao WHERE enviado = 0 AND encerrada = 1 "
            "AND segundos > 30 LIMIT ?", (limite,))]
    return placares, sessoes


def contar_pendentes():
    with banco() as conexao:
        placares = conexao.execute(
            "SELECT COUNT(*) FROM placar WHERE enviado = 0").fetchone()[0]
        sessoes = conexao.execute(
            "SELECT COUNT(*) FROM sessao WHERE enviado = 0 AND encerrada = 1 "
            "AND segundos > 30").fetchone()[0]
    return placares + sessoes


def gravar_recebidos(placares, sessoes):
    """Guarda registros vindos de outro ARENA.

    INSERT OR IGNORE com o uuid como chave primaria: reenviar o mesmo
    recorde dez vezes nao cria dez linhas. E o que torna a sincronizacao
    segura de repetir quando a rede cai no meio.
    """
    novos = 0
    with TRAVA_BANCO, banco() as conexao:
        for p in placares:
            try:
                cursor = conexao.execute(
                    "INSERT OR IGNORE INTO placar (uuid, apelido, jogo_id, "
                    "jogo_titulo, pontos, registrado_em, dispositivo, enviado) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, 1)",
                    (str(p["uuid"])[:40], str(p["apelido"])[:24],
                     str(p["jogo_id"])[:400], str(p["jogo_titulo"])[:200],
                     int(p["pontos"]), str(p["registrado_em"])[:40],
                     str(p["dispositivo"])[:40]))
                novos += cursor.rowcount
            except (KeyError, TypeError, ValueError, sqlite3.Error):
                continue
        for s in sessoes:
            try:
                cursor = conexao.execute(
                    "INSERT OR IGNORE INTO sessao (uuid, apelido, jogo_id, "
                    "jogo_titulo, inicio, segundos, encerrada, dispositivo, "
                    "enviado) VALUES (?, ?, ?, ?, ?, ?, 1, ?, 1)",
                    (str(s["uuid"])[:40], str(s["apelido"])[:24],
                     str(s["jogo_id"])[:400], str(s["jogo_titulo"])[:200],
                     str(s["inicio"])[:40], int(s["segundos"]),
                     str(s["dispositivo"])[:40]))
                novos += cursor.rowcount
            except (KeyError, TypeError, ValueError, sqlite3.Error):
                continue
    return novos


def marcar_enviados(placares, sessoes):
    with TRAVA_BANCO, banco() as conexao:
        if placares:
            conexao.executemany("UPDATE placar SET enviado = 1 WHERE uuid = ?",
                                [(p["uuid"],) for p in placares])
        if sessoes:
            conexao.executemany("UPDATE sessao SET enviado = 1 WHERE uuid = ?",
                                [(s["uuid"],) for s in sessoes])


def registros_desde(carimbo, limite=LIMITE_LOTE, exceto=None):
    """Devolve registros gravados depois de um carimbo de data.

    Usado quando OUTRO ARENA pede o que ha de novo aqui. E assim que os
    amigos veem a pontuacao e o tempo de jogo um do outro.

    Devolve tambem ate onde foi: se houver mais registros do que cabe num
    lote, a marca para a proxima vez e a data do ULTIMO registro enviado,
    nunca 'agora'. Sem esse cuidado, um aluno que voltasse de duas semanas
    de ferias mandaria os primeiros 500 recordes e perderia todo o resto
    para sempre, porque a marca teria pulado para o presente.
    """
    carimbo = str(carimbo or "")[:40]
    # Nao devolver ao amigo os registros que ele mesmo criou: ele ja tem.
    # Sem isso, a sala inteira trocava dez vezes mais dados do que precisa.
    excluir = str(exceto or "")[:40]

    with banco() as conexao:
        placares = [dict(l) for l in conexao.execute(
            "SELECT uuid, apelido, jogo_id, jogo_titulo, pontos, registrado_em, "
            "dispositivo FROM placar WHERE registrado_em > ? AND dispositivo <> ? "
            "ORDER BY registrado_em LIMIT ?", (carimbo, excluir, limite))]
        sessoes = [dict(l) for l in conexao.execute(
            "SELECT uuid, apelido, jogo_id, jogo_titulo, inicio, segundos, "
            "dispositivo FROM sessao WHERE encerrada = 1 AND segundos > 30 "
            "AND inicio > ? AND dispositivo <> ? "
            "ORDER BY inicio LIMIT ?", (carimbo, excluir, limite))]

    lotado = len(placares) >= limite or len(sessoes) >= limite
    if lotado:
        # Avanca so ate o mais antigo dos dois ultimos, para nao pular nada.
        marcas = []
        if len(placares) >= limite:
            marcas.append(placares[-1]["registrado_em"])
        if len(sessoes) >= limite:
            marcas.append(sessoes[-1]["inicio"])
        ate = min(marcas)
    else:
        ate = agora_utc()

    return placares, sessoes, ate
