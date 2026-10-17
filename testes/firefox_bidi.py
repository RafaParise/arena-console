# -*- coding: utf-8 -*-
r"""O Firefox sem janela, controlado pelo WebDriver BiDi (item 11, 17/10/2026).

O Edge e o Chrome os testes controlam pelo protocolo de depuracao do Chrome
(CDP: testes\tela_sem_janela.py). O Firefox nao tem mais o CDP (saiu na
versao 129); ele fala o WebDriver BiDi, o protocolo padronizado pelo W3C
(w3.org/TR/webdriver-bidi), pelo mesmo tipo de WebSocket -- reaproveitado de
tela_sem_janela._WebSocket, so com a biblioteca padrao do Python.

A classe NavegadorFirefox tem a mesma cara da tela_sem_janela.Navegador:
abrir, avaliar, foto, esperar, pids e antes_de_cada_pagina. Perfil sempre
temporario: o Firefox de quem usa o computador nao e' tocado.
"""
import base64
import json
import os
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import limpeza  # noqa: E402
from tela_sem_janela import _WebSocket, porta_livre  # noqa: E402

# Sem as telas de primeira vez, sem atualizacao e sem enviar nada a Mozilla.
PREFERENCIAS = {
    "browser.shell.checkDefaultBrowser": False,
    "browser.startup.homepage_override.mstone": "ignore",
    "browser.aboutwelcome.enabled": False,
    "datareporting.policy.dataSubmissionEnabled": False,
    "toolkit.telemetry.reportingpolicy.firstRun": False,
    "app.update.disabledForTesting": True,
    "browser.tabs.warnOnClose": False,
}


def _valor(remoto):
    """Um valor do BiDi (RemoteValue) -> o valor do Python."""
    tipo = (remoto or {}).get("type")
    if tipo in ("undefined", "null", None):
        return None
    if tipo in ("string", "boolean"):
        return remoto.get("value")
    if tipo == "number":
        valor = remoto.get("value")
        return float(valor) if isinstance(valor, str) else valor
    if tipo == "array":
        return [_valor(v) for v in remoto.get("value") or []]
    if tipo in ("object", "map"):
        return {(k if isinstance(k, str) else _valor(k)): _valor(v) for k, v in remoto.get("value") or []}
    return None


class NavegadorFirefox:
    """Firefox pelo WebDriver BiDi: sem janela (headless) ou, com janela=True,
    numa janela de verdade."""

    def __init__(self, executavel, tamanho=(1366, 768), janela=False):
        """janela=True: com janela de verdade (como o aluno ve), para medir
        a memoria e o processador da tela desenhada pela placa de video."""
        self.exe = executavel
        self.perfil = tempfile.mkdtemp(prefix="arena_firefox_")
        self.porta = porta_livre()
        self.tamanho = tamanho
        self.janela = janela
        self.proc = None
        self.ws = None
        self.n = 0
        self.contexto = None
        self.eventos = []

    def __enter__(self):
        with open(os.path.join(self.perfil, "user.js"), "w", encoding="utf-8") as arquivo:
            for chave, valor in PREFERENCIAS.items():
                arquivo.write("user_pref(%s, %s);\n" % (json.dumps(chave), json.dumps(valor)))
        sem_janela = [] if self.janela else ["--headless"]
        self.proc = subprocess.Popen([self.exe] + sem_janela + ["--remote-debugging-port=%d" % self.porta,
                                      "--profile", self.perfil, "--no-remote",
                                      "--window-size=%d,%d" % self.tamanho, "about:blank"],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(150):
            try:
                self.ws = _WebSocket("ws://127.0.0.1:%d/session" % self.porta)
                break
            except OSError:
                time.sleep(0.2)
        if not self.ws:
            self.__exit__(None, None, None)
            raise OSError("o Firefox sem janela nao respondeu")
        self.comando("session.new", capabilities={"alwaysMatch": {}})
        arvore = self.comando("browsingContext.getTree")
        self.contexto = arvore["contexts"][0]["context"]
        return self

    def __exit__(self, *_):
        if self.ws:
            try:
                self.comando("browser.close")
            except (OSError, ValueError):
                pass
            self.ws.fechar()
            self.ws = None
        if self.proc:
            try:
                self.proc.wait(15)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(10)
        limpeza.apagar_pasta(self.perfil, segundos=15)

    def comando(self, metodo, **parametros):
        self.n += 1
        self.ws.enviar(json.dumps({"id": self.n, "method": metodo, "params": parametros}))
        while True:
            mensagem = json.loads(self.ws.receber())
            if mensagem.get("id") == self.n:
                if mensagem.get("type") == "error":
                    raise OSError("%s: %s (%s)" % (metodo, mensagem.get("error"), mensagem.get("message")))
                return mensagem.get("result", {})
            if mensagem.get("type") == "event":
                self.eventos.append(mensagem)

    def antes_de_cada_pagina(self, codigo):
        """JavaScript que roda antes do da pagina (o CDP
        Page.addScriptToEvaluateOnNewDocument)."""
        self.comando("script.addPreloadScript", functionDeclaration="() => {%s}" % codigo)

    def abrir(self, url, largura=1366, altura=768, escala=1, espera=2.5, tema=None):
        self.comando("browsingContext.setViewport", context=self.contexto,
                     viewport={"width": largura, "height": altura}, devicePixelRatio=escala)
        self.comando("browsingContext.navigate", context=self.contexto, url=url, wait="complete")
        time.sleep(espera)

    def avaliar(self, expressao):
        """Roda JavaScript na pagina (await permitido) e devolve o valor."""
        r = self.comando("script.evaluate", expression=expressao, awaitPromise=True,
                         target={"context": self.contexto}, resultOwnership="none",
                         serializationOptions={"maxObjectDepth": 20})
        if r.get("type") == "exception":
            detalhe = r.get("exceptionDetails") or {}
            raise OSError("erro no JavaScript: %s" % (detalhe.get("text") or detalhe))
        return _valor(r.get("result"))

    def esperar(self, segundos):
        time.sleep(segundos)

    def foto(self, caminho):
        r = self.comando("browsingContext.captureScreenshot", context=self.contexto)
        with open(caminho, "wb") as arquivo:
            arquivo.write(base64.b64decode(r["data"]))
        return caminho

    def pids(self):
        """Os processos deste Firefox (os que usam o perfil deste teste)."""
        comando = ("Get-CimInstance Win32_Process -Filter \"Name = 'firefox.exe'\" | Where-Object "
                   "{ $_.CommandLine -like '*%s*' -or $_.ParentProcessId -eq %d } | "
                   "ForEach-Object { $_.ProcessId }" % (self.perfil, self.proc.pid if self.proc else 0))
        try:
            saida = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", comando],
                                   capture_output=True, text=True, timeout=30).stdout
        except (OSError, subprocess.TimeoutExpired):
            return []
        return sorted({int(p) for p in saida.split() if p.strip().isdigit()} | {self.proc.pid})


if __name__ == "__main__":
    import navegadores_de_teste
    programa, versao = navegadores_de_teste.firefox()
    with NavegadorFirefox(programa) as nav:
        nav.abrir("data:text/html,<title>ok</title><p id=x>ARENA</p>", espera=0.5)
        print("Firefox", versao, "titulo:", nav.avaliar("document.title"),
              "| texto:", nav.avaliar("document.getElementById('x').textContent"),
              "| objeto:", nav.avaliar("({a: 1, b: [1, 'dois', null]})"))
    sys.exit(0)
