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
   - Pedido de 14/10: o GIF escuro mostrar TODOS os personagens e animações
     do modo escuro, sem deixar nenhum de fora, e uma cópia dele na pasta do
     `arena-console` para usar em outros lugares.
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
   - Feito: o botão **Desafio em rede** no painel (esmaecido sem partida em
     dois computadores, com a instrução de jogar a dois no mesmo computador
     embaixo); o anfitrião espera o jogador 2 e o jogo abre nos dois ao mesmo
     tempo (`/api/partida/cheguei`); a lista mostra "esperando você"; o
     pré-teste reconhece a espera; a abertura da BIOS fica de fora, igual
     nos dois (`graficos.json`). A entrada como jogador 2 já estava certa
     (`netplay_request_device_pN`).
   - Depende do Rafael: testar com dois computadores de verdade.
   - Emuladores de fora: o PCSX2 não tem partida em rede (os jogos com
     System Link o ARENA já configura, e eles se acham na rede local); o
     NetPlay do Dolphin não abre pela linha de comando; o PS3 tem o RPCN.
6. **Consoles e BIOS:**
   - Feito: o PS1 abre sem BIOS pelo PCSX ReARMed, que imita a BIOS (o CTR
     abriu assim; `consoles.json → core_sem_bios`). Dreamcast e Amiga já
     abriam sem. O Saturn pelo Yabause, sem BIOS, ficou com a tela preta:
     continua precisando dela (guia 2).
   - Feito: o MSX abre os cartuchos pelo C-BIOS 0.29a, a BIOS livre que vem
     no ARENA (`servidor\bios_livres`; testado com o NOBORUNOCA, MIT, em
     `testes\jogos_livres`). Disquete e fita ainda pedem o `Machines`. O MSX
     não tem Jogar Junto (o blueMSX recusa).
   - Feito: o Atari ST, console novo, liga pelo EmuTOS 1.4 (testado com o
     Rayoid, domínio público). O Hatari não abre pasta com acento: a ponte
     `servidor\ponte_sem_acento.py` abre por uma pasta sem acento e devolve o
     disquete gravado. Sem Jogar Junto (o Hatari recusa).
   - Falta (pedido de 14/10: "todos os consoles de código aberto", mantendo
     os emuladores de sempre): os consoles novos com núcleo já na pasta
     (ZX81, VIC-20, Plus/4, Watara Supervision, Thomson, CHIP-8 e os outros
     que abrirem sem BIOS das empresas), cada um testado com um jogo livre
     (`testes\teste_consoles_livres.py`).
   - Depois: versão nova do pacote (um download só, com tudo), pedido de
     14/10 ("tudo pronto para só colocar o jogo e jogar").
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
