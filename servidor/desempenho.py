# -*- coding: utf-8 -*-
r"""Desempenho que aprende: o ARENA percebe o jogo pesado demais e deixa o
grafico daquele console mais leve na proxima vez (auditoria 4).

Pedido do Rafael (22/10/2026): "ele deve saber identificar queda de
desempenho, hardware e software para entender as melhores configuracoes no
automatico, e deve ter a opcao personalizada [...] para promover uma
experiencia fluida mesmo que dependendo do hardware seja um grafico feio".

COMO MEDE (sem desenhar nada na tela e sem administrador): durante o jogo, a
cada 2 s, quanto o emulador ocupa
  - da thread mais ocupada dele (o laco do jogo): no limite, o processador
    nao da conta e o jogo anda mais devagar que o console de verdade;
  - da placa de video (no Windows, o contador "GPU Engine", o mesmo do
    Gerenciador de Tarefas).
O ARENA joga com o vsync: o jogo que roda na velocidade certa espera a tela
a cada quadro, e nenhum dos dois fica cravado. Por que nao o FPS: o
RetroArch 1.22 so poe os quadros por segundo no titulo da janela com o
contador desenhado na tela, e o registro dele nao guarda a media (os dois
conferidos em 22/10/2026).

"No limite" (ficou_no_limite): um dos dois acima de LIMITE_PCT em mais de
FRACAO_NO_LIMITE das amostras, com pelo menos AMOSTRAS_MINIMAS (os primeiros
segundos, de abrir o jogo, ficam de fora).

O QUE O ARENA FAZ (so no Automatico: quem escolheu o perfil ou o nivel do
grafico a mao manda sempre): o console ganha um degrau mais leve na proxima
partida (config_da_partida):
  1: o perfil Desempenho (filtro de escala leve, video em thread...);
  2: e o grafico igual ao do console (desenhado no tamanho dele);
  3: e o nivel "leve", abaixo do original.
Nos emuladores de fora (PS2, GameCube e Wii, PS3, Xbox 360), o degrau 1 ja
leva o "Grafico dos emuladores" para Leve. Tres partidas seguidas sem aperto
devolvem um degrau. Tudo fica em dados\desempenho.json; Ajustes -> Maquina
mostra e zera.
"""
import ctypes
import json
import os
import threading
import time

PASTA_SERVIDOR = os.path.dirname(os.path.abspath(__file__))
ARQUIVO = os.path.join(os.path.dirname(PASTA_SERVIDOR), "dados", "desempenho.json")

INTERVALO = 2.0            # segundos entre as amostras
DESCARTAR_ANTES = 20.0     # segundos do comeco (abrir o jogo pesa mais)
AMOSTRAS_MINIMAS = 15      # 30 s de jogo medido
LIMITE_PCT = 95.0
FRACAO_NO_LIMITE = 0.25
# Quando o proprio emulador diz a velocidade (o PS2 do Android: o nucleo grava arena-status.json), vale ela, e nao a
# ocupacao das threads: a thread do processador do PS2 fica em ~100% mesmo no jogo a 100% da velocidade (medido em
# 24/10/2026). Abaixo de LIMITE_VELOCIDADE por cento do tempo real, o jogo anda mais devagar que o do console.
LIMITE_VELOCIDADE = 90.0
AMOSTRAS_MINIMAS_VELOCIDADE = 10      # 20 s de jogo medido (uma amostra a cada janela nova do emulador)
DEGRAU_MAXIMO = 3
PARTIDAS_PARA_SUBIR = 3

_TRAVA = threading.Lock()


