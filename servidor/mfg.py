# -*- coding: utf-8 -*-
r"""MFG Super Motion: quadros a mais, criados entre os do jogo, pelo programa gratis da NODIX-TECH.

Pedido do Rafael (11/11/2026): trocar o Lossless Scaling (pago, da Steam)
pelo MFG SUPER MOTION, "de forma definitiva", com o ARENA configurando
sozinho as melhores opcoes.

O que e': um programa gratis (github.com/NODIX-TECH/MFG-SUPER-MOTION) que
copia a imagem da janela do jogo pela placa de video e cria quadros novos
entre os de verdade, mostrando tudo numa janela propria por cima do jogo
(que deixa o clique passar). Tres geradores:
  - DLSS MFG (generator=0): o da NVIDIA, so em placa RTX;
  - XeSS MFG (generator=1): o da Intel;
  - MSM FG   (generator=2): o do proprio programa, em qualquer placa
    (NVIDIA, AMD, Intel, integrada), Direct3D 12 puro.

O que o ARENA faz, e o que NAO faz:
  - NAO leva o programa junto, nem no pacote nem no GitHub. O codigo dele
    e' publico, mas a licenca (PolyForm Strict 1.0.0) proibe redistribuir
    e modificar. O ARENA usa o que esta instalado nesta maquina, como fazia
    com o Lossless Scaling: acha, configura e abre junto com o jogo.
  - Nao abre a tela do programa: fala direto com o motor dele
    (Engine\nvngx.dll, que e' um executavel -- o nome vem da biblioteca da
    NVIDIA, que confere o nome de quem a chama). O motor recebe as opcoes
    num arquivo "chave=valor" (--config), pega a janela do emulador pelo
    numero dela (hwnd), e fecha com a linha "stop" na entrada dele,
    devolvendo a janela do jogo como estava. Foi assim que a tela do
    proprio programa o usa (Infrastructure\MotionEngine.fs, versao 1.0.5).
  - Escolhe as opcoes por maquina e por jogo (escolher_opcoes) e decide se
    vale a pena ligar (decidir). Na placa fraca (o Celeron N5100 da rede),
    o "automatico" deixa desligado: criar quadros custa a placa que o
    proprio jogo usa.

As opcoes e os valores aceitos vem do Engine\README.md do programa (1.0.5,
lido em 11/11/2026). Medido no PC do Rafael (Ryzen 5 5600G, Radeon
integrada, 60 Hz): o motor pegou a janela do RetroArch sem administrador,
ligou o MSM FG 2x e devolveu a janela ao "stop". A primeira vez compila os
shaders (11 s); dali em diante vem do cache dele.
"""
import json
import os
import subprocess
import threading
import time

NOME = "MFG Super Motion"
PASTA_DO_PROGRAMA = "MFG SUPER MOTION"
MOTOR = os.path.join("Engine", "nvngx.dll")
TELA_DO_PROGRAMA = "Mfg Super Motion.exe"
PAGINA_OFICIAL = "https://github.com/NODIX-TECH/MFG-SUPER-MOTION/releases/latest"

# Os modos da chave nos Ajustes.
MODOS = ("automatico", "sempre", "desligado")
MODO_PADRAO = "automatico"

SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)


# ---------------------------------------------------------------------------
# Achar o programa
# ---------------------------------------------------------------------------
def lugares_para_procurar(raiz):
    """Onde o programa pode estar, na ordem: a pasta do ARENA (o pen drive do
    professor), a instalacao do usuario (o instalador dele poe aqui, sem
    administrador) e a de todos os usuarios."""
    lugares = [("arena", os.path.join(raiz, "emuladores", PASTA_DO_PROGRAMA)),
               ("arena", os.path.join(raiz, PASTA_DO_PROGRAMA))]
    for variavel, origem, partes in (("LOCALAPPDATA", "instalado", ("Programs", PASTA_DO_PROGRAMA)),
                                     ("ProgramFiles", "instalado", (PASTA_DO_PROGRAMA,)),
                                     ("ProgramFiles(x86)", "instalado", (PASTA_DO_PROGRAMA,))):
        base = os.environ.get(variavel)
        if base:
            lugares.append((origem, os.path.join(base, *partes)))
    return lugares


