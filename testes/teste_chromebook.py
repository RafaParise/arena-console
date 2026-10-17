# -*- coding: utf-8 -*-
r"""O ARENA no Chromebook: a versao do navegador (item 12 do plano de 15/10/2026).

Pedido do Rafael (15/10/2026): "o ARENA deve ser compativel se possivel com
Chromebooks que tem na escola (...) Se for melhor, mais otimizado e leve crie
uma versao para Chromebook". O Chromebook da escola e' gerenciado: sem Linux e
sem instalar programa. Entao o ARENA roda dentro do proprio Chrome
(ARENA-CHROMEBOOK.html), com a mesma tela, o servidor dentro da pagina
(launcher\navegador) e o mesmo RetroArch 1.22.2, compilado para WebAssembly.

Numa COPIA do ARENA (testes\copia_do_arena.py; nada do ARENA de verdade e'
tocado), com os 10 jogos livres de testes\jogos_livres em jogos\pessoais e a
lista feita pelo indexador do Windows (dados\manifesto.js):

  A. ABERTO DO PEN DRIVE (file://), em cada navegador pronto (o Edge, o
     Chrome for Testing e o Firefox: testes\navegadores_de_teste.py):
     1. a tela abre pelo ARENA-CHROMEBOOK.html, sem erro de JavaScript;
     2. a lista tem os 11 jogos do pen drive (a do Windows, sem pedir
        permissao) e os 5 que vem junto, cada jogo uma vez so (o repetido
        fica o que vem junto, que abre sem pedir a pasta);
     3. o que so existe no Windows nao aparece (Amigos, Avancado, Emuladores);
     4. cada um dos 5 jogos que vem junto abre, roda (quadros por segundo
        medidos dentro do quadro do jogo) e volta para a tela;
     5. o F2 grava o estado, e ele aparece em "Saves e cheats" depois;
     6. o jogo do pen drive, antes de escolher a pasta, explica o que fazer.
  B. A PASTA DO PEN DRIVE (so Edge e Chrome, os que tem o seletor de pasta):
     a mesma tela por endereco local (http://127.0.0.1, ?navegador=1), com o
     seletor de pasta trocado por uma pasta do proprio navegador (o teste
     nao consegue clicar no seletor de verdade; os comandos sao os mesmos):
     7. escolher a pasta: a lista vem do dados\manifesto.json dela (e o
        repetido passa a ser o do pen drive, onde o save fica);
     8. o jogo do pen drive abre direto da pasta;
     9. o save vai para retroarch\saves\<nucleo> da pasta (o mesmo do Windows);
    10. pasta sem manifesto: o ARENA faz a lista sozinho;
    11. guardar um jogo neste navegador (sem pen drive): entra na lista e abre;
    12. o Testar este Chromebook mede um jogo de cada console e guarda o
        relatorio que o professor baixa.
  C. DESEMPENHO (Edge): se esta maquina tiver jogos de NES, Super Nintendo,
     Mega Drive e PS1 em jogos\pessoais, mede cada um com o processador
     normal e freado 4 vezes (o Chromebook da escola e' uns 3 vezes mais
     lento que o Ryzen). So mede: nao reprova.

Uso: servidor\python\python.exe testes\teste_chromebook.py [--saida=arquivo.json] [--so=edge,chrome,firefox]
        [--sem-desempenho]
"""
import functools
import http.server
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
import copia_do_arena as copia  # noqa: E402
import firefox_bidi  # noqa: E402
import limpeza  # noqa: E402
import navegadores_de_teste  # noqa: E402
import tela_sem_janela  # noqa: E402

LIVRES = os.path.join(AQUI, "jogos_livres")
PYTHON = os.path.join(RAIZ, "servidor", "python", "python.exe")
SEGUNDOS_DE_JOGO = 6

