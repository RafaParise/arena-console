# 6 — Todos os recursos e o que fazer quando quebra

A explicação de cada opção da aba Avançado e o verificador embutido.

**Neste documento:**

- Parte A — Todos os recursos, explicados
- Parte B — Quando alguma coisa der errado

---

## Parte A — Todos os recursos, explicados

O RetroArch tem centenas de opções. O ARENA mostra as **50 que valem a
pena**, com explicação em português e exemplo quando o assunto é técnico.

Estão em **Ajustes → Avançado**, separadas por grupo.

---

### Como ler a tela

Cada recurso tem três partes:

- **O nome**, em português.
- **A explicação**, uma linha dizendo o que faz.
- **"por exemplo…"**, um botão que abre um caso concreto. Só aparece quando
  a explicação sozinha não basta.

E alguns têm um selo:

| Selo | Quer dizer |
|---|---|
| **pesa pouco** | Custa um pouquinho de processador |
| **pesa** | Custa bastante. Ligue só se o PC aguentar |

**Recurso que sua máquina não aguenta nem aparece.** Se você tem um PC nota
2, o ARENA esconde as opções que só fazem sentido em nota 4. Menos coisa na
tela, menos chance de estragar o que está funcionando.

---

### Grupo 1 — Resposta do controle

O tempo entre você apertar o botão e a coisa acontecer.

#### Resposta instantânea

O recurso mais impressionante do RetroArch, e o mais mal explicado por aí.

Todo console de verdade tem um atraso: você aperta, ele processa, a TV
desenha. Dá uns 2 ou 3 quadros — perto de 50 milissegundos.

A resposta instantânea faz o emulador rodar esses quadros **escondido** e
mostrar o resultado já pronto. Na prática: **o soco sai mais rápido do que
saía no aparelho original**.

Custa caro: medido com o jogo aberto, de **4 a 12 vezes** o processador que
o emulador gastaria sem ela (no PS1, de 8,7% para 35,8% de um núcleo; no ZX
Spectrum, de 4,7% para 55%). Por isso o ARENA **não liga sozinho** em perfil
nenhum: só você, aqui, e a opção nem aparece em máquina abaixo da nota 4.
(Até a auditoria 3, o nível **Qualidade** ligava sozinho — e o notebook da
escola tira nota 4, igual a um PC forte.)

#### Quando ler o controle

Deixe no **2**. É o que faz o emulador perguntar ao controle no último
instante antes de desenhar o quadro.

No 0 ele pergunta cedo demais, e metade do que você apertou chega tarde.

#### Fila de imagens

Quantas imagens ficam prontas esperando a vez.

- **2** — a imagem chega mais rápido na tela
- **3** — trava menos em PC fraco

Vale só em Vulkan e D3D11. Em OpenGL quem faz esse papel é a *Sincronia
rígida*.

#### Esperar antes de desenhar

O emulador segura o quanto pode antes de desenhar, para pegar seu comando o
mais tarde possível. Ligado no automático, ele mede sozinho quanto dá para
esperar. **Deixe ligado.**

---

### Grupo 2 — Imagem

#### Motor gráfico

Por onde o jogo fala com a placa de vídeo.

| Opção | Quando |
|---|---|
| **automático** | Deixe assim. O ARENA testa e escolhe |
| **vulkan** | O caminho mais curto. Placa antiga não tem |
| **d3d11** | Ótimo no Windows quando não há Vulkan |
| **glcore** | Rede de segurança, funciona em quase tudo |

#### Filtro de tela

O mais perto de um ReShade que existe aqui — e feito para emulador, então
bem mais leve. Ligado, os consoles 2D ganham o **pixel nítido**: todo
pixel do mesmo tamanho, sem borrão, em qualquer tela (até 4K). Consoles 3D
ficam sem filtro.

Usa o pacote de shaders que já vem em `retroarch\shaders\shaders_slang`.
Sem ele, o ARENA desliga o filtro sozinho e o jogo abre normal.

#### Escala inteira

Sem isso, ao esticar a imagem uns pixels ficam com 3 pontos de largura e
outros com 4 — e a imagem parece torta. Com isso, sobra tarja preta mas
cada quadradinho fica perfeito.

