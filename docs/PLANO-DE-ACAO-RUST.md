# Plano de ação: Rust no ARENA e desempenho do servidor (13/11/2026)

Junta os dois guias de "arena-web" em Rust que o Rafael trouxe em 13/11 com o plano anterior (medir antes de trocar).
Nenhum dos guias foi aplicado: o `arena-web` não existe no repositório.

**Mensagens de 13/11, todas revistas (nenhuma fica para trás):**
1. Compilar o `arena-web` no Termux com o NDK → problemas 5 e 10; o certo está na Fase 3.
2. Converter a camada web para Rust com o Claude CLI → problemas 1 a 9; vira as Fases 1 a 4.
3. Sincronizar com as releases e compilar no Termux e no Chromebook → seção do terceiro guia; regra da paridade.
4. Empacotar como `libarena_web.so` no APK → seção do quarto e quinto guias (o ARENA já faz isso com o Python).
5. Prompt para o Claude CLI ligar o `libarena_web.so` no app → idem.
6. "O que for para o PC deve ir para o celular e todas as versões" → seção de paridade.
7. Workflow `release-arena.yml` com chave nova no GitHub → NÃO salvo (seção do sexto guia).
8. O mesmo workflow com o alvo `aarch64-unknown-linux-musl` e o `build_arena_web.sh` por arquitetura → NÃO salvo
   (mesmos problemas do 7); a ideia boa virou o item "Linux ARM64" da paridade.
9. `install.sh` com `curl | bash` → NÃO criado; a ideia boa (limite da API do GitHub na rede da escola) virou uma
   melhoria do `recomps.py` (seção do nono guia).
10. Serviço do systemd no Crostini → NÃO criado; o que ele quer (reabrir sozinho, atalho no menu) já existe.
11. Serviço em primeiro plano `specialUse` no Android → já está feito; acrescentei o teste dos "processos fantasmas"
    no A12.
12. Prompt para o Claude CLI criar o `ArenaWebService` → já está feito; a ideia nova é o botão "Fechar o ARENA" no
    aviso da barra (seção do 12º guia).
13. Abrir o servidor sozinho ao ligar o celular ou a TV Box (o guia e o prompt dele) → NÃO feito; a ideia que pode
    valer é o "modo TV Box" (ARENA como tela inicial), só se a escola tiver TV Box.
14. ARENA como tela inicial da TV Box → vira o "modo TV Box", desligado por padrão (seção do 14º guia).
15. Tela cheia de verdade na TV Box → quase tudo já existe; três ajustes pequenos (seção do 15º guia).
16. Prompt para o Claude CLI aplicar o 15º guia → mesmo destino do 15. Não roda como está: pede AndroidX e Gradle
    (o ARENA não tem), liga o entalhe da câmera sem conferir e zera as margens da tela sem conferir (risco de botão
    embaixo da câmera no A12).
17. Controle e foco na tela do Android → o que existe e um teste a fazer no A12 (seção do 17º guia).
18. Ponte `window.ArenaAndroid` para abrir emuladores de fora → NÃO feito; a ponte já existe e o emulador roda dentro
    do app (seção do 18º guia).
19. Acesso a todos os arquivos → já existe; dois ajustes: TV Box sem a tela do app e Android 10 (seção do 19º guia).
20. PPSSPP, DuckStation e Mupen64Plus FZ de fora → NÃO feito; os três consoles já rodam dentro do app.
21. Cartão SD e pen drive no Android → já acha; falta perceber quando entra ou sai com o ARENA aberto (seção do 21º).
22. Indexador em Rust com cache → o Rust não entra; achou o defeito dos arquivos `._` do Mac, corrigido na 2026.11.14.
23. Aviso em tempo real pela WebSocket → a peça já existe (`controle_remoto.py`); usar só se o 21º precisar.
24. Esconder consoles sem emulador → NÃO feito; o ARENA mostra apagado com o motivo (seção do 24º guia).
25. Prompt único que junta os guias 1 a 24 → não roda como está (cada parte já tem destino acima). O que entra de
    verdade, em ordem: (a) na 2026.11.14, a correção dos `._` do Mac; (b) depois da release, a Fase 1 (medir), a
    paridade (matriz, Linux ARM64, Chromebook com APK, navegador), o cache e a reserva da API do GitHub no
    `recomps.py`, o botão "Fechar o ARENA" no aviso, o modo TV Box (alias de tela inicial desligado), os três ajustes
    da tela cheia, o foco do controle ao voltar do jogo, o acesso a arquivos em TV Box e no Android 10, o pen drive
    que entra ou sai, e o teste dos processos fantasmas no A12.
26. Roteiro de testes por `adb` na TV Box → testa peças que não existem (`libarena_web.so`, porta 8080, `BootReceiver`,
    `MediaMountReceiver`); não há TV Box aqui (o aparelho é o A12; TV só no emulador de Android TV). O que vale vira
    conferência nova da `ferramentas\auditoria_celular.py`, que hoje não olha nada disso: (a) o `ArenaServico` em
    primeiro plano com o tipo `specialUse` (`dumpsys activity services`), (b) o estado do acesso a todos os arquivos
    (`appops get ... MANAGE_EXTERNAL_STORAGE`, só leitura, nunca o `set`), e (c) com o modo TV Box, quem responde à
    tela inicial (`cmd package resolve-activity ... HOME`). O aviso `MEDIA_MOUNTED` não se simula pelo `adb` (é aviso
    protegido do sistema) [Provável]: o teste do pen drive é com o pen drive de verdade no OTG.
