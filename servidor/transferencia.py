# -*- coding: utf-8 -*-
"""Transferência P2P de jogos via Wi-Fi local.

Funciona como servidor HTTP temporário para compartilhar arquivos de jogos
entre computadores na mesma rede, similar ao snapdrop.net.
"""

import hashlib
import os
import socket
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler


class TransferHandler(SimpleHTTPRequestHandler):
    """Handler para transferência de arquivos de jogos."""

    protocol_version = "HTTP/1.1"

    def log_message(self, format, *args):
        pass  # Silencioso para não poluir logs

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()


class ServidorTransferencia:
    """Gerencia o servidor temporário de transferência."""

    def __init__(self, porta=8080):
        self.porta = porta
        self.servidor = None
        self.thread = None
        self.ativo = False
        self.arquivos_compartilhados = {}
        self.jogos_compartilhados = {}

    def set_jogos(self, jogos):
        """Define os jogos a serem compartilhados via P2P."""
        self.jogos_compartilhados = jogos

    def adicionar_jogo(self, jogo_id, jogo_info):
        """Adiciona um jogo à lista de compartilhamento."""
        self.jogos_compartilhados[jogo_id] = jogo_info

    def iniciar(self, jogos_compartilhados):
        """Inicia o servidor na porta especificada."""
        self.arquivos_compartilhados = jogos_compartilhados

        class Handler(TransferHandler):
            transferencia = self

        try:
            self.servidor = HTTPServer(("", self.porta), Handler)
            self.ativo = True
            self.thread = threading.Thread(target=self.servidor.serve_forever, daemon=True)
            self.thread.start()
            return True, f"http://{self._obter_ip_local()}:{self.porta}"
        except OSError as e:
            if e.errno == 98:  # Porta em uso
                return False, "Porta já em uso"
            return False, str(e)

    def parar(self):
        """Para o servidor."""
        if self.servidor:
            self.servidor.shutdown()
            self.ativo = False

    def _obter_ip_local(self):
        """Obtém o IP local para passar ao amigo."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"


def verificar_conexao_wi_fi():
    """Verifica se há conexão de rede local disponível."""
    try:
        # Tenta conectar a um IP de rede local
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1)
        s.connect(("192.168.1.1", 1))
        ip = s.getsockname()[0]
        s.close()
        return True, ip
    except:
        return False, None


def obter_ip_para_amigo():
    """Obtém o melhor IP para passar ao amigo."""
    # Primeiro tenta IP de rede local
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("192.168.1.1", 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        pass

    # Fallback para IP calculado
    hostname = socket.gethostname()
    try:
        return socket.gethostbyname(hostname)
    except:
        return "127.0.0.1"