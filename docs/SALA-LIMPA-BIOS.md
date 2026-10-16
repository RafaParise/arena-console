# BIOS livres por "sala limpa": Odyssey 2, ColecoVision e Intellivision

Pedido do Rafael (15/10/2026): antes de qualquer coisa, levantar a
documentação pública dessas três BIOS pequenas e dizer se dá para fazer
versões livres, como o C-BIOS do MSX e a OpenBIOS do PlayStation.

## A resposta curta

**Dá em parte, e só para jogos novos feitos por fãs (homebrew).** Os jogos
comerciais desses consoles chamam dezenas de rotinas de dentro da BIOS. Uma
BIOS livre que rode esses jogos teria de refazer cada rotina com o mesmo
comportamento, até nos detalhes que ninguém documentou. Para o ARENA, isso
não vale o risco nem o trabalho. E há um limite que não depende de trabalho:
eu não posso garantir uma sala limpa de verdade (abaixo).

## O que é uma sala limpa

São duas equipes separadas. A primeira estuda o original e escreve só o que
cada rotina faz (a especificação), sem copiar código. A segunda, que nunca
viu o código original, escreve a BIOS nova lendo só a especificação. É assim
que se prova, num tribunal, que a BIOS nova não é cópia.

**O limite:** eu sou um modelo treinado com textos públicos da internet, e
listagens e desmontagens dessas BIOS circulam há anos (a do ColecoVision
está até dentro do guia de programação mais usado, abaixo). Não dá para eu
afirmar que nunca vi o código original. Então uma BIOS escrita por mim não
tem como se apresentar como sala limpa. Ela só teria esse valor escrita por
pessoas que comprovadamente nunca viram o original, a partir de uma
especificação.

## Console por console

| Console | A BIOS | O que os jogos usam dela | Documentação pública | Dá? |
|---|---|---|---|---|
| Intellivision | EXEC: 4.096 palavras de 10 bits; GROM: 2 KB de desenhos de letras | Os jogos comerciais quase todos são escritos "em cima" do EXEC (ele roda o laço do jogo, os objetos, o som). Ao ligar, o EXEC procura o cartucho em $4800 e $7000 e, se achar, roda direto | A Mattel tratava o EXEC como segredo industrial. A wiki da comunidade lista uns 30 pontos de entrada, vários com "possivelmente" | **Só para homebrew:** um EXEC mínimo, que só liga o cartucho, mais um GROM com letras desenhadas do zero. O autor do jzIntv já fez algo assim (miniexec/minigrom), não distribuído hoje |
| ColecoVision | OS7: 8 KB (Z80) | Os jogos comerciais chamam as rotinas do OS7 (som, sprites, controles, temporizadores) por uma tabela de saltos | O "ColecoVision Coding Guide" (Daniel Bienvenu, 2005) traz a especificação das rotinas, mas também a listagem do código da Coleco (marcada como confidencial): quem lê se contamina para a sala limpa. Há também o livro de Tony Cruise (2020) | **Só para homebrew:** uma BIOS que mostra a tela de abertura e liga o cartucho. Jogo comercial pediria refazer o OS7 inteiro |
| Odyssey 2 / Videopac | 1 KB, dentro do próprio processador 8048 | Quase todo jogo, até os homebrews, chama as rotinas da BIOS (teclado, som, vídeo) | A documentação técnica da comunidade (Soeren Gust) saiu do ar; sobra a do emulador O2EM e uma ficha de hardware antiga | **Não vale a pena:** sem refazer as rotinas, nem os homebrews abrem |

## O que eu recomendo

1. **Não fazer agora.** Os três consoles continuam pedindo a BIOS de
   verdade, como hoje, com a explicação na tela.
2. **Se o professor quiser:** um projeto de aula de sala limpa de verdade,
   para o Intellivision. Uma turma lê a documentação pública e escreve a
   especificação do EXEC mínimo e do GROM. Outra turma, que não vê nada do
   original, escreve o código e desenha as letras. O resultado abriria os
   jogos homebrew de Intellivision (os feitos em IntyBASIC, por exemplo) sem
   a BIOS da Mattel.

## Fontes

- Intellivision Wiki, "Executive ROM": <https://wiki.intellivision.us/index.php/EXEC>
- Daniel Bienvenu, "ColecoVision Coding Guide" (2005):
  <https://cdn.hackaday.io/files/1959548383695936/COLECOVISION%20CODING%20GUIDE.pdf>
- Tony Cruise, "Programming Games for the ColecoVision and ADAM in Assembler" (2020):
  <https://www.thevideogamelibrary.org/book/programming-games-for-the-colecovision-and-adam-in-assembler>
- O2EM (créditos à documentação técnica de Soeren Gust): <https://generic.aminet.net/misc/emu/o2em.readme>
- Documentação da biblioteca do RetroArch: <https://docs.libretro.com/library/o2em/>,
  <https://docs.libretro.com/library/gearcoleco/>
