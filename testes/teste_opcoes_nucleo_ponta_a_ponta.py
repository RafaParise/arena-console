# -*- coding: utf-8 -*-
r"""Revisao pos-auditoria: o ajuste de imagem do ARENA chega ao nucleo?

Monta as opcoes EXATAMENTE como o ARENA faz ao abrir um jogo de PS1
(arena.gravar_override + graficos.gravar_opcoes_dos_nucleos), abre o
RetroArch com elas e confere no log detalhado:
  1. o nucleo usou a escala de resolucao que o ARENA escreveu (e nao a do
     SwanStation.opt, que agora tem um valor diferente de proposito);
  2. uma opcao que "o aluno mudou" (so no .opt, fora do controle do ARENA)
     continua valendo;
  3. o memory card continua um por jogo ("Libretro"), como os saves de hoje.
Devolve retroarch.cfg, retroarch-core-options.cfg e SwanStation.opt como
estavam.
"""
import glob
import importlib.util
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
ESCALA = "swanstation_GPU_ResolutionScale"
DO_ALUNO = "swanstation_Display_ShowOSDMessages"  # o ARENA nao ajusta esta


def valor_no_log(texto, chave):
    achados = re.findall(r'GET_VARIABLE: %s = "([^"]*)"' % re.escape(chave), texto)
    return achados[-1] if achados else None


def main():
    # Tambem em subpasta e em .chd: os jogos de PS1 desta pasta passaram a
    # ficar assim (01/10/2026) e o teste dizia "sem jogo" e reprovava.
    pasta_ps1 = os.path.join(RAIZ, "jogos", "pessoais", "PS1")
    jogos = sorted(glob.glob(os.path.join(pasta_ps1, "**", "*.cue"), recursive=True)
                   + glob.glob(os.path.join(pasta_ps1, "**", "*.chd"), recursive=True))
    if not jogos:
        print("Sem jogo de PS1 na pasta: nada a testar.")
        return 0
    guarda = tempfile.mkdtemp(prefix="arena_opcoes_e2e_")
    copias = {}
    for arq in (GLOBAL, OPT):
        copias[arq] = os.path.join(guarda, os.path.basename(arq))
        shutil.copy2(arq, copias[arq])
    try:
        # "O aluno" mudou uma opcao pelo menu (so existe no .opt), e o .opt
        # tem uma escala velha diferente da do ARENA.
        with open(OPT, encoding="utf-8") as f:
            texto_opt = f.read()
        texto_opt = re.sub(r'(?m)^%s = ".*"$' % ESCALA, '%s = "7"' % ESCALA, texto_opt)
        with open(OPT, "w", encoding="utf-8") as f:
            f.write(texto_opt)
        # Com global_core_options ligado, e' no arquivo global que o
        # RetroArch grava o que o aluno muda no menu -- entao e' la que a
        # "mudanca do aluno" vai, e o ARENA precisa mante-la.
        with open(GLOBAL, encoding="utf-8") as f:
            texto_global = f.read()
        texto_global = re.sub(r'(?m)^%s = ".*"\n' % DO_ALUNO, "", texto_global)
        texto_global += '%s = "false"\n' % DO_ALUNO
        with open(GLOBAL, "w", encoding="utf-8") as f:
            f.write(texto_global)

        sys.path.insert(0, os.path.join(RAIZ, "servidor"))
        spec = importlib.util.spec_from_file_location("arena_e2e", os.path.join(RAIZ, "servidor", "arena.py"))
        arena = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(arena)
        import graficos

        config = arena.carregar_config()
        extras = graficos.opcoes_de_memory_card(arena.PASTA_SAVES, "ps1")
        graficos.gravar_opcoes_dos_nucleos(arena.CAPACIDADE["nota"], extras,
                                           arena.CAPACIDADE.get("nota_gpu"), False)
        esperado = graficos._ler_opcoes(GLOBAL).get(ESCALA)
        override = arena.gravar_override(config)

        log_cfg = os.path.join(guarda, "log.cfg")
        with open(log_cfg, "w", encoding="utf-8") as f:
            f.write('log_dir = "%s"\nlog_to_file = "true"\nlog_verbosity = "true"\n'
                    'frontend_log_level = "0"\nlibretro_log_level = "0"\n'
                    'video_fullscreen = "false"\nconfig_save_on_exit = "false"\n' % guarda)
            # Saves e estados numa pasta temporaria: sem isto o teste criava
            # um cartao de memoria vazio na pasta de saves de verdade.
            f.write('savefile_directory = "%s"\nsavestate_directory = "%s"\n' % (guarda, guarda))
        subprocess.run([os.path.join(RA, "retroarch.exe"), "-L", CORE,
                        "--appendconfig", override + "|" + log_cfg,
                        "--max-frames", "240", "--verbose", jogos[0]],
                       cwd=RAIZ, capture_output=True, timeout=120)
        logs = glob.glob(os.path.join(guarda, "retroarch__*.log"))
        texto = open(logs[-1], encoding="utf-8", errors="ignore").read() if logs else ""

        usado = valor_no_log(texto, ESCALA)
        aluno = valor_no_log(texto, DO_ALUNO)
        cartao = valor_no_log(texto, "swanstation_MemoryCards_Card1Type")
        print("Escala: ARENA escreveu %s, .opt tinha 7, nucleo usou %s" % (esperado, usado))
        print("Opcao do aluno (%s): nucleo usou %s (esperado false)" % (DO_ALUNO, aluno))
        print("Memory card: %s (esperado Libretro)" % cartao)
        ok = usado == esperado and usado != "7" and aluno == "false" and cartao == "Libretro"
        print("\nRESULTADO:", "PASSOU" if ok else "FALHOU")
        return 0 if ok else 1
    finally:
        for arq, copia in copias.items():
            shutil.copy2(copia, arq)
        shutil.rmtree(guarda, ignore_errors=True)
        print("Arquivos de opcoes devolvidos como estavam.")


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import protege_cfg
    sys.exit(protege_cfg.rodar(main))
