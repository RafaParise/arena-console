# -*- coding: utf-8 -*-
r"""Confere um ARENA que JA ESTA ABERTO, so lendo: a tela, as rotas principais, a capa e a seguranca.

Para que serve: depois de mexer no servidor (Python ou o nativo em Rust), ou numa maquina da escola, saber em
poucos segundos se o ARENA responde certo e se continua recusando o que tem de recusar. E' a versao do ARENA da
ideia "validate_api_endpoints.sh" dos blueprints (docs\arena-blueprints\: as rotas de la nao existem aqui).

O que confere (cada item sai com OK ou FALHA e o tempo da resposta em milissegundos):
  1. GET / (a tela) e GET /app.js respondem 200.
  2. GET /api/estado e GET /api/catalogo devolvem JSON valido (conta plataformas e jogos) e se vieram do
     guardado do servidor nativo (cabecalho X-Arena-Guardado: 1).
  3. Quem atendeu: o servidor nativo (Rust) responde 200 no GET /_nativo/pronto; so o Python responde 404.
  4. Uma capa do catalogo: tipo de imagem (Content-Type) e o Cache-Control.
  5. Seguranca (o que TEM de ser recusado): Host falso (DNS rebinding), POST sem Content-Type JSON e caminho
     com ".." (subir de pasta). Se algo assim for aceito, o relatorio mostra FALHA DE SEGURANCA em destaque.
  6. No Android, todo pedido sem o cookie arena_segredo e' recusado (403). Se as rotas da API vierem todas 403,
     o script avisa que deve ser o ARENA de um Android (pelo "adb forward tcp:8777 tcp:8777"), o que e' esperado.

NUNCA grava nada no ARENA: o unico POST (item 5) e' um que o servidor tem de recusar antes de ler o corpo, e o
corpo dele nem e' JSON.

Uso:
    servidor\python\python.exe ferramentas\conferir_servidor.py [--endereco http://127.0.0.1:8777] [--espera 10]
        --endereco  onde o ARENA esta escutando (padrao http://127.0.0.1:8777)
        --espera    tempo-limite de cada pedido, em segundos (padrao 10)

Codigo de saida: 0 se tudo deu OK (aviso nao conta como falha), 1 se algum item falhou.
"""
import argparse
import http.client
import json
import socket
import sys
import time
import urllib.parse

ENDERECO_PADRAO = "http://127.0.0.1:8777"

OK = "OK"
FALHA = "FALHA"
FALHA_SEGURANCA = "FALHA DE SEGURANÇA"
AVISO = "AVISO"