#### Reduzir borrão de movimento

Pisca um quadro preto entre os quadros do jogo. Deixa o movimento nítido do
jeito que era na TV de tubo.

Escurece a tela e **só vale em monitor de 120 Hz para cima**. Em monitor
comum, só pisca.

#### A cada quantos quadros do monitor

Se seu monitor é de 120 Hz e o jogo é de 60, use **2** para casar
direitinho.

---

### Grupo 3 — Som

#### Som só para o jogo

O jogo toma a placa de som para ele. Fica mais rápido e mais limpo, mas
**nada mais toca enquanto você joga** — nem música, nem vídeo, nem chamada.

#### Atraso do som

O número é em milissegundos.

| Situação | Valor |
|---|---|
| Som falhando ou estalando | 96 ou 128 |
| Normal | 64 |
| Quer resposta rápida e o PC aguenta | 32 |
| Só com som exclusivo e PC bom | 16 |

Se baixar demais, começa a estalar. É o sinal de que passou do ponto.

#### Casar som com imagem

Segura a velocidade do jogo para o som não ficar acelerado. **Deixe
ligado.** Desligado, o jogo pode rodar mais rápido que a música.

---

### Grupo 4 — Controle

#### Folga do analógico

Quanto o analógico precisa sair do centro para o jogo perceber.

**Se o personagem anda sozinho com o controle parado**, o analógico está
gasto. Suba para 0.2.

#### Sensibilidade do analógico

Multiplica o quanto você inclinou. Suba se o analógico não chega ao máximo.
Passar de 1.5 costuma deixar o movimento nervoso.

#### Abrir menu pelo controle

Sem teclado por perto? Deixe no **2** e aperte **Start + Select juntos**.

---

### Grupo 5 — Enquanto joga

#### Voltar no tempo

Segure a tecla e o jogo volta como um vídeo de trás para frente.

Caiu no buraco? Segura e volta dois segundos antes do pulo.

Come memória o tempo todo em que está ligado, mesmo sem você usar. Em
*Quanto dá para voltar* você define quantos megabytes reservar — 20 MB dão
uns 10 segundos em jogo 16 bits, bem menos em jogo 3D.

Em console 3D ele pesa muito: no Nintendo 64, o jogo caiu de 60 para 30
quadros por segundo, num PC forte. O ARENA **não liga sozinho** (até a
auditoria 3, o nível Qualidade ligava). Ligue aqui só em jogo 2D, se quiser.

#### Avanço rápido

Quantas vezes mais rápido quando você segura o avanço.

**0.0 = sem limite**, vai o quanto o PC aguentar. Use **4.0** para pular
diálogo sem perder o áudio inteiro.

#### Câmera lenta

Serve para passar aquele trecho impossível, ou para ver de onde veio o
golpe.

#### Salvar ao sair

Grava sozinho quando você fecha o jogo. Bom no PC.

**No pen drive, deixe desligado**: cada saída vira uma gravação grande, e o
pen drive tem número limitado de gravações.

#### Foto no save

Guarda uma imagem junto de cada save, para você reconhecer qual é qual.
Útil com 10 saves. Cada foto são alguns KB.

---

### Grupo 6 — Sistema

#### Pausar quando sair da janela

Ligado, o jogo para sozinho quando a janela dele não está na frente.

**Deixe desligado.** Em muitos computadores de escola, o emulador acha que
a janela dele nunca está na frente. É como a luz com sensor de presença
que não enxerga você: você está ali, e ela apaga mesmo assim. O jogo fica
parado e só anda um quadro (uma imagem) a cada `Alt`+`Tab`.

Ligue só se quiser mesmo que o jogo pare quando você troca de janela (por
exemplo, quando o professor chama).

#### Conferir arquivos antes

Verifica os arquivos de sistema toda vez que abre um jogo.

**Deixe desligado.** O ARENA já avisa com a bolinha amarela, e a
conferência lê o disco à toa.

#### Guardar o que eu mexer

Salva suas mudanças de dentro do jogo ao fechar. **Deixe ligado** — é o que
faz o mapeamento do seu controle continuar valendo amanhã, e em outro
computador.

