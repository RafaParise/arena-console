# Relatório de qualidade — auditoria 3

Começada em 07/10/2026, no ramo `auditoria` (a partir do `main` em `9def005`,
versão 2026.10.03.2). O pedido inteiro, sem resumir, e as regras estão em
`docs\PLANO-AUDITORIA.md` (seção "Auditoria 3"). As rodadas anteriores:
`docs\RELATORIO-AUDITORIA-1.md` (setembro, fases 0 a 8) e
`docs\RELATORIO-AUDITORIA-2.md` (25/09). Os números brutos desta rodada ficam
em `docs\auditoria3\`.

**Onde foi medido:** o computador do Rafael (Ryzen 5 5600G, 12 núcleos
lógicos, Radeon integrada, ~11,8 GB). **A régua não é ele:** toda decisão de
desempenho é julgada pelo notebook da escola (Celeron N5100, sem AVX —
`docs\MAQUINA-ALVO.md`). Onde um número daqui não vale para lá, o relatório
diz.

---

## Antes (Fase 0, 07/10/2026)

### Testes de referência

| Teste | Resultado |
|---|---|
| Bateria (`servidor\tests\run.py`, a do `RODAR_TESTES.bat`) | **203 de 203**, 11,2 s |
| Rodada completa (`ferramentas\rodada_final.py`: bateria, fuzz e os 90 `testes\teste_*.py`, com RetroArch, PCSX2, RPCS3 e Edge de verdade) | ver "Rodada completa", abaixo |

### Números

Ferramentas: `testes\linha_base.py` (ampliada nesta fase: a tela de verdade,
as portas UDP, 60 s parado depois de 30 s para assentar),
`testes\medir_gravacoes_parado.py` (ampliada: 1 hora, com a tela aberta, a
pasta inteira conferida) e `testes\inventario.py` (ampliado: o mapa da tela,
os temporizadores e as linhas de execução).

| Medida | Antes | Observação |
|---|---|---|
| Tamanho da pasta de desenvolvimento, sem jogos, `.git` e `backup` | **12.766 MB** | 8,0 GB disso são dados de jogo dentro de `emuladores\` (um jogo de PS3 instalado no disco do RPCS3, `dev_hdd0\game\BLES00816`, 5,9 GB; `dev_hdd1` 1,5 GB; caches do Xenia 1,3 GB; cache do RPCS3 0,25 GB), não programa. Na auditoria 1 eram 2.810 MB |
| — `retroarch\` | 2.457 MB | núcleos 1.560 MB (196 arquivos, todos os núcleos); BIOS em `system` 325 MB; bancos `.rdb` 168 MB |
| — `emuladores\` (os 4) | 10.250 MB | RPCS3 8.307, Xenia 1.503, Dolphin 220, PCSX2 220 |
| — `servidor\` | 22,5 MB | 20,3 MB são o Python embutido |
| — `launcher\` (a tela) | 0,3 MB | 6 arquivos |
| Versão dos alunos (o que se distribui) | 1,54 GB na última montagem do zero (02/10, com BIOS) | medida de novo na Fase 8, montada do zero |
| Linhas do programa (servidor sem testes + tela + `.bat`) | **30.744** em 39 arquivos | maiores: `arena.py` 6.416, `app.js` 4.362, `graficos.py` 2.565, `estilo.css` 1.778, `bios.py` 1.445, `consoles.json` 1.278, `indexador.py` 1.151, `index.html` 1.044 |
| Linhas dos guias (raiz `.md`) | 4.796 em 7 | |
| Linhas dos testes / ferramentas / documentos | 18.647 em 130 / 7.072 em 44 / 3.312 em 10 | o arquivo inteiro, por arquivo, em `docs\auditoria3\linha_base_antes.json` |
| **Abertura até a tela pronta** (a lista de jogos desenhada) | **2,61 s** | servidor 0,58 s + **1,0 s de espera de propósito** antes de abrir a janela (`threading.Timer(1.0, ...)` em `arena.principal`) + Edge 0,52 s (abrindo do zero, perfil novo) + página 0,51 s. No Celeron (COLETAR de 30/09): 5,57 s do disco, 8,55 s do pen drive |
| Processador parado — servidor sozinho | **0,05% de um núcleo** | 60 s depois de 30 s para assentar |
| Processador parado — servidor com a tela aberta | 0,03% de um núcleo | a tela parada não pediu nada ao servidor (0 pedidos por minuto) |
| **Processador parado — a tela** | **9,67% de um núcleo** | fundo animado em "Sempre" (a configuração do Rafael) a 59,9 quadros/s, mesmo com o Windows pedindo menos movimento. No Celeron, por núcleo 43% do Ryzen, isso passaria de 20% de um núcleo |
| Memória — servidor | **42,1 MB** (29,9 MB privada) | teto do modo alvo: 64 MB |
| Memória — a tela | 539,9 MB em 8 processos do Edge (271,9 MB privada) | Edge aberto só para o ARENA (perfil novo). Com o Edge do aluno já aberto, a janela do ARENA divide os processos dele e pesa menos |
| Threads | servidor 5 parado (7 logo depois de abrir) | o servidor HTTP cria uma por pedido e a solta no fim |
| Temporizadores da tela, parada | 2 `setInterval` (3 s, um em cada fundo animado), 0 `setTimeout` por minuto, 59,9 quadros de animação por segundo | |
| Alças do Windows — servidor | 181 | |
| Gravações em disco por hora, parado com a tela | ver "Gravações em disco", abaixo | |
| Portas | **TCP 127.0.0.1:8777** (só este computador; vira 0.0.0.0 com "Aceitar conexões da rede"); **UDP 0.0.0.0:55436, a rede toda, sempre** | a 55435 (partida a dois) é do RetroArch e só existe durante a partida |

### Inventário

Tudo em `docs\auditoria3\inventario_antes.json`, lido direto do código.

**Arquivos.** 254 arquivos são do ARENA (servidor, tela, `.bat`, guias,
documentos, ferramentas, testes). As pastas que não são código do ARENA:

| Pasta | Arquivos | MB | O que é |
|---|---|---|---|
| `retroarch\` | 15.235 | 2.457 | emulador e núcleos (de terceiros) + BIOS em `system` |
| `emuladores\` | 11.756 | 10.250 | PCSX2, Dolphin, RPCS3, Xenia (de terceiros) + o que eles guardam |
| `servidor\python\` | 35 | 20,3 | Python 3.13 embutido |
| `jogos\` | 207 | 210.741 | os jogos do Rafael |
| `BIOS\` | 59 | 30,8 | as prateleiras de BIOS (03/10) |
| `backup\` | 80 | 83,0 | cópias de segurança e originais guardados |
| `dados\` | 191 | 3,0 | o que é de quem usa (banco, configuração, miniaturas) |
| `perfil\` | 33 | 0,1 | as coletas do COLETAR |

**Rotas do servidor.** 63 caminhos, 64 pares rota + método. **8 abertas à
rede** (`ROTAS_REDE_EXTERNA`): `/api/amigo/codigo`, `/api/amigo/testar`,
`/api/colegas`, `/api/jogo/impressao`, `/api/partida/testar`, `/api/ranking`,
`/api/sinc/ola`, `/api/sinc/receber`. As outras 55 recusam pedido de outro
computador. Quem chama: a tela chama 61 (uma delas, `/api/capa`, pelo
endereço que o próprio servidor põe no catálogo); o `PARTIDA.bat` chama 5;
outro ARENA pela rede, 2. Nenhuma rota sem quem a chame, e nenhuma rota pedida
pela tela que o servidor não tenha. A lista, com a função da tela que chama
cada rota, está no JSON (`rotas`).

**A tela.** 13 janelas: a principal, 7 gavetas (Perfil, Como colocar jogos,
Biblioteca online, Ajustes, Conquistas da turma, Recordes, Jogo) e 6 janelas
de pergunta (Jogar junto, Jogar junto neste computador, Registrar pontuação,
Adicionar jogo autorizado, Qual é o console deste jogo?, Como podemos chamar
você?). 131 botões, chaves, listas e campos no `index.html`: 39 em Ajustes, 25
na tela principal, 19 no Perfil, 12 em "Adicionar jogo autorizado", 9 em
"Jogar junto"... Mais 23 tipos de botão que o `app.js` cria sozinho (os de
cada BIOS, cada amigo, cada cheat, cada aviso de jogo...). Para cada um, o
JSON (`tela.controles`) diz a janela, a aba, o que faz e as rotas que usa,
seguindo as funções do `app.js` (sem contar os cliques que uma função só
prende para depois). 61 só mexem na tela (abrir, fechar, trocar de aba,
campos); 70 usam rota. **Nenhum botão sem ação** (os 14 que pareciam sem
ação estão ligados por laço, por `onclick` ou pelo atributo `data-papel`).
**Para ler:** `docs\auditoria3\inventario_antes.md` (as rotas, cada janela
com seus controles e rotas, os botões que o `app.js` cria, os
temporizadores, as linhas de execução, as chaves e os arquivos).

**Configuração.** 23 chaves em `config_padrao` (mais 21 opções avançadas em
`AVANCADO_PADRAO`, que viram opções do RetroArch todas de uma vez em
`arena.py:1486`). Cada chave e os arquivos que a leem estão no JSON
(`chaves_de_config`). Nenhuma chave sem quem a leia. Os arquivos de
`dados\`: `config.json`, `arena.db`, `controles.json`, `jogadores.txt`,
`consoles_manuais.json`, `manifesto.json` (o catálogo guardado),
`fechamentos.json`, `problemas_dos_jogos.json`, `zips_conferidos.json`,
`bios_conferidas.json`, `acervo_autorizado.json`, as miniaturas, os
registros do RetroArch e os remapeamentos da partida.

**Serviços em segundo plano** (15 pontos onde nasce uma linha de execução):

| Serviço | Quando roda | Para quê |
|---|---|---|
| Vigia (`rodar_vigia`) | sempre, a cada 20 s (60 s no modo econômico); para durante o jogo no ultra | testa quais amigos salvos estão no ar (uma linha por amigo, `testar`) e corrige o endereço que mudou; testa se há internet (conexão a 1.1.1.1:53 e 8.8.8.8:53); renova a lista de endereços deste computador; manda os recordes da fila; e faz a cópia de segurança "quando a internet volta" |
| Descoberta de colegas (`anunciar_e_escutar`) | sempre, acordando a cada 1 s | escuta a porta UDP 55436 (a rede toda); grita "estou aqui" a cada 5 s só com "Aceitar conexões da rede" ligado |
| Conferir Vulkan (`conferir_vulkan`) | uma vez, logo depois de abrir | pergunta, num processo à parte, se a placa tem Vulkan de verdade |
| Conferir fliperamas (`conferir_fliperamas`) | uma vez por zip de fliperama, devagar | acha zip danificado (o caso do `mslugx.zip`) |
| Organizar a pasta BIOS (`organizar_bios`) | uma vez, 3 s depois de abrir | prateleiras, LEIA e BIOS no lugar onde o emulador procura |
| Abrir a janela (`threading.Timer`) | uma vez, 1,0 s depois de abrir a porta | a tela |
| Janela preta (`janela_preta`) | sempre (fila de recados) | escreve na janela preta sem travar o servidor (Edição Rápida do Windows 10) |
| Servidor HTTP | uma linha por pedido | |
| Sob pedido | ao clicar | procurar partidas (até 20 amigos em paralelo), abrir o jogo e esperar o emulador fechar, abrir a tela da BIOS do console, buscar capas, nomes dos adaptadores de rede (PowerShell, com cache), trocar a escuta da rede, descompactar jogo de CD |

**Temporizadores da tela** (21 pontos no código): o laço de animação e uma
conferência a cada 3 s em cada fundo animado (`setInterval(sincronizar,
3000)`, a mesma que o `MutationObserver` e o aviso do Windows já fazem na
hora); a lista de partidas a cada 4 s
(só com a janela de Jogar junto aberta); a volta do servidor que caiu (2 s e
3 s); a fila das miniaturas; o andamento de "Arrumar" e de "Buscar capas"
(1 s, só enquanto trabalham); o mapeador de controle (só enquanto mapeia);
recados e pequenas esperas da tela. Parada, ficam vivos só os 2 dos fundos.

**O que depende de internet.**

| O quê | Para onde | Sem internet |
|---|---|---|
| Capas | `thumbnails.libretro.com`, `raw.githubusercontent.com/libretro-thumbnails`, `art.gametdb.com` (GameCube/Wii), `download.xbox.com` (Xbox 360) | fica sem a capa; capa de dentro do disco (PS3, PSP) e capa posta na pasta funcionam |
| Biblioteca online | `archive.org` (busca, ficha e download) | avisa |
| Acervo autorizado | os endereços que o professor cadastrou (`acervo_autorizado.json`, hosts restritos, SHA-256 conferido) | avisa |
| Jogar junto de casas diferentes | o repasse do RetroArch (`netplay_mitm_server`) | na escola é direto, sem internet |
| Teste de internet do vigia | 1.1.1.1:53 e 8.8.8.8:53, a cada 20 s | marca "sem internet" |
| PS3 online | RPCN (só com `rpcn_ativo`, desligado por padrão) | |
| Sincronizar com amigos | os endereços dos amigos (rede local ou internet) | fica na fila e manda depois |

### Gravações em disco

`testes\medir_gravacoes_parado.py`, contando as gravações do PRÓPRIO
processo do servidor (`WriteOperationCount`/`WriteTransferCount` do
Windows) e conferindo cada arquivo da pasta (menos `jogos\` e `.git\`).

| Medida | Antes | Observação |
|---|---|---|
| **Parado, 1 hora, com a tela aberta** | **0 gravações, 0 KB** | Nenhum arquivo de `dados\`, `backup\`, `retroarch\`, `emuladores\` ou `BIOS\` mudou na hora inteira (os que mudaram eram as minhas edições em `docs\`, `testes\` e `ferramentas\`, feitas no meio da medida) |
| **Abertura** — até o servidor responder | **43 gravações, 8.264 KB** | Quase tudo é o teste de velocidade do disco (`hardware.medir_disco`): grava até 8 MB em blocos de 1 MB na pasta do ARENA (o pen drive) e apaga; mais `dados\arena_override.cfg`, `retroarch\retroarch-core-options.cfg` e uma linha em `dados\logs\queda-do-servidor.txt` |
| **Abertura** — nos 60 s seguintes | **+2 gravações, +1.529 KB** | A cópia de segurança indevida (achado 1, abaixo): 23 arquivos, 1,6 MB, inclusive caches de shader do PSP (`.vkshadercache`, que o emulador refaz sozinho) |
| **Total por abertura** | **~9,8 MB** | Pelo desgaste do pen drive é pouco (10 aberturas por dia, o ano inteiro, ficam longe do limite de gravações de um pen drive ou cartão), mas é tempo de abertura e é cópia que não precisava |

### Rodada completa

`ferramentas\rodada_final.py --saida=docs\auditoria3\rodada_antes.json`
(07/10/2026, 21h56 às 23h13, em segundo plano, gravando depois de cada
script): **87 de 92 passaram**, em 76,8 min. Nenhum arquivo de `dados\` mudou.

| Teste | O que o ARENA fez de verdade |
|---|---|
| Bateria (`servidor\tests\run.py`) | 212 de 212 (as 203 + os 9 testes trazidos de `ferramentas\`, item R5 da Fase 1) |
| `fuzz_rotas` | 279 checagens, 0 falhas |
| `teste_abrir_todos` (27 min) | 127 jogos de 22 consoles. Dos 73 que abrem no RetroArch, **71 abrem e mostram imagem**; os 2 que não: *Micro Machines 2* (abertura preta de 25 s; falso, já conhecido) e *Marvel vs. Capcom* do Dreamcast (o RetroArch não chegou ao fim em 90 s: Fase 5). **Jogar Junto: 47 conectaram, 0 falharam**; 25 pulados de propósito (núcleo sem rede: N64, PSP, Dreamcast, C64, Amiga). Os 54 dos emuladores de fora (PCSX2, Dolphin, RPCS3, Xenia) têm testes próprios |
| `teste_orcamentos_modo_alvo` | nenhum orçamento estourou (processador parado 0,23% de um núcleo, indexação 0,19 s, 0 gravações por minuto, SNES 60,0 FPS, variação 3,0%) |
| `teste_longa_duracao` | 46.256 pedidos, 0 falhas de conexão, memória +0,6 MB, alças +10 |
| `teste_netplay_5_jogadores` | os 4 convidados entraram |
| `teste_rede_ruim` | os 5 cenários (50 a 200 ms, perda de 1% e 5%) conectaram, 0 avisos de travada |

**As 5 falhas, uma por uma** (nenhuma é defeito novo do ARENA):

| Teste | Por que falhou | O que fazer |
|---|---|---|
| `teste_descoberta_pacote_torto` | É o teste novo da Fase 1, escrito para **reproduzir** o achado C5. Reproduziu: depois de pacotes tortos na porta 55436, a linha que escuta morre e nenhum colega novo entra mais | Passa depois do conserto C5 |
| `teste_ps2_sem_bios` | O teste esperava a frase antiga ("o arquivo vai em `retroarch\system`"). Desde 03/10 (`ce05805`, pasta BIOS) a frase manda para `BIOS\PS2`, que é o certo | Corrigir o teste (Fase 1) |
| `teste_multitap_regra_de_ouro` | Compara cada jogo com a versão de antes do multitap (`97ffe03`). O KOF 2002 convertido em 03/10 ganhou o nome "The King of Fighters 2002" (`nomes_arcade.NOMES_FORA_DO_BANCO`) e não tem par na versão antiga | Pôr o título na lista de títulos novos de propósito do teste (Fase 1) |
| `teste_kof2002_convertido` | A foto de 50 s veio com 29 KB e o teste pedia mais de 50 KB. Repetido e **olhado**: em 30 s a demonstração, em 50 s a tela de título (logotipo sobre fundo preto, que comprime muito), cores certas. O jogo roda; o limite do teste estava errado | Corrigir o limite do teste (Fase 1) |
| `teste_capas_todos_os_consoles` | A capa do GameCube (GameTDB) não veio durante a rodada. Repetido em seguida: **21 de 21**, e o GameTDB responde normal. Foi a rede. Mas a tela diria "Não achei capa pra esse jogo nesse banco." — esconde que foi a rede | Fase 3 (internet ruim): dizer que o servidor de capas não respondeu |

E dois deslizes de higiene dos testes (a rodada consertou sozinha): o
`teste_pcsx2_portatil` mudou o `PCSX2.ini` de verdade (a rodada devolveu), e 6
testes deixaram pasta no Temp (a rodada apagou: 43 MB das fotos do
`teste_abrir_todos`, que as deixa de propósito para conferir, e 5 pequenas).
A regra 6 pede que cada teste apague o que criou: Fase 1.

### Achados da Fase 0 (para as próximas fases)

1. **Cópia de segurança a cada abertura** (Fase 1/2). O vigia começa com
   `internet_estava_fora: True`; na primeira volta (20 s depois de abrir),
   com internet, conta como "a internet voltou" e faz uma cópia em
   `backup\` (o `retroarch.cfg`, os arquivos de `dados\` e os saves, ~1,5 MB
   e 23 arquivos). Com o rodízio de 3, **três aberturas apagam as cópias
   anteriores**. Aconteceu de verdade nesta fase: as 4 aberturas das medições
   de hoje tiraram as cópias de 05/10 (os dados de verdade continuam inteiros
   em `dados\`; as cópias de hoje têm o mesmo conteúdo). A cópia é local: a
   internet não tem nada a ver com ela.
2. **A tela parada gasta 9,7% de um núcleo** com o fundo animado em "Sempre"
   (Fase 2: medir no Automático e no Parado, nos dois temas; estimar o
   Celeron).
3. **1,0 s de espera fixa** antes de abrir a janela (Fase 2). A porta já está
   aberta quando a espera começa.
4. **O vigia testa a internet a cada 20 s** (Fase 1: quem usa
   `VIGIA["internet"]`; se for só a cópia do item 1, as duas coisas saem
   juntas).
5. **UDP 55436 escuta a rede toda mesmo com a rede desligada** (Fase 3: o
   que um pacote de outro computador consegue fazer; se a lista de vizinhos
   tem limite).
6. **A trava do "run ahead"** (`arena.py:1484`, desliga em máquina de nota
   abaixo de 4) é desfeita duas linhas depois pelas opções avançadas do aluno
   (Fase 1: conferir se a tela deixa ligar `run_ahead_enabled`).
7. **Sobra de gravação interrompida** em
   `emuladores\Xenia\Xenia\xenia-canary.config.toml.11580.tmp` (26/09) (Fase 1).
8. **8 GB de dados de jogo dentro de `emuladores\`** na pasta de
   desenvolvimento (Fase 8: conferir que a versão dos alunos não leva nada
   disso).
9. **Conferência repetida nos fundos animados**: `setInterval(sincronizar,
   3000)` em `field-background.js` e `galaxy-background.js`, além do
   `MutationObserver` e do aviso do Windows que já disparam a mesma conta
   (Fase 1: por que existe).
10. **A versão dos alunos mudou de lugar** (fora das conversas: as pastas de
   console de `ARENA\ARENA\jogos\pessoais` foram esvaziadas em 06/10, entre
   10:02 e 10:05, e `ARENA-alunos\jogos` apareceu em 07/10 às 05:08). Hoje:
   `..\ARENA` é o programa com os dados, a BIOS e os saves do Rafael (versão
   2026.10.03.2, sem os jogos), e `..\ARENA-alunos` tem só `jogos\` (3,7 GB).
   O montador (`--atualizar`) ainda aponta para `..\ARENA-alunos` (Fase 8).
   **Resolvido no mesmo dia:** o Rafael confirmou que foi ele e pediu para
   voltar como estava. Os 103 arquivos de jogo (3.957.916.092 bytes) voltaram
   para `jogos\pessoais` da versão dos alunos, conferidos um a um (tamanho
   e data, nenhum conflito), e ela voltou a se chamar `..\ARENA-alunos`.
11. **O teste de velocidade do disco grava até 8 MB a cada abertura** (Fase 2:
   guardar a medida por máquina e pen drive e só medir de novo quando mudar
   ou envelhecer; medir o tempo de abertura antes e depois).
12. **A cópia de segurança leva caches** (`.vkshadercache` do PSP, que o
   emulador refaz) e é feita mesmo quando nada mudou desde a última (Fase 2:
   só copiar o que é save e só quando algo mudou — assim as 3 guardadas são
   de momentos diferentes).

---

## Fase 1 — Varredura e limpeza

Ferramenta nova: `testes\varredura_auditoria3.py` (só lê; pistas em
`docs\auditoria3\varredura_fase1.json`). Cada pista foi conferida à mão.
**Registro da aprovação** (leitura adotada em `PLANO-AUDITORIA.md`): a lista
abaixo é a escolha recomendada, com a prova de cada item; a regra 3 ("nada é
removido sem a prova") vale item a item.

### Conferido, e não é defeito (fica como está)

| Pista | O que é de verdade |
|---|---|
| "Só assistir" (o roteiro cita como função removida) | Existe de propósito: o Rafael pediu o conserto em 30/09 (tarefa 5, commit `d2b356d`: "Só assistir abria o jogo sozinho"); hoje entra como espectador. Testado por `testes\teste_partida_aparece.py` |
| Gravação de vídeo e transmissão | Só o código que as mantém DESLIGADAS (`arena.py:616–635`, decisão que não se reverte) e a explicação no `4-SAVES.md` |
| DuckStation | Comentários e o filtro que apaga as chaves velhas `duckstation_*` do arquivo de opções (`graficos.py:942`) |
| Scroll Lock | Nenhuma ocorrência (a tecla é F9) |
| Texto em inglês na tela | Nenhum: as 14 pistas eram "no" (português), "save state" (termo do guia 4) e o `type="search"` de uma etiqueta |
| Rota sem quem a chame / botão chamando rota que não existe / chave de configuração sem leitor | Nenhuma (inventário da Fase 0) |
| 104 chaves de `.json` "sem leitor" | Dados, não código: nomes de opção de núcleo (`graficos.json`, conferidos dentro de cada `.dll` por `teste_chaves_graficos.py`), nomes de jogo, campos de documentação do `multitap.json` e a descrição de cada controle (`perfis_controle.json`) |
| 5 caminhos absolutos | Reservas do Windows (`C:\Windows` quando falta `SystemRoot`) e a lista de navegadores em `Arquivos de Programas` |
| Arquivo aberto sem fechar | Só o registro de quedas (`janela_preta.py:69`), aberto de propósito o tempo todo: o `faulthandler` escreve nele quando o Python cai |
| 208 exceções engolidas | 195 estreitas (`OSError`, `ValueError`...) em limpeza de temporário, leitura com plano B e sondagem de hardware; as 13 largas são de propósito (registrar a queda nunca derruba o jogo; refazer a lista depois de descompactar é bônus; sondagem de hardware). Duas famílias pedem aviso: C3 |
| 30 gravações "não atômicas" | 28 já vão por temporário + `os.replace` (ou são arquivo vazio, de ajuda ou de teste de disco); a de `arrumar.py:385` grava dentro de uma pasta temporária. Sobra uma: C2 |
| `setInterval(sincronizar, 3000)` nos fundos animados | Não é repetição: além de conferir o modo, é o vigia que religa a animação quando o laço trava (mais de 3 s sem quadro com a janela à vista) |
| Arquivos repetidos | Só arquivos vazios (`__init__.py` e duas saídas vazias da auditoria 2) |
| Guias citando arquivo que não existe | Nenhum: as 14 pistas existem (em `dados\`, no Python embutido, no RPCS3, no pen drive) |
| Caminhos de menu dos guias | Batem com a tela; a diferença de acento (o guia diz "Folga do analógico", a tela "Folga do analogico") some na Fase 7 (o `recursos.json` inteiro está sem acento) |

### Remoções (com a prova)

| # | O quê | Prova de que não é usado | O que quebra |
|---|---|---|---|
| R1 | `graficos.jogo_suporta_multitap()` (`graficos.py:2280`) | Nenhuma chamada no programa, nos testes ou nas ferramentas (árvore do código + busca de texto); a mesma conta mora em `jogadores.py:158` desde 02/10 | Nada |
| R2 | `como_colocar._tem()` (`como_colocar.py:177`) | Nenhuma chamada desde que a BIOS passou para `bios.py` (03/10) | Nada |
| R3 | Ferramentas de uso único que já rodaram ("Roda uma vez só" no próprio arquivo) e que ninguém cita fora dos relatórios: `aplicar_protege_cfg.py`, `corrigir_chaves_graficos.py`, `montar_relatorio_aud2.py`, `trocar_testdb.py`; e `limpar_retroarch_cfg.py` (o montador tem a sua própria `limpar_retroarch_cfg`) | Nenhuma é importada nem chamada por `.bat`; ficam no histórico do git | Nada |
| R4 | `emuladores\Xenia\Xenia\xenia-canary.config.toml.11580.tmp` | Temporário do `gravar_atomico` (o número é o da thread) de 26/09 21:00 que nunca virou o arquivo final; a configuração de verdade é de 21:02 e está inteira | Nada |
| R5 | Os testes antigos de `ferramentas\teste_*.py` (20), que a rodada não roda | Cada um, abaixo: o que só ele conferia veio para a bateria ou para `testes\` (numa cópia isolada, sem tocar no ARENA de verdade); o resto já era conferido por outro teste | Nada (a cobertura só aumenta) |

**R5, um por um** (todos subiam o servidor na porta 8777 da pasta de
verdade ou mexiam em dado real; os de Jogar Junto deixavam sessões
"hospedeiro" no `arena.db` do professor — a origem do
`ferramentas\limpar_registros_de_teste.py`):

| Teste antigo | Onde o que ele conferia está agora |
|---|---|
| `teste_amigo_ip_muda` | bateria, `test_portados_auditoria3.TestAmigoQueMudouDeIp` (3 testes) |
| `teste_controle_neogeo` | bateria, `TestControleDoNeoGeo` |
| `teste_netplay_xbox360` | bateria, `TestSystemlinkXbox360` (2) |
| `teste_rede_ps2_gt4` | bateria, `TestRedePs2` (2) |
| `teste_rodizio_logs` | bateria, `TestRodizioDosRegistros` |
| `teste_perfil_foto` | bateria, `TestFotoDoPerfil` (6; trouxe o achado C7) |
| `teste_backup_falha_cancela_apagamento` | `testes\teste_comecar_do_zero.py` (8 checagens, cópia isolada, porta livre; trouxe o achado C6) |
| `teste_biblioteca_online` | `testes\teste_biblioteca_busca.py` e `teste_internet_archive_download.py` |
| `teste_capa_online` (o que apagava as capas de verdade) | `testes\teste_capas_todos_os_consoles.py`, parte 6 (capa baixada de verdade) |
| `teste_correcao_caminhos` | `testes\teste_caminho_fora_no_cfg.py`, `teste_cfg_sem_linha_repetida.py` e `ferramentas\teste_aceite_pasta_movida.py` |
| `teste_netplay_megadrive`, `_neogeo`, `_ps1`, `teste_pcsx_rearmed_basico` | `testes\teste_abrir_todos.py`: hospeda e conecta CADA jogo do RetroArch (47 conectaram na rodada), o PS1 com o PCSX ReARMed |
| `teste_netplay_suporte_nucleos` | `teste_abrir_todos.py` (os 25 "núcleo sem rede") e `consoles.json` (`netplay: false` com o motivo) |
| `teste_netplay_check_frames` | Investigação de 21/09 (a decisão está no CLAUDE.md); o valor (`0` no PCSX ReARMed) é conferido pelo `teste_multitap_regra_de_ouro`, que compara o arquivo da partida de cada jogo |
| `teste_memory_card_ps1` | Investigação do limite conhecido (o cartão de quem hospeda não vai para o convidado), registrada no CLAUDE.md; a partida inteira até salvar fica no roteiro de sala (Fase 5) |
| `teste_pcsx2_completo`, `teste_qualidade_pcsx2` | `testes\teste_pcsx2_inicia.py`, `teste_pcsx2_seguro.py`, `teste_pcsx2_placa.py`, `teste_abaixo_do_original.py` (PCSX2 de verdade) |
| `teste_rpcn` | bateria, `test_graficos_acervo.test_rpcn_segue_a_chave_nos_dois_sentidos` |

Fica em `ferramentas\` só o `teste_aceite_pasta_movida.py` (a rodada o roda).
`ferramentas\acentuar_textos.py` fica até a Fase 7 (serve para o
`recursos.json`). `ferramentas\inventario_jogos.py` (útil, ninguém citava)
fica e passou a ser citado no `2-JOGOS.md` ("Para o professor — conferir
muitos jogos de uma vez").

### Correções

| # | Defeito | Prova | Conserto |
|---|---|---|---|
| C1 | Toda abertura faz uma cópia em `backup\` e, com o rodízio de 3, três aberturas apagam as cópias anteriores | Visto na Fase 0: `backup\2026-10-07_204120`, `_205024`, `_205356` nasceram 20–25 s depois de cada abertura das medições, e as de 05/10 sumiram. Causa: `VIGIA["internet_estava_fora"]` começa `True` (`arena.py:3747`) e a primeira checagem com internet conta como "voltou" (`arena.py:3811`) | Começa "não sei" (`None`): só conta como "voltou" depois de ter estado fora de verdade |
| C2 | Importar o pacote de progresso grava o save direto no nome final (`arena.py:2908`): se cair no meio, fica um save cortado, e a próxima importação o pula ("já existe") | Leitura do código | Temporário ao lado + `os.replace` |
| C3 | Quando a configuração do PCSX2, do Dolphin, do Xenia ou do RPCS3 não grava (pasta somente leitura, disco cheio), o emulador abre com a configuração velha (controle, qualidade) e ninguém fica sabendo por quê | `graficos.escrever_config_*` devolve `None` e `arena.py:2381/2437/2449` só fala quando dá certo | Aviso na janela preta dizendo o que não gravou e por quê |
| C4 | Opção avançada com nota mínima que a máquina não alcança volta a valer quando o pen drive vem de um PC mais forte: a "Resposta instantânea" ligada num i5 religa no Celeron por cima da trava da `arena.py:1484` | `arena.py:1486` aplica `config["avancado"]` inteiro depois da trava; a tela só esconde a opção (`arena.py:999`) | As opções avançadas acima da nota desta máquina voltam ao padrão do ARENA (`AVANCADO_PADRAO`, sempre o desligado) e, as que não têm padrão, ficam com o que o perfil de imagem manda (vale para as 8 com `nota_minima`). Só tirar a opção não bastava — a primeira versão do conserto fazia isso, e o `teste_multitap_regra_de_ouro` pegou: três delas (`run_ahead_frames`, `run_ahead_secondary_instance`, `rewind_buffer_size`) nenhum perfil escreve, e o RetroArch guarda no `retroarch.cfg`, ao fechar, o valor que recebeu no PC forte (`config_save_on_exit`). Com o padrão, o arquivo da partida de toda máquina com a configuração padrão fica igual ao de antes |
| C5 | Descoberta de colegas: um pacote UDP torto (porta que não é número, JSON que não é objeto) derruba a linha que escuta a 55436, e a lista de vizinhos não tem limite (pacotes com códigos inventados a enchem) | `int(dados.get("porta") ...)` fora do `try` em `anunciar_e_escutar`; poda só por tempo (60 s). **Reproduzido** pelo `testes\teste_descoberta_pacote_torto.py` na rodada de referência: depois dos pacotes tortos, nenhum colega novo entrava mais | `receber_grito()` separada (testável), tudo o que vem da rede conferido (porta só de 1 a 65535 — sem porta vale a padrão, mas porta `0`, texto ou `true` recusa), no máximo 4 colegas por endereço e 200 no total, poda no máximo uma vez por segundo, apelido limpo como o resto do ARENA. Depois: 6 de 6 |
| C6 | **Achado no caminho:** um ARQUIVO com o nome de uma pasta do ARENA (`backup`, `saves`, `dados`...) derrubava o ARENA na abertura, com o erro cru do Windows, antes de a tela abrir | Reproduzido ao portar o teste da cópia que falha: `FileExistsError` em `os.makedirs` de `arena.principal()` | A pasta que não dá para criar vira aviso na janela preta ("renomeie o arquivo e abra o ARENA de novo") e o ARENA abre; quem precisa da pasta explica depois (a cópia de segurança diz "Nada foi apagado") |
| C7 | **Achado no caminho:** a foto do perfil antiga era apagada ANTES de a nova estar gravada (pen drive cheio = aluno sem foto nenhuma); e um temporário de gravação interrompida (`foto.png.1234.tmp`) podia ser servido como se fosse a foto | Leitura do código ao portar o `teste_perfil_foto`; os dois casos reproduzidos na bateria (`TestFotoDoPerfil`) | A antiga só sai depois que a nova está inteira no lugar; a foto é procurada só pelos nomes certos (`foto.png`, `foto.jpg`, `foto.webp`) |

**Revisão de segurança do C5 (08/10/2026, depois do commit da fase).** Um
revisor automático de segurança apontou "negação de serviço / limite
contornável" na descoberta. Conferido: a primeira versão do C5, com a lista
cheia, **tirava o colega mais antigo** para dar lugar ao novo — e gritos com
endereços inventados empurrariam para fora os colegas de verdade. Endurecido
(commit próprio, com 3 testes novos na bateria e o `teste_descoberta_pacote_torto`
ampliado):
- lista cheia (200 no total ou 4 do mesmo endereço): **quem já está fica**, e o
  novo espera vagar (quem some sai em 1 minuto);
- um código que **já está no ar em outro endereço** não é tomado; o computador
  que mudou de endereço de verdade volta em até 1 minuto (e o de dois
  adaptadores de rede para de trocar de endereço a cada grito).

Uma terceira proteção (no máximo 10 gritos por segundo por endereço) entrou e
**saiu** no mesmo dia: a segunda revisão de segurança mostrou que, com o
endereço de origem falsificado, alguém gastaria a cota de um colega de
verdade e o faria sumir da lista — e contar o pacote custa quase o mesmo que
lê-lo. Há um teste na bateria para isso não voltar.

**Limites que ficam (sem conserto possível sem senha):** a descoberta não tem
autenticação. Na mesma rede, alguém pode anunciar com o código de outro aluno
**enquanto esse aluno está desligado** (e a lista mostraria o endereço
errado), e uma enxurrada de pacotes na porta 55436 gasta processador (como em
qualquer programa que escuta a rede). Vai para o roteiro de sala de segurança
(Fase 3).

### Testes consertados (higiene)

| Teste | O que estava errado | Conserto |
|---|---|---|
| `teste_ps2_sem_bios`, `teste_multitap_regra_de_ouro`, `teste_kof2002_convertido` | Esperavam o ARENA de antes de 03/10 (ver "Rodada completa", Fase 0) | Expectativa nova, com o motivo comentado em cada um |
| `teste_pcsx2_portatil` | Gravava no `PCSX2.ini` de verdade e não devolvia (a rodada devolvia) | Guarda e devolve, como o `teste_pcsx2_inicia`; jogo pelo `jogos_de_teste.achar` |
| `teste_fase7`, `teste_pasta_somente_leitura`, `teste_sinc_migracao_e_lotes` | `shutil.rmtree(..., ignore_errors=True)` desistia calado de arquivo somente leitura ou preso: pasta esquecida no Temp | `limpeza.apagar_pasta` |
| `teste_netplay_isolamento` | Devolvia "passou" SEMPRE, sem conferir nada; e não apagava a pasta | Confere que o hospedeiro viu o jogador 5 entrar; apaga a pasta |
| `teste_netplay_5_jogadores` | Deixava a pasta de propósito ("rode de novo para limpar") | Guarda os registros só quando falha |
| `teste_sinc_migracao_e_lotes` | O `with sqlite3.connect(...)` do próprio teste não fecha a conexão (no Python ele só confirma a transação): o `arena.db` da cópia ficava preso e a pasta não saía do Temp | `contextlib.closing` |
| `teste_descoberta_30_maquinas` | Mandava os 30 "computadores" do mesmo endereço (127.0.0.1); com o C5 (no máximo 4 por endereço) só 4 entravam | Cada máquina falsa sai do seu próprio 127.0.0.N, como na sala (cada computador com o seu endereço): 30 de 30 |

**Não feito, com o motivo:** 25 scripts de `testes\` usam a porta 8777 fixa
(a do ARENA de verdade). Trocar todos por porta livre é uma reforma grande
dos testes, sem ganho para o aluno; a rodada já exige o ARENA fechado
(memória "rodada completa"). O teste novo desta fase (`teste_comecar_do_zero`)
já nasce com porta livre.

### Resultado da Fase 1 (08/10/2026)

| | Antes | Depois |
|---|---|---|
| Bateria (`servidor\tests\run.py`) | 203 (212 com os 9 trazidos) | **232**, todos passando |
| Testes da área mexida (20 scripts, `rodada_final.py` com pedaços de nome) | — | **20 de 20** (18 na primeira passada; as 2 falhas eram o C4 incompleto e o teste dos 30 computadores, os dois acertados e repetidos) |
| `fuzz_rotas` | 279 checagens, 0 falhas | 279 checagens, 0 falhas |
| `teste_descoberta_pacote_torto` | 2 de 6 (o defeito C5) | 6 de 6 |
| Arquivos em `ferramentas\` | 44 | 19 |
| O que saiu | | `graficos.jogo_suporta_multitap` e `como_colocar._tem` (22 linhas); 25 arquivos de ferramenta e teste antigos (2.700 linhas), cobertos por 15 testes novos na bateria e 1 script em `testes\` (mais 14 testes das correções C1 a C5) |
| Programa (`arena.py`, `graficos.py`, `como_colocar.py`) | | +184 / −83 linhas (as correções C1 a C7, quase tudo comentário e conferência do que vem da rede) |

**Como testar (o professor):** `RODAR_TESTES.bat` (a bateria: 232 testes,
~8 s). Para ver o C6 com os próprios olhos: numa CÓPIA do ARENA, crie um
arquivo de texto chamado `backup` (sem extensão) no lugar da pasta `backup` e
abra o `ARENA.bat` — a tela abre, e a janela preta avisa "nao consegui criar a
pasta backup". Os scripts da fase: `testes\teste_comecar_do_zero.py`,
`testes\teste_descoberta_pacote_torto.py`, `testes\teste_descoberta_30_maquinas.py`
e `testes\teste_multitap_regra_de_ouro.py`.

---

## Fase 2 — Leveza e desempenho (08/10/2026)

Medido no Ryzen (a régua é o Celeron N5100: por núcleo, ele tem 43% do
Ryzen, então 1 ponto daqui vale ~2,3 pontos lá — `docs\MAQUINA-ALVO.md`).
Números brutos em `docs\auditoria3\` (`*_fase2_antes.json`,
`*_fase2_depois.json`, `fundos_antes.json`, `fundos_depois.json`).

### O que mudou, com número antes e depois

| # | O quê | Antes | Depois | Como foi medido |
|---|---|---|---|---|
| L1 | **Abertura até a tela pronta** | 2,57 s (1,0 s era uma espera fixa antes de abrir a janela, sem motivo registrado: a porta já escutava) | **1,63 s** (−37%) | `testes\linha_base.py`, antes e depois |
| L2 | **Gravação no disco a cada abertura** | 43 operações, **8.264 KB** (o teste de velocidade do disco gravava até 8 MB no pen drive a cada abertura) | 35 operações, **72 KB** (−99%): a medida do disco vale 7 dias para o mesmo computador e o mesmo disco (`dados\disco_medido.json`, até 64 computadores) | `testes\medir_gravacoes_parado.py 60 --abertura` |
| L3 | **Cópia de segurança** | Uma cópia a cada chamada, mesmo sem nada mudado (o rodízio de 3 jogava fora as de outros momentos), com o cache de sombreadores do PSP junto | Só quando algo mudou (tamanho, data e, na dúvida, o conteúdo: o save de cartucho tem sempre o mesmo tamanho e o FAT32 guarda a hora de 2 em 2 s); sem `CACHE` e sem `.netplay`. O botão "Fazer cópia" diz quando nada mudou | `testes\teste_backup_rodizio.py` 12 de 12; 7 testes na bateria |
| L4 | **Fundo animado** (tela parada, cópias isoladas) | **7,7%** de um núcleo (média de 6 amostras): 30 quadros/s, acordando a cada quadro da tela (`requestAnimationFrame`, 60 por segundo) | **5,0%** (−35%): 20 quadros/s por relógio (`setTimeout`), sem desenhar com a janela escondida. No Celeron: de ~18% para ~11,5% de um núcleo, só com o menu aberto | `testes\medir_fundos.py --variante=...` |
| — | A tela parada com a configuração do Rafael (fundo "Sempre", a lista de jogos de verdade) | 9,35% | **7,64%** | `testes\linha_base.py` |

**As variantes do fundo** (% de um núcleo, claro Automático / escuro Sempre):

| Variante | Amostras | Média |
|---|---|---|
| Como era: 30 quadros, `requestAnimationFrame` | 6 | 7,72% |
| 30 quadros por relógio | 2 | 9,56% — **pior** (por isso não 30) |
| 20 quadros, `requestAnimationFrame` | 6 | 6,03% |
| **20 quadros por relógio (escolhida)** | 6 | **4,99%** |

Os casos "parado" (Automático com o Windows pedindo menos movimento, modo
modesto, "Parado") deram de 0,3% a 2,2% nas medidas de depois, mais que
antes (0,3% a 0,45%) — mas a segunda repetição pegou a janela **escondida**
num dos casos (o computador estava em uso, com outra janela por cima), e o
que decide é o `testes\teste_fundos_animados.py`: "parado não gasta
processador (0,1 ms de script em 4 s)", 29 de 29 com o código novo. No
parado nenhum laço roda (antes e depois).

### Conferido, sem mudança

| Item | Resultado |
|---|---|
| Processador com o servidor parado | 0,03% de um núcleo (nada a fazer) |
| Registros (logs) | O do RetroArch gira (ficam 10); o de quedas tem teto (128 KB, com rodízio); os de tempo de jogo (`.lrtl`) têm 130 bytes por jogo |
| CSS sem uso | 29 classes parecem sem uso, mas todas são montadas por pedaço no JavaScript (8 prefixos: `midia--`, `jogo--`, `sinal--`, `capa-`...). Nenhuma sai |
| JavaScript sem uso | Nenhuma função definida e nunca chamada (`app.js` e os fundos) |
| `id` da tela sem uso | 14: 11 são alvo de `aria-labelledby`/`aria-describedby` (acessibilidade) e 3 são inofensivos (elementos com classe própria). Ficam |
| Imagens da tela | Nenhuma: a tela tem 6 arquivos, 340 KB ao todo (`app.js` 169 KB) |
| **Estresse do catálogo** | 5.000 jogos falsos em 3 consoles: **5.125 jogos indexados em 7,07 s** (0,14 s por 100 jogos; o teto do notebook-alvo é 1,9 s por 100), releitura pelo cache em 0,05 s, tudo apagado no fim. A auditoria 1 deu 1,48 s: o indexador cresceu (capas, nomes de fliperama, BIOS, aviso de disco na pasta errada). Se a tela continua respondendo durante a indexação: Fase 3 (concorrência) |
| Fundos no computador fraco | No Automático, o fundo para sozinho com o modo modesto ou com o Windows pedindo menos animação (o "Sempre" é escolha do aluno e anima mesmo assim) |
| Orçamentos no modo alvo | Nenhum estourou. Uma passada deu 8,3% de variação dos quadros do SNES (teto 5%); repetida em seguida, **2,99%** e 60,0 FPS: interferência do momento (rodou logo depois do teste dos fundos, de madrugada), não da mudança — a medida do SNES usa as opções do ARENA, que a Fase 2 não toca |

### Também nesta fase

- **Segunda revisão de segurança da descoberta** (ver Fase 1, C5): o limite de
  10 gritos por segundo por endereço saiu.
- **Guias:** o guia 1 tinha 4 frases com a referência faltando desde a base
  de setembro ("pule para o deste documento", "veja o **neste mesmo
  documento**") e o guia 5, uma; o LEIA-ME mostrava `jogos\\pessoais` com
  barra dupla (17 trechos de código); o LEIA-ME e o guia 2 falavam em 47
  pastas de console (são 52).

### Resultado da Fase 2

| | |
|---|---|
| Bateria | **246**, todos passando |
| Testes da área (`rodada_final.py`: fundos, rodízio, Começar do zero, orçamentos, estresse, pasta movida, somente leitura, arquivos corrompidos, servidor que cai, fase 7) | 11 de 11 (as 2 falhas da primeira passada: o rodízio — defeito real do L3, consertado — e a variação do SNES, repetida e normal) |

**Como testar (o professor):** abra o `ARENA.bat` — a tela aparece cerca de
1 segundo mais cedo. Abra e feche o ARENA duas vezes e confira a pasta
`backup`: nenhuma cópia nova nasce só por abrir. Jogue, salve, feche o
jogo: aí sim nasce uma cópia (e só uma, se nada mudou depois). No tema
escuro com o fundo animado, o céu continua se mexendo (20 quadros por
segundo).

---

## Fase 3 — Servidor e API (08/10/2026)

### O que foi conferido, e o resultado

| Item do roteiro | Como | Resultado |
|---|---|---|
| Todas as rotas com dados certos, faltando, tipo errado, texto gigante, acento e emoji, `..\..\`, pedidos repetidos | `testes\fuzz_rotas.py` (64 pares rota + método) | **279 checagens, 0 falhas** |
| Pedidos que tentam derrubar o servidor (corpo torto, conexão presa, 200 conexões paradas, cabeçalhos estranhos) | `testes\teste_quebrar_api.py` | 10 de 10; com 200 conexões paradas, a tela ainda responde em 0,01 s |
| Sair da pasta pela rota da capa | `testes\teste_travessia_capa.py` | 6 tentativas (`..\`, `../`, caminho absoluto), todas bloqueadas |
| 50 pedidos ao mesmo tempo | `testes\teste_concorrencia.py` | 0 respostas 5xx; `config.json` e `controles.json` válidos; `arena.db` íntegro (`PRAGMA integrity_check`) |
| Longa duração (acelerada) | `testes\teste_longa_duracao.py` | 45.626 pedidos, 0 falhas de conexão; memória +0,4 MB e alças +2 depois de aquecer |
| Quem da rede chama o quê (a) | `testes\teste_acesso_de_rede.py` | Só as 8 rotas da partida e da sincronização atendem outro computador; as outras (inclusive as 5 novas de 03/10: BIOS e Arrumar) respondem 403, e a configuração não muda |
| Site qualquer mandando comando (b): outra origem e DNS rebinding | `testes\teste_dns_rebinding.py` + `Content-Type` obrigatório | Host de site estranho: 403; a configuração não muda |
| "Aceitar conexões da rede" sem reabrir | `testes\teste_rede_sem_reabrir.py` | Liga e desliga na hora, aguenta 12 cliques colados |
| Acervo com SHA-256 errado | `testes\teste_acervo_sha256.py` | Recusado |
| Sem internet | As funções locais não usam a rede (inventário da Fase 0, "O que depende de internet"); o vigia marca "sem internet" e as online avisam | — |
| **Internet ruim** (DNS que falha, servidor mudo, conexão recusada, a página de login do Wi-Fi) | **Novo:** `testes\teste_internet_ruim.py`, com um servidor falso neste computador | **13 de 13** depois dos consertos abaixo |

### Achados e consertos

| # | Defeito | Prova | Conserto |
|---|---|---|---|
| A1 | **A tela inteira parava enquanto o ARENA relia os jogos** ("Atualizar lista", ou depois de baixar/mover/arrumar um jogo): a releitura segurava, do começo ao fim, a mesma trava que a leitura da configuração usa — e quase toda rota lê a configuração | **Novo** `testes\teste_tela_responde_indexando.py` (5.000 jogos falsos numa cópia isolada): durante a releitura de 3,4 s, o único pedido da tela esperou **3,30 s** | A releitura ganhou a sua própria trava; a da configuração só é segurada para ler e gravar o resultado. Depois: **17 pedidos atendidos durante a releitura, o mais lento em 0,02 s**. No Celeron, com muitos jogos, a releitura passa de 15 s: era tela congelada esse tempo todo |
| A2 | **Biblioteca online: "nenhum resultado" quando a rede tinha falhado** — inclusive quando a rede da escola devolvia a página de login do Wi-Fi no lugar dos dados (o vigia testa a internet pela porta 53, que o portal costuma deixar passar) | Leitura do código: `buscar()` devolvia `[]` em qualquer erro | Falha de rede e página de login viram frase própria: "Não consegui falar com o Internet Archive agora (a internet caiu ou está muito lenta)..." e "A rede pediu login: chegou a página do Wi-Fi... Abra o navegador, entre na rede e tente de novo." |
| A3 | **Biblioteca online: uma rede lenta prendia a tela por minutos** — as fichas dos jogos eram pedidas uma de cada vez, até 30 pedidos de até 20 s | Teste: 12 fichas de 1 s cada | As fichas vêm ao mesmo tempo (10 por vez, 10 s cada): **12 s → 2,1 s**. Servidor mudo: desiste no tempo-limite, sem travar |
| A4 | **Download da biblioteca e do acervo: a página de login no lugar do jogo** dizia só "SHA diferente" | Teste com o portal falso | Frase do login (e nada fica na pasta de jogos, nem pela metade) |
| A5 | **Capa: "Não achei capa" quando foi a rede** (o caso do GameCube na rodada de referência) | Teste: conexão recusada e portal | A busca anota as falhas de rede e de login e diz a causa certa; com a rede caída, desiste depois de duas falhas (**18 s → 6 s**), sem deixar de tentar antes a capa de dentro do disco (PS3, PSP), que não usa rede |
| A6 | **Mensagens de erro sem "o que fazer"**: 25 do servidor, 3 da tela (em 4 lugares) e mais 38 frases dos outros módulos (acervo, Internet Archive, cheats, controles, capas, barreiras, foto do perfil, pacote de progresso) | `servidor\tests\test_mensagens_de_erro.py` (6 testes na bateria) lê o código e reprova a frase nova sem verbo de ação ("clique", "escolha", "tente", "peça"...) — com a lista das internas que o aluno não vê, cada uma com o motivo | Todas reescritas com as duas partes. Ex.: "Limite de 20 amigos." → "Você já tem 20 amigos, o máximo. Remova um (Perfil → Amigos) para adicionar outro."; "Arquivo grande demais para o Arena." → "O arquivo passa de 4 GB, o limite do ARENA. Escolha outro jogo." |

**Limite que fica (vai para o roteiro de sala):** a descoberta de colegas não
tem autenticação (ver Fase 1, C5), e os testes que sobem o servidor usam a
porta 8777 fixa em 25 scripts (a rodada exige o ARENA fechado).

### Resultado da Fase 3

| | |
|---|---|
| Bateria | **252**, todos passando (6 novos das mensagens) |
| Testes de servidor e API (`rodada_final.py`, 23 scripts) | **23 de 23** |

**Como testar (o professor):** com o ARENA aberto e uma pasta de jogos
grande, clique em **Atualizar lista** e, enquanto ele relê, abra os Ajustes:
a tela responde na hora. Na biblioteca online, sem internet (Wi-Fi
desligado), procure "pac": a tela diz que a internet caiu, não que não há
jogos. Num Wi-Fi com página de login, antes de fazer o login, a busca diz
que a rede pediu login.

---

## Fase 4 — Jogar Junto (08/10/2026)

Num computador só, com RetroArch de verdade (Super Bomberman 4, SNES).
Números brutos em `docs\rede_ruim_bruto.json`, `docs\cenarios_sala_bruto.json`,
`docs\netplay_5_jogadores_bruto.json` e `docs\matriz_multitap_bruto.json`.

### O que foi conferido, e o resultado

| Item do roteiro | Como | Resultado |
|---|---|---|
| Hospedeiro e 4 convidados (5 RetroArch, cada um com a sua configuração, os seus saves e a sua pasta) | `testes\teste_netplay_5_jogadores.py` | Os 4 entram, **0,9 s cada**, ping de 11 a 17 ms; memória do hospedeiro 318,5 MB com 2 jogadores e 318,7 MB com 5 |
| 5 jogadores com o Multitap (o ARENA liga sozinho nos jogos da lista; `netplay_max_connections` = 4 só com o Multitap, o padrão do RetroArch é 3) | `teste_multitap_5_jogadores_arena`, `teste_matriz_multitap` (11 consoles), `teste_multitap_regra_de_ouro`, `teste_netplay_isolamento` | Todos passam. O jogador 5 entra sozinho e entra com os outros 3 |
| Sexto jogador tentando entrar | **Novo:** `testes\teste_netplay_sexto_jogador.py` | Recusado, e os 5 continuam jogando (4 de 4). O RetroArch só escreve "Falha ao conectar ao host": agora o ARENA explica (J3) |
| Convidado que cai e volta; hospedeiro que sai no meio; convidado que entra com a partida já começada | `teste_cenarios_sala.py` (cenários 1 e 2); no teste de 5, cada convidado entra com o jogo rodando | Reconecta; o convidado percebe a queda e não trava; entra no meio sem problema |
| Duas partidas diferentes ao mesmo tempo | `teste_cenarios_sala.py` (cenário 3) | **Nunca tinha passado** ("misturou" desde a auditoria 1, e o teste saía com 0). Causa e conserto em J1. Agora: as duas conectam e não se misturam (3 de 3 cenários) |
| Simulador de rede ruim (50, 100 e 200 ms; 1% e 5% de perda) | `testes\proxy_rede_ruim.py` + `teste_rede_ruim.py` | **O convidado nunca tinha passado pelo simulador** (J1). Refeito; resultado na tabela abaixo |
| 30 computadores anunciando ao mesmo tempo | `teste_descoberta_30_maquinas.py`, `teste_descoberta_pacote_torto.py` | Os 30 na lista, `/api/colegas` em 0,001 s, servidor a 0,0% do processador |
| O mesmo recorde vindo de dois lugares; relógio errado; FAT32 | `teste_sinc_migracao_e_lotes.py`, `teste_sinc_sem_relogio.py`, `teste_mala_validacao.py`, leitura do código da mala | Não duplica (identificação única por registro); o recorde gravado com o relógio em 2020 chega ao colega; a mala do pen drive compara pela identificação, não pela data do arquivo (a hora de 2 em 2 s do FAT32 não importa) |
| 4 jogadores no mesmo computador (GoldenEye 007 e outro de 4) | `teste_local_4_jogadores.py`; com os controles na mão em 25/09 (Mega Bomberman, Micro Machines 2, CTR, GoldenEye, `docs\MAPA-MULTITAP.md`) | Abre com as 4 portas; teclado vai para o primeiro jogador sem controle |

### Rede ruim: o que o jogador sente

Jogadores parados (sem botão apertado), 12 s jogando depois de entrar
(`docs\rede_ruim_bruto.json`, depois da revisão).

| Rede entre os dois | Entrar na partida | Ping que o RetroArch mostra | A partida caiu? | Pedaços pelo simulador (ida / volta) |
|---|---|---|---|---|
| Direta (referência) | 0,8 s | 28 ms | não | — |
| 50 ms de atraso | 1,0 s | 128 ms | não | 855 / 866 |
| 100 ms | 1,3 s | 228 ms | não | 835 / 857 |
| 200 ms | 1,8 s | 428 ms | não | 802 / 839 |
| 50 ms + 1% de perda | 1,0 s | 112 ms | não | 856 / 867 (17 "perdidos") |
| 50 ms + 5% de perda | 1,0 s | 112 ms | não | 839 / 868 (78 "perdidos") |

O ping é ida e volta (2 × o atraso). **Medido:** em todas as redes ruins o
convidado entrou e a partida não caiu; o atraso aparece na hora de entrar e
no ping. **Não dá para medir aqui** (a revisão da Fase 4 pegou, e as duas
medidas saíram do teste): os quadros por segundo da janela não mostram
travada (enquanto o Jogar Junto espera a rede, o RetroArch redesenha o
último quadro e o contador segue em 60), e a dessincronia não aparece no
registro (com a conferência a cada 600 quadros, o RetroArch corrige a
diferença calado).
**O que se espera com botões** (pelo jeito que o Jogar Junto do RetroArch
funciona; só a sala confirma): o seu boneco responde na hora; o do amigo
chega atrasado e o RetroArch "volta no tempo" para corrigir, e ele dá um
pulinho para a posição certa. Com ping perto de 100–200 ms isso quase não
aparece; perto de 400 ms (200 ms de atraso), num jogo rápido como o
Bomberman, o boneco do amigo "teleporta" quando muda de direção. Com perda,
um pedaço atrasado segura tudo o que vem atrás (é assim no TCP): um soluço
curto, de uns 0,3 s.

### Achados e consertos

| # | Defeito | Prova | Conserto |
|---|---|---|---|
| J1 | **A porta da partida ia com o nome errado** (`netplay_port`; o do RetroArch é `netplay_ip_port`), e o `--port` da linha de comando é ignorado. Na escola não estragava nada (a porta padrão é a mesma, 55435), mas **dois testes nunca mediram o que diziam**: o convidado do teste de rede ruim ia direto ao hospedeiro (por isso o ping ficava em ~11 ms com 200 ms de atraso pedido, nas auditorias 1 e 3), e as duas partidas do teste de sala caíam na mesma porta | `netstat` com dois hospedeiros pedindo 55437 e 55438: os dois escutando na **55435** (o Windows deixa dois programas na mesma porta); os dois convidados entraram no mesmo hospedeiro | A chave certa no arquivo da partida; os dois testes põem a porta em cada RetroArch e conferem: o de rede ruim reprova se o simulador não receber a conexão, o de sala reprova se um cenário falhar |
| J2 | **Mais 8 chaves que o RetroArch não conhece**, todas ignoradas em silêncio: o espaço inicial do save state (`savestate_slot`; o certo é `state_slot`), o tema do menu do Esc (pedia o 27, valia o verde clássico do RetroArch), a largura do menu, o "Importar conteúdo" escondido, o atalho de gravar a partida (replay) e 4 que não existem mais. **Efeito na tela: nenhum** — conferido no RetroArch de verdade: ele já volta ao espaço 0 a cada jogo aberto (até com a configuração pedindo o 3), e o resto já era o padrão dele. É código que mentia sobre o que fazia | **Novo** `servidor\tests\test_chaves_do_retroarch.py`: gera o arquivo de opções de verdade com cada perfil, motor gráfico, modo e tipo de partida, com as 50 opções avançadas, e confere cada chave contra o `retroarch.cfg` (o RetroArch grava nele todas as que lê, ao fechar; os textos do `retroarch.exe` deixaram de valer na revisão, porque lá também estão os nomes internos do menu). O espaço: SNES aberto 3 vezes com cópias da configuração (espaço 3 na principal, no arquivo extra, nos dois): o save caiu no espaço 0 nas três | Nome certo: `state_slot` = 0 (fica por garantia: se um RetroArch novo passar a lembrar o espaço, o próximo F2 regravaria o 9, o "seguro" do guia 4); `rgui_menu_color_theme` = **4**, o verde clássico que os alunos sempre viram (o 27 nunca valeu, e trocar agora seria surpresa); `menu_rgui_full_width_layout`; `content_show_add_entry` = 0; `input_record_replay`/`input_play_replay`/`input_halt_replay` = sem tecla. **Saíram** (não existem no RetroArch desta pasta, nem no programa nem no `retroarch.cfg`): `quick_menu_show_cheevos` (as conquistas já ficam desligadas), `notification_show_recording`, `notification_show_streaming` (a gravação já está desligada) `netplay_stateless_mode` (o modo saiu do RetroArch) e, achada na revisão, `menu_show_legacy_thumbnail_updater` (o atualizador inteiro já fica escondido) |
| J2b | **11 chaves repetidas** no `BASE_COMUM` (blocos inteiros colados duas vezes, com os mesmos valores): a próxima mudança numa das cópias não valeria | O mesmo teste novo: lê todos os dicionários do servidor | Ficou uma de cada |
| J3 | **Sexto jogador sem explicação**: só "Falha ao conectar ao host", e o aluno acha que é a rede | `teste_netplay_sexto_jogador.py` (que agora confere a frase que o ARENA mostra) | `motivo_do_erro.motivo_da_partida`, no alto da tela ao voltar, com uma frase para cada caso que o RetroArch escreve: o anfitrião disse que está cheio ("a partida está cheia (este jogo aceita até 5 jogadores). Espere alguém sair, ou abram outra partida"); a entrada foi recusada, o caso do sexto ("Ela pode estar cheia: este jogo aceita até 5 jogadores. Pergunte a quem hospeda quantos já entraram; se ainda tem vaga, rode o PARTIDA.bat..."); ninguém atendeu no endereço ("o computador de quem abriu a partida não respondeu. Confira se o jogo dele já está aberto na tela... a rede pode estar barrando... PARTIDA.bat") |
| J4 | **Rede Pública: só o PARTIDA.bat percebia**, e só se o aluno rodasse | Leitura do código | Com a janela do Jogar Junto aberta, o ARENA pergunta ao Windows a categoria de todas as redes ligadas (sem administrador, em segundo plano; resposta de mais de 10 min não vale). Quem **abre** a partida numa rede Pública vê, fixo no alto da tela até o jogo fechar, o aviso com a saída que não pede senha: outro computador abre e este entra (quem entra só faz conexão de saída). O PARTIDA.bat diz o mesmo. 4 testes na bateria |
| J8 | **"Estamos em casas diferentes" nunca funcionou** (achado da revisão desta fase). Com a chave, o anfitrião vai pelo repasse da internet e deixa de atender na rede local; o convidado, que o ARENA manda para o endereço do anfitrião, nunca chega ao repasse. A primeira versão do aviso da rede Pública (J4) indicava a chave como saída | RetroArch de verdade: anfitrião com o repasse, convidado como o ARENA o abre: a 55435 não escuta e o convidado recebe "Failed to connect to host 127.0.0.1 on port 55435" | A chave saiu da tela (o código ficou) até o convidado entrar pelo repasse de verdade: o RetroArch tem `--mitm-session` para entrar numa sala do repasse, e falta o ARENA passar o "código da sala" de um para o outro, com teste entre duas casas (pendência). O aviso e o PARTIDA.bat não a indicam mais; o guia 5 explica, e perdeu a dica "ligue casas diferentes, que entra com folga" |
| J5 | **Wi-Fi que isola os aparelhos**: o PARTIDA.bat dizia só "confira se estão na mesma rede" | Leitura | Agora: "Se estão no mesmo Wi-Fi e mesmo assim não alcança, o Wi-Fi pode estar isolando os aparelhos (comum na escola): liguem o ponto de acesso de um celular e conectem os dois nele, ou liguem um cabo direto". Na tela, quando nenhuma partida aparece, a dica do que conferir (`#dicaSemPartida`) |
| J6 | **O simulador de rede ruim atrasava de 1 a 2 vezes o pedido** (dormia o atraso na mesma linha que lia) | Leitura do código | Uma linha lê, outra entrega cada pedaço no instante chegada + atraso, em ordem; a "perda" é o reenvio do TCP (uma volta + 200 ms, segurando o que vem atrás) |
| J7 | **O teste da mala deixava `ARENA-troca.json` solto no Temp do Windows** (com os recordes da cópia) a cada rodada | O arquivo no Temp, de 16h27 (a rodada da Fase 4) | O ARENA de teste numa subpasta, como os outros testes; a sobra foi apagada |

