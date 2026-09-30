# -*- coding: utf-8 -*-
r"""Neo Geo: o que o RetroArch/FBNeo diz da BIOS ao abrir um jogo.

Abre o KOF97 no FBNeo por ~5 s (--max-frames), com as mesmas pastas do
ARENA, e mostra do registro as linhas sobre BIOS, arquivos que faltam ou
com CRC errado, e se o jogo carregou. Protege o retroarch.cfg real.

Uso:
    servidor\python\python.exe testes\neogeo_bios_registro.py [nome.zip]
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
NUCLEO = os.path.join(RAIZ, "retroarch", "cores", "fbneo_libretro.dll")


def main():
    nome = sys.argv[1] if len(sys.argv) > 1 else "kof97.zip"
    jogo = os.path.join(RAIZ, "jogos", "pessoais", "Neo Geo", nome)
    pasta = tempfile.mkdtemp(prefix="arena_neogeo_")
    extra = os.path.join(pasta, "x.cfg")
    log = os.path.join(pasta, "ra.log")
    open(extra, "w", encoding="utf-8").write("\n".join([
        'config_save_on_exit = "false"', 'audio_enable = "false"',
        'system_directory = "%s"' % os.path.join(RAIZ, "retroarch", "system"),
        'savefile_directory = "%s"' % pasta, 'savestate_directory = "%s"' % pasta]) + "\n")
    subprocess.run([RETROARCH, "-L", NUCLEO, "--appendconfig", extra, "--verbose",
                    "--log-file", log, "--max-frames", "300", jogo],
                   cwd=os.path.dirname(RETROARCH), timeout=180)
    texto = open(log, encoding="utf-8", errors="replace").read() if os.path.exists(log) else ""
    for linha in texto.splitlines():
        if re.search(r"(?i)bios|neogeo|crc|missing|not found|faltando|\.sp1|sm1|sfix|000-lo|"
                     r"loaded content|conteúdo carregado|failed|falha|erro|error", linha):
            print(linha.strip()[:180])
    print("\n(registro completo tinha %d linhas)" % len(texto.splitlines()))
    return 0


if __name__ == "__main__":
    sys.exit(protege_cfg.rodar(main))
