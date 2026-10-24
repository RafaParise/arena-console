# 1 — Começar do zero

Preparar a mídia e montar o ARENA. Faça uma vez; depois é copiar e colar.

**Neste documento:**

- Parte A — Preparar o pen drive ou o SSD
- Parte B — Instalação (o jeito fácil: baixar o ARENA pronto do GitHub; ou
  montar peça por peça)
- Parte C — No Chromebook (o mesmo pen drive, dentro do Chrome)
- Parte D — No Linux (o mesmo pen drive, sem instalar nada)
- Parte E — No celular ou no tablet Android (o app do ARENA)

---

## Parte A — Preparar o pen drive ou o SSD

Faça isto antes de instalar o ARENA. Cinco minutos.

Se você vai usar o ARENA só no disco `C:` do computador, **pule para a
Parte B** deste documento. Nada aqui é obrigatório.

---

### Antes de começar

> **Formatar apaga tudo o que está na mídia.** Copie o que interessa para
> outro lugar antes.

---

### Passo 1 — Escolher a mídia

| Mídia | Serve? | Observação |
|---|---|---|
| **SSD por adaptador USB** | A melhor | Aguenta escrita constante. Use no servidor da sala |
| **Pen drive USB 3.0 ou 3.1** | Muito bom | O ideal para o aluno |
| Pen drive USB 2.0 | Funciona | Tudo demora mais na primeira abertura |
| Cartão SD por leitor USB | Só para guardar | Não rode o ARENA dele. Ver passo 6 |
| HD externo | Funciona | Mais lento para abrir jogo em CD |

**Espaço mínimo:** 4 GB. Com jogos, 16 GB ou mais.

**Como saber se a porta é rápida:** porta azul por dentro, ou com a marca
`SS` ao lado. Porta preta é USB 2.0.

---

### Passo 2 — Formatar em exFAT

1. Conecte a mídia.
2. Abra o **Explorador de Arquivos**.
3. Clique com o botão direito na unidade → **Formatar**.
4. Preencha assim:

| Campo | O que escolher |
|---|---|
| Sistema de arquivos | **exFAT** |
| Tamanho da unidade de alocação | Padrão |
| Rótulo do volume | `ARENA` |
| Formatação rápida | **marcado** |

5. **Iniciar** → confirme.

Leva menos de um minuto.

#### Por que exFAT

| Sistema | Arquivo acima de 4 GB | Lido em Windows, Linux e Mac | Permissões atrapalham? |
|---|---|---|---|
| **exFAT** | Sim | Sim | Não |
| FAT32 | **Não** | Sim | Não |
| NTFS | Sim | Parcialmente | **Sim** |

FAT32 não serve porque um jogo de PlayStation 2 passa de 4 GB.

Se o ARENA estiver num pen drive em FAT32, ele avisa: o botão **Como colocar
jogos** mostra "Atenção" nos consoles de jogo grande (PlayStation 2 e 3, Wii
e Xbox 360), antes de você copiar. E um jogo que chegou cortado no limite de
4 GB ganha, no cartão, a explicação do que houve.

NTFS funciona, mas grava dono e permissão em cada arquivo. Quando o pen
drive passa de mão em mão, o Windows do colega às vezes recusa acesso. É um
problema que só aparece na hora errada — evite.

---

### Passo 3 — Criar a pasta

Na raiz da mídia, crie uma pasta chamada **`ARENA`**. Só isso.

Deve ficar assim:

```
E:\ARENA\
```

