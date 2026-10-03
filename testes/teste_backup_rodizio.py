# -*- coding: utf-8 -*-
r"""O rodizio da copia de seguranca mantem SO as 3 mais recentes, de verdade.

Achado de 01/10/2026: a pasta backup\ deste computador tinha 209 copias
(o ARENA promete 3). O RetroArch cria saves\.netplay com o atributo
"somente leitura"; a copia herdava o atributo e o rmtree(ignore_errors)
apagava os arquivos e desistia da pasta, calado -- sobrava um esqueleto por
backup, e cada backup novo tentava apagar todos de novo.

Num ARENA isolado (pastas temporarias; o backup\ de verdade nao e' tocado):
  1. saves com um save comum e uma pasta .netplay somente leitura;
  2. 5 esqueletos velhos (pastas vazias, com .netplay somente leitura);
  3. 4 backups seguidos.
Confere: sobram exatamente 3 copias, os esqueletos sumiram, nenhuma copia
leva o .netplay, o save comum esta em todas, e o .zip do Exportar (que nao
e' pasta de data) continua la.

02/10/2026: pasta que NAO tem nome de data (backup\originais, onde a
conversao de fliperama guarda o jogo original) fica e nao toma vaga de
copia -- antes o rodizio contava qualquer pasta, e uma de nome "menor" que
as datas ("0-guardar") seria apagada.

Uso: servidor\python\python.exe testes\teste_backup_rodizio.py
"""
import os
import stat
import sys
import tempfile
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
import limpeza  # noqa: E402
import arena  # noqa: E402


def somente_leitura(caminho):
    os.chmod(caminho, stat.S_IREAD)


def main():
    falhas, total = [], [0]

    def confere(nome, ok, detalhe=""):
        total[0] += 1
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, "" if ok else detalhe))
        if not ok:
            falhas.append(nome)

    pasta = tempfile.mkdtemp(prefix="arena_backup_rodizio_")
    guardados = (arena.PASTA_BACKUP, arena.PASTA_SAVES, arena.PASTA_DADOS, arena.PASTA_RETROARCH)
    try:
        arena.PASTA_BACKUP = os.path.join(pasta, "backup")
        arena.PASTA_SAVES = os.path.join(pasta, "retroarch", "saves")
        arena.PASTA_DADOS = os.path.join(pasta, "dados")
        arena.PASTA_RETROARCH = os.path.join(pasta, "retroarch")
        for p in (arena.PASTA_BACKUP, arena.PASTA_SAVES, arena.PASTA_DADOS):
            os.makedirs(p)
        open(os.path.join(arena.PASTA_DADOS, "config.json"), "w").write("{}")
        os.makedirs(os.path.join(arena.PASTA_SAVES, "SwanStation"))
        open(os.path.join(arena.PASTA_SAVES, "SwanStation", "CTR.srm"), "wb").write(b"save" * 100)
        netplay = os.path.join(arena.PASTA_SAVES, ".netplay")
        os.makedirs(netplay)
        open(os.path.join(netplay, "do_colega.srm"), "wb").write(b"x")
        somente_leitura(os.path.join(netplay, "do_colega.srm"))
        somente_leitura(netplay)
        confere("a pasta .netplay do teste esta mesmo somente leitura",
                bool(os.stat(netplay).st_file_attributes & stat.FILE_ATTRIBUTE_READONLY))

        # Esqueletos como os de verdade: pasta de data, so com pastas dentro.
        for n in range(5):
            esqueleto = os.path.join(arena.PASTA_BACKUP, "2026-09-20_2218%02d" % n, "saves", ".netplay")
            os.makedirs(esqueleto)
            somente_leitura(esqueleto)
        open(os.path.join(arena.PASTA_BACKUP, "meu-progresso-2026-09-27_2311.zip"), "wb").write(b"PK")
        for avulsa in ("originais", "0-guardar"):
            os.makedirs(os.path.join(arena.PASTA_BACKUP, avulsa))
            open(os.path.join(arena.PASTA_BACKUP, avulsa, "jogo.zip"), "wb").write(b"PK")

        for _ in range(4):
            arena.fazer_backup()
            time.sleep(1.05)      # o nome da copia e' a data com segundos

        copias = sorted(d for d in os.listdir(arena.PASTA_BACKUP)
                        if os.path.isdir(os.path.join(arena.PASTA_BACKUP, d)) and arena.e_pasta_de_copia(d))
        confere("sobram exatamente %d copias" % arena.COPIAS_MANTIDAS,
                len(copias) == arena.COPIAS_MANTIDAS, copias)
        confere("os 5 esqueletos velhos sumiram", not any(c.startswith("2026-09-20") for c in copias), copias)
        confere("nenhuma copia leva o .netplay",
                not any(os.path.exists(os.path.join(arena.PASTA_BACKUP, c, "saves", ".netplay")) for c in copias))
        confere("o save comum esta em todas as copias",
                all(os.path.isfile(os.path.join(arena.PASTA_BACKUP, c, "saves", "SwanStation", "CTR.srm"))
                    for c in copias))
        confere("o .zip do Exportar continua la",
                os.path.isfile(os.path.join(arena.PASTA_BACKUP, "meu-progresso-2026-09-27_2311.zip")))
        confere("pastas sem nome de data (originais, 0-guardar) ficam, com o que tem dentro",
                all(os.path.isfile(os.path.join(arena.PASTA_BACKUP, a, "jogo.zip")) for a in ("originais", "0-guardar")))
        confere("e nao tomam vaga: sao 3 copias de data alem delas",
                len([d for d in os.listdir(arena.PASTA_BACKUP)
                     if os.path.isdir(os.path.join(arena.PASTA_BACKUP, d))]) == arena.COPIAS_MANTIDAS + 2)
        confere("o .netplay de verdade (em saves) nao foi mexido",
                os.path.isfile(os.path.join(netplay, "do_colega.srm")))
    finally:
        (arena.PASTA_BACKUP, arena.PASTA_SAVES, arena.PASTA_DADOS, arena.PASTA_RETROARCH) = guardados
        confere("a pasta do teste sai do Temp (com o somente leitura)", limpeza.apagar_pasta(pasta))

    print()
    if falhas:
        print("FALHOU: %d de %d" % (len(falhas), total[0]))
        return 1
    print("Rodizio da copia de seguranca: %d de %d certos." % (total[0], total[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
