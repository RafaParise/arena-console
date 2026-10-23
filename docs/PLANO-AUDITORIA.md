# Plano da Auditoria Completa do ARENA

> Pedido do Rafael, salvo aqui sem resumir (conforme instrução explícita),
> para permitir continuar a auditoria depois de um `/clear`. Ver seção
> "Estado atual" do `CLAUDE.md` pra saber em que fase a auditoria está.
>
> **Rodada atual: auditoria 4** (a última seção deste arquivo). Relatórios:
> auditoria 4 em `RELATORIO-AUDITORIA-4.md`, auditoria 3 em
> `RELATORIO-QUALIDADE.md`, auditoria 2 em `RELATORIO-AUDITORIA-2.md`,
> auditoria 1 em `RELATORIO-AUDITORIA-1.md`.

---

## AUDITORIA COMPLETA DO ARENA: TESTES, LIMPEZA E OTIMIZAÇÃO

Antes de implementar a IA, quero o ARENA perfeito: testado como um aplicativo profissional, sem código inútil, leve, portátil, com as partidas entre amigos funcionando bem nos notebooks da escola, e fácil de entender até para quem tem dificuldade de aprendizagem.

Leia o CLAUDE.md inteiro antes de começar. Trabalhe em fases, uma por vez: plano, minha aprovação, execução, testes, commit.

### PÚBLICO E MÁQUINAS
- Alunos menores de idade de escola pública, incluindo alunos com dislexia, TDAH, deficiência intelectual ou pouca experiência com computador.
- A maioria dos notebooks tem até 4 GB de RAM (Celeron dual-core, sem SSD, sem permissão de administrador). Alguns são melhores (i5 com 15 GB, Ryzen 5600G).
- Redes: Wi-Fi comum, Wi-Fi da escola (que pode isolar os aparelhos entre si e pode ter página de login), ponto de acesso do celular, cabo direto e internet entre casas.

### REGRAS QUE NÃO PODEM SER QUEBRADAS
1. Todo o trabalho num ramo novo do git, chamado auditoria. O ramo principal só muda quando eu aprovar a junção.
2. Nunca apague jogos, saves, BIOS, núcleos, memory cards nem a pasta dados\ do usuário. Nunca edite as duas pastas originais (a versão antiga e o ARENA-remake--master).
3. Nada é removido sem antes estar numa lista que eu aprovei, com a prova de que não é usado (quem chama, onde aparece, o que quebra se sair).
4. Toda afirmação de "ficou mais leve" ou "ficou mais rápido" precisa de número: medição antes e depois.
5. Portátil: sem instalação, sem administrador e sem pip. As ferramentas de teste são escritas em Python puro, em ARENA-unificado\testes\ ou ARENA-unificado\ferramentas\.
6. Arquivos temporários de teste ficam numa pasta própria, ignorada pelo git e apagada no fim de cada teste.
7. Os testes existentes do ARENA (RODAR_TESTES.bat e o que mais houver) rodam antes de tudo, como referência, e de novo no fim de cada fase. O resultado nunca pode piorar.
8. O que só pode ser testado com aparelhos de verdade (5 notebooks, o Wi-Fi da escola, celulares) vira um roteiro de teste manual, passo a passo, para eu fazer em sala. Não adivinhe o resultado.
9. Tudo em português do Brasil, inclusive a descrição curta de cada comando.
10. Se uma fase ficar grande demais, divida-a e me avise. Não pule etapas.

---

### FASE 0 - LINHA DE BASE E INVENTÁRIO (nenhuma mudança no código)
- Salve este pedido inteiro, sem resumir, em ARENA-unificado\docs\PLANO-AUDITORIA.md, e cite esse arquivo na seção "Estado atual" do CLAUDE.md. É ele que permite continuar a auditoria depois de um /clear.
- Crie o ramo auditoria e rode os testes de referência.
- Meça e anote:
  tamanho total do pacote, sem jogos;
  linhas de código por arquivo;
  tempo de abertura do ARENA até a tela ficar pronta;
  uso de processador com o ARENA parado (o ideal é perto de zero);
  memória RAM usada pelo servidor e pela tela;
  quantas gravações em disco ele faz por hora parado (cartão SD e pen drive se desgastam);
  quantas threads e temporizadores ficam rodando;
  quais portas ficam abertas e se escutam só no computador ou na rede toda.
- Faça o inventário completo:
  todos os arquivos;
  todas as rotas do servidor e quem as chama;
  todas as telas, botões e chaves da interface e a rota que cada um usa;
  todas as chaves de configuração e onde são lidas;
  todos os serviços que ficam rodando em segundo plano, com o motivo de cada um;
  tudo o que depende de internet.
- Grave o resultado em ARENA-unificado\docs\RELATORIO-QUALIDADE.md, na seção "Antes".
- Pare e me mostre um resumo.

### FASE 1 - VARREDURA E LIMPEZA DO CÓDIGO (DEBLOAT)
- Procure:
  funções nunca chamadas;
  rotas que a tela não usa;
  botões que chamam rotas que não existem;
  chaves de configuração que ninguém lê;
  arquivos duplicados ou que sobraram das duas versões originais;
  código de funções que já foram removidas (por exemplo: gravação de vídeo e transmissão, "só assistir", DuckStation, tecla Scroll Lock; confira, não presuma);
  serviços e temporizadores que não precisam existir ou que rodam com frequência maior que o necessário;
  documentação que fala de funções que não existem mais.
- Procure também código errado: exceções engolidas em silêncio, arquivos que não são fechados, gravações que não são atômicas, caminhos absolutos, textos em inglês na tela.
- Monte a lista de remoções e correções, cada item com a prova. Pare e espere minha aprovação.
- Depois de aprovado: aplique, rode todos os testes e faça commit.

### FASE 2 - LEVEZA E DESEMPENHO
- Com o ARENA parado, uso de processador perto de zero. Nada de consulta repetida sem necessidade.
- Menos gravações em disco: registros (logs) com limite de tamanho e rodízio.
- Tela: remova CSS e JavaScript não usados e confira o tamanho das imagens.
- Os fundos animados precisam respeitar o computador fraco: desligados no modo modesto e quando o Windows pede menos animação. Esta é uma pendência antiga: medir quanto pesam num Celeron.
- Teste de estresse do catálogo: gere 5.000 arquivos de jogo falsos, espalhados por vários consoles, numa pasta temporária. Meça o tempo de indexação e confirme que a tela continua respondendo. Depois apague tudo.
- Registre os números de antes e depois no relatório.

