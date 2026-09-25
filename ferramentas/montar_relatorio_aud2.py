# -*- coding: utf-8 -*-
"""Auditoria 2, Fase 8: encaixa as Fases 5 e 6 antes da Fase 7 no relatorio
e acrescenta a Fase 8 no fim. Roda uma vez so (confere se ja foi feito)."""
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RELATORIO = os.path.join(RAIZ, "docs", "RELATORIO-AUDITORIA-2.md")

FASES_5_6 = """## Fase 5 — Matriz de jogos

`testes\\teste_matriz_jogos.py` com RetroArch de verdade, agora com **7
consoles** (o Mega Drive entrou nesta rodada): N64, SNES, PS1, Dreamcast,
PSP, Mega Drive e Neo Geo. Todos abrem e mostram imagem; salvar e carregar
estado funciona em 6 — o Neo Geo continua barrado pela mesma BIOS de revisão
errada já registrada (não é achado novo). O teste liga os comandos de rede
do RetroArch **só no arquivo dele**, com `config_save_on_exit = "false"`,
para nunca gravar isso no `retroarch.cfg` de verdade (ver "network_cmd_enable
sempre false" no CLAUDE.md).

Também rodados: ajuste de imagem chegando ao núcleo de verdade
(`teste_opcoes_nucleo_ponta_a_ponta`, `teste_qual_opcao_de_nucleo_vale`), 4
jogadores locais no N64, PS3 sem firmware (avisa em vez de piscar e fechar).
**Sem mudança de código nesta fase.** PS2 (PCSX2), Xbox 360 (Xenia) e PS3
com firmware continuam no roteiro de sala (Roteiro 8), como na primeira
auditoria.

---

## Fase 6 — Portabilidade e robustez

Rodados de novo, todos OK: queda de energia no meio da gravação, arquivos
corrompidos (config, controles, banco), disco cheio, pasta somente leitura,
caminho comprido (aviso do verificador), FAT32 com arquivo de 4 GB − 1,
caminho de fora no `retroarch.cfg`, pasta movida (conserta os caminhos
sozinha) e o PowerShell bloqueado/restrito (Fase 3).

### Achado — o teste de pasta movida deixava 182 MB fora da pasta (corrigido)

`ferramentas\\teste_aceite_pasta_movida.py` copiava o ARENA para uma pasta
irmã para provar que ele se conserta sozinho — e **nunca apagava a cópia**,
que levava junto uma cópia do `dados\\` (recordes, apelido). Agora apaga no
fim, passe ou falhe, tirando antes o somente leitura do cache do PS1 (Fase 2),
que travava o `rmtree`. Entrou na rodada final.

### Achado — guia 6 com a lista errada do que a atualização traz (corrigido)

A lista de "o que copiar ao atualizar" não tinha `PARTIDA.bat`, `COLETAR.bat`
nem `ferramentas\\`, e dizia que `emuladores\\` era só PCSX2/Dolphin (tem RPCS3
e Xenia). `perfil\\` (saída do coletor) entrou como pasta do usuário, que não
se sobrescreve.

---

"""

