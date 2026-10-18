# O ARENA no Linux — item 13 (17 e 18/10/2026)

Pedido do Rafael: "uma versão do ARENA para linux perfeitamente idêntico sem
alterar nada; se tiver alguma função ou recurso impossível de rodar no linux,
use estratégias, implementações e técnicas para contornar e criar semelhantes
ou idênticas, e prioridade sempre ser o mais idêntico".

O resultado é o **mesmo ARENA, no mesmo pen drive**: o mesmo servidor, a mesma
tela, os mesmos jogos, os mesmos saves e a mesma configuração. O pen drive
pode ir do Windows para o Linux e voltar: o jogo salvo num continua salvo no
outro. O que muda de um sistema para o outro mora num lugar só,
`servidor/plataforma.py`, e o resto do ARENA nem fica sabendo.

## Como abrir

No Linux, de dentro da pasta do ARENA (no gerenciador de arquivos: botão
direito na pasta → **Abrir no terminal**):

    sh ARENA.sh

É o mesmo que o `ARENA.bat` faz no Windows: acha o Python, confere o
RetroArch, abre o servidor (que abre a tela no navegador) e reabre o
servidor sozinho se ele cair (até 3 vezes). A janela do terminal é a "janela
preta" do Linux: fechar a janela fecha o ARENA; **Ctrl+C** também.

- **Dois cliques:** o `ARENA.desktop` abre o ARENA nos gerenciadores de
  arquivos que deixam (Dolphin do KDE, Nemo do Mint, Thunar, Caja). No
  Arquivos do GNOME (Ubuntu), use o terminal na primeira vez.
- **No menu de aplicativos:** `sh ARENA.sh --atalho` põe o ARENA no menu
  deste computador (abre o ARENA desta pasta).
- **Verificar e diagnosticar:** `sh VERIFICAR.sh` (o `VERIFICAR.bat`) e
  `sh PARTIDA.sh` (o `PARTIDA.bat`).

Nada pede senha de administrador, nada é instalado no Linux. O que o ARENA
grava fora da pasta dele é só a **pasta de cache da conta**
(`~/.cache/arena`), que se refaz sozinha (ver abaixo).

## O que vem no pacote para o Linux

| O quê | Onde | De onde |
|---|---|---|
| Python 3.13 portátil (79 MB) | `servidor/python-linux` | python-build-standalone (o do `uv`) |
| RetroArch 1.22.2 (o mesmo do Windows) | `retroarch/RetroArch-Linux-x86_64.AppImage` | AppImage oficial do libretro |
| Os 63 núcleos (os mesmos consoles) | `retroarch/cores/*.so`, ao lado dos `.dll` | `RetroArch_cores.7z` do 1.22.2; o do Java ME, do FreeJ2ME-Plus 1.52 (o mesmo do `.dll`); o do Apple II, do *nightly* do libretro |
| Perfis de controle do Linux | `retroarch/autoconfig/udev` e `linuxraw` | o mesmo 7z do RetroArch |
| Bibliotecas de reserva | `retroarch/bibliotecas-linux` | a `libjack.so.0` vazia (escrita pelo ARENA) e a `libgomp.so.1` do Debian 10 |
| Java do Java ME (58 MB) | `emuladores/Java/linux` | o mesmo Temurin 21.0.12.1, reduzido com o `jlink` |
| PCSX2 2.8.2, RPCS3 0.0.42, Xenia Canary | ao lado dos do Windows, em `emuladores/*/*` | os AppImage oficiais, nas mesmas versões do Windows |

Tudo é posto no lugar por `ferramentas/preparar_linux.py`, que confere a
marca SHA-256 de cada arquivo (a publicada pelo projeto, ou a conferida aqui
quando o projeto não publica) e vai junto no pacote pelo
`ferramentas/montar_versao_alunos.py` (também no `--atualizar`). O
`TERCEIROS.md` lista cada um com a licença e o código-fonte.

