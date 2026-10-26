# -*- coding: utf-8 -*-
"""O celular como controle do computador, pelo Wi-Fi (Etapa 3 de docs\\PLANO-CELULAR.md).

Como funciona, em quatro passos:

  1. O professor liga "Celular como controle" nos Ajustes. So entao este modulo abre uma porta (8780) na rede local,
     com a tela do controle e um WebSocket. Desligado e' o padrao, e o ARENA sempre abre desligado.
  2. O aluno abre o endereco que a tela mostra (http://192.168.x.x:8780/) no navegador do celular e digita o codigo de
     6 numeros que aparece no computador.
  3. A tela do controle manda o estado dos botoes (11 bytes) a cada mudanca e a cada 250 ms (o "ainda estou aqui").
  4. Este modulo traduz o estado para o Network RetroPad do RetroArch: datagramas UDP de 20 bytes para o 127.0.0.1
     (so este computador), um por quadro de video. O RetroArch so escuta enquanto o jogo roda.

Por que "um datagrama por quadro": lido em input/input_driver.c do RetroArch 1.22.2, o RetroArch tira UM datagrama por
jogador a cada quadro (recvfrom uma vez em input_poll) e cada datagrama muda UM controle (um botao ou um eixo). Se o
celular mandasse tudo de uma vez, a fila encheria e o atraso cresceria. Por isso o EnviadorRetroPad guarda so o que
mudou, junta mudancas repetidas do mesmo controle e solta no maximo um datagrama por jogador a cada 1/60 s. Sem dado novo,
o RetroArch MANTEM o ultimo estado: se o celular some com um botao apertado, o botao ficaria preso. Por isso, sem sinal
por 1,5 s (ou ao fechar a conexao), tudo e' solto, e uma varredura manda o zero de cada controle.

Seguranca (docs\\PLANO-CELULAR.md, linha 7 da tabela):
  * desligado por padrao e so liga pelo clique do professor no computador (nunca pelo celular);
  * so aceita conexao de rede local (10.x, 172.16-31.x, 192.168.x, 169.254.x e o proprio computador);
  * codigo de 6 numeros, conferido com hmac.compare_digest NA MESMA TRAVA em que a tentativa e' contada (varias conexoes
    de uma vez nao passam do limite), bloqueio do endereco depois de 5 erros em 1 minuto, no maximo 10 tentativas a cada
    10 s de TODOS os enderecos juntos (trocar de endereco a cada tentativa nao ajuda) e codigo novo depois de 20 erros;
  * a pagina so e' do controle: nenhuma rota da API do ARENA fica na porta aberta;
  * so responde a quem chamou o computador por um endereco DELE (lista fechada de IP:porta): um site que fez o nome dele
    apontar para o computador (DNS rebinding) chega com outro Host e e' recusado; a Origin tambem tem que ser a desse Host;
  * o professor escolhe quais jogadores (1 a 4) o celular pode ser, e so esses abrem no RetroArch;
  * limite de quadros por segundo e de tamanho; no maximo 4 celulares ao mesmo tempo.

O que nao da: os emuladores de fora (PCSX2, Dolphin, RPCS3, Xenia) nao leem o Network RetroPad. E o RetroArch escuta o
UDP em TODAS as placas de rede enquanto o jogo roda (nao da para pedir so o 127.0.0.1): com o firewall do Windows
fechado para a rede publica isso nao chega a ninguem, mas na rede da escola vale o aviso na tela.

O que isso quer dizer, sem enfeite (revisao de seguranca de 25/10/2026): enquanto um jogo do RetroArch esta aberto com
o controle remoto ligado, QUALQUER computador da mesma rede que ache a porta UDP (sorteada entre 50000 e 59000 so para
nao esbarrar em outra; varrer 9 mil portas e' rapido) pode mandar botoes para os jogadores liberados. Nao ha senha: o
Network RetroPad e' do RetroArch e nao tem. O estrago e' o de uma brincadeira (apertar botao no jogo do colega), e e' o
mesmo da porta do Jogar Junto. O que o ARENA faz: desligado de fabrica, so abre os jogadores liberados pelo professor e
que o jogo tem, so enquanto o jogo roda. O conserto de verdade (escutar so o 127.0.0.1) exige mexer no RetroArch, que o
ARENA leva sem alteracao no Windows; fica anotado em docs\\PLANO-CELULAR.md.
"""
import base64
import hashlib
import hmac
import ipaddress
import json
import os
import random
import secrets
import socket
import socketserver
import struct
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PASTA_SERVIDOR = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(PASTA_SERVIDOR)
PASTA_DA_PAGINA = os.path.join(RAIZ, "launcher", "controle")

PORTA_DA_PAGINA = 8780
PORTA_BASE_PADRAO = 55400                 # o padrao do RetroArch (network_remote_base_port)
JOGADORES = 8                               # o Network RetroPad do RetroArch vai ate 16; 8 cobre os consoles com 2 multitaps
TAMANHO_MAXIMO_DO_QUADRO = 4096           # nada do controle passa de 200 bytes
QUADROS_POR_SEGUNDO_MAXIMO = 150          # o celular manda uns 60 por segundo
SEGUNDOS_SEM_SINAL = 1.5                  # sem estado novo: solta tudo
SEGUNDOS_PARA_DESISTIR = 30.0             # sem nada: fecha a conexao
SEGUNDOS_PARA_O_CODIGO = 8.0              # tempo para o celular dizer "oi" depois de abrir o WebSocket
INTERVALO_DO_ENVIO = 1.0 / 60.0           # um quadro de video
RESSINCRONIZAR_A_CADA = 12                # quadros: com a fila vazia, repete o estado de um controle (conserta perda)
ZONA_DO_ANALOGICO = 256                   # mudanca menor que isso (de 32767) nao vira datagrama
DIGITOS_DO_CODIGO = 6                     # 4 caiam em 10 mil tentativas; 6, em 1 milhao (revisao de seguranca de 25/10/2026)
TENTATIVAS_POR_JANELA = 10                # codigos ERRADOS de TODOS os enderecos juntos...
JANELA_GLOBAL_S = 10.0                    # ...a cada 10 s: passou disso, quem ja errou espera (quem ainda nao errou entra)
TENTATIVAS_LIMITE_DURO = 30               # e com 30 erros em 10 s (de varios enderecos novos) espera todo mundo, ate os que nao
                                          # erraram: no maximo uns 3 palpites por segundo, venha de quantos enderecos vier
