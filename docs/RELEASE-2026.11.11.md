# ARENA 2026.11.11

Mais quadros de verdade em todo lugar: o PS2 a 60 quadros no computador e no celular, o GameCube e o Wii a 60 pelos
códigos do Dolphin, o ARENA escolhendo sozinho o programa de quadros que rende mais na sua placa (MFG Super Motion ou
Lossless Scaling), o painel do driver da placa lido e explicado, e uma janela mais leve.

## ⬇️ Qual arquivo baixar

| Você vai usar em | Baixe | Tamanho |
|---|---|---|
| 📱 **Celular ou tablet Android** (a maioria dos aparelhos, incluindo Galaxy, Xiaomi, Motorola) | **`ARENA-2026.11.11-android-celular-arm64.apk`** | 256 MB |
| 📱 **Chromebook com Intel** ou **emulador de Android no PC** | **`ARENA-2026.11.11-android-chromebook-intel-amd-x86_64.apk`** | 246 MB |
| 🖥️ **Computador com Windows 10 ou 11**, primeira vez | **`ARENA-2026.11.11-PC-windows-linux-chromebook.zip`** | 1,1 GB |
| 🖥️ **Computador com Windows**, já usa o ARENA | **`ARENA-2026.11.11-PC-atualizacao.zip`** (só o programa) | 111 MB |
| 🐧 **Computador com Linux** (Ubuntu, Debian, Mint, Fedora; 64 bits) | o mesmo **`ARENA-2026.11.11-PC-windows-linux-chromebook.zip`** | 1,1 GB |
| 💻 **Chromebook da escola** (gerenciado) ou **sem instalar nada** | o mesmo **`ARENA-2026.11.11-PC-windows-linux-chromebook.zip`**, num pen drive | 1,1 GB |

