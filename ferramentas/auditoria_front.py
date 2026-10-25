# -*- coding: utf-8 -*-
r"""Auditoria do front-end do ARENA, sem pip e sem janela: mede em vez de opinar.

O que faz: abre uma COPIA do ARENA (testes\copia_do_arena.py, numa pasta com acento, com um jogo de mentira de PS1),
abre a tela no Edge sem janela (testes\tela_sem_janela.py) em 4 tamanhos (celular 360x740, tablet 768x1024, notebook
1280x800, tela grande 1920x1080) e nos dois temas (claro e escuro) e, em cada tela, gaveta e janela do ARENA:

  - roda o axe-core (a regra de acessibilidade mais usada do mundo, MPL-2.0, baixado uma vez e guardado no cache);
  - confere por conta propria o que o axe nao pega: estouro para os lados, nome acessivel de botoes e campos, alvo de
    toque pequeno (24 px e' o minimo da WCAG 2.2 AA; 44 px, o confortavel; o Android pede 48), contraste do texto
    CALCULADO (fundo opaco mais proximo; fundo com imagem ou translucido sai como "nao medido"), texto abaixo de 12 px,
    id repetido, imagem sem alt, ordem dos titulos, tabindex positivo, movimento sem o "reduzir movimento";
  - tira uma foto de cada uma (so celular e notebook), para olhar.

Saida: docs\auditoria5\front.json (os numeros) e as fotos na pasta pedida (fora do git). Uso:
    servidor\python\python.exe ferramentas\auditoria_front.py [--fotos PASTA] [--rapido]
(--rapido: so celular e notebook, so o tema claro e escuro do notebook; para conferir um conserto)
"""
import argparse
import json
import os
import sys
import time
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "testes"))
import copia_do_arena as c  # noqa: E402
import limpeza  # noqa: E402
from tela_sem_janela import Navegador  # noqa: E402

AXE = {
    "versao": "4.10.2",
    "enderecos": ["https://cdn.jsdelivr.net/npm/axe-core@4.10.2/axe.min.js",
                  "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.2/axe.min.js"],
}
TAMANHOS = [("celular", 360, 740), ("tablet", 768, 1024), ("notebook", 1280, 800), ("tela_grande", 1920, 1080)]
TEMAS = ["claro", "escuro"]

