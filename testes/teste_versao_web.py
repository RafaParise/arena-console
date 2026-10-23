# -*- coding: utf-8 -*-
r"""A versao web do ARENA (a da internet, GitHub Pages) num celular -- auditoria 4.
Pedido do Rafael (22/10/2026): o APK nao instalou no celular de um aluno
("Como o app nao e' compativel com seu smartphone, ele nao foi instalado",
num Galaxy A12 com Android 12); "pode preparar por favor, eu autorizo". A
versao web e' o modo do Chromebook (launcher\navegador) montado pelo
ferramentas\montar_site.py, com o controle de toque
(launcher\navegador\toque.js) e o layout de celular (estilo.css, ate 700 px).

O teste monta o site numa pasta temporaria, serve por http://127.0.0.1 e
abre no Edge sem janela imitando o Chrome do Android (toque, tela de
412x915, sem o seletor de pasta). Confere:
  1. o service worker fica no comando (a tela abre de novo sem internet);
  2. de pe: os consoles numa faixa no alto (nao uma coluna), a grade de
     jogos com 2 colunas, nada rolando para o lado e so os consoles com
     jogo na faixa;
  3. o aviso do alto oferece "Guardar um jogo" (e nao a pasta do pen drive);
  4. Guardar um jogo: o arquivo escolhido entra na lista e o aviso some;
  5. um jogo abre com o controle na tela, e o direcional e o A chegam ao
     jogo como as teclas do ARENA (seta e X);
  6. SELECT e START nao encostam no direcional nem no A/B/X/Y, de pe e
     deitado;
  7. SAIR: o primeiro toque pede confirmacao e o segundo fecha o jogo;
  8. no computador (sem toque): o controle na tela nao aparece e os
     consoles ficam na coluna da esquerda.
Uso: servidor\python\python.exe testes\teste_versao_web.py [--saida=arquivo.json] [--fotos=pasta]
"""
import functools
import http.server
import json
import os
import shutil
import sys
import tempfile
import threading
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(RAIZ, "ferramentas"))
import limpeza  # noqa: E402
import montar_site  # noqa: E402
import tela_sem_janela  # noqa: E402

CELULAR = ("Mozilla/5.0 (Linux; Android 12; SM-A125F) AppleWebKit/537.36 (KHTML, like Gecko) "
           "Chrome/130.0.0.0 Mobile Safari/537.36")
COMPUTADOR = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0")
# O Chrome do Android pode nao ter o seletor de pasta: o teste tira o do Edge.
SEM_PASTA = ("try { delete Window.prototype.showDirectoryPicker; } catch (e) {} "
             "try { delete window.showDirectoryPicker; } catch (e) {}")
JOGO_GUARDADO = os.path.join(AQUI, "jogos_livres", "CHIP-8", "slipperyslope.ch8")
LEIA_DO_RESULTADO = (
    "testes\\teste_versao_web.py: a versao web (ferramentas\\montar_site.py) servida por http://127.0.0.1 "
    "no Edge sem janela, imitando o Chrome do Android (toque, 412x915, sem seletor de pasta); depois "
    "deitado (915x412) e no computador (1366x768, sem toque). Retangulos em pontos CSS: [esquerda, alto, "
    "direita, baixo].")

ESTADO = """(() => {
  const t = document.querySelector('.trilho').getBoundingClientRect();
  const itens = [...document.querySelectorAll('#listaPlataformas > li')];
  const visiveis = itens.filter(e => e.offsetParent);
  const comJogo = itens.filter(e => Number((e.querySelector('.trilho-conta') || {}).textContent) > 0);
  const aviso = document.querySelector('#avisoPasta');
  return {
    jogos: document.querySelectorAll('#listaJogos [data-acao=jogar]').length,
    corpo: getComputedStyle(document.querySelector('.corpo')).flexDirection,
    faixa: [Math.round(t.width), Math.round(t.height)],
    colunas: getComputedStyle(document.querySelector('#listaJogos')).gridTemplateColumns.split(' ').length,
    rola_de_lado: document.documentElement.scrollWidth > innerWidth + 2,
    consoles_visiveis: visiveis.length, consoles_com_jogo: comJogo.length,
    visiveis_sem_jogo: visiveis.filter(e => !comJogo.includes(e)).length,
    aviso: aviso.hidden ? null : [document.querySelector('#avisoPastaTexto').innerText,
                                  document.querySelector('#btnPastaArena').dataset.acao],
    guardar_na_faixa: !!document.querySelector('#btnGuardarJogoTrilho').offsetParent,
    titulos: [...document.querySelectorAll('#listaJogos .jogo-titulo')].map(e => e.innerText),
    recado: (document.querySelector('#recado') || {}).innerText || '',
    service_worker: !!(navigator.serviceWorker && navigator.serviceWorker.controller),
  };
})()"""

