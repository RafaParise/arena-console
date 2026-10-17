# -*- coding: utf-8 -*-
r"""
ARENA - baixar da internet, do mesmo jeito no Windows e no Linux.

No Windows, o ARENA baixa pelo curl.exe que vem com o proprio Windows (desde
o 10): o mesmo de sempre, com o proxy e os certificados do sistema. No Linux
(item 13 do plano de 15/10/2026), o curl nem sempre existe (o Ubuntu de
desktop nao traz); entao vale o curl, se houver, e se nao, o proprio Python
(urllib, com os certificados do sistema). As duas formas fazem a mesma
coisa: seguem os redirecionamentos, desistem no tempo dado e tratam o erro
do site como falha (o --fail do curl).

rodar() devolve o MESMO numero de saida do curl nos dois casos, para quem
chama decidir a frase da tela do mesmo jeito: 0 = chegou; 22 = o site
respondeu erro (404, 500...); 6 = o nome do site nao foi achado (sem
internet ou sem DNS); 7 = nao conectou; 28 = o tempo acabou; 35 = falhou o
HTTPS; 56 = a conexao caiu no meio.
"""
import os
import shutil
import socket
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request

AGENTE = "ARENA/1.0"


def curl():
    """O curl deste sistema, ou None (no Linux sem curl)."""
    if sys.platform.startswith("win"):
        return "curl.exe"
    return shutil.which("curl")


def _pelo_python(url, segundos, destino, agente):
    """O mesmo que o curl faria, pelo urllib. (codigo do curl, bytes)."""
    limite = time.monotonic() + segundos
    pedido = urllib.request.Request(url, headers={"User-Agent": agente})
    temporario = destino + ".parcial" if destino else None
    try:
        with urllib.request.urlopen(pedido, timeout=max(1.0, segundos)) as resposta:
            partes = []
            saida = open(temporario, "wb") if temporario else None
            try:
                while True:
                    if time.monotonic() > limite:
                        return 28, b""
                    bloco = resposta.read(1 << 16)
                    if not bloco:
                        break
                    if saida:
                        saida.write(bloco)
                    else:
                        partes.append(bloco)
            finally:
                if saida:
                    saida.close()
        if temporario:
            os.replace(temporario, destino)
        return 0, b"".join(partes)
    except urllib.error.HTTPError:
        return 22, b""
    except urllib.error.URLError as falha:
        motivo = falha.reason
        if isinstance(motivo, socket.gaierror):
            return 6, b""
        if isinstance(motivo, (socket.timeout, TimeoutError)):
            return 28, b""
        if isinstance(motivo, ssl.SSLError):
            return 35, b""
        return 7, b""
    except (socket.timeout, TimeoutError):
        return 28, b""
    except ssl.SSLError:
        return 35, b""
    except (ConnectionError, OSError, ValueError):
        return 56, b""
    finally:
        if temporario and os.path.exists(temporario):
            try:
                os.remove(temporario)
            except OSError:
                pass


def rodar(url, segundos, destino=None, agente=AGENTE):
    """Baixa 'url'. Com 'destino', grava no arquivo e devolve (codigo, b"");
    sem, devolve (codigo, os bytes). 'codigo' e' o numero de saida do curl
    (ver o topo). OSError so se nem o curl nem o Python puderem tentar."""
    programa = curl()
    if not programa:
        return _pelo_python(url, segundos, destino, agente)
    comando = [programa, "--fail", "--silent", "--show-error", "--location",
               "--max-time", str(segundos), "-A", agente]
    if destino:
        comando += ["-o", destino]
    try:
        resultado = subprocess.run(comando + [url], capture_output=True)
    except subprocess.SubprocessError as falha:
        raise OSError(str(falha))
    return resultado.returncode, (b"" if destino else resultado.stdout)
