# -*- coding: utf-8 -*-
r"""Medicoes do ARENA nesta maquina, para o perfil-alvo.

Mede, sozinho:
  1. abertura, pelo proprio ARENA.bat (como o aluno abre): ate a janela da
     tela aparecer (o "abrir que o aluno sente", teto 1a) e, do arena.py ate
     o servidor entregar os dados que a tela desenha (teto 1b); e quanta
     memoria do Windows isso consome (servidor + janela do navegador);
  2. servidor parado (depois de assentar, 30 s, tela aberta, ninguem
     mexendo) e em uso (20 s de pedidos): CPU, RAM, resposta;
  3. indexacao: tempo para reler a pasta de jogos, e quantos sao;
  4. gravacoes em disco por minuto com o ARENA parado (120 s);
  5. um jogo de Super Nintendo por ~70 s: quadros por segundo, regularidade
     dos quadros, CPU e RAM do RetroArch, e se a janela do jogo ficou a
     frente (janela coberta: o Windows segura o ritmo e o FPS nao vale).
No fim, perguntas rapidas sobre o que so uma pessoa olhando ve -- inclusive
como foram os consoles que ela ja jogou nesta maquina, para comparar com o
selo que o ARENA mostra.

Cada numero e' julgado pelos TETOS APROVADOS pelo Rafael em 30/09/2026
(docs\MAQUINA-ALVO.md, secao 7): o resumo termina na tabela "medido, teto,
passou ou nao".

Nao muda nada do ARENA: o jogo roda com as opcoes REAIS do ARENA, mas
geradas numa pasta temporaria, com saves e estados tambem temporarios.
O unico efeito e' o mesmo de abrir o ARENA e clicar em "Atualizar lista".

COMO O FPS E' MEDIDO (conferido na ajuda do proprio RetroArch 1.22.2 e na
documentacao da libretro, docs.libretro.com/guides/optimal-vsync):
  - "--max-frames=N" roda N quadros e fecha sozinho. Roda-se 60 quadros
    (so para medir o tempo de abrir e fechar) e depois 4200; FPS medio =
    (4200 - 60) / (tempo da longa - tempo da curta).
  - Com "--verbose", depois de 4096 quadros o RetroArch anota no registro
    "Average monitor Hz ... frame time deviation": a variacao do tempo de
    cada quadro. Por isso 4200 quadros (~70 s) e nao 60 s cravados.

Uso:
    servidor\python\python.exe ferramentas\medir_arena.py [pasta_de_saida]
"""
import ctypes
import datetime
import glob
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON = os.path.join(RAIZ, "servidor", "python", "python.exe")
ARENA_PY = os.path.join(RAIZ, "servidor", "arena.py")
ARENA_BAT = os.path.join(RAIZ, "ARENA.bat")
RETROARCH = os.path.join(RAIZ, "retroarch", "retroarch.exe")
ENDERECO = "http://127.0.0.1:8777"
NAO_MEDIU = "nao_foi_possivel_medir"
QUADROS_CURTO, QUADROS_LONGO = 60, 4200

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import coletar_maquina  # noqa: E402  (mesma pasta: codigo da maquina e memoria)


def falhou(motivo):
    return {NAO_MEDIU: True, "motivo": str(motivo)[:200]}


def etapa(texto):
    print("  - " + texto, flush=True)


# ---------------------------------------------------------------------------
# Medir um processo (CPU, RAM, gravacoes) sem administrador
# ---------------------------------------------------------------------------

class _IO(ctypes.Structure):
    _fields_ = [(n, ctypes.c_ulonglong) for n in (
        "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
        "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]


class _MEM(ctypes.Structure):
    _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong)] + [
        (n, ctypes.c_size_t) for n in (
            "PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
            "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage",
            "PagefileUsage", "PeakPagefileUsage")]


class Processo:
    """CPU, memoria e gravacoes de um processo, pelas funcoes do Windows que
    qualquer usuario pode chamar para os processos que ele mesmo abriu."""

    def __init__(self, pid):
        self.k = ctypes.WinDLL("kernel32", use_last_error=True)
        self.k.OpenProcess.restype = ctypes.c_void_p
        self.k.GetProcessTimes.argtypes = [ctypes.c_void_p] + [ctypes.POINTER(ctypes.c_ulonglong)] * 4
        self.k.GetProcessIoCounters.argtypes = [ctypes.c_void_p, ctypes.POINTER(_IO)]
        self.k.K32GetProcessMemoryInfo.argtypes = [ctypes.c_void_p, ctypes.POINTER(_MEM), ctypes.c_ulong]
        self.k.GetSystemTimePreciseAsFileTime.argtypes = [ctypes.POINTER(ctypes.c_ulonglong)]
        self.k.CloseHandle.argtypes = [ctypes.c_void_p]
        self.h = self.k.OpenProcess(0x1000, False, pid)   # QUERY_LIMITED_INFORMATION
        if not self.h:
            raise OSError("nao consegui abrir o processo %d" % pid)

    def cpu_s(self):
        t = [ctypes.c_ulonglong() for _ in range(4)]
        self.k.GetProcessTimes(self.h, *[ctypes.byref(x) for x in t])
        return (t[2].value + t[3].value) / 1e7        # kernel + usuario

    def ram_mb(self):
        m = _MEM()
        m.cb = ctypes.sizeof(m)
        self.k.K32GetProcessMemoryInfo(self.h, ctypes.byref(m), m.cb)
        return m.WorkingSetSize / 1024 ** 2, m.PeakWorkingSetSize / 1024 ** 2

    def gravacoes(self):
        io = _IO()
        self.k.GetProcessIoCounters(self.h, ctypes.byref(io))
        return io.WriteOperationCount, io.WriteTransferCount

    def idade_s(self):
        """Ha quantos segundos o processo foi criado (relogio do Windows)."""
        t = [ctypes.c_ulonglong() for _ in range(4)]
        self.k.GetProcessTimes(self.h, *[ctypes.byref(x) for x in t])
        agora = ctypes.c_ulonglong()
        self.k.GetSystemTimePreciseAsFileTime(ctypes.byref(agora))
        return (agora.value - t[0].value) / 1e7

    def fechar(self):
        self.k.CloseHandle(self.h)


class _ENTRADA_PROCESSO(ctypes.Structure):
    _fields_ = [("dwSize", ctypes.c_ulong), ("cntUsage", ctypes.c_ulong),
                ("th32ProcessID", ctypes.c_ulong), ("th32DefaultHeapID", ctypes.c_size_t),
                ("th32ModuleID", ctypes.c_ulong), ("cntThreads", ctypes.c_ulong),
                ("th32ParentProcessID", ctypes.c_ulong), ("pcPriClassBase", ctypes.c_long),
                ("dwFlags", ctypes.c_ulong), ("szExeFile", ctypes.c_wchar * 260)]


