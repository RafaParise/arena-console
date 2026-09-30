# -*- coding: utf-8 -*-
r"""Jogar Junto: a partida hospedada pelo amigo APARECE para o convidado?

Bug relatado pelo Rafael em 30/09/2026: amigo adicionado (por codigo, por
endereco, pelo ponto de acesso) aparecia "fora do ar" embora os recordes
sincronizassem, e a partida aberta pelo jogador 1 nunca aparecia como
opcao para o jogador 2. Causa: a tela filtrava por "partida_aberta", mas o
servidor nunca mandava esse campo (em nenhuma das tres versoes).

Monta dois ARENAs isolados num computador so (A na porta 8791, B na 8792):
  1. B procura (/api/partida/procurar): A aparece online, SEM partida.
  2. A hospeda pela rota real /api/jogar (o RetroArch e' trocado por um
     falso que fica "aberto" ate o teste mandar fechar).
  3. B procura de novo: A aparece com a partida e o nome do jogo -- pela
     pergunta direta (TCP) E pelo grito da descoberta (UDP).
  4. O jogo de A fecha: a partida some das duas formas.
  5. "Só assistir" agora monta a partida (antes abria o jogo sozinho).

A trata como OUTRA MAQUINA todo pedido feito pelo nome "localhost" -- e'
por ele que B fala com A, entao a trava de rede (ROTAS_REDE_EXTERNA) vale.

Uso: servidor\python\python.exe testes\teste_partida_aparece.py
"""
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORTA_UDP_TESTE = 55499   # longe da 55436 real: nao conversa com ARENA de verdade
JOGO = "Jogo De Teste (Brasil).smc"


def montar_copia(nome, porta):
    destino = tempfile.mkdtemp(prefix="arena_%s_" % nome)
    for pasta in ("servidor", "launcher"):
        shutil.copytree(os.path.join(RAIZ, pasta), os.path.join(destino, pasta),
                        ignore=shutil.ignore_patterns("__pycache__", "tests", "python"))
    os.makedirs(os.path.join(destino, "dados"))
    # Jogo e RetroArch de mentira: so para a rota /api/jogar aceitar.
    pasta_snes = os.path.join(destino, "jogos", "pessoais", "Super Nintendo")
    os.makedirs(pasta_snes)
    open(os.path.join(pasta_snes, JOGO), "wb").write(b"\0" * 1024)
    os.makedirs(os.path.join(destino, "retroarch", "cores"))
    open(os.path.join(destino, "retroarch", "retroarch.exe"), "wb").close()
    open(os.path.join(destino, "retroarch", "cores", "snes9x_libretro.dll"), "wb").close()

    spec = importlib.util.spec_from_file_location(
        "arena_" + nome, os.path.join(destino, "servidor", "arena.py"))
    modulo = importlib.util.module_from_spec(spec)
    sys.modules["arena_" + nome] = modulo
    sys.path.insert(0, os.path.join(destino, "servidor"))
    spec.loader.exec_module(modulo)
    sys.path.pop(0)
    modulo.PORTA = porta
    modulo.PORTA_DESCOBERTA = PORTA_UDP_TESTE
    modulo.preparar_banco()
    return destino, modulo


