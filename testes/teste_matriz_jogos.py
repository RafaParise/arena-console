# -*- coding: utf-8 -*-
"""Fase 5: matriz de jogos -- para cada console com nucleo nativo do
RetroArch que tem jogo na pasta, confere:
  1. Abre e mostra imagem de verdade (--max-frames + --max-frames-ss,
     documentado no --help do proprio RetroArch.exe -- nao inventado).
     A imagem nao pode ser um arquivo vazio/quase vazio (tela preta).
  2. Salvar e carregar estado funciona (--command SAVE_STATE / LOAD_STATE
     via rede local, documentado no command.h do codigo-fonte do
     RetroArch -- precisa de network_cmd_enable=true no override).

Controle com botao de verdade e FPS continuo ficam pro roteiro manual
(mesma limitacao ja reconhecida no plano: sem jeito confiavel de apertar
botao por programa). Cheats ja tem cobertura de sobra na bateria de 44
testes (cheats.py) -- e mecanismo generico do ARENA, nao varia por jogo.

Nao mexe nos saves/states REAIS -- cada jogo roda com savefile_directory/
savestate_directory isolados numa pasta temporaria.
"""
import importlib.util
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RETROARCH = os.path.join(RAIZ, "retroarch", "retroarch.exe")
PORTA_COMANDO = 55355

sys.path.insert(0, os.path.join(RAIZ, "servidor"))
spec_a = importlib.util.spec_from_file_location("arena_matriz", os.path.join(RAIZ, "servidor", "arena.py"))
arena = importlib.util.module_from_spec(spec_a)
spec_a.loader.exec_module(arena)

JOGOS = [
    ("Nintendo 64", "mupen64plus_next_libretro.dll",
     os.path.join(RAIZ, "jogos", "pessoais", "Nintendo 64", "Bomberman 64 (USA).n64")),
    ("Super Nintendo", "snes9x_libretro.dll",
     os.path.join(RAIZ, "jogos", "pessoais", "Super Nintendo",
                 "Super Bomberman 4 (Japan) [T-En by Svambo v1.0].sfc")),
    ("PlayStation", "swanstation_libretro.dll",
     os.path.join(RAIZ, "jogos", "pessoais", "PS1", "CTR - Crash Team Racing (USA).bin")),
    ("Dreamcast", "flycast_libretro.dll",
     os.path.join(RAIZ, "jogos", "pessoais", "Dreamcast", "Marvel vs. Capcom 2 (USA).cue")),
    ("Neo Geo", "fbneo_libretro.dll",
     os.path.join(RAIZ, "jogos", "pessoais", "Neo Geo", "kof97.zip")),
    ("PSP", "ppsspp_libretro.dll",
     os.path.join(RAIZ, "jogos", "pessoais", "PSP",
                 "Killzone - Liberation (USA) (En,Fr,De,Es,It,Nl,Pl,Ru).iso")),
]


