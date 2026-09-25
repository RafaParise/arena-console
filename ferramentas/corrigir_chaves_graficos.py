# -*- coding: utf-8 -*-
r"""Auditoria 2, Fase 2: tira do servidor\graficos.json as chaves que os
nucleos nao conhecem e troca as que mudaram de nome (conferido dentro de
cada .dll com testes\chaves_graficos_vs_nucleos.py e
ferramentas\opcoes_do_nucleo.py). Roda uma vez so.

  - swanstation: "duckstation_GPU.X" e "swanstation_GPU.X" (com ponto) nao
    existem; a forma certa "swanstation_GPU_X" ja esta ao lado de cada uma.
  - genesis_plus_gx_blargg_ntsc_md    -> genesis_plus_gx_blargg_ntsc_filter
  - ppsspp_disable_slow_framebuffer_effects -> ppsspp_skip_gpu_readbacks
  - ppsspp_rendering_mode             -> ppsspp_skip_buffer_effects = "disabled"
    (o valor antigo do modesto pedia "pular efeitos de buffer", que o
    proprio nucleo avisa: "em alguns jogos nada e' desenhado". Nunca chegou
    a valer; ligar agora, sem teste, arriscaria tela preta no PSP.)
  - pcsx2_frameskip: nao existe mais no nucleo; sai.

Mantem a ordem das chaves e o recuo de 2 espacos do arquivo.
"""
import json
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQUIVO = os.path.join(RAIZ, "servidor", "graficos.json")
RENOMEAR = {"genesis_plus_gx_blargg_ntsc_md": "genesis_plus_gx_blargg_ntsc_filter",
            "ppsspp_disable_slow_framebuffer_effects": "ppsspp_skip_gpu_readbacks",
            "ppsspp_rendering_mode": "ppsspp_skip_buffer_effects"}
REMOVER = {"pcsx2_frameskip"}
contagem = {"removidas": 0, "renomeadas": 0}


def limpar(opcoes):
    novo = {}
    for chave, valor in opcoes.items():
        if chave.startswith("duckstation_") or chave.startswith("swanstation_GPU.") or chave in REMOVER:
            contagem["removidas"] += 1
            continue
        if chave in RENOMEAR:
            contagem["renomeadas"] += 1
            if chave == "ppsspp_rendering_mode":
                valor = "disabled"
            chave = RENOMEAR[chave]
        novo[chave] = valor
    return novo


dados = json.load(open(ARQUIVO, encoding="utf-8"))
for info in dados.get("nucleos", {}).values():
    if "sempre" in info:
        info["sempre"] = limpar(info["sempre"])
    for bloco in info.get("por_nota", []):
        bloco["opcoes"] = limpar(bloco.get("opcoes", {}))
for nome, opcoes in list(dados.get("modesto", {}).items()):
    if isinstance(opcoes, dict):
        dados["modesto"][nome] = limpar(opcoes)
for excecao in dados.get("excecoes", {}).values():
    for bloco in excecao.get("por_nota", []) if isinstance(excecao, dict) else []:
        bloco["opcoes"] = limpar(bloco.get("opcoes", {}))

with open(ARQUIVO, "w", encoding="utf-8", newline="\n") as f:
    json.dump(dados, f, ensure_ascii=False, indent=2)
    f.write("\n")
print("removidas: %(removidas)d, renomeadas: %(renomeadas)d" % contagem)
