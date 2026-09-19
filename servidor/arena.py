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

import contextlib
import ctypes
import errno
import hashlib
import json
import os
import re
import shutil
import socket
import sqlite3
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
import acervo      # noqa: E402
import internet_archive  # noqa: E402
import controles   # noqa: E402
import graficos    # noqa: E402
import hardware    # noqa: E402
import indexador   # noqa: E402  (precisam vir depois do ajuste de sys.path)

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
            os.replace(temporario, caminho)
        finally:
            if os.path.exists(temporario):
                try:
                    os.remove(temporario)
                except OSError:
                    pass

# Guarda contra abrir dois jogos ao mesmo tempo. Sem isso, um duplo clique
# apressado sobe duas janelas do RetroArch disputando o mesmo controle.
JOGO_EM_ANDAMENTO = {
    "ativo": False,
    "titulo": "",
    "partida_aberta": False,
    "partida_token": "",
}
LOBBY_PARTIDA = None
TRAVA_LOBBY = threading.Lock()


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
# Conquistas locais
# ---------------------------------------------------------------------------

def ler_conquistas():
    """Calcula conquistas simples sem depender de internet."""
    regras = {
        "primeira_partida": ("Primeira partida", "Terminou sua primeira partida."),
        "veterano": ("Veterano", "Terminou 5 partidas."),
        "maratonista": ("Maratonista", "Terminou 10 partidas."),
        "explorador": ("Explorador", "Jogou 3 jogos diferentes."),
        "campeao": ("Campeão", "Registrou sua primeira pontuação."),
    }
    saida = []
    with banco() as conexao:
        jogadores = {r[0] for r in conexao.execute("SELECT apelido FROM sessao")}
        jogadores |= {r[0] for r in conexao.execute("SELECT apelido FROM placar")}
        for apelido in sorted(jogadores, key=str.lower):
            partidas, jogos, pontos = conexao.execute(
                "SELECT COUNT(*), COUNT(DISTINCT jogo_id), "
                "(SELECT COUNT(*) FROM placar p WHERE p.apelido = ?) "
                "FROM sessao WHERE apelido = ? AND encerrada = 1",
                (apelido, apelido)).fetchone()
            liberadas = {
                "primeira_partida": partidas >= 1,
                "veterano": partidas >= 5,
                "maratonista": partidas >= 10,
                "explorador": jogos >= 3,
                "campeao": pontos >= 1,
            }
            lista = [{"id": chave, "nome": regras[chave][0],
                      "descricao": regras[chave][1], "liberada": valor}
                     for chave, valor in liberadas.items()]
            saida.append({"apelido": apelido, "conquistas": lista,
                          "total": sum(liberadas.values())})
    return saida


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
    "savestate_slot": "0",
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
    "menu_rgui_color_theme": "27",              # tema escuro sobrio
    "rgui_background_filler_thickness_enable": "false",
    "rgui_border_filler_enable": "true",
    "rgui_border_filler_thickness_enable": "false",
    "rgui_full_width_layout": "true",
    "rgui_inline_thumbnails": "false",
    "rgui_particle_effect": "0",                # sem animacao de fundo
    "rgui_show_start_screen": "false",
    "menu_show_advanced_settings": "false",
    "menu_show_help": "false",
    "menu_show_reboot": "false",
    "menu_show_shutdown": "false",
    "menu_show_legacy_thumbnail_updater": "false",
    "content_show_add": "false",
    "content_show_images": "false",
    "content_show_music": "false",
    "content_show_video": "false",
    "content_show_netplay": "true",
    "content_show_playlists": "false",
    "content_show_explore": "false",
    "quick_menu_show_take_screenshot": "true",
    "quick_menu_show_options": "true",
    # Itens que so confundem quem quer salvar e voltar ao jogo.
    "quick_menu_show_save_load_state": "true",
    "quick_menu_show_undo_save_load_state": "true",
    "quick_menu_show_replay": "false",
    "quick_menu_show_cheevos": "false",
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
    "input_bsv_record_toggle": "nul",
    "input_grab_mouse_toggle": "nul",
    "notification_show_recording": "false",
    "notification_show_streaming": "false",
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
    "video_black_frame_insertion": "0",
    "savestate_auto_save": "false",
    "savestate_auto_load": "false",
    "savestate_thumbnail_enable": "false",
    "content_show_favorites": "false",
    "content_show_history": "false",
    "menu_show_online_updater": "false",
    "menu_show_core_updater": "false",
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
        "resumo": "Para PC fraco. Feio, mas nao trava.",
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
        "resumo": "O mais bonito. So use se o PC aguentar.",
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
            "rewind_enable": "true",
            # Resposta instantanea: o emulador roda um quadro escondido e
            # devolve o resultado na hora, tirando o atraso que o console
            # de verdade tinha. So no perfil mais pesado, e so em maquina
            # que aguenta - por isso a checagem de nota logo abaixo.
            "run_ahead_enabled": "true",
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
        "detalhe": "Seu PC nao da conta deste console. Vai travar.",
        "perfil": "desempenho",
    },
}


def classificar(custo):
    """Diz como a plataforma vai se comportar nesta maquina.

    Regra:
      capacidade acima do custo  -> sobra folga  -> Bonito e lisinho
      capacidade igual ao custo  -> da conta justo -> Feio mas lisinho
      capacidade abaixo do custo -> nao da conta   -> Capenga
    """
    nota = CAPACIDADE["nota"]
    if nota >= custo + 1:
        chave = "otimo"
    elif nota >= custo:
        chave = "bom"
    else:
        chave = "ruim"
    return dict(CLASSES[chave], chave=chave)


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
        "tema": "claro",
        "favoritos": [],
        "recentes": [],
        "permitir_rede": True,
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
        "travar_teclas": False,
        "tipo_controle": "xbox360",
        # Por console: direcional, analogicos, vibracao e se o jogador 2
        # vira mouse ou teclado.
        "perfil_controle": {},
        "nome_dispositivo": "",
    }


_config_cache = {"quando": 0.0, "valor": None}


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
                config["avancado"][chave] = valor
    config["apelido"] = str(salvo.get("apelido", ""))[:24]
    config["tema"] = salvo.get("tema") if salvo.get("tema") in ("claro", "escuro") else "claro"
    config["favoritos"] = [str(x)[:300] for x in (salvo.get("favoritos") or [])
                           if isinstance(x, str)][:200]
    config["recentes"] = [str(x)[:300] for x in (salvo.get("recentes") or [])
                          if isinstance(x, str)][:20]
    # A descoberta local faz parte do funcionamento normal dos códigos de
    # amigo e das partidas. Não deve depender de uma chave técnica escondida.
    config["permitir_rede"] = True
    config["nome_dispositivo"] = str(salvo.get("nome_dispositivo", ""))[:40]

    servidores = []
    for item in (salvo.get("servidores") or []):
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
            "codigo_amigo": str(item.get("codigo_amigo", ""))[:20],
        })
    # Migracao das versoes antigas, que guardavam um endereco so.
    antigo = str(salvo.get("servidor_url", "")).strip()
    if antigo and not any(x["url"] == antigo for x in servidores):
        servidores.insert(0, {"apelido": "Escola", "url": antigo, "escola": True})
    config["servidores"] = servidores[:20]

    config["modo_desempenho"] = bool(salvo.get("modo_desempenho"))
    config["ultra_desempenho"] = bool(salvo.get("ultra_desempenho"))
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