# ---------------------------------------------------------------------------
# Quanto o emulador ocupa
# ---------------------------------------------------------------------------
def _tempos_das_threads_windows(pid):
    """{thread: segundos de processador} das threads do processo (Windows)."""
    from ctypes import wintypes

    class _THREADENTRY32(ctypes.Structure):
        _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
                    ("th32ThreadID", wintypes.DWORD), ("th32OwnerProcessID", wintypes.DWORD),
                    ("tpBasePri", wintypes.LONG), ("tpDeltaPri", wintypes.LONG), ("dwFlags", wintypes.DWORD)]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel32.Thread32First.argtypes = [wintypes.HANDLE, ctypes.POINTER(_THREADENTRY32)]
    kernel32.Thread32Next.argtypes = [wintypes.HANDLE, ctypes.POINTER(_THREADENTRY32)]
    kernel32.OpenThread.restype = wintypes.HANDLE
    kernel32.OpenThread.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.GetThreadTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    foto = kernel32.CreateToolhelp32Snapshot(0x4, 0)          # TH32CS_SNAPTHREAD
    if not foto or foto == wintypes.HANDLE(-1).value:
        return {}
    tempos = {}
    try:
        entrada = _THREADENTRY32()
        entrada.dwSize = ctypes.sizeof(_THREADENTRY32)
        tem = kernel32.Thread32First(foto, ctypes.byref(entrada))
        while tem:
            if entrada.th32OwnerProcessID == pid:
                alca = kernel32.OpenThread(0x0800, False, entrada.th32ThreadID)   # QUERY_LIMITED
                if alca:
                    try:
                        marcas = [wintypes.FILETIME() for _ in range(4)]
                        if kernel32.GetThreadTimes(alca, *[ctypes.byref(m) for m in marcas]):
                            usuario, nucleo = marcas[3], marcas[2]
                            total = ((usuario.dwHighDateTime << 32) | usuario.dwLowDateTime) + \
                                    ((nucleo.dwHighDateTime << 32) | nucleo.dwLowDateTime)
                            tempos[entrada.th32ThreadID] = total / 1e7
                    finally:
                        kernel32.CloseHandle(alca)
            tem = kernel32.Thread32Next(foto, ctypes.byref(entrada))
    finally:
        kernel32.CloseHandle(foto)
    return tempos


def _tempos_das_threads_proc(pid):
    """{thread: segundos de processador} lidos de /proc (Linux e Android)."""
    tempos = {}
    pasta = "/proc/%d/task" % pid
    try:
        tarefas = os.listdir(pasta)
    except OSError:
        return tempos
    por_segundo = os.sysconf("SC_CLK_TCK") if hasattr(os, "sysconf") else 100
    for tarefa in tarefas:
        try:
            with open(os.path.join(pasta, tarefa, "stat"), encoding="ascii", errors="replace") as arquivo:
                campos = arquivo.read().rsplit(")", 1)[1].split()
            tempos[tarefa] = (int(campos[11]) + int(campos[12])) / float(por_segundo)
        except (OSError, IndexError, ValueError):
            continue
    return tempos


def tempos_das_threads(pid):
    return _tempos_das_threads_windows(pid) if os.name == "nt" else _tempos_das_threads_proc(pid)


def thread_mais_ocupada(antes, depois, segundos):
    """% de um nucleo da thread que mais trabalhou entre as duas leituras."""
    if segundos <= 0:
        return 0.0
    maior = 0.0
    for thread, tempo in depois.items():
        if thread in antes:
            maior = max(maior, (tempo - antes[thread]) / segundos * 100.0)
    return round(min(maior, 100.0), 1)


class _Placa(object):
    """A % da placa de video do processo (Windows, contador GPU Engine, PDH
    sem administrador; a mesma leitura de ferramentas\\medir_escala.py)."""

    def __init__(self):
        from ctypes import wintypes

        class _VALOR(ctypes.Structure):
            _fields_ = [("CStatus", wintypes.DWORD), ("doubleValue", ctypes.c_double)]

        class _ITEM(ctypes.Structure):
            _fields_ = [("szName", wintypes.LPWSTR), ("FmtValue", _VALOR)]

        self._item = _ITEM
        self.pdh = ctypes.WinDLL("pdh")
        p = self.pdh
        p.PdhOpenQueryW.argtypes = [wintypes.LPCWSTR, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
        p.PdhAddEnglishCounterW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR, ctypes.c_void_p,
                                            ctypes.POINTER(ctypes.c_void_p)]
        p.PdhCollectQueryData.argtypes = [ctypes.c_void_p]
        p.PdhGetFormattedCounterArrayW.argtypes = [ctypes.c_void_p, wintypes.DWORD,
                                                   ctypes.POINTER(wintypes.DWORD),
                                                   ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p]
        p.PdhCloseQuery.argtypes = [ctypes.c_void_p]
        for nome in ("PdhOpenQueryW", "PdhAddEnglishCounterW", "PdhCollectQueryData",
                     "PdhGetFormattedCounterArrayW", "PdhCloseQuery"):
            getattr(p, nome).restype = wintypes.LONG
        self.consulta, self.contador = ctypes.c_void_p(), ctypes.c_void_p()
        if p.PdhOpenQueryW(None, None, ctypes.byref(self.consulta)) != 0:
            raise OSError("PdhOpenQueryW falhou")
        if p.PdhAddEnglishCounterW(self.consulta, r"\GPU Engine(*)\Utilization Percentage", None,
                                   ctypes.byref(self.contador)) != 0:
            p.PdhCloseQuery(self.consulta)
            raise OSError("o Windows nao tem o contador GPU Engine")
        p.PdhCollectQueryData(self.consulta)

    def ler(self, pid):
        from ctypes import wintypes
        p = self.pdh
        p.PdhCollectQueryData(self.consulta)
        tamanho, quantos = wintypes.DWORD(0), wintypes.DWORD(0)
        p.PdhGetFormattedCounterArrayW(self.contador, 0x200, ctypes.byref(tamanho), ctypes.byref(quantos), None)
        if not tamanho.value:
            return 0.0
        memoria = ctypes.create_string_buffer(tamanho.value)
        if p.PdhGetFormattedCounterArrayW(self.contador, 0x200, ctypes.byref(tamanho), ctypes.byref(quantos),
                                          memoria) != 0:
            return 0.0
        itens = ctypes.cast(memoria, ctypes.POINTER(self._item))
        prefixo = "pid_%d_" % pid
        return round(sum(itens[i].FmtValue.doubleValue for i in range(quantos.value)
                         if itens[i].szName.startswith(prefixo) and itens[i].szName.endswith("engtype_3D")), 1)

    def fechar(self):
        self.pdh.PdhCloseQuery(self.consulta)


