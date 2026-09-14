"use strict";

const DEFAULT_SETTINGS = {
  apiBase: "http://127.0.0.1:8000",
  format: "video",
  quality: "best",
};

function getSettings() {
  return chrome.storage.sync.get(DEFAULT_SETTINGS);
}

async function apiRequest(method, path, body, apiBase) {
  const base = (apiBase || (await getSettings()).apiBase).replace(/\/+$/, "");
  const options = { method, headers: { "Content-Type": "application/json" } };
  if (body !== undefined) options.body = JSON.stringify(body);
  const response = await fetch(base + path, options);
  if (response.status === 204) return null;
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "HTTP " + response.status);
  }
  return data;
}

function isHttp(url) {
  return /^https?:/i.test(url || "");
}

async function detectInTab(tabId) {
  const [injected] = await chrome.scripting.executeScript({
    target: { tabId },
    files: ["content.js"],
  });
  return injected && injected.result && isHttp(injected.result)
    ? injected.result
    : null;
}

async function resolveTargetUrl(tab) {
  if (!tab || !tab.id) return null;
  try {
    const detected = await detectInTab(tab.id);
    if (detected) return detected;
  } catch (error) {
    console.warn("content.js injection failed:", error);
  }
  return isHttp(tab.url) ? tab.url : null;
}

function submitDownload(payload, apiBase) {
  return apiRequest("POST", "/api/downloads", payload, apiBase);
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (!message || !message.type) return false;

  (async () => {
    const settings = await getSettings();
    try {
      switch (message.type) {
        case "health": {
          const data = await apiRequest("GET", "/api/health", undefined, settings.apiBase);
          sendResponse({ ok: true, data });
          break;
        }
        case "list": {
          const data = await apiRequest("GET", "/api/downloads", undefined, settings.apiBase);
          sendResponse({ ok: true, data });
          break;
        }
        case "submit": {
          const format = message.format || settings.format;
          const record = await submitDownload(
            {
              url: message.url,
              format,
              quality: message.quality || (format === "audio" ? "best" : settings.quality),
            },
            settings.apiBase,
          );
          sendResponse({ ok: true, record });
          break;
        }
        case "capture": {
          const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
          const url = await resolveTargetUrl(tab);
          if (!url) {
            sendResponse({ ok: false, error: "No se encontró ningún vídeo en esta página." });
            break;
          }
          const format = message.format || settings.format;
          const record = await submitDownload(
            {
              url,
              format,
              quality: message.quality || (format === "audio" ? "best" : settings.quality),
            },
            settings.apiBase,
          );
          sendResponse({ ok: true, record, url });
          break;
        }
        case "cancel": {
          const data = await apiRequest(
            "POST",
            "/api/downloads/" + encodeURIComponent(message.id) + "/cancel",
            undefined,
            settings.apiBase,
          );
          sendResponse({ ok: true, data });
          break;
        }
        case "delete": {
          const data = await apiRequest(
            "DELETE",
            "/api/downloads/" + encodeURIComponent(message.id),
            undefined,
            settings.apiBase,
          );
          sendResponse({ ok: true, data });
          break;
        }
        default:
          sendResponse({ ok: false, error: "Tipo de mensaje desconocido." });
      }
    } catch (error) {
      sendResponse({ ok: false, error: error.message });
    }
  })();
  return true;
});