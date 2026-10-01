# -*- coding: utf-8 -*-
r"""O verificador conta o que os temporarios OCUPAM, nao o tamanho de fachada.

Achado de 01/10/2026: o RPCS3 deixa no Temp um arquivo "esparso" de
memoria virtual que diz ter 32 GB e ocupa quase nada; o item "pasta de
arquivos temporarios grande" do VERIFICAR/COLETAR acusava 35 GB numa pasta
de 0,5 GB. barreiras.tamanho_no_disco() pergunta ao Windows o tamanho
ocupado de arquivo esparso ou comprimido.

Cria, numa pasta temporaria, um arquivo esparso de 1 GB com 1 byte escrito
(sem administrador: FSCTL_SET_SPARSE no proprio arquivo) e confere.

Uso: servidor\python\python.exe testes\teste_temp_esparso.py
"""
import ctypes
import msvcrt
import os
import sys
import tempfile
from ctypes import wintypes

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "servidor"))
import limpeza  # noqa: E402
import barreiras  # noqa: E402

FSCTL_SET_SPARSE = 0x000900C4


def main():
    falhas, total = [], [0]

    def confere(nome, ok, detalhe=""):
        total[0] += 1
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, "" if ok else detalhe))
        if not ok:
            falhas.append(nome)

    pasta = tempfile.mkdtemp(prefix="arena_esparso_")
    try:
        esparso = os.path.join(pasta, "memoria_virtual.tmp")
        with open(esparso, "wb") as f:
            devolvidos = wintypes.DWORD(0)
            ok = ctypes.windll.kernel32.DeviceIoControl(
                wintypes.HANDLE(msvcrt.get_osfhandle(f.fileno())), FSCTL_SET_SPARSE,
                None, 0, None, 0, ctypes.byref(devolvidos), None)
            f.seek(1024 ** 3 - 1)
            f.write(b"x")
        if not ok:
            print("  (este disco nao aceita arquivo esparso: nada a testar)")
            return 0
        comum = os.path.join(pasta, "comum.bin")
        with open(comum, "wb") as f:
            f.write(os.urandom(300 * 1024))
        fachada = os.path.getsize(esparso)
        ocupado = barreiras.tamanho_no_disco(esparso)
        confere("arquivo esparso de 1 GB: fachada 1 GB, ocupado < 1 MB",
                fachada == 1024 ** 3 and ocupado < 1024 ** 2, (fachada, ocupado))
        confere("arquivo comum: ocupado = tamanho", barreiras.tamanho_no_disco(comum) == 300 * 1024,
                barreiras.tamanho_no_disco(comum))
        confere("arquivo que nao existe: 0 (nao derruba)",
                barreiras.tamanho_no_disco(os.path.join(pasta, "nao existe")) == 0)
        guardado = os.environ.get("TEMP")
        try:
            os.environ["TEMP"] = pasta
            medido = barreiras._memoria_e_energia().get("temp_mb")
        finally:
            os.environ["TEMP"] = guardado
        confere("o verificador mede a pasta com o esparso em menos de 2 MB (era 1.024)",
                medido is not None and medido < 2, medido)
    finally:
        limpeza.apagar_pasta(pasta)

    print()
    if falhas:
        print("FALHOU: %d de %d" % (len(falhas), total[0]))
        return 1
    print("Temporarios esparsos: %d de %d certos." % (total[0], total[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
