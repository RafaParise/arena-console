"use strict";
// --------------------------------------------------------------------------
// ARENA no navegador: a parte da tela que so existe no Chromebook (item 12).
//
// O resto da tela e' o mesmo app.js do Windows. Aqui ficam tres coisas:
//   1. o aviso no alto da lista, ate a pasta do ARENA no pen drive estar
//      liberada (escolher a pasta uma vez; nos outros dias, "Permitir");
//   2. Ajustes -> Máquina -> Este Chromebook: o "Testar este Chromebook"
//      (abre os jogos livres, mede quadros por segundo e guarda o relatorio
//      para o professor) e o "Guardar um jogo neste navegador";
//   3. os textos que no Windows falam de pasta e de .bat.
// --------------------------------------------------------------------------
(function () {
  if (!window.ARENA_NO_NAVEGADOR) return;
  const $id = function (id) { return document.getElementById(id); };
  const SEGUNDOS_POR_JOGO = 8;
  let ultimoRelatorio = null;
  // Celular e tablet (a versao da internet, auditoria 4): o caminho mais
  // simples e' "Guardar um jogo": o arquivo (da pasta Download, por exemplo)
  // fica guardado no aparelho. Escolher a pasta do ARENA so aparece onde o
  // navegador sabe escolher pasta.
  const NO_CELULAR = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent) ||
    !!(navigator.userAgentData && navigator.userAgentData.mobile);
  const ESCOLHE_PASTA = typeof window.showDirectoryPicker === "function";

  function quandoPronto(fazer) {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", fazer, { once: true });
    else fazer();
  }

  async function situacao() {
    const resposta = await fetch("/api/estado");
    return (await resposta.json()).navegador || {};
  }

  async function atualizarAviso() {
    const caixa = $id("avisoPasta");
    if (!caixa) return;
    const s = await situacao();
    const pasta = s.pasta || {};
    const texto = $id("avisoPastaTexto");
    const botao = $id("btnPastaArena");
    if (pasta.tem && !pasta.precisa_permissao) {
      caixa.hidden = true;
    } else if (pasta.tem) {
      texto.textContent = "O Chrome pede para confirmar o acesso à pasta do ARENA (" + pasta.nome + "), " +
        "para abrir os jogos e guardar os saves no pen drive.";
      botao.textContent = "Permitir";
      botao.dataset.acao = "liberar";
      caixa.hidden = false;
    } else if (NO_CELULAR) {
      texto.textContent = "Os jogos livres que vêm com o ARENA já estão aqui. Para jogar um jogo seu, toque em " +
        "Guardar um jogo e escolha o arquivo (o que você baixou fica na pasta Download). Ele fica guardado neste aparelho.";
      botao.textContent = "Guardar um jogo";
      botao.dataset.acao = "guardar";
      caixa.hidden = !!(await temJogoGuardado());
    } else {
      texto.textContent = s.manifesto === "do_windows"
        ? "A lista veio do pen drive. Para abrir esses jogos, escolha a pasta do ARENA (a que tem o " +
          "ARENA-CHROMEBOOK.html). É uma vez só: o ARENA lembra."
        : "Os jogos livres que vêm com o ARENA já estão aqui. Para os seus jogos, escolha a pasta do ARENA " +
          "no pen drive (a que tem o ARENA-CHROMEBOOK.html). É uma vez só: o ARENA lembra.";
      botao.textContent = "Escolher a pasta do ARENA";
      botao.dataset.acao = "escolher";
      caixa.hidden = false;
    }
    const nomePasta = $id("chromebookPasta");
    if (nomePasta) {
      nomePasta.textContent = !pasta.tem ? "nenhuma ainda"
        : pasta.nome + (pasta.precisa_permissao ? " (falta permitir)" : pasta.pode_gravar ? " (lê e grava: os saves vão para o pen drive)"
          : " (só lê: os saves ficam neste navegador)");
    }
  }

  async function temJogoGuardado() {
    try { return (await ArenaBanco.contar("jogos", "meus/")) > 0; } catch (falha) { return false; }
  }

  async function usarPasta(acao) {
    if (acao === "guardar") { $id("campoGuardarJogo").click(); return; }
    try {
      const resposta = await fetch("/api/navegador/pasta", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ acao: acao }),
      });
      const dados = await resposta.json();
      if (!resposta.ok || dados.ok === false) throw new Error(dados.erro || "Não deu para usar a pasta.");
      if (typeof carregarCatalogo === "function") await carregarCatalogo();
      recadoSeguro(dados.total + " jogos na lista.");
    } catch (falha) {
      // Cancelar a escolha nao e' erro: so nao muda nada.
      if (!/abort|cancel|nenhuma pasta/i.test(String(falha && (falha.name + " " + falha.message)))) {
        recadoSeguro(String(falha && falha.message || falha), true);
      }
    }
    await atualizarAviso();
  }

  function recadoSeguro(texto, erro) {
    if (typeof recado === "function") recado(texto, !!erro);
  }

  // ------------------------------------------------------------------------
  // Testar este Chromebook: os jogos livres, um por um, com a medida de
  // quadros por segundo do proprio quadro do jogo.
  // ------------------------------------------------------------------------
  function esperar(ms) { return new Promise(function (pronto) { setTimeout(pronto, ms); }); }

  async function esperarAte(condicao, segundos) {
    const fim = Date.now() + segundos * 1000;
    while (Date.now() < fim) {
      if (condicao()) return true;
      await esperar(200);
    }
    return false;
  }

  async function capacidades() {
    const c = {
      seletor_de_pasta: typeof window.showDirectoryPicker === "function",
      controle: typeof navigator.getGamepads === "function",
      tela_cheia: !!document.documentElement.requestFullscreen,
      webassembly: typeof WebAssembly === "object",
      descompactar: typeof DecompressionStream === "function",
      banco: !!window.indexedDB,
      seguro: window.isSecureContext,
    };
    try { c.controles_ligados = Array.from(navigator.getGamepads() || []).filter(Boolean).map(function (g) { return g.id; }); }
    catch (falha) { c.controles_ligados = "bloqueado: " + falha.message; }
    try { const e = await navigator.storage.estimate(); c.espaco_mb = Math.round(e.quota / 1048576); } catch (falha) { c.espaco_mb = null; }
    return c;
  }

  async function testarUmJogo(jogo) {
    const resultado = { jogo: jogo.titulo, console: jogo.plataforma_nome };
    const inicio = performance.now();
    try {
      await ArenaRotas.responder("/api/jogar", "POST", { jogo_id: jogo.id, apelido: "teste" }, new URLSearchParams());
    } catch (falha) {
      resultado.erro = falha.message;
      return resultado;
    }
    if (!(await esperarAte(function () { return ArenaPartida.rodando() || !ArenaPartida.aberto(); }, 40))) {
      resultado.erro = "o jogo não começou em 40 s";
      ArenaPartida.fechar("teste");
      return resultado;
    }
    if (!ArenaPartida.aberto()) {
      resultado.erro = (ArenaRotas.estado.problema || {}).texto || "o jogo fechou sozinho";
      return resultado;
    }
    resultado.abrir_s = Math.round((performance.now() - inicio) / 100) / 10;
    await esperar(3000);                          // passa a abertura do jogo
    const antes = await ArenaPartida.medir();
    await esperar(SEGUNDOS_POR_JOGO * 1000);
    const depois = await ArenaPartida.medir(true);
    if (antes && depois) {
      const segundos = (depois.agora - antes.agora) / 1000;
      resultado.quadros_s = Math.round((depois.voltas - antes.voltas) / segundos * 10) / 10;
      resultado.imagens_s = Math.round((depois.imagens - antes.imagens) / segundos * 10) / 10;
      // Sem os avisos de sempre do RetroArch no navegador, que nao mudam nada
      // (a placa sem BGRA8888, os filtros padrao, o tamanho da tela inteira).
      const linhas = (depois.registro || []).filter(function (l) {
        return /\[(ERROR|WARN)\]/.test(l) && !/BGRA8888|Stock GLSL|screen dimensions/.test(l);
      });
      if (linhas.length) resultado.avisos = linhas.slice(-5);
    }
    ArenaPartida.sair();
    await esperarAte(function () { return !ArenaPartida.aberto(); }, 12);
    return resultado;
  }

  async function testarChromebook() {
    const botao = $id("btnTestarChromebook");
    const lista = $id("listaTesteChromebook");
    botao.disabled = true;
    lista.replaceChildren();
    const linha = function (texto) {
      const item = document.createElement("li");
      item.className = "controle";
      item.textContent = texto;
      lista.append(item);
      return item;
    };
    const andamento = linha("Medindo o processador...");
    try {
      const medida = await ArenaRotas.responder("/api/navegador/maquina", "POST", {}, new URLSearchParams());
      const m = medida.maquina;
      andamento.textContent = "Processador: " + m.velocidade.relativa_ao_alvo.toLocaleString("pt-BR") +
        "× o notebook mais fraco da escola, por núcleo (" + m.nucleos + " núcleos). Sistema: " + m.sistema +
        ". Placa: " + m.gpu.nome + ".";
      const relatorio = {
        quando: new Date().toISOString(),
        versao_arena: ARENA_DADOS.versao,
        retroarch: ARENA_DADOS.retroarch,
        maquina: m,
        navegador: navigator.userAgent,
        capacidades: await capacidades(),
        pasta: ArenaPasta.situacao(),
        pagina: location.protocol === "file:" ? "aberta do pen drive (file://)" : "aberta por endereço",
        jogos: [],
      };
      // Um jogo de cada console, dos que abrem no navegador: primeiro os que
      // vem com o ARENA, depois os do pen drive.
      const vistos = new Set();
      const escolhidos = [];
      for (const jogo of ArenaRotas.estado.jogos) {
        const p = ARENA_DADOS.consoles.find(function (c) { return c.id === jogo.plataforma; });
        if (!p || !p.core_navegador || vistos.has(p.id)) continue;
        vistos.add(p.id);
        escolhidos.push(jogo);
      }
      escolhidos.sort(function (a, b) { return (a.origem === "vem_com" ? 0 : 1) - (b.origem === "vem_com" ? 0 : 1); });
      for (const jogo of escolhidos.slice(0, 12)) {
        const item = linha("Testando " + jogo.titulo + " (" + jogo.plataforma_nome + ")...");
        const r = await testarUmJogo(jogo);
        relatorio.jogos.push(r);
        item.textContent = r.erro
          ? jogo.plataforma_nome + ": " + jogo.titulo + " — não abriu: " + r.erro
          : jogo.plataforma_nome + ": " + jogo.titulo + " — " + r.quadros_s + " quadros por segundo" +
            (r.quadros_s >= 57 ? " (roda bem)" : r.quadros_s >= 45 ? " (roda, com engasgos)" : " (lento demais)") +
            "; abriu em " + r.abrir_s + " s";
      }
      ultimoRelatorio = relatorio;
      try { await ArenaBanco.gravar("coisas", "teste_do_chromebook", relatorio); } catch (falha) { /* segue */ }
      linha("Pronto. Clique em Baixar o relatório e leve o arquivo para o professor (ele vai na pasta Downloads).");
      $id("btnBaixarRelatorio").disabled = false;
    } catch (falha) {
      linha("O teste parou: " + (falha && falha.message || falha));
    } finally {
      botao.disabled = false;
    }
  }

  function baixarRelatorio() {
    if (!ultimoRelatorio) return;
    const texto = JSON.stringify(ultimoRelatorio, null, 1);
    const link = document.createElement("a");
    link.href = URL.createObjectURL(new Blob([texto], { type: "application/json" }));
    link.download = "teste-do-chromebook-" + new Date().toISOString().slice(0, 10) + ".json";
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(function () { URL.revokeObjectURL(link.href); }, 5000);
  }

  // ------------------------------------------------------------------------
  // Guardar um jogo neste navegador (para o Chromebook sem pen drive)
  // ------------------------------------------------------------------------
  function consolesDaExtensao(nome) {
    const ext = (String(nome).match(/\.[^.]+$/) || [""])[0].toLowerCase();
    return ARENA_DADOS.consoles.filter(function (p) {
      return p.core_navegador && (p.extensoes || []).includes(ext);
    });
  }

  async function guardarJogos(arquivos) {
    let guardados = 0;
    for (const arquivo of arquivos) {
      const candidatos = consolesDaExtensao(arquivo.name);
      const escolhido = $id("listaConsoleGuardar").value;
      const p = candidatos.find(function (c) { return c.id === escolhido; }) || (candidatos.length === 1 ? candidatos[0] : null);
      if (!p) {
        recadoSeguro(candidatos.length ? arquivo.name + " serve a mais de um console: em Ajustes → Máquina, escolha o " +
          "console na lista de Guardar um jogo e mande de novo."
          : arquivo.name + ": nenhum console do navegador abre este tipo de arquivo.", true);
        continue;
      }
      const dados = await arquivo.arrayBuffer();
      await ArenaBanco.gravar("jogos", "meus/" + p.id + "/" + arquivo.name,
                              { nome: arquivo.name, plataforma: p.id, dados: dados, bytes: dados.byteLength, quando: Date.now() });
      guardados++;
    }
    if (guardados) {
      await ArenaRotas.montarLista();
      if (typeof carregarCatalogo === "function") await carregarCatalogo();
      const onde = NO_CELULAR ? "neste aparelho" : "neste navegador";
      recadoSeguro(guardados === 1 ? "Jogo guardado " + onde + "." : guardados + " jogos guardados " + onde + ".");
      await atualizarAviso();
    }
  }

  function preencherConsoles() {
    const lista = $id("listaConsoleGuardar");
    if (!lista) return;
    const automatico = document.createElement("option");
    automatico.value = "";
    automatico.textContent = "Descobrir pelo arquivo";
    lista.append(automatico);
    for (const p of ARENA_DADOS.consoles.filter(function (c) { return c.core_navegador; })
      .sort(function (a, b) { return a.nome.localeCompare(b.nome, "pt-BR"); })) {
      const opcao = document.createElement("option");
      opcao.value = p.id;
      opcao.textContent = p.nome;
      lista.append(opcao);
    }
  }

  quandoPronto(function () {
    for (const elemento of document.querySelectorAll("[data-so-navegador]")) {
      if (elemento.id !== "avisoPasta") elemento.hidden = false;
    }
    const vazio = $id("vazioTexto");
    if (vazio) {
      vazio.textContent = NO_CELULAR
        ? "Toque em Guardar um jogo (na faixa dos consoles, no alto) e escolha o arquivo do jogo."
        : "Escolha a pasta do ARENA no pen drive (botão no alto) para ver os seus jogos, ou guarde " +
          "um jogo neste navegador em Ajustes → Máquina.";
    }
    if (NO_CELULAR) textosDoCelular();
    const botaoPasta = $id("btnPastaArena");
    if (botaoPasta) botaoPasta.addEventListener("click", function () { usarPasta(botaoPasta.dataset.acao || "escolher"); });
    const outraPasta = $id("btnOutraPasta");
    if (outraPasta) outraPasta.addEventListener("click", function () { usarPasta("escolher"); });
    const testar = $id("btnTestarChromebook");
    if (testar) testar.addEventListener("click", testarChromebook);
    const baixar = $id("btnBaixarRelatorio");
    if (baixar) baixar.addEventListener("click", baixarRelatorio);
    const campo = $id("campoGuardarJogo");
    if (campo) {
      campo.addEventListener("change", function () {
        guardarJogos(Array.from(campo.files || [])).catch(function (falha) { recadoSeguro(falha.message, true); })
          .finally(function () { campo.value = ""; });
      });
    }
    preencherConsoles();
    atualizarAviso();
    ArenaBanco.ler("coisas", "teste_do_chromebook").then(function (antigo) {
      if (antigo) { ultimoRelatorio = antigo; if (baixar) baixar.disabled = false; }
    }).catch(function () {});
  });

  // No celular, o bloco "Este Chromebook" de Ajustes -> Maquina fala do
  // aparelho; e a pasta do pen drive sai (o Chrome do Android nao escolhe
  // pasta).
  function textosDoCelular() {
    const bloco = $id("blocoChromebook");
    if (!bloco) return;
    const titulos = bloco.querySelectorAll(".grupo-titulo");
    if (titulos[0]) titulos[0].textContent = "Este aparelho";
    if (titulos[1]) titulos[1].textContent = "Guardar um jogo neste aparelho";
    const explicacoes = bloco.querySelectorAll(":scope > .explica");
    if (explicacoes[0]) {
      explicacoes[0].textContent = "No celular, o ARENA roda dentro do navegador, com o mesmo RetroArch do Windows. " +
        "O teste abre um jogo de cada console, um por vez, e mede quantos quadros por segundo ele consegue: 60 é o " +
        "certo. Leva uns dois minutos; não mexa enquanto isso.";
    }
    if (explicacoes[1]) {
      explicacoes[1].textContent = "O jogo fica guardado dentro do navegador, neste aparelho. Serve para jogo " +
        "pequeno, de cartucho. Se o nome do arquivo servir a mais de um console, escolha o console aqui antes.";
    }
    const testar = $id("btnTestarChromebook");
    if (testar) testar.textContent = "Testar este aparelho";
    if (!ESCOLHE_PASTA) {
      const outra = $id("btnOutraPasta");
      if (outra) outra.hidden = true;
      const pasta = $id("chromebookPasta");
      if (pasta && pasta.closest("ul")) pasta.closest("ul").hidden = true;
    }
  }

  window.ArenaTela = { atualizarAviso: atualizarAviso, testarChromebook: testarChromebook };
})();