**Requisito:** Linux de 64 bits para processador Intel ou AMD (x86-64) com a
glibc 2.27 ou mais nova, a de 2018 para cá: Ubuntu 18.04, Debian 10, Linux
Mint 19, Fedora 28 e os mais novos. (No Chromebook de processador ARM e no
Raspberry Pi, o ARENA que roda é o do navegador: `ARENA-CHROMEBOOK.html`.)

## O que fica igual e o que muda

| Função | No Linux |
|---|---|
| Tela, jogos, saves, estados (F2/F4), recordes, amigos, Jogar Junto | **Iguais** (os mesmos arquivos; a partida a dois entre Windows e Linux usa o mesmo RetroArch 1.22.2) |
| Configuração do RetroArch | O **mesmo** `retroarch.cfg`. Os caminhos do Windows (`E:\ARENA\...`) e do Linux (`/media/.../ARENA/...`) viram os do sistema da vez, a cada abertura |
| Som | O que o Linux usa: **PulseAudio** (ou o PipeWire, que fala como ele); sem servidor de som, **ALSA**. No Windows, WASAPI. A escolha é automática |
| Controle | **udev**, o jeito do Linux ler todos os controles. Os perfis prontos são os do RetroArch para Linux; ao definir um botão do controle Xbox na tela, o ARENA usa a numeração do Linux |
| Vídeo | **Vulkan**, ou **glcore** (OpenGL) quando o Vulkan não serve. O d3d11 é só do Windows |
| Navegador | O padrão do computador (o `xdg-settings`), inclusive os do Snap e do Flatpak: Chrome, Chromium, Edge, Brave, Vivaldi, Opera, Firefox |
| Abrir a pasta, "Mostrar na pasta" | O gerenciador de arquivos do computador; o pacote aparece **marcado** (o pedido `FileManager1` do freedesktop, como o `explorer /select`) |
| PS2, PS3, Xbox 360 (emuladores de fora) | Os do Linux, nas mesmas versões, lendo e gravando a **mesma pasta** dos do Windows (a mesma BIOS, os mesmos memory cards, a configuração que o ARENA completa) |
| GameCube e Wii | Pelo núcleo do Dolphin (o Dolphin não publica versão portátil para Linux). Um Dolphin do Linux posto em `emuladores/Dolphin` também vale |
| Java ME | O núcleo `.so` do mesmo FreeJ2ME-Plus, com o Java do ARENA para Linux |
| "O que deixa este computador lento" | O mesmo painel, lido do Linux: memória, bateria, economia de energia, programas pesados, atualização rodando, disco, memória virtual (swap) e driver de vídeo |
| Ponte sem acento | **Não precisa**: no Linux todo núcleo abre caminho com acento |
| Prioridade do jogo e economia de energia | O Linux não deixa um programa sem administrador subir a prioridade: o emulador abre numa sessão própria (o Linux divide o processador por sessão), e o servidor parado fica perto de 0% |
| Lossless Scaling | É um programa do Windows: no Linux não aparece, e o jogo fica com a escala do próprio ARENA |
| Gravação e transmissão | Desligadas, como no Windows (os dados dos alunos) |

## As técnicas

**O RetroArch e os emuladores em AppImage, sem FUSE.** O AppImage é um
programa num arquivo só, que só se abre sozinho com o FUSE 2 — e o Ubuntu
deixou de trazer o FUSE 2 no 22.04 (o 24.04 também não tem; conferido na
lista oficial de pacotes dele). Além disso, pen drive FAT32 não deixa
executar programa nenhum. Então, na primeira vez, o ARENA tira o programa de
dentro do AppImage (`--appimage-extract`, o próprio AppImage faz, sem FUSE e
sem administrador) para `~/.cache/arena/<programa>-<tamanho>`, e dali em
diante abre direto de lá. Os jogos, os saves e a configuração continuam no
pen drive (o RetroArch recebe o `--config` do ARENA).

