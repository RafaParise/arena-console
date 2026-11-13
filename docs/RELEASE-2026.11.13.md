# ARENA 2026.11.13

Agora dá para **jogar com um colega de outra casa mesmo quando a internet de casa não deixa abrir porta** (CGNAT,
comum na fibra e no 4G). O botão **Equipamentos** mostra o que o ARENA já tem e baixa sozinho o que falta. E o jogo de
um sistema roda no outro **por dentro do ARENA**: jogo do Windows no Linux pelo Wine portátil, jogo do Linux no Windows
pelo WSL, e os **jogos de Android no Linux** pelo Waydroid.

## ⬇️ Qual arquivo baixar

| Você vai usar em | Baixe | Tamanho |
|---|---|---|
| 📱 **Celular ou tablet Android** (a maioria dos aparelhos, incluindo Galaxy, Xiaomi, Motorola) | **`ARENA-2026.11.13-android-celular-arm64.apk`** | 245 MB |
| 📱 **Chromebook com Intel** ou **emulador de Android no PC** | **`ARENA-2026.11.13-android-chromebook-intel-amd-x86_64.apk`** | 234 MB |
| 🖥️ **Computador com Windows 10 ou 11**, primeira vez | **`ARENA-2026.11.13-PC-windows-linux-chromebook.zip`** | 1,0 GB |
| 🖥️ **Computador com Windows**, já usa o ARENA | **`ARENA-2026.11.13-PC-atualizacao.zip`** (só o programa) | 106 MB |
| 🐧 **Computador com Linux** (Ubuntu, Debian, Mint, Fedora; 64 bits) | o mesmo **`ARENA-2026.11.13-PC-windows-linux-chromebook.zip`** | 1,0 GB |
| 💻 **Chromebook da escola** (gerenciado) ou **sem instalar nada** | o mesmo **`ARENA-2026.11.13-PC-windows-linux-chromebook.zip`**, num pen drive | 1,0 GB |

