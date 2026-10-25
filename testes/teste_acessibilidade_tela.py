# -*- coding: utf-8 -*-
r"""Acessibilidade da tela, conferida na tela de verdade (os dois temas).

Auditoria 3, Fase 7. O roteiro pede: "Navegacao so por teclado, contraste,
tamanho de letra, icone sempre com texto, nada de parede de texto, menos
animacao quando o Windows pedir." Este teste abre a tela do ARENA numa
copia isolada (Edge sem janela, 1366 x 768), passa por TODAS as gavetas e
abas (Perfil, Como colocar jogos, Biblioteca, Ajustes, Conquistas, Recordes,
Jogo) e confere, em cada uma:
  1. todo botao e link tem nome (texto, aria-label ou title);
  2. botao so com icone (sem duas letras seguidas) tem aria-label ou title;
  3. todo campo (input, select, textarea) tem rotulo;
  4. toda imagem tem alt;
  5. nenhum tabindex positivo (ele baguncaria a ordem do Tab);
  6. contraste do texto com o fundo (WCAG AA: 4,5:1; texto grande, 3:1),
     nos dois temas;
  7. a menor letra visivel (para quem tem dislexia, quanto maior melhor);
  8. nenhum elemento escondido (atributo hidden) aparece: uma classe com
     display: flex ou grid passava por cima do hidden -- a mensagem "Nenhum
     jogo na lista ainda" embaixo dos jogos, o "Mover para a pasta certa" em
     todo jogo e a chave "Estamos em casas diferentes" que a Fase 4 tinha
     tirado (achado da Fase 7). Tambem na janela do Jogar Junto.
"Menos animacao quando o Windows pedir" e' do testes\teste_fundos_animados.py.

Uso: servidor\python\python.exe testes\teste_acessibilidade_tela.py
"""
import json
import os
import socket
import sys
import tempfile
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import limpeza  # noqa: E402
import tela_sem_janela  # noqa: E402
import teste_servidor_que_cai as servidor_de_teste  # noqa: E402

GAVETAS = ["gavetaPerfil", "gavetaComoColocar", "gavetaAcervo", "gavetaAjustes", "gavetaConquistas",
           "gavetaRecordes", "gavetaJogo"]
LETRA_MINIMA_PX = 11.0

