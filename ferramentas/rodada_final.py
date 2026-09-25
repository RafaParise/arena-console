r"""Fase 8 da auditoria: roda TODOS os testes uma ultima vez, em sequencia.

Roda a bateria de referencia (servidor\tests\run.py, a mesma do
RODAR_TESTES.bat) e cada script testes\teste_*.py + testes\fuzz_rotas.py,
um de cada vez (varios sobem o servidor na mesma porta ou abrem o RetroArch,
entao nao podem rodar juntos). Anota codigo de saida e tempo de cada um em
docs\rodada_final_bruta.json.

Uso:
    servidor\python\python.exe ferramentas\rodada_final.py
"""
import glob
import json
import os
import subprocess
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON = os.path.join(RAIZ, "servidor", "python", "python.exe")
LIMITE_S = 900  # 15 min por script; o mais lento (5 RetroArch) leva bem menos


def rodar(caminho_relativo):
    inicio = time.time()
    try:
        r = subprocess.run([PYTHON, caminho_relativo], cwd=RAIZ, capture_output=True,
                           timeout=LIMITE_S)
        codigo = r.returncode
        saida = (r.stdout + r.stderr).decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        codigo, saida = "tempo esgotado", ""
    duracao = round(time.time() - inicio, 1)
    ultimas = saida.strip().splitlines()[-6:]
    print(f"[{'OK ' if codigo == 0 else 'FALHOU'}] {caminho_relativo} ({duracao}s)", flush=True)
    if codigo != 0:
        for linha in ultimas:
            print("      " + linha, flush=True)
    return {"script": caminho_relativo, "codigo_saida": codigo, "segundos": duracao,
            "ultimas_linhas": ultimas}


def principal():
    scripts = [os.path.join("servidor", "tests", "run.py"),
               os.path.join("testes", "fuzz_rotas.py"),
               # auditoria 2: frases da tela sem acento (Fase 7) e ARENA
               # copiado para outra pasta se conserta sozinho (Fase 6)
               os.path.join("testes", "textos_sem_acento.py"),
               os.path.join("ferramentas", "teste_aceite_pasta_movida.py")]
    scripts += sorted(os.path.relpath(c, RAIZ)
                      for c in glob.glob(os.path.join(RAIZ, "testes", "teste_*.py")))
    resultados = [rodar(s) for s in scripts]
    falhas = [r for r in resultados if r["codigo_saida"] != 0]
    print(f"\n{len(resultados) - len(falhas)} de {len(resultados)} passaram.")
    destino = os.path.join(RAIZ, "docs", "rodada_final_bruta.json")
    with open(destino, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    print("Resultado salvo em", destino)


if __name__ == "__main__":
    principal()
