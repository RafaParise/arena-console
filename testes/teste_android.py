# -*- coding: utf-8 -*-
r"""O ARENA no Android, no emulador (item 14 do plano de 15/10/2026).

Num aparelho virtual (o emulador do AOSP, com o Android 15 de codigo aberto:
ferramentas\preparar_android.py), sem janela, o APK de teste do ARENA
(ferramentas\montar_android.py --abi x86_64 --teste), instalado do zero:

  A. instala e ganha a permissao de arquivos, como o aluno daria;
  B. o teste poe uma pasta do ARENA no aparelho (/sdcard/ARENA, com um jogo
     livre de CHIP-8 e um de MSX), e o ARENA abre: o servidor de verdade
     (o mesmo do Windows, com o Python do APK) sobe, a tela de sempre carrega
     do 127.0.0.1:8777 e a pasta do ARENA e' achada sozinha (so ha uma);
  C. o /api/estado diz "android", a pasta escolhida e o RetroArch do APK; a
     lista tem os dois jogos da pasta;
  D. o jogo de CHIP-8 abre no RetroArch nativo (a tela de cima e' a do
     RetroArch, e a foto que o F8 tira tem a imagem do jogo); o F10 duas
     vezes (a tecla de sair do ARENA) fecha o jogo, e o servidor ve o
     processo do RetroArch terminar, como ve o retroarch.exe no Windows. As
     teclas vao pelo teclado de PC do emulador, seguradas como as de uma
     pessoa (o "input keyevent" do adb sai sem origem de teclado e solto na
     hora, e o RetroArch nao o le; achado de 21/10/2026);
  E. a partida a dois: o jogo de CHIP-8 hospedado, e o --host --port 55435
     chegando ao RetroArch do Android (que so o aceita pelo remendo
     android\retroarch\arena-args.patch); a porta 55435 escutando dentro do
     aparelho fica registrada (depende do nucleo);
  F. "Usar a pasta do app": o servidor reabre (o segredo novo, a tela
     recarrega sozinha) e a lista passa a ter os jogos livres do APK; um
     deles abre;
  G. o segredo: o mesmo /api/estado pedido de fora da tela do ARENA (pelo
     adb, chegando como um pedido do proprio aparelho) e' recusado (403).

A pagina e' lida pelo protocolo de depuracao do WebView (o APK de teste
deixa), pelo adb. No fim, o emulador desliga (--manter-ligado para nao).
O resultado, com os tempos, vai para docs\android_bruto.json.

Uso:
    servidor\python\python.exe testes\teste_android.py [--apk ARQUIVO] [--manter-ligado]
"""
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(RAIZ, "ferramentas"))
import preparar_android as sdk  # noqa: E402
from gravar_fundo_gif import ler_png  # noqa: E402
from tela_sem_janela import _WebSocket  # noqa: E402

ADB = os.path.join(sdk.SDK, "platform-tools", "adb.exe")
EMULADOR = os.path.join(sdk.SDK, "emulator", "emulator.exe")
PACOTE = "io.github.rafaparise.arena"
TELA_DO_ARENA = PACOTE + "/io.github.rafaparise.arena.ArenaActivity"
SERVIDOR = "http://127.0.0.1:8777"
FOTOS = os.path.join(os.environ.get("TEMP", "."), "teste_android_fotos")
PORTA_DE_DEPURACAO = 9333
PORTA_DE_FORA = 8778           # o adb leva para o 8777 do aparelho (o pedido sem o segredo)
PORTA_DA_PARTIDA = 55435
SEGUNDOS_DE_JOGO = 35          # partida curta demais nao conta tempo
# As teclas do ARENA, pelo codigo do Linux (o teclado de PC do emulador):
# o F10 sai do jogo (input_exit_emulator, duas vezes) e o F8 tira a foto.
F10 = 68
F8 = 66
TECLADO_DE_PC = "AT Translated Set 2 keyboard"     # o "qwerty2" e' o dos botoes de celular (68 vira MENU)


