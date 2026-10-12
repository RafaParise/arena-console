# -*- coding: utf-8 -*-
r"""Linha de base do ARENA: tamanho, linhas, abertura, parado, tela e portas.

Criado na Fase 0 da auditoria 1 (23/09/2026). Ampliado na auditoria 3
(07/10/2026) com o que o roteiro pede e a versao antiga nao media:
  - o tempo ate a TELA ficar pronta, nao so a resposta do servidor: o Edge
    abre como janela de aplicativo, como o ARENA abre (perfil temporario:
    o Edge do usuario nao e' tocado), e a pagina anota o instante em que o
    numero de jogos aparece (a lista ja desenhada);
  - memoria e processador da TELA parada, com a janela a frente;
  - os temporizadores da tela (setInterval vivos, setTimeout por minuto,
    quadros de animacao por segundo) e os pedidos dela ao servidor;
  - o servidor parado por 60 s depois de 30 s para assentar (eram 15 s
    depois de 12 s), sem a tela e com a tela;
  - as portas UDP (descoberta de colegas), alem das TCP, cada uma dizendo
    se escuta so neste computador ou na rede toda;
  - as linhas de TODOS os arquivos, por grupo (programa, ferramentas,
    testes, guias e documentos).

So biblioteca padrao do Python; o que o Windows so entrega por fora
(memoria de processo, threads, portas) vem do powershell.exe que ja vem no
Windows. O servidor sobe na pasta de verdade, como o aluno abre, mas sem a
janela dele (ARENA_SEM_JANELA=1) e com a saida para o "nada" (escrever na
janela preta nao conta). Recusa rodar com outro ARENA aberto na 8777.

Uso:
    servidor\python\python.exe testes\linha_base.py [--saida=<arquivo.json>] [--sem-tela]
"""
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
import tela_sem_janela  # noqa: E402

PYTHON = os.path.join(RAIZ, "servidor", "python", "python.exe")
ARENA_PY = os.path.join(RAIZ, "servidor", "arena.py")
PORTA = 8777
ENDERECO = "http://127.0.0.1:%d/" % PORTA
ASSENTAR_S = 30
JANELA_S = 60

PASTAS_IGNORADAS_NO_TAMANHO = {"jogos", ".git", "backup"}
# Fora da contagem de linhas: programas de terceiros (emuladores, nucleos,
# Python embutido), dados do usuario, BIOS e as saidas do COLETAR.
FORA_DAS_LINHAS = {"jogos", ".git", "backup", "emuladores", "retroarch", "dados", "perfil", "BIOS"}
EXTENSOES = (".py", ".js", ".html", ".css", ".json", ".bat", ".ps1", ".md", ".txt")

# Posto na pagina ANTES do codigo do ARENA (Page.addScriptToEvaluateOnNewDocument):
# conta os temporizadores e os pedidos, e anota quando a lista aparece.
SCRIPT_DA_PAGINA = r"""
(() => {
  if (window.__arena) return;
  const reg = { intervalos: new Map(), timeouts: 0, quadros: 0, pedidos: [], pronta: null, zeradoEm: 0 };
  window.__arena = reg;
  const si = window.setInterval.bind(window), ci = window.clearInterval.bind(window);
  const st = window.setTimeout.bind(window), raf = window.requestAnimationFrame.bind(window);
  const origem = () => ((new Error().stack || "").split("\n")[3] || "").trim().replace(/^at /, "");
  window.setInterval = (fn, ms, ...resto) => {
    const id = si(fn, ms, ...resto);
    reg.intervalos.set(id, { ms: Number(ms) || 0, origem: origem() });
    return id;
  };
  window.clearInterval = (id) => { reg.intervalos.delete(id); return ci(id); };
  window.setTimeout = (fn, ms, ...resto) => { reg.timeouts += 1; return st(fn, ms, ...resto); };
  window.requestAnimationFrame = (fn) => { reg.quadros += 1; return raf(fn); };
  const pedirOriginal = window.fetch.bind(window);
  window.fetch = (entrada, ...resto) => {
    const url = typeof entrada === "string" ? entrada : (entrada && entrada.url) || "";
    reg.pedidos.push(url.replace(location.origin, "").split("?")[0]);
    return pedirOriginal(entrada, ...resto);
  };
  reg.zerar = () => { reg.timeouts = 0; reg.quadros = 0; reg.pedidos = []; reg.zeradoEm = performance.now(); };
  const olhar = () => {
    const el = document.getElementById("lidoJogos");
    if (reg.pronta === null && el && el.textContent.trim() !== "0") {
      reg.pronta = performance.now();
      observador.disconnect();
    }
  };
  const observador = new MutationObserver(olhar);
  observador.observe(document, { subtree: true, childList: true, characterData: true });
})();
"""

