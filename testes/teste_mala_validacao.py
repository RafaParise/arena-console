# -*- coding: utf-8 -*-
"""Fase 3: confere a correcao do /api/mala -- achado real de escrita em
caminho arbitrario (nenhuma validacao antes). Agora so aceita 'caminho'
se o nome do arquivo for exatamente ARENA-troca.json; qualquer outro nome
e recusado, mas a mala continua podendo apontar pra RAIZ de qualquer
midia (pen drive), que e o uso de verdade.
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


def requisicao_post(caminho, corpo):
    dados = json.dumps(corpo).encode("utf-8")
    req = urllib.request.Request("http://127.0.0.1:8777" + caminho, data=dados,
                                  method="POST", headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def main():
    # O ARENA de teste numa SUBPASTA: sem caminho (caso 3), a mala vai para
    # a pasta de cima -- a raiz do pen drive. Com o ARENA direto no
    # temporario, a mala ficava solta no Temp do Windows a cada rodada
    # (achado da auditoria 3, 08/10/2026).
    raiz_temporaria = tempfile.mkdtemp(prefix="arena_mala_")
    destino = os.path.join(raiz_temporaria, "ARENA")
    os.makedirs(destino)
    try:
        for pasta in ("servidor", "dados", "launcher"):
            shutil.copytree(os.path.join(RAIZ, pasta), os.path.join(destino, pasta),
                             ignore=shutil.ignore_patterns("__pycache__", "tests"))

        caminho_arena = os.path.join(destino, "servidor", "arena.py")
        spec = importlib.util.spec_from_file_location("arena_mala", caminho_arena)
        arena = importlib.util.module_from_spec(spec)
        sys.path.insert(0, os.path.join(destino, "servidor"))
        spec.loader.exec_module(arena)

        servidor = arena.Servidor(("127.0.0.1", 8777), arena.Manipulador)
        thread = threading.Thread(target=servidor.serve_forever, daemon=True)
        thread.start()
        time.sleep(0.5)

        # Caso 1: nome de arquivo arbitrario (o ataque original) -- tem que
        # ser recusado, e o arquivo nao pode ser criado.
        alvo_malicioso = os.path.join(destino, "arquivo_malicioso.json")
        status, resp = requisicao_post("/api/mala", {"caminho": alvo_malicioso})
        caso1_ok = (not resp.get("ok")) and not os.path.isfile(alvo_malicioso)
        print("Caso 1 (nome arbitrario) -- status=%s resp=%s arquivo_criado=%s"
              % (status, resp, os.path.isfile(alvo_malicioso)))

        # Caso 2: nome CORRETO (ARENA-troca.json), mas numa pasta que simula
        # a raiz de outro pen drive -- tem que continuar funcionando.
        pasta_pendrive = os.path.join(destino, "pendrive_simulado")
        os.makedirs(pasta_pendrive, exist_ok=True)
        alvo_legitimo = os.path.join(pasta_pendrive, "ARENA-troca.json")
        status2, resp2 = requisicao_post("/api/mala", {"caminho": alvo_legitimo})
        caso2_ok = resp2.get("ok") and os.path.isfile(alvo_legitimo)
        print("Caso 2 (nome correto, pasta diferente) -- status=%s resp=%s arquivo_criado=%s"
              % (status2, resp2, os.path.isfile(alvo_legitimo)))

        # Caso 3: sem 'caminho' nenhum -- continua usando o padrao.
        status3, resp3 = requisicao_post("/api/mala", {})
        mala_padrao = os.path.join(raiz_temporaria, "ARENA-troca.json")
        caso3_ok = resp3.get("ok") and os.path.isfile(mala_padrao)
        print("Caso 3 (sem caminho, usa o padrao, ao lado da pasta do ARENA) -- status=%s resp=%s "
              "arquivo_criado=%s" % (status3, resp3, os.path.isfile(mala_padrao)))

        servidor.shutdown()
        servidor.server_close()

        ok = caso1_ok and caso2_ok and caso3_ok
        print("\nRESULTADO:", "PASSOU" if ok else "FALHOU")
        return 0 if ok else 1
    finally:
        sys.path = [p for p in sys.path if not p.startswith(destino)]
        shutil.rmtree(raiz_temporaria, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
