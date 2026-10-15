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
onde cada quadro e' uma lista de largura*altura cores (r, g, b). GIF comprido
(centenas de quadros grandes): conte as cores antes (contar_cores e
paleta_da_contagem) e passe os quadros por um gerador, com paleta=.
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


def contar_cores(quadros, contagem=None):
    """Soma as cores dos quadros em 'contagem' ({cor: quantas}) e a devolve. Vale
    para um gerador: o GIF comprido conta as cores sem guardar os quadros."""
    contagem = {} if contagem is None else contagem
    for quadro in quadros:
        for cor in quadro:
            contagem[cor] = contagem.get(cor, 0) + 1
    return contagem


def paleta_de(quadros, maximo=255):
    return paleta_da_contagem(contar_cores(quadros), maximo)


def paleta_da_contagem(contagem, maximo=255):
    """(paleta, mapa): ate 'maximo' cores e, para cada cor dos quadros, a da
    paleta mais parecida."""
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

    # O dicionario guarda cada sequencia como (codigo da sequencia sem o
    # ultimo ponto, ultimo ponto) -> codigo novo, num numero so: o codigo
    # vezes 256, mais o ponto (a paleta tem ate 256 entradas). A sequencia de
    # um ponto so tem o proprio ponto como codigo. Igual ao LZW de sempre, mas
    # sem montar tuplas cada vez maiores (o GIF de 1280 x 640 com centenas de
    # quadros levava horas).
    largura = tamanho_minimo + 1
    dicionario = {}
    proximo = fim + 1
    emitir(limpar, largura)
    atual = -1
    for indice in indices:
        if atual < 0:
            atual = indice
            continue
        chave = (atual << 8) | indice
        codigo = dicionario.get(chave)
        if codigo is not None:
            atual = codigo
            continue
        emitir(atual, largura)
        if proximo < 4096:
            dicionario[chave] = proximo
            proximo += 1
            if proximo > (1 << largura) and largura < 12:
                largura += 1
        else:
            emitir(limpar, largura)
            dicionario = {}
            proximo = fim + 1
            largura = tamanho_minimo + 1
        atual = indice
    if atual >= 0:
        emitir(atual, largura)
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


def salvar(caminho, largura, altura, quadros, atraso_cs=10, repetir=True, paleta=None, tolerancia=0):
    """Grava o GIF. Devolve o tamanho em bytes.

    Para um GIF comprido, 'quadros' pode ser um gerador e 'paleta' o par
    (paleta, mapa) feito antes (paleta_da_contagem): o GIF e' gravado quadro a
    quadro, e so o quadro atual e o anterior ficam na memoria.

    'tolerancia' (distancia entre duas cores, de 0 a 441): o ponto que mudou
    menos que isso fica como esta na tela. O ceu que pulsa devagar (a aurora,
    as nebulosas) deixa de ser regravado inteiro a cada quadro, e o GIF
    encolhe. A comparacao e' sempre com o que ja aparece na tela, entao a
    diferenca nunca se acumula. Com 0, so o ponto igual fica."""
    if paleta is None:
        quadros = list(quadros)
        paleta = paleta_de(quadros)
    paleta, mapa = paleta
    transparente = len(paleta)                    # a cor reservada
    cores = list(paleta) + [(0, 0, 0)]
    bits_paleta = max(1, (len(cores) - 1).bit_length())
    cores += [(0, 0, 0)] * ((1 << bits_paleta) - len(cores))
    tamanho_minimo = max(2, bits_paleta)
    # perto[a][b]: as cores a e b da paleta estao dentro da tolerancia.
    perto = [bytes(1 if a != b and (ra - rb) ** 2 + (ga - gb) ** 2 + (ba - bb) ** 2 <= tolerancia ** 2 else 0
                   for b, (rb, gb, bb) in enumerate(paleta))
             for a, (ra, ga, ba) in enumerate(paleta)] if tolerancia else None
    with open(caminho, "wb") as f:
        dados = bytearray(b"GIF89a")
        dados += struct.pack("<HHBBB", largura, altura, 0x80 | 0x70 | (bits_paleta - 1), 0, 0)
        for cor in cores:
            dados += bytes(cor)
        if repetir:
            dados += b"\x21\xff\x0bNETSCAPE2.0\x03\x01\x00\x00\x00"
        f.write(dados)
        tela = None                       # o que aparece na tela depois do quadro anterior
        for quadro in quadros:
            indices = [mapa[c] for c in quadro]
            if tela is None:
                x0, y0, x1, y1 = 0, 0, largura - 1, altura - 1
                recorte = indices
                tela = indices
            else:
                # Linha por linha (comparar a linha inteira e' muito mais rapido
                # que ponto a ponto): o que muda vira o ponto novo, o resto -1.
                mudancas = {}
                x0, y0, x1, y1 = largura, None, -1, None
                for y in range(altura):
                    inicio = y * largura
                    nova, velha = indices[inicio:inicio + largura], tela[inicio:inicio + largura]
                    if nova == velha:
                        continue
                    if perto:
                        linha = [a if a != b and not perto[a][b] else -1 for a, b in zip(nova, velha)]
                    else:
                        linha = [a if a != b else -1 for a, b in zip(nova, velha)]
                    esquerda = next((x for x, v in enumerate(linha) if v >= 0), None)
                    if esquerda is None:
                        continue                  # so mudancas pequenas: a linha fica
                    direita = largura - 1 - next(x for x, v in enumerate(reversed(linha)) if v >= 0)
                    mudancas[y] = linha
                    x0, x1 = min(x0, esquerda), max(x1, direita)
                    y0 = y if y0 is None else y0
                    y1 = y
                if y0 is None:
                    x0 = y0 = x1 = y1 = 0                 # quadro igual: 1 ponto transparente
                recorte = []
                for y in range(y0, y1 + 1):
                    linha = mudancas.get(y)
                    if linha is None:
                        recorte += [transparente] * (x1 - x0 + 1)
                    else:
                        recorte += [transparente if v < 0 else v for v in linha[x0:x1 + 1]]
                if mudancas:
                    tela = list(tela)
                    for y, linha in mudancas.items():
                        inicio = y * largura
                        tela[inicio:inicio + largura] = [v if v >= 0 else b
                                                         for v, b in zip(linha, tela[inicio:inicio + largura])]
            w, h = x1 - x0 + 1, y1 - y0 + 1
            # Controle grafico: "deixar como esta" (1), com transparencia.
            dados = bytearray(b"\x21\xf9\x04" + bytes([0x04 | 0x01]) + struct.pack("<H", atraso_cs)
                              + bytes([transparente]) + b"\x00")
            dados += b"\x2c" + struct.pack("<HHHHB", x0, y0, w, h, 0)
            dados.append(tamanho_minimo)
            dados += _lzw(recorte, tamanho_minimo)
            f.write(dados)
        f.write(b"\x3b")
        return f.tell()
