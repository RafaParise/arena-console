# O ARENA no Chromebook — item 12 (17/10/2026)

O pedido do Rafael (15/10/2026): "o ARENA deve ser compatível se possível
com Chromebooks que tem na escola, se para ser mais assertivo seja melhor eu
rodar um teste dentro do chromebook deixamos para depois mas o que puder ir
adiantando do projeto pode fazer por gentileza. Se for melhor, mais otimizado
e leve crie uma versão para Chromebook, se não fizer tanta diferênça o ARENA
deve saber reconhecer e rodar nos dois sistemas operacionais."

**Resposta curta:** fiz a versão para Chromebook, porque ela é mais leve e é
a única que roda num Chromebook gerenciado. É o **mesmo ARENA**: a mesma
tela, o mesmo RetroArch (1.22.2), os mesmos núcleos, as mesmas teclas, o
mesmo save. Ela roda dentro do próprio Chrome, aberta do pen drive, sem
instalar nada. O mesmo pen drive serve aos dois: no Windows, o `ARENA.bat`;
no Chromebook, o `ARENA-CHROMEBOOK.html`. Falta só o teste no Chromebook da
escola (seção "O teste no Chromebook da escola", no fim).

## Os três jeitos de um Chromebook rodar programa

| Jeito | O que é | No Chromebook da escola |
|---|---|---|
| **No Chrome** (página da web) | o próprio navegador | funciona em qualquer Chromebook (salvo bloqueio do administrador: a tabela no fim) |
| Android (Play Store) | aplicativos de celular | só os que o administrador libera; APK de fora, só com política do administrador |
| Linux (Crostini, e o novo Baguette) | uma máquina virtual com Debian | o administrador desliga por padrão; e mesmo ligado, o Google não dá mais suporte à aceleração gráfica nele, e, pelos relatos de quem tentou, o controle de jogo não chega ao Linux |

As fontes estão no fim. Pelo Linux, o ARENA para Linux (item 13) rodaria,
mas devagar (sem placa de vídeo), sem controle e só onde o administrador
ligou o Linux. Pelo Android, depende do item 14 e do administrador. **No
Chrome, roda em qualquer Chromebook**, com a placa de vídeo de verdade
(WebGL) e o controle (Gamepad API).

## Por que ficou mais leve

- Nada de máquina virtual (o Linux do Chromebook reserva memória e disco
  para um Debian inteiro).
- A tela do ARENA no navegador pesa **o mesmo** que a do Windows: no Edge,
  com janela, depois de assentar, **284 MB** as duas (medido do mesmo jeito,
  no mesmo Edge, em 17/10/2026; os números com jogo aberto estão abaixo).
- O emulador abre num quadro que some inteiro quando o jogo fecha: o
  navegador devolve toda a memória do jogo de uma vez.
- Os núcleos vão compactados: os 34 ocupam **91 MB** no pen drive.

## Como funciona

```
ARENA-CHROMEBOOK.html            a entrada: abre launcher\index.html
launcher\index.html, app.js      a MESMA tela do Windows
launcher\navegador\
  servidor.js   no Windows não faz nada; aberto do pen drive (file://),
                carrega o resto e atende os pedidos /api/ da tela
  rotas.js      as mesmas respostas do servidor\arena.py, feitas no navegador
  dados.js      o que o servidor sabe (consoles, opções do RetroArch e dos
                núcleos, BIOS), gerado do próprio servidor
                (ferramentas\montar_navegador.py; um teste avisa se esquecer)
  banco.js      ajustes, saves e recordes guardados no navegador (IndexedDB)
  pasta.js      lê e grava a pasta do ARENA no pen drive
  partida.js    abre o jogo por cima da tela, em tela cheia
  jogo.html/.js o quadro do jogo: o RetroArch 1.22.2 em WebAssembly
  tela.js       o aviso da pasta, o Testar este Chromebook, o Guardar um jogo
  nucleos\      os 34 núcleos (ferramentas\preparar_nucleos_navegador.py)
  livres.js     os 5 jogos livres que vêm junto
```

- **Os núcleos:** os do próprio libretro, compilados por eles para
  WebAssembly (`buildbot.libretro.com/stable/1.22.2/emscripten`, 715 MB com
  91 núcleos; a ferramenta confere a marca SHA-256 do arquivo). Aberta do
  pen drive, a página não pode ler arquivo com `fetch` nem abrir módulo
  JavaScript, então a ferramenta converte cada núcleo: o programa vira
  script comum e o emulador (`.wasm`) vai compactado em base64 num `.js`.
- **A lista de jogos:** a mesma do Windows. O indexador do Windows passa a
  gravar, ao lado do `dados\manifesto.json`, o `dados\manifesto.js`, que a
  página do pen drive lê sem pedir nada. Pen drive montado só no
  Chromebook: o ARENA faz a lista sozinho (pela pasta de cada console, como
  o indexador). As capas são as de `retroarch\thumbnails`.