CHECAGENS = r"""
(() => {
  const saida = {};
  const visivel = (el) => {
    if (el.closest('details:not([open])') && !el.closest('summary')) return false;   // dentro de <details> fechado nao aparece
    const r = el.getBoundingClientRect(), s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none' && parseFloat(s.opacity) > 0;
  };
  const seletor = (el) => {
    const partes = [];
    for (let n = el, i = 0; n && n.nodeType === 1 && i < 3; n = n.parentElement, i++) {
      let p = n.tagName.toLowerCase();
      if (n.id) { p += '#' + n.id; partes.unshift(p); break; }
      if (n.classList.length) p += '.' + [...n.classList].slice(0, 2).join('.');
      partes.unshift(p);
    }
    return partes.join(' > ');
  };
  const amostra = (lista, n = 12) => lista.slice(0, n);

  saida.estouro_horizontal_px = document.documentElement.scrollWidth - window.innerWidth;

  const semNome = [];
  for (const el of document.querySelectorAll('button, [role=button], a[href], input, select, textarea, [role=tab], [role=switch], [role=checkbox]')) {
    if (!visivel(el) || el.type === 'hidden') continue;
    const nome = (el.getAttribute('aria-label') || el.getAttribute('aria-labelledby') || el.getAttribute('title') ||
                  el.innerText || (['button', 'submit', 'reset'].includes(el.type) ? el.value : '') || el.getAttribute('placeholder') || '').trim();
    const rotulado = el.labels && el.labels.length > 0;
    if (!nome && !rotulado) semNome.push(seletor(el));
  }
  saida.sem_nome_acessivel = { total: semNome.length, amostra: amostra(semNome) };

  const pequenos24 = [], pequenos44 = [];
  for (const el of document.querySelectorAll('button, a[href], input:not([type=hidden]), select, [role=tab], [role=switch]')) {
    if (!visivel(el)) continue;
    const r = el.getBoundingClientRect();
    const menor = Math.min(r.width, r.height);
    if (menor < 24) pequenos24.push(seletor(el) + ' ' + Math.round(r.width) + 'x' + Math.round(r.height));
    else if (menor < 44) pequenos44.push(seletor(el) + ' ' + Math.round(r.width) + 'x' + Math.round(r.height));
  }
  saida.alvo_menor_que_24px = { total: pequenos24.length, amostra: amostra(pequenos24) };
  saida.alvo_entre_24_e_44px = { total: pequenos44.length, amostra: amostra(pequenos44, 6) };

  const parse = (c) => {
    const m = c.match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const p = m[1].split(/[ ,\/]+/).filter(Boolean).map(Number);
    return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 };
  };
  const lin = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
  const lum = (c) => 0.2126 * lin(c.r) + 0.7152 * lin(c.g) + 0.0722 * lin(c.b);
  const misturar = (topo, base) => ({ r: topo.r * topo.a + base.r * (1 - topo.a), g: topo.g * topo.a + base.g * (1 - topo.a), b: topo.b * topo.a + base.b * (1 - topo.a), a: 1 });
  const fundoDe = (el) => {
    const camadas = [];
    for (let n = el; n; n = n.parentElement) {
      const s = getComputedStyle(n);
      if (s.backgroundImage && s.backgroundImage !== 'none') return { complexo: true };
      const bg = parse(s.backgroundColor);
      if (bg && bg.a > 0) { camadas.push(bg); if (bg.a >= 1) break; }
    }
    let base = camadas.length && camadas[camadas.length - 1].a >= 1 ? camadas.pop() : null;
    if (!base) return { translucido: true };
    while (camadas.length) base = misturar(camadas.pop(), base);
    return { cor: base };
  };
  const falhas = [], naoMedido = { fundo_com_imagem: 0, fundo_translucido: 0, cor_estranha: 0 };
  let medidos = 0;
  const andador = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const vistos = new Set();
  for (let t = andador.nextNode(); t; t = andador.nextNode()) {
    if (!t.textContent.trim()) continue;
    const el = t.parentElement;
    if (!el || vistos.has(el) || !visivel(el) || ['SCRIPT', 'STYLE', 'NOSCRIPT'].includes(el.tagName)) continue;
    vistos.add(el);
    const s = getComputedStyle(el);
    const frente = parse(s.color);
    if (!frente) { naoMedido.cor_estranha++; continue; }
    const fundo = fundoDe(el);
    if (fundo.complexo) { naoMedido.fundo_com_imagem++; continue; }
    if (fundo.translucido) { naoMedido.fundo_translucido++; continue; }
    const cor = frente.a < 1 ? misturar(frente, fundo.cor) : frente;
    const l1 = lum(cor), l2 = lum(fundo.cor);
    const razao = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
    const tam = parseFloat(s.fontSize), negrito = parseInt(s.fontWeight, 10) >= 700;
    const grande = tam >= 24 || (tam >= 18.66 && negrito);
    const minimo = grande ? 3 : 4.5;
    medidos++;
    if (razao < minimo) falhas.push({ razao: Math.round(razao * 100) / 100, minimo, tam: Math.round(tam), seletor: seletor(el), texto: t.textContent.trim().slice(0, 40), cor: s.color, fundo: 'rgb(' + [fundo.cor.r, fundo.cor.g, fundo.cor.b].map(Math.round).join(',') + ')' });
  }
  falhas.sort((a, b) => a.razao - b.razao);
  saida.contraste = { medidos, nao_medido: naoMedido, falhas: falhas.length, piores: falhas.slice(0, 10) };

  const pequeno = [];
  for (const el of document.querySelectorAll('body *')) {
    if (!visivel(el) || !el.childNodes.length) continue;
    const proprio = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    if (proprio && parseFloat(getComputedStyle(el).fontSize) < 12) pequeno.push(seletor(el) + ' ' + getComputedStyle(el).fontSize);
  }
  saida.texto_menor_que_12px = { total: pequeno.length, amostra: amostra(pequeno, 6) };

  const ids = {}; for (const el of document.querySelectorAll('[id]')) ids[el.id] = (ids[el.id] || 0) + 1;
  saida.id_repetido = Object.entries(ids).filter(([, n]) => n > 1).map(([id, n]) => id + ' x' + n);
  saida.imagem_sem_alt = [...document.querySelectorAll('img:not([alt])')].filter(visivel).map(seletor).slice(0, 8);
  saida.tabindex_positivo = [...document.querySelectorAll('[tabindex]')].filter(e => parseInt(e.getAttribute('tabindex'), 10) > 0).map(seletor).slice(0, 8);
  const titulos = [...document.querySelectorAll('h1, h2, h3, h4, h5, h6')].filter(visivel).map(h => +h.tagName[1]);
  saida.titulos = { h1: titulos.filter(n => n === 1).length, pulos: titulos.filter((n, i) => i && n - titulos[i - 1] > 1).length };
  saida.zoom_bloqueado = /user-scalable\s*=\s*(no|0)|maximum-scale\s*=\s*1(\.0)?\b/.test((document.querySelector('meta[name=viewport]') || {}).content || '');
  saida.lang = document.documentElement.lang;
  let reduzir = 0;
  try { for (const folha of document.styleSheets) for (const r of folha.cssRules) if (r.conditionText && /prefers-reduced-motion/.test(r.conditionText)) reduzir++; } catch (e) { reduzir = -1; }
  saida.regras_reduzir_movimento = reduzir;
  const animados = [...document.querySelectorAll('canvas')].filter(visivel).length;
  saida.canvas_visiveis = animados;
  return JSON.stringify(saida);
})()
"""