class Medidor(object):
    """Mede o emulador numa thread propria enquanto o jogo roda. parar()
    devolve a medida ({"amostras", "processador", "placa"}: as listas de %)."""

    def __init__(self, pid, intervalo=INTERVALO, descartar_antes=DESCARTAR_ANTES, com_placa=True, velocidade=None):
        self.pid = int(pid or 0)
        self.com_placa = com_placa
        self.intervalo = intervalo
        self.descartar_antes = descartar_antes
        self.processador, self.placa = [], []
        # 'velocidade': funcao que devolve o ultimo status do emulador ({"sequencia", "velocidade"}) ou None.
        self._ler_velocidade = velocidade
        self._ultima_sequencia = None
        self.velocidade = []
        self._parar = threading.Event()
        self._thread = None

    def comecar(self):
        if self.pid > 0:
            self._thread = threading.Thread(target=self._medir, name="arena-desempenho", daemon=True)
            self._thread.start()
        return self

    def _medir(self):
        placa = None
        try:
            if self._parar.wait(self.descartar_antes):
                return
            # O contador da placa leva um ou dois segundos para abrir: depois
            # do comeco descartado, para nao atrasar a primeira amostra.
            if self.com_placa and os.name == "nt":
                try:
                    placa = _Placa()
                except (OSError, AttributeError):
                    placa = None
            antes, quando = tempos_das_threads(self.pid), time.monotonic()
            if placa:
                placa.ler(self.pid)
            while not self._parar.wait(self.intervalo):
                agora, depois = time.monotonic(), tempos_das_threads(self.pid)
                if not depois:
                    break          # o emulador fechou
                self.processador.append(thread_mais_ocupada(antes, depois, agora - quando))
                if placa:
                    self.placa.append(placa.ler(self.pid))
                self._anotar_velocidade()
                antes, quando = depois, agora
        finally:
            if placa:
                placa.fechar()

    def _anotar_velocidade(self):
        """Uma amostra de velocidade por janela NOVA do emulador (a sequencia anda); erro de leitura nao derruba."""
        if not self._ler_velocidade:
            return
        try:
            status = self._ler_velocidade()
        except Exception:      # noqa: BLE001 -- medir e' bonus
            return
        if status and status.get("sequencia") != self._ultima_sequencia:
            self._ultima_sequencia = status.get("sequencia")
            self.velocidade.append(float(status["velocidade"]))

    def parar(self):
        self._parar.set()
        if self._thread:
            self._thread.join(5)
        return {"amostras": len(self.processador), "processador": list(self.processador),
                "placa": list(self.placa), "mede_velocidade": bool(self._ler_velocidade),
                "velocidade": list(self.velocidade)}


def mediana(valores):
    ordenados = sorted(valores)
    meio = len(ordenados) // 2
    if not ordenados:
        return 0.0
    return ordenados[meio] if len(ordenados) % 2 else (ordenados[meio - 1] + ordenados[meio]) / 2.0


