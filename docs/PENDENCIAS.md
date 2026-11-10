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
    fica no app. **O teste no emulador passou em 21/10** (com a sua
    autorização para religar o emulador): instalação, tela, a pasta do
    ARENA do aparelho, o CHIP-8 no RetroArch nativo com o F10 fechando, a
    partida hospedada abrindo a porta 55435, o pedido de fora recusado e a
    pasta do app com os jogos livres (`docs/ANDROID.md`). O que ele achou
    está consertado: os jogos livres do APK fora da lista, o "Failed to
    fetch" na troca de pasta e o teclado com setas tomado por controle.
    **Feito (22/10):** o APK nos Releases, na versão 2026.10.22
    (arm64-v8a e x86_64), depois de passar de novo no emulador.
15. **Feito (21/10):** os testes nos sistemas virtuais (Docker e WSL), com
    números e descontando a perda, no relatório `docs/SISTEMAS-VIRTUAIS.md`.
    O RetroArch do Linux, no contêiner do WSL, rende como o do Windows sem
    desconto nenhum (de 0,94 a 1,08); o do Android, descontada a perda do
    aparelho virtual (o processador dele faz 0,46 do Windows), também (MSX
    1,19; ZX81 0,96). Achado: o VIC-20 do Android (o núcleo VICE) fica em
    uns 83 quadros por segundo mesmo sem freio. No caminho, consertada a
    medida do Linux (o RetroArch sem vídeo fechava na hora, e o tempo de 0,03
    s virava bilhões de quadros por segundo).
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
17. **Feito (22/10):** a versão 2026.10.22 no Release, com o pacote
    completo (1.065 MB; descompactado, 2,6 GB, porque agora leva o Linux),
    o de atualização (104 MB) e os dois APKs. A rodada final de 21/10 deu
    103 de 115, e o que ela achou:
    - consertado no ARENA: o PlayStation fechava sozinho com o filtro RCAS
      e o vídeo em thread (o SwanStation; agora, com o RCAS, ele roda sem a
      thread), o caso do notebook da escola; e a montagem do pacote do
      zero, parada desde 18/10 (a pasta `retroarch\cores` já existia);
    - consertado nos testes (o ARENA estava certo): o fuzz (o corte depois
      do 414), a busca e o download do Internet Archive (o falso na camada
      nova de download), o Android (o aviso de app parado engolia as
      teclas) e a matriz de consoles (o núcleo junto, o Apple II pela ponte
      sem acento e a foto das telas pequenas do CHIP-8 e do Arduboy);
    - do computador de testes: a porta UDP 55436 reservada pelo Windows (4
      testes da descoberta de colegas e da partida), o mamedev.org fora do
      ar (a biblioteca livre) e um jogo que estava fora da pasta (o BS
      F-Zero Deluxe). Depois do reinício de 22/10, com a porta livre e o
      jogo de volta, os 4 de rede passaram e o das BIOS deu 19 de 19; com o
      mamedev.org de volta (11h de 22/10), a biblioteca livre passou
      inteira (4 jogos baixados e abertos).

    Com as 12 repetidas e passando (o orçamento 1b no item 18), a rodada
    fechou 115 de 115.
18. **Investigado (22/10): não é defeito do ARENA.** O orçamento 1b do modo
    alvo (do `arena.py` até os dados da tela, teto de 2,3 s) estourou três
    vezes: 3,2 e 3,05 s na rodada de 21/10 e 3,27 s às 6h24 de 22/10, já
    com o Lively parado (então ele não era a causa). A prova por
    eliminação, às 10h45 de 22/10, com o ARENA na caixa do modo alvo:
    - o servidor sozinho, sem janela: de 0,70 a 0,84 s;
    - a tela aberta por um Edge de fora da caixa: de 0,68 a 0,72 s;
    - como o aluno abre (o ARENA abre o Edge de dentro da caixa): de 0,84
      a 1,14 s;
    - o medidor também dentro da caixa, com o mesmo laço do teste: de 0,61
      a 1,14 s;
    - dentro da caixa, o `/api/estado` inteiro custa uns 30 ms na primeira
      chamada, e o catálogo, uns 140 ms.

    Repetido logo depois, o `teste_orcamentos_modo_alvo.py` passou
    inteiro: 1b em 0,8 s e 1a em 0,81 s. Também não foi a recompilação do
    `arena.py`: o bytecode já estava pronto desde a 01h41. Causa provável:
    carga do computador na hora (às 6h24, 40 minutos depois do reinício e
    logo depois de gerar os documentos das aulas). A caixa prende o ARENA
    nos processadores 0 e 1, em prioridade abaixo do normal, e o trabalho
    do Windows nesses dois passa na frente. O fundo animado não muda a
    conta: nesta máquina ele anima também no "automático". Regra que fica
    (`docs\MAQUINA-ALVO.md`, seção 7): medir com o computador sem carga e,
    se o 1b estourar, repetir antes de procurar a causa no ARENA.

Achado de 16/10, consertado em 18/10: as faixas de porta que o Windows
reserva a cada reinício (Hyper-V, WSL, Docker). O `VERIFICAR.bat`, o
`PARTIDA.bat` e a janela preta conferem as portas do ARENA contra elas
(`servidor\portas.py`, sem administrador) e explicam o que fazer (guia 5).

## Acessórios dos consoles (pedido de 24/10/2026)

Feito: o catálogo `servidor\acessorios.json` (63 acessórios, 25 consoles, chaves conferidas nos núcleos), a tela
Ajustes → Emuladores → Acessórios dos consoles, o PocketStation na entrada 1 do PS2 (cartão de PS1) e os consoles
novos **PocketStation** (núcleo Pokket) e **VMU** (núcleo VeMUlator). Detalhes e fontes em `docs\ACESSORIOS.md`.

