# -*- coding: utf-8 -*-
r"""Qual parte da configuracao do ARENA faz o PCSX2 ficar em "Velocidade 0%"?

Achado 26/09/2026: com o PCSX2 respeitando a configuracao do ARENA, o Crash
Nitro Kart abre a janela e fica "Sem Imagem, Velocidade 0%". Parte de um
PCSX2.ini de base (argumento 1), aplica so as secoes pedidas do que o ARENA
escreveria, abre o jogo EM JANELA ~35 s e tira foto da tela (argumento 2).

Uso: servidor\python\python.exe testes\teste_pcsx2_bissecao.py <ini base> <foto.png> [secoes...]
     secoes: minimo pads gs hotkeys ui_ultra
"""
import os
import re
import shutil
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
import controles  # noqa: E402
import graficos  # noqa: E402

EXE = os.path.join(RAIZ, "emuladores", "PCSX2", "PCSX2", "pcsx2-qt.exe")
INI = os.path.join(os.path.dirname(EXE), "inis", "PCSX2.ini")
FOTO_PS1 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "foto_pcsx2_janela.ps1")


def secoes_do_arena():
    """O que o ARENA escreveria, separado por secao."""
    tmp = INI + ".arena-tmp"
    shutil.copy2(INI, tmp)
    cartoes = graficos.preparar_portatil_pcsx2(EXE)
    graficos.escrever_config_pcsx2(EXE, nota=4, nota_gpu=3, ultra=True, jogadores=4,
                                   controles_xinput=controles.controles_xinput(), cartoes=cartoes)
    texto = open(INI, encoding="utf-8").read()
    shutil.move(tmp, INI)
    secoes, atual = {}, None
    for linha in texto.splitlines():
        s = linha.strip()
        if s.startswith("[") and s.endswith("]"):
            atual = s[1:-1]
            secoes.setdefault(atual, {})
        elif atual and "=" in s:
            k, v = s.split("=", 1)
            secoes[atual][k.strip()] = v.strip()
    return secoes


def main():
    base, foto, pedidas = sys.argv[1], sys.argv[2], sys.argv[3:]
    shutil.copy2(base, INI)
    arena = secoes_do_arena()
    shutil.copy2(base, INI)
    texto = open(INI, encoding="utf-8").read()
    grupos = {
        "minimo": ["Folders", "Filenames", "MemoryCards"],
        "pastas": ["Folders"],
        "bios": ["Filenames"],
        "cartoes": ["MemoryCards"],
        "pads": ["Pad"] + ["Pad%d" % n for n in range(1, 9)] + ["InputSources"],
        "gs": ["EmuCore/GS"],
        "hotkeys": ["Hotkeys"],
        "ui_ultra": ["UI"],
    }
    texto = graficos._trocar_chaves_ini(texto, "UI", {"SettingsVersion": "1",
                                                      "SetupWizardIncomplete": "false"})
    for grupo in pedidas:
        for secao in grupos[grupo]:
            if secao in arena:
                texto = graficos._trocar_chaves_ini(texto, secao, arena[secao])
    texto = graficos._trocar_chaves_ini(texto, "Logging", {"EnableFileLogging": "true"})
    open(INI, "w", encoding="utf-8").write(texto)
    print("secoes aplicadas:", pedidas or ["(so versao e assistente)"])
    # pwsh, nao o powershell 5.1: este le o .ps1 sem BOM como ANSI e estraga
    # o "o" com acento de "Pedagogicos" no caminho do jogo.
    r = subprocess.run(["pwsh", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", FOTO_PS1,
                        "-Foto", foto, "-Espera", "35"], capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip())
    return 0


if __name__ == "__main__":
    sys.exit(main())
