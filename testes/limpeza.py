# -*- coding: utf-8 -*-
r"""Apagar de verdade as pastas temporarias dos testes.

Achado de 01/10/2026: 136 pastas arena_* (2,9 GB) esquecidas no Temp do
Windows deste computador. Duas causas, as duas silenciosas por causa do
shutil.rmtree(..., ignore_errors=True):
  1. pasta copiada com o atributo "somente leitura" -- o RetroArch cria
     saves\.netplay assim, e toda copia do ARENA leva junto: o rmtree
     apaga os arquivos e desiste da pasta;
  2. programa que acabou de fechar (Edge, RetroArch) ainda segurando
     arquivo por alguns segundos.

Uso dentro de um teste:   limpeza.apagar_pasta(pasta)
Sozinho (apaga as arena_* do Temp com mais de 1 hora, de teste que caiu
no meio):                  servidor\python\python.exe testes\limpeza.py
"""
import glob
import os
import shutil
import stat
import sys
import tempfile
import time


def apagar_pasta(caminho, segundos=10):
    """Apaga a pasta inteira: tira o "somente leitura" e tenta de novo por
    ate `segundos` se algum arquivo ainda estiver preso. True se sumiu."""
    def tirar_trava(funcao, alvo, _erro):
        try:
            os.chmod(alvo, stat.S_IWRITE)
            funcao(alvo)
        except OSError:
            pass
    fim = time.monotonic() + segundos
    while os.path.exists(caminho):
        shutil.rmtree(caminho, onexc=tirar_trava)
        if not os.path.exists(caminho) or time.monotonic() > fim:
            break
        time.sleep(0.5)
    return not os.path.exists(caminho)


def tamanho(pasta):
    total = 0
    for atual, _sub, arquivos in os.walk(pasta):
        for nome in arquivos:
            try:
                total += os.path.getsize(os.path.join(atual, nome))
            except OSError:
                pass
    return total


def pastas_de_teste(mais_velhas_que_s=0.0):
    """As pastas arena_* do Temp (as que os testes criam com mkdtemp)."""
    agora = time.time()
    achadas = []
    for caminho in glob.glob(os.path.join(tempfile.gettempdir(), "arena_*")):
        try:
            if os.path.isdir(caminho) and agora - os.path.getmtime(caminho) >= mais_velhas_que_s:
                achadas.append(caminho)
        except OSError:
            pass
    return achadas


def limpar_temp(mais_velhas_que_s=3600.0):
    """Apaga as pastas de teste do Temp. Devolve (apagadas, bytes, presas)."""
    apagadas, liberado, presas = 0, 0, []
    for caminho in pastas_de_teste(mais_velhas_que_s):
        peso = tamanho(caminho)
        if apagar_pasta(caminho, segundos=3):
            apagadas += 1
            liberado += peso
        else:
            presas.append(caminho)
    return apagadas, liberado, presas


if __name__ == "__main__":
    apagadas, liberado, presas = limpar_temp(3600.0 if "--tudo" not in sys.argv else 0.0)
    print("Pastas de teste apagadas do Temp: %d (%.1f MB)." % (apagadas, liberado / 1024 ** 2))
    for caminho in presas:
        print("  ainda presa (algum programa aberto?): %s" % caminho)
    sys.exit(0 if not presas else 1)
