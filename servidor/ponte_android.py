# -*- coding: utf-8 -*-
r"""
ARENA - a conversa do servidor com o app do Android (item 14).

No Android, o servidor do ARENA (este Python, o mesmo do Windows e do Linux)
roda dentro do app do ARENA, que o abriu (android\src\...\ArenaServico.java).
O que so o app sabe fazer -- abrir a tela do RetroArch, contar os controles
ligados, abrir uma pasta no gerenciador de arquivos -- o servidor pede a ele
por um fio so dos dois: o stdout de verdade do Python. Os print() do servidor
vao para o stderr, que o app grava no registro do Android (o logcat).

Cada pedido e' uma linha JSON, com um numero; a resposta do app chega pelo
stdin com o mesmo numero, e os avisos do app (o jogo fechou), sem pedido:

  servidor -> app   {"id": 7, "pedido": "jogar", "argumentos": ["--config", ...]}
  app -> servidor   {"id": 7, "pid": 12345}
  app -> servidor   {"evento": "fim", "id": 7, "codigo": 0}

O fio e' aberto pelo servidor\android_inicio.py, antes do arena.py. Sem ele
(um teste, ou o servidor aberto a mao), cada pedido falha com OSError e o
servidor segue, como no computador sem o programa que faltou.

Os nucleos do Android vem dentro do APK (assets\arena-nucleos\<abi>) e saem
para a pasta de nucleos do app na primeira vez que o console abre
(preparar_nucleo): o APK e' um zip, e o Python le o zip.
"""
import json
import os
import subprocess
import sys
import threading
import zipfile

# Quem abriu o servidor conta pelas variaveis do ambiente (ArenaServico.java).
APK = os.environ.get("ARENA_ANDROID_APK", "")          # o caminho do APK instalado
ABI = os.environ.get("ARENA_ANDROID_ABI", "")          # arm64-v8a ou x86_64
SISTEMA = os.environ.get("ARENA_ANDROID_SISTEMA", "")  # "Android 15 (Google Pixel 6)"
# Onde procurar a pasta do ARENA: a memoria do aparelho e cada cartao ou pen
# drive (uma por linha).
RAIZES = [r for r in os.environ.get("ARENA_ANDROID_RAIZES", "").splitlines() if r.strip()]
# A pasta do ARENA desta abertura e se ela so deixa ler (android_inicio.py).
ESTADO = {"pasta": "", "so_leitura": False}

# O fio para o app (o stdout de verdade). O android_inicio.py preenche.
CANAL = None
_TRAVA_DO_CANAL = threading.Lock()
_TRAVA = threading.Lock()
_numero = [0]
_respostas = {}      # numero -> resposta (dict)
_esperas = {}        # numero -> threading.Event
_processos = {}      # numero -> ProcessoDoRetroArch
_OUVINTE = {"rodando": False}


class SemOApp(OSError):
    """O servidor nao esta dentro do app do Android (sem o fio)."""


def _escrever(mensagem):
    if CANAL is None:
        raise SemOApp("o servidor nao esta dentro do app do ARENA")
    linha = json.dumps(mensagem, ensure_ascii=False)
    with _TRAVA_DO_CANAL:
        CANAL.write(linha + "\n")
        CANAL.flush()


def _tratar(mensagem):
    """Uma linha do app: resposta de um pedido ou aviso."""
    numero = mensagem.get("id")
    if mensagem.get("evento") == "fim":
        with _TRAVA:
            processo = _processos.pop(numero, None)
        if processo is not None:
            processo._terminou(mensagem.get("codigo", 0))
        return
    with _TRAVA:
        espera = _esperas.pop(numero, None)
        if espera is not None:
            _respostas[numero] = mensagem
    if espera is not None:
        espera.set()


def ouvir(entrada=None):
    """Le o que o app manda, ate o app fechar o fio. Fio fechado = o app
    saiu: o servidor sai junto (senao ficaria sozinho no aparelho)."""
    entrada = entrada or sys.stdin
    for linha in entrada:
        linha = linha.strip()
        if not linha:
            continue
        try:
            _tratar(json.loads(linha))
        except (ValueError, AttributeError) as falha:
            print("[ARENA] Recado do app que nao entendi (%s): %r" % (falha, linha[:200]))
    print("[ARENA] O app do ARENA fechou: encerrando o servidor.")
    sys.stdout.flush()
    os._exit(0)


def comecar_a_ouvir():
    with _TRAVA:
        if _OUVINTE["rodando"]:
            return
        _OUVINTE["rodando"] = True
    threading.Thread(target=ouvir, daemon=True, name="ponte-android").start()