RESUMO_DA_PAGINA = r"""
(() => {
  const r = window.__arena;
  const cont = {};
  for (const p of r.pedidos) cont[p] = (cont[p] || 0) + 1;
  return {
    segundos: (performance.now() - r.zeradoEm) / 1000,
    intervalos: [...r.intervalos.values()],
    timeouts: r.timeouts, quadros: r.quadros, pedidos: cont,
    visivel: document.visibilityState, foco: document.hasFocus(),
    menos_movimento: matchMedia("(prefers-reduced-motion: reduce)").matches,
    telas_de_desenho: document.querySelectorAll("canvas").length,
    tema: document.documentElement.dataset.tema || document.body.dataset.tema || "",
  };
})()
"""


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
            try:
                tamanho = os.path.getsize(os.path.join(raiz, nome))
            except OSError:
                continue
            total += tamanho
            chave = topo or "(raiz)"
            contagem[chave] = contagem.get(chave, 0) + tamanho
    return total, contagem


def grupo_do_arquivo(rel):
    partes = rel.replace("\\", "/").split("/")
    topo = partes[0] if len(partes) > 1 else ""
    ext = os.path.splitext(rel)[1].lower()
    if topo == "servidor":
        return "testes" if len(partes) > 2 and partes[1] == "tests" else "programa"
    if topo == "launcher":
        return "programa"
    if topo in ("testes", "ferramentas"):
        return topo
    if topo == "docs":
        return "documentos" if ext in (".md", ".txt") else "medidas"
    if topo == "":
        if partes[0].upper() == "RODAR_TESTES.BAT":
            return "testes"
        return "programa" if ext == ".bat" else "guias"
    return "outros"


def contar_linhas():
    arquivos = []
    for raiz, subpastas, nomes in os.walk(RAIZ):
        rel = os.path.relpath(raiz, RAIZ)
        partes = [] if rel == "." else rel.split(os.sep)
        if partes and partes[0] in FORA_DAS_LINHAS:
            subpastas[:] = []
            continue
        # O Python embutido (servidor\python) e os caches nao sao do ARENA.
        subpastas[:] = [s for s in subpastas if s != "__pycache__" and not (partes == ["servidor"] and s == "python")]
        for nome in nomes:
            ext = os.path.splitext(nome)[1].lower()
            if ext not in EXTENSOES:
                continue
            caminho = os.path.join(raiz, nome)
            try:
                with open(caminho, "r", encoding="utf-8", errors="ignore") as f:
                    n = sum(1 for _ in f)
            except OSError:
                continue
            arquivo = os.path.relpath(caminho, RAIZ)
            arquivos.append({"arquivo": arquivo, "linhas": n, "grupo": grupo_do_arquivo(arquivo), "ext": ext})
    arquivos.sort(key=lambda a: (a["grupo"], -a["linhas"]))
    por_grupo = {}
    for a in arquivos:
        g = por_grupo.setdefault(a["grupo"], {"arquivos": 0, "linhas": 0, "por_extensao": {}})
        g["arquivos"] += 1
        g["linhas"] += a["linhas"]
        g["por_extensao"][a["ext"]] = g["por_extensao"].get(a["ext"], 0) + a["linhas"]
    return arquivos, por_grupo


def powershell(comando):
    resultado = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", comando],
                               capture_output=True, text=True, timeout=90)
    return resultado.stdout.strip()


def em_json(saida):
    if not saida:
        return []
    dados = json.loads(saida)
    return [dados] if isinstance(dados, dict) else dados


def processos(pids):
    """Memoria, threads, alcas e tempo de processador de cada processo."""
    if not pids:
        return []
    comando = ("Get-Process -Id %s -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, WorkingSet64, "
               "PrivateMemorySize64, HandleCount, @{n='Threads';e={$_.Threads.Count}}, "
               "@{n='CPU';e={$_.TotalProcessorTime.TotalSeconds}} | ConvertTo-Json") % ",".join(str(p) for p in pids)
    return em_json(powershell(comando))


