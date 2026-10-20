# -*- coding: utf-8 -*-
r"""Papel de parede do ARENA: o ceu de galaxia em pixel art
(launcher\galaxy-background.js) como fundo da area de trabalho do Windows.

Pedido do Rafael (19/10/2026): "quero que esse gif fique como plano de fundo
da area de trabalho completo e bonito, com um redimensionamento perfeito
adequando todos os pixels para nao perder qualidade".

O que a ferramenta faz (sem instalar nada, so a biblioteca padrao):
  1. desenha a cena DE VERDADE no Edge sem janela (testes\tela_sem_janela.py)
     e le os pontos do canvas (o "Fundo animado: Parado", o mesmo momento
     bonito que o proprio ARENA mostra na tela);
  2. amplia por um numero INTEIRO de vezes (nearest neighbor de verdade:
     cada ponto vira um bloco igual, sem misturar duas cores -- e' o que
     "redimensionamento perfeito" quer dizer);
  3. grava o PNG (so a biblioteca padrao) e confere, relendo o arquivo, que
     todo bloco ficou igual ao ponto de origem;
  4. aplica no Windows (SystemParametersInfoW + o registro do Windows).

Sobre o tamanho: a cena nasce 160 x 90 (16:9). A tela deste computador e'
1440 x 900 (16:10) e esticar 90 linhas em 100 daria 9 de um lado e 10 do
outro -- a cena deformaria. Entao a copia usada aqui tem 160 x 100: o ceu
ganha 10 linhas de estrelas e o chao (a serra, as pistas de luz, o planeta)
desce 10 linhas, com as mesmas distancias entre as coisas. A 1440 x 900 a
ampliacao e' 9 x 9 (exata); a 1920 x 1080 e' 12 x 12 (exata).

A altura logica e' calculada a partir do formato da tela (160 dividido pela
proporcao), e o chao acompanha: o que esta preso ao numero fixo (o planeta
e as duas pistas de luz) desce junto, o que esta preso ao ceu (a aurora, a
galaxia, as estrelas) fica onde esta. A serra das montanhas ja e' relativa
a H, entao ela desce sozinha.

Uso:
  servidor\python\python.exe ferramentas\papel_de_parede.py
      (gera para a tela deste computador e aplica no Windows)

  servidor\python\python.exe ferramentas\papel_de_parede.py
      --tamanhos 1440x900,1920x1080      (gera varios tamanhos)
  servidor\python\python.exe ferramentas\papel_de_parede.py --animado
      (gera tambem o video animado, para quem quiser o papel de parede
       animado; o Windows sozinho so aceita imagem parada)
  servidor\python\python.exe ferramentas\papel_de_parede.py --aplicar
      (so aplica, sem gerar de novo)
"""
import base64
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "testes"))
import limpeza  # noqa: E402
import tela_sem_janela  # noqa: E402

DESTINO = os.path.join(RAIZ, "docs", "imagens")
LOGICO_L = 160                 # a cena tem 160 pontos de lado
ALTURA_CENA = 90               # a altura logica da cena no launcher
LOGICO_H_MIN = 80              # o ceu nao fica curto demais nem alto demais
LOGICO_H_MAX = 120
FPS_VIDEO = 30                 # quadros por segundo do video (papel de parede)
# O passo da cena tem de caber no quadro do video: se o video e' de 30 fps,
# cada quadro anda 2/60 s da cena. Se nao combinar, a animacao roda
# acelerada (ou em camera lenta) e nao bate com o que se ve no launcher.
PASSO_CENA = max(1, int(round(60.0 / FPS_VIDEO)))
SEMENTE = 20261019             # o sorteio sai sempre igual

# O que esta preso a um numero fixo e' o que fica perto do chao: o planeta
# e as duas pistas de luz. Quando a altura logica muda, esses numeros
# descem a mesma quantidade que o chao desceu (as distancias ficam iguais).
# O que e' do ceu (aurora, galaxia, estrelas, nebulosa) fica onde esta.
CHAO = [
    ("const planeta = { x: W * 0.72, y: 58 };", "const planeta = { x: W * 0.72, y: %d };", 58),
    ("const PISTA = 71;", "const PISTA = %d;", 71),
    ("const PISTA_KART = 68;", "const PISTA_KART = %d;", 68),
]

