"use strict";
// --------------------------------------------------------------------------
// ARENA no navegador: o comeco (item 12 do plano de 15/10/2026).
//
// O index.html carrega este arquivo antes do app.js, no Windows e no
// Chromebook. No Windows (a tela vem do servidor Python, http://127.0.0.1:8777)
// ele nao faz nada. Aberta do pen drive (file://, o ARENA-CHROMEBOOK.html) ou
// com ?navegador=1 no endereco, a tela passa a ter o servidor dentro dela:
//   1. carrega os outros arquivos desta pasta (os dados, o banco, a pasta do
//      pen drive, o jogo, as rotas e a parte da tela so do navegador);
//   2. atende os pedidos /api/... da tela (rotas.js) sem sair da pagina --
//      o pedido que chegar antes de as rotas carregarem espera por elas;
//   3. troca o endereco das imagens /api/capa e /api/perfil/foto pelo arquivo
//      do pen drive e pela foto guardada no navegador.
// --------------------------------------------------------------------------
(function () {
  const busca = new URLSearchParams(location.search);
  // ARENA_SEMPRE_NAVEGADOR: a versao da internet (ferramentas/montar_site.py)
  // nao tem o servidor Python atras, em nenhum endereco.
  const noNavegador = location.protocol === "file:" || busca.get("navegador") === "1" ||
    window.ARENA_SEMPRE_NAVEGADOR === true;
  window.ARENA_NO_NAVEGADOR = noNavegador;
  if (!noNavegador) return;

  document.documentElement.dataset.navegador = "true";
  const aqui = (document.currentScript && document.currentScript.src || "").replace(/[^/]*$/, "") || "navegador/";
  const SEGUNDOS_PARA_CARREGAR = 20;

  let avisarRotas = null;
  const rotasProntas = new Promise(function (pronto, falhou) {
    avisarRotas = pronto;
    setTimeout(function () {
      falhou(new Error("O ARENA no navegador não carregou: falta algum arquivo da pasta launcher\\navegador."));
    }, SEGUNDOS_PARA_CARREGAR * 1000);
  });
  rotasProntas.catch(function () { /* a resposta de cada pedido conta o erro */ });
  window.ARENA_ROTAS_PRONTAS = function () { avisarRotas(); };

  const estilo = document.createElement("link");
  estilo.rel = "stylesheet";
  estilo.href = aqui + "estilo.css";
  document.head.appendChild(estilo);
  // async = false: rodam na ordem em que entram (os dados antes das rotas).
  // No APK do Android (item 14), a ponte window.ArenaAndroid existe: os jogos
  // abrem no RetroArch nativo (android.js, que troca a pasta.js), com as
  // opcoes de todos os nucleos (android_dados.js, do montador do APK), e os
  // nucleos do navegador nem vem.
  const scripts = window.ArenaAndroid
    ? ["dados.js", "android_dados.js", "livres.js", "banco.js", "pasta.js", "android.js", "partida.js", "rotas.js",
       "tela.js"]
    : ["dados.js", "nucleos/lista.js", "livres.js", "banco.js", "pasta.js", "partida.js", "rotas.js", "tela.js"];
  for (const nome of scripts) {
    const script = document.createElement("script");
    script.src = aqui + nome;
    script.async = false;
    document.head.appendChild(script);
  }

  const fetchDoNavegador = window.fetch.bind(window);
  const JSON_UTF8 = { "Content-Type": "application/json; charset=utf-8" };

  window.fetch = function (recurso, opcoes) {
    let endereco;
    try {
      endereco = new URL(typeof recurso === "string" ? recurso : recurso.url, location.href);
    } catch (falha) {
      return fetchDoNavegador(recurso, opcoes);
    }
    const local = endereco.protocol === location.protocol &&
      (endereco.protocol === "file:" || endereco.host === location.host);
    const corte = endereco.pathname.indexOf("/api/");
    if (!local || corte < 0) return fetchDoNavegador(recurso, opcoes);
    const metodo = String((opcoes && opcoes.method) || "GET").toUpperCase();
    let corpo = null;
    try {
      corpo = opcoes && typeof opcoes.body === "string" ? JSON.parse(opcoes.body) : null;
    } catch (falha) {
      corpo = null;
    }
    return rotasProntas.then(function () {
      return window.ArenaRotas.responder(endereco.pathname.slice(corte), metodo, corpo, endereco.searchParams);
    }).then(
      function (dados) {
        return new Response(JSON.stringify(dados === undefined ? { ok: true } : dados), { status: 200, headers: JSON_UTF8 });
      },
      function (falha) {
        return new Response(JSON.stringify({ ok: false, erro: String(falha && falha.message || falha) }),
                            { status: (falha && falha.status) || 400, headers: JSON_UTF8 });
      });
  };

  const PIXEL_VAZIO = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7";

  function traduzirImagem(valor) {
    const capa = valor.match(/(?:^|\/)api\/capa\?(.*)$/);
    if (capa) {
      const arquivo = new URLSearchParams(capa[1]).get("arquivo");
      // A capa mora em retroarch\thumbnails, na pasta do ARENA: a tela esta
      // em launcher\, um nivel abaixo.
      if (arquivo) return "../" + arquivo.split("/").map(encodeURIComponent).join("/");
    }
    if (/(?:^|\/)api\/perfil\/foto/.test(valor)) return window.ARENA_FOTO_DO_PERFIL || PIXEL_VAZIO;
    return valor;
  }

  const fonte = Object.getOwnPropertyDescriptor(HTMLImageElement.prototype, "src");
  Object.defineProperty(HTMLImageElement.prototype, "src", {
    configurable: true,
    enumerable: fonte.enumerable,
    get: function () { return fonte.get.call(this); },
    set: function (valor) { fonte.set.call(this, traduzirImagem(String(valor))); },
  });
})();
