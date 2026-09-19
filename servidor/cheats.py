# -*- coding: utf-8 -*-
"""
ARENA - Cheats e save states
=============================
Duas coisas que o RetroArch ja faz muito bem, e que o ARENA apenas organiza:

CHEATS
    O RetroArch le arquivos '.cht' e mostra os codigos no menu do jogo,
    com um interruptor para ligar e desligar cada um. Ele aceita codigo de
    Game Genie, GameShark, Action Replay e Pro Action Replay.
    Este modulo escreve e le esses arquivos. A edicao acontece na tela do
    ARENA; quem aplica o codigo no jogo e o RetroArch.

SAVE STATES
    O RetroArch guarda 10 estados por jogo, nos espacos 0 a 9. O espaco 0
    grava em 'jogo.state'; os demais em 'jogo.state1' ate 'jogo.state9'.
    Este modulo apenas LE esses arquivos para mostrar na tela quais espacos
    estao ocupados, de quando sao e quanto ocupam.

So biblioteca padrao.
"""

import os
import threading
import re
import time

_TRAVA = threading.Lock()

PASTA_SERVIDOR = os.path.dirname(os.path.abspath(__file__))


def gravar_atomico(caminho, texto):
    """Grava sem deixar meio-termo, mesmo com varias gravacoes ao mesmo tempo.

    Nome de temporario unico por thread: sem isso, duas gravacoes juntas
    disputam o mesmo arquivo e a segunda estoura.
    """
    temporario = "%s.%d.tmp" % (caminho, threading.get_ident())
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with _TRAVA:
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
RAIZ = os.path.dirname(PASTA_SERVIDOR)

PASTA_RETROARCH = os.path.join(RAIZ, "retroarch")
PASTA_CHEATS = os.path.join(PASTA_RETROARCH, "cheats")
PASTA_STATES = os.path.join(PASTA_RETROARCH, "states")
PASTA_SAVES = os.path.join(PASTA_RETROARCH, "saves")

TOTAL_ESPACOS = 10

# Codigo valido: blocos de digitos hexadecimais separados por ':', '-' ou
# espaco/quebra de linha. Cobre os formatos de Game Genie, GameShark e
# Action Replay.
RE_CODIGO = re.compile(r"^[0-9A-Fa-f:\-\s\+]+$")


# ---------------------------------------------------------------------------
# Nomes de arquivo
# ---------------------------------------------------------------------------

def nome_seguro(texto):
    """Transforma um titulo em nome de arquivo valido no Windows."""
    limpo = re.sub(r'[<>:"/\\|?*]', "", str(texto)).strip()
    limpo = re.sub(r"\s+", " ", limpo)
    return limpo[:100] or "sem_nome"


def base_do_jogo(jogo):
    """Nome do arquivo do jogo, sem pasta e sem extensao.

    E assim que o RetroArch nomeia os saves e os estados: pelo nome do
    arquivo da ROM, nao pelo titulo que aparece na tela do ARENA.
    """
    return os.path.splitext(os.path.basename(jogo["arquivo"]))[0]


def caminho_cht(jogo):
    """Onde fica o arquivo de cheats deste jogo.

    Uma pasta por plataforma, do mesmo jeito que o RetroArch organiza.
    """
    pasta = os.path.join(PASTA_CHEATS, nome_seguro(jogo["plataforma_nome"]))
    return os.path.join(pasta, nome_seguro(base_do_jogo(jogo)) + ".cht")


# ---------------------------------------------------------------------------
# Save states: apenas leitura
# ---------------------------------------------------------------------------

def listar_estados(jogo):
    """Diz quais dos 10 espacos estao ocupados para este jogo."""
    base = base_do_jogo(jogo)
    espacos = []

    for numero in range(TOTAL_ESPACOS):
        # Espaco 0 nao leva numero no final. Do 1 ao 9, leva.
        sufixo = ".state" if numero == 0 else ".state%d" % numero
        caminho = os.path.join(PASTA_STATES, base + sufixo)

        item = {"espaco": numero, "existe": False,
                "quando": None, "tamanho_kb": None}
        try:
            dados = os.stat(caminho)
            item["existe"] = True
            item["quando"] = time.strftime("%d/%m/%Y %H:%M",
                                           time.localtime(dados.st_mtime))
            item["tamanho_kb"] = round(dados.st_size / 1024, 1)
        except OSError:
            pass
        espacos.append(item)

    return espacos


def apagar_estado(jogo, espaco):
    """Apaga um espaco especifico."""
    if not 0 <= int(espaco) < TOTAL_ESPACOS:
        raise ValueError("Espaco fora da faixa de 0 a 9.")
    espaco = int(espaco)
    sufixo = ".state" if espaco == 0 else ".state%d" % espaco
    caminho = os.path.join(PASTA_STATES, base_do_jogo(jogo) + sufixo)
    try:
        os.remove(caminho)
        return True
    except OSError:
        return False