### FASE 3 - TESTES DO SERVIDOR E DA API (OFFLINE E ONLINE)
- Teste todas as rotas com:
  dados corretos;
  dados faltando;
  tipo errado;
  texto gigante;
  acentos e emojis;
  tentativas de sair da pasta ("..\..\");
  pedidos repetidos muito rápidos.
- Toda resposta de erro precisa ter uma mensagem simples, que diga o que aconteceu e o que fazer.
- Concorrência: 50 pedidos ao mesmo tempo, sem travar e sem corromper arquivos.
- Teste de longa duração: o servidor ligado por horas (ou acelerado), abrindo e fechando jogos, sem crescer em memória nem em arquivos abertos.
- Segurança:
  a) quais rotas qualquer computador da rede consegue chamar. Na rede da escola, outro aluno não pode mudar as minhas configurações, apagar os meus saves nem mandar abrir jogos no meu computador. Só o que a partida e a sincronização precisam pode ficar aberto à rede;
  b) um site qualquer aberto no navegador não pode mandar comandos para o servidor local do ARENA (proteção contra pedidos de outra origem e contra DNS rebinding).
- Sem internet, tudo o que é local funciona 100%.
- Com internet ruim, confira: DNS que falha, rede lenta, tempo esgotado e a página de login do Wi-Fi da escola devolvendo HTML no lugar dos dados esperados. As funções online (acervo, busca no Internet Archive, repasse do Jogar junto) precisam falhar com uma mensagem clara, nunca travando nem corrompendo nada.
- Acervo: arquivo baixado com código de verificação (SHA-256) errado tem que ser recusado.

### FASE 4 - JOGAR JUNTO: O CORAÇÃO DO ARENA
Parte automática, num computador só:
- Abra um hospedeiro e até 4 convidados (5 RetroArch ao mesmo tempo), cada um com sua própria configuração, seus saves e sua pasta temporária, todos conectando no próprio computador.
- Jogo de 5 jogadores: Super Bomberman de Super Nintendo com o adaptador Multitap. Descubra como o ARENA deve ligar o Multitap sozinho nos jogos que aceitam mais de 2 jogadores, e qual o limite de conexões do Jogar junto (o RetroArch tem uma configuração de número máximo de conexões: confira o nome e o padrão na documentação atual e ajuste para comportar 5 jogadores). Se o jogo não estiver na pasta, me peça.
- Meça: processador e memória do hospedeiro, ping, avisos de dessincronia, tempo para cada convidado entrar.
- Se ainda não houver jeito confiável de apertar botões por programa, teste com os jogadores parados (o Jogar junto troca dados a cada quadro mesmo assim) e deixe o teste com botões para o roteiro de sala.
- Crie um simulador de rede ruim em Python puro: um intermediário entre o hospedeiro e um convidado que acrescenta atraso (50, 100 e 200 ms) e perda de pacotes (1% e 5%). Descreva o que o jogador sente em cada caso.
- Situações de sala de aula:
  convidado que cai e volta;
  hospedeiro que sai no meio;
  convidado que entra com a partida já começada;
  sexto jogador tentando entrar (precisa receber uma mensagem clara);
  duas partidas diferentes na mesma rede ao mesmo tempo.
- Descoberta de colegas com muitos aparelhos: simule 30 computadores anunciando ao mesmo tempo. A lista na tela precisa continuar clara, e o processador, baixo.
- Sincronização e mala do pen drive: o mesmo recorde vindo de dois lugares, relógios diferentes entre os notebooks e pen drive em FAT32 (que só guarda a hora de 2 em 2 segundos).

Parte dos notebooks da escola (o que precisa de diagnóstico no ARENA e no PARTIDA.bat, com mensagem simples):
- Firewall do Windows bloqueando a entrada de conexões, porque a rede está marcada como pública e o aluno não é administrador. Confira como o Windows se comporta para usuário comum. O ARENA precisa perceber, explicar e oferecer uma saída (outro computador hospeda, ou repasse pela internet, em que os dois lados só fazem conexões de saída).
- Wi-Fi que isola os aparelhos entre si.
- Ponto de acesso de celular Android e iPhone (as faixas de endereço variam).
- Cabo direto sem roteador (endereço 169.254).
- Adaptadores virtuais e VPN.
- Endereço que muda no meio da aula, notebook que dorme e acorda, Wi-Fi que cai durante a partida.

Multiplayer local (um computador, vários controles):
- Até 4 jogadores no mesmo computador, com o 007 de Nintendo 64 (GoldenEye) e outro jogo de 4 jogadores. Confira o mapeamento de 4 controles, e de teclado junto com controle.

- Ao fim da fase, escreva o roteiro manual para eu testar em sala com 5 notebooks de verdade: o que ligar, em que ordem, o que conferir e o que anotar.

### FASE 5 - MATRIZ DE JOGOS
- Para cada console que tiver jogo na pasta:
  o jogo abre e mostra imagem (se o RetroArch tiver opção de rodar um número fixo de quadros e salvar uma captura de tela, use-a para automatizar; confira na documentação);
  o controle funciona;
  salvar e carregar estado funciona;
  o save do próprio jogo funciona;
  os cheats funcionam;
  e os quadros por segundo no modo modesto e no normal.
- Pendências antigas que entram aqui:
  PS1: uma partida completa pelo Jogar junto até salvar no memory card, para confirmar que o memory card de quem hospeda fica certo;
  PS2: testar o seletor de qualidade do PCSX2 com as ISOs que estão na pasta;
  PS3 e Xbox 360, se houver jogo.
- Resultado: uma tabela console × teste no relatório, com o que passou, o que falhou e o porquê.

### FASE 6 - PORTABILIDADE E ROBUSTEZ
- Pen drive com letras diferentes, caminho com espaços, acentos e muito longo, pasta só de leitura e disco cheio.
- FAT32, exFAT e NTFS. No FAT32, nenhum arquivo passa de 4 GB: o ARENA precisa avisar antes de alguém copiar uma ISO grande.
- Queda no meio da gravação: mate o processo durante a gravação de save, config e banco. Nada pode ficar corrompido, e o VERIFICAR.bat precisa consertar o que der.
- Configuração, JSON e banco corrompidos de propósito: o ARENA abre mesmo assim e explica.
- Notebook sem driver de vídeo (adaptador de vídeo básico da Microsoft): o RetroArch precisa escolher um modo de vídeo que funcione.
- Windows 10 e 11. Windows de 32 bits: detectar e explicar.
- Antivírus e SmartScreen bloqueando os .bat de um zip baixado: explicar no LEIA-ME como liberar.
- Procure no código qualquer coisa que exija administrador (registro do sistema, netsh, serviços do Windows) e remova ou substitua.

### FASE 7 - CLAREZA PARA TODOS (USABILIDADE E ACESSIBILIDADE)
- Revise cada texto da tela e dos guias em linguagem simples: frases curtas, uma ideia por frase, palavra técnica só com explicação, e um exemplo lúdico do dia a dia sempre que o assunto for difícil (por exemplo: "hospedar a partida é como emprestar a sua casa para a festa: os amigos vêm até você").
- Mensagem de erro sempre com duas partes: o que aconteceu e o que fazer agora.
- Faça o passo a passo, clique por clique, com estas pessoas, e conte quantos passos e quantas decisões cada tarefa exige:
  Ana, 11 anos, com dislexia;
  Pedro, 13 anos, com TDAH;
  Lucas, com deficiência intelectual leve;
  Dona Maria, que nunca usou computador;
  o professor com 5 minutos antes da aula.
