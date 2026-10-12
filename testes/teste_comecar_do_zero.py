# -*- coding: utf-8 -*-
r"""'Comecar do zero' so apaga depois de uma copia de seguranca que deu certo.

Achado da auditoria 1 (Fase 1, achado #4): se a copia de seguranca falhasse
(pen drive cheio, pasta de backup que nao da para criar), /api/perfil/novo
apagava o perfil do aluno do mesmo jeito, sem copia nenhuma. O conserto
cancela o apagamento.

Era ferramentas\teste_backup_falha_cancela_apagamento.py, trazido para ca na
auditoria 3 (Fase 1): o antigo subia o servidor na porta 8777 de verdade (a
do ARENA aberto) e trocava a funcao da copia por uma que sempre falha. Aqui
o ARENA e' uma copia isolada numa pasta temporaria, numa porta livre, e a
copia falha do jeito que falha na escola: no lugar da pasta backup ha um
ARQUIVO com esse nome, e a pasta nao pode ser criada.

Confere:
  1. sem confirmar: nada e' apagado;
  2. copia de seguranca que falha: erro claro ("Nada foi apagado") e os
     arquivos do perfil continuam iguais, byte a byte;
  3. copia que funciona: apaga, e a copia guardada tem o config.json de antes.
Nada disto toca no dados\ de verdade (a copia leva o dados\ junto).

Uso: servidor\python\python.exe testes\teste_comecar_do_zero.py
"""
import hashlib
import json
import os
import socket
import sys
import tempfile
import urllib.error
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import limpeza  # noqa: E402
import teste_servidor_que_cai as servidor_de_teste  # noqa: E402

PERFIL = ("arena.db", "config.json", "controles.json")


def porta_livre():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def pedir(porta, caminho, corpo):
    """POST com a resposta de erro inteira (o pedir do ajudante a descarta)."""
    req = urllib.request.Request("http://127.0.0.1:%d%s" % (porta, caminho),
                                 data=json.dumps(corpo).encode("utf-8"), method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resposta:
            return resposta.status, json.loads(resposta.read() or b"{}")
    except urllib.error.HTTPError as erro:
        try:
            return erro.code, json.loads(erro.read() or b"{}")
        except ValueError:
            return erro.code, {}
    except (OSError, ValueError):
        return None, {}


def marcas(pasta_dados):
    saida = {}
    for nome in PERFIL:
        caminho = os.path.join(pasta_dados, nome)
        if os.path.isfile(caminho):
            with open(caminho, "rb") as arquivo:
                saida[nome] = hashlib.sha256(arquivo.read()).hexdigest()
        else:
            saida[nome] = None
    return saida


def main():
    falhas, total = [], [0]

    def confere(nome, ok, detalhe=""):
        total[0] += 1
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, "" if ok else detalhe), flush=True)
        if not ok:
            falhas.append(nome)

    base = tempfile.mkdtemp(prefix="arena_comecar_do_zero_")
    processo = None
    try:
        copia = os.path.join(base, "ARENA")
        servidor_de_teste.preparar_copia(copia)
        dados = os.path.join(copia, "dados")
        # O perfil inteiro existe na copia (o computador de quem roda o
        # teste pode nao ter o controles.json).
        caminho_controles = os.path.join(dados, "controles.json")
        if not os.path.isfile(caminho_controles):
            with open(caminho_controles, "w", encoding="utf-8") as arquivo:
                json.dump({"jogadores": {}}, arquivo)
        # A copia de seguranca vai falhar: um ARQUIVO com o nome da pasta.
        bloqueio = os.path.join(copia, "backup")
        if os.path.isdir(bloqueio):
            limpeza.apagar_pasta(bloqueio)
        with open(bloqueio, "w", encoding="utf-8") as arquivo:
            arquivo.write("no lugar da pasta backup, de proposito (teste)")

        porta = porta_livre()
        processo = servidor_de_teste.subir(copia, porta, False, os.path.join(base, "sem-trava"))
        if not servidor_de_teste.esperar_servidor(porta):
            print("FALHOU: o servidor da copia nao abriu.")
            return 1
        antes = marcas(dados)
        print("Perfil na copia:", {k: (v[:8] if v else None) for k, v in antes.items()})

        print("1. Sem confirmar")
        status, resposta = pedir(porta, "/api/perfil/novo", {})
        confere("recusa", status == 400, (status, resposta))
        confere("e nada mudou", marcas(dados) == antes)

        print("2. A copia de seguranca falha")
        status, resposta = pedir(porta, "/api/perfil/novo", {"confirmar": "sim"})
        confere("responde erro", status == 500, (status, resposta))
        confere("e diz que nada foi apagado", "Nada foi apagado" in str(resposta.get("erro", "")), resposta)
        confere("os arquivos do perfil continuam iguais, byte a byte", marcas(dados) == antes, marcas(dados))

        print("3. A copia de seguranca funciona")
        os.remove(bloqueio)
        status, resposta = pedir(porta, "/api/perfil/novo", {"confirmar": "sim"})
        confere("apaga", status == 200 and resposta.get("ok") is True and resposta.get("apagados", 0) >= 3,
                (status, resposta))
        confere("o controles.json saiu", not os.path.isfile(caminho_controles))
        copias = [os.path.join(bloqueio, d) for d in os.listdir(bloqueio)] if os.path.isdir(bloqueio) else []
        guardado = next((os.path.join(c, "config.json") for c in copias
                         if os.path.isfile(os.path.join(c, "config.json"))), None)
        if guardado:
            with open(guardado, "rb") as arquivo:
                marca_guardada = hashlib.sha256(arquivo.read()).hexdigest()
        else:
            marca_guardada = None
        confere("e a copia guardada tem o config.json de antes", marca_guardada == antes["config.json"],
                (copias, marca_guardada))
    finally:
        if processo:
            servidor_de_teste.derrubar(processo)
        limpeza.apagar_pasta(base)

    print()
    if falhas:
        print("FALHOU: %d de %d" % (len(falhas), total[0]))
        return 1
    print("Comecar do zero: %d de %d certos." % (total[0], total[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
