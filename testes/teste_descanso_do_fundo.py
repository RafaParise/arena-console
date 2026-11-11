# -*- coding: utf-8 -*-
r"""Descanso do fundo animado (11/11/2026): no "Automatico", com a tela parada ha 3 minutos, o fundo para; no
primeiro toque, volta a se mexer. No "Sempre", nao para.

Confere num navegador sem janela (testes\tela_sem_janela.py), com o servidor de verdade, nos dois temas, pela
soma dos pontos do desenho (igual em dois momentos = parado):
  - "Automatico" e acordado: o desenho muda;
  - "Automatico" em descanso (data-descanso, o que o app.js poe depois dos 3 minutos): o desenho nao muda;
  - um movimento do mouse acorda: o desenho volta a mudar;
  - "Sempre" em descanso: o desenho continua mudando;
  - nenhum erro no console.

Uso: servidor\python\python.exe testes\teste_descanso_do_fundo.py
"""
import os
import subprocess
import sys
import time
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tela_sem_janela import Navegador, achar_navegador  # noqa: E402
from teste_ver_animacao import SOMA, porta_ocupada  # noqa: E402


def main():
    falhas, total = [], [0]

    def confere(nome, ok, detalhe=""):
        total[0] += 1
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, detalhe if not ok else ""))
        if not ok:
            falhas.append(nome)

    if not achar_navegador():
        print("Sem Edge nem Chrome nesta maquina: nada a testar.")
        return 0
    if porta_ocupada():
        print("O ARENA ja esta aberto (porta 8777): feche e rode de novo.")
        return 1
    servidor = subprocess.Popen([os.path.join(RAIZ, "servidor", "python", "python.exe"),
                                 os.path.join(RAIZ, "servidor", "arena.py")], cwd=RAIZ,
                                env=dict(os.environ, ARENA_SEM_JANELA="1"),
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(150):
            try:
                urllib.request.urlopen("http://127.0.0.1:8777/api/estado", timeout=1).read()
                break
            except OSError:
                time.sleep(0.2)
        with Navegador() as nav:
            nav.comando("Runtime.enable")
            nav.abrir("http://127.0.0.1:8777", largura=1366, altura=768, espera=3)
            nav.avaliar("window.__errosTeste = []; window.addEventListener('error', e => __errosTeste.push(String(e.message)));")
            menos = nav.avaliar("matchMedia('(prefers-reduced-motion: reduce)').matches")
            if menos:
                # Este Windows pede menos movimento (o fundo do Automatico fica parado de proposito): o teste pede o
                # contrario so nesta pagina.
                print("  (o Windows desta maquina pede menos movimento; o teste simula o contrario)")
                nav.comando("Emulation.setEmulatedMedia", features=[{"name": "prefers-reduced-motion", "value": "no-preference"}])
                nav.esperar(3.5)

            def mexendo():
                s1 = nav.avaliar(SOMA)
                nav.esperar(1.5)
                return nav.avaliar(SOMA) != s1

            for tema in ("escuro", "claro"):
                nav.avaliar("document.body.dataset.tema = '%s'; document.body.dataset.modoModesto = 'false';"
                            "document.body.dataset.fundoAnimado = 'automatico'; acordarFundo();" % tema)
                nav.esperar(1)
                confere("%s: automatico e acordado, o fundo se mexe" % tema, mexendo())
                nav.avaliar("document.body.dataset.descanso = 'true'")
                nav.esperar(1)
                confere("%s: em descanso, o fundo para" % tema, not mexendo())
                nav.avaliar("window.dispatchEvent(new PointerEvent('pointermove', {bubbles: true}))")
                nav.esperar(1)
                confere("%s: o mouse acorda o fundo" % tema,
                        nav.avaliar("document.body.dataset.descanso") == "false" and mexendo())
                nav.avaliar("document.body.dataset.fundoAnimado = 'sempre'; document.body.dataset.descanso = 'true'")
                nav.esperar(1)
                confere("%s: no Sempre, o descanso nao para o fundo" % tema, mexendo())
            erros = nav.avaliar("JSON.stringify(window.__errosTeste)")
            confere("nenhum erro no console", erros == "[]", erros)
    finally:
        servidor.terminate()
        try:
            servidor.wait(timeout=10)
        except subprocess.TimeoutExpired:
            servidor.kill()
    print("\nDescanso do fundo: %d de %d certos." % (total[0] - len(falhas), total[0]))
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
