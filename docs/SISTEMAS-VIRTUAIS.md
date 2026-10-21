# O ARENA nos sistemas virtuais (item 15)

Pedido do Rafael (15/10/2026): "testes nos sistemas virtuais (Docker e WSL),
com números e descontando a perda de rodar dentro de outro sistema".

## Onde se mede

As mesmas medidas, no mesmo computador, em três lugares:

| | Sistema | Como |
|---|---|---|
| **W** | O Windows de verdade (a base) | Direto |
| **L** | O Linux num contêiner do WSL | O WSLC, o contêiner da Microsoft que vem com o WSL (o "Docker" daqui), pela parte G do `testes/teste_linux.py` |
| **A** | O Android 15 num aparelho virtual | O emulador do AOSP, pela Plataforma de Hipervisor do Windows (2 núcleos, 2 GB, o vídeo desenhado pelo processador) |

Quem junta e faz as contas é o `testes/teste_sistemas_virtuais.py`; o que se
mede é o mesmo em todo lugar (`testes/medidas_virtuais.py`). Os números
brutos ficam em `docs/sistemas_virtuais_bruto.json`.

## O que se mede

1. **O processador:** a mesma conta que dá a nota do ARENA
   (`hardware.velocidade_de_um_nucleo`), com o Python de cada sistema. A
   razão entre a do sistema virtual e a do Windows é a **perda** de rodar
   dentro de outro sistema.
2. **O RetroArch sem freio:** vídeo e som desligados (`null`), sem esperar a
   tela nem o som, com um jogo livre de três computadores antigos (MSX,
   VIC-20 e ZX81) e as BIOS livres. Uma rodada de 60 quadros e uma longa, de
   uns 8 segundos; quadros por segundo = a diferença de quadros ÷ a
   diferença de tempo, o que tira o tempo de abrir e fechar o RetroArch.
   Cada medida sai duas vezes.
3. **O disco:** a gravação e a leitura de 8 MB (`hardware.medir_velocidade`).

## Os números (21/10/2026)

O Windows e o Linux foram medidos juntos, às 14h37, depois do reinício que
soltou o contêiner; o Android, às 13h55.

| | Windows | Linux (contêiner) | Linux ÷ Windows | Android (emulador) | Android ÷ Windows |
|---|---:|---:|---:|---:|---:|
| Processador (operações por segundo) | 7,44 milhões | 8,57 milhões | 1,15 | 3,43 milhões | 0,46 |
| MSX (quadros por segundo) | 5.653 | 6.017 | 1,06 | 3.107 | 0,55 |
| VIC-20 (quadros por segundo) | 2.787 | 3.021 | 1,08 | 83 | 0,03 |
| ZX81 (quadros por segundo) | 2.018 | 1.899 | 0,94 | 892 | 0,44 |
| Disco: gravação | 1.357 MB/s | 924 MB/s | 0,68 | 212 MB/s | 0,16 |
| Disco: leitura | 991 MB/s | 8.291 MB/s | (da memória) | 1.953 MB/s | (da memória) |

**Descontada a perda** (o medido ÷ a razão do processador):

| | Linux | Android |
|---|---:|---:|
| MSX | 0,92 | **1,19** |
| VIC-20 | 0,94 | 0,07 (ver abaixo) |
| ZX81 | 0,82 | **0,96** |

As duas repetições ficaram perto uma da outra: no Windows, MSX 5.566 e
5.741, VIC-20 2.823 e 2.750, ZX81 1.965 e 2.071; no Linux, MSX 6.113 e
5.920, VIC-20 3.027 e 3.016, ZX81 1.906 e 1.893; no Android, MSX 3.144 e
3.069, ZX81 938 e 847.

**O Android.** O MSX e o ZX81, descontada a perda, ficam perto de 1: o
RetroArch do Android, por si, rende como o do Windows, e a lentidão no
emulador é toda do aparelho virtual, cujo processador faz menos da metade do
trabalho do Windows. Pela conta, um aparelho de verdade com o processador
igual ao deste computador deve rodar esses consoles como o Windows (é a
estimativa, não uma medida num aparelho).

