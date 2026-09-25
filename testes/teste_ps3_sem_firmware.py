# -*- coding: utf-8 -*-
r"""Revisao pos-auditoria: jogo de PS3 sem o firmware no RPCS3.

Achado real (Borderlands 2): sem o firmware oficial do PS3, o RPCS3 desiste
em 1 s ("Missing Firmware") e o jogo so "pisca e fecha". Agora o /api/jogar
tem que recusar ANTES de abrir, com a frase que explica o que fazer, e sem
deixar o ARENA preso em "jogo em andamento". A aba Emuladores mostra
"incompleto".

Usa o servidor de verdade em processo (porta 8777). So roda se houver um
jogo de PS3 na pasta e o RPCS3 estiver sem firmware (a situacao real hoje);
se o firmware ja estiver instalado, avisa e sai.
"""
import importlib.util
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def pedir(caminho, corpo=None):
    dados = json.dumps(corpo).encode() if corpo is not None else None
    req = urllib.request.Request("http://127.0.0.1:8777" + caminho, data=dados,
                                 method="POST" if dados else "GET",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def main():
    sys.path.insert(0, os.path.join(RAIZ, "servidor"))
    spec = importlib.util.spec_from_file_location("arena_ps3", os.path.join(RAIZ, "servidor", "arena.py"))
    arena = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(arena)
    import graficos

    servidor = arena.Servidor(("127.0.0.1", 8777), arena.Manipulador)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    time.sleep(0.5)
    try:
        _, estado = pedir("/api/estado")
        ps3 = [e for e in estado.get("externos", []) if e["id"] == "ps3"]
        print("Aba Emuladores, PS3:", ps3)
        if not ps3 or not ps3[0]["instalado"] or not ps3[0]["falta"]:
            print("RPCS3 ausente ou com firmware: nada a testar aqui.")
            return 0
        _, catalogo = pedir("/api/catalogo")
        jogos = [j for j in catalogo.get("jogos", []) if j.get("plataforma") == "ps3"]
        if not jogos:
            print("Sem jogo de PS3 na pasta.")
            return 0
        status, resposta = pedir("/api/jogar", {"jogo_id": jogos[0]["id"]})
        print("Abrir %s: status %s -> %s" % (jogos[0]["titulo"], status, resposta.get("erro")))
        livre = not arena.JOGO_EM_ANDAMENTO["ativo"]
        print("ARENA continua livre para abrir outro jogo:", livre)
        ok = (status == 409 and "firmware" in resposta.get("erro", "") and livre)
        print("\nRESULTADO:", "PASSOU" if ok else "FALHOU")
        return 0 if ok else 1
    finally:
        servidor.shutdown()
        servidor.server_close()


if __name__ == "__main__":
    sys.exit(main())