AXE_EXEC = r"""
(async () => {
  const r = await axe.run(document, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa', 'best-practice'] }, resultTypes: ['violations'] });
  return JSON.stringify(r.violations.map(v => ({ id: v.id, impacto: v.impact, ajuda: v.help, nos: v.nodes.length,
    amostra: v.nodes.slice(0, 4).map(n => ({ alvo: n.target.join(' '), html: n.html.slice(0, 110) })) })));
})()
"""


def baixar_o_axe():
    """O axe.min.js na pasta de cache (uma vez so; fora do git)."""
    cache = os.path.join(os.environ.get("LOCALAPPDATA") or os.path.expanduser("~"), "ARENA-android", "cache")
    os.makedirs(cache, exist_ok=True)
    arquivo = os.path.join(cache, "axe-core-%s.min.js" % AXE["versao"])
    if os.path.isfile(arquivo) and os.path.getsize(arquivo) > 100000:
        return open(arquivo, encoding="utf-8").read()
    ultimo = None
    for endereco in AXE["enderecos"]:
        try:
            with urllib.request.urlopen(endereco, timeout=60) as resposta:
                texto = resposta.read().decode("utf-8")
            if "axe" in texto[:400].lower() and len(texto) > 100000:
                with open(arquivo, "w", encoding="utf-8") as saida:
                    saida.write(texto)
                return texto
        except OSError as falha:
            ultimo = falha
    raise SystemExit("Nao consegui baixar o axe-core (%s). Sem internet, ponha o axe.min.js em %s" % (ultimo, arquivo))


