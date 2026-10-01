# -*- coding: utf-8 -*-
"""Fase 4: descoberta de colegas com muitos aparelhos -- simula 30
computadores anunciando ao mesmo tempo (mesmo formato de pacote que
anunciar_e_escutar() espera) e confere que a lista em /api/colegas
continua clara e o processador do ARENA continua baixo.
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

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORTA_DESCOBERTA = 55436
MARCA_DESCOBERTA = b"ARENA1"
N_MAQUINAS = 30


def powershell(comando):
    r = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", comando],
                       capture_output=True, text=True, timeout=15)
    return r.stdout.strip()


def medir_cpu(pid, janela_s=8.0):
    def cpu_agora():
        saida = powershell("(Get-Process -Id %d -ErrorAction SilentlyContinue).CPU" % pid)
        try:
            return float(saida.replace(",", "."))
        except ValueError:
            return None
    antes = cpu_agora()
    t0 = time.monotonic()
    time.sleep(janela_s)
    depois = cpu_agora()
    t1 = time.monotonic()
    if antes is None or depois is None:
        return None
    ncpu = int(powershell("(Get-CimInstance Win32_ComputerSystem).NumberOfLogicalProcessors") or 1)
    return 100.0 * (depois - antes) / (t1 - t0) / ncpu


def anunciar_maquina_falsa(indice, porta_ouvinte):
    # O proprio "sou eu?" do ARENA (mesma porta 8777 + mesmo IP = provavel
    # eco de mim mesmo) filtraria 30 pacotes vindos deste MESMO computador
    # com a porta 8777 -- de proposito, e' o que evita a maquina se listar
    # como colega dela mesma. Pra simular 30 maquinas DE VERDADE (cada uma
    # com seu proprio IP), a porta declarada varia por pacote -- assim
    # nenhum bate com a porta real do ARENA (8777) e o filtro "sou eu?"
    # nao os descarta, testando o que interessa aqui: a LISTA com 30
    # entradas, nao o transporte UDP em si (que ja e' testado pelo uso
    # real, entre maquinas de verdade).
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    recado = json.dumps({
        "apelido": "Aluno%02d" % indice,
        "id": "maquinafalsa%02d" % indice,
        "porta": 20000 + indice,
    }, ensure_ascii=False).encode("utf-8")
    s.sendto(MARCA_DESCOBERTA + recado, ("127.0.0.1", porta_ouvinte))
    s.close()


def main():
    destino = tempfile.mkdtemp(prefix="arena_descoberta30_")
    print("Pasta de teste:", destino)
    try:
        for pasta in ("servidor", "dados", "launcher"):
            shutil.copytree(os.path.join(RAIZ, pasta), os.path.join(destino, pasta),
                            ignore=shutil.ignore_patterns("__pycache__", "tests"))

        # liga permitir_rede na copia isolada, senao o proprio anunciar
        # nao dispara (e nao precisamos dele disparando pra este teste --
        # so precisamos do lado que ESCUTA, mas ligar deixa o cenario mais
        # realista sem custo)
        caminho_config = os.path.join(destino, "dados", "config.json")
        cfg = json.load(open(caminho_config, encoding="utf-8"))
        cfg["permitir_rede"] = True
        json.dump(cfg, open(caminho_config, "w", encoding="utf-8"))

        processo = subprocess.Popen(
            [os.path.join(RAIZ, "servidor", "python", "python.exe"),
             os.path.join(destino, "servidor", "arena.py")],
            cwd=destino, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            env=dict(os.environ, ARENA_SEM_JANELA="1"))
        # Espera o ARENA responder de verdade (antes: 2 s fixos). Achado de
        # 01/10/2026: com a maquina ocupada (rodada completa), o ARENA ainda
        # nao escutava quando a rajada saiu, e so 14 de 30 chegavam.
        for _ in range(150):
            try:
                urllib.request.urlopen("http://127.0.0.1:8777/api/estado", timeout=2).read()
                break
            except OSError:
                time.sleep(0.2)

        print("Disparando %d maquinas falsas anunciando (3 vezes, como na sala:"
              " cada ARENA repete o anuncio a cada 5 s)..." % N_MAQUINAS)
        for _rodada in range(3):
            threads = [threading.Thread(target=anunciar_maquina_falsa, args=(i, PORTA_DESCOBERTA))
                       for i in range(N_MAQUINAS)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            time.sleep(1.0)

        print("Esperando o ARENA processar e medindo CPU por 8s...")
        cpu_pct = medir_cpu(processo.pid, 8.0)

        t0 = time.monotonic()
        with urllib.request.urlopen("http://127.0.0.1:8777/api/colegas", timeout=5) as resp:
            colegas = json.loads(resp.read())
        tempo_resposta = time.monotonic() - t0

        vistos = colegas.get("colegas", colegas if isinstance(colegas, list) else [])
        print("\nColegas vistos:", len(vistos))
        print("Tempo de resposta de /api/colegas:", round(tempo_resposta, 3), "s")
        print("CPU do servidor durante/depois da rajada: %s%%" % (round(cpu_pct, 2) if cpu_pct is not None else "?"))

        # confere que a lista tem nomes/apelidos claros, nao lixo
        nomes_ok = all(isinstance(c, dict) and c.get("apelido", "").startswith("Aluno") for c in vistos[:5]) if vistos else False
        print("Primeiros nomes parecem corretos:", nomes_ok)
        if vistos:
            print("Exemplo:", vistos[0])

        processo.terminate()
        try:
            processo.wait(timeout=10)
        except subprocess.TimeoutExpired:
            processo.kill()

        ok = (len(vistos) >= N_MAQUINAS * 0.8 and tempo_resposta < 2.0
             and (cpu_pct is None or cpu_pct < 30.0))
        print("\nRESULTADO:", "PASSOU" if ok else "FALHOU (ou precisa olhar os numeros)")
        return 0 if ok else 1
    finally:
        sys.path = [p for p in sys.path if not p.startswith(destino)]
        shutil.rmtree(destino, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
