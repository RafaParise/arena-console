# -*- coding: utf-8 -*-
r"""Fase 5 (auditoria 3): matriz de jogos -- um jogo de CADA console que roda
pelo RetroArch, com as opcoes que o ARENA grava de verdade (gravar_override
e as opcoes de nucleo, numa pasta temporaria), duas vezes: no modo normal e
no modo modesto (grafico igual ao original). Em cada vez confere:

  1. ABRE: os quadros andam (o titulo da janela do RetroArch mostra
     "FPS: 60.00 || Quadros: N", com fps_show + framecount_show);
  2. VELOCIDADE: quadros por segundo de verdade (quadros andados / tempo)
     e o processador do RetroArch (% de UM nucleo), por 8 s;
  3. ESTADO: SAVE_STATE cria o arquivo; LOAD_STATE e o jogo continua vivo;
  4. IMAGEM: foto da tela pelo comando SCREENSHOT (mais de 2 KB) -- depois
     do estado, de proposito: no Dreamcast a foto seguida de salvar derruba
     o nucleo as vezes (achado da Fase 5, no relatorio). Espera a foto
     terminar de ser gravada (ate 10 s): depois de salvar estado, a do PSP
     leva uns 3 s;
  5. SAVE DO JOGO: sai pelo comando QUIT (fechar certo, como o F10) e olha
     o que o nucleo gravou na pasta de saves (bateria do cartucho, memory
     card, VMU...).

Os comandos chegam pela rede local (network_cmd_enable, SO neste teste; o
ARENA mantem desligado). Saves, estados, fotos e registros ficam numa pasta
temporaria, apagada no fim; o retroarch.cfg real e' protegido (protege_cfg)
e o RetroArch nao grava ao fechar (config_save_on_exit = false).

O que NAO da para automatizar (vai para o roteiro de sala): o controle com
botao apertado e o save do jogo feito pelo menu do proprio jogo. O cheat tem
teste proprio (testes\teste_cheats_no_jogo.py: le a memoria do jogo dentro
do save state). Emulador de fora (PCSX2, Dolphin, RPCS3, Xenia) tem teste
proprio.

Console cuja BIOS obrigatoria falta (ColecoVision, MSX, 3DO...): abre com a
tela preta -- e' o esperado. O teste anota "sem_bios" com a frase que o
ARENA mostra (o console fica amarelo e o Jogar nao aparece) e nao conta a
foto como falha.

Saida: docs\auditoria3\matriz_consoles.json e uma tabela no fim.

Uso:
    servidor\python\python.exe testes\teste_matriz_consoles.py [pedaco do nome do console]
"""
import ctypes
import importlib.util
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from ctypes import wintypes
from unittest import mock

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RETROARCH = os.path.join(RAIZ, "retroarch", "retroarch.exe")
SEGUNDOS_MEDINDO = 8
ESPERA_ABRIR = 40          # o Dreamcast com o jogo em CD demora a mostrar o 1o quadro