**Conferido, sem mudança:** o cabo direto (169.254) aparece como "Cabo
direto entre dois PCs" e o grito também sai pelo endereço dele; os pontos de
acesso de Android (192.168.43.x) e iPhone (172.20.10.x) são reconhecidos
(`teste_adaptadores_vpn.py`); adaptador virtual e VPN vão para o fim da lista,
marcados; o amigo salvo é achado de novo quando o endereço muda (pelo código
do aparelho no grito).

### Roteiro de sala — Jogar Junto (5 notebooks)

O passo a passo completo do Multitap continua em `docs\ROTEIRO-MULTITAP.md`.
O que entra de novo nesta fase:

1. **Rede Pública.** No notebook que vai abrir a partida, confira em
   Configurações → Rede e Internet se a rede é "Pública". Abra a partida:
   o ARENA tem que avisar, fixo no alto da tela, e dar a saída. Anote se outro notebook
   consegue entrar mesmo assim (o Firewall pode pedir senha de
   administrador: anote o que aparece). Depois troque quem abre: um
   notebook que só ENTRA tem que conseguir.
2. **Sexto jogador.** Com a partida de 5 cheia, um sexto notebook tenta
   entrar. Anote a frase que aparece no alto da tela dele ao voltar.
3. **Wi-Fi da escola.** Os dois notebooks no Wi-Fi da escola: a partida
   aparece na lista? Se não, rode o PARTIDA.bat nos dois e anote o que
   ele diz. Repita no ponto de acesso de um celular (Android e iPhone).
