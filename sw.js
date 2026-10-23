"use strict";
// --------------------------------------------------------------------------
// ARENA na internet: o "service worker" (auditoria 4, 22/10/2026).
//
// Guarda no aparelho a tela do ARENA e os nucleos que ja abriram, para o
// ARENA abrir de novo sem internet, como um app ("Adicionar a tela
// inicial"). A versao vem do ferramentas/montar_site.py: versao nova, guarda
// nova (a velha e' apagada). Os pedidos /api/ nao passam por aqui: quem
// responde e' o servidor dentro da propria pagina (launcher/navegador).
// --------------------------------------------------------------------------
// Duas guardas: a da tela (troca a cada montagem que muda algum arquivo) e a
// dos nucleos (so troca quando um nucleo muda: 92 MB nao se baixam de novo a
// cada conserto da tela). As duas levam a "impressao digital" do conteudo.
const VERSAO = "2026.10.22-20b97afdaa";
const GUARDA = "arena-" + VERSAO;
const NUCLEOS = "arena-nucleos-88782bb925";
const BASICOS = [
 "./",
 "icone-192.png",
 "icone-512.png",
 "index.html",
 "launcher/app.js",
 "launcher/estilo.css",
 "launcher/field-background.js",
 "launcher/galaxy-background.js",
 "launcher/index.html",
 "launcher/navegador/android.js",
 "launcher/navegador/banco.js",
 "launcher/navegador/dados.js",
 "launcher/navegador/estilo.css",
 "launcher/navegador/jogo.html",
 "launcher/navegador/jogo.js",
 "launcher/navegador/livres.js",
 "launcher/navegador/partida.js",
 "launcher/navegador/pasta.js",
 "launcher/navegador/rotas.js",
 "launcher/navegador/servidor.js",
 "launcher/navegador/tela.js",
 "launcher/navegador/toque.js",
 "launcher/pixel-sprites.js",
 "manifest.webmanifest"
];

self.addEventListener("install", function (evento) {
  evento.waitUntil(caches.open(GUARDA).then(function (guarda) { return guarda.addAll(BASICOS); })
    .then(function () { return self.skipWaiting(); }));
});

self.addEventListener("activate", function (evento) {
  evento.waitUntil(caches.keys().then(function (nomes) {
    return Promise.all(nomes.filter(function (nome) {
      return nome.indexOf("arena-") === 0 && nome !== GUARDA && nome !== NUCLEOS;
    }).map(function (nome) { return caches.delete(nome); }));
  }).then(function () { return self.clients.claim(); }));
});

self.addEventListener("fetch", function (evento) {
  const pedido = evento.request;
  const endereco = new URL(pedido.url);
  if (pedido.method !== "GET" || endereco.origin !== self.location.origin) return;
  const guarda = endereco.pathname.indexOf("/launcher/navegador/nucleos/") >= 0 ? NUCLEOS : GUARDA;
  evento.respondWith(caches.open(guarda).then(function (aberta) {
    return aberta.match(pedido, { ignoreSearch: true }).then(function (guardado) {
      if (guardado) return guardado;
      return fetch(pedido).then(function (resposta) {
        if (resposta.ok) aberta.put(pedido, resposta.clone());
        return resposta;
      });
    });
  }));
});
