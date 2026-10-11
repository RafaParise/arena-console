# Programas de outros projetos

O ARENA (o código desta pasta: `servidor\`, `launcher\`, os `.bat`, os guias
e as ferramentas) é software livre sob a **GPL-3.0** (arquivo `LICENSE`).

O pacote para baixar leva também os programas abaixo, **sem mudança
nenhuma**, cada um com a sua licença. O ARENA só escreve a configuração
deles antes de abrir um jogo. O código-fonte de cada um está no endereço
da tabela; se precisar da versão exata que foi no pacote, peça pelas
*Issues* do repositório do ARENA.

Nenhum jogo, BIOS ou firmware vai no pacote: são de quem tem o console.

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
| RPCS3 (PlayStation 3) | GPL-2.0 | <https://github.com/RPCS3/rpcs3> | `emuladores\RPCS3` |
| Xenia Canary (Xbox 360) | BSD-3-Clause | <https://github.com/xenia-canary/xenia-canary> | `emuladores\Xenia` |

## Núcleos do RetroArch (48)

Cada núcleo é o emulador de um console. A licença vem do arquivo `.info`
do próprio núcleo (`retroarch\info`). Os de licença **não comercial**
(Non-commercial) podem ser usados e distribuídos de graça, como aqui,
mas não vendidos. O código-fonte de todos está em
<https://github.com/libretro> (um repositório por núcleo).

| Núcleo | Arquivo | Versão | Licença |
|---|---|---|---|
| Atari - 5200 (a5200) | `a5200_libretro.dll` | 2.0.2 | GPLv2 |
| MSX/SVI/ColecoVision/SG-1000 (blueMSX) | `bluemsx_libretro.dll` | SVN | GPLv2 |
| Amstrad - CPC/GX4000 (Caprice32) | `cap32_libretro.dll` | v4.2.0 | GPLv2 |
| Nintendo - GameCube / Wii (Dolphin) | `dolphin_libretro.dll` | Git | GPLv2+ |
| DOS (DOSBox-Pure) | `dosbox_pure_libretro.dll` | 0.9.9 | GPLv2 |
| Arcade (FinalBurn Neo) | `fbneo_libretro.dll` | v1.0.0.03 | Non-commercial |
| Nintendo - NES / Famicom (FCEUmm) | `fceumm_libretro.dll` | SVN | GPLv2 |
| Sega - Dreamcast/Naomi (Flycast) | `flycast_libretro.dll` | Git | GPLv2 |
| Mattel - Intellivision (FreeIntv) | `freeintv_libretro.dll` | 2018.1.5 | GPLv3 |
| Sinclair - ZX Spectrum (Fuse) | `fuse_libretro.dll` | 1.6.0 | GPLv3 |
| Nintendo - Game Boy / Color (Gambatte) | `gambatte_libretro.dll` | v0.5.0 | GPLv2 |
| Coleco - ColecoVision (Gearcoleco) | `gearcoleco_libretro.dll` | 1.0.0 | GPLv3 |
| Sega - MS/GG/SG-1000 (Gearsystem) | `gearsystem_libretro.dll` | 3.2.0 | GPLv3 |
| Sega - MS/GG/MD/CD (Genesis Plus GX) | `genesis_plus_gx_libretro.dll` | v1.7.4 | Non-commercial |
| Handheld Electronic (GW) | `gw_libretro.dll` | Git | zlib |
| Atari - Lynx (Handy) | `handy_libretro.dll` | 0.95 | Zlib |
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
| Sony - PlayStation Portable (PPSSPP) | `ppsspp_libretro.dll` | Git | GPLv2 |
| Atari - 7800 (ProSystem) | `prosystem_libretro.dll` | 1.3e | GPLv2 |
| Commodore - Amiga (PUAE) | `puae_libretro.dll` | 5.3.0 | GPLv2 |
| Philips - CDi (SAME CDi) | `same_cdi_libretro.dll` | Git | GPLv2+ |
| ScummVM | `scummvm_libretro.dll` | 2.8.0git | GPLv3 |
| Nintendo - SNES / SFC (Snes9x) | `snes9x_libretro.dll` | 1.61 | Non-commercial |
| Atari - 2600 (Stella) | `stella_libretro.dll` | 6.6 | GPLv2 |
| Sony - PlayStation (SwanStation) | `swanstation_libretro.dll` | v0.1 | GPLv3 |
| Bandai - Tamagotchi P1 (TamaLIBretro) | `tamalibretro_libretro.dll` | 1.0 | GPL-2.0 |
| TIC-80 | `tic80_libretro.dll` | 0.80.0 | MIT |
| Uzebox (Uzem) | `uzem_libretro.dll` | — | MIT |
| GCE - Vectrex (vecx) | `vecx_libretro.dll` | SVN | GPLv3 |
| Commodore - C64 (VICE x64, fast) | `vice_x64_libretro.dll` | 3.9 | GPLv2 |
| Atari - Jaguar (Virtual Jaguar) | `virtualjaguar_libretro.dll` | v2.1.0 | GPLv3 |
| WASM-4 | `wasm4_libretro.dll` | 2.1.0 | ISC |
