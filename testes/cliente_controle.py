# -*- coding: utf-8 -*-
"""Um "celular de mentira" para os testes do controle remoto (servidor\\controle_remoto.py): faz o que a tela do
controle (launcher\\controle\\controle.js) faz, por um soquete comum. Nao e' um navegador: serve para provar o servidor
(o aperto de mao do WebSocket, o codigo, o estado dos botoes, o sinal que some) sem precisar de um aparelho."""
import base64
import os
import socket
import struct
import time

AQUI = os.path.dirname(os.path.abspath(__file__))


class RecusouAConexao(Exception):
    """O servidor respondeu outra coisa que nao '101 Switching Protocols' (guarda a linha de status)."""


class ClienteDeControle:
    def __init__(self, endereco="127.0.0.1", porta=8780, origem="auto", caminho="/ws", chave=None, segundos=5.0):
        self.s = socket.create_connection((endereco, porta), timeout=segundos)
        self.s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.buffer = bytearray()
        self.host = "%s:%d" % (endereco, porta)
        chave = chave or base64.b64encode(os.urandom(16)).decode()
        cabecas = ["GET %s HTTP/1.1" % caminho, "Host: %s" % self.host, "Upgrade: websocket", "Connection: Upgrade",
                   "Sec-WebSocket-Key: %s" % chave, "Sec-WebSocket-Version: 13"]
        if origem == "auto":
            origem = "http://%s" % self.host
        if origem:
            cabecas.append("Origin: %s" % origem)
        self.s.sendall(("\r\n".join(cabecas) + "\r\n\r\n").encode("ascii"))
        resposta = b""
        while b"\r\n\r\n" not in resposta:
            pedaco = self.s.recv(4096)
            if not pedaco:
                raise RecusouAConexao("o servidor fechou antes de responder")
            resposta += pedaco
        cabeca, _, sobra = resposta.partition(b"\r\n\r\n")
        self.status = cabeca.split(b"\r\n", 1)[0].decode("latin-1")
        self.cabecas_da_resposta = cabeca.decode("latin-1")
        self.buffer += sobra
        if " 101 " not in self.status:
            raise RecusouAConexao(self.status)

    # -- enviar (sempre mascarado, como o navegador) -----------------------------------------------
    def quadro(self, opcode, dados=b"", fim=True, reservado=0, mascarar=True):
        n = len(dados)
        cabeca = bytearray([(0x80 if fim else 0) | reservado | opcode])
        marca = 0x80 if mascarar else 0
        if n < 126:
            cabeca.append(marca | n)
        elif n < 65536:
            cabeca.append(marca | 126)
            cabeca += struct.pack(">H", n)
        else:
            cabeca.append(marca | 127)
            cabeca += struct.pack(">Q", n)
        if mascarar:
            mascara = os.urandom(4)
            cabeca += mascara
            dados = bytes(b ^ mascara[i & 3] for i, b in enumerate(dados))
        return bytes(cabeca) + dados

    def enviar_bruto(self, dados):
        self.s.sendall(dados)

    def enviar_texto(self, texto):
        self.s.sendall(self.quadro(0x1, texto.encode("utf-8")))

    def enviar_binario(self, dados):
        self.s.sendall(self.quadro(0x2, dados))

    def enviar_ping(self, dados=b""):
        self.s.sendall(self.quadro(0x9, dados))

    def fechar_com_educacao(self):
        try:
            self.s.sendall(self.quadro(0x8, struct.pack(">H", 1000)))
        except OSError:
            pass

    # -- receber -----------------------------------------------------------------------------------
    def _quadro_pronto(self):
        """(opcode, dados) se ha um quadro inteiro do servidor no buffer (o servidor nao mascara), senao None."""
        b = self.buffer
        if len(b) < 2:
            return None
        n, posicao = b[1] & 0x7F, 2
        if n == 126:
            if len(b) < 4:
                return None
            n, posicao = struct.unpack(">H", bytes(b[2:4]))[0], 4
        elif n == 127:
            if len(b) < 10:
                return None
            n, posicao = struct.unpack(">Q", bytes(b[2:10]))[0], 10
        if len(b) < posicao + n:
            return None
        opcode, dados = b[0] & 0x0F, bytes(b[posicao:posicao + n])
        del b[:posicao + n]
        return opcode, dados

    def receber(self, segundos=3.0):
        """(opcode, dados) do proximo quadro, ou None se nada chegou no prazo ou a conexao fechou."""
        fim = time.monotonic() + segundos
        while True:
            pronto = self._quadro_pronto()
            if pronto:
                return pronto
            restante = fim - time.monotonic()
            if restante <= 0:
                return None
            self.s.settimeout(restante)
            try:
                pedaco = self.s.recv(4096)
            except (socket.timeout, TimeoutError):
                return None
            except OSError:
                return None
            if not pedaco:
                return None
            self.buffer += pedaco

    def receber_ate(self, opcode, segundos=3.0):
        fim = time.monotonic() + segundos
        while time.monotonic() < fim:
            recebido = self.receber(max(0.05, fim - time.monotonic()))
            if recebido is None:
                return None
            if recebido[0] == opcode:
                return recebido
        return None

    def fechar(self):
        try:
            self.s.close()
        except OSError:
            pass


def estado(botoes=0, lx=0, ly=0, rx=0, ry=0):
    """Os 11 bytes do estado dos botoes (o mesmo que o controle.js manda)."""
    return struct.pack("<BHhhhh", 1, botoes, lx, ly, rx, ry)
