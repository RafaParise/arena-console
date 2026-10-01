# -*- coding: utf-8 -*-
r"""PS2 sem BIOS: o ARENA avisa antes, e o cartao fica amarelo.

Achado de 01/10/2026, montando a versao dos alunos (que vem sem BIOS): o
cartao do PS2 aparecia "pronto" so porque o PCSX2 estava na pasta, e o
PCSX2 abria para reclamar da BIOS. Agora graficos.tem_bios_pcsx2() confere
as duas pastas onde ela pode estar, falta_para_o_externo() devolve a frase
e o /api/catalogo marca o console "falta_sistema" com o motivo.

  1. tem_bios_pcsx2 em pastas temporarias: sem nada, com BIOS na pasta do
     PCSX2, com um .bin de 4 MB em retroarch\system, com um .bin de outro
     tamanho (nao vale);
  2. falta_para_o_externo: frase so quando falta;
  3. avaliar_plataformas: com a BIOS "sumida" (so nesta execucao), o PS2
     sai "falta_sistema" com o motivo; com ela, como antes.

Uso: servidor\python\python.exe testes\teste_ps2_sem_bios.py
"""
import os
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
import limpeza  # noqa: E402
import arena  # noqa: E402
import graficos  # noqa: E402


def main():
    falhas, total = [], [0]

    def confere(nome, ok, detalhe=""):
        total[0] += 1
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, "" if ok else detalhe))
        if not ok:
            falhas.append(nome)

    pasta = tempfile.mkdtemp(prefix="arena_ps2_bios_")
    try:
        exe = os.path.join(pasta, "PCSX2", "pcsx2-qt.exe")
        sistema = os.path.join(pasta, "system")
        os.makedirs(os.path.join(pasta, "PCSX2", "bios"))
        os.makedirs(sistema)
        open(exe, "wb").close()
        confere("sem BIOS em lugar nenhum: nao tem", not graficos.tem_bios_pcsx2(exe, sistema))
        open(os.path.join(sistema, "outra coisa.bin"), "wb").write(b"x" * 1024)
        confere(".bin de outro tamanho em system nao vale", not graficos.tem_bios_pcsx2(exe, sistema))
        with open(os.path.join(sistema, "ps2-0230a-20080220.bin"), "wb") as f:
            f.truncate(graficos.TAMANHO_BIOS_PS2)
        confere(".bin de 4 MB em retroarch\\system vale", graficos.tem_bios_pcsx2(exe, sistema))
        os.remove(os.path.join(sistema, "ps2-0230a-20080220.bin"))
        open(os.path.join(pasta, "PCSX2", "bios", "scph39001.bin"), "wb").write(b"b")
        confere("BIOS na pasta bios\\ do PCSX2 vale", graficos.tem_bios_pcsx2(exe, sistema))
    finally:
        limpeza.apagar_pasta(pasta)

    # 2 e 3: com a funcao trocada so nesta execucao (nenhum arquivo mexido).
    original = graficos.tem_bios_pcsx2
    try:
        graficos.tem_bios_pcsx2 = lambda *_a, **_k: False
        frase = graficos.falta_para_o_externo("PCSX2", os.path.join(RAIZ, "x", "pcsx2-qt.exe"))
        confere("sem BIOS: a frase diz o que fazer (BIOS, retroarch\\system, professor)",
                "BIOS" in frase and "retroarch\\system" in frase and "professor" in frase, frase)
        caminho_pcsx2, _dados = graficos.achar_externo(
            next(p for p in arena.carregar_catalogo() if p["id"] == "ps2"))
        if caminho_pcsx2:
            ps2 = next(p for p in arena.avaliar_plataformas(forcar=True) if p["id"] == "ps2")
            confere("cartao do PS2 sem BIOS: falta_sistema com o motivo",
                    ps2["estado"] == "falta_sistema" and "BIOS" in ps2["motivo"], (ps2["estado"], ps2["motivo"]))
        else:
            print("  (PCSX2 nao esta nesta pasta: parte do cartao pulada)")
        graficos.tem_bios_pcsx2 = lambda *_a, **_k: True
        confere("com BIOS: nada a avisar", graficos.falta_para_o_externo(
            "PCSX2", os.path.join(RAIZ, "x", "pcsx2-qt.exe")) == "")
        if caminho_pcsx2:
            ps2 = next(p for p in arena.avaliar_plataformas(forcar=True) if p["id"] == "ps2")
            confere("cartao do PS2 com BIOS: pronta", ps2["estado"] == "pronta", ps2["estado"])
    finally:
        graficos.tem_bios_pcsx2 = original
        arena.avaliar_plataformas(forcar=True)

    print()
    if falhas:
        print("FALHOU: %d de %d" % (len(falhas), total[0]))
        return 1
    print("PS2 sem BIOS: %d de %d certos." % (total[0], total[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
