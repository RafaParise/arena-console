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

  // Coelho aos pulos de verdade (02/10/2026: antes o corpo subia e descia
  // inteiro, sem perna nenhuma). Cada pulo: agacha, estica as pernas no ar
  // e cai agachado de novo.
  const PALETA_COELHO = { E: '#e8ddd0', H: '#f2ece4', B: '#e8ddd0', K: '#2b1c12', n: '#ff8fb0', T: '#ffffff',
                          F: '#d8ccbc' };
  const QUADROS_COELHO = S.quadros([
    ['......E.E.',          // agachado (antes e depois do pulo)
     '......E.E.',
     '.....HHHH.',
     '..BBBHKHH.',
     '.BBBBBHHn.',
     'TBBBBBBH..',
     '.BBBBBBB..',
     '..FF...FF.'],
    ['.......EE.',          // no ar: pernas de tras esticadas, as da frente na frente
     '......HEE.',
     '.....HKHH.',
     'TBBBBBHHn.',
     '.BBBBBBH..',
     'FF......F.']
  ], PALETA_COELHO);
  let coelho = null;
  let esperaCoelho = 900 + sorteio() * 1200;

  function desenharCoelho(passo) {
    if (!coelho) {
      esperaCoelho -= passo;
      if (esperaCoelho <= 0) {
        const dir = aleatorio() < 0.5 ? 1 : -1;
        coelho = { dir: dir, x: dir === 1 ? -10 : W + 2, chao: H - 4 - Math.floor(aleatorio() * 5), fase: 0 };
      }
      return;
    }
    coelho.fase += passo;
    const ciclo = 46;                                  // um pulo a cada ~0,8 s
    const p = (coelho.fase % ciclo) / ciclo;
    let quadro = QUADROS_COELHO[0], altura = 0;
    if (p >= 0.3) {                                    // no ar
      quadro = QUADROS_COELHO[1];
      altura = Math.sin(((p - 0.3) / 0.7) * Math.PI) * 6;
      coelho.x += coelho.dir * 0.9 * passo;
    }
    S.colar(ctx, quadro, coelho.x, coelho.chao - quadro.h - altura, coelho.dir);
    if (coelho.x < -14 || coelho.x > W + 4) {
      coelho = null;
      esperaCoelho = 2000 + aleatorio() * 2400;
    }
  }

  // Joaninha (02/10/2026: era "so uma barrinha preta e vermelha que passa
  // de um lado para o outro"). Agora com casco de pintas, cabeca e
  // perninhas que andam; de vez em quando abre as asas e voa para outro
  // lugar do campo.
  const QUADROS_JOANINHA = S.quadros([
    ['..RRR..',
     '.RKRKRK',
     'RRRRRRK',
     'RKRRKRK',
     '.l.l.l.'],
    ['..RRR..',
     '.RKRKRK',
     'RRRRRRK',
     'RKRRKRK',
     'l.l.l..'],
    ['w.RRR.w',
     'wRKRKRK',
     '.RRRRRK',
     '..RRKR.']
  ], { R: '#e53935', K: '#1a1a1a', l: '#1a1a1a', w: 'rgba(255,255,255,0.85)' });
  const joaninha = { x: 10 + sorteio() * (W - 30), y: HORIZONTE + 2, dir: 1, voo: null,
                     espera: 600 + sorteio() * 900 };

  function desenharJoaninha(passo) {
    const j = joaninha;
    if (j.voo) {
      j.voo.p = Math.min(1, j.voo.p + passo / j.voo.duracao);
      j.x = j.voo.x0 + (j.voo.x1 - j.voo.x0) * j.voo.p;
      j.y = j.voo.y0 + (j.voo.y1 - j.voo.y0) * j.voo.p - Math.sin(j.voo.p * Math.PI) * 14;
      S.colar(ctx, QUADROS_JOANINHA[2], j.x, j.y - 4, j.dir);
      if (j.voo.p >= 1) j.voo = null;
      return;
    }
    j.x += j.dir * 0.07 * passo;
    if (j.x > W - 10) j.dir = -1;
    if (j.x < 3) j.dir = 1;
    j.espera -= passo;
    if (j.espera <= 0) {                  // abre as asas e vai para outro canto
      const x1 = 6 + aleatorio() * (W - 20);
      j.dir = x1 > j.x ? 1 : -1;
      j.voo = { p: 0, x0: j.x, y0: j.y, x1: x1, y1: HORIZONTE + 2 + Math.floor(aleatorio() * 3),
                duracao: 90 + Math.abs(x1 - j.x) * 1.2 };
      j.espera = 900 + aleatorio() * 1200;
    }
    S.colar(ctx, QUADROS_JOANINHA[Math.floor(t / 8) % 2], j.x, j.y - 4, j.dir);
  }

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

  // Super Mario Bros. (NES, 1985): o Mario corre e pula por cima do Goomba.
  const PALETA_MARIO = { R: '#d82800', H: '#8a4b00', S: '#ffb070', E: '#000000', O: '#2038ec' };
  const MARIO = S.quadros([
    ['..RRRR..', '.RRRRRRR', '.HHSSES.', 'HSHSSSSS', 'HSHHSSSH', '.SSSSSS.',
     '.RROORR.', 'RROOOORR', 'SSOOOOSS', '.OO..OO.', 'HH....HH'],
    ['..RRRR..', '.RRRRRRR', '.HHSSES.', 'HSHSSSSS', 'HSHHSSSH', '.SSSSSS.',
     '..RORR..', '.RROORR.', '.SOOOOS.', '..OOOO..', '..HHHH..'],
    ['..RRRR.S', '.RRRRRRS', '.HHSSESR', 'HSHSSSSS', 'HSHHSSSH', '.SSSSSS.',      // pulo
     'RROORRR.', 'SROOOOR.', '.OOOOOO.', 'OO...OO.', 'H.....HH']
  ], PALETA_MARIO);
  const GOOMBA = S.quadros([
    ['..GGGG..', '.GGGGGG.', 'GWKGGKWG', 'GGGGGGGG', '.TTTTTT.', '..TTTT..', '.BB..BB.'],
    ['..GGGG..', '.GGGGGG.', 'GWKGGKWG', 'GGGGGGGG', '.TTTTTT.', '..TTTT..', 'BB....BB']
  ], { G: '#a0522d', W: '#ffffff', K: '#000000', T: '#f2c38a', B: '#3b2412' });

  function iniciarMario() {
    const dir = aleatorio() < 0.5 ? 1 : -1;
    return { dir: dir, x: dir === 1 ? -10 : W + 2, altura: 0, vy: 0, noAr: false,
             goomba: dir === 1 ? W + 2 : -10, desenhar: desenharMario };
  }

  function desenharMario(passo) {
    this.x += this.dir * 0.55 * passo;
    this.goomba -= this.dir * 0.12 * passo;
    const perto = this.dir === 1 ? this.goomba - this.x : this.x - this.goomba;
    if (!this.noAr && perto > 0 && perto < 16) { this.noAr = true; this.vy = 1.6; }
    if (this.noAr) {
      this.altura += this.vy * passo;
      this.vy -= 0.11 * passo;
      if (this.altura <= 0) { this.altura = 0; this.noAr = false; }
    }
    S.colar(ctx, GOOMBA[Math.floor(t / 14) % 2], this.goomba, CHAO - 7, -this.dir);
    const quadro = this.noAr ? MARIO[2] : MARIO[Math.floor(t / 5) % 2];
    S.colar(ctx, quadro, this.x, CHAO - quadro.h - this.altura, this.dir);
    const marioFora = this.dir === 1 ? this.x > W + 2 : this.x < -10;
    const goombaFora = this.dir === 1 ? this.goomba < -10 : this.goomba > W + 2;
    return !(marioFora && goombaFora);
  }

  // Sonic the Hedgehog (Mega Drive, 1991): passa correndo, pula em bola e
  // pega o anel dourado no meio do campo.
  const PALETA_SONIC = { b: '#2251ff', s: '#ffcc99', w: '#ffffff', k: '#000000', r: '#e8202a' };
  const SONIC = S.quadros([
    ['bbb.......', '.bbbbb....', 'bbbbbbbw..', '.bbbbbwkw.', 'bbbbbsss..', '.bbbssss..',
     '..bbss.ww.', '..bbbb....', '.rr..rr...', 'rr....rr..'],
    ['bbb.......', '.bbbbb....', 'bbbbbbbw..', '.bbbbbwkw.', 'bbbbbsss..', '.bbbssss..',
     '..bbss.ww.', '..bbbb....', '..rrrr....', '...rr.....']
  ], PALETA_SONIC);
  const SONIC_BOLA = S.fazer(['..bbbb..', '.bbwbbb.', 'bbbbbwbb', 'bwbbbbbb', 'bbbbbbwb', 'bbwbbbbb',
                              '.bbbwbb.', '..bbbb..'], { b: '#2251ff', w: '#7fa6ff' });
  const ANEL = S.fazer(['.YYY.', 'Y...Y', 'Y...Y', 'Y...Y', '.YYY.'], { Y: '#ffd23f' });

  function iniciarSonic() {
    const dir = aleatorio() < 0.5 ? 1 : -1;
    return { dir: dir, x: dir === 1 ? -12 : W + 2, altura: 0, vy: 0, noAr: false,
             anel: { x: 50 + aleatorio() * 60, pego: -1 }, poeira: [], desenhar: desenharSonic };
  }

  function desenharSonic(passo) {
    this.x += this.dir * 0.85 * passo;       // rapido, mas da para ver quem e'
    const ate = this.dir === 1 ? this.anel.x - this.x : this.x - this.anel.x;
    if (!this.noAr && this.anel.pego < 0 && ate > 0 && ate < 22) { this.noAr = true; this.vy = 1.9; }
    if (this.noAr) {
      this.altura += this.vy * passo;
      this.vy -= 0.13 * passo;
      if (this.altura <= 0) { this.altura = 0; this.noAr = false; }
    }
    if (this.anel.pego < 0 && Math.abs(this.x + 4 - this.anel.x) < 4 && this.altura > 6) this.anel.pego = 0;
    if (this.anel.pego < 0) {
      S.colar(ctx, ANEL, this.anel.x, CHAO - 22 + Math.round(Math.sin(t * 0.1)), 1);
    } else if (this.anel.pego < 30) {                 // brilhinho de anel pego
      this.anel.pego += passo;
      ctx.fillStyle = 'rgba(255,240,140,' + (1 - this.anel.pego / 30).toFixed(2) + ')';
      const r = 2 + this.anel.pego / 6;
      for (let i = 0; i < 6; i++) {
        const a = i * Math.PI / 3;
        ctx.fillRect(Math.round(this.anel.x + 2 + Math.cos(a) * r), Math.round(CHAO - 20 + Math.sin(a) * r), 1, 1);
      }
    }
    if (passo && !this.noAr && aleatorio() < 0.6) {
      this.poeira.push({ x: this.x + (this.dir === 1 ? 0 : 9), y: CHAO - 1, vida: 1 });
    }
    for (const p of this.poeira) { p.vida -= 0.05 * passo; p.y -= 0.05 * passo; }
    this.poeira = this.poeira.filter(function (p) { return p.vida > 0; });
    for (const p of this.poeira) {
      ctx.fillStyle = 'rgba(255,255,255,' + (p.vida * 0.6).toFixed(2) + ')';
      ctx.fillRect(Math.round(p.x), Math.round(p.y), 1, 1);
    }
    const quadro = this.noAr ? SONIC_BOLA : SONIC[Math.floor(t / 3) % 2];
    S.colar(ctx, quadro, this.x, CHAO - quadro.h - this.altura, this.dir);
    return this.dir === 1 ? this.x < W + 4 || this.poeira.length > 0 : this.x > -14 || this.poeira.length > 0;
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

  const VISITAS = { mario: iniciarMario, sonic: iniciarSonic, duckhunt: iniciarDuckHunt, kirby: iniciarKirby };
  let filaDeVisitas = ['mario'];
  let visita = null;
  let esperaVisita = 420;       // ~7 s depois de abrir

  function proximaVisita() {
    if (!filaDeVisitas.length) {
      filaDeVisitas = Object.keys(VISITAS);
      for (let i = filaDeVisitas.length - 1; i > 0; i--) {          // embaralha
        const j = Math.floor(aleatorio() * (i + 1));
        const troca = filaDeVisitas[i];
        filaDeVisitas[i] = filaDeVisitas[j];
        filaDeVisitas[j] = troca;
      }
    }
    return VISITAS[filaDeVisitas.shift()]();
  }

  function desenharVisitas(passo) {
    if (!visita) {
      esperaVisita -= passo;
      if (esperaVisita <= 0) visita = proximaVisita();
      return;
    }
    if (!visita.desenhar(passo)) {
      visita = null;
      esperaVisita = 1200 + aleatorio() * 900;      // 20 a 35 s
    }
  }

  // Para os testes chamarem uma visita na hora (testes\\teste_fundos_animados.py).
  window.__fundoClaro = {
    visitas: Object.keys(VISITAS),
    chamar: function (nome) { if (VISITAS[nome]) visita = VISITAS[nome](); return !!visita; },
    rodando: function () { return !!visita; },
    velocidade: function (v) { velocidade = Math.max(1, Math.min(16, Number(v) || 1)); return velocidade; },
    soltarCoelho: function () { esperaCoelho = 0; return true; }
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
    desenharJoaninha(passo);
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

  function sincronizar() {
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
    attributes: true, attributeFilter: ['data-tema', 'data-modo-modesto', 'data-fundo-animado']
  });
  // ...e a mudanca da preferencia do Windows (animacoes ligadas/desligadas).
  if (menosMovimento && menosMovimento.addEventListener) {
    menosMovimento.addEventListener('change', sincronizar);
  }
  setInterval(sincronizar, 3000);
})();
