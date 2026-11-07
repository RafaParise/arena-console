# -*- coding: utf-8 -*-
r"""
Desenha as imagens dos controles de toque de cada console (servidor\toque\consoles\*.png), a partir da lista
IMAGENS de servidor\toque_consoles.py.

So para quem mexe no ARENA: precisa do Pillow (py -m pip install pillow), que NAO vai no ARENA. O ARENA usa os .png
prontos, que ficam no repositorio. Rode de novo depois de mudar uma cor ou um texto em IMAGENS:

    py ferramentas\gerar_toque_consoles.py
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
import toque_consoles  # noqa: E402

FONTE = r"C:\Windows\Fonts\arialbd.ttf"
GRANDE = 4                              # desenha 4x maior e reduz: bordas lisas
BORDA = (255, 255, 255, 150)


def cor(texto, alfa=235):
    texto = texto.lstrip("#")
    return tuple(int(texto[i:i + 2], 16) for i in (0, 2, 4)) + (alfa,)


def escrever(d, caixa, texto, cor_texto, maximo):
    x0, y0, x1, y1 = caixa
    tamanho = maximo
    while tamanho > 8:
        fonte = ImageFont.truetype(FONTE, tamanho)
        b = d.textbbox((0, 0), texto, font=fonte)
        if b[2] - b[0] <= (x1 - x0) * 0.8 and b[3] - b[1] <= (y1 - y0) * 0.7:
            break
        tamanho -= 4
    b = d.textbbox((0, 0), texto, font=fonte)
    d.text(((x0 + x1 - (b[2] - b[0])) / 2 - b[0], (y0 + y1 - (b[3] - b[1])) / 2 - b[1]), texto, font=fonte,
           fill=cor(cor_texto, 255))


def desenhar(forma, fundo, texto, cor_texto):
    if forma in ("pilula", "feijao_deitado"):
        w, h = 240, 100
    elif forma == "feijao_vertical":
        w, h = 100, 240
    elif forma == "base":
        w, h = 256, 256
    else:
        w, h = 128, 128
    W, H, m = w * GRANDE, h * GRANDE, 4 * GRANDE
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if forma == "circulo" or forma == "pino":
        d.ellipse((m, m, W - m, H - m), fill=cor(fundo), outline=BORDA, width=3 * GRANDE)
        if texto:
            escrever(d, (m, m, W - m, H - m), texto, cor_texto, 70 * GRANDE)
    elif forma in ("pilula", "feijao_deitado", "feijao_vertical"):
        raio = min(W, H) // 2 - m
        d.rounded_rectangle((m, m, W - m, H - m), radius=raio, fill=cor(fundo), outline=BORDA, width=3 * GRANDE)
        if texto:
            escrever(d, (m, m, W - m, H - m), texto, cor_texto, 60 * GRANDE)
    elif forma == "base":
        d.ellipse((m, m, W - m, H - m), fill=cor(fundo, 90), outline=cor(fundo, 230), width=10 * GRANDE)
    elif forma == "seta":
        d.rounded_rectangle((m, m, W - m, H - m), radius=24 * GRANDE, fill=cor(fundo), outline=BORDA, width=3 * GRANDE)
        c, a = W / 2, W * 0.22
        pontas = {"cima": [(c, c - a), (c - a, c + a * 0.6), (c + a, c + a * 0.6)],
                  "baixo": [(c, c + a), (c - a, c - a * 0.6), (c + a, c - a * 0.6)],
                  "esquerda": [(c - a, c), (c + a * 0.6, c - a), (c + a * 0.6, c + a)],
                  "direita": [(c + a, c), (c - a * 0.6, c - a), (c - a * 0.6, c + a)]}[texto]
        d.polygon(pontas, fill=(255, 255, 255, 230))
    elif forma == "simbolo":
        d.ellipse((m, m, W - m, H - m), fill=cor("#2b2d31"), outline=BORDA, width=3 * GRANDE)
        c, a, linha = W / 2, W * 0.24, 9 * GRANDE
        tinta = cor(fundo, 255)
        if texto == "triangulo":
            d.polygon([(c, c - a), (c - a * 1.05, c + a * 0.7), (c + a * 1.05, c + a * 0.7)], outline=tinta, width=linha)
        elif texto == "circulo":
            d.ellipse((c - a, c - a, c + a, c + a), outline=tinta, width=linha)
        elif texto == "quadrado":
            d.rectangle((c - a * 0.85, c - a * 0.85, c + a * 0.85, c + a * 0.85), outline=tinta, width=linha)
        else:
            d.line((c - a, c - a, c + a, c + a), fill=tinta, width=linha)
            d.line((c - a, c + a, c + a, c - a), fill=tinta, width=linha)
    return img.resize((w, h), Image.LANCZOS)


def principal():
    destino = toque_consoles.PASTA_DAS_IMAGENS
    os.makedirs(destino, exist_ok=True)
    for nome, (forma, fundo, texto, cor_texto) in sorted(toque_consoles.IMAGENS.items()):
        desenhar(forma, fundo, texto, cor_texto).save(os.path.join(destino, nome + ".png"), optimize=True)
    print("%d imagens em %s" % (len(toque_consoles.IMAGENS), destino))


if __name__ == "__main__":
    principal()
