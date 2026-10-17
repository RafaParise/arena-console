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

Não vem no ARENA, mas o ARENA usa se estiver no computador de quem comprou:
o **Lossless Scaling** (programa pago, da Steam). Ele não é distribuído
aqui de jeito nenhum; o `servidor\lossless.py` só o acha, ajusta o perfil
"ARENA" dele e o abre junto com o jogo (guia 3, "Lossless Scaling"). O
`.gitignore` e o montador do pacote barram a pasta dele.

## BIOS livres (4)

Ficam em `servidor\bios_livres`, sem mudança nenhuma, com o texto da
licença ao lado; a `lista.json` dessa pasta guarda a marca (SHA-256) de
cada arquivo. O ARENA as copia para `retroarch\system` só onde falta.

| BIOS | Console | Licença | Código-fonte | Pasta |
|---|---|---|---|---|
| C-BIOS 0.29a | MSX | BSD de 2 cláusulas (o aviso de direitos vai junto, em C-BIOS\doc\cbios.txt) | <https://cbios.sourceforge.net/> | `servidor\bios_livres\C-BIOS` |
| EmuTOS 1.4 | Atari ST | GPL-2.0 ou posterior (o texto vai junto, em EmuTOS\doc\license.txt) | <https://downloads.sourceforge.net/project/emutos/emutos/1.4/emutos-src-1.4.tar.gz> | `servidor\bios_livres\EmuTOS` |
| FreeJ2ME-Plus 1.52 | Java ME | GPL-3.0 (o texto vai junto, em FreeJ2ME-Plus\LICENSE.txt, com as licenças das bibliotecas que vêm dentro: ObjectWeb ASM, JLayer e libsdl4j) | <https://github.com/TASEmulators/freej2me-plus/tree/8f87bf1497e7a9738a32d1909379376a1faca7dd> | `servidor\bios_livres\FreeJ2ME-Plus` |
| OpenBIOS do Libreboot 26.10 | PlayStation | MIT (o texto vai junto, em OpenBIOS\COPYING.txt) | <https://github.com/grumpycoders/pcsx-redux/tree/main/src/mips/openbios> | `servidor\bios_livres\OpenBIOS` |

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
