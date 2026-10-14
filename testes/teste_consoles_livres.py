# -*- coding: utf-8 -*-
r"""Consoles livres: cada jogo de testes\jogos_livres abre no nucleo de
verdade com SO as BIOS livres do ARENA (servidor\bios_livres) na pasta
system -- nenhuma BIOS das empresas.

Pedido do Rafael (12/10/2026): todos os consoles possiveis, "integrar
emuladores sem precisar baixar BIOS". Para cada jogo da lista.json:
  1. ABRE: o RetroArch roda alguns segundos com as opcoes do ARENA e tira a
     foto da tela (--max-frames-ss). A foto tem que ter imagem de verdade:
     mais de uma cor, e a cor mais comum cobrindo menos de 98% da tela (o
     tamanho do arquivo nao serve: a tela do CHIP-8 tem 128x64 pontos).
  2. O REGISTRO prova o caminho livre, quando o console tem um (no MSX:
     "falling back to 'MSX2+ - C-BIOS'").
  3. COM ACENTO: o mesmo jogo, com a pasta system e o jogo numa pasta com
     "ó" no nome (o ARENA do Rafael mora em "...Pedagógicos\...").
  4. Com --junto: hospedeiro e convidado de verdade em 127.0.0.1 (o Jogar
     Junto), para conferir o que o consoles.json diz do console.

Uso:
    servidor\python\python.exe testes\teste_consoles_livres.py [pedaco do console] [--junto]
"""
import collections
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
sys.path.insert(0, os.path.join(RAIZ, "ferramentas"))
import bios  # noqa: E402
import limpeza  # noqa: E402
import protege_cfg  # noqa: E402
import teste_matriz_multitap as base  # noqa: E402
from gravar_fundo_gif import ler_png  # noqa: E402

PASTA_JOGOS = os.path.join(AQUI, "jogos_livres")
RETROARCH = os.path.join(RAIZ, "retroarch", "retroarch.exe")

# O que cada console precisa a mais: quantos quadros rodar antes da foto e o
# que o registro tem que dizer.
POR_CONSOLE = {
    "msx": {"quadros": 900, "registro": r"falling back to 'MSX2\+ - C-BIOS'"},
}


def plataformas():
    with open(os.path.join(RAIZ, "servidor", "consoles.json"), encoding="utf-8") as arquivo:
        return {p["id"]: p for p in json.load(arquivo)["plataformas"]}


def imagem_de_verdade(foto):
    """(sim/nao, detalhe): a foto tem mais de uma cor e nenhuma cobre 98%?"""
    if not os.path.isfile(foto):
        return False, "sem foto"
    with open(foto, "rb") as arquivo:
        largura, altura, pontos = ler_png(arquivo.read())
    cores = collections.Counter(p[:3] for p in pontos)
    maior = cores.most_common(1)[0][1] / float(len(pontos))
    return len(cores) > 1 and maior < 0.98, "%dx%d, %d cores, a mais comum em %.0f%%" % (
        largura, altura, len(cores), maior * 100)


