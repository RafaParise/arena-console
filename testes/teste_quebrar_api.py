# -*- coding: utf-8 -*-
r"""Tentando QUEBRAR a API do ARENA (pedido do Rafael, 01/10/2026).

Vai alem do testes\fuzz_rotas.py (que troca um campo por vez por um tipo so
e nao tinha as rotas novas). Num ARENA isolado (copia temporaria), manda:

  A. corpo que nao e' objeto: [], "texto", 123, null, true;
  B. JSON com 5.000 niveis de [[[...]]] e com NaN/Infinity;
  C. cada campo de cada rota trocado por: null, [], {}, true, 10**40, -1,
     1.5, "", controle/quebra de linha, 50 mil emojis;
  D. Content-Length mentiroso (promete 1000, manda 10 e fica parado): o
     servidor tem que largar a conexao sozinho;
  E. 200 conexoes paradas ao mesmo tempo: a tela continua respondendo;
  F. metodo trocado, caminho estranho, Host estranho.

Criterio: o servidor nunca cai; NENHUM erro 500 (erro tratado tem que ser
4xx com mensagem); toda resposta de erro e' JSON com "erro".

Uso: servidor\python\python.exe testes\teste_quebrar_api.py
     (leva ~1 minuto: o item D espera o tempo limite do servidor)
"""
import json
import os
import shutil
import socket
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fuzz_rotas  # noqa: E402  (ambiente isolado e lista de rotas)

PORTA = 8795
for _saida in (sys.stdout, sys.stderr):      # emoji nos relatorios, em qualquer console
    try:
        _saida.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass
VALORES_RUINS = [None, [], {}, True, 10 ** 40, -1, 1.5, "", "\x00\n\r\"", "🎮" * 50000]

ROTAS_NOVAS = [
    ("POST", "/api/acervo/instalar", {"id": "naoexiste"}),
    ("POST", "/api/acervo/salvar", {"itens": []}),
    ("POST", "/api/biblioteca-online/instalar", {"id": "x", "arquivo": "y.zip", "plataforma": "nes"}),
    ("POST", "/api/capa/enviar", {"jogo_id": "abc", "imagem": "x"}),
    ("POST", "/api/capa/miniatura", {"arquivo": "jogos/x.png", "largura": 280, "imagem": "x"}),
    ("POST", "/api/jogar", {"jogo_id": "naoexiste", "apelido": "x"}),
    ("POST", "/api/jogo/mover", {"jogo_id": "naoexiste", "plataforma": "nes"}),
    ("POST", "/api/perfil/novo", {"confirmar": "nao"}),
    ("POST", "/api/config", {"apelido": "x", "motor_ps2": "d3d11", "fundo_animado": "sempre",
                             "avancado": {"video_smooth": "true"}, "bios": {"ps1": "x"}, "favorito": "x"}),
    ("POST", "/api/perfil/foto", {"imagem": "x"}),
    ("GET", "/api/partida/procurar", {}),
]


def pedido(metodo, caminho, corpo=None, cru=None, cabecalhos=None, prazo=15):
    if cru is not None:
        dados = cru
    elif corpo is not None and metodo == "POST":
        dados = json.dumps(corpo).encode("utf-8")
    else:
        dados = None
    h = {"Host": "127.0.0.1:%d" % PORTA, "Content-Type": "application/json"}
    h.update(cabecalhos or {})
    if metodo == "GET" and corpo:
        caminho += "?" + urllib.parse.urlencode({k: str(v) for k, v in corpo.items()})
    req = urllib.request.Request("http://127.0.0.1:%d%s" % (PORTA, caminho), data=dados, method=metodo, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=prazo) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except (urllib.error.URLError, OSError) as e:
        return None, str(e)


def vivo():
    status, _ = pedido("GET", "/api/estado", prazo=10)
    return status == 200


