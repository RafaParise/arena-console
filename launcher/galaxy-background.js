// ==========================================================================
// ARENA - fundo do tema ESCURO: um ceu de galaxia em pixel art (canvas).
//
// Mesmo esquema do field-background.js (leia o comentario de la):
// 160 x 90 pontos esticados pelo CSS, camada fixa desenhada uma vez,
// 30 quadros por segundo, e tres jeitos de mostrar (automatico, sempre,
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
  const PISTA = 69;            // altura da pista de luz (abaixo dos Metroides e do planeta)

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

  // Space Invaders (1978): tres invasores marcham la em cima, passo a
  // passo, trocando de pose a cada passo -- e vao embora.
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

  function iniciarInvasores() {
    const dir = aleatorio() < 0.5 ? 1 : -1;
    return { dir: dir, x: dir === 1 ? -50 : W + 4, y: 4, passoMarcha: 0, pose: 0, desenhar: desenharInvasores };
  }

  function desenharInvasores(passo) {
    this.passoMarcha += passo;
    if (this.passoMarcha >= 14) {        // a marcha: um passo de 3 pontos
      this.passoMarcha = 0;
      this.x += this.dir * 3;
      this.pose = 1 - this.pose;
    }
    for (let i = 0; i < 3; i++) {
      S.colar(ctx, INVASOR[this.pose], this.x + i * 15, this.y, 1);
    }
    return this.dir === 1 ? this.x < W + 4 : this.x > -50;
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

  const VISITAS = { fzero: iniciarFzero, kirby: iniciarKirby, invasores: iniciarInvasores, arwing: iniciarArwing };
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
      esperaVisita = 1200 + aleatorio() * 900;      // 20 a 35 s
    }
  }

  // Para os testes chamarem uma visita na hora (testes\\teste_fundos_animados.py).
  window.__fundoEscuro = {
    visitas: Object.keys(VISITAS),
    chamar: function (nome) { if (VISITAS[nome]) visita = VISITAS[nome](); return !!visita; },
    rodando: function () { return !!visita; },
    velocidade: function (v) { velocidade = Math.max(1, Math.min(16, Number(v) || 1)); return velocidade; }
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
    const escolha = document.body.dataset.fundoAnimado || 'automatico';
    if (escolha === 'parado') return 'parado';
    if (escolha === 'sempre') return 'animado';
    if (document.body.dataset.modoModesto === 'true') return 'parado';
    if (menosMovimento && menosMovimento.matches) return 'parado';
    return 'animado';
  }

  const INTERVALO = 1000 / 30;
  let velocidade = 1;   // so os testes aceleram (__fundoEscuro.velocidade)
  let geracao = 0;
  let ultimo = 0;
  let modoAtual = null;

  function iniciarLaco() {
    const minha = ++geracao;
    ultimo = 0;
    function quadro(agora) {
      if (minha !== geracao) return;
      requestAnimationFrame(quadro);
      if (ultimo && agora - ultimo < INTERVALO - 2) return;
      const passo = (ultimo ? Math.min(4, (agora - ultimo) / (1000 / 60)) : 1) * velocidade;
      ultimo = agora;
      t += passo;
      try {
        desenharQuadro(passo);
      } catch (e) {
        console.error('Fundo galactico: erro num quadro, seguindo pro proximo.', e);
      }
    }
    requestAnimationFrame(quadro);
  }

  function sincronizar() {
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
    attributes: true, attributeFilter: ['data-tema', 'data-modo-modesto', 'data-fundo-animado']
  });
  if (menosMovimento && menosMovimento.addEventListener) {
    menosMovimento.addEventListener('change', sincronizar);
  }
  setInterval(sincronizar, 3000);
})();
