# Máquina-alvo do ARENA

> **Regra do projeto:** toda decisão de desempenho é julgada por **esta
> máquina**, não pelo Ryzen 5 5600G do professor. Se uma mudança fica boa
> no Ryzen e piora aqui, ela piorou o ARENA.

Retrato oficial do notebook mais fraco da escola, feito com o `COLETAR.bat`
em 27/09/2026 e com as anotações à mão do Rafael. Escrito em 30/09/2026.

---

## 1. De onde vêm os números

| Fonte | O que traz | Onde está |
|---|---|---|
| `COLETAR.bat` → `coletar_maquina.py` | Processador, memória, discos (velocidade real), vídeo, Windows, rede | `perfil\D682F0CCEB_2026-09-27_2215\maquina.json` e `.txt` |
| `COLETAR.bat` → `medir_arena.py` | Abertura, servidor parado e em uso, indexação, gravações, jogo de SNES | `perfil\D682F0CCEB_2026-09-27_2215\arena.json` e `.txt` |
| Anotação à mão do Rafael (30/09/2026) | Cronômetro do `ARENA.bat` pelo pen drive e pelo disco, tempo de cópia | registrada no `CLAUDE.md` |
| Intel (página oficial do processador) | Frequências, TDP, instruções, vídeo | ver "Fontes", no fim |

