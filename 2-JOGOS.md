# 2 — Jogos, pastas e emuladores

Onde colocar cada jogo, como liberar console amarelo e quais programas precisam ser baixados à parte.

**Neste documento:**

- Parte A — Colocar seus jogos
- Parte B — Consoles que pedem programa próprio

---

## Parte A — Colocar seus jogos

Como adicionar jogos e como liberar os consoles que ficam amarelos.

---

### Parte A — Adicionar jogos

#### Passo 1 — Escolha a pasta

| Pasta | Para quê |
|---|---|
| `jogos\pessoais` | Os seus. Ficam só no seu pen drive |
| `jogos\turma` | Jogos feitos pela turma no TIC-80 (`.tic`) |
| `jogos\livres` | Acervo que pode ser distribuído. Já vem no pacote |

#### Passo 2 — Copie os arquivos

Arraste para dentro da pasta. Pode criar subpastas para se organizar — o
ARENA entra nelas.

#### Passo 3 — Atualize a lista

No ARENA, clique em **Atualizar lista**, no canto inferior esquerdo.

Pronto. O ARENA olha o final do nome do arquivo e descobre sozinho de qual
console ele é.

---

### Como o ARENA reconhece cada console

| Final do arquivo | Console |
|---|---|
| `.nes` `.fds` `.unf` | Nintendo (NES) |
| `.sfc` `.smc` `.swc` `.fig` | Super Nintendo |
| `.gb` `.gbc` | Game Boy e Game Boy Color |
| `.gba` | Game Boy Advance |
| `.vb` | Virtual Boy |
| `.min` | Pokémon mini |
| `.mgw` | Game & Watch |
| `.n64` `.z64` `.v64` | Nintendo 64 |
| `.nds` | Nintendo DS |
| `.rvz` `.gcm` `.gcz` `.wbfs` | GameCube e Wii |
| `.sg` | Sega SG-1000 |
| `.md` `.gen` `.smd` `.sms` `.gg` | Mega Drive, Master System e Game Gear |
| `.32x` | Sega 32X |
| `.gdi` `.cdi` | Sega Dreamcast |
| `.pbp` `.m3u` | PlayStation |
| `.cso` | PlayStation Portable |
| `.a26` | Atari 2600 |
| `.a52` | Atari 5200 |
| `.a78` | Atari 7800 |
| `.lnx` | Atari Lynx |
| `.j64` `.jag` | Atari Jaguar |
| `.col` | ColecoVision |
| `.int` | Intellivision |
| `.vec` | Vectrex |
| `.pce` `.sgx` | PC Engine |
| `.ngp` `.ngc` | Neo Geo Pocket |
| `.ws` `.wsc` | WonderSwan |
| `.d64` `.t64` `.prg` `.crt` | Commodore 64 |
| `.adf` `.hdf` `.ipf` | Commodore Amiga |
| `.tzx` `.tap` `.z80` `.szx` | ZX Spectrum |
| `.cdt` `.sna` | Amstrad CPC |
| `.rom` `.cas` | MSX |
| `.exe` `.com` `.bat` `.conf` | MS-DOS |
| `.scummvm` `.svm` | ScummVM |
| `.tic` | TIC-80 |
| `.wasm` | WASM-4 |
| `.nx` | LowRes NX |
| `.uze` | Uzebox |

#### Quando o final serve a mais de um console

`.iso`, `.cue`, `.chd`, `.bin`, `.zip` e `.dsk` servem a vários consoles.
Nesses casos **quem decide é a pasta**, igual ao RetroArch.

O ARENA não tenta adivinhar. Já tentou, e errava: o **Half-Life de
PlayStation 2 foi lançado em CD**, com a mesma estrutura de um jogo de
PlayStation 1. Nenhuma pista de tamanho ou de cabeçalho separa os dois.
Chutar só fazia o jogo abrir no emulador errado.

#### Passo 1 — Criar as pastas

No ARENA, clique em **Criar pastas dos consoles**, embaixo da lista à
esquerda.

Ele cria as 47 pastas dentro de `jogos\pessoais`:

```
ARENA\jogos\pessoais\PS1\
ARENA\jogos\pessoais\PS2\
ARENA\jogos\pessoais\PSP\
ARENA\jogos\pessoais\Nintendo 64\
ARENA\jogos\pessoais\Sega Saturn\
...
```

#### Passo 2 — Jogar os arquivos dentro

Arraste cada jogo para a pasta do console dele. Depois clique em
**Atualizar lista**.

Pronto. Não tem mais como errar.

#### Se você já tem jogos soltos

Eles aparecem no topo da lista, num grupo chamado **Precisa escolher o
console**. Duas formas de resolver:

