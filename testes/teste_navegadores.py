# -*- coding: utf-8 -*-
r"""A tela do ARENA em cada navegador: funciona igual e quanto pesa (item 11).

Pedido do Rafael (15/10/2026): "deve ser perfeitamente funcional assim como
e' no edge (...) preciso de testes para provar o desempenho em outros
navegadores, tem que ser compativel e otimizado com todos".

Numa COPIA do ARENA (testes\copia_do_arena.py: porta 8787, com os 10 jogos
livres de testes\jogos_livres; nada do ARENA de verdade e' tocado), o mesmo
roteiro em cada navegador pronto (testes\navegadores_de_teste.py: o Edge do
Windows, o Chrome for Testing e o Firefox, os dois de fonte oficial e sem
instalar nada), numa tela de 1366x768 como a do notebook da escola:

  CONFERE (cada um precisa passar em todos os navegadores):
    1. a tela fica pronta (o contador de jogos sai do 0) e mostra os 10;
    2. nenhum erro de JavaScript (erro, promessa recusada, console.error);
    3. nada vaza para os lados (sem barra de rolagem horizontal);
    4. Ajustes abre, e cada uma das 5 abas mostra o painel dela;
    5. a Escala da tela tem as 5 escolhas, e trocar grava no servidor;
    6. a lista "Abrir a tela em" tem o padrao e os instalados;
    7. a busca filtra a lista de jogos;
    8. clicar num jogo mostra os detalhes dele;
    9. o botao do tema troca o tema;
   10. a Biblioteca abre.
  MEDE: o tempo ate a tela ficar pronta, os quadros por segundo do fundo
  animado (3 s), a memoria e o processador do navegador com a tela parada
  (10 s). E tira a foto da tela de cada navegador.

O roteiro e' um JavaScript so (ROTEIRO), o mesmo em todos: clica e escolhe
como o aluno, pela propria pagina, sem depender do protocolo de cada
navegador (CDP no Edge e no Chrome; WebDriver BiDi no Firefox).

Uso: servidor\python\python.exe testes\teste_navegadores.py [--saida=arquivo.json] [--fotos=pasta]
        [--janela]
  --janela: cada navegador abre com janela de verdade, como o ARENA abre (o
  Edge e o Chrome em modo aplicativo, o Firefox numa janela comum). Sem ela,
  sem janela: o roteiro vale igual, mas a memoria e o processador nao --
  sem janela, cada navegador desenha de um jeito (as vezes sem a placa de
  video).
"""
import ctypes
import json
import os
import sys
import tempfile
import time
from ctypes import wintypes

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
import copia_do_arena as copia  # noqa: E402
import firefox_bidi  # noqa: E402
import limpeza  # noqa: E402
import navegadores_de_teste  # noqa: E402
import tela_sem_janela  # noqa: E402

LIVRES = os.path.join(AQUI, "jogos_livres")
ENDERECO = "http://127.0.0.1:%d/" % copia.PORTA

# Antes do JavaScript da pagina: guarda os erros, anota quando a lista de
# jogos aparece e conta os quadros desenhados (requestAnimationFrame).
ANTES_DA_PAGINA = r"""
  window.__teste = { erros: [], pronta: null, quadros: 0 };
  const t = window.__teste;
  window.addEventListener("error", (e) => t.erros.push("erro: " + (e.message || e)));
  window.addEventListener("unhandledrejection",
    (e) => t.erros.push("promessa: " + ((e.reason && e.reason.message) || e.reason)));
  const original = console.error.bind(console);
  console.error = (...partes) => { t.erros.push("console: " + partes.map(String).join(" ")); original(...partes); };
  const olhar = () => {
    const el = document.getElementById("lidoJogos");
    if (t.pronta === null && el && /[1-9]/.test(el.textContent)) t.pronta = performance.now();
  };
  new MutationObserver(olhar).observe(document, { subtree: true, childList: true, characterData: true });
  const contar = () => { t.quadros += 1; requestAnimationFrame(contar); };
  requestAnimationFrame(contar);
"""