def alcance(endereco):
    if endereco in ("127.0.0.1", "::1"):
        return "so este computador"
    if endereco in ("0.0.0.0", "::"):
        return "rede toda"
    return "uma placa de rede (%s)" % endereco


def portas(pids):
    lista = ",".join(str(p) for p in pids)
    tcp = em_json(powershell(
        "Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.OwningProcess -in "
        "@(%s) } | Select-Object LocalAddress, LocalPort, OwningProcess | ConvertTo-Json" % lista))
    udp = em_json(powershell(
        "Get-NetUDPEndpoint -ErrorAction SilentlyContinue | Where-Object { $_.OwningProcess -in @(%s) } | "
        "Select-Object LocalAddress, LocalPort, OwningProcess | ConvertTo-Json" % lista))
    saida = []
    for protocolo, itens in (("TCP", tcp), ("UDP", udp)):
        for item in itens:
            saida.append({"protocolo": protocolo, "endereco": item.get("LocalAddress"), "porta": item.get("LocalPort"),
                          "alcance": alcance(item.get("LocalAddress")), "pid": item.get("OwningProcess")})
    return sorted(saida, key=lambda p: (p["protocolo"], p["porta"] or 0))


def pids_descendentes(pid_raiz):
    comando = (
        "$alvo = @(%d); $todos = Get-CimInstance Win32_Process | Select-Object ProcessId, ParentProcessId; "
        "$mudou = $true; while ($mudou) { $mudou = $false; foreach ($p in $todos) { if ($alvo -contains "
        "$p.ParentProcessId -and -not ($alvo -contains $p.ProcessId)) { $alvo += $p.ProcessId; $mudou = $true } } }; "
        "$alvo -join ','") % pid_raiz
    saida = powershell(comando)
    return [int(x) for x in saida.split(",") if x.strip().isdigit()] or [pid_raiz]


def resumo_de(lista):
    return {"ram_mb": round(sum(p.get("WorkingSet64") or 0 for p in lista) / 1024 ** 2, 1),
            "privada_mb": round(sum(p.get("PrivateMemorySize64") or 0 for p in lista) / 1024 ** 2, 1),
            "threads": sum(p.get("Threads") or 0 for p in lista),
            "alcas": sum(p.get("HandleCount") or 0 for p in lista),
            "processos": len(lista)}


def medir_parado(grupos, segundos):
    """Processador de cada grupo de processos ao longo de 'segundos'.
    grupos: {"servidor": [pids], "tela": [pids]}."""
    antes = {g: {p["Id"]: p.get("CPU") or 0 for p in processos(pids)} for g, pids in grupos.items()}
    inicio = time.monotonic()
    time.sleep(segundos)
    depois_lista = {g: processos(pids) for g, pids in grupos.items()}
    janela = time.monotonic() - inicio
    ncpu = os.cpu_count() or 1
    saida = {}
    for g, lista in depois_lista.items():
        usado = sum((p.get("CPU") or 0) - antes[g].get(p["Id"], p.get("CPU") or 0) for p in lista)
        um_nucleo = 100.0 * usado / janela if janela else 0.0
        saida[g] = dict(resumo_de(lista), cpu_um_nucleo_pct=round(um_nucleo, 2),
                        cpu_total_pct=round(um_nucleo / ncpu, 3), janela_s=round(janela, 1),
                        detalhe=[{"pid": p["Id"], "nome": p["ProcessName"],
                                  "ram_mb": round((p.get("WorkingSet64") or 0) / 1024 ** 2, 1),
                                  "threads": p.get("Threads"), "alcas": p.get("HandleCount")} for p in lista])
    return saida


def espera_antes_da_janela():
    """O ARENA espera um pouco depois de abrir a porta para abrir a janela
    (threading.Timer em arena.principal): esse tempo entra na abertura."""
    with open(ARENA_PY, encoding="utf-8") as f:
        m = re.search(r"threading\.Timer\(\s*([\d.]+)\s*,\s*lambda:\s*abrir_janela", f.read())
    return float(m.group(1)) if m else 0.0


def porta_ocupada():
    try:
        with socket.create_connection(("127.0.0.1", PORTA), timeout=0.5):
            return True
    except OSError:
        return False


