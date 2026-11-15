# ARENA Console (`RafaParise/arena-console`) — Ancoragem Oficial para Claude Code

> **AVISO AO AGENTE (CLAUDE CODE):** Este arquivo é carregado automaticamente no início de toda sessão e após cada `/compact`. Siga estritamente todas as regras arquiteturais, contratos de API, mapeamentos de sistemas e protocolos anti-alucinação abaixo.

---

## 1. As 4 Práticas Obrigatórias para Zero Alucinações no Claude Code

1. **Ancoragem Automática via `CLAUDE.md` (este arquivo):**
   - Carregado automaticamente no boot de toda sessão e após qualquer compactação de contexto (`/compact`). Nunca ignore ou sobrescreva as regras aqui definidas.
2. **Leitura Direta do Disco Antes de Escrever (Zero Reescrita Cega):**
   - **NUNCA** peça para o usuário colar código longo no chat e **NUNCA** invente nomes de structs, pacotes, funções, rotas ou assinaturas de crates.
   - Antes de editar ou criar qualquer arquivo, inspecione os exports e arquivos reais no disco (`arena-web/Cargo.toml`, `arena-web/src/`, `android/`, frontend web) e consulte os blueprints de referência em `docs/arena-blueprints/`.
3. **Execução Incremental por Camada com Portão de Compilação:**
   - Implemente uma camada de cada vez (1. Backend Rust -> 2. Frontend Web -> 3. Camada Nativa Android -> 4. CI/CD) e valide obrigatoriamente o build antes de avançar:
     - Rust: `cargo check --manifest-path arena-web/Cargo.toml`
     - Android: `(cd android && ./gradlew compileDebugSources)` ou `./gradlew assembleDebug`
4. **Preservação Estrita de Código Existente e Isolamento de Contexto:**
   - Preserve rotas já existentes (`/api/status`, `/api/launch`, `.fallback(static_handler)`), pacotes Android, ABIs (`arm64-v8a`) e regras de empacotamento JNI (`useLegacyPackaging = true`, `extractNativeLibs = true`).
   - Ao trocar de camada (ex: finalizar Rust e iniciar Android), execute `/compact` ou `/clear` mantendo o `CLAUDE.md` como âncora limpa.

---

## 2. Arquitetura Geral & Variáveis de Ambiente

O **ARENA Console** opera de forma híbrida em **Android (TV Box / Smartphone / Tablet)** e **Linux / Chromebook (x86_64 e aarch64)**:

- **`ARENA_PORT`** (padrão `8080`): Porta HTTP/WebSocket local do servidor Rust (`0.0.0.0:<port>`).
- **`ARENA_DATA_DIR`**: Diretório persistente para `library_cache.json` e `favorites.json` (no Android: `context.filesDir`).
- **`ARENA_STORAGE_PATHS`**: Lista de pontos de montagem separados por `:` (ex: `/storage/emulated/0:/storage/38F2-19A0`), injetada pelo `ArenaWebRunner` via `StorageDiscovery`.
- **`RUST_LOG`**: Nível de log (`info` por padrão).

---

## 3. Contratos do Backend Rust (`arena-web/src/`)

### 3.1. Isolamento de Concorrência (Regra Crítica)
- Toda operação de I/O síncrono ou varredura recursiva de disco (`scan_all_roms`, leitura de `/proc/mounts`, parsing de `gamelist.xml`, gravação de `library_cache.json`) **DEVE** rodar dentro de `tokio::task::spawn_blocking`. Nunca bloqueie threads assíncronas do Tokio.

### 3.2. Endpoints HTTP & WebSocket
- `GET /ws` (`events.rs`): Upgrade WebSocket via `tokio::sync::broadcast::Sender<String>` (`EventBus`).
  - Eventos emitidos em JSON:
    - `{"event": "storage_updated", "data": {"roots": [...], "total_roms": N, "by_system": {...}}}`
    - `{"event": "favorites_updated", "data": {"ids": [...]}}`
- `GET /api/storage` (`storage.rs`): Retorna `{roots, total_roms, by_system}` direto da RAM (`Arc<RwLock<LibrarySnapshot>>`).
- `POST /api/storage/sync` (`storage.rs`): Recebe opcionalmente `{"paths": [...]}` (do `MediaMountReceiver` Android ou botão da UI), executa `scan_all_roms` em `spawn_blocking`, salva `library_cache.json`, atualiza `RwLock` e publica `ArenaEvent::StorageUpdated` no `EventBus`.
- `GET /api/roms` (`storage.rs`): Aceita query params `?system=<sys|all|favorites>&q=<texto>&favorites_only=<bool>`.
  - Busca instantânea *case-insensitive* tanto em `rom.title` quanto em `rom.description` (sinopse do `gamelist.xml`).
  - Retorna cada `RomEntry` acrescido de `"is_favorite": bool`.
