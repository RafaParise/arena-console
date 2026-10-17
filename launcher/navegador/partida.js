"use strict";
// --------------------------------------------------------------------------
// ARENA no navegador: o jogo aberto por cima da tela (item 12 do plano).
//
// No Windows, o RetroArch abre numa janela dele. No navegador, o ARENA cobre
// a tela com uma camada preta e poe o quadro do jogo (navegador/jogo.html)
// dentro, em tela cheia. Uma faixa fina em cima (some sozinha) lembra as
// teclas e tem o botao de voltar. Quando o jogo fecha, a camada e o quadro
// somem juntos -- e o navegador devolve a memoria do emulador.
//
// "allow" do quadro: de file://, cada arquivo e' de outra origem para o
// Chrome, e o controle (gamepad), a tela cheia e o som so chegam ao quadro
// com a permissao explicita ("*" = este quadro, de qualquer origem).
// --------------------------------------------------------------------------
window.ArenaPartida = (function () {
  const SEGUNDOS_DA_FAIXA = 4;
  let atual = null;

  function elemento(tipo, classe, texto) {
    const e = document.createElement(tipo);
    if (classe) e.className = classe;
    if (texto) e.textContent = texto;
    return e;
  }

  function botao(texto, rotulo, acao) {
    const b = elemento("button", "partida-botao", texto);
    b.type = "button";
    b.setAttribute("aria-label", rotulo);
    b.addEventListener("click", acao);
    return b;
  }

  // Chamado no clique do Jogar, antes de qualquer espera: o navegador so
  // deixa entrar em tela cheia logo depois de um clique.
  function preparar(titulo) {
    if (atual) throw new Error("Já tem um jogo aberto. Feche o jogo (F10) antes de abrir outro.");
    const capa = elemento("div", "partida-navegador");
    capa.setAttribute("role", "dialog");
    capa.setAttribute("aria-label", "Jogando " + titulo);
    const faixa = elemento("div", "partida-faixa");
    const nome = elemento("span", "partida-titulo", titulo);
    const teclas = elemento("span", "partida-teclas", "Esc: menu · F2: salvar · F4: carregar · F10: sair");
    const situacao = elemento("span", "partida-situacao", "Abrindo...");
    const telaCheia = botao("Tela cheia", "Entrar ou sair da tela cheia", alternarTelaCheia);
    const voltar = botao("Voltar ao ARENA", "Fechar o jogo e voltar ao ARENA", sair);
    faixa.append(nome, teclas, situacao, telaCheia, voltar);
    const quadro = document.createElement("iframe");
    quadro.className = "partida-quadro";
    quadro.title = "Jogo: " + titulo;
    quadro.allow = "gamepad *; fullscreen *; autoplay *";
    capa.append(faixa, quadro);
    document.body.append(capa);
    document.body.classList.add("com-partida");
    atual = { capa: capa, faixa: faixa, quadro: quadro, situacao: situacao, pedido: null, ganchos: {},
              medidas: [], relogioFaixa: null, rodando: false, saindo: false };
    capa.addEventListener("mousemove", mostrarFaixa);
    mostrarFaixa();
    if (capa.requestFullscreen) {
      capa.requestFullscreen({ navigationUI: "hide" }).then(travarEsc).catch(function () { /* sem tela cheia: a camada ja cobre a janela */ });
    }
    return atual;
  }

  // Em tela cheia, o Esc e' do jogo (abre o menu, como no Windows); para
  // sair da tela cheia, segura-se o Esc (o Chrome avisa isso na tela).
  function travarEsc() {
    try {
      if (navigator.keyboard && navigator.keyboard.lock) navigator.keyboard.lock(["Escape"]).catch(function () {});
    } catch (falha) { /* navegador sem esse recurso */ }
  }

  function alternarTelaCheia() {
    if (!atual) return;
    if (document.fullscreenElement) document.exitFullscreen().catch(function () {});
    else if (atual.capa.requestFullscreen) atual.capa.requestFullscreen({ navigationUI: "hide" }).then(travarEsc).catch(function () {});
    focar();
  }

  function mostrarFaixa() {
    if (!atual) return;
    atual.faixa.classList.add("partida-faixa--visivel");
    clearTimeout(atual.relogioFaixa);
    atual.relogioFaixa = setTimeout(function () {
      if (atual && atual.rodando) atual.faixa.classList.remove("partida-faixa--visivel");
    }, SEGUNDOS_DA_FAIXA * 1000);
  }

  function focar() {
    if (!atual) return;
    atual.quadro.focus();
    enviar({ tipo: "foco" });
  }

  function enviar(mensagem, transferir) {
    if (atual && atual.quadro.contentWindow) atual.quadro.contentWindow.postMessage(mensagem, "*", transferir || []);
  }

  // pedido: {nucleo, principal, arquivos:[{nome,dados}], sistema, guardados,
  // configuracao, opcoes}; ganchos: {guardados(lista, final), fim(motivo), erro(texto)}.
  function abrir(pedido, ganchos) {
    if (!atual) preparar(pedido.titulo || "jogo");
    atual.pedido = pedido;
    atual.ganchos = ganchos || {};
    window.addEventListener("message", ouvir);
    atual.quadro.src = "navegador/jogo.html";
  }

  function ouvir(evento) {
    if (!atual || evento.source !== atual.quadro.contentWindow) return;
    const m = evento.data || {};
    if (m.arena !== "jogo") return;
    if (m.tipo === "pronto" && atual.pedido) {
      const pedido = atual.pedido;
      atual.pedido = null;              // os dados vao embora (transferidos)
      const transferir = [];
      for (const lista of [pedido.arquivos, pedido.sistema, pedido.guardados]) {
        for (const item of lista || []) {
          if (item.dados instanceof ArrayBuffer) transferir.push(item.dados);
        }
      }
      enviar(Object.assign({ tipo: "abrir" }, pedido), transferir);
    } else if (m.tipo === "carregando") {
      atual.situacao.textContent = "Abrindo o emulador...";
    } else if (m.tipo === "rodando") {
      atual.rodando = true;
      atual.situacao.textContent = "";
      atual.tempos = m.tempos;
      focar();
      mostrarFaixa();
      if (atual.ganchos.rodando) atual.ganchos.rodando(m.tempos);
    } else if (m.tipo === "guardados") {
      if (atual.ganchos.guardados) atual.ganchos.guardados(m.arquivos || [], !!m.final);
    } else if (m.tipo === "medida") {
      const espera = atual.medidas.shift();
      if (espera) espera(m);
    } else if (m.tipo === "erro") {
      mostrarErro(m.texto, m.registro);
      if (atual.ganchos.erro) atual.ganchos.erro(m.texto, m.registro);
    } else if (m.tipo === "fim") {
      fechar(m.motivo, m.registro);
    }
  }

  function mostrarErro(texto, registro) {
    if (!atual) return;
    atual.situacao.textContent = "";
    const caixa = elemento("div", "partida-erro");
    caixa.append(elemento("strong", "", "O jogo não abriu."), elemento("p", "", texto || ""));
    if (registro && registro.length) {
      const detalhe = elemento("details");
      detalhe.append(elemento("summary", "", "Detalhes para o professor"),
                     elemento("pre", "", registro.slice(-20).join("\n")));
      caixa.append(detalhe);
    }
    caixa.append(botao("Voltar ao ARENA", "Voltar ao ARENA", function () { fechar("erro"); }));
    atual.capa.append(caixa);
    atual.faixa.classList.add("partida-faixa--visivel");
  }

  function fechar(motivo, registro) {
    if (!atual) return;
    const fechando = atual;
    atual = null;
    window.removeEventListener("message", ouvir);
    clearTimeout(fechando.relogioFaixa);
    if (document.fullscreenElement) document.exitFullscreen().catch(function () {});
    try { if (navigator.keyboard && navigator.keyboard.unlock) navigator.keyboard.unlock(); } catch (falha) { /* segue */ }
    fechando.quadro.src = "about:blank";
    fechando.capa.remove();
    document.body.classList.remove("com-partida");
    for (const espera of fechando.medidas) espera(null);
    if (fechando.ganchos.fim) fechando.ganchos.fim(motivo || "fechou", registro || []);
  }

  function sair() {
    if (!atual) return;
    if (!atual.rodando) { fechar("cancelado"); return; }
    if (atual.saindo) return;
    atual.saindo = true;
    atual.situacao.textContent = "Guardando o save...";
    enviar({ tipo: "sair" });
    // O quadro responde "fim" depois de copiar os saves. Se ele travar, a
    // tela fecha mesmo assim em 8 s (os saves de 10 em 10 s ja vieram).
    const esta = atual;
    setTimeout(function () { if (atual === esta) fechar("travou"); }, 8000);
  }

  function comando(nome) {
    enviar({ tipo: "comando", nome: nome });
    focar();
  }

  // A contagem de voltas e de imagens do quadro (para o Testar este Chromebook).
  function medir(comRegistro) {
    if (!atual) return Promise.resolve(null);
    return new Promise(function (pronto) {
      atual.medidas.push(pronto);
      enviar({ tipo: "medir", registro: !!comRegistro });
    });
  }

  return { preparar: preparar, abrir: abrir, sair: sair, comando: comando, medir: medir, fechar: fechar,
           aberto: function () { return !!atual; }, rodando: function () { return !!(atual && atual.rodando); } };
})();
