# -*- coding: utf-8 -*-
r"""Abre CADA jogo do catalogo que roda pelo RetroArch, sozinho, e confere:

  1. ABRE: ~10 s com as opcoes do ARENA e uma foto da tela (--max-frames-ss).
     Foto com mais de 2 KB = mostrou imagem. Guarda os erros do registro
     (BIOS que falta, nucleo que falta).
  2. JOGAR JUNTO: hospedeiro + convidado de verdade em 127.0.0.1 (o nucleo
     que o /api/jogar usaria), onde o console permite.

Reaproveita teste_matriz_multitap (mesmas opcoes e mesmo criterio). Jogo de
emulador de fora (PCSX2, Dolphin, RPCS3, Xenia) fica de fora: testar com o
professor. Protege o retroarch.cfg real.

Saida: docs\abrir_todos_bruto.json e as fotos em <pasta temporaria>\fotos.

Uso:
    servidor\python\python.exe testes\teste_abrir_todos.py [pedaco do nome do console]
"""
import json
import os
import shutil
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import protege_cfg  # noqa: E402
import teste_matriz_multitap as base  # noqa: E402

RAIZ = base.RAIZ
indexador = base.arena.indexador


def porta_ocupada(porta=55435):
    """Alguem ja escuta na porta do Jogar Junto? (antes de o teste abrir o seu)"""
    import socket
    with socket.socket() as teste:
        teste.settimeout(0.5)
        return teste.connect_ex(("127.0.0.1", porta)) == 0


def main():
    filtro = sys.argv[1].lower() if len(sys.argv) > 1 else ""
    plataformas, _ = indexador.carregar_plataformas()
    resultado = indexador.indexar(forcar=True)
    jogos = resultado["jogos"] if isinstance(resultado, dict) else resultado
    trabalho = tempfile.mkdtemp(prefix="arena_abrir_todos_")
    fotos = os.path.join(trabalho, "fotos")
    os.makedirs(fotos)
    saida = []
    for n, jogo in enumerate(sorted(jogos, key=lambda j: (j["plataforma_nome"], j["titulo"]))):
        plataforma = plataformas.get(jogo["plataforma"], {})
        if filtro and filtro not in jogo["plataforma_nome"].lower():
            continue
        item = {"console": jogo["plataforma_nome"], "titulo": jogo["titulo"],
                "jogadores": jogo.get("jogadores_max")}
        if plataforma.get("externo") and base.arena.graficos.achar_externo(plataforma):
            item["situacao"] = "emulador de fora (%s): testar com o professor" % plataforma["externo"]["nome"]
            saida.append(item)
            print("%-45s %s" % (jogo["titulo"][:45], item["situacao"]))
            continue
        nucleo = plataforma.get("core", "").replace("_libretro.dll", "")
        if not os.path.isfile(os.path.join(RAIZ, "retroarch", "cores", nucleo + "_libretro.dll")):
            item["situacao"] = "falta o nucleo %s" % nucleo
            saida.append(item)
            print("%-45s %s" % (jogo["titulo"][:45], item["situacao"]))
            continue
        caminho = os.path.join(RAIZ, jogo["arquivo"])
        pasta = os.path.join(trabalho, "%03d" % n)
        item["abrir"] = base.abrir(jogo["plataforma_nome"], caminho, nucleo, pasta)
        # FBNeo mostra uma tela de erro (que da foto!) quando falta arquivo
        # do romset: isso nao e' "abriu".
        if any("is required" in erro for erro in item["abrir"]["erros"]):
            item["abrir"]["abre_e_mostra_imagem"] = False
        foto = os.path.join(pasta, "foto.png")
        if os.path.exists(foto):
            nome_foto = "%03d %s - %s.png" % (n, jogo["plataforma_nome"][:20], jogo["titulo"][:40])
            nome_foto = "".join(c for c in nome_foto if c not in '\\/:*?"<>|')
            shutil.copy2(foto, os.path.join(fotos, nome_foto))
            item["foto"] = nome_foto
        if plataforma.get("netplay") is False:
            item["jogar_junto"] = {"pulado": plataforma.get("netplay_motivo", "o nucleo recusa")}
        elif porta_ocupada():
            # Achado 25/09/2026: um RetroArch esquecido de rodada anterior
            # (Snes9x) ficou na 55435; os convidados de Mega Drive e ZX
            # entravam NELE e ouviam "nucleo diferente". Resultado enganoso.
            item["jogar_junto"] = {"erros": ["porta 55435 ocupada por outro programa: teste nao vale"]}
        elif item["abrir"]["abre_e_mostra_imagem"]:
            nucleo_junto = plataforma.get("core_netplay", plataforma.get("core", "")).replace("_libretro.dll", "")
            item["jogar_junto"] = base.jogar_junto(caminho, nucleo_junto, os.path.join(pasta, "junto"))
        abre = "abre" if item["abrir"]["abre_e_mostra_imagem"] else "NAO ABRE"
        junto = item.get("jogar_junto", {})
        junto_txt = ("conectou" if junto.get("conectou") else
                     ("pulado" if "pulado" in junto else ("NAO conectou" if junto else "-")))
        print("%-45s %-9s junto: %-12s %s" % (jogo["titulo"][:45], abre, junto_txt,
                                               "; ".join(item["abrir"]["erros"])[:120]))
        saida.append(item)
    destino = os.path.join(RAIZ, "docs", "abrir_todos_bruto.json")
    with open(destino, "w", encoding="utf-8") as arquivo:
        json.dump(saida, arquivo, ensure_ascii=False, indent=1)
    print("\nFotos: %s\nResultado: %s" % (fotos, destino))
    return 0


if __name__ == "__main__":
    sys.exit(protege_cfg.rodar(main))
