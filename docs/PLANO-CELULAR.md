# O celular e o ARENA: roteiro revisado (23/10/2026)

Pedido do Rafael (23/10/2026), em três partes que aqui viram um plano só:

1. o ARENA do Android mostrar o hardware completo do aparelho ao aluno, "até
   os miliamperes da bateria", para ele saber a capacidade de uma bateria
   nova se um dia trocar a dele;
2. tudo o que a versão do computador faz, no Android, adaptado ao celular
   (controles na tela ou controle de verdade, Bluetooth ou por USB-C,
   configurado sozinho ou à mão);
3. o celular como controle do ARENA do computador, "direto nos servidores
   locais, para ambos se comunicarem".

E um roteiro de três etapas (painel de hardware pelo ADB, captura de tela,
celular como controle), que ele pediu para avaliar e aprovar antes de seguir.

## Veredito sobre o roteiro: aprovado, com mudanças

Nada no roteiro é problema em si: ADB oficial do Google, sensores e
WebSocket padrão e uma ponte de controle são engenharia comum. As mudanças
existem porque o ARENA tem regras que o roteiro não conhecia
(`CLAUDE.md`: só biblioteca padrão, sem administrador, roda do pen drive,
offline, alunos menores de idade).

| # | O roteiro dizia | Vira | Por quê |
|---|---|---|---|
| 1 | Electron ou Tauri no computador, Node.js na rede | **Python puro**: o próprio servidor do ARENA (`servidor\`) e a tela HTML/JS dele | O ARENA não instala nada, não usa `pip` e roda do pen drive num Celeron de 7,7 GB. Node e Electron são instalação e peso a mais, sem ganho |
| 2 | Gamepad virtual com o **ViGEmBus** | **Network RetroPad** do RetroArch: o servidor do ARENA manda o botão por UDP para o `127.0.0.1` | O ViGEmBus é driver de kernel (a instalação pede administrador, e o ARENA não mexe em driver) e o autor o **aposentou**: o README oficial diz "THIS PROJECT HAS BEEN RETIRED" [Certo: github.com/nefarius/ViGEmBus, lido em 23/10/2026]. O Network RetroPad já vem no RetroArch 1.22.2 que o ARENA usa, e foi provado aqui: START e A mandados por UDP tiraram o Thwaite (NES) da tela de título |
| 3 | Servidor WebSocket em Node | Uma rota WebSocket no servidor do ARENA (RFC 6455 na biblioteca padrão), com mensagens binárias de poucos bytes | Mesma latência, nenhuma instalação |
| 4 | Giroscópio lido pelo navegador do celular | Giroscópio **só dentro do app ARENA do Android**; no navegador comum, por `http://<IP do PC>`, só os botões | `DeviceOrientationEvent` exige contexto seguro [Certo: MDN, selo "Secure context"]. Dentro do app, a tela vem de `127.0.0.1`, que conta como seguro. Por `http://192.168...` não |
| 5 | Captura de tela com botão "atualizar" | **Uma imagem por clique**, sem atualizar sozinha e sem gravar em disco | Regra do projeto: nada de gravação de vídeo nem de transmissão, por causa dos alunos menores. Uma atualização em laço seria transmissão |
| 6 | "Instale o Platform Tools" | O `adb` vem do site do Google e **não vai no pacote**; o ARENA o procura em 4 lugares e, se não achar, explica onde baixar | O pacote do ARENA leva só o que é do ARENA ou de licença livre |
| 7 | (não dizia) | **Segurança do controle remoto**: desligado por padrão; liga num clique no computador; código de 4 dígitos mostrado na tela do PC; só rede local; limite de eventos por segundo; o RetroArch só escuta a porta enquanto o jogo roda | Sem isso, qualquer colega da sala mandaria botão para o jogo do outro |
| 8 | (pedido anterior) engenharia reversa do DroidJoy | **Fora.** O roteiro novo já proíbe, e não é preciso: o protocolo do RetroArch é documentado | Apps do gênero entram só como pesquisa de recursos e de layout (o que as lojas descrevem), sem descompilar nada |

Os emuladores de fora (PCSX2, Dolphin, RPCS3, Xenia) não leem o Network
RetroPad. Para eles, o celular como controle fica para uma fase seguinte, por
teclas (sem driver). Isso é dito na tela, não escondido.

## O que o A12 respondeu (SM-A125M, Android 12, medido em 23/10/2026)

O roteiro previu que `charge_full_design` quase nunca aparece sem root, e foi
isso: no Galaxy A12 **todos** os arquivos de `/sys/class/power_supply/battery/`
dão "Permission denied" para o shell do ADB. O que o aparelho dá de verdade:

| Dado | De onde | Valor no A12 |
|---|---|---|
| Nível, voltagem, temperatura, saúde, fonte de energia | `dumpsys battery` | 28%, 3711 mV, 33,7 °C, boa, USB |
| Carga agora (µAh) | `dumpsys battery` ("Charge counter") | 1405000 µAh (1405 mAh) |
| Capacidade de fábrica | `dumpsys batterystats` ("Capacity", perfil de energia do Android) | 5000 mAh |
| Capacidade "aprendida" pelo Android | `dumpsys batterystats` | 5000 mAh (igual à de fábrica) |
| Índice de saúde da Samsung (ASOC) | `dumpsys battery` ("mSavedBatteryAsoc") | 86% |
| Capacidade de projeto (`charge_full_design`) | `/sys/class/power_supply/*/` | **indisponível neste aparelho** (sem permissão) |

Duas fontes que **não concordam**: a conta "carga ÷ porcentagem" dá uns
5.018 mAh (100% da fábrica), e o ASOC da Samsung diz 86%. O painel mostra as
duas, cada uma com o nome da fonte, e não escolhe por você: a conta é uma
pista, não uma medida, porque o contador de carga de alguns fabricantes é
calculado em cima da capacidade de fábrica e não mostra o desgaste.

## A ordem do trabalho (decidida em 23/10/2026, às 21h40)

Os pedidos da noite chegaram em sequência e se apoiam uns nos outros, então a
ordem abaixo segue o que depende de quê, e não a ordem em que chegaram. Se o
Rafael quiser trocar, é só dizer.

| # | O quê | Estado | Por que nesse lugar |
|---|---|---|---|
| 0 | Pasta `ARENA` visível no Android e a gaveta "Como colocar" com o caminho certo (no celular e no PC, pelo cabo) | Feito; falta olhar no A12 | |
| 1 | Hardware completo no app (Ajustes → Máquina → Este celular) | Feito; falta olhar no A12 | |
| 2 | **ETAPA 1**: painel do celular ligado no cabo, no ARENA do computador (`servidor\adb_aparelho.py`) | **Feita**: testada ao vivo no A12, 54 testes novos, bateria inteira verde; falta o commit | |
| 3 | **PS2 no A12: os testes com o ARMSX2** | Em andamento (ver "PS2" abaixo) | Decide quanto vale tunar o 5 |
| 4 | **Armazenamento: interno e cartão SD** (volumes, jogos no cartão, cache no interno, mover entre os dois) | **Próximo** | É a base do 5, do 6 e do 11: sem volume não há "jogos do cartão" nem "mover" |
| 5 | **PS2 no ARENA do Android pelo ARMSX2** (o console PS2 aparece no celular; o ARENA abre o jogo com o caminho do arquivo) | Depende do 3 | Precisa do 4: os jogos de PS2 estão no cartão |
| 6 | **ROMs em qualquer lugar do celular** → "fora da pasta certa" → um toque move | Registrado (pedido das 21h37) | Precisa do 4 (volumes, permissão) e do 5 (o PS2 existe no celular); estende o "Procurar jogos baixados" |
| 7 | **Ícone: o supercontrole**, em todas as versões | Registrado | Independente; pode ser feito enquanto espera o celular; tem de estar pronto antes do Release |
| 8 | **ETAPA 2**: captura de tela, uma por clique | A fazer | Segue o roteiro |
| 9 | **ETAPA 3**: celular como controle do computador (Network RetroPad pelo servidor do ARENA) | A fazer | Segue o roteiro |
| 10 | **Controles e teclado no Android**: a ordem de conexão define o jogador 1 a 8, a tela de toque é o próximo jogador depois dos controles, e o teclado (com fio ou Bluetooth) é reconhecido; botões da tela somem sozinhos, mapeamento automático e à mão (o GameSir Nova Lite do Rafael, dois deles, é o de teste) | A fazer; pedido das 21h50 registrado abaixo | Os dois controles já estão pareados no A12. A tela de toque como jogador 3 precisa de um remendo no RetroArch |
| 10-A | **Controle na tela personalizável e pacotes de aparência** (mover e redimensionar peças, analógico esquerdo, direito ou nenhum, formas e cores de SNES, N64, PlayStation, Xbox, GameCube; estilos prontos dentro do APK) | Registrado (pedido das 22h30) | Usa o gerador de overlay do ARENA e o mesmo remendo do item 10 |
| 10-B | **Tela cheia sempre** (resolução e escala menores só por ajuste manual) e **o Lossless Scaling adaptado ao Android** | Registrado (pedido das 22h40) | Mexe no padrão do formato da imagem no Android, no Vulkan do A12 e na escala |
| 11 | Paridade com o computador, função por função (matriz abaixo) | A fazer | Fecha o que sobrar dos itens acima |
| 12-A | **Instalar sem tropeço**: um APK só para celular com nome claro, página "Baixar" que escolhe o arquivo certo (ou a versão web), o ARENA instala o ARMSX2 com um toque e o assistente da primeira abertura configura o resto | Registrado (pedido das 22h30) | Junto do Release; o Android sempre mostra a tela "Instalar" |
| 12 | Teste final no A12 e Release: juntar `auditoria-4` ao `main`, versão nova, `rodada_final.py`, pacotes e `gh-pages` | Por último | Só depois dos testes no Android (autorizado pelo Rafael) |

## A regra mais nova (24/10/2026, 0h): o emulador roda DENTRO do ARENA

> "assim como na versão de pc, qualquer emulador deve rodar dentro do arena e
> não um aplicativo a parte, ele não deve aparecer instalado pois a idéia como
> no computador o servidor offline manipular os arquivos, configurações,
> ajustes finos que refletem diretamente nesses emuladores mas não baixar o
> app novo assim como no arena deve ser copiar e colar a pasta no local certo,
> pois se a pessoa quiser baixar um emulador a parte poderá usar ele isolado
> do arena, além disso como no pc procure versões de bios e emuladores
> gratuitos mas permita usar os convencionais também e deixe a opção de
> escolher qual usar e continue testes por telefone para ser mais assertivo"

**Isto troca o plano do PS2** (itens 3 e 5 abaixo): o ARMSX2 **como app
instalado, aberto por intent, sai do plano** (foi o que testei até 23h40; ficou
só como medida de comparação). O que vale agora:

- **No Android, o emulador é um núcleo do RetroArch do próprio app do ARENA**
  (um `.so`), do jeito que os outros 60 já são. Nada aparece instalado, e o
  servidor do ARENA manda em tudo (opções do núcleo, BIOS, pastas, controles).
- **Instalar = copiar e colar.** Os núcleos vêm no APK (`assets/arena-nucleos`)
  e uma pasta `emuladores` visível em `/sdcard/ARENA` aceita um núcleo colado à
  mão: o ARENA o leva para a pasta dos núcleos do app (o `/sdcard` do Android
  não deixa executar código, por isso a cópia). Quem quiser outro emulador à
  parte instala o app dele e usa isolado: os dois não se misturam.
- **Livre e convencional, com escolha**, como no PC (`jeitos_de_abrir.py`): no
  PS2, o convencional é o ARMSX2 ou o PCSX2 do libretro, com a BIOS de verdade, e
  o livre é o **Play!** (código aberto, imita a BIOS, não pede arquivo da Sony).
- **Os testes são no celular de verdade**, e foi o que mudou o plano.

### O que o A12 respondeu sobre os núcleos de PS2 (medido em 24/10/2026)

O buildbot oficial do libretro (`buildbot.libretro.com/nightly/android/latest/arm64-v8a`)
tem hoje, para Android arm64, o `armsx2`, o `pcsx2`, o `play`, o `dolphin`, o `ppsspp`,
o `flycast`, o `citra`, o `azahar`, o `melonds`, o `rpcs3`, o `xenia_edge`, o `cemu`, o
`vita3k`... [Certo: o `.index-extended` da pasta, lido em 24/10/2026].

- **`armsx2_libretro_android.so` (33 MB) não roda no A12**: `SIGILL (ILL_ILLOPC)`
  no `ldaddal x9, x8, [x8]` (o contador de um `shared_ptr`), medido no aparelho
  às 0h02. Motivo [Certo: `cmake/BuildParameters.cmake` do ARMSX2]: o padrão é
  `-march=armv8.1-a`, com as atômicas LSE direto no código (524 ocorrências),
  e o Cortex-A53 é ARMv8.0 (o comentário do próprio projeto cita "casal SIGILL
  em um A53 de verdade"). O ARMSX2 só roda no A12 compilado com
  `-march=armv8-a -moutline-atomics`, como o APK `legacy` dele. Em celular com
  Cortex-A55 ou mais novo (quase todo de 2019 em diante), o do buildbot serve.
- `pcsx2_libretro_android.so` (10 MB, do repositório `libretro/ps2`) e
  `play_libretro_android.so` (5,5 MB) **não têm LSE no código** (só nas funções
  auxiliares, com teste em tempo de execução): são candidatos ao A12.
- O núcleo do ARMSX2 é Vulkan ou OpenGL e pede, em `system/pcsx2/`, a pasta
  `bios` e a pasta `resources` (11 MB, a do mesmo ARMSX2).

### O vídeo lento do PS2 no A12 (medido em 24/10/2026, de manhã)

> "o vídeo do jogo continua muito lento mas o som parece acompanhar"

**Causa [Certo, medido]:** no vídeo de abertura do Mortal Kombat Armageddon o
jogo ia a **5 a 9 quadros por segundo** (o resto do jogo, a 55 a 60). Uma só
thread do vídeo (a "GS") ficava em 94% de um núcleo do processador, enquanto a
thread do PS2 (EE) ficava em 15%: o gargalo era desenhar o filme, não emular. A
causa era a **pré-carga de textura completa** (`texture_preloading = 2`, o
padrão do núcleo), que a cada quadro do filme calcula e guarda a imagem
inteira. Com a **parcial** (`= 1`) o mesmo filme roda a **~54 fps**.

A mesma cena, o mesmo aparelho, só mudando o ajuste (o menor fps visto na
rodada de 115 s; a rodada começa apertando START, com um evento de tecla):

| Ajuste | menor fps | amostras abaixo de 40 |
|---|---|---|
| OpenGL, pré-carga completa (o padrão do núcleo) | **5,2** | 19 de 37 |
| OpenGL, pré-carga parcial | 12,8 (depois ~54) | 3 de 36 |
| OpenGL, sem pré-carga | 20,2 | 5 de 36 |
| OpenGL, parcial, sem leitura de volta da imagem | 23,0 | 3 de 36 |
| **Vulkan** (com a thread de vídeo dupla) | **51,8** | 0 de 36 |
| **Vulkan** (sem a thread dupla) | **52,8** | 0 de 36 |
| Renderizador por software (4 threads) | 57,7 | 0 de 37 |

Como ler: o OpenGL só fica bom com a pré-carga parcial; o Vulkan segura o
filme sem depender disso. O núcleo só divide o vídeo em duas threads no
Vulkan (`GSBackThreadPolicy.h` do ARMSX2: a divisão "precisa do Vulkan" para o
renderizador de hardware). O fps é o da camada do RetroArch no SurfaceFlinger
(uma janela que alisa a curva): vale para comparar rodadas, não para dizer o
quadro exato.

**Correção importante (24/10, depois):** a tabela acima usa o fps da camada do
Android, que **engana neste núcleo**: quando o PS2 não dá conta, ele repete a
última imagem e o Android continua contando 50 a 60 quadros. O Mortal Kombat
"a 50 fps" na luta andava, na verdade, a **~15 a 23% da velocidade** (o relógio
do round contava 8 segundos em 45 s reais). A medida certa é o mostrador do
próprio emulador (`OsdShowSpeed`, lido da tela), e o núcleo do ARENA agora
também grava essa velocidade (`system/pcsx2/arena-status.json`, a cada 2 s). A
linha do "renderizador por software" **não vale**: ele não liga neste núcleo
(`Failed to initialize GS`, tela preta), e o ARENA não o oferece.

**A velocidade de verdade no A12** (Mortal Kombat Armageddon, Vulkan, 1x,
mostrador do emulador; abertura e carregamentos):

| Processador do PS2 (EE) | Velocidade | EE por quadro (limite 16,7 ms) |
|---|---|---|
| sem ajuste (100%) | 70 a 73% | 22,7 ms |
| 75% | 76 a 87% | ~20 ms |
| 60% + salto de ciclos moderado | 83 a 93% | ~18 ms |
| **50%, sem salto** | **93 a 99% no filme** | 15 a 17 ms |
| regulador automático (`DynamicEECycleRate`, desce sozinho até 60%) | 80 a 93% | ~18 ms |

O OpenGL e o Vulkan deram o **mesmo** nessas cenas (68-73% e 70-73%): ali o
limite é o processador, não a placa. Mesmo com o EE a 50%, a **escolha de
lutadores** caiu para **19 a 27%** (EE 30 a 88 ms por quadro) e a luta para
~15 a 23%: **o A12 não dá conta do 3D do Mortal Kombat Armageddon**, por mais
que se ajuste. É o aparelho, não o ARENA.

**O que o ARENA faz com isso** (`graficos.passo_do_ee_do_ps2`): o salto de
ciclos fica sempre desligado (o próprio ARMSX2 diz que ele quase sempre
atrapalha, e o regulador automático só funciona sem ele); o ponto de partida do
EE é **75% no aparelho fraco (nota 1 e 2)** e 100% nos outros; "abaixo do
original" leve pede 60% e o mínimo 50%; cada degrau do "Desempenho que
aprende" desce mais um passo; e o **regulador automático fica ligado** (desce
até 2 passos sozinho durante o jogo e volta quando alivia). O "Desempenho que
aprende" agora decide pela **velocidade lida do emulador** (abaixo de 90% em
mais de uma quarta parte das medidas), porque a thread do EE fica em ~100% até
com o jogo a 100% da velocidade.

