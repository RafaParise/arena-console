use crate::events::{ArenaEvent, EventBus};
use axum::{
    extract::{Query, State},
    http::{header, StatusCode},
    response::IntoResponse,
    Json,
};
use serde::{Deserialize, Serialize};
use std::{
    collections::{BTreeSet, HashMap, HashSet},
    env, fs,
    path::{Path, PathBuf},
    sync::Arc,
};
use tokio::sync::RwLock;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RomEntry {
    pub id: String,
    pub title: String,
    #[serde(default)]
    pub description: Option<String>,
    pub system: String,
    pub emulator: String,
    pub core: String,
    pub path: String,
    pub size_bytes: u64,
    #[serde(default)]
    pub artwork_url: Option<String>,
    #[serde(skip_serializing, default)]
    pub custom_artwork_path: Option<PathBuf>,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct LibrarySnapshot {
    pub roots: Vec<String>,
    pub total_roms: usize,
    pub by_system: HashMap<String, usize>,
    pub roms: Vec<RomEntry>,
}

pub type SharedLibrary = Arc<RwLock<LibrarySnapshot>>;
pub type SharedFavorites = Arc<RwLock<HashSet<String>>>;

#[derive(Debug, Deserialize, Default)]
pub struct SyncRequest {
    #[serde(default)]
    pub paths: Vec<String>,
}

#[derive(Debug, Deserialize, Default)]
pub struct RomFilterQuery {
    pub system: Option<String>,
    pub q: Option<String>,
    #[serde(default)]
    pub favorites_only: bool,
}

#[derive(Debug, Deserialize, Default)]
pub struct ArtworkQuery {
    pub id: Option<String>,
    pub rom_path: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct FavoriteToggleRequest {
    pub id: String,
}

#[derive(Debug, Serialize)]
pub struct RomResponseItem<'a> {
    #[serde(flatten)]
    pub entry: &'a RomEntry,
    pub is_favorite: bool,
}

struct SystemProfile {
    system: &'static str,
    emulator: &'static str,
    core: &'static str,
    extensions: &'static [&'static str],
}

fn match_system_profile(folder_name: &str) -> Option<SystemProfile> {
    match folder_name.to_ascii_lowercase().as_str() {
        "snes" | "sfc" | "supernintendo" => Some(SystemProfile {
            system: "snes",
            emulator: "retroarch",
            core: "snes9x",
            extensions: &["sfc", "smc", "fig", "zip", "7z"],
        }),
        "nes" | "fc" | "famicom" => Some(SystemProfile {
            system: "nes",
            emulator: "retroarch",
            core: "nestopia",
            extensions: &["nes", "unf", "zip", "7z"],
        }),
        "gba" => Some(SystemProfile {
            system: "gba",
            emulator: "retroarch",
            core: "mgba",
            extensions: &["gba", "zip", "7z"],
        }),
        "gbc" | "gb" => Some(SystemProfile {
            system: "gbc",
            emulator: "retroarch",
            core: "gambatte",
            extensions: &["gb", "gbc", "zip", "7z"],
        }),
        "megadrive" | "genesis" | "md" => Some(SystemProfile {
            system: "megadrive",
            emulator: "retroarch",
            core: "genesis_plus_gx",
            extensions: &["md", "bin", "gen", "smd", "zip", "7z"],
        }),
        "ps1" | "psx" | "playstation" => Some(SystemProfile {
            system: "ps1",
            emulator: "duckstation",
            core: "swanstation",
            // Omite .bin para não listar faixas de áudio separadas de jogos multi-track (.cue/.chd)
            extensions: &["chd", "cue", "pbp", "iso", "m3u"],
        }),
        "ps2" | "pcsx2" => Some(SystemProfile {
            system: "ps2",
            emulator: "pcsx2",
            core: "",
            extensions: &["iso", "chd", "cso", "gz"],
        }),
        "psp" | "ppsspp" => Some(SystemProfile {
            system: "psp",
            emulator: "ppsspp",
            core: "",
            extensions: &["iso", "cso", "pbp"],
        }),
        "n64" | "mupen64" => Some(SystemProfile {
            system: "n64",
            emulator: "mupen64",
            core: "mupen64plus_next",
            extensions: &["z64", "n64", "v64", "zip", "7z"],
        }),
        "gc" | "gamecube" => Some(SystemProfile {
            system: "gc",
            emulator: "dolphin",
            core: "",
            extensions: &["iso", "rvz", "gcz", "ciso"],
        }),
        "wii" => Some(SystemProfile {
            system: "wii",
            emulator: "dolphin",
            core: "",
            extensions: &["iso", "rvz", "wbfs", "gcz"],
        }),
        "dreamcast" | "dc" => Some(SystemProfile {
            system: "dreamcast",
            emulator: "retroarch",
            core: "flycast",
            extensions: &["chd", "cdi", "gdi"],
        }),
        "arcade" | "fbneo" | "mame" | "neogeo" => Some(SystemProfile {
            system: "arcade",
            emulator: "retroarch",
            core: "fbneo",
            extensions: &["zip", "7z"],
        }),
        _ => None,
    }
}

