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

---

## Fase 1 — Varredura e limpeza

Ferramentas: `testes\varredura_fase1.py` (a da primeira auditoria, de novo),
e duas novas nesta rodada: `testes\funcoes_js_mortas.py` (funções do
`app.js` nunca chamadas) e `testes\ids_da_tela.py` (todo `#id` que o JS
procura existe no HTML? todo id do HTML é usado?). Mais o `inventario.py`
da Fase 0 (rota sem chamador).

### Removido (lista com prova, aprovada em bloco como na primeira auditoria)

| # | O quê | Prova de que não é usado | O que quebra se sair |
|---|---|---|---|
| R1 | Apelido de rota `/api/sinc/ranking` | Nenhum chamador em nenhuma versão: nem no ARENA atual, nem nas duas versões originais (`ARENA - Versão antiga…` e `ARENA-remake--master` só **atendem** a rota, nunca chamam). E nem estava na lista de rotas abertas à rede, onde faria sentido | Nada. `/api/ranking` continua igual |
| R2 | Função `registros_pendentes()` em `arena.py` | Definida e nunca chamada (nem nos testes). Sobra da época do `db.py` | Nada |
| R3 | CSS `.jogo--desaparecendo` | O servidor só produz os estados `pronta`, `falta_externo`, `sem_core`, `falta_sistema`, `sem_pasta`. A primeira auditoria deixou passar porque o prefixo `jogo--${estado}` fazia parecer vivo | Nada |
| R4 | Regra CSS duplicada `.jogo--sem_pasta .jogo-faixa` | Idêntica nas linhas 524 e 1550 do `estilo.css` | Nada (a da linha 524 fica) |

### Checado, sem achado

- **Funções mortas no JS:** 94 funções no `app.js`, nenhuma sem uso.
- **Ids da tela:** 219 ids no HTML, 195 procurados pelo JS, **nenhum
  procurado e ausente**. 5 ids sem uso aparente (`lblEnviarCapa`,
  `perfilChaves`, `rankingPontos`, `rankingTempo`, `wizardInstrucao`):
  servem de rótulo/âncora e não pesam nada — ficam.
- **Funções Python "usadas uma vez só":** as 13 candidatas da varredura são
  todas chamadas indiretamente (alvo de thread, método do servidor HTTP
  como `do_GET`, lista de regras do identificador) — vivas. Só
  `registros_pendentes` era morta de fato (R2).
- **CSS montado por partes:** os 27 candidatos da primeira auditoria foram
  conferidos de novo, prefixo por prefixo (`sinal--${…}`, `jogo--${…}`,
  `capa-${…}`, `desempenho--${…}`, `custo--${…}`, `ranking-pos--${…}`,
  `midia--${…}`) — vivos, menos o `jogo--desaparecendo` (R3).
- **Estado `falta_externo` sem cor própria:** o `.sinal` já é cinza por
  padrão, que é a cor certa para "falta o emulador". Não é defeito.
- **Caminhos absolutos:** só reservas do Windows (`SystemRoot`, `WINDIR`)
  e a lista de navegadores. Nenhum caminho da máquina.
- **Funções já removidas:** "duckstation" só em comentário e no filtro que
  limpa essa sobra antiga; "transmissão" só no comentário que explica por
  que está desligada. Scroll Lock: nenhuma ocorrência.
- **Texto em inglês na tela:** nenhum.
- **Chaves de configuração:** 20, todas lidas.

### Testes

Bateria **63 OK** (45 + 18 novos das barreiras, ver Extra), fuzz 0 falhas,
acesso de rede, sincronização e ids da tela: OK.

---

## Fase 2 — Leveza e desempenho

### Achado 1 — 37 ajustes de imagem que não faziam nada (corrigido)

Ferramenta nova: `testes\teste_chaves_graficos.py`, que confere **cada**
chave de opção do `servidor\graficos.json` contra o texto de dentro do
`.dll` do núcleo (onde as chaves ficam escritas). Das 98 chaves, **28 não
existiam** no núcleo — o ARENA as gravava a cada jogo, sem efeito nenhum:

| Núcleo | Chaves inexistentes | O que foi feito |
|---|---|---|
| SwanStation (PS1) | 24: toda opção vinha em três formas (`swanstation_GPU_X`, `duckstation_GPU.X`, `swanstation_GPU.X`); só a primeira existe | As duas formas falsas saíram (37 ocorrências no arquivo) |
| Genesis Plus GX (Mega Drive) | `genesis_plus_gx_blargg_ntsc_md` | Renomeada para `genesis_plus_gx_blargg_ntsc_filter` (nome atual, conferido no `.dll`, valores `composite`/`disabled` válidos). **O filtro NTSC passa a valer** nas máquinas nota ≥ 3, como o arquivo sempre pretendeu |
| PPSSPP (PSP) | `ppsspp_disable_slow_framebuffer_effects` | Renomeada para `ppsspp_skip_gpu_readbacks` (mesmo sentido, valor `disabled`) |
| PPSSPP (PSP) | `ppsspp_rendering_mode` | Virou `ppsspp_skip_buffer_effects = "disabled"`. O modo modesto pedia "pular efeitos de buffer", que o próprio núcleo avisa: *"em alguns jogos nada é desenhado"*. Nunca chegou a valer; ligar agora, sem teste, arriscaria tela preta. **Decidir com os números do Celeron** |
| PCSX2 do RetroArch | `pcsx2_frameskip` | Saiu (não existe mais; o padrão já é não pular quadros) |

Agora: **73 chaves, todas existem.** O teste entra na rodada completa e pega
a próxima renomeação quando um núcleo for atualizado. Ferramentas:
`ferramentas\opcoes_do_nucleo.py` (lista as opções que um núcleo conhece) e
`ferramentas\corrigir_chaves_graficos.py` (a correção, mantendo ordem e
recuo do arquivo). Matriz de jogos passou a incluir o **Mega Drive**
(7 consoles): abre, mostra imagem, salva e carrega estado, com o filtro novo.

### Achado 2 — 15 a 50 MB regravados a cada jogo de PS1 (corrigido no modo econômico)

`testes\medir_cache_ps1.py` abriu o mesmo jogo de PS1 várias vezes com as
opções reais do ARENA:

| Situação | Abrir o jogo | Cache `vulkan_pipelines.bin` |
|---|---|---|
| Com o cache (50 MB) | 6,4–7,1 s | **Regravado inteiro a cada partida, com o conteúdo IGUAL** |
| Sem o cache | 6,2 s | recriado (15,6 MB só deste jogo) |
| `swanstation_GPU_ShaderPrecompile = false` | igual | regravado do mesmo jeito (não é a opção certa) |
| Arquivo somente leitura | 6,4–7,1 s | **intocado**, e o jogo abre igual |

Ou seja: o cache não acelera a abertura, e o núcleo regrava dezenas de MB
toda vez que o jogo fecha. Num pen drive lento (5–10 MB/s) são 5 a 10 s com
o jogo "travado" fechando — e desgaste. **Correção** (`graficos.preparar_cache_ps1`
e `fixar_cache_ps1`, ligadas em `executar_jogo`), **só no modo econômico**
(o que o ARENA já liga em máquina fraca ou em pen drive/cartão): se depois
da partida o cache não cresceu, ele vira somente leitura; se o pen drive
for para outro computador (outra placa de vídeo), o cache antigo é apagado
para o núcleo montar um novo. Jogar Junto não entra (usa outro núcleo).
Testes: `servidor\tests\test_cache_ps1.py` (4). **Limite honesto:** o modo
econômico não liga nesta máquina de desenvolvimento, então o caminho
completo dentro da partida fica para o roteiro de sala (Roteiro 9).

### Achado 3 — rodízio de registros só na abertura (corrigido)

Com o limite de 10, havia **20** registros do RetroArch em `dados\`: o
rodízio só rodava ao abrir o ARENA, e o ARENA fica aberto a aula inteira.
Pequenos (15 KB em média), mas o limite não era real. Agora roda também ao
fim de cada partida.

### Medido e sem achado

| Medida | Valor |
|---|---|
| CPU com o ARENA parado | 0,02% (Fase 0) |
| Gravações em disco parado | 0 por minuto |
| Tela (`launcher\`) | 220 KB no total (app.js 118 KB, index.html 41 KB, estilo.css 44 KB, fundos 17 KB); sem imagens |
| Fundo animado × modo modesto (`testes\medir_tela.ps1`) | 0,8% × 0,5% de um núcleo nesta rodada (2,0% × 0,5% na medição anterior): a animação do navegador varia com a janela em foco ou não. RAM da tela ~420 MB, igual. O número que decide é o do Celeron |
| Estresse do catálogo (5.000 jogos falsos) | passou na rodada de referência (`teste_estresse_catalogo.py`) |
| CSS e JS não usados | ver Fase 1 |

Bateria **67 OK**; `teste_chaves_graficos`, `teste_opcoes_nucleo_ponta_a_ponta`
e a matriz (7 consoles) OK; `retroarch.cfg` sem caminho temporário.
