# ARENA 2026.11.14

Esta versão faz o **SGSR** (o filtro de imagem feito para a placa do celular) e os outros filtros de escala
**funcionarem de verdade no celular**, e ajusta a cada computador mais três versões para PC: **Ship of Harkinian**
(Zelda: Ocarina of Time), **2 Ship 2 Harkinian** (Zelda: Majora's Mask) e **Starship** (Star Fox 64).

## ⬇️ Qual arquivo baixar

| Você vai usar em | Baixe | Tamanho |
|---|---|---|
| 📱 **Celular ou tablet Android** (a maioria dos aparelhos, incluindo Galaxy, Xiaomi, Motorola) | **`ARENA-2026.11.14-android-celular-arm64.apk`** | 245 MB |
| 📱 **Chromebook com Intel** ou **emulador de Android no PC** | **`ARENA-2026.11.14-android-chromebook-intel-amd-x86_64.apk`** | 234 MB |
| 🖥️ **Computador com Windows 10 ou 11**, primeira vez | **`ARENA-2026.11.14-PC-windows-linux-chromebook.zip`** | 1,0 GB |
| 🖥️ **Computador com Windows**, já usa o ARENA | **`ARENA-2026.11.14-PC-atualizacao.zip`** (só o programa) | 106 MB |
| 🐧 **Computador com Linux** (Ubuntu, Debian, Mint, Fedora; 64 bits) | o mesmo **`ARENA-2026.11.14-PC-windows-linux-chromebook.zip`** | 1,0 GB |
| 💻 **Chromebook da escola** (gerenciado) ou **sem instalar nada** | o mesmo **`ARENA-2026.11.14-PC-windows-linux-chromebook.zip`**, num pen drive | 1,0 GB |

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

**Pen drive usado num Mac**
- O macOS cria, ao lado de cada arquivo, um irmão oculto de 4 KB (`._Mario.sfc`). Ele aparecia como um segundo jogo,
  que não abria, e o que estava na lixeira também aparecia.
- Agora o ARENA ignora os arquivos ocultos e as lixeiras do Mac, do Linux e do Windows (`$RECYCLE.BIN`). A lista de
  jogos se refaz sozinha na primeira abertura.

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
- **Celular:** o SGSR conferido no Galaxy A12 (Vulkan e o filtro compilado no registro do RetroArch). O APK de
  produção instalado no A12: abre a frio em cerca de 1 s, sem nenhuma falha no registro, passa por sair e voltar,
  girar a tela e pouca memória, e o servidor abre em primeiro plano com os 2699 jogos na tela.
- **O pacote do computador** foi montado do zero e aberto numa cópia: o servidor abriu, o RetroArch desenhou o jogo de
  prova (58 de 71 consoles prontos; os outros pedem BIOS ou programa de fora), e nenhum jogo, BIOS proprietária, save
  ou dado de quem montou ficou nele.

SHA-256 dos arquivos:

```
339a928c67a9296da607ea45a811861938a82d210225e63cf6bb665de9d9d735  ARENA-2026.11.14-PC-atualizacao.zip
c389cc177d4e7f85881052c6fc51ddf7d668083c90d013b17b96ad39457e2712  ARENA-2026.11.14-PC-windows-linux-chromebook.zip
9bf000b27aad666ca0034a26359bd41cfc61e8b217abef320894318956be4eca  ARENA-2026.11.14-android-celular-arm64.apk
b10f2395fc90dcce7440fa6a079e630a20a425f6e1f4a28732c25b49ea410f73  ARENA-2026.11.14-android-chromebook-intel-amd-x86_64.apk
```

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