def opcoes_efetivas(config, custo=None):
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

    # Trava de seguranca: resposta instantanea custa quase o dobro de
    # processador. Em maquina abaixo de nota 4, ela transforma um jogo que
    # rodava liso num jogo que engasga. Melhor nem oferecer.
    if CAPACIDADE["nota"] < 4:
        opcoes["run_ahead_enabled"] = "false"

    opcoes.update(config.get("avancado", {}))
    opcoes["video_driver"] = driver

    # Teclas e botoes que o aluno definiu na tela do ARENA. Entram por
    # ultimo, e so o que ele mexeu: o resto continua como o RetroArch tinha.
    opcoes.update(controles.opcoes_do_retroarch())

    # Filtro de tela: so entra se o perfil pedir E o arquivo existir.
    if opcoes.get("video_shader_enable") == "true":
        caminho = graficos.shader_para(CAPACIDADE.get("nota_gpu", CAPACIDADE["nota"]))
        if caminho:
            opcoes["video_shader"] = caminho
        else:
            # Sem o pacote de shaders instalado, ligar o filtro deixaria a
            # tela preta. Melhor desligar em silencio.
            opcoes["video_shader_enable"] = "false"

    return opcoes


# ---------------------------------------------------------------------------
# Ultra desempenho
# ---------------------------------------------------------------------------
# O que este modo FAZ, e cada item e real:
#
#   - o emulador sobe para prioridade alta e o ARENA cai para a mais baixa;
#   - o ARENA para de vigiar a rede e de anunciar na rede enquanto o jogo
#     roda, entao nao ha nenhuma tarefa de fundo disputando o processador;
#   - a placa de som passa a ser do jogo em modo exclusivo (WASAPI), o que
#     tira o misturador do Windows do caminho;
#   - tela cheia de verdade, nao janela sem borda;
#   - o teclado e o mouse ficam presos na janela do jogo, entao a tecla
#     Windows e o Alt+Tab vao para o jogo em vez do sistema;
#   - filtros, voltar no tempo e resposta instantanea saem de cena.
#
# O que ele NAO faz, e nao adianta prometer:
#
#   - nao desliga o Windows nem impede o Ctrl+Alt+Del. So um programa com
#     senha de administrador e driver proprio conseguiria, e o aluno nao
#     tem essa senha na maquina da escola;
#   - nao fecha programas de ninguem. Se o Teams estiver aberto, ele
#     continua aberto - so perde a vez na fila do processador.
#
# Para sair: feche o jogo com F10.