Falta (nesta ordem):
1. ~~**DreamPotato**~~ **Feito em 24/10** (`servidor\companheiros.py`: abre junto com o jogo e fecha com ele; o zip dele traz a BIOS
   do VMU da Sega e por isso só fica em `emuladores\DreamPotato`, fora do pacote). Falta testar com um jogo de Dreamcast no PC.
2. ~~**PokketSX** como emulador de fora do PS1 (Windows)~~ **Feito em 24/10**: um jeito a mais de abrir o PS1, na pergunta
   "Como ligar o PlayStation?" (`servidor\pokketsx.py`; o ARENA leva as BIOS, cria o cartão na entrada 2 e escreve o
   `settings.ini`). **Não mostra a telinha do PocketStation** (só o Pokket mostra). Falta testar com um jogo que use o
   PocketStation e com controle de verdade.
3. ~~**Cartão único** do PocketStation entre o PS1 (PokketSX) e o Pokket~~ **Feito em 25/10**: um arquivo só
   (`retroarch\saves\Pokket\Meu PocketStation.srm`), com cópia de segurança. O PS2 fica de fora (não emula o aparelho).
4. Pokket e VeMUlator já abrem no PC e no celular (BIOS: o `kernel.bin` do Rafael); falta testar com minijogos de verdade e no
   Chromebook; o APK já leva os dois núcleos (marcas em `ferramentas\android_nucleos.json`).
5. Ler as opções dos núcleos que só as declaram depois de abrir um jogo (fceumm, fbneo, dolphin, mame2003).
   **Fechado em 10/11/2026, sem mudança:** dos quatro, só o fceumm tem acessório no catálogo, e os três (portas 1, 2 e a
   de expansão) usam só o tipo de controle por porta (`alvo: porta`), que a leitura já traz. Nenhum acessório depende de
   opção desses núcleos.
6. **Conferir com controle real:** o ARENA manda o tipo `517` ao Saturn e ao PS1 (SwanStation); nesses núcleos `517` é
   "Arcade Racer" e "Analog Joystick", e o controle analógico é `261`. Se for defeito, o conserto é de uma linha em
   `servidor\perfis_controle.json`. Não mexi sem teste.
7. Mais acessórios: Game Boy Camera e Printer, e-Reader, cabo link (hoje só por rede no Gambatte), Wii Balance Board,
   EyeToy, Kinect... a lista com o motivo de cada um está no fim de `docs\ACESSORIOS.md`.

## Rodada de 25 e 26/10/2026: o que foi feito e o que falta

**Feito**

- **O celular como controle do jogo do computador** (`servidor\controle_remoto.py`): pelo Wi-Fi, até 8 jogadores, o professor escolhe
  quais jogadores o celular pode ser, a tela mostra o tempo de resposta, e o código tem três faixas de limite de erros e aviso ao
  professor (o risco que sobra está escrito em `docs\PLANO-CELULAR.md`).
- **Pelo cabo USB** (`servidor\controle_usb.py`): um botão abre o controle no celular já conectado; medido no A12, **4 a 6 ms** (o
  Wi-Fi do mesmo celular oscila de 94 ms a mais de 1 s). Ajustes na tela do celular no estilo do GameSir Nexus e do DroidJoy: zona
  morta, curva, diagonais, tamanho, canhoto, volante e 3 perfis.
- **Gamepad Xbox 360 virtual** (`servidor\gamepad_virtual.py`), **opcional e autorizado por você em 26/10**: o celular vira um controle
  de verdade para qualquer jogo do Windows. Exige o driver ViGEmBus (já instalado neste computador pelo `winget`); a DLL vem de
  `ferramentas\baixar_vigem_client.py` (o repositório público não leva binário). Vale para os jogadores 1 a 4.
- **Painel "Este celular" do Android**, um só e ao vivo: corrente da bateria em mA e potência em W, temperatura, calor segundo o
  Android, saúde e capacidade, RAM e memória virtual em tempo real, núcleos do processador, Wi-Fi e controles ligados. Sem o que era
  repetido; sem o que o aparelho não informa.
- **Nenhuma tecla de PC no Android** (F2, F4, F9, F10, Esc, Alt+Tab, "monitor", driver, Xenia): a faixa do jogo mostra MENU, SAIR e
  L3 + R3; `servidor\tests\test_textos_do_android.py` impede a volta.
- **Combo do menu pelo controle corrigido**: o valor `2` é **L3 + R3** (os guias diziam Start + Select, que é o `4`).
- **Jogar Junto entre celular e computador**, testado nos dois sentidos (Super Bomberman 4): com o Wi-Fi do app em modo de baixa
  latência e com "o próximo lugar livre"; plano e medidas em `docs\PLANO-CELULAR.md`.
- **Revisão independente** (4 revisores, um cético por achado): 14 achados confirmados e corrigidos.
- **Testes refeitos** da rodada final: regra de ouro do multitap, PokketSX, capas, como colocar jogos, motor do PS2. Bateria do
  servidor: 1130 testes OK; auditoria de acessibilidade da tela: 0 problemas.
- **Publicação**: os APKs 2026.10.26 estão no mesmo release do 2026.10.22 (a página "Latest"), e a `main` recebeu tudo (avanço
  simples, sem apagar nada).

**O que falta**

- **Controles de verdade** (você): GameSir T4 Nova Lite no celular e G7 HE no computador. Todos os testes desta rodada usaram
  controles virtuais (`testes\controle_virtual_android.py`).
- **Pacote novo do Windows**: o código do computador (controle pelo cabo, gamepad virtual, ajustes) está na `main`, mas o zip e a
  atualização do Windows continuam os da 2026.10.22. **Feito:** o zip e a atualização saíram na 2026.11.08 e de novo,
  montados do zero, na 2026.11.09 (10/11).
