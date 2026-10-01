# -*- coding: utf-8 -*-
r"""Nomes dos adaptadores de rede: o PowerShell nao pode ficar em laco.

Achado de 01/10/2026, reproduzido: quando o PowerShell que le os nomes dos
adaptadores falhava (modo restrito, bloqueado, ou mais de 15 s para
responder num notebook fraco) ou nao trazia um dos enderecos do computador,
o ARENA abria OUTRO PowerShell a cada consulta de endereco -- o grito na
rede faz uma a cada 5 s, o vigia a cada 20 s. No teste: 24 PowerShell em
12 s. Num Celeron, um nucleo inteiro ocupado fora do ARENA (o PowerShell e'
outro programa: o "servidor parado" nem ve).

Sem rede de verdade e sem PowerShell de verdade: o subprocess.run e'
trocado por um falso que conta as chamadas.

Uso: servidor\python\python.exe testes\teste_adaptadores_sem_laco.py
"""
import os
import subprocess
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
import arena  # noqa: E402

CHAMADAS = []
RESPOSTA = {"modo": "falha", "texto": ""}
ORIGINAL = subprocess.run


def falso_run(comando, *a, **k):
    if isinstance(comando, list) and comando and "Get-NetIPAddress" in " ".join(map(str, comando)):
        CHAMADAS.append(time.time())
        time.sleep(0.05)
        if RESPOSTA["modo"] == "falha":
            raise subprocess.TimeoutExpired(comando, 15)
        return subprocess.CompletedProcess(comando, 0, stdout=RESPOSTA["texto"], stderr="")
    return ORIGINAL(comando, *a, **k)


def zerar():
    CHAMADAS.clear()
    arena._adaptadores.update({"quando": 0.0, "mapa": {}, "buscando": False, "falhas": 0})
    arena._cache_enderecos.update({"quando": 0.0, "lista": None})


def consultar_por(segundos):
    """O que o grito e o vigia fazem, so que muito mais rapido (a cada 0,1 s)."""
    fim = time.time() + segundos
    while time.time() < fim:
        arena.enderecos_locais()
        time.sleep(0.1)
    time.sleep(0.3)     # deixa a ultima pergunta em segundo plano terminar


def main():
    falhas, total = [], [0]

    def confere(nome, ok, detalhe=""):
        total[0] += 1
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, detalhe if not ok else ""))
        if not ok:
            falhas.append(nome)

    subprocess.run = falso_run
    try:
        # 1. PowerShell falhando: uma pergunta, depois espera.
        zerar()
        RESPOSTA["modo"] = "falha"
        consultar_por(3)
        confere("PowerShell que falha e' chamado 1 vez em 3 s (era 1 a cada consulta)",
                len(CHAMADAS) == 1, "%d chamadas" % len(CHAMADAS))
        confere("a falha fica contada", arena._adaptadores["falhas"] == 1)

        # 2. Espera cresce com as falhas e para em 10 minutos.
        esperas = []
        for n in range(1, 8):
            arena._adaptadores["falhas"] = n
            esperas.append(arena.espera_dos_adaptadores())
        confere("espera depois de falhas: 60, 120, 240, 480, 600, 600, 600 s",
                esperas == [60.0, 120.0, 240.0, 480.0, 600.0, 600.0, 600.0], str(esperas))

        # 3. Resposta sem um dos enderecos deste computador: pergunta 1 vez
        #    e espera 1 minuto (antes perguntava de novo a cada consulta).
        zerar()
        RESPOSTA.update(modo="ok", texto="10.99.99.99|Wi-Fi|placa que nao existe aqui\n")
        consultar_por(3)
        confere("endereco que nao veio na resposta: 1 pergunta em 3 s",
                len(CHAMADAS) == 1, "%d chamadas" % len(CHAMADAS))

        # 4. Resposta completa: os nomes valem e nao se pergunta de novo.
        zerar()
        ips = [e["ip"] for e in arena.enderecos_locais()]
        time.sleep(0.3)
        texto = "".join("%s|Wi-Fi|Intel Wi-Fi\n" % ip for ip in ips)
        zerar()
        RESPOSTA.update(modo="ok", texto=texto)
        consultar_por(2)
        confere("resposta completa: 1 pergunta so", len(CHAMADAS) == 1, "%d chamadas" % len(CHAMADAS))
        confere("o mapa ficou com os nomes", set(arena._adaptadores["mapa"]) == set(ips),
                str(arena._adaptadores["mapa"]))

        # 5. O nome continua decidindo a classificacao (VPN pelo nome).
        zerar()
        RESPOSTA.update(modo="ok", texto="".join("%s|NordLynx|NordVPN adapter\n" % ip for ip in ips))
        arena.enderecos_locais()
        time.sleep(0.3)
        tipos = {e["ip"]: e["tipo"] for e in arena.enderecos_locais()}
        reais = [ip for ip in ips if not ip.startswith("127.")]
        confere("adaptador com nome de VPN continua marcado como VPN",
                not reais or all(tipos.get(ip) == "vpn" for ip in reais), str(tipos))

        # 6. Mapa velho (mais de 10 min) pede de novo, uma vez. (A lista de
        #    enderecos tem cache proprio de 30 s; o vigia a renova com
        #    forcar=True a cada volta -- aqui, zerada a mao.)
        CHAMADAS.clear()
        arena._adaptadores["quando"] = time.time() - arena.VALIDADE_ADAPTADORES - 1
        arena._cache_enderecos["quando"] = 0.0
        consultar_por(1)
        confere("mapa de mais de 10 minutos: renova 1 vez", len(CHAMADAS) == 1, "%d chamadas" % len(CHAMADAS))
    finally:
        subprocess.run = ORIGINAL

    print()
    if falhas:
        print("FALHOU: %d de %d" % (len(falhas), total[0]))
        return 1
    print("Adaptadores sem laco: %d de %d certos." % (total[0], total[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
