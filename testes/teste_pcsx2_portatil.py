# -*- coding: utf-8 -*-
r"""O PCSX2 usa a pasta do ARENA (modo portatil) e nao Documentos?

Achado 26/09/2026: sem portable.txt o PCSX2 lia Documentos\PCSX2 (OneDrive)
e ignorava tudo o que o ARENA escrevia. Aqui: prepara como o /api/jogar
(preparar_portatil_pcsx2 + escrever_config_pcsx2 com 4 jogadores), abre o
Crash Nitro Kart ~25 s e confere:
  - o registro do PCSX2 (logs\emulog.txt) nasceu DENTRO da pasta do ARENA;
  - o PCSX2.ini de Documentos nao foi tocado;
  - o registro mostra a BIOS e o jogo carregando (nao parou no assistente).

Uso: servidor\python\python.exe testes\teste_pcsx2_portatil.py
"""
import os
import subprocess
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import controles  # noqa: E402
import graficos  # noqa: E402
import jogos_de_teste  # noqa: E402

EXE = os.path.join(RAIZ, "emuladores", "PCSX2", "PCSX2", "pcsx2-qt.exe")
# Pelo ajudante (o professor reorganiza as pastas; o teste nao pode pular calado).
JOGO = jogos_de_teste.achar("PS2", "Crash Nitro Kart (USA).chd")


def main():
    if not JOGO or not os.path.isfile(EXE):
        print("FALHOU: sem o PCSX2 ou sem o Crash Nitro Kart (USA).chd em jogos\\pessoais\\PS2.")
        return 1
    documentos = os.path.join(os.path.expanduser("~"), "OneDrive", "Documents", "PCSX2", "inis", "PCSX2.ini")
    antes_doc = os.path.getmtime(documentos) if os.path.exists(documentos) else None
    log = os.path.join(os.path.dirname(EXE), "logs", "emulog.txt")
    antes_log = os.path.getmtime(log) if os.path.exists(log) else 0

    graficos.preparar_bios_pcsx2(EXE, os.path.join(RAIZ, "retroarch", "system"))
    cartoes = graficos.preparar_portatil_pcsx2(EXE)
    graficos.escrever_config_pcsx2(EXE, nota=3, nota_gpu=3, jogadores=4,
                                   controles_xinput=controles.controles_xinput(),
                                   cartoes=cartoes)
    dados = {"argumentos": ["-fullscreen", "{jogo}"]}   # os mesmos do consoles.json
    comando = graficos.comando_externo(EXE, dados, JOGO)
    print("Abrindo:", comando)
    processo = subprocess.Popen(comando, cwd=os.path.dirname(EXE))
    time.sleep(25)
    processo.kill()
    time.sleep(1)

    ok = True
    novo_log = os.path.exists(log) and os.path.getmtime(log) > antes_log
    print("Registro dentro da pasta do ARENA:", novo_log, log)
    ok &= novo_log
    if antes_doc is not None:
        intocado = os.path.getmtime(documentos) == antes_doc
        print("PCSX2.ini de Documentos intocado:", intocado)
        ok &= intocado
    if novo_log:
        texto = open(log, encoding="utf-8", errors="ignore").read()
        for chave in ("BIOS", "Multitap", "XInput", "SLUS", "Pad"):
            linhas = [l.strip()[:140] for l in texto.splitlines() if chave.lower() in l.lower()][:3]
            print("--", chave, "\n   " + "\n   ".join(linhas))
    print("Memory cards:", cartoes)
    print("\nRESULTADO:", "PASSOU" if ok else "FALHOU")
    return 0 if ok else 1


def main_devolvendo_o_ini():
    """Grava no PCSX2.ini de verdade (precisa: e' o PCSX2 da pasta que abre),
    mas devolve o original no fim. Achado da rodada da auditoria 3
    (07/10/2026): este teste deixava o PCSX2 do professor com 4 jogadores e a
    qualidade de nota 3 -- quem devolvia era a rodada, nao o teste."""
    ini = os.path.join(os.path.dirname(EXE), "inis", "PCSX2.ini")
    original = None
    if os.path.isfile(ini):
        with open(ini, "rb") as arquivo:
            original = arquivo.read()
    try:
        return main()
    finally:
        if original is not None:
            with open(ini + ".teste.tmp", "wb") as arquivo:
                arquivo.write(original)
            os.replace(ini + ".teste.tmp", ini)
            print("PCSX2.ini de verdade devolvido como estava antes do teste.")


if __name__ == "__main__":
    sys.exit(main_devolvendo_o_ini())
