# -*- coding: utf-8 -*-
r"""Jogar Junto: o SEXTO jogador tentando entrar numa partida de 5.

O roteiro da auditoria (Fase 4) pede: "sexto jogador tentando entrar
(precisa receber uma mensagem clara)". A auditoria 1 deixou para depois
(so entravam 4); desde a revisao pos-auditoria entram 5 (o Multitap do
Super Bomberman 4, com netplay_max_connections = 4). Este teste faz a sexta
maquina tentar.

Com o RetroArch de verdade, tudo neste computador (127.0.0.1), cada um com a
sua pasta temporaria: o hospedeiro e 4 convidados entram (como no
teste_netplay_5_jogadores); depois o sexto tenta. Confere:
  1. os 5 primeiros entram;
  2. o sexto NAO entra como jogador (o hospedeiro nao anuncia "se juntou");
  3. o que o sexto recebe e' uma mensagem (o registro dele mostra o porque,
     e a frase sai em portugues, que e' a lingua do menu do ARENA);
  4. o hospedeiro e os outros 4 continuam vivos depois da tentativa.
O texto exato que o sexto recebe fica impresso: e' o que vai para o
relatorio e para o roteiro de sala.

Uso: servidor\python\python.exe testes\teste_netplay_sexto_jogador.py
"""
import os
import subprocess
import sys
import tempfile
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import limpeza  # noqa: E402
import protege_cfg  # noqa: E402
import teste_netplay_5_jogadores as base  # noqa: E402


def registro(pasta):
    candidatos = sorted(n for n in os.listdir(pasta) if n.startswith("retroarch__") and n.endswith(".log"))
    if not candidatos:
        return ""
    with open(os.path.join(pasta, candidatos[-1]), encoding="utf-8", errors="ignore") as f:
        return f.read()


def main():
    falhas, total = [], [0]

    def confere(nome, ok, detalhe=""):
        total[0] += 1
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, "" if ok else detalhe), flush=True)
        if not ok:
            falhas.append(nome)

    if not os.path.isfile(base.JOGO):
        print("FALHOU: sem o Super Bomberman 4 em jogos\\pessoais\\Super Nintendo.")
        return 1
    arena, graficos = base.carregar_modulos()
    raiz_teste = tempfile.mkdtemp(prefix="arena_netplay6_")
    papeis = [{"nome": "hospedeiro", "hospedar": True, "jogador": 1, "apelido": "Anfitriao"}]
    papeis += [{"nome": "convidado%d" % n, "hospedar": False, "jogador": n, "apelido": "Jogador%d" % n}
               for n in range(2, 6)]
    papeis.append({"nome": "sexto", "hospedar": False, "jogador": None, "apelido": "Sexto"})
    processos = []
    manter_pasta = True
    try:
        pasta_host = None
        for papel in papeis:
            pasta = os.path.join(raiz_teste, papel["nome"])
            os.makedirs(pasta)
            if papel["hospedar"]:
                pasta_host = pasta
            opcoes = graficos.opcoes_de_partida(apelido=papel["apelido"], hospedar=papel["hospedar"],
                                                jogador=papel["jogador"], multitap=True)
            argumentos = graficos.argumentos_de_partida(papel["hospedar"], endereco="127.0.0.1",
                                                        porta=base.PORTA_PARTIDA)
            cfg = base.montar_override(os.path.join(pasta, "override.cfg"), pasta, arena, graficos, opcoes)
            saida = open(os.path.join(pasta, "stdout.log"), "w", encoding="utf-8")
            processo = subprocess.Popen([base.RETROARCH, "-L", base.CORE, "--appendconfig", cfg] + argumentos
                                        + [base.JOGO], cwd=base.RAIZ, stdout=saida, stderr=subprocess.STDOUT)
            processos.append({"papel": papel, "processo": processo, "pasta": pasta, "log": saida})
            print("Abrindo %s..." % papel["nome"], flush=True)
            if papel["hospedar"]:
                time.sleep(10)
            elif papel["nome"] != "sexto":
                t = base.esperar_conexao(pasta_host, papel["apelido"], tempo_limite=15.0)
                print("    entrou em %s" % ("%.2f s" % t if t is not None else "NAO ENTROU"), flush=True)
                time.sleep(2)

        print("O sexto tentou; esperando 15 s...", flush=True)
        entrou_o_sexto = base.esperar_conexao(pasta_host, "Sexto", tempo_limite=15.0)
        time.sleep(3)
        texto_host = registro(pasta_host).lower()
        texto_sexto = registro(processos[-1]["pasta"])
        linhas_do_sexto = [l.strip() for l in texto_sexto.splitlines() if "netplay" in l.lower()]
        print("\n--- O que o registro do sexto diz sobre o Jogar Junto ---")
        for linha in linhas_do_sexto[-12:]:
            print("   ", linha[:200])
        print("--- O que o registro do hospedeiro diz depois da tentativa ---")
        for linha in [l.strip() for l in registro(pasta_host).splitlines() if "netplay" in l.lower()][-8:]:
            print("   ", linha[:200])

        juntou = [p["papel"]["apelido"] for p in processos[1:5]
                  if ("%s se juntou" % p["papel"]["apelido"]).lower() in texto_host]
        confere("os 5 primeiros entraram (hospedeiro + 4)", len(juntou) == 4, juntou)
        confere("o sexto NAO entrou como jogador", entrou_o_sexto is None, entrou_o_sexto)
        motivo = [l for l in linhas_do_sexto if any(p in l.lower() for p in (
            "cheio", "full", "vaga", "slot", "recus", "refus", "desconect", "disconnect", "não foi possível",
            "nao foi possivel", "falh", "fail", "rejeit", "reject"))]
        confere("o registro do sexto diz o porque (servidor cheio / sem vaga / recusado)", bool(motivo),
                linhas_do_sexto[-6:])
        vivos = [p["papel"]["nome"] for p in processos[:5] if p["processo"].poll() is None]
        confere("o hospedeiro e os 4 convidados continuam abertos depois da tentativa", len(vivos) == 5, vivos)
        manter_pasta = bool(falhas)
    finally:
        for p in processos:
            try:
                p["processo"].terminate()
            except OSError:
                pass
        time.sleep(2)
        for p in processos:
            try:
                if p["processo"].poll() is None:
                    p["processo"].kill()
            except OSError:
                pass
            try:
                p["log"].close()
            except OSError:
                pass
        if manter_pasta:
            print("\nRegistros guardados em", raiz_teste, "(apague a pasta depois de olhar).")
        else:
            limpeza.apagar_pasta(raiz_teste)

    print()
    if falhas:
        print("FALHOU: %d de %d" % (len(falhas), total[0]))
        return 1
    print("Sexto jogador: %d de %d certos." % (total[0], total[0]))
    return 0


if __name__ == "__main__":
    sys.exit(protege_cfg.rodar(main))
