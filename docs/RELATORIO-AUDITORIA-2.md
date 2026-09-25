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

---

## Extra — Barreiras de lentidão (o testador e o ARENA)

Pedido do Rafael nesta rodada: *"garanta que ele possa identificar todas as
barreiras desses computadores que deixam eles lentos como bloatwares,
serviços e recursos desnecessários, telemetria e etc... Se tiver algum
problema o ARENA precisa saber identificar para recomendar ação"*.

**Um módulo só, `servidor\barreiras.py`, usado em três lugares** — tela do
ARENA, `VERIFICAR.bat` (item 11) e `COLETAR.bat` — para os três nunca
discordarem. Duas partes separadas de propósito:

- `coletar_fatos()` **lê** o Windows sem administrador: registro (só
  leitura), processos (duas fotos com 2 s entre elas, para o uso de CPU),
  serviços, Central de Segurança, programas instalados. Uma chamada ao
  PowerShell (~5 s aqui). O que falhar vira "não deu para ler" e segue.
- `avaliar(fatos)` **decide**, sem tocar em nada: função pura, testada com
  fatos inventados (22 testes na bateria).

**O que ele identifica** (cada item diz o que achou, por que pesa, o que
fazer e **quem faz** — o aluno ou o professor/TI):

| Grupo | Barreiras |
|---|---|
| Memória e processos | memória quase cheia / pouca livre; programas pesados abertos; **programas fecháveis** (OneDrive, Teams, Discord, Spotify, Steam, Epic, Zoom, WhatsApp, Widgets, Game Bar... — com botão **Fechar**); navegador com muitas abas; processador ocupado sem ninguém jogando |
| Windows | atualização rodando agora; reinício pendente; ligado há dias; indexação do Windows Search trabalhando |
| Segurança | **dois antivírus ligados**; antivírus examinando agora |
| Instalados | **bloatware** de fábrica e "teste grátis" (McAfee, Norton, WildTangent, Candy Crush, assistentes de fabricante...) |
| Inicialização | muitos programas abrindo com o Windows (conta só os que não foram desligados no Gerenciador de Tarefas) |
| Serviços | SysMain e Windows Search num HD mecânico; **serviços que a escola não usa** (Fax, Demonstração de loja, Mapas, Xbox, compartilhamento do Media Player, push de telemetria); Otimização de Entrega num HD |
| Telemetria | DiagTrack ligado sem limite de política |
| Recursos visuais e de jogo | **gravação em segundo plano do Xbox Game Bar**; Modo de Jogo desligado; transparência e animações; apps em segundo plano |
| Energia | na bateria; economia de bateria; plano "Economia"; **processador limitado pelo plano** (estado máximo < 100%) |
| Disco e memória virtual | disco do Windows quase cheio; temporários enormes; **memória virtual desligada** |
| Vídeo | sem driver de verdade (Adaptador de Vídeo Básico) |

**No ARENA:**
- Ajustes → Máquina → **"O que está deixando este computador lento"** com
  o botão **Verificar agora** (só sob pedido: com o ARENA parado continua
  0% de processador). Conferido no Chrome.
- **Na hora de jogar**, uma checagem de ~10 ms (memória quase cheia, na
  bateria, economia de bateria) avisa na barra do topo até o jogo fechar.
- `GET /api/barreiras` e `POST /api/barreiras/fechar` — **só para este
  computador** (403 vindo da rede); fechar **só** programas da lista
  segura, só com o clique; nunca navegador, Word ou algo com trabalho do
  aluno. A resposta não leva a lista de processos nem dado pessoal.

**No testador (`coletar_maquina.py`)**, além das barreiras: **quantos pentes
de memória e de que velocidade** (um pente só = canal simples, e o vídeo
integrado do Celeron perde muito) e **o que o próprio Windows diz do disco**
(HDD/SSD/NVMe/USB), como segunda opinião ao lado do teste de velocidade.

**Privacidade:** da inicialização guarda só o nome do programa e se é "do
usuário" ou "do computador" (a lista do Windows traz o nome do usuário e da
máquina — descartados). Dos instalados, só os que batem com a lista de
bloatware. Dos processos, só os 15 mais pesados. Teste confirma: nenhum
nome de usuário ou de máquina na resposta.

---

## Fase 3 — Servidor e API

| Item | Resultado |
|---|---|
| Fuzz das rotas (agora com `/api/barreiras` e `/api/barreiras/fechar`) | **0 falhas**. O fuzz dava 5 s a toda rota; o diagnóstico leva ~5 s de propósito — ganhou prazo de 60 s só para ele (`ROTAS_LENTAS`). A tela espera sem prazo |
| Rotas novas vindas da rede | 403 (teste `teste_barreiras_api.py`) |
| Fechar programa fora da lista | recusado nos 5 casos testados (`notepad`, `explorer`, `../../x`, vazio, nulo) |
| Rotas abertas à rede | continuam as mesmas **8** |
| CSRF e DNS rebinding | valem para as rotas novas automaticamente (checagem geral do servidor) |