def config_do_usuario():
    """O que, na config de quem usa, muda a medida (so leitura)."""
    try:
        with open(os.path.join(RAIZ, "dados", "config.json"), encoding="utf-8") as f:
            config = json.load(f)
    except (OSError, ValueError):
        return {}
    return {k: config.get(k) for k in ("permitir_rede", "modo_modesto", "tema", "fundo_animado",
                                       "ultra_desempenho")}


def medir_tela(pid_servidor):
    """Abre a tela como o ARENA abre e mede abertura, memoria, processador,
    temporizadores e pedidos (o Edge do usuario nao e' tocado)."""
    inicio = time.monotonic()
    with tela_sem_janela.Navegador(janela=True) as nav:
        navegador_s = time.monotonic() - inicio
        nav.comando("Page.addScriptToEvaluateOnNewDocument", source=SCRIPT_DA_PAGINA)
        nav.comando("Page.bringToFront")
        nav.comando("Page.navigate", url=ENDERECO)
        pronta_ms, fim = None, time.monotonic() + 90
        while pronta_ms is None and time.monotonic() < fim:
            time.sleep(0.05)
            try:
                pronta_ms = nav.avaliar("window.__arena ? window.__arena.pronta : null")
            except OSError:
                pronta_ms = None
        if pronta_ms is None:
            return {"erro": "a lista de jogos nao apareceu em 90 s", "navegador_s": round(navegador_s, 2)}
        print("    tela pronta: navegador %.2f s + pagina %.2f s" % (navegador_s, pronta_ms / 1000), flush=True)
        print("    esperando %d s para assentar..." % ASSENTAR_S, flush=True)
        time.sleep(ASSENTAR_S)
        nav.comando("Page.bringToFront")
        nav.avaliar("window.__arena.zerar(); 1")
        pids_tela = nav.pids()
        print("    medindo %d s parado com a tela (%d processos do Edge)..." % (JANELA_S, len(pids_tela)), flush=True)
        medida = medir_parado({"servidor": [pid_servidor], "tela": pids_tela}, JANELA_S)
        pagina = nav.avaliar(RESUMO_DA_PAGINA) or {}
        minutos = (pagina.get("segundos") or JANELA_S) / 60.0
        pagina["timeouts_por_minuto"] = round((pagina.get("timeouts") or 0) / minutos, 1)
        pagina["quadros_por_segundo"] = round((pagina.get("quadros") or 0) / (minutos * 60), 1)
        pagina["pedidos_por_minuto"] = {k: round(v / minutos, 1) for k, v in (pagina.get("pedidos") or {}).items()}
        return {"navegador_s": round(navegador_s, 2), "pagina_s": round(pronta_ms / 1000, 2),
                "servidor_com_tela": medida["servidor"], "tela": medida["tela"], "pagina": pagina}


