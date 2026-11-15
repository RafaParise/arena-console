# -*- coding: utf-8 -*-
r"""O servidor nativo (Rust, nativo\) na frente do Python, numa COPIA do ARENA (docs\MIGRACAO-RUST.md, etapa R1).

Confere, de ponta a ponta, com o servidor de verdade:
  1. o tempo ate a tela (GET /) e ate o /api/estado e o /api/catalogo, com e sem o nativo;
  2. na segunda abertura, o nativo entrega o estado e a lista guardados (X-Arena-Guardado) antes do Python;
  3. a seguranca: Host estranho (DNS rebinding) e X-Arena-Origem falso continuam barrados pelo Python;
  4. o Python fechando: o nativo fecha junto, com o mesmo codigo.
Nada do ARENA de verdade e' tocado (a copia vive no Temp e usa outra porta).

Uso:  servidor\python\python.exe testes\teste_nativo.py [caminho do arena-nativo.exe]
"""
import base64
import http.client
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.parse

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
import copia_do_arena as copia  # noqa: E402
import limpeza  # noqa: E402

PYTHON = os.path.join(RAIZ, "servidor", "python", "python.exe")
NATIVO_PADRAO = os.path.join(RAIZ, "nativo", "target", "x86_64-pc-windows-gnullvm", "release", "arena-nativo.exe")


def pedir(porta, metodo, rota, cabecalhos=None, corpo=None, espera=30):
    """(codigo, cabecalhos, corpo em bytes) de um pedido cru (para mandar Host e cabecalhos que o urllib nao deixa)."""
    conexao = http.client.HTTPConnection("127.0.0.1", porta, timeout=espera)
    conexao.request(metodo, rota, body=corpo, headers=cabecalhos or {})
    resposta = conexao.getresponse()
    dados = resposta.read()
    conexao.close()
    return resposta.status, dict(resposta.getheaders()), dados


def esperar_porta(porta, limite=60.0):
    fim = time.perf_counter() + limite
    while time.perf_counter() < fim:
        try:
            # Tempo-limite curto: no Windows, conectar numa porta ainda fechada so desiste no fim do tempo-limite
            # (com 0,2 s, toda abertura parecia levar pelo menos 0,2 s).
            socket.create_connection(("127.0.0.1", porta), timeout=0.01).close()
            return True
        except OSError:
            time.sleep(0.002)
    return False


def abrir(pasta, porta, nativo, registro):
    """Abre o servidor da copia (com o nativo na frente, se 'nativo') e mede os tempos da abertura."""
    ambiente = dict(os.environ, ARENA_SEM_JANELA="1", PYTHONIOENCODING="utf-8", ARENA_PORTA=str(porta),
                    ARENA_SEM_LOJAS="1")
    comando = [PYTHON, os.path.join(pasta, "servidor", "arena.py")]
    if nativo:
        comando = [nativo] + comando
    inicio = time.perf_counter()
    saida = open(registro, "w", encoding="utf-8")
    processo = subprocess.Popen(comando, cwd=pasta, env=ambiente, stdin=subprocess.DEVNULL, stdout=saida,
                                stderr=subprocess.STDOUT)
    tempos = {}
    if not esperar_porta(porta):
        raise SystemExit("a porta %d nao abriu; veja %s" % (porta, registro))
    tempos["porta"] = time.perf_counter() - inicio
    codigo, _, corpo = pedir(porta, "GET", "/", {"Host": "127.0.0.1:%d" % porta})
    tempos["tela"] = time.perf_counter() - inicio
    assert codigo == 200 and b"<html" in corpo.lower(), "a tela (GET /) nao veio"
    codigo, cab, corpo = pedir(porta, "GET", "/api/estado", {"Host": "127.0.0.1:%d" % porta})
    tempos["estado"] = time.perf_counter() - inicio
    tempos["estado_guardado"] = cab.get("X-Arena-Guardado") == "1"
    assert codigo == 200 and json.loads(corpo).get("versao"), "o /api/estado nao veio"
    codigo, cab, corpo = pedir(porta, "GET", "/api/catalogo", {"Host": "127.0.0.1:%d" % porta})
    tempos["catalogo"] = time.perf_counter() - inicio
    tempos["catalogo_guardado"] = cab.get("X-Arena-Guardado") == "1"
    assert codigo == 200 and "jogos" in json.loads(corpo), "o /api/catalogo nao veio"
    return processo, saida, tempos


def fechar(processo, saida, pasta):
    copia.derrubar(pasta)
    try:
        processo.wait(15)
    except subprocess.TimeoutExpired:
        processo.kill()
    saida.close()


