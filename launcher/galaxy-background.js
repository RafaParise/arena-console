// ==========================================================================
// ARENA - fundo do tema ESCURO: um ceu de galaxia em pixel art (canvas).
//
// Mesmo esquema do field-background.js (leia o comentario de la):
// 160 x 90 pontos esticados pelo CSS, camada fixa desenhada uma vez,
// 20 quadros por segundo por relogio (o porque, com os numeros, esta la, no
// item 3), e tres jeitos de mostrar (automatico, sempre,
// parado) -- a cena aparece SEMPRE; o que muda e' so se ela se mexe.
//
// Achado de 01/10/2026: antes, o ceu desenhava ~5.000 quadradinhos de
// fundo a cada quadro (60 por segundo). Agora eles vivem na camada fixa e
// custam uma operacao so por quadro.
//
// 02/10/2026 (Rafael): as "borboletas de luz" nao tinham nada a ver com o
// espaco -- viraram Metroides (do Metroid, NES). E o ceu ganhou visitas de
// jogos famosos de 8 e 16 bits, uma de cada vez: a corrida das quatro
// maquinas do F-Zero (SNES), o Kirby na Warp Star (NES), os Space Invaders
// e a Arwing do Star Fox (SNES). Os desenhos usam launcher\pixel-sprites.js
// (escritos como texto, pintados uma vez, so colados a cada quadro).
// ==========================================================================
(function () {
  const canvas = document.getElementById('galaxyCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const S = window.SpritesRetro;

  const W = 160, H = 90;
  canvas.width = W;
  canvas.height = H;
  ctx.imageSmoothingEnabled = false;

  let semente = 19851013;
  function sorteio() {
    semente = (semente * 1103515245 + 12345) & 0x7fffffff;
    return semente / 0x7fffffff;
  }
  const aleatorio = Math.random;

  // ------------------------------------------------------------------
  // Camada fixa
  // ------------------------------------------------------------------
  const fixa = document.createElement('canvas');
  fixa.width = W;
  fixa.height = H;
  const fctx = fixa.getContext('2d');

  function serra(x) {          // perfil das montanhas la embaixo
    return H - 6 - Math.round(4 * Math.abs(Math.sin(x * 0.045)) + 3 * Math.abs(Math.sin(x * 0.11 + 1)));
  }

  function desenharCamadaFixa() {
    const c = fctx;
    c.fillStyle = '#0b0d17';
    c.fillRect(0, 0, W, H);
    const tons = ['#140027', '#1c0033', '#22003f', '#0d001c'];
    for (let y = 0; y < H; y++) {
      for (let x = 0; x < W; x++) {
        if (sorteio() < 0.35) {
          c.fillStyle = tons[Math.floor(sorteio() * tons.length)];
          c.fillRect(x, y, 1, 1);
        }
      }
    }
    // Estrelas apagadinhas, paradas, la no fundo.
    for (let i = 0; i < 90; i++) {
      c.fillStyle = 'rgba(255,255,255,' + (0.18 + sorteio() * 0.25).toFixed(2) + ')';
      c.fillRect(Math.floor(sorteio() * W), Math.floor(sorteio() * (H - 12)), 1, 1);
    }
    // Lua crescente com crateras.
    const lx = 22, ly = 13;
    for (let y = -6; y <= 6; y++) {
      for (let x = -6; x <= 6; x++) {
        const dentro = x * x + y * y <= 36;
        const sombra = (x - 3) * (x - 3) + (y + 1) * (y + 1) <= 30;
        if (dentro && !sombra) {
          c.fillStyle = '#f4f1d0';
          c.fillRect(lx + x, ly + y, 1, 1);
        }
      }
    }
    c.fillStyle = '#d8d3a8';
    c.fillRect(lx - 4, ly - 1, 1, 1);
    c.fillRect(lx - 3, ly + 3, 1, 1);
    c.fillRect(lx - 5, ly + 2, 1, 1);
    // Montanhas escuras: dao "chao" para o foguete subir.
    for (let x = 0; x < W; x++) {
      const topo = serra(x);
      c.fillStyle = '#07040f';
      c.fillRect(x, topo, 1, H - topo);
      c.fillStyle = '#150b2e';
      c.fillRect(x, topo, 1, 1);
    }
  }
  desenharCamadaFixa();

  canvas.addEventListener('contextlost', function (e) { e.preventDefault(); });
  canvas.addEventListener('contextrestored', function () {
    ctx.imageSmoothingEnabled = false;
    desenharCamadaFixa();
    desenharQuadro(0);
  });

  // ------------------------------------------------------------------
  // O que se mexe
  // ------------------------------------------------------------------
  let t = 0;

  // Cores com transparencia, prontas: 21 tons por cor (de 0 a 1, de 0,05
  // em 0,05). Montar o texto 'rgba(...)' a cada estrela, a cada quadro,
  // criava centenas de textos por segundo para o navegador recolher.
  const tabelaCores = {};
  function rgba(rgb, alfa) {
    let lista = tabelaCores[rgb];
    if (!lista) {
      lista = tabelaCores[rgb] = [];
      for (let i = 0; i <= 20; i++) lista.push('rgba(' + rgb + ',' + (i / 20) + ')');
    }
    return lista[Math.max(0, Math.min(20, Math.round(alfa * 20)))];
  }

  const estrelas = [];
  for (let i = 0; i < 45; i++) {
    estrelas.push({ x: Math.floor(sorteio() * W), y: Math.floor(sorteio() * (H - 14)),
                    fase: sorteio() * Math.PI * 2, vel: 0.05 + sorteio() * 0.06 });
  }
  // Estrelas grandes, com quatro pontas que piscam.
  const brilhantes = [];
  for (let i = 0; i < 6; i++) {
    brilhantes.push({ x: 6 + Math.floor(sorteio() * (W - 12)), y: 4 + Math.floor(sorteio() * 45),
                      fase: sorteio() * Math.PI * 2, vel: 0.02 + sorteio() * 0.02 });
  }

  // Constelacao: estrelas ligadas por linhas que aparecem e somem devagar.
  const constelacao = [[118, 8], [126, 14], [134, 11], [141, 18], [131, 22], [146, 9]];
  const ligacoes = [[0, 1], [1, 2], [2, 3], [1, 4], [2, 5]];

  const aurora = [
    { y: 14, amp: 4, onda: 0.12, velOnda: 0.015, pulso: 0.01, fase: 0, cor: '120,255,180' },
    { y: 26, amp: 5, onda: 0.09, velOnda: 0.011, pulso: 0.008, fase: 2, cor: '180,140,255' }
  ];

  // Nebulosas: nuvens redondas e transparentes. Cada uma e' desenhada UMA
  // vez na sua propria camada e so arrastada a cada quadro.
  function fazerNebulosa(cor, raio) {
    const tela = document.createElement('canvas');
    tela.width = raio * 4;
    tela.height = raio * 2 + 2;
    const c = tela.getContext('2d');
    const bolhas = [[raio, raio, raio], [raio * 2, raio * 0.8, raio * 0.8], [raio * 2.9, raio * 1.1, raio * 0.7]];
    c.fillStyle = 'rgba(' + cor + ',0.07)';
    for (const [cx, cy, r] of bolhas) {
      for (let camada = 0; camada < 3; camada++) {       // mais densa no meio
        const rr = r * (1 - camada * 0.3);
        for (let y = -Math.floor(rr); y <= Math.floor(rr); y++) {
          const meia = Math.floor(Math.sqrt(rr * rr - y * y));
          c.fillRect(Math.round(cx - meia), Math.round(cy + y), meia * 2 + 1, 1);
        }
      }
    }
    return tela;
  }
  const coresNebulosa = ['176,102,204', '102,176,204', '204,102,160'];
  const nebulosas = [];
  for (let i = 0; i < 3; i++) {
    nebulosas.push({ tela: fazerNebulosa(coresNebulosa[i], 5 + Math.floor(sorteio() * 3)),
                     x: sorteio() * W, y: 4 + Math.floor(sorteio() * 40), vel: 0.012 + sorteio() * 0.015 });
  }

  // Planeta com anel, atravessando o ceu bem devagar (uns 4 minutos).
  const planeta = { x: W * 0.72, y: 58 };

  function desenharPlaneta(passo) {
    planeta.x -= 0.011 * passo;
    if (planeta.x < -12) planeta.x = W + 12;
    const x = Math.round(planeta.x), y = planeta.y;
    ctx.fillStyle = '#e09f5a';
    ctx.fillRect(x - 3, y - 2, 7, 5);
    ctx.fillRect(x - 2, y - 3, 5, 7);
    ctx.fillStyle = '#c47b3e';
    ctx.fillRect(x - 3, y, 7, 1);
    ctx.fillStyle = 'rgba(255,230,180,0.85)';
    ctx.fillRect(x - 6, y + 1, 3, 1);
    ctx.fillRect(x + 4, y - 1, 3, 1);
    ctx.fillRect(x - 3, y + 1, 7, 1);
  }

  // Metroides (do Metroid, NES 1986): criaturas do espaco que flutuam em oito,
  // brilhando -- no lugar das "borboletas de luz" (02/10/2026: o Rafael viu
  // que borboleta nao tinha nada a ver com o espaco). A membrana pulsa e as
  // presas abrem e fecham.
  const PALETA_METROIDE = { G: '#7dff8a', m: 'rgba(150,255,160,0.45)', R: '#ff4060', b: '#a08a3a', W: '#fff1c2' };
  const QUADROS_METROIDE = S.quadros([
    ['...GGGGG...',
     '..GmmmmmG..',
     '.GmRRmRRmG.',
     'GmmRRmRRmmG',
     'GmmmmRRmmmG',
     'GmmmmRRmmmG',
     '.GGGGGGGGG.',
     '..WbbbbbW..',
     '.WW.W.W.WW.',
     '.W..W.W..W.'],
    ['...........',
     '...GGGGG...',
     '.GGmRRmRGG.',
     'GmmmRRmRRmG',
     'GmmRRmmmmmG',
     'GmmmmRRmmmG',
     '.GGGGGGGGG.',
     '..WbbbbbW..',
     '..WW.W.WW..',
     '...W.W.W...']
  ], PALETA_METROIDE);

  // O brilho em volta: uma bolha verde transparente, pintada uma vez.
  const halo = document.createElement('canvas');
  halo.width = 17;
  halo.height = 15;
  (function () {
    const c = halo.getContext('2d');
    for (let y = 0; y < 15; y++) {
      for (let x = 0; x < 17; x++) {
        const d = Math.sqrt(Math.pow((x - 8) / 8.5, 2) + Math.pow((y - 7) / 7.5, 2));
        if (d < 1) {
          c.fillStyle = 'rgba(125,255,138,' + (0.22 * (1 - d)).toFixed(3) + ')';
          c.fillRect(x, y, 1, 1);
        }
      }
    }
  })();

  const metroides = [];
  for (let i = 0; i < 2; i++) {
    metroides.push({ fase: sorteio() * 6.28, cx: 40 + i * 72, cy: 31 + sorteio() * 8,
                     raioX: 18 + sorteio() * 12, raioY: 7 + sorteio() * 5, vel: 0.005 + sorteio() * 0.003,
                     x: 0, y: 0, esporos: [] });
  }

  function desenharMetroides(passo) {
    for (const m of metroides) {
      const a = t * m.vel + m.fase;
      m.x = m.cx + Math.sin(a) * m.raioX;
      m.y = m.cy + Math.sin(a * 2) * m.raioY;
      // Esporos: pontinhos verdes que ficam para tras e somem.
      if (passo && aleatorio() < 0.12 * passo) {
        m.esporos.push({ x: m.x + (aleatorio() - 0.5) * 6, y: m.y + 4, vida: 1 });
      }
      for (const e of m.esporos) { e.vida -= 0.02 * passo; e.y += 0.04 * passo; }
      m.esporos = m.esporos.filter(function (e) { return e.vida > 0; });
      for (const e of m.esporos) {
        ctx.fillStyle = rgba('125,255,138', e.vida * 0.5);
        ctx.fillRect(Math.round(e.x), Math.round(e.y), 1, 1);
      }
      const quadro = QUADROS_METROIDE[Math.floor((t + m.fase * 40) / 18) % 2];
      ctx.globalAlpha = 0.7 + 0.3 * Math.sin(t * 0.08 + m.fase);
      ctx.drawImage(halo, Math.round(m.x - 8.5), Math.round(m.y - 7.5));
      ctx.globalAlpha = 1;
      S.colar(ctx, quadro, m.x - quadro.w / 2, m.y - quadro.h / 2, 1);
    }
  }

  // Galaxia espiral, la no fundo, dando uma volta a cada ~3 minutos.
  const galaxia = { x: 94, y: 30, pontos: [] };
  for (let braco = 0; braco < 2; braco++) {
    for (let k = 0; k < 16; k++) {
      galaxia.pontos.push({ ang: braco * Math.PI + k * 0.38, raio: 0.8 + k * 0.42, brilho: 1 - k / 18 });
    }
  }

  function desenharGalaxia() {
    ctx.fillStyle = rgba('255,240,255', 0.6);
    ctx.fillRect(galaxia.x, galaxia.y, 1, 1);
    const giro = t * 0.0006;
    for (const p of galaxia.pontos) {
      const a = p.ang + giro;
      ctx.fillStyle = rgba('205,185,255', 0.1 + p.brilho * 0.32);
      ctx.fillRect(Math.round(galaxia.x + Math.cos(a) * p.raio * 1.7),
                   Math.round(galaxia.y + Math.sin(a) * p.raio * 0.7), 1, 1);
    }
  }

  // Cometa (de 10 em 10 a 20 s)
  let cometa = null;
  let esperaCometa = 150;

  function desenharCometa(passo) {
    if (!cometa) {
      esperaCometa -= passo;
      if (esperaCometa <= 0) {
        cometa = { x: -10, y: Math.floor(aleatorio() * H * 0.5) + 5, vx: 1.3 + aleatorio() * 0.6, rastro: [] };
        esperaCometa = 600 + aleatorio() * 600;
      }
      return;
    }
    if (passo) {
      cometa.rastro.unshift({ x: cometa.x + (aleatorio() - 0.5) * 0.8, y: cometa.y + (aleatorio() - 0.5) * 0.8, vida: 1 });
      for (const p of cometa.rastro) p.vida -= passo / 40;
      cometa.rastro = cometa.rastro.filter(function (p) { return p.vida > 0; });
    }
    const cores = ['255,255,255', '225,210,255', '190,170,255', '150,190,255'];
    for (let i = cometa.rastro.length - 1; i >= 0; i--) {
      const p = cometa.rastro[i];
      ctx.fillStyle = rgba(cores[i % cores.length], p.vida * 0.85);
      ctx.fillRect(Math.round(p.x), Math.round(p.y), 1, 1);
    }
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(Math.round(cometa.x), Math.round(cometa.y), 2, 2);
    cometa.x += cometa.vx * passo;
    cometa.y += 0.3 * passo;
    if (cometa.x > W + 40 && !cometa.rastro.length) cometa = null;
    else if (cometa.x > W + 40) cometa.vx = 0;
  }

  // Chuva de meteoros: de vez em quando, varios riscos rapidos juntos.
  let meteoros = [];
  let esperaChuva = 900 + sorteio() * 900;

  function desenharMeteoros(passo) {
    if (!meteoros.length) {
      esperaChuva -= passo;
      if (esperaChuva <= 0) {
        const n = 4 + Math.floor(aleatorio() * 4);
        for (let i = 0; i < n; i++) {
          meteoros.push({ x: 40 + aleatorio() * 120, y: -aleatorio() * 30, atraso: i * (10 + aleatorio() * 25) });
        }
        esperaChuva = 1800 + aleatorio() * 1800;
      }
      return;
    }
    for (const m of meteoros) {
      if (m.atraso > 0) { m.atraso -= passo; continue; }
      m.x -= 2.2 * passo;
      m.y += 1.6 * passo;
      for (let k = 0; k < 6; k++) {
        ctx.fillStyle = rgba('255,255,255', 0.9 - k * 0.14);
        ctx.fillRect(Math.round(m.x + k * 1.4), Math.round(m.y - k), 1, 1);
      }
    }
    meteoros = meteoros.filter(function (m) { return m.atraso > 0 || (m.y < H && m.x > -8); });
  }

  // OVNI: passa de vez em quando; as vezes para e acende o feixe de luz.
  let ovni = null;
  let esperaOvni = 360;

  function desenharOvni(passo) {
    if (!ovni) {
      esperaOvni -= passo;
      if (esperaOvni <= 0) {
        const dir = aleatorio() < 0.5 ? 1 : -1;
        ovni = { dir: dir, x: dir === 1 ? -20 : W + 20, y: 10 + Math.floor(aleatorio() * 30),
                 vx: dir * (0.5 + aleatorio() * 0.3), fase: aleatorio() * 6,
                 parada: aleatorio() < 0.4 ? 40 + aleatorio() * 80 : -1, feixe: 0 };
        esperaOvni = 900 + aleatorio() * 900;
      }
      return;
    }
    const oscila = Math.sin(t * 0.08 + ovni.fase) * 2;
    const x = Math.round(ovni.x), y = Math.round(ovni.y + oscila);
    // Para no meio do caminho e acende o feixe (uns 2 s).
    const noMeio = Math.abs(ovni.x - ovni.parada) < 1.5;
    if (noMeio && ovni.feixe === 0) ovni.feixe = 120;
    if (ovni.feixe > 0) {
      ovni.feixe -= passo;
      const luz = Math.min(1, ovni.feixe / 30) * 0.22;
      for (let k = 0; k < 14; k++) {
        ctx.fillStyle = rgba('160,255,230', luz * (1 - k / 16));
        ctx.fillRect(x - 1 - Math.floor(k / 3), y + 3 + k, 3 + 2 * Math.floor(k / 3), 1);
      }
      if (ovni.feixe <= 0) ovni.parada = -1;
    } else {
      ovni.x += ovni.vx * passo;
    }
    ctx.fillStyle = 'rgba(120,220,255,0.35)';
    ctx.fillRect(x - 4, y + 1, 8, 2);
    ctx.fillStyle = '#9aa3b2';
    ctx.fillRect(x - 3, y + 1, 6, 1);
    ctx.fillStyle = '#c7ccd6';
    ctx.fillRect(x - 4, y + 2, 8, 1);
    ctx.fillStyle = '#7fe3d8';
    ctx.fillRect(x - 1, y - 1, 2, 2);
    ctx.fillStyle = (Math.floor(t / 10) % 2 === 0) ? '#ff5b5b' : '#7a1f1f';
    ctx.fillRect(x + (ovni.dir === 1 ? 3 : -4), y + 1, 1, 1);
    ctx.fillStyle = '#3ea38f';
    ctx.fillRect(x, y - 1, 1, 1);
    if ((ovni.dir === 1 && ovni.x > W + 20) || (ovni.dir === -1 && ovni.x < -20)) ovni = null;
  }

  // Satelite: pontinho que cruza devagar piscando.
  let satelite = null;
  let esperaSatelite = 1200 + sorteio() * 1200;

  function desenharSatelite(passo) {
    if (!satelite) {
      esperaSatelite -= passo;
      if (esperaSatelite <= 0) {
        const dir = aleatorio() < 0.5 ? 1 : -1;
        satelite = { dir: dir, x: dir === 1 ? -4 : W + 4, y: 4 + aleatorio() * 20, inclina: (aleatorio() - 0.5) * 0.08 };
        esperaSatelite = 2400 + aleatorio() * 2400;
      }
      return;
    }
    satelite.x += satelite.dir * 0.22 * passo;
    satelite.y += satelite.inclina * passo;
    ctx.fillStyle = '#cfd8ff';
    ctx.fillRect(Math.round(satelite.x), Math.round(satelite.y), 1, 1);
    if (Math.floor(t / 20) % 3 === 0) {
      ctx.fillStyle = '#ff6b6b';
      ctx.fillRect(Math.round(satelite.x) + satelite.dir, Math.round(satelite.y), 1, 1);
    }
    if (satelite.x < -6 || satelite.x > W + 6) satelite = null;
  }

  // Foguete: sobe das montanhas, raro.
  let foguete = null;
  let esperaFoguete = 2100 + sorteio() * 2100;

  function desenharFoguete(passo) {
    if (!foguete) {
      esperaFoguete -= passo;
      if (esperaFoguete <= 0) {
        const x = 20 + Math.floor(aleatorio() * (W - 40));
        foguete = { x: x, y: serra(x) - 2, vy: 0, fumaca: [] };
        esperaFoguete = 4200 + aleatorio() * 4200;
      }
      return;
    }
    foguete.vy = Math.min(1.2, foguete.vy + 0.01 * passo);
    foguete.y -= foguete.vy * passo;
    if (passo && aleatorio() < 0.6) {
      foguete.fumaca.push({ x: foguete.x + (aleatorio() - 0.5) * 2, y: foguete.y + 5, vida: 1 });
    }
    for (const f of foguete.fumaca) { f.vida -= 0.02 * passo; f.y += 0.05 * passo; }
    foguete.fumaca = foguete.fumaca.filter(function (f) { return f.vida > 0; });
    for (const f of foguete.fumaca) {
      ctx.fillStyle = rgba('170,160,200', f.vida * 0.45);
      ctx.fillRect(Math.round(f.x), Math.round(f.y), 1, 1);
    }
    const x = Math.round(foguete.x), y = Math.round(foguete.y);
    ctx.fillStyle = '#e8e8f0';
    ctx.fillRect(x, y, 2, 4);
    ctx.fillStyle = '#ff5b5b';
    ctx.fillRect(x, y - 1, 2, 1);
    ctx.fillRect(x - 1, y + 3, 1, 1);
    ctx.fillRect(x + 2, y + 3, 1, 1);
    ctx.fillStyle = Math.floor(t / 3) % 2 === 0 ? '#ffb347' : '#ffe27a';
    ctx.fillRect(x, y + 4, 2, 1 + Math.floor(t / 2) % 2);
    if (foguete.y < -10) foguete = null;
  }

  // ------------------------------------------------------------------
  // Visitas de jogos famosos de 8 e 16 bits (pedido do Rafael, 02/10/2026).
  // Uma de cada vez, a cada 20 a 35 s; a primeira e' a corrida do F-Zero.
  // ------------------------------------------------------------------

  // F-Zero (SNES, 1990): as quatro maquinas da primeira copa, de lado.
  // b = corpo, k = faixa, c = cabine, F = aleta, E = turbina, N = bico,
  // r = brilho de levitacao.
  const MAQUINAS = [
    S.fazer(['FF............',          // Blue Falcon (Captain Falcon)
             'FBb.....cc....',
             '.BbbbbbcccbB..',
             'EbbbbbbbbbbbbN',
             'EkkkkkkkkkkkN.',
             '.bbbbbbbbbB...',
             '..r......r....'],
            { F: '#2f5bff', b: '#2f5bff', B: '#1c3aa8', k: '#ffd23f', c: '#9cf0ff', E: '#ff7a29',
              N: '#ff3b3b', r: 'rgba(255,90,60,0.7)' }),
    S.fazer(['YY............',          // Golden Fox (Dr. Stewart)
             'YYY.......cc..',
             'EbbbbbbbbbccbN',
             'EkkkkkkkkkkkN.',
             '.bbbbbbbbbb...',
             '..r.......r...'],
            { Y: '#c79200', b: '#ffcc33', k: '#2f5bff', c: '#9cf0ff', E: '#ff7a29', N: '#ffffff',
              r: 'rgba(255,90,60,0.7)' }),
    S.fazer(['F.F...........',          // Wild Goose (Pico)
             'FFFF....ccc...',
             'EbbbbbbbcccbB.',
             'EbbbbbbbbbbbbN',
             'EkkkkkkkkkkkbN',
             '.bbbbbbbbbbbb.',
             '..r.......r...'],
            { F: '#24803a', b: '#3cbf55', B: '#24803a', k: '#ffffff', c: '#ffe066', E: '#ff7a29',
              N: '#ffd23f', r: 'rgba(255,90,60,0.7)' }),
    S.fazer(['.FF.FF.........',         // Fire Stingray (Samurai Goroh)
             'FFFFFFF..cc....',
             'EbbbbbbbbccbBB.',
             'EkkkkkkkkkkkkkN',
             'EbbbbbbbbbbbB..',
             '.bbbbbbbbB.....',
             '..r.....r......'],
            { F: '#b02a6e', b: '#ff4fa0', B: '#b02a6e', k: '#ffffff', c: '#ffe066', E: '#ff7a29',
              N: '#ffd23f', r: 'rgba(255,90,60,0.7)' })
  ];
  const PISTA = 71;            // altura da pista de luz (abaixo dos Metroides e do planeta, que vai ate a linha 61)

  function iniciarFzero() {
    const dir = aleatorio() < 0.5 ? 1 : -1;
    const pilotos = MAQUINAS.map(function (sprite, i) {
      return { sprite: sprite, x: dir === 1 ? -16 - i * 20 : W + 2 + i * 20, faixa: i % 2,
               vel: 0.33 + aleatorio() * 0.05, fase: aleatorio() * 6, rastro: [] };
    });
    return { dir: dir, pilotos: pilotos, pista: 0, desenhar: desenharFzero };
  }

  function desenharFzero(passo) {
    const ev = this;
    const naTela = ev.pilotos.some(function (p) { return p.x > -20 && p.x < W + 20; });
    const chegaram = ev.pilotos.every(function (p) { return ev.dir === 1 ? p.x > W + 2 : p.x < -18; });
    ev.pista = Math.max(0, Math.min(1, ev.pista + (chegaram ? -0.03 : 0.03) * passo));
    // A pista: duas grades de energia, piscando em tracinhos que correm.
    if (ev.pista > 0) {
      for (let x = 0; x < W; x += 2) {
        const aceso = Math.floor((x - t * 0.9 * ev.dir) / 6) % 2 === 0;
        ctx.fillStyle = rgba(aceso ? '255,220,90' : '120,200,255', ev.pista * (aceso ? 0.55 : 0.25));
        ctx.fillRect(x, PISTA - 9, 1, 1);
        ctx.fillRect(x, PISTA + 3, 1, 1);
      }
      ctx.fillStyle = rgba('120,140,255', ev.pista * 0.08);
      ctx.fillRect(0, PISTA - 8, W, 11);
    }
    for (const p of ev.pilotos) {
      // Cada maquina acelera e alivia um pouco: elas trocam de posicao.
      p.x += ev.dir * (p.vel + 0.06 * Math.sin(t * 0.025 + p.fase)) * passo;
      const y = PISTA - p.sprite.h + p.faixa * 3 + Math.round(Math.sin(t * 0.12 + p.fase) * 0.6);
      const traseira = ev.dir === 1 ? p.x - 1 : p.x + p.sprite.w;
      if (passo && aleatorio() < 0.8) p.rastro.push({ x: traseira, y: y + 3 + Math.floor(aleatorio() * 2), vida: 1 });
      for (const r of p.rastro) r.vida -= 0.05 * passo;
      p.rastro = p.rastro.filter(function (r) { return r.vida > 0; });
      for (const r of p.rastro) {
        ctx.fillStyle = rgba('255,160,80', r.vida * 0.45);
        ctx.fillRect(Math.round(r.x), Math.round(r.y), 1, 1);
      }
      // Chama da turbina, piscando.
      ctx.fillStyle = Math.floor(t / 2 + p.fase) % 2 === 0 ? '#ffe066' : '#ff7a29';
      ctx.fillRect(Math.round(ev.dir === 1 ? p.x - 2 : p.x + p.sprite.w), y + 3, 2, 2);
      S.colar(ctx, p.sprite, p.x, y, ev.dir);
    }
    // Acaba quando as quatro passaram E a pista terminou de apagar.
    return !(chegaram && ev.pista <= 0) || naTela;
  }

  // Kirby na Warp Star (Kirby's Adventure, NES 1993): cruza o ceu em curva,
  // deixando um rastro de estrelinhas coloridas.
  const KIRBY_ESTRELA = S.fazer(['...ppp...',
                                 '..ppppp..',
                                 '..pKpKp..',
                                 '..ppppp..',
                                 '...r.r...',
                                 '....Y....',
                                 '...YYY...',
                                 'YYYYYYYYY',
                                 '.YYYYYYY.',
                                 '..YY.YY..',
                                 '.YY...YY.'],
                                { p: '#ff9ccf', K: '#1a1a3a', r: '#e8204a', Y: '#ffe14a' });
  const CORES_ARCO = ['255,90,90', '255,180,60', '255,240,90', '110,240,130', '110,190,255', '200,140,255'];

  function iniciarKirby() {
    const dir = aleatorio() < 0.5 ? 1 : -1;
    return { dir: dir, x: dir === 1 ? -12 : W + 12, base: 18 + aleatorio() * 14, rastro: [], desenhar: desenharKirby };
  }

  function desenharKirby(passo) {
    this.x += this.dir * 0.7 * passo;
    const y = this.base + Math.sin(this.x * 0.04) * 8;
    const naTela = this.x > -14 && this.x < W + 14;
    if (passo && naTela) {           // fora da tela, para de soltar estrelinhas
      this.rastro.push({ x: this.x + (this.dir === 1 ? 0 : 8), y: y + 8, vida: 1, cor: CORES_ARCO[Math.floor(t) % 6] });
    }
    for (const r of this.rastro) { r.vida -= 0.03 * passo; r.y += 0.05 * passo; }
    this.rastro = this.rastro.filter(function (r) { return r.vida > 0; });
    for (const r of this.rastro) {
      ctx.fillStyle = rgba(r.cor, r.vida * 0.8);
      ctx.fillRect(Math.round(r.x), Math.round(r.y), 1, 1);
    }
    S.colar(ctx, KIRBY_ESTRELA, this.x, y, this.dir);
    const voltando = this.dir === 1 ? this.x < W + 14 : this.x > -14;
    return voltando || this.rastro.length > 0;
  }

  // Space Invaders (1978): tres invasores entram pela direita marchando la
  // em cima, passo a passo, trocando de pose a cada passo. Perto da lua, a
  // formacao desce uma linha e volta mais depressa, como no jogo (antes ela
  // passava por cima da lua).
  const INVASOR = S.quadros([
    ['..I.....I..',
     '...I...I...',
     '..IIIIIII..',
     '.II.III.II.',
     'IIIIIIIIIII',
     'I.IIIIIII.I',
     'I.I.....I.I',
     '...II.II...'],
    ['..I.....I..',
     'I..I...I..I',
     'I.IIIIIII.I',
     'III.III.III',
     'IIIIIIIIIII',
     '.IIIIIIIII.',
     '..I.....I..',
     '.I.......I.']
  ], { I: '#7dff8a' });

  const BORDA_DA_LUA = 34;      // a lua vai ate a coluna 28 (centro em 22, raio 6)

  function iniciarInvasores() {
    return { dir: -1, x: W + 4, y: 4, ritmo: 14, passoMarcha: 0, pose: 0, desenhar: desenharInvasores };
  }

  function desenharInvasores(passo) {
    this.passoMarcha += passo;
    if (this.passoMarcha >= this.ritmo) {      // a marcha: um passo de 3 pontos
      this.passoMarcha = 0;
      this.pose = 1 - this.pose;
      if (this.dir === -1 && this.x <= BORDA_DA_LUA) {
        this.y += 8;                           // desce uma linha...
        this.dir = 1;                          // ...volta...
        this.ritmo = 10;                       // ...e acelera
      } else {
        this.x += this.dir * 3;
      }
    }
    for (let i = 0; i < 3; i++) {
      S.colar(ctx, INVASOR[this.pose], this.x + i * 15, this.y, 1);
    }
    return this.dir === -1 || this.x < W + 4;
  }

  // Arwing (Star Fox, SNES 1993): duas naves em formacao; a da frente da'
  // um giro completo no meio do caminho ("do a barrel roll!").
  const ARWING = S.quadros([
    ['BB.........',
     'BBWW.......',
     '..WWWW.....',
     'EEWWWWWccN.',
     '..WWWW.....',
     'BBWW.......',
     'BB.........'],
    ['...........',
     '...........',
     'B.WWWW.....',
     'EEWWWWWccN.',
     'B.WWWW.....',
     '...........',
     '...........']
  ], { B: '#3d7dff', W: '#e8edf5', c: '#46c8ff', E: '#ff9a3c', N: '#c9ced8' });

  function iniciarArwing() {
    const dir = aleatorio() < 0.5 ? 1 : -1;
    return { dir: dir, x: dir === 1 ? -14 : W + 14, y: 30 + aleatorio() * 10, giro: -1, tiros: [],
             desenhar: desenharArwing };
  }

  function desenharArwing(passo) {
    this.x += this.dir * 0.55 * passo;
    if (this.giro < 0 && Math.abs(this.x - W / 2) < 2) this.giro = 0;
    let pose = 0;
    if (this.giro >= 0 && this.giro < 1) {
      this.giro += 0.03 * passo;
      pose = Math.floor(this.giro * 6) % 2;            // aberta, de lado, aberta, de lado...
    }
    if (passo && aleatorio() < 0.02 * passo) this.tiros.push({ x: this.x + (this.dir === 1 ? 11 : -2), y: this.y + 3 });
    for (const tiro of this.tiros) tiro.x += this.dir * 2.4 * passo;
    this.tiros = this.tiros.filter(function (tiro) { return tiro.x > -4 && tiro.x < W + 4; });
    ctx.fillStyle = '#7dff8a';
    for (const tiro of this.tiros) ctx.fillRect(Math.round(tiro.x), Math.round(tiro.y), 2, 1);
    const fogo = Math.floor(t / 3) % 2 === 0 ? '#ffe066' : '#ff9a3c';
    for (const [dx, dy, quadro] of [[0, 0, pose], [-16 * this.dir, 6, 0]]) {   // lider e ala
      ctx.fillStyle = fogo;
      ctx.fillRect(Math.round(this.x + dx + (this.dir === 1 ? -1 : 11)), Math.round(this.y + dy + 3), 1, 1);
      S.colar(ctx, ARWING[quadro], this.x + dx, this.y + dy, this.dir);
    }
    return this.dir === 1 ? this.x < W + 30 : this.x > -30;
  }

  // ------------------------------------------------------------------
  // Mais visitas de 16 bits (lote ceu-a, 13/10/2026).
  // ------------------------------------------------------------------

  // Super Sonic e o Dr. Robotnik (Sonic 3 & Knuckles, Mega Drive 1994): a
  // luta final no espaco. O Egg Mobile foge na frente, tremendo, e o Super
  // Sonic dourado vem atras, cada vez mais perto, soltando faiscas.
  // Y/y = dourado e sombra, h = brilho (o dourado pisca), s = pele,
  // w = olho e luva, R = olho vermelho e tenis, k = nariz.
  const SUPER_SONIC = S.quadros([
    ['...........Y..........',
     '........YY..YY.Y......',
     '.....YYYYyYYYYYYY.....',
     '..YYYYYYyYYYYYYYYwY...',
     'YYYyyyyYYYYYYYYwwRY...',
     '...yyyyyyYYYYYYYwsss..',
     '.....yyyyYYYYYYYsssk..',
     '.RRwyyyyyYYYYYYss.....',
     'RRw.....yyyYYYYYYYww..',
     '............yyyyYwww..'],
    ['...........h..........',    // o dourado pisca
     '........Yh..Yh.h......',
     '.....hYYYyYYYYYYY.....',
     '..hYYYYYyYYYYYYYYwY...',
     'hYYyyyyYYYYYYYYwwRY...',
     '...yyyyyyYYYYYYYwsss..',
     '.....yyyyYYYYYYYsssk..',
     'RRw.yyyyyYYYYYYss.....',
     '.RRw....yyyYYYYYYYww..',
     '............yyyyYwww..']
  ], { Y: '#ffe24a', y: '#d09000', h: '#fff6c0', s: '#ffc890', w: '#ffffff', k: '#1a1a1a', R: '#e8202a' });
  // p = careca, N = narigao, K = oculos, w = reflexo e borda do casulo,
  // M = bigode, R = jaqueta e luzes, g/G = casco.
  const EGG_MOBILE = S.quadros([
    ['......pppp..........',
     '....pppppppp........',
     '...ppppppKKKKK......',
     '...pppppppKwKKp.....',
     '...pppppppppNNN.....',
     '...ppppppppNNNNN....',
     '....pMMMMMMMNNNMM...',
     '..RRRMMMMMMMMMMMMM..',
     '.RRRRRRRMMMMMR......',
     'wwwwwwwwwwwwwwwwwwww',
     'GgggggggggggggggggG.',
     '.GgwwggggggggggggG..',
     '..GKKKRKKKKRKKKKG...',
     '....GGGGGGGGGGG.....'],
    ['....................',    // afundando de medo
     '......pppp..........',
     '....pppppppp........',
     '...ppppppKKKKK......',
     '...pppppppKwKKp.....',
     '...pppppppppNNN.....',
     '...ppppppppNNNNN....',
     '....pMMMMMMMNNNMM...',
     '..RRRMMMMMMMMMMMMM..',
     'wwwwwwwwwwwwwwwwwwww',
     'GgggggggggggggggggG.',
     '.GgwwggggggggggggG..',
     '..GKKKwKKKKwKKKKG...',
     '....GGGGGGGGGGG.....']
  ], { p: '#f8b498', N: '#e07c64', K: '#14141e', w: '#ffffff', M: '#d0601c', R: '#e02020', g: '#c4ccd8', G: '#5e6678' });

  function iniciarSuperSonic() {
    const dir = aleatorio() < 0.5 ? 1 : -1;
    return { dir: dir, x: dir === 1 ? -12 : W + 12, base: 20 + aleatorio() * 22, distancia: 54,
             faiscas: [], desenhar: desenharSuperSonic };
  }

  function desenharSuperSonic(passo) {
    const ev = this;
    ev.x += ev.dir * 0.5 * passo;                                // centro do Egg Mobile
    ev.distancia = Math.max(27, ev.distancia - 0.05 * passo);    // o Sonic vai chegando
    const sx = ev.x - ev.dir * ev.distancia;                     // centro do Super Sonic
    const onda = function (x) { return ev.base + Math.sin(x * 0.035) * 6; };
    const egg = EGG_MOBILE[Math.floor(t / 10) % 2];
    const ex = Math.round(ev.x - egg.w / 2);
    const ey = Math.round(onda(ev.x) - egg.h / 2) + Math.floor(t / 6) % 2;   // treme
    const sonic = SUPER_SONIC[Math.floor(t / 4) % 2];
    const qx = Math.round(sx - sonic.w / 2);
    const qy = Math.round(onda(sx) - sonic.h / 2) + 3;          // o Sonic segue o mesmo caminho
    const costas = ev.dir === 1 ? qx : qx + sonic.w;             // de onde saem as faiscas
    const naTela = qx > -sonic.w && qx < W;
    // Faiscas douradas que ficam para tras.
    if (passo && naTela && aleatorio() < 0.5 * passo) {
      ev.faiscas.push({ x: costas + ev.dir * aleatorio() * 6, y: qy + aleatorio() * sonic.h, vida: 1 });
    }
    for (const f of ev.faiscas) { f.vida -= 0.04 * passo; f.x -= ev.dir * 0.15 * passo; }
    ev.faiscas = ev.faiscas.filter(function (f) { return f.vida > 0; });
    for (const f of ev.faiscas) {
      const fx = Math.round(f.x), fy = Math.round(f.y);
      ctx.fillStyle = rgba('255,236,140', f.vida);
      ctx.fillRect(fx, fy, 1, 1);
      if (f.vida > 0.65) {                                       // estrelinha de quatro pontas
        ctx.fillStyle = rgba('255,250,220', (f.vida - 0.65) * 2.5);
        ctx.fillRect(fx - 1, fy, 1, 1);
        ctx.fillRect(fx + 1, fy, 1, 1);
        ctx.fillRect(fx, fy - 1, 1, 1);
        ctx.fillRect(fx, fy + 1, 1, 1);
      }
    }
    // Riscos de velocidade atras do Sonic.
    for (let k = 0; k < 3; k++) {
      const comp = 3 + (Math.floor(t / 2) + k * 2) % 4;
      ctx.fillStyle = rgba('255,226,74', 0.4 - k * 0.1);
      ctx.fillRect(ev.dir === 1 ? costas - 2 - comp - k * 2 : costas + 2 + k * 2, qy + 2 + k * 3, comp, 1);
    }
    // Chama do motor do Egg Mobile, na traseira do casco.
    ctx.fillStyle = Math.floor(t / 2) % 2 === 0 ? '#ffe066' : '#ff7a29';
    ctx.fillRect(ev.dir === 1 ? ex - 2 : ex + egg.w, ey + 10, 2, 2);
    S.colar(ctx, egg, ex, ey, ev.dir);
    S.colar(ctx, sonic, qx, qy, ev.dir);
    const indo = ev.dir === 1 ? qx < W : qx > -sonic.w;
    return indo || ev.faiscas.length > 0;
  }

  // A nave da Samus (Super Metroid, SNES 1994): cruza o ceu devagar,
  // balancando, com as luzes piscando e os jatos azuis dos dois motores.
  // De frente ela lembra o capacete da Samus: casco laranja e visor verde.
  // O = casco, o = contorno, Y = brilho, g = visor, h = reflexo,
  // L = luz acesa, l = luz apagada, G = bocal do motor.
  const NAVE_SAMUS = S.quadros([
    ['........ooooo........',    // luzes das asas
     '......ooOOOOOoo......',
     '.....oOYYOOOOOOo.....',
     '....oOOOOOOOOOOOo....',
     '....ohggggggggggo....',
     '..ooOgggggggggggOoo..',
     '.oOOOOogggggggoOOOOo.',
     'oOOLOOOOogggoOOOOLOOo',
     'oOOOoOOOOOOOOOOOoOOOo',
     '.oGo.ooolooolooo.oGo.',
     '.GGG.............GGG.'],
    ['........ooooo........',    // luzes da barriga
     '......ooOOOOOoo......',
     '.....oOYYOOOOOOo.....',
     '....oOOOOOOOOOOOo....',
     '....ohggggggggggo....',
     '..ooOgggggggggggOoo..',
     '.oOOOOogggggggoOOOOo.',
     'oOOlOOOOogggoOOOOlOOo',
     'oOOOoOOOOOOOOOOOoOOOo',
     '.oGo.oooLoooLooo.oGo.',
     '.GGG.............GGG.']
  ], { O: '#f08a24', o: '#9a4a16', Y: '#ffd25a', g: '#3cd85a', h: '#d4ffd8', L: '#ff4050', l: '#6a2a1a', G: '#7a8496' });

  function iniciarNaveSamus() {
    const dir = aleatorio() < 0.5 ? 1 : -1;
    return { dir: dir, x: dir === 1 ? -13 : W + 13, base: 14 + aleatorio() * 24, jato: [],
             desenhar: desenharNaveSamus };
  }

  function desenharNaveSamus(passo) {
    this.x += this.dir * 0.32 * passo;                           // centro da nave
    const nave = NAVE_SAMUS[Math.floor(t / 15) % 2];             // luzes: asas, barriga, asas...
    const x0 = Math.round(this.x - nave.w / 2);
    const y0 = Math.round(this.base + Math.sin(t * 0.04) * 2.5 - nave.h / 2);
    const indo = this.dir === 1 ? x0 < W : x0 > -nave.w;
    // Jatos: pontinhos azuis que saem dos bocais e ficam para tras.
    if (passo && indo && aleatorio() < 0.6 * passo) {
      this.jato.push({ x: x0 + (aleatorio() < 0.5 ? 2 : 18), y: y0 + nave.h, vida: 1 });
    }
    for (const j of this.jato) { j.vida -= 0.05 * passo; j.y += 0.25 * passo; j.x -= this.dir * 0.2 * passo; }
    this.jato = this.jato.filter(function (j) { return j.vida > 0; });
    for (const j of this.jato) {
      ctx.fillStyle = rgba('140,210,255', j.vida * 0.6);
      ctx.fillRect(Math.round(j.x), Math.round(j.y), 1, 1);
    }
    ctx.fillStyle = Math.floor(t / 2) % 2 === 0 ? '#e8f8ff' : '#7fd0ff';
    ctx.fillRect(x0 + 1, y0 + nave.h, 3, 1);
    ctx.fillRect(x0 + 17, y0 + nave.h, 3, 1);
    S.colar(ctx, nave, x0, y0, this.dir);
    return indo || this.jato.length > 0;
  }

  // Mario de capa (Super Mario World, SNES 1990): sobe la de baixo no pulo,
  // de punho para cima, e la no alto plana -- mergulha devagar e puxa para
  // cima de novo, com a capa batendo, como no jogo.
  // R = bone e camisa, B = macacao, S = pele, H = cabelo e sapato,
  // K = olho e bigode, W = luva, Y/y = capa.
  const MARIO_CAPA = S.quadros([
    ['..............WW..',    // subindo
     '..........RRRRRR..',
     '.........RRRRRRRR.',
     '.........HHSSKS...',
     'y.......HSHSSSSS..',
     'yYy.....HSHHSSSK..',
     '.yYy.....SSKKKK...',
     '.yYYy...RRBBRR....',
     '..yYYy.RRBBBBB....',
     '..yYYYyyBBBBBB....',
     '...yYYYHH...BBH...',
     '....yyyHH....HH...'],
    ['..................',    // planando, capa para cima
     '..................',
     'y.................',
     'yYy...............',
     '.yYYy.......RRRR..',
     '..yYYYy....RRRRRRR',
     '...yYYYYy.HHSSKSS.',
     '....yYYYYyHSSSSSSS',
     'HBBBBBBBRRRSKKKK..',
     'HHBBBBBBRRRRRRRRWW',
     '..................',
     '..................'],
    ['..................',    // planando, capa batendo
     '..................',
     '..................',
     '..................',
     '............RRRR..',
     'y..........RRRRRRR',
     'yYYyy.....HHSSKSS.',
     '.yYYYYyyy.HSSSSSSS',
     'HByyYYYYYyRSKKKK..',
     'HHBBBBBBRRRRRRRRWW',
     '..................',
     '..................']
  ], { R: '#e02810', B: '#2050e8', S: '#ffc898', H: '#6a3a10', K: '#000000', W: '#ffffff', Y: '#ffd800', y: '#c07c00' });

  function iniciarMarioCapa() {
    const dir = aleatorio() < 0.5 ? 1 : -1;
    return { dir: dir, x: dir === 1 ? -18 : W, y: H + 2, alto: 10 + aleatorio() * 18, yPlano: 0,
             subindo: true, fase: 0, vento: [], desenhar: desenharMarioCapa };
  }

  function desenharMarioCapa(passo) {
    const indo = this.dir === 1 ? this.x < W + 2 : this.x > -20;
    let quadro;
    if (this.subindo) {                                          // o pulo
      this.x += this.dir * 0.5 * passo;
      this.y -= 0.65 * passo;
      quadro = MARIO_CAPA[0];
      if (this.y <= this.alto) {
        this.subindo = false;
        this.yPlano = this.y - 3;           // no quadro planando o bone fica 3 pontos mais baixo
      }
    } else {                                                     // o voo planado
      this.x += this.dir * 0.75 * passo;
      this.fase += 0.035 * passo;
      this.y = this.yPlano + 6 - 6 * Math.cos(this.fase);
      quadro = MARIO_CAPA[1 + Math.floor(t / 6) % 2];
      // Risquinhos de vento atras da capa.
      if (passo && indo && aleatorio() < 0.25 * passo) {
        this.vento.push({ x: this.x + (this.dir === 1 ? -4 : 19), y: this.y + 3 + Math.floor(aleatorio() * 7), vida: 1 });
      }
    }
    for (const v of this.vento) { v.vida -= 0.06 * passo; v.x -= this.dir * 0.3 * passo; }
    this.vento = this.vento.filter(function (v) { return v.vida > 0; });
    for (const v of this.vento) {
      ctx.fillStyle = rgba('255,255,255', v.vida * 0.4);
      ctx.fillRect(Math.round(v.x), Math.round(v.y), 3, 1);
    }
    S.colar(ctx, quadro, this.x, this.y, this.dir);
    return indo || this.vento.length > 0;
  }

  // Meta Knight (Kirby Super Star, SNES 1996): chega batendo as asas de
  // morcego, para no meio do ceu, a espada Galaxia brilha... e ele sai num
  // risco, deixando a sombra para tras.
  // B = corpo, M/m = mascara e lamina, K = visor, Y = olhos e cabo da espada,
  // V/v = asas, P = sapatos.
  const META_KNIGHT = S.quadros([
    ['V...................V',    // asas em cima
     'VV.................VV',
     'vVV.......BBBB....VVv',
     '.vVV....BBBBMMM..VVv.',
     '.vVVV..BBBMMMMMMVVVv.',
     '..vVVVvBBKKKKKKKvVv..',
     '..V.VVvBBKYKKYKKvVV..',
     '...V.V.BBMMMMMMm.V.V.',
     '.......BBBMMMMm.Y....',
     '........BBBBBBYYMMMM.',
     '........PP...PPY.....',
     '.....................'],
    ['.....................',    // asas no meio
     '.....................',
     '..........BBBB.......',
     '........BBBBMMM......',
     'VVVV...BBBMMMMMM..VVV',
     'vVVVVVvBBKKKKKKKvVVVv',
     '.vVVVVvBBKYKKYKKvVVv.',
     '..V.V.VBBMMMMMMmV.V..',
     '.......BBBMMMMm.Y....',
     '........BBBBBBYYMMMM.',
     '........PP...PPY.....',
     '.....................'],
    ['.....................',    // asas embaixo
     '.....................',
     '..........BBBB.......',
     '........BBBBMMM......',
     '.......BBBMMMMMM.....',
     '......vBBKKKKKKKv....',
     '.....vVBBKYKKYKKVv...',
     '...vvVVBBMMMMMMmVVvv.',
     '..vVVV.BBBMMMMm.YVVVv',
     '.vVV.V..BBBBBBYYMMMM.',
     'vV..V...PP...PPY..VVv',
     'V...................V']
  ], { B: '#3448c0', M: '#dde3f0', m: '#8a92a8', K: '#101018', Y: '#ffe040', V: '#6c3fb0', v: '#a37ae6', P: '#d050b0' });
  const BATIDA_MK = [0, 1, 2, 1];          // cima, meio, baixo, meio
  const SOBE_MK = [1, 0, -1, 0];           // a asa desce e ele sobe um pouquinho

  function iniciarMetaKnight() {
    const dir = aleatorio() < 0.5 ? 1 : -1;
    return { dir: dir, x: dir === 1 ? -22 : W + 1, y: 14 + aleatorio() * 24, alvo: W / 2 + (aleatorio() - 0.5) * 50,
             fase: 'chega', espera: 0, vel: 0.5, rastro: [], desenhar: desenharMetaKnight };
  }

  function desenharMetaKnight(passo) {
    const centro = this.x + 10.5;
    if (this.fase === 'chega' && (this.dir === 1 ? centro >= this.alvo : centro <= this.alvo)) this.fase = 'para';
    if (this.fase === 'para') {
      this.espera += passo;
      if (this.espera > 90) this.fase = 'sai';
    } else {
      if (this.fase === 'sai') this.vel = Math.min(3, this.vel + 0.08 * passo);
      this.x += this.dir * this.vel * passo;
    }
    const batida = Math.floor(t / (this.fase === 'sai' ? 3 : 5)) % 4;
    const quadro = META_KNIGHT[BATIDA_MK[batida]];
    const y = Math.round(this.y + SOBE_MK[batida] + (this.fase === 'para' ? Math.sin(this.espera * 0.07) * 1.5 : 0));
    // No risco, duas sombras ficam para tras.
    if (this.fase === 'sai' && passo) {
      this.rastro.unshift({ x: this.x, y: y, quadro: quadro });
      if (this.rastro.length > 5) this.rastro.pop();
    }
    for (const [k, alfa] of [[4, 0.18], [2, 0.35]]) {
      const r = this.rastro[k];
      if (!r) continue;
      ctx.globalAlpha = alfa;
      S.colar(ctx, r.quadro, r.x, r.y, this.dir);
      ctx.globalAlpha = 1;
    }
    S.colar(ctx, quadro, this.x, y, this.dir);
    // Parado, a ponta da espada brilha.
    if (this.fase === 'para' && this.espera > 20 && this.espera < 60) {
      const k = Math.sin((this.espera - 20) / 40 * Math.PI);
      const bx = Math.round(this.dir === 1 ? this.x + 19 : this.x + 1), by = y + 9;
      const raio = Math.round(k * 2.4);
      ctx.fillStyle = rgba('255,250,200', k);
      ctx.fillRect(bx - raio, by, raio * 2 + 1, 1);
      ctx.fillRect(bx, by - raio, 1, raio * 2 + 1);
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(bx, by, 1, 1);
    }
    return this.dir === 1 ? this.x < W + 40 : this.x > -60;
  }

  // Vic Viper (Gradius III, SNES 1990): a nave do Gradius faz ondas pelo ceu
  // com as duas "options" (as bolinhas laranja) seguindo o mesmo caminho,
  // uma atras da outra, e atirando junto com ela.
  // W/w = casco, B = asa, c = cabine, R = detalhe, E = motor.
  const VIC_VIPER = S.quadros([
    ['.....wWWWWWWWWw..',    // reta
     '....wBB..........',
     '...RWWB..........',
     '..RWWWWWWWWW.....',
     'EEWWWWWWWccWWWWWw',
     '..RWWWWWWWWW.....',
     '...RWWB..........',
     '....wBB..........',
     '.....wWWWWWWWWw..'],
    ['.................',    // subindo
     '.....wWWWWWWWw...',
     '...RWBB..........',
     '..RWWWWWWWWW.....',
     'EEWWWWWWWccWWWWWw',
     '..RWWWWWWWWW.....',
     '...RWWBB.........',
     '....wWWBB........',
     '....wWWWWWWWWWWw.'],
    ['....wWWWWWWWWWWw.',    // descendo
     '....wWWBB........',
     '...RWWBB.........',
     '..RWWWWWWWWW.....',
     'EEWWWWWWWccWWWWWw',
     '..RWWWWWWWWW.....',
     '...RWBB..........',
     '.....wWWWWWWWw...',
     '.................']
  ], { W: '#e8ecf4', w: '#a8b0c8', B: '#3060e0', c: '#60d0ff', R: '#e03030', E: '#ff9a3c' });
  // A option: bolinha laranja que pulsa.
  const OPTION_GRADIUS = S.quadros([
    ['.ooo.',
     'oOOOo',
     'oOhOo',
     'oOOOo',
     '.ooo.'],
    ['..o..',
     '.oOo.',
     'oOhOo',
     '.oOo.',
     '..o..']
  ], { o: '#c84010', O: '#ff8a20', h: '#ffe9a0' });

  function iniciarVicViper() {
    const dir = aleatorio() < 0.5 ? 1 : -1;
    return { dir: dir, x: dir === 1 ? -10 : W + 10, base: 20 + aleatorio() * 26, amp: 7 + aleatorio() * 5,
             recarga: 30, tiros: [], desenhar: desenharVicViper };
  }

  function desenharVicViper(passo) {
    const ev = this;
    ev.x += ev.dir * 0.6 * passo;                                // centro da nave
    const caminho = function (x) { return ev.base + Math.sin(x * 0.045) * ev.amp; };
    const y = Math.round(caminho(ev.x));
    // Inclina conforme o caminho logo a frente: subindo, reta ou descendo.
    const frente = caminho(ev.x + ev.dir * 3) - caminho(ev.x);
    const nave = VIC_VIPER[frente < -0.6 ? 1 : frente > 0.6 ? 2 : 0];
    // As options passam pelos mesmos pontos, logo atras.
    const options = [ev.x - ev.dir * 15, ev.x - ev.dir * 28].map(function (ox) {
      return { x: Math.round(ox), y: Math.round(caminho(ox)) };
    });
    // A nave e as options atiram juntas.
    ev.recarga -= passo;
    if (ev.recarga <= 0) {
      ev.recarga = 22;
      ev.tiros.push({ x: ev.x + ev.dir * 9, y: y });
      for (const o of options) ev.tiros.push({ x: o.x + ev.dir * 3, y: o.y });
    }
    for (const tiro of ev.tiros) tiro.x += ev.dir * 2.6 * passo;
    ev.tiros = ev.tiros.filter(function (tiro) { return tiro.x > -6 && tiro.x < W + 6; });
    ctx.fillStyle = '#fff2a8';
    for (const tiro of ev.tiros) ctx.fillRect(Math.round(tiro.x) - (ev.dir === 1 ? 0 : 3), tiro.y, 4, 1);
    const opt = OPTION_GRADIUS[Math.floor(t / 4) % 2];
    for (const o of options) {
      ctx.fillStyle = rgba('255,140,40', 0.22);                  // brilho em volta
      ctx.fillRect(o.x - 3, o.y - 1, 7, 3);
      ctx.fillRect(o.x - 1, o.y - 3, 3, 7);
      S.colar(ctx, opt, o.x - 2, o.y - 2, 1);
    }
    const x0 = Math.round(ev.x) - 8;
    ctx.fillStyle = Math.floor(t / 2) % 2 === 0 ? '#ffe066' : '#ff9a3c';
    ctx.fillRect(ev.dir === 1 ? x0 - 2 : x0 + nave.w, y, 2, 1);  // chama do motor
    S.colar(ctx, nave, x0, y - 4, ev.dir);
    const indo = ev.dir === 1 ? options[1].x < W + 6 : options[1].x > -6;
    return indo || ev.tiros.length > 0;
  }

  // ------------------------------------------------------------------
  // Mais visitas de 16 bits (lote ceu-b, 14/10/2026): Ristar, ToeJam &
  // Earl, o Starman do EarthBound, Earthworm Jim, Mario e Luigi na
  // Rainbow Road e a Lunar Whale do Final Fantasy IV.
  // ------------------------------------------------------------------
  const RISTAR = S.quadros([
    ['......L......',
     '.....LYL.....',
     '.....LYY.....',
     '....LYYYD....',
     'WWLYYYYYYYDWW',
     'WgDYKYYYKYDgW',
     '...YKYYYKY...',
     '...YYYYYYYD..',
     '..YYYrrrYYD..',
     '..YYYDYDYYD..',
     '.DYYD...DYYD.',
     'WWr.......rWW',
     'ggg.......ggg'],
    ['gW.....WW....',
     'gWD....gW....',
     'grYYY..DL....',
     '..YYYYYYY....',
     '..DYYYKKYL...',
     '...DrYYYYYLL.',
     '...YrYYYYYYYL',
     '...DrYYYYYYL.',
     '..DYYYKKYD...',
     '..YYYYYYY....',
     'grYDDD.DD....',
     'gWD....gW....',
     'gW.....WW....'],
    ['ggg.......ggg',
     'WWr.......rWW',
     '.DYYD...DYYD.',
     '..DYYDYDYYY..',
     '..DYYrrrYYY..',
     '..DYYYYYYY...',
     '...YKYYYKY...',
     'WgDYKYYYKYDgW',
     'WWDYYYYYYYLWW',
     '....DYYYL....',
     '.....YYL.....',
     '.....LYL.....',
     '......L......'],
    ['......L......',
     '.....LYL.....',
     '.....LYY.....',
     '....LYYYD....',
     '.LLYYYYYYYDD.',
     '..DYKYYYKYD..',
     '...YKYYYKY...',
     '...YYYYYYYD..',
     '..YYYrrrYYD..',
     '..YYYDYDYYD..',
     '.DYYD...DYYD.',
     'WWr.......rWW',
     'ggg.......ggg']
  ], { Y: '#ffd23a', L: '#fff4a8', D: '#e8941e', K: '#1c1a3a', W: '#ffffff', g: '#b9c3dd', r: '#e8202a' });

  const TOEJAM_EARL = S.quadros([
    ['...o..o...............',
     '..oooooo........W..W..',
     '.oKKKKKKo.......r..r..',
     '.oKWKoKWo.....BBrrrr..',
     'oooooooooo......rrrr..',
     'oooooooooo......rYrr..',
     '.BBBBBBBB.......rrrr..',
     '.BBB..BBB.......r.r.r.',
     '.rrr..rrr......WW.W.WW',
     'rr..sSSSSSSSSSSSSSSs..',
     'rrsSSSSSSSSSSSSSSSSSSs',
     'rrSSSrrrrrrrrBBSSSSSSS',
     'rrsSSSSSSSSSSSSSSSSSs.',
     'rr...sssssssssssssss..'],
    ['..o....o..............',
     '...oooooo.......W...W.',
     '..oKKKKKKo.......r.r..',
     '..oKWKoKWo....BBBrrrr.',
     '.oooooooooo......rrrr.',
     '.oooooooooo......rYrr.',
     '..BBBBBBBB.......rrrr.',
     '..BBB..BBB......r.r.r.',
     '..rrr..rrr.....WW.W.WW',
     'rr..sSSSSSSSSSSSSSSs..',
     'rrsSSSSSSSSSSSSSSSSSSs',
     'rrSSSrrrrrrrrBBSSSSSSS',
     'rrsSSSSSSSSSSSSSSSSSs.',
     'rr...sssssssssssssss..']
  ], { r: '#ec2d45', o: '#ff9a3c', K: '#15151f', W: '#ffffff', B: '#3a6cff', Y: '#ffd23f', S: '#d4dae8', s: '#8a93aa' });

  const STARMAN = S.quadros([
    ['....sWs....',
     '...sWWWs...',
     '...sKKKs...',
     '..dsWWWsd..',
     '.dsWWWWWsd.',
     'ds.sKKKs.sd',
     'ds.sWKWs.sd',
     '.ds.sKs.sd.',
     '..dsWWWsd..',
     '...ss.ss...',
     '...sd.ds...',
     '...sd.ds...',
     '..dsd.dsd..'],
    ['....sWs....',
     '...sWWWs...',
     '...sKKcs...',
     '..dsWWWsd..',
     '.dsWWWWWsd.',
     'ds.sKKKs.sd',
     'ds.sWKWs.sd',
     '.ds.sKs.sd.',
     '..dsWWWsd..',
     '...ss.ss...',
     '...sd.ds...',
     '...sd.ds...',
     '..dsd.dsd..'],
    ['....sWs....',
     '...........',
     '...sKKKs...',
     '...........',
     '.dsWWWWWsd.',
     '...........',
     'ds.sWKWs.sd',
     '...........',
     '..dsWWWsd..',
     '...........',
     '...sd.ds...',
     '...........',
     '..dsd.dsd..'],
    ['.....c.....',
     '.....W.....',
     '.....W.....',
     '....sWs....',
     '....sWs....',
     '....sWs....',
     '....sWs....',
     '....sWs....',
     '....sWs....',
     '.....W.....',
     '.....W.....',
     '.....W.....',
     '.....c.....']
  ], { W: '#f2f5fb', s: '#b3bccf', d: '#737d99', K: '#14161f', c: '#8ff3ff' });

  const JIM = S.quadros([
    ['.....qpp............',
     '.....pWW............',
     '.....pWK............',
     '......pp............',
     '......qp............',
     '.....gWWg.yy........',
     '.....WWWWWRR........',
     '.....gWWg...........',
     '..r.RRRWRRRRRRRWW...',
     '.rrRRRRWWRRRRRRRWWy.',
     '..rrRRRRRRRRRRRRWW..',
     '.rr.................'],
    ['....qpp.............',
     '....pWW.............',
     '....pWK.............',
     '.....pp.............',
     '......qp............',
     '.....gWWg.yy........',
     '.....WWWWWRR........',
     '.....gWWg...........',
     '..r.RRRWRRRRRRRWW...',
     '.rrRRRRWWRRRRRRRWWy.',
     '..rrRRRRRRRRRRRRWW..',
     '.rr.................']
  ], { p: '#ff9a8a', q: '#d8606a', W: '#ffffff', K: '#16161f', g: '#9fb2d6', R: '#e8302a', r: '#9a1c22', y: '#ffd23f' });

  const KART_MARIO = S.quadros([
    ['....CCCC....',
     '...CCCCCC...',
     '....SSES....',
     '....SKKS....',
     '...OOOOGG...',
     '.BBBBBBBBBB.',
     'BBBBBBBBBBBB',
     '.KKK....KKK.',
     '.KGK....KGK.',
     '..K......K..'],
    ['............',
     '....CCCC....',
     '...CCCCCC...',
     '....SSES....',
     '....SKKS....',
     '...OOOOGG...',
     '.BBBBBBBBBB.',
     'BKKKBBBBKKKB',
     '.KKG....KKG.',
     '..K......K..']
  ], { C: '#e8202a', S: '#ffb070', E: '#14141f', K: '#1a1a22', O: '#2f5bff', G: '#c9ced8', B: '#e8202a' });

  const KART_LUIGI = S.quadros([
    ['....CCCC....',
     '...CCCCCC...',
     '....SSES....',
     '....SKKS....',
     '...OOOOGG...',
     '.BBBBBBBBBB.',
     'BBBBBBBBBBBB',
     '.KKK....KKK.',
     '.KGK....KGK.',
     '..K......K..'],
    ['............',
     '....CCCC....',
     '...CCCCCC...',
     '....SSES....',
     '....SKKS....',
     '...OOOOGG...',
     '.BBBBBBBBBB.',
     'BKKKBBBBKKKB',
     '.KKG....KKG.',
     '..K......K..']
  ], { C: '#2fbf4a', S: '#ffb070', E: '#14141f', K: '#1a1a22', O: '#2f5bff', G: '#c9ced8', B: '#2fbf4a' });

  const BALEIA = S.quadros([
    ['F...................',
     'FF........DDDD......',
     '.Fdd...dDDDDDDDD....',
     '..ddddDDDDDDDDDDDD..',
     '...dddrrrrrrrrrrDDD.',
     '....ddPPPPPPPPPPPdDD',
     '.....dpPpPpPpPpPPPd.',
     '.......pppppppppp...',
     '..........y..y......'],
    ['....................',
     'F.........DDDD......',
     'FFdd...dDDDDDDDD....',
     '.FddddDDDDDDDDDDDD..',
     '...dddrrrrrrrrrrDDD.',
     '....ddPPPPPPPPPPPdDD',
     '.....dpPpPpPpPpPPPd.',
     '.......pppppppppp...',
     '..........y..y......']
  ], { d: '#4b4670', D: '#7a74a6', P: '#ece6f6', p: '#b2a8cf', r: '#e8483a', F: '#f6cfe0', y: '#ffd84a', K: '#15131f' });

  // Ristar (Ristar, Mega Drive 1995): a estrelinha heroi cruza o ceu em arco,
  // girando, e deixa um rastro de faiscas douradas.
  function iniciarRistar() {
    const dir = aleatorio() < 0.5 ? 1 : -1;
    return { dir: dir, x: dir === 1 ? -14 : W + 2, base: 14 + aleatorio() * 18, rastro: [], desenhar: desenharRistar };
  }

  function desenharRistar(passo) {
    this.x += this.dir * 0.65 * passo;
    const y = this.base + Math.sin(this.x * 0.05) * 7;
    const naTela = this.x > -14 && this.x < W + 2;
    if (passo && naTela && aleatorio() < 0.7) {
      this.rastro.push({ x: this.x + 6 - this.dir * 5, y: y + 6 + (aleatorio() - 0.5) * 4, vida: 1 });
    }
    for (const r of this.rastro) { r.vida -= 0.04 * passo; r.y += 0.04 * passo; }
    this.rastro = this.rastro.filter(function (r) { return r.vida > 0; });
    for (const r of this.rastro) {
      ctx.fillStyle = rgba('255,230,110', r.vida * 0.8);
      ctx.fillRect(Math.round(r.x), Math.round(r.y), 1, 1);
    }
    S.colar(ctx, RISTAR[Math.floor(t / 5) % RISTAR.length], this.x, y, this.dir);
    const voltando = this.dir === 1 ? this.x < W + 2 : this.x > -14;
    return voltando || this.rastro.length > 0;
  }

  // ToeJam & Earl (Mega Drive 1991): os dois alienigenas passam devagar no
  // pedaco de foguete deles, balancando, com a chama piscando atras.
  function iniciarToeJam() {
    const dir = aleatorio() < 0.5 ? 1 : -1;
    return { dir: dir, x: dir === 1 ? -24 : W + 2, base: 20 + aleatorio() * 16, chama: [], desenhar: desenharToeJam };
  }

  function desenharToeJam(passo) {
    this.x += this.dir * 0.32 * passo;
    const y = this.base + Math.sin(t * 0.06) * 2;
    const traseira = this.dir === 1 ? this.x - 1 : this.x + 22;
    const naTela = this.x > -24 && this.x < W + 2;          // fora da tela, a chama para
    if (passo && naTela && aleatorio() < 0.5) this.chama.push({ x: traseira, y: y + 10 + aleatorio() * 2, vida: 1 });
    for (const c of this.chama) { c.vida -= 0.035 * passo; c.x -= this.dir * 0.15 * passo; }
    this.chama = this.chama.filter(function (c) { return c.vida > 0; });
    for (const c of this.chama) {
      ctx.fillStyle = rgba('255,170,80', c.vida * 0.6);
      ctx.fillRect(Math.round(c.x), Math.round(c.y), 1, 1);
    }
    S.colar(ctx, TOEJAM_EARL[Math.floor(t / 8) % 2], this.x, y, this.dir);
    const voltando = this.dir === 1 ? this.x < W + 2 : this.x > -24;
    return voltando || this.chama.length > 0;
  }

  // Starman (EarthBound, SNES 1994): aparece num risco de luz, flutua um pouco
  // no lugar e vai embora do mesmo jeito (o teleporte deles).
  function iniciarStarman() {
    return { x: 24 + aleatorio() * (W - 48), y: 12 + aleatorio() * 26, fase: 0, desenhar: desenharStarman };
  }

  function desenharStarman(passo) {
    this.fase += passo;
    const f = this.fase;
    let quadro;
    if (f < 12 || (f >= 216 && f < 228)) quadro = STARMAN[3];        // o risco de luz
    else if (f < 24 || (f >= 204 && f < 216)) quadro = STARMAN[2];   // se formando / sumindo
    else if (f < 204) quadro = STARMAN[Math.floor(t / 10) % 2];      // flutuando (~3 s)
    else return false;
    const y = this.y + (f >= 24 && f < 204 ? Math.sin(t * 0.05) * 1.5 : 0);
    S.colar(ctx, quadro, this.x, y, 1);
    return true;
  }

  // Earthworm Jim (SNES/Mega Drive 1994): a toda velocidade no foguete de
  // bolso, tremendo de leve e soltando fumaca.
  function iniciarJim() {
    const dir = aleatorio() < 0.5 ? 1 : -1;
    return { dir: dir, x: dir === 1 ? -22 : W + 2, y: 22 + aleatorio() * 24, fumaca: [], desenhar: desenharJim };
  }

  function desenharJim(passo) {
    this.x += this.dir * 1.0 * passo;
    const y = this.y + Math.sin(t * 0.3) * 0.7;
    const traseira = this.dir === 1 ? this.x : this.x + 19;
    if (passo && this.x > -22 && this.x < W + 2) {
      this.fumaca.push({ x: traseira, y: y + 9 + (aleatorio() - 0.5) * 2, vida: 1 });
    }
    for (const f of this.fumaca) { f.vida -= 0.03 * passo; f.y -= 0.03 * passo; }
    this.fumaca = this.fumaca.filter(function (f) { return f.vida > 0; });
    for (const f of this.fumaca) {
      ctx.fillStyle = rgba('200,190,220', f.vida * 0.5);
      ctx.fillRect(Math.round(f.x), Math.round(f.y), 1, 1);
    }
    S.colar(ctx, JIM[Math.floor(t / 3) % 2], this.x, y, this.dir);
    const voltando = this.dir === 1 ? this.x < W + 2 : this.x > -22;
    return voltando || this.fumaca.length > 0;
  }

  // Super Mario Kart (SNES 1992): Mario e Luigi disputam uma volta numa faixa
  // da Rainbow Road, a pista de arco-iris, que aparece e some como a do F-Zero.
  const ARCO_IRIS = ['255,90,90', '255,180,60', '255,240,90', '110,240,130', '110,190,255', '200,140,255'];
  const PISTA_KART = 68;       // na altura da pista do F-Zero, abaixo do planeta

  function iniciarKart() {
    const dir = aleatorio() < 0.5 ? 1 : -1;
    const karts = [KART_MARIO, KART_LUIGI].map(function (sprite, i) {
      return { sprite: sprite, x: dir === 1 ? -14 - i * 16 : W + 2 + i * 16, faixa: i,
               vel: 0.5 + aleatorio() * 0.04, fase: aleatorio() * 6 };
    });
    return { dir: dir, karts: karts, pista: 0, desenhar: desenharKart };
  }

  function desenharKart(passo) {
    const ev = this;
    const chegaram = ev.karts.every(function (k) { return ev.dir === 1 ? k.x > W + 2 : k.x < -14; });
    ev.pista = Math.max(0, Math.min(1, ev.pista + (chegaram ? -0.03 : 0.03) * passo));
    if (ev.pista > 0) {
      for (let i = 0; i < ARCO_IRIS.length; i++) {
        ctx.fillStyle = rgba(ARCO_IRIS[i], ev.pista * 0.45);
        ctx.fillRect(0, PISTA_KART + i, W, 1);
      }
      for (let x = 0; x < W; x += 2) {          // o brilho que corre na pista
        if (Math.floor((x - t * 1.2 * ev.dir) / 8) % 3 === 0) {
          ctx.fillStyle = rgba('255,255,255', ev.pista * 0.35);
          ctx.fillRect(x, PISTA_KART + 2, 1, 2);
        }
      }
    }
    for (const k of ev.karts) {          // trocam de posicao: um acelera, o outro alivia
      k.x += ev.dir * (k.vel + 0.08 * Math.sin(t * 0.03 + k.fase)) * passo;
      const y = PISTA_KART - k.sprite[0].h + 4 + k.faixa * 2;
      S.colar(ctx, k.sprite[Math.floor(t / 4) % 2], k.x, y, ev.dir);
    }
    return !(chegaram && ev.pista <= 0);
  }

  // Lunar Whale (Final Fantasy IV, SNES 1991): a nave-baleia sobe devagar ate
  // a lua do ceu (em 22, 13), passa por ela e vai embora.
  function iniciarBaleia() {
    const y0 = 40 + aleatorio() * 8;
    const ticks = (W + 4 - 12) / 0.28;             // ate o meio dela chegar a lua
    return { x: W + 4, y: y0, vy: (y0 - 9) / ticks, desenhar: desenharBaleia };
  }

  function desenharBaleia(passo) {
    this.x -= 0.28 * passo;
    this.y -= this.vy * passo;
    S.colar(ctx, BALEIA[Math.floor(t / 12) % 2], this.x, this.y + Math.sin(t * 0.04) * 1.2, -1);
    return this.x > -24;
  }

  const VISITAS = { fzero: iniciarFzero, kirby: iniciarKirby, invasores: iniciarInvasores, arwing: iniciarArwing,
                    supersonic: iniciarSuperSonic, navesamus: iniciarNaveSamus, mariocapa: iniciarMarioCapa, metaknight: iniciarMetaKnight, vicviper: iniciarVicViper, ristar: iniciarRistar, toejam: iniciarToeJam, starman: iniciarStarman, jim: iniciarJim, kart: iniciarKart, baleia: iniciarBaleia };
  let filaDeVisitas = ['fzero'];
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
  window.__fundoEscuro = {
    visitas: Object.keys(VISITAS),
    chamar: function (nome) { if (VISITAS[nome]) visita = VISITAS[nome](); return !!visita; },
    rodando: function () { return !!visita; },
    velocidade: function (v) { velocidade = Math.max(1, Math.min(16, Number(v) || 1)); return velocidade; },
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

  function desenharCeu(passo) {
    for (const faixa of aurora) {
      const brilho = 0.06 + 0.08 * ((Math.sin(t * faixa.pulso + faixa.fase) + 1) / 2);
      ctx.fillStyle = rgba(faixa.cor, brilho);
      for (let x = 0; x < W; x += 2) {
        const y = Math.round(faixa.y + Math.sin(x * faixa.onda + t * faixa.velOnda + faixa.fase) * faixa.amp);
        ctx.fillRect(x, y, 2, 6);
      }
    }
    for (const n of nebulosas) {
      n.x += n.vel * passo;
      if (n.x > W + 4) n.x = -n.tela.width;
      ctx.globalAlpha = 0.6 + 0.4 * ((Math.sin(t * 0.015 + n.y) + 1) / 2);
      ctx.drawImage(n.tela, Math.round(n.x), n.y);
      ctx.globalAlpha = 1;
    }
    // Constelacao: as linhas acendem e apagam num ciclo de ~25 s.
    const acesa = (Math.sin(t * 0.004) + 1) / 2;
    if (acesa > 0.05) {
      ctx.strokeStyle = rgba('170,190,255', acesa * 0.35);
      ctx.lineWidth = 1;
      ctx.beginPath();
      for (const [a, b] of ligacoes) {
        ctx.moveTo(constelacao[a][0] + 0.5, constelacao[a][1] + 0.5);
        ctx.lineTo(constelacao[b][0] + 0.5, constelacao[b][1] + 0.5);
      }
      ctx.stroke();
    }
    ctx.fillStyle = '#dfe6ff';
    for (const [x, y] of constelacao) ctx.fillRect(x, y, 1, 1);
    for (const s of estrelas) {
      const a = (Math.sin(t * s.vel + s.fase) + 1) / 2;
      ctx.fillStyle = rgba('255,255,255', 0.1 + a * 0.9);
      ctx.fillRect(s.x, s.y, 1, 1);
    }
    for (const s of brilhantes) {
      const a = (Math.sin(t * s.vel + s.fase) + 1) / 2;
      ctx.fillStyle = rgba('255,255,255', 0.35 + a * 0.65);
      ctx.fillRect(s.x, s.y, 1, 1);
      if (a > 0.55) {
        ctx.fillStyle = rgba('200,220,255', (a - 0.55) * 1.6);
        ctx.fillRect(s.x - 1, s.y, 1, 1);
        ctx.fillRect(s.x + 1, s.y, 1, 1);
        ctx.fillRect(s.x, s.y - 1, 1, 1);
        ctx.fillRect(s.x, s.y + 1, 1, 1);
      }
    }
  }

  function desenharQuadro(passo) {
    passo = passo || 0;
    ctx.drawImage(fixa, 0, 0);
    desenharCeu(passo);
    desenharGalaxia();
    desenharPlaneta(passo);
    desenharSatelite(passo);
    desenharMeteoros(passo);
    desenharCometa(passo);
    desenharOvni(passo);
    desenharVisitas(passo);
    desenharMetroides(passo);
    desenharFoguete(passo);
  }

  // ------------------------------------------------------------------
  // Quando animar (igual ao field-background.js)
  // ------------------------------------------------------------------
  const menosMovimento = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : null;

  function modo() {
    if (document.body.dataset.tema !== 'escuro') return 'oculto';
    if (gravando) return 'gravando';       // ferramentas\gravar_fundo_gif.py avanca na mao
    if (soFundo()) return 'animado';       // "Visualizar animação": anima sempre
    const escolha = document.body.dataset.fundoAnimado || 'automatico';
    if (escolha === 'parado') return 'parado';
    if (escolha === 'sempre') return 'animado';
    if (document.body.dataset.modoModesto === 'true') return 'parado';
    if (menosMovimento && menosMovimento.matches) return 'parado';
    return 'animado';
  }

  const INTERVALO = 1000 / 20;   // 20 por segundo, por relogio (field-background.js, item 3)
  let velocidade = 1;   // so os testes aceleram (__fundoEscuro.velocidade)
  let geracao = 0;
  let ultimo = 0;
  let modoAtual = null;

  function iniciarLaco() {
    const minha = ++geracao;
    ultimo = 0;
    function quadro() {
      if (minha !== geracao) return;
      setTimeout(quadro, INTERVALO);
      // Janela escondida (minimizada, ou o jogo por cima): nao desenha.
      if (document.visibilityState !== 'visible') return;
      const agora = performance.now();
      const passo = (ultimo ? Math.min(4, (agora - ultimo) / (1000 / 60)) : 1) * velocidade;
      ultimo = agora;
      t += passo;
      try {
        desenharQuadro(passo);
      } catch (e) {
        console.error('Fundo galactico: erro num quadro, seguindo pro proximo.', e);
      }
    }
    setTimeout(quadro, 0);
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
    modoAtual = novo;
    if (novo === 'animado') {
      iniciarLaco();
    } else {
      geracao++;
      if (novo === 'parado') {
        t = 300;          // aurora e constelacao num momento bonito
        desenharQuadro(0);
      }
    }
  }

  sincronizar();
  new MutationObserver(sincronizar).observe(document.body, {
    attributes: true, attributeFilter: ['data-tema', 'data-modo-modesto', 'data-fundo-animado', 'data-so-fundo']
  });
  if (menosMovimento && menosMovimento.addEventListener) {
    menosMovimento.addEventListener('change', sincronizar);
  }
  setInterval(sincronizar, 3000);
})();
