# -*- coding: utf-8 -*-
r"""Jogo de varios discos vira um cartao so e abre por uma lista .m3u.

Pendencia de 01/10/2026: "Final Fantasy VII (Disc 1/2/3)" apareciam como
tres jogos, e trocar de disco exigia sair do jogo. Agora o indexador junta
os discos do mesmo jogo, NA MESMA PASTA, quando o nucleo do console aceita
.m3u (conferido no .info dele), e o /api/jogar abre a lista.

  1. agrupar_discos: o que junta e o que NAO junta (Sonic CD, CD32,
     versoes diferentes, formato diferente, console sem .m3u, emulador de
     fora); disco faltando vira aviso; "Disc 1.chd" dentro da pasta do jogo
     fica com o nome da pasta.
  2. lista_de_discos: grava dados\m3u\<nome do disco 1>.m3u (o save fica
     com o mesmo nome de antes); disco sumido ou nucleo sem .m3u abre o
     disco 1, como antes.
  3. RetroArch de verdade abre a lista: PS1 (SwanStation) e Amiga (PUAE),
     com um jogo real repetido como "disco 2" (o teste nao cria jogo
     nenhum na pasta jogos\). O registro do RetroArch tem que dizer que
     carregou a lista e o jogo tem que mostrar imagem.

Uso: servidor\python\python.exe testes\teste_varios_discos.py
"""
import os
import shutil
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import protege_cfg  # noqa: E402
import teste_matriz_multitap as base  # noqa: E402

RAIZ = base.RAIZ
arena = base.arena
indexador = arena.indexador


def item(pasta, nome, plataforma, mb=500.0):
    caminho = os.path.join("jogos", "pessoais", pasta, nome)
    return {"id": caminho.lower(), "arquivo": caminho, "plataforma": plataforma,
            "titulo": indexador.titulo_do_jogo(nome, os.path.join(RAIZ, "jogos", "pessoais", pasta)),
            "tamanho_mb": mb, "avisos": []}


