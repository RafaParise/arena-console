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

## O que falta (precisa mudar o escritor primeiro)

| Motor | Arquivo | O que falta |
|---|---|---|
| UnleashedRecomp (Xbox 360) | `%APPDATA%\UnleashedRecomp\config.toml`, seção `[Video]` | o escritor precisa entender seção de TOML e INI (hoje a chave nova vai para o fim do arquivo, na última seção) |
| libultraship (Shipwright e parentes) | `shipofharkinian.json`, com as chaves dentro de `"CVars"` | mescla em profundidade no JSON |
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
