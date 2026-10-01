# -*- coding: utf-8 -*-
r"""PCSX2 (PS2): motor de video escolhido pela tela do ARENA.

Frente 6 (01/10/2026): no automatico, o PCSX2 2.8 escolhe DirectX 12 em
placa Intel e AMD com nivel de recurso 12_0 (D3D::GetPreferredRenderer, no
codigo-fonte dele) -- suspeito dos graficos piscando no Celeron da escola.
Ajustes -> Emuladores -> "Motor de video do PS2" grava a chave Renderer
(-1 automatico, 3 DirectX 11, 15 DirectX 12, 14 Vulkan: enum
GSRendererType do pcsx2/Config.h).

Confere, numa pasta temporaria (nunca no PCSX2 de verdade):
  - cada escolha grava o numero certo, e so uma vez no arquivo;
  - voltar ao automatico grava -1 (a volta vale);
  - valor desconhecido vira automatico;
  - o resto do [EmuCore/GS] do Rafael continua la;
  - a config do ARENA guarda so valores conhecidos.

Uso: servidor\python\python.exe testes\teste_pcsx2_motor.py
"""
import json
import os
import shutil
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
import graficos  # noqa: E402

INI = """[EmuCore/GS]
VsyncEnable = true
upscale_multiplier = 2
AspectRatio = 16:9
accurate_blending_unit = 5
Renderer = 3
"""


def ler_gs(caminho):
    valores, dentro, repetidas = {}, False, []
    for linha in open(caminho, encoding="utf-8"):
        limpo = linha.strip()
        if limpo.startswith("["):
            dentro = limpo == "[EmuCore/GS]"
        elif dentro and " = " in limpo:
            chave, valor = limpo.split(" = ", 1)
            if chave in valores:
                repetidas.append(chave)
            valores[chave] = valor
    return valores, repetidas


def main():
    falhas, total = [], [0]

    def confere(nome, ok, detalhe=""):
        total[0] += 1
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, detalhe if not ok else ""))
        if not ok:
            falhas.append(nome)

    pasta = tempfile.mkdtemp(prefix="arena_pcsx2_motor_")
    try:
        exe = os.path.join(pasta, "pcsx2-qt.exe")
        ini = os.path.join(pasta, "inis", "PCSX2.ini")
        os.makedirs(os.path.dirname(ini))
        open(exe, "w").close()
        open(ini, "w", encoding="utf-8").write(INI)

        esperado = {"d3d11": "3", "d3d12": "15", "vulkan": "14", "automatico": "-1"}
        for motor, numero in esperado.items():
            graficos.escrever_config_pcsx2(exe, nota=3, nota_gpu=3, integrada=True, motor=motor)
            gs, repetidas = ler_gs(ini)
            confere("motor %s grava Renderer = %s" % (motor, numero), gs.get("Renderer") == numero,
                    str(gs.get("Renderer")))
            confere("motor %s: nenhuma chave repetida" % motor, not repetidas, str(repetidas))

        graficos.escrever_config_pcsx2(exe, nota=3, nota_gpu=3, integrada=True)
        confere("sem dizer o motor = automatico (-1)", ler_gs(ini)[0].get("Renderer") == "-1")
        graficos.escrever_config_pcsx2(exe, nota=3, nota_gpu=3, integrada=True, motor="opengl-inventado")
        confere("motor desconhecido = automatico (-1)", ler_gs(ini)[0].get("Renderer") == "-1")
        graficos.escrever_config_pcsx2(exe, motor="d3d11")
        confere("sem nota (so controles) o motor vale do mesmo jeito",
                ler_gs(ini)[0].get("Renderer") == "3")
        gs = ler_gs(ini)[0]
        confere("o 16:9 do Rafael continua", gs.get("AspectRatio") == "16:9")
        confere("o vsync do Rafael continua", gs.get("VsyncEnable") == "true")

        # Config do ARENA: so entra valor conhecido.
        import arena  # noqa: E402
        config_teste = os.path.join(pasta, "config.json")
        original = arena.ARQUIVO_CONFIG
        try:
            arena.ARQUIVO_CONFIG = config_teste
            for valor, esperado_cfg in (("d3d11", "d3d11"), ("vulkan", "vulkan"),
                                        ("<script>", "automatico"), (5, "automatico"),
                                        ([1, 2], "automatico"), ({"a": 1}, "automatico")):
                json.dump({"motor_ps2": valor}, open(config_teste, "w", encoding="utf-8"))
                lido = arena.ler_config_do_disco().get("motor_ps2")
                confere("config com motor_ps2 = %r vira %r" % (valor, esperado_cfg),
                        lido == esperado_cfg, str(lido))
            os.remove(config_teste)
            confere("config sem a chave = automatico",
                    arena.ler_config_do_disco().get("motor_ps2") == "automatico")
        finally:
            arena.ARQUIVO_CONFIG = original

        # A tela oferece exatamente os motores que o servidor aceita.
        html = open(os.path.join(RAIZ, "launcher", "index.html"), encoding="utf-8").read()
        bloco = html.split('id="listaMotorPs2"', 1)[-1].split("</select>", 1)[0]
        oferecidos = {parte.split('"', 1)[0] for parte in bloco.split('value="')[1:]}
        confere("a tela oferece os mesmos motores que o servidor aceita",
                oferecidos == set(graficos.MOTORES_PCSX2), str(oferecidos))
    finally:
        shutil.rmtree(pasta, ignore_errors=True)

    print()
    if falhas:
        print("FALHOU: %d de %d" % (len(falhas), total[0]))
        return 1
    print("Motor do PS2: %d de %d certos." % (total[0], total[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
