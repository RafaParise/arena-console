use axum::{
    extract::{
        ws::{Message, WebSocket, WebSocketUpgrade},
        State,
    },
    response::IntoResponse,
};
use serde::Serialize;
use std::collections::HashMap;
use tokio::sync::broadcast;

#[derive(Debug, Clone, Serialize)]
#[serde(tag = "event", content = "data", rename_all = "snake_case")]
pub enum ArenaEvent {
    StorageUpdated {
        roots: Vec<String>,
        total_roms: usize,
        by_system: HashMap<String, usize>,
    },
    FavoritesUpdated {
        ids: Vec<String>,
    },
}

#[derive(Clone)]
pub struct EventBus {
    tx: broadcast::Sender<String>,
}

impl EventBus {
    pub fn new(capacity: usize) -> Self {
        let (tx, _) = broadcast::channel(capacity);
        Self { tx }
    }

    pub fn publish(&self, event: &ArenaEvent) {
        if let Ok(json) = serde_json::to_string(event) {
            // Ignora Err quando não há nenhum cliente WebSocket conectado no momento
            let _ = self.tx.send(json);
        }
    }
}

/// GET /ws — Upgrade HTTP para WebSocket persistente
pub async fn ws_handler(
    ws: WebSocketUpgrade,
    State(bus): State<EventBus>,
) -> impl IntoResponse {
    let rx = bus.tx.subscribe();
    ws.on_upgrade(move |socket| handle_socket(socket, rx))
}

async fn handle_socket(mut socket: WebSocket, mut rx: broadcast::Receiver<String>) {
    loop {
        tokio::select! {
            // 1. Repassa eventos internos do Rust para o frontend conectado
            recv_res = rx.recv() => {
                match recv_res {
                    Ok(payload) => {
                        if socket.send(Message::Text(payload)).await.is_err() {
                            break;
                        }
                    }
                    Err(broadcast::error::RecvError::Lagged(_)) => continue,
                    Err(broadcast::error::RecvError::Closed) => break,
                }
            }
            // 2. Detecta desconexão imediata da WebView ou responde pings
            client_msg = socket.recv() => {
                match client_msg {
                    Some(Ok(Message::Close(_))) | None => break,
                    Some(Ok(Message::Ping(data))) => {
                        if socket.send(Message::Pong(data)).await.is_err() {
                            break;
                        }
                    }
                    _ => {}
                }
            }
        }
    }
}