# -*- coding: utf-8 -*-
r"""Medicoes do ARENA nesta maquina, para o perfil-alvo.

Mede, sozinho:
  1. abertura: do ARENA.bat ate o servidor responder e entregar os dados
     que a tela desenha, e quanta memoria do Windows isso consome;
  2. servidor parado (30 s) e em uso (20 s de pedidos): CPU, RAM, resposta;
  3. indexacao: tempo para reler a pasta de jogos, e quantos sao;
  4. gravacoes em disco por minuto com o ARENA parado (120 s);
  5. um jogo de Super Nintendo por ~70 s: quadros por segundo, regularidade
     dos quadros, CPU e RAM do RetroArch.
No fim, perguntas rapidas sobre o que so uma pessoa olhando ve.

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
import importlib.util
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

    def fechar(self):
        self.k.CloseHandle(self.h)


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


def medir_servidor(dados):
    """Etapas 1 a 4. Abre o ARENA de verdade e fecha no fim."""
    if porta_ocupada():
        motivo = "o ARENA ja estava aberto -- feche a janela preta e rode de novo"
        for chave in ("abertura", "servidor", "indexacao", "gravacoes_parado"):
            dados[chave] = falhou(motivo)
        print("  ! " + motivo)
        return

    etapa("abrindo o ARENA (como o ARENA.bat)")
    memoria_antes = coletar_maquina.memoria_agora()["livre_mb"]
    saida = open(os.path.join(PASTA, "arena_janela_preta.txt"), "w", encoding="utf-8", errors="replace")
    inicio = time.perf_counter()
    servidor = subprocess.Popen([PYTHON, ARENA_PY], cwd=RAIZ, stdin=subprocess.DEVNULL,
                                stdout=saida, stderr=subprocess.STDOUT)
    try:
        pronto = None
        while time.perf_counter() - inicio < 120:
            try:
                urllib.request.urlopen(ENDERECO + "/", timeout=1).read()
                pronto = time.perf_counter() - inicio
                break
            except (urllib.error.URLError, OSError):
                if servidor.poll() is not None:
                    break
                time.sleep(0.05)
        if pronto is None:
            dados["abertura"] = falhou("o servidor nao respondeu em 120 s (veja arena_janela_preta.txt)")
            return
        pedir("/api/estado")
        catalogo = pedir("/api/catalogo")
        dados_prontos = time.perf_counter() - inicio
        time.sleep(10)          # a janela do navegador abrir e assentar
        memoria_depois = coletar_maquina.memoria_agora()["livre_mb"]
        dados["abertura"] = {
            "servidor_responde_s": round(pronto, 2),
            "dados_da_tela_prontos_s": round(dados_prontos, 2),
            "memoria_consumida_mb": memoria_antes - memoria_depois,
            "nota": "memoria_consumida = RAM livre do Windows antes - depois de abrir "
                    "(servidor + janela do navegador). O desenho da tela em si nao e' medido.",
        }

        proc = Processo(servidor.pid)
        etapa("servidor parado (30 s)")
        parado, _ = amostrar(proc, 30)

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
        subprocess.run(["taskkill", "/PID", str(servidor.pid), "/T", "/F"], capture_output=True)
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

    Achado de 30/09/2026: antes pegava so o menor, que nesta pasta e' o
    "BS F-ZERO (J)" -- de Satellaview. O RetroArch fechava em 1 s sem abrir
    o jogo, a conta dava 4.140.000 quadros por segundo e o resumo ainda
    marcava [BOM]. O FPS do SNES nunca tinha sido medido, em maquina
    nenhuma. Devolve (snes, lista); quem mede tenta um por um."""
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
            amostras.append((100 * (agora_cpu - ultimo_cpu) / (agora_t - ultimo_t) / ncpu,
                             proc.ram_mb()[0]))
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
        sys.path.insert(0, os.path.join(RAIZ, "servidor"))
        spec = importlib.util.spec_from_file_location("arena_medicao", ARENA_PY)
        arena = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(arena)
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
        dados["jogo"] = resultado
    except Exception as falha:
        dados["jogo"] = falhou(falha)
    finally:
        sys.path = [p for p in sys.path if not p.endswith("servidor")] + [os.path.join(RAIZ, "servidor")]
        shutil.rmtree(temp, ignore_errors=True)


