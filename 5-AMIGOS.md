# 5 — Amigos, servidor e jogar a dois

Ver a pontuação dos colegas e jogar junto, com ou sem Wi-Fi.

**Neste documento:**

- Parte A — Servidor da sala e amigos
- Parte B — Jogar a dois e assistir

---

## Parte A — Servidor da sala e amigos

Ver a pontuação dos colegas, comparar tempo de jogo e jogar a dois.

**Funciona sem internet. Funciona sem roteador. Funciona sem Wi-Fi.**

---

### Como funciona

Todo ARENA é servidor. Não existe computador central obrigatório: o seu
ARENA fala direto com o do colega.

O servidor da escola, quando existe, é só mais um amigo da lista. Se ele
estiver desligado, vocês continuam trocando entre si normalmente.

E tem um detalhe: o que a Marina mandou para o Lucas **chega à escola pelo
ARENA do Lucas**, mesmo sem a Marina conhecer a escola. A informação se
espalha sozinha por quem está conectado.

---

### Passo 1 — Escolha seu apelido

No topo da tela, em **Jogando como**. É por ele que os colegas vão te
reconhecer.

Apelido, nunca nome completo.

---

### Passo 2 — Ligue duas máquinas na mesma rede

Você tem quatro jeitos. Escolha o primeiro que servir para o seu caso.

#### Jeito 1 — Já estão no mesmo Wi-Fi

Não precisa fazer nada. Vá para o passo 3.

#### Jeito 2 — Não tem Wi-Fi, mas tem um cabo de rede

**Ligue o cabo direto de um computador no outro.** Sem roteador, sem nada no
meio.

O Windows dá um endereço sozinho para cada um, em poucos segundos. Não
precisa configurar absolutamente nada.

No ARENA vai aparecer um endereço com a etiqueta **"Cabo direto entre dois
PCs"**. É esse que você passa para o colega.

Cabo de rede comum serve. Placa de rede de qualquer notebook dos últimos 15
anos faz a inversão sozinha — não precisa de cabo cruzado.

#### Jeito 3 — Não tem cabo nem Wi-Fi: um notebook vira a rede

1. Num dos computadores: **Configurações → Rede e Internet → Ponto de
   acesso móvel**.
2. Ligue. Anote o nome da rede e a senha que aparecem.
3. O outro conecta nessa rede como conectaria em qualquer Wi-Fi.

Não precisa de internet para isso funcionar. O notebook cria a rede do
nada.

No ARENA vai aparecer um endereço com a etiqueta **"Ponto de acesso do
Windows"**.

#### Jeito 4 — O celular vira a rede

Ligue o roteamento de Wi-Fi do celular (o mesmo que você usa para dar
internet ao notebook) e conecte os dois computadores nele.

**Não precisa ter internet no celular.** Ele cria a rede do mesmo jeito, e é
só isso que o ARENA precisa. Se você desligar os dados móveis, nem consome
seu pacote.

#### Jeito 5 — Sem rede nenhuma: a mala do pen drive

Se não dá para ligar as máquinas de jeito nenhum, os recordes ainda viajam.

1. No seu ARENA: **Ajustes → Amigos → Trocar pelo pen drive**.
2. Leve o pen drive até a máquina do colega.
3. No ARENA dele, o mesmo botão.
4. Volte e clique de novo no seu.

Pronto. Os dois ficam com os recordes dos dois, sem nunca terem se falado.

O ARENA guarda um arquivo chamado `ARENA-troca.json` na raiz da mídia — a
"mala". Cada máquina que a mala visita deixa o que tem de novo e leva o que
ainda não tinha.

**Passar a mala dez vezes não duplica nada**, pelo mesmo motivo da rede:
cada recorde tem identificação própria.

E ela funciona como ponte: se a mala passou pela máquina de um terceiro
colega antes de chegar em você, os recordes dele vêm junto.

#### Jeito 6 — Wi-Fi da escola que não deixa as máquinas se verem

Se o ping não responde entre dois computadores no mesmo Wi-Fi, é
**isolamento de cliente**: o roteador está configurado de propósito para os
aparelhos não conversarem. Não tem como desligar sem acesso ao equipamento.

Use o jeito 2 ou o jeito 3. Os dois criam uma rede própria, fora do
controle do roteador da escola.

---

### Passo 3 — Deixe o colega te achar

