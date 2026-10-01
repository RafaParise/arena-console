# -*- coding: utf-8 -*-
r"""Dolphin (GameCube e Wii): o ARENA escreve a imagem, nao so os controles?

Achado de 30/09/2026: o GFX.ini do Dolphin estava VAZIO -- o modo grafico
original e o ultra nao chegavam no GameCube/Wii, e a compilacao de efeitos
ficava no padrao do Dolphin (sincrona: trava a cada efeito novo).

Escreve numa pasta temporaria (nunca no Dolphin de verdade) e confere:
  1. Celeron (placa integrada, nota 3): hibrido, nativa, sem filtro, Dual Core.
  2. Placa dedicada forte (nota 4): 2x e filtro 4x.
  3. Grafico original (modesto) manda a nativa mesmo com placa forte.
  4. Preset da aba Emuladores ("leve"/"bonito") vale por cima da nota.
  5. Ultra liga tela cheia e anota o que havia; desligado, devolve o que a
     pessoa tinha (nao fica grudado, nem apaga escolha feita no Dolphin).
  6. O que ja estava nos arquivos fica; o que e' do ARENA e' trocado.
  7. Rodar duas vezes nao duplica chave.
  8. Os controles continuam sendo escritos.

Uso: servidor\python\python.exe testes\teste_dolphin_config.py
"""
import configparser
import os
import shutil
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
import graficos  # noqa: E402


def ler(caminho):
    ini = configparser.ConfigParser(strict=False, interpolation=None)
    ini.optionxform = str
    ini.read(caminho, encoding="utf-8")
    return ini


