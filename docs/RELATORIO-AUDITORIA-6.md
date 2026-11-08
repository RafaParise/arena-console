# Relatório da Auditoria 6 (07 e 08/11/2026, de madrugada)

Pedido do Rafael (inteiro em `docs\PLANO-AUDITORIA.md`, "Auditoria 6"): terminar o que o teste no Galaxy A12 mostrou,
as pendências das conversas passadas, ferramentas novas e o Lossless Scaling, e então "aquela auditoria que fizemos
outras duas vezes completa para poder lançar um release com todas as pendências amarradas".

## Como foi feita

Igual à auditoria 5, que deu certo: **medir antes de opinar** e só depois revisores, com teto.

1. **Medidas sem modelo**: bateria do servidor, auditoria estática, métricas de código, paridade de funções (tela ×
   servidor × navegador), axe-core + contraste em 108 telas, teste dos três navegadores.
2. **Três revisores em paralelo**, cada um com o seu arquivo de saída e teto de 45 chamadas, só no código novo desde a
   auditoria 5 (35 commits, ~5.500 linhas): redes e segurança, dados e back-end, front-end e lógica. O limite de uso da
   conta caiu no meio dos três; eles foram retomados de onde pararam (usaram 21 a 25 chamadas cada).
3. **Cada achado conferido no código** antes de consertar (o papel do cético), com teste novo para cada conserto.

## Resultado em números

| Medida | Auditoria 5 | Auditoria 6 |
|---|---|---|
| Auditoria estática (Python e tela) | 0 | **0** |
| Problemas na tela (axe-core + medidas) | 0 (100 telas) | **0** (108 telas, celular e notebook, claro e escuro) |
| Rotas que a tela chama sem o servidor atender | 0 de 79 | **0 de 90** |
| Teste dos navegadores | 30 de 30 | **30 de 30** (Edge, Chrome, Firefox) |
| Servidor | 29.320 linhas, 42 módulos | 32.647 linhas, 48 módulos |
| Achados dos revisores | 20 (5 médios) | **21**: 1 alto, 10 médios, 10 baixos |
| Corrigidos | 5 | **16** (o alto e 9 dos 10 médios) |
| Testes do servidor | 987 | **1213** |

## Os achados

Detalhes em `docs\auditoria6\achados_*.json` (cada um com a situação).

**Dados** (o que mais pesa: nenhum caminho pode apagar jogo ou save do aluno), em "Levar jogos da memória para o
cartão" e nos jogos baixados:

| ID | Gravidade | O que era | Situação |
|---|---|---|---|
| DAD6-01 | **alta** | Arquivo de mesmo nome e tamanho no cartão contava como cópia, e o original — até o save `.srm` de outro progresso — era apagado | **Corrigido**: conteúdo comparado byte a byte |
| DAD6-02 | média | O original saía sem reconferir a cópia (cartão retirado no meio) e o erro ao apagar era engolido | **Corrigido** |
| DAD6-03 | média | Trilha do `.cue` com maiúscula diferente e as trilhas dos `.cue` de um `.m3u` ficavam para trás: jogo quebrado nos dois lugares | **Corrigido**; trilha que falta não leva nada |
| DAD6-04 | média | O jogo levado perdia placar, tempo de jogo, favoritos e recentes (o id do jogo é o caminho) | **Corrigido** |
| DAD6-05 | média | "Levar para o ARENA" entre memória e cartão copiava direto no nome final | **Corrigido** (cópia conferida) |
| DAD6-06 | média | Jogo numa pasta com outros jogos levava a pasta inteira | **Corrigido** |
| DAD6-09 | média | A procura dos baixados roda na thread do pedido | Aceito: é da auditoria 4, só com o botão do aluno e limitada a 300 arquivos |
| DAD6-07, 08, 10, 11 | baixa | Jogar durante a mudança, erro inesperado sem recado, sobras `.arena-parcial`, cópia do Settings.xml do Lossless não atômica, arquivo de registro aberto | **Corrigidos** |

**Redes e segurança** (celular como controle, porta 8780): as rotas novas não aceitam pedido de fora, todo POST exige
JSON, nada de injeção de comando nem `../` em `/toque/`, apelido sem virar código na tela.

| ID | Gravidade | O que era | Situação |
|---|---|---|---|
| REDE6-01 | média | Um colega da mesma rede, sem o código, segurava as 24 vagas e nenhum celular entrava | **Corrigido**: no máximo 4 conexões por aparelho (o cabo USB fica no teto geral) |
| REDE6-04 | baixa | Desligar e ligar seguido deixava o controle sem código | **Corrigido** |
| REDE6-02, 03 | baixa | Celular já autenticado sem limite de ping; no cabo todos são 127.0.0.1 | Registrados (pedem um token por celular: melhoria futura) |

**Front-end e lógica**: nenhum `innerHTML` em `app.js` (sem XSS).

| ID | Gravidade | O que era | Situação |
|---|---|---|---|
| FRT6-01 | média | "Arrumar os botões da tela": trocar de console antes de Salvar perdia o que se arrumou no outro | **Corrigido**: todos os consoles mexidos são salvos |
| FRT6-02 | média | Peças do editor menores que 24 × 24 px no celular (a regra da auditoria 5) | **Corrigido** |
| FRT6-03 | média | O código e os celulares conectados ficavam velhos ao voltar à aba | **Corrigido** |
| FRT6-04 | baixa | "Levando para o cartão" congelava com uma falha passageira | **Corrigido** |
| FRT6-05, 06 | baixa | L3/R3 do PlayStation fora de ordem em pé; "Voltar ao de fábrica" grava na hora | Registrados (o aluno arruma no editor; o botão diz o que faz) |

## Antes da auditoria (os pedidos do teste no A12)

- **Deadly Alliance preso no LOADING**: o EE do PS2 a 50% (nível "mínimo") travava o carregamento; o mínimo agora é
  60% e a imagem do leve. Medido: carrega e roda a 100%.
- **Dois toques na tela** mostram o controle de toque com controle de verdade ligado (remendo do RetroArch).
- **Lossless Scaling**: geração de quadros também no PCSX2, Dolphin, RPCS3 e Xenia; no Black, 30 → 60 na tela
  (PresentMon). No A12 não dá (PowerVR; o Android 12 bloqueia).
- **Saturn no Jogar Junto PC × celular**: o Beetle Saturn declara o estado dependente da plataforma; registrado.

## O que NÃO foi verificado (e por quê)

- **Matriz de consoles** (`testes\teste_matriz_consoles.py`): o sistema a interrompeu por falta de memória do computador
  enquanto a sessão esperava; por regra, só roda de novo a pedido. Faz parte da **rodada final**, que o `CLAUDE.md`
  exige antes de versão nova.
- **`teste_android`**: precisa do emulador do Android, que não está instalado neste computador.
- **Linux de verdade** (`testes\teste_linux.py`, contêiner no WSL): não rodado nesta madrugada, pelo mesmo cuidado com a
  memória.
- **Controles de verdade** (GameSir T4 e G7 HE): só o Rafael.

Por isso o **release não foi publicado**: a versão 2026.11.08 e os APKs de produção ficaram prontos, e o texto do
release com "Qual arquivo baixar" por sistema está escrito; falta a rodada final e o "sim" do Rafael.
