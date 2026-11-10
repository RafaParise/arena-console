# ARENA 2026.11.09

O ARENA é um lançador de emuladores para a sala de aula: abre jogos de dezenas de consoles antigos numa tela só, com
recordes, conquistas e o **Jogar Junto** (partida em rede entre os computadores e celulares da sala). Roda de uma pasta
ou de um pen drive, **sem instalar nada e sem administrador**, e funciona sem internet. Feito em Python puro sobre o
RetroArch, com o código comentado em português para servir de material de aula.

## ⬇️ Qual arquivo baixar

Os arquivos estão em **Assets**, no fim desta página.

| Seu aparelho | Baixe este arquivo | Tamanho |
|---|---|---|
| 🖥️ **Computador com Windows 10 ou 11**, primeira vez | **`ARENA-2026.11.09-PC-windows-linux-chromebook.zip`** | 1068 MB |
| 🖥️ **Computador com Windows**, já usa o ARENA | **`ARENA-2026.11.09-PC-atualizacao.zip`** (só o programa) | 106 MB |
| 🐧 **Computador com Linux** (Ubuntu, Debian, Mint, Fedora; 64 bits) | o mesmo **`ARENA-2026.11.09-PC-windows-linux-chromebook.zip`** | 1068 MB |
| 📱 **Celular ou tablet Android** (Android 7 ou mais novo; quase todos) | **`ARENA-2026.11.09-android-celular-arm64.apk`** | 245 MB |
| 💻 **Chromebook da escola** (gerenciado) ou **sem instalar nada** | o mesmo **`ARENA-2026.11.09-PC-windows-linux-chromebook.zip`**, num pen drive | 1068 MB |
| 💻 **Chromebook pessoal com processador Intel ou AMD**, ou emulador de Android no computador | **`ARENA-2026.11.09-android-chromebook-intel-amd-x86_64.apk`** | 234 MB |
| 💻 Chromebook pessoal com processador ARM (MediaTek, Snapdragon) | o APK do celular, **`ARENA-2026.11.09-android-celular-arm64.apk`** | 245 MB |

**Não sabe qual é o seu celular?** Quase todo celular e tablet Android dos últimos 8 anos é `arm64`: baixe o do
celular. O `x86_64` é só para Chromebook com processador Intel ou AMD e para emulador de Android no computador.

**Nada de BIOS nem de jogo comercial vem junto**: só os jogos e as BIOS de licença livre (veja "O que não vem").

## Como instalar

### 🖥️ Windows (uns 10 minutos, mais o download)

1. Baixe o **`ARENA-2026.11.09-PC-windows-linux-chromebook.zip`** (1068 MB; descompactado, 2,6 GB).
2. **Antes de descompactar, desbloqueie o arquivo:** botão direito no `.zip` → **Propriedades** → embaixo, em
   *Segurança*, marque **Desbloquear** → **OK**. Não precisa de senha de administrador. Sem esse passo, o Windows
   pergunta, programa por programa, se pode abrir.
