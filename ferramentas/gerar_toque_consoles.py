# -*- coding: utf-8 -*-
r"""
Desenha as imagens dos controles de toque de cada console (servidor\toque\consoles\*.png), a partir da lista
IMAGENS de servidor\toque_consoles.py.

So para quem mexe no ARENA: precisa do Pillow (py -m pip install pillow), que NAO vai no ARENA. O ARENA usa os .png
prontos, que ficam no repositorio. Rode de novo depois de mudar uma cor ou um texto em IMAGENS:

    py ferramentas\gerar_toque_consoles.py

Cada botao e' desenhado como o de verdade (pedido do Rafael, 07/11/2026): a sombra embaixo, o corpo com a luz vindo de
cima, a borda mais escura, um brilho no alto e a letra gravada. O desenho sai 4 vezes maior e e' reduzido no fim, para
as bordas ficarem lisas. Alem das pecas, sai uma imagem inteira de cada direcional (<fundo>_tela.png), que a tela
"Arrumar os botoes" mostra.
"""
import math
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
import toque_consoles  # noqa: E402

FONTE = r"C:\Windows\Fonts\arialbd.ttf"
G = 4                                   # desenha 4x maior e reduz: bordas lisas


# ---------------------------------------------------------------------------
# Cores
# ---------------------------------------------------------------------------

def rgb(texto):
    texto = texto.lstrip("#")
    return tuple(int(texto[i:i + 2], 16) for i in (0, 2, 4))


def misturar(cor, alvo, quanto):
    """A cor 'cor' levada 'quanto' (0 a 1) na direcao de 'alvo'."""
    return tuple(int(round(a + (b - a) * quanto)) for a, b in zip(cor, alvo))


def clarear(cor, quanto):
    return misturar(cor, (255, 255, 255), quanto)


def escurecer(cor, quanto):
    return misturar(cor, (0, 0, 0), quanto)


def claridade(cor):
    return (0.299 * cor[0] + 0.587 * cor[1] + 0.114 * cor[2]) / 255


# ---------------------------------------------------------------------------
# O volume: sombra, corpo com luz de cima, borda, brilho
# ---------------------------------------------------------------------------

def mascara(tamanho, desenho):
    m = Image.new("L", tamanho, 0)
    desenho(ImageDraw.Draw(m))
    return m


def gradiente(tamanho, cima, baixo):
    """Um degrade de cima para baixo (RGB)."""
    w, h = tamanho
    faixa = Image.new("RGB", (1, h))
    for y in range(h):
        faixa.putpixel((0, y), misturar(cima, baixo, y / max(1, h - 1)))
    return faixa.resize((w, h))