No celular, instale o APK por cima do anterior: os jogos, os saves e os recordes ficam. No computador, quem já tem o
ARENA descompacta o `PC-atualizacao.zip` por cima da pasta (só o programa muda: `dados\`, `jogos\`, `BIOS\` e
`retroarch\` não são tocados).

## O que há de novo desde a 2026.11.12

**Partida entre casas, mesmo com CGNAT**
- Sem repasse da turma em Ajustes, o **"Estamos em casas diferentes"** passa pelo retransmissor público do RetroArch
  (o servidor de São Paulo). Quem abre a partida recebe um **código de 20 letras**; quem entra cola o código. A sala
  não aparece em lista pública nenhuma, e a ponte fecha quando o jogo termina.
- Com o repasse da turma em Ajustes, tudo segue como antes (o código de 6 números).
- **A conferência da internet de casa** (em Equipamentos → Partidas pela internet) diz, em 3 passos simples, se a casa
  está atrás de CGNAT, de dois roteadores, ou pronta; quando o roteador deixa (UPnP, só na rede de casa), o ARENA abre
  as portas da partida por 4 horas.

**Equipamentos: o ARENA mostra o que tem e baixa o que falta**
- Uma linha por recurso (consoles, emuladores de fora, imagem, MFG Super Motion, Lossless Scaling, versões para PC dos
  jogos que você tem, WSL, Wine, Waydroid), com ícone e palavra, e um botão. **"Equipar tudo o que é grátis"** baixa em
  fila, em segundo plano, dizendo o tamanho antes.
- O **MFG Super Motion** é baixado do site do autor, com a marca SHA-256 conferida. O Lossless Scaling, que é pago,
  ganha só o botão para a página da loja (não é obrigatório).
- A **versão para PC** (recomp) baixada abre direto no **Jogar**, e o painel do jogo troca entre ela e o emulador sem
  apagar nada.

**Jogo de um sistema no outro, por dentro do ARENA**
- **Linux:** o Equipamentos baixa o **Wine portátil** para a pasta do ARENA, sem administrador. Jogo do Windows abre
  por ele.
- **Windows:** o botão **Instalar o WSL** liga o subsistema de Linux do Windows. **É a única coisa do ARENA que pede
  permissão de administrador**: o ARENA avisa, explica e pergunta antes, e o próprio Windows mostra o pedido. Depois,
  **Preparar o Linux do ARENA** (sem administrador) baixa o Ubuntu 24.04 oficial, confere a marca do site e guarda o
  disco em `emuladores\Linux`. Os jogos de Linux passam a abrir nele.
- **Jogos de Android no Linux:** com o **Waydroid** (o botão **Instalar o Waydroid**, que também avisa antes e usa a
  senha de administrador do próprio Linux), o console **Jogos de Android** aparece no computador com Linux: o ARENA
  lista os apps de jogo, abre o escolhido e instala os APKs da pasta `jogos › pessoais › Android`.

**Consertos**
- O servidor responde ao pedido recusado sem derrubar a conexão (a tela às vezes mostrava "conexão abortada" em vez do
  motivo).
- No celular, o painel **Este celular** ficou certo para os leitores de tela (a barrinha de cada número entrou no lugar
  certo da lista).

## Como esta versão foi conferida

- **1.476 testes automáticos** do servidor passaram (eram 1.414 na 2026.11.12; os novos são do Equipamentos, do Wine,
  do WSL, do retransmissor público, da internet de casa e do Waydroid).
- **Rodada final** (os testes de ponta a ponta, que abrem os emuladores de verdade): **123 de 131** de primeira. A
  rodada correu com o computador sem memória, e as falhas foram repetidas uma a uma:
  - uma era de verdade e foi consertada: o retransmissor público tomava o lugar do repasse da turma quando o endereço
    do repasse era "de casa";
  - quatro passaram sozinhas, com o computador folgado: a abertura do servidor no modo da máquina-alvo (**2,0 s**, meta
    2,3 s), os 36 jogos que rodam abaixo do original, os jogos de PS2 que "não começavam" (começam em 21 s) e o patch de
    60 quadros do PS2;
  - duas pediam o celular, e passaram no Galaxy A12: o PS2 a 60 quadros no celular e o computador entrando como
    jogador 2 na partida do celular (em 18 s);
  - a última é a foto da telinha do PocketStation, que às vezes sai quase vazia (já conhecida; nada dele mudou).
- **Partida entre casas pelo retransmissor público:** dois RetroArch de verdade, o jogador 2 entrou. **Linux** (Ubuntu
  no WSL): passou (683 s). **Chromebook** (a versão do navegador): passou. **Navegadores** (Edge, Chrome e Firefox):
  passaram. **Android 15** no emulador e o teste de estresse: passaram.
- **Galaxy A12** (Android 12, 4 GB), com o APK de produção (`ferramentas\auditoria_celular.py`): pacote 2026.11.13
  com versão-alvo 35, sem depuração e sem cópia na nuvem, abertura a frio em 740 ms (mediana), nenhuma falha no
  registro, e o ciclo de vida (sair e voltar, girar a tela, pouca memória) passou. Com o APK de teste (o mesmo código),
  a tela foi conferida no tamanho real do celular: 28 telas, nenhum aviso de acessibilidade (axe) e nenhuma falha de
  contraste, e todas as rotas do servidor responderam.
- **O pacote do computador** foi montado do zero e aberto numa cópia: o servidor abriu, o RetroArch desenhou o jogo de
  prova, e nenhum jogo, BIOS proprietária, save ou dado de quem montou ficou nele.

SHA-256 dos arquivos:

```
e836d18e37ab6853d179993d38e127655b3d44a82bf992c03558086c82c7964c  ARENA-2026.11.13-PC-atualizacao.zip
666079c37a6966cc43b60ddaab59e83f6831ea969864ab8486ae8c9be1222135  ARENA-2026.11.13-PC-windows-linux-chromebook.zip
14979f78eacc18989c04ae10f359ba5882ecc7fca1660de5d76515329cce0cd7  ARENA-2026.11.13-android-celular-arm64.apk
38aa80cebba105ced13affbe09070f0f4a73ad40c83bc8020a0d2f9be70beee9  ARENA-2026.11.13-android-chromebook-intel-amd-x86_64.apk
```

## Limites conhecidos

- **Retransmissor público:** é o servidor do próprio RetroArch, de terceiros; se ele estiver fora do ar, a partida
  entre casas sem repasse da turma não abre (a mensagem diz isso). Com o repasse da turma, a escola não depende dele.
- **Waydroid** precisa de Linux com o *binder* no núcleo e sessão gráfica Wayland. Não funciona dentro do WSL. Sem
  isso, o Equipamentos diz o que falta. Ainda não foi testado num Linux de verdade com binder (os testes simulam as
  respostas do Waydroid): se der problema, conte numa *issue*.
- **WSL** pede Windows 10 (2004 ou mais novo) ou 11 e a virtualização ligada na BIOS do computador.
- **Jogo de PC no celular:** não. O processador e o sistema são outros; lá o console PC aparece cinza, com o motivo.
- **Celular:** PS3, Xbox 360 e Java ME são só do computador. Consoles pesados (Wii, GameCube, Dreamcast) ficam lentos
  num celular de entrada como o Galaxy A12.
- **Xbox 360:** o Xenia exige processador com AVX; não roda no Celeron N5100 de muitos notebooks da rede.

## 🎓 Contribuições de alunos

O ARENA é um projeto da sala, e dois alunos mudaram o rumo das últimas versões:

- **[DOOK3DS](https://github.com/DOOK3DS)**, que levou o ARENA ao GitHub pela primeira vez (a v1.0, em 19/09/2026), trouxe
  o MFG Super Motion, a ideia de juntar o melhor do Lossless Scaling e do MFG e a de deixar o ARENA mais leve: viraram
  o Mais quadros, os quadros de verdade do PS2, do GameCube e do Wii, a janela leve e, nesta versão, o MFG baixado
  sozinho pelo Equipamentos.
- **[HugoVHK](https://github.com/HugoVHK)** testou o ARENA em casa, no computador e no celular (Poco X7, Android 15), e
  mandou tudo o que achou, com fotos: o save do PS2 que travava, o bloqueio do Play Protect, o colega com Xiaomi que só
  instalou pelo APKMirror Installer. Viraram a revisão dos saves, o "Continuar de onde parou" que nunca passa por cima
  de um save e a troca da versão-alvo para o Android 15.

Obrigado aos dois. Créditos completos em [CREDITOS.md](https://github.com/RafaParise/arena-console/blob/main/CREDITOS.md).