MEMORIA_DE_ACERTO_S = 600.0               # ...menos o celular que entrou com o codigo certo ha menos de 10 min (o Wi-Fi piscou)
JOGADORES_LIBERADOS_PADRAO = (2, 3, 4)    # o 1 costuma ser o teclado ou o controle de verdade
ERROS_ANTES_DO_BLOQUEIO = 5
JANELA_DOS_ERROS_S = 60.0
BLOQUEIO_S = 120.0
ERROS_ANTES_DE_TROCAR_O_CODIGO = 20
CONEXOES_MAXIMAS = 24                     # abertas ao mesmo tempo (com ou sem codigo certo)

GUID_DO_WEBSOCKET = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"       # fixo, da RFC 6455
TIPO_ESTADO = 1                           # primeiro byte do quadro binario "estado dos botoes"
FORMATO_DO_ESTADO = struct.Struct("<BHhhhh")       # tipo, botoes, lx, ly, rx, ry = 11 bytes
FORMATO_DO_PACOTE = struct.Struct("<iiiiHxx")      # struct remote_message do RetroArch: 20 bytes
DISPOSITIVO_JOYPAD = 1                    # RETRO_DEVICE_JOYPAD
DISPOSITIVO_ANALOGICO = 5                 # RETRO_DEVICE_ANALOG
CONTROLES = 16 + 4                        # 16 botoes (ids 0 a 15 do RetroPad) e 4 eixos (lx, ly, rx, ry)

OP_TEXTO, OP_BINARIO, OP_FECHAR, OP_PING, OP_PONG = 0x1, 0x2, 0x8, 0x9, 0xA


# ---------------------------------------------------------------------------
# WebSocket (RFC 6455), so o que o controle usa: texto e binario inteiros, ping, fechar
# ---------------------------------------------------------------------------

class ErroDeProtocolo(Exception):
    """O outro lado quebrou o protocolo: 'codigo' e' o codigo de fechamento do WebSocket (RFC 6455, 7.4)."""

    def __init__(self, codigo, motivo):
        super().__init__(motivo)
        self.codigo = codigo
        self.motivo = motivo


def chave_de_aceite(chave):
    """O Sec-WebSocket-Accept que responde a um Sec-WebSocket-Key (RFC 6455, 4.2.2)."""
    return base64.b64encode(hashlib.sha1((chave + GUID_DO_WEBSOCKET).encode("ascii")).digest()).decode("ascii")


def chave_valida(chave):
    """O Sec-WebSocket-Key e' um valor de 16 bytes em base64 (24 letras)."""
    try:
        return len(chave) == 24 and len(base64.b64decode(chave, validate=True)) == 16
    except (ValueError, TypeError):
        return False


def montar_quadro(opcode, dados=b""):
    """Um quadro do servidor para o cliente (sem mascara, inteiro)."""
    n = len(dados)
    if n < 126:
        cabeca = bytes([0x80 | opcode, n])
    elif n < 65536:
        cabeca = bytes([0x80 | opcode, 126]) + struct.pack(">H", n)
    else:
        cabeca = bytes([0x80 | opcode, 127]) + struct.pack(">Q", n)
    return cabeca + dados


def extrair_quadro(buffer, maximo=TAMANHO_MAXIMO_DO_QUADRO):
    """Tira do comeco de 'buffer' (bytearray) um quadro COMPLETO do cliente: (opcode, dados). Sem o quadro inteiro
    ainda, devolve None e nao mexe no buffer (o resto chega no proximo recv). Quebra de protocolo: ErroDeProtocolo."""
    if len(buffer) < 2:
        return None
    b0, b1 = buffer[0], buffer[1]
    fim, reservado, opcode = b0 & 0x80, b0 & 0x70, b0 & 0x0F
    mascarado, tamanho, posicao = b1 & 0x80, b1 & 0x7F, 2
    if reservado:
        raise ErroDeProtocolo(1002, "bits reservados ligados")
    if not mascarado:
        raise ErroDeProtocolo(1002, "o cliente tem que mascarar os quadros")
    if tamanho == 126:
        if len(buffer) < 4:
            return None
        tamanho, posicao = struct.unpack(">H", bytes(buffer[2:4]))[0], 4
    elif tamanho == 127:
        if len(buffer) < 10:
            return None
        tamanho, posicao = struct.unpack(">Q", bytes(buffer[2:10]))[0], 10
    if opcode >= 0x8 and (tamanho > 125 or not fim):
        raise ErroDeProtocolo(1002, "quadro de controle invalido")
    if not fim or opcode == 0x0:
        raise ErroDeProtocolo(1003, "quadro em pedacos nao e' aceito")
    if opcode not in (OP_TEXTO, OP_BINARIO, OP_FECHAR, OP_PING, OP_PONG):
        raise ErroDeProtocolo(1003, "tipo de quadro desconhecido")
    if tamanho > maximo:
        raise ErroDeProtocolo(1009, "quadro grande demais")
    if len(buffer) < posicao + 4 + tamanho:
        return None
    mascara = bytes(buffer[posicao:posicao + 4])
    dados = bytearray(buffer[posicao + 4:posicao + 4 + tamanho])
    for i in range(tamanho):
        dados[i] ^= mascara[i & 3]
    del buffer[:posicao + 4 + tamanho]
    return opcode, bytes(dados)


