# -*- coding: utf-8 -*-
r"""Quanto o fundo animado pesa na tela parada, em cada jeito de mostrar.

Auditoria 3, Fase 2 (07/10/2026). Na linha de base, a tela parada gastou
9,7% de um nucleo com o fundo em "Sempre" (a escolha do Rafael), a 60
voltas do laco de animacao por segundo. O roteiro pede: "Os fundos animados
precisam respeitar o computador fraco [...] medir quanto pesam".

Para cada caso (tema claro/escuro x fundo Automatico/Sempre/Parado x Windows
pedindo ou nao menos movimento), num ARENA isolado (copia no temporario, com
a configuracao do caso), abre a tela como o ARENA abre (Edge em janela de
aplicativo, perfil temporario) e mede, com a janela a frente:
  - processador e memoria dos processos do Edge dessa janela;
  - voltas do laco de animacao por segundo (requestAnimationFrame);
  - se o fundo esta animando, parado ou escondido.

O "Windows pedindo menos movimento" e' imitado pelo proprio navegador
(Emulation.setEmulatedMedia, prefers-reduced-motion), sem mexer no Windows.

Uso:
    servidor\python\python.exe testes\medir_fundos.py [--saida=<arquivo.json>] [--segundos=30] [--so=escuro] [--variante=atual|20qps|relogio|relogio20]
"""
import json
import os
import sys
import tempfile
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
import limpeza  # noqa: E402
import linha_base  # noqa: E402
import tela_sem_janela  # noqa: E402
import teste_servidor_que_cai as servidor_de_teste  # noqa: E402

# (rotulo, tema, fundo_animado, modo_modesto, Windows pede menos movimento)
CASOS = [
    ("claro, Automatico (padrao), Windows com animacao", "claro", "automatico", False, False),
    ("claro, Automatico, Windows pedindo menos movimento", "claro", "automatico", False, True),
    ("claro, Sempre", "claro", "sempre", False, False),
    ("claro, Parado", "claro", "parado", False, False),
    ("escuro, Automatico, Windows com animacao", "escuro", "automatico", False, False),
    ("escuro, Automatico, modo modesto", "escuro", "automatico", True, False),
    ("escuro, Sempre (o do Rafael)", "escuro", "sempre", True, True),
    ("escuro, Parado", "escuro", "parado", False, False),
]


# Variantes para comparar (so na COPIA isolada; a tela de verdade nao muda):
#   atual      -- como esta no launcher;
#   20qps      -- 20 quadros por segundo em vez de 30;
#   relogio    -- o laco anda por relogio (setTimeout no ritmo do desenho) em
#                 vez de acordar a cada quadro da tela (requestAnimationFrame
#                 a 60 por segundo, desenhando em um de cada dois);
#   relogio20  -- as duas coisas.
VARIANTES = ("atual", "20qps", "relogio", "relogio20")


def aplicar_variante(copia, variante):
    import re
    if variante == "atual":
        return
    for nome in ("field-background.js", "galaxy-background.js"):
        caminho = os.path.join(copia, "launcher", nome)
        with open(caminho, encoding="utf-8", newline="") as f:
            bruto = f.read()
        crlf = "\r\n" in bruto
        texto = bruto.replace("\r\n", "\n")
        if "20" in variante:
            assert texto.count("const INTERVALO = 1000 / 30;") == 1, nome
            texto = texto.replace("const INTERVALO = 1000 / 30;", "const INTERVALO = 1000 / 20;")
        if variante.startswith("relogio"):
            texto, n = re.subn(
                r"function quadro\(agora\) \{\n(\s*)if \(minha !== geracao\) return;([^\n]*)\n\s*"
                r"requestAnimationFrame\(quadro\);\n\s*if \(ultimo && agora - ultimo < INTERVALO - 2\) return;",
                lambda m: ("function quadro() {\n%sif (minha !== geracao) return;%s\n%ssetTimeout(quadro, INTERVALO);\n"
                           "%sif (document.visibilityState !== 'visible') return;\n%sconst agora = performance.now();"
                           % (m.group(1), m.group(2), m.group(1), m.group(1), m.group(1))), texto)
            assert n == 1, (nome, n)
            assert texto.count("requestAnimationFrame(quadro);") == 1, nome
            texto = texto.replace("requestAnimationFrame(quadro);", "setTimeout(quadro, 0);")
        with open(caminho, "w", encoding="utf-8", newline="") as f:
            f.write(texto.replace("\n", "\r\n") if crlf else texto)


