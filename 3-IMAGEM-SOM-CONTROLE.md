# 3 — Imagem, som e controle

Tudo o que muda como o jogo se vê, se ouve e responde ao seu comando.

**Neste documento:**

- Parte A — Teclado e controles
- Parte B — Imagem e som
- Parte C — Ajuste fino por console

---

## Parte A — Teclado e controles

Qualquer controle serve: Xbox, PlayStation, Switch, arcade stick ou genérico.
E o teclado sempre funciona, mesmo com controle plugado.

---

### Regra número um

**Plugue o controle antes de abrir o jogo.** Quase todos são reconhecidos
sozinhos.

### O que funciona

| Controle | Como |
|---|---|
| **Xbox 360, One, Series** | Plugou, funcionou |
| **PlayStation 4 e 5** | Por cabo USB funciona direto. Por Bluetooth, pareie antes |
| **PlayStation 3** | Precisa do driver SCP ou DsHidMini no Windows |
| **Switch Pro** | Por cabo funciona. Por Bluetooth, pareie antes |
| **Joy-Con avulso** | Funciona, mas mapeie os botões na mão |
| **Steam Controller** | Deixe o Steam aberto — ele converte sozinho |
| **Arcade stick** | Quase todos funcionam. Se não, troque para `dinput` |
| **Genéricos** | Quase todos funcionam. Se não, troque para `dinput` |
| **Teclado** | Sempre funciona como jogador 1, mesmo com controle plugado |

### Se o controle não aparecer

**Ajustes → Controles → Tipo de controle.** Duas opções:

| Tipo | Cobre |
|---|---|
| **xinput** (padrão) | Xbox, PS4, PS5, Switch Pro e a maioria dos modernos |
| **dinput** | PS3, arcade stick, genéricos antigos |

Troque, feche o ARENA, abra de novo e teste.

### Mapear as teclas e os botões pelo ARENA

Não precisa mais entrar no menu do RetroArch para configurar o controle. Em
**Ajustes → Controles**, o ARENA faz isso com os nomes do seu console.

#### Primeiro: diga qual controle você tem

Em **Ajustes → Controles**, no topo, tem **Qual controle você tem**. Escolha
o seu na lista:

| Controle | Botões | Analógicos | Vibra | Paletas |
|---|---|---|---|---|
| Xbox 360 | 11 | 2 | sim | — |
| Xbox One, Series S e X | 11 | 2 | sim | — |
| **Xbox Elite** | 11 | 2 | sim | **4 (L4, R4, L5, R5)** |
| PlayStation 3, 4 e 5 | 11 | 2 | sim | — |
| Switch Pro | 11 | 2 | sim | — |
| Joy-Con avulso | 8 | 1 | sim | — |
| Steam Controller | 11 | 2 | sim | 2 |
| Genérico com 12 botões | 11 | 2 | não | — |
| Genérico com 10 botões | 9 | 0 | não | — |
| Arcade stick | 8 | 0 | não | — |
| Teclado | — | — | — | — |

O ARENA passa a mostrar **os nomes do seu controle**. No Xbox aparece "A";
no DualShock, "X". É o mesmo botão, com o nome que está escrito nele.

#### Depois: para qual console

Aqui está o pulo do gato. O ARENA cruza as duas coisas e mostra **só o que
existe dos dois lados**:

| Seu controle | No console | O que aparece |
|---|---|---|
| Xbox 360 | NES | 8 botões, sem analógico, sem vibração |
| Xbox 360 | Nintendo 64 | 12 botões, **1 analógico**, vibração (Rumble Pak) |
| Xbox 360 | PlayStation 2 | 16 botões, 2 analógicos, vibração |
| **Arcade stick** | PlayStation 2 | 16 botões, **nenhum analógico** |
| **Joy-Con** | PlayStation 2 | **1 analógico só** |

Não adianta oferecer analógico direito num jogo de NES, nem prometer
vibração num arcade stick. A chave que não serve fica apagada e não clica.

#### As quatro chaves

| Chave | O que faz |
|---|---|
| **Direcional** | Liga e desliga a cruz |
| **Analógico esquerdo** | Anda, junto com o direcional |
| **Analógico direito** | Câmera e mira, quando o jogo usa |
| **Vibração** | Só nos consoles que tinham |

**Desligar o analógico esquerdo muda o console de verdade.** No PlayStation,
o ARENA passa a dizer ao emulador que o controle é o de 1994, sem analógico
— que é como alguns jogos antigos esperam encontrar.

#### Mouse e teclado do computador

Alguns consoles aceitavam mouse e teclado de verdade. Nesses, aparece
**Jogador 2 usa**, com três opções: controle, mouse ou teclado.

