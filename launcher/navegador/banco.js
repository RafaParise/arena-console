"use strict";
// --------------------------------------------------------------------------
// ARENA no navegador: o banco (item 12 do plano de 15/10/2026).
//
// No Windows, o ARENA guarda tudo em arquivos (dados\config.json, os saves
// em retroarch\saves). No navegador nao ha disco livre para isso: cada site
// tem a sua base IndexedDB, que continua la quando o Chromebook desliga.
// Tres gavetas:
//   coisas    -> a configuracao, o perfil, o placar, o acesso a pasta do pen drive
//   guardados -> os saves e os estados ("saves/FCEUmm/Contra.srm"), os
//                mesmos caminhos do retroarch\ do Windows
//   jogos     -> jogos copiados para dentro do navegador (sem pen drive)
// Se o navegador recusar a base (janela anonima, cota cheia), o ARENA usa a
// memoria e avisa: funciona, mas o save some quando a aba fecha.
// --------------------------------------------------------------------------
window.ArenaBanco = (function () {
  const NOME = "arena-navegador";
  const VERSAO = 1;
  const GAVETAS = ["coisas", "guardados", "jogos"];
  let base = null;
  let naMemoria = null;          // Map por gaveta, quando o IndexedDB falha

  function abrir() {
    if (base) return base;
    base = new Promise(function (pronto) {
      let pedido;
      try {
        pedido = indexedDB.open(NOME, VERSAO);
      } catch (falha) {
        pronto(null);
        return;
      }
      pedido.onupgradeneeded = function () {
        for (const gaveta of GAVETAS) {
          if (!pedido.result.objectStoreNames.contains(gaveta)) pedido.result.createObjectStore(gaveta);
        }
      };
      pedido.onsuccess = function () { pronto(pedido.result); };
      pedido.onerror = function () { pronto(null); };
      pedido.onblocked = function () { pronto(null); };
    }).then(function (aberta) {
      if (!aberta) {
        naMemoria = new Map(GAVETAS.map(function (g) { return [g, new Map()]; }));
      }
      return aberta;
    });
    return base;
  }

  function pedir(gaveta, modo, fazer) {
    return abrir().then(function (aberta) {
      if (!aberta) return fazer(null, naMemoria.get(gaveta));
      return new Promise(function (pronto, falhou) {
        const transacao = aberta.transaction(gaveta, modo);
        const resultado = fazer(transacao.objectStore(gaveta), null);
        transacao.oncomplete = function () { pronto(resultado instanceof IDBRequest ? resultado.result : resultado); };
        transacao.onerror = function () { falhou(transacao.error); };
        transacao.onabort = function () { falhou(transacao.error || new Error("gravação cancelada")); };
      });
    });
  }

  function ler(gaveta, chave) {
    return pedir(gaveta, "readonly", function (armario, memoria) {
      return memoria ? memoria.get(chave) : armario.get(chave);
    });
  }

  function gravar(gaveta, chave, valor) {
    return pedir(gaveta, "readwrite", function (armario, memoria) {
      if (memoria) { memoria.set(chave, valor); return undefined; }
      armario.put(valor, chave);
      return undefined;
    });
  }

  function apagar(gaveta, chave) {
    return pedir(gaveta, "readwrite", function (armario, memoria) {
      if (memoria) { memoria.delete(chave); return undefined; }
      armario.delete(chave);
      return undefined;
    });
  }

  // [[chave, valor], ...] das chaves que comecam com "prefixo".
  function listar(gaveta, prefixo) {
    prefixo = prefixo || "";
    return abrir().then(function (aberta) {
      if (!aberta) {
        return Array.from(naMemoria.get(gaveta).entries()).filter(function (par) {
          return String(par[0]).startsWith(prefixo);
        });
      }
      return new Promise(function (pronto, falhou) {
        const transacao = aberta.transaction(gaveta, "readonly");
        const armario = transacao.objectStore(gaveta);
        const faixa = prefixo ? IDBKeyRange.bound(prefixo, prefixo + "￿") : undefined;
        const chaves = armario.getAllKeys(faixa);
        const valores = armario.getAll(faixa);
        transacao.oncomplete = function () {
          pronto(chaves.result.map(function (chave, i) { return [chave, valores.result[i]]; }));
        };
        transacao.onerror = function () { falhou(transacao.error); };
      });
    });
  }

  // Quantas chaves comecam com "prefixo", sem ler os valores (um jogo
  // guardado pode ter megabytes).
  function contar(gaveta, prefixo) {
    prefixo = prefixo || "";
    return abrir().then(function (aberta) {
      if (!aberta) {
        return Array.from(naMemoria.get(gaveta).keys()).filter(function (chave) {
          return String(chave).startsWith(prefixo);
        }).length;
      }
      return new Promise(function (pronto, falhou) {
        const transacao = aberta.transaction(gaveta, "readonly");
        const faixa = prefixo ? IDBKeyRange.bound(prefixo, prefixo + "￿") : undefined;
        const pedido = transacao.objectStore(gaveta).count(faixa);
        transacao.oncomplete = function () { pronto(pedido.result); };
        transacao.onerror = function () { falhou(transacao.error); };
      });
    });
  }

  async function soNaMemoria() {
    await abrir();
    return !!naMemoria;
  }

  // Pede ao navegador para nao apagar a base quando faltar espaco (o Chrome
  // so apaga base de site "nao persistente"). Sem resposta, segue igual.
  async function pedirParaGuardar() {
    try {
      if (navigator.storage && navigator.storage.persist) return await navigator.storage.persist();
    } catch (falha) { /* sem esse recurso: segue */ }
    return false;
  }

  return { ler: ler, gravar: gravar, apagar: apagar, listar: listar, contar: contar, soNaMemoria: soNaMemoria,
           pedirParaGuardar: pedirParaGuardar };
})();
