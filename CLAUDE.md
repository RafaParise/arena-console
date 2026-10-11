# CLAUDE.md — a memória do projeto ARENA

**Não substitua este arquivo inteiro.** Ele é lido por todo assistente que
abre o ARENA (Claude Code no computador ou na nuvem, Hermes e outros):
acrescente na seção certa e mantenha o que os outros escreveram. Desde
11/10/2026 ele mora no repositório (`https://github.com/RafaParise/arena-console`,
público): **nada de e-mail, senha, token ou dado de aluno aqui.**

**Caminhos:** o texto abaixo foi escrito com o Claude Code aberto na pasta
de cima do repositório. Onde estiver `ARENA-unificado\...`, dentro do
repositório é só tirar o `ARENA-unificado\` do começo (ex.:
`ARENA-unificado\docs\PLANO-AUDITORIA.md` = `docs\PLANO-AUDITORIA.md`). A
versão dos alunos fica ao lado do repositório, em `..\ARENA`.

## Regras de git (valem para todo assistente; detalhe no `AGENTS.md`)

- **Nunca `git add -A` nem `git add .`**: só os arquivos que você mudou.
  Mais de um assistente trabalha nesta pasta, às vezes ao mesmo tempo.
- **O repositório é só esta pasta.** Nunca `git init` na pasta dos alunos
  (`..\ARENA`) nem em pasta com jogos, BIOS ou dados.
- Sincronizar com o `SINCRONIZAR.bat` (ou `git pull --ff-only` / `git push`):
  ele confere antes de enviar (`ferramentas\conferir_antes_de_publicar.py`)
  e recusa BIOS, jogo, banco, save, e-mail institucional, senha e token.
  Nunca `git push --force` (o GitHub recusa: regra "Proteger os ramos").
- **No começo da sessão:** puxar, e conferir se outro assistente (Hermes)
  está rodando (`hermes.exe`) e se a pasta dos alunos ganhou um `.git`.
  **No fim:** atualizar o "Estado atual" abaixo, commit e push.

---

# ARENA

Console/launcher de jogos retrô portátil e sem instalação, baseado em RetroArch. Roda de uma pasta única (disco local ou pen drive), com cerca de 47 consoles emulados (NES ao PS2).

Uso: sala de aula, curso técnico de Desenvolvimento de Sistemas (Novotec, Ensino Médio), com alunos menores de idade.

Ambiente de desenvolvimento: Windows 11.

## Regras desta sessão de trabalho (ler antes de tudo)

- **Idioma:** tudo em português do Brasil — respostas, explicações, perguntas de decisão E a descrição curta de cada comando (o texto que aparece na caixa de permissão). O professor não trabalha com inglês técnico.
- **Tudo dentro da pasta, por disciplina — não por trava.** A trava `permissions.blockReadsOutsideWorkingDirectories` foi DESLIGADA em 21/09/2026 (mas em 24/09/2026 `~\.claude\settings.json` estava com ela LIGADA de novo — conferir antes de assumir; só o Rafael altera esse arquivo): neste Windows, com esta pasta, o analisador de comandos falhava ("Linha de comando muito longa") e todo comando pedia aprovação, dando o mesmo erro com Yes ou No. A regra continua valendo: o ARENA não pode depender de nada fora da própria pasta. Se um teste precisar ler fora dela, isso é BUG de portabilidade — um caminho absoluto vazando. Corrigir o caminho; não ler lá.
- **Comandos curtos.** Operação com mais de um passo → escrever um script `.py` em `ARENA-unificado\ferramentas\` e rodar com o Python embutido (`servidor\python\python.exe`). Comando que o analisador de permissões não consegue ler (ex.: "Linha de comando muito longa") pede aprovação manual e trava o trabalho. Se um comando travar ou for recusado duas vezes, não insistir: trocar por um script `.py` curto.
- **Régua de desempenho = máquina-alvo.** Toda decisão de desempenho é julgada pelo notebook descrito em `ARENA-unificado\docs\MAQUINA-ALVO.md` (Celeron N5100, sem AVX), **não pelo Ryzen do Rafael**. Mudança que fica boa no Ryzen e piora lá piorou o ARENA. Número medido com a janela do jogo coberta ou na bateria não decide nada.
- **Ao encerrar cada sessão:** atualizar a seção "Estado atual" abaixo e fazer commit. É isso que permite retomar sem depender do histórico da conversa.

## Estado atual (atualizar ao fim de cada sessão)

**RETOMAR DAQUI (11/10/2026, ~01h00) — sessão aberta em `C:\Projetos\Criador
De Apps Pedagógicos` (pedido: "continue de onde parou
quando acabou o limite da sessão do dia de hoje").** O que aconteceu e já foi
resolvido nesta sessão (detalhe no `docs\RELATORIO-QUALIDADE.md`, quando a
Fase 8 for escrita):

- **Pastas mudaram de lugar (10/10, ~23h49, não fui eu):** o repositório agora
  é `C:\Projetos\Criador De Apps Pedagógicos\ARENA-unificado` (era
  `...\ARENA\ARENA-unificado`) e a **versão dos alunos é
  `C:\Projetos\Criador De Apps Pedagógicos\ARENA`** (era `ARENA-alunos`). As
  duas versões originais e o `Instruções.txt` não estão mais em `C:\Projetos`
  (perguntar ao Rafael). O montador procura `..\ARENA-alunos`: usar o destino
  novo no `--atualizar` (conferir o parâmetro antes).
- **O GitHub é `RafaParise/arena-console`** (público; NÃO `RafaParise/ARENA`,
  que não existe — os docs `SINCRONIZAR-COM-O-GITHUB.md` e a ferramenta
  `sincronizar_github.py` ainda citam o nome errado: corrigir). `gh` instalado
  (`C:\Program Files\GitHub CLI\gh.exe`, logado como RafaParise) e credencial
  do Git guardada: dá para enviar sem pedir login.
- **10/10 19h23 — `git pull` (do Hermes) trocou o `.gitignore` do ARENA pelo de
  Python do GitHub**, deixou a junção pela metade e uma trava `index.lock`;
  um `sync_to_github.bat` (20h22) faria `git add -A` + push (BIOS, jogos e
  `arena.db` iriam a público). Consertado: junção desfeita, `.gitignore` de
  volta, trava velha removida, script em `ARENA-unificado\backup\desativados\`.
- **11/10 00h21–00h50 — o Hermes (`hermes --yolo`) fez `git init` NA PASTA DOS
  ALUNOS**, commit de 4.942 arquivos (BIOS da Sony/Sega/Nintendo, `backup\...
  \arena.db`, saves) e tentou `git push --force-with-lease` ao GitHub
  público (recusado: arquivos > 100 MB). **Parei o Hermes.** Ele tinha
  APAGADO do disco 8 arquivos (BIOS PS1/PS2, `dc_boot.zip`, `neogeo.zip`, o
  memory card `Memory Card Slot 1.ps2` do PCSX2, `rpcs3.exe`,
  `ni-n-sat.zip`): **devolvidos do commit dele e conferidos pelo hash.** O
  checkout dele converteu 6.453 textos para CRLF: 5.981 voltaram ao original
  (referência: a pasta de desenvolvimento). Conferência final: 8.637 de 9.113
  arquivos idênticos byte a byte ao das 00h29 (o resto: CRLF original ou
  configuração). Jogos intocados (103 arquivos, 3.957.916.092 bytes). O
  `.git` dele virou `ARENA\.git-do-hermes-desativado` (568 MB, nada apagado);
  o `.gitignore` dele em `.gitignore-do-hermes.txt`; `.gitignore` do ARENA no
  lugar; `ARENA\LEIA - GIT DESATIVADO.txt` explica. Há uma tarefa agendada
  `Hermes_Gateway` no Windows (não mexi).
- **E-mail institucional do professor** estava em 9 commits do `auditoria`
  (arquivos do Hermes, nunca enviados): tirado com `filter-branch` só nesse
  trecho; original em `ARENA-unificado\backup\git\auditoria-antes-de-tirar-o-email-2026-10-11.bundle`.
  Hashes novos: e752b0b→08aaac7, 69cc361→1053f15, a5e4e7b→b2fdf44,
  6ae7fc2→5dc2363, ae58a21→cfdc66d, 1e6967a→0133c38, 8740aa2→f3a641a,
  60d8932→b2e45f8, b27fffd→7bd973b. (Ele JÁ está público nos arquivos que o
  Hermes enviou ao GitHub — avisar o Rafael; tirar de lá exige envio forçado.)
- **Gmail no histórico:** decidido NÃO reescrever (já está público em 10
  commits do GitHub; reescrever mudaria ~450 hashes citados). Registrar.
- **Novo:** `ferramentas\conferir_antes_de_publicar.py` + teste (commit
  `68e5e2f`; bateria **298**): rodar antes de todo envio ao GitHub.
- **GitHub agora:** `main` = `c4f62dc` (o `main` aprovado, versão 2026.10.03.2,
  + junção "ours" que guarda os 10 commits do GitHub sem os arquivos);
  `auditoria` enviado (`68e5e2f`). Regra 24866071: sem envio forçado e sem
  apagar ramo (todos os ramos). `git config maintenance.auto` — o repack
  geométrico automático trava aqui (matei um preso às 00h45): desligar.

**Feito depois (11/10, até ~10h30; tudo enviado ao `auditoria` do GitHub):**
`dc30207` SINCRONIZAR confere antes de enviar; `9cb3f64` conferência: caminho
com acento, binário renomeado, avisos à mostra (revisão de segurança
automática); `bd3a590` **Fase 6 FECHADA** (F1: pasta que sobe um nível
passava na correção de caminhos — o `retroarch.cfg` dos alunos tem 7 linhas
em `...\ARENA\ARENA-alunos` que se consertam no 1º abrir depois do
`--atualizar`; F2 âncora; driver de vídeo; linha do PS2 da Fase 5: 37 de 37);
`a2314f1` README completo (desbloquear o .zip), capa sem desenho atrás do
texto, `TERCEIROS.md`, docs do Hermes removidos. Bateria **310**. O
`retroarch.cfg` de desenvolvimento foi corrigido (8 linhas no lugar antigo).

**Feito à tarde (11/10, 17h–17h30):** as revisões automáticas morreram 4×
no limite de uso → feitas à mão; `b68ea4b` **Fases 5 e 7 FECHADAS** (revisão
da Fase 5 sem defeito; Fase 7: o foco agora entra na janela que abre —
`ligarFocoDasJanelas`, acessibilidade 9 de 9 com prova negativa; passo a
passo das 5 pessoas conferido); `ad28dbd` **versão 2026.10.11** e guias
(1-COMECAR "O jeito fácil" pelo GitHub + Desbloquear; LEIA-ME). Esta
memória (o CLAUDE.md) passou a morar no repositório; a pasta de cima tem só
o apontador `@ARENA-unificado/CLAUDE.md` (a antiga em `backup\claude-md\`).
No GitHub há um **PR #1** (`auditoria` → `main`), aberto pela conta RafaParise
às 10h45 com um texto-modelo: usar para a junção, com a descrição de
verdade. Rodada completa da Fase 8 começada às 17h20
(`docs\auditoria3\rodada_depois.json`, gravada a cada script; se morrer:
`rodada_final.py --saida=docs/auditoria3/rodada_depois.json --continuar`).

**Falta (nesta ordem):** terminar a rodada completa; `testes\linha_base.py` e
`testes\medir_gravacoes_parado.py` (1 h) para a tabela Depois; seção da
Fase 8 no relatório (Depois × Antes, removidos, corrigidos, o que falta,
roteiros); `auditoria`→`main` pelo PR #1 (descrição de verdade) e push;
`--atualizar --destino ..\ARENA`; Release (montador `--destino <temp>` sem
`--com-bios`, conferir, zip < 2 GB, `gh release create v2026.10.11`);
tópicos e página do repositório; avisar o Rafael da "Social preview" (só
pelo site). A seção "Duas versões nesta pasta", mais abaixo, ficou velha:
as duas versões originais não estão mais no disco (perguntar ao Rafael).

**AUDITORIA 3 — EM ANDAMENTO (começada em 07/10/2026), ramo `auditoria`.**
O pedido do Rafael ("AUDITORIA COMPLETA DO ARENA: TESTES, LIMPEZA E
OTIMIZAÇÃO", fases 0 a 8, 10 regras) está salvo SEM RESUMIR em
`ARENA-unificado\docs\PLANO-AUDITORIA.md`, seção "Auditoria 3", com as
autorizações de 07/10: "permissão total de responder toda e qualquer
requisição desse script com base no que foi feito no ARENA e no que é melhor
e recomendado" e, depois, "autonomia de administrador para tomar as melhores
decisões [...] sempre continuando quando o limite acabar". **Leitura:** as
paradas para aprovação viram REGISTRO no relatório, com a escolha recomendada
e o porquê (como na auditoria 2); as 10 regras continuam valendo (nada
removido sem a prova na lista, nada de dado do aluno apagado, número antes e
depois). Relatório desta rodada: `docs\RELATORIO-QUALIDADE.md` (o da
auditoria 1 virou `docs\RELATORIO-AUDITORIA-1.md`); números brutos em
`docs\auditoria3\`. **Depois de um /clear: ler os dois arquivos antes de
continuar.**

- **Fase 0** (linha de base e inventário): números e inventário na seção
  "Antes" do relatório. Ferramentas ampliadas: `testes\linha_base.py` (a
  tela de verdade numa janela de aplicativo com perfil temporário, portas
  UDP, a ordem do ARENA de verdade), `testes\inventario.py` (mapa da tela:
  cada botão e a rota que usa; temporizadores; linhas de execução),
  `testes\medir_gravacoes_parado.py` (1 hora, com a tela, a pasta inteira),
  `ferramentas\rodada_final.py` (`--saida` grava depois de CADA script e
  `--continuar` retoma — a rodada já morreu 2× por falta de memória) e
  `testes\varredura_auditoria3.py` (a varredura da Fase 1).
  `testes\tela_sem_janela.Navegador(janela=True)` abre a tela COM janela.
- **Antes:** abertura até a tela pronta 2,61 s (servidor 0,58 + **1,0 s de
  espera fixa** + Edge 0,52 + página 0,51); servidor parado 0,05% de um
  núcleo, 42 MB; **a tela parada 9,7% de um núcleo** (fundo "Sempre" a 60
  quadros/s); TCP 127.0.0.1:8777; **UDP 0.0.0.0:55436 na rede toda mesmo com
  a rede desligada**; bateria 203.
- **Achado que já fez estrago:** toda abertura faz uma cópia em `backup\`
  20 s depois (o vigia começa com `internet_estava_fora: True` e a primeira
  checagem conta como "a internet voltou"); com o rodízio de 3, as aberturas
  das medições de 07/10 tiraram as cópias de 05/10 (os dados de verdade
  estão inteiros em `dados\`). Conserto na Fase 1.
- **A versão dos alunos ficou fora do lugar e VOLTOU (07/10/2026, pedido do
  Rafael: "Foi eu sim [...] por favor arrume como estava").** Ele tinha
  renomeado `..\ARENA-alunos` para `..\ARENA` (03/10) e tirado os jogos
  para uma `..\ARENA-alunos\jogos` nova (06–07/10). Voltou com
  `voltar_versao_alunos.py` (rascunho da conversa): os 103 arquivos de jogo
  (3.957.916.092 bytes) de volta em `jogos\pessoais`, conferidos um a um
  (tamanho e data), nenhum conflito, e o nome `ARENA-alunos` de novo (9.341
  arquivos). Continua valendo: é DELE, nunca remontar; levar conserto só
  com `--atualizar`.
- **Pedido do GitHub (07/10), para DEPOIS da auditoria:** gerar o programa
  limpo (como a versão dos alunos, sem ROM e sem BIOS — BIOS e firmware são
  da Sony, da Sega, da SNK... e não podem ir), criar um repositório público
  com todos os campos preenchidos e o ARENA pronto para baixar; e o
  repositório vira a cópia central, para o Rafael trabalhar daqui e da nuvem
  (puxar no começo da sessão, enviar no fim; o `CLAUDE.md` vai para dentro
  do repositório). O `gh` não está instalado aqui; a conta do GitHub está
  logada no Edge.

- **RETOMAR DAQUI (08/10/2026, ~01h50).** Pedido do Rafael de 07/10 à
  noite: "continue quando o limite retornar e finalize a auditoria sozinho,
  já rodou todos os jogos no último teste, depois o github com o ARENA
  completo para download, bem explicado e na página do github do arena com a
  imagem do fundo do modo escuro do ARENA para personalizar, não deixe de
  preencher nenhum campo no git hub [...] eu poder trabalhar pelo computador
  e github ao mesmo tempo e vice versa, eu acho que conectei o github no
  claude de todas as formas". **Fase 0 commitada** (`3086334`; rodada de
  referência 87 de 92, as 5 falhas analisadas no relatório). **Fase 1
  commitada** (`a0f464c`: C1–C7, R1–R5, bateria 232, 20 de 20 na área) +
  endurecimento da descoberta (`9874003`, duas revisões de segurança).
  **Fase 2 commitada** (`b0f55bd`: abertura 2,57→1,63 s; 8.264→72 KB por
  abertura; cópia só quando muda; fundos 20 quadros/s por relógio 7,7→5,0%;
  bateria 246) + guias (`3505272`). **Fase 3 (servidor e API) em
  andamento**: `fase3_mensagens.py` e `test_mensagens_de_erro.py` prontos
  (conversa `ddb7a96c...`, copiados para a `1feed006...`); falta o teste de
  internet ruim (portal do Wi-Fi, DNS, lento) para Internet Archive, capas e
  acervo (a busca do Internet Archive devolve "nenhum resultado" quando a
  rede falha e pode prender ~10 min numa rede lenta; a capa que não vem por
  falha da rede aparece como "Não achei capa") e o teste "a tela responde
  durante a indexação de 5.000 jogos". Prontos para o GitHub, sem commit:
  `README.md`, `ferramentas\imagem_do_github.py`, `ferramentas\lista_de_terceiros.py`;
  texto da GPL-3.0 baixado e conferido no rascunho (`baixados_licenca`). O GitHub: `gh` não
  instalado; git 2.55 + Git Credential Manager 2.9.1 sem conta guardada; o
  conector do GitHub do Claude não conectou nesta sessão ("Incompatible auth
  server"). Plano em `github_plano.md` (conversa `ddb7a96c...`).

**SESSÃO DE 03/10/2026 (manhã e tarde) — BIOS e posicionamento dos jogos.
TERMINADA. Versão: 2026.10.03.2.** Bateria `servidor\tests\run.py`: 203.
Pedidos do Rafael (autorizou configurar, posicionar e renomear): (a) "todas
as novas BIOS requisitadas estão nas pastas [...] faça as configurações
necessárias [...] garanta que o ARENA saiba explicar"; (b) "faça o ARENA
criar pastas de todas as BIOS [...] PS2 BIOS e dentro da pasta PS2 - PS2 USA
BIOS [...] verifique quais bios faltam"; (c) "A parte de emuladores do ARENA
deve conversar com essas pastas [...] constar ativa assim como é feito nos
emuladores como pcsx2 [...] O ARENA deve saber como cada jogo deve ser
posicionado, por exemplo o Killer Instinct [...] criar essas subpastas".
Veio também uma mensagem "3" sem pergunta pendente (perguntado no fim).

1. **Pasta `BIOS\`** (`ce05805`, `346d45d`, `9def005`):
   `servidor\bios_catalogo.py` (45 BIOS de 26 consoles, nomes das listas
   firmware dos .info; nível precisa / só para alguns jogos / opcional;
   PS1 e PS2: basta uma, região lida de dentro — no PS2 pelo ROMVER, como o
   PCSX2 mostra) + `servidor\bios.py` `organizar()` (ao abrir, em 2º plano,
   e no botão Conferir): cria `BIOS\<console>\<região>` (o mesmo nome da
   pasta de jogos) com LEIA.txt e `BIOS\LEIA - O QUE FALTA.txt`; reconhece
   pela marca MD5 dos .info, pelo conteúdo (PS1, PS2, neogeo.zip), pelo nome
   exato (sem marca conhecida) ou pelo tamanho na prateleira certa ("outra
   versão"); instala em `retroarch\system` com o nome exato (até zip dentro
   de zip); nunca troca (só a de outra versão pela recomendada; a antiga em
   `backup\bios-trocadas`); copia de volta para a prateleira uma vez (quem
   apaga não vê voltar; pasta BIOS recém-criada copia de novo); neogeo.zip
   também em `jogos\pessoais\Arcade`; BIOS deixada na pasta de jogos não
   aparece como jogo. Memória: `dados\bios_conferidas.json`. Na tela:
   Ajustes → Emuladores → **BIOS dos consoles** (Ativa / Falta / Outra
   versão por console; PS2 com versão e "é com esta que o PCSX2 liga";
   Conferir; Abrir a pasta). Rotas `/api/bios`, `/api/bios/conferir`,
   `/api/bios/pasta` (locais). Satellaview pelo cabeçalho, como o Snes9x
   (`bsx.cpp`, `is_bsx`): o **BS F-Zero Deluxe abre sem o BS-X** (testado)
   e não pede mais a BIOS. 3DO: a escolha só oferece BIOS de 3DO.
2. **Aplicado nas duas pastas:** `segamegacdbios.zip`, `segasaturnbios.zip`
   e `dc_boot.zip` saíram de `retroarch\system` para `BIOS\Sega CD`,
   `BIOS\Sega Saturn` e `BIOS\Dreamcast`; o BS-X em inglês (`BS-X BIOS
   (English) [No DRM] [2016 v1.3].sfc`) para `BIOS\Super Nintendo
   (Satellaview)` (na de desenvolvimento, uma cópia). Instaladas:
   bios_CD_U/E/J, mpr-17933, sega_101, dc\dc_boot e BS-X.bin. **13 BIOS
   ativas em cada pasta.** Ficaram em `retroarch\system` (não são BIOS):
   `ni-n-sat.zip` (321 jogos de Satellaview, 128 MB) e, na dos alunos,
   `bsxpage_new2.bin` (dados do satélite).
3. **Testado abrindo jogo** (`testes\teste_bios_consoles.py` 19/19): Sonic
   CD (Europa) → SEGA; Saturn Bomberman → SEGA e a abertura; Marvel vs.
   Capcom 1 → CAPCOM; BS F-ZERO e GP2 → a tela do BS-X (chegar do BS-X ao
   jogo NÃO foi testado: tecla simulada não chega ao RetroArch); Deluxe sem
   BS-X abre. `teste_bios_organizador.py` 23/23 (servidor e tela de verdade).
4. **Botão "Arrumar"** (`5c4fc6d`): `servidor\arrumar.py`, só no clique,
   nunca apaga nem passa por cima: zip dentro da pasta do disco (o kinst),
   disco solto, disco em pasta com outro nome, disco dentro de outro zip,
   neogeo.mame.zip → neogeo.zip, cópia do neogeo.zip para jogo de Neo Geo no
   MAME, zip com pasta dentro (original em `backup\originais`) e **jogo de
   CD dentro de .zip → descompacta em 2º plano** (andamento na tela, espaço
   conferido antes; o zip fica e sai da lista; o Jogar recusa explicando).
   Quando o MAME diz que falta o disco, o ARENA cria a pasta dele com um
   LEIA. Rotas `/api/jogo/arrumar`, `/api/arrumar/progresso`. Achados
   corrigidos: o .chd solto dizia "falta o arcade.zip"; a pasta de um jogo
   de PS1 descompactado ao lado do zip sumia da lista. `teste_arrumar_jogos.py`
   18/18 (Killer Instinct de verdade: botão na tela, clique, MAME abre).
5. Montador: `BIOS` é de quem usou; `--com-bios` leva as do catálogo; a
   folha de rosto explica a pasta BIOS. ARENA-alunos atualizada
   (`--atualizar`): 15 trocados, 294 arquivos dele intocados, 2026.10.03.2.
   Fuzz das rotas: 279 checagens, 0 falhas.

**Para o Rafael (substitui TODAS as listas de baixo):**
1. **BIOS que faltam** — ponha cada uma na pasta `BIOS\<console>` e clique
   em Conferir (a lista também está em `BIOS\LEIA - O QUE FALTA.txt` e na
   tela). Os jogos precisam: PC-FX `pcfx.rom`; 3DO `panafz10.bin`; CD-i
   `cdimono1.zip`; Odyssey 2 `o2rom.bin`; ColecoVision `colecovision.rom`;
   Intellivision `exec.bin` e `grom.bin`; MSX as pastas `Machines` e
   `Databases` do blueMSX; Amiga `kick34005.A500`. Só para alguns jogos:
   Sufami Turbo `STBIOS.bin`; Famicom Disk System `disksys.rom`; PC Engine
   CD `syscard3.pce`; 64DD `IPL.n64`; Videopac+ `g7400.bin`; Amiga 1200
   `kick40068.A1200`; CD32 `kick40060.CD32` e `.ext`; os cartuchos do Saturn
   (KOF 95 `mpr-18811-mx.ic1`, Ultraman `mpr-19367-mx.ic1`). Opcionais:
   `5200.rom`, `7800 BIOS (U).rom`, `lynxboot.img`, `gba_bios.bin`,
   `gb_bios.bin`, `gbc_bios.bin`, `bios7.bin`/`bios9.bin`/`firmware.bin`
   (DS), `bios.min`.
2. Satellaview: abrir um BS F-ZERO e ver se, pela tela do BS-X, dá para
   chegar ao jogo.
3. `mslugx.zip` (só uma cópia boa resolve); com os controles na mão: Crash
   Nitro Kart com 3 e 4 (teclado no jogador 4); no notebook: PS2 (se
   piscar, DirectX 11), God of War (PSP), COLETAR na tomada, Jogar Junto
   em 2 computadores.
4. A mensagem "3" de 03/10: perguntar a que se refere.

**SESSÃO DE 03/10/2026 (madrugada) — "faça por favor eu autorizo, e por
favor tudo que ficou pendente eu te autorizo a terminar e tomar as decisões
mais recomendadas" (Rafael, 02/10 ~21h30). TERMINADA. Versão: 2026.10.03.**
Bateria `servidor\tests\run.py`: 158. A conversa cortada às 17h55 tinha
sido retomada por OUTRA conversa às 21h (os 3 pedidos já estavam feitos);
nesta, a lista "Para o Rafael" virou trabalho:

1. **Renomeações autorizadas (21h25):** `ARENA-alunos\...\Arcade\neogeo.mame.zip`
   → `neogeo.zip`; na de desenvolvimento, o mesmo + `The King Of Fighters
   2002.zip` → `kof2002.zip` + `Arcade\kinst\kinst.zip` → `Arcade\kinst.zip`.
2. **KOF 2002 RODA** (`7d1cf49`): o zip era o conjunto DECRIPTADO de
   emulador antigo (`kof2k2_*.rom`; Kawaks/Nebula). O FBNeo tem o "Fully
   Decrypted" (`kof2k2fd`) com as mesmas partes: 13 iguais pela marca (o
   som 4 × 4 MB junta 2 a 2), menos o M1 (`ab9d360e`, outra versão: não é
   o oficial pelo CMC50 nem decriptado com chave errada — as 65.536
   testadas; o FBNeo usa essa versão no `kof2k2omg`). O M1 vai na pasta de
   correções do FBNeo (`retroarch\system\fbneo\patched\kof2k2fd.zip`,
   opção "Allow patched romsets", ligada). `ferramentas\converter_fliperama_decriptado.py`
   (partes pela marca, confere antes de gravar, original em
   `backup\originais`), rodada nas DUAS pastas → `Neo Geo\kof2k2fd.zip`.
   Visto: demonstração e tela de título, cores certas.
   `nomes_arcade.NOMES_FORA_DO_BANCO` (o banco do RetroArch não tem o
   kof2k2fd). `teste_kof2002_convertido` 7/7, `test_converter_fliperama`.
3. **Rodízio do backup** (`d35a8f9`): só giram as pastas com nome de data
   (contava qualquer pasta: `backup\originais` tomaria a vaga de uma cópia).
4. **Capas** (`7d1cf49`, `7aba40c`): entre capas do mesmo jogo, a do
   original ganha da do bootleg/hack; quando nenhum nome acha, o jogo pela
   MARCA (CRC) no `.rdb` do RetroArch (o BS F-ZERO é o "F-Zero (Japan)
   (7-10)"). Busca rodada nas duas pastas: **129 de 129 e 53 de 53**. A
   versão dos alunos não leva os `.rdb` de console (~50 MB): lá vale o nome.
5. **Crash Bandicoot 3** (SCES-01420, PS1) estava na pasta PS2 da de
   desenvolvimento, onde o PCSX2 não abre → pasta PS1 (abre até o menu).
6. **Registros de teste no banco** (o da de desenvolvimento): 24 apagados
   (2 recordes "Ana"/"Bruno", 22 sessões "hospedeiro"/"teste"); as 4
   sessões "aluno" FICARAM (podem ser do roteiro de conta de aluno); cópia
   em `backup\arena.db.antes-de-limpar-testes-20261003-015454`. O banco da
   ARENA-alunos não tinha nenhum (só "RafaParise").
7. **PS2, motor de vídeo:** fica no Automático — o PCSX2 escolhe DirectX 12
   em Intel de nível 12_0 por decisão dos desenvolvedores (conferido no
   código dele); o piscar do Celeron bate com o conserto da 2026.10.02.2;
   DirectX 11 a um clique (guia 3).
8. Montador: `retroarch\system\fbneo\patched` é de quem usou (`f051d17`).
   ARENA-alunos atualizada (`--atualizar`) para a 2026.10.03; os dados
   dele intocados (226 arquivos, contando as capas novas).
9. **Rodada completa** (`ferramentas\rodada_final.py`): INTERROMPIDA pelo Claude Code por falta de memória do sistema (como em 02/10), no teste_abrir_todos, depois de 5 de 5 OK (bateria, fuzz_rotas, textos_sem_acento, teste_aceite_pasta_movida, teste_abaixo_do_original). NÃO repetida: o Claude Code manda só repetir com o pedido do Rafael. O que mudou hoje passou nos testes da área (bateria 158, teste_kof2002_convertido 7/7, teste_backup_rodizio 10/10, teste_atualizar_versao_alunos 15/15, teste_capas_todos_os_consoles 21/21, teste_fliperama_nomes 35/35, VERIFICAR --so-ver). O corte não estragou nada: retroarch.cfg igual à cópia do protege_cfg, PCSX2.ini e dados\ intocados, nenhum emulador aberto; 7 pastas de teste esquecidas no Temp (~60 MB) apagadas. Notado, não feito: a conferência do --atualizar às vezes deixa uma pasta vazia arena_atualizacao_* no Temp.

**Para o Rafael (substitui TODAS as listas de baixo):**
1. `mslugx.zip`: as duas cópias (desenvolvimento e alunos) são o MESMO
   arquivo, com a parte `MSX_C3.rom` estragada, e não existe cópia boa no
   projeto. Só uma cópia nova resolve.
2. BIOS que não existem no projeto: Sega CD, Saturn, Dreamcast e
   Satellaview (BS-X; sem ela os 5 BS F-ZERO não abrem).
3. Com os controles na mão: Crash Nitro Kart com 3 e 4 (com 3 GameSir o
   teclado tem que ser o jogador 4 — às 2h não havia controle ligado aqui) e
   o desenho a 3 jogadores.
4. No notebook dele: PS2 (se piscar, DirectX 11), God of War (PSP), COLETAR
   na tomada, Jogar Junto em 2 computadores.
5. Na ARENA-alunos ficou uma "Nova pasta" VAZIA em `jogos\pessoais\Arcade`
   (criada por ele às 21h34; não atrapalha — deixada).

**SESSÃO DE 02/10/2026, NOITE — 3 pedidos novos do Rafael (17h09), feitos,
testados e commitados (um commit por item). Versão: 2026.10.02.3.**
Bateria `servidor\tests\run.py`: 147 (cada commit conferido sozinho numa
cópia limpa, `git worktree`). A conversa bateu no limite de uso às 17h55
com o código pronto e SEM commit; retomada às 21h a partir do registro da
conversa (`~\.claude\projects\<pasta>\<id>.jsonl`). Pedido: "O buscar capas
funciona muito bem mas não funciona exatamente com todas as capas. O crash
nitro kart não reconhece mais de 2 controles [...] e já ativei o multitap.
o ARENA não reconhece o motivo do kof2002 não roda porque para o ARENA está
tudo certo mas não roda".

**A `..\ARENA-alunos` AGORA É DO RAFAEL (3,7 GB de jogos dele,
configuração, recordes, saves): NUNCA remontar.** A montagem recusa pasta
em uso. Para levar conserto: `ferramentas\montar_versao_alunos.py
--atualizar` (troca só o programa e confere que nada dele mudou). Feito
nesta sessão: 11 arquivos trocados, 147 dele intocados, servidor na
2026.10.02.3.

1. **KOF 2002 "não roda e para o ARENA está tudo certo"** (`c971a24`): o
   MAME escrevia no registro o que faltava e a tela ficava calada (o
   RetroArch só mostra "Falha ao carregar o conteúdo"). Causas: o
   `kof2002.zip` dele é de outro emulador (`kof2k2_c1.rom`...) e a BIOS
   está como `neogeo.mame.zip` (o MAME só procura `neogeo.zip`, e SÓ na
   pasta do jogo — o guia 2 dizia `retroarch\system`: errado, corrigido).
   Novo `servidor\motivo_do_erro.py`: lê o registro DESTA partida e explica
   (no alto da tela ao voltar do jogo e no painel, "Da última vez: ...";
   `dados\problemas_dos_jogos.json`). O cartão avisa antes de abrir: BIOS
   com outro nome, Neo Geo no MAME sem `neogeo.zip`, `kinst.zip` dentro da
   pasta `kinst` (assim o MAME não abre). Montador leva a BIOS sempre como
   `neogeo.zip`. `teste_motivo_fliperama.py` (MAME e FBNeo de verdade) 8/8.
2. **Capas que faltavam** (`60af7b3`): 11 de 130 na pasta de
   desenvolvimento. Número do disquete no nome, GameBase (nome cortado em 8
   letras → `VERSION.NFO`), `&` gravado como `_`, palavras na ordem, tela
   de título para quem não tem caixa (Satellaview), PS1 na pasta do PS2
   (banco do PS1 + recado). 9 das 10 achadas (fica o BS F-ZERO).
   `test_capas_que_faltavam.py`.
3. **Crash Nitro Kart só com 2 controles** (`a2fe019`): o 4 estava SÓ no
   `dados\jogadores.txt` da pasta de desenvolvimento (dado de usuário, não
   vai na versão); na dos alunos o jogo ficava com 2 e o ARENA desligava o
   multitap do PCSX2 a cada abertura. Agora `consoles.json →
   jogadores_por_jogo` (os jogos conferidos, com o programa) vale para jogo
   fora do arquivo; o professor continua mandando. A tela dizia "escolha o
   modo de 2, 3 ou 2 jogadores". `test_jogadores.py`,
   `teste_tela_motivo.py` 11/11.
4. **Montador com trava e `--atualizar`** (`9c53eb5`):
   `teste_atualizar_versao_alunos.py` 15/15 (numa ARENA-alunos de mentira).

**Para o Rafael (SUBSTITUÍDA pela lista de 03/10, acima):**
1. `ARENA-alunos\jogos\pessoais\Arcade`: renomear `neogeo.mame.zip` →
   `neogeo.zip` (o cartão vai pedir) e trocar o `kof2002.zip` por um feito
   para o MAME 0.289 do ARENA (o dele é de outro emulador; o FBNeo também
   recusa).
2. Pasta de desenvolvimento, `jogos\pessoais\Arcade`: o mesmo, mais `The
   King Of Fighters 2002.zip` → `kof2002.zip` e o `kinst.zip` para FORA da
   pasta `kinst` (hoje está dentro, junto do `.chd`).
3. Na ARENA-alunos: Crash Nitro Kart com 3 e 4 controles (agora 4; e o
   desenho a 3 jogadores, item 2 da tarde) e "Buscar capas que faltam" de
   novo.
4. Trocar o `mslugx.zip` (danificado).
5. Registros de teste no banco: `ferramentas\limpar_registros_de_teste.py`
   (`--apagar`).
6. No notebook dele: PS2 DX11 × DX12, God of War (PSP), COLETAR na tomada.
7. BIOS que não existem aqui: Sega CD, Saturn, Dreamcast, Satellaview.
8. Com os 3 GameSir ligados, conferir o teclado no jogador 4.

**SESSÃO DE 02/10/2026, TARDE — 6 pedidos novos do Rafael, todos feitos e
commitados (um commit por item, cada um com teste). Versão: 2026.10.02.2.**
Bateria `servidor\tests\run.py`: 117. Versão dos alunos REMONTADA
(`..\ARENA-alunos`, 1,54 GB, com todas as BIOS, conferida).

1. **Servidor que "parava sem motivo"** (`4537814`): o registro de aplicativos
   do Windows mostrou o Python do ARENA caindo 2× em 26/09 (0xC0000005 no
   ntdll.dll), com ele jogando e sem teste rodando. Suspeita principal: a
   contagem antiga de controles (joyGetPosEx), já trocada no `a58910a` (não
   reproduziu em 12 mil contagens com 8 linhas). Proteções novas:
   `servidor\janela_preta.py` (faulthandler grava a linha da queda em
   `dados\logs\queda-do-servidor.txt`; Edição Rápida desligada — clique na
   janela preta do Windows 10 travava o servidor, REPRODUZIDO; recados da
   janela por fila; sem janela "parou de funcionar"), `ARENA.bat` reabre o
   servidor que caiu (até 3×, `ARENA_REABERTO` sem abrir outra janela), a
   tela mostra "parou de responder" e recarrega sozinha. VERIFICAR não
   conferia 5 módulos (agora a bateria confere a lista contra os imports).
   `testes\teste_servidor_que_cai.py` 17/17.
2. **Crash Nitro Kart a 3: mapa com lixo e "P1" em blocos** (`a296174`): o
   jogo é "perfeito" no banco do PCSX2 com o padrão; o registro do PCSX2
   avisava mipmapping e trilinear desligados (mudados na tela do PCSX2), e o
   "Mais leve" do ARENA punha a pré-carga de texturas em "Nenhuma" (o PCSX2
   diz que deixa MAIS LENTO). Agora sempre `hw_mipmap=true`, `TriFilter=-1`,
   `filter=2`, `HWDownloadMode=0`, `texture_preloading=2`, mistura ≥ básica.
   No PCSX2 de verdade: automático = 0 avisos; Vulkan (escolha do Rafael na
   tela do ARENA) só o aviso do motor. `teste_pcsx2_seguro.py` 22/22.
   **FALTA o Rafael confirmar a 3 jogadores** (e, se persistir, testar o
   motor Automático / DirectX 11 em vez do Vulkan).
3. **Modos abaixo do gráfico original** (`d3b78de`): Ajustes → Máquina →
   "Nível do gráfico": Normal / Igual ao original / Abaixo: leve / Abaixo:
   mínimo (bonecos de papelão). Chave `abaixo_do_original`. Dreamcast
   320×240, PSP/N64/2D pulam quadros, PS2 com EE a 75%/60%, Dolphin com CPU
   a 80%/60%, PS3 a 50%/25% (valores conferidos no código-fonte de cada
   núcleo/emulador). Achado: chaves da tela 4K grudavam no arquivo como
   "do aluno" (N64 seguia em 2x). `teste_abaixo_do_original.py` 31/31 +
   RetroArch e PCSX2 de verdade.
4. **Biblioteca: "Mario" trazia coisa aleatória** (`b728f76`): buscava na
   descrição; agora só no título, com todas as palavras. E o jogo baixado ia
   para `livres\Internet Archive`, onde o .zip de DOS virava "Precisa
   escolher o console" — agora `livres\MS-DOS`. A tela explica que só há
   MS-DOS livre e que Mario/Sonic/Pokémon não são livres.
   `teste_biblioteca_busca.py` 11/11.
5. **Capas para os consoles sem** (`21b2aec`): 49 consoles (131 bancos do
   libretro-thumbnails), pela lista oficial de cada banco (nome parecido,
   região certa); `servidor\capas_do_disco.py`: ícone do PS3/PSP de dentro
   do .iso (sem internet), Title ID do Xbox 360 → capa oficial da Microsoft,
   código de GameCube/Wii → GameTDB; Cover.jpg da pasta de um jogo sozinho.
   Botão "Buscar capas que faltam". Nos jogos da pasta: 68 de 78 sem capa
   acharam (PS2 37/38, PS3 6/6, Xbox 360 2/2). `teste_capas_todos_os_consoles.py`
   21/21. **O Rafael ainda não clicou** (as capas reais não foram baixadas).
6. **Como colocar jogos** (`c59ffa1`): `servidor\como_colocar.py` + botão na
   barra da esquerda (pasta, "Abrir a pasta", formatos, .zip pode/não/tem
   que ser, BIOS com "já está/falta", exemplo) + tabela dos 52 consoles no
   `2-JOGOS.md`. Zip de cartucho CONFERIDO (SNES zipado abre).
   `teste_como_colocar.py` 18/18.

7. **Fundos animados** (`0341011`, pedido depois dos 6): no céu, as
   "borboletas brilhantes" viraram **Metroides** (Metroid, NES), e entrou
   uma galáxia espiral; no campo, a joaninha ("só uma barrinha preta e
   vermelha") ganhou casco, pintas, pernas e voo, e o coelho pula com as
   pernas. Visitas de jogos famosos, uma de cada vez a cada 20–35 s — céu:
   as 4 máquinas do F-Zero numa pista de luz (~8 s para cruzar; a 1ª, ~7 s
   depois de abrir), Kirby na Warp Star, Space Invaders, Arwing; campo:
   Mario e Goomba, Sonic e o anel, Duck Hunt (patos + cachorro), Kirby.
   Sprites como texto em `launcher\pixel-sprites.js` (desenhos próprios, em
   homenagem). `teste_fundos_animados.py` 29/29 (cada visita vai embora
   sozinha; animado com visita: 0,6%/1,1% de um núcleo). Versão dos alunos
   remontada de novo.

**Para o Rafael (o de hoje cedo continua valendo + o novo; SUBSTITUÍDA pela
lista da noite, acima):**
1. Trocar o `mslugx.zip` (danificado).
2. Arcade: `The King Of Fighters 2002.zip` → `kof2002.zip`; `kinst.zip` ao
   lado da pasta `kinst`.
3. Registros de teste no banco: `ferramentas\limpar_registros_de_teste.py`
   (`--apagar`).
4. No notebook dele: PS2 DX11 × DX12, God of War (PSP), COLETAR na tomada.
5. BIOS que não existem aqui: Sega CD, Saturn, Dreamcast, Satellaview.
6. Com os 3 GameSir ligados, conferir o teclado no jogador 4 (contagem nova).
7. NOVO: Crash Nitro Kart a 3 jogadores (item 2 acima).
8. NOVO: clicar em "Buscar capas que faltam" (item 5).

**SESSÃO DE 01 E 02/10/2026 (tarde, noite, madrugada e manhã) — o mesmo
pedido (pendências, testes para quebrar, versão dos alunos) + as respostas
do Rafael de 02/10 (fliperama; tarefa 6 encerrada; versão COM todas as BIOS;
registros de teste do banco ele mesmo apaga). TERMINADA. Versão: 2026.10.02.**
Bateria `servidor\tests\run.py`: 115. Cada item abaixo com teste.

- **VERSÃO DOS ALUNOS PRONTA, COM TODAS AS BIOS:** `..\ARENA-alunos` (ao lado
  do ARENA-unificado), 1,54 GB, 49 núcleos, 51 de 53 consoles prontos
  (J2ME não tem núcleo nem aqui). BIOS de PS1, PS2 (+ a pasta de BIOS do
  PCSX2), firmware do PS3 instalado e `neogeo.zip`. Sem nada de quem montou.
  Conferida: o RetroArch DELA abre um jogo de PS1 pela BIOS dela, o PCSX2
  DELA liga o Crash Nitro Kart (BIOS achada na pasta dela), 0 erro de
  JavaScript em 1366×768 e 4K, VERIFICAR 13 certos. Montador:
  `ferramentas\montar_versao_alunos.py --com-bios`. **Desde 02/10 à noite a
  ARENA-alunos está EM USO pelo Rafael: NÃO remontar** (a montagem recusa);
  levar mudança com `--atualizar`, que troca só o programa.
- **Tarefa 7 RESOLVIDA** (`c76c2d5`): o Metal Slug X de fliperama tinha o
  **`mslugx.zip` danificado** — a parte `MSX_C3.rom` (gráfico dos
  personagens) não confere com o CRC do zip; o FBNeo carrega assim mesmo
  (personagens de cor estranha), o MAME recusa. Novo `servidor\integridade.py`:
  cada zip de fliperama conferido UMA vez, em segundo plano; o cartão e o
  "Abrindo..." avisam. "O arcade não é reconhecido": `The King Of Fighters
  2002.zip` (nome de título) — o cartão agora diz o nome certo (`kof2002.zip`,
  procurado no banco do RetroArch); `kinst.chd` sem `kinst.zip` também avisa.
- **Tarefas 3 e 4 FEITAS** (`4df9e61`): `ferramentas\modo_alvo.py` (o ARENA
  numa "caixa" do Windows com os limites do notebook-alvo, sem admin) e
  `testes\teste_orcamentos_modo_alvo.py` (também no `RODAR_TESTES.bat`):
  tabela medido × teto, reprova apontando o estouro. 1ª rodada reprovou a
  memória do servidor (64,4 MB, teto 64) — causa: índice de títulos de
  fliperama do mesmo dia (+13 MB); consertado: 43,9 MB. O SNES a 52 FPS não
  era o ARENA: era o headset sem fio deste PC segurando a sincronia pelo
  som (sem ela, 60,1); o COLETAR agora separa os dois. Final: nenhum
  orçamento estourado. Detalhe: `docs\MAQUINA-ALVO.md` seção 7.
- **Vazamento de alças do Windows no servidor** (`a58910a`): 181.570 em 3
  minutos de pedidos (24 por `/api/estado`, 48 por ajuste salvo). A
  contagem de controles (`joyGetPosEx`) rodava em toda chamada e vaza com o
  controle desligado. Agora conta só ao abrir o jogo, pelo Raw Input + XInput
  (0 alça por chamada). Depois: 47.782 pedidos em 3 min e +10 alças.
- Antes, na mesma sessão: endereço gigante recusado; jogo de vários discos
  num cartão (.m3u); rodízio das cópias de segurança (209 → 3); retroarch.cfg
  com `cache_directory` repetido; PS2 sem BIOS e Satellaview sem BS-X
  avisam no cartão; DCNet do Dreamcast desligado; degrau "tela 4K"; alarme
  falso de temporários (arquivo esparso do RPCS3); 2,9 GB de sobras de
  teste e 128 Edge invisíveis limpos; guias e LEIA.txt reescritos; fliperama
  grande vira índice; abertura da tela 67→14 pedidos; Vulkan só com placa de
  verdade; API à prova de corpo torto/conexão presa; dados\ tortos.
- **Rodadas:** a de 01/10 deu 69 de 75 (as 6 não eram defeito; consertadas e
  repetidas). A final de 02/10 foi **interrompida pelo Claude Code por falta
  de memória** no começo do teste do RPCS3, depois de 65 scripts (64 OK; o 1
  que falhou era o vazamento, consertado e repetido). Os leves que faltavam
  rodaram à parte e passaram. **NÃO repetido:** `teste_rpcs3_controles` (o
  pesado de memória; o código dele não mudou desde a rodada que passou).

**Para o Rafael (só o que depende dele):**
1. Trocar o `mslugx.zip` por uma cópia boa (o atual está danificado).
2. Pasta Arcade: renomear `The King Of Fighters 2002.zip` → `kof2002.zip`
   (pode ainda ser de outra versão do MAME: o emulador diz o que falta) e
   pôr o `kinst.zip` ao lado da pasta `kinst`.
3. Registros de teste no banco: ele mesmo apaga
   (`ferramentas\limpar_registros_de_teste.py`, `--apagar`).
4. No notebook dele (frente 6): PS2 Direct3D 11 × 12, PSP God of War com
   Gráfico original, COLETAR na tomada (recalibrar a referência 3.200.000).
5. BIOS que não existem nesta pasta (e por isso não foram na versão): Sega
   CD, Saturn, Dreamcast (o Marvel vs. Capcom 1 trava sem ela), Satellaview.
6. Com os 3 GameSir LIGADOS, abrir o Super Bomberman 4: o teclado tem que
   ser o jogador 4. A contagem nova (Raw Input + XInput, `a58910a`) só foi
   conferida aqui sem controle nenhum (0 → teclado no jogador 1).

**SESSÃO DE 01/10/2026 (madrugada) — pedido do Rafael: terminar as frentes,
seguir TODAS as pendências com configuração recomendada, testar tentando
quebrar, e no fim montar uma versão limpa para os alunos na pasta do
projeto. Ele deu permissão para eu decidir; só o estritamente necessário
fica para ele.** O trabalho voltou a ser no `main` (estava no ramo
`auditoria`, 51 commits à frente; avanço rápido, nada reescrito).
Feito e commitado (cada um com teste):
- Frente 5 COLETAR (`5b33f6b`): régua dos tetos aprovados (tabela medido/
  teto/PASSOU), abertura pelo próprio ARENA.bat medida sozinha (janela com
  título ARENA), curva do parado, velocidade de um núcleo + selo de cada
  console no retrato, perguntas sobre consoles testados (ARENA diz x você
  viu). `testes\teste_coletar_regua.py`.
- PowerShell dos adaptadores em laço quando falhava (`9463610`); teste de
  disco gravava 24 MB a cada abertura (`0c83acc`).
- Frente 6 sem o notebook (`2a76e57`): motor de vídeo do PS2 escolhível
  (auto do PCSX2 2.8 = DX12 em Intel); PSP com pulo de quadros automático
  no Gráfico original. FALTA no notebook dele: comparar DX11 × DX12.
- Filtro de tela NUNCA funcionava (`f1e6453`): RetroArch ignora
  video_shader do arquivo; agora `--set-shader`, só pixel nítido nos 2D.
- Tarefa 7 (`74c025e`): nomes de fliperama pelos .rdb do RetroArch, avisos
  na tela do jogo (CHD dentro de zip, pasta dentro do zip, disco na pasta
  errada — que NUNCA aparecia), identificador sem chute (19 PS2 viravam
  PS1). Metal Slug X com cor errada: resolvido em 02/10 (zip danificado).
- Ferramentas antigas apagavam dado real (`8afe472`): EU rodei a de capa e
  apaguei `retroarch\thumbnails`; re-baixei 50 de 69 com
  `ferramentas\baixar_capas.py`. Corrigidas as 3.
- Tarefa 8 (`fa68313`): causa = Windows em "melhor desempenho" → navegador
  pede menos movimento → fundo não desenhava NADA. Agora sempre aparece;
  Ajustes → Simples → Fundo animado (Automático/Sempre/Parado); mais leve;
  muito mais borboletas e animações nos dois temas.
- Tarefa 6 (`115e4bd`): gaveta Perfil (Meu perfil com apelido editável +
  Amigos); apelido limpo (aspas quebravam o arquivo do emulador); topo
  cabe em 1366×768.
- Ferramenta nova `testes\tela_sem_janela.py`: Edge sem janela por
  protocolo de depuração (fotos em qualquer resolução, inclusive 4K).
PERGUNTAS PARA O RAFAEL: respondidas em 02/10/2026 — fliperama; tarefa 6
fica como está; versão dos alunos com todas as BIOS (ver o bloco acima).

Última atualização anterior: 30/09/2026, noite (tarefas 5 e 1 feitas e revisadas; tarefa 2 proposta).

**ETAPA pedida pelo Rafael em 30/09/2026 — CONCLUÍDA em 02/10/2026.** Fica
só o que depende dele (tarefa 5 em 2 computadores, frente 6 no notebook
dele). O que segue é o histórico. O pedido "antes de tudo, escolher as
melhores configurações de plugins e habilidades do Claude Code" foi feito
em 30/09 (frontend-design, claude-md-management e security-guidance).

*Notebook mais fraco da escola (anotado à mão pelo Rafael):* Positivo
(luzes de Wi-Fi e de ligado verdes na tampa), **Intel Celeron N5100 @
1,10 GHz, 4 núcleos lógicos, 7,7 GB de RAM (3,8 livres)**, disco SD
"Generic A3V012". Pen drive = letra D (SSD KODAK X120 PRO 1 TB em
adaptador USB 3.0). Abrir o ARENA pelo pen drive: **8,55 s** até a tela
ficar pronta (sem aviso do Windows/antivírus/firewall — já tinha rodado
a versão do remake). Copiar a pasta para o disco: 27.224 arquivos, 2.548
pastas, 12,2 GB (sem jogos), **5 min 13 s**. Abrir pelo disco: **5,57 s**.
Coletas em `ARENA-unificado\perfil\` (códigos `59A30E147B` de 28/09 e
`D682F0CCEB` de 27/09; `012944B9B2` é o PC do Rafael).

**REDIRECIONAMENTO (30/09/2026, noite) — aprovado pelo Rafael:** a
máquina dos testes de jogo dele é um N5100 que ELE otimizou (sem bloatware,
serviços inúteis); o COLETAR rodou em notebooks COMUNS do mesmo modelo, com
Windows pesado. No otimizado: PS2 com 4 jogadores (Crash Nitro Kart, Marvel
Ultimate Alliance) sem travar, só gráficos piscando/distorcendo rápido;
Naruto Ultimate Ninja 4 muito bem, poucas travadas; God of War (PSP) bem,
abaixo de 60. Conclusão: quem manda é o estado do Windows, e a avaliação do
ARENA é imprecisa. **Tarefas 3 e 4 (modo alvo, teste que reprova) PAUSADAS**
(os 6 tetos continuam valendo). **Nova ordem aprovada:**
1. Dolphin externo: hoje NÃO recebe ajuste de imagem (só controles);
   `ShaderCompilationMode` padrão é Síncrono (trava a cada efeito novo) →
   compilação assíncrona + resolução pela placa / nativa no gráfico original.
2. Avaliação honesta: nota hoje conta núcleos (Celeron = Ryzen = 4; PS2/GC/
   Wii/PS3/Xbox custo 5 → "Capenga: vai travar" até no Ryzen; round(4,5)=4);
   medir AVX/AVX2 e velocidade real de um núcleo; requisito por console
   (Xbox 360 exige AVX; PS2 calibrado pelo teste do Rafael no N5100);
   etiquetas Roda bem / Roda com ajustes / Pode travar / Não abre (motivo);
   "como o Windows está hoje" à parte (barreiras).
3. Ultra: emulador fora da economia de energia do Windows (SetProcessInformation
   ProcessPowerThrottling, sem admin, não grava nada); prioridade de memória
   baixa do ARENA no jogo; teste que confere o que o ultra promete. **Modo de
   energia do Windows: NÃO mexer** (decisão do Rafael).
4. PCSX2 em placa integrada: 1x nativo + mistura "Básica" no automático e no
   gráfico original (**ajustar pela placa — decisão do Rafael**; o PCSX2.ini
   está com accurate_blending_unit = 5, "Máxima", escolhido na tela dele;
   placa dedicada/"Mais bonito" mantém).
5. COLETAR: tetos aprovados como régua; velocidade medida, AVX e "o que o
   ARENA diria de cada console"; perguntas sobre os consoles testados.
6. No notebook dele: PCSX2 D3D11 × D3D12 (auto escolhe D3D12 na Intel FL12 —
   candidato aos gráficos piscando), PSP God of War com pulo de quadros,
   calibrar a avaliação.
Depois: tarefas 6, 7, 8 (perfil, Metal Slug X, fundos animados).
**Progresso (30/09/2026, noite):** frente 1 FEITA (`5007d9e`, Dolphin: híbrido,
resolução pela placa, Dual Core fixado, ultra com anotação/devolução da tela
cheia; teste `testes\teste_dolphin_config.py`); frente 2 FEITA (`5bb3c97`,
`classificar_plataforma` + `hardware.velocidade_de_um_nucleo/instrucoes`;
referência do alvo PROVISÓRIA 3.200.000 op/s — recalibrar com o COLETAR do
Celeron; perfil gráfico continua na regra antiga de propósito); frente 3
FEITA (`6f54ddc`: a "prioridade alta" e o "ARENA abaixo do normal" NUNCA
funcionavam — 0x8000|0x80 vira acima do normal; SetPriorityClass sem tipos
cortava o handle; vigia ficava suspenso se o emulador não abria. Novo
`servidor\processos.py`; teste `testes\teste_ultra_promessas.py`); frente 4
FEITA (`95a08dc`, PCSX2 integrada: 1x + mistura Básica; teste
`testes\teste_pcsx2_placa.py`). Próxima: frente 5 (COLETAR).

*Tarefas pedidas (ordem dele):*
1. **FEITO (30/09/2026): retrato oficial em `ARENA-unificado\docs\MAQUINA-ALVO.md`.**
   Máquina `D682F0CCEB` = Celeron N5100 (4 núcleos, 1,1–2,8 GHz, 6 W,
   **sem AVX/AVX2**, PassMark 1.361 por núcleo = 43% do Ryzen), 7,7 GB em
   **canal simples**, UHD 24 EU (driver de 2021), tela 1366×768, C: eMMC
   com só 14,3 GB livres (ARENA roda do SSD USB). Proíbe: Xbox 360 (Xenia
   exige AVX — mensagem no próprio .exe), PS3 impraticável, PS2 abaixo do
   mínimo do PCSX2. **Achados:** o FPS do SNES NUNCA foi medido na escola
   (medidor pegava "BS F-ZERO", de Satellaview, que não abre → 4.140.000
   FPS "BOM"; corrigido no commit `95f783b`, falta recoletar lá, na
   tomada); `hardware.capacidade()` dá **nota 4/placa 3 ao Celeron, igual
   ao Ryzen** (conta núcleos, não velocidade; só cai para 3 com pen drive
   abaixo de 45 MB/s); modo econômico não liga
   nele; servidor parado a 8,4% de um núcleo (causa desconhecida).
   Pedido original: **Retrato oficial** — ler `perfil\` e escrever `docs\MAQUINA-ALVO.md`:
   o que o notebook é, o que não permite e o que isso proíbe no projeto
   (ex.: sem AVX → IA local não roda, máquina só cliente). Citar aqui no
   "Estado atual" + regra nova: **toda decisão de desempenho é julgada
   por essa máquina, não pelo Ryzen**.
2. **APROVADO pelo Rafael (30/09/2026, commit `18c3906`)** — `docs\MAQUINA-ALVO.md` seção 7: abertura sentida 10 s
   (Nielsen) e do servidor 2,3 s; memória 64 MB; parado 2% de um núcleo
   (exceção: 8,4% medido é suspeito — Celeron estoura 4×); indexação
   1,9 s/100 jogos; gravações ≤ 1 em 2 min e 16 KB/min; SNES ≥ 59,0 FPS
   e variação ≤ 5% (provisório). Regra: ×1,5 com 1 coleta, pior de 3 ×1,2.
   Investigação do parado: no Ryzen a tela custa ~0,07 s por abertura e
   o servidor assentado 0,05% — não explica o Celeron. Medidor agora
   espera assentar (`dba49f8`); `ferramentas\medir_parado.py` (novo)
   mostra a curva — rodar no Celeron. A tela faz 52 pedidos ao abrir
   (`/api/botoes` 3×, `/api/perfis-controle` 3×, `/api/mapeamento` 2×
   repetidos — candidato a enxugar).
   Pedido original: **Orçamentos** — teto para: tempo de abertura, memória do servidor,
   CPU parado, tempo de indexação, gravações em disco/min, FPS no SNES.
   Valor medido + folga, explicando cada folga. Em `MAQUINA-ALVO.md`.
3. **FEITO (02/10/2026, commit `4df9e61`).** **Modo alvo no PC dele** — `ferramentas\modo_alvo.py`: abre o ARENA
   limitado (2 núcleos, prioridade baixa, teto de memória), sem admin,
   confirmado na documentação oficial da Microsoft (afinidade/prioridade
   do próprio processo; Job Object para memória). Dizer no arquivo o que
   NÃO imita: disco lento, placa de vídeo fraca, falta de AVX.
4. **FEITO (02/10/2026, commit `4df9e61`; a frase da régua está em
   `docs\MAQUINA-ALVO.md`).** **Teste que reprova** — na bateria, roda com o modo alvo e falha
   apontando qual orçamento estourou; entra no `RODAR_TESTES.bat`.
   No fim: uma frase dizendo o que mudou na régua do projeto.
   Rotina depois: "Rode a bateria no modo alvo e me mostre a tabela de
   orçamentos: medido, teto e passou ou não. Se algo estourou, aponte a
   causa antes de propor conserto." No notebook da escola: repetir a
   coleta 1×/mês ou antes de cada versão nova.
5. **FEITO no código (commit `d2b356d`, 30/09/2026), FALTA o Rafael
   confirmar em 2 computadores.** Causas achadas: a tela filtrava por
   `partida_aberta`, que o servidor nunca mandou (nas 3 versões); depois
   de Sincronizar, `desenharAmigos` recebia só apelidos → todos "Fora do
   ar"; o grito UDP saía só pelo adaptador principal; "Só assistir"
   abria o jogo sozinho. Agora: `PARTIDA_ABERTA` no grito e no
   `/api/sinc/ola`, rota local `/api/partida/procurar` (UDP + TCP a cada
   amigo salvo), `gritar()` por adaptador, tela atualiza a cada 4 s.
   Teste `testes\teste_partida_aparece.py` 23/23; bateria 112.
   **Revisão (30/09, commit `1cc6d70`)** achou e corrigiu: junção por
   código de aparelho (clone sumia atrás do outro — agora só endereço),
   config inteira regravada 3 s depois (`gravar_enderecos_de_amigos`,
   também no vigia), 1ª partida marcada sozinha com 2+ abertas, lista
   redesenhada sem mudança. Visto no Chrome com `testesbrir_dois_arenas.py
   --duas` (3 ARENAs num PC). Lógica da tela: `node testes\teste_lista_partidas.js`.
   Pedido original: **BUG GRAVE — Jogar Junto parou de conectar.** Amigo adicionado
   (por código, por endereço, hotspot do celular ou do Windows, com ou
   sem internet) aparece "fora do ar", embora os recordes sincronizem.
   O jogador 2 não vê a partida hospedada pelo jogador 1 como opção;
   falha até em console leve e jogo que já funcionava. Suspeitas a
   conferir (não presumir): lista `ROTAS_REDE_EXTERNA`/`host_confiavel()`
   da auditoria, reabertura do servidor sem reiniciar (`TRAVA_REDE`),
   `quem_esta_online()`/`resolver_endereco_amigo()`.
6. **FEITO (01/10/2026, commit `115e4bd`); a frase cortada ficou sem
   resposta — encerrado como está (02/10).** **Perfil** — ter a aba de amigos (conexões entre servidores locais) e
   uma aba para mudar o apelido; "e cada perfil..." (frase veio cortada —
   perguntar o resto).
7. **RESOLVIDO (02/10/2026, commit `c76c2d5`: zip danificado e nome de
   título).** **Metal Slug X com cores erradas** (personagens com cor estranha) e
   "o arcade FBNeo ou MAME não é reconhecido".
8. **FEITO (01/10/2026, commit `fa68313`).** **Fundos animados não funcionam mais** (`launcher\field-background.js`
   e `launcher\galaxy-background.js`; ele citou sem o `launcher\`).
   Consertar e acrescentar mais borboletas e mais variações de animação
   nos dois temas (escuro e claro), no mesmo estilo pixel art.

*Sobras sem commit (25/09): RESOLVIDO em 02/10/2026* — a rodada nova foi gravada (`25513fc`); o Dreamcast "arquivo não encontrado" era o teste apontando para um jogo que mudou de nome.

**Auditoria 2 CONCLUÍDA e juntada ao `main` (25/09/2026, merge `5675df2`).**
Pedido do Rafael: refazer as Fases 0–8 com as mesmas decisões da primeira
+ o testador de máquinas e o ARENA identificarem o que deixa o computador
lento. Tudo em `ARENA-unificado\docs\RELATORIO-AUDITORIA-2.md` (o
`RELATORIO-AUDITORIA-1.md` fica como histórico). Ramo `auditoria` mantido.
Principais: **`servidor\barreiras.py`** (novo; usado pela tela em Ajustes →
Máquina, pelo item 11 do `VERIFICAR.bat` e pelo `COLETAR.bat`): memória,
programas fecháveis (botão Fechar, só lista segura), bloatware,
inicialização, serviços inúteis, telemetria, indexação, dois antivírus,
Game Bar gravando, plano de energia, memória virtual, driver de vídeo... —
cada item com ação e "quem faz" (aluno × professor/TI); rotas
`/api/barreiras` e `/api/barreiras/fechar` só locais; aviso rápido na hora
de jogar. Funciona com PowerShell em modo restrito (scripts sem
`[pscustomobject]`/`[math]`). **Achados corrigidos:** 28 chaves de núcleo
inexistentes no `graficos.json` (teste `teste_chaves_graficos.py` pega a
próxima); cache do PS1 (`vulkan_pipelines.bin`, 15–50 MB) regravado a cada
partida — somente leitura no modo econômico; rodízio de registros também
após cada jogo; VERIFICAR conferia 13 arquivos, agora 20; ~110 mensagens de
tela sem acento (`testes\textos_sem_acento.py`); teste de pasta movida
deixava 182 MB fora da pasta. **Removidos:** `/api/sinc/ranking`,
`registros_pendentes()`, 2 regras CSS. Bateria `servidor\tests\run.py`:
**71**. Rodada completa `ferramentas\rodada_final.py`: **42 de 42**. Rotas:
51 caminhos (8 abertas à rede). **Falta (sala):** Roteiros 9 (cache PS1 no
pen drive), 10 (conta de aluno de verdade: COLETAR + Verificar agora) e 11
(Jogar Junto Ryzen × Celeron) no relatório 2; decidir
`ppsspp_skip_buffer_effects` do modo modesto com os números do Celeron.

**Multitap, Fase E — teste com os controles na mão (25/09/2026), no `main`.**
Com 3 GameSir (G7 HE com cabo = XInput 0, T4 Nova Lite preto = 1, roxo = 2)
+ teclado, no Super Bomberman 4. **Dois achados reais, corrigidos e
confirmados pelo Rafael no jogo:** (1) **o RetroArch ignora
`input_libretro_device_pN` vindo do `--appendconfig`** — o jogo abria com
"SNES Joypad" na porta 2 e só 2 jogadores, mesmo com o arquivo da partida
pedindo o Multitap (a Fase D conferia o arquivo, não o que o RetroArch fez
com ele). Agora `arena.remapeamento_da_partida()` grava o tipo das portas
num `.rmp` só da partida (`dados\remap_partida\<Núcleo>\<jogo>.rmp`,
copiando o remapeamento do aluno se houver); com ele, 5 jogadores, cada
controle no boneco certo, sem mexer no menu. (2) **Botões trocados**: o
`retroarch.cfg` tinha números de controle DirectInput gravados para os
jogadores 1 e 2 (Start = 9, que no XInput é o R3) — passavam por cima do
reconhecimento automático. Limpo (`ferramentas\limpar_botoes_retroarch_cfg.py`,
cópia `retroarch.cfg.antes-limpeza-*`), e `controles.opcoes_do_retroarch()`
agora manda `nul` em todo botão/eixo de controle que o aluno não definiu
(jogadores 1–16; teclado continua somando). Ferramenta nova
`ferramentas\testar_controles.py`: mostra em qual número do XInput cada
controle entrou. Testes: bateria 93, multitap por console 11/11 (agora
confere o `.rmp`), regra de ouro OK. **Falta da Fase E:** Mega Bomberman,
Micro Machines 2, CTR e GoldenEye com os controles (Mega Bomberman já
aprovado: 4 jogadores, analógico e direcional juntos).
**Plano A→B→C aprovado pelo Rafael (25/09/2026):** (A) FEITO, commit
`eb10e76` — `joypad_autoconfig_dir` aponta para `retroarch\autoconfig`
(~380 perfis: Xbox, DualShock 3/4, DualSense, fliperamas, 8BitDo...);
GameSir casam com o perfil "Xbox 360 Wireless Controller" (mesmo formato).
(B) FEITO e confirmado no jogo — **o teclado é o primeiro jogador sem
controle** (`controles.contar_controles()` via winmm+XInput na hora de
abrir; 3 controles → teclado jogador 4; nenhum → jogador 1). Teclas fixas
em `controles.TECLADO_PADRAO` + o que o aluno mudou no jogador 1, porque o
RetroArch reescreve o `retroarch.cfg` ao fechar. **Achado no caminho,
corrigido:** a bateria (`TestControles`) gravava no `dados\controles.json`
DE VERDADE a cada rodada (trocava só a `RAIZ`; o `ARQUIVO` é calculado na
importação) — era a origem do "jogador 2, a = botão 0"; limpo com
autorização (cópia `controles.json.antes-limpeza`). (C) FEITO e confirmado
na tela — **raiz do "Start no R3" achada**: a tela gravava a numeração do
NAVEGADOR (Start 9, Select 8, gatilhos 6/7), que no XInput do RetroArch
são outros botões; o "Mapear meu controle sozinho" gravava isso sempre.
Agora: "Definir" traduz para XInput quando o navegador diz "xinput" ou
"xbox" (o Chrome atual chama os GameSir de "Xbox One Game Controller
(STANDARD GAMEPAD)", sem "XInput") — Start → 6, gatilhos → eixos +4/+5;
genérico sem padrão grava o número cru (= DirectInput); PS/Switch
reconhecidos pelo navegador: a tela avisa que não precisa. O botão virou
"Voltar ao reconhecimento automático" (apaga os botões de controle do
jogador, mantém o teclado). Tela e servidor com jogadores 1 a 5. Limite
do navegador (não do ARENA): o Chrome só enxergou 1 dos 3 GameSir; não
atrapalha, porque o "Definir" grava para o jogador escolhido na lista.
PS3/PS4/PS5 e fliperama não dá para testar aqui: roteiro de sala.
**Micro Machines 2 (J-Cart) aprovado com 4 jogadores** — mas só depois de
voltar "Tipo de controle" para XInput: durante o teste da tela alguém
trocou para DirectInput (`dados\config.json → avancado.input_joypad_driver`),
e no DirectInput cada GameSir aparece duplicado (7 "controles" para 3), o
que joga preto/roxo para as portas 5–7. O núcleo (Genesis Plus GX) liga as
portas em sequência — porta A, porta B, J-Cart 1, J-Cart 2 = jogadores 1–4
do RetroArch (conferido no código-fonte dele). **Melhoria FEITA (commit
`6384e56`, confirmada na tela):** a tela avisa que DirectInput duplica
controle tipo Xbox (aviso mais forte se o navegador vê um ligado); guia 3
diz para usar dinput só quando todos os controles são PS3/arcade/genérico.
**CTR (PS1, 4 jogadores) aprovado depois de achado GRAVE, corrigido:** o
texto/menus saíam em blocos coloridos. Causa: `hardware.placa_video()` lia
o registro e pegava a PRIMEIRA placa — nesta máquina uma "NVIDIA GeForce
210" que já saiu (sobra no registro); a tela está na Radeon integrada. O
ARENA achava "placa dedicada" → nota da placa 4 → PS1 em 6x (e todos os
consoles de `_usa_nota_gpu` na nota 4). Isolado por eliminação com fotos
automáticas (`testes\teste_imagem_ps1.py`, `--max-frames-ss`): só baixar a
resolução conserta (1x–4x certo; MSAA, PGXP, filtro, cor verdadeira e
leitura por software não). Agora `placa_da_tela_principal()`
(`EnumDisplayDevicesW`, sem admin) vem antes do registro: Radeon
integrada, nota da placa 3, PS1 em 4x, CTR certo. Teste na bateria. Ordem
dos controles sem fio pode trocar entre partidas (o Windows numera o
XInput pela ordem de conexão) — não é do ARENA.
**FASE E CONCLUÍDA (25/09/2026):** GoldenEye 007 com 4 também aprovado.
Os 5 jogos (SB4 5 jogadores, Mega Bomberman, Micro Machines 2, CTR,
GoldenEye) funcionaram com 3 GameSir + teclado, analógicos incluídos.
Resultado em `docs\MAPA-MULTITAP.md`. Falta só o que depende de arquivo
(Saturn e Dreamcast incompletos, BIOS do Neo Geo) e o roteiro de sala com 5
notebooks (`docs\ROTEIRO-MULTITAP.md`).

**Jogos novos do Rafael + Wii (25/09/2026, no `main`).** BIOS do Neo Geo
agora CERTA (`ferramentas\conferir_bios_neogeo.py`: sm1, sp-s3, sfix, 000-lo
com nome e CRC). **Catálogo** (commit `16cf868`): jogo de CD em trilhas
aparecia uma vez por trilha (Saturn Bomberman 31×, Dreamcast 28 para 6) —
agora só o `.cue/.gdi`, um formato por jogo (prefere `.chd`), título pela
pasta quando o arquivo é "disc"/"track", `neogeo*.zip` escondido (114 → 62
jogos). `dados\jogadores.txt` atualizado com autorização (cópia `.antes-*`).
**Dolphin** (commits `262bd6b`, `54c05b2`): estava sem `portable.txt`
(gravaria em Documentos) e sem controle nenhum — agora portátil, 4
jogadores XInput + teclado no 1º livre; Wii = Wii Remote + Nunchuk; **só um
tipo por jogo** (com os dois, o Mario Kart Wii contava o G7 duas vezes);
tipo lido do disco (`.rvz` byte 0x48). **Wii separado do GameCube** na
lista (commit `98b3000`), identificador avisa disco na pasta errada.
Confirmado pelo Rafael: Mario Kart Wii, Double Dash e Mario Party com 4.
**Abertura automática de todos os jogos do RetroArch**
(`testes\teste_abrir_todos.py`, commit `b7e38bb`): abrem e conectam no
Jogar Junto — Atari 2600, ColecoVision, Mega Drive (5), Neo Geo (KOF97,
MSlugX), NES, PS1 (5), 32X (3), SNES (2), ZX Spectrum. Abrem, núcleo sem
rede — N64 (6), PSP, Dreamcast (6), **C64 e Amiga (marcados agora
`netplay: false`)**. Falta arquivo do Rafael: Sonic CD (`bios_CD_E.bin`),
Saturn (`mpr-17933.bin`), KOF 2002 (romset de outra versão, 12 arquivos).
Não roda: Kinst (Killer Instinct não é Neo Geo; FBNeo "Romset is unknown").
Micro Machines 2 "não abre" no teste é falso (abertura preta de 25 s).
**Falta testar com o Rafael:** PS2 (9), PS3, Xbox 360, Smash Melee/Brawl,
NSMB Wii; e os de 3+ que não passaram pelo controle (Gauntlet Legends,
Armada, GigaWing 2; Saturn Bomberman depende da BIOS).

**Fliperama, Jogar Junto local e PS2 com 4 (26/09/2026, no `main`).**
MAME (núcleo `mame_libretro`) e Neo Geo (FBNeo, renomeado "Neo Geo e
fliperamas") funcionando; romset precisa bater com a versão do núcleo, CHD
em subpasta com o nome do romset, ficha = Select (aviso ao abrir).
Consoles sem partida entre computadores: o botão Jogar Junto abre uma
explicação curta de jogo LOCAL (vários controles num computador) em vez
do "quem hospeda" (`#modalJuntoLocal`). Left 4 Dead 2 entrou no System
Link do Xenia (`jogos_netplay`). **PCSX2 — 5 achados, corrigidos:**
(1) não era portátil (gravava em Documentos/OneDrive) → `portable.txt`
vazio ao lado do `pcsx2-qt.exe`, cartões copiados uma vez de Documentos;
(2) sem `[UI] SettingsVersion = 1` o PCSX2 apaga a config e abre o
assistente de BIOS → gravado com `SetupWizardIncomplete = false`;
(3) controles por `SDL-N` trocavam de número a cada reconexão → fonte
`XInput-N`; Multitap = `MultitapPort1`, jogadores em Pad1/Pad3/Pad4/Pad5;
(4) forçar a BIOS (v1.60) dava tela preta "Velocidade 0%" → BIOS NÃO é
forçada; (5) nomes de qualidade do 2.8 (`upscale_multiplier`,
`texture_preloading`, `VsyncEnable`) — os antigos não existiam, o seletor
não fazia nada (commit `46ab4c7`). **Confirmado pelo Rafael: Crash Nitro
Kart com 4** (G7 = 1, roxo = 2, preto = 3, teclado = 4). Mensagem "Falha
ao ler o cartão" só aparece com dois PCSX2 abertos ao mesmo tempo.
Champions of Norrath com 4 também aprovado.
**PS3 (26/09/2026):** firmware 4.93 instalado pelo Rafael. RPCS3 só tinha o
jogador 1 configurado → `graficos.escrever_controles_rpcs3()` grava
`config\input_configs\global\Default.yml` a cada jogo: um jogador por
controle XInput ("XInput Pad #N" = número do Windows + 1, conferido no
registro), teclado no 1º livre, 7 jogadores (commit `89654e4`). Aprovados:
Rayman Legends 4, Resident Evil 5 com 2, **Minecraft 4** — este dava
"falhou no carregamento" ao criar o mundo por causa do **RPCN** (ligado
pela tela do RPCS3 com a conta do Rafael); agora a chave `rpcn_ativo` vale
nos dois sentidos, desligada o ARENA desliga a internet do RPCS3 (commit
`fe402d7`, conta preservada). `dados\jogadores.txt`: RE5 = 2, Minecraft = 4
(autorizado, cópia `.antes-ps3`). Fotos de tela do PS3:
`testes\foto_rpcs3.ps1` (chamar via Python; pelo PowerShell direto trava).
Diablo III aprovado. **Xbox 360 (26/09/2026):** teclado do Xenia no 1º
jogador sem controle (`keyboard_mode`/`keyboard_user_index`, commit
`a20f164`). **Left 4 Dead 2 travava** (aviso de atualização → tela preta):
Direct3D 12 sem memória de vídeo na Radeon integrada ("Graphics device
lost"), também no Xenia normal. Com Vulkan abre — lista
`consoles.json → xbox360.externo.jogos_vulkan`, `graficos.placa_do_xenia()`
(commit `1bd45db`); teste `testes\teste_xenia_abre.py`. **Mas o texto do
menu sai ilegível** (letras quebradas) — igual no Direct3D 12 (rtv), no
Vulkan com `readback_resolve=full`, `readback_memexport=true`,
`gpu_3d_to_2d_texture=false`, `gpu_allow_invalid_fetch_constants=false`, e
no `xenia_edge.exe` (texto some). Falha do Xenia com esse jogo nesta
Radeon integrada, não do ARENA; não resolvida. Falta ver em placa dedicada.
Depois o **Gears também deu "Graphics device lost" no Direct3D 12** →
Vulkan para TODO o Xbox 360 (`consoles.json → xbox360.externo.placa`,
commit `71afbe9`); Gears no Vulkan estável e com texto certo.
**"Gears of War (USA) (Bonus Disc).iso" é o disco de EXTRAS** (Movies,
Map Packs, Gears 2 Content), não o jogo — falta o disco do jogo.
`testes\apertar_teclas.ps1` aperta teclas na janela (passar do PRESS START).
Marvel Ultimate Alliance (PS2) com 4 aprovado. **"Dead Space 3" da pasta
XBOX360 é o disco de PS3** (BLES-01733, cópia idêntica à da pasta PS3) —
Xenia: "Failed to verify disc image header". `identificador.py` agora
reconhece PS3 ("PlayStation3" no setor 1) e Xbox 360 (MICROSOFT*XBOX*MEDIA)
e o catálogo avisa pasta errada (commit `3b50cfe`). Nenhum arquivo apagado.
Dead Space 3 não tem cooperativo na mesma tela (só online).
**Borderlands 2 (PS3) com 2 aprovado** (G7 = 1, preto = 2). 4 na mesma
máquina: impossível (tela dividida do console vai até 2). Opção A aprovada
pelo Rafael: versão de **Xbox 360** pela rede local, 2 computadores × 2.
`borderlands 2` já em `xbox360.externo.jogos_netplay`. **Falta:** o Rafael
trazer a imagem de Xbox 360 do jogo; conferir com o identificador; testar
em 2 computadores (menu de rede de dentro do jogo). **26/09 18h:** o
"Borderlands 2" colocado na pasta XBOX360 é de novo o de PS3 (BLUS-30982,
saiu da pasta PS3) — catálogo avisa "disco de PS3". Gears of War Judgment
(Xbox 360, em subpasta) abre no Vulkan e roda a abertura; lista 2
jogadores e rede local por casar com "gears of war" (System Link do
Judgment não confirmado). **Judgment com 2 APROVADO pelo Rafael** (G7 = 1,
preto = 2, imagem excelente no Vulkan) — primeiro jogo de Xbox 360
jogado a dois nesta máquina. **Smash Brawl (Wii) com 4 aprovado** (preto =
1, roxo = 2, G7 = 3, teclado = 4 — ordem do XInput mudou nesta sessão, é
a ordem de conexão do Windows, não do ARENA).
**Falta testar com o Rafael:** L4D2 com 4 (depois do Vulkan), Gears com 2,
Marvel Ultimate Alliance, Borderlands 2, Smash Melee/Brawl, NSMB Wii,
Gauntlet Legends, Armada, GigaWing 2.

**Perfil-alvo (etapa 1 no `main` desde a auditoria 2; ramo `perfil-alvo` mantido).**
Objetivo do Rafael: o notebook mais fraco da escola (Celeron 2 núcleos,
4 GB, sem SSD, sem admin) vira o alvo oficial — bom nele, melhor nas
boas. **Etapa 1 feita (25/09/2026, commit `836427c`): só ferramentas de
coleta, nada do ARENA mudou.** `COLETAR.bat` (raiz) roda
`ferramentas\coletar_maquina.py` (retrato: CPU com AVX/AVX2, memória,
discos com velocidade real sem cache, vídeo, Windows, energia, rede,
Firewall, instalação) e `ferramentas\medir_arena.py` (abertura, servidor
parado/em uso, indexação, gravações/min, jogo de SNES com as opções reais
do ARENA: FPS por `--max-frames` e variação dos quadros do registro do
RetroArch; perguntas no fim). Saída em `perfil\<código>_<data-hora>\`
(fora do git): `.json` + `.txt`. Sem dado pessoal (código embaralhado
diferente do da sincronização). Limites do BOM/NO LIMITE/RUIM são
**provisórios** — recalibrar com os números do Celeron. Referência neste
PC (Ryzen 5 5600G): abre em 0,5 s, 76–93 MB, 0 gravações/min parado,
SNES 60 FPS, variação 3,2%. **Próximo passo:** o Rafael roda o
`COLETAR.bat` nos notebooks da escola e traz a pasta `perfil`.

**Auditoria completa CONCLUÍDA e juntada ao `main` em 25/09/2026.** Pedido do Rafael, salvo sem resumir em
`ARENA-unificado\docs\PLANO-AUDITORIA.md` — 9 fases (0 a 8), 10 regras que
não podem ser quebradas (ramo `auditoria` isolado, nada é removido sem
lista aprovada, toda medição precisa de número real, teste manual pra tudo
que só dá pra confirmar com notebook de verdade). Progresso e resultado de
cada fase ficam em `ARENA-unificado\docs\RELATORIO-AUDITORIA-1.md`. Trabalho
todo no ramo `auditoria`; o `main` só muda quando o Rafael aprovar a junção
no fim da Fase 8. Se a conversa for retomada depois de um `/clear`, ler os
dois arquivos antes de continuar — eles têm o pedido completo e o que já
foi feito.

- **Fase 0 concluída (23/09/2026).** Linha de base medida de verdade (script
  novo `testes\linha_base.py`, reaproveitável nas fases seguintes): pacote
  2.809,8 MB sem jogos, 21.857 linhas de código só do ARENA (a conta
  anterior de "7.847 + 5.501" da seção 4 abaixo está desatualizada — cresceu
  bastante nesta sessão; corrigir na Fase 8), abre em 0,63 s, 0,04% de CPU
  parado, 35,5 MB de RAM (só o servidor — a RAM da "tela" não deu pra isolar
  nesta máquina porque o Edge já estava rodando em segundo plano antes do
  teste; detalhe e solução alternativa no relatório), 15 threads, só a porta
  8777 em 127.0.0.1 (rede desligada por padrão, como deveria). Inventário
  completo de rotas (45, não 44 — diferença documentada), chaves de
  configuração, serviços em segundo plano e dependências de internet, tudo
  em `RELATORIO-AUDITORIA-1.md`. **Achado real, ainda não corrigido (fica pra
  Fase 1/2):** `dados\` acumula 38 arquivos de log do RetroArch de sessões
  de teste antigas, sem rodízio nem limite de tamanho. Bateria de 44 testes
  automatizados rodada como referência: OK, 0 falhas.

- **Fase 1 concluída (23/09/2026), aprovada em bloco pelo Rafael.** Varredura
  de código morto (`testes\varredura_fase1.py`) achou 3 remoções e 3
  correções reais, todas aplicadas e testadas. **Removido**:
  `servidor\transferencia.py` inteiro (módulo órfão de transferência P2P,
  nunca importado por ninguém); `graficos.opcoes_de_controle()` (duplicata
  morta — quem liga o analógico de verdade é `controles.opcoes_do_console()`);
  `hardware.shutil_disk_usage()` (wrapper nunca chamado). **Corrigido**: bug
  real de perda de dados em `/api/perfil/novo` — se a cópia de segurança
  falhasse (pen drive cheio, por exemplo), o código apagava o perfil do
  mesmo jeito, sem avisar; agora cancela o apagamento e devolve erro claro
  (testado nos dois caminhos, script novo
  `ferramentas\teste_backup_falha_cancela_apagamento.py`); lista
  `NAVEGADORES` (que acha o navegador pra abrir a tela) só cobria instalação
  com administrador — acrescentados os caminhos sem admin
  (`%LOCALAPPDATA%\...`); `2-JOGOS.md` corrigido — dizia que o núcleo do PS1
  "é o DuckStation", hoje é SwanStation. **Fica pendente, não decidido
  sozinho** (mesma pendência já existente na seção 10 abaixo): duas chaves
  `duckstation_*` em `graficos.py` (linhas 397, 550-551) — hedge intencional
  ou resíduo, só confirma testando PS1 de verdade contra um
  `retroarch-core-options.cfg` real. Bateria de 44 testes: OK, 0 falhas,
  antes e depois.

- **Fase 2 concluída (23/09/2026).** Leveza e desempenho. CPU parado já
  media 0,04% desde a Fase 0 — nada a corrigir. **Logs do RetroArch sem
  rodízio** (achado da Fase 0, 38 arquivos acumulados): `limpar_logs_antigos()`
  nova em `arena.py`, chamada a cada abertura, mantém só os 10 mais
  recentes — confirmado na pasta real (36 → 10). **Fundos animados**
  (pendência antiga desta seção, ver "Pendências conhecidas" abaixo):
  `galaxy-background.js`/`field-background.js` tinham um loop de animação
  que rodava para sempre, a cada quadro, mesmo escondido — nem modo modesto
  nem "prefira menos movimento" desligavam. Corrigido: os dois só animam
  quando tema+modo-modesto+preferência do sistema permitem, e o loop para
  de vez (não só de desenhar) quando não devem animar. No meio do próprio
  teste, achei e corrigi um bug novo que a primeira versão da correção
  introduziu (trocar de tema com o modo modesto ligado prendia o fundo
  errado na tela — separado `sincronizarVisibilidade()` de `draw()`).
  **Não deu pra medir o ganho de CPU do loop ativo** nesta sessão — a aba
  controlada pelo navegador automatizado ficou sempre com
  `visibilityState: hidden`, e nenhum navegador roda `requestAnimationFrame`
  de aba em segundo plano; fica pro roteiro manual de sala medir num
  Celeron de verdade. **CSS morto**: 5 classes confirmadas órfãs e
  removidas (`campo-apelido`, `jogo-acoes`, `jogo-gerir`, `jogo-dupla`,
  `acervo-cabeca-acoes` — sobras de redesenhos documentados no próprio
  código, ex.: o comentário em `app.js` sobre os botões terem saído do
  card); outras 27 pareciam mortas mas são construídas por template
  literal (`` `midia--${tipo}` ``) — confirmadas vivas, não removidas.
  Confirmado visualmente no navegador depois da remoção, sem mudança de
  layout. **Teste de estresse do catálogo**: 5.000 jogos falsos (3
  consoles reais) indexados em 1,48s (contra 0,13s com 32 jogos reais);
  segunda leitura com cache, 0,02s. Bateria de 44 testes: OK, 0 falhas, em
  cada etapa.

- **Fase 3 concluída (24/09/2026). Testes do servidor e da API — a fase com
  os achados mais sérios da auditoria até agora, todos corrigidos e
  testados.** Fuzz das 45 rotas (`testes\fuzz_rotas.py`, 244 checagens:
  dados corretos/faltando/tipo errado/texto gigante/emoji/travessia de
  pasta/repetição rápida) — achou 4 rotas respondendo erro em HTML em vez
  do formato JSON padrão do ARENA, corrigidas. **Achado maior: TODAS as 45
  rotas ficavam abertas pra rede inteira assim que "Aceitar conexões da
  rede" era ligado** — sem isso, nenhum estudante estaria seguro numa
  mesma rede com outro que soubesse abrir o DevTools. Corrigido com uma
  lista (`ROTAS_REDE_EXTERNA`) das 8 rotas que a partida a dois e a
  sincronização realmente precisam; todo o resto agora recusa (403) pedido
  vindo de fora deste computador. **CSRF provado AO VIVO**: uma página de
  outra origem, no mesmo navegador, conseguia mudar a configuração do
  ARENA real sem clique nenhum do aluno (Content-Type "text/plain" evitava
  a pergunta de permissão do navegador) — corrigido exigindo
  Content-Type application/json. **`/api/mala` escrevia em qualquer
  caminho do disco escolhido pelo cliente, sem validação nenhuma** —
  provado ao vivo criando um arquivo fora da pasta do ARENA; corrigido
  exigindo que o nome seja sempre `ARENA-troca.json` (o pen drive continua
  podendo ser qualquer um). XSS: checado, nenhum achado (`app.js` nunca usa
  innerHTML). Corrida de gravação real sob concorrência (`os.replace()`
  falhando no Windows quando outra thread lê o arquivo no mesmo instante) —
  corrigido com repetição curta; 6 rodadas de 50 pedidos simultâneos depois,
  zero falha. Longa duração acelerada (57 mil pedidos): RAM e handles
  estáveis, sem vazamento. Internet ruim: `internet_archive.instalar()` não
  tratava rede fora nem portal cativo (mensagens técnicas cruas) — corrigido
  com mensagem clara nos dois casos, e ganhou verificação de SHA-1 contra o
  que o Internet Archive declara (não tinha nenhuma antes). `capas_online.py`
  aceitava qualquer resposta 200 como "capa baixada", mesmo sendo a página
  HTML de um portal cativo — corrigido conferindo a assinatura de bytes
  real do PNG. SHA-256 do acervo (`acervo.py`): confirmado funcionando de
  verdade, com prova ao vivo (hash errado → recusado; hash certo → aceito).
  `/api/partida/testar` custava ~5,3s pra um endereço inválido (duas
  resoluções de DNS sequenciais, cada uma sem respeitar o timeout do socket
  no Windows) — corrigido resolvendo uma vez só, ~2,68s agora. Bateria de
  44 testes: OK, 0 falhas, depois de cada uma das correções acima.

- **Fase 4 concluída (24/09/2026). Jogar Junto — a fase mais trabalhosa,
  com uma funcionalidade nova pedida no plano e vários achados reais de
  rede.** **Multitap implementado do zero** (não existia): descoberto no
  código-fonte do núcleo snes9x que a porta 2 vira
  `RETRO_DEVICE_JOYPAD_MULTITAP` (257), abrindo 4 encaixes extras — porta 1
  continua jogador 1. `graficos.jogo_suporta_multitap()` +
  `consoles.json → jogos_multitap` (lista curada, hoje só "Super
  Bomberman"); `indexador.py` calcula `jogadores_max` **por jogo**, não
  por console inteiro; `app.js` já tinha o seletor genérico de posição,
  só passou a ler do jogo certo. Testado com 5 RetroArch reais (Super
  Bomberman 4): jogador 5 sozinho conecta perfeito; jogadores 2+3+4
  juntos conectam sem erro. **Achado real, não resolvido**: com os 4
  convidados juntos, só os 3 primeiros conectam — o 4º sempre falha,
  reproduzido em 3 rodadas mesmo com esperas bem generosas (afasta
  disputa de CPU). `input_max_users` e `MAX_CLIENTS` do RetroArch não
  explicam um limite de 4. Pode ser limite real do RetroArch ou artefato
  de testar 5 "computadores" todos em 127.0.0.1 — só 5 notebooks de
  verdade resolvem essa dúvida (item do roteiro manual, ver
  `RELATORIO-AUDITORIA-1.md`). **4 jogadores locais (GoldenEye 007, N64)**:
  configuração de 4 controles confirmada correta (`input_max_users` em
  Ajustes → Avançado, já existia); controle+teclado junto confirmado
  funcionando, mas só nos consoles que sempre suportaram isso (PS2,
  Dreamcast, MSX, ScummVM — não N64). **Simulador de rede ruim**
  (`testes\proxy_rede_ruim.py`, TCP puro em Python) testado com 5 níveis
  de atraso/perda: todos conectaram sem aviso de travada, até em 200ms +
  5% de perda simulada — mas o "ping" que o próprio RetroArch relata no
  log não acompanhou o atraso configurado de forma confiável (parece medir
  só o início da conexão), então não vale como prova do atraso sentido.
  **Cenários de sala**: convidado cai e reconecta — funciona; hospedeiro
  sai no meio — convidado detecta a queda e não trava; duas partidas
  simultâneas não dá pra testar num computador só (a porta do netplay é
  fixa no código, mas isso não é problema real — em computadores
  diferentes cada host tem seu próprio IP, sem conflito nenhum). 30
  "colegas" simulados anunciando ao mesmo tempo: lista completa, resposta
  em 18ms, CPU em 0%. **Sincronização**: registro duplicado já coberto
  pela bateria antiga (`INSERT OR IGNORE` por uuid); mala do pen drive
  **não depende de data de arquivo** — FAT32 (2s de granularidade) não é
  problema pra ela. **Achado real, não corrigido (pendência de design)**:
  relógio errado numa máquina faz os registros dela ficarem
  **permanentemente invisíveis** pra sincronização de outras — provado
  ao vivo (registro de 2020 nunca aparece numa consulta "desde as 09h de
  hoje"). Corrigir direito trocaria o carimbo de data por outra coisa
  (mudança de arquitetura, não feita agora); proposta seria um aviso na
  tela se o relógio do Windows parecer muito errado. **Diagnóstico de
  rede da escola** — pesquisa completa dos 6 itens do plano: **bug real
  corrigido** — `FAIXAS_DE_REDE` tinha `"172.2"` (faltava o "0.") em vez
  de `"172.20."`, e por comparar prefixo de texto isso classificava
  hotspot de iPhone inteiro (confirmado: `172.20.10.0/28`) como
  "adaptador virtual, não serve pro colega"; corrigido enumerando
  172.20–172.29 explicitamente. **Firewall/rede pública**: não tinha
  detecção nenhuma, só um palpite no texto de erro — `partida.py` ganhou
  `categoria_de_rede()` (lê `Get-NetConnectionProfile`, sem admin) e
  confirma/explica quando a rede está "Pública" (Firewall mais fechado,
  caixa de permissão pede senha de admin que o aluno não tem); testado
  nesta máquina, que realmente está numa rede Pública. VPN: gap real
  documentado, não corrigido (exigiria trocar o mecanismo de detecção de
  endereço todo, risco alto pra essa fase). Guias `5-AMIGOS.md`
  atualizados com o Multitap e o novo aviso de rede pública. Bateria de
  44 testes: OK, 0 falhas, em cada mudança. Roteiro manual completo (5
  cenários) escrito em `RELATORIO-AUDITORIA-1.md` pro Rafael testar em
  sala com notebooks de verdade — o Multitap de 5 jogadores é o mais
  importante dos cinco.

- **Fase 5 concluída (24/09/2026). Matriz de jogos.** Script novo
  `testes\teste_matriz_jogos.py`: pra cada console com núcleo nativo do
  RetroArch com jogo de verdade na pasta, usou `--max-frames-ss`
  (documentado no `--help` do RetroArch) pra abrir e tirar print sozinho,
  e `network_cmd_enable` + `SAVE_STATE`/`LOAD_STATE` por UDP (documentado
  no código-fonte) pra confirmar save state sem apertar botão nenhum.
  **6 consoles testados com jogo real** (N64, SNES, PS1, Dreamcast, PSP,
  Neo Geo): 6/6 abrem e mostram imagem; 5/6 salvam/carregam estado — o
  Neo Geo falha, mas é a MESMA pendência de BIOS já registrada aqui
  (seção "Neo Geo" abaixo) — log mostrou a causa exata (`sm1.sm1` com CRC
  errado impede o conteúdo de carregar por completo, e o núcleo desliga
  o save state sozinho quando isso acontece); não é achado novo, só mais
  detalhado agora. PCSX2 (PS2) e Xenia (Xbox 360, Gears of War) já
  tinham teste de ponta a ponta de sessão anterior — não repetidos. RPCS3
  (PS3, Borderlands 2) não testado nesta sessão — inicialização muito
  lenta pra automação seria arriscado; fica pro roteiro manual. Cheats:
  já cobertos pela bateria de 44 testes, mecanismo genérico. Controle
  físico e FPS contínuo (modo modesto × normal): não deu pra automatizar
  sem hardware/OCR de tela — ficam pendentes, sem número inventado.
  Nenhuma correção de código nesta fase, só teste e confirmação.

- **Fase 6 concluída (24/09/2026). Portabilidade e robustez — outra fase
  com achados reais corrigidos.** **Queda de energia no pior instante
  possível** (temporário já escrito, troca ainda não aconteceu): provado
  ao vivo, `config.json` continua intacto — `os.replace()` atômico
  funciona como prometido. **Achado real, corrigido: `arena.db`
  corrompido derrubava o ARENA inteiro**, cru, com traceback, antes do
  servidor HTTP conseguir subir — o oposto do que o projeto promete.
  `preparar_banco()` agora guarda o banco quebrado do lado (nunca apaga
  sem copiar) e começa um banco novo; `VERIFICAR.bat` já tinha essa
  proteção (com restauração de backup), meu conserto cobre a abertura
  **normal** do `ARENA.bat`, que é o caminho que um aluno realmente usa.
  **Achado real, corrigido: FAT32 sem aviso nenhum** — este projeto TEM
  jogos reais maiores que 4 GB (Gran Turismo 4, 4,95 GB) que
  simplesmente não cabem inteiros num pen drive FAT32; `VERIFICAR.bat`
  agora detecta o tipo de disco e avisa quais jogos provavelmente vieram
  truncados. **Achado real, corrigido: Windows de 32 bits nunca seria
  detectado** — o Python embutido é sempre 64 bits, então ele nem chega
  a rodar (e portanto nunca executaria a checagem) num Windows de 32
  bits de verdade; `ARENA.bat` ganhou uma checagem ANTES de tentar abrir
  o Python, no lugar certo. **Achado real, não corrigido (pendência
  documentada)**: caminho de 279 caracteres falha de verdade
  (`No such file or directory`, o limite classico de 260 do Windows) —
  mas a função central de gravação (`gravar_texto_atomico`) não é o
  risco (caminhos sempre curtos); o risco de verdade está em
  `capas_online.py`, `indexador.py` e principalmente o próprio
  RetroArch (C++, não testado), então corrigir direito é mais uma sessão
  de trabalho, não um ajuste pontual — mesmo padrão já usado pra VPN e
  relógio errado. Sem driver de vídeo de verdade: checado, o ARENA nunca
  força um `video_driver` específico (não piora nada, mas também não
  ajuda) — não dá pra testar sem a máquina certa. Antivírus/SmartScreen:
  `1-COMECAR.md` ganhou passo a passo pros dois (antes só citava
  "antivírus bloqueou" sem explicar como resolver). Código que precisa
  de administrador: varredura completa, zero achados — os únicos usos de
  `winreg` são leituras (não pedem admin), zero `netsh`, zero serviço.
  Pen drive com letra diferente/caminho com espaço e acento: já coberto
  e testado antes desta auditoria (e testado IMPLICITAMENTE em
  centenas de comandos ao longo de toda a auditoria — este próprio
  projeto tem espaço e acento no caminho). Disco cheio: não testado (sem
  jeito seguro de simular), só raciocínio por leitura de código
  (documentado como tal, não como prova). Bateria de 44 testes: OK, 0
  falhas, em cada mudança.

- **Fase 7 concluída (24/09/2026). Clareza para todos — proposta aprovada
  pelo Rafael ("fazer todos") e aplicada.** (A1) "Jogo não encontrado" agora
  diz o que fazer (Atualizar lista) nas 7 rotas; (A3) `traduzir_erro_do_sistema()`
  em `arena.py` troca texto cru do Windows/Python (`[WinError 5]`...) por
  frase em português nos 7 pontos que vazavam exceção; (A2/A4) mensagens
  "Índice inválido", "Espaço inválido", "Imagem inválida", "Destino inválido",
  "Console/Tipo de controle desconhecido" reescritas; (B) "BIOS" agora é
  explicada em `index.html` e `2-JOGOS.md`; (C) contraste do
  `--texto-apagado` no modo claro subiu de ~2,8:1 para >=4,76:1 (WCAG AA,
  calculado, `#75634d`); (D) card do jogo navegável por teclado
  (`tabindex`, `role=button`, Enter/Espaço). **Bug real achado no caminho,
  corrigido:** `/api/conquistas` dava 500 com 2+ jogadores no placar
  (`sorted()` sobre `sqlite3.Row`) — exatamente o caso de sala de aula;
  script `testes\teste_fase7.py` cobre. Bateria de 44: OK. **Não testado
  no navegador de verdade:** o foco por teclado do card e a nova cor.

- **Fase 8 concluída (25/09/2026) — AUDITORIA TERMINADA, ESPERANDO O
  RAFAEL APROVAR A JUNÇÃO `auditoria` → `main`. Não juntar sem ele.**
  `RELATORIO-AUDITORIA-1.md` completo: seção da Fase 7 (faltava), tabela
  antes × depois, removidos, corrigidos, o que falta, e 8 roteiros manuais
  de sala (eram 5; entraram máquina fraca, segurança de rede e pen drive).
  Números: pacote igual (2.810 MB), produto 22.428 → 22.801 linhas
  (`testes\comparar_linhas_produto.py main auditoria`), abertura 0,63 s,
  CPU parado 0,02%, RAM 35,8 MB, rotas abertas à rede 45 → 8. Gravações em
  disco por hora parado medidas pela primeira vez: **zero** em 10 min
  (`testes\medir_gravacoes_parado.py`). Rodada final de todos os testes
  (`ferramentas\rodada_final.py`, resultado em `docs\rodada_final_bruta.json`):
  **21 de 23**. O fuzz reprova as mesmas 7 checagens `414 URI Too Long` da
  Fase 3 (recusa do próprio Python, não é bug); `teste_local_4_jogadores`
  reprovou só por erro de SOM (Windows sem saída de áudio padrão na hora
  do teste) — repetir com fone/caixa ligados. Commit `e85621b`. Guias 1, 5, 6 e LEIA-ME atualizados
  (32 bits, SmartScreen, exclusão do antivírus pede admin, segurança de
  "Aceitar conexões da rede", banco corrompido na abertura normal, FAT32
  no verificador). Seção 4 deste arquivo com as contagens novas.
  **Achados da Fase 8, aprovados ("opção 2") e aplicados, com teste:**
  (1) alerta de "jogo cortado" do FAT32 da Fase 6 nunca disparava (procurava
  arquivo > 4 GB, impossível em FAT32; o teste fingia o disco) — agora
  procura 4 GB − 1 byte (commit `e96e178`); (2) DNS rebinding — reproduzido
  (site disfarçado de 127.0.0.1 mudava a config), corrigido com
  `host_confiavel()` em `arena.py`; (3) achado no caminho: `PARTIDA.bat`
  perdeu em silêncio, desde a Fase 3, as checagens de versão e código de
  aparelho do colega (pedia `/api/estado`, fechada à rede) — agora usa
  `/api/sinc/ola`, que passou a devolver `versao` (commit `051084e`).
  Testes novos: `teste_dns_rebinding.py`, `teste_partida_colega.py`.
  **Junção feita (25/09/2026, aprovada pelo Rafael):** `auditoria` →
  `main` no commit `2633704` (merge sem avanço rápido, histórico das fases
  preservado). Bateria de 44 no `main` depois da junção: OK. O ramo
  `auditoria` foi mantido, não apagado. Trabalho novo volta a ser no `main`.

- **Revisão pós-auditoria (25/09/2026), no `main`.** Pedido do Rafael:
  "revise todas as pendências... quero tudo resolvido". Detalhe completo,
  com prova e teste de cada item, em `RELATORIO-AUDITORIA-1.md` → "Revisão
  pós-auditoria". Resumo dos achados GRAVES corrigidos:
  (1) **o ajuste de imagem do ARENA era ignorado em 8 núcleos** —
  `global_core_options=false` fazia cada núcleo ler o próprio `.opt`;
  agora `gravar_override` liga o arquivo global, que mantém o que o aluno
  mudou no menu; (2) **Multitap: 5º jogador recusado** pelo padrão
  `netplay_max_connections=3` — sobe para 4 com Multitap, 4 convidados
  entram (e o teste de 5 jogadores devolvia OK sempre; corrigido);
  (3) **sincronização por data** — relógio errado sumia com recordes e
  partida longa nunca era enviada; agora é por número de chegada (`seq`),
  banco antigo migra sozinho; (4) **`retroarch.cfg` real com saves
  apontando para pasta temporária apagada** (deixado pelo teste da matriz)
  e **nome completo do Rafael** como apelido de netplay — corrigido, e
  `testes\protege_cfg.py` protege o cfg nos 11 scripts que abrem o
  RetroArch; (5) escolha de BIOS não fazia nada em 3 de 4 núcleos (chaves
  inexistentes) — tela só oferece onde funciona; (6) memory card: fica um
  por jogo (é onde todo save de PS1 já está; "compartilhado" nunca valeu).
  Também: VPN/adaptador virtual pelo NOME do adaptador; VERIFICAR avisa
  caminho de save > 260 letras; disco cheio testado (mensagem clara);
  PS3 sem firmware avisa em vez de "piscar e fechar"; download real do
  acervo testado; RAM da tela (~420 MB, teto) e CPU do fundo animado
  (2,0% × 0,5% de um núcleo) medidos; passo a passo das 5 pessoas feito
  (análise de tela, não observação); `fechamentos.json` zerado (autorizado).
  Bateria: **45** testes. **Rodada completa (`ferramentas\rodada_final.py`):
  35 de 35** (bateria + fuzz + 33 scripts, com RetroArch de verdade; a
  primeira tentativa caiu por falta de memória, a segunda foi até o fim).
  **Fase 8 fechada.** **Decisões do Rafael (25/09/2026), aplicadas:**
  `servidor\db.py` removido (a bateria testava a cópia; `TestDB` agora
  testa o `arena.py`); "Aceitar conexões da rede" vale na hora, sem
  reabrir (servidor reabre no mesmo processo, `SERVIDOR_ATUAL` +
  `TRAVA_REDE`); faixa "F2 salva · F4 volta · F10 fecha" **na janela do
  ARENA** (dentro do jogo não dá: stdin do RetroArch não funciona no
  Windows, e rede é brecha). **Não escolhido:** "Salvar ao sair" por
  padrão — fica desligado. **Achado de segurança no caminho, corrigido:**
  `network_cmd_enable` estava `true` no `retroarch.cfg` e o RetroArch
  aceitava comandos (fechar jogo, salvar) de qualquer máquina da rede em
  `0.0.0.0:55355`; agora é forçado `false` em toda partida e na correção
  automática do cfg.
  **Depende de arquivo/conta dele**: firmware do PS3, BIOS do Neo Geo,
  conta RPCN, Mario Kart 64 (para conferir o HUD com `parallel-rdp`).
  Seção 7 deste arquivo está desatualizada (descreve testes da versão
  antiga): os testes de verdade são `servidor\tests\run.py` (45) +
  `testes\*.py`; rodada completa: `ferramentas\rodada_final.py`.

**Feito na unificação** (32 commits, último `c4bc8bf`):
- **Ajustes enxugados, aba por aba, nada removido.** Achado real: "Tipo de controle" tinha um campo DUPLICADO e escondido (`#listaDriverControle`, `div hidden`) que nunca aparecia na tela — código morto, só sincronizava com o campo de verdade. Removido. "Ou digite o endereço na mão" (Amigos) virou `<details>` recolhido por padrão — continua tudo lá, só não compete visualmente com o jeito fácil (código). 4 parágrafos soltos na seção de mapeamento de controle viraram 2. Parágrafo interrompendo os 3 toggles de desempenho (Máquina) foi absorvido no texto de ajuda do próprio toggle. Frase órfã no topo da aba Perfil (sobrou de antes da foto entrar ali) removida. Confirmado visualmente no navegador em cada aba mexida (Amigos, Controles, Máquina, Perfil). Simples/Avançado/Emuladores já estavam enxutos, conferidos sem mudança.
- **Revisão dos controles pros consoles novos (Mega Drive, Neo Geo, PS3, Xbox 360).** Achado real: `graficos.py` já tinha o Neo Geo mapeado certo (A/B/C/D/Start/Select) há tempos, mas `perfis_controle.json` — o arquivo que a tela "Ajustes → Controles" usa de verdade — não tinha entrada nenhuma pra ele, caindo no perfil genérico de 8 botões (com L/R que o joystick de arcade não tem). Corrigido e confirmado em dois níveis (API + navegador de verdade): a tela agora mostra A/B/C/D e desliga sozinha os campos de analógico/vibração. Mega Drive já estava correto nos dois arquivos, sem mudança. **PS3 e Xbox 360 continuam de propósito fora desse sistema**: rodam por RPCS3/Xenia, que têm suporte nativo a controle XInput sem precisar de nada do ARENA — já documentado na própria tela ("Xbox 360, One e Series: plugou, funcionou").
- **Bug real corrigido: capa baixada dava 404 na hora de mostrar.** Achado testando no navegador de verdade (rede do Chrome mostrando 404 em toda capa de `retroarch/thumbnails`): a rota `/api/capa` só deixava servir arquivo de dentro de `jogos\` (proteção contra path traversal); o download automático salva em `retroarch\thumbnails\`, fora dali. Corrigido: aceita as duas pastas agora. Confirmado no navegador com capas que já tinham sido baixadas antes e não apareciam.
- **PS3 virou disco (como o PS1), Xbox 360 e PSP ganharam molde próprio** (verde pro Xbox, UMD pequeno pro PSP). Capa em molde retangular (cartucho/DVD/cartão) parou de cortar — usa `object-fit: contain` agora, mostra inteira. Disco continua cortando em círculo de propósito (é pra virar o disco mesmo). Busca automática de capa agora tenta tags de região comuns quando o título não tem nenhuma.
- **Correções pós-fase-4** (Rafael testou e achou 3 problemas reais, todos corrigidos): (1) foto de perfil tinha ido pra aba errada (Amigos) — movida pra aba Perfil de verdade, confirmado no navegador; (2) moldes de mídia "não pareciam com nada" — refeitos com `clip-path` de verdade (cartucho com ombro cortado + trilha dourada, **jewel case onde a própria capa vira um disco redondo com furo no meio**, caixa de DVD com lombada), confirmado no navegador pros 3 tipos testados; (3) capa "não baixava" — nunca tinha existido busca automática (só pasta manual), e havia um bug de cache separado (`dados/manifesto.json` não percebia miniatura nova em `retroarch/thumbnails`). Implementado `servidor/capas_online.py`: busca sob pedido no libretro-thumbnails (o banco que o próprio RetroArch usa no Atualizador Online dele), só pros consoles conferidos de verdade — PS2/PS3/Xbox 360 não tem banco bom nessa fonte, ficam só com envio manual. Botões "Buscar capa" / "Enviar capa" no painel de detalhes. Testado de ponta a ponta (Sonic 3 → baixou 492 KB reais).
- **Capas em formato de mídia física (fase 4)**, agrupado por tipo de mídia (5 categorias) — combinado com o Rafael, não um molde fiel por console. Só CSS, leve. Testado visualmente no navegador de verdade. Documentado em `2-JOGOS.md`.
- **Perfil com foto, permanente** — Ajustes → Amigos → Meu perfil. Foto em arquivo separado (`dados/perfil/`), tipo conferido pelos bytes de verdade, recorte 256×256 no navegador antes de enviar. Testado de ponta a ponta.
- **Amigo não precisa mais ser re-adicionado quando o IP muda.** Causa raiz: nem `/api/amigo/adicionar` nem `/api/amigo/codigo` gravavam o `id` do aparelho no registro do amigo — só apelido e endereço. Sem o `id`, o ARENA não tinha como cruzar "amigo salvo" com "vizinho visto agora na rede" (mecanismo que já existe, `VIZINHOS`/broadcast UDP 55436). `resolver_endereco_amigo()` nova: confere o `id` contra os vizinhos vistos agora, corrige o endereço salvo sozinho quando muda (rede diferente/internet continua usando o endereço fixo, do jeito certo). `quem_esta_online()` e `sincronizar_com()` usam isso antes de testar. Amigo adicionado à mão por endereço (sem `id`) continua igual — é o esperado. Testado direto no módulo + pela API real. Script: `ferramentas/teste_amigo_ip_muda.py`.
- **RPCS3 online (RPCN) implementado, desligado por padrão.** Diferente do PS2/Xbox 360, o RPCN pede conta num servidor comunitário de terceiros — o ARENA nunca cria essa conta sozinho (dado de gente indo pra fora da escola, confirmação por e-mail que só quem tem a caixa de entrada completa). `escrever_config_rpcn()` liga `Internet enabled`/`PSN status: RPCN` no `config.yml`; chave `rpcn_ativo` em Ajustes → Emuladores, desligada até o professor criar a conta pela própria tela do RPCS3 e ligar. Testado de ponta a ponta (sem criar conta — só a configuração). Script: `ferramentas/teste_rpcn.py`.
- **Biblioteca online corrigida — tinha DOIS bugs, não um.** `internet_archive.py` estava sem validação de licença/coleção (histórico de uma sessão anterior) — restaurado pra só buscar em coleções com curadoria de verdade do Internet Archive (hoje: `softwarelibrary_msdos_shareware`, verificada uma por uma; pesquisei outras "homebrew"/"domínio público" mas a maioria é envio de usuário sem checagem, incluindo ROM comercial rotulada errado — não entraram). Achado no caminho: um SEGUNDO bug, funcional — `arena.py` chamava `internet_archive.instalar()` com um dicionário só, mas a função espera três argumentos separados; toda tentativa de baixar dava `TypeError` disfarçado de "Download falhou" genérico. Provavelmente a causa real de "não funciona nada bem". Corrigido e testado de ponta a ponta (busca real + download real confirmado em disco). Script: `ferramentas/teste_biblioteca_online.py`.
- **Xbox 360 em rede de verdade (Systemlink), sem driver nenhum.** O Xenia Netplay (`xenia_canary_netplay.exe`, já vem na pasta) tem um modo "Systemlink" 100% em software — só muda `network_mode=1` no `config.toml` dele. ARENA troca pro build de netplay só quando abre um jogo da lista (hoje só Gears of War); sozinho continua o Xenia normal. Testado de ponta a ponta pelo `/api/jogar` real.
- Detecção automática de BIOS testada com 15 arquivos reais: o SwanStation e o PCSX ReARMed acham e usam o `SCPH1001.BIN` certo, ignorando os de tamanho errado.
- Aba Emuladores com seletor de qualidade "Automático / Mais leve / Mais bonito" para PCSX2, RPCS3 e Xenia, com frase de exemplo em cada opção. Testado contra o `.toml` real do Xenia.
- **Correção permanente de caminhos**: `graficos.corrigir_caminhos_retroarch_cfg()`, chamada por `arena.py::principal()` a cada abertura, reescreve qualquer caminho do `retroarch.cfg` que não aponte pra pasta atual do ARENA — não precisa saber qual era a pasta antiga, só reconhece as pastas que sempre existem (`dados`, `retroarch`, `jogos`, `launcher`, `emuladores`) dentro do valor velho. Achado no caminho: `cache_directory` nunca tinha sido setado em lugar nenhum, então o RetroArch usava a pasta Temp do Windows por padrão — corrigido nos dois lados (override em toda partida + força essa chave na correção automática). Teste de aceite (copiar pra pasta de teste, abrir de lá, conferir que não sobra caminho de fora) passando — scripts em `ferramentas/teste_correcao_caminhos.py` e `ferramentas/teste_aceite_pasta_movida.py`.
- **Netplay de PS1 resolvido com PCSX ReARMed**, testado de ponta a ponta (hospedar pelo ARENA de verdade + segunda instância conectando em 127.0.0.1, igual foi feito com o SNES): `pcsx_rearmed_libretro.dll` declara `savestate_features = "deterministic"` e aceita a mesma BIOS (`SCPH1001.BIN`, achada por CRC32). Cadastro novo em `consoles.json`: `core_netplay` no PS1 aponta pro PCSX ReARMed; `arena.py` troca o núcleo só quando é Jogar Junto (hospedar/entrar/assistir) — jogando sozinho continua o SwanStation, mais fiel. Aviso sobre a troca aparece na tela (`aviso_netplay` → `recado()`). Script: `ferramentas/teste_netplay_ps1.py`.
- Netplay testado por console (tabela na seção "Funcionalidades existentes").
- **PS2 em rede de verdade (system link) implementado, opcional, sem pedir admin sozinho** (commit `416930b`). Investigação inicial achou que precisava do driver Npcap/WinPcap pros dois lados (hospedar+entrar) e que instalar driver pede administrador — o Rafael pediu pra implementar mesmo assim, como opcional: o ARENA só *detecta* se o driver já existe (isso não pede admin, só olha se o arquivo está lá) e mostra o status em Ajustes → Emuladores com link oficial (npcap.com) pra quem quiser instalar por conta própria. `graficos.npcap_instalado()`, `graficos.adaptador_de_rede_real()` (acha o adaptador Wi-Fi/Ethernet real, ignora virtuais), `graficos.escrever_config_rede_ps2()` (grava `[DEV9/Eth]` no PCSX2.ini — `PCAPBridged` com driver, `Sockets` sem driver, só entra). Lista de jogos compatíveis fica em `consoles.json → ps2.externo.jogos_system_link`, começa só com Gran Turismo 4 (confirmado que tem system link de verdade), cresce aos poucos. Testado de ponta a ponta pelo `/api/jogar` real: aviso certo, `[DEV9/Eth]` gravado com o adaptador Wi-Fi real. Script: `ferramentas/teste_rede_ps2_gt4.py`. **Npcap foi instalado nesta máquina de desenvolvimento** (autorizado pelo Rafael, só pra esse teste). Limite honesto: não dá pra confirmar que duas máquinas reais se encontram pela rede sem duas máquinas de verdade — só a escola testando confirma.
- **Netplay testado em mais 3 consoles** (commit `7bc307b`): Mega Drive/Master System/Game Gear (Genesis Plus GX) funciona, testado de ponta a ponta como PS1/SNES. Dreamcast (Flycast) e PSP (PPSSPP) recusam — confirmado tentando hospedar de verdade, não só pelo `savestate_features` do `.info`. `netplay=false` + motivo adicionados pros dois, senão o botão Jogar Junto apareceria disponível sem funcionar (mesmo bug que o N64 tinha). Scripts: `ferramentas/teste_netplay_megadrive.py`, `ferramentas/teste_netplay_suporte_nucleos.py`.
- **Seletor de qualidade ligado no PCSX2**, testado de ponta a ponta pelo ARENA de verdade (`ferramentas/teste_pcsx2_completo.py`, abre Crash Nitro Kart pelo `/api/jogar`). Achados no caminho: (1) o PCSX2 nunca tinha rodado de verdade nesta pasta — sem BIOS na pasta `bios\` dele, trava num assistente visual que não dá pra responder sem tela; `graficos.preparar_bios_pcsx2()` agora copia sozinho uma BIOS de PS2 de `retroarch\system` (reconhece pelo tamanho fixo de 4 MB, sem CRC32 cadastrado — se houver mais de uma, pega sempre a mesma, em ordem alfabética; não mexe se já tem BIOS lá). (2) O PCSX2 só grava `[EmuCore/GS]` no `.ini` quando alguém muda algo pela tela de Configurações — abrir um jogo sozinho, mesmo rodando de verdade por 20s, não cria o bloco. `escrever_config_pcsx2()` agora escreve esse bloco do zero (`UpscaleMultiplier`, `MaxAnisotropy`, `TexturePreloading` — conferidas contra o código-fonte do PCSX2 no GitHub, não inventadas), em vez de só completar um arquivo existente como no Xenia/RPCS3. Testado com os presets "leve" e "bonito" abrindo o jogo de verdade nos dois. Scripts: `ferramentas/teste_qualidade_pcsx2.py`, `ferramentas/teste_pcsx2_completo.py`.

- **`netplay_check_frames = 0` ligado no PCSX ReARMed** (só quando o Jogar Junto troca pro núcleo alternativo — SNES e outros continuam com o padrão 600). Testado host+convidado reais por 25s em cada valor, medindo CPU do host quadro a quadro (script `ferramentas/teste_netplay_check_frames.py`): confirmei que é seguro (conexão estável nos dois casos), mas **não consegui confirmar o ganho de fluidez** — esta máquina de desenvolvimento é forte demais pra revelar um custo que só pesa em hardware fraco. Liguei mesmo assim por ser seguro, reversível e não dar pra testar o ganho real sem o Positivo da escola. Se algum dia notar diferença (ou notar o oposto), é aqui: `arena.py`, bloco `if plataforma.get("core_netplay")` dentro do `/api/jogar`.

**Pendente:**
- ~~Limpar `dados/fechamentos.json`~~ — zerado em 25/09/2026 com autorização (cópia em `backup\`).
- ~~Firmware do PS3~~ — instalado pelo Rafael (4.93, 26/09/2026); vai na versão dos alunos. Sem ele, o ARENA avisa.
- **RPCN:** ligado pelo Rafael com a conta DELE, pela tela do RPCS3 (26/09/2026). A conta é dado pessoal: `rpcn.yml` nunca vai na versão dos alunos (o montador não leva e confere). Claude não cria conta nem digita senha.
- ~~Neo Geo sem a BIOS certa~~ — certa desde 25/09/2026 (`ferramentas\conferir_bios_neogeo.py`: sm1, sp-s3, sfix e 000-lo com nome e CRC); vai na versão dos alunos.
- ~~"Testes de stress e revisão de todas as funções"~~ — feito: auditoria completa (Fases 0–8) + revisão pós-auditoria.
- **Memory card da partida a dois de PS1 NÃO sincroniza — confirmado testando de verdade** (script `ferramentas/teste_memory_card_ps1.py`, hospedou Crash Team Racing pelo ARENA, conectou um convidado de verdade, comparou o hash dos dois cartões). O host grava normal; o convidado, ao conectar, ganha um cartão em branco — o RetroArch redireciona a pasta de saves dele pra uma subpasta isolada `.netplay` e cria um cartão novo ali, porque o PCSX ReARMed não usa a interface padrão de SRAM do RetroArch (gerencia o cartão sozinho — log mostra "Ignorando carregamento da SRAM"). A frase da comunidade ("funciona bem contanto que os dois usem o memory card de quem hospeda") é instrução pro operador, não descrição de um comportamento automático. Efeito prático: a corrida em si roda igual pros dois (a simulação determinística não depende do cartão), mas o que cada um destrava/salva na sessão fica só na máquina dele, sem compartilhar. Sem prioridade agora — registrado, não implementado.
- **Medir de verdade o efeito do `netplay_check_frames = 0`** num Positivo dual-core/4GB da escola (não deu pra confirmar no computador de desenvolvimento, forte demais).

## Duas versões nesta pasta
- `ARENA - Versão antiga para.implemen…` (nome completo no disco): versão feita pelo professor no chat do Claude. É a que a seção "Funcionalidades existentes" descreve (arena.py, graficos.py, dados\controles.json).
- `ARENA-remake--master`: remake feito por um aluno.
- `Instruções.txt`: **não se aplica ao ARENA.** É um modelo genérico de prompts para outro aplicativo (ZeroHit, com Next.js, Supabase e cobrança). Contradiz todas as restrições do ARENA — Python puro, offline, sem administrador, sem monetização. Não seguir.

## Objetivo atual: unificar as duas versões
- Trabalhar somente em `ARENA-unificado`. Os dois originais nunca são editados: são backup e referência.
- Não existe mesclagem automática entre bases de código escritas de forma independente. O método é portar funcionalidade por funcionalidade.
- Ordem:
  1. Auditar as duas versões: linguagem, estrutura de arquivos, como iniciar cada uma e lista de funcionalidades.
  2. Montar a tabela funcionalidade × versão (tem / não tem / parcial).
  3. Recomendar qual versão serve de base, com justificativa técnica, e esperar aprovação.
  4. Copiar a base para `ARENA-unificado`, sem jogos, ROMs, cores nem saves.
  5. `git init` dentro de `ARENA-unificado`, com `.gitignore` que exclua os arquivos pesados, e commit inicial.
  6. Portar, uma por vez, as funcionalidades que existem só na outra versão.
  7. Testar e fazer commit a cada uma.
- Quando as duas versões implementam a mesma função de formas diferentes, mostrar as duas e recomendar uma. Não decidir sozinho.

## Funcionalidades existentes
- Backup automático ao fechar o jogo
- Ferramenta de verificação e reparo
- Pacote portátil de progresso (saves e cheats, sem os jogos)
- Sincronização de placar entre colegas, sem depender de internet
- Descoberta automática de colegas na rede ("Colegas encontrados na rede")
- Netplay pela internet (relay oficial do RetroArch), exposto como "Estamos em casas diferentes"
- Ajuste automático de desempenho por hardware
- Mapeamento de controle nativo em Ajustes → Controles, salvo em `dados\controles.json`
- Emuladores externos: PCSX2 (PS2), Dolphin (GameCube), RPCS3 (PS3), Xenia (Xbox 360)

### Jogar junto — testado de verdade, por console

| Console | Partida a dois em máquinas separadas |
|---|---|
| Super Nintendo | Funciona — testado com conexão real, na escola e no ponto de acesso do celular. Multitap (Super Bomberman, até 5 jogadores): os 5 conectam num computador só depois de subir `netplay_max_connections` (o padrão 3 do RetroArch era a causa do 5º recusado); falta confirmar em 5 notebooks (Roteiro 1) |
| Mega Drive, Master System, Game Gear | Funciona — testado de ponta a ponta (Genesis Plus GX) |
| Nintendo 64, Dreamcast, PSP | Não — o núcleo de cada um recusa ("núcleo não tem suporte para Netplay") |
| PlayStation 1 | Funciona — testado com conexão real, usando o PCSX ReARMed em vez do SwanStation (só no Jogar Junto; sozinho continua o SwanStation) |
| PlayStation 2 | Não pelo Jogar Junto normal (emulador externo) — mas alguns jogos (hoje só Gran Turismo 4) têm rede de verdade por dentro do próprio jogo, ver "PS2 pela rede" |
| Xbox 360 | Alguns jogos (hoje só Gears of War) têm rede local de verdade (Systemlink) via um build separado do Xenia dedicado a isso — sem driver nenhum. Testado de ponta a ponta |
| PS3 | Não investigado a fundo ainda — RPCS3 tem "RPCN", mas passa por criar conta num servidor comunitário de terceiros; decisão de privacidade pendente do Rafael antes de implementar |
| Neo Geo | Núcleo (FBNeo) declara suporte a netplay (`savestate_features = "deterministic"`), mas não testado de ponta a ponta — faltou romset zipado com nome identificável e BIOS de Neo Geo pra testar de verdade |

## Decisão que não pode ser revertida
- Gravação de vídeo e transmissão ao vivo estão desativadas de propósito, para proteger dados de aluno menor de idade. Não reativar nem propor reativação.

## Documentação
- LEIA-ME.md e guias numerados de 1 a 6 descrevem o comportamento para o usuário final.
- Ao mudar uma função, atualizar o guia correspondente na mesma tarefa.
- A tecla que destrava os atalhos no modo Ultra Desempenho é **F9** (era Scroll Lock; trocada porque notebook de escola costuma não ter). Conferir se os guias da versão unificada já dizem F9.

## Regras de trabalho
- Mostrar o plano e esperar aprovação antes de criar ou editar arquivos.
- Nunca editar as pastas originais das duas versões.
- Uma alteração por vez. Depois de cada uma, dizer exatamente como testar.
- Antes de corrigir um bug, confirmar a causa lendo o código e reproduzindo o problema. Não presumir.
- Nunca apagar saves, jogos, cores nem a pasta `dados\`. Alterar arquivos de dados do usuário só com autorização explícita.
- Fazer commit no git depois de cada alteração testada e aprovada.
- Nomes de arquivo, textos da interface e documentação em português do Brasil.
- Se faltar informação para decidir, perguntar em vez de assumir.

---
# ARENA — memória do projeto

> Este arquivo é lido automaticamente pelo Claude Code ao abrir a pasta.
> Ele carrega o contexto de meses de desenvolvimento: o que o ARENA é, para
> quem, o que já foi decidido e **por quê**, e os erros que custaram caro
> para descobrir. Leia antes de propor qualquer mudança.

**Versão atual:** 2026.10.03.2
**Autor:** Rafael Parise Passos — professor, SEDUC-SP
**Local do projeto no Windows:** `C:\Projetos\Criador De Apps Pedagógicos\ARENA`

---

## 1. O que é o ARENA

Um lançador portátil de emuladores, escrito em **Python puro**, que roda de
pen drive em computador de escola. Serve a dois propósitos ao mesmo tempo:

1. **Produto que funciona:** os alunos jogam, guardam recordes, jogam a dois
   pela rede e levam o progresso no bolso.
2. **Material didático:** o próprio código é o objeto de estudo das aulas de
   Redes, Banco de Dados, Back-End, Front-End e Metodologias Ágeis.

O segundo ponto é o que justifica várias decisões que, num projeto comum,
pareceriam excesso de zelo. O código é lido por adolescentes.

---

## 2. Restrições inegociáveis

Estas não são preferências. São o ambiente real e **qualquer proposta que as
viole está errada**, por melhor que seja tecnicamente.

| Restrição | Por quê |
|---|---|
| **Sem `pip install`** | Só biblioteca padrão. Máquina de escola não deixa instalar nada |
| **Sem permissão de administrador** | Em nada, nunca. Nem para firewall, nem para driver, nem para serviço |
| **Roda de pen drive** | Caminhos relativos sempre. Nada de registro do Windows para gravar |
| **Funciona offline** | Internet é bônus. Sincronização, acervo e busca online degradam com elegância |
| **Celeron de 2 núcleos, 4 GB, sem SSD** | É o piso. Se não roda nele, não serve. **Máquina-alvo medida (30/09/2026): Celeron N5100, sem AVX — `ARENA-unificado\docs\MAQUINA-ALVO.md`.** A descrição "2 núcleos, 4 GB" é a antiga estimativa; falta o Rafael confirmar se ainda existe notebook assim na escola |
| **Firewall restrito** | O ARENA pede passagem duas vezes (Python 8777, RetroArch 55435) e explica isso ao aluno |
| **Código comentado em português** | Aluno de 2ª série do médio lê este código |

---

## 3. Contexto pedagógico

**Escolas:** EE Alexandrina Santiago Netto e EE Vilma Catharina Mosca Leone
(Praia Grande/SP). Sede administrativa em EE Silvia Jorge Pollastrini
(Itanhaém/SP).

**Turmas e componentes:**

| Turma | Componentes |
|---|---|
| 2ºC (Alexandrina) | Lógica e Linguagem de Programação (C1); Redes e Segurança da Informação na Nuvem (C2) |
| 2ºA (Vilma) | Redes e Segurança (C2); Processos de Desenvolvimento de Software e Metodologias Ágeis (C3) |
| 3ºB (Alexandrina) | Programação Back-End (C2); Front-End (C3); Modelagem e Desenvolvimento de Banco de Dados (C4) |

**Como o ARENA vira aula:**

| Componente | O que o ARENA oferece |
|---|---|
| Redes | Captura do handshake TCP na partida a dois (porta 55435); LAN sem roteador; isolamento de cliente |
| Banco de Dados | `RANK() OVER (PARTITION BY ...)` no `arena.db` real; CTEs; discussão de desnormalização |
| Back-End | As 45 rotas da API; gravação atômica; travas de concorrência |
| Front-End | `app.js` sem framework; acessibilidade; estados de carregamento |
| Metodologias Ágeis | Kanban com os defeitos reais do projeto; casos de teste a partir de bugs que aconteceram |

**Hardware alvo:**

- Alexandrina: notebooks i5/i7, 8 GB, NVMe
- Vilma: Positivo dual-core, 4 GB, sem SSD
- Máquina do Rafael: Ryzen 5 5600G, Radeon Vega **integrada**, ~11,8 GB
- Portáteis: SanDisk USB 3.1 64 GB, cartão SD 512 GB, SSD SATA com adaptador USB 3.2

---

## 4. Arquitetura

```
ARENA\
├── ARENA.bat              abre o servidor e o navegador
├── VERIFICAR.bat          confere e conserta (10 verificações)
├── PARTIDA.bat            diagnostica por que a partida a dois não conecta
├── LEIA-ME.md             índice
├── 1-COMECAR.md           pen drive, instalação, Python embutido
├── 2-JOGOS.md             jogos, pastas, consoles, acervo, capas
├── 3-IMAGEM-SOM-CONTROLE.md  gráficos, perfis de controle, desempenho
├── 4-SAVES.md             save states, cheats, menu Esc, PCSX2
├── 5-AMIGOS.md            servidor, rede, partida a dois
├── 6-RECURSOS-E-REPARO.md as 50 opções avançadas e o verificador
│
├── servidor\              (Python puro, 18.626 linhas em 24 módulos — contado em 03/10/2026, à tarde)
│   ├── arena.py           servidor HTTP, banco, sincronização (6.416 linhas)
│   ├── indexador.py       varre pastas, lê capas, detecta discordância
│   ├── jogadores.py       quantos jogadores cada jogo aceita (dados\jogadores.txt + jogos testados)
│   ├── motivo_do_erro.py  por que o jogo não abriu, pelo registro do emulador
│   ├── bios.py            a pasta BIOS: reconhece cada BIOS e põe onde o emulador procura
│   ├── bios_catalogo.py   todas as BIOS dos consoles (pasta, região, nível)
│   ├── arrumar.py         o botão Arrumar: o arquivo do jogo no lugar certo
│   ├── hardware.py        CPU, RAM, disco, GPU integrada/dedicada, identidade
│   ├── graficos.py        perfis por núcleo, BIOS, memory card, partida, PCSX2
│   ├── controles.py       mapeamento, perfis controle × console
│   ├── cheats.py          save states e códigos
│   ├── identificador.py   lê SYSTEM.CNF e cabeçalho CHD
│   ├── acervo.py          jogos livres, SHA-256, hosts restritos
│   ├── internet_archive.py  busca e download do Internet Archive
│   ├── diagnostico.py     VERIFICAR.bat
│   ├── partida.py         PARTIDA.bat
│   ├── consoles.json      52 plataformas
│   ├── graficos.json      ajuste por núcleo, por nota, modo modesto, exceções
│   ├── recursos.json      50 opções com explicação e analogia
│   ├── perfis_controle.json  13 tipos de controle × 19 consoles
│   └── python\            Python 3.13.15 x64 embutido (21 MB)
│
├── launcher\              (8.649 linhas — 02/10/2026, à noite)
│   ├── index.html         1.032 linhas
│   ├── app.js             4.109 linhas, sem framework
│   ├── estilo.css         1.765 linhas
│   ├── galaxy-background.js
│   ├── field-background.js
│   └── pixel-sprites.js   desenhos das visitas dos fundos animados
│
├── dados\                 arena.db, config.json, controles.json, acervo_autorizado.json
├── jogos\                 pessoais\ (47 pastas de console), turma\, livres\
├── BIOS\                  uma pasta por console (e por região), com LEIA; o ARENA cria e instala
├── retroarch\             emulador, núcleos, saves, states, cheats, system (BIOS)
├── emuladores\            PCSX2\ (obrigatório p/ PS2), Dolphin\ (opcional)
└── backup\                cópias automáticas
```

**Portas:**
- `8777` — servidor ARENA (Python)
- `55435` — partida a dois (RetroArch)
- `55436` — descoberta de colegas na rede (UDP broadcast)

**63 rotas da API** (contadas em 03/10/2026: `grep -oE 'caminho == "/api/[a-z0-9/_-]+"' servidor/arena.py | sort -u`; as 5 novas — `/api/bios`, `/api/bios/conferir`, `/api/bios/pasta`, `/api/jogo/arrumar`, `/api/arrumar/progresso` — só deste computador, conferido em `testes\teste_acesso_de_rede.py`). 8 delas abertas à rede (lista `ROTAS_REDE_EXTERNA`); o resto só aceita pedido deste computador.

---

## 5. Decisões e o porquê delas

Cada linha aqui custou tempo para descobrir. Reverter sem entender o motivo
reintroduz o bug.

### Identificação de jogos

- **A pasta manda, sempre.** Detecção por tamanho falha: Half-Life de PS2
  saiu em CD de 624 MB. A pasta onde o arquivo está é a autoridade.
- **O conteúdo só avisa.** O `identificador.py` lê `SYSTEM.CNF` e o cabeçalho
  CHD; quando discorda da pasta, mostra um aviso e um botão de mover. **Nunca
  move sozinho.** Caso real: Gran Turismo 2 de 660 MB na pasta do Magnavox
  Odyssey 2.
- **CHD:** trilhas CHT2/CHTR = CD; marca DVD = DVD. PSP e PS2 em DVD pequeno
  são indistinguíveis → seletor manual.

### Gráficos e desempenho

- **Nota da GPU é separada da nota geral.** Foi o bug mais caro: o ARENA dava
  perfil pesado a um Ryzen 5 5600G por causa do processador, ignorando que a
  Vega é integrada. Resultado: PSP em 1920×1088, áudio picotado. GPU
  integrada não passa de nota 3.
- **PSP sem xBRZ.** Causava pontos pretos em superfícies transparentes.
- **Dolphin com `async_uber`**, não `sync_uber` — este travava a cada efeito
  novo enquanto compilava shader.
- **N64 com `parallel-rdp` em placa nota ≥ 4.** O `gliden64` é mais rápido mas
  desenha errado o HUD de alguns jogos (Mario Kart 64 é o caso clássico).
  Isso vive em `graficos.json → excecoes`, porque é conhecimento de emulador,
  não de hardware.
- **`global_core_options = "true"` em toda partida** (`arena.gravar_override`).
  Sem isso, cada núcleo lê o próprio `retroarch\config\<Núcleo>\<Núcleo>.opt`
  e **tudo** o que o ARENA escreve em `retroarch-core-options.cfg` (nota da
  GPU, modo modesto, exceções como a do N64) é ignorado em silêncio depois
  da primeira abertura do núcleo. Foi o que aconteceu até 25/09/2026. O
  arquivo do ARENA mantém as opções que o aluno mudou no menu
  (`graficos.opcoes_do_aluno`). Teste: `testes\teste_qual_opcao_de_nucleo_vale.py`.
- **Modo modesto** (`graficos.json → modesto`) é um patamar à parte, não um
  ajuste fino: renderização por processador, resolução nativa, sem PGXP, sem
  filtro. Existe porque mesmo o perfil Desempenho entregava imagem melhor que
  o console original — e isso pesa.

### Controles

- **O automático NÃO mapeia o direcional.** A numeração do navegador (botões
  12–15) não é a do RetroArch: no xinput o direcional é um *chapéu* (`h0up`).
  Escrever "12" ali deixa o direcional mudo. O autoconfig do RetroArch já
  acerta sozinho; o ARENA não tinha o que melhorar, só o que estragar.
- **Tipo `hat`** existe para quem quiser definir na mão. A tela traduz
  botão 12–15 → `h0up/h0down/h0left/h0right`.
- **O console precisa saber que o controle tem analógico.** O PS1 saiu de
  fábrica com controle sem analógico; sem `input_libretro_device_pN = 517`
  os dois analógicos ficam mudos por mais que o controle esteja certo.
- **Perfis cruzam controle × console** (`perfis_controle.json`): arcade stick
  no PS2 não oferece analógico; NES não oferece vibração. Chave que não serve
  fica apagada, não escondida.

### Menu do RetroArch

- **`user_language = 7`** (português do Brasil). Já esteve como 17, que é
  **grego** — o menu abria em alfabeto grego.
- **`menu_driver = rgui` sempre.** Os perfis Equilibrado e Qualidade forçavam
  `ozone`, e todas as opções de tema do ARENA valem só para o rgui.
- **`pause_nonactive = false`.** Ligado, o emulador pausa quando a janela
  perde o foco — e em máquina de escola ela nunca ganha foco de verdade,
  porque o navegador do ARENA fica com ele. Sintoma: o jogo avança **um
  quadro por alt+tab**. Parece defeito grave e é só isto.
- **`input_auto_game_focus` NÃO entra no ultra desempenho.** Ele prende o
  teclado no jogo — e prende o `Esc` junto, deixando o aluno sem menu.
  Virou chave separada (`travar_teclas`), desligada por padrão, com escape
  em `F9`.

### Rede e partida a dois

- **Nem todo núcleo tem netplay, e não dá pra "destravar" editando o `.info`.**
  Descoberto testando de verdade (não só lendo doc): SwanStation (PS1) e
  Mupen64Plus-Next (N64) recusam com "núcleo não tem suporte para Netplay".
  A tentação é editar `savestate_features` no `.info` pra "deterministic" —
  **não fazer isso**: é contornar a própria declaração do núcleo (pode
  dessincronizar no meio da partida) e a próxima atualização do núcleo
  apaga a edição. Solução certa: cadastrar um núcleo ALTERNATIVO que já
  declare netplay oficialmente, só pra quando for Jogar Junto — PS1 usa
  PCSX ReARMed nesse caso (`consoles.json → core_netplay`), continua
  SwanStation pra jogar sozinho (mais fiel, mas sem essa opção). N64 não
  tem alternativa boa: fica documentado como limite, não escondido.
- **Trocar de núcleo resolve a conexão, mas não o memory card sozinho.**
  O PCSX ReARMed gerencia o cartão de memória por fora da SRAM padrão do
  RetroArch, então o convidado não recebe automaticamente o cartão de quem
  hospeda — ganha um cartão em branco isolado. Confirmado testando de
  verdade, não só lendo doc. Detalhe e pendência em "Estado atual".
- **A ordem dos argumentos importa.** Estava
  `retroarch -L core JOGO --appendconfig X --host` e o `--host` não surtia
  efeito: cada máquina abria o jogo sozinha. Agora as opções vêm **antes** do
  arquivo do jogo, e a porta vai explícita (`--port 55435`).
- **O código do aparelho nasce da máquina**, não do `config.json`. Copiar a
  pasta para 30 pen drives dava 30 ARENAs com o mesmo código — cada um achava
  que o outro era ele mesmo, e a sincronização recusava tudo. Deriva de nome
  da máquina + usuário + MAC. Se ainda assim dois colidirem (laboratório com
  imagem clonada), o ARENA percebe e troca o dele sozinho.
- **Adaptadores virtuais vão para o fim da lista e vêm marcados.** WSL,
  Hyper-V, VirtualBox e Wi-Fi Direct aparecem como "rede local" e nenhum
  colega alcança. Era a causa de o aluno copiar o endereço errado.
- **Repasse (MITM) só para jogar de casa.** Na escola, direto. O repasse
  adiciona atraso e só existe porque a internet residencial brasileira usa
  CGNAT.
- **A sincronização marca o que já foi enviado pelo número de chegada
  (`seq`), nunca pela data.** Com a data, notebook de relógio errado tinha
  os recordes invisíveis para sempre, e partida mais longa que o intervalo
  do vigia nunca era enviada (a sessão nasce no começo e fecha no fim).
  Toda gravação de placar/sessão passa por `inserir_placar`,
  `abrir_sessao`, `encerrar_sessao`, `inserir_sessao_recebida` — INSERT
  solto sem `seq` não sincroniza.
- **`network_cmd_enable` sempre `false`** (override de toda partida e
  `graficos.VALORES_OBRIGATORIOS`). Ligado, o RetroArch escuta comandos em
  `0.0.0.0:55355`, e como o `retroarch.exe` é liberado no Firewall para o
  Jogar Junto, qualquer colega da rede fecharia o jogo de outro. Teste que
  precisar de comando (a matriz) liga só no override dele, com
  `config_save_on_exit = "false"`.
- **Multitap precisa de `netplay_max_connections = 4`.** O padrão do
  RetroArch é 3 convidados; o 5º jogador era recusado.
- **Tipo de porta (`input_libretro_device_pN`) vai no `.rmp` da partida,
  não só no `--appendconfig`.** O RetroArch ignora esse valor vindo do
  arquivo extra (provado com controle na mão). Conferir o arquivo da
  partida não basta: conferir o `.rmp` (o teste por console faz isso).
- **Botão de controle que o aluno não definiu vai `nul` em toda partida.**
  Número velho no `retroarch.cfg` (de outro tipo de controle) passa por
  cima do reconhecimento automático. Tecla de teclado continua somando.
- **Memory card do PS1 é um por jogo (`Libretro`), de propósito.** O
  "compartilhado" nunca chegou a valer, e todo save existente está no
  cartão de cada jogo; ligar agora esconderia esses saves.
- **A mala do pen drive** (`ARENA-troca.json` na raiz da mídia) sincroniza
  sem rede nenhuma. Idempotente por UUID: passar dez vezes não duplica.
- **Descoberta por UDP broadcast** na 55436, a cada 5 s. O "sou eu?" usa
  endereço+porta, não o código — senão máquinas clonadas se ignoram.

### Limites que não dá para contornar

Diga isso ao Rafael em vez de tentar:

- **Tela dividida não separa.** O console gera **um** sinal de vídeo com as
  duas metades dentro. Twisted Metal 2 a dois mostra a mesma tela dividida nas
  duas máquinas. Jogo de tela única (luta, esporte) fica perfeito.
- **O menu do PCSX2 é do PCSX2.** Outro programa, tela própria em C++.
  Injetar código seria frágil e barrado pelo antivírus. O que dá é **escrever
  a configuração dele antes de abrir** — e é o que o ARENA faz (controle,
  analógicos, vibração, 4 das 7 teclas iguais).
- **O ultra desempenho não tranca o Windows.** Não impede `Ctrl+Alt+Del`.
  Exigiria senha de administrador e driver próprio.
- **Partida a dois só pelo RetroArch.** Plataforma com emulador externo
  presente não oferece o botão — e o servidor recusa por segurança.
- **PS2 pela rede: implementado como opcional, não como recurso pronto pra todo mundo.** O PCSX2 emula a placa de rede do PS2 de verdade (DEV9) e suporta o "system link" original de ~56 jogos — não é netplay de emulador, é o jogo conversando pela rede do mesmo jeito que faria em dois PS2 físicos ligados por cabo. O modo que funciona pros dois lados (hospedar E entrar) precisa do driver Npcap/WinPcap, que pede administrador pra instalar — o ARENA nunca instala isso sozinho, só detecta se já existe (sem admin nenhum pra checar) e mostra em Ajustes → Emuladores, com link oficial pra quem quiser tentar. Sem o driver, ainda dá pra **entrar** (modo "Sockets"). Detalhe completo em "Estado atual". Lista de jogos compatíveis é curta de propósito — só cresce testando com jogo real.

---

## 6. Padrões de código

- **Gravação atômica em tudo:** temporário com nome único por thread →
  `os.replace()`. Pen drive é arrancado no meio da escrita.
- **Travas:** `TRAVA_JOGO` para um jogo por vez, `TRAVA_VIZINHOS` para a
  descoberta. O checker e o setter ficam na mesma trava.
- **Modo econômico** liga sozinho em máquina fraca ou mídia removível:
  vigia de rede a cada 60 s (não 20), backup a cada 15 min, cache de 15 s,
  fila de conexões menor. Cartão SD tem número finito de gravações.
- **Config antiga não derruba nada:** chave que não existe mais é filtrada ao
  carregar.
- **Validação em toda entrada.** Já barrados em teste: `'; DROP` em cheat,
  `../dados/config.json` na rota de capa, host não autorizado no acervo,
  item de 99 GB, injeção de nova linha no mapeamento.

---

## 7. Testes

Atualizado em 02/10/2026 (a versão antiga desta seção descrevia baterias
`t_*.py` que não existem mais).

| O quê | Onde | Quando rodar |
|---|---|---|
| **Bateria** (203 testes, ~7 s) | `servidor\tests\run.py` (ou `RODAR_TESTES.bat`) | Antes de todo commit |
| **Scripts de teste** (90 `teste_*.py`) | `testes\` | O da área mexida; cada um explica no topo o achado que o criou |
| **Rodada completa** (~1h30) | `ferramentas\rodada_final.py [pedaço do nome]` | Antes de versão nova; em segundo plano, nada na porta 8777 no meio |
| **Orçamentos no modo alvo** (~8 min) | `testes\teste_orcamentos_modo_alvo.py` (2ª pergunta do `RODAR_TESTES.bat`) | Depois de mudança que pese no processador/memória |
| **Versão dos alunos** | `ferramentas\montar_versao_alunos.py --atualizar` (a `..\ARENA-alunos` está em uso pelo Rafael: troca só o programa); `--com-bios` só monta do zero, e recusa pasta em uso | Depois de qualquer mudança |

O que os testes conferem de verdade: o RetroArch abrindo jogo real
(`--max-frames-ss`, foto da tela), Jogar Junto com dois RetroArch em
127.0.0.1, a tela no Edge sem janela (`testes\tela_sem_janela.py`, inclusive
4K), a API sob ataque (`fuzz_rotas`, `teste_quebrar_api`), dados tortos,
disco cheio, banco corrompido, pasta movida, caminho comprido.

**Padrões que valem para todo teste novo** (cada um nasceu de um estrago):
- ARENA isolado numa **subpasta** do temporário (`mkdtemp()/ARENA`): a mala
  do pen drive vai para a pasta de cima.
- Quem abre o RetroArch usa `testes\protege_cfg.rodar(main)`; a rodada ainda
  confere o `retroarch.cfg` e os arquivos de `dados\` de verdade antes e
  depois de cada teste.
- Apagar pasta temporária com `testes\limpeza.apagar_pasta` (somente
  leitura e arquivo preso); a rodada aponta o teste que esquecer pasta no Temp.
- Jogo de verdade por `testes\jogos_de_teste.achar` (o professor reorganiza
  as pastas; o teste não pode pular calado).
- Medida de desempenho só vale com a janela do jogo à frente, na tomada e com
  a saída de som normal (fone sem fio desligado segura o ritmo).
- Ferramenta de investigação que pede argumentos fica em
  `rodada_final.FORA_DA_RODADA`, com o motivo.
- A cópia isolada (`fuzz_rotas.preparar_ambiente`, usada pelo
  `teste_servidor_que_cai.preparar_copia`) leva o `dados\` DE VERDADE: o que
  o ARENA anotou lá (ex.: `bios_conferidas.json`) vale na cópia. E o
  `teste_servidor_que_cai.pedir` devolve `{}` no erro (sem a mensagem).
- Script Python com barra invertida (caminho do Windows) vai pelo Write,
  nunca por heredoc no Bash daqui (`\\` vira `\`).

---

## 8. Histórico de bugs (para não repetir)

| Bug | Sintoma | Causa |
|---|---|---|
| Comentário Python no JS | Tela vazia, "lendo…" para sempre | `#` não é comentário em JavaScript |
| Menu em grego | Menu ilegível | `user_language = 17` é grego, não pt-BR |
| Alt+tab quadro a quadro | Jogo parado | `pause_nonactive = true` |
| Esc morto no ultra | Sem menu no jogo | `input_auto_game_focus` prende todos os atalhos |
| Netplay não conecta | Cada um abre sozinho | Jogo antes do `--host` na linha de comando |
| Sincronização recusada | "É o próprio computador" | Mesmo código de aparelho em pen drives clonados |
| Direcional mudo | Cruz não funciona | Botão 12–15 em vez de `h0up` |
| Analógico mudo no PS1 | Só o direcional anda | Falta `input_libretro_device = 517` |
| PSP travando | Áudio picotado | Nota da GPU herdada do processador |
| Endereço errado | Colega não alcança | Adaptador virtual listado como rede local |
| `montar_conquistas` | Erro 500 | Chamava `abrir_banco()`, o nome é `banco()` |
| Acervo de 99 GB | Pen drive entupido | Cadastro não validava tamanho |
| Favoritos não gravavam | Estrela acendia e sumia ao reabrir | Tela enviava a lista inteira; servidor só aceitava um por vez |
| Log fora da pasta | Teste não achava o log; leitura bloqueada | `retroarch.cfg` com caminho absoluto da pasta antiga (OneDrive) — corrigido, `corrigir_caminhos_retroarch_cfg()` roda a cada abertura |
| Cache do RetroArch fora da pasta | Nada visível — só aparecia auditando o `.cfg` | `cache_directory` nunca foi setado; o RetroArch usa a pasta Temp do Windows quando ninguém diz o contrário |
| Netplay de PS1 recusado | "Núcleo não tem suporte para Netplay" | SwanStation declara savestate "basic" — resolvido usando PCSX ReARMed (declara "deterministic") só no Jogar Junto |
| Multitap não ligava | Só 2 jogadores; 3º controle não mexe nada | RetroArch ignora `input_libretro_device_pN` do `--appendconfig` — vai num `.rmp` da partida |
| Start no R3 | Botões do controle "confusos" | Números DirectInput esquecidos no `retroarch.cfg` passavam por cima do XInput |
| Metal Slug X com personagens de cor estranha | Só no fliperama; demonstração parecia certa | `mslugx.zip` danificado (parte `MSX_C3.rom` não confere com o CRC); o FBNeo carrega assim mesmo — `servidor\integridade.py` confere cada zip uma vez |
| "O fliperama não é reconhecido" | Jogo não abre, cartão calado | Nome de título (`The King Of Fighters 2002.zip`) no lugar do romset (`kof2002.zip`) — o cartão agora diz o nome certo |
| 209 cópias em `backup\` | O rodízio de 3 nunca apagava | `saves\.netplay` é somente leitura; `rmtree(ignore_errors=True)` desistia calado |
| `cache_directory` 5 vezes no `retroarch.cfg` | Uma linha a mais por abertura | O RetroArch grava `:\cache`; a correção só reconhecia `C:\...` |
| 128 Edge invisíveis vivos (1,8 GB) | Memória sumindo durante os testes | `tela_sem_janela` matava só o lançador do Edge — agora `Browser.close` |
| "35 GB em temporários" | Alarme falso no VERIFICAR | Arquivo esparso do RPCS3 (diz 32 GB, ocupa quase nada) somado pelo tamanho de fachada |
| SNES a 52 FPS no medidor | Parecia máquina lenta | Headset sem fio desligado segurando a sincronia pelo som — o COLETAR agora separa |
| Memória do servidor 64,4 MB (teto 64) | Reprovado no modo alvo | Índice dos 37 mil títulos do MAME guardado em memória (+13 MB) |
| Alças do Windows subindo sem parar (181.570 em 3 min) | Nada visível; num dia de aula o Windows acabaria recusando | `joyGetPosEx` contava os controles a cada pedido e vaza com o controle desligado — agora conta só ao abrir o jogo, pelo Raw Input + XInput |
| Servidor some "sem motivo" | Tela parada; fechar e abrir tudo | Python caindo (0xC0000005 no ntdll, 26/09) e, no Windows 10, clique na janela preta (Edição Rápida) travando quem escreve nela — `janela_preta.py`, reabertura no `ARENA.bat`, tela que volta sozinha |
| VERIFICAR "tudo presente" sem 5 módulos | O ARENA nem abria | Lista `PROGRAMA` parada no tempo — a bateria agora compara com os imports do `arena.py` |
| Crash Nitro Kart a 3: "P1" em blocos, lixo no mapa | Só no PS2 | Mipmapping e trilinear desligados na tela do PCSX2 (o próprio PCSX2 avisava) — o ARENA grava os valores seguros |
| "Mais leve" do PS2 mais lento | Pré-carga de texturas "Nenhuma" | O PCSX2 diz que a completa "melhora o desempenho na maioria dos jogos" |
| N64 em 2x depois de sair da TV 4K | Imagem pesada na tela comum | Chave da tela 4K não contava como do ARENA e ficava como "mudada pelo aluno" |
| Biblioteca: "Mario" traz coisa aleatória | Jogos de DOS que só citam a palavra | Busca olhava a descrição — agora só o título |
| Jogo baixado sem console | "Precisa escolher o console" | Ia para `livres\Internet Archive` (a pasta não diz o console) — agora `livres\MS-DOS` |
| Fliperama "não roda e o ARENA diz que está tudo certo" | O RetroArch só diz "Falha ao carregar o conteúdo" | O que falta só aparece no registro do emulador — `motivo_do_erro.py` lê e explica ao voltar do jogo |
| MAME não acha a BIOS do Neo Geo | "000-lo.lo NOT FOUND" com a BIOS na pasta | O MAME só procura `neogeo.zip`, e só na pasta do jogo; a montagem levava `neogeo.mame.zip` e o guia mandava pôr em `retroarch\system` |
| Kinst não abre no MAME | "unknown option: kinst" | `kinst.zip` dentro da pasta `kinst`, junto do `.chd` — o zip vai na pasta de cima |
| Crash Nitro Kart com 2 controles só na versão dos alunos | Multitap ligado no PCSX2 desligava sozinho | O 4 estava só no `dados\jogadores.txt` de quem montou (dado de usuário) — os jogos testados agora vêm em `consoles.json → jogadores_por_jogo` |
| Capa baixada e a lista não acha | Jogo sem capa com a capa na pasta | O banco grava `&` `:` etc. como `_`; a lista procurava o título cru |
| Montar a versão dos alunos apagaria os jogos do Rafael | (evitado) | O montador fazia `rmtree` da pasta sem olhar — agora recusa pasta em uso; `--atualizar` troca só o programa |
| KOF 2002 recusado pelo MAME e pelo FBNeo, com tudo "certo" | "Falha ao carregar o conteúdo" | Zip decriptado de emulador antigo (`kof2k2_*.rom`) — vira o `kof2k2fd` do FBNeo, com o M1 na pasta de correções (`converter_fliperama_decriptado.py`) |
| Pasta avulsa em `backup\` ocupando vaga de cópia | (evitado) | O rodízio contava qualquer pasta, não só as de data |
| KOF 2002 com a capa do bootleg | Capa de outra versão | Desempate pelo nome mais curto; agora a do original ganha |
| BS F-ZERO sem capa | Nenhum nome batia com o banco de capas | Reconhecido pela marca (CRC) no banco de dados do RetroArch |
| Crash Bandicoot 3 não abria | Na pasta PS2 | Era de PS1 (SCES-01420); o PCSX2 não abre jogo de PS1 |
| Sega CD e Saturn "prontos" sem BIOS | O jogo não abria ("Unable to open CD BIOS") | O console só ficava amarelo com a pasta system vazia — `bios.falta_para_o_console` |
| BIOS baixada em pacote (zip dentro de zip) não valia | O emulador só lê a BIOS solta, com o nome exato | `bios.organizar` acha pela marca e instala com o nome certo |
| BS F-Zero Deluxe pedia a BIOS à toa | Abre sem o BS-X | O aviso olhava o "BS" do nome — agora o cabeçalho, como o Snes9x |
| .chd solto na pasta Arcade: "falta o arcade.zip" | Instrução errada | O nome da pasta do console virava o romset |
| Jogo de PS1 descompactado sumia da lista | Pasta ao lado do .zip de mesmo nome | A regra da pasta de disco do fliperama valia em todo console |
| Prateleiras da pasta BIOS vazias numa cópia do ARENA | "Já copiei" herdado do dados\ | Pasta BIOS recém-criada ignora a anotação antiga |

---

## 9. Como trabalhar neste projeto

1. **Rode a auditoria depois de mexer na tela:** `python auditoria.py`.
   Botão novo sem documentação é divergência.
2. **Rode a bateria antes de empacotar.** Teste que falha por expectativa
   antiga se corrige no teste, com o motivo comentado — não se apaga.
3. **Documento junto com o código.** Recurso sem leia-me não existe para o
   aluno.
4. **Ao remover algo, confira se não é a única forma de fazer aquilo.** A
   fusão de setembro perdeu a chave "Aceitar conexões da rede" — sem ela
   ninguém conecta com ninguém.
5. **Antes de investigar um relato, confira a versão.** O carimbo está no
   topo da tela e na janela preta. Metade dos problemas relatados já estava
   corrigida numa versão mais nova.

---

## 10. Pendências conhecidas

- [x] Modo modesto (e "prefira menos movimento") agora desligam os fundos
      animados de verdade (Fase 2 da auditoria, 23/09/2026) — o loop de
      animação parava de desenhar mas continuava se reagendando pra
      sempre; agora para de vez. **Ainda falta** confirmar quanto isso
      pesava num Celeron de 2 núcleos de verdade — não deu pra medir em
      navegador automatizado (aba sempre "hidden"). Fica pro roteiro
      manual de sala da Fase 4/6 da auditoria.
- [x] Download real do acervo testado com internet (25/09/2026,
      `testes\teste_acervo_download_real.py`). O acervo desta pasta está vazio.
- [x] Chaves de BIOS e memory card do `swanstation` conferidas contra o
      próprio `.dll` e o `.opt` gerado pelo RetroArch (25/09/2026): as
      `duckstation_*`, `swanstation_BIOS_Path` e `..._Directory` não
      existiam — removidas; corrigidas para as chaves reais.
- [ ] Validar a partida pela internet (repasse) entre operadoras diferentes.
- [ ] Confirmar que `parallel-rdp` resolve o HUD do Mario Kart 64 em placa
      capaz.

---

## 11. Estilo de resposta esperado pelo Rafael

Direto e pragmático. Sem introdução, sem cortesia, sem repetir o que ele
disse. Solução ou primeiro passo primeiro.

Quando a teoria for necessária: **tese central → analogia simples → prática**.

Diagnóstico de hardware e software: **isolamento de falhas por eliminação**,
do componente mais simples ao mais complexo. Nada de troca cega de peça.

E o mais importante: **quando algo não é possível, diga que não é possível**,
com o motivo técnico. Ele prefere saber na hora a descobrir na aula.
