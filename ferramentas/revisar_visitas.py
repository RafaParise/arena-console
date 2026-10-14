# -*- coding: utf-8 -*-
"""Revisa as visitas dos fundos animados (os personagens de 16 bits que
passam pelo ceu e pelo campo): chama cada uma, avanca quadro a quadro ate ela
ir embora, conta quanto durou, avisa de erro de JavaScript e monta folhas de
conferencia (uma linha por visita, alguns quadros espalhados pela visita).

Uso:
  servidor\\python\\python.exe ferramentas\\revisar_visitas.py [--tema escuro|claro]
      [--visitas nome1,nome2] [--quadros 5] [--escala 2] [--por-folha 8]
      [--semente 7] [--saida pasta]

Sem --tema, revisa os dois. A semente deixa o sorteio (direcao, altura)
igual de uma rodada para outra, para comparar antes e depois de um ajuste.
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
import limpeza  # noqa: E402
import tela_sem_janela  # noqa: E402

W, H = 160, 90
PASSO = 3                 # 3/60 s: um quadro dos 20 por segundo do fundo
INTERVALO = 10            # guarda um quadro a cada 10 (meio segundo)
LIMITE = 20 * 90          # visita que passa de 90 s e' erro

PAGINA = """<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<style>html, body { margin: 0; background: #000; } canvas { width: 160px; height: 90px; }</style>
<script>
  // Sorteio com semente (mulberry32): a mesma rodada sai sempre igual.
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
<body data-tema="%(tema)s" data-fundo-animado="sempre">
<canvas id="galaxyCanvas"></canvas>
<canvas id="fieldCanvas"></canvas>
<script src="pixel-sprites.js"></script>
<script src="%(fundo)s"></script>
</body></html>
"""


def argumento(nome, padrao):
    if nome in sys.argv:
        return sys.argv[sys.argv.index(nome) + 1]
    return padrao


def salvar_png(caminho, largura, altura, pontos):
    """PNG RGB simples (sem filtro), so com a biblioteca padrao."""
    cru = bytearray()
    for y in range(altura):
        cru.append(0)
        for r, g, b in pontos[y * largura:(y + 1) * largura]:
            cru += bytes((r, g, b))

    def bloco(tipo, dados):
        return (struct.pack(">I", len(dados)) + tipo + dados
                + struct.pack(">I", zlib.crc32(tipo + dados) & 0xFFFFFFFF))

    with open(caminho, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + bloco(b"IHDR", struct.pack(">IIBBBBB", largura, altura, 8, 2, 0, 0, 0))
                + bloco(b"IDAT", zlib.compress(bytes(cru), 9)) + bloco(b"IEND", b""))


def revisar_tema(tema, so_estas, quadros, escala, por_folha, semente, saida):
    gancho = "window.__fundoEscuro" if tema == "escuro" else "window.__fundoClaro"
    fundo = "galaxy-background.js" if tema == "escuro" else "field-background.js"
    pasta = tempfile.mkdtemp(prefix="arena_visitas_")
    problemas = []
    linhas = []                     # (nome, [quadros 160x90 RGB])
    try:
        for js in ("pixel-sprites.js", fundo):
            shutil.copy2(os.path.join(RAIZ, "launcher", js), os.path.join(pasta, js))
        caminho = os.path.join(pasta, "pagina.html")
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(PAGINA % {"tema": tema, "fundo": fundo, "semente": semente})
        with tela_sem_janela.Navegador() as nav:
            nav.abrir("file:///" + caminho.replace("\\", "/"), largura=320, altura=200, espera=1.5)
            nav.avaliar("%s.gravar(); %s.avancar(40, %d)" % (gancho, gancho, PASSO))
            nomes = nav.avaliar("%s.visitas" % gancho) or []
            for nome in [n for n in nomes if not so_estas or n in so_estas]:
                guardados = []
                passos = 0
                try:
                    nav.avaliar("%s.chamar('%s')" % (gancho, nome))
                    while True:
                        foi = nav.avaliar(
                            "(function () { const g = %s; for (let i = 0; i < %d; i++) {"
                            " if (!g.rodando()) return true; g.avancar(1, %d); } return !g.rodando(); })()"
                            % (gancho, INTERVALO, PASSO))
                        passos += INTERVALO
                        bruto = base64.b64decode(nav.avaliar("%s.pixels()" % gancho))
                        guardados.append([(bruto[i], bruto[i + 1], bruto[i + 2]) for i in range(0, len(bruto), 4)])
                        if foi or passos >= LIMITE:
                            break
                except OSError as e:
                    problemas.append("%s/%s: %s" % (tema, nome, e))
                segundos = passos / 20.0
                aviso = ""
                if passos >= LIMITE:
                    aviso = "  <- NAO FOI EMBORA"
                    problemas.append("%s/%s: passou de %d s" % (tema, nome, LIMITE // 20))
                elif segundos < 3:
                    aviso = "  <- curta demais"
                print("  %-12s %5.1f s%s" % (nome, segundos, aviso), flush=True)
                if guardados:
                    # Quadros espalhados pela visita (nem o primeiro nem o ultimo,
                    # quando o personagem ainda esta fora da tela).
                    escolha = [guardados[min(len(guardados) - 1, int((k + 0.5) * len(guardados) / quadros))]
                               for k in range(quadros)]
                    linhas.append((nome, escolha))
                # Termina a visita de vez antes da proxima.
                nav.avaliar("(function () { const g = %s; let n = 0; while (g.rodando() && n < 4000) {"
                            " g.avancar(1, %d); n++; } return n; })()" % (gancho, PASSO))
    finally:
        limpeza.apagar_pasta(pasta)
    # Folhas: por_folha visitas em cada uma, uma linha por visita.
    vao = 4
    fw, fh = W * escala, H * escala
    for i in range(0, len(linhas), por_folha):
        grupo = linhas[i:i + por_folha]
        largura = quadros * (fw + vao) + vao
        altura = len(grupo) * (fh + vao) + vao
        pontos = [(40, 40, 48)] * (largura * altura)
        for r, (_nome, escolha) in enumerate(grupo):
            for c, quadro in enumerate(escolha):
                x0, y0 = vao + c * (fw + vao), vao + r * (fh + vao)
                for y in range(fh):
                    origem = (y // escala) * W
                    base = (y0 + y) * largura + x0
                    for x in range(fw):
                        pontos[base + x] = quadro[origem + x // escala]
        arquivo = os.path.join(saida, "visitas-%s-%d.png" % (tema, i // por_folha + 1))
        salvar_png(arquivo, largura, altura, pontos)
        print("  folha: %s (%s)" % (arquivo, ", ".join(n for n, _ in grupo)))
    return problemas


def principal():
    temas = [argumento("--tema", "")] if "--tema" in sys.argv else ["escuro", "claro"]
    so_estas = [v for v in argumento("--visitas", "").split(",") if v]
    saida = os.path.abspath(argumento("--saida", os.path.join(tempfile.gettempdir(), "arena_revisao_visitas")))
    os.makedirs(saida, exist_ok=True)
    problemas = []
    for tema in temas:
        print("== %s" % tema)
        problemas += revisar_tema(tema, so_estas, int(argumento("--quadros", "5")), int(argumento("--escala", "2")),
                                  int(argumento("--por-folha", "8")), int(argumento("--semente", "7")), saida)
    print("\nProblemas: %d" % len(problemas))
    for p in problemas:
        print("  " + p)
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(principal())
