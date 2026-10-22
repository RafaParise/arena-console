"use strict";
// --------------------------------------------------------------------------
// ARENA no navegador: o controle de toque (auditoria 4, 22/10/2026).
//
// No celular e no tablet sem controle, o jogo do navegador nao tinha como
// ser jogado: so havia teclado. Este controle desenha os botoes na tela e
// manda as MESMAS teclas que o ARENA do Windows usa no RetroArch (as setas,
// X = A, Z = B, S = X, A = Y, Q = L, W = R, Enter = Start, Shift direito =
// Select), como eventos de teclado no proprio quadro do jogo. MENU, SALVAR,
// CARREGAR e SAIR usam os comandos do quadro (navegador/jogo.js). O SAIR
// pede um segundo toque, como o F10 duas vezes no computador.
//
// Aparece so em tela de toque; some quando um controle de verdade e' ligado
// ou quando alguem usa o teclado, e volta no proximo toque.
// --------------------------------------------------------------------------
(function () {
  const jogo = window.ArenaJogo;
  if (!jogo) return;
  const temToque = (navigator.maxTouchPoints || 0) > 0 ||
    (window.matchMedia && window.matchMedia("(pointer: coarse)").matches);
  if (!temToque) return;

  const TECLAS = {
    cima: ["ArrowUp", "ArrowUp", 38], baixo: ["ArrowDown", "ArrowDown", 40],
    esquerda: ["ArrowLeft", "ArrowLeft", 37], direita: ["ArrowRight", "ArrowRight", 39],
    a: ["x", "KeyX", 88], b: ["z", "KeyZ", 90], x: ["s", "KeyS", 83], y: ["a", "KeyA", 65],
    l: ["q", "KeyQ", 81], r: ["w", "KeyW", 87], start: ["Enter", "Enter", 13], select: ["Shift", "ShiftRight", 16],
  };
  const apertadas = new Set();

  function tecla(nome, apertar) {
    if (apertar === apertadas.has(nome)) return;
    if (apertar) apertadas.add(nome); else apertadas.delete(nome);
    const [key, code, keyCode] = TECLAS[nome];
    const evento = new KeyboardEvent(apertar ? "keydown" : "keyup",
      { key: key, code: code, bubbles: true, cancelable: true });
    Object.defineProperty(evento, "keyCode", { get: function () { return keyCode; } });
    Object.defineProperty(evento, "which", { get: function () { return keyCode; } });
    evento.arenaToque = true;
    jogo.canvas.dispatchEvent(evento);
  }

  function vibrar() {
    try { if (navigator.vibrate) navigator.vibrate(8); } catch (falha) { /* sem vibracao */ }
  }

  const estilo = document.createElement("style");
  estilo.textContent = [
    "#toque{position:fixed;inset:0;pointer-events:none;z-index:10;font:700 16px system-ui,sans-serif;",
    "user-select:none;-webkit-user-select:none;touch-action:none}",
    "#toque[hidden]{display:none}",
    "#toque .t{position:absolute;pointer-events:auto;display:flex;align-items:center;justify-content:center;",
    "color:#fff;background:rgba(30,32,40,.55);border:2px solid rgba(255,255,255,.6);touch-action:none;",
    "-webkit-tap-highlight-color:transparent;box-sizing:border-box}",
    "#toque .t.on{background:rgba(255,255,255,.4)}",
    "#toque .redondo{width:14vmin;height:14vmin;border-radius:50%;font-size:6vmin}",
    "#toque .pilula{height:9vmin;min-width:16vmin;padding:0 2.5vmin;border-radius:5vmin;font-size:3.6vmin}",
    "#toque .sair{background:rgba(198,40,40,.75)}",
    "#toque .dpad{width:40vmin;height:40vmin;left:max(3vmin,env(safe-area-inset-left));bottom:5vmin;",
    "border-radius:50%;font-size:6vmin}",
    "#toque .dpad span{position:absolute;opacity:.85}",
    "#toque .botoes{position:absolute;width:40vmin;height:40vmin;right:max(3vmin,env(safe-area-inset-right));",
    "bottom:5vmin;pointer-events:none}",
    "#toque .topo{position:absolute;top:max(2vmin,env(safe-area-inset-top));left:0;right:0;display:flex;",
    "justify-content:center;gap:2vmin;pointer-events:none}",
    "#toque .topo .t{position:static}",
  ].join("");
  document.head.appendChild(estilo);

  const caixa = document.createElement("div");
  caixa.id = "toque";
  caixa.setAttribute("aria-hidden", "true");

  function botao(texto, classe, estiloPosicao) {
    const b = document.createElement("div");
    b.className = "t " + classe;
    b.textContent = texto;
    if (estiloPosicao) b.style.cssText = estiloPosicao;
    return b;
  }

  // Um botao que segura a tecla enquanto o dedo esta nele.
  function segurar(elemento, nome) {
    elemento.addEventListener("pointerdown", function (e) {
      e.preventDefault();
      elemento.setPointerCapture(e.pointerId);
      elemento.classList.add("on");
      vibrar();
      tecla(nome, true);
    });
    const soltar = function () { elemento.classList.remove("on"); tecla(nome, false); };
    elemento.addEventListener("pointerup", soltar);
    elemento.addEventListener("pointercancel", soltar);
  }

  // Um botao de comando (um toque, uma acao).
  function tocar(elemento, acao) {
    elemento.addEventListener("pointerdown", function (e) {
      e.preventDefault();
      elemento.classList.add("on");
      vibrar();
    });
    elemento.addEventListener("pointerup", function () { elemento.classList.remove("on"); acao(); });
    elemento.addEventListener("pointercancel", function () { elemento.classList.remove("on"); });
  }

  // O direcional: uma area so, com as diagonais (o dedo desliza sem soltar).
  const dpad = botao("", "dpad");
  for (const [seta, lugar] of [["▲", "top:6%;left:43%"], ["▼", "bottom:6%;left:43%"],
                               ["◀", "left:7%;top:41%"], ["▶", "right:7%;top:41%"]]) {
    const s = document.createElement("span");
    s.textContent = seta;
    s.style.cssText = lugar;
    dpad.append(s);
  }
  function direcoes(e) {
    const r = dpad.getBoundingClientRect();
    const dx = (e.clientX - r.left) / r.width - 0.5;
    const dy = (e.clientY - r.top) / r.height - 0.5;
    const agora = new Set();
    if (Math.hypot(dx, dy) < 0.12) return agora;          // o centro: nada
    const angulo = Math.atan2(dy, dx) * 180 / Math.PI;     // 0 = direita, 90 = baixo
    if (angulo > -67.5 && angulo < 67.5) agora.add("direita");
    if (angulo > 22.5 && angulo < 157.5) agora.add("baixo");
    if (angulo > 112.5 || angulo < -112.5) agora.add("esquerda");
    if (angulo > -157.5 && angulo < -22.5) agora.add("cima");
    return agora;
  }
  function aplicar(agora) {
    for (const nome of ["cima", "baixo", "esquerda", "direita"]) tecla(nome, agora.has(nome));
    dpad.classList.toggle("on", agora.size > 0);
  }
  dpad.addEventListener("pointerdown", function (e) {
    e.preventDefault();
    dpad.setPointerCapture(e.pointerId);
    vibrar();
    aplicar(direcoes(e));
  });
  dpad.addEventListener("pointermove", function (e) { if (dpad.hasPointerCapture(e.pointerId)) aplicar(direcoes(e)); });
  for (const fim of ["pointerup", "pointercancel"]) dpad.addEventListener(fim, function () { aplicar(new Set()); });

  // A, B, X e Y em losango, como no controle do Super Nintendo.
  const botoes = document.createElement("div");
  botoes.className = "botoes";
  for (const [nome, texto, lugar] of [["a", "A", "right:0;top:13vmin"], ["b", "B", "left:13vmin;bottom:0"],
                                       ["x", "X", "left:13vmin;top:0"], ["y", "Y", "left:0;top:13vmin"]]) {
    const b = botao(texto, "redondo", lugar);
    segurar(b, nome);
    botoes.append(b);
  }

  const l = botao("L", "pilula", "left:max(3vmin,env(safe-area-inset-left));bottom:48vmin");
  const r = botao("R", "pilula", "right:max(3vmin,env(safe-area-inset-right));bottom:48vmin");
  const select = botao("SELECT", "pilula", "left:calc(50% - 19vmin);bottom:4vmin");
  const start = botao("START", "pilula", "left:calc(50% + 3vmin);bottom:4vmin");
  segurar(l, "l");
  segurar(r, "r");
  segurar(select, "select");
  segurar(start, "start");

  const topo = document.createElement("div");
  topo.className = "topo";
  const menu = botao("☰ MENU", "pilula");
  const salvar = botao("SALVAR", "pilula");
  const carregar = botao("CARREGAR", "pilula");
  const sair = botao("✕ SAIR", "pilula sair");
  tocar(menu, function () { jogo.comando("menu"); });
  tocar(salvar, function () { jogo.comando("salvar_estado"); });
  tocar(carregar, function () { jogo.comando("carregar_estado"); });
  let confirmar = null;
  tocar(sair, function () {
    if (confirmar) {
      clearTimeout(confirmar);
      jogo.sair();
      return;
    }
    sair.textContent = "TOQUE DE NOVO";
    confirmar = setTimeout(function () { confirmar = null; sair.textContent = "✕ SAIR"; }, 2500);
  });
  topo.append(menu, salvar, carregar, sair);

  caixa.append(dpad, botoes, l, r, select, start, topo);
  document.body.appendChild(caixa);

  // Some com controle de verdade ou com o teclado; volta no proximo toque.
  function haControle() {
    const lista = navigator.getGamepads ? Array.from(navigator.getGamepads()) : [];
    return lista.some(Boolean);
  }
  function mostrar(sim) {
    if (!sim) for (const nome of Array.from(apertadas)) tecla(nome, false);
    caixa.hidden = !sim;
  }
  window.addEventListener("gamepadconnected", function () { mostrar(false); });
  window.addEventListener("gamepaddisconnected", function () { mostrar(!haControle()); });
  window.addEventListener("keydown", function (e) { if (e.isTrusted && !e.arenaToque) mostrar(false); }, true);
  window.addEventListener("pointerdown", function (e) {
    if (e.pointerType === "touch" && caixa.hidden && !haControle()) mostrar(true);
  }, true);
  mostrar(!haControle());
})();
