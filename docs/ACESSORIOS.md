# Acessórios dos consoles

Pedido do Rafael (24/10/2026): "emular todos os acessórios de todos os consoles", com uma lista na parte da BIOS
para ligar e desligar cada um (o VMU do Dreamcast, o Rumble Pak do Nintendo 64, o PocketStation, pistolas de luz,
multitaps, cartuchos de expansão), em todas as versões (Windows, Linux, Android, Chromebook), valendo só para os
jogos que foram feitos para o acessório.

## Como usar

**Ajustes → Emuladores → Acessórios dos consoles.** Escolha o console, ligue ou desligue cada acessório e, quando
ele tem opções (onde fica a telinha do VMU, o tamanho, qual cartão), escolha ali mesmo. Vale no próximo jogo que você
abrir. "Voltar os acessórios deste console ao padrão" desfaz tudo daquele console.

O que você escolhe fica em `config.json → acessorios`. Controle que você nunca mexeu **não é gravado**: o emulador
fica como estava. O ARENA é dono dessas chaves: ao voltar ao padrão, a linha antiga some do arquivo de opções.

## O que já se liga hoje (63 acessórios, 25 consoles)

Cada chave, cada valor e cada tipo de controle foi **perguntado ao próprio núcleo**
(`ferramentas\levantar_opcoes_dos_nucleos.py` carrega o núcleo e anota o que ele declara) e é conferido por
`ferramentas\conferir_acessorios.py`: **63 acessórios, 0 problemas, conferidos contra os núcleos do PC** [Certo: rodado em
24/10/2026]. O catálogo é o `servidor\acessorios.json` (dados, não código).

