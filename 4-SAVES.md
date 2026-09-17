# 4 — Saves, cheats e não perder nada

Os 10 pontos de salvamento, os códigos e como levar seu progresso para onde quiser.

**Neste documento:**

- Parte A — Save states e cheats
- Parte B — Não perder nada

---

## Parte A — Save states e cheats

Dez pontos de salvamento por jogo e códigos estilo GameShark. Tudo dentro do
menu que abre com **Esc**.

---

### A tecla Esc

No RetroArch normal, `Esc` fecha o jogo. **No ARENA, `Esc` abre o menu.**

| Tecla | O que faz |
|---|---|
| **`Esc`** | **Abre o menu do jogo** |
| `F10` | Fecha o jogo e volta ao ARENA |
| `F2` | Grava no espaço atual |
| `F4` | Volta ao espaço atual |
| `F6` | Espaço anterior |
| `F7` | Próximo espaço |
| `F8` | Foto da tela |
| `F` | Tela cheia |
| `P` | Pausa |

Sem teclado: `Start` + `Select` juntos abrem o mesmo menu.

#### No PlayStation 2 o menu é outro

Aviso honesto: **o menu que aparece no PCSX2 é o dele, não o do ARENA.** É
outro programa, com tela própria escrita em C++. Não existe como um
desenhar o menu do outro — e tentar injetar código no processo seria frágil
e barrado pelo antivírus.

O que o ARENA faz é o possível e resolve na prática: **escreve a
configuração do PCSX2 antes de abrir**, para as teclas serem as mesmas e o
controle já vir pronto.

| | Pelo RetroArch | Pelo PCSX2 |
|---|---|---|
| Abrir o menu | `Esc` | **`Esc`** |
| Salvar estado | `F2` | `F1` |
| Voltar estado | `F4` | `F3` |
| Trocar o espaço | `F6` e `F7` | `F2` |
| Foto da tela | `F8` | **`F8`** |
| Tela cheia | `F` | `F11` |
| Fechar | `F10` | **`F10`** |

Quatro das sete teclas ficaram iguais. As três diferentes são limitação do
próprio PCSX2, que não deixa remapear essas.

#### O que o ARENA já configura no PCSX2

Você não precisa entrar no menu dele para nada disso:

| Item | Como fica |
|---|---|
| Controle | DualShock 2, reconhecido sozinho |
| Analógico | Os dois, esquerdo e direito, mais o direcional |
| Vibração | Ligada nos dois motores |
| Jogador 2 | Segundo controle plugado, já mapeado |
| Zona morta | 0.10, para analógico gasto não andar sozinho |
| Tela cheia | Abre direto, no modo ultra desempenho |

**A BIOS continua sendo pela tela dele**, na primeira vez. O ARENA preserva
essa configuração ao escrever o resto — testado.

Os 10 espaços de save do ARENA e os cheats cadastrados por ele **também não
valem no PCSX2** — ele tem os próprios. Isso está na tabela de comparação do
documento 2.

Se você prefere ter tudo pelo ARENA, tire a pasta do PCSX2 de dentro de
`emuladores`. O PlayStation 2 volta ao RetroArch — com a ressalva de que
muitos jogos não abrem por lá.

#### Gravação e transmissão: desligadas

O RetroArch sabe gravar vídeo da partida e transmitir ao vivo. **O ARENA
desliga as duas coisas**, e não só escondendo do menu: as teclas de atalho
foram retiradas, para ninguém ligar sem querer.

O motivo é simples. Gravar aula com voz e imagem de estudante menor de
idade, ou transmitir para a internet, são dois problemas que não têm o que
fazer numa escola. O ARENA não vai criar nenhum dos dois.

Para tirar foto da tela, `F8` continua funcionando — imagem parada, salva
na pasta do ARENA, sem áudio e sem sair do computador.

#### O que tem no menu

O ARENA deixa o menu enxuto de propósito. O RetroArch vem com dezenas de
itens que só atrapalham na hora de achar o save. Ficou assim:

| Item | Para quê |
|---|---|
| **Salvar Estado** | Grava no espaço atual |
| **Carregar Estado** | Volta ao espaço atual |
| **Desfazer** | Recupera se você errou o espaço |
| **Cheats** | Liga e desliga os códigos |
| **Controles** | Remapeia os botões deste jogo |
| **Opções** | Ajustes do console em que você está |
| **Filtros de tela** | Troca o efeito de imagem |
| **Foto da tela** | Mesmo que `F8` |
| **Reiniciar** | Começa o jogo do zero |
| **Fechar** | Mesmo que `F10` |

O visual é texto sobre fundo escuro, sem imagem nem animação. Abre
instantâneo até no computador mais fraco — e tem a cara certa para um
console retro.