4. **Rede ruim, com botões.** Um notebook perto do roteador e outro longe
   (ou com o celular como ponto de acesso, e alguém vendo vídeo no mesmo
   celular). Joguem 2 minutos apertando ao mesmo tempo. Anote o ping (o
   RetroArch mostra ao entrar) e se o boneco do amigo "pula".
5. **Wi-Fi que cai.** No meio da partida, desligue o Wi-Fi de quem entrou
   por 10 s e religue. Anote o que cada um vê e se dá para entrar de novo.
6. **Notebook que dorme.** Feche a tampa de um convidado por 1 minuto,
   abra, e confira se ele aparece de novo na lista de colegas.

**Como testar (o professor):** em 2 notebooks na mesma rede, os dois com
"Aceitar conexões da rede" ligado, um abre a partida e o outro entra.
Para ver o aviso de rede Pública, abra a partida num notebook com a rede
marcada como Pública (Configurações → Rede e Internet): o ARENA avisa, fixo
no alto da tela, e dá a saída (outro computador abre e este entra). Com 5
jogando o Super Bomberman 4, um sexto que tenta entrar vê, ao voltar, a
frase de que a partida pode estar cheia.

### Revisão independente da Fase 4 (09/10/2026)

Três revisores (as chaves do RetroArch, os testes, o código novo de produto)
leram o commit da fase sem rodar nada, e cada achado foi conferido aqui (o
verificador automático caiu no limite de uso). **Os 15 eram reais**, e todos
foram consertados:

