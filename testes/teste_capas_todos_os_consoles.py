# -*- coding: utf-8 -*-
r"""Capas para os consoles que ainda nao tinham (pedido do Rafael, 02/10/2026).

Antes: so 16 consoles tinham busca de capa, e so pelo nome EXATO do banco
do RetroArch ("PS2, PS3 e Xbox 360 nao tem cobertura boa", dizia o codigo
-- o banco do PS2 tem 8.501 capas). Agora:
  - todo console com banco no libretro-thumbnails (131 bancos, lista
    oficial) busca capa; sem banco, so Uzebox, Tamagotchi e Java ME;
  - pela LISTA oficial de cada banco: nome parecido, regiao certa, nome de
    cena limpo ("... V2 00 USA MULTi3 PSP PUSSYCAT"), subtitulo a mais --
    sem confundir "Crash Bandicoot" com "Crash Bandicoot 3";
  - pelo proprio disco: icone do PS3/PSP (sem internet), Title ID do
    Xbox 360 (capa oficial da Microsoft), codigo de GameCube/Wii (GameTDB);
  - Cover.jpg dentro da pasta de um jogo sozinho vale como capa;
  - botao "Buscar capas que faltam": busca todas em segundo plano.

  1. todo console do consoles.json tem banco ou esta na lista "sem banco";
     com internet, todo banco do mapa existe de verdade;
  2. escolha do nome (logica);
  3. o disco: um .iso montado pelo teste com PSP_GAME\ICON0.PNG; e os
     jogos de verdade da pasta, se estiverem (PS3, Xbox 360, Wii);
  4. o indexador acha capa .jpg e a Cover.jpg da pasta de um jogo sozinho
     (e NAO a de uma pasta com varios jogos);
  5. servidor isolado: "Buscar capas que faltam" acha a capa do .iso de
     teste e a lista passa a mostrar;
  6. com internet: PS2, Xbox 360 e GameCube de verdade baixam capa.

Uso: servidor\python\python.exe testes\teste_capas_todos_os_consoles.py
"""
import json
import os
import socket
import struct
import subprocess
import sys
import tempfile
import time
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
import capas_do_disco  # noqa: E402
import capas_online  # noqa: E402
import limpeza  # noqa: E402

SEM_BANCO = {"uzebox", "tamagotchi", "j2me"}
P = os.path.join(RAIZ, "jogos", "pessoais")
# PNG minimo valido (1x1), o mesmo tipo de icone que o disco traz.
PNG = bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
                    "0000000d4944415478da63f8cfc0f01f0005000201a5b5a1c70000000049454e44ae426082")


def registro(nome, setor, tamanho, pasta=False):
    nome = nome.encode("ascii")
    corpo = (bytes([0]) + struct.pack("<I", setor) + struct.pack(">I", setor)
             + struct.pack("<I", tamanho) + struct.pack(">I", tamanho)
             + bytes(7) + bytes([0x02 if pasta else 0, 0, 0]) + struct.pack("<H", 1) + struct.pack(">H", 1)
             + bytes([len(nome)]) + nome)
    if len(nome) % 2 == 0:
        corpo += b"\x00"
    return bytes([len(corpo) + 1]) + corpo


def montar_iso(caminho, pasta_jogo, icone):
    """ISO 9660 minimo: raiz -> <pasta_jogo> -> ICON0.PNG."""
    setor = 2048
    raiz = registro("\x00", 18, setor, True) + registro("\x01", 18, setor, True) + registro(pasta_jogo, 19, setor, True)
    pasta = registro("\x00", 19, setor, True) + registro("\x01", 18, setor, True) + registro("ICON0.PNG;1", 20, len(icone))
    descritor = bytearray(setor)
    descritor[0:7] = b"\x01CD001\x01"
    descritor[156:156 + 34] = registro("\x00", 18, setor, True)[:34]
    fim = bytearray(setor)
    fim[0:7] = b"\xffCD001\x01"
    with open(caminho, "wb") as arquivo:
        arquivo.write(bytes(16 * setor) + bytes(descritor) + bytes(fim))
        arquivo.write(raiz.ljust(setor, b"\x00") + pasta.ljust(setor, b"\x00"))
        arquivo.write(icone.ljust(setor, b"\x00"))


def tem_internet():
    try:
        socket.create_connection(("thumbnails.libretro.com", 443), timeout=4).close()
        return True
    except OSError:
        return False


