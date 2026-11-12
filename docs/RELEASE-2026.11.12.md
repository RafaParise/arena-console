# ARENA 2026.11.12

O ARENA passou a abrir mais do que consoles: os **jogos de computador** (os da pasta e os já instalados pela Steam,
GOG, Epic e Heroic, inclusive jogo do Windows no Linux e do Linux no Windows), a **versão para PC dos jogos de
console** (os recomps: baixar e jogar, sem emulador) e, no celular, os **jogos de Android instalados**. E ganhou o
filtro **SGSR** e a **nitidez ajustável** na escala da tela.

## ⬇️ Qual arquivo baixar

| Você vai usar em | Baixe | Tamanho |
|---|---|---|
| 📱 **Celular ou tablet Android** (a maioria dos aparelhos, incluindo Galaxy, Xiaomi, Motorola) | **`ARENA-2026.11.12-android-celular-arm64.apk`** | 257 MB |
| 📱 **Chromebook com Intel** ou **emulador de Android no PC** | **`ARENA-2026.11.12-android-chromebook-intel-amd-x86_64.apk`** | 246 MB |
| 🖥️ **Computador com Windows 10 ou 11**, primeira vez | **`ARENA-2026.11.12-PC-windows-linux-chromebook.zip`** | 1,1 GB |
| 🖥️ **Computador com Windows**, já usa o ARENA | **`ARENA-2026.11.12-PC-atualizacao.zip`** (só o programa) | 111 MB |
| 🐧 **Computador com Linux** (Ubuntu, Debian, Mint, Fedora; 64 bits) | o mesmo **`ARENA-2026.11.12-PC-windows-linux-chromebook.zip`** | 1,1 GB |
| 💻 **Chromebook da escola** (gerenciado) ou **sem instalar nada** | o mesmo **`ARENA-2026.11.12-PC-windows-linux-chromebook.zip`**, num pen drive | 1,1 GB |

