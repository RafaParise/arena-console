# -*- coding: utf-8 -*-
r"""Gera a imagem da pagina do ARENA no GitHub a partir do proprio fundo
escuro do ARENA (o ceu de galaxia em pixel art, launcher\galaxy-background.js).

Pedido do Rafael (07/10/2026): "a pagina do github do arena com a imagem do
fundo do modo escuro do ARENA para personalizar". A imagem sai do codigo de
verdade da tela -- o mesmo ceu, os mesmos desenhos --, desenhado como no
"Fundo animado: Parado" (a cena num momento bonito), com o nome ARENA no
estilo do topo da tela. Mudou o fundo? Rode de novo e a pagina acompanha.

Gera, em docs\imagens\:
  - arena-capa.png        1280 x 640: a capa parada. O topo do LEIA-ME do
                          GitHub agora e' o GIF animado
                          (ferramentas\gravar_fundo_gif.py); a capa fica
                          como alternativa para a "Social preview" (a
                          imagem de quando alguem compartilha o link);
  - arena-fundo-escuro.png 1920 x 1080: o fundo sozinho, sem texto (papel de
                          parede, apresentacao de aula).

Usa o Edge (ou o Chrome) sem janela, com perfil temporario: o navegador do
usuario nao e' tocado. Nada de internet.

Uso:
    servidor\python\python.exe ferramentas\imagem_do_github.py
"""
import os
import shutil
import sys
import tempfile
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "testes"))
import limpeza  # noqa: E402
import tela_sem_janela  # noqa: E402

DESTINO = os.path.join(RAIZ, "docs", "imagens")

# O nome no estilo do topo da tela (estilo.css: .marca-nome), em tamanho de
# cartaz. A cena tem 160 x 90 pontos: esticada para 1280 x 720 (8 vezes) e
# cortada no meio para os 1280 x 640 da capa.
PAGINA = """<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<style>
  html, body { margin: 0; width: %(largura)dpx; height: %(altura)dpx; overflow: hidden; background: #070514; }
  #galaxyCanvas { position: fixed; left: 0; top: %(topo)dpx; width: %(largura)dpx; height: %(altura_cena)dpx;
                  image-rendering: pixelated; display: block; }
  .marca { position: fixed; inset: 0; display: %(com_texto)s; flex-direction: column; align-items: center;
           justify-content: center; gap: 10px; text-align: center; }
  .nome { font-family: "Courier New", monospace; font-weight: 700; font-size: 176px; letter-spacing: 0.08em;
          color: #ffe08a; line-height: 1;
          text-shadow: 8px 8px 0 #7c4d9e, 0 0 46px rgba(255, 209, 102, .35); }
  .sub { font-family: "Segoe UI", system-ui, sans-serif; font-size: 40px; font-weight: 600; color: #f1ecff;
         text-shadow: 0 2px 10px rgba(0, 0, 0, .85); }
  .linha { font-family: "Segoe UI", system-ui, sans-serif; font-size: 25px; color: #d6cff5;
           text-shadow: 0 2px 8px rgba(0, 0, 0, .9); margin-top: 8px; }
</style></head>
<body data-tema="escuro" data-fundo-animado="parado">
<canvas id="galaxyCanvas"></canvas>
<div class="marca">
  <div class="nome">ARENA</div>
  <div class="sub">central retr&ocirc; da turma</div>
  <div class="linha">mais de 50 consoles na sala de aula &middot; roda de pen drive &middot; sem instalar nada</div>
</div>
<script src="pixel-sprites.js"></script>
<script src="galaxy-background.js"></script>
</body></html>
"""


# Na capa, os Metroides e o planeta caiam bem atras das letras (o "Parado"
# desenha a cena em t = 300, sempre no mesmo lugar). So na copia da capa,
# eles vao para as laterais e para baixo, parados; os sorteios continuam na
# mesma ordem, entao o resto do ceu (estrelas, nebulosas, lua) fica igual.
# Se o galaxy-background.js mudar e um trecho nao casar, para e avisa.
AJUSTES_DA_CAPA = [
    ("cx: 40 + i * 72, cy: 31 + sorteio() * 8,",
     "cx: [16, 144][i], cy: 47 + 0 * sorteio(),"),
    ("raioX: 18 + sorteio() * 12, raioY: 7 + sorteio() * 5,",
     "raioX: 0 * (18 + sorteio() * 12), raioY: 0 * (7 + sorteio() * 5),"),
    ("const planeta = { x: W * 0.72, y: 58 };",
     "const planeta = { x: W * 0.875, y: 76 };"),
]


def preparar_fundo_da_capa(pasta):
    """Grava galaxy-background-capa.js (a copia com os ajustes da capa)."""
    with open(os.path.join(pasta, "galaxy-background.js"), encoding="utf-8") as f:
        texto = f.read()
    for velho, novo in AJUSTES_DA_CAPA:
        if texto.count(velho) != 1:
            raise SystemExit("O launcher\\galaxy-background.js mudou: o trecho '%s' nao foi achado "
                             "(uma vez). Atualize AJUSTES_DA_CAPA nesta ferramenta." % velho)
        texto = texto.replace(velho, novo)
    with open(os.path.join(pasta, "galaxy-background-capa.js"), "w", encoding="utf-8") as f:
        f.write(texto)


def desenhar(navegador, pasta, nome, largura, altura, com_texto):
    altura_cena = largura * 9 // 16              # a cena e' 16:9
    pagina = os.path.join(pasta, nome + ".html")
    html = PAGINA % {"largura": largura, "altura": altura, "altura_cena": altura_cena,
                     "topo": (altura - altura_cena) // 2, "com_texto": "flex" if com_texto else "none"}
    if com_texto:
        html = html.replace('src="galaxy-background.js"', 'src="galaxy-background-capa.js"')
    with open(pagina, "w", encoding="utf-8") as f:
        f.write(html)
    url = "file:///" + pagina.replace("\\", "/")
    navegador.abrir(url, largura=largura, altura=altura, espera=2.0)
    destino = os.path.join(DESTINO, nome + ".png")
    navegador.foto(destino)
    return destino


def principal():
    os.makedirs(DESTINO, exist_ok=True)
    pasta = tempfile.mkdtemp(prefix="arena_imagem_github_")
    try:
        for js in ("pixel-sprites.js", "galaxy-background.js"):
            shutil.copy2(os.path.join(RAIZ, "launcher", js), os.path.join(pasta, js))
        preparar_fundo_da_capa(pasta)
        with tela_sem_janela.Navegador() as navegador:
            for nome, largura, altura, com_texto in (("arena-capa", 1280, 640, True),
                                                     ("arena-fundo-escuro", 1920, 1080, False)):
                destino = desenhar(navegador, pasta, nome, largura, altura, com_texto)
                print("%s (%d x %d, %d KB)" % (os.path.relpath(destino, RAIZ), largura, altura,
                                              os.path.getsize(destino) // 1024))
                time.sleep(0.3)
    finally:
        limpeza.apagar_pasta(pasta)
    return 0


if __name__ == "__main__":
    sys.exit(principal())
