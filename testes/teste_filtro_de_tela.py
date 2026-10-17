# -*- coding: utf-8 -*-
r"""Escala da tela (o filtro que estica o jogo ate a tela): chega de verdade
ao RetroArch, e o certo para cada jogo.

Achado de 01/10/2026: o ARENA escrevia o filtro como video_shader no
arquivo extra (--appendconfig), e o RetroArch 1.22 IGNORA essa chave -- o
registro dizia "Loading stock shader" em todo jogo. Desde entao o filtro vai
pela linha de comando (--set-shader).

Desde 17/10/2026 (item 10 dos pedidos de 15/10, a escala como a do Lossless
Scaling), o filtro e' um preset do ARENA (servidor\filtros), que cita o
shader do RetroArch por caminho relativo, e a escolha e' de
graficos.jeito_da_escala. Confere:
  - SNES (2D): o pixel nitido, video_shader_enable "true", e a chave
    video_shader nunca vai para o arquivo extra;
  - PSP (3D desenhado menor que a tela): Catmull-Rom na placa media (nota
    3), FSR na boa (nota 4), so a nitidez no Ultra;
  - "Original" e o nivel minimo: nada;
  - o "Filtro de tela" antigo, desligado nos Ajustes avancados, nao manda mais;
  - com o RetroArch de verdade: cada um dos 5 presets do ARENA compila
    (registro "Compiling shader" com o shader citado), sem cair no padrao.
Nada do ARENA de verdade e' tocado (arquivos numa pasta temporaria).

Uso: servidor\python\python.exe testes\teste_filtro_de_tela.py
"""
import glob
import os
import subprocess
import sys
import tempfile
from unittest import mock

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RA = os.path.join(RAIZ, "retroarch")
# O shader que cada preset do ARENA cita (o que o registro tem que mostrar).
CITADOS = {"pixel": "sharp-bilinear-simple.slang", "nitido": "fsr-pass1.slang",
           "catmull": "catmull-rom-x.slang", "rcas": "rcas.slang", "suave": "scalefx-pass"}


def ler_cfg(caminho):
    valores = {}
    for linha in open(caminho, encoding="utf-8"):
        if " = " in linha and not linha.startswith("#"):
            chave, valor = linha.strip().split(" = ", 1)
            valores[chave] = valor.strip('"')
    return valores


