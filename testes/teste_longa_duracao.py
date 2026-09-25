# -*- coding: utf-8 -*-
"""Fase 3: teste de longa duracao acelerado.

'Horas' de verdade nao cabem numa sessao de auditoria -- este teste
acelera: milhares de pedidos num intervalo curto (poucos minutos), muitos
deles gravando em disco (como abrir e fechar jogo faria), medindo RAM e
arquivos abertos do processo a cada amostra. Se a linha de RAM/handles
sobe sem parar, e vazamento; se estabiliza depois do aquecimento inicial
do Python (normal, e o GC se ajustando), esta ok.
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DURACAO_S = float(sys.argv[1]) if len(sys.argv) > 1 else 180.0
AMOSTRA_A_CADA_S = 10.0


def requisicao(metodo, caminho, corpo=None, timeout=5):
    dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
    req = urllib.request.Request("http://127.0.0.1:8777" + caminho, data=dados, method=metodo,
                                  headers={"Content-Type": "application/json"} if dados else {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return None


def powershell(comando):
    resultado = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", comando],
        capture_output=True, text=True, timeout=30)
    return resultado.stdout.strip()


def medir_processo(pid):
    saida = powershell(
        "Get-Process -Id %d -ErrorAction SilentlyContinue | "
        "Select-Object WorkingSet64, HandleCount, "
        "@{n='Threads';e={$_.Threads.Count}} | ConvertTo-Json" % pid)
    if not saida:
        return None
    return json.loads(saida)


def main():
    destino = tempfile.mkdtemp(prefix="arena_longaduracao_")
    print("Pasta de teste:", destino)
    print("Duracao:", DURACAO_S, "s")
    try:
        for pasta in ("servidor", "dados", "launcher"):
            shutil.copytree(os.path.join(RAIZ, pasta), os.path.join(destino, pasta),
                             ignore=shutil.ignore_patterns("__pycache__", "tests"))
        pasta_nes = os.path.join(destino, "jogos", "pessoais", "NES")
        os.makedirs(pasta_nes, exist_ok=True)
        with open(os.path.join(pasta_nes, "Jogo Longa Duracao.nes"), "w"):
            pass

        # Roda o servidor como PROCESSO SEPARADO (nao em processo, como os
        # outros testes) -- assim a medicao de RAM/handles e a de verdade
        # do processo do servidor, sem misturar com o processo do teste.
        processo = subprocess.Popen(
            [os.path.join(RAIZ, "servidor", "python", "python.exe"),
             os.path.join(destino, "servidor", "arena.py")],
            cwd=destino, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1.5)

        status, texto = None, None
        for _ in range(50):
            status = requisicao("GET", "/api/estado")
            if status == 200:
                break
            time.sleep(0.2)
        if status != 200:
            print("[ERRO] servidor nao respondeu a tempo")
            processo.terminate()
            return 1

        catalogo_status = requisicao("GET", "/api/catalogo")
        with urllib.request.urlopen("http://127.0.0.1:8777/api/catalogo", timeout=5) as resp:
            catalogo = json.loads(resp.read())
        jogo_id = next(j["id"] for j in catalogo["jogos"] if "Longa Duracao" in j["titulo"])

        amostras = []
        inicio = time.monotonic()
        proxima_amostra = inicio
        pedidos = 0
        falhas = 0

        ciclo = [
            ("GET", "/api/estado", None),
            ("GET", "/api/catalogo", None),
            ("POST", "/api/jogar", {"jogo_id": jogo_id}),  # sem retroarch.exe -> erro limpo, testa o caminho mesmo assim
            ("POST", "/api/config", {"tema": "escuro"}),
            ("POST", "/api/config", {"tema": "claro"}),
            ("POST", "/api/cheat/adicionar", {"jogo_id": jogo_id, "codigo": "AAAA-0000", "descricao": "x"}),
            ("GET", "/api/colegas", None),
        ]

        print("\nAquecendo e medindo...")
        while time.monotonic() - inicio < DURACAO_S:
            for metodo, caminho, corpo in ciclo:
                status = requisicao(metodo, caminho, corpo)
                pedidos += 1
                if status is None:
                    falhas += 1

            agora = time.monotonic()
            if agora >= proxima_amostra:
                info = medir_processo(processo.pid)
                if info:
                    amostras.append({
                        "t": round(agora - inicio, 1),
                        "ram_mb": round(info["WorkingSet64"] / (1024 * 1024), 1),
                        "handles": info["HandleCount"],
                        "threads": info["Threads"],
                        "pedidos_ate_aqui": pedidos,
                    })
                    print("  t=%5.1fs  RAM=%7.1f MB  handles=%4d  threads=%3d  pedidos=%d"
                          % (amostras[-1]["t"], amostras[-1]["ram_mb"],
                             amostras[-1]["handles"], amostras[-1]["threads"], pedidos))
                proxima_amostra += AMOSTRA_A_CADA_S

        processo.terminate()
        try:
            processo.wait(timeout=10)
        except subprocess.TimeoutExpired:
            processo.kill()

        destino_relatorio = os.path.join(RAIZ, "docs", "longa_duracao_bruto.json")
        with open(destino_relatorio, "w", encoding="utf-8") as f:
            json.dump({"duracao_s": DURACAO_S, "pedidos_total": pedidos,
                       "falhas": falhas, "amostras": amostras}, f, ensure_ascii=False, indent=2)

        print("\n--- RESUMO ---")
        print("Pedidos totais:", pedidos, "| falhas de conexao:", falhas)
        if len(amostras) >= 3:
            primeira_estavel = amostras[1]  # pula a 1a (aquecimento)
            ultima = amostras[-1]
            cresc_ram = ultima["ram_mb"] - primeira_estavel["ram_mb"]
            cresc_handles = ultima["handles"] - primeira_estavel["handles"]
            print("Crescimento de RAM (apos aquecimento): %.1f MB" % cresc_ram)
            print("Crescimento de handles (apos aquecimento): %d" % cresc_handles)
            ok = falhas == 0 and cresc_ram < 15 and cresc_handles < 50
        else:
            print("Poucas amostras para avaliar tendencia.")
            ok = falhas == 0
        print("\nRelatorio salvo em", destino_relatorio)
        print("RESULTADO:", "PASSOU" if ok else "FALHOU (ou precisa de mais tempo pra confirmar)")
        return 0 if ok else 1
    finally:
        sys.path = [p for p in sys.path if not p.startswith(destino)]
        shutil.rmtree(destino, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
