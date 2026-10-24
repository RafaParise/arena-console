# -*- coding: utf-8 -*-
r"""Gera o icone oficial do ARENA, o SUPERCONTROLE, em todas as versoes.

Pedido do Rafael (23/10/2026): "o icone do arena deve ser um controle que e
uma juncao de todos os controles [...] um controle daquele Xbox Duke com 3
pernas para ter aquele analogico do Nintendo 64, com analogicos direcionais
apenas como o do PS2, ou seja, dois direcionais esquerdos como cada um fica
no controle e apenas um direito. O padrao de quatro botoes de ambos os
controles continua, mas adicione aqueles botoes especiais do Nintendo 64 e
GameCube alem daqueles do proprio controle Duke do Xbox [...] como icone
oficial do ARENA em todas as suas versoes".

O desenho (tudo sai do mesmo codigo, em SVG):
  - o corpo de TRES PONTAS do Nintendo 64, com a massa do Xbox Duke;
  - dois analogicos a esquerda (o do PS2/Xbox e o do meio, do Nintendo 64) e
    UM so a direita (amarelo, como o C-stick do GameCube), mais o direcional;
  - os quatro botoes de sempre, nas cores do Xbox (A verde, B vermelho, X azul,
    Y ambar), o A maior como o do GameCube;
  - os botoes especiais: os 4 C amarelos e o Start vermelho do Nintendo 64, o
    Z roxo do GameCube e o preto e o branco do Duke;
  - a joia do meio e' a do ARENA (rosa, com um A).
Ha duas versoes do desenho: a COMPLETA (64 pixels para cima) e a SIMPLES (de 16
a 48, onde os detalhes viram mancha: silhueta, quatro botoes grandes e os
analogicos como circulos).

Saidas (nada disto e' lido pelo ARENA em tempo de uso; so o resultado vai no pacote):
  docs/imagens/icone/   os SVG (fonte) e os PNG de apresentacao
  launcher/             o icone da tela do ARENA (SVG, PNG e o .ico do Windows)
  ferramentas/site/     os icones do site/Chromebook (PWA, "any maskable")
  docs/imagens/icone/android/mipmap-*   os icones do APK (montar_android.py os copia)

Precisa so do Python e de um navegador Chrome ou Edge (para desenhar o SVG;
o Edge ja vem no Windows). Uso:  servidor\python\python.exe ferramentas\gerar_icone.py
"""
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import zlib

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESTINO = os.path.join(RAIZ, "docs", "imagens", "icone")

# A silhueta de tres pontas (em um quadro de 400 x 400).
SILHUETA = ("M40,140 C40,98 72,66 118,66 L282,66 C328,66 360,98 360,140 C360,200 372,262 366,312 "
            "C360,352 334,372 304,372 C278,372 262,352 262,322 L262,282 C262,262 250,252 236,252 "
            "L236,330 C236,348 222,358 200,358 C178,358 164,348 164,330 L164,252 C150,252 138,262 138,282 "
            "L138,322 C138,352 122,372 96,372 C66,372 40,352 34,312 C28,262 40,200 40,140 Z")

DEGRADES = """
    <linearGradient id="fundo" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#241f4a"/><stop offset="1" stop-color="#0d0c17"/></linearGradient>
    <radialGradient id="brilho" cx="50%" cy="46%" r="52%"><stop offset="0" stop-color="#ff6f9c" stop-opacity=".42"/><stop offset="0.6" stop-color="#5a46ff" stop-opacity=".16"/><stop offset="1" stop-color="#5a46ff" stop-opacity="0"/></radialGradient>
    <linearGradient id="corpo" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fbf9ff"/><stop offset="0.55" stop-color="#d8d3ee"/><stop offset="1" stop-color="#a59fc9"/></linearGradient>
    <linearGradient id="gripe" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#2a2552" stop-opacity=".38"/></linearGradient>
    <radialGradient id="capa" cx="38%" cy="30%" r="75%"><stop offset="0" stop-color="#6a6597"/><stop offset="1" stop-color="#25213f"/></radialGradient>
    <radialGradient id="capa-clara" cx="38%" cy="30%" r="75%"><stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#a9a6c4"/></radialGradient>
    <radialGradient id="capa-amarela" cx="38%" cy="30%" r="75%"><stop offset="0" stop-color="#fff0a0"/><stop offset="1" stop-color="#f0a500"/></radialGradient>
    <radialGradient id="verde" cx="38%" cy="30%" r="80%"><stop offset="0" stop-color="#8dffbf"/><stop offset="1" stop-color="#14b45a"/></radialGradient>
    <radialGradient id="vermelho" cx="38%" cy="30%" r="80%"><stop offset="0" stop-color="#ffa3b5"/><stop offset="1" stop-color="#e0214a"/></radialGradient>
    <radialGradient id="azul" cx="38%" cy="30%" r="80%"><stop offset="0" stop-color="#a6c0ff"/><stop offset="1" stop-color="#2f56e8"/></radialGradient>
    <radialGradient id="ambar" cx="38%" cy="30%" r="80%"><stop offset="0" stop-color="#ffe7a1"/><stop offset="1" stop-color="#f09a00"/></radialGradient>
    <radialGradient id="joia" cx="40%" cy="30%" r="80%"><stop offset="0" stop-color="#ffd0df"/><stop offset="0.5" stop-color="#ff6f9c"/><stop offset="1" stop-color="#c2185b"/></radialGradient>
    <filter id="sombra" x="-20%" y="-20%" width="140%" height="150%"><feDropShadow dx="0" dy="10" stdDeviation="9" flood-color="#000" flood-opacity=".55"/></filter>
"""


