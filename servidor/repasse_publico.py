# -*- coding: utf-8 -*-
r"""Partida entre casas pelo retransmissor publico do RetroArch, sem lista publica (13/11/2026).

Por que: com CGNAT (a operadora divide um endereco de internet entre varios clientes; o ARENA confere em
servidor\internet_de_casa.py), nada de fora chega a casa -- nem o repasse da turma (servidor\repasse_proprio.py).
O RetroArch tem retransmissores publicos (os "tuneis" da libretro). Os dois lados LIGAM PARA FORA, entao funciona
mesmo com CGNAT dos dois lados.

Sem a lista publica: o jeito comum de achar a sessao no retransmissor e' a lista de salas da libretro, que e' aberta
a qualquer um, so por http, e mostra o endereco de internet de quem hospeda. Para alunos menores, nao. Entao:
  1. o RetroArch de quem hospeda fala com uma PONTE local do ARENA (127.0.0.1), que repassa tudo, byte a byte, ao
     retransmissor de Sao Paulo;
  2. a ponte le a resposta do retransmissor ao "RATS + 12 zeros" (o mesmo protocolo do repasse da turma: RATS + os
     12 bytes da sessao) e o ARENA mostra esses 12 bytes como um CODIGO de 20 letras e numeros;
  3. quem hospeda copia o codigo e manda ao colega (na aula, no grupo da turma); o ARENA do colega devolve os 12
     bytes ao RetroArch dele (--mitm-session) e liga direto no retransmissor.
O codigo nunca vai para lista nenhuma. 12 bytes aleatorios (96 bits): adivinhar uma sala e' impossivel na pratica.
O retransmissor ve os enderecos de quem joga (como qualquer servidor), e so.

So a biblioteca padrao. A ponte so escuta em 127.0.0.1 e so liga no retransmissor da lista abaixo.
"""
import base64
import socket
import threading

# lobby.libretro.com/tunnel?name=saopaulo (13/11/2026): o tunel de Sao Paulo, o mais perto das escolas de SP.
TUNEL = ("southamerica-east1.relay.retroarch.com", 55435)
PEDIDO_DE_SESSAO = b"RATS" + bytes(12)
CODIGO_LETRAS = 20

_ponte = {"atual": None}
_TRAVA = threading.Lock()


# ---------------------------------------------------------------------------
# O codigo da sala: os 12 bytes da sessao em letras e numeros (base32, sem 0/1/8/9 que confundem com O/I/B/g)
# ---------------------------------------------------------------------------
def codigo_da_sessao(sessao):
    """12 bytes -> 'ABCD-EFGH-IJKL-MNOP-QRST' (20 letras e numeros, de 4 em 4)."""
    letras = base64.b32encode(bytes(sessao)).decode("ascii").rstrip("=")
    return "-".join(letras[i:i + 4] for i in range(0, len(letras), 4))


def sessao_do_codigo(texto):
    """O codigo digitado (com ou sem tracos, maiusculas ou minusculas; 0 vira O e 1 vira I) -> 12 bytes, ou None."""
    limpo = "".join(c for c in str(texto or "").upper() if c.isalnum()).replace("0", "O").replace("1", "I")
    if len(limpo) != CODIGO_LETRAS:
        return None
    try:
        sessao = base64.b32decode(limpo + "====")
    except ValueError:          # o binascii.Error do b32decode e' um ValueError
        return None
    return sessao if len(sessao) == 12 and sessao != bytes(12) else None


def parece_codigo_publico(texto):
    return sessao_do_codigo(texto) is not None


def para_o_retroarch(sessao):
    """O --mitm-session do RetroArch: a sessao em base64 (o mesmo formato do repasse da turma)."""
    return base64.b64encode(bytes(sessao)).decode("ascii")


# ---------------------------------------------------------------------------
# A ponte local
# ---------------------------------------------------------------------------
class Ponte:
    """Escuta em 127.0.0.1 numa porta livre; cada ligacao do RetroArch vira uma ligacao com o tunel, e os bytes passam
    dos dois lados. Na primeira resposta do tunel a um pedido de sessao, guarda os 12 bytes."""

    def __init__(self, tunel=TUNEL):
        self.tunel = tunel
        self.sessao = None
        self.pronta = threading.Event()
        self.aberta = True
        self.escuta = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.escuta.bind(("127.0.0.1", 0))
        self.escuta.listen(8)
        self.porta = self.escuta.getsockname()[1]
        threading.Thread(target=self._aceitar, daemon=True).start()

    def _aceitar(self):
        while self.aberta:
            try:
                cliente, _endereco = self.escuta.accept()
            except OSError:
                break
            threading.Thread(target=self._ligar, args=(cliente,), daemon=True).start()

    def _ligar(self, cliente):
        try:
            remoto = socket.create_connection(self.tunel, timeout=15)
            remoto.settimeout(None)
        except OSError:
            cliente.close()
            return
        for lado in (cliente, remoto):
            lado.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)   # jogo: cada tecla sai na hora
        pediu_sessao = threading.Event()
        threading.Thread(target=self._passar, args=(cliente, remoto, pediu_sessao, True), daemon=True).start()
        self._passar(remoto, cliente, pediu_sessao, False)

    def _passar(self, de, para, pediu_sessao, do_retroarch):
        inicio = b""
        try:
            while True:
                dados = de.recv(65536)
                if not dados:
                    break
                if len(inicio) < 16:
                    inicio += dados[:16 - len(inicio)]
                    if len(inicio) == 16:
                        if do_retroarch and inicio == PEDIDO_DE_SESSAO:
                            pediu_sessao.set()
                        elif not do_retroarch and inicio[:4] == b"RATS" and pediu_sessao.wait(2) \
                                and inicio[4:] != bytes(12) and self.sessao is None:
                            self.sessao = inicio[4:]
                            self.pronta.set()
                para.sendall(dados)
        except OSError:
            pass
        finally:
            for lado in (de, para):
                try:
                    lado.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                lado.close()

    def esperar_codigo(self, segundos=12):
        """O codigo da sala quando o tunel responder, ou None."""
        return codigo_da_sessao(self.sessao) if self.pronta.wait(segundos) else None

    def fechar(self):
        self.aberta = False
        try:
            self.escuta.close()
        except OSError:
            pass


def abrir_ponte(tunel=TUNEL):
    """Fecha a ponte anterior (se houver) e abre uma nova. Devolve a Ponte."""
    with _TRAVA:
        if _ponte["atual"]:
            _ponte["atual"].fechar()
        _ponte["atual"] = Ponte(tunel)
        return _ponte["atual"]


def fechar_ponte():
    with _TRAVA:
        if _ponte["atual"]:
            _ponte["atual"].fechar()
            _ponte["atual"] = None


def ponte_atual():
    with _TRAVA:
        return _ponte["atual"]


def tunel_responde(tunel=TUNEL, espera=8):
    """O retransmissor publico responde a um pedido de sessao? (o teste do botao; abre e fecha uma sessao)."""
    try:
        with socket.create_connection(tunel, timeout=espera) as ligacao:
            ligacao.sendall(PEDIDO_DE_SESSAO)
            ligacao.settimeout(espera)
            resposta = b""
            while len(resposta) < 16:
                pedaco = ligacao.recv(16 - len(resposta))
                if not pedaco:
                    break
                resposta += pedaco
        return resposta[:4] == b"RATS" and len(resposta) == 16 and resposta[4:] != bytes(12)
    except OSError:
        return False