fn compute_rom_id(path: &str) -> String {
    let mut hash: u64 = 0xcbf29ce484222325;
    for byte in path.as_bytes() {
        hash ^= u64::from(*byte);
        hash = hash.wrapping_mul(0x100000001b3);
    }
    format!("{:016x}", hash)
}

#[derive(Debug, Clone, Default)]
struct GamelistEntry {
    name: Option<String>,
    desc: Option<String>,
    image_path: Option<PathBuf>,
}

fn normalize_rel_key(raw_path: &str) -> String {
    let unix_style = raw_path.trim().replace('\\', "/");
    unix_style
        .strip_prefix("./")
        .unwrap_or(&unix_style)
        .trim_start_matches('/')
        .to_string()
}

fn unescape_xml(input: &str) -> String {
    let trimmed = input.trim();
    let without_cdata = if let Some(inner) = trimmed
        .strip_prefix("<![CDATA[")
        .and_then(|s| s.strip_suffix("]]>"))
    {
        inner.trim()
    } else {
        trimmed
    };

    without_cdata
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", "\"")
        .replace("&apos;", "'")
        .replace("&#39;", "'")
        .replace("&#10;", "\n")
        .replace("&#13;", "")
}

fn extract_xml_tag(block: &str, tag: &str) -> Option<String> {
    let open_pattern = format!("<{}", tag);
    let start_idx = block.find(&open_pattern)?;
    let after_open = &block[start_idx + open_pattern.len()..];

    // Garante que o nome da tag terminou (evita confundir <name> com <namesake>)
    let first_char = after_open.chars().next()?;
    if first_char != '>' && !first_char.is_whitespace() {
        return None;
    }

    let content_offset = after_open.find('>')? + 1;
    let rest = &after_open[content_offset..];
    let close_pattern = format!("</{}>", tag);
    let end_idx = rest.find(&close_pattern)?;

    let value = unescape_xml(&rest[..end_idx]);
    if value.is_empty() {
        None
    } else {
        Some(value)
    }
}

fn resolve_gamelist_image(system_dir: &Path, raw_image: &str) -> Option<PathBuf> {
    let clean = raw_image.trim().replace('\\', "/");
    if clean.is_empty() {
        return None;
    }

    let candidate = if clean.starts_with('/') {
        PathBuf::from(&clean)
    } else {
        let rel = clean.strip_prefix("./").unwrap_or(&clean);
        system_dir.join(rel)
    };

    if candidate.is_file() {
        Some(candidate)
    } else {
        None
    }
}