**Arrastando:** pegue a linha do jogo e solte em cima do console certo, na
lista da esquerda. O ARENA **move o arquivo de verdade** para a pasta.

**Pela gaveta:** clique em *Saves e cheats* e escolha em **Console deste
jogo**. Mesma coisa, também move o arquivo.

Nos dois casos o ARENA já deixa marcada a opção mais provável — na maioria
das vezes é só confirmar.

#### As pastas que o ARENA reconhece

Você pode usar o nome que ele criou, ou qualquer apelido comum:

| Console | Pasta criada | Também aceita |
|---|---|---|
| PlayStation | `PS1` | `psx`, `playstation` |
| PlayStation 2 | `PS2` | `playstation 2` |
| PlayStation Portable | `PSP` | `playstation portable` |
| Nintendo 64 | `Nintendo 64` | `n64` |
| Sega CD | `Sega CD` | `mega cd`, `scd` |
| GameCube e Wii | `GameCube` | `wii`, `ngc` |

Funciona em qualquer nível: `Sony\PlayStation 2\Corrida` também é
reconhecido.

**A pasta vale acima de tudo.** Se você põe um arquivo na pasta `PS2`, ele
é PlayStation 2 — mesmo que a extensão dele normalmente pertença a outro
console.

---

### Nomes de arquivo

O ARENA limpa o nome sozinho para mostrar na tela:

```
super_jogo_(Brazil)_[!].sfc   →   Super Jogo
```

Ele tira o que está entre parênteses e colchetes, troca `_`, `.` e `-` por
espaço e coloca as iniciais em maiúscula. Você não precisa renomear nada.

A busca ignora acento: digitar `pokemon` acha `Pokémon`.

**Não renomeie o arquivo depois de começar a jogar.** Os saves seguem o nome
do arquivo — trocou o nome, perdeu o save. Escolha o nome antes.

---

### Parte B — Consoles amarelos

#### O que é

Alguns consoles não funcionam só com o emulador. Eles precisam dos arquivos
que vinham gravados de fábrica dentro do aparelho.

**O ARENA não fornece esses arquivos, não diz quais são e não baixa nada.**
Eles pertencem às empresas que fabricaram os consoles. Se você tem o
aparelho original, existem procedimentos para extrair da sua própria
máquina.

#### Quais consoles pedem

| Console | Quantos arquivos |
|---|---|
| 3DO | 1 |
| Arcade (MAME) | 1 |
| Atari 5200 | 1 |
| Atari Lynx | 1 |
| ColecoVision | 1 |
| Commodore Amiga | 1 |
| Intellivision | 1 |
| Magnavox Odyssey 2 | 1 |
| MSX | 1 |
| Neo Geo | 1 |
| PC-FX | 1 |
| Philips CD-i | 1 |
| PlayStation | 1 |
| PlayStation 2 | 1 |
| Sega 32X | 1 |
| **Sega CD** | **3** |
| Sega Dreamcast | 1 |
| Sega Saturn | 1 |

#### Os 29 que não pedem nada

Amstrad CPC · Atari 2600 · Atari 7800 · Atari Jaguar · Commodore 64 ·
Game & Watch · Game Boy e Game Boy Color · Game Boy Advance · GameCube e
Wii · LowRes NX · Mega Drive, Master System e Game Gear · MS-DOS ·
Neo Geo Pocket · Nintendo (NES) · Nintendo 64 · Nintendo DS · PC Engine ·
PlayStation Portable · Pokémon mini · ScummVM · Sega SG-1000 ·
Super Nintendo · TIC-80 · Uzebox · Vectrex · Virtual Boy · WASM-4 ·
WonderSwan · ZX Spectrum

#### Passo a passo

**1.** Veja a bolinha da plataforma, do lado esquerdo:

| Cor | Quer dizer |
|---|---|
| Azul | Pronto, é só clicar |
| Amarelo | Falta arquivo de sistema |
| Cinza | Falta baixar o emulador desse console |

**2.** Se estiver amarela, a linha mostra **quantos** arquivos faltam.

**3.** Coloque os arquivos em:

```
ARENA\retroarch\system\
```

Direto nessa pasta. Sem criar subpasta, sem renomear.

**4.** Feche e abra o ARENA. A bolinha vira azul sozinha.

---

### Parte C — Consoles cinzas

Falta o emulador daquele console. Resolve em um minuto:

1. Abra o `retroarch.exe` direto, fora do ARENA.
2. **Carregar Núcleo → Baixar um Núcleo**.
3. Escolha o que falta na lista.
4. Feche o RetroArch e abra o ARENA.

A bolinha vira azul.

---

### As etiquetas dos jogos

Cada jogo tem uma etiqueta dizendo como vai rodar **no seu computador**:

| Etiqueta | O que esperar |
|---|---|
| **Bonito e lisinho** | Seu PC sobra. Roda com a melhor imagem |
| **Feio mas lisinho** | Roda liso, sem os enfeites |
| **Capenga** | Vai travar |

**Capenga não impede de jogar.** O ARENA só avisa antes, para você não achar
que quebrou. Se quiser tentar, tente — o botão funciona igual.

Detalhes de como o ARENA decide isso: **documento 6**.

---

### Problemas

| O que aconteceu | O que fazer |
|---|---|
| Coloquei o jogo e ele não aparece | Clique em **Atualizar lista**. Confira o final do arquivo na tabela acima |
| Apareceu no console errado | Ponha numa subpasta com o nome do console, ou crie o `_console.txt` (acima) |
| **Muitos jogos** no console errado | Quase sempre são `.iso` ou `.chd` soltos. Ponha cada grupo na sua pasta |
| Bolinha continua amarela | O arquivo tem que estar direto em `retroarch\system`, sem subpasta. Feche e abra o ARENA |
| Bolinha cinza | Baixe o núcleo pelo RetroArch (Parte C) |
| O jogo abre e fecha na hora | Falta arquivo de sistema, ou o motor gráfico não existe nessa máquina (documento 3) |
| O nome ficou estranho na lista | Renomeie o arquivo. O ARENA usa o nome do arquivo como título |
| A lista está lenta com muitos jogos | Só na primeira abertura. Depois o ARENA reaproveita e fica rápido |

---

### Regra da turma

**Não passe jogo comercial para os colegas.** A pasta `jogos\pessoais` é sua
e fica no seu pen drive. Não copie para o colega, não distribua pelo
servidor da sala.


---

## Parte B — Consoles que pedem programa próprio

O PlayStation 2 não abre pelo RetroArch. Isso não é defeito do ARENA nem do
seu computador.

---

### O que está acontecendo

O RetroArch roda cada console através de um "núcleo". A maioria é excelente.
O núcleo de PlayStation 2 é a exceção: é pouco mantido, exige a BIOS numa
pasta específica e, quando algo não bate, **fecha sem dizer nada**.

É exatamente o sintoma: você clica, aparece "Abrindo...", e nada acontece.

A solução é usar o **PCSX2 de verdade** — o programa que a própria equipe do
PlayStation 2 mantém. O ARENA passa a chamar ele sozinho.

---

### Passo a passo

#### 1. Baixe o emulador

**Só dois.** O RetroArch dá conta de todo o resto, inclusive PlayStation 1
(o núcleo dele *é* o DuckStation) e PSP.

| Console | Programa | Precisa? | Onde |
|---|---|---|---|
| **PlayStation 2** | PCSX2 | **Sim, obrigatório** | `pcsx2.net/downloads` |
| GameCube e Wii | Dolphin | Opcional | `dolphin-emu.org/download` |

**Pegue sempre a versão portátil** (`.7z` ou `.zip`), nunca o instalador.
Assim continua tudo dentro da pasta do ARENA, sem instalar nada no Windows
e sem senha de administrador.

No PCSX2, o arquivo certo é o **Windows 64-bit AVX2 — Portable**.

#### 2. Descompacte na pasta que já existe

O ARENA já criou as pastas, cada uma com um `LEIA.txt` dizendo o que baixar:

```
ARENA\emuladores\PCSX2\
ARENA\emuladores\Dolphin\
```

Descompacte dentro. Tem que ficar assim:

```
ARENA\emuladores\PCSX2\pcsx2-qt.exe
ARENA\emuladores\Dolphin\Dolphin.exe
```

Se o programa vier dentro de uma subpasta com o número da versão, tudo bem —
o ARENA procura um nível abaixo também.

#### 3. Feche e abra o ARENA

Pronto. Em **Ajustes → Emuladores** você vê a lista, com "em uso" ao lado de
cada um que ele encontrou.

Ao abrir um jogo, o aviso diz por qual programa: *"Abrindo Black pelo PCSX2"*.

---

### A BIOS

#### Pelos emuladores de fora

O PCSX2 e o Dolphin pedem a BIOS pela tela deles mesmos, na primeira vez que
abrem. Siga o que o programa pedir.

#### Abrir só a BIOS, sem jogo nenhum

Em **Ajustes → Emuladores**, escolha o console e clique em **Abrir só a
BIOS**.

O console abre na tela inicial — aquela onde você acerta a data e a hora,
mexe nos ajustes e vê os saves do memory card com os iconezinhos.

Tudo o que você mudar ali **fica salvo**, porque o ARENA usa sempre o mesmo
arquivo de BIOS e a mesma pasta. Vale para jogos que mudam conforme o
horário, e vale para apagar ou copiar save de um cartão.

Funciona pelo RetroArch e pelo PCSX2 — o ARENA usa o que estiver instalado
para aquele console.