**Uma exceção:** se você ligou *Travar Alt+Tab e tecla Windows* em Ajustes →
Máquina, o `Esc` para de abrir o menu. É como essa trava funciona: ela
prende todas as teclas de atalho no jogo, inclusive a do menu.

Para soltar, aperte **`F9`**. O `Esc` volta a funcionar na hora.

**O menu abre em português**, e cada item traz uma linha explicando o que
faz. Depois de salvar ou carregar, ele volta sozinho para o jogo em vez de
deixar você procurando a saída.

Dos 46 itens que o RetroArch mostra por padrão, o ARENA deixa **12**.

---

### Parte A — Os 10 save states

Cada jogo tem 10 espaços, numerados de **0 a 9**. Cada espaço guarda o jogo
exatamente como estava: posição, vida, itens, tudo.

Diferente do save do próprio jogo, que só grava nos pontos que o jogo
permite. O save state grava em qualquer lugar, até no meio de um chefe.

#### Gravar

**Pelas teclas:**

1. `F6` ou `F7` até chegar no espaço que você quer.
2. `F2` grava. A tela avisa em qual espaço gravou.

**Pelo menu:**

1. `Esc`
2. **Salvar Estado**

#### Voltar

**Pelas teclas:** `F6`/`F7` para escolher o espaço, `F4` para voltar.

**Pelo menu:** `Esc` → **Carregar Estado**.

Se você voltou sem querer, `Esc` → **Desfazer Carregar Estado** recupera o
que estava antes.

#### Como usar bem os 10 espaços

Uma forma que funciona:

| Espaço | Para quê |
|---|---|
| 0 | O de sempre. Grava a cada avanço |
| 1 a 3 | Antes de cada chefe |
| 4 a 6 | Pontos de virada da história |
| 7 e 8 | Testar caminhos diferentes |
| 9 | Ponto seguro. Só grave aqui quando tiver certeza |

**Deixe o espaço 9 como seu seguro.** Só grave nele quando tiver certeza.
Se você gravar por engano por cima de um espaço bom, não tem como recuperar.

#### Ver e apagar pelo ARENA

Na lista de jogos, clique em **Saves e cheats**, aba **Save states**.

Mostra os 10 espaços: quais estão ocupados, de quando são e quanto ocupam.
Espaço com borda azul está cheio. O botão *apagar* libera o espaço.

Se o pen drive estiver ficando cheio, é aqui que você vê o que dá para
apagar. Save state de PlayStation passa de 1 MB cada.

---

### Parte B — Cheats

Códigos que alteram o jogo durante a partida: vidas infinitas, todos os
itens, munição sem acabar, passar de fase.

Serve código de **Game Genie, GameShark e Action Replay** — os mesmos
daqueles cartuchos antigos.

#### Como funciona

O ARENA guarda os códigos num arquivo por jogo. O RetroArch lê esse arquivo
e mostra os códigos dentro do jogo, com um interruptor para cada um. Você
liga e desliga na hora, sem fechar nada.

#### Passo 1 — Cadastrar o código

1. Na lista de jogos, clique em **Saves e cheats**.
2. Aba **Cheats**.
3. Preencha:
   - **O que o código faz** — escreva em português. É o que vai aparecer no
     menu do jogo. `Vidas infinitas` é melhor que `cheat 1`.
   - **Código** — cole o código. Se tiver mais de uma linha, cole todas.
4. **Adicionar código**.

#### Passo 2 — Ligar

Duas formas:

**Pelo ARENA:** o interruptor azul ao lado do código.

**Dentro do jogo:** `Esc` → **Cheats** → ligue o que quiser.

O jeito de dentro do jogo é melhor: você liga o código no chefe difícil e
desliga depois, sem sair.

#### Formato do código

O ARENA aceita:

```
7E0DBE09
7E0DBE:09
7E0DBE09 7E0DBF09
```

Código de várias linhas: cole uma por linha, ou separe por espaço. O ARENA
junta sozinho.

**Só entram números e as letras de A a F.** Qualquer outra coisa é recusada
na hora, com aviso. Isso protege o arquivo de virar lixo.

#### Descobrir códigos sem procurar na internet

O RetroArch tem um buscador embutido que funciona como um GameShark de
verdade — você não precisa saber o código, você **acha** o código:

1. `Esc` → **Cheats** → **Iniciar ou Continuar Busca de Cheat**
2. Escolha o tamanho do valor (a maioria dos jogos usa **8 bits**)
3. **Buscar valor igual a** — digite quantas vidas você tem agora
4. Volte ao jogo, perca uma vida
5. `Esc` → busque de novo com o número novo
6. Repita até sobrar pouca coisa
7. **Adicionar correspondências à lista** — pronto, o código é seu