PAGINA = """<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<style>html, body { margin: 0; padding: 0; background: #070514; overflow: hidden; }
canvas { display: none; }</style>
<script>
  // Sorteio com semente (mulberry32): a mesma rodada sai sempre igual, para
  // o papel de parede sair igual em toda maquina e toda vez.
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
</script></head>
<body data-tema="escuro" data-fundo-animado="parado">
<canvas id="galaxyCanvas"></canvas>
<script src="pixel-sprites.js"></script>
<script src="galaxy-background.js"></script>
</body></html>
"""


# ----------------------------------------------------------------------
# A cena
# ----------------------------------------------------------------------
def ajustar_cena(texto, logico_h):
    """Ajusta o codigo da cena para a altura logica pedida e devolve o
    codigo novo. Separado do I/O para dar para testar sem navegador.

    O ceu cresce (ou encolhe) e o chao desce a MESMA quantidade: as
    distancias entre o planeta, as pistas e a serra continuam as mesmas."""
    marca = "const W = %d, H = %d;" % (LOGICO_L, ALTURA_CENA)
    if marca not in texto:
        raise SystemExit("o fundo mudou e nao achei mais isto: %s" % marca)
    novo = texto.replace(marca, "const W = %d, H = %d;" % (LOGICO_L, logico_h), 1)
    desloco = logico_h - ALTURA_CENA
    for velho, modelo, altura in CHAO:
        if velho not in novo:
            raise SystemExit("o fundo mudou e nao achei mais isto: %s" % velho)
        novo = novo.replace(velho, modelo % (altura + desloco), 1)
    return novo


def preparar_cena(pasta, logico_h):
    """Copia os arquivos do launcher para a pasta e ajusta a altura logica
    da cena: o ceu cresce (ou encolhe) e o chao desce a mesma quantidade."""
    for js in ("pixel-sprites.js", "galaxy-background.js"):
        shutil.copy2(os.path.join(RAIZ, "launcher", js), os.path.join(pasta, js))
    caminho = os.path.join(pasta, "galaxy-background.js")
    with open(caminho, encoding="utf-8") as f:
        texto = f.read()
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(ajustar_cena(texto, logico_h))


def pagina_pronta(pasta):
    with open(os.path.join(pasta, "pagina.html"), "w", encoding="utf-8") as f:
        f.write(PAGINA % {"semente": SEMENTE})


def pontos_da_cena(nav, logico_w, logico_h):
    """Os pontos da cena (logico_w x logico_h) em RGB."""
    base = nav.avaliar("window.__fundoEscuro.pixels()")
    dados = base64.b64decode(base)
    if len(dados) != logico_w * logico_h * 4:
        raise SystemExit("a cena veio com %d bytes, esperava %d"
                         % (len(dados), logico_w * logico_h * 4))
    return [(dados[i], dados[i + 1], dados[i + 2]) for i in range(0, len(dados), 4)]


# ----------------------------------------------------------------------
# PNG (so a biblioteca padrao)
# ----------------------------------------------------------------------
def _bloco(tipo, dados):
    return (struct.pack(">I", len(dados)) + tipo + dados
            + struct.pack(">I", zlib.crc32(tipo + dados) & 0xFFFFFFFF))


def _gravar_png(caminho, largura, altura, linhas):
    """linhas: lista de bytes, cada uma com largura * 3 bytes (RGB)."""
    cru = bytearray()
    for linha in linhas:
        cru.append(0)              # filtro 0 (nenhum)
        cru += linha
    with open(caminho, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n"
                + _bloco(b"IHDR", struct.pack(">IIBBBBB", largura, altura, 8, 2, 0, 0, 0))
                + _bloco(b"IDAT", zlib.compress(bytes(cru), 9))
                + _bloco(b"IEND", b""))