def tem_save(jogo):
    """Diz se o jogo tem save comum (o do proprio jogo, nao o estado)."""
    base = base_do_jogo(jogo)
    for extensao in (".srm", ".sav", ".rtc", ".mcr"):
        if os.path.isfile(os.path.join(PASTA_SAVES, base + extensao)):
            return True
    return False


# ---------------------------------------------------------------------------
# Cheats: leitura
# ---------------------------------------------------------------------------

RE_LINHA = re.compile(r'^\s*cheat(\d+)_(\w+)\s*=\s*"?(.*?)"?\s*$')


def ler_cheats(jogo):
    """Le o arquivo .cht do jogo e devolve a lista de codigos."""
    caminho = caminho_cht(jogo)
    if not os.path.isfile(caminho):
        return []

    campos = {}
    try:
        with open(caminho, "r", encoding="utf-8", errors="replace") as arquivo:
            for linha in arquivo:
                achou = RE_LINHA.match(linha)
                if not achou:
                    continue
                indice, campo, valor = achou.groups()
                campos.setdefault(int(indice), {})[campo] = valor
    except OSError:
        return []

    cheats = []
    for indice in sorted(campos):
        item = campos[indice]
        cheats.append({
            "descricao": item.get("desc", "Sem descricao"),
            "codigo": item.get("code", ""),
            "ligado": item.get("enable", "false").lower() == "true",
        })
    return cheats


# ---------------------------------------------------------------------------
# Cheats: escrita
# ---------------------------------------------------------------------------

def validar_codigo(codigo):
    """Confere se o codigo tem cara de codigo antes de gravar.

    Nao valida se o codigo FUNCIONA - so o RetroArch e o jogo sabem disso.
    Valida se o formato e aceitavel, para nao gravar lixo no arquivo.
    """
    codigo = (codigo or "").strip()
    if not codigo:
        return None, "Digite o codigo."
    if len(codigo) > 2000:
        return None, "Codigo grande demais."
    if not RE_CODIGO.match(codigo):
        return None, ("Codigo invalido. Use apenas numeros e as letras de A a F, "
                      "separando as linhas por espaco ou dois-pontos.")
    # Normaliza: uma linha so, blocos separados por '+', que e o separador
    # que o RetroArch usa para codigo de varias linhas.
    blocos = [b for b in re.split(r"[\s+]+", codigo) if b]
    return "+".join(blocos), None


def gravar_cheats(jogo, cheats):
    """Escreve o arquivo .cht no formato que o RetroArch le.

    Formato:
        cheats = 2
        cheat0_desc = "Vidas infinitas"
        cheat0_code = "7E0DBE:09"
        cheat0_enable = false
        cheat0_handler = "1"

    handler 1 significa 'codigo tratado pelo emulador', que e o modo dos
    codigos de Game Genie, GameShark e Action Replay.
    """
    caminho = caminho_cht(jogo)
    os.makedirs(os.path.dirname(caminho), exist_ok=True)

    linhas = ["cheats = %d" % len(cheats), ""]
    for indice, cheat in enumerate(cheats):
        descricao = str(cheat.get("descricao", ""))[:120].replace('"', "'")
        linhas.append('cheat%d_desc = "%s"' % (indice, descricao or "Sem descricao"))
        linhas.append('cheat%d_code = "%s"' % (indice, cheat["codigo"]))
        linhas.append('cheat%d_enable = %s'
                      % (indice, "true" if cheat.get("ligado") else "false"))
        linhas.append('cheat%d_handler = "1"' % indice)
        linhas.append("")

    # Grava em arquivo temporario e so depois troca. Se o pen drive for
    # retirado no meio, o arquivo antigo continua intacto.
    gravar_atomico(caminho, "\n".join(linhas))
    return caminho


def adicionar_cheat(jogo, descricao, codigo, ligado=False):
    codigo_limpo, erro = validar_codigo(codigo)
    if erro:
        return None, erro

    cheats = ler_cheats(jogo)
    if len(cheats) >= 60:
        return None, "Limite de 60 codigos por jogo."

    cheats.append({"descricao": descricao, "codigo": codigo_limpo,
                   "ligado": bool(ligado)})
    gravar_cheats(jogo, cheats)
    return cheats, None


def alterar_cheat(jogo, indice, ligado=None, apagar=False):
    cheats = ler_cheats(jogo)
    if not 0 <= indice < len(cheats):
        return None, "Codigo nao encontrado."
    if apagar:
        cheats.pop(indice)
    elif ligado is not None:
        cheats[indice]["ligado"] = bool(ligado)
    gravar_cheats(jogo, cheats)
    return cheats, None