Funciona para vida, munição, dinheiro, itens — qualquer número que aparece
na tela.

É chato na primeira vez e vicia depois. E você aprende o que é endereço de
memória sem ninguém precisar falar essas palavras.

---

### Onde os arquivos ficam

Tudo dentro da pasta do ARENA. Copiou a pasta, levou tudo.

| O quê | Onde |
|---|---|
| Os 10 save states | `retroarch\states\` |
| Save do próprio jogo | `retroarch\saves\` |
| Cheats | `retroarch\cheats\<Console>\` |
| Fotos da tela | `retroarch\screenshots\` |

Os save states seguem o nome do arquivo do jogo:

```
arena_do_joao.state     ← espaço 0
arena_do_joao.state1    ← espaço 1
...
arena_do_joao.state9    ← espaço 9
```

**Se você renomear o arquivo do jogo, o ARENA perde os saves dele.** Não é
defeito: o RetroArch procura pelo nome. Escolha o nome antes de começar a
jogar.

---

### Cópia de segurança

Toda vez que você fecha um jogo, o ARENA copia sozinho para a pasta
`backup`: os recordes, o seu perfil e os saves dos jogos. As 3 cópias mais
recentes ficam guardadas.

**Save state não entra na cópia.** Um estado de PlayStation passa de 1 MB, e
são 10 por jogo — copiar isso a cada partida acabaria com um pen drive em
poucas semanas. Os estados ficam só no lugar original.

Para forçar uma cópia: **Ajustes → Máquina → Fazer cópia agora**.

Para restaurar: copie os arquivos de dentro de `backup\<data>` de volta para
`dados\` e `retroarch\saves\`, com o ARENA fechado.

---

### Problemas

| Sintoma | Causa | Solução |
|---|---|---|
| `Esc` fecha o jogo em vez de abrir o menu | O ARENA não gerou a configuração | Feche e abra o ARENA. Ele reescreve na abertura |
| Save state some ao trocar de computador | O jogo foi renomeado | Use o mesmo nome de arquivo |
| Gravei por cima de um espaço bom | Não tem como recuperar | `Esc` → Desfazer Salvar Estado, mas só funciona antes de fechar o jogo |
| Cheat cadastrado mas não aparece no jogo | O código não foi ligado | `Esc` → Cheats → ligue o interruptor |
| Cheat ligado mas nada muda | O código não é desse jogo ou dessa versão | Códigos são específicos por versão. Tente o buscador de cheat |
| Cheat travou o jogo | Normal. Cheat mexe direto na memória | Desligue, `Esc` → Carregar Estado |
| "Código inválido" ao cadastrar | Tem letra fora de A a F | Confira se não copiou texto junto |
| Pen drive enchendo | Save states ocupam muito | Aba Save states, apague os espaços que não usa |

---

### Para a aula

Este arquivo de cheat é texto puro:

```
cheats = 2