#### Botões por jogo

Deixa você trocar os botões só num jogo, sem bagunçar os outros. Trocou
pulo e tiro num jogo de plataforma? Fica só nele.

---

### Voltar tudo ao normal

No fim da aba Avançado tem **Voltar tudo ao padrão**. Devolve todos os 50
recursos ao valor de fábrica.

Não apaga seus jogos, saves nem recordes.

---

### Mexer no arquivo

Tudo isso mora em **`servidor\recursos.json`**, em texto puro:

```json
{
  "chave": "run_ahead_enabled",
  "nome": "Resposta instantanea",
  "grupo": "resposta",
  "tipo": "bool",
  "custo": "alto",
  "nota_minima": 4,
  "explica": "Tira o atraso natural que todo console tem...",
  "exemplo": "O console de verdade demora 2 ou 3 quadros..."
}
```

Você pode traduzir, reescrever a explicação, mudar a `nota_minima` ou
acrescentar um recurso que o RetroArch tenha e o ARENA não mostre.

**Chave que o RetroArch não reconhece é ignorada.** Se estragar o arquivo, o
ARENA avisa no console e continua funcionando sem a aba Avançado — nada
quebra.


---

## Parte B — Quando alguma coisa der errado

### Atualizar o ARENA sem perder nada

Chegou uma versão nova? Use o **pacote de atualização**, e não o completo.
Não apague nada.

1. Na página do Release, baixe o `ARENA-<versão>-atualizacao.zip` (só o
   programa, uns 11 MB) e desbloqueie o arquivo como na instalação: botão
   direito → **Propriedades** → **Desbloquear** → **OK**.
