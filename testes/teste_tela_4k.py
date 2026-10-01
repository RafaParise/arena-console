# -*- coding: utf-8 -*-
r"""Degrau "tela 4K": com placa dedicada e tela de 4K, os 3D leves sobem.

Pedido do Rafael (01/10/2026): graficos em 4K. Antes, na melhor placa, o PS1
parava em 6x (1440p), o PSP em 1920x1088 e o Dreamcast em 1920x1440 -- e o
N64, na placa dedicada, ia para o parallel-rdp em 1x (320x240). Agora
(graficos.json -> tela_4k), so com placa DEDICADA e tela de 2.000+ linhas:
PS1 9x, PSP 2880x1632, Dreamcast 2880x2160, N64 parallel-rdp 2x.

  1. logica: 4K + dedicada sobe; 1080p, placa integrada, "Grafico igual ao
     console original" e chamada sem nota da placa NAO sobem;
  2. hardware.altura_da_tela responde um numero de tela de verdade;
  3. RetroArch de verdade abre um jogo de cada console com os valores 4K:
     o registro mostra o nucleo lendo o valor novo, e o jogo mostra imagem
     (prova que o nucleo ACEITA o valor -- se a placa aguenta, so numa placa
     dedicada de verdade).

Uso: servidor\python\python.exe testes\teste_tela_4k.py [--sem-retroarch]
"""
import os
import re
import subprocess
import sys
import tempfile
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import limpeza  # noqa: E402
import protege_cfg  # noqa: E402
import teste_matriz_multitap as base  # noqa: E402

RAIZ = base.RAIZ
graficos = base.graficos
hardware = base.arena.hardware
P = os.path.join(RAIZ, "jogos", "pessoais")

ESPERADO_4K = {"swanstation_GPU_ResolutionScale": "9", "ppsspp_internal_resolution": "2880x1632",
               "reicast_internal_resolution": "2880x2160", "mupen64plus-parallel-rdp-upscaling": "2x"}
JOGOS = [  # (console, arquivo, nucleo, chave conferida no registro)
    ("PS1", os.path.join(P, "PS1", "Crash Bandicoot (USA).chd"), "swanstation", "swanstation_GPU_ResolutionScale"),
    ("PSP", os.path.join(P, "PSP", "Burnout Legends (Europe) (En,Fr,De,Es,It,Nl) (v2.00).iso"), "ppsspp",
     "ppsspp_internal_resolution"),
    ("Dreamcast", os.path.join(P, "Dreamcast", "Marvel vs. Capcom 2 - New Age of Heroes (Europe)",
                               "Marvel vs. Capcom 2 - New Age of Heroes (Europe).cue"), "flycast",
     "reicast_internal_resolution"),
    ("Nintendo 64", os.path.join(P, "Nintendo 64", "GoldenEye 007 (USA).z64"), "mupen64plus_next",
     "mupen64plus-parallel-rdp-upscaling"),
]


def opcoes_geradas(pasta, **kwargs):
    """Gera o retroarch-core-options.cfg numa pasta do teste e le de volta."""
    arquivo = os.path.join(pasta, "opcoes_%d.cfg" % len(os.listdir(pasta)))
    original = graficos.ARQUIVO_OPCOES_CORE
    graficos.ARQUIVO_OPCOES_CORE = arquivo
    try:
        graficos.gravar_opcoes_dos_nucleos(**kwargs)
    finally:
        graficos.ARQUIVO_OPCOES_CORE = original
    return dict(re.findall(r'^(\S+) = "(.*)"$', open(arquivo, encoding="utf-8").read(), re.M)), arquivo


