// A tela do celular como controle (servidor\controle_remoto.py).
// O que ela faz: junta os dedos que estao na tela num ESTADO (16 botoes + 4 eixos), manda o estado ao computador pelo
// WebSocket (11 bytes) quando muda e a cada 250 ms ("ainda estou aqui"), e se reconecta sozinha se o Wi-Fi piscar.
// Os numeros dos botoes sao os do RetroPad do libretro: B=0 Y=1 Select=2 Start=3 Cima=4 Baixo=5 Esq=6 Dir=7 A=8 X=9
// L1=10 R1=11 L2=12 R2=13 L3=14 R3=15. Nao ha biblioteca, nem rede alem do proprio computador, nem gravacao de nada.
"use strict";
(() => {
  const $ = (seletor) => document.querySelector(seletor);
  const guardar = {
    ler(chave, padrao) { try { const v = localStorage.getItem(chave); return v === null ? padrao : v; } catch (e) { return padrao; } },
    gravar(chave, valor) { try { localStorage.setItem(chave, valor); } catch (e) { /* sem armazenamento: segue sem lembrar */ } },
  };

  const BATIDA_MS = 250;            // com a tela parada, manda o estado de novo (o computador solta tudo se ficar 1,5 s sem ouvir)
  const ESPERAS = [500, 1000, 2000, 4000];
  const ZONA_MORTA_DO_ANALOGICO = 0.12;

  let botoes = 0;
  const eixos = [0, 0, 0, 0];
  let sujo = true;
  let ultimoEnvio = 0;
  let ws = null;
  let tentativa = 0;
  let desistiu = false;
  let dados = { codigo: "", jogador: 2, apelido: "" };
  const dedos = new Map();          // id do dedo -> {tipo, elemento, ...}

  // ---------- falar com o computador ----------
  function mensagem(texto, bom) {
    const aviso = $("#aviso");
    aviso.textContent = texto;
    aviso.classList.toggle("bom", !!bom);
  }

  function estadoDaConexao(texto, perdida) {
    const rotulo = $("#estadoDaConexao");
    rotulo.textContent = texto;
    rotulo.classList.toggle("perdida", !!perdida);
  }

  function conectar() {
    if (ws) { try { ws.close(); } catch (e) { /* ja fechado */ } }
    const endereco = (location.protocol === "https:" ? "wss://" : "ws://") + location.host + "/ws";
    ws = new WebSocket(endereco);
    ws.binaryType = "arraybuffer";
    const este = ws;
    este.onopen = () => {
      este.send(JSON.stringify({ t: "oi", codigo: dados.codigo, jogador: dados.jogador, apelido: dados.apelido }));
    };
    este.onmessage = (evento) => {
      if (typeof evento.data !== "string") return;
      let m;
      try { m = JSON.parse(evento.data); } catch (e) { return; }
      if (m.t === "ok") {
        tentativa = 0;
        mostrarControle();
        estadoDaConexao("Conectado", false);
        sujo = true;
      } else if (m.t === "erro") {
        desistiu = true;
        mostrarEntrada();
        mensagem(textoDoErro(m), false);
      } else if (m.t === "sem_sinal") {
        sujo = true;                          // o computador soltou os botoes: manda o que esta apertado de novo
      }
    };
    este.onclose = () => {
      if (este !== ws || desistiu) return;
      estadoDaConexao("Sem conexão. Tentando de novo…", true);
      const espera = ESPERAS[Math.min(tentativa, ESPERAS.length - 1)];
      tentativa += 1;
      setTimeout(() => { if (!desistiu && este === ws) conectar(); }, espera);
    };
    este.onerror = () => { /* o onclose cuida */ };
  }

  function textoDoErro(m) {
    if (m.motivo === "codigo") return "Código errado. Confira o número que está na tela do computador. Tentativas que restam: " + (m.restam ?? "?") + ".";
    if (m.motivo === "bloqueado") return "Muitas tentativas erradas. Espere 2 minutos e tente de novo.";
    if (m.motivo === "ocupado") return "Esse jogador já está sendo usado por outro celular. Escolha outro número.";
    if (m.motivo === "jogador") return "Escolha o número do jogador, de 1 a 4.";
    return "O computador recusou a conexão.";
  }

  function enviar() {
    if (!ws || ws.readyState !== 1) return;
    const bytes = new ArrayBuffer(11);
    const v = new DataView(bytes);
    v.setUint8(0, 1);
    v.setUint16(1, botoes, true);
    for (let i = 0; i < 4; i += 1) v.setInt16(3 + i * 2, eixos[i], true);
    ws.send(bytes);
    ultimoEnvio = performance.now();
    sujo = false;
  }

  setInterval(() => {
    if (!ws || ws.readyState !== 1 || $("#controle").hidden) return;
    if (sujo || performance.now() - ultimoEnvio > BATIDA_MS) enviar();
  }, 16);

  // ---------- os dedos ----------
  function alvoDe(x, y) {
    // A cruz inteira vale como UM direcional (as setas tem data-b so para acender), depois os analogicos, depois as teclas.
    const el = document.elementFromPoint(x, y);
    if (!el) return null;
    return el.closest("#cruz") || el.closest(".stick") || el.closest(".tecla[data-b]");
  }

  // O direcional em cruz: a direcao vem do ANGULO do dedo em relacao ao centro, com zona morta no meio.
  // Dois lados juntos (diagonal) quando o dedo esta perto de 45 graus.
  function direcoes(elemento, x, y) {
    const r = elemento.getBoundingClientRect();
    const dx = x - (r.left + r.width / 2);
    const dy = y - (r.top + r.height / 2);
    const dist = Math.hypot(dx, dy);
    if (dist < r.width * 0.14) return 0;
    const ax = dx / dist;
    const ay = dy / dist;
    let bits = 0;
    if (ay < -0.38) bits |= 1 << 4;     // cima
    if (ay > 0.38) bits |= 1 << 5;      // baixo
    if (ax < -0.38) bits |= 1 << 6;     // esquerda
    if (ax > 0.38) bits |= 1 << 7;      // direita
    return bits;
  }

  // O analogico: o dedo puxa a bolinha ate a borda; o eixo vai de -32767 a 32767 (cima e esquerda negativos).
  function puxar(dedo, x, y) {
    const base = dedo.elemento;
    const r = base.getBoundingClientRect();
    const raio = r.width / 2;
    let dx = x - (r.left + raio);
    let dy = y - (r.top + raio);
    const dist = Math.hypot(dx, dy);
    if (dist > raio) { dx = dx / dist * raio; dy = dy / dist * raio; }
    dedo.dx = dx;
    dedo.dy = dy;
    dedo.raio = raio;
  }

  function recalcular() {
    let novoBotoes = 0;
    const novosEixos = [0, 0, 0, 0];
    const acesas = new Set();
    for (const dedo of dedos.values()) {
      if (dedo.tipo === "tecla" && dedo.elemento) {
        novoBotoes |= 1 << Number(dedo.elemento.dataset.b);
        acesas.add(dedo.elemento);
      } else if (dedo.tipo === "cruz") {
        novoBotoes |= dedo.bits;
        acesas.add(dedo.elemento);
      } else if (dedo.tipo === "stick") {
        const nx = dedo.dx / dedo.raio;
        const ny = dedo.dy / dedo.raio;
        const forca = Math.hypot(nx, ny);
        const i = Number(dedo.elemento.dataset.eixos);
        if (forca > ZONA_MORTA_DO_ANALOGICO) {
          novosEixos[i] = Math.round(nx * 32767);
          novosEixos[i + 1] = Math.round(ny * 32767);
        }
        acesas.add(dedo.elemento);
      }
    }
    // o desenho: tecla acesa enquanto ha dedo nela; setas acesas pelo bit; bolinha acompanha o dedo
    for (const el of document.querySelectorAll("#controle [data-b]")) {
      const bit = Number(el.dataset.b);
      el.classList.toggle("ativa", (novoBotoes & (1 << bit)) !== 0 && el.matches(".tecla, .seta"));
    }
    for (const stick of document.querySelectorAll(".stick")) {
      const dedo = [...dedos.values()].find((d) => d.tipo === "stick" && d.elemento === stick);
      const bolinha = stick.querySelector(".bolinha");
      bolinha.style.transform = dedo ? "translate(" + dedo.dx.toFixed(1) + "px," + dedo.dy.toFixed(1) + "px)" : "";
      stick.classList.toggle("ativa", !!dedo);
    }
    if (novoBotoes !== botoes || novosEixos.some((v, i) => v !== eixos[i])) {
      botoes = novoBotoes;
      for (let i = 0; i < 4; i += 1) eixos[i] = novosEixos[i];
      sujo = true;
    }
  }

  function bater(tecla) {
    if (guardar.ler("arena_ctl_vibrar", "1") === "1" && navigator.vibrate) navigator.vibrate(tecla ? 10 : 6);
  }

  function aoTocar(e) {
    if (e.target.closest("#botaoMenu")) return;
    e.preventDefault();
    const alvo = alvoDe(e.clientX, e.clientY);
    if (!alvo) return;
    let dedo;
    if (alvo.matches("#cruz")) dedo = { tipo: "cruz", elemento: alvo, bits: direcoes(alvo, e.clientX, e.clientY) };
    else if (alvo.matches(".stick")) { dedo = { tipo: "stick", elemento: alvo, dx: 0, dy: 0, raio: 1 }; puxar(dedo, e.clientX, e.clientY); }
    else { dedo = { tipo: "tecla", elemento: alvo }; bater(true); }
    dedos.set(e.pointerId, dedo);
    try { e.target.setPointerCapture(e.pointerId); } catch (erro) { /* sem captura: o movimento ainda chega */ }
    recalcular();
  }

  function aoMexer(e) {
    const dedo = dedos.get(e.pointerId);
    if (!dedo) return;
    e.preventDefault();
    if (dedo.tipo === "cruz") dedo.bits = direcoes(dedo.elemento, e.clientX, e.clientY);
    else if (dedo.tipo === "stick") puxar(dedo, e.clientX, e.clientY);
    else {
      // deslizar de um botao para o vizinho: solta um e aperta o outro
      const alvo = alvoDe(e.clientX, e.clientY);
      const bota = alvo && alvo.matches("[data-b]") && alvo.matches(".tecla") ? alvo : null;
      if (bota !== dedo.elemento) { dedo.elemento = bota; if (bota) bater(true); }
    }
    recalcular();
  }

  function aoSoltar(e) {
    if (!dedos.has(e.pointerId)) return;
    dedos.delete(e.pointerId);
    recalcular();
  }

  function soltarTudo() {
    dedos.clear();
    recalcular();
    sujo = true;
  }

  // ---------- telas ----------
  function mostrarControle() {
    $("#entrada").hidden = true;
    $("#controle").hidden = false;
    $("#rotuloDoJogador").textContent = "Jogador " + dados.jogador;
  }

  function mostrarEntrada() {
    soltarTudo();
    $("#controle").hidden = true;
    $("#menu").hidden = true;
    $("#entrada").hidden = false;
  }

  function aplicarModo(modo) {
    document.body.dataset.modo = modo;
    guardar.gravar("arena_ctl_modo", modo);
    for (const radio of document.querySelectorAll("input[name=modo]")) radio.checked = radio.value === modo;
    soltarTudo();
  }

  function pedirTelaCheia() {
    try {
      const raiz = document.documentElement;
      const pedido = raiz.requestFullscreen ? raiz.requestFullscreen() : (raiz.webkitRequestFullscreen ? raiz.webkitRequestFullscreen() : null);
      Promise.resolve(pedido).then(() => { if (screen.orientation && screen.orientation.lock) return screen.orientation.lock("landscape"); }).catch(() => {});
    } catch (e) { /* sem tela cheia: segue */ }
  }

  function iniciar() {
    const params = new URLSearchParams(location.search);
    $("#codigo").value = (params.get("c") || "").replace(/\D/g, "").slice(0, 4);
    const jogador = params.get("j") || guardar.ler("arena_ctl_jogador", "2");
    for (const radio of document.querySelectorAll("input[name=jogador]")) radio.checked = radio.value === jogador;
    $("#apelido").value = params.get("a") || guardar.ler("arena_ctl_apelido", "");
    $("#vibrar").checked = guardar.ler("arena_ctl_vibrar", "1") === "1";
    $("#telaCheia").checked = guardar.ler("arena_ctl_tela_cheia", "1") === "1";
    aplicarModo(guardar.ler("arena_ctl_modo", "direcional"));

    $("#formulario").addEventListener("submit", (e) => {
      e.preventDefault();
      const codigo = $("#codigo").value.replace(/\D/g, "");
      if (codigo.length !== 4) { mensagem("O código tem 4 números.", false); return; }
      const escolhido = document.querySelector("input[name=jogador]:checked");
      dados = { codigo, jogador: Number(escolhido ? escolhido.value : 2), apelido: $("#apelido").value.trim().slice(0, 20) };
      guardar.gravar("arena_ctl_jogador", String(dados.jogador));
      guardar.gravar("arena_ctl_apelido", dados.apelido);
      desistiu = false;
      mensagem("Conectando…", true);
      if ($("#telaCheia").checked) pedirTelaCheia();
      conectar();
    });

    const controle = $("#controle");
    controle.addEventListener("pointerdown", aoTocar);
    controle.addEventListener("pointermove", aoMexer);
    controle.addEventListener("pointerup", aoSoltar);
    controle.addEventListener("pointercancel", aoSoltar);
    controle.addEventListener("lostpointercapture", aoSoltar);
    document.addEventListener("contextmenu", (e) => e.preventDefault());
    document.addEventListener("touchmove", (e) => { if (!$("#controle").hidden) e.preventDefault(); }, { passive: false });
    document.addEventListener("gesturestart", (e) => e.preventDefault());

    $("#botaoMenu").addEventListener("click", () => { $("#menu").hidden = false; soltarTudo(); });
    $("#fecharMenu").addEventListener("click", () => { $("#menu").hidden = true; });
    for (const radio of document.querySelectorAll("input[name=modo]")) radio.addEventListener("change", () => aplicarModo(radio.value));
    $("#vibrar").addEventListener("change", (e) => guardar.gravar("arena_ctl_vibrar", e.target.checked ? "1" : "0"));
    $("#telaCheia").addEventListener("change", (e) => {
      guardar.gravar("arena_ctl_tela_cheia", e.target.checked ? "1" : "0");
      if (e.target.checked) pedirTelaCheia(); else if (document.fullscreenElement) document.exitFullscreen();
    });
    $("#sair").addEventListener("click", () => {
      desistiu = true;
      if (ws && ws.readyState === 1) ws.send(JSON.stringify({ t: "tchau" }));
      if (ws) ws.close();
      mostrarEntrada();
      mensagem("Desconectado.", true);
    });

    // tela apagou ou trocou de app: solta tudo (o computador tambem solta depois de 1,5 s sem ouvir)
    document.addEventListener("visibilitychange", () => { if (document.hidden) { soltarTudo(); enviar(); } });
    window.addEventListener("pagehide", () => { if (ws && ws.readyState === 1) ws.send(JSON.stringify({ t: "tchau" })); });

    // para os testes: o que o controle acha que esta apertado
    window.__controle = { estado: () => ({ botoes, eixos: eixos.slice() }), conectado: () => !!ws && ws.readyState === 1 };

    if (/^\d{4}$/.test($("#codigo").value)) $("#conectar").focus(); else $("#codigo").focus();
  }

  iniciar();
})();
