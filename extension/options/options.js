"use strict";

const DEFAULTS = {
  apiBase: "http://127.0.0.1:8000",
  format: "video",
  quality: "best",
};

const apiBase = document.getElementById("apiBase");
const format = document.getElementById("format");
const quality = document.getElementById("quality");
const saved = document.getElementById("saved");

async function load() {
  const settings = await chrome.storage.sync.get(DEFAULTS);
  apiBase.value = settings.apiBase;
  format.value = settings.format;
  quality.value = settings.quality;
}

async function persist() {
  const value = apiBase.value.trim().replace(/\/+$/, "");
  if (!/^https?:\/\/[^/]+$/.test(value)) {
    window.alert("Introduce una URL válida (por ejemplo, http://127.0.0.1:8000).");
    return;
  }
  await chrome.storage.sync.set({
    apiBase: value,
    format: format.value,
    quality: quality.value,
  });
  saved.hidden = false;
  window.setTimeout(() => {
    saved.hidden = true;
  }, 1500);
}

document.getElementById("form").addEventListener("submit", (event) => {
  event.preventDefault();
  persist();
});

document.getElementById("reset").addEventListener("click", async () => {
  await chrome.storage.sync.set(DEFAULTS);
  await load();
});

load();