- **Release 2026.11.08 — o que falta para publicar (08/11, madrugada):** a versão, a auditoria 6 e o APK de produção arm64
  estão prontos (instalado no A12). O computador ficou sem memória duas vezes e o sistema parou a **matriz de consoles** e
  a montagem do **APK x86_64**; pela regra, só rodam de novo com o seu pedido. Faltam: (1) a rodada final
  (`ferramentas\rodada_final.py`); (2) o APK x86_64 (`montar_android.py --abi x86_64`); (3) o pacote do Windows
  (`montar_versao_alunos.py --zip-completo` e `--zip-atualizacao`); (4) publicar pelo `SINCRONIZAR.bat` e acrescentar à
  página do release o texto de `docs\RELEASE-2026.11.08.md` (com "Qual arquivo baixar" por sistema). **Feito** em
  08/11 (a 2026.11.08) e, completo e limpo, no release novo `v2026.11.09` (10/11).
- ~~Botão "Partida pelo cabo" no Jogar Junto~~ **Feito** (`a12efa1`, testado nos dois sentidos em 07/11).
- **Jogar Junto**: com 8 jogadores e o celular como um deles; num Linux de verdade; Wi-Fi do roteador (o celular está em 2,4 GHz e o
  computador em 5 GHz, e a partida ainda caiu uma vez em 6 s: o cabo é o jeito firme).
- **Chromebook**: o navegador não tem jogo em rede; o APK x86_64 no ChromeOS não foi testado num Chromebook de verdade; o teste do
  Chromebook da escola segue na lista abaixo.
- **Testes**: `teste_navegadores` 30 de 30 (`7a98b86`); `teste_matriz_consoles` refeito na auditoria 6; `teste_android` precisa do
  emulador do Android, que não está instalado neste computador.
- **Volante**: o A12 não tem giroscópio, então o volante usa o acelerômetro e o sinal da inclinação não foi conferido girando o
  celular de verdade.
- **Não feitos, de propósito ou por prioridade**: modo teclado/mouse por SendInput (o gamepad virtual cobre quase todo jogo), aprovação
  de cada celular pelo professor (a saída de verdade do limite de tentativas), modo de dados móveis com servidor-ponte, e a opção
  de Android de 32 bits.
- **Limpezas no celular**: apagar `/sdcard/ARENA/BIOS-PS2-teste` e, se você quiser, desinstalar o `com.armsx2`; o APK de teste foi
  trocado pelo de produção.

## Rodada de 07/11/2026: o que foi feito e o que falta

**Feito**

- **A abertura do ARENA no celular parava minutos** em "Abrindo o ARENA…" com muitos jogos no cartão SD (no A12, 6.567 jogos): a
  busca de capa perguntava ao armazenamento do Android, jogo por jogo, por centenas de nomes. Agora cada pasta é lida uma vez:
  **de mais de 5 minutos (sem terminar) para 24 s**, varrendo do zero. Um vigia (`janela_preta.vigiar_abertura`) escreve no registro de
  queda onde o servidor está se a abertura passar de 60 s.
- **Savestate no celular**: o estado só se salvava pelo menu do jogo (F2 e F4 não existem no celular). O controle de toque ganhou
  **SALVAR e CARREGAR**, e o estado passa a guardar **a foto de onde parou**. Testado no A12: estado e foto gravados, e carregados.
- **Pasta de jogos do ARENA no cartão SD** (Ajustes → Máquina → Onde ficam os jogos): "Criar a pasta no cartão" faz `ARENA-jogos` com
  uma pasta por console; os **jogos baixados** passam a ir para ela; e "Levar jogos da memória para o cartão" lista os jogos que estão
  na memória do aparelho e leva os marcados (copia, confere e só depois apaga o original; o jogo vai inteiro, com as trilhas).
  Testado no A12: pasta criada no cartão, 422 jogos achados na memória, um arquivo de teste levado e conferido.
- **O celular vibra também**: chave que manda o tremor do jogo para o próprio celular, e "Vibrar ao tocar" nos botões da tela.
- **Controle de toque com a cara de cada console**: 15 desenhos (Super Nintendo, NES, Game Boy, GBA, PC Engine, Nintendo 64,
  GameCube, Mega Drive, Saturn, Dreamcast, PlayStation, PSP, Neo Geo, fliperama, Nintendo DS), deitado e em pé, com o formato e a
  posição do controle de verdade. O botão que cada peça manda foi lido do próprio núcleo. **Os dois analógicos** podem ficar sempre
  (para os jogos adaptados), só os do console ou nenhum. Em Ajustes → Imagem → **"Arrumar os botões da tela"** o aluno arrasta cada
  botão, muda o tamanho e volta ao de fábrica.
- **Botões com o desenho, o formato e a cor dos originais** (pedido do Rafael, 07/11, à noite): volume de botão de verdade e letra
  gravada; PlayStation com o triângulo verde, o xis azul, a bola vermelha e o quadrado rosa no botão preto, e as quatro setas soltas;
  direcional de cada console (cruz da Nintendo, disco da Sega, alavanca do fliperama); os quatro C amarelos do Nintendo 64; feijões
  do GameCube. A tela de arrumar mostra as mesmas imagens (rota `/toque/<nome>.png`). 108 imagens de
  `ferramentas\gerar_toque_consoles.py`. Visto no A12 (APK de teste): Crash (PlayStation), Mario Kart 64 e Smash Melee
  (GameCube) com os desenhos novos, e a tela de arrumar com as mesmas imagens.
- **Jogar Junto pelo cabo USB**: botão "Ligar pelo cabo USB" no computador; no celular, a opção "Computador ligado neste celular pelo
  cabo USB" na lista. A revisão de segurança automática achou e eu corrigi: o túnel chega numa porta só para o aviso da partida
  (8778), nunca nas rotas do professor.
