# Relatório da Auditoria 5 (24 e 25/10/2026)

Pedido do Rafael: depois de implementar os acessórios, conferir **função por função** que nada ficou de fora das versões
(Windows, Linux, Android, Chromebook) e fazer uma **auditoria completa** (front-end, back-end, banco e modelagem, lógica e
linguagem, redes e segurança, processos de desenvolvimento), distribuindo o trabalho e economizando tokens, com os testes
dele e as etapas manuais **por último**. O pedido inteiro está em `docs\PLANO-AUDITORIA.md` ("Auditoria 5").

## Como foi feita (e por que nessa ordem)

1. **Medir antes de opinar** (zero token de modelo): bateria do servidor, auditoria estática, matriz de paridade dos consoles,
   `ferramentas\auditoria_front.py` (axe-core + contraste calculado + alvos de toque, em 4 tamanhos e 2 temas, 200 telas),
   `ferramentas\metricas_de_codigo.py` (funções longas e complexas, exceções engolidas, módulos sem teste) e
   `ferramentas\paridade_de_funcoes.py` (rotas da tela × servidor × versão web).
2. **Revisores em paralelo só onde o juízo humano pesa**: 3 revisores de leitura (redes e segurança, back-end, código novo em
   Python), cada um com o **seu arquivo de saída**, esforço médio e teto de 45 chamadas de ferramenta; cada achado de gravidade
   média ou maior foi conferido por um **cético** que tenta refutar. Custo: ~640 mil tokens (110 chamadas), contra os ~2
   milhões gastos, sem resultado nenhum, pela primeira tentativa (5 revisores sem teto, que bateram no limite da sessão).
3. Consertar o que é real, com teste, e medir de novo.

## Resultado em números

| Medida | Antes | Depois |
|---|---|---|
| Problemas distintos na tela (axe-core + medidas) | 10 | **0** (100 telas medidas de novo) |
| Rotas que a tela chama sem o servidor atender | 0 de 79 | 0 de 79 |
| Achados dos revisores | 20 (0 críticos, 0 altos; 5 de gravidade média declarada) | 5 conferidos por céticos: 3 médios confirmados, 2 rebaixados a baixa, **0 refutados**; todos os 5 consertados |
| Testes do servidor | 981 | **987** (6 novos) |
| Servidor | 29.320 linhas em 42 módulos | idem |

## Front-end

Medido com o axe-core 4.10.2 (regras WCAG 2.0/2.1/2.2 A e AA e boas práticas) e conferências próprias. Eram 10 problemas; todos
consertados (`2994d04`):

- **Lista de jogos**: o `<li>` tinha `role="button"` com botões dentro (botão dentro de botão: o leitor de tela não anuncia certo; axe
  `nested-interactive`, `aria-allowed-role` e `list`, graves, em 200 telas). Agora o item é um item de lista comum (com `title`).
- **Título principal**: não havia `<h1>`; "ARENA" passou a ser o `h1`. **Fundos animados** (`canvas`) marcados `aria-hidden`.
- **Contraste** (WCAG 1.4.3): o vermelho de texto no tema claro dava 3,3:1 (`--erro-texto` agora dá 5,9:1); o selo "não instalado"
  usava `opacity: 0.55` (virou um selo de contorno); o selo cinza dava 4,06:1.
- **Alvos de toque** (WCAG 2.2, 2.5.8: mínimo 24 × 24): interruptores de 40 × 22 viraram 40 × 24; o botão "ver exemplo" (19 px) e as
  caixas de marcar (13 px) passaram de 24 px.
- **Letra mínima** de 12 px (era 11,52).
- Não eram problema (falso positivo da própria medida, já corrigido na ferramenta): botões dentro de `<details>` fechado.

Sem estouro para os lados em nenhum dos 4 tamanhos (360, 768, 1280 e 1920 px), sem id repetido, `lang="pt-BR"`, janela e gaveta com
`role="dialog"` e foco guardado (auditoria 3).

## Redes e segurança

