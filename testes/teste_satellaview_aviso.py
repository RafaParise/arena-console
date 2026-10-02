# -*- coding: utf-8 -*-
r"""Jogo de Satellaview sem a BIOS BS-X: o cartao avisa antes de abrir.

Achado de 02/10/2026 (teste_abrir_todos): os 5 "BS F-ZERO" da pasta do
Super Nintendo nao abriam ("falha ao carregar o conteudo") -- o Snes9x so
abre cartucho de Satellaview com a BIOS dele (BS-X.bin ou BS-X.bios) em
retroarch\system -- e o cartao do jogo nao dizia nada.

Numa pasta temporaria (nenhum jogo de verdade e' tocado):
  1. "BS Teste (J).smc" sem a BIOS: aviso no jogo;
  2. com a BIOS: sem aviso;
  3. jogo comum de Super Nintendo: sem aviso;
  4. extensao .bs entra na lista (o Snes9x aceita .bs).

Uso: servidor\python\python.exe testes\teste_satellaview_aviso.py
"""
import os
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "servidor"))
import limpeza  # noqa: E402
import indexador  # noqa: E402


def main():
    falhas, total = [], [0]

    def confere(nome, ok, detalhe=""):
        total[0] += 1
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, "" if ok else detalhe))
        if not ok:
            falhas.append(nome)

    por_id, por_extensao = indexador.carregar_plataformas()
    pasta = tempfile.mkdtemp(prefix="arena_satellaview_")
    original = indexador.tem_bios_do_satellaview
    try:
        snes = os.path.join(pasta, por_id["snes"]["pasta"])
        os.makedirs(snes)
        for nome in ("BS Teste (J).smc", "Jogo Comum (USA).sfc", "Outro BS.bs"):
            with open(os.path.join(snes, nome), "wb") as f:
                f.write(b"\0" * 1024)

        def avisos(sem_bios):
            indexador.tem_bios_do_satellaview = (lambda: not sem_bios)
            jogos = indexador.varrer_pasta(pasta, "pessoais", por_extensao, por_id)
            return {os.path.basename(j["arquivo"]): [a["texto"] for a in j.get("avisos", [])] for j in jogos}

        sem = avisos(sem_bios=True)
        confere("BS sem a BIOS: aviso no cartao",
                any("Satellaview" in a and "BS-X" in a for a in sem.get("BS Teste (J).smc", [])), sem)
        confere("jogo comum: sem aviso", sem.get("Jogo Comum (USA).sfc") == [], sem.get("Jogo Comum (USA).sfc"))
        confere("extensao .bs entra na lista (e avisa)", any("Satellaview" in a for a in sem.get("Outro BS.bs", [])),
                sorted(sem))
        com = avisos(sem_bios=False)
        confere("com a BIOS: sem aviso", com.get("BS Teste (J).smc") == [], com.get("BS Teste (J).smc"))
    finally:
        indexador.tem_bios_do_satellaview = original
        limpeza.apagar_pasta(pasta)
    confere("tem_bios_do_satellaview le a pasta de BIOS de verdade sem erro",
            indexador.tem_bios_do_satellaview() in (True, False))

    print()
    if falhas:
        print("FALHOU: %d de %d" % (len(falhas), total[0]))
        return 1
    print("Satellaview: %d de %d certos." % (total[0], total[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