def adb(*argumentos, segundos=120):
    return subprocess.run([ADB] + list(argumentos), capture_output=True, timeout=segundos)


def adb_texto(*argumentos, segundos=120):
    return adb(*argumentos, segundos=segundos).stdout.decode("utf-8", "replace")


def ligado():
    return "emulator-" in adb_texto("devices")


def ligar_emulador():
    """Liga o aparelho virtual sem janela (ou usa o que ja estiver ligado)."""
    if ligado():
        return None, 0.0
    inicio = time.monotonic()
    processo = subprocess.Popen([EMULADOR, "-avd", sdk.NOME_DO_AVD, "-no-window", "-no-audio", "-no-snapshot",
                                 "-no-boot-anim", "-gpu", "swiftshader_indirect"], env=sdk.ambiente(),
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    fim = time.monotonic() + 420
    while time.monotonic() < fim:
        if adb_texto("shell", "getprop", "sys.boot_completed", segundos=15).strip() == "1":
            return processo, time.monotonic() - inicio
        time.sleep(3)
    raise SystemExit("O Android do emulador nao terminou de ligar em 7 minutos.")


def desligar_emulador(processo):
    adb("emu", "kill", segundos=30)
    if processo:
        try:
            processo.wait(60)
        except subprocess.TimeoutExpired:
            processo.kill()


def foto(nome):
    """A foto da tela do aparelho: (arquivo, quantas cores, a fracao da mais comum)."""
    os.makedirs(FOTOS, exist_ok=True)
    dados = adb("exec-out", "screencap", "-p", segundos=60).stdout
    caminho = os.path.join(FOTOS, nome + ".png")
    with open(caminho, "wb") as arquivo:
        arquivo.write(dados)
    largura, altura, pontos = ler_png(dados)
    amostra = pontos[::97]
    contagem = {}
    for p in amostra:
        contagem[p[:3]] = contagem.get(p[:3], 0) + 1
    return caminho, len(contagem), max(contagem.values()) / float(len(amostra))


def tela_de_cima():
    for linha in adb_texto("shell", "dumpsys", "activity", "activities").splitlines():
        if "topResumedActivity" in linha or "mResumedActivity" in linha:
            return linha.strip()
    return ""


def processo_do_retroarch():
    """O pid do processo principal do app (o do RetroArch), ou ""."""
    return adb_texto("shell", "pidof", PACOTE).strip()


_NO_DO_TECLADO = {}


def no_do_teclado():
    """O arquivo (/dev/input/eventN) do teclado de PC do emulador."""
    if "no" not in _NO_DO_TECLADO:
        atual = None
        for linha in adb_texto("shell", "getevent", "-p").splitlines():
            linha = linha.strip()
            if linha.startswith("add device"):
                atual = linha.split(":", 1)[1].strip()
            elif linha.startswith("name:") and TECLADO_DE_PC in linha:
                _NO_DO_TECLADO["no"] = atual
                break
    return _NO_DO_TECLADO.get("no")


AVISOS_DO_SISTEMA = []


def sem_aviso_do_sistema():
    """Fecha o aviso "System UI isn't responding" (o Android do emulador,
    logo depois de ligar, as vezes demora a responder; o aviso fica na frente
    do jogo e pega as teclas: visto em 21/10/2026). Anota quando havia um."""
    foco = next((l.strip() for l in adb_texto("shell", "dumpsys", "window", "windows").splitlines()
                 if "mCurrentFocus" in l), "")
    if "Not Responding" in foco or "isn't responding" in foco:
        AVISOS_DO_SISTEMA.append(foco[-120:])
        adb("shell", "am", "broadcast", "-a", "android.intent.action.CLOSE_SYSTEM_DIALOGS")
        time.sleep(2)


def apertar(codigo):
    """Aperta a tecla 'codigo' (o codigo do Linux) no teclado de PC do
    emulador, segurando um pouco, como uma pessoa (precisa do adb root, que o
    emulador do AOSP deixa)."""
    sem_aviso_do_sistema()
    no = no_do_teclado()
    adb("shell", "sendevent %s 1 %d 1; sendevent %s 0 0 0; sleep 0.12; sendevent %s 1 %d 0; sendevent %s 0 0 0"
        % (no, codigo, no, no, codigo, no))


def foto_do_jogo(nome):
    """A foto que o proprio RetroArch tira no F8: so o quadro do jogo, sem o
    controle desenhado na tela (a foto da tela inteira sempre tem cor, por
    causa dele). (arquivo, quantas cores, a fracao da mais comum), ou None."""
    marca = "/data/local/tmp/arena_antes_do_f8"
    adb("shell", "touch", marca)
    apertar(F8)
    time.sleep(3)
    achadas = adb_texto("shell", "find /storage/emulated/0/ARENA /data/user/0/%s/files -name '*.png' "
                                 "-path '*screenshots*' -newer %s 2>/dev/null" % (PACOTE, marca)).split()
    if not achadas:
        return None
    dados = adb("exec-out", "cat", achadas[-1], segundos=60).stdout
    os.makedirs(FOTOS, exist_ok=True)
    caminho = os.path.join(FOTOS, nome + "_retroarch.png")
    with open(caminho, "wb") as arquivo:
        arquivo.write(dados)
    _largura, _altura, pontos = ler_png(dados)
    contagem = {}
    for p in pontos[::7]:
        contagem[p[:3]] = contagem.get(p[:3], 0) + 1
    return caminho, len(contagem), max(contagem.values()) / float(sum(contagem.values()))


class Pagina:
    """A tela do ARENA no WebView, pelo protocolo de depuracao (CDP)."""

    def __init__(self, endereco=SERVIDOR, segundos=240):
        self.endereco = endereco
        self._conectar(segundos)

    def _conectar(self, segundos=240):
        endereco = self.endereco
        fim = time.monotonic() + segundos
        alvo = None
        while time.monotonic() < fim and not alvo:
            pid = adb_texto("shell", "pidof", PACOTE + ":tela").strip()
            if pid:
                adb("forward", "tcp:%d" % PORTA_DE_DEPURACAO, "localabstract:webview_devtools_remote_%s" % pid)
                try:
                    with urllib.request.urlopen("http://127.0.0.1:%d/json" % PORTA_DE_DEPURACAO, timeout=5) as r:
                        paginas = json.loads(r.read())
                    alvo = next((p for p in paginas if p.get("url", "").startswith(endereco)), None)
                except (OSError, ValueError):
                    alvo = None
            if not alvo:
                time.sleep(2)
        if not alvo:
            raise SystemExit("A tela do servidor do ARENA (%s) nao apareceu no WebView em %d s." % (endereco, segundos))
        self.ws = _WebSocket(alvo["webSocketDebuggerUrl"])
        self.n = 0

    def avaliar(self, expressao, segundos=60):
        self.n += 1
        mensagem = json.dumps({"id": self.n, "method": "Runtime.evaluate",
                               "params": {"expression": expressao, "awaitPromise": True, "returnByValue": True}})
        try:
            self.ws.s.settimeout(segundos)
            self.ws.enviar(mensagem)
        except OSError:
            # A ligacao com a pagina caiu antes de o pedido sair (nada chegou
            # a ela): liga de novo e manda outra vez.
            self._conectar()
            self.ws.s.settimeout(segundos)
            self.ws.enviar(mensagem)
        while True:
            resposta = json.loads(self.ws.receber())
            if resposta.get("id") == self.n:
                resultado = resposta.get("result", {})
                if "exceptionDetails" in resultado:
                    raise RuntimeError(json.dumps(resultado["exceptionDetails"])[:500])
                return resultado.get("result", {}).get("value")

    def pedir(self, rota, corpo=None):
        """Um pedido da propria tela (com o cookie do segredo, como o app.js)."""
        opcoes = {"headers": {"Content-Type": "application/json"}}
        if corpo is not None:
            opcoes.update(method="POST", body=json.dumps(corpo))
        return self.avaliar("fetch(%s, %s).then(r => r.json()).catch(e => ({erro: String(e)}))"
                            % (json.dumps(rota), json.dumps(opcoes)))

    def fechar(self):
        try:
            self.ws.fechar()
        except OSError:
            pass
        adb("forward", "--remove", "tcp:%d" % PORTA_DE_DEPURACAO)


def esperar(condicao, segundos):
    fim = time.monotonic() + segundos
    while time.monotonic() < fim:
        try:
            if condicao():
                return True
        except (OSError, RuntimeError, ValueError):
            pass
        time.sleep(1)
    return False


def sair_do_jogo():
    """O F10 duas vezes (input_exit_emulator, com o quit_press_twice do ARENA).
    Se o RetroArch nao fechar, o teste fecha o processo dele (o adb ja e'
    root desde o comeco: reiniciar o adb aqui derrubava a ligacao com a
    pagina)."""
    for _ in range(2):
        apertar(F10)
        time.sleep(1.5)
    if esperar(lambda: not processo_do_retroarch(), 20):
        return "F10"
    pid = processo_do_retroarch()
    if pid:
        adb("shell", "kill", pid)
    return "kill"


def jogar(pagina, jogo, resultado, falhas, rotulo, extra=None, durante=None):
    """Abre o jogo pela rota da tela, confere o RetroArch na frente e a foto,
    fecha pelo F10 e confere que o servidor viu o jogo terminar."""
    antes = time.monotonic()
    resposta = pagina.pedir("/api/jogar", dict({"jogo_id": jogo["id"]}, **(extra or {})))
    if not resposta or resposta.get("ok") is False or resposta.get("erro"):
        falhas.append("%s: /api/jogar respondeu %s" % (rotulo, resposta))
        return
    abriu = esperar(lambda: "RetroActivityFuture" in tela_de_cima(), 90)
    resultado[rotulo + "_abriu_s"] = round(time.monotonic() - antes, 1)
    if not abriu:
        falhas.append("%s: o RetroArch nao ficou na frente (%s)" % (rotulo, tela_de_cima()))
        return
    time.sleep(10)
    caminho, cores, maior = foto(rotulo)
    resultado[rotulo + "_foto"] = {"arquivo": os.path.basename(caminho), "cores": cores, "a_mais_comum": round(maior, 3)}
    do_jogo = foto_do_jogo(rotulo)
    if not do_jogo:
        falhas.append("%s: o F8 nao tirou a foto do jogo (a tecla nao chegou ao RetroArch?)" % rotulo)
    else:
        caminho, cores, maior = do_jogo
        resultado[rotulo + "_foto_do_retroarch"] = {"arquivo": os.path.basename(caminho), "cores": cores, "a_mais_comum": round(maior, 3)}
        if cores < 2 or maior > 0.995:
            falhas.append("%s: o jogo nao tem imagem (%d cores)" % (rotulo, cores))
    if durante:
        durante()
    time.sleep(max(0, SEGUNDOS_DE_JOGO - (time.monotonic() - antes)))
    resultado[rotulo + "_saiu_por"] = sair_do_jogo()
    voltou = esperar(lambda: "ArenaActivity" in tela_de_cima(), 30)
    if not voltou:
        adb("shell", "am", "start", "-n", TELA_DO_ARENA)
    fechado = esperar(lambda: not (pagina.pedir("/api/estado") or {}).get("jogo_em_andamento", {}).get("ativo"),
                      30)
    resultado[rotulo + "_fechou_s"] = round(time.monotonic() - antes, 1)
    if not fechado:
        falhas.append("%s: o servidor nao viu o jogo fechar" % rotulo)


def porta_da_partida_escuta():
    """O RetroArch hospedando: a porta 55435 de dentro do aparelho atende (pelo adb)."""
    adb("forward", "tcp:%d" % PORTA_DA_PARTIDA, "tcp:%d" % PORTA_DA_PARTIDA)
    try:
        with socket.create_connection(("127.0.0.1", PORTA_DA_PARTIDA), timeout=5) as conexao:
            conexao.settimeout(5)
            try:
                return len(conexao.recv(4)) > 0      # o RetroArch fala primeiro (o cabecalho do netplay)
            except socket.timeout:
                return True
    except OSError:
        return False
    finally:
        adb("forward", "--remove", "tcp:%d" % PORTA_DA_PARTIDA)


def linha_de_comando_do_retroarch():
    """Os argumentos que o RetroArch do APK recebeu na ultima abertura (ele os
    escreve no logcat, um por linha, depois de "[ENV] Command line (ARGS)")."""
    argumentos, lendo = [], False
    for linha in adb_texto("logcat", "-d", "-s", "RetroArch", segundos=60).splitlines():
        texto = linha.split("RetroArch:", 1)[-1].strip()
        if "Command line (ARGS):" in texto:
            argumentos, lendo = [texto.split("(ARGS):", 1)[1].strip().strip('".')], True
        elif lendo:
            if texto.startswith("["):
                lendo = False
            else:
                argumentos.append(texto.strip('".'))
    return [a for a in argumentos if a]


def pedido_de_fora():
    """O /api/estado pedido sem a tela do ARENA: pelo adb, ele chega ao
    servidor como um pedido do proprio aparelho (o que outro app faria)."""
    adb("forward", "tcp:%d" % PORTA_DE_FORA, "tcp:8777")
    try:
        pedido = urllib.request.Request("http://127.0.0.1:%d/api/estado" % PORTA_DE_FORA,
                                        headers={"Host": "127.0.0.1:8777"})
        with urllib.request.urlopen(pedido, timeout=10) as resposta:
            return resposta.status
    except urllib.error.HTTPError as erro:
        return erro.code
    except OSError as falha:
        return str(falha)
    finally:
        adb("forward", "--remove", "tcp:%d" % PORTA_DE_FORA)


def principal():
    apk = sys.argv[sys.argv.index("--apk") + 1] if "--apk" in sys.argv else None
    if not apk:
        pasta = os.path.join(sdk.BASE, "apk")
        candidatos = sorted(n for n in os.listdir(pasta) if n.endswith("-x86_64-teste.apk")) if os.path.isdir(pasta) else []
        if not candidatos:
            raise SystemExit("Monte antes o APK de teste: ferramentas\\montar_android.py --abi x86_64 --teste")
        apk = os.path.join(pasta, candidatos[-1])
    resultado = {"quando": time.strftime("%Y-%m-%d %H:%M:%S"), "apk": os.path.basename(apk)}
    falhas = []
    processo, ligou = ligar_emulador()
    resultado["emulador_ligou_s"] = round(ligou, 1)
    resultado["android"] = adb_texto("shell", "getprop", "ro.build.version.release").strip()
    # O adb como root uma vez so, antes de tudo (as teclas pelo teclado de PC
    # e o fechar do RetroArch precisam; ligado no meio, ele derrubava a
    # ligacao com a pagina).
    adb("root", segundos=60)
    time.sleep(3)
    adb("wait-for-device", segundos=120)
    if ligou:
        # Ligado agora, a frio: o Android ainda arruma a casa por um tempo, e
        # a interface do sistema chegou a parar de responder no meio do jogo.
        time.sleep(30)
    pagina = None
    try:
        # A. instalar do zero, com a permissao de arquivos (o aluno toca em Permitir)
        adb("uninstall", PACOTE, segundos=120)
        antes = time.monotonic()
        instalou = adb("install", apk, segundos=600)
        resultado["instalou_s"] = round(time.monotonic() - antes, 1)
        if instalou.returncode != 0:
            raise SystemExit("O APK nao instalou: %s" % (instalou.stdout + instalou.stderr).decode("utf-8", "replace"))
        for permissao in ("READ_EXTERNAL_STORAGE", "WRITE_EXTERNAL_STORAGE"):
            adb("shell", "pm", "grant", PACOTE, "android.permission." + permissao)
        adb("shell", "appops", "set", PACOTE, "MANAGE_EXTERNAL_STORAGE", "allow")
        # O aviso de tela cheia do Android ("Viewing full screen... Got it")
        # aparece na primeira tela cheia de cada app e fica na frente do jogo,
        # com as teclas, ate a pessoa tocar em "Entendi" (o aluno faz isso uma
        # vez). O teste o marca como visto.
        adb("shell", "settings", "put", "secure", "immersive_mode_confirmations", "confirmed")
        # B. a pasta do ARENA no aparelho, com um jogo de CHIP-8 e um de MSX em
        # jogos/pessoais (os "Meus jogos", como no Windows: a lista so procura
        # nas origens do indexador; direto em jogos/<console>, nao acha nada)
        with open(os.path.join(RAIZ, "testes", "jogos_livres", "lista.json"), encoding="utf-8") as arquivo:
            livres = json.load(arquivo)["arquivos"]
        adb("shell", "rm", "-rf", "/sdcard/ARENA")
        for console, pasta_console in (("chip8", "CHIP-8"), ("msx", "MSX")):
            item = next(j for j in livres if j["console"] == console)
            destino = "/sdcard/ARENA/jogos/pessoais/%s" % pasta_console
            adb("shell", "mkdir", "-p", destino, "/sdcard/ARENA/retroarch")
            adb("push", os.path.join(RAIZ, "testes", "jogos_livres", *item["origem"].split("/")),
                "%s/%s" % (destino, os.path.basename(item["origem"])))
        adb("logcat", "-c")
        antes = time.monotonic()
        adb("shell", "am", "start", "-n", TELA_DO_ARENA)
        pagina = Pagina()
        pronta = esperar(lambda: pagina.avaliar("document.readyState === 'complete' && !!window.fetch"), 60)
        resultado["servidor_e_tela_s"] = round(time.monotonic() - antes, 1)
        if not pronta:
            falhas.append("B: a tela do servidor nao terminou de carregar")
        time.sleep(4)
        caminho, cores, maior = foto("tela")
        resultado["tela_foto"] = {"arquivo": os.path.basename(caminho), "cores": cores, "a_mais_comum": round(maior, 3)}
        if cores < 3:
            falhas.append("B: a foto da tela do ARENA nao tem imagem")
        # C. o estado e a lista
        estado = pagina.pedir("/api/estado") or {}
        android = estado.get("android") or {}
        resultado["estado"] = {"sistema": estado.get("sistema_do_computador"), "pasta": android.get("pasta"),
                               "so_leitura": android.get("so_leitura"), "retroarch": estado.get("retroarch_presente"),
                               "cpu": (estado.get("maquina") or {}).get("cpu"),
                               "gpu": ((estado.get("maquina") or {}).get("gpu") or {}).get("nome"),
                               "nota": (estado.get("capacidade") or {}).get("nota")}
        if estado.get("sistema_do_computador") != "android":
            falhas.append("C: o servidor nao disse android (%s)" % (estado.get("erro") or estado.get("sistema_do_computador")))
        if not str(android.get("pasta") or "").rstrip("/").endswith("/ARENA"):
            falhas.append("C: a pasta do ARENA do aparelho nao foi escolhida sozinha (%s)" % android.get("pasta"))
        if not estado.get("retroarch_presente"):
            falhas.append("C: o servidor nao achou o RetroArch do APK")
        catalogo = pagina.pedir("/api/catalogo") or {}
        jogos = catalogo.get("jogos", [])
        resultado["jogos_na_lista"] = len(jogos)
        chip8 = next((j for j in jogos if j.get("plataforma") == "chip8"), None)
        msx = next((j for j in jogos if j.get("plataforma") == "msx"), None)
        if not (chip8 and msx):
            falhas.append("C: os jogos da pasta do ARENA nao estao na lista (%d jogos)" % len(jogos))
        # D. o jogo no RetroArch nativo, e o fim visto pelo servidor
        if chip8:
            jogar(pagina, chip8, resultado, falhas, "D_chip8")
        # E. a partida hospedada: o --host chega ao RetroArch do APK pelo
        # remendo (a linha de comando inteira, como no Windows). Com o CHIP-8:
        # os outros consoles dos jogos livres recusam o jogo em rede
        # (consoles.json -> netplay false, como o MSX, que o teste usava). A
        # porta aberta fica so registrada: quem hospeda e' o nucleo, e o do
        # CHIP-8 nao a abriu nem no Windows (21/10/2026).
        if chip8:
            escuta = {}
            adb("logcat", "-c")
            jogar(pagina, chip8, resultado, falhas, "E_partida", extra={"partida": "hospedar"},
                  durante=lambda: escuta.update(ok=porta_da_partida_escuta()))
            resultado["E_porta_55435_escutando"] = escuta.get("ok")
            argumentos = linha_de_comando_do_retroarch()
            resultado["E_linha_de_comando"] = argumentos
            if not ("--host" in argumentos and "55435" in argumentos):
                falhas.append("E: o --host da partida nao chegou ao RetroArch do APK (%s)" % " ".join(argumentos)[:200])
        # G. sem o segredo, nada (o que outro app do aparelho faria)
        resultado["G_pedido_de_fora"] = pedido_de_fora()
        if resultado["G_pedido_de_fora"] != 403:
            falhas.append("G: o pedido sem o segredo nao foi recusado (%s)" % resultado["G_pedido_de_fora"])
        # F. a pasta do app: o servidor reabre e a lista tem os jogos livres do APK
        antes = time.monotonic()
        resposta = pagina.pedir("/api/android/pasta", {"caminho": ""})
        if not (resposta or {}).get("reabrindo"):
            falhas.append("F: a troca para a pasta do app nao foi aceita (%s)" % resposta)
        pagina.fechar()
        time.sleep(5)
        pagina = Pagina()
        esperar(lambda: (pagina.pedir("/api/estado") or {}).get("sistema_do_computador") == "android", 120)
        resultado["F_reabriu_s"] = round(time.monotonic() - antes, 1)
        catalogo = pagina.pedir("/api/catalogo") or {}
        jogos = catalogo.get("jogos", [])
        resultado["F_jogos_livres"] = len(jogos)
        if len(jogos) < 5:
            falhas.append("F: a pasta do app nao recebeu os jogos livres do APK (%d jogos)" % len(jogos))
        zx81 = next((j for j in jogos if j.get("plataforma") == "zx81"), None)
        if zx81:
            jogar(pagina, zx81, resultado, falhas, "F_livre")
        # Os erros: da pagina (o console dela vai para o logcat com a etiqueta
        # ARENA) e do servidor (ARENA-servidor).
        registro = adb_texto("logcat", "-d", "-s", "ARENA", "ARENA-servidor", segundos=60)
        erros = [l.strip() for l in registro.splitlines() if "Uncaught" in l or "TypeError" in l
                 or "ReferenceError" in l or "SyntaxError" in l or "Traceback" in l]
        resultado["erros"] = erros[:10]
        resultado["servidor_registro"] = [l.strip() for l in registro.splitlines() if "ARENA-servidor" in l][:40]
        if erros:
            falhas.append("erro na tela ou no servidor: %s" % erros[0][:200])
    finally:
        if pagina:
            pagina.fechar()
        adb("shell", "am", "force-stop", PACOTE)
        if "--manter-ligado" not in sys.argv:
            desligar_emulador(processo)
        resultado["avisos_do_sistema_fechados"] = AVISOS_DO_SISTEMA
        resultado["falhas"] = falhas
        with open(os.path.join(RAIZ, "docs", "android_bruto.json"), "w", encoding="utf-8") as arquivo:
            json.dump(resultado, arquivo, ensure_ascii=False, indent=1)
    print(json.dumps(resultado, ensure_ascii=False, indent=1))
    if falhas:
        print("\nFALHAS:\n  " + "\n  ".join(falhas))
        return 1
    print("\nTudo certo. Fotos: %s" % FOTOS)
    return 0


if __name__ == "__main__":
    socket.setdefaulttimeout(60)
    sys.exit(principal())
