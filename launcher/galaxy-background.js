(function () {
  const canvas = document.getElementById('galaxyCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  // Resolução interna "8-bit" do céu (baixa resolução, esticada via CSS)
  const W = 160, H = 90;
  canvas.width = W;
  canvas.height = H;
  ctx.imageSmoothingEnabled = false;

  // Se o navegador perder o contexto do canvas (comum depois de muito
  // tempo ligado, sono da GPU, etc.), evitamos que a tela fique
  // permanentemente travada: avisamos o navegador que sabemos lidar com
  // isso e restauramos as configurações quando ele volta.
  canvas.addEventListener('contextlost', function (e) {
    e.preventDefault();
  });
  canvas.addEventListener('contextrestored', function () {
    ctx.imageSmoothingEnabled = false;
  });

  const bgTones = ['#140027', '#1c0033', '#22003f', '#0d001c'];
  const bgBlocks = [];
  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      if (Math.random() < 0.35) {
        bgBlocks.push({ x, y, c: bgTones[Math.floor(Math.random() * bgTones.length)] });
      }
    }
  }

  const stars = [];
  for (let i = 0; i < 45; i++) {
    stars.push({
      x: Math.floor(Math.random() * W),
      y: Math.floor(Math.random() * H),
      phase: Math.random() * Math.PI * 2,
      speed: 0.05 + Math.random() * 0.06
    });
  }

  // ---- Aurora: faixas onduladas que pulsam de brilho devagar ----
  const auroraBands = [
    { baseY: 14, amp: 4, waveLen: 0.12, waveSpeed: 0.015, pulseSpeed: 0.01, phase: 0, cor: '120,255,180' },
    { baseY: 26, amp: 5, waveLen: 0.09, waveSpeed: 0.011, pulseSpeed: 0.008, phase: 2, cor: '180,140,255' }
  ];

  // ---- Nebulosas: nuvens coloridas grandes e translúcidas, à deriva ----
  const nebulaShapes = [
    [[0,0],[1,0],[2,0],[1,1],[2,1],[3,1],[0,1]],
    [[0,1],[1,0],[2,0],[3,0],[4,1],[1,1],[2,1],[3,1]]
  ];
  const nebulaCores = ['176,102,204', '102,176,204', '204,102,160'];
  const nebulas = [];
  for (let i = 0; i < 3; i++) {
    nebulas.push({
      shape: nebulaShapes[i % nebulaShapes.length],
      cor: nebulaCores[i % nebulaCores.length],
      x: Math.random() * W,
      y: 6 + Math.floor(Math.random() * 40),
      speed: 0.015 + Math.random() * 0.02,
      escala: 3
    });
  }

  let comet = null;

  function spawnComet() {
    const y = Math.floor(Math.random() * H * 0.6) + 5;
    comet = { x: -10, y: y, vx: 1.3 + Math.random() * 0.6, trail: [] };
  }

  function scheduleNext() {
    const delay = 10000 + Math.random() * 10000;
    setTimeout(function () {
      spawnComet();
      scheduleNext();
    }, delay);
  }

  setTimeout(spawnComet, 2500);
  scheduleNext();

  // ---- Mini OVNI com alienígena, passando de vez em quando ----
  let ufo = null;

  function spawnUfo() {
    const dir = Math.random() < 0.5 ? 1 : -1;
    ufo = {
      x: dir === 1 ? -20 : W + 20,
      y: 10 + Math.floor(Math.random() * 30),
      vx: dir * (0.5 + Math.random() * 0.3),
      dir: dir,
      wobblePhase: Math.random() * Math.PI * 2
    };
  }

  function scheduleUfo() {
    const delay = 15000 + Math.random() * 15000;
    setTimeout(function () {
      spawnUfo();
      scheduleUfo();
    }, delay);
  }

  setTimeout(spawnUfo, 6000);
  scheduleUfo();

  // Só desenha quando o canvas está de fato visível (tema escuro ligado).
  // O próprio script decide sua visibilidade via style.display (em vez de
  // depender só do CSS), pra nunca correr o risco de dois fundos
  // aparecerem sobrepostos por uma inconsistência entre script e CSS.
  function estaVisivel() {
    return document.body.dataset.tema === 'escuro';
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

    for (const b of bgBlocks) {
      ctx.fillStyle = b.c;
      ctx.fillRect(b.x, b.y, 1, 1);
    }

    for (const band of auroraBands) {
      const brilho = 0.06 + 0.08 * ((Math.sin(t * band.pulseSpeed + band.phase) + 1) / 2);
      for (let x = 0; x < W; x += 2) {
        const onda = Math.sin(x * band.waveLen + t * band.waveSpeed + band.phase) * band.amp;
        const y = Math.round(band.baseY + onda);
        ctx.fillStyle = 'rgba(' + band.cor + ',' + brilho.toFixed(2) + ')';
        ctx.fillRect(x, y, 2, 6);
      }
    }

    for (const neb of nebulas) {
      neb.x += neb.speed;
      if (neb.x > W + 20) neb.x = -20;
      const pulso = 0.10 + 0.08 * ((Math.sin(t * 0.015 + neb.y) + 1) / 2);
      ctx.fillStyle = 'rgba(' + neb.cor + ',' + pulso.toFixed(2) + ')';
      for (const px of neb.shape) {
        ctx.fillRect(Math.round(neb.x) + px[0] * neb.escala, neb.y + px[1] * neb.escala, neb.escala, neb.escala);
      }
    }

    for (const s of stars) {
      const a = (Math.sin(t * s.speed + s.phase) + 1) / 2;
      ctx.fillStyle = 'rgba(255,255,255,' + (0.1 + a * 0.9).toFixed(2) + ')';
      ctx.fillRect(s.x, s.y, 1, 1);
    }

    if (comet) {
      comet.trail.unshift({
        x: comet.x + (Math.random() - 0.5) * 0.8,
        y: comet.y + (Math.random() - 0.5) * 0.8,
        life: 1
      });

      const maxAge = 40;
      comet.trail = comet.trail.filter(function (p) {
        p.life -= 1 / maxAge;
        return p.life > 0;
      });

      const cols = ['255,255,255', '225,210,255', '190,170,255', '150,190,255'];
      for (let i = comet.trail.length - 1; i >= 0; i--) {
        const p = comet.trail[i];
        if (Math.random() < 0.15) continue;
        const flicker = 0.7 + Math.random() * 0.3;
        const a = Math.max(0, p.life * flicker);
        ctx.fillStyle = 'rgba(' + cols[i % cols.length] + ',' + a.toFixed(2) + ')';
        ctx.fillRect(Math.round(p.x), Math.round(p.y), 1, 1);
      }

      ctx.fillStyle = '#ffffff';
      ctx.fillRect(Math.round(comet.x), Math.round(comet.y), 2, 2);
      ctx.fillRect(Math.round(comet.x) + 1, Math.round(comet.y) - 1, 1, 1);

      comet.x += comet.vx;
      comet.y += 0.3;

      if (comet.x > W + 40 && comet.trail.length === 0) {
        comet = null;
      } else if (comet.x > W + 40) {
        comet.vx = 0;
      }
    }

    if (ufo) {
      const bob = Math.sin(t * 0.08 + ufo.wobblePhase) * 2;
      const ux = Math.round(ufo.x);
      const uy = Math.round(ufo.y + bob);

      ctx.fillStyle = 'rgba(120,220,255,0.35)';
      ctx.fillRect(ux - 4, uy + 1, 8, 2);

      ctx.fillStyle = '#9aa3b2';
      ctx.fillRect(ux - 3, uy + 1, 6, 1);
      ctx.fillStyle = '#c7ccd6';
      ctx.fillRect(ux - 4, uy + 2, 8, 1);

      ctx.fillStyle = '#7fe3d8';
      ctx.fillRect(ux - 1, uy - 1, 2, 2);

      ctx.fillStyle = (t % 20 < 10) ? '#ff5b5b' : '#7a1f1f';
      ctx.fillRect(ux + (ufo.dir === 1 ? 3 : -4), uy + 1, 1, 1);

      ctx.fillStyle = '#3ea38f';
      ctx.fillRect(ux, uy - 1, 1, 1);

      ufo.x += ufo.vx;
      if (ufo.dir === 1 && ufo.x > W + 20) ufo = null;
      if (ufo.dir === -1 && ufo.x < -20) ufo = null;
    }
    } catch (e) {
      console.error('Fundo galáctico: erro num frame, seguindo pro próximo.', e);
    }

    requestAnimationFrame(draw);
  }

  draw();

  // Vigia: se o loop de animação parar de rodar por qualquer motivo
  // (perda de contexto que escapou do tratamento acima, erro fora do
  // try/catch, travamento do navegador, etc.), detecta e reinicia
  // sozinho, sem precisar recarregar a página.
  setInterval(function () {
    if (document.visibilityState !== 'visible') return;
    const parado = performance.now() - ultimoFrame > 3000;
    if (parado) {
      console.warn('Fundo galáctico parado há mais de 3s, reiniciando o loop.');
      draw();
    }
  }, 2000);
})();
