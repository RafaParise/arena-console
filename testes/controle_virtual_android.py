# -*- coding: utf-8 -*-
r"""Controles virtuais no celular Android: o que uma pessoa faria com o controle na mao.

Por que existe (25/10/2026): os testes com os controles de verdade (os dois
GameSir T4 Nova Lite por Bluetooth) ficavam sempre para o Rafael, porque o
adb nao consegue escrever nos controles de verdade: o /dev/input/event* e'
barrado pelo SELinux (sendevent: Permission denied). Mas o usuario "shell"
do Android esta no grupo "uhid", e o Android traz a ferramenta `hid`, que
cria aparelhos HID virtuais pelo /dev/uhid (a mesma que o CTS usa). Um
controle virtual com o mesmo fabricante, produto, nome e botoes do T4 passa
pelo MESMO caminho do Android que o de verdade: o kernel (hid-input), o
InputReader, o Generic.kl e, la no fim, o RetroArch. So o radio Bluetooth fica
de fora.

Dois jeitos de usar:

  1. Como biblioteca, nos testes:

         with ControlesVirtuais(2) as controles:
             controles.apertar(1, "A")            # jogador 1 aperta o A
             controles.direcao(2, "direita")      # jogador 2 segura para a direita
             controles.soltar_tudo(2)

  2. Como servico, para eu mexer nos controles enquanto olho a tela:

         servidor\python\python.exe testes\controle_virtual_android.py servir --controles 2
         servidor\python\python.exe testes\controle_virtual_android.py enviar "apertar 1 A 150"

     O servico escuta so no 127.0.0.1 (nunca na rede) e fecha com "sair".

Os controles somem do celular quando o servico fecha (a ferramenta `hid` os
apaga ao terminar). Nada fica gravado no aparelho.
"""
import argparse
import json
import os
import socket
import subprocess
import sys
import threading
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, os.path.join(RAIZ, "ferramentas"))
import preparar_android as sdk  # noqa: E402

ADB = os.path.join(sdk.SDK, "platform-tools", "adb.exe")
PORTA_DO_SERVICO = 55601        # so no 127.0.0.1

# O T4 Nova Lite de verdade, como o Android o descreve (getevent -il, 25/10/2026):
# fabricante 0x3537 (GameSir), produto 0x1041, nome "GameSir-Nova Lite".
NOME = "GameSir-Nova Lite"
FABRICANTE = 0x3537
PRODUTO = 0x1041

# O descritor HID: um Game Pad com 16 botoes (BTN_GAMEPAD a 0x13f), o direcional
# (chapeu), os dois analogicos (X Y e Z Rz) e os dois gatilhos analogicos
# (Accelerator e Brake, que o Linux chama de ABS_GAS e ABS_BRAKE). E' o
# mesmo conjunto de eixos e botoes que o getevent mostra no T4 de verdade.
DESCRITOR = [
    0x05, 0x01, 0x09, 0x05, 0xA1, 0x01,                                     # Game Pad (aplicacao)
    0x05, 0x09, 0x19, 0x01, 0x29, 0x10,                                     # botoes 1 a 16
    0x15, 0x00, 0x25, 0x01, 0x75, 0x01, 0x95, 0x10, 0x81, 0x02,
    0x05, 0x01, 0x09, 0x39,                                                 # chapeu (o direcional)
    0x15, 0x00, 0x25, 0x07, 0x35, 0x00, 0x46, 0x3B, 0x01, 0x65, 0x14,
    0x75, 0x04, 0x95, 0x01, 0x81, 0x42,
    0x75, 0x04, 0x95, 0x01, 0x81, 0x03,                                     # 4 bits de enchimento
    0x05, 0x01, 0x09, 0x30, 0x09, 0x31, 0x09, 0x32, 0x09, 0x35,            # X Y Z Rz
    0x15, 0x00, 0x26, 0xFF, 0x00, 0x35, 0x00, 0x45, 0x00, 0x65, 0x00,
    0x75, 0x08, 0x95, 0x04, 0x81, 0x02,
    0x05, 0x02, 0x09, 0xC4, 0x09, 0xC5,                                     # gatilhos
    0x15, 0x00, 0x26, 0xFF, 0x00, 0x75, 0x08, 0x95, 0x02, 0x81, 0x02,
    0xC0,
]

