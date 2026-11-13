# Recomps: desempenho por máquina

Pesquisa de 13/11/2026. Fiz só leitura do código-fonte de cada repositório, sem chute. Cada fato está marcado como
**[Certo]** (visto no código) ou **[Provável]**. O que já está no ARENA fica em `servidor\recomps.py`, no
`ajuste_da_maquina`.

## Como o ARENA ajusta

- **Um perfil por motor**, não por jogo. A nota da placa vem do `nota_da_placa_de_fora`, de 1 a 5; na placa
  integrada ela para no 3. Os níveis:
  - **fraco**: nota 1 ou 2;
  - **médio**: nota 3;
  - **forte**: nota 4 ou 5. Aqui nada muda, porque o padrão do recomp já é o mais bonito.
- O ajuste entra pelo grupo `ensure` do escritor (`escrever_configuracao`). Só grava a chave que ainda não existe, então
  o que a pessoa escolhe dentro do jogo continua valendo.

## Motor RT64 (recomps de N64): feito

Arquivo `graphics.json`, em JSON plano.

| Sistema | Onde fica o arquivo |
|---|---|
| Windows | `%LOCALAPPDATA%\<programa>\graphics.json` |
| Linux | `~/.config/<programa>/graphics.json` (o recomp usa o `$HOME` direto e ignora o `XDG_CONFIG_HOME`) |

[Certo nos dois]

| id no catálogo | pasta do programa | `hpfb_option` | `ds_option` sem superamostragem |
|---|---|---|---|
| zelda64recomp | Zelda64Recompiled | sim | 1 |
| mariokart64recomp (e -2) | MarioKart64Recompiled | **não existe** | 1 |
| banjorecomp | BanjoRecompiled | sim | 0 (RecompFrontend) |

| nível | o que o ARENA grava |
|---|---|
| fraco | `res_option: "Original"`, `msaa_option: "None"`, `rr_option: "Original"`, `hpfb_option: "Off"` |
| médio | `res_option: "Original2x"`, `msaa_option: "None"`, `rr_option: "Manual"`, `rr_manual_value: 60`, `hpfb_option: "Off"` |