sys.path.insert(0, os.path.join(RAIZ, "servidor"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import limpeza  # noqa: E402
import porta_de_comando  # noqa: E402
# A 55355 do RetroArch, ou outra se o Windows reservou a faixa dela
# (testes\porta_de_comando.py).
PORTA_COMANDO = porta_de_comando.livre()
spec_a = importlib.util.spec_from_file_location("arena_matriz_consoles", os.path.join(RAIZ, "servidor", "arena.py"))
arena = importlib.util.module_from_spec(spec_a)
spec_a.loader.exec_module(arena)
graficos = arena.graficos
controles = arena.controles
indexador = arena.indexador

# O jogo de cada console, quando esta na pasta (senao, o primeiro que houver).
PREFERIDOS = ["Super Bomberman 4", "Sonic The Hedgehog 3", "Bomberman 64", "CTR", "Burnout Legends",
              "Contra", "Combat", "Metal Slug X", "Armada", "Saturn Bomberman", "Sonic CD",
              "Knuckles' Chaotix", "International Karate", "Alien Breed", "Slither", "Killer Instinct",
              "Match Day"]

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
_PROCURAR = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]


def fps_e_quadros(pid):
    """Do titulo da janela: "... || FPS:  60.00 || Quadros: 256"."""
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


def tempo_de_processador(pid):
    """Segundos de processador (usuario + sistema) gastos pelo processo."""
    alca = kernel32.OpenProcess(0x1000, False, pid)      # PROCESS_QUERY_LIMITED_INFORMATION
    if not alca:
        return None
    try:
        tempos = [wintypes.FILETIME() for _ in range(4)]
        if not kernel32.GetProcessTimes(alca, *[ctypes.byref(t) for t in tempos]):
            return None
        return sum((t.dwHighDateTime << 32 | t.dwLowDateTime) for t in tempos[2:]) / 1e7
    finally:
        kernel32.CloseHandle(alca)


def comando(texto):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.sendto(texto.encode("ascii"), ("127.0.0.1", PORTA_COMANDO))


def arquivos(pasta):
    achados = {}
    for atual, _sub, nomes in os.walk(pasta):
        for nome in nomes:
            caminho = os.path.join(atual, nome)
            try:
                achados[os.path.relpath(caminho, pasta)] = os.path.getsize(caminho)
            except OSError:
                pass
    return achados


def escolher_jogos(filtro=""):
    """Um jogo por console do RetroArch (o emulador de fora fica de fora)."""
    plataformas, _ = indexador.carregar_plataformas()
    resultado = indexador.indexar(forcar=True)
    jogos = resultado["jogos"] if isinstance(resultado, dict) else resultado
    por_console = {}
    for jogo in sorted(jogos, key=lambda j: j["titulo"]):
        plataforma = plataformas.get(jogo["plataforma"], {})
        if plataforma.get("externo") and graficos.achar_externo(plataforma):
            continue
        if filtro and filtro not in jogo["plataforma_nome"].lower():
            continue
        if not os.path.isfile(os.path.join(RAIZ, "retroarch", "cores", plataforma.get("core", "") or "-")):
            continue
        por_console.setdefault(jogo["plataforma_nome"], []).append((jogo, plataforma))

    escolhidos = []
    for nome in sorted(por_console):
        candidatos = por_console[nome]

        def nota(par):
            titulo = par[0]["titulo"].lower()
            for i, preferido in enumerate(PREFERIDOS):
                if preferido.lower() in titulo:
                    return i
            return len(PREFERIDOS)
        escolhidos.append(min(candidatos, key=nota))
    return escolhidos


def preparar_sessao(jogo, plataforma, modesto, pasta):
    """Grava, numa pasta temporaria, o MESMO arquivo de opcoes e as MESMAS
    opcoes de nucleo que o ARENA grava ao abrir este jogo."""
    config = arena.config_padrao()
    if modesto:
        config["modo_modesto"] = True
    custo = int(plataforma.get("custo", 3) or 3)
    pastas = {nome: os.path.join(pasta, nome.lower()) for nome in (
        "PASTA_DADOS", "PASTA_SAVES", "PASTA_STATES", "PASTA_CAPTURAS", "PASTA_CHEATS",
        "PASTA_REMAPS", "PASTA_CACHE")}
    pastas["ARQUIVO_OVERRIDE"] = os.path.join(pastas["PASTA_DADOS"], "arena_override.cfg")
    opcoes_nucleo = os.path.join(pasta, "retroarch-core-options.cfg")
    nome_core = arena.nome_curto_do_core(plataforma["core"])
    with mock.patch.multiple(arena, **pastas), mock.patch.object(graficos, "ARQUIVO_OPCOES_CORE", opcoes_nucleo):
        extras_core = {}
        extras_core.update(graficos.opcoes_de_bios(nome_core, None))
        extras_core.update(graficos.opcoes_de_memory_card(pastas["PASTA_SAVES"], jogo["plataforma"]))
        extras_controle = controles.opcoes_do_console(jogo["plataforma"], jogadores=2, usar_analogico=True,
                                                      vibracao=True, dispositivo_extra=None)
        graficos.gravar_opcoes_dos_nucleos(arena.CAPACIDADE["nota"], extras_core,
                                           arena.CAPACIDADE.get("nota_gpu"),
                                           modesto=arena.grafico_original(config),
                                           abaixo=arena.nivel_abaixo(config))
        override, filtro = arena.gravar_override(config, custo, extras_controle, plataforma=jogo["plataforma"],
                                                 devolver_filtro=True, controles_ligados=0)
    # So deste teste: comandos pela rede local, FPS no titulo, janela, e o
    # RetroArch sem gravar o retroarch.cfg real ao fechar.
    so_do_teste = {
        "network_cmd_enable": "true", "network_cmd_port": str(PORTA_COMANDO),
        "fps_show": "true", "framecount_show": "true", "fps_update_interval": "30",
        "config_save_on_exit": "false", "video_fullscreen": "false", "quit_press_twice": "false",
        "playlist_directory": pasta, "savestate_thumbnail_enable": "false",
    }
    with open(override, encoding="utf-8") as arquivo:
        linhas = [l for l in arquivo.read().splitlines()
                  if not any(l.startswith(chave + " = ") for chave in so_do_teste)]
    linhas += ['%s = "%s"' % item for item in sorted(so_do_teste.items())]
    with open(override, "w", encoding="utf-8") as arquivo:
        arquivo.write("\n".join(linhas) + "\n")
    return override, filtro, pastas


def comandos_chegam(override):
    """O RetroArch atende os comandos de rede nesta sessao? Achado de 09/10/2026
    (Fase 5): com a resposta instantanea (run-ahead) numa instancia so e a
    leitura do controle adiantada ou atrasada (input_poll_type_behavior 0 ou
    2 -- o ARENA usa 2), ele NAO atende comando nenhum (nem QUIT). Com a
    leitura normal (1) ou com a segunda instancia, atende."""
    with open(override, encoding="utf-8") as arquivo:
        opcoes = dict(re.findall(r'^([a-z0-9_]+) = "([^"]*)"', arquivo.read(), re.M))
    return not (opcoes.get("run_ahead_enabled") == "true"
                and opcoes.get("run_ahead_secondary_instance") != "true"
                and opcoes.get("input_poll_type_behavior", "2") != "1")


def sessao(jogo, plataforma, modesto, pasta):
    os.makedirs(pasta)
    override, filtro, pastas = preparar_sessao(jogo, plataforma, modesto, pasta)
    com_comandos = comandos_chegam(override)
    caminho_jogo = os.path.join(RAIZ, jogo["arquivo"])
    linha = [RETROARCH, "-L", os.path.join(RAIZ, "retroarch", "cores", plataforma["core"]),
             "--appendconfig", override]
    if filtro:
        linha += ["--set-shader", filtro]
    linha.append(caminho_jogo)
    resultado = {"modo": "modesto" if modesto else "normal"}
    saves_antes = arquivos(pastas["PASTA_SAVES"])
    with open(os.path.join(pasta, "stdout.log"), "w") as saida:
        inicio = time.monotonic()
        processo = subprocess.Popen(linha, cwd=os.path.join(RAIZ, "retroarch"), stdout=saida,
                                    stderr=subprocess.STDOUT)
        try:
            # 1. Abre: o titulo mostra quadros andando.
            primeiro = None
            while time.monotonic() - inicio < ESPERA_ABRIR and processo.poll() is None:
                lido = fps_e_quadros(processo.pid)
                if lido and lido[1] > 0:
                    primeiro = lido
                    break
                time.sleep(0.25)
            resultado["abre"] = primeiro is not None
            resultado["ate_o_1o_quadro_s"] = round(time.monotonic() - inicio, 1) if primeiro else None
            if not primeiro:
                resultado["motivo"] = ("fechou sozinho" if processo.poll() is not None
                                       else "nenhum quadro em %d s" % ESPERA_ABRIR)
                return resultado

            # 2. Velocidade e processador.
            time.sleep(2)
            t0, cpu0, lido0 = time.monotonic(), tempo_de_processador(processo.pid), fps_e_quadros(processo.pid)
            menor = 999.0
            while time.monotonic() - t0 < SEGUNDOS_MEDINDO:
                lido = fps_e_quadros(processo.pid)
                if lido:
                    menor = min(menor, lido[0])
                time.sleep(0.25)
            t1, cpu1, lido1 = time.monotonic(), tempo_de_processador(processo.pid), fps_e_quadros(processo.pid)
            if lido0 and lido1 and t1 > t0:
                resultado["quadros_por_segundo"] = round((lido1[1] - lido0[1]) / (t1 - t0), 1)
                resultado["menor_fps"] = round(menor, 1)
            if cpu0 is not None and cpu1 is not None:
                resultado["processador_pct_de_um_nucleo"] = round(100 * (cpu1 - cpu0) / (t1 - t0), 1)

            # 3. Estado -- ANTES da foto: no Dreamcast (Flycast), a foto da tela
            # seguida de salvar estado derruba o nucleo as vezes ("[GPF] ...
            # unhandled access"; 3 de 3 sem dispositivo de som, 1 de 3 com o som
            # desligado no RetroArch). Achado da Fase 5, no relatorio e no
            # roteiro de sala (F8 e logo F2). Cada funcao e' conferida sozinha.
            antes = arquivos(pastas["PASTA_STATES"])
            comando("SAVE_STATE")
            time.sleep(3)
            depois = arquivos(pastas["PASTA_STATES"])
            salvou = any(depois.get(c, 0) > antes.get(c, -1) for c in depois)
            if not salvou and not com_comandos:
                # Foto, estado e o fechar certo deste console ficam para a outra
                # sessao (o modesto, sem resposta instantanea, mesmo nucleo).
                resultado["comandos"] = ("nao conferidos: resposta instantanea (run-ahead) com a leitura "
                                         "atrasada do controle -- o RetroArch nao atende comando de rede assim")
                return resultado
            resultado["salva_estado"] = salvou
            comando("LOAD_STATE")
            time.sleep(2)
            resultado["carrega_estado"] = processo.poll() is None and salvou

            # 4. Imagem. A foto pode demorar a ser gravada: depois de salvar
            # estado, a do PSP nasce com 0 bytes e fica completa uns 3 s depois
            # (medido na Fase 5; com espera fixa de 2 s, o PSP "nao mostrava
            # imagem"). Espera o tamanho parar de mudar, ate 10 s.
            comando("SCREENSHOT")
            fotos, anterior, limite = {}, None, time.monotonic() + 10
            while time.monotonic() < limite:
                time.sleep(0.5)
                fotos = {k: v for k, v in arquivos(pastas["PASTA_CAPTURAS"]).items()
                         if k.lower().endswith(".png")}
                maior = max(fotos.values()) if fotos else 0
                if maior > 2000 and maior == anterior:
                    break
                anterior = maior
            resultado["foto_kb"] = round(max(fotos.values()) / 1024, 1) if fotos else 0
            resultado["mostra_imagem"] = bool(fotos) and max(fotos.values()) > 2000

            # 5. Fechar certo (como o F10) e o save do proprio jogo.
            comando("QUIT")
            try:
                processo.wait(timeout=15)
                resultado["fecha_certo"] = True
            except subprocess.TimeoutExpired:
                resultado["fecha_certo"] = False
            novos = {k: v for k, v in arquivos(pastas["PASTA_SAVES"]).items() if k not in saves_antes}
            resultado["save_do_jogo"] = sorted(novos)[:4]
            return resultado
        finally:
            if processo.poll() is None:
                processo.terminate()
                try:
                    processo.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    processo.kill()


def sessao_certa(r, sem_bios=False):
    """A sessao fez tudo o que podia conferir? (Sem comandos -- a resposta
    instantanea -- so o "abre" vale; sem a BIOS, a foto escura e' esperada.)"""
    chaves = ("abre",) if r.get("comandos") else ("abre", "mostra_imagem", "salva_estado", "carrega_estado")
    if sem_bios:
        chaves = tuple(c for c in chaves if c != "mostra_imagem")
    return all(r.get(c) for c in chaves)


def main():
    filtro = sys.argv[1].lower() if len(sys.argv) > 1 else ""
    trabalho = tempfile.mkdtemp(prefix="arena_matriz_consoles_")
    tabela = []
    try:
        for n, (jogo, plataforma) in enumerate(escolher_jogos(filtro)):
            item = {"console": jogo["plataforma_nome"], "jogo": jogo["titulo"],
                    "nucleo": plataforma["core"].replace("_libretro.dll", "")}
            sem_bios = arena.bios.falta_para_o_console(plataforma["id"], arena.PASTA_SISTEMA)
            if sem_bios:
                item["sem_bios"] = sem_bios
            for modesto in (False, True):
                r = sessao(jogo, plataforma, modesto, os.path.join(trabalho, "%02d_%s" % (n, int(modesto))))
                if not sessao_certa(r, bool(sem_bios)):
                    # Uma segunda chance, anotada: o nucleo do Dreamcast (Flycast)
                    # cai as vezes neste teste ("[GPF] unhandled access"). O que
                    # falhou na primeira vez fica no resultado -- e a tabela mostra.
                    primeira = {k: r.get(k) for k in ("abre", "mostra_imagem", "salva_estado",
                                                      "carrega_estado", "fecha_certo")}
                    r = sessao(jogo, plataforma, modesto, os.path.join(trabalho, "%02d_%s_b" % (n, int(modesto))))
                    r["repetida"] = primeira
                item[r.pop("modo")] = r
            print("%-34s %-30s %s" % (item["console"][:34], item["jogo"][:30],
                                      json.dumps({k: item[k] for k in ("normal", "modesto")}, ensure_ascii=False)))
            tabela.append(item)
    finally:
        limpeza.apagar_pasta(trabalho)

    destino = os.path.join(RAIZ, "docs", "auditoria3", "matriz_consoles.json")
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(destino, "w", encoding="utf-8") as arquivo:
        json.dump(tabela, arquivo, ensure_ascii=False, indent=1)

    def sim(r, chave):
        return "-" if r.get("comandos") else ("s" if r.get(chave) else "N")

    print("\n%-28s %-8s %-6s %-6s %-6s %-6s %-11s %-11s" % (
        "Console", "Abre n/m", "Foto", "Estado", "Fecha", "Save", "FPS n/m", "CPU% n/m"))
    falhas = []
    for item in tabela:
        n, m = item["normal"], item["modesto"]
        for modo, r in (("normal", n), ("modesto", m)):
            # Sem comandos (resposta instantanea), so o "abre" vale nesta sessao.
            # Sem a BIOS obrigatoria, a tela preta e' o esperado (o ARENA avisa).
            chaves = ("abre",) if r.get("comandos") else ("abre", "mostra_imagem", "salva_estado", "carrega_estado")
            if item.get("sem_bios"):
                chaves = tuple(c for c in chaves if c != "mostra_imagem")
            for chave in chaves:
                if not r.get(chave):
                    falhas.append("%s (%s): %s" % (item["console"], modo, chave))
        if n.get("comandos") and m.get("comandos"):
            falhas.append("%s: nenhuma sessao conferiu foto e estado" % item["console"])
        for modo, r in (("normal", n), ("modesto", m)):
            if r.get("repetida"):
                print("[REPETIDA] %s (%s): na primeira vez %s" % (item["console"], modo, r["repetida"]))
        print("%-28s %-8s %-6s %-6s %-6s %-6s %-11s %-11s" % (
            item["console"][:28], "%s/%s" % ("s" if n.get("abre") else "N", "s" if m.get("abre") else "N"),
            "%s/%s" % (sim(n, "mostra_imagem"), sim(m, "mostra_imagem")),
            "%s/%s" % (sim(n, "salva_estado"), sim(m, "salva_estado")),
            "%s/%s" % (sim(n, "fecha_certo"), sim(m, "fecha_certo")),
            "s" if (n.get("save_do_jogo") or m.get("save_do_jogo")) else "-",
            "%s/%s" % (n.get("quadros_por_segundo"), m.get("quadros_por_segundo")),
            "%s/%s" % (n.get("processador_pct_de_um_nucleo"), m.get("processador_pct_de_um_nucleo"))))
    for item in tabela:
        if item.get("sem_bios"):
            print("[SEM BIOS] %s: %s" % (item["console"], item["sem_bios"][:110]))
    for falha in falhas:
        print("[FALHOU]", falha)
    print("\nConsoles: %d | falhas: %d\nResultado: %s" % (len(tabela), len(falhas), destino))
    print("RESULTADO:", "PASSOU" if not falhas else "FALHOU")
    return 0 if not falhas else 1


if __name__ == "__main__":
    import protege_cfg
    sys.exit(protege_cfg.rodar(main))