- **A pasta do pen drive:** para abrir os jogos, o navegador só entrega um
  arquivo que a pessoa escolheu. Então, uma vez, o aluno escolhe a pasta do
  ARENA (o aviso no alto da lista pede). No Chrome e no Edge, o ARENA
  lembra; nos outros dias, um clique em "Permitir". No Firefox, que não tem
  o seletor de pasta, o campo de pasta lê os jogos (e os saves ficam no
  navegador).
- **O save é o mesmo do Windows:** com a pasta liberada, o save vai para
  `retroarch\saves\<núcleo>` no pen drive, no mesmo arquivo que o Windows
  usa (o nome da pasta de cada núcleo é o `corename` do `.info`, conferido
  por `servidor\tests\test_navegador_dados.py`). No PS1, o navegador usa o
  PCSX ReARMed; o cartão de memória do SwanStation (o do Windows) vale
  também, quando o PCSX ReARMed ainda não tem um daquele jogo.
- **As teclas e o menu:** as do Windows (`arena.BASE_COMUM`): Esc abre o
  menu do RetroArch em português, F2 salva, F4 carrega, F10 fecha. Em tela
  cheia, o Esc fica com o jogo; para sair da tela cheia, segure o Esc. A
  faixa no alto (aparece ao mexer o mouse) tem o "Voltar ao ARENA".
- **Gravação e transmissão:** continuam desligadas, as mesmas opções do
  Windows.

## O que tem e o que não tem no Chromebook

**Tem, e o teste prova** (`testes\teste_chromebook.py`): a lista (a do
Windows ou a feita no Chromebook), as capas, o apelido e a foto, os
recordes, o save do próprio jogo e os 10 espaços de save state (no
navegador e no pen drive), a BIOS que estiver no pen drive (Sega CD e Neo
Geo), a pasta do pen drive, o "Guardar um jogo neste navegador" e o
"Testar este Chromebook".

**Também tem**, porque é a mesma tela do Windows (o teste dos navegadores
do item 11 prova lá): a busca, os favoritos e os recentes, o tema e o fundo
animado, o tempo de jogo nos recordes.

**Feito, mas só se prova no Chromebook ou com controle na mão:** o
controle (a Gamepad API, que o quadro do jogo recebe), dois jogadores no
mesmo Chromebook (cada controle é um jogador; o teclado é o primeiro), o
jogo de vários discos (a lista `.m3u`, como no Windows), o som e a tela
cheia de verdade.

**Consoles (35 dos 66):** NES, Super Nintendo, Game Boy e Game Boy Color,
Game Boy Advance, Mega Drive/Master System/Game Gear, Sega CD, 32X,
SG-1000, PlayStation, Neo Geo e fliperamas (FBNeo), Neo Geo Pocket, PC
Engine, WonderSwan, Virtual Boy, Atari Lynx, Game & Watch, ColecoVision,
Odyssey 2, Vectrex, 3DO, os Commodore (64, 128, VIC-20, Plus/4, PET),
Thomson, ScummVM, Tamagotchi, TIC-80, WASM-4, LowRes NX, Uzebox, CHIP-8,
Arduboy e MicroW8.

**Fica só no Windows**, e a tela diz isso no console:

- os consoles sem núcleo para navegador no libretro: Nintendo 64, Nintendo
  DS, PSP, Dreamcast, Saturn, Atari 2600/5200/7800/8-bit, Jaguar, Atari ST,
  MSX, Amiga, ZX Spectrum, ZX81, Amstrad, Apple II, MS-DOS, Pokémon mini,
  Intellivision, PC-FX, CD-i, Supervision, Vircon32, o Arcade do MAME atual
  e o Java ME (o SquirrelJME do navegador não abriu o jogo livre de teste);
- os emuladores de fora (PS2, GameCube, Wii, PS3, Xbox 360);
- o jogo em rede (Amigos, Jogar Junto), as opções avançadas do RetroArch,
  o mapeamento de controles, os cheats, o Lossless Scaling, a busca de
  capas na internet e a biblioteca online.

Mesmo que existisse núcleo, N64, PSP e Dreamcast não rodariam num Celeron
de Chromebook dentro do navegador.

## Os números (17/10/2026, Ryzen 5 5600G, `docs\chromebook_bruto.json`)

O teste (`testes\teste_chromebook.py`) roda numa cópia do ARENA, aberto do
arquivo, no Edge, no Chrome for Testing e no Firefox: **41 de 41**.

| | Edge | Chrome | Firefox |
|---|---|---|---|
| os 5 jogos que vêm junto | 60 quadros/s | 60 | 60 |
| abrir um jogo | 0,2 s | 0,3 s | 0,2 s |
| memória do navegador inteiro, a tela parada | 295 MB | 305 MB | 852 MB |
| ... com um jogo aberto (o VIC-20) | 482 MB | 504 MB | 978 MB |
| a pasta do pen drive (lista, jogo, save no pen drive) | sim | sim | só leitura (sem seletor de pasta) |

A memória foi medida como no item 11 (sem janela, depois de 30 s parada):
o jogo aberto soma uns 200 MB, que voltam quando ele fecha. O Firefox pesa
o triplo, como já se viu no item 11: no Chromebook, o navegador é o Chrome.

