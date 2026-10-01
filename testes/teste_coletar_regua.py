# -*- coding: utf-8 -*-
r"""COLETAR.bat: a regua e' a dos tetos APROVADOS (MAQUINA-ALVO.md, secao 7).

Frente 5 (01/10/2026). Confere, com numeros inventados e sem abrir o ARENA:
  - cada teto passa no limite exato e estoura logo acima (e o piso do FPS
    ao contrario);
  - a indexacao tem teto de 1,9 s por 100 jogos, e nunca menos que 1,9 s;
  - "nao medido" nunca vira PASSOU (o 4.140.000 FPS marcado [BOM] de
    27/09 nao pode voltar);
  - o selo do ARENA x o que a pessoa viu: otimista, pessimista, concorda;
  - o resumo sai inteiro com medicoes que falharam, avisa a bateria e
    termina na tabela de orcamentos;
  - os tetos daqui sao os mesmos numeros escritos no MAQUINA-ALVO.md.

Uso: servidor\python\python.exe testes\teste_coletar_regua.py
"""
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "ferramentas"))
import coletar_maquina  # noqa: E402
import medir_arena      # noqa: E402

NAO = medir_arena.NAO_MEDIU


def dados_no_teto():
    """Uma medicao inventada com TODO numero exatamente no teto."""
    return {
        "codigo_maquina": "TESTE00000", "medido_em": "2026-10-01T00:00:00", "duracao_s": 1,
        "energia": {"na_tomada": True},
        "abertura": {"janela_da_tela_s": 10.0, "bat_ate_o_python_s": 0.2,
                     "servidor_responde_s": 1.0, "dados_da_tela_prontos_s": 2.3,
                     "memoria_consumida_mb": 400},
        "servidor": {"parado": {"cpu_pct_de_um_nucleo": 2.0, "cpu_pct_da_maquina": 0.5, "ram_mb": 40,
                                "assentar": {"segundos": 5, "cpu_s_de_um_nucleo": 0.1,
                                             "fatias_pct_de_um_nucleo": [3.0, 0.4]}},
                     "em_uso": {"cpu_pct_da_maquina": 20, "pedidos": 100, "resposta_media_ms": 30,
                                "resposta_p95_ms": 100},
                     "ram_pico_mb": 64.0},
        "indexacao": {"segundos": 1.9, "total": 80, "por_console": {"snes": 80}},
        "gravacoes_parado": {"por_minuto": 0.5, "kb_por_minuto": 16.0, "arquivos_de_dados_que_mudaram": []},
        "jogo": {"jogo": "Teste (USA).sfc", "modo_modesto": False, "fps_medio": 59.0,
                 "variacao_dos_quadros_pct": 5.0, "tempo_de_abrir_s": 1.0,
                 "janela_do_jogo_a_frente_pct": 100},
        "respostas": "perguntas puladas",
    }


