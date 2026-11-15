# Desempenho do servidor: a Fase 1 do plano (14/11/2026)

Medição pedida pelo `docs\PLANO-DE-ACAO-RUST.md` (Fase 1) antes de qualquer decisão sobre trocar o servidor Python.
Nada do código mudou para medir. Versão medida: **2026.11.14**. A Fase 2 (otimizar o Python) está no fim.

## Os números

| Medida | Galaxy A12 (Android 12, MT6765, 3,7 GB) | PC no modo alvo (perfil do Celeron N5100) | Limite do plano |
|---|---|---|---|
| Memória do servidor | **41,5 MB** (pico 47,6 MB), processo `libarenapython.so` | **59,2 MB** de pico (`teste_orcamentos_modo_alvo`, item 2) | 150 MB |
| Processador com o servidor parado | **0,43%** de um núcleo (13 de 3000 centésimos em 30 s, tela do ARENA aberta) | **0,23%** de um núcleo (item 3; cerca de 0,5% num núcleo do Celeron) | 1% |
| Abertura do servidor | **cerca de 5 s** do toque no ícone até a lista na tela (abaixo) | **1,14 s** do `arena.py` até os dados da tela (item 1b) | 2 s |

Memória da tela no A12, para comparar: a parte do app que desenha a tela (WebView) usa **108,6 MB** (PSS), mais que o
dobro do servidor.

### A abertura no A12, passo a passo (registro do Android, 14/11, 00h52)

| Momento | Tempo desde o toque |
|---|---|
| a tela do app aparece (`Displayed ... +701ms`) | 0,7 s |
| a porta 8777 do servidor abre (3 medidas: 1,95; 1,12; 0,89 s) | 0,9 a 2,0 s |
| o servidor imprime o cabeçalho (Python carregado e o começo do `arena.py`) | 3,9 s |
| o catálogo de 2699 jogos lido do arquivo guardado (`[cache, 1.64s]`) | 5,7 s |
| "Tela do app do ARENA avisada" | 5,7 s |

## Conclusão

- **Memória e processador parado: dentro dos limites com folga**, nos dois aparelhos. Trocar o servidor por Rust não
  traria ganho que alguém sinta.
- **A abertura no celular passa do limite** (cerca de 5 s, para 2 s). Dois trechos pesam: uns 3 s entre a tela aparecer
  e o servidor terminar de carregar, e 1,6 s só para ler o catálogo de 2699 jogos já guardado. No PC o mesmo caminho
  leva 1,14 s.
- Pela regra do plano, isso abre a **Fase 2: otimizar o Python primeiro**, não o Rust. Ler um catálogo guardado não
  deveria levar 1,6 s, e a parte que mais pesa (carregar o programa) se mede módulo por módulo.

## Fase 2: otimizar o Python (feita em 14/11/2026, madrugada)

Como se mediu: o servidor agora anota no registro do Android cada etapa da abertura, contada desde que o processo do
Python nasce (`ponte_android.marca_da_abertura`, só no Android: linhas `[ARENA] Abertura, X s: ...`), e o catálogo
mostra quanto levou para conferir as pastas e para ler a lista guardada. Com o APK de teste (depurável), o próprio
Python do app rodou dentro do celular (`run-as`) com o `cProfile`. Os achados, do maior para o menor:

| Achado no A12 | Custo | Correção |
|---|---|---|
| A tela criava a WebView (o Chromium inteiro) e só **depois** pedia o servidor | ~2,7 s no APK de teste; **no de produção, nada** (A/B abaixo) | `ArenaActivity.onCreate`: o servidor começa antes da WebView (mantido: não piora e o Python nasce ~0,15 s antes) |
| A conta de velocidade do processador rodava **a cada abertura** (`hardware.velocidade_de_um_nucleo`) | ~0,9 s | `hardware.velocidade_guardada`: vale 7 dias no mesmo aparelho (`dados/processador_medido.json`), como o disco |
| O `runpy.run_path` **compilava as ~9.400 linhas** do `arena.py` toda vez | 0,63 s | `android_inicio.py` abre por `import arena` (usa o `.pyc` guardado) e chama `arena.principal()` |
| A medida do disco nunca ficava guardada no Android (sem número do volume) | 0,26 s | `hardware.numero_do_volume`: no Android, o número do dispositivo da pasta |
| Os certificados do Android eram remontados antes de o Python nascer | parte do tempo do Java | com o arquivo já feito, o servidor nasce com ele e o novo é montado em segundo plano |
| Cada APK novo regravava o `consoles.json` (data nova, conteúdo igual) e o ARENA **varria os 2699 jogos de novo** | 9 a 13 s na 1ª abertura depois de atualizar | a assinatura usa o conteúdo do arquivo (md5), não a data (`indexador.conteudo_do_consoles`) |

