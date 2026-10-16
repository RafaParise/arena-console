# -*- coding: utf-8 -*-
r"""Descoberta de colegas: um pacote torto nao pode matar quem escuta, e a
lista de vizinhos tem limite.

Achado da auditoria 3 (07/10/2026), Fase 1: em anunciar_e_escutar, depois do
json.loads, "dados.get(...)" e "int(dados.get('porta'))" ficavam FORA do
try. Um unico pacote de qualquer computador da rede na porta UDP 55436 --
um JSON que nao e' objeto, ou "porta": "abc" -- levantava erro e encerrava a
linha de execucao que escuta: a descoberta de colegas acabava ate alguem
fechar e abrir o ARENA. A lista de vizinhos tambem nao tinha limite.

Desde 16/10/2026, a porta so escuta com "Aceitar conexoes da rede" ligado ou
enquanto a janela do Jogar Junto procura partida: o teste pede a procura
(/api/partida/procurar?rede=1, a rota de verdade) e espera a porta abrir.

Num ARENA isolado (copia no temporario, servidor de verdade):
  1. um grito valido aparece em /api/colegas;
  2. chegam pacotes tortos (JSON que nao e' objeto, porta que nao e' numero,
     porta fora da faixa, sem id);
  3. um grito valido novo TEM que aparecer (quem escuta continua vivo);
  4. 500 gritos de um mesmo computador com codigos inventados nao enchem a
     lista (no maximo LIMITE_POR_ENDERECO desse endereco).

A porta UDP 55436 e' fixa: o teste recusa rodar com outro ARENA aberto.

Uso: servidor\python\python.exe testes\teste_descoberta_pacote_torto.py
"""
import ast
import json
import os
import socket
import sys
import tempfile
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
import limpeza  # noqa: E402
import tela_sem_janela  # noqa: E402
import teste_servidor_que_cai as servidor_de_teste  # noqa: E402

MARCA = b"ARENA1"
PORTA_UDP = 55436


def marca_de_verdade():
    """A marca que o servidor espera (MARCA_DESCOBERTA = b"..." em arena.py),
    lida como literal (ast.literal_eval nao executa codigo)."""
    with open(os.path.join(RAIZ, "servidor", "arena.py"), encoding="utf-8") as f:
        for linha in f:
            if linha.startswith("MARCA_DESCOBERTA"):
                return ast.literal_eval(linha.split("=", 1)[1].split("#")[0].strip())
    return MARCA


def gritar(marca, dados, de="127.0.0.1"):
    """Manda um grito saindo do endereco `de` (o Windows aceita qualquer
    127.x.y.z como "este computador": cada um faz as vezes de um colega)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.bind((de, 0))
        corpo = dados if isinstance(dados, bytes) else json.dumps(dados).encode("utf-8")
        s.sendto(marca + corpo, ("127.0.0.1", PORTA_UDP))
    finally:
        s.close()


def ids_na_lista(porta):
    _status, resposta = servidor_de_teste.pedir(porta, "GET", "/api/colegas")
    lista = resposta.get("colegas", resposta) if isinstance(resposta, dict) else resposta
    return {str(c.get("id")) for c in (lista or []) if isinstance(c, dict)}


def porta_udp_livre():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.bind(("", PORTA_UDP))
        return True
    except OSError:
        return False
    finally:
        s.close()


def main():
    falhas, total = [], [0]

    def confere(nome, ok, detalhe=""):
        total[0] += 1
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, "" if ok else detalhe), flush=True)
        if not ok:
            falhas.append(nome)

    if not porta_udp_livre():
        print("A porta UDP %d esta em uso (outro ARENA aberto?). Feche e rode de novo." % PORTA_UDP)
        return 2
    marca = marca_de_verdade()
    pasta = tempfile.mkdtemp(prefix="arena_descoberta_torta_")
    try:
        copia = os.path.join(pasta, "isolado", "ARENA")
        os.makedirs(copia)
        servidor_de_teste.preparar_copia(copia)
        porta = tela_sem_janela.porta_livre()
        processo = servidor_de_teste.subir(copia, porta, True, os.path.join(pasta, "sem-trava"))
        try:
            confere("o servidor abre", servidor_de_teste.esperar_servidor(porta))
            servidor_de_teste.pedir(porta, "GET", "/api/partida/procurar?rede=1")
            fim = time.time() + 10
            while porta_udp_livre() and time.time() < fim:
                time.sleep(0.25)
            confere("a procura de partida abre a porta da descoberta", not porta_udp_livre())

            print("1. Um grito valido aparece")
            gritar(marca, {"id": "colega-antes", "apelido": "Antes", "porta": 9001})
            time.sleep(1.5)
            confere("colega-antes na lista", "colega-antes" in ids_na_lista(porta), ids_na_lista(porta))

            print("2. Pacotes tortos")
            for torto in (b"[1, 2, 3]", b'"so um texto"', b"42",
                          json.dumps({"id": "torto-1", "porta": "abc"}).encode(),
                          json.dumps({"id": "torto-2", "porta": [1]}).encode(),
                          json.dumps({"id": "torto-3", "porta": 999999}).encode(),
                          json.dumps({"apelido": "sem id"}).encode()):
                gritar(marca, torto)
            time.sleep(1.5)

            print("3. Depois dos tortos, quem escuta continua vivo")
            gritar(marca, {"id": "colega-depois", "apelido": "Depois", "porta": 9002})
            time.sleep(2.0)
            vistos = ids_na_lista(porta)
            confere("colega-depois na lista (a descoberta nao morreu)", "colega-depois" in vistos, sorted(vistos))
            confere("nenhum torto entrou", not any(i.startswith("torto") for i in vistos), sorted(vistos))

            print("4. 500 codigos inventados do mesmo computador")
            for n in range(500):
                gritar(marca, {"id": "inventado-%03d" % n, "apelido": "x", "porta": 9100})
            time.sleep(2.0)
            vistos = ids_na_lista(porta)
            inventados = [i for i in vistos if i.startswith("inventado")]
            confere("a lista nao encheu (no maximo 4 deste endereco)", len(inventados) <= 4, len(inventados))
            confere("e os colegas que ja estavam continuam", {"colega-antes", "colega-depois"} <= vistos,
                    sorted(vistos))
            # O colega novo chega de OUTRO computador (o endereco da enxurrada
            # ficou com a cota cheia de proposito).
            gritar(marca, {"id": "colega-final", "apelido": "Final", "porta": 9003}, de="127.0.0.2")
            time.sleep(1.5)
            confere("e um colega novo ainda entra", "colega-final" in ids_na_lista(porta))
        finally:
            servidor_de_teste.derrubar(processo)
    finally:
        limpeza.apagar_pasta(pasta)

    print()
    if falhas:
        print("FALHOU: %d de %d" % (len(falhas), total[0]))
        return 1
    print("Descoberta com pacote torto: %d de %d certos." % (total[0], total[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
