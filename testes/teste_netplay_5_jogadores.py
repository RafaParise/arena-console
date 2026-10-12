# -*- coding: utf-8 -*-
"""Fase 4: "Jogar Junto" com 5 jogadores (Multitap) -- Super Bomberman 4
(SNES), 1 hospedeiro + 4 convidados, todos no mesmo computador.

O ARENA de producao so deixa UM RetroArch local por vez (TRAVA_JOGO) --
correto pra uso normal, mas significa que este teste nao pode passar
pelas rotas HTTP do /api/jogar cinco vezes seguidas. Em vez disso, chama
as MESMAS funcoes que o /api/jogar usa por baixo
(graficos.opcoes_de_partida, graficos.argumentos_de_partida,
arena.opcoes_efetivas) diretamente, uma vez por "jogador", cada um com:
  - arquivo de configuracao (--appendconfig) proprio;
  - pasta de saves/states/system propria;
  - o mesmo jogo real, retroarch.exe real, nucleo real.

Abre 5 janelas de verdade do RetroArch (nao da pra testar netplay sem
isso -- nao existe modo sem tela). Fecha todas ao final.

Nao mexe em dados\\, retroarch\\saves, retroarch\\states nem no
arena_override.cfg real -- cada instancia de teste usa sua propria copia
isolada dessas pastas dentro de uma pasta temporaria.
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jogos_de_teste  # noqa: E402
import limpeza  # noqa: E402

JOGO = jogos_de_teste.achar("Super Nintendo", "Super Bomberman 4 (Japan) [T-En by Svambo v1.0].sfc") or ""
RETROARCH = os.path.join(RAIZ, "retroarch", "retroarch.exe")
CORE = os.path.join(RAIZ, "retroarch", "cores", "snes9x_libretro.dll")
PORTA_PARTIDA = 55435


def carregar_modulos():
    sys.path.insert(0, os.path.join(RAIZ, "servidor"))
    spec_a = importlib.util.spec_from_file_location("arena_5j", os.path.join(RAIZ, "servidor", "arena.py"))
    arena = importlib.util.module_from_spec(spec_a)
    spec_a.loader.exec_module(arena)
    return arena, arena.graficos


def montar_override(destino_cfg, pasta_instancia, arena, graficos, opcoes_partida):
    """Mesma logica de arena.gravar_override(), mas escrevendo num
    arquivo E em pastas de saves/states PROPRIAS desta instancia de
    teste -- nunca nas pastas reais do ARENA."""
    config = arena.config_padrao()
    opcoes = arena.opcoes_efetivas(config)
    opcoes.update(opcoes_partida)

    for chave in ("saves", "states", "system", "capturas"):
        os.makedirs(os.path.join(pasta_instancia, chave), exist_ok=True)

    opcoes["savefile_directory"] = os.path.join(pasta_instancia, "saves")
    opcoes["savestate_directory"] = os.path.join(pasta_instancia, "states")
    opcoes["screenshot_directory"] = os.path.join(pasta_instancia, "capturas")
    opcoes["system_directory"] = os.path.join(RAIZ, "retroarch", "system")
    opcoes["cache_directory"] = os.path.join(pasta_instancia, "cache")
    opcoes["playlist_directory"] = pasta_instancia
    opcoes["log_dir"] = pasta_instancia
    opcoes["log_to_file"] = "true"
    opcoes["log_verbosity"] = "true"
    opcoes["frontend_log_level"] = "0"
    opcoes["video_fullscreen"] = "false"
    opcoes["menu_driver"] = "rgui"

    linhas = ["# Gerado pelo teste de auditoria. Nao e o override real do ARENA."]
    linhas += ['%s = "%s"' % (c, opcoes[c]) for c in sorted(opcoes)]
    with open(destino_cfg, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n")
    return destino_cfg


def powershell(comando):
    r = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", comando],
                       capture_output=True, text=True, timeout=15)
    return r.stdout.strip()


def medir_processo(pid):
    saida = powershell(
        "Get-Process -Id %d -ErrorAction SilentlyContinue | "
        "Select-Object WorkingSet64, @{n='CPU';e={$_.CPU}} | ConvertTo-Json" % pid)
    if not saida:
        return None
    return json.loads(saida)


def esperar_conexao(caminho_pasta, apelido_esperado, tempo_limite=20.0):
    """Sonda o log de verdade do RetroArch ate ver 'apelido se juntou' ou
    estourar o tempo limite. Devolve o tempo (s) ate aparecer, ou None."""
    inicio = time.monotonic()
    alvo = ("%s se juntou" % apelido_esperado).lower()
    while time.monotonic() - inicio < tempo_limite:
        candidatos = [n for n in os.listdir(caminho_pasta)
                      if n.startswith("retroarch__") and n.endswith(".log")]
        if candidatos:
            try:
                with open(os.path.join(caminho_pasta, sorted(candidatos)[-1]),
                          "r", encoding="utf-8", errors="ignore") as f:
                    texto = f.read().lower()
                if alvo in texto:
                    return round(time.monotonic() - inicio, 2)
            except OSError:
                pass
        time.sleep(0.3)
    return None


def main():
    if not os.path.isfile(JOGO):
        print("[ERRO] Jogo nao encontrado:", JOGO)
        return 1

    arena, graficos = carregar_modulos()

    raiz_teste = tempfile.mkdtemp(prefix="arena_netplay5_")
    print("Pasta de teste:", raiz_teste)

    papeis = [
        {"nome": "hospedeiro", "hospedar": True, "jogador": 1, "apelido": "Anfitriao"},
        {"nome": "convidado2", "hospedar": False, "jogador": 2, "apelido": "Jogador2"},
        {"nome": "convidado3", "hospedar": False, "jogador": 3, "apelido": "Jogador3"},
        {"nome": "convidado4", "hospedar": False, "jogador": 4, "apelido": "Jogador4"},
        {"nome": "convidado5", "hospedar": False, "jogador": 5, "apelido": "Jogador5"},
    ]

    processos = []
    pasta_host = None
    tempos_de_entrada = {}
    amostras_host = []
    manter_pasta = True        # erro no meio: os registros ficam para olhar
    try:
        for papel in papeis:
            pasta_instancia = os.path.join(raiz_teste, papel["nome"])
            os.makedirs(pasta_instancia, exist_ok=True)
            if papel["hospedar"]:
                pasta_host = pasta_instancia

            opcoes_partida = graficos.opcoes_de_partida(
                apelido=papel["apelido"], hospedar=papel["hospedar"],
                jogador=papel["jogador"], multitap=True)
            argumentos_partida = graficos.argumentos_de_partida(
                papel["hospedar"], endereco="127.0.0.1", porta=PORTA_PARTIDA)

            cfg = os.path.join(pasta_instancia, "override.cfg")
            montar_override(cfg, pasta_instancia, arena, graficos, opcoes_partida)

            comando = [RETROARCH, "-L", CORE, "--appendconfig", cfg] + argumentos_partida + [JOGO]
            log_saida = open(os.path.join(pasta_instancia, "stdout.log"), "w", encoding="utf-8")
            print("Abrindo %s (jogador %d)..." % (papel["nome"], papel["jogador"]))
            processo = subprocess.Popen(comando, cwd=RAIZ, stdout=log_saida, stderr=subprocess.STDOUT)
            processos.append({"papel": papel, "processo": processo, "pasta": pasta_instancia, "log": log_saida})

            if papel["hospedar"]:
                time.sleep(10)
            else:
                # espera este convidado aparecer no log do HOST (tempo de
                # entrada de verdade, medido do lado de quem mais importa)
                t = esperar_conexao(pasta_host, papel["apelido"], tempo_limite=15.0)
                tempos_de_entrada[papel["nome"]] = t
                print("    entrou em %s" % (("%.2fs" % t) if t is not None else "NAO ENTROU (>15s)"))
                info = medir_processo(processos[0]["processo"].pid)
                if info:
                    amostras_host.append({
                        "apos": papel["nome"],
                        "ram_mb": round(info["WorkingSet64"] / (1024 * 1024), 1),
                        "cpu_s": info.get("CPU"),
                    })
                time.sleep(2)

        print("\nEsperando estabilizar (10s)...")
        time.sleep(10)

        print("\n--- Estado dos processos ---")
        vivos = 0
        for p in processos:
            rodando = p["processo"].poll() is None
            vivos += rodando
            print("  %-12s pid=%s vivo=%s" % (p["papel"]["nome"], p["processo"].pid, rodando))

        # fecha os logs pra poder ler o conteudo
        for p in processos:
            p["log"].flush()

        print("\n--- Procurando evidencia de conexao nos logs ---")
        achados = {}
        for p in processos:
            # O RetroArch grava o log de verdade num arquivo proprio
            # (log_dir + log_to_file_timestamp), nao no stdout do processo.
            candidatos = [n for n in os.listdir(p["pasta"]) if n.startswith("retroarch__") and n.endswith(".log")]
            texto = ""
            if candidatos:
                caminho_log = os.path.join(p["pasta"], sorted(candidatos)[-1])
                try:
                    with open(caminho_log, "r", encoding="utf-8", errors="ignore") as f:
                        texto = f.read()
                except OSError:
                    pass
            linhas_relevantes = [l.strip() for l in texto.splitlines() if "[netplay]" in l.lower()]
            achados[p["papel"]["nome"]] = linhas_relevantes
            print("  %s:" % p["papel"]["nome"])
            for l in linhas_relevantes:
                print("      ", l)

        print("\n--- Tempo de entrada de cada convidado (medido no log do host) ---")
        for nome, t in tempos_de_entrada.items():
            print("  %-12s %s" % (nome, ("%.2fs" % t) if t is not None else "NAO ENTROU"))

        print("\n--- RAM/CPU do hospedeiro, a cada convidado que tentou entrar ---")
        for a in amostras_host:
            print("  apos %-12s RAM=%.1f MB  CPU=%ss" % (a["apos"], a["ram_mb"], a["cpu_s"]))

        destino_relatorio = os.path.join(RAIZ, "docs", "netplay_5_jogadores_bruto.json")
        with open(destino_relatorio, "w", encoding="utf-8") as f:
            json.dump({"processos_vivos": vivos, "de_5": len(papeis), "logs": achados,
                      "tempos_de_entrada_s": tempos_de_entrada, "amostras_host": amostras_host},
                      f, ensure_ascii=False, indent=2)
        print("Resumo salvo em", destino_relatorio)

        # Corrigido na revisao pos-auditoria: antes devolvia 0 SEMPRE, e a
        # rodada final contava como "passou" mesmo com um convidado de fora.
        faltaram = [n for n, t in tempos_de_entrada.items() if t is None]
        ok = not faltaram and vivos == len(papeis)
        # Os registros de cada instancia so ficam quando falha (para ver o
        # porque); passou, a pasta sai -- regra 6 da auditoria 3 (a rodada
        # achava esta pasta esquecida no Temp a cada vez).
        manter_pasta = not ok
        if manter_pasta:
            print("\nRegistros completos de cada instancia guardados em", raiz_teste,
                  "(apague a pasta depois de olhar).")
        print("\nRESULTADO:", "PASSOU (os %d convidados entraram)" % len(tempos_de_entrada)
              if ok else "FALHOU (nao entraram: %s)" % (", ".join(faltaram) or "-"))
        return 0 if ok else 1
    finally:
        print("\nEncerrando os 5 processos...")
        for p in processos:
            try:
                p["processo"].terminate()
            except Exception:
                pass
        time.sleep(2)
        for p in processos:
            try:
                if p["processo"].poll() is None:
                    p["processo"].kill()
            except Exception:
                pass
            try:
                p["log"].close()
            except Exception:
                pass
        if not manter_pasta:
            limpeza.apagar_pasta(raiz_teste)


if __name__ == "__main__":
    # Devolve o retroarch.cfg real como estava (o RetroArch grava ao
    # fechar, e levaria junto as pastas temporarias deste teste).
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "testes"))
    import protege_cfg
    sys.exit(protege_cfg.rodar(main))