class Resposta:
    """O que voltou de um pedido: codigo, cabecalhos (nomes em minusculas), corpo e o tempo em ms.
    Se a conexao falhou, 'erro' diz o motivo e 'codigo' fica 0."""

    def __init__(self, codigo=0, cabecalhos=None, corpo=b"", ms=0.0, erro=""):
        self.codigo = codigo
        self.cabecalhos = cabecalhos or {}
        self.corpo = corpo
        self.ms = ms
        self.erro = erro

    def cabecalho(self, nome):
        return self.cabecalhos.get(nome.lower(), "")

    def json(self):
        """O corpo lido como JSON, ou None se nao for JSON valido."""
        try:
            return json.loads(self.corpo.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            return None

    def resumo(self):
        if self.erro:
            return "sem resposta (%s)" % self.erro
        return "%d em %.0f ms" % (self.codigo, self.ms)


def ler_endereco(texto):
    """'http://127.0.0.1:8777', '127.0.0.1:8777' ou 'localhost' -> (nome, porta). So http (o ARENA nao usa https)."""
    texto = (texto or "").strip()
    if "://" not in texto:
        texto = "http://" + texto
    partes = urllib.parse.urlsplit(texto)
    if partes.scheme != "http" or not partes.hostname:
        raise ValueError("Endereço inválido: %r. Use algo como http://127.0.0.1:8777." % texto)
    return partes.hostname, partes.port or 80


def pedir(nome, porta, metodo, rota, cabecalhos=None, corpo=None, espera=10.0):
    """Um pedido cru com http.client (deixa mandar um Host falso e caminho com '..', que o urllib arrumaria)."""
    inicio = time.perf_counter()
    conexao = http.client.HTTPConnection(nome, porta, timeout=espera)
    try:
        conexao.request(metodo, rota, body=corpo, headers=cabecalhos or {})
        resposta = conexao.getresponse()
        dados = resposta.read()
        ms = (time.perf_counter() - inicio) * 1000
        return Resposta(resposta.status, {k.lower(): v for k, v in resposta.getheaders()}, dados, ms)
    except socket.timeout:
        return Resposta(erro="passou de %g s sem resposta" % espera, ms=(time.perf_counter() - inicio) * 1000)
    except (OSError, http.client.HTTPException) as falha:
        return Resposta(erro=str(falha) or type(falha).__name__, ms=(time.perf_counter() - inicio) * 1000)
    finally:
        conexao.close()


def conferir(endereco=ENDERECO_PADRAO, espera=10.0):
    """Faz todas as conferencias e devolve a lista de itens: (estado, titulo, detalhe)."""
    nome, porta = ler_endereco(endereco)
    itens = []

    def item(estado, titulo, detalhe=""):
        itens.append((estado, titulo, detalhe))

    def get(rota, cabecalhos=None):
        return pedir(nome, porta, "GET", rota, cabecalhos, espera=espera)

    # -- 1. A tela -------------------------------------------------------------------------------------------
    tela = get("/")
    if tela.erro:
        item(FALHA, "O ARENA responde em %s" % endereco,
             "%s. Abra o ARENA (ARENA.bat) ou confira o --endereco; no Android, rode antes "
             "'adb forward tcp:8777 tcp:8777'." % tela.resumo())
        return itens
    script = get("/app.js")

    # -- 2. O estado e o catalogo (decidem se e' um Android antes de julgar o resto) ---------------------------
    estado = get("/api/estado")
    catalogo = get("/api/catalogo")
    android = estado.codigo == 403 and catalogo.codigo == 403
    if android:
        item(AVISO, "Parece o ARENA de um Android",
             "o /api/estado e o /api/catalogo vieram 403: no Android, todo pedido sem o cookie arena_segredo "
             "(que só a tela do app tem) é recusado. Isso é o esperado pelo 'adb forward tcp:8777 tcp:8777'; "
             "para conferir as rotas, use o ARENA do computador.")

    for rota, resposta, conteudo in (("/", tela, b"<html"), ("/app.js", script, b"")):
        titulo = "GET %s (%s)" % (rota, "a tela" if rota == "/" else "o código da tela")
        if resposta.codigo == 200 and conteudo.lower() in resposta.corpo.lower():
            item(OK, titulo, resposta.resumo())
        elif android and resposta.codigo == 403:
            item(AVISO, titulo, resposta.resumo() + " (esperado no Android sem o cookie)")
        else:
            item(FALHA, titulo, resposta.resumo() + "; esperava 200 com a página. Veja se a pasta launcher\\ "
                 "está inteira.")

    dados_catalogo = None
    if not android:
        for rota, resposta, chave in (("/api/estado", estado, "versao"), ("/api/catalogo", catalogo, "jogos")):
            titulo = "GET %s" % rota
            dados = resposta.json()
            guardado = " | guardado pelo nativo" if resposta.cabecalho("X-Arena-Guardado") == "1" else \
                " | veio na hora (não do guardado)"
            if resposta.codigo != 200:
                item(FALHA, titulo, resposta.resumo() + "; esperava 200. Veja a janela/registro do servidor.")
            elif not isinstance(dados, dict) or chave not in dados:
                item(FALHA, titulo, resposta.resumo() + "; o corpo não é o JSON esperado (falta '%s')." % chave)
            elif rota == "/api/estado":
                item(OK, titulo, "%s | versão %s%s" % (resposta.resumo(), dados.get("versao"), guardado))
            else:
                dados_catalogo = dados
                plataformas = dados.get("plataformas") or []
                jogos = dados.get("jogos") or []
                item(OK, titulo, "%s | %d plataformas, %d jogos%s"
                     % (resposta.resumo(), len(plataformas), len(jogos), guardado))

    # -- 3. Quem atendeu -------------------------------------------------------------------------------------
    pronto = get("/_nativo/pronto")
    servidor = tela.cabecalho("Server")
    if pronto.codigo == 200:
        item(OK, "Quem atendeu", "o servidor nativo (Rust) na frente do Python (GET /_nativo/pronto %s)"
             % pronto.resumo())
    elif pronto.codigo == 404:
        item(OK, "Quem atendeu", "só o Python, sem o nativo (GET /_nativo/pronto %s%s)"
             % (pronto.resumo(), "; Server: " + servidor if servidor else ""))
    elif pronto.codigo == 503:
        item(FALHA, "Quem atendeu", "o nativo está na frente, mas o Python não ficou pronto (503). Veja o "
             "registro do servidor Python.")
    elif android and pronto.codigo == 403:
        item(AVISO, "Quem atendeu", "não deu para saber (403 do Android)")
    else:
        item(FALHA, "Quem atendeu", "GET /_nativo/pronto: %s; esperava 200 (nativo) ou 404 (só o Python)."
             % pronto.resumo())

    # -- 4. Uma capa -----------------------------------------------------------------------------------------
    if dados_catalogo is not None:
        url_capa = next((j["capa_urls"][0] for j in dados_catalogo.get("jogos") or []
                         if isinstance(j, dict) and j.get("capa_urls")), None)
        if not url_capa:
            item(AVISO, "Uma capa", "nenhum jogo do catálogo tem capa_urls: item pulado.")
        else:
            capa = get(url_capa)
            tipo = capa.cabecalho("Content-Type")
            cache = capa.cabecalho("Cache-Control")
            if capa.codigo == 200 and tipo.startswith("image/") and "max-age" in cache:
                item(OK, "Uma capa", "%s | %s | Cache-Control: %s" % (capa.resumo(), tipo, cache))
            else:
                item(FALHA, "Uma capa (%s)" % url_capa,
                     "%s | Content-Type: %s | Cache-Control: %s; esperava 200, image/* e max-age."
                     % (capa.resumo(), tipo or "(nenhum)", cache or "(nenhum)"))

    # -- 5. Seguranca: o que TEM de ser recusado ------------------------------------------------------------
    def recusa(titulo, resposta, aceitos):
        if resposta.erro:
            item(FALHA, titulo, resposta.resumo())
        elif resposta.codigo in aceitos:
            item(OK, titulo, "recusado: " + resposta.resumo())
        elif 200 <= resposta.codigo < 300:
            item(FALHA_SEGURANCA, titulo, "ACEITO (%s), mas tinha de ser recusado (%s)."
                 % (resposta.resumo(), "/".join(str(c) for c in sorted(aceitos))))
        else:
            item(FALHA, titulo, "%s; esperava %s." % (resposta.resumo(), "/".join(str(c) for c in sorted(aceitos))))

    recusa("Host falso (Host: exemplo.com) no /api/estado", get("/api/estado", {"Host": "exemplo.com"}), {403})
    # O corpo nao e' JSON e o tipo nao e' application/json: o servidor recusa (415) antes de ler e de mudar algo.
    recusa("POST /api/config sem Content-Type: application/json",
           pedir(nome, porta, "POST", "/api/config", {"Content-Type": "text/plain"}, b"x=1", espera),
           {400, 403, 415})
    recusa("Caminho com .. (GET /../servidor/arena.py)", get("/../servidor/arena.py"), {400, 403, 404})
    recusa("Capa fora da pasta (GET /api/capa?arquivo=../../servidor/arena.py)",
           get("/api/capa?arquivo=" + urllib.parse.quote("../../servidor/arena.py")), {400, 403, 404})
    return itens


def relatorio(itens, endereco):
    """O texto do relatorio, pronto para imprimir."""
    linhas = ["Conferência do ARENA em %s (só leitura)" % endereco, ""]
    for estado, titulo, detalhe in itens:
        linhas.append("  [%-5s] %s" % ("FALHA" if estado == FALHA_SEGURANCA else estado, titulo))
        if detalhe:
            linhas.append("          %s" % detalhe)
    seguranca = [i for i in itens if i[0] == FALHA_SEGURANCA]
    falhas = [i for i in itens if i[0] in (FALHA, FALHA_SEGURANCA)]
    linhas.append("")
    if seguranca:
        linhas.append("!" * 72)
        linhas.append("!!! FALHA DE SEGURANÇA: o ARENA aceitou o que tinha de recusar.")
        for _, titulo, detalhe in seguranca:
            linhas.append("!!!   %s: %s" % (titulo, detalhe))
        linhas.append("!!! Não use esta versão com alunos; reveja o servidor (checar_acesso_de_rede).")
        linhas.append("!" * 72)
    if falhas:
        linhas.append("RESULTADO: %d de %d itens falharam." % (len(falhas), len(itens)))
    else:
        linhas.append("RESULTADO: tudo OK (%d itens%s)." % (
            len(itens), ", %d aviso(s)" % sum(1 for i in itens if i[0] == AVISO)
            if any(i[0] == AVISO for i in itens) else ""))
    return "\n".join(linhas)


def principal(argumentos=None):
    leitor = argparse.ArgumentParser(description="Confere, só lendo, um ARENA que já está aberto.")
    leitor.add_argument("--endereco", default=ENDERECO_PADRAO, help="padrão: %s" % ENDERECO_PADRAO)
    leitor.add_argument("--espera", type=float, default=10.0, help="tempo-limite de cada pedido (s)")
    opcoes = leitor.parse_args(argumentos)
    try:
        sys.stdout.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass
    try:
        itens = conferir(opcoes.endereco, opcoes.espera)
    except ValueError as falha:
        print(falha)
        return 1
    print(relatorio(itens, opcoes.endereco))
    return 1 if any(i[0] in (FALHA, FALHA_SEGURANCA) for i in itens) else 0


if __name__ == "__main__":
    sys.exit(principal())