**Ajustes → Amigos → Aceitar conexões da rede.**

Ligue e **feche e abra o ARENA**. A mudança só vale depois de reiniciar.

Logo abaixo aparece a lista de endereços do seu computador:

| Etiqueta | Quando usar |
|---|---|
| **Rede local** | Mesmo Wi-Fi ou mesmo switch |
| **Ponto de acesso do Windows** | Você criou a rede pelo notebook |
| **Cabo direto entre dois PCs** | Cabo ligado direto, sem roteador |
| **Só este computador** | A rede ainda não foi liberada |

Passe **um** deles para o colega. Se aparecer mais de um, tente o primeiro;
não funcionou, tente o próximo.

Na primeira vez o Windows pergunta se o Python pode se comunicar na rede.
**Marque "Redes privadas" e clique em Permitir acesso.**

---

### Passo 4 — Adicione o amigo

#### O jeito fácil: deixe o ARENA achar

Em **Ajustes → Amigos**, logo abaixo da sua lista, tem **Colegas
encontrados na rede**.

O ARENA avisa "estou aqui" na rede a cada cinco segundos e escuta quem mais
está avisando. Quem estiver na mesma rede aparece ali sozinho, com o
endereço já preenchido. Clique em **Adicionar** e acabou.

**Não precisa digitar endereço nenhum** — e some de vez o erro de copiar o
endereço do adaptador virtual.

Funciona em qualquer rede compartilhada: Wi-Fi da escola, ponto de acesso do
notebook, roteamento do celular ou cabo direto. Os dois precisam estar com
*Aceitar conexões da rede* ligado. Leva uns segundos para aparecer.

O aviso é um pacotinho de cem letras com apelido, código do aparelho e a
porta. Não leva recorde, não leva nome, não sai da rede local.

#### O jeito manual

**Ajustes → Amigos.**

1. **Apelido do amigo** — o apelido dele.
2. **Endereço que ele te passou** — pode digitar só o número; o ARENA
   completa o resto.
3. **Testar** — confirma que ele está no ar e já preenche o apelido sozinho.
4. **Adicionar**.

Fica guardado. Não precisa repetir.

---

### Passo 5 — Sincronize

Clique em **Enviar recordes**, no topo.

O ARENA fala com todos os amigos de uma vez e mostra quem respondeu, quem
estava fora do ar, quanto foi enviado e quanto chegou.

Amigo fora do ar não é erro — fica para a próxima.

**Sincronizar dez vezes não duplica nada.** Cada registro tem identificação
própria e o outro lado reconhece o que já recebeu.

E toda vez que você fecha um jogo, se algum amigo estiver ligado, o ARENA
sincroniza sozinho.

---

### Ver as estatísticas dos amigos

Depois de sincronizar, clique em **Recordes**, no topo. Duas abas.

#### Aba Pontuação

Mostra os cinco primeiros de cada jogo, misturando você e seus amigos:

```
Arena do João
  1  marina    9.900
  2  lucas     4.500
  2  bia       4.500
  3  você      3.200
```

Empate recebe a mesma posição — por isso aparecem dois segundos lugares.

#### Aba Tempo de jogo

Quanto tempo cada pessoa jogou cada jogo, e em quantas partidas:

```
Arena do João
  1  lucas     3 h 12 min · 27 partidas
  2  você      1 h 40 min · 14 partidas
```

É calculado sozinho. Você não precisa registrar nada.

Partida de menos de 30 segundos não conta — abrir e fechar não é jogar.

#### O que dá para descobrir olhando

| Pergunta | Onde ver |
|---|---|
| Quem é o melhor neste jogo? | Aba Pontuação, posição 1 |
| Quem jogou mais? | Aba Tempo de jogo |
| Que jogos meus amigos andam jogando? | Os títulos que aparecem nas duas abas |
| Meu recorde ainda está de pé? | Procure seu apelido na lista |
| Quantos recordes meus ainda não subiram? | O número amarelo no botão Enviar recordes |

#### Por que um amigo não aparece

| Motivo | Como confirmar |
|---|---|
| Vocês ainda não sincronizaram | Clique em **Sincronizar agora** |
| Ele não registrou pontuação nenhuma | Só sessões acima de 30 s e pontos registrados aparecem |
| Vocês não jogaram o mesmo jogo | O ranking é por jogo. Sem jogo em comum, não há comparação |
| Ele estava fora do ar na hora | A lista de amigos mostra bolinha azul para quem está online |