def main():
    falhas, total = [], [0]

    def confere(nome, ok, detalhe=""):
        total[0] += 1
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, "" if ok else detalhe))
        if not ok:
            falhas.append(nome)

    por_id, _ = indexador.carregar_plataformas()

    # ---- 1. o que junta e o que nao junta ---------------------------------
    print("1. agrupar_discos")
    itens = [item("PS1", "Final Fantasy VII (USA) (Disc %d).chd" % n, "ps1") for n in (2, 1, 3)]
    saida = indexador.agrupar_discos(itens, por_id)
    confere("FF7 com 3 discos vira 1 cartao", len(saida) == 1, [i["arquivo"] for i in saida])
    ff7 = saida[0]
    confere("o cartao e' o do disco 1, com os 3 discos em ordem",
            ff7["arquivo"].endswith("(Disc 1).chd") and [os.path.basename(d) for d in ff7.get("discos", [])]
            == ["Final Fantasy VII (USA) (Disc %d).chd" % n for n in (1, 2, 3)], ff7.get("discos"))
    confere("titulo sem o numero do disco e tamanho somado",
            ff7["titulo"] == "Final Fantasy VII" and ff7["tamanho_mb"] == 1500.0,
            (ff7["titulo"], ff7["tamanho_mb"]))
    confere("sem aviso quando nao falta disco", ff7["avisos"] == [], ff7["avisos"])

    saida = indexador.agrupar_discos([item("PS1", "Metal Gear Solid (USA) (Disc 2).chd", "ps1")], por_id)
    confere("so o disco 2 na pasta: avisa que falta o 1",
            len(saida) == 1 and any("Falta o disco 1" in a["texto"] for a in saida[0]["avisos"]),
            saida[0]["avisos"])
    saida = indexador.agrupar_discos([item("PS1", "Jogo (Disc %d).chd" % n, "ps1") for n in (1, 3)], por_id)
    confere("discos 1 e 3: junta e avisa que falta o 2",
            len(saida) == 1 and any("Falta o disco 2" in a["texto"] for a in saida[0]["avisos"]),
            [(i["arquivo"], i["avisos"]) for i in saida])

    saida = indexador.agrupar_discos([item("Amiga", "Alien Breed_Disk%d.adf" % n, "amiga", 0.88) for n in (1, 2)],
                                     por_id)
    confere("Amiga 'Alien Breed_Disk1/2.adf': 1 cartao 'Alien Breed'",
            len(saida) == 1 and saida[0]["titulo"] == "Alien Breed" and len(saida[0].get("discos", [])) == 2,
            [(i["titulo"], i.get("discos")) for i in saida])

    pasta_jogo = "PS1" + os.sep + "Final Fantasy IX"
    saida = indexador.agrupar_discos([item(pasta_jogo, "Disc %d.chd" % n, "ps1") for n in (1, 2)], por_id)
    confere("'Disc 1.chd' dentro da pasta do jogo: 1 cartao com o nome da pasta",
            len(saida) == 1 and saida[0]["titulo"] == "Final Fantasy IX", [i["titulo"] for i in saida])

    nao_juntam = [
        ("Sonic CD", [item("Sega CD", "Sonic CD (USA).chd", "segacd")]),
        ("CD32 no nome", [item("Amiga", "Jogo CD32 (Disk 1).adf", "amiga"),
                          item("Amiga", "Jogo CD32 (Disk 1) (Alt).adf", "amiga")]),
        ("versoes diferentes", [item("PS1", "Jogo (Disc 1) (v1.0).chd", "ps1"),
                                item("PS1", "Jogo (Disc 2) (v1.1).chd", "ps1")]),
        ("formatos diferentes", [item("PS1", "Jogo (Disc 1).chd", "ps1"), item("PS1", "Jogo (Disc 2).cue", "ps1")]),
        ("console sem .m3u (3DO)", [item("3DO", "Jogo (Disc %d).iso" % n, "threedo") for n in (1, 2)]),
        ("emulador de fora (PS2)", [item("PS2", "Jogo (Disc %d).iso" % n, "ps2") for n in (1, 2)]),
    ]
    for nome, lista in nao_juntam:
        saida = indexador.agrupar_discos([dict(i) for i in lista], por_id)
        confere("nao junta: %s" % nome, len(saida) == len(lista) and not any(i.get("discos") for i in saida),
                [(i["titulo"], i.get("discos")) for i in saida])
    confere("nucleo_aceita_m3u le o .info: SwanStation sim, Opera (3DO) nao",
            indexador.nucleo_aceita_m3u("swanstation_libretro.dll")
            and not indexador.nucleo_aceita_m3u("opera_libretro.dll"))

    # ---- 2. a lista .m3u ----------------------------------------------------
    print("2. lista_de_discos")
    jogos_reais = {
        "ps1": os.path.join("jogos", "pessoais", "PS1", "Crash Bandicoot (USA).chd"),
        "amiga": os.path.join("jogos", "pessoais", "Amiga", "Alien Breed_Disk1.adf"),
    }
    faltando = [j for j in jogos_reais.values() if not os.path.isfile(os.path.join(RAIZ, j))]
    if faltando:
        print("  (sem o jogo de exemplo: %s -- partes 2 e 3 puladas)" % faltando)
        return 0 if not falhas else 1
    m3u_antes = set(os.listdir(arena.PASTA_M3U)) if os.path.isdir(arena.PASTA_M3U) else set()
    criados = []
    try:
        disco = jogos_reais["ps1"]
        jogo = {"core": "swanstation_libretro.dll", "discos": [disco, disco]}
        caminho = arena.lista_de_discos(jogo, os.path.join(RAIZ, disco))
        criados.append(caminho)
        confere("grava dados\\m3u\\<nome do disco 1>.m3u",
                os.path.normcase(caminho) == os.path.normcase(
                    os.path.join(arena.PASTA_M3U, "Crash Bandicoot (USA).m3u")) and os.path.isfile(caminho), caminho)
        linhas = open(caminho, encoding="utf-8").read().splitlines()
        confere("a lista tem os 2 discos, caminho inteiro",
                linhas == [os.path.join(RAIZ, disco)] * 2, linhas)
        sem_m3u = arena.lista_de_discos({"core": "opera_libretro.dll", "discos": [disco, disco]},
                                        os.path.join(RAIZ, disco))
        confere("nucleo sem .m3u: abre o disco 1", sem_m3u == os.path.join(RAIZ, disco), sem_m3u)
        sumiu = arena.lista_de_discos({"core": "swanstation_libretro.dll",
                                       "discos": [disco, disco.replace("Crash", "Naoexiste")]},
                                      os.path.join(RAIZ, disco))
        confere("disco sumido: abre o disco 1", sumiu == os.path.join(RAIZ, disco), sumiu)
        um_so = arena.lista_de_discos({"core": "swanstation_libretro.dll", "discos": [disco]},
                                      os.path.join(RAIZ, disco))
        confere("um disco so: abre ele mesmo (sem lista)", um_so == os.path.join(RAIZ, disco), um_so)

        # ---- 3. RetroArch de verdade ---------------------------------------
        print("3. RetroArch abrindo a lista")
        trabalho = tempfile.mkdtemp(prefix="arena_discos_")
        try:
            for console, nucleo, disco in (("PS1", "swanstation", jogos_reais["ps1"]),
                                           ("Amiga", "puae", jogos_reais["amiga"])):
                lista = arena.lista_de_discos({"core": nucleo + "_libretro.dll", "discos": [disco, disco]},
                                              os.path.join(RAIZ, disco))
                criados.append(lista)
                pasta = os.path.join(trabalho, console)
                r = base.abrir(console, lista, nucleo, pasta)
                registro = open(os.path.join(pasta, "sozinho.log"), encoding="utf-8", errors="ignore").read()
                sobre = [l.strip() for l in registro.splitlines()
                         if ".m3u" in l.lower() or "disk" in l.lower() or "disc" in l.lower()]
                print("     registro (%s): %s" % (console, " | ".join(sobre[:6])[:400]))
                confere("%s: abre pela lista e mostra imagem" % console,
                        r["abre_e_mostra_imagem"] and any(".m3u" in l.lower() for l in sobre),
                        (r, sobre[:3]))
        finally:
            shutil.rmtree(trabalho, ignore_errors=True)
    finally:
        # So o que este teste criou; o resto de dados\m3u fica.
        for caminho in set(criados):
            if os.path.basename(caminho) not in m3u_antes and caminho.lower().endswith(".m3u"):
                try:
                    os.remove(caminho)
                except OSError:
                    pass
        if not m3u_antes and os.path.isdir(arena.PASTA_M3U) and not os.listdir(arena.PASTA_M3U):
            os.rmdir(arena.PASTA_M3U)

    print()
    if falhas:
        print("FALHOU: %d de %d" % (len(falhas), total[0]))
        return 1
    print("Varios discos: %d de %d certos." % (total[0], total[0]))
    return 0


if __name__ == "__main__":
    sys.exit(protege_cfg.rodar(main))