# ---------------------------------------------------------------------------
# O estado dos botoes e o Network RetroPad
# ---------------------------------------------------------------------------

def codificar_estado(botoes, eixos):
    """Os 11 bytes que a tela do controle manda: tipo, 16 botoes (bit i = id i do RetroPad), lx, ly, rx, ry (int16)."""
    lx, ly, rx, ry = (max(-32768, min(32767, int(e))) for e in eixos)
    return FORMATO_DO_ESTADO.pack(TIPO_ESTADO, botoes & 0xFFFF, lx, ly, rx, ry)


def decodificar_estado(dados):
    """(botoes, [lx, ly, rx, ry]) de um quadro binario de estado, ou None se nao for um."""
    if len(dados) != FORMATO_DO_ESTADO.size or dados[0] != TIPO_ESTADO:
        return None
    _, botoes, lx, ly, rx, ry = FORMATO_DO_ESTADO.unpack(dados)
    return botoes, [lx, ly, rx, ry]


def pacote_do_retropad(porta, dispositivo, indice, identificador, valor):
    """O struct remote_message do RetroArch (20 bytes, na ordem da maquina): porta, dispositivo, indice, id, estado."""
    return FORMATO_DO_PACOTE.pack(porta, dispositivo, indice, identificador, valor & 0xFFFF)


