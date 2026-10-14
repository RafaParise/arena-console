# Pendências do ARENA

Lista curta do que falta. Ao terminar um item, apague a linha (o registro
fica no commit). O detalhe de cada pedido está em
`git show bfc84a0:CLAUDE.md`, seção "Estado atual".

## Pedidos de 12/10/2026, nesta ordem

1. **GitHub:**
   - O perfil (bio, empresa, local e site) espera o escopo `user` do gh:
     `gh auth refresh -h github.com -s user`.
   - A "Social preview" e os repositórios fixados só se fazem pelo site,
     com o GIF do item 3.
2. **Fundos animados** (`launcher\field-background.js` e
   `galaxy-background.js`):
   - Feito: o botão "Visualizar animação", o subtítulo novo ("central
     retrô da turma", também no README, no LEIA-ME e na capa) e a joaninha
     fora (`bfc84a0`); 22 personagens novos de 16 bits, 15 visitas em cada
     fundo, todas revisadas quadro a quadro (`ferramentas\revisar_visitas.py`)
     e listadas no guia 3.
3. **GIFs** dos dois fundos:
   - Para a "Social preview" (1280×640, margem de 40 pt, menos de 1 MB),
     para o README e para o perfil.
   - Feito: `docs\imagens\arena-escuro.gif` (Mario e Luigi na Rainbow Road,
     997 mil bytes) e `arena-claro.gif` (o Yoshi, 804 mil bytes), 1280×640,
     no topo do README (um para cada tema do GitHub). Os comandos estão no
     README, em "Imagens desta página".
   - Depende do Rafael: enviar o `arena-escuro.gif` em Settings → General →
     Social preview (só pelo site).
4. **Controles:**
   - Feito, sem os controles na mão: até 8 jogadores (PS1 com o adaptador
     nas duas portas, Saturn até 10, PS2 até 5, tela de controles com 8),
     e as setas movendo também o analógico (RetroArch, PCSX2 e RPCS3; o
     Dolphin já fazia). A ordem continua a mesma.
   - Depende do Rafael: testar o Diddy Kong Racing só no teclado e, se der,
     um jogo de PS1 com 6 ou mais controles.
   - Limite do Windows: só 4 controles do tipo Xbox de cada vez. O driver
     SDL2 do RetroArch passaria disso, mas a tela traduz os botões para a
     numeração do XInput; fica para depois de um teste com os controles.
5. **Jogar Junto:**
   - Revisar o servidor e a entrada do amigo como jogador 2.
   - O anfitrião espera o jogador 2 para começarem juntos, e nesse caso a
     BIOS se pula.
   - Intermediar a conexão também no PS2 e nos outros emuladores onde der.
   - Um botão na lateral direita, com um nome bacana. Fica esmaecido
     quando o jogo não tem partida em dois computadores, e embaixo dele vai
     a instrução de como jogar a dois no mesmo computador.
6. **Consoles e BIOS:**
   - Todos os consoles possíveis, de preferência pelo RetroArch, com BIOS
     livre ou emulação de BIOS (HLE) onde houver.
   - Dizer com clareza onde não dá: o PS2 não tem BIOS livre, e distribuir
     BIOS da Sony, da Sega ou da SNK é proibido.

Também: o botão "Gerenciar catálogo" (acervo) nunca aparece, e um "Abrir a
pasta dos pacotes" ajudaria quem nunca usou computador.

## Depende do Rafael

- Mandar ao Suporte do GitHub o pedido de limpeza do PR #1 e do cache. O
  texto está pronto em `backup\git\pedido-ao-suporte-do-github.txt`.
- Pôr a "Social preview" pelo site (Settings → General).
- As BIOS que faltam estão listadas em `BIOS\LEIA - O QUE FALTA.txt`.
- O `mslugx.zip` está danificado. Só uma cópia nova resolve.
- Testes de sala: Jogar Junto em 5 notebooks, o Celeron, os controles na
  mão e o pen drive.

## Limites conhecidos (registrados, sem conserto)

- Na partida a dois de PS1 (PCSX ReARMed), o memory card do convidado
  nasce em branco e não sincroniza.
- A partida pela internet (repasse) entre operadoras diferentes ainda não
  foi validada.