def _novo_numero():
    with _TRAVA:
        _numero[0] += 1
        return _numero[0]


def avisar(pedido):
    """Manda o pedido (dict) ao app, sem esperar resposta."""
    _escrever(dict(pedido, id=_novo_numero()))


def perguntar(pedido, limite=10.0):
    """Manda o pedido (dict) ao app e devolve a resposta (dict), ou {} se o
    app nao respondeu no limite (segundos)."""
    numero = _novo_numero()
    espera = threading.Event()
    with _TRAVA:
        _esperas[numero] = espera
    try:
        _escrever(dict(pedido, id=numero))
    except Exception:
        with _TRAVA:
            _esperas.pop(numero, None)
        raise
    if not espera.wait(limite):
        with _TRAVA:
            _esperas.pop(numero, None)
        return {}
    with _TRAVA:
        return _respostas.pop(numero, None) or {}


# ---------------------------------------------------------------------------
# O RetroArch: uma tela do app, que se espera como um processo
# ---------------------------------------------------------------------------

class ProcessoDoRetroArch:
    """O RetroArch aberto pelo app, com o jeito de um subprocess.Popen (o
    servidor espera o jogo fechar com o wait(), como no Windows)."""

    def __init__(self, numero, pid=0):
        self.numero = numero
        self.pid = pid
        self.returncode = None
        self._fim = threading.Event()

    def _terminou(self, codigo):
        self.returncode = int(codigo) if isinstance(codigo, (int, float)) else 0
        self._fim.set()

    def poll(self):
        return self.returncode

    def wait(self, timeout=None):
        if not self._fim.wait(timeout):
            raise subprocess.TimeoutExpired("RetroArch", timeout or 0)
        return self.returncode

    def terminate(self):
        try:
            avisar({"pedido": "fechar_jogo", "jogo": self.numero})
        except OSError:
            pass

    kill = terminate


def abrir_retroarch(comando, **_nao_se_aplicam):
    """Abre o RetroArch com a linha de comando 'comando' (a mesma do Windows
    e do Linux; o primeiro item, o programa, o app ja sabe qual e'). O
    RetroArch do APK recebe o resto inteiro (o remendo
    android/retroarch/arena-args.patch). O cwd e as variaveis do ambiente
    nao se aplicam: o RetroArch e' uma tela do app."""
    numero = _novo_numero()
    processo = ProcessoDoRetroArch(numero)
    espera = threading.Event()
    with _TRAVA:
        _processos[numero] = processo
        _esperas[numero] = espera
    try:
        _escrever({"id": numero, "pedido": "jogar", "argumentos": [str(a) for a in comando[1:]]})
    except Exception:
        with _TRAVA:
            _processos.pop(numero, None)
            _esperas.pop(numero, None)
        raise
    if not espera.wait(30.0):
        with _TRAVA:
            _esperas.pop(numero, None)
            _processos.pop(numero, None)
        raise OSError("o app do ARENA nao abriu o RetroArch (sem resposta em 30 s)")
    with _TRAVA:
        resposta = _respostas.pop(numero, None) or {}
    if resposta.get("erro"):
        with _TRAVA:
            _processos.pop(numero, None)
        raise OSError(resposta["erro"])
    processo.pid = int(resposta.get("pid") or 0)
    return processo


# ---------------------------------------------------------------------------
# Os outros pedidos
# ---------------------------------------------------------------------------

def controles():
    """Quantos controles de jogo estao ligados (o app pergunta ao Android)."""
    try:
        resposta = perguntar({"pedido": "controles"}, limite=3.0)
    except OSError:
        return 0
    return int(resposta.get("quantos") or 0)


def abrir_pasta(caminho):
    """Abre a pasta no gerenciador de arquivos do aparelho. False se o
    aparelho nao tem um que abra pasta (quem chamou mostra o caminho)."""
    try:
        resposta = perguntar({"pedido": "abrir_pasta", "caminho": caminho}, limite=5.0)
    except OSError:
        return False
    return bool(resposta.get("ok"))


def tela_pronta(endereco):
    """O servidor ja escuta: o app pode mostrar a tela do ARENA."""
    try:
        avisar({"pedido": "pronto", "endereco": endereco})
        return True
    except OSError:
        return False


def reabrir():
    """Pede ao app para abrir o servidor de novo (a pasta do ARENA mudou)."""
    avisar({"pedido": "reabrir"})


# ---------------------------------------------------------------------------
# Os nucleos, de dentro do APK
# ---------------------------------------------------------------------------

_NUCLEOS = {}


