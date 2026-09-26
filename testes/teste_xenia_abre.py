# -*- coding: utf-8 -*-
r"""O jogo de Xbox 360 chega a rodar no Xenia? (isolar travas por eliminacao)

Achado 26/09/2026: Left 4 Dead 2 mostrava "atualizacao disponivel" e
travava em tela preta; o registro dizia "Graphics device lost". Aqui abre o
jogo num dos Xenia da pasta, opcionalmente com '--gpu=...', espera, tira
foto da tela e resume o registro (placa perdida, rede, mensagens).

Uso: servidor\python\python.exe testes\teste_xenia_abre.py <parte do nome> <exe> <foto.png> [--gpu=vulkan ...]
     exe: xenia_canary.exe ou xenia_canary_netplay.exe
"""
import glob
import os
import subprocess
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA = os.path.join(RAIZ, "emuladores", "Xenia", "Xenia")
FOTO_PS1 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "foto_tela.ps1")
ESPERA = 70


def main():
    nome, exe, foto = sys.argv[1].lower(), sys.argv[2], sys.argv[3]
    extras = sys.argv[4:]
    jogo = [j for j in glob.glob(os.path.join(RAIZ, "jogos", "pessoais", "XBOX360", "*.iso"))
            if nome in os.path.basename(j).lower()][0]
    log = os.path.join(PASTA, "xenia.log")
    processo = subprocess.Popen([os.path.join(PASTA, exe)] + extras + [jogo], cwd=PASTA)
    time.sleep(ESPERA)
    subprocess.run(["pwsh", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", FOTO_PS1,
                    "-Foto", foto], capture_output=True, timeout=60)
    vivo = processo.poll() is None
    processo.kill()
    time.sleep(2)
    texto = open(log, encoding="utf-8", errors="ignore").read()
    print("rodando depois de %d s: %s" % (ESPERA, vivo))
    for marca in ("Graphics device lost", "Failed to create", "Cannot reach API server",
                  "XamShowMessageBoxUI", "D3D12", "Vulkan"):
        print("  %-28s %d" % (marca, texto.count(marca)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