**O que o ARENA faz agora:**
- `graficos.json → ini_armsx2` guarda o que o ARENA ajusta no `.ini` do núcleo
  (`texture_preloading = 1` sempre; `GSBackThreadMode = 1` só com o Vulkan).
- O núcleo ganhou um **segundo remendo**
  (`ferramentas/remendos/armsx2-libretro-sobreposicao-do-arena.patch`): ele lê
  `system/pcsx2/inis/arena-overrides.ini` a cada abertura, **inclusive a
  primeira** (o `.ini` do próprio núcleo só existe depois da primeira vez).
  Para um núcleo sem o remendo (colado à mão), o ARENA também troca direto no
  `.ini` dele quando já existe.
- O menu da BIOS do PS2 (idioma, data e hora, memory card) abre por **Ajustes →
  Emuladores → Abrir só a BIOS**, escolhendo o PS2: no celular, sem disco, com a
  abertura do PS2 ligada (`preparar_o_ps2_do_android`).

**O que o Rafael sentiu (24/10, manhã):** o jogador 2 passou a ser reconhecido
(dois cursores independentes na escolha de lutadores; "o controle moveu o
jogador certo"); o vídeo e o jogo "melhoraram, mas ainda lentos e travando
muito" no vídeo de abertura e na luta. Combina com os números: o A12 só chega
perto dos 100% em trechos do filme, e a luta fica entre 15 e 27%.

**Decisões desta rodada (todas com teste):**
- **Automático = Vulkan quando o aparelho tem Vulkan de verdade**, senão OpenGL
  (`graficos.opcoes_do_armsx2(..., vulkan=)`); quem escolhe na mão manda.
- **EE**: partida em 75% no aparelho fraco, sem salto de ciclos, regulador
  automático ligado; o degrau do "Desempenho que aprende" (agora pela
  velocidade lida do emulador) desce mais um passo por partida lenta.
- **Pré-carga de textura parcial** sempre; **thread dupla do vídeo** só no
  Vulkan.
- A linha de ajuste fino da pessoa **substitui** a da escada (antes saía duas
  vezes a mesma chave no arquivo de opções do RetroArch).
- Nota do celular pela velocidade medida e pela memória (até o 5) e placa pela
  tabela `hardware.nota_da_placa_de_celular` (estimativa; só o A12 foi medido).

**Falta, em ordem:**
1. Instalar o APK final no A12 e rodar `levantamento_ps2.py` (a velocidade real
   de cada um dos 37 jogos de PS2, sem apertar tecla): dirá quais jogos o A12
   aguenta.
2. Aprendizado e selo **por jogo** (hoje o "Desempenho que aprende" é por
   console, e no PS2 a diferença entre jogos é enorme).
3. Testar o menu da BIOS do PS2 (Ajustes → Emuladores → Abrir só a BIOS), o
   `arena-overrides.ini` na primeira abertura, a piscada clara, retrato e
   paisagem.
4. Aviso de calor: o processador do A12 cai de 2,3 para 1,88 GHz perto de
   45-47 °C (sensor AP); dizer ao aluno (tirar a capinha e o carregador).
5. Autoconfig do GameSir Nova Lite (13623/4161; hoje cai no "padrão alternativo").
6. Pesquisa de outras otimizações (Game Mode, ADPF, taxa de atualização, escala
   estilo Lossless Scaling), **uma frente por vez e com busca curta**.

**Armadilhas de teste** (também na memória do assistente): comando injetado por
`adb input` cria um controle "Virtual" que toma o jogador 1; e o fps do Android
engana (medir pelo mostrador de velocidade ou por `arena-status.json`).

### Cartão SD e armazenamento interno cheio (item 4)

> "O Arena no android deve ser capaz de armazenar jogos tanto na memória
> interna como no [cartão SD] (corrigi: não é ssd e sim sd), e ele deve ser
> capaz de gerenciar isso perfeitamente para telefones que quase sempre estão
> com armazenamento interno cheio, então busque em programas e apps do gênero
> que são case de sucesso implementações que permitam eu ter o arena
> instalado no armazenamento interno e poder jogar jogos salvos no cartão sd
> utilizando o processamento da memória de armazenamento interna onde tem
> mais capacidade de leitura e escrita"

- **Pesquisa feita** (código aberto, lido em 23/10/2026): o **Lemuroid**
  (`Swordfish90/Lemuroid`, arquivos `StorageAccessFrameworkProvider.kt`,
  `CacheCleaner.kt` e `GameCacheUtils.kt`) deixa a pasta de jogos onde a
  pessoa quiser, inclusive o cartão, e na hora de jogar **copia o jogo para o
  cache interno do app** (reaproveita se já está lá), com **limite de cache
  escolhido** (de 64 MB a 10 GB, padrão 1% do interno) e limpeza **LRU pelo
  último acesso**. É o modelo para o ARENA.
- **Medido no A12** (leitura sequencial de 256 MB, primeira leitura): cartão
  **59 MB/s**, interno **106 MB/s**. Para jogo de CD/DVD isso quer dizer que o
  cartão dá conta de jogar direto; o que pesa é o processador.
- **Desenho:** o programa, o banco, os saves, os estados, as BIOS e os
  atalhos ficam no interno (já ficam); o cartão vira uma **origem de jogos
  extra** (`indexador.ORIGENS`) ligada por atalho dentro de `jogos\`; jogo
  grande de disco pode ser copiado para o cache interno ao jogar (limite e
  limpeza LRU); o painel mostra o espaço e a velocidade de cada volume; mover
  jogo entre volumes **copia, confere e só então apaga o original**, e só com
  o toque do aluno.

### Os jogos do PC no cartão

> "Todos os jogos que tem no pc tem no cartão sd no meu celular nesse caminho
> para você por favor já implementá-los no arena no meu celular para os
> testes reais com o aparelho: Este Computador\[o celular]\[o cartão
> SD]\Projetos\Criador De Apps Pedagógicos\arena-console/jogos/pessoais"

Conferido em 23/10/2026: o cartão (exFAT, 477 GB, 58 GB livres) tem a pasta
`jogos\pessoais` com **35 pastas de console e 115 GB**, mas **faltam** as que
o PC tem de PSP (7,8 GB), PS3, Sega CD, Sega Saturn, Super Nintendo, Wii,
Xbox 360 e Sega 32X. Dos que o celular roda, estão lá Dreamcast (6,7 GB), PS1
(2,9 GB), Nintendo 64, Neo Geo, Mega Drive, fliperama, Commodore 64, Atari
2600, Amiga e ColecoVision, e de PS2 há 37 jogos (cerca de 100 GB).

### PS2 no A12 (itens 3 e 5)

> "por favor faça o possível para implementar o ps2 nesse telefone, pois já
> vi celulares menos capazes rodando o videogame mas sozinho eu nunca consegui
> fazer um emulador de ps2 funcionar o oficial pelo menos"

- Não existe PCSX2 **oficial** para Android; o que roda em celular são
  projetos à parte. O aberto e ativo hoje é o **ARMSX2** (GPL-3.0,
  `ARMSX2/ARMSX2`, versão 2.8.4 de 17/10/2026, nightly de 23/10).
- Os requisitos oficiais [Certo: armsx2.net/docs/system-requirements, lido em
  23/10/2026]: mínimo Android 8.0 e 64 bits; recomendado SoC potente, GPU
  Vulkan atual, **6 GB de RAM ou mais** e refrigeração. O A12 cumpre o mínimo
  e fica bem abaixo do recomendado (3,7 GB, 8 × Cortex-A53, PowerVR GE8320).
- O A12 é ARMv8.0: três dos quatro APKs da 2.8.4 são ARMv8.2 e **não rodam**
  no Cortex-A53. O certo é o `ARMSX2-2.8.4-legacy-armv8.0-sdk26.apk`
  (SHA-256 `62db5395...dd8c4f`, conferido com o publicado pelo GitHub).
- Como o ARENA abre um jogo: intent explícita para
  `com.armsx2/com.armsx2.MainActivity` com o caminho em texto no extra
  `path` (o próprio ARMSX2 aceita; código lido em
  `MainActivityRuntime.kt`, `extractLaunchUri`). A BIOS vai em
  `Android/data/com.armsx2/files/bios`, e o assistente do app pede a pasta da
  BIOS pelo seletor do Android.
- O ARMSX2 tem recursos de rede (Remote play, Discord, RetroAchievements) que
  o ARENA **não liga e não oferece**, por causa da regra de não transmitir.
- Resultados dos testes: ver a seção "O PS2 no A12, medido" mais abaixo.

### ROMs em qualquer lugar do celular (item 6)

> "o ARENA deve achar roms baixadas em qualquer lugar do telefone para poder
> de dentro do arena mover esses jogos para a pasta ps2, ou seja a rom vai
> ser reconhecida pelo arena na parte de ps2 porém vai ter o aviso que não
> está na pasta certa e com um toque ele vai se precisar pedir permissão para
> mover o arquivo para pasta certa, apenas registre isso e decida a ordem de
> implementar"

O que isso exige, já separado em regras (para quando for feito):

1. **Procurar no aparelho todo** (interno, cartão e pen drive de OTG), e não
   só em `Download` como o "Procurar jogos baixados" faz hoje
   (`servidor\baixados.py`). Só olha **arquivo com extensão de jogo** (as do
   `consoles.json`); nunca abre foto, vídeo, áudio nem documento. Fica de fora
   `Android\`, pasta oculta, `DCIM`, `Pictures`, `Movies`, `Music` e a pasta
   do próprio ARENA. Tem barra de progresso, limite de tempo e botão Parar.
2. **Reconhecer o console pelo conteúdo**, e não só pela extensão
   (`servidor\identificador.py`: o `.iso` pode ser de PS1, PS2, PSP ou
   GameCube; o `.bin` e o `.chd` também).
3. O jogo aparece **na seção do console certo** (por exemplo, PS2) com o
   selo **"fora da pasta certa"** e de onde ele veio; dá para jogá-lo de onde
   está, e o aviso só some quando ele é levado para a pasta do console.
4. **Um toque em "Levar para a pasta certa"**: se o Android pedir permissão
   (Acesso a todos os arquivos), explica para quê antes e abre a tela do
   sistema. No mesmo volume é só renomear. Entre volumes, **copia com
   progresso, confere o tamanho e só então tira o original**. Cria a pasta do
   console se faltar. **Nunca sobrescreve**: se já existe um arquivo com o
   mesmo nome, pergunta. Nunca apaga sem o toque do aluno.
5. Jogo de vários arquivos (`.cue` com `.bin`, `.gdi` com as trilhas, `.m3u`
   com os discos) é levado **junto**, como no `arrumar.py`.
6. **Privacidade** (alunos menores): a busca só lê nome e os primeiros bytes
   de arquivo com extensão de jogo; nada sai do aparelho; nada é guardado além
   da lista do ARENA.
7. Mesma função no computador (paridade): lá o "Procurar jogos baixados" já
   existe; "procurar em outra unidade" fica como melhoria.

### Controles e teclado no Android: a ordem dos jogadores (item 10)

> "A ideia é que, assim como no PC, a ordem de conexão dos controles
> determina que é player 1, 2, 3, 4 ou player 8, e, como no PC, se tem 2
> controles, quem vai jogar na tela do celular é o player 3 e assim por
> diante. O ARENA do Android deve também reconhecer teclados para telefones,
> sejam com fio ou via Bluetooth, por gentileza."

O que já existe (lido no código em 23/10/2026): o app conta os controles de
jogo (`ArenaServico.java`, `InputDevice` com GAMEPAD ou JOYSTICK, sem os
virtuais) e o servidor repassa (`ponte_android.controles()`), e o
`controles.opcoes_do_retroarch` põe o **teclado como o jogador N+1** (com 3
controles, o teclado é o 4, igual no PC). O teclado de verdade é achado pelo
nome (`ponte_android.teclado_fisico()`, tipo alfabético, fora os que também
são controle) e entregue ao RetroArch em `input_android_physical_keyboard`;
sem isso, o RetroArch toma o teclado com setas por um controle.

O que falta:

1. **A tela de toque como o próximo jogador.** Lido no RetroArch 1.22.2
   (`input/input_driver.c`): o toque do overlay é somado **sempre à porta 0 do
   núcleo** (`if (port == 0)` no joypad, no teclado e no analógico), mesmo com
   o remapeamento de usuários, e não existe opção para mudar (só
   `input_overlay_lightgun_port`, da pistola, e `input_overlay_show_inputs_port`,
   do desenho). Então "a tela é o jogador 3" pede um **remendo pequeno no
   RetroArch**: uma opção nova `input_overlay_port` (padrão 0) em
   `configuration.h`/`configuration.c` e a troca dos quatro `port == 0` do
   overlay por `port == input_overlay_port`, no mesmo molde do
   `android/retroarch/arena-args.patch`. O ARENA grava o número no arquivo da
   partida (= quantos controles estão ligados, mais o teclado, se houver).
   Com a tela escondida (modo Automático com controle ligado) nada muda;
   com **Sempre**, a tela vira o jogador seguinte.
2. **A ordem de conexão** vira o número do jogador (1 a 8): conferir no
   aparelho, com os dois GameSir, em que ordem o Android numera e o RetroArch
   atribui (`input_playerN_joypad_index`); controle que sai e volta entra por
   último (o Android lhe dá um número novo).
3. **Conferir o teclado de verdade** (USB-OTG e Bluetooth): reconhecido ao
   abrir o jogo, no jogador N+1, com as teclas do ARENA (setas, Z, X, Enter,
   F10) e o menu; e se ele chega **durante** o jogo.
4. A mesma regra no **Jogar Junto** e no **celular como controle do PC** (o
   jogador que vem do celular entra como o próximo).

### Controles na tela personalizáveis e pacotes de aparência (item 10-A)

> "A interface e a disposição dos botões na tela deve ser personalizável, ou
> seja, poder mudar o lugar e a posição dos botões, adicionar analógico
> esquerdo, direito ou nenhum dos dois, e colocar os botões no formato e cor
> do Super Nintendo, Nintendo 64, enfim, poder personalizar os controles da
> tela com ícones que se assemelham aos controles de outros consoles. Deve ter
> todas as opções para todos os botões de todos os controles, por exemplo:
> analógico direcional com o formato do analógico do Nintendo 64. Revise os
> apps de referência que são cases de sucesso para ter ideias e exemplos de
> como implementar isso para ficar simples e intuitivo como o ARENA é, e
> descubra uma forma de deixar os pacotes de aparência de botões no jogo
> totalmente configurados e prontos para usar, como tudo deve ser no ARENA: a
> instalação deve ocorrer automaticamente, assim que baixa o APK, ou qualquer
> que seja o formato mais compatível com todos os aparelhos Android antigos ou
> atuais [...]. Que essa instalação faça o caminho que deu certo no telefone
> para instalar, ou verifique alguma solução que seja baixar do GitHub,
> clicar, instalar e configurar tudo sozinho."

**O que os apps de sucesso fazem** (lido em 23/10/2026):

- **Lemuroid e o RadialGamePad** (código aberto, `Swordfish90/RadialGamePad`,
  README): a biblioteca "foi desenhada para personalização" e alimenta todos os
  layouts do Lemuroid; cada controle é um **dial primário** no centro (cruz,
  analógico ou botões) cercado de **dials secundários** (botão único, grupo de
  botões, analógico), e a biblioteca dimensiona e posiciona tudo para
  aproveitar o espaço. O Lemuroid deixa mudar tamanho e posição dos controles.
- **PPSSPP** ("Edit touch control layout", ppsspp.org/docs/settings/controls):
  cada botão se **arrasta e se redimensiona** na própria tela; o centro do
  analógico pode seguir o dedo; a versão 1.20 passou a guardar um layout para
  **retrato** e outro para **paisagem** (Android Authority).
- **Dolphin no Android**: edita posição, tamanho e opacidade; relatos de
  usuários pedem "reiniciar a posição" e dizem que algumas posições se perdem
  (fórum do Dolphin): lição: sempre ter **Restaurar o padrão** e gravar
  certo.
- **Delta (iOS)**: a aparência é um **pacote** (`.deltaskin`, um zip com um
  JSON do mapeamento e a arte por aparelho e orientação, fileinfo.com): abrir
  o arquivo já instala. É o modelo de "pacote de aparência" para o ARENA.
- **RetroArch** (o motor do ARENA): o controle na tela é um texto `.cfg` com
  PNGs e áreas de toque normalizadas (`descN = "entrada,x,y,forma,w,h"`, forma
  `radial` ou `rect`, `descN_overlay = img/arquivo.png`), com páginas
  (`overlay_next`) e analógicos; a comunidade mantém **32 pastas de overlays
  prontos** (`libretro/common-overlays`, CC-BY-4.0, atualizado em 15/10/2026),
  entre elas `n64`, `snes`, `nes`, `psx`, `dual-shock`, `genesis`, `gameboy`,
  `gba` e `arcade`.

**Desenho proposto** (simples para o aluno, no jeito do ARENA):

1. **O ARENA gera o controle na tela.** Um **modelo de layout** (JSON, em
   `dados/`) mais um **pacote de aparência** (as imagens e um JSON que diz o
   formato de cada peça) viram, a cada partida, o `.cfg` do RetroArch, para
   retrato e paisagem, como o ARENA já faz com os botões SAIR e MENU
   (`plataforma.controle_de_toque_do_arena`). Não depende de editar overlay à
   mão nem de baixar nada.
2. **As peças** (todas com todas as opções): direcional (cruz, quatro botões
   separados, estilos NES, SNES, Mega Drive, N64), analógico **esquerdo,
   direito ou nenhum** (formatos: N64 cinza com anel, GameCube amarelo,
   PlayStation, Xbox, genérico), botões de rosto em formas e cores de cada
   console (SNES: Y verde, X azul, B amarelo, A vermelho; N64: A azul, B verde,
   quatro C amarelos, Z; PlayStation: ✕ ○ □ △; Xbox: A verde, B vermelho, X
   azul, Y âmbar; GameCube: A verde grande), gatilhos e ombros, Start e
   Select, e os do ARENA (Menu, Sair, avanço rápido).
3. **Editar na tela, em três toques**: Ajustes → Controle na tela. Um desenho do
   celular (deitado e de pé) onde se **arrasta** cada peça e se muda o tamanho;
   chaves para os analógicos (esquerdo, direito, nenhum); **um toque** escolhe
   o estilo de console (muda formas e cores de tudo junto) e depois dá para
   ajustar peça por peça (formato, cor, tamanho, transparência); "canhoto"
   (espelha); **Restaurar o padrão**. O estilo sugerido muda com o console do
   jogo (SNES abre com o do SNES etc.), e o aluno pode fixar um só.
4. **Pacotes de aparência prontos, dentro do APK**: as imagens e os modelos
   vão em `assets/arena-aparencias/` e são extraídos sozinhos na primeira
   abertura (o `android_inicio.tirar_do_apk` já faz isso com os overlays do
   RetroArch). Arte **original do ARENA**, feita pelo mesmo caminho do ícone
   (SVG → PNG), na mesma paleta; os overlays da comunidade (CC-BY) só entram
   se forem creditados em `CREDITOS.md`.
5. A ordem dos jogadores e a **tela como o próximo jogador** (item 10) usam o
   mesmo gerador: o jogador da tela vira o `input_overlay_port` do remendo.

### Instalar o ARENA no celular: o que dá e o que não dá (item 12-A)

- **[Certo] O Android não deixa nenhum app instalar a si mesmo, nem em
  silêncio.** O aluno sempre vê a tela do sistema ("Instalar") e, na primeira
  vez, autoriza o navegador (ou o gerenciador de arquivos) a "instalar apps
  desconhecidos". Isso vale para qualquer APK baixado do GitHub. O caminho mais
  curto que existe: tocar no arquivo, **Permitir** (uma vez), **Instalar**.
- **O erro do A12 foi o APK errado, não o jeito de instalar.** A mensagem
  "Como o app não é compatível com seu smartphone" veio do APK `x86_64` (o do
  emulador do computador); o `arm64` instala (provado pelo cabo, com a
  Depuração USB). O que o aluno precisa é **um nome claro e um só arquivo**:
  `ARENA-celular.apk` (arm64, o do celular) e o do emulador/PC separado.
- **A página "Baixar"** (GitHub Pages, ao lado da versão web) **escolhe o
  arquivo certo pelo aparelho** (arm64 → o APK; 32 bits ou Android anterior ao
  7.0 → a **versão web**, que se instala pelo navegador, "Adicionar à tela
  inicial", sem APK) e mostra o passo a passo em três telas.
- **O ARENA instala o ARMSX2 (PS2) sozinho**: baixa do GitHub só o APK certo
  para o processador do celular (o `legacy-armv8.0` para o Cortex-A53; os
  `armv8.2` para os mais novos, escolhidos pelas instruções que o processador
  declara) e abre o instalador do Android: um toque.
- **Configurar tudo sozinho** = o assistente da primeira abertura: pasta do
  ARENA, permissão de arquivos, cartão SD, estilo do controle na tela, tela
  cheia, e nada para baixar.

### Tela cheia sempre, e o Lossless Scaling adaptado ao Android (item 10-B)

> "E lembre-se sempre tela cheia, a não ser que vá nas configurações e
> manualmente decida uma resolução ou escala menor, por gentileza, usando
> todas as estratégias, ideias e funcionamento do Lossless Scaling, mas
> adaptado para o Android, sua arquitetura, hardware e possibilidades
> atuais."

- **Hoje** o padrão do formato da imagem é `automatico` (`arena.py`,
  `formato_da_imagem`): o console estica até a borda, **mas com a tela mais
  larga que 16:9 (o celular deitado, 20:9) estica só até o 16:9** e deixa
  faixa dos lados. No Android o padrão passa a ser **tela cheia de verdade**
  (`esticar`, `aspect_ratio_index` 24, sem escala inteira); a resolução ou
  escala menor só vem de um ajuste **manual** em Ajustes. O que o "desempenho
  que aprende" mexe é a qualidade interna do jogo, **nunca o tamanho da imagem
  na tela**.
- **Estratégias do Lossless Scaling e como ficam no Android** (a engenharia
  reversa já feita para o computador, em `servidor/lossless.py`, e a escala do
  ARENA):
  1. *Escala espacial* (LS1, FSR, NIS, Anime4K, xBR, nítido): os `.slangp` do
     ARENA rodam no **Vulkan**; o A12 tem Vulkan 1.1, então testar a
     estabilidade e o custo ali; no OpenGL ES ficam o filtro bilinear ou de
     ponto, a escala inteira e os shaders GLSL leves (sharp-bilinear).
  2. *Fator de escala de renderização* (renderizar menor e subir para a tela
     cheia): a resolução interna de cada núcleo (PS1, N64, PSP, Dreamcast, PS2)
     e o modo modesto, **só a pedido do aluno**.
  3. *Geração de quadros* (LSFG): o RetroArch não tem; no Android fica o que
     existe de verdade: mistura de quadros (shader) para jogo de 30 em tela de
     60 Hz ou mais, **Black Frame Insertion** em tela de 120 Hz,
     sincronização com a taxa real da tela e `video_frame_delay`. O A12 tem
     tela de 60 Hz fixa: lá não se aplica, e o painel diz isso.
  4. *Modo automático*: escolher escala e filtro pelo aparelho e pelo
     console, com o que o ARENA já mede (nota do aparelho e carga por thread).

### O ícone: o supercontrole (item 7)

> "o ícone do arena deve ser um controle que é uma junção de todos os
> controles e formatos já existentes, ou seja, um controle fundido com todos
> que existem de uma forma harmônica. Por exemplo, um controle daquele Xbox
> Duke com 3 pernas para ter aquele analógico do Nintendo 64 com analógicos
> direcionais apenas como o do PS2, ou seja, dois direcionais esquerdos como
> cada um fica no controle e apenas um direito. O padrão de quatro botões de
> ambos os controles continua, mas adicione aqueles botões especiais do
> Nintendo 64 e GameCube além daqueles do próprio controle Duke do Xbox 360
> que serve como base. Então um supercontrole que mistura todos os existentes
> como ícone oficial do ARENA em todas as suas versões."

Em todas as versões: Windows (atalho e `.ico`), tela do ARENA (favicon e
cabeçalho), Android (ícone do app, redondo e adaptativo), Chromebook e site
(PWA: `manifest` e ícones maskable), Linux (`ARENA.desktop`) e as imagens do
`README`. O desenho tem de funcionar de 16 a 512 pixels: versão completa para
tamanho grande e versão simplificada (silhueta de três pontas, quatro botões
coloridos e um analógico) para tamanho pequeno.

## Paridade com o computador

O levantamento por área ainda **não foi feito**. A primeira tentativa (cinco
leitores em paralelo mais um crítico, às 20h) gastou uns 800 mil tokens e os
seis caíram no limite da sessão sem entregar nada. Refazer sem agentes
paralelos: busca curta nas 77 rotas `/api/...` de `servidor\arena.py`, nas 11
abas de `launcher\index.html` e nos atributos `data-fora-do-android` /
`data-so-android` / `data-so-windows`, anotando cada função como igual,
adaptada, faltando ou sem sentido no celular.