- `GET /api/artwork?id=<hash>` (`storage.rs`): Serve imagens locais (`image/png`, `image/jpeg`, `image/webp`) direto das pastas de ROMs / cartão SD / USB com header `Cache-Control: public, max-age=86400`, validando o ID determinístico (FNV-1a 64-bit do caminho) na biblioteca em RAM para bloquear *path traversal*.
- `GET /api/favorites` & `POST /api/favorites/toggle` (`storage.rs`): Alterna o ID em `Arc<RwLock<HashSet<String>>>`, persiste em `favorites.json` e emite `ArenaEvent::FavoritesUpdated`.
- `GET /api/emulators` (`storage.rs`): Paridade Linux/Chromebook verificando binários no `PATH` (`retroarch`, `pcsx2`/`pcsx2-qt`, `dolphin-emu`/`dolphin-emu-nogui`, `PPSSPPSDL`/`ppsspp`).

### 3.3. Scanner Recursivo, `gamelist.xml` e Tabela de Sistemas (`storage.rs`)
- **Descoberta de raízes (`discover_storage_roots`)**: Combina `extra_paths`, `ARENA_STORAGE_PATHS`, `/storage/emulated/0`, `$HOME` e leitura direta de `/proc/mounts` filtrando `/storage/` (exceto `/storage/emulated` e `/storage/self`) e `/mnt/media_rw/` nos sistemas de arquivos `vfat`, `exfat`, `ntfs`, `fuse`, `sdfat`, `sdcardfs`, `ext4`.
- **Subpastas candidatas**: `["ROMs", "roms", "Roms", "ARENA/roms", "ARENA/ROMs"]`.
- **Varredura segura (`walk_roms`)**: Profundidade máxima `4`, ignora symlinks (`is_symlink()`) para evitar loops em `/storage/self`, ignora arquivos ocultos (`.*` / `._*`).
- **Parser `gamelist.xml` (zero dependências externas)**: Lê `gamelist.xml` de cada pasta de console, normaliza chaves relativas (`\` -> `/`, remove `./`), extrai `<name>`, `<desc>` e `<image>` (tratando `<![CDATA[...]]>` e entidades XML), priorizando a capa do XML sobre a detecção automática (`.`, `covers/`, `boxart/`, `images/`, `media/boxart/`, `media/images/` e sufixo `-image`).
- **Perfis de Consoles (`match_system_profile`)**:
  - `snes` / `sfc` / `supernintendo` -> `retroarch` | core `snes9x` | `["sfc", "smc", "fig", "zip", "7z"]`
  - `nes` / `fc` / `famicom` -> `retroarch` | core `nestopia` | `["nes", "unf", "zip", "7z"]`
  - `gba` -> `retroarch` | core `mgba` | `["gba", "zip", "7z"]`
  - `gbc` / `gb` -> `retroarch` | core `gambatte` | `["gb", "gbc", "zip", "7z"]`
  - `megadrive` / `genesis` / `md` -> `retroarch` | core `genesis_plus_gx` | `["md", "bin", "gen", "smd", "zip", "7z"]`
  - `ps1` / `psx` / `playstation` -> `duckstation` | core `swanstation` | `["chd", "cue", "pbp", "iso", "m3u"]` *(omite `.bin` para não duplicar faixas de áudio)*
  - `ps2` / `pcsx2` -> `pcsx2` | core `""` | `["iso", "chd", "cso", "gz"]`
  - `psp` / `ppsspp` -> `ppsspp` | core `""` | `["iso", "cso", "pbp"]`
  - `n64` / `mupen64` -> `mupen64` | core `mupen64plus_next` | `["z64", "n64", "v64", "zip", "7z"]`
  - `gc` / `gamecube` -> `dolphin` | core `""` | `["iso", "rvz", "gcz", "ciso"]`
  - `wii` -> `dolphin` | core `""` | `["iso", "rvz", "wbfs", "gcz"]`
  - `dreamcast` / `dc` -> `retroarch` | core `flycast` | `["chd", "cdi", "gdi"]`
  - `arcade` / `fbneo` / `mame` / `neogeo` -> `retroarch` | core `fbneo` | `["zip", "7z"]`

---

## 4. Contratos da Camada Nativa Android (`android/`)

- **Gradle & Empacotamento**:
  - `abiFilters` com `'arm64-v8a'`
  - `packaging { jniLibs { useLegacyPackaging = true } }` + `android:extractNativeLibs="true"` para extrair `libarena_web.so` em `nativeLibraryDir` executável.
- **Manifesto & Permissões**:
  - Permissões: `INTERNET`, `FOREGROUND_SERVICE`, `FOREGROUND_SERVICE_SPECIAL_USE`, `POST_NOTIFICATIONS`, `RECEIVE_BOOT_COMPLETED`, `MANAGE_EXTERNAL_STORAGE`, `READ_EXTERNAL_STORAGE` (`maxSdkVersion=32`), `WRITE_EXTERNAL_STORAGE` (`maxSdkVersion=29`), `android:requestLegacyExternalStorage="true"`.
  - Features (`required="false"`): `android.hardware.gamepad`, `android.software.leanback`, `android.hardware.touchscreen`.
  - `<queries>` para pacotes: `com.retroarch.aarch64`, `com.retroarch`, `xyz.aethersx2.android`, `org.dolphinemu.dolphinemu`, `org.ppsspp.ppsspp`, `org.ppsspp.ppssppgold`, `com.github.stenzek.duckstation`, `org.mupen64plusae.v3.fzurita`, `org.mupen64plusae.v3.fzurita.pro`.
- **Componentes Nativos (Blueprints completos em `docs/arena-blueprints/android/`)**:
  1. `StoragePermissionHelper`: Verifica/solicita `Environment.isExternalStorageManager()` (API 30+) com fallback para TV Boxes que ocultam a tela específica, e `READ/WRITE_EXTERNAL_STORAGE` nas APIs anteriores.
  2. `StorageDiscovery`: Enumera volumes montados via `StorageManager` (interno + microSD + pendrives USB) com fallback para `/mnt/media_rw`.
  3. `MediaMountReceiver`: Escuta `MEDIA_MOUNTED`, `MEDIA_UNMOUNTED`, `MEDIA_EJECT`, `MEDIA_BAD_REMOVAL` (`scheme="file"`) e dispara `POST http://127.0.0.1:<port>/api/storage/sync` em thread separada.
  4. `ArenaWebRunner`: Executa `File(context.applicationInfo.nativeLibraryDir, "libarena_web.so")` via `ProcessBuilder` em `context.filesDir` com variáveis `ARENA_PORT`, `ARENA_DATA_DIR`, `ARENA_STORAGE_PATHS` e `RUST_LOG=info`.
  5. `ArenaWebService`: Foreground Service (`ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE` no Android 14+ / API 34 + `PROPERTY_SPECIAL_USE_FGS_SUBTYPE`), notificação persistente com ação "Encerrar" (`ACTION_STOP`), salvando `server_port` em `SharedPreferences("arena_prefs")`.
  6. `BootReceiver`: Escuta `BOOT_COMPLETED`, `QUICKBOOT_POWERON`, `com.htc.intent.action.QUICKBOOT_POWERON`, lê `server_port` de `SharedPreferences("arena_prefs")` e inicia `ArenaWebService.start(...)`.
  7. `ArenaEmulatorBridge`: `@JavascriptInterface` registrada como `ArenaAndroid`, valida origem local (`http://127.0.0.1:` / `http://localhost:`), expõe `isAndroidNative()`, `getInstalledEmulators()` (JSON com emuladores instalados e sistemas habilitados) e `launchGame(emulator, romPath, coreName)` via Intents nativas (`FLAG_ACTIVITY_NEW_TASK`).
  8. `MainActivity`: Launcher `HOME` (`singleTask`, `stateNotNeeded`, `landscape`, `Theme.ArenaConsole`), `FLAG_KEEP_SCREEN_ON`, modo imersivo total (`WindowInsetsControllerCompat` + `WindowInsets.CONSUMED`), `OnBackPressedCallback` navegando no histórico da WebView, `dispatchKeyEvent` repassando D-Pad/Gamepad (inclusive `KEYCODE_BUTTON_B` / `KEYCODE_BACK`) para a WebView, e healthcheck socket na porta local antes de carregar `http://127.0.0.1:<port>`.

---

## 5. Contratos do Frontend Web (`docs/arena-blueprints/frontend/`)

- **WebSocket (`/ws`)**: Reconexão automática em `2000ms`; reage a `storage_updated` (atualiza contadores e recarrega lista ativa sem `alert()`) e `favorites_updated`.
- **Filtro Dinâmico de Consoles**: Consulta `window.ArenaAndroid.getInstalledEmulators()` (no Android) ou `/api/emulators` (no Linux/Chromebook) no `DOMContentLoaded` e `visibilitychange`, ocultando `[data-system]` sem emulador e movendo o foco do D-Pad para o primeiro console visível. Se DuckStation não estiver instalado mas RetroArch estiver, usa fallback `emulator="retroarch"`, `core="swanstation"`.
- **Capas, Sinopse, Busca e Favoritos**:
  - Cards usam `rom.artwork_url || FALLBACK_COVER` com `loading="lazy"`, `decoding="async"` e `onerror`.
  - Detalhes usam `textContent` para exibir `rom.title` e `rom.description` (`gamelist.xml`).
  - Busca instantânea com `AbortController` + debounce `100ms` (`GET /api/roms?system=...&q=...`).
  - Favoritos via `POST /api/favorites/toggle` e atalho de teclado `'F'`.