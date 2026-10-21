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

| | Windows | Android (emulador) | Android ÷ Windows | Descontada a perda |
|---|---:|---:|---:|---:|
| Processador (operações por segundo) | 7,57 milhões | 3,43 milhões | 0,45 | — |
| MSX (quadros por segundo) | 5.790 | 3.107 | 0,54 | **1,19** |
| ZX81 (quadros por segundo) | 2.064 | 892 | 0,43 | **0,96** |
| VIC-20 (quadros por segundo) | 2.839 | 83 | 0,03 | 0,07 (ver abaixo) |
| Disco: gravação | 550 MB/s | 212 MB/s | 0,38 | — |
| Disco: leitura | 930 MB/s | 1.953 MB/s | 2,1 | — |

As duas repetições ficaram perto uma da outra: no Windows, MSX 5.889 e
5.690, VIC-20 2.840 e 2.838, ZX81 2.068 e 2.060; no Android, MSX 3.144 e
3.069, ZX81 938 e 847.

**Descontando a perda.** "Descontada a perda" é o medido no Android ÷ a
perda do processador (0,45). O MSX e o ZX81 ficam perto de 1: o RetroArch do
Android, por si, rende como o do Windows, e a lentidão no emulador é toda do
aparelho virtual, cujo processador faz menos da metade do trabalho do
Windows. Pela conta, um aparelho de verdade com o processador igual ao deste
computador deve rodar esses consoles como o Windows (é a estimativa, não
uma medida num aparelho).

**A margem.** A conta do processador do emulador variou ao longo do dia
(de 0,45 a 0,70 do Windows, em sete medidas): o aparelho virtual divide o
processador com o resto do computador. O desconto, então, tem margem de uns
20% para cima ou para baixo.

**O disco.** A gravação no aparelho virtual sai a 38% da do Windows (ela
passa pelo disco virtual do emulador). A leitura sai mais rápida no
Android, provavelmente porque o arquivo recém-gravado é lido da memória;
para o ARENA, o número que conta é a gravação (os saves e o banco).

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

## Falta

- **O Linux do contêiner (L):** o contêiner do WSL travou de novo em 21/10,
  às 12h34 (a terceira vez, depois de 18 e 20/10), e só o reinício do Windows
  o solta. Depois dele:
  `servidor\python\python.exe testes\teste_sistemas_virtuais.py L`. As
  medidas do Windows e do Android ficam guardadas e entram na mesma conta.
- **O WSL sem contêiner:** este computador não tinha distribuição do WSL
  instalada (conferido em 17/10); o contêiner roda na máquina virtual do
  próprio WSL, então a perda dele deve ser a mesma do WSL.
