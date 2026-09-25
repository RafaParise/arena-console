r"""Fase 8 da auditoria: quantas gravacoes em disco o ARENA faz parado.

Pendencia da Fase 0 (a amostra de 15 s era curta demais para pegar um ciclo
do vigia). Sobe o ARENA, espera assentar e observa por JANELA_S segundos:

- contador de gravacoes do proprio processo (Win32_Process.WriteOperationCount
  e WriteTransferCount, que o Windows ja entrega sem instalar nada);
- quais arquivos de dados\ e backup\ mudaram de data nesse tempo.

A saida do servidor vai para o "nada" (DEVNULL), para que escrever na
janela preta nao conte como gravacao.

Uso:
    servidor\python\python.exe testes\medir_gravacoes_parado.py [segundos]
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON = os.path.join(RAIZ, "servidor", "python", "python.exe")
JANELA_S = int(sys.argv[1]) if len(sys.argv) > 1 else 600


def contadores(pid):
    saida = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
         "Get-CimInstance Win32_Process -Filter 'ProcessId=%d' | "
         "Select-Object WriteOperationCount, WriteTransferCount | ConvertTo-Json" % pid],
        capture_output=True, text=True, timeout=60).stdout
    dados = json.loads(saida)
    return int(dados["WriteOperationCount"]), int(dados["WriteTransferCount"])


def datas_dos_arquivos():
    datas = {}
    for pasta in ("dados", "backup"):
        for atual, _subs, arquivos in os.walk(os.path.join(RAIZ, pasta)):
            for nome in arquivos:
                caminho = os.path.join(atual, nome)
                try:
                    datas[os.path.relpath(caminho, RAIZ)] = os.path.getmtime(caminho)
                except OSError:
                    pass
    return datas


def principal():
    processo = subprocess.Popen([PYTHON, os.path.join(RAIZ, "servidor", "arena.py")], cwd=RAIZ,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(200):
            try:
                urllib.request.urlopen("http://127.0.0.1:8777/", timeout=0.5)
                break
            except Exception:
                time.sleep(0.1)
        print("Servidor no ar. Esperando 20 s para assentar...", flush=True)
        time.sleep(20)
        ops_antes, bytes_antes = contadores(processo.pid)
        datas_antes = datas_dos_arquivos()
        print("Observando por %d s sem ninguem usar..." % JANELA_S, flush=True)
        time.sleep(JANELA_S)
        ops_depois, bytes_depois = contadores(processo.pid)
        datas_depois = datas_dos_arquivos()
    finally:
        subprocess.run(["taskkill", "/PID", str(processo.pid), "/T", "/F"], capture_output=True)

    fator = 3600.0 / JANELA_S
    ops = ops_depois - ops_antes
    kb = (bytes_depois - bytes_antes) / 1024.0
    mudaram = sorted(c for c, d in datas_depois.items() if datas_antes.get(c) != d)
    resultado = {
        "janela_s": JANELA_S,
        "operacoes_de_gravacao": ops,
        "kb_gravados": round(kb, 1),
        "operacoes_por_hora": round(ops * fator),
        "kb_por_hora": round(kb * fator, 1),
        "arquivos_que_mudaram": mudaram,
    }
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    with open(os.path.join(RAIZ, "docs", "gravacoes_parado_bruto.json"), "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    principal()
