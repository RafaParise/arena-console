# Guia Completo de Prompts para o Claude Code (`arena-console`)

Este documento reúne todos os prompts estruturados para operar o **Claude Code** no repositório `RafaParise/arena-console` com zero alucinações, forçando leitura direta do disco e consulta aos blueprints locais em `docs/arena-blueprints/`.

---

## Prompt 0 — Inicialização e Ancoragem Obrigatória (Use Sempre ao Abrir o Claude Code)

> Pode ser acionado diretamente digitando `/project:arena-audit` dentro do Claude Code.

```text
Inspecione a árvore de diretórios deste repositório usando apenas ferramentas de leitura de disco (sem colar códigos no chat).

Confirme a presença e leia:
1. CLAUDE.md na raiz e os blueprints em docs/arena-blueprints/
2. arena-web/Cargo.toml e arena-web/src/
3. O módulo Android (AndroidManifest.xml, build.gradle / build.gradle.kts e código-fonte Kotlin/Java)
4. Os arquivos do frontend web e .github/workflows/

Assim que confirmar a estrutura física no disco e mapear os exports reais, aguarde minhas instruções específicas para implementar ou refatorar cada camada sem reescrever o que já funciona.
```

---

## Prompt 1 — Backend Rust Completo (`events.rs`, `storage.rs`, `main.rs`)

```text
Leia os arquivos reais em arena-web/Cargo.toml, arena-web/src/main.rs e os blueprints completos em docs/arena-blueprints/rust/ (events.rs, storage.rs, main.rs).

Implemente/atualize no servidor Axum (arena-web) sem bloquear threads assíncronas do Tokio (usando tokio::task::spawn_blocking para toda leitura de disco):
1. events.rs: EventBus com tokio::sync::broadcast emitindo ArenaEvent::StorageUpdated e ArenaEvent::FavoritesUpdated na rota GET /ws.
2. storage.rs:
   - Scanner recursivo (profundidade máx. 4, ignorando symlinks e arquivos ocultos '.*') descobrindo raízes via extra_paths, ARENA_STORAGE_PATHS, /storage/emulated/0, $HOME e /proc/mounts.
   - Parser XML zero-dependências para gamelist.xml (EmulationStation / RetroBat / Skraper) extraindo <name>, <desc> e <image> (com suporte a CDATA e barras '\').
   - Persistência de cache em library_cache.json e de favoritos em favorites.json (dentro de ARENA_DATA_DIR).
   - Rotas: GET /api/storage, POST /api/storage/sync, GET /api/roms (com filtro por sistema, favoritos e busca em título + sinopse), GET /api/artwork?id=<hash> (com Cache-Control: public, max-age=86400), GET /api/favorites, POST /api/favorites/toggle e GET /api/emulators.
3. main.rs: AppState unificado com FromRef, carga instantânea do cache no boot + varredura atualizada em background.

Ao concluir, rode 'cargo check --manifest-path arena-web/Cargo.toml' e corrija qualquer warning ou erro de compilação.
```

---

## Prompt 2 — Frontend Web Completo (WebSocket, Filtro de Emuladores, Capas, Sinopse, Busca e Favoritos)

```text
Leia os arquivos reais do frontend web deste repositório e o blueprint completo em docs/arena-blueprints/frontend/arena_realtime_ui.js.

Integre na interface web do ARENA (mantendo compatibilidade total com navegação D-Pad/Gamepad):
1. Cliente WebSocket (/ws) com reconexão automática a cada 2000ms para atualizar contadores e recarregar a lista de jogos nos eventos storage_updated e favorites_updated (sem usar alert() nativo).
2. Filtro automático de consoles [data-system] via window.ArenaAndroid.getInstalledEmulators() (ou GET /api/emulators no Linux/Chromebook) no DOMContentLoaded e visibilitychange, garantindo que o foco do D-Pad nunca fique preso em um botão oculto e aplicando fallback para core 'swanstation' no RetroArch quando o DuckStation não estiver instalado.
3. Renderização de capas via rom.artwork_url || FALLBACK_COVER com loading="lazy" e decoding="async", além de exibição segura via textContent da sinopse (rom.description) do gamelist.xml.
4. Busca instantânea por título e sinopse com AbortController + debounce de 100ms e alternância de favoritos via POST /api/favorites/toggle (incluindo atalho na tecla 'F').
```

