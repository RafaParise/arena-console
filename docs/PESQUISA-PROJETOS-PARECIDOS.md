# Pesquisa: o que os melhores lançadores fazem, e o que o ARENA ainda não faz

Pedido do Rafael (10/11/2026): pesquisar os melhores projetos parecidos atrás de recursos e otimizações "para servir
todo celular". Meta realista combinada: Android 7 ou mais novo, 64 bits, aparelhos dos últimos 7 a 8 anos (o Galaxy A12
como piso). Pesquisa feita em 10/11/2026, de madrugada, com busca na web e leitura do código do RetroArch 1.22.2 que o
ARENA compila. Confiança marcada em cada item: **[Certo]** (li na fonte ou no código), **[Provável]** (fonte boa, não
medido aqui), **[Palpite]** (dedução minha).

## Resumo

Os projetos olhados (Lemuroid, ES-DE, Daijishō, Pegasus, Batocera, RetroBat e o próprio RetroArch) se dividem em dois
tipos: **emulador completo** (Lemuroid, RetroArch) e **só lançador** (ES-DE, Daijishō, Pegasus, que não trazem
emulador nenhum e mandam a pessoa instalar e configurar cada um). O ARENA é dos dois: traz o RetroArch e os núcleos
dentro do app, como o Lemuroid, e escolhe o ajuste pela máquina, como o Batocera. Quase tudo que esses projetos fazem
para celular fraco o ARENA **já faz**; sobram quatro ideias que valem a pena, e uma delas depende de uma decisão do
Rafael por causa da sala de aula.

## O que o ARENA já faz (conferido no código, 10/11)

| Ideia | Quem faz | No ARENA |
|---|---|---|
| Ajuste padrão por aparelho, com exceção por arquitetura | Batocera (`configgen-defaults-arch.yml`) [Certo] | `graficos.json` por nota da placa, `no_android`, modo modesto |
| Núcleo diferente por console e por jogo | Daijishō ("Player" por plataforma e por jogo) [Certo] | `consoles.json` (`core`, `core_sem_bios`, `core_netplay`), o jeito livre e o original |
| Pular quadros sozinho em aparelho fraco | Lemuroid (núcleos leves), RetroArch [Certo] | `frameskip` automático em 18 lugares do `graficos.json` |
| Vibrar ao tocar e vibração do jogo no próprio celular | Lemuroid (`hapticFeedbackMode`, `enableDeviceRumble`) [Certo] | `vibrate_on_keypress` e `enable_device_vibration` (`plataforma.py`) |
| Botões de toque somem com controle ligado | RetroArch [Certo] | `input_overlay_hide_when_gamepad_connected` |
| Latência de som menor só onde aguenta | blog do libretro: Vulkan aguenta 64 ou 32 ms [Certo] | `audio_latency` por motor e piso de 64 ms no Android |
| Vulkan quando o aparelho tem | blog do libretro (menos tempo por quadro que o OpenGL) [Certo] | motor conferido num processo à parte; o Dreamcast pede Vulkan |
| Pastas por console criadas na primeira vez | ES-DE (configurador, com `systeminfo.txt` por pasta) [Certo] | `jogos\pessoais\<console>` e a Biblioteca de jogos livres |
| Capas e informações do jogo | ES-DE (ScreenScraper, busca pelo hash do arquivo) [Certo] | capas pela internet; sem ela, o nome |
| Calor e bateria à vista | (nenhum dos lançadores mostra) | painel "Este celular", ao vivo |

## O que vale copiar, em ordem

### 1. "Continuar de onde parou" (do Lemuroid) — **decisão do Rafael**