2. Feche o ARENA (a janela preta também).
3. Descompacte no mesmo lugar onde está a pasta `ARENA` (por exemplo, `C:\`
   ou a raiz do pen drive) e, quando o Windows perguntar, escolha
   **Substituir os arquivos no destino**.

O que o pacote de atualização traz e substitui:

```
ARENA.bat · VERIFICAR.bat · PARTIDA.bat · COLETAR.bat · LEIA-ME e guias 1 a 6
LICENSE · TERCEIROS.md · servidor\ (com o Python embutido) · launcher\ · ferramentas\
```

O que é **seu** e não vem no pacote de atualização:

```
jogos\        seus jogos
dados\        recordes, apelido, amigos, mapeamento de controle
BIOS\         as BIOS que você colocou
retroarch\    o emulador, os núcleos, saves, states, cheats e a configuração dele
emuladores\   PCSX2, Dolphin, RPCS3 e Xenia, com a configuração e os saves deles
perfil\       as coletas do COLETAR.bat
backup\       suas cópias
```

Ao mandar substituir, o Windows só troca o que tem o mesmo nome. Tudo o que
é seu fica.

O **pacote completo** (`ARENA-<versão>.zip`) é para instalar do zero: ele traz
também o RetroArch e os emuladores com a configuração do pacote. Descompactado
por cima de um ARENA em uso, ele troca a configuração que você fez neles (os
jogos, os saves, as BIOS e os recordes ficam).

**Depois de copiar:**

1. Dois cliques em **`VERIFICAR.bat`**.
2. Abra o ARENA.
3. Clique em **Atualizar lista**.

Se alguma configuração antiga não existir mais na versão nova, o ARENA
ignora sozinho — não trava por causa disso.

### Se a tela abrir vazia e ficar em "lendo…"

Sintoma: a janela abre, mas Processador diz "lendo…", Memória e Motor ficam
com um traço, e Jogos fica em 0. A janela preta do servidor está normal.

Quer dizer que a tela não conseguiu carregar. Duas causas:

| Causa | Solução |
|---|---|
| Arquivo do `launcher` veio incompleto | Copie a pasta `launcher` inteira de novo |
| Cache do navegador com a versão velha | Com a janela do ARENA na frente, aperte `Ctrl` + `F5` |

Se persistir, rode o **VERIFICAR.bat**: ele confere se todos os arquivos do
programa estão no lugar.

---


O ARENA tem um verificador embutido. Ele confere a instalação inteira e
conserta sozinho o que der.

**Ele nunca apaga jogo, save nem save state.**

---

### Como usar

Dois cliques em **`VERIFICAR.bat`**, na pasta do ARENA.

Feche o ARENA antes. Leva alguns segundos.

Se quiser só olhar sem deixar ele mexer em nada, abra o Prompt na pasta e
rode:

```
servidor\python\python.exe servidor\diagnostico.py --so-ver
```

---

### O que ele confere

| # | O quê | Conserta sozinho? |
|---|---|---|
| 1 | As 17 pastas do ARENA existem | **Sim**, recria |
| 2 | Os 20 arquivos de que o ARENA precisa para abrir estão lá | Não, avisa |
| 3 | Arquivos temporários esquecidos | **Sim**, apaga |
| 4 | Suas configurações estão legíveis | **Sim**, põe de lado a versão quebrada |
| 5 | O catálogo de jogos está legível | **Sim**, apaga para ser remontado |
| 6 | O banco de recordes está íntegro | **Sim**, restaura da cópia |
| 7 | RetroArch e emuladores presentes | Não, avisa |
| 8 | Espaço em disco, tipo do pen drive (FAT32 não aceita arquivo acima de 4 GB) e jogo com nome tão comprido que o save passaria do limite de 260 letras do Windows | Não, avisa e diz o que fazer |
| 9 | Cópias de segurança existem | Não, informa |
| 10 | A porta 8777 está livre | Não, avisa |
| 11 | O que deixa este computador lento (programas, serviços, telemetria, bateria, memória, disco...) — detalhes no documento 3 | Não, só diz o que fazer e quem faz |

---

### O que ele faz em cada conserto

#### Pasta faltando

Recria vazia. Se era `jogos\pessoais`, seus jogos não voltam — mas eles não
foram apagados pelo verificador, e sim antes.

#### Configuração ilegível

Renomeia para `config.json.quebrado` e deixa o ARENA criar uma nova.

**Você vai precisar reescrever seu apelido** e cadastrar os amigos de novo.
O arquivo antigo fica guardado, caso queira olhar.

#### Catálogo ilegível

Apaga o `manifesto.json`. O ARENA remonta sozinho na próxima abertura, lendo
as pastas de jogos. Não se perde nada — é um arquivo descartável.

#### Banco de recordes danificado

O caso mais sério, e o mais comum quando se puxa o pen drive com o ARENA
aberto.

O verificador procura a cópia mais recente em `backup\`, restaura, e guarda
o banco danificado como `arena.db.quebrado`.

**Você perde só o que jogou depois da última cópia** — e a cópia é feita
toda vez que você fecha um jogo.

Se não houver cópia nenhuma, ele avisa e não mexe. Nesse caso, veja o
documento 4.

**E se você abrir o `ARENA.bat` direto, sem passar pelo verificador?** O
ARENA abre do mesmo jeito. Ele guarda o banco danificado do lado, com o
nome `arena.db.corrompido-` mais a data e a hora, e começa um banco novo,
vazio. A janela preta mostra onde ficou a cópia. Os recordes antigos não
aparecem na tela, mas não foram apagados: rode o `VERIFICAR.bat` depois,
que ele tenta restaurar da cópia em `backup\`.

---

### Um exemplo real

Instalação quebrada de propósito: configuração corrompida, catálogo
corrompido, banco destruído, duas pastas apagadas e dois arquivos
temporários esquecidos.

```
1. Pastas
  criei  jogos/livres
  criei  retroarch/remaps

6. Banco de recordes
  QUEBRADO  file is not a database
  restaurei a copia de 2026-09-06_120000
  o banco danificado ficou como arena.db.quebrado

RESUMO
  Consertado:   7
  Grave:        0
  Consertei o que estava errado. Pode abrir o ARENA.
```

O recorde que estava no banco voltou intacto.

---

### Quando rodar

| Situação | Rode |
|---|---|
| Puxei o pen drive com o ARENA aberto | Sim, na hora |
| O ARENA abre e fecha sozinho | Sim |
| Os recordes sumiram | Sim |
| A lista de jogos ficou vazia sem motivo | Sim |
| Faltou energia no meio da aula | Sim |
| Antes de emprestar o pen drive | Boa ideia |
| Uma vez por bimestre | Boa ideia |

---

### O que ele NÃO resolve

| Problema | Onde resolver |
|---|---|
| Falta o Python | Documento 1, Parte B, passo 2 |
| Falta o RetroArch | Documento 1, Parte B, passo 3 |
| Falta emulador de algum console | Documento 2, "Parte C — Consoles cinzas" (PS2, PS3, Xbox 360, GameCube e Wii: "Parte B — Consoles que pedem programa próprio") |
| Falta arquivo de sistema (a BIOS) | Documento 2, "Parte B — Consoles amarelos: a BIOS" |
| Jogo no console errado | Documento 2, "Como o ARENA reconhece cada console" e "Aviso de disco na pasta errada" |
| Jogo volta para a lista sem abrir | O motivo aparece no alto da tela e no painel do jogo ("Da última vez") — `2-JOGOS.md`, "Quando o jogo não abre" |
| Jogo travando | Documento 3, "Quando travar" |
| Controle não funciona | Documento 3, "Se o controle não aparecer" |
| Amigo não conecta | Documento 5, "Quando não conecta" |

---

### Se ele disser "grave"

Aparece quando ele encontrou algo que não consegue consertar:

| Mensagem | O que fazer |
|---|---|
| `arquivo do programa faltando` | Copie a pasta original do ARENA por cima. Seus jogos, saves e recordes ficam onde estão |
| `consoles.json ilegivel` | Copie esse arquivo da pasta original |
| `banco danificado e sem copia` | Documento 4, seção "Se der ruim" |
| `menos de 0,5 GB livres` | Apague save states que não usa, em *Saves e cheats* |


---

---

## Parte C — Coletar o perfil desta máquina (para o professor)

O **`COLETAR.bat`**, na raiz, tira um retrato da máquina e mede como o
ARENA roda nela. Serve para comparar os notebooks da escola e decidir o que
o ARENA precisa melhorar para o mais fraco.

1. Feche o ARENA, se estiver aberto, e ligue o notebook **na tomada** (na
   bateria o resultado não vale).
2. Dois cliques em **`COLETAR.bat`**. Leva uns 6 minutos.
3. No meio, um jogo de Super Nintendo abre sozinho por uns 70 segundos. É
   de propósito: deixe a janela dele **na frente** e olhe se o som e a
   imagem ficam lisos. (Sem jogo de Super Nintendo na pasta, essa parte é
   pulada.)
4. No fim, responda as 6 perguntas (uma tecla e Enter) — e mais algumas,
   se você já jogou outros consoles nesse notebook: o ARENA compara o que
   ele diz de cada console com o que você viu.

O resultado fica em `perfil\<código>_<data-hora>\`:

| Arquivo | Para quê |
|---|---|
| `maquina.txt` | Retrato da máquina em português: processador (com a velocidade medida de um núcleo e se tem AVX), memória (e quantos pentes), discos (com velocidade e o que o Windows diz deles), vídeo, Windows, rede, de onde o ARENA roda, **o que o ARENA diria de cada console** nela, e **o que deixa essa máquina lenta**, com o que fazer |
| `arena.txt` | O ARENA nessa máquina: tempo para abrir, servidor, lista de jogos, gravações em disco e o jogo de SNES (quadros por segundo), com BOM / NO LIMITE / RUIM, e no fim a **tabela de orçamentos**: medido × teto do notebook-alvo, passou ou não |
| `maquina.json`, `arena.json` | Os mesmos números, para análise |

**Não coleta nada pessoal.** Nem nome da máquina, nem usuário, nem endereço
da placa de rede. A máquina aparece só como um código embaralhado.

**Não pede administrador e não precisa de internet.** O que não dá para
medir sem administrador vira "não foi possível medir". O teste de disco
grava e apaga um arquivo de 64 MB.

**Não muda nada no ARENA.** O efeito é o mesmo de abrir o ARENA e clicar em
Atualizar lista. O jogo roda com saves temporários.

Leve a pasta `perfil` inteira no pen drive: cada máquina ganha a sua pasta,
uma não apaga a outra.