ULTRA_DESEMPENHO = {
    # Som direto na placa, sem o misturador do Windows no meio.
    "audio_driver": "wasapi",
    "audio_wasapi_exclusive_mode": "true",
    "audio_latency": "32",
    "audio_resampler_quality": "1",

    # Tela cheia de verdade.
    "video_fullscreen": "true",
    "video_windowed_fullscreen": "false",
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


def gravar_override(config, custo=None, extras=None, em_partida=False):
    """Monta o arquivo de configuracao extra que o RetroArch vai ler."""
    opcoes = opcoes_efetivas(config, custo)

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

    if config.get("ultra_desempenho"):
        opcoes.update(ULTRA_DESEMPENHO)

    if config.get("travar_teclas"):
        # Prende o teclado no jogo: Alt+Tab e a tecla Windows passam a ser
        # do jogo. O Esc para de abrir o menu enquanto isso estiver ligado
        # - por isso a tecla de escape abaixo, que liga e desliga na hora.
        opcoes["input_auto_game_focus"] = "1"
        opcoes["input_game_focus_toggle"] = "f9"

    if extras:
        opcoes.update(extras)

    for pasta in (PASTA_SAVES, PASTA_STATES, PASTA_CAPTURAS, PASTA_SISTEMA,
                  PASTA_CHEATS, PASTA_REMAPS, PASTA_CONTROLES):
        os.makedirs(pasta, exist_ok=True)

    # Saves, estados e capturas sempre dentro do ARENA: e o que torna a
    # pasta portatil de verdade.
    opcoes["savefile_directory"] = PASTA_SAVES
    opcoes["savestate_directory"] = PASTA_STATES
    opcoes["screenshot_directory"] = PASTA_CAPTURAS
    opcoes["system_directory"] = PASTA_SISTEMA
    opcoes["cheat_database_path"] = PASTA_CHEATS
    opcoes["input_remapping_directory"] = PASTA_REMAPS
    opcoes["joypad_autoconfig_dir"] = PASTA_CONTROLES
    opcoes["playlist_directory"] = PASTA_DADOS
    opcoes["log_dir"] = PASTA_DADOS

    linhas = ["# Gerado pelo ARENA. Nao edite a mao: sera reescrito."]
    linhas += ['%s = "%s"' % (c, opcoes[c]) for c in sorted(opcoes)]

    os.makedirs(PASTA_DADOS, exist_ok=True)
    gravar_texto_atomico(ARQUIVO_OVERRIDE, "\n".join(linhas) + "\n")
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


def manifesto(forcar=False):
    """Catalogo de jogos, com cache curto em memoria."""
    with TRAVA_CACHE:
        idade, salvo = _cache["manifesto"]
        if not forcar and salvo and (time.time() - idade) < VALIDADE_CACHE:
            return salvo
        resultado = indexador.indexar(forcar=forcar)
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
        if caminho_externo:
            # Com o emulador de fora instalado, nem nucleo nem arquivo de
            # sistema do RetroArch importam: quem manda e ele.
            estado = "pronta"
            motivo = ""
        elif not core_ok:
            estado = "sem_core"
            motivo = "Nucleo nao instalado. Baixe pelo RetroArch."
        elif precisa_sistema and not tem_sistema:
            estado = "falta_sistema"
            motivo = ("Precisa de %d arquivo(s) de sistema em "
                      "retroarch\\system." % plataforma["arquivos_sistema"])
        else:
            estado = "pronta"
            motivo = ""

        classe = classificar(plataforma.get("custo", 3))
        resultado.append({
            "id": plataforma["id"],
            "nome": plataforma["nome"],
            "descricao": plataforma["descricao"],
            "peso": plataforma["peso"],
            "pasta": plataforma["pasta"],
            "custo": plataforma.get("custo", 3),
            "estado": estado,
            "motivo": motivo,
            # Como vai rodar nesta maquina: verde, azul ou vermelho.
            "classe": classe["chave"],
            "classe_rotulo": classe["rotulo"],
            "classe_cor": classe["cor"],
            "classe_detalhe": classe["detalhe"],
            "emulador": (dados_externo["nome"] if caminho_externo
                         else "RetroArch"),
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
        "classe": "bom", "classe_rotulo": "", "classe_cor": "azul",
        "classe_detalhe": "", "perfil_sugerido": "",
        "emulador": "-", "externo_sugerido": None,
    }

    # Nao copiar cada jogo so para carimbar o estado da plataforma nele.
    # Com doze mil jogos, essa copia sozinha custava dezenas de MB e um
    # JSON bem maior. A tela ja recebe a lista de plataformas: basta ela
    # cruzar pelo 'plataforma' que cada jogo ja carrega.
    jogos = [j for j in manifesto()["jogos"] if j["plataforma"] in por_id]

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


def achar_jogo(jogo_id):
    return next((j for j in manifesto()["jogos"] if j["id"] == jogo_id), None)


# ---------------------------------------------------------------------------
# BLOCO 6 - Execucao do jogo
# ---------------------------------------------------------------------------

def nome_curto_do_core(arquivo_core):
    """'swanstation_libretro.dll' -> 'swanstation'."""
    return os.path.basename(arquivo_core).replace("_libretro.dll", "").lower()


ARQUIVO_QUEDAS = os.path.join(PASTA_DADOS, "fechamentos.json")


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


def ler_fechamentos():
    try:
        with open(ARQUIVO_QUEDAS, "r", encoding="utf-8") as arquivo:
            lista = json.load(arquivo)
        return lista[-10:] if isinstance(lista, list) else []
    except (OSError, ValueError):
        return []


def executar_jogo(jogo, apelido, config, custo=None, partida=None):
    """Abre o RetroArch, espera fechar e grava a sessao.

    Roda em thread separada para o servidor continuar respondendo enquanto
    o aluno joga.
    """
    sessao_uuid = uuid.uuid4().hex

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
        extras_controle = controles.opcoes_do_console(
            jogo["plataforma"],
            jogadores=int(config.get("avancado", {}).get("input_max_users", 2) or 2),
            usar_analogico=escolhas.get("analogico_esq", True),
            vibracao=escolhas.get("vibracao", True),
            dispositivo_extra=escolhas.get("extra"))
        graficos.gravar_opcoes_dos_nucleos(
            CAPACIDADE["nota"], extras_core, CAPACIDADE.get("nota_gpu"))
    except OSError as falha:
        print("[ARENA] Nao consegui gravar as opcoes de imagem: %s" % falha)

    caminho_jogo = os.path.join(RAIZ, jogo["arquivo"])
    pasta_trabalho = PASTA_RETROARCH

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
            escrito = graficos.escrever_config_pcsx2(
                jogo["externo"]["caminho"],
                ultra=bool(config.get("ultra_desempenho")))
            if escrito:
                print("[ARENA] Controle do PCSX2 configurado.")

        print("[ARENA] Abrindo pelo %s" % jogo["externo"]["dados"]["nome"])
    else:
        extra = dict(partida["opcoes"]) if partida else None
        comando = [
            EXECUTAVEL_RETROARCH,
            "-L", os.path.join(PASTA_CORES, jogo["core"]),
            caminho_jogo,
            "--appendconfig", gravar_override(
                config, custo, dict(extra or {}, **extras_controle),
                em_partida=bool(partida)),
        ]
        if partida:
            comando += partida["argumentos"]

    try:
        with TRAVA_BANCO, banco() as conexao:
            conexao.execute(
                "INSERT INTO sessao (uuid, apelido, jogo_id, jogo_titulo, "
                "inicio, dispositivo) VALUES (?, ?, ?, ?, ?, ?)",
                (sessao_uuid, apelido, jogo["id"], jogo["titulo"],
                 agora_utc(), config["dispositivo_id"]),
            )

        inicio = time.monotonic()
        try:
            # Prioridade acima do normal: o jogo ganha a CPU na frente do
            # navegador e do resto. Faz diferenca real em maquina de 2 nucleos.
            extras = {}
            if sys.platform.startswith("win"):
                extras["creationflags"] = getattr(
                    subprocess, "ABOVE_NORMAL_PRIORITY_CLASS", 0)
            # Modo desempenho: o emulador entra com prioridade alta e o
            # ARENA cai para baixa enquanto o jogo roda. O Windows passa a
            # dar o processador para quem esta jogando, e nao para o
            # navegador nem para o servidor. Nao fecha nada de ninguem -
            # so muda quem tem preferencia na fila.
            acelerar = (config.get("modo_desempenho")
                        or config.get("ultra_desempenho"))
            if acelerar and sys.platform.startswith("win"):
                extras["creationflags"] = extras.get("creationflags", 0) | 0x00000080
                try:
                    ctypes.windll.kernel32.SetPriorityClass(
                        ctypes.windll.kernel32.GetCurrentProcess(), 0x00004000)
                except Exception:
                    pass

            # No modo ultra, o ARENA para de vigiar a rede e de se
            # anunciar enquanto o jogo roda. Volta sozinho ao fechar.
            if config.get("ultra_desempenho"):
                VIGIA["suspenso"] = True

            # Registrar o comando exato. Sem isto, quando a partida a dois
            # nao conecta, nao ha como saber se o problema foi o ARENA
            # montar errado ou o RetroArch/rede recusar.
            print("[ARENA] %s" % " ".join(
                ('"%s"' % p if " " in p else p) for p in comando))

            processo = subprocess.Popen(comando, cwd=pasta_trabalho, **extras)
            codigo = processo.wait()

            VIGIA["suspenso"] = False

            # Devolve a prioridade do ARENA ao normal.
            acelerar = (config.get("modo_desempenho")
                        or config.get("ultra_desempenho"))
            if acelerar and sys.platform.startswith("win"):
                try:
                    ctypes.windll.kernel32.SetPriorityClass(
                        ctypes.windll.kernel32.GetCurrentProcess(), 0x00000020)
                except Exception:
                    pass

            # Fechou sozinho? Guarda o motivo, para o aluno nao ficar sem
            # explicacao e para dar o que investigar depois.
            if codigo not in (0, None):
                registrar_fechamento(jogo, codigo, comando)
        except OSError as falha:
            print("[ARENA] Nao foi possivel abrir o RetroArch: %s" % falha)

        duracao = int(time.monotonic() - inicio)

        with TRAVA_BANCO, banco() as conexao:
            conexao.execute(
                "UPDATE sessao SET segundos = ?, encerrada = 1 WHERE uuid = ?",
                (duracao, sessao_uuid),
            )
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
            JOGO_EM_ANDAMENTO["partida_aberta"] = False
            JOGO_EM_ANDAMENTO["partida_token"] = ""


def executar_partida_aguardando(lobby):
    """Abre o host somente depois que um colega confirmar a entrada."""
    global LOBBY_PARTIDA
    entrou = lobby["evento"].wait(timeout=120)
    if not entrou:
        with TRAVA_LOBBY:
            if LOBBY_PARTIDA is lobby:
                LOBBY_PARTIDA = None
        with TRAVA_JOGO:
            JOGO_EM_ANDAMENTO["ativo"] = False
            JOGO_EM_ANDAMENTO["titulo"] = ""
            JOGO_EM_ANDAMENTO["partida_aberta"] = False
            JOGO_EM_ANDAMENTO["partida_token"] = ""
        return

    with TRAVA_LOBBY:
        if LOBBY_PARTIDA is lobby:
            LOBBY_PARTIDA = None
    executar_jogo(lobby["jogo"], lobby["apelido"], lobby["config"],
                  lobby["custo"], lobby["partida"])


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


def fazer_backup():
    """Guarda banco, configuracao e saves comuns na pasta backup."""
    import shutil
    try:
        os.makedirs(PASTA_BACKUP, exist_ok=True)
        carimbo = time.strftime("%Y-%m-%d_%H%M%S")
        destino = os.path.join(PASTA_BACKUP, carimbo)
        os.makedirs(destino, exist_ok=True)

        # A configuracao do RetroArch entra na copia: e ela que guarda o
        # mapeamento dos controles.
        origem_cfg = os.path.join(PASTA_RETROARCH, "retroarch.cfg")
        if os.path.isfile(origem_cfg):
            shutil.copy2(origem_cfg, os.path.join(destino, "retroarch.cfg"))

        for nome in ARQUIVOS_DE_BACKUP:
            origem = os.path.join(PASTA_DADOS, nome)
            if os.path.isfile(origem):
                shutil.copy2(origem, os.path.join(destino, nome))

        # Saves comuns sao pequenos (alguns KB) e sao o que doi perder.
        if os.path.isdir(PASTA_SAVES):
            shutil.copytree(PASTA_SAVES, os.path.join(destino, "saves"),
                            dirs_exist_ok=True)

        # Mantem so as copias mais recentes.
        copias = sorted(
            d for d in os.listdir(PASTA_BACKUP)
            if os.path.isdir(os.path.join(PASTA_BACKUP, d)))
        for antiga in copias[:-COPIAS_MANTIDAS]:
            shutil.rmtree(os.path.join(PASTA_BACKUP, antiga), ignore_errors=True)

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
    import zipfile

    caminho = os.path.join(PASTA_BACKUP, os.path.basename(str(nome_arquivo)))
    if not dentro_da_pasta(caminho, PASTA_BACKUP) or not os.path.isfile(caminho):
        return None, "Pacote nao encontrado na pasta backup."

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
                with pacote.open(item) as origem, open(alvo, "wb") as saida:
                    saida.write(origem.read())
                trazidos += 1
    except (zipfile.BadZipFile, OSError) as falha:
        return None, "Pacote danificado ou ilegivel (%s)." % falha

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
        return {"ok": False, "erro": "Nao consegui gravar a mala: %s" % falha}

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


def codigo_amigo(dispositivo_id):
    """Código curto compartilhável, sem expor o IP da máquina."""
    bruto = hashlib.sha256(("ARENA-AMIGO:" + str(dispositivo_id)).encode("utf-8")).hexdigest().upper()
    return "ARENA-%s-%s" % (bruto[:4], bruto[4:8])


def normalizar_codigo_amigo(codigo):
    return re.sub(r"[^A-Z0-9]", "", str(codigo or "").upper()).replace("ARENA", "", 1)


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
              "ainda podem ser adicionados pelo endereco." % falha)
        return

    falante = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    falante.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

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
                recado = json.dumps({
                    "apelido": config.get("apelido") or "sem apelido",
                    "id": config["dispositivo_id"],
                    "porta": PORTA,
                    "partida_aberta": bool(JOGO_EM_ANDAMENTO.get("partida_aberta")),
                    "jogo_partida": JOGO_EM_ANDAMENTO.get("titulo", "") if JOGO_EM_ANDAMENTO.get("partida_aberta") else "",
                    "partida_token": JOGO_EM_ANDAMENTO.get("partida_token", "") if JOGO_EM_ANDAMENTO.get("partida_aberta") else "",
                }, ensure_ascii=False).encode("utf-8")[:400]
                for destino in ("255.255.255.255", "127.0.0.1"):
                    try:
                        falante.sendto(MARCA_DESCOBERTA + recado,
                                       (destino, PORTA_DESCOBERTA))
                    except OSError:
                        pass

        # ---- escutar ----
        try:
            pacote, remetente = ouvinte.recvfrom(1024)
        except (socket.timeout, OSError):
            continue

        if not pacote.startswith(MARCA_DESCOBERTA):
            continue
        try:
            dados = json.loads(pacote[len(MARCA_DESCOBERTA):].decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            continue

        identificacao = str(dados.get("id", ""))[:32]
        if not identificacao:
            continue

        # "Sou eu?" nao da para responder pelo codigo: em laboratorio com
        # maquinas clonadas o codigo pode se repetir, e ai o ARENA
        # ignoraria o colega achando que e o proprio eco. Quem responde e
        # o par endereco+porta, que e unico de verdade.
        porta_dele = int(dados.get("porta") or PORTA)
        meus = {e["ip"] for e in enderecos_locais()} | {"127.0.0.1"}
        if porta_dele == PORTA and remetente[0] in meus:
            continue

        with TRAVA_VIZINHOS:
            VIZINHOS[identificacao] = {
                "id": identificacao,
                "apelido": str(dados.get("apelido", ""))[:24],
                "ip": remetente[0],
                "porta": int(dados.get("porta") or PORTA),
                "partida_aberta": bool(dados.get("partida_aberta")),
                "jogo_partida": str(dados.get("jogo_partida", ""))[:120],
                "partida_token": str(dados.get("partida_token", ""))[:64],
                "visto_em": time.monotonic(),
            }
            # Some quem sumiu ha mais de um minuto.
            for chave in [k for k, v in VIZINHOS.items()
                          if time.monotonic() - v["visto_em"] > 60]:
                VIZINHOS.pop(chave, None)


def colegas_na_rede():
    """Quem esta gritando na rede agora, fora os que ja sao amigos."""
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
            "codigo_amigo": codigo_amigo(vizinho["id"]),
            "ja_e_amigo": vizinho["id"] in conhecidos or url in conhecidos,
            "partida_aberta": bool(vizinho.get("partida_aberta")),
            "jogo_partida": str(vizinho.get("jogo_partida", ""))[:120],
            "partida_token": str(vizinho.get("partida_token", ""))[:64],
            "ha_quantos_segundos": int(time.monotonic() - vizinho["visto_em"]),
        })
    return saida


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
    except OSError:
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
    url = normalizar_url(destino.get("url"))
    apelido_destino = destino.get("apelido", "servidor")

    if not url:
        return {"ok": False, "apelido": apelido_destino,
                "erro": "Endereco vazio."}

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
                "erro": detalhe or "Recusado (codigo %d)." % falha.code}
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
                    "erro": "Este endereco e o proprio computador."}

        # Caso 2: e outro computador. Trocar o NOSSO codigo, guardar, e
        # avisar. Na proxima sincronizacao ja funciona.
        novo = uuid.uuid4().hex[:12]
        print("[ARENA] Codigo repetido com %s. Trocando o nosso de %s para %s."
              % (alvo, config["dispositivo_id"], novo))
        config["dispositivo_id"] = novo
        config["codigo_proprio"] = True
        salvar_config(config)
        return {"ok": False, "apelido": apelido_destino,
                "erro": ("Voces dois tinham o mesmo codigo de aparelho. "
                         "Ja troquei o meu. Clique em sincronizar de novo.")}

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
    "internet_estava_fora": True,
    "encerrar": threading.Event(),
    # Ligado durante o jogo no modo ultra: as tarefas de fundo param de
    # vez, para nao roubar processador nem tocar no disco enquanto o
    # aluno joga.
    "suspenso": False,
}


