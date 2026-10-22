# 2 — Jogos, pastas e emuladores

Onde colocar cada jogo, como liberar console amarelo e quais programas precisam ser baixados à parte.

**Neste documento:**

- Parte A — Colocar seus jogos
- Parte B — Consoles que pedem programa próprio

---

## Parte A — Colocar seus jogos

Como adicionar jogos e como liberar os consoles que ficam amarelos.

### O jeito mais fácil: Procurar jogos baixados

Baixou um jogo no computador ou no celular? Toque em **Procurar jogos
baixados** (na coluna da esquerda, ou na lista vazia). O ARENA olha a pasta
de downloads (no celular, também os documentos do WhatsApp e do Telegram),
mostra cada jogo que achou com o console já escolhido e só leva o jogo para
a pasta certa quando você toca em **Levar para o ARENA**. É como uma
estante que arruma o livro na prateleira certa, mas só quando você manda.

- O ARENA olha só os arquivos com o final de algum console (`.nes`,
  `.sfc`, `.gba`, `.iso`...). Fotos e documentos ficam de fora.
- Quando o final serve a mais de um console (como `.iso` ou `.zip`), o
  ARENA olha dentro do arquivo; se ainda assim não souber, você escolhe.
- No celular, o ARENA precisa da permissão de ver os arquivos (Ajustes →
  Máquina → Deixar o ARENA ver os arquivos).
- Se já existe um jogo com o mesmo nome no console, nada é trocado.

---

### Capa dos jogos

Cada jogo aparece na tela dentro de um molde parecido com a mídia física
de verdade do console dele — cartucho, caixa de CD (o disco aparece ao
passar o mouse), caixa de DVD ou cartão, dependendo do console. É por
categoria de mídia, não um desenho exato de cada console — leve de
propósito, para rodar bem até no Celeron mais fraco da escola.

**Para colocar a capa de um jogo**, coloque uma imagem (`.png`, `.jpg`,
`.jpeg` ou `.webp`) com o **mesmo nome do jogo** na mesma pasta dele, ou
dentro de uma subpasta `capas`:

```
jogos\pessoais\PS1\Twisted Metal 2.chd
jogos\pessoais\PS1\capas\Twisted Metal 2.png
```

Se o jogo está **sozinho numa pasta dele** (o jeito comum de jogo de PS3 e
Xbox 360), uma imagem chamada `Cover`, `folder`, `boxart`, `capa` ou
`front` nessa pasta também vale:

```
jogos\pessoais\XBOX360\Gears Of War - Judgment\Gears of War Judgment.iso
jogos\pessoais\XBOX360\Gears Of War - Judgment\Cover.jpg
```

Sem capa, aparecem as duas primeiras letras do título. Não tem limite de
tamanho de imagem além do bom senso: a sua capa fica como está. Para a
lista abrir leve, na primeira vez que uma capa aparece o próprio navegador
faz uma **cópia pequena** dela (280 px de largura, ou 480 em tela 4K), que
o ARENA guarda em `dados\miniaturas` e usa dali em diante — e só carrega as
capas que estão perto da tela. Medido: a lista passou de 21 MB para menos
de 1 MB ao abrir. Pode apagar `dados\miniaturas` quando quiser; ela se
refaz sozinha.

**Buscar automático:** o botão **Buscar capas que faltam** (embaixo de
"Atualizar lista") procura a capa de **todos** os jogos que estão sem, de
uma vez; clicar de novo para. Com um jogo selecionado, o painel de
detalhes tem **Buscar capa** (só aquele) e **Enviar capa** (escolhe um
arquivo do computador na hora).

De onde a capa vem:

| Console | Fonte |
|---|---|
| Quase todos (NES ao PS2, fliperama, MSX, Amiga, DOS...) | O banco de capas do próprio RetroArch (libretro-thumbnails, o do Atualizador Online dele). O ARENA baixa a lista do console e acha o jogo pelo nome **parecido**, na região do arquivo |
| PS3 e PSP | Se o banco não tiver: o **ícone que vem dentro do disco** (`.iso`). Funciona **sem internet** |
| Xbox 360 | Só o banco do RetroArch. A capa oficial do servidor do Xbox 360 (Microsoft) saiu em 22/10/2026: ele só responde sem criptografia, e alguém na rede da escola poderia trocar a imagem no caminho |
| GameCube e Wii | Se o banco não tiver: o GameTDB, de onde o próprio Dolphin baixa as capas, pelo código do disco |
| Uzebox, Tamagotchi e Java ME | Não existe banco: só a capa que você colocar |

Precisa de internet (menos o ícone do PS3/PSP). A lista de capas de cada
console fica guardada por 30 dias em `retroarch\thumbnails`, então a
segunda busca é bem mais rápida. Na primeira versão da busca, ela achou
68 das 78 capas que faltavam na pasta do professor; com os casos abaixo,
achou todas.

A busca também acerta estes casos (achados com os jogos da pasta do
professor, 02/10/2026):

- **Disquete com número no nome** (`Alien Breed_Disk1.adf`): a capa é a do
  jogo (*Alien Breed*); o "(AGA)" no nome do arquivo escolhe a versão AGA.
- **Commodore 64 e Amiga da coleção GameBase**, com o nome cortado em 8
  letras (`INTKARAT.D64`): o nome de verdade vem do `VERSION.NFO` da pasta
  do jogo (*International Karate*). A capa já baixada com o nome antigo
  continua valendo.
- **Nome com `&` ou `:`** (`Sonic & Knuckles`): o banco grava a capa com
  `_` no lugar desses sinais, e a lista agora acha.
- **Jogo que nunca teve caixa** (Satellaview, que chegava por satélite):
  vem a **tela de título** do jogo (ou, por último, uma foto dele), e a
  busca avisa.
- **Jogo de PS1 na pasta do PS2**: a capa vem do banco do PS1, com o aviso
  de que o PCSX2 não abre jogo de PS1. Mova o arquivo para a pasta `PS1`.
- **Nome que não lembra nada** (`BS F-ZERO (J).smc`): quando nenhum nome
  acha, a busca reconhece o jogo pelo **conteúdo** do arquivo — a marca
  (CRC), no banco de dados do próprio RetroArch
  (`retroarch\database\rdb`), do jeito que o "Escanear" do RetroArch faz.
  Esse arquivo é o *F-Zero (Japan) (7-10)* do Satellaview, e a tela de
  título dele veio certa. Só para arquivo de até 64 MB (cartucho,
  disquete, fita) e só quando o banco do console está na pasta: a pasta
  completa do RetroArch tem todos; a versão dos alunos leva só os de
  fliperama, para não pesar no pen drive (lá, o nome já acha quase tudo).

Com isso, a busca achou a capa de **todos** os jogos: 129 de 129 na pasta
do professor e 53 de 53 na versão dos alunos (03/10/2026).

### Parte A — Adicionar jogos

#### Passo 1 — Escolha a pasta

| Pasta | Para quê |
|---|---|
| `jogos\pessoais` | Os seus. Ficam só no seu pen drive |
| `jogos\turma` | Jogos feitos pela turma no TIC-80 (`.tic`) |
| `jogos\livres` | Acervo que pode ser distribuído. Já vem no pacote |

#### Passo 2 — Copie os arquivos

Arraste para dentro da pasta. Pode criar subpastas para se organizar — o
ARENA entra nelas.

#### Biblioteca online

No botão **Biblioteca** (no topo) dá para buscar e baixar sem copiar nada
na mão. A busca só olha coleções do Internet Archive com curadoria de
verdade e licença livre confirmada — hoje, **shareware de MS-DOS** (jogos
que os autores deixaram distribuir de graça, como Commander Keen e Jazz
Jackrabbit). Não é a internet inteira: é só o que pode ser distribuído sem
problema nenhum.

- A busca é **pelo nome do jogo**: todas as palavras precisam estar no nome.
- O jogo baixado vai para `jogos\livres\MS-DOS` e já aparece como MS-DOS.
- **Mario, Sonic, Pokémon** e outros jogos de empresas **não estão lá**:
  eles não são livres. Procurar "Mario" traz só jogos de DOS que têm Mario
  no nome. Se você tem o jogo, veja "Colocar um jogo seu" (abaixo).
- Precisa de internet; sem ela, os jogos que já estão na pasta continuam
  funcionando normal.

**Jogos livres por console.** Logo abaixo da busca, a Biblioteca tem uma
lista escolhida a dedo, para mais consoles. Toque no console para abrir a
lista e em **Baixar** no jogo:

| Console | Jogos | De onde vêm |
|---|---|---|
| Arcade (MAME) | 20 fliperamas clássicos: Circus, Car Polo, Robby Roto, Super Tank, Looping, Hard Hat e outros | mamedev.org, a equipe do MAME, com licença dos donos (uso não comercial) |
| NES | Thwaite, Concentration Room, Nova the Squirrel | os autores, no GitHub (GPL) |
| Game Boy e Game Boy Color | Libbet and the Magic Floor, µCity | os autores (zlib e GPL) |
| Game Boy Advance | Blind Jump | o autor (GPL; arte e música só para uso não comercial) |
| Mega Drive | KleleAtoms (até 4 jogadores) | o autor (MIT) |
| Atari 2600 | Space Raid | o autor (uso não comercial e educativo) |
| Apple II, Arduboy, CHIP-8, MicroW8, MSX, Plus/4, VIC-20, ZX81 e Java ME | um jogo de cada | os autores (MIT, GPL, CC0 e outras licenças livres) |

- Cada jogo vem do site de quem publicou. O ARENA confere a marca do
  arquivo (SHA-256) e só instala se for exatamente o que foi testado. Nada
  disso vai dentro do ARENA: é baixado quando você pede.
- Os fliperamas do mamedev.org e o Space Raid são só para uso não comercial.
  Antes de baixar, marque a caixinha desse console, a mesma confirmação que
  o site deles pede.