#### Um detalhe que confunde

**O placar que você vê é o do SEU ARENA.** Ele tem o que você registrou mais
o que chegou dos amigos com quem você sincronizou.

Se o Lucas sincronizou com a Marina e você só sincronizou com o Lucas, você
vê os três — porque o que a Marina mandou passou pelo ARENA do Lucas.

Mas se você nunca sincronizou com ninguém, vê só o seu.

Para ver o placar completo da turma, abra **o endereço do servidor da
escola** no navegador e clique em Recordes lá.

---

### Jogar a dois

Depois que vocês são amigos:

**Quem vai abrir:** clique em **Jogar junto** na linha do jogo → **Eu abro a
partida** → **Começar**. Você é o jogador 1.

**Quem vai entrar:** clique em **Jogar junto** no **mesmo jogo** → **Entrar
na partida do amigo** → cole o endereço → **Começar**. Você é o jogador 2.

Os dois precisam do **mesmo arquivo de jogo**. Se um tiver a versão
americana e o outro a japonesa, a partida nem começa.

Pela rede não passa vídeo nem som, só *"o jogador 2 apertou soco"*. Por isso
funciona bem até em cabo direto entre dois computadores fracos.

Detalhes no **neste mesmo documento**.

---

### O que é trocado

| Vai | Não vai |
|---|---|
| Apelido | Nome, matrícula, endereço |
| Pontuação registrada | Seus arquivos de jogo |
| Tempo de partida acima de 30 s | Jogos salvos |
| Nome do jogo e do console | Save states |
| Quando aconteceu | Fotos de tela |

São algumas centenas de bytes por registro.

**Só quem tem o ARENA participa.** Não existe site, conta nem cadastro em
lugar nenhum.

---

### Montar o servidor da sala

Para quem vai centralizar o placar na TV.

1. **Onde:** SSD por adaptador USB 3.2 é o melhor. Disco `C:` também serve.
   **Cartão SD não** — documento 1.
2. Ligue **Aceitar conexões da rede** e reinicie o ARENA.
3. Escreva o endereço na lousa.
4. Libere no firewall quando o Windows perguntar.

Para projetar: abra o endereço do servidor no navegador da TV e clique em
**Recordes**.

#### Se o firewall não perguntou

1. Iniciar → **Firewall do Windows Defender com Segurança Avançada**
2. **Regras de Entrada → Nova Regra**
3. **Porta** → Avançar
4. **TCP**, portas locais específicas: `8777` → Avançar
5. **Permitir a conexão** → Avançar
6. Marque só **Particular** → Avançar
7. Nome: `ARENA` → Concluir

---

### Cada ARENA precisa do seu próprio código

Se a pasta do ARENA foi copiada para vários pen drives, **todos saem com o
mesmo código de aparelho** — e isso quebra tudo. Cada ARENA acha que o outro
é ele mesmo, a sincronização não sai do lugar e a partida a dois recusa a
conexão.

**O ARENA resolve sozinho na primeira abertura.** O código passou a nascer
da própria máquina, não do arquivo copiado.

Para conferir: **Ajustes → Amigos → Código deste ARENA**. Dois colegas com o
mesmo código é sinal de problema.

E se mesmo assim dois computadores saírem iguais — acontece em laboratório
onde as máquinas vêm da mesma imagem, com o mesmo nome e o mesmo usuário —
o ARENA percebe na primeira sincronização, troca o dele e avisa. Basta
sincronizar de novo.

---

### O botão que diz onde está o problema

Na janela de **Jogar junto** tem o botão **Testar antes de começar**. Cole o
endereço do colega e clique. Ele responde uma de três coisas:

| Resposta | O que fazer |
|---|---|
| ARENA responde, partida aberta | Está tudo certo. Pode começar |
| ARENA responde, partida fechada | Ele não clicou em *Eu abro a partida*, **ou o firewall dele bloqueia o retroarch.exe** |
| **Arquivo: DIFERENTE** | Vocês têm o mesmo jogo, mas arquivos diferentes. **A partida não começa assim** |
| Ele não tem esse jogo | Passe o arquivo antes de começar |
| ARENA não responde | Endereço errado, ou ele não ligou *Aceitar conexões da rede* |

---

### O arquivo tem que ser o MESMO, não só o mesmo jogo

