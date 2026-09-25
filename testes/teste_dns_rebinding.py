# -*- coding: utf-8 -*-
"""Fase 8: protecao contra DNS rebinding.

Como e' o ataque: um site faz o proprio nome (ex.: sitemalicioso.example)
passar a apontar para 127.0.0.1. O navegador acha que continua falando com
o mesmo site, entao deixa a pagina mandar pedidos "normais" (inclusive com
Content-Type application/json) e LER as respostas -- mas quem responde e'
o ARENA deste computador. O pedido chega vindo de 127.0.0.1, entao a trava
de rede da Fase 3 deixa passar. A unica pista e' o cabecalho Host, que
continua com o nome do site.

Confere, num ARENA isolado (copia temporaria):
  1. pedido local com Host estranho -> recusado (403), config intacta;
  2. pedido local com Host 127.0.0.1 / localhost -> funciona normal;
  3. pedido vindo de OUTRA maquina (simulado) com Host qualquer, numa rota
     da rede (ex.: /api/ranking) -> continua funcionando: rebinding so
     ataca o navegador deste computador, e amigo pela internet pode usar
     um nome (ex.: um endereco fixo) no lugar do IP.
"""
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def requisicao(porta, metodo, caminho, host, corpo=None):
    dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
    headers = {"Host": host}
    if dados is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request("http://127.0.0.1:%d%s" % (porta, caminho), data=dados,
                                 method=metodo, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code


def main():
    destino = tempfile.mkdtemp(prefix="arena_rebinding_")
    servidores = []
    try:
        for pasta in ("servidor", "dados", "launcher"):
            shutil.copytree(os.path.join(RAIZ, pasta), os.path.join(destino, pasta),
                            ignore=shutil.ignore_patterns("__pycache__", "tests"))
        # A copia herda o tema real do professor; com "escuro" ja escolhido,
        # o teste acusava falha sem invasao nenhuma (visto em 25/09/2026).
        # Fixa "claro" so NA COPIA; o dados\ real nao e' tocado.
        cfg_copia = os.path.join(destino, "dados", "config.json")
        cfg = json.load(open(cfg_copia, encoding="utf-8"))
        cfg["tema"] = "claro"
        json.dump(cfg, open(cfg_copia, "w", encoding="utf-8"), ensure_ascii=False)
        spec = importlib.util.spec_from_file_location(
            "arena_rebinding_teste", os.path.join(destino, "servidor", "arena.py"))
        arena = importlib.util.module_from_spec(spec)
        sys.path.insert(0, os.path.join(destino, "servidor"))
        spec.loader.exec_module(arena)

        class ManipuladorRemoto(arena.Manipulador):
            def pedido_e_local(self):
                return False

        for porta, classe in ((8777, arena.Manipulador), (8778, ManipuladorRemoto)):
            s = arena.Servidor(("127.0.0.1", porta), classe)
            threading.Thread(target=s.serve_forever, daemon=True).start()
            servidores.append(s)
        time.sleep(0.5)

        casos = [
            # (porta, metodo, caminho, host, corpo, deve_recusar, descricao)
            (8777, "POST", "/api/config", "sitemalicioso.example:8777", {"tema": "escuro"}, True,
             "local, Host de site estranho, muda config"),
            (8777, "GET", "/api/estado", "sitemalicioso.example:8777", None, True,
             "local, Host de site estranho, le estado"),
            (8777, "GET", "/api/estado", "127.0.0.1:8777", None, False, "local, Host 127.0.0.1"),
            (8777, "GET", "/api/estado", "localhost:8777", None, False, "local, Host localhost"),
            (8778, "GET", "/api/ranking", "meuarena.exemplo.org:8777", None, False,
             "outra maquina, rota da rede, Host com nome"),
        ]
        ok = True
        for porta, metodo, caminho, host, corpo, deve_recusar, descricao in casos:
            status = requisicao(porta, metodo, caminho, host, corpo)
            passou = (status == 403) == deve_recusar
            ok = ok and passou
            print("  %-45s status=%s %s" % (descricao, status, "OK" if passou else "ERRADO"))

        tema = json.load(open(os.path.join(destino, "dados", "config.json"), encoding="utf-8")).get("tema")
        print("\nTema continua o mesmo (a tentativa nao mudou nada):", tema != "escuro")
        ok = ok and tema != "escuro"
        print("\nRESULTADO:", "PASSOU" if ok else "FALHOU")
        return 0 if ok else 1
    finally:
        for s in servidores:
            s.shutdown()
            s.server_close()
        sys.path = [p for p in sys.path if not p.startswith(destino)]
        shutil.rmtree(destino, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