**O Linux.** No contêiner, o RetroArch do Linux rende como o do Windows
**sem desconto nenhum**: de 0,94 a 1,08 do Windows. A conta do processador
sai 1,15 lá dentro, mais rápida que no Windows, e por isso o "descontado"
(0,82 a 0,94) fica abaixo do medido. Essa diferença provavelmente não é a
máquina virtual: a conta é feita em Python, e o Python do Linux (o mesmo
3.13, compilado de outro jeito) costuma rodar esse tipo de laço mais depressa
que o do Windows. Na prática, o contêiner do WSL quase não tira nada do
trabalho do processador, e um computador com Linux de verdade, com este
processador, deve rodar esses consoles como o Windows, com uns 10% para
mais ou para menos.

**A margem.** A conta do processador do emulador variou ao longo do dia
(de 0,45 a 0,70 do Windows, em sete medidas): o aparelho virtual divide o
processador com o resto do computador. O desconto, então, tem margem de uns
20% para cima ou para baixo.

**O disco.** A gravação varia muito de uma medida para outra: a do Windows
saiu a 550 MB/s de manhã e a 1.357 MB/s à tarde, no mesmo dia. Medidas na
mesma hora, a do contêiner do Linux sai a 68% da do Windows, e a do aparelho
virtual bem abaixo (ela passa pelo disco virtual do emulador). A leitura sai
mais rápida nos dois sistemas virtuais porque o arquivo recém-gravado é lido
da memória; para o ARENA, o número que conta é a gravação (os saves e o
banco).

## O que as medidas acharam

- **O VIC-20 no Android:** o núcleo do VIC-20 (o VICE) do Android fica em
  uns 83 quadros por segundo, mesmo sem freio; o do Windows faz 2.839. Não é
  a perda do sistema virtual, porque no mesmo aparelho o MSX e o ZX81 rendem
  como no Windows: é o VICE do Android. Ainda passa dos 50 quadros por
  segundo do VIC-20 neste emulador, mas num aparelho mais fraco pode ficar
  abaixo e o jogo, lento. A causa não foi investigada.
- **O MSX do Android usa o C-BIOS certo:** o registro do RetroArch no
  emulador diz "falling back to 'MSX2+ - C-BIOS'", depois do conserto do
  `config.ini` (`docs/LINUX.md`).
- **O método, consertado no caminho:**
  - Por cima da configuração do ARENA, o RetroArch ficava preso em uns 90
    quadros por segundo em qualquer núcleo (algum ajuste de jogo); a medida
    usa só a configuração dela.
  - No Android, o fim do processo não serve para medir: depois do último
    quadro, o Android deixa o app vivo. A conta usa o registro do RetroArch
    no logcat, do começo do jogo ("[Core] Geometry") ao fim dos quadros
    ("Unloading game").
  - O `unzip` do Android deixava o núcleo cheio de zeros, e o RetroArch
    abria sem jogo e contava quadros do menu: o núcleo sai do APK no
    computador.
  - O CHIP-8 ficou de fora: é leve demais para esta conta.
  - No Linux, sem vídeo, o RetroArch tentava o controle pelo X11 e fechava
    na hora ("Cannot initialize input driver"): a medida liga o controle
    `null` (no Windows e no Linux; o Android fica com o dele). E o tempo de
    quem fechou com erro, 0,03 s, virava bilhões de quadros por segundo sem
    ninguém perceber: agora a medida só aceita o RetroArch que termina com o
    código 0 e a rodada longa que dura de verdade.
  - O contêiner do WSL travou três vezes (18, 20 e 21/10), e só o reinício
    do Windows o soltava: a máquina virtual dele roda como serviço do
    Windows, e nem `wsl --shutdown` adiantava.

## O que ficou de fora

- **O WSL sem contêiner:** este computador não tinha distribuição do WSL
  instalada (conferido em 17/10); o contêiner roda na máquina virtual do
  próprio WSL, então a perda dele deve ser a mesma do WSL.
- **O vídeo:** fica de fora das contas de propósito. O do emulador do
  Android é desenhado pelo processador (SwiftShader), e o contêiner nem tem
  placa de vídeo.

Para medir de novo: `servidor\python\python.exe testes\teste_sistemas_virtuais.py`
(ou só uma parte: `W`, `L` ou `A`; o Android pede o emulador ligado).
