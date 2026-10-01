/* ==========================================================================
   ARENA - logica da interface
   JavaScript puro. Sem framework, sem build, sem internet.
   ========================================================================== */

"use strict";

// Uma fonte de verdade so. A tela inteira le daqui.
const estado = {
  jogos: [],
  plataformas: [],
  filtroPlataforma: "",
  busca: "",
  limite: 200,          // quantas linhas desenhar de uma vez
  config: null,
  efetivas: {},         // valores que realmente vao valer (perfil + avancado)
  perfis: {},
  recursos: [],
  gruposRecursos: [],
  jogoDoPlacar: null,
  jogoAberto: null,
  maquina: null,
  mapa: null,
  ouvindo: null,
  porPlataforma: {},
  jogoDaPartida: null,
  papelDaPartida: "hospedar",
  amigos: [],
  colegasOnline: [],
  filtroRapido: "todos",
  jogoSelecionado: null,
};

let jogoConsoleEditando = null;


const PASSO_LIMITE = 200;

const $ = (seletor) => document.querySelector(seletor);
const apelidoAtual = () => (estado.config?.apelido || "").trim();

function formatarBytes(valor) {
  let tamanho = Number(valor) || 0;
  const unidades = ["B", "KB", "MB", "GB"];
  let indice = 0;
  while (tamanho >= 1024 && indice < unidades.length - 1) {
    tamanho /= 1024;
    indice += 1;
  }
  return `${tamanho.toFixed(indice ? 1 : 0)} ${unidades[indice]}`;
}

function atualizarBotaoTema() {
  const botao = $("#btnTema");
  if (!botao || !estado.config) return;
  const escuro = estado.config.tema === "escuro";
  document.body.dataset.tema = escuro ? "escuro" : "claro";
  // Os fundos animados (galaxy-background.js, field-background.js) leem
  // isto para se desligar sozinhos no modo modesto -- computador fraco
  // nao precisa gastar quadro nenhum com decoracao.
  document.body.dataset.modoModesto = estado.config.modo_modesto ? "true" : "false";
  botao.textContent = escuro ? "☀ Claro" : "☾ Escuro";
  botao.setAttribute("aria-label", escuro ? "Usar modo claro" : "Usar modo escuro");
}

// --------------------------------------------------------------------------
// Comunicacao com o servidor
// --------------------------------------------------------------------------

async function pedir(rota, metodo = "GET", corpo = null) {
  const opcoes = { method: metodo, headers: { "Content-Type": "application/json" } };
  if (corpo) opcoes.body = JSON.stringify(corpo);

  let resposta;
  try {
    resposta = await fetch(rota, opcoes);
  } catch (falha) {
    const erro = new Error(
      "O servidor do Arena não está acessível. Abra o ARENA pela janela preta e tente novamente."
    );
    erro.causa = falha;
    throw erro;
  }
  const dados = await resposta.json().catch(() => ({}));

  if (!resposta.ok || dados.ok === false) {
    throw new Error(dados.erro || "O servidor não respondeu como esperado.");
  }
  return dados;
}

// --------------------------------------------------------------------------
// Mensagens na tela
// --------------------------------------------------------------------------

let temporizadorRecado = null;

function recado(texto, erro = false, duracaoMs = 4500) {
  const caixa = $("#recado");
  caixa.textContent = texto;
  caixa.classList.toggle("recado--erro", erro);
  caixa.hidden = false;
  clearTimeout(temporizadorRecado);
  temporizadorRecado = setTimeout(() => { caixa.hidden = true; }, duracaoMs);
}

function aviso(texto) {
  const caixa = $("#aviso");
  if (!texto) { caixa.hidden = true; return; }
  $("#avisoTexto").textContent = texto;
  caixa.hidden = false;
}

// --------------------------------------------------------------------------
// Carregamento
// --------------------------------------------------------------------------

async function carregarEstado() {
  const dados = await pedir("/api/estado");

  estado.config = dados.config;
  atualizarBotaoTema();

  $("#versao").textContent = dados.versao ? "v" + dados.versao : "";

  // A chave que libera a rede. Sem ela nenhum colega alcanca ninguem.
  $("#chaveRede").setAttribute("aria-pressed",
    dados.config.permitir_rede ? "true" : "false");
  $("#ajudaRede").textContent = dados.config.permitir_rede
    ? "Ligado. Os colegas já podem te achar."
    : "Desligado, só este computador acessa.";

  $("#chaveModesto").setAttribute("aria-pressed",
    dados.config.modo_modesto ? "true" : "false");

  $("#chaveRpcn").setAttribute("aria-pressed",
    dados.config.rpcn_ativo ? "true" : "false");

  $("#listaPresetGrafico").value = dados.config.preset_grafico_externo || "automatico";
  atualizarExplicaPreset();
  $("#listaMotorPs2").value = dados.config.motor_ps2 || "automatico";
  desenharRedePs2(dados.rede_ps2 || {});

  desenharEnderecos(dados.enderecos || []);
  estado.efetivas = dados.efetivas;
  estado.perfis = dados.perfis;
  estado.recursos = dados.recursos || [];
  estado.gruposRecursos = dados.grupos || [];

  const m = dados.maquina;
  estado.maquina = m;

  // Barra do topo: o essencial. O detalhe fica na aba Máquina.
  $("#lidoCpu").textContent = m.cpu;
  $("#lidoRam").textContent = `${m.ram_total_gb} GB`;
  $("#lidoDriver").textContent = estado.efetivas.video_driver || m.driver_video;
  if (!estado.config.apelido) {
    $("#modalApelido").hidden = false;
    $("#campoApelidoInicial").focus();
  }

  // Aba Máquina
  $("#hwCpu").textContent = m.cpu;
  $("#hwNucleos").textContent = `${m.nucleos} núcleos lógicos`;
  $("#hwRam").textContent = `${m.ram_total_gb} GB (${m.ram_livre_gb} GB livres)`;
  $("#hwDisco").textContent = `${m.disco.descricao} · unidade ${m.disco.unidade}`;

  $("#hwEspaco").textContent = m.disco.livre_gb
    ? `${m.disco.livre_gb} GB livres de ${m.disco.total_gb} GB` +
      (m.disco.cabem_states ? ` · cabem uns ${m.disco.cabem_states} save states` : "")
    : "não consegui medir";

  $("#hwVelocidade").textContent = m.disco.escrita_mbs
    ? `${m.disco.escrita_mbs} MB por segundo`
    : "não consegui medir";

  $("#hwInternet").textContent = dados.internet
    ? "conectado — a cópia de segurança acontece sozinha"
    : "sem internet — tudo continua funcionando e sobe depois";
  $("#hwSistema").textContent = m.sistema;
  $("#hwMotor").textContent = estado.efetivas.video_driver || m.driver_video;
  // O que o perfil muda de verdade: o modo econômico (rede e cópias de
  // segurança mais espaçadas). Nenhum console some da lista -- a frase
  // antiga ("consoles pesados ficam ocultos") não valia mais desde que o
  // selo "Pode travar" passou a avisar em vez de esconder.
  $("#hwPerfil").textContent = dados.economico
    ? "Econômico — rede e cópias de segurança mais espaçadas, para poupar a máquina"
    : "Normal — todos os consoles na lista, com o selo de cada um";
  $("#hwRuntime").textContent = m.runtime_ok
    ? "Visual C++ presente"
    : "Visual C++ AUSENTE — os jogos não vão abrir";
  $("#blocoRuntime").hidden = m.runtime_ok;

  // Capacidade MEDIDA: velocidade de um núcleo em "vezes o notebook mais
  // fraco da escola" e as instruções que decidem se um emulador abre. A nota
  // antiga contava núcleos e dava o mesmo 4 ao Celeron e ao Ryzen.
  const vel = (m.velocidade || {}).relativa_ao_alvo;
  const instr = m.instrucoes || {};
  if (typeof vel === "number") {
    const avx = instr.avx2 ? "AVX2" : instr.avx ? "AVX (sem AVX2)"
      : instr.avx === false ? "sem AVX (Xbox 360 não abre)" : "AVX não conferido";
    $("#hwCapacidade").textContent =
      `${vel.toLocaleString("pt-BR")}× o notebook mais fraco da escola, por núcleo · ${avx}`;
  } else {
    const nota = dados.capacidade.nota;
    $("#hwCapacidade").textContent =
      `${nota} de 5 — ${["", "muito modesta", "modesta", "boa", "forte", "muito forte"][nota]}`;
  }

  desenharControles(dados.controles || []);
  prepararBotoes(dados.consoles_botoes || []);
  prepararMapa(dados.consoles_botoes || []);
  desenharExternos(dados.externos || []);
  desenharBios(dados.bios_consoles || [], dados.bios_disponiveis || []);
  desenharCartoes(dados.memory_cards || []);
  prepararAbrirBios(dados.bios_consoles || []);
  $("#relogioPc").textContent = new Date().toLocaleString("pt-BR");
  $("#pastaBios").textContent = dados.pastas.sistema;
  $("#listaDriverControleTopo").value =
    estado.efetivas.input_joypad_driver || "xinput";

  estado.amigos = estado.config.servidores || [];
  const codigo = $("#meuCodigoAmigo");
  if (codigo) codigo.textContent = dados.codigo_amigo || "—";
  estado.servidoresOnline = dados.servidores_online || [];
  desenharAmigos([]);
  preencherAmigosPartida();

  atualizarFotoPerfil(dados.tem_foto_perfil);

  $("#camSaves").textContent = dados.pastas.saves;
  $("#camCapturas").textContent = dados.pastas.capturas;
  $("#camJogos").textContent = dados.pastas.jogos;
  $("#camSistema").textContent = dados.pastas.sistema;

  // A descoberta local é automática; não expomos IP nem pedimos configuração.
  carregarColegas();
  // Confere os amigos salvos direto (TCP), sem esperar o vigia do servidor.
  procurarPartidas();

  $("#chaveDesempenho").setAttribute("aria-pressed",
    dados.config.modo_desempenho ? "true" : "false");
  $("#chaveUltra").setAttribute("aria-pressed",
    dados.config.ultra_desempenho ? "true" : "false");
  $("#chaveTravar").setAttribute("aria-pressed",
    dados.config.travar_teclas ? "true" : "false");
  desenharFechamentos(dados.fechamentos || []);

  $("#perfilApelido").textContent = dados.config.apelido || "(sem apelido)";
  $("#perfilCodigo").textContent = dados.config.dispositivo_id || "—";
  $("#perfilRecordes").textContent = `${dados.pendentes} aguardando envio`;
  desenharPacotes(dados.pacotes || []);
  mostrarPendentes(dados.pendentes);
  $("#malaCaminho").textContent = dados.mala.caminho;
  $("#malaSituacao").textContent = dados.mala.existe
    ? "mala presente" : "nenhuma mala aqui ainda";

  if (!dados.runtime_ok) {
    aviso("Faltam as bibliotecas gráficas do Windows neste computador, então os " +
          "jogos não vão abrir. Vá em Ajustes → Máquina e clique no botão " +
          "para copiar. Não precisa de senha de administrador.");
  } else if (!dados.retroarch_presente) {
    aviso("Faltou o RetroArch. Coloque a pasta dele dentro da pasta do ARENA, " +
          "com o nome retroarch, e abra o ARENA de novo.");
  } else {
    aviso("");
  }

  desenharPerfis();
  desenharAvancado();
}

async function carregarCatalogo() {
  const dados = await pedir("/api/catalogo");
  estado.plataformas = dados.plataformas;

  // O servidor manda a lista de plataformas e a lista de jogos separadas.
  // Aqui a gente cruza as duas uma unica vez, em vez de o servidor repetir
  // o estado da plataforma dentro de cada um dos jogos.
  estado.porPlataforma = {};
  for (const p of dados.plataformas) estado.porPlataforma[p.id] = p;
  estado.jogos = dados.jogos;
  if (!estado.jogoSelecionado || !estado.jogos.some((jogo) => jogo.id === estado.jogoSelecionado.id))
    estado.jogoSelecionado = estado.jogos[0] || null;
  estado.limite = PASSO_LIMITE;

  $("#lidoJogos").textContent = dados.total;
  $("#contaTodos").textContent = dados.total;

  desenharPlataformas();
  desenharJogos();
  desenharDetalhes();
}

// --------------------------------------------------------------------------
// Trilho de plataformas
// --------------------------------------------------------------------------

function desenharPlataformas() {
  const contagem = {};
  for (const jogo of estado.jogos) {
    contagem[jogo.plataforma] = (contagem[jogo.plataforma] || 0) + 1;
  }

  // Plataformas com jogos primeiro; depois as vazias, para consulta.
  const ordenadas = [...estado.plataformas].sort((a, b) => {
    const diferenca = (contagem[b.id] || 0) - (contagem[a.id] || 0);
    return diferenca !== 0 ? diferenca : a.nome.localeCompare(b.nome, "pt-BR");
  });

  // Monta fora da tela e insere de uma vez: um unico redesenho.
  const lote = document.createDocumentFragment();

  for (const plataforma of ordenadas) {
    const item = document.createElement("li");
    const botao = document.createElement("button");
    botao.type = "button";
    botao.className = "trilho-item";
    botao.dataset.plataforma = plataforma.id;
    botao.title = plataforma.motivo || plataforma.descricao;

    const sinal = document.createElement("span");
    sinal.className = `sinal sinal--${plataforma.estado}`;

    const nome = document.createElement("span");
    nome.className = "trilho-nome";
    nome.textContent = plataforma.nome;

    const conta = document.createElement("span");
    conta.className = "trilho-conta";
    conta.textContent = contagem[plataforma.id] || 0;

    // O console vira alvo para receber jogo arrastado.
    if (plataforma.id !== "indefinido") {
      botao.addEventListener("dragover", (evento) => {
        evento.preventDefault();
        evento.dataTransfer.dropEffect = "move";
        botao.classList.add("trilho-item--alvo");
      });
      botao.addEventListener("dragleave", () =>
        botao.classList.remove("trilho-item--alvo"));
      botao.addEventListener("drop", async (evento) => {
        evento.preventDefault();
        botao.classList.remove("trilho-item--alvo");
        await moverJogo(evento.dataTransfer.getData("text/plain"), plataforma.id);
      });
    }

    botao.append(sinal, nome, conta);
    item.append(botao);
    lote.append(item);
  }

  $("#listaPlataformas").replaceChildren(lote);
}

// --------------------------------------------------------------------------
// Lista de jogos
// --------------------------------------------------------------------------

// Tira acento e caixa alta para a busca achar "Pokemon" digitando "pokémon".
function normalizar(texto) {
  return texto.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
}

function jogosVisiveis() {
  const busca = normalizar(estado.busca.trim());
  const plataforma = estado.filtroPlataforma;

  if (!busca && !plataforma && estado.filtroRapido === "todos") return estado.jogos;

  return estado.jogos.filter((jogo) => {
    if (estado.filtroRapido === "favoritos" &&
        !(estado.config.favoritos || []).includes(jogo.id)) return false;
    if (estado.filtroRapido === "recentes" &&
        !(estado.config.recentes || []).includes(jogo.id)) return false;
    if (plataforma && jogo.plataforma !== plataforma) return false;
    // 'ordenacao' ja vem do servidor sem acento e em minusculas: comparar
    // com ela evita normalizar 3000 titulos a cada tecla digitada.
    if (busca && !jogo.ordenacao.includes(busca)) return false;
    return true;
  });
}

// Capa tipográfica local: funciona offline e dá identidade visual mesmo
// quando o aluno ainda não colocou artes na pasta do jogo.
function iniciaisDaCapa(titulo) {
  const palavras = String(titulo || "ARENA").trim().split(/\s+/).filter(Boolean);
  return (palavras.length === 1
    ? palavras[0].slice(0, 2)
    : palavras.slice(0, 2).map((palavra) => palavra[0]).join(""))
    .toUpperCase();
}

