# -*- coding: utf-8 -*-
r"""Multitap, Fase B: o RetroArch de verdade obedece a COPIA das opcoes de
nucleo que o ARENA aponta no arquivo da partida (core_options_path)?

PS1 e Saturn ligam o adaptador por opcao do nucleo. O ARENA grava uma copia
do arquivo de opcoes com o multitap ligado e aponta a partida para ela. Se o
RetroArch ignorasse esse apontamento, o multitap falharia em silencio.

Prova: abre o CTR (PS1) no PCSX ReARMed por ~5 s (--max-frames), tres vezes:
  1. com a copia e o adaptador na porta 1 -> o nucleo escreve "multitap: 1 0"
     no registro (3 a 5 jogadores);
  2. com a copia e o adaptador nas duas portas -> "multitap: 1 1" (6 a 8
     jogadores; pedido do Rafael, 14/10/2026);
  3. sem apontar nada extra -> o nucleo NAO liga o multitap.
Protege o retroarch.cfg real (testes\protege_cfg.py).

Uso:
    servidor\python\python.exe testes\teste_multitap_opcao_nucleo_real.py
"""
import os
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import graficos  # noqa: E402
import protege_cfg  # noqa: E402
import jogos_de_teste  # noqa: E402  (acha o jogo tambem em subpasta)
import limpeza  # noqa: E402

RETROARCH = os.path.join(RAIZ, "retroarch", "retroarch.exe")
NUCLEO = os.path.join(RAIZ, "retroarch", "cores", "pcsx_rearmed_libretro.dll")
JOGO = (jogos_de_teste.achar("PS1", "CTR - Crash Team Racing (USA).cue")
        or os.path.join(RAIZ, "jogos", "pessoais", "PS1", "CTR - Crash Team Racing (USA).cue"))
NOMES = {None: "sem", "port 1": "uma", "ports 1 and 2": "duas"}


def abrir(pasta, multitap):
    nome = NOMES[multitap]
    log = os.path.join(pasta, "ra_%s.log" % nome)
    linhas = ['config_save_on_exit = "false"', 'network_cmd_enable = "false"',
              'global_core_options = "true"',
              'system_directory = "%s"' % os.path.join(RAIZ, "retroarch", "system"),
              'savefile_directory = "%s"' % pasta, 'savestate_directory = "%s"' % pasta,
              'audio_enable = "false"']
    if multitap:
        # O mesmo caminho do ARENA: copia do arquivo de sempre + o multitap.
        antigo = graficos.ARQUIVO_OPCOES_CORE_PARTIDA
        graficos.ARQUIVO_OPCOES_CORE_PARTIDA = os.path.join(pasta, "opcoes_%s.cfg" % nome)
        try:
            copia = graficos.gravar_opcoes_de_nucleo_da_partida({"pcsx_rearmed_multitap": multitap})
        finally:
            graficos.ARQUIVO_OPCOES_CORE_PARTIDA = antigo
        linhas.append('core_options_path = "%s"' % copia)
    else:
        linhas.append('core_options_path = "%s"' % graficos.ARQUIVO_OPCOES_CORE)
    extra = os.path.join(pasta, "extra_%s.cfg" % nome)
    open(extra, "w", encoding="utf-8").write("\n".join(linhas) + "\n")
    subprocess.run([RETROARCH, "-L", NUCLEO, "--appendconfig", extra, "--verbose",
                    "--log-file", log, "--max-frames", "300", JOGO],
                   cwd=os.path.dirname(RETROARCH), timeout=120)
    return open(log, encoding="utf-8", errors="replace").read() if os.path.exists(log) else ""


def main():
    for caminho in (RETROARCH, NUCLEO, JOGO):
        if not os.path.isfile(caminho):
            print("PULADO: falta %s" % caminho)
            return 0
    pasta = tempfile.mkdtemp(prefix="arena_multitap_real_")
    try:
        uma = abrir(pasta, "port 1")
        duas = abrir(pasta, "ports 1 and 2")
        sem = abrir(pasta, None)
    finally:
        limpeza.apagar_pasta(pasta)     # antes ficava no Temp
    ligou_uma = "multitap: 1 0" in uma
    ligou_duas = "multitap: 1 1" in duas
    ligou_sem = "multitap: 1" in sem
    print("Porta 1:       registro diz 'multitap: 1 0'?", ligou_uma)
    print("Duas portas:   registro diz 'multitap: 1 1'?", ligou_duas)
    print("Sem a copia:   multitap ligado?             ", ligou_sem)
    for texto, nome in ((uma, "uma"), (duas, "duas"), (sem, "sem")):
        for linha in texto.splitlines():
            if "multitap" in linha.lower() or "core options" in linha.lower():
                print("   [%s] %s" % (nome, linha.strip()[:150]))
    ok = ligou_uma and ligou_duas and not ligou_sem
    print("RESULTADO:", "PASSOU" if ok else "FALHOU")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(protege_cfg.rodar(main))
