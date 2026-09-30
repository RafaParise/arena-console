# -*- coding: utf-8 -*-
r"""Dois ARENAs isolados num computador so, para VER a tela do Jogar Junto.

Sobe duas copias temporarias do ARENA (com um jogo de mentira):
  - "Colega A" na porta 8791, ja com a partida aberta ("Eu abro a partida");
  - "Colega B" na porta 8792, com A salvo como amigo.
Abra http://127.0.0.1:8792 no navegador (e' o computador do convidado),
clique em Jogar junto no "Jogo de Teste" e em "Entrar na partida do amigo".

Nenhum arquivo do ARENA de verdade e' tocado; o RetroArch e' de mentira
(nenhum jogo abre de fato). Fecha sozinho depois de N segundos (padrao 600)
ou com Ctrl+C, e apaga as copias.

Uso: servidor\python\python.exe testes\abrir_dois_arenas.py [segundos] [--duas]
     --duas  sobe tambem "Colega C" (porta 8793) com OUTRA partida aberta,
             para ver a lista com mais de uma partida.
"""
import os
import shutil
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import teste_partida_aparece as base  # noqa: E402


def subir(nome, porta, apelido, servidores=(), como_colega=False):
    pasta, modulo = base.montar_copia(nome, porta)
    cfg = modulo.carregar_config()
    cfg.update(apelido=apelido, permitir_rede=True, servidores=list(servidores))
    modulo.salvar_config(cfg)

    manipulador = modulo.Manipulador
    if como_colega:
        class ManipuladorColega(modulo.Manipulador):
            # Pedido pelo nome "localhost" = outra maquina (a trava de rede vale).
            def pedido_e_local(self):
                return not (self.headers.get("Host") or "").startswith("localhost")
        manipulador = ManipuladorColega
    srv = modulo.Servidor(("127.0.0.1", porta), manipulador)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return pasta, modulo, srv, cfg["dispositivo_id"]


def abrir_partida(modulo, porta, fechar):
    def executar_falso(*args, **kwargs):
        fechar.wait()     # "jogo aberto" ate o fim
    modulo.executar_jogo = executar_falso
    jogo = base.achar_jogo_no_catalogo(base.pedir(porta, "/api/catalogo"), "Jogo de Teste")
    base.pedir(porta, "/api/jogar", {"jogo_id": jogo["id"], "partida": "hospedar"})


def main():
    segundos = next((int(a) for a in sys.argv[1:] if a.isdigit()), 600)
    fechar = threading.Event()
    subidos = []
    try:
        pasta_a, A, srv_a, id_a = subir("A", 8791, "Colega A", como_colega=True)
        subidos.append((pasta_a, A, srv_a))
        amigos = [{"apelido": "Colega A", "url": "http://localhost:8791", "id": id_a}]
        if "--duas" in sys.argv:
            pasta_c, C, srv_c, id_c = subir("C", 8793, "Colega C", como_colega=True)
            subidos.append((pasta_c, C, srv_c))
            amigos.append({"apelido": "Colega C", "url": "http://localhost:8793", "id": id_c})
        pasta_b, B, srv_b, _ = subir("B", 8792, "Colega B", servidores=amigos)
        subidos.append((pasta_b, B, srv_b))

        abrir_partida(A, 8791, fechar)
        if "--duas" in sys.argv:
            abrir_partida(C, 8793, fechar)
        print("PRONTO: abra http://127.0.0.1:8792 (tela do convidado). "
              "Fecha em %d s." % segundos, flush=True)
        fim = time.monotonic() + segundos
        while time.monotonic() < fim:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        fechar.set()
        for pasta, modulo, srv in subidos:
            srv.shutdown()
            srv.server_close()
            modulo.VIGIA["encerrar"].set()
            try:
                modulo.fechar_banco()
            except Exception:
                pass
        time.sleep(1.0)
        for pasta, _, _ in subidos:
            shutil.rmtree(pasta, ignore_errors=True)
        print("Fechado e apagado.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
