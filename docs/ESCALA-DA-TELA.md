# Escala da tela e desempenho — item 10 (16 e 17/10/2026)

O pedido do Rafael (15/10/2026), em resumo: todo jogo abre em tela cheia,
desenhado no tamanho que o computador aguenta e "redimensionado, bonito,
perfeitamente desenhado", como o Lossless Scaling; a prioridade é integrar o
Lossless Scaling; se não der, as mesmas técnicas no ARENA; 4K perfeito na
placa boa; leve no computador fraco; "números de testes que comprovem".

**Onde foi medido:** o computador do professor (Ryzen 5 5600G, Radeon
integrada Vega 7, tela 1440×900 a 60 Hz, fone sem fio JBL Quantum 810). **A
régua continua sendo o notebook da escola** (Celeron N5100, Intel UHD,
`docs\MAQUINA-ALVO.md`), que não foi medido aqui: onde o número daqui não
vale para lá, este relatório diz.

**Ferramenta:** `ferramentas\medir_escala.py` (commit `db4efc8`). Para cada
console, um trecho com 3D na tela, achado foto a foto (o jogo sozinho, sem
ninguém apertar botão); o medidor salva um estado no começo do trecho e abre
cada jeito a partir dele; mede por 10 s, a 60 quadros por segundo, quanto da
placa de vídeo o RetroArch gasta (o contador "GPU Engine" do Windows, o mesmo
do Gerenciador de Tarefas); e tira a foto no mesmo quadro em todo jeito. Os
números brutos: `docs\escala_antes_bruto.json` e `docs\escala_nota4_bruto.json`.

## Três achados no caminho

1. **O som exclusivo deixava o jogo 13% mais lento** (commit `a3d6ce0`). O
   perfil Qualidade (o que o automático escolhe para quase todo console) e o
   Ultra tomavam a placa de som só para o jogo (WASAPI exclusivo). Com o fone
   sem fio, a sincronia pelo som segurava o jogo no ritmo do fone:

   | Mesmo jogo de Super Nintendo, 4.300 quadros | Quadros por segundo | Variação de cada quadro |
   |---|---|---|
   | Antes (exclusivo) | 51,97 | 21,3% (tremido) |
   | Depois (compartilhado) | 59,89 | 2,2% |
   | PSP (Burnout Legends), 10 s | 51,0 → 60,0 | — |

   É o mesmo "52 FPS e 22% de variação" do achado de 02/10/2026, que tinha
   ficado só anotado.

