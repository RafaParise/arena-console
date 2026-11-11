# Levantamento: Lossless Scaling, MFG Super Motion e o ARENA (11/11/2026)

Método das skills `replica-recon`, `replica-architect`, `replica-build`, `replica-test` e `replica-diff` (a pasta
`Skills De IA` do Rafael), aplicado ao código do ARENA: Python puro, RetroArch, sem instalar nada. A ideia dos dois
programas e do Rust veio do aluno **[DOOK3DS](https://github.com/DOOK3DS)**, contribuinte do ARENA, adaptada pelo
professor.

## Núcleo do uso

O aluno abre um jogo e ele roda **liso** e **nítido** na tela inteira, sem configurar nada. Os dois programas fazem
isso por fora do jogo: copiam a imagem da janela, esticam e criam quadros no meio.

## Fontes

| Fonte | O que deu |
|---|---|
| `LosslessScaling.dll` 3.2.2 (metadados .NET, lidos em 16/10/2026: `servidor\lossless.py`) | as opções e os valores de cada perfil |
| github.com/NODIX-TECH/MFG-SUPER-MOTION, `README.md`, `LICENSE`, `Engine\README.md`, `Engine\docs\MSM-FG.md` (versão 1.0.5) | as opções do motor, os geradores, o custo medido em cada placa e a licença |
| `Infrastructure\MotionEngine.fs` do MFG (código público) | como a tela dele abre o motor: `--config`, `key=value`, `stop` |
| PCSX2 2.8.2 desta pasta (`resources\patches.zip`, registro `emulog.txt`) | os 627 patches "60 FPS" e como ligar um |
| Medidas no PC do Rafael (Ryzen 5 5600G, Radeon integrada, 60 Hz) | a memória e o processador da tela, e o motor pegando a janela |

## Licenças (o que dá para levar junto)

- **Lossless Scaling:** pago, da Steam. Não vai junto; o ARENA usa o de quem comprou.
- **MFG Super Motion:** grátis, mas com a licença **PolyForm Strict 1.0.0**, que proíbe redistribuir e modificar. O
  código é público, mas não é aberto. Não vai junto; o ARENA usa o instalado. Nenhuma linha dele foi copiada: o
  ARENA só fala com o motor pelas opções documentadas.
- **Patches do PCSX2:** vêm dentro do próprio PCSX2, que o ARENA já distribui. O ARENA só liga um por nome.

## Fluxos

- **F01 Jogar com mais quadros**
  - **No PS2:** o ARENA lê o serial e o CRC do disco, liga o patch de 60 FPS no `gamesettings` do PCSX2, e o jogo
    abre a 60.
  - **Nos outros consoles:** abre o motor do MFG com a janela do emulador, ou o Lossless minimizado. O motor fecha
    junto com o jogo.
- **F02 Ver nítido:** o ARENA escolhe a escala pela placa e pelo jogo: pixel nítido, FSR, Catmull, RCAS, ScaleFX,
  Anime4K ou inteiro.
- **F03 Ajustar:** Ajustes → Emuladores → "Mais quadros" (Automático, Sempre, Desligado).

## O que não dá para copiar (e por quê)

- **LS1:** algoritmo fechado do Lossless.
- **Gerador próprio de quadros:** o MSM FG tem licença que proíbe derivar, e fazer um gerador do zero pede Direct3D
  12 por `ctypes`. Na placa da escola nem o próprio MFG aguenta: na UHD 730, o teste dele mede 13,6 ms por par.
- **VRR e HDR:** as máquinas da escola não têm.
- **Contador desenhado no jogo e Spout:** o ARENA não desenha por cima do jogo, e a transmissão fica desligada de
  propósito.

## Tamanho

**M.** São dois módulos novos (`mfg.py` e `quadros_ps2.py`) e mudanças no `arena.py`, no `navegadores.py` e na tela.
As partes difíceis:
- a janela certa do emulador (o PCSX2 e o Dolphin abrem uma janela de carregamento antes);
- o CRC do PS2 sem biblioteca de fora;
- o perfil leve do navegador sem tela de boas-vindas.

A tabela de recursos está em `features.csv` (nota em `parity.md`) e as decisões em `architecture.md`.
