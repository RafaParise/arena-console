# -*- coding: utf-8 -*-
r"""PSP no "Grafico original": pulo de quadros automatico chega ao nucleo.

Frente 6 (01/10/2026). God of War (PSP) rodou "bem, abaixo de 60" no
Celeron otimizado: abaixo de 60, o jogo e o som ficam LENTOS. No PPSSPP o
pulo de quadros automatico (ppsspp_auto_frameskip) so deixa de desenhar um
quadro quando o emulador esta atrasado -- o jogo e o som seguem na
velocidade certa; com folga, nada muda. Pelo codigo do PPSSPP
(Core/HLE/sceDisplay.cpp, DoFrameTiming e UseAutoFrameSkip):
  - so funciona com ppsspp_frameskip diferente de zero;
  - nao funciona com ppsspp_skip_buffer_effects ligado.
Por isso o modo modesto leva frameskip "1" + automatico, e continua com
skip_buffer_effects desligado. Fora do modesto, tudo como antes. Tambem:
"0" nao e' um valor que o nucleo conhece para ppsspp_frameskip (o .opt que
o RetroArch gera diz "disabled") -- trocado.

Monta as opcoes como o ARENA faz (numa pasta temporaria), abre um jogo de
PSP de verdade por 600 quadros e confere no registro detalhado o que o
nucleo LEU (GET_VARIABLE). Nada do ARENA de verdade e' tocado.

Uso: servidor\python\python.exe testes\teste_psp_pulo_de_quadros.py
"""
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RA = os.path.join(RAIZ, "retroarch")
CORE = os.path.join(RA, "cores", "ppsspp_libretro.dll")


def valor_no_log(texto, chave):
    achados = re.findall(r'GET_VARIABLE: %s = "([^"]*)"' % re.escape(chave), texto)
    return achados[-1] if achados else None


def rodar(arena, graficos, pasta, jogo, modesto):
    graficos.ARQUIVO_OPCOES_CORE = os.path.join(pasta, "opcoes_%d.cfg" % modesto)
    arena.ARQUIVO_OVERRIDE = os.path.join(pasta, "override_%d.cfg" % modesto)
    config = arena.carregar_config()
    graficos.gravar_opcoes_dos_nucleos(arena.CAPACIDADE["nota"], None,
                                       arena.CAPACIDADE.get("nota_gpu"), modesto=modesto)
    override = arena.gravar_override(config, 3)
    log_dir = os.path.join(pasta, "log_%d" % modesto)
    os.makedirs(log_dir)
    extra = os.path.join(pasta, "extra_%d.cfg" % modesto)
    with open(extra, "w", encoding="utf-8") as f:
        f.write('log_dir = "%s"\nlog_to_file = "true"\nlog_verbosity = "true"\n'
                'frontend_log_level = "0"\nlibretro_log_level = "0"\n'
                'video_fullscreen = "false"\nconfig_save_on_exit = "false"\n'
                'savefile_directory = "%s"\nsavestate_directory = "%s"\n'
                'savestate_auto_save = "false"\nsavestate_auto_load = "false"\n'
                % (log_dir, pasta, pasta))
    subprocess.run([os.path.join(RA, "retroarch.exe"), "-L", CORE,
                    "--appendconfig", override + "|" + extra,
                    "--max-frames", "600", "--verbose", jogo],
                   cwd=RAIZ, capture_output=True, timeout=180)
    logs = glob.glob(os.path.join(log_dir, "retroarch__*.log"))
    return open(logs[-1], encoding="utf-8", errors="ignore").read() if logs else ""


def main():
    falhas, total = [], [0]

    def confere(nome, ok, detalhe=""):
        total[0] += 1
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, detalhe))
        if not ok:
            falhas.append(nome)

    jogos = sorted(glob.glob(os.path.join(RAIZ, "jogos", "pessoais", "PSP", "*.iso")),
                   key=os.path.getsize)
    if not jogos or not os.path.isfile(CORE):
        print("Sem jogo de PSP ou sem o nucleo PPSSPP: nada a testar.")
        return 0
    sys.path.insert(0, os.path.join(RAIZ, "servidor"))
    import arena  # noqa: E402
    import graficos  # noqa: E402

    pasta = tempfile.mkdtemp(prefix="arena_psp_pulo_")
    try:
        jogo = jogos[0]
        print("Jogo: %s" % os.path.basename(jogo))
        normal = rodar(arena, graficos, pasta, jogo, modesto=False)
        modesto = rodar(arena, graficos, pasta, jogo, modesto=True)
        for nome, texto in (("normal", normal), ("modesto", modesto)):
            confere("%s: o jogo abriu (registro sem falha de carregar)" % nome,
                    bool(texto) and "Failed to load content" not in texto
                    and "Falha ao carregar" not in texto)
        confere("normal: pulo automatico desligado",
                valor_no_log(normal, "ppsspp_auto_frameskip") == "disabled",
                str(valor_no_log(normal, "ppsspp_auto_frameskip")))
        confere("normal: frameskip 'disabled' (valor que o nucleo conhece)",
                valor_no_log(normal, "ppsspp_frameskip") == "disabled",
                str(valor_no_log(normal, "ppsspp_frameskip")))
        confere("modesto: pulo automatico ligado",
                valor_no_log(modesto, "ppsspp_auto_frameskip") == "enabled",
                str(valor_no_log(modesto, "ppsspp_auto_frameskip")))
        confere("modesto: frameskip 1 (o automatico precisa dele diferente de zero)",
                valor_no_log(modesto, "ppsspp_frameskip") == "1",
                str(valor_no_log(modesto, "ppsspp_frameskip")))
        confere("modesto: skip_buffer_effects desligado (senao o automatico nao funciona)",
                valor_no_log(modesto, "ppsspp_skip_buffer_effects") == "disabled",
                str(valor_no_log(modesto, "ppsspp_skip_buffer_effects")))
    finally:
        shutil.rmtree(pasta, ignore_errors=True)

    print()
    if falhas:
        print("FALHOU: %d de %d" % (len(falhas), total[0]))
        return 1
    print("PSP pulo de quadros: %d de %d certos." % (total[0], total[0]))
    return 0


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import protege_cfg
    sys.exit(protege_cfg.rodar(main))