def quem_esta_online(config):
    """Testa todos os amigos EM PARALELO, com espera curta."""
    amigos = config.get("servidores") or []
    if not amigos:
        return []

    online = []
    trava = threading.Lock()

    def testar(amigo):
        if servidor_alcancavel(amigo["url"]):
            with trava:
                online.append(amigo["apelido"])

    threads = [threading.Thread(target=testar, args=(a,), daemon=True)
               for a in amigos]
    for t in threads:
        t.start()
    # Espera curta: o teste de cada um ja tem limite proprio.
    for t in threads:
        t.join(timeout=3.0)
    return online


def rodar_vigia():
    """Laco do vigia. Roda ate o ARENA fechar."""
    while not VIGIA["encerrar"].wait(INTERVALO_VIGIA):
        if VIGIA["suspenso"]:
            continue

        try:
            config = carregar_config()
            online = quem_esta_online(config)
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
        return [], "Este reparo so faz sentido no Windows."
    if not os.path.isdir(PASTA_RETROARCH):
        return [], "A pasta retroarch nao foi encontrada."

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
        return [], ("Este computador tambem nao tem as bibliotecas. Copie "
                    "a pasta do ARENA de um computador que tenha, ou peca "
                    "a instalacao do Visual C++ Redistributable.")
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


