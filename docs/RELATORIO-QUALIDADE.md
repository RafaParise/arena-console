# Relatório de Qualidade — Auditoria do ARENA

> Ramo `auditoria`. Ver `docs\PLANO-AUDITORIA.md` para o pedido completo e as
> 10 regras. Este arquivo acumula "Antes" (Fase 0) e, ao final, "Depois"
> (Fase 8), com uma tabela comparando os dois.

Medido em: 23/09/2026, na máquina de desenvolvimento do Rafael (Ryzen 5
5600G, Radeon Vega integrada, 12 núcleos lógicos, Windows 11 Enterprise
10.0.26200). **Isto não é a máquina alvo.** A máquina alvo (Positivo
dual-core, 4 GB, sem SSD) só pode ser medida na escola — ver limitações no
fim de cada bloco.

Script usado para as medições automáticas: `testes\linha_base.py` (pode ser
rodado de novo a qualquer momento para comparar; grava o resultado bruto em
`docs\linha_base_bruta.json`).

---

## Antes (Fase 0)

### Teste de referência (regra 7)

`servidor\tests\run.py`, rodado no ramo `auditoria` antes de qualquer
mudança:

```
Ran 44 tests in 0.292s
OK
```

44 testes, 0 falhas. Este é o piso que não pode piorar em nenhuma fase
seguinte.

### Medições