def com_volume(img, forma, cor, alfa=240, sombra=True, brilho=True, borda=True):
    """Pinta em 'img' o corpo de um botao com o formato da mascara 'forma' e a cor 'cor'."""
    w, h = img.size
    if sombra:
        s = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        s.putalpha(ImageChops.offset(forma, 0, 3 * G).point(lambda v: v * 120 // 255))
        s = s.filter(ImageFilter.GaussianBlur(4 * G))
        img.alpha_composite(s)
    corpo = gradiente((w, h), clarear(cor, 0.22), escurecer(cor, 0.28)).convert("RGBA")
    corpo.putalpha(forma.point(lambda v: v * alfa // 255))
    img.alpha_composite(corpo)
    if borda:
        miolo = forma.filter(ImageFilter.MinFilter(2 * (2 * G) + 1))
        aro = ImageChops.subtract(forma, miolo)
        camada = Image.new("RGBA", (w, h), escurecer(cor, 0.45) + (0,))
        camada.putalpha(aro.point(lambda v: v * 200 // 255))
        img.alpha_composite(camada)
    if brilho:
        caixa = forma.getbbox()
        if caixa:
            x0, y0, x1, y1 = caixa
            luz = Image.new("L", (w, h), 0)
            ImageDraw.Draw(luz).ellipse((x0 + (x1 - x0) * 0.18, y0 + (y1 - y0) * 0.06,
                                         x1 - (x1 - x0) * 0.18, y0 + (y1 - y0) * 0.46), fill=95)
            luz = ImageChops.multiply(luz.filter(ImageFilter.GaussianBlur(5 * G)), forma)
            branco = Image.new("RGBA", (w, h), (255, 255, 255, 0))
            branco.putalpha(luz)
            img.alpha_composite(branco)


def escrever(img, caixa, texto, cor_botao, cor_texto, maximo):
    """A letra no meio da caixa. Sem cor de texto, a letra fica gravada: a cor do botao, mais escura, com uma linha
    de luz embaixo (como as letras em relevo dos controles da Nintendo e da Sega)."""
    if not texto:
        return
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = caixa
    tamanho = maximo
    while tamanho > 8:
        fonte = ImageFont.truetype(FONTE, tamanho)
        b = d.textbbox((0, 0), texto, font=fonte)
        if b[2] - b[0] <= (x1 - x0) * 0.78 and b[3] - b[1] <= (y1 - y0) * 0.6:
            break
        tamanho -= 4
    b = d.textbbox((0, 0), texto, font=fonte)
    px = (x0 + x1 - (b[2] - b[0])) / 2 - b[0]
    py = (y0 + y1 - (b[3] - b[1])) / 2 - b[1]
    if cor_texto:
        d.text((px, py + 2 * G), texto, font=fonte, fill=(0, 0, 0, 90))
        d.text((px, py), texto, font=fonte, fill=rgb(cor_texto) + (255,))
    else:
        base = rgb(cor_botao)
        gravada = escurecer(base, 0.5) if claridade(base) > 0.35 else clarear(base, 0.45)
        d.text((px, py + 2 * G), texto, font=fonte, fill=clarear(base, 0.55) + (150,))
        d.text((px, py), texto, font=fonte, fill=gravada + (255,))


# ---------------------------------------------------------------------------
# Cada forma
# ---------------------------------------------------------------------------

TAMANHOS = {"pilula": (240, 100), "feijao_deitado": (240, 100), "feijao_vertical": (100, 240),
            "base_redonda": (256, 256), "base_octogono": (256, 256), "botoes_c": (256, 256),
            "dpad_cruz": (256, 256), "dpad_sega": (256, 256), "dpad_ps": (256, 256), "dpad_alavanca": (256, 256)}


def octogono(cx, cy, raio):
    return [(cx + raio * math.cos(math.radians(22.5 + 45 * i)), cy + raio * math.sin(math.radians(22.5 + 45 * i)))
            for i in range(8)]


def triangulo(cx, cy, a, lado):
    """Um triangulo de 'tamanho' a, com a ponta para 'lado'."""
    return {"cima": [(cx, cy - a), (cx - a, cy + a * 0.7), (cx + a, cy + a * 0.7)],
            "baixo": [(cx, cy + a), (cx - a, cy - a * 0.7), (cx + a, cy - a * 0.7)],
            "esquerda": [(cx - a, cy), (cx + a * 0.7, cy - a), (cx + a * 0.7, cy + a)],
            "direita": [(cx + a, cy), (cx - a * 0.7, cy - a), (cx - a * 0.7, cy + a)]}[lado]


def desenhar(forma, fundo, texto, cor_texto):
    w, h = TAMANHOS.get(forma, (128, 128))
    W, H = w * G, h * G
    m = 7 * G                                          # a folga da sombra
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cor = rgb(fundo)

    if forma == "circulo":
        com_volume(img, mascara((W, H), lambda d: d.ellipse((m, m, W - m, H - m - 2 * G), fill=255)), cor)
        escrever(img, (m, m, W - m, H - m), texto, fundo, cor_texto, 64 * G)

    elif forma in ("pilula", "feijao_deitado", "feijao_vertical"):
        raio = min(W, H) // 2 - m
        if forma == "pilula":
            alvo = lambda d: d.rounded_rectangle((m, m, W - m, H - m - 2 * G), radius=raio, fill=255)  # noqa: E731
        else:
            # o feijao do GameCube: uma pilula curvada em arco (o X e o Y abracam o A)
            def alvo(d):
                deitado = forma == "feijao_deitado"
                comprido, grosso = (W, H) if deitado else (H, W)
                pincel = grosso * 0.33
                curva = comprido * 1.15                      # o raio do arco: quanto maior, mais reto
                meio = math.asin((comprido / 2 - pincel - m) / curva)   # metade do angulo do arco
                caida = curva * (1 - math.cos(meio))         # quanto as pontas descem
                for i in range(81):
                    a = -meio + 2 * meio * i / 80
                    ao_longo = comprido / 2 + curva * math.sin(a)
                    fundo_do_arco = (grosso - caida) / 2 + curva * (1 - math.cos(a))
                    px, py = (ao_longo, fundo_do_arco) if deitado else (grosso - fundo_do_arco, ao_longo)
                    d.ellipse((px - pincel, py - pincel - G, px + pincel, py + pincel - G), fill=255)
        com_volume(img, mascara((W, H), alvo), cor)
        escrever(img, (m, m, W - m, H - m), texto, fundo, cor_texto, 58 * G)

    elif forma == "simbolo":
        # PlayStation: o botao preto e brilhante com o simbolo colorido por cima
        com_volume(img, mascara((W, H), lambda d: d.ellipse((m, m, W - m, H - m - 2 * G), fill=255)), rgb("#26272b"))
        d = ImageDraw.Draw(img)
        c, a, linha = W / 2, W * 0.215, 10 * G
        tinta = cor + (255,)
        cy = c - G
        if texto == "triangulo":
            pontos = [(c, cy - a * 1.05), (c - a * 1.1, cy + a * 0.78), (c + a * 1.1, cy + a * 0.78)]
            d.line(pontos + [pontos[0]], fill=tinta, width=linha, joint="curve")
        elif texto == "circulo":
            d.ellipse((c - a, cy - a, c + a, cy + a), outline=tinta, width=linha)
        elif texto == "quadrado":
            d.rectangle((c - a * 0.86, cy - a * 0.86, c + a * 0.86, cy + a * 0.86), outline=tinta, width=linha)
        else:
            d.line((c - a, cy - a, c + a, cy + a), fill=tinta, width=linha)
            d.line((c - a, cy + a, c + a, cy - a), fill=tinta, width=linha)

    elif forma == "base_redonda":
        anel = mascara((W, H), lambda d: d.ellipse((m, m, W - m, H - m), fill=255))
        camada = Image.new("RGBA", (W, H), cor + (0,))
        camada.putalpha(anel.point(lambda v: v * 120 // 255))
        img.alpha_composite(camada)
        ImageDraw.Draw(img).ellipse((m, m, W - m, H - m), outline=escurecer(cor, 0.35) + (230,), width=7 * G)
        ImageDraw.Draw(img).ellipse((W * 0.2, H * 0.2, W * 0.8, H * 0.8), outline=clarear(cor, 0.25) + (70,), width=2 * G)

    elif forma == "base_octogono":
        # o "portao" de oito lados do Nintendo 64 e do GameCube, por onde o analogico anda
        c = W / 2
        fora = mascara((W, H), lambda d: d.polygon(octogono(c, c, c - m), fill=255))
        camada = Image.new("RGBA", (W, H), cor + (0,))
        camada.putalpha(fora.point(lambda v: v * 130 // 255))
        img.alpha_composite(camada)
        d = ImageDraw.Draw(img)
        d.polygon(octogono(c, c, c - m), outline=escurecer(cor, 0.4) + (235,), width=7 * G)
        d.polygon(octogono(c, c, c * 0.62), outline=clarear(cor, 0.2) + (70,), width=2 * G)

    elif forma == "pino":
        com_volume(img, mascara((W, H), lambda d: d.ellipse((m, m, W - m, H - m - 2 * G), fill=255)), cor)
        d = ImageDraw.Draw(img)
        d.ellipse((W * 0.24, H * 0.22, W * 0.76, H * 0.74), outline=escurecer(cor, 0.3) + (150,), width=3 * G)
        escrever(img, (m, m, W - m, H - m), texto, fundo, cor_texto, 56 * G)

    elif forma == "botoes_c":
        # os quatro C amarelos do Nintendo 64, cada um com a seta para o seu lado
        c, r, dist = W / 2, W * 0.165, W * 0.315
        for lado, (dx, dy) in (("cima", (0, -1)), ("baixo", (0, 1)), ("esquerda", (-1, 0)), ("direita", (1, 0))):
            cx, cy = c + dx * dist, c + dy * dist
            com_volume(img, mascara((W, H), lambda d, cx=cx, cy=cy: d.ellipse((cx - r, cy - r, cx + r, cy + r),
                                                                               fill=255)), cor)
            ImageDraw.Draw(img).polygon(triangulo(cx, cy - G, r * 0.42, lado), fill=escurecer(cor, 0.5) + (255,))

    elif forma == "dpad_cruz":
        # a cruz da Nintendo: bracos com 1/3 da largura, o meio levemente afundado
        c = W / 2
        braco = W * (2 * toque_consoles.MEIO_BRACO) / (2 * toque_consoles.FUNDO_DO_DIRECIONAL) / 2
        borda = m

        def cruz(d):
            d.rounded_rectangle((c - braco, borda, c + braco, H - borda - 2 * G), radius=5 * G, fill=255)
            d.rounded_rectangle((borda, c - braco - G, W - borda, c + braco - G), radius=5 * G, fill=255)
        com_volume(img, mascara((W, H), cruz), cor, brilho=False)
        d = ImageDraw.Draw(img)
        d.ellipse((c - braco * 0.55, c - braco * 0.55 - G, c + braco * 0.55, c + braco * 0.55 - G),
                  fill=escurecer(cor, 0.25) + (200,))

    elif forma == "dpad_sega":
        # o disco da Sega com a cruz em relevo
        c = W / 2
        com_volume(img, mascara((W, H), lambda d: d.ellipse((m, m, W - m, H - m - 2 * G), fill=255)), cor)
        braco = W * 0.15
        d = ImageDraw.Draw(img)
        relevo = clarear(cor, 0.12) + (255,)
        d.rounded_rectangle((c - braco, W * 0.16, c + braco, W * 0.84 - 2 * G), radius=4 * G, fill=relevo)
        d.rounded_rectangle((W * 0.16, c - braco - G, W * 0.84, c + braco - G), radius=4 * G, fill=relevo)
        d.ellipse((c - braco * 0.6, c - braco * 0.6 - G, c + braco * 0.6, c + braco * 0.6 - G),
                  fill=escurecer(cor, 0.2) + (255,))

    elif forma == "dpad_ps":
        # o buraco redondo onde ficam as quatro setas soltas do PlayStation
        c = W / 2
        d = ImageDraw.Draw(img)
        d.ellipse((m, m, W - m, H - m), fill=cor + (150,), outline=escurecer(cor, 0.4) + (200,), width=4 * G)
        d.ellipse((c - W * 0.07, c - W * 0.07, c + W * 0.07, c + W * 0.07), fill=escurecer(cor, 0.3) + (200,))

    elif forma == "dpad_alavanca":
        # a alavanca de fliperama vista de cima: o aro e a bola
        c = W / 2
        d = ImageDraw.Draw(img)
        d.ellipse((m, m, W - m, H - m), fill=(30, 31, 35, 130), outline=(20, 20, 22, 220), width=6 * G)
        d.ellipse((c - W * 0.08, c - W * 0.08, c + W * 0.08, c + W * 0.08), fill=(70, 72, 78, 255))
        bola = W * 0.24
        com_volume(img, mascara((W, H), lambda d: d.ellipse((c - bola, c - bola - 2 * G, c + bola, c + bola - 2 * G),
                                                            fill=255)), cor)

    elif forma == "marca":
        # o triangulo em relevo de cada braco do direcional (acende quando o braco e' tocado)
        c = W / 2
        ImageDraw.Draw(img).polygon(triangulo(c, c, W * 0.17, texto), fill=cor + (110,))

    elif forma == "seta_ps":
        # cada seta do PlayStation: a tecla larga na ponta de fora e fina perto do meio, com o triangulo
        c = W / 2

        def tecla(d):
            # desenhada com a ponta para cima e girada depois
            d.polygon([(W * 0.06, H * 0.04), (W * 0.94, H * 0.04), (W * 0.94, H * 0.60), (c, H * 0.97),
                       (W * 0.06, H * 0.60)], fill=255)
        alvo = mascara((W, H), tecla).filter(ImageFilter.GaussianBlur(G)).point(lambda v: 255 if v > 128 else 0)
        giro = {"cima": 0, "esquerda": 90, "baixo": 180, "direita": 270}[texto]
        alvo = alvo.rotate(giro)
        com_volume(img, alvo, cor)
        ImageDraw.Draw(img).polygon(triangulo(c, c, W * 0.12, texto), fill=(18, 18, 20, 230))

    return img.resize((w, h), Image.LANCZOS)


def direcional_inteiro(fundo, bracos, imagens):
    """O direcional montado (fundo + os quatro bracos), como ele aparece no jogo: para a tela de arrumar."""
    lado = 256
    tela = imagens[fundo].resize((lado, lado), Image.LANCZOS).copy()
    medida = int(round(lado / 2 * toque_consoles.MEIO_BRACO / toque_consoles.FUNDO_DO_DIRECIONAL))  # metade do braco
    passo = lado / 2 / toque_consoles.FUNDO_DO_DIRECIONAL                                         # um braco
    for nome, (dx, dy) in zip(bracos, ((0, -1), (0, 1), (-1, 0), (1, 0))):
        peca = imagens[nome].resize((2 * medida, 2 * medida), Image.LANCZOS)
        tela.alpha_composite(peca, (int(lado / 2 + dx * passo - medida), int(lado / 2 + dy * passo - medida)))
    return tela


def principal():
    destino = toque_consoles.PASTA_DAS_IMAGENS
    os.makedirs(destino, exist_ok=True)
    feitas = {}
    for nome, (forma, fundo, texto, cor_texto) in sorted(toque_consoles.IMAGENS.items()):
        feitas[nome] = desenhar(forma, fundo, texto, cor_texto)
        feitas[nome].save(os.path.join(destino, nome + ".png"), optimize=True)
    for fundo, bracos in toque_consoles.DIRECIONAIS.values():
        direcional_inteiro(fundo, bracos, feitas).save(os.path.join(destino, fundo + "_tela.png"), optimize=True)
    # as imagens velhas que nenhum desenho usa mais
    validas = {n + ".png" for n in toque_consoles.IMAGENS} | {f + "_tela.png" for f, _ in
                                                             toque_consoles.DIRECIONAIS.values()}
    for arquivo in os.listdir(destino):
        if arquivo.endswith(".png") and arquivo not in validas:
            os.remove(os.path.join(destino, arquivo))
    print("%d imagens em %s" % (len(validas), destino))


if __name__ == "__main__":
    principal()