27. `.gitignore`, `git add .`, push no main e tag `2026.11.13` → só o `.gitignore` aproveitado: entraram `*.keystore`,
    `*.jks` e `*.p12` (a chave já fica fora do git; é proteção contra descuido). NÃO feito: `git add .` (proibido: há
    dezenas de arquivos soltos na pasta, alguns com nome de extrator de senha, que não podem ir ao repositório
    público), `git push origin main` (o ARENA publica pelo ramo de trabalho com a conferência de ancestral), a tag
    `2026.11.13` (a `v2026.11.13` já existe) e apagar e recriar tag no GitHub (quem já baixou ficaria com outro
    arquivo sob o mesmo nome). A release 2026.11.14 sai pelo processo do projeto.
28. `.github/release.yml` e etiquetas no GitHub → NÃO feito. O próprio guia diz que ele só agrupa pull requests, e o
    ARENA não usa pull requests (os commits vão direto, pelo ramo de trabalho): a nota sairia vazia. A nota do ARENA
    é escrita à mão (`docs\RELEASE-*.md`), em português, explicando qual arquivo baixar em cada aparelho e terminando
    com as contribuições dos alunos; a automática do GitHub é uma lista de títulos em inglês. Também cita a tag
    `2026.11.08` (as tags do ARENA começam com `v`).
29. `.github/labeler.yml` e o workflow de etiquetas automáticas → NÃO feito: só etiqueta pull request (o ARENA não
    usa) e serve ao `release.yml` do item 28, que não entrou. Reabrir só se os alunos passarem a mandar contribuições
    por pull request; aí o `pull_request_target` do guia está certo (não roda o código do pull request).
30. Capas locais servidas pelo Rust → o ARENA já faz em Python: `indexador.capas_do_jogo` (linhas 577 a 640) acha a
    capa com o mesmo nome do jogo, na subpasta `capas`, a genérica (`cover`, `folder`...) quando o jogo está sozinho na
    pasta e as miniaturas do RetroArch; a rota `/api/capa` só entrega o que a `capa_permitida` aprova (protege contra
    `..` no caminho), com cache no navegador e miniaturas de 280 e 480; a tela carrega só a capa perto da tela
    (`loading="lazy"`, `decoding="async"`, `launcher\app.js` linhas 681 a 726). O código de tela do guia põe o nome do
    jogo direto no HTML sem escapar (um nome com `<` quebraria a tela ou rodaria código).
    **O que vale (pequeno, depois da release):** reconhecer também as pastas e os nomes de capa do EmulationStation,
    do Batocera e do Skyscraper, comuns em pen drive de quem já tinha outro emulador: subpastas `covers`, `boxart`,
    `images`, `media/boxart`, `media/images` e o sufixo `-image` (`Mario-image.png`). Conferir antes se a
    `capa_permitida` aceita essas pastas; teste no `run.py` com cada formato.