/// Lê system_dir/gamelist.xml e indexa metadados pela rota relativa da ROM
fn parse_gamelist_xml(system_dir: &Path) -> HashMap<String, GamelistEntry> {
    let mut map = HashMap::new();
    let xml_path = system_dir.join("gamelist.xml");
    let Ok(content) = fs::read_to_string(&xml_path) else {
        return map;
    };

    let mut cursor = content.as_str();
    while let Some(game_start) = cursor.find("<game") {
        let after_tag = &cursor[game_start + 5..];
        let Some(tag_end) = after_tag.find('>') else {
            break;
        };
        let body = &after_tag[tag_end + 1..];
        let Some(game_end) = body.find("</game>") else {
            break;
        };

        let block = &body[..game_end];
        if let Some(raw_rom_path) = extract_xml_tag(block, "path") {
            let key = normalize_rel_key(&raw_rom_path);
            let name = extract_xml_tag(block, "name");
            let desc = extract_xml_tag(block, "desc");
            let image_path = extract_xml_tag(block, "image")
                .and_then(|img| resolve_gamelist_image(system_dir, &img));

            map.insert(
                key,
                GamelistEntry {
                    name,
                    desc,
                    image_path,
                },
            );
        }

        cursor = &body[game_end + 7..];
    }

    map
}

/// Procura imagens PNG/JPG/WebP seguindo convenções padrão ao lado da ROM
pub fn find_artwork_for_rom(rom_path: &Path) -> Option<PathBuf> {
    let parent = rom_path.parent()?;
    let stem = rom_path.file_stem()?.to_str()?;
    let extensions = ["png", "jpg", "jpeg", "webp"];

    let candidate_dirs = [
        parent.to_path_buf(),
        parent.join("covers"),
        parent.join("boxart"),
        parent.join("images"),
        parent.join("media/boxart"),
        parent.join("media/images"),
    ];

    for dir in &candidate_dirs {
        for ext in extensions {
            let direct = dir.join(format!("{}.{}", stem, ext));
            if direct.is_file() {
                return Some(direct);
            }

            // Convenção Skyscraper / EmulationStation (<nome>-image.png)
            let suffix = dir.join(format!("{}-image.{}", stem, ext));
            if suffix.is_file() {
                return Some(suffix);
            }
        }
    }

    None
}

/// Combina os caminhos recebidos do Android com as montagens ativas em /proc/mounts e $HOME
pub fn discover_storage_roots(extra_paths: &[String]) -> Vec<PathBuf> {
    let mut roots = BTreeSet::new();

    for raw in extra_paths {
        let p = PathBuf::from(raw.trim());
        if p.exists() && p.is_dir() {
            roots.insert(p);
        }
    }

    if let Ok(env_paths) = env::var("ARENA_STORAGE_PATHS") {
        for raw in env_paths.split(':').filter(|s| !s.is_empty()) {
            let p = PathBuf::from(raw);
            if p.exists() && p.is_dir() {
                roots.insert(p);
            }
        }
    }

    let internal = PathBuf::from("/storage/emulated/0");
    if internal.exists() {
        roots.insert(internal);
    }
    if let Ok(home) = env::var("HOME") {
        let home_path = PathBuf::from(home);
        if home_path.exists() {
            roots.insert(home_path);
        }
    }

    if let Ok(mounts) = fs::read_to_string("/proc/mounts") {
        for line in mounts.lines() {
            let mut parts = line.split_whitespace();
            let _device = parts.next();
            let Some(mount_point) = parts.next() else { continue };
            let Some(fs_type) = parts.next() else { continue };

            let is_external_prefix = (mount_point.starts_with("/storage/")
                && !mount_point.starts_with("/storage/emulated")
                && !mount_point.starts_with("/storage/self"))
                || mount_point.starts_with("/mnt/media_rw/");

            let is_supported_fs = matches!(
                fs_type,
                "vfat" | "exfat" | "ntfs" | "fuse" | "sdfat" | "sdcardfs" | "ext4"
            );

            if is_external_prefix && is_supported_fs {
                let path = PathBuf::from(mount_point);
                if path.exists() && fs::read_dir(&path).is_ok() {
                    roots.insert(path);
                }
            }
        }
    }

    roots.into_iter().collect()
}