- **Quatro botões do celular-controle que nunca funcionaram pela tela** (a chave, o cabo, o gamepad e os jogadores): mandavam o
  pedido sem o método e o navegador recusava. Corrigidos, com teste que impede a volta.
- **Ferramentas em qualquer projeto**: os plugins, MCP, kits, subagentes e permissões ficam no nível do usuário; `continuar-projeto`
  passou a ser um comando geral.
- Bateria do servidor: **1177 testes OK**; auditoria de acessibilidade da tela: **0 problemas** em 108 telas.
- **`teste_navegadores` refeito: 30 de 30** (Edge, Chrome for Testing 157 e Firefox 159; tela pronta em 0,5 a 1,1 s, 32
  quadros por segundo no fundo animado). Os 6 que falhavam eram do próprio teste: a Escala da tela ganhou duas escolhas
  (anime4k e inteiro) e o nome do jogo saiu do cartão para o botão de dentro, e o teste buscava por um texto vazio.

- **Teste no celular pelo cabo (07/11, à noite)**, com o APK de teste novo:
  - **Celular em pé** consertado: o controle de cada console não trocava para o desenho em pé (faltava o botão
    `overlay_next` que o RetroArch exige para girar) e o jogo era esticado até a altura da tela. Agora o jogo fica no alto, na
    proporção dele (remendo `android/retroarch/arena-em-pe.patch`), e os botões embaixo; girando com o jogo aberto, troca sozinho.
  - **SALVAR e CARREGAR** com a foto de onde parou: conferidos no Streets of Rage 2 (o estado e o `.png` gravados no celular).
  - **Vibrar ao tocar**: o ARENA manda a vibração (50 ms por toque, no registro do Android), mas o celular estava em "Não
    perturbe", que zera a vibração de toque de todos os apps. Com o modo normal, vibra.
  - **Jogar Junto computador × celular pelo cabo**, console por console (tabela no guia 5): funcionam Super Nintendo, NES,
    Mega Drive, Sega CD, 32X, fliperama, Neo Geo, Atari 2600, ColecoVision e PlayStation. Mega Drive e Sega CD passaram a usar
    o PicoDrive na partida (o Genesis Plus GX recusa plataformas diferentes). **Saturn** não conecta: o Beetle Saturn declara o estado "platform-dependent" (abaixo).
  - **Tipo de controle errado em 3 consoles** (lido dos próprios núcleos): o ARENA mandava 517 para todos, que é o
    **volante (Arcade Racer) no Saturn**, o "Analog Joystick" no SwanStation do PlayStation e nada no Dreamcast. Agora: Saturn
    3D Control Pad, PlayStation DualShock (no SwanStation e no PCSX ReARMed), Dreamcast o controle comum; teclado do C64 e do
    Amiga e mouse do PlayStation e do Saturn com o número certo. No GameCube/Wii e no PS2 do Android o ARENA não manda
    tipo nenhum: vale o controle padrão de cada núcleo (o controle do GameCube; o DualShock 2), o mesmo que o Rafael usou no
    Melee e no Bully no A12 (08/11).
  - **No celular, nenhum jogo passava de 2 jogadores** (nem o N64 de 4, nem o adaptador do Saturn, do PlayStation ou do Mega
    Drive): o mapa dos adaptadores procurava o núcleo pelo nome do Windows. Consertado.
  - No PC, a leitura dos adaptadores de rede morria com nome acentuado ("Conexão local") quando o ARENA roda com `-X utf8`.
  - **Deadly Alliance no A12: consertado (07/11, de madrugada).** Achado por eliminação, mesmo jogo, mesmo celular: o nível
    "mínimo" (em que o celular estava) punha o processador do PS2 (EE) a **50%**, e com ele o jogo fica para sempre no LOADING,
    mesmo rodando a 100%; no nível normal e no leve (60%) ele carrega. O 50% saiu da escada do EE (o mais lento agora é 60%). No
    mesmo teste, a mistura de cores "Minimum" e o "Disable Readbacks" do mínimo trocavam o logotipo e o texto dos menus por
    manchas: no PS2 do celular o mínimo economiza só pelo EE. Resultado: carrega e roda a 100% (60 quadros) no mínimo.
    O aviso "No space on memory card slot 2" é do PocketStation na entrada 2 (decisão de 24/10): basta apertar X uma vez.
  - **Dois toques na tela mostram o controle de toque** (pedido do Bully, 07/11): com um controle de verdade ligado, o RetroArch
    escondia os botões da tela e não havia como chegar ao SAIR. Remendo `android/retroarch/arena-toque.patch`.
  - **PS2 abrindo durante um giro de tela** (rotação automática ligada): uma vez em quatro, o PS2 abriu com o desenho em pé
    espremido na tela deitada. Girar o celular uma vez conserta na hora; girar com o jogo aberto funciona nos dois sentidos.

**O que falta**

- **Sentir a vibração com o T4** (controle de verdade, só você).
- **Saturn no Jogar Junto entre computador e celular: fechado como limitação (08/11).** O Beetle Saturn declara o estado
  "PLATFORM_DEPENDENT" (lido do próprio núcleo, com `retro_load_game` fora do RetroArch), e o RetroArch recusa a partida
  entre Windows x64 e Android arm64, como no Genesis Plus GX. Os núcleos Yabause, YabaSanshiro e Kronos declaram só
  "SINGLE_SESSION" e existem para Android arm64 no buildbot: seria o caminho (`core_netplay` do Saturn), mas trocaria
  também a partida entre computadores por um emulador menos compatível. Fica como melhoria futura, se o Rafael quiser.