Esta é a causa mais comum de "conecta e não começa", e a mais difícil de
perceber sozinho.

Versão americana e europeia, revisão 1 e revisão 2, com e sem cabeçalho: são
arquivos diferentes. O título na lista fica igual, e o RetroArch recusa a
conexão sem explicar.

O botão **Testar antes de começar** agora compara os dois arquivos e diz na
cara: *"Vocês têm o mesmo jogo, mas ARQUIVOS DIFERENTES"*.

Ele compara o começo, o fim e o tamanho do arquivo — dois arquivos
diferentes praticamente nunca batem nos três.

**Solução:** um dos dois copia o arquivo do outro. Use o pen drive, ou a
pasta compartilhada.

---

### Ordem importa: abra primeiro, entre depois

Quem hospeda clica **Eu abro a partida** e **espera o jogo aparecer na
tela**. Só então o outro clica em Entrar.

Se o convidado clicar antes, a conexão falha uma vez e não tenta de novo.
Fechem os dois e comecem de novo, na ordem.

---

### O firewall pede permissão DUAS vezes

Esse é o motivo mais comum de "o ARENA conecta mas a partida não começa".

São dois programas diferentes pedindo passagem:

| Programa | Porta | Quando o Windows pergunta |
|---|---|---|
| **Python** | 8777 | Ao ligar *Aceitar conexões* pela primeira vez |
| **retroarch.exe** | 55435 | Ao **abrir uma partida** pela primeira vez |

Se você clicou em "Cancelar" na segunda, a partida nunca conecta — mesmo com
o ARENA funcionando perfeitamente.

Para liberar na mão, nos dois computadores:

1. Iniciar → **Firewall do Windows Defender com Segurança Avançada**
2. **Regras de Entrada → Nova Regra → Porta → TCP → 55435**
3. **Permitir a conexão** → marque só **Particular** → nome: `ARENA partida`

---

### Endereço certo e endereço que não serve

O ARENA lista mais de um endereço. Nem todos servem:

| Etiqueta | Serve? |
|---|---|
| Rede local | **Sim** |
| Ponto de acesso do Windows | **Sim** |
| Cabo direto entre dois PCs | **Sim** |
| **Adaptador virtual** | **Não.** É do WSL, VirtualBox ou máquina virtual. Ninguém alcança |

Os virtuais aparecem por último e vêm marcados. Se você copiou um deles por
engano, era esse o problema.

---

### Quando não conecta

Teste nesta ordem, sem pular etapa.

| Ordem | Teste | Se falhar |
|---|---|---|
| 1 | No ARENA dele, abrir `http://127.0.0.1:8777` | O ARENA dele não está aberto |
| 2 | Na janela preta dele, diz "Rede: LIBERADA"? | Ele não fez o passo 3, ou não reiniciou |
| 3 | No Prompt, `ping` no endereço dele | As máquinas não se enxergam. Volte ao passo 2 |
| 4 | Ping responde mas o ARENA não | É o firewall dele |

---

### Problemas

| Sintoma | Solução |
|---|---|
| "Este endereço é o próprio computador" | Você digitou o seu. Use o do amigo |
| "Já existe um amigo com esse apelido" | Remova o antigo, ou use outro apelido |
| "Não respondeu" ao testar | O ARENA dele está fechado ou a rede não foi liberada |
| Só aparece "Só este computador" | Passo 3 não foi feito, ou o ARENA não foi reiniciado |
| Só aparece "Cabo direto" | Normal, e está certo. Use esse endereço |
| Sincronizou e o placar não mudou | `recebidos: 0` quer dizer que nada era novo |
| A escola não vê minha pontuação | Cadastre a escola como amigo, ou peça a um colega que já a tenha para sincronizar com você |

---

### Privacidade

O banco guarda **apelido, jogo, pontos e tempo**. Nada além disso.

Dado de estudante menor de idade é dado pessoal sob a LGPD, e o artigo 14
exige tratamento no melhor interesse do adolescente. A forma mais segura de
proteger um dado é não coletá-lo.

Se alguém pedir nome completo no ranking, a resposta é não.


---

## Parte B — Jogar a dois e assistir

Dois jogando o mesmo jogo, como se estivessem no mesmo sofá — só que cada um
no seu computador.

---

### Como funciona