def abrir(jogo, nucleo, pasta, sistema, quadros):
    """Roda o jogo e devolve (foto, texto do registro, travou)."""
    os.makedirs(pasta)
    cfg = base.config_base(pasta, {})
    # A pasta system so com as BIOS livres (o --appendconfig aceita varios
    # arquivos separados por "|"; o ultimo vale).
    extra = os.path.join(pasta, "system.cfg")
    with open(extra, "w", encoding="utf-8") as arquivo:
        arquivo.write('system_directory = "%s"\n' % sistema)
    foto = os.path.join(pasta, "foto.png")
    registro = os.path.join(pasta, "ra.log")
    try:
        subprocess.run([RETROARCH, "-L", os.path.join(RAIZ, "retroarch", "cores", nucleo),
                        "--appendconfig", cfg + "|" + extra, "--verbose", "--log-file", registro,
                        "--max-frames=%d" % quadros, "--max-frames-ss", "--max-frames-ss-path=" + foto, jogo],
                       cwd=os.path.dirname(RETROARCH), timeout=150,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        travou = False
    except subprocess.TimeoutExpired:
        travou = True
    texto = open(registro, encoding="utf-8", errors="ignore").read() if os.path.exists(registro) else ""
    return foto, texto, travou


def jogar_junto(jogo, nucleo, pasta, sistema):
    """O Jogar Junto de verdade (teste_matriz_multitap), com a pasta system
    das livres em cada um dos dois RetroArch."""
    original = base.config_base

    def com_sistema(sub, extras):
        # Troca a linha (nao acrescenta): com a chave repetida no mesmo
        # arquivo, o RetroArch fica com a PRIMEIRA (visto em 14/10/2026).
        cfg = original(sub, extras)
        with open(cfg, encoding="utf-8") as arquivo:
            linhas = [l for l in arquivo.read().splitlines() if not l.startswith("system_directory ")]
        with open(cfg, "w", encoding="utf-8") as arquivo:
            arquivo.write("\n".join(linhas + ['system_directory = "%s"' % sistema]) + "\n")
        return cfg

    base.config_base = com_sistema
    try:
        return base.jogar_junto(jogo, nucleo.replace("_libretro.dll", ""), pasta)
    finally:
        base.config_base = original


def main():
    filtro = " ".join(a for a in sys.argv[1:] if not a.startswith("--")).lower()
    junto = "--junto" in sys.argv
    with open(os.path.join(PASTA_JOGOS, "lista.json"), encoding="utf-8") as arquivo:
        jogos = json.load(arquivo)["arquivos"]
    todas = plataformas()
    falhas = []
    fotos = tempfile.mkdtemp(prefix="arena_livres_fotos_")
    for item in jogos:
        if filtro and filtro not in item["console"] and filtro not in item["jogo"].lower():
            continue
        plataforma = todas.get(item["console"])
        if not plataforma:
            falhas.append("%s: console %s nao esta no consoles.json" % (item["jogo"], item["console"]))
            continue
        regras = POR_CONSOLE.get(item["console"], {})
        print("== %s (%s, %s)" % (plataforma["nome"], item["jogo"], plataforma["core"]))
        for rotulo, prefixo in (("pasta comum", "arena_livres_"), ("pasta com acento", "arena_livres_Pedagógicos_")):
            trabalho = tempfile.mkdtemp(prefix=prefixo)
            try:
                sistema = os.path.join(trabalho, "system")
                os.makedirs(sistema)
                bios.instalar_livres(sistema)
                jogo = os.path.join(trabalho, os.path.basename(item["origem"]))
                shutil.copyfile(os.path.join(PASTA_JOGOS, *item["origem"].split("/")), jogo)
                foto, texto, travou = abrir(jogo, plataforma["core"], os.path.join(trabalho, "rodada"),
                                            sistema, regras.get("quadros", 600))
                ok, detalhe = imagem_de_verdade(foto)
                if os.path.isfile(foto):
                    shutil.copyfile(foto, os.path.join(fotos, "%s - %s.png" % (item["console"], rotulo)))
                print("   %-17s imagem: %-3s (%s)%s" % (rotulo, "sim" if ok else "NAO", detalhe,
                                                       " TRAVOU" if travou else ""))
                if not ok or travou:
                    falhas.append("%s, %s: sem imagem (%s)" % (plataforma["nome"], rotulo, detalhe))
                if regras.get("registro"):
                    achou = bool(re.search(regras["registro"], texto))
                    print("   %-17s registro: %s" % ("", "confere" if achou else "NAO confere"))
                    if not achou:
                        falhas.append("%s, %s: o registro nao diz %r" % (plataforma["nome"], rotulo,
                                                                        regras["registro"]))
                if junto and rotulo == "pasta comum":
                    resultado = jogar_junto(jogo, plataforma["core"], os.path.join(trabalho, "junto"), sistema)
                    print("   %-17s Jogar Junto: %s %s" % ("", "conectou" if resultado.get("conectou") else
                                                          "NAO conectou", resultado.get("recusa_do_nucleo", "")))
                    if bool(resultado.get("conectou")) != plataforma.get("netplay", True):
                        falhas.append("%s: o consoles.json diz netplay=%s, mas o Jogar Junto %s" % (
                            plataforma["nome"], plataforma.get("netplay", True),
                            "conectou" if resultado.get("conectou") else "nao conectou"))
            finally:
                time.sleep(1)
                limpeza.apagar_pasta(trabalho)
    print("\nFotos: %s" % fotos)
    if falhas:
        print("\nFALHAS:\n  " + "\n  ".join(falhas))
        return 1
    print("\nTudo certo.")
    return 0


if __name__ == "__main__":
    sys.exit(protege_cfg.rodar(main))
