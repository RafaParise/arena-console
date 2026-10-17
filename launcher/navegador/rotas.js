"use strict";
// --------------------------------------------------------------------------
// ARENA no navegador: o "servidor" que mora na propria pagina (item 12).
//
// A tela do ARENA (app.js) conversa com o servidor por pedidos /api/... .
// No Windows quem responde e' o Python (servidor\arena.py). No Chromebook
// nao ha Python: este arquivo responde os mesmos pedidos, com as mesmas
// respostas, a partir do banco do navegador (banco.js), da pasta do pen
// drive (pasta.js) e do que o servidor sabe (dados.js, gerado dele). A tela
// e' a mesma, sem uma linha a mais por causa do Chromebook; o que so existe
// no Windows (rede, emuladores de fora, Lossless Scaling...) a tela esconde.
//
// O pedido nao sai da pagina: o fetch de /api/ e' atendido aqui (fim deste
// arquivo). Endereco de fora (capas da internet, por exemplo) segue normal.
// --------------------------------------------------------------------------
window.ArenaRotas = (function () {
  const D = window.ARENA_DADOS;
  const POR_ID = new Map(D.consoles.map(function (p) { return [p.id, p]; }));
  const ORIGENS = { livres: "Acervo livre", turma: "Feito pela turma", pessoais: "Meus jogos",
                    vem_com: "Vem com o ARENA", navegador: "Guardado neste navegador" };
  const ESPACOS = 10;
  const SAVES = "retroarch/saves";
  const ESTADOS = "retroarch/states";
  const SISTEMA = "retroarch/system";
  const EXTENSOES_DE_SAVE = [".srm", ".sav", ".rtc", ".mcr", ".eep", ".fla", ".sra", ".nv"];
  // Medido em 17/10/2026 no Ryzen 5 5600G (Edge 155, tres aberturas): a
  // carga de medirVelocidade() fez uns 935 mil "instrucoes" por milissegundo,
  // e o Python dele mede 2,38 vezes o notebook-alvo (servidor\hardware.py).
  // Dai sai quanto o notebook-alvo faria aqui: 935.000 / 2,38. E' a mesma
  // regua do Windows -- e, como la, provisoria ate a medida no Celeron.
  const INSTRUCOES_DO_ALVO_POR_MS = 393000;
  const DIAS_DA_MEDIDA = 7;
  // O emulador em WebAssembly roda mais devagar que o do Windows (medido no
  // espinho de 17/10/2026: o PS1 cai antes no navegador). A regua do custo
  // de cada console (arena.VELOCIDADE_POR_CUSTO) pede esta folga a mais.
  const FOLGA_DO_NAVEGADOR = 2.0;

  const E = {
    config: null,
    jogos: [],
    plataformas: null,
    maquina: null,
    partida: { ativo: false },
    problema: null,
    placar: [],
    manifesto: null,
    iniciado: null,
    soNaMemoria: false,
  };

  function falha(texto, status) {
    const erro = new Error(texto);
    erro.status = status || 400;
    return erro;
  }

  function copia(valor) { return JSON.parse(JSON.stringify(valor)); }

  function nucleos() { return (window.ARENA_NUCLEOS_LISTA || {}).nucleos || {}; }

  function temNucleo(p) { return !!(p && p.core_navegador && nucleos()[p.core_navegador]); }

  function extensao(nome) {
    const corte = String(nome).lastIndexOf(".");
    return corte < 0 ? "" : String(nome).slice(corte).toLowerCase();
  }

  function semExtensao(nome) {
    const corte = String(nome).lastIndexOf(".");
    return corte <= 0 ? String(nome) : String(nome).slice(0, corte);
  }

  function nomeDoArquivo(caminho) { return ArenaPasta.normalizar(caminho).split("/").pop(); }

  function pastaDoArquivo(caminho) {
    const partes = ArenaPasta.normalizar(caminho).split("/");
    partes.pop();
    return partes.join("/");
  }

  // ------------------------------------------------------------------------
  // O mesmo limpar_titulo do servidor\indexador.py (titulo legivel do nome).
  // ------------------------------------------------------------------------
  const LIGACOES = new Set(["de", "da", "do", "dos", "das", "e", "the", "of", "in", "a", "o"]);

  function limparTitulo(nome) {
    let titulo = semExtensao(nome).replace(/\([^)]*\)/g, " ").replace(/\[[^\]]*\]/g, " ");
    titulo = titulo.replace(/[_.\-]/g, " ").replace(/\s+/g, " ").trim();
    if (!titulo) return "Sem titulo";
    return titulo.split(" ").map(function (palavra, i) {
      return i > 0 && LIGACOES.has(palavra.toLowerCase()) ? palavra.toLowerCase()
        : palavra.slice(0, 1).toUpperCase() + palavra.slice(1);
    }).join(" ");
  }

  // 4 casas, como o manifesto do Windows (um jogo de CHIP-8 tem 3 KB).
  function emMegabytes(bytes) { return Math.round((bytes || 0) / 1048576 * 10000) / 10000; }

  function ordenacao(texto) {
    return String(texto).normalize("NFKD").replace(/[̀-ͯ]/g, "").toLowerCase();
  }

  function limparApelido(texto) {
    const limpo = Array.from(String(texto || "")).filter(function (c) {
      return c >= " " && c !== "\u007f" && c !== '"' && c !== "\\";
    }).join("");
    return limpo.split(/\s+/).filter(Boolean).join(" ").slice(0, 24);
  }

  function novoId() {
    const bytes = new Uint8Array(8);
    crypto.getRandomValues(bytes);
    return Array.from(bytes, function (b) { return b.toString(16).padStart(2, "0"); }).join("");
  }

  // ------------------------------------------------------------------------
  // A maquina: o que o navegador deixa saber (sem nome do processador).
  // ------------------------------------------------------------------------
  // Uma carga parecida com a de um emulador (le um byte, decide, faz conta,
  // grava): conta quantas "instrucoes" cabem em 1 ms. A primeira rodada so
  // aquece (o navegador compila o codigo enquanto ele roda); das outras, fica
  // a melhor, como o hardware.py: o numero diz do que o processador e' capaz.
  function medirVelocidade() {
    const memoria = new Uint8Array(65536);
    for (let i = 0; i < memoria.length; i++) memoria[i] = (i * 7 + 13) & 255;
    let melhor = 0;
    let a = 1, x = 0, y = 0, pc = 0;
    for (let rodada = 0; rodada < 6; rodada++) {
      let feitas = 0;
      const inicio = performance.now();
      while (performance.now() - inicio < 50) {
        for (let k = 0; k < 20000; k++) {
          const op = memoria[pc & 0xffff];
          switch (op & 7) {
            case 0: a = (a + memoria[(pc + 1) & 0xffff]) & 255; pc += 2; break;
            case 1: x = (x ^ a) & 255; pc += 1; break;
            case 2: memoria[((x << 8) | y) & 0xffff] = a; pc += 1; break;
            case 3: y = (y + 1) & 255; pc += 1; break;
            case 4: pc += (a & 1) ? 3 : 1; break;
            case 5: a = memoria[((a << 8) | x) & 0xffff]; pc += 1; break;
            case 6: pc = (pc + (a ^ x)) & 0xffff; break;
            default: a = (a * 3 + 1) & 255; pc += 1;
          }
        }
        feitas += 20000;
      }
      if (rodada > 0) melhor = Math.max(melhor, feitas / (performance.now() - inicio));
    }
    memoria[0] = a ^ x ^ y;          // o resultado e' usado: a conta nao some
    return Math.round(melhor);
  }

  function placaDeVideo() {
    let gl = null;
    try {
      gl = document.createElement("canvas").getContext("webgl2") ||
           document.createElement("canvas").getContext("webgl");
      if (!gl) return { nome: "sem WebGL", webgl2: false };
      const info = gl.getExtension("WEBGL_debug_renderer_info");
      const nome = info ? gl.getParameter(info.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER);
      return { nome: String(nome || "desconhecida"), webgl2: typeof WebGL2RenderingContext !== "undefined" &&
               gl instanceof WebGL2RenderingContext };
    } catch (erro) {
      return { nome: "desconhecida", webgl2: false };
    } finally {
      // So para ler o nome: a placa devolve a memoria na hora (o jogo abre
      // o dele, no quadro do jogo).
      const fim = gl && gl.getExtension("WEBGL_lose_context");
      if (fim) fim.loseContext();
    }
  }

  async function sistema() {
    const ua = navigator.userAgent;
    const dados = { cromebook: /\bCrOS\b/.test(ua), plataforma: "", versao: "", arquitetura: "", navegador: "" };
    try {
      if (navigator.userAgentData) {
        const alto = await navigator.userAgentData.getHighEntropyValues(
          ["platformVersion", "architecture", "bitness", "fullVersionList"]);
        dados.plataforma = navigator.userAgentData.platform || "";
        dados.versao = alto.platformVersion || "";
        dados.arquitetura = (alto.architecture || "") + (alto.bitness ? " " + alto.bitness + " bits" : "");
        const marca = (alto.fullVersionList || []).find(function (m) { return !/Not.?A.?Brand|Chromium/i.test(m.brand); });
        if (marca) dados.navegador = marca.brand + " " + marca.version;
        if (/Chrome ?OS/i.test(dados.plataforma)) dados.cromebook = true;
      }
    } catch (erro) { /* navegador sem esses dados: fica o userAgent */ }
    if (!dados.navegador) {
      const m = ua.match(/(Firefox|Edg|OPR|Chrome)\/([\d.]+)/);
      if (m) dados.navegador = ({ Edg: "Microsoft Edge", OPR: "Opera" }[m[1]] || m[1]) + " " + m[2];
    }
    if (!dados.plataforma) {
      dados.plataforma = /CrOS/.test(ua) ? "Chrome OS" : /Windows/.test(ua) ? "Windows" : /Android/.test(ua) ? "Android"
        : /Linux/.test(ua) ? "Linux" : /Mac/.test(ua) ? "macOS" : "outro";
    }
    return dados;
  }

  // A medida fica guardada por uma semana (medir toda vez atrasaria a
  // abertura do ARENA); o "Testar este Chromebook" sempre mede de novo.
  async function velocidadeGuardada(medirDeNovo) {
    const agora = Date.now();
    let guardada = null;
    try { guardada = await ArenaBanco.ler("coisas", "velocidade"); } catch (erro) { guardada = null; }
    if (!medirDeNovo && guardada && guardada.navegador === navigator.userAgent &&
        agora - guardada.quando < DIAS_DA_MEDIDA * 86400000) return guardada.instrucoes;
    const instrucoes = medirVelocidade();
    try { await ArenaBanco.gravar("coisas", "velocidade", { instrucoes: instrucoes, quando: agora, navegador: navigator.userAgent }); }
    catch (erro) { /* sem banco: mede de novo na proxima */ }
    return instrucoes;
  }

  async function medirMaquina(medirDeNovo) {
    const so = await sistema();
    const instrucoes = await velocidadeGuardada(medirDeNovo);
    const relativa = Math.round(instrucoes / calibracao() * 100) / 100;
    const placa = placaDeVideo();
    let espaco = null;
    try { espaco = await navigator.storage.estimate(); } catch (erro) { espaco = null; }
    const nucleosLogicos = navigator.hardwareConcurrency || 2;
    const memoria = navigator.deviceMemory || null;
    const nomeSistema = (so.cromebook ? "ChromeOS" : so.plataforma) + (so.versao ? " " + so.versao : "") +
      (so.navegador ? " · " + so.navegador : "");
    return {
      cpu: "Processador de " + nucleosLogicos + " núcleos" + (so.arquitetura ? " (" + so.arquitetura + ")" : ""),
      nucleos: nucleosLogicos,
      ram_total_gb: memoria || 0,
      ram_livre_gb: 0,
      ram_aproximada: true,
      disco: {
        descricao: "o navegador guarda os saves; os jogos ficam no pen drive",
        unidade: "navegador",
        livre_gb: espaco && espaco.quota ? Math.round((espaco.quota - (espaco.usage || 0)) / 1073741824 * 10) / 10 : 0,
        total_gb: espaco && espaco.quota ? Math.round(espaco.quota / 1073741824 * 10) / 10 : 0,
        escrita_mbs: 0,
        cabem_states: 0,
        classe: "navegador",
      },
      sistema: nomeSistema,
      sistema_detalhe: so,
      driver_video: placa.webgl2 ? "WebGL 2" : "WebGL",
      gpu: { nome: placa.nome, integrada: true },
      runtime_ok: true,
      velocidade: { relativa_ao_alvo: relativa, instrucoes_por_ms: instrucoes, referencia_provisoria: true },
      instrucoes: {},
      perfil_maquina: relativa < 0.8 ? "leve" : relativa < 1.6 ? "medio" : "forte",
      removivel: true,
      no_navegador: true,
    };
  }

  // ------------------------------------------------------------------------
  // A etiqueta de cada console nesta maquina (arena.classificar_plataforma):
  // a mesma regua, com a folga do WebAssembly.
  // ------------------------------------------------------------------------
  function etiqueta(chave, detalhe) {
    const base = D.etiquetas[chave] || D.etiquetas.ajustes;
    return { chave: chave, rotulo: base.rotulo, cor: base.cor, detalhe: detalhe || base.detalhe };
  }

  function classificar(p) {
    if (!p.core_navegador) {
      return etiqueta("nao_abre", "Este console só roda no ARENA do Windows: o Chromebook não tem o emulador dele.");
    }
    const velocidade = (((E.maquina || {}).velocidade) || {}).relativa_ao_alvo;
    if (typeof velocidade !== "number") return etiqueta("ajustes");
    const custo = Math.max(1, Math.min(5, parseInt(p.custo || 3, 10)));
    const regua = (p.requisitos || {}).velocidade || D.velocidade_por_custo[String(custo)];
    const efetiva = velocidade / FOLGA_DO_NAVEGADOR;
    if (efetiva >= regua[1]) return etiqueta("bem");
    if (efetiva >= regua[0]) return etiqueta("ajustes");
    return etiqueta("pesado", "Este Chromebook está abaixo do que este console pede no navegador. Dá para tentar: " +
      "se travar, os jogos dele rodam melhor no ARENA do Windows.");
  }

  // ------------------------------------------------------------------------
  // A configuracao (a mesma do dados\config.json, guardada no banco).
  // ------------------------------------------------------------------------
  async function carregarConfig() {
    const config = copia(D.config_padrao);
    let salvo = null;
    try { salvo = await ArenaBanco.ler("coisas", "config"); } catch (erro) { salvo = null; }
    if (salvo && typeof salvo === "object") {
      for (const chave of Object.keys(config)) {
        if (chave in salvo) config[chave] = salvo[chave];
      }
    }
    if (!config.dispositivo_id) config.dispositivo_id = novoId();
    return config;
  }

  async function guardarConfig() {
    try { await ArenaBanco.gravar("coisas", "config", E.config); } catch (erro) { /* sem banco: vale nesta aba */ }
  }

  // ------------------------------------------------------------------------
  // A lista de jogos
  // ------------------------------------------------------------------------
  function carregarScript(endereco) {
    return new Promise(function (pronto) {
      const script = document.createElement("script");
      script.src = endereco;
      script.onload = function () { pronto(true); };
      script.onerror = function () { script.remove(); pronto(false); };
      document.head.appendChild(script);
    });
  }

  // O dados\manifesto.js que o ARENA do Windows grava ao lado do
  // manifesto.json (servidor\indexador.py): a pagina aberta do pen drive o
  // le sem pedir permissao nenhuma.
  async function manifestoDoWindows() {
    if (location.protocol !== "file:") return null;
    if (!window.ARENA_MANIFESTO) await carregarScript("../dados/manifesto.js");
    const m = window.ARENA_MANIFESTO;
    return m && Array.isArray(m.jogos) ? m : null;
  }

  async function lerManifesto() {
    const pasta = ArenaPasta.situacao();
    if (pasta.tem && !pasta.precisa_permissao) {
      const texto = await ArenaPasta.lerTexto("dados/manifesto.json");
      if (texto) {
        try {
          const m = JSON.parse(texto);
          if (m && Array.isArray(m.jogos)) return m;
        } catch (erro) { /* manifesto cortado (pen drive arrancado): refaz abaixo */ }
      }
      return indexarAqui();
    }
    return manifestoDoWindows();
  }

  // Sem o manifesto do Windows (pen drive montado so no Chromebook): a lista
  // feita aqui, pela pasta de cada console e pela extensao -- o basico do
  // servidor\indexador.py. No Windows, o indexador completo refaz tudo.
  const BIOS_NA_PASTA = /^(neogeo|pgm|naomi|naomi2|awbios|stvbios|skns|cpzn1|cpzn2|nss|playch10|megatech|megaplay|decocass|qsound)([ ._-].*)?\.(zip|7z)$/i;
  const IGNORAR = new Set(["leia.txt", "leia-me.txt", "_console.txt", "readme.txt", "licenca.txt", "license.txt",
                           "thumbs.db", "desktop.ini", ".gitkeep"]);

  async function indexarAqui() {
    const porPasta = new Map();
    for (const p of D.consoles) {
      if (p.pasta) porPasta.set(p.pasta.toLowerCase(), p);
      for (const apelido of p.apelidos || []) if (!porPasta.has(apelido.toLowerCase())) porPasta.set(apelido.toLowerCase(), p);
    }
    const jogos = [];
    for (const origem of ["livres", "turma", "pessoais"]) {
      for (const item of await ArenaPasta.listar("jogos/" + origem)) {
        const p = item.pasta ? porPasta.get(item.nome.toLowerCase()) : null;
        if (p) await varrer("jogos/" + origem + "/" + item.nome, p, origem, jogos, 0);
      }
    }
    jogos.sort(function (a, b) {
      return a.plataforma_nome.localeCompare(b.plataforma_nome, "pt-BR") || a.ordenacao.localeCompare(b.ordenacao, "pt-BR");
    });
    return { jogos: jogos, total: jogos.length, feito_no_navegador: true };
  }

  let _extensoes = null;
  function extensoesConhecidas() {
    if (!_extensoes) {
      _extensoes = new Set();
      for (const p of D.consoles) for (const e of p.extensoes || []) _extensoes.add(e.toLowerCase());
    }
    return _extensoes;
  }

  async function referenciados(pasta, nome) {
    const texto = await ArenaPasta.lerTexto(pasta + "/" + nome);
    if (!texto) return [];
    if (/\.m3u$/i.test(nome)) {
      return texto.split(/\r?\n/).map(function (l) { return l.trim(); }).filter(function (l) { return l && !l.startsWith("#"); });
    }
    const achados = [];
    const re = /^\s*FILE\s+"?([^"\r\n]+?)"?\s+\w+\s*$/gim;
    let m;
    while ((m = re.exec(texto))) achados.push(m[1]);
    return achados;
  }

  async function varrer(pasta, p, origem, jogos, nivel) {
    const itens = await ArenaPasta.listar(pasta);
    const escondidos = new Set();
    for (const item of itens) {
      if (!item.pasta && /\.(cue|m3u)$/i.test(item.nome)) {
        for (const ref of await referenciados(pasta, item.nome)) escondidos.add(nomeDoArquivo(ref).toLowerCase());
      }
    }
    // Como no indexador do Windows: a extensao precisa ser de algum console,
    // e a pasta decide qual (o .PRG na pasta do Atari ST e' do Atari ST).
    const aceitas = extensoesConhecidas();
    for (const item of itens) {
      if (item.pasta) {
        if (nivel < 2) await varrer(pasta + "/" + item.nome, p, origem, jogos, nivel + 1);
        continue;
      }
      const minusculo = item.nome.toLowerCase();
      if (IGNORAR.has(minusculo) || escondidos.has(minusculo) || BIOS_NA_PASTA.test(item.nome)) continue;
      if (!aceitas.has(extensao(item.nome))) continue;
      const caminho = pasta + "/" + item.nome;
      const titulo = limparTitulo(item.nome);
      jogos.push({
        id: caminho.toLowerCase(), titulo: titulo, ordenacao: ordenacao(titulo), plataforma: p.id,
        plataforma_nome: p.nome, arquivo: caminho, origem: origem, origem_rotulo: ORIGENS[origem],
        pede_placar: !!p.pede_placar, jogadores_do_jogo: p.jogadores_max || 2, jogadores_max: p.jogadores_max || 2,
        rede_propria: false, motivo_jogadores: "", tamanho_mb: null, ambiguo: false, discorda: null,
        discorda_nome: null, corrigido: false, sugestao: null,
        capas: ["retroarch/thumbnails/" + p.id + "/Named_Boxarts/" + semExtensao(item.nome) + ".png"],
        romset: null, nome_banco: null, avisos: [],
      });
    }
  }

  // Os jogos livres que vem dentro do ARENA do Chromebook (navegador\livres.js).
  function jogosQueVemJunto() {
    return (window.ARENA_LIVRES || []).map(function (j) {
      const p = POR_ID.get(j.plataforma) || {};
      return {
        id: "vem-com/" + j.arquivo, titulo: j.titulo, ordenacao: ordenacao(j.titulo), plataforma: j.plataforma,
        plataforma_nome: p.nome || j.plataforma, arquivo: "vem-com/" + j.arquivo, origem: "vem_com",
        origem_rotulo: ORIGENS.vem_com, pede_placar: false, jogadores_do_jogo: 1, jogadores_max: p.jogadores_max || 2,
        rede_propria: false, motivo_jogadores: "", tamanho_mb: emMegabytes(j.bytes), ambiguo: false,
        discorda: null, discorda_nome: null, corrigido: false, sugestao: null, capas: [], romset: null,
        nome_banco: null, avisos: [], licenca: j.licenca,
      };
    });
  }

  // Jogos guardados dentro do navegador (Ajustes -> Máquina -> Guardar um
  // jogo neste navegador): para o Chromebook sem pen drive.
  async function jogosDoNavegador() {
    let itens = [];
    try { itens = await ArenaBanco.listar("jogos", "meus/"); } catch (erro) { itens = []; }
    return itens.map(function (par) {
      const j = par[1];
      const p = POR_ID.get(j.plataforma) || {};
      const titulo = limparTitulo(j.nome);
      return {
        id: par[0], titulo: titulo, ordenacao: ordenacao(titulo), plataforma: j.plataforma,
        plataforma_nome: p.nome || j.plataforma, arquivo: par[0], origem: "navegador", origem_rotulo: ORIGENS.navegador,
        pede_placar: !!p.pede_placar, jogadores_do_jogo: p.jogadores_max || 2, jogadores_max: p.jogadores_max || 2,
        rede_propria: false, motivo_jogadores: "", tamanho_mb: emMegabytes(j.bytes),
        ambiguo: false, discorda: null, discorda_nome: null, corrigido: false, sugestao: null, capas: [],
        romset: null, nome_banco: null, avisos: [],
      };
    });
  }

  async function montarLista() {
    E.manifesto = await lerManifesto();
    const doPen = [];
    for (const j of (E.manifesto && E.manifesto.jogos) || []) {
      if (POR_ID.has(j.plataforma) || j.plataforma === "indefinido") doPen.push(j);
    }
    // O mesmo jogo no pen drive e entre os que vem junto aparece uma vez so:
    // o do pen drive quando a pasta esta liberada (o save vai para la); antes
    // disso, o que vem junto (abre sem pedir nada).
    const junto = jogosQueVemJunto();
    const chave = function (j) { return j.plataforma + "/" + nomeDoArquivo(j.arquivo).toLowerCase(); };
    const pasta = ArenaPasta.situacao();
    let lista;
    if (pasta.tem && !pasta.precisa_permissao) {
      const noPen = new Set(doPen.map(chave));
      lista = doPen.concat(junto.filter(function (j) { return !noPen.has(chave(j)); }));
    } else {
      const nosQueVem = new Set(junto.map(chave));
      lista = doPen.filter(function (j) { return !nosQueVem.has(chave(j)); }).concat(junto);
    }
    E.jogos = lista.concat(await jogosDoNavegador());
    E.plataformas = null;
  }

  function capaUrls(jogo) {
    // A tela pede "/api/capa?arquivo=..."; no navegador a imagem sai direto
    // do pen drive (servidor.js troca o endereco do <img>).
    return (jogo.capas || []).map(function (c) { return "/api/capa?arquivo=" + encodeURIComponent(c); });
  }

  // ------------------------------------------------------------------------
  // BIOS: o que o console pede, procurado no pen drive
  // ------------------------------------------------------------------------
  async function biosDoConsole(p) {
    const achadas = [];
    const faltam = [];
    for (const b of D.bios[p.id] || []) {
      let arquivo = null;
      for (const nome of [b.destino].concat(b.aceitos || [])) {
        arquivo = await ArenaPasta.arquivo(SISTEMA + "/" + nome);
        if (arquivo) break;
      }
      if (!arquivo && b.pasta) {
        // Ainda na prateleira BIOS\<console>, sem ter passado pelo Windows.
        for (const sub of await ArenaPasta.listar("BIOS/" + b.pasta)) {
          const caminho = "BIOS/" + b.pasta + "/" + sub.nome;
          if (!sub.pasta && (b.aceitos || []).includes(sub.nome.toLowerCase())) arquivo = await ArenaPasta.arquivo(caminho);
          if (!arquivo && sub.pasta) {
            for (const dentro of await ArenaPasta.listar(caminho)) {
              if (!dentro.pasta && (b.aceitos || []).includes(dentro.nome.toLowerCase())) {
                arquivo = await ArenaPasta.arquivo(caminho + "/" + dentro.nome);
              }
              if (arquivo) break;
            }
          }
          if (arquivo) break;
        }
      }
      if (arquivo) achadas.push({ caminho: b.destino, arquivo: arquivo, grupo: b.grupo, id: b.id });
      else faltam.push(b);
    }
    // "uma" (o PS1): basta uma das regioes.
    const grupos = new Set(achadas.map(function (a) { return a.grupo; }).filter(Boolean));
    const faltaDeVerdade = faltam.filter(function (b) { return b.nivel === "precisa" && !(b.grupo && grupos.has(b.grupo)); });
    return { achadas: achadas, faltam: faltaDeVerdade };
  }

  // ------------------------------------------------------------------------
  // Saves e estados: o banco do navegador e o pen drive (o mais novo vale)
  // ------------------------------------------------------------------------
  function pastaDoNucleo(p) { return D.pasta_do_nucleo[p.core_navegador] || p.core_navegador; }

  async function guardadosDoJogo(p, base) {
    const pasta = pastaDoNucleo(p);
    const achados = new Map();         // caminho relativo ("saves/FCEUmm/x.srm") -> {dados, quando}
    const prefixos = ["saves/" + pasta + "/" + base + ".", "states/" + pasta + "/" + base + "."];
    for (const prefixo of prefixos) {
      let itens = [];
      try { itens = await ArenaBanco.listar("guardados", prefixo); } catch (erro) { itens = []; }
      for (const [caminho, valor] of itens) achados.set(caminho, { dados: valor.dados, quando: valor.quando || 0 });
    }
    const situacao = ArenaPasta.situacao();
    if (situacao.tem && !situacao.precisa_permissao) {
      for (const [raiz, tipo] of [[SAVES, "saves"], [ESTADOS, "states"]]) {
        const pastas = [pasta].concat(D.pastas_parecidas[pasta] || []);
        for (let i = 0; i < pastas.length; i++) {
          for (const item of await ArenaPasta.listar(raiz + "/" + pastas[i])) {
            if (item.pasta || !item.nome.toLowerCase().startsWith(base.toLowerCase() + ".")) continue;
            const caminho = tipo + "/" + pasta + "/" + base + item.nome.slice(base.length);
            // Pasta parecida (o save do SwanStation para o PCSX ReARMed):
            // so quando o nucleo do navegador ainda nao tem o dele.
            if (i > 0 && achados.has(caminho)) continue;
            const f = await ArenaPasta.arquivo(raiz + "/" + pastas[i] + "/" + item.nome);
            if (!f) continue;
            const antes = achados.get(caminho);
            if (!antes || (i === 0 && f.lastModified > antes.quando)) {
              achados.set(caminho, { dados: await f.arrayBuffer(), quando: f.lastModified });
            }
          }
        }
      }
    }
    return Array.from(achados.entries()).map(function (par) { return { caminho: par[0], dados: par[1].dados }; });
  }

  // O quadro do jogo mandou saves/estados novos: guarda no banco e, com a
  // pasta liberada, no pen drive (retroarch\saves, o mesmo do Windows).
  async function guardar(arquivos) {
    for (const a of arquivos) {
      const caminho = ArenaPasta.normalizar(a.caminho);
      if (!/^(saves|states)\//.test(caminho) || caminho.includes("..")) continue;
      try { await ArenaBanco.gravar("guardados", caminho, { dados: a.dados, quando: Date.now() }); }
      catch (erro) { E.problema = { texto: "O navegador não deixou guardar o save: " + erro.message }; }
      try { await ArenaPasta.gravar("retroarch/" + caminho, a.dados); }
      catch (erro) { /* pen drive saiu: o save continua no navegador */ }
    }
  }

  function sufixoDoEspaco(numero) { return numero === 0 ? ".state" : ".state" + numero; }

  async function listarEstados(jogo) {
    const p = POR_ID.get(jogo.plataforma);
    const espacos = [];
    if (!p || !p.core_navegador) {
      for (let n = 0; n < ESPACOS; n++) espacos.push({ espaco: n, existe: false, quando: null, tamanho_kb: null });
      return { espacos: espacos, tem_save: false };
    }
    const base = semExtensao(nomeDoArquivo(jogo.arquivo));
    const guardados = await guardadosDoJogo(p, base);
    const pasta = pastaDoNucleo(p);
    const porCaminho = new Map(guardados.map(function (g) { return [g.caminho, g]; }));
    for (let n = 0; n < ESPACOS; n++) {
      const g = porCaminho.get("states/" + pasta + "/" + base + sufixoDoEspaco(n));
      espacos.push({ espaco: n, existe: !!g, quando: g ? "guardado" : null,
                     tamanho_kb: g ? Math.round(g.dados.byteLength / 102.4) / 10 : null });
    }
    const temSave = guardados.some(function (g) {
      return g.caminho.startsWith("saves/") && EXTENSOES_DE_SAVE.includes(extensao(g.caminho));
    });
    return { espacos: espacos, tem_save: temSave };
  }

  // ------------------------------------------------------------------------
  // Abrir o jogo
  // ------------------------------------------------------------------------
  async function bytesDe(caminho) {
    const f = await ArenaPasta.arquivo(caminho);
    return f ? { nome: f.name, dados: await f.arrayBuffer() } : null;
  }

  function deBase64(texto) {
    if (Uint8Array.fromBase64) return Uint8Array.fromBase64(texto).buffer;
    const binario = atob(texto);
    const bytes = new Uint8Array(binario.length);
    for (let i = 0; i < binario.length; i++) bytes[i] = binario.charCodeAt(i);
    return bytes.buffer;
  }

  async function arquivosDoJogo(jogo) {
    if (jogo.origem === "vem_com") {
      const livre = (window.ARENA_LIVRES || []).find(function (j) { return "vem-com/" + j.arquivo === jogo.arquivo; });
      if (!livre) throw falha("Este jogo livre não veio nesta cópia do ARENA.");
      return { principal: nomeDoArquivo(livre.arquivo), arquivos: [{ nome: nomeDoArquivo(livre.arquivo), dados: deBase64(livre.dados) }] };
    }
    if (jogo.origem === "navegador") {
      const guardado = await ArenaBanco.ler("jogos", jogo.arquivo);
      if (!guardado) throw falha("Este jogo não está mais guardado neste navegador.");
      return { principal: guardado.nome, arquivos: [{ nome: guardado.nome, dados: guardado.dados.slice(0) }] };
    }
    const pasta = ArenaPasta.situacao();
    if (!pasta.tem || pasta.precisa_permissao) {
      throw falha(pasta.tem ? "O Chrome pede para confirmar o acesso à pasta do ARENA: clique em Permitir, no alto da lista."
        : "Para abrir os jogos do pen drive, escolha a pasta do ARENA uma vez (botão no alto da lista).", 409);
    }
    const arquivos = [];
    const vistos = new Set();
    async function pegar(caminho) {
      const chave = ArenaPasta.normalizar(caminho).toLowerCase();
      if (vistos.has(chave)) return;
      vistos.add(chave);
      const item = await bytesDe(caminho);
      if (!item) throw falha("Não achei " + nomeDoArquivo(caminho) + " no pen drive. Ele pode ter sido movido: clique em Atualizar lista.");
      arquivos.push(item);
      // .cue e .m3u levam junto os arquivos que eles citam (as trilhas).
      if (/\.(cue|m3u)$/i.test(caminho)) {
        for (const ref of await referenciados(pastaDoArquivo(caminho), nomeDoArquivo(caminho))) {
          await pegar(pastaDoArquivo(caminho) + "/" + ArenaPasta.normalizar(ref));
        }
      }
    }
    const discos = jogo.discos && jogo.discos.length > 1 ? jogo.discos : [jogo.arquivo];
    for (const disco of discos) await pegar(disco);
    let principal = nomeDoArquivo(jogo.arquivo);
    if (discos.length > 1) {
      // Varios discos: a lista .m3u, o jeito do RetroArch de trocar de disco
      // sem sair (Esc -> Controle de disco), como no Windows.
      principal = semExtensao(nomeDoArquivo(jogo.arquivo)) + ".m3u";
      const lista = discos.map(nomeDoArquivo).join("\n") + "\n";
      arquivos.push({ nome: principal, dados: new TextEncoder().encode(lista).buffer });
    }
    // O fliperama do Neo Geo procura a BIOS (neogeo.zip) ao lado do jogo.
    const p = POR_ID.get(jogo.plataforma) || {};
    if (p.id === "neogeo") {
      const bios = await bytesDe(pastaDoArquivo(jogo.arquivo) + "/neogeo.zip");
      if (bios && !arquivos.some(function (a) { return a.nome.toLowerCase() === "neogeo.zip"; })) arquivos.push(bios);
    }
    return { principal: principal, arquivos: arquivos };
  }

  function linhaCfg(chave, valor) {
    return chave + ' = "' + String(valor).replace(/"/g, "") + '"';
  }

  function montarConfiguracao(p) {
    const opcoes = Object.assign({}, D.base_retroarch);
    // Em todo jogo: o menu do Esc em portugues, as teclas do ARENA, a
    // gravacao e a transmissao desligadas (privacidade dos alunos).
    Object.assign(opcoes, {
      video_vsync: "true",
      video_smooth: "false",
      video_scale_integer: "false",
      video_aspect_ratio_auto: "true",
      audio_latency: "96",
      audio_sync: "true",
      menu_driver: "rgui",
      pause_nonactive: "false",
      log_verbosity: "true",
      frontend_log_level: "1",
      savestate_file_compression: "true",
      sort_savefiles_enable: "true",
      sort_savestates_enable: "true",
      notification_show_autoconfig: "false",
      input_autodetect_enable: "true",
    });
    Object.assign(opcoes, p.opcoes_retroarch || {});
    return Object.keys(opcoes).map(function (chave) { return linhaCfg(chave, opcoes[chave]); }).join("\n") + "\n";
  }

  function notaDaMaquina() {
    const v = (((E.maquina || {}).velocidade) || {}).relativa_ao_alvo;
    if (typeof v !== "number") return 2;
    const efetiva = v / FOLGA_DO_NAVEGADOR;
    return efetiva >= 2 ? 4 : efetiva >= 1.2 ? 3 : efetiva >= 0.6 ? 2 : 1;
  }

  function montarOpcoes(p) {
    const tabela = (D.opcoes_nucleo[p.core_navegador] || {})[String(notaDaMaquina())] || {};
    return Object.keys(tabela).map(function (chave) { return linhaCfg(chave, tabela[chave]); }).join("\n") + "\n";
  }

  async function jogar(corpo) {
    const jogo = E.jogos.find(function (j) { return j.id === corpo.jogo_id; });
    if (!jogo) throw falha("Jogo não encontrado. Ele pode ter sido movido ou apagado. Clique em Atualizar lista e tente de novo.", 404);
    const p = POR_ID.get(jogo.plataforma);
    if (!p || !p.core_navegador) {
      throw falha((p ? p.nome : "Este console") + " só roda no ARENA do Windows: o Chromebook não tem o emulador dele.");
    }
    if (!temNucleo(p)) {
      throw falha("Falta o núcleo do " + p.nome + " nesta cópia do ARENA (launcher\\navegador\\nucleos).");
    }
    if (ArenaPartida.aberto()) throw falha("Já tem um jogo aberto. Feche ele (F10) antes de abrir outro.", 409);
    ArenaPartida.preparar(jogo.titulo);            // ainda no clique: a tela cheia so vem assim
    try {
      const pedido = await arquivosDoJogo(jogo);
      const bios = await biosDoConsole(p);
      // O Neo Geo: o ARENA do Windows guarda o neogeo.zip na pasta do jogo
      // (onde o FBNeo procura), e ele ja veio junto com o jogo.
      const aoLado = new Set(pedido.arquivos.map(function (a) { return a.nome.toLowerCase(); }));
      bios.faltam = bios.faltam.filter(function (b) { return !aoLado.has(String(b.destino).toLowerCase()); });
      if (bios.faltam.length) {
        throw falha(p.nome + " precisa da BIOS: " + bios.faltam.map(function (b) { return b.o_que || b.destino; }).join("; ") +
          ". Ponha na pasta BIOS do ARENA (guia 2-JOGOS.md).");
      }
      const sistema = [];
      for (const b of bios.achadas) sistema.push({ caminho: b.caminho, dados: await b.arquivo.arrayBuffer() });
      const base = semExtensao(pedido.principal);
      const guardados = await guardadosDoJogo(p, base);
      E.partida = { ativo: true, id: jogo.id, titulo: jogo.titulo, plataforma: p.id, inicio: Date.now() };
      ArenaPartida.abrir({
        titulo: jogo.titulo,
        nucleo: p.core_navegador,
        principal: pedido.principal,
        arquivos: pedido.arquivos,
        sistema: sistema,
        guardados: guardados,
        configuracao: montarConfiguracao(p),
        opcoes: montarOpcoes(p),
      }, {
        guardados: function (lista) { guardar(lista); },
        // A tela mostra o motivo no alto (app.js, mostrarPorQueNaoAbriu).
        erro: function (texto) { E.problema = { jogo_id: jogo.id, titulo: jogo.titulo, texto: texto }; },
        fim: function (motivo) {
          registrarTempo(jogo, Date.now() - E.partida.inicio);
          E.partida = { ativo: false, ultimo: jogo.id, motivo: motivo };
        },
      });
    } catch (erro) {
      ArenaPartida.fechar("erro");
      E.partida = { ativo: false };
      throw erro;
    }
    return { ok: true, emulador: "RetroArch " + D.retroarch + " no navegador", alerta_maquina: null };
  }

  // ------------------------------------------------------------------------
  // Recordes e tempo de jogo (so deste navegador)
  // ------------------------------------------------------------------------
  async function registrarTempo(jogo, ms) {
    try {
      const tempos = (await ArenaBanco.ler("coisas", "tempos")) || {};
      tempos[jogo.id] = { titulo: jogo.titulo, plataforma: jogo.plataforma_nome,
                          minutos: Math.round(((tempos[jogo.id] || {}).minutos || 0) + ms / 60000) };
      await ArenaBanco.gravar("coisas", "tempos", tempos);
    } catch (erro) { /* sem banco: o tempo desta vez se perde */ }
  }

  async function ranking() {
    const placar = (await ArenaBanco.ler("coisas", "placar")) || [];
    const tempos = (await ArenaBanco.ler("coisas", "tempos")) || {};
    const pontos = placar.slice().sort(function (a, b) { return b.pontos - a.pontos; }).slice(0, 50);
    const tempo = Object.values(tempos).sort(function (a, b) { return b.minutos - a.minutos; }).slice(0, 50);
    return { pontos: pontos, tempo: tempo, ok: true };
  }

  // ------------------------------------------------------------------------
  // As respostas
  // ------------------------------------------------------------------------
  function plataformas() {
    if (E.plataformas) return E.plataformas;
    const lista = D.consoles.map(function (p) {
      let estado = "pronta";
      let motivo = "";
      if (!p.core_navegador) {
        estado = "sem_core";
        motivo = "Este console só roda no ARENA do Windows: o Chromebook não tem o emulador dele.";
      } else if (!temNucleo(p)) {
        estado = "sem_core";
        motivo = "Falta o núcleo deste console nesta cópia do ARENA (launcher\\navegador\\nucleos).";
      }
      const e = classificar(p);
      return {
        id: p.id, nome: p.nome, descricao: p.descricao, peso: p.peso, pasta: p.pasta, custo: p.custo || 3,
        jogadores_max: p.jogadores_max || 2, netplay: false,
        netplay_motivo: "No Chromebook ainda não há jogo em rede: os jogadores jogam no mesmo Chromebook.",
        estado: estado, motivo: motivo, classe: e.chave, classe_rotulo: e.rotulo, classe_cor: e.cor,
        classe_detalhe: e.detalhe, emulador: p.core_navegador ? "RetroArch no navegador" : "só no Windows",
        aceita_partida: false, motivo_sem_partida: "No Chromebook ainda não há jogo em rede.",
        externo_sugerido: null, perfil_sugerido: "", jeitos: [],
      };
    });
    lista.push({
      id: "indefinido", nome: "Precisa escolher o console", descricao: "Arraste para a pasta do console certo, no lado esquerdo.",
      peso: "leve", pasta: "", custo: 1, estado: "sem_pasta", motivo: "Este arquivo serve a mais de um console. Diga qual e.",
      classe: "ajustes", classe_rotulo: "", classe_cor: "azul", classe_detalhe: "", perfil_sugerido: "",
      emulador: "-", externo_sugerido: null, jeitos: [],
    });
    E.plataformas = lista;
    return lista;
  }

  function catalogo() {
    const jogos = E.jogos.map(function (j) {
      const copiaDoJogo = Object.assign({}, j);
      if (j.capas && j.capas.length) copiaDoJogo.capa_urls = capaUrls(j);
      return copiaDoJogo;
    });
    return { plataformas: plataformas(), jogos: jogos, total: jogos.length };
  }

  async function estado() {
    const config = copia(E.config);
    const pasta = ArenaPasta.situacao();
    const lista = window.ARENA_NUCLEOS_LISTA;
    return {
      no_navegador: true,
      navegador: {
        pasta: pasta,
        tem_seletor: ArenaPasta.temSeletor,
        manifesto: E.manifesto ? (E.manifesto.feito_no_navegador ? "feito_aqui" : "do_windows") : "nenhum",
        nucleos: Object.keys(nucleos()).length,
        retroarch: D.retroarch,
        so_na_memoria: E.soNaMemoria,
        pagina: location.protocol === "file:" ? "pen_drive" : "endereco",
      },
      maquina: E.maquina,
      retroarch_presente: !!lista,
      arquivos_sistema: 0,
      runtime_ok: true,
      servidores_online: [],
      rede_checada_ha: null,
      config: config,
      efetivas: { video_driver: E.maquina.driver_video + " (navegador)", input_joypad_driver: "navegador" },
      perfis: D.perfis,
      versao: D.versao,
      codigo_amigo: "",
      tem_foto_perfil: !!(await ArenaBanco.ler("coisas", "foto").catch(function () { return null; })),
      capacidade: { nota: notaDaMaquina() },
      economico: false,
      versao_confere: D.versao,
      vigia_suspenso: false,
      fechamentos: [],
      repasses: [],
      controles: [],
      consoles_botoes: [],
      externos: [],
      lossless: null,
      navegadores: null,
      rede_ps2: {},
      bios_disponiveis: [],
      memory_cards: [],
      bios_consoles: [],
      shader: null,
      porta_partida: 0,
      recursos: [],
      grupos: [],
      jogo_em_andamento: copia(E.partida),
      ultimo_problema: E.problema,
      pendentes: 0,
      mala: { caminho: "—", existe: false },
      meu_endereco: "",
      enderecos: [],
      internet: navigator.onLine,
      pacotes: [],
      pastas: {
        saves: pasta.pode_gravar ? "retroarch\\saves (no pen drive) e neste navegador" : "neste navegador",
        capturas: "neste navegador",
        jogos: pasta.tem ? pasta.nome + "\\jogos" : "escolha a pasta do ARENA",
        sistema: pasta.tem ? pasta.nome + "\\retroarch\\system" : "escolha a pasta do ARENA",
        raiz: pasta.nome || "",
      },
    };
  }

  async function salvarMudanca(dados) {
    const c = E.config;
    if (["claro", "escuro"].includes(dados.tema)) c.tema = dados.tema;
    if (["automatico", "sempre", "parado"].includes(dados.fundo_animado)) c.fundo_animado = dados.fundo_animado;
    if ("apelido" in dados) c.apelido = limparApelido(dados.apelido);
    if (dados.favorito) {
      const alvo = String(dados.favorito).slice(0, 300);
      if (c.favoritos.includes(alvo)) c.favoritos = c.favoritos.filter(function (f) { return f !== alvo; });
      else if (E.jogos.some(function (j) { return j.id === alvo; })) c.favoritos = [alvo].concat(c.favoritos).slice(0, 200);
    }
    if (Array.isArray(dados.recentes)) {
      c.recentes = dados.recentes.filter(function (r) { return typeof r === "string"; }).map(function (r) { return r.slice(0, 300); }).slice(0, 20);
    }
    if ("modo_modesto" in dados) c.modo_modesto = !!dados.modo_modesto;
    await guardarConfig();
    return { ok: true, config: copia(c), efetivas: { video_driver: E.maquina.driver_video + " (navegador)" }, rede_aplicada: false };
  }

  const SO_NO_WINDOWS = "No Chromebook isto não existe: é do ARENA do Windows.";

  async function responder(caminho, metodo, corpo, busca) {
    await E.iniciado;
    if (metodo === "GET") {
      switch (caminho) {
        case "/api/estado": return estado();
        case "/api/catalogo": return catalogo();
        case "/api/jogo": {
          const jogo = E.jogos.find(function (j) { return j.id === busca.get("id"); });
          if (!jogo) throw falha("Jogo não encontrado. Clique em Atualizar lista e tente de novo.", 404);
          const estados = await listarEstados(jogo);
          return {
            titulo: jogo.titulo, plataforma: jogo.plataforma, plataforma_nome: jogo.plataforma_nome,
            ambiguo: !!jogo.ambiguo, corrigido: !!jogo.corrigido,
            consoles: D.consoles.map(function (p) { return { id: p.id, nome: p.nome, pasta: p.pasta }; })
              .sort(function (a, b) { return a.nome.localeCompare(b.nome, "pt-BR"); }),
            sugestao: jogo.sugestao || null, pasta_atual: pastaDoArquivo(jogo.arquivo),
            estados: estados.espacos, tem_save: estados.tem_save, cheats: [],
          };
        }
        case "/api/ranking": return ranking();
        case "/api/conquistas": return { conquistas: [], ok: true };
        case "/api/colegas": return { colegas: [] };
        case "/api/partida/estado": return { ativa: false };
        case "/api/partida/procurar": return { partidas: [], amigos: [] };
        case "/api/capas/progresso": return { rodando: false, total: 0, feitos: 0, achados: 0, atual: "" };
        case "/api/arrumar/progresso": return { terminou: true };
        case "/api/acervo": return { itens: [], fontes: [] };
        case "/api/biblioteca-online": return { resultados: [], ok: true };
        case "/api/biblioteca-livre": return { jogos: [] };
        case "/api/barreiras": return { itens: [] };
        case "/api/bios": return { consoles: [] };
        case "/api/mapeamento": return { jogadores: {} };
        case "/api/botoes": return { botoes: [] };
        case "/api/perfis-controle": return {};
        case "/api/como-colocar": return { consoles: [] };
        default: throw falha("Rota não encontrada.", 404);
      }
    }
    switch (caminho) {
      case "/api/config": return salvarMudanca(corpo || {});
      case "/api/jogar": return jogar(corpo || {});
      case "/api/indexar":
        await montarLista();
        return { ok: true, total: E.jogos.length };
      case "/api/placar": {
        const jogo = E.jogos.find(function (j) { return j.id === (corpo || {}).jogo_id; });
        const pontos = parseInt((corpo || {}).pontos, 10);
        if (!jogo || !(pontos >= 0)) throw falha("Diga quantos pontos você fez.");
        const placar = (await ArenaBanco.ler("coisas", "placar")) || [];
        placar.push({ apelido: E.config.apelido, jogo: jogo.titulo, plataforma: jogo.plataforma_nome, pontos: pontos,
                      quando: new Date().toLocaleString("pt-BR") });
        await ArenaBanco.gravar("coisas", "placar", placar.slice(-500));
        return { ok: true, recorde: false, posicao: null };
      }
      case "/api/estado/apagar": {
        const jogo = E.jogos.find(function (j) { return j.id === (corpo || {}).jogo_id; });
        const numero = parseInt((corpo || {}).espaco, 10);
        if (!jogo || !(numero >= 0 && numero < ESPACOS)) throw falha("Escolha um espaço de 0 a 9.");
        const p = POR_ID.get(jogo.plataforma);
        const nome = "states/" + pastaDoNucleo(p) + "/" + semExtensao(nomeDoArquivo(jogo.arquivo)) + sufixoDoEspaco(numero);
        await ArenaBanco.apagar("guardados", nome);
        await ArenaPasta.apagarArquivo("retroarch/" + nome);
        await ArenaPasta.apagarArquivo("retroarch/" + nome + ".png");
        return { ok: true, estados: (await listarEstados(jogo)).espacos };
      }
      case "/api/perfil/foto": {
        if ((corpo || {}).remover) await ArenaBanco.apagar("coisas", "foto");
        else if (typeof (corpo || {}).imagem === "string" && corpo.imagem.startsWith("data:image/") &&
                 corpo.imagem.length < 3000000) await ArenaBanco.gravar("coisas", "foto", corpo.imagem);
        else throw falha("Use uma imagem PNG, JPG ou WEBP de até 2 MB.");
        await lerFoto();
        return { ok: true };
      }
      case "/api/capa/miniatura": return { ok: true };
      case "/api/navegador/pasta": {
        const acao = (corpo || {}).acao;
        const situacao = acao === "liberar" ? await ArenaPasta.liberar() : await ArenaPasta.escolher();
        await montarLista();
        return { ok: true, pasta: situacao, total: E.jogos.length };
      }
      case "/api/navegador/maquina":
        E.maquina = await medirMaquina(true);
        E.plataformas = null;
        return { ok: true, maquina: E.maquina };
      default:
        throw falha(SO_NO_WINDOWS);
    }
  }

  // A foto do perfil fica pronta na memoria: o <img> pede /api/perfil/foto
  // e o servidor.js troca pelo endereco "data:" na hora.
  async function lerFoto() {
    try { window.ARENA_FOTO_DO_PERFIL = (await ArenaBanco.ler("coisas", "foto")) || ""; }
    catch (erro) { window.ARENA_FOTO_DO_PERFIL = ""; }
  }

  // ------------------------------------------------------------------------
  // A calibracao da regua de velocidade (ver INSTRUCOES_DO_ALVO_POR_MS).
  // ------------------------------------------------------------------------
  function calibracao() {
    return INSTRUCOES_DO_ALVO_POR_MS;
  }

  async function iniciar() {
    E.soNaMemoria = await ArenaBanco.soNaMemoria();
    E.config = await carregarConfig();
    await guardarConfig();
    E.maquina = await medirMaquina();
    await ArenaPasta.iniciar();
    await montarLista();
    await lerFoto();
    ArenaBanco.pedirParaGuardar();
  }

  E.iniciado = iniciar().catch(function (erro) {
    E.problema = { texto: "O ARENA no navegador não conseguiu começar: " + (erro && erro.message || erro) };
    if (!E.config) E.config = copia(D.config_padrao);
    if (!E.maquina) E.maquina = { cpu: "?", nucleos: 0, ram_total_gb: 0, ram_livre_gb: 0, disco: {}, sistema: "", driver_video: "", runtime_ok: true, velocidade: {} };
  });

  return { responder: responder, estado: E, medirVelocidade: medirVelocidade, limparTitulo: limparTitulo,
           montarLista: montarLista, falha: falha };
})();
// Os pedidos da tela que chegaram antes (servidor.js) ja podem ser atendidos.
if (window.ARENA_ROTAS_PRONTAS) window.ARENA_ROTAS_PRONTAS();
