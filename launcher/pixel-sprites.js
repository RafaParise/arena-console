// ==========================================================================
// ARENA - sprites em pixel art para os fundos animados (ceu e campo).
//
// Cada sprite e' escrito como TEXTO: uma linha por fileira de pontos, uma
// letra por ponto ('.' = vazio), e a paleta diz a cor de cada letra. Assim
// o desenho fica legivel no proprio codigo -- da para "ver" o personagem
// olhando o arquivo -- e qualquer aluno pode desenhar o seu.
//
// O sprite e' pintado UMA vez numa telinha escondida (e numa espelhada,
// para andar para o outro lado). A cada quadro o fundo so cola a telinha
// pronta (drawImage): custa quase nada, ate no Celeron da escola.
//
// Personagens de jogos famosos de 8 e 16 bits (pedido do Rafael, 02/10/2026):
// desenhos proprios, pequenos, em homenagem aos jogos -- nao sao os sprites
// tirados dos jogos. Todo desenho olha para a DIREITA; para a esquerda,
// usa-se o espelho.
// ==========================================================================
(function () {
  // Uma telinha com o desenho, e outra com o desenho espelhado.
  function fazer(linhas, paleta) {
    const h = linhas.length;
    let w = 0;
    for (const linha of linhas) w = Math.max(w, linha.length);
    const tela = document.createElement('canvas');
    tela.width = w;
    tela.height = h;
    const c = tela.getContext('2d');
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < linhas[y].length; x++) {
        const cor = paleta[linhas[y][x]];
        if (!cor) continue;                 // '.' e letra sem cor: vazio
        c.fillStyle = cor;
        c.fillRect(x, y, 1, 1);
      }
    }
    const espelho = document.createElement('canvas');
    espelho.width = w;
    espelho.height = h;
    const e = espelho.getContext('2d');
    e.translate(w, 0);
    e.scale(-1, 1);
    e.drawImage(tela, 0, 0);
    return { tela: tela, espelho: espelho, w: w, h: h };
  }

  // Varios quadros de animacao com a mesma paleta.
  function quadros(lista, paleta) {
    return lista.map(function (linhas) { return fazer(linhas, paleta); });
  }

  // O mesmo sprite girado de 90 em 90 graus (quartos = 1, 2 ou 3, no sentido
  // do relogio). Em pixel art, girar de 90 em 90 nao perde nada: cada ponto so
  // muda de lugar, copiado um a um. Serve para a estrela do Diddy e o
  // rolamento do Kiddy (20/10/2026).
  function girar(sprite, quartos) {
    quartos = ((quartos % 4) + 4) % 4;
    const deitado = quartos % 2 === 1;
    const w = deitado ? sprite.h : sprite.w, h = deitado ? sprite.w : sprite.h;
    const origem = sprite.tela.getContext('2d').getImageData(0, 0, sprite.w, sprite.h).data;
    const tela = document.createElement('canvas');
    tela.width = w;
    tela.height = h;
    const c = tela.getContext('2d');
    const destino = c.createImageData(w, h);
    for (let y = 0; y < sprite.h; y++) {
      for (let x = 0; x < sprite.w; x++) {
        let nx = x, ny = y;
        if (quartos === 1) { nx = sprite.h - 1 - y; ny = x; }
        else if (quartos === 2) { nx = sprite.w - 1 - x; ny = sprite.h - 1 - y; }
        else if (quartos === 3) { nx = y; ny = sprite.w - 1 - x; }
        const de = (y * sprite.w + x) * 4, para = (ny * w + nx) * 4;
        for (let i = 0; i < 4; i++) destino.data[para + i] = origem[de + i];
      }
    }
    c.putImageData(destino, 0, 0);
    const espelho = document.createElement('canvas');
    espelho.width = w;
    espelho.height = h;
    const e = espelho.getContext('2d');
    e.translate(w, 0);
    e.scale(-1, 1);
    e.drawImage(tela, 0, 0);
    return { tela: tela, espelho: espelho, w: w, h: h };
  }

  // Cola o sprite com o canto de cima a esquerda em (x, y), virado para
  // a direita (dir = 1) ou para a esquerda (dir = -1).
  function colar(ctx, sprite, x, y, dir) {
    ctx.drawImage(dir === -1 ? sprite.espelho : sprite.tela, Math.round(x), Math.round(y));
  }

  window.SpritesRetro = { fazer: fazer, quadros: quadros, girar: girar, colar: colar };
})();