Superfície bem fechada (conferido pelo revisor): `Host` validado (contra DNS rebinding), todo POST exige JSON, só 7 rotas abertas à
rede, segredo do Android com HMAC, componentes do RetroArch não exportados, `allowBackup` desligado, tráfego em texto claro só para
127.0.0.1, extração de zip com `_partes_seguras`, redirecionamento só para HTTPS, conferidor de publicação (token, e-mail, CPF, caminho
de usuário). Achados:

| ID | Gravidade | O que era | Situação |
|---|---|---|---|
| REDE-01 | média (confirmado) | `/api/partida/testar`, com a rede liberada, deixava um colega mandar o ARENA do aluno **varrer portas** da rede da escola | **Corrigido** (`d83cf42`): pedido de fora só testa quem pediu, na porta de sempre |
| REDE-02 | média (confirmado) | o código de aparelho, anunciado em claro no UDP, podia ser trocado por qualquer colega a cada pedido | **Corrigido**: no máximo uma troca por hora (o caso real, duas máquinas da mesma imagem, resolve na primeira) |
| REDE-03 | baixa | `/api/partida/cheguei` de fora abre o jogo de quem esperava a partida | registrado (é o propósito da rota; o risco é só "abrir o jogo que o aluno já ia abrir") |
| SUP-01 | baixa | emuladores e companheiros (`emuladores\...`) abrem de pasta gravável sem conferir hash | **aceito e registrado**: o aluno que escreve ali já executa código como ele mesmo; conferir hash exigiria lista de versões e quebraria a troca do emulador pelo professor |
| SUP-02 | baixa | arquivos soltos na raiz (conversas, troca de recordes) fora do `.gitignore` | **Corrigido** |
| AND-01 | informativa | `MANAGE_EXTERNAL_STORAGE` e cookie do segredo sem escopo de porta | registrado (o RetroArch oficial também pede) |

## Back-end e código novo

Nenhum defeito crítico ou alto. Conferidos e corrigidos: **DAD-01** (média, no limite de baixa): cartão de PS2 de 64 MB que falha no
meio deixava o `.tmp` parcial por tentativa; **COR-01**: o laço sobre `indexador.ORIGENS` quebraria se o cartão SD ligasse em outra
thread (agora percorre uma cópia); **ACE-01**: o DreamPotato pedido e ausente agora avisa no registro. Pequenos corrigidos: expressões
regulares com `$` (aceitam quebra de linha no fim) viraram `\Z`; `companheiros.fechar` aguenta `TimeoutExpired`; `pokketsx` grava com
temporário por thread. Registrados sem conserto: `desempenho.py` grava JSON sem o gravador atômico (baixa), buscas longas do
armazenamento rodam na thread do pedido (baixa), config antiga `cartoes_ps2` anula em silêncio a escolha nova (baixa).

## Banco e modelagem

SQLite `dados\arena.db`: duas tabelas autossuficientes (`placar`, `sessao`) com `uuid` como chave (o recorde viaja sozinho entre ARENAs, de
propósito), índices em `jogo_id` e `enviado`, WAL com `synchronous = NORMAL`, migrações com `ALTER TABLE` sob trava, banco corrompido
guardado ao lado em vez de apagado. **Sem risco de dado**; melhorias baratas, sem urgência: `CHECK (pontos >= 0)` (hoje a validação
é só em código: `pontos_validos`) e índice em `apelido` (as consultas de conquistas agrupam por apelido; a tabela é do tamanho de uma
sala). O que se grava do aluno: apelido, código do aparelho, jogo, pontos e tempo; nenhum nome real, telemetria ou captura de tela.

## Lógica e linguagem

Nove `except Exception: pass` no servidor e nas ferramentas (`arena.py` 2, `hardware.py` 4, `arrumar.py` 1, ferramentas 2): todos em
leitura de informação opcional da máquina (o ARENA segue sem ela); nenhum esconde gravação. Funções gigantes: `api_post` (1.591 linhas,
complexidade 441), `executar_jogo` (588 / 140), `api_get` (436 / 88), `barreiras.avaliar` (253 / 102): **dívida técnica**, não defeito
(ver processos).

## Processos de desenvolvimento e métodos ágeis

