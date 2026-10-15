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
