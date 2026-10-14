# -*- coding: utf-8 -*-
"""
ARENA - Servidor local
======================
Entrega a interface do launcher, a API que ela consome e a sincronizacao de
recordes entre os ARENAs da turma.

So biblioteca padrao do Python:
  http.server     -> servidor web
  sqlite3         -> banco de recordes
  json            -> troca de dados
  subprocess      -> execucao do RetroArch
  urllib.request  -> envio dos recordes ao servidor da sala
  ctypes          -> RAM, driver de video e tipo de disco no Windows

Nenhum 'pip install'. Nenhuma conexao com a internet.
"""

import base64
import binascii
import contextlib
import errno
import hashlib
import ipaddress
import json
import os
import shutil
import socket
import sqlite3
import stat
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# A janela preta nunca pode derrubar o servidor. Achado de 01/10/2026
# (testes\teste_quebrar_api.py): com a saida redirecionada para arquivo --
# o COLETAR.bat faz isso -- o Windows usa a pagina de codigo antiga
# (cp1252), e um print com emoji ou japones (apelido de colega, nome de
# jogo, pedido de fora) dava erro DENTRO do tratamento de erro: o pedido
# ficava sem resposta. Agora o caractere que nao cabe vira "?" e segue.
for _saida in (sys.stdout, sys.stderr):
    try:
        _saida.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass

# ---------------------------------------------------------------------------
# BLOCO 1 - Caminhos (tudo relativo, nada preso a letra de drive)
# ---------------------------------------------------------------------------

PASTA_SERVIDOR = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(PASTA_SERVIDOR)

# Garante que 'import indexador' funcione mesmo se o ARENA for chamado a
# partir de outra pasta de trabalho.
if PASTA_SERVIDOR not in sys.path:
    sys.path.insert(0, PASTA_SERVIDOR)

import cheats      # noqa: E402
import controles   # noqa: E402
import acervo      # noqa: E402
import barreiras   # noqa: E402  (o que deixa o computador lento -- auditoria 2)
import internet_archive  # noqa: E402
import capas_online     # noqa: E402
import graficos    # noqa: E402
import hardware    # noqa: E402
import indexador   # noqa: E402  (precisam vir depois do ajuste de sys.path)
import integridade  # noqa: E402  (zip de fliperama danificado)
import jogadores   # noqa: E402  (quantos jogadores cada jogo aceita)
import processos   # noqa: E402  (prioridade e economia de energia -- 30/09/2026)
import janela_preta  # noqa: E402  (servidor que caia ou travava -- 02/10/2026)
import como_colocar  # noqa: E402  (como colocar os jogos de cada console -- 02/10/2026)
import motivo_do_erro  # noqa: E402  (por que o jogo nao abriu, pelo registro -- 02/10/2026)
import bios        # noqa: E402  (nome, pasta e versao certa de cada BIOS -- 03/10/2026)
import arrumar     # noqa: E402  (o botao Arrumar: o arquivo do jogo no lugar certo -- 03/10/2026)
import ponte_sem_acento  # noqa: E402  (nucleo que nao abre pasta com acento: o Hatari -- 14/10/2026)

PASTA_LAUNCHER = os.path.join(RAIZ, "launcher")
PASTA_DADOS = os.path.join(RAIZ, "dados")
PASTA_PERFIL = os.path.join(PASTA_DADOS, "perfil")
PASTA_JOGOS = os.path.join(RAIZ, "jogos")
PASTA_RETROARCH = os.path.join(RAIZ, "retroarch")
PASTA_MINIATURAS = os.path.join(PASTA_RETROARCH, "thumbnails")
PASTA_CORES = os.path.join(PASTA_RETROARCH, "cores")
PASTA_SISTEMA = os.path.join(PASTA_RETROARCH, "system")
PASTA_SAVES = os.path.join(PASTA_RETROARCH, "saves")
PASTA_STATES = os.path.join(PASTA_RETROARCH, "states")
PASTA_CAPTURAS = os.path.join(PASTA_RETROARCH, "screenshots")
PASTA_CHEATS = os.path.join(PASTA_RETROARCH, "cheats")
PASTA_REMAPS = os.path.join(PASTA_RETROARCH, "remaps")
PASTA_REMAP_PARTIDA = os.path.join(RAIZ, "dados", "remap_partida")
PASTA_CONTROLES = os.path.join(PASTA_RETROARCH, "controles")
# Os ~380 perfis prontos que vem com o RetroArch (Xbox, DualShock 3/4,
# DualSense, fliperamas, 8BitDo, genericos...). O RetroArch so procura em
# UMA pasta: apontar para "controles" (vazia) escondia todos, e controle
# que nao fosse do formato Xbox podia ficar com os botoes trocados.
PASTA_PERFIS_CONTROLE = os.path.join(PASTA_RETROARCH, "autoconfig")
PASTA_CACHE = os.path.join(PASTA_RETROARCH, "cache")
PASTA_BACKUP = os.path.join(RAIZ, "backup")

EXECUTAVEL_RETROARCH = os.path.join(PASTA_RETROARCH, "retroarch.exe")
ARQUIVO_CONSOLES = os.path.join(PASTA_SERVIDOR, "consoles.json")
ARQUIVO_BANCO = os.path.join(PASTA_DADOS, "arena.db")
ARQUIVO_CONFIG = os.path.join(PASTA_DADOS, "config.json")
ARQUIVO_OVERRIDE = os.path.join(PASTA_DADOS, "arena_override.cfg")

# Carimbo desta versao. Aparece na janela preta e no topo da tela.
# Serve para uma coisa so: acabar com a duvida de "sera que estou testando
# a versao corrigida?". Quando algo nao bate com o esperado, o primeiro
# passo e comparar este numero.
VERSAO = "2026.10.11"   # auditoria 3: matriz de jogos, cheats que funcionam, portabilidade, acessibilidade

PORTA = 8777

# Porta usada quando o aluno digita so o IP do servidor, sem ":porta".
PORTA_PADRAO = 8777

TRAVA_BANCO = threading.Lock()
TRAVA_JOGO = threading.Lock()
TRAVA_CACHE = threading.Lock()
TRAVA_ARQUIVO = threading.Lock()


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
            # No Windows, o proprio os.replace() pode falhar com "Acesso
            # negado" quando outra thread tem o arquivo destino aberto
            # so para LEITURA no instante exato da troca (carregar_config()
            # e outras leituras nao usam esta trava, so os gravadores usam
            # -- de proposito, senao toda leitura esperaria toda escrita).
            # Achado real na auditoria, testando 50 pedidos simultaneos:
            # a leitura solta por uma fracao de segundo é o suficiente pro
            # Windows recusar a troca. E transitorio -- tentar de novo
            # poucas vezes resolve, sem precisar travar as leituras.
            for tentativa in range(5):
                try:
                    os.replace(temporario, caminho)
                    break
                except PermissionError:
                    if tentativa == 4:
                        raise
                    time.sleep(0.05)
        finally:
            if os.path.exists(temporario):
                try:
                    os.remove(temporario)
                except OSError:
                    pass

# Guarda contra abrir dois jogos ao mesmo tempo. Sem isso, um duplo clique
# apressado sobe duas janelas do RetroArch disputando o mesmo controle.
JOGO_EM_ANDAMENTO = {"ativo": False, "titulo": "", "id": ""}
# Os codigos do jogo aberto nao mudam pela tela: ao fechar o jogo, o
# RetroArch grava por cima do .cht a lista que ele carregou (registro dele:
# "Save game-specific cheatfile"), e a mudanca feita no meio se perderia.
MENSAGEM_CHEAT_COM_JOGO_ABERTO = (
    "Este jogo está aberto agora. Feche o jogo (F10) antes de mudar os códigos dele: quando o jogo "
    "fecha, o RetroArch grava por cima a lista de códigos que ele tem aberta, e a sua mudança se "
    "perderia.")

# A partida que ESTE computador esta hospedando agora (ou None). E' o que
# faz o amigo ver "Fulano - partida aberta: Super Bomberman 4" na lista de
# Entrar na partida. Vai no grito da descoberta (UDP) e na resposta de
# /api/sinc/ola (TCP, o mesmo caminho dos recordes), e some quando o jogo
# fecha. Bug relatado em 30/09/2026: a tela ja filtrava por
# "partida_aberta", mas o servidor nunca mandava esse campo -- a lista do
# convidado ficava sempre vazia e ninguem conseguia entrar pela tela.
PARTIDA_ABERTA = {"partida": None}


def partida_aberta_agora():
    """Copia da partida hospedada agora, ou None."""
    with TRAVA_JOGO:
        atual = PARTIDA_ABERTA["partida"]
        return dict(atual) if atual else None


# Partida esperando o jogador 2 (pedido do Rafael, 14/10/2026): quem abre a
# partida nao abre o jogo na hora. O ARENA guarda tudo pronto aqui e abre
# quando o amigo chega (POST /api/partida/cheguei, vindo do ARENA dele) ou
# quando o anfitriao clica em "Comecar sem esperar". Assim os dois comecam
# juntos, em vez de o amigo cair no meio do jogo. Sem ninguem em 15 minutos,
# a espera se desfaz sozinha (a janela pode ter sido fechada).
PARTIDA_PENDENTE = {"args": None, "convidado": "", "vez": 0}
ESPERA_MAXIMA = 15 * 60


def esperar_o_amigo(argumentos):
    """Guarda a partida pronta (os argumentos de executar_jogo) e arma o
    relogio da espera maxima."""
    with TRAVA_JOGO:
        PARTIDA_PENDENTE["args"] = argumentos
        PARTIDA_PENDENTE["convidado"] = ""
        PARTIDA_PENDENTE["vez"] += 1
        vez = PARTIDA_PENDENTE["vez"]
    relogio = threading.Timer(ESPERA_MAXIMA, cancelar_partida_pendente, args=(vez,))
    relogio.daemon = True
    relogio.start()


def comecar_partida_pendente(convidado=""):
    """Abre o jogo que esperava o amigo. False se nao havia espera."""
    with TRAVA_JOGO:
        argumentos = PARTIDA_PENDENTE["args"]
        if not argumentos:
            return False
        PARTIDA_PENDENTE["args"] = None
        PARTIDA_PENDENTE["convidado"] = convidado
        if PARTIDA_ABERTA["partida"]:
            PARTIDA_ABERTA["partida"]["esperando"] = False
            PARTIDA_ABERTA["partida"]["convidado"] = convidado
    threading.Thread(target=executar_jogo, args=argumentos, daemon=True).start()
    return True


def cancelar_partida_pendente(vez=None):
    """Desfaz a espera (botao Cancelar, ou o tempo acabou). 'vez': so
    cancela se ainda for a MESMA espera -- o relogio de uma espera antiga
    nao derruba uma nova. True se cancelou."""
    with TRAVA_JOGO:
        if not PARTIDA_PENDENTE["args"] or (vez is not None and vez != PARTIDA_PENDENTE["vez"]):
            return False
        PARTIDA_PENDENTE["args"] = None
        PARTIDA_ABERTA["partida"] = None
        JOGO_EM_ANDAMENTO["ativo"] = False
        JOGO_EM_ANDAMENTO["titulo"] = ""
    return True


def estado_da_partida():
    """Para a janela "Esperando o jogador 2" de quem abriu a partida."""
    with TRAVA_JOGO:
        aberta = PARTIDA_ABERTA["partida"] or {}
        esperando = bool(PARTIDA_PENDENTE["args"])
        return {"esperando": esperando,
                "convidado": PARTIDA_PENDENTE["convidado"],
                "jogo": aberta.get("jogo", ""),
                "aberto": bool(JOGO_EM_ANDAMENTO["ativo"]) and not esperando}


def chegar_na_partida(anfitriao, apelido, porta=None, limite=25.0):
    """Quem ENTRA avisa o ARENA de quem abriu a partida ("cheguei"). Se ele
    estava esperando, espera a porta da partida dele abrir antes de abrir o
    proprio RetroArch -- senao o --connect bateria numa porta fechada.
    Anfitriao de versao antiga ou fora do ar: segue como antes, sem esperar.
    Nunca levanta erro: o outro computador pode responder qualquer coisa
    (revisao de seguranca, 14/10/2026), e quem entra so perde a espera.
    Devolve True se o anfitriao estava esperando."""
    porta = porta or graficos.PORTA_PARTIDA
    try:
        ip = urllib.parse.urlsplit(anfitriao).hostname
        corpo = json.dumps({"apelido": (apelido or "")[:24]}).encode("utf-8")
        pedido = urllib.request.Request(anfitriao.rstrip("/") + "/api/partida/cheguei", data=corpo,
                                        headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(pedido, timeout=3) as resposta:
            dados = json.loads(resposta.read(4096) or b"{}")   # a resposta certa e' curta
    except Exception:
        return False
    if not ip or not isinstance(dados, dict) or dados.get("abrindo") is not True:
        return False
    fim = time.monotonic() + limite
    while time.monotonic() < fim:
        try:
            with socket.create_connection((ip, porta), timeout=1.0):
                pass
        except (OSError, ValueError):
            time.sleep(0.5)
            continue
        # A porta abriu: o RetroArch dele ja carregou o jogo. Um respiro e vai.
        time.sleep(1.0)
        break
    return True


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


_ESQUEMA_CONFERIDO = {}


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
        # Na primeira conexao do processo, garante o esquema atual (coluna
        # 'seq' e tabela 'contador'), por qualquer caminho que chegue aqui --
        # nao so pela abertura normal (preparar_banco).
        if _ESQUEMA_CONFERIDO.get(ARQUIVO_BANCO) is not True:
            _ESQUEMA_CONFERIDO[ARQUIVO_BANCO] = True
            aplicar_esquema(conexao)
        yield conexao
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def aplicar_esquema(conexao):
    """Cria as tabelas e acrescenta o que faltar num banco antigo.

    'seq' = ordem de chegada NESTE computador (1, 2, 3...). E' por ela que a
    sincronizacao sabe o que ja mandou para cada colega -- e nao pela data.
    Achado real (revisao pos-auditoria, testes\\teste_sinc_sem_relogio.py):
    com a data como marca, (1) notebook com o relogio errado tinha os
    recordes invisiveis para sempre, e (2) partida mais longa que o
    intervalo do vigia nunca era enviada, porque a sessao nasce no comeco e
    so fecha no fim. Numero de chegada nao depende de relogio nenhum.

    Banco antigo (sem 'seq'): a coluna entra e os registros que ja existiam
    recebem numero na ordem em que foram gravados. Nada e' apagado.
    """
    conexao.executescript(ESQUEMA)
    conexao.execute("CREATE TABLE IF NOT EXISTS contador ("
                    "nome TEXT PRIMARY KEY, valor INTEGER NOT NULL)")
    for tabela in ("placar", "sessao"):
        colunas = {c["name"] for c in conexao.execute("PRAGMA table_info(%s)" % tabela)}
        if "seq" not in colunas:
            conexao.execute("ALTER TABLE %s ADD COLUMN seq INTEGER" % tabela)
    if conexao.execute("SELECT 1 FROM contador WHERE nome = 'sinc'").fetchone() is None:
        conexao.execute("UPDATE placar SET seq = rowid WHERE seq IS NULL")
        deslocamento = conexao.execute("SELECT COALESCE(MAX(seq), 0) FROM placar").fetchone()[0]
        conexao.execute("UPDATE sessao SET seq = rowid + ? WHERE seq IS NULL AND encerrada = 1",
                        (deslocamento,))
        maior = conexao.execute(
            "SELECT MAX(COALESCE((SELECT MAX(seq) FROM placar), 0), "
            "COALESCE((SELECT MAX(seq) FROM sessao), 0))").fetchone()[0]
        conexao.execute("INSERT INTO contador (nome, valor) VALUES ('sinc', ?)", (maior,))
    conexao.execute("CREATE INDEX IF NOT EXISTS idx_placar_seq ON placar(seq)")
    conexao.execute("CREATE INDEX IF NOT EXISTS idx_sessao_seq ON sessao(seq)")


def proximo_seq(conexao):
    """Proximo numero de chegada. Dentro da mesma transacao da gravacao --
    o SQLite so deixa um escrever por vez, entao a ordem nunca embaralha."""
    conexao.execute("UPDATE contador SET valor = valor + 1 WHERE nome = 'sinc'")
    return conexao.execute("SELECT valor FROM contador WHERE nome = 'sinc'").fetchone()[0]


def preparar_banco():
    try:
        with banco() as conexao:
            aplicar_esquema(conexao)
    except sqlite3.DatabaseError as falha:
        # Banco corrompido -- pen drive arrancado no meio de uma
        # gravacao, cartao SD com setor ruim, arquivo trocado por
        # engano. Achado real na auditoria: sem este tratamento, isso
        # derrubava o ARENA INTEIRO, cru, com traceback do Python, antes
        # mesmo do servidor HTTP conseguir subir -- exatamente o
        # contrario do que o projeto promete ("abre mesmo assim e
        # explica"). Guarda o arquivo quebrado do lado (nunca apaga dado
        # do usuario sem manter uma copia) e comeca um banco novo vazio.
        print("[ARENA] O banco de recordes (arena.db) esta corrompido: %s" % falha)
        try:
            quebrado = ARQUIVO_BANCO + ".corrompido-" + time.strftime("%Y%m%d-%H%M%S")
            os.replace(ARQUIVO_BANCO, quebrado)
            print("[ARENA] Guardei o arquivo quebrado em: %s" % quebrado)
        except OSError as falha_ao_guardar:
            print("[ARENA] Nao consegui guardar uma copia do banco quebrado "
                 "(%s) -- vou sobrescrever." % falha_ao_guardar)
        # O SQLite pode ter deixado arquivos -wal/-shm associados ao
        # banco quebrado; sem apaga-los, o banco NOVO tentaria reusa-los
        # e cairia no mesmo erro.
        for sufixo in ("-wal", "-shm"):
            try:
                os.remove(ARQUIVO_BANCO + sufixo)
            except OSError:
                pass
        with banco() as conexao:
            aplicar_esquema(conexao)
        print("[ARENA] Comecei um banco novo, vazio. Os recordes antigos "
             "ficaram guardados no arquivo acima, mas nao aparecem mais "
             "na tela (um banco novo nao consegue ler um arquivo quebrado).")


def inserir_placar(conexao, id_registro, apelido, jogo_id, jogo_titulo, pontos,
                   registrado_em, dispositivo, enviado=0):
    """Grava um recorde. Devolve quantas linhas entraram (0 = ja existia).
    Todo recorde passa por aqui -- o feito neste computador e o que chegou
    de um colega -- para a sincronizacao marcar a ordem de chegada igual."""
    return conexao.execute(
        "INSERT OR IGNORE INTO placar (uuid, apelido, jogo_id, jogo_titulo, "
        "pontos, registrado_em, dispositivo, enviado, seq) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (id_registro, apelido, jogo_id, jogo_titulo, pontos, registrado_em,
         dispositivo, enviado, proximo_seq(conexao))).rowcount


def abrir_sessao(conexao, id_registro, apelido, jogo_id, jogo_titulo, inicio,
                 dispositivo):
    """Sessao de jogo comecando (ainda aberta: so conta quando fechar)."""
    conexao.execute(
        "INSERT INTO sessao (uuid, apelido, jogo_id, jogo_titulo, inicio, "
        "dispositivo) VALUES (?,?,?,?,?,?)",
        (id_registro, apelido, jogo_id, jogo_titulo, inicio, dispositivo))


def encerrar_sessao(conexao, id_registro, segundos):
    # O numero de chegada vem AGORA, no fim da partida: e' quando ela passa
    # a contar e precisa ir para os colegas.
    conexao.execute(
        "UPDATE sessao SET segundos = ?, encerrada = 1, seq = ? WHERE uuid = ?",
        (segundos, proximo_seq(conexao), id_registro))


def inserir_sessao_recebida(conexao, id_registro, apelido, jogo_id, jogo_titulo,
                            inicio, segundos, dispositivo):
    """Sessao ja encerrada vinda de outro ARENA. 0 = ja existia."""
    return conexao.execute(
        "INSERT OR IGNORE INTO sessao (uuid, apelido, jogo_id, jogo_titulo, "
        "inicio, segundos, encerrada, dispositivo, enviado, seq) "
        "VALUES (?,?,?,?,?,?,1,?,1,?)",
        (id_registro, apelido, jogo_id, jogo_titulo, inicio, segundos,
         dispositivo, proximo_seq(conexao))).rowcount


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
# BLOCO 3 - Leitura da maquina
# ---------------------------------------------------------------------------

def detectar_maquina():
    """Le a maquina uma vez, na abertura. Ver servidor/hardware.py."""
    return hardware.resumo(RAIZ)


# Lidos uma vez na abertura. Nao mudam enquanto o ARENA estiver aberto.
MAQUINA = detectar_maquina()
CAPACIDADE = hardware.capacidade(MAQUINA)

# Em maquina modesta, cada volta do vigia e cada gravacao pesam. O ARENA
# mede a maquina e espaca tudo: continua funcionando igual, so conversa com
# a rede e com o disco com menos frequencia.
ECONOMICO = (MAQUINA["perfil_maquina"] == "leve"
             or MAQUINA["disco"]["classe"] in ("lento", "medio")
             or MAQUINA["removivel"])

INTERVALO_VIGIA = 60.0 if ECONOMICO else 20.0
INTERVALO_ENVIO = 300.0 if ECONOMICO else 90.0

# Cartao SD e pen drive tem numero limitado de gravacoes. A copia a cada
# jogo fechado vira a cada 15 minutos no modo economico - e continua
# havendo copia quando a internet volta.
INTERVALO_BACKUP = 900.0 if ECONOMICO else 0.0


# ---------------------------------------------------------------------------
# BLOCO 4 - Perfis de video e audio
# ---------------------------------------------------------------------------
# Cada perfil e um conjunto de opcoes do proprio RetroArch. O ARENA grava
# num arquivo separado e manda o RetroArch juntar por cima da configuracao
# normal, com --appendconfig. A configuracao original nunca e alterada.
#
# Drivers de video oferecidos: so vulkan, d3d11 e glcore. Os antigos
# (d3d9, sdl2, gdi) ficaram de fora de proposito: sao mais lentos e nao
# fazem nada que estes tres nao facam melhor.

DRIVERS_VIDEO = ["automatico", "vulkan", "d3d11", "glcore"]

# Opcoes que valem para qualquer perfil. Reduzem trabalho inutil.
BASE_COMUM = {
    "audio_driver": "wasapi",

    # --- Teclas ------------------------------------------------------------
    # Por padrao o RetroArch usa Esc para FECHAR o jogo. Aqui Esc passa a
    # ABRIR o menu, que e onde ficam os 10 espacos de save state e os
    # cheats. Para fechar o jogo, F10.
    "input_menu_toggle": "escape",
    "input_exit_emulator": "f10",
    "input_enable_hotkey": "nul",
    "input_save_state": "f2",
    "input_load_state": "f4",
    "input_state_slot_decrease": "f6",
    "input_state_slot_increase": "f7",
    "input_screenshot": "f8",
    "input_pause_toggle": "p",
    "input_toggle_fullscreen": "f",

    # --- Save states -------------------------------------------------------
    # Todo jogo abre no espaco 0, "o de sempre" (guia 4). O RetroArch desta
    # pasta ja volta ao 0 sozinho a cada jogo aberto -- conferido em
    # 08/10/2026 com a configuracao pedindo o espaco 3. A chave fica, agora
    # com o nome certo (era "savestate_slot", que nao existe: auditoria 3,
    # servidor\tests\test_chaves_do_retroarch.py), para o caso de uma versao
    # nova do RetroArch passar a lembrar o espaco -- e o proximo F2 regravar
    # o 9, o "seguro" do guia.
    "state_slot": "0",
    "savestate_max_keep": "0",     # 0 = nao apaga estado antigo sozinho
    "quick_menu_show_save_load_state": "true",
    "quick_menu_show_undo_save_load_state": "true",

    # --- Cheats ------------------------------------------------------------
    "quick_menu_show_cheats": "true",
    "apply_cheats_after_load": "true",

    # --- O menu do Esc, enxuto -------------------------------------------
    # O menu do RetroArch vem com dezenas de itens que o aluno nunca vai
    # usar e que so atrapalham na hora de achar o save. Aqui fica so o que
    # importa: salvar, voltar, cheats, controle, imagem e som.
    #
    # O visual e o rgui: texto em cima de fundo escuro, sem imagem nem
    # animacao. Abre instantaneo ate no PC mais fraco, e tem a cara certa
    # para um console retro.
    # Menu em portugues. Sem isto ele abre em ingles e o aluno se perde
    # logo na primeira tela.
    # 7 = portugues do Brasil na tabela do RetroArch. Eu tinha escrito 17,
    # que e grego - e o menu abria em grego, com as letras que o aluno nao
    # le. Erro simples, efeito devastador.
    "user_language": "7",
    # Verde classico (o 4 do RetroArch): letra branca no fundo verde-escuro,
    # o que os alunos sempre viram. O ARENA pedia o 27 (Solarized escuro),
    # mas com o nome errado ("menu_rgui_color_theme") -- nunca valeu, e
    # trocar agora seria surpresa para quem ja conhece o menu.
    "rgui_menu_color_theme": "4",
    "rgui_background_filler_thickness_enable": "false",
    "rgui_border_filler_enable": "true",
    "rgui_border_filler_thickness_enable": "false",
    "menu_rgui_full_width_layout": "true",
    "rgui_inline_thumbnails": "false",
    "rgui_particle_effect": "0",                # sem animacao de fundo
    "rgui_show_start_screen": "false",
    "menu_show_advanced_settings": "false",
    "menu_show_help": "false",
    "menu_show_reboot": "false",
    "menu_show_shutdown": "false",
    "content_show_add_entry": "0",              # "Importar conteudo": escondido
    "content_show_images": "false",
    "content_show_music": "false",
    "content_show_video": "false",
    "content_show_netplay": "true",
    "content_show_playlists": "false",
    "content_show_explore": "false",
    "quick_menu_show_take_screenshot": "true",
    "quick_menu_show_options": "true",
    # Itens que so confundem quem quer salvar e voltar ao jogo. (As
    # conquistas nem aparecem: cheevos_enable fica no padrao, desligado.)
    "quick_menu_show_replay": "false",
    "menu_show_core_updater": "false",
    "menu_show_online_updater": "false",
    "menu_show_load_content_animation": "false",
    "menu_savestate_resume": "true",
    "menu_insert_disk_resume": "true",
    "menu_show_sublabels": "true",
    # "Controles" dentro do Esc: e por ali que o aluno remapeia sem sair do
    # jogo, inclusive o jogador 2. Precisa estar visivel, e a tela de
    # entrada tambem, senao ele so consegue mexer no jogador 1.
    "quick_menu_show_controls": "true",
    "settings_show_input": "true",
    "input_remap_binds_enable": "true",
    "quick_menu_show_save_content_dir_overrides": "false",
    "quick_menu_show_restart_content": "true",
    "quick_menu_show_close_content": "true",
    "quick_menu_show_reset_core_association": "false",
    "quick_menu_show_download_thumbnails": "false",
    "quick_menu_show_information": "false",
    "quick_menu_show_add_to_favorites": "false",
    "quick_menu_show_set_core_association": "false",
    "quick_menu_show_shaders": "true",
    "quick_menu_show_save_core_overrides": "false",
    "quick_menu_show_save_game_overrides": "false",
    "settings_show_ai_service": "false",
    "settings_show_accessibility": "false",
    "settings_show_achievements": "false",
    "settings_show_logging": "false",
    "settings_show_playlists": "false",
    "settings_show_recording": "false",

    # --- Gravacao e transmissao: desligadas de verdade -------------------
    # O RetroArch sabe gravar video da partida e transmitir ao vivo. Nada
    # disso tem lugar numa escola: gravar aula com voz e imagem de menor
    # de idade e transmitir para a internet sao dois problemas que o ARENA
    # nao vai criar. Desligado no arquivo, escondido no menu, e a tecla de
    # atalho tirada para nao ligar sem querer.
    "video_record_quality": "0",
    "video_record_threads": "1",
    "video_gpu_record": "false",
    "video_post_filter_record": "false",
    "streaming_mode": "0",
    "video_stream_quality": "0",
    "quick_menu_show_start_recording": "false",
    "quick_menu_show_start_streaming": "false",
    "input_recording_toggle": "nul",
    "input_streaming_toggle": "nul",
    # Gravar e repetir a partida (replay, so os botoes): o atalho tinha o
    # nome antigo ("input_bsv_record_toggle") e nao valia; o padrao do
    # RetroArch ja e' sem tecla, e aqui fica garantido.
    "input_record_replay": "nul",
    "input_play_replay": "nul",
    "input_halt_replay": "nul",
    "input_grab_mouse_toggle": "nul",
    "settings_show_user_interface": "false",
    "settings_show_file_browser": "false",

    # --- O que voce ajustar fica guardado ----------------------------------
    # config_save_on_exit faz o RetroArch gravar, ao fechar, tudo o que
    # voce mexeu dentro do jogo: mapeamento de teclado, mapeamento de
    # controle, volume, filtros. Como o retroarch.cfg mora dentro da pasta
    # do ARENA, isso viaja junto no pen drive.
    #
    # O ARENA reescreve, a cada abertura, apenas as opcoes que ELE
    # gerencia (caminhos e perfil de desempenho). O resto e seu e fica.
    "config_save_on_exit": "true",

    # --- Deixar rastro quando algo der errado ----------------------------
    # Sem log, cada fechamento inesperado e uma investigacao do zero. Um
    # arquivo por sessao em dados\retroarch__AAAA_MM_DD__HH_MM_SS.log;
    # limpar_logs_antigos() mantem so os LOGS_MANTIDOS mais recentes.
    "log_to_file": "true",
    "log_to_file_timestamp": "true",
    "log_verbosity": "true",
    "frontend_log_level": "1",
    "perfcnt_enable": "false",
    "input_remapping_directory": "",   # preenchido em gravar_override
    "joypad_autoconfig_dir": "",       # preenchido em gravar_override
    "auto_remaps_enable": "true",
    "auto_overrides_enable": "true",
    "input_autodetect_enable": "true",

    # --- Analogico E direcional funcionando juntos ------------------------
    # Valor 1 faz o analogico esquerdo tambem valer como direcional, SEM
    # desligar o direcional de verdade. Os dois funcionam ao mesmo tempo,
    # em qualquer controle - e o aluno usa o que preferir sem configurar
    # nada. Num jogo de PlayStation 1 sem suporte a analogico, e a
    # diferenca entre o controle funcionar ou nao.
    "input_player1_analog_dpad_mode": "1",
    "input_player2_analog_dpad_mode": "1",
    "input_player3_analog_dpad_mode": "1",
    "input_player4_analog_dpad_mode": "1",

    # --- Vibracao --------------------------------------------------------
    # Funciona em Xbox, PS4, PS5 e Switch Pro por cabo. Em controle
    # generico depende do modelo.
    "input_rumble_gain": "100",
    "input_auto_game_focus": "0",
    # Consulta o controle o mais tarde possivel dentro do quadro: e o
    # ajuste que mais reduz atraso de comando sem custar desempenho.
    "input_poll_type_behavior": "2",

    "video_black_frame_insertion": "0",
    "savestate_auto_save": "false",
    "savestate_auto_load": "false",
    "savestate_thumbnail_enable": "false",
    "content_show_favorites": "false",
    "content_show_history": "false",
    "check_firmware_before_loading": "false",
    "video_font_enable": "false",
    "fps_show": "false",
}

# 'automatico' nao e um perfil proprio: ele escolhe, para cada jogo, o
# melhor perfil que aquela plataforma aguenta nesta maquina. E o padrao.
PERFIL_AUTOMATICO = {
    "rotulo": "Automatico",
    "resumo": "Deixe assim. O ARENA escolhe o melhor para cada jogo sozinho.",
}

PERFIS_GRAFICOS = {
    "desempenho": {
        "rotulo": "Desempenho",
        "resumo": "Para PC fraco. Feio, mas não trava.",
        "opcoes": {
            "video_threaded": "true",
            "video_smooth": "false",
            "video_shader_enable": "false",
            "video_vsync": "true",
            "video_frame_delay": "0",
            "video_frame_delay_auto": "false",
            "video_swap_interval": "1",
            "menu_driver": "rgui",
            "menu_show_load_content_animation": "false",
            "audio_latency": "96",
            "audio_resampler_quality": "1",
            "rewind_enable": "false",
            "run_ahead_enabled": "false",
        },
    },
    "equilibrado": {
        "rotulo": "Equilibrado",
        "resumo": "Meio-termo. Bonito o suficiente e leve o suficiente.",
        "opcoes": {
            "video_threaded": "true",
            "video_smooth": "true",
            "video_shader_enable": "false",
            "video_vsync": "true",
            "video_frame_delay": "0",
            "video_frame_delay_auto": "true",
            "video_swap_interval": "1",
            "menu_driver": "rgui",
            "menu_show_load_content_animation": "true",
            "audio_latency": "64",
            "audio_resampler_quality": "3",
            "rewind_enable": "false",
            "run_ahead_enabled": "false",
        },
    },
    "qualidade": {
        "rotulo": "Qualidade",
        "resumo": "O mais bonito. Só use se o PC aguentar.",
        "opcoes": {
            "video_threaded": "false",
            "video_smooth": "true",
            "video_shader_enable": "true",
            "video_vsync": "true",
            "video_frame_delay": "0",
            "video_frame_delay_auto": "true",
            "video_swap_interval": "1",
            "menu_driver": "rgui",
            "menu_show_load_content_animation": "true",
            "audio_latency": "32",
            "audio_resampler_quality": "5",
            # "Voltar no tempo" e "Resposta instantanea" NAO entram sozinhas
            # (auditoria 3, Fase 5, 09/10/2026). O Qualidade e' o que o
            # automatico escolhe para todo console de custo ate 3 numa
            # maquina de nota 4 -- e o Celeron N5100 da escola tira nota 4,
            # igual ao Ryzen (a nota conta nucleos). Medido no Ryzen, com o
            # jogo aberto (testes da Fase 5): o voltar no tempo derrubava o
            # N64 de 60 para 30 quadros/s; a resposta instantanea fazia o
            # ZX Spectrum gastar 12x o processador (55% contra 4,7% de um
            # nucleo), e as duas juntas, o PS1 5x (46,7% contra 8,7%, e 57
            # quadros/s). No Celeron (43% da velocidade de um nucleo do
            # Ryzen) o PS1 passaria de um nucleo inteiro. As duas continuam
            # em Ajustes -> Avancado para quem quiser ligar.
            "rewind_enable": "false",
            "run_ahead_enabled": "false",
        },
    },
}


# ---------------------------------------------------------------------------
# Classificacao de desempenho por plataforma
# ---------------------------------------------------------------------------
# Compara a capacidade medida da maquina (1 a 5) com o custo de cada
# plataforma (1 a 5). O resultado diz, em portugues claro, o que esperar.

CLASSES = {
    "otimo": {
        "rotulo": "Bonito e lisinho",
        "cor": "verde",
        "detalhe": "Seu PC sobra para este console. Vai rodar bonito.",
        "perfil": "qualidade",
    },
    "bom": {
        "rotulo": "Feio mas lisinho",
        "cor": "azul",
        "detalhe": "Vai rodar liso, mas sem os enfeites.",
        "perfil": "desempenho",
    },
    "ruim": {
        "rotulo": "Capenga",
        "cor": "vermelho",
        "detalhe": "Seu PC não dá conta deste console. Vai travar.",
        "perfil": "desempenho",
    },
}


def classificar(custo):
    """Perfil grafico automatico do RetroArch (Qualidade x Desempenho).

    ATENCAO (30/09/2026): desde a avaliacao nova, isto decide SO o perfil
    grafico -- a etiqueta que o aluno ve no cartao vem de
    classificar_plataforma(), abaixo. Ficou separado de proposito: trocar
    a etiqueta nao pode mudar sozinho a imagem dos jogos que ja rodam bem.

    Regra (antiga, mantida para o perfil):
      capacidade acima do custo  -> sobra folga  -> Qualidade
      capacidade igual ou abaixo -> Desempenho
    """
    nota = CAPACIDADE["nota"]
    if nota >= custo + 1:
        chave = "otimo"
    elif nota >= custo:
        chave = "bom"
    else:
        chave = "ruim"
    return dict(CLASSES[chave], chave=chave)


# ---------------------------------------------------------------------------
# Etiqueta de cada console NESTA maquina (o selo colorido do cartao)
# ---------------------------------------------------------------------------
# Achado de 30/09/2026: a etiqueta antiga comparava a nota (que conta
# nucleos, nao velocidade) com o custo. O Celeron N5100 e o Ryzen 5 5600G
# tiravam a mesma nota 4, e o PS2 (custo 5) aparecia "Capenga: vai travar"
# nos DOIS -- mas o Rafael jogou PS2 com 4 jogadores no Celeron otimizado
# (Crash Nitro Kart, Marvel Ultimate Alliance, Naruto Ultimate Ninja 4). E o
# Xbox 360 aparecia "Capenga" no Celeron, quando la ele nem ABRE (sem AVX).
#
# Agora a etiqueta usa o que foi MEDIDO (hardware.py): a velocidade de um
# nucleo, em "vezes o notebook-alvo", e as instrucoes do processador.

CLASSES_ETIQUETA = {
    "bem": {
        "rotulo": "Roda bem",
        "cor": "verde",
        "detalhe": "Sobra máquina para este console.",
    },
    "ajustes": {
        "rotulo": "Roda com ajustes",
        "cor": "azul",
        "detalhe": ("Roda, com a imagem que o ARENA escolhe para este PC. "
                    "Se engasgar, ligue o Gráfico original."),
    },
    "pesado": {
        "rotulo": "Pode travar",
        "cor": "vermelho",
        "detalhe": ("Este PC está abaixo do que este console pede. Dá para "
                    "tentar com o Gráfico original e o Ultra desempenho ligados."),
    },
    "nao_abre": {
        "rotulo": "Não abre neste PC",
        "cor": "cinza",
        "detalhe": "",
    },
}

# Velocidade minima de um nucleo, em vezes o notebook-alvo, para "Roda com
# ajustes" e para "Roda bem", pelo custo do console (consoles.json).
# Calibrado com o que foi jogado de verdade no Celeron N5100 otimizado
# (velocidade 1,0 por definicao): PS2 (custo 5) roda -> 0,9 basta para
# "com ajustes"; PSP (custo 3) roda abaixo de 60 -> "com ajustes", nao
# "bem". Console pode trocar estes numeros com "requisitos.velocidade".
VELOCIDADE_POR_CUSTO = {
    1: (0.25, 0.5),
    2: (0.35, 0.7),
    3: (0.6, 1.3),
    4: (0.8, 1.6),
    5: (0.9, 2.0),
}


