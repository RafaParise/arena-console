// ---------------------------------------------------------------------------
// Assistente de configuração para controles genéricos
// Pressione cada botão quando pedido — o ARENA detecta qual foi e grava.
// ---------------------------------------------------------------------------

const PASSOS_WIZARD = [
  { botao: "b", texto: "Qual é o botão A (ou X no PlayStation)? Pressione agora." },
  { botao: "a", texto: "Qual é o botão B (ou Circulo no PlayStation)? Pressione agora." },
  { botao: "y", texto: "Qual é o botão Y (ou Quadrado no PlayStation)? Pressione agora." },
  { botao: "x", texto: "Qual é o botão X (ou Triângulo no PlayStation)? Pressione agora." },
  { botao: "l", texto: "Qual é o botão esquerdo (LB ou L1)? Pressione agora." },
  { botao: "r", texto: "Qual é o botão direito (RB ou R1)? Pressione agora." },
  { botao: "l2", texto: "Qual é o gatilho esquerdo (LT ou L2)? Pressione agora." },
  { botao: "r2", texto: "Qual é o gatilho direito (RT ou R2)? Pressione agora." },
  { botao: "start", texto: "Qual é o botão Start? Pressione agora." },
  { botao: "select", texto: "Qual é o botão Select? Pressione agora." },
  { botao: "l3", texto: "Pressione o analógico esquerdo (o stick esquerdo). Pressione agora." },
  { botao: "r3", texto: "Pressione o analógico direito (o stick direito). Pressione agora." },
];

let wizardEstado = null;
let wizardCancela = null;

function iniciarWizard() {
  if (wizardEstado) return;
  const tipoSelecionado = $("#mapaTipo").value;
  if (!tipoSelecionado) return;

  wizardEstado = {
    passo: 0,
    jogador: $("#mapaJogador").value,
    tipo: tipoSelecionado,
  };

  $("#wizardGenerico").hidden = false;
  $("#btnMapaWizard").hidden = true;
  $("#btnMapaAuto").hidden = true;
  $("#listaMapa").hidden = true;
  $("#mapaResumo").hidden = true;
  $("#mapaWatacao").hidden = true;

  $("#wizardTitulo").textContent =
    "Configurando " + $("#mapaTipo").selectedOptions[0].textContent;
  wizardPasso(0);
}

function wizardPasso(indice) {
  if (!wizardEstado) return;
  const passo = PASSOS_WIZARD[indice];
  if (!passo) {
    wizardFinalizar();
    return;
  }

  $("#wizardDescricao").textContent = passo.texto;
  $("#wizardAndamento").textContent =
    `Passo ${indice + 1} de ${PASSOS_WIZARD.length}`;
  $("#wizardAguardar").textContent = "Pressione o botão agora";
  $("#wizardAguardar").disabled = false;
  $("#wizardAguardar").onclick = wizardAguardar;
  $("#wizardPular").onclick = wizardPular;
  $("#wizardObservacao").hidden = true;
  $("#wizardAguardar").onmouseover = null;
  $("#wizardAguardar").onmouseout = null;
}

function wizardAguardar() {
  if (!wizardEstado) return;
  $("#wizardAguardar").disabled = true;
  $("#wizardAguardar").textContent = "Aguardando…";
  $("#wizardDescricao").textContent =
    "Pressione o botão do controle agora. Clique em Cancelar para voltar.";

  if (wizardCancela) wizardCancela();
  wizardCancela = null;

  let vivo = true;
  let quadro = null;

  const encerrar = () => {
    if (!vivo) return;
    vivo = false;
    if (quadro) cancelAnimationFrame(quadro);
    document.removeEventListener("keydown", noTecladoWizard, true);
  };

  const DIRECIONAL_DO_NAVEGADOR = { 12: "up", 13: "down", 14: "left", 15: "right" };

  function noTecladoWizard(evento) {
    if (evento.key === "Escape") {
      encerrar();
      wizardCancelar();
      return;
    }
    const tecla = traduzirTecla(evento);
    if (tecla) {
      encerrar();
      gravaWizard("teclado", tecla);
    } else {
      recado("Essa tecla o RetroArch não reconhece.", true);
    }
  }

  function olharControleWizard() {
    if (!vivo) return;
    const conectados = navigator.getGamepads ? navigator.getGamepads() : [];
    for (const pad of conectados) {
      if (!pad) continue;
      for (let i = 0; i < pad.buttons.length; i++) {
        if (!pad.buttons[i].pressed) continue;
        if (DIRECIONAL_DO_NAVEGADOR[i]) {
          encerrar();
          gravaWizard("hat", DIRECIONAL_DO_NAVEGADOR[i]);
        } else {
          encerrar();
          gravaWizard("botao", String(i));
        }
        return;
      }
    }
    quadro = requestAnimationFrame(olharControleWizard);
  }

  document.addEventListener("keydown", noTecladoWizard, true);
  quadro = requestAnimationFrame(olharControleWizard);
  wizardCancela = encerrar;
  estado.ouvindo = encerrar;
}

function gravaWizard(tipo, valor) {
  const passo = PASSOS_WIZARD[wizardEstado.passo];
  if (!passo) return;

  wizardCancela = null;
  estado.ouvindo = null;

  $.post("/api/mapeamento/definir", {
    jogador: wizardEstado.jogador,
    botao: passo.botao,
    tipo: tipo,
    valor: valor,
  }).then(() => {
    wizardEstado.passo++;
    wizardPasso(wizardEstado.passo);
    recado("Registrado! Próximo passo.");
  }).catch((falha) => {
    recado(falha.message || "Erro ao gravar.", true);
    wizardCancelar();
  });
}

function wizardPular() {
  if (!wizardEstado) return;
  wizardEstado.passo++;
  wizardPasso(wizardEstado.passo);
  recado("Pulado. Você pode mapear depois manualmente.");
}

function wizardCancelar() {
  if (wizardCancela) wizardCancela();
  wizardCancela = null;
  estado.ouvindo = null;
  wizardEstado = null;
  $("#wizardGenerico").hidden = true;
  $("#btnMapaWizard").hidden = false;
  $("#btnMapaAuto").hidden = false;
  $("#listaMapa").hidden = false;
  $("#mapaResumo").hidden = false;
  $("#mapaWatacao").hidden = false;
  desenharMapa();
  recado("Configuração cancelada. Os botões já mapeados foram gravados.");
}

function wizardFinalizar() {
  wizardCancela = null;
  estado.ouvindo = null;
  wizardEstado = null;
  $("#wizardGenerico").hidden = true;
  $("#btnMapaWizard").hidden = false;
  $("#btnMapaAuto").hidden = false;
  $("#listaMapa").hidden = false;
  $("#mapaResumo").hidden = false;
  $("#mapaWatacao").hidden = false;
  desenharMapa();
  recado("Controle genérico configurado! Teste no jogo e ajuste só o que sair trocado.");
}

// Fica ouvindo teclado e controle ao mesmo tempo, até vir alguma coisa.