31. `gamelist.xml` (EmulationStation, RetroBat, Batocera, Skraper) → o ARENA **não lê** hoje (conferido: nenhuma
    menção em `servidor\`). Vale fazer, em Python, junto com o item 30, depois da release:
    - no `indexador`, ler uma vez por pasta o `gamelist.xml` com o `xml.etree.ElementTree` da biblioteca padrão (o
      Python 3.13 traz o expat novo, que já barra a "bomba de entidades" [Provável]; mesmo assim, recusar arquivo
      maior que alguns MB e não seguir `<!ENTITY>` externa);
    - por jogo (`<path>`, com `./` e `\` do Windows normalizados): o `<name>` como título quando existir, a `<desc>`
      como sinopse e a `<image>` como capa, que passa pela mesma `capa_permitida` (nunca um caminho fora da pasta);
    - na tela, a sinopse no painel do jogo com `textContent` (nunca HTML);
    - testes no `run.py`: arquivo com CDATA, com `&amp;`, com caminho do Windows, com imagem fora da pasta (recusada)
      e com XML quebrado (ignorado, a pasta continua indexada como hoje).
32. Favoritos e busca no Rust → já existem: os favoritos ficam na configuração do aluno (`favoritos`, até 200,
    `arena.py` linhas 1394 e 1589, consertados na 2026.11.13.2 e levados junto quando o jogo muda de nome), com a
    estrela ☆ em cada jogo (`alternarFavorito`, `launcher\app.js` linha 1827) e o filtro Favoritos (linha 561); a busca
    roda na própria tela, sem pedir ao servidor, com o texto sem acento já preparado (linhas 556 a 582), então não há
    resposta lenta para cancelar. **O que vale (depois da release):** (a) quando o `gamelist.xml` (item 31) trouxer a
    sinopse, a busca procurar também nela; (b) conferir se dá para favoritar pelo controle (botão Y, ou tecla F) no
    jogo em foco; se não der, acrescentar, com teste.
33. Armbian (Linux ARM64) em TV Box pelo cartão microSD → não é código do ARENA, é preparar o aparelho; mas ligou
    o item "Linux ARM64" da paridade: hoje o `ARENA.sh` recusa `aarch64`, então nessas TV Box com Armbian o ARENA de
    PC não abre (só a versão do navegador). Se a escola tiver essas TV Box, o item Linux ARM64 sobe para o primeiro
    da fila depois da release (Python 3.13 aarch64, RetroArch e núcleos aarch64, `ARENA.sh` escolhendo pela
    `uname -m`, teste pelo QEMU no WSL e depois na TV Box). Cuidados do guia que ficam como aviso, não como passo
    automático: o `dd` apaga o disco errado se a letra estiver trocada (preferir o Rufus ou o balenaEtcher, que mostram
    o nome do cartão); trocar a senha `1234` no primeiro acesso; o `install.sh` e o serviço `arena-web` do guia não
    existem (itens 9 e 10); o Tailscale pede conta e é opcional. A aceleração de vídeo dessas placas no Linux (Mali,
    pelo Panfrost) varia por modelo: medir antes de prometer console 3D [Palpite].

## Por que os guias não entram como estão

| # | Problema | Nível |
|---|---|---|
| 1 | Pedem a pasta `web/`, que não existe (a tela fica em `launcher/`), e a versão 2026.11.08, já velha | Certo |
| 2 | "Converter todas as rotas" com um prompt: são 118 rotas, o `arena.py` tem 9.620 linhas e há 62 módulos em `servidor\`. O servidor não é só HTTP: abre o RetroArch e os emuladores, mexe na prioridade pelo `ctypes`, usa o banco SQLite, acha colegas pela rede (UDP), atende o controle pelo celular e grava tudo de forma atômica. Seriam duas bases de código, e os 1.512 testes e a rodada final só conferem a de Python | Certo (números contados) |
| 3 | O prompt B manda o `arena.py` abrir o binário "no lugar do servidor em Python", mas o servidor em Python é o próprio `arena.py`: as rotas chamam funções Python que o binário não tem | Certo |
| 4 | Esquece o Windows, que é o sistema da sala: só compila para Linux (musl) e Android | Certo |
| 5 | No PC com Windows, `aarch64-linux-android` precisa do linker do NDK e o musl precisa de um linker próprio; o script não configura nenhum dos dois e para na hora de ligar | Provável |
| 6 | O APK já roda o mesmo servidor em Python (Python 3.13 do Android): é isso que garante a paridade com uma base só. Um binário em `bin/` não pode ser executado pelo app (Android 10 em diante); teria de ir como `.so` dentro do APK | Certo |
| 7 | O `rust-embed` põe a tela dentro do binário: some a edição da tela no pen drive, e cada mudança exige recompilar | Certo |
| 8 | O ganho seria pequeno: o servidor em Python usa 42 MB parado e quase 0% do processador (medido em 11/11); um servidor Axum talvez use de 5 a 15 MB. São uns 30 MB num PC de 7,7 GB. O que pesava era o navegador, já cortado de 629 para 238 MB | Medido / Palpite (Axum) |
| 9 | Quebra as regras do projeto: Python puro e código legível por aluno | Certo |
| 10 | O `rustup` não roda no Termux (o guia anterior); lá o Rust vem de `pkg install rust`, e compilar no A12 (4 GB) é lento | Certo |

## O plano (cada fase só começa se a anterior passar)

**Fase 0 (agora):** terminar a versão 2026.11.14: rodada final, APKs de produção conferidos no A12, pacote dos alunos e
release.

**Fase 1, medir (uma sessão, sem mudar código; aprovada pelo Rafael em 13/11, logo depois da release):**
- A12: abertura a frio e memória do APK de produção (`auditoria_celular`), separando o servidor Python do resto do app.
- PC: memória e processador do servidor parado, abrindo jogo e com o catálogo grande, no perfil do Celeron N5100
  (`docs\MAQUINA-ALVO.md`).
- Resultado em `docs\DESEMPENHO-SERVIDOR.md`.
- **Portão** (proposta): só seguir se o servidor Python for o gargalo medido, por exemplo mais de 150 MB, mais de
  2 s da abertura por conta dele, ou mais de 1% do processador parado.

**Fase 2, se o portão abrir:** otimizar o Python primeiro (importar módulo só quando for usado, cache, menos trabalho na
abertura). É mais barato e mantém uma base só. Medir de novo.

**Fase 3, só se ainda faltar:** prova de conceito em Rust, num ramo à parte, só do trecho que a medição apontar (nunca o
servidor inteiro). Condições:
- Windows primeiro (ferramentas gratuitas: `x86_64-pc-windows-gnu` ou as Build Tools do Visual Studio), depois Linux, e
  Android como `.so`, compilado no PC com o NDK oficial e o `cargo-ndk`;
- todas as versões no mesmo dia (Windows, Linux x86_64 e arm64, Android arm64 e x86_64), compiladas no GitHub Actions
  como os núcleos já são, nunca no Termux nem no Chromebook do aluno (o aluno não compila nada);
- o Python continua como reserva automática;
- a tela continua em arquivos (`launcher\`);
- a rodada final passa sem nenhuma regressão;
- medido no Celeron N5100 e no A12.

**Fase 4:** decisão registrada em `docs\replica\architecture.md`, com os números.

## O terceiro guia (13/11, "sincronizar com as releases e compilar no Termux e no Chromebook")

Repete os problemas 1 a 10 e acrescenta:
- cita as releases 2026.10.22, 10.26 e 11.08, mas depois delas vieram a 11.10, a 11.11, a 11.12, a 11.13 e a 11.13.2;
- o `find . -maxdepth 3` lista também `jogos\`, `retroarch\` e as BIOS: milhares de linhas sem uso;
- "menos de 5 MB de memória" não foi medido (palpite do guia);
- compila no Termux e no Chromebook: o binário do Termux serve só ao Termux do Rafael (o aluno usa o APK, não o
  Termux), e o Chromebook da escola não tem Linux para compilar;
- põe o binário em `bin/` no repositório público, sem passar pelo `SINCRONIZAR.bat`.

O que ele tem de certo vira regra deste plano: **o que entra no PC entra no celular e em todas as versões**. Hoje isso
já vale por construção, porque o mesmo servidor Python roda no Windows, no Linux, no Android e no Chromebook com o APK.

## O quarto e o quinto guias (13/11, "rodar o arena-web pelo APK como libarena_web.so")

**A técnica está certa e o ARENA já a usa desde o primeiro APK com servidor:** o lançador do Python vai no APK como
`lib/<abi>/libarenapython.so` (`android/python/lancador.c`, montado por `ferramentas\python_android.py`), e o
`ArenaServico.java` o executa da `nativeLibraryDir` com o `ProcessBuilder`, num serviço em primeiro plano. A
`auditoria_celular` confere o `extractNativeLibs`. O que os guias propõem de diferente:

| Proposta | Situação no ARENA |
|---|---|
| Editar `build.gradle` e `useLegacyPackaging` | Não há Gradle: o `montar_android.py` desmonta o APK do RetroArch com o apktool, acrescenta o ARENA e remonta. A extração das bibliotecas já é conferida pela `auditoria_celular` |
| `jniLibs/arm64-v8a/libarena_web.so` | Mesmo caminho do `libarenapython.so`; só faria sentido na Fase 3, e para as duas ABIs (arm64 e x86_64), nunca só arm64 |
| Classe `ArenaWebRunner` (Kotlin) | Já existe em Java: `ArenaServico.java` (ciclo de vida, reabertura, parada) |
| Conferir se o servidor respondeu antes de mostrar a tela | Já existe: a tela só fala com a porta depois do aviso `pronto` do servidor, e há a tela de reserva quando ele não abre |
| Porta 8080 e variáveis `ARENA_PORT` / `ARENA_DATA_DIR` | O ARENA usa a 8777 em todo sistema; mudar quebraria a paridade e os testes |
| "Substituir a chamada legada do servidor Python" | Seria tirar do celular o mesmo servidor do PC: contra a regra da paridade. Só na Fase 3, com o Python como reserva automática |
| `./gradlew assembleDebug` | O APK é montado e assinado pelo `montar_android.py` (produção e `--teste`) |

Nada a fazer agora: entra na Fase 3 só se a medição pedir.

## O sexto guia (13/11, workflow `release-arena.yml` com chave nova no GitHub): NÃO salvo

| Problema | Por quê | Nível |
|---|---|---|
| Chave de assinatura nova | O Android só instala por cima um APK com a mesma chave. Com outra, o aluno teria de desinstalar o ARENA e perderia jogos, saves e recordes. A chave do ARENA já existe, fora do git, em `%LOCALAPPDATA%\ARENA-android\` | Certo |
| Chave e senha no GitHub, senha digitada no comando | A senha fica no histórico do terminal, e a chave sai do PC. Contra a regra: senha e chave nunca saem do PC nem vão para arquivo | Certo |
| Dados no certificado | O `-dname` põe cidade, "SEDUC-SP" e nome num certificado público, que qualquer um lê no APK | Certo |
| Dispara em toda tag `v*` | O `gh release create v2026.11.14` cria a tag `v2026.11.14`: o workflow rodaria em toda release, falharia (não há `arena-web` nem Gradle) e mexeria na release publicada | Certo |
| `git push origin main` e `git tag 2026.11.13` | O ARENA publica pelo ramo de trabalho com a conferência de ancestral, e a tag `v2026.11.13` já existe | Certo |
| Só arm64 e só Linux | Sem Windows e sem o APK x86_64: contra a paridade | Certo |
| Ações de terceiros pela versão, não pelo SHA | Quem controla a ação muda o código sem aviso (risco de cadeia de suprimentos) | Provável |

O que fica: se a Fase 3 acontecer, a compilação vai para o GitHub Actions como a do `nucleo-ps2-android.yml` (só
compila e guarda o `.so`); quem monta, assina e publica continua sendo o PC do Rafael, com a chave que já existe.

## Paridade: o que ainda falta em alguma versão (`docs\PARIDADE.md`)

- **Atualizar a matriz:** foi gerada em 24/10 (fala em 86 rotas; hoje são 118). Rodar de novo o
  `ferramentas\matriz_de_paridade.py` depois da release.
- **Android x86_64 (Chromebook com o APK):** sem PS2 (o ARMSX2 é só arm64). Conferir se a nota "falta compilar a
  biblioteca do RetroArch para x86_64" ainda vale e o que dá para fechar.
- **Navegador (Chromebook sem instalar):** 33 consoles a menos, limitados pelos núcleos que existem para o RetroArch do
  navegador. Conferir se saiu núcleo novo.
- **Linux ARM64 (Chromebook ARM com Linux/Crostini, Raspberry Pi 4 e 5)** (achado pelo sétimo guia): hoje o
  `ARENA.sh` recusa o que não é x86_64 e manda para a versão do navegador (33 consoles a menos). O que falta não é o
  servidor (o Python roda em ARM), e sim três peças: o Python 3.13 embutido para aarch64 (o python-build-standalone
  publica essa versão), o RetroArch do Linux aarch64 e os núcleos aarch64. Caminho sem Rust: o `preparar_linux.py`
  baixar as três por arquitetura e o `ARENA.sh` escolher pela `uname -m`; teste sem aparelho ARM pelo QEMU no WSL
  (lento, mas abre). Primeiro conferir se o RetroArch e os núcleos aarch64 existem para baixar (não verificado).
  Lembrete: no Chromebook ARM com a Play Store, o APK arm64 já roda hoje (se a escola deixar instalar).
- O que é só do Windows (Lossless, MFG, patch de 60 do PS2 no PCSX2) já tem irmão no Android quando é possível (painel
  "Este celular", PS2 a 60 no ARMSX2); o resto depende de programa que só existe no Windows.

## O nono guia (13/11, `install.sh` com `curl | bash`): NÃO criado

- Baixaria o `arena-web-linux-*`, que não existe nas releases, e mesmo que existisse instalaria só o servidor web, sem
  RetroArch, núcleos nem tela: o ARENA não abriria.
- O ARENA não se instala: roda da pasta ou do pen drive. Um binário em `~/.local/bin` (ou em `/usr/local/bin` com
  `sudo`) vai contra "sem instalar" e "sem administrador".
- `curl ... | bash` ensina o aluno a rodar código da internet sem ler; e a conferência do cabeçalho ELF não garante
  que o arquivo é o certo (para isso existe o `SHA256.txt` de cada release).

**A ideia boa que fica (implementar depois da release):** o limite de 60 consultas por hora da API do GitHub vale por
**endereço público**, e numa escola todos os computadores saem pelo mesmo. O `servidor\recomps.py` consulta
`api.github.com` a cada instalação de recomp: com uma sala inteira, a partir da 61ª consulta da hora todo mundo recebe
erro. Melhorias:
1. guardar a resposta da release (por repositório e tag) num cache local por algumas horas, para o mesmo computador não
   consultar de novo;
2. quando a API recusar, tentar o caminho direto `github.com/<repo>/releases/download/<tag>/<arquivo>`, que não passa
   pela API, quando o catálogo já souber o nome do arquivo;
3. corrigir a mensagem: o limite é da rede (o endereço público da escola), não de cada computador;
4. teste que simula a API recusando (código 403) e confere o caminho de reserva.

## O décimo guia (13/11, serviço do systemd `arena-web.service` no Crostini): NÃO criado

- Depende do `arena-web`, que não existe; usa a porta 8080 (o ARENA usa a 8777).
- Põe os dados em `~/.local/share/arena`: os saves sairiam do pen drive e ficariam presos naquele Chromebook.
- Deixa o servidor sempre ligado (`Restart=always` e `linger`), mesmo sem ninguém jogando: gasta memória e deixa a
  porta aberta o tempo todo. O ARENA abre quando o aluno clica e fecha junto com a janela.
- O que ele quer resolver já existe: o `ARENA.sh` reabre o servidor que cai (até 3 vezes, como o `ARENA.bat`), o
  `ARENA.sh --atalho` põe o ARENA no menu do Linux, e no celular o `ArenaServico.java` reabre o servidor.

## O 11º guia (13/11, serviço em primeiro plano `specialUse`): já está feito

Tudo o que ele pede o ARENA já tem: o `ArenaServico.java` sobe em primeiro plano com o tipo `specialUse` (linha 209),
o `montar_android.py` declara o serviço com o tipo, a explicação e as permissões `FOREGROUND_SERVICE`,
`FOREGROUND_SERVICE_SPECIAL_USE` e `POST_NOTIFICATIONS` (linhas 480 a 502), e a `ArenaActivity.java` pede a permissão
de notificação no Android 13 em diante (linha 240). Correção do guia: o tipo só é obrigatório para quem mira o
Android 14 (versão-alvo 34+); no Android 12 e anteriores não.

**O que vale conferir (ideia minha, puxada por este guia):** do Android 12 em diante o sistema pode matar os
"processos fantasmas" (processos filhos de um app, como o servidor Python que o `ArenaServico` abre) quando passam de
32 no aparelho ou gastam muito processador. Não achei nenhuma menção a isso no projeto. Teste no A12 (Android 12):
uma partida longa com o `adb logcat` aberto, procurando `PhantomProcessRecord`; se aparecer, o servidor cai no meio
do jogo (o `ArenaServico` reabre, mas o aluno perde a tela por alguns segundos) e aí se estuda a saída.

## O 12º guia (13/11, prompt para o Claude CLI criar o `ArenaWebService`): já está feito, com uma ideia a mais

Conferido item a item: as quatro permissões, o serviço `specialUse` com a propriedade
`PROPERTY_SPECIAL_USE_FGS_SUBTYPE` (`montar_android.py`, linhas 482 a 502), o canal de aviso silencioso
(`IMPORTANCE_LOW`, `ArenaServico.java` linha 194), o aviso fixo (`setOngoing`), o pedido da permissão de notificação
na `ArenaActivity` (Activity pura, com `requestPermissions`) e o servidor que continua quando o jogo abre (ele só
para quando a pessoa tira o ARENA dos recentes, `onTaskRemoved`). Não há Gradle para rodar.

**O que falta e vale fazer (pequeno, depois da release):** um botão **"Fechar o ARENA"** no aviso da barra, para o
aluno desligar o servidor sem abrir os recentes (economiza bateria quando ele esquece o ARENA aberto). Com cuidado:
se houver jogo aberto, o botão não fecha no meio da partida (avisa e espera o jogo fechar), para nunca perder o save.
Teste no A12 pelo `adb` (abrir o aviso, tocar no botão, conferir que o processo saiu e que o ARENA reabre normal).

## O 13º guia (13/11, abrir o servidor sozinho ao ligar o celular ou a TV Box): NÃO feito como está

- No celular do aluno, que é pessoal, o servidor ligaria sozinho a cada vez que o aparelho liga, com o aviso fixo na
  barra e gastando bateria, mesmo sem ninguém jogar; e a porta do ARENA ficaria aberta em qualquer Wi-Fi em que ele
  entrar. O ARENA abre quando o aluno toca no ícone e fecha quando ele tira dos recentes.
- O servidor sozinho não serve: sem a tela, ninguém joga. E do Android 10 em diante o app não pode abrir a tela a
  partir do "ligou o aparelho" (o sistema bloqueia abrir tela pelo fundo).
- Porta 8080 e porta salva nas preferências: o ARENA usa a 8777 fixa.
- Dado técnico do guia que confere: no Android 15, o aviso de "ligou" não pode abrir serviço de alguns tipos
  (`dataSync`, `mediaPlayback`, câmera, microfone...); o `specialUse` não está na lista. [Provável]

**A ideia que pode valer (só se houver TV Box na escola):** um **modo TV Box**, desligado por padrão, em que o ARENA
pode ser escolhido como a **tela inicial** do aparelho (o Android pergunta "abrir sempre com"). Assim a TV Box liga
direto no ARENA, sem truque de fundo e sem servidor sozinho. Antes de fazer, conferir com o Rafael se a escola tem
TV Box; teste no emulador de Android TV (x86_64).

## O 14º guia (13/11, ARENA como tela inicial da TV Box): vira o "modo TV Box", desligado por padrão

**Feito em 14/11:** passos 1 a 4 (apelido `ArenaComoInicio` desligado, chave em Ajustes → Máquina → TV Box pela rota
`/api/android/tela-inicial`, Voltar que fica no ARENA, `adb` no `1-COMECAR.md`). Conferido no A12: o ARENA não aparece
entre as telas iniciais e a chave aparece. **Falta:** ligar e desligar a chave no emulador de Android TV (não no A12,
para não mexer na tela inicial do Rafael).

**Já existe:** a `ArenaActivity` já tem `singleTask`, já aparece na grade da Android TV (`LEANBACK_LAUNCHER`,
`montar_android.py` linhas 542 e 559) e o Voltar já não fecha o ARENA: fecha a janela aberta na tela e, sem nada
aberto, só manda o app para trás (`ArenaActivity.java`, linhas 381 a 393).

**O que o guia faria de errado:**
- pôr a categoria `HOME` sempre: em todo celular de aluno, o botão de início passaria a perguntar "qual tela inicial?";
- forçar `screenOrientation="landscape"`: o ARENA usa `fullUser` (gira como o aparelho), e o celular em pé perderia;
- desligar o launcher de fábrica pelo `pm disable-user`: se der errado, a TV Box fica sem tela inicial até alguém
  ligar o `adb`. Nunca automático.

**Como fazer (depois da release):**
1. No `montar_android.py`, um `activity-alias` (`ArenaComoInicio`, apontando para a `ArenaActivity`) com as categorias
   `HOME` e `DEFAULT`, **desligado** (`android:enabled="false"`): nos celulares nada muda.
2. Em Ajustes (só no Android), a chave **"Usar o ARENA como tela inicial (TV Box)"**: liga o alias pelo
   `setComponentEnabledSetting` e abre a tela do Android para a pessoa escolher a tela inicial; desligar a chave
   desliga o alias e o aparelho volta à tela de fábrica.
3. Com o modo ligado, o Voltar sem nada aberto não faz nada (em vez de mandar o app para trás).
4. Para TV Box que esconde a escolha: o guia do professor ensina o `adb shell cmd package set-home-activity` e como
   desfazer; nada disso roda sozinho.
5. Testes: a `auditoria_celular` confere que o alias vem desligado; no emulador de Android TV (x86_64), ligar a chave,
   apertar Início, conferir o ARENA, desligar e conferir a tela de fábrica de volta; no A12, conferir que nada mudou.
   Guia `1-COMECAR.md` e `docs\PARIDADE.md` atualizados.

## O 15º guia (13/11, tela cheia de verdade na TV Box): quase tudo já existe; três ajustes pequenos

**Feito em 14/11:** ajustes 1 e 2 (`onWindowFocusChanged` e `WindowInsetsController` no Android 11 em diante).
Conferido no A12: barras escondidas, e escondidas de novo sozinhas depois de abrir e fechar a cortina. O 3 (entalhe da
câmera) continua só estudo.

**Já existe:** tela sempre acesa (`FLAG_KEEP_SCREEN_ON`, `ArenaActivity.java` linha 166), barras escondidas no modo
imersivo (`esconderAsBarras`, linhas 396 a 400) ao abrir e ao voltar do jogo (`onResume`, linha 364), e tema preto
sem barra de título (`Theme.Black.NoTitleBar.Fullscreen`, `montar_android.py` linha 538). O código do guia usa
AndroidX (`WindowInsetsControllerCompat`, `AppCompatActivity`, Material), que o ARENA não tem: o APK é montado sem
Gradle, só com o Android puro.

**Ajustes que valem (depois da release, com teste no A12 e no emulador de Android TV):**
1. Reesconder as barras também no `onWindowFocusChanged`: hoje, se a barra aparece por causa de um aviso ou da
   cortina de notificações, ela só some de novo no próximo `onResume`.
2. Do Android 11 em diante, usar o `WindowInsetsController` do próprio Android (o `setSystemUiVisibility` está
   marcado como antigo desde o Android 11, mas ainda funciona), mantendo o jeito atual nos aparelhos mais velhos.
3. Celular com entalhe da câmera (o A12 tem a "gota"): estudar o `LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES` junto
   com as margens seguras na tela (`viewport-fit=cover` e `env(safe-area-inset-*)` no `launcher\`). Só entra se a
   foto no A12, deitado e em pé, mostrar que nenhum botão fica embaixo da câmera; senão fica como está.

## O 17º guia (13/11, controle e foco na tela do Android): o que existe e um teste a fazer

**Feito em 14/11:** a tela pede o foco no `onWindowFocusChanged` (o WebView aparece com foco no `dumpsys` do A12); o
manifesto final declara `gamepad`, `leanback`, `touchscreen` e `type.pc` como `required="false"`. **Falta:** o teste
com o T4 virtual depois de um jogo.

**Já existe:** a tela do ARENA lê o controle pela Gamepad API (`launcher\app.js` e `launcher\navegador\`), e o
botão B do controle já funciona como "voltar" do jeito certo para o ARENA: o Android o entrega como Voltar, e o
`onBackPressed` pergunta à tela (`ARENA_ANDROID_VOLTAR`), que fecha a janela aberta; sem nada aberto, o app só vai
para trás, nunca fecha (`ArenaActivity.java`, linhas 381 a 393). A depuração remota da tela já existe, só no APK de
teste (`setWebContentsDebuggingEnabled`, linha 170).

**O que o guia faria de errado:** o `dispatchKeyEvent` dele manda o B direto para a página e engole o Voltar: o B
deixaria de fechar as janelas do ARENA.

**Teste a fazer (depois da release, no A12 com o T4 virtual pelo `hid`):** abrir um jogo, voltar ao ARENA e conferir
se o controle mexe na tela sem tocar nela. Se não mexer, pedir o foco para a tela no `onWindowFocusChanged` (junto com
o ajuste 1 do 15º guia). Conferir também se o manifesto final (o do RetroArch com o do ARENA) declara o controle e a
TV como opcionais (`uses-feature ... required="false"`), para a Play Protect e as TV Box não esconderem o app.

## O 18º guia (13/11, ponte `window.ArenaAndroid` para abrir emuladores de fora): NÃO feito

- A ponte já existe, com esse mesmo nome: `tela.addJavascriptInterface(new Ponte(), "ArenaAndroid")`
  (`ArenaActivity.java`, linha 191), com métodos para a permissão, a pasta e a saída.
- Regra do projeto (24/10): no Android o emulador roda **dentro** do app do ARENA, pelo núcleo libretro do próprio
  APK; nunca um emulador instalado à parte. O guia abre o RetroArch, o AetherSX2 e o Dolphin de fora.
- O AetherSX2 foi abandonado pelo autor, e o NetherSX2 é uma cópia modificada dele, com licença duvidosa; o PS2 do
  ARENA é o núcleo ARMSX2, dentro do APK.
- Outro app não lê `/data/data/<pacote>/cores`: o caminho do núcleo que o guia monta não funcionaria.
- Uma ponte que abre qualquer caminho de arquivo que a página mandar aumenta o risco: o ARENA só abre jogo pelo
  servidor, que confere o caminho.

## O 19º guia (13/11, acesso a todos os arquivos): já existe; dois ajustes para TV Box e Android 10

**Feito em 14/11:** ajuste 1 (as três telas em ordem e o `adb appops` no `1-COMECAR.md`). Ajuste 2 conferido no
manifesto final: `requestLegacyExternalStorage="true"` e sem `maxSdkVersion` no `READ`/`WRITE_EXTERNAL_STORAGE`,
então o Android 10 enxerga as pastas. **Falta:** o teste num emulador com Android 10.

**Já existe:** o `montar_android.py` declara o `MANAGE_EXTERNAL_STORAGE` (linha 500); a `ArenaActivity` explica
antes de pedir, abre a tela "Acesso a todos os arquivos" do ARENA no Android 11 em diante (linhas 317 a 337), confere
com o `Environment.isExternalStorageManager()` (linha 433) e faz o pedido antigo de leitura e gravação nos aparelhos
mais velhos. Sem a permissão, o ARENA abre do mesmo jeito, com as pastas dele.

**Ajustes que valem (depois da release):**
1. **TV Box sem a tela do app:** hoje, se o aparelho não tem a tela "Acesso a todos os arquivos" do ARENA, o pedido
   cai no pedido antigo, que no Android 11 em diante não dá acesso. Tentar antes a lista geral
   (`ACTION_MANAGE_ALL_FILES_ACCESS_PERMISSION`) e, por último, a tela de detalhes do app; e explicar ao professor o
   `adb shell appops set --uid <pacote> MANAGE_EXTERNAL_STORAGE allow` (no guia, nunca automático).
2. **Android 10:** conferir no manifesto final (o do RetroArch com o do ARENA) se há o `requestLegacyExternalStorage`
   e os limites `maxSdkVersion` do `READ`/`WRITE_EXTERNAL_STORAGE`; sem o primeiro, um celular com Android 10 não
   enxerga as pastas de jogos fora do app. Teste no emulador com Android 10.

## O 20º guia (13/11, PPSSPP, DuckStation e Mupen64Plus FZ de fora): NÃO feito

Continua o 18º (abrir emuladores instalados à parte), contra a regra de 24/10. E o ARENA já tem os três consoles
dentro do app, pelos núcleos libretro: PSP pelo `ppsspp`, PlayStation pelo `swanstation` (que é o DuckStation em
forma de núcleo) e pelo `pcsx_rearmed`, Nintendo 64 pelo `mupen64plus_next` (`servidor\consoles.json`, linhas 466,
780, 781 e 902). Erros técnicos do guia: mandar `file://` para outro app derruba o ARENA no Android 7 em diante
(`FileUriExposedException`, com o app mirando a versão 24 ou mais nova), não importa se o endereço foi montado com o
`Uri.Builder` [Certo]; e o DuckStation para Android saiu de circulação pelo próprio autor, com licença que proíbe
redistribuir versões modificadas [Provável].

## O 21º guia (13/11, cartão SD e pen drive no Android): já acha; falta perceber quando entra ou sai

**Feito em 14/11:** passos 1 e 2 (`ArenaServico.ouvirOsCartoes`, e a tela lê as pastas de novo pelo `/api/indexar`
com um aviso). Conferido no A12: o receptor aparece registrado com as quatro ações e o esquema `file`. Mais o botão
**Fechar o ARENA** no aviso (testado no A12: fecha a tela, o servidor e o aviso). **Falta:** o teste com um pen drive
de verdade no OTG (o aviso do sistema não se imita pelo `adb`).

**Já existe:** a `ArenaActivity.raizes()` (linhas 581 a 601) acha a memória interna e cada cartão SD ou pen drive
pelo `getExternalFilesDirs` (cortando o `/Android/data/...`), e a `candidatas()` procura a pasta do ARENA até dois
níveis dentro de cada um. Não precisa de `/proc/mounts`.

**O que o guia tem de errado:** a reserva por `/mnt/media_rw` não funciona para app comum (a pasta é só do sistema)
[Provável]; o receptor declarado no manifesto, `exported="true"`, aceitaria aviso de qualquer app; e a porta 8080 e o
`/api/storage/sync` são do servidor Rust que não existe.

**O que vale fazer (depois da release):** perceber o cartão ou o pen drive que entra ou sai com o ARENA aberto.
1. No `ArenaServico`, registrar em código (não no manifesto) um receptor de `MEDIA_MOUNTED`, `MEDIA_UNMOUNTED`,
   `MEDIA_EJECT` e `MEDIA_BAD_REMOVAL`, com o esquema `file` (sem ele o aviso não chega) [Certo].
2. Ao receber, avisar a tela (como o "pronto" já faz), que pede ao servidor para ler as pastas de novo pela rota que
   o indexador já usa; na saída do pen drive, a tela avisa "o pen drive saiu" em vez de mostrar jogos que sumiram.
3. Conferir antes como o PC trata o mesmo caso (pen drive que entra com o ARENA aberto), para os dois ficarem iguais.
4. Teste no A12 com um pen drive no OTG (ou cartão): entra, a lista aparece; sai, o aviso aparece e nada trava.

## O 22º guia (13/11, indexador em Rust com cache): o Rust não entra, mas o guia achou um defeito de verdade

**Defeito reproduzido em 13/11 (22h09)** com o `indexador.varrer_pasta` de hoje: num pen drive usado num Mac, o
`._Mario (USA).sfc` (o arquivo de 4 KB que o macOS cria ao lado de cada arquivo) aparece como um segundo "Mario" na
lista, e o que está na lixeira do Mac (`.Trashes\Zelda.sfc`) aparece como jogo. Abrir esses itens falha.
**Correção (entra na 2026.11.14, depois da rodada):** o `varrer_pasta` passa a pular arquivo que começa com `._` e as
pastas ocultas do sistema (`.Trashes`, `.Spotlight-V100`, `.fseventsd`, `.Trash-1000` do Linux, `$RECYCLE.BIN` e
`System Volume Information` do Windows), com teste no `servidor\tests\run.py`. Vale em todo sistema (o servidor é o
mesmo).

**O resto já existe:** o `os.walk` do indexador não segue atalho de pasta (`followlinks` desligado), o catálogo fica
gravado em disco de forma atômica, o trabalho demorado roda em thread separada e a tela abre com o catálogo que já
estava gravado. As pastas por console do guia (13 fixas) são bem menos que as do ARENA (`consoles.json`, por nome de
pasta e por extensão, com os casos de disco, trilhas e fliperama).

## O 23º guia (13/11, aviso em tempo real pela WebSocket): já há WebSocket no ARENA; só se o 21º precisar

O ARENA já tem uma WebSocket feita só com a biblioteca padrão (`servidor\controle_remoto.py`, RFC 6455, a do controle
pelo celular). Se o item do pen drive que entra ou sai (21º guia) precisar avisar a tela do PC sem ela perguntar, a
mesma peça serve; no Android, o caminho mais simples é o que já existe (o `ArenaServico` avisa a tela pelo
`evaluateJavascript`, como o "pronto"). Nada de laço de consulta (regra do servidor parado perto de 0%).

## O 24º guia (13/11, esconder consoles sem emulador instalado): NÃO feito; o ARENA avisa em vez de esconder

Depende dos emuladores de fora (18º e 20º guias), que não entram. E o ARENA já trata o caso, de propósito de outro
jeito: o servidor diz o estado de cada console (`plataforma.estado`, `"pronta"` ou não, com o `motivo`), e a tela
mostra o jogo apagado, com o botão Abrir desligado e o motivo escrito (`launcher\app.js`, linhas 757 a 850). Esconder
deixaria o aluno sem saber por que o jogo sumiu; foi a mesma decisão do selo "Pode travar", que passou a avisar em vez
de esconder (linha 347). Procurar emulador no `PATH` do Linux também não serve: o ARENA usa os dele, na pasta
`emuladores\`, não os instalados no sistema.

## Outras melhorias do projeto que já estão na fila

- Perfil do dusklight (GameCube) por máquina, como o dos recomps do libultraship (`docs\RECOMPS-DESEMPENHO.md`).
- Medir os perfis dos recomps no Celeron N5100 com o jogo de verdade.
- A abertura do servidor (orçamento 1b) já foi resolvida em 12/11: 1,91 s, para um teto de 2,3 s. A Fase 1 confere se
  continua assim.
