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

  // Cola o sprite com o canto de cima a esquerda em (x, y), virado para
  // a direita (dir = 1) ou para a esquerda (dir = -1).
  function colar(ctx, sprite, x, y, dir) {
    ctx.drawImage(dir === -1 ? sprite.espelho : sprite.tela, Math.round(x), Math.round(y));
  }

  window.SpritesRetro = { fazer: fazer, quadros: quadros, colar: colar };
})();
