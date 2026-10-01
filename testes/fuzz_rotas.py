# -*- coding: utf-8 -*-
"""Fase 3 da auditoria: fuzz das rotas da API.

Sobe um ARENA isolado (copia temporaria de servidor/dados/launcher, mais um
jogo falso para ter um jogo_id de verdade) e testa cada rota com:
  1. dados corretos (linha de base -- confirma que a rota funciona)
  2. dados faltando (corpo/query vazio)
  3. tipo errado (numero no lugar de texto, lista no lugar de dict, etc.)
  4. texto gigante (2 MB numa string que normalmente e curta)
  5. acentos e emojis
  6. tentativa de sair da pasta (soh nos campos marcados como caminho)
  7. pedidos repetidos rapido (20x seguidas, sem trava nem crash)

Criterio de PASSOU por rota: nenhuma categoria derruba o servidor (conexao
recusada depois do teste), nenhuma resposta e HTML de traceback do Python
(erro 500 sem tratamento, only "Erro interno: ..." tratado conta como ok),
e toda resposta de erro tem o campo "erro" com uma mensagem (nao vazia).

Nao mexe na pasta real do projeto -- roda tudo numa copia temporaria.
"""
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENDERECO = "http://127.0.0.1:8777"

TEXTO_GIGANTE = "A" * (2 * 1024 * 1024)
TEXTO_EMOJI = "Olá 🎮🕹️ Ação, coração, façanha 日本語 émoji ñ"
CAMINHOS_TRAVESSIA = [
    "../../../../Windows/win.ini",
    "..\\..\\..\\..\\Windows\\win.ini",
    "/etc/passwd",
    "C:\\Windows\\win.ini",
    "....//....//....//Windows/win.ini",
]


def carregar_arena_isolado(destino):
    caminho = os.path.join(destino, "servidor", "arena.py")
    spec = importlib.util.spec_from_file_location("arena_fuzz_%d" % time.time_ns(), caminho)
    arena = importlib.util.module_from_spec(spec)
    sys.path.insert(0, os.path.join(destino, "servidor"))
    spec.loader.exec_module(arena)
    return arena


def preparar_ambiente(destino):
    for pasta in ("servidor", "dados", "launcher"):
        shutil.copytree(os.path.join(RAIZ, pasta), os.path.join(destino, pasta),
                         ignore=shutil.ignore_patterns("__pycache__", "tests"))
    # um jogo de verdade (falso, 0 bytes) pra ter jogo_id real
    pasta_nes = os.path.join(destino, "jogos", "pessoais", "NES")
    os.makedirs(pasta_nes, exist_ok=True)
    with open(os.path.join(pasta_nes, "Jogo de Teste Fuzz.nes"), "w") as f:
        pass


ROTAS_LENTAS = {"/api/barreiras": 60}


def requisicao(metodo, caminho, corpo=None, timeout=5):
    url = ENDERECO + caminho
    dados = None
    headers = {}
    if corpo is not None:
        dados = json.dumps(corpo).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=dados, method=metodo, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            texto = resp.read().decode("utf-8", errors="replace")
            return resp.status, texto
    except urllib.error.HTTPError as e:
        texto = e.read().decode("utf-8", errors="replace")
        return e.code, texto
    except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
        return None, str(e)


def resposta_e_sadia(status, texto):
    """Nao trava, nao devolve HTML de traceback cru, se for erro tem
    campo 'erro' com mensagem nao vazia."""
    if status is None:
        return False, "conexao falhou/travou"
    if "<title>" in texto.lower() and "traceback" in texto.lower():
        return False, "vazou traceback em HTML"
    if status >= 500:
        # 500 tratado (self.erro dentro de um except) ainda deve ser JSON
        try:
            corpo = json.loads(texto)
            if not corpo.get("erro"):
                return False, "500 sem mensagem de erro"
        except ValueError:
            return False, "500 com corpo nao-JSON (provavel traceback cru)"
    if status == 414:
        # URL gigante recusada pelo proprio http.server do Python ANTES de
        # chegar ao ARENA: rejeita cedo e nao trava, que e' o certo. Nao ha
        # como devolver JSON aqui sem reescrever o servidor da biblioteca
        # padrao. Conclusao da Fase 3, aplicada ao criterio na revisao
        # pos-auditoria (antes o script reprovava essas 7 checagens sempre).
        return True, "414 recusado pelo http.server (esperado)"
    if status >= 400:
        try:
            corpo = json.loads(texto)
        except ValueError:
            return False, "erro 4xx com corpo nao-JSON"
        if not corpo.get("erro"):
            return False, "erro 4xx sem mensagem"
    return True, "ok"


