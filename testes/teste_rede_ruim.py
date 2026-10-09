# -*- coding: utf-8 -*-
"""Fase 4: o Jogar Junto (SNES, Super Bomberman 4) passando pelo simulador
de rede ruim (proxy_rede_ruim.py), em varios niveis de atraso e perda:
o convidado entra? quanto tempo leva? que ping o RetroArch mede? a conexao
cai depois de entrar?

Auditoria 3 (08/10/2026): ate aqui o convidado NUNCA passou pelo
simulador. O RetroArch ignora o "--port" da linha de comando, e a chave do
arquivo ia com o nome errado ("netplay_port"); o convidado caia direto no
hospedeiro, na 55435 -- por isso o ping ficava em ~11 ms com 200 ms de
atraso pedido. Agora a porta vai na chave certa (netplay_ip_port).

Revisao da Fase 4 (09/10/2026): o teste reprova se um cenario nao conectar,
ou se o simulador nao repassou dados NOS DOIS SENTIDOS (so aceitar a
conexao nao prova que a partida passou por ele). E saiu daqui o que nao
provava nada: o FPS do titulo da janela (enquanto o Jogar Junto espera a
rede, o RetroArch redesenha o ultimo quadro, e o contador continua em 60)
e a contagem de "dessincronia" (com netplay_check_frames positivo, o
RetroArch corrige a diferenca calado, sem escrever no registro).

Limite (vai para o roteiro de sala): os jogadores ficam parados -- sem
botao apertado, o "volta no tempo" do Jogar Junto (rollback) quase nao
trabalha. O que o jogador sente com os botoes, so a sala mede.
"""
import ast
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOGO = os.path.join(RAIZ, "jogos", "pessoais", "Super Nintendo",
                    "Super Bomberman 4 (Japan) [T-En by Svambo v1.0].sfc")
RETROARCH = os.path.join(RAIZ, "retroarch", "retroarch.exe")
CORE = os.path.join(RAIZ, "retroarch", "cores", "snes9x_libretro.dll")
PYTHON = os.path.join(RAIZ, "servidor", "python", "python.exe")
PORTA_HOST = 55435
SEGUNDOS_JOGANDO = 12

sys.path.insert(0, os.path.join(RAIZ, "servidor"))
spec_a = importlib.util.spec_from_file_location("arena_rede_ruim", os.path.join(RAIZ, "servidor", "arena.py"))
arena = importlib.util.module_from_spec(spec_a)
spec_a.loader.exec_module(arena)
graficos = arena.graficos