# Antes do JavaScript da pagina: guarda os erros (o mesmo do teste dos
# navegadores) e, so na parte B, troca o seletor de pasta por uma pasta do
# proprio navegador (OPFS), com os mesmos comandos de pasta.
ANTES_DA_PAGINA = r"""
  window.__teste = { erros: [] };
  const t = window.__teste;
  window.addEventListener("error", (e) => t.erros.push("erro: " + (e.message || e)));
  window.addEventListener("unhandledrejection",
    (e) => t.erros.push("promessa: " + ((e.reason && e.reason.message) || e.reason)));
  const original = console.error.bind(console);
  console.error = (...partes) => { t.erros.push("console: " + partes.map(String).join(" ")); original(...partes); };
"""
PASTA_FALSA = r"""
  window.__pastaFalsa = async (nome) => {
    const raiz = await navigator.storage.getDirectory();
    return raiz.getDirectoryHandle(nome || window.__nomeDaPasta || "ARENA", { create: true });
  };
  window.showDirectoryPicker = async () => window.__pastaFalsa();
  // Copia arquivos do servidor de teste para a pasta falsa (o "pen drive").
  window.__espelhar = async (nome, caminhos) => {
    const pasta = await window.__pastaFalsa(nome);
    for (const c of caminhos) {
      const resposta = await fetch("/" + c.split("/").map(encodeURIComponent).join("/"));
      if (!resposta.ok) throw new Error("faltou " + c);
      const partes = c.split("/");
      let atual = pasta;
      for (const p of partes.slice(0, -1)) atual = await atual.getDirectoryHandle(p, { create: true });
      const f = await atual.getFileHandle(partes[partes.length - 1], { create: true });
      const w = await f.createWritable();
      await w.write(await resposta.blob());
      await w.close();
    }
    return caminhos.length;
  };
  window.__lerDaPasta = async (nome, caminho) => {
    let atual = await window.__pastaFalsa(nome);
    const partes = caminho.split("/");
    try {
      for (const p of partes.slice(0, -1)) atual = await atual.getDirectoryHandle(p);
      const f = await (await atual.getFileHandle(partes[partes.length - 1])).getFile();
      return f.size;
    } catch (e) { return -1; }
  };
"""

# Um jogo pelo caminho do aluno: o cartao, o "Jogar agora", a medida, o F2 e
# o "Voltar ao ARENA". Devolve o que aconteceu.
JOGAR = r"""
(async (titulo, segundos, salvar) => {
  const esperar = (ms) => new Promise((ok) => setTimeout(ok, ms));
  const ate = async (condicao, s) => { const fim = Date.now() + s * 1000;
    while (Date.now() < fim) { if (condicao()) return true; await esperar(150); } return false; };
  const r = { titulo };
  const cartao = Array.from(document.querySelectorAll("#listaJogos .jogo"))
    .find((e) => (e.querySelector(".jogo-titulo, h3, strong") || e).textContent.includes(titulo));
  if (!cartao) { r.erro = "cartao nao achado"; return JSON.stringify(r); }
  (cartao.querySelector("button") || cartao).click();
  await esperar(300);
  const inicio = performance.now();
  document.getElementById("btnJogarSelecionado").click();
  r.abriu_camada = await ate(() => !!document.querySelector(".partida-navegador"), 5);
  r.rodando = await ate(() => ArenaPartida.rodando() || !ArenaPartida.aberto(), 40);
  if (!ArenaPartida.aberto()) {
    r.erro = (document.getElementById("recado").textContent || "") +
      ((ArenaRotas.estado.problema || {}).texto || "");
    return JSON.stringify(r);
  }
  r.abrir_s = Math.round((performance.now() - inicio) / 100) / 10;
  await esperar(2500);
  const a = await ArenaPartida.medir();
  await esperar(segundos * 1000);
  const b = await ArenaPartida.medir(true);
  if (a && b) {
    const s = (b.agora - a.agora) / 1000;
    r.quadros_s = Math.round((b.voltas - a.voltas) / s * 10) / 10;
    r.imagens_s = Math.round((b.imagens - a.imagens) / s * 10) / 10;
    r.erros_do_emulador = (b.registro || []).filter((l) => /\[ERROR\]/.test(l) && !/screen dimensions/.test(l)).slice(-4);
  }
  if (salvar) { ArenaPartida.comando("salvar_estado"); await esperar(1500); }
  const voltar = document.querySelector(".partida-navegador button[aria-label^='Fechar o jogo']");
  if (voltar) voltar.click();
  r.voltou = await ate(() => !document.querySelector(".partida-navegador"), 12);
  return JSON.stringify(r);
})
"""


def esperar(nav, expressao, segundos=20):
    fim = time.monotonic() + segundos
    while time.monotonic() < fim:
        try:
            if nav.avaliar(expressao):
                return True
        except OSError:
            pass
        time.sleep(0.25)
    return False