def principal():
    nativo = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else NATIVO_PADRAO
    if not os.path.isfile(nativo):
        raise SystemExit("Falta o servidor nativo (%s). Compile com ferramentas\\compilar_nativo.py." % nativo)
    trabalho, pasta = copia.nova_pasta()
    porta = copia._porta_da_copia(8793)
    falhas = []
    try:
        livres = os.path.join(RAIZ, "testes", "jogos_livres")
        jogos = {}
        for console in ("nes", "snes", "gba"):
            onde = os.path.join(livres, console)
            if os.path.isdir(onde):
                jogos[console] = [os.path.join(onde, n) for n in os.listdir(onde) if not n.endswith((".txt", ".md"))]
        copia.montar(pasta, [], jogos)
        # O nativo DENTRO da copia (servidor/), como no pacote: ele acha a pasta do ARENA pelo proprio lugar, e assim
        # nada do teste vai para o dados/ do ARENA de verdade.
        dentro = os.path.join(pasta, "servidor", os.path.basename(nativo))
        shutil.copyfile(nativo, dentro)
        nativo = dentro
        registro = os.path.join(trabalho, "servidor.txt")

        # A: so o Python (como era), duas aberturas (a segunda com o .pyc pronto e a lista guardada).
        resultados = {}
        for rodada in ("python_1", "python_2"):
            processo, saida, tempos = abrir(pasta, porta, None, registro)
            fechar(processo, saida, pasta)
            resultados[rodada] = tempos
        # B: com o nativo na frente. A primeira grava o estado e a lista; a segunda ja entrega guardado.
        for rodada in ("nativo_1", "nativo_2", "nativo_3"):
            processo, saida, tempos = abrir(pasta, porta, nativo, registro)
            if rodada == "nativo_3":
                falhas += conferir_seguranca(porta)
                falhas += conferir_capas(porta, pasta)
                falhas += conferir_avisos(porta)
                falhas += conferir_saida(processo, pasta)
            fechar(processo, saida, pasta)
            resultados[rodada] = tempos

        print("\nTempo desde abrir o processo (s):  porta  tela  estado  catalogo  (guardado?)")
        for nome, t in resultados.items():
            print("  %-9s  %5.3f  %5.3f  %6.3f  %8.3f  estado=%s catalogo=%s"
                  % (nome, t["porta"], t["tela"], t["estado"], t["catalogo"],
                     "sim" if t["estado_guardado"] else "nao", "sim" if t["catalogo_guardado"] else "nao"))
        if not resultados["nativo_2"]["estado_guardado"] or not resultados["nativo_2"]["catalogo_guardado"]:
            falhas.append("na segunda abertura o nativo nao entregou o estado e a lista guardados")
        if resultados["nativo_2"]["catalogo"] >= resultados["python_2"]["catalogo"]:
            falhas.append("com o nativo, a lista nao chegou antes do que so com o Python")
    finally:
        copia.derrubar(pasta)
        limpeza.apagar_pasta(trabalho)
    print()
    if falhas:
        for falha in falhas:
            print("FALHOU: " + falha)
        return 1
    print("OK: o nativo abre a porta e entrega a tela e a lista guardada antes do Python, sem afrouxar a seguranca.")
    return 0


def conferir_seguranca(porta):
    """O nativo nao pode abrir brecha: o que nao for da tela deste aparelho vai ao Python, que barra como antes."""
    falhas = []
    local = {"Host": "127.0.0.1:%d" % porta}
    # DNS rebinding: Host de um site. O nativo nao responde sozinho; o Python recusa (403).
    codigo, _, _ = pedir(porta, "GET", "/api/estado", {"Host": "site-malvado.com:%d" % porta})
    if codigo != 403:
        falhas.append("Host estranho no /api/estado passou (codigo %d)" % codigo)
    # X-Arena-Origem falso vindo de quem pede: o nativo tira e escreve o de verdade (127.0.0.1), entao o pedido
    # continua local e passa (e nao vira "outro computador" com regras de fora).
    codigo, _, _ = pedir(porta, "GET", "/api/estado", dict(local, **{"X-Arena-Origem": "10.9.9.9",
                                                                       "X-Arena-Proxy": "chute"}))
    if codigo != 200:
        falhas.append("o pedido local com X-Arena-Origem falso foi tratado errado (codigo %d)" % codigo)
    # Um POST sem o Content-Type JSON continua barrado pelo Python (415).
    codigo, _, _ = pedir(porta, "POST", "/api/config", local, corpo=b"x=1")
    if codigo not in (400, 403, 415):
        falhas.append("POST sem JSON passou pelo nativo (codigo %d)" % codigo)
    # So o Python troca a escuta: sem o segredo, 403.
    codigo, _, _ = pedir(porta, "POST", "/_nativo/rede", dict(local, **{"Content-Type": "application/json"}),
                         corpo=b'{"escuta": "0.0.0.0"}')
    if codigo != 403:
        falhas.append("a troca da escuta aceitou pedido sem o segredo (codigo %d)" % codigo)
    # Caminho que sobe de pasta: nunca sai do launcher.
    codigo, _, corpo = pedir(porta, "GET", "/../servidor/arena.py", local)
    if codigo == 200 and b"def principal" in corpo:
        falhas.append("o caminho com .. entregou um arquivo do servidor")
    return falhas