FASE_8 = """
---

## Fase 8 — Relatório final e entrega

### Rodada final de todos os testes

`ferramentas\\rodada_final.py` (bateria + fuzz + todos os `testes\\teste_*.py`,
com RetroArch de verdade onde o teste pede; entraram nesta rodada o
verificador de acentos e o teste de pasta movida): **42 de 42**. Bateria
`servidor\\tests\\run.py`: **71 de 71** (eram 45 na Fase 0: +22 das barreiras,
+4 do cache do PS1). Fuzz: 258 checagens, 0 falhas. Bruto:
`docs\\rodada_final_bruta.json`.

### Antes × depois (mesma máquina, Ryzen 5 5600G)

Brutos: `docs\\auditoria2\\linha_base_fase0.json` × `linha_base_fase8.json`,
`medir_fase0\\` × `medir_fase8\\`.

| Medida | Fase 0 | **Fase 8** |
|---|---|---|
| Testes de referência | 45/45 + 36/36 | **71/71 + 42/42** |
| Pacote sem jogos | 2.845,1 MB | **2.845,5 MB** (igual) |
| Linhas do produto | 23.186 em 33 arquivos | **24.126 em 34** (+940: `barreiras.py` e a tela dele, o item 11 do verificador) |
| Rotas (caminhos / pares caminho+método) | 50 / 51 | **51 / 52** (−1 `/api/sinc/ranking`; +2 das barreiras, só deste computador) |
| Rotas abertas à rede | 8 | **8** |
| Rotas sem chamador | 1 | **0** |
| Abertura (página responde) | 0,62 s | **0,52–0,63 s** |
| Dados da tela prontos | 0,54 s | **0,54 s** |
| Memória tomada do Windows | 76–141 MB | **84 MB** |
| CPU parado | 0,02% | **0,01–0,03%** |
| RAM do servidor parado | 36,0 MB | **36,2–36,4 MB** |
| Threads | 14 | **14** |
| Portas em escuta (rede desligada) | só 127.0.0.1:8777 | **só 127.0.0.1:8777** |
| Servidor em uso (20 s) | 7,5%, 4.044 pedidos, 4,9 ms | **7,5%, 4.172 pedidos, 4,8 ms** |
| Releitura da lista de jogos | 35 em 0,14 s | **35 em 0,14 s** |
| Gravações em disco parado | 0/min | **0/min** |
| SNES | 60,0 FPS, variação 3,2%, CPU 0,6% | **60,0 FPS, variação 3,1%, CPU 0,5%** |
| Chaves de imagem que não existiam no núcleo | 28 (37 ocorrências) | **0** |
| Frases de tela sem acento | ~110 | **0** |
| Arquivos que o VERIFICAR confere | 13 | **20** |

Nesta máquina o ganho do ARENA parado é zero porque já era zero. Os ganhos
desta rodada estão onde esta máquina não mostra: **pen drive** (cache do PS1
sem regravação de 15–50 MB por partida) e **máquina da escola** (barreiras de
lentidão identificadas com ação para o aluno ou para a TI).

### Removido (Fase 1, com prova)

R1 `/api/sinc/ranking`; R2 `registros_pendentes()`; R3 CSS
`.jogo--desaparecendo`; R4 regra CSS duplicada. Mais, na Fase 2, as 37
ocorrências de chaves de núcleo que não existiam.

### Corrigido

| Fase | O quê |
|---|---|
| 2 | 28 chaves de opção inexistentes (Mega Drive ganha o filtro NTSC de verdade) |
| 2 | Cache do PS1 regravado inteiro a cada partida (econômico) |
| 2 | Rodízio de registros só na abertura |
| Extra | O ARENA e o testador identificam o que deixa o computador lento e recomendam ação |
| 3 | Diagnóstico e coletor perdiam listas em silêncio com PowerShell restrito |
| 3 | VERIFICAR não conferia 7 arquivos sem os quais o ARENA não abre |
| 6 | Teste de pasta movida deixava 182 MB (com dados do aluno) fora da pasta |
| 6 | Guia 6 com a lista errada da atualização |
| 7 | ~110 mensagens de tela sem acento |

### O que falta (não dá para fechar nesta máquina)

- **Roteiros 9, 10 e 11** (acima) e os 8 da primeira auditoria.
- **Números do Celeron**: `COLETAR.bat` na escola → recalibrar os limites
  do `medir_arena.py` e decidir o `ppsspp_skip_buffer_effects` do modo
  modesto (Fase 2).
- Continuam do Rafael: firmware do PS3, BIOS do Neo Geo, conta RPCN, Mario
  Kart 64 para o HUD com `parallel-rdp`, repasse entre operadoras.

### Entrega

Mesmas decisões da primeira auditoria: commit do relatório, junção
`auditoria` → `main` sem avanço rápido (histórico das fases preservado),
ramo `auditoria` mantido.
"""


def principal():
    texto = open(RELATORIO, encoding="utf-8").read()
    if "## Fase 8 — Relatório final e entrega" in texto:
        print("Ja montado, nada a fazer.")
        return
    marca = "## Fase 7 — Clareza para todos"
    assert texto.count(marca) == 1, "marca da Fase 7 nao encontrada"
    texto = texto.replace(marca, FASES_5_6 + marca)
    texto = texto.rstrip("\n") + "\n" + FASE_8
    with open(RELATORIO, "w", encoding="utf-8", newline="\n") as f:
        f.write(texto)
    print("Relatorio montado.")


if __name__ == "__main__":
    principal()