def controle_completo():
    """O supercontrole com todos os detalhes (quadro de 400 x 400)."""
    return """
    <g filter="url(#sombra)">
      <rect id="gatilho-esquerdo" x="62" y="44" width="92" height="34" rx="16" fill="#4a4575" stroke="#1d1a33" stroke-width="7"/>
      <rect id="gatilho-direito" x="246" y="44" width="92" height="34" rx="16" fill="#4a4575" stroke="#1d1a33" stroke-width="7"/>
      <rect id="z-gamecube" x="168" y="38" width="64" height="30" rx="14" fill="#8a63ff" stroke="#1d1a33" stroke-width="7"/>
      <path id="corpo-de-tres-pontas" d="%(s)s" fill="url(#corpo)" stroke="#1d1a33" stroke-width="9" stroke-linejoin="round"/>
    </g>
    <path d="%(s)s" fill="url(#corpo)"/>
    <path d="%(s)s" fill="url(#gripe)"/>
    <path d="M70,110 C86,84 108,78 130,78 L270,78 C292,78 314,84 330,110 C300,96 270,92 200,92 C130,92 100,96 70,110 Z" fill="#fff" opacity=".7"/>
    <g id="direcional" transform="translate(92,136)">
      <rect x="-33" y="-12" width="66" height="24" rx="7" fill="#2b2748" stroke="#14122a" stroke-width="4"/>
      <rect x="-12" y="-33" width="24" height="66" rx="7" fill="#2b2748" stroke="#14122a" stroke-width="4"/>
      <rect x="-30" y="-9" width="60" height="18" rx="5" fill="#3d3866"/>
      <rect x="-9" y="-30" width="18" height="60" rx="5" fill="#3d3866"/>
      <circle r="6" fill="#241f3f"/>
    </g>
    <g id="analogico-esquerdo" transform="translate(112,222)">
      <circle r="31" fill="#1b1830" stroke="#0e0c1c" stroke-width="4"/>
      <circle r="23" fill="url(#capa)" stroke="#0e0c1c" stroke-width="3"/>
      <circle cx="-6" cy="-7" r="8" fill="#fff" opacity=".18"/>
    </g>
    <g id="analogico-do-meio" transform="translate(200,298)">
      <circle r="31" fill="#1b1830" stroke="#0e0c1c" stroke-width="4"/>
      <circle r="22" fill="url(#capa-clara)" stroke="#0e0c1c" stroke-width="3"/>
      <circle r="9" fill="none" stroke="#6f6a96" stroke-width="3"/>
    </g>
    <g id="joia-do-arena" transform="translate(200,146)">
      <circle r="35" fill="#1b1830" stroke="#0e0c1c" stroke-width="4"/>
      <circle r="28" fill="url(#joia)" stroke="#7d0e3a" stroke-width="3"/>
      <path d="M-13,12 L0,-14 L13,12 M-8,4 L8,4" fill="none" stroke="#fff" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
    </g>
    <circle id="start-do-n64" cx="200" cy="205" r="10" fill="#ff3b4e" stroke="#7a0d1e" stroke-width="3"/>
    <g id="botoes-xyab" stroke="#14122a" stroke-width="4">
      <circle cx="292" cy="102" r="16" fill="url(#ambar)"/>
      <circle cx="256" cy="138" r="16" fill="url(#azul)"/>
      <circle cx="330" cy="138" r="16" fill="url(#vermelho)"/>
      <circle cx="293" cy="176" r="22" fill="url(#verde)"/>
    </g>
    <rect id="botao-branco-do-duke" x="252" y="208" width="27" height="13" rx="6.5" fill="#f4f2ff" stroke="#14122a" stroke-width="3.5"/>
    <rect id="botao-preto-do-duke" x="284" y="208" width="27" height="13" rx="6.5" fill="#1d1a33" stroke="#0a0916" stroke-width="3.5"/>
    <g id="botoes-c-do-n64" fill="url(#ambar)" stroke="#14122a" stroke-width="3">
      <circle cx="334" cy="194" r="6"/><circle cx="334" cy="216" r="6"/><circle cx="323" cy="205" r="6"/><circle cx="345" cy="205" r="6"/>
    </g>
    <g id="analogico-direito" transform="translate(305,262)">
      <circle r="29" fill="#1b1830" stroke="#0e0c1c" stroke-width="4"/>
      <circle r="21" fill="url(#capa-amarela)" stroke="#0e0c1c" stroke-width="3"/>
      <circle cx="-5" cy="-6" r="7" fill="#fff" opacity=".35"/>
    </g>
""" % {"s": SILHUETA}