# Posicao de cada botao no relatorio (o botao N do HID vira o codigo 0x12f + N do Linux).
BOTOES = {
    "A": 0, "B": 1, "C": 2, "X": 3, "Y": 4, "Z": 5,
    "L1": 6, "R1": 7, "L2": 8, "R2": 9,
    "SELECT": 10, "START": 11, "MODE": 12, "L3": 13, "R3": 14,
}
# O valor do chapeu: 0 cima, 1 cima-direita, 2 direita ... 7 cima-esquerda; 8 = solto.
DIRECOES = {
    "cima": 0, "cima-direita": 1, "direita": 2, "baixo-direita": 3,
    "baixo": 4, "baixo-esquerda": 5, "esquerda": 6, "cima-esquerda": 7,
    "centro": 8, "solto": 8,
}


# Um teclado de PC simples (o "boot keyboard" do HID): 8 bytes por relatorio (modificadores, 0 e ate 6 teclas).
# O RetroArch do ARENA usa o F10 duas vezes para sair do jogo e o F8 para tirar a foto do quadro; no celular, so
# um teclado de verdade (ou um virtual como este) faz o RetroArch ler a tecla (o "input keyevent" do adb nao).
DESCRITOR_DO_TECLADO = [
    0x05, 0x01, 0x09, 0x06, 0xA1, 0x01, 0x05, 0x07, 0x19, 0xE0, 0x29, 0xE7, 0x15, 0x00, 0x25, 0x01,
    0x75, 0x01, 0x95, 0x08, 0x81, 0x02, 0x95, 0x01, 0x75, 0x08, 0x81, 0x01, 0x95, 0x06, 0x75, 0x08,
    0x15, 0x00, 0x25, 0x65, 0x05, 0x07, 0x19, 0x00, 0x29, 0x65, 0x81, 0x00, 0xC0,
]
NOME_DO_TECLADO = "ARENA teclado de teste"
ID_DO_TECLADO = 100
# O codigo de uso de cada tecla no HID (pagina 7).
TECLAS = {"ENTER": 0x28, "ESC": 0x29, "TAB": 0x2B, "ESPACO": 0x2C, "DIREITA": 0x4F, "ESQUERDA": 0x50,
          "BAIXO": 0x51, "CIMA": 0x52}
TECLAS.update({"F%d" % n: 0x39 + n for n in range(1, 13)})                 # F1 = 0x3A ... F12 = 0x45
TECLAS.update({chr(ord("A") + n): 0x04 + n for n in range(26)})            # A = 0x04 ... Z = 0x1D
TECLAS.update({str((n + 1) % 10): 0x1E + n for n in range(10)})            # 1 = 0x1E ... 0 = 0x27


class EstadoDoControle:
    """O que o controle esta segurando agora (vira um relatorio de 9 bytes)."""

    def __init__(self):
        self.botoes = 0
        self.chapeu = 8
        self.x = self.y = self.z = self.rz = 128
        self.gas = self.freio = 0

    def relatorio(self):
        return [self.botoes & 0xFF, (self.botoes >> 8) & 0xFF, self.chapeu & 0x0F,
                self.x, self.y, self.z, self.rz, self.gas, self.freio]


def caminho_do_adb(serie=None):
    """O adb e o numero de serie do celular (o fisico, nunca o emulador)."""
    if serie:
        return ADB, serie
    saida = subprocess.run([ADB, "devices"], capture_output=True, timeout=30).stdout.decode("utf-8", "replace")
    fisicos = [linha.split()[0] for linha in saida.splitlines()[1:]
               if linha.strip().endswith("device") and not linha.startswith("emulator-")]
    if not fisicos:
        raise SystemExit("Nenhum celular com a depuracao ligada no adb.")
    return ADB, fisicos[0]


