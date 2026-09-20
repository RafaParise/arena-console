# 1 — Começar do zero

Preparar a mídia e montar o ARENA. Faça uma vez; depois é copiar e colar.

**Neste documento:**

- Parte A — Preparar o pen drive ou o SSD
- Parte B — Instalação

---

## Parte A — Preparar o pen drive ou o SSD

Faça isto antes de instalar o ARENA. Cinco minutos.

Se você vai usar o ARENA só no disco `C:` do computador, **pule para o
deste documento**. Nada aqui é obrigatório.

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

Continue no **deste documento — Instalação**.

---

### Passo 5 — Retirar com segurança

**Feche o ARENA antes de puxar o pen drive.**

A janela preta escreve *"Pode retirar o pen drive com segurança"* quando
terminou de gravar. Só desconecte depois disso.

Se puxar antes, o arquivo de recordes pode estragar. O ARENA guarda cópia
automática em `backup`, então dá para recuperar — mas é chato e evitável.

---

### Passo 6 — O cartão SD

Cartão SD tem escrita aleatória lenta e desgaste rápido. O banco de recordes
grava o tempo todo; num cartão, ele degrada e mais cedo ou mais tarde
corrompe no meio da aula.

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

**Tempo:** 20 minutos.

---

### Passo 1 — Criar a pasta

Crie `C:\ARENA` e copie tudo deste pacote para dentro.

Monte primeiro no disco `C:`. É mais rápido para montar e testar. Só depois
copie para o pen drive ou o SSD.

Se você já preparou a mídia pelo **neste mesmo documento**, pode montar direto nela.

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

Se faltar: baixe o **Microsoft Visual C++ Redistributable (x64)** no site da
Microsoft e instale. É rápido e só precisa ser feito uma vez por computador.
Um pacote que reúne todas as versões, como o *Visual C++ Runtimes All-in-One*,
também resolve.

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
jogos. Para adicionar, veja o **neste mesmo documento**.

**Se aparecer `[ERRO] O Python nao foi encontrado`:** volte ao passo 2.

---

### Passo 6 — Copiar para o pen drive ou SSD

A mídia precisa estar em exFAT — veja o **neste mesmo documento**.

1. Formate a mídia em **exFAT**. Aceita arquivo maior que 4 GB e é lida em
   qualquer computador. NTFS funciona, mas cria permissões que atrapalham
   quando o pen drive passa de mão em mão.
2. Copie a pasta `ARENA` inteira para a raiz da mídia.
3. Teste em outro computador.

Deve funcionar sem nenhum ajuste. Se pedir configuração, alguma coisa foi
copiada com caminho fixo — refaça a cópia.

#### Antes de distribuir para a turma

- [ ] `jogos\pessoais` está vazia
- [ ] `retroarch\system` está vazia
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
│   ├── PCSX2\              PlayStation 2 (obrigatório)
│   └── Dolphin\            GameCube e Wii (opcional)
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
| Janela preta abre e fecha na hora | Antivírus bloqueou | Libere a pasta do ARENA no antivírus |
| ARENA abre mas nenhum jogo inicia | Falta o Visual C++ | Passo 4b |
| Tudo lento na primeira abertura no pen drive | Varredura inicial | Normal. Depois o catálogo é reaproveitado |


---