**A `libjack.so.0` vazia.** O RetroArch do AppImage foi montado ligado à
biblioteca do JACK (um servidor de som de estúdio), e o Linux só o abre se a
achar — o Ubuntu 24.04 não traz. O ARENA nunca usa o JACK, então basta uma
biblioteca com o mesmo nome e as mesmas funções, cada uma devolvendo "não
deu". O `ferramentas/jack_vazio.py` escreve o arquivo byte a byte, no
formato dos programas do Linux (ELF), sem compilador. Ela (e a `libgomp`) só
vai ao lado do RetroArch quando o Linux não tem a de verdade.

**O Python do pen drive FAT32.** O `ARENA.sh` tenta o Python que veio junto;
se o pen drive não deixar executar, uma cópia dele vai para
`~/.cache/arena` (uma vez só) e roda de lá. Do zip sem a permissão de
executar, numa pasta que aceita, ele só marca a permissão. Sem o Python que
veio junto, vale o do computador (3.11 ou mais novo).

**Os emuladores de fora na mesma pasta de dados.** No Windows, o PCSX2, o
RPCS3 e o Xenia ficam portáteis pelo `portable.txt`. No Linux, o PCSX2 e o
RPCS3 guardam tudo em `$XDG_CONFIG_HOME/PCSX2` e `$XDG_CONFIG_HOME/rpcs3`: o
ARENA aponta o `XDG_CONFIG_HOME` para a pasta de cima (`emuladores/PCSX2`), e
a pasta de dados vira a mesma do Windows. O Xenia recebe a pasta pelo
`--storage_root`, o Dolphin pelo `-u`.

**O Java do Java ME.** O `jlink` do JDK do Windows monta o Java do Linux
quando recebe os módulos (`jmods`) do JDK do Linux da mesma versão: o mesmo
Temurin, os mesmos três módulos, 58 MB.

**Um `retroarch.cfg` para os dois sistemas.** A cada abertura, o ARENA
reescreve os caminhos que apontam para a pasta do outro sistema e troca os
motores que só existem num deles (o som WASAPI vira PulseAudio ou ALSA; o
controle XInput vira udev; o d3d11 vira glcore), e o contrário no Windows.

## Os testes

- **A bateria inteira no Linux:** `testes/linux/bateria.sh`, num Debian 13
  no conteiner do WSL (WSLC), numa cópia gravável do ARENA: **532 de 532**
  em 17/10/2026 (os mesmos testes do Windows, 25 pulados por precisarem do
  Windows ou do git).
- **De ponta a ponta:** `testes/teste_linux.py` (no Windows, ele mesmo monta
  o conteiner e roda lá dentro): cada jogo livre dos testes abre no
  RetroArch do Linux com imagem de verdade, também numa pasta com acento;
  um jogo pelo servidor (`/api/jogar`), com a foto da tela e a sessão no
  banco; o `ARENA.sh` com o Python que não pode ser executado; o
  `VERIFICAR.sh`; e os emuladores de fora. O resultado, com os tempos, vai
  para `docs/linux_bruto.json`.
- **A conferir:** o teste de ponta a ponta ainda não rodou. Na madrugada de
  18/10, a máquina virtual do contêiner travou (o serviço do WSL ficou
  "parando" e o Windows não a deixou encerrar); ele volta a funcionar
  depois de reiniciar o Windows. Até lá, o que está provado é a bateria
  inteira no Linux e as partes separadas: o AppImage extraído no contêiner
  e as bibliotecas que faltavam (a `libjack` no RetroArch, a `libgomp` no
  Dreamcast), conferidas uma a uma.

## O que não dá para ter igual

- **Dolphin de fora:** o projeto não publica versão portátil para Linux. O
  GameCube e o Wii abrem pelo núcleo do Dolphin (o mesmo do Windows).
- **Xbox 360:** o Xenia do Linux é experimental (muitos jogos não abrem), e,
  como no Windows, exige processador com AVX e placa com Vulkan: não roda
  no notebook da escola.
- **Apple II:** o núcleo do Linux é o *nightly* do libretro (o do 1.22.2 do
  Linux não existe); o ARENA leva o conferido em 17/10/2026.
- **Prioridade alta para o emulador:** sem administrador, o Linux não deixa
  subir a prioridade de um programa. O efeito parecido vem da sessão
  própria do emulador (ver a tabela).
