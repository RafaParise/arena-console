# -*- coding: utf-8 -*-
r"""Jogo de Satellaview sem a BIOS BS-X: o cartao avisa antes de abrir.

Achado de 02/10/2026 (teste_abrir_todos): os 5 "BS F-ZERO" da pasta do
Super Nintendo nao abriam ("falha ao carregar o conteudo") -- o Snes9x so
abre cartucho de Satellaview com a BIOS dele (BS-X.bin, ou BS-X.bios nas
versoes antigas) em retroarch\system -- e o cartao do jogo nao dizia nada.
Desde 03/10/2026 o aviso vem de servidor\bios.py (junto com os do Sega CD,
Saturn e Dreamcast) e diz qual cartucho e' a BIOS.

Num ARENA de mentira, numa pasta temporaria (nenhum jogo de verdade e'
tocado):
  1. "BS Teste (J).smc" sem a BIOS: aviso no jogo, com o nome do arquivo;
  2. com a BIOS (BS-X.bin, ou BS-X.bios): sem aviso;
  3. jogo comum de Super Nintendo: sem aviso;
  4. extensao .bs entra na lista (o Snes9x aceita .bs);
  5. "BS" no nome sem cabecalho de Satellaview (o BS F-Zero Deluxe, feito
     para abrir sozinho -- testado em 03/10/2026): sem aviso. O ARENA confere
     o cabecalho como o proprio Snes9x (bsx.cpp, is_bsx).

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
    raiz_original = indexador.RAIZ
    try:
        indexador.RAIZ = pasta                      # retroarch\system de mentira
        sistema = os.path.join(pasta, "retroarch", "system")
        os.makedirs(sistema)
        jogos_pasta = os.path.join(pasta, "jogos")
        snes = os.path.join(jogos_pasta, por_id["snes"]["pasta"])
        os.makedirs(snes)
        # Cartucho de Satellaview de mentira: o cabecalho em 0x7FC0 que o
        # Snes9x reconhece (0x33 em 0x7FDA, mes 1 em 0x7FD6, banco 0x20).
        cartucho_bs = bytearray(0x8000)
        cartucho_bs[0x7FD5], cartucho_bs[0x7FD6], cartucho_bs[0x7FD7] = 0x80, 0x10, 0x01
        cartucho_bs[0x7FD8], cartucho_bs[0x7FDA] = 0x20, 0x33
        for nome, dados in (("BS Teste (J).smc", cartucho_bs), ("Jogo Comum (USA).sfc", b"\0" * 1024),
                            ("Outro BS.bs", cartucho_bs), ("BS Deluxe Sozinho (USA).sfc", b"\0" * 0x8000)):
            with open(os.path.join(snes, nome), "wb") as f:
                f.write(bytes(dados))

        def avisos():
            jogos = indexador.varrer_pasta(jogos_pasta, "pessoais", por_extensao, por_id)
            return {os.path.basename(j["arquivo"]): [a["texto"] for a in j.get("avisos", [])] for j in jogos}

        sem = avisos()
        confere("BS sem a BIOS: aviso no cartao, com o nome do arquivo",
                any("Satellaview" in a and "BS-X.bin" in a for a in sem.get("BS Teste (J).smc", [])), sem)
        confere("jogo comum: sem aviso", sem.get("Jogo Comum (USA).sfc") == [], sem.get("Jogo Comum (USA).sfc"))
        confere("extensao .bs entra na lista (e avisa)", any("Satellaview" in a for a in sem.get("Outro BS.bs", [])),
                sorted(sem))
        confere("'BS' no nome sem cabeçalho de Satellaview: sem aviso",
                sem.get("BS Deluxe Sozinho (USA).sfc") == [], sem.get("BS Deluxe Sozinho (USA).sfc"))
        for nome_bios in ("BS-X.bin", "BS-X.bios"):
            caminho = os.path.join(sistema, nome_bios)
            with open(caminho, "wb") as f:
                f.write(b"\0" * 1024)
            com = avisos()
            confere("com a BIOS (%s): sem aviso" % nome_bios, com.get("BS Teste (J).smc") == [],
                    com.get("BS Teste (J).smc"))
            os.remove(caminho)
    finally:
        indexador.RAIZ = raiz_original
        limpeza.apagar_pasta(pasta)

    print()
    if falhas:
        print("FALHOU: %d de %d" % (len(falhas), total[0]))
        return 1
    print("Satellaview: %d de %d certos." % (total[0], total[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
