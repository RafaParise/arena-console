# -*- coding: utf-8 -*-
r"""Quais controles o RetroArch enxerga agora, e em qual porta.

Abre o Super Mario Kart (SNES) por ~2 s com 8 portas liberadas e le o
registro do RetroArch: nome de cada controle e a porta em que ele entrou.
Nao aperta botao nenhum; so confirma DETECCAO. Que o botao mexe o
personagem, so uma pessoa apertando confirma (roteiro da Fase E).

Uso:
    servidor\python\python.exe testes\controles_detectados.py
"""
import os
import re
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import protege_cfg  # noqa: E402

RETROARCH = os.path.join(RAIZ, "retroarch", "retroarch.exe")
NUCLEO = os.path.join(RAIZ, "retroarch", "cores", "snes9x_libretro.dll")
JOGO = os.path.join(RAIZ, "jogos", "pessoais", "Super Nintendo", "Super Mario Kart (USA).sfc")


def main():
    pasta = tempfile.mkdtemp(prefix="arena_controles_")
    extra = os.path.join(pasta, "extra.cfg")
    log = os.path.join(pasta, "ra.log")
    open(extra, "w", encoding="utf-8").write("\n".join([
        'config_save_on_exit = "false"', 'network_cmd_enable = "false"',
        'input_max_users = "8"', 'audio_enable = "false"',
        'joypad_autoconfig_dir = "%s"' % os.path.join(RAIZ, "retroarch", "autoconfig"),
        'savefile_directory = "%s"' % pasta, 'savestate_directory = "%s"' % pasta]) + "\n")
    subprocess.run([RETROARCH, "-L", NUCLEO, "--appendconfig", extra, "--verbose",
                    "--log-file", log, "--max-frames", "120", JOGO],
                   cwd=os.path.dirname(RETROARCH), timeout=120)
    texto = open(log, encoding="utf-8", errors="replace").read() if os.path.exists(log) else ""
    achados = []
    for linha in texto.splitlines():
        if re.search(r"autoconf|joypad|controller|gamepad|port \d", linha, re.I) and \
                not re.search(r"directory|dir\b", linha, re.I):
            achados.append(linha.strip())
    for linha in achados[:40]:
        print(linha[:170])
    print("\n%d linha(s) sobre controles no registro." % len(achados))
    return 0


if __name__ == "__main__":
    sys.exit(protege_cfg.rodar(main))
