<p align="center">
  <picture>
    <source media="(prefers-color-scheme: light)" srcset="docs/imagens/arena-claro.gif">
    <img src="docs/imagens/arena-escuro.gif" width="100%"
         alt="ARENA, central retrô da turma: o nome ARENA em letras douradas sobre o fundo animado em pixel art do ARENA. No tema escuro, todos os personagens do céu de galáxia passam na frente do nome, um de cada vez: Mario e Luigi na Rainbow Road, as máquinas do F-Zero, o Kirby na Warp Star, os Space Invaders, as Arwings, o Super Sonic e o Dr. Robotnik, a nave da Samus, o Mario de capa, o Meta Knight, a Vic Viper, o Ristar, ToeJam &amp; Earl, o Starman, o Earthworm Jim e a Lunar Whale, com o cometa, a chuva de meteoros, o OVNI, o satélite e o foguete; no tema claro, o Yoshi come uma frutinha no campo florido">
  </picture>
</p>

<h1 align="center">ARENA — central retrô da turma</h1>

<p align="center">
  Uma central de jogos retrô <b>portátil</b> para a sala de aula.<br>
  Copia a pasta, dá dois cliques e joga: <b>sem instalar nada e sem senha de administrador</b>.<br>
  Roda de pen drive, funciona sem internet e foi feita para o notebook mais fraco da escola.
</p>

<p align="center">
  <a href="https://github.com/RafaParise/arena-console/releases/latest"><b>⬇️ Baixar o ARENA pronto</b></a>
  &nbsp;·&nbsp; <a href="LEIA-ME.md">Leia-me do aluno</a>
  &nbsp;·&nbsp; <a href="1-COMECAR.md">Primeiros passos</a>
  &nbsp;·&nbsp; <a href="#perguntas-frequentes">Perguntas frequentes</a>
</p>

---

## O que é

O ARENA junta numa tela só, em português, os emuladores de **mais de 50 consoles** —
do Atari 2600 ao PlayStation 3 e ao Xbox 360 — e cuida do que costuma dar
trabalho: achar o jogo, escolher o emulador, ajustar a imagem para o
computador que está ali, configurar o controle, guardar o save e juntar os
recordes da turma.

Ele nasceu nas aulas do curso técnico de **Desenvolvimento de Sistemas**
(Ensino Médio, rede estadual de São Paulo) e tem dois papéis ao mesmo tempo:

1. **Um produto que funciona:** os alunos jogam, guardam recordes, jogam juntos
   pela rede da escola e levam o progresso no bolso.
2. **Material de aula:** o próprio código é o objeto de estudo de Redes,
   Banco de Dados, Back-End, Front-End e Metodologias Ágeis. Por isso ele é
   escrito em **Python puro**, sem bibliotecas de fora, e todo comentado em
   português.

## O que ele faz

| | |
|---|---|
| 🎮 **Um clique para jogar** | A pasta de cada console decide de quem é o jogo. Capas, nomes e quantos jogadores cada jogo aceita aparecem sozinhos |
| 🧠 **Ajuste automático** | Mede o computador (processador, memória, placa de vídeo, disco) e escolhe a imagem certa para cada console. Tem modo para notebook fraco |
| 💾 **Saves e cópia de segurança** | 10 lugares de salvar por jogo, cheats, e uma cópia de segurança quando algo muda |
| 👥 **Jogar junto** | Dois ou mais computadores na mesma rede, sem servidor: até **5 jogadores** no Super Bomberman (Multitap). Funciona por Wi-Fi, cabo direto e celular como rede (de uma casa para outra, pela internet, ainda não) |
| 🕹️ **Vários controles** | Xbox, PlayStation, Switch Pro, fliperamas e genéricos, com o teclado como o próximo jogador |
| 🏆 **Recordes da turma** | Placar com posição por jogo, conquistas e sincronização entre os computadores da sala — até sem rede, levando a "mala" no pen drive |
| 🧰 **Conserta sozinho** | `VERIFICAR.bat` confere e conserta a pasta; `PARTIDA.bat` explica por que a partida a dois não conecta; a tela explica por que um jogo não abriu |
| 🔒 **Seguro para menores** | Sem gravação de vídeo e sem transmissão ao vivo. Só o que o Jogar Junto precisa fica aberto à rede |

## Baixar e usar