#### Pelo RetroArch: escolher qual usar

Em **Ajustes → Emuladores** tem a lista **Qual BIOS usar em cada console**.

Aparecem ali os arquivos que você já colocou em `retroarch\system`. O ARENA
não fornece, não indica onde conseguir e não baixa nada.

**Por que fixar uma:** o console guarda a data, a hora e as preferências
*dentro* da BIOS. Se cada jogo abrir com um arquivo diferente, o relógio
volta para 1 de janeiro toda vez e a tela inicial parece vazia.

Fixando uma, você abre a tela do PlayStation, vê a data certa e os
**ícones do memory card** — do jeito que era no aparelho de verdade.

---

### Memory card

Um cartão por console, guardado em:

```
ARENA\retroarch\saves\memcards\
```

É o **mesmo cartão em todos os jogos daquele console**. Por isso os saves
aparecem juntos na tela inicial, com os iconezinhos, e dá para copiar de um
jogo para outro como no aparelho original.

O ARENA cria a pasta sozinho na primeira vez. Vale para PlayStation 1 e 2;
os outros consoles gravam do jeito deles, cada jogo no seu arquivo.

#### Ver os cartões

Na mesma aba, embaixo, o ARENA lista os cartões que existem — como uma
caixinha de memory cards em cima da TV:

```
ps1-1.mcd    4 de 15 blocos usados · último uso em 07/09/2026 22:14   [11 livres]
```

Para o cartão de PlayStation 1 ele conta os blocos de verdade, lendo o
índice do cartão — o mesmo número que o console mostrava na tela de memory
card.

O cartão entra no pacote de progresso (documento 4), então você leva os
saves para outro computador junto com o resto.

---

### Data e hora do console

Alguns jogos mudam conforme o horário. O emulador usa **o relógio deste
computador**: se a data do Windows está certa, a do console também está.

Em **Ajustes → Emuladores** você vê a hora atual e onde a BIOS guarda os
ajustes.

Os ajustes que você faz na tela do console — idioma, formato da data, som —
ficam gravados junto da BIOS, em `retroarch\system`. Como o ARENA usa
sempre o mesmo arquivo e a mesma pasta, eles continuam valendo amanhã, e
viajam junto quando você copia a pasta do ARENA.

---

### O que muda quando o emulador de fora assume

| Recurso | Pelo RetroArch | Pelo emulador de fora |
|---|---|---|
| Abrir o jogo pelo ARENA | Sim | **Sim** |
| Contar tempo de jogo | Sim | **Sim** |
| Registrar pontuação | Sim | **Sim** |
| Bolinha e etiqueta na lista | Sim | **Sim** |
| Ajuste de imagem do ARENA | Sim | Não. Configure pelo programa |
| Os 10 save states do ARENA | Sim | Não. Ele tem os dele |
| Cheats pelo ARENA | Sim | Não. Ele tem os dele |
| Jogar junto e assistir | Sim | Não. Ele tem rede própria |
| Esc abre o menu | Sim | Cada programa tem a tecla dele |

O ARENA avisa se você tentar *Jogar junto* num console que está usando
emulador de fora.

---

### Como o ARENA decide

Para cada console, na ordem:

1. **Tem emulador de fora na pasta?** Usa ele. Nem olha o RetroArch.
2. **Tem o núcleo do RetroArch?** Usa o núcleo.
3. **Nenhum dos dois?** A bolinha fica cinza e a lista diz o que instalar.

Você não escolhe nada. Se quiser voltar ao RetroArch, é só tirar a pasta do
emulador de dentro de `emuladores`.

---

### Vale a pena para os opcionais?

**PlayStation 2 e GameCube: sim, é obrigatório.** Os núcleos não dão conta.

**PlayStation, PSP e Dreamcast: provavelmente não.** Os núcleos do RetroArch
já rodam muito bem, e pelo RetroArch você mantém os 10 save states, os
cheats e o jogar junto. Só instale o programa de fora se você quiser alguma
opção específica que só ele tem.

---

### Problemas

| O que aconteceu | O que fazer |
|---|---|
| Coloquei o programa e continua no RetroArch | Feche e abra o ARENA. Confira o nome do arquivo na tabela acima |
| Em Ajustes → Emuladores diz "não instalado" | O executável tem outro nome, ou está fundo demais. Deixe no máximo uma subpasta |
| Abre o emulador mas não carrega o jogo | Quase sempre é BIOS. Abra o emulador direto e siga o que ele pedir |
| Quero voltar ao RetroArch | Tire a pasta de dentro de `emuladores` e reabra o ARENA |
| "Jogar junto só funciona pelo RetroArch" | É esperado. Use a rede do próprio emulador, ou tire a pasta dele |


---
