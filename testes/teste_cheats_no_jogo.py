# -*- coding: utf-8 -*-
r"""O cheat cadastrado pela tela do ARENA chega ao jogo? E a gaveta "Saves e
cheats" ve o estado salvo?

Achado da auditoria 3 (Fase 5, 09/10/2026): os cheats NUNCA funcionaram, por
dois defeitos juntos -- o ARENA gravava o .cht em retroarch\cheats\<console>\
(o RetroArch so procura em retroarch\cheats\<nucleo>\, com o nome do jogo
cortado no ultimo ponto) e com handler "1" (a busca de memoria do proprio
RetroArch, que ignora o codigo; o do emulador e' "0"). E a gaveta procurava
os estados na raiz de retroarch\states, mas o RetroArch grava numa subpasta
por nucleo: os espacos apareciam sempre "vazio".

Como confere, com o RetroArch de verdade e o Super Nintendo (Snes9x):
  1. cadastra um cheat pelas funcoes do ARENA (cheats.adicionar_cheat) que
     escreve 0x5A no fim da memoria do SNES (7FFF00, que o jogo quase nunca
     usa), numa pasta temporaria;
  2. abre o jogo com as opcoes que o ARENA grava (modo modesto: sem a
     resposta instantanea, o RetroArch atende os comandos de rede deste
     teste), salva o estado pelo comando SAVE_STATE e le a memoria do jogo
     DENTRO do estado (o bloco "RAM:" do Snes9x);
  3. confere no registro do RetroArch que ele carregou o arquivo do ARENA;
  4. confere que a gaveta (cheats.listar_estados) ve o estado salvo;
  5. depois que o RetroArch regrava o .cht ao fechar, o ARENA ainda le o
     codigo, ligado;
  6. para comparar, "como era": o .cht no lugar antigo e com handler 1 -- a
     memoria fica como o jogo deixou.
Nada do ARENA de verdade e' tocado: tudo numa pasta temporaria, e o
retroarch.cfg real e' protegido (protege_cfg).

Uso: servidor\python\python.exe testes\teste_cheats_no_jogo.py
"""
import glob
import os
import struct
import subprocess
import sys
import tempfile
import time
import zlib
from unittest import mock

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cheats  # noqa: E402
import limpeza  # noqa: E402
import protege_cfg  # noqa: E402
import teste_matriz_consoles as t  # noqa: E402

ENDERECO = 0x7FFF00
VALOR = 0x5A
falhas = []
total = [0]


def confere(nome, ok, detalhe=""):
    total[0] += 1
    print("  [%s] %s%s" % ("OK" if ok else "FALHOU", nome, (" -- " + detalhe) if detalhe and not ok else ""),
          flush=True)
    if not ok:
        falhas.append(nome)


def descomprimir(dados):
    """O estado do RetroArch comprimido: "#RZIPv" + versao + "#", tamanho do
    pedaco (4 bytes), tamanho total (8), e os pedacos zlib, cada um com o
    tamanho (4 bytes) na frente."""
    if not dados.startswith(b"#RZIPv"):
        return dados
    _pedaco, total_bytes = struct.unpack_from("<IQ", dados, 8)
    pos, saida = 20, bytearray()
    while pos < len(dados) and len(saida) < total_bytes:
        (tamanho,) = struct.unpack_from("<I", dados, pos)
        saida += zlib.decompress(dados[pos + 4:pos + 4 + tamanho])
        pos += 4 + tamanho
    return bytes(saida)


def byte_da_memoria(estado):
    with open(estado, "rb") as arquivo:
        dados = descomprimir(arquivo.read())
    marca = b"RAM:131072:"
    i = dados.find(marca)
    return None if i < 0 else dados[i + len(marca) + ENDERECO - 0x7E0000]


