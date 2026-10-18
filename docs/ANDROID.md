# O ARENA no Android — item 14 (18/10/2026)

Pedido do Rafael: "o ARENA se tornar um aplicativo de Android também com um
apk no github para download ... sempre a ideia é baixar e já usar, simples e
rápido. Mas antes de implementar o android baixe o melhor emulador de android
de código aberto para testes locais na máquina".

## O emulador dos testes

O escolhido é o **emulador do próprio Android** (o do AOSP, o Android Open
Source Project: código aberto, o mesmo que o Android Studio usa), com uma
imagem **AOSP do Android 15** (a "default", sem os serviços do Google, toda
de código aberto). Ele roda o aparelho de verdade, com o processador do
computador, e o teste fala com ele pelo `adb`.

- `ferramentas/preparar_android.py` monta tudo fora do ARENA, em
  `%LOCALAPPDATA%\ARENA-android` (uns 3 GB): o Java das ferramentas, o SDK do
  Android, o emulador, a imagem e o aparelho virtual "ARENA" (2 GB de
  memória, 2 núcleos, como um tablet de escola). As ferramentas vêm com a
  marca da lista oficial do Google; instalar pelo `sdkmanager` pede aceitar
  as licenças do SDK do Android.
- O emulador roda ao lado do WSL pela **Plataforma de Hipervisor do
  Windows**, que foi ligada nesta máquina em 18/10 (`dism /Online
  /Enable-Feature /FeatureName:HypervisorPlatform`, administrador). O
  Android 15 ligou em 99 segundos.

## O APK do ARENA

O APK é o **RetroArch 1.22.2 oficial para Android** (o `RetroArch.apk` do
libretro, o mesmo RetroArch do Windows, do Linux e do Chromebook) com a tela
do ARENA na frente. Nada do código do RetroArch muda:

| O quê | Como |
|---|---|
| A tela | A de sempre (`launcher/`), num WebView, com o servidor dentro da página do ARENA do Chromebook (`launcher/navegador`), servida de dentro do APK |
| A ponte | `android/src/.../ArenaActivity.java`: acha a pasta do ARENA no aparelho, lista e grava arquivos dela, e abre o jogo no RetroArch **nativo** |
| A pasta do ARENA | No cartão SD, no pen drive ligado pelo cabo OTG ou na memória do aparelho; os saves e os estados vão para `retroarch/saves` e `retroarch/states` dela: **os mesmos do Windows** |
| Os núcleos | 62 dos 63 do ARENA, na versão para Android, dentro do APK; cada um sai do APK na primeira vez que o console abre |
| Sem a pasta | Os jogos livres que vêm no APK (os mesmos do Chromebook) abrem direto; o aparelho também guarda jogos pequenos (Ajustes → Máquina) |
| Os consoles | Os do Windows, menos o Java ME (o núcleo precisa de Java, que o Android não tem) e os emuladores de fora (PS3 e Xbox 360 não têm versão para Android); o PS2, o GameCube e o Wii vão pelos núcleos |

Um APK por tipo de processador: **arm64-v8a** (quase todo celular e tablet
de hoje, 207 MB) e **x86_64** (Chromebook Intel e o emulador). O pacote é
`io.github.rafaparise.arena`, para conviver com um RetroArch já instalado. O
APK pede o Android 7 ou mais novo e a permissão de arquivos (para ler a
pasta do ARENA), como o RetroArch.

Uma diferença de propósito para o RetroArch oficial: lá, as telas do
RetroArch (a do jogo, a do menu e a de instalar núcleo) ficam abertas a
qualquer app do aparelho, e a do jogo aceita o caminho de um núcleo. No APK
do ARENA elas só abrem por dentro do ARENA; senão, outro app poderia fazer o
RetroArch do ARENA carregar um programa dele, com a permissão de arquivos do
ARENA.

Montar: `ferramentas/montar_android.py` (detalhes no topo dele). A chave que
assina o APK fica fora do git, em `%LOCALAPPDATA%\ARENA-android\assinatura`:
**guarde uma cópia**; sem ela, o APK seguinte não instala por cima do
anterior.

## O que muda no Android

- **Sem jogo em rede** por enquanto (como no Chromebook): os jogadores jogam
  no mesmo aparelho.
- **Sem os filtros de tela do ARENA**: eles são do Vulkan; no Android vale a
  escala do próprio RetroArch.
- **Os saves e os estados** o RetroArch grava direto na pasta do ARENA; o
  painel "Saves e cheats" da tela ainda não os lista no Android.
- **Toque na tela:** o RetroArch mostra o controle na tela quando não há
  controle ligado, e o esconde quando um controle é ligado.

## Os testes

`testes/teste_android.py` liga o emulador sem janela, instala o APK de teste
(`montar_android.py --abi x86_64 --teste`), confere a tela, a pasta do ARENA
no aparelho e um jogo livre e um da pasta no RetroArch nativo (a foto da
tela de cada um), com os tempos, em `docs/android_bruto.json`.

**A conferir:** o teste ainda não rodou inteiro. O emulador ligou, o
RetroArch oficial instalou nele (2 s) e abriu; na madrugada de 18/10 o
Claude Code encerrou o emulador porque o computador ficou com pouca memória
(a sessão estava parada), e ele só volta a ser ligado com a autorização do
Rafael.
