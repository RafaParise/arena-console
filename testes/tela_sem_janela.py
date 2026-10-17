# -*- coding: utf-8 -*-
r"""Fotos e conferencias da TELA do ARENA sem abrir janela nenhuma.

Por que existe (01/10/2026): a aba do navegador controlado pelo Claude fica
"escondida" (visibilityState = hidden) quando a janela dele nao esta a
frente -- e ai nem foto da tela, nem animacao, nem medida de quadro
funcionam. Aqui o Edge (ou o Chrome) roda em modo "headless" (sem janela,
mas desenhando de verdade) e e' controlado pelo protocolo de depuracao do
proprio navegador (Chrome DevTools Protocol), so com a biblioteca padrao
do Python: um WebSocket minimo escrito a mao.

Serve para:
  - foto da tela em qualquer tamanho, inclusive 4K (3840x2160) e com a
    escala do Windows (150%, 200%) -- pagina(..., escala=2);
  - rodar JavaScript na pagina e ler o resultado (avaliar);
  - conferir se o fundo animado esta desenhando (a aba headless conta como
    visivel).

Uso como ferramenta (o ARENA precisa estar aberto em 127.0.0.1:8777):
    servidor\python\python.exe testes\tela_sem_janela.py [saida.png] [largura altura escala]
Uso nos testes:
    with Navegador() as nav:
        nav.abrir("http://127.0.0.1:8777", largura=1366, altura=768)
        nav.avaliar("document.title")
        nav.foto("tela.png")
"""
import base64
import json
import os
import socket
import struct
import subprocess
import sys
import tempfile
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import limpeza  # noqa: E402

_LOCAL = os.environ.get("LOCALAPPDATA", "")
CANDIDATOS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.join(_LOCAL, r"Google\Chrome\Application\chrome.exe"),
    os.path.join(_LOCAL, r"Microsoft\Edge\Application\msedge.exe"),
]


def achar_navegador():
    return next((c for c in CANDIDATOS if c and os.path.isfile(c)), None)


def porta_livre():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    porta = s.getsockname()[1]
    s.close()
    return porta


