# -*- coding: utf-8 -*-
r"""Quanto o servidor do ARENA gasta PARADO -- e quando ele assenta.

Motivo (30/09/2026): o COLETAR.bat mediu o servidor "parado" a 8,4% de um
nucleo no Celeron da escola, contra 0,01% no i5. O medidor comeca a contar
10 s depois dos dados da tela prontos; se o navegador demora a abrir (o
Celeron e' lento), a tela ainda esta pedindo catalogo e capas dentro da
janela -- e isso seria custo de ABRIR, nao de ficar parado.

Esta ferramenta sobe o ARENA (como o ARENA.bat) e mede o processador do
servidor em fatias de 5 s, do comeco ao fim, para ver a curva: quanto custa
a abertura, quando assenta, e quanto gasta depois de assentado.

So o processo do servidor (Python) entra na conta: o navegador e os
programas que o servidor abre sao processos separados.

Uso:
    servidor\python\python.exe ferramentas\medir_parado.py [segundos] [--sem-tela]
        segundos    quanto tempo medir (padrao 120)
        --sem-tela  nao abre a janela do navegador: mede o servidor sozinho
                    (a tela pode ser aberta a mao, em http://127.0.0.1:8777)
"""
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import medir_arena  # noqa: E402  (Processo, caminhos)

FATIA = 5.0          # segundos por amostra
ASSENTADO = 1.0      # % de um nucleo: abaixo disto, a fatia conta como "parado"


def subir(sem_tela):
    if sem_tela:
        # O mesmo principal() do ARENA, so trocando a funcao que abre a janela.
        codigo = ("import sys; sys.path.insert(0, r'%s'); import arena; "
                  "arena.abrir_janela = lambda endereco: None; arena.principal()"
                  % os.path.dirname(medir_arena.ARENA_PY))
        comando = [medir_arena.PYTHON, "-c", codigo]
    else:
        comando = [medir_arena.PYTHON, medir_arena.ARENA_PY]
    return subprocess.Popen(comando, cwd=medir_arena.RAIZ, stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)


def esperar_resposta(servidor, inicio):
    while time.perf_counter() - inicio < 120:
        try:
            urllib.request.urlopen(medir_arena.ENDERECO + "/api/estado", timeout=1).read()
            return time.perf_counter() - inicio
        except (urllib.error.URLError, OSError):
            if servidor.poll() is not None:
                return None
            time.sleep(0.05)
    return None


def medir(segundos, sem_tela):
    if medir_arena.porta_ocupada():
        print("O ARENA ja esta aberto (porta 8777). Feche a janela preta e rode de novo.")
        return 1
    inicio = time.perf_counter()
    servidor = subir(sem_tela)
    try:
        pronto = esperar_resposta(servidor, inicio)
        if pronto is None:
            print("O servidor nao respondeu em 120 s.")
            return 1
        proc = medir_arena.Processo(servidor.pid)
        print("Servidor respondeu em %.2f s%s. Medindo %d s em fatias de %d s..."
              % (pronto, " (sem a janela da tela)" if sem_tela else "", segundos, FATIA),
              flush=True)
        print("   de      ate   processador (% de um nucleo)   memoria")
        fatias = []
        cpu_antes, t_antes = proc.cpu_s(), time.perf_counter()
        fim = t_antes + segundos
        while time.perf_counter() < fim:
            time.sleep(FATIA)
            cpu, t = proc.cpu_s(), time.perf_counter()
            pct = 100 * (cpu - cpu_antes) / (t - t_antes)
            ram = proc.ram_mb()[0]
            fatias.append((t_antes - inicio, t - inicio, pct, cpu - cpu_antes))
            print("  %5.0f s  %5.0f s   %6.2f %%  %s   %5.1f MB"
                  % (t_antes - inicio, t - inicio, pct, "#" * min(40, int(round(pct))), ram),
                  flush=True)
            cpu_antes, t_antes = cpu, t

        # Assentou: a partir da primeira fatia em que ESTA e TODAS as
        # seguintes ficam abaixo do limite.
        assentou = None
        for i in range(len(fatias)):
            if all(f[2] < ASSENTADO for f in fatias[i:]):
                assentou = fatias[i][0]
                break
        total = sum(f[3] for f in fatias)
        print()
        print("Processador gasto em %d s: %.2f s de um nucleo." % (segundos, total))
        if assentou is None:
            print("NAO assentou: ate a ultima fatia ainda passava de %.0f%% de um nucleo."
                  % ASSENTADO)
        else:
            depois = [f for f in fatias if f[0] >= assentou]
            gasto = sum(f[3] for f in depois)
            duracao = sum(f[1] - f[0] for f in depois)
            antes = total - gasto
            print("Assentou %.0f s depois de abrir. Ate ali: %.2f s de um nucleo (custo de abrir)."
                  % (assentou, antes))
            print("Depois de assentado (%.0f s): %.2f%% de um nucleo em media."
                  % (duracao, 100 * gasto / max(duracao, 0.001)))
        # Mesma janela que o COLETAR.bat usa (10 s depois dos dados prontos,
        # por 30 s), para comparar com o numero dele.
        janela = [f for f in fatias if f[0] >= pronto + 10 - 0.01 and f[1] <= pronto + 40 + FATIA]
        if janela:
            gasto = sum(f[3] for f in janela)
            duracao = sum(f[1] - f[0] for f in janela)
            print("Na janela do COLETAR.bat (%.0f a %.0f s): %.2f%% de um nucleo."
                  % (janela[0][0], janela[-1][1], 100 * gasto / duracao))
        proc.fechar()
        return 0
    finally:
        subprocess.run(["taskkill", "/PID", str(servidor.pid), "/T", "/F"], capture_output=True)


if __name__ == "__main__":
    numeros = [int(a) for a in sys.argv[1:] if a.isdigit()]
    sys.exit(medir(numeros[0] if numeros else 120, "--sem-tela" in sys.argv))