No celular, instale o APK por cima do anterior: os jogos, os saves e os recordes ficam. No computador, quem já tem o
ARENA descompacta o `PC-atualizacao.zip` por cima da pasta (só o programa muda: `dados\`, `jogos\`, `BIOS\` e
`retroarch\` não são tocados).

## O que há de novo desde a 2026.11.11

**Jogos de computador (o console PC)**
- **A pasta do jogo inteira** em `jogos › pessoais › PC`: o ARENA acha o programa principal sozinho (o `.exe` do
  Windows, o AppImage ou o programa do Linux) e deixa de fora o desinstalador, o `UnityCrashHandler`, o `vcredist` e o
  instalador. O `.exe` do MS-DOS continua indo para o MS-DOS (o ARENA olha o começo do arquivo).
- **Os jogos já instalados no computador** pela Steam, pela GOG, pela Epic e pelo Heroic entram sozinhos na lista,
  com a origem "Instalado pela Steam" (ou pela loja de cada um), e abrem pelo atalho da loja. O ARENA só lê os arquivos
  que as lojas gravam: não entra em conta nenhuma. Programas vendidos na loja que não são jogos (o Lossless Scaling, o
  Wallpaper Engine) ficam de fora.
- **Jogo de um sistema no outro:** jogo do Windows no Linux abre pelo **Wine** ou pelo **Proton** da Steam; jogo do
  Linux no Windows, pelo **WSL**. Só quando já estão instalados: o ARENA não instala nada e, sem eles, diz o que falta.

**A versão para PC dos jogos de console (recomps)**
- Um **recomp** é o jogo de console traduzido para programa de computador: roda **sem emulador**, com a resolução da
  tela, 60 quadros ou mais, tela larga e controle moderno (o Zelda 64: Recompiled, o Mario Kart 64: Recompiled, o
  Sonic Unleashed Recompiled...). Os dados do jogo continuam vindo **da sua cópia**, a que já está no ARENA.
- O ARENA confere cada jogo da biblioteca num catálogo de **1.219 recomps de 22 consoles**. O painel do jogo avisa
  "Versão para PC", e o **Jogar agora** oferece esse jeito ao lado do emulador.
- **Baixar e jogar:** na primeira vez, o ARENA pergunta (mostrando o tamanho, o autor e a licença), baixa **da release
  oficial no GitHub de quem fez**, confere a marca SHA-256 e descompacta em `emuladores\Recomps`. Nada é instalado no
  sistema. Quando o recomp traz o arquivo `recomplauncher.json`, o ARENA confere se o disco é o certo (lê o disco por
  dentro), escreve os ajustes que ele pede, roda o preparo mostrando o andamento e passa a cópia do jogo.
- A técnica foi estudada no RecompLauncher (de código fechado): **nada dele vem junto**; o ARENA guarda só os fatos do
  catálogo público e faz o resto com código próprio.

**Jogos de Android no celular**
- No ARENA do celular há o console **Jogos de Android**: o ARENA pergunta ao Android quais apps instalados são jogos e
  mostra todos na lista. **Jogar agora** abre o jogo direto. O ARENA só lê a lista e abre o app.

**Imagem**
- **SGSR** (Snapdragon Game Super Resolution, da Qualcomm, código aberto) em Ajustes → **Escala da tela**: feito para a
  placa de vídeo do celular, estica num passo só e refaz só as bordas. O Automático continua o mesmo.
- **Nitidez** de 0 a 100, logo abaixo da escala: quanto o FSR, o SGSR e a nitidez das placas fracas firmam as bordas.
  O 50 é o de sempre.

**Mais rápido e mais seguro**
- A abertura do servidor no modo da máquina-alvo caiu de 2,56 s para **1,91 s** (o que a primeira tela não usa só é
  carregado quando é preciso).
- Revisão de segurança do código novo: o atalho dos jogos da Epic não passa mais pelo `cmd` (o `&` do endereço viraria
  outro comando); o download do recomp é conferido também pela marca guardada no catálogo, não só pela do GitHub, e uma
  versão que nenhuma das duas marcas confere não é instalada.

## Como esta versão foi conferida

- **1.414 testes automáticos** do servidor passaram (eram 1.356 na 2026.11.11; os novos são do console PC, dos
  recomps, dos jogos de Android e do SGSR).
- **Rodada final** (os testes de ponta a ponta, que abrem os emuladores de verdade): **121 de 130** passaram de
  primeira. Oito das nove falhas eram testes que ainda não conheciam o que entrou nesta versão (o jogo que tem versão
  para PC passou a perguntar o jeito de abrir; a cópia de teste via os jogos da Steam do computador; a escala ganhou o
  SGSR; frases sem acento no catálogo). Foram consertados e repetidos: todos passaram. O nono é a foto da telinha do
  PocketStation, que às vezes sai quase vazia (passou em 3 de 6 tentativas; nada do PocketStation mudou nesta versão).
- **Abertura do servidor no modo da máquina-alvo:** 2,08 s (meta 2,3 s). O código novo pesa cerca de 12 ms nela.
- **Linux** (Ubuntu no WSL): passou (682 s). **Chromebook** (a versão do navegador): 32 de 32. **Navegadores**
  (Edge, Chrome e Firefox): 30 de 30. **Android 15** no emulador e o teste de estresse: passaram. **Partida entre
  computador e celular:** passou.
- **Galaxy A12** (Android 12, 4 GB), com o APK de produção (`ferramentas\auditoria_celular.py`): pacote 2026.11.12
  com versão-alvo 35, sem depuração e sem cópia na nuvem, nenhuma porta aberta pelo app, abertura a frio em 700 ms
  (mediana; eram 868 ms), nenhuma falha no registro, e o ciclo de vida (sair e voltar, girar a tela, pouca memória)
  passou. O console **Jogos de Android** achou os apps de jogo do aparelho e abriu o escolhido (conferido com o
  APK de teste, que tem o mesmo código).
- **No computador, de verdade:** o console PC listou os jogos instalados pela Steam (e deixou o Lossless Scaling de
  fora); o recomp do Bomberman 64 foi baixado da release oficial e a marca SHA-256 conferiu; o SGSR compilou no
  RetroArch de verdade e a foto do quadro saiu certa.
- **Três revisões de segurança** do código novo, com os achados corrigidos (o atalho da Epic sem o `cmd`, a marca do
  catálogo além da do GitHub, a versão sem marca conferida que não instala).

SHA-256 dos arquivos:

```
2351e5b89089fa325eb00099cf147e483cacb8393ae90af0f2f72c306207cc02  ARENA-2026.11.12-PC-atualizacao.zip
378f55234bcb2ef4196c25042cedb5d705431262fcba4845e088f160e0080bde  ARENA-2026.11.12-PC-windows-linux-chromebook.zip
fdcb41273c9495011c4361aeac467848b14bb89650518669dd8143a9d6cb73aa  ARENA-2026.11.12-android-celular-arm64.apk
14a5c13156e52544eebf444cf6dc7e33c1734cc844e574fdb81f5668ed3d369d  ARENA-2026.11.12-android-chromebook-intel-amd-x86_64.apk
```

## Limites conhecidos

- **Jogo de Android no computador:** não. Seria preciso um Android instalado no PC (o subsistema de Android do Windows
  acabou; o Waydroid do Linux pede administrador).
- **Jogo de PC no celular:** não. O processador e o sistema são outros; lá o console PC aparece cinza, com o motivo.
- **Recomps** desenham pela placa de vídeo (Direct3D 12 ou Vulkan) e são feitos por terceiros: num computador fraco,
  ou com driver antigo, um recomp pode travar. Se travar, use o jeito de sempre (o emulador). O GitHub limita as
  consultas (60 por hora por computador) e, sem internet, o recomp que ainda não foi baixado não abre.
- **Celular:** PS3, Xbox 360 e Java ME são só do computador. Consoles pesados (Wii, GameCube, Dreamcast) ficam lentos
  num celular de entrada como o Galaxy A12.
- **Xbox 360:** o Xenia exige processador com AVX; não roda no Celeron N5100 de muitos notebooks da rede.

## 🎓 Contribuições de alunos

O ARENA é um projeto da sala, e dois alunos mudaram o rumo das últimas versões:

- **[DOOK3DS](https://github.com/DOOK3DS)**, que levou o ARENA ao GitHub pela primeira vez (a v1.0, em 19/09/2026), trouxe
  o MFG Super Motion, a ideia de juntar o melhor do Lossless Scaling e do MFG e a de deixar o ARENA mais leve: viraram
  o Mais quadros, os quadros de verdade do PS2, do GameCube e do Wii e a janela leve.
- **[HugoVHK](https://github.com/HugoVHK)** testou o ARENA em casa, no computador e no celular (Poco X7, Android 15), e
  mandou tudo o que achou, com fotos: o save do PS2 que travava, o bloqueio do Play Protect, o colega com Xiaomi que só
  instalou pelo APKMirror Installer. Viraram a revisão dos saves, o "Continuar de onde parou" que nunca passa por cima
  de um save e a troca da versão-alvo para o Android 15.

Obrigado aos dois. Créditos completos em [CREDITOS.md](https://github.com/RafaParise/arena-console/blob/main/CREDITOS.md).
