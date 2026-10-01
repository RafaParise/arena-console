r"""Fase 8 da auditoria: roda TODOS os testes uma ultima vez, em sequencia.

Roda a bateria de referencia (servidor\tests\run.py, a mesma do
RODAR_TESTES.bat) e cada script testes\teste_*.py + testes\fuzz_rotas.py,
um de cada vez (varios sobem o servidor na mesma porta ou abrem o RetroArch,
entao nao podem rodar juntos). Anota codigo de saida e tempo de cada um em
docs\rodada_final_bruta.json.

Uso:
    servidor\python\python.exe ferramentas\rodada_final.py [pedaco do nome ...]

Com pedacos de nome, roda so os scripts que tem algum deles no nome (para
repetir os que falharam sem esperar a rodada inteira).
"""
import glob
import json
import os
import subprocess
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON = os.path.join(RAIZ, "servidor", "python", "python.exe")
sys.path.insert(0, os.path.join(RAIZ, "testes"))
import limpeza  # noqa: E402  (pastas que um teste esquece no Temp)
LIMITE_S = 900  # 15 min por script; o mais lento (5 RetroArch) leva bem menos

# Ferramentas de investigacao que moram em testes\ mas pedem arquivos de uma
# partida especifica (nao ha o que testar sem eles). Ficam fora, com o motivo.
FORA_DA_RODADA = {
    os.path.join("testes", "teste_imagem_ps1.py"):
        "investigacao do CTR (25/09): pede o .cfg e as opcoes de uma partida",
}

# Achado de 01/10/2026: a rodada caiu no meio porque um teste escreveu
# acento na saida (o Windows manda em cp1252 para o cano) e o print desta
# janela, redirecionada para arquivo, nao aceitava o caractere trocado.
for _saida in (sys.stdout, sys.stderr):
    try:
        _saida.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass


def rodar(caminho_relativo):
    antes = set(limpeza.pastas_de_teste())
    inicio = time.time()
    # Sem abrir a tela do ARENA a cada servidor que um teste sobe. Saida em
    # UTF-8 e sem espera (PYTHONUNBUFFERED): um teste que morre de vez
    # (processo encerrado a forca) perdia tudo o que estava na memoria e
    # aparecia aqui como "FALHOU" sem uma linha de explicacao.
    ambiente = dict(os.environ, ARENA_SEM_JANELA="1", PYTHONIOENCODING="utf-8",
                    PYTHONUNBUFFERED="1")
    try:
        r = subprocess.run([PYTHON, caminho_relativo], cwd=RAIZ, capture_output=True,
                           timeout=LIMITE_S, env=ambiente)
        codigo = r.returncode
        saida = (r.stdout + r.stderr).decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        codigo, saida = "tempo esgotado", ""
    duracao = round(time.time() - inicio, 1)
    # Linha gigante (2 MB do fuzz) nao enche o relatorio.
    ultimas = [linha[:300] for linha in saida.strip().splitlines()[-8:]]
    print(f"[{'OK ' if codigo == 0 else 'FALHOU'}] {caminho_relativo} ({duracao}s)", flush=True)
    if codigo != 0:
        print("      codigo de saida: %s" % codigo, flush=True)
        for linha in ultimas:
            print("      " + linha, flush=True)
    # Teste que deixa pasta no Temp: aponta e apaga (achado de 01/10/2026:
    # 2,9 GB esquecidos neste computador).
    sobras = [c for c in limpeza.pastas_de_teste() if c not in antes]
    sujeira = sum(limpeza.tamanho(c) for c in sobras)
    presas = [c for c in sobras if not limpeza.apagar_pasta(c)]
    if sobras:
        print("      [sujeira] deixou %d pasta(s) no Temp (%.1f MB)%s" % (
            len(sobras), sujeira / 1024 ** 2, "; %d nao saiu(ram)" % len(presas) if presas else ": apagadas"),
              flush=True)
    return {"script": caminho_relativo, "codigo_saida": codigo, "segundos": duracao,
            "ultimas_linhas": ultimas, "pastas_esquecidas_no_temp": len(sobras),
            "mb_esquecidos": round(sujeira / 1024 ** 2, 1)}


def principal():
    scripts = [os.path.join("servidor", "tests", "run.py"),
               os.path.join("testes", "fuzz_rotas.py"),
               # auditoria 2: frases da tela sem acento (Fase 7) e ARENA
               # copiado para outra pasta se conserta sozinho (Fase 6)
               os.path.join("testes", "textos_sem_acento.py"),
               os.path.join("ferramentas", "teste_aceite_pasta_movida.py")]
    scripts += sorted(os.path.relpath(c, RAIZ)
                      for c in glob.glob(os.path.join(RAIZ, "testes", "teste_*.py")))
    pedacos = [p.lower() for p in sys.argv[1:]]
    if pedacos:
        scripts = [s for s in scripts if any(p in s.lower() for p in pedacos)]
    resultados = []
    for script in scripts:
        if script in FORA_DA_RODADA:
            print("[fora] %s (%s)" % (script, FORA_DA_RODADA[script]), flush=True)
            continue
        resultados.append(rodar(script))
    falhas = [r for r in resultados if r["codigo_saida"] != 0]
    print(f"\n{len(resultados) - len(falhas)} de {len(resultados)} passaram.")
    if pedacos:
        print("(rodada parcial: o docs\\rodada_final_bruta.json nao foi trocado)")
        return 1 if falhas else 0
    destino = os.path.join(RAIZ, "docs", "rodada_final_bruta.json")
    with open(destino, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    print("Resultado salvo em", destino)
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(principal())
