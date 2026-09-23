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
- **Não encontrada em `fetch(...)` na busca automática** (pode estar em uso
  como `<img src="/api/capa?...">`, que a busca por `fetch(` não pega —
  precisa conferir na Fase 1, não presumir que é morta): `/api/capa`,
  `/api/jogo/impressao`.

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
segundo plano de capa/jogo (`arena.py:3517`, `4048`), transferência de
arquivo (`transferencia.py:59`, usada pela mala do pen drive).

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

## Depois (Fase 8)

*(a preencher ao final da auditoria)*
