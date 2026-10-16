# Pendências do ARENA

Lista curta do que falta. Ao terminar um item, apague a linha (o registro
fica no commit). O detalhe de cada pedido está em
`git show bfc84a0:CLAUDE.md`, seção "Estado atual".

## Pedidos de 15/10/2026, nesta ordem

Visão do Rafael: o pacote vem o mais completo possível, com BIOS e
emuladores livres, e só fica para baixar o que não tem versão livre. Quando
um console tiver o original (do professor) e o livre, o ARENA pergunta qual
usar, para BIOS e para emulador.

Primeiro, o que já estava pedido:

1. Feito: o Java ME (FreeJ2ME-Plus com o Java do ARENA, `fc788dd`), as
   versões antigas no histórico e nos Releases (`v0.9` do professor e `v1.0`
   do aluno DOOK3DS, `1cdb034`) e o `CREDITOS.md` (`009722f`).
2. Feito: a escolha entre o original e o livre (`servidor\jeitos_de_abrir.py`):
   o PS1 com a OpenBIOS (`f50cdac`); o GameCube e o Wii pelo Dolphin de fora
   ou pelo núcleo do RetroArch, com os arquivos de apoio `dolphin-emu\Sys`.
   O Saturn não tem jeito livre (tela preta sem a BIOS, nos três
   emuladores). O Play! (PS2 sem BIOS) não entrou: o RetroArch fica preso
   ao fechar e ele cai em pasta com acento (números no guia 2).
3. Feito: a biblioteca de jogos livres por console (`servidor\biblioteca_livre.json`,
   37 jogos de 15 consoles, baixados de quem publicou, com a marca conferida).
   Do mamedev.org, 20 dos 28: os 8 da Video Klein são de pôquer e aposta.
4. Feito o levantamento (`docs\SALA-LIMPA-BIOS.md`): dá só para homebrew, no
   Intellivision e no ColecoVision; o Odyssey 2 não vale a pena. Recomendação:
   não fazer agora (abaixo, em "Depende do Rafael").
5. Feito: os jogos do professor abrem em todos os consoles (a rodada final de
   15/10 e, de novo, os 3 "NAO ABRE" dela, que eram aberturas lentas). Das
   BIOS dele, só a do Dreamcast tem alternativa livre: o jeito livre dele
   entrou (`80a7d35`). O `protege_cfg` passou a guardar a `system\dc`.
6. Feito: os fundos e os GIFs (a Fire Stingray rosa, as naves sem piloto do
   F-Zero, nove karts, Clown Car, Sparkster, Ryu, Mega Man X, Bomberman,
   Bonk e os de longe no pé do morro; os GIFs com todos, pelo tema do GitHub).
7. Feito: as pendências desta lista (a pasta system relativa do N64 e do
   VICE, o nome do jogo na ponte sem acento, a descoberta de colegas só
   com a rede aberta, o código de amigo curto, o "Mostrar na pasta" dos
   pacotes) e, abaixo, o que fica com o professor. De quebra, três
   consertos de segurança: a cópia da ponte não sai da pasta dela, a lista
   de amigos só muda deste computador, e o código curto com dois donos não
   vira escolha no chute.
8. Feito: o `INICIAR-ARENA.bat`/`.ps1` do professor (fora do git, de
   propósito). O erro: o OmniRoute passou a exigir chave de API, e o
   `omniroute setup-claude` recebia "401 Authentication required", não
   criava perfil nenhum e o script parava no passo 4 com uma mensagem que
   não dizia o motivo. Agora ele pede a chave (sem mostrá-la), reaproveita
   os perfis, liga o OmniRoute com os scripts liberados (o Windows bloqueava
   o `omniroute.ps1` na janela nova), pula o plugin já instalado e libera só
   os comandos do projeto (sem o `python:*`, e barrando o `git add -A` e o
   `push --force`). O plano dele passou a ser este arquivo.
9. Feito (16/10): o Release v2026.10.16. O pacote completo é um download só,
   o `ARENA-2026.10.16.zip` (528 MB; 66 consoles, 63 núcleos, o Java do Java ME,
   os arquivos de apoio do Dolphin e as BIOS livres, a OpenBIOS inclusive); ao
   lado, o de atualização (12 MB), para quem já usa o ARENA. Antes, a rodada
   final inteira: 110 de 110 (`fdb8e77`).

Depois do Release, nesta ordem:

10. Tela cheia com escala otimizada em todo jogo (como o Lossless
    Scaling): integrar o Lossless Scaling do professor, se a licença
    deixar; se não, as mesmas técnicas no ARENA. Inclui o 4K nas placas
    boas e números de desempenho antes e depois.
11. O ARENA em qualquer navegador (não só o Edge), com testes.
12. Chromebook.
13. Linux, idêntico.
14. Android: antes, um emulador de Android de código aberto para os
    testes; depois, o APK nos Releases.
15. Testes nos sistemas virtuais (Docker e WSL), com números e
    descontando a perda de rodar dentro de outro sistema.