fn walk_roms(
    system_root: &Path,
    dir: &Path,
    profile: &SystemProfile,
    gamelist: &HashMap<String, GamelistEntry>,
    depth: usize,
    out: &mut Vec<RomEntry>,
) {
    if depth > 4 {
        return;
    }
    let Ok(entries) = fs::read_dir(dir) else {
        return;
    };

    for entry in entries.flatten() {
        let Ok(file_type) = entry.file_type() else {
            continue;
        };
        if file_type.is_symlink() {
            continue;
        }

        let path = entry.path();
        let file_name = entry.file_name();
        let name_str = file_name.to_string_lossy();

        if name_str.starts_with('.') {
            continue;
        }

        if file_type.is_dir() {
            walk_roms(system_root, &path, profile, gamelist, depth + 1, out);
        } else if file_type.is_file() {
            let ext = path
                .extension()
                .and_then(|e| e.to_str())
                .map(|e| e.to_ascii_lowercase())
                .unwrap_or_default();

            if profile.extensions.contains(&ext.as_str()) {
                let rel_key = path
                    .strip_prefix(system_root)
                    .ok()
                    .and_then(|p| p.to_str())
                    .map(normalize_rel_key)
                    .unwrap_or_default();

                let meta = gamelist.get(&rel_key);

                let fallback_title = path
                    .file_stem()
                    .and_then(|s| s.to_str())
                    .unwrap_or("Unknown")
                    .to_string();

                let title = meta
                    .and_then(|m| m.name.clone())
                    .unwrap_or(fallback_title);
                let description = meta.and_then(|m| m.desc.clone());

                let custom_artwork_path = meta
                    .and_then(|m| m.image_path.clone())
                    .or_else(|| find_artwork_for_rom(&path));

                let path_str = path.to_string_lossy().into_owned();
                let id = compute_rom_id(&path_str);
                let artwork_url = custom_artwork_path
                    .as_ref()
                    .map(|_| format!("/api/artwork?id={}", id));

                let size_bytes = entry.metadata().map(|m| m.len()).unwrap_or(0);

                out.push(RomEntry {
                    id,
                    title,
                    description,
                    system: profile.system.to_string(),
                    emulator: profile.emulator.to_string(),
                    core: profile.core.to_string(),
                    path: path_str,
                    size_bytes,
                    artwork_url,
                    custom_artwork_path,
                });
            }
        }
    }
}

/// Executa a varredura síncrona completa de forma isolada
pub fn scan_all_roms(extra_paths: &[String]) -> LibrarySnapshot {
    let roots = discover_storage_roots(extra_paths);
    let mut roms = Vec::new();
    let candidate_subfolders = ["ROMs", "roms", "Roms", "ARENA/roms", "ARENA/ROMs"];

    for root in &roots {
        for sub in candidate_subfolders {
            let roms_base = root.join(sub);
            let Ok(system_dirs) = fs::read_dir(&roms_base) else {
                continue;
            };

            for sys_entry in system_dirs.flatten() {
                let Ok(ft) = sys_entry.file_type() else {
                    continue;
                };
                if !ft.is_dir() || ft.is_symlink() {
                    continue;
                }

                let folder_name = sys_entry.file_name().to_string_lossy().into_owned();
                if let Some(profile) = match_system_profile(&folder_name) {
                    let sys_dir = sys_entry.path();
                    let gamelist = parse_gamelist_xml(&sys_dir);
                    walk_roms(&sys_dir, &sys_dir, &profile, &gamelist, 0, &mut roms);
                }
            }
        }
    }

    roms.sort_by(|a, b| a.title.to_lowercase().cmp(&b.title.to_lowercase()));
    roms.dedup_by(|a, b| a.path == b.path);

    let mut by_system: HashMap<String, usize> = HashMap::new();
    for rom in &roms {
        *by_system.entry(rom.system.clone()).or_insert(0) += 1;
    }

    LibrarySnapshot {
        roots: roots
            .into_iter()
            .map(|p| p.to_string_lossy().into_owned())
            .collect(),
        total_roms: roms.len(),
        by_system,
        roms,
    }
}

fn cache_file_path() -> PathBuf {
    let base = env::var("ARENA_DATA_DIR").unwrap_or_else(|_| ".".to_string());
    PathBuf::from(base).join("library_cache.json")
}

