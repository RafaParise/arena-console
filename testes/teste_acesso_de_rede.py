# -*- coding: utf-8 -*-
"""Fase 3, achado maior: confere que a lista ROTAS_REDE_EXTERNA de verdade
bloqueia rota sensivel quando o pedido NAO vem deste computador.

Nao da pra simular um IP de outra maquina de verdade sem uma segunda
maquina fisica (a deteccao usa o endereco real do socket, que o proprio
Python garante). Em vez disso, subclassa o Manipulador so pra forcar
pedido_e_local() a devolver False -- exatamente a condicao que uma rede de
verdade produziria -- e confere que:
  1. uma rota da lista (ex.: /api/colegas) continua respondendo normal;
  2. uma rota QUALQUER fora da lista (ex.: /api/config, /api/perfil/novo,
     /api/jogar) e recusada com 403, sem executar nada.
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


def requisicao(metodo, caminho, corpo=None):
    dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
    headers = {"Content-Type": "application/json"} if dados is not None else {}
    req = urllib.request.Request("http://127.0.0.1:8777" + caminho, data=dados,
                                  method=metodo, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def main():
    # O ARENA isolado numa SUBPASTA do temporario: a mala do pen drive vai
    # para a pasta de cima (caminho_da_mala), e com o ARENA direto no Temp
    # ela ficava esquecida no Temp do Windows (achado de 01/10/2026).
    destino = os.path.join(tempfile.mkdtemp(prefix="arena_rede_"), "ARENA")
    os.makedirs(destino)
    try:
        for pasta in ("servidor", "dados", "launcher"):
            shutil.copytree(os.path.join(RAIZ, pasta), os.path.join(destino, pasta),
                             ignore=shutil.ignore_patterns("__pycache__", "tests"))
        # A copia herda o tema que o professor escolheu de verdade; se ele
        # ja usa "escuro", o teste abaixo (que tenta mudar PARA escuro)
        # acusava falha sem ter havido invasao nenhuma (visto em 25/09/2026).
        # Fixa "claro" so NA COPIA; o dados\ real nao e' tocado.
        cfg_copia = os.path.join(destino, "dados", "config.json")
        cfg = json.load(open(cfg_copia, encoding="utf-8"))
        cfg["tema"] = "claro"
        json.dump(cfg, open(cfg_copia, "w", encoding="utf-8"), ensure_ascii=False)

        spec = importlib.util.spec_from_file_location(
            "arena_rede_teste", os.path.join(destino, "servidor", "arena.py"))
        arena = importlib.util.module_from_spec(spec)
        sys.path.insert(0, os.path.join(destino, "servidor"))
        spec.loader.exec_module(arena)

        class ManipuladorRemoto(arena.Manipulador):
            """Finge que TODO pedido vem de outra maquina na rede --
            e exatamente a condicao real quando permitir_rede esta ligado
            e outro aluno acessa pelo IP."""
            def pedido_e_local(self):
                return False

        servidor = arena.Servidor(("127.0.0.1", 8777), ManipuladorRemoto)
        thread = threading.Thread(target=servidor.serve_forever, daemon=True)
        thread.start()
        time.sleep(0.5)

        print("Rotas permitidas (allowlist) -- tem que continuar funcionando:")
        ok_permitidas = True
        for metodo, caminho, corpo in [
            ("GET", "/api/colegas", None),
            ("GET", "/api/ranking", None),
            ("POST", "/api/sinc/ola", {}),
            ("POST", "/api/amigo/testar", {"url": "127.0.0.1:8777"}),
        ]:
            status, resp = requisicao(metodo, caminho, corpo)
            passou = status != 403
            ok_permitidas = ok_permitidas and passou
            print("  %s %-25s status=%s %s" % (metodo, caminho, status, "OK" if passou else "BLOQUEOU (bug!)"))

        print("\nRotas sensiveis -- tem que ser RECUSADAS (403) vindas de fora:")
        ok_bloqueadas = True
        for metodo, caminho, corpo in [
            ("POST", "/api/config", {"tema": "escuro"}),
            ("POST", "/api/perfil/novo", {"confirmar": "sim"}),
            ("POST", "/api/jogar", {"jogo_id": "qualquer"}),
            ("POST", "/api/cheat/adicionar", {"jogo_id": "x", "codigo": "AAAA"}),
            ("POST", "/api/mala", {}),
            ("GET", "/api/estado", None),
            ("GET", "/api/catalogo", None),
            # Rotas novas de 02/10/2026: abrir pasta no Explorador e buscar
            # capas -- so deste computador.
            ("POST", "/api/pasta/abrir", {"plataforma": "snes"}),
            ("POST", "/api/capas/buscar-faltando", {}),
            ("POST", "/api/capas/parar", {}),
            ("GET", "/api/capas/progresso", None),
            ("GET", "/api/como-colocar", None),
        ]:
            status, resp = requisicao(metodo, caminho, corpo)
            passou = status == 403
            ok_bloqueadas = ok_bloqueadas and passou
            print("  %s %-25s status=%s %s" % (metodo, caminho, status, "OK, recusado" if passou else "NAO BLOQUEOU (bug grave!)"))

        # confere que o tema NAO mudou (a tentativa de config foi mesmo
        # recusada antes de executar, nao so a resposta que mentiu)
        tema_depois = json.load(open(os.path.join(destino, "dados", "config.json"), encoding="utf-8")).get("tema")
        print("\nConfig realmente NAO foi alterada (tema continua 'claro'):", tema_depois == "claro")

        servidor.shutdown()
        servidor.server_close()

        ok = ok_permitidas and ok_bloqueadas and tema_depois == "claro"
        print("\nRESULTADO:", "PASSOU" if ok else "FALHOU")
        return 0 if ok else 1
    finally:
        sys.path = [p for p in sys.path if not p.startswith(destino)]
        shutil.rmtree(os.path.dirname(destino), ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
