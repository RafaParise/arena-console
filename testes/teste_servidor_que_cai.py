# -*- coding: utf-8 -*-
r"""O servidor que caia ou travava (pedido do Rafael, 02/10/2026).

"algumas vezes sem motivo nenhum o servidor do ARENA para de funcionar e tem
que fechar e abrir tudo". O registro de aplicativos do Windows mostrou o
Python do ARENA caindo duas vezes em 26/09/2026 (0xC0000005 no ntdll.dll),
com jogo aberto. Este teste confere as protecoes (servidor\janela_preta.py,
ARENA.bat e app.js):

  1. registro da queda: um Python que cai DE VERDADE (le o endereco 0)
     deixa em queda-do-servidor.txt a falha e a linha do codigo que caiu;
  2. o ARENA.bat reabre o servidor que caiu (ate 3 vezes, sem abrir outra
     janela) e NAO repete quando o erro tem explicacao na tela (codigo 1);
  3. janela preta travada (no Windows 10, um clique na janela comeca uma
     selecao e o programa para ao escrever nela): SEM a protecao, um
     pedido que escreve na janela fica preso -- o teste mostra isso -- e
     COM ela o servidor de verdade continua respondendo;
  4. a Edicao Rapida (o clique que trava) sai desligada numa janela de
     console nova;
  5. a tela (Edge sem janela) avisa "parou de responder" quando o servidor
     some e recarrega sozinha quando ele volta.

Uso: servidor\python\python.exe testes\teste_servidor_que_cai.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
import fuzz_rotas  # noqa: E402
import limpeza  # noqa: E402
import tela_sem_janela  # noqa: E402

PYTHON = os.path.join(RAIZ, "servidor", "python", "python.exe")
QUEDA_DE_VERDADE = 0xC0000005          # o codigo que o Windows registrou em 26/09

FILHO_QUE_CAI = r'''
import faulthandler, sys
sys.path.insert(0, sys.argv[1])
import janela_preta
janela_preta.ligar_registro_de_queda(sys.argv[2], "teste")

def funcao_que_cai():
    faulthandler._read_null()      # le o endereco 0: falha de acesso a memoria de verdade

funcao_que_cai()
'''

ARENA_FALSO = r'''
import os, sys
aqui = os.path.dirname(os.path.abspath(__file__))
registro = os.path.join(aqui, "inicios.txt")
with open(registro, "a") as f:
    f.write(os.environ.get("ARENA_REABERTO", "-") + "\n")
vezes = len(open(registro).read().split())
modo = open(os.path.join(aqui, "modo.txt")).read().strip()
if (modo == "cai2" and vezes <= 2) or modo == "caisempre":
    os._exit(-1073741819)       # 0xC0000005 escrito com sinal (o _exit do C quer um int)
if modo == "erro":
    sys.exit(1)
'''

# Sobe o ARENA de verdade (de uma copia isolada) numa porta livre. Com
# "trava": a partir do momento em que esse arquivo existir, escrever na
# janela preta nunca termina -- como no console com selecao ativa.
MOTORISTA = r'''
import os, sys, threading
servidor, porta, protecao, trava = sys.argv[1], int(sys.argv[2]), sys.argv[3] == "1", sys.argv[4]
sys.path.insert(0, servidor)
os.environ["ARENA_SEM_JANELA"] = "1"
real = sys.__stdout__

class Janela:
    encoding = "utf-8"
    errors = "replace"
    def write(self, texto):
        if os.path.exists(trava):
            threading.Event().wait()
        real.write(texto)
        return len(texto)
    def flush(self):
        pass

sys.stdout = Janela()
sys.stderr = Janela()
import arena
arena.PORTA = porta
if not protecao:
    arena.janela_preta.preparar = lambda *a, **k: None
arena.principal()
'''


def pedir(porta, metodo, caminho, corpo=None, espera=5):
    dados = json.dumps(corpo).encode() if corpo is not None else None
    req = urllib.request.Request("http://127.0.0.1:%d%s" % (porta, caminho), data=dados, method=metodo,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=espera) as resposta:
            return resposta.status, json.loads(resposta.read() or b"{}")
    except urllib.error.HTTPError as erro:
        return erro.code, {}
    except (OSError, ValueError):
        return None, {}


def esperar_servidor(porta, segundos=30):
    fim = time.monotonic() + segundos
    while time.monotonic() < fim:
        if pedir(porta, "GET", "/api/estado", espera=2)[0] == 200:
            return True
        time.sleep(0.3)
    return False


def preparar_copia(pasta):
    """Copia isolada do ARENA, sem rede aberta (nao pede passagem no Firewall)."""
    fuzz_rotas.preparar_ambiente(pasta)
    caminho = os.path.join(pasta, "dados", "config.json")
    try:
        config = json.load(open(caminho, encoding="utf-8"))
    except (OSError, ValueError):
        config = {}
    config["permitir_rede"] = False
    json.dump(config, open(caminho, "w", encoding="utf-8"))


def subir(pasta, porta, protecao, trava):
    roteiro = os.path.join(os.path.dirname(pasta), "motorista.py")
    open(roteiro, "w", encoding="utf-8").write(MOTORISTA)
    return subprocess.Popen([PYTHON, roteiro, os.path.join(pasta, "servidor"), str(porta),
                             "1" if protecao else "0", trava],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def derrubar(processo):
    subprocess.run(["taskkill", "/T", "/F", "/PID", str(processo.pid)], capture_output=True)
    try:
        processo.wait(10)
    except subprocess.TimeoutExpired:
        pass


def main():
    falhas, total = [], [0]

    def confere(nome, ok, detalhe=""):
        total[0] += 1
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, "" if ok else detalhe), flush=True)
        if not ok:
            falhas.append(nome)

    base = tempfile.mkdtemp(prefix="arena_queda_")
    try:
        # 1. Registro da queda ------------------------------------------------
        logs = os.path.join(base, "logs")
        filho = subprocess.run([PYTHON, "-c", FILHO_QUE_CAI, os.path.join(RAIZ, "servidor"), logs],
                               capture_output=True, timeout=60)
        confere("Python que le o endereco 0 cai como em 26/09 (0xC0000005)",
                filho.returncode == QUEDA_DE_VERDADE, hex(filho.returncode & 0xFFFFFFFF))
        try:
            texto = open(os.path.join(logs, "queda-do-servidor.txt"), encoding="utf-8").read()
        except OSError:
            texto = ""
        confere("registro diz que foi falha de acesso a memoria", "access violation" in texto, texto[-300:])
        confere("registro diz EM QUE FUNCAO caiu", "funcao_que_cai" in texto, texto[-300:])
        confere("registro tem a hora de abertura", "--- ARENA teste aberto em" in texto)

        # 2. ARENA.bat reabre o servidor que caiu -------------------------------
        raiz_bat = os.path.join(base, "bat")
        os.makedirs(os.path.join(raiz_bat, "servidor"))
        shutil.copy(os.path.join(RAIZ, "ARENA.bat"), raiz_bat)
        shutil.copytree(os.path.join(RAIZ, "servidor", "python"), os.path.join(raiz_bat, "servidor", "python"),
                        ignore=shutil.ignore_patterns("__pycache__"))
        open(os.path.join(raiz_bat, "servidor", "arena.py"), "w").write(ARENA_FALSO)
        ambiente = {k: v for k, v in os.environ.items() if k != "ARENA_REABERTO"}
        for modo, esperado_inicios, esperado_quedas, frase in (
                ("cai2", ["-", "1", "1"], 2, "ARENA encerrado."),
                ("caisempre", ["-", "1", "1", "1"], 4, "Caiu 4 vezes seguidas"),
                ("erro", ["-"], 0, "fechou com erro")):
            open(os.path.join(raiz_bat, "servidor", "modo.txt"), "w").write(modo)
            registro = os.path.join(raiz_bat, "servidor", "inicios.txt")
            if os.path.exists(registro):
                os.remove(registro)
            rodou = subprocess.run(["cmd", "/c", os.path.join(raiz_bat, "ARENA.bat")], cwd=raiz_bat,
                                   stdin=subprocess.DEVNULL, capture_output=True, timeout=120, env=ambiente)
            saida = rodou.stdout.decode("cp850", errors="replace")
            inicios = open(registro).read().split() if os.path.exists(registro) else []
            confere("ARENA.bat (%s): abriu %d vez(es), reabertas sem abrir outra janela" % (
                modo, len(esperado_inicios)), inicios == esperado_inicios, inicios)
            confere("ARENA.bat (%s): avisou %d queda(s) e '%s'" % (modo, esperado_quedas, frase),
                    saida.count("[QUEDA]") == esperado_quedas and frase in saida, saida[-400:])

        # 3. Janela preta travada: sem e com a protecao -------------------------
        copia = os.path.join(base, "copia", "ARENA")
        os.makedirs(copia)
        preparar_copia(copia)
        for protecao in (False, True):
            trava = os.path.join(base, "trava-%d" % protecao)
            porta = tela_sem_janela.porta_livre()
            processo = subir(copia, porta, protecao, trava)
            try:
                if not esperar_servidor(porta):
                    confere("servidor de verdade abriu (%s protecao)" % ("com" if protecao else "sem"), False)
                    continue
                catalogo = pedir(porta, "GET", "/api/catalogo")[1]
                jogo = next((j for j in catalogo.get("jogos", []) if "Fuzz" in j.get("titulo", "")), None)
                open(trava, "w").close()             # a partir daqui, a janela preta "nao anda"
                destino = "snes" if (jogo or {}).get("plataforma") == "nes" else "nes"
                inicio = time.monotonic()
                status, resposta = pedir(porta, "POST", "/api/jogo/mover",
                                         {"jogo_id": (jogo or {}).get("id", ""), "plataforma": destino}, espera=6)
                demorou = time.monotonic() - inicio
                if protecao:
                    confere("COM a protecao: mover jogo (escreve na janela travada) responde",
                            status == 200 and resposta.get("ok"), (status, resposta, round(demorou, 1)))
                    confere("COM a protecao: o servidor segue respondendo depois",
                            pedir(porta, "GET", "/api/estado")[0] == 200)
                else:
                    confere("SEM a protecao: o mesmo pedido fica preso (era o defeito)",
                            status is None and demorou >= 5, (status, round(demorou, 1)))
            finally:
                derrubar(processo)

        # 4. Edicao Rapida desligada numa janela de console nova ---------------
        saida_modo = os.path.join(base, "modo_console.txt")
        roteiro = os.path.join(base, "console.py")
        open(roteiro, "w", encoding="utf-8").write(
            "import ctypes, sys\nfrom ctypes import wintypes\nsys.path.insert(0, sys.argv[1])\n"
            "import janela_preta\nk = ctypes.WinDLL('kernel32')\n"
            "k.GetStdHandle.restype = wintypes.HANDLE\nk.GetStdHandle.argtypes = [wintypes.DWORD]\n"
            "k.GetConsoleMode.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]\n"
            "def modo():\n    m = wintypes.DWORD(0)\n"
            "    return m.value if k.GetConsoleMode(k.GetStdHandle(0xFFFFFFF6), ctypes.byref(m)) else -1\n"
            "antes = modo()\nmudou = janela_preta.desligar_edicao_rapida()\n"
            "open(sys.argv[2], 'w').write('%d %d %d' % (antes, int(mudou), modo()))\n")
        escondida = subprocess.STARTUPINFO()
        escondida.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        escondida.wShowWindow = 0
        subprocess.run(["conhost.exe", PYTHON, roteiro, os.path.join(RAIZ, "servidor"), saida_modo],
                       startupinfo=escondida, timeout=60)
        for _ in range(50):
            if os.path.exists(saida_modo):
                break
            time.sleep(0.2)
        try:
            antes, mudou, depois = (int(x) for x in open(saida_modo).read().split())
        except (OSError, ValueError):
            antes = mudou = depois = -1
        confere("janela de console nova: Edicao Rapida desligada (o clique nao trava mais)",
                depois >= 0 and not depois & 0x40 and depois & 0x80, (hex(antes), mudou, hex(depois)))
        if antes >= 0 and antes & 0x40:
            confere("a Edicao Rapida estava LIGADA antes (o padrao do Windows)", mudou == 1)

        # 5. A tela avisa e volta sozinha ---------------------------------------
        porta = tela_sem_janela.porta_livre()
        processo = subir(copia, porta, True, os.path.join(base, "sem-trava"))
        try:
            esperar_servidor(porta)
            with tela_sem_janela.Navegador() as nav:
                nav.abrir("http://127.0.0.1:%d/" % porta, espera=4)
                nav.avaliar("window.__antes_da_queda = 1")
                derrubar(processo)                     # o servidor some de uma vez, como numa queda
                nav.avaliar("pedir('/api/estado').then(() => 'respondeu', () => 'falhou')")
                confere("servidor fora: a tela mostra 'parou de responder'",
                        nav.avaliar("document.getElementById('semServidor').hidden") is False)
                processo = subir(copia, porta, True, os.path.join(base, "sem-trava"))
                esperar_servidor(porta)
                voltou = False
                for _ in range(40):
                    time.sleep(0.5)
                    try:
                        if nav.avaliar("window.__antes_da_queda === undefined && "
                                       "document.readyState === 'complete' && "
                                       "document.getElementById('semServidor').hidden"):
                            voltou = True
                            break
                    except OSError:
                        pass                           # pagina recarregando no meio da pergunta
                confere("servidor de volta: a tela recarrega sozinha e o aviso some", voltou)
        finally:
            derrubar(processo)
    finally:
        limpeza.apagar_pasta(base)

    print()
    if falhas:
        print("FALHOU: %d de %d" % (len(falhas), total[0]))
        return 1
    print("Servidor que cai: %d de %d certos." % (total[0], total[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