Com o processador **freado 4 vezes** (o Chromebook da escola, um Celeron
N4020, é uns 3 vezes mais lento por núcleo que este Ryzen), no Edge:

| Console (jogo) | Normal | Freado 4× | Memória do navegador com o jogo |
|---|---|---|---|
| NES (Contra) | 59,9 | 59,7 | ~530 MB |
| Super Nintendo (F-Zero) | 60,0 | 59,9 | ~520 MB |
| Mega Drive (Golden Axe) | 59,9 | 59,9 | ~520 MB |
| PlayStation (Crash Bandicoot) | 59,9 | 55 a 59 | ~960 a 1.000 MB |
| Sega CD (Sonic CD, com a BIOS do pen drive) | 59,7 | 59,9 | ~830 a 970 MB |
| Neo Geo (The King of Fighters '97, com o `neogeo.zip` ao lado) | 59,9 | 59,9 | ~720 MB |

O Sega CD e o Neo Geo provam a BIOS vinda do pen drive: a do Sega CD de
`retroarch\system`, a do Neo Geo da pasta do jogo (onde o ARENA do Windows
a guarda). Esse teste achou um defeito, já consertado: o navegador só
procurava o `neogeo.zip` em `retroarch\system`.

No espinho (a prova de 17/10): o Super Nintendo (Donkey Kong Country) ainda
dava 60 com o processador freado **12 vezes**; o PS1 pesado (Crash Team
Racing) caía a 85% da velocidade com 4 vezes. Os jogos de CD vão inteiros
para a memória (o `.chd` do Crash tem 443 MB; o do Sonic CD, 323 MB): num
Chromebook de 4 GB, cabem, mas são os mais pesados da lista. Prefira o
`.chd` (compactado) ao `.cue` com `.bin` (o disco cheio, uns 700 MB).

**A régua de velocidade é a do Windows:** o "Testar este Chromebook" mede
uma carga parecida com a de um emulador e dá o resultado em "vezes o
notebook mais fraco da escola" (este Ryzen: 2,42 no navegador; 2,38 no
Python do `servidor\hardware.py`). As etiquetas dos consoles (Roda bem,
Roda com ajustes, Pode travar) usam essa medida com uma folga de 2 vezes
para o WebAssembly.

## O teste no Chromebook da escola (com o Rafael)

1. Copie o pacote do ARENA (o zip do Release, descompactado) para um pen
   drive.
2. No Chromebook, abra o **Arquivos**, o pen drive, a pasta do ARENA, e
   clique no **ARENA-CHROMEBOOK.html**. Ele abre no Chrome.
3. Escolha um apelido. Em **Ajustes → Máquina → Este Chromebook**, clique em
   **Testar este Chromebook** e espere uns dois minutos sem mexer.
4. Clique em **Baixar o relatório**: o arquivo
   `teste-do-chromebook-<data>.json` vai para a pasta Downloads do
   Chromebook. Copie para o pen drive e traga.
5. Confira à mão o que o teste não alcança: com um controle USB ligado, um
   jogo responde aos botões? Sai som? A tela cheia funciona? O botão
   **Escolher a pasta do ARENA** (no alto da lista) abre a escolha de pasta?

O relatório diz o processador, a placa, a memória, o sistema, o que o
navegador deixa (seletor de pasta, controle, tela cheia) e os quadros por
segundo de um jogo de cada console. Com ele, eu ajusto o que for preciso.

**O que pode estar bloqueado pelo administrador**, e o que fazer:

| Bloqueio possível | O que acontece | O que fazer |
|---|---|---|
| abrir arquivo do pen drive no Chrome (`file://`) | o ARENA-CHROMEBOOK.html não abre | publicar a versão do navegador num endereço (por exemplo, o GitHub Pages do ARENA): decisão do Rafael |
| pen drive (armazenamento externo) | o pen drive não aparece | "Guardar um jogo neste navegador" (Ajustes → Máquina), com o jogo baixado |
| o seletor de pasta | o "Escolher a pasta do ARENA" não abre | os jogos que vêm junto e o "Guardar um jogo" continuam |
| controle USB | o controle não responde | o teclado joga (as setas, Z, X, A, S, Enter) |

## Fontes

- Encaminhamento de portas do Crostini (Chromium OS):
  <https://www.chromium.org/chromium-os/developer-library/reference/security/port-forwarding/>
- Contêineres e máquinas virtuais no ChromeOS (o administrador pode
  desligar o Crostini; "lento sem 8 GB de RAM"):
  <https://www.chromium.org/chromium-os/developer-library/guides/containers/containers-and-vms/>
- O Baguette, o Linux novo do ChromeOS (padrão a partir do M147; aceleração
  gráfica "não suportada"): <https://developers.google.com/chromeos/app-development/develop/news>
- O Gamepad API restrito a contexto seguro (por isso a versão do navegador
  abre do arquivo ou de `https`, e não de um endereço `http` da rede):
  <https://hacks.mozilla.org/2020/07/securing-gamepad-api/>
- O RetroArch para navegador do libretro:
  <https://buildbot.libretro.com/stable/1.22.2/emscripten/> e
  <https://github.com/libretro/RetroArch/tree/master/pkg/emscripten>