O código `D682F0CCEB` é embaralhado: não revela nome da máquina nem do
usuário. A pasta `perfil\` fica fora do git.

**Condições da coleta:** notebook **na bateria** (52%), plano "Equilibrado",
Wi-Fi marcado como rede **Pública**, java aberto (401 MB) em segundo plano.
Na bateria o processador tende a subir menos de frequência, então alguns
números podem estar um pouco piores que na tomada. É assim que muito aluno
usa o notebook, por isso eles valem como estão.

---

## 2. O que esta máquina é

**Notebook Positivo** (luzes de Wi-Fi e de ligado verdes na tampa traseira).

| Peça | Medido na máquina | Especificação oficial (Intel) |
|---|---|---|
| Processador | Intel Celeron N5100, 4 núcleos, 4 threads | Base **1,1 GHz**, até **2,8 GHz**, TDP **6 W**, 10 nm, lançado no 1º tri. de 2021 |
| Instruções | SSE até **4.2**; **sem AVX, sem AVX2, sem AVX-512** | "Instruction Set Extensions: Intel® SSE4.2" (nada de AVX) |
| Força (PassMark) | — | **1.361** por núcleo; **3.299** com os 4 núcleos (438 amostras) |
| Memória | **7,7 GB** (7.934 MB), **um pente só** de 8 GB a 2.933 MHz; 4,2 GB livres com o Windows aberto | Suporta 2 canais; aqui está em **canal simples** |
| Vídeo | Intel UHD Graphics (integrado), driver 27.20.100.9168 **de janeiro de 2021**; tela **1366×768** a 60 Hz | 24 unidades de execução, 350–800 MHz, DirectX 12, OpenGL 4.5 |
| Disco interno (C:) | 101,7 GB, **só 14,3 GB livres**; o Windows diz "SSD ligado por SD" (modelo A3V012 — pelo jeito, memória eMMC soldada, que o Windows mostra como ligada por SD; não confirmado). Grava 170 MB/s, lê 240 MB/s | — |
| Onde o ARENA estava (D:) | SSD KODAK X120 PRO 1 TB num adaptador USB 3.0 (JMicron). Grava 237 MB/s, lê 289 MB/s. O Windows vê como disco **fixo**, não removível | — |
| Windows | 11 Pro 24H2, 64 bits. A conta usada **era administradora** | — |
| Rede | Intel Wireless-AC 9560. Wi-Fi em rede **Pública** | — |

Para comparar, o Ryzen 5 5600G do Rafael tem PassMark **3.178** por núcleo
e **19.621** no total. **Cada núcleo do Celeron faz 43% do trabalho de um
núcleo do Ryzen, e a máquina inteira faz 17%.** Emulação depende quase
toda de um núcleo só, então os 43% são o número que mais importa.

---

## 3. O que foi medido do ARENA nesta máquina

### Números que valem

| Item | Celeron N5100 | i5-1345U da escola (referência) | Como foi medido |
|---|---|---|---|
| `ARENA.bat` até a tela pronta, **pelo pen drive** (SSD USB) | **8,55 s** | — | cronômetro à mão |
| `ARENA.bat` até a tela pronta, **pelo disco interno** | **5,57 s** | — | cronômetro à mão |
| Servidor responde (de iniciar o `arena.py` até a primeira resposta) | 1,18 s | 0,58 s | `medir_arena.py` |
| Dados da tela prontos (idem, até `/api/estado` e `/api/catalogo`) | 1,48 s | 0,69 s | `medir_arena.py` |
| Memória do Windows tomada ao abrir (servidor + janela da tela) | **488 MB** | 180 MB | RAM livre antes − depois |
| Servidor parado (tela aberta, ninguém mexendo): processador | **2,09% da máquina = 8,4% de um núcleo** | 0,01% | 30 s parado |
| Servidor parado: memória | 41,1 MB | 40,5 MB | idem |
| Servidor em uso: processador | 20% da máquina (80% de um núcleo) | 4,5% | 20 s de pedidos |
| Servidor em uso: resposta média / pior 5% | 38,5 ms / 124,6 ms | 13,8 ms / 35,8 ms | 520 pedidos, 0 falhas |
| Reler a lista de jogos (102 jogos) | 1,23 s | 0,43 s | "Atualizar lista" |
| Gravações em disco com o ARENA parado | **0 por minuto** | 0 | 120 s |
| Copiar a pasta do ARENA (sem jogos) para o disco | 5 min 13 s (27.224 arquivos, 2.548 pastas, 12,2 GB ≈ 40 MB/s) | — | cronômetro à mão |

**Leitura:**
- **Pelo pen drive a abertura levou 3 s a mais** (8,55 s × 5,57 s, +53%).
  Cuidado ao atribuir tudo ao USB: a abertura pelo disco veio **logo depois
  da cópia**, com os arquivos provavelmente ainda no cache de memória do
  Windows. Para separar USB de cache, cronometrar de novo as duas depois de
  reiniciar o notebook.
- **A diferença entre 1,48 s e 8,55 s é o que o script não vê:** o
  `ARENA.bat` (conferências antes do Python), abrir a janela do navegador e
  desenhar a tela. É isso que o aluno espera. O script mede só a parte do
  servidor.
- **O servidor parado não está parado:** 8,4% de um núcleo aqui, contra
  0,01% no i5, com a mesma tela aberta. Ainda não se sabe o motivo (ver
  seção 6).
- **Sob carga, 2,8 vezes mais devagar que o i5**, mas a pior resposta
  (124,6 ms) fica bem abaixo do que se percebe como espera. O teste foi de
  pedidos seguidos **deste mesmo computador**, não de uma sala inteira.

### Números que NÃO valem

| Item | O que saiu | Por que não vale |
|---|---|---|
| FPS do Super Nintendo | 4.140.000 quadros por segundo, marcado [BOM] | **Defeito do medidor, já corrigido** (commits `95f783b` e `1cc6d70`). Ele escolhia o menor jogo da pasta, que desde 26/09 (quando entrou) é o "BS F-ZERO (J)", de Satellaview, que não abre sem a BIOS do BS-X. O RetroArch fechava em segundos, sem abrir o jogo, e a conta explodia. O mesmo aconteceu no i5. **O FPS do SNES nunca foi medido em nenhuma máquina da escola.** A referência do Ryzen (25/09: 60 FPS, variação 3,2%) foi antes e vale |
| Variação do tempo de cada quadro | "não foi possível medir" | Mesmo motivo: o jogo não abriu |
| Respostas "o som picotou?" e "a imagem engasgou?" = "não" | — | Foram dadas sobre um jogo que fechou sem chegar a abrir. Não dizem nada sobre o SNES nesta máquina |

Com o medidor corrigido, o `COLETAR.bat` precisa ser rodado **de novo**
neste notebook, **na tomada**, para ter o FPS e a variação dos quadros.

**Por que não dá para medir o FPS no PC do Rafael no lugar:** testado em
30/09/2026 com o medidor corrigido. O jogo deu 51,7 FPS com 25% de
variação, usando 0,9% do processador. Sem as opções do ARENA, deu 51,0 FPS
com 72%. No mesmo PC, em 25/09, tinha dado 60 FPS e 3,2%. Então não é falta
de força (0,9%) nem as opções do ARENA (sem elas ficou pior): mudou o
ambiente. **Suspeita, não provada:** a janela do jogo não fica em primeiro
plano enquanto o Rafael usa o navegador, e o Windows segura o ritmo de
janela coberta. Regra que sai daqui: o FPS com imagem só vale medido com a
janela do jogo visível e ninguém usando o computador.

---

## 4. O que esta máquina não permite

Cada linha tem a prova. "Mensagem no executável" = texto encontrado dentro
do próprio programa que está na pasta `emuladores\`.

| Limite | Prova | Consequência |
|---|---|---|
| **Xbox 360 não abre** | Mensagem no `xenia_canary.exe`: *"Your CPU does not support AVX, which is required by Xenia"*. O guia oficial do Xenia pede "processador com AVX ou AVX2" | O ARENA não pode oferecer Xbox 360 nesta máquina |
| **PS3 é impraticável** | Requisitos do RPCS3: processador sem AVX2 e com 4 threads ou menos "deve ter desempenho ruim". O Celeron tem as duas coisas | Pode até abrir; não serve para jogar |
| **PS2 está abaixo do mínimo** | Requisitos oficiais do PCSX2: mínimo SSE4.1 (tem), **PassMark por núcleo ≥ 1.500** (o Celeron tem 1.361) e 8 GB de memória (tem 8 GB instalados, 7,7 GB visíveis). Mensagem no `pcsx2-qt.exe`: *"SSE4.1 is now a minimum requirement"* | Abre, mas abaixo do piso que o próprio PCSX2 publica. Não testado aqui |
| **GameCube e Wii (Dolphin)** | Requisitos oficiais do Dolphin: exige "CPU com SSE2" (tem) e recomenda "3 GHz e dois núcleos"; o N5100 começa em 1,1 GHz e só chega a 2,8 GHz em pico | Abre, abaixo do recomendado. Desempenho não medido |
| **Nada que exija AVX** | O processador não tem AVX (Intel e coleta concordam) | Todo programa compilado exigindo AVX fecha na hora, sem aviso útil |
| **Vídeo fraco e com memória emprestada** | 24 unidades de execução até 800 MHz, **memória em canal simples** (a placa de vídeo divide a banda com o processador), tela 1366×768 | Resolução interna alta, filtro pesado e N64 com `parallel-rdp` custam caro aqui. Não medido ainda |
| **Pouco espaço no disco interno** | 14,3 GB livres de 101,7 GB no disco interno. O ARENA sem jogos tem 12,2 GB | Copiar o ARENA para o disco quase enche o C:, e com o C: cheio o Windows fica sem espaço para memória virtual. **Nesta máquina o ARENA roda do pen drive/SSD externo** |
| **Rede Pública no Wi-Fi** | "Rede de Wi-Fi marcada como: Public" | O Firewall fecha mais. A caixa de "permitir" do Python e do RetroArch pede administrador (esta conta tinha, a de aluno não). Pesa direto no Jogar Junto |

---

## 5. O que isso proíbe e obriga no projeto

1. **Nenhuma parte obrigatória do ARENA pode exigir AVX ou AVX2.** O
   Python embutido, o RetroArch e os núcleos usados nos consoles leves têm
   que rodar em SSE4.2. Núcleo novo ou atualização de emulador entra só
   depois de abrir nesta máquina.
2. **IA local: esta máquina é só cliente.** O ARENA não tem hoje nenhum
   módulo de IA. Se um dia tiver, ele roda num computador com AVX2 da rede,
   e o Celeron só pergunta e mostra a resposta. Nunca como parte que o
   ARENA precisa para abrir ou para jogar.
3. **Xbox 360, PS3 e PS2 são "extras de máquina boa".** O ARENA precisa
   saber disso sozinho e dizer ao aluno, em vez de deixar o emulador
   fechar sem explicação (Xbox 360) ou rodar lento demais para jogar (PS3).
4. **Tempo de abertura, memória, processador parado, indexação, gravações e
   FPS do SNES têm teto** (orçamentos, tarefa 2), e o teto é julgado aqui.
5. **O pacote não pode crescer sem motivo:** 12,2 GB sem jogos já quase não
   cabe no disco interno.
6. **A tela tem que caber em 1366×768**, com a barra do Windows aberta.
7. **Tudo o que depende de rede funciona com o Wi-Fi em rede Pública** ou
   explica ao aluno o que fazer, sem supor administrador.
8. **Medir com o jogo visível e na tomada.** Número tirado com janela
   coberta ou na bateria não serve para decidir nada.

---

## 6. O que este retrato revela sobre o ARENA de hoje

Achados que saíram de comparar os números com o código. **Nada foi mudado
ainda**: cada um vira proposta nas próximas tarefas, com aprovação.

| Achado | Prova | Efeito |
|---|---|---|
| **O ARENA dá a mesma nota ao Celeron e ao Ryzen** | `hardware.capacidade()` conta só a quantidade de núcleos (4 = 3 pontos), memória (7,7 GB = 2), motor de vídeo (1 — no Windows 11 sempre, porque o `d3d11.dll` existe) e disco (1, se o disco do ARENA gravar a 45 MB/s ou mais — o SSD USB grava 237): **nota 4, placa 3, perfil "completo"**. O Ryzen 5 5600G também tira **nota 4, placa 3** (conta refeita em 30/09/2026 com a própria função). Só com um pen drive lento (menos de 45 MB/s) o Celeron cairia para 3 | O Celeron recebe os mesmos ajustes de imagem que o Ryzen. A nota não vê velocidade do processador, AVX nem memória em canal simples |
| **O modo econômico não liga nesta máquina, com o ARENA no SSD USB** | Ele liga com perfil "leve", disco lento/médio (menos de 45 MB/s) ou mídia removível. Aqui o perfil é "completo" e o SSD USB é visto como disco fixo e rápido. Com um pen drive comum (visto como removível) ele ligaria | Vigia a cada 20 s em vez de 60 s, e cópia de segurança a cada jogo fechado |
| **Servidor parado a 8,4% de um núcleo** | Medido: 2,09% da máquina, contra 0,01% no i5 com o mesmo medidor (no Ryzen, a auditoria mediu 0,02–0,04% com outro método) | Causa ainda não conhecida. Suspeitas a conferir (não presumir): o vigia a cada 20 s (item acima), a coleta na bateria, a leitura de endereços de rede |
| **Medidor de FPS quebrado** | Seção 3 | Corrigido (commit `95f783b`); falta medir de novo na escola |

---

## 7. Orçamentos

A preencher na tarefa 2 (teto de abertura, memória do servidor, processador
parado, indexação, gravações por minuto e FPS do SNES), com o valor medido
mais uma folga explicada.

---

## 8. Como refazer este retrato

1. No notebook da escola, **na tomada**, com o ARENA no pen drive:
   `COLETAR.bat`. São cerca de 25 minutos.
2. Durante o jogo de SNES, deixe a janela do jogo **à frente** e olhe/ouça.
3. Traga a pasta nova de `perfil\` e peça para atualizar este arquivo.
4. Uma vez por mês, ou antes de cada versão nova. Notebook diferente na
   escola: rode também, porque cada retrato ajuda a decidir.

---

## Fontes

- Intel, especificação do Celeron N5100:
  <https://www.intel.com/content/www/us/en/products/sku/212329/intel-celeron-processor-n5100-4m-cache-up-to-2-80-ghz/specifications.html>
- PassMark, Celeron N5100 (1.361 por núcleo, 3.299 total, 438 amostras):
  <https://www.cpubenchmark.net/cpu.php?cpu=Intel+Celeron+N5100+%40+1.10GHz&id=4331>
- PassMark, Ryzen 5 5600G (3.178 por núcleo, 19.621 total):
  <https://www.cpubenchmark.net/cpu.php?cpu=AMD+Ryzen+5+5600G&id=4325>
- PCSX2, requisitos do sistema: <https://pcsx2.net/docs/setup/requirements>
- Dolphin, requisitos (README oficial: "CPU with SSE2 support", recomenda
  "3 GHz and Dual Core"): <https://github.com/dolphin-emu/dolphin>
- Xenia Canary, guia inicial (CPU com AVX ou AVX2):
  <https://github.com/xenia-canary/xenia-canary/wiki/Quickstart>
- RPCS3, requisitos: <https://rpcs3.net/requirements>. O site recusou a leitura
  automática (erro 403); o trecho citado veio do resumo da busca, não da
  página lida inteira. **Conferir no navegador.**
- Mensagens dentro dos executáveis: procuradas com `grep -a` em
  `emuladores\Xenia\Xenia\xenia_canary.exe` e
  `emuladores\PCSX2\PCSX2\pcsx2-qt.exe` em 30/09/2026.
