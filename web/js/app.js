"use strict";

/* Client for the localhost API. Resolves the base URL from Eel (desktop) or
   falls back to the page origin (FastAPI serves the UI on the API port). */
const Api = (() => {
  let base = null;

  async function init() {
    if (base) return base;
    if (window.eel && typeof window.eel.get_app_info === "function") {
      try {
        const data = await new Promise((resolve) => eel.get_app_info()(resolve));
        if (data && data.api_url) {
          base = data.api_url;
          return base;
        }
      } catch (err) {
        console.warn("eel.get_app_info failed:", err);
      }
    }
    base = window.location.origin;
    return base;
  }

  function setBase(value) {
    base = value ? value.replace(/\/+$/, "") : null;
  }

  async function json(method, path, body) {
    const options = { method, headers: { "Content-Type": "application/json" } };
    if (body !== undefined) options.body = JSON.stringify(body);
    const resp = await fetch((await init()) + path, options);
    if (resp.status === 204) return null;
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) throw new Error(data.detail || "HTTP " + resp.status);
    return data;
  }

  return {
    init,
    setBase,
    getInfo: (url) => json("GET", "/api/info" + (url ? "?url=" + encodeURIComponent(url) : "")),
    list: () => json("GET", "/api/downloads"),
    get: (id) => json("GET", "/api/downloads/" + encodeURIComponent(id)),
    create: (payload) => json("POST", "/api/downloads", payload),
    cancel: (id) => json("POST", "/api/downloads/" + encodeURIComponent(id) + "/cancel"),
    remove: (id) => json("DELETE", "/api/downloads/" + encodeURIComponent(id)),
  };
})();

/* In-memory state: id -> download record. */
const store = { downloads: new Map() };

const el = {
  form: document.getElementById("download-form"),
  url: document.getElementById("url"),
  format: document.getElementById("format"),
  container: document.getElementById("container"),
  quality: document.getElementById("quality"),
  directory: document.getElementById("directory"),
  directoryPicker: document.getElementById("directory-picker"),
  chooseDirectory: document.getElementById("choose-directory"),
  submit: document.getElementById("submit"),
  list: document.getElementById("downloads"),
  empty: document.getElementById("empty"),
  info: document.getElementById("info"),
  refresh: document.getElementById("refresh"),
};

const STATUS_LABELS = {
  pending: "En cola",
  downloading: "Descargando",
  processing: "Procesando",
  completed: "Completado",
  error: "Error",
  cancelled: "Cancelado",
};

function esc(value) {
  const node = document.createElement("div");
  node.textContent = value == null ? "" : String(value);
  return node.innerHTML;
}

function clamp(percent) {
  return Math.max(0, Math.min(100, Number(percent) || 0));
}

function isActive(status) {
  return status === "pending" || status === "downloading" || status === "processing";
}

function upsert(item) {
  if (!item || !item.id) return;
  store.downloads.set(item.id, { ...store.downloads.get(item.id), ...item });
  renderAll();
}

function removeItem(id) {
  store.downloads.delete(id);
  renderAll();
}

function renderAll() {
  const items = [...store.downloads.values()];
  el.empty.hidden = items.length > 0;
  el.list.replaceChildren(...items.map(renderItem));
}

function renderItem(item) {
  const article = document.createElement("article");
  article.className = "download" + (item.status === "error" ? " error" : "");
  article.setAttribute("role", "listitem");
  article.dataset.id = item.id;

  const active = isActive(item.status);
  const label = STATUS_LABELS[item.status] || item.status;
  const kindLabel = item.format === "audio" ? "Audio MP3" : "Vídeo";

  article.innerHTML =
    '<div class="download-head">' +
    '<span class="download-url" title="' + esc(item.url || item.id) + '">' +
    esc(item.file || item.url || item.id) +
    "</span>" +
    '<span class="badge badge-' + esc(item.status) + '">' + esc(label) + "</span>" +
    "</div>" +
    '<div class="download-meta">' +
    "<span>" + esc(kindLabel + " · " + item.quality) + "</span>" +
    (item.speed ? "<span>" + esc(item.speed) + "</span>" : "") +
    (item.eta ? "<span>ETA " + esc(item.eta) + "</span>" : "") +
    "</div>" +
    '<div class="progress"><div class="progress-bar" style="width:' +
    clamp(item.progress) + '%"></div></div>' +
    (item.error_message
      ? '<p class="error">' + esc(item.error_message) + "</p>"
      : "") +
    '<div class="download-actions">' +
    (active
      ? '<button class="btn" type="button" data-action="cancel">Cancelar</button>'
      : '<button class="btn btn-danger" type="button" data-action="delete">Eliminar</button>') +
    "</div>";

  const cancelBtn = article.querySelector("[data-action=cancel]");
  if (cancelBtn) cancelBtn.addEventListener("click", () => onCancel(item.id));

  const deleteBtn = article.querySelector("[data-action=delete]");
  if (deleteBtn) deleteBtn.addEventListener("click", () => onDelete(item.id));

  return article;
}