| Console | Aceita |
|---|---|
| PlayStation 2 | mouse e teclado |
| Dreamcast | mouse e teclado |
| Super Nintendo | mouse (era o de Mario Paint) |
| Nintendo DS | mouse (vira a caneta da tela de baixo) |
| MSX, Commodore 64, Amiga, MS-DOS | mouse e teclado |
| ScummVM | mouse e teclado |

#### O jeito rápido: mapear sozinho

Plugou o controle e quer jogar agora? Clique em **Mapear meu controle
sozinho**. Ele preenche os 16 botões de uma vez, na numeração que Xbox,
PlayStation 4 e 5, Switch Pro, Steam Controller e a maioria dos genéricos
usam.

Se algum sair trocado, refaça só aquele em **Definir**. O resto fica.

Para o teclado, o botão ao lado é **Padrão do teclado**.

E dá para misturar: **jogador 1 no controle, jogador 2 no teclado**, ao
mesmo tempo. É só escolher o jogador antes de clicar.

#### O direcional é diferente dos outros botões

O **Mapear meu controle sozinho** preenche os botões mas **não toca no
direcional**, de propósito.

Motivo: o direcional do Xbox e da maioria dos controles modernos não é um
botão comum. É um "chapéu" — um controle de quatro posições que o driver
reporta de outro jeito. Qualquer número que o ARENA escrevesse ali teria
boa chance de estar errado, e o direcional ficaria mudo.

**O RetroArch já reconhece o direcional sozinho, e acerta.** O ARENA não
tem o que melhorar ali — só o que estragar. Então deixa.

Se ainda assim você quiser definir na mão: clique em **Definir** na linha do
direcional e aperte a direção no controle. O ARENA grava no formato certo.

#### Analógico e direcional funcionam juntos

Você não precisa escolher entre um e outro. Os dois funcionam ao mesmo
tempo, em todos os controles:

| | O que faz |
|---|---|
| **Direcional** | Anda |
| **Analógico esquerdo** | Anda também |
| **Analógico direito** | Fica livre para o jogo — câmera, mira |

#### Por que o analógico não funcionava antes

O console não adivinha qual controle está plugado. O PlayStation 1 saiu de
fábrica com um controle **sem analógico** — o DualShock veio depois. O
emulador começava imitando o controle antigo, e os dois analógicos ficavam
mudos por mais que o seu controle estivesse certo.

O ARENA agora avisa o console de que o controle tem analógico. Vale para
PlayStation 1 e 2, Dreamcast, Saturn, Nintendo 64 e GameCube.

Em *Ajustes → Avançado → Controle* dá para desligar, se você quiser.

#### Vibração

Ligada por padrão, na força máxima. Em *Ajustes → Avançado → Controle →
Força da vibração* dá para baixar ou desligar.

Funciona em Xbox, PS4, PS5 e Switch Pro por cabo. Em genérico depende do
modelo — se o seu não vibra, não é o ARENA.

#### Mapear de dentro do jogo

Não precisa fechar para arrumar um botão. No jogo: **`Esc` → Controles**.

Ali dá para mexer no jogador 1 e no jogador 2, e o que você mudar vale só
naquele jogo. Para mudar em todos, use a tela do ARENA.

#### Passo a passo pelo ARENA

1. Escolha o **console** — muda só os nomes mostrados. Se você escolher
   PlayStation 2, a lista fala em X, Círculo, Quadrado e Triângulo.
2. Escolha o **jogador**: 1 ou 2. Cada um tem o seu mapeamento.
3. Clique em **Definir** na linha do botão que você quer.
4. **Aperte a tecla no teclado, ou o botão no controle.** O ARENA reconhece
   sozinho qual dos dois foi.
5. Pronto. Vale no próximo jogo que você abrir.

Para desistir no meio, aperte `Esc` ou clique em **Cancelar**.

#### Os dois atalhos

| Botão | O que faz |
|---|---|
| **Usar o padrão do teclado** | Preenche os 12 botões com o mapeamento de fábrica. Bom ponto de partida |
| **Limpar tudo** | Apaga o mapeamento daquele jogador |

#### Uma coisa importante

**O ARENA só grava o que você definir aqui.** Botão que você não mexeu nem
aparece no arquivo — e o que o RetroArch já sabia continua valendo.

Por isso *Limpar tudo* não deixa você sem controle: devolve aqueles botões
para o RetroArch decidir.

#### O que dá para atribuir

| Tipo | Exemplo | Quando |
|---|---|---|
| Tecla do teclado | `x`, `enter`, `space` | Jogando no teclado |
| Botão do controle | botão 0 a 31 | Controle plugado |
| Eixo do analógico | `-0`, `+1` | Direcional analógico |

O ARENA recusa o que o RetroArch não entende, e diz o motivo na hora.

#### Onde fica guardado

Em `dados\controles.json`. Entra no pacote de progresso e nas cópias de
segurança, então **configurou uma vez, vale em qualquer computador** para
onde você levar a pasta.

