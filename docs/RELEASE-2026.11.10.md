# ARENA 2026.11.10

O ARENA é um lançador de emuladores para a sala de aula: abre jogos de dezenas de consoles antigos numa tela só, com
recordes, conquistas e o **Jogar Junto** (partida em rede entre os computadores e celulares da sala). Roda de uma pasta
ou de um pen drive, **sem instalar nada e sem administrador**, e funciona sem internet. Feito em Python puro sobre o
RetroArch, com o código comentado em português para servir de material de aula.

> **RASCUNHO** (10/11/2026): tamanhos, SHA-256 e "Como esta versão foi conferida" entram na hora de publicar, depois da
> rodada final, do teste no emulador com Android 15 e do teste no Galaxy A12 com o APK desta versão.

## ⬇️ Qual arquivo baixar

Os arquivos estão em **Assets**, no fim desta página.

| Seu aparelho | Baixe este arquivo | Tamanho |
|---|---|---|
| 🖥️ **Computador com Windows 10 ou 11**, primeira vez | **`ARENA-2026.11.10-PC-windows-linux-chromebook.zip`** | (a medir) |
| 🖥️ **Computador com Windows**, já usa o ARENA | **`ARENA-2026.11.10-PC-atualizacao.zip`** (só o programa) | (a medir) |
| 🐧 **Computador com Linux** (Ubuntu, Debian, Mint, Fedora; 64 bits) | o mesmo **`ARENA-2026.11.10-PC-windows-linux-chromebook.zip`** | (a medir) |
| 📱 **Celular ou tablet Android** (Android 7 ou mais novo; quase todos) | **`ARENA-2026.11.10-android-celular-arm64.apk`** | (a medir) |
| 💻 **Chromebook da escola** (gerenciado) ou **sem instalar nada** | o mesmo **`ARENA-2026.11.10-PC-windows-linux-chromebook.zip`**, num pen drive | (a medir) |
| 💻 **Chromebook pessoal com processador Intel ou AMD**, ou emulador de Android no computador | **`ARENA-2026.11.10-android-chromebook-intel-amd-x86_64.apk`** | (a medir) |
| 💻 Chromebook pessoal com processador ARM (MediaTek, Snapdragon) | o APK do celular, **`ARENA-2026.11.10-android-celular-arm64.apk`** | (a medir) |

**Não sabe qual é o seu celular?** Quase todo celular e tablet Android dos últimos 8 anos é `arm64`: baixe o do
celular. O `x86_64` é só para Chromebook com processador Intel ou AMD e para emulador de Android no computador.

**Nada de BIOS nem de jogo comercial vem junto**: só os jogos e as BIOS de licença livre.

## 📱 O aviso "App de risco bloqueado" (Play Protect) acabou