1. Baixe o arquivo **`ARENA-2026.10.11.zip`** (uns 480 MB; descompactado, 1,3 GB) na página
   [**Releases**](https://github.com/RafaParise/arena-console/releases/latest).
2. **Antes de descompactar, desbloqueie o arquivo:** botão direito no `.zip`
   → **Propriedades** → marque **Desbloquear** (embaixo, em "Segurança") →
   **OK**. O Windows marca tudo o que vem da internet; sem esse passo, cada
   programa de dentro do pacote pergunta se pode abrir. Não precisa de senha
   de administrador.
3. Descompacte na raiz do disco: em **Extrair tudo**, troque o destino por
   `C:\` (o `.zip` já traz a pasta `ARENA`, e fica `C:\ARENA`) ou pela raiz
   de um pen drive formatado em **exFAT** (`D:\`, e fica `D:\ARENA`). Em pen
   drive FAT32, jogo maior que 4 GB (PS2, Wii, PS3, Xbox 360) não cabe.
4. Dois cliques em **`ARENA.bat`**. Uma janela preta abre (não feche ela) e,
   em seguida, a tela do ARENA.
   - Se ainda assim o Windows mostrar *"O Windows protegeu o seu computador"*:
     clique em **Mais informações → Executar assim mesmo**. Isso acontece com
     todo programa baixado da internet que não é vendido em loja.
5. Coloque os seus jogos em `jogos\pessoais\<console>` e clique em
   **Atualizar lista**. A barra da esquerda tem o botão **Como colocar
   jogos**, que diz a pasta, os formatos e o que falta para cada console.

**Já usa o ARENA?** Para atualizar sem perder nada, baixe o
`ARENA-2026.10.11-atualizacao.zip` (só o programa, uns 11 MB) e descompacte
no mesmo lugar, substituindo os arquivos: o passo a passo está no
[guia 6](6-RECURSOS-E-REPARO.md). O pacote completo é para instalar do zero.

Passo a passo completo, com a tabela dos problemas mais comuns: [`1-COMECAR.md`](1-COMECAR.md).

### O que vem no pacote

O ARENA, o Python embutido, o **RetroArch** com os 48 núcleos que o ARENA usa,
o **PCSX2** (PlayStation 2), o **Dolphin** (GameCube e Wii), o **RPCS3**
(PlayStation 3) e o **Xenia** (Xbox 360) — já configurados para rodar de
dentro da pasta, sem gravar nada fora dela.

### O que NÃO vem (e por quê)

- **Jogos.** São de quem tem o jogo. O ARENA lê o que você colocar nas
  pastas. Para começar sem nada, a **Biblioteca online** (barra da esquerda)
  baixa jogos de MS-DOS que os próprios autores liberaram, e os consoles de
  fantasia (TIC-80, WASM-4, LowRes NX, Uzebox) existem justamente para jogos
  livres.
- **BIOS e firmware** (PlayStation, Sega CD, Saturn, Neo Geo, PS3...). São
  programas da Sony, da Sega, da SNK e de outras empresas: só podem vir do seu
  próprio console. Ponha cada uma em `BIOS\<console>` e o ARENA reconhece,
  instala com o nome certo e mostra o que ainda falta
  (**Ajustes → Emuladores → BIOS dos consoles**). A exceção é a **BIOS
  livre**, escrita do zero por voluntários: essa já vem com o ARENA (o
  C-BIOS, que abre os cartuchos do MSX, e o EmuTOS, que liga o Atari ST; o
  AltirraOS, que liga o Atari 8-bit, vem dentro do emulador dele), e a de
  verdade passa na frente dela.

## Requisitos

| | Mínimo | Bom |
|---|---|---|
| Sistema | Windows 10 ou 11, **64 bits** | |
| Processador | 2 núcleos (Celeron, Pentium) | 4 núcleos ou mais |
| Memória | 4 GB | 8 GB |
| Espaço | 4 GB, mais os jogos | SSD ou pen drive USB 3.0 |
| Permissão | **nenhuma** — conta de aluno serve | |
| Internet | não precisa | capas e biblioteca online |

A régua de desempenho do projeto é um notebook de escola com **Celeron N5100**
(4 núcleos de 1,1 a 2,8 GHz, sem AVX, 8 GB em canal simples). Nos testes do
professor, num N5100 com o Windows enxuto, o PlayStation 2 e o PSP rodaram,
com quedas em alguns jogos. O PlayStation 2 e o GameCube ficam abaixo do
mínimo que os próprios emuladores pedem: depende do jogo e de como o Windows
está. O Xbox 360 exige processador com AVX (não abre nele), e o PlayStation 3
pede uma máquina bem mais forte. O desempenho de cada console nesse notebook
ainda vai ser medido em sala; o que já foi medido está em
[`docs/MAQUINA-ALVO.md`](docs/MAQUINA-ALVO.md).

## Os consoles

| Família | Consoles |
|---|---|
| Nintendo | NES, Super Nintendo, Game Boy e Color, Game Boy Advance, Virtual Boy, Nintendo 64, Nintendo DS, GameCube, Wii, Pokémon mini, Game & Watch |
| Sega | SG-1000, Master System, Mega Drive, Game Gear, 32X, Sega CD, Saturn, Dreamcast |
| Sony | PlayStation, PlayStation 2, PSP, PlayStation 3 |
| Microsoft | Xbox 360, MS-DOS |
| Atari | 2600, 5200, 7800, Lynx, Jaguar, ST, 8-bit (400, 800, XL e XE) |
| Fliperama | Neo Geo e fliperamas (FBNeo), Arcade (MAME), Neo Geo Pocket |
| Outros | PC Engine, PC-FX, WonderSwan, 3DO, CD-i, Odyssey 2, ColecoVision, Intellivision, Vectrex, MSX, Commodore 64, Commodore 128, VIC-20, Plus/4, PET, Amiga, ZX Spectrum, ZX81, Amstrad CPC, Apple II, Thomson MO/TO, Watara Supervision, Arduboy, ScummVM, Tamagotchi, Java ME (ainda sem núcleo) |
| Consoles de fantasia | TIC-80, WASM-4, LowRes NX, Uzebox, CHIP-8, MicroW8 |

## Os guias

Cada guia tem passos numerados e uma tabela de problemas no fim.

| # | Guia | Para quê |
|---|---|---|
| — | [LEIA-ME](LEIA-ME.md) | O começo, para o aluno |
| 1 | [COMEÇAR](1-COMECAR.md) | Preparar o pen drive e montar o ARENA |
| 2 | [JOGOS](2-JOGOS.md) | Pastas, consoles, BIOS, fliperama, emuladores de fora |
| 3 | [IMAGEM, SOM E CONTROLE](3-IMAGEM-SOM-CONTROLE.md) | Controles, travamentos, desempenho |
| 4 | [SAVES](4-SAVES.md) | Os 10 saves, cheats e não perder nada |
| 5 | [AMIGOS](5-AMIGOS.md) | Recordes da turma e jogar junto pela rede |
| 6 | [RECURSOS E REPARO](6-RECURSOS-E-REPARO.md) | As opções avançadas e o verificador |

## Para quem programa

Tudo é **Python 3.13 puro** (só a biblioteca padrão) e uma tela em
**HTML + CSS + JavaScript sem framework**. O servidor roda em `127.0.0.1:8777`
e a tela abre como janela de aplicativo no Edge que já vem no Windows.

```
ARENA\
├── ARENA.bat · VERIFICAR.bat · PARTIDA.bat · COLETAR.bat · RODAR_TESTES.bat
├── servidor\     o servidor, o banco (SQLite), o catálogo, a rede e os ajustes
│   ├── arena.py         as rotas da API, o banco, a sincronização e o Jogar Junto
│   ├── indexador.py     acha os jogos nas pastas
│   ├── hardware.py      mede o computador
│   ├── graficos.py      a configuração de cada emulador
│   ├── consoles.json    os 65 consoles
│   └── tests\           a bateria de testes (RODAR_TESTES.bat)
├── launcher\     a tela (index.html, app.js, estilo.css e os fundos em pixel art)
├── testes\       testes de ponta a ponta com os emuladores de verdade
├── ferramentas\  montar a versão dos alunos, medir o computador, a rodada de testes
└── docs\         relatórios das auditorias, a máquina-alvo, os roteiros de sala
```

**Por onde começar a mexer**, do mais fácil para o mais difícil:

1. `launcher\estilo.css` — as cores estão todas no topo. Mude uma e recarregue a tela.
2. `servidor\consoles.json` — acrescente uma extensão de arquivo e veja a lista mudar.
3. `servidor\indexador.py`, função `limpar_titulo` — mude como o nome do jogo aparece.

**Testes:** `RODAR_TESTES.bat` roda a bateria (mais de 300 testes, uns 25
segundos). Os scripts de `testes\` abrem os emuladores de verdade (o
RetroArch, o PCSX2, o Edge sem janela) e a rodada completa
(`ferramentas\rodada_final.py`) leva cerca de 1h30. As decisões do projeto, com
o porquê de cada uma, estão no [`CLAUDE.md`](CLAUDE.md); os relatórios das
auditorias, em [`docs\`](docs/).

**Trabalhar em mais de um computador (e na nuvem):** este repositório é a
cópia central. No começo, puxe; no fim, envie — o `SINCRONIZAR.bat` faz os
dois e confere, antes de enviar, que nada de BIOS, jogo, save ou dado de
aluno vai junto (o repositório é público). Passo a passo e regras para os
assistentes de programação: [`docs/SINCRONIZAR-COM-O-GITHUB.md`](docs/SINCRONIZAR-COM-O-GITHUB.md)
e [`AGENTS.md`](AGENTS.md).

**Restrições que valem para toda mudança:** sem `pip install`, sem
administrador, caminhos relativos (roda de pen drive), funciona sem
internet, e cabe num Celeron de escola.

### Imagens desta página

As imagens do topo saem dos próprios fundos animados do ARENA
(`launcher\galaxy-background.js` e `launcher\field-background.js`): quem usa
o GitHub no tema escuro vê o céu, e quem usa o tema claro vê o campo. O do
céu mostra **todos os personagens e animações do modo escuro**: as 15
visitas, uma atrás da outra e em velocidade dobrada, e os de passagem
(cometa, chuva de meteoros, OVNI, satélite e foguete), com os personagens
passando na frente do nome. Uma cópia dele fica na raiz do repositório
(`arena-escuro.gif`), para usar em outros lugares. Mudou um fundo? Grave de
novo:

```
servidor\python\python.exe ferramentas\gravar_fundo_gif.py --tema escuro --visitas kart,todas --disparar foguete,satelite,meteoros,ovni,cometa --ate-o-fim --quadros 2000 --passo 12 --escala 6 --girar 13 --tolerancia 12
servidor\python\python.exe ferramentas\gravar_fundo_gif.py --tema claro --visitas yoshi --quadros 68 --girar 26
servidor\python\python.exe ferramentas\gravar_fundo_gif.py --tema escuro --visitas kart --quadros 63 --passo 6.4 --girar 24 --tolerancia 12 --saida docs\imagens\arena-escuro-curto.gif
```

Eles gravam `docs\imagens\arena-escuro.gif` (960 × 480, 5,2 MB, com
todos), `docs\imagens\arena-claro.gif` (1280 × 640, o Yoshi) e
`docs\imagens\arena-escuro-curto.gif` (1280 × 640, só a Rainbow Road, 784 KB:
a "Social preview" do GitHub aceita até 1 MB). Para conferir o GIF sem abri-lo quadro a quadro, ponha
`--amostras folha.png` no comando: sai uma folha com cada visita.
A versão parada, em PNG, sai de:

```
servidor\python\python.exe ferramentas\imagem_do_github.py
```

Ela grava `docs\imagens\arena-capa.png` (1280 × 640) e
`docs\imagens\arena-fundo-escuro.png` (1920 × 1080, o céu sem texto, para
papel de parede ou apresentação).

Para a imagem aparecer quando alguém compartilha o link do repositório
(WhatsApp, Classroom, redes sociais), o dono do repositório envia a imagem
uma vez pelo site — o GitHub não deixa fazer isso por programa: **Settings →
General → Social preview → Edit → Upload an image** →
`docs\imagens\arena-escuro-curto.gif` (o completo passa de 1 MB, o limite
dessa página). A maioria dos sites mostra só o primeiro quadro (Mario e
Luigi na Rainbow Road); a `arena-capa.png` também serve.

## Perguntas frequentes

**Precisa de internet?** Não. Internet só serve para baixar capas e buscar jogos na
biblioteca online.

**Por que um jogo de PlayStation não abre?** Quase sempre é a BIOS. Abra
**Ajustes → Emuladores → BIOS dos consoles**: a tela diz qual arquivo falta e
onde pôr.

**A janela preta abre e fecha na hora.** O antivírus bloqueou o Python
embutido, ou o Windows é de 32 bits. O [`1-COMECAR.md`](1-COMECAR.md) explica
como liberar.

**Meu amigo não aparece na lista para jogar junto.** Rode o **`PARTIDA.bat`**
nos dois computadores: ele testa a rede e diz o que fazer ("Aceitar conexões
da rede" desligado, rede marcada como pública no Windows, endereço de
adaptador virtual, versões ou arquivos de jogo diferentes...). Detalhes no
[`5-AMIGOS.md`](5-AMIGOS.md).

**Dá para gravar ou transmitir a partida?** Não, de propósito: o ARENA é
usado por alunos menores de idade, e gravar voz e imagem de estudante, ou
transmitir para a internet, não tem lugar na escola. A foto da tela (`F8`)
continua funcionando.

## Licença

O código do ARENA é software livre, sob a licença **GPL-3.0** (arquivo
[`LICENSE`](LICENSE)): pode usar, estudar, mudar e distribuir, desde que as
versões modificadas continuem livres.

O pacote para baixar leva programas de outros projetos, cada um com a sua
licença — a lista, com o link do código-fonte de cada um, está em
[`TERCEIROS.md`](TERCEIROS.md).

## Créditos

Criado por **Rafael Parise Passos**, professor da rede estadual de São Paulo
(SEDUC-SP), com as turmas de Desenvolvimento de Sistemas. A base da tela e a
primeira bateria de testes vieram de um remake do ARENA feito por um aluno. O
desenvolvimento usa o Claude Code como parceiro de programação, com as
decisões e os testes de sala do professor.

Os emuladores são obra das equipes do RetroArch/libretro, PCSX2, Dolphin,
RPCS3 e Xenia — o ARENA só os organiza para a sala de aula.
