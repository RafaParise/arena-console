"use strict";
// --------------------------------------------------------------------------
// ARENA no Android (item 14 do plano de 15/10/2026).
//
// No APK do ARENA, a tela e' a mesma do Chromebook (o servidor dentro da
// pagina), e o jogo abre no RetroArch NATIVO do Android, que vem dentro do
// APK (android/src/.../ArenaActivity.java): mais rapido que o do navegador e
// com os mesmos nucleos do Windows. A pagina fala com o Android pela ponte
// window.ArenaAndroid. Este arquivo so roda no APK (o servidor.js so o
// carrega quando a ponte existe) e:
//   1. troca a pasta do pen drive (pasta.js, que usa o seletor de pasta do
//      Chrome) pela do Android: a pasta do ARENA no cartao SD, no pen drive
//      do cabo OTG ou na memoria do aparelho, com a permissao de arquivos;
//   2. diz qual nucleo do Android abre cada console e leva o jogo (da pasta,
//      os livres que vem junto, os guardados no aparelho) ate o RetroArch.
// Os caminhos continuam relativos a pasta do ARENA, com "/", como no
// dados\manifesto.json do Windows.
// --------------------------------------------------------------------------
(function () {
  const ponte = window.ArenaAndroid;
  if (!ponte) return;
  const sistema = JSON.parse(ponte.sistema() || "{}");
  const nucleos = new Set(sistema.nucleos || []);
  document.documentElement.dataset.android = "true";

  // O celular de tela pequena (deitado, uns 800 pontos de largura): a tela do
  // ARENA desenhada como num notebook pequeno e reduzida para caber, em vez
  // de espremida.
  if (window.innerWidth < 900) {
    const meta = document.querySelector('meta[name="viewport"]');
    if (meta) meta.content = "width=900";
  }

  function normalizar(caminho) {
    return String(caminho || "").replace(/\\/g, "/").replace(/^\/+/, "").replace(/\/{2,}/g, "/");
  }

  function base64(dados) {
    const bytes = dados instanceof Uint8Array ? dados : new Uint8Array(dados);
    let binario = "";
    for (let i = 0; i < bytes.length; i += 0x8000) {
      binario += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
    }
    return btoa(binario);
  }

  function endereco(caminho) {
    return "/" + normalizar(caminho).split("/").map(encodeURIComponent).join("/");
  }

  // ------------------------------------------------------------------------
  // 1. A pasta do ARENA no aparelho (a mesma interface do pasta.js)
  // ------------------------------------------------------------------------
  let raiz = sistema.pasta || "";
  let permissao = !!sistema.permissao;

  function situacao() {
    return {
      tem: !!raiz, nome: raiz ? raiz.split("/").pop() : "", jeito: "android",
      pode_gravar: !!raiz && permissao, precisa_permissao: !!raiz && !permissao, so_jogos: false,
    };
  }

  function pedirPermissao() {
    return new Promise(function (pronto) {
      window.ARENA_ANDROID_PERMISSAO = function (ok) { permissao = !!ok; pronto(permissao); };
      ponte.pedirPermissao();
    });
  }

  function achadas() {
    try { return JSON.parse(ponte.pastasDoArena() || "[]"); } catch (falha) { return []; }
  }

  async function iniciar() {
    permissao = ponte.temPermissao();
    // Uma pasta so no aparelho: ja vale, sem perguntar.
    if (permissao && !raiz) {
      const lista = achadas();
      if (lista.length === 1 && ponte.escolherPasta(lista[0].caminho)) raiz = lista[0].caminho;
    }
    return situacao();
  }

  async function escolher() {
    if (!permissao && !(await pedirPermissao())) {
      throw new Error("Sem a permissão de arquivos, o ARENA não enxerga a pasta do ARENA no aparelho. Toque de novo " +
                      "e escolha Permitir.");
    }
    const lista = achadas();
    if (!lista.length) {
      throw new Error("Não achei a pasta do ARENA neste aparelho. Copie a pasta ARENA para o cartão SD ou para a " +
                      "memória do aparelho (ou ligue o pen drive do ARENA pelo cabo OTG) e toque de novo.");
    }
    let escolhida = lista[0];
    if (lista.length > 1) {
      const texto = lista.map(function (a, i) { return (i + 1) + ". " + a.nome + ": " + a.caminho; }).join("\n");
      const numero = parseInt(window.prompt("Achei mais de uma pasta do ARENA. Qual usar? (o número)\n" + texto, "1"), 10);
      if (lista[numero - 1]) escolhida = lista[numero - 1];
    }
    if (!ponte.escolherPasta(escolhida.caminho)) throw new Error("Essa pasta não parece a do ARENA.");
    raiz = escolhida.caminho;
    return situacao();
  }

  async function liberar() {
    if (!permissao) await pedirPermissao();
    return situacao();
  }

  function itensDe(caminho) {
    if (!raiz || !permissao) return [];
    try { return JSON.parse(ponte.listar(normalizar(caminho).replace(/\/$/, "")) || "[]"); } catch (falha) { return []; }
  }

  async function listar(caminho) {
    return itensDe(caminho).map(function (i) { return { nome: i.nome, pasta: i.pasta }; });
  }

  // Um "File" que so le o conteudo quando pedem (a lista de jogos so precisa
  // do nome e do tamanho; o jogo, o RetroArch le direto do cartao).
  async function arquivo(caminho) {
    caminho = normalizar(caminho);
    if (!raiz || !permissao) return null;
    const corte = caminho.lastIndexOf("/");
    const nome = caminho.slice(corte + 1);
    const item = itensDe(corte < 0 ? "" : caminho.slice(0, corte)).find(function (i) {
      return !i.pasta && i.nome.toLowerCase() === nome.toLowerCase();
    });
    if (!item) return null;
    const real = (corte < 0 ? "" : caminho.slice(0, corte + 1)) + item.nome;
    async function conteudo() {
      const resposta = await fetch(endereco(real), { cache: "no-store" });
      if (!resposta.ok) throw new Error("Não consegui ler " + item.nome + " no aparelho.");
      return resposta;
    }
    return {
      name: item.nome, size: item.tamanho,
      arrayBuffer: async function () { return (await conteudo()).arrayBuffer(); },
      text: async function () { return (await conteudo()).text(); },
    };
  }

  async function lerTexto(caminho) {
    const f = await arquivo(caminho);
    return f ? f.text() : null;
  }

  async function gravar(caminho, dados) {
    if (!raiz || !permissao) return false;
    const bytes = typeof dados === "string" ? new TextEncoder().encode(dados) : dados;
    return !!ponte.gravar(normalizar(caminho), base64(bytes));
  }

  async function apagarArquivo(caminho) {
    return !!(raiz && permissao && ponte.apagar(normalizar(caminho)));
  }

  window.ArenaPasta = {
    iniciar: iniciar, escolher: escolher, liberar: liberar, situacao: situacao, arquivo: arquivo, listar: listar,
    lerTexto: lerTexto, gravar: gravar, apagarArquivo: apagarArquivo, normalizar: normalizar, temSeletor: true,
  };

  // ------------------------------------------------------------------------
  // 2. O jogo no RetroArch do Android
  // ------------------------------------------------------------------------
  // O nucleo do Windows (consoles.json, "fceumm_libretro.dll") e o do
  // Android ("fceumm_libretro_android.so"). Dois tem outro nome la: o do N64
  // (a versao para o OpenGL ES 3 dos celulares) e o MAME atual.
  const OUTRO_NOME = {
    mupen64plus_next_libretro: "mupen64plus_next_gles3_libretro",
    mame_libretro: "mamearcade_libretro",
  };

  function nucleoDe(p) {
    if (!p || !p.core) return "";
    const base = String(p.core).replace(/\.dll$/i, "");
    const nome = (OUTRO_NOME[base] || base) + "_android.so";
    return nucleos.has(nome) ? nome : "";
  }

  // "fceumm" (o nome curto, o das opcoes de nucleo do ARENA).
  function nomeCurto(p) {
    return p && p.core ? String(p.core).replace(/_libretro\.dll$/i, "").toLowerCase() : "";
  }

  function pastaDoArquivo(caminho) {
    const partes = normalizar(caminho).split("/");
    partes.pop();
    return partes.join("/");
  }

  // O caminho inteiro do jogo no aparelho, para o RetroArch abrir.
  async function caminhoDoJogo(jogo) {
    if (jogo.origem === "vem_com") {
      const livre = (window.ARENA_LIVRES || []).find(function (j) { return "vem-com/" + j.arquivo === jogo.arquivo; });
      if (!livre) throw new Error("Este jogo livre não veio nesta cópia do ARENA.");
      const caminho = ponte.gravar("app:livres/" + normalizar(livre.arquivo), livre.dados);
      if (!caminho) throw new Error("Não consegui preparar o jogo livre no aparelho.");
      return caminho;
    }
    if (jogo.origem === "navegador") {
      const guardado = await ArenaBanco.ler("jogos", jogo.arquivo);
      if (!guardado) throw new Error("Este jogo não está mais guardado neste aparelho.");
      const caminho = ponte.gravar("app:guardados/" + normalizar(guardado.nome), base64(guardado.dados));
      if (!caminho) throw new Error("Não consegui preparar o jogo guardado no aparelho.");
      return caminho;
    }
    if (!raiz || !permissao) {
      throw new Error(raiz ? "O Android pede a permissão de arquivos: toque em Escolher a pasta do ARENA."
        : "Para abrir os jogos do cartão ou do pen drive, toque em Escolher a pasta do ARENA (no alto da lista).");
    }
    const discos = jogo.discos && jogo.discos.length > 1 ? jogo.discos : null;
    if (discos) {
      // Varios discos: a lista .m3u (com o caminho inteiro de cada um), o
      // jeito do RetroArch de trocar de disco sem sair, como no Windows.
      const linhas = discos.map(function (d) { return ponte.caminho(normalizar(d)); });
      if (linhas.some(function (l) { return !l; })) throw new Error("Falta um dos discos deste jogo no aparelho.");
      const nome = normalizar(jogo.arquivo).split("/").pop().replace(/\.[^.]*$/, "") + ".m3u";
      const caminho = ponte.gravar("app:listas/" + nome, base64(new TextEncoder().encode(linhas.join("\n") + "\n")));
      if (!caminho) throw new Error("Não consegui montar a lista dos discos.");
      return caminho;
    }
    const caminho = ponte.caminho(normalizar(jogo.arquivo));
    if (!caminho) throw new Error("Não achei " + normalizar(jogo.arquivo).split("/").pop() + " no aparelho. " +
                                  "Ele pode ter sido movido: toque em Atualizar lista.");
    return caminho;
  }

  // Abre o jogo. "" quando o Android aceitou o pedido; senao, a frase do erro.
  // O fim do jogo vem pelo ARENA_ANDROID_FIM (segundos), quando a tela volta.
  function jogar(pedido) {
    return ponte.jogar(JSON.stringify(pedido)) || "";
  }

  window.ArenaNoAparelho = {
    sistema: sistema, nucleoDe: nucleoDe, nomeCurto: nomeCurto, caminhoDoJogo: caminhoDoJogo, jogar: jogar,
    pastaDoArquivo: pastaDoArquivo,
  };

  // O botao "voltar" do aparelho: fecha o painel aberto, ou pergunta se sai.
  window.ARENA_ANDROID_VOLTAR = function () {
    const aberto = document.querySelector("dialog[open], .painel-aberto, [data-aberto='true']");
    if (aberto && typeof aberto.close === "function") { aberto.close(); return; }
    if (window.confirm("Sair do ARENA?")) ponte.sair();
  };
})();
