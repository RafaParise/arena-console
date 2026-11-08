<!-- Texto a ACRESCENTAR no topo da página do release Latest (a descrição só acrescenta). Falta: rodada final, APK x86_64 e pacote do Windows. -->

## ⬇️ Qual arquivo baixar (atualização de 2026.11.08)

| Seu aparelho | Baixe | O que fazer |
|---|---|---|
| **Computador com Windows** (10 ou 11), primeira vez | **`ARENA-2026.11.08.zip`** | Desbloquear o .zip (botão direito → Propriedades → Desbloquear), extrair em `C:\` ou num pen drive exFAT e abrir o `ARENA.bat` |
| **Computador com Windows**, já usa o ARENA | **`ARENA-2026.11.08-atualizacao.zip`** | Extrair por cima da pasta `ARENA`, escolhendo **Substituir**: jogos, saves e configurações ficam |
| **Computador com Linux** (Ubuntu, Debian, Mint, Fedora; 64 bits) | o mesmo **`ARENA-2026.11.08.zip`** | Extrair e rodar `sh ARENA.sh` |
| **Celular ou tablet Android** (7 ou mais novo; quase todos) | **`ARENA-2026.11.08-arm64-v8a.apk`** | Tocar no arquivo e permitir instalar; instala por cima do anterior sem perder nada |
| **Chromebook da escola** (gerenciado) ou **sem instalar nada** | o mesmo **`ARENA-2026.11.08.zip`**, num pen drive | Abrir o `ARENA-CHROMEBOOK.html` no Chrome (35 consoles, sem jogo em rede) |
| **Chromebook pessoal com processador Intel ou AMD**, ou emulador de Android no PC | **`ARENA-2026.11.08-x86_64.apk`** | O ChromeOS só instala APK baixado com a **depuração ADB** ligada (Configurações → Desenvolvedores → Linux → Desenvolver apps Android; na primeira vez ele pede para restaurar o Chromebook). Não testado num Chromebook de verdade |
| Chromebook pessoal com processador ARM (MediaTek, Snapdragon) | **`ARENA-2026.11.08-arm64-v8a.apk`** | Do mesmo jeito da linha de cima |

Os arquivos que terminam em **`-ANTERIOR`** são das versões passadas, guardados para quem precisar voltar. **Nada de BIOS nem de jogo comercial vem junto**: só os jogos e as BIOS de licença livre.

### O que já foi feito

- **Controle de toque com a cara de cada console** (15 desenhos, com o formato, a cor e os símbolos do controle de verdade:
  triângulo verde, xis azul, bola vermelha e quadrado rosa no PlayStation; botões C amarelos no Nintendo 64...), **em pé e
  deitado**, e o editor **"Arrumar os botões da tela"**.
- **Dois toques rápidos na tela** mostram os botões (SAIR, MENU, SALVAR) quando há um controle de verdade ligado.
- **SALVAR e CARREGAR** no controle de toque, com a foto de onde parou; **o celular vibra também**; **pasta de jogos no
  cartão SD** e levar os jogos da memória para ela.
- **PS2 no celular**: o Mortal Kombat Deadly Alliance voltou a carregar no Galaxy A12 (o nível mínimo deixava o processador
  do PS2 lento demais para o carregamento terminar).
- **Android revisado console por console no Galaxy A12** (23 consoles, um jogo de cada, com os quadros por segundo medidos):
  o **PlayStation** abre em 2,5 s em vez de 32 s de tela preta; o **Saturn** passou de 21 para 56 quadros por segundo (outro
  emulador, o YabaSanshiro, com os botões no mesmo lugar do computador); o botão **"Voltar ao jogo"** traz de volta o jogo
  que ficou aberto atrás do ARENA; Java ME, PS3 e Xbox 360 dizem que são só do computador.
- **Jogar Junto computador × celular pelo cabo**, testado console por console; Mega Drive e Sega CD pelo PicoDrive.
- **Lossless Scaling** (para quem comprou): geração de quadros também no PS2, GameCube/Wii, PS3 e Xbox 360 — medido: um
  jogo que roda a 30 passa a 60 na tela.
- **Auditoria 6**: 21 achados de três revisores, 16 corrigidos (o mais grave: levar jogos para o cartão podia apagar um save
  de mesmo tamanho); 0 problemas de acessibilidade em 108 telas; 1213 testes OK.

### O que ainda falta

- **Rodada final completa** antes de cada versão (matriz de consoles e Linux de verdade) e os **controles de verdade**.
- **Saturn no Jogar Junto entre computador e celular**: o emulador de Saturn não aceita (o salvamento dele só vale no mesmo
  tipo de aparelho); entre dois computadores funciona.
- **Lossless Scaling no celular**: só em placa Adreno 7xx ou mais nova (o A12 não tem).
- Chromebook de verdade com o APK; volante com giroscópio; modo de dados móveis; Android de 32 bits.