# Os retangulos dos botoes do controle, dentro do quadro do jogo.
CONTROLE = """(() => {
  const q = document.querySelector('.partida-quadro');
  const d = q && q.contentDocument;
  const caixa = d && d.querySelector('#toque');
  if (!caixa) return null;
  const r = e => { const b = e.getBoundingClientRect(); return [b.left, b.top, b.right, b.bottom].map(Math.round); };
  return {
    visivel: !caixa.hidden && getComputedStyle(caixa).display !== 'none',
    meio: [...d.querySelectorAll('#toque .meio')].map(r),
    outros: [d.querySelector('#toque .dpad'), ...d.querySelectorAll('#toque .redondo')].filter(Boolean).map(r),
    sair: d.querySelector('#toque .sair') ? d.querySelector('#toque .sair').textContent : null,
  };
})()"""


class _Silencioso(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):      # noqa: A002 (o nome vem da classe de base)
        pass


def servir(pasta):
    servidor = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(_Silencioso, directory=pasta))
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    return servidor


def esperar(nav, expressao, segundos=40):
    fim = time.time() + segundos
    while time.time() < fim:
        try:
            if nav.avaliar(expressao):
                return True
        except OSError:
            pass
        time.sleep(0.5)
    return False


def tocar(nav, x, y):
    """Um toque de dedo (o Edge transforma em pointerdown e pointerup)."""
    nav.comando("Input.dispatchTouchEvent", type="touchStart", touchPoints=[{"x": x, "y": y}])
    time.sleep(0.08)
    nav.comando("Input.dispatchTouchEvent", type="touchEnd", touchPoints=[])
    time.sleep(0.08)


def centro_no_jogo(nav, seletor):
    """O centro de um elemento de dentro do quadro do jogo, na tela."""
    return nav.avaliar("""(() => {
      const q = document.querySelector('.partida-quadro'); if (!q) return null;
      const e = q.contentDocument && q.contentDocument.querySelector(%s); if (!e) return null;
      const a = q.getBoundingClientRect(), b = e.getBoundingClientRect();
      return [a.left + b.left + b.width / 2, a.top + b.top + b.height / 2, b.width];
    })()""" % json.dumps(seletor))