Fontes:
- [Zelda64Recomp config.cpp](https://github.com/Zelda64Recomp/Zelda64Recomp/blob/HEAD/src/game/config.cpp)
- [rt64_render_context.cpp](https://github.com/Zelda64Recomp/Zelda64Recomp/blob/HEAD/src/main/rt64_render_context.cpp)
- [N64ModernRuntime config.hpp](https://github.com/N64Recomp/N64ModernRuntime/blob/df7e820d8c55e4fcb4616c210cbb2c01b25cd48c/ultramodern/include/ultramodern/config.hpp)
- [MarioKart64Recomp config.cpp](https://github.com/sonicdcer/MarioKart64Recomp/blob/HEAD/src/game/config.cpp)
- [RecompFrontend](https://github.com/N64Recomp/RecompFrontend/blob/d0d90ba49f46f4896aaeda362056c21b1e342561/recompui/src/config/ui_config_tab_graphics.cpp)

Ainda **sem perfil**:
- **dino-recomp**: não confirmei o nome da pasta do programa.
- **Os outros recomps de N64** (Starfox, Goemon, DK64...): devem usar o mesmo `graphics.json`, mas as chaves mudam de
  um para outro. Cada um precisa ser conferido antes de entrar. [Provável]

## UnleashedRecomp (Sonic Unleashed, Xbox 360): feito

Arquivo `config.toml`, seção `[Video]`. O escritor passou a entender seção de TOML e INI: procura a chave dentro da
seção, acrescenta no fim dela e cria a seção quando falta.

| Sistema | Onde fica o arquivo |
|---|---|
| Windows | `%APPDATA%\UnleashedRecomp\config.toml` |
| Linux | `~/.config/UnleashedRecomp/config.toml` |

[Certo nos dois]

| nível | o que o ARENA grava |
|---|---|
| fraco | `ResolutionScale = 0.5`, `AntiAliasing = "None"`, `TransparencyAntiAliasing = false`, `ShadowResolution = "512"`, `GITextureFiltering = "Bilinear"`, `DepthOfFieldQuality = "Low"`, `MotionBlur = "Off"`, `FPS = 30` |
| médio | `ResolutionScale = 0.75`, `AntiAliasing = "2x MSAA"`, `ShadowResolution = "2048"`, `DepthOfFieldQuality = "Medium"` |

**Exige AVX** [Certo, [README](https://github.com/hedge-dev/UnleashedRecomp#minimum-system-requirements): "CPU with
support for the AVX instruction set"]. Sem AVX (o Celeron N5100), o ARENA não baixa nem abre e explica o motivo
(`recomps.falta_no_processador`). Ele também pede placa com Direct3D 12 ou Vulkan 1.2.

## Ship of Harkinian (Zelda: Ocarina of Time, motor libultraship): feito

Arquivo `shipofharkinian.json`, **aninhado**: a chave `gSettings.InternalResolution` fica em
`{"CVars": {"gSettings": {"InternalResolution": ...}}}` (o libultraship troca cada ponto por um nível,
`Config::FormatNestedKey` e `unflatten`). O escritor do ARENA agora mescla em profundidade: só entra o que falta,
e o que a pessoa escolheu no menu do jogo continua valendo. [Certo, conferido na versão 9.3.1 do catálogo]

- Nomes: `CMake/lus-cvars.cmake` e `CMake/soh-cvars.cmake` do Shipwright (`CVAR_PREFIX_SETTING = gSettings`).
- Limites e padrões: `soh/soh/SohGui/SohMenuSettings.cpp` (resolução de 0,5 a 2,0, padrão 1; MSAA de 1 a 8,
  padrão 1; quadros a partir de 20, o original).
- Lugar: no Windows, a pasta de onde o jogo abre (`Context::GetAppDirectoryPath` devolve "."; o ARENA abre o
  recomp na pasta do programa). No Linux (AppImage), `$XDG_DATA_HOME/soh` ou `~/.local/share/soh`, a não ser que
  a pasta de onde ele abre já tenha `shipofharkinian.json`, `oot.o2r` ou `oot-mq.o2r` (`SetAppImageHome` em
  `OTRGlobals.cpp`; o README diz o mesmo).

| nível | o que o ARENA grava (em `CVars.gSettings`) |
|---|---|
| fraco | `InternalResolution = 0.5`, `MSAAValue = 1`, `InterpolationFPS = 20` (o original) |
| médio | `InternalResolution = 1.0`, `MSAAValue = 1`, `InterpolationFPS = 60` |

Placa forte: nada muda. Não medido no Celeron N5100 (falta a cópia do jogo para medir).

## O que falta (precisa mudar o escritor primeiro)

| Motor | Arquivo | O que falta |
|---|---|---|
| libultraship (2 Ship 2 Harkinian, Starship) | o `.json` de cada um, como o do Ship of Harkinian | conferir os nomes das chaves de cada um (o prefixo pode mudar) |
| dusklight (GameCube) | `config.json` plano (o escritor já atende) | o caminho fora do modo portátil e o sentido de `game.internalResolutionScale` não foram confirmados |
| SuperTuxKart, OpenRA | XML e YAML | o escritor não lê esses formatos |

Chaves conferidas desses motores:

- **UnleashedRecomp** ([config_def.h](https://github.com/hedge-dev/UnleashedRecomp/blob/HEAD/UnleashedRecomp/user/config_def.h)):
  `ResolutionScale`, `AntiAliasing` (`"None"`, `"2x MSAA"`...), `ShadowResolution`, `MotionBlur`, `FPS`, `VSync`.
  Antes de oferecer este jogo no Celeron N5100, falta conferir se ele exige AVX.
- **Shipwright** ([SohMenuSettings.cpp](https://github.com/HarbourMasters/Shipwright/blob/HEAD/soh/soh/SohGui/SohMenuSettings.cpp)):
  - `gSettings.InternalResolution`: de 0.5 a 2.0;
  - `gSettings.MSAAValue`: de 1 a 8;
  - `gSettings.InterpolationFPS`: de 20 a 360.
- **dusklight** ([settings.cpp](https://github.com/TwilitRealm/dusklight/blob/HEAD/src/dusk/settings.cpp)):
  `game.bloomMode`, `game.depthOfFieldMode`, `game.enableFrameInterpolation`, `video.maxFrameRate`.

Nenhum perfil foi medido no notebook-alvo (Celeron N5100). Medir antes de dar o perfil por certo.