def controle_simples():
    """A versao para 16 a 48 pixels: silhueta forte, botoes grandes, sem o miudo."""
    return """
    <path d="%(s)s" fill="url(#corpo)" stroke="#1d1a33" stroke-width="16" stroke-linejoin="round"/>
    <path d="%(s)s" fill="url(#corpo)"/>
    <path d="%(s)s" fill="url(#gripe)"/>
    <g id="direcional" transform="translate(92,136)" fill="#2b2748" stroke="#14122a" stroke-width="5">
      <rect x="-37" y="-14" width="74" height="28" rx="8"/><rect x="-14" y="-37" width="28" height="74" rx="8"/>
    </g>
    <circle id="analogico-esquerdo" cx="112" cy="226" r="27" fill="#2b2748" stroke="#14122a" stroke-width="6"/>
    <circle cx="112" cy="226" r="12" fill="#6a6597"/>
    <circle id="analogico-do-meio" cx="200" cy="300" r="27" fill="#f1effa" stroke="#14122a" stroke-width="6"/>
    <circle cx="200" cy="300" r="10" fill="none" stroke="#6f6a96" stroke-width="5"/>
    <circle id="joia-do-arena" cx="200" cy="148" r="33" fill="url(#joia)" stroke="#7d0e3a" stroke-width="6"/>
    <g id="botoes-xyab" stroke="#14122a" stroke-width="5">
      <circle cx="296" cy="104" r="20" fill="url(#ambar)"/>
      <circle cx="257" cy="143" r="20" fill="url(#azul)"/>
      <circle cx="335" cy="143" r="20" fill="url(#vermelho)"/>
      <circle cx="296" cy="188" r="26" fill="url(#verde)"/>
    </g>
    <circle id="analogico-direito" cx="306" cy="270" r="26" fill="url(#capa-amarela)" stroke="#14122a" stroke-width="6"/>
""" % {"s": SILHUETA}


def tamanho_do_corpo(detalhado):
    """(x, y, largura, altura) do controle no quadro de 400 x 400, para centrar."""
    return (28, 38, 344, 334) if detalhado else (24, 58, 352, 324)


def svg(tipo, tamanho=512, escala=None, cantos="redondos"):
    """O SVG de um icone.

    tipo     "completo" ou "simples" (o desenho); "so-controle" (completo, sem fundo,
             para o primeiro plano do icone do Android e para apresentacao)
    escala   quanto do quadrinho de 512 o controle ocupa (largura do controle / 512)
    cantos   "redondos" (o quadradinho do icone) ou "quadrados" (a tela inteira: o PWA e
             o Android recortam o formato por conta propria)"""
    detalhado = tipo != "simples"
    desenho = controle_completo() if detalhado else controle_simples()
    x, y, largura, altura = tamanho_do_corpo(detalhado)
    if escala is None:
        escala = 0.64 if detalhado else 0.80
    fator = escala * 512.0 / largura
    mover_x = 256 - fator * (x + largura / 2.0)
    mover_y = 256 - fator * (y + altura / 2.0) + 6
    controle = '<g transform="translate(%.2f,%.2f) scale(%.4f)">%s</g>' % (mover_x, mover_y, fator, desenho)
    fundo = ""
    if tipo != "so-controle":
        recorte = ' clip-path="url(#recorte)"' if cantos == "redondos" else ""
        estrelas = ""
        if detalhado:
            estrelas = ('<g fill="#ffffff" opacity=".55"><circle cx="62" cy="70" r="2.4"/><circle cx="448" cy="56" r="3"/>'
                        '<circle cx="470" cy="150" r="2"/><circle cx="40" cy="190" r="2"/><circle cx="455" cy="420" r="2.4"/>'
                        '<circle cx="70" cy="452" r="3"/><circle cx="400" cy="470" r="2"/><circle cx="120" cy="38" r="2"/></g>')
        fundo = ('<g%s><rect width="512" height="512" fill="url(#fundo)"/><rect width="512" height="512" fill="url(#brilho)"/>%s</g>'
                 % (recorte, estrelas))
    recorte_def = '<clipPath id="recorte"><rect width="512" height="512" rx="112"/></clipPath>'
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 512 512">'
            '<defs>%s%s</defs>%s%s</svg>\n' % (tamanho, tamanho, DEGRADES, recorte_def, fundo, controle))