---

### Que botão é qual, em cada console

O RetroArch fala em "botão A" e "botão B" — que são os nomes do Super
Nintendo. Na hora de configurar um controle para PlayStation 2, isso não
ajuda em nada.

Em **Ajustes → Controles**, escolha seu console e a tabela mostra o nome de
verdade:

| No PlayStation | Aparece como |
|---|---|
| X | Botão B |
| Círculo | Botão A |
| Quadrado | Botão Y |
| Triângulo | Botão X |
| L1 / R1 | Botão L / R |
| L2 / R2 | Botão L2 / R2 |

Tem tabela para 14 consoles. No Nintendo 64, por exemplo, o botão A do
controle aparece como "botão B" — trocado mesmo.

---

### Se os botões estiverem trocados

No jogo:

1. **Esc**
2. **Configurações → Entrada → Controles da Porta 1**
3. **Definir Todos os Controles**
4. Aperte cada botão quando a tela pedir. Botão que você não tem: espere,
   passa sozinho.

Faça uma vez por modelo de controle. **Fica salvo para sempre**, inclusive
quando você levar a pasta para outro computador.

### Teclado

| Tecla | Botão |
|---|---|
| Setas | Direcional |
| `Z` e `X` | Botões principais |
| `A` e `S` | Botões secundários |
| `Enter` | Start |
| `Shift` direito | Select |

### Dois controles na mesma máquina

Plugue os dois antes de abrir o jogo. Em **Ajustes → Avançado → Controle →
Quantos jogadores**, deixe em 2 ou mais.

Isso é diferente de jogar pela rede: aqui são duas pessoas no mesmo
computador, dividindo a tela.

### Abrir o menu sem teclado

Aperte **Start + Select juntos**. Dá para trocar a combinação em *Ajustes →
Avançado → Controle → Abrir menu pelo controle*.

---

### Onde ficam as configurações de controle

