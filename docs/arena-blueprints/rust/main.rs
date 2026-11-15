mod events;
mod storage;

use axum::{
    extract::FromRef,
    routing::{get, post},
    Router,
};
use events::{ws_handler, ArenaEvent, EventBus};
use std::{env, net::SocketAddr, sync::Arc};
use storage::{
    get_artwork_handler, get_favorites_handler, get_installed_emulators_handler,
    get_roms_handler, get_storage_handler, load_cached_library, load_favorites, scan_all_roms,
    sync_storage_handler, toggle_favorite_handler, SharedFavorites, SharedLibrary,
};
use tokio::sync::RwLock;

#[derive(Clone)]
struct AppState {
    library: SharedLibrary,
    favorites: SharedFavorites,
    events: EventBus,
}

impl FromRef<AppState> for SharedLibrary {
    fn from_ref(state: &AppState) -> Self {
        state.library.clone()
    }
}

impl FromRef<AppState> for SharedFavorites {
    fn from_ref(state: &AppState) -> Self {
        state.favorites.clone()
    }
}

impl FromRef<AppState> for EventBus {
    fn from_ref(state: &AppState) -> Self {
        state.events.clone()
    }
}

#[tokio::main]
async fn main() {
    let library: SharedLibrary = Arc::new(RwLock::new(load_cached_library()));
    let favorites: SharedFavorites = Arc::new(RwLock::new(load_favorites()));
    let events = EventBus::new(32);

    // Varredura inicial em background: ao terminar, notifica a WebView caso ela já tenha aberto o cache
    let bg_library = Arc::clone(&library);
    let bg_events = events.clone();
    tokio::spawn(async move {
        if let Ok(fresh) = tokio::task::spawn_blocking(|| scan_all_roms(&[])).await {
            let evt = ArenaEvent::StorageUpdated {
                roots: fresh.roots.clone(),
                total_roms: fresh.total_roms,
                by_system: fresh.by_system.clone(),
            };
            *bg_library.write().await = fresh;
            bg_events.publish(&evt);
        }
    });

    let state = AppState {
        library,
        favorites,
        events,
    };

    let app = Router::new()
        .route("/ws", get(ws_handler))
        .route("/api/storage", get(get_storage_handler))
        .route("/api/storage/sync", post(sync_storage_handler))
        .route("/api/roms", get(get_roms_handler))
        .route("/api/artwork", get(get_artwork_handler))
        .route("/api/favorites", get(get_favorites_handler))
        .route("/api/favorites/toggle", post(toggle_favorite_handler))
        .route("/api/emulators", get(get_installed_emulators_handler))
        .with_state(state);
        // Mantenha aqui suas rotas existentes (/api/status, /api/launch e .fallback(static_handler))

    let port: u16 = env::var("ARENA_PORT")
        .ok()
        .and_then(|p| p.parse().ok())
        .unwrap_or(8080);

    let addr = SocketAddr::from(([0, 0, 0, 0], port));
    println!("ARENA Web Server (Rust) ativo em http://{}", addr);

    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}