---

## Prompt 3 — Consolidado Completo Android (Todas as 7 Camadas Nativas)

```text
Inspecione a estrutura completa deste repositório (RafaParise/arena-console), identificando o módulo Android (ex: android/app ou app), o package name real, a linguagem utilizada (Kotlin ou Java) e o código atual de arena-web/src/ e do frontend web. Consulte também o CLAUDE.md na raiz e os blueprints completos em docs/arena-blueprints/android/.

Aplique todas as integrações nativas abaixo diretamente nos arquivos do projeto:

1. GRADLE E ANDROID MANIFEST:
   - No build.gradle / build.gradle.kts do módulo app: configure abiFilters para incluir 'arm64-v8a', ative 'useLegacyPackaging = true' em packaging { jniLibs { ... } } e garanta a dependência androidx.core:core / core-ktx e androidx.activity.
   - No AndroidManifest.xml:
     * Permissões: INTERNET, FOREGROUND_SERVICE, FOREGROUND_SERVICE_SPECIAL_USE, POST_NOTIFICATIONS, RECEIVE_BOOT_COMPLETED, MANAGE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE (maxSdkVersion=32) e WRITE_EXTERNAL_STORAGE (maxSdkVersion=29).
     * Features opcionais (required="false"): android.hardware.gamepad, android.software.leanback e android.hardware.touchscreen.
     * Bloco <queries> declarando os pacotes: com.retroarch.aarch64, com.retroarch, xyz.aethersx2.android, org.dolphinemu.dolphinemu, org.ppsspp.ppsspp, org.ppsspp.ppssppgold, com.github.stenzek.duckstation, org.mupen64plusae.v3.fzurita e org.mupen64plusae.v3.fzurita.pro.
     * Na tag <application>: adicione android:extractNativeLibs="true" e android:requestLegacyExternalStorage="true".
     * Na MainActivity: configure android:launchMode="singleTask", android:stateNotNeeded="true", android:screenOrientation="landscape", android:theme="@style/Theme.ArenaConsole" e os intent-filters de MAIN com categorias HOME, DEFAULT, LAUNCHER e LEANBACK_LAUNCHER.
     * Registre <service android:name=".ArenaWebService" android:enabled="true" android:exported="false" android:foregroundServiceType="specialUse"> com <property android:name="android.app.PROPERTY_SPECIAL_USE_FGS_SUBTYPE" android:value="Local embedded Rust HTTP/WebSocket server for ARENA console frontend and emulator IPC" />.
     * Registre <receiver android:name=".BootReceiver" android:enabled="true" android:exported="true"> para BOOT_COMPLETED, QUICKBOOT_POWERON e com.htc.intent.action.QUICKBOOT_POWERON.
     * Registre <receiver android:name=".MediaMountReceiver" android:enabled="true" android:exported="true"> com <data android:scheme="file" /> para MEDIA_MOUNTED, MEDIA_UNMOUNTED, MEDIA_EJECT e MEDIA_BAD_REMOVAL.

2. ARMAZENAMENTO, MICROSD/USB E HOTPLUG:
   - Crie StoragePermissionHelper para checar/solicitar Environment.isExternalStorageManager() (API 30+) com fallback para ACTION_MANAGE_ALL_FILES_ACCESS_PERMISSION em TV Boxes, e READ/WRITE_EXTERNAL_STORAGE nas APIs anteriores.
   - Crie StorageDiscovery para listar todos os volumes montados via StorageManager (interno + microSD + pendrives USB) com fallback para /mnt/media_rw.
   - Crie MediaMountReceiver para capturar eventos de montagem/desmontagem e enviar POST JSON {"paths": [...]} em thread separada para http://127.0.0.1:<port>/api/storage/sync.

3. RUNNER RUST, FOREGROUND SERVICE (API 34+) E BOOT:
   - Crie/atualize ArenaWebRunner para executar File(context.applicationInfo.nativeLibraryDir, "libarena_web.so") via ProcessBuilder em context.filesDir, injetando ARENA_PORT, ARENA_DATA_DIR, ARENA_STORAGE_PATHS (caminhos de StorageDiscovery unidos por ':') e RUST_LOG=info.
   - Crie ArenaWebService promovendo o serviço com ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE no Android 14+ (API 34), notificação persistente com botão "Encerrar" (ACTION_STOP), salvando server_port em SharedPreferences("arena_prefs") e iniciando ArenaWebRunner.
   - Crie BootReceiver para ler server_port de SharedPreferences("arena_prefs") e disparar ArenaWebService.start(context.applicationContext, port) no boot.

4. PONTE JAVASCRIPTINTERFACE (ArenaEmulatorBridge):
   - Crie ArenaEmulatorBridge exposta na WebView como "ArenaAndroid", validando origem local (http://127.0.0.1: ou http://localhost:).
   - Implemente isAndroidNative(), getInstalledEmulators() (retornando JSON com emuladores instalados e lista de sistemas habilitados) e launchGame(emulator, romPath, coreName) disparando Intents nativas (FLAG_ACTIVITY_NEW_TASK) para RetroArch, PCSX2/AetherSX2/NetherSX2, Dolphin, PPSSPP (Free/Gold), DuckStation e Mupen64Plus FZ (Free/Pro).

5. MAINACTIVITY (MODO IMERSIVO, LAUNCHER HOME E GAMEPAD/D-PAD):
   - Crie/atualize o estilo Theme.ArenaConsole (parent NoActionBar, windowFullscreen=true, windowBackground=#000000).
   - Na MainActivity: ative FLAG_KEEP_SCREEN_ON, configure WindowCompat.setDecorFitsSystemWindows(window, false) e WindowInsetsControllerCompat (BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE ocultando systemBars()) no onCreate e no onWindowFocusChanged.
   - Configure a WebView com JavaScript/DOMStorage habilitados, hardware acceleration, foco travado (requestFocus), OnApplyWindowInsetsListener zerando padding (WindowInsets.CONSUMED) e ArenaEmulatorBridge registrado.
   - Intercepte OnBackPressedCallback (voltando histórico da WebView sem fechar o Launcher) e sobrescreva dispatchKeyEvent para repassar eventos de D-Pad e Gamepad (incluindo KEYCODE_BUTTON_B / KEYCODE_BACK de joysticks) diretamente para a WebView.
   - Solicite permissão de armazenamento e POST_NOTIFICATIONS antes de iniciar ArenaWebService.start(), aguarde a porta local responder (healthcheck socket) e carregue http://127.0.0.1:<port>.

6. SINCRONIZAÇÃO COM BACKEND RUST E FRONTEND WEB:
   - Garanta que arena-web (Rust/Axum) leia ARENA_PORT, ARENA_DATA_DIR e ARENA_STORAGE_PATHS, exponha GET /api/storage, POST /api/storage/sync, GET /api/roms e GET /ws (broadcast Tokio emitindo evento storage_updated ao sincronizar).
   - No frontend web: conecte startArenaGame() e o filtro de consoles [data-system] à ponte window.ArenaAndroid (com fallback HTTP no Linux/Chromebook) e adicione o cliente WebSocket (/ws) com reconexão automática para recarregar a lista de jogos ao conectar/remover pendrives ou cartões SD.

7. VALIDAÇÃO FINAL:
   - Verifique a sintaxe dos arquivos XML e execute 'cargo check --manifest-path arena-web/Cargo.toml' e './gradlew compileDebugSources' (ou './gradlew assembleDebug') corrigindo eventuais erros até compilar limpo.
```