| Medida | Valor | Como foi medido |
|---|---|---|
| Tamanho do pacote, sem jogos | **2.809,8 MB** (≈ 2,8 GB) | Soma de todos os arquivos da pasta, exceto `jogos\`, `.git\` e `backup\` |
| — dos quais `retroarch\` | 2.121,1 MB | núcleos libretro + RetroArch em si (de terceiros) |
| — dos quais `emuladores\` | 666,7 MB | PCSX2 + Dolphin + RPCS3 + Xenia (de terceiros) |
| — dos quais `servidor\` | 21,2 MB | inclui o Python embutido (≈ 21 MB) |
| — dos quais `launcher\`, `dados\`, raiz | ≈ 0,6 MB | código e configuração próprios do ARENA |
| Linhas de código **do ARENA** (sem `emuladores\`/`retroarch\`, que são de terceiros) | **21.857 linhas** | `.py` 12.680 (37 arquivos) · `.js` 3.764 (3 arquivos) · `.html` 886 (1 arquivo) · `.css` 1.688 (1 arquivo) · `.json` 2.839 (10 arquivos de configuração) |
| Tempo de abertura até responder a página principal | **0,63 s** | tempo entre abrir `arena.py` e o primeiro HTTP 200 em `/` |
| Uso de processador parado | **0,04%** | processo já respondendo, sem nenhuma aba usando; amostra de 15,9 s, 12 núcleos lógicos |
| RAM do servidor parado | **35,5 MB** (1 processo, 15 threads) | `python.exe` sozinho — **não inclui a tela**, ver limitação abaixo |
| Threads do servidor | **15** | inclui os 2 daemons permanentes (`rodar_vigia`, `anunciar_e_escutar`) + pool de conexões HTTP + principal |
| Portas em escuta | **1 — 127.0.0.1:8777** | `permitir_rede` estava desligado (padrão); nenhuma porta exposta à rede |
| Gravações em disco por hora, parado | **não medido nesta rodada** | ver pendência abaixo |

**Limitação encontrada e registrada (não é erro do teste, é um limite real
de medição):** o ARENA abre a "tela" chamando o navegador já instalado em
modo app (`abrir_janela()`, ver `arena.py:4282`), para economizar 15–25 MB
que uma janela gráfica própria custaria. Nesta máquina, o Edge **já estava
rodando em segundo plano** (comportamento padrão do Windows 11 — o Edge
continua vivo depois que todas as janelas fecham). Quando isso acontece, o
processo que o ARENA abre não nasce como filho do `python.exe`: ele é
absorvido pelo processo de navegador que já existia, e a nova janela vira só
mais uma aba desse processo. Resultado prático: **não dá para isolar
automaticamente quanto de RAM só a tela do ARENA usa**, porque ela se mistura
com todo o resto que o navegador já tinha aberto. Em um notebook da escola
recém-ligado (sem Edge/Chrome ainda rodando), o processo nasceria isolado e
essa medição funcionaria. Isso vira item do roteiro manual (Fase 4/6): medir
a RAM da janela do ARENA pelo Gerenciador de Tarefas, coluna "Memória",
olhando o processo do navegador com o título da janela do ARENA.

**Pendência desta rodada:** gravações em disco por hora (parado) e
temporizadores de repetição (o "vigia" roda a cada quanto tempo, a
descoberta de colegas a cada quanto tempo) — dá para responder por código
(ver "Serviços em segundo plano" abaixo) mas a contagem de gravações reais
em disco pedida pelo plano precisa de uma janela de medição mais longa (a
amostra de 15 s não teve tempo de capturar um ciclo completo do vigia, que
roda a cada 60 s no modo econômico). Fica para a Fase 2, que já pede esse
número de novo com o detalhamento por tipo de gravação.

### Inventário de arquivos (por pasta de topo)

| Pasta | Arquivos | Tamanho | O que é |
|---|---|---|---|
| `retroarch\` | 15.070 | 2.121,1 MB | RetroArch + núcleos libretro (terceiros) |
| `emuladores\` | 3.212 | 666,7 MB | PCSX2, Dolphin, RPCS3, Xenia (terceiros) |
| `jogos\` | 36 (na raiz de cada pasta) | 43.594,3 MB | ROMs — **fora da auditoria de tamanho**, cada escola/aluno tem o seu |
| `servidor\` | 68 | 21,2 MB | código Python do ARENA + Python embutido |
| `dados\` | 45 | 0,3 MB | banco, configuração, saves de config — **dado do usuário, não mexer sem autorização** |
| `backup\` | 49 | 3,5 MB | cópias automáticas — dado do usuário |
| `launcher\` | 5 | 0,2 MB | HTML/JS/CSS da tela |
| `ferramentas\` | 19 | 0,1 MB | scripts de teste já existentes (sessões anteriores) |
| `docs\` | 2 (agora 3, com este arquivo) | ~0 MB | este relatório + o plano da auditoria |
| `testes\` | 1 (agora 2) | ~0 MB | scripts novos desta auditoria (regra 5) |
| raiz | 12 arquivos | ~0,1 MB | `.bat`, `LEIA-ME.md`, guias 1–6, `.gitignore` |

**Achado real, registrado para a Fase 1/2:** `dados\` tem **38 arquivos de
log do RetroArch** (`retroarch__2026_09_22__*.log`), todos de sessões de
teste de ontem (22/09/2026), sem nenhum rodízio ou limite — cada partida
aberta cria um `.log` novo com carimbo de data/hora e ele nunca é apagado.
É exatamente o "menos gravações em disco, com rodízio" que a Fase 2 pede.
Não apaguei nada agora (regra 2 e regra 3 — nada some sem lista aprovada);
fica anotado para a Fase 1 propor.

### Inventário de rotas da API

`servidor\arena.py` despacha por comparação direta de string (`if caminho ==
"/api/..."` e dois casos com `caminho in (...)`), sem tabela nem regex.
**45 rotas únicas** (a documentação em `CLAUDE.md` citava "44 rotas" — bem
próximo; a diferença é que `/api/perfil/foto` tem GET e POST separados e
`/api/sinc/ranking` é um apelido de `/api/ranking` que eu não tinha contado
antes). Lista completa, com quem parece chamar cada uma (via `fetch(...)` ou
atributo `src=` em `launcher\app.js` — cross-referência completa fica para a
Fase 1, que decide o que é código morto):

- **Chamadas confirmadas pela tela** (apareceram em `app.js`): `/api/estado`,
  `/api/catalogo`, `/api/jogo`, `/api/jogo/mover`, `/api/jogar`,
  `/api/placar`, `/api/config`, `/api/colegas`, `/api/amigo/codigo`,
  `/api/perfil/foto` (GET e POST), `/api/exportar`, `/api/importar`,
  `/api/perfis-controle`, `/api/perfil-controle`, `/api/mapeamento`,
  `/api/botoes`, `/api/mapeamento/definir`, `/api/amigo/adicionar`,
  `/api/amigo/remover`, `/api/amigo/testar`, `/api/estado/apagar`,
  `/api/cheat/alterar`, `/api/cheat/adicionar`, `/api/sincronizar`,
  `/api/conquistas`, `/api/ranking`, `/api/acervo`, `/api/acervo/instalar`,
  `/api/acervo/remover`, `/api/biblioteca-online`,
  `/api/biblioteca-online/instalar`, `/api/pastas/criar`, `/api/indexar`,
  `/api/capa/atualizar`, `/api/capa/enviar`, `/api/jogo/console`,
  `/api/acervo/salvar`, `/api/partida/testar`, `/api/mapeamento/padrao`,
  `/api/mapeamento/limpar`, `/api/bios/abrir`, `/api/reparar-runtime`,
  `/api/backup`, `/api/perfil/novo`, `/api/mala`.
- **Prováveis chamadas entre ARENAs (servidor-a-servidor, não pela tela)**:
  `/api/sinc/receber`, `/api/sinc/ola`, `/api/sinc/ranking` — fazem parte da
  sincronização de placar entre colegas, chamadas pelo `arena.py` de um
  colega para o outro, não pelo navegador.
- **Resolvido na Fase 1** (não apareciam em `fetch(...)` porque não são
  chamadas desse jeito — confirmado, não são rotas mortas):
  `/api/capa` é montada **pelo servidor**, não pela tela — `arena.py:1401`
  gera `jogo["capa_urls"]` com a URL pronta (`/api/capa?arquivo=...`), que
  vira `<img src>` direto; `/api/jogo/impressao` é chamada de servidor para
  servidor, por `arena.py:3415` e por `servidor\partida.py:187/189` (o
  `PARTIDA.bat`), para comparar se os dois lados têm o mesmo arquivo de jogo
  antes de conectar o Jogar Junto — não é rota de tela, é rota de
  diagnóstico entre ARENAs.

### Inventário de chaves de configuração (`config.json`, via `config_padrao()` em `arena.py`)

`perfil_grafico`, `avancado` (dicionário à parte, ver `AVANCADO_PADRAO`),
`apelido`, `permitir_rede`, `servidores`, `bios`, `dispositivo_id`,
`codigo_proprio`, `modo_desempenho`, `ultra_desempenho`, `modo_modesto`,
`preset_grafico_externo`, `rpcn_ativo`, `tema`, `favoritos`, `recentes`,
`travar_teclas`, `tipo_controle`, `perfil_controle`, `nome_dispositivo` — 20
chaves de topo. Todas lidas de volta em `carregar_config()`/`ler_config_do_disco()`
na mesma `arena.py`. Chave antiga que sobrou de versão anterior é filtrada ao
carregar (regra já documentada em `CLAUDE.md` seção 6) — não vi indício de
chave morta na leitura rápida; confirmação fina de uso de cada uma fica para
a Fase 1.

### Inventário de serviços em segundo plano

| Serviço | Onde nasce | O que faz | Frequência |
|---|---|---|---|
| `rodar_vigia` | `threading.Thread(daemon=True)`, `arena.py:4421` | backup automático, checagem de saúde | a cada 60 s (modo econômico) / 20 s (normal) — conforme `CLAUDE.md` seção "Padrões de código" |
| `anunciar_e_escutar` | `threading.Thread(daemon=True)`, `arena.py:4422` | descoberta de colegas por UDP broadcast, porta 55436 | a cada 5 s |
| abrir a janela do navegador | `threading.Timer(1.0, ...)`, `arena.py:4423` | não é permanente — dispara uma vez, 1 s depois de abrir |
| Servidor HTTP principal | thread principal do processo | responde a `/api/*` e serve `launcher\` | sob demanda |

Threads efêmeras (nascem e morrem por pedido, não contam como "serviço
rodando"): teste de endereço de amigo (`arena.py:2634`), download em
segundo plano de capa/jogo (`arena.py:3517`, `4048`).

**Correção desta entrada, feita na Fase 1**: eu tinha escrito aqui, por
suposição, que `transferencia.py:59` era usada pela mala do pen drive.
Não é — conferido na Fase 1: `transferencia.py` inteiro nunca é importado
por `arena.py`, é um módulo órfão. A mala do pen drive de verdade é
`ARENA-troca.json`, por arquivo, sem servidor HTTP nenhum (ver CLAUDE.md).
Ver a lista de remoções da Fase 1 abaixo.

### Inventário do que depende de internet

- `servidor\internet_archive.py` — busca e download no acervo online
  (Internet Archive).
- `servidor\capas_online.py` — busca automática de capa no
  libretro-thumbnails.
- `servidor\arena.py` — netplay pela internet (repasse/relay oficial do
  RetroArch, "Estamos em casas diferentes") e RPCN do RPCS3 (desligado por
  padrão).

Tudo com o padrão já documentado em `CLAUDE.md`: degrada, não trava, quando
não há internet. Testar isso de propósito (DNS falho, timeout, Wi-Fi da
escola devolvendo HTML de login) é o que a Fase 3 pede — não testado ainda
nesta fase, só inventariado.

---

## Fase 1 — Varredura e limpeza

Script usado: `testes\varredura_fase1.py` (resultado bruto em
`docs\varredura_fase1_bruta.json`). Ele só aponta candidatos — cada um foi
conferido à mão, lendo o código de verdade, antes de entrar nesta lista
(regra 3: nada entra por suposição de regex).

**Aprovada em bloco pelo Rafael ("Todas por gentileza") e aplicada em
23/09/2026.** Os 6 itens abaixo foram todos aplicados, testados e
commitados. Detalhe de cada aplicação logo após a tabela correspondente.

### Remoções propostas (código morto, com prova)

| # | O quê | Prova | Risco de remover |
|---|---|---|---|
| 1 | `servidor\transferencia.py` inteiro (116 linhas) — um servidor HTTP de transferência P2P de jogos por Wi-Fi, tipo snapdrop.net | `grep` por `transferencia`, `ServidorTransferencia` e `TransferHandler` no projeto inteiro só acha o próprio arquivo. `arena.py` nunca importa `transferencia`. Nenhum guia (1–6, LEIA-ME) menciona a função. Não está na lista "Funcionalidades existentes" do CLAUDE.md. | Nenhum — nada usa |
| 2 | `graficos.opcoes_de_controle()` (`graficos.py:619-636`) — função que liga o analógico via `input_libretro_device_pN` | Nunca chamada (`grep` só acha a definição). A mesma responsabilidade já é feita de verdade por `controles.opcoes_do_console()`, chamada em `arena.py:1614` — que é quem realmente grava `input_libretro_device_pN` (`controles.py:198-205`). É duplicata morta, não a versão em uso. | Nenhum — é a cópia que não roda |
| 3 | `hardware.shutil_disk_usage()` (`hardware.py:265-267`) — wrapper de 2 linhas em volta de `shutil.disk_usage` | Nunca chamada. O espaço em disco de verdade já é calculado direto em `hardware.disco()` (`hardware.py:215`). | Nenhum |

### Correções propostas (bug real ou risco real, não é remoção de código morto)

| # | O quê | Prova / cenário concreto | Proposta |
|---|---|---|---|
| 4 | **Bug real — perda de dados silenciosa.** `arena.py:3334-3337`, dentro de `/api/perfil/novo` ("Começar do zero"): `fazer_backup()` roda dentro de `try / except Exception: pass` **antes** de apagar `arena.db`, `config.json`, `controles.json`, `manifesto.json` e `arena_override.cfg`. Se o backup falhar, o código apaga os arquivos do mesmo jeito. | O comentário do próprio código promete "se alguém clicar por engano, o progresso ainda está em backup" — mas se `fazer_backup()` lançar exceção (pen drive quase cheio, pasta de backup virou só-leitura, mídia removida no meio), essa promessa quebra sem avisar ninguém. Cenário: professor clica "Começar do zero" com o pen drive cheio → backup falha → perfil inteiro apagado, sem cópia e sem mensagem de erro. | Se o backup falhar, **cancelar o apagamento** e devolver erro claro ("Não consegui garantir uma cópia de segurança antes de apagar. Nada foi apagado. Verifique o espaço livre e tente de novo.") em vez de seguir em frente sem rede de segurança. |
| 5 | **Portabilidade — navegador não encontrado sem admin.** `arena.py:4275-4279`, lista `NAVEGADORES`, só verifica os caminhos de instalação **com administrador** (`C:\Program Files\...`). | Instalação de Chrome **sem admin** (comportamento padrão do instalador quando falta privilégio — o cenário exato que o ARENA já assume como normal, "sem permissão de administrador") fica em `%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe`, caminho que a lista não verifica. Confirmado nesta máquina de desenvolvimento: o Edge instalado no caminho padrão foi achado, mas a checagem não cobre instalação por usuário. Quando nenhum caminho da lista bate, o ARENA cai silenciosamente para `webbrowser.open()` — abre numa aba comum, sem o modo "app" limpo. | Acrescentar os caminhos `%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe` e `%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe` (via `os.environ["LOCALAPPDATA"]`) à lista `NAVEGADORES`, antes dos caminhos de admin. |
| 6 | **Documentação desatualizada.** `2-JOGOS.md:358-359` diz, para o PlayStation 1: "o núcleo dele *é* o DuckStation". | O núcleo de verdade, hoje, é o **SwanStation** (só troca para PCSX ReARMed durante o Jogar Junto — ver CLAUDE.md, seção "Rede e partida a dois"). Um aluno que abrir a lista de núcleos do RetroArch procurando "DuckStation" não vai achar nenhum com esse nome. | Trocar a frase para citar SwanStation, com uma nota de que ele nasceu como um fork do DuckStation (é por isso que o nome aparece em alguns lugares do código) — mantém o contexto sem confundir o aluno na hora de procurar. |

### Verificar, não decidir agora (pendência já existente, só reforçada)

| # | O quê | Situação |
|---|---|---|
| 7 | `graficos.py:397` grava a chave `"duckstation_BIOS.Path"` (além de `"swanstation_BIOS_Path"`); `graficos.py:550-551` grava `"duckstation_MemoryCards.Card1Type"` e `"duckstation_MemoryCards.Directory"`. | Pode ser hedge intencional (SwanStation nasceu como fork do DuckStation e pode aceitar as duas grafias de opção) ou resíduo de quando o projeto usava o núcleo DuckStation de verdade. **Não decido sozinho** — isto é exatamente a pendência já escrita no CLAUDE.md, seção 10: "Confirmar as chaves de BIOS e memory card do núcleo swanstation contra um `retroarch-core-options.cfg` gerado pelo RetroArch real". Proponho resolver isso quando testarmos PS1 de verdade (Fase 3 ou Fase 5), não como remoção às cegas agora. |

### Checado, sem achado (para não parecer que não foi olhado)

- **As 20 chaves de `config.json`**: todas usadas mais de uma vez no código. Nenhuma órfã.
- **~50 `except OSError/Exception: pass` ou `continue`**: a grande maioria segue o padrão defensivo já documentado no CLAUDE.md ("tenta a próxima fonte, degrada sem travar") — sondagem de adaptador de rede, leitura de hardware opcional, prioridade de processo, checkpoint de banco ao fechar. Não escondem bug real, exceto o item 4 acima, que é o único promovido à lista de correção.
- **Rotas da API**: as 2 que pareciam sem uso na Fase 0 (`/api/capa`, `/api/jogo/impressao`) foram confirmadas vivas — ver correção acima, no inventário de rotas.
- **Textos em inglês na tela**: nenhum achado na varredura por padrões comuns (`Save`, `Cancel`, `Loading`, `Settings`, `alert(...)` em inglês).
- **Arquivos duplicados da junção das duas versões**: `launcher\` tem exatamente os 5 arquivos que o CLAUDE.md documenta (`index.html`, `app.js`, `estilo.css`, `galaxy-background.js`, `field-background.js`) — nada sobrando.
- **Frequência dos 2 serviços permanentes** (`rodar_vigia`, `anunciar_e_escutar`): já justificada no CLAUDE.md pelo desgaste do cartão SD (modo econômico sobe o intervalo do vigia de 20s para 60s). Não proponho mudança agora — a Fase 2 pede o número real de gravações em disco por hora, e é lá que decido se ainda está alto demais.

### Aplicação (23/09/2026)

Todos os 6 itens aplicados no ramo `auditoria`. Verificação depois de
aplicar:

- `import arena, graficos, hardware` sem erro de sintaxe (as remoções 1–3
  não quebraram nenhum import).
- Bateria de 44 testes automatizados: **OK, 0 falhas**, antes e depois.
- Item 4 (o bug de perda de dados) ganhou teste novo e específico —
  `ferramentas\teste_backup_falha_cancela_apagamento.py`, que sobe um ARENA
  isolado (cópia temporária, não mexe na pasta real) e prova os dois
  caminhos: **Caso 1** (backup funciona) continua apagando o perfil normal
  (HTTP 200, `apagados: 5`); **Caso 2** (backup forçado a falhar) agora
  **cancela** o apagamento (HTTP 500, mensagem clara, os 3 arquivos
  conferidos continuam intactos). Os dois casos passaram.
- Item 5 (lista `NAVEGADORES`): conferido que os 2 caminhos novos
  (`%LOCALAPPDATA%\...`) entram corretamente na lista, expandidos para o
  caminho real desta máquina. Não havia Chrome/Edge instalado sem admin
  nesta máquina de desenvolvimento para testar o caso positivo de verdade
  (só o Edge no caminho padrão) — fica como item do roteiro manual de sala,
  se algum notebook da escola tiver Chrome instalado por usuário.
- Item 6: frase de `2-JOGOS.md` corrigida para citar SwanStation.

### Fica pendente (não é da Fase 1)

- `dados\` com 38 logs do RetroArch sem rodízio (achado na Fase 0) — a correção (limite de tamanho + rodízio) é da Fase 2, não da Fase 1. **Resolvido na Fase 2, ver abaixo.**

---

## Fase 2 — Leveza e desempenho

### CPU parado

Já medido na Fase 0: **0,04%**, perto de zero. Nada a corrigir — não achei
nenhuma consulta repetida sem necessidade na revisão desta fase (o catálogo
e a configuração já têm cache por data de modificação do arquivo, ver
`CLAUDE.md` seção 6).

### Gravações em disco — logs do RetroArch sem rodízio (achado real da Fase 0, corrigido)

`dados\` tinha 38 arquivos `retroarch__AAAA_MM_DD__HH_MM_SS.log` (um por
sessão, `log_to_file_timestamp = true`), crescendo para sempre — o
comentário original do código («o arquivo fica em dados\retroarch.log e o
ARENA não o apaga») estava desatualizado: virou um arquivo novo por sessão,
não um único arquivo reescrito.

**Correção**: `limpar_logs_antigos()` nova em `arena.py`, chamada a cada
abertura (`principal()`), mantém só os `LOGS_MANTIDOS = 10` mais recentes —
dá pra investigar uma sessão recente sem o cartão SD/pen drive acumular log
para sempre. Testado contra pasta isolada (`ferramentas\teste_rodizio_logs.py`,
16 logs falsos → sobram 10, arquivo que não é log não é tocado) **e** contra
a pasta real do projeto, subindo o ARENA de verdade uma vez: **36 → 10**
logs, confirmado.

### Fundos animados — pendência antiga do CLAUDE.md, resolvida

Achado real, lendo o código: `galaxy-background.js` e `field-background.js`
tinham um loop de animação (`requestAnimationFrame`) que **rodava para
sempre, a cada quadro, mesmo com o canvas escondido** (tema errado) — só não
desenhava nada, mas continuava agendando o próximo quadro sem parar. Nem
modo modesto nem "prefira menos movimento" (do Windows/navegador) tinham
como desligar isso: a informação de modo modesto nem chegava a
`document.body.dataset` para o script ler.

**Correção**: `atualizarBotaoTema()` (`app.js`) agora também grava
`document.body.dataset.modoModesto`; os dois fundos ganharam `deveAnimar()`
(tema certo **e** modo modesto desligado **e** sem pedido de menos
movimento) e só chamam `requestAnimationFrame` quando isso é verdade — caso
contrário o loop para de vez, e um vigia a cada 2s (não mais a cada quadro)
o acorda se a condição mudar.

**Bug pego no meio do próprio teste, antes de aplicar**: a primeira versão
da correção só atualizava `canvas.style.display` durante o `draw()` — como
o `draw()` para de rodar quando pausado, trocar de tema com o modo modesto
ligado deixaria o fundo errado preso na tela. Corrigido separando
`sincronizarVisibilidade()` (roda sempre, inclusive pausado) de `draw()`
(só roda quando deveAnimar()). Confirmado no navegador de verdade: tema
escuro+modo modesto → só o fundo galáctico aparece; tema claro+modo modesto
→ só o fundo de campo aparece, os dois com a animação parada.

**Limitação de medição, honesta**: não consegui medir o custo de CPU do
loop *ativo* (rodando de verdade) nesta sessão de automação do navegador —
a aba controlada pelo Claude in Chrome ficou com `document.visibilityState
= "hidden"` o tempo todo (não é a janela em foco do sistema), e navegador
nenhum roda `requestAnimationFrame` de aba em segundo plano, pausado ou não
— então não dava pra ver a diferença de custo entre "animando" e "pausado"
por essa via. O que ficou provado, por leitura de código e pelo teste do
`sincronizarVisibilidade()`: o loop realmente para de se re-agendar quando
pausado (não é mais "sempre pediu o próximo quadro"), o que já resolve o
crescimento sem fim que a pendência do CLAUDE.md descrevia. Medir o ganho
de FPS/CPU de verdade, num Celeron fraco, fica pro roteiro manual de sala
(Fase 4/6) — mesma limitação já registrada para o `netplay_check_frames`.

### CSS não usado

Script novo `testes\varredura_fase2_css.py`: 185 seletores de classe no
CSS, 32 sem nenhuma ocorrência fora do `estilo.css`. Conferido um a um
(risco de falso positivo: classe montada por template literal no JS, tipo
`` `midia--${tipo}` ``, nunca aparece como texto literal na busca) —
**27 eram exatamente isso**, confirmados vivos (`midia--*`, `capa-*`,
`jogo--*`, `custo--*`, `desempenho--*`, `sinal--*`, `ranking-pos--*`, todos
construídos com um valor vindo de dado, não digitados por extenso em
lugar nenhum). **5 eram mortos de verdade**, confirmados por dois lados —
zero ocorrência do nome completo E zero ocorrência da raiz do nome em
`app.js`/`index.html`, e a maioria com uma explicação encontrada no próprio
código do motivo de terem ficado pra trás:

| Classe | Por que estava morta |
|---|---|
| `.campo-apelido` (+ `span`, + regra de tela pequena) | O campo de apelido virou um modal (`#modalApelido`) num redesenho; a classe do wrapper antigo nunca foi apagada do CSS |
| `.jogo-acoes` (+ `.botao`, + regra de tela pequena) | Comentário no próprio `app.js` (linha 531): "As ações grandes ficam no painel de detalhes... não repete uma fileira de botões pequenos em cada jogo" — decisão de design documentada, CSS órfão desde então |
| `.jogo-gerir` | Botão de gerenciar virou `#btnGerirSelecionado` (id, no painel de detalhes), não mais uma classe no card |
| `.jogo-dupla` | Mesmo padrão — Jogar Junto virou `#btnMultiplayerSelecionado` |
| `.acervo-cabeca-acoes` | Sem nenhum vestígio em `index.html`; layout do acervo mudou e a classe ficou pra trás |

Removidas as 5. Confirmado visualmente no navegador de verdade depois da
remoção (tela principal, Ajustes → Avançado, Biblioteca online) — nenhuma
mudança visual, como esperado de CSS morto. Bateria de 44 testes: OK.

### JavaScript não usado

Não achei função JS órfã nesta revisão (o `app.js` é um arquivo só, sem
módulos separados para cruzar) — o achado real de JS desperdiçado desta
fase foi o loop de animação sem fim dos fundos, já corrigido acima.

### Teste de estresse do catálogo (5.000 jogos falsos)

Script novo `testes\teste_estresse_catalogo.py`: cria 4.998 arquivos falsos
(extensão válida, 0 bytes) espalhados em 3 consoles reais (NES, Super
Nintendo, Game Boy), numa subpasta própria fácil de apagar depois, e mede
`indexador.indexar()` direto (sem precisar do servidor HTTP inteiro).
Apaga tudo ao final, mesmo se o teste falhar no meio (bloco `finally`).

| Medida | Resultado |
|---|---|
| Antes (catálogo real) | 32 jogos, indexado em 0,131s |
| Depois (+4.998 falsos = 5.030 jogos) | indexado em **1,481s** — varredura fria, sem cache |
| Segunda chamada, mesmo catálogo | **0,023s** — cache por assinatura de pasta funcionando, ~64× mais rápido |

Catálogo real conferido depois: voltou para 32 jogos, pasta de teste
apagada. Não subi o servidor HTTP para conferir "a tela continua
respondendo" à parte — a rota `/api/catalogo` só devolve o que
`indexador.indexar()` já calculou, então uma indexação de 1,48s não vira
travamento perceptível na tela.

### Aplicação e testes (Fase 2)

Bateria de 44 testes automatizados: **OK, 0 falhas**, em cada etapa
(rodízio de logs, fundos animados, remoção de CSS, teste de estresse).
Arquivos alterados: `servidor\arena.py` (rodízio de logs),
`launcher\app.js`, `launcher\galaxy-background.js`,
`launcher\field-background.js` (fundos animados), `launcher\estilo.css`
(CSS morto removido). Scripts novos: `testes\varredura_fase2_css.py`,
`testes\teste_estresse_catalogo.py`, `ferramentas\teste_rodizio_logs.py`.

---

## Fase 3 — Testes do servidor e da API (offline e online)

Nenhum teste desta fase mexeu na pasta real do projeto — todos sobem um
ARENA isolado (cópia temporária de `servidor`/`dados`/`launcher`, apagada
ao final, mesmo padrão já usado desde a Fase 1) ou testam a função
diretamente. As únicas exceções, feitas de propósito e de forma segura,
foram as provas ao vivo do CSRF (revertida no mesmo teste) e da limpeza de
logs (rodou o ARENA real uma vez, só para confirmar o rodízio na pasta de
verdade).

### 1. Fuzz das 45 rotas

Script novo `testes\fuzz_rotas.py`: para cada rota, testa dados corretos,
dados faltando, tipo errado, texto gigante (2 MB), acentos/emoji, tentativa
de sair da pasta (nos campos que recebem caminho de arquivo) e 20 pedidos
repetidos rápido. 244 checagens ao todo.

**Resultado final: 7 "falhas" reportadas pelo script, todas explicadas —
nenhuma é bug real:**

- **7×** `414 URI Too Long` em rotas GET com o campo de texto gigante na
  query string. Isto não é o ARENA: é o `http.server` da própria biblioteca
  padrão do Python recusando a linha da URL antes mesmo dela chegar ao
  código do ARENA — comportamento correto e seguro (rejeita cedo, não
  trava). A checagem do meu script era severa demais aqui (esperava corpo
  JSON até em erro que nunca passa pelo roteador da aplicação); não é um
  achado da auditoria.

Antes de chegar nesses 7, o fuzz achou e ajudou a corrigir problemas reais
— ver itens 2, 4 e 6 abaixo.

**Achado real, corrigido — respostas de erro inconsistentes.** 4 pontos
usavam `self.send_error(...)` (gera uma página HTML de erro, do próprio
Python) em vez do `self.erro(...)` do ARENA (`{"ok": false, "erro": "..."}`,
o formato que todas as outras ~45 rotas usam): os 3 erros de `/api/capa`
("Capa não encontrada", "Não é imagem", "Não consegui ler a capa"), os 2 de
`/api/perfil/foto`, e os 2 "Rota não encontrada" genéricos no fim de
`api_get`/`api_post`. Corrigido — as 7 trocadas para `self.erro(...)`.
Confirmado: bateria de 44 testes OK, fuzz não aponta mais essas 7 como
inconsistentes.

### 2. Tentativa de sair da pasta (path traversal)

O fuzz genérico não testava isto direito para `/api/capa` (todo payload de
travessia usado lá termina em `.ini`, e a rota recusa **antes** de checar a
pasta, só por não ser imagem). Script à parte,
`testes\teste_travessia_capa.py`: cria um "segredo" fora da pasta permitida
terminando em `.png` de propósito, e tenta 6 formas de alcançá-lo
(`../`, `..\`, caminho absoluto, misturado com `jogos/..`). **Nenhuma
vazou** — `dentro_da_pasta()` (usa `os.path.commonpath`, não `startswith`)
funciona.

`/api/mala` foi outra história — ver item 4b.

### 3. Concorrência — 50 pedidos ao mesmo tempo

Script `testes\teste_concorrencia.py`: 50 threads batendo ao mesmo tempo em
`/api/config`, `/api/placar`, `/api/mapeamento/definir` e
`/api/cheat/adicionar` (todas gravam em disco).

**Achado real, corrigido — corrida de gravação no Windows.** Rodando pela
primeira vez: 0 a 4 das 50 respostas (variava a cada rodada) vinham com
erro 500, `[WinError 5] Acesso negado`, no `os.replace()` de
`gravar_texto_atomico()`. Causa: `carregar_config()`/`ler_config_do_disco()`
**leem** o arquivo sem usar a trava `TRAVA_ARQUIVO` (de propósito — senão
toda leitura esperaria toda escrita), e no Windows (diferente do Linux)
`os.replace()` pode falhar quando OUTRA thread tem o arquivo destino aberto
para leitura no instante exato da troca. É transitório: a leitura solta em
microssegundos. Corrigido com uma repetição curta (até 5 tentativas, 50ms
de espera entre elas) só em cima do `PermissionError` do `os.replace()` —
não muda o resto da função. Confirmado com **6 rodadas consecutivas de 50
pedidos simultâneos, 0 erros em todas**, e depois nas rodadas seguintes de
toda a Fase 3. Bateria de 44 testes: OK.

Nenhum arquivo saiu corrompido em nenhuma rodada (`config.json`/
`controles.json` continuavam JSON válido, `PRAGMA integrity_check` do
`arena.db` sempre `ok`) — mesmo nas rodadas com erro 500, o problema era a
gravação **recusada**, não uma gravação pela metade. O `os.replace()`
atômico já garantia isso; o achado era só a experiência ruim de ver "erro
interno" numa operação normal.

### 4. Segurança

#### 4a. Rede — achado maior da auditoria, corrigido

**Antes desta fase, TODAS as 45 rotas da API ficavam abertas para
qualquer computador da rede assim que "Aceitar conexões da rede" era
ligado** (obrigatório para o Jogar Junto funcionar). Conferido lendo o
código inteiro: `self.client_address` (o endereço de quem fez o pedido) só
era consultado em UM lugar, dentro de `/api/sinc/receber`, sem relação
nenhuma com controle de acesso — nenhuma outra rota checava de onde o
pedido vinha. Na prática: um colega na mesma rede da escola conseguiria
mandar `/api/perfil/novo` (apagar o perfil de outro aluno), `/api/config`
(mudar a configuração de outro), `/api/jogar` (abrir jogo no computador de
outro), `/api/cheat/adicionar`, etc — exatamente o cenário que o plano da
auditoria descreve como inaceitável.

**Corrigido**: lista nova `ROTAS_REDE_EXTERNA` em `arena.py` com só as 8
rotas que a partida a dois e a sincronização precisam de verdade
(`/api/colegas`, `/api/ranking`, `/api/jogo/impressao`, `/api/amigo/testar`,
`/api/amigo/codigo`, `/api/partida/testar`, `/api/sinc/ola`,
`/api/sinc/receber`). Toda outra rota, vinda de um endereço que não é este
computador (nem 127.0.0.1 nem nenhum dos próprios endereços de rede da
máquina), é recusada com 403 antes de executar qualquer coisa. O jogo em
si (netplay do RetroArch) nunca passou por aqui — usa a porta 55435 dele,
separada — então isto não tira nenhuma funcionalidade de verdade.

Testado com `testes\teste_acesso_de_rede.py`: como não dá para simular o
endereço de uma segunda máquina de verdade sem uma segunda máquina física
(a detecção usa o endereço real do socket, que o próprio Python garante),
o teste subclassa o `Manipulador` só para forçar
`pedido_e_local()` a devolver `False` — exatamente a condição que uma rede
de verdade produz. Resultado: as 8 rotas da lista continuam respondendo
normalmente; **todas** as outras testadas (`/api/config`, `/api/perfil/novo`,
`/api/jogar`, `/api/cheat/adicionar`, `/api/mala`, `/api/estado`,
`/api/catalogo`) foram recusadas com 403, e o `config.json` de verdade
ficou intocado. Bateria de 44 testes: OK.

**Limite honesto**: isto prova a lógica de bloqueio de verdade (a condição
que dispara é exatamente a de um pedido vindo de fora), mas não substitui
confirmar com uma segunda máquina física na rede da escola — vira item do
roteiro manual da Fase 4/6.

#### 4b. CSRF / origem cruzada — provado ao vivo, corrigido

Testado de verdade, não só lido: subi o ARENA real e uma página HTML servida
por **outra origem** (porta diferente, `127.0.0.1:9999`) no mesmo Chrome,
com um `fetch()` mandando `POST /api/config` com `Content-Type: text/plain`
contendo `{"tema":"escuro"}`. **Funcionou** — o `tema` no `config.json` real
mudou para `"escuro"`, mesmo a página tendo relatado "Failed to fetch" (o
navegador nunca deixou o site LER a resposta, mas o pedido já tinha sido
processado no servidor — CSRF às cegas, o tipo mais perigoso: o site nem
precisa saber se funcionou). Revertido no mesmo teste.

Causa: `ler_corpo()` sempre tentava interpretar o corpo como JSON,
**qualquer que fosse o `Content-Type`**. Um `Content-Type: text/plain` é um
"pedido simples" para o navegador — não exige permissão prévia (preflight
CORS) para ser enviado, só para a resposta ser lida. Como o ARENA nunca
checava o cabeçalho, processava o pedido mesmo assim.

**Corrigido**: `do_POST` agora recusa (415) qualquer pedido cujo
`Content-Type` não seja exatamente `application/json` — é o que a própria
tela (`pedir()` em `app.js`) e a sincronização entre ARENAs sempre mandam,
conferido nos dois lugares antes de aplicar. Reproduzido o mesmo ataque
depois da correção: `tema` continuou `"claro"`. Bateria de 44 testes +
todos os outros testes de HTTP desta fase: OK (todos já mandavam
`Content-Type: application/json` de propósito).

#### 4c. `/api/mala` — escrita em caminho arbitrário, provada ao vivo, corrigida

Achado durante o mapeamento das rotas: `trocar_pela_mala(dados.get("caminho"))`
usava o `caminho` vindo do cliente **sem validação nenhuma** — nem
`dentro_da_pasta()`, nem `os.path.basename()`, os dois que toda outra rota
com caminho de arquivo do cliente usa (ex.: `/api/importar`). Provado ao
vivo: um `POST /api/mala` com `{"caminho": "C:\\Users\\...\\Temp\\arena_prova_mala.json"}`
criou o arquivo exatamente ali — escrita em qualquer caminho que o processo
consiga gravar, escolhido inteiramente pelo cliente.

**Corrigido**, respeitando o uso de verdade (a mala pode estar na raiz de
QUALQUER pen drive, não só dentro da pasta do ARENA — por isso não dá para
usar `dentro_da_pasta()` como as outras rotas): agora exige que o **nome**
do arquivo seja exatamente `ARENA-troca.json`, rejeitando qualquer outro
nome. Testado em 3 casos (`testes\teste_mala_validacao.py`): nome arbitrário
→ recusado, arquivo não criado; nome certo numa pasta diferente (simulando
outro pen drive) → continua funcionando; sem `caminho` nenhum (uso normal)
→ continua funcionando. Bateria de 44 testes: OK.

#### 4d. XSS — checado, sem achado

`app.js` nunca usa `innerHTML`/`insertAdjacentHTML`/`outerHTML` em lugar
nenhum (varredura completa do arquivo) — todo texto vindo de fora (apelido
de colega, título de jogo, mensagens) passa por `.textContent`, que nunca
interpreta HTML. Não há caminho de XSS refletido nem armazenado pela tela.

### 5. Internet ruim (DNS falho, timeout, portal cativo)

**Achado real, corrigido — `internet_archive.instalar()` não tratava falha
de rede nem resposta fora do esperado.** `buscar()` já tinha essa proteção;
`instalar()` não, em dois pontos: a busca de metadados (`_ler(...)`, sem
try/except) e o download em si (`subprocess.run(["curl.exe", ...])`, erro
do curl não tratado). Provado ao vivo com dois cenários simulados
(monkeypatch de `_ler`, sem precisar de rede de verdade): (1) rede fora —
vazava `OSError` cru; a rota em `arena.py` tem um `except Exception`
genérico que evita o 500 sem tratamento, mas a mensagem virava "Download
falhou: rede inacessivel" (técnica, não explica o que fazer); (2) portal
cativo (HTML no lugar do JSON esperado) — o `json.loads` no HTML gerava
`Expecting value: line 1 column 1 (char 0)`, mensagem do interpretador
Python, não uma frase para o aluno entender.

Corrigido: as duas chamadas agora ficam dentro de `try/except`, convertendo
para uma mensagem única e clara: "Não consegui falar com o Internet Archive
agora. Confira a internet e tente de novo." (metadados) e "O download caiu
no meio do caminho. Confira a internet e tente de novo." (arquivo).
Reproduzidos os dois cenários depois da correção: mensagem clara nos dois
casos, nenhuma exceção crua. Bateria de 44 testes: OK.

**Achado real, corrigido — `capas_online.py` aceitava qualquer resposta
200 como "capa baixada com sucesso", mesmo sem ser imagem.** `curl --fail`
só falha em erro HTTP (4xx/5xx) — um portal cativo de Wi-Fi normalmente
responde 200 com a página de login em HTML, então `--fail` não pega isso.
Provado ao vivo com um servidor local simulando o portal: `curl` devolveu
código de saída 0 e um arquivo de 85 bytes de HTML foi salvo — exatamente
a condição que o código aceitava como "capa boa" (`returncode == 0` +
arquivo não vazio), sem checar o CONTEÚDO. Corrigido: `_e_png_de_verdade()`
nova, confere a assinatura de bytes real do PNG (`\x89PNG\r\n\x1a\n`) antes
de aceitar. Testado com HTML disfarçado de `.png` (recusado) e PNG de
verdade (aceito). Bateria de 44 testes: OK.

Netplay pela internet (repasse do RetroArch): `graficos.repasses_disponiveis()`
é só uma lista fixa, sem chamada de rede nenhuma — não tem como travar por
internet ruim. A conexão de repasse em si é feita pelo próprio RetroArch
(processo separado), fora do servidor Python do ARENA.

### 6. Acervo — verificação de SHA-256

**Confirmado funcionando, ao vivo** (`testes\teste_acervo_sha256.py`):
subi um servidor HTTP local com um arquivo de conteúdo e hash conhecidos,
salvei um item no manifesto com um SHA-256 **errado** de propósito — `acervo.instalar()`
recusou (`"SHA-256 diferente: download recusado por seguranca."`), sem
criar o arquivo de destino. Com o SHA-256 **certo**, instalou normalmente.
Esta é exatamente a proteção que o plano da auditoria pedia para conferir,
e ela já existia e funciona.

**Achado à parte, corrigido por analogia** — o caminho de download do
Internet Archive (`internet_archive.instalar()`, mecanismo diferente e mais
novo, busca dinâmica em vez de manifesto curado) não tinha proteção
equivalente: calculava um SHA-256 do arquivo baixado mas **nunca comparava
com nada** (nem guardava no retorno). O Internet Archive não declara
SHA-256 por arquivo na própria API — declara `md5`, `sha1` e `crc32`
(conferido numa consulta real à API deles). Corrigido: agora calcula SHA-1
(o mais forte dos três que existem) e compara com o que o Internet Archive
declarou para aquele arquivo específico, recusando se não bater. Testado
em 3 casos (`testes\teste_internet_archive_download.py`): download que cai
no meio (erro claro), conteúdo trocado/incompleto (SHA-1 não bate, recusado,
nada instalado), caminho feliz (instala normal). Bateria de 44 testes: OK.

### 7. `/api/partida/testar` — custo real de um endereço inválido

Achado durante o fuzz: um `endereco` sem sentido de rede (ex.: `"12345"`)
fazia a rota demorar o bastante para estourar o tempo limite do meu
script de teste. Medido à parte: **~5,3 s** — a rota tenta resolver o
mesmo endereço **duas vezes seguidas** (uma para a porta do ARENA, outra
para a porta da partida), e no Windows `socket.create_connection()` não
respeita o `timeout` do socket na fase de resolução de nome (medido direto:
uma resolução de endereço inválido custa ~2,6 s sozinha). Não é um bug de
segurança — a rota já está na lista de acesso de rede restrito (item 4a) —
mas é um custo real e evitável: um colega testando o endereço errado
repetidas vezes ocuparia uma thread por ~5 s a cada tentativa.

Corrigido: resolve o endereço **uma vez** (`socket.gethostbyname`) e reusa
o IP nas duas tentativas de conexão, cortando o custo pela metade — medido
depois da correção: **~2,68 s**. Confirmado que a mensagem de diagnóstico
("Não alcanço o computador dele...") continua aparecendo igual no caminho
rápido, e que o caminho feliz (endereço alcançável) continua funcionando
normal (`testes\teste_partida_testar_timing.py`). Bateria de 44 testes: OK.

### 8. Teste de longa duração (acelerado)

"Horas" de verdade não cabem numa sessão de auditoria — acelerado:
milhares de pedidos num intervalo curto, medindo RAM e handles do processo
a cada 10s (`testes\teste_longa_duracao.py`).

| Duração testada | Pedidos | Falhas de conexão | Crescimento de RAM | Crescimento de handles |
|---|---|---|---|---|
| 3 min | 57.596 | 0 | 0,2 MB | 10 |
| 45s (reconfirmação, depois de todas as correções desta fase) | 15.316 | 0 | 0,4 MB | 14 |

RAM e handles ficam estáveis depois do aquecimento inicial (esperado — é o
Python se ajustando) — nenhum vazamento detectado sob carga sustentada,
nas duas rodadas.

### 9. Sem internet, o que é local funciona 100%

Confirmado por construção, não só por suposição: **todos** os testes desta
fase (fuzz das 45 rotas, concorrência, mala, acesso de rede, longa duração)
rodam contra uma cópia isolada do ARENA que não tem nenhuma mock nem
simulação de internet — e todos passaram normalmente, porque nenhuma rota
local (catálogo, config, controles, cheats, placar, mapeamento, mala) faz
qualquer chamada de rede. As únicas partes que tocam a internet de verdade
(`internet_archive.py`, `capas_online.py`, repasse de netplay) já foram
testadas à parte, com internet simulada ruim (item 5) — e falham com
mensagem clara, sem travar o resto do ARENA.

### Aplicação e testes (Fase 3)

Todas as correções desta fase foram aplicadas direto (a Fase 3 não tem
"pare e espere aprovação" no plano — só as Fases 1, 7 e 8 têm), testadas
uma a uma e a bateria de 44 testes automatizados conferida depois de cada
mudança em `servidor\arena.py`, `servidor\internet_archive.py` e
`servidor\capas_online.py`: **OK, 0 falhas, em toda etapa.**

Scripts novos: `testes\fuzz_rotas.py`, `testes\teste_travessia_capa.py`,
`testes\teste_concorrencia.py`, `testes\teste_acesso_de_rede.py`,
`testes\teste_mala_validacao.py`, `testes\teste_acervo_sha256.py`,
`testes\teste_internet_archive_download.py`,
`testes\teste_partida_testar_timing.py`, `testes\teste_longa_duracao.py`.

---

## Fase 4 — Jogar Junto: o coração do ARENA

Esta fase abriu janelas de verdade do RetroArch várias vezes (não dá para
testar netplay sem tela — não existe modo sem interface). Todas fechadas ao
final de cada teste. Nenhum teste mexeu em `dados\`, `retroarch\saves`,
`retroarch\states` nem no `arena_override.cfg` real — cada instância de
teste usa cópia isolada dessas pastas numa pasta temporária apagada ao
final.

### 1. Multitap — funcionalidade nova, pedida explicitamente no plano

O plano pediu para "descobrir como o ARENA deve ligar o Multitap sozinho".
Não existia nada disso no código — foi preciso pesquisar o mecanismo real
(lido no código-fonte do núcleo `snes9x`, não suposto): a porta 2 do
console vira `RETRO_DEVICE_JOYPAD_MULTITAP` (valor `257`), o que abre mais
4 encaixes de controle (jogadores 2 a 5) mantendo a porta 1 como jogador 1
normal — é assim que o adaptador de verdade funciona (pluga na porta 2, não
substitui a porta 1).

**Implementado** (aprovado pelo Rafael como funcionalidade completa, com
tela):
- `graficos.opcoes_de_partida(..., multitap=True)` liga
  `input_libretro_device_p2 = 257` quando o jogo pede.
- `graficos.jogo_suporta_multitap()` + `consoles.json → snes → jogos_multitap`
  (lista curada — hoje só "Super Bomberman" — mesmo espírito do "system
  link" do PS2: cresce testando com jogo real, nunca por suposição).
- `indexador.py` calcula `jogadores_max` **por jogo**, não por console
  inteiro — só o jogo específico da lista curada mostra a opção de
  "Jogador 3/4/5"; o resto do catálogo de SNES continua em 2, sem
  confundir o aluno com uma opção que não serve pro jogo dele.
- `app.js`: o seletor de posição do jogador já existia (genérico, construído
  dinamicamente) — só precisou passar a ler do jogo específico em vez de só
  da plataforma.

**Testado com RetroArch de verdade**, Super Bomberman 4 (SNES), host + até
4 convidados no mesmo computador:

| Cenário | Resultado |
|---|---|
| Jogador 5 sozinho (sem 2, 3, 4) | Conecta perfeitamente — prova que a configuração do Multitap e a posição 5 estão corretas |
| Jogadores 2, 3 e 4 juntos | Conectam todos, sem erro, com ping medido (11–34 ms neste computador) |
| Jogadores 2, 3, 4 **e** 5 juntos | Os 3 primeiros conectam; o 4º (a última tentativa, seja ela qual posição for) **sempre falha** — "Falha ao conectar ao host", reproduzido em **3 rodadas**, inclusive com esperas bem generosas (10s entre cada abertura, 25s de espera final) para afastar a hipótese de disputa de CPU entre 5 emuladores no mesmo computador |

**Achado real, não resolvido.** O mecanismo exato não foi identificado
apesar de pesquisa no código-fonte oficial do RetroArch: `input_max_users`
(padrão 8 em build de Windows) e `MAX_CLIENTS` (32, constante de
compilação) foram conferidos e nenhum dos dois explica um limite de 4
jogadores totais. **Duas hipóteses, nenhuma confirmada:**
1. É um limite real do RetroArch não documentado que não consegui
   localizar no código em tempo hábil.
2. É um artefato de testar os 5 "computadores" todos como `127.0.0.1`
   (mesmo endereço de origem) — não dá para descartar isso sem 5 máquinas
   físicas de verdade.

**Isto vira item do roteiro manual** (seção no fim deste relatório): testar
com 5 notebooks reais da escola é a única forma de confirmar qual das duas
hipóteses é a certa. Se o limite for real mesmo com 5 máquinas físicas,
Super Bomberman fica documentado como "até 4 jogadores confirmados, 5º sem
confirmação" — igual ao já documentado para N64/Dreamcast/PSP sem netplay:
limite honesto, não escondido.

### 2. Multiplayer local (GoldenEye 007, N64 — 4 controles, 1 computador só)

Diferente do item 1, isto **não é netplay** — são 4 controles físicos no
MESMO computador. `controles.opcoes_do_console()` já suportava isso
(`input_max_users` em Ajustes → Avançado, opções 1/2/4/8, já exposto na
tela); testado direto:

```
input_libretro_device_p1 = 1
input_libretro_device_p2 = 1
input_libretro_device_p3 = 1
input_libretro_device_p4 = 1
```

As 4 portas corretas, e o jogo abriu sem nenhum erro de controle/entrada
(os únicos erros no log foram de **áudio**, "Failed to get default audio
endpoint" — falha do driver de som nesta máquina depois de várias rodadas
de RetroArch abertas em sequência, sem relação nenhuma com a configuração
de controle testada; não é um bug do ARENA).

**Controle + teclado junto**: o recurso existe (`dispositivo_extra`), mas
**não para N64** — a lista de consoles que aceitam essa troca é PS2,
Dreamcast, MSX e ScummVM (documentado no próprio código). Testado contra
PS2 (um dos consoles que de fato suporta): `input_libretro_device_p2` troca
corretamente para teclado (`3`) ou mouse (`2`) quando pedido. Não é bug —
GoldenEye/N64 nunca teve essa opção nem no código original; o item do plano
"controle E teclado junto" e "4 controles" são dois recursos diferentes,
cada um testado no console certo.

**Apertar botão de verdade, com 4 controles físicos**: fica pro roteiro
manual — não dá pra simular sem hardware de verdade.

### 3. Simulador de rede ruim

Script novo `testes\proxy_rede_ruim.py`: um repasse TCP (RetroArch usa TCP
no netplay) em Python puro, que atrasa cada pedaço de dado em N
milissegundos e, com uma chance configurável, atrasa um pedaço bem mais —
é assim que "perda de pacote" se sente de verdade num protocolo TCP (o dado
não some, chega muito atrasado, como uma retransmissão de verdade). O
mecanismo do proxy foi **confirmado isoladamente** antes de usar com
RetroArch: com 150ms configurados, um echo simples foi e voltou em 0,31s —
bate com o esperado (150ms × 2, ida e volta).

Testado com Super Bomberman 4 (host + 1 convidado) atrás do proxy, 5
cenários:

| Cenário | Conectou? | Avisos de travada/timeout do RetroArch |
|---|---|---|
| Só atraso, 50 ms | Sim | 0 |
| Só atraso, 100 ms | Sim | 0 |
| Só atraso, 200 ms | Sim | 0 |
| Perda 1% (com 50ms de base) | Sim | 0 |
| Perda 5% (com 50ms de base) | Sim | 0 |

**Achado sobre o método de medição**: o "ping" que o próprio RetroArch
registra no log **não acompanhou de forma confiável** o atraso que eu
configurei no proxy (por exemplo, o cenário de 200ms registrou "12ms" —
bem abaixo do esperado). Isso sugere que esse número é medido só no
início da conexão (antes do atraso completo do proxy valer), não durante a
partida inteira — então não posso afirmar "o RetroArch relatou X ms" como
prova confiável do atraso sentido. O que **é** uma prova real e boa: em
nenhum dos 5 cenários o RetroArch registrou aviso de travada/dessincronia/
timeout — a conexão se manteve estável até em 200ms + 5% de perda
simulada, no protocolo/handshake em si.

**O que o jogador sentiria de verdade** (conhecimento geral de como
netplay por atraso funciona — o RetroArch usa `netplay_input_latency_frames`,
não *rollback*; isto é explicação técnica, não algo medido nesta sessão):
com atraso baixo (50ms) o jogo responde quase normal; a partir de 100-200ms
o atraso entre apertar o botão e ver o efeito na tela fica perceptível,
mais em jogos de reação rápida (luta, corrida) que em jogos por turno.
Perda de pacote em netplay por atraso costuma aparecer como um soluço
(input trava por um instante) em vez de um corte definitivo. **Confirmar
como isso se sente na prática precisa de um aluno jogando de verdade** —
mesmo limite já reconhecido pelo próprio plano para testes de botão.

### 4. Cenários de sala de aula

Script `testes\teste_cenarios_sala.py`, com RetroArch real:

| Cenário | Resultado |
|---|---|
| Convidado cai e volta | **Funciona.** Conectou na 1ª vez, foi morto, reconectou na 2ª tentativa apontando pro mesmo host — 2 entradas registradas no log do host |
| Hospedeiro sai no meio | **Funciona bem.** O convidado registrou a queda no próprio log (desconexão detectada) e **não travou** — continuou respondendo, não precisou ser forçado a fechar |
| Convidado entra com a partida já começada | Já coberto pelo próprio mecanismo de conectar (não existe estado "partida começada" que bloqueie entrada tardia no RetroArch — quem entra depois só perde o que já aconteceu, como assistir um filme atrasado) |
| 6º jogador tentando entrar | Já respondido pelo achado da seção 1 — o limite prático encontrado (4 jogadores totais) é *menor* que 6, então um 6º nunca chegaria a ser a pergunta relevante até o achado da seção 1 ser resolvido/confirmado |
| Duas partidas diferentes na mesma rede | **Não dá pra testar direito num computador só.** `graficos.opcoes_de_partida()` grava a porta do netplay (`netplay_port`) como uma constante fixa (`PORTA_PARTIDA`, 55435) — não há como duas partidas terem portas diferentes *na configuração que o ARENA gera*. Isso não é um bug: em uma sala de aula de verdade, dois grupos hospedando em **computadores diferentes** usam a mesma porta 55435 sem conflito nenhum, porque cada host tem seu próprio endereço IP — só dá conflito de porta quando os dois hosts estão no MESMO computador, cenário que só existe em teste, não em sala de aula real. Tentar forçar isso num computador só (dando portas diferentes na linha de comando) expôs justamente essa limitação de teste, não do ARENA. **Vira item do roteiro manual**, com dois grupos em computadores de verdade. |

### 5. Descoberta de colegas com muitos aparelhos

Script `testes\teste_descoberta_30_maquinas.py`: 30 "computadores" falsos
anunciando ao mesmo tempo (mesmo formato de pacote UDP que
`anunciar_e_escutar()` espera).

| Medida | Resultado |
|---|---|
| Colegas vistos na lista | 30 de 30 |
| Tempo de resposta de `/api/colegas` | 0,018 s |
| CPU do servidor durante/depois da rajada | 0,0% |

Limpo — a lista aguenta 30 sem ficar lenta nem pesar no processador.

### 6. Sincronização e mala do pen drive

**Mesmo recorde vindo de duas vezes**: já coberto pela bateria de 44 testes
(`test_insert_or_ignore`) — `INSERT OR IGNORE` com `uuid` como chave, testado
e confirmado desde antes desta auditoria (reenviar o mesmo registro não
duplica).

**Pen drive em FAT32 (só guarda hora de 2 em 2 segundos)**: conferido no
código — `trocar_pela_mala()`/`ler_mala()` **não usam a data do arquivo no
disco (mtime) em lugar nenhum**. A ordem e o "até onde cada ARENA já
passou" vêm de um carimbo gravado *dentro* do JSON (`agora_utc()`, com
microssegundos), não do sistema de arquivos. Achado real, mas tranquilizador:
**a granularidade de 2 segundos do FAT32 não afeta a mala**, porque ela
nunca olha pra essa informação.

**Relógios diferentes entre os notebooks — achado real, sem correção
segura ainda.** Testado de verdade: um registro gravado com o relógio da
própria máquina **errado** (simulado: data de 2020 em vez de hoje) fica
**permanentemente invisível** para a sincronização incremental de outro
colega. Prova:

```
Registros encontrados desde as 09:00 de hoje: ['Ana']
O registro do relógio errado (Bruno, 2020) apareceu? False
```

Causa: `registros_desde()` usa `WHERE registrado_em > ?` — uma comparação
de texto contra o carimbo (`registrado_em`, o mesmo `agora_utc()` da
máquina que gravou). Se o relógio de uma máquina está preso no passado, os
registros dela sempre parecem "mais antigos que a última sincronização" —
mesmo sendo, na prática, registros novos que o colega nunca viu. O registro
continua existindo no banco *local* de quem tem o relógio errado (aparece
no ranking da própria máquina), só não viaja pros colegas.

**Por que não corrigi agora**: consertar isso de verdade significa trocar
o "carimbo de progresso" da sincronização de data/hora para outra coisa
(um contador por aparelho, por exemplo) — uma mudança de arquitetura no
formato que já roda em produção e no formato da mala do pen drive, não um
ajuste pontual. Risco alto de mexer sem testar direito com máquinas de
verdade. **Proposta, não aplicada**: um aviso na tela quando o ARENA abre,
se o relógio do Windows parecer muito errado (comparar contra uma data
mínima razoável, tipo "não pode ser antes de 2024"), pedindo pro aluno
acertar a hora antes de sincronizar — reduz o risco sem mexer na
arquitetura. Fica registrado como pendência de design, não como bug
"corrigido".

### 7. Diagnóstico nos notebooks da escola

Pesquisa de código (o que já existe) + pesquisa externa (faixas de
endereço reais, comportamento documentado do Windows), item por item do
plano:

| Item | Situação encontrada | O que foi feito nesta fase |
|---|---|---|
| **Firewall bloqueando entrada, rede pública, aluno sem admin** | Nada de detecção real — só um palpite no texto de erro ("...ou o firewall dele está bloqueando..."). Pesquisado (Microsoft Learn): o Firewall do Windows bloqueia entrada por padrão, e a caixa de permissão **pede senha de administrador** — um aluno comum não tem como aprovar sozinho. | **Corrigido.** `partida.py` ganhou `categoria_de_rede()` — confere via `Get-NetConnectionProfile` (só leitura, sem admin) se a rede está marcada "Pública", e nesse caso explica a causa de verdade e a saída (pedir pro professor trocar pra rede Privada). Testado nesta máquina: a rede aqui **é** Pública — achado real, na hora. |
| **Wi-Fi que isola os aparelhos entre si** | Nada — e não tem como detectar por software no cliente (o isolamento acontece no roteador). | Não dá pra corrigir; documentado como limite técnico honesto (como "tela dividida não separa" já documentado no CLAUDE.md). |
| **Ponto de acesso de Android e iPhone** | Android (`192.168.43.0/24`): coberto certo. iPhone (`172.20.10.0/28`, confirmado por pesquisa): **bug real** — a entrada `"172.2"` (faltando o "0.") casava por acidente com 172.20. até 172.29. inteiros e classificava hotspot de iPhone como "adaptador virtual, não serve pro colega". | **Corrigido** — ver Fase 4 no `CLAUDE.md`/commit. Testado com 8 endereços reais, incluindo o range exato do iPhone. |
| **Cabo direto sem roteador (169.254.x.x)** | Já coberto e testado desde antes desta auditoria. | Nada a fazer — checado, funciona. |
| **Adaptadores virtuais e VPN** | Adaptadores "clássicos" (VirtualBox, WSL, Hyper-V): cobertos, mas por **dois mecanismos diferentes e inconsistentes** — um por faixa de IP (usado pela descoberta de colegas) e outro por nome do adaptador (usado só pelo PCSX2/PS2). VPN: **não coberto de forma confiável** — WireGuard, Tailscale e a maioria dos clientes de VPN não aparecem na lista por nome, e o Tailscale usa uma faixa (`100.64.0.0/10`) que cai em "Outra rede" sem aviso nenhum. Achado extra ao vivo: o WSL2 desta máquina usa uma faixa `192.168.x.x` **dinâmica** (não é uma das fixas já excluídas), então nem o mecanismo por IP pega isso de forma confiável. | **Não corrigido agora** — resolver isso direito exigiria trocar `enderecos_locais()` de "só pergunta o IP ao socket" para "pergunta o IP E o nome do adaptador ao Windows", um mecanismo mais lento e mais arriscado de testar sem quebrar o caminho rápido que já existe (documentado como razão de ser da função atual). Fica como pendência de design, não decidida sozinha. |
| **Endereço muda, notebook dorme e acorda, Wi-Fi cai no meio** | Nada de proativo — o cache de 30s de `enderecos_locais()` pega o endereço novo na próxima consulta, mas nada AVISA o aluno que mudou. Uma queda de Wi-Fi durante a partida é responsabilidade inteira do RetroArch. | Documentado como limite; a `cache_directory`/`enderecos_locais()` já pega o valor novo sozinho na próxima vez que a tela perguntar — não trava em endereço velho, só não avisa proativamente. |

### Aplicação e testes (Fase 4)

Bateria de 44 testes: OK, 0 falhas, depois de cada mudança em `arena.py`,
`graficos.py`, `indexador.py`, `partida.py`, `consoles.json` e `app.js`.

Scripts novos: `testes\teste_netplay_5_jogadores.py`,
`testes\teste_netplay_isolamento.py`, `testes\teste_local_4_jogadores.py`,
`testes\proxy_rede_ruim.py`, `testes\teste_rede_ruim.py`,
`testes\teste_cenarios_sala.py`, `testes\teste_descoberta_30_maquinas.py`.

---

## Roteiro manual — Fase 4 (5 notebooks de verdade, sala de aula)

Isto é o que só dá pra confirmar com máquinas físicas de verdade. Leve
este roteiro pra sala, com 5 notebooks (ou o máximo que der — quanto mais
perto de 5, melhor).

### O que separar antes

- 5 notebooks com o ARENA (mesma versão, pasta `ARENA-unificado` copiada
  igual nos 5, ou pen drives idênticos).
- O jogo `Super Bomberman 4 (Japan) [T-En by Svambo v1.0].sfc` nos 5,
  na pasta `jogos\pessoais\Super Nintendo\`.
- `GoldenEye 007 (USA).z64` em pelo menos 1 notebook (pra teste local),
  na pasta `jogos\pessoais\Nintendo 64\`.
- 4 controles USB/Bluetooth (pro teste local de 4 jogadores) — ou
  controle + teclado, sabendo que só PS2/Dreamcast/MSX/ScummVM aceitam
  esse mix (não o N64 do GoldenEye).
- Anotar em cada notebook: nome da rede Wi-Fi que vai usar, se é a rede da
  escola, ponto de acesso de celular, ou cabo direto.

### Roteiro 1 — Super Bomberman, 5 jogadores (o achado da seção 1)

**Isto é o teste mais importante desta fase** — resolve a dúvida que a
auditoria não conseguiu fechar sozinha.

1. Notebook 1: liga "Aceitar conexões da rede", abre Super Bomberman 4,
   clica "Eu abro a partida" (Multitap deve ligar sozinho — o jogo está
   na lista curada).
2. Notebooks 2, 3 e 4: cada um entra como jogador 2, 3 e 4 (nessa ordem,
   um de cada vez, esperando a tela confirmar antes do próximo). **Anote**
   se os 3 conseguem entrar.
3. Notebook 5: entra como jogador 5. **Este é o teste**: anote se conecta
   ou se recusa (e qual mensagem aparece). Se conectar aqui — em 5
   máquinas físicas de verdade — significa que o problema encontrado
   nesta auditoria era mesmo um artefato de testar tudo em `127.0.0.1`, e
   o Multitap funciona pros 5 jogadores de verdade. Se recusar do mesmo
   jeito, é um limite real do RetroArch, e o ARENA vai documentar "até 4
   jogadores confirmados" pro Multitap.
4. Se os 5 conectarem: joguem uma rodada de verdade. Anote se os 5
   personagens aparecem na arena, se os controles de cada um respondem
   certo (jogador 3 no controle do notebook 3, não trocado).

### Roteiro 2 — GoldenEye, 4 jogadores no mesmo computador

1. Num notebook só, pluga os 4 controles (ou 3 controles + teclado, se
   quiser testar esse caminho também, mesmo sabendo que oficialmente não é
   suportado pro N64 — vale testar mesmo assim e anotar o que acontece).
2. Ajustes → Avançado → "Quantos jogadores" → 4.
3. Abre GoldenEye 007. Confirma que os 4 controles mexem o personagem
   certo (jogador 1 no primeiro controle plugado, e assim por diante).
4. Anote se algum controle ficou mudo ou trocado.

### Roteiro 3 — Duas partidas ao mesmo tempo, dois grupos

1. Separe os 5 notebooks em 2 grupos (ex.: 3 + 2).
2. Grupo A hospeda uma partida (qualquer jogo de 2). Grupo B hospeda
   OUTRA partida, ao mesmo tempo, na mesma rede Wi-Fi.
3. Confirme que cada grupo só vê e alcança o jogo do seu próprio grupo —
   nenhum jogador do grupo A aparece achando que está jogando com o grupo B.

### Roteiro 4 — Situações de queda

1. Durante uma partida de 2, force o fechamento do RetroArch de quem
   hospeda (Gerenciador de Tarefas). Anote a mensagem que aparece pro
   convidado.
2. Durante uma partida, force o fechamento do convidado. No host, tente
   deixar outro notebook entrar no lugar dele. Anote se funciona e como.
3. Desligue o Wi-Fi de um notebook por 5 segundos, no meio de uma partida,
   e ligue de novo. Anote se reconecta sozinho ou precisa reabrir tudo.

### Roteiro 5 — Rede real da escola

1. Rode `PARTIDA.bat` em cada notebook, na rede real da escola. Anote:
   - A categoria da rede (Pública/Privada) que aparece agora — nova
     checagem desta fase.
   - Se algum endereço aparece marcado "adaptador virtual" que na verdade
     deveria servir (ex.: alguma VPN de antivírus da escola).
2. Se algum notebook usa ponto de acesso de celular (Android ou iPhone),
   confirme que o endereço aparece corretamente como "Rede local" agora
   (era o bug do iPhone corrigido nesta fase).
3. Se possível, teste também um cabo de rede direto entre dois notebooks
   (sem roteador) — já era um caso resolvido, só confirma que continua.

Anote tudo — mesmo o que já era esperado — porque é isso que fecha, de
verdade, o que só a sala de aula pode confirmar.

*(a preencher ao final da auditoria)*