def versao_da_pasta(pasta):
    """A versao do motor (Engine\\engine-version.txt), ou ''."""
    try:
        with open(os.path.join(pasta, "Engine", "engine-version.txt"), encoding="utf-8", errors="replace") as arquivo:
            return arquivo.read().strip()[:20]
    except OSError:
        return ""


def achar(raiz):
    """{"pasta", "motor", "origem", "versao"} do programa desta maquina, ou None.

    So vale a pasta que tem o motor E um sinal de que e' o MFG Super Motion
    (a tela dele ou o arquivo de versao do motor): um nvngx.dll solto e' a
    biblioteca da NVIDIA de algum jogo, nao o motor."""
    if os.name != "nt":
        return None
    for origem, pasta in lugares_para_procurar(raiz):
        motor = os.path.join(pasta, MOTOR)
        if not os.path.isfile(motor):
            continue
        if not (os.path.isfile(os.path.join(pasta, TELA_DO_PROGRAMA))
                or os.path.isfile(os.path.join(pasta, "Engine", "engine-version.txt"))):
            continue
        return {"pasta": pasta, "motor": motor, "origem": origem, "versao": versao_da_pasta(pasta)}
    return None


# ---------------------------------------------------------------------------
# As placas que o motor ve
# ---------------------------------------------------------------------------
_PLACAS = {}
_TRAVA_PLACAS = threading.Lock()


def ler_placas(texto):
    """As linhas do "nvngx.dll --cards" viram uma lista de placas.

    "@card <numero> <1: DLSS MFG roda nela> <MB> <nome>" e, depois,
    "@xess <numero> <1: XeSS MFG roda nela>"."""
    placas = {}
    for linha in (texto or "").splitlines():
        partes = linha.strip().split(None, 4)
        if len(partes) >= 4 and partes[0] == "@card":
            try:
                numero, dlss, memoria = int(partes[1]), partes[2] == "1", int(partes[3])
            except ValueError:
                continue
            placas[numero] = {"numero": numero, "dlss": dlss, "memoria_mb": memoria,
                              "nome": partes[4] if len(partes) > 4 else "", "xess": False}
        elif len(partes) >= 3 and partes[0] == "@xess":
            try:
                numero = int(partes[1])
            except ValueError:
                continue
            if numero in placas:
                placas[numero]["xess"] = partes[2] == "1"
    return [placas[n] for n in sorted(placas)]


def placas(motor, espera=8, guardar_em=None, maquina=""):
    """As placas que o motor ve, perguntadas uma vez por motor (o "--cards"
    so lista e sai, mas leva de 0,13 a 0,27 s: e' um processo a parte, medido
    em 12/11/2026). Com guardar_em (dados\\mfg_placas.json), a resposta fica
    guardada e vale enquanto forem o mesmo motor (caminho, tamanho e data do
    arquivo) e a mesma maquina (`maquina`: o computador e a placa de video;
    o pen drive muda de computador). E' o que deixa a primeira tela do ARENA
    sair sem esperar o motor (orcamento 1b). Lista vazia se nao der para
    perguntar, e essa nao se guarda: na proxima abertura pergunta de novo."""
    with _TRAVA_PLACAS:
        if motor in _PLACAS:
            return _PLACAS[motor]
        chave = _chave_das_placas(motor, maquina)
        guardada = _placas_guardadas(guardar_em, chave)
        if guardada is not None:
            _PLACAS[motor] = guardada
            return guardada
        try:
            feito = subprocess.run([motor, "--cards"], cwd=os.path.dirname(motor), capture_output=True,
                                   timeout=espera, creationflags=SEM_JANELA)
            lista = ler_placas(feito.stdout.decode("utf-8", "replace"))
        except (OSError, subprocess.SubprocessError):
            lista = []
        _PLACAS[motor] = lista
        if guardar_em and chave and lista:
            _guardar_placas(guardar_em, chave, lista)
        return lista


def _chave_das_placas(motor, maquina):
    """O que tem de ser igual para a lista guardada valer. None se o motor nao esta ai."""
    try:
        estado = os.stat(motor)
    except OSError:
        return None
    return {"motor": os.path.abspath(motor), "tamanho": estado.st_size, "data": int(estado.st_mtime),
            "maquina": maquina or ""}