CONFERIR = r"""
(() => {
  const r = {semNome: [], soIcone: [], camposSemRotulo: [], imagensSemAlt: [], tabindexPositivo: [],
             contrasteBaixo: [], menorLetra: 999, menorLetraOnde: "", textosVistos: 0,
             escondidoAparece: []};
  for (const el of document.querySelectorAll("[hidden]")) {
    if (getComputedStyle(el).display === "none") continue;
    let dentroDeEscondido = false;
    for (let p = el.parentElement; p; p = p.parentElement)
      if (getComputedStyle(p).display === "none") { dentroDeEscondido = true; break; }
    if (!dentroDeEscondido) r.escondidoAparece.push("#" + el.id + " (" + getComputedStyle(el).display + ")");
  }
  const visivel = el => { const s = getComputedStyle(el);
    return s.display !== "none" && s.visibility !== "hidden" && el.getClientRects().length > 0; };
  const quem = el => "#" + (el.id || "") + "." + (el.className && el.className.baseVal === undefined
    ? String(el.className).split(" ")[0] : "") + " " + (el.textContent || "").trim().slice(0, 40);
  const nomeDe = el => {
    let n = (el.getAttribute("aria-label") || "").trim();
    if (!n && el.getAttribute("aria-labelledby")) {
      n = el.getAttribute("aria-labelledby").split(" ").map(id => (document.getElementById(id) || {}).textContent || "").join(" ").trim();
    }
    return n || (el.textContent || "").trim() || (el.getAttribute("title") || "").trim();
  };
  for (const el of document.querySelectorAll("button, [role=button], a[href]")) {
    if (!visivel(el)) continue;
    const nome = nomeDe(el);
    if (!nome) r.semNome.push(quem(el));
    else if (!/[A-Za-zÀ-ú]{2}/.test(nome)) r.soIcone.push(quem(el) + " -> " + nome);
  }
  for (const el of document.querySelectorAll("input:not([type=hidden]), select, textarea")) {
    if (!visivel(el)) continue;
    const rotulo = (el.labels && el.labels.length) || el.getAttribute("aria-label") ||
                   el.getAttribute("aria-labelledby") || el.getAttribute("title");
    if (!rotulo) r.camposSemRotulo.push(quem(el));
  }
  for (const el of document.querySelectorAll("img")) {
    if (visivel(el) && !el.hasAttribute("alt")) r.imagensSemAlt.push((el.getAttribute("src") || "").slice(-60));
  }
  for (const el of document.querySelectorAll("[tabindex]")) {
    if (parseInt(el.getAttribute("tabindex"), 10) > 0) r.tabindexPositivo.push(quem(el));
  }
  // "rgb(255, 255, 255)" ou "color(srgb 1 1 1 / 0.94)": no segundo, as tres
  // cores vem de 0 a 1 (sem isso, o branco translucido virava preto e o
  // texto do tema claro "reprovava" com 3,6:1 -- o contraste contra o preto).
  const rgb = c => { const v = (c.match(/[\d.]+/g) || []).map(Number);
    return c.startsWith("color(srgb") ? v.map((x, i) => (i < 3 ? x * 255 : x)) : v; };
  const lum = c => { const [a, b, d] = rgb(c).slice(0, 3).map(x => { x /= 255;
      return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4); });
    return 0.2126 * a + 0.7152 * b + 0.0722 * d; };
  // O fundo de verdade: o primeiro ancestral com cor quase opaca (os paineis
  // ficam por cima do ceu/campo animado; com transparencia demais, pula).
  const fundo = el => { for (let e = el; e; e = e.parentElement) {
      const v = rgb(getComputedStyle(e).backgroundColor);
      if (v.length >= 3 && (v.length < 4 || v[3] >= 0.75)) return getComputedStyle(e).backgroundColor; }
    return null; };
  const ja = new Set();
  for (const el of document.querySelectorAll("body *")) {
    if (!visivel(el) || ["SCRIPT", "STYLE", "CANVAS", "svg", "path"].includes(el.tagName)) continue;
    const proprio = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim().length > 1);
    if (!proprio) continue;
    const s = getComputedStyle(el);
    if (parseFloat(s.opacity) < 0.6) continue;           // apagado de proposito (ex.: desativado)
    // O logotipo (o nome ARENA no alto, amarelo com sombra roxa) e' isento:
    // a WCAG 1.4.3 nao pede contraste para texto que e' parte de um logotipo.
    if (el.closest(".marca-nome")) continue;
    r.textosVistos++;
    const tamanho = parseFloat(s.fontSize);
    if (tamanho < r.menorLetra) { r.menorLetra = tamanho; r.menorLetraOnde = quem(el); }
    const f = fundo(el);
    if (!f) continue;
    const a = lum(s.color), b = lum(f);
    const contraste = (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
    const grande = tamanho >= 24 || (tamanho >= 18.66 && parseInt(s.fontWeight, 10) >= 700);
    if (contraste < (grande ? 3 : 4.5)) {
      const chave = s.color + "|" + f + "|" + el.className;
      if (!ja.has(chave)) { ja.add(chave);
        r.contrasteBaixo.push(quem(el) + " -> " + contraste.toFixed(2) + ":1 (" + s.color + " sobre " + f + ")"); }
    }
  }
  return r;
})()
"""


