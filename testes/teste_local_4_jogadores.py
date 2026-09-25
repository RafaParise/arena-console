# -*- coding: utf-8 -*-
"""Fase 4: multiplayer local (GoldenEye 007, N64) -- confere que a
configuracao de 4 jogadores locais (1 computador so, sem netplay) gera as
4 portas corretas e o jogo abre sem erro com elas. Nao aperta botao
nenhum -- isso fica pro roteiro manual (precisa de controle fisico de
verdade). So confirma que o nucleo aceita a config e nao trava/recusa.
"""
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOGO = os.path.join(RAIZ, "jogos", "pessoais", "Nintendo 64", "GoldenEye 007 (USA).z64")
RETROARCH = os.path.join(RAIZ, "retroarch", "retroarch.exe")
CORE = os.path.join(RAIZ, "retroarch", "cores", "mupen64plus_next_libretro.dll")

sys.path.insert(0, os.path.join(RAIZ, "servidor"))
spec_a = importlib.util.spec_from_file_location("arena_4j", os.path.join(RAIZ, "servidor", "arena.py"))
arena = importlib.util.module_from_spec(spec_a)
spec_a.loader.exec_module(arena)
import controles


def main():
    if not os.path.isfile(JOGO):
        print("[ERRO] Jogo nao encontrado:", JOGO)
        return 1

    raiz_teste = tempfile.mkdtemp(prefix="arena_local4_")
    print("Pasta de teste:", raiz_teste)
    try:
        config = arena.config_padrao()
        opcoes = arena.opcoes_efetivas(config)
        extras = controles.opcoes_do_console("n64", jogadores=4, usar_analogico=True, vibracao=True)
        opcoes.update(extras)
        # Multitap, Fase B: o mesmo calculo do /api/jogar. Sem isto o teste
        # ficava com input_max_users = 2 (padrao do ARENA) e, com um 3o
        # controle fisico ligado, o RetroArch recusava ("No free and
        # unreserved player slots... max_users: 2") -- visto em 25/09/2026.
        # Era exatamente o defeito que a Fase B corrige no ARENA.
        opcoes.update(arena.graficos.jogadores_do_jogo(
            os.path.basename(CORE), 4, config["avancado"]["input_max_users"])["cfg"])

        for chave in ("saves", "states"):
            os.makedirs(os.path.join(raiz_teste, chave), exist_ok=True)
        opcoes["savefile_directory"] = os.path.join(raiz_teste, "saves")
        opcoes["savestate_directory"] = os.path.join(raiz_teste, "states")
        opcoes["system_directory"] = os.path.join(RAIZ, "retroarch", "system")
        opcoes["cache_directory"] = raiz_teste
        opcoes["playlist_directory"] = raiz_teste
        opcoes["log_dir"] = raiz_teste
        opcoes["log_to_file"] = "true"
        opcoes["log_verbosity"] = "true"
        opcoes["frontend_log_level"] = "0"
        opcoes["video_fullscreen"] = "false"
        opcoes["menu_driver"] = "rgui"

        cfg = os.path.join(raiz_teste, "override.cfg")
        linhas = ["# teste local 4 jogadores"] + ['%s = "%s"' % (c, opcoes[c]) for c in sorted(opcoes)]
        with open(cfg, "w", encoding="utf-8") as f:
            f.write("\n".join(linhas) + "\n")

        print("Config gerada -- portas:")
        for n in range(1, 5):
            print("  p%d = %s" % (n, opcoes.get("input_libretro_device_p%d" % n)))

        comando = [RETROARCH, "-L", CORE, "--appendconfig", cfg, JOGO]
        log = open(os.path.join(raiz_teste, "stdout.log"), "w")
        print("\nAbrindo GoldenEye 007 com config de 4 jogadores...")
        processo = subprocess.Popen(comando, cwd=RAIZ, stdout=log, stderr=subprocess.STDOUT)
        time.sleep(8)

        vivo = processo.poll() is None
        print("Processo vivo apos 8s:", vivo)

        candidatos = [n for n in os.listdir(raiz_teste) if n.startswith("retroarch__") and n.endswith(".log")]
        if candidatos:
            with open(os.path.join(raiz_teste, sorted(candidatos)[-1]), "r", encoding="utf-8", errors="ignore") as f:
                texto = f.read()
            # Erro de SOM nao conta: depende de ter caixa/fone ligado na hora
            # (a rodada final da Fase 8 reprovou so por isso, de madrugada,
            # com o Windows sem saida de audio padrao). Nada a ver com os 4
            # controles, que e' o que este teste confere.
            def e_de_som(linha):
                baixo = linha.lower()
                return any(p in baixo for p in ("audio", "áudio", "[midi]", "mmdevice"))
            erros = [l for l in texto.splitlines()
                     if "[error]" in l.lower() and not e_de_som(l)]
            print("Linhas de erro no log:", len(erros))
            for l in erros[:10]:
                print("  ", l.strip())

        processo.terminate()
        time.sleep(1.5)
        if processo.poll() is None:
            processo.kill()
        log.close()

        ok = vivo and not erros
        print("\nRESULTADO:", "PASSOU (abriu sem erro com 4 portas configuradas)" if ok else "FALHOU/PRECISA OLHAR")
        return 0 if ok else 1
    finally:
        shutil.rmtree(raiz_teste, ignore_errors=True)


if __name__ == "__main__":
    # Devolve o retroarch.cfg real como estava (o RetroArch grava ao
    # fechar, e levaria junto as pastas temporarias deste teste).
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "testes"))
    import protege_cfg
    sys.exit(protege_cfg.rodar(main))
