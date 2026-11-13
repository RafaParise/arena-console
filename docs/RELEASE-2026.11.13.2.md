# ARENA 2026.11.13.2

A segunda versão do dia traz o que você pediu depois de usar a primeira no celular: a tela cabe no celular deitado,
o painel do jogo virou uma barra que entra pela direita, a estrela de **favorito voltou a funcionar** e o ARENA
**acha e tira os jogos repetidos**, liberando espaço. E exporta jogos para o cartão SD pelo computador.

## ⬇️ Qual arquivo baixar

| Você vai usar em | Baixe | Tamanho |
|---|---|---|
| 📱 **Celular ou tablet Android** (a maioria dos aparelhos, incluindo Galaxy, Xiaomi, Motorola) | **`ARENA-2026.11.13.2-android-celular-arm64.apk`** | 245 MB |
| 📱 **Chromebook com Intel** ou **emulador de Android no PC** | **`ARENA-2026.11.13.2-android-chromebook-intel-amd-x86_64.apk`** | 234 MB |
| 🖥️ **Computador com Windows 10 ou 11**, primeira vez | **`ARENA-2026.11.13.2-PC-windows-linux-chromebook.zip`** | 1,0 GB |
| 🖥️ **Computador com Windows**, já usa o ARENA | **`ARENA-2026.11.13.2-PC-atualizacao.zip`** (só o programa) | 106 MB |
| 🐧 **Computador com Linux** (Ubuntu, Debian, Mint, Fedora; 64 bits) | o mesmo **`ARENA-2026.11.13.2-PC-windows-linux-chromebook.zip`** | 1,0 GB |
| 💻 **Chromebook da escola** (gerenciado) ou **sem instalar nada** | o mesmo **`ARENA-2026.11.13.2-PC-windows-linux-chromebook.zip`**, num pen drive | 1,0 GB |