def porta_livre():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main():
    falhas, total = [], [0]

    def confere(nome, ok, detalhe=""):
        total[0] += 1
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, "" if ok else detalhe), flush=True)
        if not ok:
            falhas.append(nome)

    base = tempfile.mkdtemp(prefix="arena_acessibilidade_")
    processo = None
    try:
        copia = os.path.join(base, "ARENA")
        servidor_de_teste.preparar_copia(copia)
        porta = porta_livre()
        processo = servidor_de_teste.subir(copia, porta, False, os.path.join(base, "sem-trava"))
        if not servidor_de_teste.esperar_servidor(porta, segundos=60):
            print("FALHOU: o servidor da copia nao abriu.")
            return 1
        resultados = {}
        with tela_sem_janela.Navegador() as nav:
            nav.abrir("http://127.0.0.1:%d/" % porta, largura=1366, altura=768, espera=4)
            for tema in ("escuro", "claro"):
                nav.avaliar("document.body.dataset.tema = '%s'; 1" % tema)
                telas = {"principal": nav.avaliar(CONFERIR)}
                for gaveta in GAVETAS:
                    nav.avaliar("abrirGaveta('%s'); for (const p of document.querySelectorAll('#%s .aba-conteudo')) "
                                "p.hidden = false; 1" % (gaveta, gaveta))
                    time.sleep(0.4)
                    telas[gaveta] = nav.avaliar(CONFERIR)
                nav.avaliar("abrirGaveta(''); document.querySelector('#modalPartida').hidden = false; 1")
                time.sleep(0.4)
                telas["janelaJogarJunto"] = nav.avaliar(CONFERIR)
                nav.avaliar("document.querySelector('#modalPartida').hidden = true; 1")
                resultados[tema] = telas
            # 9. O foco entra na janela que abre e volta para quem abriu.
            foco = {}
            for nome, abrir in (("gaveta de Ajustes", "document.querySelector('#btnAjustes').click()"),
                                ("janela do Jogar Junto", "document.querySelector('#modalPartida').hidden = false")):
                nav.avaliar("abrirGaveta(''); document.querySelector('#modalPartida').hidden = true; "
                            "document.querySelector('#btnAjustes').focus(); 1")
                time.sleep(0.3)
                nav.avaliar(abrir + "; 1")
                time.sleep(0.5)
                foco[nome + ": entra"] = nav.avaliar(
                    "(() => { const a = document.activeElement; return !!(a && a.closest('.modal:not([hidden]), "
                    ".gaveta:not([hidden])')); })()")
                nav.avaliar("document.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape'})); 1")
                time.sleep(0.5)
                foco[nome + ": volta"] = nav.avaliar("document.activeElement && document.activeElement.id === 'btnAjustes'")
            # 10. Janela aberta: o fundo sai do Tab e do leitor de tela (inert). Janela sempre; gaveta so quando cobre a
            # tela (o celular): numa tela larga ela e' um painel do lado e a biblioteca segue usavel. Achado de 25/10/2026,
            # medido no A12: o fundo ficava exposto atras de todas as gavetas e janelas.
            lido = ("JSON.stringify({fundo: [...document.querySelectorAll('header.painel-topo, main.corpo')].map(e => e.inert), "
                    "aberta: [...document.querySelectorAll('.modal:not([hidden]), .gaveta:not([hidden])')].map(e => e.id + ':' + e.inert)})")
            isolamento = {}
            nav.abrir("http://127.0.0.1:%d/" % porta, largura=1366, altura=768, espera=3)
            # a janela do apelido (primeiro acesso) abre sozinha numa copia nova e nao conta nesta medida
            nav.avaliar("document.querySelector('#modalApelido').hidden = true; abrirGaveta(''); 1")
            time.sleep(0.2)
            isolamento["larga, sem janela"] = json.loads(nav.avaliar(lido))
            nav.avaliar("document.querySelector('#modalPartida').hidden = false; 1")
            time.sleep(0.2)
            isolamento["larga, com janela"] = json.loads(nav.avaliar(lido))
            nav.avaliar("document.querySelector('#modalPartida').hidden = true; abrirGaveta('gavetaAjustes'); 1")
            time.sleep(0.2)
            isolamento["larga, com gaveta do lado"] = json.loads(nav.avaliar(lido))
            nav.avaliar("document.querySelector('#modalPartida').hidden = false; 1")
            time.sleep(0.2)
            isolamento["larga, janela por cima da gaveta"] = json.loads(nav.avaliar(lido))
            nav.avaliar("document.querySelector('#modalPartida').hidden = true; abrirGaveta(''); 1")
            time.sleep(0.2)
            isolamento["larga, tudo fechado de novo"] = json.loads(nav.avaliar(lido))
            nav.abrir("http://127.0.0.1:%d/" % porta, largura=412, altura=800, espera=3)
            nav.avaliar("document.querySelector('#modalApelido').hidden = true; abrirGaveta('gavetaAjustes'); 1")
            time.sleep(0.2)
            isolamento["celular, com gaveta"] = json.loads(nav.avaliar(lido))
            nav.avaliar("document.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape'})); 1")
            time.sleep(0.3)
            isolamento["celular, depois do Esc"] = json.loads(nav.avaliar(lido))
        destino = os.path.join(os.path.dirname(AQUI), "docs", "auditoria3", "acessibilidade.json")
        with open(destino, "w", encoding="utf-8") as f:
            json.dump(resultados, f, ensure_ascii=False, indent=1)

        def juntar(campo):
            saida = []
            for tema, telas in resultados.items():
                for onde, r in telas.items():
                    for item in (r or {}).get(campo, []):
                        linha = "%s/%s: %s" % (tema, onde, item)
                        if linha not in saida:
                            saida.append(linha)
            return saida

        vistos = sum((r or {}).get("textosVistos", 0) for telas in resultados.values() for r in telas.values())
        menor = min(((r or {}).get("menorLetra", 999), (r or {}).get("menorLetraOnde", ""))
                    for telas in resultados.values() for r in telas.values())
        print("Textos conferidos: %d; menor letra visivel: %.1f px (%s)" % (vistos, menor[0], menor[1]))
        confere("todo botao e link tem nome", not juntar("semNome"), juntar("semNome")[:10])
        confere("botao so com icone tem nome escrito (aria-label ou title)", not juntar("soIcone"),
                juntar("soIcone")[:10])
        confere("todo campo tem rotulo", not juntar("camposSemRotulo"), juntar("camposSemRotulo")[:10])
        confere("toda imagem tem texto alternativo", not juntar("imagensSemAlt"), juntar("imagensSemAlt")[:10])
        confere("nenhum tabindex positivo", not juntar("tabindexPositivo"), juntar("tabindexPositivo")[:10])
        baixos = juntar("contrasteBaixo")
        confere("contraste do texto (AA) nos dois temas (%d casos abaixo)" % len(baixos), not baixos, baixos[:12])
        confere("menor letra visivel de pelo menos %.0f px" % LETRA_MINIMA_PX, menor[0] >= LETRA_MINIMA_PX, menor)
        confere("nenhum elemento escondido (hidden) aparece na tela", not juntar("escondidoAparece"),
                juntar("escondidoAparece")[:10])
        sem_foco = [k for k, v in foco.items() if v is not True]
        confere("o foco entra na janela que abre e volta para quem abriu (Esc)", not sem_foco, sem_foco)
        esperado = {
            "larga, sem janela": ([False, False], []),
            "larga, com janela": ([True, True], ["modalPartida:false"]),
            "larga, com gaveta do lado": ([False, False], ["gavetaAjustes:false"]),
            "larga, janela por cima da gaveta": ([True, True], ["gavetaAjustes:true", "modalPartida:false"]),
            "larga, tudo fechado de novo": ([False, False], []),
            "celular, com gaveta": ([True, True], ["gavetaAjustes:false"]),
            "celular, depois do Esc": ([False, False], []),
        }
        erradas = ["%s: veio %s, esperava %s" % (nome, isolamento.get(nome), esperado[nome]) for nome in esperado
                   if (isolamento.get(nome, {}).get("fundo"), sorted(isolamento.get(nome, {}).get("aberta", [])))
                   != (esperado[nome][0], sorted(esperado[nome][1]))]
        confere("janela aberta tira o fundo do Tab e do leitor de tela (inert); gaveta so no celular", not erradas,
                "; ".join(erradas))
    finally:
        if processo:
            servidor_de_teste.derrubar(processo)
        limpeza.apagar_pasta(base)

    print()
    if falhas:
        print("FALHOU: %d de %d" % (len(falhas), total[0]))
        return 1
    print("Acessibilidade da tela: %d de %d certos." % (total[0], total[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