Os dois computadores rodam **o mesmo jogo ao mesmo tempo**. Pela rede não
passa vídeo nem som: passa só *"o jogador 2 apertou soco"*.

É exatamente assim que funcionavam os arcades ligados em rede, e é por isso
que funciona bem até em Wi-Fi fraco — são poucos bytes por quadro.

**Quem abre a partida é o jogador 1. Quem entra é o jogador 2.**

### Passo a passo

**No computador de quem vai abrir:**

1. Ache o jogo na lista.
2. Clique em **Jogar junto**.
3. Escolha **Eu abro a partida**.
4. **Começar**.
5. Passe seu endereço para o amigo. Ele está em *Ajustes → Amigos → Meu
   endereço*.

**No computador de quem vai entrar:**

1. Ache **o mesmo jogo** na lista.
2. Clique em **Jogar junto**.
3. Escolha **Entrar na partida do amigo**.
4. Cole o endereço que ele passou.
5. **Começar**.

A tela abre e vocês estão jogando juntos.

### Precisa ser o mesmo arquivo

Os dois precisam ter **o mesmo jogo, com o mesmo arquivo**. Se um tiver a
versão americana e o outro a japonesa, a partida nem começa — o RetroArch
compara os arquivos antes de conectar.

Combine antes quem passa o arquivo para quem.

### Jogos que funcionam

Qualquer jogo de **dois jogadores no mesmo console**: luta, corrida,
esporte, plataforma cooperativa. Se dava para jogar com dois controles no
aparelho de verdade, dá para jogar assim.

Não funciona em jogo de um jogador só. Nesse caso o segundo entra como
espectador.

### Como a tela fica em cada um

Isto costuma surpreender, então vale explicar antes.

**Os dois computadores rodam o mesmo console emulado.** Cada um desenha a
mesma imagem que o outro. Por isso:

| Tipo de jogo | O que cada um vê |
|---|---|
| **Tela única** — luta, esporte, quebra-cabeça | Tela cheia, imagem completa. Fica perfeito |
| **Tela dividida** — corrida, tiro em primeira pessoa | A mesma tela dividida ao meio, nos dois |

Killer Instinct, Street Fighter, futebol: cada um na sua tela cheia, imagem
idêntica, do jeito que você espera.

Twisted Metal 2 em dois jogadores, Top Gear, Mario Kart: **os dois veem a
tela dividida**, com as duas metades. Não dá para separar.

Por quê: o PlayStation de verdade gerava **um** sinal de vídeo, com as duas
metades dentro. A divisão está na imagem que o jogo desenha, não em como
ela é mostrada. Não existe configuração de emulador que separe isso — nem
no ARENA, nem no RetroArch, nem em nenhum outro.

Se você quer que cada aluno tenha a tela inteira só para ele, escolha jogos
de tela única. Numa aula de dois computadores, jogo de luta funciona melhor
que corrida.

### Trocar quem é o 1 e quem é o 2

Dentro do jogo: `Esc → Rede → Trocar dispositivos`. Ou fechem tudo e abram
de novo invertendo quem hospeda.

### Só na mesma rede

Funciona no laboratório da escola, ou na mesma casa, ou no mesmo Wi-Fi.

**De uma casa para outra pela internet não funciona.** A internet
residencial brasileira usa CGNAT — o aluno não tem endereço próprio na
internet, então não existe porta para o amigo alcançar. Não é limitação do
ARENA; é como a internet de casa funciona aqui.

Se as máquinas da escola não se enxergam, é isolamento de cliente no
roteador. As saídas estão na Parte A deste mesmo documento.

### Quando dá problema

| O que aconteceu | O que fazer |
|---|---|
| Não conecta | Confira se os dois têm o mesmo arquivo de jogo |
| "Aguardando" e não sai disso | O endereço está errado, ou o firewall bloqueou a porta 55435 |
| Conectou mas está travando | Ligue a chave "casas diferentes", que já entra com folga. Ou, no jogo: `Esc → Rede → Atraso de Entrada` |
| Está lento em máquina fraca | Normal: partida a dois custa o dobro. O ARENA já desliga filtros e efeitos durante a partida |
| Os dois controlam o jogador 1 | Quem entrou não pediu o jogador 2. Fechem e abram de novo |
| Dessincronizou no meio | `Esc → Rede → Desconectar` e entrem de novo |

---

Configuração de controle: **documento 3**.


---