def principal():
    saida = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--saida=")),
                 os.path.join(RAIZ, "docs", "linha_base_bruta.json"))
    if not os.path.isabs(saida):
        saida = os.path.join(RAIZ, saida)
    if porta_ocupada():
        print("Ja ha um ARENA aberto na porta %d. Feche-o e rode de novo (a medida precisa do servidor sozinho)."
              % PORTA)
        return 2
    resultado = {"quando": time.strftime("%Y-%m-%d %H:%M"), "nucleos_logicos": os.cpu_count(),
                 "config_do_usuario": config_do_usuario()}

    print("1/5 - Tamanho do pacote (sem jogos, sem .git, sem backup)...", flush=True)
    total, por_pasta = tamanho_pasta(RAIZ, PASTAS_IGNORADAS_NO_TAMANHO)
    resultado["tamanho_total_mb"] = round(total / 1024 ** 2, 1)
    resultado["tamanho_por_pasta_mb"] = {k: round(v / 1024 ** 2, 1)
                                         for k, v in sorted(por_pasta.items(), key=lambda kv: -kv[1])}
    print("    %.1f MB" % resultado["tamanho_total_mb"], flush=True)

    print("2/5 - Linhas de cada arquivo...", flush=True)
    arquivos, por_grupo = contar_linhas()
    resultado["linhas_por_grupo"] = por_grupo
    resultado["linhas_por_arquivo"] = arquivos
    for grupo, dados in sorted(por_grupo.items()):
        print("    %-11s %4d arquivos, %6d linhas" % (grupo, dados["arquivos"], dados["linhas"]), flush=True)

    # A ordem segue o ARENA de verdade: a tela abre logo depois do servidor
    # (com o catalogo e as tarefas de abertura ainda correndo); so depois
    # vem o servidor parado sozinho.
    print("3/5 - Abrindo o servidor (sem a janela dele) e, logo em seguida, a tela...", flush=True)
    ambiente = dict(os.environ, ARENA_SEM_JANELA="1")
    inicio = time.monotonic()
    processo = subprocess.Popen([PYTHON, ARENA_PY], cwd=RAIZ, env=ambiente,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        pronto_em = None
        while time.monotonic() - inicio < 30:
            try:
                with urllib.request.urlopen(ENDERECO, timeout=0.5) as resposta:
                    if resposta.status == 200:
                        pronto_em = time.monotonic() - inicio
                        break
            except OSError:
                time.sleep(0.05)
        if pronto_em is None:
            resultado["erro"] = "o servidor nao respondeu em 30 s"
            print("    [ERRO] o servidor nao respondeu em 30 s", flush=True)
        else:
            resultado["servidor_abre_s"] = round(pronto_em, 2)
            resultado["espera_antes_da_janela_s"] = espera_antes_da_janela()
            print("    servidor respondeu em %.2f s; o ARENA espera mais %.1f s para abrir a janela"
                  % (pronto_em, resultado["espera_antes_da_janela_s"]), flush=True)
            pids = pids_descendentes(processo.pid)
            if "--sem-tela" not in sys.argv:
                print("4/5 - A tela (Edge em janela de aplicativo, perfil temporario)...", flush=True)
                tela = medir_tela(processo.pid)
                resultado["tela"] = tela
                if "erro" not in tela:
                    resultado["abertura_sem_a_espera_s"] = round(pronto_em + tela["navegador_s"] + tela["pagina_s"], 2)
                    resultado["abertura_total_s"] = round(resultado["abertura_sem_a_espera_s"]
                                                          + resultado["espera_antes_da_janela_s"], 2)
                    t = tela["tela"]
                    print("    abertura ate a tela pronta: %.2f s (%.2f s sem a espera de %.1f s)"
                          % (resultado["abertura_total_s"], resultado["abertura_sem_a_espera_s"],
                             resultado["espera_antes_da_janela_s"]), flush=True)
                    print("    tela: %.1f MB (%d processos), processador %.2f%% de um nucleo; servidor com a "
                          "tela: %.2f%%" % (t["ram_mb"], t["processos"], t["cpu_um_nucleo_pct"],
                                           tela["servidor_com_tela"]["cpu_um_nucleo_pct"]), flush=True)
                    pagina = tela["pagina"]
                    print("    temporizadores: %d setInterval vivos, %.1f setTimeout/min, %.1f quadros/s; "
                          "pedidos/min: %s" % (len(pagina.get("intervalos") or []), pagina["timeouts_por_minuto"],
                                               pagina["quadros_por_segundo"], pagina["pedidos_por_minuto"]),
                          flush=True)
                    # As portas com a tela aberta: a tela pode ter ligado alguma coisa.
                    resultado["portas_com_tela"] = portas(pids_descendentes(processo.pid))
            print("5/5 - Servidor sozinho: %d s para assentar e %d s parado..." % (ASSENTAR_S, JANELA_S), flush=True)
            time.sleep(ASSENTAR_S)
            resultado["servidor_parado"] = medir_parado({"servidor": pids}, JANELA_S)["servidor"]
            s = resultado["servidor_parado"]
            print("    processador %.2f%% de um nucleo; memoria %.1f MB; %d threads; %d alcas"
                  % (s["cpu_um_nucleo_pct"], s["ram_mb"], s["threads"], s["alcas"]), flush=True)
            resultado["portas"] = portas(pids)
            for p in resultado["portas"]:
                print("    porta %s %s %s: %s" % (p["protocolo"], p["endereco"], p["porta"], p["alcance"]), flush=True)
    finally:
        subprocess.run(["taskkill", "/PID", str(processo.pid), "/T", "/F"], capture_output=True)
        try:
            processo.wait(timeout=10)
        except subprocess.TimeoutExpired:
            pass

    os.makedirs(os.path.dirname(saida), exist_ok=True)
    with open(saida, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    print("\nResultado bruto salvo em", saida)
    return 0 if "erro" not in resultado else 1


if __name__ == "__main__":
    sys.exit(principal())
