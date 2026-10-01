# -*- coding: utf-8 -*-
"""Testa a busca automatica de capa de ponta a ponta pela API real:
pede pra atualizar a capa do Sonic 3 (Mega Drive), confere que baixou de
verdade e que o catalogo passa a mostrar essa capa.

ATENCAO, corrigido em 01/10/2026: a versao anterior COMECAVA APAGANDO a
pasta retroarch\\thumbnails inteira (todas as capas baixadas pelo aluno) e
o dados\\manifesto.json, e apagava as capas de novo no fim. Agora mexe so
na capa do jogo testado: se ela ja existia, guarda uma copia e devolve no
fim; se nao existia, apaga so a que o teste baixou.

Roda: servidor\\python\\python.exe ferramentas\\teste_capa_online.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_MINIATURAS = os.path.join(RAIZ, "retroarch", "thumbnails")
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
import capas_online  # noqa: E402


def pedir(caminho, corpo=None, metodo="GET"):
    url = "http://127.0.0.1:8777%s" % caminho
    dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
    req = urllib.request.Request(url, data=dados, method=metodo,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    servidor_proc = subprocess.Popen(
        [os.path.join(RAIZ, "servidor", "python", "python.exe"),
         os.path.join(RAIZ, "servidor", "arena.py")],
        cwd=os.path.join(RAIZ, "servidor"), env=dict(os.environ, ARENA_SEM_JANELA="1"))
    print("Servidor ARENA rodando, PID", servidor_proc.pid)
    time.sleep(3)

    guarda = tempfile.mkdtemp(prefix="arena_capa_teste_")
    alvo = copia = None
    try:
        catalogo = pedir("/api/catalogo")
        # O Sonic 3 tem capa no banco (o "Sonic & Knuckles + Sonic 2", que
        # tambem esta na pasta, nao tem: o teste reprovaria a toa).
        sonics = [j for j in catalogo["jogos"] if "Sonic" in j["titulo"]
                  and j["plataforma"] in capas_online.REPO_POR_PLATAFORMA]
        jogo = next((j for j in sonics if "Hedgehog 3" in j["titulo"]), sonics[0] if sonics else None)
        if not jogo:
            print("Sem jogo do Sonic num console com banco de capas: nada a testar.")
            return 0
        # Onde a capa baixada vai parar (a mesma conta do capas_online).
        alvo = os.path.join(PASTA_MINIATURAS, jogo["plataforma"], "Named_Boxarts",
                            capas_online._limpar_nome_arquivo(jogo["titulo"]) + ".png")
        if os.path.isfile(alvo):
            copia = os.path.join(guarda, "capa_original.png")
            shutil.move(alvo, copia)        # so ESTA capa sai, e volta no fim
            pedir("/api/indexar", {}, "POST")

        for _ in range(15):
            estado = pedir("/api/estado")
            if estado.get("internet"):
                break
            time.sleep(2)
        else:
            print("AVISO: vigia nao confirmou internet em 30s - tentando mesmo assim.")

        resp = pedir("/api/capa/atualizar", {"jogo_id": jogo["id"]}, "POST")
        print("Resposta:", resp)
        if not resp.get("ok"):
            print("FALHOU ao atualizar a capa.")
            return 1
        if not os.path.isfile(alvo) or os.path.getsize(alvo) < 1000:
            print("FALHOU: arquivo da capa nao existe ou esta vazio de verdade.")
            return 1
        catalogo = pedir("/api/catalogo")
        jogo = next((j for j in catalogo["jogos"] if j["id"] == jogo["id"]), None)
        mostradas = " ".join(urllib.parse.unquote(u) for u in (jogo or {}).get("capa_urls") or [])
        if os.path.basename(alvo) not in mostradas:
            print("FALHOU: catalogo nao mostra a capa nova (%s)." % mostradas)
            return 1
        print("OK: capa baixada de verdade (%d bytes) e aparece no catalogo." % os.path.getsize(alvo))
        return 0
    finally:
        if alvo and os.path.isfile(alvo) and copia:
            os.remove(alvo)
        if copia and os.path.isfile(copia):
            shutil.move(copia, alvo)
        try:
            pedir("/api/indexar", {}, "POST")
        except Exception:
            pass
        servidor_proc.terminate()
        try:
            servidor_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            servidor_proc.kill()
        shutil.rmtree(guarda, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