def processos_abertos():
    """{pid: (pid do pai, nome do .exe)} de todos os processos, pela "foto"
    de processos do Windows (CreateToolhelp32Snapshot, sem administrador)."""
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.CreateToolhelp32Snapshot.restype = ctypes.c_void_p
    k.CreateToolhelp32Snapshot.argtypes = [ctypes.c_ulong, ctypes.c_ulong]
    k.Process32FirstW.argtypes = [ctypes.c_void_p, ctypes.POINTER(_ENTRADA_PROCESSO)]
    k.Process32NextW.argtypes = [ctypes.c_void_p, ctypes.POINTER(_ENTRADA_PROCESSO)]
    k.CloseHandle.argtypes = [ctypes.c_void_p]
    foto = k.CreateToolhelp32Snapshot(0x2, 0)          # TH32CS_SNAPPROCESS
    if not foto or foto == ctypes.c_void_p(-1).value:
        return {}
    achados = {}
    try:
        e = _ENTRADA_PROCESSO()
        e.dwSize = ctypes.sizeof(e)
        ok = k.Process32FirstW(foto, ctypes.byref(e))
        while ok:
            achados[e.th32ProcessID] = (e.th32ParentProcessID, e.szExeFile.lower())
            ok = k.Process32NextW(foto, ctypes.byref(e))
    finally:
        k.CloseHandle(foto)
    return achados


def filho_chamado(pid_pai, exe):
    """Pid do processo 'exe' aberto por 'pid_pai' (ou None)."""
    for pid, (pai, nome) in processos_abertos().items():
        if pai == pid_pai and nome == exe:
            return pid
    return None


# ---------------------------------------------------------------------------
# Janelas: a tela do ARENA apareceu? A janela do jogo esta a frente?
# ---------------------------------------------------------------------------

NAVEGADORES_EXE = ("msedge.exe", "chrome.exe", "firefox.exe", "brave.exe", "opera.exe")


def _user32():
    u = ctypes.WinDLL("user32", use_last_error=True)
    u.IsWindowVisible.argtypes = [ctypes.c_void_p]
    u.GetWindowTextLengthW.argtypes = [ctypes.c_void_p]
    u.GetWindowTextW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_int]
    u.GetWindowThreadProcessId.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
    u.GetForegroundWindow.restype = ctypes.c_void_p
    u.PostMessageW.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p, ctypes.c_void_p]
    return u


def pid_da_janela(u, hwnd):
    pid = ctypes.c_ulong()
    u.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value


def janelas_do_arena():
    """Janelas visiveis de navegador com o titulo da tela do ARENA.

    O <title> do launcher\\index.html e' "ARENA", e o ARENA abre a tela como
    janela de aplicativo (--app) do Edge ou do Chrome: a janela ganha
    exatamente esse nome quando a pagina chega. So o nome EXATO conta: uma
    aba comum chamada "ARENA - Claude - ... - Microsoft Edge" (visto em
    01/10/2026, no PC do Rafael) nao e' a tela. A janela preta do ARENA.bat
    ("ARENA - servidor local") nao e' de navegador: o programa e' conferido."""
    u = _user32()
    exes = {pid: nome for pid, (_pai, nome) in processos_abertos().items()}
    achadas = set()
    TIPO = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    def cada(hwnd, _):
        if u.IsWindowVisible(hwnd):
            n = u.GetWindowTextLengthW(hwnd)
            if 0 < n < 200:
                texto = ctypes.create_unicode_buffer(n + 1)
                u.GetWindowTextW(hwnd, texto, n + 1)
                if texto.value.strip() == "ARENA":
                    if exes.get(pid_da_janela(u, hwnd)) in NAVEGADORES_EXE:
                        achadas.add(hwnd)
        return True
    u.EnumWindows(TIPO(cada), 0)
    return achadas


def fechar_janelas(janelas):
    """Pede para fechar (WM_CLOSE, como o X da janela)."""
    u = _user32()
    for hwnd in janelas:
        u.PostMessageW(hwnd, 0x0010, None, None)


def janela_da_frente_e_de(pid):
    u = _user32()
    hwnd = u.GetForegroundWindow()
    return bool(hwnd) and pid_da_janela(u, hwnd) == pid


def amostrar(proc, segundos, trabalho=None):
    """CPU media (% de UM nucleo e % da maquina) e RAM, durante 'segundos'.
    'trabalho' (opcional) roda em volta enquanto isso, e devolve uma lista."""
    ncpu = os.cpu_count() or 1
    cpu0, t0 = proc.cpu_s(), time.perf_counter()
    ram = []
    resultado_trabalho = []
    fim = t0 + segundos
    while time.perf_counter() < fim:
        if trabalho:
            resultado_trabalho.extend(trabalho())
        else:
            time.sleep(0.5)
        ram.append(proc.ram_mb()[0])
    duracao = time.perf_counter() - t0
    cpu = proc.cpu_s() - cpu0
    return {"segundos": round(duracao, 1),
            "cpu_pct_de_um_nucleo": round(100 * cpu / duracao, 1),
            "cpu_pct_da_maquina": round(100 * cpu / duracao / ncpu, 2),
            "ram_mb": round(statistics.mean(ram), 1) if ram else NAO_MEDIU}, resultado_trabalho


# ---------------------------------------------------------------------------
# Conversa com o servidor
# ---------------------------------------------------------------------------

def pedir(caminho, corpo=None, limite=60):
    dados = json.dumps(corpo).encode() if corpo is not None else None
    req = urllib.request.Request(ENDERECO + caminho, data=dados,
                                 method="POST" if dados is not None else "GET",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=limite) as r:
        return json.loads(r.read())


def porta_ocupada():
    import socket
    s = socket.socket()
    s.settimeout(0.5)
    try:
        return s.connect_ex(("127.0.0.1", 8777)) == 0
    finally:
        s.close()


def porta_responde():
    """O servidor ja aceita conexao? Tentativa CURTA de proposito: no Windows,
    conectar numa porta fechada do proprio computador leva ~1 s (o Windows
    insiste antes de desistir), e o cronometro da abertura ficaria com esse
    "relogio" grosso."""
    import socket
    s = socket.socket()
    s.settimeout(0.1)
    try:
        return s.connect_ex(("127.0.0.1", 8777)) == 0
    except OSError:
        return False
    finally:
        s.close()


