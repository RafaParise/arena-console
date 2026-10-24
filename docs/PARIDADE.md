# Paridade entre as versões do ARENA

Gerado em 24/10/2026 por `ferramentas\matriz_de_paridade.py` (rode de novo quando entrar console ou núcleo novo).
O servidor Python e a tela (`launcher\`) são **os mesmos** no Windows, no Linux, no Android e no Chromebook com o APK:
toda rota `/api/...` (86) e toda aba existe onde o servidor roda; o que muda é o que cada sistema tem por baixo.

## O que não existe em cada versão, e por quê

| Versão | Falta | Motivo |
|---|---|---|
| Linux | nenhum console | `pokket` e `vemulator` entram pelo `preparar_linux.py` (marcas conferidas); PCSX2, Dolphin, RPCS3 e Xenia são os do Linux, em `emuladores\` |
| Android arm64 | Java ME, PS3, Xbox 360 | o núcleo do Java ME não existe para Android; PS3 e Xbox 360 só por emulador de fora (não cabe no celular) |
| Android x86_64 (Chromebook com o APK) | os mesmos + PS2 | o ARMSX2 é só de arm64; falta compilar a biblioteca do RetroArch para x86_64 (`ferramentas\compilar_retroarch_android.py --abi x86_64`) |
| Navegador (Chromebook sem instalar) | 33 consoles | só os núcleos que o RetroArch do navegador (Emscripten) traz; sem servidor, então sem **Acessórios** (escondidos), sem emuladores de fora e sem BIOS pela tela |
| Só Windows | Lossless Scaling, prioridade e energia do processo, placa pelo `ctypes`, **PokketSX** (PS1 com o PocketStation de verdade, um jeito a mais na pergunta "Como ligar o PlayStation?") | dependem do Windows (no Android e no Linux o servidor usa o que o sistema oferece) |

## Consoles por versão

| Console | Windows | Linux | Android arm64 | Android x86_64 | Navegador |
|---|---|---|---|---|---|
| TIC-80 | sim | sim | sim | sim | sim |
| WASM-4 | sim | sim | sim | sim | sim |
| LowRes NX | sim | sim | sim | sim | sim |
| Uzebox | sim | sim | sim | sim | sim |
| CHIP-8 | sim | sim | sim | sim | sim |
| Arduboy | sim | sim | sim | sim | sim |
| MicroW8 | sim | sim | sim | sim | sim |
| Vircon32 | sim | sim | sim | sim | **não** |
| Atari 2600 | sim | sim | sim | sim | **não** |
| Atari 5200 | sim | sim | sim | sim | **não** |
| Atari 7800 | sim | sim | sim | sim | **não** |
| Atari 8-bit | sim | sim | sim | sim | **não** |
| Atari Lynx | sim | sim | sim | sim | sim |
| Atari Jaguar | sim | sim | sim | sim | **não** |
| Atari ST | sim | sim | sim | sim | **não** |
| Nintendo (NES) | sim | sim | sim | sim | sim |
| Super Nintendo | sim | sim | sim | sim | sim |
| Game Boy e Game Boy Color | sim | sim | sim | sim | sim |
| Game Boy Advance | sim | sim | sim | sim | sim |
| Virtual Boy | sim | sim | sim | sim | sim |
| Pokemon mini | sim | sim | sim | sim | **não** |
| Game & Watch | sim | sim | sim | sim | sim |
| Nintendo 64 | sim | sim | sim | sim | **não** |
| Nintendo DS | sim | sim | sim | sim | **não** |
| GameCube (de fora) | sim | sim | sim | sim | **não** |
| Nintendo Wii (de fora) | sim | sim | sim | sim | **não** |
| Sega SG-1000 | sim | sim | sim | sim | sim |
| Mega Drive, Master System e Game Gear | sim | sim | sim | sim | sim |
| Sega 32X | sim | sim | sim | sim | sim |
| Sega CD | sim | sim | sim | sim | sim |
| Sega Saturn | sim | sim | sim | sim | **não** |
| Sega Dreamcast | sim | sim | sim | sim | **não** |
| PlayStation | sim | sim | sim | sim | sim |
| PlayStation 2 (de fora) | sim | sim | sim | **não** | **não** |
| PlayStation Portable | sim | sim | sim | sim | **não** |
| Neo Geo e fliperamas (FBNeo) | sim | sim | sim | sim | sim |
| Neo Geo Pocket | sim | sim | sim | sim | sim |
| Arcade (MAME) | sim | sim | sim | sim | **não** |
| PC Engine | sim | sim | sim | sim | sim |
| PC-FX | sim | sim | sim | sim | **não** |
| WonderSwan | sim | sim | sim | sim | sim |
| Watara Supervision | sim | sim | sim | sim | **não** |
| 3DO | sim | sim | sim | sim | sim |
| Philips CD-i | sim | sim | sim | sim | **não** |
| Magnavox Odyssey 2 | sim | sim | sim | sim | sim |
| ColecoVision | sim | sim | sim | sim | sim |
| Intellivision | sim | sim | sim | sim | **não** |
| Vectrex | sim | sim | sim | sim | sim |
| MSX | sim | sim | sim | sim | **não** |
| Commodore 64 | sim | sim | sim | sim | sim |
| Commodore 128 | sim | sim | sim | sim | sim |
| Commodore VIC-20 | sim | sim | sim | sim | sim |
| Commodore Plus/4 | sim | sim | sim | sim | sim |
| Commodore PET | sim | sim | sim | sim | sim |
| Commodore Amiga | sim | sim | sim | sim | **não** |
| ZX Spectrum | sim | sim | sim | sim | **não** |
| ZX81 | sim | sim | sim | sim | **não** |
| Amstrad CPC | sim | sim | sim | sim | **não** |
| Apple II | sim | sim | sim | sim | **não** |
| Thomson MO/TO | sim | sim | sim | sim | sim |
| MS-DOS | sim | sim | sim | sim | **não** |
| ScummVM | sim | sim | sim | sim | sim |
| Tamagotchi | sim | sim | sim | sim | sim |
| PocketStation | sim | sim | sim | sim | **não** |
| VMU (Dreamcast) | sim | sim | sim | sim | **não** |
| Java ME (celular antigo) | sim | sim | **não** | **não** | **não** |
| PlayStation 3 (de fora) | sim | sim | **não** | **não** | **não** |
| Xbox 360 (de fora) | sim | sim | **não** | **não** | **não** |

## Funções que só existem em parte (decidido)

- **Acessórios dos consoles** (`docs\ACESSORIOS.md`): Windows, Linux e Android. Navegador: não (sem servidor).
- **Cartão PocketStation na entrada 1 do PS2**: só no celular (ARMSX2). No PC o PCSX2 de fora segue com os cartões do
  Rafael (dado dele; opção a pedir).
- **BIOS-só do PS2 pelo OpenGL na placa fraca**: só no celular.