# ---------------------------------------------------------------------------
# Desenhar o SVG (pelo Chrome ou Edge, sem janela) e mexer em PNG so com a biblioteca padrao
# ---------------------------------------------------------------------------

def achar_navegador():
    candidatos = [os.path.join(os.environ.get(v, ""), p) for v, p in (
        ("ProgramFiles(x86)", r"Microsoft\Edge\Application\msedge.exe"),
        ("ProgramFiles", r"Microsoft\Edge\Application\msedge.exe"),
        ("ProgramFiles", r"Google\Chrome\Application\chrome.exe"),
        ("ProgramFiles(x86)", r"Google\Chrome\Application\chrome.exe"),
        ("LOCALAPPDATA", r"Google\Chrome\Application\chrome.exe"))]
    for nome in ("google-chrome", "chromium", "chromium-browser", "microsoft-edge", "chrome"):
        achado = shutil.which(nome)
        if achado:
            candidatos.append(achado)
    return next((c for c in candidatos if c and os.path.isfile(c)), None)


def renderizar(navegador, caminho_svg, caminho_png, tamanho):
    """SVG -> PNG com fundo transparente. O navegador sem janela nao desenha janela
    pequena (minimo de uns 500 pixels): desenha-se grande e reduz-se depois."""
    perfil = tempfile.mkdtemp(prefix="arena-icone-")
    try:
        url = "file:///" + os.path.abspath(caminho_svg).replace("\\", "/")
        subprocess.run([navegador, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                        "--default-background-color=00000000", "--user-data-dir=" + perfil,
                        "--screenshot=" + caminho_png, "--window-size=%d,%d" % (tamanho, tamanho), url],
                       check=True, timeout=120, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # O Edge entrega o trabalho a um processo filho e o primeiro sai logo: espera o PNG
        # aparecer e parar de crescer.
        fim, ultimo = time.time() + 90, -1
        while time.time() < fim:
            tamanho_agora = os.path.getsize(caminho_png) if os.path.isfile(caminho_png) else 0
            if tamanho_agora and tamanho_agora == ultimo:
                break
            ultimo = tamanho_agora
            time.sleep(0.4)
    finally:
        shutil.rmtree(perfil, ignore_errors=True)   # pasta temporaria do navegador, nao e' dado de ninguem
    if not os.path.isfile(caminho_png):
        raise RuntimeError("o navegador nao gerou %s" % caminho_png)


def ler_png(caminho):
    """(largura, altura, bytes RGBA) de um PNG 8 bits (RGB ou RGBA, sem entrelacamento)."""
    with open(caminho, "rb") as arquivo:
        dados = arquivo.read()
    largura, altura, bits, cor = struct.unpack(">IIBB", dados[16:26])
    if bits != 8 or cor not in (2, 6) or dados[28] != 0:
        raise ValueError("PNG nao suportado: %s" % caminho)
    posicao, idat = 8, b""
    while posicao < len(dados):
        tamanho, tipo = struct.unpack(">I4s", dados[posicao:posicao + 8])
        if tipo == b"IDAT":
            idat += dados[posicao + 8:posicao + 8 + tamanho]
        posicao += 12 + tamanho
    cru = zlib.decompress(idat)
    por_pixel = 4 if cor == 6 else 3
    passo = largura * por_pixel
    anterior = bytearray(passo)
    saida = bytearray()
    for linha in range(altura):
        filtro = cru[linha * (passo + 1)]
        atual = bytearray(cru[linha * (passo + 1) + 1:(linha + 1) * (passo + 1)])
        for i in range(passo):
            a = atual[i - por_pixel] if i >= por_pixel else 0
            b = anterior[i]
            c = anterior[i - por_pixel] if i >= por_pixel else 0
            if filtro == 1:
                atual[i] = (atual[i] + a) & 255
            elif filtro == 2:
                atual[i] = (atual[i] + b) & 255
            elif filtro == 3:
                atual[i] = (atual[i] + ((a + b) >> 1)) & 255
            elif filtro == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                atual[i] = (atual[i] + (a if pa <= pb and pa <= pc else (b if pb <= pc else c))) & 255
        anterior = atual
        if por_pixel == 4:
            saida += atual
        else:
            for i in range(0, passo, 3):
                saida += atual[i:i + 3] + b"\xff"
    return largura, altura, bytes(saida)


def gravar_png(caminho, largura, altura, rgba):
    cru = bytearray()
    for y in range(altura):
        cru.append(0)
        cru += rgba[y * largura * 4:(y + 1) * largura * 4]

    def bloco(tipo, dados):
        return struct.pack(">I", len(dados)) + tipo + dados + struct.pack(">I", zlib.crc32(tipo + dados) & 0xFFFFFFFF)
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "wb") as arquivo:
        arquivo.write(b"\x89PNG\r\n\x1a\n" + bloco(b"IHDR", struct.pack(">IIBBBBB", largura, altura, 8, 6, 0, 0, 0))
                      + bloco(b"IDAT", zlib.compress(bytes(cru), 9)) + bloco(b"IEND", b""))


