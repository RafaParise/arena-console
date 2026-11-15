// ============================================================================
// ARENA Console — Integração Frontend Completa
// (WebSocket /ws, Filtro de Emuladores Instalados, Capas Lazy + Fallback,
//  Sinopse gamelist.xml, Busca Instantânea com AbortController e Favoritos)
// ============================================================================

const FALLBACK_COVER =
  "data:image/svg+xml;utf8," +
  encodeURIComponent(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 400" fill="#18181b">' +
      '<rect width="300" height="400" rx="12"/>' +
      '<text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" ' +
      'fill="#52525b" font-family="sans-serif" font-size="18">NO COVER</text>' +
    "</svg>"
  );

function initArenaWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws`;
  const socket = new WebSocket(wsUrl);

  socket.onmessage = async (event) => {
    try {
      const msg = JSON.parse(event.data);
      if (msg.event === "storage_updated") {
        console.log(`[ARENA-WS] Armazenamento atualizado: ${msg.data.total_roms} ROMs`);
        if (typeof updateConsoleCounters === "function") {
          updateConsoleCounters(msg.data.by_system);
        }
        if (typeof reloadCurrentSystemGames === "function") {
          await reloadCurrentSystemGames();
        }
      } else if (msg.event === "favorites_updated") {
        if (typeof syncFavoriteBadges === "function") {
          syncFavoriteBadges(new Set(msg.data.ids || []));
        }
      }
    } catch (err) {
      console.error("[ARENA-WS] Erro ao processar evento:", err);
    }
  };

  socket.onclose = () => {
    // Reconecta em 2s caso a WebView retorne de suspensão ou o servidor reinicie
    setTimeout(initArenaWebSocket, 2000);
  };

  socket.onerror = () => {
    socket.close();
  };
}

async function applyInstalledEmulatorsFilter() {
  let allowedSystems = null;

  if (window.ArenaAndroid && typeof window.ArenaAndroid.getInstalledEmulators === "function") {
    try {
      const payload = JSON.parse(window.ArenaAndroid.getInstalledEmulators());
      allowedSystems = new Set(payload.systems || []);
      window.__arenaInstalledEmulators = payload.emulators || {};
    } catch (err) {
      console.error("[ARENA-UI] Falha ao ler emuladores do Android:", err);
      return;
    }
  } else {
    try {
      const res = await fetch("/api/emulators");
      if (res.ok) {
        const data = await res.json();
        const emu = data.emulators || {};
        window.__arenaInstalledEmulators = emu;
        allowedSystems = new Set();
        if (emu.retroarch) {
          ["snes", "nes", "gba", "gbc", "megadrive", "dreamcast", "arcade", "ps1", "n64"].forEach((s) =>
            allowedSystems.add(s)
          );
        }
        if (emu.pcsx2) allowedSystems.add("ps2");
        if (emu.dolphin) {
          allowedSystems.add("gc");
          allowedSystems.add("wii");
        }
        if (emu.ppsspp) allowedSystems.add("psp");
      }
    } catch {
      return;
    }
  }

  if (!allowedSystems) return;

  const consoleItems = document.querySelectorAll("[data-system]");
  let firstVisible = null;
  let activeWasHidden = false;

  consoleItems.forEach((el) => {
    const sys = (el.dataset.system || "").toLowerCase();
    if (sys === "all" || sys === "favorites") return;

    const isSupported = allowedSystems.has(sys);
    if (isSupported) {
      el.hidden = false;
      el.style.removeProperty("display");
      if (!firstVisible) firstVisible = el;
    } else {
      if (el.classList.contains("active") || document.activeElement === el) {
        activeWasHidden = true;
      }
      el.hidden = true;
      el.style.display = "none";
    }
  });

  // Evita que o foco do D-Pad fique preso em um botão oculto
  if (firstVisible && (activeWasHidden || !document.querySelector("[data-system].active:not([hidden])"))) {
    firstVisible.click();
    firstVisible.focus();
  }
}

function launchArenaRom(rom) {
  let emulator = rom.emulator;
  let core = rom.core || "";

  // Fallback PS1: se DuckStation não estiver instalado, usa RetroArch + core swanstation
  const emuMap = window.__arenaInstalledEmulators || {};
  if (emulator === "duckstation" && emuMap.duckstation === false && emuMap.retroarch === true) {
    emulator = "retroarch";
    core = "swanstation";
  }

  if (window.ArenaAndroid && typeof window.ArenaAndroid.launchGame === "function") {
    window.ArenaAndroid.launchGame(emulator, rom.path, core);
    return;
  }

  fetch("/api/launch", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      emulator,
      rom_path: rom.path,
      core,
    }),
  }).catch((err) => console.error("[ARENA-LAUNCH] Erro HTTP:", err));
}

function renderGameCard(rom) {
  const coverSrc = rom.artwork_url || FALLBACK_COVER;
  const favClass = rom.is_favorite ? " is-favorite" : "";
  const favStar = rom.is_favorite ? "★" : "☆";
  return `
    <button class="game-card${favClass}" data-id="${rom.id}" data-path="${rom.path}" data-emulator="${rom.emulator}" data-core="${rom.core}">
      <span class="fav-badge">${favStar}</span>
      <img
        src="${coverSrc}"
        alt="${rom.title}"
        loading="lazy"
        decoding="async"
        onerror="this.onerror=null;this.src='${FALLBACK_COVER}'"
      />
      <span>${rom.title}</span>
    </button>
  `;
}

function updateGameDetailsPanel(rom) {
  const titleEl = document.getElementById("detail-title");
  const descEl = document.getElementById("detail-description");

  if (titleEl) titleEl.textContent = rom.title;
  if (descEl) {
    descEl.textContent = rom.description || "Sem sinopse disponível no gamelist.xml.";
  }
}

let searchTimer = null;
let searchAbortController = null;

async function fetchFilteredGames({ system = "all", query = "" } = {}) {
  if (searchAbortController) {
    searchAbortController.abort();
  }
  searchAbortController = new AbortController();

  const params = new URLSearchParams();
  if (system) params.set("system", system);
  if (query.trim()) params.set("q", query.trim());

  try {
    const res = await fetch(`/api/roms?${params.toString()}`, {
      signal: searchAbortController.signal,
    });
    const roms = await res.json();
    if (typeof renderGameGrid === "function") {
      renderGameGrid(roms);
    }
  } catch (err) {
    if (err.name !== "AbortError") {
      console.error("[ARENA-SEARCH] Erro ao buscar ROMs:", err);
    }
  }
}

async function toggleFavoriteRom(romId, cardElement) {
  const res = await fetch("/api/favorites/toggle", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: romId }),
  });
  const data = await res.json();

  if (data.ok && cardElement) {
    cardElement.classList.toggle("is-favorite", data.is_favorite);
    const badge = cardElement.querySelector(".fav-badge");
    if (badge) badge.textContent = data.is_favorite ? "★" : "☆";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  initArenaWebSocket();
  applyInstalledEmulatorsFilter();

  const searchInput = document.getElementById("arena-search-input");
  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      const q = e.target.value;
      const activeSystem =
        q.trim().length > 0
          ? "all"
          : document.querySelector("[data-system].active")?.dataset.system || "all";

      clearTimeout(searchTimer);
      searchTimer = setTimeout(() => {
        fetchFilteredGames({ system: activeSystem, query: q });
      }, 100);
    });
  }
});

document.addEventListener("visibilitychange", () => {
  if (!document.hidden) applyInstalledEmulatorsFilter();
});

window.addEventListener("keydown", (e) => {
  if (document.activeElement?.tagName === "INPUT") return;
  if (e.key.toLowerCase() === "f") {
    const focusedCard = document.activeElement?.closest(".game-card");
    if (focusedCard?.dataset.id) {
      toggleFavoriteRom(focusedCard.dataset.id, focusedCard);
    }
  }
});