cheat0_desc = "Vidas infinitas"
cheat0_code = "7E0DBE09"
cheat0_enable = true
cheat0_handler = "1"
```

`7E0DBE` é um endereço de memória. `09` é o valor gravado nele. O cheat não
tem mágica nenhuma: ele escreve um número num lugar da memória, toda vez que
o jogo roda um quadro.

Quem entende isso entende variável, endereço e atribuição — e entendeu
jogando, não no quadro.

O código que escreve esse arquivo está em `servidor\cheats.py`, comentado em
português.


---

## Parte B — Não perder nada

Seu progresso, seus saves e seus recordes. Como o ARENA cuida sozinho e
como você leva tudo para outro lugar.

---

### O que o ARENA faz sem você pedir

| Quando | O que acontece |
|---|---|
| Você fecha um jogo | Cópia dos recordes, do perfil e dos saves vai para `backup` |
| Um amigo está ligado | Seus recordes sobem para ele na hora |
| A internet volta | Nova cópia de segurança, sozinha |
| Você fecha o ARENA | O banco é fechado direito e a janela avisa quando dá para tirar o pen drive |

São mantidas as **3 cópias mais recentes**. As antigas somem sozinhas para
não encher o pen drive.

**Você não precisa lembrar de fazer backup.** Se lembrar e quiser forçar
uma cópia, é *Ajustes → Máquina → Fazer cópia agora*.

---

### Sem internet, nada se perde

Você joga a tarde inteira sem rede. Cada pontuação fica guardada, marcada
como pendente — o número amarelo no botão **Enviar recordes** mostra
quantas.

Quando encontrar um amigo ligado ou chegar na escola, sobe tudo. Se você
esquecer de clicar, o ARENA percebe sozinho e manda.

---

### Levar seu progresso para outro lugar

Serve para: trocar de computador, formatar o pen drive, levar seus saves
para casa, ou só guardar em lugar seguro.

#### Montar o pacote

1. **Ajustes → Máquina**
2. Role até **Levar meu progresso para outro lugar**
3. **Montar meu pacote**

Pronto. Vai aparecer um arquivo na pasta `backup`, com o nome
`meu-progresso-2026-09-06_1430.zip`.

Dentro dele vão:

| Item | Volta ao importar? |
|---|---|
| Todos os seus saves | **Sim** |
| Os 10 save states de cada jogo | **Sim** |
| Os cheats que você cadastrou | **Sim** |
| Cópia dos seus recordes (`arena.db`) | Não — vai junto só para guardar |
| Cópia das suas configurações | Não — vai junto só para guardar |

**Por que recordes e configurações não voltam sozinhos:** eles são da
máquina onde você está. Trazer o `arena.db` de outro lugar apagaria o
placar de quem já jogou ali. Recorde viaja pela sincronização com os
amigos, não pelo pacote — veja o documento 5.

Se você quiser mesmo restaurar os recordes de um pacote, feche o ARENA,
abra o `.zip` à mão e copie `dados\arena.db` por cima.

**Não vão os jogos.** Só o seu progresso. É por isso que o pacote é pequeno
e dá para mandar por qualquer meio.

#### Trazer de volta

1. Copie o arquivo `.zip` para a pasta `backup` do outro ARENA
2. Lá: **Ajustes → Máquina**
3. O pacote aparece na lista → **Trazer de volta**

#### O que ele NÃO faz

**Não sobrescreve o que já existe.** Se você já jogou naquela máquina, seu
save de lá continua valendo. O pacote só preenche o que estava faltando.

Isso é de propósito: é impossível perder progresso por trazer um pacote
antigo por engano.

---

### Mudar de computador

Você tem dois caminhos. Escolha pelo que quer levar.

#### Levar tudo, inclusive os jogos

Copie a pasta `ARENA` inteira. Acabou.

Vão junto: jogos, saves, save states, cheats, recordes, configuração de
vídeo e som, mapeamento de teclado e de controle, lista de amigos e as
cópias de segurança.

O ARENA se ajusta sozinho ao novo lugar: mede a máquina nova, mede o disco
novo e reescreve as configurações na abertura.

#### Levar só o progresso

Use o pacote (acima). Serve quando a outra máquina já tem o ARENA com os
jogos, e você só quer seus saves e recordes.

---

### Onde cada coisa mora

| O quê | Onde | Tamanho típico |
|---|---|---|
| Saves do próprio jogo | `retroarch\saves\` | alguns KB cada |
| Save states (F2 e F4) | `retroarch\states\` | de 100 KB a 2 MB cada |
| Cheats | `retroarch\cheats\` | 1 KB cada |
| Fotos de tela (F8) | `retroarch\screenshots\` | uns 200 KB cada |
| Recordes | `dados\arena.db` | poucos KB |
| Configurações | `dados\config.json` | 2 KB |
| Cópias automáticas | `backup\` | 3 pastas + seus pacotes |

Nada disso sai da pasta do ARENA. Nunca.

---

### Quando o pen drive estiver enchendo

Veja o espaço em **Ajustes → Máquina → Espaço livre**. Ele também diz
quantos save states cabem ainda.

O que ocupa mais, na ordem:

1. **Os jogos** — não dá para reduzir, só apagar o que você não joga
2. **Save states** — de PlayStation em diante, cada um passa de 1 MB. Apague
   os espaços que não usa em *Saves e cheats*
3. **Fotos de tela** — apague direto de `retroarch\screenshots`
4. **Cópias antigas** — apague pastas velhas de `backup`

---

### Se der ruim

| O que aconteceu | O que fazer |
|---|---|
| Tirei o pen drive com o ARENA aberto e perdi os recordes | Copie `arena.db` de `backup\<data mais recente>` para `dados\` com o ARENA fechado |
| Apaguei um save sem querer | Se estava numa cópia, ele está em `backup\<data>\saves\` |
| Formatei o pen drive sem querer | Se você tinha montado um pacote e copiado para outro lugar, é só trazer de volta |
| O pacote não aparece na lista | Ele precisa estar na pasta `backup`, e terminar em `.zip` |
| "Pacote danificado" | A cópia veio incompleta. Copie de novo do original |

---

### A regra que evita 90% dos problemas

**Feche o ARENA antes de tirar o pen drive.**

A janela preta escreve *"Pode retirar o pen drive com segurança"* quando
terminou de gravar. Espere essa linha.

Se você esquecer, o ARENA se recupera na próxima abertura e ainda tem as
cópias em `backup`. Mas é chato, e é evitável com dois segundos de
paciência.


---