def jogar(jogo, plataforma, pasta, preparar):
    """Abre o jogo com as opcoes do ARENA; 'preparar(pastas)' poe o .cht.
    Devolve (byte da memoria, linhas do registro, pastas)."""
    os.makedirs(pasta)
    override, filtro, pastas = t.preparar_sessao(jogo, plataforma, True, pasta)
    preparar(pastas)
    linha = [t.RETROARCH, "-L", os.path.join(RAIZ, "retroarch", "cores", plataforma["core"]),
             "--appendconfig", override]
    if filtro:
        linha += ["--set-shader", filtro]
    linha.append(os.path.join(RAIZ, jogo["arquivo"]))
    valor = None
    processo = subprocess.Popen(linha, cwd=os.path.join(RAIZ, "retroarch"),
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        fim = time.monotonic() + t.ESPERA_ABRIR
        while time.monotonic() < fim and processo.poll() is None and not (t.fps_e_quadros(processo.pid) or (0, 0))[1]:
            time.sleep(0.25)
        time.sleep(4)
        t.comando("SAVE_STATE")
        time.sleep(3)
        estados = [e for e in glob.glob(os.path.join(pastas["PASTA_STATES"], "**", "*.state"), recursive=True)]
        if estados:
            valor = byte_da_memoria(max(estados, key=os.path.getmtime))
        t.comando("QUIT")
        try:
            processo.wait(timeout=15)
        except subprocess.TimeoutExpired:
            pass
    finally:
        if processo.poll() is None:
            processo.kill()
    registro = []
    for caminho in glob.glob(os.path.join(pasta, "**", "*.log"), recursive=True):
        with open(caminho, encoding="utf-8", errors="replace") as arquivo:
            registro += [l.strip() for l in arquivo if "[Cheats]" in l]
    return valor, registro, pastas


def main():
    escolhidos = t.escolher_jogos("super nintendo")
    if not escolhidos:
        print("FALHOU: nenhum jogo de Super Nintendo na pasta jogos\\pessoais (o teste precisa de um).")
        return 1
    jogo, plataforma = escolhidos[0]
    nucleo = cheats.nome_do_nucleo(plataforma["core"], os.path.join(RAIZ, "retroarch", "info"))
    print("Jogo: %s | nucleo: %s" % (os.path.basename(jogo["arquivo"]), nucleo))
    trabalho = tempfile.mkdtemp(prefix="arena_cheats_no_jogo_")
    try:
        # --- Como o ARENA grava agora ---------------------------------------
        def pelo_arena(pastas):
            with mock.patch.object(cheats, "PASTA_CHEATS", pastas["PASTA_CHEATS"]):
                _lista, erro = cheats.adicionar_cheat(jogo, "Teste do ARENA", "7FFF00:%02X" % VALOR, True, nucleo)
            assert erro is None, erro

        valor, registro, pastas = jogar(jogo, plataforma, os.path.join(trabalho, "agora"), pelo_arena)
        print("Agora: memoria 7FFF00 = %s" % (None if valor is None else "0x%02X" % valor))
        with mock.patch.object(cheats, "PASTA_CHEATS", pastas["PASTA_CHEATS"]):
            esperado = cheats.caminho_cht(jogo, nucleo)
            confere("o RetroArch carregou o arquivo que o ARENA gravou",
                    any("Load game-specific cheatfile" in l and os.path.basename(esperado) in l for l in registro),
                    " | ".join(registro) or "nada no registro")
            confere("o codigo mudou a memoria do jogo (0x%02X em 7FFF00)" % VALOR, valor == VALOR,
                    "lido: %s" % valor)
            lidos = cheats.ler_cheats(jogo, nucleo)
            confere("depois que o RetroArch regravou o .cht, a gaveta ainda le o codigo, ligado",
                    len(lidos) == 1 and lidos[0]["ligado"] and lidos[0]["codigo"].replace(":", "").upper()
                    == "7FFF00%02X" % VALOR, str(lidos))
        with mock.patch.object(cheats, "PASTA_STATES", pastas["PASTA_STATES"]):
            agora = [e["espaco"] for e in cheats.listar_estados(jogo, nucleo) if e["existe"]]
            antes = [e["espaco"] for e in cheats.listar_estados(jogo) if e["existe"]]
        confere("a gaveta ve o estado salvo (espaco 0) na pasta do nucleo", agora == [0], str(agora))
        confere("(como era: olhando so a raiz, a gaveta nao via nada)", antes == [], str(antes))

        # --- Como era ate a auditoria 3, para comparar ------------------------
        def como_era(pastas):
            with mock.patch.object(cheats, "PASTA_CHEATS", pastas["PASTA_CHEATS"]):
                caminho = cheats.caminho_cht_antigo(jogo)
            os.makedirs(os.path.dirname(caminho), exist_ok=True)
            with open(caminho, "w", encoding="utf-8") as arquivo:
                arquivo.write('cheats = 1\n\ncheat0_desc = "Como era"\ncheat0_code = "7FFF00:%02X"\n'
                              'cheat0_enable = true\ncheat0_handler = "1"\n' % VALOR)

        valor, registro, _ = jogar(jogo, plataforma, os.path.join(trabalho, "antes"), como_era)
        print("Como era: memoria 7FFF00 = %s" % (None if valor is None else "0x%02X" % valor))
        confere("(como era: o cheat nao chegava ao jogo)", valor is not None and valor != VALOR,
                "lido: %s" % valor)
    finally:
        limpeza.apagar_pasta(trabalho)

    print()
    if falhas:
        print("FALHOU: %d de %d" % (len(falhas), total[0]))
        return 1
    print("Cheats no jogo: %d de %d certos." % (total[0], total[0]))
    return 0


if __name__ == "__main__":
    sys.exit(protege_cfg.rodar(main))
