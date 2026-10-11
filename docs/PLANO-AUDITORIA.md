# Plano da Auditoria Completa do ARENA

> Pedido do Rafael, salvo aqui sem resumir (conforme instrução explícita),
> para permitir continuar a auditoria depois de um `/clear`. Ver seção
> "Estado atual" do `CLAUDE.md` pra saber em que fase a auditoria está.
>
> **Rodada atual: auditoria 3** (seção no fim deste arquivo). Relatórios:
> auditoria 3 em `RELATORIO-QUALIDADE.md`, auditoria 2 em
> `RELATORIO-AUDITORIA-2.md`, auditoria 1 em `RELATORIO-AUDITORIA-1.md`.

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
- [ ] Fase 5 — Matriz de jogos
- [x] Fase 6 — Portabilidade e robustez (10–11/10/2026) — rodada da área 14 de 14 (da pasta antiga e da nova, depois que as pastas mudaram de lugar no disco); a mudança mostrou que a correção de caminhos deixava passar a pasta que sobe um nível (F1) e escolhia a âncora pela ordem da lista (F2); notebook sem driver de vídeo cai no Direct3D 11 (4 testes novos); nenhum comando que peça administrador; bateria 310
- [ ] Fase 7 — Clareza para todos
- [ ] Fase 8 — Relatório final e entrega