- As tarefas:
  abrir o ARENA e jogar;
  salvar e continuar depois;
  jogar com um amigo em outro notebook;
  resolver "meu amigo não aparece na lista";
  levar o progresso no pen drive.
- Navegação só por teclado, contraste, tamanho de letra, ícone sempre com texto, nada de parede de texto, menos animação quando o Windows pedir.
- Proponha as mudanças, espere minha aprovação e depois aplique.

### FASE 8 - RELATÓRIO FINAL E ENTREGA
- Complete o RELATORIO-QUALIDADE.md com:
  a seção "Depois" e uma tabela antes × depois com todos os números da Fase 0;
  o que foi removido;
  o que foi corrigido;
  o que ainda falta, com honestidade;
  e os roteiros manuais de sala de aula.
- Atualize os guias 1 a 6, o LEIA-ME.md e o CLAUDE.md ("Estado atual").
- Rode tudo uma última vez. Pare e espere minha aprovação para juntar o ramo auditoria ao principal.

Ao fim de cada fase: diga exatamente como testar, faça commit no ramo auditoria e atualize a seção "Estado atual" do CLAUDE.md.

Comece só pela Fase 0.

---

## Autorização de continuidade (registrada aqui, fora do pedido original)

Depois de ler as 8 fases completas, o Rafael autorizou: *"agora sim pode
começar por favor, e a cada rodada que finalizar pode continuar sozinho
até realizar a auditoria completa se possível"*.

Leitura adotada: isso libera seguir de fase em fase sem perguntar "posso
continuar?" a cada uma — mas não anula os pontos em que o PRÓPRIO plano
acima diz "pare e espere minha aprovação" (Fase 0 - resumo; Fase 1 -
lista de remoção; Fase 7 - mudanças de texto; Fase 8 - juntar ao
`main`). Esses continuam sendo paradas de verdade.

## Progresso da auditoria

- [x] Fase 0 — Linha de base e inventário (23/09/2026)
- [x] Fase 1 — Varredura e limpeza (debloat) (23/09/2026)
- [x] Fase 2 — Leveza e desempenho (23/09/2026)
- [x] Fase 3 — Testes do servidor e da API (24/09/2026)
- [x] Fase 4 — Jogar Junto (24/09/2026)
- [x] Fase 5 — Matriz de jogos (24/09/2026)
- [x] Fase 6 — Portabilidade e robustez (24/09/2026)
- [x] Fase 7 — Clareza para todos (24/09/2026)
- [x] Fase 8 — Relatório final e entrega (25/09/2026) — aprovada pelo Rafael e juntada ao `main` em 25/09/2026 (commit `2633704`); revisão pós-auditoria no mesmo dia; rodada final completa: 35 de 35

---

## Auditoria 2 (25/09/2026) — pedido do Rafael, sem resumir

> "Agora no esforço ultracode, refaça a auditoria completa, leia as
> instruções enviadas anteriormente e siga como recomendado, inatruções,
> passo 0 até o 8, mas exatamente com as mesmas escolhas e decisões que fiz
> nessa primeira auditoria, mas revise também o testador de maquinas e suas
> especificações e garanta que ele possa identificar todas as barreiras
> desses computadores que deixam eles lentos como bloatwares, serviços e
> recursos desnecessários, telemetria e etc... Se tiver algum problema o
> ARENA precisa saber identificar para recomendar ação"

**Leitura adotada ("as mesmas escolhas e decisões"):** na primeira
auditoria o Rafael (1) autorizou seguir de fase em fase sozinho, (2)
aprovou a lista de remoção da Fase 1 em bloco, (3) aprovou todas as
mudanças da Fase 7 ("fazer todos"), (4) aprovou juntar ao `main`. Nesta
segunda rodada essas quatro decisões valem de novo: as paradas do plano
viram registro no relatório, não pergunta. Continuam valendo as 10 regras
do plano — em especial: nada removido sem prova, nada de dado do aluno
apagado, número real para toda afirmação de "mais leve/rápido", roteiro
manual para o que só a sala confirma.

**Ramo:** `auditoria`, avançado (sem perder nada) até o `perfil-alvo`, que
é o `main` + as ferramentas de coleta.

**Relatório desta rodada:** `docs\RELATORIO-AUDITORIA-2.md` (o da primeira,
hoje `RELATORIO-AUDITORIA-1.md`, fica como histórico).

**Extra pedido nesta rodada:** o testador de máquinas passa a identificar
as barreiras que deixam o computador lento (inicialização, bloatware,
serviços, telemetria, atualização em andamento, antivírus, efeitos
visuais, gravação em segundo plano, disco, calor/bateria...), e o ARENA
passa a identificar e recomendar ação.

### Progresso da auditoria 2

- [x] Fase 0 — Linha de base e inventário (25/09/2026)
- [x] Fase 1 — Varredura e limpeza (25/09/2026)
- [x] Fase 2 — Leveza e desempenho (25/09/2026)
- [x] Fase 3 — Servidor e API (25/09/2026)
- [x] Fase 4 — Jogar Junto (25/09/2026)
- [x] Fase 5 — Matriz de jogos (25/09/2026)
- [x] Fase 6 — Portabilidade e robustez (25/09/2026)
- [x] Fase 7 — Clareza para todos (25/09/2026)
- [x] Fase 8 — Relatório final e entrega (25/09/2026) — rodada final 42 de 42, bateria 71; juntada ao `main`
- [x] Extra — Barreiras de lentidão (testador + ARENA) (25/09/2026)

---

## Auditoria 3 (03/10/2026, começada em 07/10/2026) — pedido do Rafael, sem resumir

O pedido, colado de novo em 03/10/2026 (o mesmo texto da auditoria 1), está
abaixo inteiro, sem resumir, entre as duas linhas de `====`.

E a autorização que veio junto, em 07/10/2026: *"você tem permissão total
de responder toda e qualquer requisição desse script com base no que foi
feito no ARENA e no que é melhor e recomendado para a melhor otimização
possível"* — e depois: *"Continuar de onde parou quando acabou o limite"*.

**Leitura adotada:** as paradas do roteiro ("pare e espere minha
aprovação": resumo da Fase 0, lista de remoção da Fase 1, mudanças da
Fase 7, junção ao `main` na Fase 8) viram REGISTRO no relatório, com a
escolha recomendada e o porquê — não pergunta (como na auditoria 2).
Continuam valendo as 10 regras: nada removido sem a prova na lista, nada
de dado do aluno apagado, número medido antes e depois para todo "mais
leve/rápido", roteiro manual para o que só a sala confirma.

