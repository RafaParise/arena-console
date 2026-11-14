# -*- coding: utf-8 -*-
"""Programas que abrem JUNTO com o jogo e fecham com ele.

O primeiro e' o DreamPotato (github.com/RikkiGibson/DreamPotato, licenca MIT): um VMU do Dreamcast de verdade numa janela
a parte. Com o encaixe "DreamPotato" ligado em Acessorios, o Flycast fala com ele pela rede do proprio computador
(127.0.0.1): a telinha, os botoes, o som e a MEMORIA do VMU passam a ser os do jogo, e o que se faz de um lado vale do outro.

O ARENA nao leva o DreamPotato no pacote: o zip dele traz a BIOS do VMU da Sega (american_v1.05.bin), que nao se distribui.
Quem quer usar baixa o zip e poe em emuladores\\DreamPotato (o ARENA procura ali). Sem a pasta, nada acontece e o jogo abre
do mesmo jeito.

Mesmo desenho do Lossless Scaling (servidor\\lossless.py): abre antes do jogo, fecha no fim, e so fecha o que o ARENA abriu."""
import json
import os
import subprocess
import sys
import threading
import time

PASTA_SERVIDOR = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(PASTA_SERVIDOR)

# id -> onde procurar. "exe": o arquivo do programa, por sistema; "pasta": a pasta dele dentro de emuladores\.
# "nao_forcar": se o programa nao fechar quando o ARENA pede, fica aberto (em vez de ser derrubado): e' ele perguntando
# se grava o que mudou, e derrubar perderia o save.
PROGRAMAS = {
    "dreampotato": {"nome": "DreamPotato", "pasta": "DreamPotato", "nao_forcar": True,
                    "exe": {"windows": "DreamPotato.exe", "linux": "DreamPotato"}},
}

# O DreamPotato com o Flycast (conferido no codigo dos dois em 10/11/2026): o Flycast se liga a ele e, na mesma hora,
# pergunta "quem e' voce?". Se o VMU nao estiver ENCAIXADO no controle, o DreamPotato responde "reiniciar"
# (FF FF FF FF), o Flycast desiste ("receive failed") e o DreamPotato, com o encaixe automatico (AutoDockEject), desencaixa
# de novo: a ligacao nunca se firma. O encaixe automatico so acontece DEPOIS da ligacao; no Hollycast (o derivado do
# Flycast para o qual ele foi feito) a ordem e' outra. Por isso o ARENA abre o DreamPotato JA encaixado no controle 1
# (porta A, o encaixe A1 que a tela de Acessorios oferece) e sem o encaixe automatico. Vale para a 0.3.1 e a 1.0.0.
AJUSTES_DO_DREAMPOTATO = {"AutoDockEject": False, "VmuConnectionState": "PrimaryDocked", "DreamcastPort": "A"}


def preparar_dreampotato(pasta):
    """Grava os AJUSTES_DO_DREAMPOTATO no Data\\configuration.json dele, sem mexer nos outros ajustes da pessoa.
    Devolve True se gravou (ou se ja estava assim)."""
    arquivo = os.path.join(pasta, "Data", "configuration.json")
    ajustes = {}
    try:
        with open(arquivo, encoding="utf-8-sig") as entrada:
            lido = json.load(entrada)
        if isinstance(lido, dict):
            ajustes = lido
    except (OSError, ValueError):
        pass                              # sem arquivo (primeira vez) ou estragado: comeca do zero, como ele faria
    if all(ajustes.get(chave) == valor for chave, valor in AJUSTES_DO_DREAMPOTATO.items()):
        return True
    ajustes.update(AJUSTES_DO_DREAMPOTATO)
    temporario = "%s.%d.tmp" % (arquivo, threading.get_ident())
    try:
        os.makedirs(os.path.dirname(arquivo), exist_ok=True)
        with open(temporario, "w", encoding="utf-8") as saida:   # sem BOM: e' o que o .NET grava
            json.dump(ajustes, saida, indent=2)
        os.replace(temporario, arquivo)                         # troca de uma vez so (pen drive que sai no meio)
        return True
    except OSError as falha:
        print("[ARENA] Nao consegui ajustar o DreamPotato (%s): ele abre, mas o jogo pode nao se ligar a ele." % falha)
        try:
            os.remove(temporario)
        except OSError:
            pass
        return False


PREPARAR = {"dreampotato": preparar_dreampotato}

# Com a "memoria do VMU compartilhada", o jogo le e grava na memoria do DreamPotato. Sem um arquivo aberto, essa memoria
# so existe nele, e ao fechar ele pergunta se grava (10/11/2026: o ARENA nao derruba, mas o aluno pode nao ver a
# pergunta). Com um arquivo .bin de 128 KB aberto, o DreamPotato grava direto no arquivo. O ARENA usa um arquivo SO dele
# para isso, em saves\DreamPotato: o VMU por jogo do Flycast tem o nome pelo codigo gravado no disco, que o ARENA nao le.
NOME_DO_VMU_DO_DREAMPOTATO = "VMU-A1.bin"
TAMANHO_DO_VMU = 128 * 1024


