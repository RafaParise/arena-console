# -*- coding: utf-8 -*-
r"""A tela conta por que o jogo nao abriu, e de onde vem o numero de jogadores.

Achados de 02/10/2026 (Rafael):
  - "o ARENA nao reconhece o motivo do kof2002 nao rodar": o servidor agora
    le o registro do emulador (servidor\motivo_do_erro.py); aqui se confere
    que a TELA mostra isso no alto quando o aluno volta do jogo, e no painel
    do jogo -- so para o jogo que ele acabou de abrir, e que some ao abrir
    o proximo;
  - "o Crash Nitro Kart nao reconhece mais de 2 controles, e ja ativei o
    multitap": a janela "Jogar junto neste computador" dizia "escolha o modo
    de 2, 3 ou 2 jogadores" e nao contava que o numero vem do
    dados\jogadores.txt (ligar pelo menu do PCSX2 nao vale: o ARENA arruma a
    configuracao a cada jogo).

ARENA isolado (copia temporaria), Edge sem janela. Nenhum jogo e' aberto.

Uso: servidor\python\python.exe testes\teste_tela_motivo.py
"""
import json
import os
import sys
import tempfile
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import limpeza  # noqa: E402
import tela_sem_janela  # noqa: E402
import teste_servidor_que_cai as servidor_de_teste  # noqa: E402

TEXTO = ("MAME não abriu este jogo. A BIOS está na pasta, mas com o nome errado: renomeie "
         "neogeo.mame.zip para neogeo.zip (o emulador só procura por esse nome).")


def main():
    falhas, total = [], [0]

    def confere(nome, ok, detalhe=""):
        total[0] += 1
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, "" if ok else detalhe), flush=True)
        if not ok:
            falhas.append(nome)

    pasta = tempfile.mkdtemp(prefix="arena_tela_motivo_")
    try:
        copia = os.path.join(pasta, "isolado", "ARENA")
        os.makedirs(copia)
        servidor_de_teste.preparar_copia(copia)
        porta = tela_sem_janela.porta_livre()
        processo = servidor_de_teste.subir(copia, porta, True, os.path.join(pasta, "sem-trava"))
        try:
            confere("o servidor isolado abriu", servidor_de_teste.esperar_servidor(porta))
            status, estado = servidor_de_teste.pedir(porta, "GET", "/api/estado")
            confere("/api/estado traz 'ultimo_problema' (vazio sem jogo nenhum)",
                    status == 200 and "ultimo_problema" in estado and estado["ultimo_problema"] is None,
                    (status, estado.get("ultimo_problema", "SEM A CHAVE")))
            with tela_sem_janela.Navegador() as nav:
                nav.comando("Runtime.enable")
                nav.abrir("http://127.0.0.1:%d/" % porta, espera=4)
                # Um jogo de mentira na lista da tela (a copia isolada nao tem jogos).
                nav.avaliar("estado.jogos.push({id: 'kof', titulo: 'The King of Fighters 2002', "
                            "plataforma: 'arcade', avisos: []}); 1")

                print("1. Por que nao abriu")
                problema = json.dumps({"jogo_id": "kof", "titulo": "The King of Fighters 2002", "texto": TEXTO})
                antes = nav.avaliar("document.querySelector('#aviso').hidden ? '' : "
                                    "document.querySelector('#avisoTexto').textContent") or ""
                if antes:
                    print("     (aviso que ja estava no alto ao abrir: %s)" % antes[:120])
                nav.avaliar("estado.jogoAberto = 'outro'; mostrarPorQueNaoAbriu(%s); 1" % problema)
                depois = nav.avaliar("document.querySelector('#aviso').hidden ? '' : "
                                     "document.querySelector('#avisoTexto').textContent") or ""
                confere("motivo de OUTRO jogo nao aparece", "neogeo.mame.zip" not in depois, depois[:200])
                nav.avaliar("marcarJogoAberto('kof'); mostrarPorQueNaoAbriu(%s); 1" % problema)
                texto = nav.avaliar("document.querySelector('#aviso').hidden ? '' : "
                                    "document.querySelector('#avisoTexto').textContent") or ""
                confere("ao voltar do jogo, o motivo aparece no alto", "renomeie neogeo.mame.zip" in texto
                        and texto.startswith("The King of Fighters 2002:"), texto)
                avisos = nav.avaliar("JSON.stringify(acharJogo('kof').avisos)") or ""
                confere("e fica no painel do jogo (\"Da última vez\")", "Da última vez: MAME não abriu" in avisos,
                        avisos)
                nav.avaliar("mostrarPorQueNaoAbriu(%s); 1" % problema)
                confere("aparece uma vez so (o painel nao repete o aviso)",
                        nav.avaliar("acharJogo('kof').avisos.length") == 1)
                nav.avaliar("marcarJogoAberto('outro'); 1")
                confere("abrir o proximo jogo tira o motivo do alto",
                        nav.avaliar("document.querySelector('#aviso').hidden") is True)

                print("2. Jogar junto neste computador")
                passos = nav.avaliar("abrirJuntoLocal({id: 'cnk', titulo: 'Crash Nitro Kart', plataforma: 'ps2', "
                                     "jogadores_max: 2}); document.querySelector('#juntoLocalPassos').innerText")
                passos = passos or ""
                confere("com 2 jogadores: 'o modo de 2 jogadores' (nao mais '2, 3 ou 2')",
                        "o modo de 2 jogadores" in passos and "2, 3 ou 2" not in passos, passos[:400])
                confere("diz que o numero vem do dados\\jogadores.txt, com o nome do jogo",
                        "dados\\jogadores.txt" in passos and "Crash Nitro Kart = 4" in passos, passos[:600])
                passos = nav.avaliar("abrirJuntoLocal({id: 'cnk', titulo: 'Crash Nitro Kart', plataforma: 'ps2', "
                                     "jogadores_max: 4}); document.querySelector('#juntoLocalPassos').innerText") or ""
                confere("com 4 jogadores: 'de 2 a 4'", "(de 2 a 4)" in passos, passos[:400])
                nav.foto(os.path.join(pasta, "junto_local.png"))
                nav.esperar(0.3)
                erros = [e["params"].get("exceptionDetails", {}).get("text") for e in nav.eventos
                         if e.get("method") == "Runtime.exceptionThrown"]
                confere("sem erro de JavaScript", not erros, erros)
        finally:
            servidor_de_teste.derrubar(processo)
    finally:
        time.sleep(0.5)
        limpeza.apagar_pasta(pasta)

    print()
    if falhas:
        print("FALHOU: %d de %d" % (len(falhas), total[0]))
        return 1
    print("Tela (motivo e jogadores): %d de %d certos." % (total[0], total[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