No celular, instale o APK por cima do anterior: os jogos, os saves e os recordes ficam. No computador, quem já tem o
ARENA descompacta o `PC-atualizacao.zip` por cima da pasta (só o programa muda: `dados\`, `jogos\`, `BIOS\` e
`retroarch\` não são tocados).

## O que há de novo desde a 2026.11.10

**Mais quadros de verdade**
- **PS2 a 60 quadros de verdade, no computador e no celular.** O PCSX2 traz patches de "60 FPS" para 627 jogos
  (ele roda a 30 e o patch faz o jogo desenhar 60 de verdade, sem inventar quadro). O ARENA identifica o jogo pelo
  disco (serial e CRC), liga o patch só naquele jogo e desliga ao sair. No celular, o núcleo ARMSX2 é o mesmo PCSX2 e
  traz os mesmos patches: o ARENA liga do mesmo jeito. Quem tem disco comprimido (`.chd`) ganha o patch a partir da
  segunda partida (o ARENA aprende o serial no registro da primeira).
- **GameCube e Wii a 60 quadros**, pelos códigos que o próprio Dolphin traz para 25 jogos (F-Zero GX, Zelda, Mario
  Sunshine...). O código liga só no jogo e só enquanto o ARENA abre o jogo; o arquivo de ajustes do jogo fica como a
  pessoa deixou.
- **Mais quadros unificado: o ARENA escolhe o programa que rende mais na sua placa.** Com o **MFG Super Motion** (grátis)
  ou o **Lossless Scaling** (pago) instalado, o ARENA abre o certo junto com o jogo, com as opções para a sua máquina,
  e nunca os dois juntos: numa NVIDIA RTX, o MFG (gerador DLSS); numa AMD ou Intel, o Lossless (medido com o
  PresentMon: 59,5 contra 56,6 quadros por segundo). A chave **Mais quadros** fica em Ajustes → Imagem: Automático,
  Sempre, Desligado. No Automático, os quadros a mais só ligam com placa de vídeo dedicada e nunca num console que o
  "Desempenho que aprende" já viu ficar no limite: **nunca um quadro a menos do que antes.**
- O MFG Super Motion não vem no pacote (a licença dele não deixa): o ARENA mostra onde baixar e acha o instalado.

**O painel do driver da placa**
- **Windows com AMD:** o ARENA lê o que o AMD Software (Adrenalin) deixou ligado (sincronia vertical, limite de
  quadros, filtragem de textura, escala RSR, antisserrilhado, anti-lag, cache de sombreadores...) e mostra em
  Ajustes → Máquina o que está certo e o que vale mudar à mão, com o motivo. E se alinha: o limite de quadros do
  driver corta a tela rápida (o ARENA respeita), a escala do RSR vale como nitidez do ARENA.
- **Intel:** o ARENA mostra o caminho do painel e o que conferir.
- **Celular:** o mesmo painel lê o driver da GPU (OpenGL ES, Vulkan), o antisserrilhado forçado, a economia de
  bateria, a taxa da tela escolhida e a escala das animações, e explica o que mexe no jogo.

**Mais leve**
- **Janela leve:** o navegador abre a tela do ARENA num perfil só dele, sem extensões, sincronização, páginas em
  segundo plano e outros serviços (no Edge, de 629 MB para 238 MB e de 14 para 8 processos). Se o navegador já está
  aberto, o ARENA entra nele (+56 MB) em vez de abrir outro.
- **Descanso do fundo animado:** três minutos sem mexer e o fundo para; volta ao primeiro toque.

**Revisão**
- Revisão de código de tudo o que entrou desde a 2026.11.10 (10 achados, 9 corrigidos no código).

## Como esta versão foi conferida

- **1.356 testes automáticos** do servidor passaram antes de cada mudança entrar.
- **Rodada final** (os testes de ponta a ponta, que abrem os emuladores de verdade): **128 de 130** passaram. Os dois
  que falharam foram repetidos com o computador folgado:
  - a **partida entre computador e celular** passou (o celular hospedou e o computador entrou em 18 s; na rodada o
    jogo do teste não estava no celular);
  - o **orçamento da abertura do servidor no modo da máquina-alvo** ficou em 2,56 s (meta 2,3 s; na versão anterior
    eram 4,5 a 5,3 s, e dentro da rodada, com o computador carregado, 4,4 s). A causa medida foi a listagem das
    placas pelo motor do MFG no primeiro pedido da tela, que agora roda em segundo plano. O que sobra é o antivírus
    e o navegador disputando o processador do computador de testes; o servidor sozinho abre em menos de 2 s.
- **Teste no Linux** (Ubuntu no WSL): todos os jogos livres abriram com imagem, o `ARENA.sh` e o `VERIFICAR.sh`
  passaram (664 s).
- **Galaxy A12** (Android 12, 4 GB): o PS2 a 60 quadros provado com o *Black* (o núcleo ARMSX2 escreveu "Enabled
  patch" no registro dele); o teste do Android no emulador (Android 15) e o de estresse passaram na rodada;
  auditoria do celular com o APK de produção (`ferramentasuditoria_celular.py`): pacote 2026.11.11 com versão-alvo 35, sem depuração e sem cópia na nuvem, nenhuma porta aberta pelo app, abertura a frio em 868 ms (mediana), 70 MB de memória, e o ciclo de vida (sair e voltar, girar a tela, pouca memória) passou.
- **PS2 a 60 e MFG no computador** (`testes	este_mais_quadros.py`): o PCSX2 ligou o patch e o motor do MFG pegou a
  janela do jogo e fechou com o jogo.
- **GameCube a 60** (`testes	este_60_dolphin.py`): o Dolphin leu o código do F-Zero GX pelo arquivo do jogo.
- **Revisão de código** de tudo o que entrou desde a 2026.11.10 (10 achados, 9 corrigidos) e uma segunda opinião de
  outra IA sobre o módulo do Dolphin (nenhum defeito real).

SHA-256 dos arquivos:

```
20b01e857cec6a45cc13684e1fe040fd495b2bebcc82665ad4e15bd41b21c501  ARENA-2026.11.11-PC-windows-linux-chromebook.zip
d8910dcdc3b1a2856895576dfbaa826d208d43812fe3981e9563bfebbcf302ca  ARENA-2026.11.11-PC-atualizacao.zip
c6af62f6f43ddf395fdfc4b6837170697a5734b93a57edb0a1b8a6e7ed5d02e0  ARENA-2026.11.11-android-celular-arm64.apk
242719ed3037da37e5197e175bf9e048d25cbc7e477b3bfa05a44411e0e00c7d  ARENA-2026.11.11-android-chromebook-intel-amd-x86_64.apk
```

## Limites conhecidos

- **Celular:** PS3, Xbox 360 e Java ME são só do computador. Consoles pesados (Wii, GameCube, Dreamcast, fliperama de
  3D) ficam lentos num celular de entrada como o Galaxy A12. O PS2 a 60 quadros pede mais do celular: no Automático,
  só liga em aparelho forte.
- **Mais quadros:** o MFG Super Motion e o Lossless Scaling são do Windows. No Linux e no celular, os quadros de
  verdade (os patches do PS2 e os códigos do Dolphin) valem do mesmo jeito; o gerador de quadros, não.
- **Partida entre casas:** precisa de alguém com o repasse ligado e a porta liberada no roteador; na operadora com
  CGNAT (sem endereço público), ninguém de fora chega.
- **Xbox 360:** o Xenia exige processador com AVX; não roda no Celeron N5100 de muitos notebooks da rede.

## 🎓 Contribuição de aluno: DOOK3DS

As ideias desta versão vieram do aluno da conta **[DOOK3DS](https://github.com/DOOK3DS)**, o mesmo que levou o ARENA ao
GitHub pela primeira vez (a v1.0, em 19/09/2026). Em 11/11 ele mostrou ao professor:

- **o MFG Super Motion**, o programa gratuito que cria quadros entre os do jogo: virou o Mais quadros do ARENA, que
  acha o programa, escolhe as opções para cada máquina e o abre junto com o jogo;
- **a ideia de juntar o melhor do Lossless Scaling e do MFG** dentro do ARENA: virou o Mais quadros unificado (o ARENA
  sabe qual programa rende mais em cada placa) e, acima de tudo, os **quadros de verdade**: o patch de 60 do PS2 no
  computador e no celular, e os códigos de 60 do GameCube e do Wii, que não inventam quadro nenhum;
- **a ideia de trocar a parte web por Rust** para o ARENA ficar mais leve: virou a medida de onde estava o peso (o
  servidor em Python usa 42 MB; a janela do navegador usava 629) e, daí, a janela leve e o descanso do fundo.

Obrigado. Créditos completos em [CREDITOS.md](https://github.com/RafaParise/arena-console/blob/main/CREDITOS.md).
