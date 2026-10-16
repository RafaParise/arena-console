# -*- coding: utf-8 -*-
r"""Grava os fundos animados do ARENA (o ceu do modo escuro e o campo do modo
claro) como GIF animado, para a "Social preview" do GitHub (a imagem que
aparece quando alguem compartilha o link) e para o topo do README.

Pedido do Rafael (12/10/2026): "transforme os fundos em gif para eu poder usar
no social preview do meu github [...] e onde mais puder". A pagina do GitHub
pede: PNG, GIF ou JPG, pelo menos 640 x 320 (1280 x 640 e' o melhor), ate
1 MB, e deixar 40 pontos de borda livres em volta do que importa (o modelo
oficial, "repository-open-graph-template.png").

Como funciona, sem instalar nada (so a biblioteca padrao do Python):
  1. Monta uma pagina avulsa (numa pasta temporaria) com o fundo de verdade
     (launcher\pixel-sprites.js + o fundo do tema) e o nome ARENA no estilo do
     topo da tela -- igual a ferramentas\imagem_do_github.py.
  2. Abre no Edge sem janela (testes\tela_sem_janela.py) e liga o modo
     "gravando" do fundo (o laco normal para; a ferramenta avanca quadro a
     quadro pelo gancho avancar(), entao o tempo fica certinho).
  3. Le os 160 x 90 pontos de cada quadro (gancho pixels()), corta para 2:1
     (160 x 80), amplia e cola por cima o titulo, desenhado UMA vez pelo
     navegador com fundo transparente.
  4. Grava o GIF com ferramentas\gif_animado.py (so o que muda de um quadro
     para o outro; uma paleta para o GIF inteiro).

Uso:
    servidor\python\python.exe ferramentas\gravar_fundo_gif.py [--tema escuro|claro]
        [--visitas fzero,kirby] [--quadros 60] [--passo 6] [--atraso 10]
        [--escala 8] [--adiantar 0] [--girar 0] [--semente 7] [--sem-texto]
        [--disparar ovni,cometa] [--ate-o-fim] [--tolerancia 0] [--amostras folha.png]
        [--saida docs\imagens\arena-escuro.gif]
  --passo e' quanto o fundo anda por quadro, em 1/60 s (6 = 10 quadros por
  segundo em tempo real, com --atraso 10 centesimos).
  --visitas kart,todas: a Rainbow Road e depois todas as outras visitas, uma
  atras da outra; com --ate-o-fim, a gravacao para quando a ultima acaba
  (--quadros vira o maximo).
  --disparar: os de passagem do ceu (cometa, meteoros, ovni, satelite,
  foguete), um no comeco de cada visita, da segunda em diante; sozinhos, eles
  demoram (o foguete aparece a cada 1 ou 2 minutos).
  No ceu com o titulo, os personagens passam NA FRENTE dele (o fundo e' lido
  em duas camadas: o ceu, ate o planeta, e o resto).
  --tolerancia N: o ponto que mudou menos que N (distancia de cor) fica como
  esta (ferramentas\gif_animado.py): a aurora e as nebulosas pulsam devagar
  e, sem isso, seriam regravadas a cada quadro.
  --amostras: uma folha PNG com o quadro do meio de cada visita, para revisar.
  --girar K: o GIF comeca no quadro K da gravacao, e os quadros antes dele
  vao para o fim. Gravando uma visita inteira (do ceu vazio ao ceu vazio),
  o primeiro quadro ja mostra o personagem e a emenda do laco cai na parte
  vazia, onde quase nao se nota.
"""
import base64
import os
import shutil
import struct
import sys
import tempfile
import zlib

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "testes"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gif_animado  # noqa: E402
import limpeza  # noqa: E402
import tela_sem_janela  # noqa: E402

W, H = 160, 90
# 160 x 90 -> 160 x 80 (2:1): quantas linhas saem em cima (o resto sai embaixo).
# No campo, quem anda na grama pisa na linha 85: ali o corte e' maior em cima
# (so a ponta dos raios do sol) para os pes nao sumirem.
CORTE_TOPO = {"escuro": 5, "claro": 7}
ALTURA_GIF = 80