def montar_override(destino_cfg, pasta_instancia, opcoes_partida):
    config = arena.config_padrao()
    opcoes = arena.opcoes_efetivas(config)
    opcoes.update(opcoes_partida)
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
    opcoes["config_save_on_exit"] = "false"
    linhas = ["# teste rede ruim"] + ['%s = "%s"' % (c, opcoes[c]) for c in sorted(opcoes)]
    with open(destino_cfg, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n")


def abrir(pasta_instancia, hospedar, jogador, apelido, porta_conexao):
    os.makedirs(pasta_instancia, exist_ok=True)
    opcoes_partida = graficos.opcoes_de_partida(apelido=apelido, hospedar=hospedar, jogador=jogador)
    # A porta vale pelo arquivo (o "--port" da linha de comando e' ignorado).
    opcoes_partida["netplay_ip_port"] = str(porta_conexao)
    argumentos_partida = graficos.argumentos_de_partida(hospedar, endereco="127.0.0.1", porta=porta_conexao)
    cfg = os.path.join(pasta_instancia, "override.cfg")
    montar_override(cfg, pasta_instancia, opcoes_partida)
    comando = [RETROARCH, "-L", CORE, "--appendconfig", cfg] + argumentos_partida + [JOGO]
    log = open(os.path.join(pasta_instancia, "stdout.log"), "w")
    processo = subprocess.Popen(comando, cwd=RAIZ, stdout=log, stderr=subprocess.STDOUT)
    return processo, log


def ler_log(pasta):
    candidatos = [n for n in os.listdir(pasta) if n.startswith("retroarch__") and n.endswith(".log")]
    if not candidatos:
        return ""
    with open(os.path.join(pasta, sorted(candidatos)[-1]), "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def pedacos_do_simulador(registro):
    """A ultima contagem que o simulador imprimiu: {sentido: pedacos}."""
    contagens = re.findall(r"\[proxy\] pedacos: (\{.*\})", registro)
    try:
        return ast.literal_eval(contagens[-1]) if contagens else {}
    except (ValueError, SyntaxError):
        return {}


def rodar_cenario(nome, atraso_ms, perda_pct, porta_proxy):
    com_simulador = porta_proxy is not None
    print("\n=== Cenario: %s (atraso=%dms, perda=%.0f%%) ===" % (nome, atraso_ms, perda_pct))
    raiz_teste = tempfile.mkdtemp(prefix="arena_rede_ruim_")
    proxy = proxy_saida = None
    processos = []
    resultado = {"cenario": nome, "atraso_ms": atraso_ms, "perda_pct": perda_pct,
                 "com_simulador": com_simulador}
    try:
        if com_simulador:
            proxy_saida = open(os.path.join(raiz_teste, "proxy.log"), "w")
            proxy = subprocess.Popen(
                [PYTHON, os.path.join(RAIZ, "testes", "proxy_rede_ruim.py"),
                 str(porta_proxy), "127.0.0.1", str(PORTA_HOST), str(atraso_ms), str(perda_pct)],
                cwd=RAIZ, stdout=proxy_saida, stderr=subprocess.STDOUT)
            time.sleep(1)

        pasta_host = os.path.join(raiz_teste, "host")
        p_host, log_host = abrir(pasta_host, True, 1, "Anfitriao", PORTA_HOST)
        processos.append((p_host, log_host))
        time.sleep(6)

        pasta_convidado = os.path.join(raiz_teste, "convidado")
        inicio = time.monotonic()
        p_conv, log_conv = abrir(pasta_convidado, False, 2, "Convidado",
                                 porta_proxy if com_simulador else PORTA_HOST)
        processos.append((p_conv, log_conv))

        entrou_em = None
        while time.monotonic() - inicio < 40:
            if "se juntou como o jogador 2" in ler_log(pasta_host).lower():
                entrou_em = round(time.monotonic() - inicio, 1)
                break
            time.sleep(0.25)
        resultado["conectou"] = entrou_em is not None
        resultado["entrou_em_s"] = entrou_em

        # Jogando (parados) um tempo, para ver se a conexao aguenta.
        time.sleep(SEGUNDOS_JOGANDO)
        texto_host = ler_log(pasta_host).lower()
        ping_m = re.search(r"ping:\s*(\d+)\s*ms", texto_host)
        resultado["ping_ms"] = int(ping_m.group(1)) if ping_m else None
        resultado["caiu_depois_de_entrar"] = bool(re.search(r"desconect|disconnect", texto_host))
        resultado["os_dois_abertos_no_fim"] = p_host.poll() is None and p_conv.poll() is None

        if com_simulador:
            time.sleep(2.5)            # a proxima contagem do simulador
            proxy_saida.flush()
            with open(os.path.join(raiz_teste, "proxy.log"), encoding="utf-8", errors="replace") as f:
                pedacos = pedacos_do_simulador(f.read())
            resultado["pedacos_no_simulador"] = pedacos
            resultado["passou_pelo_simulador"] = (pedacos.get("cliente->host", 0) > 0
                                                  and pedacos.get("host->cliente", 0) > 0)

        print("  " + json.dumps(resultado, ensure_ascii=False))
        return resultado
    finally:
        for p, log in processos:
            try:
                p.terminate()
            except Exception:
                pass
        time.sleep(1.5)
        for p, log in processos:
            try:
                if p.poll() is None:
                    p.kill()
            except Exception:
                pass
            try:
                log.close()
            except Exception:
                pass
        if proxy:
            proxy.terminate()
            try:
                proxy.wait(timeout=5)
            except Exception:
                proxy.kill()
        if proxy_saida:
            proxy_saida.close()
        time.sleep(0.5)
        shutil.rmtree(raiz_teste, ignore_errors=True)


def main():
    if not os.path.isfile(JOGO):
        print("[ERRO] jogo nao encontrado")
        return 1

    cenarios = [
        ("sem simulador (referencia)", 0, 0, None),
        ("so atraso 50ms", 50, 0, 55440),
        ("so atraso 100ms", 100, 0, 55441),
        ("so atraso 200ms", 200, 0, 55442),
        ("perda 1% (com 50ms de base)", 50, 1, 55443),
        ("perda 5% (com 50ms de base)", 50, 5, 55444),
    ]
    resultados = [rodar_cenario(*c) for c in cenarios]

    print("\n\n--- RESUMO ---")
    for r in resultados:
        print(" ", r)
    with open(os.path.join(RAIZ, "docs", "rede_ruim_bruto.json"), "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    falhas = []
    for r in resultados:
        if not r.get("conectou"):
            falhas.append("%s: o convidado nao entrou" % r["cenario"])
        elif r.get("caiu_depois_de_entrar") or not r.get("os_dois_abertos_no_fim"):
            falhas.append("%s: a partida caiu depois de entrar" % r["cenario"])
        if r["com_simulador"] and not r.get("passou_pelo_simulador"):
            falhas.append("%s: a partida NAO passou pelo simulador nos dois sentidos" % r["cenario"])
    for falha in falhas:
        print("[FALHOU]", falha)
    print("\nRESULTADO:", "PASSOU" if not falhas else "FALHOU")
    return 0 if not falhas else 1


if __name__ == "__main__":
    # Devolve o retroarch.cfg real como estava (o RetroArch grava ao
    # fechar, e levaria junto as pastas temporarias deste teste).
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "testes"))
    import protege_cfg
    sys.exit(protege_cfg.rodar(main))
