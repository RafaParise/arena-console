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
const VERSAO = "__VERSAO__";
const GUARDA = "arena-" + VERSAO;
const BASICOS = __BASICOS__;

self.addEventListener("install", function (evento) {
  evento.waitUntil(caches.open(GUARDA).then(function (guarda) { return guarda.addAll(BASICOS); })
    .then(function () { return self.skipWaiting(); }));
});

self.addEventListener("activate", function (evento) {
  evento.waitUntil(caches.keys().then(function (nomes) {
    return Promise.all(nomes.filter(function (nome) { return nome.indexOf("arena-") === 0 && nome !== GUARDA; })
      .map(function (nome) { return caches.delete(nome); }));
  }).then(function () { return self.clients.claim(); }));
});

self.addEventListener("fetch", function (evento) {
  const pedido = evento.request;
  if (pedido.method !== "GET" || new URL(pedido.url).origin !== self.location.origin) return;
  evento.respondWith(caches.match(pedido, { ignoreSearch: true }).then(function (guardado) {
    if (guardado) return guardado;
    return fetch(pedido).then(function (resposta) {
      if (resposta.ok) {
        const copia = resposta.clone();
        caches.open(GUARDA).then(function (guarda) { guarda.put(pedido, copia); });
      }
      return resposta;
    });
  }));
});