def medir_servidor(dados):
    """Etapas 1 a 4. Abre o ARENA pelo ARENA.bat, de verdade, e fecha no fim."""
    if porta_ocupada():
        motivo = "o ARENA ja estava aberto -- feche a janela preta e rode de novo"
        for chave in ("abertura", "servidor", "indexacao", "gravacoes_parado"):
            dados[chave] = falhou(motivo)
        print("  ! " + motivo)
        return

    etapa("abrindo o ARENA pelo ARENA.bat (como o aluno abre)")
    memoria_antes = coletar_maquina.memoria_agora()["livre_mb"]
    janelas_antes = janelas_do_arena()
    saida = open(os.path.join(PASTA, "arena_janela_preta.txt"), "w", encoding="utf-8", errors="replace")
    inicio = time.perf_counter()
    # Sem janela propria (CREATE_NO_WINDOW): o "title" do .bat mudaria o
    # nome da janela do COLETAR, e o "pause" do fim sai sozinho (sem teclado).
    bat = subprocess.Popen(["cmd.exe", "/d", "/c", ARENA_BAT], cwd=RAIZ, stdin=subprocess.DEVNULL,
                           stdout=saida, stderr=subprocess.STDOUT,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    novas = set()
    try:
        # Tres coisas ao mesmo tempo: achar o Python que o .bat abriu, o
        # servidor responder (os pedidos vao numa linha a parte, para nao
        # atrasar o resto) e a janela da tela aparecer.
        marcas = {}

        def pedir_dados():
            try:
                urllib.request.urlopen(ENDERECO + "/", timeout=30).read()
                marcas["responde"] = time.perf_counter() - inicio
                pedir("/api/estado")
                pedir("/api/catalogo")
                marcas["dados"] = time.perf_counter() - inicio
            except Exception as falha:
                marcas["falha"] = str(falha)[:200]

        import threading
        pedidos = None
        python_pid, janela = None, None
        while time.perf_counter() - inicio < 120:
            if python_pid is None:
                python_pid = filho_chamado(bat.pid, "python.exe")
            if pedidos is None and porta_responde():
                pedidos = threading.Thread(target=pedir_dados, daemon=True)
                pedidos.start()
            if janela is None:
                novas = janelas_do_arena() - janelas_antes
                if novas:
                    janela = time.perf_counter() - inicio
            prontos = pedidos is not None and not pedidos.is_alive()
            if prontos and (janela is not None or time.perf_counter() - inicio - marcas.get("dados", 0) > 60):
                break       # a janela nao veio em 60 s depois dos dados: segue sem ela
            if bat.poll() is not None:
                break
            time.sleep(0.05)
        if pedidos is not None:
            pedidos.join(30)
        if "dados" not in marcas:
            dados["abertura"] = falhou(marcas.get("falha") or "o servidor nao respondeu em 120 s "
                                       "(veja arena_janela_preta.txt)")
            return
        if not python_pid:
            dados["abertura"] = falhou("nao achei o Python que o ARENA.bat abriu")
            return
        proc = Processo(python_pid)
        # Quando o .bat chamou o Python (relogio do Windows): separa o tempo
        # das conferencias do .bat do tempo do servidor (teto 1b).
        python_nasceu = (time.perf_counter() - inicio) - proc.idade_s()
        espera = marcas["dados"] + 10 - (time.perf_counter() - inicio)
        if espera > 0:
            time.sleep(espera)  # a janela do navegador abrir e assentar
        memoria_depois = coletar_maquina.memoria_agora()["livre_mb"]
        dados["abertura"] = {
            "janela_da_tela_s": round(janela, 2) if janela is not None else falhou(
                "a janela da tela nao apareceu (navegador nao achado, ou titulo diferente de 'ARENA')"),
            "bat_ate_o_python_s": round(max(0.0, python_nasceu), 2),
            "servidor_responde_s": round(marcas["responde"] - python_nasceu, 2),
            "dados_da_tela_prontos_s": round(marcas["dados"] - python_nasceu, 2),
            "memoria_consumida_mb": memoria_antes - memoria_depois,
            "nota": "janela_da_tela = do ARENA.bat ate a janela do navegador ganhar o titulo "
                    "ARENA (a pagina chegou; a lista e as capas vem logo depois). servidor_responde "
                    "e dados_da_tela_prontos contam do Python aberto pelo .bat. memoria_consumida "
                    "= RAM livre do Windows antes - depois (servidor + janela do navegador).",
        }

        # Espera o servidor ASSENTAR antes de medir o parado. Achado de
        # 30/09/2026: o Celeron mediu 8,4% de um nucleo "parado" contra
        # 0,01% no i5; comecar a contar 10 s depois da abertura pode pegar
        # trabalho de abrir (a tela carregando, a primeira volta do vigia).
        # Fatias de 5 s ate uma ficar abaixo de 1% de um nucleo (no maximo
        # 90 s); o que gastou ate ali vira "custo de assentar". As fatias
        # ficam guardadas: sao a mesma curva do ferramentas\medir_parado.py,
        # sem precisar rodar outra ferramenta.
        etapa("esperando o servidor assentar (ate 90 s)")
        assentar = {"segundos": None, "cpu_s_de_um_nucleo": 0.0, "fatias_pct_de_um_nucleo": []}
        t_assentar, cpu_assentar = time.perf_counter(), proc.cpu_s()
        while time.perf_counter() - t_assentar < 90:
            fatia, _ = amostrar(proc, 5)
            assentar["fatias_pct_de_um_nucleo"].append(fatia["cpu_pct_de_um_nucleo"])
            if fatia["cpu_pct_de_um_nucleo"] < 1.0:
                assentar["segundos"] = round(time.perf_counter() - t_assentar, 1)
                break
        assentar["cpu_s_de_um_nucleo"] = round(proc.cpu_s() - cpu_assentar, 2)
        if assentar["segundos"] is None:
            assentar["nao_assentou_em_90_s"] = True
        etapa("servidor parado (30 s)")
        parado, _ = amostrar(proc, 30)
        parado["assentar"] = assentar

        etapa("servidor em uso (20 s de pedidos seguidos)")

        def rodada():
            tempos = []
            for rota in ("/api/estado", "/api/catalogo", "/api/ranking", "/api/conquistas"):
                t = time.perf_counter()
                try:
                    pedir(rota)
                    tempos.append((time.perf_counter() - t) * 1000)
                except Exception:
                    tempos.append(None)
            return tempos
        em_uso, tempos = amostrar(proc, 20, rodada)
        validos = sorted(t for t in tempos if t is not None)
        em_uso["pedidos"] = len(tempos)
        em_uso["falhas"] = len(tempos) - len(validos)
        if validos:
            em_uso["resposta_media_ms"] = round(statistics.mean(validos), 1)
            em_uso["resposta_p95_ms"] = round(validos[int(len(validos) * 0.95) - 1], 1)
        dados["servidor"] = {"parado": parado, "em_uso": em_uso,
                             "ram_pico_mb": round(proc.ram_mb()[1], 1)}

        etapa("indexacao (o mesmo que o botao Atualizar lista)")
        t = time.perf_counter()
        resposta = pedir("/api/indexar", {}, limite=600)
        segundos = time.perf_counter() - t
        jogos = pedir("/api/catalogo").get("jogos", [])
        por_console = {}
        for j in jogos:
            por_console[j.get("plataforma", "?")] = por_console.get(j.get("plataforma", "?"), 0) + 1
        dados["indexacao"] = {"segundos": round(segundos, 2),
                              "total": resposta.get("total", len(jogos)),
                              "por_console": dict(sorted(por_console.items()))}

        etapa("gravacoes em disco com o ARENA parado (120 s)")
        pasta_dados = os.path.join(RAIZ, "dados")

        def datas():
            achadas = {}
            for atual, _s, arquivos in os.walk(pasta_dados):
                for n in arquivos:
                    try:
                        achadas[os.path.join(atual, n)] = os.path.getmtime(os.path.join(atual, n))
                    except OSError:
                        pass
            return achadas
        antes, datas_antes = proc.gravacoes(), datas()
        time.sleep(120)
        depois, datas_depois = proc.gravacoes(), datas()
        mudaram = sorted(os.path.relpath(c, RAIZ) for c, d in datas_depois.items()
                         if datas_antes.get(c) != d)
        dados["gravacoes_parado"] = {
            "janela_s": 120,
            "por_minuto": round((depois[0] - antes[0]) / 2, 1),
            "kb_por_minuto": round((depois[1] - antes[1]) / 1024 / 2, 1),
            "arquivos_de_dados_que_mudaram": mudaram,
        }
        proc.fechar()
    except Exception as falha:
        for chave in ("abertura", "servidor", "indexacao", "gravacoes_parado"):
            dados.setdefault(chave, falhou(falha))
    finally:
        # A janela da tela primeiro (senao ela fica aberta mostrando "nao foi
        # possivel conectar"), depois o .bat com tudo o que ele abriu.
        try:
            fechar_janelas(novas | (janelas_do_arena() - janelas_antes))
        except Exception:
            pass
        subprocess.run(["taskkill", "/PID", str(bat.pid), "/T", "/F"], capture_output=True)
        saida.close()


# ---------------------------------------------------------------------------
# Jogo de Super Nintendo
# ---------------------------------------------------------------------------

def e_satellaview(caminho):
    """Jogo de Satellaview (BS-X): transmitido por satelite no Japao, precisa
    da BIOS do BS-X e o snes9x recusa sem ela ("ROM loading failed")."""
    nome = os.path.basename(caminho).lower()
    return nome.startswith("bs ") or "satellaview" in nome or "(bs)" in nome


def jogo_carregou(texto_do_registro):
    """O registro do RetroArch mostra que o jogo abriu de verdade?"""
    falhas = ("ROM loading failed", "Falha ao carregar o conte", "Failed to load content")
    return bool(texto_do_registro) and not any(f in texto_do_registro for f in falhas)


def achar_jogo_snes():
    """Jogos de SNES da pasta, do menor para o maior (carrega mais rapido; o
    que se mede e' a maquina, nao o jogo), SEM os de Satellaview.

    Achado de 30/09/2026: antes pegava so o menor, que nesta pasta passou a
    ser o "BS F-ZERO (J)" -- de Satellaview -- quando ele entrou, em 26/09.
    O RetroArch fechava em 1 s sem abrir o jogo, a conta dava 4.140.000
    quadros por segundo e o resumo ainda marcava [BOM]. As coletas da
    escola (27 e 28/09) nao mediram o FPS do SNES; a referencia do Ryzen
    (25/09) foi antes e vale. Devolve (snes, lista); quem mede tenta um
    por um."""
    with open(os.path.join(RAIZ, "servidor", "consoles.json"), encoding="utf-8") as f:
        consoles = json.load(f)
    lista = consoles if isinstance(consoles, list) else consoles.get("plataformas", [])
    snes = next((p for p in lista if p.get("id") == "snes"), None)
    if not snes:
        return None, None
    pasta = os.path.join(RAIZ, "jogos", "pessoais", snes.get("pasta", "Super Nintendo"))
    extensoes = tuple("." + e.lstrip(".").lower() for e in snes.get("extensoes", ["sfc", "smc"]))
    candidatos = [c for c in glob.glob(os.path.join(pasta, "*"))
                  if os.path.isfile(c) and c.lower().endswith(extensoes)]
    # Versao europeia (PAL) roda a 50 quadros por segundo, nao 60: medida
    # assim nao compara com a regua. Vai para o fim da fila.
    candidatos = sorted((c for c in candidatos if not e_satellaview(c)),
                        key=lambda c: (e_pal(c), os.path.getsize(c)))
    return snes, candidatos


def e_pal(caminho):
    """Versao europeia do jogo (50 Hz): (E), (Europe), (Germany)..."""
    nome = os.path.basename(caminho).lower()
    return any(marca in nome for marca in (
        "(e)", "(europe", "(eur", "(germany", "(france", "(spain", "(italy", "(uk)", "(pal"))


def rodar_quadros(core, opcoes_cfg, extra_cfg, jogo, quadros, log):
    """Roda o jogo N quadros; devolve (segundos, amostras de CPU/RAM)."""
    comando = [RETROARCH, "-L", core, "--appendconfig", opcoes_cfg + "|" + extra_cfg,
               "--max-frames=%d" % quadros, "--verbose", "--log-file=" + log, jogo]
    inicio = time.perf_counter()
    p = subprocess.Popen(comando, cwd=RAIZ, stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    amostras = []
    try:
        proc = Processo(p.pid)
        ncpu = os.cpu_count() or 1
        ultimo_cpu, ultimo_t = proc.cpu_s(), time.perf_counter()
        while p.poll() is None:
            time.sleep(1)
            if p.poll() is not None:
                break
            agora_cpu, agora_t = proc.cpu_s(), time.perf_counter()
            try:
                a_frente = janela_da_frente_e_de(p.pid)
            except Exception:
                a_frente = None
            amostras.append((100 * (agora_cpu - ultimo_cpu) / (agora_t - ultimo_t) / ncpu,
                             proc.ram_mb()[0], a_frente))
            ultimo_cpu, ultimo_t = agora_cpu, agora_t
            if agora_t - inicio > quadros / 60 * 4 + 60:
                p.kill()          # travou: nunca deixa a coleta presa
                raise OSError("o jogo nao terminou os %d quadros a tempo" % quadros)
        proc.fechar()
    except OSError:
        if p.poll() is None:
            p.kill()
        raise
    return time.perf_counter() - inicio, amostras


def medir_jogo(dados):
    etapa("jogo de Super Nintendo (~70 s, com imagem e som -- pode olhar)")
    snes, candidatos = achar_jogo_snes()
    core = os.path.join(RAIZ, "retroarch", "cores", (snes or {}).get("core", "snes9x_libretro.dll"))
    if not candidatos:
        dados["jogo"] = falhou("nenhum jogo de Super Nintendo na pasta jogos\\pessoais "
                               "(os de Satellaview, 'BS ...', nao servem)")
        return
    if not (os.path.isfile(RETROARCH) and os.path.isfile(core)):
        dados["jogo"] = falhou("RetroArch ou nucleo do Super Nintendo ausente")
        return

    temp = tempfile.mkdtemp(prefix="arena_medir_jogo_")
    try:
        # As opcoes REAIS do ARENA para este jogo, geradas numa pasta
        # temporaria: o gravar_override e o arquivo de opcoes dos nucleos
        # leem o caminho de destino na hora, entao basta apontar os dois
        # para ca. Os arquivos do ARENA nao sao tocados.
        arena = coletar_maquina.carregar_arena()
        import graficos
        arena.ARQUIVO_OVERRIDE = os.path.join(temp, "arena_override.cfg")
        graficos.ARQUIVO_OPCOES_CORE = os.path.join(temp, "retroarch-core-options.cfg")
        config = arena.carregar_config()
        graficos.gravar_opcoes_dos_nucleos(arena.CAPACIDADE["nota"], None,
                                           arena.CAPACIDADE.get("nota_gpu"),
                                           modesto=bool(config.get("modo_modesto")))
        opcoes_cfg = arena.gravar_override(config, (snes or {}).get("custo"))

        extra_cfg = os.path.join(temp, "medicao.cfg")
        with open(extra_cfg, "w", encoding="utf-8") as f:
            f.write('savefile_directory = "%s"\nsavestate_directory = "%s"\n'
                    'screenshot_directory = "%s"\nconfig_save_on_exit = "false"\n'
                    'network_cmd_enable = "false"\nsavestate_auto_save = "false"\n'
                    'savestate_auto_load = "false"\n'
                    # As opcoes do ARENA deixam o registro curto; a linha da
                    # variacao dos quadros so sai com o registro detalhado.
                    'log_verbosity = "true"\nfrontend_log_level = "0"\n' % (temp, temp, temp))

        # A rodada curta tambem serve de prova: so segue com o jogo que o
        # registro mostra que abriu. Tenta ate 3 da lista.
        jogo, curto, recusados = None, None, []
        for candidato in candidatos[:3]:
            log_curto = os.path.join(temp, "curto.log")
            if os.path.isfile(log_curto):
                os.remove(log_curto)
            segundos, _ = rodar_quadros(core, opcoes_cfg, extra_cfg, candidato,
                                        QUADROS_CURTO, log_curto)
            texto_curto = (open(log_curto, encoding="utf-8", errors="replace").read()
                           if os.path.isfile(log_curto) else "")
            if jogo_carregou(texto_curto):
                jogo, curto = candidato, segundos
                break
            recusados.append(os.path.basename(candidato))
        if not jogo:
            dados["jogo"] = falhou("o RetroArch nao conseguiu abrir nenhum destes jogos: %s"
                                   % ", ".join(recusados))
            return

        log = os.path.join(temp, "longo.log")
        longo, amostras = rodar_quadros(core, opcoes_cfg, extra_cfg, jogo, QUADROS_LONGO, log)
        texto = open(log, encoding="utf-8", errors="replace").read() if os.path.isfile(log) else ""
        # 4200 quadros a 60 por segundo sao ~70 s. Se a rodada longa nao
        # durou nem 30 s a mais que a curta, o jogo fechou antes da hora:
        # nao ha FPS para contar (nunca mais um 4.140.000 marcado [BOM]).
        if not jogo_carregou(texto) or (longo - curto) < 30:
            dados["jogo"] = falhou("a rodada longa fechou antes da hora (%.1f s; "
                                   "esperado ~70 s)" % longo)
            return

        resultado = {"jogo": os.path.basename(jogo), "modo_modesto": bool(config.get("modo_modesto")),
                     "quadros": QUADROS_LONGO,
                     "fps_medio": round((QUADROS_LONGO - QUADROS_CURTO) / (longo - curto), 1),
                     "tempo_de_abrir_s": round(curto, 1)}
        if recusados:
            resultado["jogos_que_nao_abriram"] = recusados
        cpu = [a[0] for a in amostras[2:]] or [a[0] for a in amostras]
        ram = [a[1] for a in amostras]
        if cpu:
            resultado["cpu_media_pct_da_maquina"] = round(statistics.mean(cpu), 1)
            resultado["cpu_pico_pct_da_maquina"] = round(max(cpu), 1)
        if ram:
            resultado["ram_pico_mb"] = round(max(ram), 1)
        # Regra 8 do MAQUINA-ALVO.md: FPS so vale com a janela do jogo a
        # vista. Janela coberta, o Windows segura o ritmo (achado de 30/09:
        # 51,7 FPS no Ryzen com o Rafael usando o navegador por cima).
        frente = [a[2] for a in amostras if a[2] is not None]
        if frente:
            resultado["janela_do_jogo_a_frente_pct"] = round(100.0 * sum(frente) / len(frente))
        m = re.search(r"Average monitor Hz:\s*([\d.]+)\s*Hz\.\s*\(([\d.]+)\s*%\s*frame time deviation", texto)
        if m:
            resultado["monitor_hz_medido"] = float(m.group(1))
            resultado["variacao_dos_quadros_pct"] = float(m.group(2))
        else:
            resultado["variacao_dos_quadros_pct"] = falhou("o RetroArch nao anotou a variacao no registro")
        # O registro nao escreve "driver X": o motor aparece na etiqueta de
        # cada linha ([Vulkan], [D3D11], [GL]...).
        motores = {"[Vulkan]": "vulkan", "[D3D12]": "d3d12", "[D3D11]": "d3d11",
                   "[D3D10]": "d3d10", "[D3D9]": "d3d9", "[GL]": "gl", "[WGL]": "gl", "[GDI]": "gdi"}
        achados = [(texto.find(etiqueta), nome) for etiqueta, nome in motores.items() if etiqueta in texto]
        resultado["driver_de_video"] = min(achados)[1] if achados else NAO_MEDIU
        # "Game FPS > Monitor FPS": o jogo quer um pouco mais de 60 quadros
        # que o monitor mostra. Normal no SNES (60,10); anotado para leitura.
        resultado["jogo_mais_rapido_que_o_monitor"] = "Game FPS > Monitor FPS" in texto
        # FPS abaixo do piso: e' a maquina ou a SAIDA DE SOM? Achado de
        # 02/10/2026 neste Ryzen: 52 FPS e 22% de variacao com o som num
        # headset sem fio (desligado de madrugada) -- o RetroArch segue o
        # ritmo em que a placa de som consome o audio, e o receptor do
        # headset consumia devagar. Sem a sincronia pelo som: 60,1 FPS. Mede
        # de novo assim (so quando sai baixo) e anota qual dos dois foi.
        if resultado["fps_medio"] < TETOS["6a"]["teto"]:
            sem_som_cfg = os.path.join(temp, "medicao_sem_sincronia_do_som.cfg")
            with open(extra_cfg, encoding="utf-8") as origem, open(sem_som_cfg, "w", encoding="utf-8") as f:
                f.write(origem.read() + 'audio_sync = "false"\n')
            curto2, _ = rodar_quadros(core, opcoes_cfg, sem_som_cfg, jogo, QUADROS_CURTO,
                                      os.path.join(temp, "curto_sem_som.log"))
            longo2, _ = rodar_quadros(core, opcoes_cfg, sem_som_cfg, jogo, QUADROS_LONGO,
                                      os.path.join(temp, "longo_sem_som.log"))
            if longo2 - curto2 >= 30:
                fps2 = round((QUADROS_LONGO - QUADROS_CURTO) / (longo2 - curto2), 1)
                resultado["fps_sem_sincronia_pelo_som"] = fps2
                resultado["som_segura_o_ritmo"] = fps2 >= TETOS["6a"]["teto"]
        dados["jogo"] = resultado
    except Exception as falha:
        dados["jogo"] = falhou(falha)
    finally:
        shutil.rmtree(temp, ignore_errors=True)


# ---------------------------------------------------------------------------
# Perguntas (o que so uma pessoa olhando ve)
# ---------------------------------------------------------------------------

PERGUNTAS = [
    ("tela_inteira", "A tela do ARENA abriu inteira, com a lista de jogos?", {"s": "sim", "n": "nao", "x": "nao vi"}),
    ("tempo_tela", "Quanto tempo ate a LISTA DE JOGOS aparecer? (o teto e' 10 s)",
     {"1": "menos de 5 s", "2": "de 5 a 10 s", "3": "mais de 10 s", "x": "nao vi"}),
    ("som_picotou", "No jogo de Super Nintendo, o som picotou ou chiou?", {"s": "sim", "n": "nao", "x": "nao ouvi"}),
    ("imagem_engasgou", "A imagem do jogo engasgou ou ficou lenta?", {"s": "sim", "n": "nao", "x": "nao vi"}),
    ("controle", "Se tinha controle ou teclado a mao: respondeu na hora?",
     {"s": "sim", "n": "nao", "x": "nao testei"}),
]

# Consoles pesados, em que o selo do ARENA mais precisa acertar. A resposta
# de quem jogou de verdade NESTA maquina e' o que calibra a avaliacao
# (arena.classificar_plataforma): sem isso, a regua e' so estimativa.
CONSOLES_PERGUNTADOS = [
    ("ps2", "PlayStation 2"), ("gamecube", "GameCube"), ("wii", "Wii"),
    ("psp", "PSP"), ("n64", "Nintendo 64"), ("ps1", "PlayStation 1"),
    ("dreamcast", "Dreamcast"), ("saturn", "Saturn"), ("nds", "Nintendo DS"),
    ("ps3", "PlayStation 3"), ("xbox360", "Xbox 360"),
]
OPCOES_CONSOLE = {"b": "rodou bem", "e": "rodou com engasgos", "t": "travou ou lento demais",
                  "n": "nao abriu", "x": "nao testei"}


def _perguntar(texto, opcoes):
    legenda = "  ".join("[%s] %s" % (k, v) for k, v in opcoes.items())
    while True:
        try:
            r = input("  %s\n     %s\n     > " % (texto, legenda)).strip().lower()
        except (EOFError, KeyboardInterrupt):
            r = "x" if "x" in opcoes else list(opcoes)[-1]
        if r in opcoes:
            return opcoes[r]
        print("     (digite so uma das letras entre colchetes)")


def perguntar(dados):
    if not sys.stdin or not sys.stdin.isatty():
        dados["respostas"] = "ninguem no teclado: perguntas puladas"
        return
    print()
    print("Faltam so %d perguntas rapidas (uma tecla e Enter):" % (len(PERGUNTAS) + 1))
    respostas = {}
    for chave, texto, opcoes in PERGUNTAS:
        respostas[chave] = _perguntar(texto, opcoes)
    jogou = _perguntar("Ja jogou outro console NESTE notebook (PS2, PSP, GameCube...)?",
                       {"s": "sim", "n": "nao"})
    if jogou == "sim":
        print("  Para cada console, como foi NESTE notebook:")
        consoles = {}
        for chave, nome in CONSOLES_PERGUNTADOS:
            consoles[chave] = _perguntar(nome, OPCOES_CONSOLE)
        respostas["consoles"] = consoles
    dados["respostas"] = respostas


# ---------------------------------------------------------------------------
# O que o ARENA diz de cada console x o que a pessoa viu
# ---------------------------------------------------------------------------

def etiquetas_do_arena():
    """{id: {rotulo, etiqueta}} com o MESMO codigo do selo da tela."""
    try:
        arena = coletar_maquina.carregar_arena()
        return {p["id"]: {"etiqueta": p.get("classe"), "rotulo": p.get("classe_rotulo"),
                          "estado": p.get("estado")}
                for p in arena.avaliar_plataformas(forcar=True)}
    except Exception as falha:
        return falhou(falha)


# Para cada selo, as respostas que mostram o ARENA errando -- e para que lado.
DISCORDANCIAS = {
    "bem": {"travou ou lento demais": "otimista demais", "nao abriu": "otimista demais",
            "rodou com engasgos": "um pouco otimista"},
    "ajustes": {"travou ou lento demais": "otimista", "nao abriu": "otimista demais"},
    "pesado": {"rodou bem": "pessimista"},
    "nao_abre": {"rodou bem": "errou: abriu", "rodou com engasgos": "errou: abriu",
                 "travou ou lento demais": "errou: abriu"},
}


def comparar_consoles(etiquetas, respostas):
    """Lista de {console, arena_diz, voce_viu, leitura} para os consoles que a
    pessoa disse ter testado. Vazia se nao testou nenhum."""
    if not isinstance(etiquetas, dict) or etiquetas.get(NAO_MEDIU):
        return []
    vistos = (respostas or {}).get("consoles") if isinstance(respostas, dict) else None
    saida = []
    for chave, nome in CONSOLES_PERGUNTADOS:
        viu = (vistos or {}).get(chave)
        if not viu or viu == "nao testei" or chave not in etiquetas:
            continue
        selo = etiquetas[chave]
        leitura = DISCORDANCIAS.get(selo.get("etiqueta"), {}).get(viu, "concorda")
        saida.append({"console": nome, "arena_diz": selo.get("rotulo"), "voce_viu": viu,
                      "leitura": leitura})
    return saida


# ---------------------------------------------------------------------------
# Tetos (orcamentos) APROVADOS pelo Rafael em 30/09/2026
# ---------------------------------------------------------------------------
# A regua oficial: docs\MAQUINA-ALVO.md, secao 7. Os numeros valem para o
# notebook-alvo (Celeron N5100); numa maquina mais forte e' normal passar
# com folga. Mudou o teto la? Muda aqui tambem.

TETOS = {
    "1a": {"item": "Abertura sentida (ARENA.bat ate a janela da tela)", "teto": 10.0, "unidade": "s"},
    "1b": {"item": "Abertura do servidor (arena.py ate os dados da tela)", "teto": 2.3, "unidade": "s"},
    "2": {"item": "Memoria do servidor (pico)", "teto": 64.0, "unidade": "MB"},
    "3": {"item": "Processador parado (de UM nucleo)", "teto": 2.0, "unidade": "%"},
    "4": {"item": "Indexacao (1,9 s por 100 jogos)", "teto": 1.9, "unidade": "s"},
    "5a": {"item": "Gravacoes com o ARENA parado (por minuto)", "teto": 0.5, "unidade": "/min"},
    "5b": {"item": "Gravacoes com o ARENA parado (volume)", "teto": 16.0, "unidade": "KB/min"},
    "6a": {"item": "FPS do Super Nintendo (piso)", "teto": 59.0, "unidade": "FPS", "piso": True},
    "6b": {"item": "Variacao dos quadros no SNES", "teto": 5.0, "unidade": "%"},
}


def teto_da_indexacao(total):
    """1,9 s por 100 jogos. Abaixo de 100 jogos fica em 1,9 s: o custo fixo
    de olhar as pastas dos consoles nao encolhe com a colecao."""
    return round(TETOS["4"]["teto"] * max(1.0, (total or 0) / 100.0), 2)


def _numero(valor):
    return valor if isinstance(valor, (int, float)) and not isinstance(valor, bool) else None


def orcamentos(d):
    """A tabela que o Rafael pediu: item, medido, teto, passou ou nao."""
    a = d.get("abertura") or {}
    s = d.get("servidor") or {}
    i = d.get("indexacao") or {}
    g = d.get("gravacoes_parado") or {}
    j = d.get("jogo") or {}
    parado = (s.get("parado") or {}) if isinstance(s, dict) else {}
    medidos = {
        "1a": a.get("janela_da_tela_s"),
        "1b": a.get("dados_da_tela_prontos_s"),
        "2": s.get("ram_pico_mb"),
        "3": parado.get("cpu_pct_de_um_nucleo"),
        "4": i.get("segundos"),
        "5a": g.get("por_minuto"),
        "5b": g.get("kb_por_minuto"),
        "6a": j.get("fps_medio"),
        "6b": j.get("variacao_dos_quadros_pct"),
    }
    linhas = []
    for chave, regra in TETOS.items():
        teto = teto_da_indexacao(i.get("total")) if chave == "4" else regra["teto"]
        medido = _numero(medidos[chave])
        if medido is None:
            passou = None
        elif regra.get("piso"):
            passou = medido >= teto
        else:
            passou = medido <= teto
        linhas.append({"chave": chave, "item": regra["item"], "unidade": regra["unidade"],
                       "medido": medido, "teto": teto, "piso": bool(regra.get("piso")),
                       "passou": passou})
    return linhas


def selo(linha):
    if linha["passou"] is None:
        return "nao medido"
    if linha["passou"]:
        return "PASSOU"
    return "ABAIXO DO PISO" if linha["piso"] else "ESTOUROU"


# ---------------------------------------------------------------------------
# Resumo em portugues
# ---------------------------------------------------------------------------

def _v(valor):
    if isinstance(valor, dict) and valor.get(NAO_MEDIU):
        return "nao foi possivel medir (%s)" % valor.get("motivo", "")
    return valor


def _br(numero):
    """3.5 -> "3,5" (o resumo e' lido por gente, em portugues)."""
    return str(numero).replace(".", ",") if isinstance(numero, (int, float)) else str(numero)


def escrever_resumo(d):
    tabela = {linha["chave"]: linha for linha in d.get("orcamentos") or orcamentos(d)}

    def contra(chave):
        linha = tabela.get(chave)
        if not linha:
            return ""
        return "  [%s; %s %s %s]" % (selo(linha), "piso" if linha["piso"] else "teto",
                                     _br(linha["teto"]), linha["unidade"])

    L = ["MEDICOES DO ARENA NESTA MAQUINA",
         "Codigo da maquina: %s    Medido em: %s" % (d["codigo_maquina"], d["medido_em"])]
    e = d.get("energia") or {}
    if e.get("na_tomada") is False:
        L.append("! MEDIDO NA BATERIA (%s%%): os numeros de desempenho NAO decidem nada "
                 "(MAQUINA-ALVO.md, regra 8). Repita na tomada." % e.get("bateria_pct", "?"))
    L.append("")
    a = d.get("abertura", {})
    L.append("ABRIR O ARENA (pelo ARENA.bat, como o aluno abre)")
    if a.get(NAO_MEDIU):
        L.append("  " + str(_v(a)))
    else:
        janela = a.get("janela_da_tela_s")
        L.append("  janela da tela apareceu em %s s%s" % (
            _br(janela) if not isinstance(janela, dict) else _v(janela), contra("1a")))
        L.append("    (a lista e as capas vem logo depois; o .bat levou %s s ate abrir o Python)"
                 % _br(a.get("bat_ate_o_python_s", "?")))
        L.append("  servidor respondeu em %s s" % _br(a["servidor_responde_s"]))
        L.append("  dados da tela prontos em %s s%s" % (_br(a["dados_da_tela_prontos_s"]), contra("1b")))
        L.append("  memoria que o ARENA tomou do Windows: %s MB  [sem teto: acompanhar]"
                 % a["memoria_consumida_mb"])
    L.append("")
    s = d.get("servidor", {})
    L.append("SERVIDOR")
    if s.get(NAO_MEDIU):
        L.append("  " + str(_v(s)))
    else:
        p, u = s["parado"], s["em_uso"]
        ass = p.get("assentar") or {}
        if ass:
            L.append("  assentou em %s s depois da tela pronta (gastou %s s de processador ate ali)" % (
                _br(ass.get("segundos")) if ass.get("segundos") is not None else "mais de 90",
                _br(ass.get("cpu_s_de_um_nucleo", "?"))))
            fatias = ass.get("fatias_pct_de_um_nucleo") or []
            if len(fatias) > 1:
                L.append("    curva (%% de um nucleo, a cada 5 s): %s" % ", ".join(_br(f) for f in fatias))
        L.append("  parado: %s%% de um nucleo (%s%% da maquina)%s" % (
            _br(p["cpu_pct_de_um_nucleo"]), _br(p["cpu_pct_da_maquina"]), contra("3")))
        L.append("  memoria: %s MB parado, pico %s MB%s" % (_br(p["ram_mb"]), _br(s.get("ram_pico_mb")),
                                                          contra("2")))
        L.append("  em uso: %s%% da maquina, %s pedidos, resposta media %s ms, pior 5%% %s ms"
                 "  [sem teto: acompanhar]" % (
                     _br(u["cpu_pct_da_maquina"]), u["pedidos"], _br(u.get("resposta_media_ms", "?")),
                     _br(u.get("resposta_p95_ms", "?"))))
    L.append("")
    i = d.get("indexacao", {})
    L.append("LISTA DE JOGOS")
    if i.get(NAO_MEDIU):
        L.append("  " + str(_v(i)))
    else:
        L.append("  %s jogos, relidos em %s s%s" % (i["total"], _br(i["segundos"]), contra("4")))
        L.append("  por console: " + ", ".join("%s %d" % kv for kv in i["por_console"].items()))
    L.append("")
    g = d.get("gravacoes_parado", {})
    L.append("GRAVACOES EM DISCO (ARENA PARADO)")
    if g.get(NAO_MEDIU):
        L.append("  " + str(_v(g)))
    else:
        L.append("  %s por minuto%s" % (_br(g["por_minuto"]), contra("5a")))
        L.append("  %s KB por minuto%s" % (_br(g["kb_por_minuto"]), contra("5b")))
        if g.get("arquivos_de_dados_que_mudaram"):
            L.append("  arquivos que mudaram: %s" % ", ".join(g["arquivos_de_dados_que_mudaram"]))
    L.append("")
    j = d.get("jogo", {})
    L.append("JOGO DE SUPER NINTENDO")
    if j.get(NAO_MEDIU):
        L.append("  " + str(_v(j)))
    else:
        L.append("  %s%s" % (j["jogo"], " (modo modesto)" if j["modo_modesto"] else ""))
        L.append("  %s quadros por segundo em media (o normal e' 60)%s" % (_br(j["fps_medio"]), contra("6a")))
        var = j.get("variacao_dos_quadros_pct")
        L.append("  variacao do tempo de cada quadro: %s%s" % (
            _v(var) if isinstance(var, dict) else "%s%%" % _br(var),
            "" if isinstance(var, dict) else contra("6b")))
        frente = j.get("janela_do_jogo_a_frente_pct")
        if isinstance(frente, (int, float)):
            L.append("  janela do jogo a frente em %d%% do tempo%s" % (
                frente, "" if frente >= 90 else
                "  ! coberta parte do tempo: o FPS e a variacao podem estar piores que o real"))
        if "fps_sem_sincronia_pelo_som" in j:
            if j.get("som_segura_o_ritmo"):
                L.append("  ! sem seguir o ritmo da saida de SOM: %s quadros por segundo. Quem segurou o jogo"
                         % _br(j["fps_sem_sincronia_pelo_som"]))
                L.append("    foi a saida de som (fone sem fio desligado ou dormindo? troque a saida"
                         " no icone de som do Windows), nao o processador.")
            else:
                L.append("  sem seguir o ritmo da saida de som: %s quadros por segundo (nao e' o som)"
                         % _br(j["fps_sem_sincronia_pelo_som"]))
        L.append("  RetroArch: CPU media %s%% da maquina (pico %s%%), RAM %s MB, abriu em %s s, video %s" % (
            _br(j.get("cpu_media_pct_da_maquina", "?")), _br(j.get("cpu_pico_pct_da_maquina", "?")),
            _br(j.get("ram_pico_mb", "?")), _br(j["tempo_de_abrir_s"]), j.get("driver_de_video", "?")))
    L.append("")
    r = d.get("respostas")
    L.append("O QUE VOCE VIU")
    if isinstance(r, dict):
        for chave, texto, _o in PERGUNTAS:
            L.append("  %s  %s" % (texto, r.get(chave, "-")))
    else:
        L.append("  " + str(r))
    L.append("")
    comparacao = d.get("consoles_comparados") or []
    if comparacao:
        L.append("O SELO DO ARENA x O QUE VOCE VIU NESTE NOTEBOOK")
        for c in comparacao:
            L.append("  %-14s ARENA diz \"%s\"; voce viu \"%s\"  -> %s" % (
                c["console"], c["arena_diz"], c["voce_viu"],
                "ok" if c["leitura"] == "concorda" else "DISCORDA (" + c["leitura"] + ")"))
        L.append("")
    L.append("ORCAMENTOS (docs\\MAQUINA-ALVO.md, secao 7) -- tetos do notebook-alvo")
    L.append("  %-55s %10s %10s  %s" % ("item", "medido", "teto", "resultado"))
    for linha in tabela.values():
        L.append("  %-55s %10s %10s  %s" % (
            linha["item"], "-" if linha["medido"] is None else "%s %s" % (_br(linha["medido"]), linha["unidade"]),
            "%s%s %s" % (">=" if linha["piso"] else "<=", _br(linha["teto"]), linha["unidade"]),
            selo(linha)))
    estourados = [linha for linha in tabela.values() if linha["passou"] is False]
    if estourados:
        L.append("  -> %d fora do teto: antes de qualquer conserto, achar a causa." % len(estourados))
    L.append("")
    L.append("Tempo total: %s s" % _br(d["duracao_s"]))
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------------------

def pasta_da_medicao(pedida):
    """Usa a mesma pasta do coletar_maquina.py, se ele rodou ha pouco."""
    if pedida:
        os.makedirs(pedida, exist_ok=True)
        return pedida
    marca = os.path.join(coletar_maquina.PASTA_PERFIL, "ultima_coleta.txt")
    try:
        if time.time() - os.path.getmtime(marca) < 3 * 3600:
            nome = open(marca, encoding="utf-8").read().strip()
            if nome.startswith(coletar_maquina.codigo_da_maquina()):
                pasta = os.path.join(coletar_maquina.PASTA_PERFIL, nome)
                os.makedirs(pasta, exist_ok=True)
                return pasta
    except OSError:
        pass
    return coletar_maquina.pasta_da_coleta()


PASTA = None


def medir(pedida=None, pular_perguntas=False):
    global PASTA
    inicio = time.time()
    PASTA = pasta_da_medicao(pedida)
    print("Medicoes do ARENA (%s) -- leva uns 5 minutos..." % os.path.basename(PASTA), flush=True)
    dados = {"versao_coletor": coletar_maquina.VERSAO_COLETOR,
             "codigo_maquina": coletar_maquina.codigo_da_maquina(),
             "medido_em": datetime.datetime.now().isoformat(timespec="seconds")}
    try:
        dados["energia"] = coletar_maquina.energia_agora()
    except (OSError, AttributeError) as falha:
        dados["energia"] = falhou(falha)
    if dados["energia"].get("na_tomada") is False:
        print("  ! O notebook esta NA BATERIA: o resultado vai valer pouco. Se der, ligue o")
        print("    carregador agora (a medicao comeca do mesmo jeito).", flush=True)
    medir_servidor(dados)
    medir_jogo(dados)
    if pular_perguntas:
        dados["respostas"] = "perguntas puladas (--sem-perguntas)"
    else:
        perguntar(dados)
    dados["etiquetas_do_arena"] = etiquetas_do_arena()
    dados["consoles_comparados"] = comparar_consoles(dados["etiquetas_do_arena"], dados.get("respostas"))
    dados["orcamentos"] = orcamentos(dados)
    dados["duracao_s"] = round(time.time() - inicio, 1)
    with open(os.path.join(PASTA, "arena.json"), "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    texto = escrever_resumo(dados)
    with open(os.path.join(PASTA, "arena.txt"), "w", encoding="utf-8") as f:
        f.write(texto)
    return PASTA, texto


if __name__ == "__main__":
    if not sys.platform.startswith("win"):
        print("Este medidor e' para Windows.")
        sys.exit(1)
    argumentos = [a for a in sys.argv[1:] if not a.startswith("--")]
    pasta, texto = medir(argumentos[0] if argumentos else None,
                         pular_perguntas="--sem-perguntas" in sys.argv)
    print()
    print(texto)
    print("Arquivos em: %s" % pasta)