No celular, instale o APK por cima do anterior: os jogos, os saves e os recordes ficam. No computador, quem já tem o
ARENA descompacta o `PC-atualizacao.zip` por cima da pasta (só o programa muda: `dados\`, `jogos\`, `BIOS\` e
`retroarch\` não são tocados).

## O que há de novo desde a 2026.11.13

**A tela no celular**
- **Celular deitado:** o topo cabe numa linha só (botões menores) e a faixa "No jogo" ficou com letra menor e
  frases curtas. No Galaxy A12, as duas juntas ocupam 84 pontos de altura (antes, quase metade da tela).
- **O painel do jogo no celular** (Jogar agora, Desafio em rede, Saves e cheats, capa), que não aparecia na tela
  estreita, virou uma **barra que entra pela direita**. Toque na **capa** do jogo ou na alça **‹ Jogo**, na borda da tela. Tocar no
  **nome** do jogo continua abrindo o jogo direto. Fecha no **Fechar**, no botão voltar ou tocando fora.
- **Menos botões no topo:**
  - **Amigos** virou **Jogar junto**: amigos, rede, partidas entre casas, o pen drive e o **Enviar recordes**, com
    o número de recordes esperando no próprio botão.
  - **Recordes** foi para dentro de **Conquistas** (abas Pontuação e Tempo de jogo).
  - O **Enviar recordes** fica em Jogar junto e também no seu **Perfil**.

**Favoritos**
- A estrela **☆** não ficava gravada; agora fica.
- **★ Favoritos** é o primeiro item da lista de consoles: os favoritos de todos os consoles, com a quantidade.

**Jogos repetidos** (coluna da esquerda → **Repetidos e cartão SD**)
- O ARENA compara os arquivos e mostra as **cópias iguais** e o **mesmo jogo em arquivos diferentes**. Nas
  coleções de ROMs com etiquetas no nome (GoodTools, No-Intro), vêm marcadas as variantes ruins que têm uma cópia
  limpa da mesma região: `[b]` dump ruim, `[o]` overdump, `[a]` alternativo, `[h]` hack, `[t]` trainer.
  **Tradução em português e outra região nunca vêm marcadas.**
- Fica sempre pelo menos uma cópia, e fica a da pasta do ARENA. No Windows, os apagados vão para a Lixeira do Windows.
  No celular, no Linux e no pen drive, vão para a **Lixeira do ARENA**, no mesmo cartão: **Devolver tudo** põe cada
  arquivo de volta, e **Esvaziar** apaga de vez e libera o espaço.
- Testado no Galaxy A12 com uma coleção de verdade: 406 repetidos (18,4 GB), sem nenhum erro, e o Devolver tudo
  conferido.

**Exportar para o cartão SD** (no computador)
- Com o cartão no leitor (ou um pen drive), marque os jogos e toque em **Exportar os marcados**. O ARENA copia para a
  pasta `ARENA-jogos` do cartão, uma pasta por console, e confere cada arquivo. No celular, o cartão aparece em
  **Ajustes → Máquina → Procurar jogos no cartão**.

**O ARENA.bat reabre o servidor mesmo com a rede do Windows travada**
- Quando o servidor caía, o ARENA.bat esperava 2 segundos com o comando `ping` antes de reabrir. Num computador em que a
  rede do Windows emperrou, o `ping` não termina nunca, e o servidor não voltava. Agora a espera é feita pelo próprio
  Python do ARENA.

**Versões para PC (recomps) ajustadas a cada computador**
- Como já acontecia com os emuladores: na placa fraca, o recomp abre com resolução original e sem antisserrilhado;
  na média, com resolução 2x e 60 quadros. Vale para o Zelda 64, o Mario Kart 64, o Banjo-Kazooie e o Sonic
  Unleashed. O que você mudar dentro do jogo continua valendo.
- O **Sonic Unleashed** exige processador com AVX. Sem ele (o Celeron N5100 de muitos notebooks da rede), o ARENA
  não baixa e explica o motivo.

## Como esta versão foi conferida

- **Rodada final** (todos os testes de uso real, cerca de 5 horas): 124 de 131 na primeira passada. As 7 falhas foram
  repetidas uma a uma: 6 passaram (eram a máquina carregada ou uma queda rápida do Wi-Fi) e 1 achou um defeito de verdade,
  já consertado (veja abaixo).
- **Bateria rápida:** 1.505 testes, todos certos.
- **Celular (Galaxy A12, Android 12):** APK de teste com a auditoria completa (30 telas, 0 aviso de acessibilidade do axe,
  0 falha de contraste, nada sem nome para o leitor de tela, nada saindo da tela; abertura a frio em 1,8 s; girar, ir à
  tela inicial e pouca memória sem perder nada). Depois, o APK de produção instalado por cima e conferido aberto.

SHA-256 dos arquivos:

```
f40531ebb50021589d0d048c7218a6438708d40f3e845fe4d653b6e437145c51  ARENA-2026.11.13.2-android-celular-arm64.apk
4fc088cf78245df9707df243f123644d6111b47a9f2dd6efac8a758382e6228e  ARENA-2026.11.13.2-android-chromebook-intel-amd-x86_64.apk
83a1ec40fb75bab2df6eae0dfe7b41dec35da7eed406dcb307a14689ba93bdcf  ARENA-2026.11.13.2-PC-windows-linux-chromebook.zip
f87d7c48b73721c9479bc21f6ab6e9860eb4b7dc3b802bc1b018f5228051f1ef  ARENA-2026.11.13.2-PC-atualizacao.zip
```

## Limites conhecidos

- **Exportar para o cartão SD** não foi testado com um cartão de verdade no leitor (a cópia é a mesma do "Levar para
  o cartão" do celular, que foi testada).
- **Lixeira do ARENA:** o espaço só fica livre quando você esvazia.
- **Recomps:** os outros (Ship of Harkinian, dusklight...) ainda abrem com o padrão deles
  (`docs\RECOMPS-DESEMPENHO.md`).
- **Celular:** PS3, Xbox 360 e Java ME são só do computador. Consoles pesados (Wii, GameCube, Dreamcast) ficam lentos
  num celular de entrada como o Galaxy A12.
- **Xbox 360:** o Xenia exige processador com AVX; não roda no Celeron N5100 de muitos notebooks da rede.

- **PS2 no computador:** com o computador muito carregado, o PCSX2 às vezes não chega a começar o jogo (na rodada, 15 de
  40 jogos; com a máquina livre, nenhum). Se acontecer, feche e abra o jogo de novo.
- **Jogar junto:** o botão de apagar um amigo da lista ainda é pequeno para o dedo (16 pontos de altura).

## 🎓 Contribuições de alunos

O ARENA é um projeto da sala, e dois alunos mudaram o rumo das últimas versões:

- **[DOOK3DS](https://github.com/DOOK3DS)**, que levou o ARENA ao GitHub pela primeira vez (a v1.0, em 19/09/2026), trouxe
  o MFG Super Motion, a ideia de juntar o melhor do Lossless Scaling e do MFG e a de deixar o ARENA mais leve: viraram
  o Mais quadros, os quadros de verdade do PS2, do GameCube e do Wii, a janela leve e o MFG baixado pelo Equipamentos.
- **[HugoVHK](https://github.com/HugoVHK)** testou o ARENA em casa, no computador e no celular (Poco X7, Android 15), e
  mandou tudo o que achou, com fotos: o save do PS2 que travava, o bloqueio do Play Protect, o colega com Xiaomi que só
  instalou pelo APKMirror Installer. Viraram a revisão dos saves, o "Continuar de onde parou" que nunca passa por cima
  de um save e a troca da versão-alvo para o Android 15.

Obrigado aos dois. Créditos completos em [CREDITOS.md](https://github.com/RafaParise/arena-console/blob/main/CREDITOS.md).
