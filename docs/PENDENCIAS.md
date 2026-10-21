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

10. Feito (16 e 17/10): a escala da tela, com o relatório e os números em
    `docs\ESCALA-DA-TELA.md`.
    - Todo jogo esticado até a tela com o filtro certo (pixel nítido no 2D;
      FSR, Catmull-Rom ou só a nitidez no 3D, pela placa), também nos
      emuladores de fora (CAS no PCSX2, FSR no RPCS3, Catmull-Rom no
      Dolphin). Escolha em Ajustes → Simples → Escala da tela.
    - O Lossless Scaling de quem comprou: o ARENA o acha, confere a licença
      da Steam, ajusta o perfil "ARENA" e o abre junto com o jogo
      (`servidor\lossless.py`). O programa não vai no pacote nem no git: é
      pago e o próprio motor dele confere a instalação pela Steam.
    - No caminho: o som exclusivo deixava o jogo a 52 quadros com o fone
      sem fio (agora 60, variação de 21% para 2%), e a nota da placa (o
      Ryzen de mesa com Vega vai a 4 nos núcleos do RetroArch; a dedicada
      antiga para em 2).
11. Feito (17/10): o ARENA em qualquer navegador, com o relatório em
    `docs/NAVEGADORES.md`. A tela abre no navegador padrão do aluno (ou no
    escolhido em Ajustes → Simples → Abrir a tela em). Teste novo,
    `testes/teste_navegadores.py`, numa cópia do ARENA: 30 de 30 no Edge, no
    Chrome for Testing e no Firefox (sem instalar nada), com os números de
    abertura, memória e processador.
12. Feito (17/10): o ARENA no Chromebook, com o relatório em
    `docs/CHROMEBOOK.md`. No Chromebook gerenciado o Linux vem desligado,
    então o ARENA roda dentro do próprio Chrome (`ARENA-CHROMEBOOK.html`),
    aberto do pen drive: a mesma tela, o mesmo RetroArch 1.22.2 em
    WebAssembly (34 núcleos, 35 consoles), o mesmo save do Windows no pen
    drive. Teste novo, `testes/teste_chromebook.py`: 41 de 41 no Edge, no
    Chrome e no Firefox; NES, Super Nintendo e Mega Drive a 60 quadros com
    o processador freado 4 vezes. Falta o teste num Chromebook da escola
    (em "Depende do Rafael").
13. **Feito (17 a 21/10):** o ARENA do Linux, idêntico, com o relatório em
    `docs/LINUX.md`. O mesmo pen drive abre no Linux pelo `ARENA.sh`: o
    mesmo servidor e a mesma tela, o Python portátil do Linux, o RetroArch
    1.22.2 do Linux (o AppImage, que sai para `~/.cache/arena` sem FUSE), os
    63 núcleos `.so`, o Java ME com o Java do Linux, o PS2, o PS3 e o Xbox
    360 com os emuladores do Linux usando a mesma pasta de dados dos do
    Windows, e o mesmo `retroarch.cfg` (caminhos e motores traduzidos a cada
    abertura). A bateria inteira passa no Linux (532 de 532, 17/10). O
    teste de ponta a ponta (`testes/teste_linux.py`) de 21/10: **32 de 32**
    aberturas com imagem (também numa pasta com acento), o servidor, o
    `ARENA.sh`, o `VERIFICAR.sh`, o PCSX2, o RPCS3 e o Xenia, sem nenhuma
    falha. O que as rodadas acharam está consertado: o MSX (o `config.ini`
    do C-BIOS com barra invertida, que também valia para o Android), o Java
    ME com acento, o RPCS3, o falso "Python incompleto" e, na revisão, o
    Xbox 360 do Linux (o ajuste e o Xenia Netplay, que só existe para
    Windows).
14. Android: em andamento (18/10), com o relatório em `docs/ANDROID.md`.
    Feito o emulador de testes (o do AOSP, com o Android 15 de código
    aberto: `ferramentas/preparar_android.py`) e o APK do ARENA
    (`ferramentas/montar_android.py`): o RetroArch 1.22.2 oficial para
    Android com uma peça compilada do código oficial com o remendo do ARENA
    (a mesma linha de comando do Windows, e com ela o Jogar Junto), o
    **servidor de verdade do ARENA** com o Python 3.13.16 do Android, a tela
    de sempre, 62 núcleos e os jogos livres. Revisado em segurança: só a
    tela do ARENA fala com o servidor, e o que ele grava (e os recordes)
    fica no app. **Falta** o teste no emulador (`testes/teste_android.py`,
    pronto para rodar) e o APK nos Releases. Em 20/10, o APK de teste foi
    remontado com o servidor de agora e o teste começou, mas o Claude Code
    o encerrou de novo porque a memória do computador ficou crítica.