# ---------------------------------------------------------------------------
# Perguntas (o que so uma pessoa olhando ve)
# ---------------------------------------------------------------------------

PERGUNTAS = [
    ("tela_inteira", "A tela do ARENA abriu inteira, com a lista de jogos?", {"s": "sim", "n": "nao", "x": "nao vi"}),
    ("tempo_tela", "Quanto tempo a tela do ARENA levou para aparecer?",
     {"1": "rapido (menos de 5 s)", "2": "uns segundos (5 a 15 s)", "3": "demorou (mais de 15 s)", "x": "nao vi"}),
    ("som_picotou", "No jogo de Super Nintendo, o som picotou ou chiou?", {"s": "sim", "n": "nao", "x": "nao ouvi"}),
    ("imagem_engasgou", "A imagem do jogo engasgou ou ficou lenta?", {"s": "sim", "n": "nao", "x": "nao vi"}),
    ("controle", "Se tinha controle ou teclado a mao: respondeu na hora?",
     {"s": "sim", "n": "nao", "x": "nao testei"}),
]


def perguntar(dados):
    if not sys.stdin or not sys.stdin.isatty():
        dados["respostas"] = "ninguem no teclado: perguntas puladas"
        return
    print()
    print("Faltam so %d perguntas rapidas (uma tecla e Enter):" % len(PERGUNTAS))
    respostas = {}
    for chave, texto, opcoes in PERGUNTAS:
        legenda = "  ".join("[%s] %s" % (k, v) for k, v in opcoes.items())
        while True:
            try:
                r = input("  %s\n     %s\n     > " % (texto, legenda)).strip().lower()
            except (EOFError, KeyboardInterrupt):
                r = "x"
            if r in opcoes:
                respostas[chave] = opcoes[r]
                break
            print("     (digite so uma das letras entre colchetes)")
    dados["respostas"] = respostas


# ---------------------------------------------------------------------------
# Resumo em portugues, com veredito
# ---------------------------------------------------------------------------

# Limites do veredito (bom / no limite). Acima do segundo = ruim. Escritos
# aqui para todo mundo ver de onde vem o sinal. PROVISORIOS: sao estimativa,
# nao medida -- a ideia e' recalibrar com os numeros do Celeron da escola.
# (Referencia: num Ryzen 5 5600G a variacao dos quadros deu 3,2%, com o SNES
# pedindo 60,10 quadros para um monitor de 60 Hz.)
LIMITES = {
    "servidor_responde_s": (3, 8), "dados_da_tela_prontos_s": (4, 10),
    "memoria_consumida_mb": (400, 800), "cpu_parado": (1, 5),
    "resposta_p95_ms": (300, 1000), "indexacao_s": (5, 20), "gravacoes_min": (5, 30),
    "variacao_quadros_pct": (5, 10),
}


def veredito(valor, chave, maior_e_melhor=False):
    if not isinstance(valor, (int, float)):
        return "?"
    if maior_e_melhor:        # FPS
        return "BOM" if valor >= 58 else "NO LIMITE" if valor >= 50 else "RUIM"
    bom, limite = LIMITES[chave]
    return "BOM" if valor < bom else "NO LIMITE" if valor < limite else "RUIM"


def _v(valor):
    if isinstance(valor, dict) and valor.get(NAO_MEDIU):
        return "nao foi possivel medir (%s)" % valor.get("motivo", "")
    return valor