def reduzir(largura, altura, rgba, para):
    """Reduz por media de caixa, com a cor ponderada pelo alfa (sem borda escura)."""
    saida = bytearray(para * para * 4)
    for y in range(para):
        y0, y1 = y * altura // para, max((y + 1) * altura // para, y * altura // para + 1)
        for x in range(para):
            x0, x1 = x * largura // para, max((x + 1) * largura // para, x * largura // para + 1)
            r = g = b = a = n = 0
            for yy in range(y0, y1):
                base = (yy * largura + x0) * 4
                for xx in range(x1 - x0):
                    alfa = rgba[base + xx * 4 + 3]
                    r += rgba[base + xx * 4] * alfa
                    g += rgba[base + xx * 4 + 1] * alfa
                    b += rgba[base + xx * 4 + 2] * alfa
                    a += alfa
                    n += 1
            if a:
                saida[(y * para + x) * 4:(y * para + x) * 4 + 4] = bytes((r // a, g // a, b // a, a // n))
    return bytes(saida)


def png_do_svg(navegador, texto_svg, lado, trabalho, nome):
    """O PNG (RGBA) de um SVG, no lado pedido (desenha em 512 ou mais e reduz)."""
    grande = max(lado, 512)
    caminho_svg = os.path.join(trabalho, nome + ".svg")
    with open(caminho_svg, "w", encoding="utf-8") as arquivo:
        arquivo.write(texto_svg.replace('width="%d" height="%d"' % (lado, lado), 'width="%d" height="%d"' % (grande, grande), 1)
                      if lado != grande else texto_svg)
    caminho_png = os.path.join(trabalho, "%s-%d.png" % (nome, grande))
    renderizar(navegador, caminho_svg, caminho_png, grande)
    largura, altura, rgba = ler_png(caminho_png)
    if largura != grande:
        # o navegador as vezes devolve a janela com margem: corta o canto de cima, a esquerda
        raise RuntimeError("PNG de %dx%d, esperava %d" % (largura, altura, grande))
    return rgba if lado == grande else reduzir(largura, altura, rgba, lado)


def escrever_ico(caminho, imagens):
    """O .ico do Windows com PNG dentro (aceito desde o Vista): imagens = [(lado, bytes do PNG)]."""
    cabecalho = struct.pack("<HHH", 0, 1, len(imagens))
    entradas, dados = b"", b""
    deslocamento = 6 + 16 * len(imagens)
    for lado, png in imagens:
        entradas += struct.pack("<BBBBHHII", lado % 256, lado % 256, 0, 0, 1, 32, len(png), deslocamento + len(dados))
        dados += png
    with open(caminho, "wb") as arquivo:
        arquivo.write(cabecalho + entradas + dados)


def bytes_do_png(largura, altura, rgba):
    with tempfile.TemporaryDirectory() as pasta:
        temporario = os.path.join(pasta, "x.png")
        gravar_png(temporario, largura, altura, rgba)
        with open(temporario, "rb") as arquivo:
            return arquivo.read()


# ---------------------------------------------------------------------------

def principal():
    navegador = achar_navegador()
    if not navegador:
        sys.exit("Precisa do Edge ou do Chrome para desenhar o SVG (o Edge ja vem no Windows).")
    with tempfile.TemporaryDirectory(prefix="arena-icone-trabalho-") as trabalho:
        os.makedirs(DESTINO, exist_ok=True)
        # 1. os SVG, a fonte do desenho
        fontes = {
            "arena-icone.svg": svg("completo", 512),
            "arena-icone-pequeno.svg": svg("simples", 512),
            "arena-supercontrole.svg": svg("so-controle", 512, escala=0.80),
        }
        for nome, texto in fontes.items():
            with open(os.path.join(DESTINO, nome), "w", encoding="utf-8", newline="\n") as arquivo:
                arquivo.write(texto)
        print("SVG:", ", ".join(fontes))

        def renderizar_png(tipo, lado, nome, **opcoes):
            return png_do_svg(navegador, svg(tipo, lado, **opcoes), lado, trabalho, nome)

        # 2. o .ico do Windows e o icone da tela: o simples de 16 a 48, o completo de 64 para cima
        imagens = []
        for lado in (16, 24, 32, 48):
            imagens.append((lado, bytes_do_png(lado, lado, renderizar_png("simples", lado, "ico-s%d" % lado, escala=0.88))))
        for lado in (64, 128, 256):
            imagens.append((lado, bytes_do_png(lado, lado, renderizar_png("completo", lado, "ico-c%d" % lado, escala=0.70))))
        escrever_ico(os.path.join(RAIZ, "launcher", "arena.ico"), imagens)
        gravar_png(os.path.join(RAIZ, "launcher", "arena-icone-64.png"), 64, 64, renderizar_png("completo", 64, "l64", escala=0.70))
        gravar_png(os.path.join(RAIZ, "launcher", "arena-icone-192.png"), 192, 192, renderizar_png("completo", 192, "l192", escala=0.70))
        for nome in ("arena-icone.svg", "arena-icone-pequeno.svg"):
            shutil.copyfile(os.path.join(DESTINO, nome), os.path.join(RAIZ, "launcher", nome))
        print("launcher: arena.ico (%s), arena-icone-64.png, arena-icone-192.png, os dois SVG" % ", ".join(str(l) for l, _ in imagens))

        # 3. o site e o Chromebook (PWA "any maskable": tela cheia quadrada, controle dentro da zona segura)
        for lado in (192, 512):
            gravar_png(os.path.join(RAIZ, "ferramentas", "site", "icone-%d.png" % lado), lado, lado,
                       renderizar_png("completo", lado, "pwa%d" % lado, escala=0.56, cantos="quadrados"))
        print("site: icone-192.png, icone-512.png")

        # 4. o APK: o icone comum (48 a 192) e a frente do icone adaptavel (108 a 432, so o controle, na zona segura)
        for pasta, comum, frente in (("mipmap-mdpi", 48, 108), ("mipmap-hdpi", 72, 162), ("mipmap-xhdpi", 96, 216),
                                     ("mipmap-xxhdpi", 144, 324), ("mipmap-xxxhdpi", 192, 432)):
            saida = os.path.join(DESTINO, "android", pasta)
            tipo = "simples" if comum <= 48 else "completo"
            gravar_png(os.path.join(saida, "ic_launcher.png"), comum, comum,
                       renderizar_png(tipo, comum, "a%d" % comum, escala=0.80 if tipo == "simples" else 0.68))
            gravar_png(os.path.join(saida, "ic_launcher_foreground.png"), frente, frente,
                       renderizar_png("so-controle", frente, "f%d" % frente, escala=0.49))
        print("android: mipmap-* em docs/imagens/icone/android")

        # 5. as imagens de apresentacao
        for lado in (512, 1024):
            gravar_png(os.path.join(DESTINO, "arena-icone-%d.png" % lado), lado, lado, renderizar_png("completo", lado, "p%d" % lado, escala=0.70))
        gravar_png(os.path.join(DESTINO, "arena-supercontrole-512.png"), 512, 512,
                   renderizar_png("so-controle", 512, "sc512", escala=0.80))
        print("apresentacao: arena-icone-512/1024.png, arena-supercontrole-512.png")


if __name__ == "__main__":
    principal()