def vmu_do_dreampotato(pasta_saves, pasta_sistema):
    """O arquivo de VMU que o DreamPotato abre com a memoria compartilhada. Na primeira vez, nasce como copia do VMU comum
    do Flycast (system\\dc\\vmu_save_A1.bin), para os saves que o aluno ja tem continuarem la; um que ja existe NUNCA e'
    trocado. Sem o do Flycast para copiar, devolve None (o DreamPotato abre o VMU vazio dele, como antes)."""
    destino = os.path.join(pasta_saves, "DreamPotato", NOME_DO_VMU_DO_DREAMPOTATO)
    if os.path.isfile(destino):
        return destino if os.path.getsize(destino) == TAMANHO_DO_VMU else None
    origem = os.path.join(pasta_sistema, "dc", "vmu_save_A1.bin")
    if not os.path.isfile(origem) or os.path.getsize(origem) != TAMANHO_DO_VMU:
        return None
    temporario = "%s.%d.tmp" % (destino, threading.get_ident())
    try:
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        with open(origem, "rb") as entrada, open(temporario, "wb") as saida:
            saida.write(entrada.read())
        if os.path.exists(destino):           # outro pedido criou no meio do caminho: o dele fica
            os.remove(temporario)
        else:
            os.replace(temporario, destino)
        return destino
    except OSError as falha:
        print("[ARENA] Nao consegui preparar o VMU do DreamPotato (%s): ele abre com o VMU vazio dele." % falha)
        try:
            os.remove(temporario)
        except OSError:
            pass
        return None

_TRAVA = threading.Lock()
_ABERTOS = {}          # id -> processo que o ARENA abriu


def _sistema():
    return "windows" if os.name == "nt" else "linux"


def achar(programa, raiz=None):
    """O caminho do programa em emuladores\\<pasta>, ou None se nao estiver la (ou se o id nao existir)."""
    ficha = PROGRAMAS.get(programa)
    if not ficha:
        return None
    nome = ficha["exe"].get(_sistema())
    caminho = os.path.join(raiz or RAIZ, "emuladores", ficha["pasta"], nome or "")
    return caminho if nome and os.path.isfile(caminho) else None


def abrir(programa, raiz=None, argumentos=()):
    """Abre o programa (se achar e se ainda nao estiver aberto por aqui), com os 'argumentos' (o arquivo de VMU do
    DreamPotato). Devolve True se o ARENA abriu agora."""
    caminho = achar(programa, raiz)
    if not caminho:
        return False
    with _TRAVA:
        antigo = _ABERTOS.get(programa)
        if antigo is not None and antigo.poll() is None:
            return False
        if programa in PREPARAR:
            PREPARAR[programa](os.path.dirname(caminho))
        try:
            # O mesmo PATH limpo do emulador (processos.ambiente_do_emulador): a DLL de outro programa nunca entra.
            import processos
            raiz_do_arena = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            _ABERTOS[programa] = subprocess.Popen([caminho] + list(argumentos), cwd=os.path.dirname(caminho),
                                                  stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                                  stderr=subprocess.DEVNULL,
                                                  env=processos.ambiente_do_emulador(None, raiz_do_arena))
        except OSError as falha:
            print("[ARENA] Nao consegui abrir o %s: %s" % (PROGRAMAS[programa]["nome"], falha))
            return False
    return True


def abrir_todos(programas, raiz=None, argumentos=None):
    """Abre cada programa da lista (com os argumentos de cada um, {id: [...]}); devolve os ids que o ARENA abriu agora."""
    return [p for p in programas if abrir(p, raiz, (argumentos or {}).get(p, ()))]


def _pedir_para_fechar(processo):
    """Pede para fechar como quem clica no X: no Windows, o taskkill SEM /F manda o "fechar" a janela (o programa grava o
    que precisa antes de sair). Fora do Windows, o SIGTERM faz o mesmo papel."""
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(processo.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        processo.terminate()


def fechar_os_que_o_arena_abriu(espera=6.0):
    """Fecha o que o ARENA abriu (o que a pessoa ja tinha aberto antes fica). Pede com educacao e, se nao fechar, forca
    -- menos os "nao_forcar" (o DreamPotato), que ficam abertos: ele esta perguntando se grava o VMU."""
    with _TRAVA:
        abertos = dict(_ABERTOS)
        _ABERTOS.clear()
    fechados = []
    for programa, processo in abertos.items():
        if processo.poll() is None:
            try:
                _pedir_para_fechar(processo)
                limite = time.monotonic() + espera
                while time.monotonic() < limite and processo.poll() is None:
                    time.sleep(0.2)
                if processo.poll() is None:
                    if PROGRAMAS.get(programa, {}).get("nao_forcar"):
                        print("[ARENA] O %s ficou aberto: ele pergunta se grava o que mudou (responda na janela dele)."
                              % PROGRAMAS[programa]["nome"])
                        continue
                    processo.kill()
                    processo.wait(5)
            except (OSError, subprocess.TimeoutExpired):
                pass                     # um que nao fecha nao impede de fechar os outros
        fechados.append(programa)
    return fechados


if __name__ == "__main__":
    for programa in PROGRAMAS:
        print(programa, "->", achar(programa) or "nao esta em emuladores\\" + PROGRAMAS[programa]["pasta"], file=sys.stderr)