3. **Descompacte na raiz do disco:** em **Extrair tudo**, troque o destino por `C:\` (o `.zip` já traz a pasta
   `ARENA`, que fica em `C:\ARENA`) ou pela raiz de um pen drive formatado em **exFAT**. Em FAT32, jogos maiores que
   4 GB (PS2, Wii, PS3, Xbox 360) não cabem.
4. Dê dois cliques em **`ARENA.bat`**. Abre uma janela preta (não feche essa janela) e, em seguida, a tela do ARENA.
   Se aparecer *"O Windows protegeu o seu computador"*, clique em **Mais informações → Executar assim mesmo**.
5. Coloque os seus jogos em `jogos\pessoais\<console>` e clique em **Atualizar lista**. O botão **Como colocar
   jogos** mostra a pasta, os formatos e o que falta para cada console.

**Já usa o ARENA?** Não descompacte o pacote completo por cima: ele troca a configuração que você fez no RetroArch e
nos emuladores. Baixe o **`ARENA-2026.11.09-PC-atualizacao.zip`**, desbloqueie como no passo 2 e descompacte no mesmo
lugar onde está a pasta `ARENA`, escolhendo **Substituir os arquivos no destino**. Jogos, saves, BIOS, recordes e a
configuração dos emuladores ficam como estão.

### 🐧 Linux

O mesmo pacote do Windows. Descompacte e rode `sh ARENA.sh` (Ubuntu 18.04, Debian 10, Mint 19, Fedora 28 ou mais
novos, 64 bits). Usa o mesmo save do Windows: dá para levar a pasta no pen drive de um para o outro.

### 📱 Celular e tablet Android

1. Baixe o **`ARENA-2026.11.09-android-celular-arm64.apk`** no próprio celular.
2. Toque no arquivo e, quando o Android pedir, **permita instalar apps desta fonte**.
3. Abra o ARENA. Já vem com jogos livres para testar; os seus jogos vão na pasta `ARENA\jogos\pessoais` do celular
   ou do cartão SD (o ARENA mostra o caminho em **Como colocar jogos**).
4. **Já tem o ARENA no celular?** Instale por cima: jogos, saves e recordes ficam.

Sem controle, o jogo aparece com **botões de toque com a cara de cada console** (deitado ou em pé), com MENU,
SALVAR, CARREGAR e SAIR. Com um controle de verdade ligado, os botões somem; **dois toques rápidos** na tela os trazem
de volta.

### 💻 Chromebook

- **Da escola (gerenciado), sem instalar nada:** copie o `ARENA-2026.11.09-PC-windows-linux-chromebook.zip` descompactado para um pen drive e
  abra o **`ARENA-CHROMEBOOK.html`** no Chrome (35 consoles, sem jogo em rede).
- **Pessoal, com a Play Store:** o APK do processador dele. O ChromeOS só instala APK baixado com a **depuração ADB**
  ligada (Configurações → Desenvolvedores → Linux → Desenvolver apps Android; na primeira vez ele pede para
  restaurar o Chromebook). **Não testado num Chromebook de verdade.**

## O que há de novo desde a 2026.10.22

**Celular (Android)**
- **Botões de toque com a cara de cada console** (15 desenhos: o PlayStation com triângulo verde, xis azul, bola
  vermelha e quadrado rosa; os botões C amarelos do Nintendo 64...), deitado e em pé, com o editor **"Arrumar os
  botões da tela"**, e **SALVAR/CARREGAR** com a foto de onde parou. O celular vibra junto com o jogo.
- **Revisado console por console num Galaxy A12** (23 consoles, um jogo de cada, com os quadros por segundo medidos):
  - o **PlayStation** abre em 2,5 s, em vez de 32 s de tela preta;
  - o **Saturn** passou de 21 para 56 quadros por segundo (outro emulador, o YabaSanshiro);
  - o **PSP** voltou a abrir (ele fechava sozinho logo no começo);
  - o **Dreamcast** voltou a mostrar os botões de toque (sem eles, quem não tinha controle não jogava nem saía);
  - o **PS2** voltou a carregar o Mortal Kombat Deadly Alliance.
- **Voltar ao jogo:** quem sai do jogo pelo botão de início do celular volta para ele pelo ARENA (antes, o jogo ficava
  perdido atrás e travava a abertura de outro).
- **Painel "Este celular"** ao vivo (bateria em mA e W, temperatura, calor do aparelho, memória, Wi-Fi e controles),
  aviso de calor e nenhuma dica de teclado de computador no celular (no lugar de F2, F9 e Esc: MENU, SAIR e L3 + R3).
- **Pasta de jogos no cartão SD**, com o botão para levar os jogos da memória para lá.
- **Telinha do VMU do Dreamcast** por cima do jogo, no canto e no tamanho que a pessoa escolher.

**Jogar Junto**
- **Entre computador e celular**, nos dois sentidos, pelo Wi-Fi (entra em 5 a 17 s) ou pelo cabo USB (23 a 34 ms). O
  app segura o Wi-Fi em modo de baixa latência durante a partida, e há **"o próximo lugar livre"** para entrar sem
  escolher o número.
- Mega Drive e Sega CD pelo PicoDrive.

**Computador**
- **O celular como controle do jogo do computador:** até 8 jogadores, pelo Wi-Fi ou pelo **cabo USB** (4 a 6 ms), com
  zona morta, curva, canhoto, volante e 3 perfis.
- **Abertura 1,3 s mais rápida** com a rede da sala liberada.
- **Lossless Scaling** (para quem comprou): geração de quadros também no PS2, GameCube/Wii, PS3 e Xbox 360; um jogo
  que roda a 30 passa a 60 na tela.
- A placa de vídeo certa mesmo com a tela bloqueada ou sem monitor.
- **Corrigido:** o menu do jogo pelo controle abre com **L3 + R3** (os guias diziam Start + Select).
- **Corrigido:** o APK guardava, dentro da biblioteca do RetroArch, o caminho da pasta do computador onde foi montado
  (com o nome do usuário do Windows). Agora sai trocado por um nome fixo, e a montagem reprova o APK se ele sobrar.

## O que vem no pacote

- O ARENA (o servidor em Python e a tela) e o **Python 3.13** embutido; para o Linux, o Python portátil do Linux.
- O **RetroArch 1.22.2** com os núcleos que o ARENA usa e os emuladores **PCSX2** (PlayStation 2), **Dolphin**
  (GameCube e Wii), **RPCS3** (PlayStation 3) e **Xenia** (Xbox 360), configurados para rodar de dentro da pasta.
- O **Java** do Java ME e a versão do Chromebook (`ARENA-CHROMEBOOK.html`).
- As **BIOS livres**: o C-BIOS (MSX, licença BSD), o EmuTOS (Atari ST, GPL) e a OpenBIOS (PlayStation, MIT).
- Os guias (LEIA-ME e 1 a 6), o `VERIFICAR.bat`/`.sh`, o `PARTIDA.bat`/`.sh` e o `COLETAR.bat`.
- As licenças: `LICENSE` (a do ARENA) e `TERCEIROS.md` (a de cada programa incluído, com o link do código-fonte).

O app do Android traz o mesmo servidor e a mesma tela, 67 núcleos (66 no APK `x86_64`, que não tem o do PS2) e os jogos livres.

## O que não vem, e por quê

- **Jogos.** São de quem tem o jogo. Para começar sem nenhum, a **Biblioteca** (barra da esquerda) baixa jogos
  liberados pelos próprios autores, e os consoles de fantasia (TIC-80, WASM-4, LowRes NX, Uzebox, CHIP-8, MicroW8 e
  Vircon32) e o Arduboy têm muitos jogos livres.
- **BIOS e firmware das empresas** (PlayStation, PS2, Sega CD, Saturn, Neo Geo, PS3...). São programas da Sony, da
  Sega, da SNK e de outras empresas e precisam vir do seu próprio console. Coloque cada uma em `BIOS\<console>`: o
  ARENA reconhece, instala com o nome certo e mostra o que ainda falta (**Ajustes → Emuladores → BIOS dos consoles**).
  Sem elas, 57 dos 69 consoles já abrem; alguns têm um jeito livre (o Dreamcast e o PlayStation imitam a BIOS).

## Limites conhecidos

- **Celular:** PS3, Xbox 360 e Java ME são só do computador. Consoles pesados (Wii, GameCube, Dreamcast, fliperama de
  3D) ficam lentos num celular de entrada como o Galaxy A12. O Lossless Scaling no celular só vale em placa Adreno 7xx
  ou mais nova.
- **Saturn no Jogar Junto entre computador e celular:** o emulador do Saturn não aceita (entre dois computadores
  funciona).
- **Xbox 360:** o Xenia exige processador com AVX; não roda no Celeron N5100 de muitos notebooks da rede.
- **Chromebook:** sem jogo em rede no navegador; o APK `x86_64` não foi testado num Chromebook de verdade.
- **Ainda não testado:** controles de verdade no Saturn e no PlayStation do celular, o Linux num computador de verdade
  (só em contêiner) e o Jogar Junto em cinco notebooks da escola.

## Como esta versão foi conferida

- **1226 testes automáticos**, todos passando.
- **A rodada final completa** (120 testes, cerca de 3 horas e meia): 113 passaram de primeira; os 7 que falharam foram repetidos um de cada vez e passaram. As causas: a internet caiu no meio de um download; um tempo-limite curto demais (o teste do Chromebook leva 10 minutos); a abertura do servidor 0,05 s acima do teto no modo alvo; uma conexão cortada pelo Windows no meio da bateria principal (sozinha, ela passou 4 vezes); a imagem do PocketStation no modo modesto (passou na repetição); e os dois testes de celular rodaram com APKs antigos (repetidos com os desta versão, no emulador e no Galaxy A12).
- **No Galaxy A12:** a revisão console por console de 08/11 (23 consoles: abrir, mostrar a imagem, os botões de toque
  e sair pelo SAIR), refeita no Dreamcast com o conserto desta versão (Vulkan); o Voltar ao jogo do zero (jogo,
  botão de início, ARENA, Voltar ao jogo, SAIR, outro jogo); e, com o APK desta versão, o Jogar Junto com o computador
  nos dois sentidos (o computador entrou em 19 s; o celular, em 5 s).
- **No modo da máquina-alvo** (o notebook da escola, imitado aqui): a abertura do servidor mediu 1,07 s na última medição (o teto é 2,3 s), mas passou do teto em 3 de 5 medições desta noite (2,35 a 2,77 s), com um serviço do próprio Windows ocupando um núcleo inteiro do computador de teste; fica em observação.
- O pacote foi conferido antes da publicação: nenhuma BIOS das empresas, firmware, jogo, conta ou dado pessoal. O
  envio do código pelo `SINCRONIZAR.bat` passa por uma conferência que barra BIOS, jogos, saves, o banco de recordes,
  senhas, tokens e e-mails.

### SHA-256 (para conferir o download)

```
643f38dd6bfd2c3dfac5ed7fbd53ca2478d27a914d389c9722de0e218fefc684  ARENA-2026.11.09-PC-atualizacao.zip
c4b5a669b7edbefea6c8d5bfbc73bf8c3f255565eea82c1177b1356dec700618  ARENA-2026.11.09-PC-windows-linux-chromebook.zip
6adeb1af8f96f35fe2e9083192b1d8fd8001a75f6cab7e72bcdd1eb32d097699  ARENA-2026.11.09-android-celular-arm64.apk
7327b793cfff1301801c125db4361be73dce78607767521859fd1e6498e1f86c  ARENA-2026.11.09-android-chromebook-intel-amd-x86_64.apk
```