def _placas_guardadas(arquivo, chave):
    """A lista guardada em `arquivo`, se a chave bate; senao None."""
    if not arquivo or not chave:
        return None
    try:
        with open(arquivo, encoding="utf-8") as f:
            dados = json.load(f)
    except (OSError, ValueError):
        return None
    if isinstance(dados, dict) and dados.get("chave") == chave and isinstance(dados.get("placas"), list):
        return dados["placas"]
    return None


def _guardar_placas(arquivo, chave, lista):
    """Grava a lista com a chave, de forma atomica (temporario .tmp e os.replace; o ARENA apaga .tmp orfao
    na abertura). Falha de disco nao derruba nada: so fica sem a guardada."""
    temporario = "%s.%d.tmp" % (arquivo, threading.get_ident())
    try:
        os.makedirs(os.path.dirname(arquivo) or ".", exist_ok=True)
        with open(temporario, "w", encoding="utf-8") as f:
            json.dump({"chave": chave, "placas": lista, "quando": time.strftime("%Y-%m-%d %H:%M:%S")}, f,
                      ensure_ascii=False, indent=1)
        os.replace(temporario, arquivo)
    except OSError:
        try:
            os.remove(temporario)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Decidir e escolher as opcoes
# ---------------------------------------------------------------------------
def placa_forte(nota_gpu, integrada):
    """A placa aguenta criar quadros sem tirar do jogo, sozinha (no Automatico)?

    Medido em 11/11/2026 (testes/medir_mais_quadros.py, PresentMon, Black no
    PCSX2, Ryzen 5 5600G com a Radeon integrada, nota da placa 4): o jogo
    ficou nos mesmos 29,8 quadros com o MFG (56,6 na tela) e com o Lossless
    (59,5 na tela) -- nada tirado do jogo. Entao: a dedicada que nao e' das
    fracas (nota 3 ou mais) e a integrada forte (nota 4, a do Ryzen de mesa
    com Vega). A integrada comum (nota 3 ou menos: o Celeron N5100 da rede)
    fica de fora -- regra do Rafael, "nunca regresso de desempenho"; quem
    quiser, escolhe "Sempre"."""
    nota = int(nota_gpu or 0)
    return nota >= 4 if integrada else nota >= 3


def qual_programa(placas_do_mfg, tem_mfg, tem_lossless):
    """Qual programa cria os quadros nesta maquina: "mfg", "lossless" ou None. NUNCA os dois juntos: dois
    geradores um em cima do outro somam o atraso e os erros dos dois, e o segundo criaria quadros a partir dos
    quadros adivinhados pelo primeiro.

    - Placa NVIDIA RTX: o MFG Super Motion (o DLSS MFG e' feito pela propria placa, com o fluxo optico dela).
    - Outra placa (AMD, Intel): o Lossless Scaling, se a pessoa tiver -- medido na Radeon integrada, ele chegou
      a 59,5 quadros na tela contra 56,6 do MFG, e nos dois o jogo ficou igual; senao o MFG.
    """
    rtx = any(p.get("dlss") for p in placas_do_mfg or ())
    if tem_mfg and rtx:
        return "mfg"
    if tem_lossless:
        return "lossless"
    if tem_mfg:
        return "mfg"
    return None


def decidir(modo, achado, nota_gpu, integrada, hz, de_fora, degrau=0):
    """(usar, motivo) para esta partida.

    - "desligado": nunca. "sempre": sempre que o programa estiver aqui.
    - "automatico": so onde ajuda e a placa aguenta --
        * emulador de fora (PS2, GameCube e Wii, PS3, Xbox 360): muitos jogos
          desses consoles rodam a 30 quadros, ou caem abaixo de 60 numa
          maquina media; os quadros criados enchem a tela;
        * tela de mais de 60 Hz: o jogo de 60 vira 120 ou 144.
      Jogo do RetroArch a 60 numa tela de 60 Hz nao ganha nada (o motor nao
      cria quadro quando o jogo ja enche a tela) e so pagaria a copia."""
    modo = modo if modo in MODOS else MODO_PADRAO
    if modo == "desligado":
        return False, "desligado nos Ajustes"
    if not achado:
        return False, "nem o MFG Super Motion nem o Lossless Scaling estao nesta maquina"
    if modo == "sempre":
        return True, "ligado sempre, nos Ajustes"
    if not placa_forte(nota_gpu, integrada):
        return False, "a placa de video desta maquina e' fraca para criar quadros sem atrasar o jogo"
    if int(degrau or 0) > 0:
        return False, "o console ficou no limite da maquina antes"
    if de_fora:
        return True, "emulador de fora, com placa que aguenta"
    if int(hz or 60) > 65:
        return True, "tela de %d Hz" % int(hz)
    return False, "jogo de 60 quadros numa tela de 60 Hz: nao ha o que criar"