// Tipo de midia fisica por console, pra desenhar um molde parecido com o
// objeto de verdade (cartucho, jewel case de CD, caixa de DVD...) em vez
// de so um retangulo generico. Agrupado por TIPO, nao por console - um
// molde fiel por console seria trabalho de design grande demais; um por
// categoria da o suficiente pro aluno reconhecer o formato.
const MIDIA_POR_PLATAFORMA = {
  cartucho_h: [
    "nes", "snes", "megadrive", "sega32x", "n64", "sg1000", "atari2600",
    "atari5200", "atari7800", "jaguar", "intellivision", "colecovision",
    "odyssey2", "arcade", "c64", "msx", "vectrex", "neogeo", "amstrad",
  ],
  cartucho_v: [
    "gameboy", "gba", "virtualboy", "pokemini", "gamewatch", "ngp",
    "wonderswan", "nds", "lynx", "pcengine",
  ],
  jewel_case: [
    "ps1", "ps3", "saturn", "dreamcast", "segacd", "threedo", "cdi", "pcfx",
    "scummvm", "dos", "amiga", "spectrum",
  ],
  caixa_dvd: ["ps2", "gamecube", "wii"],
  caixa_xbox: ["xbox360"],
  // UMD: disco pequeno numa caixinha propria, nem CD nem cartucho.
  umd: ["psp"],
  // Sem mídia física de verdade (portátil digital, homebrew) - cartão
  // genérico.
  cartao: ["tic80", "wasm4", "lowresnx", "uzebox", "tamagotchi", "j2me"],
};

const TIPO_MIDIA_POR_ID = {};
for (const [tipo, ids] of Object.entries(MIDIA_POR_PLATAFORMA)) {
  for (const id of ids) TIPO_MIDIA_POR_ID[id] = tipo;
}

function tipoDeMidia(plataformaId) {
  return TIPO_MIDIA_POR_ID[plataformaId] || "cartao";
}

function classeDaCapa(plataforma) {
  return String(plataforma || "").toLowerCase()
    .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "retro";
}

function prepararCapa(elemento, jogo) {
  const iniciais = iniciaisDaCapa(jogo.titulo);
  elemento.textContent = iniciais;
  const urls = [...(jogo.capa_urls || [])];
  if (!urls.length) return;

  const imagem = document.createElement("img");
  imagem.className = "capa-imagem";
  imagem.alt = `Capa de ${jogo.titulo}`;
  let indice = 0;
  const tentar = () => {
    if (indice >= urls.length) {
      imagem.remove();
      return;
    }
    imagem.src = urls[indice++];
  };
  imagem.addEventListener("error", tentar);
  elemento.append(imagem);
  tentar();
}

// "1 jogador", "até 2 jogadores", "até 5 jogadores" -- linguagem de aluno.
function textoJogadores(numero) {
  const n = Number(numero) || 2;
  return n <= 1 ? "1 jogador" : `até ${n} jogadores`;
}

function linhaDoJogo(jogo) {
  const plataforma = estado.porPlataforma[jogo.plataforma] || {};
  const disponivel = plataforma.estado === "pronta";

  const item = document.createElement("li");
  item.className = `jogo jogo--${plataforma.estado}` +
                   (disponivel ? "" : " jogo--indisponivel");
  item.dataset.jogo = jogo.id;
  item.classList.toggle("jogo--selecionado", estado.jogoSelecionado?.id === jogo.id);
  // Sem isto, quem usa só o teclado não consegue abrir o painel de detalhes.
  item.tabIndex = 0;
  item.setAttribute("role", "button");
  item.setAttribute("aria-label", `Ver detalhes de ${jogo.titulo}`);
  item.addEventListener("keydown", (evento) => {
    if (evento.target !== item) return;
    if (evento.key === "Enter" || evento.key === " ") {
      evento.preventDefault();
      selecionarJogo(jogo);
    }
  });

  // Arrastar a linha e soltar num console do lado esquerdo move o
  // arquivo de verdade para a pasta daquele console.
  item.draggable = true;
  item.addEventListener("dragstart", (evento) => {
    evento.dataTransfer.setData("text/plain", jogo.id);
    evento.dataTransfer.effectAllowed = "move";
    item.classList.add("jogo--arrastando");
  });
  item.addEventListener("dragend", () => {
    item.classList.remove("jogo--arrastando");
    for (const alvo of document.querySelectorAll(".trilho-item")) {
      alvo.classList.remove("trilho-item--alvo");
    }
  });

  const faixa = document.createElement("span");
  faixa.className = "jogo-faixa";

  const tipoMidia = tipoDeMidia(jogo.plataforma);
  const capa = document.createElement("div");
  capa.className = `jogo-cover jogo-cover--placeholder capa-${classeDaCapa(jogo.plataforma_nome)} ` +
                   `midia midia--${tipoMidia}`;
  capa.setAttribute("aria-hidden", "true");
  capa.title = { cartucho_h: "Cartucho", cartucho_v: "Cartucho portátil",
                jewel_case: "Caixa de CD/Blu-ray", caixa_dvd: "Caixa de DVD",
                caixa_xbox: "Caixa de DVD (Xbox 360)", umd: "UMD",
                cartao: "Mídia digital" }[tipoMidia];

  const etiqueta = document.createElement("div");
  etiqueta.className = "midia-etiqueta";
  prepararCapa(etiqueta, jogo);
  capa.append(etiqueta);

  const abrir = document.createElement("button");
  abrir.type = "button";
  abrir.className = "jogo-abrir";
  abrir.dataset.acao = "jogar";
  abrir.disabled = !disponivel;

  const favorito = document.createElement("button");
  favorito.type = "button";
  favorito.className = "jogo-favorito";
  favorito.dataset.acao = "favorito";
  const estaFavorito = (estado.config.favoritos || []).includes(jogo.id);
  favorito.textContent = estaFavorito ? "★" : "☆";
  favorito.title = estaFavorito ? "Remover dos favoritos" : "Adicionar aos favoritos";
  favorito.setAttribute("aria-label", favorito.title);

  const titulo = document.createElement("span");
  titulo.className = "jogo-titulo";
  titulo.textContent = jogo.titulo;

  const meta = document.createElement("span");
  meta.className = "jogo-meta";
  // Quantos jogam juntos: o número do arquivo do professor, já limitado
  // ao que o emulador deste console permite (servidor\jogadores.py).
  meta.textContent = `${jogo.plataforma_nome} · ${jogo.tamanho_mb} MB · ${textoJogadores(jogo.jogadores_max)}`;

  abrir.append(titulo, meta);

  // Como este console vai rodar nesta máquina. A cor é a informação.
  if (plataforma.classe_rotulo) {
    const selo = document.createElement("span");
    selo.className = `desempenho desempenho--${plataforma.classe_cor}`;
    selo.textContent = plataforma.classe_rotulo;
    // O porquê, ao parar o mouse: "não abre" sem motivo não ajuda ninguém.
    if (plataforma.classe_detalhe) selo.title = plataforma.classe_detalhe;
    abrir.append(selo);
  }

  if (!disponivel && plataforma.motivo) {
    const motivo = document.createElement("span");
    motivo.className = "jogo-motivo";
    motivo.textContent = plataforma.motivo;
    abrir.append(motivo);
  }

  const origem = document.createElement("span");
  origem.className = "jogo-origem";
  origem.textContent = jogo.origem_rotulo;

  const corpo = document.createElement("div");
  corpo.className = "jogo-corpo";
  corpo.append(abrir, origem);

  // As acoes grandes ficam no painel de detalhes. O card serve para navegar
  // pela biblioteca e nao repete uma fileira de botoes pequenos em cada jogo.
  item.append(faixa, capa, favorito, corpo);
  return item;
}

function desenharDetalhes() {
  const jogo = estado.jogoSelecionado;
  const painel = $("#detalhesJogo");
  const jogarBotao = $("#btnJogarSelecionado");
  const multiplayerBotao = $("#btnMultiplayerSelecionado");
  const gerirBotao = $("#btnGerirSelecionado");
  const consoleBotao = $("#btnEscolherConsole");
  if (!jogo) {
    painel.classList.add("detalhes--vazio");
    jogarBotao.disabled = true;
    multiplayerBotao.disabled = true;
    gerirBotao.disabled = true;
    consoleBotao.hidden = true;
    $("#btnAtualizarCapa").disabled = true;
    return;
  }
  $("#btnAtualizarCapa").disabled = false;
  const plataforma = estado.porPlataforma[jogo.plataforma] || {};
  painel.classList.remove("detalhes--vazio");
  $("#detalhesTitulo").textContent = jogo.titulo;
  $("#detalhesConsole").textContent = jogo.plataforma_nome;
  $("#detalhesDescricao").textContent = plataforma.descricao || "Jogo da biblioteca do ARENA.";
  $("#detalhesPlataforma").textContent = jogo.plataforma_nome;
  $("#detalhesTamanho").textContent = `${jogo.tamanho_mb} MB`;
  $("#detalhesOrigem").textContent = jogo.origem_rotulo;
  const capa = $("#detalhesCapa");
  capa.className = `detalhes-capa capa-${classeDaCapa(jogo.plataforma_nome)}`;
  prepararCapa(capa, jogo);
  jogarBotao.disabled = plataforma.estado !== "pronta";
  // Console sem jogo entre computadores: o botao continua ativo e abre a
  // explicacao de como jogar junto NO MESMO computador (pedido do Rafael).
  multiplayerBotao.disabled = plataforma.estado !== "pronta";
  multiplayerBotao.title = soNoMesmoComputador(jogo)
    ? "Neste console, jogar junto é no mesmo computador. Clique para ver como."
    : (jogo.motivo_jogadores || "");
  gerirBotao.disabled = plataforma.estado !== "pronta";
  consoleBotao.hidden = jogo.plataforma !== "indefinido";
}

async function abrirEscolhaConsole(jogo) {
  try {
    const dados = await pedir("/api/jogo?id=" + encodeURIComponent(jogo.id));
    const lista = $("#listaConsoleJogoModal");
    lista.replaceChildren();
    for (const console of dados.consoles || []) {
      const opcao = document.createElement("option");
      opcao.value = console.id;
      opcao.textContent = console.nome;
      if (console.id === dados.sugestao) opcao.selected = true;
      lista.append(opcao);
    }
    jogoConsoleEditando = jogo;
    $("#tituloConsoleJogo").textContent = `Escolha o console de ${jogo.titulo}`;
    $("#explicaConsoleJogo").textContent = dados.sugestao
      ? `O Arena suspeita de ${dados.consoles.find((c) => c.id === dados.sugestao)?.nome || "um console"}, mas você pode corrigir.`
      : "O Arena não conseguiu identificar automaticamente este arquivo.";
    $("#modalConsole").hidden = false;
  } catch (falha) {
    recado(falha.message, true);
  }
}

function selecionarJogo(jogo) {
  estado.jogoSelecionado = jogo;
  // A grade nao precisa ser recriada: recria-la faria cada imagem voltar
  // para o estado de carregamento e causaria o pisca das capas.
  for (const item of document.querySelectorAll("#listaJogos .jogo")) {
    item.classList.toggle("jogo--selecionado", item.dataset.jogo === jogo?.id);
  }
  desenharDetalhes();
}

function desenharJogos() {
  const lista = $("#listaJogos");
  const vazio = $("#vazio");
  const visiveis = jogosVisiveis();

  $("#contaVisivel").textContent =
    visiveis.length === estado.jogos.length
      ? "" : `${visiveis.length} de ${estado.jogos.length}`;

  if (visiveis.length === 0) {
    lista.replaceChildren();
    lista.hidden = true;
    vazio.hidden = false;
    $("#btnMais").hidden = true;
    if (estado.jogos.length > 0) {
      $("#vazioTitulo").textContent = "Nada encontrado com esse filtro";
      $("#vazioTexto").textContent =
        "Limpe a busca ou escolha Todos os jogos no lado esquerdo.";
    }
    return;
  }

  vazio.hidden = true;
  lista.hidden = false;

  // Desenha no maximo 'limite' linhas por vez. Com milhares de jogos num
  // pen drive, desenhar tudo de uma vez travaria a pagina por segundos.
  const lote = document.createDocumentFragment();
  const parcial = visiveis.slice(0, estado.limite);
  for (const jogo of parcial) lote.append(linhaDoJogo(jogo));
  lista.replaceChildren(lote);

  const faltam = visiveis.length - parcial.length;
  const botaoMais = $("#btnMais");
  botaoMais.hidden = faltam <= 0;
  botaoMais.textContent = `Mostrar mais ${Math.min(faltam, PASSO_LIMITE)}`;
}

// --------------------------------------------------------------------------
// Mover um jogo para a pasta de outro console
// --------------------------------------------------------------------------

async function moverJogo(jogoId, plataformaId) {
  const jogo = acharJogo(jogoId);
  if (!jogo) return;

  try {
    const dados = await pedir("/api/jogo/mover", "POST",
      { jogo_id: jogoId, plataforma: plataformaId });

    recado(dados.movido
      ? `${jogo.titulo} foi para a pasta ${dados.pasta}. Agora é ${dados.plataforma_nome}.`
      : `${jogo.titulo} já estava em ${dados.plataforma_nome}.`);

    await carregarCatalogo();
  } catch (falha) {
    recado(falha.message, true);
  }
}

// --------------------------------------------------------------------------
// Abrir jogo e registrar pontos
// --------------------------------------------------------------------------

const acharJogo = (id) => estado.jogos.find((jogo) => jogo.id === id);

async function jogar(jogo) {
  const apelido = apelidoAtual();
  if (!apelido) {
    recado("Escreva seu apelido lá em cima antes de jogar.", true);
    $("#campoApelidoInicial").focus();
    return;
  }
  try {
    const dados = await pedir("/api/jogar", "POST", { jogo_id: jogo.id, apelido });
    const recentes = [jogo.id, ...(estado.config.recentes || []).filter((id) => id !== jogo.id)].slice(0, 20);
    salvarConfig({ recentes }).then(() => desenharJogos()).catch(() => {});
    // O aviso do servidor (ficha do fliperama, rede do PS2/Xbox 360) nao
    // aparecia jogando sozinho: so o Jogar Junto lia dados.aviso.
    const aviso = dados.aviso ? " " + dados.aviso : "";
    recado(`Abrindo ${jogo.titulo} pelo ${dados.emulador}. Aguarde uns segundos.` + aviso,
      false, aviso ? 9000 : 6000);
    mostrarFaixaTeclas();
    mostrarAlertaMaquina(dados.alerta_maquina);
  } catch (falha) {
    recado(falha.message, true);
  }
}

// --------------------------------------------------------------------------
// O que esta deixando este computador lento (Ajustes > Maquina)
// --------------------------------------------------------------------------
// Tudo vem pronto do servidor (servidor/barreiras.py): o que foi achado, por
// que pesa, o que fazer e quem faz. A tela so desenha. O unico botao que
// muda alguma coisa e' "Fechar", e so para programas da lista segura.

const NOME_GRAVIDADE = { alta: "Grave", media: "Médio", baixa: "Leve" };

function desenharBarreiras(dados) {
  const lista = $("#listaBarreiras");
  const itens = dados.barreiras || [];
  $("#barreirasEstado").textContent = itens.length
    ? `${itens.length} coisa(s) encontrada(s), da mais grave para a mais leve. (Levou ${dados.segundos} s.)`
    : `Nada encontrado: este computador está sem as barreiras que o ARENA conhece. (Levou ${dados.segundos} s.)`;
  const lote = document.createDocumentFragment();
  for (const b of itens) {
    const item = document.createElement("li");
    item.className = `barreira barreira--${b.gravidade}`;

    const titulo = document.createElement("p");
    titulo.className = "barreira-titulo";
    const selo = document.createElement("span");
    selo.className = "barreira-selo";
    selo.textContent = NOME_GRAVIDADE[b.gravidade] || b.gravidade;
    titulo.append(selo, " " + b.titulo);

    const achado = document.createElement("p");
    achado.textContent = b.achado + " " + b.por_que;

    const acao = document.createElement("p");
    const rotulo = document.createElement("strong");
    rotulo.textContent = "O que fazer: ";
    acao.append(rotulo, b.acao);

    const quem = document.createElement("p");
    quem.className = "barreira-quem";
    quem.textContent = b.quem === "aluno"
      ? "Você consegue fazer isso sozinho."
      : "Precisa do professor ou do TI (pede senha de administrador).";

    item.append(titulo, achado, acao, quem);

    for (const alvo of b.fechar || []) {
      const botao = document.createElement("button");
      botao.className = "botao";
      botao.type = "button";
      botao.textContent = `Fechar ${alvo.nome}`;
      botao.addEventListener("click", async () => {
        botao.disabled = true;
        try {
          const r = await pedir("/api/barreiras/fechar", "POST", { programa: alvo.processo });
          recado(r.mensagem);
          botao.textContent = "Fechado";
        } catch (falha) {
          recado(falha.message, true);
          botao.disabled = false;
        }
      });
      item.append(botao);
    }
    lote.append(item);
  }
  lista.replaceChildren(lote);
}

