(function () {
  const canvas = document.getElementById('fieldCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  // Resolução interna "8-bit" da cena (baixa resolução, esticada via CSS)
  const W = 160, H = 90;
  canvas.width = W;
  canvas.height = H;
  ctx.imageSmoothingEnabled = false;

  // Se o navegador perder o contexto do canvas, evitamos que a tela
  // fique permanentemente travada.
  canvas.addEventListener('contextlost', function (e) {
    e.preventDefault();
  });
  canvas.addEventListener('contextrestored', function () {
    ctx.imageSmoothingEnabled = false;
  });

  const horizonte = 52;

  // Faixas do céu, de cima pra baixo, tipo bandas de cor 8-bit
  const skyBands = [
    { y: 0, h: 18, c: '#8fd3ff' },
    { y: 18, h: 16, c: '#a9e0ff' },
    { y: 34, h: 18, c: '#c9edff' }
  ];

  // Faixas da grama, criando um degradê em blocos de verde
  const grassBands = [
    { y: horizonte, h: 8, c: '#8fd14f' },
    { y: horizonte + 8, h: 10, c: '#79bd3f' },
    { y: horizonte + 18, h: 20, c: '#5fa334' }
  ];

  // Textura da grama: pontinhos aleatórios um pouco mais escuros/claros
  const grassSpecks = [];
  for (let i = 0; i < 260; i++) {
    grassSpecks.push({
      x: Math.floor(Math.random() * W),
      y: horizonte + Math.floor(Math.random() * (H - horizonte)),
      c: Math.random() < 0.5 ? 'rgba(255,255,255,0.10)' : 'rgba(0,0,0,0.10)'
    });
  }

  // Nuvens: cada uma é um pequeno agrupamento de blocos brancos
  const cloudShapes = [
    [[0,1],[1,0],[2,0],[3,0],[4,1],[1,1],[2,1],[3,1]],
    [[0,0],[1,0],[2,0],[1,1],[2,1],[3,1],[0,1]],
    [[0,1],[1,0],[2,0],[3,1],[1,1],[2,1],[4,1],[5,1]]
  ];
  const clouds = [];
  for (let i = 0; i < 3; i++) {
    clouds.push({
      shape: cloudShapes[i % cloudShapes.length],
      x: Math.random() * W,
      y: 4 + Math.floor(Math.random() * 22),
      speed: 0.05 + Math.random() * 0.05
    });
  }

  // Girassóis: linha ao longo da grama, cada um com fase própria de balanço
  const sunflowers = [];
  const count = 11;
  for (let i = 0; i < count; i++) {
    sunflowers.push({
      baseX: 6 + i * ((W - 12) / (count - 1)) + (Math.random() - 0.5) * 4,
      baseY: H - 4 - Math.floor(Math.random() * 6),
      stemH: 12 + Math.floor(Math.random() * 8),
      phase: Math.random() * Math.PI * 2,
      speed: 0.02 + Math.random() * 0.015
    });
  }
  sunflowers.sort(function (a, b) { return a.baseY - b.baseY; });

  // Posição do "alvo" (miolo da flor) de um girassol no frame atual,
  // acompanhando o mesmo balanço usado no desenho do caule.
  function posicaoFlor(f, frame) {
    const sway = Math.sin(frame * f.speed + f.phase) * 2.2;
    return {
      x: f.baseX + sway,
      y: f.baseY - f.stemH - 2
    };
  }

  // ---- Borboleta: visita uma flor, cheira ela por um tempo, vai embora
  // e depois volta pra uma flor diferente da anterior ----
  let borboleta = null;
  let ultimaFlorVisitada = -1;

  function sortearFlorDiferente() {
    if (sunflowers.length <= 1) return 0;
    let idx;
    do {
      idx = Math.floor(Math.random() * sunflowers.length);
    } while (idx === ultimaFlorVisitada);
    return idx;
  }

  function iniciarVisita() {
    const idx = sortearFlorDiferente();
    ultimaFlorVisitada = idx;
    const lado = Math.random() < 0.5 ? -1 : 1;
    borboleta = {
      estado: 'entrando',
      florIndex: idx,
      x: lado === 1 ? -8 : W + 8,
      y: 8 + Math.random() * 25,
      idade: 0,
      duracaoCheirar: 180 + Math.random() * 240,
      ladoSaida: Math.random() < 0.5 ? -1 : 1,
      faseAsa: Math.random() * Math.PI * 2
    };
  }

  function agendarProximaVisita(atraso) {
    setTimeout(iniciarVisita, atraso);
  }

  agendarProximaVisita(3000 + Math.random() * 3000);

  function estaVisivel() {
    return document.body.dataset.tema !== 'escuro';
  }

  let t = 0;
  let ultimoFrame = performance.now();

  function draw() {
    ultimoFrame = performance.now();

    const visivel = estaVisivel();
    canvas.style.display = visivel ? 'block' : 'none';

    if (!visivel) {
      requestAnimationFrame(draw);
      return;
    }

    try {
      t += 1;
      ctx.clearRect(0, 0, W, H);

    for (const b of skyBands) {
      ctx.fillStyle = b.c;
      ctx.fillRect(0, b.y, W, b.h);
    }

    for (const cloud of clouds) {
      cloud.x += cloud.speed;
      if (cloud.x > W + 10) cloud.x = -10;
      ctx.fillStyle = 'rgba(255,255,255,0.9)';
      for (const px of cloud.shape) {
        ctx.fillRect(Math.round(cloud.x) + px[0] * 2, cloud.y + px[1] * 2, 2, 2);
      }
    }

    for (const b of grassBands) {
      ctx.fillStyle = b.c;
      ctx.fillRect(0, b.y, W, b.h);
    }
    for (const s of grassSpecks) {
      ctx.fillStyle = s.c;
      ctx.fillRect(s.x, s.y, 1, 1);
    }

    for (const f of sunflowers) {
      const sway = Math.sin(t * f.speed + f.phase) * 2.2;
      const topX = f.baseX + sway;
      const topY = f.baseY - f.stemH;
      const midX = f.baseX + sway * 0.5;
      const midY = f.baseY - f.stemH * 0.5;

      ctx.strokeStyle = '#3f7d2b';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(f.baseX, f.baseY);
      ctx.lineTo(midX, midY);
      ctx.lineTo(topX, topY);
      ctx.stroke();

      ctx.fillStyle = '#3f7d2b';
      ctx.fillRect(Math.round(midX) - 2, Math.round(midY), 2, 1);
      ctx.fillRect(Math.round(midX) + 1, Math.round(midY) - 2, 2, 1);

      ctx.fillStyle = '#f4c430';
      const hx = Math.round(topX), hy = Math.round(topY - 2);
      ctx.fillRect(hx - 2, hy - 1, 5, 1);
      ctx.fillRect(hx - 1, hy - 2, 3, 3);
      ctx.fillRect(hx - 2, hy, 5, 1);

      ctx.fillStyle = '#6b4423';
      ctx.fillRect(hx - 1, hy - 1, 3, 2);
    }

    if (borboleta) {
      borboleta.idade += 1;
      const alvo = posicaoFlor(sunflowers[borboleta.florIndex], t);

      if (borboleta.estado === 'entrando') {
        borboleta.x += (alvo.x - borboleta.x) * 0.06;
        borboleta.y += (alvo.y - borboleta.y) * 0.06;
        if (Math.abs(alvo.x - borboleta.x) < 1.2 && Math.abs(alvo.y - borboleta.y) < 1.2) {
          borboleta.estado = 'cheirando';
          borboleta.idade = 0;
        }
      } else if (borboleta.estado === 'cheirando') {
        borboleta.x = alvo.x + Math.sin(t * 0.12) * 0.5;
        borboleta.y = alvo.y + Math.sin(t * 0.18) * 0.5;
        if (borboleta.idade > borboleta.duracaoCheirar) {
          borboleta.estado = 'saindo';
          borboleta.idade = 0;
        }
      } else if (borboleta.estado === 'saindo') {
        const destinoX = borboleta.ladoSaida === 1 ? W + 12 : -12;
        borboleta.x += (destinoX - borboleta.x) * 0.05;
        borboleta.y += Math.sin(t * 0.06) * 0.4;
        const saiu = borboleta.ladoSaida === 1 ? borboleta.x > W + 8 : borboleta.x < -8;
        if (saiu) {
          borboleta = null;
          agendarProximaVisita(4000 + Math.random() * 6000);
        }
      }

      if (borboleta) {
        const bx = Math.round(borboleta.x);
        const by = Math.round(borboleta.y);
        const flap = 1 + Math.round(Math.abs(Math.sin(t * 0.35 + borboleta.faseAsa)) * 2);

        ctx.fillStyle = '#ff9f43';
        ctx.fillRect(bx - flap, by - 1, flap, 2);
        ctx.fillRect(bx + 1, by - 1, flap, 2);

        ctx.fillStyle = '#2b1c12';
        ctx.fillRect(bx, by - 1, 1, 2);
      }
    }
    } catch (e) {
      console.error('Fundo de campo: erro num frame, seguindo pro próximo.', e);
    }

    requestAnimationFrame(draw);
  }

  draw();

  setInterval(function () {
    if (document.visibilityState !== 'visible') return;
    const parado = performance.now() - ultimoFrame > 3000;
    if (parado) {
      console.warn('Fundo de campo parado há mais de 3s, reiniciando o loop.');
      draw();
    }
  }, 2000);
})();