### Antes e depois no A12

**Dentro do Python** (do nascimento do processo até a tela avisada, mesmo celular, mesma hora, só os `.py` trocados):
**4,75 s → 2,6 a 3,0 s**. O `principal()` passou a começar em 1,4 a 1,6 s (antes 3,4 a 3,5 s).

**Do toque até a lista pronta**, APK de produção, celular parado, 4 aberturas de cada (14/11, 02h40):

| Versão | Primeiro quadro | O Python nasce | Lista pronta (mediana) |
|---|---|---|---|
| Python novo, ordem antiga da tela | 0,94 a 1,09 s | 0,79 a 0,95 s | **3,55 s** (3,48 a 4,12) |
| Python novo, servidor antes da WebView | 0,75 a 1,11 s | 0,62 a 0,99 s | **3,54 s** (3,06 a 3,77) |

A ordem da tela não mudou o total em produção: o "buraco" de ~2,7 s antes de o Python nascer era do APK de teste
(depurável, Java bem mais lento). A medida de "antes" (5,7 s, às 00h52) foi feita com o celular copiando filmes
grandes para o PC ao mesmo tempo, então não serve de comparação direta; pela parte Python medida lado a lado, a
abertura com o celular parado caiu de cerca de 5,3 s para cerca de 3,5 s. Os 1520 testes passam; no PC o
`import arena` caiu de 0,19 para 0,13 s (a conta de velocidade também fica guardada).

### O que ainda pesa (e por que não mexi agora)

- **Conferir as pastas de jogos: 0,8 a 1,0 s**, quase tudo nas pastas do **cartão SD** (64 pastas em 0,55 s; a
  memória do aparelho, 98 pastas em 0,2 s): o Android entrega o cartão por uma camada lenta (FUSE). Dar a lista
  guardada antes de conferir mudaria o que o aluno vê (o jogo recém-copiado só apareceria depois): seria regressão.
  Caminho possível, com cuidado: conferir em segundo plano e a tela se atualizar sozinha quando a lista mudar.
- **O Python nascer (0,65 s) e carregar os ~60 módulos (0,7 s)**: o próximo passo seria carregar sob demanda os
  módulos que a primeira tela não usa (capas online, recompilados, Waydroid, exportar...), medindo cada um.
- **O limite de 2 s ainda não é alcançado no A12** (cerca de 3,5 s). Pela regra do plano, o Rust continua fora: o
  ganho veio todo de corrigir trabalho repetido no Python e no Java, e o que sobra é ler o cartão e carregar o
  programa, que o Rust não tornaria mais rápidos sem reescrever o servidor inteiro.

## Fase 3: a prova em Rust (14/11/2026, manhã)

Pedido do Rafael: "finalize os testes em Rust de todas as etapas; se não for mudar tudo para Rust, pelo menos aprender
com esses testes". A prova (`ferramentas\prova_rust`, Rust só com a biblioteca padrão, compilado estático para ARM64
com o linker do próprio Rust) faz o trabalho do trecho que a Fase 2 deixou como o maior: a conferência das pastas de
jogos (`indexador.assinatura_das_pastas`). O gêmeo em Python (`medir_python.py`) faz o mesmo trabalho, e o "resumo"
impresso confere que os dois viram as mesmas pastas.

**Conferência das pastas no Galaxy A12** (134 pastas do cartão SD, os dois rodando como o mesmo app, no Termux):

| Jeito | Rust | Python |
|---|---|---|
| uma pasta de cada vez | ~370 ms | ~410 ms (o `os.walk` de antes: ~460 ms) |
| 8 pastas ao mesmo tempo | ~60 ms | ~92 ms |

Rodando pelo `adb` (outro usuário do Android), o Rust em sequência levava 190 ms: o FUSE do cartão confere a
permissão de cada app, então só vale comparar no mesmo usuário. **A linguagem muda uns 10%; perguntar ao disco em
paralelo muda 4 a 5 vezes**, nas duas. O Python faz isso com threads, porque o `os.scandir` e o `os.stat` soltam a
trava do Python enquanto esperam o disco.