**Ramo:** `auditoria`, novo, a partir do `main` (`9def005`). O `auditoria`
de setembro (das auditorias 1 e 2, todo dentro do `main`) virou
`auditoria-anterior`, sem perder nada.

**Relatório desta rodada:** `docs\RELATORIO-QUALIDADE.md` (como o pedido
manda). O da auditoria 1, que tinha esse nome, virou
`docs\RELATORIO-AUDITORIA-1.md`; o da 2 é `docs\RELATORIO-AUDITORIA-2.md`.
Os números brutos desta rodada ficam em `docs\auditoria3\`.

**Testes de referência (regra 7):** a bateria (`servidor\tests\run.py`) e
os orçamentos no modo alvo (o `RODAR_TESTES.bat` inteiro) a cada fase; a
rodada completa (`ferramentas\rodada_final.py`, ~1h30, todos os
`testes\teste_*.py` com RetroArch de verdade) na Fase 0 e na Fase 8; no
fim das outras fases, os scripts da área mexida.

==========================================================================

AUDITORIA COMPLETA DO ARENA: TESTES, LIMPEZA E OTIMIZAÇÃO

Antes de implementar a IA, quero o ARENA perfeito: testado como um aplicativo profissional, sem código inútil, leve, portátil, com as partidas entre amigos funcionando bem nos notebooks da escola, e fácil de entender até para quem tem dificuldade de aprendizagem.

Leia o CLAUDE.md inteiro antes de começar. Trabalhe em fases, uma por vez: plano, minha aprovação, execução, testes, commit.

PÚBLICO E MÁQUINAS
- Alunos menores de idade de escola pública, incluindo alunos com dislexia, TDAH, deficiência intelectual ou pouca experiência com computador.
- A maioria dos notebooks tem até 4 GB de RAM (Celeron dual-core, sem SSD, sem permissão de administrador). Alguns são melhores (i5 com 15 GB, Ryzen 5600G).
- Redes: Wi-Fi comum, Wi-Fi da escola (que pode isolar os aparelhos entre si e pode ter página de login), ponto de acesso do celular, cabo direto e internet entre casas.

REGRAS QUE NÃO PODEM SER QUEBRADAS
1. Todo o trabalho num ramo novo do git, chamado auditoria. O ramo principal só muda quando eu aprovar a junção.
2. Nunca apague jogos, saves, BIOS, núcleos, memory cards nem a pasta dados\ do usuário. Nunca edite as duas pastas originais (a versão antiga e o ARENA-remake--master).
3. Nada é removido sem antes estar numa lista que eu aprovei, com a prova de que não é usado (quem chama, onde aparece, o que quebra se sair).
4. Toda afirmação de "ficou mais leve" ou "ficou mais rápido" precisa de número: medição antes e depois.
5. Portátil: sem instalação, sem administrador e sem pip. As ferramentas de teste são escritas em Python puro, em ARENA-unificado\testes\ ou ARENA-unificado\ferramentas\.
6. Arquivos temporários de teste ficam numa pasta própria, ignorada pelo git e apagada no fim de cada teste.
7. Os testes existentes do ARENA (RODAR_TESTES.bat e o que mais houver) rodam antes de tudo, como referência, e de novo no fim de cada fase. O resultado nunca pode piorar.
8. O que só pode ser testado com aparelhos de verdade (5 notebooks, o Wi-Fi da escola, celulares) vira um roteiro de teste manual, passo a passo, para eu fazer em sala. Não adivinhe o resultado.
9. Tudo em português do Brasil, inclusive a descrição curta de cada comando.
10. Se uma fase ficar grande demais, divida-a e me avise. Não pule etapas.

FASE 0 - LINHA DE BASE E INVENTÁRIO (nenhuma mudança no código)
- Salve este pedido inteiro, sem resumir, em ARENA-unificado\docs\PLANO-AUDITORIA.md, e cite esse arquivo na seção "Estado atual" do CLAUDE.md. É ele que permite continuar a auditoria depois de um /clear.
- Crie o ramo auditoria e rode os testes de referência.
- Meça e anote:
  tamanho total do pacote, sem jogos;
  linhas de código por arquivo;
  tempo de abertura do ARENA até a tela ficar pronta;
  uso de processador com o ARENA parado (o ideal é perto de zero);
  memória RAM usada pelo servidor e pela tela;
  quantas gravações em disco ele faz por hora parado (cartão SD e pen drive se desgastam);
  quantas threads e temporizadores ficam rodando;
  quais portas ficam abertas e se escutam só no computador ou na rede toda.
- Faça o inventário completo:
  todos os arquivos;
  todas as rotas do servidor e quem as chama;
  todas as telas, botões e chaves da interface e a rota que cada um usa;
  todas as chaves de configuração e onde são lidas;
  todos os serviços que ficam rodando em segundo plano, com o motivo de cada um;
  tudo o que depende de internet.
- Grave o resultado em ARENA-unificado\docs\RELATORIO-QUALIDADE.md, na seção "Antes".
- Pare e me mostre um resumo.

FASE 1 - VARREDURA E LIMPEZA DO CÓDIGO (DEBLOAT)
- Procure:
  funções nunca chamadas;
  rotas que a tela não usa;
  botões que chamam rotas que não existem;
  chaves de configuração que ninguém lê;
  arquivos duplicados ou que sobraram das duas versões originais;
  código de funções que já foram removidas (por exemplo: gravação de vídeo e transmissão, "só assistir", DuckStation, tecla Scroll Lock; confira, não presuma);
  serviços e temporizadores que não precisam existir ou que rodam com frequência maior que o necessário;
  documentação que fala de funções que não existem mais.
- Procure também código errado: exceções engolidas em silêncio, arquivos que não são fechados, gravações que não são atômicas, caminhos absolutos, textos em inglês na tela.
- Monte a lista de remoções e correções, cada item com a prova. Pare e espere minha aprovação.
- Depois de aprovado: aplique, rode todos os testes e faça commit.

FASE 2 - LEVEZA E DESEMPENHO
- Com o ARENA parado, uso de processador perto de zero. Nada de consulta repetida sem necessidade.
- Menos gravações em disco: registros (logs) com limite de tamanho e rodízio.
- Tela: remova CSS e JavaScript não usados e confira o tamanho das imagens.
- Os fundos animados precisam respeitar o computador fraco: desligados no modo modesto e quando o Windows pede menos animação. Esta é uma pendência antiga: medir quanto pesam num Celeron.
- Teste de estresse do catálogo: gere 5.000 arquivos de jogo falsos, espalhados por vários consoles, numa pasta temporária. Meça o tempo de indexação e confirme que a tela continua respondendo. Depois apague tudo.
- Registre os números de antes e depois no relatório.

FASE 3 - TESTES DO SERVIDOR E DA API (OFFLINE E ONLINE)
- Teste todas as rotas com:
  dados corretos;
  dados faltando;
  tipo errado;
  texto gigante;
  acentos e emojis;
  tentativas de sair da pasta ("..\..\");
  pedidos repetidos muito rápidos.
- Toda resposta de erro precisa ter uma mensagem simples, que diga o que aconteceu e o que fazer.
- Concorrência: 50 pedidos ao mesmo tempo, sem travar e sem corromper arquivos.
- Teste de longa duração: o servidor ligado por horas (ou acelerado), abrindo e fechando jogos, sem crescer em memória nem em arquivos abertos.
- Segurança:
  a) quais rotas qualquer computador da rede consegue chamar. Na rede da escola, outro aluno não pode mudar as minhas configurações, apagar os meus saves nem mandar abrir jogos no meu computador. Só o que a partida e a sincronização precisam pode ficar aberto à rede;
  b) um site qualquer aberto no navegador não pode mandar comandos para o servidor local do ARENA (proteção contra pedidos de outra origem e contra DNS rebinding).
- Sem internet, tudo o que é local funciona 100%.
- Com internet ruim, confira: DNS que falha, rede lenta, tempo esgotado e a página de login do Wi-Fi da escola devolvendo HTML no lugar dos dados esperados. As funções online (acervo, busca no Internet Archive, repasse do Jogar junto) precisam falhar com uma mensagem clara, nunca travando nem corrompendo nada.
- Acervo: arquivo baixado com código de verificação (SHA-256) errado tem que ser recusado.

FASE 4 - JOGAR JUNTO: O CORAÇÃO DO ARENA
Parte automática, num computador só:
- Abra um hospedeiro e até 4 convidados (5 RetroArch ao mesmo tempo), cada um com sua própria configuração, seus saves e sua pasta temporária, todos conectando no próprio computador.
- Jogo de 5 jogadores: Super Bomberman de Super Nintendo com o adaptador Multitap. Descubra como o ARENA deve ligar o Multitap sozinho nos jogos que aceitam mais de 2 jogadores, e qual o limite de conexões do Jogar junto (o RetroArch tem uma configuração de número máximo de conexões: confira o nome e o padrão na documentação atual e ajuste para comportar 5 jogadores). Se o jogo não estiver na pasta, me peça.
- Meça: processador e memória do hospedeiro, ping, avisos de dessincronia, tempo para cada convidado entrar.
- Se ainda não houver jeito confiável de apertar botões por programa, teste com os jogadores parados (o Jogar junto troca dados a cada quadro mesmo assim) e deixe o teste com botões para o roteiro de sala.
- Crie um simulador de rede ruim em Python puro: um intermediário entre o hospedeiro e um convidado que acrescenta atraso (50, 100 e 200 ms) e perda de pacotes (1% e 5%). Descreva o que o jogador sente em cada caso.
- Situações de sala de aula:
  convidado que cai e volta;
  hospedeiro que sai no meio;
  convidado que entra com a partida já começada;
  sexto jogador tentando entrar (precisa receber uma mensagem clara);
  duas partidas diferentes na mesma rede ao mesmo tempo.
- Descoberta de colegas com muitos aparelhos: simule 30 computadores anunciando ao mesmo tempo. A lista na tela precisa continuar clara, e o processador, baixo.
- Sincronização e mala do pen drive: o mesmo recorde vindo de dois lugares, relógios diferentes entre os notebooks e pen drive em FAT32 (que só guarda a hora de 2 em 2 segundos).

Parte dos notebooks da escola (o que precisa de diagnóstico no ARENA e no PARTIDA.bat, com mensagem simples):
- Firewall do Windows bloqueando a entrada de conexões, porque a rede está marcada como pública e o aluno não é administrador. Confira como o Windows se comporta para usuário comum. O ARENA precisa perceber, explicar e oferecer uma saída (outro computador hospeda, ou repasse pela internet, em que os dois lados só fazem conexões de saída).
- Wi-Fi que isola os aparelhos entre si.
- Ponto de acesso de celular Android e iPhone (as faixas de endereço variam).
- Cabo direto sem roteador (endereço 169.254).
- Adaptadores virtuais e VPN.
- Endereço que muda no meio da aula, notebook que dorme e acorda, Wi-Fi que cai durante a partida.

Multiplayer local (um computador, vários controles):
- Até 4 jogadores no mesmo computador, com o 007 de Nintendo 64 (GoldenEye) e outro jogo de 4 jogadores. Confira o mapeamento de 4 controles, e de teclado junto com controle.

- Ao fim da fase, escreva o roteiro manual para eu testar em sala com 5 notebooks de verdade: o que ligar, em que ordem, o que conferir e o que anotar.

FASE 5 - MATRIZ DE JOGOS
- Para cada console que tiver jogo na pasta:
  o jogo abre e mostra imagem (se o RetroArch tiver opção de rodar um número fixo de quadros e salvar uma captura de tela, use-a para automatizar; confira na documentação);
  o controle funciona;
  salvar e carregar estado funciona;
  o save do próprio jogo funciona;
  os cheats funcionam;
  e os quadros por segundo no modo modesto e no normal.
- Pendências antigas que entram aqui:
  PS1: uma partida completa pelo Jogar junto até salvar no memory card, para confirmar que o memory card de quem hospeda fica certo;
  PS2: testar o seletor de qualidade do PCSX2 com as ISOs que estão na pasta;
  PS3 e Xbox 360, se houver jogo.
- Resultado: uma tabela console × teste no relatório, com o que passou, o que falhou e o porquê.

FASE 6 - PORTABILIDADE E ROBUSTEZ
- Pen drive com letras diferentes, caminho com espaços, acentos e muito longo, pasta só de leitura e disco cheio.
- FAT32, exFAT e NTFS. No FAT32, nenhum arquivo passa de 4 GB: o ARENA precisa avisar antes de alguém copiar uma ISO grande.
- Queda no meio da gravação: mate o processo durante a gravação de save, config e banco. Nada pode ficar corrompido, e o VERIFICAR.bat precisa consertar o que der.
- Configuração, JSON e banco corrompidos de propósito: o ARENA abre mesmo assim e explica.
- Notebook sem driver de vídeo (adaptador de vídeo básico da Microsoft): o RetroArch precisa escolher um modo de vídeo que funcione.
- Windows 10 e 11. Windows de 32 bits: detectar e explicar.
- Antivírus e SmartScreen bloqueando os .bat de um zip baixado: explicar no LEIA-ME como liberar.
- Procure no código qualquer coisa que exija administrador (registro do sistema, netsh, serviços do Windows) e remova ou substitua.

FASE 7 - CLAREZA PARA TODOS (USABILIDADE E ACESSIBILIDADE)
- Revise cada texto da tela e dos guias em linguagem simples: frases curtas, uma ideia por frase, palavra técnica só com explicação, e um exemplo lúdico do dia a dia sempre que o assunto for difícil (por exemplo: "hospedar a partida é como emprestar a sua casa para a festa: os amigos vêm até você").
- Mensagem de erro sempre com duas partes: o que aconteceu e o que fazer agora.
- Faça o passo a passo, clique por clique, com estas pessoas, e conte quantos passos e quantas decisões cada tarefa exige:
  Ana, 11 anos, com dislexia;
  Pedro, 13 anos, com TDAH;
  Lucas, com deficiência intelectual leve;
  Dona Maria, que nunca usou computador;
  o professor com 5 minutos antes da aula.
- As tarefas:
  abrir o ARENA e jogar;
  salvar e continuar depois;
  jogar com um amigo em outro notebook;
  resolver "meu amigo não aparece na lista";
  levar o progresso no pen drive.
- Navegação só por teclado, contraste, tamanho de letra, ícone sempre com texto, nada de parede de texto, menos animação quando o Windows pedir.
- Proponha as mudanças, espere minha aprovação e depois aplique.

FASE 8 - RELATÓRIO FINAL E ENTREGA
- Complete o RELATORIO-QUALIDADE.md com:
  a seção "Depois" e uma tabela antes × depois com todos os números da Fase 0;
  o que foi removido;
  o que foi corrigido;
  o que ainda falta, com honestidade;
  e os roteiros manuais de sala de aula.
- Atualize os guias 1 a 6, o LEIA-ME.md e o CLAUDE.md ("Estado atual").
- Rode tudo uma última vez. Pare e espere minha aprovação para juntar o ramo auditoria ao principal.

Ao fim de cada fase: diga exatamente como testar, faça commit no ramo auditoria e atualize a seção "Estado atual" do CLAUDE.md.

Comece só pela Fase 0.

==========================================================================

### Progresso da auditoria 3

- [x] Fase 0 — Linha de base e inventário (07/10/2026) — rodada de referência 87 de 92 (as 5 falhas analisadas)
- [x] Fase 1 — Varredura e limpeza (debloat) (08/10/2026) — C1 a C7, R1 a R5; bateria 232
- [x] Fase 2 — Leveza e desempenho (08/10/2026) — abertura 2,57→1,63 s; 8.264→72 KB por abertura; fundo animado 7,7→5,0% de um núcleo; bateria 246
- [x] Fase 3 — Servidor e API (08/10/2026) — a tela não congela mais na releitura (3,3 s → 0,02 s); internet ruim com frase certa (teste novo, 13/13); 66+ mensagens com "o que fazer"; bateria 252
- [x] Fase 4 — Jogar Junto (08–09/10/2026) — a porta da partida ia com o nome errado (os testes de rede ruim e de duas partidas nunca mediram o que diziam: refeitos); 8 chaves mortas do RetroArch; sexto jogador e rede Pública com explicação; bateria 261
- [x] Fase 5 — Matriz de jogos (09–11/10/2026) — 17 consoles pelo RetroArch nos modos normal e modesto; o perfil Qualidade ligava sozinho "voltar no tempo" e "resposta instantânea" (N64 a 30 quadros/s, PS1 com 5× o processador: P1); os cheats nunca funcionaram (P2); PS2 37 de 37 jogos; GameCube, Wii, PS3 e Xbox 360 abrem; revisão independente refeita à mão (a automática morreu 4× no limite): nenhum defeito
- [x] Fase 6 — Portabilidade e robustez (10–11/10/2026) — rodada da área 14 de 14 (da pasta antiga e da nova, depois que as pastas mudaram de lugar no disco); a mudança mostrou que a correção de caminhos deixava passar a pasta que sobe um nível (F1) e escolhia a âncora pela ordem da lista (F2); notebook sem driver de vídeo cai no Direct3D 11 (4 testes novos); nenhum comando que peça administrador; bateria 310
- [x] Fase 7 — Clareza para todos (09–11/10/2026) — 46 de 48 trechos reescritos em linguagem simples (+ o botão Registrar pontos, que não existia); acessibilidade 9 de 9 (o hidden não escondia, contraste AA, letra mínima 11 px, o foco agora entra na janela que abre); passo a passo das 5 pessoas conferido na tela de hoje
- [x] Fase 8 — Relatório final e entrega (11–12/10/2026) — rodada completa 101 de 102 (o Dreamcast da matriz, repetido sozinho, passou); abertura 2,61 → 1,7–1,9 s; 35 gravações e 72 KB por abertura; 1 h parado com a tela: 0 gravações; E1–E5 (os testes não mexem mais em dado de quem joga; 5,5 GB soltos no `.git`, provados e limpos); bateria 323; juntada ao `main` (PR #1) e Release v2026.10.11

---

## Auditoria 4 (22/10/2026) — pedido do Rafael, sem resumir

O pedido, de 22/10/2026 (por volta das 11h40), está abaixo inteiro, sem
resumir, entre as duas linhas de `====`. O Rafael estava fora de casa,
acompanhando pelo celular.

==========================================================================

Faça uma auditoria completa de todas as versões do Arena, começando pela versão de android que possui diversas limitações como precisar sair do aplicativo para poder sair do jogo, adaptar comandos de teclado para interface do android e adaptar recursos e funcionalidades do windows para android assim como para outros sistemas operacionais, analise os aplicativos do gênero de maior sucesso para implementar melhorias e ideias, depois passe para o linux, windows e chromebook. Por favor utilize as ferramentas, skills, scripts e plugins mais modernos e ja implementados ao claude para fazer essa auditoria completa, baseado na minha auditoria que antes constava na memória mas melhorando ela ainda mais com as novas ferramentas, implemente uma auditoria profissional, utilize um recurso que tem no claude para atacar o aplicativo e descobrir falhas de segurança e funcionalidade para corrigir, testes de strees diversos e simule o uso de todos os recursos no android, linux para ver se falta implementa algum recurso ou função ou adaptar para o ambiente do android, seus comandos e limitações, foque na inteface e capacidade do android de funcionamento para isso. E claro garanta uma interface intuitiva e simples de mexer, no android como no windows precisa ser claro e autoexplicativo cada função exemplo: não tem jogos na pasta, precisa ter um passo a passo simples de onde adicionar o jogo e se possível um link que direcione direto para pasta onde precisa colocar o jogo ou se possível um identificador que identifica roms no celular baixadas e que pede permissão para mover o arquivo para pasta correta ou algo do gênero, todas as funções e recursos do windows devem ser implementados em todas as versões e adaptados para as limitações de hardware ou de sistema operacional, não estou em casa no momento

==========================================================================

**Leitura adotada** (a mesma das auditorias 2 e 3): a "minha auditoria"
é este arquivo, com as 8 fases e as 10 regras, que continuam valendo. O
ramo é o `auditoria-4`, a partir do `main` (`8cf3371`, a versão
2026.10.22). Com o Rafael fora de casa, as paradas viram registro no
relatório, com a escolha recomendada e o porquê. A única parada de
verdade é juntar ao `main` e publicar versão nova, que esperam a
aprovação dele. Relatório: `docs\RELATORIO-AUDITORIA-4.md`; números
brutos em `docs\auditoria4\`. Código do Android em Java, como já é (sem
Gradle nem biblioteca nova); ferramentas e testes em Python puro.

**As fases desta rodada:**

- Fase 0 — Linha de base dos quatro sistemas: a bateria e os testes do
  Android, do Linux e do Chromebook como referência; a matriz de
  paridade (cada função da tela do Windows × Android, Linux e
  Chromebook: igual, adaptada, falta ou impossível, com o porquê); os
  atalhos de teclado e o equivalente em toque e em controle.
- Fase 1 — Android: o uso real no emulador, tela por tela, com fotos; os
  limites (sair do jogo sem sair do app, atalhos de teclado, voltar,
  girar a tela, segundo plano, pouca memória, permissão de pasta); o
  estresse (o Monkey do Android, matar e voltar, sem rede, armazenamento
  cheio); e o conserto do que faltar.
- Fase 2 — Os aplicativos de maior sucesso do gênero: o que fazem melhor
  e o que serve ao ARENA (sala de aula, alunos menores, offline, sem
  conta).
- Fase 3 — Ataque de segurança e de funcionamento (Claude Security, com
  a revisão adversarial), com foco no Android (a ponte da WebView, os
  componentes exportados, o servidor local aberto a outros apps, as
  pastas) e na rede da escola; corrigir o que for real.
- Fase 4 — Primeiro uso claro em todos os sistemas: sem jogos na pasta,
  o passo a passo e o botão que abre a pasta certa; no Android, achar os
  jogos baixados e pedir permissão para levá-los ao lugar certo.
- Fases 5, 6 e 7 — Linux, Windows e Chromebook: a mesma auditoria (uso,
  estresse e paridade), adaptada a cada um.
- Fase 8 — Relatório, guias e rodada final. Parar e esperar a aprovação
  para juntar ao `main` e publicar.

**Segunda mensagem, no mesmo dia, sem resumir:**

> Utilize todas as melhores ferramentas implementadas no claude code para aprimorar o script que escrevi acima, para fazer engenharias reversas em aplicativos de android do gênero de sucesso para ter ideias de como melhorar a interface e adaptar recursos do windows, para tomada de decisões ou até mesmo adicionar processos e testes e tudo que precisa em uma auditoria para criar aplicativos profissionais, seguros e com uma interface intuitiva simples e seguindo o padrão do app no windows em questão de interface e onde fica cada configuração e etc...

**Mensagens da noite de 22/10/2026, sem resumir:**

> continuar pot gentileza até o final e por favor continue a trabalhar sozinho quando o limite da sessaão voltar para eu dormir enquanro você trabalha, o claude code está atualizado, se puder fazer isso e deixar ações manuais por ultimo eu agradeço muito

> no meu celular samsung a12 4gb 64 gb de memória e andoroid 12 ele diz o seguinte ao instalar o arena: Como o app não é compatível com seu smartphone, ele não foi instalado, a iéia é do arena ser também a salvação de versões de aondroid mais antigas também, a idéia é que qualquer computador mesmo desatualizado possa usar o arnea como porta de salvação de entreterimento no computador, mas primeiro finalize todo o projeto e só no final junto com as etapas manuais vem essa opção para eu verificar a melhor ordem de implementação por gentileza

> por favor faça uma engenharia reversa com o lossless scalling e implemente todas suas funções, tpecnicas e tudo que ele faz no arena, de forma que ocorra automáticamente que precisa ser verificado também, e a tela não mais está esticando até a borda da tela como fazia antes, então precisa ser verificado. O ARENA de android tamb´pem deve ser possível fazer as mesmas funções como controle configurável automáticamente ou manual, escolher entre os bitões da tela ou não, 8 jogadores, jogar com amigo cada um em seu telefone conectados pelo hotspot do player um que o player 2 se conecta, pelo wi-fi cada um em sua casa ou no mesmo wifi (se for implementação grande deixa oara depois), por gentileza eu gostaria que depois da auditoria instale no meu telefone a versão mais atualizada possível do arena atravpes do cabo usbc adaptado e configurado finamente para meu samsung a12 e com todas as bios, emuladores e tudo que tenho localmente de configurações assim como a engenharia reversa do lossless scalling que seja configurado finamente para meu telefone, para meu computadir também onde rodo o claude code por gentileza, mas ele deve saber identificar queda de desempenho, hardware e software para entender as melhores configurações no automático, e deve ter a opçlão personalizada, tanto para implementações da engenharia reversa do lossless como tudo que o arena já faz para melhorar a experiência, para promover uma experiência fluida mesmo que dependendo do hardware seja um grafico feio

> tem que ser feito de forma que possa ter tudo implementado e instalado no guthub, o arena deve ser sempre baixar e jogar, e a atualização deve ser abrir a pasta compactada copiar tudo e arrastar para o arena e atualiza sem perder nada de progresso, perfil, saves e nem bios importantes ou suas configurações, tudo integro

**Leitura adotada para essas mensagens:**

- Trabalho sozinho durante a noite: um agendamento da sessão retoma o
  trabalho depois do limite; as ações manuais ficam para o fim do relatório.
- O Galaxy A12 (Android 12) recusa o APK com "não é compatível": o mais
  provável é o Android de 32 bits (o APK só tem arm64-v8a e x86_64). A
  versão web resolve já. O APK de 32 bits e o computador antigo entram como
  opções no fim, com a ordem recomendada, para o Rafael decidir; a
  instalação no A12 dele pelo cabo, depois da auditoria, entra nessa mesma
  lista.
- Lossless Scaling: é um programa pago e fechado. Abrir o código dele para
  copiar algoritmo fere a licença, e o repositório é público. A leitura é a
  mesma da regra dos apps fechados do roteiro abaixo: só informação pública
  (página da Steam, guias, notas de versão) e o uso do programa. As funções
  dele entram no ARENA por técnicas abertas (FSR, NIS, CAS, escala inteira,
  esticar até a borda), no automático e com a opção personalizada. A
  geração de quadros (LSFG) não cabe em Python puro sem instalar nada; para
  ela, o ARENA continua usando o Lossless de quem comprou (item 10).
- "A tela não estica até a borda": o RetroArch sempre usou a proporção do
  console (faixas pretas no 4:3 em tela larga), e o perfil "ARENA" que o
  ARENA grava no Lossless usa o modo "Aspect ratio". Entra a opção "Formato
  da imagem" (Automático, Esticar até a borda, Do console), nos núcleos e
  nos emuladores de fora.
- Android: botões na tela (automático, sempre ou nunca), controles,
  até 8 jogadores e o Jogar Junto pelo roteador do celular ou pelo mesmo
  Wi-Fi. Pela internet (cada um em casa) fica para depois, por ser grande.
- O automático deve perceber a queda de desempenho e o hardware e
  escolher sozinho, com a opção personalizada.
- Tudo vai pelo GitHub (o código, o pacote e o APK): baixar e jogar. A
  atualização é copiar o zip novo por cima da pasta do ARENA, sem perder
  progresso, perfil, saves, BIOS nem configurações; o pacote nunca leva
  arquivo que apague dado de quem usa, e um teste confere isso.

### O roteiro aprimorado (as ferramentas de hoje)

**O que "profissional" quer dizer aqui** (os padrões de referência):

- Segurança: OWASP MASVS 2 e MASTG para o Android, OWASP ASVS (nível 1)
  para o servidor local, e o modelo de ameaças da sala de aula: outro
  aluno na mesma rede, outro app no mesmo celular, um site aberto no
  navegador, um pen drive trocado.
- Android: as diretrizes de qualidade do Google para apps (o Voltar
  sempre volta um passo, segundo plano, permissões, sem travar nem "app
  não responde") e o Material Design 3 (alvo de toque de 48 dp).
- Acessibilidade: WCAG 2.2 AA (contraste, tamanho, foco, texto
  alternativo), a fonte grande do sistema e o leitor de tela.
- Interface: as 10 heurísticas de Nielsen e as regras da Fase 7 das
  auditorias anteriores (frase curta, ícone com texto, erro com o que
  fazer).

**As ferramentas, cada uma onde rende mais:**

| Ferramenta | Para quê |
|---|---|
| Claude Security (varredura com painel adversarial de 3 votos) | Atacar o código inteiro; depois, só o que mudou, a cada fase |
| `/security-review` e `code-review` | Revisar cada conjunto de mudanças antes do commit |
| Android Lint, `apkanalyzer` e `aapt2` (do SDK) | O APK do ARENA: componentes exportados, WebView, permissões, depuração ligada |
| Engenharia reversa (`leanrea`) e o uso no emulador | Os apps de sucesso de código aberto (Lemuroid, Dolphin, PPSSPP, RetroArch, ES-DE, melonDS): manifesto, telas e textos, e o uso real no emulador (fotos do primeiro uso, de colocar jogos e de sair do jogo). App fechado (Daijishō) só por informação pública, sem decompilar |
| Monkey do Android, `am`, `cmd` e `dumpsys` | Estresse: milhares de toques aleatórios, matar e voltar, girar, pouca memória, sem rede, fonte grande, tema escuro, tela dividida; travamentos e "app não responde" |
| Playwright (navegador sem janela) | A tela do ARENA em celular, tablet, notebook e Chromebook: clique por clique, fotos e a árvore de acessibilidade |
| `design:accessibility-review`, `design:ux-copy` e `design:design-critique` | A tela e os textos de cada sistema, a partir das fotos |
| `delegar` (os modelos gratuitos do kit) | Leitura em massa e rascunhos; o Claude confere antes de usar |

**Os processos que ficam no ARENA:**

1. Pronto quer dizer: teste junto com a mudança; a bateria e os testes da
   área; revisão do código; revisão de segurança quando mexe em rede,
   arquivo, ponte ou permissão; guia atualizado; um commit por mudança.
2. Matriz de rastreabilidade no relatório: pedido → mudança → teste →
   resultado.
3. Classificação de cada achado: crítico (perde dado, invasão, trava a
   aula), alto, médio ou baixo.
4. Teste de paridade da tela: a mesma árvore de telas e ajustes no
   Windows, no Linux, no Android e no Chromebook. O que é de um sistema
   só aparece no mesmo lugar, marcado. Reprova se um ajuste mudar de
   lugar ou sumir sem explicação.
5. Teste de primeiro uso em cada sistema: sem jogos → passo a passo → o
   jogo na lista, sem ajuda de ninguém.
6. Antes de versão nova: a rodada final, o Android no emulador, o Monkey
   e a varredura de segurança do que mudou.
7. Roteiro manual para o que só aparelho de verdade confirma (celular
   barato, tablet, Chromebook da escola, controle Bluetooth).

**A interface: o padrão é o Windows.**

- As mesmas abas, na mesma ordem e com os mesmos nomes, e cada ajuste no
  mesmo lugar. O que não existe num sistema vem explicado ali mesmo;
  nada some sem aviso.
- No jogo, toda tecla do ARENA tem o equivalente no toque e no controle,
  num mapa só, mostrado na ajuda.
- Sem jogos: um passo a passo curto; o botão que abre a pasta certa em
  cada sistema; "Procurar jogos baixados" (acha jogos na pasta Download
  e pergunta antes de mover); arrastar e soltar no computador; e
  "Adicionar jogo" pelo seletor de arquivos no Android e no Chromebook.
- No Android: sair do jogo pelo Voltar (com "Sair do jogo" no menu) e
  por um botão na tela, sem nunca precisar fechar o app.

### Progresso da auditoria 4

- [ ] Fase 0 — Linha de base dos quatro sistemas e matriz de paridade
  (bateria, Chromebook 41/41 e versão web 18/18 passam; a matriz falta)
- [~] Fase 1 — Android: sair do jogo e menu pelo toque (`d05ff26`),
  permissões explicadas antes de pedir, Procurar jogos baixados
  (`07f0491`); faltam os botões na tela (automático/sempre/nunca), 8
  jogadores, o Jogar Junto pelo roteador do celular, os textos "PC", o
  Voltar no jogo, o Monkey e o Lint
- [~] Fase 2 — Apps de sucesso: a pesquisa roda de novo (o limite da
  sessão derrubou a primeira)
- [~] Fase 3 — Segurança: F3 (`c95688f`) e F4 (`38306a7`) corrigidos; a
  segunda varredura parou no limite da sessão e será retomada
- [x] Fase 4 — Primeiro uso: Procurar jogos baixados (Windows e Android) e
  Guardar um jogo (versão web e Chromebook)
- [~] Versão web para o celular que não instala o APK (`333c0ca`,
  `665126a`): pronta e testada; falta publicar no GitHub Pages e o
  `docs\WEB.md`
- [ ] Mensagens da noite de 22/10: Formato da imagem (esticar até a
  borda), as funções do Lossless por técnicas abertas e o automático que
  percebe queda de desempenho, a atualização por cima sem perder nada
  (teste), o APK de 32 bits e a instalação no A12 (no fim, com o Rafael)
- [ ] Fases 5, 6 e 7 — Linux, Windows e Chromebook
- [ ] Fase 8 — Relatório (`docs\RELATORIO-AUDITORIA-4.md`), guias, rodada
  final; ações manuais no fim