def pedir(porta, rota, corpo=None, host="127.0.0.1"):
    dados = None if corpo is None else json.dumps(corpo).encode("utf-8")
    pedido = urllib.request.Request(
        "http://%s:%d%s" % (host, porta, rota), data=dados,
        method="GET" if corpo is None else "POST",
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(pedido, timeout=10) as resposta:
        return json.loads(resposta.read().decode("utf-8"))


def achar_jogo_no_catalogo(no, inicio):
    """Procura em qualquer nivel do catalogo o jogo cujo titulo comeca assim."""
    if isinstance(no, dict):
        if str(no.get("titulo", "")).startswith(inicio) and no.get("id"):
            return no
        no = list(no.values())
    if isinstance(no, list):
        for item in no:
            achado = achar_jogo_no_catalogo(item, inicio)
            if achado:
                return achado
    return None


def achar(lista, apelido):
    return next((c for c in lista if c.get("apelido") == apelido), None)


def main():
    pastas, servidores, falhas = [], [], []

    def confere(nome, ok, detalhe=""):
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, detalhe))
        if not ok:
            falhas.append(nome)

    try:
        pasta_a, A = montar_copia("A", 8791)
        pasta_b, B = montar_copia("B", 8792)
        pastas += [pasta_a, pasta_b]

        # A: rede liberada (senao nao grita) e apelido.
        cfg = A.carregar_config()
        cfg.update(apelido="Colega A", permitir_rede=True)
        A.salvar_config(cfg)
        id_a = cfg["dispositivo_id"]

        # B: A salvo como amigo pelo nome "localhost" (= outra maquina para A).
        cfg = B.carregar_config()
        cfg.update(apelido="Colega B", permitir_rede=True, servidores=[
            {"apelido": "Colega A", "url": "http://localhost:8791", "id": id_a}])
        B.salvar_config(cfg)

        class ManipuladorA(A.Manipulador):
            def pedido_e_local(self):
                return not (self.headers.get("Host") or "").startswith("localhost")

        for modulo, manipulador, porta in ((A, ManipuladorA, 8791), (B, B.Manipulador, 8792)):
            srv = modulo.Servidor(("127.0.0.1", porta), manipulador)
            threading.Thread(target=srv.serve_forever, daemon=True).start()
            servidores.append(srv)

        # RetroArch falso em A: fica "aberto" ate FECHAR ser ligado, depois
        # chama o executar_jogo de verdade (que falha ao abrir o .exe vazio
        # e cai no finally -- o mesmo caminho de quando o aluno fecha o jogo).
        FECHAR = threading.Event()
        original = A.executar_jogo
        partida_recebida = {}

        def executar_falso(jogo, apelido, config, custo=None, partida=None):
            partida_recebida["A"] = partida
            FECHAR.wait(30)
            original(jogo, apelido, config, custo, None)
        A.executar_jogo = executar_falso

        time.sleep(0.5)
        print("\n1. Antes de A hospedar")
        r = pedir(8792, "/api/partida/procurar")
        a = achar(r["colegas"], "Colega A")
        confere("A aparece online para B (TCP)", bool(a and a.get("online")))
        confere("A ainda sem partida", bool(a) and not a.get("partida_aberta"))

        print("\n2. A hospeda pela rota /api/jogar")
        jogo_a = achar_jogo_no_catalogo(pedir(8791, "/api/catalogo"), "Jogo de Teste")
        confere("catalogo de A tem o jogo de teste", bool(jogo_a))
        resp = pedir(8791, "/api/jogar", {"jogo_id": jogo_a["id"], "apelido": "Colega A",
                                          "partida": "hospedar"})
        confere("A abriu como jogador 1", resp.get("papel") == "jogador 1", str(resp.get("papel")))

        print("\n3. B procura de novo")
        r = pedir(8792, "/api/partida/procurar")
        a = achar(r["colegas"], "Colega A")
        confere("B ve a partida de A (TCP)", bool(a and a.get("partida_aberta")))
        confere("com o nome do jogo", bool(a) and a.get("jogo_partida", "").startswith("Jogo de Teste"),
                repr(a and a.get("jogo_partida")))
        confere("e o mesmo jogo (jogo_id)", bool(a) and a.get("jogo_id_partida") == jogo_a["id"])

        ola = pedir(8791, "/api/sinc/ola", {}, host="localhost")
        confere("/api/sinc/ola de A (pedido de fora) informa a partida",
                bool(ola.get("partida")))

        # So agora liga o grito UDP de A (e o ouvinte de B), na porta de
        # teste. Depois disso B passa a usar o IP de rede de A, que aqui nao
        # responde (A so escuta em 127.0.0.1) -- por isso o TCP vem antes.
        for modulo in (A, B):
            threading.Thread(target=modulo.anunciar_e_escutar, daemon=True).start()
        viu_udp = None
        limite = time.monotonic() + 12
        while time.monotonic() < limite and not viu_udp:
            time.sleep(0.5)
            viu_udp = next((c for c in pedir(8792, "/api/colegas")["colegas"]
                            if c.get("id") == id_a and c.get("partida_aberta")), None)
        confere("B ve a partida de A pelo grito UDP", bool(viu_udp),
                repr(viu_udp and viu_udp.get("jogo_partida")))

        print("\n4. O jogo de A fecha")
        FECHAR.set()
        limite = time.monotonic() + 10
        while time.monotonic() < limite and A.partida_aberta_agora():
            time.sleep(0.2)
        confere("A deixa de anunciar a partida", A.partida_aberta_agora() is None)
        time.sleep(6)   # proximo grito de A (a cada 5 s)
        some_udp = next((c for c in pedir(8792, "/api/colegas")["colegas"]
                         if c.get("id") == id_a), None)
        confere("grito UDP de A sem partida", bool(some_udp) and not some_udp.get("partida_aberta"))
        r = pedir(8792, "/api/partida/procurar")
        restos = [c for c in r["colegas"] if c.get("id") == id_a and c.get("partida_aberta")]
        confere("lista de B (UDP + TCP) sem a partida de A", not restos,
                json.dumps(restos, ensure_ascii=False)[:300])
        confere("A continua na lista, sem partida", any(c.get("id") == id_a for c in r["colegas"]))

        print("\n5. Só assistir")
        A.executar_jogo = lambda j, a, c, cu=None, p=None: partida_recebida.__setitem__("assistir", p)
        with A.TRAVA_JOGO:
            A.JOGO_EM_ANDAMENTO["ativo"] = False
        resp = pedir(8791, "/api/jogar", {"jogo_id": jogo_a["id"], "apelido": "Colega A",
                                          "partida": "assistir", "endereco": "http://10.0.0.9:8777"})
        montada = partida_recebida.get("assistir") or {}
        confere("assistir monta a partida (antes: None)", bool(montada))
        confere("assistir usa --connect no endereco do amigo",
                "--connect" in montada.get("argumentos", []) and
                "10.0.0.9" in montada.get("argumentos", []), str(montada.get("argumentos")))
        confere("papel = espectador", resp.get("papel") == "espectador", str(resp.get("papel")))
        confere("assistir NAO anuncia partida aberta", A.partida_aberta_agora() is None)
    except Exception as falha:
        import traceback
        traceback.print_exc()
        falhas.append("excecao: %s" % falha)
    finally:
        for srv in servidores:
            srv.shutdown()
            srv.server_close()
        for modulo_nome in ("arena_A", "arena_B"):
            m = sys.modules.get(modulo_nome)
            if m:
                m.VIGIA["encerrar"].set()
                try:
                    m.fechar_banco()
                except Exception:
                    pass
        time.sleep(1.5)
        for pasta in pastas:
            shutil.rmtree(pasta, ignore_errors=True)

    print("\nRESULTADO:", "PASSOU" if not falhas else "FALHOU (%s)" % ", ".join(falhas))
    return 0 if not falhas else 1


if __name__ == "__main__":
    sys.exit(main())