| O quê | Onde |
|---|---|
| Perfil de cada controle | `retroarch\controles\` |
| Botões trocados por jogo | `retroarch\remaps\` |
| Tipo de controle escolhido | `dados\config.json` |

Tudo dentro da pasta do ARENA. Copiou a pasta, levou a configuração junto.

---

### Onde as configurações de controle ficam

| O quê | Onde |
|---|---|
| Perfil de cada controle | `retroarch\controles\` |
| Botões trocados por jogo | `retroarch\remaps\` |
| Tipo de controle escolhido | `dados\config.json` |

Tudo dentro da pasta do ARENA. Copiou a pasta, levou a configuração junto.

---

### Problemas

| O que aconteceu | O que fazer |
|---|---|
| O controle não aparece | Troque o tipo em Ajustes → Controles e reabra o ARENA |
| Os botões estão trocados | Refaça o mapeamento pelo menu do jogo (acima) |
| O analógico anda sozinho | Ajustes → Avançado → Folga do analógico para 0.2 |
| O analógico não chega ao máximo | Ajustes → Avançado → Sensibilidade para 1.2 |
| Só um controle funciona | Ajustes → Avançado → Quantos jogadores para 2 |
| Não consigo abrir o menu sem teclado | Aperte Start + Select juntos |
| Funciona no meu PC mas não no do colega | Cada máquina reconhece na primeira vez. Plugue e reabra o ARENA lá |

Ajuste fino de resposta do controle: **documento 6**, grupo *Resposta do
controle*.


---

## Parte B — Imagem e som

Como deixar o jogo fluido, bonito e com o controle respondendo rápido.

---

### Caminho rápido

**Não faça nada.** O padrão é **Automático**, e ele acerta na maioria dos
casos.

O ARENA mede seu computador na abertura — processador, memória, motor
gráfico e velocidade de escrita do disco — e dá uma nota de 1 a 5. Depois
compara essa nota com o peso de cada console e escolhe a configuração para
cada um separadamente.

Na prática: seu Super Nintendo abre com filtros e imagem caprichada, e seu
PlayStation 2 abre no modo mais leve possível. **Na mesma máquina, no mesmo
dia, sem você mexer em nada.**

### Como o ARENA mede seu computador

Em **Ajustes → Máquina** você vê tudo o que ele encontrou: processador,
núcleos, memória total e livre, disco, espaço livre, velocidade de gravação,
sistema e se há internet.

A velocidade do disco é **medida**, não perguntada ao Windows. Descobrir se
um disco é SSD ou HD exigiria senha de administrador; medir a gravação real
não exige nada e diz o que importa.

Ele grava 8 MB, cronometra, e repete até três vezes ficando com a melhor
amostra. As piores são descartadas porque quase sempre são o antivírus ou
outro programa mexendo no disco ao mesmo tempo.

Aparece também a **confirmação em milissegundos**, separada da velocidade.
Confirmação alta com velocidade alta é normal: é o disco avisando que
gravou, não lentidão.

---

### Se o jogo ficar avançando um quadro por vez

Sintoma: o jogo carrega, sai do menu inicial, e daí em diante só anda quando
você aperta `Alt` + `Tab`. Um quadro por vez.

**Não é defeito do emulador nem da máquina.** É uma opção chamada *Pausar
quando sair da janela*: o emulador pausa sempre que acha que a janela dele
não está na frente. Em vários computadores de escola ele nunca acha que
está, porque o navegador do ARENA continua com o foco.

O ARENA agora deixa isso **desligado** por padrão, e o problema não acontece
mais. Se por algum motivo voltar: *Ajustes → Avançado → Sistema → Pausar
quando sair da janela*, e deixe desligado.

---

### Modo desempenho

Em **Ajustes → Máquina → Dar prioridade ao jogo**.

Enquanto o jogo roda, o Windows dá preferência a ele. O ARENA e o navegador
ficam em segundo plano até você fechar. **Não fecha nada de ninguém** — só
muda quem tem preferência na fila do processador.

Recomendado em computador modesto. Para ajudar ainda mais, antes de jogar
feche as abas do navegador que não estiver usando, e o Teams ou o OneDrive
se estiverem abertos.

---

### Ultra desempenho

Um degrau acima do modo desempenho. Em **Ajustes → Máquina → Ultra
desempenho**.

**O que ele faz, e cada item é real:**

- o emulador sobe para prioridade alta e o ARENA cai para a mais baixa;
- o ARENA **para de vigiar a rede** enquanto você joga — nenhuma tarefa de
  fundo disputando o processador;
- a placa de som passa a ser do jogo, sem o misturador do Windows no meio;
- tela cheia de verdade, não janela sem borda;
- filtros e efeitos saem de cena.

**Travar o `Alt`+`Tab` é uma chave separada**, logo abaixo. Ela prende o
teclado no jogo — mas prende o `Esc` junto, então **o menu para de abrir**
enquanto estiver ligada.

Para soltar sem fechar o jogo: **`F9`**. Aperte uma vez e o `Esc` volta a
funcionar; aperte de novo para travar outra vez.

Ela vem **desligada**. Antes ela vinha junto com o ultra desempenho, e o
aluno ficava sem menu sem entender por quê — eram duas decisões diferentes
num botão só.
- filtros, voltar no tempo e resposta instantânea saem de cena.

**O que ele não faz**, e não adianta prometer:

- **não desliga o Windows nem impede o `Ctrl`+`Alt`+`Del`.** Isso exigiria
  senha de administrador e um driver próprio — o aluno não tem essa senha
  na máquina da escola;
- **não fecha programa de ninguém.** Se o Teams estiver aberto, continua
  aberto: só perde a vez na fila do processador.

Para sair: **`F10`**, que fecha o jogo. Aí tudo volta ao normal sozinho.

---

### Se um jogo fechar sozinho

O ARENA anota. Em **Ajustes → Máquina → Jogos que fecharam sozinhos** fica o
registro: qual jogo, qual emulador, que código de saída e quando.

Serve para descobrir o padrão. Se é sempre o mesmo jogo, é aquele arquivo.
Se é sempre o mesmo emulador, é o núcleo. Se é em qualquer jogo depois de
muito tempo, costuma ser memória.

O que fazer, na ordem:

| Ordem | O que tentar |
|---|---|
| 1 | Ligue o **modo desempenho** e feche o que não estiver usando |
| 2 | Desça para **Desempenho** em Ajustes → Simples |
| 3 | Desligue **Voltar no tempo**, que come memória o tempo todo |
| 4 | Se for sempre o mesmo jogo, o arquivo pode estar incompleto |
| 5 | Rode o **VERIFICAR.bat** |

---

### Modo econômico

Em máquina modesta, em cartão SD ou rodando de pen drive, o ARENA entra
sozinho em modo econômico. Você vê isso na janela preta ao abrir.

O que muda:

| | Normal | Econômico |
|---|---|---|
| Checa a rede a cada | 20 s | 60 s |
| Cópia de segurança | a cada jogo fechado | a cada 15 min |
| Lista de jogos em memória | 4 s | 15 s |
| Conexões em espera | 128 | 48 |

Nada some. O ARENA só conversa menos com o disco e com a rede — que é
exatamente o que trava um Celeron de dois núcleos e desgasta um cartão SD.

### Partida a dois pesa o dobro

Jogar junto custa muito mais que jogar sozinho: o emulador roda o jogo,
guarda o estado para poder voltar quando a rede atrasa, e às vezes
reprocessa quadros já passados.

Por isso o ARENA **alivia sozinho durante a partida**: desliga filtros de
tela, suavização, voltar no tempo e resposta instantânea, e sobe o vídeo em
paralelo. Vale só enquanto a partida dura; jogando sozinho tudo volta.

Se mesmo assim ficar abaixo de 30 quadros num jogo de dois jogadores, é o
limite da máquina — e o ARENA já está no mínimo.

---

### O selo de cada jogo

Cada jogo na lista mostra como vai rodar aqui:

| Selo | O que esperar | Perfil que o ARENA usa |
|---|---|---|
| **Bonito e lisinho** (verde) | Sobra máquina | Qualidade |
| **Feio mas lisinho** (azul) | Roda liso, imagem simples | Desempenho |
| **Capenga** (vermelho) | Vai travar | Desempenho |

Vermelho não impede de tentar. Só avisa antes, para você não achar que
quebrou.

### Escolher na mão

**Ajustes → Simples.** Se quiser mandar você mesmo:

| Nível | Para quem |
|---|---|
| **Automático** | O padrão. Escolhe por jogo |
| **Desempenho** | Força o modo leve em tudo |
| **Equilibrado** | Meio-termo em tudo |
| **Qualidade** | Força a melhor imagem em tudo |

**Regra: se travar ou o som picotar, desça um nível.** A mudança vale no
próximo jogo aberto.

O resto deste documento é para quem quer ajustar fino.

---

### O motor gráfico

Está em **Ajustes → Avançado → Imagem → Motor gráfico**.

| Opção | Quando usar |
|---|---|
| **Automático** | Deixe assim. O ARENA testa e escolhe o melhor da máquina |
| **vulkan** | O mais rápido e com menor atraso, quando a placa aceita |
| **d3d11** | Ótimo no Windows quando não há Vulkan |
| **glcore** | Rede de segurança. Funciona em quase tudo |

Só esses três são oferecidos. Os motores antigos foram tirados de propósito:
são mais lentos e não fazem nada que estes três não façam melhor.

#### Como saber se sua máquina tem Vulkan

A barra do topo do ARENA mostra, em **Motor**, o que está sendo usado. Se
aparecer `vulkan`, sua máquina tem.

Placas Intel HD anteriores a 2015 — caso de vários notebooks escolares mais
antigos — **não têm Vulkan**. Nessas máquinas o ARENA usa d3d11 ou glcore
sozinho, e está certo.

#### Se você forçar Vulkan numa máquina sem Vulkan

O jogo abre e fecha na hora, sem mensagem nenhuma. É o sintoma clássico.
Volte o motor para **Automático**.

---

### Vulkan bem configurado

Quando o motor é Vulkan ou D3D11, quem controla o atraso é a **Fila de
imagens** (`Ajustes → Avançado → Imagem`), não as opções de OpenGL.

| Fila | Efeito |
|---|---|
| **2** | Responde mais rápido. Use quando a máquina dá conta |
| **3** | Engasga menos. Use em máquina fraca |

O ARENA já ajusta isso sozinho conforme o nível escolhido: Desempenho usa 3,
os outros usam 2.

**Esta é a diferença que faz Vulkan valer a pena.** Trocar o motor sem
trocar a fila junto é o motivo clássico de "mudei para Vulkan e ficou pior".
O ARENA muda os dois de uma vez.

#### Comparação dos três níveis com Vulkan

| Opção | Desempenho | Equilibrado | Qualidade |
|---|---|---|---|
| Fila de imagens | 3 | 2 | 2 |
| Vídeo em segundo plano | ligado | ligado | desligado |
| Atraso de quadro automático | desligado | ligado | ligado |
| Filtros de tela | desligado | desligado | ligado |
| Suavizar imagem | desligado | ligado | ligado |
| Atraso do som | 96 ms | 64 ms | 32 ms |
| Som exclusivo | não | não | sim |
| Menu | leve | completo | completo |

---

### Imagem: o que cada opção faz

| Opção | Ligado | Desligado |
|---|---|---|
| **Suavizar imagem** | Borra um pouco, disfarça o pixel | Pixel quadrado e nítido |
| **Escala inteira** | Todo pixel do mesmo tamanho | Preenche mais a tela, alguns pixels ficam maiores |
| **Filtros de tela** | Efeito de TV antiga. **Pesa muito** | Imagem limpa e rápida |
| **Sincronizar com o monitor** | Sem imagem cortada ao meio | Responde um pouco mais rápido, mas corta |
| **Vídeo em segundo plano** | Ajuda muito em PC fraco | Menos atraso no controle |
| **Atraso de quadro automático** | O RetroArch mede e reduz sozinho | Você controla no manual |

**Para pixel art nítida:** Suavizar desligado + Escala inteira ligada.

**Para PC fraco:** Vídeo em segundo plano ligado + Filtros desligados.

---

### Som

| Opção | O que faz |
|---|---|
| **Motor de audio** | `wasapi` é o caminho mais curto até a placa de som. Deixe assim |
| **Som exclusivo** | Menor atraso, mas o jogo toma a placa de som só para ele. Nada mais toca enquanto joga |
| **Atraso do som** | Menor responde mais rápido, maior evita chiado |
| **Volume** | 0 é o volume original do console |

#### Escolher o atraso do som

| Situação | Valor |
|---|---|
| Som picotando ou com falhas | 96 ou 128 |
| Normal | 64 |
| Quer resposta rápida e o PC aguenta | 32 |
| Só com som exclusivo ligado e PC forte | 16 |

Se você baixar demais, o som começa a estalar. É o sinal de que passou do
ponto: suba um nível.

---

### Controle

Conecte **antes** de abrir o jogo. Na maioria dos casos é reconhecido
sozinho.

#### Se não responder

1. Abra o menu com `Esc`.
2. **Configurações → Entrada → Controles da Porta 1**.
3. **Definir Todos os Controles**.
4. Aperte cada botão quando a tela pedir. Botão que você não tem: espere,
   passa sozinho.

O RetroArch grava por modelo de controle. Faça uma vez por controle
diferente.

#### Opções de controle

| Opção | O que faz |
|---|---|
| **Leitura do controle** | `2` (tardia) dá o menor atraso. É o padrão do ARENA |
| **Quantos jogadores** | Quantos controles o jogo aceita ao mesmo tempo |
| **Abrir menu pelo controle** | `2` abre o menu com Start e Select juntos |
| **Velocidade do turbo** | Menor = dispara mais rápido |

#### Dois jogadores

Conecte os dois controles antes de abrir o jogo e confira que **Quantos
jogadores** está em 2 ou mais.

O teclado sempre funciona como jogador 1, mesmo com controle conectado:
setas movem, `Z` e `X` são os botões, `Enter` é Start, `Shift` direito é
Select.

---

### Teclas durante o jogo

| Tecla | O que faz |
|---|---|
| `Esc` | **Menu do jogo**: save states, cheats, configurações |
| `F2` / `F4` | Grava / volta o save state |
| `F6` / `F7` | Troca entre os 10 espaços de save |
| `F8` | Foto da tela |
| `F` | Alterna tela cheia e janela |
| `P` | Pausa |
| `F10` | Fecha o jogo e volta ao ARENA |

Save states e cheats estão no **documento 4**.

---

### Resolver problemas

Mexa numa coisa por vez e teste. Se mudar cinco de uma vez, você nunca vai
saber qual resolveu.

| Problema | O que fazer, na ordem |
|---|---|
| **Jogo travando** | 1. Desça para Desempenho · 2. Ligue Vídeo em segundo plano · 3. Desligue Filtros de tela · 4. Fila de imagens para 3 |
| **Som picotando** | 1. Atraso do som para 96 · 2. Desligue Som exclusivo · 3. Se persistir, 128 |
| **Controle demorando** | 1. Suba para Qualidade · 2. Desligue Vídeo em segundo plano · 3. Atraso do som para 32 · 4. Fila de imagens para 2 |
| **Imagem borrada** | Desligue Suavizar imagem, ligue Escala inteira |
| **Imagem cortando ao meio** | Ligue Sincronizar com o monitor |
| **Imagem esticada** | Ligue Escala inteira |
| **Abre e fecha na hora** | Motor gráfico para Automático. Se persistir, falta arquivo de sistema (documento 2) |
| **Bagunçou tudo** | **Voltar tudo ao padrão**, no fim da aba Avançado |

---

### Rodando do pen drive

Use o nível **Desempenho**. Não é por causa da velocidade do pen drive —
depois que o jogo carrega, ele roda da memória. É porque a máquina onde o
pen drive é usado costuma ser a mais fraca.

O que o nível Desempenho já desliga sozinho: menu pesado, fontes na tela,
salvamento automático de estado, verificação de arquivos na abertura. Tudo
isso são gravações e leituras que o pen drive faria à toa.

**Feche o ARENA pela janela preta antes de retirar o pen drive.** Ela mostra
"Pode retirar o pen drive com segurança" quando terminou de gravar. Retirar
antes disso pode corromper o banco de recordes.

---

### O que fica guardado

Tudo o que você ajustar fica, e viaja junto com a pasta:

| O que você mexeu | Onde fica guardado |
|---|---|
| Nível de qualidade, motor gráfico, som | `dados\config.json` |
| Mapeamento de teclado e de controle | `retroarch\retroarch.cfg` |
| Botões trocados por jogo | `retroarch\remaps\` |
| Perfil de cada controle conectado | `retroarch\controles\` |

Configurou o controle uma vez, está configurado para sempre — inclusive em
outro computador, porque a pasta vai junto.

O ARENA reescreve, a cada abertura, apenas as opções que **ele** gerencia:
caminhos das pastas e o perfil de desempenho. O resto é seu e não é tocado.

### As bibliotecas gráficas, sem instalar nada

Os emuladores precisam do Visual C++ Runtime da Microsoft. Sem ele, o
RetroArch nem abre, e o Windows mostra um erro que não explica nada.

Instalar o pacote oficial exige senha de administrador, que o aluno não tem
no computador da escola. Mas existe um caminho que não exige nada:

**Ajustes → Máquina → Copiar para a pasta do ARENA.**

O Windows procura essas bibliotecas primeiro **na pasta do programa**, antes
de procurar no sistema. Copiando para dentro da pasta do RetroArch, ele
passa a usar essas. Sem instalador, sem senha, e a cópia viaja junto no pen
drive.

Se o computador atual também não tiver as bibliotecas, faça a cópia num que
tenha: a pasta leva tudo junto.


---

## Parte C — Ajuste fino por console

O ARENA já acerta sozinho quando abre. Este documento é para quem quer
entender e mexer.

---

### Como o ARENA decide

Quando você abre o ARENA, ele:

1. Vê seu processador, sua memória e sua placa de vídeo.
2. Mede a velocidade de escrita do disco onde ele está rodando.
3. Dá uma nota de **1 a 5** para o seu computador.
4. Escolhe os ajustes de cada emulador de acordo com essa nota.

A nota aparece em **Ajustes → Máquina → Capacidade**.

#### Duas notas, não uma

O ARENA dá **duas** notas, e isso importa:

| Nota | Baseada em | Manda em |
|---|---|---|
| **Geral** | Processador, memória, disco | Quais consoles aparecem |
| **Da placa** | A placa de vídeo | Resolução, filtros, anti-serrilhado |

**Placa integrada nunca passa de 3**, por melhor que seja o processador.

Isso existe porque um Ryzen 5 5600G tem 12 núcleos e 11,8 GB — nota 4
tranquila — mas a placa dele é uma Radeon Vega integrada, que divide a
memória com o sistema. Sem essa separação, o ARENA ligava PSP em 1920×1088
com filtro 16x numa placa que não dá conta, e o resultado era jogo travando
e som picotando.

| Nota | Como é |
|---|---|
| 1 | Muito modesta |
| 2 | Modesta |
| 3 | Boa |
| 4 | Forte |
| 5 | Muito forte |

---

### O que muda em cada nota

Exemplo com PlayStation:

| Nota | Resolução interna | Filtro de textura |
|---|---|---|
| 1 e 2 | Original (1x) | Nenhum |
| 3 | Dobrada (2x) | Cor real, dithering suave |
| 4 e 5 | Quádrupla (4x) | xBR, correção de geometria |

E com PSP:

| Nota | Resolução | Anisotrópico |
|---|---|---|
| 1 e 2 | 480×272 | desligado |
| 3 | 960×544 | 4x |
| 4 e 5 | 1920×1088 | 16x |

Máquina forte roda o mesmo jogo com quatro vezes mais definição. Máquina
fraca roda o mesmo jogo sem engasgar. Você não escolhe nada.

---

### Sobre o ReShade

Não dá para usar ReShade aqui, e você não vai sentir falta.

ReShade injeta uma DLL dentro de jogos de PC. Os emuladores não funcionam
assim. O que o RetroArch tem no lugar é o **sistema de shaders**, que faz a
mesma coisa — melhora cor, nitidez e aparência — mas foi feito para
emulador, é mais leve e não precisa injetar nada em lugar nenhum.

O ARENA liga o shader sozinho quando a máquina é nota 3 ou mais:

| Nota | Filtro |
|---|---|
| 3 | Pixellate — deixa o pixel quadrado e limpo, custa quase nada |
| 4 | Grade de LCD — cara de tela de portátil |
| 5 | CRT Geom — cara de TV de tubo, com curvatura |

**Para os filtros funcionarem, você precisa do pacote de shaders.** Abra o
RetroArch por fora, vá em *Atualizador Online → Baixar Shaders Slang*. Se
não baixar, o ARENA desliga o filtro em silêncio — o jogo abre normal, só
sem o efeito.

---

### Sobre 60 quadros por segundo

Cada console tem a velocidade dele. Super Nintendo americano roda a 60,09
quadros. Europeu roda a 50. Forçar 60 em tudo **desafina o som e acelera o
jogo**.

O certo é o que o ARENA já faz: sincroniza com o seu monitor e deixa cada
console rodar na velocidade original.

Se a imagem estiver tremendo ou o som picotando de leve, o problema quase
sempre é que seu monitor roda a 60,00 e o console pede 60,09. Solução: no
jogo, `Esc → Configurações → Vídeo → Taxa de Atualização Estimada`. Deixe o
RetroArch medir por uns segundos e aceite o valor que ele achar.

---

### PlayStation: tirar o tremido

Aquele balanço dos cenários no PlayStation não é defeito do emulador. O
console de 1994 calculava a posição dos polígonos com números inteiros, sem
casa decimal. O resultado é vértice que pula de um pixel para o outro — e a
textura escorregando junto.

O **PGXP** refaz essa conta com precisão de verdade. O cenário para de
balançar, a textura para de escorregar, e o jogo continua exatamente o mesmo
por dentro.

O ARENA liga a partir da nota 2, porque custa pouco e é a maior diferença
visual que existe nesse console:

| Nota | O que entra |
|---|---|
| 2 | PGXP, correção de textura, resolução dobrada, cor real |
| 3 | Resolução 4x, dithering suave, cache de vértice |
| 4 | Resolução 6x, filtro xBR, buffer de profundidade, anti-serrilhado 4x |

O disco inteiro também vai para a memória, então o jogo para de engasgar nas
trocas de tela.

---

### PSP: os pontinhos pretos

Se você viu pontos pretos espalhados pela tela, era o **aumento de textura
por xBRZ**. Ele inventa pixel onde não havia, e em jogo com transparência
isso vira sujeira.

O ARENA agora deixa desligado. O ganho de imagem vem da **resolução
interna**, que multiplica o desenho sem inventar nada:

| Nota | Resolução |
|---|---|
| 1 e 2 | 480×272, a original |
| 3 | 960×544 |
| 4 e 5 | 1920×1088 |

Se você quiser mesmo o xBRZ de volta, é em `servidor\graficos.json`, na
chave `ppsspp_texture_scaling_level`.

---

### Mipmap, texturas e anisotrópico

Só valem para consoles 3D — Nintendo 64, Dreamcast, PSP, PS2, GameCube. Em
jogo 2D não existe textura em perspectiva, então não muda nada.

| Ajuste | O que faz |
|---|---|
| **Mipmap** | Deixa o chão longe menos "fervilhante". O ARENA já liga no Dreamcast |
| **Anisotrópico** | Deixa a textura nítida quando vista de lado |
| **Filtro de textura** | Suaviza ou reconstrói a textura ampliada |
| **Resolução interna** | O jogo é desenhado maior e depois cabe na tela |

Todos custam **placa de vídeo**, não disco. Se a imagem estiver bonita e o
jogo travando, é a placa que não dá conta — desça a resolução interna
primeiro, ela é a que mais pesa.

---

### Liberar o disco durante o jogo

O ARENA manda os emuladores carregarem o jogo para a memória em vez de ler
do disco o tempo todo:

| Console | Ajuste |
|---|---|
| PlayStation | `LoadImageToRAM` — o CD inteiro vai para a memória |
| Sega Saturn | `cdimagecache` — mesma coisa |

Isso resolve três coisas de uma vez: **o jogo para de engasgar** nas
trocas de tela, **o pen drive dura mais** porque para de ser lido, e **o
disco fica livre** para o servidor do ARENA gravar os recordes.

Só use em máquina com 4 GB ou mais. Um jogo de PlayStation ocupa uns 600 MB
de memória.

---

### Mexer você mesmo

Todos esses ajustes estão em **`servidor\graficos.json`**, em texto puro.

```json
"swanstation": {
  "por_nota": [
    { "nota_minima": 4, "opcoes": {
      "swanstation_GPU_ResolutionScale": "4"
    }}
  ]
}
```

`nota_minima` é a nota que a máquina precisa ter para receber aquele bloco.
Os blocos vão sendo aplicados um por cima do outro, do mais leve para o mais
pesado.

**Errou alguma coisa?** Opção que o RetroArch não reconhece é simplesmente
ignorada. Se quiser voltar do zero, apague o arquivo `graficos.json` — o
ARENA volta a rodar sem ajuste fino, sem quebrar nada.

Depois de editar, feche e abra o ARENA.

---

### Quando travar

Faça na ordem. Uma coisa por vez, testando entre elas.

| Ordem | O que fazer |
|---|---|
| 1 | Ajustes → Simples → **Desempenho** |
| 2 | `graficos.json`: baixe a resolução interna daquele console |
| 3 | Ajustes → Avançado → desligue **Filtros de tela** |
| 4 | Ajustes → Avançado → ligue **Vídeo em segundo plano** |
| 5 | Ajustes → Avançado → **Fila de imagens** para 3 |

Se depois de tudo isso ainda travar, aquele console é grande demais para
essa máquina. A etiqueta vermelha **Capenga** já avisava.

---

### O que pesa mais, na ordem

1. **Resolução interna** — dobrar é quatro vezes mais trabalho
2. **Filtro de tela (shader)** — CRT pesa muito, Pixellate quase nada
3. **Filtro de textura** — xBR e xBRZ pesam, Bilinear é barato
4. **Anisotrópico** — barato em placa moderna
5. **Mipmap** — praticamente de graça, e melhora a imagem

Se precisar cortar, corte de cima para baixo.


---