class Manipulador(BaseHTTPRequestHandler):

    protocol_version = "HTTP/1.1"

    def log_message(self, formato, *args):
        pass

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

    LIMITE_CORPO = 4 * 1024 * 1024

    def ler_corpo(self):
        """Le o JSON enviado. Devolve (dados, erro).

        Quando o corpo passa do limite, o servidor precisa ESVAZIAR a
        conexao antes de responder. Sem isso o cliente recebe um corte
        seco de conexao, sem saber o que aconteceu - foi o que apareceu
        no teste de corpo gigante.
        """
        try:
            tamanho = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return {}, "Tamanho do envio invalido."

        if tamanho <= 0:
            return {}, None

        if tamanho > self.LIMITE_CORPO:
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
            return json.loads(self.rfile.read(tamanho).decode("utf-8")), None
        except (ValueError, UnicodeDecodeError):
            return {}, "O conteudo enviado nao e um JSON valido."

    # -- GET --------------------------------------------------------------
    def do_GET(self):
        caminho = urllib.parse.urlparse(self.path).path

        if caminho.startswith("/api/"):
            try:
                return self.api_get(caminho)
            except Exception as falha:
                return self.erro("Erro interno: %s" % falha, 500)

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
                "codigo_amigo": codigo_amigo(config.get("dispositivo_id", "")),
                # Valores que realmente vao valer, ja com o perfil aplicado.
                # Sem isso a aba Avancado mostraria estado errado.
                "efetivas": opcoes_efetivas(config),
                "perfis": dict(
                    [("automatico", PERFIL_AUTOMATICO)] +
                    [(c, {"rotulo": v["rotulo"], "resumo": v["resumo"]})
                     for c, v in PERFIS_GRAFICOS.items()]),
                "capacidade": CAPACIDADE,
                "economico": ECONOMICO,
                "vigia_suspenso": VIGIA["suspenso"],
                "fechamentos": ler_fechamentos(),
                "repasses": graficos.repasses_disponiveis(),
                "controles": graficos.CONTROLES_CONHECIDOS,
                "consoles_botoes": [
                    {"id": p["id"], "nome": p["nome"]}
                    for p in carregar_catalogo()
                    if p["id"] in graficos.consoles_com_botoes()],
                "externos": graficos.situacao_dos_externos(carregar_catalogo()),
                "bios_disponiveis": graficos.bios_disponiveis(PASTA_SISTEMA),
                "memory_cards": graficos.listar_memory_cards(PASTA_SAVES),
                "bios_consoles": [
                    {"id": p["id"], "nome": p["nome"]}
                    for p in carregar_catalogo()
                    if p["arquivos_sistema"] > 0],
                "shader": os.path.basename(
                    graficos.shader_para(CAPACIDADE["nota"])) or None,
                "porta_partida": graficos.PORTA_PARTIDA,
                "recursos": recursos_visiveis(),
                "grupos": carregar_recursos()["grupos"],
                "jogo_em_andamento": dict(JOGO_EM_ANDAMENTO),
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

        if caminho == "/api/acervo":
            return self.responder_json({"itens": acervo.listar(), "fontes": acervo.fontes()})

        if caminho == "/api/biblioteca-online":
            parametros = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            consulta = (parametros.get("q") or [""])[0]
            return self.responder_json({"itens": internet_archive.buscar(consulta)})

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
                return self.erro("Nao tenho esse jogo.", 404)
            marca = impressao_do_jogo(achado)
            if not marca:
                return self.erro("Nao consegui ler o arquivo.", 404)
            return self.responder_json(marca)

        if caminho == "/api/colegas":
            return self.responder_json({"colegas": colegas_na_rede()})

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

        if caminho in ("/api/ranking", "/api/sinc/ranking"):
            return self.responder_json(ler_ranking())

        if caminho == "/api/conquistas":
            return self.responder_json({"jogadores": ler_conquistas()})

        if caminho == "/api/jogo":
            parametros = urllib.parse.parse_qs(
                urllib.parse.urlparse(self.path).query)
            jogo = achar_jogo((parametros.get("id") or [""])[0])
            if not jogo:
                return self.erro("Jogo nao encontrado.", 404)
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
                "estados": cheats.listar_estados(jogo),
                "tem_save": cheats.tem_save(jogo),
                "cheats": cheats.ler_cheats(jogo),
            })

        return self.send_error(404, "Rota nao encontrada")

    # -- POST -------------------------------------------------------------
    def do_POST(self):
        caminho = urllib.parse.urlparse(self.path).path
        try:
            dados, falha_corpo = self.ler_corpo()
            if falha_corpo:
                return self.erro(falha_corpo, 413)
            return self.api_post(caminho, dados)
        except Exception as falha:
            return self.erro("Erro interno: %s" % falha, 500)

    def api_post(self, caminho, dados):
        if not isinstance(dados, dict):
            return self.erro("O post precisa de um JSON com chaves.", 400)

        if len(json.dumps(dados)) > 50000:
            return self.erro("JSON demais — recomendo dividir por partes.", 413)
        if caminho == "/api/sinc/receber":
            placares = dados.get("placares")
            sessoes = dados.get("sessoes")
            if not isinstance(placares, list) or not isinstance(sessoes, list):
                return self.erro("Formato do lote invalido.")
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
                        "Voces dois tinham o mesmo codigo de aparelho. Ja "
                        "troquei o meu. Peca para ele sincronizar de novo.", 409)

                return self.erro(
                    "Este endereco e o proprio computador. Digite o endereco "
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
                    return self.erro("Tipo de controle desconhecido.")
                config["tipo_controle"] = str(dados["tipo_controle"])

            console = str(dados.get("console", "")).strip().lower()
            if console:
                if console not in {p["id"] for p in carregar_catalogo()}:
                    return self.erro("Console desconhecido.")
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

        # ---- comecar do zero: novo perfil ---------------------------------
        if caminho == "/api/perfil/novo":
            if str(dados.get("confirmar")) != "sim":
                return self.erro("Falta confirmar.")

            with TRAVA_JOGO:
                if JOGO_EM_ANDAMENTO["ativo"]:
                    return self.erro("Feche o jogo aberto antes.", 409)

            apagados = []

            # Guarda uma copia antes de apagar. Se alguem clicar por
            # engano, o progresso ainda esta em backup.
            try:
                fazer_backup()
            except Exception:
                pass

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
        if caminho == "/api/partida/testar":
            alvo = normalizar_url(str(dados.get("endereco", "")))
            partes = urllib.parse.urlsplit(alvo)
            endereco = partes.hostname or ""
            # A porta vem do endereco que o colega passou. Usar a porta
            # local aqui faria o ARENA perguntar a si mesmo se o arquivo e
            # o mesmo - e a resposta seria sempre "sim".
            porta_dele = partes.port or PORTA
            if not endereco:
                return self.erro("Informe o endereco do colega.")

            resultado = {"endereco": endereco, "arena": False,
                         "partida": False, "arquivo": None}

            # 1. O ARENA dele responde? Isso prova que as maquinas se veem.
            try:
                with socket.create_connection((endereco, porta_dele), timeout=2.0):
                    resultado["arena"] = True
            except OSError:
                pass

            # 2. E a porta da partida? Quem responde ali e o RetroArch, e
            #    ele so escuta enquanto a partida esta aberta.
            try:
                with socket.create_connection(
                        (endereco, graficos.PORTA_PARTIDA), timeout=2.0):
                    resultado["partida"] = True
            except OSError:
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
                    "Voces tem o mesmo jogo, mas ARQUIVOS DIFERENTES - regiao "
                    "ou versao. A partida nao comeca assim. Um dos dois "
                    "precisa copiar o arquivo do outro.")
            elif resultado["arquivo"] == "eu nao tenho":
                resultado["diagnostico"] = (
                    "Esse jogo nao esta na SUA lista. Clique em Atualizar "
                    "lista, ou peca o arquivo ao colega.")
            elif resultado["arquivo"] == "ele nao tem":
                resultado["diagnostico"] = (
                    "Ele nao tem esse jogo na lista. Passe o arquivo para ele "
                    "antes de comecar.")
            elif resultado["arena"] and resultado["partida"]:
                resultado["diagnostico"] = (
                    "Tudo certo. A partida dele esta aberta e voce alcanca.")
            elif resultado["arena"]:
                resultado["diagnostico"] = (
                    "Voces se enxergam%s, mas a porta da partida esta fechada. "
                    % (" e o arquivo do jogo e o mesmo"
                       if resultado["arquivo"] == "igual" else "") +
                    "Duas causas: ele ainda nao clicou em 'Eu abro a partida', "
                    "ou o firewall do Windows dele esta bloqueando o "
                    "retroarch.exe. Veja o documento 5.")
            else:
                resultado["diagnostico"] = (
                    "Nao alcanco o computador dele. Confira o endereco, e se "
                    "ele ligou 'Aceitar conexoes da rede' e reabriu o ARENA.")

            return self.responder_json(resultado)

        # ---- abrir so a BIOS do console -----------------------------------
        if caminho == "/api/bios/abrir":
            plataforma_id = str(dados.get("plataforma", "")).strip().lower()
            plataforma = next((p for p in carregar_catalogo()
                               if p["id"] == plataforma_id), None)
            if not plataforma:
                return self.erro("Console desconhecido.")

            with TRAVA_JOGO:
                if JOGO_EM_ANDAMENTO["ativo"]:
                    return self.erro("Feche o jogo aberto antes.", 409)
                JOGO_EM_ANDAMENTO["ativo"] = True
                JOGO_EM_ANDAMENTO["titulo"] = "BIOS do %s" % plataforma["nome"]

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
                    return self.erro("Este console nao tem emulador instalado.")
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
                           "--appendconfig", gravar_override(config)]
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
                return self.erro("Jogo nao encontrado.", 404)

            destino_id = str(dados.get("plataforma", "")).strip().lower()
            plataforma = next((p for p in carregar_catalogo()
                               if p["id"] == destino_id), None)
            if not plataforma:
                return self.erro("Console desconhecido.")

            origem = os.path.join(RAIZ, jogo["arquivo"])
            if not dentro_da_pasta(origem, PASTA_JOGOS) or not os.path.isfile(origem):
                return self.erro("O arquivo do jogo nao esta mais no lugar.", 404)

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
                    "Ja existe um arquivo com esse nome em %s." % plataforma["pasta"])

            try:
                os.makedirs(pasta_destino, exist_ok=True)
                # os.replace nao atravessa disco; move e o caminho seguro.
                shutil.move(origem, destino)
            except OSError as falha:
                return self.erro("Nao consegui mover: %s" % falha)

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

        # ---- corrigir o console de um jogo ---------------------------------
        if caminho == "/api/jogo/console":
            jogo_id = str(dados.get("jogo_id", ""))
            if not achar_jogo(jogo_id):
                return self.erro("Jogo nao encontrado.", 404)

            plataforma = str(dados.get("plataforma", "")).strip().lower()
            validas = {p["id"] for p in carregar_catalogo()}
            if plataforma and plataforma not in validas:
                return self.erro("Console desconhecido.")

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
                return self.erro("Jogo nao encontrado.", 404)
            try:
                apagou = cheats.apagar_estado(jogo, dados.get("espaco"))
            except (TypeError, ValueError):
                return self.erro("Espaco invalido.")
            return self.responder_json({
                "ok": True, "apagou": apagou,
                "estados": cheats.listar_estados(jogo)})

        # ---- cheats ------------------------------------------------------
        if caminho == "/api/cheat/adicionar":
            jogo = achar_jogo(dados.get("jogo_id"))
            if not jogo:
                return self.erro("Jogo nao encontrado.", 404)
            lista, erro = cheats.adicionar_cheat(
                jogo, str(dados.get("descricao", ""))[:120],
                str(dados.get("codigo", "")), bool(dados.get("ligado")))
            if erro:
                return self.erro(erro)
            return self.responder_json({"ok": True, "cheats": lista})

        if caminho == "/api/cheat/alterar":
            jogo = achar_jogo(dados.get("jogo_id"))
            if not jogo:
                return self.erro("Jogo nao encontrado.", 404)
            try:
                indice = int(dados.get("indice"))
            except (TypeError, ValueError):
                return self.erro("Indice invalido.")
            lista, erro = cheats.alterar_cheat(
                jogo, indice, dados.get("ligado"), bool(dados.get("apagar")))
            if erro:
                return self.erro(erro, 404)
            return self.responder_json({"ok": True, "cheats": lista})

        # ---- copia de seguranca -------------------------------------------
        if caminho == "/api/exportar":
            try:
                return self.responder_json(dict(ok=True, **exportar_saves()))
            except OSError as falha:
                return self.erro("Nao consegui montar o pacote: %s" % falha)

        if caminho == "/api/importar":
            resultado, erro = importar_saves(dados.get("arquivo"))
            if erro:
                return self.erro(erro, 404)
            return self.responder_json(dict(ok=True, **resultado))

        if caminho == "/api/backup":
            destino = fazer_backup()
            if not destino:
                return self.erro("Nao foi possivel gravar a copia.")
            return self.responder_json(
                {"ok": True, "pasta": os.path.basename(destino)})

        # ---- amigos e servidores -------------------------------------------
        if caminho == "/api/amigo/codigo":
            codigo = normalizar_codigo_amigo(dados.get("codigo", ""))
            if len(codigo) != 8:
                return self.erro("Código de amigo inválido.")
            config = carregar_config()
            encontrado = None
            with TRAVA_VIZINHOS:
                for vizinho in VIZINHOS.values():
                    if normalizar_codigo_amigo(codigo_amigo(vizinho.get("id", ""))) == codigo:
                        encontrado = vizinho
                        break
            if not encontrado:
                return self.erro("Não encontrei esse amigo na rede local. Os dois ARENAs precisam estar abertos e com a rede liberada.")
            if len(config["servidores"]) >= 20:
                return self.erro("Limite de 20 amigos.")
            if any(a.get("url") == "http://%s:%d" % (encontrado["ip"], encontrado["porta"])
                   for a in config["servidores"]):
                return self.erro("Esse amigo já está na sua lista.")
            config["servidores"].append({
                "apelido": apelido,
                "url": url,
                "id": encontrado["id"] if encontrado else str(uuid.uuid4()),
                "codigo_amigo": codigo_amigo(config["dispositivo_id"]),
                "escola": not encontrado,
            })
            salvar_config(config)
            return self.responder_json({"ok": True, "servidores": config["servidores"]})

        if caminho == "/api/amigo/adicionar":
            config = carregar_config()
            apelido = str(dados.get("apelido", "")).strip()[:24]
            url = str(dados.get("url", "")).strip()[:200]
            if not apelido:
                return self.erro("Escreva o apelido do amigo.")
            if not url:
                return self.erro("Escreva o endereco do ARENA dele.")
            if len(config["servidores"]) >= 20:
                return self.erro("Limite de 20 amigos.")
            if any(a["apelido"].lower() == apelido.lower()
                   for a in config["servidores"]):
                return self.erro("Ja existe um amigo com esse apelido.")

            config["servidores"].append({
                "apelido": apelido, "url": url,
                "escola": bool(dados.get("escola")),
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
            url = normalizar_url(str(dados.get("url", "")))
            if not url:
                return self.erro("Endereco vazio.")
            try:
                retorno = falar_com(url, "/api/sinc/ola", {}, "POST", 4)
            except Exception:
                return self.erro("Nao respondeu. Confira o endereco e se o "
                                 "ARENA dele esta aberto com a rede liberada.")
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
            })

        # ---- bibliotecas graficas sem instalar ------------------------------
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

        if caminho == "/api/acervo/instalar":
            try:
                resultado = acervo.instalar(dados.get("id", ""))
                limpar_caches()
                return self.responder_json({"ok": True, **resultado})
            except (OSError, ValueError, urllib.error.URLError, subprocess.SubprocessError) as falha:
                return self.erro(str(falha), 400)

        if caminho == "/api/biblioteca-online/instalar":
            try:
                resultado = internet_archive.instalar(
                    dados.get("id", ""), dados.get("arquivo", ""), dados.get("plataforma", ""))
                limpar_caches()
                return self.responder_json({"ok": True, **resultado})
            except (OSError, ValueError, urllib.error.URLError, subprocess.SubprocessError) as falha:
                return self.erro(str(falha), 400)

        if caminho == "/api/acervo/salvar":
            try:
                item = acervo.salvar(dados.get("item", {}))
                return self.responder_json({"ok": True, "item": item})
            except (OSError, ValueError) as falha:
                return self.erro(str(falha), 400)

        if caminho == "/api/acervo/remover":
            try:
                resultado = acervo.remover(dados.get("id", ""))
                return self.responder_json({"ok": True, **resultado})
            except (OSError, ValueError) as falha:
                return self.erro(str(falha), 400)

        # ---- download de jogo via Wi-Fi ou Internet Archive -------------
        if caminho == "/api/jogo/baixar":
            jogo_id = str(dados.get("jogo_id", ""))
            jogo = achar_jogo(jogo_id)
            if not jogo:
                return self.erro("Jogo não encontrado.", 404)

            caminho_jogo = os.path.join(RAIZ, jogo["arquivo"])
            if os.path.isfile(caminho_jogo):
                return self.responder_json({"ok": True, "ja_existe": True, "caminho": jogo["arquivo"]})

            modo = dados.get("modo", "automatico")
            ip_host = dados.get("ip_host", "")
            porta_host = int(dados.get("porta_host", 8080))

            # Limpar cache antes do download
            limpar_caches()

            if modo == "wifi" and ip_host:
                try:
                    url = "http://%s:%d/%s" % (ip_host, porta_host, os.path.basename(caminho_jogo))
                    temporario = caminho_jogo + ".download"
                    with urllib.request.urlopen(url, timeout=30) as resposta:
                        with open(temporario, "wb") as f:
                            while True:
                                pacote = resposta.read(65536)
                                if not pacote:
                                    break
                                f.write(pacote)
                    os.replace(temporario, caminho_jogo)
                    limpar_caches()
                    return self.responder_json({"ok": True, "via": "wifi", "tamanho": os.path.getsize(caminho_jogo)})
                except Exception as e:
                    return self.erro("Falha no download via Wi-Fi: %s" % str(e), 400)

            # Fallback para Internet Archive
            try:
                ia_id = dados.get("ia_id", "")
                ia_arquivo = dados.get("ia_arquivo", jogo.get("arquivo", ""))
                if ia_id:
                    resultado = internet_archive.instalar(ia_id, ia_arquivo, jogo["plataforma"])
                    limpar_caches()
                    return self.responder_json({"ok": True, "via": "internet_archive", **resultado})
                return self.erro("Sem modo de download válido.", 400)
            except Exception as e:
                return self.erro("Falha no download via Internet Archive: %s" % str(e), 400)

        if caminho == "/api/instancia/servidor":
            try:
                import transferencia as tf
                porta = int(dados.get("porta", 8080))
                servidores = dados.get("servidores", [])
                url = tf.iniciar_servidor(porta, servidores) if hasattr(tf, 'iniciar_servidor') else None
                if url:
                    return self.responder_json({"ok": True, "url": url, "porta": porta})
                return self.erro("Falha ao iniciar servidor.", 500)
            except Exception as e:
                return self.erro(str(e), 500)

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
            if "travar_teclas" in dados:
                config["travar_teclas"] = bool(dados["travar_teclas"])
            if "ultra_desempenho" in dados:
                config["ultra_desempenho"] = bool(dados["ultra_desempenho"])
                # Ultra sem prioridade nao faz sentido: ligam juntos.
                if config["ultra_desempenho"]:
                    config["modo_desempenho"] = True

            if "apelido" in dados:
                config["apelido"] = str(dados["apelido"]).strip()[:24]
            if dados.get("tema") in ("claro", "escuro"):
                config["tema"] = dados["tema"]

            for chave, limite in (("favoritos", 200), ("recentes", 20)):
                if chave in dados and isinstance(dados[chave], list):
                    config[chave] = list(dict.fromkeys(
                        str(x)[:300] for x in dados[chave]
                        if isinstance(x, str)))[:limite]

            if "permitir_rede" in dados:
                config["permitir_rede"] = bool(dados["permitir_rede"])

            if dados.get("restaurar"):
                config["avancado"] = dict(AVANCADO_PADRAO)
                config["perfil_grafico"] = "automatico"

            salvar_config(config)
            gravar_override(config)
            return self.responder_json({
                "ok": True, "config": config,
                "efetivas": opcoes_efetivas(config),
            })

        if caminho == "/api/partida/entrada":
            global LOBBY_PARTIDA
            token = str(dados.get("token", "")).strip()[:64]
            jogo_id = str(dados.get("jogo_id", "")).strip()[:240]
            with TRAVA_LOBBY:
                lobby = LOBBY_PARTIDA
                if not lobby or token != lobby["token"] or jogo_id != lobby["jogo"]["id"]:
                    return self.erro("Essa sala já fechou ou está usando outro jogo.", 409)
                lobby["evento"].set()
            return self.responder_json({"ok": True, "titulo": lobby["jogo"]["titulo"]})

        if caminho == "/api/jogar":
            jogo = achar_jogo(dados.get("jogo_id"))
            if not jogo:
                return self.erro("Jogo nao esta no catalogo. Clique em Atualizar lista.", 404)

            plataforma = next((p for p in carregar_catalogo()
                               if p["id"] == jogo["plataforma"]), None)
            if not plataforma:
                return self.erro("Plataforma desconhecida.")

            # Emulador de fora tem prioridade. Se ele existe, o RetroArch
            # nem precisa estar instalado para esta plataforma.
            caminho_externo, dados_externo = graficos.achar_externo(plataforma)

            if not caminho_externo:
                if not os.path.isfile(EXECUTAVEL_RETROARCH):
                    return self.erro(
                        "retroarch.exe nao foi encontrado na pasta retroarch.")
                if not os.path.isfile(os.path.join(PASTA_CORES, plataforma["core"])):
                    sugestao = ""
                    if dados_externo:
                        sugestao = (" Ou instale o %s na pasta emuladores."
                                    % dados_externo["nome"])
                    return self.erro(
                        "O nucleo desta plataforma nao esta instalado." + sugestao)

            caminho_rom = os.path.join(RAIZ, jogo["arquivo"])
            if not dentro_da_pasta(caminho_rom, PASTA_JOGOS) or not os.path.isfile(caminho_rom):
                return self.erro("O arquivo do jogo nao esta mais no lugar.", 404)

            jogo = dict(jogo)
            jogo["core"] = plataforma["core"]
            if caminho_externo:
                jogo["externo"] = {"caminho": caminho_externo,
                                   "dados": dados_externo}

            config = carregar_config()
            apelido = (dados.get("apelido") or config["apelido"] or "convidado")[:24]

            # Conferir e marcar DENTRO DA MESMA TRAVA. Em travas separadas
            # abre-se uma janela em que varios pedidos passam juntos, e o
            # aluno acaba com varios emuladores abertos disputando o mesmo
            # controle. Foi o que o teste de rajada mostrou.
            with TRAVA_JOGO:
                if JOGO_EM_ANDAMENTO["ativo"]:
                    return self.erro(
                        "Ja existe um jogo aberto (%s). Feche com F10 antes "
                        "de abrir outro." % JOGO_EM_ANDAMENTO["titulo"], 409)
                JOGO_EM_ANDAMENTO["ativo"] = True
                JOGO_EM_ANDAMENTO["titulo"] = jogo["titulo"]

            # Partida a dois, se pedida.
            partida = None
            modo = dados.get("partida")
            if modo and caminho_externo:
                with TRAVA_JOGO:
                    JOGO_EM_ANDAMENTO["ativo"] = False
                    JOGO_EM_ANDAMENTO["titulo"] = ""
                    JOGO_EM_ANDAMENTO["partida_aberta"] = False
                return self.erro(
                    "Jogar junto so funciona pelo RetroArch. Esta plataforma "
                    "esta usando o %s, que tem rede propria."
                    % dados_externo["nome"], 409)
            if modo and jogo["plataforma"] == "ps1":
                with TRAVA_JOGO:
                    JOGO_EM_ANDAMENTO["ativo"] = False
                    JOGO_EM_ANDAMENTO["titulo"] = ""
                    JOGO_EM_ANDAMENTO["partida_aberta"] = False
                    JOGO_EM_ANDAMENTO["partida_token"] = ""
                return self.erro(
                    "O núcleo de PlayStation usado pelo Arena não oferece "
                    "netplay confiável no RetroArch. Para Metal Slug, use a "
                    "versão Arcade com FBNeo; para jogos de PS1, será preciso "
                    "integrar o servidor próprio do Mednafen.", 409)
            if modo in ("hospedar", "entrar", "assistir"):
                hospedar = (modo == "hospedar")
                assistir = (modo == "assistir")
                endereco = ""
                endereco_url = ""
                if not hospedar:
                    endereco_url = normalizar_url(dados.get("endereco", ""))
                    endereco = urllib.parse.urlsplit(endereco_url).hostname or ""
                    if not endereco:
                        # Ja marcamos a trava acima: soltar antes de sair,
                        # senao o ARENA fica achando que tem jogo aberto.
                        with TRAVA_JOGO:
                            JOGO_EM_ANDAMENTO["ativo"] = False
                            JOGO_EM_ANDAMENTO["titulo"] = ""
                            JOGO_EM_ANDAMENTO["partida_aberta"] = False
                        return self.erro("Informe o endereco de quem esta "
                                         "hospedando a partida.")
                pela_internet = bool(dados.get("pela_internet"))
                if not hospedar and not pela_internet:
                    token = str(dados.get("partida_token", "")).strip()[:64]
                    if not token:
                        with TRAVA_JOGO:
                            JOGO_EM_ANDAMENTO["ativo"] = False
                            JOGO_EM_ANDAMENTO["titulo"] = ""
                            JOGO_EM_ANDAMENTO["partida_aberta"] = False
                            JOGO_EM_ANDAMENTO["partida_token"] = ""
                        return self.erro("A sala não está mais disponível. Atualize a lista de partidas.", 409)
                    try:
                        entrada = falar_com(endereco_url, "/api/partida/entrada", {
                            "token": token,
                            "jogo_id": jogo["id"],
                            "apelido": apelido,
                        }, "POST", 5)
                    except Exception:
                        entrada = {"ok": False}
                    if not entrada.get("ok"):
                        with TRAVA_JOGO:
                            JOGO_EM_ANDAMENTO["ativo"] = False
                            JOGO_EM_ANDAMENTO["titulo"] = ""
                            JOGO_EM_ANDAMENTO["partida_aberta"] = False
                            JOGO_EM_ANDAMENTO["partida_token"] = ""
                        return self.erro("Não consegui entrar nessa sala. Atualize a lista e tente outra partida.", 409)
                partida = {
                    "opcoes": graficos.opcoes_de_partida(
                        apelido, hospedar, assistir=assistir,
                        pela_internet=pela_internet,
                        repasse=str(dados.get("repasse", "saopaulo"))),
                    "argumentos": graficos.argumentos_de_partida(hospedar, endereco),
                    "papel": ("jogador 1" if hospedar
                              else "espectador" if assistir else "jogador 2"),
                }
                with TRAVA_JOGO:
                    JOGO_EM_ANDAMENTO["partida_aberta"] = hospedar
                if hospedar:
                    token = uuid.uuid4().hex
                    lobby = {
                        "token": token,
                        "evento": threading.Event(),
                        "jogo": jogo,
                        "apelido": apelido,
                        "config": config,
                        "custo": plataforma.get("custo"),
                        "partida": partida,
                    }
                    with TRAVA_LOBBY:
                        LOBBY_PARTIDA = lobby
                    with TRAVA_JOGO:
                        JOGO_EM_ANDAMENTO["partida_token"] = token

            if partida and modo == "hospedar":
                threading.Thread(target=executar_partida_aguardando,
                                 args=(lobby,), daemon=True).start()
            else:
                threading.Thread(
                    target=executar_jogo,
                    args=(jogo, apelido, config, plataforma.get("custo"), partida),
                    daemon=True).start()

            resposta = {"ok": True, "titulo": jogo["titulo"],
                        "pela_internet": bool(partida and
                                              dados.get("pela_internet")),
                        "emulador": (dados_externo["nome"] if caminho_externo
                                     else "RetroArch")}
            if partida:
                resposta["papel"] = partida["papel"]
                resposta["porta"] = graficos.PORTA_PARTIDA
                resposta["aguardando"] = bool(modo == "hospedar")
            return self.responder_json(resposta)

        if caminho == "/api/placar":
            try:
                pontos = int(dados.get("pontos"))
            except (TypeError, ValueError):
                return self.erro("Informe a pontuacao usando apenas numeros.")
            if not 0 <= pontos <= 99999999:
                return self.erro("Pontuacao fora da faixa aceita.")

            jogo = achar_jogo(dados.get("jogo_id"))
            if not jogo:
                return self.erro("Jogo nao encontrado.", 404)

            config = carregar_config()
            apelido = (dados.get("apelido") or config["apelido"] or "convidado")[:24]

            with TRAVA_BANCO, banco() as conexao:
                conexao.execute(
                    "INSERT INTO placar (uuid, apelido, jogo_id, jogo_titulo, "
                    "pontos, registrado_em, dispositivo) VALUES (?,?,?,?,?,?,?)",
                    (uuid.uuid4().hex, apelido, jogo["id"], jogo["titulo"],
                     pontos, agora_utc(), config["dispositivo_id"]),
                )
            return self.responder_json({"ok": True, "pendentes": contar_pendentes()})

        return self.send_error(404, "Rota nao encontrada")


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
    ("172.16.", "virtual", "Adaptador virtual (nao serve para o colega)"),
    ("172.17.", "virtual", "Adaptador virtual (nao serve para o colega)"),
    ("172.18.", "virtual", "Adaptador virtual (nao serve para o colega)"),
    ("172.19.", "virtual", "Adaptador virtual (nao serve para o colega)"),
    ("172.2", "virtual", "Adaptador virtual (nao serve para o colega)"),
    ("172.30.", "virtual", "Adaptador virtual (nao serve para o colega)"),
    ("172.31.", "virtual", "Adaptador virtual (nao serve para o colega)"),
    ("192.168.56.", "virtual", "Adaptador virtual (nao serve para o colega)"),
    ("192.168.99.", "virtual", "Adaptador virtual (nao serve para o colega)"),
    ("192.168.", "rede_local", "Rede local"),
    ("10.", "rede_local", "Rede local"),
    ("172.16.", "rede_local", "Rede local"),
    ("172.17.", "rede_local", "Rede local"),
    ("172.18.", "rede_local", "Rede local"),
    ("172.19.", "rede_local", "Rede local"),
    ("172.2", "rede_local", "Rede local"),
    ("172.30.", "rede_local", "Rede local"),
    ("172.31.", "rede_local", "Rede local"),
]


