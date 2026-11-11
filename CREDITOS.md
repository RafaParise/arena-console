# Créditos

O ARENA foi criado por **Rafael Parise Passos**, professor da rede estadual
de São Paulo (SEDUC-SP), com as turmas de Desenvolvimento de Sistemas. As
decisões e os testes de sala são do professor, e o desenvolvimento usa o
Claude Code como parceiro de programação.

## O aluno DOOK3DS: a primeira publicação no GitHub

O ARENA chegou ao GitHub pela primeira vez pelas mãos de um aluno, a conta
**[DOOK3DS](https://github.com/DOOK3DS)**, em 19/09/2026: o repositório
[`DOOK3DS/ARENA-remake-`](https://github.com/DOOK3DS/ARENA-remake-), o
"ARENA v1.0". Esse trabalho faz parte da história deste repositório (a
etiqueta `v1.0`), e o pacote dele está nos Releases.

**Ideias dele que estão no ARENA de hoje** (contadas pelo professor):

- a primeira ideia e o esqueleto dos **fundos animados claro e escuro** da
  tela (`launcher\galaxy-background.js` e `launcher\field-background.js`);
- **baixar as capas dos jogos**: na v1.0, o ARENA montava o endereço das
  capas do repositório público do libretro; hoje é o `servidor\capas_online.py`;
- a **biblioteca para baixar jogos direto do archive.org**
  (`servidor\internet_archive.py`, a Biblioteca online).

**O que está na v1.0 dele** (conferido no código, comparando com a versão do
professor de 17/09/2026):

- a tela que virou a base do ARENA unificado em 20/09/2026;
- o **assistente de controle** para controle genérico, que pede cada botão
  na ordem (`launcher\app-wizard.js`; hoje é o "Configurar com assistente");
- a **primeira bateria de testes automáticos** (`servidor\tests`, 44 testes,
  e o `RODAR_TESTES.bat`). Hoje são 388 testes, que cresceram a partir dela;
- a **página de instalação** (`index.html`);
- o **código de amigo** curto, que não mostra o endereço do computador;
- a **sala de espera do Jogar Junto**: quem abre a partida espera o colega
  confirmar a entrada, e o **modo espectador**. O ARENA de hoje faz a mesma
  coisa desde 14/10/2026 (os dois começam juntos);
- **baixar o jogo de um colega** pela rede da sala (`servidor\transferencia.py`)
  ou pelo archive.org;
- as **conquistas** calculadas no próprio computador;
- o banco de dados num módulo separado (`servidor\db.py`) e o `.gitignore`.

**Correções dele:** o servidor passou a recusar o pedido que não fosse um
JSON com chaves e o grande demais; favoritos e recentes deixaram de repetir
jogo; o Jogar Junto do PlayStation passou a avisar em vez de falhar (o
núcleo da época não sincronizava as duas máquinas).

### As ideias de 11/11/2026: mais quadros e uma tela mais leve

O DOOK3DS também mostrou ao professor programas que ele não conhecia, e o professor adaptou as ideias para o ARENA:

| O que ele trouxe | O que virou |
|---|---|
| O **MFG Super Motion**, programa gratuito que cria quadros entre os do jogo, como o Lossless Scaling | O ARENA acha o programa instalado, escolhe as opções para cada máquina e abre o motor dele junto com o jogo, no lugar do Lossless (`servidor\mfg.py`). A licença dele não deixa levá-lo junto |
| A ideia de juntar o melhor do Lossless e do MFG dentro do ARENA | O **Mais quadros unificado** (o ARENA sabe qual dos dois rende mais em cada placa e nunca abre os dois) e os **quadros de verdade**: o patch "60 FPS" que o próprio PCSX2 traz (627 jogos), no computador e no celular (`servidor\quadros_ps2.py`), e os códigos de 60 do Dolphin para o GameCube e o Wii (`servidor\quadros_dolphin.py`), antes de qualquer programa de fora |
| A ideia de trocar a parte web por **Rust**, para o ARENA ficar mais leve | A medida de onde está o peso: o servidor em Python usa 42 MB, a janela do navegador 629 MB. Virou a **janela leve** (perfil só do ARENA no navegador: 238 MB) e o **descanso do fundo animado**. A decisão sobre o Rust, com os números, está em `docs/replica/architecture.md` |

## O aluno HugoVHK: o teste dos saves do PS2 (03/11/2026)

O aluno da conta **[HugoVHK](https://github.com/HugoVHK)** testou o ARENA em
casa e mandou ao professor, com fotos da tela:

- **um defeito no save do PS2:** no *Crash of the Titans*, a tela de salvar
  ficava parada (só o logotipo do jogo e as linhas da caixa de salvamento).
  O primeiro save gravou, e o segundo não gravou mais;
- **o PS2 funcionando no computador dele:** *God of War* rodando liso, com a
  BIOS do console dele.

Depois (10/11/2026), mandou outro achado, também com foto: **o Google Play
Protect bloqueia a instalação do app do ARENA no celular** ("App de risco
bloqueado: esse app foi criado para uma versão mais antiga do Android"), e
avisou o professor para orientar a turma enquanto isso não se resolve. O
motivo está no APK: ele declara o Android 9 como versão-alvo, e o Play Protect
avisa quando a versão-alvo está mais de duas versões abaixo da do celular.
Ele também mandou os dados do celular onde o problema aparece (um Xiaomi
Poco X7, com HyperOS 2 e Android 15, o mesmo Android do emulador de testes do
ARENA) e contou que um colega só conseguiu instalar pelo APKMirror Installer.
Com isso, a nova versão-alvo do app foi escolhida para esse Android (API 35).

Os dois relatos viraram pendências registradas (`docs\PENDENCIAS.md`) e foram
a base da revisão dos saves e dos cartões de memória e da troca da versão-alvo
do app, na atualização de novembro de 2026. É o tipo de teste que o ARENA mais precisa: um aluno jogando de
verdade, numa máquina que não é a do professor, e contando o que travou.

**Tudo o que veio dele, e o que cada coisa virou no ARENA** (acrescentado em 10/11/2026):

| O que ele mandou | O que virou |
|---|---|
| Fotos da tela de salvar parada no *Crash of the Titans* (PS2): o segundo save não gravou | A revisão dos saves e dos cartões de memória: o "Continuar de onde parou" com a trava que nunca passa por cima de um save (`servidor\continuar.py`), a bateria do cartucho gravada a cada 10 s e a regra de ouro do PS2 no guia `4-SAVES.md` |
| O PS2 rodando liso no computador dele (*God of War*, com a BIOS do console dele) | A confirmação de que o caminho do PS2 no computador funciona fora da máquina do professor |
| A foto do aviso do Play Protect ("App de risco bloqueado") | A troca da versão-alvo do app para o Android 15 (API 35) e o aviso no texto dos downloads |
| A pergunta "desligar o Play Protect faz mal para o celular?" | A orientação para a turma: tocar em "Instalar assim mesmo" e **não** desligar o Play Protect (ele é o antivírus do celular) |
| O aviso para orientar o grupo da turma sobre o erro na instalação | O texto dos downloads explicado por aparelho |
| O colega com um Xiaomi mais novo que só instalou pelo APKMirror Installer | O estudo de como esse instalador funciona (o instalador em sessões do Android), anotado para o ARENA se atualizar sozinho |
| Os prints do ARENA no celular dele e os dados completos do aparelho: Poco X7, HyperOS 2.0, Android 15, Dimensity 7300-Ultra, 12 GB de memória (mais 6 GB virtuais) | O primeiro teste do app num celular de aluno com Android 15: a referência de aparelho moderno, ao lado do A12 do professor |

## As versões para baixar

Nos [Releases](https://github.com/RafaParise/arena-console/releases), da
mais antiga para a mais nova:

| Versão | Data | O que é |
|---|---|---|
| `v0.9` | 17/09/2026 | a versão do professor antes da do aluno (o `ARENA.zip` de então) |
| `v1.0` | 19/09/2026 | a do aluno DOOK3DS, a primeira publicação no GitHub |
| `v2026.10.11` | 12/10/2026 | a primeira versão pública do ARENA unificado |
| `v2026.10.15` | 15/10/2026 | 66 consoles e BIOS livres, num download só |

A v1.0 do aluno não descende da v0.9: ela saiu de uma versão do professor
um pouco mais antiga. Por isso as duas entram no histórico do git como
pontos de partida separados, unidos depois na base de 20/09/2026.

## Os emuladores

São obra das equipes do RetroArch/libretro, PCSX2, Dolphin, RPCS3, Xenia,
FreeJ2ME-Plus e dos outros projetos listados em
[`TERCEIROS.md`](TERCEIROS.md). O ARENA só os organiza para a sala de aula.