async function verificarBarreiras() {
  const botao = $("#btnBarreiras");
  botao.disabled = true;
  botao.textContent = "Verificando…";
  $("#barreirasEstado").textContent = "Olhando o Windows. Leva uns 5 segundos.";
  try {
    desenharBarreiras(await pedir("/api/barreiras?forcar=1"));
  } catch (falha) {
    $("#barreirasEstado").textContent = falha.message;
  } finally {
    botao.disabled = false;
    botao.textContent = "Verificar de novo";
  }
}

// Memoria quase cheia, notebook na bateria, economia de bateria: o servidor
// confere isso na hora de abrir o jogo (~10 ms). Fica na barra de aviso do
// topo ate o jogo fechar -- o recado sumiria antes do aluno voltar.
function mostrarAlertaMaquina(alertas) {
  if (!alertas || !alertas.length) return;
  estado.avisoDaMaquina = true;
  aviso("Pode travar: " + alertas.map((a) => `${a.titulo}. ${a.acao}`).join(" ") +
        " (Veja mais em Ajustes > Máquina > O que está deixando este computador lento.)");
}

// --------------------------------------------------------------------------
// Faixa com as teclas do jogo
// --------------------------------------------------------------------------
// O ideal seria a mensagem aparecer DENTRO do jogo. Nao da, com seguranca:
// o RetroArch deste ARENA nao le comandos pelo stdin no Windows (testado:
// ignorou QUIT), e o outro caminho -- comandos pela rede -- deixaria um
// colega fechar o jogo de outro (brecha fechada na revisao pos-auditoria).
// Entao a faixa fica na janela do ARENA: aparece ao abrir o jogo e some
// quando ele fecha. Para saber se fechou, NAO fica perguntando ao servidor
// a cada segundo (roubaria processador do jogo num Celeron): pergunta uma
// vez so, quando o aluno volta para esta janela.

function mostrarFaixaTeclas() {
  $("#faixaTeclaF9").hidden = !estado.config.travar_teclas;
  $("#faixaTeclas").hidden = false;
}

async function conferirFaixaTeclas() {
  const faixa = $("#faixaTeclas");
  if (faixa.hidden) return;
  try {
    const dados = await pedir("/api/estado");
    if (!(dados.jogo_em_andamento && dados.jogo_em_andamento.ativo)) {
      faixa.hidden = true;
      if (estado.avisoDaMaquina) {
        estado.avisoDaMaquina = false;
        aviso("");
      }
    }
  } catch (falha) {
    // sem resposta: deixa a faixa como esta, confere na proxima volta
  }
}

window.addEventListener("focus", conferirFaixaTeclas);

async function alternarFavorito(jogo) {
  const atuais = new Set(estado.config.favoritos || []);
  if (atuais.has(jogo.id)) atuais.delete(jogo.id);
  else atuais.add(jogo.id);
  try {
    await salvarConfig({ favoritos: [...atuais] });
    desenharJogos();
    recado(atuais.has(jogo.id) ? "Adicionado aos favoritos." : "Removido dos favoritos.");
  } catch (falha) {
    recado(falha.message, true);
  }
}

function abrirPlacar(jogo) {
  estado.jogoDoPlacar = jogo;
  $("#placarJogo").textContent = jogo.titulo;
  $("#campoPontos").value = "";
  $("#modalPlacar").hidden = false;
  $("#campoPontos").focus();
}

async function salvarPlacar() {
  const pontos = $("#campoPontos").value;
  const apelido = apelidoAtual();

  if (!apelido) { recado("Escreva seu apelido no topo primeiro.", true); return; }
  if (pontos === "") { recado("Digite a pontuação.", true); return; }

  try {
    const resposta = await pedir("/api/placar", "POST", {
      jogo_id: estado.jogoDoPlacar.id, pontos: Number(pontos), apelido,
    });
    $("#modalPlacar").hidden = true;
    recado("Pontuação registrada.");
    mostrarPendentes(resposta.pendentes ?? 0);
    carregarRanking();
  } catch (falha) {
    recado(falha.message, true);
  }
}

// --------------------------------------------------------------------------
// Ajustes
// --------------------------------------------------------------------------

function desenharPerfis() {
  const lote = document.createDocumentFragment();

  for (const [chave, perfil] of Object.entries(estado.perfis)) {
    const botao = document.createElement("button");
    botao.type = "button";
    botao.className = "perfil" +
      (estado.config.perfil_grafico === chave ? " ativo" : "");
    botao.dataset.perfil = chave;

    const nome = document.createElement("span");
    nome.className = "perfil-nome";
    nome.textContent = perfil.rotulo;

    const resumo = document.createElement("span");
    resumo.className = "perfil-resumo";
    resumo.textContent = perfil.resumo;

    botao.append(nome, resumo);
    lote.append(botao);
  }

  $("#listaPerfis").replaceChildren(lote);
}

function controleDaOpcao(opcao) {
  // O valor mostrado e o EFETIVO: perfil aplicado, depois ajuste manual.
  // Ler so de config.avancado mostraria estado errado nas opcoes que vem
  // do perfil, como suavizar imagem e filtros de tela.
  const valor = estado.efetivas[opcao.chave] ??
                estado.config.avancado[opcao.chave] ?? "";

  if (opcao.tipo === "bool") {
    const chave = document.createElement("button");
    chave.type = "button";
    chave.className = "chave opcao-controle";
    chave.setAttribute("aria-pressed", String(valor === "true"));
    chave.setAttribute("aria-label", opcao.rotulo);
    chave.addEventListener("click", async () => {
      const novo = chave.getAttribute("aria-pressed") === "true" ? "false" : "true";
      chave.setAttribute("aria-pressed", novo);
      try {
        await salvarConfig({ avancado: { [opcao.chave]: novo } });
      } catch (falha) {
        chave.setAttribute("aria-pressed", novo === "true" ? "false" : "true");
        recado(falha.message, true);
      }
    });
    return chave;
  }

  const lista = document.createElement("select");
  lista.className = "opcao-controle";
  lista.setAttribute("aria-label", opcao.rotulo);
  for (const item of opcao.opcoes) {
    const escolha = document.createElement("option");
    escolha.value = item;
    escolha.textContent = item;
    if (item === valor) escolha.selected = true;
    lista.append(escolha);
  }
  lista.addEventListener("change", async () => {
    try {
      await salvarConfig({ avancado: { [opcao.chave]: lista.value } });
      if (opcao.chave === "video_driver") {
        $("#lidoDriver").textContent = estado.efetivas.video_driver;
      }
    } catch (falha) {
      recado(falha.message, true);
    }
  });
  return lista;
}

function desenharAvancado() {
  const lote = document.createDocumentFragment();

  for (const grupo of estado.gruposRecursos) {
    const doGrupo = estado.recursos.filter((r) => r.grupo === grupo.id);
    if (doGrupo.length === 0) continue;

    const titulo = document.createElement("h3");
    titulo.className = "grupo-titulo";
    titulo.textContent = grupo.nome;

    const resumo = document.createElement("p");
    resumo.className = "grupo-resumo";
    resumo.textContent = grupo.resumo;

    lote.append(titulo, resumo);

    for (const recurso of doGrupo) lote.append(linhaDoRecurso(recurso));
  }

  $("#listaAvancado").replaceChildren(lote);
}

function linhaDoRecurso(recurso) {
  const linha = document.createElement("div");
  linha.className = "opcao";

  const rotulo = document.createElement("span");
  rotulo.className = "opcao-rotulo";
  rotulo.textContent = recurso.nome;

  // Selo de custo: avisa antes de ligar algo pesado.
  if (recurso.custo && recurso.custo !== "nada") {
    const custo = document.createElement("span");
    custo.className = `custo custo--${recurso.custo}`;
    custo.textContent = recurso.custo === "alto" ? "pesa" : "pesa pouco";
    rotulo.append(" ", custo);
  }

  const ajuda = document.createElement("span");
  ajuda.className = "opcao-ajuda";
  ajuda.textContent = recurso.explica;

  linha.append(rotulo, controleDaOpcao(recurso), ajuda);

  // Exemplo: só aparece quando você pede, para não encher a tela.
  if (recurso.exemplo) {
    const puxar = document.createElement("button");
    puxar.type = "button";
    puxar.className = "opcao-exemplo-botao";
    puxar.textContent = "por exemplo…";

    const exemplo = document.createElement("span");
    exemplo.className = "opcao-exemplo";
    exemplo.textContent = recurso.exemplo;
    exemplo.hidden = true;

    puxar.addEventListener("click", () => {
      exemplo.hidden = !exemplo.hidden;
      puxar.hidden = !exemplo.hidden;
    });

    linha.append(puxar, exemplo);
  }

  return linha;
}

async function salvarConfig(mudanca) {
  const resposta = await pedir("/api/config", "POST", mudanca);
  estado.config = resposta.config;
  estado.efetivas = resposta.efetivas;
  atualizarBotaoTema();
  return resposta;
}

// --------------------------------------------------------------------------
// Colegas que o ARENA achou sozinho
// --------------------------------------------------------------------------

async function carregarColegas() {
  try {
    const dados = await pedir("/api/colegas");
    estado.colegasOnline = dados.colegas || [];
    desenharAmigos(estado.colegasOnline);
    preencherAmigosPartida();
    const lote = document.createDocumentFragment();

    const ativos = (dados.colegas || []).filter((colega) => colega.partida_aberta);

    if (ativos.length === 0) {
      const vazio = document.createElement("li");
      vazio.className = "explica";
      vazio.textContent =
        "Nenhuma partida aberta por perto ainda. Quando alguém começar uma " +
        "partida na mesma rede, ela aparecerá aqui.";
      lote.append(vazio);
    }

    for (const colega of ativos) {
      const item = document.createElement("li");
      item.className = "controle";

      const nome = document.createElement("span");
      nome.className = "controle-nome";
      nome.textContent = colega.apelido;

      const nota = document.createElement("span");
      nota.className = "controle-nota";
      nota.textContent = colega.partida_aberta
        ? `${colega.jogo_partida || "Partida aberta"} · ${colega.codigo_amigo}`
        : `${colega.codigo_amigo} · Arena disponível na rede`;

      item.append(nome, nota);

      if (colega.ja_e_amigo) {
        const selo = document.createElement("span");
        selo.className = "controle-tipo";
        selo.textContent = "já é amigo";
        item.append(selo);
      } else {
        const adicionar = document.createElement("button");
        adicionar.type = "button";
        adicionar.className = "botao jogo-placar";
        adicionar.textContent = "Adicionar";
        adicionar.addEventListener("click", async () => {
          try {
            await pedir("/api/amigo/codigo", "POST",
              { codigo: colega.codigo_amigo });
            recado(`${colega.apelido} entrou na sua lista de amigos.`);
            await carregarEstado();
          } catch (falha) {
            recado(falha.message, true);
          }
        });
        item.append(adicionar);
      }
      lote.append(item);
    }

    $("#listaColegas").replaceChildren(lote);
  } catch (falha) {
    // Sem rede liberada isso é esperado. Não vale um aviso na tela.
  }
}

// --------------------------------------------------------------------------
// Qualidade gráfica dos emuladores externos (PCSX2, RPCS3, Xenia)
// --------------------------------------------------------------------------

const EXPLICA_PRESET_GRAFICO = {
  automatico: "O ARENA escolhe pela força do seu computador: aumenta a " +
    "resolução em máquina forte, deixa no tamanho original em máquina fraca.",
  leve: "Sempre no tamanho original do jogo, sem suavizar nada. Ex.: um " +
    "jogo de PS3 que travava vira jogável, mas com um pouco mais de serrilhado.",
  bonito: "Sempre a maior resolução e o melhor acabamento que o ARENA " +
    "sabe pedir. Ex.: um jogo de Xbox 360 fica bem mais nítido, mas pode " +
    "cair de quadros por segundo em computador fraco.",
};

function atualizarExplicaPreset() {
  const valor = $("#listaPresetGrafico").value;
  $("#explicaPresetGrafico").textContent =
    EXPLICA_PRESET_GRAFICO[valor] || EXPLICA_PRESET_GRAFICO.automatico;
}

// --------------------------------------------------------------------------
// Perfil: apelido + foto, permanente
// --------------------------------------------------------------------------

function atualizarFotoPerfil(temFoto) {
  const img = $("#perfilFoto");
  const vazia = $("#perfilFotoVazia");
  const remover = $("#btnRemoverFotoPerfil");
  if (temFoto) {
    img.src = "/api/perfil/foto?t=" + Date.now();
    img.hidden = false;
    vazia.hidden = true;
    remover.hidden = false;
  } else {
    img.hidden = true;
    vazia.hidden = false;
    remover.hidden = true;
  }
}

function redimensionarFotoPerfil(arquivo) {
  return new Promise((resolve, reject) => {
    const leitor = new FileReader();
    leitor.onerror = () => reject(new Error("Não consegui ler o arquivo."));
    leitor.onload = () => {
      const imagem = new Image();
      imagem.onerror = () => reject(new Error("Arquivo não é uma imagem válida."));
      imagem.onload = () => {
        const tamanho = 256;
        const tela = document.createElement("canvas");
        tela.width = tamanho;
        tela.height = tamanho;
        const ctx = tela.getContext("2d");
        const lado = Math.min(imagem.width, imagem.height);
        const origemX = (imagem.width - lado) / 2;
        const origemY = (imagem.height - lado) / 2;
        ctx.drawImage(imagem, origemX, origemY, lado, lado, 0, 0, tamanho, tamanho);
        resolve(tela.toDataURL("image/jpeg", 0.85));
      };
      imagem.src = leitor.result;
    };
    leitor.readAsDataURL(arquivo);
  });
}

function desenharRedePs2(redePs2) {
  const jogos = redePs2.jogos || [];
  const status = $("#statusRedePs2");
  const explicaDriver = $("#explicaDriverPs2");

  if (jogos.length === 0) {
    status.textContent = "Nenhum jogo com rede de verdade confirmado ainda.";
    explicaDriver.hidden = true;
    return;
  }

  const lista = jogos.map((j) => j[0].toUpperCase() + j.slice(1)).join(", ");
  if (redePs2.driver_instalado) {
    status.textContent = `Driver de rede instalado — hospedar e entrar liberados em: ${lista}.`;
  } else {
    status.textContent = `Sem o driver de rede — só dá pra entrar (não hospedar) em: ${lista}.`;
  }
  explicaDriver.hidden = !!redePs2.driver_instalado;
}

// --------------------------------------------------------------------------
// Endereços desta máquina
// --------------------------------------------------------------------------

function desenharEnderecos(lista) {
  const lote = document.createDocumentFragment();

  for (const item of lista) {
    const linha = document.createElement("li");

    const rotulo = document.createElement("span");
    rotulo.textContent = item.rotulo;

    const endereco = document.createElement("code");
    endereco.textContent = item.url;

    linha.append(rotulo, endereco);
    lote.append(linha);
  }

  $("#listaEnderecos").replaceChildren(lote);
}

// --------------------------------------------------------------------------
// Levar o progresso de um ARENA para outro
// --------------------------------------------------------------------------

function desenharPacotes(lista) {
  const lote = document.createDocumentFragment();

  if (lista.length === 0) {
    const vazio = document.createElement("li");
    vazio.className = "explica";
    vazio.textContent = "Nenhum pacote montado ainda.";
    lote.append(vazio);
  }

  for (const pacote of lista) {
    const linha = document.createElement("li");

    const nome = document.createElement("span");
    nome.textContent = `${pacote.quando} · ${pacote.tamanho_mb} MB`;

    const trazer = document.createElement("button");
    trazer.type = "button";
    trazer.className = "botao jogo-placar";
    trazer.textContent = "Trazer de volta";
    trazer.addEventListener("click", () => importarPacote(pacote.nome));

    const arquivo = document.createElement("code");
    arquivo.textContent = pacote.nome;

    linha.append(nome, arquivo, trazer);
    lote.append(linha);
  }

  $("#listaPacotes").replaceChildren(lote);
}

async function exportarPacote() {
  const botao = $("#btnExportar");
  botao.disabled = true;
  recado("Juntando tudo…");
  try {
    const dados = await pedir("/api/exportar", "POST", {});
    recado(`Pronto: ${dados.itens} arquivos, ${dados.tamanho_mb} MB. ` +
           `Está em backup\\${dados.arquivo}`);
    const estadoNovo = await pedir("/api/estado");
    desenharPacotes(estadoNovo.pacotes || []);
  } catch (falha) {
    recado(falha.message, true);
  } finally {
    botao.disabled = false;
  }
}

