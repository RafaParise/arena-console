# -*- coding: utf-8 -*-
r"""A "mao" e os "olhos" no celular Android, pelo adb (depuracao USB ligada).

Por que existe (25/10/2026): quase todo teste "manual" no celular era olhar a
tela e tocar nela. Com isto eu faco os dois: tiro a foto da tela (e leio a
imagem), listo o que esta escrito e onde, e toco, deslizo, aperto tecla,
escrevo, abro e fecho o app, olho o registro do sistema e a lista de
controles. Nenhuma instalacao no celular: so o que o proprio Android traz
(screencap, uiautomator, input, dumpsys, logcat).

Duas armadilhas ja conhecidas (docs do projeto e memoria):
  * `input keyevent` sai como um teclado "Virtual" (id -1) e toma o jogador 1
    no RetroArch. Para controle, use testes\controle_virtual_android.py.
  * Com mais de um aparelho no adb (celular + emulador), o adb recusa:
    "more than one device/emulator". Aqui o aparelho e' sempre escolhido
    (o fisico, ou o da variavel ANDROID_SERIAL, ou o emulador com --emulador).

Uso na linha de comando (cada um imprime o que fez):
    servidor\python\python.exe testes\celular_mao.py foto [nome]
    servidor\python\python.exe testes\celular_mao.py ver [filtro]          lista os textos da tela
    servidor\python\python.exe testes\celular_mao.py tocar X Y
    servidor\python\python.exe testes\celular_mao.py tocar_texto "Ajustes"
    servidor\python\python.exe testes\celular_mao.py deslizar X1 Y1 X2 Y2 [ms]
    servidor\python\python.exe testes\celular_mao.py tecla VOLTAR|INICIO|ENTER|<codigo>
    servidor\python\python.exe testes\celular_mao.py escrever "texto"
    servidor\python\python.exe testes\celular_mao.py abrir [pacote/atividade]
    servidor\python\python.exe testes\celular_mao.py fechar [pacote]
    servidor\python\python.exe testes\celular_mao.py cima                  o que esta na frente
    servidor\python\python.exe testes\celular_mao.py controles             os controles que o Android enxerga
    servidor\python\python.exe testes\celular_mao.py registro [filtro]     o fim do logcat
"""
import os
import re
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, os.path.join(RAIZ, "ferramentas"))
import preparar_android as sdk  # noqa: E402

ADB = os.path.join(sdk.SDK, "platform-tools", "adb.exe")
PACOTE = "io.github.rafaparise.arena"
TELA_DO_ARENA = PACOTE + "/io.github.rafaparise.arena.ArenaActivity"
FOTOS = os.path.join(tempfile.gettempdir(), "celular_mao_fotos")
TECLAS = {"VOLTAR": 4, "INICIO": 3, "ENTER": 66, "MENU": 82, "RECENTES": 187, "ESC": 111,
          "CIMA": 19, "BAIXO": 20, "ESQUERDA": 21, "DIREITA": 22, "TAB": 61}


def aparelhos():
    """[(serie, estado)] de tudo o que o adb enxerga."""
    saida = subprocess.run([ADB, "devices"], capture_output=True, timeout=30).stdout.decode("utf-8", "replace")
    return [tuple(linha.split()[:2]) for linha in saida.splitlines()[1:] if len(linha.split()) >= 2]


def escolher(emulador=False):
    """O numero de serie do aparelho de trabalho."""
    forcado = os.environ.get("ANDROID_SERIAL")
    if forcado:
        return forcado
    prontos = [serie for serie, estado in aparelhos() if estado == "device"]
    fisicos = [s for s in prontos if not s.startswith("emulator-")]
    virtuais = [s for s in prontos if s.startswith("emulator-")]
    escolhidos = virtuais if emulador else fisicos
    if not escolhidos:
        raise SystemExit("Nenhum %s pronto no adb (depuracao USB ligada?)." % ("emulador" if emulador else "celular"))
    return escolhidos[0]