def estados(nav):
    """(nome, JS que liga o estado, JS que desliga) de cada tela, gaveta (e aba de gaveta) e janela do ARENA."""
    lista = [("inicio", "1", "1")]
    lista.append(("detalhes_do_jogo", "selecionarJogo(estado.jogos[0]); true", "1"))
    gavetas = nav.avaliar("JSON.stringify([...document.querySelectorAll('.gaveta')].map(g => ({id: g.id, abas: [...g.querySelectorAll('[role=tab]')].map(a => a.dataset.aba)})))")
    for g in json.loads(gavetas):
        ligar = "abrirGaveta('%s'); true" % g["id"]
        desligar = "document.querySelector('#%s').hidden = true; true" % g["id"]
        if g["abas"]:
            for aba in g["abas"]:
                lista.append(("%s:%s" % (g["id"], aba), ligar + "; document.querySelector('#%s [data-aba=\"%s\"]').click(); true" % (g["id"], aba), desligar))
        else:
            lista.append((g["id"], ligar, desligar))
    modais = nav.avaliar("JSON.stringify([...document.querySelectorAll('.modal')].map(m => m.id))")
    for m in json.loads(modais):
        lista.append((m, "document.querySelector('#%s').hidden = false; true" % m, "document.querySelector('#%s').hidden = true; true" % m))
    return lista