Até a 2026.11.09, o Google Play Protect bloqueava a instalação em celulares novos ("esse app foi criado para uma versão
mais antiga do Android"). O motivo: o app declarava o Android 9 como versão-alvo, e o Play Protect avisa quando ela
está mais de duas versões abaixo da do celular. **Nesta versão, a versão-alvo é o Android 15.**

O que muda para quem instala:

- **Na primeira abertura, no Android 11 ou mais novo**, o ARENA abre a tela do sistema **"Acesso a todos os
  arquivos"**: ligue a chave do ARENA e volte. É o que deixa o ARENA achar a pasta dele e os jogos do celular e do
  cartão SD.
- **No Android 13 ou mais novo**, ele pergunta antes se pode **mostrar notificações**: é o aviso de que o ARENA está
  aberto, para o Android não fechá-lo no meio do jogo.
- **Não desligue o Play Protect** para instalar: ele é o antivírus do celular. Se você desligou para instalar uma
  versão antiga, ligue de novo (Play Store → foto do perfil → Play Protect → engrenagem → "Verificar apps com o Play
  Protect").

## O que há de novo desde a 2026.11.09

**Saves**
- **Continuar de onde parou:** ao fechar o jogo, o ARENA guarda o ponto onde você estava, e o jogo abre ali na
  próxima vez. Vem ligado no celular e desligado no computador da escola (dividido entre turmas); a chave fica em
  **Ajustes**. **Nunca passa por cima de um save:** se o save do jogo ou o cartão de memória foi gravado depois desse
  ponto, o jogo começa pelo save. Não vale no Jogar Junto.
- **Cartão do PS2 no celular: de volta ao de 8 MB**, o tamanho do cartão original e o que todos os jogos aceitam
  (alguns jogos não salvavam direito no de 64 MB). Quem já usava o de 64 MB continua com ele e com os saves; dá para
  trocar em Ajustes → Emuladores → Acessórios dos consoles → Cartões de memória do PS2.
- A memória de save do cartucho vai para o disco a cada 10 segundos, quando muda. Se o celular fechar o app sem
  aviso, o save feito no jogo não se perde.

**Capas**
- **A capa enche o molde:** o ARENA mede cada capa e dá ao cartucho ou à caixa o formato dela, sem cortar a imagem
  e sem sobra de fundo roxo. Cartuchos e caixas foram redesenhados. O CD agora é uma caixa de CD com a capa inteira à
  vista.

**Jogos e BIOS em qualquer pasta**
- **Procurar jogos baixados** agora olha também as pastas que você escolher (até 5, com três pastas abaixo de cada).
  No celular, há **Procurar no celular inteiro**.
- **As BIOS achadas** (pela marca do arquivo ou pelo nome, como o `neogeo.zip`) vão para a pasta `BIOS` com um toque e
  são instaladas no lugar do console delas na hora.
- Ao levar um jogo, o ARENA diz na hora se falta alguma BIOS para ele abrir, e onde pôr.

**Jogar entre casas diferentes**
- **O repasse da turma:** quem hospeda recebe um **código de sala** de 6 números, e o colega entra com ele, de outra
  casa, sem lista pública e sem mostrar o endereço de ninguém. O repasse roda no computador ou celular do professor
  (Amigos → **Partidas entre casas**).

**Consoles e acessórios**
- **DreamPotato** (o VMU do Dreamcast numa janela à parte) liga de verdade ao jogo: o VMU já entra encaixado.
- **PocketStation** conferido com minijogo de verdade.
- Mais de 4 controles do tipo Xbox no computador.
- No Jogar Junto de PS1, quem hospeda joga com o cartão de memória de sempre.

## Limites conhecidos

- **Celular:** PS3, Xbox 360 e Java ME são só do computador. Consoles pesados (Wii, GameCube, Dreamcast, fliperama de
  3D) ficam lentos num celular de entrada como o Galaxy A12.
- **Partida entre casas:** precisa de alguém com o repasse ligado e a porta liberada no roteador; na operadora com
  CGNAT (sem endereço público), ninguém de fora chega.
- **Xbox 360:** o Xenia exige processador com AVX; não roda no Celeron N5100 de muitos notebooks da rede.

## 🎓 Contribuição de aluno: HugoVHK

Esta versão existe em boa parte por causa do aluno da conta **[HugoVHK](https://github.com/HugoVHK)**, que testou o
ARENA em casa, no computador e no celular, e mandou ao professor tudo o que achou, com fotos:

- **o save do PS2 travando** no *Crash of the Titans* (o segundo save não gravava): virou a revisão dos saves e dos
  cartões de memória e o "Continuar de onde parou" que nunca passa por cima de um save;
- **o PS2 rodando liso** no computador dele (*God of War*, com a BIOS do console dele);
- **a foto do bloqueio do Play Protect**, a pergunta "desligar o Play Protect faz mal?" e o aviso para orientar a
  turma: viraram a troca da versão-alvo para o Android 15 e a orientação desta página;
- **o colega com um Xiaomi mais novo** que só conseguiu instalar pelo APKMirror Installer;
- **os prints do ARENA no celular dele** e os dados completos do aparelho (Poco X7, HyperOS 2, Android 15,
  Dimensity 7300-Ultra, 12 GB): o primeiro teste do app num celular de aluno com Android 15.

Obrigado, Hugo. Créditos completos em [CREDITOS.md](https://github.com/RafaParise/arena-console/blob/main/CREDITOS.md).
