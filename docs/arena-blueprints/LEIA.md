# Blueprints de 14/11/2026: o que entrou no ARENA, e onde

Os arquivos desta pasta saíram de cinco geradores em PowerShell (`geradores\`), rodados em 14/11/2026 às 12h11.
Eles descrevem um projeto que **não existe neste repositório**: um `arena-web` em Rust com Axum e Tokio, um app
Android em Kotlin com Gradle, uma WebSocket `/ws` e rotas como `/api/roms` e `/api/storage`. Por isso nada daqui entra
como está. O pedido do Rafael foi outro: "são apenas ideias, pegue o que tem de cada ideia, transforme em scripts do
que é possível implementar no ARENA". Esta página diz o que foi aproveitado e onde, e por que o resto ficou de fora.

Os geradores levaram `.NAO-EXECUTAR` no nome: rodá-los de novo reescreveria o `CLAUDE.md` da raiz com as regras do
`arena-web` (foi o que aconteceu às 12h13; o `CLAUDE.md` de antes voltou, e o texto dos geradores está em
`CLAUDE-blueprint.md`). Os arquivos de `github\` e `scripts\` estavam na raiz e em `.github\`; vieram para cá sem
estar ativos.

## O que entrou (adaptado)

| Ideia (arquivo daqui) | Onde está no ARENA | Como ficou diferente |
|---|---|---|
| Servidor em Rust na frente (`rust\main.rs`) | `nativo\src\main.rs` (etapas R1 e R2, `docs\MIGRACAO-RUST.md`) | Só a biblioteca padrão do Rust, sem Axum nem Tokio: 0,5 MB, compila para ARM64 sem o NDK, e o Python fica atrás como reserva |
| Avisos em tempo real (`rust\events.rs`, `frontend\arena_realtime_ui.js`) | `/_nativo/eventos` no nativo, `avisar_a_tela()` no `servidor\arena.py`, `ouvirOsAvisosDoServidor()` no `launcher\app.js` (etapa R3) | Server-Sent Events em vez de WebSocket (o aviso só vai num sentido e o navegador reconecta sozinho); a tela compara a geração da lista e redesenha sem perder o foco do controle |
| Sinopse do `gamelist.xml` e busca nela (`rust\storage.rs`) | `servidor\indexador.py` (`sinopse`), busca e painel no `launcher\app.js` (commit `fb26024`) | O nome e a capa do `gamelist.xml` já existiam (`141b2a3`) |
| Pasta `roms\` do Batocera (`rust\storage.rs`) | apelidos no `servidor\consoles.json` e `servidor\armazenamento.py` (`fb26024`) | |
| Emuladores no `PATH` do Linux (`/api/emulators`) | `plataforma.programa_do_sistema()` e `graficos.achar_externo_detalhado()`; a tela diz "instalado no sistema" | A pasta `emuladores\` do ARENA vem sempre antes; a configuração e a BIOS ficam na pasta do ARENA (o `/usr/bin` nem deixa gravar); o flatpak fica de fora (o sandbox dele troca a pasta de configuração) |
| Esconder os consoles sem emulador (`frontend\arena_realtime_ui.js`) | botão **Só os que abrem aqui** na tela | Desligado por padrão e a cada abertura: o ARENA continua mostrando o jogo apagado com o motivo (decisão de 13/11, 24º guia do `docs\PLANO-DE-ACAO-RUST.md`); quem liga sabe o que pediu |
| `validate_api_endpoints` (`scripts\`) | `ferramentas\conferir_servidor.py` | Só lê; confere também o que tem de ser recusado (Host falso, POST sem JSON, caminho com `..`) e reconhece o Android, que recusa tudo sem o cookie |
| `test_adb_tvbox` (`scripts\`) | `ferramentas\medir_abertura_no_celular.py` (e o `ferramentas\auditoria_celular.py`, que já existia) | Mede do toque até a lista e confere o nativo no aparelho; nunca manda tecla, nunca muda configuração, nunca instala |
| `publish_release` e `release.yml`/`labeler.yml` (`scripts\`, `github\`) | `ferramentas\rascunho_da_release.py` | Só o rascunho da nota, agrupado pela pasta que cada commit mudou. Nunca etiqueta, nunca envia: o `publish_release` fazia `git add .` e `push`, que as regras do ARENA proíbem |
| `build_arena_web` (`scripts\`) | `ferramentas\compilar_nativo.py` | Já existia: compila os 3 alvos e roda o `cargo test` |
| As 4 práticas de ancoragem (`CLAUDE-blueprint.md`) | seção "Como trabalhar" do `CLAUDE.md` | Com os caminhos reais: ler o arquivo do disco antes de escrever, portão de compilação por camada, preservar o que existe |
| Ouvir pen drive e cartão (`android\MediaMountReceiver.kt`) | `ArenaServico.ouvirOsCartoes()` | Já existia (21º guia); registrado no código, não no manifesto, para nenhum outro app mandar aviso falso |
| Serviço em primeiro plano, permissão de arquivos, tela inicial (`android\ArenaWebService.kt`, `StoragePermissionHelper.kt`, `MainActivity.kt`) | `ArenaServico.java` e `ArenaActivity.java` | Já existiam (11º, 19º e 14º guias; o modo TV Box vem desligado) |

## O que ficou de fora, e por quê

- **`BootReceiver.kt`** (abrir sozinho ao ligar o aparelho): no celular do aluno, abrir sem pedir não é desejável; na
  TV Box, o modo TV Box (o ARENA como tela inicial) já cobre (13º guia).
- **`ArenaEmulatorBridge.kt`** (a página abre outros apps de emulador por `@JavascriptInterface`): o ARENA usa o
  RetroArch dele; uma ponte JavaScript que abre apps seria uma porta a mais para outra página usar (18º guia).
- **`<queries>` do `AndroidManifest.xml`** (enxergar os apps de emulador instalados): só serve à ponte acima.
- **`build.gradle.kts`**: o APK do ARENA é montado pelo `ferramentas\montar_android.py`, sem Gradle.
- **`styles.xml`** (desenhar também na área do entalhe da câmera): fica para testar no A12 antes; mudança de tela no
  Android só entra conferida no aparelho.
- **`setup_github_labels`** e o **`labeler.yml`**: o ARENA não trabalha com pull request; o rascunho da versão agrupa
  pela pasta, sem etiquetas.
- **`GUIA_INFRAESTRUTURA_ARMBIAN_SERVIDOR.md`**: o ARENA já abre no Armbian pelo `ARENA.sh` (`56c4da5`); o
  `install.sh` por `curl | bash` e o serviço `arena-web` do systemd não foram criados (9º e 10º guias). Se for seguir
  o guia, troque a senha padrão do Armbian no primeiro acesso.
- **`CLAUDE_PROMPTS_PRONTOS.md`**: prompts para o `arena-web`; ficam só como referência.
- **`gitignore_arena_rules.txt`**: o `.gitignore` do ARENA já ignora as chaves de assinatura (`*.keystore`, `*.jks`) e
  o que o Rust compila (`nativo/target/`, os executáveis do nativo em `servidor\`).
