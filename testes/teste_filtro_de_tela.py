# -*- coding: utf-8 -*-
r"""Filtro de tela (shader): chega de verdade ao RetroArch, e so no 2D.

Achado de 01/10/2026: o ARENA escrevia o filtro como video_shader no
arquivo extra (--appendconfig), e o RetroArch 1.22 IGNORA essa chave -- o
registro dizia "Loading stock shader" em todo jogo. Nenhum filtro chegou a
aparecer (o caminho do Pixellate nem existia mais), e o filtro da nota 4
era uma grade de Game Boy Color que mudaria a cor de qualquer console.

Agora: o "Filtro de tela" (perfil Qualidade ou ligado pelo aluno) coloca o
"pixel nitido" (sharp-bilinear) so nos consoles de desenho 2D, pela linha
de comando (--set-shader). Confere, com o RetroArch de verdade:
  - SNES com o filtro pedido: gravar_override devolve o filtro, e o
    registro mostra o RetroArch compilando ESSE filtro;
  - PS1 (3D) com o filtro pedido: sem filtro, e video_shader_enable "false";
  - filtro desligado: nada, mesmo no SNES;
  - a chave video_shader nunca mais vai para o arquivo extra.
Nada do ARENA de verdade e' tocado (arquivos numa pasta temporaria).

Uso: servidor\python\python.exe testes\teste_filtro_de_tela.py
"""
import glob
import os
import shutil
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RA = os.path.join(RAIZ, "retroarch")


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

    pasta = tempfile.mkdtemp(prefix="arena_filtro_")
    original = (arena.ARQUIVO_OVERRIDE, graficos.ARQUIVO_OPCOES_CORE)
    try:
        arena.ARQUIVO_OVERRIDE = os.path.join(pasta, "override.cfg")
        graficos.ARQUIVO_OPCOES_CORE = os.path.join(pasta, "opcoes.cfg")
        config = arena.carregar_config()
        config["avancado"] = dict(config.get("avancado") or {}, video_shader_enable="true")
        config["modo_modesto"] = False
        config["ultra_desempenho"] = False

        caminho, filtro = arena.gravar_override(config, 1, plataforma="snes", devolver_filtro=True)
        cfg = ler_cfg(caminho)
        confere("SNES com filtro pedido: devolve o pixel nitido",
                filtro.endswith("sharp-bilinear-simple.slangp") and os.path.isfile(filtro), filtro)
        confere("SNES: video_shader_enable = true", cfg.get("video_shader_enable") == "true",
                str(cfg.get("video_shader_enable")))
        confere("a chave video_shader nao vai mais para o arquivo (o RetroArch ignora)",
                "video_shader" not in cfg)

        caminho_ps1, filtro_ps1 = arena.gravar_override(config, 2, plataforma="ps1", devolver_filtro=True)
        cfg_ps1 = ler_cfg(caminho_ps1)
        confere("PS1 (3D): sem filtro", filtro_ps1 == "", filtro_ps1)
        confere("PS1: video_shader_enable = false", cfg_ps1.get("video_shader_enable") == "false")

        sem = dict(config, avancado=dict(config["avancado"], video_shader_enable="false"))
        _c, filtro_sem = arena.gravar_override(sem, 1, plataforma="snes", devolver_filtro=True)
        confere("filtro desligado: nada, mesmo no SNES", filtro_sem == "", filtro_sem)
        confere("chamada antiga (sem devolver_filtro) devolve so o arquivo",
                isinstance(arena.gravar_override(config, 1), str))

        jogos = sorted(glob.glob(os.path.join(RAIZ, "jogos", "pessoais", "Super Nintendo", "*.sfc"))
                       + glob.glob(os.path.join(RAIZ, "jogos", "pessoais", "Super Nintendo", "*.smc")),
                       key=os.path.getsize)
        jogos = [j for j in jogos if not os.path.basename(j).lower().startswith("bs ")]
        if jogos and filtro:
            caminho, filtro = arena.gravar_override(config, 1, plataforma="snes", devolver_filtro=True)
            extra = os.path.join(pasta, "extra.cfg")
            with open(extra, "w", encoding="utf-8") as f:
                f.write('config_save_on_exit = "false"\nsavefile_directory = "%s"\n'
                        'savestate_directory = "%s"\nsavestate_auto_load = "false"\n'
                        'audio_enable = "false"\nvideo_fullscreen = "false"\n' % (pasta, pasta))
            log = os.path.join(pasta, "log.txt")
            subprocess.run([os.path.join(RA, "retroarch.exe"), "-L",
                            os.path.join(RA, "cores", "snes9x_libretro.dll"),
                            "--appendconfig", caminho + "|" + extra, "--set-shader", filtro,
                            "--max-frames=120", "--verbose", "--log-file=" + log, jogos[0]],
                           cwd=RAIZ, capture_output=True, timeout=120)
            texto = open(log, encoding="utf-8", errors="replace").read() if os.path.isfile(log) else ""
            confere("o RetroArch compila o filtro do ARENA (registro)",
                    "sharp-bilinear-simple.slang" in texto and "Compiling shader" in texto,
                    "[nada no registro]" if not texto else "")
            confere("e nao fica no filtro padrao", "Loading stock shader" not in texto)
        else:
            print("  (sem jogo de SNES ou sem o pacote de shaders: parte do RetroArch pulada)")
    finally:
        arena.ARQUIVO_OVERRIDE, graficos.ARQUIVO_OPCOES_CORE = original
        shutil.rmtree(pasta, ignore_errors=True)

    print()
    if falhas:
        print("FALHOU: %d de %d" % (len(falhas), total[0]))
        return 1
    print("Filtro de tela: %d de %d certos." % (total[0], total[0]))
    return 0


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import protege_cfg
    sys.exit(protege_cfg.rodar(main))