def _controle_para_pacote(porta, chave, valor):
    """chave = ("b", id do botao) ou ("a", 0 a 3: lx ly rx ry)."""
    tipo, numero = chave
    if tipo == "b":
        return pacote_do_retropad(porta, DISPOSITIVO_JOYPAD, 0, numero, 1 if valor else 0)
    return pacote_do_retropad(porta, DISPOSITIVO_ANALOGICO, numero // 2, numero % 2, valor)


class _FilaDoJogador:
    """O que falta o RetroArch saber de um jogador (um controle por datagrama, um datagrama por quadro)."""

    def __init__(self):
        self.desejado_botoes = 0
        self.desejado_eixos = [0, 0, 0, 0]
        self.enviado_botoes = 0
        self.enviado_eixos = [0, 0, 0, 0]
        self.pendentes = []            # chaves ("b", i) / ("a", k) cujo desejado e' diferente do enviado, em ordem
        self.ativo = False             # ha celular ligado neste jogador (liga a ressincronizacao)
        self.zerando = 0               # varreduras de zero que faltam (depois de um sinal perdido ou de um fechamento)
        self.varredura = 0             # qual controle a ressincronizacao manda agora
        self.quadros = 0

    def _valor_desejado(self, chave):
        tipo, numero = chave
        if tipo == "b":
            return (self.desejado_botoes >> numero) & 1
        return self.desejado_eixos[numero]

    def _valor_enviado(self, chave):
        tipo, numero = chave
        if tipo == "b":
            return (self.enviado_botoes >> numero) & 1
        return self.enviado_eixos[numero]

    def _guardar_como_enviado(self, chave, valor):
        tipo, numero = chave
        if tipo == "b":
            self.enviado_botoes = (self.enviado_botoes | (1 << numero)) if valor else (self.enviado_botoes & ~(1 << numero))
        else:
            self.enviado_eixos[numero] = valor

    def _refazer_pendentes(self):
        todos = [("b", i) for i in range(16)] + [("a", k) for k in range(4)]
        diferentes = {c for c in todos if self._valor_desejado(c) != self._valor_enviado(c)}
        # quem ja esperava continua na frente (ordem de chegada); quem acabou de mudar entra no fim
        self.pendentes = [c for c in self.pendentes if c in diferentes] + [c for c in todos if c in diferentes and c not in self.pendentes]

    def definir(self, botoes, eixos):
        self.desejado_botoes = botoes & 0xFFFF
        for k in range(4):
            valor = max(-32768, min(32767, int(eixos[k])))
            # o dedo treme: mudanca pequena nao gasta datagrama (mas voltar ao zero, sim)
            if valor != 0 and abs(valor - self.enviado_eixos[k]) < ZONA_DO_ANALOGICO:
                valor = self.enviado_eixos[k]
            self.desejado_eixos[k] = valor
        self._refazer_pendentes()

    def zerar(self):
        self.desejado_botoes = 0
        self.desejado_eixos = [0, 0, 0, 0]
        self.zerando = 1
        self.varredura = 0
        self._refazer_pendentes()

    def ocupada(self):
        return bool(self.pendentes or self.ativo or self.zerando)

    def proximo(self):
        """O proximo controle a mandar neste quadro (chave, valor), ou None."""
        if self.pendentes:
            chave = self.pendentes.pop(0)
            valor = self._valor_desejado(chave)
            self._guardar_como_enviado(chave, valor)
            return chave, valor
        if self.zerando or self.ativo:
            self.quadros += 1
            if self.zerando or self.quadros % RESSINCRONIZAR_A_CADA == 0:
                numero = self.varredura
                self.varredura = (self.varredura + 1) % CONTROLES
                if self.zerando and self.varredura == 0:
                    self.zerando -= 1
                chave = ("b", numero) if numero < 16 else ("a", numero - 16)
                valor = self._valor_desejado(chave)
                self._guardar_como_enviado(chave, valor)
                return chave, valor
        return None


class EnviadorRetroPad:
    """Manda o estado dos botoes para o Network RetroPad do RetroArch (UDP no 127.0.0.1), um datagrama por jogador
    por quadro. 'enviar(dados, porta)' e' injetavel (o teste troca por uma lista)."""

    def __init__(self, enviar=None, porta_base=PORTA_BASE_PADRAO):
        self.porta_base = porta_base
        self._enviar = enviar or self._enviar_udp
        self._soquete = None
        self._filas = {n: _FilaDoJogador() for n in range(1, JOGADORES + 1)}
        self._condicao = threading.Condition()
        self._parar = False
        self._thread = None

    def _enviar_udp(self, dados, porta):
        if self._soquete is None:
            self._soquete = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self._soquete.sendto(dados, ("127.0.0.1", porta))
        except OSError:
            pass            # sem ninguem escutando (o jogo nao abriu): o datagrama se perde, e ta tudo bem

    def porta_do(self, jogador):
        return self.porta_base + jogador - 1

    # -- o que a tela do controle pede ------------------------------------------------------------
    def ativar(self, jogador, ativo=True):
        with self._condicao:
            self._filas[jogador].ativo = ativo
            self._condicao.notify_all()

    def definir(self, jogador, botoes, eixos):
        with self._condicao:
            self._filas[jogador].definir(botoes, eixos)
            self._condicao.notify_all()

    def zerar(self, jogador):
        with self._condicao:
            self._filas[jogador].zerar()
            self._condicao.notify_all()

    # -- o relogio --------------------------------------------------------------------------------
    def passo(self):
        """Um quadro de video: no maximo um datagrama por jogador. Devolve [(jogador, dados)] do que mandou."""
        mandados = []
        with self._condicao:
            for jogador, fila in self._filas.items():
                escolhido = fila.proximo()
                if escolhido:
                    mandados.append((jogador, _controle_para_pacote(self.porta_do(jogador), *escolhido)))
        for jogador, dados in mandados:
            self._enviar(dados, self.porta_do(jogador))
        return mandados

    def ocupado(self):
        return any(fila.ocupada() for fila in self._filas.values())

    def iniciar(self):
        if self._thread and self._thread.is_alive():
            return
        self._parar = False
        self._thread = threading.Thread(target=self._laco, name="controle-remoto-udp", daemon=True)
        self._thread.start()

    def parar(self):
        with self._condicao:
            self._parar = True
            self._condicao.notify_all()
        if self._thread:
            self._thread.join(2.0)

    def _laco(self):
        proximo = time.monotonic()
        while True:
            with self._condicao:
                while not self._parar and not self.ocupado():
                    self._condicao.wait(1.0)       # parado, nao gasta processador
                    proximo = time.monotonic()
                if self._parar:
                    return
            self.passo()
            proximo += INTERVALO_DO_ENVIO
            folga = proximo - time.monotonic()
            if folga > 0:
                time.sleep(folga)
            else:
                proximo = time.monotonic()           # atrasou: nao tenta recuperar quadros


# ---------------------------------------------------------------------------
# Regras de quem pode entrar
# ---------------------------------------------------------------------------

def rede_privada(endereco):
    """O endereco e' deste computador ou da rede local (nunca da internet)?"""
    try:
        ip = ipaddress.ip_address(endereco.split("%")[0])
    except ValueError:
        return False
    if ip.version == 6 and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    return ip.is_loopback or ip.is_private or ip.is_link_local


def origem_confiavel(origem, host, permitidos):
    """O pedido veio da tela DESTE servidor? 'permitidos' e' a lista fechada dos enderecos que o computador tem de
    verdade (IP:porta). Comparar a Origin so com o Host nao basta: num "DNS rebinding" um site qualquer faz o nome dele
    apontar para o IP do computador, e a Origin e o Host chegam IGUAIS, com o nome do site. Um nome fora da lista nao
    entra. Sem Origin nao e' navegador (so o codigo vale)."""
    host = (host or "").strip().lower()
    if host not in permitidos:
        return False
    if not origem:
        return True
    try:
        partes = urllib.parse.urlsplit(origem)
    except ValueError:
        return False
    return partes.scheme in ("http", "https") and partes.netloc.lower() == host


def codigo_novo():
    return "".join(str(secrets.randbelow(10)) for _ in range(DIGITOS_DO_CODIGO))


def porta_base_livre(tentativas=30):
    """Sorteia uma porta-base (ela e as 3 seguintes) que ninguem usa: o RetroArch desiste de TODO o controle remoto se
    uma so das portas ja estiver ocupada. Cai no padrao do RetroArch se nao achar."""
    for _ in range(tentativas):
        base = random.randint(50000, 59000)
        soquetes = []
        try:
            for n in range(JOGADORES):
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                soquetes.append(s)
                s.bind(("0.0.0.0", base + n))
            return base
        except OSError:
            continue
        finally:
            for s in soquetes:
                s.close()
    return PORTA_BASE_PADRAO


def opcoes_do_retroarch(porta_base, jogadores=None):
    """As chaves do arquivo da partida (--appendconfig) que ligam o Network RetroPad dos 'jogadores' (so esses: cada um
    e' uma porta UDP aberta em todas as placas de rede enquanto o jogo roda, sem senha: e' do proprio RetroArch).
    O RetroArch so abre os soquetes dos jogadores abaixo de input_max_users: quem junta isto com o resto sobe o
    input_max_users para pelo menos o maior destes."""
    jogadores = sorted(set(jogadores if jogadores is not None else range(1, JOGADORES + 1)))
    chaves = {"network_remote_enable": "true", "network_remote_base_port": str(int(porta_base))}
    for n in range(1, JOGADORES + 1):
        chaves["network_remote_enable_user_p%d" % n] = "true" if n in jogadores else "false"
    return chaves


def _enderecos_do_computador():
    """Os enderecos IPv4 deste computador na rede local (o primeiro e' o da rota principal)."""
    achados = []
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.254.254.254", 9))            # nao manda nada: so pergunta qual placa sairia
            achados.append(s.getsockname()[0])
    except OSError:
        pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            if info[4][0] not in achados:
                achados.append(info[4][0])
    except OSError:
        pass
    return [a for a in achados if not a.startswith("127.") and rede_privada(a)]


# ---------------------------------------------------------------------------
# O servico
# ---------------------------------------------------------------------------

_TIPOS = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8"}
_ROTAS_DA_PAGINA = {"/": "index.html", "/index.html": "index.html", "/controle.js": "controle.js", "/controle.css": "controle.css"}
_CABECALHOS_DE_SEGURANCA = (
    ("Cache-Control", "no-store"),
    ("X-Content-Type-Options", "nosniff"),
    ("Referrer-Policy", "no-referrer"),
    ("Content-Security-Policy", "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
                                "connect-src 'self' ws: wss:; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"),
)


class _ServidorDoControle(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True
    request_queue_size = 16

    def __init__(self, endereco, controle):
        self.controle = controle
        self._abertas = 0
        self._trava_abertas = threading.Lock()
        super().__init__(endereco, _Manipulador)

    def server_bind(self):
        # O HTTPServer de fabrica pergunta o nome do computador por DNS (getfqdn) ao ligar: no Windows leva mais de 1 s.
        socketserver.TCPServer.server_bind(self)
        self.server_name, self.server_port = self.server_address[:2]

    def verify_request(self, request, client_address):
        # so a rede local; e um teto de conexoes abertas (uma pessoa mal intencionada nao esgota as linhas de execucao)
        if not rede_privada(client_address[0]):
            return False
        with self._trava_abertas:
            if self._abertas >= CONEXOES_MAXIMAS:
                return False
            self._abertas += 1
        return True

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            with self._trava_abertas:
                self._abertas = max(0, self._abertas - 1)

    def handle_error(self, request, client_address):
        pass                    # cliente que some no meio nao enche a janela preta de erro


class _Manipulador(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    timeout = 10

    def log_message(self, formato, *args):
        pass

    def _responder(self, codigo, corpo=b"", tipo="text/plain; charset=utf-8"):
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        for nome, valor in _CABECALHOS_DE_SEGURANCA:
            self.send_header(nome, valor)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(corpo)

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        caminho = urllib.parse.urlparse(self.path).path
        controle = self.server.controle
        # So responde a quem chamou o computador por um endereco DELE (o IP da rede ou 127.0.0.1): um nome de site que
        # passou a apontar para ca (DNS rebinding) traz outro Host e nao entra.
        if not controle.host_confiavel(self.headers.get("Host")):
            return self._responder(403, "Pedido recusado: use o endereço que o ARENA mostra no computador.".encode("utf-8"))
        if caminho == "/ws":
            return self._abrir_websocket()
        if caminho == "/jogadores":
            # quais jogadores o professor liberou para o celular (sem segredo nenhum): a tela do celular so oferece estes
            corpo = json.dumps({"jogadores": controle.jogadores(), "digitos": DIGITOS_DO_CODIGO}).encode("utf-8")
            return self._responder(200, corpo, "application/json; charset=utf-8")
        arquivo = _ROTAS_DA_PAGINA.get(caminho)
        if not arquivo:
            return self._responder(404, "Não achei esta página. O controle está em /".encode("utf-8"))
        try:
            with open(os.path.join(controle.pasta_da_pagina, arquivo), "rb") as f:
                corpo = f.read()
        except OSError:
            return self._responder(404, "A tela do controle não está nesta cópia do ARENA.".encode("utf-8"))
        self._responder(200, corpo, _TIPOS.get(os.path.splitext(arquivo)[1], "application/octet-stream"))

    def do_POST(self):
        self._responder(405, b"")

    do_PUT = do_DELETE = do_PATCH = do_OPTIONS = do_POST

    def _abrir_websocket(self):
        controle = self.server.controle
        cab = self.headers
        chave = cab.get("Sec-WebSocket-Key", "")
        if (cab.get("Upgrade", "").lower() != "websocket" or "upgrade" not in cab.get("Connection", "").lower()
                or cab.get("Sec-WebSocket-Version") != "13" or not chave_valida(chave)):
            return self._responder(400, b"Isto e' um WebSocket.")
        if not origem_confiavel(cab.get("Origin"), cab.get("Host"), controle.hosts_confiaveis()):
            return self._responder(403, "Pedido recusado: ele não veio da tela do controle.".encode("utf-8"))
        self.send_response(101, "Switching Protocols")
        self.send_header("Upgrade", "websocket")
        self.send_header("Connection", "Upgrade")
        self.send_header("Sec-WebSocket-Accept", chave_de_aceite(chave))
        self.end_headers()
        self.wfile.flush()
        self.close_connection = True
        controle.atender(self.connection, self.client_address[0])


class ControleRemoto:
    """Liga e desliga o controle remoto e atende os celulares."""

    def __init__(self, enviador=None, enderecos=None, pasta_da_pagina=PASTA_DA_PAGINA, porta=PORTA_DA_PAGINA):
        self.enviador = enviador or EnviadorRetroPad()
        self._enderecos = enderecos or _enderecos_do_computador
        self.pasta_da_pagina = pasta_da_pagina
        self.porta_pedida = porta
        self.porta = None
        self.codigo = None
        self.ligado = False
        self._servidor = None
        self._thread = None
        self._trava = threading.Lock()
        self._clientes = {}            # jogador -> {"ip", "desde", "apelido", "soquete", "visto"}
        self._erros = {}               # ip -> [instantes dos erros de codigo]
        self._bloqueios = {}           # ip -> instante em que o bloqueio acaba
        self._erros_no_total = 0
        self._falhas = []              # instantes dos ultimos codigos errados, de qualquer endereco
        self._acertos = {}             # ip -> instante em que entrou com o codigo certo (passa pelo teto duro)
        self._trocas_do_codigo = 0     # quantas vezes o codigo mudou sozinho (alguem errou demais): o professor ve
        self._liberados = set(JOGADORES_LIBERADOS_PADRAO)      # os jogadores que o celular pode ser (o professor muda)
        self._hosts_extras = set()     # outros nomes que valem como Host (o endereco do tunel, quando houver)

    # -- liga e desliga ---------------------------------------------------------------------------
    def ligar(self):
        with self._trava:
            if self.ligado:
                return self._estado_sem_trava()
            servidor = None
            for porta in [self.porta_pedida] + list(range(self.porta_pedida + 1, self.porta_pedida + 10)):
                try:
                    servidor = _ServidorDoControle(("0.0.0.0", porta), self)
                    self.porta = servidor.server_address[1]      # (com porta 0, o sistema escolhe: so os testes pedem)
                    break
                except OSError:
                    continue
            if servidor is None:
                raise OSError("Não consegui abrir uma porta para o controle remoto (as portas 8780 a 8789 estão ocupadas). Feche o programa que as usa e tente de novo.")
            self._servidor = servidor
            self._thread = threading.Thread(target=servidor.serve_forever, name="controle-remoto-http", daemon=True,
                                            kwargs={"poll_interval": 0.1})
            self._thread.start()
            self.enviador.iniciar()
            self.codigo = codigo_novo()
            self._erros.clear()
            self._bloqueios.clear()
            self._erros_no_total = 0
            self._falhas = []
            self._acertos = {}
            self._trocas_do_codigo = 0
            self.ligado = True
            return self._estado_sem_trava()

    def desligar(self):
        with self._trava:
            if not self.ligado:
                return
            self.ligado = False
            servidor, self._servidor = self._servidor, None
            clientes = list(self._clientes.items())
            self._clientes.clear()
        for jogador, dados in clientes:
            self.enviador.zerar(jogador)
            self.enviador.ativar(jogador, False)
            try:
                dados["soquete"].close()
            except OSError:
                pass
        if servidor:
            servidor.shutdown()
            servidor.server_close()
        self.codigo = None

    def estado(self):
        with self._trava:
            return self._estado_sem_trava()

    def _estado_sem_trava(self):
        if not self.ligado:
            return {"ligado": False, "porta_da_pagina": self.porta_pedida, "jogadores_liberados": sorted(self._liberados)}
        enderecos = ["http://%s:%d/" % (ip, self.porta) for ip in self._enderecos()]
        return {"ligado": True, "codigo": self.codigo, "porta_da_pagina": self.porta, "enderecos": enderecos,
                "jogadores_liberados": sorted(self._liberados), "trocas_do_codigo": self._trocas_do_codigo,
                "conectados": [{"jogador": n, "ip": d["ip"], "apelido": d["apelido"], "ha_s": round(time.monotonic() - d["desde"]),
                                "rtt_ms": d.get("rtt_ms"), "pelo_cabo": d["ip"].startswith("127.")}
                               for n, d in sorted(self._clientes.items())]}

    # -- que jogadores o celular pode ser ---------------------------------------------------------
    def jogadores(self):
        with self._trava:
            return sorted(self._liberados)

    def liberar_jogadores(self, numeros):
        """O professor escolhe (de 1 a 8) quais jogadores o celular pode ser. Vale no PROXIMO jogo que abrir: cada jogador
        liberado e' uma porta UDP aberta no RetroArch enquanto o jogo roda (sem senha: e' do proprio RetroArch), entao
        so se abre o que se vai usar."""
        novos = {int(n) for n in numeros if str(n).isdigit() and 1 <= int(n) <= JOGADORES}
        with self._trava:
            self._liberados = novos
        return sorted(novos)

    def preparar_partida(self, jogadores_do_jogo=JOGADORES):
        """Chamado quando um jogo vai abrir: sorteia a porta-base do Network RetroPad e devolve as chaves do RetroArch,
        so dos jogadores liberados que o jogo tem (um jogo de 2 abre so o jogador 2 de um celular). Sem o controle remoto
        ligado, ou sem nenhum jogador a abrir, devolve {} e o jogo abre como sempre."""
        if not self.ligado:
            return {}
        ativos = [n for n in self.jogadores() if n <= max(2, int(jogadores_do_jogo or JOGADORES))]
        if not ativos:
            return {}
        self.enviador.porta_base = porta_base_livre()
        return opcoes_do_retroarch(self.enviador.porta_base, ativos)

    # -- que nomes valem como Host ----------------------------------------------------------------
    def hosts_confiaveis(self):
        """Os 'IP:porta' deste computador (o da rede, o do proprio computador, o nome dele) e os nomes extras (o tunel)."""
        nomes = {"127.0.0.1", "localhost", "[::1]", socket.gethostname().lower()}
        nomes.update(self._enderecos())
        nomes.add(socket.gethostname().lower() + ".local")
        porta = self.porta
        permitidos = {"%s:%d" % (n.lower(), porta) for n in nomes if porta}
        permitidos.update(h.lower() for h in self._hosts_extras)
        return permitidos

    def host_confiavel(self, host):
        return (host or "").strip().lower() in self.hosts_confiaveis()

    # -- quem pode entrar -------------------------------------------------------------------------
    def _bloqueado(self, ip, agora):
        fim = self._bloqueios.get(ip)
        if fim and agora < fim:
            return True
        self._bloqueios.pop(ip, None)
        return False

    def _anotar_erro(self, ip, agora):
        """Conta o erro (chamar com a trava na mao)."""
        recentes = [t for t in self._erros.get(ip, []) if agora - t < JANELA_DOS_ERROS_S] + [agora]
        self._erros[ip] = recentes
        if len(recentes) >= ERROS_ANTES_DO_BLOQUEIO:
            self._bloqueios[ip] = agora + BLOQUEIO_S
        self._erros_no_total += 1
        if self._erros_no_total >= ERROS_ANTES_DE_TROCAR_O_CODIGO:
            self.codigo = codigo_novo()          # alguem esta tentando todos: o codigo que ele tem nao vale mais
            self._erros_no_total = 0
            self._trocas_do_codigo += 1
        return max(0, ERROS_ANTES_DO_BLOQUEIO - len(recentes))

    def _ja_errou(self, ip, agora):
        return any(agora - t < JANELA_DOS_ERROS_S for t in self._erros.get(ip, ()))

    def conferir_o_codigo(self, ip, codigo, agora=None):
        """(ok, motivo, restam). Tudo na mesma trava: conferir e anotar o erro nao se separam, mesmo com 60 conexoes ao
        mesmo tempo. O bloqueio vale para o endereco inteiro (com o codigo certo ou errado).

        Os limites de todos os enderecos juntos contam so os ERROS, em duas faixas (duas revisoes de seguranca de
        25/10/2026 puxaram cada uma para um lado):
          - TENTATIVAS_POR_JANELA: so quem ja errou espera. Quem despeja erros nao tranca a porta de todos (contando
            tambem os acertos, dois enderecos com 5 erros cada trancavam o celular do professor);
          - TENTATIVAS_LIMITE_DURO: espera todo mundo, ate quem nao errou, MENOS o endereco que entrou com o codigo
            certo ha pouco (MEMORIA_DE_ACERTO_S). E' o teto de palpites por segundo de quem usa muitos enderecos (o
            IPv6 deixa criar quantos quiser). RISCO QUE FICA, de proposito: um celular NOVO, ou que nao entrou nos
            ultimos 10 min, espera ate 10 s durante uma rajada de 30 erros (para fazer isso, quem ataca precisa de
            6 enderecos ou mais, cada um bloqueado por 2 min depois de 5 erros), e o professor ve o aviso. A saida
            de verdade para esse resto seria o professor aprovar cada celular; nao se fez para nao pesar na aula.
        Alem dos limites, o codigo troca a cada ERROS_ANTES_DE_TROCAR_O_CODIGO erros, venha de onde vier: cada codigo
        sofre no maximo uns 20 palpites, de 1 milhao de possibilidades."""
        agora = time.monotonic() if agora is None else agora
        with self._trava:
            if self._bloqueado(ip, agora):
                return False, "bloqueado", 0
            self._falhas = [t for t in self._falhas if agora - t < JANELA_GLOBAL_S]
            ultimo_acerto = self._acertos.get(ip)
            conhecido = ultimo_acerto is not None and agora - ultimo_acerto < MEMORIA_DE_ACERTO_S
            if (len(self._falhas) >= TENTATIVAS_LIMITE_DURO and not conhecido) or (
                    len(self._falhas) >= TENTATIVAS_POR_JANELA and self._ja_errou(ip, agora)):
                return False, "muitas", 0
            certo = self.codigo
            if (certo and isinstance(codigo, str)
                    and hmac.compare_digest(codigo.encode("utf-8"), certo.encode("utf-8"))):
                self._acertos = {a: t for a, t in self._acertos.items() if agora - t < MEMORIA_DE_ACERTO_S}
                self._acertos[ip] = agora
                return True, "", ERROS_ANTES_DO_BLOQUEIO
            self._falhas.append(agora)
            return False, "codigo", self._anotar_erro(ip, agora)

    # -- a conversa com um celular ----------------------------------------------------------------
    def atender(self, soquete, ip):
        """Roda na linha de execucao do pedido, ate o celular sair. O WebSocket ja foi aceito."""
        jogador = None
        try:
            soquete.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except OSError:
            pass
        buffer = bytearray()
        try:
            jogador = self._receber_o_oi(soquete, ip, buffer)
            if jogador is None:
                return
            self._laco_do_jogador(soquete, jogador, buffer)
        except ErroDeProtocolo as erro:
            self._fechar(soquete, erro.codigo, erro.motivo)
        except (OSError, TimeoutError):
            pass
        finally:
            if jogador is not None:
                self._soltar_o_jogador(jogador, soquete)
            try:
                soquete.close()
            except OSError:
                pass

    def _enviar_texto(self, soquete, objeto):
        soquete.sendall(montar_quadro(OP_TEXTO, json.dumps(objeto, ensure_ascii=False).encode("utf-8")))

    def _fechar(self, soquete, codigo=1000, motivo=""):
        try:
            soquete.sendall(montar_quadro(OP_FECHAR, struct.pack(">H", codigo) + motivo.encode("utf-8")[:100]))
        except OSError:
            pass

    def _receber_o_oi(self, soquete, ip, buffer):
        """A primeira mensagem tem que ser {"t":"oi","codigo":"1234","jogador":2,"apelido":"..."} em ate 8 segundos."""
        fim = time.monotonic() + SEGUNDOS_PARA_O_CODIGO
        soquete.settimeout(1.0)
        quadro = None
        while quadro is None:
            quadro = extrair_quadro(buffer)
            if quadro:
                break
            if time.monotonic() > fim:
                self._fechar(soquete, 1008, "sem o codigo")
                return None
            try:
                pedaco = soquete.recv(4096)
            except socket.timeout:
                continue
            if not pedaco:
                return None
            buffer += pedaco
        opcode, dados = quadro
        if opcode != OP_TEXTO:
            raise ErroDeProtocolo(1003, "a primeira mensagem tem que ser texto")
        try:
            oi = json.loads(dados.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            raise ErroDeProtocolo(1007, "mensagem ilegivel") from None
        if not isinstance(oi, dict) or oi.get("t") != "oi":
            raise ErroDeProtocolo(1008, "faltou o oi")
        ok, motivo, restam = self.conferir_o_codigo(ip, str(oi.get("codigo", "")))
        if not ok:
            self._enviar_texto(soquete, {"t": "erro", "motivo": motivo, "restam": restam})
            self._fechar(soquete, 1008, motivo)
            return None
        try:
            jogador = int(oi.get("jogador", 0))
        except (TypeError, ValueError):
            jogador = 0
        if not 1 <= jogador <= JOGADORES or jogador not in self.jogadores():
            self._enviar_texto(soquete, {"t": "erro", "motivo": "jogador", "jogadores": self.jogadores()})
            self._fechar(soquete, 1008, "jogador")
            return None
        apelido = str(oi.get("apelido", ""))[:20]
        with self._trava:
            atual = self._clientes.get(jogador)
            if atual and atual["ip"] != ip:
                ocupado = True
            else:
                ocupado = False
                if atual:       # o mesmo aparelho voltando (o Wi-Fi piscou): o ultimo que chega vence
                    try:
                        atual["soquete"].close()
                    except OSError:
                        pass
                self._clientes[jogador] = {"ip": ip, "desde": time.monotonic(), "apelido": apelido, "soquete": soquete,
                                           "visto": time.monotonic()}
        if ocupado:
            self._enviar_texto(soquete, {"t": "erro", "motivo": "ocupado"})
            self._fechar(soquete, 1008, "ocupado")
            return None
        self.enviador.ativar(jogador, True)
        self._enviar_texto(soquete, {"t": "ok", "jogador": jogador})
        return jogador

    def _laco_do_jogador(self, soquete, jogador, buffer):
        soquete.settimeout(0.5)
        ultimo_estado = ultimo_dado = time.monotonic()
        sem_sinal = False
        fichas, ficha_em = float(QUADROS_POR_SEGUNDO_MAXIMO), time.monotonic()
        while self.ligado:
            try:
                while True:
                    quadro = extrair_quadro(buffer)
                    if quadro is None:
                        break
                    agora = time.monotonic()
                    ultimo_dado = agora
                    opcode, dados = quadro
                    if opcode == OP_FECHAR:
                        self._fechar(soquete, 1000, "tchau")
                        return
                    if opcode == OP_PING:
                        soquete.sendall(montar_quadro(OP_PONG, dados))
                    elif opcode == OP_BINARIO:
                        # limite de quadros por segundo: o que passa do limite e' jogado fora (o proximo estado vale mais)
                        fichas = min(float(QUADROS_POR_SEGUNDO_MAXIMO), fichas + (agora - ficha_em) * QUADROS_POR_SEGUNDO_MAXIMO)
                        ficha_em = agora
                        if fichas < 1.0:
                            continue
                        fichas -= 1.0
                        estado = decodificar_estado(dados)
                        if estado is None:
                            raise ErroDeProtocolo(1003, "estado invalido")
                        self.enviador.definir(jogador, *estado)
                        ultimo_estado = agora
                        sem_sinal = False
                    elif opcode == OP_TEXTO:
                        try:
                            mensagem = json.loads(dados.decode("utf-8"))
                        except (ValueError, UnicodeDecodeError):
                            raise ErroDeProtocolo(1007, "mensagem ilegivel") from None
                        tipo = mensagem.get("t") if isinstance(mensagem, dict) else None
                        if tipo == "tchau":
                            self._fechar(soquete, 1000, "tchau")
                            return
                        if tipo == "p":
                            # "ping" da tela do celular: ela mede sozinha a ida e volta (a latencia que importa)
                            self._enviar_texto(soquete, {"t": "q", "n": mensagem.get("n")})
                        elif tipo == "rtt":
                            self._anotar_rtt(jogador, soquete, mensagem.get("ms"))
                pedaco = soquete.recv(4096)
                if not pedaco:
                    return
                buffer += pedaco
            except socket.timeout:
                agora = time.monotonic()
                if not sem_sinal and agora - ultimo_estado > SEGUNDOS_SEM_SINAL:
                    self.enviador.zerar(jogador)             # a tela do celular parou (apagou, trocou de app): solta tudo
                    sem_sinal = True
                    try:
                        self._enviar_texto(soquete, {"t": "sem_sinal"})
                    except OSError:
                        return
                if agora - ultimo_dado > SEGUNDOS_PARA_DESISTIR:
                    self._fechar(soquete, 1001, "parado")
                    return

    def _anotar_rtt(self, jogador, soquete, ms):
        """A ida e volta, em milissegundos, que a tela do celular mediu: aparece na lista de celulares do computador."""
        try:
            ms = float(ms)
        except (TypeError, ValueError):
            return
        if not 0 <= ms < 10000:
            return
        with self._trava:
            dados = self._clientes.get(jogador)
            if dados is not None and dados["soquete"] is soquete:
                dados["rtt_ms"] = round(ms)

    def _soltar_o_jogador(self, jogador, soquete):
        with self._trava:
            atual = self._clientes.get(jogador)
            dono = atual is not None and atual["soquete"] is soquete
            if dono:
                del self._clientes[jogador]
        if dono:
            self.enviador.zerar(jogador)          # solta tudo e manda o zero de cada controle
            self.enviador.ativar(jogador, False)