- O jogo vai para `jogos\livres\<console>` e já aparece no console certo.
- Victory e Top Gunner mostram uma tela de teste da placa na primeira vez:
  aperte um botão (ou Start) e ela não volta mais. O FAX testa a memória por
  uns 2 minutos ao ligar.
- O mamedev.org tem também 8 jogos da Video Klein, que ficaram de fora: são
  de pôquer e de aposta, impróprios para uma turma de menores de idade.

#### Passo 3 — Atualize a lista

No ARENA, clique em **Atualizar lista**, no canto inferior esquerdo.

Pronto. O ARENA olha o final do nome do arquivo e descobre sozinho de qual
console ele é.

**Para o professor — conferir muitos jogos de uma vez.** Antes de levar jogo
novo para a sala, dá para ver a lista inteira, console por console, com o
nome que o ARENA vai mostrar, o arquivo e quantos jogadores ele aceita:

```
servidor\python\python.exe ferramentas\inventario_jogos.py
```

Serve para pegar cedo um jogo na pasta do console errado ou uma trilha de CD
aparecendo como se fosse um jogo sozinho.

---

### Colocar um jogo seu: console por console

A ideia central: **cada console tem a sua prateleira** — uma pasta dentro de
`jogos\pessoais`. O jogo vai na prateleira certa, do jeito que aquele
aparelho "lê". No ARENA, o botão **Como colocar jogos** (barra da esquerda)
mostra tudo isto para o console que você escolher, diz se a BIOS já está na
pasta e tem o botão **Abrir a pasta**.

1. Ache a pasta do console na tabela abaixo (ou clique em **Criar pastas dos
   consoles**, que cria todas).
2. Arraste o arquivo do jogo para dentro.
3. Clique em **Atualizar lista**.

**Pode ser `.zip`?** Depende do tipo de jogo:

| Tipo | Regra | Por quê |
|---|---|---|
| Cartucho e computador antigo | **Pode** ser `.zip` com **um** jogo dentro | O RetroArch abre o jogo de dentro do zip (conferido com um jogo de SNES zipado) |
| CD e DVD (PS1, Sega CD, Saturn, Dreamcast, PSP...) | **Não** | Disco é o `.chd` (um arquivo só — o melhor) ou o `.cue` **junto** com os `.bin` na mesma pasta. De dentro do zip o emulador não acha as trilhas |
| Fliperama (MAME, Neo Geo) | **Tem que ser** `.zip` | O jogo **é** o zip, com o nome curto que o emulador conhece (`mslugx.zip`). Não descompacte nem troque o nome |
| PS2, GameCube, Wii, PS3, Xbox 360 | **Não** | Esses emuladores não abrem zip: descompacte antes |
| MS-DOS | **Pode** | O DOSBox abre o zip direto (ou a pasta do jogo com o `.exe`) |

**BIOS** é o "programa de fábrica" de alguns consoles. Há dois jeitos de
colocar a BIOS:

- **O mais fácil:** ponha o arquivo na pasta do console dentro de `BIOS`
  (ex.: `BIOS\PS1`). Depois clique em **Conferir**, em **Ajustes →
  Emuladores → BIOS dos consoles**. Nessa pasta, o nome do arquivo não
  importa: o ARENA reconhece e instala com o nome certo (veja "A pasta
  BIOS", mais abaixo).
- **Direto em `retroarch\system`:** aí o nome do arquivo tem que ser
  **exatamente** o da tabela. A do Dreamcast vai numa pasta `dc` lá dentro.

No fliperama do MAME, a BIOS vai na pasta dos próprios jogos.

| Console | Pasta (em `jogos\pessoais`) | Arquivos que servem | `.zip`? | BIOS |
|---|---|---|---|---|
| 3DO | `3DO` | `.iso` `.cue` `.chd` | **não** | uma de: `panafz10.bin`, `panafz1.bin`, `goldstar.bin` |
| Amstrad CPC | `Amstrad CPC` | `.cdt` `.sna` `.dsk` | pode | não precisa |
| Apple II | `Apple II` | `.dsk` `.do` `.po` `.nib` `.woz` `.2mg` | pode | não precisa |
| Arcade (MAME) | `Arcade` | `.zip` `.7z` | **tem que ser** | só jogo de Neo Geo: `neogeo.zip` **na própria pasta `Arcade`** |
| Arduboy | `Arduboy` | `.hex` `.arduboy` | pode | não precisa |
| Atari 2600 | `Atari 2600` | `.a26` | pode | não precisa |
| Atari 5200 | `Atari 5200` | `.a52` | pode | `5200.rom` |
| Atari 7800 | `Atari 7800` | `.a78` | pode | não precisa |
| Atari 8-bit | `Atari 8-bit` | `.atr` `.xex` `.car` `.cas` `.xfd` `.atx` `.dcm` | pode | não precisa (liga pelo AltirraOS, livre); opcional: `ATARIXL.ROM` e `ATARIBAS.ROM` |
| Atari Jaguar | `Atari Jaguar` | `.j64` `.jag` | pode | não precisa |
| Atari Lynx | `Atari Lynx` | `.lnx` | pode | `lynxboot.img` |
| Atari ST | `Atari ST` | `.st` `.msa` `.stx` `.dim` | pode | `tos.img` (sem ele, liga pelo EmuTOS, livre) |
| CHIP-8 | `CHIP-8` | `.ch8` `.sc8` `.xo8` | pode | não precisa |
| ColecoVision | `ColecoVision` | `.col` | pode | `colecovision.rom` |
| Commodore 128 | `Commodore 128` | `.d64` `.d71` `.d81` `.prg` `.t64` `.tap` `.crt` | pode | não precisa |
| Commodore 64 | `Commodore 64` | `.d64` `.t64` `.prg` `.crt` | pode | não precisa |
| Commodore Amiga | `Amiga` | `.adf` `.hdf` `.ipf` | pode | uma de: `kick34005.A500`, `kick40068.A1200` |
| Commodore PET | `Commodore PET` | `.prg` `.d64` `.d80` `.d82` `.t64` `.tap` | pode | não precisa |
| Commodore Plus/4 | `Commodore Plus-4` | `.prg` `.d64` `.t64` `.tap` `.crt` | pode | não precisa |
| Commodore VIC-20 | `Commodore VIC-20` | `.prg` `.d64` `.t64` `.tap` `.crt` `.20` `.40` `.60` `.a0` `.b0` | pode | não precisa |
| Game & Watch | `Game and Watch` | `.mgw` | pode | não precisa |
| Game Boy Advance | `Game Boy Advance` | `.gba` | pode | não precisa |
| Game Boy e Game Boy Color | `Game Boy` | `.gb` `.gbc` | pode | não precisa |
| GameCube | `GameCube` | `.rvz` `.gcm` `.gcz` `.chd` `.iso` | **não** | não precisa |
| Intellivision | `Intellivision` | `.int` | pode | `exec.bin`, `grom.bin` |
| Java ME (celular antigo) | `J2ME` | `.jar` `.kjx` | **não** (o `.jar` já é compactado) | não precisa (o Java vem no ARENA) |
| LowRes NX | `LowRes NX` | `.nx` | pode | não precisa |
| Magnavox Odyssey 2 | `Odyssey 2` | `.bin` | pode | `o2rom.bin` |
| Mega Drive, Master System e Game Gear | `Mega Drive` | `.md` `.gen` `.smd` `.sms` `.gg` | pode | não precisa |
| MicroW8 | `MicroW8` | `.uw8` | pode | não precisa |
| MS-DOS | `MS-DOS` | `.exe` `.com` `.bat` `.conf` | pode | não precisa |
| MSX | `MSX` | `.rom` `.dsk` `.cas` | pode | não precisa no cartucho (C-BIOS livre); disquete e fita: `Machines` |
| Neo Geo e fliperamas (FBNeo) | `Neo Geo` | `.zip` `.7z` | **tem que ser** | `neogeo.zip` |
| Neo Geo Pocket | `Neo Geo Pocket` | `.ngp` `.ngc` | pode | não precisa |
| Nintendo (NES) | `NES` | `.nes` `.fds` `.unf` `.unif` | pode | não precisa |
| Nintendo 64 | `Nintendo 64` | `.n64` `.z64` `.v64` | pode | não precisa |
| Nintendo DS | `Nintendo DS` | `.nds` | pode | não precisa |
| Nintendo Wii | `Wii` | `.rvz` `.wbfs` `.wia` `.iso` | **não** | não precisa |
| PC Engine | `PC Engine` | `.pce` `.sgx` | pode | não precisa |
| PC-FX | `PC-FX` | `.cue` `.chd` | **não** | `pcfx.rom` |
| Philips CD-i | `CD-i` | `.chd` `.cue` | **não** | `same_cdi\bios\cdimono1.zip` |
| PlayStation | `PS1` | `.pbp` `.m3u` `.cue` `.chd` `.iso` | **não** | uma de: `scph5501.bin`, `scph5500.bin`, `scph5502.bin`, `scph1001.bin` |
| PlayStation 2 | `PS2` | `.iso` `.chd` | **não** | Uma BIOS de PS2 (um arquivo .bin de 4 MB) em retroarch\system |
| PlayStation 3 | `PS3` | `.iso` `.pkg` | **não** | O firmware oficial do PS3 (PS3UPDAT.PUP), instalado UMA vez pelo próprio RPCS3 |
| PlayStation Portable | `PSP` | `.cso` `.iso` `.chd` | **não** | não precisa |
| Pokemon mini | `Pokemon mini` | `.min` | pode | não precisa |
| ScummVM | `ScummVM` | `.scummvm` `.svm` | **não** | não precisa |
| Sega 32X | `Sega 32X` | `.32x` | pode | não precisa |
| Sega CD | `Sega CD` | `.cue` `.chd` `.iso` | **não** | uma de: `bios_CD_U.bin`, `bios_CD_E.bin`, `bios_CD_J.bin` |
| Sega Dreamcast | `Dreamcast` | `.gdi` `.cdi` `.chd` `.iso` | **não** | `dc\dc_boot.bin` |
| Sega Saturn | `Sega Saturn` | `.cue` `.chd` | **não** | uma de: `sega_101.bin`, `mpr-17933.bin` |
| Sega SG-1000 | `SG-1000` | `.sg` | pode | não precisa |
| Super Nintendo | `Super Nintendo` | `.sfc` `.smc` `.swc` `.fig` `.bs` | pode | não precisa |
| Tamagotchi | `Tamagotchi` | `.b` `.bin` | pode | não precisa |
| Thomson MO/TO | `Thomson` | `.k7` `.fd` `.sap` `.m5` `.m7` | pode | não precisa |
| TIC-80 | `TIC-80` | `.tic` | pode | não precisa |
| Uzebox | `Uzebox` | `.uze` | pode | não precisa |
| Vectrex | `Vectrex` | `.vec` | pode | não precisa |
| Vircon32 | `Vircon32` | `.v32` | pode | não precisa (a BIOS livre vem no emulador) |
| Virtual Boy | `Virtual Boy` | `.vb` `.vboy` | pode | não precisa |
| WASM-4 | `WASM-4` | `.wasm` | pode | não precisa |
| Watara Supervision | `Watara Supervision` | `.sv` | pode | não precisa |
| WonderSwan | `WonderSwan` | `.ws` `.wsc` | pode | não precisa |
| Xbox 360 | `XBOX360` | `.iso` `.xex` | **não** | não precisa |
| ZX Spectrum | `ZX Spectrum` | `.tzx` `.tap` `.z80` `.szx` | pode | não precisa |
| ZX81 | `ZX81` | `.p` `.t81` `.tzx` | pode | não precisa |

Jogo de **vários discos** (PS1, Saturn...): deixe todos na mesma pasta, com
`(Disc 1)`, `(Disc 2)` no nome — o ARENA junta num jogo só e troca o disco
pelo menu. **PS3** precisa do firmware oficial instalado uma vez pelo RPCS3
(menu *File → Install Firmware*). **Xbox 360** precisa de processador com
AVX. **Thomson MO/TO:** a fita (`.k7`) e o disquete (`.fd`, `.sap`)
começam pelo **Start** do controle (a partida automática do emulador fica
desligada).

---

### Como o ARENA reconhece cada console

| Final do arquivo | Console |
|---|---|
| `.nes` `.fds` `.unf` | Nintendo (NES) |
| `.sfc` `.smc` `.swc` `.fig` | Super Nintendo |
| `.gb` `.gbc` | Game Boy e Game Boy Color |
| `.gba` | Game Boy Advance |
| `.vb` | Virtual Boy |
| `.min` | Pokémon mini |
| `.mgw` | Game & Watch |
| `.n64` `.z64` `.v64` | Nintendo 64 |
| `.nds` | Nintendo DS |
| `.gcm` `.gcz` | GameCube |
| `.wbfs` `.wia` | Nintendo Wii |
| `.rvz` | GameCube ou Wii — quem decide é a pasta (o ARENA avisa se o disco diz outra coisa) |
| `.sg` | Sega SG-1000 |
| `.md` `.gen` `.smd` `.sms` `.gg` | Mega Drive, Master System e Game Gear |
| `.32x` | Sega 32X |
| `.gdi` `.cdi` | Sega Dreamcast |
| `.pbp` `.m3u` | PlayStation |
| `.cso` | PlayStation Portable |
| `.a26` | Atari 2600 |
| `.a52` | Atari 5200 |
| `.a78` | Atari 7800 |
| `.lnx` | Atari Lynx |
| `.j64` `.jag` | Atari Jaguar |
| `.st` `.msa` `.stx` `.dim` | Atari ST |
| `.atr` `.car` `.xfd` `.atx` `.dcm` | Atari 8-bit |
| `.col` | ColecoVision |
| `.int` | Intellivision |
| `.vec` | Vectrex |
| `.pce` `.sgx` | PC Engine |
| `.ngp` `.ngc` | Neo Geo Pocket |
| `.ws` `.wsc` | WonderSwan |
| `.sv` | Watara Supervision |
| `.d64` `.t64` `.prg` `.crt` | Commodore 64 (na pasta dele, o VIC-20, o Plus/4, o 128 ou o PET) |
| `.d71` `.d81` | Commodore 128 |
| `.d80` `.d82` | Commodore PET |
| `.20` `.40` `.60` `.a0` `.b0` | Commodore VIC-20 |
| `.adf` `.hdf` `.ipf` | Commodore Amiga |
| `.tzx` `.tap` `.z80` `.szx` | ZX Spectrum (na pasta dele, o ZX81, o VIC-20, o Plus/4, o Commodore 128 ou o PET) |
| `.p` `.t81` | ZX81 |
| `.cdt` `.sna` | Amstrad CPC |
| `.do` `.po` `.nib` `.woz` `.2mg` | Apple II |
| `.rom` `.cas` | MSX (o `.cas`, na pasta dele, o Atari 8-bit) |
| `.k7` `.fd` `.sap` `.m5` `.m7` | Thomson MO/TO |
| `.exe` `.com` `.bat` `.conf` | MS-DOS |
| `.scummvm` `.svm` | ScummVM |
| `.tic` | TIC-80 |
| `.wasm` | WASM-4 |
| `.nx` | LowRes NX |
| `.uze` | Uzebox |
| `.ch8` `.sc8` `.xo8` | CHIP-8 |
| `.hex` `.arduboy` | Arduboy |
| `.uw8` | MicroW8 |
| `.v32` | Vircon32 |

#### Quando o final serve a mais de um console

`.iso`, `.cue`, `.chd`, `.bin`, `.zip` e `.dsk` servem a vários consoles,
assim como os finais dos computadores da Commodore (`.prg`, `.d64`, `.t64`,
`.crt` e `.tap`: C64, C128, VIC-20, Plus/4 e PET), o `.tzx` (ZX Spectrum e
ZX81), o `.cas` (MSX e Atari 8-bit) e o `.xex` (Xbox 360 e Atari 8-bit).
Nesses casos **quem decide é a pasta**, igual ao RetroArch. Fora da pasta
de um console, vale o C64 e o ZX Spectrum.

O ARENA não tenta adivinhar. Já tentou, e errava: o **Half-Life de
PlayStation 2 foi lançado em CD**, com a mesma estrutura de um jogo de
PlayStation 1. Nenhuma pista de tamanho ou de cabeçalho separa os dois.
Chutar só fazia o jogo abrir no emulador errado.

#### Jogo de CD em vários arquivos

Muitos jogos de CD (Saturn, Dreamcast, PlayStation) vêm em várias
**trilhas** (`Track 01.bin`, `Track 02.bin`...) mais um arquivo-índice
(`.cue` ou `.gdi`) que diz quais trilhas formam o disco. O ARENA mostra
**só o índice**, como um jogo; as trilhas ficam escondidas. Deixe tudo na
mesma pasta, de preferência uma pasta com o nome do jogo.

- Se o arquivo se chama só `disc.gdi` ou `track01.bin`, o nome do jogo vem
  da **pasta**.
- Se o mesmo jogo está em dois formatos na pasta (`.chd` e `.cue`), aparece
  **uma vez só**, pelo `.chd` (um arquivo só, mais fácil de carregar).
- A BIOS do Neo Geo (`neogeo.zip`) não aparece como jogo, mesmo se estiver
  na pasta dos jogos.

#### Jogo de CD baixado em .zip

O emulador não abre jogo de CD de dentro de um `.zip` (o `.cue` precisa dos
`.bin` ao lado, soltos). Se você puser o `.zip` na pasta do console, o
cartão avisa e traz o botão **Arrumar: descompactar**: o ARENA descompacta
numa pasta com o nome do jogo, em segundo plano (um CD tem até 700 MB: o
botão mostra quanto já foi), conferindo antes se cabe. O `.zip` fica — pode
apagar depois, para liberar espaço. Com `.7z` o ARENA não consegue: use o
7-Zip ou o Explorador do Windows.

#### Jogo de vários discos

Jogo que saiu em mais de um disco — `Final Fantasy VII (USA) (Disc 1).chd`,
`(Disc 2)`, `(Disc 3)`; ou disquetes, `Jogo_Disk1.adf`, `Jogo_Disk2.adf` —
aparece **uma vez só**, com "3 discos" ao lado do tamanho. Ao abrir, o ARENA
entrega os discos todos ao emulador. Quando o jogo pedir o próximo:
**Esc → Controle de disco → ejetar, escolher o disco e inserir**, sem sair
do jogo.

- Os discos precisam estar **na mesma pasta**, com o mesmo nome e o mesmo
  formato, mudando só o número (`Disc 1`, `Disk 2`, `Disco 3`, `CD 2`).
- Se faltar um disco, o jogo mostra o aviso "Falta o disco 2...".
- O save continua com o nome do disco 1: quem já jogava o disco 1 sozinho
  não perde nada.
- Vale nos consoles cujo emulador aceita lista de discos: PlayStation,
  Sega CD, Saturn, Dreamcast, PC Engine CD, Amiga, Commodore 64, MSX,
  Amstrad e DOS. Nos outros (3DO, PC-FX), cada disco continua sendo um jogo.
- No **Jogar Junto** abre só o disco 1: trocar de disco no meio da partida
  desencontra os dois computadores.

#### Fliperama: Neo Geo e Arcade (MAME)

São dois consoles diferentes no ARENA, cada um com o seu emulador:

| Console | Pasta | Emulador | Serve para |
|---|---|---|---|
| **Neo Geo e fliperamas (FBNeo)** | `jogos\pessoais\Neo Geo` | FBNeo | KOF, Metal Slug e muitos fliperamas da Capcom, Konami e outras (Turtles in Time, por exemplo). Mais leve que o MAME |
| **Arcade (MAME)** | `jogos\pessoais\Arcade` | MAME (versão atual) | O resto dos fliperamas |

Regras que valem para os dois (do guia oficial do libretro):

- **O jogo é o `.zip` inteiro, com o nome original** (`kof97.zip`,
  `mslugx.zip`). Não descompacte e não renomeie: nome trocado não abre.
- **O `.zip` precisa ser da versão que o emulador espera.** Cópia antiga ou
  feita para outro emulador (arquivos com outros nomes, como `kof2k2_c1.rom`
  no lugar de `265-c1.c1`, ou subpastas dentro do `.zip`) não abre. O
  RetroArch só diz "Falha ao carregar o conteúdo"; o que falta fica no
  registro do emulador, e o ARENA lê e explica (veja **Quando o jogo não
  abre**, abaixo).
- **BIOS dos jogos de Neo Geo:** o arquivo tem que se chamar exatamente
  **`neogeo.zip`**. Com outro nome (`neogeo.mame.zip`, por exemplo), o
  emulador não acha. Onde ele fica:
  - **Neo Geo (FBNeo):** em `retroarch\system` ou na pasta dos jogos;
  - **Arcade (MAME):** **na mesma pasta do jogo** (`Arcade\neogeo.zip`). O
    MAME não procura em `retroarch\system` (conferido no registro dele).

  O ARENA não mostra a BIOS como jogo.
- **Jogo com disco rígido ou CD** (Killer Instinct, por exemplo) precisa
  também de um `.chd`, numa subpasta com o nome do jogo:
  `Arcade\kinst.zip` + `Arcade\kinst\kinst.chd`. Esse `.chd` não aparece na
  lista como jogo separado. O `.zip` fica **fora** da subpasta: com
  `Arcade\kinst\kinst.zip`, junto do disco, o MAME não abre.
- **Ficha:** fliperama abre em demonstração ("CREDIT 00"). Aperte **Select**
  (no controle Xbox, **Back**) para pôr uma ficha e depois **Start**. O
  ARENA lembra disso toda vez que abre um jogo de fliperama.

O MAME atual é pesado: em máquina fraca, prefira os jogos de Neo Geo.

**O nome do jogo na lista** vem do banco de dados do próprio RetroArch
(`retroarch\database\rdb`), não do nome do arquivo: `mslugx.zip` aparece
como **Metal Slug X - Super Vehicle-001**, `kinst.zip` como **Killer
Instinct**. É também esse nome que o botão **Buscar capa** usa. Na lista de
jogadores (`dados\jogadores.txt`), vale escrever o nome completo ou o curto
(`Tmnt2 = 4` continua valendo).

**O ARENA avisa, na tela do jogo, o que impede um fliperama de abrir.**
Quando só existe um jeito certo, o aviso vem com o botão **Arrumar**, que
faz o conserto no clique (o ARENA nunca mexe no arquivo do jogo sozinho, e
nunca apaga nem passa por cima de nada):

| Aviso | O que fazer |
|---|---|
| O disco (`.chd`) está dentro de um `.zip` (ex.: `kinst-chd.zip`) | **Arrumar** tira o `.chd` para a subpasta com o nome do jogo (`Arcade\kinst\kinst.chd`); o `.zip` fica. O emulador não lê disco de dentro de `.zip` |
| O disco (`.chd`) está solto, ao lado do `.zip` (`Arcade\kinst.chd`) | **Arrumar** cria a pasta `kinst` e põe o disco dentro |
| O disco (`.chd`) está numa pasta com outro nome (`Arcade\Killer Instinct\kinst.chd`) | **Arrumar** leva o disco para a pasta com o nome do `.zip` (`Arcade\kinst`) |
| O disco (`.chd`) está sozinho, sem o `.zip` do jogo | Ponha na pasta o **romset** do jogo (ex.: `kinst.zip`). Romset é o `.zip` com as partes do jogo de fliperama, com o nome curto que o emulador conhece. O jogo abre pelo `.zip`. O `.chd` é só o disco dele |
| O jogo não abriu porque falta o disco (o MAME diz qual) | O ARENA cria a pasta onde ele vai (`Arcade\kinst`), com um `LEIA.txt` dizendo o nome do arquivo: é só pôr lá |
| O emulador não conhece o nome do arquivo (ex.: `The King Of Fighters 2002.zip`) | Renomeie para o nome curto do romset. É como a matrícula na escola: o professor chama pelo nome, mas o sistema só acha o aluno pela matrícula. O aviso já diz o nome certo: ele procura o título no banco do RetroArch (ex.: **kof2002.zip**). Quando é só um palpite pelo começo do título, o aviso diz "confira" |
| Os arquivos estão dentro de uma pasta no `.zip` | **Arrumar** refaz o `.zip` sem a pasta; o original fica guardado em `backup\originais` |
| O `.zip` está corrompido | Baixe ou copie o jogo de novo |
| **O arquivo está danificado: a parte X não confere** | Copie o jogo de novo, de uma cópia boa. Foi o caso do Metal Slug X com personagens de cor estranha: uma parte do gráfico dos personagens estava estragada dentro do `.zip`, e o FBNeo abria assim mesmo |
| A BIOS do Neo Geo está com outro nome (ex.: `neogeo.mame.zip`) | **Arrumar** renomeia para `neogeo.zip` |
| Jogo de Neo Geo na pasta `Arcade` sem o `neogeo.zip` ao lado | **Arrumar** põe uma cópia do `neogeo.zip` da pasta `BIOS` ao lado do jogo: o MAME só procura ali |
| O `.zip` está dentro da pasta do disco (`Arcade\kinst\kinst.zip`) | **Arrumar** tira o `.zip` dessa pasta e põe na pasta de cima; dentro dela fica só o `.chd` |

A conferência de "arquivo danificado" descompacta o `.zip` inteiro, então o
ARENA faz uma vez só por arquivo, em segundo plano, logo depois de abrir
(e de novo só se você trocar o arquivo). O resultado fica em
`dados\zips_conferidos.json`.

**Quando o jogo não abre.** Algumas coisas só o emulador descobre na hora
de abrir: se o `.zip` é da versão certa, se falta algum arquivo dentro
dele. Quando um jogo volta para a lista sem abrir, o ARENA lê o registro do
emulador daquela partida e explica o motivo **no alto da tela** e no
**painel do jogo** ("Da última vez: ..."), com o nome dos arquivos. Foi o
caso do KOF 2002 da pasta do professor:

> MAME não abriu este jogo. A BIOS está na pasta, mas com o nome errado:
> renomeie neogeo.mame.zip para neogeo.zip (o emulador só procura por esse
> nome). Faltam 13 arquivos do jogo dentro do kof2002.zip (265-p1.p1,
> 265-p2.sp2, 265-m1.m1 e mais 10). Este zip é de outra versão ou feito
> para outro emulador: dentro dele há kof2k2_c1.rom, kof2k2_c2.rom,
> kof2k2_c3.rom e mais 13. Troque por um kof2002.zip feito para o MAME
> desta versão do ARENA.

Vale para todo jogo que abre pelo RetroArch, não só fliperama: quando o
registro não traz uma frase conhecida, o ARENA repete o que o emulador
disse. O aviso some quando o jogo abre ou quando você troca o arquivo. Os
consoles que abrem por outro programa (PS2, PS3, Xbox 360 e, com o Dolphin
na pasta, GameCube e Wii) ficam de fora: o ARENA não lê o registro deles.

**Zip "decriptado" de emulador antigo (Kawaks, Nebula).** Muito zip de
fliperama que circula foi feito para emulador de 20 anos atrás: as partes
já vêm decriptadas e com outros nomes (`kof2k2_c1.rom`...). O MAME e o
FBNeo de hoje pedem as partes originais e recusam. Para alguns jogos, o
FBNeo tem um conjunto **"Fully Decrypted"** feito exatamente dessas partes,
e a ferramenta `ferramentas\converter_fliperama_decriptado.py` converte:

```
servidor\python\python.exe ferramentas\converter_fliperama_decriptado.py           (só mostra)
servidor\python\python.exe ferramentas\converter_fliperama_decriptado.py --fazer   (converte)
```

Ela reconhece cada parte pela **marca** (o CRC), não pelo nome, e confere a
marca do resultado antes de gravar: faltou ou não bateu alguma parte, não
mexe em nada. Hoje ela sabe converter o **The King of Fighters 2002**
(`kof2002.zip` decriptado → `kof2k2fd.zip`, na pasta **Neo Geo**). Foi o
que aconteceu com o KOF 2002 da pasta do professor (03/10/2026, nas duas
pastas):

| O que | Onde ficou |
|---|---|
| O jogo (13 partes, as do som juntadas de 2 em 2) | `jogos\pessoais\Neo Geo\kof2k2fd.zip`; na lista: **The King of Fighters 2002** |
| O programa de som (é de outra versão da que o FBNeo espera para este conjunto; o próprio FBNeo usa essa versão num conjunto parecido) | `retroarch\system\fbneo\patched\kof2k2fd.zip` — a pasta de **correções** do FBNeo: ali ele aceita a parte pelo nome e pelo tamanho, sem conferir a marca (opção "Allow patched romsets", ligada por padrão) |
| O `.zip` de antes, intacto | `backup\originais\kof2002.zip` (fora do rodízio das cópias de segurança) |

Conferido abrindo de verdade: demonstração e tela de título, com as cores
certas (`testes\teste_kof2002_convertido.py`). Para levar esse jogo para
outro ARENA, copie os **dois** primeiros arquivos: sem a correção, o FBNeo
diz que falta o `265-m1d.m1`. Zip de outro jogo que a ferramenta não
conhece continua precisando de uma cópia feita para o MAME ou o FBNeo
desta versão.

#### Passo 1 — Criar as pastas

No ARENA, clique em **Criar pastas dos consoles**, embaixo da lista à
esquerda.

Ele cria as 52 pastas dentro de `jogos\pessoais` (uma por console):

```
ARENA\jogos\pessoais\PS1\
ARENA\jogos\pessoais\PS2\
ARENA\jogos\pessoais\PSP\
ARENA\jogos\pessoais\Nintendo 64\
ARENA\jogos\pessoais\Sega Saturn\
...
```

#### Passo 2 — Jogar os arquivos dentro

Arraste cada jogo para a pasta do console dele. Depois clique em
**Atualizar lista**.

Pronto. Não tem mais como errar.

#### Se você já tem jogos soltos

Eles aparecem no topo da lista, num grupo chamado **Precisa escolher o
console**. Duas formas de resolver:

**Arrastando:** pegue a linha do jogo e solte em cima do console certo, na
lista da esquerda. O ARENA **move o arquivo de verdade** para a pasta.

**Pela gaveta:** clique em *Saves e cheats* e escolha em **Console deste
jogo**. Mesma coisa, também move o arquivo.

Nos dois casos o ARENA já deixa marcada a opção mais provável — na maioria
das vezes é só confirmar.

#### As pastas que o ARENA reconhece

Você pode usar o nome que ele criou, ou qualquer apelido comum:

| Console | Pasta criada | Também aceita |
|---|---|---|
| PlayStation | `PS1` | `psx`, `playstation` |
| PlayStation 2 | `PS2` | `playstation 2` |
| PlayStation Portable | `PSP` | `playstation portable` |
| Nintendo 64 | `Nintendo 64` | `n64` |
| Sega CD | `Sega CD` | `mega cd`, `scd` |
| GameCube | `GameCube` | `gc`, `ngc` |
| Nintendo Wii | `Wii` | `nintendo wii` |

Funciona em qualquer nível: `Sony\PlayStation 2\Corrida` também é
reconhecido.

**A pasta vale acima de tudo.** Se você põe um arquivo na pasta `PS2`, ele
é PlayStation 2 — mesmo que a extensão dele normalmente pertença a outro
console.

---

### Nomes de arquivo

O ARENA limpa o nome sozinho para mostrar na tela:

```
super_jogo_(Brazil)_[!].sfc   →   Super Jogo
```

Ele tira o que está entre parênteses e colchetes, troca `_`, `.` e `-` por
espaço e coloca as iniciais em maiúscula. Você não precisa renomear nada.

A busca ignora acento: digitar `pokemon` acha `Pokémon`.

**Não renomeie o arquivo depois de começar a jogar.** Os saves seguem o nome
do arquivo — trocou o nome, perdeu o save. Escolha o nome antes.

---

### Parte B — Consoles amarelos: a BIOS

#### O que é

Alguns consoles não funcionam só com o emulador: precisam da **BIOS**, o
programinha que vinha gravado de fábrica dentro do aparelho e que liga ele
por dentro. Ela pertence à empresa que fabricou o console — **o ARENA não
baixa BIOS**. Quem tem o aparelho original pode extrair da própria máquina.
A exceção é a **BIOS livre**, escrita do zero por voluntários: essa vem com o
ARENA (veja "BIOS livres", mais abaixo).

#### A pasta BIOS: uma pasta por console

Na primeira vez que abre, o ARENA cria a pasta `BIOS`, ao lado da pasta
`jogos`. Dentro dela há uma pasta para cada console que usa BIOS — com o
mesmo nome da pasta de jogos dele — e, quando cada região tem a sua BIOS,
uma pasta por região:

```
ARENA\BIOS\
├── LEIA - O QUE FALTA.txt          ← quantas são, quais estão ativas e quais faltam
├── PS1\EUA · Europa · Japão        ← basta UMA, de qualquer região
├── PS2\EUA · Europa · Japão        ← basta UMA (o ARENA passa ao PCSX2)
├── PS3                             ← o firmware (PS3UPDAT.PUP)
├── Sega CD\EUA · Europa · Japão    ← uma por região: o jogo europeu só abre com a europeia
├── Sega Saturn\EUA e Europa · Japão · Cartuchos
├── Dreamcast
├── Neo Geo
├── Super Nintendo (Satellaview)
└── ... (uma pasta para cada um dos outros)
```

Cada pasta tem um `LEIA.txt` que diz o que vai ali, se já está **ativa** e o
que acontece sem ela. A mesma lista aparece na tela, em **Ajustes →
Emuladores → BIOS dos consoles**, com um botão para abrir a pasta de cada
console.

#### Passo a passo

**1.** Ponha o arquivo na pasta do console. **O nome não importa**, e pode
ser o `.zip` em que ele veio (até um zip dentro de outro zip, como vêm os
pacotes da internet).

**2.** Clique em **Conferir**, em **Ajustes → Emuladores → BIOS dos
consoles** (ou feche e abra o ARENA).

**3.** Pronto: a BIOS aparece como **Ativa**. O ARENA reconheceu o arquivo
pela marca da versão certa (o MD5 que o próprio RetroArch publica) ou, no
PlayStation, pela região que vem gravada dentro dela, e instalou onde o
emulador procura (`retroarch\system`), com o nome exato que ele exige.

Arquivo na pasta certa, com o tamanho certo, mas de marca desconhecida fica
**ativo, de outra versão**: pode funcionar; se algum jogo der problema,
troque pela recomendada (o `LEIA.txt` da pasta traz a marca dela). Quando a
recomendada chega, o ARENA troca sozinho e guarda a antiga em
`backup\bios-trocadas`. **O ARENA nunca apaga BIOS.** Arquivo que ele não
reconhece fica listado no `LEIA.txt` da pasta ("não reconheceu").

Também vale pôr a BIOS direto em `retroarch\system`, como os tutoriais do
RetroArch ensinam — solta ou no pacote `.zip`: o ARENA acha e põe uma cópia
na pasta `BIOS`, para lá mostrar tudo o que existe. E a BIOS deixada junto
dos jogos (o `SCPH1001.BIN` na pasta do PS1) não aparece como jogo: o ARENA
reconhece e leva para o lugar certo.

#### Quais consoles pedem

| Os jogos precisam (sem ela, não abrem) | O que vai |
|---|---|
| PlayStation 2 | uma BIOS de qualquer região (um `.bin` de 4 MB) |
| PlayStation 3 | o firmware `PS3UPDAT.PUP`, instalado uma vez pelo RPCS3 |
| Sega CD | uma por região: `bios_CD_U.bin` (EUA), `bios_CD_E.bin` (Europa), `bios_CD_J.bin` (Japão) |
| Sega Saturn | `mpr-17933.bin` (EUA e Europa) e `sega_101.bin` (Japão) |
| Neo Geo | `neogeo.zip` inteiro — o mesmo serve ao FBNeo e ao MAME (o ARENA põe uma cópia na pasta Arcade) |
| PC-FX | `pcfx.rom` |
| 3DO | uma BIOS de 3DO (`panafz10.bin` é a mais comum) |
| Philips CD-i | `cdimono1.zip` inteiro |
| Magnavox Odyssey 2 | `o2rom.bin` |
| ColecoVision | `colecovision.rom` |
| Intellivision | `exec.bin` e `grom.bin` |
| Commodore Amiga | `kick34005.A500` (Kickstart 1.3) |

**Só para alguns jogos:** PlayStation (uma BIOS de qualquer região — sem
ela, o PlayStation liga pela OpenBIOS, a BIOS livre que vem no ARENA, e
quase todos os jogos abrem; com as duas, o ARENA pergunta qual usar) ·
Dreamcast (`dc_boot.bin` — a maioria abre sem ela, pela BIOS imitada do
emulador, mas algum pode travar no meio; com a BIOS na pasta, o ARENA
pergunta qual usar) · Satellaview, os jogos "BS"
do Super Nintendo (`BS-X.bin`) · Sufami Turbo (`STBIOS.bin`) · Famicom Disk
System, os jogos `.fds` (`disksys.rom`) · PC Engine em CD (`syscard3.pce`) ·
64DD (`IPL.n64`) · Videopac+ (`g7400.bin`) · Amiga 1200 e CD32 · os dois
cartuchos do Saturn (o do The King of Fighters '95 e o do Ultraman) · MSX,
os jogos de disquete (`.dsk`) e de fita (`.cas`): a pasta `Machines` do
blueMSX (os de cartucho abrem pelo C-BIOS, a BIOS livre que vem no ARENA).

**Opcionais (o console abre sem; com ela, fica mais fiel):** Atari 5200 ·
Atari 7800 · Atari Lynx · Game Boy e Game Boy Color · Game Boy Advance ·
Nintendo DS · Pokémon mini · a pasta `Databases` do blueMSX (sem ela, o
emulador do MSX adivinha o tipo de cada cartucho) · o TOS original do Atari
ST (`tos.img`; sem ele, o Atari ST liga pelo EmuTOS, a BIOS livre) · o
sistema original do Atari 8-bit (`ATARIXL.ROM` e `ATARIBAS.ROM`; sem eles,
ele liga pelo AltirraOS e pelo Altirra BASIC, livres, que vêm no emulador).

**Sem BIOS nenhuma (o pacote do ARENA não leva BIOS da Sony, da Sega nem da
SNK):** o PlayStation liga pela OpenBIOS, o Dreamcast e o Amiga abrem com
uma imitação da BIOS que vem dentro do emulador, o MSX abre os cartuchos
pelo C-BIOS, o Atari ST liga pelo EmuTOS e o Atari 8-bit, pelo AltirraOS.
O Saturn continua precisando da BIOS: testado em 15/10/2026 com os três
emuladores de Saturn de código aberto. O Kronos e o YabaSanshiro nem ligam
sem ela, e com a imitação da BIOS forçada os três (com o Yabause) abrem com
a tela preta no Saturn Bomberman, mesmo esperando 60 segundos. Com a
`mpr-17933.bin`, o jogo aparece em cerca de 32 segundos. PS2, Sega CD, PC
Engine CD, Neo Geo e os outros da tabela não têm BIOS livre.

**PS2 sem BIOS: o Play! foi testado e ainda não entra.** O Play! é um
emulador de PS2 de código aberto (licença BSD) que imita a BIOS. Em
15/10/2026, ele foi testado com os 37 jogos de PS2 do professor, num Ryzen 5
5600G:

| O que se mediu | Resultado |
|---|---|
| Jogos com imagem | 33 de 37 (Dynasty Warriors 6, Guitar Hero III, Mortal Kombat Deadly Alliance e SOCOM não mostraram nada em 4 minutos) |
| Velocidade | de 47% a 100% da do console: Gun 47%, Black 51%, God Hand 53%, Burnout 3 54%; God of War 80%; Gran Turismo 4 e Dragon Quest VIII 100% |
| Fechar o jogo | o RetroArch fica preso ("Unloading core...") e só sai derrubado: 3 de 3 pela janela, como o aluno fecha |
| Pasta com acento | o emulador cai na hora (numa pasta com "ó" no nome) |

Num Celeron da escola, que é bem mais lento, a velocidade cairia muito
abaixo disso. Por isso o PS2 continua pelo PCSX2, com a BIOS do console. O
Play! volta a ser avaliado quando fechar direito.

#### BIOS livres: as que vêm com o ARENA

Alguns consoles têm uma BIOS livre, escrita do zero por voluntários, que
qualquer um pode copiar. Essas vêm com o ARENA, em `servidor\bios_livres`,
cada uma com a licença dela:

| Console | BIOS livre | O que abre |
|---|---|---|
| MSX | C-BIOS 0.29a (licença BSD) | os jogos de cartucho (`.rom`); disquete e fita continuam pedindo a pasta `Machines` |
| Atari ST | EmuTOS 1.4 (licença GPL) | liga o computador e abre os jogos; o TOS original é opcional |
| PlayStation | OpenBIOS do Libreboot 26.10 (licença MIT) | quase todos os jogos; não tem a tela do memory card nem o tocador de CD de música (salvar dentro do jogo funciona) |

O Atari 8-bit também liga sem BIOS da Atari: o AltirraOS e o Altirra BASIC,
de Avery Lee (licença livre), já vêm dentro do emulador dele (o atari800).
O Vircon32, console de fantasia de código aberto, também traz a BIOS dele
(licença BSD) dentro do emulador. Ele desenha pela placa de vídeo em
OpenGL: o RetroArch troca de motor sozinho para esse console.

Ninguém precisa mexer nela. Ao abrir, o ARENA copia para `retroarch\system`
só o que falta (e atualiza a cópia antiga de um arquivo livre que mudou,
como o `config.ini` do C-BIOS, que em 21/10/2026 ganhou `/` no lugar de `\`
para o MSX abrir no Linux e no Android). **As duas funções continuam
valendo:** a BIOS de verdade, se
você puser na pasta `BIOS`, passa na frente da livre (no MSX, o próprio
emulador escolhe: tenta a máquina original e, sem a BIOS dela, liga a do
C-BIOS; no Atari ST, o TOS original entra no lugar do EmuTOS).

**PlayStation: com as duas, você escolhe.** Pense na peça de um carro: a
original é a de fábrica, e a livre foi feita pela comunidade, para qualquer
um usar. Com a BIOS do PlayStation na pasta `BIOS` e a OpenBIOS que vem no
ARENA, o primeiro jogo de PlayStation pergunta qual usar:

| Escolha | Como liga | Bom para |
|---|---|---|
| BIOS original | com a BIOS do console de verdade | é a mais fiel: todos os jogos abrem |
| BIOS livre (OpenBIOS) | com a BIOS escrita do zero por voluntários | funciona sem nada das empresas |

A caixinha **Lembrar** já vem marcada: o ARENA guarda a resposta e não
pergunta de novo. Para trocar ou voltar a perguntar: **Ajustes → Emuladores
→ Jeito de ligar cada console**. Os dois jeitos usam o mesmo emulador (o
SwanStation), então os saves são os mesmos nos dois. Sem a BIOS da Sony, o
ARENA liga pela OpenBIOS sem perguntar. O **Jogar Junto** continua do jeito
de sempre: o PCSX ReARMed, com a BIOS original se ela estiver na pasta.

A OpenBIOS fica numa pasta só dela, `retroarch\system\OpenBIOS`. Solta na
`system`, o emulador a escolheria até no jeito original: ele procura a BIOS
em ordem alfabética, e `openbios.bin` vem antes de `SCPH1001.BIN` (testado
em 15/10/2026). Nos testes desse dia, os 7 jogos de PlayStation do professor
abriram com a OpenBIOS (Crash Bandicoot, Crash 3, CTR, Soul Reaver, Twisted
Metal 2, Metal Slug X e Vigilante 8). Quem jogou sem BIOS na versão de
15/10, pelo PCSX ReARMed, não perde o save: na primeira vez que o jogo abre
pelo SwanStation, o ARENA leva uma cópia do cartão de memória (o original
fica onde estava).

**Dreamcast: a mesma escolha.** Com a `dc_boot.bin` na pasta, o primeiro
jogo de Dreamcast pergunta: **BIOS original** (a do console, com o logo de
abertura) ou **BIOS imitada (Flycast)**, a que o próprio emulador, de código
aberto, faz no lugar dela: abre mais rápido (pula o logo), e a maioria dos
jogos funciona, mas algum pode travar no meio. Sem a `dc_boot.bin`, o
Dreamcast liga pela imitada sem perguntar, como sempre. Os saves (os VMUs)
são os mesmos nos dois jeitos. Testado em 16/10/2026 com o GigaWing 2 e o
Marvel vs. Capcom 1 do professor, que abriram nos dois.

**Atari ST, Apple II, Atari 8-bit e Java ME numa pasta com acento:** os
emuladores deles (o Hatari, o AppleWin, o atari800 e o FreeJ2ME-Plus) não
abrem arquivo de pasta com acento (como `Área de Trabalho`). O ARENA resolve
sozinho: copia o jogo e a BIOS para uma pasta nova, sem acento e só sua (a
temporária do Windows), abre de lá e, ao fechar, leva de volta o disquete se
o jogo gravou nele (recorde, jogo salvo) e apaga a pasta. A cópia guarda o
nome do jogo, só sem o acento ("Ação.st" vira "Acao.st"): cada jogo tem o
seu estado (F2). Até 15/10/2026, toda cópia se chamava `jogo`, e o estado
de um jogo ficava por cima do de outro.

**Nintendo 64 e Commodore numa pasta com acento:** o mupen64plus-next e o
VICE abrem o jogo, mas gravam os arquivos deles (o cache de imagem e o banco
de jogos `mupen64plus.ini` do N64; a pasta `vice`) pelo jeito antigo do
Windows, em que o "ó" vira "Ã³". Até 15/10/2026, isso criava, fora do ARENA,
uma pasta de nome estragado (com `Ã³` no lugar de cada `ó`): ela só tem
cache e pode ser apagada. Agora o ARENA dá a eles a pasta das BIOS pelo
caminho curto (`system`, a partir da pasta do RetroArch), e tudo fica dentro
do ARENA. De quebra, o N64 passou a ler o banco de jogos, com o ajuste certo
de cada jogo.

**Fliperama (MAME e FBNeo):** cada placa tem a sua BIOS em `.zip`
(`neogeo.zip`, `pgm.zip`, `naomi.zip`...), que vai na mesma pasta dos jogos
dela. O cartão do jogo avisa qual falta.

**Satellaview:** o ARENA reconhece o jogo de Satellaview pelo cabeçalho do
cartucho, do mesmo jeito que o emulador (não só pelo "BS" do nome): o BS
F-Zero Deluxe, por exemplo, é uma versão feita para abrir sozinha e não pede
a BIOS. Com o BS-X, os jogos BS ligam pela tela do BS-X.

#### Os que não pedem nada

Amstrad CPC · Apple II · Arduboy · Atari 2600 · Atari Jaguar · CHIP-8 ·
Commodore 64 · Commodore 128 · Commodore PET · Commodore
Plus/4 · Commodore VIC-20 · Game & Watch ·
GameCube · Java ME (celular antigo) · LowRes NX · Mega Drive, Master System
e Game Gear · MicroW8 · MS-DOS · Neo Geo Pocket · Nintendo Wii · PlayStation Portable ·
ScummVM · Sega 32X · Sega SG-1000 · Tamagotchi · Thomson MO/TO · TIC-80 ·
Uzebox · Vectrex · Vircon32 · Virtual Boy · WASM-4 · Watara Supervision ·
WonderSwan ·
Xbox 360 · ZX Spectrum · ZX81. Também não pedem
o NES, o Super Nintendo, o Nintendo 64 e o PC Engine (só as partes que
aparecem na lista de cima).

#### A bolinha do console

| Cor | Quer dizer |
|---|---|
| Azul | Pronto, é só clicar |
| Amarelo | Falta a BIOS (a linha diz qual) |
| Cinza | Falta baixar o emulador desse console |

---

### Parte C — Consoles cinzas

Falta o emulador daquele console. No RetroArch, o emulador de cada console
se chama **núcleo**. Pense num celular: o RetroArch é o celular, e cada
núcleo é o aplicativo de um console. Console cinza é aplicativo que ainda
não foi baixado. Resolve em um minuto:

1. Abra o `retroarch.exe` direto, fora do ARENA.
2. **Carregar Núcleo → Baixar um Núcleo**.
3. Escolha o que falta na lista.
4. Feche o RetroArch e abra o ARENA.

A bolinha vira azul.

---

### As etiquetas dos jogos

Cada jogo tem uma etiqueta dizendo como vai rodar **no seu computador**:

| Etiqueta | O que esperar |
|---|---|
| **Roda bem** (verde) | Sobra máquina para este console |
| **Roda com ajustes** (azul) | Roda, com a imagem que o ARENA escolhe para este PC. Se engasgar, escolha o Nível do gráfico **Igual ao console original** |
| **Pode travar** (vermelho) | O PC está abaixo do que o console pede. Dá para tentar o Nível do gráfico **Abaixo do original** (leve ou mínimo) e o Ultra desempenho. Documento 3 |
| **Não abre neste PC** (cinza) | Falta algo no processador (ex.: o Xbox 360 exige AVX). Não é configuração. Pare o mouse em cima da etiqueta para ver o motivo |

**"Pode travar" não impede de jogar.** O ARENA só avisa antes, para você não
achar que quebrou. Se quiser tentar, tente — o botão funciona igual.

O ARENA **mede** o computador ao abrir, em vez de adivinhar. Pense no
processador como uma cozinha. O ARENA olha duas coisas:

- **A velocidade de um núcleo.** Cada núcleo do processador é um cozinheiro
  (não confunda com o núcleo do RetroArch). Não basta contar os cozinheiros:
  importa o quanto cada um é rápido.
- **Se o processador tem AVX**, um tipo de instrução extra. O AVX é como
  uma batedeira: algumas receitas só saem com ela. O Xbox 360 é uma delas.
  Nem todo processador tem AVX.

A conta usa o notebook mais fraco da escola como régua: em
**Ajustes → Máquina → Capacidade** aparece, por exemplo, "2,3× o notebook
mais fraco da escola". Quanto o Windows está pesando hoje (programas
abertos, bateria) é outra coisa: aparece na mesma aba e na hora de jogar.

Mais detalhes: **documento 3**, parte "O selo de cada jogo".

---

### Problemas

| O que aconteceu | O que fazer |
|---|---|
| Coloquei o jogo e ele não aparece | Clique em **Atualizar lista**. Confira o final do arquivo na tabela acima |
| Apareceu no console errado | Ponha numa subpasta com o nome do console, ou crie o `_console.txt` (acima) |
| **Muitos jogos** no console errado | Quase sempre são `.iso` ou `.chd` soltos. Ponha cada grupo na sua pasta |
| Bolinha continua amarela | Ainda falta a BIOS (a linha do console diz qual). Ponha o arquivo na pasta do console dentro de `BIOS` e clique em **Conferir** (Ajustes → Emuladores → BIOS dos consoles). Se puser direto em `retroarch\system`, deixe o arquivo solto, sem subpasta. Depois feche e abra o ARENA |
| Bolinha cinza | Baixe o núcleo pelo RetroArch (Parte C) |
| O jogo abre e fecha na hora | Pode ser uma de duas coisas. 1) Falta a BIOS, o "programa de fábrica" do console: veja se a bolinha do console está amarela (parte "Consoles amarelos: a BIOS"). 2) O motor gráfico (por onde o jogo conversa com a placa de vídeo) não funciona neste computador: em **Ajustes → Avançado → Imagem → Motor gráfico**, volte para **Automático** (documento 3) |
| O nome ficou estranho na lista | O ARENA usa o nome do arquivo como título: renomeie o arquivo. Faça isso **antes** de começar a jogar, porque o save segue o nome do arquivo. No fliperama, não renomeie: o `.zip` com outro nome não abre |
| A lista está lenta com muitos jogos | Só na primeira abertura. Depois o ARENA reaproveita e fica rápido |

---

### Regra da turma

**Não passe jogo comercial para os colegas.** A pasta `jogos\pessoais` é sua
e fica no seu pen drive. Não copie para o colega, não distribua pelo
servidor da sala.


---

## Parte B — Consoles que pedem programa próprio

Cinco consoles não abrem pelo RetroArch, e sim por um programa próprio — o
mesmo que a comunidade de cada console mantém. **Os quatro programas já vêm
na pasta do ARENA**, prontos: o ARENA chama cada um sozinho e escreve a
configuração dele antes de cada jogo (controles, imagem, rede).

| Console | Programa | O que mais precisa |
|---|---|---|
| PlayStation 2 | PCSX2 | a BIOS do PS2 em `retroarch\system` (ver "A BIOS") |
| GameCube e Wii | Dolphin | nada |
| PlayStation 3 | RPCS3 | o firmware oficial, instalado uma vez (abaixo) |
| Xbox 360 | Xenia Canary | processador com AVX e computador forte |

Ao abrir um jogo, o aviso diz por qual programa: *"Abrindo Black pelo
PCSX2"*. Em **Ajustes → Emuladores** você vê a lista, com "em uso" ao lado
de cada um — e o que falta, se faltar. Enquanto falta a BIOS do PS2 ou o
firmware do PS3, o cartão do console fica **amarelo** e diz o que fazer.

**Por que não pelo RetroArch?** O núcleo de PS2 dele é pouco mantido e fecha
sem dizer nada quando algo não bate; PS3 e Xbox 360 nem têm núcleo.
PlayStation 1 e PSP continuam pelo RetroArch (o PS1 pelo **SwanStation**,
que nasceu do DuckStation — por isso esse nome aparece em alguns lugares).

#### Trocar por uma versão nova

Baixe sempre a versão **portátil** (`.7z` ou `.zip`), nunca o instalador, e
descompacte por cima da pasta que já existe (`emuladores\PCSX2\`,
`emuladores\Dolphin\`, `emuladores\RPCS3\`, `emuladores\Xenia\`). Se
vier dentro de uma subpasta com o número da versão, tudo bem: o ARENA
procura um nível abaixo também. Feche e abra o ARENA. Assim continua tudo
dentro da pasta do ARENA, sem instalar nada no Windows e sem senha de
administrador.

#### GameCube e Wii pelo Dolphin: controles e pasta

Jogos de **Wii** vão em `jogos\pessoais\Wii`, e os de GameCube em
`jogos\pessoais\GameCube`. Na lista do ARENA, cada um aparece no seu
console (**GameCube** e **Nintendo Wii**). Os dois abrem pelo Dolphin, e o
ARENA lê dentro do disco se ele é de Wii ou de GameCube: se um jogo estiver
na pasta errada, aparece o aviso para mover.

**Dois jeitos de abrir.** O GameCube e o Wii também abrem pelo núcleo do
Dolphin que vem dentro do RetroArch. Com os dois no ARENA, o primeiro jogo
pergunta qual usar, e a resposta fica lembrada (dá para trocar em **Ajustes
→ Emuladores → Jeito de ligar cada console**):

| Jeito | Bom para |
|---|---|
| Dolphin (programa próprio) | é o mais completo e o mais rápido; os controles de Wii (Wii Remote + Nunchuk) vêm prontos |
| Dentro do RetroArch | as mesmas teclas, saves e telas dos outros consoles do ARENA |

O núcleo usa os arquivos de apoio do Dolphin, em
`retroarch\system\dolphin-emu\Sys` (fontes do console, códigos de trapaça e
filtros de imagem), que já vêm no pacote. Sem essa pasta, o ARENA só
oferece o Dolphin de fora. Teste de 15/10/2026, num Ryzen 5 5600G, pelo
núcleo, com os 8 jogos de GameCube e Wii do professor: os 8 abriram e
fecharam direito. F-Zero GX, Super Smash Bros. Melee e New Super Mario Bros.
Wii rodaram na velocidade do console; Smash Bros. Brawl, a 99%; Mario Kart
Wii, a 98%; Mario Kart Double Dash, de 78% a 94%, conforme o disco. Sem a
pasta `Sys`, dois deles não abriam.

#### Aviso de disco na pasta errada

Quando dá para ler dentro do disco de qual console ele é (PS1 × PS2, PSP,
GameCube × Wii, PS3, Xbox 360) e isso não bate com a pasta, a tela do jogo
mostra um **quadro de aviso** e o botão **Mover para...**, que leva o
arquivo para a pasta certa com um clique. O ARENA nunca move sozinho. Disco
de CD que pode ser de vários consoles (Sega CD, Saturn, PS1...) não gera
aviso: o cabeçalho dele não diz qual é, e a pasta decide.

A cada jogo, o ARENA:

- deixa o Dolphin **portátil** (cria o `portable.txt`): configuração e saves
  ficam em `emuladores\Dolphin\...\User`. Sem isso, o Dolphin gravaria em
  `Documentos`, fora do pen drive;
- liga **até 4 controles**, na ordem em que o Windows os numera, e põe o
  **teclado no primeiro jogador sem controle**, como no resto do ARENA;
- ajusta a **imagem**, do mesmo jeito que no PS2:
  - **compilação de efeitos híbrida**: o Dolphin, sozinho, para o jogo a
    cada efeito novo enquanto prepara o desenho (a "travadinha" na
    primeira explosão, no primeiro menu). Com o híbrido, ele mostra uma
    versão provisória enquanto prepara a definitiva, e o jogo não para;
  - **resolução**: nativa do console em placa integrada, no **Gráfico
    original** e em "Mais leve"; 2x em placa dedicada forte ou em "Mais
    bonito" (Ajustes → Emuladores);
  - **Dual Core** ligado (dois núcleos do processador para o jogo);
  - **Ultra desempenho**: abre em tela cheia e sem a pergunta "parar o
    jogo?". Desligou o ultra, volta o que estava antes: se você mesmo tinha
    ligado a tela cheia pela tela do Dolphin, ela continua.

No **GameCube**, cada controle vira um controle de GameCube (RB é o Z,
gatilhos são L e R, analógico direito é o C).

No **Wii**, cada controle vira um **Wii Remote + Nunchuk**:

| No controle | No Wii |
|---|---|
| Analógico esquerdo | Analógico do Nunchuk |
| A | A |
| RT (gatilho direito) | B (gatilho do Wii Remote) |
| LT / LB | Z / C do Nunchuk |
| X / Y | 1 / 2 |
| Start / Back | + / − |
| Analógico direito | Aponta (cursor dos menus) |
| RB | Balançar o controle |

Funciona nos jogos que aceitam Wii Remote + Nunchuk: Mario Kart Wii, Super
Smash Bros. Brawl, New Super Mario Bros. Wii e muitos outros. **Limite:**
jogo que exige apontar para a tela com precisão ou fazer o movimento de
verdade (Wii Sports, por exemplo) não fica bom num controle comum.

Hoje o ARENA liga no Dolphin os controles do tipo **Xbox** (XInput: Xbox,
GameSir e parecidos). Controle de PlayStation ou genérico no Dolphin ainda
precisa ser configurado pela tela do próprio Dolphin.

#### PS3: falta mais um passo (o firmware)

O RPCS3 sozinho não abre jogo nenhum. Ele precisa do **firmware** do PS3 —
o "sistema operacional" do console, o mesmo que a Sony manda como
atualização. Sem ele, o jogo pisca e fecha.

Isso é passo do professor, uma vez só:

1. Baixe o arquivo `PS3UPDAT.PUP` no site oficial da PlayStation (página
   de atualização do sistema do PS3).
2. Abra o `rpcs3.exe` (em `emuladores\RPCS3\RPCS3\`).
3. Menu **File → Install Firmware** e escolha o arquivo baixado.

Enquanto o firmware não está lá, a aba Emuladores mostra o RPCS3 como
**incompleto**, e o ARENA avisa em vez de tentar abrir o jogo.

---

### A BIOS

**BIOS** é o programinha que vem de fábrica dentro do console de verdade e
liga ele por dentro. Sem uma cópia dele, o emulador não sabe nem começar —
é como tentar dar a partida num carro sem a chave: o motor está lá, mas
falta a peça que acorda tudo.

#### Pelos emuladores de fora

**PCSX2:** o ARENA copia uma BIOS de PS2 sozinho (a da pasta `BIOS\PS2`,
instalada em `retroarch\system`) na primeira vez que você abre um jogo por
ele, sem precisar mexer em nada. Em **Ajustes → Emuladores → BIOS dos
consoles**, a do PS2 mostra a região e a versão de cada uma, como o PCSX2
mostra, e qual é a que ele usa para ligar. Se
você já colocou uma BIOS na pasta do PCSX2 antes, o ARENA não mexe nela.
Sem nenhuma BIOS de PS2 (um `.bin` de 4 MB), o cartão do PS2 fica
**amarelo** e diz o que falta — antes de abrir, não depois.

**PS3 (RPCS3):** precisa do firmware oficial instalado nele (ver "PS3: falta
mais um passo"; o arquivo pode ficar guardado na pasta `BIOS\PS3`). Sem ele,
o cartão também fica amarelo, com o caminho.

**Dolphin:** não precisa de BIOS — GameCube e Wii abrem sem ela.

#### Abrir só a BIOS, sem jogo nenhum

Em **Ajustes → Emuladores**, escolha o console e clique em **Abrir só a
BIOS**.

O console abre na tela inicial — aquela onde você acerta a data e a hora,
mexe nos ajustes e vê os saves do memory card com os iconezinhos.

Tudo o que você mudar ali **fica salvo**, porque o ARENA usa sempre o mesmo
arquivo de BIOS e a mesma pasta. Vale para jogos que mudam conforme o
horário, e vale para apagar ou copiar save de um cartão.

Funciona pelo RetroArch e pelo PCSX2 — o ARENA usa o que estiver instalado
para aquele console.

#### Pelo RetroArch: escolher qual usar

Em **Ajustes → Emuladores** tem **Escolher a BIOS e abrir a tela do
console**.

**Na maioria dos consoles não precisa escolher.** O emulador confere o
conteúdo de cada arquivo e acha a BIOS certa sozinho. Esses nem aparecem na
lista.

A escolha só aparece onde o emulador deixa escolher de verdade:

| Console | O que dá para escolher |
|---|---|
| PlayStation 1 | Só arquivos com um destes nomes: `scph5500.bin`, `scph5501.bin`, `scph5502.bin`, `psxonpsp660.bin`, `ps1_rom.bin`, `openbios.bin`. Com outro nome (por exemplo `SCPH1001.BIN`), o emulador ignora a escolha, então a tela nem oferece. Ele acha esse arquivo sozinho do mesmo jeito |
| 3DO | Só as BIOS de 3DO que o emulador conhece (`panafz10.bin`, `panafz1.bin`, `goldstar.bin`...) |

**Por que fixar uma, quando dá:** o console guarda a data, a hora e as
preferências *dentro* da BIOS. Se cada jogo abrir com um arquivo diferente,
o relógio volta para 1 de janeiro toda vez.

---

### Qualidade gráfica do PCSX2, Dolphin, RPCS3 e Xenia

Em **Ajustes → Emuladores** tem o seletor **Automático / Mais leve / Mais
bonito**, com um exemplo de cada opção. Vale para os emuladores de fora
que têm imagem ajustável (PS2, GameCube/Wii, PS3, Xbox 360).

| Opção | O que faz |
|---|---|
| **Automático** | O padrão. Decide pela placa de vídeo desta máquina — mesma lógica do resto do ARENA |
| **Mais leve** | Sempre resolução original do console, sem suavizar nada |
| **Mais bonito** | Sempre a resolução mais alta e o melhor acabamento que o ARENA sabe pedir |

**No PS2, com placa de vídeo integrada** (a dos notebooks da escola, e
também a do Ryzen do professor), o Automático usa a **resolução original**
e a **mistura de cores "Básica"** (o padrão do próprio PCSX2). Foi o que
acabou com o peso nos notebooks: antes ia 2x de resolução, filtro 4x e a
mistura que estivesse escolhida na tela do PCSX2 (estava na "Máxima", a
mais pesada). Quer a imagem mais bonita numa máquina boa? Escolha **Mais
bonito**: aí a mistura que você escolheu na tela do PCSX2 é respeitada. O
**Gráfico original** (Ajustes → Máquina) também usa resolução original e
mistura "Básica".

**Xbox 360 abre sempre no Vulkan.** No modo de vídeo padrão do Xenia
(Direct3D 12), a placa integrada "caía" no meio do jogo — tela preta,
mensagem "Graphics device lost" e o Xenia travado, saindo só pelo
Gerenciador de Tarefas. No Vulkan os mesmos jogos rodaram estáveis.

---

### Memory card

No PlayStation 1, **cada jogo tem o seu próprio cartão**, guardado em:

```
ARENA\retroarch\saves\SwanStation\Nome do Jogo.srm
```

É como ter um memory card separado para cada jogo, com o nome do jogo
escrito na etiqueta. Um jogo nunca apaga o save do outro. O lado ruim: a
tela inicial do console (Abrir só a BIOS) não mostra os saves dos jogos,
porque ali não tem nenhum jogo aberto.

(Até setembro de 2026 este guia dizia que era um cartão só por console.
Essa configuração nunca chegou a valer de verdade, e todo save já feito
está no cartão do próprio jogo. Por isso o ARENA manteve assim: mudar
agora faria os saves de hoje sumirem da tela do jogo.)

O PlayStation 2 usa o PCSX2, que cuida dos cartões dele sozinho.

#### Ver os cartões

Na mesma aba, embaixo, o ARENA lista os cartões que existem — como uma
caixinha de memory cards em cima da TV:

```
Crash Bandicoot (USA)    1 de 15 blocos usados · último uso em 10/09/2026 08:56   [14 livres]
```

Para o cartão de PlayStation 1 ele conta os blocos de verdade, lendo o
índice do cartão — o mesmo número que o console mostrava na tela de memory
card.

O cartão entra no pacote de progresso (documento 4), então você leva os
saves para outro computador junto com o resto.

---

### Data e hora do console

Alguns jogos mudam conforme o horário. O emulador usa **o relógio deste
computador**: se a data do Windows está certa, a do console também está.

Em **Ajustes → Emuladores** você vê a hora atual e onde a BIOS guarda os
ajustes.

Os ajustes que você faz na tela do console — idioma, formato da data, som —
ficam gravados junto da BIOS, em `retroarch\system`. Como o ARENA usa
sempre o mesmo arquivo e a mesma pasta, eles continuam valendo amanhã, e
viajam junto quando você copia a pasta do ARENA.

---

### O que muda quando o emulador de fora assume

| Recurso | Pelo RetroArch | Pelo emulador de fora |
|---|---|---|
| Abrir o jogo pelo ARENA | Sim | **Sim** |
| Contar tempo de jogo | Sim | **Sim** |
| Registrar pontuação | Sim | **Sim** |
| Bolinha e etiqueta na lista | Sim | **Sim** |
| Ajuste de imagem do ARENA | Sim | Não. Configure pelo programa |
| Os 10 save states do ARENA | Sim | Não. Ele tem os dele |
| Cheats pelo ARENA | Sim | Não. Ele tem os dele |
| Jogar junto e assistir | Sim | Não. Ele tem rede própria |
| Esc abre o menu | Sim | Cada programa tem a tecla dele |

O ARENA avisa se você tentar *Jogar junto* num console que está usando
emulador de fora.

---

### Como o ARENA decide

Para cada console, na ordem:

1. **Tem emulador de fora na pasta?** Usa ele. Nem olha o RetroArch.
2. **Tem o núcleo do RetroArch?** Usa o núcleo.
3. **Nenhum dos dois?** A bolinha fica cinza e a lista diz o que instalar.

Você não escolhe nada. Se quiser voltar ao RetroArch, é só tirar a pasta do
emulador de dentro de `emuladores`.

---

### Vale a pena para os opcionais?

**PlayStation 2 e GameCube: sim, é obrigatório.** Os núcleos não dão conta.

**PlayStation, PSP e Dreamcast: provavelmente não.** Os núcleos do RetroArch
já rodam muito bem, e pelo RetroArch você mantém os 10 save states, os
cheats e o jogar junto. Só instale o programa de fora se você quiser alguma
opção específica que só ele tem.

---

### Problemas

| O que aconteceu | O que fazer |
|---|---|
| Coloquei o programa e continua no RetroArch | Feche e abra o ARENA. Confira o nome do arquivo na tabela acima |
| Em Ajustes → Emuladores diz "não instalado" | O executável tem outro nome, ou está fundo demais. Deixe no máximo uma subpasta |
| Abre o emulador mas não carrega o jogo | Quase sempre é BIOS. Abra o emulador direto e siga o que ele pedir |
| Quero voltar ao RetroArch | Tire a pasta de dentro de `emuladores` e reabra o ARENA |
| "Jogar junto só funciona pelo RetroArch" | É esperado. Use a rede do próprio emulador, ou tire a pasta dele |


---
