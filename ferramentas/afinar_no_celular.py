# -*- coding: utf-8 -*-
r"""Mede o ARENA num celular de verdade, console por console (auditoria 4, 23/10/2026).

Pedido do Rafael (23/10/2026): "Eu autorizo fazer as implementacoes e teste em
tempo real com o meu telefone para um ajuste acertivo e preciso [...] faca
ajustes finos adaptando perfeitamente ao meu celular o arena para ficar com
um desempenho perfeito".

Com o APK de teste (ferramentas\montar_android.py --abi arm64-v8a --teste: a
tela do ARENA aceita a depuracao pelo cabo) instalado e o celular no cabo,
para cada console que tem jogo na pasta do ARENA do aparelho:
  1. abre o primeiro jogo pela propria tela do ARENA (/api/jogar, com o
     segredo da tela, como o app.js);
  2. deixa o jogo assentar e mede os quadros por segundo de verdade pelo
     SurfaceFlinger do Android (o tempo em que cada quadro chegou a tela),
     sem desenhar nada no jogo; e quanto da tela fica parada (os quadros
     repetidos de jogo que roda a 30 ou de pulo de quadros);
  3. tira a foto da tela;
  4. sai como o aluno: dois toques no SAIR do controle de toque.
O resultado vai para docs\auditoria4\celular_<modelo>.json.
Uso: servidor\python\python.exe ferramentas\afinar_no_celular.py [--consoles=snes,ps1] [--segundos=30]
"""
import json
import os
import re
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, os.path.join(RAIZ, "testes"))
import teste_android as base  # noqa: E402

PACOTE = base.PACOTE
# O SAIR do controle de toque, deitado (servidor\plataforma.py, BOTOES_DO_TOQUE).
SAIR_DEITADO = (0.85, 0.08)


def argumento(nome, padrao):
    for a in sys.argv[1:]:
        if a.startswith("--%s=" % nome):
            return a.split("=", 1)[1]
    return padrao


def tamanho_da_tela():
    """(largura, altura) com o celular deitado."""
    m = re.search(r"(\d+)x(\d+)", base.adb_texto("shell", "wm", "size"))
    lados = sorted((int(m.group(1)), int(m.group(2)))) if m else [720, 1600]
    return lados[1], lados[0]


def camada_do_jogo():
    """O nome da camada do RetroArch no SurfaceFlinger."""
    for linha in base.adb_texto("shell", "dumpsys", "SurfaceFlinger", "--list").splitlines():
        if "RetroActivityFuture" in linha and "SurfaceView" in linha and "Background" not in linha:
            return linha.strip()
    return None


def quadros_por_segundo(camada):
    """(quadros por segundo, fracao de quadros que demoraram mais de 1,5 vez
    o tempo da tela) dos ultimos ~127 quadros da camada."""
    if not camada:
        return None, None
    linhas = base.adb_texto("shell", "dumpsys", "SurfaceFlinger", "--latency", camada).splitlines()
    if len(linhas) < 3:
        return None, None
    try:
        periodo = int(linhas[0].strip())
    except ValueError:
        return None, None
    tempos = []
    for linha in linhas[1:]:
        partes = linha.split()
        if len(partes) == 3:
            apresentado = int(partes[1])
            if 0 < apresentado < (1 << 62):
                tempos.append(apresentado)
    tempos.sort()
    if len(tempos) < 10:
        return None, None
    intervalos = [b - a for a, b in zip(tempos, tempos[1:]) if b > a]
    fps = (len(tempos) - 1) / ((tempos[-1] - tempos[0]) / 1e9)
    lentos = sum(1 for i in intervalos if i > 1.5 * periodo) / float(len(intervalos) or 1)
    return round(fps, 1), round(lentos, 3)