15. Testes nos sistemas virtuais (Docker e WSL), com números e
    descontando a perda de rodar dentro de outro sistema.
16. **Feito em 20/10** (adiantado, com o 13 ao 15 parados à espera do
    Rafael): o fundo novo (`launcher/field-background.js`, guia 3) e o GIF
    do README gravado de novo. O pedido: o fundo animado do tema
    claro, com personagens em tamanhos proporcionais entre si (o Ryu estava
    pequeno perto do Link; o Mario, o Sonic e o Bomberman, fora de
    proporção; a bomba e a explosão ficam como estão). Cenas novas: Ryu e
    Ken treinando (cada um com o seu hadouken, o shoryuken do Ken com o
    punho de fogo, o tatsumaki senpukyaku) e saindo andando; o Tails com o
    Sonic; o Luigi com o Mario, logo depois do Yoshi; um Yoshi roxo que vem
    pelo ar, pousa perto do verde e os dois comem a fruta do arbusto, que
    balança como no jogo, some ao ser comida e volta depois que eles saem;
    na turma do Donkey Kong, o DK anda, rola e corre, o Diddy dá a estrela
    e corre, a Dixie gira o cabelo e corre e o bebê do DKC 3 rola e corre
    atrás; o coelho branco maior, com uma coelha de jubinha caramelo
    (caramelo com uma listra marrom nas costas) e um coelho médio, sem
    juba, todo preto, maior que a coelha; o Mega Man redesenhado, com um
    companheiro de um dos jogos.

Achado de 16/10, consertado em 18/10: as faixas de porta que o Windows
reserva a cada reinício (Hyper-V, WSL, Docker). O `VERIFICAR.bat`, o
`PARTIDA.bat` e a janela preta conferem as portas do ARENA contra elas
(`servidor\portas.py`, sem administrador) e explicam o que fazer (guia 5).

## Depende do Rafael

- **Se o contêiner do Linux travar de novo** (o WSLC travou em 18 e em
  20/10): só reiniciar o Windows o solta. A máquina virtual dele
  (`vmmemwslc`) roda como serviço do Windows, e nem `wsl --shutdown` nem
  fechar a sessão adiantam. O reinício de 21/10 resolveu.

- **O teste no Chromebook da escola** (item 12, `docs/CHROMEBOOK.md`, "O
  teste no Chromebook da escola"): abrir o `ARENA-CHROMEBOOK.html` do pen
  drive, Ajustes → Máquina → Testar este Chromebook, Baixar o relatório e
  trazer o arquivo `teste-do-chromebook-<data>.json`. E conferir à mão o
  controle USB, o som, a tela cheia e o botão Escolher a pasta do ARENA.
  Se a escola bloquear abrir arquivo do pen drive no Chrome, a saída é
  publicar a versão do navegador num endereço (o GitHub Pages do ARENA,
  por exemplo): decisão sua.
- **O seu ARENA está no "Gráfico igual ao console original", no perfil
  Desempenho e no Ultra**: todo jogo desenhado no tamanho do console. Para
  ver a escala nova por inteiro: Ajustes → Simples → Automático; Ajustes →
  Máquina → Nível do gráfico → Normal (`docs\ESCALA-DA-TELA.md`).
- Medir a escala no notebook da escola: copiar os jogos das cenas (CTR,
  Burnout Legends, Mario Kart 64, Gauntlet Legends, Super Bomberman 4) e
  rodar `servidor\python\python.exe ferramentas\medir_escala.py`. E
  conferir lá se o N64 pelo parallel-rdp roda liso: aqui ele gastou um
  terço do processador do GLideN64 (22% contra 76% de um núcleo no modo
  alvo); se rodar, ele pode valer já na placa média.
- O Lossless Scaling foi tirado da pasta da Steam e posto em
  `arena-console\Lossless Scaling`: ele funciona dali, mas não se atualiza
  mais sozinho. O ARENA também o acha na pasta da Steam
  (`steamapps\common`), se você preferir devolver.

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