Não coloque em `E:\Documentos\Jogos\Emuladores\ARENA\`. Caminho curto evita
problema com nome de arquivo comprido, que ainda existe no Windows.

---

### Passo 4 — Instalar

Continue na **Parte B — Instalação**, logo abaixo.

---

### Passo 5 — Retirar com segurança

**Feche o ARENA antes de puxar o pen drive.**

A janela preta escreve *"Pode retirar o pen drive com segurança"* quando
terminou de gravar. Só desconecte depois disso.

Se puxar antes, o arquivo de recordes pode estragar. O ARENA guarda cópia
automática em `backup`, então dá para recuperar — mas é chato e evitável.

---

### Passo 6 — O cartão SD

O cartão SD grava devagar quando são muitos pedacinhos espalhados. E ele se
gasta rápido. O ARENA grava no arquivo de recordes o tempo todo. Num cartão,
isso gasta o cartão aos poucos. Cedo ou tarde, o arquivo estraga no meio da
aula. É como apagar e escrever sempre no mesmo canto da folha: uma hora o
papel rasga.

**Não rode o ARENA do cartão SD.** Use o cartão para o que ele faz bem:

- guardar a cópia de segurança da pasta `backup`;
- guardar o acervo de jogos que você só copia de lá, sem rodar;
- levar uma cópia completa do ARENA como reserva.

---

### Passo 7 — Levar para outro computador

Não existe instalação. Copie a pasta `ARENA` inteira e dê dois cliques em
`ARENA.bat`.

Vai junto: seus jogos, saves, os 10 save states, cheats, recordes,
configuração de vídeo e som, mapeamento de teclado e controle, e a lista de
amigos. Tudo mora dentro da pasta.

**Do pen drive para o PC:** copie a pasta para `C:\ARENA`.

**Do PC para o pen drive:** copie a pasta para a raiz da mídia.

Nos dois casos o ARENA se ajusta sozinho ao novo lugar. Ele mede a máquina e
o disco na abertura e reescreve as configurações.

---

### Problemas

| Sintoma | Causa | Solução |
|---|---|---|
| exFAT não aparece na lista | Mídia pequena demais | Use FAT32 e evite jogos acima de 4 GB, ou troque a mídia |
| "O Windows não conseguiu concluir a formatação" | Mídia protegida ou com defeito | Veja se há chavinha de proteção na lateral. Se não houver, a mídia pode estar no fim da vida |
| Tudo muito lento | Porta USB 2.0, ou pen drive antigo | Use porta azul. Na primeira abertura o ARENA varre tudo; depois fica rápido |
| Windows pede para formatar toda vez que conecta | Sistema de arquivos corrompido | Formate de novo em exFAT |
| Pasta some ou aparece vazia | Mídia retirada com o ARENA aberto | Feche o ARENA antes de retirar |


---

## Parte B — Instalação

Faça uma vez. Depois é só copiar e colar a pasta.

### O jeito fácil: baixar o ARENA pronto (GitHub)

**Tempo:** 10 minutos, mais o download (uns 480 MB; descompactado, 1,3 GB).

1. Abra <https://github.com/RafaParise/arena-console/releases/latest>.
2. Baixe o arquivo **`ARENA-` + a versão + `.zip`**, na parte *Assets*.
3. **Antes de descompactar, desbloqueie:** botão direito no `.zip` →
   **Propriedades** → embaixo, em *Segurança*, marque **Desbloquear** →
   **OK**. Não precisa de senha de administrador. Sem esse passo, o Windows
   marca cada programa de dentro do pacote como "vindo da internet" e
   pergunta, um por um, se pode abrir.
4. Descompacte na raiz do disco: em **Extrair tudo**, troque o destino por
   `C:\` — o `.zip` já traz a pasta `ARENA`, e fica `C:\ARENA`. No pen drive
   em exFAT (Parte A), o destino é a raiz dele (`D:\`, por exemplo).
5. Dois cliques em **`ARENA.bat`**. Pronto: pule para o **Passo 5 — Testar**.

O pacote já traz o Python, o RetroArch com os núcleos e os emuladores de
fora (PCSX2, Dolphin, RPCS3, Xenia). **Não traz jogos nem BIOS:** são de
quem tem o console. Ponha cada BIOS em `BIOS\<console>` e o ARENA instala
sozinho (documento 2).

Prefere montar peça por peça (sem internet rápida, ou para estudar como o
ARENA é feito)? Siga os passos abaixo.

### Montar peça por peça

**Tempo:** 20 minutos.

---

### Passo 1 — Criar a pasta

Crie `C:\ARENA` e copie tudo deste pacote para dentro.

Monte primeiro no disco `C:`. É mais rápido para montar e testar. Só depois
copie para o pen drive ou o SSD.

Se você já preparou a mídia pela **Parte A** deste documento, pode montar direto nela.

---

### Passo 2 — Colocar o Python dentro da pasta

1. Acesse `python.org` → **Downloads** → **Windows**.
2. Baixe **Windows embeddable package (64-bit)**. É um `.zip` de uns 10 MB.
   **Não é o instalador** — é a versão que roda de qualquer pasta.
3. Descompacte dentro de `servidor\python`.

Precisa existir exatamente este caminho:

```
ARENA\servidor\python\python.exe
```

Se o `python.exe` ficou dentro de mais uma subpasta, mova os arquivos um
nível para cima.

---

### Passo 3 — Colocar o RetroArch dentro da pasta

1. Copie sua pasta do RetroArch para dentro de `ARENA`.
2. **Renomeie para `retroarch`** — minúsculo, sem número, sem sufixo.

Precisa existir:

```
ARENA\retroarch\retroarch.exe
ARENA\retroarch\cores\
```

---

### Passo 4 — Baixar os núcleos

Núcleo é o emulador de cada console.

1. Abra o `retroarch.exe` direto, uma vez.
2. **Carregar Núcleo → Baixar um Núcleo**.
3. Baixe estes:

| Console | Nome na lista |
|---|---|
| TIC-80 | TIC-80 |
| NES | Nintendo - NES / Famicom (FCEUmm) |
| Super Nintendo | Nintendo - SNES / SFC (Snes9x) |
| Mega Drive, Master System, Game Gear | Sega - MS/GG/MD/CD (Genesis Plus GX) |
| Game Boy e Color | Nintendo - Game Boy / Color (Gambatte) |
| Game Boy Advance | Nintendo - Game Boy Advance (mGBA) |
| Atari 2600 | Atari - 2600 (Stella) |
| PC Engine | NEC - PC Engine (Beetle PCE) |

4. Feche o RetroArch.

Os outros consoles (PlayStation, Nintendo 64, PSP, Saturn, Arcade, Neo Geo,
MSX, DS, GameCube, PS2, CD-i) funcionam igual: baixe o núcleo quando for
usar. O ARENA detecta sozinho.

---

### Passo 4b — A única instalação necessária

O ARENA não instala nada. Mas os emuladores são programas compilados com as
**bibliotecas gráficas da Microsoft** (Visual C++ Redistributable). Sem elas
o RetroArch nem abre, e o Windows mostra um erro que não explica nada.

**A maioria dos computadores já tem**, porque quase todo programa instala
junto. O ARENA confere na abertura e avisa no topo da tela se faltar.

Se faltar, tente primeiro o botão do ARENA. Vá em **Ajustes → Máquina** e
clique em **Copiar para a pasta do ARENA**. Não precisa de senha de
administrador.

A tela disse que este computador também não tem as bibliotecas? Então baixe
o **Microsoft Visual C++ Redistributable (x64)** no site da Microsoft e
instale. Instalar pede a senha de administrador (a senha de quem cuida do
computador): é tarefa do professor ou do técnico. É rápido e só precisa ser
feito uma vez por computador. Um pacote que reúne todas as versões, como o
*Visual C++ Runtimes All-in-One*, também resolve.

Isso é do computador, não do ARENA — a pasta continua portátil.

---

### Passo 4c — Conferir se ficou tudo certo

Dois cliques em **`VERIFICAR.bat`**. Ele checa as pastas, os arquivos do
programa, o banco e a porta do servidor, e conserta o que der sozinho.

Vale rodar agora, antes do primeiro uso, e sempre que algo estranho
acontecer. Detalhes no **documento 6**.

---

### Passo 5 — Testar

Dois cliques em **`ARENA.bat`**. A janela preta deve mostrar:

```
  Catalogo: 0 jogo(s)  [varredura, 0.01s]
  CPU:      Intel Core i5-8250U (8 nucleos)
  RAM:      8.0 GB  ->  perfil completo
  Disco:    Disco rapido (SSD ou NVMe) em C:
  Sistema:  Windows 11 Pro (64 bits)
  Video:    motor detectado -> vulkan
  Rede:     fechada (so este computador)
  Endereco: http://127.0.0.1:8777
