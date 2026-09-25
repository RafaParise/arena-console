# -*- coding: utf-8 -*-
r"""Revisao pos-auditoria (aprovado pelo Rafael): "Aceitar conexoes da rede"
vale NA HORA, sem fechar e abrir o ARENA.

Roda o ARENA de verdade (principal(), igual ao ARENA.bat) numa copia isolada
de servidor\dados\launcher, com o MESMO python.exe da pasta (o Firewall do
Windows guarda permissao por programa; outro python.exe faria aparecer a
caixa de permissao na tela). Confere pelo proprio Windows (Get-NetTCPConnection)
em que endereco a porta 8777 escuta:
  1. chave desligada -> 127.0.0.1 (so este computador);
  2. liga pela API -> em ~1 s passa a 0.0.0.0 (rede inteira), sem reabrir;
  3. desliga -> volta a 127.0.0.1;
  4. a tela continua respondendo o tempo todo, e liga/desliga 5 vezes
     seguidas sem travar.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON = os.path.join(RAIZ, "servidor", "python", "python.exe")


def escuta(pid):
    saida = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
         "Get-NetTCPConnection -LocalPort 8777 -State Listen -ErrorAction SilentlyContinue | "
         "Where-Object OwningProcess -eq %d | ForEach-Object LocalAddress" % pid],
        capture_output=True, text=True, timeout=30).stdout.split()
    return sorted(set(saida))


def pedir(caminho, corpo=None, tentativas=20):
    for _ in range(tentativas):
        try:
            dados = json.dumps(corpo).encode() if corpo is not None else None
            req = urllib.request.Request("http://127.0.0.1:8777" + caminho, data=dados,
                                         method="POST" if dados else "GET",
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=5) as r:
                return json.loads(r.read())
        except (urllib.error.URLError, ConnectionError):
            time.sleep(0.25)
    raise RuntimeError("servidor nao respondeu em %s" % caminho)


def esperar_escuta(pid, esperado, limite=5.0):
    fim = time.time() + limite
    while time.time() < fim:
        atual = escuta(pid)
        if atual == esperado:
            return atual
        time.sleep(0.3)
    return escuta(pid)


def main():
    destino = tempfile.mkdtemp(prefix="arena_rede_viva_")
    processo = None
    try:
        for pasta in ("servidor", "dados", "launcher"):
            shutil.copytree(os.path.join(RAIZ, pasta), os.path.join(destino, pasta),
                            ignore=shutil.ignore_patterns("__pycache__", "tests", "python", "*.log"))
        cfg = os.path.join(destino, "dados", "config.json")
        dados_cfg = json.load(open(cfg, encoding="utf-8"))
        dados_cfg["permitir_rede"] = False
        json.dump(dados_cfg, open(cfg, "w", encoding="utf-8"), ensure_ascii=False)

        processo = subprocess.Popen([PYTHON, os.path.join(destino, "servidor", "arena.py")],
                                    cwd=destino, stdin=subprocess.DEVNULL,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        pedir("/api/estado", tentativas=80)
        ok = True

        inicio = esperar_escuta(processo.pid, ["127.0.0.1"])
        print("1. Chave desligada, escuta em:", inicio)
        ok = ok and inicio == ["127.0.0.1"]

        resp = pedir("/api/config", {"permitir_rede": True})
        t0 = time.time()
        ligada = esperar_escuta(processo.pid, ["0.0.0.0"])
        print("2. Ligou pela API (rede_aplicada=%s): escuta em %s depois de %.1f s"
              % (resp.get("rede_aplicada"), ligada, time.time() - t0))
        ok = ok and resp.get("rede_aplicada") is True and ligada == ["0.0.0.0"]
        ok = ok and pedir("/api/estado")["config"]["permitir_rede"] is True

        pedir("/api/config", {"permitir_rede": False})
        desligada = esperar_escuta(processo.pid, ["127.0.0.1"])
        print("3. Desligou: escuta em", desligada)
        ok = ok and desligada == ["127.0.0.1"]

        for i in range(5):
            pedir("/api/config", {"permitir_rede": i % 2 == 0})
            pedir("/api/estado")
        final = esperar_escuta(processo.pid, ["0.0.0.0"])
        vivo = processo.poll() is None
        print("4. Liga/desliga 5 vezes seguidas: vivo=%s, escuta final %s (esperado 0.0.0.0)"
              % (vivo, final))
        ok = ok and vivo and final == ["0.0.0.0"]

        # 5. Cliques colados (sem esperar resposta nenhuma entre eles): o
        # caso da corrida. O ARENA nao pode fechar, e vale o ULTIMO clique.
        for i in range(12):
            pedir("/api/config", {"permitir_rede": i % 2 == 1})
        time.sleep(3)
        vivo = processo.poll() is None
        colados = esperar_escuta(processo.pid, ["0.0.0.0"])
        print("5. 12 cliques colados: vivo=%s, escuta %s (ultimo clique = ligar)" % (vivo, colados))
        ok = ok and vivo and colados == ["0.0.0.0"]

        print("\nRESULTADO:", "PASSOU" if ok else "FALHOU")
        return 0 if ok else 1
    finally:
        if processo:
            subprocess.run(["taskkill", "/PID", str(processo.pid), "/T", "/F"], capture_output=True)
            try:
                processo.communicate(timeout=10)
            except Exception:
                pass
        time.sleep(1)
        shutil.rmtree(destino, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