- **Partida pelo cabo**: testada nos dois sentidos (o celular abriu o Super Nintendo e o computador entrou como jogador 2, ping
  14 ms). Falta só o Saturn.
- **APK e pacote do Windows novos e a página do release**: só depois do teste acima. **Feito:** release `v2026.11.09`
  (10/11), com os APKs e os dois zips.
- Da rodada anterior: 8 jogadores e Linux de verdade, `teste_matriz_consoles`, `teste_android`, modo de dados móveis, controles de
  verdade.
- **Pedidos antigos conferidos na revisão de todos os pedidos (07/11)**: o clarão do tema claro ao abrir o jogo (24/10) já
  estava resolvido (a856884: fundo preto na tela do jogo e abertura do Android 12 preta e sem ícone), e a turma do Donkey Kong com
  a Dixie e o bebê (21/10) já está no fundo animado. Faltam, e dependem do celular: **em pé e deitado do jeito que o aluno quiser,
  com a tela espelhada na TV** (Smart View/Miracast; 24/10) e o **Deadly Alliance lento no A12** (24/10; o PS2 pede mais do que o
  processador dele dá, então a meta é medir e achar o melhor ajuste, sem prometer velocidade cheia).

## Android com o mesmo cuidado do PC (08/11/2026, de manhã)

Pedido do Rafael: "a maioria tem celular do que pc, então merece um cuidado e carinho especial". O APK de teste 2026.11.08
foi aberto **console por console no Galaxy A12** (`ferramentas\afinar_no_celular.py`; bruto em
`docs\auditoria6\celular_SM_A125M.json`): um jogo de cada um dos 23 consoles com jogo no celular, quadros por segundo
pelo SurfaceFlinger, foto e saída pelo SAIR. Todos os que abriram saíram pelo SAIR.

| Console | Jogo | Quadros por segundo no A12 |
|---|---|---|
| NES, Super Nintendo, Mega Drive, Atari 2600, ColecoVision | Contra, 1997 New Year FD, Golden Axe, Combat, Slither | 60 (nenhum lento) |
| Neo Geo | Metal Slug X | 59,3 |
| PlayStation | CTR | **59,3** (depois do conserto abaixo) |
| PS2 | Black | 58 no Android (o número do Android engana no PS2: conferir pelo mostrador do emulador) |
| Saturn | Saturn Bomberman | **56** com o YabaSanshiro (era 21 com o Beetle Saturn) |
| Amiga, C64, 32X, Sega CD | Alien Breed, International Karate, Chaotix, Sonic CD | ~50 (provavelmente região europeia, 50 Hz; não conferido) |
| Nintendo 64 | Bomberman 64 | 48,8 |
| PocketStation | 15 Puzzle | 31,9 (provavelmente o ritmo do próprio aparelho; não conferido) |
| GameCube | F-Zero GX | 17 (limite do A12) |
| Fliperama | Killer Instinct | 13,6 (dos mais pesados do MAME; limite do A12) |
| Dreamcast | Armada | 11,5 com a BIOS original (limite do A12; falta medir com a BIOS imitada) |
| Wii | Mario Kart Wii | 1,4 e o Android acusou "não responde" (limite do A12) |
| PSP | Burnout Legends | abriu e saiu; a medida veio vazia (refazer com mais tempo de carga) |
| Java ME, PS3, Xbox 360 | — | não têm versão para Android (o recado agora diz isso) |

**Consertado nesta manhã** (commits e6c1088, 21c3a16, 271affd):
- **PS1 levava 31,9 s de tela preta** antes do primeiro quadro: o SwanStation carregava o disco inteiro na memória (bom no
  pen drive do PC, ruim no cartão SD de um celular de 4 GB). No Android ele lê direto do cartão: **2,5 s**, e o jogo a 59,3.
- **Saturn pelo YabaSanshiro no celular**: 21 → 56 quadros. Com o tipo de controle dele (o 261 do Beetle não existe nele e
  deixaria o jogador sem controle), o C e o Z no mesmo lugar do computador (troca pelo `.rmp` da partida) e o adaptador de 6.
- **"Voltar ao jogo"**: o jogo que ficava aberto atrás do ARENA travava a abertura de outro (achado ao vivo no A12).
- **Recado do console sem versão para Android** (Java ME, PS3, Xbox 360) em vez de "instale de novo".
- A medida do celular (`afinar_no_celular.py`) achava a camada errada e tocava o SAIR no lugar antigo.

**Falta, com o celular de volta**:
- Instalar o APK de teste novo (com o Saturn, o PS1 e o Voltar ao jogo) e conferir: a **proporção da imagem do Saturn** no
  YabaSanshiro (a foto pareceu esticada na largura), os **botões C e Z** na mão, o **Voltar ao jogo** (sair pelo botão de
  início e tocar em outro jogo) e o recado do Java ME.
- Medir de novo o PSP (com mais tempo de carga) e o Dreamcast com a BIOS imitada.
- No fim, **instalar o APK de produção** (o A12 ficou com o de teste).

## Rodada final de 08/11/2026 (PC, com o Rafael fora de casa e a tela bloqueada)

**110 de 120** na rodada inteira (09:53 às 13:00). As 10 falhas, uma por uma:

| Teste | Causa | Situação |
|---|---|---|
| `fuzz_rotas` | o celular cadastrado como amigo estava fora de casa: o sincronizar espera 8 s, o fuzz esperava 5 | prazo de 30 s (df057fd); **passou** |
| `teste_abaixo_do_original` | o terminal de testes é administrador: o Edge sem janela só subia depois que o Python saía; o Edge 156 abre a página de sincronização da conta antes da nossa | `--do-not-de-elevate` e o alvo `about:blank` (df057fd); **passou** |
| `teste_android_estresse` | começou 0,2 s depois do `emu kill` e pegou o emulador ainda desligando | espera o emulador sair da lista do adb (3c436ef); **passou** |
| `teste_matriz_consoles` (PocketStation) | a ponte sem acento acrescentava uma 2ª `system_directory`, e o RetroArch fica com a 1ª (com acento). Só no teste: no `/api/jogar` a ponte entra antes | a linha é trocada (3c436ef); abre, salva, carrega e fecha nos dois modos. A foto do modo modesto saiu branca 3 vezes na matriz, mas com a mesma configuração fora dela mostra o coração do 15 Puzzle (tela de 32×32 que pisca entre animações) |
| `teste_multitap_regra_de_ouro` | as mudanças de propósito de 07/11 (foto do save, tipo de porta lido dos núcleos, PicoDrive no netplay) nunca foram ensinadas ao teste | 8179eff; **254 casos iguais, passou** |
| `teste_partida_aparece` | oscilação de tempo do grito UDP | sozinho, **passou** inteiro |
| `teste_pasta_system_pelo_arena` | 2 fotos da janela pretas: **tela bloqueada** (o resto, 15 conferências, certo) | com a tela desbloqueada (08/11, 20h): **passou** |
| `teste_pokketsx_pelo_arena` | "fechou pela janela" aperta F10 na janela, e com a **tela bloqueada** nenhuma tecla chega | com a tela desbloqueada: **passou** inteiro, inclusive o F10 |
| `teste_orcamentos_modo_alvo` | 1b (abertura do servidor) 3,36 e 3,97 s no modo alvo, teto 2,3. Com a **tela bloqueada** o Windows não diz a placa da tela principal e o ARENA cai no registro: "NVIDIA GeForce 210, placa 2/5" em vez da Radeon do 5600G. Fora do modo alvo, a mesma abertura leva 1,6 a 2,3 s | com a tela desbloqueada estourou de novo (4,51 s): **não era a tela**. Causa achada e consertada (abaixo); agora **2,0 s, passou** |
| `teste_jogar_junto_pc_celular` | precisa do celular no cabo | com o celular de volta |

**Causa do 1b (consertada em 08/11):** com a rede liberada em Ajustes (o ARENA escuta em `0.0.0.0`), o `HTTPServer` do
Python pergunta o nome do computador pela rede (`socket.getfqdn`) ao abrir a porta: **1,27 s** em toda abertura no PC do
Rafael (numa rede de escola com DNS lento, pode ser mais). Em 22/10 a rede estava fechada, por isso não aparecia. O
`Servidor` agora pula essa pergunta, como o `controle_remoto.py` já fazia: a porta abre em 0,43 s em vez de 1,3 a 1,7 s,
e no modo alvo o 1b caiu de 4,51 para 2,0 s e o 1a de 3,33 para 1,37 s.

**No celular, 08/11 à noite (APK de teste com o conserto acima):**
- **Saturn:** 56,1 quadros por segundo no Saturn Bomberman. A imagem "esticada" não é defeito: o `config.json` do A12
  está com o Formato da imagem em **"esticar"** (até a borda, em todo console) desde antes das 8h34. No "automático" o
  Saturn para em 16:9.
- **PSP: caía 2 a 3 s depois de abrir, toda vez** (não era tempo de carga: o registro de queda do Android mostra ponteiro
  nulo dentro do PPSSPP, igual em OpenGL e em Vulkan). Separado opção por opção pelo ajuste fino por emulador: a culpada
  é o **"pular efeitos de buffer"** (`ppsspp_skip_buffer_effects`), que os níveis abaixo do original ligam. Com ela
  desligada o Burnout Legends chega à tela de título. Consertado só no Android (`graficos.json → no_android`); no
  Windows o mesmo jogo abre com ela ligada (`teste_abaixo_do_original`). A pasta de apoio do PPSSPP
  (`system/PPSSPP`) também foi testada e não muda nada.
- **Dreamcast com a BIOS imitada** (o registro diz "using reios"): 8,1 quadros no Armada (11,5 com a original; limite
  do A12). O "Invalid value" do `reicast_texupscale` no celular é inofensivo: o Flycast do Android não tem essa opção
  (recusa também a vizinha, que o ARENA nem manda). Conferindo isso (09/11), achei o degrau da nota 1 mandando `"off"`,
  que o Flycast do PC não aceita (só `1` = desligado, `2`, `4`, `6`): trocado por `"1"`, com teste.
- **Botão de início do aparelho com um jogo aberto: o servidor do ARENA caía e o Voltar ao jogo não achava o jogo**
  (o aluno ficava preso: o ARENA recusava outro jogo e o botão dizia "não consegui trazer o jogo de volta"). Causa: a
  tela do jogo e a do ARENA tinham a mesma afinidade de tarefa, e o Android 12 só mostra uma tarefa por afinidade:
  esconde a outra e, no botão de início, a destrói (o `onTaskRemoved` do serviço encerrava o servidor). Consertado com
  afinidade própria para a tela do jogo e o serviço sem fechar o servidor com jogo aberto (c5c39ff). No A12, do zero:
  Contra → início → ARENA → Voltar ao jogo → SAIR → Golden Axe → SAIR, os 10 passos certos.
- **Dreamcast sem botões de toque no celular (achado e consertado em 09/11):** em OpenGL ES, o Flycast deixava o
  controle de toque do RetroArch em quadrados escuros (deitado) ou sumido (em pé): quem não tem controle não jogava nem
  saía. Em Vulkan os botões aparecem, na mesma velocidade (Armada 9,7 contra 9,3; Capcom vs. SNK 2, 30 nos dois).
  Agora o Dreamcast pede Vulkan no Android (`consoles.json → motor_no_android`), só com Vulkan no aparelho e o motor no
  automático. Conferido no A12 pelo caminho normal ("vulkan driver forced" no registro, botões na foto).
