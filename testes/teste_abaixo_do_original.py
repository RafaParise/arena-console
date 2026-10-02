# -*- coding: utf-8 -*-
r"""Niveis ABAIXO do grafico original: leve e minimo ("bonecos de papelao").

Pedido do Rafael (02/10/2026): "Precisa ter modos abaixo do grafico de
console original mesmo que o grafico fique muito feio, bonecos de papelao,
a ideia e que se configurar corretamente pode rodar em qualquer maquina".

  1. nucleos do RetroArch (logica): leve e minimo mudam o que devem
     (Dreamcast 320x240, pulo de quadros no PSP/N64/2D...), o minimo inclui
     o leve, e o normal nao tem nada disso;
  2. a volta ao normal LIMPA: chave que o ARENA nao reconhece como dele
     fica no arquivo como "mudada pelo aluno" -- era o que acontecia com a
     tela 4K (o N64 continuava em 2x depois de sair da TV 4K);
  3. servidor (ARENA isolado, em outro processo): a chave nova vale, valor
     invalido vira "", o minimo da mais folga ao som, a tela grava os dois
     ajustes juntos;
  4. emuladores de fora (logica): PCSX2 com o processador do PS2 mais
     devagar, Dolphin com o do GameCube a 80%/60%, RPCS3 a 50%/25% -- e
     a volta ao normal devolve os padroes;
  5. RetroArch DE VERDADE abre um jogo de cada console no minimo: o
     registro mostra o nucleo lendo cada valor novo (valor que o nucleo
     nao aceita apareceria com o padrao dele) e o jogo mostra imagem;
  6. PCSX2 de verdade (copia isolada) abre o Crash Nitro Kart no minimo;
  7. a tela (Edge sem janela, ARENA isolado): o seletor "Nivel do grafico"
     tem os 4 niveis, grava os dois ajustes juntos e, ao recarregar, mostra
     o nivel escolhido.

Uso: servidor\python\python.exe testes\teste_abaixo_do_original.py [--sem-emuladores]
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
import jogos_de_teste  # noqa: E402
import limpeza  # noqa: E402
import protege_cfg  # noqa: E402
import teste_matriz_multitap as base  # noqa: E402

graficos = base.graficos
P = os.path.join(RAIZ, "jogos", "pessoais")
PYTHON = os.path.join(RAIZ, "servidor", "python", "python.exe")

# Console, jogo, nucleo e o que o registro do RetroArch tem que mostrar.
JOGOS = [
    ("Dreamcast", os.path.join(P, "Dreamcast", "Marvel vs. Capcom 2 - New Age of Heroes (Europe)",
                               "Marvel vs. Capcom 2 - New Age of Heroes (Europe).cue"), "flycast",
     {"reicast_internal_resolution": "320x240", "reicast_auto_skip_frame": "more",
      "reicast_fog": "disabled", "reicast_alpha_sorting": "per-strip (fast, least accurate)"}),
    ("PSP", os.path.join(P, "PSP", "Burnout Legends (Europe) (En,Fr,De,Es,It,Nl) (v2.00).iso"), "ppsspp",
     {"ppsspp_frameskip": "3", "ppsspp_auto_frameskip": "enabled", "ppsspp_skip_buffer_effects": "enabled"}),
    ("Nintendo 64", os.path.join(P, "Nintendo 64", "GoldenEye 007 (USA).z64"), "mupen64plus_next",
     {"mupen64plus-FrameDuping": "True", "mupen64plus-CountPerOp": "3",
      "mupen64plus-EnableCopyColorToRDRAM": "Off"}),
    ("Mega Drive", None, "genesis_plus_gx", {"genesis_plus_gx_frameskip": "auto"}),
]

SERVIDOR_ISOLADO = r'''
import json, os, sys, threading, time, urllib.request
sys.path.insert(0, sys.argv[1])
import fuzz_rotas
pasta = sys.argv[2]
fuzz_rotas.preparar_ambiente(pasta)
arena = fuzz_rotas.carregar_arena_isolado(pasta)
saida = {}
config = arena.carregar_config()
saida["padrao"] = config.get("abaixo_do_original")
for valor in ("leve", "minimo", "qualquer", 3):
    saida["nivel_" + str(valor)] = arena.nivel_abaixo({"abaixo_do_original": valor})
saida["original_com_leve"] = arena.grafico_original({"abaixo_do_original": "leve"})
def latencia(config):
    texto = open(arena.gravar_override(config), encoding="utf-8").read()
    achado = [l for l in texto.splitlines() if l.startswith("audio_latency")]
    return achado[-1].split("=", 1)[1].strip().strip('"') if achado else None
for ultra in (False, True):
    config["ultra_desempenho"] = ultra
    config["abaixo_do_original"] = "minimo"
    saida["latencia_minimo_ultra_%s" % ultra] = latencia(config)
    config["abaixo_do_original"] = ""
    config["modo_modesto"] = False
    saida["latencia_normal_ultra_%s" % ultra] = latencia(config)
config["ultra_desempenho"] = False
servidor = arena.Servidor(("127.0.0.1", 0), arena.Manipulador)
porta = servidor.server_address[1]
threading.Thread(target=servidor.serve_forever, daemon=True).start()
def mandar(corpo):
    pedido = urllib.request.Request("http://127.0.0.1:%d/api/config" % porta, data=json.dumps(corpo).encode(),
                                    method="POST", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(pedido, timeout=20) as resposta:
        return json.loads(resposta.read())["config"]
saida["post_minimo"] = mandar({"modo_modesto": True, "abaixo_do_original": "minimo"}).get("abaixo_do_original")
opcoes = open(os.path.join(pasta, "retroarch", "retroarch-core-options.cfg"), encoding="utf-8").read()
saida["arquivo_tem_320"] = 'reicast_internal_resolution = "320x240"' in opcoes
saida["post_invalido"] = mandar({"abaixo_do_original": "../../x"}).get("abaixo_do_original")
saida["post_lista"] = mandar({"abaixo_do_original": ["minimo"]}).get("abaixo_do_original")
saida["post_normal"] = mandar({"modo_modesto": False, "abaixo_do_original": ""}).get("modo_modesto")
opcoes = open(os.path.join(pasta, "retroarch", "retroarch-core-options.cfg"), encoding="utf-8").read()
saida["arquivo_sem_320"] = "320x240" not in opcoes and "reicast_fog" not in opcoes
servidor.shutdown()
print("RESULTADO " + json.dumps(saida))
'''


def opcoes_em(arquivo, **kwargs):
    """Gera o retroarch-core-options.cfg em 'arquivo' e le de volta."""
    original = graficos.ARQUIVO_OPCOES_CORE
    graficos.ARQUIVO_OPCOES_CORE = arquivo
    try:
        graficos.gravar_opcoes_dos_nucleos(**kwargs)
    finally:
        graficos.ARQUIVO_OPCOES_CORE = original
    return dict(re.findall(r'^(\S+) = "(.*)"$', open(arquivo, encoding="utf-8").read(), re.M))


def ler_ini(caminho, secao):
    valores, dentro = {}, False
    for linha in open(caminho, encoding="utf-8", errors="replace"):
        limpo = linha.strip()
        if limpo.startswith("["):
            dentro = limpo == "[%s]" % secao
        elif dentro and " = " in limpo:
            chave, valor = limpo.split(" = ", 1)
            valores[chave] = valor
    return valores


def main():
    falhas, total = [], [0]

    def confere(nome, ok, detalhe=""):
        total[0] += 1
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, "" if ok else detalhe), flush=True)
        if not ok:
            falhas.append(nome)

    pasta = tempfile.mkdtemp(prefix="arena_abaixo_")
    try:
        # 1. Nucleos ---------------------------------------------------------
        print("1. Nucleos do RetroArch (logica)")
        normal = opcoes_em(os.path.join(pasta, "normal.cfg"), nota=3, nota_gpu=3, altura_tela=1080)
        leve = opcoes_em(os.path.join(pasta, "leve.cfg"), nota=3, nota_gpu=3, altura_tela=1080, abaixo="leve")
        minimo = opcoes_em(os.path.join(pasta, "minimo.cfg"), nota=3, nota_gpu=3, altura_tela=1080, abaixo="minimo")
        confere("normal: Dreamcast em 640x480 ou mais, sem pulo de quadros",
                normal.get("reicast_internal_resolution") != "320x240" and "handy_frameskip" not in normal,
                normal.get("reicast_internal_resolution"))
        esperado_leve = {"reicast_internal_resolution": "320x240", "reicast_auto_skip_frame": "some",
                         "ppsspp_frameskip": "2", "mupen64plus-FrameDuping": "True",
                         "genesis_plus_gx_frameskip": "auto", "handy_frameskip": "auto",
                         "fbneo-frameskip-type": "Auto", "swanstation_GPU_Renderer": "Software"}
        errados = {k: leve.get(k) for k, v in esperado_leve.items() if leve.get(k) != v}
        confere("leve: Dreamcast pela metade, pulo de quadros, e o original por baixo (PS1 por processador)",
                not errados, errados)
        esperado_minimo = {"reicast_internal_resolution": "320x240", "reicast_auto_skip_frame": "more",
                           "reicast_fog": "disabled", "ppsspp_frameskip": "3", "mupen64plus-CountPerOp": "3",
                           "handy_frameskip": "auto"}
        errados = {k: minimo.get(k) for k, v in esperado_minimo.items() if minimo.get(k) != v}
        confere("minimo: mais pulo de quadros, sem neblina, e tudo do leve", not errados, errados)

        # 2. A volta ao normal limpa ------------------------------------------
        print("2. A volta ao normal limpa")
        mesmo = os.path.join(pasta, "mesmo.cfg")
        opcoes_em(mesmo, nota=3, nota_gpu=3, altura_tela=1080, abaixo="minimo")
        depois = opcoes_em(mesmo, nota=3, nota_gpu=3, altura_tela=1080)
        grudou = {k: depois[k] for k in ("handy_frameskip", "reicast_fog", "mupen64plus-CountPerOp",
                                          "fbneo-frameskip-type", "picodrive_frameskip") if k in depois}
        confere("saiu do minimo: nenhuma chave do minimo ficou no arquivo", not grudou, grudou)
        confere("saiu do minimo: o Dreamcast voltou da metade",
                depois.get("reicast_internal_resolution") != "320x240", depois.get("reicast_internal_resolution"))
        quatro_k = os.path.join(pasta, "4k.cfg")
        opcoes_em(quatro_k, nota=5, nota_gpu=5, altura_tela=2160)
        tela_comum = opcoes_em(quatro_k, nota=5, nota_gpu=5, altura_tela=1080)
        confere("saiu da TV 4K: o N64 nao ficou no 2x (defeito antigo da mesma raiz)",
                tela_comum.get("mupen64plus-parallel-rdp-upscaling") != "2x",
                tela_comum.get("mupen64plus-parallel-rdp-upscaling"))

        # 3. Servidor isolado, em outro processo ------------------------------
        print("3. Servidor (ARENA isolado, em outro processo)")
        copia = os.path.join(pasta, "isolado", "ARENA")
        os.makedirs(copia)
        rodou = subprocess.run([PYTHON, "-c", SERVIDOR_ISOLADO, AQUI, copia], capture_output=True, timeout=180,
                               env=dict(os.environ, ARENA_SEM_JANELA="1"))
        linha = next((l for l in rodou.stdout.decode("utf-8", "replace").splitlines()
                      if l.startswith("RESULTADO ")), "")
        r = json.loads(linha[len("RESULTADO "):]) if linha else {}
        if not r:
            confere("servidor isolado rodou", False, rodou.stderr.decode("utf-8", "replace")[-600:])
        else:
            confere("config nova: o padrao e' nao (vazio)", r.get("padrao") == "", r.get("padrao"))
            confere("nivel valido passa, invalido vira vazio",
                    r.get("nivel_leve") == "leve" and r.get("nivel_minimo") == "minimo"
                    and r.get("nivel_qualquer") == "" and r.get("nivel_3") == "", r)
            confere("abaixo do original liga o grafico original junto", r.get("original_com_leve") is True)
            confere("minimo: mais folga no som (128), com e sem ultra; normal: menos",
                    r.get("latencia_minimo_ultra_False") == "128" and r.get("latencia_minimo_ultra_True") == "128"
                    and r.get("latencia_normal_ultra_False") != "128"
                    and r.get("latencia_normal_ultra_True") != "128",
                    {k: v for k, v in r.items() if k.startswith("latencia")})
            confere("tela grava o minimo e o arquivo dos nucleos e' refeito na hora",
                    r.get("post_minimo") == "minimo" and r.get("arquivo_tem_320"), r)
            confere("pedido com valor torto (caminho, lista) vira vazio",
                    r.get("post_invalido") == "" and r.get("post_lista") == "", r)
            confere("volta ao normal pela tela limpa o arquivo dos nucleos",
                    r.get("post_normal") is False and r.get("arquivo_sem_320"), r)

        # 4. Emuladores de fora (logica) ---------------------------------------
        print("4. Emuladores de fora (logica)")
        pcsx2 = os.path.join(pasta, "pcsx2")
        os.makedirs(os.path.join(pcsx2, "inis"))
        shutil.copy(os.path.join(RAIZ, "emuladores", "PCSX2", "PCSX2", "inis", "PCSX2.ini"),
                    os.path.join(pcsx2, "inis", "PCSX2.ini"))
        ini = os.path.join(pcsx2, "inis", "PCSX2.ini")
        for nivel, ciclos, mistura, aviso in (("leve", ("-1", "1"), "1", "false"),
                                              ("minimo", ("-2", "2"), "0", "false"),
                                              ("", ("0", "0"), None, "true")):
            graficos.escrever_config_pcsx2(os.path.join(pcsx2, "pcsx2-qt.exe"), nota=3, nota_gpu=3,
                                           integrada=True, jogadores=4, controles_xinput=[], abaixo=nivel)
            rapido, gs, nucleo = ler_ini(ini, "EmuCore/Speedhacks"), ler_ini(ini, "EmuCore/GS"), ler_ini(ini, "EmuCore")
            nome = nivel or "normal (depois do minimo)"
            confere("PCSX2 %s: processador do PS2 em %s/%s, aviso do PCSX2 %s" % (nome, ciclos[0], ciclos[1], aviso),
                    (rapido.get("EECycleRate"), rapido.get("EECycleSkip")) == ciclos
                    and nucleo.get("WarnAboutUnsafeSettings") == aviso,
                    (rapido.get("EECycleRate"), rapido.get("EECycleSkip"), nucleo.get("WarnAboutUnsafeSettings")))
            if mistura is not None:
                confere("PCSX2 %s: 1x, mistura %s" % (nome, mistura),
                        gs.get("upscale_multiplier") == "1" and gs.get("accurate_blending_unit") == mistura,
                        (gs.get("upscale_multiplier"), gs.get("accurate_blending_unit")))
            else:
                confere("PCSX2 normal: mistura nunca abaixo da basica, quadro repetido desenhado",
                        gs.get("accurate_blending_unit") != "0" and gs.get("SkipDuplicateFrames") == "false",
                        (gs.get("accurate_blending_unit"), gs.get("SkipDuplicateFrames")))
        for nivel, relogio, neblina, efb, modo in (("leve", "0.8", "False", "True", "2"),
                                                   ("minimo", "0.6", "True", "False", "3"),
                                                   ("", "1.0", "False", "True", "2")):
            imagem = graficos.opcoes_de_imagem_dolphin(nota=3, nota_gpu=3, abaixo=nivel)
            core, gfx = imagem["Dolphin.ini"]["Core"], imagem["GFX.ini"]
            confere("Dolphin %s: processador a %s, neblina desligada %s, EFB %s, sombras modo %s"
                    % (nivel or "normal", relogio, neblina, efb, modo),
                    core.get("Overclock") == relogio and core.get("OverclockEnable") == ("True" if nivel else "False")
                    and gfx["Settings"].get("DisableFog") == neblina and gfx["Hacks"].get("EFBAccessEnable") == efb
                    and gfx["Settings"].get("ShaderCompilationMode") == modo, imagem)
        rpcs3 = os.path.join(pasta, "rpcs3")
        os.makedirs(os.path.join(rpcs3, "config"))
        shutil.copy(os.path.join(RAIZ, "emuladores", "RPCS3", "RPCS3", "config", "config.yml"),
                    os.path.join(rpcs3, "config", "config.yml"))
        for nivel, escala, relaxado in (("leve", "50", "true"), ("minimo", "25", "true"), ("", "100", "false")):
            graficos.escrever_config_rpcs3(os.path.join(rpcs3, "rpcs3.exe"), 3, 3, abaixo=nivel)
            texto = open(os.path.join(rpcs3, "config", "config.yml"), encoding="utf-8").read()
            confere("RPCS3 %s: desenha a %s%%, ZCULL relaxado %s" % (nivel or "normal", escala, relaxado),
                    "  Resolution Scale: %s\n" % escala in texto and "  Relaxed ZCULL Sync: %s\n" % relaxado in texto,
                    re.findall(r"  (Resolution Scale|Relaxed ZCULL Sync|Accurate ZCULL stats): (\S+)", texto))

        # 7. A tela -------------------------------------------------------------
        print("7. A tela (Edge sem janela)")
        import teste_servidor_que_cai as servidor_de_teste
        import tela_sem_janela
        copia_tela = os.path.join(pasta, "tela", "ARENA")
        os.makedirs(copia_tela)
        servidor_de_teste.preparar_copia(copia_tela)
        porta = tela_sem_janela.porta_livre()
        processo = servidor_de_teste.subir(copia_tela, porta, True, os.path.join(pasta, "sem-trava"))
        try:
            servidor_de_teste.esperar_servidor(porta)
            with tela_sem_janela.Navegador() as nav:
                nav.comando("Runtime.enable")          # o navegador passa a avisar erro de JavaScript
                nav.abrir("http://127.0.0.1:%d/" % porta, espera=4)
                opcoes = nav.avaliar("[...document.querySelectorAll('#listaNivelGrafico option')].map(o => o.value)")
                confere("o seletor tem os 4 niveis", opcoes == ["normal", "original", "leve", "minimo"], opcoes)
                nav.avaliar("(() => { const l = document.querySelector('#listaNivelGrafico'); l.value = 'minimo';"
                            " l.dispatchEvent(new Event('change')); return 1; })()")
                time.sleep(1.5)
                config = nav.avaliar("pedir('/api/estado').then(d => d.config)") or {}
                confere("escolher 'minimo' grava abaixo do original E o grafico original",
                        config.get("abaixo_do_original") == "minimo" and config.get("modo_modesto") is True,
                        {k: config.get(k) for k in ("abaixo_do_original", "modo_modesto")})
                explica = nav.avaliar("document.querySelector('#explicaNivelGrafico').textContent") or ""
                confere("a explicacao fala dos bonecos de papelao", "papelão" in explica, explica[:80])
                nav.abrir("http://127.0.0.1:%d/" % porta, espera=4)
                confere("recarregou: o seletor mostra 'minimo'",
                        nav.avaliar("document.querySelector('#listaNivelGrafico').value") == "minimo")
                nav.avaliar("(() => { const l = document.querySelector('#listaNivelGrafico'); l.value = 'normal';"
                            " l.dispatchEvent(new Event('change')); return 1; })()")
                time.sleep(1.5)
                config = nav.avaliar("pedir('/api/estado').then(d => d.config)") or {}
                confere("voltar para 'normal' desliga os dois",
                        config.get("abaixo_do_original") == "" and config.get("modo_modesto") is False,
                        {k: config.get(k) for k in ("abaixo_do_original", "modo_modesto")})
                nav.esperar(0.5)
                erros = [e["params"].get("exceptionDetails", {}).get("text") for e in nav.eventos
                         if e.get("method") == "Runtime.exceptionThrown"]
                confere("sem erro de JavaScript na tela (avisos do navegador)", not erros, erros)
        finally:
            servidor_de_teste.derrubar(processo)

        if "--sem-emuladores" in sys.argv:
            print("\n(5 e 6 pulados: --sem-emuladores)")
        else:
            # 5. RetroArch de verdade no minimo ------------------------------
            print("5. RetroArch de verdade no minimo")
            arquivo = os.path.join(pasta, "minimo_real.cfg")
            opcoes_em(arquivo, nota=3, nota_gpu=3, altura_tela=1080, abaixo="minimo",
                      extras=graficos.opcoes_de_memory_card("", "ps1"))
            for console, jogo, nucleo, esperado in JOGOS:
                if jogo is None:
                    jogo = jogos_de_teste.achar("Mega Drive", "Sonic The Hedgehog 3 (USA).md")
                if not jogo or not os.path.isfile(jogo):
                    confere("%s: jogo de teste na pasta" % console, False, jogo)
                    continue
                sub = os.path.join(pasta, console.replace(" ", "_"))
                cfg = base.config_base(sub, {"audio_enable": "false"})
                texto = open(cfg, encoding="utf-8").read()
                texto = re.sub(r'^core_options_path = ".*"$', lambda _m: 'core_options_path = "%s"' % arquivo,
                               texto, flags=re.M)
                open(cfg, "w", encoding="utf-8").write(texto)
                foto, registro = os.path.join(sub, "foto.png"), os.path.join(sub, "ra.log")
                inicio = time.monotonic()
                try:
                    subprocess.run([base.RETROARCH, "-L", os.path.join(RAIZ, "retroarch", "cores",
                                                                       nucleo + "_libretro.dll"),
                                    "--appendconfig", cfg, "--verbose", "--log-file", registro, "--max-frames=900",
                                    "--max-frames-ss", "--max-frames-ss-path=" + foto, jogo],
                                   cwd=os.path.dirname(base.RETROARCH), timeout=180,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    travou = False
                except subprocess.TimeoutExpired:
                    travou = True
                log = open(registro, encoding="utf-8", errors="ignore").read() if os.path.isfile(registro) else ""
                nao_leu = [chave for chave, valor in esperado.items()
                           if not re.search(r'GET_VARIABLE: %s = "%s"' % (re.escape(chave), re.escape(valor)), log)]
                tamanho = os.path.getsize(foto) if os.path.isfile(foto) else 0
                confere("%s: o nucleo leu os %d valores do minimo e mostrou imagem (%.0f s)"
                        % (console, len(esperado), time.monotonic() - inicio),
                        not nao_leu and tamanho > 2000 and not travou,
                        {"nao_leu": nao_leu, "foto": tamanho, "travou": travou,
                         "erros": base.erros_importantes(log)[:2]})

            # 6. PCSX2 de verdade no minimo ---------------------------------
            print("6. PCSX2 de verdade no minimo")
            cnk = os.path.join(P, "PS2", "Crash Nitro Kart (USA).chd")
            if not os.path.isfile(cnk):
                confere("PS2: Crash Nitro Kart na pasta", False)
            else:
                copia_pcsx2 = os.path.join(pasta, "PCSX2_de_verdade")   # "pcsx2" ja e' a da parte 4
                shutil.copytree(os.path.join(RAIZ, "emuladores", "PCSX2", "PCSX2"), copia_pcsx2,
                                ignore=shutil.ignore_patterns("memcards", "cache", "logs", "snaps", "sstates",
                                                              "covers", "videos"))
                os.makedirs(os.path.join(copia_pcsx2, "memcards"), exist_ok=True)
                exe = os.path.join(copia_pcsx2, "pcsx2-qt.exe")
                graficos.escrever_config_pcsx2(exe, nota=3, nota_gpu=3, integrada=True, jogadores=4,
                                               controles_xinput=[], abaixo="minimo")
                ini_copia = os.path.join(copia_pcsx2, "inis", "PCSX2.ini")
                texto = graficos._trocar_chaves_ini(open(ini_copia, encoding="utf-8").read(),
                                                    "Logging", {"EnableFileLogging": "true"})
                open(ini_copia, "w", encoding="utf-8").write(texto)
                registro = os.path.join(copia_pcsx2, "logs", "emulog.txt")
                janela = subprocess.STARTUPINFO()
                janela.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                janela.wShowWindow = 7
                processo = subprocess.Popen([exe, cnk], cwd=copia_pcsx2, startupinfo=janela)
                lido, comecou, vivo = "", False, False
                fim = time.monotonic() + 60
                while time.monotonic() < fim:
                    time.sleep(1)
                    try:
                        lido = open(registro, encoding="utf-8", errors="replace").read()
                    except OSError:
                        continue
                    if "is executing" in lido:
                        comecou = True
                        time.sleep(8)               # roda um pouco no minimo
                        vivo = processo.poll() is None
                        break
                subprocess.run(["taskkill", "/T", "/F", "/PID", str(processo.pid)], capture_output=True)
                try:
                    processo.wait(15)
                except subprocess.TimeoutExpired:
                    pass
                confere("PS2 no minimo: o Crash Nitro Kart comecou e seguiu rodando 8 s",
                        comecou and vivo, lido[-300:])
    finally:
        limpeza.apagar_pasta(pasta)

    print()
    if falhas:
        print("FALHOU: %d de %d" % (len(falhas), total[0]))
        return 1
    print("Abaixo do original: %d de %d certos." % (total[0], total[0]))
    return 0


if __name__ == "__main__":
    sys.exit(protege_cfg.rodar(main))