# O roteiro: uma funcao assincrona que devolve o resultado de cada passo.
ROTEIRO = r"""
(async () => {
  const dormir = (ms) => new Promise((r) => setTimeout(r, ms));
  const visivel = (el) => !!el && !el.hidden && el.getClientRects().length > 0;
  const r = {};
  r.jogos = Number((document.getElementById("lidoJogos").textContent.match(/\d+/) || [0])[0]);
  r.cartoes = document.querySelectorAll("#listaJogos .jogo").length;
  r.sem_rolagem_lateral = document.documentElement.scrollWidth <= window.innerWidth + 1;

  document.getElementById("btnAjustes").click();
  await dormir(400);
  const ajustes = document.getElementById("gavetaAjustes");
  r.ajustes_abre = visivel(ajustes);
  r.abas = {};
  for (const aba of ajustes.querySelectorAll(".aba[data-aba]")) {
    aba.click();
    await dormir(250);
    const painel = ajustes.querySelector('.aba-conteudo[data-painel="' + aba.dataset.aba + '"]');
    r.abas[aba.dataset.aba] = visivel(painel);
  }
  ajustes.querySelector('.aba[data-aba="simples"]').click();
  await dormir(200);
  const escala = document.getElementById("listaEscalaTela");
  r.escalas = [...escala.options].map((o) => o.value);
  escala.value = "nitido";
  escala.dispatchEvent(new Event("change", { bubbles: true }));
  await dormir(600);
  const estado = await (await fetch("/api/estado", { cache: "no-store" })).json();
  r.escala_gravada = estado.config.escala_da_tela;
  r.navegadores = [...document.getElementById("listaNavegador").options].map((o) => o.value);
  escala.value = "automatico";
  escala.dispatchEvent(new Event("change", { bubbles: true }));
  await dormir(400);
  document.getElementById("btnAjustes").closest("body").querySelector("#gavetaAjustes").hidden = true;

  const busca = document.getElementById("campoBusca");
  const primeiro = document.querySelector("#listaJogos .jogo");
  // O titulo do jogo: o mesmo que o leitor de tela le ("Ver detalhes de ...").
  const nome = primeiro ? (primeiro.getAttribute("aria-label") || "").replace(/^Ver detalhes de /, "").trim() : "";
  r.busca_por = nome.slice(0, 5);
  busca.value = r.busca_por;
  busca.dispatchEvent(new Event("input", { bubbles: true }));
  await dormir(500);
  r.cartoes_na_busca = document.querySelectorAll("#listaJogos .jogo").length;
  busca.value = "";
  busca.dispatchEvent(new Event("input", { bubbles: true }));
  await dormir(500);

  const cartao = document.querySelector("#listaJogos .jogo");
  if (cartao) cartao.click();
  await dormir(400);
  r.detalhes_aparecem = visivel(document.getElementById("detalhesJogo")) &&
    document.getElementById("detalhesTitulo").textContent.trim().length > 0;

  const temaAntes = document.body.dataset.tema;
  document.getElementById("btnTema").click();
  await dormir(700);
  r.tema_troca = document.body.dataset.tema !== temaAntes;
  document.getElementById("btnTema").click();
  await dormir(700);

  document.getElementById("btnAcervo").click();
  await dormir(500);
  r.biblioteca_abre = visivel(document.getElementById("gavetaAcervo"));
  document.getElementById("gavetaAcervo").hidden = true;
  r.erros = window.__teste.erros.slice();
  return JSON.stringify(r);
})()
"""

kernel32 = ctypes.WinDLL("kernel32")
kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]


class _Memoria(ctypes.Structure):
    _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
                ("PrivateUsage", ctypes.c_size_t)]


def _tempo_e_memoria(pids):
    """(segundos de processador, MB de memoria privada) somados dos processos."""
    psapi = ctypes.WinDLL("psapi")
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD]
    segundos, memoria = 0.0, 0
    for pid in pids:
        alca = kernel32.OpenProcess(0x1000 | 0x0010, False, pid)
        if not alca:
            continue
        try:
            tempos = [wintypes.FILETIME() for _ in range(4)]
            if kernel32.GetProcessTimes(alca, *[ctypes.byref(t) for t in tempos]):
                segundos += sum((t.dwHighDateTime << 32 | t.dwLowDateTime) for t in tempos[2:]) / 1e7
            info = _Memoria()
            info.cb = ctypes.sizeof(info)
            if psapi.GetProcessMemoryInfo(alca, ctypes.byref(info), info.cb):
                memoria += info.PrivateUsage
        finally:
            kernel32.CloseHandle(alca)
    return segundos, memoria / (1024 * 1024)


def medir_um(codigo, nome, programa, protocolo, pasta_fotos, janela=False):
    resultado = {"codigo": codigo, "navegador": nome, "com_janela": janela}
    abrir = (firefox_bidi.NavegadorFirefox(programa, janela=janela) if protocolo == "bidi"
             else tela_sem_janela.Navegador(executavel=programa, janela=janela, tamanho=(1366, 768)))
    with abrir as nav:
        nav.antes_de_cada_pagina(ANTES_DA_PAGINA)
        nav.abrir(ENDERECO, largura=1366, altura=768, espera=0.5)
        limite = time.monotonic() + 45
        pronta = None
        while pronta is None and time.monotonic() < limite:
            pronta = nav.avaliar("window.__teste ? window.__teste.pronta : null")
            if pronta is None:
                time.sleep(0.2)
        resultado["pronta_ms"] = round(pronta) if pronta is not None else None
        if pronta is None:
            resultado["erros"] = nav.avaliar("window.__teste ? window.__teste.erros : ['sem o registro']")
            return resultado
        time.sleep(1.5)
        q0 = nav.avaliar("window.__teste.quadros")
        time.sleep(3)
        q1 = nav.avaliar("window.__teste.quadros")
        resultado["quadros_por_segundo"] = round((q1 - q0) / 3, 1)
        pids = nav.pids()
        cpu0, _ = _tempo_e_memoria(pids)
        t0 = time.monotonic()
        time.sleep(10)
        cpu1, memoria = _tempo_e_memoria(pids)
        resultado["processador_pct_parado"] = round(100 * (cpu1 - cpu0) / (time.monotonic() - t0), 1)
        resultado["memoria_mb"] = round(memoria, 1)
        resultado["processos"] = len(pids)
        resultado["foto"] = os.path.basename(nav.foto(os.path.join(pasta_fotos, "tela_%s.png" % codigo)))
        resultado.update(json.loads(nav.avaliar(ROTEIRO)))
    return resultado