- **Pirâmide de testes**: 987 unitários em segundos (sem pip), integração em `testes\` (cópia do ARENA numa pasta com acento, RetroArch de
  verdade) e a rodada final (~80 min). Faltava um teste de integração por recurso novo grande: o PokketSX e o cartão único ganharam o
  seu (`testes\teste_pokketsx_pelo_arena.py`). Os 42 módulos do servidor são citados por algum teste.
- **Testes sensíveis à carga** (dois, ambos passam com a máquina livre): `test_desempenho.Medida` (o processo de teste demora a nascer e o
  medidor desiste) e os pisos de quadros do `teste_chromebook.py` no Firefox. **Intermitente**: `test_android.RotasDoAndroid`
  falhou 1 vez em 4. Pelo caminho, `test_icone` falha se a bateria rodar com `python -X utf8` (rodar sem).
- **Integração contínua**: só existe `.github\workflows\nucleo-ps2-android.yml` (compila o núcleo do PS2). **Nada roda a bateria a
  cada commit.** História recomendada abaixo.
- **Dívida técnica**: `arena.py` com 8.192 linhas (o CLAUDE.md dizia ~6.700; corrigido). Refatoração segura: testes de caracterização das
  rotas, depois uma tabela `{rota: função}` tirando as rotas uma a uma do `api_post`, sem mudar o comportamento.
- **Documentação que desatualiza**: o CLAUDE.md (contagem de linhas) e o `docs\ACESSORIOS.md` (63 contra 64 acessórios) divergiam do
  código; o primeiro foi corrigido, o segundo é a contagem por jogador contra por definição (a conferir).

### Backlog em histórias (ordem sugerida)

1. **Como mantenedor, quero a bateria rodando a cada commit** (GitHub Actions, `windows-latest` e `ubuntu-latest`, Python 3.13, sem pip) *para
   pegar regressão antes do Rafael*. Aceite: o commit com teste quebrado fica vermelho; os testes dependentes de RetroArch pulam. Tamanho **M**.
2. **Como mantenedor, quero as rotas do `api_post` numa tabela** *para poder testar e mudar uma sem arriscar as outras*. Aceite: nenhum
   teste muda; `api_post` abaixo de 100 linhas. Tamanho **G**, em fatias de 5 rotas.
3. **Como professor, quero que o DreamPotato ausente apareça na tela** (hoje só no registro) *para saber por que o VMU não abriu*. **P**.
4. **Como mantenedor, quero `CHECK (pontos >= 0)` e índice em `apelido`** no banco *para a defesa não depender só do código*. **P**.
5. **Como aluno elegível a adaptação, quero conferir a tela com leitor de tela de verdade** (NVDA) *para além do que o axe mede*. **M**.

Definição de pronto sugerida: código + teste (unitário e, se abre emulador, de integração) + guia atualizado + bateria verde + medida
do front (`auditoria_front.py --rapido`) sem problema novo.

## O que não foi verificado (honesto)

- Os revisores não leram por inteiro `api_get`/`api_post`, `bios.py`, `arrumar.py`, `baixar.py`, `indexador.py`, `hardware.py`,
  `processos.py`, `portas.py`; nem a escuta UDP (spoof e amplificação), nem `ArenaServico.java` além do cabeçalho, nem injeção de comando em
  `.bat`/`.ps1`/`.sh`, nem links simbólicos em `dentro_da_pasta` (usa `abspath`, não `realpath`: exigiria escrita na pasta de jogos).
- Nada do servidor foi executado pelos revisores; REDE-01, REDE-02 e DAD-01 foram cobertos por testes novos
  (`servidor\tests\test_auditoria_25_10.py`).
- Front-end: medido por máquina (axe-core e contraste); **não** testado com leitor de tela, e o contraste sobre fundo animado ou translúcido
  sai como "não medido".
- Os domínios de lógica e de front-end não tiveram um revisor próprio nesta rodada (custo): o primeiro foi coberto pela revisão do código
  novo e o segundo pelas medidas.

## Fica por último (com o Rafael)

Os testes que dependem dos controles dele (GameSir G7 HE no PC, T4 Nova Lite no celular: Saturn e PS1 com o tipo 517, PokketSX, jogador 1 e 2 no
Android), o Chromebook da escola e as etapas manuais de `docs\PENDENCIAS.md`; e a rodada final de regressão (`ferramentas\rodada_final.py`).