def preparar(copia, tema, fundo, modesto, variante="atual"):
    servidor_de_teste.preparar_copia(copia)
    aplicar_variante(copia, variante)
    caminho = os.path.join(copia, "dados", "config.json")
    try:
        with open(caminho, encoding="utf-8") as f:
            config = json.load(f)
    except (OSError, ValueError):
        config = {}
    config.update(tema=tema, fundo_animado=fundo, modo_modesto=modesto, apelido=config.get("apelido") or "teste")
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False)


def medir_caso(rotulo, tema, fundo, modesto, menos_movimento, segundos, pasta, variante="atual"):
    copia = os.path.join(pasta, "isolado", "ARENA")
    os.makedirs(copia)
    preparar(copia, tema, fundo, modesto, variante)
    porta = tela_sem_janela.porta_livre()
    processo = servidor_de_teste.subir(copia, porta, True, os.path.join(pasta, "sem-trava"))
    try:
        if not servidor_de_teste.esperar_servidor(porta):
            return {"caso": rotulo, "erro": "o servidor nao abriu"}
        with tela_sem_janela.Navegador(janela=True) as nav:
            nav.comando("Emulation.setEmulatedMedia", features=[
                {"name": "prefers-reduced-motion", "value": "reduce" if menos_movimento else "no-preference"}])
            nav.comando("Page.addScriptToEvaluateOnNewDocument", source=linha_base.SCRIPT_DA_PAGINA)
            nav.comando("Page.bringToFront")
            nav.comando("Page.navigate", url="http://127.0.0.1:%d/" % porta)
            fim = time.monotonic() + 60
            while time.monotonic() < fim:
                time.sleep(0.2)
                try:
                    if nav.avaliar("window.__arena && window.__arena.pronta"):
                        break
                except OSError:
                    pass
            time.sleep(15)                                   # assentar
            nav.comando("Page.bringToFront")
            nav.avaliar("window.__arena.zerar(); 1")
            medida = linha_base.medir_parado({"tela": nav.pids()}, segundos)["tela"]
            pagina = nav.avaliar(linha_base.RESUMO_DA_PAGINA) or {}
            situacao = nav.avaliar(
                "(() => { const c = [...document.querySelectorAll('canvas')]"
                ".filter(x => getComputedStyle(x).display !== 'none'); return {visiveis: c.length,"
                " escuro: !!(window.__fundoEscuro), claro: !!(window.__fundoClaro)}; })()") or {}
        voltas = round((pagina.get("quadros") or 0) / max(pagina.get("segundos") or segundos, 1), 1)
        return {"caso": rotulo, "variante": variante, "tema": tema, "fundo": fundo, "modesto": modesto,
                "menos_movimento": menos_movimento,
                "cpu_um_nucleo_pct": medida["cpu_um_nucleo_pct"], "ram_mb": medida["ram_mb"],
                "voltas_por_segundo": voltas, "visivel": pagina.get("visivel"),
                "telas_de_desenho_visiveis": situacao.get("visiveis")}
    finally:
        servidor_de_teste.derrubar(processo)


def principal():
    destino = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--saida=")),
                   os.path.join(RAIZ, "docs", "auditoria3", "fundos.json"))
    if not os.path.isabs(destino):
        destino = os.path.join(RAIZ, destino)
    segundos = int(next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--segundos=")), "30"))
    filtro = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--so=")), "")
    variante = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--variante=")), "atual")
    if variante not in VARIANTES:
        print("Variante desconhecida: %s (use %s)" % (variante, ", ".join(VARIANTES)))
        return 2
    resultados = []
    for caso in CASOS:
        # --so=a|b: os casos que tem "a" OU "b" no nome.
        if filtro and not any(pedaco in caso[0] for pedaco in filtro.split("|")):
            continue
        pasta = tempfile.mkdtemp(prefix="arena_fundos_")
        try:
            print("- %s..." % caso[0], flush=True)
            r = medir_caso(*caso, segundos=segundos, pasta=pasta, variante=variante)
            resultados.append(r)
            if "erro" in r:
                print("    ERRO: %s" % r["erro"], flush=True)
            else:
                print("    %.2f%% de um nucleo, %.0f MB, %.1f voltas/s, %s" % (
                    r["cpu_um_nucleo_pct"], r["ram_mb"], r["voltas_por_segundo"], r["visivel"]), flush=True)
        finally:
            limpeza.apagar_pasta(pasta)
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(destino, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    print("Salvo em", destino)
    return 0


if __name__ == "__main__":
    sys.exit(principal())
