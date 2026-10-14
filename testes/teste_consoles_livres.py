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
import struct
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
import ponte_sem_acento  # noqa: E402
import protege_cfg  # noqa: E402
import teste_matriz_multitap as base  # noqa: E402
from gravar_fundo_gif import ler_png  # noqa: E402

PASTA_JOGOS = os.path.join(AQUI, "jogos_livres")
RETROARCH = os.path.join(RAIZ, "retroarch", "retroarch.exe")


def disquete_st(destino, programas):
    """Um disquete de Atari ST (720 KB, FAT12) com os programas na pasta AUTO:
    o TOS (aqui, o EmuTOS) roda sozinho o que esta nela, ao ligar. O setor de
    boot nao e' executavel (a soma dele nao da 0x1234)."""
    bps, spc, reservados, fats, entradas, total, spf, spt, lados = 512, 2, 1, 2, 112, 1440, 3, 9, 2
    imagem = bytearray(total * bps)
    struct.pack_into("<HBHBHHBHHHH", imagem, 11, bps, spc, reservados, fats, entradas, total, 0xF9,
                     spf, spt, lados, 0)
    imagem[0:2] = b"\x60\x38"
    imagem[2:8] = b"ARENA "
    tamanho_cluster = bps * spc
    inicio_dados = (reservados + fats * spf + entradas * 32 // bps) * bps
    tabela = {0: 0xFF9, 1: 0xFFF}
    proximo = [2]

    def alocar(quantos):
        primeiro = proximo[0]
        for i in range(quantos):
            tabela[primeiro + i] = primeiro + i + 1 if i < quantos - 1 else 0xFFF
        proximo[0] += quantos
        return primeiro

    def gravar(cluster, dados):
        posicao = inicio_dados + (cluster - 2) * tamanho_cluster
        imagem[posicao:posicao + len(dados)] = dados

    def entrada(nome, extensao, atributo, cluster, tamanho):
        bloco = bytearray(32)
        bloco[0:8] = nome.ljust(8).encode("ascii")
        bloco[8:11] = extensao.ljust(3).encode("ascii")
        bloco[11] = atributo
        struct.pack_into("<HHHI", bloco, 22, 0, 0x5A21, cluster, tamanho)
        return bytes(bloco)

    auto = alocar(1)
    pasta = bytearray(tamanho_cluster)
    pasta[0:32] = entrada(".", "", 0x10, auto, 0)
    pasta[32:64] = entrada("..", "", 0x10, 0, 0)
    for i, caminho in enumerate(programas):
        with open(caminho, "rb") as arquivo:
            dados = arquivo.read()
        quantos = -(-len(dados) // tamanho_cluster)
        primeiro = alocar(quantos)
        for k in range(quantos):
            gravar(primeiro + k, dados[k * tamanho_cluster:(k + 1) * tamanho_cluster])
        nome, extensao = os.path.splitext(os.path.basename(caminho).upper())
        pasta[64 + 32 * i:96 + 32 * i] = entrada(nome, extensao[1:], 0x20, primeiro, len(dados))
    gravar(auto, pasta)
    raiz = (reservados + fats * spf) * bps
    imagem[raiz:raiz + 32] = entrada("AUTO", "", 0x10, auto, 0)
    fat = bytearray(spf * bps)
    for c in range(0, max(tabela) + 2, 2):
        a, b = tabela.get(c, 0), tabela.get(c + 1, 0)
        fat[c * 3 // 2:c * 3 // 2 + 3] = bytes([a & 0xFF, ((a >> 8) & 0x0F) | ((b & 0x0F) << 4), (b >> 4) & 0xFF])
    for k in range(fats):
        posicao = (reservados + k * spf) * bps
        imagem[posicao:posicao + len(fat)] = fat
    with open(destino, "wb") as arquivo:
        arquivo.write(imagem)


# O que cada console precisa a mais: quantos quadros rodar antes da foto, o
# que o registro tem que dizer e, quando o jogo livre nao e' o arquivo que o
# nucleo abre, como montar esse arquivo.
POR_CONSOLE = {
    "msx": {"quadros": 900, "registro": r"falling back to 'MSX2\+ - C-BIOS'"},
    "atarist": {"quadros": 1500, "montar": (".st", lambda destino, origem: disquete_st(destino, [origem]))},
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
    """Roda o jogo e devolve (foto, texto do registro, travou, usou a ponte).
    O nucleo que nao abre caminho com acento (o Hatari) vai pela MESMA ponte
    que o ARENA usa (servidor\\ponte_sem_acento.py)."""
    os.makedirs(pasta)
    cfg = base.config_base(pasta, {})
    opcoes = {"system_directory": sistema}
    jogo_do_nucleo, devolver = jogo, None
    ponte = ponte_sem_acento.precisa(nucleo, sistema, jogo)
    if ponte:
        jogo_do_nucleo, opcoes_da_ponte, devolver = ponte_sem_acento.preparar(nucleo, sistema, jogo)
        opcoes.update(opcoes_da_ponte)
    # A pasta system so com as BIOS livres (o --appendconfig aceita varios
    # arquivos separados por "|"; o ultimo vale).
    extra = os.path.join(pasta, "system.cfg")
    with open(extra, "w", encoding="utf-8") as arquivo:
        arquivo.write("".join('%s = "%s"\n' % par for par in sorted(opcoes.items())))
    foto = os.path.join(pasta, "foto.png")
    registro = os.path.join(pasta, "ra.log")
    try:
        subprocess.run([RETROARCH, "-L", os.path.join(RAIZ, "retroarch", "cores", nucleo),
                        "--appendconfig", cfg + "|" + extra, "--verbose", "--log-file", registro,
                        "--max-frames=%d" % quadros, "--max-frames-ss", "--max-frames-ss-path=" + foto,
                        jogo_do_nucleo],
                       cwd=os.path.dirname(RETROARCH), timeout=150,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        travou = False
    except subprocess.TimeoutExpired:
        travou = True
    if devolver:
        devolver()          # como o ARENA faz quando o jogo fecha: a pasta da ponte some
    texto = open(registro, encoding="utf-8", errors="ignore").read() if os.path.exists(registro) else ""
    return foto, texto, travou, ponte


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
                origem = os.path.join(PASTA_JOGOS, *item["origem"].split("/"))
                if regras.get("montar"):
                    extensao, montar = regras["montar"]
                    jogo = os.path.join(trabalho, os.path.splitext(os.path.basename(origem))[0].lower() + extensao)
                    montar(jogo, origem)
                else:
                    jogo = os.path.join(trabalho, os.path.basename(origem))
                    shutil.copyfile(origem, jogo)
                foto, texto, travou, ponte = abrir(jogo, plataforma["core"], os.path.join(trabalho, "rodada"),
                                                   sistema, regras.get("quadros", 600))
                ok, detalhe = imagem_de_verdade(foto)
                if os.path.isfile(foto):
                    shutil.copyfile(foto, os.path.join(fotos, "%s - %s.png" % (item["console"], rotulo)))
                print("   %-17s imagem: %-3s (%s)%s%s" % (rotulo, "sim" if ok else "NAO", detalhe,
                                                         " TRAVOU" if travou else "",
                                                         " [pela ponte sem acento]" if ponte else ""))
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