PAGINA = """<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<script>
  // Sorteio com semente (mulberry32): a mesma gravacao sai sempre igual.
  (function () {
    let s = %(semente)d >>> 0;
    Math.random = function () {
      s = (s + 0x6D2B79F5) >>> 0;
      let t = s;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  })();
</script>
<style>
  html, body { margin: 0; width: %(largura)dpx; height: %(altura)dpx; overflow: hidden; background: transparent; }
  canvas { display: none; }
  .marca { position: fixed; inset: 0; display: flex; flex-direction: column; align-items: center;
           justify-content: center; gap: %(gap)dpx; text-align: center; }
  .nome { font-family: "Courier New", monospace; font-weight: 700; font-size: %(nome)dpx; letter-spacing: 0.08em;
          color: #ffe08a; line-height: 1; text-shadow: %(sombra)dpx %(sombra)dpx 0 #7c4d9e;%(contorno_nome)s }
  .sub { font-family: "Segoe UI", system-ui, sans-serif; font-size: %(sub)dpx; font-weight: 600; color: %(cor_sub)s;
         text-shadow: 0 0 %(contorno)dpx %(cor_contorno)s, 0 0 %(contorno)dpx %(cor_contorno)s; }
</style></head>
<body data-tema="%(tema)s" data-fundo-animado="sempre">
<canvas id="galaxyCanvas"></canvas>
<canvas id="fieldCanvas"></canvas>
<div class="marca" id="marca">
  <div class="nome">ARENA</div>
  <div class="sub">central retr&ocirc; da turma</div>
</div>
<script src="pixel-sprites.js"></script>
<script src="%(fundo)s"></script>
</body></html>
"""


