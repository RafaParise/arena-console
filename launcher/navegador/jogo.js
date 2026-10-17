"use strict";
// --------------------------------------------------------------------------
// ARENA no navegador: o quadro do jogo (item 12 do plano de 15/10/2026).
//
// No Chromebook o ARENA roda dentro do proprio Chrome (ARENA-CHROMEBOOK.html).
// Cada jogo abre neste quadro (um iframe), com o RetroArch 1.22.2 compilado
// para WebAssembly: o mesmo RetroArch do Windows, com o mesmo menu (Esc) e as
// mesmas teclas (F2 salva, F4 carrega, F10 fecha). Quando o jogo fecha, a
// tela do ARENA apaga o quadro inteiro, e o navegador devolve toda a memoria
// do emulador de uma vez (um Chromebook da escola tem 4 GB).
//
// A conversa com a tela e' por mensagens (postMessage), porque de file:// o
// Chrome trata cada arquivo como de outra origem:
//   tela -> quadro: "abrir" (nucleo, jogo, configuracao, saves, BIOS),
//                   "sair", "comando", "medir"
//   quadro -> tela: "pronto", "rodando", "guardados" (saves e estados que
//                   mudaram), "fim", "erro", "medida"
// --------------------------------------------------------------------------
(function () {
  const RAIZ = "/home/web_user/retroarch";
  const USUARIO = RAIZ + "/userdata";
  const PASTA_JOGOS = "/jogos";
  // As pastas que voltam para a tela quando mudam: os saves (a memoria do
  // cartucho) e os estados (F2). O resto do quadro some quando o jogo fecha.
  const PASTAS_GUARDADAS = ["saves", "states"];
  const SEGUNDOS_ENTRE_COPIAS = 10;
  const LINHAS_DO_REGISTRO = 400;

  const tela = window.parent;
  const canvas = document.getElementById("canvas");
  const registro = [];
  const contagem = { voltas: 0, imagens: 0 };
  let modulo = null;
  let marcas = new Map();         // caminho -> "tamanho:hora" do que a tela ja tem
  let relogio = null;
  let terminou = false;
  let saindo = false;

  function avisar(mensagem, transferir) {
    tela.postMessage(Object.assign({ arena: "jogo" }, mensagem), "*", transferir || []);
  }

  function anotar(texto) {
    registro.push(String(texto));
    if (registro.length > LINHAS_DO_REGISTRO) registro.splice(0, registro.length - LINHAS_DO_REGISTRO);
  }

  // Conta as voltas do laco do RetroArch (um quadro do jogo por volta) e as
  // imagens que o nucleo manda para a placa: e' assim que o "Testar este
  // Chromebook" sabe se o jogo roda na velocidade certa.
  const pedirQuadro = window.requestAnimationFrame.bind(window);
  window.requestAnimationFrame = function (funcao) {
    return pedirQuadro(function (hora) { contagem.voltas++; funcao(hora); });
  };
  for (const Contexto of [window.WebGLRenderingContext, window.WebGL2RenderingContext]) {
    if (!Contexto) continue;
    for (const nome of ["texSubImage2D", "texImage2D"]) {
      const original = Contexto.prototype[nome];
      Contexto.prototype[nome] = function () { contagem.imagens++; return original.apply(this, arguments); };
    }
  }

  function carregarScript(endereco) {
    return new Promise(function (pronto, falhou) {
      const script = document.createElement("script");
      script.src = endereco;
      script.onload = pronto;
      script.onerror = function () { falhou(new Error("Não achei " + endereco + " na pasta do ARENA.")); };
      document.head.appendChild(script);
    });
  }

  function deBase64(texto) {
    if (Uint8Array.fromBase64) return Uint8Array.fromBase64(texto);
    const binario = atob(texto);
    const bytes = new Uint8Array(binario.length);
    for (let i = 0; i < binario.length; i++) bytes[i] = binario.charCodeAt(i);
    return bytes;
  }

  async function descompactar(bytes) {
    const fluxo = new Blob([bytes]).stream().pipeThrough(new DecompressionStream("gzip"));
    return new Uint8Array(await new Response(fluxo).arrayBuffer());
  }

  // Cria a pasta e as de cima dela (o FS do Emscripten nao tem "mkdir -p").
  function criarPasta(FS, caminho) {
    let atual = "";
    for (const parte of caminho.split("/").filter(Boolean)) {
      atual += "/" + parte;
      try { FS.mkdir(atual); } catch (falha) { /* ja existe */ }
    }
  }

  function escrever(FS, caminho, dados) {
    criarPasta(FS, caminho.slice(0, caminho.lastIndexOf("/")));
    FS.writeFile(caminho, dados instanceof ArrayBuffer ? new Uint8Array(dados) : dados);
  }

  // Todos os arquivos das pastas guardadas: [[caminho relativo, stat]].
  function listarGuardados(FS) {
    const achados = [];
    function varrer(pasta, relativo) {
      let nomes;
      try { nomes = FS.readdir(pasta); } catch (falha) { return; }
      for (const nome of nomes) {
        if (nome === "." || nome === "..") continue;
        const caminho = pasta + "/" + nome;
        const info = FS.stat(caminho);
        if (FS.isDir(info.mode)) varrer(caminho, relativo + nome + "/");
        else achados.push([relativo + nome, info]);
      }
    }
    for (const pasta of PASTAS_GUARDADAS) varrer(USUARIO + "/" + pasta, pasta + "/");
    return achados;
  }

  function marcaDe(info) {
    return info.size + ":" + (info.mtime instanceof Date ? info.mtime.getTime() : info.mtime);
  }

  // Manda para a tela so o que mudou desde a ultima copia.
  function copiarGuardados(final) {
    if (!modulo) return 0;
    const FS = modulo.FS;
    if (!terminou) {
      try { modulo._cmd_savefiles(); } catch (falha) { /* nucleo sem save: nada a gravar */ }
    }
    const arquivos = [];
    const transferir = [];
    for (const [caminho, info] of listarGuardados(FS)) {
      const marca = marcaDe(info);
      if (marcas.get(caminho) === marca) continue;
      const dados = FS.readFile(USUARIO + "/" + caminho);
      marcas.set(caminho, marca);
      arquivos.push({ caminho: caminho, dados: dados.buffer });
      transferir.push(dados.buffer);
    }
    if (arquivos.length || final) avisar({ tipo: "guardados", arquivos: arquivos, final: !!final }, transferir);
    return arquivos.length;
  }

  function acabou(motivo) {
    if (terminou) return;
    terminou = true;
    clearInterval(relogio);
    try { copiarGuardados(true); } catch (falha) { anotar("[ARENA] copia final falhou: " + falha); }
    avisar({ tipo: "fim", motivo: motivo || "fechou", registro: registro.slice(-60) });
  }

  async function abrir(pedido) {
    const inicio = performance.now();
    const nucleo = String(pedido.nucleo || "");
    if (!/^[a-z0-9_]+$/.test(nucleo)) throw new Error("Núcleo desconhecido: " + nucleo);
    avisar({ tipo: "carregando", etapa: "nucleo" });
    await carregarScript("nucleos/" + nucleo + ".js");
    await carregarScript("nucleos/" + nucleo + ".wasm.js");
    const fabrica = (window.ARENA_NUCLEOS || {})[nucleo];
    const compactado = (window.ARENA_WASM_GZ || {})[nucleo];
    if (!fabrica || !compactado) throw new Error("O núcleo " + nucleo + " veio incompleto.");
    const wasm = await descompactar(deBase64(compactado));
    delete window.ARENA_WASM_GZ[nucleo];        // o texto de base64 nao e' mais preciso
    const nucleoPronto = performance.now();

    modulo = await fabrica({
      noInitialRun: true,
      canvas: canvas,
      wasmBinary: wasm,
      print: anotar,
      printErr: anotar,
      preRun: [function (m) { m.ENV.LIBRARY_PATH = RAIZ + "/cores/" + nucleo + "_libretro.core"; }],
      retroArchExit: function () { acabou("fechou"); },
      onAbort: function (motivo) {
        avisar({ tipo: "erro", texto: "O emulador parou: " + motivo, registro: registro.slice(-60) });
        acabou("parou");
      },
    });
    const FS = modulo.FS;
    criarPasta(FS, RAIZ + "/cores");
    FS.writeFile(RAIZ + "/cores/" + nucleo + "_libretro.core", new Uint8Array());
    for (const pasta of ["saves", "states", "system", "screenshots", "cheats", "remaps"]) criarPasta(FS, USUARIO + "/" + pasta);
    criarPasta(FS, PASTA_JOGOS);

    for (const arquivo of pedido.arquivos || []) escrever(FS, PASTA_JOGOS + "/" + arquivo.nome, arquivo.dados);
    for (const arquivo of pedido.sistema || []) escrever(FS, USUARIO + "/system/" + arquivo.caminho, arquivo.dados);
    for (const arquivo of pedido.guardados || []) {
      escrever(FS, USUARIO + "/" + arquivo.caminho, arquivo.dados);
    }
    // O que veio da tela ja esta guardado la: so volta se o jogo mudar.
    marcas = new Map(listarGuardados(FS).map(function (par) { return [par[0], marcaDe(par[1])]; }));

    // A configuracao vem da tela (as mesmas opcoes do ARENA do Windows); as
    // pastas sao deste quadro e vao por ultimo, para valer sempre.
    const pastas = [
      'savefile_directory = "' + USUARIO + '/saves"',
      'savestate_directory = "' + USUARIO + '/states"',
      'system_directory = "' + USUARIO + '/system"',
      'screenshot_directory = "' + USUARIO + '/screenshots"',
      'cheat_database_path = "' + USUARIO + '/cheats"',
      'input_remapping_directory = "' + USUARIO + '/remaps"',
      'core_options_path = "' + USUARIO + '/retroarch-core-options.cfg"',
      'global_core_options = "true"',
      'config_save_on_exit = "false"',
    ];
    FS.writeFile(USUARIO + "/retroarch.cfg", String(pedido.configuracao || "") + "\n" + pastas.join("\n") + "\n");
    FS.writeFile(USUARIO + "/retroarch-core-options.cfg", String(pedido.opcoes || ""));

    const principal = String(pedido.principal || ((pedido.arquivos || [])[0] || {}).nome || "");
    canvas.focus();
    contagem.voltas = 0;
    contagem.imagens = 0;
    modulo.callMain(["-c", USUARIO + "/retroarch.cfg", PASTA_JOGOS + "/" + principal]);
    relogio = setInterval(function () {
      try { copiarGuardados(false); } catch (falha) { anotar("[ARENA] copia falhou: " + falha); }
    }, SEGUNDOS_ENTRE_COPIAS * 1000);
    avisar({ tipo: "rodando", tempos: {
      nucleo_ms: Math.round(nucleoPronto - inicio),
      abrir_ms: Math.round(performance.now() - inicio),
    } });
  }

  // O mesmo que o aluno faria no teclado: o ARENA do Windows usa estas
  // teclas (servidor\arena.py, BASE_COMUM).
  const COMANDOS = {
    salvar_estado: "_cmd_save_state",
    carregar_estado: "_cmd_load_state",
    pausar: "_cmd_pause",
    continuar: "_cmd_unpause",
    menu: "_cmd_toggle_menu",
    reiniciar: "_cmd_reset",
  };

  function sair() {
    if (saindo || terminou) return;
    saindo = true;
    try { copiarGuardados(false); } catch (falha) { anotar("[ARENA] copia falhou: " + falha); }
    try {
      modulo.EmscriptenSendCommand("QUIT");
    } catch (falha) {
      acabou("fechou");
      return;
    }
    // Se o RetroArch nao fechar sozinho em 3 s, a tela fecha o quadro mesmo
    // assim: os saves ja foram copiados acima.
    setTimeout(function () { acabou("fechou"); }, 3000);
  }

  window.addEventListener("message", function (evento) {
    if (evento.source !== tela) return;
    const pedido = evento.data || {};
    if (pedido.tipo === "abrir" && !modulo) {
      abrir(pedido).catch(function (falha) {
        avisar({ tipo: "erro", texto: String(falha && falha.message || falha), registro: registro.slice(-60) });
      });
    } else if (pedido.tipo === "sair") {
      sair();
    } else if (pedido.tipo === "comando" && modulo && COMANDOS[pedido.nome]) {
      modulo[COMANDOS[pedido.nome]]();
    } else if (pedido.tipo === "foco") {
      canvas.focus();
    } else if (pedido.tipo === "medir") {
      avisar({ tipo: "medida", voltas: contagem.voltas, imagens: contagem.imagens, agora: performance.now(),
               registro: pedido.registro ? registro.slice(-LINHAS_DO_REGISTRO) : undefined });
    }
  });

  window.addEventListener("error", function (evento) {
    anotar("[JS] " + evento.message);
  });
  // O navegador fecha a aba ou a tela some: ultima copia dos saves.
  window.addEventListener("pagehide", function () { if (!terminou) copiarGuardados(true); });

  avisar({ tipo: "pronto" });
})();