```

O navegador abre no ARENA. A lista fica vazia — está certo, ainda não há
jogos. Para adicionar, veja o **documento 2** (`2-JOGOS.md`).

O ARENA abre no **navegador padrão** do computador, seja ele o Edge, o
Chrome, o Firefox, o Brave, o Vivaldi ou o Opera: a tela é um site que roda
dentro do seu computador, sem internet, então funciona em qualquer um. Edge,
Chrome, Brave e Vivaldi abrem como um programa, sem abas nem barra de
endereço; Firefox e Opera, numa janela nova. Para escolher outro: **Ajustes
→ Simples → Abrir a tela em** (vale na próxima vez que abrir o ARENA).
No computador fraco, prefira o Edge ou o Chrome: a tela funciona igual nos
três, mas o Firefox gasta umas 2,5 vezes mais memória (os números estão em
`docs\NAVEGADORES.md`).

**Atalho com o ícone do ARENA (Windows):** dois cliques em
**`CRIAR-ATALHO.bat`** põem o atalho `ARENA` na área de trabalho, com o
**supercontrole**, o ícone oficial (veja `docs\ICONE.md`). O atalho guarda o
caminho desta pasta: se você mudar a pasta de lugar, ou se o pen drive ganhar
outra letra, rode o `CRIAR-ATALHO.bat` de novo. A janela do ARENA já mostra o
supercontrole na barra de tarefas.

**Se aparecer `[ERRO] O Python nao foi encontrado`:** volte ao passo 2.

---

### Passo 6 — Copiar para o pen drive ou SSD

A mídia precisa estar em exFAT — veja a **Parte A**, passo 2, deste documento.

1. Formate a mídia em **exFAT**. Aceita arquivo maior que 4 GB e é lida em
   qualquer computador. NTFS funciona, mas cria permissões que atrapalham
   quando o pen drive passa de mão em mão.
2. Copie a pasta `ARENA` inteira para a raiz da mídia.
3. Teste em outro computador.

Deve funcionar sem nenhum ajuste. Se pedir configuração, alguma coisa foi
copiada com caminho fixo — refaça a cópia.

#### Antes de distribuir para a turma

- [ ] `jogos\pessoais` está vazia
- [ ] `retroarch\system` e a pasta `BIOS` só têm as BIOS que você decidiu levar
      (a versão dos alunos do `ferramentas\montar_versao_alunos.py --com-bios`
      já vem com elas)
- [ ] `dados\arena.db` foi apagado (senão os recordes de teste vão junto)
- [ ] `dados\config.json` foi apagado (senão todos os alunos ficam com a
      mesma identificação e os recordes se misturam)
- [ ] a pasta `backup` está vazia
- [ ] `retroarch\states` e `retroarch\saves` estão vazias
- [ ] o `ARENA.bat` abre numa máquina que nunca rodou o ARENA

---

### Onde cada coisa mora

```
ARENA\
├── ARENA.bat               dois cliques aqui
├── VERIFICAR.bat           conferir e consertar (documento 6)
├── LEIA-ME.md              comece por aqui
├── 1-COMECAR.md            este documento
├── 2-JOGOS.md              jogos, pastas e PCSX2
├── 3-IMAGEM-SOM-CONTROLE.md
├── 4-SAVES.md
├── 5-AMIGOS.md
├── 6-RECURSOS-E-REPARO.md
├── launcher\               a tela do ARENA
├── servidor\
│   ├── arena.py            servidor, banco, sincronização
│   ├── indexador.py        procura os jogos nas pastas
│   ├── identificador.py    lê o disco para saber o console
│   ├── hardware.py         mede processador, memória, placa e disco
│   ├── graficos.py         imagem, BIOS, memory card, partida
│   ├── controles.py        mapeamento de teclas e botões
│   ├── cheats.py           save states e códigos
│   ├── diagnostico.py      verificar e consertar
│   └── python\             runtime que viaja junto
├── emuladores\
│   ├── PCSX2\              PlayStation 2 (precisa da BIOS do PS2)
│   ├── Dolphin\            GameCube e Wii
│   ├── RPCS3\              PlayStation 3 (precisa do firmware)
│   └── Xenia\              Xbox 360 (precisa de AVX)
├── retroarch\
│   ├── cores\              emuladores
│   ├── system\             BIOS (documento 2)
│   ├── saves\              saves e memory cards
│   ├── states\             os 10 saves rápidos
│   ├── cheats\             códigos por console
│   ├── remaps\             botões trocados por jogo
│   └── controles\          perfis dos controles
├── jogos\
│   ├── livres\
│   ├── turma\
│   └── pessoais\           uma pasta por console (documento 2)
├── dados\
│   ├── arena.db            recordes
│   ├── config.json         suas configurações
│   └── controles.json      seu mapeamento de controle
└── backup\                 cópias automáticas e pacotes
```

---

### Problemas na instalação

| Sintoma | Causa | Solução |
|---|---|---|
| `[ERRO] O Python nao foi encontrado` | Passo 2 incompleto | Confira `servidor\python\python.exe` |
| `[AVISO] retroarch.exe nao encontrado` | Passo 3 incompleto | A pasta precisa se chamar `retroarch` |
| `A porta 8777 ja esta em uso` | ARENA já aberto | Procure a outra janela preta |
| `[ERRO] Este Windows e de 32 bits` | O Python da pasta é de 64 bits | Não tem conserto nesse computador. Use outro |
| Janela preta abre e fecha na hora | Antivírus bloqueou | Libere a pasta do ARENA no antivírus (veja abaixo) |
| ARENA abre mas nenhum jogo inicia | Falta o Visual C++ | Passo 4b |
| Tudo lento na primeira abertura no pen drive | Varredura inicial | Normal. Depois o catálogo é reaproveitado |
| `[QUEDA] O servidor do ARENA caiu` | O Windows fechou o Python (o programa que roda o ARENA) por causa de uma falha grave | Não precisa fazer nada na hora. A janela preta reabre o servidor sozinha (até 3 vezes), e a tela volta sozinha. Depois, leve o arquivo `dados\logs\queda-do-servidor.txt` para o professor. Esse arquivo mostra em que parte do programa foi a queda |

#### Quando o servidor cai ou trava

O servidor é o programa da janela preta. Duas coisas o derrubavam ou
travavam "sem motivo", e as duas têm proteção desde 02/10/2026:

- **Queda.** Às vezes o Windows fecha o Python por uma falha grave, sem
  mensagem nenhuma. Agora a janela preta percebe, escreve
  `[QUEDA] O servidor do ARENA caiu` e **reabre o servidor sozinha** (até 3
  vezes seguidas). A tela do ARENA mostra "parou de responder" por uns
  segundos e **volta sozinha**, sem fechar nada. O motivo da queda fica
  anotado em `dados\logs\queda-do-servidor.txt`: é o arquivo que conta em
  que parte do programa foi.
- **Clique na janela preta.** No Windows 10, clicar dentro da janela preta
  começa uma seleção de texto (a "Edição Rápida") e o programa **para** até
  alguém apertar uma tecla. O ARENA desliga isso na janela dele. Se mesmo
  assim aparecer "Selecionar" no título da janela, aperte **Esc**.

#### "O Windows protegeu o seu computador" (SmartScreen)

Isso costuma aparecer na **primeira vez** que você abre um `.bat` ou
`.exe` que veio de um arquivo `.zip` baixado da internet (o Windows marca
o arquivo como "de fora", mesmo sendo o próprio ARENA). É diferente de
antivírus — é uma tela azul do próprio Windows, não do programa de
segurança.

1. Na tela azul, clique em **"Mais informações"** (não no X).
2. Vai aparecer o botão **"Executar assim mesmo"** — clique nele.
3. Isso só acontece uma vez por arquivo. Nas próximas aberturas, não
   aparece mais.

**Para não aparecer em nenhum:** desbloqueie o `.zip` **antes** de
descompactar (botão direito no `.zip` → **Propriedades** → **Desbloquear**
→ **OK**). Já descompactou? Apague a pasta, desbloqueie o `.zip` e
descompacte de novo. Não precisa de senha de administrador.

#### Antivírus bloqueando (janela preta abre e fecha na hora)

Cada antivírus tem os seus próprios menus. Mas a ideia é sempre a mesma:
dizer ao antivírus que a pasta inteira do ARENA é confiável. É como pôr um
nome na lista de convidados da portaria: a pessoa entra sem ser barrada.
Você nunca precisa desligar o antivírus inteiro. Faça assim:

1. Abra o programa antivírus instalado no computador.
2. Procure por **"Exclusões"**, **"Exceções"** ou **"Itens confiáveis"**
   (o nome muda de antivírus para antivírus).
3. Adicione a **pasta inteira** do ARENA (não só o `.bat`). Escolher a
   pasta errada é o erro mais comum aqui.

No **Segurança do Windows** (o antivírus que já vem com o Windows, sem
instalar nada a mais):

1. Iniciar → **Segurança do Windows**.
2. **Proteção contra vírus e ameaças → Gerenciar configurações**
   (role a tela até achar).
3. Em **Exclusões**, clique em **Adicionar ou remover exclusões**.
4. **Adicionar uma exclusão → Pasta** → escolha a pasta do ARENA.

Atenção: o Windows pede a senha de administrador nos passos 2 e 3. Aluno
não tem essa senha — é um passo para o professor ou para o técnico.

Tentou e o ARENA continua fechando sozinho? Peça para o professor fazer esse
passo. Ele precisa ter acesso de administrador (a conta de quem cuida do
computador). Em computador de escola, às vezes o antivírus é controlado à
distância, pela equipe de informática. Aí um aluno comum não consegue mexer
nele.

---

## Parte C — No Chromebook

O mesmo pen drive abre no Chromebook, dentro do próprio Chrome, sem
instalar nada. A tela é a mesma do Windows.

1. No Chromebook, abra o **Arquivos**, o pen drive, a pasta do ARENA, e
   clique em **ARENA-CHROMEBOOK.html**.
2. Escolha o apelido. Os jogos livres que vêm com o ARENA já estão na lista.
3. Para os **seus** jogos, clique em **Escolher a pasta do ARENA** (no alto
   da lista) e escolha a pasta do ARENA no pen drive. É uma vez só: nos
   outros dias, o Chrome pergunta se pode e você clica em **Permitir**.
4. Jogue como no Windows: **Esc** abre o menu, **F2** salva, **F4** carrega,
   **F10** fecha. O botão **Voltar ao ARENA** aparece no alto quando você
   mexe o mouse. Em tela cheia, para sair dela, segure o **Esc**.

O save fica no pen drive, no mesmo lugar do Windows (`retroarch\saves`): o
jogo salvo no Chromebook continua salvo no Windows, e o contrário também.

O que muda no Chromebook: rodam **35 dos 66 consoles** (NES, Super
Nintendo, Game Boy, GBA, Mega Drive, PlayStation, Neo Geo e outros). Os
outros aparecem com o aviso "só roda no ARENA do Windows". Não há jogo em
rede nem os emuladores de fora (PS2, GameCube, Wii, PS3, Xbox 360).

**Chromebook sem pen drive:** em **Ajustes → Máquina → Guardar um jogo
neste navegador**, escolha o arquivo do jogo (um jogo pequeno, de
cartucho). Ele fica guardado no Chrome, nesta conta.

**Para o professor:** em **Ajustes → Máquina → Testar este Chromebook**, o
ARENA abre um jogo de cada console, mede quantos quadros por segundo o
Chromebook consegue e monta um relatório para baixar. Os detalhes, os
números e o que fazer se a escola bloquear algo estão em
`docs\CHROMEBOOK.md`.

---

## Parte D — No Linux

O mesmo pen drive abre no Linux (Ubuntu, Mint, Debian, Fedora e outros, de
2018 para cá, 64 bits), sem instalar nada e sem senha de administrador. É o
mesmo ARENA: a mesma tela, os mesmos 66 consoles, o mesmo save do Windows.

1. No Linux, abra a pasta do ARENA no gerenciador de arquivos, clique com o
   botão direito num espaço vazio e escolha **Abrir no terminal**.
2. Digite `sh ARENA.sh` e aperte Enter. A tela abre no navegador do
   computador, como no Windows. Na primeira vez, o ARENA prepara o RetroArch
   (uns segundos); nas outras, abre direto.
3. Não feche a janela do terminal enquanto joga: ela é a "janela preta" do
   Linux. Para fechar o ARENA, feche a janela ou aperte **Ctrl+C** nela.

Para abrir com dois cliques nas outras vezes: `sh ARENA.sh --atalho` põe o
ARENA no menu de aplicativos deste computador. Nos gerenciadores de arquivos
que deixam (o do KDE, o do Mint), o `ARENA.desktop` da pasta também abre.

O que muda no Linux: o som vai pelo PulseAudio (ou pelo ALSA) e o controle
pelo udev, o jeito do Linux; o Lossless Scaling (programa do Windows) não
aparece. O resto é igual, inclusive o PS2, o PS3 e o Xbox 360, com os
emuladores do Linux usando a mesma pasta de dados dos do Windows. Para
conferir a pasta, `sh VERIFICAR.sh`. Os detalhes estão em `docs\LINUX.md`.

---

## Parte E — No celular ou no tablet Android

O mesmo ARENA, num app: a mesma tela, o mesmo Jogar Junto, os mesmos jogos e
saves do Windows. Precisa do Android 7 ou mais novo.

1. **Baixar.** Na página de *Releases* do ARENA no GitHub, baixe o
   `ARENA-...-arm64-v8a.apk` (quase todo celular e tablet). O `x86_64` é só
   para Chromebook com processador Intel e para o emulador de testes.
2. **Instalar.** Abra o arquivo baixado. O Android pergunta se deixa o
   navegador (ou o Arquivos) instalar apps de fora da loja: permita. O ARENA
   não vem da Play Store; o APK é assinado pelo ARENA, e a versão seguinte
   instala por cima, sem perder nada.
3. **Abrir.** Na primeira vez, o ARENA pede para ver os arquivos do
   aparelho (permita: é para achar a pasta do ARENA) e leva uns segundos se
   preparando. Sem pasta do ARENA no aparelho, ele abre com 8 jogos livres
   que vêm junto.
4. **Os seus jogos.** Copie a pasta do ARENA do pen drive para a memória do
   aparelho ou para o cartão (ou ligue o pen drive pelo cabo OTG). Em
   **Ajustes → A pasta do ARENA neste aparelho**, escolha a pasta; se houver
   uma só, o ARENA já usa ela na primeira abertura. Os jogos, as BIOS e os
   saves são os do computador.
   - Alguns Android só deixam ler no cartão: o ARENA avisa, os jogos abrem
     de lá e os saves ficam no aparelho. O botão **Deixar gravar no
     cartão** abre a tela do Android que libera.
   - **Memória cheia?** Deixe os jogos no cartão de memória e, em **Ajustes →
     Máquina → Onde ficam os jogos**, clique em **Procurar jogos no cartão** e
     em **Jogar desta pasta**. O ARENA joga ao mesmo tempo o que está na
     memória do aparelho e o que está no cartão, só lê (não copia nem apaga
     nada) e, se você tirar o cartão, os jogos dele somem da lista até você
     encaixá-lo de novo.
5. **Jogar.** Sem controle, o jogo mostra um controle desenhado na tela;
   com um controle ligado (pelo cabo OTG ou por Bluetooth), ele some. Para
   sair do jogo, o botão **voltar** do aparelho abre o menu do RetroArch:
   escolha **Sair do RetroArch**. Num teclado, o **F10** duas vezes.
6. **Jogar Junto.** Como no computador: os dois aparelhos na mesma rede
   Wi-Fi, com **Aceitar conexões** ligado em quem hospeda.

O que muda no Android:

- Os **recordes e o apelido ficam no aparelho**: a pasta do ARENA no
  cartão ou na memória é aberta a outros apps, e esses são dados de aluno.
  Para levar os recordes a outro ARENA, use a sincronização (Amigos).
- Os filtros de tela do ARENA só valem com o motor **Vulkan** (Ajustes →
  Avançado → Motor gráfico); no padrão do Android (o `gl`), o jogo sai sem
  filtro.
- Não há o Java ME, o PS3 nem o Xbox 360 (não têm versão para Android); o
  PS2, o GameCube e o Wii vão pelos núcleos do RetroArch, em aparelho bom.
- Enquanto o ARENA está aberto, o Android mostra "ARENA aberto" na barra:
  é o que deixa o ARENA aberto durante o jogo. Para fechar de vez, tire o
  ARENA da tela dos apps abertos.

Os detalhes estão em `docs/ANDROID.md`.