Achado de 16/10 que espera conserto:

- O Windows reserva faixas de porta para o Hyper-V e o WSL, e elas mudam a
  cada reinício (`netsh interface ipv4 show excludedportrange protocol=udp`,
  sem administrador). Em 16/10, de 55335 a 55434 (UDP): a 55355 dos comandos
  de rede dos testes caiu dentro, e o RetroArch não atendia nada (os testes
  já escolhem outra, `testes\porta_de_comando.py`). As portas do ARENA
  ficaram de fora por uma: a 55435 (partida a dois) e a 55436 (descoberta).
  Avaliar o `VERIFICAR.bat` e o `PARTIDA.bat` conferirem essas faixas e
  avisarem, antes do item 15 (o Docker e o WSL criam essas reservas).

## Depende do Rafael

- Mandar ao Suporte do GitHub o pedido de limpeza do PR #1 e do cache. O
  texto está pronto em `backup\git\pedido-ao-suporte-do-github.txt`.
- Pelo site do GitHub: a "Social preview" (Settings → General, com o
  `docs\imagens\arena-escuro-curto.gif`, 1280×640 e menos de 1 MB) e os
  repositórios fixados do perfil.
- O perfil do GitHub (bio, empresa, local e site) espera o escopo `user` do
  gh: rodar `gh auth refresh -h github.com -s user`, que abre o site para
  entrar.
- Atualizar a pasta dos alunos (`..\ARENA`) com o
  `ferramentas\montar_versao_alunos.py --atualizar` e, para os consoles
  novos, copiar para ela as pastas `retroarch\cores` e `retroarch\info` do
  pacote novo (guia 6). O `--atualizar` só troca o programa: para o
  GameCube e o Wii pelo núcleo, copiar também a
  `retroarch\system\dolphin-emu\Sys`; sem ela, os dois seguem pelo Dolphin
  de fora, sem pergunta.
- Rodar o `INICIAR-ARENA.bat` de novo: no passo 4 ele pede a chave de API do
  OmniRoute (no painel, http://localhost:20128, na parte de chaves). O
  caminho com a chave certa eu não pude testar: só você tem a chave.
- As BIOS que faltam estão listadas em `BIOS\LEIA - O QUE FALTA.txt`.
- O `mslugx.zip` está danificado. Só uma cópia nova resolve.
- O botão "Gerenciar catálogo" (o editor do acervo autorizado, escondido
  desde a versão 0.9): com ele, qualquer pessoa diante da tela marca "tenho
  autorização" e o ARENA baixa do archive.org ou do GitHub o arquivo que ela
  indicar. Recomendação: deixar escondido. Os jogos livres conferidos já vêm
  pela biblioteca livre (item 3), e os da turma vão em `jogos\pessoais`. Se
  quiser o editor só para o professor (com senha), é um pedido novo.
- Apagar, se quiser, a pasta `C:\Projetos\Criador De Apps PedagÃ³gicos` (o
  nome estragado de "Pedagógicos"): só tem o cache do N64 da rodada final de
  15/10, gravado ali pelo caminho em ANSI. Desde 16/10 o ARENA não grava mais
  lá (guia 2, "Nintendo 64 e Commodore numa pasta com acento").
- Testes de sala: Jogar Junto em dois computadores de verdade (e em 5
  notebooks), o Celeron, o pen drive e os controles na mão: o Diddy Kong
  Racing só no teclado e, se der, um jogo de PS1 com 6 ou mais controles.
- BIOS livre por sala limpa (`docs\SALA-LIMPA-BIOS.md`): se quiser, um
  projeto de aula para o Intellivision (uma turma escreve a especificação,
  outra, que nunca viu o original, escreve o código). Eu não posso garantir
  a sala limpa: já posso ter visto o código original nos meus dados.

## Limites conhecidos (registrados, sem conserto)

- Só 4 controles do tipo Xbox de cada vez (limite do Windows, o XInput). O
  driver SDL2 do RetroArch passaria disso, mas a tela traduz os botões para
  a numeração do XInput: fica para depois de um teste com os controles na
  mão.
- Emuladores de fora no Jogar Junto: o PCSX2 não tem partida em rede (os
  jogos com System Link o ARENA já configura, e eles se acham na rede
  local); o NetPlay do Dolphin não abre pela linha de comando; o PS3 tem o
  RPCN.
- Na partida a dois de PS1 (PCSX ReARMed), o memory card do convidado
  nasce em branco e não sincroniza.
- A partida pela internet (repasse) entre operadoras diferentes ainda não
  foi validada.
- A descoberta de colegas não tem senha (revisão de segurança de 16/10/2026):
  quem está na rede vê o código de todos e pode anunciar o de outro (o
  inteiro, com o colega desligado, ou um que começa igual, e aí o código
  curto fica com dois donos). O ARENA não escolhe no chute quando há dois, e
  quem está no ar não perde o lugar; o endereço digitado na mão continua
  sendo o jeito seguro de adicionar um amigo.