async function importarPacote(arquivo) {
  try {
    const dados = await pedir("/api/importar", "POST", { arquivo });
    recado(dados.trazidos === 0
      ? "Você já tinha tudo o que estava nesse pacote."
      : `${dados.trazidos} arquivos trazidos. ${dados.ja_existiam} já existiam e foram mantidos.`);
  } catch (falha) {
    recado(falha.message, true);
  }
}

// --------------------------------------------------------------------------
// Controles
// --------------------------------------------------------------------------

function desenharControles(lista) {
  const lote = document.createDocumentFragment();

  for (const [nome, tipo, nota] of lista) {
    const item = document.createElement("li");
    item.className = "controle";

    const titulo = document.createElement("span");
    titulo.className = "controle-nome";
    titulo.textContent = nome;

    const detalhe = document.createElement("span");
    detalhe.className = "controle-nota";
    detalhe.textContent = nota;

    item.append(titulo, detalhe);

    if (tipo !== "-") {
      const selo = document.createElement("span");
      selo.className = "controle-tipo";
      selo.textContent = tipo;
      item.append(selo);
    }
    lote.append(item);
  }

  $("#listaControles").replaceChildren(lote);
}

// --------------------------------------------------------------------------
// Mapear teclas e botões
// --------------------------------------------------------------------------

// O RetroArch tem nomes próprios para as teclas. Esta tabela traduz o que
// o navegador informa (event.code) para o nome que ele entende.
const TECLA_RETROARCH = {
  ArrowUp: "up", ArrowDown: "down", ArrowLeft: "left", ArrowRight: "right",
  Enter: "enter", NumpadEnter: "kp_enter", Space: "space", Tab: "tab",
  Backspace: "backspace", Escape: "escape",
  ShiftLeft: "shift", ShiftRight: "rshift",
  ControlLeft: "ctrl", ControlRight: "rctrl",
  AltLeft: "alt", AltRight: "ralt",
  Insert: "insert", Delete: "del", Home: "home", End: "end",
  PageUp: "pageup", PageDown: "pagedown",
  Comma: "comma", Period: "period", Semicolon: "semicolon",
  Quote: "quote", Slash: "slash", Backslash: "backslash",
  Minus: "minus", Equal: "equals",
  BracketLeft: "leftbracket", BracketRight: "rightbracket",
  Backquote: "backquote",
};

function traduzirTecla(evento) {
  const codigo = evento.code || "";
  if (TECLA_RETROARCH[codigo]) return TECLA_RETROARCH[codigo];
  if (/^Key[A-Z]$/.test(codigo)) return codigo.slice(3).toLowerCase();
  if (/^Digit[0-9]$/.test(codigo)) return codigo.slice(5);
  if (/^F([1-9]|1[0-2])$/.test(codigo)) return codigo.toLowerCase();
  if (/^Numpad[0-9]$/.test(codigo)) return "keypad" + codigo.slice(6);
  return null;
}

function aplicarPerfil(perfil) {
  // Chave que aquele controle ou aquele console nao tem fica apagada e
  // nao clica. Mostrar um interruptor que nao faz nada e pior que
  // esconder.
  const chaves = [
    ["chaveDirecional", perfil.direcional, perfil.direcional_possivel],
    ["chaveAnalogicoEsq", perfil.analogico_esquerdo,
     perfil.analogicos_possiveis >= 1],
    ["chaveAnalogicoDir", perfil.analogico_direito,
     perfil.analogicos_possiveis >= 2],
    ["chaveVibracao", perfil.vibracao, perfil.vibracao_possivel],
  ];

  for (const [id, ligado, possivel] of chaves) {
    const botao = $("#" + id);
    botao.setAttribute("aria-pressed", ligado ? "true" : "false");
    botao.closest(".opcao").classList.toggle("opcao--indisponivel", !possivel);
  }

  const temExtra = perfil.aceita_mouse || perfil.aceita_teclado;
  $("#campoExtra").hidden = !temExtra;
  if (temExtra) {
    $("#listaExtra").value = perfil.dispositivo_extra || "";
    $("#notaExtra").textContent = perfil.aceita_teclado
      ? "Este console aceitava mouse e teclado de verdade."
      : "Este console aceitava mouse de verdade.";
  }

  $("#notaTipo").textContent = perfil.nota_controle ||
    `${perfil.tipo}: ${perfil.analogicos_possiveis} analógico(s) neste console` +
    (perfil.paletas ? `, ${perfil.paletas} paletas` : "");
  $("#notaConsole").textContent = perfil.nota_console ||
    (perfil.vibracao_possivel ? "Este console tinha vibração."
                              : "Este console não tinha vibração.");
}

function prepararMapa(consoles) {
  const lista = $("#mapaConsole");
  const lote = document.createDocumentFragment();

  for (const c of consoles) {
    const item = document.createElement("option");
    item.value = c.id;
    item.textContent = c.nome;
    if (c.id === "ps2") item.selected = true;
    lote.append(item);
  }
  lista.replaceChildren(lote);

  // Lista de controles que o aluno pode ter.
  pedir("/api/perfis-controle?tipo=xbox360&console=ps1").then((perfil) => {
    const tipos = document.createDocumentFragment();
    for (const t of perfil.tipos) {
      const item = document.createElement("option");
      item.value = t.id;
      item.textContent = t.nome;
      if (t.id === perfil.tipo_escolhido) item.selected = true;
      tipos.append(item);
    }
    $("#mapaTipo").replaceChildren(tipos);
    desenharMapa();
  }).catch(() => {});

  lista.onchange = () => desenharMapa();
  $("#mapaJogador").onchange = () => desenharMapa();
  $("#mapaTipo").onchange = async () => {
    await pedir("/api/perfil-controle", "POST",
      { tipo_controle: $("#mapaTipo").value });
    desenharMapa();
  };

  for (const [id, chave] of [["direcional", "chaveDirecional"],
                             ["analogico_esq", "chaveAnalogicoEsq"],
                             ["analogico_dir", "chaveAnalogicoDir"],
                             ["vibracao", "chaveVibracao"]]) {
    $("#" + chave).addEventListener("click", async (evento) => {
      const botao = evento.currentTarget;
      const novo = botao.getAttribute("aria-pressed") !== "true";
      try {
        await pedir("/api/perfil-controle", "POST",
          { console: $("#mapaConsole").value, [id]: novo });
        await desenharMapa();
      } catch (falha) {
        recado(falha.message, true);
      }
    });
  }

  $("#listaExtra").addEventListener("change", async (evento) => {
    try {
      await pedir("/api/perfil-controle", "POST",
        { console: $("#mapaConsole").value, extra: evento.target.value });
      recado(evento.target.value
        ? `Jogador 2 vai usar o ${evento.target.value} do computador.`
        : "Jogador 2 volta ao controle.");
    } catch (falha) {
      recado(falha.message, true);
    }
  });

  desenharMapa();
}

async function desenharMapa() {
  const consoleId = $("#mapaConsole").value;
  const jogador = $("#mapaJogador").value;

  try {
    const tipo = $("#mapaTipo").value || "xbox360";
    const [mapa, nomes, perfil] = await Promise.all([
      pedir("/api/mapeamento"),
      pedir("/api/botoes?console=" + encodeURIComponent(consoleId)),
      pedir("/api/perfis-controle?tipo=" + encodeURIComponent(tipo) +
            "&console=" + encodeURIComponent(consoleId)),
    ]);
    estado.mapa = mapa;
    estado.perfil = perfil;
    aplicarPerfil(perfil);

    // Nome do console para cada botão do RetroArch: "Botao B" -> "X"
    const traducao = {};
    for (const b of nomes.botoes) {
      const chave = b.retroarch.replace("Botao ", "").replace("Direcional ", "")
        .toLowerCase();
      traducao[chave] = b.console;
    }

    const atribuidos = mapa.mapeamento[jogador] || {};
    const lote = document.createDocumentFragment();

    const permitidos = new Set(perfil.linhas.map((l) => l.botao));

    for (const botao of mapa.botoes) {
      if (!permitidos.has(botao)) continue;
      const linha = document.createElement("li");
      linha.className = "mapa-linha";

      const noControle = (perfil.linhas.find((l) => l.botao === botao) || {})
        .no_controle;

      const nome = document.createElement("span");
      nome.className = "mapa-nome";
      nome.textContent = traducao[botao] || botao.toUpperCase();

      const tecnico = document.createElement("span");
      tecnico.className = "mapa-tecnico";
      tecnico.textContent = noControle
        ? `no seu controle: ${noControle}`
        : "no RetroArch: " + botao;

      const valor = document.createElement("span");
      const atual = atribuidos[botao];
      valor.className = "mapa-valor" + (atual ? "" : " mapa-valor--vazio");
      valor.textContent = atual
        ? (atual.tipo === "teclado" ? `tecla ${atual.valor}`
           : atual.tipo === "botao" ? `botão ${atual.valor}`
           : atual.tipo === "hat" ? `direcional ${atual.valor}`
           : `eixo ${atual.valor}`)
        : "o RetroArch decide";

      const definir = document.createElement("button");
      definir.type = "button";
      definir.className = "botao mapa-definir";
      definir.textContent = atual ? "Trocar" : "Definir";
      definir.addEventListener("click", () =>
        capturar(linha, valor, definir, jogador, botao));

      linha.append(nome, valor, definir, tecnico);
      lote.append(linha);
    }

    $("#listaMapa").replaceChildren(lote);
    $("#mapaResumo").textContent = Object.entries(mapa.resumo || {})
      .map(([numero, quantos]) => `Jogador ${numero}: ${quantos}`)
      .join(" · ") + " botões definidos.";

    // Controles conhecidos (Xbox, PlayStation, etc.) já têm mapeamento
    // automático — o assistente só aparece para controles genéricos.
    const ehGenerico = tipo.startsWith("generico");
    $("#btnMapaWizard").hidden = !ehGenerico;
    $("#mapaWatacao").hidden = !ehGenerico;
  } catch (falha) {
    recado(falha.message, true);
  }
}

  $("#btnMapaWizard").addEventListener("click", () => {
    iniciarWizard();
  });

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