def sair_tocando():
    largura, altura = tamanho_da_tela()
    x, y = int(SAIR_DEITADO[0] * largura), int(SAIR_DEITADO[1] * altura)
    for _ in range(2):
        base.adb("shell", "input", "tap", str(x), str(y))
        time.sleep(0.8)
    if base.esperar(lambda: "ArenaActivity" in base.tela_de_cima(), 15):
        return "SAIR"
    base.adb("shell", "input", "keyevent", "4")          # Voltar
    time.sleep(2)
    for _ in range(2):
        base.adb("shell", "input", "tap", str(x), str(y))
        time.sleep(0.8)
    if base.esperar(lambda: "ArenaActivity" in base.tela_de_cima(), 15):
        return "Voltar e SAIR"
    base.adb("shell", "am", "start", "-n", base.TELA_DO_ARENA)
    return "nao saiu"


def medir(pagina, jogo, segundos):
    r = {"jogo": jogo["titulo"], "plataforma": jogo["plataforma"]}
    antes = time.monotonic()
    resposta = pagina.pedir("/api/jogar", {"jogo_id": jogo["id"]})
    if not resposta or resposta.get("ok") is False or resposta.get("erro"):
        r["erro"] = str(resposta)[:200]
        return r
    if not base.esperar(lambda: "RetroActivityFuture" in base.tela_de_cima(), 90):
        r["erro"] = "o RetroArch nao ficou na frente"
        return r
    r["abriu_s"] = round(time.monotonic() - antes, 1)
    time.sleep(max(8, segundos - 10))
    camada = camada_do_jogo()
    medidas = []
    for _ in range(3):
        medidas.append(quadros_por_segundo(camada))
        time.sleep(3)
    validas = [m for m in medidas if m[0]]
    if validas:
        r["quadros_por_segundo"] = round(sum(m[0] for m in validas) / len(validas), 1)
        r["quadros_lentos"] = round(sum(m[1] for m in validas) / len(validas), 3)
    r["foto"] = os.path.basename(base.foto("celular-" + jogo["plataforma"])[0])
    r["saiu_por"] = sair_tocando()
    base.esperar(lambda: not (pagina.pedir("/api/estado") or {}).get("jogo_em_andamento", {}).get("ativo"), 30)
    return r


def principal():
    segundos = int(argumento("segundos", "30"))
    pedidos = [c for c in argumento("consoles", "").split(",") if c]
    modelo = base.adb_texto("shell", "getprop", "ro.product.model").strip() or "celular"
    pagina = base.Pagina()
    try:
        catalogo = pagina.pedir("/api/catalogo") or {}
        jogos = catalogo.get("jogos") or []
        primeiro = {}
        for jogo in sorted(jogos, key=lambda j: j.get("titulo", "")):
            if jogo.get("disponivel", True) is not False:
                primeiro.setdefault(jogo["plataforma"], jogo)
        consoles = pedidos or sorted(primeiro)
        estado = pagina.pedir("/api/estado") or {}
        resultado = {"modelo": modelo, "quando": time.strftime("%Y-%m-%d %H:%M"),
                     "maquina": estado.get("maquina"), "consoles": []}
        print("== %s: %d consoles com jogo" % (modelo, len(consoles)))
        for plataforma in consoles:
            jogo = primeiro.get(plataforma)
            if not jogo:
                continue
            r = medir(pagina, jogo, segundos)
            resultado["consoles"].append(r)
            print("  %-12s %-40s %s q/s, lentos %s, saiu por %s %s" % (
                plataforma, jogo["titulo"][:40], r.get("quadros_por_segundo"), r.get("quadros_lentos"),
                r.get("saiu_por"), r.get("erro", "")), flush=True)
    finally:
        pagina.fechar()
    saida = os.path.join(RAIZ, "docs", "auditoria4", "celular_%s.json" % re.sub(r"\W+", "_", modelo))
    with open(saida, "w", encoding="utf-8") as arquivo:
        json.dump(resultado, arquivo, ensure_ascii=False, indent=1)
    print("Resultado: %s" % saida)
    return 0


if __name__ == "__main__":
    sys.exit(principal())
