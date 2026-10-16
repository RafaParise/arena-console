# -*- coding: utf-8 -*-
r"""A descoberta de colegas so escuta a rede quando deve (achado de
15/10/2026).

Antes, o servidor escutava a porta da descoberta (UDP 55436, em todas as
redes) desde a abertura, mesmo com a rede fechada ("so este computador
acessa"). Por isso o Firewall do Windows perguntava pelo Python logo na
primeira vez, para quem nunca ia usar a rede. Agora a escuta abre so:
  - com a rede liberada (Aceitar conexoes da rede), ou
  - enquanto a janela do Jogar Junto procura partida
    (/api/partida/procurar?rede=1), e fecha 2 minutos depois.

Monta um ARENA isolado (so o servidor e uma pasta dados nova), com a porta
da descoberta trocada por uma de teste, e confere pelo netstat se ESTE
processo escuta a porta:
  1. rede fechada: a porta fica fechada;
  2. a janela do Jogar Junto procura partida (a rota de verdade): a porta
     abre, e o grito de um colega aparece na lista;
  3. a procura acaba: a porta fecha e a lista de colegas vistos se apaga;
  4. a rede liberada abre a porta, e fechada de novo, fecha.

Uso:
    servidor\python\python.exe testes\teste_descoberta_rede_fechada.py
"""
import importlib.util
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
import limpeza  # noqa: E402

PORTA_UDP_TESTE = 55497   # longe da 55436 de verdade: nao conversa com ARENA nenhum
PORTA_HTTP_TESTE = 8793


def montar_copia():
    destino = tempfile.mkdtemp(prefix="arena_descoberta_")
    shutil.copytree(os.path.join(RAIZ, "servidor"), os.path.join(destino, "servidor"),
                    ignore=shutil.ignore_patterns("__pycache__", "tests", "python"))
    os.makedirs(os.path.join(destino, "dados"))
    spec = importlib.util.spec_from_file_location("arena_descoberta",
                                                  os.path.join(destino, "servidor", "arena.py"))
    modulo = importlib.util.module_from_spec(spec)
    sys.modules["arena_descoberta"] = modulo
    sys.path.insert(0, os.path.join(destino, "servidor"))
    spec.loader.exec_module(modulo)
    sys.path.pop(0)
    modulo.PORTA = PORTA_HTTP_TESTE
    modulo.PORTA_DESCOBERTA = PORTA_UDP_TESTE
    modulo.preparar_banco()
    return destino, modulo


def escutando(porta):
    """ESTE processo escuta a porta UDP? (pelo netstat do Windows)"""
    saida = subprocess.run(["netstat", "-ano", "-p", "UDP"], capture_output=True, text=True).stdout
    for linha in saida.splitlines():
        partes = linha.split()
        if len(partes) >= 4 and partes[0] == "UDP" and partes[1].endswith(":%d" % porta) \
                and partes[-1] == str(os.getpid()):
            return True
    return False


def esperar(condicao, limite=8.0):
    fim = time.time() + limite
    while time.time() < fim:
        if condicao():
            return True
        time.sleep(0.25)
    return condicao()


def main():
    falhas = []

    def confere(nome, ok, detalhe=""):
        print("  %-6s %s%s" % ("ok" if ok else "FALHOU", nome, (" (%s)" % detalhe) if detalhe else ""))
        if not ok:
            falhas.append(nome)

    if escutando(PORTA_UDP_TESTE):
        print("A porta de teste %d ja esta aberta por este processo?" % PORTA_UDP_TESTE)
        return 1
    pasta, A = montar_copia()
    servidor = None
    try:
        cfg = A.carregar_config()
        cfg.update(apelido="Colega A", permitir_rede=False)
        A.salvar_config(cfg)
        servidor = A.Servidor(("127.0.0.1", PORTA_HTTP_TESTE), A.Manipulador)
        threading.Thread(target=servidor.serve_forever, daemon=True).start()
        threading.Thread(target=A.anunciar_e_escutar, daemon=True).start()

        print("1. Rede fechada", flush=True)
        time.sleep(3.0)
        confere("a porta da descoberta fica fechada", not escutando(PORTA_UDP_TESTE))

        print("2. A janela do Jogar Junto procura partida", flush=True)
        with urllib.request.urlopen("http://127.0.0.1:%d/api/partida/procurar?rede=1" % PORTA_HTTP_TESTE,
                                    timeout=15) as resposta:
            json.loads(resposta.read().decode("utf-8"))
        confere("a porta abre", esperar(lambda: escutando(PORTA_UDP_TESTE)))
        grito = A.MARCA_DESCOBERTA + json.dumps({"apelido": "Colega B", "id": "colega-b-teste",
                                                  "porta": 8794}).encode("utf-8")

        def colega_apareceu():
            falante = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                falante.sendto(grito, ("127.0.0.1", PORTA_UDP_TESTE))
            finally:
                falante.close()
            return any(c["apelido"] == "Colega B" for c in A.colegas_na_rede())

        confere("o grito de um colega aparece na lista", esperar(colega_apareceu))

        print("3. A procura acaba", flush=True)
        with A.TRAVA_VIZINHOS:
            A.PROCURA_DE_PARTIDA["ate"] = 0.0
        A.ESCUTA_MUDOU.set()
        confere("a porta fecha", esperar(lambda: not escutando(PORTA_UDP_TESTE)))
        confere("a lista de colegas vistos se apaga", not A.colegas_na_rede())

        print("4. A rede liberada e fechada de novo", flush=True)
        cfg = A.carregar_config()
        cfg["permitir_rede"] = True
        A.salvar_config(cfg)
        A.ESCUTA_MUDOU.set()
        confere("a rede liberada abre a porta", esperar(lambda: escutando(PORTA_UDP_TESTE)))
        cfg["permitir_rede"] = False
        A.salvar_config(cfg)
        A.ESCUTA_MUDOU.set()
        confere("a rede fechada fecha a porta", esperar(lambda: not escutando(PORTA_UDP_TESTE)))
    finally:
        A.VIGIA["encerrar"].set()
        A.ESCUTA_MUDOU.set()
        if servidor is not None:
            servidor.shutdown()
            servidor.server_close()
        try:
            A.fechar_banco()        # o banco aberto segurava a pasta dados
        except Exception:           # noqa: BLE001 -- so a limpeza do teste
            pass
        time.sleep(1.5)
        if not limpeza.apagar_pasta(pasta):
            print("Nao consegui apagar a pasta do teste: %s" % pasta)
    if falhas:
        print("\nFALHAS: %d" % len(falhas))
        return 1
    print("\nTudo certo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