def ficou_no_limite(medida):
    """True (pesado), False (folgado) ou None (jogo curto demais para saber).

    Com a velocidade do proprio emulador (medida["mede_velocidade"]) vale so ela: mais de uma quarta parte das
    amostras abaixo de LIMITE_VELOCIDADE por cento e' pesado."""
    if (medida or {}).get("mede_velocidade"):
        velocidades = (medida or {}).get("velocidade") or []
        if len(velocidades) < AMOSTRAS_MINIMAS_VELOCIDADE:
            return None
        return sum(1 for v in velocidades if v < LIMITE_VELOCIDADE) > FRACAO_NO_LIMITE * len(velocidades)
    amostras = int((medida or {}).get("amostras") or 0)
    if amostras < AMOSTRAS_MINIMAS:
        return None
    for nome in ("processador", "placa"):
        valores = (medida or {}).get(nome) or []
        if valores and sum(1 for v in valores if v >= LIMITE_PCT) > FRACAO_NO_LIMITE * len(valores):
            return True
    return False


# ---------------------------------------------------------------------------
# O que fica guardado e o que muda na proxima partida
# ---------------------------------------------------------------------------
def ler(arquivo=None):
    try:
        with open(arquivo or ARQUIVO, encoding="utf-8") as entrada:
            dados = json.load(entrada)
        return dados if isinstance(dados, dict) else {}
    except (OSError, ValueError):
        return {}


def _gravar(dados, arquivo=None):
    destino = arquivo or ARQUIVO
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    temporario = "%s.%d.tmp" % (destino, threading.get_ident())
    with open(temporario, "w", encoding="utf-8") as saida:
        json.dump(dados, saida, ensure_ascii=False, indent=1, sort_keys=True)
    os.replace(temporario, destino)


def registrar(plataforma, medida, arquivo=None):
    """Guarda a partida e muda o degrau do console. Devolve (degrau antes,
    degrau depois)."""
    resultado = ficou_no_limite(medida)
    with _TRAVA:
        dados = ler(arquivo)
        console = dados.get(plataforma) or {}
        antes = int(console.get("degrau") or 0)
        depois, folgadas = antes, int(console.get("folgadas") or 0)
        if resultado is True:
            depois, folgadas = min(DEGRAU_MAXIMO, antes + 1), 0
        elif resultado is False:
            folgadas += 1
            if antes and folgadas >= PARTIDAS_PARA_SUBIR:
                depois, folgadas = antes - 1, 0
        if resultado is not None or plataforma in dados:
            maximo = lambda v: max(v) if v else 0          # noqa: E731
            console.update({"degrau": depois, "folgadas": folgadas, "quando": time.strftime("%Y-%m-%d %H:%M"),
                            "ultima": {"no_limite": resultado, "amostras": int((medida or {}).get("amostras") or 0),
                                       "processador_max": maximo((medida or {}).get("processador")),
                                       "placa_max": maximo((medida or {}).get("placa")),
                                       "velocidade_mediana": (round(mediana(medida["velocidade"]), 1)
                                                              if (medida or {}).get("velocidade") else None)}})
            dados[plataforma] = console
            _gravar(dados, arquivo)
    return antes, depois


def degrau(plataforma, arquivo=None):
    return int((ler(arquivo).get(plataforma) or {}).get("degrau") or 0)


def zerar(plataforma=None, arquivo=None):
    """Volta um console (ou todos) ao normal."""
    with _TRAVA:
        dados = ler(arquivo)
        if plataforma:
            dados.pop(plataforma, None)
        else:
            dados = {}
        _gravar(dados, arquivo)


def config_da_partida(config, plataforma, arquivo=None):
    """A configuracao desta partida com o degrau do console -- so no
    Automatico (perfil e nivel do grafico escolhidos pelo ARENA) e com o
    ajuste ligado. Nao muda 'config'; devolve uma copia (ou o proprio)."""
    if not config.get("ajuste_pelo_desempenho", True) or not plataforma:
        return config
    if config.get("perfil_grafico", "automatico") != "automatico" or config.get("abaixo_do_original"):
        return config
    nivel = degrau(plataforma, arquivo)
    if not nivel:
        return config
    copia = dict(config)
    copia["perfil_grafico"] = "desempenho"
    if config.get("preset_grafico_externo", "automatico") == "automatico":
        copia["preset_grafico_externo"] = "leve"
    if nivel >= 2:
        copia["modo_modesto"] = True
    if nivel >= 3:
        copia["abaixo_do_original"] = "leve"
    return copia