def main():
    falhas, total = [], [0]

    def confere(nome, ok, detalhe=""):
        total[0] += 1
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, detalhe if not ok else ""))
        if not ok:
            falhas.append(nome)

    sys.path.insert(0, os.path.join(RAIZ, "servidor"))
    import arena  # noqa: E402
    import graficos  # noqa: E402
    import limpeza  # noqa: E402

    pasta = tempfile.mkdtemp(prefix="arena_filtro_")
    original = (arena.ARQUIVO_OVERRIDE, graficos.ARQUIVO_OPCOES_CORE)
    try:
        arena.ARQUIVO_OVERRIDE = os.path.join(pasta, "override.cfg")
        graficos.ARQUIVO_OPCOES_CORE = os.path.join(pasta, "opcoes.cfg")
        config = arena.config_padrao()

        def partida(plataforma, nucleo, nota_gpu=3, tela=900, **mudancas):
            with mock.patch.object(arena.hardware, "altura_da_tela", return_value=tela), \
                    mock.patch.dict(arena.CAPACIDADE, {"nota": 4, "nota_gpu": nota_gpu}):
                caminho, filtro = arena.gravar_override(dict(config, **mudancas), 2, plataforma=plataforma,
                                                        devolver_filtro=True, nucleo=nucleo)
            return filtro, ler_cfg(caminho)

        filtro, cfg = partida("snes", "snes9x_libretro.dll")
        confere("SNES: o pixel nitido do ARENA",
                os.path.basename(filtro) == "pixel-nitido.slangp" and os.path.isfile(filtro), filtro)
        confere("SNES: video_shader_enable = true", cfg.get("video_shader_enable") == "true",
                str(cfg.get("video_shader_enable")))
        confere("a chave video_shader nao vai para o arquivo (o RetroArch ignora)",
                "video_shader" not in cfg)

        # Nota 3: 960x544 na tela de 900 -> estica. Nota 4: 1920x1088, maior
        # que a tela -> nada a esticar. Nota 4 na TV 4K: 2880x1632 -> FSR.
        for nota, tela, esperado in ((3, 900, "catmull-rom.slangp"), (4, 900, ""),
                                     (4, 2160, "fsr.slangp")):
            filtro, _cfg = partida("psp", "ppsspp_libretro.dll", nota_gpu=nota, tela=tela)
            confere("PSP, placa nota %d, tela de %d linhas: %s" % (nota, tela, esperado or "sem filtro"),
                    os.path.basename(filtro) == esperado, filtro)
        filtro, cfg = partida("psp", "ppsspp_libretro.dll", ultra_desempenho=True)
        confere("PSP no Ultra: so a nitidez (RCAS), esticada pelo bilinear",
                os.path.basename(filtro) == "rcas.slangp" and cfg.get("video_smooth") == "true",
                "%s %s" % (filtro, cfg.get("video_smooth")))

        for mudanca in ({"escala_da_tela": "original"}, {"abaixo_do_original": "minimo"}):
            filtro, cfg = partida("snes", "snes9x_libretro.dll", **mudanca)
            confere("%s: nada, mesmo no SNES" % mudanca, filtro == "" and
                    cfg.get("video_shader_enable") == "false", filtro)
        filtro, _cfg = partida("snes", "snes9x_libretro.dll",
                               avancado=dict(config["avancado"], video_shader_enable="false"))
        confere("o Filtro de tela antigo, desligado, nao manda mais",
                os.path.basename(filtro) == "pixel-nitido.slangp", filtro)
        confere("chamada antiga (sem devolver_filtro) devolve so o arquivo",
                isinstance(arena.gravar_override(config, 1), str))

        jogos = sorted(glob.glob(os.path.join(RAIZ, "jogos", "pessoais", "Super Nintendo", "*.sfc"))
                       + glob.glob(os.path.join(RAIZ, "jogos", "pessoais", "Super Nintendo", "*.smc")),
                       key=os.path.getsize)
        jogos = [j for j in jogos if not os.path.basename(j).lower().startswith("bs ")]
        presets = {jeito: graficos.caminho_do_filtro(jeito) for jeito in CITADOS}
        if jogos and all(presets.values()):
            caminho = arena.gravar_override(config, 1)
            extra = os.path.join(pasta, "extra.cfg")
            with open(extra, "w", encoding="utf-8") as f:
                f.write('config_save_on_exit = "false"\nsavefile_directory = "%s"\n'
                        'savestate_directory = "%s"\nsavestate_auto_load = "false"\n'
                        'audio_enable = "false"\nvideo_fullscreen = "false"\n'
                        'video_shader_enable = "true"\nlog_verbosity = "true"\n'
                        'frontend_log_level = "0"\n' % (pasta, pasta))
            for jeito, preset in presets.items():
                log = os.path.join(pasta, "log_%s.txt" % jeito)
                subprocess.run([os.path.join(RA, "retroarch.exe"), "-L",
                                os.path.join(RA, "cores", "snes9x_libretro.dll"),
                                "--appendconfig", caminho + "|" + extra, "--set-shader", preset,
                                "--max-frames=90", "--verbose", "--log-file=" + log, jogos[0]],
                               cwd=RAIZ, capture_output=True, timeout=120)
                texto = open(log, encoding="utf-8", errors="replace").read() if os.path.isfile(log) else ""
                confere("RetroArch compila o preset %s (%s)" % (os.path.basename(preset), CITADOS[jeito]),
                        CITADOS[jeito] in texto and "Compiling shader" in texto
                        and "Loading stock shader" not in texto,
                        "[nada no registro]" if not texto else "")
        else:
            print("  (sem jogo de SNES ou sem o pacote de shaders: parte do RetroArch pulada)")
    finally:
        arena.ARQUIVO_OVERRIDE, graficos.ARQUIVO_OPCOES_CORE = original
        limpeza.apagar_pasta(pasta)

    print()
    if falhas:
        print("FALHOU: %d de %d" % (len(falhas), total[0]))
        return 1
    print("Escala da tela: %d de %d certos." % (total[0], total[0]))
    return 0


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import protege_cfg
    sys.exit(protege_cfg.rodar(main))