def main():
    falhas = []

    def confere(nome, ok, detalhe=""):
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, detalhe))
        if not ok:
            falhas.append(nome)

    pasta = tempfile.mkdtemp(prefix="arena_dolphin_")
    try:
        exe = os.path.join(pasta, "Dolphin.exe")
        config = os.path.join(pasta, "User", "Config")
        os.makedirs(config)
        # O que ja existia: chave do usuario + um 3x que o ARENA deve trocar.
        with open(os.path.join(config, "Dolphin.ini"), "w", encoding="utf-8") as f:
            f.write("[Analytics]\nID = abc123\n[Display]\nRenderToMain = True\n")
        with open(os.path.join(config, "GFX.ini"), "w", encoding="utf-8") as f:
            f.write("[Settings]\nShowFPS = True\nInternalResolution = 3\n")

        def escrever(**kw):
            return graficos.escrever_config_dolphin(exe, [0, 1], **kw)

        print("\n1. Celeron (placa integrada, nota da placa 3)")
        escrever(nota=4, nota_gpu=3)
        gfx, dol = ler(os.path.join(config, "GFX.ini")), ler(os.path.join(config, "Dolphin.ini"))
        confere("compilacao hibrida (2), nao sincrona", gfx["Settings"].get("ShaderCompilationMode") == "2")
        confere("resolucao nativa (1) -- trocou o 3x antigo", gfx["Settings"].get("InternalResolution") == "1")
        confere("sem filtro anisotropico (0)", gfx["Enhancements"].get("MaxAnisotropy") == "0")
        confere("Dual Core ligado", dol["Core"].get("CPUThread") == "True")
        confere("sem ultra: tela cheia nao e' tocada (nao estava no arquivo)",
                "Fullscreen" not in dol["Display"])

        print("\n2. Placa dedicada forte (nota 4)")
        escrever(nota=4, nota_gpu=4)
        gfx = ler(os.path.join(config, "GFX.ini"))
        confere("2x", gfx["Settings"].get("InternalResolution") == "2")
        confere("filtro 4x (2)", gfx["Enhancements"].get("MaxAnisotropy") == "2")

        print("\n3. Grafico original (modesto) com placa forte")
        escrever(nota=5, nota_gpu=5, modesto=True)
        gfx = ler(os.path.join(config, "GFX.ini"))
        confere("nativa", gfx["Settings"].get("InternalResolution") == "1")

        print("\n4. Preset da aba Emuladores")
        escrever(nota=5, nota_gpu=5, preset="leve")
        confere("'Mais leve' com placa forte: nativa",
                ler(os.path.join(config, "GFX.ini"))["Settings"].get("InternalResolution") == "1")
        escrever(nota=2, nota_gpu=2, preset="bonito")
        confere("'Mais bonito' com placa fraca: 2x",
                ler(os.path.join(config, "GFX.ini"))["Settings"].get("InternalResolution") == "2")

        print("\n5. Ultra desempenho")
        anotacao = os.path.join(config, graficos.ANOTACAO_ULTRA_DOLPHIN)
        escrever(nota=4, nota_gpu=3, ultra=True)
        dol = ler(os.path.join(config, "Dolphin.ini"))
        confere("ultra: tela cheia e sem pergunta ao parar",
                dol["Display"].get("Fullscreen") == "True" and dol["Interface"].get("ConfirmStop") == "False")
        confere("ultra: anotou o que havia antes", os.path.exists(anotacao))
        antes = open(anotacao, encoding="utf-8").read()
        escrever(nota=4, nota_gpu=3, ultra=True)
        confere("ultra de novo: a anotacao original continua",
                open(anotacao, encoding="utf-8").read() == antes)
        escrever(nota=4, nota_gpu=3, ultra=False)
        dol = ler(os.path.join(config, "Dolphin.ini"))
        confere("ultra desligado: volta a janela (nao fica grudado)",
                dol["Display"].get("Fullscreen") == "False" and dol["Interface"].get("ConfirmStop") == "True")
        confere("ultra desligado: anotacao apagada", not os.path.exists(anotacao))

        print("\n5b. Tela cheia escolhida pela pessoa na tela do Dolphin")
        caminho_ini = os.path.join(config, "Dolphin.ini")
        texto = open(caminho_ini, encoding="utf-8").read()
        with open(caminho_ini, "w", encoding="utf-8") as f:
            f.write(texto.replace("Fullscreen = False", "Fullscreen = True"))
        escrever(nota=4, nota_gpu=3)
        confere("sem ultra: a escolha da pessoa fica",
                ler(caminho_ini)["Display"].get("Fullscreen") == "True")
        escrever(nota=4, nota_gpu=3, ultra=True)
        escrever(nota=4, nota_gpu=3, ultra=False)
        confere("ultra liga e desliga: devolve a tela cheia DELA (True)",
                ler(caminho_ini)["Display"].get("Fullscreen") == "True")

        print("\n6. O que ja estava nos arquivos")
        gfx, dol = ler(os.path.join(config, "GFX.ini")), ler(os.path.join(config, "Dolphin.ini"))
        confere("GFX.ini: ShowFPS do usuario ficou", gfx["Settings"].get("ShowFPS") == "True")
        confere("Dolphin.ini: Analytics e RenderToMain ficaram",
                dol["Analytics"].get("ID") == "abc123" and dol["Display"].get("RenderToMain") == "True")
        confere("portas dos controles no [Core]", dol["Core"].get("SIDevice0") == "6")

        print("\n7. Duas vezes seguidas")
        escrever(nota=4, nota_gpu=3)
        escrever(nota=4, nota_gpu=3)
        texto = open(os.path.join(config, "GFX.ini"), encoding="utf-8").read()
        confere("nenhuma chave repetida", texto.count("ShaderCompilationMode") == 1
                and texto.count("InternalResolution") == 1, repr(texto))

        print("\n8. Controles")
        pad = open(os.path.join(config, "GCPadNew.ini"), encoding="utf-8").read()
        confere("GCPadNew.ini com os dois controles XInput",
                "XInput/0/Gamepad" in pad and "XInput/1/Gamepad" in pad)
    finally:
        shutil.rmtree(pasta, ignore_errors=True)

    print("\nRESULTADO:", "PASSOU" if not falhas else "FALHOU (%s)" % ", ".join(falhas))
    return 0 if not falhas else 1


if __name__ == "__main__":
    sys.exit(main())
