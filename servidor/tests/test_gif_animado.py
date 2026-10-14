# -*- coding: utf-8 -*-
"""ferramentas\\gif_animado.py (o GIF dos fundos para o GitHub, 12/10/2026):
grava, le de volta com um decodificador independente (escrito aqui) e confere
ponto a ponto. O Edge tambem leu um GIF dificil igual (200 cores, LZW ate
12 bits com reinicio) quando a ferramenta foi escrita."""
import os
import struct
import sys
import tempfile
import unittest

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(AQUI)), "ferramentas"))
import gif_animado  # noqa: E402


def decodificar(caminho):
    d = open(caminho, "rb").read()
    largura, altura, flags = struct.unpack("<HHB", d[6:11])
    n = 2 << (flags & 7)
    paleta = [tuple(d[13 + 3 * i:16 + 3 * i]) for i in range(n)]
    p, tela, quadros, transparente = 13 + 3 * n, [None] * (largura * altura), [], None
    while d[p] != 0x3B:
        if d[p] == 0x21:
            if d[p + 1] == 0xF9:
                transparente = d[p + 6] if d[p + 3] & 1 else None
            p += 2
            while d[p]:
                p += d[p] + 1
            p += 1
            continue
        x0, y0, w, h, _ = struct.unpack("<HHHHB", d[p + 1:p + 10])
        minimo, p = d[p + 10], p + 11
        dados = bytearray()
        while d[p]:
            dados += d[p + 1:p + 1 + d[p]]
            p += d[p] + 1
        p += 1
        limpar = 1 << minimo
        bits, saida, anterior, pos = minimo + 1, [], None, 0
        dic = [[i] for i in range(limpar)] + [None, None]
        while pos + bits <= len(dados) * 8:
            cod = sum(1 << k for k in range(bits) if dados[(pos + k) // 8] >> ((pos + k) % 8) & 1)
            pos += bits
            if cod == limpar:
                dic, bits, anterior = [[i] for i in range(limpar)] + [None, None], minimo + 1, None
                continue
            if cod == limpar + 1:
                break
            if cod < len(dic) and dic[cod] is not None:
                ent = dic[cod]
                if anterior is not None:
                    dic.append(anterior + [ent[0]])
            else:
                ent = anterior + [anterior[0]]
                dic.append(ent)
            saida += ent
            anterior = ent
            if len(dic) == (1 << bits) and bits < 12:
                bits += 1
        for i, idx in enumerate(saida[:w * h]):
            if idx != transparente:
                tela[(y0 + i // w) * largura + x0 + i % w] = paleta[idx]
        quadros.append(list(tela))
    return largura, altura, quadros


class TestGifAnimado(unittest.TestCase):
    def test_grava_e_le_igual(self):
        largura, altura, quadros = 48, 24, []
        for k in range(5):
            quadros.append([(255, 200, 0) if (x - 6 - k * 8) ** 2 + (y - 12) ** 2 < 30
                            else (40, 0, 80) if (x + y) % 5 == 0 else (11, 13, 23)
                            for y in range(altura) for x in range(largura)])
        pasta = tempfile.mkdtemp(prefix="arena_gif_teste_")
        try:
            caminho = os.path.join(pasta, "teste.gif")
            gif_animado.salvar(caminho, largura, altura, quadros, atraso_cs=8)
            w, h, lidos = decodificar(caminho)
        finally:
            for nome in os.listdir(pasta):
                os.remove(os.path.join(pasta, nome))
            os.rmdir(pasta)
        self.assertEqual((w, h, len(lidos)), (largura, altura, len(quadros)))
        for original, lido in zip(quadros, lidos):
            self.assertEqual(original, lido)

    def test_muitas_cores_viram_ate_255(self):
        cores = [(i % 256, (i * 7) % 256, (i * 13) % 256) for i in range(1000)]
        paleta, mapa = gif_animado.paleta_de([cores])
        self.assertLessEqual(len(paleta), 255)
        self.assertEqual(set(mapa), set(cores))


if __name__ == "__main__":
    unittest.main()
