# Programas de outros projetos

O ARENA (o código desta pasta: `servidor\`, `launcher\`, os `.bat`, os guias
e as ferramentas) é software livre sob a **GPL-3.0** (arquivo `LICENSE`).

O pacote para baixar leva também os programas abaixo, **sem mudança
nenhuma**, cada um com a sua licença. O ARENA só escreve a configuração
deles antes de abrir um jogo. O código-fonte de cada um está no endereço
da tabela; se precisar da versão exata que foi no pacote, peça pelas
*Issues* do repositório do ARENA.

Nenhum jogo vai no pacote, nem BIOS ou firmware das empresas: são de quem
tem o console. Vão só as **BIOS livres** da tabela abaixo, escritas do zero
por voluntários para qualquer um copiar.

## Programas

| Programa | Licença | Código-fonte | Pasta |
|---|---|---|---|
| Python 3.13 (versão embutida) | PSF License | <https://www.python.org/downloads/source/> | `servidor\python` |
| RetroArch | GPL-3.0 | <https://github.com/libretro/RetroArch> | `retroarch` |
| Recursos do RetroArch (menu, sons) | CC BY 4.0 | <https://github.com/libretro/retroarch-assets> | `retroarch\assets` |
| Filtros de tela do RetroArch (slang-shaders) | licença de cada filtro, no cabeçalho do arquivo | <https://github.com/libretro/slang-shaders> | `retroarch\shaders` |
| Perfis de controle do RetroArch (autoconfig) | a do repositório | <https://github.com/libretro/retroarch-joypad-autoconfig> | `retroarch\autoconfig` |
| PCSX2 (PlayStation 2) | GPL-3.0 ou posterior | <https://github.com/PCSX2/pcsx2> | `emuladores\PCSX2` |
| Dolphin (GameCube e Wii) | GPL-2.0 ou posterior | <https://github.com/dolphin-emu/dolphin> | `emuladores\Dolphin` |
| Arquivos de apoio do núcleo Dolphin do RetroArch (Sys) | GPL-2.0 ou posterior (dolphin-emu\license.txt); as fontes do GameCube, feitas da Droid Sans, Apache 2.0 (Sys\GC\font-licenses.txt) | <https://github.com/libretro/dolphin> | `retroarch\system\dolphin-emu` |
| RPCS3 (PlayStation 3) | GPL-2.0 | <https://github.com/RPCS3/rpcs3> | `emuladores\RPCS3` |
| Xenia Canary (Xbox 360) | BSD-3-Clause | <https://github.com/xenia-canary/xenia-canary> | `emuladores\Xenia` |
| Java do Java ME: OpenJDK 21 (Eclipse Temurin), reduzido com o jlink | GPL-2.0 com a exceção Classpath (os textos vão em emuladores\Java\legal) | <https://github.com/adoptium/temurin21-binaries> | `emuladores\Java` |
| RetroArch 1.22.2 para navegador (WebAssembly), o do ARENA do Chromebook: o build oficial do libretro (buildbot.libretro.com/stable/1.22.2/emscripten), só convertido para abrir do pen drive (ferramentas\preparar_nucleos_navegador.py) | GPL-3.0 (o RetroArch); cada núcleo, a licença dele (tabela do Chromebook, abaixo) | <https://github.com/libretro/RetroArch> | `launcher\navegador\nucleos` |
| Python 3.13 para Linux (python-build-standalone, o do uv) | PSF License (o Python); BSD-3-Clause (a montagem) | <https://github.com/astral-sh/python-build-standalone> | `servidor\python-linux` |
| RetroArch 1.22.2 para Linux (o AppImage oficial do libretro) | GPL-3.0 | <https://github.com/libretro/RetroArch> | `retroarch\RetroArch-Linux-x86_64.AppImage` |
| libgomp do GCC 8 (Debian 10), que o núcleo do Dreamcast pede no Linux | GPL-3.0 com a exceção das bibliotecas do GCC | <https://archive.debian.org/debian/pool/main/g/gcc-8/> | `retroarch\bibliotecas-linux\libgomp.so.1` |
| libjack.so.0 vazia: escrita pelo ARENA, sem nada do JACK (só os nomes das funções, que devolvem 0; ferramentas\jack_vazio.py) | GPL-3.0 (a do ARENA) | <https://github.com/RafaParise/arena-console> | `retroarch\bibliotecas-linux\libjack.so.0` |
| PCSX2 2.8.2 para Linux (AppImage oficial) | GPL-3.0 ou posterior | <https://github.com/PCSX2/pcsx2> | `emuladores\PCSX2\PCSX2` |
| RPCS3 0.0.42 para Linux (AppImage oficial) | GPL-2.0 | <https://github.com/RPCS3/rpcs3> | `emuladores\RPCS3\RPCS3` |
| Xenia Canary para Linux (AppImage oficial) | BSD-3-Clause | <https://github.com/xenia-canary/xenia-canary> | `emuladores\Xenia\Xenia` |
| Java do Java ME para Linux: o mesmo OpenJDK 21 (Eclipse Temurin), reduzido com o jlink | GPL-2.0 com a exceção Classpath (os textos vão em emuladores\Java\linux\legal) | <https://github.com/adoptium/temurin21-binaries> | `emuladores\Java\linux` |

Não vem no ARENA, mas o ARENA usa se estiver no computador de quem comprou:
o **Lossless Scaling** (programa pago, da Steam). Ele não é distribuído
aqui de jeito nenhum; o `servidor\lossless.py` só o acha, ajusta o perfil
"ARENA" dele e o abre junto com o jogo (guia 3, "Lossless Scaling"). O
`.gitignore` e o montador do pacote barram a pasta dele.

## BIOS livres (4)

Ficam em `servidor\bios_livres`, como cada projeto publica (salvo o que vai abaixo), com o texto da
licença ao lado; a `lista.json` dessa pasta guarda a marca (SHA-256) de
cada arquivo. O ARENA as copia para `retroarch\system` só onde falta (e troca a cópia antiga de um arquivo que mudou).

| BIOS | Console | Licença | Código-fonte | Pasta |
|---|---|---|---|---|
| C-BIOS 0.29a | MSX | BSD de 2 cláusulas (o aviso de direitos vai junto, em C-BIOS\doc\cbios.txt) | <https://cbios.sourceforge.net/> | `servidor\bios_livres\C-BIOS` |
| EmuTOS 1.4 | Atari ST | GPL-2.0 ou posterior (o texto vai junto, em EmuTOS\doc\license.txt) | <https://downloads.sourceforge.net/project/emutos/emutos/1.4/emutos-src-1.4.tar.gz> | `servidor\bios_livres\EmuTOS` |
| FreeJ2ME-Plus 1.52 | Java ME | GPL-3.0 (o texto vai junto, em FreeJ2ME-Plus\LICENSE.txt, com as licenças das bibliotecas que vêm dentro: ObjectWeb ASM, JLayer e libsdl4j) | <https://github.com/TASEmulators/freej2me-plus/tree/8f87bf1497e7a9738a32d1909379376a1faca7dd> | `servidor\bios_livres\FreeJ2ME-Plus` |
| OpenBIOS do Libreboot 26.10 | PlayStation | MIT (o texto vai junto, em OpenBIOS\COPYING.txt) | <https://github.com/grumpycoders/pcsx-redux/tree/main/src/mips/openbios> | `servidor\bios_livres\OpenBIOS` |

O que mudou em relação ao que o projeto publica:

- `C-BIOS/configs/blueMSX/MSX - C-BIOS/config.ini`: Os caminhos das ROMs com barra (/) no lugar da barra invertida do pacote: no Linux e no Android, o blueMSX não acha a ROM pelo caminho com \ e não liga esta máquina (21/10/2026). O MSX2 do mesmo pacote já vinha com /.
- `C-BIOS/configs/blueMSX/MSX2+ - C-BIOS/config.ini`: Os caminhos das ROMs com barra (/) no lugar da barra invertida do pacote: no Linux e no Android, o blueMSX não acha a ROM pelo caminho com \ e liga o MSX2 no lugar do MSX2+ (21/10/2026). O MSX2 do mesmo pacote já vinha com /.

## Núcleos do RetroArch (63)

Cada núcleo é o emulador de um console. A licença vem do arquivo `.info`
do próprio núcleo (`retroarch\info`). Os de licença **não comercial**
(Non-commercial) podem ser usados e distribuídos de graça, como aqui,
mas não vendidos. O código-fonte de todos está em
<https://github.com/libretro> (um repositório por núcleo), menos os
que a lista depois da tabela aponta.

| Núcleo | Arquivo | Versão | Licença |
|---|---|---|---|
| Sinclair - ZX 81 (EightyOne) | `81_libretro.dll` | 1.0a | GPLv3 |
| Atari - 5200 (a5200) | `a5200_libretro.dll` | 2.0.2 | GPLv2 |
| Apple II (AppleWin) | `applewin_libretro.dll` | 1.30.21.0 | GPLv2 |
| Arduboy (Ardens) | `ardens_libretro.dll` | Git | MIT |
| Atari - 400/800/600XL/800XL/130XE/5200 (Atari800) | `atari800_libretro.dll` | 3.1.0 | GPLv2 |
| MSX/SVI/ColecoVision/SG-1000 (blueMSX) | `bluemsx_libretro.dll` | SVN | GPLv2 |
| Amstrad - CPC/GX4000 (Caprice32) | `cap32_libretro.dll` | v4.2.0 | GPLv2 |
| Nintendo - GameCube / Wii (Dolphin) | `dolphin_libretro.dll` | Git | GPLv2+ |
| DOS (DOSBox-Pure) | `dosbox_pure_libretro.dll` | 0.9.9 | GPLv2 |
| Arcade (FinalBurn Neo) | `fbneo_libretro.dll` | v1.0.0.03 | Non-commercial |
| Nintendo - NES / Famicom (FCEUmm) | `fceumm_libretro.dll` | SVN | GPLv2 |
| Sega - Dreamcast/Naomi (Flycast) | `flycast_libretro.dll` | Git | GPLv2 |
| Mattel - Intellivision (FreeIntv) | `freeintv_libretro.dll` | 2018.1.5 | GPLv3 |
| Mobile - J2ME (FreeJ2ME-Plus) | `freej2me_libretro.dll` | 1.52-GIT | GPLv3 |
| Sinclair - ZX Spectrum (Fuse) | `fuse_libretro.dll` | 1.6.0 | GPLv3 |
| Nintendo - Game Boy / Color (Gambatte) | `gambatte_libretro.dll` | v0.5.0 | GPLv2 |
| Coleco - ColecoVision (Gearcoleco) | `gearcoleco_libretro.dll` | 1.0.0 | GPLv3 |
| Sega - MS/GG/SG-1000 (Gearsystem) | `gearsystem_libretro.dll` | 3.2.0 | GPLv3 |
| Sega - MS/GG/MD/CD (Genesis Plus GX) | `genesis_plus_gx_libretro.dll` | v1.7.4 | Non-commercial |
| Handheld Electronic (GW) | `gw_libretro.dll` | Git | zlib |
| Atari - Lynx (Handy) | `handy_libretro.dll` | 0.95 | Zlib |
| Atari - ST/STE/TT/Falcon (Hatari) | `hatari_libretro.dll` | 1.8 | GPLv2 |
| CHIP-8/S-CHIP/XO-CHIP (JAXE) | `jaxe_libretro.dll` | GIT | MIT |
| LowRes NX | `lowresnx_libretro.dll` | v1.2 | zlib |
| Arcade (MAME) | `mame_libretro.dll` | Git | GPLv2+ |
| SNK - Neo Geo Pocket / Color (Beetle NeoPop) | `mednafen_ngp_libretro.dll` | v0.9.36.1 | GPLv2 |
| NEC - PC Engine / SuperGrafx / CD (Beetle PCE) | `mednafen_pce_libretro.dll` | v0.9.38.7 | GPLv2 |
| NEC - PC-FX (Beetle PC-FX) | `mednafen_pcfx_libretro.dll` | v0.9.33.3 | GPLv2 |
| Sega - Saturn (Beetle Saturn) | `mednafen_saturn_libretro.dll` | v0.9.45.1 | GPLv2 |
| Nintendo - Virtual Boy (Beetle VB) | `mednafen_vb_libretro.dll` | v0.9.36.1 | GPLv2 |
| Bandai - WonderSwan/Color (Beetle Wonderswan) | `mednafen_wswan_libretro.dll` | v0.9.35.1 | GPLv2 |
| Nintendo - DS (melonDS) | `melonds_libretro.dll` | Git | GPLv3 |
| Nintendo - Game Boy Advance (mGBA) | `mgba_libretro.dll` | 0.10-dev | MPLv2.0 |
| Nintendo - Nintendo 64 (Mupen64Plus-Next) | `mupen64plus_next_libretro.dll` | 1.0 | GPLv2 |
| Magnavox - Odyssey2 / Philips Videopac+ (O2EM) | `o2em_libretro.dll` | 1.18 | Artistic License |
| The 3DO Company - 3DO (Opera) | `opera_libretro.dll` | 1.0.0 | LGPL/Non-commercial |
| Sony - PlayStation 2 (LRPS2) | `pcsx2_libretro.dll` | Git | GPL |
| Sony - PlayStation (PCSX ReARMed) | `pcsx_rearmed_libretro.dll` | r24 | GPLv2 |
| Sega - MS/GG/MD/CD/32X (PicoDrive) | `picodrive_libretro.dll` | 1.99 | MAME |
| Nintendo - Pokemon Mini (PokeMini) | `pokemini_libretro.dll` | v0.60 | GPLv3 |
| Watara - Supervision (Potator) | `potator_libretro.dll` | 1.0.5 | Public Domain |
| Sony - PlayStation Portable (PPSSPP) | `ppsspp_libretro.dll` | Git | GPLv2 |
| Atari - 7800 (ProSystem) | `prosystem_libretro.dll` | 1.3e | GPLv2 |
| Commodore - Amiga (PUAE) | `puae_libretro.dll` | 5.3.0 | GPLv2 |
| Philips - CDi (SAME CDi) | `same_cdi_libretro.dll` | Git | GPLv2+ |
| ScummVM | `scummvm_libretro.dll` | 2.8.0git | GPLv3 |
| Nintendo - SNES / SFC (Snes9x) | `snes9x_libretro.dll` | 1.61 | Non-commercial |
| Atari - 2600 (Stella) | `stella_libretro.dll` | 6.6 | GPLv2 |
| Sony - PlayStation (SwanStation) | `swanstation_libretro.dll` | v0.1 | GPLv3 |
| Bandai - Tamagotchi P1 (TamaLIBretro) | `tamalibretro_libretro.dll` | 1.0 | GPL-2.0 |
| Thomson - MO/TO (Theodore) | `theodore_libretro.dll` | Git | GPLv3 |
| TIC-80 | `tic80_libretro.dll` | 0.80.0 | MIT |
| MicroW8 | `uw8_libretro.dll` | 0.2.2 | The Unlicense |
| Uzebox (Uzem) | `uzem_libretro.dll` | — | MIT |
| GCE - Vectrex (vecx) | `vecx_libretro.dll` | SVN | GPLv3 |
| Commodore - C128 (VICE x128) | `vice_x128_libretro.dll` | 3.9 | GPLv2 |
| Commodore - C64 (VICE x64, fast) | `vice_x64_libretro.dll` | 3.9 | GPLv2 |
| Commodore - PET (VICE xpet) | `vice_xpet_libretro.dll` | 3.9 | GPLv2 |
| Commodore - PLUS/4 (VICE xplus4) | `vice_xplus4_libretro.dll` | 3.9 | GPLv2 |
| Commodore - VIC-20 (VICE xvic) | `vice_xvic_libretro.dll` | 3.9 | GPLv2 |
| Vircon32 | `vircon32_libretro.dll` | 2024.08.28 | 3-clause BSD |
| Atari - Jaguar (Virtual Jaguar) | `virtualjaguar_libretro.dll` | v2.1.0 | GPLv3 |
| WASM-4 | `wasm4_libretro.dll` | 2.1.0 | ISC |

Código-fonte fora do libretro:

- `freej2me_libretro.dll`: <https://github.com/TASEmulators/freej2me-plus/tree/8f87bf1497e7a9738a32d1909379376a1faca7dd>

## Núcleos do RetroArch no Linux (63)

Os mesmos núcleos, na versão para Linux do mesmo RetroArch 1.22.2 (o
`RetroArch_cores.7z` do libretro): ficam ao lado dos do Windows, em
`retroarch\cores`, com a mesma licença (o mesmo `.info`) e o mesmo
código-fonte. Só a extensão muda: `.so` no lugar de `.dll`.

| Núcleo | Arquivo | Licença |
|---|---|---|
| Sinclair - ZX 81 (EightyOne) | `81_libretro.so` | GPLv3 |
| Atari - 5200 (a5200) | `a5200_libretro.so` | GPLv2 |
| Apple II (AppleWin) | `applewin_libretro.so` | GPLv2 |
| Arduboy (Ardens) | `ardens_libretro.so` | MIT |
| Atari - 400/800/600XL/800XL/130XE/5200 (Atari800) | `atari800_libretro.so` | GPLv2 |
| MSX/SVI/ColecoVision/SG-1000 (blueMSX) | `bluemsx_libretro.so` | GPLv2 |
| Amstrad - CPC/GX4000 (Caprice32) | `cap32_libretro.so` | GPLv2 |
| Nintendo - GameCube / Wii (Dolphin) | `dolphin_libretro.so` | GPLv2+ |
| DOS (DOSBox-Pure) | `dosbox_pure_libretro.so` | GPLv2 |
| Arcade (FinalBurn Neo) | `fbneo_libretro.so` | Non-commercial |
| Nintendo - NES / Famicom (FCEUmm) | `fceumm_libretro.so` | GPLv2 |
| Sega - Dreamcast/Naomi (Flycast) | `flycast_libretro.so` | GPLv2 |
| Mattel - Intellivision (FreeIntv) | `freeintv_libretro.so` | GPLv3 |
| Mobile - J2ME (FreeJ2ME-Plus) | `freej2me_libretro.so` | GPLv3 |
| Sinclair - ZX Spectrum (Fuse) | `fuse_libretro.so` | GPLv3 |
| Nintendo - Game Boy / Color (Gambatte) | `gambatte_libretro.so` | GPLv2 |
| Coleco - ColecoVision (Gearcoleco) | `gearcoleco_libretro.so` | GPLv3 |
| Sega - MS/GG/SG-1000 (Gearsystem) | `gearsystem_libretro.so` | GPLv3 |
| Sega - MS/GG/MD/CD (Genesis Plus GX) | `genesis_plus_gx_libretro.so` | Non-commercial |
| Handheld Electronic (GW) | `gw_libretro.so` | zlib |
| Atari - Lynx (Handy) | `handy_libretro.so` | Zlib |
| Atari - ST/STE/TT/Falcon (Hatari) | `hatari_libretro.so` | GPLv2 |
| CHIP-8/S-CHIP/XO-CHIP (JAXE) | `jaxe_libretro.so` | MIT |
| LowRes NX | `lowresnx_libretro.so` | zlib |
| Arcade (MAME) | `mame_libretro.so` | GPLv2+ |
| SNK - Neo Geo Pocket / Color (Beetle NeoPop) | `mednafen_ngp_libretro.so` | GPLv2 |
| NEC - PC Engine / SuperGrafx / CD (Beetle PCE) | `mednafen_pce_libretro.so` | GPLv2 |
| NEC - PC-FX (Beetle PC-FX) | `mednafen_pcfx_libretro.so` | GPLv2 |
| Sega - Saturn (Beetle Saturn) | `mednafen_saturn_libretro.so` | GPLv2 |
| Nintendo - Virtual Boy (Beetle VB) | `mednafen_vb_libretro.so` | GPLv2 |
| Bandai - WonderSwan/Color (Beetle Wonderswan) | `mednafen_wswan_libretro.so` | GPLv2 |
| Nintendo - DS (melonDS) | `melonds_libretro.so` | GPLv3 |
| Nintendo - Game Boy Advance (mGBA) | `mgba_libretro.so` | MPLv2.0 |
| Nintendo - Nintendo 64 (Mupen64Plus-Next) | `mupen64plus_next_libretro.so` | GPLv2 |
| Magnavox - Odyssey2 / Philips Videopac+ (O2EM) | `o2em_libretro.so` | Artistic License |
| The 3DO Company - 3DO (Opera) | `opera_libretro.so` | LGPL/Non-commercial |
| Sony - PlayStation 2 (LRPS2) | `pcsx2_libretro.so` | GPL |
| Sony - PlayStation (PCSX ReARMed) | `pcsx_rearmed_libretro.so` | GPLv2 |
| Sega - MS/GG/MD/CD/32X (PicoDrive) | `picodrive_libretro.so` | MAME |
| Nintendo - Pokemon Mini (PokeMini) | `pokemini_libretro.so` | GPLv3 |
| Watara - Supervision (Potator) | `potator_libretro.so` | Public Domain |
| Sony - PlayStation Portable (PPSSPP) | `ppsspp_libretro.so` | GPLv2 |
| Atari - 7800 (ProSystem) | `prosystem_libretro.so` | GPLv2 |
| Commodore - Amiga (PUAE) | `puae_libretro.so` | GPLv2 |
| Philips - CDi (SAME CDi) | `same_cdi_libretro.so` | GPLv2+ |
| ScummVM | `scummvm_libretro.so` | GPLv3 |
| Nintendo - SNES / SFC (Snes9x) | `snes9x_libretro.so` | Non-commercial |
| Atari - 2600 (Stella) | `stella_libretro.so` | GPLv2 |
| Sony - PlayStation (SwanStation) | `swanstation_libretro.so` | GPLv3 |
| Bandai - Tamagotchi P1 (TamaLIBretro) | `tamalibretro_libretro.so` | GPL-2.0 |
| Thomson - MO/TO (Theodore) | `theodore_libretro.so` | GPLv3 |
| TIC-80 | `tic80_libretro.so` | MIT |
| MicroW8 | `uw8_libretro.so` | The Unlicense |
| Uzebox (Uzem) | `uzem_libretro.so` | MIT |
| GCE - Vectrex (vecx) | `vecx_libretro.so` | GPLv3 |
| Commodore - C128 (VICE x128) | `vice_x128_libretro.so` | GPLv2 |
| Commodore - C64 (VICE x64, fast) | `vice_x64_libretro.so` | GPLv2 |
| Commodore - PET (VICE xpet) | `vice_xpet_libretro.so` | GPLv2 |
| Commodore - PLUS/4 (VICE xplus4) | `vice_xplus4_libretro.so` | GPLv2 |
| Commodore - VIC-20 (VICE xvic) | `vice_xvic_libretro.so` | GPLv2 |
| Vircon32 | `vircon32_libretro.so` | 3-clause BSD |
| Atari - Jaguar (Virtual Jaguar) | `virtualjaguar_libretro.so` | GPLv3 |
| WASM-4 | `wasm4_libretro.so` | ISC |

## Núcleos do ARENA no Chromebook (34)

No Chromebook, o ARENA roda dentro do navegador (`ARENA-CHROMEBOOK.html`),
com estes núcleos na versão que o libretro compila para WebAssembly, do
mesmo RetroArch 1.22.2: dois arquivos cada um em `launcher\navegador\nucleos`
(o programa e o emulador compactado). A licença é a do mesmo núcleo
(o `.info` dele); o código-fonte, o repositório dele em
<https://github.com/libretro>.

| Núcleo | Arquivos | Consoles | Licença |
|---|---|---|---|
| Arduboy (Ardens) | `ardens.js`, `ardens.wasm.js` | Arduboy | MIT |
| Arcade (FinalBurn Neo) | `fbneo.js`, `fbneo.wasm.js` | Neo Geo e fliperamas (FBNeo) | Non-commercial |
| Nintendo - NES / Famicom (FCEUmm) | `fceumm.js`, `fceumm.wasm.js` | Nintendo (NES) | GPLv2 |
| Nintendo - Game Boy / Color (Gambatte) | `gambatte.js`, `gambatte.wasm.js` | Game Boy e Game Boy Color | GPLv2 |
| Coleco - ColecoVision (Gearcoleco) | `gearcoleco.js`, `gearcoleco.wasm.js` | ColecoVision | GPLv3 |
| Sega - MS/GG/SG-1000 (Gearsystem) | `gearsystem.js`, `gearsystem.wasm.js` | Sega SG-1000 | GPLv3 |
| Sega - MS/GG/MD/CD (Genesis Plus GX) | `genesis_plus_gx.js`, `genesis_plus_gx.wasm.js` | Mega Drive, Master System e Game Gear, Sega CD | Non-commercial |
| Handheld Electronic (GW) | `gw.js`, `gw.wasm.js` | Game & Watch | zlib |
| Atari - Lynx (Handy) | `handy.js`, `handy.wasm.js` | Atari Lynx | Zlib |
| CHIP-8/S-CHIP/XO-CHIP (JAXE) | `jaxe.js`, `jaxe.wasm.js` | CHIP-8 | MIT |
| LowRes NX | `lowresnx.js`, `lowresnx.wasm.js` | LowRes NX | zlib |
| SNK - Neo Geo Pocket / Color (Beetle NeoPop) | `mednafen_ngp.js`, `mednafen_ngp.wasm.js` | Neo Geo Pocket | GPLv2 |
| NEC - PC Engine / CD (Beetle PCE FAST) | `mednafen_pce_fast.js`, `mednafen_pce_fast.wasm.js` | PC Engine | GPLv2 |
| Nintendo - Virtual Boy (Beetle VB) | `mednafen_vb.js`, `mednafen_vb.wasm.js` | Virtual Boy | GPLv2 |
| Bandai - WonderSwan/Color (Beetle Wonderswan) | `mednafen_wswan.js`, `mednafen_wswan.wasm.js` | WonderSwan | GPLv2 |
| Nintendo - Game Boy Advance (mGBA) | `mgba.js`, `mgba.wasm.js` | Game Boy Advance | MPLv2.0 |
| Magnavox - Odyssey2 / Philips Videopac+ (O2EM) | `o2em.js`, `o2em.wasm.js` | Magnavox Odyssey 2 | Artistic License |
| The 3DO Company - 3DO (Opera) | `opera.js`, `opera.wasm.js` | 3DO | LGPL/Non-commercial |
| Sony - PlayStation (PCSX ReARMed) | `pcsx_rearmed.js`, `pcsx_rearmed.wasm.js` | PlayStation | GPLv2 |
| Sega - MS/GG/MD/CD/32X (PicoDrive) | `picodrive.js`, `picodrive.wasm.js` | Sega 32X | MAME |
| ScummVM | `scummvm.js`, `scummvm.wasm.js` | ScummVM | GPLv3 |
| Nintendo - SNES / SFC (Snes9x) | `snes9x.js`, `snes9x.wasm.js` | Super Nintendo | Non-commercial |
| Bandai - Tamagotchi P1 (TamaLIBretro) | `tamalibretro.js`, `tamalibretro.wasm.js` | Tamagotchi | GPL-2.0 |
| Thomson - MO/TO (Theodore) | `theodore.js`, `theodore.wasm.js` | Thomson MO/TO | GPLv3 |
| TIC-80 | `tic80.js`, `tic80.wasm.js` | TIC-80 | MIT |
| MicroW8 | `uw8.js`, `uw8.wasm.js` | MicroW8 | The Unlicense |
| Uzebox (Uzem) | `uzem.js`, `uzem.wasm.js` | Uzebox | MIT |
| GCE - Vectrex (vecx) | `vecx.js`, `vecx.wasm.js` | Vectrex | GPLv3 |
| Commodore - C128 (VICE x128) | `vice_x128.js`, `vice_x128.wasm.js` | Commodore 128 | GPLv2 |
| Commodore - C64 (VICE x64, fast) | `vice_x64.js`, `vice_x64.wasm.js` | Commodore 64 | GPLv2 |
| Commodore - PET (VICE xpet) | `vice_xpet.js`, `vice_xpet.wasm.js` | Commodore PET | GPLv2 |
| Commodore - PLUS/4 (VICE xplus4) | `vice_xplus4.js`, `vice_xplus4.wasm.js` | Commodore Plus/4 | GPLv2 |
| Commodore - VIC-20 (VICE xvic) | `vice_xvic.js`, `vice_xvic.wasm.js` | Commodore VIC-20 | GPLv2 |
| WASM-4 | `wasm4.js`, `wasm4.wasm.js` | WASM-4 | ISC |

## Jogos livres que vêm junto no Chromebook (5)

Para o Chromebook ter jogo na primeira vez e para o "Testar este
Chromebook" medir sem pen drive, vão embutidos em
`launcher\navegador\livres.js` estes jogos de licença livre (os mesmos de
`testes\jogos_livres`, conferidos pela marca SHA-256 da `lista.json`):

| Jogo | Console | Autor | Licença | Código-fonte |
|---|---|---|---|---|
| Evade | Arduboy | Modus Create | MIT | <https://github.com/ModusCreateOrg/evade-arduboy-game> |
| Slippery Slope | CHIP-8 | John Earnest | CC0 (domínio público), como todo o Chip8 Community Archive | <https://github.com/JohnEarnest/chip8Archive> |
| Skip Ahead | MicroW8 | Dennis Ranke (exoticorn) | Unlicense (domínio público) | <https://github.com/exoticorn/microw8> |
| Intervallo | Commodore Plus/4 | Zalka Ernő (ern0) | MIT | <https://github.com/ern0/intervallo> |
| Baguel | Commodore VIC-20 | Marco Giorgini (MGProduction) | MIT | <https://github.com/mgproduction/baguel> |

## O APK do Android

O APK do ARENA (Releases do GitHub, um por tipo de processador) leva o
servidor e a tela do ARENA (GPL-3.0) e estes programas de outros
projetos. Um deles vai **com mudança**, dita na tabela e no
`docs/ANDROID.md`: a GPL-3.0 do RetroArch pede que a versão modificada
diga que é modificada e onde está o código dela.

| Programa | Licença | Código-fonte |
|---|---|---|
| RetroArch 1.22.2 para Android (o RetroArch.apk oficial do libretro), **com uma mudança**: a biblioteca `lib/<abi>/libretroarch-activity.so` compilada do código oficial (a etiqueta v1.22.2) com o remendo `android/retroarch/arena-args.patch` do ARENA (a linha de comando inteira pela intent), em 18/10/2026, por `ferramentas/compilar_retroarch_android.py`. O resto do RetroArch.apk vai como veio | GPL-3.0 | https://github.com/libretro/RetroArch (a etiqueta v1.22.2) + o remendo, neste repositório |
| Recursos do RetroArch que vêm no RetroArch.apk (menu, perfis de controle do Android, controle de toque, informações dos núcleos, filtros de som e imagem) | os de cada repositório: retroarch-assets (CC BY 4.0), common-overlays, retroarch-joypad-autoconfig, libretro-core-info e os filtros do RetroArch | https://github.com/libretro |
| Python 3.13.16 para Android: o CPython compilado pelo Chaquopy (os pacotes "target" do Maven Central), sem mudança, com o OpenSSL, o SQLite, o libffi, o bzip2 e o xz dele | PSF License (o Python); MIT (o Chaquopy); Apache-2.0 (o OpenSSL); domínio público (o SQLite); MIT (o libffi); bzip2 e xz, as deles | https://github.com/chaquo/chaquopy e https://www.python.org/downloads/source/ |
| O lançador do Python (`lib/<abi>/libarenapython.so`): escrito pelo ARENA (`android/python/lancador.c`) | GPL-3.0 (a do ARENA) | https://github.com/RafaParise/arena-console |

### Núcleos do RetroArch no APK do Android (62)

Os mesmos núcleos, na versão para Android que o libretro publica (o
"nightly", com a marca SHA-256 de cada um em
`ferramentas/android_nucleos.json`), com a licença do mesmo `.info` e o
mesmo código-fonte (<https://github.com/libretro>).

| Núcleo | Arquivo | Licença |
|---|---|---|
| Sinclair - ZX 81 (EightyOne) | `81_libretro_android.so` | GPLv3 |
| Atari - 5200 (a5200) | `a5200_libretro_android.so` | GPLv2 |
| Apple II (AppleWin) | `applewin_libretro_android.so` | GPLv2 |
| Arduboy (Ardens) | `ardens_libretro_android.so` | MIT |
| Atari - 400/800/600XL/800XL/130XE/5200 (Atari800) | `atari800_libretro_android.so` | GPLv2 |
| MSX/SVI/ColecoVision/SG-1000 (blueMSX) | `bluemsx_libretro_android.so` | GPLv2 |
| Amstrad - CPC/GX4000 (Caprice32) | `cap32_libretro_android.so` | GPLv2 |
| Nintendo - GameCube / Wii (Dolphin) | `dolphin_libretro_android.so` | GPLv2+ |
| DOS (DOSBox-Pure) | `dosbox_pure_libretro_android.so` | GPLv2 |
| Arcade (FinalBurn Neo) | `fbneo_libretro_android.so` | Non-commercial |
| Nintendo - NES / Famicom (FCEUmm) | `fceumm_libretro_android.so` | GPLv2 |
| Sega - Dreamcast/Naomi (Flycast) | `flycast_libretro_android.so` | GPLv2 |
| Mattel - Intellivision (FreeIntv) | `freeintv_libretro_android.so` | GPLv3 |
| Sinclair - ZX Spectrum (Fuse) | `fuse_libretro_android.so` | GPLv3 |
| Nintendo - Game Boy / Color (Gambatte) | `gambatte_libretro_android.so` | GPLv2 |
| Coleco - ColecoVision (Gearcoleco) | `gearcoleco_libretro_android.so` | GPLv3 |
| Sega - MS/GG/SG-1000 (Gearsystem) | `gearsystem_libretro_android.so` | GPLv3 |
| Sega - MS/GG/MD/CD (Genesis Plus GX) | `genesis_plus_gx_libretro_android.so` | Non-commercial |
| Handheld Electronic (GW) | `gw_libretro_android.so` | zlib |
| Atari - Lynx (Handy) | `handy_libretro_android.so` | Zlib |
| Atari - ST/STE/TT/Falcon (Hatari) | `hatari_libretro_android.so` | GPLv2 |
| CHIP-8/S-CHIP/XO-CHIP (JAXE) | `jaxe_libretro_android.so` | MIT |
| LowRes NX | `lowresnx_libretro_android.so` | zlib |
| Arcade (MAME/Arcade) | `mamearcade_libretro_android.so` | GPLv2+ |
| SNK - Neo Geo Pocket / Color (Beetle NeoPop) | `mednafen_ngp_libretro_android.so` | GPLv2 |
| NEC - PC Engine / SuperGrafx / CD (Beetle PCE) | `mednafen_pce_libretro_android.so` | GPLv2 |
| NEC - PC-FX (Beetle PC-FX) | `mednafen_pcfx_libretro_android.so` | GPLv2 |
| Sega - Saturn (Beetle Saturn) | `mednafen_saturn_libretro_android.so` | GPLv2 |
| Nintendo - Virtual Boy (Beetle VB) | `mednafen_vb_libretro_android.so` | GPLv2 |
| Bandai - WonderSwan/Color (Beetle Wonderswan) | `mednafen_wswan_libretro_android.so` | GPLv2 |
| Nintendo - DS (melonDS) | `melonds_libretro_android.so` | GPLv3 |
| Nintendo - Game Boy Advance (mGBA) | `mgba_libretro_android.so` | MPLv2.0 |
| Nintendo - Nintendo 64 (Mupen64Plus-Next GLES3) | `mupen64plus_next_gles3_libretro_android.so` | GPLv2 |
| Magnavox - Odyssey2 / Philips Videopac+ (O2EM) | `o2em_libretro_android.so` | Artistic License |
| The 3DO Company - 3DO (Opera) | `opera_libretro_android.so` | LGPL/Non-commercial |
| Sony - PlayStation 2 (LRPS2) | `pcsx2_libretro_android.so` | GPL |
| Sony - PlayStation (PCSX ReARMed) | `pcsx_rearmed_libretro_android.so` | GPLv2 |
| Sega - MS/GG/MD/CD/32X (PicoDrive) | `picodrive_libretro_android.so` | MAME |
| Nintendo - Pokemon Mini (PokeMini) | `pokemini_libretro_android.so` | GPLv3 |
| Watara - Supervision (Potator) | `potator_libretro_android.so` | Public Domain |
| Sony - PlayStation Portable (PPSSPP) | `ppsspp_libretro_android.so` | GPLv2 |
| Atari - 7800 (ProSystem) | `prosystem_libretro_android.so` | GPLv2 |
| Commodore - Amiga (PUAE) | `puae_libretro_android.so` | GPLv2 |
| Philips - CDi (SAME CDi) | `same_cdi_libretro_android.so` | GPLv2+ |
| ScummVM | `scummvm_libretro_android.so` | GPLv3 |
| Nintendo - SNES / SFC (Snes9x) | `snes9x_libretro_android.so` | Non-commercial |
| Atari - 2600 (Stella) | `stella_libretro_android.so` | GPLv2 |
| Sony - PlayStation (SwanStation) | `swanstation_libretro_android.so` | GPLv3 |
| Bandai - Tamagotchi P1 (TamaLIBretro) | `tamalibretro_libretro_android.so` | GPL-2.0 |
| Thomson - MO/TO (Theodore) | `theodore_libretro_android.so` | GPLv3 |
| TIC-80 | `tic80_libretro_android.so` | MIT |
| MicroW8 | `uw8_libretro_android.so` | The Unlicense |
| Uzebox (Uzem) | `uzem_libretro_android.so` | MIT |
| GCE - Vectrex (vecx) | `vecx_libretro_android.so` | GPLv3 |
| Commodore - C128 (VICE x128) | `vice_x128_libretro_android.so` | GPLv2 |
| Commodore - C64 (VICE x64, fast) | `vice_x64_libretro_android.so` | GPLv2 |
| Commodore - PET (VICE xpet) | `vice_xpet_libretro_android.so` | GPLv2 |
| Commodore - PLUS/4 (VICE xplus4) | `vice_xplus4_libretro_android.so` | GPLv2 |
| Commodore - VIC-20 (VICE xvic) | `vice_xvic_libretro_android.so` | GPLv2 |
| Vircon32 | `vircon32_libretro_android.so` | 3-clause BSD |
| Atari - Jaguar (Virtual Jaguar) | `virtualjaguar_libretro_android.so` | GPLv3 |
| WASM-4 | `wasm4_libretro_android.so` | ISC |

### Jogos livres que vêm no APK (8)

Sem pasta do ARENA no aparelho, o ARENA do Android põe estes jogos na
pasta dele (os de `testes\jogos_livres` que o Android abre), cada um
com o texto da licença ao lado:

| Jogo | Console | Autor | Licença | Código-fonte |
|---|---|---|---|---|
| DIAFLW | Apple II | Randall Frank | MIT | <https://github.com/randall-frank/DIAFLW> |
| Evade | Arduboy | Modus Create | MIT | <https://github.com/ModusCreateOrg/evade-arduboy-game> |
| Slippery Slope | CHIP-8 | John Earnest | CC0 (domínio público), como todo o Chip8 Community Archive | <https://github.com/JohnEarnest/chip8Archive> |
| NOBORUNOCA | MSX | Hiromasa Tanaka (h1romas4) | MIT (código e recursos: gráficos e música) | <https://github.com/h1romas4/noborunoca> |
| Skip Ahead | MicroW8 | Dennis Ranke (exoticorn) | Unlicense (domínio público) | <https://github.com/exoticorn/microw8> |
| Intervallo | Commodore Plus/4 | Zalka Ernő (ern0) | MIT | <https://github.com/ern0/intervallo> |
| Baguel | Commodore VIC-20 | Marco Giorgini (MGProduction) | MIT | <https://github.com/mgproduction/baguel> |
| Factory 2023 | ZX81 | Sebastien Andrivet | GPL-3.0 | <https://github.com/andrivet/Factory-2023> |