### Achado — PowerShell bloqueado ou em "modo restrito" (corrigido)

Muita escola bloqueia o PowerShell ou liga o **modo de linguagem restrita**
para aluno. Nele, `[pscustomobject]`, `[math]`, `[Environment]`,
`[Convert]` e métodos de objetos não-básicos são recusados. O diagnóstico
usava tudo isso e **perdia listas inteiras em silêncio** — e o primeiro teste
que escrevi só contava os campos, não o conteúdo, e deixou passar.

**Corrigido:** os scripts do diagnóstico e do coletor foram reescritos com
`Select-Object` calculado (permitido) e as contas feitas no Python.
`teste_barreiras_modo_restrito.py` agora compara **conteúdo**: paridade
total (63 processos, 5 itens de inicialização, 16 serviços, 1 antivírus,
262 programas, 13 campos iguais). Com o PowerShell **bloqueado de vez**, o
diagnóstico segue com memória, energia e disco e diz o que não conseguiu
ler (teste na bateria). O coletor passou a usar a resposta mesmo com código
de erro (no modo restrito uma linha recusada deixa o código diferente de
zero) e ganhou reserva sem PowerShell para os endereços de rede.

**Limite honesto:** ligar o modo restrito pelo próprio script (a única
simulação possível aqui) é **mais duro** que a política de verdade: bloqueia
também os módulos da Microsoft de rede, disco e Firewall, que numa escola
com modo restrito real continuam liberados por serem assinados. Esses três
itens do coletor ficam "não foi possível medir" na simulação. Roteiro 10
confere numa conta de aluno de verdade.

### Achado — o VERIFICAR não conferia 7 arquivos sem os quais o ARENA nem abre (corrigido)

A lista de "arquivos do programa" tinha 5 dos 11 módulos que o `arena.py`
importa na abertura: faltavam `controles`, `acervo`, `internet_archive`,
`capas_online`, `identificador`, o novo `barreiras` e o
`perfis_controle.json`. Faltando qualquer um, o ARENA não abria — e o
verificador dizia *"os 13 arquivos do programa estão presentes"*. Agora
confere **20**. `teste_verificador_arquivos.py` prova as duas pontas numa
cópia sem o `controles.py`: o ARENA não abre, e o verificador acusa. (No
caminho, o teste pegou uma armadilha: o Python embutido já traz a pasta
`servidor` de verdade no caminho de busca — linha `..` do `python313._pth` —
e achava o arquivo original. O teste tira essa pasta antes de provar.)

---

## Fase 4 — Jogar Junto

Rodados de novo com RetroArch de verdade, depois das mudanças desta rodada
na partida (cache do PS1 fora do Jogar Junto; rodízio de registros ao fim
do jogo): 5 jogadores (os 4 convidados entram), isolamento, cenários de sala,
PARTIDA.bat com colega, rede sem reabrir, descoberta de 30 máquinas,
sincronização sem relógio, migração e lotes, mala: **9 de 9**.

### Pergunta nova: notas diferentes dessincronizam a partida?

Agora que o ajuste de imagem do ARENA chega aos núcleos, o Ryzen e o Celeron
recebem opções diferentes. O Jogar Junto exige que as duas máquinas simulem
o jogo **igualzinho**. Conferido núcleo por núcleo: nos que fazem Jogar
Junto de verdade (SNES, Mega Drive, NES, e o PS1 pelo PCSX ReARMed), o
`graficos.json` só manda opções **de imagem** (filtros NTSC, bordas, paleta,
transparência, recorte). O PCSX ReARMed não recebe nenhuma. **Nenhuma opção
de simulação** — sem risco conhecido. A prova definitiva (host no Ryzen,
convidado no Celeron) fica no Roteiro 11.

---

## Fase 5 — Matriz de jogos

`testes\teste_matriz_jogos.py` com RetroArch de verdade, agora com **7
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