def main():
    falhas, total = [], [0]

    def confere(nome, ok, detalhe=""):
        total[0] += 1
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, "" if ok else detalhe), flush=True)
        if not ok:
            falhas.append(nome)

    internet = tem_internet()
    pasta = tempfile.mkdtemp(prefix="arena_capas_teste_")
    try:
        print("1. Todo console tem banco de capas")
        consoles = json.load(open(os.path.join(RAIZ, "servidor", "consoles.json"), encoding="utf-8"))["plataformas"]
        sem = sorted(p["id"] for p in consoles if p["id"] not in capas_online.REPO_POR_PLATAFORMA
                     and p["id"] not in SEM_BANCO)
        confere("todo console do ARENA tem banco (ou esta na lista sem banco)", not sem, sem)
        if internet:
            nomes = set()
            for pagina in (1, 2, 3):
                pedido = urllib.request.Request(
                    "https://api.github.com/orgs/libretro-thumbnails/repos?per_page=100&page=%d" % pagina,
                    headers={"User-Agent": "ARENA/1.0"})
                try:
                    with urllib.request.urlopen(pedido, timeout=20) as resposta:
                        nomes |= {r["name"] for r in json.loads(resposta.read())}
                except (OSError, ValueError):
                    break
            if len(nomes) > 100:
                usados = {r for v in capas_online.REPO_POR_PLATAFORMA.values()
                          for r in ((v,) if isinstance(v, str) else v)}
                confere("todo banco do mapa existe no libretro-thumbnails (%d bancos)" % len(nomes),
                        usados <= nomes, sorted(usados - nomes))
            else:
                print("  (a API do GitHub nao respondeu agora: conferencia dos nomes pulada)")

        print("2. Escolha do nome")
        lista = ["Crash Nitro Kart (USA)", "Crash Nitro Kart (Europe) (En,Fr,De)", "Crash Bandicoot (USA)",
                 "Street Fighter II Turbo (USA)", "Metal Gear Solid - Peace Walker (Japan) (v1.02)",
                 "Metal Gear Solid - Peace Walker (USA) (En,Fr,Es) (v2.00)", "Legend of Zelda, The - A Link to the Past (USA)"]
        for titulo, base, esperado in (
                ("Crash Nitro Kart", "Crash Nitro Kart", "Crash Nitro Kart (USA)"),
                ("Crash Nitro Kart", "Crash Nitro Kart (Europe)", "Crash Nitro Kart (Europe) (En,Fr,De)"),
                ("Street Fighter II Turbo Hyper Fighting", "", "Street Fighter II Turbo (USA)"),
                ("Metal Gear Solid Peace Walker V2 00 USA MULTi3 PSP PUSSYCAT", "",
                 "Metal Gear Solid - Peace Walker (USA) (En,Fr,Es) (v2.00)"),
                ("The Legend of Zelda A Link to the Past", "", "Legend of Zelda, The - A Link to the Past (USA)"),
                ("Crash Bandicoot 3 Warped", "", None),
                ("Mario", "", None)):
            escolhido = capas_online.escolher_capa(lista, titulo, base)
            confere("%r -> %r" % (titulo[:40], esperado), escolhido == esperado, escolhido)

        print("3. O proprio disco")
        iso = os.path.join(pasta, "teste psp.iso")
        montar_iso(iso, "PSP_GAME", PNG)
        confere("icone de dentro de um .iso de PSP montado pelo teste",
                capas_do_disco.icone_do_disco(iso, "psp") == PNG)
        confere("disco sem a pasta do console: sem icone (sem chute)",
                capas_do_disco.icone_do_disco(iso, "ps3") is None)
        halo = os.path.join(P, "XBOX360", "Halo 3 (Brazil) (En,Ja,Fr,De,Es,It,Pt,Zh,Ko).iso")
        if os.path.isfile(halo):
            confere("Xbox 360 de verdade: Title ID do Halo 3 = 4D5307E6",
                    capas_do_disco.title_id_do_xbox360(halo) == "4D5307E6", capas_do_disco.title_id_do_xbox360(halo))
        mkwii = os.path.join(P, "Wii", "Mario Kart Wii (USA) (En,Fr,Es).rvz")
        if os.path.isfile(mkwii):
            confere("Wii de verdade (.rvz): codigo RMCE01", capas_do_disco.id_do_disco_nintendo(mkwii) == "RMCE01")
        borderlands = os.path.join(P, "PS3", "Borderlands 2 (USA) (En,Fr,De,Es,It).iso")
        if os.path.isfile(borderlands):
            icone = capas_do_disco.icone_do_disco(borderlands, "ps3")
            confere("PS3 de verdade: o icone sai do .iso (PNG)", bool(icone) and icone.startswith(b"\x89PNG"))

        print("4. O indexador acha a capa")
        import indexador
        jogos = os.path.join(pasta, "jogos")
        sozinho = os.path.join(jogos, "pessoais", "PSP", "Jogo Sozinho")
        varios = os.path.join(jogos, "pessoais", "PSP", "Varios")
        for alvo in (sozinho, varios):
            os.makedirs(alvo)
        open(os.path.join(sozinho, "jogo sozinho.iso"), "wb").write(b"x")
        open(os.path.join(sozinho, "Cover.jpg"), "wb").write(b"\xff\xd8\xff" + bytes(10))
        for nome in ("um.iso", "dois.iso"):
            open(os.path.join(varios, nome), "wb").write(b"x")
        open(os.path.join(varios, "cover.png"), "wb").write(PNG)
        confere("Cover.jpg na pasta de um jogo sozinho vale",
                any(c.endswith("Cover.jpg") for c in indexador.capas_do_jogo(
                    os.path.join(sozinho, "jogo sozinho.iso"), sozinho, "jogo sozinho", sozinho_na_pasta=True)))
        confere("e a decisao 'sozinho' esta certa (pasta propria: sim; pasta da plataforma ou com 2 jogos: nao)",
                indexador.sozinho_na_pasta(sozinho, os.path.join(jogos, "pessoais"), "jogo sozinho.iso",
                                           ["jogo sozinho.iso", "Cover.jpg"])
                and not indexador.sozinho_na_pasta(varios, os.path.join(jogos, "pessoais"), "um.iso",
                                                   ["um.iso", "dois.iso", "cover.png"])
                and not indexador.sozinho_na_pasta(os.path.join(jogos, "pessoais"), os.path.join(jogos, "pessoais"),
                                                   "a.iso", ["a.iso"]))

        print("5. Servidor isolado: Buscar capas que faltam")
        import teste_servidor_que_cai as servidor_de_teste
        import tela_sem_janela
        copia = os.path.join(pasta, "isolado", "ARENA")
        os.makedirs(copia)
        servidor_de_teste.preparar_copia(copia)
        pasta_psp = os.path.join(copia, "jogos", "pessoais", "PSP")
        os.makedirs(pasta_psp, exist_ok=True)
        montar_iso(os.path.join(pasta_psp, "Jogo Inventado Pelo Teste.iso"), "PSP_GAME", PNG)
        porta = tela_sem_janela.porta_livre()
        processo = servidor_de_teste.subir(copia, porta, True, os.path.join(pasta, "sem-trava"))
        try:
            servidor_de_teste.esperar_servidor(porta)
            servidor_de_teste.pedir(porta, "POST", "/api/indexar", {}, espera=60)
            servidor_de_teste.pedir(porta, "POST", "/api/capas/buscar-faltando", {}, espera=20)
            situacao = {}
            for _ in range(240):
                time.sleep(0.5)
                situacao = servidor_de_teste.pedir(porta, "GET", "/api/capas/progresso")[1]
                if situacao and not situacao.get("rodando"):
                    break
            confere("a busca terminou e achou a capa do jogo de teste (icone do disco)",
                    situacao.get("rodando") is False and situacao.get("achados", 0) >= 1, situacao)
            catalogo = servidor_de_teste.pedir(porta, "GET", "/api/catalogo")[1]
            jogo = next((j for j in catalogo.get("jogos", []) if "Inventado" in j.get("titulo", "")), {})
            confere("a lista agora mostra a capa", bool(jogo.get("capas")), jogo.get("capas"))
        finally:
            servidor_de_teste.derrubar(processo)

        print("6. Com internet: PS2, Xbox 360 e GameCube de verdade")
        if not internet:
            print("  (sem internet agora: pulado)")
        else:
            capas_online.PASTA_MINIATURAS = os.path.join(pasta, "miniaturas")
            for console, arquivo, titulo, extensao in (
                    ("ps2", os.path.join(P, "PS2", "Crash Nitro Kart (USA).chd"), "Crash Nitro Kart", ".png"),
                    ("xbox360", halo, "Halo 3", ".jpg"),
                    ("gamecube", os.path.join(P, "GameCube", "MKDD 3-4 Grand Prix.iso"), "MKDD 3 4 Grand Prix", ".png")):
                if not os.path.isfile(arquivo):
                    print("  (sem %s: pulado)" % os.path.basename(arquivo))
                    continue
                base = os.path.splitext(os.path.basename(arquivo))[0]
                ok, fonte = capas_online.buscar_e_baixar(console, titulo, base, caminho_jogo=arquivo)
                salvo = os.path.join(capas_online.PASTA_MINIATURAS, console, "Named_Boxarts", titulo + extensao)
                confere("%s: capa de %s baixada (%s)" % (console, titulo, fonte or "banco do RetroArch"),
                        ok and os.path.isfile(salvo) and os.path.getsize(salvo) > 1024, (ok, fonte))
    finally:
        limpeza.apagar_pasta(pasta)

    print()
    if falhas:
        print("FALHOU: %d de %d" % (len(falhas), total[0]))
        return 1
    print("Capas: %d de %d certos." % (total[0], total[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