def escolher_opcoes(lista_de_placas, nota_gpu, integrada, hz, desenho_2d):
    """As opcoes do motor para esta partida, nesta maquina (chave -> texto).

    - Gerador: o DLSS MFG numa RTX (o melhor, feito pela placa); senao o
      MSM FG, que roda em qualquer placa. O XeSS MFG fica de fora: no teste
      do proprio programa (README do MSM FG, "jelly"), ele errou 43% da
      caixa que se move, contra 3,5% do MSM FG.
    - Na placa que nao e' dedicada e forte, o MSM FG "Fast" (o que o proprio
      programa usa de partida): menos trabalho por par de quadros.
    - Quantos quadros: "screen_limit=1" -- so os que enchem a tela, e nenhum
      quando o jogo ja chega la sozinho. O maximo por par segue a tela (2
      numa de 60 Hz, ate 4 numa de 144) e fica no 2 na placa integrada.
    - Tipo de jogo: 1 (2D) para jogo de pixel; 0 (o motor descobre) no 3D.
    - Atraso: fila de menor atraso (queue=0), quadro mais novo a cada
      atualizacao da tela (sync=1): quem joga sente o controle antes da
      suavidade.
    - Pixel parado continua o de verdade (still=1): placar e vida nao tremem.
    - Nada que desenhe por cima do jogo (contador, estudo de movimento), nada
      de compartilhar a imagem (spout, que e' para transmissao: desligado de
      proposito no ARENA), nada de ligar com outro programa (link).
    - Registro do motor desligado (log=0): ele grava muito, e o ARENA
      registra o que importa (as linhas "@" da saida dele)."""
    rtx = next((p for p in lista_de_placas or () if p.get("dlss")), None)
    forte_dedicada = (not integrada) and int(nota_gpu or 0) >= 4
    hz = int(hz or 60)
    maximo = 2 if integrada else max(2, min(4, (hz + 15) // 30))
    opcoes = {
        "mfg": "1",
        "generator": "0" if rtx else "2",
        "multiplier": str(maximo),
        "screen_limit": "1",
        "game": "1" if desenho_2d else "0",
        "queue": "0",
        "sync": "1",
        "still": "1",
        "guard": "0",
        "frame_limit": "0",
        "window_mode": "0",
        "upscaler": "0",
        "counter": "0",
        "hdr": "0",
        "spout": "0",
        "link": "0",
        "aml": "0",
        "delay": "0",
        "log": "0",
    }
    if rtx:
        opcoes["gpu"] = str(rtx["numero"])
    else:
        opcoes["msm_search"] = "0" if forte_dedicada else "1"
    return opcoes


def texto_da_partida(opcoes, hwnd, dono):
    """O arquivo de partida do motor: uma linha "chave=valor" cada, sem "#"
    (o motor toma o que vem depois de um "#" por comentario)."""
    linhas = ["%s=%s" % (chave, str(valor).replace("#", " ").replace("\n", " "))
              for chave, valor in opcoes.items()]
    linhas += ["hwnd=%d" % int(hwnd), "owner=%d" % int(dono)]
    return "\n".join(linhas) + "\n"


# ---------------------------------------------------------------------------
# A janela do jogo
# ---------------------------------------------------------------------------
def janelas_do_processo(pid):
    """[(hwnd, area)] das janelas visiveis de primeiro nivel do processo."""
    if os.name != "nt":
        return []
    import ctypes
    from ctypes import wintypes
    usuario = ctypes.WinDLL("user32")
    tipo = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    usuario.EnumWindows.argtypes = [tipo, wintypes.LPARAM]
    usuario.EnumWindows.restype = wintypes.BOOL
    usuario.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    usuario.GetWindowThreadProcessId.restype = wintypes.DWORD
    usuario.IsWindowVisible.argtypes = [wintypes.HWND]
    usuario.IsWindowVisible.restype = wintypes.BOOL
    usuario.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    usuario.GetWindowRect.restype = wintypes.BOOL
    achadas = []

    def olhar(hwnd, _):
        dono = wintypes.DWORD()
        usuario.GetWindowThreadProcessId(hwnd, ctypes.byref(dono))
        if dono.value == pid and usuario.IsWindowVisible(hwnd):
            caixa = wintypes.RECT()
            if usuario.GetWindowRect(hwnd, ctypes.byref(caixa)):
                area = max(0, caixa.right - caixa.left) * max(0, caixa.bottom - caixa.top)
                achadas.append((int(hwnd or 0), area))
        return True

    usuario.EnumWindows(tipo(olhar), 0)
    return achadas


def esperar_a_janela(pid, area_da_tela, espera=40.0, ainda_aberto=None):
    """O hwnd da janela do jogo, ou None.

    A janela do jogo e' a maior do processo, quando ela chega a metade da
    tela (o ARENA abre os emuladores em tela cheia sem borda): o PCSX2 e o
    Dolphin mostram antes uma janela pequena de carregamento. Espera no
    maximo 'espera' segundos, olhando duas vezes por segundo (so durante a
    abertura: depois disso, nada fica consultando)."""
    limite = time.monotonic() + espera
    metade = max(1, int(area_da_tela or 0) // 2)
    while time.monotonic() < limite:
        if ainda_aberto is not None and not ainda_aberto():
            return None
        janelas = sorted(janelas_do_processo(pid), key=lambda j: j[1], reverse=True)
        if janelas and janelas[0][1] >= metade:
            return janelas[0][0]
        time.sleep(0.5)
    return None


# ---------------------------------------------------------------------------
# Abrir e fechar o motor junto com o jogo
# ---------------------------------------------------------------------------
class Sessao:
    """O motor desta partida: abre quando a janela do jogo aparece, fecha no fim.

    Tudo o que espera roda numa thread daemon: o jogo abre sem esperar o
    motor. As linhas "@" da saida do motor vao para o registro do ARENA
    (estado, fonte, quadros, erro)."""

    def __init__(self, motor, opcoes, arquivo_da_partida, registrar=print):
        self.motor = motor
        self.opcoes = dict(opcoes)
        self.arquivo = arquivo_da_partida
        self.registrar = registrar
        self.processo = None
        self.estado = "esperando a janela"
        self.ultimas = []
        self._trava = threading.Lock()
        self._fim = threading.Event()

    def comecar(self, pid, area_da_tela, ainda_aberto=None):
        threading.Thread(target=self._abrir, args=(pid, area_da_tela, ainda_aberto), daemon=True,
                         name="mfg-super-motion").start()
        return self

    def _abrir(self, pid, area_da_tela, ainda_aberto):
        hwnd = esperar_a_janela(pid, area_da_tela, ainda_aberto=lambda: not self._fim.is_set() and (
            ainda_aberto is None or ainda_aberto()))
        if not hwnd or self._fim.is_set():
            self.estado = "sem janela do jogo"
            if self._fim.is_set():
                pass                                   # o ARENA mandou parar: nada a dizer
            elif ainda_aberto is not None and not ainda_aberto():
                self.registrar("[ARENA] %s: o jogo fechou antes de o motor abrir." % NOME)
            else:
                self.registrar("[ARENA] %s: a janela do jogo nao apareceu; o jogo segue sem quadros a mais." % NOME)
            return
        try:
            os.makedirs(os.path.dirname(self.arquivo), exist_ok=True)
            temporario = "%s.%d.tmp" % (self.arquivo, os.getpid())
            with open(temporario, "w", encoding="utf-8", newline="\n") as arquivo:
                arquivo.write(texto_da_partida(self.opcoes, hwnd, os.getpid()))
            os.replace(temporario, self.arquivo)
            processo = subprocess.Popen([self.motor, "--config", self.arquivo], cwd=os.path.dirname(self.motor),
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.DEVNULL, creationflags=SEM_JANELA)
        except OSError as falha:
            self.estado = "nao abriu"
            self.registrar("[ARENA] %s nao abriu: %s. O jogo segue sem quadros a mais." % (NOME, falha))
            return
        with self._trava:
            if self._fim.is_set():
                self._parar_processo(processo)
                return
            self.processo = processo
        self.estado = "aberto"
        self.registrar("[ARENA] %s ligado no jogo (%s)." % (NOME, descrever(self.opcoes)))
        self._ler_saida(processo)

    def _ler_saida(self, processo):
        for bruta in processo.stdout:
            linha = bruta.decode("utf-8", "replace").strip()
            if not linha.startswith("@"):
                continue
            with self._trava:
                self.ultimas = (self.ultimas + [linha])[-20:]
            if linha.startswith("@error"):
                self.registrar("[ARENA] %s: %s" % (NOME, linha[len("@error"):].strip()))
            elif linha.startswith("@source"):
                self.registrar("[ARENA] %s pegou a janela do jogo: %s" % (NOME, linha[len("@source"):].strip()))

    @staticmethod
    def _parar_processo(processo, espera=10.0):
        try:
            processo.stdin.write(b"stop\n")
            processo.stdin.flush()
            processo.stdin.close()
        except (OSError, ValueError):
            pass
        try:
            processo.wait(espera)
        except subprocess.TimeoutExpired:
            processo.kill()
            try:
                processo.wait(5)
            except subprocess.TimeoutExpired:
                pass

    def parar(self):
        """Fecha o motor (ele devolve a janela do jogo como estava). Devolve se havia motor aberto."""
        self._fim.set()
        with self._trava:
            processo, self.processo = self.processo, None
        if processo is None:
            return False
        if processo.poll() is None:
            self._parar_processo(processo)
        self.estado = "fechado"
        return True


def descrever(opcoes, para_a_tela=False):
    """Uma linha com o gerador e o maximo de quadros: sem acento para o
    registro, com acento para a tela."""
    gerador = {"0": "DLSS MFG", "1": "XeSS MFG", "2": "MSM FG"}.get(opcoes.get("generator"), "?")
    rapido = gerador == "MSM FG" and opcoes.get("msm_search") == "1"
    if para_a_tela:
        return "%s%s, até %sx, só o que enche a tela" % (gerador, " rápido" if rapido else "",
                                                       opcoes.get("multiplier", "2"))
    return "%s%s, ate %sx, so o que enche a tela" % (gerador, " rapido" if rapido else "",
                                                   opcoes.get("multiplier", "2"))


def situacao(raiz, nota_gpu=None, integrada=True, hz=60, tem_lossless=False, guardar_em=None, maquina=""):
    """Para a tela dos Ajustes: o MFG (achou, de onde, a versao, o gerador), se o Lossless pronto tambem esta
    aqui, qual dos dois o ARENA usa nesta maquina (qual_programa) e se o automatico liga (placa_forte).
    guardar_em e maquina: os de placas()."""
    achado = achar(raiz)
    lista = placas(achado["motor"], guardar_em=guardar_em, maquina=maquina) if achado else []
    base = {"achado": bool(achado), "disponivel": os.name == "nt", "lossless": bool(tem_lossless),
            "escolhido": qual_programa(lista, bool(achado), bool(tem_lossless)),
            "placa_forte": placa_forte(nota_gpu, integrada), "hz": int(hz or 60), "pagina": PAGINA_OFICIAL}
    if not achado:
        return base
    opcoes = escolher_opcoes(lista, nota_gpu, integrada, hz, False)
    base.update({"origem": achado["origem"], "versao": achado["versao"], "placas": [p.get("nome", "") for p in lista],
                 "gerador": descrever(opcoes, para_a_tela=True)})
    return base


if __name__ == "__main__":
    import json
    import sys
    print(json.dumps(situacao(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                     ensure_ascii=False, indent=1))
    sys.exit(0)
