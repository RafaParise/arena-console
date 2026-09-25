# -*- coding: utf-8 -*-
r"""Auditoria 2, Fase 2: o cache de video do PS1 (vulkan_pipelines.bin, ~50 MB
em retroarch\system\swanstation) e' regravado a cada partida?

Se for, sao 50 MB gravados no pen drive toda vez -- desgaste e demora para
fechar o jogo num disco lento. Abre o mesmo jogo de PS1 duas vezes (300
quadros cada) com as opcoes REAIS do ARENA (geradas numa pasta temporaria,
saves temporarios), e compara: data e conteudo do cache antes/depois, e o
tempo de abrir cada vez.

Uso:
    servidor\python\python.exe testes\cache_pipelines_ps1.py
"""
import glob
import hashlib
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(RAIZ, "retroarch", "system", "swanstation", "vulkan_pipelines.bin")
CORE = os.path.join(RAIZ, "retroarch", "cores", "swanstation_libretro.dll")


def resumo():
    if not os.path.isfile(CACHE):
        return None
    with open(CACHE, "rb") as f:
        return os.path.getmtime(CACHE), os.path.getsize(CACHE), hashlib.sha1(f.read()).hexdigest()


def main():
    jogo = (sorted(glob.glob(os.path.join(RAIZ, "jogos", "pessoais", "PS1", "*.cue"))) or [None])[0]
    if not jogo:
        print("Sem jogo de PS1.")
        return 0
    temp = tempfile.mkdtemp(prefix="arena_cache_ps1_")
    try:
        sys.path.insert(0, os.path.join(RAIZ, "servidor"))
        spec = importlib.util.spec_from_file_location("arena_cache", os.path.join(RAIZ, "servidor", "arena.py"))
        arena = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(arena)
        import graficos
        arena.ARQUIVO_OVERRIDE = os.path.join(temp, "override.cfg")
        graficos.ARQUIVO_OPCOES_CORE = os.path.join(temp, "core.cfg")
        config = arena.carregar_config()
        graficos.gravar_opcoes_dos_nucleos(arena.CAPACIDADE["nota"], graficos.opcoes_de_memory_card("", "ps1"),
                                           arena.CAPACIDADE.get("nota_gpu"), bool(config.get("modo_modesto")))
        # Experimento: opcao extra de nucleo, ex. ARENA_TESTE_OPCAO=chave=valor
        teste = os.environ.get("ARENA_TESTE_OPCAO")
        if teste:
            chave, valor = teste.split("=", 1)
            with open(graficos.ARQUIVO_OPCOES_CORE, "a", encoding="utf-8") as f:
                f.write('%s = "%s"\n' % (chave, valor))
            print("com a opcao extra:", teste)
        ovr = arena.gravar_override(config)
        extra = os.path.join(temp, "extra.cfg")
        with open(extra, "w", encoding="utf-8") as f:
            f.write('savefile_directory = "%s"\nsavestate_directory = "%s"\nconfig_save_on_exit = "false"\n'
                    'network_cmd_enable = "false"\n' % (temp, temp))
        antes = resumo()
        print("cache antes:", "nao existe" if not antes else "%.1f MB" % (antes[1] / 1024 ** 2))
        for vez in (1, 2):
            t = time.perf_counter()
            subprocess.run([os.path.join(RAIZ, "retroarch", "retroarch.exe"), "-L", CORE,
                            "--appendconfig", ovr + "|" + extra, "--max-frames=300", jogo],
                           cwd=RAIZ, capture_output=True, timeout=180)
            depois = resumo()
            regravou = antes != depois
            print("vez %d: %.1f s; cache %s%s" % (vez, time.perf_counter() - t,
                  "REGRAVADO (%.1f MB)" % (depois[1] / 1024 ** 2) if regravou else "intocado",
                  "" if not regravou else (", conteudo IGUAL (so regravou)" if antes and antes[2] == depois[2]
                                           else ", conteudo mudou")))
            antes = depois
        return 0
    finally:
        sys.path = [p for p in sys.path if not p.endswith("servidor")]
        shutil.rmtree(temp, ignore_errors=True)


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import protege_cfg
    sys.exit(protege_cfg.rodar(main))