`ferramentas\teste_aceite_pasta_movida.py` copiava o ARENA para uma pasta
irmã para provar que ele se conserta sozinho — e **nunca apagava a cópia**,
que levava junto uma cópia do `dados\` (recordes, apelido). Agora apaga no
fim, passe ou falhe, tirando antes o somente leitura do cache do PS1 (Fase 2),
que travava o `rmtree`. Entrou na rodada final.

### Achado — guia 6 com a lista errada do que a atualização traz (corrigido)

A lista de "o que copiar ao atualizar" não tinha `PARTIDA.bat`, `COLETAR.bat`
nem `ferramentas\`, e dizia que `emuladores\` era só PCSX2/Dolphin (tem RPCS3
e Xenia). `perfil\` (saída do coletor) entrou como pasta do usuário, que não
se sobrescreve.

---

## Fase 7 — Clareza para todos

### Achado — cerca de 110 mensagens da tela sem acento (corrigido)

A primeira auditoria reescreveu as mensagens confusas, mas **não olhou a
grafia**. Ferramenta nova `testes\textos_sem_acento.py` (entra na rodada
final; falha se achar alguma) procura, só no que chega à tela, palavras como
"nao", "codigo", "endereco", "invalido", "So", "Ja". Achou 55 frases; uma
segunda varredura mais larga (erros que viram mensagem via `ValueError`,
dicas de controle, veredito do "testar partida") achou mais ~55.

Exemplos do que o aluno lia: *"So este computador"*, *"Adaptador virtual
(nao serve para o colega)"*, *"Jogo nao encontrado"*, *"Codigo invalido"*,
*"OBRIGATORIO. Nao existe nucleo de PlayStation 3..."*, *"Voces tem o mesmo
jogo, mas ARQUIVOS DIFERENTES - regiao ou versao"*.

Corrigido com `ferramentas\acentuar_textos.py`, que troca **só dentro das
frases de tela** e resolve à mão os casos ambíguos ("esta" × "está",
"e" × "é"). **De fora, de propósito:** chaves internas que a tela compara
(`"ele nao tem"`, a classe de disco `"nao medido"`), nomes de campo JSON e a
janela preta (`VERIFICAR.bat`, `PARTIDA.bat`, avisos do servidor), que é
ASCII para não virar símbolo estranho no console do Windows. Conferido que
nenhuma chave, comparação ou nome de campo ganhou acento. A tela
(`index.html`, `app.js`) já estava certa.

Dois testes comparavam o texto antigo e foram ajustados com o motivo
comentado (bateria `run.py`: validação de cheat; `teste_partida_testar_timing`).

### Checado, sem achado

- Mensagens de erro da API em JSON e em português: fuzz 0 falhas.
- Textos novos desta rodada (barreiras) já nasceram com acento, com "quem
  faz" (aluno × professor/TI) e ação concreta em cada item.
- Contraste e teclado: sem mudança desde a primeira auditoria (Roteiro 6).

---

## Roteiros de sala novos (continuam a numeração do `RELATORIO-QUALIDADE.md`)

### Roteiro 9 — Cache do PS1 no pen drive (Fase 2)

Num Positivo (ou qualquer máquina com o ARENA **no pen drive**, onde o modo
econômico liga sozinho):

1. Abra um jogo de PS1, jogue 1 minuto, feche. Abra de novo e feche.
2. Em `retroarch\system\swanstation\`, clique com o botão direito em
   `vulkan_pipelines.bin` → Propriedades. **Esperado:** "Somente leitura"
   marcado depois da segunda partida.
3. Anote quanto tempo o jogo leva para **fechar** (do F10 até a tela do
   ARENA voltar), antes e depois — o ganho esperado é de 5 a 10 s num pen
   drive lento.
4. Leve o mesmo pen drive a outra máquina (outra placa de vídeo) e abra o
   mesmo jogo. **Esperado:** abre normal (o cache velho é apagado sozinho).

### Roteiro 10 — Conta de aluno de verdade (Fase 3 e Extra)

Numa máquina da escola, **entrando com a conta de aluno**:

1. Rode o `COLETAR.bat`. Abra `perfil\maquina.txt`. Anote quais itens
   saíram "não foi possível medir" (o esperado é quase nenhum; se a escola
   liga o modo restrito do PowerShell, rede/disco/Firewall devem continuar
   medidos, porque os módulos da Microsoft são assinados).
2. No ARENA: Ajustes → Máquina → **Verificar agora**. Anote as barreiras
   que aparecem e se cada ação sugerida faz sentido para o aluno.
3. Se aparecer "Programas que dá para fechar", clique **Fechar** num deles
   e confira no Gerenciador de Tarefas que ele fechou (e nada mais).
4. Rode o `VERIFICAR.bat` e confira a seção 11.

### Roteiro 11 — Jogar Junto entre máquinas de notas diferentes (Fase 4)

Host no computador **forte** (Ryzen/i5), convidado no **Celeron/Positivo**:

1. SNES (Super Bomberman ou Street Fighter II) por 5 minutos.
2. Mega Drive (Sonic 3 ou Streets of Rage 2) por 5 minutos.
3. PS1 (Crash Team Racing) por 5 minutos.

Em cada um, anote se aparece **"dessincronizado"** / "desync" ou se os dois
veem coisas diferentes (um personagem num lugar numa tela e em outro na
outra). O ARENA manda opções de imagem diferentes para cada máquina; a
análise do código diz que nenhuma afeta a simulação — só isto confirma.

---

## Fase 8 — Relatório final e entrega

### Rodada final de todos os testes

`ferramentas\rodada_final.py` (bateria + fuzz + todos os `testes\teste_*.py`,
com RetroArch de verdade onde o teste pede; entraram nesta rodada o
verificador de acentos e o teste de pasta movida): **42 de 42**. Bateria
`servidor\tests\run.py`: **71 de 71** (eram 45 na Fase 0: +22 das barreiras,
+4 do cache do PS1). Fuzz: 258 checagens, 0 falhas. Bruto:
`docs\rodada_final_bruta.json`.

### Antes × depois (mesma máquina, Ryzen 5 5600G)

Brutos: `docs\auditoria2\linha_base_fase0.json` × `linha_base_fase8.json`,
`medir_fase0\` × `medir_fase8\`.

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
