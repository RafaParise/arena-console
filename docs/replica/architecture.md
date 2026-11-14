# Arquitetura: mais quadros, tela leve e o Rust (11/11/2026)

## Pilha

É a do ARENA, sem trocar nada:
- **Python 3.13** embutido, só com a biblioteca padrão;
- **RetroArch** e os emuladores de fora;
- a tela em **HTML/JS** sem framework.

Nada a instalar, nada de administrador, e todo caminho guardado é relativo.

## Ordem do "mais quadros" (do melhor para o resto)

1. **PS2 com o patch de 60 FPS do PCSX2** (`servidor\quadros_ps2.py`). O próprio jogo roda a 60: nada copiado, nada
   adivinhado, nenhum atraso a mais.
   - O serial e o CRC saem do ISO. O CRC é o "ou exclusivo" das palavras de 32 bits do ELF, conferido nos 5 ISOs.
   - Disco comprimido aprende pelo registro do PCSX2 na primeira partida.
   - Automático: só com processador e placa de nota 4 ou mais, e com o console fora do limite (o Desempenho que
     aprende desliga o patch se apertar).
2. **MFG Super Motion instalado** (`servidor\mfg.py`).
   - Gerador DLSS MFG numa RTX; MSM FG ("Fast" fora da dedicada forte) nas outras placas.
   - Sempre só os quadros que enchem a tela, menor atraso e pixel parado intacto.
   - Nada desenhado por cima do jogo.
   - Automático: só com placa forte, nos emuladores de fora ou numa tela de mais de 60 Hz.
3. **Lossless Scaling de quem comprou** (`servidor\lossless.py`), só onde o MFG não estiver.

## A tela: medido antes de decidir

Edge parado na tela inicial, catálogo de 3.294 jogos, PC do Rafael:

| Parte | Memória privada | Processador parado |
|---|---|---|
| Servidor em Python | 42 MB | 0,07% de um núcleo |
| Edge, perfil de sempre (14 processos) | 629 MB | ~8% (é o fundo animado) |
| Edge, perfil só do ARENA (8 processos) | 238 MB | igual |

Feito nesta versão:
- **janela leve** (`servidor\navegadores.py`): perfil próprio, sem extensões, sem sincronizar e sem os serviços de
  fundo. Fica fora do pen drive e mantém o SmartScreen ligado;
- **descanso do fundo animado**: no Automático, 3 minutos sem ninguém mexer e ele para.

## Decisão sobre o Rust

O roteiro recebido (Axum + tokio + rust-embed, alvos musl e aarch64-linux-android) troca **só o servidor**. Pelas
medidas, o servidor é a parte que menos pesa: 42 MB e quase 0% de processador parado. A troca economizaria no máximo
uns 35 MB, menos que os 391 MB que a janela leve tirou do navegador sem mudar de linguagem.

Além disso, o roteiro:
- **não tira o navegador**, porque o Axum continua mandando HTML para ele;
- abriria o servidor em `0.0.0.0:8080`, para toda a rede da escola, em vez de só `127.0.0.1` e as rotas de
  `ROTAS_REDE_EXTERNA`;
- **não serve ao Chromebook gerenciado**, que não roda programa baixado; ali a versão do navegador (file://)
  continua;
- **não serve ao Android sozinho**: o alvo aarch64-linux-android precisa do NDK, e o app já tem o servidor dentro.

Por fim, o código em Python é material de aula, e Rust é bem mais difícil de um aluno do ensino médio ler.

**Decidido:** o servidor fica em Python. Tirar o navegador de vez pediria refazer toda a tela numa biblioteca de
interface nativa (egui ou Slint, por exemplo), mantendo a versão HTML para o Chromebook: duas telas para manter e
semanas de trabalho, por uns 200 MB a menos. Isso só vale se a máquina-alvo, medida, mostrar que a janela leve não
basta.

**Próximo passo:** medir a janela leve no Celeron N5100.

### Fase 4 do plano Rust: decisão com os números (14/11/2026)

Seguiu o `docs\PLANO-DE-ACAO-RUST.md` até o fim (medir, otimizar o Python, prova em Rust só do trecho apontado).
No Galaxy A12, a conferência das pastas do cartão SD levou ~370 ms em Rust e ~410 ms em Python, uma pasta de cada
vez, e ~60 ms contra ~92 ms com 8 ao mesmo tempo: o ganho veio do paralelismo, e ele entrou no Python
(`indexador.pastas_com_data`). Com mais três correções achadas na mesma medida (assinatura pelo conteúdo, recursos
do RetroArch em segundo plano e `.pyc` prontos no APK), a abertura a frio no A12 ficou em 2,1 a 2,5 s dentro do
Python e a primeira depois de atualizar caiu de 13,4 s para 2,9 s. **Continua decidido: o servidor fica em Python.**
O Rust só tiraria o ~1,2 s do Python nascer e carregar a biblioteca padrão, ao custo de reescrever o servidor
inteiro. Detalhes em `docs\DESEMPENHO-SERVIDOR.md` (Fases 3 e 4); a prova fica em `ferramentas\prova_rust`.

## Alinhado ao driver da placa (11/11/2026, à noite)

`servidor\driver_video.py` lê o painel do driver (AMD Software) sem administrador e o ARENA se alinha: o Mais quadros
segue `min(tela, limite de quadros do driver)`; com o RSR ligado, o ARENA não estica de novo. Nada é gravado no
driver: a tela diz o que mudar a mão. O mesmo bloco existe no celular (`itens_android`: driver da GPU, MSAA forçado,
economia de bateria, taxa da tela, animações), lido com `getprop`, `/sys` e três chaves que o app passa em Java.

O "Mais quadros" ficou **unificado**: o ARENA escolhe o programa que rende mais na placa (NVIDIA RTX: o MFG com o
DLSS MFG; AMD e Intel: o Lossless, medido com 59,5 contra 56,6 quadros na tela), e nunca os dois juntos, porque o
segundo criaria quadros a partir dos quadros adivinhados pelo primeiro.

## Riscos

- **Janela do emulador:** o motor do MFG pega a maior janela do processo quando ela passa da metade da tela; se não
  aparecer em 40 s, o jogo segue sem ele.
- **Perfil novo do Edge:** só a janela "ARENA" apareceu nas duas aberturas. Se um Edge futuro abrir uma tela de
  boas-vindas, a regra está num lugar só (`navegadores.OPCOES_LEVES`).
- **Patch de 60 FPS:** o jogo fica mais pesado. No Automático, a máquina fraca nunca liga.
