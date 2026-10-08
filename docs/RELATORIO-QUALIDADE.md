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
