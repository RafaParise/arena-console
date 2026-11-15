# Migração para Rust: o servidor nativo na frente do Python (desde 14/11/2026)

Pedido do Rafael (14/11/2026): "eu quero desempenho máximo possível, mesmo que não seja mais em Python". A regra do
ARENA mudou nesse dia (`CLAUDE.md`, linha "Rust"): o Rust entra onde a medida mostra ganho que se sente, e o Python
fica atrás, como reserva. Esta página diz como as duas partes conversam, o que cada etapa trouxe (medido) e a resposta
honesta à pergunta "vale reescrever tudo em Rust?".

## Como funciona

```
ARENA.bat / ARENA.sh / app do Android
        │  abrem  arena-nativo  <o mesmo comando que abria o Python>
        ▼
  nativo (Rust, porta 8777) ──── abre a porta em ~15 a 50 ms
        │  sobe o Python numa porta sorteada, só em 127.0.0.1,
        │  com o segredo ARENA_ATRAS_DO_NATIVO
        ▼
  Python (servidor\arena.py) ──── as ~121 rotas /api de sempre
```

- **O nativo responde sozinho só ao pedido local confiável**: do próprio aparelho (loopback), com o `Host` de um nome
  dele (contra DNS rebinding) e, no Android, com o cookie `arena_segredo` da tela. Tudo o mais vai para o Python, que
  confere como antes (`checar_acesso_de_rede`, `ROTAS_REDE_EXTERNA`, `Content-Type` do POST).
- O Python só acredita no `X-Arena-Origem` (o endereço de quem pediu) quando o pedido traz o `X-Arena-Proxy` com o
  segredo daquela abertura. O nativo apaga os dois cabeçalhos que vierem de fora antes de repassar.
- **Sem o executável, ou depois de uma queda do nativo, o ARENA abre só com o Python**, como era antes
  (`ARENA_SEM_NATIVO=1` no `ARENA.bat`, `NATIVO=""` no `ARENA.sh`, `quedas == 0` no `ArenaServico.java`).
- Código: `nativo\src\main.rs` (abertura, repasse, avisos), `http.rs` (ler e responder HTTP/1.1), `sistema.rs`
  (Ctrl+C, morrer junto com o pai no Linux), `capas.rs` (etapa R2). Só a biblioteca padrão do Rust, sem pacote de fora.

## As etapas