def jogar(nav, titulo, segundos=SEGUNDOS_DE_JOGO, salvar=False):
    return json.loads(nav.avaliar("(%s)(%s, %d, %s)" % (JOGAR.strip(), json.dumps(titulo), segundos,
                                                       "true" if salvar else "false")))


def montar_copia(destino):
    """A copia: servidor, tela (com launcher\\navegador inteiro), os 10 jogos
    livres em jogos\\pessoais, o ARENA-CHROMEBOOK.html e a lista feita pelo
    indexador do Windows (dados\\manifesto.json e .js)."""
    jogos = {}
    for pasta in sorted(os.listdir(LIVRES)):
        caminho = os.path.join(LIVRES, pasta)
        if os.path.isdir(caminho) and pasta != "licencas":
            jogos[pasta] = [os.path.join(caminho, n) for n in os.listdir(caminho)]
    copia.montar(destino, [], jogos)
    # Um jogo que so esta no pen drive (os outros 5 de console do navegador
    # tambem vem junto, e a lista mostra cada jogo uma vez so).
    shutil.copyfile(os.path.join(LIVRES, "CHIP-8", "slipperyslope.ch8"),
                    os.path.join(destino, "jogos", "pessoais", "CHIP-8", "escorregador.ch8"))
    shutil.copyfile(os.path.join(RAIZ, "ARENA-CHROMEBOOK.html"), os.path.join(destino, "ARENA-CHROMEBOOK.html"))
    r = subprocess.run([PYTHON, os.path.join(destino, "servidor", "indexador.py")], cwd=destino,
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
    if not os.path.isfile(os.path.join(destino, "dados", "manifesto.js")):
        raise OSError("o indexador da copia nao gravou o dados\\manifesto.js:\n" + r.stdout[-800:] + r.stderr[-800:])


def parte_a(nav, endereco):
    """Aberto do pen drive (file://)."""
    r = {}
    nav.antes_de_cada_pagina(ANTES_DA_PAGINA)
    nav.abrir(endereco, largura=1366, altura=768, espera=1)
    inicio = time.monotonic()
    r["lista_pronta"] = esperar(nav, "document.querySelectorAll('#listaJogos .jogo').length >= 11", 40)
    r["pronta_s"] = round(time.monotonic() - inicio, 1)
    nav.avaliar("document.getElementById('campoApelidoInicial').value = 'teste'; "
                "document.getElementById('btnSalvarApelido').click(); 1")
    time.sleep(0.8)
    r["no_navegador"] = nav.avaliar("document.documentElement.dataset.navegador === 'true'")
    r["origens"] = nav.avaliar("ArenaRotas.estado.jogos.reduce((c, j) => (c[j.origem] = (c[j.origem] || 0) + 1, c), {})")
    r["manifesto"] = nav.avaliar("ArenaRotas.estado.manifesto ? (ArenaRotas.estado.manifesto.feito_no_navegador ? 'aqui' : 'windows') : null")
    r["escondidos"] = nav.avaliar(
        "['btnAmigos', 'btnSincronizar', 'btnAcervo'].every((id) => getComputedStyle(document.getElementById(id)).display === 'none')"
        " && ['avancado', 'emuladores', 'controles'].every((a) => getComputedStyle(document.querySelector("
        "'#gavetaAjustes .aba[data-aba=\"' + a + '\"]')).display === 'none')")
    r["jogos"] = []
    for titulo in ("Evade", "Slippery Slope", "Skip Ahead", "Intervallo", "Baguel"):
        resultado = jogar(nav, titulo, salvar=(titulo == "Slippery Slope"))
        r["jogos"].append(resultado)
        print("    %-15s %s" % (titulo, resultado.get("erro") or "%s q/s, abriu em %s s, voltou %s"
                                % (resultado.get("quadros_s"), resultado.get("abrir_s"), resultado.get("voltou"))))
    r["estado_guardado"] = nav.avaliar(
        "(async () => { const j = ArenaRotas.estado.jogos.find((x) => x.titulo === 'Slippery Slope' && x.origem === 'vem_com');"
        " const d = await (await fetch('/api/jogo?id=' + encodeURIComponent(j.id))).json();"
        " return d.estados && d.estados[0] && d.estados[0].existe; })()")
    # O jogo do pen drive sem a pasta escolhida: o recado tem de dizer o que fazer.
    r["sem_pasta"] = nav.avaliar(
        "(async () => { const j = ArenaRotas.estado.jogos.find((x) => x.origem === 'pessoais' && x.plataforma === 'chip8');"
        " const resposta = await fetch('/api/jogar', {method: 'POST', headers: {'Content-Type': 'application/json'},"
        " body: JSON.stringify({jogo_id: j.id, apelido: 'teste'})}); const d = await resposta.json();"
        " return d.erro || 'abriu'; })()")
    r["erros"] = nav.avaliar("window.__teste.erros")
    return r


def conferir_a(r):
    jogos = r.get("jogos") or []
    return [
        ("a tela abre pelo ARENA-CHROMEBOOK.html, sem erro de JavaScript",
         r.get("lista_pronta") is True and r.get("no_navegador") is True and r.get("erros") == []),
        ("a lista: os 11 do pen drive (a do Windows) e os 5 que vem junto, sem repetir",
         (r.get("origens") or {}).get("pessoais") == 6 and (r.get("origens") or {}).get("vem_com") == 5
         and r.get("manifesto") == "windows"),
        ("o que so existe no Windows nao aparece", r.get("escondidos") is True),
        ("os 5 jogos que vem junto abrem, rodam e voltam",
         len(jogos) == 5 and all(j.get("rodando") and j.get("voltou") and (j.get("quadros_s") or 0) >= 30
                                 for j in jogos)),
        ("o F2 grava o estado e ele aparece em Saves e cheats", r.get("estado_guardado") is True),
        ("o jogo do pen drive sem a pasta explica o que fazer", "escolha a pasta do ARENA" in (r.get("sem_pasta") or "")),
    ]


class _Silencioso(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):      # noqa: A002 (o nome vem da classe de base)
        pass


def servir(pasta):
    servidor = http.server.ThreadingHTTPServer(("127.0.0.1", 0),
                                               functools.partial(_Silencioso, directory=pasta))
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    return servidor


def arquivos_da_copia(destino, *pastas):
    """Os caminhos (com /) de tudo dentro de 'pastas' da copia."""
    achados = []
    for pasta in pastas:
        for atual, _sub, nomes in os.walk(os.path.join(destino, pasta)):
            for nome in nomes:
                achados.append(os.path.relpath(os.path.join(atual, nome), destino).replace("\\", "/"))
    return achados


def parte_b(nav, porta, destino):
    """A pasta do pen drive, pelo endereco local, com a pasta falsa."""
    r = {}
    nav.antes_de_cada_pagina(ANTES_DA_PAGINA + PASTA_FALSA)
    nav.abrir("http://127.0.0.1:%d/launcher/index.html?navegador=1" % porta, largura=1366, altura=768, espera=1)
    esperar(nav, "document.querySelectorAll('#listaJogos .jogo').length >= 5", 40)
    nav.avaliar("document.getElementById('campoApelidoInicial').value = 'teste'; "
                "document.getElementById('btnSalvarApelido').click(); 1")
    caminhos = arquivos_da_copia(destino, "jogos", "dados")
    r["copiados"] = nav.avaliar("window.__espelhar('ARENA', %s)" % json.dumps(caminhos))
    nav.avaliar("document.getElementById('btnPastaArena').click(); 1")
    r["pasta_liberada"] = esperar(nav, "ArenaPasta.situacao().tem && !ArenaPasta.situacao().precisa_permissao", 15)
    esperar(nav, "ArenaRotas.estado.jogos.filter((j) => j.origem === 'pessoais').length >= 11", 15)
    r["origens"] = nav.avaliar("ArenaRotas.estado.jogos.reduce((c, j) => (c[j.origem] = (c[j.origem] || 0) + 1, c), {})")
    r["manifesto"] = nav.avaliar("ArenaRotas.estado.manifesto && !ArenaRotas.estado.manifesto.feito_no_navegador")
    r["aviso_some"] = esperar(nav, "document.getElementById('avisoPasta').hidden", 10)
    # O jogo do pen drive (o Slippery Slope de jogos\pessoais\CHIP-8), com F2.
    nav.avaliar("document.getElementById('campoBusca').value = ''; 1")
    # O "arquivo" do manifesto do Windows vem com barra invertida.
    jogo = nav.avaliar("(() => { const j = ArenaRotas.estado.jogos.find((x) => x.origem === 'pessoais' && "
                       "x.arquivo.replace(/\\\\/g, '/').endsWith('/slipperyslope.ch8'));"
                       " return j ? j.id : null; })()")
    r["jogo_do_pen"] = json.loads(nav.avaliar(
        "(async () => { const r = {}; const esperar = (ms) => new Promise((ok) => setTimeout(ok, ms));"
        " const resposta = await fetch('/api/jogar', {method: 'POST', headers: {'Content-Type': 'application/json'},"
        " body: JSON.stringify({jogo_id: %s, apelido: 'teste'})}); r.resposta = await resposta.json();"
        " const fim = Date.now() + 30000; while (Date.now() < fim && !ArenaPartida.rodando()) await esperar(150);"
        " r.rodando = ArenaPartida.rodando(); await esperar(2500); ArenaPartida.comando('salvar_estado'); await esperar(1500);"
        " ArenaPartida.sair(); const fim2 = Date.now() + 12000; while (Date.now() < fim2 && ArenaPartida.aberto()) await esperar(150);"
        " r.voltou = !ArenaPartida.aberto(); await esperar(800); return JSON.stringify(r); })()" % json.dumps(jogo)))
    r["save_no_pen"] = nav.avaliar("window.__lerDaPasta('ARENA', 'retroarch/saves/JAXE/slipperyslope.srm')")
    r["estado_no_pen"] = nav.avaliar("window.__lerDaPasta('ARENA', 'retroarch/states/JAXE/slipperyslope.state')")
    # Pasta sem manifesto: so os jogos. O ARENA faz a lista sozinho.
    so_jogos = [c for c in caminhos if c.startswith("jogos/")]
    nav.avaliar("window.__nomeDaPasta = 'SEM-LISTA'; 1")
    nav.avaliar("window.__espelhar('SEM-LISTA', %s)" % json.dumps(so_jogos))
    nav.avaliar("document.getElementById('btnOutraPasta').click(); 1")
    esperar(nav, "ArenaPasta.situacao().nome === 'SEM-LISTA'", 10)
    esperar(nav, "ArenaRotas.estado.manifesto && ArenaRotas.estado.manifesto.feito_no_navegador", 15)
    r["lista_feita_aqui"] = nav.avaliar(
        "ArenaRotas.estado.manifesto && ArenaRotas.estado.manifesto.feito_no_navegador ? ArenaRotas.estado.manifesto.total : null")
    # Guardar um jogo neste navegador (Ajustes -> Maquina), para o Chromebook
    # sem pen drive: um jogo que nao esta na pasta.
    guardado = os.path.join(destino, "Guardado Aqui.ch8")
    shutil.copyfile(os.path.join(LIVRES, "CHIP-8", "slipperyslope.ch8"), guardado)
    raiz = nav.comando("DOM.getDocument")["root"]["nodeId"]
    campo = nav.comando("DOM.querySelector", nodeId=raiz, selector="#campoGuardarJogo")["nodeId"]
    nav.comando("DOM.setFileInputFiles", files=[guardado], nodeId=campo)
    r["guardado"] = esperar(nav, "ArenaRotas.estado.jogos.some((j) => j.origem === 'navegador')", 10)
    if r["guardado"]:
        r["guardado_abre"] = jogar(nav, "Guardado Aqui", segundos=3)
    # Testar este Chromebook: um jogo de cada console, a medida e o relatorio.
    nav.avaliar("document.getElementById('btnTestarChromebook').click(); 1")
    esperar(nav, "(() => { const l = Array.from(document.querySelectorAll('#listaTesteChromebook li'));"
                 " return l.length > 1 && /^(Pronto|O teste parou)/.test(l[l.length - 1].textContent); })()", 300)
    r["teste_do_chromebook"] = nav.avaliar(
        "ArenaBanco.ler('coisas', 'teste_do_chromebook').then((t) => t ? t.jogos.map((j) => [j.console, j.quadros_s || j.erro]) : null)")
    r["erros"] = nav.avaliar("window.__teste.erros")
    return r


def conferir_b(r):
    jogo = r.get("jogo_do_pen") or {}
    return [
        ("escolher a pasta: a lista vem do manifesto.json dela",
         r.get("pasta_liberada") is True and r.get("manifesto") is True and (r.get("origens") or {}).get("pessoais") == 11
         and not (r.get("origens") or {}).get("vem_com") and r.get("aviso_some") is True),
        ("o jogo do pen drive abre direto da pasta", jogo.get("rodando") is True and jogo.get("voltou") is True),
        ("o save vai para retroarch\\saves\\<nucleo> da pasta", (r.get("save_no_pen") or -1) > 0
         and (r.get("estado_no_pen") or -1) > 0),
        ("pasta sem manifesto: o ARENA faz a lista sozinho", r.get("lista_feita_aqui") == 11),
        ("guardar um jogo neste navegador: ele entra na lista e abre", r.get("guardado") is True
         and (r.get("guardado_abre") or {}).get("rodando") is True and (r.get("guardado_abre") or {}).get("voltou") is True),
        ("Testar este Chromebook mede um jogo de cada console e guarda o relatório",
         len(r.get("teste_do_chromebook") or []) >= 5
         and all(isinstance(q, (int, float)) and q >= 30 for _c, q in r.get("teste_do_chromebook") or [])),
        ("sem erro de JavaScript", r.get("erros") == []),
    ]


def jogos_desta_maquina():
    """Um jogo de cada console pesado, se o ARENA de verdade tiver (so para
    medir; nunca sai desta maquina: vai para a copia temporaria)."""
    pessoais = os.path.join(RAIZ, "jogos", "pessoais")
    escolhas = [("NES", ".nes"), ("Super Nintendo", ".smc"), ("Super Nintendo", ".sfc"), ("Mega Drive", ".md"),
                ("Game Boy Advance", ".gba"), ("PS1", ".chd")]
    achados = {}
    for pasta, extensao in escolhas:
        caminho = os.path.join(pessoais, pasta)
        if pasta in achados or not os.path.isdir(caminho):
            continue
        for nome in sorted(os.listdir(caminho)):
            if nome.lower().endswith(extensao) and os.path.getsize(os.path.join(caminho, nome)) < 700 * 1048576:
                achados[pasta] = os.path.join(caminho, nome)
                break
    return achados


def parte_c(nav, endereco, nomes):
    """Desempenho dos consoles pesados, com o processador normal e freado."""
    resultados = []
    nav.antes_de_cada_pagina(ANTES_DA_PAGINA)
    for lento in (1, 4):
        nav.comando("Emulation.setCPUThrottlingRate", rate=1)
        nav.abrir(endereco, largura=1366, altura=768, espera=1)
        esperar(nav, "document.querySelectorAll('#listaJogos .jogo').length >= 5", 40)
        nav.avaliar("document.getElementById('campoApelidoInicial').value = 'teste'; "
                    "document.getElementById('btnSalvarApelido').click(); 1")
        for console_, arquivo in nomes.items():
            jogo = nav.avaliar("(() => { const j = ArenaRotas.estado.jogos.find((x) => "
                               "x.arquivo.replace(/\\\\/g, '/').endsWith(%s));"
                               " return j ? j.titulo : null; })()" % json.dumps("/" + os.path.basename(arquivo)))
            if not jogo:
                continue
            nav.comando("Emulation.setCPUThrottlingRate", rate=lento)
            r = jogar(nav, jogo, segundos=8)
            nav.comando("Emulation.setCPUThrottlingRate", rate=1)
            r.update({"console": console_, "processador_freado": lento})
            resultados.append(r)
            print("    x%d %-16s %-36s %s" % (lento, console_, jogo[:36], r.get("erro") or "%s q/s" % r.get("quadros_s")))
    return resultados


def argumento(nome, padrao):
    for a in sys.argv[1:]:
        if a.startswith("--%s=" % nome):
            return a.split("=", 1)[1]
    return padrao


def main():
    saida = argumento("saida", os.path.join(tempfile.gettempdir(), "teste_chromebook.json"))
    lista = navegadores_de_teste.prontos()
    so = argumento("so", "")
    if so:
        lista = [n for n in lista if n[0] in so.split(",")]
    if not os.path.isfile(os.path.join(RAIZ, "launcher", "navegador", "nucleos", "lista.js")):
        print("Faltam os nucleos do navegador: rode ferramentas\\preparar_nucleos_navegador.py.")
        return 2
    trabalho, destino = copia.nova_pasta()
    resultados = []
    servidor = None
    try:
        montar_copia(destino)
        endereco = "file:///" + os.path.join(destino, "ARENA-CHROMEBOOK.html").replace("\\", "/")
        for codigo, nome, programa, protocolo in lista:
            print("== %s: aberto do pen drive (file://)" % nome)
            abrir = (firefox_bidi.NavegadorFirefox(programa) if protocolo == "bidi"
                     else tela_sem_janela.Navegador(executavel=programa, tamanho=(1366, 768)))
            try:
                with abrir as nav:
                    r = parte_a(nav, endereco)
            except (OSError, ValueError, KeyError, TypeError) as falha:
                r = {"falha": str(falha)}
            r.update({"codigo": codigo, "navegador": nome, "parte": "A"})
            r["conferencias"] = conferir_a(r)
            resultados.append(r)
            for item, passou in r["conferencias"]:
                print("  [%s] %s" % ("OK" if passou else "FALHOU", item))
            if r.get("erros"):
                print("  erros:", r["erros"][:5])
            if r.get("falha"):
                print("  falha:", r["falha"])
        servidor = servir(destino)
        porta = servidor.server_address[1]
        for codigo, nome, programa, protocolo in lista:
            if protocolo != "cdp":
                continue
            print("== %s: a pasta do pen drive (http://127.0.0.1)" % nome)
            try:
                with tela_sem_janela.Navegador(executavel=programa, tamanho=(1366, 768)) as nav:
                    r = parte_b(nav, porta, destino)
            except (OSError, ValueError, KeyError, TypeError) as falha:
                r = {"falha": str(falha)}
            r.update({"codigo": codigo, "navegador": nome, "parte": "B"})
            r["conferencias"] = conferir_b(r)
            resultados.append(r)
            for item, passou in r["conferencias"]:
                print("  [%s] %s" % ("OK" if passou else "FALHOU", item))
            if r.get("erros"):
                print("  erros:", r["erros"][:5])
            if r.get("falha"):
                print("  falha:", r["falha"])
        desempenho = []
        nomes = {} if "--sem-desempenho" in sys.argv else jogos_desta_maquina()
        if nomes:
            for console_, arquivo in nomes.items():
                pasta = os.path.join(destino, "jogos", "pessoais", console_)
                os.makedirs(pasta, exist_ok=True)
                shutil.copyfile(arquivo, os.path.join(pasta, os.path.basename(arquivo)))
            subprocess.run([PYTHON, os.path.join(destino, "servidor", "indexador.py")], cwd=destino,
                           capture_output=True, timeout=300)
            print("== Desempenho no Edge (jogos desta maquina, numa copia temporaria)")
            with tela_sem_janela.Navegador(tamanho=(1366, 768)) as nav:
                nav.antes_de_cada_pagina(ANTES_DA_PAGINA + PASTA_FALSA)
                nav.abrir("http://127.0.0.1:%d/launcher/index.html?navegador=1" % porta, espera=1)
                esperar(nav, "document.querySelectorAll('#listaJogos .jogo').length >= 5", 40)
                nav.avaliar("window.__espelhar('ARENA', %s)" % json.dumps(arquivos_da_copia(destino, "jogos", "dados")))
                nav.avaliar("document.getElementById('btnPastaArena').click(); 1")
                esperar(nav, "ArenaPasta.situacao().tem", 15)
                desempenho = parte_c(nav, "http://127.0.0.1:%d/launcher/index.html?navegador=1" % porta, nomes)
        resultados.append({"parte": "C", "desempenho": desempenho, "conferencias": []})
    finally:
        if servidor:
            servidor.shutdown()
        limpeza.apagar_pasta(trabalho)
    with open(saida, "w", encoding="utf-8") as arquivo:
        json.dump({"data": time.strftime("%Y-%m-%d %H:%M"), "resultados": resultados}, arquivo,
                  ensure_ascii=False, indent=1)
    falhas = sum(1 for r in resultados for _item, passou in r["conferencias"] if not passou)
    total = sum(len(r["conferencias"]) for r in resultados)
    print()
    print("ARENA no Chromebook: %d de %d certos. Resultado: %s" % (total - falhas, total, saida))
    return 1 if falhas or not total else 0


if __name__ == "__main__":
    sys.exit(main())
