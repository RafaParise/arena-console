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
        [--escala 8] [--sem-texto] [--saida docs\imagens\arena-escuro.gif]
  --passo e' quanto o fundo anda por quadro, em 1/60 s (6 = 10 quadros por
  segundo em tempo real, com --atraso 10 centesimos).
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
CORTE_TOPO = 5           # 160 x 90 -> 160 x 80 (2:1): tira 5 linhas em cima e 5 embaixo
ALTURA_GIF = 80

PAGINA = """<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<style>
  html, body { margin: 0; width: %(largura)dpx; height: %(altura)dpx; overflow: hidden; background: transparent; }
  canvas { display: none; }
  .marca { position: fixed; inset: 0; display: flex; flex-direction: column; align-items: center;
           justify-content: center; gap: %(gap)dpx; text-align: center; }
  .nome { font-family: "Courier New", monospace; font-weight: 700; font-size: %(nome)dpx; letter-spacing: 0.08em;
          color: #ffe08a; line-height: 1; text-shadow: %(sombra)dpx %(sombra)dpx 0 #7c4d9e; }
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


def principal():
    tema = argumento("--tema", "escuro")
    escala = int(argumento("--escala", "8"))
    quadros = int(argumento("--quadros", "60"))
    passo = float(argumento("--passo", "6"))
    atraso = int(argumento("--atraso", "10"))
    visitas = [v for v in argumento("--visitas", "").split(",") if v]
    com_texto = "--sem-texto" not in sys.argv
    saida = os.path.abspath(argumento("--saida", os.path.join(RAIZ, "docs", "imagens", "arena-%s.gif" % tema)))
    largura, altura = W * escala, ALTURA_GIF * escala
    gancho = "__fundoEscuro" if tema == "escuro" else "__fundoClaro"
    fundo = "galaxy-background.js" if tema == "escuro" else "field-background.js"
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
        k = escala / 8.0          # o titulo foi medido para 1280 x 640
        escuro = tema == "escuro"
        html = PAGINA % {"largura": largura, "altura": altura, "tema": tema, "fundo": fundo,
                         "gap": int(14 * k), "nome": int(170 * k), "sombra": max(2, int(8 * k)),
                         "sub": int(40 * k), "contorno": max(2, int(6 * k)),
                         "cor_sub": "#f1ecff" if escuro else "#ffffff",
                         "cor_contorno": "rgba(0,0,0,.9)" if escuro else "rgba(40,70,20,.95)"}
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
            nav.avaliar("window.%s.avancar(40, 3)" % gancho)     # a cena assenta
            fila = list(visitas)
            imagens = []
            for n in range(quadros):
                if fila and not nav.avaliar("window.%s.rodando()" % gancho):
                    nav.avaliar("window.%s.chamar('%s')" % (gancho, fila.pop(0)))
                nav.avaliar("window.%s.avancar(1, %s)" % (gancho, passo))
                px = base64.b64decode(nav.avaliar("window.%s.pixels()" % gancho))
                linhas = []
                for y in range(CORTE_TOPO, CORTE_TOPO + ALTURA_GIF):
                    linha = []
                    for x in range(W):
                        i = (y * W + x) * 4
                        linha += [(px[i], px[i + 1], px[i + 2])] * escala
                    linhas += [linha] * escala
                quadro = [c for linha in linhas for c in linha]
                for i, (r, g, b, a) in titulo:
                    if a >= 255:
                        quadro[i] = (r, g, b)
                    else:
                        fr, fg, fb = quadro[i]
                        quadro[i] = ((r * a + fr * (255 - a)) // 255, (g * a + fg * (255 - a)) // 255,
                                     (b * a + fb * (255 - a)) // 255)
                imagens.append(quadro)
                if (n + 1) % 10 == 0:
                    print("  %d de %d quadros" % (n + 1, quadros), flush=True)
        os.makedirs(os.path.dirname(saida), exist_ok=True)
        tamanho = gif_animado.salvar(saida, largura, altura, imagens, atraso_cs=atraso)
        print("GIF: %s (%dx%d, %d quadros, %.0f KB)" % (saida, largura, altura, len(imagens), tamanho / 1024))
        return 0
    finally:
        limpeza.apagar_pasta(pasta)


if __name__ == "__main__":
    sys.exit(principal())