def ampliar(pontos, largura_orig, altura_orig, escala):
    """Cada ponto vira um bloco escala x escala de uma cor so. E' a
    ampliacao 'perfeita' de pixel art: nearest neighbor, numero inteiro,
    sem misturar cores nem suavizar."""
    linhas = []
    for y in range(altura_orig):
        linha = bytearray()
        for x in range(largura_orig):
            linha += bytes(pontos[y * largura_orig + x]) * escala
        bloco = bytes(linha)
        linhas.extend([bloco] * escala)
    return linhas


def completar(linhas, largura_orig, altura_orig, escala, largura, altura):
    """Se a ampliacao ficou menor que a tela pedida, preenche as bordas (a
    ultima linha e a ultima coluna repetidas) para nao sobrar fundo
    preto. A cena continua no mesmo tamanho, sem esticar."""
    if largura_orig * escala == largura and altura_orig * escala == altura:
        return linhas
    novas = []
    for y in range(altura):
        y0 = min(y, altura_orig * escala - 1)
        linha = linhas[y0]
        if largura_orig * escala < largura:
            linha = linha + linha[-3:] * (largura - largura_orig * escala)
        novas.append(linha)
    return novas


def ler_png(caminho):
    """Le o PNG de volta: devolve (largura, altura, lista de linhas RGB)."""
    with open(caminho, "rb") as f:
        dados = f.read()
    p, idat, largura, altura = 8, bytearray(), 0, 0
    while p < len(dados):
        n, tipo = struct.unpack(">I4s", dados[p:p + 8])
        corpo = dados[p + 8:p + 8 + n]
        if tipo == b"IHDR":
            largura, altura, bits, cor = struct.unpack(">IIBB", corpo[:10])
            if bits != 8 or cor != 2:
                raise SystemExit("PNG inesperado (bits %d, cor %d)" % (bits, cor))
        elif tipo == b"IDAT":
            idat += corpo
        p += 12 + n
    cru = zlib.decompress(bytes(idat))
    tamanho = largura * 3
    saida = []
    for y in range(altura):
        inicio = y * (tamanho + 1)
        if cru[inicio] != 0:
            raise SystemExit("a linha %d do PNG tem filtro %d" % (y, cru[inicio]))
        saida.append(bytes(cru[inicio + 1:inicio + 1 + tamanho]))
    return largura, altura, saida


def conferir(caminho, pontos, largura_orig, altura_orig, escala, largura, altura):
    """Relê o PNG gravado e prova que a ampliacao foi perfeita: cada linha
    do arquivo tem que ser a linha da origem repetida, e cada bloco tem que
    ter uma cor so. Devolve a lista do que deu errado (vazia = tudo certo)."""
    l, a, linhas = ler_png(caminho)
    problemas = []
    if (l, a) != (largura, altura):
        problemas.append("o arquivo tem %dx%d, esperava %dx%d" % (l, a, largura, altura))
        return problemas
    for y in range(altura_orig):
        esperado = bytearray()
        for x in range(largura_orig):
            esperado += bytes(pontos[y * largura_orig + x]) * escala
        for k in range(escala):
            if linhas[y * escala + k] != bytes(esperado):
                problemas.append("a linha %d nao bate com o ponto de origem" % (y * escala + k))
                break
        if len(problemas) > 5:
            break
    return problemas


# ----------------------------------------------------------------------
# O video animado (para quem quiser o papel de parede se mexendo)
# ----------------------------------------------------------------------
def achar_ffmpeg():
    achado = shutil.which("ffmpeg")
    if achado:
        return achado
    base = os.path.join(os.environ.get("LOCALAPPDATA", ""), "hermes", "tools")
    if os.path.isdir(base):
        for nome in sorted(os.listdir(base)):
            cand = os.path.join(base, nome, "bin", "ffmpeg.exe")
            if os.path.isfile(cand):
                return cand
    return None