| Etapa | O que o nativo passou a fazer | Medido |
|---|---|---|
| **R1** | Abre a porta na hora; entrega os arquivos da tela; entrega o último `/api/estado` e `/api/catalogo` guardados (`dados\nativo\`, cabeçalho `X-Arena-Guardado`) enquanto o Python carrega; `/_nativo/pronto` avisa a tela quando ele abre; troca a escuta quando a chave da rede muda (`/_nativo/rede`) | A12, do toque até a lista: **6,76 s → 2,52 a 2,65 s**. PC (cópia de teste): lista em **0,33 s → 0,02 a 0,03 s** na segunda abertura |
| **R2** | As capas (`/api/capa`), com a mesma regra de caminho e a mesma miniatura (nome SHA-1) do Python | As capas saem antes de o Python ficar pronto (o registro do nativo conta quantas) |
| **R3** | Avisos em tempo real (`/_nativo/eventos`, Server-Sent Events): o Python conta que a lista mudou, o nativo repassa à tela, que se redesenha sozinha sem perder o foco | PC: a tela recebe a lista nova **103 ms** depois da mudança (100 ms são de propósito: juntam a rajada) |

### R3 em detalhe (a ideia do `events.rs` dos blueprints, adaptada)

- Trabalho que termina em segundo plano (a busca de capas, um download, as BIOS organizadas na abertura, a mudança de
  jogos para o cartão) muda a lista depois de a tela já ter desenhado. Antes, a tela só via no próximo clique.
- O Python sobe uma **geração** da lista a cada `limpar_caches()` (ela começa na hora da abertura, em ms, para ser
  sempre maior que a de uma lista guardada) e manda `POST /_nativo/evento?tipo=catalogo` ao nativo por **uma thread só,
  que dorme** num `Event` enquanto não há aviso. O fim de um jogo manda `tipo=jogo`.
- O nativo guarda os últimos 64 avisos, numerados, e entrega a quem ouve. A conexão parada não gasta processador: a
  thread dorme numa `Condvar` e acorda a cada 20 s só para mandar um sinal de vida (é como se descobre uma aba
  fechada). No máximo 8 telas ouvindo; quem não lê perde a vez em 10 s.
- A tela só abre o `EventSource` quando a resposta traz `X-Arena-Nativo: 1`. Compara a geração do aviso com a da lista
  que tem (o próprio clique já trouxe a lista nova? então ignora), espera 400 ms e redesenha mantendo o jogo em foco,
  as linhas do "Mostrar mais" e o jogo escolhido. Com a tela escondida (durante o jogo), só marca e redesenha quando
  ela volta.
- De quebra, o `/api/catalogo` deixou de guardar uma resposta montada durante uma mudança (ela nascia velha e ficava
  guardada até o cache vencer).
- Por que não a WebSocket do `controle_remoto.py`: o aviso só vai num sentido, o navegador reconecta sozinho o
  `EventSource`, e no nativo a conexão parada não prende uma thread do Python.

## Vale reescrever tudo em Rust? (a resposta, com os números)

**Não as ~121 rotas que sobram.** O que o aluno sentia era a abertura, e ela já saiu do Python:

- No A12, dos 2,52 s do toque até a lista, **1,6 a 1,7 s são da própria página** no WebView (HTML, `app.js`,
  JavaScript e desenho), não do servidor. Nenhum servidor, em nenhuma língua, tira esse tempo.
- O repasse pelo nativo custa **0,1 a 1,5 ms por pedido** (`testes\medir_nativo.py`), e a rota mais cara do Python, o
  `/api/estado`, leva ~12 ms no PC. Reescrever as rotas pouparia milissegundos por clique, que ninguém nota.
- A Fase 3 (`docs\DESEMPENHO-SERVIDOR.md`) já tinha medido: no disco do celular (FUSE), ler em paralelo deu 4 a 5
  vezes mais rápido; trocar a língua, uns 10%. O que pesa é disco e trabalho repetido, não o Python.
- Reescrever custaria semanas, duas bases de código para manter iguais (a segurança do Python é a referência) e o
  código de aula legível por aluno do ensino médio.

**Próxima etapa só com medida**: um trecho frequente, de processador, que custe mais de ~100 ms e que o Python não
resolva. Até agora não apareceu nenhum.

## Como compilar e conferir

- `servidor\python\python.exe ferramentas\compilar_nativo.py`: compila os 3 alvos (Windows `x86_64-pc-windows-gnullvm`
  com o llvm-mingw; Linux e Android `x86_64`/`aarch64-unknown-linux-musl` com o `rust-lld`, sem o NDK), roda o
  `cargo test` e copia para `servidor\arena-nativo.exe`, `servidor\arena-nativo-linux-x86_64` e
  `servidor\arena-nativo-linux-aarch64`. O `ferramentas\montar_android.py` põe o de ARM64 no APK como
  `lib\arm64-v8a\libarenanativo.so`. O aluno nunca compila.
- `testes\teste_nativo.py`: ponta a ponta numa cópia do ARENA (tempos, segurança, capas, avisos, o Python fechando).
- `testes\medir_nativo.py`: o custo de cada rota, direto no Python e pelo nativo.
- `ferramentas\conferir_servidor.py`: confere um ARENA que já está rodando (só lê).
- `ferramentas\medir_abertura_no_celular.py`: mede a abertura no celular pelo cabo e confere o nativo no aparelho.
