"""Fase 0 da auditoria: mede a linha de base do ARENA parado e recem-aberto.

Nao depende de nenhum pacote fora da biblioteca padrao do Python (regra 5
do PLANO-AUDITORIA.md). Para numeros que o Windows so entrega por fora do
Python (memoria de processo, threads, portas, gravacoes em disco), chama o
powershell.exe que ja vem no Windows -- isso nao e "pip install", e usar uma
ferramenta que o sistema operacional ja tem, do mesmo jeito que o ARENA usa
retroarch.exe.

Uso:
    servidor\\python\\python.exe testes\\linha_base.py

Nao apaga nem grava nada em dados\\. So le o codigo e sobe o servidor uma vez,
numa pasta de trabalho normal (a mesma pasta do projeto), para medir o
processo de verdade.
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON = os.path.join(RAIZ, "servidor", "python", "python.exe")
ARENA_PY = os.path.join(RAIZ, "servidor", "arena.py")
ENDERECO = "http://127.0.0.1:8777/"

PASTAS_IGNORADAS_NO_TAMANHO = {"jogos", ".git", "backup"}


def tamanho_pasta(caminho, ignorar_no_topo=None):
    total = 0
    contagem = {}
    for raiz, subpastas, arquivos in os.walk(caminho):
        rel = os.path.relpath(raiz, caminho)
        topo = rel.split(os.sep)[0] if rel != "." else None
        if ignorar_no_topo and topo in ignorar_no_topo:
            subpastas[:] = []
            continue
        for nome in arquivos:
            caminho_arquivo = os.path.join(raiz, nome)
            try:
                tamanho = os.path.getsize(caminho_arquivo)
            except OSError:
                continue
            total += tamanho
            chave = topo or "(raiz)"
            contagem[chave] = contagem.get(chave, 0) + tamanho
    return total, contagem


def contar_linhas():
    extensoes = {".py": 0, ".js": 0, ".html": 0, ".css": 0, ".json": 0}
    linhas_por_extensao = {ext: 0 for ext in extensoes}
    arquivos_por_extensao = {ext: 0 for ext in extensoes}
    detalhe = []
    for raiz, subpastas, arquivos in os.walk(RAIZ):
        rel = os.path.relpath(raiz, RAIZ)
        topo = rel.split(os.sep)[0] if rel != "." else None
        # emuladores\ e retroarch\ sao de terceiros (PCSX2, RPCS3, Xenia,
        # nucleos libretro) -- nao e codigo do ARENA, entraria como bloat
        # falso na contagem (ex.: ThirdPartyLicenses.html com 5914 linhas).
        if topo in ("jogos", ".git", "backup", "python", "emuladores", "retroarch"):
            subpastas[:] = []
            continue
        if os.path.basename(raiz) == "python" and "servidor" in raiz:
            subpastas[:] = []
            continue
        for nome in arquivos:
            ext = os.path.splitext(nome)[1].lower()
            if ext not in extensoes:
                continue
            caminho_arquivo = os.path.join(raiz, nome)
            try:
                with open(caminho_arquivo, "r", encoding="utf-8", errors="ignore") as f:
                    n = sum(1 for _ in f)
            except OSError:
                continue
            linhas_por_extensao[ext] += n
            arquivos_por_extensao[ext] += 1
            detalhe.append((os.path.relpath(caminho_arquivo, RAIZ), n))
    detalhe.sort(key=lambda item: -item[1])
    return linhas_por_extensao, arquivos_por_extensao, detalhe


def powershell(comando):
    resultado = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", comando],
        capture_output=True, text=True, timeout=60,
    )
    return resultado.stdout.strip()


def pids_descendentes(pid_raiz):
    comando = (
        "$alvo = @(%d); $todos = Get-CimInstance Win32_Process | "
        "Select-Object ProcessId, ParentProcessId, Name; "
        "$mudou = $true; while ($mudou) { $mudou = $false; "
        "foreach ($p in $todos) { if ($alvo -contains $p.ParentProcessId -and -not ($alvo -contains $p.ProcessId)) "
        "{ $alvo += $p.ProcessId; $mudou = $true } } }; $alvo -join ','"
    ) % pid_raiz
    saida = powershell(comando)
    if not saida:
        return [pid_raiz]
    return [int(x) for x in saida.split(",") if x.strip()]


def memoria_e_threads(pids):
    lista = ",".join(str(p) for p in pids)
    comando = (
        "Get-Process -Id %s -ErrorAction SilentlyContinue | "
        "Select-Object Id, ProcessName, WorkingSet64, "
        "@{n='Threads';e={$_.Threads.Count}}, "
        "@{n='CPU';e={$_.CPU}} | ConvertTo-Json"
    ) % lista
    saida = powershell(comando)
    if not saida:
        return []
    dados = json.loads(saida)
    if isinstance(dados, dict):
        dados = [dados]
    return dados


def portas_escutando(pids):
    lista = ",".join(str(p) for p in pids)
    comando = (
        "Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | "
        "Where-Object { $_.OwningProcess -in @(%s) } | "
        "Select-Object LocalAddress, LocalPort, OwningProcess | ConvertTo-Json"
    ) % lista
    saida = powershell(comando)
    if not saida:
        return []
    dados = json.loads(saida)
    if isinstance(dados, dict):
        dados = [dados]
    return dados


def main():
    resultado = {}

    print("1/5 - Tamanho do pacote (sem jogos, sem .git, sem backup)...")
    total, por_pasta = tamanho_pasta(RAIZ, PASTAS_IGNORADAS_NO_TAMANHO)
    resultado["tamanho_total_mb"] = round(total / (1024 * 1024), 1)
    resultado["tamanho_por_pasta_mb"] = {
        k: round(v / (1024 * 1024), 1) for k, v in sorted(por_pasta.items(), key=lambda kv: -kv[1])
    }
    print("    %.1f MB" % resultado["tamanho_total_mb"])

    print("2/5 - Linhas de codigo por extensao...")
    linhas, arquivos, detalhe = contar_linhas()
    resultado["linhas_por_extensao"] = linhas
    resultado["arquivos_por_extensao"] = arquivos
    resultado["maiores_arquivos"] = detalhe[:15]
    print("    total:", sum(linhas.values()), "linhas")

    print("3/5 - Subindo o ARENA de verdade para medir tempo de abertura...")
    inicio = time.time()
    processo = subprocess.Popen(
        [PYTHON, ARENA_PY], cwd=RAIZ,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    pronto_em = None
    for _ in range(200):
        try:
            with urllib.request.urlopen(ENDERECO, timeout=0.5) as resp:
                if resp.status == 200:
                    pronto_em = time.time() - inicio
                    break
        except Exception:
            time.sleep(0.1)
    if pronto_em is None:
        print("    [ERRO] O servidor nao respondeu em 20s.")
        processo.terminate()
        resultado["erro"] = "servidor nao respondeu"
    else:
        print("    pronto em %.2fs (resposta HTTP da pagina principal)" % pronto_em)
        resultado["tempo_abertura_s"] = round(pronto_em, 2)

        print("4/5 - Esperando 12s para o processo assentar, depois medindo parado...")
        time.sleep(12)
        pids = pids_descendentes(processo.pid)
        print("    processos encontrados (python + navegador se abriu):", pids)
        antes = memoria_e_threads(pids)
        cpu_antes = {p["Id"]: p.get("CPU") or 0 for p in antes}
        t_cpu_antes = time.time()

        time.sleep(15)
        depois = memoria_e_threads(pids)
        cpu_depois = {p["Id"]: p.get("CPU") or 0 for p in depois}
        t_cpu_depois = time.time()

        janela = t_cpu_depois - t_cpu_antes
        cpu_usado = sum(cpu_depois.get(pid, 0) - cpu_antes.get(pid, 0) for pid in cpu_depois)
        ncpu_saida = powershell("(Get-CimInstance Win32_ComputerSystem).NumberOfLogicalProcessors")
        try:
            ncpu = int(ncpu_saida)
        except ValueError:
            ncpu = 1
        cpu_percentual = 100.0 * cpu_usado / janela / ncpu if janela > 0 else 0.0

        ram_total_mb = sum((p.get("WorkingSet64") or 0) for p in depois) / (1024 * 1024)
        detalhe_ram = [
            {"pid": p["Id"], "nome": p["ProcessName"], "ram_mb": round((p.get("WorkingSet64") or 0) / (1024 * 1024), 1),
             "threads": p.get("Threads")}
            for p in depois
        ]

        resultado["cpu_parado_pct"] = round(cpu_percentual, 2)
        resultado["cpu_medido_em_s"] = round(janela, 1)
        resultado["ram_total_mb"] = round(ram_total_mb, 1)
        resultado["processos"] = detalhe_ram
        resultado["threads_total"] = sum((p.get("Threads") or 0) for p in depois)

        print("    CPU parado: %.2f%% (janela de %.1fs, %d nucleos logicos)" % (cpu_percentual, janela, ncpu))
        print("    RAM total: %.1f MB" % ram_total_mb)
        for p in detalhe_ram:
            print("      -", p["nome"], "pid", p["pid"], ":", p["ram_mb"], "MB,", p["threads"], "threads")

        print("5/5 - Portas TCP em escuta...")
        portas = portas_escutando(pids)
        resultado["portas_escutando"] = portas
        for porta in portas:
            print("    ", porta.get("LocalAddress"), ":", porta.get("LocalPort"))

        print("\nEncerrando o servidor de teste...")
        for pid in pids:
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
        processo.wait(timeout=10)

    destino = os.path.join(RAIZ, "docs", "linha_base_bruta.json")
    with open(destino, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    print("\nResultado bruto salvo em", destino)


if __name__ == "__main__":
    main()
