# -*- coding: utf-8 -*-
r"""GIF animado em Python puro (so a biblioteca padrao), para o ARENA gravar os
fundos animados como GIF (a imagem de compartilhamento do GitHub aceita GIF de
ate 1 MB).

- Paleta unica de ate 255 cores (corte pela mediana quando passa) e uma cor
  reservada para "transparente".
- Cada quadro grava so o retangulo que mudou em relacao ao anterior, e dentro
  dele os pontos iguais ao anterior viram transparentes (o GIF guarda muito
  menos). Pixel art ampliado comprime muito bem assim.
- LZW do GIF com codigos de 3 a 12 bits.

Uso (como biblioteca):
    import gif_animado
    gif_animado.salvar("saida.gif", largura, altura, quadros, atraso_cs=10)
onde cada quadro e' uma lista de largura*altura cores (r, g, b).
"""
import struct


def _corte_pela_mediana(contagem, maximo):
    """contagem: {cor: quantas}. Devolve ate 'maximo' cores representativas."""
    caixas = [list(contagem.items())]
    while len(caixas) < maximo:
        # Divide a caixa com mais pontos e alguma variacao.
        caixas.sort(key=lambda c: sum(q for _, q in c), reverse=True)
        for i, caixa in enumerate(caixas):
            if len(caixa) > 1:
                break
        else:
            break
        caixa = caixas.pop(i)
        faixas = [max(c[0][k] for c in caixa) - min(c[0][k] for c in caixa) for k in range(3)]
        eixo = faixas.index(max(faixas))
        caixa.sort(key=lambda c: c[0][eixo])
        total = sum(q for _, q in caixa)
        acumulado, corte = 0, 1
        for j, (_, q) in enumerate(caixa):
            acumulado += q
            if acumulado >= total / 2:
                corte = max(1, min(len(caixa) - 1, j + 1))
                break
        caixas += [caixa[:corte], caixa[corte:]]
    paleta = []
    for caixa in caixas:
        total = sum(q for _, q in caixa)
        paleta.append(tuple(int(round(sum(c[k] * q for c, q in caixa) / total)) for k in range(3)))
    return paleta


def paleta_de(quadros, maximo=255):
    contagem = {}
    for quadro in quadros:
        for cor in quadro:
            contagem[cor] = contagem.get(cor, 0) + 1
    if len(contagem) <= maximo:
        paleta = sorted(contagem)
        return paleta, {cor: i for i, cor in enumerate(paleta)}
    paleta = _corte_pela_mediana(contagem, maximo)
    mapa = {}
    for cor in contagem:
        mapa[cor] = min(range(len(paleta)), key=lambda i: (paleta[i][0] - cor[0]) ** 2
                        + (paleta[i][1] - cor[1]) ** 2 + (paleta[i][2] - cor[2]) ** 2)
    return paleta, mapa


def _lzw(indices, tamanho_minimo):
    limpar = 1 << tamanho_minimo
    fim = limpar + 1
    saida = bytearray()
    acumulador = 0
    bits = 0

    def emitir(codigo, largura):
        nonlocal acumulador, bits
        acumulador |= codigo << bits
        bits += largura
        while bits >= 8:
            saida.append(acumulador & 0xff)
            acumulador >>= 8
            bits -= 8

    largura = tamanho_minimo + 1
    dicionario = {(i,): i for i in range(limpar)}
    proximo = fim + 1
    emitir(limpar, largura)
    atual = None
    for indice in indices:
        if atual is None:
            atual = (indice,)
            continue
        candidato = atual + (indice,)
        if candidato in dicionario:
            atual = candidato
            continue
        emitir(dicionario[atual], largura)
        if proximo < 4096:
            dicionario[candidato] = proximo
            proximo += 1
            if proximo > (1 << largura) and largura < 12:
                largura += 1
        else:
            emitir(limpar, largura)
            dicionario = {(i,): i for i in range(limpar)}
            proximo = fim + 1
            largura = tamanho_minimo + 1
        atual = (indice,)
    if atual is not None:
        emitir(dicionario[atual], largura)
    emitir(fim, largura)
    if bits:
        saida.append(acumulador & 0xff)
    blocos = bytearray()
    for i in range(0, len(saida), 255):
        pedaco = saida[i:i + 255]
        blocos.append(len(pedaco))
        blocos += pedaco
    blocos.append(0)
    return bytes(blocos)


def salvar(caminho, largura, altura, quadros, atraso_cs=10, repetir=True):
    """Grava o GIF. Devolve o tamanho em bytes."""
    paleta, mapa = paleta_de(quadros)
    transparente = len(paleta)                    # a cor reservada
    cores = list(paleta) + [(0, 0, 0)]
    bits_paleta = max(1, (len(cores) - 1).bit_length())
    cores += [(0, 0, 0)] * ((1 << bits_paleta) - len(cores))
    tamanho_minimo = max(2, bits_paleta)
    dados = bytearray(b"GIF89a")
    dados += struct.pack("<HHBBB", largura, altura, 0x80 | 0x70 | (bits_paleta - 1), 0, 0)
    for cor in cores:
        dados += bytes(cor)
    if repetir:
        dados += b"\x21\xff\x0bNETSCAPE2.0\x03\x01\x00\x00\x00"
    anterior = None
    for quadro in quadros:
        indices = [mapa[c] for c in quadro]
        if anterior is None:
            x0, y0, x1, y1 = 0, 0, largura - 1, altura - 1
        else:
            mudou = [i for i in range(len(indices)) if indices[i] != anterior[i]]
            if mudou:
                ys = [i // largura for i in mudou]
                xs = [i % largura for i in mudou]
                x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
            else:
                x0 = y0 = x1 = y1 = 0                 # quadro igual: 1 ponto transparente
        w, h = x1 - x0 + 1, y1 - y0 + 1
        recorte = []
        for y in range(y0, y1 + 1):
            linha = indices[y * largura + x0:y * largura + x1 + 1]
            if anterior is not None:
                velha = anterior[y * largura + x0:y * largura + x1 + 1]
                linha = [transparente if a == b else a for a, b in zip(linha, velha)]
            recorte += linha
        # Controle grafico: "deixar como esta" (1), com transparencia.
        dados += b"\x21\xf9\x04" + bytes([0x04 | 0x01]) + struct.pack("<H", atraso_cs) + bytes([transparente]) + b"\x00"
        dados += b"\x2c" + struct.pack("<HHHHB", x0, y0, w, h, 0)
        dados.append(tamanho_minimo)
        dados += _lzw(recorte, tamanho_minimo)
        anterior = indices
    dados += b"\x3b"
    with open(caminho, "wb") as f:
        f.write(dados)
    return len(dados)
