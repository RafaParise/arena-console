# -*- coding: utf-8 -*-
"""Fase 4: o Jogar Junto (SNES, Super Bomberman 4) passando pelo simulador
de rede ruim (proxy_rede_ruim.py), em varios niveis de atraso e perda, e o
que o jogador sente: quanto tempo o convidado leva para entrar, o ping que
o RetroArch mede, e a que velocidade a partida anda nos dois computadores
(quadros por segundo, lidos do titulo da janela do RetroArch: 60 = normal).

Auditoria 3 (08/10/2026): ate aqui o convidado NUNCA passou pelo
simulador. O RetroArch ignora o "--port" da linha de comando, e a chave do
arquivo ia com o nome errado ("netplay_port"); o convidado caia direto no
hospedeiro, na 55435 -- por isso o ping ficava em ~11 ms com 200 ms de
atraso pedido. Agora a porta vai na chave certa (netplay_ip_port), e o
teste confere que o simulador recebeu a conexao (senao, reprova).

Limite (vai para o roteiro de sala): os jogadores ficam parados -- sem
botao apertado, o "volta no tempo" do Jogar Junto (rollback) quase nao
trabalha. O soluco de quando os dois apertam ao mesmo tempo so a sala mede.
"""
import ctypes
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from ctypes import wintypes

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOGO = os.path.join(RAIZ, "jogos", "pessoais", "Super Nintendo",
                    "Super Bomberman 4 (Japan) [T-En by Svambo v1.0].sfc")
RETROARCH = os.path.join(RAIZ, "retroarch", "retroarch.exe")
CORE = os.path.join(RAIZ, "retroarch", "cores", "snes9x_libretro.dll")
PYTHON = os.path.join(RAIZ, "servidor", "python", "python.exe")
PORTA_HOST = 55435
SEGUNDOS_MEDINDO = 12

sys.path.insert(0, os.path.join(RAIZ, "servidor"))
spec_a = importlib.util.spec_from_file_location("arena_rede_ruim", os.path.join(RAIZ, "servidor", "arena.py"))
arena = importlib.util.module_from_spec(spec_a)
spec_a.loader.exec_module(arena)
graficos = arena.graficos

user32 = ctypes.WinDLL("user32", use_last_error=True)
_PROCURAR = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]


def fps_e_quadros(pid):
    """O titulo da janela do RetroArch: "... || FPS:  60.00 || Quadros: 256"."""
    achado = []

    def cada(hwnd, _):
        dono = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(dono))
        if dono.value == pid:
            texto = ctypes.create_unicode_buffer(512)
            user32.GetWindowTextW(hwnd, texto, 512)
            m = re.search(r"FPS:\s*([\d.]+)\s*\|\|\s*\w+:\s*(\d+)", texto.value)
            if m:
                achado.append((float(m.group(1)), int(m.group(2))))
        return True
    user32.EnumWindows(_PROCURAR(cada), 0)
    return achado[0] if achado else None


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
    # O FPS e os quadros no titulo da janela, atualizados a cada meio segundo.
    opcoes["fps_show"] = "true"
    opcoes["framecount_show"] = "true"
    opcoes["fps_update_interval"] = "30"
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


def medir_velocidade(processos, segundos):
    """Quadros por segundo de verdade em cada processo (quadros andados /
    tempo) e o menor FPS que o titulo mostrou."""
    primeiro, ultimo, menor = {}, {}, {}
    fim = time.monotonic() + segundos
    while time.monotonic() < fim:
        agora = time.monotonic()
        for nome, processo in processos.items():
            lido = fps_e_quadros(processo.pid)
            if lido:
                fps, quadros = lido
                primeiro.setdefault(nome, (agora, quadros))
                ultimo[nome] = (agora, quadros)
                menor[nome] = min(menor.get(nome, 999.0), fps)
        time.sleep(0.25)
    velocidade = {}
    for nome in processos:
        if nome in primeiro and ultimo[nome][0] > primeiro[nome][0]:
            (t0, q0), (t1, q1) = primeiro[nome], ultimo[nome]
            velocidade[nome] = round((q1 - q0) / (t1 - t0), 1)
        else:
            velocidade[nome] = None
    return velocidade, {n: round(v, 1) for n, v in menor.items()}


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

        if entrou_em is not None:
            velocidade, menor_fps = medir_velocidade({"hospedeiro": p_host, "convidado": p_conv},
                                                     SEGUNDOS_MEDINDO)
            resultado["quadros_por_segundo"] = velocidade
            resultado["menor_fps_no_titulo"] = menor_fps

        texto_host = ler_log(pasta_host).lower()
        texto_conv = ler_log(pasta_convidado).lower()
        ping_m = re.search(r"ping:\s*(\d+)\s*ms", texto_host)
        resultado["ping_ms"] = int(ping_m.group(1)) if ping_m else None
        resultado["desconectou"] = bool(re.search(r"desconect|disconnect", texto_host))
        # Dessincronia: o RetroArch confere o estado dos dois de tempos em
        # tempos (netplay_check_frames) e avisa quando difere.
        resultado["avisos_de_dessincronia"] = len(re.findall(
            r"crcs? mismatch|prepare for desync|dessincron", texto_host + texto_conv))

        if com_simulador:
            proxy_saida.flush()
            with open(os.path.join(raiz_teste, "proxy.log"), encoding="utf-8", errors="replace") as f:
                registro_proxy = f.read()
            resultado["passou_pelo_simulador"] = "nova conexao aceita" in registro_proxy
            contagens = re.findall(r"\[proxy\] pedacos: (\{.*\})", registro_proxy)
            resultado["pedacos_no_simulador"] = contagens[-1] if contagens else ""

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
    referencia = resultados[0]
    if not referencia.get("conectou"):
        falhas.append("sem simulador, o convidado nao entrou")
    for r in resultados[1:]:
        if not r.get("passou_pelo_simulador"):
            falhas.append("%s: o convidado NAO passou pelo simulador" % r["cenario"])
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