def conferir_avisos(porta):
    """Os avisos em tempo real (/_nativo/eventos, 14/11/2026): o Atualizar lista da tela faz chegar o aviso de lista
    nova, com a geracao maior; so a tela deste aparelho ouve, e so o Python (com o segredo) manda aviso."""
    falhas = []
    local = {"Host": "127.0.0.1:%d" % porta}
    codigo, cabecalhos, corpo = pedir(porta, "GET", "/api/catalogo", local)
    geracao = json.loads(corpo.decode("utf-8")).get("geracao") if codigo == 200 else None
    if not isinstance(geracao, int):
        return ["o /api/catalogo nao trouxe a geracao da lista (%r)" % (geracao,)]
    if cabecalhos.get("X-Arena-Nativo") != "1":
        falhas.append("a resposta do /api/catalogo nao diz que o nativo esta na frente (X-Arena-Nativo)")
    # Ouvir como o EventSource do navegador: conexao crua, que nao termina.
    ouvinte = socket.create_connection(("127.0.0.1", porta), timeout=10)
    try:
        ouvinte.sendall(("GET /_nativo/eventos HTTP/1.1\r\nHost: 127.0.0.1:%d\r\nAccept: text/event-stream\r\n\r\n"
                         % porta).encode("ascii"))
        recebido = b""
        while b"\r\n\r\n" not in recebido:
            pedaco = ouvinte.recv(4096)
            if not pedaco:
                break
            recebido += pedaco
        cabeca, _, resto = recebido.partition(b"\r\n\r\n")
        cabeca = cabeca.decode("latin-1")
        if not cabeca.startswith("HTTP/1.1 200") or "text/event-stream" not in cabeca:
            return falhas + ["o /_nativo/eventos nao abriu como Server-Sent Events: %s" % cabeca.splitlines()[:1]]
        # Uma mudanca de verdade na lista: o botao Atualizar lista (POST /api/indexar).
        inicio = time.perf_counter()
        codigo, _, _ = pedir(porta, "POST", "/api/indexar", dict(local, **{"Content-Type": "application/json"}),
                             corpo=b"{}")
        if codigo != 200:
            return falhas + ["o Atualizar lista (/api/indexar) falhou (codigo %d)" % codigo]
        nova = None
        texto = resto.decode("utf-8", "replace")
        while nova is None and time.perf_counter() - inicio < 10:
            for bloco in texto.split("\n\n")[:-1]:
                linhas = dict(l.split(": ", 1) for l in bloco.split("\n") if ": " in l and not l.startswith(":"))
                if linhas.get("event") == "catalogo":
                    nova = json.loads(linhas.get("data") or "{}").get("geracao")
            if nova is None:
                pedaco = ouvinte.recv(4096)
                if not pedaco:
                    break
                texto += pedaco.decode("utf-8", "replace")
        if nova is None:
            falhas.append("o aviso de lista nova nao chegou em 10 s")
        elif not isinstance(nova, int) or nova <= geracao:
            falhas.append("o aviso trouxe uma geracao que nao subiu (%r -> %r)" % (geracao, nova))
        else:
            print("  aviso de lista nova chegou %.0f ms depois do Atualizar lista (geracao %d -> %d)"
                  % ((time.perf_counter() - inicio) * 1000, geracao, nova))
    except OSError as falha:
        falhas.append("a conexao dos avisos caiu: %s" % falha)
    finally:
        ouvinte.close()
    # As recusas: outro site (DNS rebinding) nao ouve; aviso sem o segredo, ou com o segredo errado, nao entra.
    codigo, _, _ = pedir(porta, "GET", "/_nativo/eventos", {"Host": "site-malvado.com:%d" % porta}, espera=5)
    if codigo != 403:
        falhas.append("os avisos aceitaram um Host de fora (codigo %d)" % codigo)
    # Outro site aberto no mesmo navegador (o Host e' o certo, mas o Origin denuncia): nao ocupa vaga de ouvinte.
    codigo, _, _ = pedir(porta, "GET", "/_nativo/eventos", dict(local, Origin="https://site-malvado.com"), espera=5)
    if codigo != 403:
        falhas.append("os avisos aceitaram um pedido de outro site (codigo %d)" % codigo)
    json_local = dict(local, **{"Content-Type": "application/json"})
    codigo, _, _ = pedir(porta, "POST", "/_nativo/evento?tipo=catalogo", json_local, corpo=b'{"geracao": 1}')
    if codigo != 403:
        falhas.append("um aviso sem o segredo foi aceito (codigo %d)" % codigo)
    codigo, _, _ = pedir(porta, "POST", "/_nativo/evento?tipo=catalogo", dict(json_local, **{"X-Arena-Proxy": "chute"}),
                         corpo=b'{"geracao": 1}')
    if codigo != 403:
        falhas.append("um aviso com o segredo errado foi aceito (codigo %d)" % codigo)
    return falhas


