# ARENA — o console da turma

Você copia a pasta, dá dois cliques e joga. Não instala nada.

Tudo fica dentro da pasta: seus jogos, seus saves, seus recordes. Copiou a
pasta para outro computador, levou tudo junto.

---

## Começando

**1.** Dois cliques em **`ARENA.bat`**.
Abre uma janela preta. **Não feche ela.** É ela que faz o ARENA funcionar.

**2.** O ARENA abre sozinho na tela.
Escreva seu apelido lá em cima, onde diz *Jogando como*.

**3.** Clique num jogo.
Ele abre em alguns segundos.

**4.** Terminou? Aperte **F10** para fechar o jogo.
Para desligar o ARENA, feche a janela preta.

---

## Teclas dentro do jogo

| Tecla | O que faz |
|---|---|
| **Esc** | Abre o menu (save, cheats, configurações) |
| **F2** | Salva onde você está |
| **F4** | Volta para onde você salvou |
| **F6** e **F7** | Trocam entre os 10 lugares de salvar |
| **F8** | Tira foto da tela |
| **F10** | Fecha o jogo |

Atenção: **Esc não fecha o jogo, abre o menu.** Para fechar é F10.

---

## Os documentos

Seis documentos. Cada um tem passos numerados e uma tabela de problemas.

| # | Documento | Para quê |
|---|---|---|
| **1** | COMECAR | Preparar o pen drive e montar o ARENA |
| **2** | JOGOS | Colocar jogos nas pastas, liberar console, PCSX2 |
| **3** | IMAGEM-SOM-CONTROLE | Controle, travamento, som, ajuste fino por console |
| **4** | SAVES | Os 10 saves, os cheats e não perder nada |
| **5** | AMIGOS | Servidor da sala, pontuação dos colegas, jogar a dois |
| **6** | RECURSOS-E-REPARO | As 50 opções explicadas e o verificador |

**Só quer jogar hoje?** Documentos 1 e 2. O resto é quando precisar.

---

## Organizar os jogos por pasta

Quem decide o console de um jogo é **a pasta em que ele está**, igual ao
RetroArch. O ARENA não adivinha.

1. Clique em **Criar pastas dos consoles**, embaixo da lista à esquerda.
2. Arraste cada jogo para a pasta dele: `PS1`, `PS2`, `Nintendo 64`…
3. Clique em **Atualizar lista**.

Jogo solto aparece no topo, em **Precisa escolher o console**. Para
resolver, **arraste a linha do jogo para cima do console certo** — o ARENA
move o arquivo para a pasta de verdade.

Detalhes no documento 2.

---

## Recebeu esta pasta de outra pessoa?

**Ajustes → Perfil → Começar do zero.**

Apaga o apelido, os recordes, a lista de amigos, o mapeamento de controle e
as configurações de quem te passou. **Os jogos ficam.** Você escolhe se quer
apagar os saves também.

O ARENA cria um código de aparelho novo — é ele que faz você aparecer como
uma pessoa diferente para os colegas.

Antes de apagar, guarda uma cópia em `backup`. Clicou por engano? Dá para
voltar.

---

## Configurar o controle

Em **Ajustes → Controles**, o ARENA mapeia com os nomes do seu console.

**Plugou e quer jogar agora?** Clique em **Mapear meu controle sozinho**.
Ele preenche os 16 botões de uma vez, e funciona em Xbox, PlayStation 4 e 5,
Switch Pro, Steam Controller e genéricos.

Para ajustar um botão específico: escolha o console, escolha o jogador,
clique em **Definir** e **aperte a tecla ou o botão** — ele reconhece
sozinho qual dos dois foi.

Analógico e direcional funcionam ao mesmo tempo, e a vibração vem ligada.

Se você escolher PlayStation 2, a lista fala em X, Círculo, Quadrado e
Triângulo, não em "botão A" e "botão B".

Detalhes no documento 3.

---

## Sem Wi-Fi? Sem problema

São cinco jeitos de jogar junto e trocar recordes, do mais simples ao mais
teimoso:

| Jeito | Quando |
|---|---|
| Mesmo Wi-Fi | O normal |
| Cabo de rede direto entre dois PCs | Sem roteador nenhum |
| Um notebook vira a rede | Sem cabo e sem Wi-Fi |
| O celular vira a rede | Nem precisa de internet nele |
| **A mala do pen drive** | Sem rede de jeito nenhum |

A mala é o último recurso e nunca falha: você leva o pen drive até a máquina
do colega, clica em *Trocar pelo pen drive* nos dois, e os recordes se
juntam. Documento 5.

E para jogar de casa, cada um na sua, tem a chave **Estamos em casas
diferentes** na janela de Jogar junto.

---

## O que o ARENA não faz

**Não grava vídeo da partida e não transmite ao vivo.** O RetroArch sabe
fazer as duas coisas; o ARENA desliga e tira as teclas de atalho.

Gravar aula com voz e imagem de estudante menor de idade, ou transmitir
para a internet, são dois problemas que não têm o que fazer numa escola.

Foto da tela com `F8` continua funcionando: imagem parada, salva na pasta,
sem áudio e sem sair do computador.

---

## Botões que aparecem em toda tela

| Botão | O que faz |
|---|---|
| **Fechar** | Fecha o painel lateral. A tecla `Esc` faz o mesmo |
| **Cancelar** | Sai da janelinha sem salvar nada |
| **Mostrar mais** | A lista carrega 200 jogos por vez. Clique para ver os próximos |
| **Criar pastas dos consoles** | Cria as 47 pastas em `jogos\\pessoais` |
| **Atualizar lista** | Relê as pastas depois que você mexeu nos arquivos |

---

## Quando dá problema

| O que aconteceu | O que fazer |
|---|---|
| A janela preta some na hora | Falta o Python. Documento 1 |
| Diz que a porta 8777 está em uso | O ARENA já está aberto. Procure a outra janela preta |
| Diz que faltou o RetroArch | A pasta tem que se chamar `retroarch`. Documento 1 |
| A lista está vazia | Clique em Atualizar lista. Documento 2 |
| Nenhum jogo abre | Ajustes → Máquina → botão de copiar as bibliotecas |
| Jogo de PlayStation 2 não abre | Documento 2, parte B. Precisa do PCSX2 |
| O jogo abre e fecha na hora | Documento 2 (falta arquivo) ou 4 (motor gráfico) |
| Trava ou o som falha | Documento 2 |
| Diz que já tem um jogo aberto | Feche o outro com F10 |
| Não sei o que houve, só sei que quebrou | Dois cliques em **`VERIFICAR.bat`**. Documento 6 |

---

## Três regras

**1. Não passe jogo comercial para os colegas.** A pasta `jogos\\pessoais` é
sua e fica no seu pen drive.

**2. Use apelido, nunca seu nome completo.**

**3. O jogo é o objeto de estudo.** Você vai ver como o ARENA encontra os
jogos, como guarda os recordes e como conversa com os outros computadores.
Quem só joga aprende metade.

---

## Quer mexer no código?

Está tudo aqui dentro, comentado em português.

| Arquivo | O que faz |
|---|---|
| `servidor\\indexador.py` | Procura os jogos nas pastas |
| `servidor\\hardware.py` | Descobre como é o seu computador |
| `servidor\\arena.py` | O servidor, o banco e a conversa com os amigos |
| `servidor\\cheats.py` | Os saves e os códigos |
| `servidor\\graficos.py` | Imagem, BIOS, memory card e partida a dois |
| `servidor\\controles.py` | Mapeamento de teclas e botões |
| `servidor\\perfis_controle.json` | O que cada controle e cada console têm |
| `servidor\\recursos.json` | Os 50 recursos da aba Avançado |
| `servidor\\graficos.json` | Ajuste fino de imagem de cada emulador |
| `launcher\\` | A tela que você está usando |

Comece por aqui, do mais fácil para o mais difícil:

1. `launcher\\estilo.css` — as cores estão todas no topo. Mude uma e recarregue.
2. `servidor\\consoles.json` — acrescente uma extensão e veja a lista mudar.
3. `servidor\\indexador.py`, na função `limpar_titulo` — mude como o nome do
   jogo aparece.

Se estragar tudo, é só copiar a pasta original de novo.