pub fn load_cached_library() -> LibrarySnapshot {
    let path = cache_file_path();
    fs::read_to_string(path)
        .ok()
        .and_then(|raw| serde_json::from_str(&raw).ok())
        .unwrap_or_default()
}

fn save_cached_library(snapshot: &LibrarySnapshot) {
    let path = cache_file_path();
    if let Ok(json) = serde_json::to_string(snapshot) {
        let _ = fs::write(path, json);
    }
}

fn favorites_file_path() -> PathBuf {
    let base = env::var("ARENA_DATA_DIR").unwrap_or_else(|_| ".".to_string());
    PathBuf::from(base).join("favorites.json")
}

pub fn load_favorites() -> HashSet<String> {
    fs::read_to_string(favorites_file_path())
        .ok()
        .and_then(|raw| serde_json::from_str::<Vec<String>>(&raw).ok())
        .map(|list| list.into_iter().collect())
        .unwrap_or_default()
}

fn save_favorites(favorites: &HashSet<String>) {
    let path = favorites_file_path();
    let list: Vec<&String> = favorites.iter().collect();
    if let Ok(json) = serde_json::to_string_pretty(&list) {
        let _ = fs::write(path, json);
    }
}

/// POST /api/storage/sync — Indexa armazenamento e notifica o frontend via WebSocket
pub async fn sync_storage_handler(
    State(library): State<SharedLibrary>,
    State(events): State<EventBus>,
    payload: Option<Json<SyncRequest>>,
) -> impl IntoResponse {
    let extra_paths = payload.map(|p| p.0.paths).unwrap_or_default();

    let scan_result = tokio::task::spawn_blocking(move || {
        let snapshot = scan_all_roms(&extra_paths);
        save_cached_library(&snapshot);
        snapshot
    })
    .await;

    match scan_result {
        Ok(snapshot) => {
            let event = ArenaEvent::StorageUpdated {
                roots: snapshot.roots.clone(),
                total_roms: snapshot.total_roms,
                by_system: snapshot.by_system.clone(),
            };

            let summary = serde_json::json!({
                "ok": true,
                "roots": snapshot.roots,
                "total_roms": snapshot.total_roms,
                "by_system": snapshot.by_system,
            });

            *library.write().await = snapshot;
            events.publish(&event);

            (StatusCode::OK, Json(summary)).into_response()
        }
        Err(e) => (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(serde_json::json!({ "ok": false, "error": e.to_string() })),
        )
            .into_response(),
    }
}

/// GET /api/storage — Retorna raízes montadas e contadores por console sem trafegar a lista completa
pub async fn get_storage_handler(State(library): State<SharedLibrary>) -> impl IntoResponse {
    let guard = library.read().await;
    Json(serde_json::json!({
        "roots": guard.roots,
        "total_roms": guard.total_roms,
        "by_system": guard.by_system,
    }))
}

/// GET /api/roms?system=snes&q=zelda — Busca instantânea em título e sinopse
pub async fn get_roms_handler(
    State(library): State<SharedLibrary>,
    State(favorites): State<SharedFavorites>,
    Query(filter): Query<RomFilterQuery>,
) -> impl IntoResponse {
    let lib_guard = library.read().await;
    let fav_guard = favorites.read().await;

    let sys_filter = filter.system.map(|s| s.to_ascii_lowercase());
    let text_filter = filter
        .q
        .map(|q| q.trim().to_ascii_lowercase())
        .filter(|q| !q.is_empty());

    let only_favs = filter.favorites_only || sys_filter.as_deref() == Some("favorites");

    let filtered: Vec<RomResponseItem<'_>> = lib_guard
        .roms
        .iter()
        .filter(|rom| {
            let is_fav = fav_guard.contains(&rom.id);
            if only_favs && !is_fav {
                return false;
            }

            let match_sys = match sys_filter.as_deref() {
                None | Some("all") | Some("favorites") => true,
                Some(s) => rom.system == s,
            };
            if !match_sys {
                return false;
            }

            if let Some(ref query) = text_filter {
                let in_title = rom.title.to_ascii_lowercase().contains(query);
                let in_desc = rom
                    .description
                    .as_deref()
                    .map(|d| d.to_ascii_lowercase().contains(query))
                    .unwrap_or(false);
                return in_title || in_desc;
            }

            true
        })
        .map(|rom| RomResponseItem {
            entry: rom,
            is_favorite: fav_guard.contains(&rom.id),
        })
        .collect();

    Json(filtered)
}

