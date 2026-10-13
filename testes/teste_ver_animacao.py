# -*- coding: utf-8 -*-
r"""O botao "Visualizar animacao" (pedido do Rafael, 12/10/2026): esconde a tela
inteira do ARENA e deixa so o fundo animado; o "Voltar" (ou o Esc) traz tudo
de volta.

Confere, num navegador sem janela (testes\tela_sem_janela.py), com o
servidor de verdade, nos dois temas:
  - a tela some (topo, lista de jogos) e o fundo continua na tela;
  - o "Voltar" aparece e recebe o foco;
  - o fundo anima mesmo com o "Fundo animado" em "Parado" (quem abriu quer
    ver a animacao) e uma visita de personagem chega logo;
  - o Esc volta: a tela reaparece, o "Voltar" some e o foco volta ao botao;
  - os ganchos de teste avancar() e pixels() funcionam (160 x 90 pontos);
  - nenhum erro no console.

Uso: servidor\python\python.exe testes\teste_ver_animacao.py
"""
import base64
import json
import os
import subprocess
import sys
import time
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tela_sem_janela import Navegador, achar_navegador  # noqa: E402

ESTADO = """(() => {
  const vis = (sel) => { const e = document.querySelector(sel); return !!e && getComputedStyle(e).display !== 'none'; };
  const tema = document.body.dataset.tema;
  return JSON.stringify({
    soFundo: document.body.dataset.soFundo || 'false',
    topo: vis('.painel-topo'), corpo: vis('main.corpo'), voltar: vis('#btnVoltarAnimacao'),
    fundo: vis(tema === 'escuro' ? '#galaxyCanvas' : '#fieldCanvas'),
    foco: document.activeElement ? document.activeElement.id : ''
  });
})()"""
SOMA = """(() => {
  const c = document.getElementById(document.body.dataset.tema === 'escuro' ? 'galaxyCanvas' : 'fieldCanvas');
  const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
  let s = 0; for (let i = 0; i < d.length; i += 4) s = (s * 31 + d[i] + d[i + 1] * 7 + d[i + 2] * 13) >>> 0;
  return s;
})()"""


def porta_ocupada():
    import socket
    s = socket.socket()
    s.settimeout(0.5)
    try:
        return s.connect_ex(("127.0.0.1", 8777)) == 0
    finally:
        s.close()


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
            for tema in ("escuro", "claro"):
                gancho = "__fundoEscuro" if tema == "escuro" else "__fundoClaro"
                nav.avaliar("document.body.dataset.tema = '%s'; document.body.dataset.fundoAnimado = 'parado';" % tema)
                nav.esperar(0.6)
                antes = json.loads(nav.avaliar(ESTADO))
                confere("%s: antes, a tela aparece" % tema, antes["topo"] and antes["corpo"] and not antes["voltar"], antes)
                nav.avaliar("document.getElementById('btnVerAnimacao').click()")
                nav.esperar(0.4)
                agora = json.loads(nav.avaliar(ESTADO))
                confere("%s: a tela some e o fundo fica" % tema,
                        agora["soFundo"] == "true" and not agora["topo"] and not agora["corpo"] and agora["fundo"], agora)
                confere("%s: o Voltar aparece e recebe o foco" % tema,
                        agora["voltar"] and agora["foco"] == "btnVoltarAnimacao", agora)
                s1 = nav.avaliar(SOMA)
                nav.esperar(1.5)
                s2 = nav.avaliar(SOMA)
                confere("%s: anima mesmo com o fundo em Parado" % tema, s1 != s2)
                chegou = False
                for _ in range(20):
                    if nav.avaliar("window.%s.rodando()" % gancho):
                        chegou = True
                        break
                    nav.esperar(0.25)
                confere("%s: uma visita chega logo (em ate 5 s)" % tema, chegou)
                nav.avaliar("document.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape', bubbles: true}))")
                nav.esperar(0.4)
                depois = json.loads(nav.avaliar(ESTADO))
                confere("%s: o Esc volta a tela" % tema,
                        depois["soFundo"] == "false" and depois["topo"] and depois["corpo"] and not depois["voltar"], depois)
                confere("%s: o foco volta ao botao" % tema, depois["foco"] == "btnVerAnimacao", depois)
                t = nav.avaliar("window.%s.avancar(5)" % gancho)
                px = base64.b64decode(nav.avaliar("window.%s.pixels()" % gancho))
                confere("%s: ganchos avancar() e pixels() (160 x 90 RGBA)" % tema,
                        isinstance(t, (int, float)) and len(px) == 160 * 90 * 4, "%r %d" % (t, len(px)))
            erros = nav.avaliar("JSON.stringify(window.__errosTeste)")
            confere("nenhum erro no console", erros == "[]", erros)
            nav.avaliar("document.body.dataset.fundoAnimado = 'automatico'")
    finally:
        servidor.terminate()
        try:
            servidor.wait(timeout=10)
        except subprocess.TimeoutExpired:
            servidor.kill()
    print("\nVisualizar animacao: %d de %d certos." % (total[0] - len(falhas), total[0]))
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
