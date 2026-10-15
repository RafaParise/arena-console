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
   - Depende do Rafael: enviar o `arena-escuro-curto.gif` em Settings →
     General → Social preview (só pelo site).
   - Feito (pedido de 14/10): o `arena-escuro.gif` mostra todos os
     personagens e animações do modo escuro (as 15 visitas, em velocidade
     dobrada, e os de passagem), com os personagens na frente do nome, e há
     uma cópia na raiz do `arena-console`. O de 1 MB, para a Social preview,
     virou o `arena-escuro-curto.gif`.
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
   - Feito: ZX81 (Factory 2023), VIC-20 (Baguel), Plus/4 (Intervallo) e
     CHIP-8 (Slippery Slope), consoles novos testados com jogo livre nas
     duas pastas (com e sem acento). Só o CHIP-8 tem Jogar Junto (os
     outros três núcleos recusam).
   - Feito: Apple II (DIAFLW, MIT; a ROM vem no AppleWin, que também não
     abre pasta com acento e passou pela ponte), Arduboy (Evade, MIT) e
     MicroW8 (Skip Ahead, domínio público). Arduboy e MicroW8 têm Jogar
     Junto; o Apple II, não.
   - Feito: Atari 8-bit (liga pelo AltirraOS, livre, que vem no emulador; com
     acento, pela ponte), Commodore PET e 128, Watara Supervision e Thomson
     MO/TO. Sem jogo livre publicado que servisse, cada um foi testado com um
     programa que o próprio teste escreve (a cor que ele pinta prova que
     rodou). Atari 8-bit e Supervision têm Jogar Junto; PET, C128 e Thomson,
     não. No Thomson, a fita e o disquete começam pelo Start do controle (a
     partida automática do núcleo ficou desligada, sem jogo para testá-la).
   - Feito: Vircon32 (a BIOS livre vem no núcleo; o menor jogo oficial tem
     18 MB, então o teste escreve um cartucho de 168 bytes que desenha a
     textura da BIOS). Tem Jogar Junto. Ele desenha em OpenGL: o RetroArch
     troca de motor sozinho (driver_switch_enable).
   - Feito (15/10): a versão nova do pacote, num download só (pedido de
     14/10, "tudo pronto para só colocar o jogo e jogar"): o Release
     v2026.10.15, com o `ARENA-2026.10.15.zip` (493 MB, 66 consoles, 62
     núcleos, as BIOS livres) e o de atualização. O README e as notas do
     Release dizem com clareza onde não dá: o PS2 não tem BIOS livre, e as
     BIOS da Sony, da Sega e da SNK não vão no pacote.
   - Depende do Rafael: atualizar a pasta dos alunos (`..\ARENA`) com o
     `--atualizar` e, para os consoles novos, copiar para ela as pastas
     `retroarch\cores` e `retroarch\info` do pacote novo (guia 6).

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