/// GET /api/artwork?id=<hash> — Serve capas locais direto do SD/USB sem embutir no binário
pub async fn get_artwork_handler(
    State(library): State<SharedLibrary>,
    Query(params): Query<ArtworkQuery>,
) -> impl IntoResponse {
    let img_path_opt = {
        let guard = library.read().await;
        guard
            .roms
            .iter()
            .find(|r| {
                params.id.as_deref() == Some(r.id.as_str())
                    || params.rom_path.as_deref() == Some(r.path.as_str())
            })
            .and_then(|r| {
                r.custom_artwork_path
                    .clone()
                    .or_else(|| find_artwork_for_rom(Path::new(&r.path)))
            })
    };

    let Some(img_path) = img_path_opt else {
        return StatusCode::NOT_FOUND.into_response();
    };

    let mime = match img_path
        .extension()
        .and_then(|e| e.to_str())
        .map(|e| e.to_ascii_lowercase())
        .as_deref()
    {
        Some("png") => "image/png",
        Some("jpg") | Some("jpeg") => "image/jpeg",
        Some("webp") => "image/webp",
        _ => return StatusCode::UNSUPPORTED_MEDIA_TYPE.into_response(),
    };

    match tokio::fs::read(&img_path).await {
        Ok(bytes) => (
            StatusCode::OK,
            [
                (header::CONTENT_TYPE, mime),
                (header::CACHE_CONTROL, "public, max-age=86400"),
            ],
            bytes,
        )
            .into_response(),
        Err(_) => StatusCode::NOT_FOUND.into_response(),
    }
}

/// POST /api/favorites/toggle — Alterna favorito por ID e persiste em favorites.json
pub async fn toggle_favorite_handler(
    State(favorites): State<SharedFavorites>,
    State(events): State<EventBus>,
    Json(payload): Json<FavoriteToggleRequest>,
) -> impl IntoResponse {
    let mut guard = favorites.write().await;
    let is_favorite = if guard.contains(&payload.id) {
        guard.remove(&payload.id);
        false
    } else {
        guard.insert(payload.id.clone());
        true
    };

    save_favorites(&guard);
    let ids: Vec<String> = guard.iter().cloned().collect();
    let total = ids.len();
    drop(guard);

    events.publish(&ArenaEvent::FavoritesUpdated { ids });

    Json(serde_json::json!({
        "ok": true,
        "id": payload.id,
        "is_favorite": is_favorite,
        "total_favorites": total
    }))
}

/// GET /api/favorites — Retorna lista de IDs favoritados
pub async fn get_favorites_handler(State(favorites): State<SharedFavorites>) -> impl IntoResponse {
    let guard = favorites.read().await;
    let ids: Vec<&String> = guard.iter().collect();
    Json(ids)
}

/// GET /api/emulators — Paridade Linux/Chromebook verificando binários no PATH
pub async fn get_installed_emulators_handler() -> Json<serde_json::Value> {
    let has_bin = |names: &[&str]| -> bool {
        env::var_os("PATH")
            .map(|paths| {
                env::split_paths(&paths).any(|dir| names.iter().any(|n| dir.join(n).is_file()))
            })
            .unwrap_or(false)
    };

    let retroarch = has_bin(&["retroarch"]);
    let pcsx2 = has_bin(&["pcsx2", "pcsx2-qt"]);
    let dolphin = has_bin(&["dolphin-emu", "dolphin-emu-nogui"]);
    let ppsspp = has_bin(&["PPSSPPSDL", "ppsspp"]);

    Json(serde_json::json!({
        "emulators": {
            "retroarch": retroarch,
            "pcsx2": pcsx2,
            "dolphin": dolphin,
            "ppsspp": ppsspp
        }
    }))
}