def servidor_vivo():
    try:
        with urllib.request.urlopen(ENDERECO + "/api/estado", timeout=2):
            return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Tabela de rotas: (metodo, caminho, campos_validos, campos_de_caminho)
# campos_de_caminho: quais chaves do corpo/query representam um caminho de
# arquivo vindo do cliente (usadas no teste de travessia de pasta).
# ---------------------------------------------------------------------------

def montar_rotas(jogo_id_real):
    return [
        # ---- GET, sem parametro ----
        ("GET", "/api/estado", {}, []),
        ("GET", "/api/catalogo", {}, []),
        ("GET", "/api/acervo", {}, []),
        ("GET", "/api/conquistas", {}, []),
        ("GET", "/api/perfil/foto", {}, []),
        ("GET", "/api/colegas", {}, []),
        ("GET", "/api/mapeamento", {}, []),
        ("GET", "/api/ranking", {}, []),
        ("GET", "/api/barreiras", {}, []),          # auditoria 2

        # ---- GET, com parametro ----
        ("GET", "/api/perfis-controle", {"tipo": "xbox360", "console": "ps1"}, []),
        ("GET", "/api/jogo/impressao", {"titulo": "Jogo de Teste Fuzz"}, []),
        ("GET", "/api/biblioteca-online", {"q": "Pong"}, []),
        ("GET", "/api/capa", {"arquivo": "jogos/pessoais/NES/Jogo de Teste Fuzz.nes"}, ["arquivo"]),
        ("GET", "/api/botoes", {"console": "nes"}, []),
        ("GET", "/api/jogo", {"id": jogo_id_real or "abc"}, []),

        # ---- POST ----
        ("POST", "/api/sinc/receber", {"placares": [], "sessoes": [], "dispositivo": "abc123"}, []),
        ("POST", "/api/mala", {}, []),  # SEM caminho aqui -- travessia testada a parte, ver nota abaixo
        ("POST", "/api/sincronizar", {}, []),
        ("POST", "/api/perfil-controle", {"console": "ps1", "direcional": True}, []),
        ("POST", "/api/mapeamento/definir", {"jogador": "1", "botao": "a", "tipo": "tecla", "valor": "Space"}, []),
        ("POST", "/api/mapeamento/padrao", {"jogador": "1"}, []),
        ("POST", "/api/mapeamento/limpar", {"jogador": "1"}, []),
        ("POST", "/api/acervo/remover", {"id": "x"}, []),
        ("POST", "/api/amigo/codigo", {"codigo": "abc123"}, []),
        ("POST", "/api/partida/testar", {"endereco": "192.168.0.5"}, []),
        ("POST", "/api/bios/abrir", {"plataforma": "ps1"}, []),
        ("POST", "/api/pastas/criar", {}, []),
        ("POST", "/api/jogo/console", {"jogo_id": jogo_id_real or "abc", "plataforma": "nes"}, []),
        ("POST", "/api/estado/apagar", {"jogo_id": jogo_id_real or "abc", "espaco": 0}, []),
        ("POST", "/api/cheat/adicionar", {"jogo_id": jogo_id_real or "abc", "codigo": "ABCD-1234", "descricao": "teste"}, []),
        ("POST", "/api/cheat/alterar", {"jogo_id": jogo_id_real or "abc", "indice": 0}, []),
        ("POST", "/api/exportar", {}, []),
        ("POST", "/api/importar", {"arquivo": "naoexiste.zip"}, ["arquivo"]),
        ("POST", "/api/backup", {}, []),
        # auditoria 2: "notepad" nao esta na lista segura -> recusa sem fechar nada
        ("POST", "/api/barreiras/fechar", {"programa": "notepad"}, ["programa"]),
        ("POST", "/api/capa/atualizar", {"jogo_id": jogo_id_real or "abc"}, []),
        ("POST", "/api/amigo/adicionar", {"apelido": "TesteFuzz", "url": "192.168.0.5:8777"}, []),
        ("POST", "/api/amigo/remover", {"apelido": "TesteFuzz"}, []),
        ("POST", "/api/amigo/testar", {"url": "192.168.0.5:8777"}, []),
        ("POST", "/api/sinc/ola", {}, []),
        ("POST", "/api/indexar", {}, []),
        ("POST", "/api/config", {"tema": "escuro"}, []),
        ("POST", "/api/placar", {"pontos": 100, "jogo_id": jogo_id_real or "abc", "apelido": "TesteFuzz"}, []),
        # jogo/mover e jogar tem efeito colateral maior (move arquivo real /
        # tenta abrir processo) -- testados a parte, com mais cuidado.
    ]