def main():
    falhas, total = [], [0]

    def confere(nome, ok, detalhe=""):
        total[0] += 1
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, "" if ok else detalhe))
        if not ok:
            falhas.append(nome)

    pasta = tempfile.mkdtemp(prefix="arena_tela_4k_")
    try:
        print("1. logica")
        vale, _ = opcoes_geradas(pasta, nota=5, nota_gpu=5, altura_tela=2160)
        confere("4K + placa dedicada: os 4 consoles sobem", all(vale.get(c) == v for c, v in ESPERADO_4K.items()),
                {c: vale.get(c) for c in ESPERADO_4K})
        confere("4K + dedicada: o N64 continua no parallel-rdp (Mario Kart 64)",
                vale.get("mupen64plus-rdp-plugin") == "parallel", vale.get("mupen64plus-rdp-plugin"))
        hd, _ = opcoes_geradas(pasta, nota=5, nota_gpu=5, altura_tela=1080)
        confere("tela 1080p + dedicada: como antes (PS1 6x, PSP 1920x1088)",
                hd.get("swanstation_GPU_ResolutionScale") == "6"
                and hd.get("ppsspp_internal_resolution") == "1920x1088", hd.get("swanstation_GPU_ResolutionScale"))
        integrada, _ = opcoes_geradas(pasta, nota=5, nota_gpu=3, altura_tela=2160)
        confere("tela 4K + placa integrada (nota 3): nao sobe (PS1 4x)",
                integrada.get("swanstation_GPU_ResolutionScale") == "4", integrada.get("swanstation_GPU_ResolutionScale"))
        modesto, _ = opcoes_geradas(pasta, nota=5, nota_gpu=5, modesto=True, altura_tela=2160)
        confere("4K + Grafico igual ao console original: o original vence (PS1 1x)",
                modesto.get("swanstation_GPU_ResolutionScale") == "1", modesto.get("swanstation_GPU_ResolutionScale"))
        antiga, _ = opcoes_geradas(pasta, nota=5, altura_tela=2160)
        confere("chamada sem nota da placa: nao sobe", antiga.get("swanstation_GPU_ResolutionScale") != "9",
                antiga.get("swanstation_GPU_ResolutionScale"))

        print("2. tela")
        altura = hardware.altura_da_tela()
        confere("altura da tela principal: %d linhas" % altura, 400 <= altura <= 10000, altura)

        if "--sem-retroarch" in sys.argv:
            return 0 if not falhas else 1
        print("3. RetroArch com os valores 4K")
        _vale, arquivo_4k = opcoes_geradas(pasta, nota=5, nota_gpu=5, altura_tela=2160,
                                           extras=graficos.opcoes_de_memory_card("", "ps1"))
        for console, jogo, nucleo, chave in JOGOS:
            if not os.path.isfile(jogo):
                print("  (sem jogo de %s: pulado)" % console)
                continue
            sub = os.path.join(pasta, console.replace(" ", "_"))
            cfg = base.config_base(sub, {"audio_enable": "false"})
            # As opcoes de nucleo desta rodada sao as do degrau 4K.
            texto = open(cfg, encoding="utf-8").read()
            texto = re.sub(r'^core_options_path = ".*"$', lambda _m: 'core_options_path = "%s"' % arquivo_4k,
                           texto, flags=re.M)
            open(cfg, "w", encoding="utf-8").write(texto)
            foto, registro = os.path.join(sub, "foto.png"), os.path.join(sub, "ra.log")
            inicio = time.monotonic()
            try:
                subprocess.run([base.RETROARCH, "-L", os.path.join(RAIZ, "retroarch", "cores", nucleo + "_libretro.dll"),
                                "--appendconfig", cfg, "--verbose", "--log-file", registro, "--max-frames=900",
                                "--max-frames-ss", "--max-frames-ss-path=" + foto, jogo],
                               cwd=os.path.dirname(base.RETROARCH), timeout=180,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                travou = False
            except subprocess.TimeoutExpired:
                travou = True
            log = open(registro, encoding="utf-8", errors="ignore").read() if os.path.isfile(registro) else ""
            leu = re.search(r'GET_VARIABLE: %s = "%s"' % (re.escape(chave), re.escape(ESPERADO_4K[chave])), log)
            tamanho = os.path.getsize(foto) if os.path.isfile(foto) else 0
            confere("%s: o nucleo leu %s = %s e o jogo mostrou imagem (%.0f s)"
                    % (console, chave, ESPERADO_4K[chave], time.monotonic() - inicio),
                    bool(leu) and tamanho > 2000 and not travou,
                    {"leu": bool(leu), "foto": tamanho, "travou": travou, "erros": base.erros_importantes(log)[:2]})
    finally:
        limpeza.apagar_pasta(pasta)

    print()
    if falhas:
        print("FALHOU: %d de %d" % (len(falhas), total[0]))
        return 1
    print("Tela 4K: %d de %d certos." % (total[0], total[0]))
    return 0


if __name__ == "__main__":
    sys.exit(protege_cfg.rodar(main))
