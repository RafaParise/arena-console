# ARENA 2026.11.14

Esta versão faz o **SGSR** (o filtro de imagem feito para a placa do celular) e os outros filtros de escala
**funcionarem de verdade no celular**, e ajusta a cada computador mais três versões para PC: **Ship of Harkinian**
(Zelda: Ocarina of Time), **2 Ship 2 Harkinian** (Zelda: Majora's Mask) e **Starship** (Star Fox 64).

## ⬇️ Qual arquivo baixar

| Você vai usar em | Baixe | Tamanho |
|---|---|---|
| 📱 **Celular ou tablet Android** (a maioria dos aparelhos, incluindo Galaxy, Xiaomi, Motorola) | **`ARENA-2026.11.14-android-celular-arm64.apk`** | TAMANHO_APK_ARM |
| 📱 **Chromebook com Intel** ou **emulador de Android no PC** | **`ARENA-2026.11.14-android-chromebook-intel-amd-x86_64.apk`** | TAMANHO_APK_X86 |
| 🖥️ **Computador com Windows 10 ou 11**, primeira vez | **`ARENA-2026.11.14-PC-windows-linux-chromebook.zip`** | TAMANHO_ZIP |
| 🖥️ **Computador com Windows**, já usa o ARENA | **`ARENA-2026.11.14-PC-atualizacao.zip`** (só o programa) | TAMANHO_ATU |
| 🐧 **Computador com Linux** (Ubuntu, Debian, Mint, Fedora; 64 bits) | o mesmo **`ARENA-2026.11.14-PC-windows-linux-chromebook.zip`** | TAMANHO_ZIP |
| 💻 **Chromebook da escola** (gerenciado) ou **sem instalar nada** | o mesmo **`ARENA-2026.11.14-PC-windows-linux-chromebook.zip`**, num pen drive | TAMANHO_ZIP |

No celular, instale o APK por cima do anterior: os jogos, os saves e os recordes ficam. No computador, quem já tem o
ARENA descompacta o `PC-atualizacao.zip` por cima da pasta (só o programa muda: `dados\`, `jogos\`, `BIOS\` e
`retroarch\` não são tocados).

## O que há de novo desde a 2026.11.13.2

**Filtros de imagem no celular** (Ajustes → Escala da tela)
- No Android, os filtros do ARENA só funcionam com o motor de vídeo **Vulkan**, e o celular não mostra a aba onde se
  escolhe o motor. Por isso o SGSR escolhido no celular não mudava nada.
- Agora, quando você escolhe um filtro (**Pixel nítido, Nítido, Suave, Anime4K ou SGSR**), o ARENA abre os **jogos 2D**
  com o Vulkan, se o aparelho tiver. Os jogos 3D continuam como estavam, sem filtro. O **Automático** não mudou.
- Testado no Galaxy A12: o SGSR rodou no Super Nintendo, com o motor no automático.
- No **gráfico mínimo** ("bonecos de papelão") continua sem filtro, de propósito: é o mais leve.

**Versões para PC (recomps) ajustadas a cada computador: mais três**
- **Ship of Harkinian** (Zelda: Ocarina of Time), **2 Ship 2 Harkinian** (Zelda: Majora's Mask) e **Starship**
  (Star Fox 64). Na placa fraca, o jogo abre com metade da resolução, sem antisserrilhado e com os quadros do
  original; na média, com a resolução da tela e 60 quadros (o Starship já vem bom na média e não muda).
- Só entra o que falta: o que você escolher no menu do jogo continua valendo.
- As chaves de cada jogo foram conferidas no código de cada um (cada jogo usa nomes diferentes).

## Como esta versão foi conferida

- **Rodada final** (131 testes de uma vez, cerca de 3 h): **127 passaram**. As 4 falhas foram repetidas uma a uma:
  - o tempo de abertura do servidor (estourou com o PC ocupado) e a foto da janela do Commodore VIC-20 passaram
    sozinhos;
  - o teste da regra de ouro do multitap estava desatualizado (comparava com uma versão antiga, de antes da mudança
    de 16/10 no som); foi corrigido e passou;
  - o teste de **todos os jogos de PS2** segue em investigação: nesta noite o PCSX2 às vezes não começou em 60 s,
    um jogo e um nível diferentes a cada vez, e o mesmo jogo abriu em cerca de 21 s na repetição. Nada do PS2 mudou
    desde a 2026.11.13.2, e de tarde os 40 abriram.
- **Bateria do servidor:** 1513 testes, todos passando.
- **Celular:** o SGSR conferido no Galaxy A12 (Vulkan e o filtro compilado no registro do RetroArch); o APK de
  produção instalado e conferido no A12 (abertura a frio e `auditoria_celular`).

**Também nesta versão:** num pen drive usado num Mac, os arquivos ocultos que o macOS cria ao lado de cada jogo
(`._Mario.sfc`) apareciam como jogos repetidos que não abriam, e o que estava na lixeira também aparecia. Agora o
ARENA ignora os arquivos ocultos e as lixeiras do Mac, do Linux e do Windows.

## Limites conhecidos

- **Filtros no celular:** só nos jogos 2D. Os 3D (PSP, Nintendo 64, Dreamcast...) usam o OpenGL ES, onde os filtros
  do ARENA não compilam.
- **Recomps:** o dusklight (GameCube) ainda abre com o padrão dele (`docs\RECOMPS-DESEMPENHO.md`). Nenhum perfil foi
  medido no Celeron N5100 com o jogo de verdade.
- **Celular:** PS3, Xbox 360 e Java ME são só do computador. Consoles pesados (Wii, GameCube, Dreamcast) ficam lentos
  num celular de entrada como o Galaxy A12.
- **Xbox 360:** o Xenia exige processador com AVX; não roda no Celeron N5100 de muitos notebooks da rede.

## 🎓 Contribuições de alunos

O ARENA é um projeto da sala, e dois alunos mudaram o rumo das últimas versões:

- **[DOOK3DS](https://github.com/DOOK3DS)**, que levou o ARENA ao GitHub pela primeira vez (a v1.0, em 19/09/2026), trouxe
  o MFG Super Motion, a ideia de juntar o melhor do Lossless Scaling e do MFG e a de deixar o ARENA mais leve. Viraram
  o Mais quadros, os quadros de verdade do PS2, do GameCube e do Wii, a janela leve e o MFG baixado pelo Equipamentos.
  O **SGSR**, filtro desta versão, também saiu da lista de ideias dele.
- **[HugoVHK](https://github.com/HugoVHK)** testou o ARENA em casa, no computador e no celular (Poco X7, Android 15), e
  mandou tudo o que achou, com fotos: o save do PS2 que travava, o bloqueio do Play Protect, o colega com Xiaomi que só
  instalou pelo APKMirror Installer. Viraram a revisão dos saves, o "Continuar de onde parou" que nunca passa por cima
  de um save e a troca da versão-alvo para o Android 15.

Obrigado aos dois. Créditos completos em [CREDITOS.md](https://github.com/RafaParise/arena-console/blob/main/CREDITOS.md).
