# -*- coding: utf-8 -*-
"""Fase 6: dados\\config.json marcado como somente-leitura (Windows) --
confere que o ARENA nao trava com traceback cru; deve dar erro claro ao
tentar gravar, sem derrubar o servidor inteiro.

Nota: 'attrib +R' numa PASTA no Windows nao bloqueia gravar arquivo novo
dentro dela (e' so cosmetico pro Explorer) -- quem bloqueia de verdade e'
o atributo +R num ARQUIVO especifico. Por isso o teste marca o proprio
config.json, nao a pasta dados\\ inteira.
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
sys.path.insert(0, os.path.join(RAIZ, "testes"))
import limpeza  # noqa: E402


def main():
    destino = tempfile.mkdtemp(prefix="arena_ro_")
    print("Pasta de teste:", destino)
    try:
        for pasta in ("servidor", "dados", "launcher"):
            shutil.copytree(os.path.join(RAIZ, pasta), os.path.join(destino, pasta),
                            ignore=shutil.ignore_patterns("__pycache__", "tests"))

        arquivo_config = os.path.join(destino, "dados", "config.json")
        print("Marcando config.json como somente-leitura (attrib +R)...")
        subprocess.run(["attrib", "+R", arquivo_config], shell=True, capture_output=True)

        processo = subprocess.Popen(
            [os.path.join(RAIZ, "servidor", "python", "python.exe"),
             os.path.join(destino, "servidor", "arena.py")],
            cwd=destino, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        subiu = False
        for _ in range(40):
            try:
                with urllib.request.urlopen("http://127.0.0.1:8777/api/estado", timeout=1):
                    subiu = True
                    break
            except Exception:
                time.sleep(0.3)
        print("ARENA subiu com dados\\ somente-leitura:", subiu)

        # tenta gravar uma config -- tem que dar erro CLARO, nao 500 cru
        status = None
        if subiu:
            corpo = json.dumps({"tema": "escuro"}).encode("utf-8")
            req = urllib.request.Request("http://127.0.0.1:8777/api/config", data=corpo,
                                        method="POST", headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=5) as resp:
                    status = resp.status
                    corpo_resp = json.loads(resp.read())
            except urllib.error.HTTPError as e:
                status = e.code
                corpo_resp = json.loads(e.read())
            print("Status ao tentar gravar config:", status, "| resposta:", corpo_resp)

        processo.terminate()
        try:
            saida, _ = processo.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            processo.kill()
            saida, _ = processo.communicate()

        vazou_traceback = "Traceback (most recent call last)" in saida
        print("Vazou traceback no console (nao deveria):", vazou_traceback)

        subprocess.run(["attrib", "-R", arquivo_config], shell=True, capture_output=True)

        ok = subiu and not vazou_traceback and (status is None or status < 500 or (status >= 500 and corpo_resp.get("erro")))
        print("\nRESULTADO:", "PASSOU" if ok else "FALHOU")
        return 0 if ok else 1
    finally:
        subprocess.run(["attrib", "-R", os.path.join(destino, "dados", "config.json")], shell=True, capture_output=True)
        # shutil.rmtree calado desistia de arquivo somente leitura ou preso (a rodada da auditoria 3 achava esta pasta no Temp).
        limpeza.apagar_pasta(destino)


if __name__ == "__main__":
    sys.exit(main())
