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

  // ------------------------------------------------------------------
  // Mais visitas de 16 bits (lote campo-a, 13/10/2026): Yoshi, Link,
  // o Wiggler, o Monty Mole e o Lakitu.
  // ------------------------------------------------------------------
  // Yoshi (Super Mario World, SNES, 1990): vem correndo pela grama, para
  // diante de uma frutinha vermelha, estica a lingua, come e segue feliz.
  // G verde, d verde escuro, W branco, K olho, R sela, O espinhos e botas.
  const PALETA_YOSHI = { G: '#4cd640', d: '#219a34', W: '#ffffff', K: '#101010', R: '#ee3226', O: '#f68a1e',
                         k: '#0f3a16' };
  const YOSHI = S.quadros([
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
  ], PALETA_YOSHI);
  const FRUTA_YOSHI = S.fazer([
    '.gl.',
    'RWRR',
    'RRRD',
    '.DD.'
  ], { l: '#4caf3a', R: '#ee2030', W: '#ffd6d6', D: '#a01020', g: '#2e7d1f' });
  const CORACAO_YOSHI = [[0, 0], [1, 0], [3, 0], [4, 0], [0, 1], [1, 1], [2, 1], [3, 1], [4, 1],
                         [1, 2], [2, 2], [3, 2], [2, 3]];

  function iniciarYoshi() {
    const dir = aleatorio() < 0.5 ? 1 : -1;
    return { dir: dir, x: dir === 1 ? -YOSHI[0].w : W, fase: 'correndo', relogio: 0,
             fruta: Math.round(62 + aleatorio() * 34), lingua: 0, puxou: false, comeu: false,
             haste: 1, balanco: 0, poeira: [], coracao: -1, desenhar: desenharYoshi };
  }

  function desenharYoshi(passo) {
    const w = YOSHI[0].w, topo = CHAO - YOSHI[0].h;
    const boca = this.dir === 1 ? this.x + 10 : this.x + w - 11;    // de onde a lingua sai
    const alcance = this.dir === 1 ? this.fruta + 3 - boca : boca - this.fruta;
    let quadro = YOSHI[1];
    this.relogio += passo;
    if (this.fase === 'correndo') {
      this.x += this.dir * 0.6 * passo;
      quadro = YOSHI[Math.floor(t / 4) % 2];
      if (!this.comeu && alcance <= 11) { this.fase = 'parando'; this.relogio = 0; }
      if (this.comeu) this.haste = Math.max(0, this.haste - passo / 90);   // o talo vazio some aos poucos
    } else if (this.fase === 'parando') {
      if (this.relogio >= 10) { this.fase = 'lingua'; this.relogio = 0; }
    } else if (this.fase === 'lingua') {
      quadro = YOSHI[2];
      const p = Math.min(1, this.relogio / 20);                     // estica e recolhe
      this.lingua = Math.max(1, Math.round(Math.sin(p * Math.PI) * alcance));
      if (p >= 0.5 && !this.puxou) { this.puxou = true; this.balanco = 1; }
      if (p >= 1) { this.fase = 'mastigando'; this.relogio = 0; this.comeu = true; }
    } else if (this.fase === 'mastigando') {
      quadro = Math.floor(this.relogio / 6) % 2 === 0 ? YOSHI[3] : YOSHI[1];
      if (this.relogio >= 42) { this.fase = 'correndo'; this.coracao = 0; }
    }
    // O talo da frutinha (balanca quando ela e' arrancada).
    if (this.haste > 0) {
      this.balanco = Math.max(0, this.balanco - passo / 30);
      const hx = this.fruta + 1, a = this.haste.toFixed(2);
      const torto = Math.round(Math.sin(t * 0.9) * 1.4 * this.balanco);
      ctx.fillStyle = 'rgba(46,125,31,' + a + ')';
      ctx.fillRect(hx, CHAO - 4, 1, 4);
      ctx.fillRect(hx + torto, CHAO - 7, 1, 3);
      ctx.fillStyle = 'rgba(76,175,58,' + a + ')';
      ctx.fillRect(hx - 1, CHAO - 3, 1, 1);
      ctx.fillRect(hx + 1, CHAO - 5, 1, 1);
    }
    if (!this.puxou) S.colar(ctx, FRUTA_YOSHI, this.fruta, CHAO - 11, 1);
    // Poeira das botas.
    const fora = this.dir === 1 ? this.x > W + 1 : this.x < -w - 1;
    if (passo && this.fase === 'correndo' && !fora && aleatorio() < 0.5) {
      this.poeira.push({ x: this.x + (this.dir === 1 ? 3 : w - 4), y: CHAO - 1, vida: 1 });
    }
    for (const p of this.poeira) { p.vida -= 0.05 * passo; p.y -= 0.05 * passo; }
    this.poeira = this.poeira.filter(function (p) { return p.vida > 0; });
    for (const p of this.poeira) {
      ctx.fillStyle = 'rgba(255,255,255,' + (p.vida * 0.6).toFixed(2) + ')';
      ctx.fillRect(Math.round(p.x), Math.round(p.y), 1, 1);
    }
    S.colar(ctx, quadro, this.x, topo, this.dir);
    // A lingua cor-de-rosa (ponta mais grossa), com a fruta presa na volta.
    if (this.fase === 'lingua') {
      const ponta = this.dir === 1 ? boca + this.lingua - 1 : boca - this.lingua + 1;
      ctx.fillStyle = '#ff6a9a';
      ctx.fillRect(Math.round(this.dir === 1 ? boca : ponta), topo + 7, this.lingua, 1);
      ctx.fillRect(Math.round(this.dir === 1 ? ponta - 1 : ponta), topo + 7, 2, 2);
      if (this.puxou) S.colar(ctx, FRUTA_YOSHI, ponta - (this.dir === 1 ? 2 : 1), CHAO - 11, 1);
    }
    // Coracaozinho (que delicia!) subindo e sumindo.
    if (this.coracao >= 0 && this.coracao < 50) {
      this.coracao += passo;
      ctx.fillStyle = 'rgba(255,92,138,' + Math.max(0, 1 - this.coracao / 50).toFixed(2) + ')';
      const cx = Math.round(this.x + (this.dir === 1 ? 4 : w - 9)), cy = Math.round(topo - 4 - this.coracao / 8);
      for (const p of CORACAO_YOSHI) ctx.fillRect(cx + p[0], cy + p[1], 1, 1);
    }
    return !(fora && this.haste <= 0 && !this.poeira.length && (this.coracao < 0 || this.coracao >= 50));
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

  // Donkey Kong Country (SNES, 1994): o Donkey Kong passa rolando (o ataque
  // de rolar) e o Diddy Kong vem correndo atras e pula para pegar a banana
  // que gira no ar.
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
  const DIDDY = S.quadros([
    ['....RRRR....',
     '...RRRRRR...',
     '...RRRRRRRR.',
     '..TBTTWKT...',
     '..TBTTTTTT..',
     '...BBTTTT...',
     '.B.BRYRB....',
     'B..BRRRBT...',
     'B...RRRR....',
     '.BBBB..BB...',
     '..TT....TT..'],
    ['....RRRR....',
     '...RRRRRR...',
     '...RRRRRRRR.',
     '..TBTTWKT...',
     '..TBTTTTTT..',
     '...BBTTTT...',
     '.B.BRYRB....',
     'B..BRRRBT...',
     'B...RRRR....',
     '.BB.BBB.....',
     '....TTT.....'],
    ['....RRRR....',
     '...RRRRRR..T',
     '...RRRRRRRRB',
     '..TBTTWKT.B.',
     '..TBTTTTTB..',
     '...BBTTTB...',
     '.B.BRYRB....',
     'B..BRRRR....',
     'B...RRRR....',
     '.BBB..BB....',
     '..TT...TT...']
  ], { R: '#e02a2a', B: '#7a4018', T: '#f0b878', K: '#1a0e06', Y: '#ffd23f', W: '#ffffff' });
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

  function iniciarDonkey() {
    const dir = aleatorio() < 0.5 ? 1 : -1;
    return { dir: dir, x: dir === 1 ? -16 : W + 2, giro: 0,
             diddy: dir === 1 ? -46 : W + 32, altura: 0, vy: 0, noAr: false,
             banana: { x: 55 + aleatorio() * 50, pega: -1 }, poeira: [], desenhar: desenharDonkey };
  }

  function desenharDonkey(passo) {
    this.x += this.dir * 0.95 * passo;
    this.giro += 0.95 * passo;
    this.diddy += this.dir * 0.85 * passo;
    // O Diddy pula com a banana logo a frente: o alto do pulo cai em cima dela.
    const meio = this.banana.x + 3;
    const ate = this.dir === 1 ? meio - (this.diddy + 6) : (this.diddy + 6) - meio;
    if (!this.noAr && this.banana.pega < 0 && ate > 0 && ate < 14) { this.noAr = true; this.vy = 1.7; }
    if (this.noAr) {
      this.altura += this.vy * passo;
      this.vy -= 0.11 * passo;
      if (this.altura <= 0) { this.altura = 0; this.noAr = false; }
    }
    if (this.banana.pega < 0 && this.altura > 6 && Math.abs(this.diddy + 6 - meio) < 5) this.banana.pega = 0;
    if (this.banana.pega < 0) {
      const g = GIRO_BANANA[Math.floor(t / 5) % 8];
      S.colar(ctx, BANANA_DKC[g[0]], this.banana.x, CHAO - 23 + Math.round(Math.sin(t * 0.08)), g[1]);
    } else if (this.banana.pega < 24) {                 // estrelinha onde estava a banana
      this.banana.pega += passo;
      const r = 1 + Math.floor(this.banana.pega / 6);
      const y = CHAO - 20;
      ctx.fillStyle = 'rgba(255,240,140,' + Math.max(0, 1 - this.banana.pega / 24).toFixed(2) + ')';
      ctx.fillRect(Math.round(meio), y, 1, 1);
      ctx.fillRect(Math.round(meio) - r, y, 1, 1);
      ctx.fillRect(Math.round(meio) + r, y, 1, 1);
      ctx.fillRect(Math.round(meio), y - r, 1, 1);
      ctx.fillRect(Math.round(meio), y + r, 1, 1);
    }
    // Poeira de terra levantada pelo rolamento.
    const rolando = this.dir === 1 ? this.x < W + 2 : this.x > -16;
    if (passo && rolando && aleatorio() < 0.5) {
      this.poeira.push({ x: this.x + (this.dir === 1 ? 3 : 10), y: CHAO - 1 - Math.floor(aleatorio() * 2), vida: 1 });
    }
    for (const p of this.poeira) { p.vida -= 0.06 * passo; p.y -= 0.04 * passo; }
    this.poeira = this.poeira.filter(function (p) { return p.vida > 0; });
    for (const p of this.poeira) {
      ctx.fillStyle = 'rgba(232,212,160,' + (p.vida * 0.7).toFixed(2) + ')';
      ctx.fillRect(Math.round(p.x), Math.round(p.y), 1, 1);
    }
    // Um quarto de volta a cada ~9 pontos andados (a bola tem 12 de largura).
    S.colar(ctx, DONKEY[Math.floor(this.giro / 9) % 4], this.x, CHAO - 13, this.dir);
    const diddy = this.noAr ? DIDDY[2] : DIDDY[Math.floor(t / 4) % 2];
    S.colar(ctx, diddy, this.diddy, CHAO - diddy.h - this.altura, this.dir);
    const diddyFora = this.dir === 1 ? this.diddy > W + 2 : this.diddy < -14;
    return rolando || !diddyFora || this.poeira.length > 0;
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

  const VISITAS = { mario: iniciarMario, sonic: iniciarSonic, duckhunt: iniciarDuckHunt, kirby: iniciarKirby,
                    yoshi: iniciarYoshi, link: iniciarLink, wiggler: iniciarWiggler, monty: iniciarMonty, lakitu: iniciarLakitu, donkey: iniciarDonkey, tails: iniciarTails, knuckles: iniciarKnuckles, chocobo: iniciarChocobo, rabites: iniciarRabites, saturno: iniciarSaturno };
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
      // 20 a 35 s; no "Visualizar animação", 1,5 a 4 s (quem abriu quer ver).
      esperaVisita = soFundo() ? 90 + aleatorio() * 150 : 1200 + aleatorio() * 900;
    }
  }

  function soFundo() { return document.body.dataset.soFundo === 'true'; }
  let gravando = false;

  // Para os testes chamarem uma visita na hora (testes\\teste_fundos_animados.py).
  window.__fundoClaro = {
    visitas: Object.keys(VISITAS),
    chamar: function (nome) { if (VISITAS[nome]) visita = VISITAS[nome](); return !!visita; },
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
