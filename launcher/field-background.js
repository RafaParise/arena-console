// ==========================================================================
// ARENA - fundo do tema CLARO: um campo de girassois em pixel art (canvas).
//
// Como funciona (vale ler, e' o mesmo esquema do galaxy-background.js):
//
//  1. A cena tem so 160 x 90 pontos e e' esticada pelo CSS
//     (image-rendering: pixelated). Por isso fica nitida em qualquer tela,
//     de 1366x768 ate 4K, custando quase nada.
//  2. O que nunca se mexe (ceu, morros, grama, florzinhas) e' desenhado UMA
//     vez numa "camada fixa" escondida. A cada quadro so se cola essa
//     camada (1 operacao) e se desenha por cima o que se mexe.
//  3. 20 quadros por segundo bastam para 160 x 90, contados por relogio
//     (setTimeout), e nao a cada quadro da tela (requestAnimationFrame, 60
//     por segundo). Auditoria 3 (08/10/2026), medido com a tela parada, 6
//     amostras: a 30 quadros acordando a cada quadro da tela, 7,7% de um
//     nucleo do Ryzen; a 20 por relogio, 5,0% (-35%). No Celeron da escola
//     e' de ~18% para ~11% de um nucleo, so com o menu aberto. (A 30 por
//     relogio ficou PIOR: 10%. Por isso os 20.)
//  4. Tres jeitos de mostrar (body[data-fundo-animado], escolha do aluno em
//     Ajustes -> Simples): "automatico" anima, a nao ser que o modo modesto
//     esteja ligado ou o Windows peca menos movimento; "sempre" anima
//     sempre; "parado" desenha a cena uma vez so e nao gasta mais nada.
//
// Achado de 01/10/2026 (tarefa 8 do Rafael, "os fundos animados nao
// funcionam mais"): o Windows em "Ajustar para obter melhor desempenho"
// (animacoes desligadas) faz o navegador avisar "prefira menos movimento",
// e desde 23/09 o fundo, nesse caso, nao desenhava NADA. Agora a cena
// aparece sempre; o que muda e' so se ela se mexe.
//
// 02/10/2026 (Rafael): a joaninha era "so uma barrinha preta e vermelha" e
// o coelho "nao mostra mexendo as pernas pulando" -- os dois ganharam
// desenho de verdade. E o campo recebe visitas de jogos famosos de 8 e 16
// bits, uma de cada vez: Mario e o Goomba, o Sonic, os patos e o cachorro
// do Duck Hunt e o Kirby flutuando. Desenhos em launcher\pixel-sprites.js.
// ==========================================================================
(function () {
  const canvas = document.getElementById('fieldCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const S = window.SpritesRetro;

  const W = 160, H = 90;
  const HORIZONTE = 52;
  canvas.width = W;
  canvas.height = H;
  ctx.imageSmoothingEnabled = false;

  // Sorteio com semente: a cena parada sai sempre igual (nada de "pular"
  // de lugar ao trocar de tema), e a animada continua variada.
  let semente = 20260930;
  function sorteio() {
    semente = (semente * 1103515245 + 12345) & 0x7fffffff;
    return semente / 0x7fffffff;
  }
  const aleatorio = Math.random;

  // ------------------------------------------------------------------
  // Camada fixa: desenhada uma vez, colada a cada quadro.
  // ------------------------------------------------------------------
  const fixa = document.createElement('canvas');
  fixa.width = W;
  fixa.height = H;
  const fctx = fixa.getContext('2d');

  const ceu = ['#78c4ff', '#8dd0ff', '#a3dbff', '#bce6ff', '#d3f1ff'];
  const flores = [];          // florzinhas paradas na grama
  for (let i = 0; i < 34; i++) {
    flores.push({
      x: Math.floor(sorteio() * W),
      y: HORIZONTE + 4 + Math.floor(sorteio() * (H - HORIZONTE - 6)),
      c: ['#ffffff', '#ff8fc7', '#c39bff', '#ffe066', '#ff6b6b'][Math.floor(sorteio() * 5)]
    });
  }

  function desenharCamadaFixa() {
    const c = fctx;
    // Ceu em faixas, tipo degrade de console 8 bits.
    const faixa = Math.ceil(HORIZONTE / ceu.length);
    for (let i = 0; i < ceu.length; i++) {
      c.fillStyle = ceu[i];
      c.fillRect(0, i * faixa, W, faixa);
    }
    // Morros ao longe (dois planos), pela soma de duas ondas.
    for (let x = 0; x < W; x++) {
      const longe = HORIZONTE - 7 - Math.round(3 * Math.sin(x * 0.05) + 2 * Math.sin(x * 0.13 + 1));
      c.fillStyle = '#a7d8b4';
      c.fillRect(x, longe, 1, HORIZONTE - longe);
      const perto = HORIZONTE - 3 - Math.round(2 * Math.sin(x * 0.08 + 2) + 1.5 * Math.sin(x * 0.21));
      c.fillStyle = '#93cf7a';
      c.fillRect(x, perto, 1, HORIZONTE - perto + 1);
    }
    // Arvore no morro da esquerda.
    c.fillStyle = '#6b4423';
    c.fillRect(17, HORIZONTE - 9, 2, 6);
    c.fillStyle = '#3f8f3a';
    c.fillRect(13, HORIZONTE - 15, 10, 4);
    c.fillRect(14, HORIZONTE - 17, 8, 2);
    c.fillRect(15, HORIZONTE - 11, 6, 2);
    c.fillStyle = '#56a84a';
    c.fillRect(15, HORIZONTE - 16, 4, 2);
    // Grama em faixas.
    const grama = [['#8fd14f', 8], ['#79bd3f', 10], ['#5fa334', H]];
    let y = HORIZONTE;
    for (const [cor, altura] of grama) {
      c.fillStyle = cor;
      c.fillRect(0, y, W, altura);
      y += altura;
    }
    // Textura da grama: pontinhos um pouco mais claros ou escuros.
    for (let i = 0; i < 260; i++) {
      c.fillStyle = sorteio() < 0.5 ? 'rgba(255,255,255,0.10)' : 'rgba(0,0,0,0.10)';
      c.fillRect(Math.floor(sorteio() * W), HORIZONTE + Math.floor(sorteio() * (H - HORIZONTE)), 1, 1);
    }
    // Florzinhas: ponto colorido com miolo amarelo.
    for (const f of flores) {
      c.fillStyle = f.c;
      c.fillRect(f.x, f.y, 1, 1);
      c.fillRect(f.x - 1, f.y + 1, 1, 1);
      c.fillRect(f.x + 1, f.y + 1, 1, 1);
      c.fillStyle = '#f4c430';
      c.fillRect(f.x, f.y + 1, 1, 1);
    }
  }
  desenharCamadaFixa();

  canvas.addEventListener('contextlost', function (e) { e.preventDefault(); });
  canvas.addEventListener('contextrestored', function () {
    ctx.imageSmoothingEnabled = false;
    desenharCamadaFixa();
    desenharQuadro();
  });

  // ------------------------------------------------------------------
  // O que se mexe
  // ------------------------------------------------------------------
  let t = 0;          // tempo em "quadros de 1/60 s"
  let vento = 1;      // 1 = brisa; rajada sobe ate ~2,5 e volta
  let ventoAlvo = 1;

  // Nuvens
  const formasNuvem = [
    [[0, 1], [1, 0], [2, 0], [3, 0], [4, 1], [1, 1], [2, 1], [3, 1]],
    [[0, 0], [1, 0], [2, 0], [1, 1], [2, 1], [3, 1], [0, 1]],
    [[0, 1], [1, 0], [2, 0], [3, 1], [1, 1], [2, 1], [4, 1], [5, 1], [3, 0]],
    [[1, 0], [2, 0], [0, 1], [1, 1], [2, 1], [3, 1], [4, 1], [2, -1]]
  ];
  const nuvens = [];
  for (let i = 0; i < 4; i++) {
    nuvens.push({ forma: formasNuvem[i], x: sorteio() * W, y: 3 + Math.floor(sorteio() * 22),
                  vel: 0.04 + sorteio() * 0.05, escala: i === 3 ? 3 : 2 });
  }

  // Girassois, cada um com seu balanco
  const girassois = [];
  for (let i = 0; i < 11; i++) {
    girassois.push({
      baseX: 6 + i * ((W - 12) / 10) + (sorteio() - 0.5) * 4,
      baseY: H - 4 - Math.floor(sorteio() * 6),
      haste: 12 + Math.floor(sorteio() * 8),
      fase: sorteio() * Math.PI * 2,
      vel: 0.02 + sorteio() * 0.015
    });
  }
  girassois.sort(function (a, b) { return a.baseY - b.baseY; });

  function balanco(g) {
    return Math.sin(t * g.vel + g.fase) * 2.2 * vento;
  }

  function miolo(g) {
    return { x: g.baseX + balanco(g), y: g.baseY - g.haste - 2 };
  }

  // Borboletas: cada especie com sua cor de asa e de borda
  const especies = [
    { asa: '#ff9f43', borda: '#2b1c12' },   // monarca (laranja)
    { asa: '#4aa3ff', borda: '#1d3b6b' },   // morfo (azul)
    { asa: '#ffe066', borda: '#8a6d00' },   // amarela
    { asa: '#ff7eb6', borda: '#7a2450' },   // rosa
    { asa: '#ffffff', borda: '#7a7a7a' },   // branca
    { asa: '#b388ff', borda: '#3d2470' }    // roxa
  ];
  const borboletas = [];
  for (let i = 0; i < 4; i++) {
    borboletas.push({
      especie: especies[i],
      estado: 'longe',
      espera: 60 + i * 140 + sorteio() * 120,     // entra uma de cada vez
      x: 0, y: 0, flor: -1, idade: 0,
      faseAsa: sorteio() * Math.PI * 2,
      fasePasseio: sorteio() * Math.PI * 2
    });
  }

  function florLivre(atual) {
    const ocupadas = new Set(borboletas.map(function (b) { return b.flor; }));
    let tentativa = 0, idx;
    do {
      idx = Math.floor(aleatorio() * girassois.length);
      tentativa++;
    } while ((idx === atual || ocupadas.has(idx)) && tentativa < 20);
    return idx;
  }

  function atualizarBorboleta(b, passo) {
    b.idade += passo;
    if (b.estado === 'longe') {
      b.espera -= passo;
      if (b.espera <= 0) {
        const lado = aleatorio() < 0.5 ? -1 : 1;
        b.x = lado === 1 ? -8 : W + 8;
        b.y = 8 + aleatorio() * 25;
        b.estado = aleatorio() < 0.5 ? 'passeando' : 'indo';
        b.flor = florLivre(b.flor);
        b.idade = 0;
        b.duracao = 180 + aleatorio() * 300;
        b.saida = aleatorio() < 0.5 ? -1 : 1;
      }
      return;
    }
    const alvo = miolo(girassois[b.flor]);
    if (b.estado === 'passeando') {
      // Oito no ar (curva de Lissajous) antes de escolher a flor.
      const cx = W * 0.5 + Math.sin(b.fasePasseio) * 40;
      b.x += ((cx + Math.sin(t * 0.021 + b.fasePasseio) * 34) - b.x) * 0.04 * passo;
      b.y += ((22 + Math.sin(t * 0.042 + b.fasePasseio) * 10) - b.y) * 0.04 * passo;
      if (b.idade > 240) { b.estado = 'indo'; b.idade = 0; }
    } else if (b.estado === 'indo') {
      b.x += (alvo.x - b.x) * 0.05 * passo;
      b.y += (alvo.y - b.y) * 0.05 * passo + Math.sin(t * 0.3) * 0.2;
      if (Math.abs(alvo.x - b.x) < 1.2 && Math.abs(alvo.y - b.y) < 1.2) {
        b.estado = 'pousada';
        b.idade = 0;
      }
    } else if (b.estado === 'pousada') {
      b.x = alvo.x + Math.sin(t * 0.12) * 0.4;
      b.y = alvo.y + Math.sin(t * 0.18) * 0.4;
      if (b.idade > b.duracao) {
        // Mais uma flor ou embora?
        if (aleatorio() < 0.45) {
          b.flor = florLivre(b.flor);
          b.estado = 'indo';
        } else {
          b.estado = 'saindo';
        }
        b.idade = 0;
      }
    } else if (b.estado === 'saindo') {
      const destino = b.saida === 1 ? W + 12 : -12;
      b.x += (destino - b.x) * 0.04 * passo;
      b.y += Math.sin(t * 0.06 + b.faseAsa) * 0.4 * passo - 0.05 * passo;
      const saiu = b.saida === 1 ? b.x > W + 8 : b.x < -8;
      if (saiu) {
        b.estado = 'longe';
        b.flor = -1;
        b.espera = 200 + aleatorio() * 400;
        b.especie = especies[Math.floor(aleatorio() * especies.length)];
      }
    }
  }

  // Borboleta em 5 x 4 pontos, tres posicoes da batida de asa:
  // 0 = asas abertas, 1 = meio caminho, 2 = asas fechadas pra cima.
  // A = asa, P = ponta da asa (cor da borda), C = corpo.
  const POSES_BORBOLETA = [
    [[-2, -1, 'P'], [-1, -1, 'A'], [1, -1, 'A'], [2, -1, 'P'],
     [-2, 0, 'A'], [-1, 0, 'A'], [1, 0, 'A'], [2, 0, 'A'],
     [-1, 1, 'A'], [1, 1, 'A'], [0, -1, 'C'], [0, 0, 'C'], [0, 1, 'C']],
    [[-1, -2, 'P'], [1, -2, 'P'], [-1, -1, 'A'], [1, -1, 'A'],
     [-1, 0, 'A'], [1, 0, 'A'], [0, -1, 'C'], [0, 0, 'C'], [0, 1, 'C']],
    [[0, -3, 'P'], [0, -2, 'A'], [0, -1, 'C'], [0, 0, 'C'], [0, 1, 'C']]
  ];

  function desenharBorboleta(b) {
    if (b.estado === 'longe') return;
    const bx = Math.round(b.x), by = Math.round(b.y);
    const pousada = b.estado === 'pousada';
    // Pousada bate a asa devagar; voando, rapido.
    const onda = Math.abs(Math.sin(t * (pousada ? 0.06 : 0.3) + b.faseAsa));
    const pose = POSES_BORBOLETA[onda > 0.66 ? 0 : onda > 0.33 ? 1 : 2];
    const cores = { A: b.especie.asa, P: b.especie.borda, C: '#2b1c12' };
    for (const p of pose) {
      ctx.fillStyle = cores[p[2]];
      ctx.fillRect(bx + p[0], by + p[1], 1, 1);
    }
  }

  // Abelhas: voltinhas em volta de uma flor, trocam de flor de vez em quando
  const abelhas = [];
  for (let i = 0; i < 2; i++) {
    abelhas.push({ flor: Math.floor(sorteio() * girassois.length), fase: sorteio() * 6, troca: 300 + sorteio() * 400 });
  }

  function desenharAbelhas(passo) {
    for (const a of abelhas) {
      a.troca -= passo;
      if (a.troca <= 0) {
        a.flor = Math.floor(aleatorio() * girassois.length);
        a.troca = 300 + aleatorio() * 400;
      }
      const m = miolo(girassois[a.flor]);
      const x = Math.round(m.x + Math.cos(t * 0.09 + a.fase) * 5);
      const y = Math.round(m.y - 3 + Math.sin(t * 0.18 + a.fase) * 2);
      ctx.fillStyle = '#ffd23f';
      ctx.fillRect(x, y, 2, 1);
      ctx.fillStyle = '#2b1c12';
      ctx.fillRect(x + 1, y, 1, 1);
      if (Math.floor(t / 2) % 2 === 0) {          // asinhas piscando
        ctx.fillStyle = 'rgba(255,255,255,0.85)';
        ctx.fillRect(x, y - 1, 1, 1);
      }
    }
  }

  // Passarinhos: um bando em "v" cruzando o ceu de vez em quando
  let bando = null;
  let esperaBando = 600 + sorteio() * 600;

  function desenharBando(passo) {
    if (!bando) {
      esperaBando -= passo;
      if (esperaBando <= 0) {
        const dir = aleatorio() < 0.5 ? 1 : -1;
        const n = 3 + Math.floor(aleatorio() * 3);
        bando = { dir: dir, x: dir === 1 ? -20 : W + 20, y: 8 + aleatorio() * 18, n: n, fase: aleatorio() * 6 };
      }
      return;
    }
    bando.x += bando.dir * 0.45 * passo;
    for (let i = 0; i < bando.n; i++) {
      const lado = i % 2 === 0 ? 1 : -1;
      const fila = Math.ceil(i / 2);
      const x = Math.round(bando.x - bando.dir * fila * 5);
      const y = Math.round(bando.y + lado * fila * 2 + Math.sin(t * 0.05 + i) * 0.8);
      const asaPraCima = Math.floor((t + i * 7) / 8) % 2 === 0;
      ctx.fillStyle = '#3a3a5a';
      ctx.fillRect(x, y, 1, 1);
      ctx.fillRect(x - 1, y + (asaPraCima ? -1 : 0), 1, 1);
      ctx.fillRect(x + 1, y + (asaPraCima ? -1 : 0), 1, 1);
    }
    if (bando.x < -40 || bando.x > W + 40) {
      bando = null;
      esperaBando = 900 + aleatorio() * 1500;
    }
  }

  // Os coelhos aos pulos de verdade (02/10/2026: antes o corpo subia e
  // descia inteiro, sem perna nenhuma). Pedido do Rafael (20/10/2026): o
  // coelho branco maior, com uma coelha caramelo de jubinha (com a listra
  // marrom nas costas) e um coelho preto medio, sem juba, maior que ela.
  // Cada pulo: agacha, estica as pernas no ar e cai agachado de novo; os tres
  // vao para o mesmo lado, cada um no seu tempo.
  // B pelo, b sombra, E orelha, e dentro da orelha, K olho, n nariz, T rabo,
  // F patas; na coelha, J a jubinha e L a listra das costas.
  const COELHO_BRANCO = S.quadros([
    ['.........k.k...',
     '........kEkEk..',
     '.......kEeEek..',
     '.......kEeEek..',
     '.......kEeEek..',
     '....kkkBBBBBk..',
     '...kbBBBBBKBBk.',
     '..kbBBBBBBBBBnk',
     '.kBBBBBBBBBBBk.',
     'kTBBBBBBBBBbk..',
     '.kbBBBBBBBBbk..',
     '..kFFFkkFFFFk..',
     '...kkk..kkkk...'],   // agachado (antes e depois do pulo)
    ['...............',
     '...............',
     '..........k.k..',
     '.........kEkEk.',
     '........kEeEek.',
     '........kEeEek.',
     '....kkkkBBBBBk.',
     '.kkkbBBBBBBKBnk',
     'kTBBBBBBBBBBBk.',
     '.kbBBBBBBBBBk..',
     '.kkbbBBBBbbk...',
     'kFFFkkkkkFFFk..',
     '.kkk.....kkk...']   // no ar: as pernas de tras esticadas
  ], { B: '#f4f0ea', b: '#d4cabc', E: '#f4f0ea', e: '#ffb0c0', K: '#3a1a1a', n: '#ff8fb0', T: '#ffffff', F: '#e0d6c8', k: '#5a4c44' });
  const COELHO_PRETO = S.quadros([
    ['........k.k...',
     '.......kEkEk..',
     '......kEeEek..',
     '......kEeEek..',
     '...kkkBBBBBk..',
     '..kbBBBBBWKBk.',
     '.kbBBBBBBBBBnk',
     'kBBBBBBBBBBBk.',
     'kTBBBBBBBBBbk.',
     '.kbBBBBBBBbk..',
     '..kFFkkFFFk...',
     '...kk..kkk....'],   // agachado
    ['..............',
     '..............',
     '..............',
     '.........k.k..',
     '........kEkEk.',
     '.......kEeEek.',
     '...kkkkBBBBBk.',
     '.kkbBBBBBBWKnk',
     'kTBBBBBBBBBBk.',
     '.kbBBBBBBBBbk.',
     'kFFkkkkkkFFk..',
     '.kk......kk...']   // no ar
  ], { B: '#26262e', b: '#44445a', E: '#26262e', e: '#8a6a78', W: '#ffffff', K: '#000000', n: '#c87890', T: '#3a3a48', F: '#3a3a48', k: '#0c0c12' });
  const COELHA_CARAMELO = S.quadros([
    ['.......k.k...',
     '......kEkEk..',
     '.....kJEeEJk.',
     '...kkJJJCCJJk',
     '..kLLJJCCKCnk',
     '.kLLCJJJCCCJk',
     'kTCCCCCJJJJk.',
     'kTCCCCCCCCCk.',
     '.kCCCCCCCCCk.',
     '..kFFkkFFFk..',
     '...kk..kkk...'],   // agachada (a jubinha em volta da cabeca)
    ['.............',
     '.............',
     '.............',
     '........k.k..',
     '.......kEkEk.',
     '......kJEeEJk',
     '.kkkkkJJCKCnk',
     'kTLLLLJJJCCk.',
     '.kCCCCCCCCJk.',
     'kFFkkkkkFFk..',
     '.kk.....kk...']   // no ar
  ], { C: '#d8a060', J: '#f4d09a', L: '#7a4a20', E: '#d8a060', e: '#ffb0b8', K: '#2a1408', n: '#e07890', T: '#f4e4c8', F: '#c08850', k: '#4a2a10' });
  // O branco na frente; a coelha e o preto logo atras, cada um num tempo
  // de pulo (fase) e com o seu pulo (alto).
  const TRIO_COELHOS = [{ sprites: COELHO_BRANCO, atras: 0, fase: 0, alto: 6 },
                        { sprites: COELHA_CARAMELO, atras: 23, fase: 15, alto: 5 },
                        { sprites: COELHO_PRETO, atras: 44, fase: 29, alto: 5.5 }];
  let coelhos = null;
  let esperaCoelho = 900 + sorteio() * 1200;

  function desenharCoelho(passo) {
    if (!coelhos) {
      esperaCoelho -= passo;
      if (esperaCoelho <= 0) {
        const dir = aleatorio() < 0.5 ? 1 : -1;
        const chao = H - 4 - Math.floor(aleatorio() * 4);
        coelhos = { dir: dir, bando: TRIO_COELHOS.map(function (c) {
          return { sprites: c.sprites, fase: c.fase, alto: c.alto, chao: chao,
                   x: dir === 1 ? -c.sprites[0].w - c.atras : W + 2 + c.atras };
        }) };
      }
      return;
    }
    const ciclo = 46;                                  // um pulo a cada ~0,8 s
    const dir = coelhos.dir;
    // De tras para a frente: o da frente fica por cima.
    for (let i = coelhos.bando.length - 1; i >= 0; i--) {
      const c = coelhos.bando[i];
      c.fase += passo;
      const p = (c.fase % ciclo) / ciclo;
      let quadro = c.sprites[0], altura = 0;
      if (p >= 0.3) {                                  // no ar
        quadro = c.sprites[1];
        altura = Math.sin(((p - 0.3) / 0.7) * Math.PI) * c.alto;
        c.x += dir * 0.9 * passo;
      }
      S.colar(ctx, quadro, c.x, c.chao - quadro.h - altura, dir);
    }
    if (coelhos.bando.every(function (c) { return dir === 1 ? c.x > W + 4 : c.x < -c.sprites[0].w - 4; })) {
      coelhos = null;
      esperaCoelho = 2000 + aleatorio() * 2400;
    }
  }

  // (A joaninha saiu em 12/10/2026, a pedido do Rafael: o chao do campo
  // ficou para os personagens de 16 bits que visitam.)

  // Sementes de dente-de-leao: vao com o vento
  const sementes = [];
  for (let i = 0; i < 7; i++) {
    sementes.push({ x: sorteio() * W, y: 10 + sorteio() * 60, vel: 0.08 + sorteio() * 0.08, fase: sorteio() * 6 });
  }

  function desenharSementes(passo) {
    ctx.fillStyle = 'rgba(255,255,255,0.9)';
    for (const s of sementes) {
      s.x += s.vel * vento * passo;
      s.y += Math.sin(t * 0.03 + s.fase) * 0.12 * passo - 0.01 * passo;
      if (s.x > W + 2) { s.x = -2; s.y = 20 + aleatorio() * 55; }
      if (s.y < 2) s.y = H - 10;
      ctx.fillRect(Math.round(s.x), Math.round(s.y), 1, 1);
      if ((Math.floor(t / 10) + Math.floor(s.fase * 3)) % 3 === 0) {
        ctx.fillRect(Math.round(s.x) - 1, Math.round(s.y) - 1, 1, 1);
      }
    }
  }

  // Balao de ar quente, raro e devagar, la no alto
  let balao = null;
  let esperaBalao = 2200 + sorteio() * 2600;

  function desenharBalao(passo) {
    if (!balao) {
      esperaBalao -= passo;
      if (esperaBalao <= 0) {
        balao = { x: -8, y: 8 + aleatorio() * 10, cor: aleatorio() < 0.5 ? '#ff5b5b' : '#5b8cff' };
      }
      return;
    }
    balao.x += 0.08 * vento * passo;
    const x = Math.round(balao.x), y = Math.round(balao.y + Math.sin(t * 0.02) * 1.5);
    ctx.fillStyle = balao.cor;
    ctx.fillRect(x - 2, y, 5, 4);
    ctx.fillRect(x - 1, y - 1, 3, 1);
    ctx.fillRect(x - 1, y + 4, 3, 1);
    ctx.fillStyle = '#ffe066';
    ctx.fillRect(x, y, 1, 5);
    ctx.fillStyle = '#6b4423';
    ctx.fillRect(x - 1, y + 7, 3, 2);
    ctx.fillStyle = 'rgba(60,40,20,0.7)';
    ctx.fillRect(x - 1, y + 5, 1, 2);
    ctx.fillRect(x + 1, y + 5, 1, 2);
    if (balao.x > W + 10) {
      balao = null;
      esperaBalao = 3600 + aleatorio() * 3600;
    }
  }

  // Sol com raios que giram devagar
  function desenharSol() {
    const cx = 138, cy = 12;
    ctx.fillStyle = '#fff3b0';
    ctx.fillRect(cx - 3, cy - 4, 7, 9);
    ctx.fillRect(cx - 4, cy - 3, 9, 7);
    ctx.fillStyle = '#ffe066';
    ctx.fillRect(cx - 2, cy - 3, 5, 7);
    ctx.fillRect(cx - 3, cy - 2, 7, 5);
    ctx.fillStyle = 'rgba(255,224,102,0.75)';
    for (let i = 0; i < 8; i++) {
      const a = t * 0.004 + i * Math.PI / 4;
      const r = 7 + (i % 2);
      ctx.fillRect(Math.round(cx + 0.5 + Math.cos(a) * r), Math.round(cy + 0.5 + Math.sin(a) * r), 1, 1);
    }
  }

  function desenharNuvens(passo) {
    for (const n of nuvens) {
      n.x += n.vel * vento * passo;
      if (n.x > W + 12) n.x = -14;
      ctx.fillStyle = 'rgba(255,255,255,0.92)';
      for (const p of n.forma) {
        ctx.fillRect(Math.round(n.x) + p[0] * n.escala, n.y + p[1] * n.escala, n.escala, n.escala);
      }
    }
  }

  function desenharGirassois() {
    for (const g of girassois) {
      const b = balanco(g);
      const topoX = g.baseX + b, topoY = g.baseY - g.haste;
      const meioX = g.baseX + b * 0.5, meioY = g.baseY - g.haste * 0.5;
      ctx.strokeStyle = '#3f7d2b';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(g.baseX, g.baseY);
      ctx.lineTo(meioX, meioY);
      ctx.lineTo(topoX, topoY);
      ctx.stroke();
      ctx.fillStyle = '#3f7d2b';
      ctx.fillRect(Math.round(meioX) - 2, Math.round(meioY), 2, 1);
      ctx.fillRect(Math.round(meioX) + 1, Math.round(meioY) - 2, 2, 1);
      const hx = Math.round(topoX), hy = Math.round(topoY - 2);
      ctx.fillStyle = '#f4c430';
      ctx.fillRect(hx - 2, hy - 1, 5, 1);
      ctx.fillRect(hx - 1, hy - 2, 3, 3);
      ctx.fillRect(hx - 2, hy, 5, 1);
      ctx.fillStyle = '#6b4423';
      ctx.fillRect(hx - 1, hy - 1, 3, 2);
    }
  }

  // ------------------------------------------------------------------
  // Visitas de jogos famosos de 8 e 16 bits (pedido do Rafael, 02/10/2026).
  // Uma de cada vez, a cada 20 a 35 s; a primeira e' o Mario.
  // ------------------------------------------------------------------
  const CHAO = H - 4;              // onde pisa quem anda na grama

  // Super Mario Bros. (NES, 1985): o Mario e o Luigi correm juntos e pulam
  // por cima do Goomba -- o Luigi pula mais alto, como no jogo. Pedido do
  // Rafael (20/10/2026): na medida do Yoshi e do Link (antes o Mario era
  // pequeno demais), o Luigi mais alto e mais magro que o Mario, e os dois
  // chegam logo depois do Yoshi (ver desenharVisitas). R e G a roupa, H
  // cabelo e sapato, S pele, K olho, M bigode, B macacao, Y botao.
  const MARIO = S.quadros([
    ['....kkkkk......',
     '...kRRRRRkkk...',
     '..kRRRRRRRRRk..',
     '..kHHHSSKSkk...',
     '.kHSHSSSKSSSk..',
     '.kHSHHSSSKSSSk.',
     '.kHHSSSSMMMMk..',
     '..kkSSSSSSSk...',
     '..kRRRBRRRkk...',
     '.kRRRRBBRRRSk..',
     'kSSRRBBYBBSSk..',
     'kSSkBBBBBBBk...',
     '.kkBBBBkBBBkk..',
     '.kHHHkk.kkHHHk.',
     'kHHHHk...kHHHHk',
     '.kkkk.....kkkk.'],   // andando (pernas abertas)
    ['....kkkkk......',
     '...kRRRRRkkk...',
     '..kRRRRRRRRRk..',
     '..kHHHSSKSkk...',
     '.kHSHSSSKSSSk..',
     '.kHSHHSSSKSSSk.',
     '.kHHSSSSMMMMk..',
     '..kkSSSSSSSk...',
     '...kRRBRRRk....',
     '..kRRRBBRRRk...',
     '..kRRBBYBBSk...',
     '..kSSBBBBBSk...',
     '...kBBBBBBk....',
     '...kHHHHHHk....',
     '..kHHHHkHHHk...',
     '...kkkk.kkk....'],   // andando (pernas juntas)
    ['...........kk..',
     '....kkkkk.kSSk.',
     '...kRRRRRkkSSk.',
     '..kRRRRRRRRRRk.',
     '..kHHHSSKSkRRk.',
     '.kHSHSSSKSSRRk.',
     '.kHSHHSSSKSRRk.',
     '.kHHSSSSMMMRRk.',
     '..kkSSSSSSRRk..',
     '.kRRRRBRRRBRk..',
     'kRRRRRBBBBBk...',
     'kSSkBBYBBYBk...',
     'kSSkBBBBBBBBk..',
     '.kkBBBkkkBBBk..',
     '.kHHHk...kHHHk.',
     '..kkk.....kkk..']   // pulo (o punho para o alto)
  ], { R: '#e02818', H: '#7a4010', S: '#ffb878', K: '#101010', M: '#4a2408', B: '#2848e8', Y: '#ffd23f', k: '#1a1622' });
  const LUIGI = S.quadros([
    ['....kkkkk......',
     '...kGGGGGkkk...',
     '..kGGGGGGGGGk..',
     '..kHHHSSKSkk...',
     '.kHSHSSSKSSSk..',
     '.kHSHSSSSKSSSk.',
     '.kHSHHSSSKSSSk.',
     '.kHHSSSSMMMMk..',
     '..kkSSSSSSSk...',
     '..kGGGBGGGkk...',
     '.kGGGGBBGGGSk..',
     'kSSGGBBYBBSSk..',
     'kSSkBBBBBBBk...',
     '.kkBBBBkBBBk...',
     '..kBBBk.kBBBk..',
     '.kHHHk...kHHHk.',
     'kHHHHk...kHHHHk',
     '.kkkk.....kkkk.'],   // andando (pernas abertas)
    ['....kkkkk......',
     '...kGGGGGkkk...',
     '..kGGGGGGGGGk..',
     '..kHHHSSKSkk...',
     '.kHSHSSSKSSSk..',
     '.kHSHSSSSKSSSk.',
     '.kHSHHSSSKSSSk.',
     '.kHHSSSSMMMMk..',
     '..kkSSSSSSSk...',
     '...kGGBGGGk....',
     '..kGGGBBGGGk...',
     '..kGGBBYBBSk...',
     '..kSSBBBBBSk...',
     '...kBBBBBBk....',
     '...kBBBBBBk....',
     '...kHHHHHHk....',
     '..kHHHHkHHHk...',
     '...kkkk.kkk....'],   // andando (pernas juntas)
    ['...........kk..',
     '....kkkkk.kSSk.',
     '...kGGGGGkkSSk.',
     '..kGGGGGGGGGGk.',
     '..kHHHSSKSkGGk.',
     '.kHSHSSSKSSGGk.',
     '.kHSHSSSSKSGGk.',
     '.kHSHHSSSKSGGk.',
     '.kHHSSSSMMMGGk.',
     '..kkSSSSSSGGk..',
     '.kGGGGBGGGBGk..',
     'kGGGGGBBBBBk...',
     'kSSkBBYBBYBk...',
     'kSSkBBBBBBBBk..',
     '.kkBBBkkkBBBk..',
     '..kBBBk.kBBBk..',
     '.kHHHk...kHHHk.',
     '..kkk.....kkk..']   // pulo (o punho para o alto)
  ], { G: '#2fae3a', H: '#7a4010', S: '#ffb878', K: '#101010', M: '#4a2408', B: '#2848e8', Y: '#ffd23f', k: '#1a1622' });
  const GOOMBA = S.quadros([
    ['.....kkkk.....',
     '...kkGGGGkk...',
     '..kGGGGGGGGk..',
     '.kGGKKGGKKGGk.',
     '.kGGWKGGKWGGk.',
     'kGGGWKGGKWGGGk',
     'kGGGGGGGGGGGGk',
     '.kgGGGGGGGGgk.',
     '..kkTTTTTTkk..',
     '..kTTTTTTTTk..',
     '.kBBBBkkBBBBk.',
     '..kkkk..kkkk..'],   // andando
    ['.....kkkk.....',
     '...kkGGGGkk...',
     '..kGGGGGGGGk..',
     '.kGGKKGGKKGGk.',
     '.kGGWKGGKWGGk.',
     'kGGGWKGGKWGGGk',
     'kGGGGGGGGGGGGk',
     '.kgGGGGGGGGgk.',
     '..kkTTTTTTkk..',
     '..kTTTTTTTTk..',
     '..kBBBkkBBBk..',
     '...kkk..kkk...']   // andando (o outro pe)
  ], { G: '#a0522d', g: '#7a3a1e', W: '#ffffff', K: '#101010', T: '#f2c38a', B: '#3b2412', k: '#2a160a' });

  function iniciarMario() {
    const dir = aleatorio() < 0.5 ? 1 : -1;
    const w = MARIO[0].w;
    // O Goomba entra primeiro; o Mario e o Luigi chegam correndo depois (o
    // encontro cai perto do meio do campo) e pulam quando chegam perto dele.
    return { dir: dir, goomba: dir === 1 ? W + 2 : -GOOMBA[0].w - 2, virou: false, susto: 0, desenhar: desenharMario,
             irmaos: [{ sprites: MARIO, x: dir === 1 ? -w - 90 : W + 90, altura: 0, vy: 0, noAr: false, pulo: 2.0 },
                      { sprites: LUIGI, x: dir === 1 ? -w - 110 : W + 110, altura: 0, vy: 0, noAr: false, pulo: 2.3 }] };
  }

  function desenharMario(passo) {
    // O Goomba anda devagar ao encontro deles; depois que os dois passam por
    // cima, ele da um pulinho de susto, vira e vai atras (sai mais depressa).
    const gw = GOOMBA[0].w;
    if (!this.virou && this.irmaos.every(function (irmao) {
      return this.dir === 1 ? irmao.x > this.goomba + gw : irmao.x + irmao.sprites[0].w < this.goomba;
    }, this)) { this.virou = true; this.susto = 1; }
    if (this.susto > 0) this.susto = Math.max(0, this.susto - passo / 16);
    this.goomba += (this.virou ? this.dir * 0.3 : -this.dir * 0.25) * passo * (this.susto > 0 ? 0 : 1);
    const pulinho = Math.round(Math.sin(this.susto * Math.PI) * 3);
    S.colar(ctx, GOOMBA[Math.floor(t / (this.virou ? 7 : 14)) % 2], this.goomba, CHAO - GOOMBA[0].h - pulinho,
            this.virou ? this.dir : -this.dir);
    let foram = true;
    for (const irmao of this.irmaos) {
      const w = irmao.sprites[0].w;
      // A distancia da frente dele ate o Goomba (negativa: ja esta por cima).
      const perto = this.dir === 1 ? this.goomba - (irmao.x + w) : irmao.x - (this.goomba + GOOMBA[0].w);
      if (!irmao.noAr && perto > -2 && perto < 6) { irmao.noAr = true; irmao.vy = irmao.pulo; }
      irmao.x += this.dir * (irmao.noAr ? 0.75 : 0.55) * passo;
      if (irmao.noAr) {
        irmao.altura += irmao.vy * passo;
        irmao.vy -= 0.11 * passo;
        if (irmao.altura <= 0) { irmao.altura = 0; irmao.noAr = false; }
      }
      const quadro = irmao.noAr ? irmao.sprites[2] : irmao.sprites[Math.floor(t / 5) % 2];
      S.colar(ctx, quadro, irmao.x, CHAO - quadro.h - irmao.altura, this.dir);
      if (this.dir === 1 ? irmao.x < W + 2 : irmao.x > -w - 2) foram = false;
    }
    const goombaFoi = this.virou ? (this.dir === 1 ? this.goomba > W + 2 : this.goomba < -gw - 2)
      : (this.dir === 1 ? this.goomba < -gw - 2 : this.goomba > W + 2);
    return !(foram && goombaFoi);
  }

  // Sonic the Hedgehog (Mega Drive, 1991): passa correndo, pula em bola e
  // pega o anel dourado no meio do campo. Pedido do Rafael (20/10/2026):
  // maior (antes era o menor do campo) e com o Tails correndo atras, que
  // no mesmo lugar sobe girando as caudas, como no Sonic 2.
  const SONIC = S.quadros([
    ['......kkkk......',
     '....kkBBBBkk....',
     '.kkkBBBBBBBBk...',
     'kBBBBBBBBBWWWk..',
     '.kbBBBBBBWWKWk..',
     '.kkBBBBBBWWKWSk.',
     'kbBBBBBBBSSSSSKk',
     '.kkBBBBBBBSSSkk.',
     '...kkBBBSSBBGGk.',
     '..kGGBBSSSBkkk..',
     '...kkkBSSBk.....',
     '...kkBBkkBBkkk..',
     '..kRRGRk.kRRGRk.',
     '.kRRRRk...kRRRRk',
     '..kkkk.....kkkk.'],   // correndo (pernas abertas)
    ['......kkkk......',
     '....kkBBBBkk....',
     '.kkkBBBBBBBBk...',
     'kBBBBBBBBBWWWk..',
     '.kbBBBBBBWWKWk..',
     '.kkBBBBBBWWKWSk.',
     'kbBBBBBBBSSSSSKk',
     '.kkBBBBBBBSSSkk.',
     '...kkBBBSSBkk...',
     '...kGBBSSSBGk...',
     '....kkBSSBkk....',
     '.....kBBBBk.....',
     '....kRRGRRk.....',
     '...kRRRRRRRk....',
     '....kkkkkkk.....']   // correndo (pernas juntas)
  ], { B: '#2251ff', b: '#1638b8', S: '#ffcc99', W: '#ffffff', K: '#101010', R: '#e8202a', G: '#f4f4f4', k: '#0c1640' });
  const SONIC_BOLA = S.quadros([
    ['.....kkkk.....',
     '...kkBBBBkk...',
     '..kBBBBBBBBk..',
     '.kBBLBBBBBBBk.',
     '.kBLBBBBBbBBk.',
     'kBBBBBBBBBBbBk',
     'kBLBBBbbBBBBBk',
     'kBBBBbbbbBBBBk',
     'kBbBBBBbBBBLBk',
     '.kBBbBBBBBLBk.',
     '.kBBBBBBBLBBk.',
     '..kBBBBBBBBk..',
     '...kkBBBBkk...',
     '.....kkkk.....'],   // a bola (o giro do pulo)
    ['.....kkkk.....',
     '...kkBBBBkk...',
     '..kBBBBBBBBk..',
     '.kBBBBBBBLBBk.',
     '.kBBbBBBBBLBk.',
     'kBbBBBBBBBBBBk',
     'kBBBBBbbBBBLBk',
     'kBBBBbbbbBBBBk',
     'kBLBBBBbBBBbBk',
     '.kBLBBBBBbBBk.',
     '.kBBLBBBBBBBk.',
     '..kBBBBBBBBk..',
     '...kkBBBBkk...',
     '.....kkkk.....']   // a bola, um quarto de volta
  ], { B: '#2251ff', b: '#1638b8', L: '#7fa6ff', k: '#0c1640' });
  const TAILS_CHAO = S.quadros([
    ['.........k..k..',
     '........kOkkOk.',
     '.......kOOOOOk.',
     '...k..kOOWWKOk.',
     '..kWk.kOOWWKWk.',
     '.kWOOkkOOWWWWNk',
     'kWOOOOkoOWWWkk.',
     '.kWOOOOOOWWk...',
     '..kOOWOOOWGk...',
     '...kOOkOOOkk...',
     '....kkkOOkOOk..',
     '.....kRGk.kRGk.',
     '....kRRRk.kRRRk',
     '.....kkk...kkk.'],   // correndo, as caudas para cima
    ['.........k..k..',
     '........kOkkOk.',
     '.......kOOOOOk.',
     '......kOOWWKOk.',
     '......kOOWWKWk.',
     '......kOOWWWWNk',
     '..kkkkkoOWWWkk.',
     '.kWOOOOOOWWk...',
     'kWOOOWOOOWGk...',
     '.kWOOOOOOOk....',
     '..kOOkkkOOk....',
     '...kk..kRGk....',
     '......kRRRRk...',
     '.......kkkk....']   // correndo, as caudas para baixo
  ], { O: '#f0a020', o: '#c87810', W: '#ffffff', K: '#1a3a8a', N: '#101010', R: '#e8202a', G: '#f4f4f4', k: '#3a1e06' });
  const ANEL = S.fazer(['.YYY.', 'Y...Y', 'Y...Y', 'Y...Y', '.YYY.'], { Y: '#ffd23f' });

  function iniciarSonic() {
    const dir = aleatorio() < 0.5 ? 1 : -1;
    const w = SONIC[0].w;
    return { dir: dir, x: dir === 1 ? -w : W + 2, altura: 0, vy: 0, noAr: false, pulouEm: null,
             tails: { x: dir === 1 ? -w - 22 : W + 24, altura: 0, vy: 0, noAr: false },
             anel: { x: 50 + aleatorio() * 60, pego: -1 }, poeira: [], desenhar: desenharSonic };
  }

  function desenharSonic(passo) {
    const w = SONIC[0].w;
    this.x += this.dir * 0.85 * passo;       // rapido, mas da para ver quem e'
    const ate = this.dir === 1 ? this.anel.x - (this.x + w / 2) : (this.x + w / 2) - this.anel.x;
    if (!this.noAr && this.anel.pego < 0 && ate > 0 && ate < 18) {
      this.noAr = true; this.vy = 1.9; this.pulouEm = this.x;
    }
    if (this.noAr) {
      this.altura += this.vy * passo;
      this.vy -= 0.13 * passo;
      if (this.altura <= 0) { this.altura = 0; this.noAr = false; }
    }
    if (this.anel.pego < 0 && Math.abs(this.x + w / 2 - this.anel.x - 2) < 5 && this.altura > 6) this.anel.pego = 0;
    // O Tails corre atras e, onde o Sonic pulou, sobe girando as caudas.
    const tails = this.tails;
    tails.x += this.dir * 0.85 * passo;
    if (!tails.noAr && this.pulouEm !== null && (this.dir === 1 ? tails.x >= this.pulouEm : tails.x <= this.pulouEm)) {
      tails.noAr = true; tails.vy = 1.5; this.pulouEm = null;
    }
    if (tails.noAr) {
      tails.altura += tails.vy * passo;
      tails.vy -= 0.09 * passo;
      if (tails.altura <= 0) { tails.altura = 0; tails.noAr = false; }
    }
    if (this.anel.pego < 0) {
      S.colar(ctx, ANEL, this.anel.x, CHAO - 26 + Math.round(Math.sin(t * 0.1)), 1);
    } else if (this.anel.pego < 30) {                 // brilhinho de anel pego
      this.anel.pego += passo;
      ctx.fillStyle = 'rgba(255,240,140,' + (1 - this.anel.pego / 30).toFixed(2) + ')';
      const r = 2 + this.anel.pego / 6;
      for (let i = 0; i < 6; i++) {
        const a = i * Math.PI / 3;
        ctx.fillRect(Math.round(this.anel.x + 2 + Math.cos(a) * r), Math.round(CHAO - 24 + Math.sin(a) * r), 1, 1);
      }
    }
    for (const corredor of [this, tails]) {
      if (passo && !corredor.noAr && aleatorio() < 0.5) {
        this.poeira.push({ x: corredor.x + (this.dir === 1 ? 1 : w - 2), y: CHAO - 1, vida: 1 });
      }
    }
    for (const p of this.poeira) { p.vida -= 0.05 * passo; p.y -= 0.05 * passo; }
    this.poeira = this.poeira.filter(function (p) { return p.vida > 0; });
    for (const p of this.poeira) {
      ctx.fillStyle = 'rgba(255,255,255,' + (p.vida * 0.6).toFixed(2) + ')';
      ctx.fillRect(Math.round(p.x), Math.round(p.y), 1, 1);
    }
    const qt = tails.noAr ? TAILS[Math.floor(t / 3) % 4] : TAILS_CHAO[Math.floor(t / 3) % 2];
    S.colar(ctx, qt, tails.x, CHAO - qt.h - tails.altura, this.dir);
    const quadro = this.noAr ? SONIC_BOLA[Math.floor(t / 2) % 2] : SONIC[Math.floor(t / 3) % 2];
    S.colar(ctx, quadro, this.x, CHAO - quadro.h - this.altura, this.dir);
    const fora = this.dir === 1 ? tails.x > W + 2 : tails.x < -w - 2;
    return !fora || this.poeira.length > 0;
  }

  // Duck Hunt (NES, 1984): dois patos sobem batendo as asas, e depois o
  // cachorro aparece no meio da grama dando risada.
  const PALETA_PATO = { W: '#e8d8b0', G: '#1f8f3a', K: '#000000', Y: '#f2b400', B: '#5a3a1a', n: '#ffffff' };
  const PATO = S.quadros([
    ['...WW.....', '..WWW...GG', '.WWW...GGKY', 'BBBBBBBnn.', 'BBBBBBBB..', '.BBBBB....'],
    ['..........', '.......GG.', '......GGKY', 'BBBBBBBnn.', 'BBWWWBBB..', '.WWWBB....', '..WW......']
  ], PALETA_PATO);
  const CACHORRO = S.quadros([
    ['LL....LL', 'LBBBBBBL', 'LBKBBKBL', '.BBWWBB.', '.BWKKWB.', '.BWrrWB.', '..BWWB..', '...BB...'],
    ['LL....LL', 'LBBBBBBL', 'LBKBBKBL', '.BBWWBB.', '.BWKKWB.', '.BWWWWB.', '..BWWB..', '...BB...']
  ], { L: '#6b3d1a', B: '#b07040', K: '#000000', W: '#f2e0c0', r: '#e8204a' });

  function iniciarDuckHunt() {
    const dir = aleatorio() < 0.5 ? 1 : -1;
    const x = dir === 1 ? 20 + aleatorio() * 30 : W - 50 - aleatorio() * 30;
    return { dir: dir, patos: [{ x: x, y: HORIZONTE }, { x: x - dir * 12, y: HORIZONTE + 8 }],
             cachorro: -1, cachorroX: 40 + aleatorio() * 80, desenhar: desenharDuckHunt };
  }

  function desenharDuckHunt(passo) {
    if (this.cachorro < 0) {
      for (const [i, p] of this.patos.entries()) {
        p.x += this.dir * 0.5 * passo;
        p.y -= 0.32 * passo;
        S.colar(ctx, PATO[Math.floor((t + i * 4) / 6) % 2], p.x, p.y + Math.sin(t * 0.1 + i) * 1.5, this.dir);
      }
      if (this.patos.every(function (p) { return p.y < -10 || p.x < -14 || p.x > W + 4; })) this.cachorro = 0;
      return true;
    }
    this.cachorro += passo;                           // sobe, ri e desce (uns 3 s)
    const subida = Math.min(1, this.cachorro / 20, (180 - this.cachorro) / 20);
    if (subida <= 0) return false;
    const quadro = CACHORRO[Math.floor(this.cachorro / 7) % 2];
    S.colar(ctx, quadro, this.cachorroX, CHAO + 2 - quadro.h * subida, 1);
    return true;
  }

  // Kirby (Kirby's Dream Land, Game Boy 1992): flutua estufado pelo ceu,
  // levado pela brisa.
  const KIRBY = S.fazer(['..ppppp..', '.ppppppp.', 'apKpppKpa', 'apKpppKpa', '.pcppppc.', '.ppppppp.',
                         '..ppppp..', '.rr...rr.'],
                        { p: '#ff9ccf', a: '#ff9ccf', K: '#1a1a3a', c: '#ff5c8a', r: '#e8204a' });

  function iniciarKirby() {
    const dir = aleatorio() < 0.5 ? 1 : -1;
    return { dir: dir, x: dir === 1 ? -10 : W + 2, base: 14 + aleatorio() * 16, desenhar: desenharKirby };
  }

  function desenharKirby(passo) {
    this.x += this.dir * 0.22 * vento * passo;
    S.colar(ctx, KIRBY, this.x, this.base + Math.sin(t * 0.04) * 3, this.dir);
    return this.dir === 1 ? this.x < W + 2 : this.x > -10;
  }

  // ------------------------------------------------------------------
  // Mais visitas de 16 bits (lote campo-a, 13/10/2026): Yoshi, Link,
  // o Wiggler, o Monty Mole e o Lakitu.
  // ------------------------------------------------------------------
  // Yoshi (Super Mario World, SNES, 1990): o arbusto das frutinhas fica
  // sempre no campo, com as frutinhas balancando como no jogo. O Yoshi verde
  // vem correndo pela grama e o roxo vem pelo ar, batendo as pernas (o pulo
  // flutuante do Yoshi); o roxo passa por cima do arbusto e pousa do outro
  // lado. Cada um estica a lingua, come a frutinha do seu lado e vai embora
  // feliz; depois que os dois saem, as frutinhas brotam de novo. Pedido do
  // Rafael (20/10/2026); logo depois chegam o Mario e o Luigi.
  // G verde (ou roxo), d escuro, W branco, K olho, R sela, O espinhos e botas.
  const DESENHO_YOSHI = [
    ['......kk........',        // correndo
     '.....kWWk.......',
     '....kWWKWkkk....',
     '...kOWWKWGGGkk..',
     '...kGWWWGGGGGGk.',
     '..kOGGGGGGGGGGGk',
     '..kGGGGGGGGGGGGk',
     '..kOGGGGddddGdk.',
     '..kGGGWWWGGGkk..',
     '.kGRRRGGWWkk....',
     'kGRWWRGGWWWk....',
     'kGRRRRGGWWGGk...',
     '.kGGGGGGWWGk....',
     'kGGdkdGGGGdk....',
     '.kkkOOOkkOOOk...',
     '....kkk..kkk....'],
    ['......kk........',        // correndo (e parado)
     '.....kWWk.......',
     '....kWWKWkkk....',
     '...kOWWKWGGGkk..',
     '...kGWWWGGGGGGk.',
     '..kOGGGGGGGGGGGk',
     '..kGGGGGGGGGGGGk',
     '..kOGGGGddddGdk.',
     '..kGGGWWWGGGkk..',
     '.kGRRRGGWWkk....',
     'kGRWWRGGWWWk....',
     'kGRRRRGGWWGGk...',
     '.kGGGGGGWWGk....',
     'kGGdkdGGGGdk....',
     '.kkkkOOOOOk.....',
     '.....kkkkk......'],
    ['......kk........',        // boca aberta: a lingua sai daqui
     '.....kWWk.......',
     '....kWWKWkkk....',
     '...kOWWKWGGGkk..',
     '...kGWWWGGGGGGk.',
     '..kOGGGGGGGGGGGk',
     '..kGGGGGGGGGGdk.',
     '..kOGGGGdkkkkk..',
     '..kGGGWWWGGGGk..',
     '.kGRRRGGWWkkk...',
     'kGRWWRGGWWWk....',
     'kGRRRRGGWWGGk...',
     '.kGGGGGGWWGk....',
     'kGGdkdGGGGdk....',
     '.kkkkOOOOOk.....',
     '.....kkkkk......'],
    ['................',        // mastigando de olho fechado
     '......kk........',
     '....kkGGkkkk....',
     '...kOGKKGGGGkk..',
     '...kGGGGGGGGGGk.',
     '..kOGGGGGGGGGGGk',
     '..kGGGGGGGGGGGGk',
     '..kOGGGWWdddddk.',
     '..kGGGWWWWGGGk..',
     '.kGRRRGGWWkkk...',
     'kGRWWRGGWWWk....',
     'kGRRRRGGWWGGk...',
     '.kGGGGGGWWGk....',
     'kGGdkdGGGGdk....',
     '.kkkkOOOOOk.....',
     '.....kkkkk......']
  ];
  const PALETA_YOSHI = { G: '#4cd640', d: '#219a34', W: '#ffffff', K: '#101010', R: '#ee3226', O: '#f68a1e',
                         k: '#0f3a16' };
  const PALETA_YOSHI_ROXO = { G: '#b070f0', d: '#7a3ac0', W: '#ffffff', K: '#101010', R: '#ee3226', O: '#f68a1e',
                              k: '#2a0f45' };
  const YOSHI = S.quadros(DESENHO_YOSHI, PALETA_YOSHI);
  const YOSHI_ROXO = S.quadros(DESENHO_YOSHI, PALETA_YOSHI_ROXO);
  const FRUTA_YOSHI = S.fazer([
    '.gl.',
    'RWRR',
    'RRRD',
    '.DD.'
  ], { l: '#4caf3a', R: '#ee2030', W: '#ffd6d6', D: '#a01020', g: '#2e7d1f' });
  const CORACAO_YOSHI = [[0, 0], [1, 0], [3, 0], [4, 0], [0, 1], [1, 1], [2, 1], [3, 1], [4, 1],
                         [1, 2], [2, 2], [3, 2], [2, 3]];
  const ARBUSTO_DESENHO = S.quadros([
    ['.......kkkkk..........',
     '....kkkGGGGGkk.kkk....',
     '...kGGGGGGGGGGkGGGk...',
     '..kGGGLLGGGGGGGGGGGk..',
     '.kGGLLGGGGGGGLLGGGGGk.',
     'kGGGGGGGGGGGLLGGGGGGGk',
     'kGGGGGdGGGGGGGGGdGGGGk',
     'kGdGGGGGGGdGGGGGGGGdGk',
     '.kGGdGGGGGGGGGdGGGGGk.',
     '..kddddddddddddddddk..',
     '...kkkkkkkkkkkkkkkk...']   // o arbusto das frutinhas (Super Mario World)
  ], { G: '#3cb043', L: '#7ed957', d: '#23802f', k: '#103a16' });
  const ARBUSTO_YOSHI = ARBUSTO_DESENHO[0];
  // O arbusto mora no campo: as duas frutinhas (onde ficam no arbusto e se
  // ja foram comidas) e quanto falta para cada uma brotar de novo (0 a 1).
  const arbusto = { x: 98, frutas: [{ dx: 3, dy: 1, fase: 0, comida: false, broto: 1 },
                                    { dx: 14, dy: 0, fase: 2.1, comida: false, broto: 1 }] };

  function desenharArbusto(passo) {
    const y = CHAO + 1 - ARBUSTO_YOSHI.h;
    S.colar(ctx, ARBUSTO_YOSHI, arbusto.x, y, 1);
    for (const f of arbusto.frutas) {
      if (f.comida) continue;
      if (f.broto < 1) f.broto = Math.min(1, f.broto + passo / 30);
      // A frutinha balanca no galho, de um lado para o outro (como no jogo).
      const fx = Math.round(arbusto.x + f.dx + Math.sin(t * 0.1 + f.fase) * 1.2), fy = y + f.dy - 2;
      if (f.broto >= 1) {
        S.colar(ctx, FRUTA_YOSHI, fx, fy, 1);
      } else {
        // Brotando: um pontinho que cresce, com um brilho em volta.
        const r = Math.max(1, Math.round(f.broto * 3));
        ctx.fillStyle = '#ee2030';
        ctx.fillRect(fx + 2 - Math.ceil(r / 2), fy + 2 - Math.ceil(r / 2), r, r);
        ctx.fillStyle = 'rgba(255,255,255,' + (1 - f.broto).toFixed(2) + ')';
        ctx.fillRect(fx - 1, fy, 1, 1);
        ctx.fillRect(fx + 4, fy + 1, 1, 1);
        ctx.fillRect(fx + 2, fy - 2, 1, 1);
      }
    }
  }

  // Onde fica a frutinha i agora (o meio dela, para a lingua alcancar).
  function frutaDoArbusto(i) {
    const f = arbusto.frutas[i];
    return { x: arbusto.x + f.dx + 2, y: CHAO + 1 - ARBUSTO_YOSHI.h + f.dy };
  }

  function iniciarYoshi() {
    const dir = aleatorio() < 0.5 ? 1 : -1;
    const w = YOSHI[0].w;
    // Se uma visita anterior foi cortada (os testes chamam outra no meio),
    // as frutinhas estao no arbusto de novo.
    for (const f of arbusto.frutas) { f.comida = false; f.broto = 1; }
    // Cada um come a frutinha do seu lado: o verde a de perto, o roxo a de
    // la (ele passa voando por cima do arbusto e pousa do outro lado).
    const perto = dir === 1 ? 0 : 1, longe = 1 - perto;
    const fp = frutaDoArbusto(perto), fl = frutaDoArbusto(longe);
    return { dir: dir, desenhar: desenharYoshi, poeira: [], brotar: false,
             yoshis: [
               { sprites: YOSHI, fruta: perto, x: dir === 1 ? -w : W, dir: dir, alvo: dir === 1 ? fp.x - 21 : fp.x + 21 - w,
                 fase: 'correndo', relogio: 0, altura: 0, lingua: 0, coracao: -1, espera: 0 },
               { sprites: YOSHI_ROXO, fruta: longe, x: dir === 1 ? -w - 30 : W + 30, dir: dir,
                 alvo: dir === 1 ? fl.x + 21 - w : fl.x - 21, fase: 'voando', relogio: 0, altura: 34, lingua: 0,
                 coracao: -1, espera: 0 }] };
  }

  function desenharYoshi(passo) {
    const w = YOSHI[0].w;
    for (const y of this.yoshis) {
      y.relogio += passo;
      const sprites = y.sprites;
      let quadro = sprites[1];
      const boca = y.dir === 1 ? y.x + 10 : y.x + w - 11;      // de onde a lingua sai
      const fruta = frutaDoArbusto(y.fruta);
      const alcance = Math.max(1, Math.abs(fruta.x - boca));
      if (y.fase === 'correndo') {
        // Ate o lugar de comer (sem passar dele) ou, depois de comer, embora.
        const falta = y.comeu ? y.dir * 99 : y.alvo - y.x;
        y.x += Math.sign(falta) * Math.min(Math.abs(falta), 0.6 * passo);
        quadro = sprites[Math.floor(t / 4) % 2];
        if (!y.comeu && Math.abs(y.alvo - y.x) < 0.01) { y.fase = 'parando'; y.relogio = 0; }
      } else if (y.fase === 'voando') {
        // O pulo flutuante: as pernas batendo, descendo devagar ate o lugar
        // do outro lado do arbusto.
        const falta = y.alvo - y.x;
        y.x += Math.sign(falta) * Math.min(Math.abs(falta), 0.7 * passo);
        const resta = Math.abs(y.alvo - y.x);
        y.altura = Math.min(y.altura, 6 + resta * 0.3) + Math.sin(t * 0.3) * 0.3;
        if (resta < 0.01) y.altura = Math.max(0, y.altura - 0.8 * passo);
        quadro = sprites[Math.floor(t / 2) % 2];
        if (passo && aleatorio() < 0.6) {
          this.poeira.push({ x: y.x + (y.dir === 1 ? 5 : w - 6) + aleatorio() * 4, y: CHAO - y.altura, vida: 1 });
        }
        if (resta < 0.01 && y.altura <= 0) {
          // Pousou: vira para o arbusto (a frutinha esta atras dele).
          y.altura = 0; y.dir = -y.dir; y.fase = 'parando'; y.relogio = 0;
        }
      } else if (y.fase === 'parando') {
        if (y.relogio >= 10) { y.fase = 'lingua'; y.relogio = 0; }
      } else if (y.fase === 'lingua') {
        quadro = sprites[2];
        const p = Math.min(1, y.relogio / 20);                    // estica e recolhe
        y.lingua = Math.max(1, Math.round(Math.sin(p * Math.PI) * alcance));
        if (p >= 0.5 && !arbusto.frutas[y.fruta].comida) arbusto.frutas[y.fruta].comida = true;
        if (p >= 1) { y.fase = 'mastigando'; y.relogio = 0; }
      } else if (y.fase === 'mastigando') {
        quadro = Math.floor(y.relogio / 6) % 2 === 0 ? sprites[3] : sprites[1];
        if (y.relogio >= 42) { y.coracao = 0; y.fase = 'pronto'; y.relogio = 0; }
      } else if (y.fase === 'pronto') {
        // Quem comeu primeiro espera o outro terminar.
        if (this.yoshis.every(function (o) { return o.fase === 'pronto'; })) {
          // O roxo vira de novo e os dois vao embora juntos, para o mesmo lado.
          for (const o of this.yoshis) { o.dir = this.dir; o.comeu = true; o.fase = 'correndo'; o.relogio = 0; }
        }
      }
      y.quadro = quadro;
      y.boca = boca;
    }
    // Poeira das botas e do pulo flutuante.
    for (const y of this.yoshis) {
      const dentro = y.dir === 1 ? y.x < W + 1 : y.x > -w - 1;
      if (passo && y.fase === 'correndo' && dentro && aleatorio() < 0.5) {
        this.poeira.push({ x: y.x + (y.dir === 1 ? 3 : w - 4), y: CHAO - 1, vida: 1 });
      }
    }
    for (const p of this.poeira) { p.vida -= 0.05 * passo; p.y -= 0.05 * passo; }
    this.poeira = this.poeira.filter(function (p) { return p.vida > 0; });
    for (const p of this.poeira) {
      ctx.fillStyle = 'rgba(255,255,255,' + (p.vida * 0.6).toFixed(2) + ')';
      ctx.fillRect(Math.round(p.x), Math.round(p.y), 1, 1);
    }
    for (const y of this.yoshis) {
      const topo = CHAO - w - y.altura;
      S.colar(ctx, y.quadro, y.x, topo, y.dir);
      // A lingua cor-de-rosa (ponta mais grossa), com a frutinha presa na volta.
      if (y.fase === 'lingua') {
        const ponta = y.dir === 1 ? y.boca + y.lingua - 1 : y.boca - y.lingua + 1;
        ctx.fillStyle = '#ff6a9a';
        ctx.fillRect(Math.round(y.dir === 1 ? y.boca : ponta), topo + 7, y.lingua, 1);
        ctx.fillRect(Math.round(y.dir === 1 ? ponta - 1 : ponta), topo + 7, 2, 2);
        if (arbusto.frutas[y.fruta].comida) S.colar(ctx, FRUTA_YOSHI, ponta - (y.dir === 1 ? 2 : 1), topo + 6, 1);
      }
      // Coracaozinho (que delicia!) subindo e sumindo.
      if (y.coracao >= 0 && y.coracao < 50) {
        y.coracao += passo;
        ctx.fillStyle = 'rgba(255,92,138,' + Math.max(0, 1 - y.coracao / 50).toFixed(2) + ')';
        const cx = Math.round(y.x + (y.dir === 1 ? 4 : w - 9)), cy = Math.round(topo - 4 - y.coracao / 8);
        for (const p of CORACAO_YOSHI) ctx.fillRect(cx + p[0], cy + p[1], 1, 1);
      }
    }
    const foram = this.yoshis.every(function (y) {
      return y.comeu && (y.dir === 1 ? y.x > W + 1 : y.x < -w - 1) && y.coracao >= 50;
    });
    if (!foram || this.poeira.length) return true;
    // Os dois foram embora: as frutinhas brotam de novo no arbusto.
    if (!this.brotar) {
      this.brotar = true;
      for (const f of arbusto.frutas) if (f.comida) { f.comida = false; f.broto = 0; }
    }
    return arbusto.frutas.some(function (f) { return f.broto < 1; });
  }

  // The Legend of Zelda: A Link to the Past (SNES, 1991): o Link vem
  // andando, corta um tufo de grama com a espada, acha uma rupia verde e
  // ergue a rupia sobre a cabeca, como quando abre um bau no jogo.
  // G verde, P cabelo, S pele, K olho, b cinto e botas, X e L escudo.
  const PALETA_LINK = { G: '#3cb043', P: '#f0809c', S: '#f8c890', K: '#203048', b: '#8a4a18', X: '#3f62d8',
                        L: '#bcd0ff', k: '#15301a' };
  const LINK = S.quadros([
    ['.....kkkk.....',        // andando
     '....kGGGGkk...',
     '...kGGGGGGGk..',
     '..kGGPPPPPPPk.',
     '.kGGPPSSKSSk..',
     'kGGkSPSSSSSSk.',
     'kGk.kPSSSSkk..',
     '.k.kGGGGXXXk..',
     '..kSGGGGXLXk..',
     '..kbbbbbXLXk..',
     '...kGGGGGXk...',
     '...kbbkbbk....',
     '..kbbbkbbbk...',
     '...kkk.kkk....'],
    ['.....kkkk.....',        // andando
     '....kGGGGkk...',
     '...kGGGGGGGk..',
     '..kGGPPPPPPPk.',
     '.kGGPPSSKSSk..',
     'kGGkSPSSSSSSk.',
     'kGk.kPSSSSkk..',
     '.k.kGGGGXXXk..',
     '..kSGGGGXLXk..',
     '..kbbbbbXLXk..',
     '...kGGGGGXk...',
     '....kbbbkk....',
     '...kbbbbk.....',
     '....kkkk......'],
    ['.....kkkk.....',        // golpe (a espada e' colada na mao)
     '....kGGGGkk...',
     '...kGGGGGGGk..',
     '..kGGPPPPPPPk.',
     '.kGGPPSSKSSk..',
     'kGGkSPSSSSSSk.',
     'kGkkkPSSSSkk..',
     '.kkXXGGGGkkk..',
     '..kXLGGGGSSSk.',
     '..kXLbbbbbkk..',
     '...kXGGGGk....',
     '...kbbkbbk....',
     '..kbbbkbbbk...',
     '...kkk.kkk....'],
    ['.k........k...',        // erguendo o que achou
     'kSk.kkkk.kSk..',
     'kGkkGGGGkkGk..',
     'kGkGGGGGGkGk..',
     'kGkPPPPPPkGk..',
     'kGkSKSSKSkGk..',
     'kGkSSSSSSkGk..',
     'kGGkSSSSkGGk..',
     '.kGGGGGGGGk...',
     '..kbbbbbbk....',
     '..kGGGGGGk....',
     '..kbbkkbbk....',
     '.kbbbkkbbbk...',
     '..kkk..kkk....']
  ], PALETA_LINK);
  const ESPADA_LINK = S.fazer([
    '.k.......',
    'kYkkkkkk.',
    'BYCWWWWWk',
    'kYkkkkkk.',
    '.k.......'
  ], { W: '#ffffff', C: '#a8b8d8', Y: '#f0c040', B: '#3f62d8', k: '#15301a' });
  const TUFO_LINK = S.quadros([
    ['.L...L..',        // inteiro
     '.kL.LkL.',
     'LkMLMkML',
     'kMMkMMMk',
     'kGMkGMGk',
     'kGGkGGGk'],
    ['........',        // cortado
     '........',
     '........',
     '........',
     'LkLMkLML',
     'kGGkGGGk']
  ], { k: '#173f12', G: '#2e8f2a', L: '#b4f070', M: '#5cc23c' });
  const RUPIA_LINK = S.fazer([
    '..k..',
    '.kLk.',
    'kLWGk',
    'kLGDk',
    'kGGDk',
    '.kDk.',
    '..k..'
  ], { k: '#0c3a14', W: '#ffffff', L: '#9cff9c', G: '#20c040', D: '#108030' });

  function iniciarLink() {
    const dir = aleatorio() < 0.5 ? 1 : -1;
    return { dir: dir, x: dir === 1 ? -LINK[0].w : W, fase: 'andando', relogio: 0,
             tufo: Math.round(58 + aleatorio() * 38), cortado: false, sumico: 1,
             folhas: [], rupia: null, desenhar: desenharLink };
  }

  function desenharLink(passo) {
    const w = LINK[0].w, topo = CHAO - LINK[0].h;
    let quadro = LINK[Math.floor(t / 7) % 2];
    this.relogio += passo;
    const r = this.rupia;
    if (this.fase === 'andando') {
      this.x += this.dir * 0.42 * passo;
      const ate = this.dir === 1 ? this.tufo - (this.x + w) : this.x - (this.tufo + TUFO_LINK[0].w);
      if (!this.cortado && ate <= 4) { this.fase = 'golpe'; this.relogio = 0; }
      if (r && r.parada && !r.pega) {
        const meio = this.x + w / 2, alvo = r.x + RUPIA_LINK.w / 2;
        if (this.dir === 1 ? meio >= alvo : meio <= alvo) { this.fase = 'item'; this.relogio = 0; r.pega = true; }
      }
      if (r && r.pega) this.sumico = Math.max(0, this.sumico - passo / 120);   // o toco some aos poucos
    } else if (this.fase === 'golpe') {
      quadro = this.relogio < 5 ? LINK[1] : LINK[2];                // prepara e golpeia
      if (this.relogio >= 7 && !this.cortado) {
        this.cortado = true;
        for (let i = 0; i < 8; i++) {                                  // pedacos de grama voando
          this.folhas.push({ x: this.tufo + 1 + aleatorio() * 6, y: CHAO - 5 + aleatorio() * 2,
                             vx: (aleatorio() - 0.5) * 0.9, vy: -0.7 - aleatorio() * 0.7, vida: 1 });
        }
        this.rupia = { x: this.tufo + 1.5, y: CHAO - 8, vy: -1.5, quiques: 0, parada: false, pega: false };
      }
      if (this.relogio >= 22) { this.fase = 'andando'; this.relogio = 0; }
    } else if (this.fase === 'item') {
      quadro = LINK[3];
      if (this.relogio >= 80) { this.fase = 'andando'; this.relogio = 0; }
    }
    // O tufo de grama (depois de cortado fica o toco, que some aos poucos).
    if (this.sumico > 0) {
      ctx.globalAlpha = this.sumico;
      S.colar(ctx, TUFO_LINK[this.cortado ? 1 : 0], this.tufo, CHAO - TUFO_LINK[0].h, 1);
      ctx.globalAlpha = 1;
    }
    for (const f of this.folhas) {
      f.vy += 0.06 * passo; f.x += f.vx * passo; f.y += f.vy * passo; f.vida -= 0.025 * passo;
    }
    this.folhas = this.folhas.filter(function (f) { return f.vida > 0 && f.y < CHAO; });
    this.folhas.forEach(function (f, i) {
      ctx.fillStyle = (i % 2 ? 'rgba(180,240,112,' : 'rgba(92,194,60,') + f.vida.toFixed(2) + ')';
      ctx.fillRect(Math.round(f.x), Math.round(f.y), 1, 1);
    });
    // A rupia pula do tufo, quica e fica brilhando na grama.
    if (r && !r.pega) {
      if (!r.parada) {
        r.vy += 0.12 * passo; r.y += r.vy * passo; r.x += this.dir * 0.12 * passo;
        if (r.y >= CHAO - RUPIA_LINK.h) {
          r.y = CHAO - RUPIA_LINK.h;
          // No maximo dois quiques: com o passo grande (o teste acelera 8x), a
          // gravidade de um quadro passava do limite e ela quicava para sempre.
          r.quiques++;
          if (r.vy > 0.7 && r.quiques < 3) r.vy = -r.vy * 0.4; else { r.vy = 0; r.parada = true; }
        }
      }
      S.colar(ctx, RUPIA_LINK, r.x, r.y, 1);
      if (Math.floor(t / 6) % 3 === 0) {
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(Math.round(r.x) + 2, Math.round(r.y) - 2, 1, 1);
      }
    }
    S.colar(ctx, quadro, this.x, topo, this.dir);
    if (quadro === LINK[2]) {
      // A espada na mao e o risco branco do golpe.
      const ex = this.dir === 1 ? this.x + 12 : this.x + w - 13 - (ESPADA_LINK.w - 1);
      S.colar(ctx, ESPADA_LINK, ex, topo + 6, this.dir);
      if (this.relogio < 13) {
        const ox = this.dir === 1 ? this.x + 8 : this.x + w - 9, oy = topo + 8;
        ctx.fillStyle = 'rgba(255,255,255,' + Math.max(0, 1 - (this.relogio - 5) / 8).toFixed(2) + ')';
        for (let a = -1.4; a <= 0.15; a += 0.22) {
          ctx.fillRect(Math.round(ox + this.dir * Math.cos(a) * 10), Math.round(oy + Math.sin(a) * 10), 1, 1);
        }
      }
    }
    if (this.fase === 'item') {
      // A rupia erguida entre as maos, com brilhinhos em volta.
      const rx = this.dir === 1 ? this.x + 3 : this.x + w - 3 - RUPIA_LINK.w, ry = topo - RUPIA_LINK.h + 1;
      S.colar(ctx, RUPIA_LINK, rx, ry, 1);
      ctx.fillStyle = 'rgba(255,255,255,0.9)';
      for (let i = 0; i < 4; i++) {
        const a = this.relogio * 0.12 + i * Math.PI / 2;
        ctx.fillRect(Math.round(rx + 2 + Math.cos(a) * 6), Math.round(ry + 3 + Math.sin(a) * 5), 1, 1);
      }
    }
    const fora = this.dir === 1 ? this.x > W + 1 : this.x < -w - 1;
    return !(fora && this.sumico <= 0 && !this.folhas.length);
  }

  // Wiggler (Super Mario World, SNES, 1990): a lagarta da florzinha na
  // cabeca passeia devagar pela grama, cada gomo no seu passo.
  // Y amarelo, y laranja, W brilho, K olho, f pes, P e g a flor.
  const PALETA_WIGGLER = { Y: '#ffc928', y: '#e8861a', W: '#fff4b8', K: '#1a1008', f: '#a84a14',
                           P: '#ff5f8f', g: '#2e8a2a', k: '#4a2208' };
  const CABECA_WIGGLER = S.quadros([
    ['......k.......',        // cabeca, passo 1
     '.....kPk......',
     '....kPWPk.....',
     '.....kPgk.....',
     '....kkkgk.....',
     '...kYYYYYk....',
     '..kYYYYYYYk...',
     '.kYYYYYKKYkk..',
     '.kYYYYYKKYYYk.',
     '.kYYYYYYYYYWYk',
     '.kyYYYYYYYYYYk',
     '..kyyYYYyYYYyk',
     '...kyyyykyyyk.',
     '...kfkkfkkkk..',
     '....k..k......'],
    ['.......k......',        // cabeca, passo 2
     '......kPk.....',
     '.....kPWPk....',
     '......kPk.....',
     '....kkkgk.....',
     '...kYYYYYk....',
     '..kYYYYYYYk...',
     '.kYYYYYKKYkk..',
     '.kYYYYYKKYYYk.',
     '.kYYYYYYYYYWYk',
     '.kyYYYYYYYYYYk',
     '..kyyYYYyYYYyk',
     '...kyyyykyyyk.',
     '....kffk.kkk..',
     '.....kk.......']
  ], PALETA_WIGGLER);
  const GOMO_WIGGLER = S.quadros([
    ['...kkk...',        // gomo, passo 1
     '..kYYYk..',
     '.kYYWYYk.',
     'kYYYYWYYk',
     'kYYYYYYYk',
     'kyYYYYYyk',
     '.kyyyyyk.',
     '.kfkkkfk.',
     '..k...k..'],
    ['...kkk...',        // gomo, passo 2
     '..kYYYk..',
     '.kYYWYYk.',
     'kYYYYWYYk',
     'kYYYYYYYk',
     'kyYYYYYyk',
     '.kyyyyyk.',
     '..kfkfk..',
     '...k.k...']
  ], PALETA_WIGGLER);

  function iniciarWiggler() {
    const dir = aleatorio() < 0.5 ? 1 : -1;
    return { dir: dir, x: dir === 1 ? -CABECA_WIGGLER[0].w : W, polen: [], desenhar: desenharWiggler };
  }

  function desenharWiggler(passo) {
    const cw = CABECA_WIGGLER[0].w, gw = GOMO_WIGGLER[0].w, gh = GOMO_WIGGLER[0].h;
    this.x += this.dir * 0.28 * passo;
    // Quatro gomos atras da cabeca, cada um sobe um ponto na sua vez.
    for (let i = 4; i >= 1; i--) {
      const gx = this.dir === 1 ? this.x + 1 - 6 * i : this.x + cw - 1 + 6 * i - gw;
      const sobe = Math.sin(t * 0.16 - i * 1.1) > 0.35 ? 1 : 0;
      S.colar(ctx, GOMO_WIGGLER[(Math.floor(t / 8) + i) % 2], gx, CHAO - gh - sobe, this.dir);
    }
    const sobe = Math.sin(t * 0.16) > 0.35 ? 1 : 0;
    const cy = CHAO - CABECA_WIGGLER[0].h - sobe;
    S.colar(ctx, CABECA_WIGGLER[Math.floor(t / 10) % 2], this.x, cy, this.dir);
    // Polen saindo da florzinha de vez em quando.
    if (passo && aleatorio() < 0.03 * passo) {
      this.polen.push({ x: this.x + (this.dir === 1 ? 6 : cw - 7), y: cy + 1, vida: 1 });
    }
    for (const p of this.polen) {
      p.vida -= 0.02 * passo; p.y -= 0.12 * passo; p.x += Math.sin(t * 0.1 + p.vida * 6) * 0.15 * passo;
    }
    this.polen = this.polen.filter(function (p) { return p.vida > 0; });
    for (const p of this.polen) {
      ctx.fillStyle = 'rgba(255,240,140,' + p.vida.toFixed(2) + ')';
      ctx.fillRect(Math.round(p.x), Math.round(p.y), 1, 1);
    }
    const rabo = this.dir === 1 ? this.x + 1 - 24 : this.x + cw - 1 + 24;    // ponta do ultimo gomo
    return this.dir === 1 ? rabo < W + 1 : rabo > -1;
  }

  // Monty Mole (Super Mario World, SNES, 1990): a terra treme, a toupeira
  // espia do buraco, olha para os dois lados, pula para fora e sai correndo.
  // B marrom, b pes, T focinho, W olho e unhas, K pupila e nariz, R bochecha.
  const PALETA_MONTY = { B: '#94582a', b: '#56300f', T: '#f2c88e', W: '#ffffff', K: '#141010', R: '#e88a7a',
                         k: '#2e1806' };
  const MONTY = S.quadros([
    ['............',        // espiando do buraco
     '............',
     '............',
     '............',
     '....kkkk....',
     '...kBBBBk...',
     '..kBBBBBBkk.',
     '.kBBTWWTWWBk',
     '.kBTTWKTWKTk',
     '.kBTTTTTTTTk',
     '..kkkkkkkkk.'],
    ['....kkkk....',        // pulando (pes encolhidos)
     '...kBBBBk...',
     '..kBBBBBBk..',
     '.kBBBBTWWTk.',
     '.kBBBBTWKTTk',
     'kBBBBTTTTTKk',
     'kBBBBBRTTTk.',
     '.kBBBBBBWWk.',
     '..kBBBBBkk..',
     '..kbbkbbk...',
     '...kk.kk....'],
    ['....kkkk....',        // correndo
     '...kBBBBk...',
     '..kBBBBBBk..',
     '.kBBBBTWWTk.',
     '.kBBBBTWKTTk',
     'kBBBBTTTTTKk',
     'kBBBBBRTTTk.',
     '.kBBBBBBWWk.',
     '.kBBBBBBkk..',
     'kbbkkkkbbk..',
     '.kk....kk...'],
    ['....kkkk....',        // correndo
     '...kBBBBk...',
     '..kBBBBBBk..',
     '.kBBBBTWWTk.',
     '.kBBBBTWKTTk',
     'kBBBBTTTTTKk',
     'kBBBBBRTTTk.',
     '.kBBBBBBWWk.',
     '.kBBBBBBkk..',
     '..kkbbbk....',
     '....kkk.....']
  ], PALETA_MONTY);
  const BURACO_MONTY = S.quadros([
    ['............',        // monte de terra
     '....dDDd....',
     '..dDDdddDd..',
     '.dddddDdddd.',
     'gdDdddddddDg'],
    ['............',        // buraco aberto
     '..d......d..',
     '.dDKKKKKKDd.',
     'dDKKKKKKKKDd',
     'gdddDddDdddg']
  ], { d: '#7a4a1e', D: '#a8743e', K: '#2a1606', g: '#3f8f2a' });

  function iniciarMonty() {
    const dir = aleatorio() < 0.5 ? 1 : -1;
    // o buraco fica do lado de onde ele vem: assim a corrida aparece inteira
    const buraco = Math.round(dir === 1 ? 22 + aleatorio() * 50 : W - 34 - aleatorio() * 50);
    return { dir: dir, buraco: buraco, x: buraco, fase: 'tremendo', relogio: 0, sumico: 1,
             terra: [], poeira: [], desenhar: desenharMonty };
  }

  function desenharMonty(passo) {
    const w = MONTY[0].w, h = MONTY[0].h;
    this.relogio += passo;
    const self = this;
    function terrinha(n, forca) {                     // torroes de terra pulando
      for (let i = 0; i < n; i++) {
        self.terra.push({ x: self.buraco + 2 + aleatorio() * 8, y: CHAO - 3,
                          vx: (aleatorio() - 0.5) * forca, vy: -0.5 - aleatorio() * forca, vida: 1 });
      }
    }
    // O monte tremendo, depois o buraco aberto (que some depois que ele vai).
    if (this.fase === 'tremendo') {
      S.colar(ctx, BURACO_MONTY[0], this.buraco + Math.floor(this.relogio / 3) % 2, CHAO - BURACO_MONTY[0].h, 1);
      if (passo && aleatorio() < 0.08 * passo) terrinha(1, 0.6);
      if (this.relogio >= 60) { this.fase = 'espiando'; this.relogio = 0; terrinha(5, 0.8); }
    } else if (this.sumico > 0) {
      ctx.globalAlpha = this.sumico;
      S.colar(ctx, BURACO_MONTY[1], this.buraco, CHAO - BURACO_MONTY[0].h, 1);
      ctx.globalAlpha = 1;
    }
    if (this.fase === 'espiando') {
      // olha para um lado, para o outro... e pula para onde vai correr
      const olhar = Math.floor(this.relogio / 18) % 2 === 0 ? -this.dir : this.dir;
      S.colar(ctx, MONTY[0], this.buraco, CHAO - h, olhar);
      ctx.fillStyle = '#7a4a1e';                     // a borda da frente do buraco
      ctx.fillRect(this.buraco + 1, CHAO - 1, BURACO_MONTY[0].w - 2, 1);
      if (this.relogio >= 72) { this.fase = 'salto'; this.relogio = 0; terrinha(12, 1.2); }
    } else if (this.fase === 'salto') {
      const p = Math.min(1, this.relogio / 32);
      this.x += this.dir * 0.55 * passo;
      S.colar(ctx, MONTY[1], this.x, CHAO - h - Math.sin(p * Math.PI) * 13, this.dir);
      if (p >= 1) { this.fase = 'correndo'; this.relogio = 0; }
    } else if (this.fase === 'correndo') {
      this.x += this.dir * 0.8 * passo;
      this.sumico = Math.max(0, this.sumico - passo / 150);
      S.colar(ctx, MONTY[2 + Math.floor(t / 3) % 2], this.x, CHAO - h, this.dir);
      const longe = this.dir === 1 ? this.x > W + 1 : this.x < -w - 1;
      if (passo && !longe && aleatorio() < 0.5) {
        this.poeira.push({ x: this.x + (this.dir === 1 ? 1 : w - 2), y: CHAO - 1, vida: 1 });
      }
    }
    for (const p of this.terra) {
      p.vy += 0.08 * passo; p.x += p.vx * passo; p.y += p.vy * passo; p.vida -= 0.02 * passo;
    }
    this.terra = this.terra.filter(function (p) { return p.vida > 0 && p.y < CHAO; });
    this.terra.forEach(function (p, i) {
      ctx.fillStyle = i % 2 ? '#7a4a1e' : '#a8743e';
      ctx.fillRect(Math.round(p.x), Math.round(p.y), 1, 1);
    });
    for (const p of this.poeira) { p.vida -= 0.05 * passo; p.y -= 0.05 * passo; }
    this.poeira = this.poeira.filter(function (p) { return p.vida > 0; });
    for (const p of this.poeira) {
      ctx.fillStyle = 'rgba(255,255,255,' + (p.vida * 0.6).toFixed(2) + ')';
      ctx.fillRect(Math.round(p.x), Math.round(p.y), 1, 1);
    }
    const fora = this.dir === 1 ? this.x > W + 1 : this.x < -w - 1;
    return !(this.fase === 'correndo' && fora && this.sumico <= 0 && !this.terra.length && !this.poeira.length);
  }

  // Lakitu (Super Mario World, SNES, 1990): cruza o ceu na nuvem sorridente
  // pescando com um cogumelo 1-UP na ponta da linha, como o Lakitu
  // pescador do jogo; no meio do caminho, da um puxao na vara.
  // Y pele, G e L casco, W nuvem e lentes, c sombra da nuvem, K preto, V vara.
  const PALETA_LAKITU = { Y: '#f8c838', G: '#2fa83a', L: '#8ce07c', W: '#ffffff', c: '#bcd6f2', K: '#18182a',
                          V: '#9a5a22', k: '#2c3a5c' };
  const LAKITU = S.quadros([
    ['.......kkkk......k.',        // nuvem 1
     '......kYYYYk....kVk',
     '....kkYYYYYYk..kVk.',
     '...kGGYKKKKYk.kVk..',
     '..kGLGKWWWWKYkVk...',
     '..kGGGKWWKWKYVYk...',
     '..kGLGYKKKKYVYYYk..',
     '..kGGGWYYYYYVYYk...',
     '..kGGGWYYYYYYYk....',
     '...kWWWWWWYWWkk....',
     '..kWWWWWWWWWWWWk...',
     '.kWWWKWWWWWKWWWWk..',
     '.kWWWKWWWWWKWWWWk..',
     '.kcWWWKKKKKWWWWck..',
     '..kccWWWWWWWWcck...',
     '...kccckkkccckk....',
     '....kkk...kkk......'],
    ['.......kkkk......k.',        // nuvem 2
     '......kYYYYk....kVk',
     '....kkYYYYYYk..kVk.',
     '...kGGYKKKKYk.kVk..',
     '..kGLGKWWWWKYkVk...',
     '..kGGGKWWKWKYVYk...',
     '..kGLGYKKKKYVYYYk..',
     '..kGGGWYYYYYVYYk...',
     '..kGGGWYYYYYYYk....',
     '..kWWWWWWYWWWkk....',
     '..kWWWWWWWWWWWWk...',
     '.kWWWKWWWWWKWWWWk..',
     '.kWWWKWWWWWKWWWWk..',
     '.kcWWWKKKKKWWWWck..',
     '..kccWWWWWWWWcck...',
     '...kkcckkcccckk....',
     '.....kk..kkkk......'],
    ['.......kkkk.....k..',        // puxando a vara
     '......kYYYYk...kVk.',
     '....kkYYYYYYk.kVk..',
     '...kGGYKKKKYk.kVk..',
     '..kGLGKWWWWKYkVk...',
     '..kGGGKWWKWKYVYk...',
     '..kGLGYKKKKYYVYYk..',
     '..kGGGWYYYYYYYYk...',
     '..kGGGWYYYYYYYk....',
     '...kWWWWWWYWWkk....',
     '..kWWWWWWWWWWWWk...',
     '.kWWWKWWWWWKWWWWk..',
     '.kWWWKWWWWWKWWWWk..',
     '.kcWWWKKKKKWWWWck..',
     '..kccWWWWWWWWcck...',
     '...kccckkkccckk....',
     '....kkk...kkk......']
  ], PALETA_LAKITU);
  const UMUP_LAKITU = S.fazer([
    '..kkkk..',
    '.kGWWGk.',
    'kGGWWGGk',
    'kWGGGGWk',
    'kkCKCKkk',
    '.kCCCCk.',
    '..kkkk..'
  ], { G: '#3cc848', W: '#ffffff', C: '#f8e8c0', K: '#18182a', k: '#1c4a24' });

  function iniciarLakitu() {
    const dir = aleatorio() < 0.5 ? 1 : -1;
    return { dir: dir, x: dir === 1 ? -LAKITU[0].w : W, base: 4 + aleatorio() * 7,
             ponto: W * (0.3 + aleatorio() * 0.4), puxao: -1, desenhar: desenharLakitu };
  }

  function desenharLakitu(passo) {
    const w = LAKITU[0].w;
    this.x += this.dir * 0.3 * passo;
    const y = Math.round(this.base + Math.sin(t * 0.05) * 2);
    const meio = this.x + w / 2;
    if (this.puxao === -1 && (this.dir === 1 ? meio >= this.ponto : meio <= this.ponto)) this.puxao = 0;
    let quadro = LAKITU[Math.floor(t / 16) % 2], linha = 22;
    if (this.puxao >= 0) {                                 // o puxao: sobe a linha e solta de novo
      this.puxao += passo;
      const p = Math.min(1, this.puxao / 40);
      if (p < 0.55) quadro = LAKITU[2];
      linha = 22 - Math.round(Math.sin(p * Math.PI) * 12);
      if (p >= 1) this.puxao = -2;
    }
    S.colar(ctx, quadro, this.x, y, this.dir);
    // A linha de pesca, balancando, e o 1-UP na ponta.
    const col = quadro === LAKITU[2] ? 16 : 17;              // coluna da ponta da vara
    const px = this.dir === 1 ? this.x + col : this.x + w - 1 - col, py = y + 1;
    const balanco = Math.sin(t * 0.045) * 2;
    ctx.fillStyle = 'rgba(40,40,70,0.7)';
    for (let k = 1; k <= linha; k++) ctx.fillRect(Math.round(px + balanco * k / linha), py + k, 1, 1);
    S.colar(ctx, UMUP_LAKITU, Math.round(px + balanco) - 3, py + linha + 1, 1);
    return this.dir === 1 ? this.x < W + 1 : this.x > -w - 1;
  }

  // Donkey Kong Country (SNES, 1994 a 1996): a turma dos Kongs passa em fila,
  // cada um com o seu golpe (pedido do Rafael, 20/10/2026). O Donkey Kong
  // anda na frente, sai rolando (pega a banana pelo caminho, como no jogo) e
  // depois sai correndo; o Diddy da a estrela e corre; a Dixie gira o rabo
  // de cavalo e bate com o cabelo, e corre; e o Kiddy, o bebe do DKC 3, rola
  // e corre atras. A estrela e a bola do Kiddy sao o mesmo desenho girado
  // de 90 em 90 graus (S.girar).
  const DONKEY = S.quadros([
    ['.......DD.....',
     '.....BBBD.....',
     '...BBLLLBBB...',
     '..BLLLBBDDDT..',
     '..BLLBBTTWKT..',
     '.BLLBBBTTTTTT.',
     '.BLDBBBBTTTTTT',
     '.BBDBBBBTKTTT.',
     '.BBBBBBBBTTTD.',
     '..BBBBBBRRBD..',
     '..BBBBBBRRDD..',
     '...DBBBRRYD...',
     '.....DDDRR....',
     '..............'],
    ['..............',
     '.....BBBB.....',
     '...BBLLLBBB...',
     '..BLLLDDBBBB..',
     '..BLLBBBBBBD..',
     '.BLLBBBBBBBBD.',
     '.BLBBBBBBBBBD.',
     '.BRBBBBBTTBBDD',
     '.RRRRBTTTTDBDD',
     '.RYRRTKTTWDD..',
     '..BBBTTTTKDD..',
     '...DBTTTTTT...',
     '.....DTTT.....',
     '.......T......'],
    ['..............',
     '....RRBBB.....',
     '...BYRRLBBB...',
     '..BLRRBBBBBB..',
     '..BLRRBBBBBD..',
     '.BTTTBBBBBBBD.',
     '.TTTKTBBBBDBD.',
     'TTTTTTBBBBDBD.',
     '.TTTTTTBBBBBD.',
     '..TKWTTBBBBD..',
     '..TDDDBBBBDD..',
     '...DBBBBBDD...',
     '.....DDDD.....',
     '.....DD.......'],
    ['......T.......',
     '.....TTTB.....',
     '...TTTTTTBB...',
     '..BDKTTTTBBB..',
     '..BDWTTKTRRYR.',
     'DDLDTTTTBRRRR.',
     'DBLBTTBBBBBRD.',
     '.BBBBBBBBBBBD.',
     '.BBBBBBBBBBBD.',
     '..BBBBBBBBBD..',
     '..BBBBDDBBDD..',
     '...DBBBBBDD...',
     '.....DDDD.....',
     '..............']
  ], { B: '#8a4a1e', L: '#b8743c', D: '#5a2a0e', T: '#f2c088', K: '#1a0e06', R: '#e02a2a',
     Y: '#ffd23f', W: '#ffffff' });
  const DONKEY_ANDA = S.quadros([
    ['.......kkk..........',
     '.....kkBBBkk........',
     '....kBBBBBBBk.......',
     '...kBBBBBBBBBk......',
     '...kBBBTTTTTTTk.....',
     '..kBBBTTWKTWKTk.....',
     '..kBBBBTTTTTTTTk....',
     '..kBBBBBTTTTTTTTk...',
     '.kBBBBBBTTKKKKTk....',
     'kBBBBBBBBTTTTTk.....',
     'kBBBLBBBRRRRBBBk....',
     'kBBLLBBBRYYRBBBBk...',
     '.kBBBBBBBRRBBBBBBk..',
     '..kBBBBBBBBBBkBBBBk.',
     '..kBBBBkBBBBk.kBBBk.',
     '.kBBBBk.kBBBBkkTTTk.',
     'kTTTTk...kTTTTkTTTk.',
     '.kkkk.....kkkk.kkk..'],   // andando (o braco da frente para a frente)
    ['.......kkk..........',
     '.....kkBBBkk........',
     '....kBBBBBBBk.......',
     '...kBBBBBBBBBk......',
     '...kBBBTTTTTTTk.....',
     '..kBBBTTWKTWKTk.....',
     '..kBBBBTTTTTTTTk....',
     '..kBBBBBTTTTTTTTk...',
     '.kBBBBBBTTKKKKTk....',
     'kBBBBBBBBTTTTTk.....',
     'kBBBLBBBRRRRBBBkk...',
     'kBBLLBBBRYYRBBBBBk..',
     '.kBBBBBBBRRBBBBBBBk.',
     '..kBBBBBBBBBBBkBBBk.',
     '...kBBBBBBBBkkkTTTk.',
     '....kBBBBBBk..kTTTk.',
     '...kTTTTTTTTk..kkk..',
     '....kkkkkkkk........']   // andando (o outro passo)
  ], { B: '#8a4a1e', L: '#b8743c', D: '#5a2a0e', T: '#f2c088', K: '#1a0e06', W: '#ffffff', R: '#e02a2a', Y: '#ffd23f', k: '#2a1206' });
  const DIDDY = S.quadros([
    ['.....kkkk......',
     '....kRRRRkk....',
     '...kRRRRRRRkk..',
     '...kRRRRRRRRRk.',
     '..kBBTTWKTkkk..',
     '..kBTTTTTTTk...',
     '..kkBTTTTTk....',
     '.kBkRRYRRBk....',
     'kBkkRRRRRBTk...',
     'kBkkRRRRRkk....',
     '.kBBBBkkBBk....',
     '..kkBBk.kBBk...',
     '..kTTk..kTTk...',
     '...kk....kk....'],   // correndo
    ['.....kkkk......',
     '....kRRRRkk....',
     '...kRRRRRRRkk..',
     '...kRRRRRRRRRk.',
     '..kBBTTWKTkkk..',
     '..kBTTTTTTTk...',
     '..kkBTTTTTk....',
     '.kBkRRYRRBk....',
     'kBkkRRRRRBTk...',
     'kBkkRRRRRkk....',
     '.kBBBkBBBk.....',
     '..kkkBBBk......',
     '....kTTTk......',
     '.....kkk.......'],   // correndo (o outro passo)
    ['...............',
     '...............',
     '.k...kkkk...k..',
     'kTk.kRRRRk.kTk.',
     'kBBkRRRRRRkBBk.',
     '.kBBRRRRRRBBk..',
     '..kBTTWKTBkk...',
     '...kTTTTTTk....',
     '...kRRYRRk.....',
     '...kRRRRRk.....',
     '..kBBkkkBBk....',
     '.kBBk...kBBk...',
     'kTTk.....kTTk..',
     '.kk.......kk...']   // a estrela (bracos e pernas abertos)
  ], { R: '#e02a2a', B: '#7a4018', T: '#f0b878', K: '#1a0e06', Y: '#ffd23f', W: '#ffffff', k: '#2a1206' });
  const DIXIE = S.quadros([
    ['.kk............',
     'kYYk...kkk.....',
     'kYYYkkkPPPk....',
     '.kYYbbPPPPPk...',
     '..kYYBBBBBPk...',
     '...kkBTTWKTk...',
     '....kBTTTTTTk..',
     '....kBBTTTTk...',
     '...kPPPPPBk....',
     '..kBBPPPPBBk...',
     '...kBBBBBBk....',
     '...kBBkkBBk....',
     '..kTTTkkTTTk...',
     '...kkk..kkk....'],   // correndo (o rabo de cavalo para tras)
    ['..kk...........',
     '.kYYk..kkk.....',
     'kYYYkkkPPPk....',
     '.kYYbbPPPPPk...',
     '..kYYBBBBBPk...',
     '...kkBTTWKTk...',
     '....kBTTTTTTk..',
     '....kBBTTTTk...',
     '...kPPPPPBk....',
     '..kBBPPPPBBk...',
     '...kBBBBBBk....',
     '....kBBBBk.....',
     '....kTTTTk.....',
     '.....kkkk......'],   // correndo (o outro passo)
    ['...............',
     '.......kkk.....',
     '.kkkkkkPPPkk...',
     'kYYYYbbPPPPPk..',
     'kyYYYYYBBBBPk..',
     '.kkkkkBTTWKTk..',
     '.....kBTTTTTTk.',
     '.....kBBTTTTk..',
     '....kPPPPPBk...',
     '...kBBPPPPBBk..',
     '....kBBBBBBk...',
     '....kBBkkBBk...',
     '...kTTTkkTTTk..',
     '....kkk..kkk...'],   // girando: o cabelo para um lado
    ['..................',
     '.......kkk........',
     '......kPPPkkkkkkk.',
     '.....kPPPPPbbYYYYk',
     '.....kBBBBBYYYYYyk',
     '.....kBTTWKTkkkkk.',
     '.....kBTTTTTTk....',
     '.....kBBTTTTk.....',
     '....kPPPPPBk......',
     '...kBBPPPPBBk.....',
     '....kBBBBBBk......',
     '....kBBkkBBk......',
     '...kTTTkkTTTk.....',
     '....kkk..kkk......']   // girando: o cabelo para o outro lado (a chicotada)
  ], { P: '#ff5fa8', p: '#d83a86', Y: '#ffd23f', y: '#e0a800', b: '#7fd0ff', B: '#a8643a', T: '#f2c898', K: '#1a0e06', W: '#ffffff', k: '#2a1206' });
  const KIDDY = S.quadros([
    ['.......kk.......',
     '.....kkBBkk.....',
     '...kkBBBBBBkk...',
     '..kBBBBBBBBBBk..',
     '.kBBBTTTTTTTBBk.',
     '.kBBTTWKTTWKTBk.',
     'kBBBTTTTTTTTTTTk',
     'kBBBTTKWWWWKTTk.',
     '.kBBBTTKKKKTTk..',
     '..kBBBTTTTTTk...',
     '.kCCCCCCCCCCk...',
     'kCCCCCcCCCCCCk..',
     'kTCCCCcCCCCCTk..',
     '.kCCCCCCCCCCk...',
     '.kCCCCkkCCCCk...',
     '.kTTTTkkTTTTk...',
     '..kkkk..kkkk....'],   // correndo
    ['.......kk.......',
     '.....kkBBkk.....',
     '...kkBBBBBBkk...',
     '..kBBBBBBBBBBk..',
     '.kBBBTTTTTTTBBk.',
     '.kBBTTWKTTWKTBk.',
     'kBBBTTTTTTTTTTTk',
     'kBBBTTKWWWWKTTk.',
     '.kBBBTTKKKKTTk..',
     '..kBBBTTTTTTk...',
     '.kCCCCCCCCCCk...',
     'kCCCCCcCCCCCCk..',
     'kCCCCCcCCCCCTk..',
     '.kCCCCCCCCCCk...',
     '..kCCCCCCCCk....',
     '..kTTTTTTTTk....',
     '...kkkkkkkk.....'],   // correndo (o outro passo)
    ['...............',
     '...............',
     '...............',
     '.....kkkkk.....',
     '...kkCCCCCkk...',
     '..kCCCCCCCCCk..',
     '.kCCcCCBBBCCCk.',
     '.kCcCCBTTTBCCk.',
     'kCCCCBTTWTTBCCk',
     'kCCCCBTTTTTBCCk',
     'kCCCCCBTKTBCCCk',
     'kCcCCCCBBBCCCCk',
     '.kCCcCCCCCCCCk.',
     '.kCCCCCCCCcCCk.',
     '..kCCCCCCCCCk..',
     '...kkCCCCCkk...',
     '.....kkkkk.....']   // a bola (rolando)
  ], { C: '#8ec8ff', c: '#5a98e0', B: '#9a5a2a', T: '#f2c088', K: '#1a0e06', W: '#ffffff', k: '#1e1430' });
  const ESTRELA_DIDDY = [0, 1, 2, 3].map(function (q) { return S.girar(DIDDY[2], q); });
  const BOLA_KIDDY = [0, 1, 2, 3].map(function (q) { return S.girar(KIDDY[2], q); });
  const BANANA_DKC = S.quadros([
    ['......b',
     '.....Yb',
     '....YYy',
     'Y..YYYy',
     'YYYYYy.',
     '.yyyy..'],
    ['.....b.',
     '....Yb.',
     '...YYy.',
     '..YYy..',
     '.YYyy..',
     '..yy...'],
    ['....b..',
     '....Y..',
     '...Yy..',
     '...Yy..',
     '...Yy..',
     '...y...']
  ], { Y: '#ffe14a', y: '#e0a800', b: '#6b4423' });
  // A banana gira: de frente, de lado, de costas (o espelho) e de volta.
  const GIRO_BANANA = [[0, 1], [1, 1], [2, 1], [1, -1], [0, -1], [1, -1], [2, -1], [1, 1]];

  // Cada Kong: onde comeca (atras do da frente), onde faz o golpe (contado
  // da borda por onde entrou) e quanto o golpe anda.
  const TURMA_KONG = [
    { nome: 'donkey', atras: 20, golpe: 30 },
    { nome: 'diddy', atras: 45, golpe: 55 },
    { nome: 'dixie', atras: 66, golpe: 75 },
    { nome: 'kiddy', atras: 120, golpe: 60 }
  ];

  function iniciarDonkey() {
    const dir = aleatorio() < 0.5 ? 1 : -1;
    return { dir: dir, desenhar: desenharDonkey, poeira: [], faiscas: [],
             banana: { x: 62 + aleatorio() * 20, pega: -1 },
             kongs: TURMA_KONG.map(function (k) {
               return { nome: k.nome, golpe: k.golpe, fase: 'chegando', relogio: 0, altura: 0,
                        x: dir === 1 ? -k.atras : W + k.atras - 14 };
             }) };
  }

  // Quanto o Kong ja entrou no campo, a partir da borda de onde veio.
  function entrou(visita, k) {
    return visita.dir === 1 ? k.x : W - k.x;
  }

  function desenharDonkey(passo) {
    const dir = this.dir;
    for (const k of this.kongs) {
      k.relogio += passo;
      let vel = 0.5;
      if (k.fase === 'chegando' && entrou(this, k) >= k.golpe) { k.fase = 'golpe'; k.relogio = 0; }
      if (k.nome === 'donkey') {
        // Anda devagar, rola depressa por uns 60 pontos e sai correndo.
        if (k.fase === 'chegando') { vel = 0.4; k.quadro = DONKEY_ANDA[Math.floor(t / 8) % 2]; }
        else if (k.fase === 'golpe') {
          vel = 1.0;
          k.giro = (k.giro || 0) + passo;
          k.quadro = DONKEY[Math.floor(k.giro / 9) % 4];
          if (passo && aleatorio() < 0.5) {
            this.poeira.push({ x: k.x + (dir === 1 ? 3 : 10), y: CHAO - 1 - Math.floor(aleatorio() * 2), vida: 1 });
          }
          if (k.relogio >= 60) { k.fase = 'saindo'; k.relogio = 0; }
        } else { vel = 0.95; k.quadro = DONKEY_ANDA[Math.floor(t / 4) % 2]; }
      } else if (k.nome === 'diddy') {
        // A estrela: duas voltas inteiras de lado, de maos e pes no chao.
        if (k.fase === 'golpe') {
          vel = 0.7;
          k.quadro = ESTRELA_DIDDY[Math.floor(k.relogio / 8) % 4];
          if (k.relogio >= 64) { k.fase = 'saindo'; k.relogio = 0; }
        } else {
          vel = k.fase === 'saindo' ? 0.9 : 0.5;
          k.quadro = DIDDY[Math.floor(t / (k.fase === 'saindo' ? 3 : 4)) % 2];
        }
      } else if (k.nome === 'dixie') {
        // Gira o rabo de cavalo tres vezes no lugar e da a chicotada.
        if (k.fase === 'golpe') {
          vel = 0;
          const chicote = k.relogio >= 36;
          k.quadro = chicote ? DIXIE[3] : DIXIE[2 + Math.floor(k.relogio / 3) % 2];
          if (chicote && !k.bateu) {
            k.bateu = true;
            const ponta = dir === 1 ? k.x + DIXIE[3].w + 1 : k.x - 2;
            for (let i = 0; i < 6; i++) {
              const a = i * Math.PI / 3;
              this.faiscas.push({ x: ponta, y: CHAO - 12, vx: Math.cos(a) * 0.4, vy: Math.sin(a) * 0.4, vida: 1 });
            }
          }
          if (k.relogio >= 50) { k.fase = 'saindo'; k.relogio = 0; }
        } else {
          vel = k.fase === 'saindo' ? 0.9 : 0.5;
          k.quadro = DIXIE[Math.floor(t / (k.fase === 'saindo' ? 3 : 4)) % 2];
        }
      } else {
        // O Kiddy rola, como o Donkey, e depois corre atras dos outros.
        if (k.fase === 'golpe') {
          vel = 0.9;
          k.quadro = BOLA_KIDDY[Math.floor(k.relogio / 5) % 4];
          if (k.relogio >= 60) { k.fase = 'saindo'; k.relogio = 0; }
        } else {
          vel = k.fase === 'saindo' ? 0.85 : 0.5;
          k.quadro = KIDDY[Math.floor(t / (k.fase === 'saindo' ? 3 : 5)) % 2];
        }
      }
      k.x += dir * vel * passo;
    }
    // A banana gira no ar; o Donkey a pega rolando por ela.
    const banana = this.banana, dk = this.kongs[0];
    if (banana.pega < 0 && dk.fase === 'golpe' && Math.abs(dk.x + 7 - banana.x - 3) < 6) banana.pega = 0;
    if (banana.pega < 0) {
      const g = GIRO_BANANA[Math.floor(t / 5) % 8];
      S.colar(ctx, BANANA_DKC[g[0]], banana.x, CHAO - 12 + Math.round(Math.sin(t * 0.08)), g[1]);
    } else if (banana.pega < 24) {                    // estrelinha onde estava a banana
      banana.pega += passo;
      const r = 1 + Math.floor(banana.pega / 6), x = Math.round(banana.x + 3), y = CHAO - 10;
      ctx.fillStyle = 'rgba(255,240,140,' + Math.max(0, 1 - banana.pega / 24).toFixed(2) + ')';
      ctx.fillRect(x, y, 1, 1);
      ctx.fillRect(x - r, y, 1, 1);
      ctx.fillRect(x + r, y, 1, 1);
      ctx.fillRect(x, y - r, 1, 1);
      ctx.fillRect(x, y + r, 1, 1);
    }
    // Poeira do rolamento e faiscas da chicotada da Dixie.
    for (const p of this.poeira) { p.vida -= 0.06 * passo; p.y -= 0.04 * passo; }
    this.poeira = this.poeira.filter(function (p) { return p.vida > 0; });
    for (const p of this.poeira) {
      ctx.fillStyle = 'rgba(232,212,160,' + (p.vida * 0.7).toFixed(2) + ')';
      ctx.fillRect(Math.round(p.x), Math.round(p.y), 1, 1);
    }
    for (const f of this.faiscas) { f.vida -= 0.05 * passo; f.x += f.vx * passo; f.y += f.vy * passo; }
    this.faiscas = this.faiscas.filter(function (f) { return f.vida > 0; });
    for (const f of this.faiscas) {
      ctx.fillStyle = 'rgba(255,230,120,' + f.vida.toFixed(2) + ')';
      ctx.fillRect(Math.round(f.x), Math.round(f.y), 1, 1);
    }
    // De tras para a frente: o da frente fica por cima.
    for (let i = this.kongs.length - 1; i >= 0; i--) {
      const k = this.kongs[i];
      S.colar(ctx, k.quadro, k.x, CHAO - k.quadro.h, dir);
    }
    const foram = this.kongs.every(function (k) { return dir === 1 ? k.x > W + 2 : k.x < -22; });
    return !foram || this.poeira.length > 0 || this.faiscas.length > 0;
  }

  // Sonic the Hedgehog 2 (Mega Drive, 1992): o Tails cruza o ceu voando, as
  // duas caudas girando por cima da cabeca como a helice de um helicoptero.
  const TAILS = S.quadros([
    ['..............',
     'WOOOOOoOOOOOW.',
     '.ooooo.ooooo..',
     '....O...O.....',
     '....OO.OO.....',
     '...OOOOOOOOO..',
     '..OOOOOOWWO...',
     '..oOOOOOWKO...',
     '...oOOOOOOWWK.',
     '....oOOWWWWW..',
     '.....WWOOOO...',
     '.....OOOOW....',
     '.....O..O.....',
     '....RR..RR....'],
    ['..wwwwwwwww...',
     '..WOOOoOOOW...',
     '..wooo.ooow...',
     '....O...O.....',
     '....OO.OO.....',
     '...OOOOOOOOO..',
     '..OOOOOOWWO...',
     '..oOOOOOWKO...',
     '...oOOOOOOWWK.',
     '....oOOWWWWW..',
     '.....WWOOOO...',
     '.....OOOOW....',
     '.....O..O.....',
     '....RR..RR....'],
    ['..wwwwwwwww...',
     'w....OoO....w.',
     '.www.ooo.www..',
     '....O...O.....',
     '....OO.OO.....',
     '...OOOOOOOOO..',
     '..OOOOOOWWO...',
     '..oOOOOOWKO...',
     '...oOOOOOOWWK.',
     '....oOOWWWWW..',
     '.....WWOOOO...',
     '.....OOOOW....',
     '.....O..O.....',
     '....RR..RR....'],
    ['..wwwwwwwww...',
     '..WOOOoOOOW...',
     '..wooo.ooow...',
     '....O...O.....',
     '....OO.OO.....',
     '...OOOOOOOOO..',
     '..OOOOOOWWO...',
     '..oOOOOOWKO...',
     '...oOOOOOOWWK.',
     '....oOOWWWWW..',
     '.....WWOOOO...',
     '.....OOOOW....',
     '.....O..O.....',
     '....RR..RR....']
  ], { O: '#ffa630', o: '#d06a18', W: '#ffffff', K: '#1c2a6e', R: '#e8202a',
     w: 'rgba(255,255,255,0.5)' });

  function iniciarTails() {
    const dir = aleatorio() < 0.5 ? 1 : -1;
    return { dir: dir, x: dir === 1 ? -14 : W + 2, base: 12 + aleatorio() * 14, fase: aleatorio() * 6,
             ar: [], desenhar: desenharTails };
  }

  function desenharTails(passo) {
    this.x += this.dir * 0.5 * passo;
    const y = this.base + Math.sin(t * 0.04 + this.fase) * 5;
    const dentro = this.dir === 1 ? this.x < W + 2 : this.x > -14;
    // Ventinho que sai das pontas das caudas e fica para tras.
    if (passo && dentro && aleatorio() < 0.5) {
      this.ar.push({ x: this.x + (aleatorio() < 0.5 ? 0 : 12), y: y + 1, vida: 1 });
    }
    for (const a of this.ar) { a.vida -= 0.06 * passo; a.x -= this.dir * 0.3 * passo; a.y += 0.05 * passo; }
    this.ar = this.ar.filter(function (a) { return a.vida > 0; });
    for (const a of this.ar) {
      ctx.fillStyle = 'rgba(255,255,255,' + (a.vida * 0.7).toFixed(2) + ')';
      ctx.fillRect(Math.round(a.x), Math.round(a.y), 1, 1);
    }
    // Um quadro da helice por quadro desenhado (20 por segundo): gira rapido.
    S.colar(ctx, TAILS[Math.floor(t / 3) % 4], this.x, y, this.dir);
    return dentro || this.ar.length > 0;
  }

  // Sonic & Knuckles (Mega Drive, 1994): o Knuckles chega planando de bracos
  // abertos, pousa de barriga e desliza na grama, levanta, pula e sai
  // planando de novo.
  const KNUCKLES = S.quadros([
    ['...................',
     '...................',
     '...................',
     '...................',
     '...................',
     'rr..........RRR....',
     '..rrrr....RRRRRR.WW',
     'rrr..rrrRRRRRRKRWWW',
     '...rrrrRRRRRRRMMww.',
     'GG..RRRRRRRRRMMMM..',
     'GGYRRRRRRRRRRRMM...',
     '....RRRRR....RRWW..',
     '.............WWWw..'],
    ['...................',
     '...................',
     '...................',
     '...................',
     '...................',
     '.r..........RRR....',
     'rrrrrr....RRRRRR.WW',
     '...rrrrrRRRRRRKRWWW',
     '.rrr.rrRRRRRRRMMww.',
     '....RRRRRRRRRMMMM..',
     'GGYRRRRRRRRRRRMM...',
     'GG..RRRR.....RRWW..',
     '.............WWWw..'],
    ['...................',
     '...................',
     '...................',
     '...................',
     '...................',
     '...........RRR.....',
     '.........rRRRRR....',
     '........rrRRRRKM...',
     '.......rrrRRRRMMM..',
     '.......rr.RWWRMM...',
     '........WWRRWRRWW..',
     '.........RRRRRRWW..',
     '.......GGYR...RGGY.'],
    ['...................',
     '...........RRR.....',
     '.........rRRRRR....',
     '........rrRRRRKM...',
     '.......rrrRRRRMMM..',
     '.......rr.RRRMMM...',
     '.......r..RWWRR....',
     '..........RRWRRWW..',
     '.........WWRRRRWW..',
     '..........RRRR.....',
     '..........RR.RR....',
     '..........RR.RR....',
     '.........GGY.GGY...']
  ], { R: '#e2242e', r: '#9e1626', M: '#ffc89a', W: '#ffffff', w: '#c8c8d8', K: '#6a2c9a',
     G: '#28a844', Y: '#ffd23f' });

  function iniciarKnuckles() {
    const dir = aleatorio() < 0.5 ? 1 : -1;
    // Entra la no ceu (acima dos morros) e desce devagar ate a grama.
    return { dir: dir, x: dir === 1 ? -19 : W + 1, altura: 36 + aleatorio() * 10, vel: 0, vy: 0,
             estado: 'chegando', tempo: 0, poeira: [], desenhar: desenharKnuckles };
  }

  function desenharKnuckles(passo) {
    this.tempo += passo;
    let quadro = KNUCKLES[Math.floor(t / 6) % 2];        // planando: as mechas balancam
    if (this.estado === 'chegando') {
      this.x += this.dir * 0.8 * passo;
      this.altura -= 0.34 * passo;
      if (this.altura <= 0) { this.altura = 0; this.estado = 'deslizando'; this.vel = 0.8; }
    } else if (this.estado === 'deslizando') {           // de barriga na grama
      this.x += this.dir * this.vel * passo;
      this.vel -= 0.025 * passo;
      quadro = KNUCKLES[0];
      if (passo && aleatorio() < 0.7) {
        this.poeira.push({ x: this.x + (this.dir === 1 ? 13 : 5), y: CHAO - 1 - Math.floor(aleatorio() * 3), vida: 1 });
      }
      if (this.vel <= 0) { this.estado = 'agachado'; this.tempo = 0; }
    } else if (this.estado === 'agachado') {
      quadro = KNUCKLES[2];
      if (this.tempo > 15) { this.estado = 'em pe'; this.tempo = 0; }
    } else if (this.estado === 'em pe') {
      quadro = KNUCKLES[3];
      if (this.tempo > 50) { this.estado = 'impulso'; this.tempo = 0; }
    } else if (this.estado === 'impulso') {              // agacha para tomar impulso
      quadro = KNUCKLES[2];
      if (this.tempo > 8) { this.estado = 'pulando'; this.vy = 2.2; }
    } else if (this.estado === 'pulando') {
      quadro = KNUCKLES[3];
      this.x += this.dir * 0.4 * passo;
      this.altura += this.vy * passo;
      this.vy -= 0.1 * passo;
      if (this.vy <= 0.2) this.estado = 'saindo';
    } else {                                             // 'saindo': plana ate sumir
      this.x += this.dir * 0.85 * passo;
      this.altura = Math.max(0, this.altura - 0.12 * passo);
    }
    for (const p of this.poeira) { p.vida -= 0.05 * passo; p.y -= 0.05 * passo; }
    this.poeira = this.poeira.filter(function (p) { return p.vida > 0; });
    for (const p of this.poeira) {
      ctx.fillStyle = 'rgba(255,255,255,' + (p.vida * 0.6).toFixed(2) + ')';
      ctx.fillRect(Math.round(p.x), Math.round(p.y), 1, 1);
    }
    S.colar(ctx, quadro, this.x, CHAO - quadro.h - this.altura, this.dir);
    return this.dir === 1 ? this.x < W + 2 : this.x > -21;
  }

  // Final Fantasy VI (SNES, 1994): um Chocobo passa correndo, levantando
  // poeira, e solta uma pena amarela que cai devagar com o vento.
  const CHOCOBO = S.quadros([
    ['........yy......',
     '.......yyYYY....',
     '......yyYYYYY...',
     '........yYYYKY..',
     '.........YYYYOOO',
     '........YYYY.Oo.',
     '.......YYYY.....',
     'y.....YYYY......',
     'yy...YYYYY......',
     '.yyyYYLLLYY.....',
     '..YyYLLLLYYY....',
     '..YYYyyyyYYY....',
     '...YYYyyYYY.....',
     '....YYYYYY......',
     '.....Y...Y......',
     '....O.....O.....',
     '...O.......O....',
     '..Oo........Oo..'],
    ['........yy......',
     '.......yyYYY....',
     '......yyYYYYY...',
     '........yYYYKY..',
     '.........YYYYOOO',
     '........YYYY.Oo.',
     '.......YYYY.....',
     'y.....YYYY......',
     'yy...YYYYY......',
     '.yyyYYLLLYY.....',
     '..YyYLLLLYYY....',
     '..YYYyyyyYYY....',
     '...YYYyyYYY.....',
     '....YYYYYY......',
     '......YY........',
     '.......O.O......',
     '......O..OOO....',
     '.....Oo.........']
  ], { Y: '#ffd23f', y: '#d89a1c', L: '#fff07a', O: '#ff8c1a', o: '#c86010', K: '#1a1a1a' });

  function iniciarChocobo() {
    const dir = aleatorio() < 0.5 ? 1 : -1;
    return { dir: dir, x: dir === 1 ? -16 : W + 2, passada: 0, poeira: [],
             pena: null, soltar: 40 + aleatorio() * 60, desenhar: desenharChocobo };
  }

  function desenharChocobo(passo) {
    this.x += this.dir * 0.8 * passo;                    // rapido, mas da para ver quem e'
    this.passada += passo;
    const q = Math.floor(this.passada / 5) % 2;          // passada aberta / pernas passando
    const dentro = this.dir === 1 ? this.x < W + 2 : this.x > -16;
    if (passo && dentro && aleatorio() < 0.45) {
      this.poeira.push({ x: this.x + (this.dir === 1 ? 3 : 12), y: CHAO - 1, vida: 1 });
    }
    for (const p of this.poeira) { p.vida -= 0.06 * passo; p.y -= 0.04 * passo; }
    this.poeira = this.poeira.filter(function (p) { return p.vida > 0; });
    for (const p of this.poeira) {
      ctx.fillStyle = 'rgba(255,255,255,' + (p.vida * 0.6).toFixed(2) + ')';
      ctx.fillRect(Math.round(p.x), Math.round(p.y), 1, 1);
    }
    // Uma pena so, que cai balancando; no chao, some aos poucos.
    this.soltar -= passo;
    if (this.soltar <= 0 && dentro) {
      this.pena = { x: this.x + (this.dir === 1 ? 1 : 14), y: CHAO - 10, vida: 1, fase: aleatorio() * 6 };
      this.soltar = Infinity;
    }
    if (this.pena) {
      const p = this.pena;
      const balanco = Math.sin(t * 0.08 + p.fase);
      if (p.y < CHAO - 2) {
        p.y += 0.12 * passo;
        p.x += (balanco * 0.35 + 0.06 * vento) * passo;
      } else {
        p.vida -= 0.02 * passo;
      }
      if (p.vida <= 0) {
        this.pena = null;
      } else {
        const px = Math.round(p.x), py = Math.round(p.y);
        ctx.fillStyle = 'rgba(255,210,63,' + p.vida.toFixed(2) + ')';
        ctx.fillRect(px, py, 2, 1);
        ctx.fillStyle = 'rgba(216,154,28,' + p.vida.toFixed(2) + ')';
        ctx.fillRect(balanco > 0 ? px + 2 : px - 1, py - 1, 1, 1);
      }
    }
    S.colar(ctx, CHOCOBO[q], this.x, CHAO - 18 - q, this.dir);   // sobe 1 ponto a cada passada
    return dentro || this.poeira.length > 0 || !!this.pena;
  }

  // Secret of Mana (SNES, 1993): dois ou tres Rabites, os coelhinhos-monstro,
  // atravessam o campo aos pulos, cada um no seu ritmo.
  const RABITE = S.quadros([
    ['..........',
     '...Yp.Yp..',
     '...Yp.Yp..',
     '...Yp.Yp..',
     '..YYYYYY..',
     '.YYYYYKKY.',
     'WYYYYYKWYY',
     'WYYYYYYYYY',
     '.YYYYYmmmY',
     '.YYYYYYWYY',
     '..yyyyyy..'],
    ['Yp........',
     '.Yp.Yp....',
     '..YYpYp...',
     '...YYYYY..',
     '..YYYYKKY.',
     '.YYYYYKWYY',
     'WYYYYYYYYY',
     'WYYYYYmmmY',
     '.YYYYYYWYY',
     '..yyyyyy..',
     '..........'],
    ['..........',
     '..........',
     '..........',
     '...Yp..Yp.',
     '...YY.YY..',
     '.YYYYYKKY.',
     'YYYYYYKWYY',
     'WYYYYYYYYY',
     'WYYYYYmmmY',
     '.YYYYYYWYY',
     '.yyyyyyyy.']
  ], { Y: '#ffe066', y: '#e0a830', W: '#ffffff', K: '#2a1a10', p: '#ff9cae', m: '#5a1a10' });

  function iniciarRabites() {
    const dir = aleatorio() < 0.5 ? 1 : -1;
    const n = 2 + Math.floor(aleatorio() * 2);
    const bando = [];
    for (let i = 0; i < n; i++) {
      bando.push({ x: (dir === 1 ? -12 : W + 2) - dir * i * 17, fase: i * 11 + aleatorio() * 8,
                   alto: 6 + aleatorio() * 5, caiu: false });
    }
    return { dir: dir, bando: bando, poeira: [], desenhar: desenharRabites };
  }

  function desenharRabites(passo) {
    const ciclo = 42;                                    // um pulo a cada ~0,7 s
    let algum = false;
    for (const r of this.bando) {
      r.fase += passo;
      const p = (r.fase % ciclo) / ciclo;
      let quadro = RABITE[0], altura = 0;
      if (p >= 0.2 && p < 0.85) {                        // no ar
        quadro = RABITE[1];
        altura = Math.sin(((p - 0.2) / 0.65) * Math.PI) * r.alto;
        r.x += this.dir * passo;
        r.caiu = false;
      } else if (p >= 0.85) {                            // amassa ao cair, com poeirinha
        quadro = RABITE[2];
        if (!r.caiu && passo) {
          r.caiu = true;
          this.poeira.push({ x: r.x, y: CHAO - 1, vx: -0.15, vida: 1 },
                           { x: r.x + 9, y: CHAO - 1, vx: 0.15, vida: 1 });
        }
      }
      S.colar(ctx, quadro, r.x, CHAO - quadro.h - altura, this.dir);
      if (this.dir === 1 ? r.x < W + 2 : r.x > -12) algum = true;
    }
    for (const p of this.poeira) { p.vida -= 0.07 * passo; p.x += p.vx * passo; }
    this.poeira = this.poeira.filter(function (p) { return p.vida > 0; });
    for (const p of this.poeira) {
      ctx.fillStyle = 'rgba(255,255,255,' + (p.vida * 0.7).toFixed(2) + ')';
      ctx.fillRect(Math.round(p.x), Math.round(p.y), 1, 1);
    }
    return algum || this.poeira.length > 0;
  }

  // EarthBound (SNES, 1994): o Mr. Saturn atravessa o campo bem devagar, com
  // o lacinho na cabeca; no meio do caminho para, da um pulinho ("boing!") e
  // solta um coracao.
  const SATURNO = S.quadros([
    ['...RR.RR..',
     '...RRrRR..',
     '...RR.RR..',
     '.....K....',
     '....K.....',
     '..CCCKCC..',
     '.CCCCCCCC.',
     'CCCCCKCKC.',
     'CCCCCCCNNN',
     'CCCCCCNNNN',
     'CCCCCCCNN.',
     '.cccccccc.',
     '..c....c..'],
    ['...RR.RR..',
     '...RRrRR..',
     '...RR.RR..',
     '.....K....',
     '....K.....',
     '..CCCKCC..',
     '.CCCCCCCC.',
     'CCCCCKCKC.',
     'CCCCCCCNNN',
     'CCCCCCNNNN',
     'CCCCCCCNN.',
     '.cccccccc.',
     '...c..c...']
  ], { C: '#f6ead0', c: '#dccbaa', N: '#f4a890', K: '#1a1a1a', R: '#e8202a', r: '#a8141c' });
  const CORACAO_SATURNO = [[0, 0], [2, 0], [0, 1], [1, 1], [2, 1], [1, 2]];

  function iniciarSaturno() {
    const dir = aleatorio() < 0.5 ? 1 : -1;
    return { dir: dir, x: dir === 1 ? -11 : W + 1, passos: 0, andado: 0, ate: 60 + aleatorio() * 50,
             parado: -1, coracao: null, deuCoracao: false, desenhar: desenharSaturno };
  }

  function desenharSaturno(passo) {
    let quadro = SATURNO[0], altura = 0;
    if (this.parado < 0) {                               // andando, passinho a passinho
      this.x += this.dir * 0.3 * passo;
      this.andado += 0.3 * passo;
      this.passos += passo;
      const q = Math.floor(this.passos / 10) % 2;
      quadro = SATURNO[q];
      altura = q;                                        // sobe e desce a cada passo
      if (this.ate > 0 && this.andado >= this.ate) { this.parado = 0; this.ate = 0; }
    } else {                                             // parado: pulinho e coracao
      this.parado += passo;
      if (this.parado < 24) altura = Math.sin((this.parado / 24) * Math.PI) * 4;
      if (!this.deuCoracao && this.parado >= 12) {
        this.deuCoracao = true;
        this.coracao = { x: this.x + (this.dir === 1 ? 5 : 2), y: CHAO - 17, vida: 1 };
      }
      if (this.parado >= 70) this.parado = -1;
    }
    if (this.coracao) {
      const c = this.coracao;
      c.y -= 0.15 * passo;
      c.vida -= 0.012 * passo;
      if (c.vida <= 0) {
        this.coracao = null;
      } else {
        ctx.fillStyle = 'rgba(255,107,154,' + c.vida.toFixed(2) + ')';
        const cx = Math.round(c.x + Math.sin(t * 0.1) * 0.6), cy = Math.round(c.y);
        for (const p of CORACAO_SATURNO) ctx.fillRect(cx + p[0], cy + p[1], 1, 1);
      }
    }
    S.colar(ctx, quadro, this.x, CHAO - quadro.h - altura, this.dir);
    const dentro = this.dir === 1 ? this.x < W + 1 : this.x > -11;
    return dentro || !!this.coracao;
  }

  // Street Fighter II (SNES 1992): o Ryu e o Ken treinando juntos (pedido do
  // Rafael, 20/10/2026; antes era o Ryu sozinho, pequeno perto do Link).
  // Cada um entra por um lado e para de frente para o outro. Os dois soltam
  // o Hadouken ao mesmo tempo -- o do Ryu azul, o do Ken de fogo -- e as
  // bolas se anulam no meio, como no jogo. Depois vem o Shoryuken de cada um
  // (o do Ken com o punho em chamas), o Tatsumaki Senpukyaku dos dois (o
  // chute girando no ar) e, no fim, os dois vao embora andando juntos.
  // Os dois tem o MESMO desenho, com paletas diferentes: no Ken, a faixa da
  // testa (h) vira cabelo loiro e as pontas dela (f) somem.
  // k contorno, H cabelo, h faixa, f pontas da faixa, S pele, s sombra da
  // pele, E olho, W quimono, g dobra do quimono, B faixa da cintura, R luva.
  const PALETA_RYU = { k: '#1a1622', H: '#4a2c18', h: '#e8202a', f: '#e8202a', S: '#f2b880', s: '#c8875a',
                       E: '#101010', W: '#ffffff', g: '#c4c8d4', B: '#2a2a2a', R: '#c81e1e' };
  const PALETA_KEN = { k: '#1a1622', H: '#f2c43a', h: '#f2c43a', S: '#f2b880', s: '#c8875a',
                       E: '#101010', W: '#e8302a', g: '#a81c18', B: '#2a2a2a', R: '#4a3a30' };
  const LUTADOR = [
    ['......kkkk........',      // 0 guarda
     '.....kHHHHk.......',
     '...fkhhhhhhk......',
     '..f.kHSSSESk......',
     '.f..kHSSSSSSk.....',
     '.....kSssSSk......',
     '....kWkSSkWWk.....',
     '...kWWWkkWWWWkk...',
     '..kWWgWWWWWWWRRk..',
     '..kWgWWWWWkkkRRk..',
     '..kgWWWRRk...kk...',
     '...kWWWRRk........',
     '...kBBBBBBk.......',
     '..kWWWgWWWWk......',
     '..kWWgk.kWWWk.....',
     '.kWWgk...kWWWk....',
     '.kWWk.....kWWk....',
     'kSSk......kSSSk...',
     'kkkk.......kkkk...'],
    ['......kkkk........',      // 1 andando (pernas abertas)
     '.....kHHHHk.......',
     '...fkhhhhhhk......',
     '..f.kHSSSESk......',
     '.f..kHSSSSSSk.....',
     '.....kSssSSk......',
     '....kWkSSkWWk.....',
     '...kWWWkkWWWk.....',
     '...kWgWWWWWWkk....',
     '...kWgWWWWkRRk....',
     '...kgWWWWWkRRk....',
     '....kWWWWWkkk.....',
     '....kBBBBBk.......',
     '...kWWWgWWWk......',
     '..kWWgk.kWWWk.....',
     '..kWWk...kWWk.....',
     '.kWWk.....kWWk....',
     'kSSk......kSSSk...',
     'kkk........kkkk...'],
    ['......kkkk........',      // 2 andando (pernas juntas)
     '.....kHHHHk.......',
     '...fkhhhhhhk......',
     '..f.kHSSSESk......',
     '.f..kHSSSSSSk.....',
     '.....kSssSSk......',
     '....kWkSSkWWk.....',
     '...kWWWkkWWWk.....',
     '...kWgWWWWWWkk....',
     '...kWgWWWWkRRk....',
     '...kgWWWWWkRRk....',
     '....kWWWWWkkk.....',
     '....kBBBBBk.......',
     '....kWWgWWk.......',
     '....kWWgWWk.......',
     '....kWWkWWk.......',
     '....kWWkWWk.......',
     '...kSSSkSSSk......',
     '...kkkkkkkkk......'],
    ['.......kkkk.........',    // 3 Hadouken: as maos juntas, atras
     '......kHHHHk........',
     '....fkhhhhhhk.......',
     '...f.kHSSSESk.......',
     '..f..kHSSSSSSk......',
     '......kSssSSk.......',
     '.....kWkSSkWk.......',
     '....kWWWkkWWWk......',
     '..kkWWWWWWWWWk......',
     '.kRRkWgWWWWWk.......',
     '.kRRRkWWWWWk........',
     '..kkkWWWWWWk........',
     '....kBBBBBBk........',
     '...kWWWgWWWWk.......',
     '..kWWWk.kWWWWk......',
     '.kWWgk...kWWWWk.....',
     'kWWk.......kWWk.....',
     'kSSk.......kSSSk....',
     'kkkk........kkkk....'],
    ['.....kkkk...........',    // 4 Hadouken: solta, os bracos esticados
     '....kHHHHk..........',
     '..fkhhhhhhk.........',
     '.f.kHSSSESk.........',
     'f..kHSSSSSSk........',
     '....kSssSSk.........',
     '...kWkSSkWWkkkkkk...',
     '..kWWWkkWWWWWWWRRk..',
     '..kWgWWWWWWWWWWRRRk.',
     '..kWgWWWWWkkkkkRRk..',
     '..kgWWWWWk....kkk...',
     '...kWWWWWk..........',
     '...kBBBBBBk.........',
     '..kWWWgWWWWk........',
     '.kWWWk..kWWWk.......',
     'kWWgk....kWWWk......',
     'kWWk......kWWWk.....',
     'kSSk.......kSSSk....',
     'kkkk........kkkkk...'],
    ['......kkkk....',          // 5 agachado (antes e depois do Shoryuken)
     '.....kHHHHk...',
     '...fkhhhhhhk..',
     '..f.kHSSSESk..',
     '.f..kHSSSSSSk.',
     '.....kSssSSk..',
     '...kkWkSSkWk..',
     '..kWWWWkkWWWk.',
     '..kWgWWWWWkRRk',
     '..kgWWWWWWkRRk',
     '..kWWWWWWkkkk.',
     '..kBBBBBBBk...',
     '.kWWWWgWWWWk..',
     'kWWWWk.kWWWWk.',
     'kSSSk...kSSSk.',
     'kkkk.....kkkk.'],
    ['.........kk...',          // 6 Shoryuken: o punho para o alto
     '........kRRk..',
     '........kRRk..',
     '........kWWk..',
     '.......kWWk...',
     '..kkkk.kWWk...',
     '.kHHHHkWWk....',
     'fkhhhhhkWk....',
     '.kHSSSESkk....',
     '.kHSSSSSSk....',
     '..kSssSSk.....',
     '.kWWkSSkWk....',
     'kWWWWkkWWWk...',
     'kRRkWgWWWWk...',
     'kRRkWWWWWk....',
     '.kkkBBBBBk....',
     '...kWWWWWWk...',
     '...kWWWWWWWk..',
     '...kWWk.kWWk..',
     '..kWWk..kSSk..',
     '..kSSk...kk...',
     '..kkk.........'],
    ['......kkkk............',  // 7 Tatsumaki: a perna esticada
     '.....kHHHHk...........',
     '...fkhhhhhhk..........',
     '..f.kHSSSESk..........',
     '.f..kHSSSSSSk.........',
     '.....kSssSSk..........',
     '..kkkWkSSkWWkkk.......',
     '.kRRWWWkkWWWWRRk......',
     '..kkWWgWWWWWkkk.......',
     '....kWgWWWWk..........',
     '....kBBBBBBkkkkkkkkk..',
     '....kWWWgWWWWWWWWWWSSk',
     '....kWWgWWWWWWWWWWWSSk',
     '...kWWWk.kkkkkkkkkkkk.',
     '...kWWk...............',
     '..kSSk................',
     '..kkk.................'],
    ['......kkkk......',        // 8 Tatsumaki: de frente, no meio do giro
     '.....kHHHHk.....',
     '....khhhhhhk....',
     '....kSESSESk....',
     '....kSSSSSSk....',
     '.....kSssSk.....',
     '.kkkkWkSSkWkkkk.',
     'kRRWWWWkkWWWWRRk',
     '.kkkWWWWWWWWkkk.',
     '....kWWgWWWk....',
     '....kBBBBBBk....',
     '...kWWWWWWWWk...',
     '...kWWWkkWWWk...',
     '...kWWk..kWWk...',
     '....kSSkkSSk....',
     '....kkk..kkk....']
  ];
  const RYU = S.quadros(LUTADOR, PALETA_RYU);
  const KEN = S.quadros(LUTADOR, PALETA_KEN);
  // O meio do corpo em cada quadro (a coluna), para o lutador nao pular de
  // lugar ao trocar de quadro nem ao virar.
  const MEIO_LUTADOR = [7, 7, 7, 8, 6, 7, 5, 8, 7.5];
  // O Hadouken do Ryu (azul) e o do Ken (de fogo), com a cabeca a direita.
  const BOLA_RYU = S.quadros([
    ['......cCCc..', '..c..cCWWCc.', '.cCccCWWWWCc', 'cCCCCWWWWWWC', '.cCccCWWWWCc', '..c..cCWWCc.', '......cCCc..'],
    ['......cCCc..', '...c.cCWWCc.', '..cCcCWWWWCc', '.cCCCWWWWWWC', 'cCccCCWWWWCc', '.....cCWWCc.', '......cCCc..']
  ], { c: '#2f6bff', C: '#7fb0ff', W: '#ffffff' });
  const BOLA_KEN = S.quadros([
    ['.....c.cc...', '..c.cCcCCc..', '.cC.cCWWWCc.', 'cCCcCWWwwWCc', '.cCCCWWwWWCc', '..ccCCWWWCc.', '....c.cCc...'],
    ['....c..cc...', '.c..cCcCCc..', '..cCcCWWWCc.', '.cCCCWWwwWCc', 'cCcCCWWwWWCc', '...cCCWWWCc.', '.....ccCc...']
  ], { c: '#c81e00', C: '#ff7a1a', W: '#ffd23f', w: '#fff6c0' });

  function iniciarRyu() {
    // x de cada lutador e' o meio do corpo.
    const ryu = 36 + Math.round(aleatorio() * 10);
    return { fase: 'chegando', relogio: 0, saida: aleatorio() < 0.5 ? 1 : -1, proxima: 'hadouken',
             ryu: { x: -12, marca: ryu, dir: 1, altura: 0, quadro: 1, giro: 0 },
             ken: { x: W + 12, marca: ryu + 72, dir: -1, altura: 0, quadro: 1, giro: 0 },
             bolas: [], estouro: null, chamas: [], desenhar: desenharRyuKen };
  }

  // Anda ate a marca sem passar dela (o teste acelera o passo 8 vezes).
  function andarAte(lutador, passo) {
    const falta = lutador.marca - lutador.x;
    lutador.x += Math.sign(falta) * Math.min(Math.abs(falta), 0.42 * passo);
    const chegou = Math.abs(lutador.marca - lutador.x) < 0.01;
    lutador.quadro = chegou ? 0 : 1 + Math.floor(t / 7) % 2;
    return chegou;
  }

  // O golpe que sobe: agacha, sobe com o punho para o alto, cai e agacha de
  // novo (r e' o relogio do golpe; antes dele, o lutador espera em guarda).
  function shoryuken(lutador, r) {
    lutador.altura = 0;
    if (r < 0 || r >= 42) lutador.quadro = 0;
    else if (r < 8 || r >= 34) lutador.quadro = 5;
    else {
      lutador.quadro = 6;
      lutador.altura = Math.round(Math.sin(((r - 8) / 26) * Math.PI) * 16);
    }
    // Sobe andando um pouco para a frente.
    return r < 8 ? 0 : Math.min(26, r - 8) * 0.2;
  }

  function desenharRyuKen(passo) {
    const ryu = this.ryu, ken = this.ken;
    this.relogio += passo;
    const r = this.relogio;
    const de = function (fase) { this.fase = fase; this.relogio = 0; }.bind(this);
    if (this.fase === 'chegando') {
      const a = andarAte(ryu, passo), b = andarAte(ken, passo);
      if (a && b) de('guarda');
    } else if (this.fase === 'guarda') {
      // Os dois em guarda, balancando de leve, antes de cada golpe.
      ryu.quadro = ken.quadro = Math.floor(r / 12) % 2;
      if (r >= 40) de(this.proxima);
    } else if (this.fase === 'hadouken') {
      ryu.quadro = ken.quadro = r < 14 ? 3 : 4;
      if (r >= 14 && !this.soltou) {
        this.soltou = true;
        this.bolas = [{ de: 'ryu', x: ryu.x + 9, dir: 1 }, { de: 'ken', x: ken.x - 9 - BOLA_KEN[0].w, dir: -1 }];
      }
      if (r >= 54 && !this.bolas.length && !this.estouro) { this.proxima = 'shoryuken'; de('guarda'); }
    } else if (this.fase === 'shoryuken') {
      // Primeiro o do Ryu, depois o do Ken (com o punho em chamas).
      ryu.x = ryu.marca + shoryuken(ryu, r);
      ken.x = ken.marca - shoryuken(ken, r - 60);
      if (passo && ken.quadro === 6) {
        // As chamas do punho do Ken, que ficam para tras enquanto ele sobe.
        for (let i = 0; i < 2; i++) {
          this.chamas.push({ x: ken.x - 6 + aleatorio() * 4, y: CHAO - 21 - ken.altura + aleatorio() * 6, vida: 1 });
        }
      }
      if (r >= 110) {
        ryu.marca = ryu.x; ken.marca = ken.x;
        // O Tatsumaki leva cada um ate perto do outro, sem se cruzarem.
        this.curso = Math.max(0, ((ken.x - 8) - (ryu.x + 8) - 10) / 2);
        this.proxima = 'tatsumaki';
        de('guarda');
      }
    } else if (this.fase === 'tatsumaki') {
      // Os dois sobem girando um na direcao do outro e param perto.
      const giro = Math.floor(r / 4) % 4, no_ar = r >= 6 && r < 66;
      for (const lutador of [ryu, ken]) {
        lutador.quadro = no_ar ? (giro % 2 ? 8 : 7) : 5;
        lutador.giro = no_ar && giro === 2 ? -lutador.dir : 0;
        lutador.altura = no_ar ? Math.min(6, (r - 6) * 0.6, (66 - r) * 0.6) : 0;
      }
      const andou = this.curso * Math.max(0, Math.min(r, 66) - 6) / 60;
      ryu.x = ryu.marca + andou;
      ken.x = ken.marca - andou;
      if (r >= 74) { this.proxima = 'saindo'; de('guarda'); }
    } else if (this.fase === 'saindo') {
      // Viram para o mesmo lado e vao embora andando, um ao lado do outro.
      for (const lutador of [ryu, ken]) {
        lutador.dir = this.saida;
        lutador.x += this.saida * 0.42 * passo;
        lutador.quadro = 1 + Math.floor((t + (lutador === ken ? 3 : 0)) / 7) % 2;
      }
    }
    // As bolas: as duas se encontram no meio e se anulam num estouro.
    for (const bola of this.bolas) bola.x += bola.dir * 0.9 * passo;
    if (this.bolas.length === 2 && this.bolas[0].x + BOLA_RYU[0].w >= this.bolas[1].x) {
      this.estouro = { x: (this.bolas[0].x + BOLA_RYU[0].w + this.bolas[1].x) / 2, vida: 0 };
      this.bolas = [];
    }
    for (const bola of this.bolas) {
      const sprites = bola.de === 'ryu' ? BOLA_RYU : BOLA_KEN;
      S.colar(ctx, sprites[Math.floor(t / 3) % 2], bola.x, CHAO - 15, bola.dir);
    }
    if (this.estouro) {
      const e = this.estouro;
      e.vida += passo;
      const k = e.vida / 30;
      if (k >= 1) {
        this.estouro = null;
      } else {
        // Dois aneis que se abrem (azul do Ryu e laranja do Ken) e um
        // clarao branco em cruz no comeco.
        const y = CHAO - 12, x = Math.round(e.x), luz = (1 - k).toFixed(2);
        for (const [raio, cor, n] of [[2 + k * 11, 'rgba(127,176,255,', 12], [1 + k * 7, 'rgba(255,160,40,', 8]]) {
          ctx.fillStyle = cor + luz + ')';
          for (let i = 0; i < n; i++) {
            const a = i * 2 * Math.PI / n + k;
            ctx.fillRect(Math.round(x + Math.cos(a) * raio), Math.round(y + Math.sin(a) * raio * 0.8), 1, 1);
          }
        }
        if (k < 0.45) {
          ctx.fillStyle = '#ffffff';
          ctx.fillRect(x - 1, y - 1, 3, 3);
          ctx.fillRect(x - 3, y, 7, 1);
          ctx.fillRect(x, y - 3, 1, 7);
        }
      }
    }
    for (const c of this.chamas) { c.vida -= 0.06 * passo; c.y += 0.25 * passo; }
    this.chamas = this.chamas.filter(function (c) { return c.vida > 0; });
    for (const c of this.chamas) {
      ctx.fillStyle = c.vida > 0.6 ? '#ffe066' : c.vida > 0.3 ? '#ff7a1a' : '#c81e00';
      ctx.fillRect(Math.round(c.x), Math.round(c.y), 1, 1);
    }
    for (const [lutador, sprites] of [[ryu, RYU], [ken, KEN]]) {
      const q = sprites[lutador.quadro], meio = MEIO_LUTADOR[lutador.quadro];
      const dir = lutador.giro || lutador.dir;
      S.colar(ctx, q, lutador.x - (dir === 1 ? meio : q.w - 1 - meio), CHAO - q.h - lutador.altura, dir);
    }
    // O fogo no punho do Ken, enquanto ele sobe.
    if (ken.quadro === 6) {
      const fx = Math.round(ken.x - 6), fy = CHAO - 22 - Math.round(ken.altura);
      ctx.fillStyle = '#ff7a1a';
      ctx.fillRect(fx, fy - 1, 4, 2);
      ctx.fillStyle = '#ffe066';
      ctx.fillRect(fx + 1, fy - 2 - (Math.floor(t / 3) % 2), 2, 2);
    }
    if (this.fase !== 'saindo') return true;
    const fora = function (l) { return l.dir === 1 ? l.x - 12 > W : l.x + 12 < 0; };
    return !(fora(ryu) && fora(ken) && !this.chamas.length);
  }

  // Mega Man X (SNES 1993): o X corre, da a arrancada com rastro, para,
  // carrega o canhao do braco (o X Buster) e solta o tiro carregado; o Zero,
  // o parceiro dele em todos os Mega Man X, vem atras, para e da o golpe do
  // sabre verde (o Z-Saber). Depois os dois saem correndo. Redesenhados em
  // 20/10/2026 (pedido do Rafael: o X estava irreconhecivel): o capacete
  // redondo com a joia vermelha e o disco da orelha, o peito azul-claro, as
  // botas grandes; o Zero com o capacete vermelho de aleta branca, a joia
  // azul, o cabelo loiro comprido, as ombreiras brancas e a joia verde.
  const MEGAMAN_X = S.quadros([
    ['.....kkkkk......',
     '....kBBBBBk.....',
     '...kBBBRBBBk....',
     '..kBBBBBBBBBk...',
     '..kBCCBSSSSBk...',
     '..kBCCBSWKSSk...',
     '..kBBBBSSSSk....',
     '...kbBCCCbkk....',
     '..kBBCCCCCBBk...',
     '.kBBbCCCCbBBCk..',
     '.kCCkbBBBbkCCk..',
     '..kkBBBkBBBkk...',
     '..kCBBk.kBBCk...',
     '.kBBBBk.kBBBBk..',
     '..kkkk...kkkk...'],   // correndo
    ['.....kkkkk......',
     '....kBBBBBk.....',
     '...kBBBRBBBk....',
     '..kBBBBBBBBBk...',
     '..kBCCBSSSSBk...',
     '..kBCCBSWKSSk...',
     '..kBBBBSSSSk....',
     '...kbBCCCbkk....',
     '...kBCCCCCBBk...',
     '..kBbCCCCbBBCk..',
     '..kCCbBBBbkCCk..',
     '...kkBBBBBkkk...',
     '....kCBBBCk.....',
     '...kBBBBBBBk....',
     '....kkkkkkk.....'],   // correndo (o outro passo)
    ['.....kkkkk........',
     '....kBBBBBk.......',
     '...kBBBRBBBk......',
     '..kBBBBBBBBBk.....',
     '..kBCCBSSSSBk.....',
     '..kBCCBSWKSSk.....',
     '..kBBBBSSSSkkkk...',
     '...kbBCCCbBBBBBk..',
     '..kBBCCCCCbBBBBbk.',
     '.kBBbCCCCbBBBBBk..',
     '.kCCkbBBBbkkkkk...',
     '..kkBBBkBBBk......',
     '..kCBBk.kBBCk.....',
     '.kBBBBk.kBBBBk....',
     '..kkkk...kkkk.....']   // atirando: o braco vira o canhao (X Buster)
  ], { B: '#2f5bff', b: '#1c3aa8', C: '#7fd0ff', R: '#ff2a3a', S: '#ffc8a0', W: '#ffffff', K: '#1a3a8a', k: '#0c1640' });
  const ZERO = S.quadros([
    ['.......kkkk.......',
     '......kRRRRk......',
     '....kkRRBRRWk.....',
     '...kYRRRRRRWWk....',
     '..kYYRSSSSRkk.....',
     '.kYYYRSWKSSk......',
     'kYYYyRSSSSk.......',
     'kYYYykkRRkkk......',
     'kYYykWWRRRWWk.....',
     '.kYykWkRGRkWkk....',
     '..kykkkRRRkkk.....',
     '...k.kkkWkkk......',
     '....kRRkkkRRk.....',
     '...kWRRk.kRRWk....',
     '..kRRRRk.kRRRRk...',
     '...kkkk...kkkk....'],   // correndo (o cabelo voando para tras)
    ['.......kkkk.......',
     '......kRRRRk......',
     '....kkRRBRRWk.....',
     '..kkYRRRRRRWWk....',
     '.kYYYRSSSSRkk.....',
     'kYYYyRSWKSSk......',
     'kYYYyRSSSSk.......',
     '.kYYykkRRkkk......',
     '.kYykWWRRRWWk.....',
     '..kykWkRGRkWkk....',
     '...k.kkRRRkkk.....',
     '.....kkkWkkk......',
     '.....kRRRRRk......',
     '.....kWRRRWk......',
     '....kRRRRRRRk.....',
     '.....kkkkkkk......'],   // correndo (o outro passo)
    ['.......kkkk.......',
     '......kRRRRk......',
     '....kkRRBRRWk.....',
     '...kYRRRRRRWWk....',
     '..kYYRSSSSRkk.....',
     '.kYYYRSWKSSk......',
     'kYYYyRSSSSkkk.....',
     'kYYYykkRRkkkkkk...',
     'kYYykWWRRRWWkkkk..',
     '.kYykWkRGRWWkkk...',
     '..kykkkRRRkk......',
     '...k.kkkWkkkk.....',
     '....kRRkkkkRRk....',
     '...kWRRk..kRRWk...',
     '..kRRRRk..kRRRRk..',
     '...kkkk....kkkk...']   // o golpe do sabre (o braco esticado para a frente)
  ], { R: '#e8202a', r: '#a81420', W: '#ffffff', w: '#c8ccd8', B: '#3a8aff', Y: '#ffd23f', y: '#e0a800', S: '#ffc8a0', K: '#101010', G: '#3cd060', k: '#2a2a36', k: '#1a0a0e' });
  const TIRO_X = S.fazer(['.YY.', 'YWWY', '.YY.'], { Y: '#ffe066', W: '#ffffff' });
  // O tiro carregado: maior, amarelo-esverdeado, com a cauda de luz.
  const TIRO_CARREGADO = S.fazer(['..yYYYy..', '.yYWWWYy.', 'yYWWWWWYy', 'yYWWWWWYy', 'yYWWWWWYy', '.yYWWWYy.',
                                  '..yYYYy..'], { Y: '#ffe066', y: '#7dff6a', W: '#ffffff' });

  function iniciarMegaManX() {
    const dir = aleatorio() < 0.5 ? 1 : -1;
    const w = MEGAMAN_X[0].w;
    return { dir: dir, desenhar: desenharMegaManX, rastro: [], tiros: [], faiscas: [], corte: -1,
             x: { x: dir === 1 ? -w : W + 2, fase: 'correndo', relogio: 0, para: 90 + aleatorio() * 16 },
             zero: { x: dir === 1 ? -w - 26 : W + 28, fase: 'correndo', relogio: 0 } };
  }

  function desenharMegaManX(passo) {
    const dir = this.dir, x = this.x, zero = this.zero, w = MEGAMAN_X[0].w;
    const entrou = function (p) { return dir === 1 ? p.x : W - p.x; };
    x.relogio += passo;
    zero.relogio += passo;
    let velX = 0.55;
    if (x.fase === 'correndo') {
      if (!x.arrancou && entrou(x) >= 34) { x.fase = 'arrancada'; x.relogio = 0; x.arrancou = true; }
      if (entrou(x) >= x.para) { x.fase = 'carregando'; x.relogio = 0; }
    } else if (x.fase === 'arrancada') {
      velX = 1.6;
      if (passo) this.rastro.push({ x: x.x, vida: 1 });
      if (x.relogio >= 30) { x.fase = 'correndo'; x.relogio = 0; }
    } else if (x.fase === 'carregando') {
      // As faiscas vem de longe e se juntam na boca do canhao.
      velX = 0;
      if (passo && aleatorio() < 0.8) {
        const a = aleatorio() * Math.PI * 2;
        this.faiscas.push({ a: a, r: 9, vida: 1 });
      }
      if (x.relogio >= 40) {
        x.fase = 'atirando'; x.relogio = 0;
        this.tiros.push({ x: x.x + (dir === 1 ? w - 1 : 1 - TIRO_CARREGADO.w), grande: true });
      }
    } else if (x.fase === 'atirando') {
      velX = 0;
      if (x.relogio >= 24) { x.fase = 'saindo'; x.relogio = 0; }
    } else {
      velX = 0.8;
    }
    x.x += dir * velX * passo;
    // O Zero para atras do X quando ele carrega e da o golpe quando ele atira.
    let velZ = zero.fase === 'saindo' ? 0.8 : 0.55;
    const atras = dir === 1 ? x.x - zero.x : zero.x - x.x;
    if (zero.fase === 'correndo' && (x.fase === 'carregando' || x.fase === 'atirando') && atras <= 30) {
      zero.fase = 'parado'; zero.relogio = 0;
    }
    if (zero.fase === 'parado') {
      velZ = 0;
      if (x.fase === 'atirando' || x.fase === 'saindo') { zero.fase = 'sabre'; zero.relogio = 0; this.corte = 0; }
    } else if (zero.fase === 'sabre') {
      velZ = 0;
      if (zero.relogio >= 26) { zero.fase = 'saindo'; zero.relogio = 0; }
    }
    zero.x += dir * velZ * passo;
    // O rastro da arrancada.
    for (const r of this.rastro) r.vida -= 0.07 * passo;
    this.rastro = this.rastro.filter(function (r) { return r.vida > 0; });
    ctx.globalAlpha = 0.35;
    for (const r of this.rastro) S.colar(ctx, MEGAMAN_X[1], r.x, CHAO - MEGAMAN_X[1].h, dir);
    ctx.globalAlpha = 1;
    // Os tiros (o carregado e maior e deixa uma cauda).
    for (const tiro of this.tiros) {
      tiro.x += dir * 1.8 * passo;
      const sprite = tiro.grande ? TIRO_CARREGADO : TIRO_X;
      const y = CHAO - (tiro.grande ? 12 : 6);
      if (tiro.grande) {
        ctx.fillStyle = 'rgba(125,255,106,0.6)';
        ctx.fillRect(Math.round(tiro.x - dir * 6 + (dir === 1 ? 0 : sprite.w)), y + 3, 6, 1);
      }
      S.colar(ctx, sprite, tiro.x, y, dir);
    }
    this.tiros = this.tiros.filter(function (tiro) { return tiro.x > -12 && tiro.x < W + 12; });
    // O Zero, com o sabre e o arco verde do golpe.
    const qz = zero.fase === 'sabre' && zero.relogio < 18 ? ZERO[2]
      : zero.fase === 'parado' || zero.fase === 'sabre' ? ZERO[0] : ZERO[Math.floor(t / 4) % 2];
    S.colar(ctx, qz, zero.x, CHAO - qz.h, dir);
    if (this.corte >= 0 && this.corte < 18) {
      this.corte += passo;
      const mao = zero.x + (dir === 1 ? 13 : ZERO[2].w - 14), my = CHAO - 9;
      const luz = Math.max(0, 1 - this.corte / 18);
      for (let a = -1.5; a <= 0.6; a += 0.16) {
        const px = Math.round(mao + dir * Math.cos(a) * 9), py = Math.round(my + Math.sin(a) * 9);
        ctx.fillStyle = 'rgba(125,255,125,' + luz.toFixed(2) + ')';
        ctx.fillRect(px, py, 1, 1);
        ctx.fillStyle = 'rgba(255,255,255,' + (luz * 0.8).toFixed(2) + ')';
        ctx.fillRect(Math.round(mao + dir * Math.cos(a) * 7), Math.round(my + Math.sin(a) * 7), 1, 1);
      }
    }
    // O X (o canhao esticado enquanto carrega e atira).
    const qx = x.fase === 'carregando' || x.fase === 'atirando' ? MEGAMAN_X[2]
      : MEGAMAN_X[Math.floor(t / (velX > 1 ? 3 : 4)) % 2];
    S.colar(ctx, qx, x.x, CHAO - qx.h, dir);
    // As faiscas da carga, e o canhao piscando quando ela esta cheia.
    const bocaX = x.x + (dir === 1 ? w + 1 : -2), bocaY = CHAO - 8;
    for (const f of this.faiscas) { f.r -= 0.35 * passo; f.vida = f.r / 9; }
    this.faiscas = this.faiscas.filter(function (f) { return f.r > 0.5; });
    if (x.fase === 'carregando') {
      for (const f of this.faiscas) {
        ctx.fillStyle = f.r > 5 ? '#7dff6a' : '#ffe066';
        ctx.fillRect(Math.round(bocaX + Math.cos(f.a) * f.r), Math.round(bocaY + Math.sin(f.a) * f.r * 0.7), 1, 1);
      }
      if (x.relogio > 20 && Math.floor(t / 3) % 2 === 0) {
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(Math.round(bocaX) - 1, bocaY - 1, 2, 2);
      }
    } else {
      this.faiscas = [];
    }
    const fora = function (p) { return dir === 1 ? p.x > W + 2 : p.x < -w - 4; };
    return !(fora(x) && fora(zero) && this.tiros.length === 0);
  }

  // Super Bomberman (SNES 1993): o Bomberman para, deixa a bomba e sai
  // andando; a bomba pisca, e as chamas saem em cruz. Redesenhado em
  // 20/10/2026 (pedido do Rafael: estava fora de proporcao): a cabeca grande e
  // redonda do capacete, a antena com a bolinha rosa e o visor com os olhos,
  // na medida do Link. A bomba e a explosao ficaram como eram.
  const BOMBERMAN = S.quadros([
    ['......kk.......',
     '.....kPPk......',
     '....kkkAkkk....',
     '...kWWWWWWWk...',
     '..kWWWWWWWWWk..',
     '..kWWSSSSSSWk..',
     '..kWSSSKSSKSk..',
     '..kWSSSKSSKSk..',
     '..kwWSSSSSSWk..',
     '...kwWWWWWWk...',
     '..kPWBBBBBWPk..',
     '...kWBBbBBWk...',
     '...kWWkkkWWk...',
     '..kPPPk.kPPPk..',
     '...kkk...kkk...'],   // andando (pernas abertas)
    ['......kk.......',
     '.....kPPk......',
     '....kkkAkkk....',
     '...kWWWWWWWk...',
     '..kWWWWWWWWWk..',
     '..kWWSSSSSSWk..',
     '..kWSSSKSSKSk..',
     '..kWSSSKSSKSk..',
     '..kwWSSSSSSWk..',
     '...kwWWWWWWk...',
     '..kPWBBBBBWPk..',
     '...kWBBbBBWk...',
     '....kWWWWkk....',
     '....kPPPPk.....',
     '.....kkkk......']   // andando (pernas juntas)
  ], { P: '#ff5fa8', p: '#c83a7a', W: '#ffffff', w: '#c8d0e0', S: '#ffc8a0', K: '#101010', B: '#2f5bff', b: '#1f3cb8', A: '#5a5a6a', k: '#1a1a2a' });
  const BOMBA = S.quadros([
    ['....Y.', '...F..', '.KKKK.', 'KKwKKK', 'KwKKKK', 'KKKKKK', '.KKKK.'],
    ['...Y..', '...F..', '.KKKK.', 'KKwKKK', 'KwKKKK', 'KKKKKK', '.KKKK.']
  ], { Y: '#ffe066', F: '#8a5a2a', K: '#202030', w: '#8a8aa8' });

  function iniciarBomberman() {
    const dir = aleatorio() < 0.5 ? 1 : -1;
    return { dir: dir, x: dir === 1 ? -BOMBERMAN[0].w : W + 2, larga: W / 2 + (aleatorio() - 0.5) * 50, bomba: null,
             desenhar: desenharBomberman };
  }

  function desenharBomberman(passo) {
    this.x += this.dir * 0.45 * passo;
    if (!this.bomba && (this.dir === 1 ? this.x >= this.larga : this.x <= this.larga)) {
      this.bomba = { x: Math.round(this.x + (BOMBERMAN[0].w - 6) / 2), vida: 0 };
    }
    if (this.bomba && this.bomba.vida < 150) {
      this.bomba.vida += passo;
      const b = this.bomba;
      if (b.vida < 110) {
        // A bomba pisca mais depressa perto de explodir.
        if (b.vida < 80 || Math.floor(b.vida / 3) % 2 === 0) S.colar(ctx, BOMBA[Math.floor(t / 4) % 2], b.x, CHAO - 7, 1);
      } else {
        const k = (b.vida - 110) / 40;            // as chamas em cruz, que encolhem
        const braco = Math.round(10 * (1 - k * 0.6));
        const cx = b.x + 3, cy = CHAO - 4;
        ctx.fillStyle = k < 0.5 ? '#ffe066' : '#ff7a29';
        ctx.fillRect(cx - braco, cy - 1, braco * 2 + 1, 3);
        ctx.fillRect(cx - 1, cy - braco, 3, braco + 3);
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(cx - braco + 2, cy, braco * 2 - 3, 1);
        ctx.fillRect(cx, cy - braco + 2, 1, braco);
      }
    }
    S.colar(ctx, BOMBERMAN[Math.floor(t / 6) % 2], this.x, CHAO - BOMBERMAN[0].h, this.dir);
    const fora = this.dir === 1 ? this.x > W + 2 : this.x < -BOMBERMAN[0].w - 2;
    return !(fora && (!this.bomba || this.bomba.vida >= 150));
  }

  // Bonk's Adventure (PC Engine 1989, o PC Genjin): o homem das cavernas de
  // cabeca enorme vem pulando e da a cabecada em giro.
  const PALETA_BONK = { S: '#f2b880', s: '#d8905a', E: '#101010', M: '#a83a2a', Y: '#ffb02e', K: '#7a4a20' };
  const BONK = S.quadros([
    ['..SSSSS...', '.SSSSSSS..', 'SSSSSSSSS.', 'SSSESSESS.', 'SSSSSSSSS.', '.SSMMSSs..', '..sSSSs...',
     '...YKY....', '..SYYYS...', '...S.S....', '..SS.SS...'],
    ['..SSSSS...', '.SSSSSSS..', 'SSSSSSSSS.', 'SSSESSESS.', 'SSSSSSSSS.', '.SSMMSSs..', '..sSSSs...',
     '...YKY....', '..SYYYS...', '..S...S...', '.SS...SS..']
  ], PALETA_BONK);

  function iniciarBonk() {
    const dir = aleatorio() < 0.5 ? 1 : -1;
    return { dir: dir, x: dir === 1 ? -10 : W + 2, altura: 0, vy: 0, desenhar: desenharBonk };
  }

  function desenharBonk(passo) {
    this.x += this.dir * 0.5 * passo;
    // Pula o tempo todo (pulinhos baixos e, de vez em quando, um alto).
    if (this.altura <= 0) { this.altura = 0; this.vy = Math.floor(t / 90) % 3 === 2 ? 1.6 : 0.9; }
    this.altura += this.vy * passo;
    this.vy -= 0.12 * passo;
    if (this.altura < 0) this.altura = 0;
    const quadro = BONK[this.altura > 0.5 ? 1 : 0];
    S.colar(ctx, quadro, this.x, CHAO - quadro.h - this.altura, this.dir);
    return this.dir === 1 ? this.x < W + 2 : this.x > -10;
  }

  // Ao longe, no pe do morro (pedido do Rafael, 15/10/2026: "poderia aparecer
  // mais no pe do morro, um pouco menor, como se estivesse mais distante"):
  // os desenhos sao pequenos (5 a 6 pontos) e pisam no comeco da grama.
  const LONGE = HORIZONTE + 1;
  const MINI_TURMA = [
    S.quadros([['.RR.', 'RRRR', '.SS.', 'OOOO', '.OO.', 'H..H'], ['.RR.', 'RRRR', '.SS.', 'OOOO', '.OO.', '.HH.']],
              { R: '#d82800', S: '#ffb070', O: '#2038ec', H: '#8a4b00' }),                         // Mario
    S.quadros([['.GG.', 'GGGG', '.SS.', 'OOOO', '.OO.', 'H..H'], ['.GG.', 'GGGG', '.SS.', 'OOOO', '.OO.', '.HH.']],
              { G: '#2fbf4a', S: '#ffb070', O: '#2038ec', H: '#8a4b00' }),                         // Luigi
    S.quadros([['.YY.', 'HHHH', 'HSS.', 'PPPP', 'PPPP', '.PP.'], ['.YY.', 'HHHH', 'HSS.', 'PPPP', 'PPPP', 'PPPP']],
              { Y: '#ffc21a', H: '#ffe27a', S: '#ffd2aa', P: '#ff8ccf' }),                         // Peach
    S.quadros([['RWWR', 'WRRW', '.SS.', 'UUUU', '.SS.', 'S..S'], ['RWWR', 'WRRW', '.SS.', 'UUUU', '.SS.', '.SS.']],
              { R: '#e8202a', W: '#ffffff', S: '#ffd2aa', U: '#2f5bff' })                           // Toad
  ];
  const MINI_SONIC = S.quadros([['BBB..', '.BBBW', 'BBBSS', '.BBS.', 'RR.RR'], ['BBB..', '.BBBW', 'BBBSS', '.BBS.', '.RRR.']],
                               { B: '#2251ff', W: '#ffffff', S: '#ffcc99', R: '#e8202a' });
  const MINI_TAILS = S.quadros([['O.OO.', 'OOOOW', 'TOOWW', 'TTOW.', '.R.R.'], ['T.OO.', 'TOOOW', '.OOWW', 'TTOW.', '..RR.']],
                               { O: '#f0a020', W: '#ffffff', T: '#fff2d8', R: '#e8202a' });

  function iniciarTurmaLonge() {
    const dir = aleatorio() < 0.5 ? 1 : -1;
    return { dir: dir, x: dir === 1 ? -6 : W + 2, desenhar: desenharTurmaLonge };
  }

  function desenharTurmaLonge(passo) {
    this.x += this.dir * 0.18 * passo;
    for (let i = 0; i < MINI_TURMA.length; i++) {
      const x = this.x - this.dir * i * 7;
      const pulinho = Math.floor(t / 8 + i) % 2;
      S.colar(ctx, MINI_TURMA[i][pulinho], x, LONGE - 6, this.dir);
    }
    const ultimo = this.x - this.dir * (MINI_TURMA.length - 1) * 7;
    return this.dir === 1 ? ultimo < W + 2 : ultimo > -6;
  }

  function iniciarSonicTailsLonge() {
    const dir = aleatorio() < 0.5 ? 1 : -1;
    return { dir: dir, x: dir === 1 ? -6 : W + 2, desenhar: desenharSonicTailsLonge };
  }

  function desenharSonicTailsLonge(passo) {
    this.x += this.dir * 0.7 * passo;
    const quadro = Math.floor(t / 3) % 2;
    S.colar(ctx, MINI_SONIC[quadro], this.x, LONGE - 5, this.dir);
    S.colar(ctx, MINI_TAILS[quadro], this.x - this.dir * 8, LONGE - 5, this.dir);
    const tails = this.x - this.dir * 8;
    return this.dir === 1 ? tails < W + 2 : tails > -6;
  }

  const VISITAS = { mario: iniciarMario, sonic: iniciarSonic, duckhunt: iniciarDuckHunt, kirby: iniciarKirby,
                    yoshi: iniciarYoshi, link: iniciarLink, wiggler: iniciarWiggler, monty: iniciarMonty, lakitu: iniciarLakitu, donkey: iniciarDonkey, tails: iniciarTails, knuckles: iniciarKnuckles, chocobo: iniciarChocobo, rabites: iniciarRabites, saturno: iniciarSaturno,
                    ryu: iniciarRyu, megamanx: iniciarMegaManX, bomberman: iniciarBomberman, bonk: iniciarBonk,
                    turmalonge: iniciarTurmaLonge, sonictailslonge: iniciarSonicTailsLonge };
  // As visitas que chegam logo depois de outra (pedido do Rafael, 20/10/2026:
  // o Mario e o Luigi aparecem assim que o Yoshi vai embora). Elas nao
  // entram no sorteio: vem sempre com a outra.
  const DEPOIS_DE = { yoshi: 'mario' };
  const SO_DEPOIS = Object.keys(DEPOIS_DE).map(function (n) { return DEPOIS_DE[n]; });
  let filaDeVisitas = ['yoshi'];
  let visita = null;
  let seguinte = null;          // a visita que vem logo depois desta
  let esperaVisita = 420;       // ~7 s depois de abrir

  function iniciarVisita(nome) {
    const nova = VISITAS[nome]();
    nova.nome = nome;
    return nova;
  }

  function proximaVisita() {
    if (seguinte) {
      const nome = seguinte;
      seguinte = null;
      return iniciarVisita(nome);
    }
    if (!filaDeVisitas.length) {
      filaDeVisitas = Object.keys(VISITAS).filter(function (n) { return SO_DEPOIS.indexOf(n) < 0; });
      for (let i = filaDeVisitas.length - 1; i > 0; i--) {          // embaralha
        const j = Math.floor(aleatorio() * (i + 1));
        const troca = filaDeVisitas[i];
        filaDeVisitas[i] = filaDeVisitas[j];
        filaDeVisitas[j] = troca;
      }
    }
    return iniciarVisita(filaDeVisitas.shift());
  }

  function desenharVisitas(passo) {
    if (!visita) {
      esperaVisita -= passo;
      if (esperaVisita <= 0) visita = proximaVisita();
      return;
    }
    if (!visita.desenhar(passo)) {
      seguinte = DEPOIS_DE[visita.nome] || null;
      visita = null;
      // 20 a 35 s; no "Visualizar animação", 1,5 a 4 s (quem abriu quer ver).
      // A que vem logo depois (o Mario depois do Yoshi) chega em meio segundo.
      esperaVisita = seguinte ? 30 : soFundo() ? 90 + aleatorio() * 150 : 1200 + aleatorio() * 900;
    }
  }

  function soFundo() { return document.body.dataset.soFundo === 'true'; }
  let gravando = false;

  // Para os testes chamarem uma visita na hora (testes\\teste_fundos_animados.py).
  window.__fundoClaro = {
    visitas: Object.keys(VISITAS),
    chamar: function (nome) { if (VISITAS[nome]) { visita = iniciarVisita(nome); seguinte = null; } return !!visita; },
    rodando: function () { return !!visita; },
    velocidade: function (v) { velocidade = Math.max(1, Math.min(16, Number(v) || 1)); return velocidade; },
    soltarCoelho: function () { esperaCoelho = 0; return true; },
    // Avanca n quadros na hora (passo em 1/60 s; 3 = um quadro dos 20 por
    // segundo): para revisar as visitas quadro a quadro e gravar o GIF.
    // Para o laco normal: quem grava o GIF avanca quadro a quadro (avancar).
    gravar: function () { gravando = true; sincronizar(); return true; },
    avancar: function (n, passo) {
      passo = passo || 3;
      for (let i = 0; i < (n || 1); i++) { t += passo; desenharQuadro(passo); }
      return t;
    },
    // Os pontos da tela (160 x 90, RGBA) em base64.
    pixels: function () {
      const d = ctx.getImageData(0, 0, W, H).data;
      let s = '';
      for (let i = 0; i < d.length; i += 8192) s += String.fromCharCode.apply(null, d.subarray(i, i + 8192));
      return btoa(s);
    }
  };

  // Um quadro completo
  function desenharQuadro(passo) {
    passo = passo || 0;
    ctx.drawImage(fixa, 0, 0);
    desenharSol();
    desenharBalao(passo);
    desenharNuvens(passo);
    desenharBando(passo);
    desenharGirassois();
    desenharArbusto(passo);
    desenharCoelho(passo);
    desenharVisitas(passo);
    desenharAbelhas(passo);
    for (const b of borboletas) {
      if (passo) atualizarBorboleta(b, passo);
      desenharBorboleta(b);
    }
    desenharSementes(passo);
  }

  // Cena parada: as borboletas pousadas nas flores, sem nada se mexer.
  function prepararCenaParada() {
    borboletas.forEach(function (b, i) {
      b.estado = 'pousada';
      b.flor = (i * 3 + 1) % girassois.length;
      const m = miolo(girassois[b.flor]);
      b.x = m.x;
      b.y = m.y;
      b.duracao = 1e9;
    });
  }

  // ------------------------------------------------------------------
  // Quando animar
  // ------------------------------------------------------------------
  const menosMovimento = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : null;

  function modo() {
    if (document.body.dataset.tema === 'escuro') return 'oculto';
    if (gravando) return 'gravando';       // ferramentas\gravar_fundo_gif.py avanca na mao
    if (soFundo()) return 'animado';       // "Visualizar animação": anima sempre
    const escolha = document.body.dataset.fundoAnimado || 'automatico';
    if (escolha === 'parado') return 'parado';
    if (escolha === 'sempre') return 'animado';
    if (document.body.dataset.modoModesto === 'true') return 'parado';
    if (menosMovimento && menosMovimento.matches) return 'parado';
    return 'animado';
  }

  const INTERVALO = 1000 / 20;   // 20 quadros por segundo (ver o item 3, no topo)
  let velocidade = 1;   // so os testes aceleram (__fundoClaro.velocidade)
  let geracao = 0;      // cada laco novo ganha um numero; o velho para sozinho
  let ultimo = 0;       // hora do ultimo quadro desenhado
  let modoAtual = null;

  function iniciarLaco() {
    const minha = ++geracao;
    ultimo = 0;
    function quadro() {
      if (minha !== geracao) return;      // laco antigo: morre aqui
      setTimeout(quadro, INTERVALO);
      // Janela escondida (minimizada, ou o jogo por cima): nao desenha.
      if (document.visibilityState !== 'visible') return;
      const agora = performance.now();
      const passo = (ultimo ? Math.min(4, (agora - ultimo) / (1000 / 60)) : 1) * velocidade;
      ultimo = agora;
      t += passo;
      // Vento: rajada de vez em quando, sobe e desce suave.
      if (aleatorio() < 0.0007 * passo) ventoAlvo = 2.4;
      if (ventoAlvo > 1 && aleatorio() < 0.006 * passo) ventoAlvo = 1;
      vento += (ventoAlvo - vento) * 0.02 * passo;
      try {
        desenharQuadro(passo);
      } catch (e) {
        console.error('Fundo de campo: erro num quadro, seguindo pro proximo.', e);
      }
    }
    setTimeout(quadro, 0);
  }

  function pararLaco() {
    geracao++;
  }

  let assistindo = false;
  function sincronizar() {
    // Quem acabou de abrir o "Visualizar animação" ve uma visita logo.
    if (soFundo() && !assistindo) esperaVisita = Math.min(esperaVisita, 45);
    assistindo = soFundo();
    const novo = modo();
    canvas.style.display = novo === 'oculto' ? 'none' : 'block';
    const travado = novo === 'animado' && modoAtual === 'animado'
      && document.visibilityState === 'visible' && ultimo
      && performance.now() - ultimo > 3000;
    if (novo === modoAtual && !travado) return;
    const anterior = modoAtual;
    modoAtual = novo;
    if (novo === 'animado') {
      if (anterior === 'parado') {
        // Saindo da cena parada: as borboletas voltam a ir e vir.
        borboletas.forEach(function (b) { b.duracao = 60 + aleatorio() * 240; });
      }
      iniciarLaco();
    } else {
      pararLaco();
      if (novo === 'parado') {
        prepararCenaParada();
        t = 90;
        desenharQuadro(0);
      }
    }
  }

  sincronizar();
  // Reage na hora a troca de tema, modo modesto e escolha do aluno...
  new MutationObserver(sincronizar).observe(document.body, {
    attributes: true, attributeFilter: ['data-tema', 'data-modo-modesto', 'data-fundo-animado', 'data-so-fundo']
  });
  // ...e a mudanca da preferencia do Windows (animacoes ligadas/desligadas).
  if (menosMovimento && menosMovimento.addEventListener) {
    menosMovimento.addEventListener('change', sincronizar);
  }
  setInterval(sincronizar, 3000);
})();
