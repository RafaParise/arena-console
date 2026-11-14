# Desempenho do servidor: a Fase 1 do plano (14/11/2026)

Medição pedida pelo `docs\PLANO-DE-ACAO-RUST.md` (Fase 1) antes de qualquer decisão sobre trocar o servidor Python.
Nada do código mudou para medir. Versão medida: **2026.11.14**.

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

## Fase 2 (próximo passo)

1. Medir onde vão os 3 s no A12: um registro de tempo por etapa na abertura, ligado por uma variável de ambiente (só
   no APK de teste), e o `python -X importtime` com o mesmo código.
2. Medir a leitura do catálogo (1,64 s para 2699 jogos): o formato do arquivo guardado, a conferência de cada jogo e o
   que pode ficar para depois da tela aparecer.
3. Cada mudança com teste, medida de novo no A12 e no modo alvo; nada muda no PC para pior.
