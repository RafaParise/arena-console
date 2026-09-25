# Relatório — Auditoria 2 do ARENA

> Segunda rodada completa das Fases 0 a 8 do `docs\PLANO-AUDITORIA.md`,
> pedida pelo Rafael em 25/09/2026, com as mesmas decisões da primeira
> (seguir sozinho de fase em fase; remoções com prova aplicadas em bloco;
> mudanças da Fase 7 aplicadas; juntar ao `main` no fim). O pedido completo
> está no fim do `PLANO-AUDITORIA.md`. O relatório da primeira auditoria,
> `RELATORIO-QUALIDADE.md`, fica como histórico.
>
> **Extra desta rodada:** o testador de máquinas e o próprio ARENA passam
> a identificar o que deixa o computador lento e a recomendar ação.

Ramo: `auditoria`, avançado até o `perfil-alvo` (= `main` + ferramentas de
coleta). Máquina das medições: Ryzen 5 5600G, Radeon Vega integrada, 12 GB,
SSD NVMe, Windows 11 — **não é a máquina alvo**; os números do Celeron vêm
do `COLETAR.bat` rodado na escola.

---

## Fase 0 — Linha de base e inventário

### Testes de referência (regra 7)

`servidor\tests\run.py` (45 testes) + `ferramentas\rodada_final.py` (a
bateria + fuzz das rotas + 34 scripts de `testes\`, com RetroArch de verdade
onde o teste pede), rodados antes de qualquer mudança desta rodada:

**45 de 45 e 36 de 36.** Este é o piso: nenhuma fase pode terminar com menos.
Resultado bruto: `docs\rodada_final_bruta.json`.

### Inventário (lido do código: `testes\inventario.py` → `docs\inventario_bruto.json`)

| Item | Valor |
|---|---|
| Linhas do produto (servidor sem testes, tela, `.bat`, guias) | **23.186** em 33 arquivos |
| Rotas da API | **50** caminhos (51 pares caminho+método; `/api/perfil/foto` tem GET e POST) |
| Rotas abertas à rede (`ROTAS_REDE_EXTERNA`) | **8** |
| Rotas sem ninguém que chame | **1** — `/api/sinc/ranking` (ver Fase 1) |
| Chaves de configuração (`config_padrao`) | 20, todas lidas em algum lugar |
| Linhas de execução/temporizadores | 8 pontos de criação: vigia de rede e descoberta de colegas (permanentes); jogo, teste de partida, reindexação, busca de adaptadores (sob demanda); troca de escuta da rede e abrir a janela (uma vez) |
| O que sai para a internet | `capas_online.py` (raw.githubusercontent.com), `internet_archive.py` (archive.org), links na tela (github.com, npcap.com) |

A primeira auditoria contou "45 rotas". A diferença para 50 não é rota nova: o
script antigo não enxergava rotas testadas com `caminho in (...)` nem
contava separado o que tem GET e POST. O `inventario.py` desta rodada lê os
dois formatos.

### Medições (`testes\linha_base.py` + `ferramentas\medir_arena.py`)

Brutos em `docs\auditoria2\` (`linha_base_fase0.json` e `medir_fase0\`).

| Medida | Auditoria 1, depois | **Auditoria 2, Fase 0** | Observação |
|---|---|---|---|
| Pacote sem jogos | 2.810,0 MB | **2.845,1 MB** | +35 MB é o cache de vídeo do PS1 (`retroarch\system\swanstation\vulkan_pipelines.bin`, 50 MB), que só passou a ser criado depois que o ajuste de imagem do ARENA começou a chegar aos núcleos. Investigado na Fase 2 |
| Abertura até a página responder | 0,63 s | **0,62 s** | igual |
| Dados da tela prontos | — | **0,54 s** | medição nova (medir_arena) |
| Memória que o ARENA toma do Windows | — | **141 MB** | servidor + janela; varia com o que o Windows faz no momento (76–141 MB em 3 medições hoje) |
| CPU parado | 0,02% | **0,02%** | igual |
| RAM do servidor parado | 35,8 MB | **36,0 MB** | igual |
| Threads do servidor | 14 | **14** | igual |
| Portas em escuta (rede desligada) | só 127.0.0.1:8777 | **só 127.0.0.1:8777** | igual |
| Servidor em uso (4 rotas da tela sem parar) | — | **7,5% da máquina, 4.044 pedidos em 20 s, resposta média 4,9 ms, pior 5% 14,3 ms** | medição nova |
| Releitura da lista de jogos | — | **35 jogos em 0,14 s** | |
| Gravações em disco parado | 0/h | **0/min** | igual |
| SNES com as opções reais | — | **60,0 FPS, variação 3,2%, CPU 0,6%, RAM 148 MB, abre em 2,0 s, vídeo Vulkan** | medição nova |

**Não é a máquina alvo.** Estes números servem para comparar antes/depois
nesta mesma máquina; o alvo é o Celeron (COLETAR.bat na escola).