**O nascimento do programa no A12:** o Python vazio nasce em ~200 ms e um programa Rust em ~27 ms. Os módulos da
biblioteca padrão que um servidor em Python precisa somam mais ~450 ms (só o `http.server`, ~300 ms). Isso o Rust
tiraria, mas só reescrevendo o servidor inteiro (9.600 linhas e 62 módulos), e o `-X importtime` mostrou que não há
um módulo do ARENA que pese sozinho: carregar sob demanda daria pouco (o `urllib.request` e o `ssl` por cima do
`http.server` ficaram dentro do ruído da medida).

### O que a prova ensinou e entrou no ARENA (em Python)

| Achado | Correção | Antes → depois no A12 (APK de produção) |
|---|---|---|
| Conferir as pastas uma de cada vez | `indexador.pastas_com_data`: por níveis, 8 ao mesmo tempo, a mesma lista de antes | conferência 1,24-1,42 s → 0,59-0,78 s |
| O `multitap.json` entrava na assinatura pela data, e cada APK novo o regrava | `indexador.conteudo_do_arquivo`: o conteúdo (md5), como o `consoles.json` | a 1ª abertura depois de atualizar varria os 2699 jogos (9,9 s); agora usa a lista guardada |
| Os 2305 recursos do RetroArch saíam do APK antes de o servidor começar | `android_inicio.tirar_em_segundo_plano`: numa thread; o jogo espera (`ponte_android.RECURSOS_PRONTOS`) | 8,6 s a menos antes do servidor |
| O celular compilava o `arena.py` e os ~60 módulos depois de cada atualização | o APK leva os `.pyc` no modo *checked-hash* (valem se o `.py` for o mesmo) | ~3,5 s a menos |
| O APK levava o `servidor/python-linux-aarch64` do Linux ARM | fora (`FORA_DO_SERVIDOR`) | 22 MB a menos no APK |

**Do Python nascer até a tela avisada**, mesmo celular:

| Abertura | Antes (14/11, 10h38) | Depois (14/11, 11h04) |
|---|---|---|
| a frio, celular parado | 2,7 a 3,6 s | **2,1 a 2,5 s** |
| a primeira depois de instalar ou atualizar o app | 13,4 s (21 s quando varria os jogos) | **2,8 a 2,9 s** |

Somando o ~0,6 s antes de o Python nascer, a abertura a frio do toque até a lista fica perto de 2,7 a 3,1 s: ainda
acima dos 2 s do portão, mas agora o que sobra é o próprio Python nascer e carregar a biblioteca padrão (~1,2 s) e o
cartão SD (~0,6 s).

## Fase 4: a decisão (14/11/2026)

**O servidor continua em Python.** Medido no aparelho mais fraco (o A12), o que deixava a abertura lenta era trabalho
repetido ou feito em série, e tudo se resolveu em Python: a abertura a frio caiu de ~5,3 s (13/11) para ~2,3 s
dentro do Python, e a primeira depois de atualizar, de 13 a 21 s para 2,9 s. O que o Rust ainda daria (~1,2 s do
Python nascer e carregar a biblioteca) exigiria reescrever o servidor inteiro, com duas bases de código, e o código
deixaria de ser material de aula legível por aluno do ensino médio. Os números e o porquê ficam também em
`docs\replica\architecture.md`.

**O que fica do Rust:** a prova em `ferramentas\prova_rust` (ferramenta de medida, fora do pacote) e o jeito de
compilar para ARM64 sem o NDK (`aarch64-unknown-linux-musl` com o `rust-lld`), que serve para medir qualquer outro
trecho no celular ou na TV Box antes de decidir. Reabrir a pergunta só se uma medida nova apontar um trecho de
processador (não de disco) que o Python não resolva.

## Fase 5: a regra mudou (14/11/2026, tarde)

O Rafael pediu desempenho máximo, "mesmo que não seja mais em Python", e a decisão da Fase 4 foi revista: o
servidor **nativo em Rust** passou a ir na frente do Python (que fica atrás, como reserva), por etapas medidas. No
A12, do toque até a lista: 6,76 s → 2,52 a 2,65 s. Como funciona, cada etapa (R1 abertura, R2 capas, R3 avisos em
tempo real) e por que as ~121 rotas restantes continuam em Python: `docs\MIGRACAO-RUST.md`.