def main():
    falhas, total = [], [0]

    def confere(nome, ok, detalhe=""):
        total[0] += 1
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, detalhe if not ok else ""))
        if not ok:
            falhas.append(nome)

    # 1. No teto exato: tudo passa.
    d = dados_no_teto()
    linhas = {l["chave"]: l for l in medir_arena.orcamentos(d)}
    confere("9 itens na tabela (1a, 1b, 2, 3, 4, 5a, 5b, 6a, 6b)",
            sorted(linhas) == sorted(["1a", "1b", "2", "3", "4", "5a", "5b", "6a", "6b"]), str(sorted(linhas)))
    confere("no teto exato, todos passam", all(l["passou"] is True for l in linhas.values()),
            str([k for k, l in linhas.items() if l["passou"] is not True]))

    # 2. Um pouco acima (ou abaixo, no piso): cada um estoura sozinho.
    mexer = {
        "1a": ("abertura", "janela_da_tela_s", 10.01),
        "1b": ("abertura", "dados_da_tela_prontos_s", 2.31),
        "2": ("servidor", "ram_pico_mb", 64.1),
        "4": ("indexacao", "segundos", 1.91),
        "5a": ("gravacoes_parado", "por_minuto", 0.6),
        "5b": ("gravacoes_parado", "kb_por_minuto", 16.1),
        "6a": ("jogo", "fps_medio", 58.9),
        "6b": ("jogo", "variacao_dos_quadros_pct", 5.1),
    }
    for chave, (grupo, campo, valor) in mexer.items():
        d = dados_no_teto()
        d[grupo][campo] = valor
        tabela = {l["chave"]: l for l in medir_arena.orcamentos(d)}
        reprovados = [k for k, l in tabela.items() if l["passou"] is False]
        confere("item %s reprova sozinho com %s" % (chave, valor), reprovados == [chave], str(reprovados))
    d = dados_no_teto()
    d["servidor"]["parado"]["cpu_pct_de_um_nucleo"] = 8.4      # o Celeron de 27/09
    tabela = {l["chave"]: l for l in medir_arena.orcamentos(d)}
    confere("parado de 8,4% de um nucleo estoura o teto de 2%", tabela["3"]["passou"] is False)
    confere("selo do piso abaixo diz ABAIXO DO PISO",
            medir_arena.selo(dict(tabela["6a"], passou=False)) == "ABAIXO DO PISO")

    # 3. Indexacao: 1,9 s por 100 jogos, nunca menos que 1,9 s.
    confere("teto da indexacao com 50 jogos = 1,9 s", medir_arena.teto_da_indexacao(50) == 1.9)
    confere("teto da indexacao com 150 jogos = 2,85 s", medir_arena.teto_da_indexacao(150) == 2.85)
    confere("teto da indexacao sem total = 1,9 s", medir_arena.teto_da_indexacao(None) == 1.9)

    # 4. Nao medido nunca passa (nem com 4.140.000 FPS escondido num erro).
    d = dados_no_teto()
    d["jogo"] = {NAO: True, "motivo": "o jogo nao abriu"}
    d["abertura"]["janela_da_tela_s"] = {NAO: True, "motivo": "sem navegador"}
    tabela = {l["chave"]: l for l in medir_arena.orcamentos(d)}
    confere("jogo que falhou fica 'nao medido' (passou = None)",
            tabela["6a"]["passou"] is None and tabela["6b"]["passou"] is None)
    confere("janela que nao apareceu fica 'nao medido'", tabela["1a"]["passou"] is None)
    confere("selo de nao medido nao diz PASSOU", medir_arena.selo(tabela["6a"]) == "nao medido")
    d = dados_no_teto()
    d["jogo"]["fps_medio"] = True       # booleano nao e' numero
    confere("booleano no lugar do numero nao conta como medido",
            {l["chave"]: l for l in medir_arena.orcamentos(d)}["6a"]["passou"] is None)

    # 5. Selo do ARENA x o que a pessoa viu.
    etiquetas = {"ps2": {"etiqueta": "pesado", "rotulo": "Pode travar"},
                 "psp": {"etiqueta": "bem", "rotulo": "Roda bem"},
                 "xbox360": {"etiqueta": "nao_abre", "rotulo": "Não abre neste PC"},
                 "n64": {"etiqueta": "ajustes", "rotulo": "Roda com ajustes"},
                 "gamecube": {"etiqueta": "ajustes", "rotulo": "Roda com ajustes"}}
    respostas = {"consoles": {"ps2": "rodou bem", "psp": "travou ou lento demais",
                              "xbox360": "nao abriu", "n64": "rodou com engasgos",
                              "gamecube": "nao testei"}}
    comparados = {c["console"]: c["leitura"] for c in medir_arena.comparar_consoles(etiquetas, respostas)}
    confere("PS2 'Pode travar' que rodou bem = pessimista", comparados.get("PlayStation 2") == "pessimista",
            str(comparados))
    confere("PSP 'Roda bem' que travou = otimista demais", comparados.get("PSP") == "otimista demais")
    confere("Xbox 360 'Nao abre' que nao abriu = concorda", comparados.get("Xbox 360") == "concorda")
    confere("N64 'com ajustes' com engasgos = concorda", comparados.get("Nintendo 64") == "concorda")
    confere("console 'nao testei' fica de fora", "GameCube" not in comparados)
    confere("sem respostas, comparacao vazia", medir_arena.comparar_consoles(etiquetas, "puladas") == [])
    confere("etiquetas que falharam, comparacao vazia",
            medir_arena.comparar_consoles({NAO: True}, respostas) == [])

    # 6. Resumo: sai inteiro com falhas, avisa a bateria, termina na tabela.
    d = dados_no_teto()
    d["energia"] = {"na_tomada": False, "bateria_pct": 52}
    d["servidor"]["parado"]["cpu_pct_de_um_nucleo"] = 8.4
    d["jogo"] = {NAO: True, "motivo": "o RetroArch nao abriu"}
    d["consoles_comparados"] = medir_arena.comparar_consoles(etiquetas, respostas)
    d["orcamentos"] = medir_arena.orcamentos(d)
    texto = medir_arena.escrever_resumo(d)
    confere("resumo avisa NA BATERIA", "NA BATERIA" in texto)
    confere("resumo traz a tabela de orcamentos", "ORCAMENTOS" in texto and "ESTOUROU" in texto)
    confere("resumo conta quantos ficaram fora do teto", "1 fora do teto" in texto, texto[-400:])
    confere("resumo mostra a curva do assentar", "curva (% de um nucleo" in texto)
    confere("resumo mostra a discordancia do PSP", "DISCORDA (otimista demais)" in texto)
    confere("numeros com virgula (pt-BR)", "8,4%" in texto)
    texto_vazio = medir_arena.escrever_resumo({"codigo_maquina": "X", "medido_em": "-", "duracao_s": 0,
                                               "abertura": {NAO: True, "motivo": "a"},
                                               "servidor": {NAO: True, "motivo": "b"},
                                               "indexacao": {NAO: True, "motivo": "c"},
                                               "gravacoes_parado": {NAO: True, "motivo": "d"},
                                               "jogo": {NAO: True, "motivo": "e"}})
    confere("resumo com TUDO falhando nao quebra", "nao medido" in texto_vazio)

    # 7. Os tetos sao os do MAQUINA-ALVO.md (mesma regua nos dois lugares).
    doc = open(os.path.join(RAIZ, "docs", "MAQUINA-ALVO.md"), encoding="utf-8").read()
    resumo = doc.split("### Resumo", 1)[-1].split("### A regra da folga", 1)[0]
    esperado = {"1a": "10 s", "1b": "2,3 s", "2": "64 MB", "3": "2% de um núcleo",
                "4": "1,9 s por 100 jogos", "6": "59,0 FPS"}
    for item, texto_teto in esperado.items():
        confere("MAQUINA-ALVO.md, item %s, diz %s" % (item, texto_teto),
                re.search(r"\| %s \|.*%s" % (re.escape(item), re.escape(texto_teto)), resumo) is not None)
    confere("teto 1a do medidor = 10", medir_arena.TETOS["1a"]["teto"] == 10.0)
    confere("teto 1b do medidor = 2,3", medir_arena.TETOS["1b"]["teto"] == 2.3)
    confere("teto 2 do medidor = 64", medir_arena.TETOS["2"]["teto"] == 64.0)
    confere("teto 3 do medidor = 2", medir_arena.TETOS["3"]["teto"] == 2.0)
    confere("teto 5 do medidor = 1 em 2 min e 16 KB/min",
            medir_arena.TETOS["5a"]["teto"] == 0.5 and medir_arena.TETOS["5b"]["teto"] == 16.0)
    confere("piso 6 do medidor = 59 FPS e 5%",
            medir_arena.TETOS["6a"]["teto"] == 59.0 and medir_arena.TETOS["6b"]["teto"] == 5.0)

    # 8. Retrato: o resumo do selo de cada console.
    avaliacao = {"velocidade": {"operacoes_por_segundo": 3200000, "relativa_ao_alvo": 1.0},
                 "nota_antiga": {"geral": 4, "placa": 3}, "modo_economico": False,
                 "consoles": [{"id": "snes", "nome": "Super Nintendo", "etiqueta": "bem",
                               "rotulo": "Roda bem", "estado": "pronta"},
                              {"id": "xbox360", "nome": "Xbox 360", "etiqueta": "nao_abre",
                               "rotulo": "Não abre neste PC", "detalhe": "sem AVX", "estado": "pronta"},
                              {"id": "j2me", "nome": "Java ME", "etiqueta": "bem", "rotulo": "Roda bem",
                               "estado": "sem_core", "motivo": "Núcleo não instalado."}]}
    linhas_resumo = "\n".join(coletar_maquina.resumo_da_avaliacao(avaliacao))
    confere("retrato lista quem 'Roda bem'", "Roda bem (2): Super Nintendo, Java ME" in linhas_resumo,
            linhas_resumo)
    confere("retrato explica o 'Nao abre'", "Xbox 360: sem AVX" in linhas_resumo)
    confere("retrato separa 'falta arquivo' de maquina fraca", "Falta arquivo" in linhas_resumo)
    confere("retrato com avaliacao que falhou nao quebra",
            "nao foi possivel medir" in "\n".join(coletar_maquina.resumo_da_avaliacao({NAO: True, "motivo": "x"})))

    print()
    if falhas:
        print("FALHOU: %d de %d" % (len(falhas), total[0]))
        return 1
    print("Regua do COLETAR: %d de %d certos." % (total[0], total[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