| Achado | O que mudou |
|---|---|
| O teste das chaves aceitava como "conhecida" qualquer palavra do `retroarch.exe`, inclusive os nomes internos do menu (ex.: `netplay_tcp_udp_port`, que parece a porta e não é) — e por isso deixava passar uma chave morta: `menu_show_legacy_thumbnail_updater` | A referência é só o `retroarch.cfg`; a chave saiu (J2) |
| O aviso da rede Pública indicava "Estamos em casas diferentes" — que não funciona | J8 |
| "Failed to connect to host 192.168.0.12 on port 55435" (ninguém atendeu) também dizia "pode estar cheia"; "Host de netplay cheio" não dizia nada | Três frases (J3) |
| O aviso da rede Pública ia num recado de 9 s, que some atrás da janela do jogo | Fixo no alto até o jogo fechar |
| A pergunta ao Windows (PowerShell) rodava em toda abertura do ARENA, e a resposta valia para sempre | Só com a janela do Jogar Junto aberta; resposta de mais de 10 min não vale |
| Só a primeira rede da lista era olhada (cabo direto + Wi-Fi) | Todas; basta uma ser Pública (no ARENA e no PARTIDA.bat) |
| O teste de rede ruim só reprovava se o simulador não aceitasse a conexão; os "60 quadros/s" e "0 dessincronia" não provavam nada | Reprova se não conectar, se cair ou se os dados não passarem pelo simulador nos dois sentidos; as duas medidas saíram (ver "Rede ruim") |
| O teste do sexto jogador aceitava qualquer "falh" ou "slot" no registro | Confere a frase que o ARENA mostra |
| A regra de ouro tirava da comparação os nomes novos para sempre (uma troca futura da porta passaria calada) | Compara pelo nome certo (a versão antiga passa por um mapa) |
| O teste da porta era pulado sem o RetroArch (a cópia do GitHub) | Em classe própria, roda sempre |

### Resultado da Fase 4

| | |
|---|---|
| Bateria | **267**, todos passando (novos: as chaves do RetroArch, a porta, as chaves repetidas, as três frases da partida, a resposta velha da rede, o FAT32 da Fase 6) |
| Testes do Jogar Junto (`rodada_final.py`) | 23 de 23 antes dos consertos J1–J2. Depois: **21 de 22**; a falha foi a `teste_multitap_regra_de_ouro`, que compara cada jogo com a versão de antes do multitap e pegou exatamente as chaves renomeadas de propósito (J2). Depois da revisão: regra de ouro, sexto jogador e rede ruim, **3 de 3**. O de sala passou a conferir as duas partidas de verdade (3 de 3) e o de rede ruim, o simulador no caminho |