function renderQualities(media) {
  const key = el.format.value === "audio" ? "audio" : "video";
  const values = media?.formats?.[key] || [];
  el.quality.replaceChildren(new Option("Mejor calidad", "best"));
  values.forEach((item) => {
    const suffix = key === "audio" ? " kbps" : "p";
    el.quality.add(new Option(item.quality + suffix, item.quality));
  });
  el.quality.disabled = values.length === 0;
}

async function analyzeUrl() {
  const url = el.url.value.trim();
  if (!url) {
    el.url.focus();
    return;
  }
  try {
    const response = await Api.getInfo(url);
    renderQualities(response.media);
    el.info.textContent = response.media?.title || "URL analizada";
  } catch (err) {
    renderQualities(null);
    window.alert("No se pudo analizar la URL:\n" + err.message);
  }
}

async function onCreate(event) {
  event.preventDefault();
  const url = el.url.value.trim();
  if (!url) {
    el.url.focus();
    return;
  }
  if (el.quality.disabled) {
    await analyzeUrl();
    if (el.quality.disabled) return;
  }
  const payload = {
    url,
    format: el.format.value,
    container: el.container.value,
    quality: el.quality.value,
  };
  const directory = el.directory.value.trim();
  if (directory) payload.directory = directory;

  el.submit.disabled = true;
  try {
    upsert(await Api.create(payload));
    el.url.value = "";
    el.directory.value = "";
  } catch (err) {
    window.alert("No se pudo iniciar la descarga:\n" + err.message);
  } finally {
    el.submit.disabled = false;
  }
}

async function onCancel(id) {
  try {
    upsert(await Api.cancel(id));
  } catch (err) {
    window.alert(err.message);
  }
}

async function onDelete(id) {
  try {
    await Api.remove(id);
    removeItem(id);
  } catch (err) {
    window.alert(err.message);
  }
}

async function loadInfo() {
  try {
    const data = await Api.getInfo();
    const parts = ["backend v" + data.version];
    if (data.yt_dlp_version) parts.push("yt-dlp " + data.yt_dlp_version);
    if (data.ffmpeg_available) parts.push("FFmpeg OK");
    el.info.textContent = parts.join(" · ");
    if (!el.directory.value && data.downloads_dir) {
      el.directory.placeholder = data.downloads_dir;
    }
  } catch (err) {
    el.info.textContent = "backend offline";
  }
}

async function refreshList() {
  try {
    const data = await Api.list();
    (data.items || []).forEach(upsert);
  } catch (err) {
    el.info.textContent = "backend offline";
  }
}

const lastRefresh = new Map();

function maybeRefreshFull(id) {
  const now = Date.now();
  if (now - (lastRefresh.get(id) || 0) < 1500) return;
  lastRefresh.set(id, now);
  Api.get(id).then(upsert).catch(() => {});
}

function applyProgressEvent(data) {
  if (!data || !data.download_id) return;
  const existing = store.downloads.get(data.download_id) || {};
  upsert({
    ...existing,
    id: data.download_id,
    status: data.status,
    progress: data.progress,
    speed: data.speed,
    eta: data.eta,
  });
  if (data.status === "completed" || data.status === "error" || data.status === "cancelled") {
    maybeRefreshFull(data.download_id);
  }
}

/* Real-time progress via WebSocket, with HTTP polling as fallback. */
let socket = null;
let pollTimer = null;

async function connectSocket() {
  try {
    const base = await Api.init();
    const url = base.replace(/^http/, "ws") + "/ws/progress";
    socket = new WebSocket(url);
    socket.onopen = () => stopPolling();
    socket.onmessage = (event) => {
      try {
        applyProgressEvent(JSON.parse(event.data));
      } catch (err) {
        console.warn("Malformed progress message:", err);
      }
    };
    socket.onclose = () => startPolling();
    socket.onerror = () => socket.close();
  } catch (err) {
    startPolling();
  }
}

function startPolling() {
  if (pollTimer) return;
  pollTimer = setInterval(refreshList, 2000);
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

el.form.addEventListener("submit", onCreate);
el.url.addEventListener("change", analyzeUrl);
el.url.addEventListener("blur", analyzeUrl);
el.format.addEventListener("change", () => {
  const audio = el.format.value === "audio";
  el.container.replaceChildren(
    ...(audio
      ? [new Option("MP3", "mp3"), new Option("M4A", "m4a")]
      : [new Option("MP4", "mp4"), new Option("WebM", "webm"), new Option("AVI", "avi")]),
  );
  renderQualities(null);
});
el.chooseDirectory.addEventListener("click", async () => {
  if (window.eel && typeof window.eel.select_download_folder === "function") {
    const selected = await new Promise((resolve) => eel.select_download_folder()(resolve));
    if (selected) el.directory.value = selected;
    return;
  }
  el.directoryPicker.click();
});
el.directoryPicker.addEventListener("change", () => {
  const file = el.directoryPicker.files?.[0];
  if (file?.webkitRelativePath) {
    el.directory.value = file.webkitRelativePath.split("/")[0];
  }
});
el.refresh.addEventListener("click", refreshList);
renderQualities(null);

Api.init().then(() => {
  connectSocket();
  loadInfo();
  refreshList();
});