# -*- coding: utf-8 -*-
r"""
ARENA - as portas que o Windows reservou e que o ARENA precisa.

Achado de 16/10/2026: o Windows separa faixas de porta para o Hyper-V, o WSL
e o Docker, e elas MUDAM a cada reinicio. Ninguem consegue usar uma porta
dentro dessas faixas: nem o ARENA. Em 16/10, de 55335 a 55434 (UDP); as
portas do ARENA ficaram de fora por uma: a 55435 (a partida a dois, no
RetroArch) e a 55436 (a descoberta dos colegas). Num outro dia, com outra
faixa, a partida a dois simplesmente nao abriria, sem explicar.

O Windows mostra as faixas sem pedir senha de administrador
(netsh interface ipv4 show excludedportrange protocol=tcp e protocol=udp).
O VERIFICAR.bat, o PARTIDA.bat e a janela preta (ao abrir o ARENA) olham
as portas do ARENA contra elas e explicam o que fazer.

No Linux nao existe esse tipo de reserva: a lista fica vazia.
"""
import os
import re
import subprocess

# (porta, protocolo, para que serve)
PORTAS_DO_ARENA = [
    (8777, "tcp", "o servidor do ARENA (a tela)"),
    (55435, "tcp", "a partida a dois (o RetroArch)"),
    (55435, "udp", "a partida a dois (o RetroArch acha a partida na rede)"),
    (55436, "udp", "a descoberta dos colegas na rede"),
]

# O que fazer, para a tela e para os .bat.
O_QUE_FAZER = ("Reinicie o computador: o Windows escolhe outras faixas a cada reinicio. Se acontecer "
               "sempre, o professor (com a senha de administrador) pode mudar a faixa de portas "
               "do Windows para depois das do ARENA, uma vez so: netsh int ipv4 set dynamic tcp "
               "start=56000 num=9536, o mesmo com udp, e reiniciar.")


def ler_faixas(texto):
    """As faixas (inicio, fim) da saida do netsh, em qualquer idioma do
    Windows: as linhas que comecam com dois numeros."""
    return [(int(inicio), int(fim)) for inicio, fim in re.findall(r"^\s*(\d+)\s+(\d+)", texto, re.M)]


def faixas_reservadas(protocolo):
    """As faixas que o Windows reservou neste reinicio, ou [] (fora do
    Windows, ou se o netsh nao respondeu)."""
    if os.name != "nt":
        return []
    try:
        saida = subprocess.run(["netsh", "interface", "ipv4", "show", "excludedportrange",
                                "protocol=" + protocolo], capture_output=True, text=True, timeout=10,
                               errors="replace", creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except (OSError, subprocess.SubprocessError):
        return []
    return ler_faixas(saida.stdout)


def portas_bloqueadas(faixas=None):
    """[{porta, protocolo, para, faixa}] das portas do ARENA que cairam numa
    faixa reservada. 'faixas': {"tcp": [...], "udp": [...]} (para os testes;
    sem ele, pergunta ao Windows)."""
    faixas = faixas if faixas is not None else {p: faixas_reservadas(p) for p in ("tcp", "udp")}
    achadas = []
    for porta, protocolo, para in PORTAS_DO_ARENA:
        for inicio, fim in faixas.get(protocolo, []):
            if inicio <= porta <= fim:
                achadas.append({"porta": porta, "protocolo": protocolo, "para": para, "faixa": (inicio, fim)})
                break
    return achadas


def frase(bloqueada):
    """A explicacao de uma porta bloqueada, para o aluno."""
    return ("A porta %d (%s, %s) esta reservada pelo Windows desde que ele ligou (faixa de %d a %d, das "
            "que o Hyper-V, o WSL e o Docker separam): enquanto isso, ninguem consegue usa-la."
            % (bloqueada["porta"], bloqueada["protocolo"].upper(), bloqueada["para"],
               bloqueada["faixa"][0], bloqueada["faixa"][1]))