class ControlesVirtuais:
    """Abre `quantos` controles virtuais iguais ao T4 Nova Lite no celular."""

    def __init__(self, quantos=2, serie=None, nome=NOME, teclado=False):
        self.adb, self.serie = caminho_do_adb(serie)
        self.nome = nome
        self.com_teclado = teclado
        self.estados = {n: EstadoDoControle() for n in range(1, quantos + 1)}
        self.processo = None
        self.avisos = []
        self._trava = threading.Lock()

    # ----- ciclo de vida -------------------------------------------------
    def __enter__(self):
        self.abrir()
        return self

    def __exit__(self, *_):
        self.fechar()

    def abrir(self):
        self.processo = subprocess.Popen([self.adb, "-s", self.serie, "shell", "hid", "-"],
                                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        threading.Thread(target=self._ler_avisos, daemon=True).start()
        for numero in self.estados:
            self._enviar({"id": numero, "command": "register", "name": self.nome, "vid": FABRICANTE,
                          "pid": PRODUTO, "bus": "bluetooth", "descriptor": DESCRITOR})
            time.sleep(0.4)
        if self.com_teclado:
            self._enviar({"id": ID_DO_TECLADO, "command": "register", "name": NOME_DO_TECLADO, "vid": 0x1D6B,
                          "pid": 0x0104, "bus": "usb", "descriptor": DESCRITOR_DO_TECLADO})
            time.sleep(0.4)
        time.sleep(1.0)
        for numero in self.estados:
            self._mandar(numero)

    def teclar(self, nome, milissegundos=120):
        """Aperta uma tecla do teclado virtual (F10, ESC, ENTER, A, 1...) e solta."""
        if not self.com_teclado:
            raise ValueError("o teclado virtual nao foi pedido (teclado=True)")
        codigo = TECLAS[nome.upper()]
        self._enviar({"id": ID_DO_TECLADO, "command": "report", "report": [0, 0, codigo, 0, 0, 0, 0, 0]})
        time.sleep(milissegundos / 1000.0)
        self._enviar({"id": ID_DO_TECLADO, "command": "report", "report": [0] * 8})

    def _ler_avisos(self):
        for linha in self.processo.stdout:
            self.avisos.append(linha.decode("utf-8", "replace").rstrip())

    def fechar(self):
        if not self.processo:
            return
        try:
            for numero in self.estados:
                self.estados[numero] = EstadoDoControle()
                self._mandar(numero)
            time.sleep(0.2)
            self.processo.stdin.close()
        except OSError:
            pass
        try:
            self.processo.wait(8)
        except subprocess.TimeoutExpired:
            self.processo.kill()
        self.processo = None

    def _enviar(self, objeto):
        with self._trava:
            self.processo.stdin.write((json.dumps(objeto) + "\n").encode())
            self.processo.stdin.flush()

    def _mandar(self, numero):
        self._enviar({"id": numero, "command": "report", "report": self.estados[numero].relatorio()})

    # ----- o que uma pessoa faz ------------------------------------------
    def _estado(self, jogador):
        if jogador not in self.estados:
            raise ValueError("jogador %r nao existe (1 a %d)" % (jogador, len(self.estados)))
        return self.estados[jogador]

    def segurar(self, jogador, botao):
        estado = self._estado(jogador)
        estado.botoes |= 1 << BOTOES[botao.upper()]
        self._mandar(jogador)

    def soltar(self, jogador, botao=None):
        estado = self._estado(jogador)
        if botao is None:
            estado.botoes = 0
        else:
            estado.botoes &= ~(1 << BOTOES[botao.upper()])
        self._mandar(jogador)

    def apertar(self, jogador, botao, milissegundos=120):
        """Aperta, segura um pouco e solta: o toque de uma pessoa."""
        self.segurar(jogador, botao)
        time.sleep(milissegundos / 1000.0)
        self.soltar(jogador, botao)

    def direcao(self, jogador, nome):
        self._estado(jogador).chapeu = DIRECOES[nome.lower()]
        self._mandar(jogador)

    def analogico(self, jogador, lado, x, y):
        estado = self._estado(jogador)
        x, y = max(0, min(255, int(x))), max(0, min(255, int(y)))
        if lado.lower() in ("esq", "esquerdo", "l"):
            estado.x, estado.y = x, y
        else:
            estado.z, estado.rz = x, y
        self._mandar(jogador)

    def gatilho(self, jogador, lado, valor):
        estado = self._estado(jogador)
        valor = max(0, min(255, int(valor)))
        if lado.lower() in ("esq", "esquerdo", "l"):
            estado.freio = valor
        else:
            estado.gas = valor
        self._mandar(jogador)

    def soltar_tudo(self, jogador):
        self.estados[jogador] = EstadoDoControle()
        self._mandar(jogador)

    # ----- comandos em texto (o servico) ---------------------------------
    def comando(self, linha):
        partes = linha.strip().split()
        if not partes:
            return "ok"
        verbo, resto = partes[0].lower(), partes[1:]
        if verbo == "apertar":
            self.apertar(int(resto[0]), resto[1], int(resto[2]) if len(resto) > 2 else 120)
        elif verbo == "segurar":
            self.segurar(int(resto[0]), resto[1])
        elif verbo == "soltar":
            self.soltar(int(resto[0]), resto[1] if len(resto) > 1 else None)
        elif verbo == "direcao":
            self.direcao(int(resto[0]), resto[1])
        elif verbo == "analogico":
            self.analogico(int(resto[0]), resto[1], resto[2], resto[3])
        elif verbo == "gatilho":
            self.gatilho(int(resto[0]), resto[1], resto[2])
        elif verbo == "soltar_tudo":
            self.soltar_tudo(int(resto[0]))
        elif verbo == "tecla":
            self.teclar(resto[0], int(resto[1]) if len(resto) > 1 else 120)
        elif verbo == "esperar":
            time.sleep(float(resto[0]))
        else:
            raise ValueError("comando desconhecido: %s" % verbo)
        return "ok"


def servir(quantos, porta, teclado=False):
    """Deixa os controles abertos e atende comandos de texto no 127.0.0.1."""
    with ControlesVirtuais(quantos, teclado=teclado) as controles:
        servidor = socket.socket()
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor.bind(("127.0.0.1", porta))
        servidor.listen(4)
        print("pronto: %d controle(s) virtual(is) no celular; comandos em 127.0.0.1:%d" % (quantos, porta), flush=True)
        if controles.avisos:
            print("avisos do hid:", controles.avisos, flush=True)
        parar = False
        while not parar:
            conexao, _ = servidor.accept()
            with conexao:
                conexao.settimeout(10)
                dados = b""
                try:
                    while not dados.endswith(b"\n"):
                        pedaco = conexao.recv(4096)
                        if not pedaco:
                            break
                        dados += pedaco
                except OSError:
                    continue
                respostas = []
                for linha in dados.decode("utf-8", "replace").splitlines():
                    if linha.strip().lower() == "sair":
                        parar = True
                        respostas.append("ok")
                        break
                    try:
                        respostas.append(controles.comando(linha))
                    except (ValueError, KeyError, IndexError) as erro:
                        respostas.append("erro: %s" % erro)
                try:
                    conexao.sendall(("\n".join(respostas) + "\n").encode())
                except OSError:
                    pass
        servidor.close()
    print("controles virtuais fechados", flush=True)


def enviar(texto, porta=PORTA_DO_SERVICO):
    """Manda comandos (um por linha) ao servico e devolve a resposta."""
    with socket.create_connection(("127.0.0.1", porta), timeout=10) as conexao:
        conexao.sendall((texto.replace(";", "\n").strip() + "\n").encode())
        conexao.settimeout(60)
        return conexao.recv(65536).decode("utf-8", "replace")


def main():
    analisador = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = analisador.add_subparsers(dest="acao", required=True)
    s = sub.add_parser("servir", help="abre os controles e fica atendendo comandos")
    s.add_argument("--controles", type=int, default=2)
    s.add_argument("--teclado", action="store_true", help="liga tambem um teclado virtual (F10, F8, ESC...)")
    s.add_argument("--porta", type=int, default=PORTA_DO_SERVICO)
    e = sub.add_parser("enviar", help='manda comandos ao servico (separe por ";")')
    e.add_argument("texto")
    e.add_argument("--porta", type=int, default=PORTA_DO_SERVICO)
    args = analisador.parse_args()
    if args.acao == "servir":
        servir(args.controles, args.porta, args.teclado)
    else:
        print(enviar(args.texto, args.porta), end="")


if __name__ == "__main__":
    main()