class Celular:
    def __init__(self, serie=None, emulador=False):
        self.serie = serie or escolher(emulador)

    # ----- o adb em si -----------------------------------------------------
    def adb(self, *argumentos, segundos=60):
        return subprocess.run([ADB, "-s", self.serie] + [str(a) for a in argumentos],
                              capture_output=True, timeout=segundos).stdout

    def texto(self, *argumentos, segundos=60):
        return self.adb(*argumentos, segundos=segundos).decode("utf-8", "replace")

    def shell(self, comando, segundos=60):
        return self.texto("shell", comando, segundos=segundos)

    # ----- olhos -----------------------------------------------------------
    def foto(self, nome=None):
        """Tira a foto da tela e devolve o caminho do PNG (a imagem se le com a ferramenta Read)."""
        os.makedirs(FOTOS, exist_ok=True)
        dados = self.adb("exec-out", "screencap", "-p", segundos=60)
        caminho = os.path.join(FOTOS, "%s.png" % (nome or time.strftime("%H%M%S")))
        with open(caminho, "wb") as arquivo:
            arquivo.write(dados)
        return caminho

    def arvore(self, ocultos=False):
        """Tudo o que esta na tela: [{'texto','desc','id','classe','caixa':(x1,y1,x2,y2),'clicavel'}].
        O WebView entrega tambem o que esta fora da tela ou escondido, com caixa vazia ou fora do aparelho:
        isso fica de fora, a menos que 'ocultos' seja True."""
        largura, altura = self.tamanho()
        self.adb("shell", "uiautomator", "dump", "/sdcard/arena_tela_mao.xml", segundos=60)
        xml = self.adb("exec-out", "cat", "/sdcard/arena_tela_mao.xml")
        self.adb("shell", "rm", "-f", "/sdcard/arena_tela_mao.xml")
        nos = []
        try:
            raiz = ET.fromstring(xml)
        except ET.ParseError:
            return nos
        for no in raiz.iter("node"):
            achou = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", no.get("bounds", ""))
            if not achou:
                continue
            caixa = tuple(int(n) for n in achou.groups())
            # O Android responde o tamanho em pe (720x1600) mesmo com o aparelho deitado: vale o maior lado.
            if not ocultos and (caixa[2] <= caixa[0] or caixa[3] <= caixa[1]
                                or caixa[0] >= max(largura, altura) or caixa[1] >= max(largura, altura)):
                continue
            nos.append({"texto": no.get("text", ""), "desc": no.get("content-desc", ""),
                        "id": no.get("resource-id", ""), "classe": no.get("class", ""),
                        "caixa": caixa,
                        "clicavel": no.get("clickable") == "true", "ligado": no.get("checked") == "true"})
        return nos

    def achar(self, texto=None, desc=None, id=None, contem=True, rotulo=None):
        """Os nos da tela que casam (texto, descricao ou id; sem diferenciar maiusculas).
        'rotulo' casa o texto OU a descricao, numa leitura da tela so (cada leitura leva uns 3 s)."""
        achados = []
        for no in self.arvore():
            alvos = [(no["texto"], texto), (no["desc"], desc), (no["id"], id),
                     (no["texto"], rotulo), (no["desc"], rotulo)]
            for atual, procurado in alvos:
                if procurado is None:
                    continue
                if (procurado.lower() in atual.lower()) if contem else (procurado.lower() == atual.lower()):
                    achados.append(no)
                    break
        return achados

    def cima(self):
        """A atividade que esta na frente (pacote/atividade), ou ''."""
        for linha in self.texto("shell", "dumpsys", "activity", "activities").splitlines():
            if "topResumedActivity" in linha or "mResumedActivity" in linha:
                achou = re.search(r"\s([\w.]+/[\w.$]+)", linha)
                return achou.group(1) if achou else linha.strip()
        return ""

    def tamanho(self):
        """(largura, altura) da tela, como o Android responde (em pe, mesmo com o aparelho deitado)."""
        if not getattr(self, "_tamanho", None):
            achou = re.search(r"(\d+)x(\d+)", self.shell("wm size"))
            self._tamanho = (int(achou.group(1)), int(achou.group(2))) if achou else (0, 0)
        return self._tamanho

    # ----- maos ------------------------------------------------------------
    def tocar(self, x, y):
        self.adb("shell", "input", "tap", int(x), int(y))

    def tocar_texto(self, texto, esperar=5):
        """Toca no meio do primeiro item com esse texto (ou descricao). False se nao achou."""
        fim = time.monotonic() + esperar
        while True:
            for no in self.achar(rotulo=texto):
                x1, y1, x2, y2 = no["caixa"]
                self.tocar((x1 + x2) // 2, (y1 + y2) // 2)
                return True
            if time.monotonic() >= fim:
                return False
            time.sleep(0.8)

    def deslizar(self, x1, y1, x2, y2, ms=300):
        self.adb("shell", "input", "swipe", int(x1), int(y1), int(x2), int(y2), int(ms))

    def rolar_ate(self, texto, tentativas=12, x=None):
        """Rola a tela para baixo (o dedo sobe) ate o texto aparecer; devolve o no, ou None."""
        largura, altura = self.tamanho()
        largura, altura = max(largura, altura), min(largura, altura)      # deitado
        x = x or largura // 2
        for _ in range(tentativas):
            achados = self.achar(rotulo=texto)
            if achados:
                return achados[0]
            self.deslizar(x, int(altura * 0.8), x, int(altura * 0.3), 350)
            time.sleep(0.6)
        return None

    def tecla(self, codigo):
        codigo = TECLAS.get(str(codigo).upper(), codigo)
        self.adb("shell", "input", "keyevent", codigo)

    def escrever(self, texto):
        self.adb("shell", "input", "text", texto.replace(" ", "%s"))

    def abrir(self, atividade=TELA_DO_ARENA):
        return self.texto("shell", "am", "start", "-n", atividade)

    def fechar(self, pacote=PACOTE):
        self.adb("shell", "am", "force-stop", pacote)

    def acordar(self):
        """Acende a tela e tira a trava simples (sem senha)."""
        self.adb("shell", "input", "keyevent", 224)
        self.adb("shell", "wm", "dismiss-keyguard")

    # ----- controles e registro -------------------------------------------
    def controles(self):
        """Os dispositivos de entrada que o Android enxerga: [(id, nome, descritor)]."""
        achados = []
        atual = None
        for linha in self.texto("shell", "dumpsys", "input").splitlines():
            m = re.match(r"\s+(\d+): (.+)$", linha)
            if m and "Descriptor" not in linha and "Device " not in linha:
                atual = [int(m.group(1)), m.group(2).strip(), ""]
                achados.append(atual)
            elif atual and linha.strip().startswith("Descriptor:"):
                atual[2] = linha.split(":", 1)[1].strip()
                atual = None
        return [tuple(a) for a in achados if a[0] > 0]

    def registro(self, filtro="", linhas=80):
        saida = self.texto("logcat", "-d", "-t", str(linhas * 4), segundos=60).splitlines()
        if filtro:
            saida = [l for l in saida if filtro.lower() in l.lower()]
        return "\n".join(saida[-linhas:])


def main(argv):
    # A tela do ARENA tem simbolos (estrela, lua): o cano do Windows (cp1252) nao os aceita.
    for saida in (sys.stdout, sys.stderr):
        try:
            saida.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass
    if len(argv) < 2:
        print(__doc__)
        return 2
    verbo, resto = argv[1].lower(), argv[2:]
    celular = Celular(emulador="--emulador" in argv)
    resto = [r for r in resto if r != "--emulador"]
    if verbo == "foto":
        print(celular.foto(resto[0] if resto else None))
    elif verbo == "ver":
        filtro = resto[0].lower() if resto else ""
        for no in celular.arvore():
            rotulo = no["texto"] or no["desc"]
            if rotulo and filtro in rotulo.lower():
                print("%-6s %-60s %s %s" % ("[x]" if no["ligado"] else ("*" if no["clicavel"] else " "),
                                             rotulo[:60], no["caixa"], no["id"].split("/")[-1]))
    elif verbo == "tocar":
        celular.tocar(resto[0], resto[1])
    elif verbo == "tocar_texto":
        print("tocou" if celular.tocar_texto(" ".join(resto)) else "nao achou")
    elif verbo == "deslizar":
        celular.deslizar(*resto)
    elif verbo == "rolar_ate":
        no = celular.rolar_ate(" ".join(resto))
        print("achou em %s" % (no["caixa"],) if no else "nao achou")
    elif verbo == "tecla":
        celular.tecla(resto[0])
    elif verbo == "escrever":
        celular.escrever(" ".join(resto))
    elif verbo == "abrir":
        print(celular.abrir(resto[0] if resto else TELA_DO_ARENA))
    elif verbo == "fechar":
        celular.fechar(resto[0] if resto else PACOTE)
    elif verbo == "cima":
        print(celular.cima())
    elif verbo == "controles":
        for numero, nome, descritor in celular.controles():
            print("%3d  %-40s %s" % (numero, nome, descritor[:12]))
    elif verbo == "registro":
        print(celular.registro(resto[0] if resto else ""))
    else:
        print("verbo desconhecido: %s\n" % verbo + __doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