2. **O driver desta Radeon força o vsync** ("Aguardar atualização vertical:
   Sempre ligado", `VSyncControl = 3`). Nenhum programa passa de 60 quadros
   aqui. Não atrapalha o jogo (o ARENA joga com vsync), mas impede medir a
   folga "sem trava": por isso o medidor usa a % da placa a 60 quadros.

3. **O computador do professor estava no "Gráfico igual ao console
   original", no perfil Desempenho e no Ultra**, com o "Filtro de tela"
   desligado (`dados\config.json`): todo jogo desenhado no tamanho do console
   e esticado sem filtro nenhum — o "pequeno" do pedido, sem o "bonito".

## Quanto custa esticar (antes)

Pontos de placa a mais sobre esticar sem filtro (bilinear), a 1440×900:

| Filtro | PS1 4x | PSP 2x | N64 2x | DC 1x | SNES |
|---|---|---|---|---|---|
| Pixel nítido (sharp-bilinear) | +0,2 | +1,0 | +1,0 | +0,6 | +1,3 |
| Só a nitidez (RCAS) | +2,4 | +1,3 | +0,7 | +0,2 | — |
| Catmull-Rom | +2,4 | +2,8 | +2,5 | +1,9 | +3,2 |
| Lanczos 2 | +4,5 | +3,8 | +3,5 | +2,9 | — |
| Só o EASU do FSR | +3,3 | +4,8 | +4,3 | +3,5 | — |
| FSR completo (EASU + RCAS) | +4,9 | +5,0 | +5,0 | +4,5 | +6,1 |
| ScaleFX / xBR (2D) | — | — | — | — | +5,7 / +8,8 |

E desenhar maior (a resolução interna), sem filtro:

| Console | 1x | 2x | 4x | 6x |
|---|---|---|---|---|
| PS1 (CTR) | 6,9% | 7,6% | 10,0% | 14,3% |
| PSP (Burnout Legends) | 7,3% | 8,5% | 12,4% | 18,9% |
| N64 (Mario Kart 64) | 8,8% | 10,2% | 15,5% | 23,6% |
| Dreamcast (Gauntlet Legends) | 7,5% | 11,1% | 19,8% | 35,1% |

O que isso ensinou: **o custo do filtro é por ponto da tela, quase fixo**, e
nos consoles antigos desenhar maior é barato. No PSP, desenhar em 4x (12,4%)
custou menos que desenhar em 2x e esticar com o FSR (13,5%). "Desenhar menor
e esticar com FSR" só compensa quando a placa não aguenta desenhar maior.

## O que mudou

- **Escala da tela em todo jogo** (commit `98f8af8`): pixel nítido no 2D, em
  todo nível; no 3D desenhado menor que a tela, FSR na placa boa, Catmull-Rom
  na média, só a nitidez na fraca e nos modos de folga; sem filtro quando o
  jogo já é desenhado do tamanho da tela. Escolha em Ajustes → Simples.
- **Emuladores de fora** (commit `12a3f82`): CAS no PCSX2 em 1x, FSR no
  RPCS3 até 720p, Catmull-Rom no Dolphin em 1x.
- **Lossless Scaling de quem comprou** (commit `50615a0`): achado, licença,
  perfil "ARENA", janela do tamanho do desenho, abre e fecha junto.
- **Nota da placa** (commit `c4c88ef`): o Ryzen de mesa com Vega (série G) e o
  8000G vão a 4 nos núcleos do RetroArch; os emuladores de fora ficam no 3
  em toda integrada; a dedicada antiga e fraca para em 2 (veja abaixo).

## A Radeon integrada com a nota 4 (medido)

Até aqui, toda placa integrada parava na nota 3: o Celeron N5100 e o Ryzen
5 5600G recebiam a mesma imagem. Com a nota 4 nesta Radeon
(`medir_escala.py --nota-placa=4`, `docs\escala_nota4_bruto.json`), sempre a
60 quadros:

| Console | Nota 3 (como era) | Nota 4 (agora, nesta máquina) |
|---|---|---|
| PS1 (CTR) | 4x: 10,0% da placa | 6x + MSAA 4x + xBR: 53,6% |
| PSP (Burnout Legends) | 960×544: 8,5% | 1920×1088: 16,6% |
| N64 (Mario Kart 64) | GLideN64 2x: 10,1% da placa e ~52% de um núcleo | parallel-rdp + FSR: 10,0% e 20,3% |
| Dreamcast (Gauntlet Legends) | 640×480: 7,5% | 1280×960: 12,2% |

Os emuladores de fora (PS2, GameCube e Wii, PS3, Xbox 360) não foram
medidos com a nota 4 — ela levaria o PS2 a 4x e o PS3 a 150% —, então ficam
no 3 em toda integrada. O "jogo travando e som picotando" de 25/09/2026, que
tinha feito a integrada parar no 3, era o aumento de textura xBRZ do PSP (no
processador) e o som exclusivo com o fone sem fio.

**Achado do N64:** o parallel-rdp (que desenha o N64 na placa de vídeo) gastou
um terço do processador do GLideN64 — no modo alvo, 22,0% de um núcleo
contra 75,8%, os dois a 60 quadros. No Celeron, o N64 é limitado pelo
processador; o parallel-rdp pode ser o que faltava, se o Vulkan da Intel UHD
de lá der conta (não medido). Fica como teste para a escola.

## Lossless Scaling, medido com o programa de verdade

| PSP (Burnout Legends) | Placa de vídeo |
|---|---|
| Só o ARENA, tela cheia | ~12,4% |
| ARENA + Lossless Scaling (LS1) | 3,5% + 9,0% = 12,5% |
| ARENA + Lossless Scaling + geração de quadros (LSFG 3) | 6,7% + 33,8% = 40,5% |

A escala do próprio ARENA faz o mesmo pelo mesmo custo, sem o atraso de
captura do programa. O Lossless Scaling vale pelo LS1 e pela geração de
quadros, que só ajuda em jogo abaixo de 60 quadros.

## O que falta (depende do Rafael)

- **O seu ARENA está no "Gráfico igual ao console original", no perfil
  Desempenho e no Ultra** (`dados\config.json`). Com isso, todo jogo é
  desenhado no tamanho do console (o PSP em 480×272) e só ganha os filtros
  baratos. Para ver o resultado deste item na sua máquina: Ajustes → Simples
  → **Automático** e, em Ajustes → Máquina, **Nível do gráfico → Normal**; o
  Ultra também pode ficar desligado.

- **O notebook da escola.** O Celeron N5100 tem a placa de 4 a 5 vezes mais
  fraca que a Radeon daqui (24 unidades a 800 MHz, memória em canal simples).
  Pela conta, o Catmull-Rom (+2,5 aqui) custaria uns +10 lá, e o FSR, uns
  +20. Para medir lá: copiar os quatro jogos das cenas e rodar
  `servidor\python\python.exe ferramentas\medir_escala.py`.
- **O N64 pelo parallel-rdp no notebook da escola**: se ele rodar liso lá, o
  ARENA pode ligá-lo já na placa média (hoje, só da nota 4).
- **A chave "sincronizar com a taxa exata do jogo"** (`vrr_runloop_enable`)
  está ligada no `retroarch.cfg` daqui e no do pacote. Aqui não fez
  diferença (o driver força o vsync); o RetroArch avisa "Game FPS > Monitor
  FPS. Cannot rely on VSync". Vale conferir numa máquina sem essa trava.