def gerar_video(nav, pasta, saida, quadros, escala, logico_h, largura, altura, ffmpeg):
    """Grava a cena se mexendo num video (MP4) que da para usar como papel
    de parede animado. A cena vai e volta (ida e volta), entao o video
    fecha em loop sem o pulo do fim."""
    pasta_quadros = os.path.join(pasta, "quadros")
    shutil.rmtree(pasta_quadros, ignore_errors=True)
    os.makedirs(pasta_quadros, exist_ok=True)
    nav.avaliar("window.__fundoEscuro.gravar()")
    nav.avaliar("window.__fundoEscuro.chamar('fzero')")
    nav.avaliar("window.__fundoEscuro.disparar('cometa')")
    nav.avaliar("window.__fundoEscuro.disparar('meteoros')")
    quadros_capturados = []
    for _i in range(quadros):
        nav.avaliar("window.__fundoEscuro.avancar(1, %d)" % PASSO_CENA)
        pontos = pontos_da_cena(nav, LOGICO_L, logico_h)
        quadros_capturados.append(ampliar(pontos, LOGICO_L, logico_h, escala))
    # Ida e volta: a mesma lista, ao contrario. O video fecha em loop.
    ordem = list(range(quadros)) + list(range(quadros - 2, 0, -1))
    for i, indice in enumerate(ordem):
        _gravar_png(os.path.join(pasta_quadros, "q_%04d.png" % i), largura, altura,
                    quadros_capturados[indice])
    comando = [ffmpeg, "-y", "-loglevel", "error", "-framerate", str(FPS_VIDEO),
               "-i", os.path.join(pasta_quadros, "q_%04d.png"),
               "-c:v", "libx264", "-preset", "slow", "-crf", "4",
               "-pix_fmt", "yuv444p", "-movflags", "+faststart", saida]
    subprocess.run(comando, check=True)
    return saida, len(ordem)


# ----------------------------------------------------------------------
# O Windows
# ----------------------------------------------------------------------
def tela_do_computador():
    """(largura, altura) em pixels de verdade da tela principal."""
    import ctypes
    u = ctypes.windll.user32
    g = ctypes.windll.gdi32
    dc = u.GetDC(0)
    try:
        return g.GetDeviceCaps(dc, 8), g.GetDeviceCaps(dc, 10)
    finally:
        u.ReleaseDC(0, dc)


def pasta_do_windows():
    """Onde o Windows guarda o papel de parede deste computador."""
    base = os.path.join(os.environ.get("LOCALAPPDATA", ""), "ARENA")
    os.makedirs(base, exist_ok=True)
    return base


def aplicar_no_windows(caminho):
    """Poe a imagem como fundo da area de trabalho (SystemParametersInfoW) e
    acerta o registro do Windows (o "preencher" e' o 10: a imagem cobre a
    tela toda, sem repetir)."""
    import ctypes
    import winreg
    destino = os.path.abspath(caminho)
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                        r"Software\Microsoft\Windows\CurrentVersion\Explorer\Wallpapers",
                        0, winreg.KEY_SET_VALUE) as k:
        winreg.SetValueEx(k, "ARENA", 0, winreg.REG_SZ, destino)
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop",
                        0, winreg.KEY_SET_VALUE) as k:
        winreg.SetValueEx(k, "WallpaperStyle", 0, winreg.REG_SZ, "10")
        winreg.SetValueEx(k, "TileWallpaper", 0, winreg.REG_SZ, "0")
        winreg.SetValueEx(k, "Wallpaper", 0, winreg.REG_SZ, destino)
    SPI_SETDESKWALLPAPER = 0x0014
    SPIF_UPDATEINIFILE, SPIF_SENDCHANGE = 0x01, 0x02
    ok = ctypes.windll.user32.SystemParametersInfoW(
        SPI_SETDESKWALLPAPER, 0, destino, SPIF_UPDATEINIFILE | SPIF_SENDCHANGE)
    return bool(ok)