def montar_override(destino_cfg, pasta_instancia):
    config = arena.config_padrao()
    opcoes = arena.opcoes_efetivas(config)
    for chave in ("saves", "states"):
        os.makedirs(os.path.join(pasta_instancia, chave), exist_ok=True)
    opcoes["savefile_directory"] = os.path.join(pasta_instancia, "saves")
    opcoes["savestate_directory"] = os.path.join(pasta_instancia, "states")
    opcoes["system_directory"] = os.path.join(RAIZ, "retroarch", "system")
    opcoes["cache_directory"] = pasta_instancia
    opcoes["playlist_directory"] = pasta_instancia
    opcoes["log_dir"] = pasta_instancia
    opcoes["log_to_file"] = "true"
    opcoes["log_verbosity"] = "true"
    opcoes["frontend_log_level"] = "0"
    opcoes["video_fullscreen"] = "false"
    opcoes["menu_driver"] = "rgui"
    opcoes["network_cmd_enable"] = "true"
    opcoes["network_cmd_port"] = str(PORTA_COMANDO)
    # Revisao pos-auditoria: as opcoes de nucleo do ARENA so passaram a valer
    # com global_core_options ligado. A matriz agora abre cada jogo com
    # EXATAMENTE essas opcoes (geradas pela nota desta maquina), numa copia
    # temporaria do arquivo -- o de verdade nao e' tocado.
    import graficos
    opcoes_nucleo = os.path.join(pasta_instancia, "retroarch-core-options.cfg")
    original = graficos.ARQUIVO_OPCOES_CORE
    graficos.ARQUIVO_OPCOES_CORE = opcoes_nucleo
    try:
        graficos.gravar_opcoes_dos_nucleos(
            arena.CAPACIDADE["nota"], graficos.opcoes_de_memory_card("", "ps1"),
            arena.CAPACIDADE.get("nota_gpu"), bool(config.get("modo_modesto")))
    finally:
        graficos.ARQUIVO_OPCOES_CORE = original
    opcoes["global_core_options"] = "true"
    opcoes["core_options_path"] = opcoes_nucleo
    # O RetroArch nao grava a configuracao ao fechar: se este teste for
    # morto no meio (aconteceu por falta de memoria), o protege_cfg nao chega
    # a devolver o retroarch.cfg, e as pastas temporarias ficariam nele.
    opcoes["config_save_on_exit"] = "false"
    linhas = ["# teste matriz de jogos"] + ['%s = "%s"' % (c, opcoes[c]) for c in sorted(opcoes)]
    with open(destino_cfg, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n")


def enviar_comando(texto):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.sendto(texto.encode("ascii"), ("127.0.0.1", PORTA_COMANDO))
    s.close()


def testar_jogo(console, core_nome, caminho_jogo):
    resultado = {"console": console, "jogo": os.path.basename(caminho_jogo)}
    if not os.path.isfile(caminho_jogo):
        resultado["erro"] = "arquivo nao encontrado"
        return resultado

    core = os.path.join(RAIZ, "retroarch", "cores", core_nome)
    raiz_teste = tempfile.mkdtemp(prefix="arena_matriz_")
    try:
        # ---- 1. abre e mostra imagem (max-frames + screenshot) ----
        pasta1 = os.path.join(raiz_teste, "imagem")
        os.makedirs(pasta1, exist_ok=True)
        cfg1 = os.path.join(pasta1, "override.cfg")
        montar_override(cfg1, pasta1)
        caminho_print = os.path.join(pasta1, "captura.png")
        comando = [RETROARCH, "-L", core, "--appendconfig", cfg1,
                  "--max-frames=180", "--max-frames-ss",
                  "--max-frames-ss-path=" + caminho_print, caminho_jogo]
        try:
            subprocess.run(comando, cwd=RAIZ, stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL, timeout=30)
        except subprocess.TimeoutExpired:
            resultado["abre_e_mostra_imagem"] = False
            resultado["motivo_imagem"] = "nao saiu sozinho em 30s (travou ou nao respeitou max-frames)"
        else:
            existe = os.path.isfile(caminho_print)
            tamanho = os.path.getsize(caminho_print) if existe else 0
            resultado["abre_e_mostra_imagem"] = existe and tamanho > 2000
            resultado["tamanho_captura_bytes"] = tamanho

        # ---- 2. salvar e carregar estado ----
        pasta2 = os.path.join(raiz_teste, "estado")
        os.makedirs(pasta2, exist_ok=True)
        cfg2 = os.path.join(pasta2, "override.cfg")
        montar_override(cfg2, pasta2)
        log2 = open(os.path.join(pasta2, "stdout.log"), "w")
        processo = subprocess.Popen([RETROARCH, "-L", core, "--appendconfig", cfg2, caminho_jogo],
                                    cwd=RAIZ, stdout=log2, stderr=subprocess.STDOUT)
        time.sleep(6)

        def arquivos_de_estado():
            # O RetroArch grava dentro de uma subpasta POR NUCLEO
            # (states/<Nome do nucleo>/...), nao direto em states/ --
            # achado ao depurar esta mesma checagem: a comparacao rasa
            # (so o topo da pasta) nunca via a subpasta como "nova"
            # porque ela ja existia antes do SAVE_STATE, mesmo sem
            # arquivo .state dentro ainda. Por isso ista anda a pasta
            # inteira, recursivo.
            pasta_states = os.path.join(pasta2, "states")
            achados = {}
            for atual, _sub, arquivos in os.walk(pasta_states):
                for nome in arquivos:
                    caminho = os.path.join(atual, nome)
                    achados[caminho] = os.path.getsize(caminho)
            return achados

        antes = arquivos_de_estado()
        enviar_comando("SAVE_STATE")
        time.sleep(3)
        depois = arquivos_de_estado()
        criou_estado = any(
            depois.get(c, 0) > antes.get(c, -1) for c in depois) or len(set(depois) - set(antes)) > 0
        resultado["salva_estado"] = criou_estado

        enviar_comando("LOAD_STATE")
        time.sleep(2)
        resultado["carrega_sem_travar"] = processo.poll() is None

        processo.terminate()
        time.sleep(1.5)
        if processo.poll() is None:
            processo.kill()
        log2.close()

        return resultado
    finally:
        shutil.rmtree(raiz_teste, ignore_errors=True)


def main():
    resultados = []
    for console, core, jogo in JOGOS:
        print("\n=== %s: %s ===" % (console, os.path.basename(jogo)))
        r = testar_jogo(console, core, jogo)
        print("  ", r)
        resultados.append(r)

    print("\n\n--- RESUMO ---")
    for r in resultados:
        print(" ", r)

    import json
    with open(os.path.join(RAIZ, "docs", "matriz_jogos_bruto.json"), "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    # Devolve o retroarch.cfg real como estava (o RetroArch grava ao
    # fechar, e levaria junto as pastas temporarias deste teste).
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "testes"))
    import protege_cfg
    sys.exit(protege_cfg.rodar(main))