def ler_png(dados):
    """PNG de 8 bits (RGB ou RGBA, sem entrelacamento) -> (largura, altura,
    lista de (r, g, b, a)). So o que o Edge entrega na foto da tela."""
    assert dados[:8] == b"\x89PNG\r\n\x1a\n", "nao e' PNG"
    p, idat, largura = 8, bytearray(), None
    while p < len(dados):
        n, tipo = struct.unpack(">I4s", dados[p:p + 8])
        corpo = dados[p + 8:p + 8 + n]
        if tipo == b"IHDR":
            largura, altura, bits, cor, _, _, entrelacado = struct.unpack(">IIBBBBB", corpo)
            assert bits == 8 and cor in (2, 6) and not entrelacado, "PNG diferente do esperado"
            canais = 4 if cor == 6 else 3
        elif tipo == b"IDAT":
            idat += corpo
        p += 12 + n
    cru = zlib.decompress(bytes(idat))
    linha = largura * canais
    anterior = bytearray(linha)
    saida = []
    for y in range(altura):
        filtro = cru[y * (linha + 1)]
        atual = bytearray(cru[y * (linha + 1) + 1:(y + 1) * (linha + 1)])
        if filtro == 1:
            for i in range(canais, linha):
                atual[i] = (atual[i] + atual[i - canais]) & 255
        elif filtro == 2:
            for i in range(linha):
                atual[i] = (atual[i] + anterior[i]) & 255
        elif filtro == 3:
            for i in range(linha):
                a = atual[i - canais] if i >= canais else 0
                atual[i] = (atual[i] + ((a + anterior[i]) >> 1)) & 255
        elif filtro == 4:
            for i in range(linha):
                a = atual[i - canais] if i >= canais else 0
                b = anterior[i]
                c = anterior[i - canais] if i >= canais else 0
                pp = a + b - c
                pa, pb, pc = abs(pp - a), abs(pp - b), abs(pp - c)
                atual[i] = (atual[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        for x in range(largura):
            base = x * canais
            saida.append((atual[base], atual[base + 1], atual[base + 2], atual[base + 3] if canais == 4 else 255))
        anterior = atual
    return largura, altura, saida


def argumento(nome, padrao):
    if nome in sys.argv:
        return sys.argv[sys.argv.index(nome) + 1]
    return padrao


def ler_pixels(nav, expressao, corte):
    """Os 160 x 90 pontos RGBA que a expressao devolve em base64, so as linhas
    que entram no GIF (o corte de 2:1, a partir da linha 'corte')."""
    px = base64.b64decode(nav.avaliar(expressao))
    return px[corte * W * 4:(corte + ALTURA_GIF) * W * 4]


def montar_quadro(tudo, ceu, titulo, escala, largura):
    """O quadro grande (lista de cores) de um quadro pequeno: amplia o ceu,
    cola o titulo por cima e, com as camadas, os personagens por cima de tudo
    (cada ponto de 'tudo' diferente do 'ceu' e' de um personagem)."""
    base = ceu if ceu is not None else tudo
    linhas = []
    for y in range(ALTURA_GIF):
        linha = []
        for x in range(W):
            i = (y * W + x) * 4
            linha += [(base[i], base[i + 1], base[i + 2])] * escala
        linhas += [linha] * escala
    quadro = [c for linha in linhas for c in linha]
    for i, (r, g, b, a) in titulo:
        if a >= 255:
            quadro[i] = (r, g, b)
        else:
            fr, fg, fb = quadro[i]
            quadro[i] = ((r * a + fr * (255 - a)) // 255, (g * a + fg * (255 - a)) // 255,
                         (b * a + fb * (255 - a)) // 255)
    if ceu is not None and titulo:
        for p in range(0, len(tudo), 4):
            if tudo[p:p + 3] != ceu[p:p + 3]:
                y, x = divmod(p // 4, W)
                cor = (tudo[p], tudo[p + 1], tudo[p + 2])
                for dy in range(escala):
                    inicio = (y * escala + dy) * largura + x * escala
                    quadro[inicio:inicio + escala] = [cor] * escala
    return quadro


def salvar_amostras(caminho, pequenos, comecos, titulo, escala, largura, altura):
    """Uma folha PNG para revisar o GIF sem abri-lo: o quadro do meio de cada
    visita, pela metade do tamanho, 4 por linha (antes do --girar)."""
    from revisar_visitas import salvar_png
    inicios = [n for n, nome in comecos if not nome.startswith("+")] + [len(pequenos)]
    meios = [(a + b) // 2 for a, b in zip(inicios, inicios[1:])]
    colunas, lw, lh = 4, largura // 2, altura // 2
    linhas = (len(meios) + colunas - 1) // colunas
    folha = [(0, 0, 0)] * (colunas * lw * linhas * lh)
    for k, n in enumerate(meios):
        tudo, ceu = pequenos[n]
        quadro = montar_quadro(tudo, ceu, titulo, escala, largura)
        ox, oy = (k % colunas) * lw, (k // colunas) * lh
        for y in range(lh):
            inicio = (oy + y) * colunas * lw + ox
            folha[inicio:inicio + lw] = quadro[2 * y * largura:2 * y * largura + largura:2]
    salvar_png(caminho, colunas * lw, linhas * lh, folha)
    print("amostras: %s (%d visitas)" % (caminho, len(meios)))


def principal():
    tema = argumento("--tema", "escuro")
    escala = int(argumento("--escala", "8"))
    quadros = int(argumento("--quadros", "60"))
    passo = float(argumento("--passo", "6"))
    atraso = int(argumento("--atraso", "10"))
    visitas = [v for v in argumento("--visitas", "").split(",") if v]
    # Os de passagem que o GIF chama (um no comeco de cada visita, da segunda
    # em diante): no ceu, cometa, meteoros, ovni, satelite e foguete.
    disparos = [d for d in argumento("--disparar", "").split(",") if d]
    # Quadros que a primeira visita anda antes de comecar a gravar: o primeiro
    # quadro do GIF ja mostra o personagem (e o que aparece quando alguem
    # compartilha o link: a maioria dos sites nao anima a imagem).
    adiantar = int(argumento("--adiantar", "0"))
    girar = int(argumento("--girar", "0"))
    semente = int(argumento("--semente", "7"))
    com_texto = "--sem-texto" not in sys.argv
    ate_o_fim = "--ate-o-fim" in sys.argv
    tolerancia = int(argumento("--tolerancia", "0"))
    amostras = argumento("--amostras", "")
    saida = os.path.abspath(argumento("--saida", os.path.join(RAIZ, "docs", "imagens", "arena-%s.gif" % tema)))
    largura, altura = W * escala, ALTURA_GIF * escala
    gancho = "__fundoEscuro" if tema == "escuro" else "__fundoClaro"
    fundo = "galaxy-background.js" if tema == "escuro" else "field-background.js"
    # Personagens na frente do titulo (pedido do Rafael, 14/10/2026: o GIF
    # mostrar todos, sem deixar nenhum para tras). No ceu, quase todas as
    # visitas cruzam a faixa do meio, a do titulo.
    # No campo tambem (16/10/2026): os de longe passam no pe do morro, bem
    # atras do titulo, e no GIF sumiam atras das letras.
    camadas = com_texto
    pasta = tempfile.mkdtemp(prefix="arena_gif_")
    try:
        for js in ("pixel-sprites.js", fundo):
            shutil.copy2(os.path.join(RAIZ, "launcher", js), os.path.join(pasta, js))
        if tema == "escuro" and com_texto:
            # Os Metroides e o planeta passavam por tras das letras: o mesmo
            # ajuste da capa (ferramentas\imagem_do_github.py) leva os dois
            # para as laterais, so na copia usada aqui.
            import imagem_do_github
            imagem_do_github.preparar_fundo_da_capa(pasta)
            fundo = "galaxy-background-capa.js"
            # A capa leva o planeta para baixo, onde no GIF passam as pistas do
            # F-Zero e da Rainbow Road: aqui ele vai para o alto, a direita do
            # titulo, embaixo da constelacao.
            capa = os.path.join(pasta, fundo)
            with open(capa, encoding="utf-8") as f:
                texto = f.read()
            trocas = [("const planeta = { x: W * 0.875, y: 76 };", "const planeta = { x: 132, y: 26 };"),
                      # As camadas: o ceu (ate o planeta) fica guardado a cada
                      # quadro; o que vem depois (os de passagem, as visitas,
                      # os Metroides e o foguete) vai na frente do titulo.
                      ("    desenharPlaneta(passo);\n",
                       "    desenharPlaneta(passo);\n"
                       "    if (window.__camadas) window.__camadas.ceu = ctx.getImageData(0, 0, W, H).data.slice();\n")]
            for velho, novo in trocas:
                if texto.count(velho) != 1:
                    raise SystemExit("O fundo mudou (%r): atualize esta ferramenta." % velho[:40])
                texto = texto.replace(velho, novo)
            with open(capa, "w", encoding="utf-8") as f:
                f.write(texto)
        if tema == "claro" and com_texto:
            # As camadas no campo: o cenario (ate os girassois e o coelho) fica
            # guardado a cada quadro; as visitas e o que vem depois (abelhas,
            # borboletas, sementes) vao na frente do titulo -- so na copia.
            copia = os.path.join(pasta, "field-background-gif.js")
            with open(os.path.join(pasta, fundo), encoding="utf-8") as f:
                texto = f.read()
            velho = "    desenharVisitas(passo);\n"
            if texto.count(velho) != 1:
                raise SystemExit("O fundo mudou (%r): atualize esta ferramenta." % velho.strip())
            texto = texto.replace(velho, "    if (window.__camadas) window.__camadas.ceu = "
                                         "ctx.getImageData(0, 0, W, H).data.slice();\n" + velho)
            with open(copia, "w", encoding="utf-8") as f:
                f.write(texto)
            fundo = "field-background-gif.js"
        k = escala / 8.0          # o titulo foi medido para 1280 x 640
        escuro = tema == "escuro"
        html = PAGINA % {"largura": largura, "altura": altura, "tema": tema, "fundo": fundo, "semente": semente,
                         "gap": int(14 * k), "nome": int(170 * k), "sombra": max(2, int(8 * k)),
                         "sub": int(40 * k), "contorno": max(2, int(6 * k)),
                         "cor_sub": "#f1ecff" if escuro else "#ffffff",
                         "cor_contorno": "rgba(0,0,0,.9)" if escuro else "rgba(40,70,20,.95)",
                         # No ceu claro o amarelo do titulo fica fraco: ganha contorno.
                         "contorno_nome": "" if escuro else (
                             " -webkit-text-stroke: %dpx #4b2c6f; paint-order: stroke fill;" % max(3, int(9 * k)))}
        caminho = os.path.join(pasta, "pagina.html")
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(html)
        with tela_sem_janela.Navegador() as nav:
            nav.abrir("file:///" + caminho.replace("\\", "/"), largura=largura, altura=altura, espera=1.5)
            # O fundo desenha no canvas escondido (os pontos saem pelo gancho
            # pixels()); na foto do titulo so pode aparecer o titulo.
            nav.avaliar("for (const c of document.querySelectorAll('canvas')) c.style.visibility = 'hidden'")
            titulo = []
            if com_texto:
                # O titulo, uma vez, com o fundo transparente.
                nav.comando("Emulation.setDefaultBackgroundColorOverride", color={"r": 0, "g": 0, "b": 0, "a": 0})
                foto = os.path.join(pasta, "titulo.png")
                nav.foto(foto)
                lw, lh, pontos = ler_png(open(foto, "rb").read())
                titulo = [(i, p) for i, p in enumerate(pontos) if p[3] > 0]
                print("titulo: %d pontos (%dx%d)" % (len(titulo), lw, lh))
            nav.avaliar("document.getElementById('marca').style.display = 'none'; window.%s.gravar()" % gancho)
            if camadas:
                nav.avaliar("window.__camadas = {}")
            if "todas" in visitas:
                # "kart,todas": a Rainbow Road primeiro, depois as outras, na
                # ordem do fundo.
                todas = nav.avaliar("window.%s.visitas" % gancho)
                i = visitas.index("todas")
                visitas = visitas[:i] + [v for v in todas if v not in visitas] + visitas[i + 1:]
            nav.avaliar("window.%s.avancar(40, 3)" % gancho)     # a cena assenta
            fila = list(visitas)
            comecos = []                 # (quadro, nome): o que entrou em cada quadro
            if fila and adiantar:
                comecos.append((0, fila[0]))
                nav.avaliar("window.%s.chamar('%s')" % (gancho, fila.pop(0)))
                nav.avaliar("window.%s.avancar(%d, %s)" % (gancho, adiantar, passo))
            ceu_js = ("(function () { const d = window.__camadas.ceu; let s = ''; for (let i = 0; i < d.length; "
                      "i += 8192) s += String.fromCharCode.apply(null, d.subarray(i, i + 8192)); return btoa(s); })()")
            # Os quadros pequenos (160 x 80, RGBA): os grandes saem deles na
            # hora de gravar, um de cada vez (centenas de quadros de 1280 x 640
            # nao cabem na memoria).
            pequenos = []
            for n in range(quadros):
                rodando = nav.avaliar("window.%s.rodando()" % gancho)
                if fila and not rodando:
                    nome = fila.pop(0)
                    nav.avaliar("window.%s.chamar('%s')" % (gancho, nome))
                    comecos.append((n, nome))
                    if disparos and len([c for c in comecos if not c[1].startswith("+")]) >= 2:
                        extra = disparos.pop(0)
                        nav.avaliar("window.%s.disparar && window.%s.disparar('%s')" % (gancho, gancho, extra))
                        comecos.append((n, "+" + extra))
                elif ate_o_fim and not fila and not rodando and n:
                    break
                nav.avaliar("window.%s.avancar(1, %s)" % (gancho, passo))
                tudo = ler_pixels(nav, "window.%s.pixels()" % gancho, CORTE_TOPO[tema])
                pequenos.append((tudo, ler_pixels(nav, ceu_js, CORTE_TOPO[tema]) if camadas else None))
                if (n + 1) % 50 == 0:
                    print("  %d quadros" % (n + 1), flush=True)
        print("entraram: " + ", ".join("%s (%d)" % (nome, n) for n, nome in comecos))
        if fila or disparos:
            print("AVISO: nao couberam em %d quadros: %s" % (quadros, ", ".join(fila + disparos)))
        os.makedirs(os.path.dirname(saida), exist_ok=True)
        if amostras:
            salvar_amostras(amostras, pequenos, comecos, titulo, escala, largura, altura)
        if girar:
            girar %= len(pequenos)
            pequenos = pequenos[girar:] + pequenos[:girar]

        def grandes():
            for tudo, ceu in pequenos:
                yield montar_quadro(tudo, ceu, titulo, escala, largura)

        # Duas passadas: a primeira conta as cores (a paleta e' uma so para o
        # GIF inteiro), a segunda grava.
        paleta = gif_animado.paleta_da_contagem(gif_animado.contar_cores(grandes()))
        tamanho = gif_animado.salvar(saida, largura, altura, grandes(), atraso_cs=atraso, paleta=paleta,
                                     tolerancia=tolerancia)
        print("GIF: %s (%dx%d, %d quadros, %.0f KB)" % (saida, largura, altura, len(pequenos), tamanho / 1024))
        return 0
    finally:
        limpeza.apagar_pasta(pasta)


if __name__ == "__main__":
    sys.exit(principal())