def classificar_plataforma(plataforma, maquina=None):
    """Etiqueta do console nesta maquina: dict com chave, rotulo, cor e
    detalhe. Ordem: o que impede de ABRIR, depois a velocidade, depois a
    placa de video. 'maquina' existe para os testes (padrao: MAQUINA)."""
    maquina = MAQUINA if maquina is None else maquina
    custo = int(plataforma.get("custo", 3) or 3)
    requisitos = plataforma.get("requisitos") or {}
    instr = maquina.get("instrucoes") or {}

    def etiqueta(chave, detalhe=None):
        resultado = dict(CLASSES_ETIQUETA[chave], chave=chave)
        if detalhe:
            resultado["detalhe"] = detalhe
        return resultado

    # 1. O que impede de abrir (o emulador fecha na hora, sem explicar).
    if requisitos.get("avx") and instr.get("avx") is False:
        nome = (plataforma.get("externo") or {}).get("nome") or "o emulador"
        return etiqueta("nao_abre",
                        "O processador deste PC não tem AVX, que o %s exige. "
                        "Não é configuração: é o processador." % nome)

    # 2. Velocidade de um nucleo, medida.
    velocidade = (maquina.get("velocidade") or {}).get("relativa_ao_alvo")
    if not isinstance(velocidade, (int, float)):
        # Nao deu para medir: cai na regra antiga (nota x custo).
        antiga = classificar(custo)["chave"]
        return etiqueta({"otimo": "bem", "bom": "ajustes"}.get(antiga, "pesado"))
    minimo, folgado = requisitos.get("velocidade") or VELOCIDADE_POR_CUSTO.get(
        max(1, min(5, custo)))
    if velocidade >= folgado:
        chave = "bem"
    elif velocidade >= minimo:
        chave = "ajustes"
    else:
        chave = "pesado"

    # 3. Sem AVX2, o RPCS3 avisa que vai mal (requisitos dele); e console
    # 3D pesado em placa integrada nunca e' "Roda bem": o ARENA abaixa a
    # imagem sozinho, e a etiqueta conta isso.
    if requisitos.get("avx2_recomendado") and instr.get("avx2") is False:
        chave = "pesado"
    if chave == "bem" and custo >= 5 and (maquina.get("gpu") or {}).get("integrada", True):
        chave = "ajustes"
    return etiqueta(chave)


def ajustar_para_driver(opcoes, driver, perfil):
    """Aplica os ajustes que dependem do motor grafico escolhido.

    Isso importa porque as opcoes de sincronia do RetroArch NAO sao as
    mesmas nos tres motores:

      - Vulkan e D3D11 controlam o atraso pela fila de imagens
        (video_max_swapchain_images). 2 e o menor valor sem engasgo.
      - OpenGL usa video_hard_sync, que nao tem efeito em Vulkan.

    Trocar o motor sem trocar essas opcoes junto e o motivo classico de
    "mudei para Vulkan e ficou pior".
    """
    if driver in ("vulkan", "d3d11"):
        opcoes["video_max_swapchain_images"] = "3" if perfil == "desempenho" else "2"
        opcoes["video_hard_sync"] = "false"
        opcoes["video_hard_sync_frames"] = "0"
    else:  # glcore e gl
        opcoes["video_max_swapchain_images"] = "2"
        opcoes["video_hard_sync"] = "false" if perfil == "desempenho" else "true"
        opcoes["video_hard_sync_frames"] = "0"

    # WASAPI em modo exclusivo entrega o menor atraso de som, mas toma a
    # placa de som para si. Reservado ao perfil de maior qualidade.
    opcoes["audio_wasapi_exclusive_mode"] = "true" if perfil == "qualidade" else "false"
    opcoes["audio_wasapi_float_format"] = "true"
    return opcoes


# ---------------------------------------------------------------------------
# Recursos do RetroArch expostos na tela
# ---------------------------------------------------------------------------
# Vinham escritos aqui no codigo, em duplicidade com o resto. Agora moram em
# um arquivo unico, servidor/recursos.json, que o aluno pode ler e editar.
# Uma fonte de verdade so: o que esta la e o que aparece na tela e o que e
# aceito pela API.

ARQUIVO_RECURSOS = os.path.join(PASTA_SERVIDOR, "recursos.json")

_recursos_cache = {"dados": None}


def carregar_recursos():
    """Le recursos.json. Se estiver quebrado, o ARENA segue sem a aba."""
    if _recursos_cache["dados"] is None:
        try:
            with open(ARQUIVO_RECURSOS, "r", encoding="utf-8") as arquivo:
                _recursos_cache["dados"] = json.load(arquivo)
        except (OSError, ValueError) as falha:
            print("[ARENA] recursos.json ilegivel (%s). Seguindo sem os "
                  "ajustes avancados." % falha)
            _recursos_cache["dados"] = {"grupos": [], "recursos": []}
    return _recursos_cache["dados"]


def recursos_visiveis():
    """So os recursos que esta maquina aguenta.

    Esconder o que nao serve e melhor do que mostrar e deixar o aluno
    ligar algo que vai travar o jogo dele.
    """
    nota = CAPACIDADE["nota"]
    return [r for r in carregar_recursos()["recursos"]
            if nota >= r.get("nota_minima", 0)]


def avancado_desta_maquina(config):
    """As opcoes avancadas que valem NESTA maquina.

    A configuracao viaja no pen drive. Uma opcao pesada (nota_minima no
    recursos.json) ligada num PC forte nao pode voltar a valer no
    notebook fraco: aqui a tela nem a mostra (recursos_visiveis). Achado
    da auditoria 3 (07/10/2026): a "Resposta instantanea" ligada num i5
    religava no Celeron por cima da trava de opcoes_efetivas.

    Fora da nota, a opcao volta ao padrao do ARENA (AVANCADO_PADRAO, sempre
    o desligado); sem padrao, vale o que o perfil de imagem manda (os perfis
    sempre escrevem filtro, voltar no tempo, resposta instantanea e quadro
    preto). Tirar a opcao nao bastava: o RetroArch guarda no retroarch.cfg,
    ao fechar, o que recebeu -- e o valor do PC forte voltaria por la."""
    nota = CAPACIDADE["nota"]
    pesadas = {r["chave"] for r in carregar_recursos()["recursos"]
               if nota < r.get("nota_minima", 0)}
    desta = {}
    for chave, valor in (config.get("avancado") or {}).items():
        if chave not in pesadas:
            desta[chave] = valor
        elif chave in AVANCADO_PADRAO:
            desta[chave] = AVANCADO_PADRAO[chave]
    return desta


def recursos_por_chave():
    return {r["chave"]: r for r in carregar_recursos()["recursos"]}


AVANCADO_PADRAO = {
    "video_driver": "automatico",
    "video_fullscreen": "true",
    "video_scale_integer": "false",
    "video_swap_interval": "1",
    "audio_enable": "true",
    "audio_sync": "true",
    "audio_volume": "0",
    "input_joypad_driver": "xinput",
    "input_max_users": "2",
    "input_menu_toggle_gamepad_combo": "2",
    "input_turbo_period": "6",
    "input_analog_deadzone": "0.1",
    "input_analog_sensitivity": "1.0",
    "fastforward_ratio": "4.0",
    "slowmotion_ratio": "3.0",
    "rewind_buffer_size": "20",
    "run_ahead_frames": "1",
    "run_ahead_secondary_instance": "false",
    "savestate_thumbnail_enable": "false",
    # DESLIGADO de proposito. Ligado, o RetroArch pausa o jogo sempre que
    # a janela perde o foco - e em varias maquinas de escola a janela do
    # emulador nunca ganha o foco de verdade, porque o navegador do ARENA
    # continua com ele. O resultado e o jogo parado, avancando um quadro a
    # cada alt+tab. Parece defeito grave e e so isto.
    "pause_nonactive": "false",
    "fps_show": "false",
}


def config_padrao():
    return {
        "perfil_grafico": "automatico",
        "avancado": dict(AVANCADO_PADRAO),
        "apelido": "",
        "permitir_rede": False,
        # Lista de ARENAs com quem este troca informacao. O da escola e
        # apenas mais um da lista: se ele estiver desligado, os amigos
        # continuam funcionando entre si.
        # Cada item: {"apelido": "lucas", "url": "192.168.0.22", "escola": false}
        "servidores": [],
        # BIOS escolhida por console: {"ps1": "scph5501.bin"}
        "bios": {},
        "dispositivo_id": "",
        "codigo_proprio": False,
        "modo_desempenho": False,
        "ultra_desempenho": False,
        "modo_modesto": False,
        # Abaixo do grafico original (02/10/2026): "" (nao), "leve" ou
        # "minimo" -- imagem feia, roda em maquina mais fraca. Ligado, vale
        # como se o modo_modesto tambem estivesse (ver grafico_original).
        "abaixo_do_original": "",
        # "automatico" (decide pela nota da maquina), "leve" ou "bonito".
        # Vale para os emuladores externos (PCSX2, RPCS3, Xenia).
        "preset_grafico_externo": "automatico",
        # Motor de video do PCSX2 (PS2): "automatico" deixa o PCSX2 escolher
        # (no 2.8 ele escolhe DirectX 12 em placa Intel e AMD com nivel 12).
        "motor_ps2": "automatico",
        # Fundo animado da tela (ceu e campo): "automatico" anima, a nao ser
        # com o modo modesto ou o Windows pedindo menos movimento; "sempre";
        # "parado" (desenha a cena uma vez so).
        "fundo_animado": "automatico",
        "rpcn_ativo": False,
        # Interface: tema, jogos marcados e os ultimos abertos.
        "tema": "claro",
        "favoritos": [],
        "recentes": [],
        "travar_teclas": False,
        "tipo_controle": "xbox360",
        # Por console: direcional, analogicos, vibracao e se o jogador 2
        # vira mouse ou teclado.
        "perfil_controle": {},
        "nome_dispositivo": "",
    }


_config_cache = {"quando": 0.0, "valor": None}


def limpar_apelido(texto):
    """Apelido que pode ir para qualquer lugar: tela, banco, sincronizacao
    e o arquivo do RetroArch (netplay_nickname = "...").

    Achado de 01/10/2026: o apelido ia cru para esse arquivo. Uma aspa
    digitada pelo aluno (Joao "o brabo") quebrava a linha, e uma quebra de
    linha poderia enfiar outra opcao do emulador. Fica sem aspas, sem barra
    invertida e sem caractere de controle; espacos repetidos viram um so."""
    limpo = "".join(c for c in str(texto or "") if c.isprintable() and c not in '"\\')
    return " ".join(limpo.split())[:24]

# Jeitos de mostrar o fundo da tela (launcher\field-background.js e
# galaxy-background.js leem body[data-fundo-animado]).
FUNDOS_ANIMADOS = ("automatico", "sempre", "parado")


def carregar_config():
    """Le a configuracao, reaproveitando o que ja esta na memoria.

    Antes, cada requisicao reabria e reinterpretava o config.json. Com a
    sala inteira usando o ARENA de pen drive, isso vira leitura de disco a
    toda hora, a toa: o arquivo quase nunca muda. Agora o ARENA so rele
    quando a data de modificacao do arquivo mudou.
    """
    try:
        marca = os.path.getmtime(ARQUIVO_CONFIG)
    except OSError:
        marca = 0.0

    with TRAVA_CACHE:
        if _config_cache["valor"] is not None and _config_cache["quando"] == marca:
            # Copia, para quem chamar nao alterar o original sem querer.
            return json.loads(json.dumps(_config_cache["valor"]))

    config = ler_config_do_disco()

    with TRAVA_CACHE:
        _config_cache["quando"] = marca
        _config_cache["valor"] = config
    return json.loads(json.dumps(config))


def ler_config_do_disco():
    """Le config.json de verdade. Se nao existir ou estiver quebrado, usa o padrao."""
    config = config_padrao()
    try:
        with open(ARQUIVO_CONFIG, "r", encoding="utf-8") as arquivo:
            salvo = json.load(arquivo)
    except (OSError, ValueError):
        salvo = {}
    if not isinstance(salvo, dict):
        salvo = {}     # [] ou "texto" no lugar de {...}: vale o padrao

    if salvo.get("perfil_grafico") in list(PERFIS_GRAFICOS) + ["automatico"]:
        config["perfil_grafico"] = salvo["perfil_grafico"]
    if isinstance(salvo.get("avancado"), dict):
        # So entram chaves que o ARENA conhece hoje. Um config.json de uma
        # versao anterior pode trazer opcao que nao existe mais, e nao ha
        # por que carregar isso adiante nem escrever no arquivo do
        # RetroArch.
        validas = recursos_por_chave()
        for chave, valor in salvo["avancado"].items():
            if chave in validas or chave in AVANCADO_PADRAO:
                # config.json mexido a mao (ou de versao antiga) pode trazer
                # true/false do JSON: no arquivo do RetroArch isso viraria
                # "True", que ele nao entende. Lista e objeto nao servem.
                if isinstance(valor, bool):
                    valor = "true" if valor else "false"
                elif isinstance(valor, (int, float)):
                    valor = str(valor)
                elif not isinstance(valor, str):
                    continue
                config["avancado"][chave] = valor
    config["apelido"] = limpar_apelido(salvo.get("apelido", ""))
    config["permitir_rede"] = bool(salvo.get("permitir_rede", False))
    config["nome_dispositivo"] = str(salvo.get("nome_dispositivo", ""))[:40]

    servidores = []
    # So lista: "servidores": 5 (config.json mexido a mao) derrubava a
    # leitura da config -- e a abertura do ARENA junto (achado de 01/10/2026,
    # fuzz do config.json).
    lista = salvo.get("servidores")
    for item in (lista if isinstance(lista, list) else []):
        if not isinstance(item, dict) or not item.get("url"):
            continue
        servidores.append({
            "apelido": str(item.get("apelido", ""))[:24] or "sem nome",
            "url": str(item["url"])[:200].strip(),
            "escola": bool(item.get("escola")),
            # Ate onde ja trocamos com este amigo. Mantem a conversa curta
            # mesmo depois de meses: so o que e novo viaja.
            "ultimo_recebido": str(item.get("ultimo_recebido", ""))[:40],
            "ultimo_enviado": str(item.get("ultimo_enviado", ""))[:40],
            "id": str(item.get("id", ""))[:40],
        })
    # Migracao das versoes antigas, que guardavam um endereco so.
    antigo = str(salvo.get("servidor_url", "")).strip()
    if antigo and not any(x["url"] == antigo for x in servidores):
        servidores.insert(0, {"apelido": "Escola", "url": antigo, "escola": True})
    config["servidores"] = servidores[:20]

    config["modo_desempenho"] = bool(salvo.get("modo_desempenho"))
    config["ultra_desempenho"] = bool(salvo.get("ultra_desempenho"))
    config["modo_modesto"] = bool(salvo.get("modo_modesto"))
    if salvo.get("abaixo_do_original") in graficos.NIVEIS_ABAIXO:
        config["abaixo_do_original"] = salvo["abaixo_do_original"]
    config["rpcn_ativo"] = bool(salvo.get("rpcn_ativo"))
    if salvo.get("preset_grafico_externo") in ("automatico", "leve", "bonito"):
        config["preset_grafico_externo"] = salvo["preset_grafico_externo"]
    # tuple(): um valor que nao e' texto (lista, por exemplo) num dict daria
    # erro de "unhashable" e derrubaria a leitura da config inteira.
    if salvo.get("motor_ps2") in tuple(graficos.MOTORES_PCSX2):
        config["motor_ps2"] = salvo["motor_ps2"]
    if salvo.get("fundo_animado") in FUNDOS_ANIMADOS:
        config["fundo_animado"] = salvo["fundo_animado"]

    if salvo.get("tema") in ("claro", "escuro"):
        config["tema"] = salvo["tema"]
    for chave, limite in (("favoritos", 200), ("recentes", 12)):
        guardado = salvo.get(chave)
        if isinstance(guardado, list):
            config[chave] = [str(x)[:300] for x in guardado][:limite]
    config["travar_teclas"] = bool(salvo.get("travar_teclas"))
    if isinstance(salvo.get("tipo_controle"), str):
        config["tipo_controle"] = salvo["tipo_controle"][:24]
    if isinstance(salvo.get("perfil_controle"), dict):
        for console, escolhas in salvo["perfil_controle"].items():
            if isinstance(escolhas, dict):
                config["perfil_controle"][str(console)[:24]] = {
                    k: escolhas[k] for k in
                    ("direcional", "analogico_esq", "analogico_dir",
                     "vibracao", "extra") if k in escolhas}

    if isinstance(salvo.get("bios"), dict):
        config["bios"] = {str(k)[:24]: str(v)[:120]
                          for k, v in salvo["bios"].items()}

    # Identificador desta instalacao. Criado uma vez e nunca mais muda:
    # e o que permite juntar recordes de varios ARENAs sem duplicar.
    # O codigo do aparelho nasce da propria maquina, nao do arquivo. E o
    # que impede trinta pen drives copiados de terem o mesmo codigo - o
    # que quebraria a sincronizacao e a partida a dois de todo mundo.
    da_maquina = hardware.identidade_da_maquina()
    guardado = salvo.get("dispositivo_id") or ""

    if salvo.get("codigo_proprio"):
        # Ja houve troca por codigo repetido: aquele codigo e definitivo.
        config["dispositivo_id"] = guardado or uuid.uuid4().hex[:12]
        config["codigo_proprio"] = True
    elif da_maquina:
        config["dispositivo_id"] = da_maquina
    else:
        config["dispositivo_id"] = guardado or uuid.uuid4().hex[:12]

    if config["dispositivo_id"] != guardado:
        salvar_config(config)
    return config


