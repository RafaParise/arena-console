# -*- coding: utf-8 -*-
r"""Auditoria 2 (extra): o diagnostico de lentidao pela API do ARENA.

Num servidor isolado (copia temporaria):
  1. GET /api/barreiras responde, no formato que a tela espera, em menos de
     20 s, e a segunda consulta vem do guardado (instantanea);
  2. a resposta NAO leva a lista de processos nem dado pessoal (nome de
     usuario, nome da maquina);
  3. POST /api/barreiras/fechar recusa programa fora da lista segura (e nao
     fecha nada), e recusa texto estranho;
  4. vindo de OUTRA maquina da rede, as duas rotas sao recusadas (403).
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


def pedir(porta, caminho, corpo=None, limite=60):
    dados = json.dumps(corpo).encode() if corpo is not None else None
    req = urllib.request.Request("http://127.0.0.1:%d%s" % (porta, caminho), data=dados,
                                 method="POST" if dados else "GET",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=limite) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def main():
    destino = tempfile.mkdtemp(prefix="arena_barreiras_api_")
    servidores = []
    try:
        for pasta in ("servidor", "dados", "launcher"):
            shutil.copytree(os.path.join(RAIZ, pasta), os.path.join(destino, pasta),
                            ignore=shutil.ignore_patterns("__pycache__", "tests", "python", "*.log"))
        sys.path.insert(0, os.path.join(destino, "servidor"))
        spec = importlib.util.spec_from_file_location("arena_barr", os.path.join(destino, "servidor", "arena.py"))
        arena = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(arena)

        class Remoto(arena.Manipulador):
            def pedido_e_local(self):
                return False

        for porta, classe in ((8777, arena.Manipulador), (8778, Remoto)):
            s = arena.Servidor(("127.0.0.1", porta), classe)
            threading.Thread(target=s.serve_forever, daemon=True).start()
            servidores.append(s)
        time.sleep(0.5)
        ok = True

        t = time.perf_counter()
        status, r = pedir(8777, "/api/barreiras?forcar=1")
        primeira = time.perf_counter() - t
        formato = (status == 200 and isinstance(r.get("barreiras"), list)
                   and all({"id", "gravidade", "titulo", "achado", "por_que", "acao", "quem"} <= set(b)
                           for b in r["barreiras"]))
        print("1. %d barreira(s) em %.1f s, formato certo: %s" % (len(r.get("barreiras", [])), primeira, formato))
        t = time.perf_counter()
        pedir(8777, "/api/barreiras")
        segunda = time.perf_counter() - t
        print("   segunda consulta (guardada): %.3f s" % segunda)
        ok = ok and formato and primeira < 20 and segunda < 1

        texto = json.dumps(r, ensure_ascii=False).lower()
        pessoais = [v for v in (os.environ.get("USERNAME"), os.environ.get("COMPUTERNAME")) if v]
        vazou = [v for v in pessoais if v.lower() in texto]
        sem_processos = "processos" not in r and "fatos" not in r
        print("2. sem lista de processos: %s; dado pessoal vazado: %s" % (sem_processos, vazou or "nenhum"))
        ok = ok and sem_processos and not vazou

        for programa in ("notepad", "explorer", "../../x", "", None):
            status, resposta = pedir(8777, "/api/barreiras/fechar", {"programa": programa})
            recusou = status == 400 and bool(resposta.get("erro"))
            ok = ok and recusou
        print("3. fechar programa fora da lista: recusado nos 5 casos:", ok)

        s1, _ = pedir(8778, "/api/barreiras")
        s2, _ = pedir(8778, "/api/barreiras/fechar", {"programa": "onedrive"})
        print("4. de outra maquina: GET %d, fechar %d (esperado 403 e 403)" % (s1, s2))
        ok = ok and s1 == 403 and s2 == 403

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