def escrever_resumo(d):
    L = ["MEDICOES DO ARENA NESTA MAQUINA",
         "Codigo da maquina: %s    Medido em: %s" % (d["codigo_maquina"], d["medido_em"]), ""]
    a = d.get("abertura", {})
    L.append("ABRIR O ARENA")
    if a.get(NAO_MEDIU):
        L.append("  " + str(_v(a)))
    else:
        L.append("  servidor respondeu em %s s  [%s]" % (a["servidor_responde_s"],
                 veredito(a["servidor_responde_s"], "servidor_responde_s")))
        L.append("  dados da tela prontos em %s s  [%s]" % (a["dados_da_tela_prontos_s"],
                 veredito(a["dados_da_tela_prontos_s"], "dados_da_tela_prontos_s")))
        L.append("  memoria que o ARENA tomou do Windows: %s MB  [%s]" % (
            a["memoria_consumida_mb"], veredito(a["memoria_consumida_mb"], "memoria_consumida_mb")))
    L.append("")
    s = d.get("servidor", {})
    L.append("SERVIDOR")
    if s.get(NAO_MEDIU):
        L.append("  " + str(_v(s)))
    else:
        p, u = s["parado"], s["em_uso"]
        L.append("  parado: %s%% da maquina, %s MB  [%s]" % (
            p["cpu_pct_da_maquina"], p["ram_mb"], veredito(p["cpu_pct_da_maquina"], "cpu_parado")))
        L.append("  em uso: %s%% da maquina, %s pedidos, resposta media %s ms, pior 5%% %s ms  [%s]" % (
            u["cpu_pct_da_maquina"], u["pedidos"], u.get("resposta_media_ms", "?"),
            u.get("resposta_p95_ms", "?"), veredito(u.get("resposta_p95_ms"), "resposta_p95_ms")))
    L.append("")
    i = d.get("indexacao", {})
    L.append("LISTA DE JOGOS")
    if i.get(NAO_MEDIU):
        L.append("  " + str(_v(i)))
    else:
        L.append("  %s jogos, relidos em %s s  [%s]" % (i["total"], i["segundos"],
                 veredito(i["segundos"], "indexacao_s")))
        L.append("  por console: " + ", ".join("%s %d" % kv for kv in i["por_console"].items()))
    L.append("")
    g = d.get("gravacoes_parado", {})
    L.append("GRAVACOES EM DISCO (ARENA PARADO)")
    if g.get(NAO_MEDIU):
        L.append("  " + str(_v(g)))
    else:
        L.append("  %s por minuto (%s KB/min)  [%s]" % (g["por_minuto"], g["kb_por_minuto"],
                 veredito(g["por_minuto"], "gravacoes_min")))
    L.append("")
    j = d.get("jogo", {})
    L.append("JOGO DE SUPER NINTENDO")
    if j.get(NAO_MEDIU):
        L.append("  " + str(_v(j)))
    else:
        L.append("  %s%s" % (j["jogo"], " (modo modesto)" if j["modo_modesto"] else ""))
        L.append("  %s quadros por segundo em media (o normal e' 60)  [%s]" % (
            j["fps_medio"], veredito(j["fps_medio"], None, maior_e_melhor=True)))
        var = j.get("variacao_dos_quadros_pct")
        L.append("  variacao do tempo de cada quadro: %s%s" % (
            _v(var) if isinstance(var, dict) else "%s%%" % var,
            "" if isinstance(var, dict) else "  [%s]" % veredito(var, "variacao_quadros_pct")))
        L.append("  RetroArch: CPU media %s%% da maquina (pico %s%%), RAM %s MB, abriu em %s s, video %s" % (
            j.get("cpu_media_pct_da_maquina", "?"), j.get("cpu_pico_pct_da_maquina", "?"),
            j.get("ram_pico_mb", "?"), j["tempo_de_abrir_s"], j.get("driver_de_video", "?")))
    L.append("")
    r = d.get("respostas")
    L.append("O QUE VOCE VIU")
    if isinstance(r, dict):
        for chave, texto, _o in PERGUNTAS:
            L.append("  %s  %s" % (texto, r.get(chave, "-")))
    else:
        L.append("  " + str(r))
    L.append("")
    L.append("BOM / NO LIMITE / RUIM: limites PROVISORIOS (estimativa, ainda nao calibrada")
    L.append("com o Celeron), escritos em LIMITES, dentro de medir_arena.py.")
    L.append("Tempo total: %s s" % d["duracao_s"])
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
    medir_servidor(dados)
    medir_jogo(dados)
    if pular_perguntas:
        dados["respostas"] = "perguntas puladas (--sem-perguntas)"
    else:
        perguntar(dados)
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