def salvar_config(config):
    with TRAVA_CACHE:
        _config_cache["valor"] = None      # forca releitura na proxima vez
    os.makedirs(PASTA_DADOS, exist_ok=True)
    gravar_texto_atomico(
        ARQUIVO_CONFIG, json.dumps(config, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------------------
# Perfil do aluno: apelido + foto, permanente (como um perfil de Steam)
# ---------------------------------------------------------------------------
# A foto fica num arquivo separado do config.json, nao dentro dele - imagem
# em base64 misturada com config de texto deixaria o arquivo ilegivel e
# pesado de reler a cada requisicao. So um arquivo por vez: nome sempre
# "foto.<extensao>", trocar a foto apaga a extensao antiga.

TIPOS_FOTO_PERFIL = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}
ASSINATURAS_FOTO_PERFIL = {
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
}
LIMITE_FOTO_PERFIL = 2 * 1024 * 1024


def foto_perfil_caminho():
    """Acha o arquivo da foto atual, seja qual for a extensao - ou None
    se ninguem colocou foto ainda. So os nomes certos (foto.png, foto.jpg,
    foto.webp): o temporario de uma gravacao interrompida tambem comeca com
    "foto." (foto.png.1234.tmp) e nao pode passar por foto (auditoria 3)."""
    for extensao in TIPOS_FOTO_PERFIL.values():
        caminho = os.path.join(PASTA_PERFIL, "foto" + extensao)
        if os.path.isfile(caminho):
            return caminho
    return None


def _tipo_da_imagem(brutos):
    for assinatura, tipo in ASSINATURAS_FOTO_PERFIL.items():
        if brutos.startswith(assinatura):
            return tipo
    # WEBP: RIFF....WEBP
    if brutos[:4] == b"RIFF" and brutos[8:12] == b"WEBP":
        return "image/webp"
    return None


def gravar_foto_perfil(imagem_base64):
    """Decodifica e grava a foto de perfil, conferindo de verdade o tipo
    do arquivo (nao confia na extensao nem no que o navegador disse que
    era) - mesmo cuidado que o resto do ARENA tem com entrada de fora.
    """
    if "," in imagem_base64:
        imagem_base64 = imagem_base64.split(",", 1)[1]
    try:
        brutos = base64.b64decode(imagem_base64, validate=True)
    except (binascii.Error, ValueError):
        raise ValueError("Não consegui ler essa imagem. Escolha outra foto (PNG, JPG ou WEBP).")

    if not brutos or len(brutos) > LIMITE_FOTO_PERFIL:
        raise ValueError("Foto grande demais: o limite é 2 MB. Escolha uma foto menor.")

    tipo = _tipo_da_imagem(brutos)
    if tipo not in TIPOS_FOTO_PERFIL:
        raise ValueError("Esse formato de imagem não serve. Escolha uma foto PNG, JPG ou WEBP.")

    os.makedirs(PASTA_PERFIL, exist_ok=True)
    antiga = foto_perfil_caminho()
    destino = os.path.join(PASTA_PERFIL, "foto" + TIPOS_FOTO_PERFIL[tipo])
    temporario = "%s.%d.tmp" % (destino, threading.get_ident())
    try:
        with TRAVA_ARQUIVO:
            with open(temporario, "wb") as arquivo:
                arquivo.write(brutos)
                arquivo.flush()
                os.fsync(arquivo.fileno())
            os.replace(temporario, destino)
    finally:
        if os.path.exists(temporario):
            try:
                os.remove(temporario)
            except OSError:
                pass
    # A antiga (de outra extensao) so sai depois que a nova esta inteira no
    # lugar. Achado da auditoria 3: saia ANTES, e uma gravacao que falhasse
    # (pen drive cheio) deixava o aluno sem foto nenhuma.
    if antiga and os.path.normcase(antiga) != os.path.normcase(destino):
        try:
            os.remove(antiga)
        except OSError:
            pass
    return destino


# ---------------------------------------------------------------------------
# Miniaturas das capas
# ---------------------------------------------------------------------------
# Achado de 01/10/2026 (medido com testes\tela_sem_janela.py): a tela pedia
# as capas em TAMANHO CHEIO (~450 KB, ~1000 px de largura) para cartoes de
# ~220 px -- 21 MB e ~130 MB de imagem aberta na memoria so para mostrar a
# lista. Agora, na primeira vez, o PROPRIO NAVEGADOR reduz a capa (e' nativo
# e rapido; em Python puro levaria segundos por imagem) e manda a
# miniatura; o servidor guarda em dados\miniaturas e entrega ela dali em
# diante. 280 px para tela comum, 480 px para tela de alta densidade (4K).

PASTA_MINIATURAS_CAPA = os.path.join(PASTA_DADOS, "miniaturas")
LARGURAS_MINIATURA = (280, 480)
LIMITE_MINIATURA = 200 * 1024
MAXIMO_MINIATURAS = 4000


def capa_permitida(pedido):
    """Caminho da capa pedida pela tela, ou None. So arte dentro da pasta
    de jogos OU das miniaturas baixadas (retroarch\\thumbnails): sem isto,
    bastaria pedir ../../dados/config.json para ler o que nao devia."""
    alvo = os.path.join(RAIZ, str(pedido or "").replace("/", os.sep))
    if not (dentro_da_pasta(alvo, PASTA_JOGOS) or dentro_da_pasta(alvo, PASTA_MINIATURAS)):
        return None
    if not os.path.isfile(alvo) or not alvo.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
        return None
    return alvo


def base_da_miniatura(alvo, largura):
    """dados\\miniaturas\\<codigo> (sem extensao). O codigo muda quando a
    capa muda (tamanho ou data): miniatura velha nunca aparece."""
    estado = os.stat(alvo)
    texto = "%s|%d|%d|%d" % (os.path.relpath(alvo, RAIZ).lower(), estado.st_size,
                             int(estado.st_mtime), largura)
    return os.path.join(PASTA_MINIATURAS_CAPA, hashlib.sha1(texto.encode("utf-8")).hexdigest()[:24])


def miniatura_pronta(alvo, largura):
    try:
        base = base_da_miniatura(alvo, largura)
    except OSError:
        return None
    for extensao in (".webp", ".jpg", ".png"):
        if os.path.isfile(base + extensao):
            return base + extensao
    return None


def gravar_miniatura(alvo, largura, imagem_base64):
    """Guarda a miniatura que a tela fez. Confere o tipo pelos bytes (nao
    confia no que o navegador disse) e o tamanho."""
    texto = str(imagem_base64 or "")
    if "," in texto:
        texto = texto.split(",", 1)[1]
    try:
        brutos = base64.b64decode(texto, validate=True)
    except (binascii.Error, ValueError):
        raise ValueError("Miniatura inválida.")
    if not brutos or len(brutos) > LIMITE_MINIATURA:
        raise ValueError("Miniatura grande demais.")
    tipo = _tipo_da_imagem(brutos)
    extensao = TIPOS_FOTO_PERFIL.get(tipo)
    if not extensao:
        raise ValueError("Miniatura em formato não aceito.")
    os.makedirs(PASTA_MINIATURAS_CAPA, exist_ok=True)
    destino = base_da_miniatura(alvo, largura) + extensao
    temporario = "%s.%d.tmp" % (destino, threading.get_ident())
    with open(temporario, "wb") as arquivo:
        arquivo.write(brutos)
    os.replace(temporario, destino)
    limpar_miniaturas_antigas()
    return destino


def limpar_miniaturas_antigas():
    """Teto de MAXIMO_MINIATURAS arquivos: passou, apaga as mais antigas
    (sao so copias pequenas; a capa de verdade continua onde estava)."""
    try:
        arquivos = [e for e in os.scandir(PASTA_MINIATURAS_CAPA) if e.is_file()]
    except OSError:
        return 0
    if len(arquivos) <= MAXIMO_MINIATURAS:
        return 0
    arquivos.sort(key=lambda e: e.stat().st_mtime)
    sobra = arquivos[:len(arquivos) - int(MAXIMO_MINIATURAS * 0.9)]
    for entrada in sobra:
        try:
            os.remove(entrada.path)
        except OSError:
            pass
    return len(sobra)


def apagar_foto_perfil():
    caminho = foto_perfil_caminho()
    if caminho:
        try:
            os.remove(caminho)
        except OSError:
            pass
        return True
    return False


def perfil_para(config, custo=None):
    """Resolve qual perfil vale agora.

    Com 'automatico', o perfil sai da classificacao da plataforma: console
    que sobra folga roda em Qualidade, console apertado roda em Desempenho.
    Assim o Super Nintendo fica bonito e o PlayStation 2 fica jogavel, na
    mesma maquina, sem o aluno mexer em nada.
    """
    escolhido = config.get("perfil_grafico", "automatico")
    if escolhido in PERFIS_GRAFICOS:
        return escolhido
    if custo is None:
        return "equilibrado"
    return classificar(custo)["perfil"]


def nivel_abaixo(config):
    """"leve" ou "minimo" quando o aluno escolheu ABAIXO do grafico original;
    "" fora disso (pedido do Rafael, 02/10/2026)."""
    valor = config.get("abaixo_do_original")
    return valor if valor in graficos.NIVEIS_ABAIXO else ""


def grafico_original(config):
    """O grafico igual ao console original vale -- ligado direto ou porque
    o aluno escolheu um nivel ABAIXO dele (que comeca no original)."""
    return bool(config.get("modo_modesto")) or bool(nivel_abaixo(config))


def opcoes_efetivas(config, custo=None, controles_ligados=None):
    """Junta base + perfil + ajustes avancados na ordem certa.

    O perfil entra primeiro; o ajuste manual do aluno entra por cima e
    vence. 'automatico' no motor grafico vira o driver realmente detectado,
    e so entao os ajustes que dependem do motor sao aplicados.
    """
    nome_perfil = perfil_para(config, custo)
    perfil = PERFIS_GRAFICOS.get(nome_perfil, PERFIS_GRAFICOS["equilibrado"])

    opcoes = dict(BASE_COMUM)
    opcoes.update(perfil["opcoes"])

    driver = config.get("avancado", {}).get("video_driver", "automatico")
    if driver == "automatico":
        driver = MAQUINA["driver_video"]
    ajustar_para_driver(opcoes, driver, nome_perfil)

    # Trava de seguranca: resposta instantanea custa de 4 a 12 vezes o
    # processador do emulador (medido na Fase 5 da auditoria 3: PS1 e ZX
    # Spectrum). Em maquina abaixo de nota 4, ela transforma um jogo que
    # rodava liso num jogo que engasga. Melhor nem oferecer. (Nenhum perfil
    # liga sozinho; so o aluno, em Ajustes -> Avancado.)
    if CAPACIDADE["nota"] < 4:
        opcoes["run_ahead_enabled"] = "false"

    opcoes.update(avancado_desta_maquina(config))
    opcoes["video_driver"] = driver
    opcoes["log_dir"] = PASTA_DADOS

    # Teclas e botoes que o aluno definiu na tela do ARENA, entrando por
    # ultimo. O teclado vai para o primeiro jogador sem controle: quem abre
    # o jogo conta os controles ligados AGORA e passa o numero. Achado de
    # 02/10/2026: contava em TODA chamada -- a cada /api/estado e a cada
    # ajuste salvo --, e a contagem antiga deixava alcas do Windows abertas.
    opcoes.update(controles.opcoes_do_retroarch(
        controles_ligados=controles_ligados or 0))

    # Filtro de tela: o perfil (ou o aluno) diz se quer; QUAL filtro e' se
    # o console aceita, so se sabe com o jogo na mao -- gravar_override().
    return opcoes


# ---------------------------------------------------------------------------
# Ultra desempenho
# ---------------------------------------------------------------------------
# O que este modo FAZ, e cada item e real:
#
#   - o ARENA cede a vez (prioridade abaixo do normal, memoria de prioridade
#     baixa) e o emulador fica fora da economia de energia do Windows --
#     o mesmo do modo desempenho (ver executar_jogo e servidor\processos.py;
#     ate 30/09/2026 a "prioridade alta" prometida aqui nunca acontecia);
#   - o ARENA para de vigiar a rede e de anunciar na rede enquanto o jogo
#     roda, entao nao ha nenhuma tarefa de fundo disputando o processador;
#   - a placa de som passa a ser do jogo em modo exclusivo (WASAPI), o que
#     tira o misturador do Windows do caminho;
#   - tela cheia sem borda (nao a exclusiva - motivo abaixo);
#   - filtros, voltar no tempo e resposta instantanea saem de cena.
#
# O que ele NAO faz, e nao adianta prometer:
#
#   - nao desliga o Windows nem impede o Ctrl+Alt+Del. So um programa com
#     senha de administrador e driver proprio conseguiria, e o aluno nao
#     tem essa senha na maquina da escola;
#   - nao fecha programas de ninguem. Se o Teams estiver aberto, ele
#     continua aberto - so perde a vez na fila do processador;
#   - NAO prende o teclado. Isso e outra chave (travar_teclas, mais
#     abaixo). Ultra desempenho sozinho nunca tranca o Esc.
#
# Para sair: feche o jogo com F10.

ULTRA_DESEMPENHO = {
    # Som direto na placa, sem o misturador do Windows no meio.
    "audio_driver": "wasapi",
    "audio_wasapi_exclusive_mode": "true",
    "audio_latency": "32",
    "audio_resampler_quality": "1",

    # Tela cheia SEM BORDA, nao a exclusiva. A exclusiva troca o modo de
    # video da placa e, em placa de video integrada (o caso comum na
    # escola), costuma perder o foco do teclado quando o Esc tenta abrir
    # o menu - o RetroArch "recebe" o Esc mas a troca de superficie
    # engasga e o menu nao aparece. Sem borda custa quase nada de FPS e
    # nao tem esse problema.
    "video_fullscreen": "true",
    "video_windowed_fullscreen": "true",
    "video_max_swapchain_images": "2",
    "video_hard_sync": "false",
    "video_threaded": "false",
    "video_frame_delay_auto": "true",

    # Nada de enfeite.
    "video_shader_enable": "false",
    "video_smooth": "false",
    "video_font_enable": "false",
    "fps_show": "false",
    "rewind_enable": "false",
    "run_ahead_enabled": "false",
    "savestate_thumbnail_enable": "false",
    "savestate_auto_save": "false",
    "check_firmware_before_loading": "false",

    # ATENCAO: prender o teclado NAO entra aqui.
    #
    # input_auto_game_focus = 1 trava o Alt+Tab e a tecla Windows - mas
    # trava junto o proprio Esc, porque o RetroArch para de interceptar
    # TODAS as teclas de atalho, inclusive a que abre o menu. O aluno
    # ficava sem menu e sem entender por que.
    #
    # Virou uma chave separada, desligada por padrao, com tecla de escape
    # documentada (F9). Desempenho e travar o teclado sao duas decisoes
    # diferentes, e agora sao dois botoes diferentes.
    "input_auto_game_focus": "0",

    # Menu no mais leve.
    "menu_driver": "rgui",
    "rgui_particle_effect": "0",
}


def remapeamento_da_partida(opcoes, caminho_core, caminho_jogo):
    """Grava o tipo de cada porta (input_libretro_device_pN) num arquivo de
    remapeamento SO desta partida e devolve a pasta dele.

    Achado real (Multitap, 25/09/2026, com os controles na mao): o RetroArch
    IGNORA input_libretro_device_pN vindo do --appendconfig. O Super
    Bomberman 4 abria com "SNES Joypad" na porta 2 e so 2 jogadores, mesmo
    com o arquivo da partida pedindo o Multitap (257). O arquivo de
    remapeamento (.rmp) e' onde o proprio RetroArch guarda o "Tipo de
    dispositivo" -- dele ele le sempre. Provado: com ele, 5 jogadores."""
    tipos = {c: v for c, v in opcoes.items() if c.startswith("input_libretro_device_p")}
    if not tipos:
        return None
    nome_info = os.path.splitext(os.path.basename(caminho_core))[0] + ".info"
    nome_nucleo = None
    try:
        with open(os.path.join(PASTA_RETROARCH, "info", nome_info), encoding="utf-8") as arquivo:
            for linha in arquivo:
                if linha.startswith("corename"):
                    nome_nucleo = linha.split("=", 1)[1].strip().strip('"')
                    break
    except OSError:
        pass
    if not nome_nucleo:
        return None
    nome_jogo = os.path.splitext(os.path.basename(caminho_jogo))[0]

    # O remapeamento que o aluno salvou pelo menu do RetroArch continua
    # valendo: entra primeiro, e so o tipo das portas e' trocado.
    linhas = []
    for candidato in (os.path.join(PASTA_REMAPS, nome_nucleo, nome_jogo + ".rmp"),
                      os.path.join(PASTA_REMAPS, nome_nucleo, nome_nucleo + ".rmp")):
        if os.path.isfile(candidato):
            with open(candidato, encoding="utf-8", errors="replace") as arquivo:
                linhas = [l.rstrip("\n") for l in arquivo
                          if not l.startswith("input_libretro_device_p")]
            break
    linhas += ['%s = "%s"' % (c, tipos[c]) for c in sorted(tipos)]

    if os.path.isdir(PASTA_REMAP_PARTIDA):
        apagar_pasta_toda(PASTA_REMAP_PARTIDA)
    pasta_nucleo = os.path.join(PASTA_REMAP_PARTIDA, nome_nucleo)
    os.makedirs(pasta_nucleo, exist_ok=True)
    gravar_texto_atomico(os.path.join(pasta_nucleo, nome_jogo + ".rmp"), "\n".join(linhas) + "\n")
    return PASTA_REMAP_PARTIDA


def gravar_override(config, custo=None, extras=None, em_partida=False,
                    opcoes_de_nucleo=None, remapear=None, plataforma=None,
                    devolver_filtro=False, controles_ligados=None):
    """Monta o arquivo de configuracao extra que o RetroArch vai ler.

    'opcoes_de_nucleo': caminho de uma COPIA do arquivo de opcoes de nucleo
    (partida de 3+ jogadores no PS1/Saturn, que ligam o adaptador por opcao
    do nucleo). Sem ele, vale o arquivo de sempre.

    'plataforma' + 'devolver_filtro': devolve (arquivo, filtro de tela) --
    o filtro vai na linha de comando (--set-shader), porque o RetroArch
    ignora video_shader vindo de arquivo (ver graficos.filtro_de_tela)."""
    opcoes = opcoes_efetivas(config, custo, controles_ligados)

    if not em_partida:
        # Fora da partida, desligar a rede EXPLICITAMENTE. Nao basta deixar
        # a chave de fora: o RetroArch guarda a configuracao ao fechar,
        # entao uma partida pela internet deixaria o repasse ligado para o
        # proximo jogo, sozinho, sem motivo e com atraso a toa.
        opcoes.update({
            "netplay_use_mitm_server": "false",
            "netplay_public_announce": "false",
            "netplay_start_as_spectator": "false",
            "netplay_nat_traversal": "false",
        })

    if em_partida:
        # Partida a dois custa MUITO mais que jogar sozinho: o emulador
        # roda o jogo, guarda o estado para poder voltar quando a rede
        # atrasa, e as vezes reprocessa quadros ja passados. Numa maquina
        # modesta isso derruba os quadros por segundo pela metade.
        #
        # Aqui o ARENA abre mao do enfeite e fica com o que importa numa
        # partida: fluidez e resposta. Vale so enquanto a partida dura.
        opcoes.update({
            "video_shader_enable": "false",
            "video_smooth": "false",
            "video_threaded": "true",
            "run_ahead_enabled": "false",
            "rewind_enable": "false",
            "video_max_swapchain_images": "2",
            "audio_latency": "64",
            "audio_resampler_quality": "1",
            "menu_driver": "rgui",
            "video_font_enable": "true",
        })

    if grafico_original(config):
        # Resolucao nativa vale pouco se o RetroArch ainda desenha filtro
        # por cima. Aqui morre tudo o que sobra.
        opcoes.update({
            "video_shader_enable": "false",
            "video_smooth": "false",
            "video_scale_integer": "false",
            "video_threaded": "true",
            "video_black_frame_insertion": "0",
            "rewind_enable": "false",
            "run_ahead_enabled": "false",
            "audio_resampler_quality": "1",
            "audio_latency": "96",
            "savestate_thumbnail_enable": "false",
            "menu_driver": "rgui",
        })
    if config.get("ultra_desempenho"):
        opcoes.update(ULTRA_DESEMPENHO)

    if nivel_abaixo(config) == "minimo":
        # Bonecos de papelao: o computador atrasa mais vezes, e o pulo de
        # quadros dos nucleos olha a folga do som. Mais folga = som sem
        # picote. Vem DEPOIS do ultra de proposito: o ultra pede 32 ms (som
        # mais rapido), e no minimo o som que nao picota vale mais.
        opcoes["audio_latency"] = "128"

    if config.get("travar_teclas"):
        # Prende o teclado no jogo: Alt+Tab e a tecla Windows passam a ser
        # do jogo. O Esc para de abrir o menu enquanto isso estiver ligado
        # - por isso a tecla de escape abaixo, que liga e desliga na hora.
        opcoes["input_auto_game_focus"] = "1"
        opcoes["input_game_focus_toggle"] = "f9"

    if extras:
        opcoes.update(extras)

    for pasta in (PASTA_SAVES, PASTA_STATES, PASTA_CAPTURAS, PASTA_SISTEMA,
                  PASTA_CHEATS, PASTA_REMAPS, PASTA_CONTROLES, PASTA_CACHE):
        os.makedirs(pasta, exist_ok=True)

    # Saves, estados e capturas sempre dentro do ARENA: e o que torna a
    # pasta portatil de verdade.
    opcoes["savefile_directory"] = PASTA_SAVES
    opcoes["savestate_directory"] = PASTA_STATES
    opcoes["screenshot_directory"] = PASTA_CAPTURAS
    # A pasta das BIOS e' a do ARENA, a nao ser que a partida mande outra:
    # a ponte sem acento do Hatari (servidor\ponte_sem_acento.py) manda a
    # copia dela, numa pasta sem acento.
    opcoes["system_directory"] = (extras or {}).get("system_directory") or PASTA_SISTEMA
    opcoes["cheat_database_path"] = PASTA_CHEATS
    opcoes["input_remapping_directory"] = PASTA_REMAPS
    if remapear:
        try:
            pasta_remap = remapeamento_da_partida(opcoes, *remapear)
        except OSError as falha:
            pasta_remap = None
            print("[ARENA] Nao consegui gravar o tipo de controle das portas: %s" % falha)
        if pasta_remap:
            opcoes["input_remapping_directory"] = pasta_remap
    opcoes["joypad_autoconfig_dir"] = (PASTA_PERFIS_CONTROLE
                                       if os.path.isdir(PASTA_PERFIS_CONTROLE)
                                       else PASTA_CONTROLES)
    opcoes["playlist_directory"] = PASTA_DADOS
    opcoes["log_dir"] = PASTA_DADOS
    # As opcoes de cada nucleo (resolucao, filtro, BIOS, memory card, modo
    # modesto...) que o ARENA monta ficam em retroarch-core-options.cfg.
    # Achado real (revisao pos-auditoria, testes\teste_qual_opcao_de_nucleo_vale.py):
    # no padrao do RetroArch (global_core_options = false) quem vale e' o
    # arquivo retroarch\config\<Nucleo>\<Nucleo>.opt, e o do ARENA so era
    # lido na PRIMEIRA vez que o nucleo abria. Depois disso, todo ajuste do
    # ARENA era ignorado em silencio. Com isto, vale sempre o do ARENA.
    opcoes["global_core_options"] = "true"
    opcoes["core_options_path"] = opcoes_de_nucleo or graficos.ARQUIVO_OPCOES_CORE
    # Comandos pela rede SEMPRE desligados. Achado real (revisao
    # pos-auditoria): o retroarch.cfg estava com network_cmd_enable = "true"
    # (sobra de teste), e o RetroArch ficava esperando comandos em
    # 0.0.0.0:55355 -- conferido pelo Windows. Como o aluno libera o
    # retroarch.exe no Firewall para o Jogar Junto, um colega na mesma rede
    # poderia mandar QUIT (fechar o jogo), SAVE_STATE, LOAD_STATE... no
    # computador de outro. O ARENA nunca precisa disso.
    opcoes["network_cmd_enable"] = "false"
    # Sem isto, o RetroArch usa a pasta Temp do Windows pra descompactar
    # jogo em .zip - fora da pasta do ARENA, contra a regra de nunca
    # deixar nada fora dela.
    opcoes["cache_directory"] = PASTA_CACHE

    # Filtro de tela: so com o perfil (ou o aluno) pedindo, e so se este
    # console tiver filtro. Sem filtro, a chave vai "false": nada de filtro
    # velho salvo no menu do RetroArch aparecendo por cima.
    filtro = ""
    if opcoes.get("video_shader_enable") == "true":
        filtro = graficos.filtro_de_tela(plataforma)
        if not filtro:
            opcoes["video_shader_enable"] = "false"

    linhas = ["# Gerado pelo ARENA. Nao edite a mao: sera reescrito."]
    # Nenhum valor pode quebrar a linha nem fechar as aspas antes da hora:
    # seria outra opcao entrando escondida no emulador.
    linhas += ['%s = "%s"' % (c, str(opcoes[c]).replace('"', "'").replace("\r", " ").replace("\n", " "))
               for c in sorted(opcoes)]

    os.makedirs(PASTA_DADOS, exist_ok=True)
    gravar_texto_atomico(ARQUIVO_OVERRIDE, "\n".join(linhas) + "\n")
    if devolver_filtro:
        return ARQUIVO_OVERRIDE, filtro
    return ARQUIVO_OVERRIDE


# ---------------------------------------------------------------------------
# BLOCO 5 - Catalogo, com cache em memoria
# ---------------------------------------------------------------------------
# Ler pasta em pen drive e lento. Estes caches evitam consultar o disco a
# cada clique. Duram poucos segundos, entao mudanca feita a mao aparece
# rapido, e o botao Atualizar lista sempre forca a releitura.

VALIDADE_CACHE = 15.0 if ECONOMICO else 4.0
_cache = {"catalogo": None, "plataformas": (0.0, None),
          "manifesto": (0.0, None), "resposta": (0.0, None)}


def carregar_catalogo():
    """Le consoles.json uma vez e guarda na memoria (nunca muda em uso)."""
    if _cache["catalogo"] is None:
        with open(ARQUIVO_CONSOLES, "r", encoding="utf-8") as arquivo:
            _cache["catalogo"] = json.load(arquivo)["plataformas"]
    return _cache["catalogo"]


# Uma releitura dos jogos por vez. Separada da TRAVA_CACHE de proposito:
# achado da auditoria 3 (08/10/2026, testes\teste_tela_responde_indexando.py)
# -- a releitura segurava a TRAVA_CACHE do comeco ao fim, e essa trava e' a
# mesma da configuracao, que quase toda rota le. Enquanto o ARENA relia
# 5.000 jogos (7 s no Ryzen, ~16 s no Celeron), a tela inteira esperava.
TRAVA_RELEITURA = threading.Lock()


def manifesto(forcar=False):
    """Catalogo de jogos, com cache curto em memoria."""
    with TRAVA_CACHE:
        idade, salvo = _cache["manifesto"]
        if not forcar and salvo and (time.time() - idade) < VALIDADE_CACHE:
            return salvo
    with TRAVA_RELEITURA:
        if not forcar:
            # Quem esperou a releitura de outro pedido usa o resultado dela.
            with TRAVA_CACHE:
                idade, salvo = _cache["manifesto"]
                if salvo and (time.time() - idade) < VALIDADE_CACHE:
                    return salvo
        resultado = indexador.indexar(forcar=forcar)
        with TRAVA_CACHE:
            _cache["manifesto"] = (time.time(), resultado)
        return resultado


def contar_arquivos_sistema():
    """Conta arquivos na pasta system, sem listar nem nomear nenhum."""
    try:
        return sum(
            1 for entrada in os.scandir(PASTA_SISTEMA)
            if entrada.is_file() and not entrada.name.lower().endswith(".txt")
        )
    except OSError:
        return 0


def avaliar_plataformas(forcar=False):
    """Para cada plataforma, diz se esta pronta e, se nao, por que."""
    with TRAVA_CACHE:
        idade, salvo = _cache["plataformas"]
        if not forcar and salvo and (time.time() - idade) < VALIDADE_CACHE:
            return salvo

    tem_sistema = contar_arquivos_sistema() > 0

    try:
        cores = {e.name.lower() for e in os.scandir(PASTA_CORES) if e.is_file()}
    except OSError:
        cores = set()

    resultado = []
    for plataforma in carregar_catalogo():
        core_ok = plataforma["core"].lower() in cores
        precisa_sistema = plataforma["arquivos_sistema"] > 0
        caminho_externo, dados_externo = graficos.achar_externo(plataforma)

        # Maquina fraca NAO impede mais de jogar. Antes, console pesado
        # sumia da lista em PC fraco - o aluno nem sabia que existia. Agora
        # ele abre normal e a etiqueta vermelha "Capenga" avisa antes.
        # Quem quer tentar, tenta. O ARENA so nao mente sobre o resultado.
        falta_externo = (graficos.falta_para_o_externo(dados_externo["nome"], caminho_externo)
                         if caminho_externo else "")
        if caminho_externo and falta_externo:
            # Emulador de fora instalado, mas sem o que ele precisa para
            # abrir um jogo (BIOS do PS2, firmware do PS3): cartao amarelo
            # com o motivo, em vez de "pronto" que so falha depois.
            estado = "falta_sistema"
            motivo = falta_externo
        elif caminho_externo:
            # Com o emulador de fora instalado, nem nucleo nem arquivo de
            # sistema do RetroArch importam: quem manda e ele.
            estado = "pronta"
            motivo = ""
        elif not core_ok:
            externo_obrigatorio = (plataforma.get("externo") or {}).get("obrigatorio")
            if externo_obrigatorio and not plataforma["core"]:
                # Plataforma sem nucleo nenhum no RetroArch (PS3, Xbox 360):
                # nao faz sentido mandar "baixar pelo RetroArch" algo que
                # nao existe. O unico caminho e o emulador de fora.
                estado = "falta_externo"
                motivo = ("%s obrigatorio. Baixe e coloque em emuladores\\%s." %
                          (plataforma["externo"]["nome"], plataforma["externo"]["pasta"]))
            else:
                estado = "sem_core"
                motivo = "Núcleo não instalado. Baixe pelo RetroArch."
        elif precisa_sistema and not tem_sistema and not (
                plataforma.get("core_sem_bios", "").lower() in cores):
            # (Com um nucleo que imita a BIOS -- o PS1 pelo PCSX ReARMed --,
            # o console abre mesmo sem BIOS nenhuma.)
            estado = "falta_sistema"
            motivo = ("Precisa da BIOS do console. Veja o que falta em Ajustes → Emuladores → BIOS "
                      "dos consoles (a pasta é a BIOS, na pasta do ARENA).")
        elif bios.falta_para_o_console(plataforma["id"], PASTA_SISTEMA):
            # Sega CD e Saturn nao abrem jogo nenhum sem a BIOS deles. Antes
            # (ate 03/10/2026) so ficavam "falta" com a pasta system VAZIA:
            # com a BIOS do PS1 la, apareciam prontos e o jogo nao abria.
            # Desde a auditoria 3 (Fase 5), tambem os que so abrem com a BIOS
            # do catalogo (ColecoVision, MSX, 3DO, Intellivision, PC-FX, CD-i,
            # Odyssey 2): o ColecoVision abria com a tela preta, calado.
            estado = "falta_sistema"
            motivo = bios.falta_para_o_console(plataforma["id"], PASTA_SISTEMA)
        else:
            estado = "pronta"
            motivo = ""

        classe = classificar(plataforma.get("custo", 3))      # perfil grafico
        etiqueta = classificar_plataforma(plataforma)          # selo do cartao
        resultado.append({
            "id": plataforma["id"],
            "nome": plataforma["nome"],
            "descricao": plataforma["descricao"],
            "peso": plataforma["peso"],
            "pasta": plataforma["pasta"],
            "custo": plataforma.get("custo", 3),
            "jogadores_max": plataforma.get("jogadores_max", 2),
            "netplay": plataforma.get("netplay", True),
            "netplay_motivo": plataforma.get("netplay_motivo", ""),
            "estado": estado,
            "motivo": motivo,
            # Como vai rodar nesta maquina (medido): verde, azul, vermelho
            # ou cinza (nao abre). Ver classificar_plataforma().
            "classe": etiqueta["chave"],
            "classe_rotulo": etiqueta["rotulo"],
            "classe_cor": etiqueta["cor"],
            "classe_detalhe": etiqueta["detalhe"],
            "emulador": (dados_externo["nome"] if caminho_externo
                         else "RetroArch"),
            # Partida a dois e coisa do RetroArch. Emulador de fora tem
            # rede propria, entao a tela nem oferece o botao - melhor que
            # deixar o aluno clicar e receber um erro no meio da aula.
            "aceita_partida": not caminho_externo,
            "motivo_sem_partida": (
                "Esta plataforma usa o %s, que tem rede própria. "
                "Jogar junto só funciona pelo RetroArch."
                % dados_externo["nome"] if caminho_externo else ""),
            "externo_sugerido": (dados_externo["nome"] if dados_externo
                                 and not caminho_externo else None),
            "perfil_sugerido": PERFIS_GRAFICOS[classe["perfil"]]["rotulo"],
        })

    with TRAVA_CACHE:
        _cache["plataformas"] = (time.time(), resultado)
    return resultado


def montar_catalogo():
    """Monta a resposta de /api/catalogo e guarda JA SERIALIZADA.

    Sem este cache, cada acesso remontava 4 mil dicionarios e os convertia
    em JSON de novo. Com a sala inteira abrindo o ARENA ao mesmo tempo,
    isso vira trabalho repetido a toa: a resposta e identica para todos.
    Guardar os bytes prontos derruba o custo para uma copia de memoria.
    """
    with TRAVA_CACHE:
        idade, salvo = _cache["resposta"]
        if salvo and (time.time() - idade) < VALIDADE_CACHE:
            return salvo

    por_id = {p["id"]: p for p in avaliar_plataformas()}

    # Grupo dos jogos que ainda nao estao em pasta de console nenhum.
    # Aparece primeiro na lista, para o aluno resolver e seguir.
    por_id[indexador.SEM_PASTA] = {
        "id": indexador.SEM_PASTA,
        "nome": "Precisa escolher o console",
        "descricao": "Arraste para a pasta do console certo, no lado esquerdo.",
        "peso": "leve", "pasta": "", "custo": 1,
        "estado": "sem_pasta",
        "motivo": "Este arquivo serve a mais de um console. Diga qual e.",
        "classe": "ajustes", "classe_rotulo": "", "classe_cor": "azul",
        "classe_detalhe": "", "perfil_sugerido": "",
        "emulador": "-", "externo_sugerido": None,
    }

    # Nao copiar cada jogo so para carimbar o estado da plataforma nele.
    # Com doze mil jogos, essa copia sozinha custava dezenas de MB e um
    # JSON bem maior. A tela ja recebe a lista de plataformas: basta ela
    # cruzar pelo 'plataforma' que cada jogo ja carrega.
    jogos = []
    problemas = ler_problemas()
    for jogo in manifesto()["jogos"]:
        if jogo["plataforma"] not in por_id:
            continue
        problema = problemas.get(jogo["id"])
        if problema and problema.get("assinatura") == assinatura_do_arquivo(
                os.path.join(RAIZ, jogo["arquivo"])):
            jogo = dict(jogo)
            jogo["avisos"] = list(jogo.get("avisos") or []) + [
                {"texto": "Da última vez: " + problema["texto"], "ultima_vez": True}]
        if jogo.get("capas"):
            # A tela nunca le o disco direto: pede a arte ao servidor, que
            # confere se o caminho esta mesmo dentro da pasta de jogos.
            jogo = dict(jogo)
            jogo["capa_urls"] = ["/api/capa?arquivo=" + urllib.parse.quote(c)
                                 for c in jogo["capas"]]
        jogos.append(jogo)

    corpo = json.dumps({
        "plataformas": list(por_id.values()),
        "jogos": jogos,
        "total": len(jogos),
    }, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    with TRAVA_CACHE:
        _cache["resposta"] = (time.time(), corpo)
    return corpo


def limpar_caches():
    with TRAVA_CACHE:
        _cache["plataformas"] = (0.0, None)
        _cache["manifesto"] = (0.0, None)
        _cache["resposta"] = (0.0, None)


# Capas para todos os jogos sem capa (botao "Buscar capas que faltam",
# pedido do Rafael em 02/10/2026). Uma busca por vez, em segundo plano; a
# lista e' refeita UMA vez, no fim (refazer a cada capa custava segundos
# cada uma no notebook-alvo).
BUSCA_DE_CAPAS = {"rodando": False, "total": 0, "feitos": 0, "achados": 0, "atual": "", "parar": False}
TRAVA_CAPAS = threading.Lock()


def situacao_das_capas():
    with TRAVA_CAPAS:
        return dict(BUSCA_DE_CAPAS)


def buscar_capas_que_faltam():
    """Tenta a capa de cada jogo que nao tem (roda em segundo plano)."""
    try:
        jogos = [j for j in manifesto().get("jogos", []) if not j.get("capas")]
        with TRAVA_CAPAS:
            BUSCA_DE_CAPAS.update(total=len(jogos), feitos=0, achados=0)
        for jogo in jogos:
            with TRAVA_CAPAS:
                if BUSCA_DE_CAPAS["parar"]:
                    break
                BUSCA_DE_CAPAS["atual"] = jogo["titulo"]
            nome_base = (jogo.get("nome_banco")
                         or os.path.splitext(os.path.basename(jogo["arquivo"]))[0])
            try:
                achou, _motivo = capas_online.buscar_e_baixar(
                    jogo["plataforma"], jogo["titulo"], nome_base,
                    caminho_jogo=os.path.join(RAIZ, jogo["arquivo"]),
                    com_internet=bool(VIGIA["internet"]))
            except Exception:     # um jogo estranho nao para a busca dos outros
                achou = False
            with TRAVA_CAPAS:
                BUSCA_DE_CAPAS["feitos"] += 1
                BUSCA_DE_CAPAS["achados"] += 1 if achou else 0
        if situacao_das_capas()["achados"]:
            limpar_caches()
            manifesto(forcar=True)
    finally:
        with TRAVA_CAPAS:
            BUSCA_DE_CAPAS.update(rodando=False, atual="", parar=False)


def achar_jogo(jogo_id):
    return next((j for j in manifesto()["jogos"] if j["id"] == jogo_id), None)


def nucleo_das_pastas(jogo):
    """'Snes9x': a subpasta do nucleo deste jogo dentro de retroarch\\saves,
    states e cheats -- onde o RetroArch guarda tudo dele (servidor\\cheats.py).
    None para console sem nucleo do RetroArch (emulador de fora)."""
    plataforma = next((p for p in carregar_catalogo() if p["id"] == jogo.get("plataforma")), None)
    return cheats.nome_do_nucleo((plataforma or {}).get("core"), os.path.join(PASTA_RETROARCH, "info"))


def jogo_aberto_agora(jogo):
    """Este jogo esta aberto no emulador agora?"""
    with TRAVA_JOGO:
        return JOGO_EM_ANDAMENTO["ativo"] and JOGO_EM_ANDAMENTO.get("id") == jogo["id"]


# ---------------------------------------------------------------------------
# BLOCO 6 - Execucao do jogo
# ---------------------------------------------------------------------------

def nome_curto_do_core(arquivo_core):
    """'swanstation_libretro.dll' -> 'swanstation'."""
    return os.path.basename(arquivo_core).replace("_libretro.dll", "").lower()


ARQUIVO_QUEDAS = os.path.join(PASTA_DADOS, "fechamentos.json")
# Por que cada jogo nao abriu da ultima vez (servidor\motivo_do_erro.py).
ARQUIVO_PROBLEMAS = os.path.join(PASTA_DADOS, "problemas_dos_jogos.json")
PROBLEMAS_GUARDADOS = 50
# O do ultimo jogo aberto, para a tela mostrar assim que o aluno volta.
ULTIMO_PROBLEMA = {}


# ---------------------------------------------------------------------------
# Conquistas
# ---------------------------------------------------------------------------
# Nada de servico externo nem de conta: o ARENA ja guarda pontuacao e tempo
# de jogo. As conquistas sao leitura desses numeros, calculadas na hora.
#
# Foram escolhidas para premiar CONSTANCIA e VARIEDADE, nao so pontuacao -
# senao o mesmo aluno ganha tudo e o resto desiste.

CONQUISTAS = [
    ("primeiro_recorde", "Primeiro recorde",
     "Registrou a primeira pontuacao"),
    ("dez_recordes", "Dez recordes",
     "Registrou dez pontuacoes"),
    ("explorador", "Explorador",
     "Jogou em tres consoles diferentes"),
    ("colecionador", "Colecionador",
     "Jogou em cinco consoles diferentes"),
    ("uma_hora", "Uma hora de jogo",
     "Somou uma hora jogando"),
    ("maratonista", "Maratonista",
     "Somou cinco horas jogando"),
    ("persistente", "Persistente",
     "Voltou ao mesmo jogo dez vezes"),
    ("primeiro_lugar", "Primeiro lugar",
     "Tem o melhor recorde de algum jogo"),
]


def montar_conquistas():
    """Le o banco e diz quem desbloqueou o que."""
    with banco() as conexao:
        linhas = conexao.execute(
            "SELECT apelido, COUNT(*), COUNT(DISTINCT jogo_id) "
            "FROM placar GROUP BY apelido").fetchall()
        tempos = dict(conexao.execute(
            "SELECT apelido, COALESCE(SUM(segundos), 0) FROM sessao "
            "WHERE encerrada = 1 GROUP BY apelido").fetchall())
        repeticoes = {}
        for apelido, quantas in conexao.execute(
                "SELECT apelido, MAX(vezes) FROM (SELECT apelido, jogo_id, "
                "COUNT(*) AS vezes FROM sessao GROUP BY apelido, jogo_id) "
                "GROUP BY apelido").fetchall():
            repeticoes[apelido] = quantas or 0
        lideres = set()
        for apelido, in conexao.execute(
                "SELECT apelido FROM (SELECT jogo_id, apelido, "
                "RANK() OVER (PARTITION BY jogo_id ORDER BY MAX(pontos) DESC) "
                "AS posicao FROM placar GROUP BY jogo_id, apelido) "
                "WHERE posicao = 1").fetchall():
            lideres.add(apelido)

    jogadores = []
    for apelido, quantos, consoles in sorted(linhas, key=lambda linha: linha[0]):
        segundos = tempos.get(apelido, 0)
        ganhou = {
            "primeiro_recorde": quantos >= 1,
            "dez_recordes": quantos >= 10,
            "explorador": consoles >= 3,
            "colecionador": consoles >= 5,
            "uma_hora": segundos >= 3600,
            "maratonista": segundos >= 5 * 3600,
            "persistente": repeticoes.get(apelido, 0) >= 10,
            "primeiro_lugar": apelido in lideres,
        }
        jogadores.append({
            "apelido": apelido,
            "quantas": sum(1 for v in ganhou.values() if v),
            "total": len(CONQUISTAS),
            "conquistas": [
                {"id": chave, "nome": nome, "descricao": descricao,
                 "ganhou": ganhou.get(chave, False)}
                for chave, nome, descricao in CONQUISTAS
            ],
        })

    jogadores.sort(key=lambda j: (-j["quantas"], j["apelido"].lower()))
    return {"jogadores": jogadores, "total": len(CONQUISTAS)}


def impressao_do_jogo(jogo):
    """Uma marca curta do arquivo, para os dois lados compararem.

    A partida a dois exige o MESMO arquivo nos dois computadores. Titulo
    parecido nao basta: versao americana e europeia, com e sem cabecalho,
    revisao 1 e revisao 2 sao arquivos diferentes, e o RetroArch recusa a
    conexao sem dizer o porque.

    Le so o comeco e o fim do arquivo, mais o tamanho. Dois arquivos
    diferentes praticamente nunca batem nos tres.
    """
    import hashlib

    caminho = os.path.join(RAIZ, jogo["arquivo"])
    try:
        tamanho = os.path.getsize(caminho)
        with open(caminho, "rb") as arquivo:
            comeco = arquivo.read(65536)
            if tamanho > 131072:
                arquivo.seek(-65536, os.SEEK_END)
                fim = arquivo.read(65536)
            else:
                fim = b""
    except OSError:
        return None

    marca = hashlib.sha1(comeco + fim + str(tamanho).encode()).hexdigest()[:16]
    return {"titulo": jogo["titulo"], "tamanho": tamanho, "marca": marca}


def registrar_fechamento(jogo, codigo, comando):
    """Anota quando um jogo fecha sozinho.

    O aluno relata 'o jogo fechou do nada' e nao ha o que investigar. Aqui
    fica o registro: qual jogo, qual emulador, que codigo de saida o
    programa devolveu e quando foi.
    """
    try:
        try:
            with open(ARQUIVO_QUEDAS, "r", encoding="utf-8") as arquivo:
                lista = json.load(arquivo)
            if not isinstance(lista, list):
                lista = []
        except (OSError, ValueError):
            lista = []

        lista.append({
            "quando": agora_utc(),
            "jogo": jogo.get("titulo", ""),
            "plataforma": jogo.get("plataforma_nome", ""),
            "emulador": (jogo.get("externo", {}).get("dados", {}).get("nome")
                         if jogo.get("externo") else "RetroArch"),
            "codigo_saida": codigo,
            "programa": os.path.basename(comando[0]) if comando else "",
        })
        gravar_texto_atomico(
            ARQUIVO_QUEDAS,
            json.dumps(lista[-30:], ensure_ascii=False, indent=1))
        print("[ARENA] %s fechou sozinho (codigo %s). Registrado."
              % (jogo.get("titulo", "o jogo"), codigo))
    except Exception:
        pass


def assinatura_do_arquivo(caminho):
    """Tamanho e data do arquivo: trocou o arquivo, o motivo antigo some."""
    try:
        info = os.stat(caminho)
        return "%d|%d" % (info.st_size, int(info.st_mtime))
    except OSError:
        return ""


def ler_problemas():
    """{id do jogo: {"texto", "quando", "assinatura"}} -- vazio se nao ha."""
    try:
        with open(ARQUIVO_PROBLEMAS, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except (OSError, ValueError):
        return {}
    if not isinstance(dados, dict):
        return {}
    return {k: v for k, v in dados.items()
            if isinstance(v, dict) and isinstance(v.get("texto"), str)}


def anotar_motivo_do_erro(jogo, desde, partida=None):
    """Depois do jogo: le o registro DESTA partida e guarda por que ele nao
    abriu -- ou apaga o motivo antigo, se agora abriu.

    Achado de 02/10/2026: o Rafael abriu o KOF 2002 quatro vezes; nas quatro
    o MAME escreveu no registro o que faltava, e o ARENA nao dizia nada (o
    RetroArch so mostra "Falha ao carregar o conteudo"). Nunca atrapalha o
    resto: qualquer falha aqui e' ignorada.

    Jogar Junto (auditoria 3): quem tentou ENTRAR na partida de um colega e
    nao conseguiu ve, ao voltar, o porque (partida cheia ou rede barrando).
    Isso nao marca o jogo como "com problema": o jogo abre."""
    try:
        registro = motivo_do_erro.registro_da_partida(PASTA_DADOS, desde)
        if not registro:
            return None
        texto_do_registro = motivo_do_erro.ler(registro)
        if partida and not partida.get("hospedar") and not partida.get("assistir"):
            recado = motivo_do_erro.motivo_da_partida(
                texto_do_registro, (jogo.get("ligacao") or {}).get("jogadores"))
            if recado:
                ULTIMO_PROBLEMA.clear()
                ULTIMO_PROBLEMA.update({"jogo_id": jogo["id"], "titulo": jogo.get("titulo", ""),
                                        "texto": recado})
                print("[ARENA] Jogar junto: %s" % recado)
                return None
        caminho = os.path.join(RAIZ, jogo["arquivo"])
        resultado = motivo_do_erro.analisar(texto_do_registro, caminho, jogo.get("core", ""))
        problemas = ler_problemas()
        if resultado and resultado.get("discos"):
            # Faltou o disco (.chd) de um fliperama: a pasta onde ele vai
            # (Arcade\kinst, ao lado do kinst.zip) passa a existir, com um
            # LEIA dizendo o que por la -- guia quem nao sabe onde fica.
            if arrumar.pasta_do_disco(caminho, resultado["discos"], PASTA_JOGOS):
                resultado["texto"] += " O ARENA criou essa pasta, com um LEIA dentro."
        if resultado:
            problemas[jogo["id"]] = {"texto": resultado["texto"], "quando": agora_utc(),
                                     "assinatura": assinatura_do_arquivo(caminho)}
            ULTIMO_PROBLEMA.clear()
            ULTIMO_PROBLEMA.update({"jogo_id": jogo["id"], "titulo": jogo.get("titulo", ""),
                                    "texto": resultado["texto"]})
            print("[ARENA] %s nao abriu: %s" % (jogo.get("titulo", "o jogo"), resultado["texto"]))
        elif jogo["id"] in problemas:
            del problemas[jogo["id"]]          # agora abriu: o motivo antigo sai
        else:
            return None
        guardados = sorted(problemas.items(), key=lambda item: item[1].get("quando", ""))
        gravar_texto_atomico(ARQUIVO_PROBLEMAS, json.dumps(
            dict(guardados[-PROBLEMAS_GUARDADOS:]), ensure_ascii=False, indent=1))
        with TRAVA_CACHE:
            _cache["resposta"] = (0.0, None)   # o cartao mostra o motivo novo
        return resultado
    except Exception as falha:   # noqa: BLE001 -- explicar e' bonus, nunca derruba
        print("[ARENA] Nao consegui ler o motivo do jogo: %s" % falha)
        return None


def ler_fechamentos():
    try:
        with open(ARQUIVO_QUEDAS, "r", encoding="utf-8") as arquivo:
            lista = json.load(arquivo)
        return lista[-10:] if isinstance(lista, list) else []
    except (OSError, ValueError):
        return []


def jogadores_pedidos(plataforma, jogo):
    """Quantos jogadores o JOGO aceita (antes de ver o que o nucleo deixa).

    Vem do indice (indexador), que le o dados\\jogadores.txt do professor --
    o MESMO numero que o cartao mostra. Indice antigo, de antes do arquivo
    existir: o que o ARENA ja sabe (jogos testados, lista de Multitap = 5,
    numero do console, senao 2 -- jogadores.numero_sem_regra)."""
    if jogo.get("jogadores_do_jogo"):
        return int(jogo["jogadores_do_jogo"])
    return jogadores.numero_sem_regra(plataforma, jogo.get("titulo"))


def executar_jogo(jogo, apelido, config, custo=None, partida=None):
    """Abre o RetroArch, espera fechar e grava a sessao.

    Roda em thread separada para o servidor continuar respondendo enquanto
    o aluno joga.
    """
    sessao_uuid = uuid.uuid4().hex

    # Definidos antes do 'try': se gravar as opcoes falhar (pen drive
    # protegido...), o jogo ainda abre, so sem esses ajustes -- em vez de
    # cair mais abaixo por falta destas variaveis (achado na revisao).
    extras_controle = {}
    jogadores_controle = 2
    jogadores_ligacao = int((jogo.get("ligacao") or {}).get("jogadores") or 0)

    # Ajuste fino de imagem do emulador deste jogo (resolucao interna,
    # filtro de textura, mipmap, carregar CD para a memoria).
    try:
        extras_core = {}
        nome_core = nome_curto_do_core(jogo.get("core", ""))
        # A MESMA BIOS toda vez: e o que faz a data, a hora e os icones do
        # memory card continuarem de uma sessao para a outra.
        extras_core.update(graficos.opcoes_de_bios(
            nome_core, config.get("bios", {}).get(jogo["plataforma"])))
        extras_core.update(graficos.opcoes_de_memory_card(
            PASTA_SAVES, jogo["plataforma"]))
        # Avisa o console de que o controle tem analogico. Sem isto, no
        # PlayStation os dois analogicos ficam mudos.
        escolhas = config.get("perfil_controle", {}).get(jogo["plataforma"], {})
        jogadores_controle = int(config.get("avancado", {}).get("input_max_users", 2) or 2)
        # Partida de 3+ (Fase B do multitap): o tipo de controle vai para
        # TODOS os jogadores, nao so para os da configuracao (2). Achado na
        # revisao: sem isto, numa partida de 4 no Dreamcast ou de 5 no PS1
        # os jogadores 3 em diante ficavam sem o 517 -- analogico mudo, o
        # mesmo defeito antigo do PS1. Com 1 ou 2, a conta e' a de sempre.
        if jogadores_ligacao > 2:
            jogadores_controle = max(jogadores_controle, jogadores_ligacao)
        extras_controle = controles.opcoes_do_console(
            jogo["plataforma"],
            jogadores=jogadores_controle,
            usar_analogico=escolhas.get("analogico_esq", True),
            vibracao=escolhas.get("vibracao", True),
            dispositivo_extra=escolhas.get("extra"))
        # opcoes_do_console cobre ate 4 portas; o 5o jogador em diante (PS1 e
        # Saturn com adaptador) recebe o mesmo tipo de controle do 1o.
        for n in range(5, jogadores_ligacao + 1):
            for chave in ("input_libretro_device_p%d", "input_player%d_analog_dpad_mode"):
                if chave % 1 in extras_controle:
                    extras_controle[chave % n] = extras_controle[chave % 1]
        graficos.gravar_opcoes_dos_nucleos(
            CAPACIDADE["nota"], extras_core, CAPACIDADE.get("nota_gpu"),
            modesto=grafico_original(config), abaixo=nivel_abaixo(config))
    except OSError as falha:
        print("[ARENA] Nao consegui gravar as opcoes de imagem: %s" % falha)

    caminho_jogo = os.path.join(RAIZ, jogo["arquivo"])
    pasta_trabalho = PASTA_RETROARCH
    # Leva de volta o disquete que o jogo gravou na pasta sem acento (so o
    # Hatari usa: servidor\ponte_sem_acento.py).
    devolver_ponte = None

    if jogo.get("externo"):
        # Emulador de fora: o RetroArch fica de lado nesta plataforma.
        # Partida a dois e save state do ARENA nao valem aqui - quem
        # cuida disso passa a ser o proprio emulador.
        comando = graficos.comando_externo(
            jogo["externo"]["caminho"], jogo["externo"]["dados"], caminho_jogo)
        pasta_trabalho = os.path.dirname(jogo["externo"]["caminho"])

        # O PCSX2 tem tela propria, mas le a configuracao antes de abrir.
        # O ARENA escreve o controle ali: dois analogicos, direcional
        # junto, vibracao e as mesmas teclas do resto do ARENA.
        if jogo["externo"]["dados"]["nome"] == "PCSX2":
            bios_copiada = graficos.preparar_bios_pcsx2(
                jogo["externo"]["caminho"], PASTA_SISTEMA)
            if bios_copiada:
                print("[ARENA] BIOS do PS2 copiada para o PCSX2: %s" % bios_copiada)
            try:
                cartoes_ps2 = graficos.preparar_portatil_pcsx2(jogo["externo"]["caminho"])
            except OSError as falha:
                cartoes_ps2 = ("Mcd001.ps2", "Mcd002.ps2")
                print("[ARENA] Nao consegui deixar o PCSX2 portatil: %s" % falha)
            preset = config.get("preset_grafico_externo", "automatico")
            escrito = graficos.escrever_config_pcsx2(
                jogo["externo"]["caminho"],
                ultra=bool(config.get("ultra_desempenho")),
                nota=CAPACIDADE["nota"], nota_gpu=CAPACIDADE.get("nota_gpu"),
                modesto=grafico_original(config), abaixo=nivel_abaixo(config),
                preset=None if preset == "automatico" else preset,
                jogadores=jogo.get("jogadores_max", 2),
                controles_xinput=controles.controles_xinput(),
                cartoes=cartoes_ps2,
                integrada=bool(MAQUINA["gpu"].get("integrada", True)),
                motor=config.get("motor_ps2", "automatico"))
            if escrito:
                print("[ARENA] Controle e qualidade do PCSX2 configurados "
                      "(%s jogadores)." % jogo.get("jogadores_max", 2))

            plataforma_ps2 = next((p for p in carregar_catalogo()
                                   if p["id"] == jogo.get("plataforma")), None)
            if plataforma_ps2 and graficos.jogo_tem_system_link_ps2(
                    plataforma_ps2, jogo["titulo"]):
                rede = graficos.escrever_config_rede_ps2(jogo["externo"]["caminho"])
                if rede and rede["com_driver"]:
                    print("[ARENA] Rede do PS2 (system link) configurada "
                         "pelo adaptador %s." % rede["adaptador"])
                elif rede:
                    print("[ARENA] Rede do PS2 configurada so pra ENTRAR "
                         "(sem o driver Npcap, não dá pra hospedar).")

        # Dolphin (GameCube e Wii): pasta portatil e controles de 4 jogadores
        # -- XInput na ordem, teclado no primeiro jogador sem controle.
        elif jogo["externo"]["dados"]["nome"] == "Dolphin":
            # Wii ou GameCube: pelo proprio disco; sem resposta, pela pasta.
            console = graficos.console_do_disco_dolphin(caminho_jogo) or (
                "wii" if "wii" in jogo["arquivo"].lower() else "gamecube")
            preset = config.get("preset_grafico_externo", "automatico")
            pasta = graficos.escrever_config_dolphin(
                jogo["externo"]["caminho"], controles.controles_xinput(),
                console=console,
                nota=CAPACIDADE["nota"], nota_gpu=CAPACIDADE.get("nota_gpu"),
                modesto=grafico_original(config), abaixo=nivel_abaixo(config),
                ultra=bool(config.get("ultra_desempenho")),
                preset=None if preset == "automatico" else preset)
            if pasta:
                print("[ARENA] Controles e imagem do Dolphin configurados (%s)."
                      % ("Wii" if console == "wii" else "GameCube"))

        # Xenia e RPCS3: mesma ideia do PCSX2 acima - video, controles (o
        # teclado no primeiro jogador sem controle) e, no Xenia, a placa
        # (Vulkan: o Direct3D 12 derrubava a placa - ver placa_do_xenia).
        elif jogo["externo"]["dados"]["nome"] == "Xenia":
            plataforma_360 = next((p for p in carregar_catalogo()
                                   if p["id"] == jogo.get("plataforma")), None)
            externo_360 = (plataforma_360 or {}).get("externo") or {}
            if (plataforma_360 and externo_360.get("executavel_netplay") and
                    graficos.jogo_tem_netplay_xbox360(plataforma_360, jogo["titulo"])):
                caminho_netplay = os.path.join(
                    os.path.dirname(jogo["externo"]["caminho"]),
                    externo_360["executavel_netplay"])
                if os.path.isfile(caminho_netplay):
                    jogo["externo"]["caminho"] = caminho_netplay
                    comando = graficos.comando_externo(
                        caminho_netplay, jogo["externo"]["dados"], caminho_jogo)
                    ligou = graficos.escrever_config_netplay_xbox360(caminho_netplay)
                    if ligou:
                        print("[ARENA] Rede do Xbox 360 (Systemlink) ligada - "
                             "sem precisar de driver nenhum.")

            preset = config.get("preset_grafico_externo", "automatico")
            escrito = graficos.escrever_config_xenia(
                jogo["externo"]["caminho"], CAPACIDADE["nota"],
                CAPACIDADE.get("nota_gpu"),
                modesto=grafico_original(config),
                ultra=bool(config.get("ultra_desempenho")),
                preset=None if preset == "automatico" else preset,
                controles_xinput=controles.controles_xinput(),
                placa=graficos.placa_do_xenia(plataforma_360 or {}, jogo["titulo"]))
            if escrito:
                print("[ARENA] Video e teclado do Xenia configurados.")
        elif jogo["externo"]["dados"]["nome"] == "RPCS3":
            preset = config.get("preset_grafico_externo", "automatico")
            escrito = graficos.escrever_config_rpcs3(
                jogo["externo"]["caminho"], CAPACIDADE["nota"],
                CAPACIDADE.get("nota_gpu"),
                modesto=grafico_original(config), abaixo=nivel_abaixo(config),
                ultra=bool(config.get("ultra_desempenho")),
                preset=None if preset == "automatico" else preset)
            if escrito:
                print("[ARENA] Video do RPCS3 configurado.")
            if graficos.escrever_controles_rpcs3(jogo["externo"]["caminho"],
                                                 controles.controles_xinput()):
                print("[ARENA] Controles do RPCS3 configurados.")
            # Segue a chave nos dois sentidos: desligada, o ARENA desliga o
            # RPCN que alguem tenha ligado pela tela do RPCS3 (ver
            # graficos.escrever_config_rpcn - caso do Minecraft).
            rpcn = bool(config.get("rpcn_ativo"))
            if graficos.escrever_config_rpcn(jogo["externo"]["caminho"], ligado=rpcn):
                print("[ARENA] RPCN %s." % ("ligado (precisa de conta ja criada "
                                            "pela tela do RPCS3)" if rpcn else "desligado"))

        print("[ARENA] Abrindo pelo %s" % jogo["externo"]["dados"]["nome"])
    else:
        # Jogo de varios discos: a lista .m3u (indexador.agrupar_discos).
        # Na partida a dois, nao: abre o disco 1 como sempre (o caminho
        # testado). Trocar de disco no meio dessincroniza os dois lados, e
        # jogo de varios discos e' quase sempre de um jogador so (RPG).
        if not partida:
            caminho_jogo = lista_de_discos(jogo, caminho_jogo)
            # Codigo de cheat cadastrado antes da auditoria 3 ficava num
            # lugar em que o RetroArch nao procura (servidor\cheats.py): vai
            # para o lugar certo antes de abrir. Na partida a dois o
            # RetroArch nao usa cheat nenhum.
            try:
                if cheats.levar_do_lugar_antigo(jogo, cheats.nome_do_nucleo(jogo.get("core"))):
                    print("[ARENA] Codigos de cheat deste jogo levados para a pasta que o RetroArch le.")
            except OSError as falha:
                print("[ARENA] Nao consegui levar os codigos de cheat para a pasta certa: %s" % falha)
        extra = dict(partida["opcoes"]) if partida else None
        # Mais de 2 jogadores (graficos.jogadores_do_jogo, calculado no
        # /api/jogar). Entra POR ULTIMO, depois das opcoes de controle:
        # achado real (Fase B do multitap) -- as opcoes de controle
        # escreviam input_libretro_device_p2 = "1" por cima do "257" do
        # Multitap, e o adaptador do Super Bomberman nunca chegava ao
        # RetroArch. Com 1 ou 2 jogadores, 'ligacao' vem vazia e nada muda.
        ligacao = jogo.get("ligacao") or {}
        opcoes_jogo = dict(extra or {}, **extras_controle)
        opcoes_jogo.update(ligacao.get("cfg", {}))
        # Nucleo que nao abre caminho com acento (o Hatari, do Atari ST): a
        # BIOS e o jogo vao por uma pasta sem acento. O caminho de verdade
        # continua valendo para o resto (nome do remapeamento, sessao).
        caminho_do_nucleo = caminho_jogo
        chaves_da_ponte = []
        if ponte_sem_acento.precisa(jogo.get("core"), PASTA_SISTEMA, caminho_jogo):
            try:
                caminho_do_nucleo, opcoes_ponte, devolver_ponte = ponte_sem_acento.preparar(
                    jogo["core"], PASTA_SISTEMA, caminho_jogo)
                opcoes_jogo.update(opcoes_ponte)
                chaves_da_ponte = list(opcoes_ponte)
                print("[ARENA] Pasta com acento: o jogo abre por %s." % os.path.dirname(caminho_do_nucleo))
            except OSError as falha:
                print("[ARENA] Nao consegui preparar a pasta sem acento: %s" % falha)
        copia_nucleo = None
        if ligacao.get("nucleo"):
            try:
                copia_nucleo = graficos.gravar_opcoes_de_nucleo_da_partida(ligacao["nucleo"])
            except OSError as falha:
                print("[ARENA] Nao consegui ligar o adaptador de controles: %s" % falha)
        # O RetroArch grava no retroarch.cfg, ao fechar, o que veio aqui;
        # guarda o valor de antes para devolver no fim (ver graficos).
        # Tudo o que so a partida de 3+ escreve: o adaptador (ligacao), as
        # portas 3 em diante (tipo de controle e analogico, acima) e a copia
        # das opcoes de nucleo. Com 1 ou 2 jogadores a lista fica vazia.
        so_desta_partida = list(ligacao.get("cfg", {}))
        # A pasta system da ponte sem acento (pasta temporaria) tambem: senao
        # o proximo jogo, de outro console, procuraria a BIOS la.
        so_desta_partida += chaves_da_ponte
        if jogadores_ligacao > 2:
            for n in range(3, jogadores_controle + 1):
                so_desta_partida += ["input_libretro_device_p%d" % n,
                                     "input_player%d_analog_dpad_mode" % n]
        if copia_nucleo:
            so_desta_partida.append("core_options_path")
        cfg_antes = graficos.valores_no_retroarch_cfg(so_desta_partida)
        # ORDEM IMPORTA. As opcoes vem antes do arquivo do jogo.
        #
        # Estava assim: retroarch -L core JOGO --appendconfig X --host
        #
        # Com o caminho do jogo no meio, o RetroArch trata o que vem depois
        # como se ja fosse outra coisa, e o --host/--connect nao surte
        # efeito: cada maquina abre o jogo sozinha, sem se ligar - que e
        # exatamente o sintoma relatado.
        #
        # Agora: retroarch -L core --appendconfig X --host JOGO
        override, filtro = gravar_override(
            config, custo, opcoes_jogo,
            em_partida=bool(partida), opcoes_de_nucleo=copia_nucleo,
            remapear=(os.path.join(PASTA_CORES, jogo["core"]), caminho_jogo),
            plataforma=jogo.get("plataforma"), devolver_filtro=True,
            controles_ligados=controles.contar_controles())
        comando = [
            EXECUTAVEL_RETROARCH,
            "-L", os.path.join(PASTA_CORES, jogo["core"]),
            "--appendconfig", override,
        ]
        if filtro:
            comando += ["--set-shader", filtro]
        if partida:
            comando += partida["argumentos"]
        comando.append(caminho_do_nucleo)
        if partida and partida.get("anfitriao"):
            # Quem entra avisa o anfitriao e, se ele esperava, aguarda o
            # jogo dele abrir: os dois comecam juntos (14/10/2026). Fica
            # protegido: aqui ainda nao entrou o trecho que solta a trava
            # do jogo no fim, e um erro deixaria o ARENA preso.
            try:
                chegar_na_partida(partida["anfitriao"], apelido)
            except Exception as falha:
                print("[ARENA] Nao consegui avisar quem abriu a partida: %s" % falha)

    try:
        with TRAVA_BANCO, banco() as conexao:
            abrir_sessao(conexao, sessao_uuid, apelido, jogo["id"], jogo["titulo"],
                         agora_utc(), config["dispositivo_id"])

        inicio = time.monotonic()
        # Modo desempenho (e o ultra, que o liga junto): enquanto o jogo roda,
        # o ARENA cede a vez -- prioridade abaixo do normal, memoria com
        # prioridade baixa (se faltar memoria, o Windows tira do servidor, nao
        # do jogo) -- e o emulador fica fora da economia de energia do Windows.
        # Nao fecha nada de ninguem: so muda quem tem preferencia na fila.
        # Achado de 30/09/2026 (ver servidor\processos.py): antes, nenhuma das
        # mudancas de prioridade acontecia de verdade.
        acelerar = bool(config.get("modo_desempenho") or config.get("ultra_desempenho"))
        try:
            # Todo jogo abre "acima do normal": ganha a CPU na frente do
            # navegador e do resto. Faz diferenca real em maquina de 2 nucleos.
            # A "alta" NAO entra: ela nunca chegou a valer (as duas juntas, o
            # Windows aplica a acima do normal) e, numa maquina de 4 nucleos
            # com o emulador usando todos, pode deixar o proprio Windows
            # engasgado -- fica para teste no notebook da escola.
            extras = {}
            if sys.platform.startswith("win"):
                extras["creationflags"] = processos.ACIMA_DO_NORMAL
            if acelerar:
                processos.prioridade_do_arena(processos.ABAIXO_DO_NORMAL)
                processos.memoria_do_arena(processos.MEMORIA_BAIXA)

            # No modo ultra, o ARENA para de vigiar a rede e de se
            # anunciar enquanto o jogo roda. Volta sozinho ao fechar (no
            # finally la embaixo: antes, se o emulador nem abria, o vigia
            # ficava parado ate reabrir o ARENA).
            if config.get("ultra_desempenho"):
                VIGIA["suspenso"] = True

            # Registrar o comando exato. Sem isto, quando a partida a dois
            # nao conecta, nao ha como saber se o problema foi o ARENA
            # montar errado ou o RetroArch/rede recusar.
            print("[ARENA] %s" % " ".join(
                ('"%s"' % p if " " in p else p) for p in comando))

            # Modo economico + PS1 no SwanStation: nao deixa o nucleo
            # regravar 15-50 MB de cache de video a cada fechamento (ver
            # graficos.preparar_cache_ps1). Nao vale no Jogar Junto, que usa
            # outro nucleo.
            cuidar_cache_ps1 = (ECONOMICO and jogo["plataforma"] == "ps1" and not partida
                                and not jogo.get("externo")
                                and "swanstation" in str(jogo.get("core", "")))
            placa = str(MAQUINA["gpu"].get("nome", ""))
            cache_antes = graficos.preparar_cache_ps1(placa) if cuidar_cache_ps1 else -1

            ULTIMO_PROBLEMA.clear()
            aberto_em = time.time()
            processo = subprocess.Popen(comando, cwd=pasta_trabalho, **extras)
            if acelerar and processos.tirar_da_economia_de_energia(processo.pid):
                print("[ARENA] Emulador fora da economia de energia do Windows.")
            codigo = processo.wait()

            # O jogo gravou no disquete da pasta sem acento: leva de volta.
            if devolver_ponte:
                try:
                    if devolver_ponte():
                        print("[ARENA] O jogo gravou no disquete: copia levada de volta para a pasta dele.")
                except OSError as falha:
                    print("[ARENA] Nao consegui levar o disquete de volta: %s" % falha)

            # Partida de 3+ jogadores: o que foi so dela nao pode ficar no
            # retroarch.cfg para o proximo jogo (ver graficos).
            if not jogo.get("externo") and cfg_antes:
                try:
                    graficos.devolver_valores_no_retroarch_cfg(cfg_antes)
                except OSError as falha:
                    print("[ARENA] Nao consegui arrumar o retroarch.cfg: %s" % falha)

            if cuidar_cache_ps1 and graficos.fixar_cache_ps1(cache_antes, placa):
                print("[ARENA] Cache de video do PS1 estavel: nao sera mais regravado.")

            # Cada partida deixa um registro do RetroArch em dados\. O rodizio
            # rodava so na abertura do ARENA: aberto a aula inteira, os
            # registros passavam do limite (auditoria 2 achou 20 com limite
            # 10). Agora roda tambem aqui, ao fim de cada jogo.
            limpar_logs_antigos()

            # Fechou sozinho? Guarda o motivo, para o aluno nao ficar sem
            # explicacao e para dar o que investigar depois.
            if codigo not in (0, None):
                registrar_fechamento(jogo, codigo, comando)
            # Nao abriu? O registro do RetroArch diz por que (MAME e FBNeo
            # dizem ate o nome de cada arquivo que falta).
            if not jogo.get("externo"):
                anotar_motivo_do_erro(jogo, aberto_em, partida)
        except OSError as falha:
            print("[ARENA] Nao foi possivel abrir o RetroArch: %s" % falha)
        finally:
            # Volta tudo ao normal, abrindo o jogo ou nao.
            VIGIA["suspenso"] = False
            if acelerar:
                processos.prioridade_do_arena(processos.NORMAL)
                processos.memoria_do_arena(processos.MEMORIA_NORMAL)

        duracao = int(time.monotonic() - inicio)

        with TRAVA_BANCO, banco() as conexao:
            encerrar_sessao(conexao, sessao_uuid, duracao)
        print("[ARENA] Sessao encerrada: %ds" % duracao)

        # Copia de seguranca dentro da pasta. Em maquina modesta ou com
        # cartao SD, espacada: gravacao demais desgasta a midia e trava o
        # jogo seguinte enquanto o disco escreve.
        agora = time.monotonic()
        if (agora - VIGIA["ultimo_backup_local"]) >= INTERVALO_BACKUP:
            fazer_backup()
            VIGIA["ultimo_backup_local"] = agora

        # Se o servidor da sala estiver alcancavel, sobe na hora. Se nao
        # estiver, os recordes ficam na fila e sobem depois. O aluno nao
        # precisa fazer nada nem saber que a rede caiu.
        atual = carregar_config()
        if VIGIA["online"] or any(servidor_alcancavel(a["url"])
                                  for a in atual.get("servidores", [])[:3]):
            resultado = sincronizar(atual)
            if resultado.get("ok"):
                print("[ARENA] Sincronizado: %d enviados, %d recebidos"
                      % (resultado["enviados"], resultado["recebidos"]))

    finally:
        # Libera a trava mesmo se algo der errado no meio do caminho.
        with TRAVA_JOGO:
            JOGO_EM_ANDAMENTO["ativo"] = False
            JOGO_EM_ANDAMENTO["titulo"] = ""
            PARTIDA_ABERTA["partida"] = None


# ---------------------------------------------------------------------------
# BLOCO 6b - Copia de seguranca dentro da propria pasta
# ---------------------------------------------------------------------------
# Roda quando um jogo e fechado. Copia o que nao pode ser perdido para
# 'backup\', dentro da propria pasta do ARENA. Assim a copia viaja junto
# com o pen drive, sem depender de rede nenhuma.
#
# Nao copia save state: um estado de PlayStation passa de 1 MB, e sao 10
# por jogo. Copiar isso a cada partida acabaria com um pen drive em poucas
# semanas. Estado fica so no lugar original.

ARQUIVOS_DE_BACKUP = ("arena.db", "config.json", "controles.json")
COPIAS_MANTIDAS = 3
LOGS_MANTIDOS = 10


def apagar_pasta_toda(caminho):
    """shutil.rmtree que tambem apaga o que esta marcado "somente leitura".

    Achado de 01/10/2026: o RetroArch cria saves\\.netplay com o atributo
    somente leitura. A copia de seguranca herdava o atributo; o rmtree com
    ignore_errors apagava os arquivos e desistia da pasta, sem dizer nada.
    Resultado: o rodizio de 3 copias deixava um esqueleto de pastas por
    backup (209 nesta maquina em duas semanas), e cada backup novo tentava
    apagar todos de novo -- mais lento a cada dia, num pen drive.
    Devolve True se a pasta sumiu."""
    def tirar_trava(funcao, alvo, _erro):
        try:
            os.chmod(alvo, stat.S_IWRITE)
            funcao(alvo)
        except OSError:
            pass
    shutil.rmtree(caminho, onexc=tirar_trava)
    return not os.path.exists(caminho)


def traduzir_erro_do_sistema(falha, acao):
    """Troca o texto cru do Windows/Python por uma frase que o aluno entende:
    o que aconteceu + o que fazer agora."""
    if isinstance(falha, PermissionError) or getattr(falha, "errno", None) in (errno.EACCES, errno.EPERM):
        motivo = ("Outro programa está usando esse arquivo, ou a pasta está "
                  "protegida. Feche os outros programas e tente de novo.")
    elif getattr(falha, "errno", None) == errno.ENOSPC:
        motivo = ("Acabou o espaço no disco ou no pen drive. Apague algo que "
                  "não precisa mais e tente de novo.")
    elif isinstance(falha, FileNotFoundError):
        motivo = ("Um arquivo ou pasta sumiu no meio do caminho. Clique em "
                  "Atualizar lista e tente de novo.")
    elif isinstance(falha, (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError)):
        motivo = ("A internet falhou no meio do caminho. Confira a conexão e "
                  "tente de novo.")
    else:
        motivo = "Tente de novo; se continuar, chame o professor."
    print("[ARENA] %s falhou: %r" % (acao, falha))
    return "Não consegui %s. %s" % (acao, motivo)


_cache_barreiras = {"quando": 0.0, "resultado": None}
TRAVA_BARREIRAS = threading.Lock()


def diagnostico_de_barreiras(forcar=False):
    """Roda barreiras.diagnosticar() no maximo uma vez por minuto (o aluno
    pode clicar varias vezes). Um de cada vez: dois cliques colados nao
    abrem dois PowerShell. Para a tela vai so o que ela mostra -- nada da
    lista de processos inteira."""
    with TRAVA_BARREIRAS:
        with TRAVA_CACHE:
            idade = time.time() - _cache_barreiras["quando"]
            salvo = _cache_barreiras["resultado"]
        if salvo and idade < 60 and not forcar:
            return salvo
        # O tipo do disco do Windows (HD ou SSD) o proprio diagnostico
        # pergunta ao Windows; aqui nao se mede nada.
        completo = barreiras.diagnosticar()
        fatos = completo.get("fatos", {})
        resultado = {
            "ok": True,
            "barreiras": completo["barreiras"],
            "segundos": completo["segundos"],
            "nao_deu_para_ler": completo["nao_deu_para_ler"],
            "resumo": {chave: fatos.get(chave) for chave in (
                "memoria_livre_mb", "memoria_total_mb", "ligado_ha_horas",
                "programas_instalados", "disco_windows_livre_gb")},
            "verificado_em": agora_utc(),
        }
        with TRAVA_CACHE:
            _cache_barreiras["quando"] = time.time()
            _cache_barreiras["resultado"] = resultado
        return resultado


def limpar_logs_antigos():
    """Apaga os logs do RetroArch mais velhos, mantendo so os LOGS_MANTIDOS
    mais recentes (por nome -- o carimbo de data/hora no nome ja ordena
    certo). Devolve quantos apagou."""
    try:
        nomes = sorted(
            nome for nome in os.listdir(PASTA_DADOS)
            if nome.startswith("retroarch__") and nome.endswith(".log"))
    except OSError:
        return 0

    excedentes = nomes[:-LOGS_MANTIDOS] if len(nomes) > LOGS_MANTIDOS else []
    apagados = 0
    for nome in excedentes:
        try:
            os.remove(os.path.join(PASTA_DADOS, nome))
            apagados += 1
        except OSError:
            pass
    return apagados


def e_pasta_de_copia(nome):
    """'2026-10-02_170059' (o carimbo do fazer_backup)? So essas giram."""
    try:
        time.strptime(nome, "%Y-%m-%d_%H%M%S")
        return True
    except ValueError:
        return False


# Pastas de saves que a copia nao leva: o saves\.netplay e' a pasta
# descartavel que o RetroArch usa so enquanto o aluno e' convidado numa
# partida (para o save do colega nao cobrir o dele) -- e vem somente
# leitura; CACHE e' o que o emulador refaz sozinho (os sombreadores do PSP,
# saves\PPSSPP\PSP\SYSTEM\CACHE -- achado da auditoria 3, Fase 0).
FORA_DA_COPIA = {".netplay", "cache"}


def arquivos_da_copia():
    """(origem, caminho dentro da copia) de tudo o que a copia leva: a
    configuracao do RetroArch (e' ela que guarda o mapeamento dos
    controles), o banco, a configuracao e os controles do ARENA, e os saves
    comuns (pequenos -- alguns KB -- e o que doi perder)."""
    itens = []
    origem_cfg = os.path.join(PASTA_RETROARCH, "retroarch.cfg")
    if os.path.isfile(origem_cfg):
        itens.append((origem_cfg, "retroarch.cfg"))
    for nome in ARQUIVOS_DE_BACKUP:
        origem = os.path.join(PASTA_DADOS, nome)
        if os.path.isfile(origem):
            itens.append((origem, nome))
    if os.path.isdir(PASTA_SAVES):
        for atual, pastas, arquivos in os.walk(PASTA_SAVES):
            pastas[:] = sorted(p for p in pastas if p.lower() not in FORA_DA_COPIA)
            for nome in sorted(arquivos):
                origem = os.path.join(atual, nome)
                itens.append((origem, os.path.join("saves", os.path.relpath(origem, PASTA_SAVES))))
    return itens


def ultima_copia():
    """A pasta da copia de seguranca mais recente, ou None."""
    try:
        copias = sorted(d for d in os.listdir(PASTA_BACKUP)
                        if os.path.isdir(os.path.join(PASTA_BACKUP, d)) and e_pasta_de_copia(d))
    except OSError:
        return None
    return os.path.join(PASTA_BACKUP, copias[-1]) if copias else None


def copia_igual(pasta_da_copia, itens):
    """A copia guardada ja tem tudo o que uma nova levaria, igual?

    Tamanho diferente: mudou. Mesmo tamanho e a mesma data (a copia guarda a
    data do original): igual. Mesmo tamanho e data diferente: compara o
    conteudo -- o save de cartucho tem SEMPRE o mesmo tamanho, e o FAT32
    guarda a hora de 2 em 2 segundos (a copia pode ficar com outra hora sem
    nada ter mudado). Os arquivos sao pequenos (KB)."""
    import filecmp
    if not pasta_da_copia or not itens:
        return False
    for origem, relativo in itens:
        guardado = os.path.join(pasta_da_copia, relativo)
        try:
            atual, antes = os.stat(origem), os.stat(guardado)
            if atual.st_size != antes.st_size:
                return False
            if atual.st_mtime_ns != antes.st_mtime_ns and not filecmp.cmp(origem, guardado, shallow=False):
                return False
        except OSError:
            return False
    return True


def fazer_backup():
    """Guarda banco, configuracao e saves comuns na pasta backup.

    So quando algo mudou desde a ultima copia. Achado da auditoria 3 (Fase
    0): copias iguais umas as outras (uma a cada abertura, uma a cada volta
    da internet) faziam o rodizio de 3 jogar fora as copias de momentos
    diferentes. Nada mudou: devolve a ultima copia, que ja guarda tudo."""
    import shutil
    try:
        os.makedirs(PASTA_BACKUP, exist_ok=True)
        itens = arquivos_da_copia()
        anterior = ultima_copia()
        if copia_igual(anterior, itens):
            return anterior
        carimbo = time.strftime("%Y-%m-%d_%H%M%S")
        destino = os.path.join(PASTA_BACKUP, carimbo)
        os.makedirs(destino, exist_ok=True)
        for origem, relativo in itens:
            alvo = os.path.join(destino, relativo)
            os.makedirs(os.path.dirname(alvo), exist_ok=True)
            shutil.copy2(origem, alvo)

        # Mantem so as copias mais recentes. Giram SO as pastas com nome de
        # data (o carimbo acima): o .zip do "Exportar" e as pastas avulsas
        # ficam. Achado de 02/10/2026: o comentario ja dizia isso, mas o
        # codigo contava qualquer pasta -- backup\originais (o jogo original
        # guardado pela conversao de fliperama) tomaria a vaga de uma copia,
        # e uma pasta de nome "menor" que as datas seria apagada.
        copias = sorted(
            d for d in os.listdir(PASTA_BACKUP)
            if os.path.isdir(os.path.join(PASTA_BACKUP, d)) and e_pasta_de_copia(d))
        for antiga in copias[:-COPIAS_MANTIDAS]:
            apagar_pasta_toda(os.path.join(PASTA_BACKUP, antiga))

        return destino
    except OSError as falha:
        print("[ARENA] Nao foi possivel fazer a copia de seguranca: %s" % falha)
        return None


def exportar_saves():
    """Junta saves, save states, cheats e recordes num arquivo unico.

    Um .zip na pasta backup. Serve para levar seu progresso para outro
    ARENA, para outro computador, ou so para guardar em lugar seguro.
    E um arquivo so: da para mandar por qualquer meio.
    """
    import zipfile

    os.makedirs(PASTA_BACKUP, exist_ok=True)
    nome = "meu-progresso-%s.zip" % time.strftime("%Y-%m-%d_%H%M")
    destino = os.path.join(PASTA_BACKUP, nome)

    # O perfil do aluno e tudo isso junto: saves, estados, cheats, o
    # mapeamento dos controles e os ajustes que ele fez dentro do jogo.
    pastas = [(PASTA_SAVES, "saves"), (PASTA_STATES, "states"),
              (PASTA_CHEATS, "cheats"), (PASTA_REMAPS, "remaps"),
              (PASTA_CONTROLES, "controles"), (PASTA_SISTEMA, "system")]
    quantos = 0

    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as pacote:
        for pasta, rotulo in pastas:
            if not os.path.isdir(pasta):
                continue
            for atual, _sub, arquivos in os.walk(pasta):
                for arquivo in arquivos:
                    if arquivo.lower() == "leia.txt":
                        continue
                    caminho = os.path.join(atual, arquivo)
                    dentro = os.path.join(rotulo, os.path.relpath(caminho, pasta))
                    pacote.write(caminho, dentro)
                    quantos += 1
        for arquivo in ("arena.db", "config.json", "controles.json"):
            caminho = os.path.join(PASTA_DADOS, arquivo)
            if os.path.isfile(caminho):
                pacote.write(caminho, os.path.join("dados", arquivo))
                quantos += 1
        # A configuracao do RetroArch guarda o mapeamento do teclado e do
        # controle. Sem ela, o aluno reconfiguraria tudo na outra maquina.
        principal_cfg = os.path.join(PASTA_RETROARCH, "retroarch.cfg")
        if os.path.isfile(principal_cfg):
            pacote.write(principal_cfg, os.path.join("retroarch", "retroarch.cfg"))
            quantos += 1

    return {"arquivo": nome, "itens": quantos,
            "tamanho_mb": round(os.path.getsize(destino) / 1048576.0, 1)}


def importar_saves(nome_arquivo):
    """Traz de volta um pacote de progresso, sem apagar o que ja existe.

    Arquivo que ja existe NAO e sobrescrito: se voce ja jogou nesta
    maquina, seu save continua valendo. O que vem de fora so preenche o
    que estava faltando. Assim ninguem perde progresso por engano.
    """
    import shutil
    import zipfile

    caminho = os.path.join(PASTA_BACKUP, os.path.basename(str(nome_arquivo)))
    if not dentro_da_pasta(caminho, PASTA_BACKUP) or not os.path.isfile(caminho):
        return None, ("Não achei o pacote na pasta backup. Copie o arquivo meu-progresso (o .zip) para a pasta backup e tente de novo.")

    destinos = {"saves": PASTA_SAVES, "states": PASTA_STATES,
                "cheats": PASTA_CHEATS, "remaps": PASTA_REMAPS,
                "controles": PASTA_CONTROLES, "system": PASTA_SISTEMA}
    trazidos = pulados = 0

    try:
        with zipfile.ZipFile(caminho) as pacote:
            for item in pacote.namelist():
                if item.endswith("/") or ".." in item:
                    continue
                partes = item.replace("\\", "/").split("/", 1)
                if len(partes) != 2 or partes[0] not in destinos:
                    continue
                alvo = os.path.join(destinos[partes[0]], partes[1].replace("/", os.sep))
                if not dentro_da_pasta(alvo, PASTA_RETROARCH):
                    continue
                if os.path.exists(alvo):
                    pulados += 1
                    continue
                os.makedirs(os.path.dirname(alvo), exist_ok=True)
                # Pelo temporario: se o pen drive sair no meio, nao fica um
                # save cortado com o nome certo -- a proxima importacao o
                # pularia por "ja existir". Achado da auditoria 3.
                temporario = alvo + ".importando"
                try:
                    with pacote.open(item) as origem, open(temporario, "wb") as saida:
                        shutil.copyfileobj(origem, saida)
                    os.replace(temporario, alvo)
                finally:
                    if os.path.exists(temporario):
                        try:
                            os.remove(temporario)
                        except OSError:
                            pass
                trazidos += 1
    except (zipfile.BadZipFile, OSError) as falha:
        return None, ("O pacote está danificado ou não dá para ler (%s). No outro computador, clique em Montar meu pacote de novo e tente outra vez." % falha)

    return {"trazidos": trazidos, "ja_existiam": pulados}, None


def listar_pacotes():
    """Pacotes de progresso disponiveis na pasta backup."""
    try:
        nomes = [n for n in os.listdir(PASTA_BACKUP) if n.endswith(".zip")]
    except OSError:
        return []
    saida = []
    for nome in sorted(nomes, reverse=True)[:20]:
        caminho = os.path.join(PASTA_BACKUP, nome)
        try:
            saida.append({
                "nome": nome,
                "tamanho_mb": round(os.path.getsize(caminho) / 1048576.0, 1),
                "quando": time.strftime("%d/%m/%Y %H:%M",
                                        time.localtime(os.path.getmtime(caminho))),
            })
        except OSError:
            continue
    return saida


# ---------------------------------------------------------------------------
# Troca pelo pen drive: sincronizar sem rede nenhuma
# ---------------------------------------------------------------------------
# O jeito mais confiavel de trocar recordes numa escola sem Wi-Fi liberado
# e sem cabo: levar o pen drive ate a maquina do colega.
#
# Funciona assim: o ARENA grava uma "mala" na raiz da midia. Quando outro
# ARENA encontra essa mala, ele le o que tem dentro, junta ao dele, e
# devolve na mesma mala o que ele tinha de novo. Na volta, o dono da mala
# recebe tudo. Duas maquinas ficam iguais sem nunca terem se falado.
#
# A mesma identificacao unica por registro que vale na rede vale aqui:
# passar a mala dez vezes nao duplica nada.

NOME_DA_MALA = "ARENA-troca.json"
LIMITE_MALA = 4000


def caminho_da_mala(pasta=None):
    """A mala fica na raiz da midia, ao lado da pasta do ARENA."""
    base = pasta or os.path.dirname(RAIZ)
    return os.path.join(base, NOME_DA_MALA)


def ler_mala(caminho):
    try:
        with open(caminho, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except (OSError, ValueError):
        return None
    if not isinstance(dados, dict) or dados.get("formato") != "arena-troca-1":
        return None
    return dados


def trocar_pela_mala(caminho=None):
    """Le a mala, junta o que veio, e devolve o que este ARENA tem de novo.

    Uma passada so resolve os dois lados: quem recebe ja deixa na mala o
    que o outro ainda nao tem.
    """
    # 'caminho' pode apontar para a raiz de QUALQUER midia (pen drive,
    # disco), entao nao da pra travar com dentro_da_pasta() como as outras
    # rotas fazem. Mas o NOME tem que ser sempre o da mala -- sem isto, um
    # pedido malicioso (achado real na auditoria: nenhuma validacao aqui)
    # conseguia mandar o ARENA gravar um arquivo em QUALQUER caminho, com
    # QUALQUER nome, so escolhendo o valor de 'caminho'.
    if caminho and os.path.basename(caminho) != NOME_DA_MALA:
        return {"ok": False,
                "erro": "Caminho da mala inválido: o arquivo precisa se "
                        "chamar %s." % NOME_DA_MALA}

    config = carregar_config()
    destino = caminho or caminho_da_mala()

    recebidos = 0
    ja_vistos = {}
    mala = ler_mala(destino)

    if mala:
        recebidos = gravar_recebidos(mala.get("placares") or [],
                                     mala.get("sessoes") or [])
        # Marca ate onde cada ARENA que ja passou por aqui deixou registro,
        # para a proxima passada carregar so o que e novo.
        ja_vistos = dict(mala.get("ate") or {})

    # O que este ARENA poe na mala: tudo que ele tem, menos o que ja estava
    # la. O uuid resolve o resto do outro lado.
    dentro = {p["uuid"] for p in (mala.get("placares") if mala else []) or []}
    dentro |= {s["uuid"] for s in (mala.get("sessoes") if mala else []) or []}

    placares, sessoes, _ate = registros_desde("", LIMITE_MALA)
    placares = [p for p in placares if p["uuid"] not in dentro][:LIMITE_MALA]
    sessoes = [s for s in sessoes if s["uuid"] not in dentro][:LIMITE_MALA]

    if mala:
        placares = (mala.get("placares") or []) + placares
        sessoes = (mala.get("sessoes") or []) + sessoes

    ja_vistos[config["dispositivo_id"]] = agora_utc()

    nova = {
        "formato": "arena-troca-1",
        "atualizada_em": agora_utc(),
        "passou_por": sorted(ja_vistos),
        "ate": ja_vistos,
        "placares": placares[-LIMITE_MALA:],
        "sessoes": sessoes[-LIMITE_MALA:],
    }

    try:
        gravar_texto_atomico(destino,
                             json.dumps(nova, ensure_ascii=False,
                                        separators=(",", ":")))
    except OSError as falha:
        return {"ok": False, "erro": "Não consegui gravar a mala: %s" % falha}

    marcar_enviados(placares[:0], sessoes[:0])   # a mala nao e um destino fixo

    return {
        "ok": True,
        "recebidos": recebidos,
        "na_mala": len(nova["placares"]) + len(nova["sessoes"]),
        "maquinas": len(nova["passou_por"]),
        "arquivo": destino,
    }


# ---------------------------------------------------------------------------
# Achar os colegas sozinho na rede
# ---------------------------------------------------------------------------
# Digitar endereco e a parte que mais da errado: o aluno copia o endereco
# do adaptador virtual, erra um numero, ou nem acha onde ele fica.
#
# Aqui cada ARENA grita "estou aqui" na rede a cada poucos segundos, e
# escuta quem mais esta gritando. Funciona em qualquer rede compartilhada:
# Wi-Fi da escola, ponto de acesso do notebook, roteamento do celular ou
# cabo direto. Nao precisa de servidor nem de internet.
#
# O grito e um pacote UDP de umas 100 letras. Nao leva recorde, nao leva
# nome: leva apelido, codigo do aparelho e a porta.

PORTA_DESCOBERTA = 55436
MARCA_DESCOBERTA = b"ARENA1"

VIZINHOS = {}          # codigo do aparelho -> dados vistos
TRAVA_VIZINHOS = threading.Lock()


_FALANTES = {}   # endereco local -> socket UDP preso a ele


def broadcast_da_rede(ip):
    """Endereco de "todos desta rede" para um IP, sem saber a mascara.

    Palpite pelas redes que a sala usa de verdade: /24 (roteador, ponto de
    acesso do Windows 192.168.137.x, Android), /28 do iPhone (172.20.10.x)
    e /16 do cabo direto (169.254.x.x). Errar aqui nao quebra nada: o
    255.255.255.255 continua indo junto."""
    partes = ip.split(".")
    if len(partes) != 4:
        return None
    if ip.startswith("172.20.10."):
        return "172.20.10.15"
    if ip.startswith("169.254."):
        return "169.254.255.255"
    return "%s.%s.%s.255" % tuple(partes[:3])


def gritar(pacote):
    """Manda o grito por TODOS os adaptadores, nao so pelo principal.

    Achado de 30/09/2026: o Windows manda o 255.255.255.255 so pelo
    adaptador de rota principal (em geral o Wi-Fi). Com o ponto de acesso
    do Windows ou do celular, o colega fica do outro lado e nunca ouvia.
    Um socket preso ao endereco de cada adaptador faz o grito sair por ele.
    """
    # 127.0.0.1: outro ARENA neste mesmo computador (testes).
    for destino in ("127.0.0.1", "255.255.255.255"):
        falante = _FALANTES.get("")
        try:
            if falante is None:
                falante = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                falante.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                _FALANTES[""] = falante
            falante.sendto(pacote, (destino, PORTA_DESCOBERTA))
        except OSError:
            pass

    for endereco in enderecos_locais():
        ip = endereco["ip"]
        if ip.startswith("127.") or endereco["tipo"] in ("so_aqui", "virtual"):
            continue
        falante = _FALANTES.get(ip)
        try:
            if falante is None:
                falante = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                falante.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                falante.bind((ip, 0))
                _FALANTES[ip] = falante
            for destino in ("255.255.255.255", broadcast_da_rede(ip)):
                if destino:
                    falante.sendto(pacote, (destino, PORTA_DESCOBERTA))
        except OSError:
            # Adaptador sumiu (Wi-Fi desligado, hotspot fechado): esquece o
            # socket; se o endereco voltar, cria outro.
            velho = _FALANTES.pop(ip, None)
            if velho is not None:
                try:
                    velho.close()
                except OSError:
                    pass


# Teto da lista de colegas vistos: numa sala cabem uns 40. Cada computador
# da rede pode mandar o que quiser na porta da descoberta; sem teto, quem
# inventasse codigos enchia a lista (e a poda, a cada pacote, ficava
# cada vez mais lenta). Por endereco, ate 4 (dois ARENAs no mesmo
# computador ja acontece nos testes).
LIMITE_VIZINHOS = 200
LIMITE_POR_ENDERECO = 4
# (Sem limite de gritos por segundo por endereco, de proposito: a revisao
# de seguranca de 08/10/2026 mostrou que, com o endereco de origem
# falsificado, alguem gastaria a cota de um colega de verdade e o faria
# sumir da lista -- e contar o pacote custa quase o mesmo que le-lo.)
_PODA_DOS_VIZINHOS = {"ultima": 0.0, "aviso": 0.0}


def receber_grito(pacote, remetente, meus=None, agora=None):
    """Trata um grito recebido na porta da descoberta. Devolve True se o
    colega entrou (ou foi renovado) na lista.

    Vem da rede: qualquer computador pode mandar qualquer coisa. Achado da
    auditoria 3 (07/10/2026): um pacote torto -- um JSON que nao e'
    objeto, ou "porta": "abc" -- levantava erro fora do try e MATAVA a
    linha que escuta: a descoberta de colegas acabava ate fechar o ARENA.
    E a lista nao tinha teto. Agora tudo o que chega e' conferido, e uma
    enxurrada (de um computador, ou com enderecos inventados) nao tira da
    lista os colegas que ja estao nela.
    """
    agora = time.monotonic() if agora is None else agora
    if not pacote.startswith(MARCA_DESCOBERTA):
        return False
    ip = str(remetente[0])
    try:
        dados = json.loads(pacote[len(MARCA_DESCOBERTA):].decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return False
    if not isinstance(dados, dict):
        return False
    identificacao = str(dados.get("id") or "")[:32]
    if not identificacao:
        return False
    # Sem porta no grito: a padrao. Porta que nao e' numero de 1 a 65535
    # (0, "abc", true, [1]...): o grito nao vale.
    porta_bruta = dados.get("porta")
    if isinstance(porta_bruta, bool):
        return False
    try:
        porta_dele = PORTA if porta_bruta in (None, "") else int(porta_bruta)
    except (TypeError, ValueError, OverflowError):
        return False
    if not 1 <= porta_dele <= 65535:
        return False
    # "Sou eu?" nao da para responder pelo codigo: em laboratorio com
    # maquinas clonadas o codigo pode se repetir, e ai o ARENA ignoraria o
    # colega achando que e o proprio eco. Quem responde e o par
    # endereco+porta, que e unico de verdade.
    if meus is None:
        meus = {e["ip"] for e in enderecos_locais()} | {"127.0.0.1"}
    if porta_dele == PORTA and ip in meus:
        return False
    with TRAVA_VIZINHOS:
        # Some quem sumiu ha mais de um minuto -- no maximo uma vez por
        # segundo (com pacote chegando sem parar, era a cada pacote).
        if agora - _PODA_DOS_VIZINHOS["ultima"] >= 1.0:
            _PODA_DOS_VIZINHOS["ultima"] = agora
            for chave in [k for k, v in VIZINHOS.items() if agora - v["visto_em"] > 60]:
                VIZINHOS.pop(chave, None)
        atual = VIZINHOS.get(identificacao)
        if atual is None:
            # Lista cheia (no total, ou deste endereco): quem ja esta fica, e
            # o novo espera vagar (quem some sai em 1 minuto). A primeira
            # versao tirava o mais antigo -- e uma enxurrada de codigos
            # inventados empurrava para fora os colegas de verdade.
            do_mesmo = sum(1 for v in VIZINHOS.values() if v["ip"] == ip)
            if do_mesmo >= LIMITE_POR_ENDERECO or len(VIZINHOS) >= LIMITE_VIZINHOS:
                return False
        elif atual["ip"] != ip and agora - atual["visto_em"] <= 60:
            # O codigo ja esta no ar em outro endereco: quem chega com o
            # codigo de outro nao toma o lugar dele. O computador que mudou
            # de endereco de verdade volta em ate 1 minuto, quando o
            # endereco antigo some (e o de dois adaptadores de rede para de
            # trocar de endereco a cada grito).
            return False
        VIZINHOS[identificacao] = {
            "id": identificacao,
            "apelido": limpar_apelido(dados.get("apelido", "")),
            "ip": ip,
            "porta": porta_dele,
            "visto_em": agora,
            "partida": limpar_partida_recebida(dados.get("partida")),
        }
    return True


def anunciar_e_escutar():
    """Fica gritando e ouvindo na rede local, em segundo plano."""
    try:
        ouvinte = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ouvinte.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Sem isto, dois ARENAs no mesmo computador disputam a porta e so
        # um recebe. Nao existe no Windows, e la nao faz falta.
        if hasattr(socket, "SO_REUSEPORT"):
            try:
                ouvinte.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except OSError:
                pass
        ouvinte.settimeout(1.0)
        ouvinte.bind(("", PORTA_DESCOBERTA))
    except OSError as falha:
        print("[ARENA] Nao consegui escutar a rede local (%s). Os colegas "
              "ainda podem ser adicionados pelo endereço." % falha)
        return

    ultimo_grito = 0.0

    while not VIGIA["encerrar"].is_set():
        if VIGIA["suspenso"]:
            time.sleep(1.0)
            continue

        agora = time.monotonic()

        # ---- gritar ----
        if agora - ultimo_grito > 5.0:
            ultimo_grito = agora
            config = carregar_config()
            if config.get("permitir_rede"):
                partida = partida_aberta_agora()
                recado = json.dumps({
                    "apelido": config.get("apelido") or "sem apelido",
                    "id": config["dispositivo_id"],
                    "porta": PORTA,
                    # Nome do jogo cortado: o pacote tem limite de tamanho.
                    "partida": ({"jogo": partida["jogo"][:80],
                                 "jogo_id": partida["jogo_id"][:120]}
                                if partida else None),
                }, ensure_ascii=False).encode("utf-8")
                gritar(MARCA_DESCOBERTA + recado)

        # ---- escutar ----
        try:
            pacote, remetente = ouvinte.recvfrom(2048)
        except (socket.timeout, OSError):
            continue

        # Vem da rede: nada do que chega pode derrubar quem escuta.
        try:
            receber_grito(pacote, remetente)
        except Exception as falha:   # noqa: BLE001 -- defeito nosso, nao do pacote
            if time.monotonic() - _PODA_DOS_VIZINHOS["aviso"] > 60:
                _PODA_DOS_VIZINHOS["aviso"] = time.monotonic()
                print("[ARENA] Descoberta de colegas: pacote ignorado (%s)." % falha)


def limpar_partida_recebida(partida):
    """Partida anunciada por outro ARENA: so os campos esperados, curtos.
    Vem da rede -- qualquer um pode mandar qualquer coisa."""
    if not isinstance(partida, dict):
        return None
    jogo = str(partida.get("jogo") or "")[:80].strip()
    if not jogo:
        return None
    # "esperando": quem abriu espera o jogador 2 (14/10/2026); so verdadeiro
    # ou falso, nada que venha da rede passa como texto.
    return {"jogo": jogo, "jogo_id": str(partida.get("jogo_id") or "")[:120],
            "esperando": partida.get("esperando") is True}


def colegas_na_rede():
    """Quem esta gritando na rede agora (amigos marcados com ja_e_amigo)."""
    config = carregar_config()
    conhecidos = {str(s.get("id", "")) for s in config.get("servidores", [])}
    conhecidos |= {normalizar_url(s.get("url", "")) for s in config.get("servidores", [])}

    with TRAVA_VIZINHOS:
        vistos = list(VIZINHOS.values())

    saida = []
    for vizinho in sorted(vistos, key=lambda v: v["apelido"].lower()):
        url = "http://%s:%d" % (vizinho["ip"], vizinho["porta"])
        saida.append({
            "apelido": vizinho["apelido"],
            "url": url,
            "id": vizinho["id"],
            "codigo_amigo": vizinho["id"],
            "ja_e_amigo": vizinho["id"] in conhecidos or url in conhecidos,
            "ha_quantos_segundos": int(time.monotonic() - vizinho["visto_em"]),
            "partida_aberta": bool(vizinho.get("partida")),
            "jogo_partida": (vizinho.get("partida") or {}).get("jogo", ""),
            "jogo_id_partida": (vizinho.get("partida") or {}).get("jogo_id", ""),
            "esperando_partida": bool((vizinho.get("partida") or {}).get("esperando")),
        })
    return saida


# A rede que o Windows marcou como Publica (auditoria 3, Fase 4). O Firewall
# fecha bem mais nela, e a caixa "Permitir que este app se comunique" pede
# senha de administrador -- o aluno nao consegue aprovar, e ninguem entra na
# partida dele. O PARTIDA.bat ja dizia isso; agora a tela avisa quem ABRE a
# partida, na hora, com a saida que nao pede senha: outro computador abre e
# este entra (quem entra so faz conexao de saida, que o Firewall deixa).
# O "Estamos em casas diferentes" NAO e' saida: testado em 09/10/2026, com
# ele o anfitriao vai pelo repasse da internet e nao atende na rede local, e
# o convidado (que o ARENA manda para o endereco local) nao entra.
_CATEGORIA_DA_REDE = {"valor": None, "quando": 0.0, "perguntando": False}
VALIDADE_DA_CATEGORIA = 300.0
AVISO_REDE_PUBLICA = (
    "Atenção: o Windows marcou esta rede como Pública, e o Firewall pode barrar quem tentar "
    "entrar (a caixa de permissão pede senha de administrador). Se ninguém conseguir entrar, "
    "troquem: outro computador abre a partida e este entra — quem entra não precisa dessa permissão.")


def _perguntar_categoria_da_rede():
    """"Public", "Private", "DomainAuthenticated" ou None (so LER a categoria
    nao pede administrador). Leva ~1 s (PowerShell): nunca no caminho de
    abrir o jogo. Com duas redes ligadas (o cabo direto e o Wi-Fi), basta
    uma ser Publica: a partida pode estar passando justo por ela (revisao da
    Fase 4 -- antes valia so a primeira da lista)."""
    try:
        resultado = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
             "(Get-NetConnectionProfile).NetworkCategory"],
            capture_output=True, text=True, timeout=10,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        categorias = [c.strip() for c in resultado.stdout.splitlines() if c.strip()]
        if "Public" in categorias:
            return "Public"
        return categorias[0] if categorias else None
    except (OSError, subprocess.SubprocessError):
        return None
    finally:
        _CATEGORIA_DA_REDE["perguntando"] = False


def preparar_categoria_da_rede():
    """Pergunta em segundo plano, se a resposta guardada ja passou de 5 min."""
    if not sys.platform.startswith("win") or _CATEGORIA_DA_REDE["perguntando"]:
        return
    if time.monotonic() - _CATEGORIA_DA_REDE["quando"] < VALIDADE_DA_CATEGORIA and _CATEGORIA_DA_REDE["quando"]:
        return
    _CATEGORIA_DA_REDE["perguntando"] = True

    def perguntar():
        _CATEGORIA_DA_REDE["valor"] = _perguntar_categoria_da_rede()
        _CATEGORIA_DA_REDE["quando"] = time.monotonic()
    threading.Thread(target=perguntar, daemon=True).start()


def aviso_da_rede_para_quem_hospeda(agora=None):
    """O aviso da rede Publica, ou "" (sem resposta recente: nao espera, e
    nem usa resposta velha -- a rede pode ter mudado de categoria ou de
    lugar desde entao). Quem chama ja pede outra pergunta para a proxima."""
    agora = time.monotonic() if agora is None else agora
    recente = _CATEGORIA_DA_REDE["quando"] and agora - _CATEGORIA_DA_REDE["quando"] < 2 * VALIDADE_DA_CATEGORIA
    return AVISO_REDE_PUBLICA if recente and _CATEGORIA_DA_REDE["valor"] == "Public" else ""


def procurar_partidas(config):
    """Quem tem partida aberta agora, por DOIS caminhos juntos:

    1. o grito UDP da descoberta (colegas_na_rede), e
    2. uma pergunta direta, por TCP, a cada amigo salvo (/api/sinc/ola) --
       o mesmo caminho dos recordes. Bug de 30/09/2026: os recordes
       passavam, mas o amigo aparecia "fora do ar" e a partida nao aparecia,
       porque tudo dependia so do UDP (que o Firewall ou o ponto de acesso
       podem barrar).

    Devolve (lista, enderecos_corrigidos). Cada item: apelido, url, id,
    ja_e_amigo, online, partida_aberta, jogo_partida, jogo_id_partida."""
    achados = {}
    for colega in colegas_na_rede():
        achados[colega["url"]] = dict(colega, online=True)

    amigos = config.get("servidores") or []
    trava = threading.Lock()
    mudou = [False]

    def perguntar(amigo):
        anterior = amigo.get("url", "")
        url = normalizar_url(resolver_endereco_amigo(amigo))
        if url != normalizar_url(anterior):
            with trava:
                mudou[0] = True
        if not url:
            return
        try:
            retorno = falar_com(url, "/api/sinc/ola", {}, "POST", 2)
        except Exception:
            return
        if not isinstance(retorno, dict):
            return      # resposta torta de outro computador: fica de fora
        partida = limpar_partida_recebida(retorno.get("partida"))
        item = {
            "apelido": amigo.get("apelido", ""),
            "url": url,
            "id": str(retorno.get("servidor_id") or amigo.get("id") or ""),
            "codigo_amigo": str(retorno.get("servidor_id") or amigo.get("id") or ""),
            "ja_e_amigo": True,
            "online": True,
            "partida_aberta": bool(partida),
            "jogo_partida": (partida or {}).get("jogo", ""),
            "jogo_id_partida": (partida or {}).get("jogo_id", ""),
            "esperando_partida": bool((partida or {}).get("esperando")),
        }
        with trava:
            # O que veio por TCP e' mais novo que o grito (ate 5 s de atraso)
            # e substitui o do MESMO ENDERECO. Nunca juntar pelo codigo do
            # aparelho: em laboratorio com imagem clonada (ou dois ARENAs no
            # mesmo computador) o codigo se repete, e um colega sumia da
            # lista escondido atras do outro -- achado na revisao de
            # 30/09/2026, com tres ARENAs de teste. Mesmo motivo do "sou eu?"
            # da descoberta usar endereco+porta. O endereco ja vem igual ao
            # do grito: resolver_endereco_amigo usa o IP visto no grito.
            achados[url] = item

    threads = [threading.Thread(target=perguntar, args=(a,), daemon=True)
               for a in amigos[:20]]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=3.0)

    with trava:
        lista = sorted(achados.values(),
                       key=lambda c: (not c.get("partida_aberta"),
                                      str(c.get("apelido", "")).lower()))
    return lista, mudou[0]


def resolver_endereco_amigo(amigo):
    """Acha o endereco ATUAL de um amigo, mesmo que o IP tenha mudado
    desde que foi adicionado.

    Bug relatado: todo amigo tinha o endereco fixo no dia que foi
    adicionado; IP de DHCP muda (outro dia, outra rede, reconectou o
    Wi-Fi) e o amigo "sumia", so voltando se alguem removesse e
    adicionasse nao dinovo. A descoberta automatica de colegas
    (VIZINHOS, broadcast UDP na 55436) ja resolve exatamente isso, so
    que so pra quem ainda nao e' amigo - o amigo salvo nunca era
    conferido contra ela. Agora confere: se o id do amigo estiver entre
    os vizinhos vistos AGORA, usa o IP de agora (e corrige o salvo, pra
    nao pedir de novo da proxima vez) - so cai pro endereco antigo salvo
    se ele nao estiver na rede local agora (rede diferente, internet).
    """
    amigo_id = str(amigo.get("id") or "")
    if amigo_id:
        with TRAVA_VIZINHOS:
            vizinho = VIZINHOS.get(amigo_id)
        if vizinho:
            url_atual = "http://%s:%d" % (vizinho["ip"], vizinho["porta"])
            if normalizar_url(url_atual) != normalizar_url(amigo.get("url", "")):
                amigo["url"] = url_atual
            return url_atual
    return amigo.get("url", "")


def gravar_enderecos_de_amigos(amigos_atualizados):
    """Grava SO os enderecos novos dos amigos, relendo a configuracao agora.

    Achado na revisao de 30/09/2026: quem testa os amigos (o vigia e a busca
    de partidas) le a configuracao, espera ate 3 s pela rede e gravava a
    configuracao INTEIRA de volta -- apagando o que tivesse sido salvo
    nesses segundos (um ajuste, a lista de recentes do /api/jogar). Agora
    relê na hora de gravar e so troca o endereco de quem mudou."""
    novos = {}
    for amigo in amigos_atualizados or []:
        chave = str(amigo.get("id") or "") or "apelido:" + str(amigo.get("apelido", ""))
        if amigo.get("url"):
            novos[chave] = amigo["url"]
    config = carregar_config()
    mudou = False
    for amigo in config.get("servidores") or []:
        chave = str(amigo.get("id") or "") or "apelido:" + str(amigo.get("apelido", ""))
        if chave in novos and amigo.get("url") != novos[chave]:
            amigo["url"] = novos[chave]
            mudou = True
    if mudou:
        salvar_config(config)
    return mudou


ENDERECO_ESTRANHO = ("Esse endereço não parece certo. Use o que aparece no "
                     "ARENA dele, como 192.168.0.15:8777.")


def servidor_alcancavel(url):
    """Testa se o servidor da sala responde, sem travar a interface."""
    url = normalizar_url(url)
    if not url:
        return False
    try:
        partes = urllib.parse.urlsplit(url)
        with socket.create_connection(
                (partes.hostname, partes.port or PORTA_PADRAO), timeout=1.2):
            return True
    except (OSError, UnicodeError, ValueError):
        return False


# ---------------------------------------------------------------------------
# BLOCO 7 - Sincronizacao de recordes
# ---------------------------------------------------------------------------
# Todo ARENA e servidor e cliente ao mesmo tempo:
#
#   SERVIDOR  - recebe registros de outros ARENAs em /api/sinc/receber e
#               responde com o que ha de novo aqui
#   CLIENTE   - envia os proprios registros para cada amigo cadastrado
#
# Nao existe servidor central obrigatorio. O da escola e so mais um da
# lista: se ele estiver desligado, os amigos continuam trocando entre si.
#
# Funciona offline: o aluno joga em casa sem rede nenhuma, os recordes ficam
# marcados como nao enviados, e sobem quando ele voltar para a escola e
# clicar em Sincronizar. E uma fila de envio, o mesmo padrao de mensageria
# usado em sistemas de verdade.

LIMITE_LOTE = 500


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
                novos += inserir_placar(
                    conexao, str(p["uuid"])[:40], str(p["apelido"])[:24],
                    str(p["jogo_id"])[:400], str(p["jogo_titulo"])[:200],
                    int(p["pontos"]), str(p["registrado_em"])[:40],
                    str(p["dispositivo"])[:40], enviado=1)
            except (KeyError, TypeError, ValueError, sqlite3.Error):
                continue
        for s in sessoes:
            try:
                novos += inserir_sessao_recebida(
                    conexao, str(s["uuid"])[:40], str(s["apelido"])[:24],
                    str(s["jogo_id"])[:400], str(s["jogo_titulo"])[:200],
                    str(s["inicio"])[:40], int(s["segundos"]),
                    str(s["dispositivo"])[:40])
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


def nome_de_maquina_valido(nome):
    """IP ou nome de computador que da para procurar na rede.

    Achado de 01/10/2026 (fuzz): um "endereco" de 2 MB chegava ate o
    socket, que estourava com erro de codificacao do nome (cada pedaco
    entre pontos tem no maximo 63 letras) -- erro interno na tela. Aceita
    letra de qualquer lingua, numero, - e _ (nome de computador do Windows
    pode ter _)."""
    nome = (nome or "").rstrip(".")
    if not nome or len(nome) > 253:
        return False
    try:
        ipaddress.ip_address(nome)
        return True
    except ValueError:
        pass
    for parte in nome.split("."):
        if not 1 <= len(parte) <= 63 or parte[0] == "-" or parte[-1] == "-":
            return False
        if not all(c.isalnum() or c in "-_" for c in parte):
            return False
    return True


def normalizar_url(url):
    """Aceita '192.168.0.15', '192.168.0.15:8777' ou o endereco completo.

    Endereco que nao da para usar -- nome com espaco ou gigante, porta que
    nao e' numero, texto que nem e' texto -- vira "", e quem chama ja trata
    "" como "sem endereco"."""
    url = (url if isinstance(url, str) else "").strip().rstrip("/")
    if not url or len(url) > 300:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    try:
        partes = urllib.parse.urlsplit(url)
        porta = partes.port         # porta que nao e' numero: ValueError
    except ValueError:
        return ""
    if not nome_de_maquina_valido(partes.hostname):
        return ""
    if porta is None:
        url = "%s://%s:%d" % (partes.scheme, partes.netloc, PORTA_PADRAO)
    return url


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
    # A marca e' "seq:<numero de chegada>" (ver aplicar_esquema). Marca
    # antiga (uma data, de antes desta correcao) ou vazia = desde o comeco:
    # manda tudo uma vez, e o uuid impede duplicata do outro lado.
    carimbo = str(carimbo or "")[:40]
    try:
        desde = int(carimbo[4:]) if carimbo.startswith("seq:") else 0
    except ValueError:
        desde = 0
    # Nao devolver ao amigo os registros que ele mesmo criou: ele ja tem.
    # Sem isso, a sala inteira trocava dez vezes mais dados do que precisa.
    excluir = str(exceto or "")[:40]

    with banco() as conexao:
        placares = [dict(l) for l in conexao.execute(
            "SELECT uuid, apelido, jogo_id, jogo_titulo, pontos, registrado_em, "
            "dispositivo, seq FROM placar WHERE seq > ? AND dispositivo <> ? "
            "ORDER BY seq LIMIT ?", (desde, excluir, limite))]
        sessoes = [dict(l) for l in conexao.execute(
            "SELECT uuid, apelido, jogo_id, jogo_titulo, inicio, segundos, "
            "dispositivo, seq FROM sessao WHERE encerrada = 1 AND segundos > 30 "
            "AND seq > ? AND dispositivo <> ? "
            "ORDER BY seq LIMIT ?", (desde, excluir, limite))]
        maior = conexao.execute(
            "SELECT valor FROM contador WHERE nome = 'sinc'").fetchone()[0]

    lotado = len(placares) >= limite or len(sessoes) >= limite
    if lotado:
        # Avanca so ate o mais antigo dos dois ultimos, para nao pular nada.
        marcas = []
        if len(placares) >= limite:
            marcas.append(placares[-1]["seq"])
        if len(sessoes) >= limite:
            marcas.append(sessoes[-1]["seq"])
        ate = min(marcas)
    else:
        ate = maior

    for registro in placares + sessoes:
        registro.pop("seq", None)  # numero local, nao interessa ao colega
    return placares, sessoes, "seq:%d" % ate


def falar_com(url, rota, corpo=None, metodo="POST", segundos=8):
    """Uma requisicao HTTP simples para outro ARENA."""
    dados = None
    if corpo is not None:
        dados = json.dumps(corpo, ensure_ascii=False).encode("utf-8")

    pedido = urllib.request.Request(
        url + rota, data=dados, method=metodo,
        headers={"Content-Type": "application/json; charset=utf-8"})

    with urllib.request.urlopen(pedido, timeout=segundos) as resposta:
        return json.loads(resposta.read().decode("utf-8"))


def sincronizar_com(destino, config):
    """Troca informacao com UM servidor: envia o que e novo, recebe o dele.

    Os dois lados usam o mesmo uuid por registro, entao a troca pode ser
    repetida a vontade sem duplicar nada. Se a rede cair no meio, e so
    tentar de novo.
    """
    url = normalizar_url(resolver_endereco_amigo(destino))
    apelido_destino = destino.get("apelido", "servidor")

    if not url:
        return {"ok": False, "apelido": apelido_destino,
                "erro": "Endereço vazio."}

    # O que enviar para ESTE destino: tudo que e mais novo que a ultima
    # troca com ele. Nao so o que foi gravado aqui - tambem o que chegou
    # de outro amigo. E assim que a pontuacao da Marina chega ao servidor
    # da escola passando pelo ARENA do Lucas, sem os dois precisarem se
    # conhecer. Reenviar nao custa: o uuid impede duplicata do outro lado.
    placares, sessoes, enviado_ate = registros_desde(
        destino.get("ultimo_enviado", ""), exceto=destino.get("id", ""))

    try:
        retorno = falar_com(url, "/api/sinc/receber", {
            "dispositivo": config["dispositivo_id"],
            "apelido": config.get("apelido", ""),
            "nome": config.get("nome_dispositivo", ""),
            "placares": placares,
            "sessoes": sessoes,
            # Diz ao outro lado ate onde ja recebemos dele, para ele mandar
            # so o que e novo. Isso mantem a troca leve mesmo depois de
            # meses de uso.
            "desde": destino.get("ultimo_recebido", ""),
        })
    except urllib.error.HTTPError as falha:
        try:
            detalhe = json.loads(falha.read().decode("utf-8")).get("erro", "")
        except Exception:
            detalhe = ""
        return {"ok": False, "apelido": apelido_destino,
                "erro": detalhe or "Recusado (código %d)." % falha.code}
    except urllib.error.URLError as falha:
        return {"ok": False, "apelido": apelido_destino,
                "erro": "Sem resposta de %s (%s)." % (url, falha.reason)}
    except (socket.timeout, ValueError, OSError):
        return {"ok": False, "apelido": apelido_destino,
                "erro": "Demorou demais para responder."}

    if not retorno.get("ok"):
        return {"ok": False, "apelido": apelido_destino,
                "erro": retorno.get("erro", "Recusado.")}

    # Se o outro lado responder com a NOSSA identificacao, o endereco
    # aponta de volta para ca. Nao marcar nada como enviado.
    destino["id"] = retorno.get("servidor_id", destino.get("id", ""))

    if retorno.get("servidor_id") == config["dispositivo_id"]:
        # Duas explicacoes possiveis, e elas pedem respostas opostas.
        #
        # 1. O endereco aponta mesmo para ca. Recusar e o certo.
        # 2. Sao dois computadores DIFERENTES com o mesmo codigo. Acontece
        #    em laboratorio de escola, onde as maquinas saem da mesma
        #    imagem, com o mesmo nome e o mesmo usuario. Ai recusar seria
        #    condenar os dois a nunca sincronizarem.
        #
        # Para separar os dois casos, basta olhar se o endereco de destino
        # e um dos nossos.
        alvo = urllib.parse.urlsplit(normalizar_url(url)).hostname or ""
        meus = {e["ip"] for e in enderecos_locais()} | {"127.0.0.1", "localhost"}

        if alvo in meus:
            return {"ok": False, "apelido": apelido_destino,
                    "erro": "Este endereço é o próprio computador."}

        # Caso 2: e outro computador. Trocar o NOSSO codigo, guardar, e
        # avisar. Na proxima sincronizacao ja funciona.
        novo = uuid.uuid4().hex[:12]
        print("[ARENA] Codigo repetido com %s. Trocando o nosso de %s para %s."
              % (alvo, config["dispositivo_id"], novo))
        config["dispositivo_id"] = novo
        config["codigo_proprio"] = True
        salvar_config(config)
        return {"ok": False, "apelido": apelido_destino,
                "erro": ("Vocês dois tinham o mesmo código de aparelho. "
                         "Já troquei o meu. Clique em sincronizar de novo.")}

    # Marca como enviados os registros criados aqui. Serve so para o
    # contador de pendentes da tela.
    marcar_enviados(placares, sessoes)

    # O que veio de volta: recordes e partidas do amigo.
    recebidos = gravar_recebidos(retorno.get("placares") or [],
                                 retorno.get("sessoes") or [])

    return {
        "ok": True,
        "apelido": apelido_destino,
        "url": url,
        "enviados": len(placares) + len(sessoes),
        "novos_la": retorno.get("novos", 0),
        "recebidos": recebidos,
        "ate": retorno.get("ate", ""),
        # Marca ate onde ja mandamos para este destino. Quando o lote
        # encheu, e a data do ultimo registro enviado - nao 'agora'.
        "enviado_ate": enviado_ate,
        "faltou": len(placares) + len(sessoes) >= LIMITE_LOTE,
    }


def sincronizar(config):
    """Troca informacao com todos os servidores da lista.

    Cada um e independente: se o da escola estiver desligado, os amigos
    continuam funcionando. Nenhum e obrigatorio.
    """
    lista = config.get("servidores") or []
    if not lista:
        return {"ok": False,
                "erro": "Nenhum amigo ou servidor cadastrado ainda."}

    resultados = []
    mudou = False

    for destino in lista:
        resultado = sincronizar_com(destino, config)
        resultados.append(resultado)
        if resultado["ok"]:
            if resultado.get("ate"):
                destino["ultimo_recebido"] = resultado["ate"]
            if resultado.get("enviado_ate"):
                destino["ultimo_enviado"] = resultado["enviado_ate"]
            mudou = True

    if mudou:
        salvar_config(config)

    sucessos = [r for r in resultados if r["ok"]]
    return {
        "ok": bool(sucessos),
        "erro": None if sucessos else "Nenhum servidor respondeu.",
        "enviados": sum(r.get("enviados", 0) for r in sucessos),
        "recebidos": sum(r.get("recebidos", 0) for r in sucessos),
        "resultados": resultados,
    }


# ---------------------------------------------------------------------------
# BLOCO 7c - Vigia de rede
# ---------------------------------------------------------------------------
# Duas coisas ao mesmo tempo, numa thread que fica em segundo plano:
#
# 1. Saber quem esta online SEM travar a tela. Antes, a tela inicial
#    testava cada amigo na hora, um de cada vez, com espera de 1,5 s cada.
#    Com dez amigos desligados, a tela levava quinze segundos para abrir.
#    Agora quem testa e o vigia, e a tela apenas le o resultado pronto.
#
# 2. Perceber quando a rede voltou. O aluno joga a tarde inteira sem
#    conexao; quando ela volta, o ARENA sozinho manda o que estava na
#    fila. Ninguem precisa lembrar de clicar em nada.

VIGIA = {
    "online": [],             # apelidos alcancaveis agora
    "internet": False,        # ha internet de verdade, nao so rede local
    "ultima_checagem": 0.0,
    "ultimo_envio": 0.0,
    "ultimo_backup": 0.0,
    "ultimo_backup_local": 0.0,
    "estava_offline": True,
    # None = "ainda nao sei". Comecava True, e a primeira checagem (20 s
    # depois de abrir) contava como "a internet voltou": uma copia de
    # seguranca a CADA abertura -- e, com o rodizio de 3, tres aberturas
    # apagavam as copias de antes. Achado da auditoria 3 (07/10/2026).
    "internet_estava_fora": None,
    "encerrar": threading.Event(),
    # Ligado durante o jogo no modo ultra: as tarefas de fundo param de
    # vez, para nao roubar processador nem tocar no disco enquanto o
    # aluno joga.
    "suspenso": False,
}


def quem_esta_online(config):
    """Testa todos os amigos EM PARALELO, com espera curta.

    Antes de testar, confere se o amigo apareceu na descoberta automatica
    com um IP diferente do salvo (DHCP mudou, trocou de rede) - se sim,
    corrige o endereco salvo sozinho. E o que faz o amigo nao precisar
    ser removido e adicionado de novo toda vez que o IP muda.
    """
    amigos = config.get("servidores") or []
    if not amigos:
        return [], False

    online = []
    mudou = [False]
    trava = threading.Lock()

    def testar(amigo):
        url_anterior = amigo.get("url", "")
        url = resolver_endereco_amigo(amigo)
        if url != url_anterior:
            with trava:
                mudou[0] = True
        if servidor_alcancavel(url):
            with trava:
                online.append(amigo["apelido"])

    threads = [threading.Thread(target=testar, args=(a,), daemon=True)
               for a in amigos]
    for t in threads:
        t.start()
    # Espera curta: o teste de cada um ja tem limite proprio.
    for t in threads:
        t.join(timeout=3.0)
    return online, mudou[0]


def rodar_vigia():
    """Laco do vigia. Roda ate o ARENA fechar."""
    while not VIGIA["encerrar"].wait(INTERVALO_VIGIA):
        if VIGIA["suspenso"]:
            continue

        try:
            config = carregar_config()
            online, enderecos_corrigidos = quem_esta_online(config)
            if enderecos_corrigidos:
                gravar_enderecos_de_amigos(config.get("servidores"))
            tem_internet = internet_disponivel()
            enderecos_locais(forcar=True)   # renova o cache fora da tela

            VIGIA["online"] = online
            VIGIA["internet"] = tem_internet
            VIGIA["ultima_checagem"] = time.time()

            # A internet voltou: hora de guardar copia de seguranca. O aluno
            # nao precisa lembrar de nada, nem saber que a rede caiu.
            if tem_internet and VIGIA["internet_estava_fora"]:
                if (time.time() - VIGIA["ultimo_backup"]) > 300:
                    if fazer_backup():
                        VIGIA["ultimo_backup"] = time.time()
                        print("[ARENA] Internet de volta: copia de seguranca feita.")
            VIGIA["internet_estava_fora"] = not tem_internet

            if not online:
                VIGIA["estava_offline"] = True
                continue

            # A rede voltou (ou nunca caiu, mas ha coisa na fila).
            agora = time.time()
            pendentes = contar_pendentes()
            passou_tempo = (agora - VIGIA["ultimo_envio"]) > INTERVALO_ENVIO

            if pendentes and (VIGIA["estava_offline"] or passou_tempo):
                resultado = sincronizar(carregar_config())
                VIGIA["ultimo_envio"] = agora
                if resultado.get("ok"):
                    print("[ARENA] Rede disponivel: %d enviados, %d recebidos"
                          % (resultado["enviados"], resultado["recebidos"]))

            VIGIA["estava_offline"] = False

        except Exception as falha:
            # O vigia nunca pode derrubar o ARENA.
            print("[ARENA] Vigia de rede: %s" % falha)


# ---------------------------------------------------------------------------
# BLOCO 7b - Bibliotecas graficas, sem instalar nada
# ---------------------------------------------------------------------------
# O RetroArch e os nucleos sao compilados com o Visual C++ Runtime da
# Microsoft. Sem essas bibliotecas o emulador nem abre.
#
# Instalar o pacote oficial exige senha de administrador, que o aluno nao
# tem no computador da escola. Mas existe um caminho que nao exige nada:
# o Windows procura DLL primeiro NA PASTA DO PROGRAMA, antes de procurar
# no sistema. Copiando as bibliotecas para dentro da pasta do RetroArch,
# ele passa a usar essas e funciona - sem instalador, sem administrador,
# e a copia viaja junto no pen drive.
#
# Isso e o que a Microsoft chama de 'application-local deployment', e e um
# uso previsto dessas bibliotecas: elas se chamam 'redistribuiveis'
# justamente por poderem ser distribuidas junto com o programa.

BIBLIOTECAS_RUNTIME = [
    "vcruntime140.dll", "vcruntime140_1.dll", "msvcp140.dll",
    "msvcp140_1.dll", "msvcp140_2.dll", "concrt140.dll",
]


def reparar_runtime():
    """Copia as bibliotecas graficas do sistema para a pasta do RetroArch.

    Nao instala nada, nao mexe no registro, nao pede administrador: so le
    de uma pasta e grava na outra.
    """
    import shutil

    if not sys.platform.startswith("win"):
        return [], "Este reparo só faz sentido no Windows."
    if not os.path.isdir(PASTA_RETROARCH):
        return [], "A pasta retroarch não foi encontrada."

    origens = [os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32")]
    copiadas, achadas = [], 0

    for biblioteca in BIBLIOTECAS_RUNTIME:
        for origem in origens:
            caminho = os.path.join(origem, biblioteca)
            if not os.path.isfile(caminho):
                continue
            achadas += 1
            destino = os.path.join(PASTA_RETROARCH, biblioteca)
            if os.path.isfile(destino):
                break
            try:
                shutil.copy2(caminho, destino)
                copiadas.append(biblioteca)
            except OSError:
                pass
            break

    if achadas == 0:
        return [], ("Este computador também não tem as bibliotecas. Copie "
                    "a pasta do ARENA de um computador que tenha, ou peca "
                    "a instalação do Visual C++ Redistributable.")
    return copiadas, None


# ---------------------------------------------------------------------------
# BLOCO 8 - Servidor HTTP
# ---------------------------------------------------------------------------

TIPOS = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
}


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


# As UNICAS rotas que outro computador da rede pode chamar quando
# "permitir_rede" esta ligado -- exatamente o que a partida a dois e a
# sincronizacao entre ARENAs precisam (descoberta de colega, testar se
# alcanca, conferir se o arquivo do jogo e o mesmo, trocar placar). Achado
# real na auditoria: antes desta lista, TODAS as 49 rotas ficavam abertas
# pra rede inteira assim que "permitir_rede" era ligado -- incluindo
# apagar perfil, mudar configuracao, instalar cheat e mandar abrir jogo.
# O jogo em si (netplay do RetroArch) nunca passa por aqui: usa a porta
# 55435 dele, direto, separada desta.
ROTAS_REDE_EXTERNA = frozenset((
    "/api/colegas",         # GET - quem esta online, pra tela de amigos
    "/api/ranking",         # GET - placar compartilhado
    "/api/jogo/impressao",  # GET - confere se e o mesmo arquivo de jogo
    "/api/amigo/testar",    # POST - "esse endereco responde?"
    "/api/amigo/codigo",    # POST - adicionar amigo pelo codigo
    "/api/partida/testar",  # POST - pre-voo do Jogar Junto
    "/api/partida/cheguei", # POST - o convidado chegou (o anfitriao esperava)
    "/api/sinc/ola",        # POST - handshake da sincronizacao
    "/api/sinc/receber",    # POST - recebe placar/sessoes de outro ARENA
))


def _sem_nan(texto):
    """json.loads aceitaria NaN e Infinity (nao sao JSON de verdade): numero
    que nao e' numero nao entra em placar nem em configuracao."""
    raise ValueError("numero invalido: %s" % texto)


class Manipulador(BaseHTTPRequestHandler):

    protocol_version = "HTTP/1.1"
    # Tempo maximo esperando o outro lado (achado de 01/10/2026, tentando
    # quebrar o ARENA): sem isto, uma conexao parada -- ou um pedido que
    # promete 1 MB e manda 10 bytes -- prendia uma linha de execucao do
    # servidor PARA SEMPRE. Com "Aceitar conexoes da rede", qualquer colega
    # podia travar o ARENA abrindo conexoes assim. 30 s nao atrapalha
    # ninguem: e' tempo SEM receber nada, nao tempo de processar.
    timeout = 30

    def log_message(self, formato, *args):
        pass

    def pedido_e_local(self):
        """O pedido veio deste MESMO computador (qualquer um dos enderecos
        dele), e nao de outra maquina na rede?"""
        origem = self.client_address[0]
        if origem == "127.0.0.1":
            return True
        return origem in {e["ip"] for e in enderecos_locais()}

    def host_confiavel(self):
        """O cabecalho Host e' um nome deste computador?

        Protecao contra DNS rebinding (achado da Fase 8 da auditoria,
        provado com testes\\teste_dns_rebinding.py): um site faz o proprio
        nome passar a apontar para 127.0.0.1, e o navegador deixa a pagina
        dele conversar com o ARENA como se fosse a nossa tela. O pedido
        chega de 127.0.0.1 -- parece local --, mas o Host continua com o
        nome do site. A nossa tela sempre usa 127.0.0.1 (ou localhost)."""
        host = (self.headers.get("Host") or "").strip().lower()
        if not host:
            return True  # sem Host nao e' navegador (so programa de linha de comando)
        if host.startswith("["):
            nome = host[1:host.find("]")] if "]" in host else host[1:]
        else:
            nome = host.rsplit(":", 1)[0]
        if nome in ("127.0.0.1", "localhost", "::1"):
            return True
        if nome == socket.gethostname().lower():
            return True
        return nome in {e["ip"] for e in enderecos_locais()}

    def checar_acesso_de_rede(self, caminho):
        """Barra rota sensivel vinda de fora deste computador. Devolve
        True se o pedido pode seguir, False se ja respondeu com erro."""
        if self.pedido_e_local():
            # Pedido deste computador: so aceita se veio da nossa tela, e nao
            # de um site que se disfarcou de 127.0.0.1 (DNS rebinding).
            # Pedido de OUTRA maquina nao passa por aqui: rebinding so ataca
            # o navegador deste computador, e amigo pela internet pode usar
            # um nome no lugar do IP.
            if self.host_confiavel():
                return True
            self.erro(
                "Pedido recusado: ele não veio da tela do ARENA. "
                "Abra o ARENA pelo ARENA.bat.", 403)
            return False
        if caminho in ROTAS_REDE_EXTERNA:
            return True
        self.erro(
            "Esta parte do ARENA só pode ser usada neste computador, não "
            "por outro da rede.", 403)
        return False

    # -- utilitarios ------------------------------------------------------
    def responder_json(self, dados, codigo=200):
        corpo = json.dumps(dados, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(corpo)

    def erro(self, mensagem, codigo=400):
        self.responder_json({"ok": False, "erro": mensagem}, codigo)

    def erro_interno(self, falha):
        """Ultima rede de seguranca de toda rota. Erro do sistema (disco
        cheio, arquivo em uso, rede) vira frase em portugues -- achado da
        revisao pos-auditoria: disco cheio chegava na tela como
        "[Errno 28] No space left on device". Erro de programa (defeito do
        ARENA) mantem o detalhe tecnico, que e' o que o professor precisa
        para achar a causa, mas com o "o que fazer" na frente."""
        if isinstance(falha, (OSError, urllib.error.URLError)):
            return self.erro(traduzir_erro_do_sistema(falha, "concluir o pedido"), 500)
        # Curto: um erro que carrega o pedido inteiro (2 MB, no fuzz de
        # 01/10/2026) enchia a janela preta e a tela.
        detalhe = repr(falha)
        if len(detalhe) > 300:
            detalhe = detalhe[:300] + "..."
        print("[ARENA] Erro interno: %s" % detalhe)
        return self.erro("Algo deu errado aqui dentro do ARENA. Tente de novo; "
                         "se continuar, chame o professor e mostre isto: %s" % detalhe, 500)

    LIMITE_CORPO = 4 * 1024 * 1024

    def ler_corpo(self):
        """Le o JSON enviado. Devolve (dados, erro); o codigo HTTP do erro
        fica em self.status_corpo (413 grande demais, 400 o resto)."""
        self.status_corpo = 400
        dados, erro = self._ler_corpo()
        if erro is None and not isinstance(dados, dict):
            # [] ou "texto" no lugar de {...}: antes chegava nas rotas e
            # virava erro 500 (dados.get de uma lista).
            return {}, "O conteúdo enviado precisa ser um objeto JSON ({...})."
        return dados, erro

    def _ler_corpo(self):
        """Le o JSON enviado. Devolve (dados, erro).

        Quando o corpo passa do limite, o servidor precisa ESVAZIAR a
        conexao antes de responder. Sem isso o cliente recebe um corte
        seco de conexao, sem saber o que aconteceu - foi o que apareceu
        no teste de corpo gigante.
        """
        try:
            tamanho = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return {}, "Tamanho do envio inválido."

        if tamanho <= 0:
            return {}, None

        if tamanho > self.LIMITE_CORPO:
            self.status_corpo = 413
            # Descarta o que veio, em pedacos, para nao guardar tudo na
            # memoria so para jogar fora.
            restante = tamanho
            while restante > 0:
                pedaco = self.rfile.read(min(65536, restante))
                if not pedaco:
                    break
                restante -= len(pedaco)
            return {}, ("Envio grande demais (%.1f MB). O limite e %d MB. "
                        "Sincronize por partes."
                        % (tamanho / 1048576.0, self.LIMITE_CORPO // 1048576))

        try:
            bruto = self.rfile.read(tamanho)
        except (TimeoutError, OSError):
            # O outro lado prometeu mais do que mandou e parou (ver o
            # 'timeout' da classe). A conexao fica inutil: fecha.
            self.close_connection = True
            self.status_corpo = 408
            return {}, "O envio parou no meio (tempo esgotado)."
        try:
            return json.loads(bruto.decode("utf-8"), parse_constant=_sem_nan), None
        except (ValueError, UnicodeDecodeError, RecursionError):
            # RecursionError: [[[[...]]]] com milhares de niveis.
            return {}, "O conteúdo enviado não é um JSON válido."

    # -- GET --------------------------------------------------------------
    def do_GET(self):
        caminho = urllib.parse.urlparse(self.path).path

        if caminho.startswith("/api/"):
            if not self.checar_acesso_de_rede(caminho):
                return
            try:
                return self.api_get(caminho)
            except Exception as falha:
                return self.erro_interno(falha)

        if caminho in ("/", "/index.html"):
            caminho = "/index.html"

        arquivo = os.path.normpath(os.path.join(PASTA_LAUNCHER, caminho.lstrip("/")))
        if not dentro_da_pasta(arquivo, PASTA_LAUNCHER) or not os.path.isfile(arquivo):
            return self.send_error(404, "Arquivo nao encontrado")

        with open(arquivo, "rb") as origem:
            conteudo = origem.read()

        self.send_response(200)
        self.send_header("Content-Type", TIPOS.get(
            os.path.splitext(arquivo)[1].lower(), "application/octet-stream"))
        self.send_header("Content-Length", str(len(conteudo)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(conteudo)

    def api_get(self, caminho):
        if caminho == "/api/estado":
            config = carregar_config()
            return self.responder_json({
                "maquina": MAQUINA,
                "retroarch_presente": os.path.isfile(EXECUTAVEL_RETROARCH),
                "arquivos_sistema": contar_arquivos_sistema(),
                "runtime_ok": MAQUINA["runtime_ok"],
                # Lido do vigia, que testa em segundo plano. A tela nunca
                # espera pela rede.
                "servidores_online": VIGIA["online"],
                "rede_checada_ha": (
                    round(time.time() - VIGIA["ultima_checagem"])
                    if VIGIA["ultima_checagem"] else None),
                "config": config,
                # Valores que realmente vao valer, ja com o perfil aplicado.
                # Sem isso a aba Avancado mostraria estado errado.
                "efetivas": opcoes_efetivas(config),
                "perfis": dict(
                    [("automatico", PERFIL_AUTOMATICO)] +
                    [(c, {"rotulo": v["rotulo"], "resumo": v["resumo"]})
                     for c, v in PERFIS_GRAFICOS.items()]),
                "versao": VERSAO,
                # Codigo curto que o aluno passa ao colega em vez do
                # endereco. O colega digita e o ARENA acha na rede.
                "codigo_amigo": config["dispositivo_id"],
                "tem_foto_perfil": bool(foto_perfil_caminho()),
                "capacidade": CAPACIDADE,
                "economico": ECONOMICO,
                "versao_confere": VERSAO,
                "vigia_suspenso": VIGIA["suspenso"],
                "fechamentos": ler_fechamentos(),
                "repasses": graficos.repasses_disponiveis(),
                "controles": graficos.CONTROLES_CONHECIDOS,
                "consoles_botoes": [
                    {"id": p["id"], "nome": p["nome"]}
                    for p in carregar_catalogo()
                    if p["id"] in graficos.consoles_com_botoes()],
                "externos": graficos.situacao_dos_externos(carregar_catalogo()),
                "rede_ps2": {
                    "driver_instalado": graficos.npcap_instalado(),
                    "jogos": next(
                        ((p.get("externo") or {}).get("jogos_system_link", [])
                         for p in carregar_catalogo() if p["id"] == "ps2"), []),
                },
                "bios_disponiveis": graficos.bios_disponiveis(PASTA_SISTEMA),
                "memory_cards": graficos.listar_memory_cards(PASTA_SAVES),
                # "escolhiveis": os arquivos que o nucleo daquele console
                # deixa escolher de verdade. Vazio = o nucleo acha a BIOS
                # sozinho, e a tela diz isso em vez de oferecer uma escolha
                # que nao faria nada (achado da revisao pos-auditoria).
                "bios_consoles": [
                    {"id": p["id"], "nome": p["nome"],
                     "escolhiveis": graficos.bios_que_o_nucleo_aceita(
                         nome_curto_do_core(p.get("core", "")),
                         [b["arquivo"] for b in graficos.bios_disponiveis(PASTA_SISTEMA)])}
                    for p in carregar_catalogo()
                    if p["arquivos_sistema"] > 0],
                "shader": os.path.basename(
                    graficos.filtro_de_tela("snes")) or None,
                "porta_partida": graficos.PORTA_PARTIDA,
                "recursos": recursos_visiveis(),
                "grupos": carregar_recursos()["grupos"],
                "jogo_em_andamento": dict(JOGO_EM_ANDAMENTO),
                "ultimo_problema": dict(ULTIMO_PROBLEMA) or None,
                "pendentes": contar_pendentes(),
                "mala": {
                    "caminho": caminho_da_mala(),
                    "existe": os.path.isfile(caminho_da_mala()),
                },
                "meu_endereco": "http://%s:%d" % (ip_da_rede(), PORTA),
                "enderecos": enderecos_locais(),
                "internet": VIGIA["internet"],
                "pacotes": listar_pacotes(),
                "pastas": {
                    "saves": PASTA_SAVES,
                    "capturas": PASTA_CAPTURAS,
                    "jogos": os.path.join(PASTA_JOGOS, "pessoais"),
                    "sistema": PASTA_SISTEMA,
                    "raiz": RAIZ,
                },
            })

        if caminho == "/api/catalogo":
            corpo = montar_catalogo()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(corpo)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(corpo)
            return

        if caminho == "/api/perfis-controle":
            parametros = urllib.parse.parse_qs(
                urllib.parse.urlparse(self.path).query)
            tipo = (parametros.get("tipo") or ["xbox360"])[0]
            console = (parametros.get("console") or ["ps1"])[0]
            config = carregar_config()
            escolhas = config.get("perfil_controle", {}).get(console, {})

            perfil, erro = controles.montar_perfil(
                tipo, console,
                usar_direcional=escolhas.get("direcional", True),
                usar_analogico_esq=escolhas.get("analogico_esq", True),
                usar_analogico_dir=escolhas.get("analogico_dir", True),
                vibracao=escolhas.get("vibracao", True))
            if erro:
                return self.erro(erro)

            perfil["tipos"] = controles.tipos_de_controle()
            perfil["tipo_escolhido"] = config.get("tipo_controle", "xbox360")
            perfil["dispositivo_extra"] = escolhas.get("extra", "")
            return self.responder_json(perfil)

        if caminho == "/api/jogo/impressao":
            parametros = urllib.parse.parse_qs(
                urllib.parse.urlparse(self.path).query)
            titulo = (parametros.get("titulo") or [""])[0].strip().lower()
            achado = next((j for j in manifesto()["jogos"]
                           if j["titulo"].lower() == titulo), None)
            if not achado:
                return self.erro("Este computador não tem esse jogo. Para jogar junto, os dois precisam do mesmo arquivo de jogo: copie o jogo para a pasta jogos\\pessoais do outro computador.", 404)
            marca = impressao_do_jogo(achado)
            if not marca:
                return self.erro("Não consegui ler o arquivo do jogo para comparar. Feche o jogo, se estiver aberto, e tente de novo.", 404)
            return self.responder_json(marca)

        # ---- acervo de jogos livres ---------------------------------------
        if caminho == "/api/como-colocar":
            # O que falta aos emuladores de fora (BIOS do PS2, firmware do
            # PS3) vem da mesma conta que o cartao do jogo usa.
            falta = {}
            for plataforma in carregar_catalogo():
                if plataforma.get("externo"):
                    caminho_externo, dados_externo = graficos.achar_externo(plataforma)
                    falta[plataforma["id"]] = (
                        graficos.falta_para_o_externo(dados_externo["nome"], caminho_externo)
                        if caminho_externo else "o emulador não está na pasta")
            # O formato do disco do ARENA: no FAT32 nao cabe arquivo maior que
            # 4 GB, e a tela avisa nos consoles de jogo grande ANTES de alguem
            # copiar (auditoria 3, Fase 6; antes so o VERIFICAR.bat dizia).
            return self.responder_json({
                "ok": True, "pasta_bios": bios.NOME_DA_PASTA,
                "formato_do_disco": hardware.sistema_de_arquivos(RAIZ) or "",
                "consoles": como_colocar.guia(carregar_catalogo(), PASTA_SISTEMA, PASTA_JOGOS, falta)})

        # As BIOS de cada console, como estao agora (Ajustes -> Emuladores ->
        # BIOS dos consoles): ativa, de outra versao ou falta, e onde fica a
        # prateleira de cada uma (a pasta BIOS do ARENA, servidor\bios.py).
        # Andamento do "Arrumar" demorado (descompactar um jogo de CD).
        if caminho == "/api/arrumar/progresso":
            parametros = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            tarefa = arrumar.progresso((parametros.get("tarefa") or [""])[0][:40])
            if not tarefa:
                return self.erro("Essa tarefa não existe mais. Clique em Atualizar lista.", 404)
            return self.responder_json(dict(ok=True, **tarefa))

        if caminho == "/api/bios":
            itens = bios.situacao(RAIZ)
            return self.responder_json({"ok": True, "pasta": bios.NOME_DA_PASTA, "itens": itens,
                                        "resumo": bios.resumo(itens), "sem_bios": bios.consoles_sem_bios()})

        if caminho == "/api/capas/progresso":
            return self.responder_json(dict(ok=True, **situacao_das_capas()))

        if caminho == "/api/acervo":
            return self.responder_json({
                "itens": acervo.listar(),
                "fontes": acervo.fontes(),
            })

        if caminho == "/api/biblioteca-online":
            parametros = urllib.parse.parse_qs(
                urllib.parse.urlparse(self.path).query)
            consulta = (parametros.get("q") or [""])[0].strip()
            if len(consulta) < 2:
                return self.responder_json({"itens": [],
                                            "consoles": internet_archive.consoles_da_biblioteca()})
            if not VIGIA["internet"]:
                return self.erro("Sem internet agora. Ligue o computador na internet para buscar; "
                                 "os jogos da pasta e o acervo local continuam "
                                 "funcionando.", 503)
            try:
                return self.responder_json({"itens": internet_archive.buscar(consulta),
                                            "consoles": internet_archive.consoles_da_biblioteca()})
            except internet_archive.FalhaDeRede as falha:
                # A rede falhou ou pediu login: a frase ja diz o que fazer
                # (antes a tela dizia "nenhum resultado").
                return self.erro(str(falha), 502)
            except Exception as falha:
                return self.erro(traduzir_erro_do_sistema(falha, "pesquisar"), 502)

        # ---- conquistas da turma ------------------------------------------
        if caminho == "/api/conquistas":
            return self.responder_json(montar_conquistas())

        if caminho == "/api/barreiras":
            # O que esta deixando ESTE computador lento. So sob pedido (botao
            # "Verificar agora"): custa ~5 s de PowerShell, entao nunca roda
            # sozinho em segundo plano -- o ARENA parado continua a 0%.
            return self.responder_json(diagnostico_de_barreiras(
                forcar=urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get("forcar") == ["1"]))

        if caminho == "/api/capa":
            parametros = urllib.parse.parse_qs(
                urllib.parse.urlparse(self.path).query)
            pedido = (parametros.get("arquivo") or [""])[0]
            alvo = capa_permitida(pedido)
            if not alvo:
                return self.erro("Capa não encontrada.", 404)
            # mini=280/480: a miniatura guardada, se ja existir (ver
            # gravar_miniatura). Senao, a capa cheia -- e a tela faz a
            # miniatura dela.
            try:
                largura = int((parametros.get("mini") or ["0"])[0])
            except ValueError:
                largura = 0
            if largura in LARGURAS_MINIATURA:
                alvo = miniatura_pronta(alvo, largura) or alvo

            tipos = {".png": "image/png", ".jpg": "image/jpeg",
                     ".jpeg": "image/jpeg", ".webp": "image/webp"}
            tipo = tipos[os.path.splitext(alvo)[1].lower()]
            try:
                with open(alvo, "rb") as arquivo:
                    dados_imagem = arquivo.read()
            except OSError:
                return self.erro("Não consegui ler a capa.", 404)

            self.send_response(200)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(dados_imagem)))
            # A arte nao muda: o navegador guarda e nao pede de novo.
            self.send_header("Cache-Control", "max-age=86400")
            self.end_headers()
            self.wfile.write(dados_imagem)
            return

        if caminho == "/api/perfil/foto":
            alvo = foto_perfil_caminho()
            if not alvo:
                return self.erro("Sem foto de perfil ainda.", 404)

            tipos = {".png": "image/png", ".jpg": "image/jpeg", ".webp": "image/webp"}
            tipo = tipos.get(os.path.splitext(alvo)[1].lower(), "application/octet-stream")
            try:
                with open(alvo, "rb") as arquivo:
                    dados_imagem = arquivo.read()
            except OSError:
                return self.erro("Não consegui ler a foto.", 404)

            self.send_response(200)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(dados_imagem)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(dados_imagem)
            return

        if caminho == "/api/colegas":
            return self.responder_json({"colegas": colegas_na_rede()})

        if caminho == "/api/partida/estado":
            # So deste computador: a janela "Esperando o jogador 2".
            return self.responder_json(estado_da_partida())
        if caminho == "/api/partida/procurar":
            # So deste computador (nao esta em ROTAS_REDE_EXTERNA): e' a tela
            # do convidado perguntando "quem tem partida aberta agora?".
            # Com ?rede=1 (a janela de Jogar junto abriu), ja pergunta ao
            # Windows, em segundo plano, se a rede e' Publica -- para o aviso
            # de quem abre a partida nao atrasar o "Comecar". Sem ele (a busca
            # de quando a tela abre), nao: seria um PowerShell a mais em toda
            # abertura do ARENA, no Celeron (revisao da Fase 4).
            if "rede=1" in urllib.parse.urlparse(self.path).query:
                preparar_categoria_da_rede()
            config = carregar_config()
            lista, corrigidos = procurar_partidas(config)
            if corrigidos:
                gravar_enderecos_de_amigos(config.get("servidores"))
            return self.responder_json({
                "colegas": lista,
                "minha_partida": partida_aberta_agora(),
            })

        if caminho == "/api/mapeamento":
            dados_mapa = controles.ler()
            return self.responder_json({
                "mapeamento": dados_mapa,
                "resumo": controles.resumo(dados_mapa),
                "botoes": controles.BOTOES,
                "jogadores": list(controles.JOGADORES),
            })

        if caminho == "/api/botoes":
            parametros = urllib.parse.parse_qs(
                urllib.parse.urlparse(self.path).query)
            plataforma = (parametros.get("console") or [""])[0]
            return self.responder_json(
                {"botoes": graficos.botoes_do_console(plataforma)})

        # Havia tambem o apelido "/api/sinc/ranking", removido na auditoria 2:
        # nenhuma versao do ARENA (nem as duas originais) chama esse nome.
        if caminho == "/api/ranking":
            return self.responder_json(ler_ranking())

        if caminho == "/api/jogo":
            parametros = urllib.parse.parse_qs(
                urllib.parse.urlparse(self.path).query)
            jogo = achar_jogo((parametros.get("id") or [""])[0])
            if not jogo:
                return self.erro("Jogo não encontrado. Ele pode ter sido movido ou apagado. "
                                 "Clique em Atualizar lista e tente de novo.", 404)
            return self.responder_json({
                "titulo": jogo["titulo"],
                "plataforma": jogo["plataforma"],
                "plataforma_nome": jogo["plataforma_nome"],
                "ambiguo": jogo.get("ambiguo", False),
                "corrigido": jogo.get("corrigido", False),
                "consoles": sorted(
                    ({"id": p["id"], "nome": p["nome"], "pasta": p["pasta"]}
                     for p in carregar_catalogo()),
                    key=lambda p: p["nome"]),
                "sugestao": jogo.get("sugestao"),
                "pasta_atual": os.path.dirname(jogo["arquivo"]),
                "estados": cheats.listar_estados(jogo, nucleo_das_pastas(jogo)),
                "tem_save": cheats.tem_save(jogo, nucleo_das_pastas(jogo)),
                "cheats": cheats.ler_cheats(jogo, nucleo_das_pastas(jogo)),
            })

        return self.erro("Rota não encontrada.", 404)

    # -- POST -------------------------------------------------------------
    def do_POST(self):
        caminho = urllib.parse.urlparse(self.path).path
        try:
            if not self.checar_acesso_de_rede(caminho):
                return
            # So aceita Content-Type application/json -- e' o que a propria
            # tela (pedir(), app.js) e a sincronizacao entre ARENAs sempre
            # mandam. Achado real na auditoria, provado ao vivo com uma
            # pagina de outra origem: uma aba qualquer aberta no MESMO
            # navegador conseguia mandar POST pra qualquer rota daqui
            # usando Content-Type "text/plain" -- esse tipo nao obriga o
            # navegador a perguntar permissao (preflight CORS) antes de
            # mandar, entao o pedido chegava e era processado do mesmo
            # jeito, mesmo sem o site nunca poder LER a resposta (CSRF as
            # cegas). Esta checagem barra esse pedido aqui (Content-Type
            # errado, 415). Se em vez disso a pagina tentasse mandar
            # "application/json" de verdade pra passar por esta checagem,
            # ela deixaria de ser um "pedido simples" e o proprio navegador
            # exigiria permissao explicita (preflight) antes de mandar --
            # permissao que este servidor nunca da, entao o navegador
            # bloqueia sozinho. Ou de um jeito ou de outro, o pedido nao
            # chega a mudar nada. Nao substitui uma trava de verdade (rota
            # por rede, ver achado maior desta fase), mas fecha o jeito
            # mais facil de abusar disso.
            tipo = (self.headers.get("Content-Type") or "").split(";")[0].strip().lower()
            if tipo != "application/json":
                return self.erro(
                    "Content-Type precisa ser application/json.", 415)
            dados, falha_corpo = self.ler_corpo()
            if falha_corpo:
                return self.erro(falha_corpo, self.status_corpo)
            return self.api_post(caminho, dados)
        except Exception as falha:
            return self.erro_interno(falha)

    def api_post(self, caminho, dados):

        # ---- recebe recordes de outro ARENA (papel de servidor) ----------
        if caminho == "/api/sinc/receber":
            placares = dados.get("placares")
            sessoes = dados.get("sessoes")
            if not isinstance(placares, list) or not isinstance(sessoes, list):
                return self.erro("Formato do lote inválido.")
            if len(placares) + len(sessoes) > 5000:
                return self.erro("Lote grande demais. Sincronize por partes.")
            meu_id = carregar_config()["dispositivo_id"]

            # Remetente com o MESMO codigo que o nosso. Duas causas:
            #
            #  - o endereco aponta mesmo para ca (o aluno digitou o proprio
            #    endereco), e ai recusar e o certo;
            #  - sao dois computadores diferentes que sairam da mesma
            #    imagem de laboratorio, com o mesmo nome e o mesmo usuario.
            #
            # Quem esta batendo na porta vem de um IP. Se esse IP nao e um
            # dos nossos, e o segundo caso: o codigo esta repetido e quem
            # tem que ceder somos nos, porque somos quem percebeu.
            if str(dados.get("dispositivo")) == meu_id:
                origem = self.client_address[0]
                meus = {e["ip"] for e in enderecos_locais()} | {"127.0.0.1"}

                if origem not in meus:
                    config = carregar_config()
                    novo = uuid.uuid4().hex[:12]
                    print("[ARENA] Codigo repetido com %s. Troquei o nosso "
                          "de %s para %s." % (origem, meu_id, novo))
                    config["dispositivo_id"] = novo
                    config["codigo_proprio"] = True
                    salvar_config(config)
                    return self.erro(
                        "Vocês dois tinham o mesmo código de aparelho. Já "
                        "troquei o meu. Peça para ele sincronizar de novo.", 409)

                return self.erro(
                    "Este endereço é o próprio computador. Digite o endereço "
                    "do servidor da sala.", 409)

            novos = gravar_recebidos(placares, sessoes)

            # Resposta carrega tambem o que HA DE NOVO AQUI desde a ultima
            # visita do outro lado. Assim uma unica conversa serve para os
            # dois sentidos, em vez de duas idas e voltas.
            meus_placares, minhas_sessoes, ate = registros_desde(
                dados.get("desde"), exceto=dados.get("dispositivo"))

            print("[ARENA] %s: recebi %d, devolvi %d"
                  % (str(dados.get("apelido") or dados.get("dispositivo"))[:24],
                     novos, len(meus_placares) + len(minhas_sessoes)))

            return self.responder_json({
                "ok": True, "novos": novos, "servidor_id": meu_id,
                "apelido": carregar_config().get("apelido", ""),
                "placares": meus_placares, "sessoes": minhas_sessoes,
                "ate": ate,
            })

        # ---- envia os proprios recordes (papel de cliente) ---------------
        if caminho == "/api/mala":
            resultado = trocar_pela_mala(dados.get("caminho") or None)
            if not resultado["ok"]:
                return self.erro(resultado["erro"])
            return self.responder_json(resultado)

        if caminho == "/api/sincronizar":
            resultado = sincronizar(carregar_config())
            if not resultado["ok"]:
                return self.responder_json(resultado, 502)
            return self.responder_json(resultado)

        # ---- perfil de controle por console --------------------------------
        if caminho == "/api/perfil-controle":
            config = carregar_config()

            if dados.get("tipo_controle"):
                validos = {t["id"] for t in controles.tipos_de_controle()}
                if str(dados["tipo_controle"]) not in validos:
                    return self.erro("Tipo de controle desconhecido. Escolha um da lista em "
                                 "Ajustes → Controles.")
                config["tipo_controle"] = str(dados["tipo_controle"])

            console = str(dados.get("console", "")).strip().lower()
            if console:
                if console not in {p["id"] for p in carregar_catalogo()}:
                    return self.erro("Console desconhecido. Escolha um console da lista "
                                 "(ou confira a pasta do jogo em jogos\\pessoais).")
                atual = dict(config.get("perfil_controle", {}).get(console, {}))
                for chave in ("direcional", "analogico_esq",
                              "analogico_dir", "vibracao"):
                    if chave in dados:
                        atual[chave] = bool(dados[chave])
                if "extra" in dados:
                    extra = str(dados["extra"] or "")
                    atual["extra"] = extra if extra in ("mouse", "teclado") else ""
                config.setdefault("perfil_controle", {})[console] = atual

            salvar_config(config)
            gravar_override(config)
            return self.responder_json({"ok": True, "config": config})

        # ---- mapear teclas e botoes ---------------------------------------
        if caminho == "/api/mapeamento/definir":
            novo, erro = controles.definir(
                str(dados.get("jogador", "1")), str(dados.get("botao", "")),
                str(dados.get("tipo", "")), dados.get("valor"))
            if erro:
                return self.erro(erro)
            # Regrava agora para valer no proximo jogo, sem precisar reabrir.
            gravar_override(carregar_config())
            return self.responder_json({"ok": True, "mapeamento": novo,
                                        "resumo": controles.resumo(novo)})

        if caminho == "/api/mapeamento/padrao":
            jogador = str(dados.get("jogador", "1"))
            if dados.get("tipo") == "controle":
                novo, erro = controles.aplicar_padrao_controle(jogador)
            else:
                novo, erro = controles.aplicar_padrao(jogador)
            if erro:
                return self.erro(erro)
            gravar_override(carregar_config())
            return self.responder_json({"ok": True, "mapeamento": novo,
                                        "resumo": controles.resumo(novo)})

        if caminho == "/api/mapeamento/limpar":
            novo = controles.limpar(str(dados.get("jogador", "")) or None)
            gravar_override(carregar_config())
            return self.responder_json({"ok": True, "mapeamento": novo,
                                        "resumo": controles.resumo(novo)})

        # ---- acervo: cadastrar, instalar, remover -------------------------
        if caminho == "/api/acervo/salvar":
            try:
                item = acervo.salvar(dados.get("item") or {})
            except ValueError as falha:
                return self.erro(str(falha))
            except OSError as falha:
                return self.erro(traduzir_erro_do_sistema(falha, "gravar o acervo"))
            return self.responder_json({"ok": True, "item": item})

        if caminho == "/api/acervo/remover":
            try:
                acervo.remover(str(dados.get("id", "")))
            except ValueError as falha:
                return self.erro(str(falha), 404)
            return self.responder_json({"ok": True})

        if caminho == "/api/acervo/instalar":
            with TRAVA_JOGO:
                if JOGO_EM_ANDAMENTO["ativo"]:
                    return self.erro("Feche o jogo aberto antes de baixar.", 409)
            try:
                resultado = acervo.instalar(str(dados.get("id", "")))
            except ValueError as falha:
                return self.erro(str(falha))
            except OSError as falha:
                return self.erro(traduzir_erro_do_sistema(falha, "baixar o jogo"), 502)
            limpar_caches()
            manifesto(forcar=True)
            return self.responder_json(dict(ok=True, **resultado))

        if caminho == "/api/biblioteca-online/instalar":
            with TRAVA_JOGO:
                if JOGO_EM_ANDAMENTO["ativo"]:
                    return self.erro("Feche o jogo aberto antes de baixar.", 409)
            try:
                resultado = internet_archive.instalar(
                    str(dados.get("id", "")), str(dados.get("arquivo", "")),
                    str(dados.get("plataforma", "")))
            except ValueError as falha:
                return self.erro(str(falha))
            except Exception as falha:
                return self.erro(traduzir_erro_do_sistema(falha, "baixar o jogo"), 502)
            limpar_caches()
            manifesto(forcar=True)
            return self.responder_json(dict(ok=True, **resultado))

        # ---- adicionar amigo pelo codigo ----------------------------------
        if caminho == "/api/amigo/codigo":
            codigo = str(dados.get("codigo", "")).strip()
            vizinho = next((v for v in colegas_na_rede()
                            if v["id"] == codigo), None)
            if not vizinho:
                return self.erro("Não achei ninguém com esse código na rede. "
                                 "Os dois precisam estar na mesma rede e com "
                                 "'Aceitar conexões' ligado.", 404)
            return self.api_post("/api/amigo/adicionar",
                                 {"apelido": vizinho["apelido"],
                                  "url": vizinho["url"],
                                  "id": vizinho["id"]})

        # ---- comecar do zero: novo perfil ---------------------------------
        if caminho == "/api/perfil/novo":
            if str(dados.get("confirmar")) != "sim":
                return self.erro("Falta confirmar. Clique em Começar do zero de novo e confirme.")

            with TRAVA_JOGO:
                if JOGO_EM_ANDAMENTO["ativo"]:
                    return self.erro("Feche o jogo aberto antes.", 409)

            apagados = []

            # Guarda uma copia antes de apagar. Se alguem clicar por
            # engano, o progresso ainda esta em backup. Por isso a copia
            # precisa dar certo de verdade -- se falhar (pen drive cheio,
            # pasta de backup virou so-leitura, midia removida no meio),
            # o apagamento e cancelado em vez de seguir sem rede de
            # seguranca (achado real na auditoria: antes, uma falha aqui
            # era engolida em silencio e o perfil era apagado do mesmo
            # jeito, sem copia nenhuma).
            try:
                copia_de_seguranca = fazer_backup()
            except Exception:
                copia_de_seguranca = None
            if not copia_de_seguranca:
                return self.erro(
                    "Não consegui garantir uma cópia de segurança antes de "
                    "apagar. Nada foi apagado. Verifique o espaço livre no "
                    "disco/pen drive e tente de novo.", 500)

            for arquivo in ("arena.db", "config.json", "controles.json",
                            "manifesto.json", "arena_override.cfg"):
                alvo = os.path.join(PASTA_DADOS, arquivo)
                if os.path.isfile(alvo):
                    try:
                        os.remove(alvo)
                        apagados.append(arquivo)
                    except OSError:
                        pass

            if dados.get("apagar_saves"):
                for pasta in (PASTA_SAVES, PASTA_STATES, PASTA_CHEATS):
                    for atual, _sub, arquivos in os.walk(pasta):
                        for arquivo in arquivos:
                            if arquivo.lower() == "leia.txt":
                                continue
                            try:
                                os.remove(os.path.join(atual, arquivo))
                                apagados.append(arquivo)
                            except OSError:
                                pass

            limpar_caches()
            preparar_banco()
            with TRAVA_VIZINHOS:
                VIZINHOS.clear()

            novo = carregar_config()
            print("[ARENA] Perfil novo. Codigo do aparelho: %s"
                  % novo["dispositivo_id"])
            return self.responder_json({
                "ok": True,
                "apagados": len(apagados),
                "dispositivo_id": novo["dispositivo_id"],
            })

        # ---- conferir se a partida a dois tem caminho ---------------------
        if caminho == "/api/partida/cheguei":
            # Vem do ARENA do amigo (ROTAS_REDE_EXTERNA): "entrei na sua
            # partida". Se este computador esperava, abre o jogo agora.
            bruto = dados.get("apelido") if isinstance(dados, dict) else ""
            apelido_amigo = "".join(c for c in str(bruto or "")[:24] if c.isprintable()).strip()
            if comecar_partida_pendente(apelido_amigo or "Seu amigo"):
                return self.responder_json({"ok": True, "abrindo": True})
            if partida_aberta_agora():
                return self.responder_json({"ok": True, "abrindo": False})
            return self.erro("Não há partida aberta neste computador. Peça para o amigo "
                             "abrir de novo: Desafio em rede → Eu abro a partida.", 404)
        if caminho == "/api/partida/comecar":
            # "Comecar sem esperar" (so deste computador).
            return self.responder_json({"ok": True, "abrindo": comecar_partida_pendente("")})
        if caminho == "/api/partida/cancelar":
            return self.responder_json({"ok": True, "cancelada": cancelar_partida_pendente()})
        if caminho == "/api/partida/testar":
            bruto = str(dados.get("endereco", "")).strip()
            alvo = normalizar_url(bruto)
            partes = urllib.parse.urlsplit(alvo)
            endereco = partes.hostname or ""
            # A porta vem do endereco que o colega passou. Usar a porta
            # local aqui faria o ARENA perguntar a si mesmo se o arquivo e
            # o mesmo - e a resposta seria sempre "sim".
            porta_dele = partes.port or PORTA
            if not endereco:
                return self.erro(ENDERECO_ESTRANHO if bruto else "Informe o endereço do colega.")

            resultado = {"endereco": endereco, "arena": False,
                         "partida": False, "arquivo": None}

            # Resolve o nome/endereco UMA vez so, antes de tentar as duas
            # portas. Achado real na auditoria, medido ao vivo: cada
            # socket.create_connection() faz a PROPRIA resolucao de nome
            # por baixo, e no Windows isso nao respeita o timeout do
            # socket -- um endereco invalido custava ~2,6s so pra falhar a
            # resolucao, DUAS vezes seguidas (~5,3s no total) pra um pedido
            # que devia ser rejeitado na hora. Resolvendo uma vez e
            # reusando o IP, o custo de um endereco ruim cai pela metade.
            try:
                ip = socket.gethostbyname(endereco)
            except (OSError, UnicodeError):
                resultado["diagnostico"] = (
                    "Não alcanço o computador dele. Confira o endereço, e se "
                    "ele ligou 'Aceitar conexões da rede' e reabriu o ARENA.")
                return self.responder_json(resultado)

            # 1. O ARENA dele responde? Isso prova que as maquinas se veem.
            try:
                with socket.create_connection((ip, porta_dele), timeout=2.0):
                    resultado["arena"] = True
            except OSError:
                pass

            # 2. E a porta da partida? Quem responde ali e o RetroArch, e
            #    ele so escuta enquanto a partida esta aberta.
            try:
                with socket.create_connection(
                        (ip, graficos.PORTA_PARTIDA), timeout=2.0):
                    resultado["partida"] = True
            except OSError:
                pass

            # Porta da partida fechada, mas o ARENA dele responde: ele pode estar
            # esperando o jogador 2 (o jogo so abre quando alguem entra). Pergunta
            # a ele, do mesmo jeito que a lista de partidas pergunta.
            if resultado["arena"] and not resultado["partida"]:
                try:
                    retorno = falar_com(alvo, "/api/sinc/ola", {}, "POST", 2)
                    dele = limpar_partida_recebida(retorno.get("partida"))
                    resultado["esperando"] = bool(dele and dele.get("esperando"))
                except Exception:
                    pass

            # O arquivo e o mesmo? E a causa mais comum de "conecta e nao
            # comeca": titulo parecido, arquivo diferente.
            titulo = str(dados.get("titulo", "")).strip()
            if resultado["arena"] and titulo:
                meu = next((j for j in manifesto()["jogos"]
                            if j["titulo"].lower() == titulo.lower()), None)
                minha_marca = impressao_do_jogo(meu) if meu else None
                try:
                    pedido = urllib.request.Request(
                        "http://%s:%d/api/jogo/impressao?titulo=%s"
                        % (endereco, porta_dele, urllib.parse.quote(titulo)),
                        headers={"User-Agent": "ARENA"})
                    with urllib.request.urlopen(pedido, timeout=4) as resposta:
                        dele = json.loads(resposta.read().decode("utf-8"))
                except Exception:
                    dele = None

                if minha_marca and dele:
                    igual = (minha_marca["marca"] == dele.get("marca"))
                    resultado["arquivo"] = "igual" if igual else "diferente"
                elif minha_marca and dele is None:
                    resultado["arquivo"] = "ele nao tem"
                elif not minha_marca:
                    resultado["arquivo"] = "eu nao tenho"

            if resultado["arquivo"] == "diferente":
                resultado["diagnostico"] = (
                    "Vocês têm o mesmo jogo, mas ARQUIVOS DIFERENTES - região "
                    "ou versão. A partida não começa assim. Um dos dois "
                    "precisa copiar o arquivo do outro.")
            elif resultado["arquivo"] == "eu nao tenho":
                resultado["diagnostico"] = (
                    "Esse jogo não está na SUA lista. Clique em Atualizar "
                    "lista, ou peca o arquivo ao colega.")
            elif resultado["arquivo"] == "ele nao tem":
                resultado["diagnostico"] = (
                    "Ele não tem esse jogo na lista. Passe o arquivo para ele "
                    "antes de comecar.")
            elif resultado["arena"] and resultado.get("esperando"):
                resultado["diagnostico"] = (
                    "Tudo certo. Ele abriu a partida e está esperando você: clique "
                    "em Começar e o jogo abre nos dois computadores.")
            elif resultado["arena"] and resultado["partida"]:
                resultado["diagnostico"] = (
                    "Tudo certo. A partida dele está aberta e você alcança.")
            elif resultado["arena"]:
                resultado["diagnostico"] = (
                    "Vocês se enxergam%s, mas a porta da partida está fechada. "
                    % (" e o arquivo do jogo e o mesmo"
                       if resultado["arquivo"] == "igual" else "") +
                    "Duas causas: ele ainda não clicou em 'Eu abro a partida', "
                    "ou o firewall do Windows dele está bloqueando o "
                    "retroarch.exe. Veja o documento 5.")
            else:
                resultado["diagnostico"] = (
                    "Não alcanço o computador dele. Confira o endereço, e se "
                    "ele ligou 'Aceitar conexões da rede' e reabriu o ARENA.")

            return self.responder_json(resultado)

        # ---- abrir so a BIOS do console -----------------------------------
        if caminho == "/api/bios/abrir":
            plataforma_id = str(dados.get("plataforma", "")).strip().lower()
            plataforma = next((p for p in carregar_catalogo()
                               if p["id"] == plataforma_id), None)
            if not plataforma:
                return self.erro("Console desconhecido. Escolha um console da lista "
                                 "(ou confira a pasta do jogo em jogos\\pessoais).")

            with TRAVA_JOGO:
                if JOGO_EM_ANDAMENTO["ativo"]:
                    return self.erro("Feche o jogo aberto antes.", 409)
                JOGO_EM_ANDAMENTO["ativo"] = True
                JOGO_EM_ANDAMENTO["titulo"] = "BIOS do %s" % plataforma["nome"]
                JOGO_EM_ANDAMENTO["id"] = ""

            config = carregar_config()
            caminho_externo, dados_externo = graficos.achar_externo(plataforma)

            if caminho_externo:
                comando = [caminho_externo]
                pasta = os.path.dirname(caminho_externo)
            else:
                core = os.path.join(PASTA_CORES, plataforma["core"])
                if not os.path.isfile(core):
                    with TRAVA_JOGO:
                        JOGO_EM_ANDAMENTO["ativo"] = False
                        JOGO_EM_ANDAMENTO["titulo"] = ""
                    return self.erro("Este console não tem emulador instalado. Veja em Como colocar jogos (barra da esquerda) o que falta para ele.")
                # Sem jogo no comando: o console abre na tela inicial, que
                # e onde ficam o relogio, os ajustes e o memory card.
                extras = {}
                extras.update(graficos.opcoes_de_bios(
                    nome_curto_do_core(plataforma["core"]),
                    config.get("bios", {}).get(plataforma_id)))
                extras.update(graficos.opcoes_de_memory_card(
                    PASTA_SAVES, plataforma_id))
                try:
                    graficos.gravar_opcoes_dos_nucleos(
                        CAPACIDADE["nota"], extras, CAPACIDADE.get("nota_gpu"))
                except OSError:
                    pass
                comando = [EXECUTAVEL_RETROARCH, "-L", core,
                           "--appendconfig", gravar_override(
                               config, controles_ligados=controles.contar_controles())]
                pasta = PASTA_RETROARCH

            def rodar():
                try:
                    subprocess.Popen(comando, cwd=pasta).wait()
                except OSError as falha:
                    print("[ARENA] Nao consegui abrir a BIOS: %s" % falha)
                finally:
                    with TRAVA_JOGO:
                        JOGO_EM_ANDAMENTO["ativo"] = False
                        JOGO_EM_ANDAMENTO["titulo"] = ""
                    fazer_backup()

            threading.Thread(target=rodar, daemon=True).start()
            return self.responder_json({
                "ok": True, "console": plataforma["nome"],
                "emulador": dados_externo["nome"] if caminho_externo else "RetroArch"})

        # ---- criar as pastas dos consoles ---------------------------------
        # Abre a pasta do console no Explorador do Windows ("Como colocar
        # jogos" -> Abrir a pasta). So deste computador (nao esta em
        # ROTAS_REDE_EXTERNA) e so pasta de console da lista.
        if caminho == "/api/pasta/abrir":
            plataforma = next((p for p in carregar_catalogo()
                               if p["id"] == str(dados.get("plataforma", ""))), None)
            if not plataforma:
                return self.erro("Console desconhecido. Escolha um console da lista.")
            alvo = os.path.join(PASTA_JOGOS, "pessoais", plataforma["pasta"])
            try:
                os.makedirs(alvo, exist_ok=True)
                if not hasattr(os, "startfile"):
                    return self.erro("Abrir a pasta só funciona no Windows. Ela fica em %s: abra pelo gerenciador de arquivos." % alvo)
                os.startfile(alvo)
            except OSError as falha:
                return self.erro(traduzir_erro_do_sistema(falha, "abrir a pasta"))
            return self.responder_json({"ok": True, "pasta": os.path.relpath(alvo, RAIZ)})

        # ---- BIOS: conferir agora e abrir a prateleira -------------------
        # Conferir: o mesmo que o ARENA faz ao abrir (servidor\bios.py), na
        # hora -- quem acabou de por a BIOS na pasta ve ela ficar ativa sem
        # fechar o ARENA. So deste computador (nao esta em ROTAS_REDE_EXTERNA).
        if caminho == "/api/bios/conferir":
            feito = organizar_bios(esperar=0)
            if feito is None:
                return self.erro("Não consegui conferir as BIOS agora. Feche os jogos abertos e tente de novo.")
            return self.responder_json({
                "ok": True, "instaladas": feito["instaladas"], "copiadas": feito["copiadas"],
                "avisos": feito["avisos"], "itens": feito["itens"], "resumo": feito["resumo"],
                "sem_bios": bios.consoles_sem_bios()})

        if caminho == "/api/bios/pasta":
            entradas = bios.catalogo.por_id()
            alvo_id = str(dados.get("id", "") or "")
            console = str(dados.get("console", "") or "")
            # 'pasta': o nome de uma pasta de console do catalogo ("Super
            # Nintendo (Sufami Turbo)") -- so nome da lista, nunca caminho.
            pasta_pedida = str(dados.get("pasta", "") or "")
            pastas_do_catalogo = {e["pasta"] for e in bios.catalogo.CATALOGO}
            if alvo_id and alvo_id not in entradas:
                return self.erro("BIOS desconhecida. Escolha uma da lista.")
            if pasta_pedida and pasta_pedida not in pastas_do_catalogo:
                return self.erro("Pasta desconhecida. Escolha uma da lista.")
            do_console = bios.catalogo.do_console(console) if console else []
            if console and not do_console:
                return self.erro("Este console não usa BIOS. Escolha um console da lista.")
            if alvo_id:
                alvo = bios.prateleira(RAIZ, entradas[alvo_id])
            elif pasta_pedida:
                alvo = os.path.join(RAIZ, bios.NOME_DA_PASTA, pasta_pedida)
            elif do_console:
                alvo = os.path.join(RAIZ, bios.NOME_DA_PASTA, do_console[0]["pasta"])
            else:
                alvo = os.path.join(RAIZ, bios.NOME_DA_PASTA)
            try:
                bios.criar_prateleiras(RAIZ)
                os.makedirs(alvo, exist_ok=True)
                if not hasattr(os, "startfile"):
                    return self.erro("Abrir a pasta só funciona no Windows. Ela fica em %s: abra pelo gerenciador de arquivos." % alvo)
                os.startfile(alvo)
            except OSError as falha:
                return self.erro(traduzir_erro_do_sistema(falha, "abrir a pasta"))
            return self.responder_json({"ok": True, "pasta": os.path.relpath(alvo, RAIZ)})

        if caminho == "/api/pastas/criar":
            criadas = []
            base = os.path.join(PASTA_JOGOS, "pessoais")
            for plataforma in carregar_catalogo():
                alvo = os.path.join(base, plataforma["pasta"])
                if not os.path.isdir(alvo):
                    try:
                        os.makedirs(alvo, exist_ok=True)
                        criadas.append(plataforma["pasta"])
                    except OSError:
                        pass
            limpar_caches()
            return self.responder_json({"ok": True, "criadas": len(criadas)})

        # ---- mover um jogo para a pasta do console certo -------------------
        if caminho == "/api/jogo/mover":
            jogo = achar_jogo(str(dados.get("jogo_id", "")))
            if not jogo:
                return self.erro("Jogo não encontrado. Ele pode ter sido movido ou apagado. "
                                 "Clique em Atualizar lista e tente de novo.", 404)

            destino_id = str(dados.get("plataforma", "")).strip().lower()
            plataforma = next((p for p in carregar_catalogo()
                               if p["id"] == destino_id), None)
            if not plataforma:
                return self.erro("Console desconhecido. Escolha um console da lista "
                                 "(ou confira a pasta do jogo em jogos\\pessoais).")

            origem = os.path.join(RAIZ, jogo["arquivo"])
            if not dentro_da_pasta(origem, PASTA_JOGOS) or not os.path.isfile(origem):
                return self.erro("O arquivo do jogo não está mais no lugar (foi movido ou apagado). Clique em Atualizar lista.", 404)

            with TRAVA_JOGO:
                if JOGO_EM_ANDAMENTO["ativo"]:
                    return self.erro(
                        "Feche o jogo aberto antes de mover arquivos.", 409)

            # A pasta de destino fica dentro da mesma origem (pessoais,
            # turma ou livres), para o jogo nao trocar de dono.
            raiz_origem = os.path.join(PASTA_JOGOS, jogo["origem"])
            pasta_destino = os.path.join(raiz_origem, plataforma["pasta"])
            destino = os.path.join(pasta_destino, os.path.basename(origem))

            if os.path.abspath(origem) == os.path.abspath(destino):
                return self.responder_json(
                    {"ok": True, "movido": False,
                     "plataforma_nome": plataforma["nome"]})
            if os.path.exists(destino):
                return self.erro(
                    "Já existe um arquivo com esse nome em %s. Apague ou renomeie o repetido e tente de novo." % plataforma["pasta"])

            try:
                os.makedirs(pasta_destino, exist_ok=True)
                # os.replace nao atravessa disco; move e o caminho seguro.
                shutil.move(origem, destino)
            except OSError as falha:
                return self.erro(traduzir_erro_do_sistema(falha, "mover o jogo"))

            # O jogo mudou de lugar, entao o save antigo perderia o vinculo.
            # Como o nome do arquivo nao muda, os saves continuam valendo.
            indexador.gravar_manual(jogo["id"], "")   # a pasta manda agora
            limpar_caches()
            manifesto(forcar=True)

            print("[ARENA] %s movido para %s" % (jogo["titulo"], plataforma["pasta"]))
            return self.responder_json({
                "ok": True, "movido": True,
                "plataforma_nome": plataforma["nome"],
                "pasta": plataforma["pasta"],
            })

        # ---- arrumar o arquivo de um jogo (botao Arrumar do cartao) --------
        # Conserto de posicao com um jeito certo so (servidor\arrumar.py): o
        # kinst.zip dentro da pasta do disco, o disco solto ao lado do zip, a
        # BIOS do Neo Geo na pasta do jogo... So no clique da pessoa (o ARENA
        # nunca move arquivo de jogo sozinho); confere de novo antes de fazer.
        # So deste computador (nao esta em ROTAS_REDE_EXTERNA).
        if caminho == "/api/jogo/arrumar":
            jogo = achar_jogo(str(dados.get("jogo_id", "")))
            if not jogo:
                return self.erro("Jogo não encontrado. Ele pode ter sido movido ou apagado. "
                                 "Clique em Atualizar lista e tente de novo.", 404)
            origem = os.path.join(RAIZ, jogo["arquivo"])
            if not dentro_da_pasta(origem, PASTA_JOGOS) or not os.path.exists(origem):
                return self.erro("O arquivo do jogo não está mais no lugar. Clique em Atualizar lista.", 404)
            with TRAVA_JOGO:
                if JOGO_EM_ANDAMENTO["ativo"]:
                    return self.erro("Feche o jogo aberto antes de arrumar os arquivos.", 409)
            acao = str(dados.get("acao", ""))
            if acao in arrumar.DEMORADAS:
                # Descompactar demora (um CD tem 700 MB): em segundo plano; a
                # tela acompanha por /api/arrumar/progresso.
                disco_zipado = None
                if acao == "extrair_disco":
                    pasta_do_jogo = os.path.dirname(origem)
                    try:
                        zipados = indexador.discos_de_fliperama_zipados(pasta_do_jogo, os.listdir(pasta_do_jogo))
                    except OSError:
                        zipados = {}
                    romset = os.path.splitext(os.path.basename(origem))[0].lower()
                    if romset in zipados:
                        disco_zipado = os.path.join(pasta_do_jogo, zipados[romset])

                def refazer_a_lista():
                    limpar_caches()
                    manifesto(forcar=True)
                try:
                    tarefa, mensagem = arrumar.iniciar(acao, origem, PASTA_JOGOS, refazer_a_lista, disco_zipado)
                except arrumar.NaoDa as falha:
                    return self.erro(str(falha))
                except OSError as falha:
                    return self.erro(traduzir_erro_do_sistema(falha, "descompactar o jogo"))
                return self.responder_json({"ok": True, "mensagem": mensagem, "tarefa": tarefa})
            try:
                mensagem, _novo = arrumar.aplicar(acao, origem, PASTA_JOGOS, RAIZ, indexador.neogeo_do_arena())
            except arrumar.NaoDa as falha:
                return self.erro(str(falha))
            except OSError as falha:
                return self.erro(traduzir_erro_do_sistema(falha, "arrumar o arquivo"))
            limpar_caches()
            manifesto(forcar=True)
            print("[ARENA] Arrumado: %s" % mensagem)
            return self.responder_json({"ok": True, "mensagem": mensagem})

        # ---- corrigir o console de um jogo ---------------------------------
        if caminho == "/api/jogo/console":
            jogo_id = str(dados.get("jogo_id", ""))
            if not achar_jogo(jogo_id):
                return self.erro("Jogo não encontrado. Ele pode ter sido movido ou apagado. "
                                 "Clique em Atualizar lista e tente de novo.", 404)

            plataforma = str(dados.get("plataforma", "")).strip().lower()
            validas = {p["id"] for p in carregar_catalogo()}
            if plataforma and plataforma not in validas:
                return self.erro("Console desconhecido. Escolha um console da lista "
                                 "(ou confira a pasta do jogo em jogos\\pessoais).")

            indexador.gravar_manual(jogo_id, plataforma)
            limpar_caches()
            manifesto(forcar=True)
            novo = achar_jogo(jogo_id)
            return self.responder_json({
                "ok": True,
                "plataforma": novo["plataforma"] if novo else plataforma,
                "plataforma_nome": novo["plataforma_nome"] if novo else "",
            })

        # ---- save states -------------------------------------------------
        if caminho == "/api/estado/apagar":
            jogo = achar_jogo(dados.get("jogo_id"))
            if not jogo:
                return self.erro("Jogo não encontrado. Ele pode ter sido movido ou apagado. "
                                 "Clique em Atualizar lista e tente de novo.", 404)
            try:
                apagou = cheats.apagar_estado(jogo, dados.get("espaco"), nucleo_das_pastas(jogo))
            except (TypeError, ValueError):
                return self.erro("Esse número de espaço não existe. Escolha um dos que "
                                 "aparecem na lista de saves do jogo.")
            return self.responder_json({
                "ok": True, "apagou": apagou,
                "estados": cheats.listar_estados(jogo, nucleo_das_pastas(jogo))})

        # ---- cheats ------------------------------------------------------
        if caminho == "/api/cheat/adicionar":
            jogo = achar_jogo(dados.get("jogo_id"))
            if not jogo:
                return self.erro("Jogo não encontrado. Ele pode ter sido movido ou apagado. "
                                 "Clique em Atualizar lista e tente de novo.", 404)
            if jogo_aberto_agora(jogo):
                return self.erro(MENSAGEM_CHEAT_COM_JOGO_ABERTO, 409)
            lista, erro = cheats.adicionar_cheat(
                jogo, str(dados.get("descricao", ""))[:120],
                str(dados.get("codigo", "")), bool(dados.get("ligado")), nucleo_das_pastas(jogo))
            if erro:
                return self.erro(erro)
            return self.responder_json({"ok": True, "cheats": lista})

        if caminho == "/api/cheat/alterar":
            jogo = achar_jogo(dados.get("jogo_id"))
            if not jogo:
                return self.erro("Jogo não encontrado. Ele pode ter sido movido ou apagado. "
                                 "Clique em Atualizar lista e tente de novo.", 404)
            try:
                indice = int(dados.get("indice"))
            except (TypeError, ValueError):
                return self.erro("Esse código não está mais na lista de cheats. "
                                 "Reabra o painel do jogo e tente de novo.")
            if jogo_aberto_agora(jogo):
                return self.erro(MENSAGEM_CHEAT_COM_JOGO_ABERTO, 409)
            lista, erro = cheats.alterar_cheat(
                jogo, indice, dados.get("ligado"), bool(dados.get("apagar")), nucleo_das_pastas(jogo))
            if erro:
                return self.erro(erro, 404)
            return self.responder_json({"ok": True, "cheats": lista})

        # ---- copia de seguranca -------------------------------------------
        if caminho == "/api/exportar":
            try:
                return self.responder_json(dict(ok=True, **exportar_saves()))
            except OSError as falha:
                return self.erro(traduzir_erro_do_sistema(falha, "montar o pacote"))

        if caminho == "/api/importar":
            resultado, erro = importar_saves(dados.get("arquivo"))
            if erro:
                return self.erro(erro, 404)
            return self.responder_json(dict(ok=True, **resultado))

        if caminho == "/api/backup":
            anterior = ultima_copia()
            destino = fazer_backup()
            if not destino:
                return self.erro("Não consegui gravar a cópia de segurança: o pen drive pode estar cheio ou só de leitura. Libere espaço e tente de novo.")
            return self.responder_json(
                {"ok": True, "pasta": os.path.basename(destino),
                 # Nada mudou desde a ultima: ela continua valendo (L3).
                 "nada_mudou": bool(anterior) and os.path.normcase(destino) == os.path.normcase(anterior)})

        # ---- capa do jogo, buscada sob pedido -------------------------------
        if caminho == "/api/capa/atualizar":
            jogo = achar_jogo(str(dados.get("jogo_id", "")))
            if not jogo:
                return self.erro("Jogo não está no catálogo. Clique em Atualizar lista.", 404)
            if not VIGIA["internet"]:
                if jogo.get("plataforma") not in ("ps3", "psp"):
                    return self.erro("Sem internet agora. Ligue o computador na internet e clique em Buscar capa de novo.", 503)

            # Fliperama: o nome completo do banco ("Metal Slug X - Super
            # Vehicle-001 (NGM-2500)(NGH-2500)") e' o que o banco de capas usa.
            nome_base = (jogo.get("nome_banco")
                         or os.path.splitext(os.path.basename(jogo["arquivo"]))[0])
            ok, motivo = capas_online.buscar_e_baixar(
                jogo["plataforma"], jogo["titulo"], nome_base,
                caminho_jogo=os.path.join(RAIZ, jogo["arquivo"]),
                com_internet=bool(VIGIA["internet"]))
            if not ok:
                return self.erro(motivo or "Não consegui achar a capa.", 404)

            limpar_caches()
            manifesto(forcar=True)
            return self.responder_json({"ok": True, "fonte": motivo or ""})

        if caminho == "/api/capas/buscar-faltando":
            with TRAVA_CAPAS:
                ja_rodando = BUSCA_DE_CAPAS["rodando"]
                if not ja_rodando:
                    BUSCA_DE_CAPAS.update(rodando=True, parar=False, total=0, feitos=0, achados=0, atual="")
            if not ja_rodando:
                threading.Thread(target=buscar_capas_que_faltam, daemon=True).start()
            return self.responder_json(dict(ok=True, **situacao_das_capas()))

        if caminho == "/api/capas/parar":
            with TRAVA_CAPAS:
                if BUSCA_DE_CAPAS["rodando"]:
                    BUSCA_DE_CAPAS["parar"] = True
            return self.responder_json(dict(ok=True, **situacao_das_capas()))

        if caminho == "/api/capa/enviar":
            jogo = achar_jogo(str(dados.get("jogo_id", "")))
            if not jogo:
                return self.erro("Jogo não está no catálogo. Clique em Atualizar lista.", 404)

            imagem = str(dados.get("imagem", ""))
            if not imagem:
                return self.erro("Nenhuma imagem chegou. Escolha a imagem e tente de novo.")
            if "," in imagem:
                imagem = imagem.split(",", 1)[1]
            try:
                brutos = base64.b64decode(imagem, validate=True)
            except (binascii.Error, ValueError):
                return self.erro("Essa imagem não abriu. Use um arquivo .png, .jpg ou .webp.")
            if not brutos or len(brutos) > 6 * 1024 * 1024:
                return self.erro("Imagem grande demais: o limite é 6 MB. Escolha uma imagem menor.")
            tipo = _tipo_da_imagem(brutos)
            if not tipo:
                return self.erro("Formato de imagem não aceito (use PNG, JPG ou WEBP).")

            caminho_rom = os.path.join(RAIZ, jogo["arquivo"])
            if not dentro_da_pasta(caminho_rom, PASTA_JOGOS) or not os.path.isfile(caminho_rom):
                return self.erro("O arquivo do jogo não está mais no lugar (foi movido ou apagado). Clique em Atualizar lista.", 404)

            extensoes = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}
            pasta_jogo = os.path.dirname(caminho_rom)
            nome_base = os.path.splitext(os.path.basename(caminho_rom))[0]
            destino = os.path.join(pasta_jogo, "capas", nome_base + extensoes[tipo])
            if not dentro_da_pasta(destino, PASTA_JOGOS):
                return self.erro("Não consegui achar onde guardar essa capa. Clique em "
                                 "Atualizar lista e tente de novo.")

            try:
                os.makedirs(os.path.dirname(destino), exist_ok=True)
                temporario = "%s.%d.tmp" % (destino, threading.get_ident())
                with TRAVA_ARQUIVO:
                    with open(temporario, "wb") as arquivo:
                        arquivo.write(brutos)
                        arquivo.flush()
                        os.fsync(arquivo.fileno())
                    os.replace(temporario, destino)
            except OSError as falha:
                return self.erro(traduzir_erro_do_sistema(falha, "gravar a capa"), 500)

            limpar_caches()
            manifesto(forcar=True)
            return self.responder_json({"ok": True})

        # ---- perfil (apelido + foto, permanente) ---------------------------
        if caminho == "/api/capa/miniatura":
            alvo = capa_permitida(dados.get("arquivo"))
            if not alvo:
                return self.erro("Capa não encontrada.", 404)
            if dados.get("largura") not in LARGURAS_MINIATURA:
                return self.erro("Largura de miniatura inválida.")
            try:
                gravar_miniatura(alvo, dados["largura"], dados.get("imagem"))
            except ValueError as falha:
                return self.erro(str(falha))
            except OSError as falha:
                return self.erro(traduzir_erro_do_sistema(falha, "guardar a miniatura da capa"))
            return self.responder_json({"ok": True})

        if caminho == "/api/perfil/foto":
            if dados.get("remover"):
                apagar_foto_perfil()
                return self.responder_json({"ok": True, "tem_foto": False})

            imagem = str(dados.get("imagem", ""))
            if not imagem:
                return self.erro("Nenhuma imagem chegou. Escolha a imagem e tente de novo.")
            try:
                gravar_foto_perfil(imagem)
            except ValueError as falha:
                return self.erro(str(falha))
            return self.responder_json({"ok": True, "tem_foto": True})

        # ---- amigos e servidores -------------------------------------------
        if caminho == "/api/amigo/adicionar":
            config = carregar_config()
            apelido = str(dados.get("apelido", "")).strip()[:24]
            url = str(dados.get("url", "")).strip()[:200]
            if not apelido:
                return self.erro("Escreva o apelido do amigo.")
            if not url:
                return self.erro("Escreva o endereço do ARENA dele.")
            if not normalizar_url(url):
                # Antes gravava qualquer coisa, e o amigo ficava "fora do
                # ar" para sempre, sem dizer por que.
                return self.erro(ENDERECO_ESTRANHO)
            if len(config["servidores"]) >= 20:
                return self.erro("Você já tem 20 amigos, o máximo. Remova um (Perfil → Amigos) para adicionar outro.")
            if any(a["apelido"].lower() == apelido.lower()
                   for a in config["servidores"]):
                return self.erro("Já existe um amigo com esse apelido. Escolha outro apelido para ele.")

            config["servidores"].append({
                "apelido": apelido, "url": url,
                "escola": bool(dados.get("escola")),
                # Guarda o id do aparelho, quando vem (adicionado pela
                # descoberta automatica) - e' o que deixa o ARENA achar o
                # amigo de novo sozinho quando o IP dele mudar. Sem id
                # (amigo digitado na mao por endereco), fica so o
                # endereco fixo mesmo, do jeito antigo.
                "id": str(dados.get("id", ""))[:64],
            })
            salvar_config(config)
            return self.responder_json({"ok": True,
                                        "servidores": config["servidores"]})

        if caminho == "/api/amigo/remover":
            config = carregar_config()
            apelido = str(dados.get("apelido", "")).strip().lower()
            config["servidores"] = [a for a in config["servidores"]
                                    if a["apelido"].lower() != apelido]
            salvar_config(config)
            return self.responder_json({"ok": True,
                                        "servidores": config["servidores"]})

        if caminho == "/api/amigo/testar":
            bruto = str(dados.get("url", "")).strip()
            url = normalizar_url(bruto)
            if not url:
                return self.erro(ENDERECO_ESTRANHO if bruto else "Endereço vazio.")
            try:
                retorno = falar_com(url, "/api/sinc/ola", {}, "POST", 4)
            except Exception:
                return self.erro("Não respondeu. Confira o endereço e se o "
                                 "ARENA dele está aberto com a rede liberada.")
            return self.responder_json({"ok": True,
                                        "apelido": retorno.get("apelido", ""),
                                        "id": retorno.get("servidor_id", "")})

        if caminho == "/api/sinc/ola":
            config = carregar_config()
            return self.responder_json({
                "ok": True,
                "apelido": config.get("apelido", ""),
                "servidor_id": config["dispositivo_id"],
                "arena": True,
                # O PARTIDA.bat compara a versao dos dois lados por aqui.
                # Antes lia /api/estado do colega, que desde a Fase 3 so
                # responde a este computador (tem a configuracao inteira).
                "versao": VERSAO,
                # Partida hospedada aqui agora (ou null): o amigo acha a
                # partida por aqui mesmo quando o grito UDP nao chega.
                "partida": partida_aberta_agora(),
            })

        # ---- bibliotecas graficas sem instalar ------------------------------
        if caminho == "/api/barreiras/fechar":
            # So programas da lista curta e segura (barreiras.FECHAVEIS), e
            # so quando o aluno clica. Nunca navegador, Word, etc.
            ok, mensagem = barreiras.fechar_programa(dados.get("programa"))
            if not ok:
                return self.erro(mensagem)
            with TRAVA_CACHE:
                _cache_barreiras["quando"] = 0.0   # a proxima consulta ja ve fechado
            return self.responder_json({"ok": True, "mensagem": mensagem})

        if caminho == "/api/reparar-runtime":
            copiadas, erro = reparar_runtime()
            if erro:
                return self.erro(erro)
            return self.responder_json({"ok": True, "copiadas": copiadas})

        if caminho == "/api/indexar":
            limpar_caches()
            total = manifesto(forcar=True)["total"]
            # Com acervo grande, cada releitura deixa listas antigas para
            # tras. Uma coleta explicita aqui devolve essa memoria em vez
            # de deixar o ARENA inchar ao longo da aula.
            import gc
            gc.collect()
            return self.responder_json({"ok": True, "total": total})

        if caminho == "/api/config":
            config = carregar_config()

            if dados.get("perfil_grafico") in list(PERFIS_GRAFICOS) + ["automatico"]:
                config["perfil_grafico"] = dados["perfil_grafico"]

            if isinstance(dados.get("avancado"), dict):
                validas = recursos_por_chave()
                for chave, valor in dados["avancado"].items():
                    opcao = validas.get(chave)
                    if not opcao:
                        continue        # chave desconhecida: ignora
                    valor = str(valor)
                    if opcao["tipo"] == "bool" and valor not in ("true", "false"):
                        continue
                    if opcao["tipo"] == "lista" and valor not in opcao.get("opcoes", []):
                        continue
                    config["avancado"][chave] = valor

            if isinstance(dados.get("bios"), dict):
                validas = {p["id"] for p in carregar_catalogo()}
                disponiveis = {b["arquivo"] for b in
                               graficos.bios_disponiveis(PASTA_SISTEMA)}
                for plataforma, arquivo in dados["bios"].items():
                    if plataforma not in validas:
                        continue
                    if arquivo and arquivo not in disponiveis:
                        continue
                    if arquivo:
                        config["bios"][plataforma] = arquivo
                    else:
                        config["bios"].pop(plataforma, None)

            if "modo_desempenho" in dados:
                config["modo_desempenho"] = bool(dados["modo_desempenho"])
            if dados.get("preset_grafico_externo") in ("automatico", "leve", "bonito"):
                config["preset_grafico_externo"] = dados["preset_grafico_externo"]
            if dados.get("motor_ps2") in tuple(graficos.MOTORES_PCSX2):
                config["motor_ps2"] = dados["motor_ps2"]
            if dados.get("fundo_animado") in FUNDOS_ANIMADOS:
                config["fundo_animado"] = dados["fundo_animado"]
            if dados.get("tema") in ("claro", "escuro"):
                config["tema"] = dados["tema"]

            # Favoritar e desfavoritar num pedido so: a tela manda o id e o
            # servidor inverte. Evita a tela e o servidor discordarem sobre
            # quem tem a lista certa.
            if dados.get("favorito"):
                alvo = str(dados["favorito"])[:300]
                if alvo in config["favoritos"]:
                    config["favoritos"].remove(alvo)
                elif achar_jogo(alvo):
                    config["favoritos"] = ([alvo] + config["favoritos"])[:200]

            if "abaixo_do_original" in dados:
                valor = dados["abaixo_do_original"]
                config["abaixo_do_original"] = (
                    valor if isinstance(valor, str) and valor in graficos.NIVEIS_ABAIXO else "")
            if "modo_modesto" in dados or "abaixo_do_original" in dados:
                if "modo_modesto" in dados:
                    config["modo_modesto"] = bool(dados["modo_modesto"])
                # Regravar os ajustes dos nucleos AGORA. Eles ficam num
                # arquivo separado do override, e sem isto a mudanca so
                # valeria no jogo seguinte ao seguinte.
                try:
                    graficos.gravar_opcoes_dos_nucleos(
                        CAPACIDADE["nota"], None, CAPACIDADE.get("nota_gpu"),
                        modesto=grafico_original(config), abaixo=nivel_abaixo(config))
                except OSError:
                    pass
            if "travar_teclas" in dados:
                config["travar_teclas"] = bool(dados["travar_teclas"])
            if "ultra_desempenho" in dados:
                config["ultra_desempenho"] = bool(dados["ultra_desempenho"])
                # Ultra sem prioridade nao faz sentido: ligam juntos.
                if config["ultra_desempenho"]:
                    config["modo_desempenho"] = True

            if "apelido" in dados:
                config["apelido"] = limpar_apelido(dados["apelido"])

            rede_mudou = False
            if "permitir_rede" in dados:
                novo = bool(dados["permitir_rede"])
                rede_mudou = novo != config["permitir_rede"]
                config["permitir_rede"] = novo

            if "rpcn_ativo" in dados:
                config["rpcn_ativo"] = bool(dados["rpcn_ativo"])

            if dados.get("restaurar"):
                config["avancado"] = dict(AVANCADO_PADRAO)
                config["perfil_grafico"] = "automatico"

            salvar_config(config)
            gravar_override(config)
            # A chave da rede vale NA HORA (antes precisava fechar e abrir o
            # ARENA): o servidor reabre sozinho, logo depois desta resposta.
            rede_aplicada = trocar_escuta_de_rede() if rede_mudou else False
            return self.responder_json({
                "ok": True, "config": config,
                "efetivas": opcoes_efetivas(config),
                "rede_aplicada": rede_aplicada,
            })

        if caminho == "/api/jogar":
            jogo = achar_jogo(dados.get("jogo_id"))
            if not jogo:
                return self.erro("Jogo não está no catálogo. Clique em Atualizar lista.", 404)

            plataforma = next((p for p in carregar_catalogo()
                               if p["id"] == jogo["plataforma"]), None)
            if not plataforma:
                return self.erro("Não sei de que console é este jogo. Clique em Atualizar lista; se continuar, ponha o jogo na pasta do console certo.")
            # Jogo de CD dentro de .zip: o emulador nao abre assim (o RetroArch
            # tira um arquivo so do zip, e o .cue precisa dos .bin ao lado).
            # O problema e' o arquivo: diz isso antes de olhar o emulador.
            if any(a.get("descompactar") for a in jogo.get("avisos") or []):
                return self.erro("Este jogo de CD está dentro de um .zip, e o emulador não abre assim. "
                                 "Clique no botão Arrumar, no painel do jogo: o ARENA descompacta.")

            # Emulador de fora tem prioridade. Se ele existe, o RetroArch
            # nem precisa estar instalado para esta plataforma.
            caminho_externo, dados_externo = graficos.achar_externo(plataforma)

            if not caminho_externo:
                if not os.path.isfile(EXECUTAVEL_RETROARCH):
                    return self.erro(
                        "Não achei o retroarch.exe na pasta retroarch. A pasta tem que se chamar retroarch (guia 1); rode o VERIFICAR.bat para conferir.")
                if not os.path.isfile(os.path.join(PASTA_CORES, plataforma["core"])):
                    sugestao = ""
                    if dados_externo:
                        sugestao = (" Ou instale o %s na pasta emuladores."
                                    % dados_externo["nome"])
                    return self.erro(
                        "Falta o núcleo deste console na pasta retroarch\\cores. Rode o VERIFICAR.bat (guia 6)." + sugestao)

            caminho_rom = os.path.join(RAIZ, jogo["arquivo"])
            if not dentro_da_pasta(caminho_rom, PASTA_JOGOS) or not os.path.isfile(caminho_rom):
                return self.erro("O arquivo do jogo não está mais no lugar (foi movido ou apagado). Clique em Atualizar lista.", 404)

            if caminho_externo:
                falta = graficos.falta_para_o_externo(dados_externo["nome"], caminho_externo)
                if falta:
                    return self.erro(falta, 409)

            # Fliperama com zip danificado: abre (as vezes da para jogar),
            # mas avisa o motivo dos graficos errados. Conferido uma vez so.
            aviso_arquivo = ""
            if jogo.get("romset"):
                ruim = integridade.parte_danificada(caminho_rom)
                if ruim:
                    frase = integridade.texto_do_aviso(ruim)
                    aviso_arquivo = "Atenção: " + frase[:1].lower() + frase[1:]

            jogo = dict(jogo)
            jogo["core"] = plataforma["core"]
            if caminho_externo:
                jogo["externo"] = {"caminho": caminho_externo,
                                   "dados": dados_externo}

            config = carregar_config()
            apelido = limpar_apelido(dados.get("apelido") or config["apelido"]) or "convidado"

            # Conferir e marcar DENTRO DA MESMA TRAVA. Em travas separadas
            # abre-se uma janela em que varios pedidos passam juntos, e o
            # aluno acaba com varios emuladores abertos disputando o mesmo
            # controle. Foi o que o teste de rajada mostrou.
            with TRAVA_JOGO:
                if JOGO_EM_ANDAMENTO["ativo"]:
                    return self.erro(
                        "Já existe um jogo aberto (%s). Feche com F10 antes "
                        "de abrir outro." % JOGO_EM_ANDAMENTO["titulo"], 409)
                JOGO_EM_ANDAMENTO["ativo"] = True
                JOGO_EM_ANDAMENTO["titulo"] = jogo["titulo"]
                # O id: a gaveta "Saves e cheats" nao deixa mudar os codigos
                # do jogo que esta aberto (o RetroArch grava a lista dele
                # por cima ao fechar).
                JOGO_EM_ANDAMENTO["id"] = jogo["id"]

            # Partida a dois, se pedida.
            partida = None
            modo = dados.get("partida")
            if modo and caminho_externo:
                with TRAVA_JOGO:
                    JOGO_EM_ANDAMENTO["ativo"] = False
                    JOGO_EM_ANDAMENTO["titulo"] = ""
                return self.erro(
                    "Jogar junto só funciona pelo RetroArch. Esta plataforma "
                    "está usando o %s, que tem rede própria: use o menu de rede do próprio jogo (guia 5)."
                    % dados_externo["nome"], 409)
            if modo and not plataforma.get("netplay", True):
                with TRAVA_JOGO:
                    JOGO_EM_ANDAMENTO["ativo"] = False
                    JOGO_EM_ANDAMENTO["titulo"] = ""
                return self.erro(plataforma.get("netplay_motivo") or
                                 "Este console não tem jogo em rede disponível.", 409)

            # Alguns consoles (PS1: SwanStation) tem um nucleo mais fiel para
            # jogar sozinho, mas sem suporte a jogo em rede - nesse caso o
            # cadastro aponta um segundo nucleo so para quando for Jogar
            # Junto. Jogando sozinho, o normal continua valendo.
            # Sem a BIOS que o nucleo de sempre precisa, o console que tem um
            # nucleo que imita a BIOS abre por ele (consoles.json ->
            # core_sem_bios): o PS1 pelo PCSX ReARMed -- o CTR abriu assim, sem
            # BIOS nenhuma (14/10/2026). O pacote do ARENA nunca leva BIOS da
            # Sony, e o SwanStation nao abre jogo nenhum sem ela.
            aviso_sem_bios = ""
            if (plataforma.get("core_sem_bios") and not caminho_externo
                    and os.path.isfile(os.path.join(PASTA_CORES, plataforma["core_sem_bios"]))
                    and not bios.tem_a_bios(plataforma["id"], PASTA_SISTEMA)):
                jogo["core"] = plataforma["core_sem_bios"]
                aviso_sem_bios = plataforma.get("sem_bios_aviso", "")

            aviso_netplay = ""
            if modo in ("hospedar", "entrar", "assistir") and plataforma.get("core_netplay"):
                core_netplay = os.path.join(PASTA_CORES, plataforma["core_netplay"])
                if not os.path.isfile(core_netplay):
                    with TRAVA_JOGO:
                        JOGO_EM_ANDAMENTO["ativo"] = False
                        JOGO_EM_ANDAMENTO["titulo"] = ""
                    return self.erro(
                        "Falta o núcleo %s para jogar em rede neste console. Sozinho dá para jogar; rode o VERIFICAR.bat para conferir os núcleos."
                        % plataforma["core_netplay"], 409)
                jogo["core"] = plataforma["core_netplay"]
                aviso_netplay = plataforma.get("netplay_aviso", "")

            # Quantos jogadores ESTE jogo aceita, e o que o nucleo que vai
            # abrir (ja trocado acima, se for Jogar Junto) precisa para isso:
            # adaptador, controles lidos, conexoes (servidor\multitap.json).
            # Vale jogando no mesmo computador tambem, nao so no Jogar Junto.
            if not caminho_externo:
                jogo["ligacao"] = graficos.jogadores_do_jogo(
                    jogo["core"], jogadores_pedidos(plataforma, jogo),
                    config.get("avancado", {}).get("input_max_users", 2),
                    arquivo=os.path.join(RAIZ, jogo["arquivo"]))

            # "assistir" entra na partida do amigo sem controlar nada. Antes
            # ficava fora deste bloco e o jogo abria sozinho, sem conectar.
            if modo in ("hospedar", "entrar", "assistir"):
                hospedar = (modo == "hospedar")
                assistir = (modo == "assistir")
                endereco = ""
                if not hospedar:
                    bruto = str(dados.get("endereco", "") or "").strip()
                    endereco = normalizar_url(bruto)
                    endereco = urllib.parse.urlsplit(endereco).hostname or ""
                    if not endereco:
                        # Ja marcamos a trava acima: soltar antes de sair,
                        # senao o ARENA fica achando que tem jogo aberto.
                        with TRAVA_JOGO:
                            JOGO_EM_ANDAMENTO["ativo"] = False
                            JOGO_EM_ANDAMENTO["titulo"] = ""
                        return self.erro(ENDERECO_ESTRANHO if bruto else
                                         "Informe o endereço de quem está "
                                         "hospedando a partida.")
                pela_internet = bool(dados.get("pela_internet"))
                # Quantos cabem vem da ligacao acima: o que o jogo aceita,
                # limitado ao que o nucleo permite.
                jogadores_max = jogo["ligacao"]["jogadores"]
                try:
                    posicao = int(dados.get("jogador") or 2)
                except (TypeError, ValueError):
                    posicao = 2
                posicao = max(2, min(posicao, jogadores_max))
                partida = {
                    "opcoes": graficos.opcoes_de_partida(
                        apelido, hospedar, assistir=assistir,
                        pela_internet=pela_internet,
                        repasse=str(dados.get("repasse", "saopaulo")),
                        jogador=posicao),
                    "argumentos": graficos.argumentos_de_partida(hospedar, endereco),
                    "hospedar": hospedar,
                    "assistir": assistir,
                    "papel": ("jogador 1" if hospedar else
                              "espectador" if assistir else
                              "jogador %d" % posicao),
                }
                # Com 3+ jogadores, o padrao do RetroArch (3 conexoes)
                # recusaria o ultimo colega. Com 1 ou 2, continua 3.
                partida["opcoes"]["netplay_max_connections"] = str(
                    jogo["ligacao"]["max_conexoes"])
                if not hospedar and not assistir:
                    # Para avisar o ARENA de quem abriu ("cheguei") antes de
                    # conectar: se ele esperava, os dois comecam juntos.
                    partida["anfitriao"] = normalizar_url(str(dados.get("endereco", "") or ""))
                if plataforma.get("core_netplay"):
                    # O nucleo alternativo so de netplay (ex.: PCSX ReARMed
                    # no PS1) tem estado maior pra serializar que o nucleo
                    # normal. A checagem periodica de dessincronia (a cada
                    # 600 quadros, ~10s) e' a comunidade que reporta como
                    # pesada o bastante pra travar um instante em hardware
                    # fraco - testado aqui que desligar (=0) nao quebra a
                    # conexao, mas o ganho de fluidez so foi confirmado
                    # pela comunidade: esta maquina de desenvolvimento e'
                    # forte demais pra revelar o custo que so pesa no
                    # Positivo fraco da escola.
                    partida["opcoes"]["netplay_check_frames"] = "0"

            # Quem abre a partida pode esperar o amigo para comecarem juntos
            # (a tela pede "esperar"; ver PARTIDA_PENDENTE). Sem o pedido, o
            # jogo abre na hora, como sempre.
            esperar = bool(modo == "hospedar" and partida and dados.get("esperar"))
            if modo == "hospedar" and partida:
                with TRAVA_JOGO:
                    PARTIDA_ABERTA["partida"] = {
                        "jogo": jogo["titulo"],
                        "jogo_id": jogo["id"],
                        "console": plataforma.get("nome", ""),
                        "jogadores": jogo["ligacao"]["jogadores"],
                        "pela_internet": bool(dados.get("pela_internet")),
                        "esperando": esperar,
                    }

            argumentos = (jogo, apelido, config, plataforma.get("custo"), partida)
            if esperar:
                esperar_o_amigo(argumentos)
            else:
                threading.Thread(target=executar_jogo, args=argumentos, daemon=True).start()

            # Lista dos ultimos abertos, sem repetir.
            recentes = [x for x in config.get("recentes", []) if x != jogo["id"]]
            config["recentes"] = ([jogo["id"]] + recentes)[:12]
            salvar_config(config)

            resposta = {"ok": True, "titulo": jogo["titulo"],
                        "pela_internet": bool(partida and
                                              dados.get("pela_internet")),
                        "emulador": (dados_externo["nome"] if caminho_externo
                                     else "RetroArch")}
            if partida:
                resposta["papel"] = partida["papel"]
                resposta["porta"] = graficos.PORTA_PARTIDA
            if esperar:
                resposta["esperando"] = True
            if aviso_netplay or aviso_sem_bios:
                resposta["aviso"] = " ".join(a for a in (aviso_sem_bios, aviso_netplay) if a)
            if partida and partida.get("hospedar"):
                # Vai separado do "aviso": a tela o deixa fixo no alto ate o
                # jogo fechar -- um recado sumiria atras da janela do jogo antes
                # de alguem tentar entrar (revisao da Fase 4).
                aviso_rede = aviso_da_rede_para_quem_hospeda()
                if aviso_rede:
                    resposta["aviso_rede"] = aviso_rede
                preparar_categoria_da_rede()
            # Na hora de jogar, o que pode travar o jogo AGORA: memoria quase
            # cheia, notebook na bateria, economia de bateria (~10 ms, sem
            # PowerShell). A tela avisa junto com "Abrindo...".
            alertas = barreiras.checagem_rapida()
            if alertas:
                resposta["alerta_maquina"] = [
                    {"titulo": b["titulo"], "acao": b["acao"]} for b in alertas]
            elif (caminho_externo and dados_externo["nome"] == "PCSX2" and
                  graficos.jogo_tem_system_link_ps2(plataforma, jogo["titulo"])):
                if graficos.npcap_instalado():
                    resposta["aviso"] = (
                        "Este jogo tem rede de verdade (system link) - o ARENA "
                        "já configurou. Abra o menu de rede DENTRO do jogo pra "
                        "hospedar ou entrar numa partida.")
                else:
                    resposta["aviso"] = (
                        "Este jogo tem rede de verdade (system link), mas só "
                        "pra ENTRAR numa partida de outra máquina - falta o "
                        "driver de rede pra também hospedar. Ver Ajustes -> "
                        "Emuladores.")
            elif (caminho_externo and dados_externo["nome"] == "Xenia" and
                  graficos.jogo_tem_netplay_xbox360(plataforma, jogo["titulo"])):
                resposta["aviso"] = (
                    "Este jogo tem rede local de verdade (Systemlink) - o "
                    "ARENA já configurou, sem precisar de driver nenhum. Abra "
                    "o menu de rede DENTRO do jogo pra hospedar ou entrar "
                    "numa partida.")
            # Aviso fixo do console (ex.: fliperama precisa de ficha antes do
            # Start), vindo do consoles.json -> aviso_ao_abrir.
            if plataforma.get("aviso_ao_abrir"):
                resposta["aviso"] = (resposta.get("aviso", "") + " " +
                                     plataforma["aviso_ao_abrir"]).strip()
            if aviso_arquivo:
                resposta["aviso"] = (aviso_arquivo + " " + resposta.get("aviso", "")).strip()
            return self.responder_json(resposta)

        if caminho == "/api/placar":
            try:
                pontos = int(dados.get("pontos"))
            except (TypeError, ValueError):
                return self.erro("Escreva a pontuação só com números, sem pontos nem letras.")
            if not 0 <= pontos <= 99999999:
                return self.erro("Essa pontuação não vale: escreva um número de 0 a 99.999.999.")

            jogo = achar_jogo(dados.get("jogo_id"))
            if not jogo:
                return self.erro("Jogo não encontrado. Ele pode ter sido movido ou apagado. "
                                 "Clique em Atualizar lista e tente de novo.", 404)

            config = carregar_config()
            apelido = limpar_apelido(dados.get("apelido") or config["apelido"]) or "convidado"

            with TRAVA_BANCO, banco() as conexao:
                inserir_placar(conexao, uuid.uuid4().hex, apelido, jogo["id"],
                               jogo["titulo"], pontos, agora_utc(),
                               config["dispositivo_id"])
            return self.responder_json({"ok": True, "pendentes": contar_pendentes()})

        return self.erro("Rota não encontrada.", 404)


class Servidor(ThreadingHTTPServer):
    daemon_threads = True

    # Fila de conexoes esperando para serem aceitas. O padrao do Python e
    # 5, o que basta para um computador so. Com uma sala inteira abrindo o
    # ARENA ao mesmo tempo, a fila enche e o navegador do aluno recebe
    # "conexao encerrada" sem explicacao. 128 cobre a turma com folga e
    # nao custa memoria praticamente nenhuma.
    request_queue_size = 48 if ECONOMICO else 128

    # No Windows, SO_REUSEADDR deixa DOIS programas escutarem a mesma porta:
    # o segundo ARENA roubaria a porta do primeiro em silencio. Por isso fica
    # desligado la, e ligado no Linux, onde o comportamento e o esperado.
    allow_reuse_address = not sys.platform.startswith("win")


# ---------------------------------------------------------------------------
# BLOCO 9 - Inicializacao
# ---------------------------------------------------------------------------

# Faixas de endereco e o que cada uma significa na pratica.
FAIXAS_DE_REDE = [
    ("169.254.", "cabo_direto", "Cabo direto entre dois PCs"),
    ("192.168.137.", "ponto_acesso", "Ponto de acesso do Windows"),
    # Adaptadores que o Windows cria sozinho para maquina virtual, WSL,
    # VirtualBox e Docker. Aparecem como se fossem rede local, mas nenhum
    # colega alcanca esses enderecos - e era isso que fazia o aluno copiar
    # o endereco errado e a conexao nunca funcionar.
    ("172.16.", "virtual", "Adaptador virtual (não serve para o colega)"),
    ("172.17.", "virtual", "Adaptador virtual (não serve para o colega)"),
    ("172.18.", "virtual", "Adaptador virtual (não serve para o colega)"),
    ("172.19.", "virtual", "Adaptador virtual (não serve para o colega)"),
    ("172.30.", "virtual", "Adaptador virtual (não serve para o colega)"),
    ("172.31.", "virtual", "Adaptador virtual (não serve para o colega)"),
    ("192.168.56.", "virtual", "Adaptador virtual (não serve para o colega)"),
    ("192.168.99.", "virtual", "Adaptador virtual (não serve para o colega)"),
    # Ponto de acesso pessoal do iPhone usa 172.20.10.0/28 -- faixa real de
    # rede local (celular do colega), nao adaptador virtual nenhum. Achado
    # real na auditoria: a entrada antiga aqui era "172.2" (faltou o "0."),
    # que sem querer casava com 172.20. ATE 172.29. inteiros (o Python
    # confere prefixo de texto, nao limite de bloco de IP) e classificava
    # hotspot de iPhone como "adaptador virtual, nao serve para o colega" --
    # exatamente o endereco que o aluno precisava passar.
    ("192.168.", "rede_local", "Rede local"),
    ("10.", "rede_local", "Rede local"),
    ("172.16.", "rede_local", "Rede local"),
    ("172.17.", "rede_local", "Rede local"),
    ("172.18.", "rede_local", "Rede local"),
    ("172.19.", "rede_local", "Rede local"),
    ("172.20.", "rede_local", "Rede local (hotspot de iPhone usa essa faixa)"),
    ("172.21.", "rede_local", "Rede local"),
    ("172.22.", "rede_local", "Rede local"),
    ("172.23.", "rede_local", "Rede local"),
    ("172.24.", "rede_local", "Rede local"),
    ("172.25.", "rede_local", "Rede local"),
    ("172.26.", "rede_local", "Rede local"),
    ("172.27.", "rede_local", "Rede local"),
    ("172.28.", "rede_local", "Rede local"),
    ("172.29.", "rede_local", "Rede local"),
    ("172.30.", "rede_local", "Rede local"),
    ("172.31.", "rede_local", "Rede local"),
]


# Classificacao pelo NOME do adaptador (revisao pos-auditoria). So pela faixa
# de endereco, nesta propria maquina de desenvolvimento, o adaptador do
# Hyper-V (192.168.96.1, "vEthernet (Default Switch)") aparecia como "Rede
# local", e os adaptadores virtuais do Wi-Fi ("Conexao Local*", 169.254.x)
# como "Cabo direto" -- o aluno podia passar qualquer um dos dois ao colega.
# E VPN (OpenVPN em 10.8.x, por exemplo) aparecia como rede local.
PALAVRAS_VIRTUAL = ("hyper-v", "vethernet", "virtualbox", "vmware", "wsl",
                    "docker", "wi-fi direct", "virtual adapter", "loopback")
PALAVRAS_VPN = ("vpn", "tap-windows", "wireguard", "wintun", "openvpn",
                "tailscale", "zerotier", "anyconnect", "fortinet", "forticlient",
                "pangp", "globalprotect", "juniper", "sonicwall", "hamachi",
                "radmin", "nordlynx", "windscribe", "warp")

_adaptadores = {"quando": 0.0, "mapa": {}, "buscando": False, "falhas": 0}

# Quanto tempo o mapa de nomes vale, e de quanto em quanto tempo se pode
# perguntar de novo por um endereco que nao veio na resposta.
VALIDADE_ADAPTADORES = 600.0
REPERGUNTA_ADAPTADORES = 60.0


def atualizar_adaptadores():
    """Pergunta ao Windows o nome de cada adaptador (nao pede administrador).
    Demora ~2,5 s: roda em segundo plano e fica guardado por 10 minutos.

    Achado de 01/10/2026 (reproduzido): quando o PowerShell falhava (modo
    restrito, bloqueado pela escola, ou mais de 15 s para responder num
    notebook fraco) ou nao trazia um dos enderecos do computador, o ARENA o
    abria DE NOVO a cada consulta de endereco -- o grito na rede, a cada
    5 s, e o vigia. 24 PowerShell em 12 s no teste: num Celeron, um nucleo
    inteiro ocupado so com isso. Agora: falhou, espera (1, 2, 4... ate 10
    minutos); endereco que nao veio, pergunta no maximo 1 vez por minuto."""
    mapa = {}
    try:
        comando = ("Get-NetIPAddress -AddressFamily IPv4 | ForEach-Object { "
                   "$a = Get-NetAdapter -InterfaceIndex $_.InterfaceIndex "
                   "-ErrorAction SilentlyContinue; "
                   "'{0}|{1}|{2}' -f $_.IPAddress, $_.InterfaceAlias, $a.InterfaceDescription }")
        saida = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", comando],
            capture_output=True, text=True, timeout=15,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).stdout
        for linha in saida.splitlines():
            partes = linha.strip().split("|")
            if len(partes) == 3 and partes[0]:
                mapa[partes[0]] = (partes[1] + " " + partes[2]).lower()
    except (OSError, subprocess.SubprocessError):
        pass
    with TRAVA_CACHE:
        mudou = bool(mapa) and mapa != _adaptadores["mapa"]
        if mapa:
            _adaptadores["mapa"] = mapa
            _adaptadores["falhas"] = 0
        else:
            _adaptadores["falhas"] += 1
        _adaptadores["quando"] = time.time()
        _adaptadores["buscando"] = False
        if mudou:
            _cache_enderecos["quando"] = 0.0  # a proxima consulta ja usa os nomes


def espera_dos_adaptadores():
    """Segundos ate poder perguntar de novo, depois de falhas seguidas:
    60, 120, 240, 480 e, dali em diante, 600 (o mesmo prazo do mapa bom)."""
    falhas = _adaptadores["falhas"]
    if not falhas:
        return REPERGUNTA_ADAPTADORES
    return min(VALIDADE_ADAPTADORES, REPERGUNTA_ADAPTADORES * (2 ** (falhas - 1)))


def nome_do_adaptador(ip):
    """Nome do adaptador ja conhecido (ou "" se ainda nao se sabe). Se a
    informacao estiver velha ou faltar este endereco, pede uma atualizacao
    em segundo plano -- nunca faz a tela esperar."""
    with TRAVA_CACHE:
        mapa = _adaptadores["mapa"]
        idade = time.time() - _adaptadores["quando"]
        if _adaptadores["falhas"] or ip not in mapa:
            velho = idade > espera_dos_adaptadores()
        else:
            velho = idade > VALIDADE_ADAPTADORES
        if velho and not _adaptadores["buscando"] and sys.platform.startswith("win"):
            _adaptadores["buscando"] = True
            threading.Thread(target=atualizar_adaptadores, daemon=True).start()
        return mapa.get(ip, "")


def classificar_endereco(ip, adaptador=""):
    # Ponto de acesso do Windows primeiro: ele TAMBEM aparece como adaptador
    # "Wi-Fi Direct" virtual, mas e' justamente o endereco que serve.
    if ip.startswith("192.168.137."):
        return "ponto_acesso", "Ponto de acesso do Windows"
    if adaptador:
        if any(p in adaptador for p in PALAVRAS_VPN):
            return "vpn", "VPN (só serve se o colega estiver na mesma VPN)"
        # "Conexao Local* 10" / "Local Area Connection* 10": o asterisco e'
        # como o Windows nomeia os adaptadores virtuais do proprio Wi-Fi.
        if (any(p in adaptador for p in PALAVRAS_VIRTUAL)
                or "local*" in adaptador or "connection*" in adaptador):
            return "virtual", "Adaptador virtual (não serve para o colega)"
    for prefixo, tipo, rotulo in FAIXAS_DE_REDE:
        if ip.startswith(prefixo):
            return tipo, rotulo
    if ip.startswith("127."):
        return "so_aqui", "Só este computador"
    return "outro", "Outra rede"


_cache_enderecos = {"quando": 0.0, "lista": None}


def enderecos_locais(forcar=False):
    """Lista TODOS os enderecos deste computador, nao apenas um.

    Guardado em memoria por 30 segundos. Motivo: descobrir endereco pede
    resolucao de nome ao sistema, e isso pode demorar segundos em rede
    ruim ou sem DNS - justamente a rede da escola. Como /api/estado e a
    primeira coisa que a tela pede ao abrir, sem esse cuidado o ARENA
    demorava para abrir por causa de uma consulta de rede que nem muda.

    Por que isso importa: a versao anterior descobria o endereco
    perguntando "por onde eu sairia para a internet". Sem roteador - dois
    notebooks ligados por um cabo de rede direto - nao existe saida para a
    internet, e a resposta era 127.0.0.1. O aluno nao tinha endereco
    nenhum para passar ao colega, e a partida a dois ficava impossivel
    justamente no cenario mais simples que existe.

    Agora o ARENA pergunta ao sistema TODOS os enderecos que ele tem, e
    explica para que serve cada um. Cabo direto entrega 169.254.x.x, que e
    um endereco perfeitamente valido - so nao serve para internet.
    """
    with TRAVA_CACHE:
        idade, salvo = _cache_enderecos["quando"], _cache_enderecos["lista"]
        if salvo and not forcar and (time.time() - idade) < 30.0:
            return salvo

    achados = {}

    # Caminho 1: enderecos que o proprio nome da maquina resolve.
    # Com limite de tempo: sem DNS, essa consulta pode ficar pendurada.
    anterior = socket.getdefaulttimeout()
    try:
        socket.setdefaulttimeout(1.0)
        for dado in socket.getaddrinfo(socket.gethostname(), None,
                                       socket.AF_INET):
            achados[dado[4][0]] = True
    except (OSError, socket.gaierror):
        pass
    finally:
        socket.setdefaulttimeout(anterior)

    # Caminho 2: por onde sairia para a internet. So funciona com rota
    # definida, mas e o mais confiavel quando existe.
    for alvo in ("10.255.255.255", "192.168.255.255", "169.254.255.255"):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as teste:
                teste.settimeout(0.2)
                teste.connect((alvo, 1))
                achados[teste.getsockname()[0]] = True
        except OSError:
            continue

    lista = []
    for ip in sorted(achados):
        if ip.startswith("127."):
            continue
        tipo, rotulo = classificar_endereco(ip, nome_do_adaptador(ip))
        lista.append({"ip": ip, "tipo": tipo, "rotulo": rotulo,
                      "url": "http://%s:%d" % (ip, PORTA)})

    # Ordem de utilidade: rede local primeiro, cabo direto logo depois.
    # Virtual por ultimo: e o endereco que nunca serve para o colega.
    ordem = {"rede_local": 0, "ponto_acesso": 1, "cabo_direto": 2,
             "outro": 3, "vpn": 4, "virtual": 9}
    lista.sort(key=lambda e: ordem.get(e["tipo"], 9))

    if not lista:
        lista.append({"ip": "127.0.0.1", "tipo": "so_aqui",
                      "rotulo": "Só este computador",
                      "url": "http://127.0.0.1:%d" % PORTA})

    with TRAVA_CACHE:
        _cache_enderecos["quando"] = time.time()
        _cache_enderecos["lista"] = lista
    return lista


def ip_da_rede():
    """O melhor endereco para passar ao colega."""
    return enderecos_locais()[0]["ip"]


def internet_disponivel():
    """Diz se ha internet de verdade, e nao apenas rede local.

    Testa uma conexao direta a servidores de nome publicos, sem consultar
    DNS - assim funciona mesmo quando o DNS da escola esta bloqueado.
    Serve para o ARENA saber quando pode fazer a copia de seguranca online.
    """
    for alvo in (("1.1.1.1", 53), ("8.8.8.8", 53)):
        try:
            with socket.create_connection(alvo, timeout=1.5):
                return True
        except OSError:
            continue
    return False


_LOCALAPPDATA = os.environ.get("LOCALAPPDATA", "")

NAVEGADORES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    # Instalacao SEM administrador (o instalador do Chrome cai aqui
    # quando falta privilegio -- exatamente o caso normal de notebook de
    # aluno, sem admin nenhum). Achado real na auditoria: sem isto, o
    # ARENA nao encontrava o navegador e caia, sem avisar, para uma aba
    # comum em vez da janela "modo app".
    os.path.join(_LOCALAPPDATA, "Google", "Chrome", "Application", "chrome.exe"),
    os.path.join(_LOCALAPPDATA, "Microsoft", "Edge", "Application", "msedge.exe"),
]


def abrir_janela(endereco):
    """Abre o ARENA como janela de aplicativo, sem abas nem barra de
    endereco, para parecer um programa e nao um site.

    Usa o navegador que ja existe no Windows em vez de embutir uma
    interface propria. Motivo pratico: o navegador ja esta na maquina e ja
    esta na memoria. Uma janela grafica propria custaria de 15 a 25 MB a
    mais de RAM, o que pesa justamente nas maquinas de 4 GB.
    """
    for caminho in NAVEGADORES:
        if os.path.isfile(caminho):
            try:
                subprocess.Popen([
                    caminho,
                    "--app=" + endereco,
                    "--window-size=1180,760",
                    "--disable-features=Translate,AutofillServerCommunication",
                ])
                return
            except OSError:
                continue
    # Nenhum encontrado: abre do jeito comum, em aba.
    webbrowser.open(endereco)


# O servidor HTTP que esta no ar agora, e se ele esta sendo trocado.
# "Aceitar conexoes da rede" muda ONDE o servidor escuta: so neste computador
# (127.0.0.1) ou na rede inteira (0.0.0.0). Isso e' decidido ao abrir o
# socket -- antes, a unica forma de mudar era fechar e abrir o ARENA (passo
# que travava a sala: 30 alunos fechando e reabrindo). Agora o servidor
# encerra e sobe de novo sozinho, no mesmo processo, em menos de 1 segundo.
SERVIDOR_ATUAL = {"servidor": None, "trocando": False}
# A marca "trocando" e a troca do servidor andam juntas sob esta trava. Sem
# ela, dois cliques rapidos na chave podiam fazer o laco de principal() ver
# um servidor encerrado SEM a marca -- e o ARENA fechava em vez de reabrir.
TRAVA_REDE = threading.Lock()


def escuta_da_config(config):
    return "0.0.0.0" if config.get("permitir_rede") else "127.0.0.1"


def trocar_escuta_de_rede():
    """Pede para o servidor reabrir com a escuta nova. Devolve False quando
    nao ha servidor principal (ex.: teste que sobe o seu proprio)."""
    if SERVIDOR_ATUAL["servidor"] is None:
        return False

    def encerrar_depois_da_resposta():
        time.sleep(0.3)   # deixa a resposta do /api/config chegar na tela
        with TRAVA_REDE:
            atual = SERVIDOR_ATUAL["servidor"]
            if atual is None:
                return
            SERVIDOR_ATUAL["trocando"] = True
        atual.shutdown()   # fora da trava: shutdown espera o laco parar

    threading.Thread(target=encerrar_depois_da_resposta, daemon=True).start()
    return True


PASTA_M3U = os.path.join(PASTA_DADOS, "m3u")


def lista_de_discos(jogo, caminho_jogo):
    """Jogo de varios discos ("discos" no indice): grava dados\\m3u\\<nome do
    disco 1>.m3u com os discos, um por linha, e abre ELA -- o RetroArch troca
    de disco sem sair do jogo (menu -> Controle de disco).

    O nome e' o do disco 1 de proposito: o save e o memory card ficam com o
    MESMO nome de quando o aluno abria o disco 1 sozinho, entao nada some.
    Nucleo que nao aceita .m3u, ou disco que sumiu: abre o disco 1 como
    antes."""
    discos = jogo.get("discos") or []
    if len(discos) < 2 or not indexador.nucleo_aceita_m3u(jogo.get("core")):
        return caminho_jogo
    caminhos = [os.path.join(RAIZ, d) for d in discos]
    if not all(os.path.isfile(c) and dentro_da_pasta(c, PASTA_JOGOS) for c in caminhos):
        return caminho_jogo
    destino = os.path.join(PASTA_M3U, os.path.splitext(os.path.basename(caminhos[0]))[0] + ".m3u")
    try:
        os.makedirs(PASTA_M3U, exist_ok=True)
        gravar_texto_atomico(destino, "\n".join(caminhos) + "\n")
    except OSError:
        return caminho_jogo
    return destino


def conferir_fliperamas():
    """Confere, em segundo plano, se algum zip de fliperama esta danificado
    (servidor\\integridade.py: o mslugx.zip abria com personagens de cor
    estranha). Cada zip uma vez so (o resultado fica guardado); devagar, e
    parado enquanto um jogo esta aberto. Achou defeito novo: refaz a lista,
    para o cartao do jogo avisar."""
    time.sleep(8.0)                       # a tela abre primeiro
    try:
        jogos = [j for j in manifesto()["jogos"] if j.get("romset")]
    except Exception:
        return
    achou = False
    for jogo in jogos:
        caminho = os.path.join(RAIZ, jogo["arquivo"])
        if integridade.parte_danificada(caminho, conferir=False) is not None:
            continue                      # ja conferido (ou nao e' .zip)
        while JOGO_EM_ANDAMENTO["ativo"] and not VIGIA["encerrar"].is_set():
            time.sleep(5.0)
        if VIGIA["encerrar"].is_set():
            return
        try:
            if integridade.parte_danificada(caminho):
                achou = True
        except Exception:
            continue
        time.sleep(1.0 if ECONOMICO else 0.2)
    if achou:
        limpar_caches()
        manifesto(forcar=True)


def organizar_bios(esperar=3.0):
    """A pasta BIOS do ARENA (servidor\\bios.py): cria as prateleiras de cada
    console, instala em retroarch\\system o que a pessoa pos nelas (ou nos
    pacotes .zip deixados em retroarch\\system) com o nome que o emulador
    procura, e escreve os LEIA de cada uma. Em segundo plano, logo ao abrir
    (e no botao Conferir, Ajustes -> Emuladores); nunca troca nem apaga
    nada. Instalou: refaz a lista, para o console e os cartoes deixarem de
    pedir a BIOS."""
    time.sleep(esperar)                   # a tela abre primeiro
    try:
        feito = bios.organizar(RAIZ)
    except Exception as falha:            # noqa: BLE001 -- e' ajuda, nunca derruba
        print("[ARENA] Nao consegui conferir as BIOS: %s" % falha)
        return None
    for item in feito["instaladas"]:
        print("[ARENA] BIOS %s instalada (tirada de %s)." % (item["arquivo"], item["de"]))
    for aviso in feito["avisos"]:
        print("[ARENA] %s" % aviso)
    if feito["instaladas"]:
        limpar_caches()
        manifesto(forcar=True)
    return feito


def conferir_vulkan():
    """O automatico escolheu Vulkan porque o vulkan-1.dll carrega; se o
    Vulkan nao enxergar placa nenhuma, troca para d3d11 (ou glcore) antes
    do primeiro jogo -- senao o jogo abre e fecha sem explicar."""
    if MAQUINA.get("driver_video") != "vulkan":
        return
    if hardware.vulkan_tem_placa() is False:
        try:
            ctypes_ok = __import__("ctypes").CDLL("d3d11.dll") is not None
        except OSError:
            ctypes_ok = False
        MAQUINA["driver_video"] = "d3d11" if ctypes_ok else "glcore"
        print("[ARENA] O Vulkan desta maquina nao enxerga placa de video: "
              "motor automatico trocado para %s." % MAQUINA["driver_video"])


def principal():
    # Janela preta: registro da queda, Edicao Rapida desligada e recados que
    # nunca travam o servidor (servidor\janela_preta.py, achado de 02/10/2026).
    janela_preta.preparar(os.path.join(PASTA_DADOS, "logs"), VERSAO)
    print("=" * 62)
    print("  ARENA %s - servidor local" % VERSAO)
    print("=" * 62)

    # Pasta que nao da para criar nao derruba a abertura. Achado da auditoria
    # 3 (08/10/2026): um ARQUIVO chamado "backup" na pasta do ARENA (ou
    # "saves", "dados"...) fazia o ARENA cair aqui, com o erro cru do Windows,
    # antes de abrir a tela. Agora avisa na janela preta e segue; quem
    # precisar da pasta (a copia de seguranca, por exemplo) explica depois.
    for pasta in (PASTA_DADOS, PASTA_SISTEMA, PASTA_SAVES, PASTA_STATES,
                  PASTA_CAPTURAS, PASTA_CORES, PASTA_CHEATS, PASTA_BACKUP,
                  PASTA_REMAPS, PASTA_CONTROLES):
        try:
            os.makedirs(pasta, exist_ok=True)
        except OSError as falha:
            print("[ARENA] AVISO: nao consegui criar a pasta %s (%s). Se ha um "
                  "arquivo com esse nome na pasta do ARENA, renomeie o arquivo "
                  "e abra o ARENA de novo." % (os.path.relpath(pasta, RAIZ),
                                               getattr(falha, "strerror", None) or falha))

    # Um desligamento abrupto (pen drive retirado, queda de energia) pode
    # deixar arquivos temporarios para tras. Limpa na abertura.
    orfaos = 0
    for pasta in (PASTA_DADOS, PASTA_RETROARCH):
        try:
            for nome in os.listdir(pasta):
                if nome.endswith(".tmp"):
                    os.remove(os.path.join(pasta, nome))
                    orfaos += 1
        except OSError:
            pass
    if orfaos:
        print("  Limpeza:  %d arquivo(s) temporario(s) de uma sessao anterior"
              % orfaos)

    # O RetroArch grava um retroarch__AAAA_MM_DD__HH_MM_SS.log por sessao
    # (log_to_file_timestamp = true, la embaixo neste arquivo) e nunca
    # apaga nenhum sozinho. Achado real na auditoria: depois de um dia de
    # testes, dados\ tinha 38 desses. Mantem so os mais recentes -- da
    # pra investigar um fechamento recente sem o cartao SD/pen drive
    # acumular log para sempre.
    apagados_log = limpar_logs_antigos()
    if apagados_log:
        print("  Limpeza:  %d log(s) antigo(s) do RetroArch" % apagados_log)

    # Pen drive muda de letra, pasta muda de lugar - conserta sozinho antes
    # de mais nada, senao o RetroArch abre com caminho de uma pasta que
    # nao existe mais nesta maquina.
    trocados = graficos.corrigir_caminhos_retroarch_cfg()
    if trocados:
        print("  Caminhos: %d corrigido(s) no retroarch.cfg" % trocados)

    preparar_banco()
    config = carregar_config()
    gravar_override(config)

    inicio = time.monotonic()
    try:
        catalogo = manifesto()
        origem = "cache" if catalogo.get("reaproveitado") else "varredura"
        print("  Catalogo: %d jogo(s)  [%s, %.2fs]"
              % (catalogo["total"], origem, time.monotonic() - inicio))
    except Exception as falha:
        print("  Nao foi possivel montar o catalogo agora: %s" % falha)

    print("  CPU:      %s (%d nucleos)" % (MAQUINA["cpu"], MAQUINA["nucleos"]))
    print("  RAM:      %.1f GB  ->  perfil %s"
          % (MAQUINA["ram_total_gb"], MAQUINA["perfil_maquina"]))
    print("  Disco:    %s em %s" % (MAQUINA["disco"]["descricao"],
                                    MAQUINA["disco"]["unidade"]))
    print("  Sistema:  %s" % MAQUINA["sistema"])
    print("  Video:    motor detectado -> %s" % MAQUINA["driver_video"])
    if ECONOMICO:
        print("  Modo:     economico (maquina modesta ou midia removivel)")
        print("            rede a cada %ds, copia a cada %d min"
              % (INTERVALO_VIGIA, INTERVALO_BACKUP / 60))
    if MAQUINA["removivel"]:
        print("  ATENCAO:  midia removivel. Feche o ARENA antes de retirar.")
    if not MAQUINA["runtime_ok"]:
        print("  ATENCAO:  Visual C++ Runtime ausente. Os jogos nao vao abrir.")
        print("            Instale o pacote Visual C++ Redistributable.")

    try:
        quantas = graficos.gravar_opcoes_dos_nucleos(
            CAPACIDADE["nota"], None, CAPACIDADE.get("nota_gpu"))
        shader = graficos.filtro_de_tela("snes")
        print("  Video:    %s%s" % (MAQUINA["gpu"]["nome"],
                                    " (integrada)" if MAQUINA["gpu"]["integrada"] else ""))
        print("  Imagem:   nota %d/5, placa %d/5, %d ajustes%s"
              % (CAPACIDADE["nota"], CAPACIDADE.get("nota_gpu", 0), quantas,
                 ", filtro de pixel nitido nos consoles 2D" if shader else ""))
    except OSError as falha:
        print("  Imagem:   nao consegui gravar os ajustes (%s)" % falha)

    if not os.path.isfile(EXECUTAVEL_RETROARCH):
        print("  AVISO:    retroarch.exe nao encontrado em .\\retroarch")

    pendentes = contar_pendentes()
    if pendentes:
        print("  Recordes: %d aguardando envio ao servidor" % pendentes)
    if config["servidores"]:
        print("  Amigos:   %s" % ", ".join(a["apelido"]
                                           for a in config["servidores"]))

    # Escuta so no proprio computador por padrao. Para a sala jogar junto,
    # marque 'permitir_rede' nos Ajustes.
    escuta = escuta_da_config(config)
    if escuta == "0.0.0.0":
        print("  Rede:     LIBERADA. Outros PCs usam http://%s:%d"
              % (ip_da_rede(), PORTA))
    else:
        print("  Rede:     fechada (so este computador)")

    local = "http://127.0.0.1:%d" % PORTA
    print("  Endereco: %s" % local)
    print("  Para encerrar, feche esta janela.")
    print("=" * 62)

    try:
        servidor = Servidor((escuta, PORTA), Manipulador)
    except OSError as falha:
        if falha.errno in (errno.EADDRINUSE, 10048):
            print("\n  [ERRO] A porta %d ja esta em uso." % PORTA)
            print("  O ARENA provavelmente ja esta aberto. Procure a outra")
            print("  janela preta, ou abra %s no navegador." % local)
        else:
            print("\n  [ERRO] Nao foi possivel abrir o servidor: %s" % falha)
        try:
            input("\n  Pressione Enter para fechar. ")
        except (EOFError, KeyboardInterrupt):
            pass
        return

    threading.Thread(target=rodar_vigia, daemon=True).start()
    threading.Thread(target=anunciar_e_escutar, daemon=True).start()
    # Vulkan de verdade? (hardware.vulkan_tem_placa): pergunta em segundo
    # plano, num processo a parte, depois que a tela ja abriu.
    threading.Thread(target=conferir_vulkan, daemon=True).start()
    # Zip de fliperama danificado: confere cada um uma vez, devagar.
    threading.Thread(target=conferir_fliperamas, daemon=True).start()
    # A pasta BIOS: prateleiras, LEIA e a BIOS posta la vai para onde o
    # emulador procura, com o nome certo (servidor\bios.py).
    threading.Thread(target=organizar_bios, daemon=True).start()
    # ARENA_SEM_JANELA=1: so o servidor, sem abrir a tela (testes
    # automaticos -- a rodada completa abria dezenas de janelas -- e quem
    # quiser abrir a tela de outro computador).
    # ARENA_REABERTO=1: o ARENA.bat reabriu o servidor depois de uma queda.
    # A tela que ja estava aberta se reconecta sozinha; abrir outra janela
    # so deixaria duas.
    if os.environ.get("ARENA_REABERTO") == "1":
        print("  Reaberto sozinho depois de uma queda. A tela que ja estava")
        print("  aberta volta sozinha em poucos segundos.")
    elif os.environ.get("ARENA_SEM_JANELA") != "1":
        # Sem espera: a porta ja escuta desde o Servidor(...) acima, e o
        # pedido da janela fica na fila do Windows ate o serve_forever logo
        # abaixo. Havia 1,0 s de espera fixa aqui, sem motivo registrado
        # (auditoria 3, Fase 2: a abertura ficou 1 s mais curta).
        threading.Thread(target=abrir_janela, args=(local,), daemon=True).start()

    try:
        with TRAVA_REDE:
            SERVIDOR_ATUAL["servidor"] = servidor
        while True:
            servidor.serve_forever()
            # serve_forever so volta quando alguem chama shutdown(). Se foi a
            # chave da rede, reabre com a escuta nova; senao, e' para sair.
            servidor.server_close()
            with TRAVA_REDE:
                if not SERVIDOR_ATUAL["trocando"]:
                    break
                SERVIDOR_ATUAL["trocando"] = False
                # A config e' lida AQUI, dentro da trava: vale sempre o
                # ultimo clique, mesmo com varios cliques seguidos.
                escuta = escuta_da_config(carregar_config())
                try:
                    servidor = Servidor((escuta, PORTA), Manipulador)
                except OSError as falha:
                    # Nao conseguiu abrir para a rede: volta a escutar so
                    # aqui, para a tela nunca ficar sem servidor.
                    print("[ARENA] Nao consegui abrir para a rede (%s). "
                          "Continuo so neste computador." % falha)
                    servidor = Servidor(("127.0.0.1", PORTA), Manipulador)
                    escuta = "127.0.0.1"
                SERVIDOR_ATUAL["servidor"] = servidor
            if escuta == "0.0.0.0":
                print("  Rede:     LIBERADA agora. Outros PCs usam http://%s:%d"
                      % (ip_da_rede(), PORTA))
            else:
                print("  Rede:     fechada agora (so este computador)")
    except KeyboardInterrupt:
        print("\n  Encerrando...")
    finally:
        SERVIDOR_ATUAL["servidor"] = None
        VIGIA["encerrar"].set()
        servidor.server_close()
        fechar_banco()
        print("  Pronto. Pode retirar o pen drive com seguranca.")
        sys.stdout.flush()   # a fila da janela preta entrega o ultimo recado


if __name__ == "__main__":
    principal()
