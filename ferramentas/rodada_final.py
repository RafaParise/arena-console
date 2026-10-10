r"""Fase 8 da auditoria: roda TODOS os testes uma ultima vez, em sequencia.

Roda a bateria de referencia (servidor\tests\run.py, a mesma do
RODAR_TESTES.bat) e cada script testes\teste_*.py + testes\fuzz_rotas.py,
um de cada vez (varios sobem o servidor na mesma porta ou abrem o RetroArch,
entao nao podem rodar juntos). Anota codigo de saida e tempo de cada um em
docs\rodada_final_bruta.json.

Uso:
    servidor\python\python.exe ferramentas\rodada_final.py [pedaco do nome ...] [--saida=<arquivo.json>] [--continuar]

Com pedacos de nome, roda so os scripts que tem algum deles no nome (para
repetir os que falharam sem esperar a rodada inteira).

--saida (auditoria 3, 07/10/2026): grava o resultado nesse arquivo DEPOIS DE
CADA script, e nao so no fim -- em 02/10 e 03/10 a rodada foi morta no meio
por falta de memoria e tudo o que ja tinha passado se perdeu. Com
--continuar, pula os scripts que ja estao no arquivo (retoma de onde parou).
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
LIMITES_ESPECIAIS = {
    # Abre CADA jogo do catalogo, e o catalogo cresceu (62 jogos em 25/09,
    # 129 em 01/10): ~45 s por jogo nos consoles com Jogar Junto.
    os.path.join("testes", "teste_abrir_todos.py"): 3600,
    # Abre CADA jogo de PS2 da pasta (37 em 10/10/2026), ~20 s cada, mais os
    # niveis de qualidade em 3 jogos; o jogo que nao comeca espera 60 s.
    os.path.join("testes", "teste_ps2_todos_os_jogos.py"): 2700,
}

# Arquivos DE VERDADE que nenhum teste deveria mudar. O retroarch.cfg volta
# sozinho se mudar (o protege_cfg dos testes nao devolve quando o teste e'
# morto por tempo); os de dados\ so sao apontados -- o ARENA de verdade pode
# estar aberto durante a rodada.
# Os que a rodada DEVOLVE quando um teste muda. O PCSX2.ini entrou em
# 02/10/2026: o teste_pcsx2_inicia gravava nele e nao devolvia (o PS2 do
# Rafael ficava com 2x e Direct3D 12 ate o proximo jogo pelo ARENA).
DEVOLVIDOS = [os.path.join("retroarch", "retroarch.cfg"),
              os.path.join("emuladores", "PCSX2", "PCSX2", "inis", "PCSX2.ini")]
VIGIADOS = DEVOLVIDOS + [
    os.path.join("dados", nome) for nome in ("arena.db", "config.json", "controles.json", "jogadores.txt",
                                             "consoles_manuais.json")]

# Ferramentas de investigacao que moram em testes\ mas pedem arquivos de uma
# partida especifica (nao ha o que testar sem eles). Ficam fora, com o motivo.
FORA_DA_RODADA = {
    os.path.join("testes", "teste_imagem_ps1.py"):
        "investigacao do CTR (25/09): pede o .cfg e as opcoes de uma partida",
    os.path.join("testes", "teste_pcsx2_bissecao.py"):
        "investigacao do PCSX2 (26/09): pede um PCSX2.ini de base e a foto",
    os.path.join("testes", "teste_xenia_abre.py"):
        "investigacao do Xenia (26/09): pede o jogo, o .exe e a foto",
}

# Achado de 01/10/2026: a rodada caiu no meio porque um teste escreveu
# acento na saida (o Windows manda em cp1252 para o cano) e o print desta
# janela, redirecionada para arquivo, nao aceitava o caractere trocado.
for _saida in (sys.stdout, sys.stderr):
    try:
        _saida.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass


def retrato_dos_vigiados():
    """Os DEVOLVIDOS inteiros (para devolver) e tamanho+data dos de dados\\."""
    retrato = {}
    for relativo in VIGIADOS:
        caminho = os.path.join(RAIZ, relativo)
        try:
            if relativo in DEVOLVIDOS:
                with open(caminho, "rb") as arquivo:
                    retrato[relativo] = arquivo.read()
            else:
                info = os.stat(caminho)
                retrato[relativo] = (info.st_size, info.st_mtime_ns)
        except OSError:
            retrato[relativo] = None
    return retrato


def conferir_vigiados(antes):
    """Aponta o que o teste mudou de verdade; devolve os DEVOLVIDOS."""
    depois = retrato_dos_vigiados()
    mexidos = [r for r in VIGIADOS if depois.get(r) != antes.get(r)]
    devolvidos = []
    for relativo in DEVOLVIDOS:
        if relativo in mexidos and antes.get(relativo) is not None:
            provisorio = os.path.join(RAIZ, relativo + ".rodada.tmp")
            with open(provisorio, "wb") as arquivo:
                arquivo.write(antes[relativo])
            os.replace(provisorio, os.path.join(RAIZ, relativo))
            devolvidos.append(os.path.basename(relativo))
    if mexidos:
        print("      [dado real] mexeu em: %s%s" % (", ".join(mexidos),
              " (devolvido: %s)" % ", ".join(devolvidos) if devolvidos else ""), flush=True)
    return mexidos


def rodar(caminho_relativo):
    antes = set(limpeza.pastas_de_teste())
    vigiados = retrato_dos_vigiados()
    limite = LIMITES_ESPECIAIS.get(caminho_relativo, LIMITE_S)
    inicio = time.time()
    # Sem abrir a tela do ARENA a cada servidor que um teste sobe. Saida em
    # UTF-8 e sem espera (PYTHONUNBUFFERED): um teste que morre de vez
    # (processo encerrado a forca) perdia tudo o que estava na memoria e
    # aparecia aqui como "FALHOU" sem uma linha de explicacao.
    ambiente = dict(os.environ, ARENA_SEM_JANELA="1", PYTHONIOENCODING="utf-8",
                    PYTHONUNBUFFERED="1")
    processo = subprocess.Popen([PYTHON, caminho_relativo], cwd=RAIZ, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, env=ambiente)
    try:
        bruto, _ = processo.communicate(timeout=limite)
        codigo = processo.returncode
    except subprocess.TimeoutExpired:
        # A ARVORE inteira: so o Python do teste caia, e o RetroArch (ou o
        # Edge) que ele tinha aberto ficava orfao. A saida ate ali vem junto.
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(processo.pid)], capture_output=True)
        bruto, _ = processo.communicate()
        codigo = "tempo esgotado (%d s)" % limite
    saida = (bruto or b"").decode("utf-8", "replace")
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
    mexidos = conferir_vigiados(vigiados)
    return {"script": caminho_relativo, "codigo_saida": codigo, "segundos": duracao,
            "ultimas_linhas": ultimas, "dados_reais_mexidos": mexidos,
            "pastas_esquecidas_no_temp": len(sobras),
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
    pedacos = [p.lower() for p in sys.argv[1:] if not p.startswith("--")]
    if pedacos:
        scripts = [s for s in scripts if any(p in s.lower() for p in pedacos)]
    saida = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--saida=")), "")
    if saida and not os.path.isabs(saida):
        saida = os.path.join(RAIZ, saida)
    resultados = []
    if saida and "--continuar" in sys.argv and os.path.isfile(saida):
        with open(saida, encoding="utf-8") as f:
            resultados = json.load(f)
        feitos = {r["script"] for r in resultados}
        print("Continuando: %d script(s) ja estao em %s" % (len(feitos), saida), flush=True)
        scripts = [s for s in scripts if s not in feitos]

    def gravar(destino):
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        temporario = destino + ".tmp"
        with open(temporario, "w", encoding="utf-8") as f:
            json.dump(resultados, f, ensure_ascii=False, indent=2)
        os.replace(temporario, destino)

    for script in scripts:
        if script in FORA_DA_RODADA:
            print("[fora] %s (%s)" % (script, FORA_DA_RODADA[script]), flush=True)
            continue
        resultados.append(rodar(script))
        if saida:
            gravar(saida)
    falhas = [r for r in resultados if r["codigo_saida"] != 0]
    print(f"\n{len(resultados) - len(falhas)} de {len(resultados)} passaram.")
    if saida:
        print("Resultado salvo em", saida)
        return 1 if falhas else 0
    if pedacos:
        print("(rodada parcial: o docs\\rodada_final_bruta.json nao foi trocado)")
        return 1 if falhas else 0
    destino = os.path.join(RAIZ, "docs", "rodada_final_bruta.json")
    gravar(destino)
    print("Resultado salvo em", destino)
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(principal())
