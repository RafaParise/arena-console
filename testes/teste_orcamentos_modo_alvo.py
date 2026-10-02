# -*- coding: utf-8 -*-
r"""Teste que REPROVA: os orcamentos do notebook-alvo, medidos no modo alvo.

Tarefa 4 do Rafael (pausada em 30/09, feita em 02/10/2026). Entra na caixa
do modo alvo (ferramentas\modo_alvo.py: 2 processadores com teto de
processador, 3,8 GB de memoria, prioridade abaixo do normal) e roda as
MESMAS medicoes do COLETAR.bat (ferramentas\medir_arena.py: abre o ARENA de
verdade pelo ARENA.bat, mede o servidor, a lista de jogos, as gravacoes em
disco parado e um jogo de Super Nintendo), sem as perguntas. No fim, a
tabela que o Rafael pediu: item, medido, teto, passou ou nao -- e reprova
apontando qual orcamento estourou.

Tetos: docs\MAQUINA-ALVO.md, secao 7 (os mesmos do medir_arena.TETOS).
Ajuste de um item so: "processador parado" e' medido em % de um nucleo
DESTE PC; a caixa deixa o trabalho mais lento, mas nao mais caro -- o mesmo
trabalho custa ~2,3x mais num nucleo do Celeron (modo_alvo.VELOCIDADE_PCT),
entao o medido e' multiplicado por isso antes de comparar.

Item sem medicao (ex.: sem jogo de Super Nintendo na pasta, ou com
ARENA_SEM_JANELA, que nao abre a tela) aparece como "nao medido" e nao
reprova. Leva uns 6 minutos e abre um jogo de SNES por ~70 s.

Rotina (pedido do Rafael): "Rode a bateria no modo alvo e me mostre a
tabela de orcamentos: medido, teto e passou ou nao. Se algo estourou,
aponte a causa antes de propor conserto."

Uso: servidor\python\python.exe testes\teste_orcamentos_modo_alvo.py
"""
import os
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(RAIZ, "ferramentas"))
import limpeza  # noqa: E402
import modo_alvo  # noqa: E402


def main():
    try:
        descricao = modo_alvo.entrar()
    except OSError as falha:
        print("Nao deu para entrar no modo alvo: %s" % falha)
        return 1
    print("Dentro do " + descricao)
    print("(nao imita disco lento, placa de video fraca nem falta de AVX: isso so a coleta de la)\n",
          flush=True)
    import medir_arena  # depois de entrar: o ARENA e o jogo nascem dentro da caixa

    pasta = tempfile.mkdtemp(prefix="arena_orcamentos_alvo_")
    try:
        _pasta, _texto = medir_arena.medir(pasta, pular_perguntas=True)
        import json
        dados = json.load(open(os.path.join(pasta, "arena.json"), encoding="utf-8"))
    finally:
        limpeza.apagar_pasta(pasta)

    fator = 100.0 / modo_alvo.VELOCIDADE_PCT
    # Regra 8 do MAQUINA-ALVO.md (e do CLAUDE.md): numero medido com a janela
    # do jogo coberta, ou na bateria, nao decide nada. Achado de 02/10/2026:
    # 51,7 FPS e 22% de variacao de madrugada, com a janela do jogo atras do
    # terminal -- o mesmo 51,7 de 30/09 com o navegador por cima.
    jogo = dados.get("jogo") or {}
    a_frente = jogo.get("janela_do_jogo_a_frente_pct")
    na_bateria = (dados.get("energia") or {}).get("na_tomada") is False
    nao_vale = {}
    if na_bateria:
        nao_vale.update({c: "na bateria" for c in ("1a", "1b", "3", "4", "6a", "6b")})
    if a_frente is not None and a_frente < 80:
        nao_vale.update({"6a": "janela do jogo coberta (%d%% a frente)" % a_frente,
                         "6b": "janela do jogo coberta (%d%% a frente)" % a_frente})
    # A saida de som segurando o ritmo (02/10/2026: headset sem fio desligado
    # -> 52 FPS; sem seguir o som, 60,1): nao e' o processador.
    if jogo.get("som_segura_o_ritmo"):
        motivo = "a saida de som segura o ritmo (sem ela: %s FPS)" % jogo.get("fps_sem_sincronia_pelo_som")
        nao_vale.update({"6a": motivo, "6b": motivo})
    estourados = []
    print("\nORCAMENTOS NO MODO ALVO (teto do notebook-alvo, docs\\MAQUINA-ALVO.md secao 7)")
    print("%-4s %-52s %12s %10s  %s" % ("item", "", "medido", "teto", "resultado"))
    for linha in dados["orcamentos"]:
        medido = linha["medido"]
        nota = ""
        if linha["chave"] == "3" and medido is not None:
            medido = round(medido * fator, 2)
            nota = " (x%.1f: num nucleo do Celeron)" % fator
        if medido is None:
            resultado = "nao medido"
        elif linha["chave"] in nao_vale:
            resultado = "NAO VALE: " + nao_vale[linha["chave"]]
        else:
            passou = medido >= linha["teto"] if linha["piso"] else medido <= linha["teto"]
            resultado = "PASSOU" if passou else "ESTOUROU"
            if not passou:
                estourados.append("%s %s: %s %s (teto %s)" % (linha["chave"], linha["item"], medido,
                                                              linha["unidade"], linha["teto"]))
        print("%-4s %-52s %12s %10s  %s%s" % (linha["chave"], linha["item"][:52],
                                              "-" if medido is None else "%s %s" % (medido, linha["unidade"]),
                                              ("%s %s" % ("min" if linha["piso"] else "max", linha["teto"])),
                                              resultado, nota))
    print()
    if estourados:
        print("REPROVOU: %d orcamento(s) estourado(s) no modo alvo:" % len(estourados))
        for item in estourados:
            print("  - " + item)
        print("Antes de propor conserto: apontar a causa (medir de novo, olhar o que mudou).")
        return 1
    print("Orcamentos no modo alvo: nenhum estourou.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
