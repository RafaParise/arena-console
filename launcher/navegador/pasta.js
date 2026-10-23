"use strict";
// --------------------------------------------------------------------------
// ARENA no navegador: a pasta do ARENA no pen drive (item 12 do plano).
//
// A pagina aberta do pen drive (file://) mostra imagens da pasta, mas nao le
// arquivo nenhum: o navegador so entrega um arquivo que a pessoa escolheu.
// Por isso, uma vez, o aluno escolhe a pasta do ARENA (a que tem o
// ARENA-CHROMEBOOK.html). Dai em diante:
//   - no Chrome e no Edge (seletor de pasta), o ARENA guarda o acesso no
//     banco e le e grava direto no pen drive: os jogos, as BIOS, e os saves
//     em retroarch\saves -- os mesmos do Windows, um save so nos dois;
//   - no Firefox (que nao tem o seletor de pasta), o campo de pasta: le os
//     jogos e as BIOS, e os saves ficam no navegador (dai da para levar).
// Os caminhos sao sempre relativos a pasta do ARENA, com "/" ("jogos/pessoais
// /NES/Contra.nes"), como no dados\manifesto.json do Windows.
// --------------------------------------------------------------------------
window.ArenaPasta = (function () {
  const temSeletor = typeof window.showDirectoryPicker === "function";
  let raiz = null;             // FileSystemDirectoryHandle (Chrome, Edge)
  let lista = null;            // Map caminho minusculo -> File (campo de pasta)
  let prefixo = "";            // "jogos/" quando escolheram so a pasta de jogos
  let podeGravar = false;
  let precisaPermissao = false;

  function normalizar(caminho) {
    return String(caminho || "").replace(/\\/g, "/").replace(/^\/+/, "").replace(/\/{2,}/g, "/");
  }

  function situacao() {
    return {
      tem: !!(raiz || lista),
      nome: raiz ? raiz.name : (lista ? lista.nome : ""),
      jeito: raiz ? "seletor" : (lista ? "campo" : (temSeletor ? "seletor" : "campo")),
      pode_gravar: podeGravar,
      precisa_permissao: precisaPermissao,
      so_jogos: prefixo === "jogos/",
    };
  }

  async function filhos(pasta) {
    const nomes = new Map();
    for await (const [nome, item] of pasta.entries()) nomes.set(nome.toLowerCase(), item);
    return nomes;
  }

  // A pessoa pode escolher a pasta do ARENA, a pasta acima dela (o pen drive
  // inteiro) ou so a pasta "jogos": o ARENA acha o lugar certo.
  async function acharRaiz(escolhida) {
    const dentro = await filhos(escolhida);
    if (dentro.has("jogos") || dentro.has("launcher")) return { pasta: escolhida, prefixo: "" };
    if (dentro.has("pessoais") || dentro.has("livres") || dentro.has("turma")) {
      return { pasta: escolhida, prefixo: "jogos/" };
    }
    for (const item of dentro.values()) {
      if (item.kind !== "directory") continue;
      const netos = await filhos(item);
      if (netos.has("jogos") && (netos.has("launcher") || netos.has("arena-chromebook.html"))) {
        return { pasta: item, prefixo: "" };
      }
    }
    return { pasta: escolhida, prefixo: "" };
  }

  async function iniciar() {
    if (!temSeletor) return situacao();
    let guardada = null;
    try { guardada = await ArenaBanco.ler("coisas", "pasta"); } catch (falha) { guardada = null; }
    if (guardada && guardada.pasta && guardada.pasta.kind === "directory") {
      raiz = guardada.pasta;
      prefixo = guardada.prefixo || "";
      await conferirPermissao();
    }
    return situacao();
  }

  async function conferirPermissao() {
    try {
      podeGravar = (await raiz.queryPermission({ mode: "readwrite" })) === "granted";
      precisaPermissao = !podeGravar && (await raiz.queryPermission({ mode: "read" })) !== "granted";
    } catch (falha) {
      podeGravar = false;
      precisaPermissao = true;
    }
  }

  // Precisa de um clique da pessoa (o navegador exige).
  async function escolher() {
    if (temSeletor) {
      const escolhida = await window.showDirectoryPicker({ id: "arena", mode: "readwrite" });
      const achada = await acharRaiz(escolhida);
      raiz = achada.pasta;
      prefixo = achada.prefixo;
      lista = null;
      try { await ArenaBanco.gravar("coisas", "pasta", { pasta: raiz, prefixo: prefixo }); } catch (falha) { /* sem banco: vale nesta aba */ }
      await conferirPermissao();
      return situacao();
    }
    const arquivos = await escolherComCampo();
    montarLista(arquivos);
    return situacao();
  }

  // De volta ao ARENA no dia seguinte: o Chrome pede para confirmar o acesso
  // a pasta (um clique em "Permitir").
  async function liberar() {
    if (!raiz) return escolher();
    try {
      const resposta = await raiz.requestPermission({ mode: "readwrite" });
      if (resposta !== "granted") await raiz.requestPermission({ mode: "read" });
    } catch (falha) { /* a pessoa recusou */ }
    await conferirPermissao();
    return situacao();
  }

  function escolherComCampo() {
    return new Promise(function (pronto, falhou) {
      const campo = document.createElement("input");
      campo.type = "file";
      campo.webkitdirectory = true;
      campo.multiple = true;
      campo.hidden = true;
      campo.addEventListener("change", function () {
        const escolhidos = Array.from(campo.files || []);
        campo.remove();
        if (escolhidos.length) pronto(escolhidos); else falhou(new Error("Nenhuma pasta escolhida."));
      }, { once: true });
      campo.addEventListener("cancel", function () { campo.remove(); falhou(new Error("Nenhuma pasta escolhida.")); },
                             { once: true });
      document.body.appendChild(campo);
      campo.click();
    });
  }

  // O campo de pasta entrega todos os arquivos, com o caminho a partir da
  // pasta escolhida ("ARENA/jogos/pessoais/NES/Contra.nes").
  function montarLista(arquivos) {
    // Sem o nome da pasta escolhida: ["jogos", "pessoais", "NES", "Contra.nes"].
    const caminhos = arquivos.map(function (f) {
      return normalizar(f.webkitRelativePath || f.name).split("/").slice(1);
    });
    const primeiros = new Set(caminhos.map(function (p) { return (p[0] || "").toLowerCase(); }));
    let dentroDe = null;       // escolheram o pen drive: a pasta do ARENA dentro dele
    prefixo = "";
    if (!primeiros.has("jogos") && !primeiros.has("launcher")) {
      if (primeiros.has("pessoais") || primeiros.has("livres") || primeiros.has("turma")) {
        prefixo = "jogos/";
      } else {
        const segundos = new Map();
        for (const p of caminhos) {
          if (p.length < 2) continue;
          const chave = p[0].toLowerCase();
          if (!segundos.has(chave)) segundos.set(chave, new Set());
          segundos.get(chave).add(p[1].toLowerCase());
        }
        for (const [chave, nomes] of segundos) {
          if (nomes.has("jogos") && (nomes.has("launcher") || nomes.has("arena-chromebook.html"))) { dentroDe = chave; break; }
        }
      }
    }
    lista = new Map();
    arquivos.forEach(function (arquivo, i) {
      let partes = caminhos[i];
      if (dentroDe !== null) {
        if ((partes[0] || "").toLowerCase() !== dentroDe) return;
        partes = partes.slice(1);
      }
      const real = prefixo + partes.join("/");
      if (partes.length) lista.set(real.toLowerCase(), { arquivo: arquivo, real: real });
    });
    lista.nome = normalizar(arquivos[0].webkitRelativePath || "").split("/")[0] || "pasta";
    podeGravar = false;
    precisaPermissao = false;
  }

  async function pastaDe(caminho, criar) {
    let atual = raiz;
    const pedacos = caminho.split("/").filter(Boolean);
    for (const pedaco of pedacos) {
      try {
        atual = await atual.getDirectoryHandle(pedaco, { create: !!criar });
      } catch (falha) {
        // Pen drive FAT/exFAT nao liga para maiusculas: procura sem ligar.
        const achado = (await filhos(atual)).get(pedaco.toLowerCase());
        if (!achado || achado.kind !== "directory") return null;
        atual = achado;
      }
    }
    return atual;
  }

  function semPrefixo(caminho) {
    caminho = normalizar(caminho);
    if (!prefixo) return caminho;
    return caminho.toLowerCase().startsWith(prefixo) ? caminho.slice(prefixo.length) : null;
  }

  // O File (com .name, .size e .arrayBuffer()) ou null.
  async function arquivo(caminho) {
    caminho = normalizar(caminho);
    if (lista) return (lista.get(caminho.toLowerCase()) || {}).arquivo || null;
    if (!raiz || precisaPermissao) return null;
    const relativo = semPrefixo(caminho);
    if (relativo === null) return null;
    const corte = relativo.lastIndexOf("/");
    const pasta = await pastaDe(corte < 0 ? "" : relativo.slice(0, corte), false);
    if (!pasta) return null;
    const nome = relativo.slice(corte + 1);
    try {
      return await (await pasta.getFileHandle(nome)).getFile();
    } catch (falha) {
      const achado = (await filhos(pasta)).get(nome.toLowerCase());
      return achado && achado.kind === "file" ? achado.getFile() : null;
    }
  }

  // [{nome, pasta: bool}] de uma pasta ("jogos/pessoais/NES").
  async function listar(caminho) {
    caminho = normalizar(caminho).replace(/\/$/, "");
    if (lista) {
      const base = caminho ? caminho.toLowerCase() + "/" : "";
      const vistos = new Map();
      for (const [chave, item] of lista) {
        if (!chave.startsWith(base)) continue;
        const resto = item.real.slice(base.length);
        const corte = resto.indexOf("/");
        const nome = corte < 0 ? resto : resto.slice(0, corte);
        if (!vistos.has(nome.toLowerCase())) vistos.set(nome.toLowerCase(), { nome: nome, pasta: corte >= 0 });
      }
      return Array.from(vistos.values());
    }
    if (!raiz || precisaPermissao) return [];
    const relativo = semPrefixo(caminho);
    if (relativo === null) return [];
    const pasta = await pastaDe(relativo, false);
    if (!pasta) return [];
    const itens = [];
    for await (const [nome, item] of pasta.entries()) itens.push({ nome: nome, pasta: item.kind === "directory" });
    return itens;
  }

  async function lerTexto(caminho) {
    const f = await arquivo(caminho);
    return f ? f.text() : null;
  }

  // Grava no pen drive (so no Chrome e no Edge, com a permissao de gravar).
  // O createWritable grava num arquivo ao lado e so troca no close: o mesmo
  // cuidado do gravar_texto_atomico do Windows, se o pen drive sair no meio.
  async function gravar(caminho, dados) {
    if (!raiz || !podeGravar) return false;
    const relativo = semPrefixo(caminho);
    if (relativo === null) return false;
    const corte = relativo.lastIndexOf("/");
    const pasta = await pastaDe(corte < 0 ? "" : relativo.slice(0, corte), true);
    if (!pasta) return false;
    const alvo = await pasta.getFileHandle(relativo.slice(corte + 1), { create: true });
    const escrita = await alvo.createWritable();
    await escrita.write(dados);
    await escrita.close();
    return true;
  }

  async function apagarArquivo(caminho) {
    if (!raiz || !podeGravar) return false;
    const relativo = semPrefixo(caminho);
    if (relativo === null) return false;
    const corte = relativo.lastIndexOf("/");
    const pasta = await pastaDe(corte < 0 ? "" : relativo.slice(0, corte), false);
    if (!pasta) return false;
    try {
      await pasta.removeEntry(relativo.slice(corte + 1));
      return true;
    } catch (falha) {
      return false;
    }
  }

  return { iniciar: iniciar, escolher: escolher, liberar: liberar, situacao: situacao, arquivo: arquivo,
           listar: listar, lerTexto: lerTexto, gravar: gravar, apagarArquivo: apagarArquivo,
           normalizar: normalizar, temSeletor: temSeletor };
})();
