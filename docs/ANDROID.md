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
do ARENA na frente. Do RetroArch, muda uma peça só: a biblioteca dele
(`libretroarch-activity.so`), compilada do código oficial da mesma versão
com um remendo de 50 linhas (`android/retroarch/arena-args.patch`). O
RetroArch oficial do Android só aceita alguns pedidos de quem o abre (o
jogo, o núcleo, o arquivo de configuração) e não tem como pedir a partida em
rede; com o remendo, ele recebe a mesma linha de comando do Windows e do
Linux (`-L`, `--appendconfig`, `--host`, `--connect`...). Sem esse pedido,
funciona como o oficial.

A compilação (`ferramentas/compilar_retroarch_android.py`) usa o mesmo NDK
da biblioteca oficial (r22, 7026061), o mesmo `Android.mk` do RetroArch e a
mesma versão mínima do Android, e saiu igual à oficial: os mesmos 11.002
símbolos (11.075 no arm64) e as mesmas seções, com 192 bytes de código a
mais no x86_64 (o do remendo). A tela de Informações do RetroArch mostra a
versão `69a4f0e-arena`, a da etiqueta v1.22.2 com a marca do remendo (a
licença do RetroArch, a GPLv3, pede que a versão modificada diga que é
modificada).

O ARENA no Android é **o mesmo programa** do Windows e do Linux: o mesmo
servidor (`servidor/`), a mesma tela (`launcher/`), os mesmos jogos e saves.
O que muda é só quem abre o servidor e o RetroArch:

| O quê | Como |
|---|---|
| O servidor | O de sempre (`servidor/arena.py`), com o **Python 3.13.16 para Android** (a mesma versão do Linux), que o `ArenaServico.java` roda no aparelho e reabre se ele cair (até 3 vezes, como o `ARENA.bat`). A abertura é o `servidor/android_inicio.py` |
| O Python | O CPython 3.13.16 compilado para Android pelo [Chaquopy](https://chaquo.com) (licença MIT, os pacotes "target" do Maven Central), sem mudança no Python; o programa `python` é o lançador do ARENA (`android/python/lancador.c`, 20 linhas, compilado com o NDK): `ferramentas/python_android.py` |
| A tela | A de sempre (`launcher/`), num WebView, falando com o servidor em `http://127.0.0.1:8777`, como no computador |
| O RetroArch | O do APK (o oficial, com o remendo acima), aberto pelo app com a **mesma linha de comando do Windows**; o servidor espera o jogo fechar como espera o `retroarch.exe` (o processo do RetroArch termina ao sair do jogo) |
| A pasta do ARENA | No cartão SD, no pen drive ligado pelo cabo OTG ou na memória do aparelho. Na primeira abertura, o app pede a permissão de arquivos e, se achar uma pasta do ARENA só, já usa ela: **baixar e já usar**. Os jogos, as BIOS, os saves, os estados, as capas, as fotos, os cheats e os remapeamentos são **os mesmos do Windows** |
| Sem a pasta | Os 8 jogos livres dos testes (licença MIT, CC0 ou Unlicense, com a licença ao lado) vão para a pasta do app na primeira abertura |
| Os núcleos | 62 dos 63 do ARENA, na versão para Android, dentro do APK; cada um sai do APK na primeira vez que o console abre |
| Os consoles | Os do Windows, menos o Java ME (o núcleo precisa de Java, que o Android não tem) e os emuladores de fora (PS3 e Xbox 360 não têm versão para Android); o PS2, o GameCube e o Wii vão pelos núcleos |
| A reserva | Se o servidor não abrir no aparelho, a tela cai no "servidor dentro da página" do ARENA do Chromebook (`launcher/navegador`), com a ponte da `ArenaActivity.java` para abrir o jogo no RetroArch nativo |

### O que fica no aparelho, de propósito

No computador, tudo fica na pasta do ARENA. No Android, a pasta do ARENA no
cartão ou na memória é **compartilhada**: qualquer app com a permissão de
arquivos lê e grava nela. Por isso (revisão de segurança de 18/10/2026):

- **ficam só no app**: o que o servidor grava e o RetroArch lê (o arquivo da
  partida, a configuração, as listas com o caminho do núcleo, os ajustes do
  RetroArch), e os **recordes e o apelido** (dados de aluno). Entre
  aparelhos, os recordes vão pela sincronização em rede do ARENA, como entre
  dois computadores;
- **só a tela do ARENA fala com o servidor**: no Android, qualquer app do
  aparelho alcança o `127.0.0.1`. O app sorteia um segredo a cada abertura,
  passa ao servidor pelo ambiente (que outro app não lê) e à tela num cookie;
  sem ele, o servidor recusa todo pedido do próprio aparelho. E a tela só
  abre o servidor depois do aviso "pronto", que vem pelo fio privado do
  próprio Python: um app que tomasse a porta antes nunca recebe o segredo;
- nada do app vai para a cópia na nuvem do Android (`allowBackup` desligado).

Um APK por tipo de processador: **arm64-v8a** (quase todo celular e tablet
de hoje) e **x86_64** (Chromebook Intel e o emulador), uns 220 MB cada. O pacote é
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

- **O jogo em rede** (Amigos, Jogar Junto) é o do computador: o mesmo
  servidor, os mesmos avisos na rede (o app segura a trava do Wi-Fi para eles
  chegarem) e o RetroArch com `--host` e `--connect` (o remendo).
- **Os filtros de tela do ARENA** (os `.slangp`) só rodam no Vulkan: no
  OpenGL ES, o motor padrão do Android, ficam de fora. Em Ajustes → Avançado,
  o motor gráfico oferece o `gl` e o `vulkan`; o som e o tipo de controle
  saem da lista (o RetroArch do Android tem um de cada).
- **Toque na tela:** o RetroArch mostra o controle na tela quando não há
  controle ligado, e o esconde quando um controle é ligado; o som tem no
  mínimo 64 ms (o celular barato estala com menos).
- **Sair do jogo e o menu, sem teclado** (auditoria 4, 22/10/2026). Antes,
  só o F10 de um teclado fechava o jogo: no celular de toque, o aluno saía
  fechando o app. Agora o controle de toque do ARENA
  (`servidor/plataforma.py`, `controle_de_toque_do_arena`, a partir do
  `neo-retropad`) tem dois botões com nome, em todos os desenhos:
  - **SAIR**, tocado duas vezes (a primeira pede confirmação, como o F10),
    fecha o jogo e volta ao ARENA;
  - **MENU** abre o menu do jogo (salvar, carregar, reiniciar...). O
    controle continua na tela com o menu aberto: anda-se pelo direcional,
    **B (o de baixo) confirma e A volta**, como no controle de Xbox do
    ARENA. "Fechar" volta ao ARENA (`quit_on_close_content`).
  De pé, vale o desenho de pé (antes era o deitado esticado). No emulador,
  o toque direto no menu (o RGUI) errava a linha com o celular de pé: por
  isso o caminho é o controle de toque.
- **Antes das permissões** (auditoria 4): uma janela do ARENA diz para que
  servem os pedidos do Android (ver os arquivos e, do Android 13 em diante,
  as notificações). Negar não quebra nada: o ARENA abre com os jogos
  livres, e a permissão fica em Ajustes → Máquina.
- **A nota do aparelho** para pela velocidade medida de um núcleo: celular
  tem 8 núcleos e 8 GB, mas os núcleos são pequenos.

## Os testes

`testes/teste_android.py` liga o emulador sem janela, instala o APK de teste
(`montar_android.py --abi x86_64 --teste`), confere a tela, a pasta do ARENA
no aparelho e um jogo livre e um da pasta no RetroArch nativo (a foto que o
próprio RetroArch tira no F8, só com o quadro do jogo), com os tempos, em
`docs/android_bruto.json`. As teclas vão pelo teclado de PC do emulador,
seguradas como as de uma pessoa.

**A rodada de 21/10/2026** (Android 15 no emulador, 2 núcleos e 2 GB, o
vídeo desenhado pelo processador): **tudo certo**. O APK instala em 5,5 s; o
servidor e a tela abrem em 9 s, e a pasta do ARENA do aparelho é achada
sozinha, com os 2 jogos dela. O jogo de CHIP-8 abre no RetroArch nativo em
1,7 s, com imagem; o F10 duas vezes fecha o jogo e o servidor vê o fim. A
partida hospedada leva o `--host --port 55435` ao RetroArch (o remendo) e a
porta 55435 abre dentro do aparelho. O pedido de fora da tela do ARENA é
recusado (403). Na pasta do app, o servidor reabre em 6 s com os 8 jogos
livres do APK, e o de ZX81 abre, com imagem, e fecha pelo F10.

**O que o teste achou, já consertado:**

- Os jogos livres do APK iam para `jogos/<console>`, e a lista só procura
  nas origens (`jogos/livres`, `jogos/turma`, `jogos/pessoais`): a pasta do
  app abria vazia. Agora eles vão para `jogos/livres`.
- A troca da pasta do ARENA às vezes mostrava "Failed to fetch": o app
  fechava o servidor antes de a resposta chegar à tela. Agora o servidor
  responde e só depois pede a troca.
- O teclado que se diz teclado e mais alguma coisa (o do emulador se diz
  teclado e direcional) o RetroArch toma por um controle, e o F10, o Esc e
  o F2 param de funcionar. O ARENA agora diz ao RetroArch qual é o teclado
  (`input_android_physical_keyboard`). O teclado de PC comum, que se diz só
  teclado, já funcionava.
- O `config.ini` do C-BIOS do MSX tinha `\` no caminho das ROMs (achado no
  Linux, ver `docs/LINUX.md`). No Android deve ser igual, porque o caminho
  com `\` também não existe lá, mas isso não foi conferido no emulador (o
  teste abre o CHIP-8 e o ZX81). O conserto vale para os dois.

**O que é do Android, não do ARENA:** na primeira tela cheia de cada app, o
Android mostra o aviso "Tela cheia: para sair, deslize de cima para baixo"
e espera um toque em "Entendi"; até lá, o aviso fica na frente do jogo e
pega as teclas. O aluno toca uma vez e ele não volta.