# ----------------------------------------------------------------------
# Escolha do tamanho
# ----------------------------------------------------------------------
def tamanho_logico(largura, altura):
    """(altura_logica, escala) para a tela pedida.

    A altura logica sai do formato da tela: 160 pontos de lado divididos
    pela proporcao. A escala e' o maior numero INTEIRO que cabe -- e' ela
    que garante que nenhum ponto vire meio ponto."""
    proporcao = largura / float(altura)
    logico_h = int(round(LOGICO_L / proporcao))
    logico_h = max(LOGICO_H_MIN, min(LOGICO_H_MAX, logico_h))
    escala = min(largura // LOGICO_L, altura // logico_h)
    if escala < 1:
        escala = 1
    return logico_h, escala


def nome_do_arquivo(largura, altura):
    return "arena-papel-de-parede-%dx%d.png" % (largura, altura)


def argumento(nome, padrao):
    if nome in sys.argv:
        return sys.argv[sys.argv.index(nome) + 1]
    return padrao


# ----------------------------------------------------------------------
def principal():
    argumentos = sys.argv[1:]
    if "--ajuda" in argumentos or "-h" in argumentos:
        print(__doc__)
        return 0

    if "--aplicar" in argumentos:
        nome = next((a for a in argumentos if a.endswith(".png")), None)
        caminho = nome or os.path.join(pasta_do_windows(), "arena-papel-de-parede.png")
        print("aplicado: %s -> %s" % (aplicar_no_windows(caminho), caminho))
        return 0

    tela = tela_do_computador()
    if "--tamanhos" in argumentos:
        pedidos = []
        for item in argumento("--tamanhos", "").split(","):
            item = item.strip()
            if "x" in item:
                a, b = item.split("x", 1)
                pedidos.append((int(a), int(b)))
    else:
        pedidos = [tela]
    if not pedidos:
        print("tamanho invalido")
        return 1

    os.makedirs(DESTINO, exist_ok=True)
    pasta = tempfile.mkdtemp(prefix="arena_papel_")
    video = "--animado" in argumentos
    ffmpeg = achar_ffmpeg() if video else None
    if video and not ffmpeg:
        print("sem ffmpeg: o video animado ficou de fora (o PNG sai do mesmo jeito)")
    gerados = []
    try:
        for largura, altura in pedidos:
            logico_h, escala = tamanho_logico(largura, altura)
            final_l, final_h = LOGICO_L * escala, logico_h * escala
            preparar_cena(pasta, logico_h)
            pagina_pronta(pasta)
            with tela_sem_janela.Navegador() as nav:
                url = "file:///" + os.path.join(pasta, "pagina.html").replace("\\", "/")
                nav.abrir(url, largura=320, altura=200, espera=1.5)
                pontos = pontos_da_cena(nav, LOGICO_L, logico_h)
                saida = os.path.join(DESTINO, nome_do_arquivo(largura, altura))
                linhas = ampliar(pontos, LOGICO_L, logico_h, escala)
                linhas = completar(linhas, LOGICO_L, logico_h, escala, largura, altura)
                _gravar_png(saida, largura, altura, linhas)
                problemas = conferir(saida, pontos, LOGICO_L, logico_h, escala, largura, altura)
                if problemas:
                    raise SystemExit("a ampliacao nao ficou exata: " + "; ".join(problemas[:3]))
                print("%s: %dx%d (cena %dx%d, escala %dx%d) - ampliacao conferida ponto a ponto"
                      % (os.path.basename(saida), largura, altura,
                         LOGICO_L, logico_h, escala, escala))
                if final_l != largura or final_h != altura:
                    print("  aviso: a cena ocupa %dx%d; a borda foi preenchida" % (final_l, final_h))
                gerados.append((saida, largura, altura))
                if video and ffmpeg:
                    nome_video = os.path.join(DESTINO, "arena-papel-de-parede-%dx%d.mp4"
                                              % (final_l, final_h))
                    quadros = int(argumento("--quadros", "30"))
                    _caminho, quantos = gerar_video(nav, pasta, nome_video, quadros, escala,
                                                    logico_h, final_l, final_h, ffmpeg)
                    print("%s: %dx%d, %d quadros (ida e volta, fecha em loop)"
                          % (os.path.basename(nome_video), final_l, final_h, quantos))
    finally:
        limpeza.apagar_pasta(pasta)

    if "--sem-aplicar" not in argumentos and gerados:
        alvo = None
        for saida, largura, altura in gerados:
            if (largura, altura) == tela:
                alvo = saida
        if alvo is None:
            alvo = gerados[0][0]
        copia = os.path.join(pasta_do_windows(), "arena-papel-de-parede.png")
        shutil.copy2(alvo, copia)
        ok = aplicar_no_windows(copia)
        print("papel de parede aplicado no Windows: %s (%s)" % (ok, copia))
    return 0


if __name__ == "__main__":
    sys.exit(principal())
