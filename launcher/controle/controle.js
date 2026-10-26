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
  let DIGITOS = 6;                  // quantos numeros tem o codigo (o computador diz em /jogadores)

  // Os ajustes de cada um (guardados so neste celular) e os 3 perfis, como no GameSir Nexus. Padrao = o de sempre.
  const AJUSTES_PADRAO = { modo: "direcional", zona: 12, curva: "linear", diagonal: 38, escala: 100, canhoto: false,
                           inclinar: false, inverterInclinacao: false };
  let ajustes = Object.assign({}, AJUSTES_PADRAO);
  const inclinacao = { eixo: 0, zero: 0, angulo: 0 };          // o volante: o eixo de agora e a posicao "reta"

  // ==== contas puras (testadas em servidor/tests/test_contas_do_controle.py, com o Node.js) ====
  // Zona morta e curva do analogico (o que o GameSir Nexus chama de "dead zone" e curva de resposta). (nx, ny) e' a
  // posicao do dedo de -1 a 1; a zona morta e' o tanto de curso que nao vale nada (de 0 a 0,4); depois dela o curso
  // volta a comecar do zero, para o personagem nao "pular" do parado para o andando.
  function aplicarZonaECurva(nx, ny, zona, curva) {
    const forca = Math.hypot(nx, ny);
    if (forca === 0 || forca <= zona) return [0, 0];
    let f = Math.min(1, (forca - zona) / (1 - zona));
    if (curva === "suave") f = f * f;                  // fino no comeco: bom para mirar
    else if (curva === "rapida") f = Math.sqrt(f);     // forte no comeco: bom para correr
    return [nx / forca * f, ny / forca * f];
  }

  // O direcional em cruz: a direcao vem do ANGULO do dedo em relacao ao centro, com zona morta no meio. 'limite' e' o
  // quanto de cada lado o dedo precisa ter (cosseno) para contar: menor = as diagonais saem mais facil (o "ajuste das
  // diagonais" do Nexus). Dois lados juntos (diagonal) quando o dedo esta perto de 45 graus.
  function bitsDoDirecional(dx, dy, largura, limite) {
    const dist = Math.hypot(dx, dy);
    if (dist < largura * 0.14) return 0;
    const ax = dx / dist;
    const ay = dy / dist;
    let bits = 0;
    if (ay < -limite) bits |= 1 << 4;     // cima
    if (ay > limite) bits |= 1 << 5;      // baixo
    if (ax < -limite) bits |= 1 << 6;     // esquerda
    if (ax > limite) bits |= 1 << 7;      // direita
    return bits;
  }

  // Inclinar o celular deitado para virar (volante): 'angulo' e' o quanto ele esta girado em graus (de -90 a 90, 0 =
  // reto); 'maximo' e' o giro que vale o curso inteiro. Devolve o eixo de -32767 a 32767, ja com zona morta e curva.
  function eixoDaInclinacao(angulo, maximo, zona, curva, inverter) {
    const n = Math.max(-1, Math.min(1, angulo / maximo)) * (inverter ? -1 : 1);
    return Math.round(aplicarZonaECurva(n, 0, zona, curva)[0] * 32767);
  }
  // ==== fim das contas puras ====

  let botoes = 0;
  const eixos = [0, 0, 0, 0];
  let sujo = true;
  let ultimoEnvio = 0;
  let ws = null;
  let tentativa = 0;
  let desistiu = false;
  let dados = { codigo: "", jogador: 2, apelido: "" };
  let jogadorPedido = "";           // o jogador que veio no endereco (o cabo USB): a conexao automatica so vale para ele
  let pelaCabo = false;             // a pagina veio por 127.0.0.1: o cabo USB (menor atraso, e o navegador libera o sensor)
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
        estadoDaConexao(pelaCabo ? "Conectado pelo cabo" : "Conectado", false);
        sujo = true;
      } else if (m.t === "erro") {
        desistiu = true;
        mostrarEntrada();
        mensagem(textoDoErro(m), false);
      } else if (m.t === "sem_sinal") {
        sujo = true;                          // o computador soltou os botoes: manda o que esta apertado de novo
      } else if (m.t === "q") {
        medirIdaEVolta(m.n);
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
    if (m.motivo === "muitas") return "Muitos códigos errados ao mesmo tempo. Espere uns 10 segundos, olhe o código na tela do computador e toque em Conectar de novo.";
    if (m.motivo === "ocupado") return "Esse jogador já está sendo usado por outro celular. Escolha outro número.";
    if (m.motivo === "jogador") {
      const liberados = (m.jogadores || []).join(", ");
      return "Esse jogador não foi liberado para o celular" + (liberados ? ". Escolha " + liberados + "." : ": peça ao professor para liberar.");
    }
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

  // Menor latencia: o estado sai NA HORA em que o dedo muda (e nao no proximo tique de 16 ms). O intervalo acima fica
  // so para o "ainda estou aqui" e para o que ficou preso; um intervalo minimo de 4 ms evita enxurrada com varios dedos.
  function enviarJa() {
    if (!ws || ws.readyState !== 1 || $("#controle").hidden) return;
    if (performance.now() - ultimoEnvio >= 4) enviar();
  }

  // A ida e volta ate o computador, medida aqui (so este lado tem o relogio): um "ping" a cada 2 s, suavizado com os
  // ultimos 5, mostrado no alto e mandado ao computador (que mostra na lista de celulares).
  const idas = new Map();
  const ultimas = [];
  let numeroDoPing = 0;
  setInterval(() => {
    if (!ws || ws.readyState !== 1 || $("#controle").hidden) return;
    numeroDoPing += 1;
    idas.set(numeroDoPing, performance.now());
    for (const antigo of [...idas.keys()]) if (antigo < numeroDoPing - 5) idas.delete(antigo);
    ws.send(JSON.stringify({ t: "p", n: numeroDoPing }));
  }, 2000);

  function medirIdaEVolta(n) {
    const saida = idas.get(n);
    if (saida === undefined) return;
    idas.delete(n);
    ultimas.push(performance.now() - saida);
    if (ultimas.length > 5) ultimas.shift();
    const ordenadas = [...ultimas].sort((a, b) => a - b);
    const mediana = ordenadas[Math.floor(ordenadas.length / 2)];
    const rotulo = $("#rtt");
    rotulo.textContent = Math.round(mediana) + " ms";
    rotulo.className = "rtt " + (mediana < 25 ? "rapida" : mediana < 60 ? "media" : "lenta");
    if (ws && ws.readyState === 1) ws.send(JSON.stringify({ t: "rtt", ms: Math.round(mediana) }));
  }

  // ---------- os dedos ----------
  function alvoDe(x, y) {
    // A cruz inteira vale como UM direcional (as setas tem data-b so para acender), depois os analogicos, depois as teclas.
    const el = document.elementFromPoint(x, y);
    if (!el) return null;
    return el.closest("#cruz") || el.closest(".stick") || el.closest(".tecla[data-b]");
  }

  function direcoes(elemento, x, y) {
    const r = elemento.getBoundingClientRect();
    return bitsDoDirecional(x - (r.left + r.width / 2), y - (r.top + r.height / 2), r.width, ajustes.diagonal / 100);
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
        const i = Number(dedo.elemento.dataset.eixos);
        const [vx, vy] = aplicarZonaECurva(dedo.dx / dedo.raio, dedo.dy / dedo.raio, ajustes.zona / 100, ajustes.curva);
        novosEixos[i] = Math.round(vx * 32767);
        novosEixos[i + 1] = Math.round(vy * 32767);
        acesas.add(dedo.elemento);
      }
    }
    if (ajustes.inclinar && novosEixos[0] === 0) novosEixos[0] = inclinacao.eixo;
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
      enviarJa();
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

  // ---------- ajustes e perfis ----------
  // O que vem do armazenamento do navegador e' dado de fora: so entra o que a pagina conhece, dentro dos limites.
  function limparAjustes(bruto) {
    const a = Object.assign({}, AJUSTES_PADRAO);
    if (!bruto || typeof bruto !== "object") return a;
    const numero = (v, minimo, maximo, padrao) => {
      const n = Number(v);
      return Number.isFinite(n) ? Math.max(minimo, Math.min(maximo, Math.round(n))) : padrao;
    };
    if (["direcional", "analogico", "dois"].includes(bruto.modo)) a.modo = bruto.modo;
    a.zona = numero(bruto.zona, 0, 40, a.zona);
    if (["linear", "suave", "rapida"].includes(bruto.curva)) a.curva = bruto.curva;
    a.diagonal = numero(bruto.diagonal, 25, 55, a.diagonal);
    a.escala = numero(bruto.escala, 80, 130, a.escala);
    a.canhoto = bruto.canhoto === true;
    a.inclinar = bruto.inclinar === true;
    a.inverterInclinacao = bruto.inverterInclinacao === true;
    return a;
  }

  function lerPerfis() {
    try {
      const perfis = JSON.parse(guardar.ler("arena_ctl_perfis", "{}"));
      return perfis && typeof perfis === "object" ? perfis : {};
    } catch (e) { return {}; }
  }

  let perfilAtual = "1";

  function aplicarAjustes() {
    document.body.dataset.modo = ajustes.modo;
    document.body.classList.toggle("canhoto", ajustes.canhoto);
    document.documentElement.style.setProperty("--escala", String(ajustes.escala / 100));
    for (const radio of document.querySelectorAll("input[name=modo]")) radio.checked = radio.value === ajustes.modo;
    $("#zona").value = String(ajustes.zona);
    $("#zonaValor").textContent = ajustes.zona + "%";
    $("#curva").value = ajustes.curva;
    $("#diagonal").value = String(ajustes.diagonal);
    $("#diagonalValor").textContent = ajustes.diagonal < 34 ? "fácil" : ajustes.diagonal > 44 ? "difícil" : "normal";
    $("#escala").value = String(ajustes.escala);
    $("#escalaValor").textContent = ajustes.escala + "%";
    $("#canhoto").checked = ajustes.canhoto;
    $("#inclinar").checked = ajustes.inclinar;
    $("#inverterInclinacao").checked = ajustes.inverterInclinacao;
    ligarInclinacao();
    guardar.gravar("arena_ctl_ajustes", JSON.stringify(ajustes));
    soltarTudo();
  }

  // O volante: so quando o navegador deixa ler o sensor. Pelo Wi-Fi (http de rede) o Chrome nao deixa; pelo cabo USB, o
  // endereco 127.0.0.1 e' "contexto seguro" e deixa. Mede o giro do celular deitado pela gravidade (o acelerometro: o
  // giroscopio nem todo celular tem).
  let ouvindoMovimento = false;
  let calibrar = true;
  function ligarInclinacao() {
    const possivel = window.isSecureContext && "DeviceMotionEvent" in window;
    $("#linhaInclinar").hidden = !possivel;
    const ligar = possivel && ajustes.inclinar;
    if (ligar && !ouvindoMovimento) { window.addEventListener("devicemotion", aoMover); ouvindoMovimento = true; calibrar = true; }
    if (!ligar && ouvindoMovimento) { window.removeEventListener("devicemotion", aoMover); ouvindoMovimento = false; }
    if (!ligar) inclinacao.eixo = 0;
  }

  function aoMover(e) {
    const g = e.accelerationIncludingGravity;
    if (!g || typeof g.x !== "number" || typeof g.y !== "number") return;
    const lado = screen.orientation ? screen.orientation.angle : (typeof window.orientation === "number" ? (window.orientation + 360) % 360 : 90);
    const sinal = lado === 270 ? -1 : 1;             // deitado para a esquerda (90) ou para a direita (270)
    inclinacao.angulo = Math.atan2(sinal * g.y, sinal * g.x) * 180 / Math.PI;
    if (calibrar) { inclinacao.zero = inclinacao.angulo; calibrar = false; }
    const eixo = $("#menu").hidden ? eixoDaInclinacao(inclinacao.angulo - inclinacao.zero, 40, ajustes.zona / 100, ajustes.curva, ajustes.inverterInclinacao) : 0;
    if (Math.abs(eixo - inclinacao.eixo) >= 256 || (eixo === 0) !== (inclinacao.eixo === 0)) { inclinacao.eixo = eixo; recalcular(); }
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
    ajustes.modo = modo;
    aplicarAjustes();
  }

  function pedirTelaCheia() {
    try {
      const raiz = document.documentElement;
      const pedido = raiz.requestFullscreen ? raiz.requestFullscreen() : (raiz.webkitRequestFullscreen ? raiz.webkitRequestFullscreen() : null);
      Promise.resolve(pedido).then(() => { if (screen.orientation && screen.orientation.lock) return screen.orientation.lock("landscape"); }).catch(() => {});
    } catch (e) { /* sem tela cheia: segue */ }
  }

  function iniciar() {
    // O ARENA abre esta pagina no celular pelo cabo USB (servidor/controle_usb.py) com o codigo depois do "#": o navegador
    // nao o manda a servidor nenhum. Lido, sai do endereco (nem fica na barra nem no historico).
    const params = new URLSearchParams(location.hash.replace(/^#/, "") || location.search);
    const veioPeloEndereco = /^\d{4,12}$/.test(params.get("c") || "");
    if (location.hash || location.search) { try { history.replaceState(null, "", location.pathname); } catch (e) { /* segue */ } }
    pelaCabo = ["127.0.0.1", "localhost", "[::1]"].includes(location.hostname);
    $("#codigo").value = (params.get("c") || "").replace(/\D/g, "").slice(0, DIGITOS);
    jogadorPedido = params.get("j") || "";
    const jogador = params.get("j") || guardar.ler("arena_ctl_jogador", "2");
    for (const radio of document.querySelectorAll("input[name=jogador]")) radio.checked = radio.value === jogador;
    $("#apelido").value = params.get("a") || guardar.ler("arena_ctl_apelido", "");
    $("#vibrar").checked = guardar.ler("arena_ctl_vibrar", "1") === "1";
    $("#telaCheia").checked = guardar.ler("arena_ctl_tela_cheia", "1") === "1";
    perfilAtual = ["1", "2", "3"].includes(guardar.ler("arena_ctl_perfil", "1")) ? guardar.ler("arena_ctl_perfil", "1") : "1";
    let salvo = null;
    try { salvo = JSON.parse(guardar.ler("arena_ctl_ajustes", "null")); } catch (e) { salvo = null; }
    ajustes = limparAjustes(salvo || { modo: guardar.ler("arena_ctl_modo", "direcional") });
    $("#perfil").value = perfilAtual;
    aplicarAjustes();

    $("#formulario").addEventListener("submit", (e) => {
      e.preventDefault();
      const codigo = $("#codigo").value.replace(/\D/g, "");
      if (codigo.length !== DIGITOS) { mensagem("O código tem " + DIGITOS + " números.", false); return; }
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

    const mudar = (campo, valor) => { ajustes[campo] = valor; aplicarAjustes(); };
    $("#zona").addEventListener("input", (e) => mudar("zona", Number(e.target.value)));
    $("#curva").addEventListener("change", (e) => mudar("curva", e.target.value));
    $("#diagonal").addEventListener("input", (e) => mudar("diagonal", Number(e.target.value)));
    $("#escala").addEventListener("input", (e) => mudar("escala", Number(e.target.value)));
    $("#canhoto").addEventListener("change", (e) => mudar("canhoto", e.target.checked));
    $("#inclinar").addEventListener("change", (e) => mudar("inclinar", e.target.checked));
    $("#inverterInclinacao").addEventListener("change", (e) => mudar("inverterInclinacao", e.target.checked));
    $("#calibrar").addEventListener("click", () => { calibrar = true; });
    $("#perfil").addEventListener("change", (e) => {
      perfilAtual = e.target.value;
      guardar.gravar("arena_ctl_perfil", perfilAtual);
      ajustes = limparAjustes(lerPerfis()[perfilAtual]);
      aplicarAjustes();
      $("#avisoDoMenu").textContent = "Perfil " + perfilAtual + (lerPerfis()[perfilAtual] ? " aberto." : " ainda está vazio: está com os ajustes de fábrica.");
    });
    $("#guardarPerfil").addEventListener("click", () => {
      const perfis = lerPerfis();
      perfis[perfilAtual] = ajustes;
      guardar.gravar("arena_ctl_perfis", JSON.stringify(perfis));
      $("#avisoDoMenu").textContent = "Ajustes guardados no perfil " + perfilAtual + ".";
    });
    $("#ajustesDeFabrica").addEventListener("click", () => {
      ajustes = Object.assign({}, AJUSTES_PADRAO);
      aplicarAjustes();
      $("#avisoDoMenu").textContent = "Ajustes de fábrica (guarde num perfil se quiser ficar com eles).";
    });
    $("#botaoMenu").addEventListener("click", () => { $("#menu").hidden = false; soltarTudo(); inclinacao.eixo = 0; });
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
    window.__controle = { estado: () => ({ botoes, eixos: eixos.slice() }), conectado: () => !!ws && ws.readyState === 1,
                          ajustes: () => Object.assign({}, ajustes), pelaCabo: () => pelaCabo };

    if (new RegExp("^\\d{" + DIGITOS + "}$").test($("#codigo").value)) $("#conectar").focus(); else $("#codigo").focus();
    const pronto = liberados();
    // Veio do cabo USB com o codigo no endereco: o professor ja escolheu esta tela, entao conecta sem pedir mais um toque.
    if (veioPeloEndereco) {
      pronto.then(() => {
        const escolhido = document.querySelector("input[name=jogador]:checked");
        // So conecta sozinha se o jogador que o professor pediu (j) continua liberado; senao deixa a escolha na tela.
        if (!$("#entrada").hidden && !ws && escolhido && !escolhido.disabled && escolhido.value === jogadorPedido) $("#conectar").click();
      });
    }
  }

  // O computador diz quais jogadores o professor liberou para o celular (e quantos numeros tem o codigo).
  function liberados() {
    return fetch("/jogadores", { cache: "no-store" }).then((r) => r.json()).then((d) => {
      if (d.digitos) {
        DIGITOS = d.digitos;
        $("#codigo").maxLength = DIGITOS;
        $("#codigo").placeholder = "0".repeat(DIGITOS);
        $("#digitosDoCodigo").textContent = String(DIGITOS);
      }
      const lista = d.jogadores || [];
      let marcado = document.querySelector("input[name=jogador]:checked");
      for (const radio of document.querySelectorAll("input[name=jogador]")) {
        const livre = lista.includes(Number(radio.value));
        radio.disabled = !livre;
        radio.closest("label").style.opacity = livre ? "" : "0.35";
      }
      if (marcado && marcado.disabled) {
        marcado.checked = false;
        const primeiro = [...document.querySelectorAll("input[name=jogador]")].find((r) => !r.disabled);
        if (primeiro) primeiro.checked = true;
      }
      if (!lista.length) mensagem("O professor ainda não liberou nenhum jogador para o celular.", false);
    }).catch(() => { /* sem a lista: o computador confere do mesmo jeito na hora de conectar */ });
  }

  iniciar();
})();