async function gravaWizard(tipo, valor) {
  const passo = PASSOS_WIZARD[wizardEstado.passo];
  if (!passo) return;

  wizardCancela = null;
  estado.ouvindo = null;

  try {
    await pedir("/api/mapeamento/definir", "POST", {
      jogador: wizardEstado.jogador,
      botao: passo.botao,
      tipo: tipo,
      valor: valor,
    });
    wizardEstado.passo++;
    wizardPasso(wizardEstado.passo);
    recado("Registrado! Próximo passo.");
  } catch (falha) {
    recado(falha.message || "Erro ao gravar.", true);
    wizardCancelar();
  }
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

function capturar(linha, valor, botaoDefinir, jogador, botao) {
  if (estado.ouvindo) estado.ouvindo();

  linha.classList.add("mapa-linha--ouvindo");
  valor.textContent = "aperte agora…";
  botaoDefinir.textContent = "Cancelar";

  let vivo = true;
  let quadro = null;

  const encerrar = () => {
    if (!vivo) return;
    vivo = false;
    estado.ouvindo = null;
    if (quadro) cancelAnimationFrame(quadro);
    document.removeEventListener("keydown", noTeclado, true);
    linha.classList.remove("mapa-linha--ouvindo");
  };

  const gravar = async (tipo, bruto) => {
    encerrar();
    try {
      await pedir("/api/mapeamento/definir", "POST",
        { jogador, botao, tipo, valor: bruto });
      await desenharMapa();
      recado("Pronto. Vale no próximo jogo que você abrir.");
    } catch (falha) {
      recado(falha.message, true);
      await desenharMapa();
    }
  };

  function noTeclado(evento) {
    evento.preventDefault();
    evento.stopPropagation();
    if (evento.key === "Escape") { encerrar(); desenharMapa(); return; }
    const tecla = traduzirTecla(evento);
    if (!tecla) { recado("Essa tecla o RetroArch não reconhece.", true); return; }
    gravar("teclado", tecla);
  }

  // O navegador numera o direcional como botões 12 a 15. O RetroArch não
  // usa essa numeração: para ele o direcional é um "chapéu" (h0up...).
  // Escrever 12 ali deixaria o direcional mudo — foi o bug que o Xbox
  // 360 mostrou.
  const DIRECIONAL_DO_NAVEGADOR = { 12: "up", 13: "down", 14: "left", 15: "right" };

  // Controle XInput (Xbox, GameSir...): o número do navegador NÃO é o do
  // RetroArch. Sem esta tradução, o Start (9 no navegador) virava o R3 (9
  // no XInput do RetroArch) — achado com os GameSir do Rafael (25/09/2026).
  // Os gatilhos no RetroArch são eixos, não botões.
  const XINPUT_DO_NAVEGADOR = {
    0: ["botao", "0"], 1: ["botao", "1"], 2: ["botao", "2"], 3: ["botao", "3"],
    4: ["botao", "4"], 5: ["botao", "5"], 6: ["eixo", "+4"], 7: ["eixo", "+5"],
    8: ["botao", "7"], 9: ["botao", "6"], 10: ["botao", "8"], 11: ["botao", "9"],
    16: ["botao", "10"],
  };

  // Controle: o navegador só entrega o estado, então a gente olha a cada
  // quadro até algum botão estar apertado.
  function olharControle() {
    if (!vivo) return;
    const conectados = navigator.getGamepads ? navigator.getGamepads() : [];
    for (const pad of conectados) {
      if (!pad) continue;
      const padrao = pad.mapping === "standard";
      // O Chrome atual chama os controles XInput de "Xbox One Game
      // Controller (STANDARD GAMEPAD)", sem a palavra "XInput" (visto com
      // os GameSir, 25/09/2026). Outros navegadores ainda dizem "XInput".
      const xinput = /xinput|xbox/i.test(pad.id);
      for (let i = 0; i < pad.buttons.length; i++) {
        if (!pad.buttons[i].pressed) continue;
        if (padrao && DIRECIONAL_DO_NAVEGADOR[i]) {
          gravar("hat", DIRECIONAL_DO_NAVEGADOR[i]);
        } else if (xinput) {
          const traduzido = XINPUT_DO_NAVEGADOR[i];
          if (!traduzido) {
            encerrar();
            desenharMapa();
            recado("Esse botão o RetroArch não lê neste controle. Clique em Definir e aperte outro.", true);
            return;
          }
          gravar(traduzido[0], traduzido[1]);
        } else if (padrao) {
          // PlayStation, Switch e outros que o navegador reconhece: o número
          // de verdade ele não mostra, e o RetroArch já tem o perfil pronto.
          encerrar();
          desenharMapa();
          recado("Esse controle já é reconhecido sozinho pelo RetroArch — " +
                 "não precisa definir. Se algum botão sair trocado, use " +
                 "Voltar ao reconhecimento automático.");
        } else {
          // Genérico sem padrão: o número cru é o mesmo do DirectInput.
          gravar("botao", String(i));
        }
        return;
      }
    }
    quadro = requestAnimationFrame(olharControle);
  }

  document.addEventListener("keydown", noTeclado, true);
  quadro = requestAnimationFrame(olharControle);
  estado.ouvindo = encerrar;

  botaoDefinir.onclick = () => { encerrar(); desenharMapa(); };
}

// --------------------------------------------------------------------------
// Que botão é qual, em cada console
// --------------------------------------------------------------------------

function prepararBotoes(consoles) {
  const lista = $("#listaConsoleBotoes");
  const lote = document.createDocumentFragment();

  for (const c of consoles) {
    const item = document.createElement("option");
    item.value = c.id;
    item.textContent = c.nome;
    if (c.id === "ps2") item.selected = true;
    lote.append(item);
  }
  lista.replaceChildren(lote);

  lista.onchange = () => desenharBotoes(lista.value);
  desenharBotoes(lista.value);
}

async function desenharBotoes(consoleId) {
  try {
    const dados = await pedir("/api/botoes?console=" + encodeURIComponent(consoleId));
    const lote = document.createDocumentFragment();

    for (const b of dados.botoes) {
      const item = document.createElement("li");
      item.className = "controle";

      const nome = document.createElement("span");
      nome.className = "controle-nome";
      nome.textContent = b.console;

      const nota = document.createElement("span");
      nota.className = "controle-nota";
      nota.textContent = `aparece como "${b.retroarch}" na tela de configuração`;

      item.append(nome, nota);
      lote.append(item);
    }
    $("#listaBotoes").replaceChildren(lote);
  } catch (falha) {
    recado(falha.message, true);
  }
}

// --------------------------------------------------------------------------
// Emuladores de fora
// --------------------------------------------------------------------------

function desenharExternos(lista) {
  const lote = document.createDocumentFragment();

  for (const item of lista) {
    const linha = document.createElement("li");
    linha.className = "controle";

    const titulo = document.createElement("span");
    titulo.className = "controle-nome";
    titulo.textContent = `${item.plataforma} — ${item.nome}`;

    const nota = document.createElement("span");
    nota.className = "controle-nota";
    if (item.instalado && item.falta) {
      nota.textContent = `instalado, mas falta uma coisa: ${item.falta}`;
    } else if (item.instalado) {
      nota.textContent = "instalado. O ARENA está usando ele.";
    } else if (item.compactado_pendente) {
      nota.textContent =
        `Achamos "${item.compactado_pendente}" em ${item.pasta}, mas ele ` +
        `ainda está compactado. Extraia o conteúdo dentro dessa mesma pasta.`;
    } else {
      nota.textContent = `${item.motivo} Baixe em ${item.site} e ponha em ${item.pasta}`;
    }

    const selo = document.createElement("span");
    selo.className = "controle-tipo";
    selo.textContent = item.instalado
      ? (item.falta ? "incompleto" : "em uso")
      : (item.compactado_pendente ? "falta extrair" : "não instalado");
    if (!item.instalado || item.falta) selo.style.opacity = "0.55";

    linha.append(titulo, nota, selo);
    lote.append(linha);
  }

  $("#listaExternos").replaceChildren(lote);
}

// --------------------------------------------------------------------------
// BIOS por console
// --------------------------------------------------------------------------

function desenharBios(consoles, arquivos) {
  const caixa = $("#listaBios");

  if (arquivos.length === 0) {
    const vazio = document.createElement("p");
    vazio.className = "explica";
    vazio.textContent =
      "Nenhum arquivo em retroarch\\system ainda. Coloque lá e volte aqui.";
    caixa.replaceChildren(vazio);
    return;
  }

  const lote = document.createDocumentFragment();
  const escolhidas = estado.config.bios || {};

  for (const c of consoles) {
    const linha = document.createElement("div");
    linha.className = "opcao";

    const rotulo = document.createElement("span");
    rotulo.className = "opcao-rotulo";
    rotulo.textContent = c.nome;

    // O emulador deste console nao deixa escolher (ele confere o conteudo
    // de cada arquivo e acha a BIOS certa sozinho). Oferecer uma lista aqui
    // seria prometer uma escolha que nao acontece.
    const escolhiveis = c.escolhiveis || [];
    if (escolhiveis.length === 0) {
      const sozinho = document.createElement("span");
      sozinho.className = "opcao-ajuda";
      sozinho.textContent =
        "O emulador acha a BIOS certa sozinho, pelo conteúdo do arquivo. Não precisa escolher.";
      linha.append(rotulo, sozinho);
      lote.append(linha);
      continue;
    }

    const lista = document.createElement("select");
    lista.className = "opcao-controle";
    lista.setAttribute("aria-label", "BIOS do " + c.nome);

    const nenhum = document.createElement("option");
    nenhum.value = "";
    nenhum.textContent = "deixar o emulador escolher";
    lista.append(nenhum);

    for (const a of arquivos.filter((a) => escolhiveis.includes(a.arquivo))) {
      const item = document.createElement("option");
      item.value = a.arquivo;
      item.textContent = `${a.arquivo} · ${a.tamanho_kb} KB`;
      if (escolhidas[c.id] === a.arquivo) item.selected = true;
      lista.append(item);
    }

    lista.addEventListener("change", async () => {
      try {
        await salvarConfig({ bios: { [c.id]: lista.value } });
        recado(lista.value
          ? `${c.nome} vai usar ${lista.value} sempre.`
          : `${c.nome} volta a escolher sozinho.`);
      } catch (falha) {
        recado(falha.message, true);
      }
    });

    const ajuda = document.createElement("span");
    ajuda.className = "opcao-ajuda";
    ajuda.textContent = "Sempre a mesma: mantém data, hora e memory card.";

    linha.append(rotulo, lista, ajuda);
    lote.append(linha);
  }

  caixa.replaceChildren(lote);
}

// --------------------------------------------------------------------------
// Abrir só a BIOS
// --------------------------------------------------------------------------

function prepararAbrirBios(consoles) {
  const lista = $("#listaBiosAbrir");
  const lote = document.createDocumentFragment();

  for (const c of consoles) {
    const item = document.createElement("option");
    item.value = c.id;
    item.textContent = c.nome;
    if (c.id === "ps1") item.selected = true;
    lote.append(item);
  }
  lista.replaceChildren(lote);
}

// --------------------------------------------------------------------------
// Jogos que fecharam sozinhos
// --------------------------------------------------------------------------

function desenharFechamentos(lista) {
  const caixa = $("#listaFechamentos");

  if (lista.length === 0) {
    const vazio = document.createElement("li");
    vazio.className = "explica";
    vazio.textContent = "Nenhum até agora.";
    caixa.replaceChildren(vazio);
    return;
  }

  const lote = document.createDocumentFragment();
  for (const q of lista.slice().reverse()) {
    const item = document.createElement("li");
    item.className = "controle";

    const nome = document.createElement("span");
    nome.className = "controle-nome";
    nome.textContent = `${q.jogo} (${q.plataforma})`;

    const nota = document.createElement("span");
    nota.className = "controle-nota";
    nota.textContent =
      `${q.emulador} saiu com código ${q.codigo_saida} · ` +
      new Date(q.quando).toLocaleString("pt-BR");

    item.append(nome, nota);
    lote.append(item);
  }
  caixa.replaceChildren(lote);
}

// --------------------------------------------------------------------------
// Memory cards
// --------------------------------------------------------------------------

function desenharCartoes(lista) {
  const caixa = $("#listaCartoes");

  if (lista.length === 0) {
    const vazio = document.createElement("li");
    vazio.className = "explica";
    vazio.textContent =
      "Nenhum cartão ainda. Ele aparece aqui depois que você salvar num jogo.";
    caixa.replaceChildren(vazio);
    return;
  }

  const lote = document.createDocumentFragment();

  for (const c of lista) {
    const item = document.createElement("li");
    item.className = "controle";

    const nome = document.createElement("span");
    nome.className = "controle-nome";
    nome.textContent = c.arquivo;

    const nota = document.createElement("span");
    nota.className = "controle-nota";
    nota.textContent = c.blocos_usados === null || c.blocos_usados === undefined
      ? `${c.tamanho_kb} KB · último uso em ${c.quando}`
      : `${c.blocos_usados} de ${c.blocos_total} blocos usados · último uso em ${c.quando}`;

    item.append(nome, nota);

    if (c.blocos_total) {
      const selo = document.createElement("span");
      selo.className = "controle-tipo";
      selo.textContent = `${c.blocos_total - c.blocos_usados} livres`;
      item.append(selo);
    }
    lote.append(item);
  }

  caixa.replaceChildren(lote);
}

// --------------------------------------------------------------------------
// Partida a dois
// --------------------------------------------------------------------------

// Console que NAO joga entre computadores (o emulador nao tem o Jogar Junto,
// ou e' emulador de fora como PCSX2/Dolphin/Xenia/RPCS3).
function soNoMesmoComputador(jogo) {
  const plataforma = estado.porPlataforma[jogo.plataforma] || {};
  return plataforma.netplay === false || plataforma.aceita_partida === false;
}

function abrirJuntoLocal(jogo) {
  const plataforma = estado.porPlataforma[jogo.plataforma] || {};
  const n = Math.max(2, Number(jogo.jogadores_max) || 2);
  $("#juntoLocalJogo").textContent = `${jogo.titulo} — até ${n} jogadores.`;
  $("#juntoLocalMotivo").textContent = plataforma.aceita_partida === false
    ? `Este console abre por outro programa (${plataforma.emulador}), que não ` +
      "tem o Jogar Junto do ARENA. Por isso vocês jogam juntos no mesmo " +
      "computador, cada um com seu controle."
    : "Neste console, o emulador não consegue deixar dois computadores " +
      "iguais ao mesmo tempo. Por isso vocês jogam juntos no mesmo " +
      "computador, cada um com seu controle.";
  const passos = [
    "Ligue os controles antes de abrir o jogo. O 1º controle é o jogador 1, " +
      "o 2º é o jogador 2, e assim por diante.",
    "O teclado joga como o primeiro jogador sem controle " +
      "(com 3 controles, o teclado é o jogador 4).",
    `Dentro do jogo, escolha o modo de 2, 3 ou ${n} jogadores.`,
    "Algum controle não responde ou está trocado? Feche o jogo, ligue os " +
      "controles na ordem certa e abra de novo. Se precisar, veja " +
      "Ajustes → Controles.",
  ];
  if (jogo.plataforma === "wii") {
    passos.splice(2, 0, "No Wii, cada controle vira um Wii Remote com Nunchuk: " +
      "o analógico esquerdo anda, o direito move a seta.");
  }
  const lista = $("#juntoLocalPassos");
  lista.replaceChildren(...passos.map((texto) => {
    const item = document.createElement("li");
    item.textContent = texto;
    return item;
  }));
  const rede = $("#juntoLocalRede");
  rede.hidden = !jogo.rede_propria;
  rede.textContent = jogo.rede_propria
    ? "Este jogo também tem rede própria (System Link): com 2 computadores, " +
      "abra o jogo nos dois e use o menu de rede DENTRO do jogo."
    : "";
  $("#modalJuntoLocal").hidden = false;
}

function abrirPartida(jogo) {
  estado.jogoDaPartida = jogo;
  estado.papelDaPartida = "hospedar";
  estado.partidaEscolhida = "";
  $("#partidaJogo").textContent = jogo.titulo;
  $("#campoAmigoPartida").hidden = true;
  $("#campoJogadorPartida").hidden = true;
  preencherAmigosPartida();
  carregarColegas();
  $("#campoInternet").hidden = false;
  $("#chaveInternet").setAttribute("aria-pressed", "false");
  $("#resultadoTeste").textContent = "";

  for (const b of document.querySelectorAll("#modalPartida .perfil")) {
    b.classList.toggle("ativo", b.dataset.papel === "hospedar");
  }
  $("#modalPartida").hidden = false;
}

async function comecarPartida() {
  const apelido = apelidoAtual();
  if (!apelido) { recado("Escreva seu apelido lá em cima primeiro.", true); return; }

  const pelaInternet =
    $("#chaveInternet").getAttribute("aria-pressed") === "true";

  const corpo = {
    jogo_id: estado.jogoDaPartida.id,
    apelido,
    partida: estado.papelDaPartida,
    pela_internet: pelaInternet,
  };
  if (estado.papelDaPartida !== "hospedar") {
    const escolha = $("#listaAmigosPartida").selectedOptions[0];
    corpo.endereco = escolha ? escolha.value : "";
    corpo.partida_token = escolha ? (escolha.dataset.token || "") : "";
    if (!corpo.endereco) {
      recado("Escolha na lista a partida aberta do amigo. Se a lista estiver " +
        "vazia, ele precisa clicar em “Eu abro a partida” primeiro.", true);
      return;
    }
  }
  if (estado.papelDaPartida === "entrar" && !$("#campoJogadorPartida").hidden) {
    corpo.jogador = Number($("#listaJogadorPartida").value) || 2;
  }

  try {
    const dados = await pedir("/api/jogar", "POST", corpo);
    $("#modalPartida").hidden = true;
    const porRepasse = dados.pela_internet ? " (pela internet, com repasse)" : "";
    const texto = estado.papelDaPartida === "hospedar"
      ? `Sala criada${porRepasse}. O jogo abrirá quando seu amigo entrar.`
      : estado.papelDaPartida === "assistir"
      ? "Entrando para assistir. Você vê a tela dele, sem controlar nada."
      : `Entrando como ${dados.papel}. Aguarde a tela abrir.`;
    const aviso = dados.aviso ? " " + dados.aviso : "";
    recado(texto + aviso, false, aviso ? 9000 : 4500);
    mostrarFaixaTeclas();
  } catch (falha) {
    recado(falha.message, true);
  }
}

// --------------------------------------------------------------------------
// Amigos
// --------------------------------------------------------------------------

// "online" pode vir de três lugares: colegas achados na rede (objetos com
// id/url), o resultado de Sincronizar (só apelidos) e o vigia do servidor
// (estado.servidoresOnline, também apelidos). Bug de 30/09/2026: depois de
// Sincronizar a lista recebia só apelidos, a comparação procurava id/url e
// TODO amigo aparecia "Fora do ar" -- justamente quando a troca deu certo.
// A busca de partidas (UDP + TCP) é a fonte mais completa: vale junto com a
// que chegou agora por até 60 s. Sem isso, quem desenhasse por último (a
// descoberta, que só vê o UDP) apagava o "online" que a busca tinha achado.
function amigoEstaOnline(amigo, online) {
  const apelidos = new Set(estado.servidoresOnline || []);
  const recente = (Date.now() - (estado.partidasEm || 0)) < 60000;
  const fontes = recente ? [...(online || []), ...(estado.partidasEncontradas || [])]
    : (online || []);
  const objetos = [];
  for (const item of fontes) {
    if (typeof item === "string") apelidos.add(item);
    else if (item.online !== false) objetos.push(item);
  }
  // Primeiro pelo endereço. O código do aparelho só vale se não se repetir:
  // em laboratório com imagem clonada dois colegas podem ter o mesmo código,
  // e um apareceria online (ou com partida) no lugar do outro.
  const porEndereco = objetos.find((item) => item.url === amigo.url);
  if (porEndereco) return porEndereco;
  if (amigo.id) {
    const mesmos = objetos.filter((item) => item.id === amigo.id);
    if (new Set(mesmos.map((item) => item.url)).size === 1) return mesmos[0];
  }
  return apelidos.has(amigo.apelido) ? {} : null;
}

function desenharAmigos(online) {
  const caixa = $("#listaAmigos");

  if (estado.amigos.length === 0) {
    const vazio = document.createElement("li");
    vazio.className = "explica";
    vazio.textContent = "Você ainda não adicionou ninguém.";
    caixa.replaceChildren(vazio);
    return;
  }

  const lote = document.createDocumentFragment();

  for (const amigo of estado.amigos) {
    const colega = amigoEstaOnline(amigo, online);
    const ligado = Boolean(colega);

    const item = document.createElement("li");
    item.className = "amigo";

    const sinal = document.createElement("span");
    sinal.className = "sinal " + (ligado ? "sinal--pronta" : "sinal--pesada");
    sinal.title = ligado ? "Online agora" : "Fora do ar";

    const nome = document.createElement("span");
    nome.className = "amigo-nome";
    nome.textContent = amigo.apelido + (amigo.escola ? " (escola)" : "");

    const url = document.createElement("span");
    url.className = "amigo-url";
    url.textContent = colega && colega.partida_aberta
      ? `Partida aberta: ${colega.jogo_partida || "jogo"}`
      : ligado
      ? "Online agora" + (amigo.codigo_amigo || amigo.id
        ? ` · ${amigo.codigo_amigo || amigo.id}` : "")
      : amigo.codigo_amigo || amigo.id || "Fora da rede local";

    const remover = document.createElement("button");
    remover.type = "button";
    remover.className = "cheat-apagar";
    remover.textContent = "remover";
    remover.addEventListener("click", () => removerAmigo(amigo.apelido));

    item.append(sinal, nome, remover, url);
    lote.append(item);
  }

  caixa.replaceChildren(lote);
}

// Lista de "Entrar na partida do amigo": só quem está com partida ABERTA
// agora. Vem de /api/partida/procurar, que junta a descoberta da rede (UDP)
// com uma pergunta direta a cada amigo salvo (o mesmo caminho dos recordes).
function preencherAmigosPartida() {
  const lista = $("#listaAmigosPartida");
  if (!lista) return;

  // Só a escolha FEITA PELO ALUNO é mantida (evento "change"). A marcação
  // automática de quando havia uma partida só não conta como escolha.
  const escolhida = estado.partidaEscolhida || "";
  const candidatos = (estado.partidasEncontradas || [])
    .filter((colega) => colega.partida_aberta);
  const unicos = new Map();
  for (const colega of candidatos) {
    if (colega.url && !unicos.has(colega.url)) unicos.set(colega.url, colega);
  }

  // A lista se atualiza a cada 4 s: só redesenha se algo mudou. Redesenhar
  // sem mudança fecha a lista aberta no meio da escolha do aluno.
  const assinatura = JSON.stringify([estado.procurandoPartidas,
    [...unicos.values()].map((c) => [c.url, c.apelido, c.jogo_partida, c.jogo_id_partida]),
    estado.jogoDaPartida ? estado.jogoDaPartida.id : ""]);
  if (assinatura === lista.dataset.assinatura && lista.options.length) return;
  lista.dataset.assinatura = assinatura;

  lista.replaceChildren();
  if (!unicos.size) {
    const opcao = document.createElement("option");
    opcao.value = "";
    opcao.textContent = estado.procurandoPartidas
      ? "Procurando partidas abertas…"
      : "Nenhuma partida aberta ainda — o amigo clica em “Eu abro a partida”";
    lista.append(opcao);
    return;
  }

  // Com mais de uma partida aberta, o aluno escolhe: nenhuma vem marcada,
  // senão um clique apressado em Começar entraria na partida errada.
  if (unicos.size > 1) {
    const escolha = document.createElement("option");
    escolha.value = "";
    escolha.textContent = `Escolha a partida (${unicos.size} abertas)`;
    lista.append(escolha);
  }

  // Compara só o NOME do arquivo: o mesmo jogo pode estar em "pessoais" num
  // computador e em "turma" no outro, e continua sendo o mesmo jogo.
  const nomeDoArquivo = (id) => String(id || "").split("/").pop();
  const meuJogo = estado.jogoDaPartida ? nomeDoArquivo(estado.jogoDaPartida.id) : "";
  for (const colega of unicos.values()) {
    const opcao = document.createElement("option");
    opcao.value = colega.url;
    opcao.dataset.token = colega.partida_token || "";
    const nome = colega.apelido || "ARENA na rede";
    const outroJogo = meuJogo && colega.jogo_id_partida &&
      nomeDoArquivo(colega.jogo_id_partida) !== meuJogo;
    const jogo = colega.jogo_partida
      ? ` · ${outroJogo ? "OUTRO JOGO: " : ""}${colega.jogo_partida}` : "";
    opcao.textContent = `${nome}${jogo}`;
    lista.append(opcao);
  }
  // Mantém a escolha do aluno quando a lista se atualiza sozinha.
  if (escolhida && unicos.has(escolhida)) lista.value = escolhida;
}

async function procurarPartidas() {
  // Uma busca por vez: amigo fora do ar faz a busca levar até 3 s, e a
  // próxima (a cada 4 s) não pode empilhar em cima.
  if (estado.buscandoPartidas) return;
  estado.buscandoPartidas = true;
  estado.procurandoPartidas = !(estado.partidasEncontradas || []).length;
  try {
    const dados = await pedir("/api/partida/procurar");
    estado.partidasEncontradas = dados.colegas || [];
    estado.partidasEm = Date.now();
    desenharAmigos(estado.partidasEncontradas);
  } catch (falha) {
    estado.partidasEncontradas = [];
  } finally {
    estado.buscandoPartidas = false;
    estado.procurandoPartidas = false;
    preencherAmigosPartida();
  }
}

// Enquanto a janela Jogar Junto está aberta como convidado, procura de novo a
// cada 4 s: a partida do amigo aparece sozinha, sem fechar e abrir a janela.
function vigiarPartidas(ligar) {
  clearInterval(estado.vigiaPartidas);
  estado.vigiaPartidas = null;
  if (!ligar) return;
  procurarPartidas();
  estado.vigiaPartidas = setInterval(() => {
    if ($("#modalPartida").hidden || estado.papelDaPartida === "hospedar") {
      vigiarPartidas(false);
      return;
    }
    procurarPartidas();
  }, 4000);
}

async function adicionarAmigoCodigo() {
  const campo = $("#amigoCodigo");
  const codigo = campo.value.trim();
  if (!codigo) { recado("Digite o código de amigo.", true); return; }

  try {
    const dados = await pedir("/api/amigo/codigo", "POST", { codigo });
    estado.amigos = dados.servidores;
    campo.value = "";
    desenharAmigos([]);
    preencherAmigosPartida();
    recado("Amigo adicionado. Quando ele estiver na mesma rede, ficará disponível para jogar.");
  } catch (falha) {
    recado(falha.message, true);
  }
}

async function adicionarAmigo() {
  const apelido = $("#amigoApelido").value.trim();
  const url = $("#amigoUrl").value.trim();

  if (!apelido) { recado("Escreva o apelido do amigo.", true); return; }
  if (!url) { recado("Escreva o endereço do ARENA dele.", true); return; }

  try {
    const dados = await pedir("/api/amigo/adicionar", "POST", { apelido, url });
    estado.amigos = dados.servidores;
    desenharAmigos([]);
    $("#amigoApelido").value = "";
    $("#amigoUrl").value = "";
    recado(`${apelido} entrou na lista. Clique em Sincronizar agora.`);
  } catch (falha) {
    recado(falha.message, true);
  }
}

async function removerAmigo(apelido) {
  try {
    const dados = await pedir("/api/amigo/remover", "POST", { apelido });
    estado.amigos = dados.servidores;
    desenharAmigos([]);
    recado(`${apelido} removido.`);
  } catch (falha) {
    recado(falha.message, true);
  }
}

async function testarAmigo() {
  const url = $("#amigoUrl").value.trim();
  if (!url) { recado("Cole o endereço primeiro.", true); return; }

  const botao = $("#btnTestarAmigo");
  botao.disabled = true;
  try {
    const dados = await pedir("/api/amigo/testar", "POST", { url });
    recado(dados.apelido
      ? `Achei! É o ARENA de ${dados.apelido}.`
      : "Achei, mas esse ARENA ainda não tem apelido.");
    if (dados.apelido && !$("#amigoApelido").value.trim()) {
      $("#amigoApelido").value = dados.apelido;
    }
  } catch (falha) {
    recado(falha.message, true);
  } finally {
    botao.disabled = false;
  }
}

// --------------------------------------------------------------------------
// Save states e cheats
// --------------------------------------------------------------------------

async function abrirGaveta_jogo(jogo) {
  estado.jogoAberto = jogo;
  $("#tituloJogo").textContent = "Saves e cheats";
  $("#jogoNomeEstados").textContent = jogo.titulo;
  $("#jogoNomeCheats").textContent = jogo.titulo;
  abrirGaveta("gavetaJogo");

  try {
    const dados = await pedir("/api/jogo?id=" + encodeURIComponent(jogo.id));
    desenharConsoleDoJogo(jogo, dados);
    desenharEspacos(dados.estados);
    desenharCheats(dados.cheats);
    $("#temSave").textContent = dados.tem_save
      ? "Este jogo também tem save normal, daquele que o próprio jogo grava."
      : "Você ainda não salvou pelo menu do próprio jogo.";
  } catch (falha) {
    recado(falha.message, true);
  }
}

function desenharConsoleDoJogo(jogo, dados) {
  const lista = $("#listaConsoleJogo");
  const lote = document.createDocumentFragment();

  for (const console_ of dados.consoles) {
    const item = document.createElement("option");
    item.value = console_.id;
    item.textContent = console_.nome;
    if (console_.id === dados.plataforma) item.selected = true;
    lote.append(item);
  }
  lista.replaceChildren(lote);

  $("#avisoConsole").textContent = dados.ambiguo
    ? "Este arquivo serve a mais de um console. Escolha e o ARENA move para a pasta certa."
    : `Está na pasta "${dados.pasta_atual || "raiz"}". Escolher outro move o arquivo.`;

  // Deixa a sugestão já marcada, para ser um clique só.
  if (dados.ambiguo && dados.sugestao) lista.value = dados.sugestao;

  lista.onchange = async () => {
    await moverJogo(jogo.id, lista.value);
    $("#gavetaJogo").hidden = true;
  };
}

function desenharEspacos(espacos) {
  const lote = document.createDocumentFragment();

  for (const espaco of espacos) {
    const caixa = document.createElement("div");
    caixa.className = "espaco" + (espaco.existe ? " espaco--cheio" : "");

    const numero = document.createElement("span");
    numero.className = "espaco-numero";
    numero.textContent = espaco.espaco;

    const info = document.createElement("span");
    info.className = "espaco-info";
    info.textContent = espaco.existe
      ? `${espaco.quando}\n${espaco.tamanho_kb} KB`
      : "vazio";

    caixa.append(numero, info);

    if (espaco.existe) {
      const apagar = document.createElement("button");
      apagar.type = "button";
      apagar.className = "espaco-apagar";
      apagar.textContent = "apagar";
      apagar.addEventListener("click", () => apagarEspaco(espaco.espaco));
      caixa.append(apagar);
    }
    lote.append(caixa);
  }

  $("#listaEspacos").replaceChildren(lote);
}

async function apagarEspaco(numero) {
  try {
    const dados = await pedir("/api/estado/apagar", "POST", {
      jogo_id: estado.jogoAberto.id, espaco: numero,
    });
    desenharEspacos(dados.estados);
    recado(`Espaço ${numero} apagado.`);
  } catch (falha) {
    recado(falha.message, true);
  }
}

function desenharCheats(lista) {
  const caixa = $("#listaCheats");

  if (lista.length === 0) {
    const vazio = document.createElement("li");
    vazio.className = "explica";
    vazio.textContent = "Nenhum código neste jogo ainda.";
    caixa.replaceChildren(vazio);
    return;
  }

  const lote = document.createDocumentFragment();

  lista.forEach((cheat, indice) => {
    const item = document.createElement("li");
    item.className = "cheat";

    const chave = document.createElement("button");
    chave.type = "button";
    chave.className = "chave";
    chave.setAttribute("aria-pressed", String(cheat.ligado));
    chave.setAttribute("aria-label", cheat.descricao);
    chave.addEventListener("click", () => alterarCheat(indice, !cheat.ligado));

    const desc = document.createElement("span");
    desc.className = "cheat-desc";
    desc.textContent = cheat.descricao;

    const codigo = document.createElement("span");
    codigo.className = "cheat-codigo";
    codigo.textContent = cheat.codigo.replace(/\+/g, "  ");

    const apagar = document.createElement("button");
    apagar.type = "button";
    apagar.className = "cheat-apagar";
    apagar.textContent = "apagar";
    apagar.addEventListener("click", () => alterarCheat(indice, null, true));

    item.append(chave, desc, apagar, codigo);
    lote.append(item);
  });

  caixa.replaceChildren(lote);
}

async function alterarCheat(indice, ligado, apagar = false) {
  try {
    const dados = await pedir("/api/cheat/alterar", "POST", {
      jogo_id: estado.jogoAberto.id, indice, ligado, apagar,
    });
    desenharCheats(dados.cheats);
  } catch (falha) {
    recado(falha.message, true);
  }
}

async function adicionarCheat() {
  const descricao = $("#cheatDescricao").value.trim();
  const codigo = $("#cheatCodigo").value.trim();

  if (!descricao) { recado("Escreva o que o código faz, tipo: vidas infinitas.", true); return; }
  if (!codigo) { recado("Digite o código.", true); return; }

  try {
    const dados = await pedir("/api/cheat/adicionar", "POST", {
      jogo_id: estado.jogoAberto.id, descricao, codigo, ligado: false,
    });
    desenharCheats(dados.cheats);
    $("#cheatDescricao").value = "";
    $("#cheatCodigo").value = "";
    recado("Código salvo. Ligue na chavinha ao lado.");
  } catch (falha) {
    recado(falha.message, true);
  }
}

// --------------------------------------------------------------------------
// Sincronizacao de recordes
// --------------------------------------------------------------------------

function mostrarPendentes(quantos) {
  const selo = $("#seloPendentes");
  selo.textContent = quantos;
  selo.hidden = quantos === 0;

  $("#statusPendentes").textContent = quantos === 0
    ? "Está tudo enviado."
    : `${quantos} recorde(s) esperando para subir.`;
}

async function enviarRecordes() {
  const botoes = [$("#btnSincronizar"), $("#btnEnviarAgora")];
  for (const b of botoes) b.disabled = true;
  recado("Mandando…");

  try {
    const dados = await pedir("/api/sincronizar", "POST");
    mostrarPendentes(0);

    const online = dados.resultados.filter((r) => r.ok).map((r) => r.apelido);
    const fora = dados.resultados.filter((r) => !r.ok);

    recado(`${dados.enviados} enviados, ${dados.recebidos} recebidos` +
      (online.length ? ` · ${online.join(", ")}` : "") +
      (fora.length ? ` · sem resposta: ${fora.map((r) => r.apelido).join(", ")}` : ""));

    desenharAmigos(online);
    carregarRanking();
  } catch (falha) {
    recado(falha.message, true);
  } finally {
    for (const b of botoes) b.disabled = false;
  }
}

// --------------------------------------------------------------------------
// Recordes
// --------------------------------------------------------------------------

function formatarTempo(segundos) {
  const horas = Math.floor(segundos / 3600);
  const minutos = Math.floor((segundos % 3600) / 60);
  return horas > 0 ? `${horas} h ${minutos} min` : `${minutos} min`;
}

function desenharRanking(alvo, linhas, formatar, textoVazio) {
  const caixa = $(alvo);

  if (linhas.length === 0) {
    const paragrafo = document.createElement("p");
    paragrafo.className = "explica";
    paragrafo.textContent = textoVazio;
    caixa.replaceChildren(paragrafo);
    return;
  }

  const grupos = new Map();
  for (const linha of linhas) {
    if (!grupos.has(linha.jogo)) grupos.set(linha.jogo, []);
    grupos.get(linha.jogo).push(linha);
  }

  const lote = document.createDocumentFragment();

  for (const [jogo, entradas] of grupos) {
    const bloco = document.createElement("div");
    bloco.className = "ranking-jogo";

    const titulo = document.createElement("h3");
    titulo.className = "ranking-titulo";
    titulo.textContent = jogo;
    bloco.append(titulo);

    for (const entrada of entradas) {
      const linha = document.createElement("div");
      linha.className = "ranking-linha";

      const posicao = document.createElement("span");
      posicao.className = `ranking-pos ranking-pos--${entrada.posicao}`;
      posicao.textContent = entrada.posicao;

      const apelido = document.createElement("span");
      apelido.textContent = entrada.apelido;

      const valor = document.createElement("span");
      valor.className = "ranking-valor";
      valor.textContent = formatar(entrada);

      linha.append(posicao, apelido, valor);
      bloco.append(linha);
    }
    lote.append(bloco);
  }

  caixa.replaceChildren(lote);
}

async function carregarConquistas() {
  try {
    const dados = await pedir("/api/conquistas");
    const caixa = $("#listaConquistas");
    const jogadores = dados.jogadores || [];
    if (!jogadores.length) {
      caixa.textContent = "A turma ainda não desbloqueou nenhuma conquista.";
      return;
    }
    const lote = document.createDocumentFragment();
    for (const jogador of jogadores) {
      const bloco = document.createElement("section");
      bloco.className = "conquistas-jogador";
      const titulo = document.createElement("h3");
      titulo.textContent = `${jogador.apelido} · ${jogador.total} desbloqueada(s)`;
      bloco.append(titulo);
      for (const conquista of jogador.conquistas) {
        const item = document.createElement("div");
        item.className = `conquista${conquista.liberada ? " conquista--liberada" : ""}`;
        const icone = document.createElement("span");
        icone.className = "conquista-icone";
        icone.setAttribute("aria-hidden", "true");
        icone.textContent = conquista.liberada ? "★" : "○";
        const texto = document.createElement("span");
        texto.className = "conquista-texto";
        const nome = document.createElement("b");
        nome.textContent = conquista.nome;
        const descricao = document.createElement("small");
        descricao.textContent = conquista.descricao;
        texto.append(nome, descricao);
        item.append(icone, texto);
        bloco.append(item);
      }
      lote.append(bloco);
    }
    caixa.replaceChildren(lote);
  } catch (falha) { recado(falha.message, true); }
}

async function carregarRanking() {
  try {
    const dados = await pedir("/api/ranking");
    desenharRanking("#rankingPontos", dados.placar,
      (e) => e.pontos.toLocaleString("pt-BR"),
      "Ninguém registrou pontuação ainda. Jogue e clique em Registrar pontos.");
    desenharRanking("#rankingTempo", dados.tempo,
      (e) => `${formatarTempo(e.segundos)} · ${e.partidas} partidas`,
      "Nenhuma partida registrada ainda. Partidas de menos de 30 segundos não contam.");
  } catch (falha) {
    recado(falha.message, true);
  }
}

async function carregarAcervo() {
  try {
    const dados = await pedir("/api/acervo");
    const lista = $("#listaAcervo");
    const consulta = $("#campoBuscaAcervo")?.value.trim().toLocaleLowerCase() || "";
    const todos = dados.itens || [];
    const itens = todos.filter((item) => !consulta ||
      `${item.titulo} ${item.plataforma} ${item.descricao} ${item.fonte_nome}`
        .toLocaleLowerCase().includes(consulta));
    $("#acervoVazio").hidden = itens.length > 0;
    const fontes = $("#listaFontesAcervo");
    if (fontes) {
      fontes.replaceChildren();
      for (const fonte of (dados.fontes || [])) {
        const selo = document.createElement("span");
        selo.className = "acervo-fonte-selo";
        selo.textContent = `Fonte: ${fonte.nome}`;
        fontes.append(selo);
      }
    }
    const lote = document.createDocumentFragment();
    for (const item of itens) {
      const linha = document.createElement("li");
      linha.className = "controle";
      const texto = document.createElement("span");
      texto.className = "controle-nome";
      texto.textContent = `${item.titulo} · ${item.plataforma}`;
      const nota = document.createElement("span");
      nota.className = "controle-nota";
      nota.textContent = !item.autorizado
        ? `Rascunho · autorização pendente · ${item.licenca}`
        : item.instalado
          ? `Instalado · ${item.licenca}`
          : `${item.fonte_nome} · ${item.licenca}`;
      const acoes = document.createElement("div");
      acoes.className = "controle-acoes";
      const botao = document.createElement("button");
      botao.className = "botao";
      botao.type = "button";
      botao.textContent = item.instalado ? "Instalado" : "Instalar";
      botao.disabled = item.instalado || !item.autorizado;
      botao.addEventListener("click", async () => {
        botao.disabled = true;
        botao.textContent = "Baixando…";
        try {
          const resultado = await pedir("/api/acervo/instalar", "POST", { id: item.id });
          recado(`${resultado.titulo} instalado com segurança.`);
          await carregarCatalogo();
          await carregarAcervo();
        } catch (falha) {
          botao.disabled = false;
          botao.textContent = "Instalar";
          recado(falha.message, true);
        }
      });
      const editar = document.createElement("button");
      editar.className = "botao";
      editar.type = "button";
      editar.textContent = "Editar";
      editar.addEventListener("click", () => abrirEditorAcervo(item));
      const remover = document.createElement("button");
      remover.className = "botao botao--perigo";
      remover.type = "button";
      remover.textContent = "Remover";
      remover.addEventListener("click", async () => {
        if (!window.confirm(`Remover “${item.titulo}” do acervo? O arquivo local não será apagado.`)) return;
        try {
          await pedir("/api/acervo/remover", "POST", { id: item.id });
          recado("Item removido do acervo. O arquivo local foi preservado.");
          await carregarAcervo();
        } catch (falha) {
          recado(falha.message, true);
        }
      });
      acoes.append(botao);
      linha.append(texto, nota, acoes);
      lote.append(linha);
    }
    lista.replaceChildren(lote);
  } catch (falha) {
    recado(falha.message, true);
  }
}

let atrasoBiblioteca = null;
let atrasoAcervo = null;

async function carregarBibliotecaOnline() {
  const consulta = $("#campoBuscaOnline").value.trim();
  const lista = $("#listaBibliotecaOnline");
  const status = $("#bibliotecaOnlineStatus");
  if (consulta.length < 2) {
    lista.replaceChildren();
    status.textContent = "Digite pelo menos 2 letras para pesquisar.";
    return;
  }
  status.textContent = "Procurando na biblioteca autorizada…";
  try {
    const dados = await pedir("/api/biblioteca-online?q=" + encodeURIComponent(consulta));
    const itens = dados.itens || [];
    const lote = document.createDocumentFragment();
    for (const item of itens) {
      const linha = document.createElement("li");
      linha.className = "controle";
      const nome = document.createElement("span");
      nome.className = "controle-nome";
      nome.textContent = item.titulo;
      const nota = document.createElement("span");
      nota.className = "controle-nota";
      nota.textContent = `${item.fonte} · ${item.tamanho ? formatarBytes(item.tamanho) : "tamanho não informado"}`;
      if (item.plataforma_nome) nota.textContent += ` · ${item.plataforma_nome}`;
      const progresso = document.createElement("div");
      progresso.className = "download-progresso";
      progresso.setAttribute("role", "progressbar");
      progresso.setAttribute("aria-label", `Instalando ${item.titulo}`);
      progresso.hidden = true;
      const botao = document.createElement("button");
      botao.className = "botao botao--principal";
      botao.type = "button";
      botao.textContent = "Instalar";
      botao.addEventListener("click", async () => {
        botao.disabled = true;
        botao.textContent = "Instalando…";
        progresso.hidden = false;
        progresso.classList.add("download-progresso--ativo");
        try {
          const resultado = await pedir("/api/biblioteca-online/instalar", "POST", {
            id: item.id, arquivo: item.arquivo, plataforma: item.plataforma,
          });
          botao.textContent = "Instalado";
          progresso.classList.remove("download-progresso--ativo");
          progresso.classList.add("download-progresso--concluido");
          recado(`${resultado.titulo} instalado na biblioteca.`);
          await carregarCatalogo();
          await carregarAcervo();
        } catch (falha) {
          botao.disabled = false;
          botao.textContent = "Instalar";
          progresso.hidden = true;
          progresso.classList.remove("download-progresso--ativo");
          recado(falha.message, true);
        }
      });
      linha.append(nome, nota, progresso, botao);
      lote.append(linha);
    }
    lista.replaceChildren(lote);
    status.textContent = itens.length
      ? `${itens.length} jogo(s) encontrado(s).`
      : "Nenhum jogo autorizado encontrado com esse nome.";
  } catch (falha) {
    status.textContent = "A biblioteca online está indisponível no momento.";
    recado(falha.message, true);
  }
}

function preencherCampo(id, valor = "") {
  const campo = $(id);
  if (campo) campo.value = valor;
}

function abrirEditorAcervo(item = null) {
  $("#tituloAcervoEditor").textContent = item ? "Editar jogo autorizado" : "Adicionar jogo autorizado";
  preencherCampo("#acervoId", item?.id || "");
  preencherCampo("#acervoTitulo", item?.titulo || "");
  preencherCampo("#acervoPlataforma", item?.plataforma || "");
  preencherCampo("#acervoDescricao", item?.descricao || "");
  preencherCampo("#acervoLicenca", item?.licenca || "");
  preencherCampo("#acervoFonte", item?.fonte || "");
  preencherCampo("#acervoUrl", item?.url || "");
  preencherCampo("#acervoDestino", item?.destino || "");
  preencherCampo("#acervoSha256", item?.sha256 || "");
  $("#acervoAutorizado").checked = Boolean(item?.autorizado);
  $("#acervoEditorStatus").textContent = "";
  $("#modalAcervo").hidden = false;
  $("#acervoTitulo").focus();
}

function lerEditorAcervo() {
  return {
    id: $("#acervoId").value.trim(),
    titulo: $("#acervoTitulo").value.trim(),
    plataforma: $("#acervoPlataforma").value.trim(),
    descricao: $("#acervoDescricao").value.trim(),
    licenca: $("#acervoLicenca").value.trim(),
    fonte: $("#acervoFonte").value.trim(),
    url: $("#acervoUrl").value.trim(),
    destino: $("#acervoDestino").value.trim(),
    sha256: $("#acervoSha256").value.trim().toLowerCase(),
    autorizado: $("#acervoAutorizado").checked,
  };
}

// --------------------------------------------------------------------------
// Eventos
// --------------------------------------------------------------------------

function abrirGaveta(id) {
  for (const gaveta of document.querySelectorAll(".gaveta")) {
    gaveta.hidden = gaveta.id !== id;
  }
}

function ligarEventos() {
  // Um ouvinte para o trilho inteiro, em vez de um por botao.
  $(".trilho").addEventListener("click", (evento) => {
    const botao = evento.target.closest(".trilho-item");
    if (!botao) return;
    estado.filtroPlataforma = botao.dataset.plataforma || "";
    estado.limite = PASSO_LIMITE;
    for (const item of document.querySelectorAll(".trilho-item")) {
      item.classList.toggle("ativo", item === botao);
    }
    desenharJogos();
  });

  // Um ouvinte para a lista inteira de jogos.
  $("#listaJogos").addEventListener("click", (evento) => {
    const alvo = evento.target.closest("[data-acao]");
    const item = evento.target.closest(".jogo");
    if (item) {
      selecionarJogo(acharJogo(item.dataset.jogo));
    }
    if (!alvo) return;
    const jogo = acharJogo(alvo.closest(".jogo").dataset.jogo);
    if (!jogo) return;
    if (alvo.dataset.acao === "favorito") { alternarFavorito(jogo); return; }
    if (alvo.dataset.acao === "jogar") jogar(jogo);
    if (alvo.dataset.acao === "placar") abrirPlacar(jogo);
    if (alvo.dataset.acao === "gerir") abrirGaveta_jogo(jogo);
    if (alvo.dataset.acao === "dupla") abrirPartida(jogo);
  });

  // Busca com atraso: sem isso, cada tecla redesenharia a lista inteira.
  let atrasoBusca = null;
  $("#campoBusca").addEventListener("input", (evento) => {
    const texto = evento.target.value;
    clearTimeout(atrasoBusca);
    atrasoBusca = setTimeout(() => {
      estado.busca = texto;
      estado.limite = PASSO_LIMITE;
      desenharJogos();
    }, 130);
  });

  $("#btnMais").addEventListener("click", () => {
    estado.limite += PASSO_LIMITE;
    desenharJogos();
  });

  for (const [id, filtro] of [["btnTodosJogos", "todos"],
                              ["btnFavoritos", "favoritos"],
                              ["btnRecentes", "recentes"]]) {
    $("#" + id).addEventListener("click", () => {
      estado.filtroRapido = filtro;
      estado.limite = PASSO_LIMITE;
      for (const botao of document.querySelectorAll(".filtro-rapido"))
        botao.classList.toggle("ativo", botao.id === id);
      desenharJogos();
    });
  }

  $("#btnCriarPastas").addEventListener("click", async () => {
    try {
      const dados = await pedir("/api/pastas/criar", "POST", {});
      recado(dados.criadas === 0
        ? "As pastas já existiam todas."
        : `${dados.criadas} pastas criadas em jogos\\pessoais. Agora é só arrastar os jogos para dentro.`);
      await carregarCatalogo();
    } catch (falha) {
      recado(falha.message, true);
    }
  });

  $("#btnAtualizar").addEventListener("click", async () => {
    try {
      await pedir("/api/indexar", "POST");
      await carregarCatalogo();
      recado(`Lista atualizada: ${estado.jogos.length} jogo(s).`);
    } catch (falha) {
      recado(falha.message, true);
    }
  });

  $("#btnAjustes").addEventListener("click", () => abrirGaveta("gavetaAjustes"));
  $("#btnTema").addEventListener("click", async () => {
    const tema = estado.config.tema === "escuro" ? "claro" : "escuro";
    try {
      await salvarConfig({ tema });
      recado(tema === "escuro" ? "Modo escuro ativado." : "Modo claro ativado.");
    } catch (falha) {
      recado(falha.message, true);
    }
  });
  $("#btnJogarSelecionado").addEventListener("click", () => {
    if (estado.jogoSelecionado) jogar(estado.jogoSelecionado);
  });
  $("#btnMultiplayerSelecionado").addEventListener("click", () => {
    const jogo = estado.jogoSelecionado;
    if (!jogo) return;
    if (soNoMesmoComputador(jogo)) abrirJuntoLocal(jogo);
    else abrirPartida(jogo);
  });
  $("#btnAbrirJuntoLocal").addEventListener("click", () => {
    $("#modalJuntoLocal").hidden = true;
    if (estado.jogoSelecionado) jogar(estado.jogoSelecionado);
  });
  $("#btnGerirSelecionado").addEventListener("click", () => {
    if (estado.jogoSelecionado) abrirGaveta_jogo(estado.jogoSelecionado);
  });
  $("#btnEscolherConsole").addEventListener("click", () => {
    if (estado.jogoSelecionado) abrirEscolhaConsole(estado.jogoSelecionado);
  });
  $("#btnAtualizarCapa").addEventListener("click", async () => {
    const jogo = estado.jogoSelecionado;
    if (!jogo) return;
    recado("Procurando capa…");
    try {
      await pedir("/api/capa/atualizar", "POST", { jogo_id: jogo.id });
      await carregarCatalogo();
      recado("Capa encontrada!");
    } catch (falha) {
      recado(falha.message, true);
    }
  });
  $("#campoEnviarCapa").addEventListener("change", async (evento) => {
    const jogo = estado.jogoSelecionado;
    const arquivo = evento.target.files[0];
    evento.target.value = "";
    if (!jogo || !arquivo) return;
    if (arquivo.size > 6 * 1024 * 1024) {
      recado("Imagem grande demais (limite de 6 MB).", true);
      return;
    }
    recado("Enviando capa…");
    try {
      const imagem = await new Promise((resolve, reject) => {
        const leitor = new FileReader();
        leitor.onerror = () => reject(new Error("Não consegui ler o arquivo."));
        leitor.onload = () => resolve(leitor.result);
        leitor.readAsDataURL(arquivo);
      });
      await pedir("/api/capa/enviar", "POST", { jogo_id: jogo.id, imagem });
      await carregarCatalogo();
      recado("Capa enviada!");
    } catch (falha) {
      recado(falha.message, true);
    }
  });
  $("#btnSalvarConsole").addEventListener("click", async () => {
    if (!jogoConsoleEditando) return;
    try {
      await pedir("/api/jogo/console", "POST", {
        jogo_id: jogoConsoleEditando.id,
        plataforma: $("#listaConsoleJogoModal").value,
      });
      $("#modalConsole").hidden = true;
      jogoConsoleEditando = null;
      recado("Console salvo. O jogo já pode ser aberto pelo emulador correto.");
      await carregarCatalogo();
    } catch (falha) {
      recado(falha.message, true);
    }
  });
  $("#btnAmigos").addEventListener("click", () => {
    abrirGaveta("gavetaAjustes");
    const aba = document.querySelector('#gavetaAjustes .aba[data-aba="rede"]');
    if (aba) aba.click();
  });
  $("#btnRecordes").addEventListener("click", () => {
    abrirGaveta("gavetaRecordes");
    carregarRanking();
  });
  $("#btnConquistas").addEventListener("click", () => {
    abrirGaveta("gavetaConquistas");
    carregarConquistas();
  });
  $("#btnAcervo").addEventListener("click", () => {
    abrirGaveta("gavetaAcervo");
    carregarAcervo();
  });
  $("#campoBuscaOnline").addEventListener("input", () => {
    clearTimeout(atrasoBiblioteca);
    atrasoBiblioteca = setTimeout(carregarBibliotecaOnline, 300);
  });
  $("#campoBuscaAcervo").addEventListener("input", () => {
    clearTimeout(atrasoAcervo);
    atrasoAcervo = setTimeout(carregarAcervo, 300);
  });
  $("#btnNovoAcervo").addEventListener("click", () => abrirEditorAcervo());
  $("#btnSalvarAcervo").addEventListener("click", async () => {
    const botao = $("#btnSalvarAcervo");
    const status = $("#acervoEditorStatus");
    botao.disabled = true;
    status.textContent = "Validando e salvando…";
    try {
      await pedir("/api/acervo/salvar", "POST", { item: lerEditorAcervo() });
      $("#modalAcervo").hidden = true;
      recado("Acervo salvo. O arquivo só será baixado quando você clicar em Instalar.");
      await carregarAcervo();
    } catch (falha) {
      status.textContent = falha.message;
      recado(falha.message, true);
    } finally {
      botao.disabled = false;
    }
  });

  $("#listaPerfis").addEventListener("click", async (evento) => {
    const botao = evento.target.closest(".perfil");
    if (!botao) return;
    try {
      await salvarConfig({ perfil_grafico: botao.dataset.perfil });
      desenharPerfis();
      desenharAvancado();
      $("#lidoDriver").textContent = estado.efetivas.video_driver;
      $("#hwMotor").textContent = estado.efetivas.video_driver;
      recado(`Agora está em ${estado.perfis[botao.dataset.perfil].rotulo}. ` +
             "Vale do próximo jogo em diante.");
    } catch (falha) {
      recado(falha.message, true);
    }
  });

  $("#btnRestaurar").addEventListener("click", async () => {
    try {
      await salvarConfig({ restaurar: true });
      desenharPerfis();
      desenharAvancado();
      $("#lidoDriver").textContent = estado.efetivas.video_driver;
      $("#hwMotor").textContent = estado.efetivas.video_driver;
      recado("Tudo voltou como era antes.");
    } catch (falha) {
      recado(falha.message, true);
    }
  });

  $("#btnAddCheat").addEventListener("click", adicionarCheat);
  $("#btnExportar").addEventListener("click", exportarPacote);
  $("#btnAbrirPartida").addEventListener("click", comecarPartida);

  $("#btnTestarPartida").addEventListener("click", async (evento) => {
    const endereco = $("#listaAmigosPartida").value;
    if (!endereco) {
      recado("Escolha uma partida encontrada na rede primeiro.", true);
      return;
    }
    evento.currentTarget.disabled = true;
    $("#resultadoTeste").textContent = "Testando…";
    try {
      const r = await pedir("/api/partida/testar", "POST",
        { endereco, titulo: estado.jogoDaPartida ? estado.jogoDaPartida.titulo : "" });
      const arquivo = r.arquivo === "igual" ? " · arquivo: o mesmo"
        : r.arquivo === "diferente" ? " · arquivo: DIFERENTE"
        : r.arquivo === "ele nao tem" ? " · ele não tem esse jogo" : "";
      $("#resultadoTeste").textContent =
        `ARENA dele: ${r.arena ? "responde" : "não responde"} · ` +
        `porta da partida: ${r.partida ? "aberta" : "fechada"}${arquivo}. ` +
        r.diagnostico;
    } catch (falha) {
      $("#resultadoTeste").textContent = falha.message;
    } finally {
      evento.currentTarget.disabled = false;
    }
  });

  $("#btnMapaPadrao").addEventListener("click", async () => {
    try {
      await pedir("/api/mapeamento/padrao", "POST",
        { jogador: $("#mapaJogador").value });
      await desenharMapa();
      recado("Mapeamento de fábrica do teclado aplicado.");
    } catch (falha) {
      recado(falha.message, true);
    }
  });

  $("#btnMapaAuto").addEventListener("click", async () => {
    try {
      await pedir("/api/mapeamento/padrao", "POST",
        { jogador: $("#mapaJogador").value, tipo: "controle" });
      await desenharMapa();
      recado("Pronto: o controle deste jogador voltou ao reconhecimento " +
             "automático. As teclas do teclado continuam como estavam.");
    } catch (falha) {
      recado(falha.message, true);
    }
  });

  $("#chaveDesempenho").addEventListener("click", async (evento) => {
    const botao = evento.currentTarget;
    const novo = botao.getAttribute("aria-pressed") !== "true";
    try {
      await salvarConfig({ modo_desempenho: novo });
      botao.setAttribute("aria-pressed", novo ? "true" : "false");
      recado(novo
        ? "Modo desempenho ligado. Vale no próximo jogo que você abrir."
        : "Modo desempenho desligado.");
    } catch (falha) {
      recado(falha.message, true);
    }
  });

  $("#chaveRede").addEventListener("click", async (evento) => {
    const botao = evento.currentTarget;
    const novo = botao.getAttribute("aria-pressed") !== "true";
    try {
      const resposta = await salvarConfig({ permitir_rede: novo });
      botao.setAttribute("aria-pressed", novo ? "true" : "false");
      // O servidor reabre sozinho com a escuta nova (rede_aplicada). Se por
      // algum motivo nao reabriu, ai sim precisa fechar e abrir o ARENA.
      const aplicou = resposta.rede_aplicada;
      $("#ajudaRede").textContent = novo
        ? "Ligado. Os colegas já podem te achar."
        : "Desligado, só este computador acessa.";
      recado(novo
        ? (aplicou ? "Ligado. Os colegas já podem te achar."
                   : "Ligado. Feche e abra o ARENA para valer.")
        : "Desligado. Só este computador acessa.");
    } catch (falha) {
      recado(falha.message, true);
    }
  });

  $("#chaveModesto").addEventListener("click", async (evento) => {
    const botao = evento.currentTarget;
    const novo = botao.getAttribute("aria-pressed") !== "true";
    try {
      await salvarConfig({ modo_modesto: novo });
      botao.setAttribute("aria-pressed", novo ? "true" : "false");
      recado(novo
        ? "Gráfico igual ao console original. Vale no próximo jogo."
        : "Voltou ao gráfico melhorado.");
    } catch (falha) {
      recado(falha.message, true);
    }
  });

  $("#perfilFotoArquivo").addEventListener("change", async (evento) => {
    const arquivo = evento.target.files[0];
    evento.target.value = "";
    if (!arquivo) return;
    if (arquivo.size > 2 * 1024 * 1024) {
      recado("Foto grande demais (limite de 2 MB).", true);
      return;
    }
    try {
      const imagem = await redimensionarFotoPerfil(arquivo);
      await pedir("/api/perfil/foto", "POST", { imagem });
      atualizarFotoPerfil(true);
      recado("Foto de perfil atualizada.");
    } catch (falha) {
      recado(falha.message, true);
    }
  });

  $("#btnRemoverFotoPerfil").addEventListener("click", async () => {
    try {
      await pedir("/api/perfil/foto", "POST", { remover: true });
      atualizarFotoPerfil(false);
      recado("Foto de perfil removida.");
    } catch (falha) {
      recado(falha.message, true);
    }
  });

  $("#chaveRpcn").addEventListener("click", async (evento) => {
    const botao = evento.currentTarget;
    const novo = botao.getAttribute("aria-pressed") !== "true";
    try {
      await salvarConfig({ rpcn_ativo: novo });
      botao.setAttribute("aria-pressed", novo ? "true" : "false");
      recado(novo
        ? "RPCN ligado. Precisa da conta já criada pela tela do RPCS3."
        : "RPCN desligado.");
    } catch (falha) {
      recado(falha.message, true);
    }
  });

  $("#listaPresetGrafico").addEventListener("change", async (evento) => {
    try {
      await salvarConfig({ preset_grafico_externo: evento.target.value });
      atualizarExplicaPreset();
      recado("Pronto. Vale no próximo jogo que você abrir pelo PCSX2, RPCS3 ou Xenia.");
    } catch (falha) {
      recado(falha.message, true);
    }
  });

  $("#listaMotorPs2").addEventListener("change", async (evento) => {
    try {
      await salvarConfig({ motor_ps2: evento.target.value });
      recado("Pronto. Vale no próximo jogo de PS2.");
    } catch (falha) {
      recado(falha.message, true);
    }
  });

  $("#chaveTravar").addEventListener("click", async (evento) => {
    const botao = evento.currentTarget;
    const novo = botao.getAttribute("aria-pressed") !== "true";
    try {
      await salvarConfig({ travar_teclas: novo });
      botao.setAttribute("aria-pressed", novo ? "true" : "false");
      recado(novo
        ? "Teclado preso no jogo. Para soltar e abrir o menu, aperte F9."
        : "Teclado solto. O Esc abre o menu normalmente.");
    } catch (falha) {
      recado(falha.message, true);
    }
  });

  $("#chaveUltra").addEventListener("click", async (evento) => {
    const botao = evento.currentTarget;
    const novo = botao.getAttribute("aria-pressed") !== "true";
    try {
      await salvarConfig({ ultra_desempenho: novo });
      botao.setAttribute("aria-pressed", novo ? "true" : "false");
      if (novo) $("#chaveDesempenho").setAttribute("aria-pressed", "true");
      recado(novo
        ? "Ultra desempenho ligado. Para sair de um jogo, use F10."
        : "Ultra desempenho desligado.");
    } catch (falha) {
      recado(falha.message, true);
    }
  });

  $("#btnMapaLimpar").addEventListener("click", async () => {
    try {
      await pedir("/api/mapeamento/limpar", "POST",
        { jogador: $("#mapaJogador").value });
      await desenharMapa();
      recado("Limpo. O RetroArch volta a mandar nesses botões.");
    } catch (falha) {
      recado(falha.message, true);
    }
  });

  $("#btnAbrirBios").addEventListener("click", async () => {
    try {
      const dados = await pedir("/api/bios/abrir", "POST",
        { plataforma: $("#listaBiosAbrir").value });
      recado(`Abrindo a tela inicial do ${dados.console} pelo ${dados.emulador}. ` +
             "O que você ajustar lá fica salvo.");
    } catch (falha) {
      recado(falha.message, true);
    }
  });

  $("#listaAmigosPartida").addEventListener("change", (evento) => {
    estado.partidaEscolhida = evento.target.value;
  });

  document.querySelector("#modalPartida .perfis")
    .addEventListener("click", (evento) => {
      const botao = evento.target.closest(".perfil");
      if (!botao) return;
      estado.papelDaPartida = botao.dataset.papel;
      for (const b of document.querySelectorAll("#modalPartida .perfil")) {
        b.classList.toggle("ativo", b === botao);
      }
      const entrando = estado.papelDaPartida !== "hospedar";
      $("#campoAmigoPartida").hidden = !entrando;
      $("#campoInternet").hidden = false;
      preencherAmigosPartida();
      vigiarPartidas(entrando);

      // O jogo especifico pode aceitar mais jogadores que o console em
      // geral (Multitap, ex.: Super Bomberman) -- por isso o numero vem
      // do PROPRIO jogo agora, nao so da plataforma.
      const maximo = estado.jogoDaPartida?.jogadores_max
        || (estado.porPlataforma[estado.jogoDaPartida?.plataforma] || {}).jogadores_max
        || 2;
      const mostrarJogador = estado.papelDaPartida === "entrar" && maximo > 2;
      $("#campoJogadorPartida").hidden = !mostrarJogador;
      if (mostrarJogador) {
        const opcoes = document.createDocumentFragment();
        for (let n = 2; n <= maximo; n++) {
          const item = document.createElement("option");
          item.value = String(n);
          item.textContent = `Jogador ${n}`;
          opcoes.append(item);
        }
        $("#listaJogadorPartida").replaceChildren(opcoes);
      }
    });

  $("#listaDriverControleTopo").addEventListener("change", async (evento) => {
    try {
      const escolhido = evento.target.value;
      await salvarConfig({ avancado: { input_joypad_driver: escolhido } });
      if (escolhido !== "dinput") {
        recado("Pronto. Vale no próximo jogo que você abrir.");
        return;
      }
      // No dinput, controle do tipo Xbox aparece duas vezes para o RetroArch
      // e os jogadores se embaralham — achado com 3 GameSir no Micro
      // Machines 2 (25/09/2026): 7 "controles" para 3 de verdade.
      const conectados = navigator.getGamepads ? [...navigator.getGamepads()] : [];
      const tipoXbox = conectados.some((pad) => pad && /xinput|xbox/i.test(pad.id));
      recado(tipoXbox
        ? "Atenção: tem um controle do tipo Xbox ligado. No dinput ele aparece " +
          "duas vezes e os jogadores se embaralham. Se não foi de propósito, " +
          "volte para xinput."
        : "Pronto: dinput. Se tiver algum controle do tipo Xbox (Xbox, GameSir " +
          "e parecidos), ele vai aparecer duas vezes e embaralhar os jogadores — " +
          "aí volte para xinput.", true);
    } catch (falha) {
      recado(falha.message, true);
    }
  });

  $("#btnAddAmigoCodigo").addEventListener("click", adicionarAmigoCodigo);
  $("#btnTestarAmigo").addEventListener("click", testarAmigo);
  $("#btnAddAmigo").addEventListener("click", adicionarAmigo);

  $("#btnRepararRuntime").addEventListener("click", async (evento) => {
    evento.currentTarget.disabled = true;
    try {
      const dados = await pedir("/api/reparar-runtime", "POST");
      recado(dados.copiadas.length
        ? `Pronto! ${dados.copiadas.length} arquivo(s) copiados. Já pode jogar.`
        : "Já estava tudo no lugar.");
      $("#blocoRuntime").hidden = true;
      aviso("");
    } catch (falha) {
      recado(falha.message, true);
    } finally {
      evento.currentTarget.disabled = false;
    }
  });

  $("#btnBarreiras").addEventListener("click", verificarBarreiras);

  $("#btnBackup").addEventListener("click", async () => {
    try {
      const dados = await pedir("/api/backup", "POST");
      recado(`Cópia guardada na pasta backup, em ${dados.pasta}`);
    } catch (falha) {
      recado(falha.message, true);
    }
  });

  $("#chaveInternet").addEventListener("click", (evento) => {
    const botao = evento.currentTarget;
    const novo = botao.getAttribute("aria-pressed") === "true" ? "false" : "true";
    botao.setAttribute("aria-pressed", novo);
  });

  $("#chaveApagarSaves").addEventListener("click", (evento) => {
    const botao = evento.currentTarget;
    botao.setAttribute("aria-pressed",
      botao.getAttribute("aria-pressed") === "true" ? "false" : "true");
  });

  $("#btnNovoPerfil").addEventListener("click", async (evento) => {
    const comSaves =
      $("#chaveApagarSaves").getAttribute("aria-pressed") === "true";

    const aviso = comSaves
      ? "Isto apaga seu apelido, recordes, amigos, configurações E TAMBÉM os " +
        "saves e cheats. Os jogos ficam. Tem certeza?"
      : "Isto apaga seu apelido, recordes, amigos e configurações. Seus saves " +
        "e os jogos ficam. Tem certeza?";

    if (!window.confirm(aviso)) return;

    evento.currentTarget.disabled = true;
    try {
      const dados = await pedir("/api/perfil/novo", "POST",
        { confirmar: "sim", apagar_saves: comSaves });
      recado(`Pronto. ${dados.apagados} arquivo(s) apagados. ` +
             `Seu código novo é ${dados.dispositivo_id}. Escreva seu apelido lá em cima.`);
      await carregarEstado();
      await carregarCatalogo();
      carregarRanking();
    } catch (falha) {
      recado(falha.message, true);
    } finally {
      evento.currentTarget.disabled = false;
    }
  });

  $("#btnMala").addEventListener("click", async (evento) => {
    evento.currentTarget.disabled = true;
    recado("Abrindo a mala…");
    try {
      const dados = await pedir("/api/mala", "POST", {});
      recado(`${dados.recebidos} recorde(s) recebidos. A mala segue com ` +
             `${dados.na_mala} registros de ${dados.maquinas} máquina(s).`);
      const novo = await pedir("/api/estado");
      mostrarPendentes(novo.pendentes);
      $("#malaSituacao").textContent = novo.mala.existe
        ? "mala presente" : "nenhuma mala aqui";
      carregarRanking();
    } catch (falha) {
      recado(falha.message, true);
    } finally {
      evento.currentTarget.disabled = false;
    }
  });

  $("#btnSincronizar").addEventListener("click", enviarRecordes);
  $("#btnEnviarAgora").addEventListener("click", enviarRecordes);


  async function salvarApelidoInicial() {
    const valor = $("#campoApelidoInicial").value.trim();
    if (!valor) { recado("Escolha um apelido para começar.", true); return; }
    await salvarConfig({ apelido: valor });
    $("#modalApelido").hidden = true;
    $("#perfilApelido").textContent = valor;
    recado(`Tudo certo, ${valor}!`);
  }
  $("#btnSalvarApelido").addEventListener("click", () =>
    salvarApelidoInicial().catch((falha) => recado(falha.message, true)));
  $("#campoApelidoInicial").addEventListener("keydown", (evento) => {
    if (evento.key === "Enter") salvarApelidoInicial();
  });

  // Abas das gavetas
  for (const grupo of document.querySelectorAll(".abas")) {
    grupo.addEventListener("click", (evento) => {
      const aba = evento.target.closest(".aba");
      if (!aba) return;
      const gaveta = grupo.closest(".gaveta");
      for (const outra of grupo.querySelectorAll(".aba")) {
        outra.classList.toggle("ativo", outra === aba);
      }
      for (const painel of gaveta.querySelectorAll(".aba-conteudo")) {
        painel.hidden = painel.dataset.painel !== aba.dataset.aba;
      }
    });
  }

  document.addEventListener("click", (evento) => {
    const fechar = evento.target.closest("[data-fechar]");
    if (fechar) document.getElementById(fechar.dataset.fechar).hidden = true;
  });

  document.addEventListener("keydown", (evento) => {
    if (evento.key !== "Escape") return;
    for (const painel of document.querySelectorAll(".gaveta, .modal")) {
      painel.hidden = true;
    }
  });

  $("#btnSalvarPontos").addEventListener("click", salvarPlacar);
  $("#campoPontos").addEventListener("keydown", (evento) => {
    if (evento.key === "Enter") salvarPlacar();
  });
}

// --------------------------------------------------------------------------
// Partida
// --------------------------------------------------------------------------

async function iniciar() {
  ligarEventos();
  try {
    await carregarEstado();
    await carregarCatalogo();
  } catch (falha) {
    aviso("O ARENA parou de responder. Feche tudo e abra o ARENA.bat de novo.");
  }
}

iniciar();