def main():
    falhas, total = [], [0]
    problemas = []

    def confere(nome, ok, detalhe=""):
        total[0] += 1
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, detalhe if not ok else ""))
        if not ok:
            falhas.append(nome)

    def julgar(rotulo, status, texto):
        """Erro tratado = 4xx com JSON {"erro": ...}. 500 ou queda = problema."""
        if status is None:
            problemas.append("%s: sem resposta (%s)" % (rotulo, texto[:80]))
        elif status >= 500:
            problemas.append("%s: %d %s" % (rotulo, status, texto[:120]))
        elif status >= 400:
            try:
                if not json.loads(texto).get("erro"):
                    problemas.append("%s: %d sem mensagem" % (rotulo, status))
            except ValueError:
                problemas.append("%s: %d nao e' JSON" % (rotulo, status))

    destino = tempfile.mkdtemp(prefix="arena_quebrar_")
    servidor = None
    try:
        jogo_id = fuzz_rotas.preparar_ambiente(destino)
        arena = fuzz_rotas.carregar_arena_isolado(destino)
        servidor = arena.Servidor(("127.0.0.1", PORTA), arena.Manipulador)
        threading.Thread(target=servidor.serve_forever, daemon=True).start()
        time.sleep(0.5)
        confere("o ARENA isolado subiu", vivo())

        rotas = [(m, c, campos) for m, c, campos, _cam in fuzz_rotas.montar_rotas(jogo_id)] + ROTAS_NOVAS
        lentas = {"/api/barreiras", "/api/biblioteca-online", "/api/sincronizar", "/api/partida/testar",
                  "/api/amigo/testar", "/api/capa/atualizar", "/api/biblioteca-online/instalar",
                  "/api/acervo/instalar", "/api/partida/procurar"}
        posts = [(c, campos) for m, c, campos in rotas if m == "POST"]

        # A. corpo que nao e' objeto
        antes = len(problemas)
        for caminho, _campos in posts:
            for corpo in (b"[]", b'"texto"', b"123", b"null", b"true"):
                status, texto = pedido("POST", caminho, cru=corpo, prazo=30 if caminho in lentas else 15)
                julgar("A %s %s" % (caminho, corpo.decode()), status, texto)
        confere("A. corpo que nao e' objeto: tudo recusado com 4xx (%d rotas x 5)" % len(posts),
                len(problemas) == antes, "; ".join(problemas[antes:antes + 4]))

        # B. JSON profundo e NaN
        antes = len(problemas)
        profundo = b"[" * 5000 + b"]" * 5000
        for caminho in ("/api/config", "/api/placar", "/api/sinc/receber"):
            julgar("B profundo %s" % caminho, *pedido("POST", caminho, cru=profundo))
            julgar("B NaN %s" % caminho, *pedido("POST", caminho, cru=b'{"pontos": NaN, "tema": Infinity}'))
            status, _ = pedido("POST", caminho, cru=b'{"pontos": NaN}')
            if status == 200:
                problemas.append("B %s aceitou NaN" % caminho)
        confere("B. 5.000 niveis de [[[...]]] e NaN/Infinity: recusados", len(problemas) == antes,
                "; ".join(problemas[antes:antes + 4]))

        # C. cada campo, cada tipo ruim
        antes = len(problemas)
        enviados = 0
        for metodo, caminho, campos in rotas:
            if caminho in lentas:
                continue
            for campo in campos:
                for ruim in VALORES_RUINS:
                    if metodo == "GET" and isinstance(ruim, str) and len(ruim) > 1000:
                        continue    # URL gigante: o proprio Python recusa (414), ja coberto no fuzz
                    corpo = dict(campos)
                    corpo[campo] = ruim
                    julgar("C %s %s=%r" % (caminho, campo, str(ruim)[:20]), *pedido(metodo, caminho, corpo))
                    enviados += 1
        confere("C. %d pedidos com tipo ruim em cada campo: nenhum erro 500" % enviados,
                len(problemas) == antes, "; ".join(problemas[antes:antes + 6]))
        confere("o servidor continua de pe depois de A, B e C", vivo())

        # D. Content-Length mentiroso
        s = socket.create_connection(("127.0.0.1", PORTA), timeout=5)
        s.sendall(b"POST /api/config HTTP/1.1\r\nHost: 127.0.0.1:%d\r\nContent-Type: application/json\r\n"
                  b"Content-Length: 1000\r\n\r\n{\"tema\":" % PORTA)
        s.settimeout(arena.Manipulador.timeout + 15)
        inicio = time.time()
        try:
            largou = s.recv(4096) == b"" or True
        except (socket.timeout, TimeoutError):
            largou = False
        except OSError:
            largou = True     # fechou com reset
        s.close()
        confere("D. pedido que promete 1000 bytes e manda 10: o servidor larga em ~%d s"
                % arena.Manipulador.timeout, largou and time.time() - inicio < arena.Manipulador.timeout + 10,
                "%.0f s" % (time.time() - inicio))

        # E. 200 conexoes paradas
        paradas = []
        for _ in range(200):
            try:
                paradas.append(socket.create_connection(("127.0.0.1", PORTA), timeout=5))
            except OSError:
                break
        inicio = time.time()
        ok = vivo()
        confere("E. com %d conexoes paradas, a tela ainda responde (%.2f s)" % (len(paradas), time.time() - inicio),
                ok and time.time() - inicio < 3)
        for p in paradas:
            p.close()

        # F. metodo trocado, caminho estranho, Host estranho
        antes = len(problemas)
        julgar("F GET em rota POST", *pedido("GET", "/api/config/naoexiste"))
        julgar("F POST em rota GET", *pedido("POST", "/api/catalogo", {}))
        julgar("F caminho com ..", *pedido("GET", "/api/../../dados/config.json"))
        julgar("F caminho com %00", *pedido("GET", "/api/capa%00.png"))
        julgar("F rota inexistente", *pedido("POST", "/api/" + "x" * 3000, {}))
        status, _ = pedido("POST", "/api/config", {"tema": "escuro"}, cabecalhos={"Host": "malicioso.example"})
        if status not in (403, 400):
            problemas.append("F Host estranho foi aceito (%s)" % status)
        status, _ = pedido("POST", "/api/config", cru=b'{"tema": "escuro"}', cabecalhos={"Content-Type": "text/plain"})
        if status != 415:
            problemas.append("F text/plain foi aceito (%s)" % status)
        confere("F. metodo, caminho e cabecalho estranhos: tratados", len(problemas) == antes,
                "; ".join(problemas[antes:antes + 4]))

        # G. Endereco estranho nas rotas que procuram outro computador. O C
        # pula essas rotas (demoram: vao para a rede), e foi por ai que
        # passou o achado do fuzz de 01/10/2026: 2 MB ou emoji no endereco =
        # erro 500. Agora sao recusados ANTES da rede, entao sao rapidos.
        antes = len(problemas)
        estranhos = ["a" * 2_000_000, "\U0001F3AE" * 300, "olá mundo", "[::1", "192.168.0.5:abc",
                     "192.168.0.5:99999", "-pc-", "a..b", "x" * 64 + ".com", "@", "pc\x00lab", "a b:8777"]
        for caminho, campo, resto in (("/api/partida/testar", "endereco", {}),
                                      ("/api/amigo/testar", "url", {}),
                                      ("/api/amigo/adicionar", "url", {"apelido": "Estranho"})):
            for ruim in estranhos:
                inicio = time.time()
                status, texto = pedido("POST", caminho, dict(resto, **{campo: ruim}))
                rotulo = "G %s %s=%r" % (caminho, campo, ruim[:15])
                julgar(rotulo, status, texto)
                if status is not None and status < 400:
                    problemas.append("%s: aceito (%s)" % (rotulo, status))
                if time.time() - inicio > 2:
                    problemas.append("%s: levou %.1f s (devia recusar na hora)" % (rotulo, time.time() - inicio))
        if any(a.get("apelido") == "Estranho" for a in arena.carregar_config().get("servidores", [])):
            problemas.append("G amigo com endereco estranho foi gravado")
        confere("G. %d enderecos estranhos em 3 rotas de rede: recusados na hora, sem erro 500"
                % len(estranhos), len(problemas) == antes, "; ".join(problemas[antes:antes + 4]))
        confere("o servidor continua de pe no fim", vivo())
    finally:
        if servidor:
            servidor.shutdown()
            servidor.server_close()
        sys.path = [p for p in sys.path if not p.startswith(destino)]
        shutil.rmtree(destino, ignore_errors=True)

    print()
    if problemas:
        print("Problemas (%d):" % len(problemas))
        for p in problemas[:40]:
            print("   - " + p)
    if falhas:
        print("FALHOU: %d de %d" % (len(falhas), total[0]))
        return 1
    print("Tentando quebrar a API: %d de %d certos." % (total[0], total[0]))
    return 0


if __name__ == "__main__":
    import urllib.parse  # noqa: E402
    sys.exit(main())