# Uma imagem PNG de 1x1 ponto (valida: o Python confere o tipo pelos bytes).
PNG_1X1 = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")


def conferir_capas(porta, pasta):
    """Etapa R2: o nativo entrega a capa e acha a miniatura que o PYTHON guardou (o mesmo SHA-1 nos dois)."""
    falhas = []
    local = {"Host": "127.0.0.1:%d" % porta}
    capas = os.path.join(pasta, "jogos", "pessoais", "snes", "capas")
    os.makedirs(capas, exist_ok=True)
    cheia = PNG_1X1 + b"capa-cheia" * 50
    with open(os.path.join(capas, "Jogo de Teste ção.png"), "wb") as saida:
        saida.write(cheia)
    arquivo = urllib.parse.quote("jogos/pessoais/snes/capas/Jogo de Teste ção.png")
    codigo, cab, corpo = pedir(porta, "GET", "/api/capa?arquivo=%s&mini=280" % arquivo, local)
    if codigo != 200 or corpo != cheia or cab.get("Cache-Control") != "max-age=86400":
        falhas.append("a capa cheia nao veio certa pelo nativo (codigo %d)" % codigo)
    # O que o Python responde chega pelo repasse, que sempre fecha a conexao; o que o nativo responde, nao.
    if cab.get("Connection", "").lower() == "close":
        falhas.append("a capa veio do Python, nao do nativo")
    # O Python guarda a miniatura que a tela fez (o POST continua nele)...
    corpo_post = json.dumps({"arquivo": urllib.parse.unquote(arquivo), "largura": 280,
                             "imagem": "data:image/png;base64," + base64.b64encode(PNG_1X1).decode()}).encode()
    codigo, _, _ = pedir(porta, "POST", "/api/capa/miniatura", dict(local, **{"Content-Type": "application/json"}),
                         corpo=corpo_post)
    if codigo != 200:
        falhas.append("o Python nao guardou a miniatura (codigo %d)" % codigo)
    # ... e o nativo acha a mesma miniatura pelo nome (sha1 de "caminho|tamanho|data|largura").
    codigo, cab, corpo = pedir(porta, "GET", "/api/capa?arquivo=%s&mini=280" % arquivo, local)
    if cab.get("Connection", "").lower() == "close":
        falhas.append("a miniatura veio do Python, nao do nativo")
    if codigo != 200 or corpo != PNG_1X1:
        falhas.append("o nativo nao achou a miniatura que o Python guardou (veio %d bytes)" % len(corpo))
    # Fora das pastas de jogos e de miniaturas: o nativo nao entrega; o Python responde 404, como sempre.
    for proibido in ("dados/config.json", "jogos/../dados/config.json", "servidor/arena.py"):
        codigo, _, corpo = pedir(porta, "GET", "/api/capa?arquivo=" + urllib.parse.quote(proibido), local)
        if codigo == 200:
            falhas.append("a capa entregou um arquivo de fora: %s" % proibido)
    return falhas


def conferir_saida(processo, pasta):
    """Fecha o Python a forca: o nativo tem que fechar junto (e o ARENA.bat decide se reabre)."""
    for pid in copia.servidores_da_copia(pasta):
        subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
    try:
        codigo = processo.wait(15)
    except subprocess.TimeoutExpired:
        return ["o nativo nao fechou quando o Python fechou"]
    return [] if codigo != 0 else ["o nativo saiu com 0 quando o Python foi derrubado (o .bat nao reabriria)"]


if __name__ == "__main__":
    sys.exit(principal())