class _WebSocket:
    """O minimo de WebSocket (RFC 6455) para conversar com o navegador:
    texto mascarado na ida, texto (ou continuacao) na volta."""

    def __init__(self, url):
        resto = url.split("://", 1)[1]
        endereco, caminho = resto.split("/", 1)
        host, porta = endereco.split(":")
        self.s = socket.create_connection((host, int(porta)), timeout=60)
        chave = base64.b64encode(os.urandom(16)).decode()
        pedido = ("GET /%s HTTP/1.1\r\nHost: %s\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                  "Sec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n\r\n" % (caminho, endereco, chave))
        self.s.sendall(pedido.encode())
        resposta = b""
        while b"\r\n\r\n" not in resposta:
            pedaco = self.s.recv(4096)
            if not pedaco:
                raise OSError("o navegador fechou a conexao de depuracao")
            resposta += pedaco
        if b" 101 " not in resposta.split(b"\r\n", 1)[0]:
            raise OSError("o navegador recusou a conexao de depuracao")
        self.sobra = resposta.split(b"\r\n\r\n", 1)[1]

    def enviar(self, texto):
        dados = texto.encode("utf-8")
        cabeca = bytearray([0x81])
        n = len(dados)
        if n < 126:
            cabeca.append(0x80 | n)
        elif n < 65536:
            cabeca.append(0x80 | 126)
            cabeca += struct.pack(">H", n)
        else:
            cabeca.append(0x80 | 127)
            cabeca += struct.pack(">Q", n)
        mascara = os.urandom(4)
        cabeca += mascara
        self.s.sendall(bytes(cabeca) + bytes(b ^ mascara[i % 4] for i, b in enumerate(dados)))

    def _ler(self, n):
        while len(self.sobra) < n:
            pedaco = self.s.recv(1 << 20)
            if not pedaco:
                raise OSError("conexao de depuracao caiu")
            self.sobra += pedaco
        saida, self.sobra = self.sobra[:n], self.sobra[n:]
        return saida

    def receber(self):
        partes = []
        while True:
            b0, b1 = self._ler(2)
            n = b1 & 0x7f
            if n == 126:
                n = struct.unpack(">H", self._ler(2))[0]
            elif n == 127:
                n = struct.unpack(">Q", self._ler(8))[0]
            if b1 & 0x80:
                self._ler(4)            # o servidor nao mascara, mas por via das duvidas
            dados = self._ler(n)
            tipo = b0 & 0x0f
            if tipo == 0x8:
                raise OSError("o navegador fechou a conexao de depuracao")
            if tipo in (0x9, 0xA):      # ping/pong: ignora
                continue
            partes.append(dados)
            if b0 & 0x80:
                return b"".join(partes).decode("utf-8", "replace")

    def fechar(self):
        try:
            self.s.close()
        except OSError:
            pass


class Navegador:
    """Edge/Chrome sem janela, controlado pelo protocolo de depuracao."""

    def __init__(self, executavel=None, janela=False, tamanho=(1180, 760)):
        """janela=True (auditoria 3, 07/10/2026): COM janela, como o ARENA
        abre a tela (arena.abrir_janela: --app, 1180x760) -- para medir a
        abertura, a memoria e o processador da tela de verdade. O perfil
        continua temporario: o Edge do usuario nao e' tocado."""
        self.exe = executavel or achar_navegador()
        if not self.exe:
            raise OSError("nenhum Edge ou Chrome encontrado")
        self.perfil = tempfile.mkdtemp(prefix="arena_navegador_")
        self.porta = porta_livre()
        self.janela = janela
        self.tamanho = tamanho
        self.proc = None
        self.ws = None
        self.n = 0
        self.eventos = []     # avisos do navegador (Network.*, Page.*...)

    def __enter__(self):
        comuns = ["--remote-debugging-port=%d" % self.porta, "--user-data-dir=" + self.perfil,
                  "--no-first-run", "--no-default-browser-check", "--disable-extensions"]
        if self.janela:
            argumentos = comuns + ["--app=about:blank", "--window-size=%d,%d" % self.tamanho,
                                   "--disable-features=Translate,AutofillServerCommunication"]
        else:
            argumentos = ["--headless=new"] + comuns + ["--hide-scrollbars", "--mute-audio", "about:blank"]
        self.proc = subprocess.Popen([self.exe] + argumentos,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        alvo = None
        for _ in range(100):
            try:
                with urllib.request.urlopen("http://127.0.0.1:%d/json" % self.porta, timeout=2) as r:
                    alvos = json.loads(r.read())
                alvo = next((a for a in alvos if a.get("type") == "page"), None)
                if alvo:
                    break
            except OSError:
                pass
            time.sleep(0.1)
        if not alvo:
            self.__exit__(None, None, None)
            raise OSError("o navegador sem janela nao respondeu")
        self.ws = _WebSocket(alvo["webSocketDebuggerUrl"])
        self.comando("Page.enable")
        self.comando("Runtime.enable")
        return self

    def __exit__(self, *_):
        if self.ws:
            self.ws.fechar()
        # Achado de 01/10/2026: 128 processos do Edge de teste vivos desde a
        # madrugada (1,8 GB de memoria) e 12 perfis no Temp (2,2 GB). O
        # processo que este script abre e' so um lancador: entrega para o
        # Edge de verdade e morre -- kill() e taskkill /T nao alcancam os
        # filhos. Agora: (1) o proprio navegador fecha tudo (Browser.close,
        # pelo endereco do navegador inteiro, nao da aba); (2) se nao der,
        # encerra os processos que usam ESTE perfil (nunca o Edge do usuario).
        self._fechar_navegador()
        if self._processos_do_perfil(encerrar=False):
            self._processos_do_perfil(encerrar=True)
        if self.proc:
            try:
                self.proc.wait(5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        limpeza.apagar_pasta(self.perfil, segundos=15)

    def _fechar_navegador(self):
        try:
            with urllib.request.urlopen("http://127.0.0.1:%d/json/version" % self.porta, timeout=2) as r:
                endereco = json.loads(r.read())["webSocketDebuggerUrl"]
            ws = _WebSocket(endereco)
            ws.enviar(json.dumps({"id": 1, "method": "Browser.close"}))
            try:
                ws.receber()
            except (OSError, ValueError):
                pass
            ws.fechar()
        except (OSError, ValueError, KeyError):
            return False
        fim = time.monotonic() + 10       # espera o navegador sair de vez
        while time.monotonic() < fim and self._processos_do_perfil(encerrar=False):
            time.sleep(0.3)
        return True

    def pids(self):
        """Os processos deste navegador (os que usam o perfil deste teste):
        para medir a memoria e o processador da tela."""
        comando = ("Get-CimInstance Win32_Process -Filter \"Name = '%s'\" | Where-Object "
                   "{ $_.CommandLine -like '*%s*' } | ForEach-Object { $_.ProcessId }"
                   % (os.path.basename(self.exe), self.perfil))
        try:
            saida = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", comando],
                                   capture_output=True, text=True, timeout=30).stdout
        except (OSError, subprocess.TimeoutExpired):
            return []
        return [int(linha) for linha in saida.split() if linha.strip().isdigit()]

    def _processos_do_perfil(self, encerrar):
        """Quantos processos do navegador usam o perfil DESTE teste (e, com
        encerrar=True, encerra esses -- so esses)."""
        if encerrar:
            acao = "| ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }; 0"
        else:
            acao = "| Measure-Object | Select-Object -ExpandProperty Count"
        comando = ("Get-CimInstance Win32_Process -Filter \"Name = '%s'\" | Where-Object "
                   "{ $_.CommandLine -like '*%s*' } %s" % (os.path.basename(self.exe), self.perfil, acao))
        try:
            saida = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", comando],
                                   capture_output=True, text=True, timeout=30).stdout.strip()
            return int(saida.splitlines()[-1]) if saida else 0
        except (OSError, ValueError, subprocess.TimeoutExpired):
            return 0

    def comando(self, metodo, **parametros):
        self.n += 1
        self.ws.enviar(json.dumps({"id": self.n, "method": metodo, "params": parametros}))
        while True:
            msg = json.loads(self.ws.receber())
            if msg.get("id") == self.n:
                if "error" in msg:
                    raise OSError("%s: %s" % (metodo, msg["error"].get("message")))
                return msg.get("result", {})
            if "method" in msg:
                self.eventos.append(msg)      # ex.: Network.requestWillBeSent

    def esperar(self, segundos):
        """Espera e depois recolhe o que o navegador avisou nesse tempo (os
        eventos ficam em self.eventos): um comando qualquer faz ler tudo o
        que chegou antes da resposta dele."""
        time.sleep(segundos)
        self.comando("Runtime.evaluate", expression="1")

    def antes_de_cada_pagina(self, codigo):
        """JavaScript que roda antes do da pagina, em toda pagina aberta
        (a mesma funcao do testes\\firefox_bidi.py, no Firefox)."""
        self.comando("Page.addScriptToEvaluateOnNewDocument", source=codigo)

    def abrir(self, url, largura=1366, altura=768, escala=1, espera=2.5, tema=None):
        """Abre a pagina numa tela de largura x altura (pontos CSS) com a
        escala do Windows ('escala' 2 = 200%: 1920x1080 a 200% e' uma tela
        4K). 'tema': "dark"/"light" para o prefers-color-scheme."""
        self.comando("Emulation.setDeviceMetricsOverride", width=largura, height=altura,
                     deviceScaleFactor=escala, mobile=False)
        if tema:
            self.comando("Emulation.setEmulatedMedia",
                         features=[{"name": "prefers-color-scheme", "value": tema}])
        self.comando("Page.navigate", url=url)
        time.sleep(espera)

    def avaliar(self, expressao):
        """Roda JavaScript na pagina (await permitido) e devolve o valor."""
        r = self.comando("Runtime.evaluate", expression=expressao, awaitPromise=True,
                         returnByValue=True)
        if r.get("exceptionDetails"):
            raise OSError("erro no JavaScript: %s" % r["exceptionDetails"].get("text"))
        return (r.get("result") or {}).get("value")

    def foto(self, caminho):
        r = self.comando("Page.captureScreenshot", format="png")
        with open(caminho, "wb") as f:
            f.write(base64.b64decode(r["data"]))
        return caminho


if __name__ == "__main__":
    numeros = [float(a) for a in sys.argv[1:] if a.replace(".", "", 1).isdigit()]
    saida = next((a for a in sys.argv[1:] if a.lower().endswith(".png")), "tela_arena.png")
    largura, altura, escala = (numeros + [1366, 768, 1][len(numeros):])[:3]
    with Navegador() as nav:
        nav.abrir("http://127.0.0.1:8777", int(largura), int(altura), escala)
        print(nav.avaliar("document.title"), "->", nav.foto(saida))