def encostam(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def nenhum_encosta(controle):
    return bool(controle and controle["meio"] and controle["outros"]) and not any(
        encostam(m, o) for m in controle["meio"] for o in controle["outros"])


def abrir_um_jogo(nav, com_toque=True):
    """Abre o primeiro jogo da lista e espera o quadro do jogo (e, no
    celular, o controle na tela; no computador o toque.js nem cria o
    controle)."""
    nav.avaliar("document.querySelector('#listaJogos [data-acao=jogar]').click(), true")
    pronto = "q.contentDocument.querySelector('#toque')" if com_toque else "q.contentWindow.ArenaJogo"
    return esperar(nav, "(() => { const q = document.querySelector('.partida-quadro');"
                        " return !!(q && q.contentDocument && %s); })()" % pronto, 60)


def apelido(nav):
    """Primeira vez no aparelho: o ARENA pede o apelido antes de tudo."""
    if nav.avaliar("!document.querySelector('#modalApelido').hidden"):
        nav.avaliar("document.getElementById('campoApelidoInicial').value = 'teste'; "
                    "document.getElementById('btnSalvarApelido').click(); 1")
        time.sleep(1)


def fechar_o_jogo(nav):
    nav.avaliar("(() => { const q = document.querySelector('.partida-quadro');"
                " const j = q && q.contentWindow && q.contentWindow.ArenaJogo; if (j) j.sair(); return !!j; })()")
    esperar(nav, "!document.querySelector('.partida-quadro')", 15)


def foto(nav, pasta, nome):
    if pasta:
        nav.foto(os.path.join(pasta, nome))


def no_celular(nav, endereco, trabalho, fotos):
    r = {}
    nav.comando("Page.enable")
    nav.antes_de_cada_pagina(SEM_PASTA)
    nav.comando("Emulation.setTouchEmulationEnabled", enabled=True, maxTouchPoints=5)
    nav.comando("Emulation.setUserAgentOverride", userAgent=CELULAR)
    nav.comando("Emulation.setDeviceMetricsOverride", width=412, height=915, deviceScaleFactor=2.625, mobile=True)
    nav.comando("Page.navigate", url=endereco)
    esperar(nav, "document.querySelectorAll('#listaJogos [data-acao=jogar]').length >= 5")
    apelido(nav)
    esperar(nav, "!!(navigator.serviceWorker && navigator.serviceWorker.controller)", 20)
    r["de_pe"] = nav.avaliar(ESTADO)
    foto(nav, fotos, "web-1-de-pe.png")

    # Guardar um jogo: o mesmo campo de arquivo que o botao abre no celular.
    arquivo = os.path.join(trabalho, "meu-jogo-teste.ch8")
    shutil.copyfile(JOGO_GUARDADO, arquivo)
    antes = r["de_pe"]["jogos"]
    raiz = nav.comando("DOM.getDocument", depth=1)["root"]["nodeId"]
    campo = nav.comando("DOM.querySelector", nodeId=raiz, selector="#campoGuardarJogo")["nodeId"]
    nav.comando("DOM.setFileInputFiles", files=[arquivo], nodeId=campo)
    esperar(nav, "document.querySelectorAll('#listaJogos [data-acao=jogar]').length > %d" % antes, 20)
    time.sleep(1)
    r["depois_de_guardar"] = nav.avaliar(ESTADO)
    foto(nav, fotos, "web-2-guardado.png")

    # Um jogo de pe: o controle, as teclas, SELECT e START, e o SAIR.
    r["jogo_abriu"] = abrir_um_jogo(nav)
    time.sleep(4)
    r["controle_de_pe"] = nav.avaliar(CONTROLE)
    foto(nav, fotos, "web-3-jogo-de-pe.png")
    nav.avaliar("""(() => { const w = document.querySelector('.partida-quadro').contentWindow;
      w.__teclas = []; w.addEventListener('keydown', e => w.__teclas.push(e.code), true); return true; })()""")
    x, y, largura = centro_no_jogo(nav, "#toque .dpad")
    tocar(nav, x, y - largura * 0.35)
    x, y, _ = centro_no_jogo(nav, "#toque .redondo")
    tocar(nav, x, y)
    r["teclas"] = nav.avaliar("document.querySelector('.partida-quadro').contentWindow.__teclas")
    x, y, _ = centro_no_jogo(nav, "#toque .sair")
    tocar(nav, x, y)
    r["sair_primeiro_toque"] = (nav.avaliar(CONTROLE) or {}).get("sair")
    r["aberto_depois_de_um_toque"] = bool(nav.avaliar("!!document.querySelector('.partida-quadro')"))
    tocar(nav, x, y)
    r["fechou"] = esperar(nav, "!document.querySelector('.partida-quadro')", 15)

    # Deitado.
    nav.comando("Emulation.setDeviceMetricsOverride", width=915, height=412, deviceScaleFactor=2.625, mobile=True)
    time.sleep(1.5)
    r["deitado"] = nav.avaliar(ESTADO)
    abrir_um_jogo(nav)
    time.sleep(3)
    r["controle_deitado"] = nav.avaliar(CONTROLE)
    foto(nav, fotos, "web-4-jogo-deitado.png")
    fechar_o_jogo(nav)
    return r


def no_computador(nav, endereco, fotos):
    r = {}
    nav.comando("Emulation.setTouchEmulationEnabled", enabled=False)
    nav.comando("Emulation.setUserAgentOverride", userAgent=COMPUTADOR)
    nav.comando("Emulation.setDeviceMetricsOverride", width=1366, height=768, deviceScaleFactor=1, mobile=False)
    nav.comando("Page.navigate", url=endereco)
    esperar(nav, "document.querySelectorAll('#listaJogos [data-acao=jogar]').length >= 5")
    apelido(nav)
    r["tela"] = nav.avaliar(ESTADO)
    r["jogo_abriu"] = abrir_um_jogo(nav, com_toque=False)
    time.sleep(3)
    r["controle"] = nav.avaliar(CONTROLE)
    foto(nav, fotos, "web-5-computador.png")
    fechar_o_jogo(nav)
    return r


def conferir(c, p):
    de_pe, guardado, deitado = c.get("de_pe") or {}, c.get("depois_de_guardar") or {}, c.get("deitado") or {}
    tela = p.get("tela") or {}
    return [
        ("o service worker fica no comando (abre de novo sem internet)", de_pe.get("service_worker") is True),
        ("de pé: os consoles numa faixa no alto, na largura toda",
         de_pe.get("corpo") == "column" and (de_pe.get("faixa") or [0, 999])[1] < 120
         and (de_pe.get("faixa") or [0])[0] >= 400),
        ("de pé: a grade de jogos com 2 colunas", de_pe.get("colunas") == 2),
        ("de pé: nada rola para o lado", de_pe.get("rola_de_lado") is False),
        ("no celular: só os consoles com jogo aparecem na faixa",
         de_pe.get("visiveis_sem_jogo") == 0 and de_pe.get("consoles_visiveis") == de_pe.get("consoles_com_jogo")),
        ("o aviso oferece Guardar um jogo (e não a pasta)",
         bool(de_pe.get("aviso")) and de_pe["aviso"][1] == "guardar" and "Guardar um jogo" in de_pe["aviso"][0]),
        ("Guardar um jogo também está na faixa dos consoles", de_pe.get("guardar_na_faixa") is True),
        ("o jogo guardado entra na lista e o aviso some",
         guardado.get("jogos") == de_pe.get("jogos", -1) + 1 and guardado.get("aviso") is None
         and "Meu Jogo Teste" in (guardado.get("titulos") or [])),
        ("o recado diz que o jogo ficou no aparelho", "neste aparelho" in guardado.get("recado", "")),
        ("o jogo abre com o controle na tela", c.get("jogo_abriu") is True
         and (c.get("controle_de_pe") or {}).get("visivel") is True),
        ("o direcional e o A chegam ao jogo (seta e X)",
         "ArrowUp" in (c.get("teclas") or []) and "KeyX" in (c.get("teclas") or [])),
        ("de pé: SELECT e START não encostam no direcional nem no A/B/X/Y",
         nenhum_encosta(c.get("controle_de_pe"))),
        ("SAIR: o primeiro toque só pede confirmação",
         c.get("sair_primeiro_toque") == "TOQUE DE NOVO" and c.get("aberto_depois_de_um_toque") is True),
        ("SAIR: o segundo toque fecha o jogo", c.get("fechou") is True),
        ("deitado: nada rola para o lado", deitado.get("rola_de_lado") is False),
        ("deitado: SELECT e START não encostam no direcional nem no A/B/X/Y",
         nenhum_encosta(c.get("controle_deitado"))),
        ("no computador: os consoles ficam na coluna da esquerda",
         tela.get("corpo") == "row" and (tela.get("faixa") or [999])[0] < 400),
        ("no computador: o jogo abre sem o controle na tela",
         p.get("jogo_abriu") is True and not (p.get("controle") or {}).get("visivel")),
    ]


def argumento(nome, padrao):
    for a in sys.argv[1:]:
        if a.startswith("--%s=" % nome):
            return a.split("=", 1)[1]
    return padrao


def main():
    saida = argumento("saida", os.path.join(tempfile.gettempdir(), "teste_versao_web.json"))
    fotos = argumento("fotos", "")
    if fotos:
        os.makedirs(fotos, exist_ok=True)
    if not os.path.isfile(os.path.join(RAIZ, "launcher", "navegador", "nucleos", "lista.js")):
        print("Faltam os nucleos do navegador: rode ferramentas\\preparar_nucleos_navegador.py.")
        return 2
    trabalho = tempfile.mkdtemp(prefix="arena-web-")
    servidor = None
    celular, computador = {}, {}
    try:
        site = os.path.join(trabalho, "site")
        montado = montar_site.montar(site)
        servidor = servir(site)
        endereco = "http://127.0.0.1:%d/" % servidor.server_address[1]
        print("== Versao web %s (%s MB) em %s" % (montado["versao"], montado["total_mb"], endereco))
        try:
            with tela_sem_janela.Navegador(tamanho=(412, 915)) as nav:
                celular = no_celular(nav, endereco, trabalho, fotos)
        except (OSError, ValueError, KeyError, TypeError) as falha:
            celular = {"falha": str(falha)}
        try:
            with tela_sem_janela.Navegador(tamanho=(1366, 768)) as nav:
                computador = no_computador(nav, endereco, fotos)
        except (OSError, ValueError, KeyError, TypeError) as falha:
            computador = {"falha": str(falha)}
    finally:
        if servidor:
            servidor.shutdown()
        limpeza.apagar_pasta(trabalho)
    conferencias = conferir(celular, computador)
    for item, passou in conferencias:
        print("  [%s] %s" % ("OK" if passou else "FALHOU", item))
    for parte in (celular, computador):
        if parte.get("falha"):
            print("  falha:", parte["falha"])
    os.makedirs(os.path.dirname(os.path.abspath(saida)), exist_ok=True)
    with open(saida, "w", encoding="utf-8") as arquivo:
        json.dump({"_leia": LEIA_DO_RESULTADO, "data": time.strftime("%Y-%m-%d %H:%M"), "celular": celular,
                   "computador": computador, "conferencias": conferencias}, arquivo, ensure_ascii=False, indent=1)
    falhas = sum(1 for _item, passou in conferencias if not passou)
    print()
    print("Versao web: %d de %d certos. Resultado: %s" % (len(conferencias) - falhas, len(conferencias), saida))
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
