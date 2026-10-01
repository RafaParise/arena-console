# -*- coding: utf-8 -*-
r"""PCSX2 (PS2): imagem pela placa de video -- integrada fica leve.

Decisao do Rafael (30/09/2026): o Celeron otimizado roda PS2 com 4
jogadores, mas com graficos piscando/distorcendo. A placa integrada recebia
2x de resolucao e filtro 4x, e a mistura de cores ficava a que estivesse no
arquivo ("Maxima", 5, escolhida na tela do PCSX2). Agora, na integrada,
automatico e grafico original: 1x nativo e mistura "Basica". Placa dedicada
e "Mais bonito" continuam como eram.

Escreve numa pasta temporaria (nunca no PCSX2 de verdade), partindo de um
PCSX2.ini igual ao da pasta (mistura 5, 16:9, filtro bilinear), e confere.

Uso: servidor\python\python.exe testes\teste_pcsx2_placa.py
"""
import os
import shutil
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
import graficos  # noqa: E402

INI_DO_RAFAEL = """[EmuCore/GS]
VsyncEnable = true
upscale_multiplier = 2
texture_preloading = 2
AspectRatio = 16:9
FMVAspectRatioSwitch = 16:9
filter = 2
accurate_blending_unit = 5
hw_mipmap = false
"""


def ler_gs(caminho):
    valores, dentro = {}, False
    for linha in open(caminho, encoding="utf-8"):
        limpo = linha.strip()
        if limpo.startswith("["):
            dentro = limpo == "[EmuCore/GS]"
        elif dentro and " = " in limpo:
            chave, valor = limpo.split(" = ", 1)
            valores[chave] = valor
    return valores


def main():
    falhas = []

    def confere(nome, ok, detalhe=""):
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, detalhe))
        if not ok:
            falhas.append(nome)

    pasta = tempfile.mkdtemp(prefix="arena_pcsx2_")
    try:
        exe = os.path.join(pasta, "pcsx2-qt.exe")
        ini = os.path.join(pasta, "inis", "PCSX2.ini")
        os.makedirs(os.path.dirname(ini))

        def escrever(**kw):
            with open(ini, "w", encoding="utf-8") as f:
                f.write(INI_DO_RAFAEL)
            graficos.escrever_config_pcsx2(exe, **kw)
            return ler_gs(ini)

        print("\n1. Celeron: placa integrada, automatico")
        gs = escrever(nota=4, nota_gpu=3, integrada=True)
        confere("1x nativo", gs.get("upscale_multiplier") == "1", gs.get("upscale_multiplier"))
        confere("mistura Basica (era Maxima)", gs.get("accurate_blending_unit") == "1")
        confere("sem filtro anisotropico", gs.get("MaxAnisotropy") == "0")
        confere("pre-carga de texturas no padrao do PCSX2 (2)", gs.get("texture_preloading") == "2")
        confere("escolhas dele ficam: 16:9, filtro bilinear, vsync",
                gs.get("AspectRatio") == "16:9" and gs.get("filter") == "2"
                and gs.get("VsyncEnable") == "true")

        print("\n2. Grafico original (modesto) com placa integrada")
        gs = escrever(nota=4, nota_gpu=3, integrada=True, modesto=True)
        confere("1x nativo e mistura Basica",
                gs.get("upscale_multiplier") == "1" and gs.get("accurate_blending_unit") == "1")

        print("\n3. 'Mais leve' (aba Emuladores)")
        gs = escrever(nota=5, nota_gpu=5, integrada=False, preset="leve")
        confere("1x e mistura Basica, mesmo com placa forte",
                gs.get("upscale_multiplier") == "1" and gs.get("accurate_blending_unit") == "1")

        print("\n4. 'Mais bonito' com placa integrada")
        gs = escrever(nota=4, nota_gpu=3, integrada=True, preset="bonito")
        confere("4x", gs.get("upscale_multiplier") == "4")
        confere("mistura NAO mexida (fica a Maxima dele)", gs.get("accurate_blending_unit") == "5")

        print("\n5. Placa dedicada, automatico")
        gs = escrever(nota=4, nota_gpu=4, integrada=False)
        confere("dedicada forte: 4x, mistura nao mexida",
                gs.get("upscale_multiplier") == "4" and gs.get("accurate_blending_unit") == "5")
        gs = escrever(nota=4, nota_gpu=3, integrada=False)
        confere("dedicada media: 2x como antes, mistura nao mexida",
                gs.get("upscale_multiplier") == "2" and gs.get("accurate_blending_unit") == "5")

        print("\n6. Quem chama sem dizer a placa (comportamento antigo)")
        gs = escrever(nota=4, nota_gpu=3)
        confere("2x, mistura nao mexida",
                gs.get("upscale_multiplier") == "2" and gs.get("accurate_blending_unit") == "5")
    finally:
        shutil.rmtree(pasta, ignore_errors=True)

    print("\nRESULTADO:", "PASSOU" if not falhas else "FALHOU (%s)" % ", ".join(falhas))
    return 0 if not falhas else 1


if __name__ == "__main__":
    sys.exit(main())
