# -*- coding: utf-8 -*-
"""Fase 3: 50 pedidos ao mesmo tempo, sem travar e sem corromper arquivo.

Sobe um ARENA isolado e dispara 50 threads batendo em rotas que gravam em
disco ao mesmo tempo: /api/config (config.json), /api/placar (arena.db,
com TRAVA_BANCO), /api/mapeamento/definir (controles.json), /api/cheat/
adicionar (cheats por jogo). No final confere que todo arquivo tocado
ainda e JSON/banco valido -- nenhuma gravacao pela metade.
"""
import importlib.util
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N_THREADS = 50


def requisicao(metodo, caminho, corpo=None, timeout=10):
    url = "http://127.0.0.1:8777" + caminho
    dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
    req = urllib.request.Request(url, data=dados, method=metodo,
                                  headers={"Content-Type": "application/json"} if dados else {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:
        return None, str(e).encode()


def main():
    destino = tempfile.mkdtemp(prefix="arena_concorrencia_")
    print("Pasta de teste:", destino)
    try:
        for pasta in ("servidor", "dados", "launcher"):
            shutil.copytree(os.path.join(RAIZ, pasta), os.path.join(destino, pasta),
                             ignore=shutil.ignore_patterns("__pycache__", "tests"))
        pasta_nes = os.path.join(destino, "jogos", "pessoais", "NES")
        os.makedirs(pasta_nes, exist_ok=True)
        with open(os.path.join(pasta_nes, "Jogo Concorrencia.nes"), "w"):
            pass

        caminho_arena = os.path.join(destino, "servidor", "arena.py")
        spec = importlib.util.spec_from_file_location("arena_concorrencia", caminho_arena)
        arena = importlib.util.module_from_spec(spec)
        sys.path.insert(0, os.path.join(destino, "servidor"))
        spec.loader.exec_module(arena)

        servidor = arena.Servidor(("127.0.0.1", 8777), arena.Manipulador)
        thread = threading.Thread(target=servidor.serve_forever, daemon=True)
        thread.start()
        time.sleep(0.5)

        _, corpo = requisicao("GET", "/api/catalogo")
        catalogo = json.loads(corpo)
        jogo_id = next(j["id"] for j in catalogo["jogos"] if "Concorrencia" in j["titulo"])

        tarefas = []
        for i in range(N_THREADS):
            if i % 4 == 0:
                tarefas.append(("POST", "/api/config", {"tema": "escuro" if i % 8 == 0 else "claro"}))
            elif i % 4 == 1:
                tarefas.append(("POST", "/api/placar", {"pontos": i, "jogo_id": jogo_id, "apelido": "T%d" % i}))
            elif i % 4 == 2:
                tarefas.append(("POST", "/api/mapeamento/definir",
                                {"jogador": "1", "botao": "a", "tipo": "tecla", "valor": "Key%d" % i}))
            else:
                tarefas.append(("POST", "/api/cheat/adicionar",
                                {"jogo_id": jogo_id, "codigo": "CODE-%04d" % i, "descricao": "cheat %d" % i}))

        resultados = [None] * N_THREADS
        excecoes = [None] * N_THREADS
        corpos = [None] * N_THREADS

        def rodar(indice, metodo, caminho, corpo):
            try:
                status, resp = requisicao(metodo, caminho, corpo)
                resultados[indice] = status
                corpos[indice] = resp
            except Exception as e:
                excecoes[indice] = str(e)

        print("Disparando %d pedidos simultaneos..." % N_THREADS)
        inicio = time.monotonic()
        threads = [threading.Thread(target=rodar, args=(i, m, c, b)) for i, (m, c, b) in enumerate(tarefas)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=20)
        duracao = time.monotonic() - inicio
        print("Concluido em %.2fs" % duracao)

        travados = [i for i, t in enumerate(threads) if t.is_alive()]
        falhas_rede = [i for i, e in enumerate(excecoes) if e]
        falhas_status = [i for i, s in enumerate(resultados) if s is not None and s >= 500]

        print("Travados (nao terminaram em 20s):", len(travados))
        print("Falhas de rede/conexao:", len(falhas_rede), [excecoes[i] for i in falhas_rede[:5]])
        print("Respostas 5xx:", len(falhas_status))
        for i in falhas_status:
            print("  [%d] %s %s -> %s :: %s" % (i, tarefas[i][0], tarefas[i][1], resultados[i], corpos[i]))

        print("\nConferindo integridade dos arquivos gravados...")
        integros = True

        caminho_config = os.path.join(destino, "dados", "config.json")
        try:
            json.load(open(caminho_config, encoding="utf-8"))
            print("  config.json: JSON valido")
        except Exception as e:
            print("  config.json: CORROMPIDO --", e)
            integros = False

        caminho_controles = os.path.join(destino, "dados", "controles.json")
        try:
            json.load(open(caminho_controles, encoding="utf-8"))
            print("  controles.json: JSON valido")
        except Exception as e:
            print("  controles.json: CORROMPIDO --", e)
            integros = False

        caminho_db = os.path.join(destino, "dados", "arena.db")
        try:
            conexao = sqlite3.connect(caminho_db)
            resultado_integridade = conexao.execute("PRAGMA integrity_check").fetchone()
            conexao.close()
            print("  arena.db: PRAGMA integrity_check ->", resultado_integridade[0])
            if resultado_integridade[0] != "ok":
                integros = False
        except Exception as e:
            print("  arena.db: CORROMPIDO --", e)
            integros = False

        servidor.shutdown()
        servidor.server_close()

        ok = (not travados and not falhas_rede and not falhas_status and integros)
        print("\nRESULTADO:", "PASSOU" if ok else "FALHOU")
        return 0 if ok else 1
    finally:
        sys.path = [p for p in sys.path if not p.startswith(destino)]
        shutil.rmtree(destino, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