def nucleos_do_apk():
    """Os nomes dos nucleos que vieram no APK, para esta ABI (lidos uma vez)."""
    if "lista" not in _NUCLEOS:
        prefixo = "assets/arena-nucleos/%s/" % ABI
        try:
            with zipfile.ZipFile(APK) as apk:
                _NUCLEOS["lista"] = sorted(n[len(prefixo):] for n in apk.namelist()
                                           if n.startswith(prefixo) and n.endswith("_libretro_android.so")
                                           and "/" not in n[len(prefixo):])
        except (OSError, zipfile.BadZipFile, ValueError):
            _NUCLEOS["lista"] = []
    return _NUCLEOS["lista"]


def marca_do_apk():
    try:
        informacao = os.stat(APK)
        return "%d-%d" % (informacao.st_size, int(informacao.st_mtime))
    except OSError:
        return ""


_TRAVA_DOS_NUCLEOS = threading.Lock()


def preparar_nucleo(caminho):
    """Poe o nucleo 'caminho' (na pasta de nucleos do app) para fora do APK,
    se ainda nao saiu deste APK. True se ele existe no fim."""
    nome = os.path.basename(caminho)
    if nome not in nucleos_do_apk():
        return os.path.isfile(caminho)
    marca = os.path.join(os.path.dirname(caminho), nome + ".arena")
    desta = marca_do_apk()
    with _TRAVA_DOS_NUCLEOS:
        try:
            with open(marca, encoding="utf-8") as arquivo:
                if os.path.isfile(caminho) and arquivo.read().strip() == desta:
                    return True
        except OSError:
            pass
        try:
            os.makedirs(os.path.dirname(caminho), exist_ok=True)
            parcial = caminho + ".parcial"
            with zipfile.ZipFile(APK) as apk, apk.open("assets/arena-nucleos/%s/%s" % (ABI, nome)) as de, \
                    open(parcial, "wb") as para:
                while True:
                    bloco = de.read(1 << 20)
                    if not bloco:
                        break
                    para.write(bloco)
            os.replace(parcial, caminho)
            with open(marca, "w", encoding="utf-8") as arquivo:
                arquivo.write(desta)
        except (OSError, KeyError, zipfile.BadZipFile) as falha:
            print("[ARENA] Nao consegui tirar o nucleo %s do APK: %s" % (nome, falha))
    return os.path.isfile(caminho)


# ---------------------------------------------------------------------------
# A pasta do ARENA no aparelho
# ---------------------------------------------------------------------------

def _filho(pasta, nome):
    """O item 'nome' da pasta, sem ligar para maiusculas (o pen drive do
    Windows pode ter "Jogos"), ou None."""
    try:
        for item in os.listdir(pasta):
            if item.lower() == nome.lower():
                return os.path.join(pasta, item)
    except OSError:
        pass
    return None


def parece_arena(pasta):
    """Tem a pasta jogos e o resto de um ARENA (o launcher, o retroarch ou a
    entrada do Chromebook)? A mesma conta da ArenaActivity.java."""
    if not pasta or not os.path.isdir(pasta) or not _filho(pasta, "jogos"):
        return False
    return any(_filho(pasta, nome) for nome in ("launcher", "retroarch", "ARENA-CHROMEBOOK.html"))


def pastas_do_arena():
    """As pastas do ARENA que este aparelho tem: cada raiz (RAIZES) e as
    pastas dentro dela, ate dois niveis (DCIM/ARENA, Download/ARENA...)."""
    achadas = []
    for raiz in RAIZES:
        candidatas = [raiz]
        try:
            filhos = sorted(os.listdir(raiz))
        except OSError:
            filhos = []
        for nome in filhos:
            if nome.startswith(".") or nome == "Android":
                continue
            primeira = os.path.join(raiz, nome)
            candidatas.append(primeira)
            try:
                netos = sorted(os.listdir(primeira)) if os.path.isdir(primeira) else []
            except OSError:
                netos = []
            candidatas += [os.path.join(primeira, n) for n in netos if not n.startswith(".")]
        for pasta in candidatas:
            if parece_arena(pasta) and pasta not in [a["caminho"] for a in achadas]:
                achadas.append({"caminho": pasta, "nome": os.path.basename(pasta) or pasta,
                                "onde": "memoria do aparelho" if raiz == (RAIZES[0] if RAIZES else "")
                                else "cartao ou pen drive"})
    return achadas


def escolher_pasta(caminho):
    """Guarda a pasta do ARENA (no app) e pede para abrir o servidor de novo
    com ela. "" = a pasta do proprio app."""
    avisar({"pedido": "escolher_pasta", "caminho": caminho or ""})


def pedir_permissao():
    """Pede ao app a permissao de arquivos do Android (a tela do sistema)."""
    avisar({"pedido": "permissao"})
