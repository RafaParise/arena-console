# -*- coding: utf-8 -*-
r"""O Dolphin liga um codigo por jogo pelo User\GameSettings\<ID>.ini? (11/11/2026)

Nenhum disco do PC do Rafael tem o codigo de 60 quadros, entao a prova usa o mecanismo com um codigo que o F-Zero GX
tem no Sys ("$All Vehicles Unlocked", Action Replay): o ARENA escreve o .ini do jogo do mesmo jeito que faria para o
"$60fps", liga o registro do Dolphin para as trapacas, abre o jogo uns 40 s e le o registro. No fim, tira o que pos
(protege_cfg devolve a configuracao do Dolphin).

Uso: servidor\python\python.exe testes\teste_60_dolphin.py
"""
import os
import subprocess
import sys
import tempfile
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
import limpeza  # noqa: E402
import protege_cfg  # noqa: E402
import quadros_dolphin  # noqa: E402

DOLPHIN = os.path.join(RAIZ, "emuladores", "Dolphin", "Dolphin-x64")
EXE = os.path.join(DOLPHIN, "Dolphin.exe")
JOGO = os.path.join(RAIZ, "jogos", "pessoais", "GameCube", "F-Zero GX (USA).rvz")
LOGGER = os.path.join(DOLPHIN, "User", "Config", "Logger.ini")
REGISTRO = os.path.join(DOLPHIN, "User", "Logs", "dolphin.log")
FALHAS = []


def confere(nome, ok, detalhe=None):
    print("  %-6s %s%s" % ("ok" if ok else "FALHOU", nome, (" (%s)" % (detalhe,)) if detalhe else ""), flush=True)
    if not ok:
        FALHAS.append(nome)


def main():
    if not (os.path.isfile(EXE) and os.path.isfile(JOGO)):
        print("Falta o Dolphin ou o F-Zero GX (USA).rvz nesta maquina.")
        return 1
    dados = tempfile.mkdtemp(prefix="arena_60_dolphin_")
    lido = quadros_dolphin.ler_id(JOGO)
    confere("ID lido do .rvz", lido == ("GFZE01", 0), lido)
    jogo = lido[0] if lido else "GFZE01"
    # O codigo de prova: um Action Replay que o Sys tem para este jogo.
    secoes = quadros_dolphin.codigos(quadros_dolphin._ler(quadros_dolphin.arquivos_do_jogo(DOLPHIN, jogo)[0]))
    codigo = secoes.get("ActionReplay", [None])[0]
    confere("o Sys tem um codigo de prova", bool(codigo), codigo)
    if not codigo:
        return 1
    ini = os.path.join(DOLPHIN, "User", "GameSettings", jogo + ".ini")
    existia = os.path.isfile(ini)
    antes = quadros_dolphin._ler(ini)
    blocos = quadros_dolphin._por_na_secao(quadros_dolphin._secoes(antes), "Core", "EnableCheats = True")
    blocos = quadros_dolphin._por_na_secao(blocos, "ActionReplay_Enabled", codigo)
    quadros_dolphin._gravar(ini, quadros_dolphin._montar(blocos))
    logger_antes = quadros_dolphin._ler(LOGGER)
    quadros_dolphin._gravar(LOGGER, "[Options]\nWriteToFile = True\nVerbosity = 4\n\n[Logs]\nActionReplay = True\n"
                                    "Core = True\nBoot = True\n")
    if os.path.isfile(REGISTRO):
        os.remove(REGISTRO)
    processo = subprocess.Popen([EXE, "-b", "-e", JOGO], cwd=DOLPHIN)
    try:
        time.sleep(40)
    finally:
        processo.terminate()
        try:
            processo.wait(20)
        except subprocess.TimeoutExpired:
            processo.kill()
        if existia:
            quadros_dolphin._gravar(ini, antes)
        else:
            try:
                os.remove(ini)
            except OSError:
                pass
        if logger_antes:
            quadros_dolphin._gravar(LOGGER, logger_antes)
        else:
            try:
                os.remove(LOGGER)
            except OSError:
                pass
    registro = quadros_dolphin._ler(REGISTRO)
    linhas = [l for l in registro.splitlines() if "actionreplay" in l.lower() or "cheat" in l.lower() or "code" in l.lower()]
    for l in linhas[:8]:
        print("   ", l[:150])
    confere("o Dolphin abriu o jogo (registro)", bool(registro))
    confere("o Dolphin leu o codigo ligado pelo .ini do jogo",
            any(codigo[1:].lower() in l.lower() or "actionreplay" in l.lower() for l in linhas))
    limpeza.apagar_pasta(dados)
    print("RESULTADO: %s" % ("tudo certo" if not FALHAS else "falhou: " + ", ".join(FALHAS)))
    return 1 if FALHAS else 0


if __name__ == "__main__":
    sys.exit(protege_cfg.rodar(main, emuladores=True))