def classificar_endereco(ip):
    for prefixo, tipo, rotulo in FAIXAS_DE_REDE:
        if ip.startswith(prefixo):
            return tipo, rotulo
    if ip.startswith("127."):
        return "so_aqui", "So este computador"
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
        tipo, rotulo = classificar_endereco(ip)
        lista.append({"ip": ip, "tipo": tipo, "rotulo": rotulo,
                      "url": "http://%s:%d" % (ip, PORTA)})

    # Ordem de utilidade: rede local primeiro, cabo direto logo depois.
    # Virtual por ultimo: e o endereco que nunca serve para o colega.
    ordem = {"rede_local": 0, "ponto_acesso": 1, "cabo_direto": 2,
             "outro": 3, "virtual": 9}
    lista.sort(key=lambda e: ordem.get(e["tipo"], 9))

    if not lista:
        lista.append({"ip": "127.0.0.1", "tipo": "so_aqui",
                      "rotulo": "So este computador",
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


NAVEGADORES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
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


def principal():
    print("=" * 62)
    print("  ARENA - servidor local")
    print("=" * 62)

    for pasta in (PASTA_DADOS, PASTA_SISTEMA, PASTA_SAVES, PASTA_STATES,
                  PASTA_CAPTURAS, PASTA_CORES, PASTA_CHEATS, PASTA_BACKUP,
                  PASTA_REMAPS, PASTA_CONTROLES):
        os.makedirs(pasta, exist_ok=True)

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
        shader = graficos.shader_para(CAPACIDADE.get("nota_gpu", CAPACIDADE["nota"]))
        print("  Video:    %s%s" % (MAQUINA["gpu"]["nome"],
                                    " (integrada)" if MAQUINA["gpu"]["integrada"] else ""))
        print("  Imagem:   nota %d/5, placa %d/5, %d ajustes%s"
              % (CAPACIDADE["nota"], CAPACIDADE.get("nota_gpu", 0), quantas,
                 ", filtro %s" % os.path.basename(shader) if shader else ""))
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
    if config["permitir_rede"]:
        escuta = "0.0.0.0"
        print("  Rede:     LIBERADA. Outros PCs usam http://%s:%d"
              % (ip_da_rede(), PORTA))
    else:
        escuta = "127.0.0.1"
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
    threading.Timer(1.0, lambda: abrir_janela(local)).start()

    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\n  Encerrando...")
    finally:
        VIGIA["encerrar"].set()
        servidor.server_close()
        fechar_banco()
        print("  Pronto. Pode retirar o pen drive com seguranca.")


if __name__ == "__main__":
    principal()