- **Recado do Java ME:** "Este console não tem versão para Android: abra o jogo no computador, com a mesma pasta do
  ARENA." Certo.
- **Jogar Junto entre PC e celular, Wi-Fi da casa:** o celular hospedando, o PC entrou em 17,1 s; o PC hospedando, o
  celular entrou em 5,1 s. Nos dois, 45 s de partida sem cair. (O Super Bomberman 4 foi copiado ao celular só para o
  teste e apagado depois.)
- **Botões C e Z do Saturn:** no desenho de toque estão no lugar do computador (foto da medição); conferir com o
  controle de verdade na mão fica com o Rafael, sem travar a versão.

**Achado de 08/11, consertado em 09/11:** com a tela bloqueada (ou sem monitor), `hardware.placa_da_tela_principal()`
volta vazio e o ARENA usava a placa do registro, que guarda placas que já saíram do computador (a GeForce 210 no lugar da
Radeon). Agora vem antes `hardware.placas_presentes()`: as placas que estão na máquina, pela SetupAPI do Windows
(`DIGCF_PRESENT`), em 24 ms e sem WMI; ela só roda quando a tela principal não responde. Com teste.

## Lançamento 2026.11.09 (09 e 10/11/2026, de madrugada, com o Rafael dormindo)

**Publicado:** release novo `v2026.11.09` (Latest), completo e limpo, com cada arquivo explicado por aparelho
(`docs/RELEASE-2026.11.09.md`). Os releases antigos ficaram como estavam.

**Rodada final de 09 e 10/11: 113 de 120** de primeira; os 7 que falharam, repetidos um de cada vez, passaram:

| Teste | Causa | Situação |
|---|---|---|
| `teste_capas_todos_os_consoles` | a internet caiu no meio de um download (IncompleteRead) | **passou** |
| `teste_chromebook` | o teste leva 10 min e o tempo-limite da rodada era 15 min com a máquina carregada | sozinho, 32 de 32 em 629 s: **passou** |
| `teste_matriz_consoles` | a imagem do PocketStation no modo modesto (mesmo achado de 08/11) | só o PocketStation: **passou** |
| `servidor/tests/run.py` | 1 conexão cortada pelo Windows (WinError 10053) no meio da sequência longa | sozinho, 4 vezes seguidas: **1226 OK**. Ambiental; não achei o teste culpado com `-v` |
| `teste_orcamentos_modo_alvo` | 1b em 2,35 s (teto 2,3) | repetido 4 vezes: 1,51 / 2,77 / 2,58 / **1,07 s**. **Fica em observação** (abaixo) |
| `teste_android` | a rodada usou o APK de teste antigo (2026.10.22) | com o APK de teste 2026.11.09 no emulador: **passou, 0 falhas** (duas vezes, antes e depois do conserto do caminho) |
| `teste_jogar_junto_pc_celular` | o A12 estava com o APK de produção, que não deixa o teste conduzir a tela | com o APK de teste no A12: o PC entrou em 19,1 s, o celular em 5,1 s: **passou** |

**Achado e consertado antes de publicar (ca5d604):** o `libretroarch-activity.so` que o ARENA compila para o APK
guardava o caminho da pasta de quem montou, com o nome do usuário do Windows (`C:/Users/<usuário>/AppData/...`, pelo
`__FILE__` dos avisos do RetroArch). Estava em todos os APKs até a 2026.11.08. Agora o `ndk-build` recebe
`-ffile-prefix-map`, e a conferência da biblioteca reprova o APK em que o caminho sobrar. A conferência do pacote
(zips e APKs) procurou também e-mail, token, BIOS, banco, `config.json` e saves: nada.

**Em observação: o 1b no modo alvo oscila (1,07 a 2,77 s).** Nesta noite um `svchost` do Windows (os serviços
DcomLaunch, PlugPlay e Power, juntos no mesmo processo) gastava **~95% de um núcleo o tempo todo**, mesmo sem nenhum
teste rodando; dentro da caixa de 2 processadores do modo alvo isso pesa. Próximo passo: medir de novo com esse serviço
calmo (depois de reiniciar o PC) antes de mexer no ARENA.

**O que vem depois (fila combinada com o Rafael em 10/11, na ordem):**
1. ~~Item 9~~ **feito em 10/11** (veja os limites conhecidos): o cartão de memória do convidado do PS1 no Jogar Junto nasce em branco (reproduzir antes com 2 RetroArch
   no PC; pode ser do próprio netplay, que usa o estado de quem hospeda).
2. ~~Item 7~~ **feito em 10/11, falta o teste na sala com 5 controles** (veja os limites conhecidos): mais de 4 controles do Xbox (o XInput do Windows só conta 4; plano: SDL2 automático com tradução de
   botões). Cinco controles de verdade só na sala.
3. Revisar PENDÊNCIAS e guias atrás de algo prometido e não feito.
4. ~~Pesquisa~~ **feita em 10/11** (`docs\PESQUISA-PROJETOS-PARECIDOS.md`; o LEIA em cada pasta de console já entrou no montador, `ab9eefb`; as outras ideias abaixo, em "Depende do Rafael" e no próprio documento). Pesquisa dos melhores projetos parecidos (Lemuroid, Daijishō, ES-DE, Pegasus, RetroBat, Batocera, RetroArch) atrás
   de recursos e otimizações para todo celular (meta realista: Android 7 ou mais novo, 64 bits, dos últimos 7 a 8 anos).
5. ~~Auditoria da tela~~ **feita em 10/11** (defeitos consertados em `78a469e`; a proposta de layout em `docs\PROPOSTA-LAYOUT.md`, à espera das suas respostas abaixo). Auditoria da tela e layout novo (abas, distribuição), o mesmo no PC, no celular e no Chromebook.