O Lemuroid grava o estado do jogo sozinho ao sair e volta nele ao abrir de novo ("Automatically save and restore game
states", recurso número um da página dele) [Certo]. No RetroArch são duas chaves, `savestate_auto_save` e
`savestate_auto_load`, que o ARENA deixa desligadas desde a primeira versão [Certo].

- **A favor:** na aula o tempo acaba no meio da fase; o aluno volta no dia seguinte de onde parou, sem saber o que é
  save state. No celular do aluno (aparelho de uma pessoa só) faz todo sentido.
- **Contra, na sala:** num computador da escola dividido por turmas, o aluno da tarde abriria o jogo **no ponto do aluno
  da manhã** e poderia gravar por cima. E gravar o estado a cada saída escreve no pen drive (alguns MB por jogo de PS1).
- **Proposta [Palpite]:** ligado por padrão **só no Android** (aparelho pessoal) e desligado no computador, com a chave
  em Ajustes nos dois. O estado automático do RetroArch fica num espaço próprio (`.state.auto`), separado dos 10 espaços
  do F2, então não apaga nada do aluno [Certo: é assim no RetroArch].

### 2. Modo de desempenho contínuo do Android (do RetroArch e do PPSSPP)

Desde o Android 7 o app pode pedir ao sistema um ritmo **mais baixo e constante** em vez do máximo que esquenta e cai
depois de alguns minutos (`Window.setSustainedPerformanceMode`; exemplo do Google: 60 quadros que viram 30 depois de 30
minutos, contra 45 o tempo todo) [Certo]. O RetroArch tem a chave `sustained_performance_mode` (padrão desligado; o
ARENA deixa desligada) [Certo]. Só funciona onde o fabricante implementou; num Samsung com MediaTek, como o A12, pode
não mudar nada [Provável].

- **Conferido em 10/11/2026:** o A12 **não aceita** o modo (o RetroArch escreve no registro do Android
  `isSustainedPerformanceModeSupported? false`). Sem aparelho que aceite para medir, fica desligado.
- **Proposta original:** medir no A12 30 minutos de um jogo pesado (Saturn ou Dreamcast) com e sem a chave, pelo mostrador de
  velocidade do emulador (o fps do Android engana, lição de 25/10). Se ficar igual ou melhor, ligar no Android. Teste
  longo: fica para uma madrugada com o celular na tomada.

### 3. Exceções por família de placa de vídeo do celular (Adreno, Mali, PowerVR)

Os guias de aparelho Android separam o ajuste pela placa de vídeo: o NetherSX2 (PS2) tem uma versão para Adreno
potente e outra "Classic" para Mali e aparelhos fracos [Certo, guia da Retrolize de 07/2026]; o ARENA já registrou que
o Lossless Scaling no celular só vale em Adreno 7xx. Hoje o `graficos.json → no_android` vale para todo celular igual.

- **Proposta [Palpite]:** quando aparecer o primeiro defeito que só uma família tem, criar `no_android_mali` /
  `no_android_adreno` no `graficos.json`, com o mesmo formato do `no_android`. Não vale criar antes de ter um caso
  medido (o A12 é PowerVR GE8320, a única placa de celular que temos para testar).

### 4. Explicação dentro de cada pasta de jogos (do ES-DE)

O ES-DE escreve um `systeminfo.txt` em cada pasta de console, dizendo quais extensões o console aceita e qual emulador
usa [Certo]. É o que mais resolve o "pus o jogo e não apareceu".

- **Proposta [Palpite]:** um `LEIA.txt` curto em cada `jogos\pessoais\<console>` com as extensões aceitas
  (`consoles.json → extensoes`) e se precisa de BIOS. Barato e offline. Conferir antes se o indexador já ignora `.txt`.

## O que não vale copiar

- **Deixar a pessoa instalar e configurar cada emulador** (ES-DE, Daijishō, Pegasus): é o que mais trava quem começa
  ("o jogo pisca e volta para o lançador"; guia da Held Games) [Certo]. O ARENA trazer tudo pronto é a vantagem dele.
- **Raspador com conta** (ScreenScraper pede conta para ter limite maior) [Certo]: o ARENA não guarda conta nenhuma,
  de propósito (repositório público, alunos menores).
- **Substituir a tela inicial do Android** (Daijishō) [Certo]: no celular pessoal do aluno, trocar a tela inicial é
  invasivo.
- **Atraso de quadro automático alto** (dica de fórum: começar em 12) [Certo que a dica existe]: a documentação do
  libretro avisa que ele gasta folga e causa engasgo em aparelho fraco [Certo]. O ARENA já usa só onde a nota deixa.

## Revisão (o elo mais fraco)

- Nenhuma das quatro propostas foi medida ainda. A 2 depende de um teste longo no A12; a 1, de uma decisão do Rafael.
- Não li o código do RetroBat nem do Pegasus a fundo: o RetroBat é Windows (já coberto pelo ARENA no PC) e o Pegasus
  não traz emulador. O que mudaria a conclusão: um recurso de celular fraco que só eles tenham. Não achei nenhum.
- Confiança geral: 7 de 10 (fontes primárias para o "o que existe"; o "vale a pena para o ARENA" é julgamento meu).

## Fontes

- Lemuroid, página do projeto e `SettingsManager.kt` (autosave, vibração, áudio de baixa latência, modo HD):
  https://github.com/Swordfish90/Lemuroid e
  https://github.com/Swordfish90/Lemuroid/blob/47b5163e/lemuroid-app/src/main/java/com/swordfish/lemuroid/app/mobile/feature/settings/SettingsManager.kt
- Lemuroid, pedido de núcleos para aparelho fraco (issue 834, 03/11/2023): https://github.com/Swordfish90/Lemuroid/issues/834
- ES-DE no Android, configurador e `systeminfo.txt`: https://github.com/RetroDECK/ES-DE/blob/retrodeck-main/ANDROID.md
- ES-DE, guia do usuário (raspador e busca por hash): https://gitlab.com/es-de/emulationstation-de/-/raw/master/USERGUIDE.md
- Batocera, padrão por arquitetura (`configgen-defaults-arch.yml`): https://wiki.batocera.org/batocera_conf_syntax e
  https://wiki.batocera.org/notable_files
- Daijishō (Player e Platform): https://github.com/TapiocaFox/Daijishou/blob/main/README.md
- Guias de aparelho (Held Games, 18/07/2026; Retrolize, 11/07/2026):
  https://heldgames.com/guides/es-de-setup-guide , https://heldgames.com/guides/daijisho-setup-guide ,
  https://retrolize.co.uk/blogs/retro-blog/complete-retroid-pocket-setup-guide-emulators-bios-controls-performance
- Android, desempenho contínuo (AOSP): https://source.android.com/docs/core/power/performance
- RetroArch, chave `sustained_performance_mode` (retroarch.cfg de referência):
  https://raw.githubusercontent.com/libretro/RetroArch/master/retroarch.cfg ; código 1.22.2 (`config.def.h`, padrão
  desligado; `RetroActivityFuture.java`, chamada ao Android)
- libretro, latência e sincronia: https://docs.libretro.com/guides/latency/ e https://docs.libretro.com/guides/optimal-vsync/
- libretro, Vulkan no Android: https://www.libretro.com/index.php/tag/android/