def main():
    parser = argparse.ArgumentParser(description="Auditoria do front-end do ARENA (axe-core, contraste calculado, alvos de toque, fotos)")
    parser.add_argument("--fotos", default=os.path.join(os.environ.get("TEMP", "."), "arena_fotos_front"))
    parser.add_argument("--rapido", action="store_true")
    parser.add_argument("--saida", default=os.path.join(RAIZ, "docs", "auditoria5", "front.json"))
    argumentos = parser.parse_args()

    axe = baixar_o_axe()
    os.makedirs(argumentos.fotos, exist_ok=True)
    if c.porta_ocupada():
        print("Ja ha um servidor na porta da copia (%d): feche-o antes." % c.PORTA)
        return 1
    tamanhos = [t for t in TAMANHOS if not argumentos.rapido or t[0] in ("celular", "notebook")]
    trabalho, copia = c.nova_pasta()
    falso = os.path.join(trabalho, "Jogo de teste (USA).iso")
    with open(falso, "wb") as arquivo:
        arquivo.write(bytes(4096))
    servidor = None
    resultado = {"axe": AXE["versao"], "feito_em": time.strftime("%Y-%m-%d %H:%M"), "telas": []}
    try:
        c.montar(copia, [], {"PS1": [falso]})
        servidor = c.subir_servidor(copia, os.path.join(trabalho, "servidor.log"))
        pedido = urllib.request.Request("http://127.0.0.1:%d/api/config" % c.PORTA, data=json.dumps({"apelido": "Teste"}).encode(),
                                        headers={"Content-Type": "application/json"}, method="POST")
        urllib.request.urlopen(pedido, timeout=30).read()
        c.pedir("/api/indexar", {}, espera=60)
        with Navegador() as nav:
            for nome_tamanho, largura, altura in tamanhos:
                for tema in TEMAS:
                    nav.abrir("http://127.0.0.1:%d/" % c.PORTA, largura=largura, altura=altura, espera=3)
                    nav.avaliar("document.body.dataset.tema = '%s'; true" % ("escuro" if tema == "escuro" else "claro"))
                    for _ in range(40):
                        if nav.avaliar("typeof estado !== 'undefined' && estado.jogos.length > 0"):
                            break
                        time.sleep(0.5)
                    nav.avaliar(axe + "; true")
                    fotografar = nome_tamanho in ("celular", "notebook")
                    for nome, ligar, desligar in estados(nav):
                        try:
                            nav.avaliar(ligar)
                            time.sleep(0.5)
                            medidas = json.loads(nav.avaliar(CHECAGENS))
                            violacoes = []
                            if not argumentos.rapido or nome_tamanho == "notebook" or nome_tamanho == "celular":
                                violacoes = json.loads(nav.avaliar(AXE_EXEC))
                            medidas.update({"tamanho": nome_tamanho, "tema": tema, "tela": nome, "axe": violacoes})
                            resultado["telas"].append(medidas)
                            if fotografar:
                                nav.foto(os.path.join(argumentos.fotos, "%s_%s_%s.png" % (nome_tamanho, tema, nome.replace(":", "_"))))
                        except OSError as falha:
                            resultado["telas"].append({"tamanho": nome_tamanho, "tema": tema, "tela": nome, "erro": str(falha)[:200]})
                        finally:
                            try:
                                nav.avaliar(desligar)
                            except OSError:
                                pass
                    print("  %-12s %-6s %d telas" % (nome_tamanho, tema, len([t for t in resultado["telas"] if t.get("tamanho") == nome_tamanho and t.get("tema") == tema])), flush=True)
    finally:
        if servidor and servidor.poll() is None:
            servidor.kill()
            servidor.wait()
        c.derrubar(copia)
        time.sleep(1)
        limpeza.apagar_pasta(trabalho)

    # O resumo: cada problema uma vez, com onde apareceu.
    unico = {}
    for tela in resultado["telas"]:
        for v in tela.get("axe", []):
            item = unico.setdefault("axe:" + v["id"], {"o_que": v["ajuda"], "impacto": v["impacto"], "onde": set(), "amostra": v["amostra"][:2]})
            item["onde"].add("%s/%s/%s" % (tela["tamanho"], tela["tema"], tela["tela"]))
        for chave in ("sem_nome_acessivel", "alvo_menor_que_24px", "texto_menor_que_12px"):
            if tela.get(chave, {}).get("total"):
                item = unico.setdefault(chave, {"o_que": chave, "impacto": "medio", "onde": set(), "amostra": tela[chave]["amostra"][:4]})
                item["onde"].add("%s/%s/%s" % (tela["tamanho"], tela["tema"], tela["tela"]))
        if tela.get("estouro_horizontal_px", 0) > 1:
            item = unico.setdefault("estouro_horizontal", {"o_que": "a pagina passa da largura da tela", "impacto": "serio", "onde": set(), "amostra": []})
            item["onde"].add("%s/%s/%s (+%dpx)" % (tela["tamanho"], tela["tema"], tela["tela"], tela["estouro_horizontal_px"]))
        if tela.get("contraste", {}).get("falhas"):
            item = unico.setdefault("contraste_calculado", {"o_que": "texto abaixo de 4,5:1 (3:1 se grande)", "impacto": "serio", "onde": set(), "amostra": []})
            item["onde"].add("%s/%s/%s (%d)" % (tela["tamanho"], tela["tema"], tela["tela"], tela["contraste"]["falhas"]))
            for pior in tela["contraste"]["piores"][:2]:
                if len(item["amostra"]) < 8 and pior not in item["amostra"]:
                    item["amostra"].append(pior)
        if tela.get("id_repetido"):
            item = unico.setdefault("id_repetido", {"o_que": "id repetido", "impacto": "serio", "onde": set(), "amostra": tela["id_repetido"][:4]})
            item["onde"].add("%s/%s/%s" % (tela["tamanho"], tela["tema"], tela["tela"]))
    resultado["resumo"] = {k: dict(v, onde=sorted(v["onde"])) for k, v in sorted(unico.items())}
    os.makedirs(os.path.dirname(argumentos.saida), exist_ok=True)
    with open(argumentos.saida, "w", encoding="utf-8") as arquivo:
        json.dump(resultado, arquivo, ensure_ascii=False, indent=1)
    print("\n%d telas medidas, %d problemas distintos -> %s (fotos em %s)" % (len(resultado["telas"]), len(unico), argumentos.saida, argumentos.fotos))
    for chave, item in resultado["resumo"].items():
        print("  %-34s %-9s %3d lugares  %s" % (chave, item["impacto"], len(item["onde"]), item["o_que"][:70]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