def conferir(r):
    """[(o que, passou)] de um navegador."""
    abas = r.get("abas") or {}
    return [
        ("tela pronta, com os 10 jogos", r.get("pronta_ms") is not None and r.get("jogos") == 10
         and r.get("cartoes", 0) >= 1),
        ("nenhum erro de JavaScript", r.get("erros") == []),
        ("nada vaza para os lados", r.get("sem_rolagem_lateral") is True),
        ("Ajustes abre e as 5 abas mostram o painel", r.get("ajustes_abre") is True
         and len(abas) == 5 and all(abas.values())),
        ("Escala da tela: 5 escolhas e a troca grava", r.get("escalas") ==
         ["automatico", "pixel", "nitido", "suave", "original"] and r.get("escala_gravada") == "nitido"),
        ("Abrir a tela em: o padrao e os instalados", (r.get("navegadores") or [""])[0] == "automatico"
         and len(r.get("navegadores") or []) >= 2),
        ("a busca filtra", 0 < r.get("cartoes_na_busca", 0) < r.get("cartoes", 0) or r.get("cartoes", 0) == 1),
        ("o jogo clicado mostra os detalhes", r.get("detalhes_aparecem") is True),
        ("o tema troca", r.get("tema_troca") is True),
        ("a Biblioteca abre", r.get("biblioteca_abre") is True),
    ]


def argumento(nome, padrao):
    for a in sys.argv[1:]:
        if a.startswith("--%s=" % nome):
            return a.split("=", 1)[1]
    return padrao


def main():
    saida = argumento("saida", os.path.join(tempfile.gettempdir(), "teste_navegadores.json"))
    pasta_fotos = argumento("fotos", os.path.splitext(saida)[0] + "_fotos")
    os.makedirs(pasta_fotos, exist_ok=True)
    if copia.porta_ocupada():
        print("A porta %d ja esta ocupada (outro teste aberto?)." % copia.PORTA)
        return 2
    lista = navegadores_de_teste.prontos()
    trabalho, destino = copia.nova_pasta()
    servidor = None
    resultados = []
    try:
        jogos = {}
        for pasta in sorted(os.listdir(LIVRES)):
            caminho = os.path.join(LIVRES, pasta)
            if os.path.isdir(caminho) and pasta != "licencas":
                jogos[pasta] = [os.path.join(caminho, n) for n in os.listdir(caminho)]
        copia.montar(destino, [], jogos)
        servidor = copia.subir_servidor(destino, os.path.join(trabalho, "servidor.log"))
        for codigo, nome, programa, protocolo in lista:
            print("== %s" % nome)
            try:
                r = medir_um(codigo, nome, programa, protocolo, pasta_fotos, "--janela" in sys.argv)
            except (OSError, ValueError, KeyError, TypeError) as falha:
                r = {"codigo": codigo, "navegador": nome, "falha": str(falha)}
            r["conferencias"] = conferir(r)
            resultados.append(r)
            for item, passou in r["conferencias"]:
                print("  [%s] %s" % ("OK" if passou else "FALHOU", item))
            if r.get("erros"):
                print("  erros:", r["erros"][:5])
            print("  pronta em %s ms | %s quadros/s | parado: %s%% de um nucleo, %s MB em %s processos"
                  % (r.get("pronta_ms"), r.get("quadros_por_segundo"), r.get("processador_pct_parado"),
                     r.get("memoria_mb"), r.get("processos")))
    finally:
        if servidor:
            servidor.kill()
            servidor.wait(10)
        limpeza.apagar_pasta(trabalho)
    with open(saida, "w", encoding="utf-8") as arquivo:
        json.dump({"data": time.strftime("%Y-%m-%d %H:%M"), "tela": "1366x768", "resultados": resultados},
                  arquivo, ensure_ascii=False, indent=1)
    falhas = sum(1 for r in resultados for _item, passou in r["conferencias"] if not passou)
    total = sum(len(r["conferencias"]) for r in resultados)
    print()
    print("Navegadores: %d de %d certos (%s). Resultado: %s"
          % (total - falhas, total, ", ".join(r["navegador"] for r in resultados), saida))
    return 1 if falhas or not resultados else 0


if __name__ == "__main__":
    sys.exit(main())
