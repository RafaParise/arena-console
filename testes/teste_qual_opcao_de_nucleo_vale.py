# -*- coding: utf-8 -*-
r"""Revisao pos-auditoria: o RetroArch usa as opcoes de nucleo que o ARENA
escreve (retroarch-core-options.cfg) ou o arquivo .opt de cada nucleo?

Suspeita: com global_core_options = false (o padrao do RetroArch), o que vale
e' retroarch\config\<Nucleo>\<Nucleo>.opt, e o arquivo global do ARENA so e'
lido na PRIMEIRA vez (quando o .opt ainda nao existe).

Experimento: poe "3" na escala de resolucao do SwanStation no arquivo global
e "2" no .opt, abre um jogo de PS1 por alguns quadros com log detalhado, e
ve no log qual escala o nucleo usou. No fim, devolve os dois arquivos (e o
retroarch.cfg) exatamente como estavam.
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
GLOBAL = os.path.join(RA, "retroarch-core-options.cfg")
OPT = os.path.join(RA, "config", "SwanStation", "SwanStation.opt")
CORE = os.path.join(RA, "cores", "swanstation_libretro.dll")
CHAVE = "swanstation_GPU_ResolutionScale"
COM_GLOBAL = "--global" in sys.argv


def trocar(caminho, valor):
    with open(caminho, encoding="utf-8") as f:
        texto = f.read()
    linha = '%s = "%s"' % (CHAVE, valor)
    novo, n = re.subn(r'(?m)^%s = ".*"$' % CHAVE, linha, texto)
    if not n:
        novo = texto.rstrip("\n") + "\n" + linha + "\n"
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(novo)


def main():
    jogos = sorted(glob.glob(os.path.join(RAIZ, "jogos", "pessoais", "PS1", "*.cue")) +
                   glob.glob(os.path.join(RAIZ, "jogos", "pessoais", "PS1", "*.chd")))
    if not jogos:
        print("Sem jogo de PS1 na pasta.")
        return 1
    guarda = tempfile.mkdtemp(prefix="arena_opcao_nucleo_")
    copias = {}
    for arq in (GLOBAL, OPT):
        copias[arq] = os.path.join(guarda, os.path.basename(arq))
        shutil.copy2(arq, copias[arq])
    try:
        trocar(GLOBAL, "3")
        trocar(OPT, "2")
        override = os.path.join(guarda, "override.cfg")
        with open(override, "w", encoding="utf-8") as f:
            f.write('log_dir = "%s"\nlog_to_file = "true"\nlog_verbosity = "true"\n'
                    'frontend_log_level = "0"\nlibretro_log_level = "0"\n'
                    'video_fullscreen = "false"\nconfig_save_on_exit = "false"\n' % guarda)
            # Saves numa pasta temporaria, nunca na de verdade.
            f.write('savefile_directory = "%s"\nsavestate_directory = "%s"\n' % (guarda, guarda))
            if COM_GLOBAL:
                f.write('global_core_options = "true"\ncore_options_path = "%s"\n' % GLOBAL)
        subprocess.run([os.path.join(RA, "retroarch.exe"), "-L", CORE, "--appendconfig", override,
                        "--max-frames", "240", "--verbose", jogos[0]],
                       cwd=RAIZ, capture_output=True, timeout=120)
        logs = glob.glob(os.path.join(guarda, "retroarch__*.log"))
        texto = open(logs[-1], encoding="utf-8", errors="ignore").read() if logs else ""
        linhas = [l.strip() for l in texto.splitlines()
                  if re.search(r"(?i)resolution scale|resolutionscale|core options|\.opt", l)]
        for l in linhas[:15]:
            print("  ", l)
        m = re.search(r'GET_VARIABLE: %s = "(\d+)"' % CHAVE, texto)
        usado = m.group(1) if m else None
        print("\nModo:", "global_core_options = true" if COM_GLOBAL else "padrao do RetroArch")
        print("Escala que o nucleo usou:", usado, "(3 = arquivo do ARENA, 2 = .opt do nucleo)")
        if COM_GLOBAL:
            ok = usado == "3"
            print("RESULTADO:", "PASSOU (o nucleo obedece o ARENA)" if ok else "FALHOU")
            return 0 if ok else 1
        return 0
    finally:
        for arq, copia in copias.items():
            shutil.copy2(copia, arq)
        shutil.rmtree(guarda, ignore_errors=True)
        print("Arquivos de opcoes devolvidos como estavam.")


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import protege_cfg
    sys.exit(protege_cfg.rodar(main))