## Depende do Rafael

- **Layout novo (`docs\PROPOSTA-LAYOUT.md`, 10/11):** (1) as 5 abas (Jogos, Amigos, Placar, Biblioteca, Ajustes) no
  lugar dos 8 botões do topo, ou manter como está? (2) no celular, abas embaixo ou em cima? (3) o tema claro/escuro
  dentro do perfil, em Ajustes ou no topo? Com as respostas, cabe numa sessão (tela, guias, testes e fotos).

- **Continuar de onde parou (ideia do Lemuroid, pesquisa de 10/11):** o jogo grava o estado sozinho ao sair e volta
  nele ao abrir (`savestate_auto_save` e `savestate_auto_load`; o estado automático fica num espaço próprio e não
  apaga os 10 do F2). Bom no celular do aluno; no computador dividido entre turmas, o aluno da tarde abriria no ponto
  do aluno da manhã. Minha proposta: ligado por padrão só no Android, com a chave em Ajustes nos dois. **Você decide.**
- **Modo de desempenho contínuo do Android:** ligar só depois de medir 30 minutos no A12 com e sem (teste longo, numa
  madrugada com o celular na tomada).

- **Acessórios (24/10/2026), o que só você faz:**
  1. ~~Olhar no celular a telinha do VMU num jogo de Dreamcast~~ **Conferido por foto em 09/11** (Capcom vs. SNK 2:
     o logotipo do jogo na telinha, no canto de baixo à direita, em 3x, sem cobrir os botões). A BIOS do PS2 com
     "PocketStation/1" já tinha sido conferida por foto.
  2. ~~Decidir o cartão do PS2~~ **Decidido em 24/10:** entrada 1 = cartão de 64 MB, entrada 2 = PocketStation (como no PC).
  3. ~~Autorizar o DreamPotato e o PokketSX~~ **Autorizado em 24/10** (a BIOS do VMU da Sega que vem no zip do DreamPotato
     fica só na máquina dele, em `emuladores\DreamPotato`, nunca no pacote).
  4. Testar com **controle de verdade** o Saturn e o PS1 no SwanStation (o tipo 517 que o ARENA manda pode ser
     "Arcade Racer" e "Analog Joystick").
  5. ~~Jogos de PocketStation~~ **Feito:** os 110 do conjunto TOSEC que você pôs no cartão SD foram descompactados e
     posicionados no PC e no celular (`jogos\pessoais\PocketStation`).
  6. Rede do Dreamcast (adaptador de banda larga): fica desligada; ligar só com a rede liberada pelo professor.

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
- **O seu ARENA está com o "Som só para o jogo" ligado** (o som exclusivo,
  WASAPI, em Ajustes → Avançado → Som; no `dados\config.json`, grupo
  `avancado`). Com o seu fone JBL Quantum, é o que deixa o Super Nintendo
  a 52 quadros, e não 60 (o teste do modo alvo de 22/10 mediu 52,4 com o
  som e 60,0 sem a sincronia pelo som). Desde 16/10 nenhum perfil liga essa
  opção, e a tela explica o efeito. Desligar é com você: é configuração
  sua (só a tela grava nesse grupo), e dado do usuário só muda com a sua
  autorização.
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
  mão. **Feito em 10/11/2026 (item 7), falta o teste na sala:** com os 4
  lugares do XInput cheios e mais de 4 controles do tipo Xbox na lista do
  Windows (Raw Input, "IG_" no nome), o jogo do RetroArch abre com
  `input_joypad_driver = sdl2` e os botões definidos na tela traduzidos
  (`controles.trocar_para_o_sdl2`; a tabela é conferida no teste contra os
  perfis `xinput` e `sdl2` do próprio RetroArch). Com até 4, nada muda.
  Conferido aqui: o `retroarch.exe` do ARENA abre com o SDL2 ("Found joypad
  driver: sdl2"). **Para o Rafael, na sala:** 5 controles de Xbox num
  jogo de 5 (ex.: um de PS1 com o adaptador), e ver se cada um mexe o seu
  jogador e se os botões trocados na tela continuam certos.
- Emuladores de fora no Jogar Junto: o PCSX2 não tem partida em rede (os
  jogos com System Link o ARENA já configura, e eles se acham na rede
  local); o NetPlay do Dolphin não abre pela linha de comando; o PS3 tem o
  RPCN.
- Na partida a dois de PS1 (PCSX ReARMed), o memory card do convidado
  nasce em branco e não sincroniza. **Resolvido em 10/11/2026 (item 9):** o
  convidado sempre recebeu o cartão de quem hospeda (o RetroArch manda na
  entrada e guarda a cópia em `saves\<núcleo>\.netplay`, sem tocar no
  cartão do convidado). O branco vinha de quem hospeda: a partida lia o
  cartão do PCSX ReARMed, e o do dia a dia é o do SwanStation. Agora quem
  hospeda joga com o cartão mais novo dos dois, no lugar dele
  (`graficos.pasta_do_cartao_do_ps1_na_partida`). Conferido com dois
  RetroArch neste PC; o cartão 2 da partida (`pcsx-card2.mcd`) passa a
  ficar na pasta do SwanStation.
- A partida pela internet (repasse) entre operadoras diferentes ainda não
  foi validada.
- A descoberta de colegas não tem senha (revisão de segurança de 16/10/2026):
  quem está na rede vê o código de todos e pode anunciar o de outro (o
  inteiro, com o colega desligado, ou um que começa igual, e aí o código
  curto fica com dois donos). O ARENA não escolhe no chute quando há dois, e
  quem está no ar não perde o lugar; o endereço digitado na mão continua
  sendo o jeito seguro de adicionar um amigo.
