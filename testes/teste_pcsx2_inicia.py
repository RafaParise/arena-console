# -*- coding: utf-8 -*-
r"""O PS2 chega a rodar o jogo com a configuracao que o ARENA escreve?

Achado 26/09/2026: depois que o PCSX2 passou a respeitar a configuracao do
ARENA (SettingsVersion), o Crash Nitro Kart ficou em tela preta e travou.
Aqui cada variante escreve a configuracao, abre o jogo ~30 s e le o
registro: "ELF ... is executing" = o jogo comecou; sem isso = travou antes.

Uso: servidor\python\python.exe testes\teste_pcsx2_inicia.py
"""
import os
import subprocess
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
import controles  # noqa: E402
import graficos  # noqa: E402

EXE = os.path.join(RAIZ, "emuladores", "PCSX2", "PCSX2", "pcsx2-qt.exe")
JOGO = os.path.join(RAIZ, "jogos", "pessoais", "PS2", "Crash Nitro Kart (USA).chd")
LOG = os.path.join(os.path.dirname(EXE), "logs", "emulog.txt")

VARIANTES = [
    ("normal", {}),
    ("ultra", {"ultra": True}),
    ("leve", {"preset": "leve"}),
    ("2jog", {"jogadores": 2}),                     # sem multitap
    ("semctl", {"controles_xinput": []}),           # so teclado
    ("cartao", {"cartoes": ("Mcd001.ps2", "Mcd002.ps2")}),  # cartoes padrao
    ("vulkan", {"gs": {"Renderer": "14"}}),         # o que o PCSX2 de Documentos usava
    ("dx11", {"gs": {"Renderer": "3"}}),
    ("semxinput", {"secoes": {"InputSources": {"XInput": "false"}}}),
    ("semsdl", {"secoes": {"InputSources": {"SDL": "false"}}}),
    ("fastboot", {"secoes": {"EmuCore": {"EnableFastBoot": "false"}}}),
]


def rodar(nome, opcoes):
    base = {"jogadores": 4, "controles_xinput": controles.controles_xinput(),
            "cartoes": graficos.preparar_portatil_pcsx2(EXE)}
    extra_gs = base.pop("gs", None) if "gs" in opcoes else None
    base.update({k: v for k, v in opcoes.items() if k not in ("gs", "secoes")})
    graficos.escrever_config_pcsx2(EXE, nota=4, nota_gpu=3, **base)
    ini = os.path.join(os.path.dirname(EXE), "inis", "PCSX2.ini")
    texto = open(ini, encoding="utf-8").read()
    # Sem o registro ligado o teste nao tem o que ler.
    texto = graficos._trocar_chaves_ini(texto, "Logging", {"EnableFileLogging": "true"})
    if opcoes.get("gs"):
        texto = graficos._trocar_chaves_ini(texto, "EmuCore/GS", opcoes["gs"])
    for secao, chaves in (opcoes.get("secoes") or {}).items():
        texto = graficos._trocar_chaves_ini(texto, secao, chaves)
    open(ini, "w", encoding="utf-8").write(texto)
    if os.path.exists(LOG):
        os.remove(LOG)   # registro novo a cada variante
    processo = subprocess.Popen([EXE, "-fullscreen", JOGO], cwd=os.path.dirname(EXE))
    comecou = False
    for _ in range(30):
        time.sleep(1)
        try:
            texto = open(LOG, encoding="utf-8", errors="ignore").read()
        except OSError:
            texto = ""
        if "is executing" in texto:
            comecou = True
            break
    processo.kill()
    subprocess.run(["taskkill", "/F", "/IM", "pcsx2-qt.exe"], capture_output=True)
    time.sleep(2)
    ultima = [l.strip() for l in texto.splitlines() if l.strip()][-1:] if texto else []
    print("%-8s %s   ultima linha: %s" % (nome, "COMECOU" if comecou else "TRAVOU ",
                                          ultima[0][:90] if ultima else "-"))
    return comecou


def main():
    so = sys.argv[1:] or [n for n, _ in VARIANTES]
    for nome, opcoes in VARIANTES:
        if nome in so:
            rodar(nome, opcoes)
    return 0


if __name__ == "__main__":
    sys.exit(main())
