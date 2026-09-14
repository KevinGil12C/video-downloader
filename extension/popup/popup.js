"use strict";

const DEFAULT_SETTINGS = {
  apiBase: "http://127.0.0.1:8000",
  format: "video",
  container: "mp4",
  quality: "best",
};

const STATUS_LABELS = {
  pending: "En cola",
  downloading: "Descargando",
  processing: "Procesando",
  completed: "Completado",
  error: "Error",
  cancelled: "Cancelado",
};

const el = {
  status: document.getElementById("status"),
  statusDot: document.getElementById("status-dot"),
  form: document.getElementById("download-form"),
  url: document.getElementById("url"),
  format: document.getElementById("format"),
  container: document.getElementById("container"),
  quality: document.getElementById("quality"),
  directory: document.getElementById("directory"),
  chooseDirectory: document.getElementById("choose-directory"),
  download: document.getElementById("download"),
  formError: document.getElementById("form-error"),
  list: document.getElementById("list"),
  empty: document.getElementById("empty"),
  openOptions: document.getElementById("open-options"),
  openUi: document.getElementById("open-ui"),
};

function send(message) {
  return new Promise((resolve) => {
    chrome.runtime.sendMessage(message, (response) => resolve(response));
  });
}

function updateContainers() {
  const audio = el.format.value === "audio";
  el.container.replaceChildren(
    ...(audio
      ? [new Option("MP3", "mp3"), new Option("M4A", "m4a")]
      : [new Option("MP4", "mp4"), new Option("WebM", "webm"), new Option("AVI", "avi")]),
  );
}

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

function setStatus(ok, text) {
  el.status.textContent = text;
  el.statusDot.classList.toggle("offline", !ok);
}

function showError(message) {
  el.formError.textContent = message;
  el.formError.hidden = false;
}

function hideError() {
  el.formError.hidden = true;
}

function renderItem(item) {
  const li = document.createElement("li");
  const label = STATUS_LABELS[item.status] || item.status;
  li.innerHTML =
    '<div class="item-head">' +
    '<span class="url" title="' + esc(item.url || item.id) + '">' +
    esc(item.file || item.url || item.id) +
    "</span>" +
    '<span class="badge badge-' + esc(item.status) + '">' + esc(label) + "</span>" +
    "</div>" +
    '<div class="progress"><div class="bar" style="width:' + clamp(item.progress) + '%"></div></div>' +
    '<div class="item-meta">' +
    (item.speed ? "<span>" + esc(item.speed) + "</span>" : "") +
    (item.eta ? "<span>ETA " + esc(item.eta) + "</span>" : "") +
    "</div>" +
    (item.error_message ? '<div class="error">' + esc(item.error_message) + "</div>" : "") +
    '<div class="actions">' +
    (isActive(item.status)
      ? '<button type="button" data-cancel="' + esc(item.id) + '">Cancelar</button>'
      : '<button type="button" data-delete="' + esc(item.id) + '">Eliminar</button>') +
    "</div>";

  const cancelBtn = li.querySelector("[data-cancel]");
  if (cancelBtn) {
    cancelBtn.addEventListener("click", () => send({ type: "cancel", id: item.id }));
  }
  const deleteBtn = li.querySelector("[data-delete]");
  if (deleteBtn) {
    deleteBtn.addEventListener("click", async () => {
      await send({ type: "delete", id: item.id });
      await refresh();
    });
  }
  return li;
}

async function refresh() {
  const result = await send({ type: "list" });
  if (!result || !result.ok) return;
  const items = result.data.items || [];
  el.empty.hidden = items.length > 0;
  el.list.replaceChildren(...items.map(renderItem));
}

function renderQualities(media) {
  const values = media?.formats?.[el.format.value === "audio" ? "audio" : "video"] || [];
  el.quality.replaceChildren(new Option("Mejor calidad", "best"));
  values.forEach((item) => {
    const suffix = el.format.value === "audio" ? " kbps" : "p";
    el.quality.add(new Option(item.quality + suffix, item.quality));
  });
  el.quality.disabled = values.length === 0;
}

async function analyzeUrl(url) {
  if (!url) {
    showError("No se detectó una URL HTTP/HTTPS.");
    return;
  }
  const result = await send({ type: "info", url });
  if (!result || !result.ok) {
    showError(result && result.error ? result.error : "No se pudo analizar la URL.");
    return;
  }
  renderQualities(result.data.media);
}

async function onSubmit(event) {
  event.preventDefault();
  hideError();
  const explicit = el.url.value.trim();
  const format = el.format.value;
  const quality = el.quality.value;
  let media;
  if (explicit) {
    const info = await send({ type: "info", url: explicit });
    if (!info || !info.ok) {
      showError(info && info.error ? info.error : "No se pudo analizar la URL.");
      return;
    }
    media = info.data.media;
    renderQualities(media);
  }
  el.download.disabled = true;
  try {
    const result = explicit
      ? await send({
          type: "submit",
          url: explicit,
          format,
          container: el.container.value,
          quality,
          directory: el.directory.value.trim() || undefined,
        })
      : await send({
          type: "capture",
          format,
          container: el.container.value,
          quality,
          directory: el.directory.value.trim() || undefined,
        });
    if (!result || !result.ok) {
      showError(result && result.error ? result.error : "No respondió el backend local.");
      return;
    }

    el.url.value = result.url || "";
    await refresh();
  } finally {
    el.download.disabled = false;
  }
}

async function loadSettings() {
  const settings = await chrome.storage.sync.get(DEFAULT_SETTINGS);
  el.format.value = settings.format;
  el.container.value = settings.container;
  el.quality.value = settings.quality;
}

async function prefill() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab && /^https?:/i.test(tab.url || "")) {
    el.url.value = tab.url;
    await analyzeUrl(tab.url);
  }
}

async function openDashboard() {
  const settings = await chrome.storage.sync.get(DEFAULT_SETTINGS);
  await chrome.tabs.create({ url: settings.apiBase + "/" });
}

el.form.addEventListener("submit", onSubmit);
el.chooseDirectory.addEventListener("click", () => {
  const selected = window.prompt(
    "Escribe la ruta absoluta de la carpeta de descarga:",
    el.directory.value || "",
  );
  if (selected !== null) el.directory.value = selected.trim();
});
el.openOptions.addEventListener("click", () => chrome.runtime.openOptionsPage());
el.openUi.addEventListener("click", openDashboard);
el.format.addEventListener("change", () => {
  updateContainers();
  renderQualities(null);
});

(async () => {
  await loadSettings();
  updateContainers();
  renderQualities(null);
  await prefill();

  const health = await send({ type: "health" });
  const online = Boolean(health && health.ok && health.data && health.data.status === "ok");
  setStatus(online, online ? "backend conectado" : "backend no disponible");

  await refresh();
  setInterval(refresh, 1500);
})();