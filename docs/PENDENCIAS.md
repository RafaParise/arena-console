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
   - Falta: o máximo de personagens famosos de 16 bits no mesmo estilo
     (espaço no escuro, campo florido no claro) e a revisão de todas as
     animações.
   - Já feito (`bfc84a0`): o botão "Visualizar animação", o subtítulo novo
     e a joaninha fora.
   - Os dois arquivos têm alterações sem commit.
3. **GIFs** dos dois fundos:
   - Para a "Social preview" (1280×640, margem de 40 pt, menos de 1 MB),
     para o README e para o perfil.
   - Em andamento, sem commit: `ferramentas\gif_animado.py` e
     `ferramentas\gravar_fundo_gif.py`.
4. **Controles:**
   - 8 controles nos consoles que permitem e têm jogos com isso.
   - Sem controle, o direcional do teclado também move o analógico (o
     Diddy Kong Racing, no N64, não aceitou o teclado). Revisar todos os
     consoles.
   - A ordem continua a mesma: o 1º controle conectado é o jogador 1, e o
     teclado fica com o próximo livre.
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