| Console | Núcleo | Acessórios |
|---|---|---|
| Sega Dreamcast | `flycast` | **VMU**: telinha por cima do jogo (cantos, tamanho de 1× a 5×, transparência), bipes do VMU, VMU de cada jogo; encaixes A1/A2 a D1/D2 de cada controle (VMU, Jump Pack, DreamPotato, vazio); tipo de controle de cada jogador (arcade stick, volante, pistola de luz, maracas, vara de pescar, Pop'n Music, Densha de Go!, teclado, mouse, Twin Stick); mira das pistolas; adaptador de banda larga (desligado) |
| Nintendo 64 | `mupen64plus_next` | encaixe de cada controle: Controller Pak, Rumble Pak ou Transfer Pak; Expansion Pak |
| NES / Famicom | `fceumm` | Zapper, Arkanoid, Power Pad, adaptador de 4 jogadores, Hyper Shot, Oeka Kids, Family Trainer |
| Super Nintendo | `snes9x` | Mouse, Multitap, Super Scope, Justifier, M.A.C.S.; mirar com mouse ou com o toque na tela |
| Mega Drive, Master System, Game Gear, Sega CD | `genesis_plus_gx` | controles de 3 e 6 botões, Mega Mouse, XE-1AP, Team Player, 4-Way Play, Menacer, Justifiers, Light Phaser, Paddle, Sports Pad; Lock-On (Sonic & Knuckles, Game Genie, Action Replay); Sega CD e cartão de memória dele; módulo FM do Master System |
| Sega 32X | `picodrive` | controles das duas portas, cartucho de RAM do Sega CD |
| Sega Saturn | `mednafen_saturn` | cartucho (memória de backup, RAM de 1 MB ou 4 MB), adaptador de 6 jogadores, Controle 3D, Virtua Gun, Stunner, Mouse, Arcade Racer, Mission Stick, Twin-Stick, teclado |
| PlayStation | `swanstation` | digital, DualShock, Analog Joystick, NeGcon, GunCon, mouse |
| PlayStation 2 (Android) | `armsx2` | entrada 1: cartão de PS2 (padrão 64 MB, o maior); entrada 2: **PocketStation** (cartão de PS1, padrão) ou cartão de PS2 de 8 a 64 MB |
| Game Boy Advance | `mgba` | sensor solar (Boktai), vibração do Game Boy Player, molduras e modelo do Super Game Boy |
| Game Boy / Color | `gambatte` | vibração dos cartuchos que têm motor |
| Pokémon mini | `pokemini` | vibração |
| Nintendo DS | `melonds` | microfone |
| Master System (SG-1000) | `gearsystem` | Light Phaser, Paddle, Sports Pad, óculos 3D |
| PC Engine | `mednafen_pce` | TurboTap de 5 controles, Arcade Card |
| 3DO | `opera` | Flightstick, mouse, pistolas, Orbatak |
| Amiga | `puae` | joystick, controle do CD32, Arcadia, pistola Phazer, caneta de luz |
| Commodore 64 | `vice_x64` | REU (até 16 MB), impressora, adaptador de joysticks |
| Atari 8 bits | `atari800` | memórias Axlon e Mosaic, impressora, paddles |
| Apple II | `applewin` | placas de expansão (Mockingboard, mouse, Z80 SoftCard...) |
| MSX | `bluemsx` | cartuchos de som SCC |
| Amstrad CPC | `cap32` | pistola Phazer e Gunstick |
| Arcade (MAME) / CD-i | `mame`, `same_cdi` | pistola de luz e mouse |

**Só os jogos feitos para o acessório respondem a ele.** Ligar o Rumble Pak não faz um jogo sem vibração vibrar, e
uma pistola de luz só mira em jogo de pistola. Por isso cada acessório do catálogo que depende do jogo traz o aviso
"só faz efeito nos jogos feitos para este acessório".

## O VMU e o PocketStation, dentro e fora do jogo

### VMU (Dreamcast)

- **Dentro do jogo** [Certo]: o Flycast desenha a telinha do VMU (48×32 pontos) por cima da imagem, **ao vivo**: o
  que o jogo mostra nela aparece ali. Dá para escolher o canto (os 4 cantos), o tamanho (1× a 5×), a transparência
  e o som. A posição é limitada aos 4 cantos: é o que o núcleo oferece (`reicast_vmu1_screen_position`). O que
  aparece na telinha é o jogo que decide (por exemplo, as jogadas escolhidas num jogo de futebol, as cartas do Sonic
  Shuffle); não conferi jogo a jogo [Palpite].
- **Fora do jogo, sozinho** [Certo]: novo console **VMU (Dreamcast)** no ARENA, pelo núcleo **VeMUlator** (GPLv3,
  Mahmoud Jaoune): abre minijogos `.vms`, saves `.dci` e cartões inteiros `.bin` (128 KB). **Não precisa de BIOS**
  (emulação de alto nível do chip Sanyo LC86K87). Controles: direcional, A, B, Start = MODE, Select = SLEEP. Limites
  do próprio núcleo: sem save state, o som pode sair fora de sincronia e fechar o conteúdo pode travar.
  Fontes: docs.libretro.com/library/vemulator e wiki.batocera.org/systems:vemulator.
- **Ligado ao jogo, um mudando o outro** [Certo, integrado no PC em 24/10/2026]: o Flycast tem o encaixe **"DreamPotato"** e a
  opção "DreamPotato VMU storage"; o **DreamPotato** (MIT, Rikki Gibson; Windows, Linux e macOS; em beta) é um VMU
  completo numa janela à parte que se liga ao Flycast por rede (TCP): a memória, a tela e os botões do VMU de lá
  passam a ser os do jogo. O README dele avisa que o Flycast 2.6 estável tem um defeito com ele e pede uma
  versão do ramo principal. **O zip do DreamPotato traz o `american_v1.05.bin`, a BIOS do VMU da Sega**
  (listei o zip): o ARENA **não pode** distribuí-lo; é um emulador de fora, que o professor baixa e põe em
  `emuladores\DreamPotato`, como o PCSX2. **Como usar:** Acessórios → Sega Dreamcast → "Controle 1: o que está encaixado nele" →
  Encaixe A1 = DreamPotato, e ligue "VMU: memória compartilhada com o DreamPotato". O ARENA abre o DreamPotato junto com o jogo
  e fecha com ele (`servidor\companheiros.py`; testado: abre, fica vivo e fecha). O do Rafael já está em `emuladores\DreamPotato`
  (zip conferido pela marca SHA-256, 24/10/2026). Só Windows e Linux: não existe para Android.

### PocketStation (PlayStation 1)

- **O que era** [Certo, Wikipedia]: acessório da Sony lançado só no Japão em 23/01/1999; um memory card com
  processador ARM7T (até 8 MHz), 2 KB de RAM, 128 KB de flash, tela de 32×32 pontos, 5 botões, infravermelho, relógio
  e alto-falante, bateria CR-2032. Os minijogos vinham dentro de jogos de PS1 e eram baixados para o cartão; ~87
  jogos compatíveis; descontinuado em 07/2002 com quase 5 milhões de unidades.
- **Fora do jogo** [Certo]: novo console **PocketStation** no ARENA, pelo núcleo **Pokket** (núcleo MIT, programas
  GPLv3, mentalfoundry): abre o cartão inteiro (`.mcd`, `.mcr`, `.gme`) ou um minijogo só (`.mcs`, `.pss`),
  mostra o relógio e o menu do aparelho, roda os minijogos e tem até a ligação por infravermelho entre dois
  PocketStation. **Precisa da BIOS do PocketStation (16 KB)**, firmware da Sony que não pode ir no ARENA. O `kernel.bin` de
  16 KB que o Rafael já tinha na pasta BIOS **é** uma BIOS de PocketStation: abre o relógio no Pokket, no PC e no
  celular [Certo: testado em 24/10/2026]. Pôr em `BIOS\PocketStation` (o ARENA reconhece pelo tamanho; copiado
  como `pocketstation.bin`). No Windows com acento no caminho ("Pedagógicos") o ARENA usa a ponte sem acento. O `.srm` que ele grava é um `.mcd`
  byte a byte, o mesmo formato do cartão de PS1.
- **No PS2** [Certo]: no celular, **a entrada 1 é o cartão de PS2 de 64 MB (o maior que o PCSX2 aceita; cabe todo save) e a
  entrada 2 é o PocketStation**, um cartão no formato do PS1 (128 KB), o mesmo formato que o Pokket lê, criado pelo ARENA
  (`PocketStation.mcr`, formatado e vazio, nunca trocado se já existir). É a mesma divisão do ARENA do computador
  (decisão do Rafael, 24/10/2026). **Confirmado no celular (foto da tela):** com um cartão de PS1 numa entrada, o
  Browser da BIOS do PS2 mostra **"PocketStation/<entrada>"** com o desenho do aparelho; é o nome que a própria BIOS dá
  a um cartão no formato do PS1.
  **Atenção, premissa a corrigir:** o PocketStation não "roda" dentro da BIOS do PS2. Nem o PCSX2 nem o ARMSX2
  emulam o aparelho; o que existe é o cartão no formato certo. E **jogo de PS2 não salva em cartão de PS1**: ele salva
  na entrada 1. Os cartões são o mesmo arquivo em qualquer entrada (o nome segue o tamanho: `Mcd001-64MB.ps2`).
  **Seus saves antigos** continuam no cartão de 8 MB (`Mcd001.ps2`); para trazê-los: em Acessórios → PlayStation 2 ponha
  a entrada 2 em "Cartão do PS2 de 8 MB", abra a BIOS (Browser), copie os saves da entrada 2 para a 1 e volte a
  entrada 2 para o PocketStation.
- **Ligado ao jogo ao vivo** [Certo; feito em 24/10/2026, só Windows]: só o **PokketSX** (GPLv3; fork do DuckStation de
  antes de a licença dele fechar; só Windows x64). Cada entrada de cartão tem uma caixinha para pôr o PocketStation no
  lugar do cartão comum, e o jogo de PS1 conversa com ele pelo protocolo do cartão: é assim que o jogo baixa o minijogo
  para o aparelho. É o único jeito conhecido de o jogo de PS1 falar com o PocketStation. Não vai para Android, Linux nem
  Chromebook (sem versão para eles).
  **Premissa a corrigir:** o PokketSX **não mostra a telinha, não toca o som e não liga os botões** do PocketStation.
  O núcleo dele tem essas funções (tela de 32×32, áudio de 8 kHz, cinco botões), mas nada da janela as usa: o aparelho
  roda "por dentro" do cartão [Provável: lido no código-fonte do PokketSX em 24/10/2026, por busca de texto em `src\`;
  não li os `.c` do núcleo]. O que o jogo faz com o PocketStation fica no cartão; para **ver** e **jogar** o minijogo na
  telinha, o cartão tem que abrir no console **PocketStation** do ARENA (núcleo Pokket): ver "Cartão único", abaixo.
  **Como usar:** abra um jogo de PlayStation e, na pergunta "Como ligar o PlayStation?", escolha **PokketSX (com
  PocketStation)** (marque "lembrar" se quiser; Ajustes → Emuladores troca depois). Ele só aparece na pergunta se
  `emuladores\PokketSX` existir; o PlayStation segue sendo do RetroArch (Jogar Junto, vários discos e o resto não mudam;
  no Jogar Junto a escolha lembrada do PokketSX não vale). **O que o ARENA faz sozinho** (`servidor\pokketsx.py`): leva
  a BIOS do PlayStation e a do PocketStation para `emuladores\PokketSX\bios`, põe o cartão
  do PocketStation (128 KB, formatado, nunca trocado) na **entrada 2** (a 1 fica com o cartão comum de cada jogo; a mesma
  divisão do PS2; o cartão é o "cartão único", abaixo), grava o `settings.ini` sem o assistente de configuração, sem
  confirmar ao fechar, sem atualizador nem Discord, e abre em tela cheia com `-batch` (o programa fecha junto com o
  jogo). **F10 fecha o jogo.** Um jogador só.
  **Cartão único** [Certo, feito e testado em 25/10/2026]: o cartão da entrada 2 do PokketSX e o do console PocketStation
  (Pokket) são **o mesmo arquivo**, `retroarch\saves\Pokket\Meu PocketStation.srm`: o PokketSX recebe o caminho relativo
  no `Card2Path` (`..\..\..\retroarch\saves\Pokket\Meu PocketStation.srm`, que ele junta à pasta `memcards` dele),
  e o Pokket usa o `.srm` como o cartão inteiro (ele o lê no começo e o grava de volta no fim). **Não há cópia entre os
  dois**, então nada fica dessincronizado: o minijogo que o jogo de PS1 baixa no PokketSX aparece no menu do
  PocketStation do Pokket, e o que se faz no Pokket vale na próxima vez que o PokketSX abrir. O ARENA cria o cartão
  vazio e o "jogo" **Meu PocketStation** (`jogos\pessoais\PocketStation\Meu PocketStation.mcd`, um cartão vazio só para
  o console PocketStation ter o que abrir) na primeira vez que se escolhe o PokketSX, e **guarda uma cópia de segurança**
  em `retroarch\saves\Pokket\copias` (as 5 mais novas, só quando o cartão mudou) antes de o PokketSX ou o Pokket abrirem
  esse cartão. Quem já tinha um `memcards\PocketStation.mcd` com coisa dentro não perde nada: ele vira o cartão único
  na primeira vez. Os outros jogos do console PocketStation (os 110 `.gme`) seguem cada um com o seu cartão.
  **O PS2 fica de fora de propósito:** o PCSX2 e o ARMSX2 não emulam o aparelho, só deixam um cartão no formato do PS1 na
  entrada (o `PocketStation.mcr`); não há "dentro" que valha para o PS2.
  **Testado em 24/10/2026** [Certo]: abre o Crash Bandicoot e o Legacy of Kain pela rota `/api/jogar` de uma cópia do
  ARENA numa pasta com acento (`testes\teste_pokketsx_pelo_arena.py`: 5 passos, tudo certo); o registro do próprio
  PokketSX diz `Memory Card Slot 2: PocketStation started from ...\bios\pocketstation.bin`. O `kernel.bin` do Rafael tem
  MD5 `3bcdcef3...d11c8`, diferente do dump "conhecido" que o PokketSX prefere (`d3dc54ef...e5ae`): ele só avisa e usa
  assim mesmo (qualquer arquivo de 16 KB serve). **Não testado:** o jogo conversando de fato com o PocketStation (nenhum
  jogo de PS1 desta pasta usa o PocketStation: precisa de um dos ~87 compatíveis, como o Final Fantasy VIII) e o
  controle de verdade (os nomes dos botões SDL foram escritos pelo código do PokketSX; o teste com controle fica para o fim).

## Premissas corrigidas

- **"No ARENA do PC o PocketStation já está na entrada 1."** Não [Certo]: no PC ele está na **2**. A entrada 1 é um cartão de PS2 de
  64 MB (`Memory Card Slot 1.ps2`) e a entrada 2 é um cartão de PS1 de 128 KB (`Memory Card Slot 2.mcr`), vazio. O celular agora
  segue a mesma divisão (decisão de 24/10/2026). O
  `pcsx2-qt.exe` 2.8.2 não tem a palavra "PocketStation" (busca de texto), mas as BIOS do PS2 que o ARENA usa
  (30004R V6 e SCPH-70004 V12) têm o texto "PocketSt…", e no celular o Browser da BIOS escreve "PocketStation" para
  um cartão de PS1: o nome que você viu vem da BIOS do console, que chama assim o cartão de PS1 que estiver na
  entrada. No PC esse cartão é o da entrada 2. O PC não foi mudado (dado seu).
- **"O 32X melhora os gráficos dos jogos do Mega Drive."** Não [Provável]: o 32X é uma peça que roda os **seus
  próprios** jogos (cartuchos de 32X); os jogos comuns do Mega Drive ficam iguais. O ARENA tem o console **Sega 32X**
  (PicoDrive) para esses jogos.
- **"O roteador (adaptador de rede)."** Existe no Dreamcast (Broadband Adapter, no Flycast) e fica **desligado por
  padrão** e avisado, por segurança dos alunos menores. A gravação de vídeo e a transmissão continuam desligadas.
- **Rumble, Controller Pak, pistola de luz:** nem todo jogo tinha o recurso. O ARENA liga o acessório; quem usa é o
  jogo.

## Como confirmar de novo (quando um núcleo mudar)

```
servidor\python\python.exe ferramentas\levantar_opcoes_dos_nucleos.py --saida opcoes_dos_nucleos.json
servidor\python\python.exe ferramentas\conferir_acessorios.py opcoes_dos_nucleos.json
```

Núcleos que só declaram as opções depois de abrir um jogo (fceumm, fbneo, dolphin, mame2003, bsnes2014) vêm sem
opções nessa leitura; os tipos de controle por porta deles (como Zapper e Power Pad do NES) vêm normalmente.

## Pendências desta frente

1. ~~DreamPotato~~ **Feito** (programa companheiro); falta testar com um jogo de Dreamcast de verdade no PC do Rafael.
2. ~~**PokketSX** como emulador de fora do PS1~~ **Feito em 24/10** (um jeito a mais de abrir o PS1; ver acima). Falta
   testar com um jogo que use o PocketStation e com controle de verdade. (Instalado em `emuladores\PokketSX`: modo portátil,
   sem o atualizador, Discord desligado; zip sha256 `ce7cdb2b...f74c`.)
3. ~~**Cartão único** entre o PokketSX e o Pokket~~ **Feito em 25/10** (um arquivo só, com cópia de segurança; ver acima). O PS2
   fica de fora de propósito (não emula o aparelho).
4. Testar o Pokket (precisa do `pocketstation.bin` do Rafael) e o VeMUlator (precisa de um `.vms`) no celular.
5. Os núcleos que declaram as opções tarde (lista acima): ler as opções abrindo um jogo.
6. Conferir os códigos de controle que o ARENA manda ao Saturn e ao PS1: o `517` aparece nos núcleos como
   **Arcade Racer** (Saturn) e **Analog Joystick** (SwanStation); o controle de PS1 analógico do SwanStation é o
   `261` e o do Saturn é o `261` (Controle 3D) [Certo: lista dos núcleos]. Não mexi: precisa de teste com controle real.

## Fontes

- Pokket: github.com/mentalfoundry/Pokket (README, docs/libretro_readme.md) e o `pokket_libretro.info` do libretro.
- PokketSX: github.com/mentalfoundry/PokketSX.
- VeMUlator: docs.libretro.com/library/vemulator; wiki.batocera.org/systems:vemulator.
- DreamPotato: github.com/RikkiGibson/DreamPotato (README, releases).
- PocketStation: en.wikipedia.org/wiki/PocketStation; psx-spx.consoledev.net/pocketstation.
- Opções e tipos de controle: perguntados aos próprios núcleos do ARENA (196 núcleos, 24/10/2026).
- Levantamento por IA (7 pesquisadores, modelo rápido) usado só como lista de nomes; a lista abaixo é dele e
  **precisa de revisão**, cada item com a confiança que ele mesmo marcou.

## O que ainda não se liga (levantamento automático, a revisar)

### ZX Spectrum

- **Joystick (Kempston, Sinclair, Cursor, Fuller)** (só o controle é mapeado (sem o acessório de verdade)): Interfaces de joystick do Spectrum [Provável] — https://docs.libretro.com/library/fuse/
- **Botões do joypad para teclado** (só o controle é mapeado (sem o acessório de verdade)): Mapeamento do joypad para teclas do Spectrum [Certo] — https://docs.libretro.com/library/fuse/
- **Interface Beta 128 / Disciple / DivMMC** (nenhum núcleo emula): Interfaces de disco e expansão de memória Ideia: Lacuna: pesquisar chave completa e valores . [Palpite]

### Amstrad CPC

- **Combo de teclas no joystick** (só o controle é mapeado (sem o acessório de verdade)): Combinação de teclas acionada pelo controle [Palpite]

### PC (DOS)

- **Joystick (tempo e zona morta)** (só o controle é mapeado (sem o acessório de verdade)): Joystick analógico do DOS [Certo] — https://docs.libretro.com/library/dosbox_pure/

### ScummVM

- **Controle analógico e cursor** (só o controle é mapeado (sem o acessório de verdade)): Cursor e velocidade do joystick [Palpite]

### Celulares Java ME (FreeJ2ME)

- **Teclado analógico como teclado numérico** (só o controle é mapeado (sem o acessório de verdade)): Analógico do controle como teclado do celular [Palpite]

### WASM-4

- **Tela sensível ao toque** (só o controle é mapeado (sem o acessório de verdade)): Toque simulado na tela do WASM-4 [Palpite]

### Atari 2600

- **Starpath Supercharger** (nenhum núcleo emula): Unidade que carrega jogos de fita de audio pelo 2600, com RAM extra Ideia: Lista de jogos do Supercharger em arquivo .bin normal, se o nucleo aceitar . [Palpite] — https://docs.libretro.com/library/stella/

### Atari 5200

- **Trak-Ball e Paddles** (nenhum núcleo emula): Esfera e controles giratorios do 5200 (Missile Command, Centipede) Ideia: Mapear o analogico para os eixos do mouse ou usar o Stella (2600) quando o jogo for do 2600 . [Palpite] — https://docs.libretro.com/library/a5200/

### Atari 7800

- **Light Gun (7800)** (nenhum núcleo emula): Pistola de luz do 7800 para jogos de tiro Ideia: Mapear o mouse ou analogico para mira em jogos de tiro do 7800 . [Palpite] — https://docs.libretro.com/library/prosystem/
- **Atari 7800 XM (modulo)** (nenhum núcleo emula): Modulo de expansao do 7800 com memoria e jogos especiais [Palpite] — https://docs.libretro.com/library/prosystem/

### Atari Lynx

- **ComLynx (cabo de link)** (nenhum núcleo emula): Cabo que liga dois Lynx para jogo a dois Ideia: Partida a dois pelo netplay do RetroArch (estado), como o ARENA ja faz em outros consoles . [Certo] — https://docs.libretro.com/library/handy/
- **Team Tap / multijogador por acessorio** (nenhum núcleo emula): Adaptador de multiplos jogadores no Lynx [Palpite] — https://docs.libretro.com/library/handy/

### Atari Jaguar

- **Teclado numerico (Keypad)** (só o controle é mapeado (sem o acessório de verdade)): Teclado numerico do controle do Jaguar [Provável] — https://docs.libretro.com/library/virtual_jaguar/

### Atari ST

- **Impressora e MIDI** (nenhum núcleo emula): Impressora paralela e interface MIDI do Atari ST [Palpite] — https://docs.libretro.com/library/hatari/

### ColecoVision

- **Teclado numerico do Coleco (Keypad)** (só o controle é mapeado (sem o acessório de verdade)): Teclado numerico do controle do ColecoVision [Provável] — https://docs.libretro.com/library/gearcoleco/
- **Teclado ADAM (computador)** (só o controle é mapeado (sem o acessório de verdade)): Teclado do computador ADAM, da mesma familia do ColecoVision [Provável] — https://docs.libretro.com/library/gearcoleco/
- **Expansion Module #1** (nenhum núcleo emula): Modulo que permite jogos de Atari 2600 e Coleco no ColecoVision Ideia: Lancar jogo de 2600 pelo Stella, como programa separado no ARENA . [Palpite] — https://docs.libretro.com/library/gearcoleco/

### Intellivision

- **Teclado numerico (keypad)** (só o controle é mapeado (sem o acessório de verdade)): Teclado numerico do controle do Intellivision [Provável] — https://docs.libretro.com/library/freeintv/
- **Disco (disc)** (só o controle é mapeado (sem o acessório de verdade)): Disco de 16 direcoes do controle do Intellivision [Provável] — https://docs.libretro.com/library/freeintv/
- **Intellivoice** (nenhum núcleo emula): Modulo de voz que fala com sintese no Intellivision [Palpite] — https://docs.libretro.com/library/freeintv/
- **ECS (Entertainment Computer System)** (nenhum núcleo emula): Teclado e expansao de computador do Intellivision Ideia: Teclado virtual no ARENA, se algum dia houver jogo que pede o ECS . [Certo] — https://docs.libretro.com/library/freeintv/

### Vectrex

- **Light pen e 3D Imager** (nenhum núcleo emula): Caneta optica e oculos 3D do Vectrex Ideia: Mapear o mouse como caneta, ou o efeito 3D por opcao de video, se o nucleo aceitar . [Palpite] — https://docs.libretro.com/library/vecx/

### Magnavox Odyssey 2

- **Teclado do Odyssey 2** (só o controle é mapeado (sem o acessório de verdade)): Teclado de 49 teclas do Odyssey 2 [Provável] — https://docs.libretro.com/library/o2em/

### Thomson (MO/TO)

- **Caneta optica (light pen)** (só o controle é mapeado (sem o acessório de verdade)): Caneta que aponta direto na tela do Thomson [Provável] — https://docs.libretro.com/library/theodore/

### Apple II

- **Super Serial Card** (nenhum núcleo emula): Placa serial para modem e impressora do Apple II [Palpite] — https://docs.libretro.com/library/applewin/

### PC Engine / TurboGrafx-16 (e CD-ROM²)

- **Memory Base 128 (backup de 128 KB)** (só o controle é mapeado (sem o acessório de verdade)): Cartão de memória extra para salvar jogos de CD; o Backup RAM do CD-ROM² já traz 2 KB, o Memory Base 128 traz 128 KB Ideia: Um arquivo de save com o backup pode ser copiado manualmente para a pasta de saves . [Palpite] — https://docs.libretro.com/library/mednafen_pce/

### NEC PC-FX

- **Multitap PC-FX** (nenhum núcleo emula): Adaptador para mais de dois controles no PC-FX Ideia: Usar dois controles em porta separada, sem multitap . [Palpite] — https://docs.libretro.com/library/beetle_pc_fx/

### Neo Geo (AES/MVS) e Neo Geo CD

- **Cartão de memória do Neo Geo** (nenhum núcleo emula): Cartão que guarda o save do Neo Geo AES/MVS Ideia: Save em arquivo na pasta do núcleo, sem cartão . [Palpite] — https://docs.libretro.com/library/fbneo/

### Neo Geo Pocket / Color

- **Cabo link (link cable)** (nenhum núcleo emula): Cabo para trocar dados ou jogar com outro Neo Geo Pocket Ideia: Partida a dois só pelo netplay do RetroArch, se o núcleo permitir . [Palpite] — https://docs.libretro.com/library/beetle_ngp/

### WonderSwan / WonderSwan Color

- **Cabo link (WonderSwan)** (nenhum núcleo emula): Cabo para jogos de dois WonderSwan Ideia: Sem solução confirmada . [Palpite] — https://docs.libretro.com/library/beetle_wonderswan/

### 3DO

- **Flightstick** (nenhum núcleo emula): Manche de voo para jogos de simulação 3DO Ideia: Mapear o analógico do controle de jogo para o manche (remapeamento no RetroArch) . [Palpite] — https://docs.libretro.com/library/opera/

### Philips CD-i

- **Mouse / trackball / arma (CD-i)** (nenhum núcleo emula): Mouse, trackball ou pistola de luz oficiais do CD-i Ideia: Mapear o analógico para o ponteiro, sem precisão . [Provável] — https://docs.libretro.com/library/same_cdi/

### Arcade (MAME)

- **Volante e pedais** (só o controle é mapeado (sem o acessório de verdade)): Volante e pedais de jogos de corrida de arcade Ideia: Mapear o analógico do controle para o volante . [Palpite] — https://docs.libretro.com/library/fbneo/

### Xbox 360 (Xenia, externo)

- **Kinect** (nenhum núcleo emula): Sensor de movimento e câmera do Xbox 360 Ideia: Sem solução confirmada . [Palpite] — https://github.com/xenia-project/xenia
- **Volante (wheel)** (só o controle é mapeado (sem o acessório de verdade)): Volante oficial para jogos de corrida [Palpite] — https://github.com/xenia-project/xenia
- **Guitarra e bateria (Rock Band / Guitar Hero)** (nenhum núcleo emula): Controles musicais oficiais do Xbox 360 Ideia: Mapear botões do controle padrão . [Palpite] — https://github.com/xenia-project/xenia
- **Headset / microfone** (nenhum núcleo emula): Fone com microfone para jogo em rede Ideia: Sem solução confirmada . [Palpite] — https://github.com/xenia-project/xenia

### Super Nintendo / Super Famicom

- **Multitap (5 jogadores)** (só o controle é mapeado (sem o acessório de verdade)): Adaptador que liga quatro ou cinco controles numa porta do SNES [Certo] — https://docs.libretro.com/library/snes9x/
- **SNES Mouse** (só o controle é mapeado (sem o acessório de verdade)): Mouse oficial do SNES, usado em Mario Paint [Certo] — https://docs.libretro.com/library/snes9x/
- **Super Game Boy (adaptador para jogos de Game Boy)** (nenhum núcleo emula): Cartucho que roda jogos de Game Boy no SNES, com moldura e paletas Ideia: Rodar o jogo de Game Boy no núcleo de Game Boy do RetroArch, separado . [Palpite] — https://docs.libretro.com/library/snes9x/

### Nintendo 64

- **N64 Mouse** (nenhum núcleo emula): Mouse oficial do N64, usado em alguns jogos Ideia: Mapear o ponteiro do mouse do PC para o analógico . [Palpite] — https://docs.libretro.com/library/mupen64plus-next/ (404)
- **VRU (reconhecimento de voz)** (nenhum núcleo emula): Unidade de reconhecimento de voz do Japão (Hey You, Pikachu!) Ideia: Simular o microfone com as frases do jogo, no teclado . [Palpite] — https://docs.libretro.com/library/mupen64plus-next/ (404)
- **64DD (drive de disco)** (nenhum núcleo emula): Drive de disco magnético do Japão, para jogos próprios [Palpite] — https://docs.libretro.com/library/mupen64plus-next/ (404)

### GameCube

- **GBA Link Cable (cabo para Game Boy Advance)** (nenhum núcleo emula): Cabo que liga o GameCube ao Game Boy Advance, para jogos integrados Ideia: Rodar o GBA em núcleo separado e unir pelo mesmo jogo . [Palpite] — https://docs.libretro.com/library/dolphin/
- **Broadband Adapter (rede)** (nenhum núcleo emula): Adaptador de banda larga (Ethernet) para jogos online do GameCube Ideia: Partida a dois local pelo Jogar Junto do ARENA, sem internet . [Palpite] — https://docs.libretro.com/library/dolphin/
- **WaveBird (controle sem fio)** (só o controle é mapeado (sem o acessório de verdade)): Controle sem fio oficial do GameCube, por rádio [Palpite] — https://docs.libretro.com/library/dolphin/
- **Bongos (Donkey Konga)** (só o controle é mapeado (sem o acessório de verdade)): Par de tambores de mão para Donkey Konga Ideia: Mapear os tambores no teclado . [Palpite] — https://docs.libretro.com/library/dolphin/
- **Microfone (GameCube)** (nenhum núcleo emula): Microfone para jogos como Gamecube Mic de Animal Crossing e Dr. Mario Ideia: Simular com tecla de ação no teclado . [Palpite] — https://docs.libretro.com/library/dolphin/
- **Tapete de dança (Dance Dance Revolution pad)** (nenhum núcleo emula): Tapete de dança para jogos de ritmo no GameCube Ideia: Mapear as setas do tapete no teclado . [Palpite] — https://docs.libretro.com/library/dolphin/

### Wii

- **Wii Speak (microfone USB)** (nenhum núcleo emula): Microfone com teclas para conversar em jogos de Wii, como Wii Party Ideia: Simular com tecla de ação no teclado . [Palpite] — https://docs.libretro.com/library/dolphin/

### Game Boy e Game Boy Color

- **Game Boy Printer** (nenhum núcleo emula): Impressora térmica que imprime as fotos e textos dos jogos Ideia: Converter o que o jogo envia para PNG com um programa à parte; não testado . [Palpite] — https://docs.libretro.com/library/gambatte/
- **Game Boy Camera** (nenhum núcleo emula): Cartucho com câmera e impressora embutidas Ideia: Usar a webcam do PC num cartucho virtual não é suportado pelo núcleo; lacuna . [Palpite] — https://docs.libretro.com/library/gambatte/
- **Game Boy Player** (nenhum núcleo emula): Acessório do GameCube que roda jogos de Game Boy e GBA Ideia: Lacuna: não verificado se o Dolphin roda essa parte . [Palpite] — https://docs.libretro.com/library/mgba/

### Game Boy Advance

- **e-Reader** (nenhum núcleo emula): Leitor de cartões de Pokémon (e-Card) que liga pela porta de link Ideia: Lacuna: o cartão é a parte que mais falta; sem cartão original não há como testar . [Palpite] — https://docs.libretro.com/library/mgba/
- **Adaptador sem fio (Wireless Adapter)** (nenhum núcleo emula): Adaptador de rádio para jogar sem fio entre GBAs Ideia: Partida a dois via rede do ARENA (Jogar Junto) é outra coisa; não substitui . [Palpite] — https://docs.libretro.com/library/mgba/

### Nintendo DS

- **Rumble Pak do DS** (nenhum núcleo emula): Acessório de vibração que se encaixa no slot GBA do DS, usado em Metroid Prime Hunters Ideia: Vibração do controle do PC, se houver; não testado . [Provável] — https://docs.libretro.com/library/melonds_ds/
- **Slot GBA do DS (cartucho de GBA)** (nenhum núcleo emula): Slot de cima do DS que aceita cartucho de GBA para jogos de GBA ou add-on Ideia: Rodar GBA pelo mGBA em outra janela; é outro emulador . [Provável] — https://docs.libretro.com/library/melonds_ds/
- **Guitar Grip** (nenhum núcleo emula): Guitarra de plástico do Guitar Hero no slot GBA do DS Ideia: Mapear um controle de guitarra USB do PC; sem teste . [Palpite] — https://docs.libretro.com/library/melonds_ds/

### Pokémon Mini

- **Pedômetro** (nenhum núcleo emula): Acessório que conta passos e libera conteúdo nos jogos da série Pokémon Mini Ideia: Sensor de passos pelo celular seria outro app; sem teste . [Provável] — https://docs.libretro.com/library/pokemini/

### SG-1000

- **Teclado SC-3000** (nenhum núcleo emula): Teclado do computador SC-3000, familia SG-1000 Ideia: Mapear teclado do PC para o joystick, sem o programa de digitacao . [Palpite] — https://docs.libretro.com/library/gearsystem/

### Mega Drive / Genesis

- **Activator** (nenhum núcleo emula): Controle infravermelho de corpo inteiro, de 1993 Ideia: Mapear sensor de movimento ou teclado para os botoes do Activator . [Palpite] — https://docs.libretro.com/library/genesis_plus_gx/
- **Modem Mega Modem** (nenhum núcleo emula): Modem para jogar pela linha telefonica (pouco usado no Brasil) Ideia: Partida a dois pelo Jogar Junto do ARENA, sem modem . [Palpite] — https://docs.libretro.com/library/genesis_plus_gx/

### Sega Saturn

- **Sega NetLink (modem)** (nenhum núcleo emula): Modem para internet e jogos online no Saturn Ideia: Partida a dois pelo Jogar Junto do ARENA . [Palpite] — https://en.wikipedia.org/wiki/Sega_Saturn

### Dreamcast

- **Fishing Controller** (só o controle é mapeado (sem o acessório de verdade)): Vara de pesca com molinete, para Sega Bass Fishing Ideia: Mapear o analogico do controle para o movimento da vara . [Palpite] — https://en.wikipedia.org/wiki/Dreamcast_accessories
- **Maracas** (só o controle é mapeado (sem o acessório de verdade)): Maracas do Samba de Amigo Ideia: Mapear sensores do controle ou botoes para as maracas . [Palpite] — https://en.wikipedia.org/wiki/Dreamcast_accessories
- **Microfone (VMU)** (nenhum núcleo emula): Microfone que liga ao controle para comando por voz e chat Ideia: Entrada de audio do PC substituindo o microfone, se o jogo permitir . [Palpite] — https://en.wikipedia.org/wiki/Dreamcast_accessories
- **Broadband Adapter / Modem** (nenhum núcleo emula): Adaptador de internet para o Dreamcast Ideia: Partida a dois pelo Jogar Junto do ARENA, sem a rede do Dreamcast . [Palpite] — https://en.wikipedia.org/wiki/Dreamcast_accessories
- **Dreameye (camera)** (nenhum núcleo emula): Camera digital para fotos e videochamada Ideia: Webcam do PC mostrada num programa a parte, sem o jogo . [Palpite] — https://en.wikipedia.org/wiki/Dreamcast_accessories
- **Arcade Stick (luta)** (só o controle é mapeado (sem o acessório de verdade)): Joystick de arcade para jogos de luta Ideia: Mapear o arcade stick USB como controle do jogador . [Palpite] — https://en.wikipedia.org/wiki/Dreamcast_accessories
- **Volante (corrida)** (só o controle é mapeado (sem o acessório de verdade)): Volante de terceiros (Mad Catz, Agetec) para corrida Ideia: Mapeamento de volante USB pelo RetroArch . [Palpite] — https://en.wikipedia.org/wiki/Dreamcast_accessories

### PlayStation

- **Cabo de link (PS1 a PS1)** (nenhum núcleo emula): Cabo que liga dois PS1 para jogos de dois consoles Ideia: Partida a dois por netplay (já existe no ARENA), em vez de cabo . [Palpite] — https://docs.libretro.com/library/pcsx_rearmed/

### PlayStation 2

- **EyeToy (câmera USB)** (nenhum núcleo emula): Câmera USB para jogos de movimento Ideia: Webcam do computador com sobreposição de vídeo. Mapear o movimento para o controle é outro caminho . [Palpite] — https://docs.libretro.com/library/pcsx2/
- **Microfone (SingStar)** (nenhum núcleo emula): Microfone USB para jogos de canto Ideia: Microfone do computador com o áudio passando pelo jogo, se o núcleo aceitar . [Palpite] — https://docs.libretro.com/library/pcsx2/

### PlayStation Portable

- **GPS (USB)** (só o controle é mapeado (sem o acessório de verdade)): Receptor GPS USB para jogos com localização [Palpite] — https://docs.libretro.com/library/ppsspp/
- **Microfone (PSP)** (só o controle é mapeado (sem o acessório de verdade)): Microfone do PSP para jogos de voz Ideia: Microfone do computador, se o núcleo aceitar . [Palpite] — https://docs.libretro.com/library/ppsspp/
- **Câmera (PSP Go, USB)** (nenhum núcleo emula): Câmera USB do PSP Ideia: Webcam do computador como sobreposição, se for preciso . [Certo] — https://docs.libretro.com/library/ppsspp/