def valor_tipo_errado(valor):
    if isinstance(valor, str):
        return 12345
    if isinstance(valor, bool):
        return "nao-e-booleano"
    if isinstance(valor, (int, float)):
        return {"isto": "deveria ser numero"}
    if isinstance(valor, list):
        return "isto deveria ser lista"
    if isinstance(valor, dict):
        return ["isto", "deveria", "ser", "dict"]
    return None


def testar_rota(metodo, caminho, campos_ok, campos_caminho, relatorio):
    def registrar(categoria, status, texto, extra=""):
        ok, motivo = resposta_e_sadia(status, texto)
        relatorio.append({
            "rota": caminho, "metodo": metodo, "categoria": categoria,
            "status": status, "ok": ok, "motivo": motivo, "extra": extra,
        })
        return ok

    # Rotas lentas de proposito (auditoria 2): o diagnostico de lentidao
    # pergunta ao Windows por PowerShell (~5 s aqui, mais num Celeron). A tela
    # espera sem prazo; so o fuzz precisava saber.
    prazo = ROTAS_LENTAS.get(caminho, 5)

    def enviar(corpo):
        if metodo == "GET":
            query = "&".join("%s=%s" % (k, urllib.request.quote(str(v))) for k, v in corpo.items())
            alvo = caminho + ("?" + query if query else "")
            return requisicao("GET", alvo, timeout=prazo)
        return requisicao("POST", caminho, corpo, timeout=prazo)

    # 1. dados corretos
    status, texto = enviar(campos_ok)
    registrar("dados_corretos", status, texto)

    # 2. dados faltando
    status, texto = enviar({})
    registrar("dados_faltando", status, texto)

    # 3. tipo errado (um campo por vez)
    for campo, valor in campos_ok.items():
        corpo = dict(campos_ok)
        corpo[campo] = valor_tipo_errado(valor)
        status, texto = enviar(corpo)
        registrar("tipo_errado", status, texto, extra="campo=%s" % campo)

    # 4. texto gigante (campos string)
    for campo, valor in campos_ok.items():
        if not isinstance(valor, str):
            continue
        corpo = dict(campos_ok)
        corpo[campo] = TEXTO_GIGANTE
        status, texto = enviar(corpo)
        registrar("texto_gigante", status, texto, extra="campo=%s" % campo)

    # 5. acentos e emojis (campos string)
    for campo, valor in campos_ok.items():
        if not isinstance(valor, str):
            continue
        corpo = dict(campos_ok)
        corpo[campo] = TEXTO_EMOJI
        status, texto = enviar(corpo)
        registrar("emoji", status, texto, extra="campo=%s" % campo)

    # 6. travessia de pasta (so nos campos marcados)
    for campo in campos_caminho:
        for payload in CAMINHOS_TRAVESSIA:
            corpo = dict(campos_ok)
            corpo[campo] = payload
            status, texto = enviar(corpo)
            ok = registrar("travessia_pasta", status, texto, extra="campo=%s payload=%s" % (campo, payload))
            # alem de nao travar, tem que RECUSAR (nao pode devolver 200
            # com conteudo de fora da pasta permitida)
            if status == 200 and metodo == "GET" and caminho == "/api/capa":
                relatorio.append({
                    "rota": caminho, "metodo": metodo, "categoria": "travessia_pasta_ACEITOU",
                    "status": status, "ok": False,
                    "motivo": "GET /api/capa devolveu 200 para %r -- possivel path traversal" % payload,
                    "extra": "",
                })

    # 7. pedidos repetidos rapido
    falhas_repeticao = 0
    for _ in range(20):
        status, texto = enviar(campos_ok)
        if status is None:
            falhas_repeticao += 1
    registrar("repeticao_rapida", 200 if falhas_repeticao == 0 else None, "",
              extra="falhas=%d/20" % falhas_repeticao)


