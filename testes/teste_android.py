# -*- coding: utf-8 -*-
r"""O ARENA no Android, no emulador (item 14 do plano de 15/10/2026).

Num aparelho virtual (o emulador do AOSP, com o Android 15 de codigo aberto:
ferramentas\preparar_android.py), sem janela, o APK de teste do ARENA
(ferramentas\montar_android.py --abi x86_64 --teste):

  A. instala e ganha a permissao de arquivos, como o aluno daria;
  B. a tela do ARENA abre (a foto da tela tem imagem de verdade) e a pagina
     carrega sem erro, com a ponte do Android e os nucleos do APK;
  C. a pasta do ARENA no aparelho: o teste poe uma (/sdcard/ARENA, com um
     jogo livre de CHIP-8 em jogos/pessoais), a pagina acha e o jogo entra
     na lista;
  D. um jogo livre que vem no APK abre no RetroArch nativo (a tela de cima e'
     a do RetroArch, e a foto tem a imagem do jogo) e, de volta a tela do
     ARENA, o tempo de jogo conta;
  E. o jogo da pasta do ARENA abre do mesmo jeito.

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
FOTOS = os.path.join(os.environ.get("TEMP", "."), "teste_android_fotos")
PORTA_DE_DEPURACAO = 9333
SEGUNDOS_DE_JOGO = 35          # partida de 30 s ou menos nao conta tempo (rotas.js)


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


class Pagina:
    """A pagina do ARENA no WebView, pelo protocolo de depuracao (CDP)."""

    def __init__(self):
        pid = ""
        for _ in range(30):
            pid = adb_texto("shell", "pidof", PACOTE + ":tela").strip()
            if pid:
                break
            time.sleep(1)
        if not pid:
            raise SystemExit("A tela do ARENA (o processo :tela) nao abriu.")
        adb("forward", "tcp:%d" % PORTA_DE_DEPURACAO, "localabstract:webview_devtools_remote_%s" % pid)
        alvo = None
        for _ in range(30):
            try:
                with urllib.request.urlopen("http://127.0.0.1:%d/json" % PORTA_DE_DEPURACAO, timeout=5) as r:
                    paginas = json.loads(r.read())
                alvo = next((p for p in paginas if "arena.local" in p.get("url", "")), None)
            except (OSError, ValueError):
                alvo = None
            if alvo:
                break
            time.sleep(1)
        if not alvo:
            raise SystemExit("Nao achei a pagina do ARENA no WebView (o APK e' o de teste?).")
        self.ws = _WebSocket(alvo["webSocketDebuggerUrl"])
        self.n = 0

    def avaliar(self, expressao, segundos=60):
        self.n += 1
        self.ws.s.settimeout(segundos)
        self.ws.enviar(json.dumps({"id": self.n, "method": "Runtime.evaluate",
                                   "params": {"expression": expressao, "awaitPromise": True,
                                              "returnByValue": True}}))
        while True:
            resposta = json.loads(self.ws.receber())
            if resposta.get("id") == self.n:
                resultado = resposta.get("result", {})
                if "exceptionDetails" in resultado:
                    raise RuntimeError(json.dumps(resultado["exceptionDetails"])[:500])
                return resultado.get("result", {}).get("value")

    def pedir(self, rota, corpo=None):
        opcoes = "{}" if corpo is None else json.dumps({"method": "POST", "body": json.dumps(corpo)})
        return self.avaliar("fetch(%s, %s).then(r => r.json())" % (json.dumps(rota), opcoes))

    def fechar(self):
        self.ws.fechar()
        adb("forward", "--remove", "tcp:%d" % PORTA_DE_DEPURACAO)


def esperar(condicao, segundos):
    fim = time.monotonic() + segundos
    while time.monotonic() < fim:
        if condicao():
            return True
        time.sleep(1)
    return False


def jogar(pagina, jogo, resultado, falhas, rotulo):
    """Abre o jogo pela rota da tela, confere o RetroArch na frente e a foto,
    volta para a tela do ARENA e confere que o tempo contou."""
    antes = time.monotonic()
    resposta = pagina.pedir("/api/jogar", {"jogo_id": jogo["id"]})
    if not resposta or resposta.get("ok") is False:
        falhas.append("%s: /api/jogar respondeu %s" % (rotulo, resposta))
        return
    abriu = esperar(lambda: "RetroActivityFuture" in tela_de_cima(), 60)
    resultado[rotulo + "_abriu_s"] = round(time.monotonic() - antes, 1)
    if not abriu:
        falhas.append("%s: o RetroArch nao ficou na frente (%s)" % (rotulo, tela_de_cima()))
        return
    time.sleep(10)
    caminho, cores, maior = foto(rotulo)
    resultado[rotulo + "_foto"] = {"arquivo": caminho, "cores": cores, "a_mais_comum": round(maior, 3)}
    if cores < 2 or maior > 0.995:
        falhas.append("%s: a tela do jogo nao tem imagem (%d cores)" % (rotulo, cores))
    time.sleep(max(0, SEGUNDOS_DE_JOGO - (time.monotonic() - antes)))
    adb("shell", "am", "start", "-n", TELA_DO_ARENA)            # de volta a tela do ARENA
    voltou = esperar(lambda: "ArenaActivity" in tela_de_cima(), 30)
    if not voltou:
        falhas.append("%s: a tela do ARENA nao voltou" % rotulo)
        return
    fechado = esperar(lambda: not (pagina.pedir("/api/estado") or {}).get("jogo_em_andamento", {}).get("ativo"), 30)
    if not fechado:
        falhas.append("%s: a tela nao viu o jogo fechar" % rotulo)


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
    try:
        # A. instalar, com a permissao de arquivos (o aluno toca em Permitir)
        antes = time.monotonic()
        instalou = adb("install", "-r", apk, segundos=600)
        resultado["instalou_s"] = round(time.monotonic() - antes, 1)
        if instalou.returncode != 0:
            raise SystemExit("O APK nao instalou: %s" % (instalou.stdout + instalou.stderr).decode("utf-8", "replace"))
        for permissao in ("READ_EXTERNAL_STORAGE", "WRITE_EXTERNAL_STORAGE"):
            adb("shell", "pm", "grant", PACOTE, "android.permission." + permissao)
        # C. a pasta do ARENA no aparelho, com um jogo livre de CHIP-8
        with open(os.path.join(RAIZ, "testes", "jogos_livres", "lista.json"), encoding="utf-8") as arquivo:
            chip8 = next(j for j in json.load(arquivo)["arquivos"] if j["console"] == "chip8")
        adb("shell", "rm", "-rf", "/sdcard/ARENA")
        adb("shell", "mkdir", "-p", "/sdcard/ARENA/jogos/pessoais/CHIP-8", "/sdcard/ARENA/retroarch")
        adb("push", os.path.join(RAIZ, "testes", "jogos_livres", *chip8["origem"].split("/")),
            "/sdcard/ARENA/jogos/pessoais/CHIP-8/" + os.path.basename(chip8["origem"]))
        # B. a tela abre
        adb("shell", "am", "force-stop", PACOTE)
        adb("logcat", "-c")
        antes = time.monotonic()
        adb("shell", "am", "start", "-n", TELA_DO_ARENA)
        pagina = Pagina()
        pronta = esperar(lambda: pagina.avaliar("!!(window.ArenaRotas && window.ArenaNoAparelho && "
                                                "document.querySelector('#listaJogos, .jogos, main'))"), 60)
        resultado["tela_abriu_s"] = round(time.monotonic() - antes, 1)
        if not pronta:
            falhas.append("B: a pagina do ARENA nao ficou pronta")
        time.sleep(3)
        caminho, cores, maior = foto("tela")
        resultado["tela_foto"] = {"arquivo": caminho, "cores": cores, "a_mais_comum": round(maior, 3)}
        if cores < 3:
            falhas.append("B: a foto da tela do ARENA nao tem imagem")
        sistema = pagina.avaliar("window.ArenaNoAparelho.sistema")
        resultado["sistema"] = {k: sistema.get(k) for k in ("android", "abi", "modelo")}
        resultado["nucleos_no_apk"] = len(sistema.get("nucleos", []))
        if resultado["nucleos_no_apk"] < 50:
            falhas.append("B: o APK veio com poucos nucleos (%d)" % resultado["nucleos_no_apk"])
        # C. a pagina acha a pasta
        situacao = pagina.avaliar("ArenaPasta.escolher().then(s => s, e => ({erro: String(e.message)}))")
        resultado["pasta"] = situacao
        if not (situacao or {}).get("tem"):
            falhas.append("C: a pasta do ARENA no aparelho nao foi achada (%s)" % situacao)
        pagina.avaliar("location.reload()")
        time.sleep(2)
        pagina.fechar()
        pagina = Pagina()
        esperar(lambda: pagina.avaliar("!!window.ArenaRotas"), 60)
        catalogo = pagina.pedir("/api/catalogo") or {}
        jogos = catalogo.get("jogos", [])
        resultado["jogos_na_lista"] = len(jogos)
        livre = next((j for j in jogos if j.get("origem") == "vem_com"), None)
        da_pasta = next((j for j in jogos if j.get("plataforma") == "chip8" and j.get("origem") != "vem_com"), None)
        if not livre:
            falhas.append("C: os jogos livres que vem no APK nao estao na lista")
        if not da_pasta:
            falhas.append("C: o jogo da pasta do ARENA nao entrou na lista")
        # D e E. os jogos no RetroArch nativo
        if livre:
            jogar(pagina, livre, resultado, falhas, "D_livre")
        if da_pasta:
            jogar(pagina, da_pasta, resultado, falhas, "E_da_pasta")
        # O que a pagina escreveu no console vai para o registro do Android
        # (ArenaActivity.onConsoleMessage, com a etiqueta ARENA).
        registro = adb_texto("logcat", "-d", "-s", "ARENA", segundos=60)
        erros = [l.strip() for l in registro.splitlines() if "Uncaught" in l or "TypeError" in l
                 or "ReferenceError" in l or "SyntaxError" in l]
        resultado["erros_da_pagina"] = erros[:10]
        if erros:
            falhas.append("B: erro de JavaScript na pagina: %s" % erros[0][:200])
        pagina.fechar()
    finally:
        adb("shell", "am", "force-stop", PACOTE)
        if "--manter-ligado" not in sys.argv:
            desligar_emulador(processo)
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
