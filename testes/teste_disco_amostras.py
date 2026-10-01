# -*- coding: utf-8 -*-
r"""Teste de velocidade do disco na abertura: so insiste perto da divisa.

Achado de 01/10/2026: hardware.medir_velocidade() tinha um "continue" onde
o comentario dizia "nao precisa insistir". Resultado: TODA abertura do
ARENA gravava 3 x 8 MB no disco dele -- e num pen drive comum (15 a
40 MB/s) isso custava mais de 1 s so para medir, dentro do teto 1b
(2,3 s). Agora: uma amostra; mais duas so quando a primeira cai a menos
de 30% de uma divisa de classe (15, 45, 150 MB/s).

O disco e' "fingido" trocando o open() do hardware.py por um que demora o
quanto um disco de X MB/s demoraria. Grava de verdade numa pasta temporaria.

Uso: servidor\python\python.exe testes\teste_disco_amostras.py
"""
import builtins
import os
import shutil
import sys
import tempfile
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
import hardware  # noqa: E402

CONTAGEM = {"gravacoes": 0}


def disco_de(mb_por_s):
    """open() que faz cada 1 MB gravado demorar como num disco de X MB/s."""
    original = builtins.open

    class Lento:
        def __init__(self, arquivo):
            self.arquivo = arquivo

        def write(self, dados):
            if mb_por_s:
                time.sleep(len(dados) / (1024 * 1024) / mb_por_s)
            return self.arquivo.write(dados)

        def __getattr__(self, nome):
            return getattr(self.arquivo, nome)

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return self.arquivo.__exit__(*a)

    def falso_open(caminho, modo="r", *a, **k):
        arquivo = original(caminho, modo, *a, **k)
        if "w" in modo:
            CONTAGEM["gravacoes"] += 1
            return Lento(arquivo)
        return arquivo
    return falso_open


def main():
    falhas, total = [], [0]

    def confere(nome, ok, detalhe=""):
        total[0] += 1
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, detalhe))
        if not ok:
            falhas.append(nome)

    confere("divisas sao as mesmas da classificacao (15, 45, 150)",
            hardware.DIVISAS_DISCO == (15.0, 45.0, 150.0))
    confere("25 MB/s nao esta perto de divisa", not hardware.perto_da_divisa(25))
    confere("45 MB/s esta perto de divisa", hardware.perto_da_divisa(45))
    confere("1.600 MB/s (NVMe) nao esta perto de divisa", not hardware.perto_da_divisa(1600))
    confere("120 MB/s esta perto da divisa de 150", hardware.perto_da_divisa(120))

    pasta = tempfile.mkdtemp(prefix="arena_disco_")
    try:
        casos = [(None, 1, "disco rapido de verdade"), (25, 1, "pen drive de 25 MB/s"),
                 (45, 3, "45 MB/s, em cima da divisa"), (5, 1, "pen drive lento de 5 MB/s")]
        for mbs, esperadas, nome in casos:
            CONTAGEM["gravacoes"] = 0
            hardware.open = disco_de(mbs)
            try:
                inicio = time.perf_counter()
                medida = hardware.medir_velocidade(pasta)
                gasto = time.perf_counter() - inicio
            finally:
                del hardware.open
            confere("%s: %d amostra(s)" % (nome, esperadas),
                    CONTAGEM["gravacoes"] == esperadas,
                    "(%d amostras, %.2f s, %s MB/s medidos, amostra de %s MB)" % (
                        CONTAGEM["gravacoes"], gasto, medida and medida["escrita_mbs"],
                        medida and medida.get("amostra_mb")))
            if mbs:
                confere("%s: velocidade medida perto da real" % nome,
                        abs(medida["escrita_mbs"] - mbs) <= mbs * 0.2, str(medida))
            if mbs == 5:
                confere("pen drive lento: para em ~2 MB (antes gravava 8 MB, 1,6 s)",
                        medida["amostra_mb"] <= 3 and gasto < 0.8, "%.2f s" % gasto)
        confere("o arquivo do teste nao fica para tras",
                not os.path.exists(os.path.join(pasta, ".arena_teste_velocidade")))
    finally:
        shutil.rmtree(pasta, ignore_errors=True)

    print()
    if falhas:
        print("FALHOU: %d de %d" % (len(falhas), total[0]))
        return 1
    print("Disco na abertura: %d de %d certos." % (total[0], total[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