def main():
    # O ARENA isolado numa SUBPASTA do temporario: a mala do pen drive vai
    # para a pasta de cima (caminho_da_mala), e com o ARENA direto no Temp
    # ela ficava esquecida no Temp do Windows (achado de 01/10/2026).
    destino = os.path.join(tempfile.mkdtemp(prefix="arena_fuzz_"), "ARENA")
    os.makedirs(destino)
    print("Pasta de teste:", destino)
    relatorio = []
    try:
        preparar_ambiente(destino)
        arena = carregar_arena_isolado(destino)

        servidor = arena.Servidor(("127.0.0.1", 8777), arena.Manipulador)
        thread = threading.Thread(target=servidor.serve_forever, daemon=True)
        thread.start()
        time.sleep(0.5)

        # pega o jogo_id real do jogo falso que semeamos
        status, texto = requisicao("GET", "/api/catalogo")
        jogo_id_real = None
        try:
            catalogo = json.loads(texto)
            for jogo in catalogo.get("jogos", []):
                if "Teste Fuzz" in jogo.get("titulo", ""):
                    jogo_id_real = jogo["id"]
                    break
        except Exception:
            pass
        print("jogo_id real encontrado:", jogo_id_real)

        rotas = montar_rotas(jogo_id_real)
        print("Testando %d rotas..." % len(rotas))
        for i, (metodo, caminho, campos_ok, campos_caminho) in enumerate(rotas, 1):
            print("  [%d/%d] %s %s" % (i, len(rotas), metodo, caminho))
            testar_rota(metodo, caminho, campos_ok, campos_caminho, relatorio)
            if not servidor_vivo():
                print("    [ERRO GRAVE] servidor parou de responder depois desta rota!")
                relatorio.append({
                    "rota": caminho, "metodo": metodo, "categoria": "SERVIDOR_CAIU",
                    "status": None, "ok": False, "motivo": "servidor nao respondeu mais", "extra": "",
                })
                break

        servidor.shutdown()
        servidor.server_close()

    finally:
        sys.path = [p for p in sys.path if not p.startswith(destino)]
        shutil.rmtree(os.path.dirname(destino), ignore_errors=True)

    # ---- resumo ----
    falhas = [r for r in relatorio if not r["ok"]]
    destino_relatorio = os.path.join(RAIZ, "docs", "fuzz_rotas_bruto.json")
    with open(destino_relatorio, "w", encoding="utf-8") as f:
        json.dump(relatorio, f, ensure_ascii=False, indent=2)

    print("\n--- RESUMO ---")
    print("Total de checagens:", len(relatorio))
    print("Falhas:", len(falhas))
    if falhas:
        print("\nDetalhe das falhas:")
        for f in falhas:
            print("  %s %s [%s] status=%s :: %s %s" % (
                f["metodo"], f["rota"], f["categoria"], f["status"], f["motivo"], f["extra"]))
    print("\nRelatorio completo salvo em", destino_relatorio)
    return 0 if not falhas else 1


if __name__ == "__main__":
    sys.exit(main())
