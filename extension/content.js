// content.js — inyectado en la pestaña activa vía chrome.scripting.
// Devuelve la mejor fuente de video que encuentre, o null.
(() => {
  "use strict";

  const MEDIA_EXT = /\.(mp4|webm|ogg|ogv|m4v|m4a|mov|3gp|flv)(\?|#|$)/i;

  function best() {
    const og = document.querySelector(
      'meta[property="og:video"], meta[property="og:video:url"], meta[property="og:video:secure_url"]',
    );
    if (og && og.content && /^https?:/i.test(og.content)) {
      return og.content;
    }

    const videos = Array.from(document.querySelectorAll("video"));
    for (const video of videos) {
      if (video.currentSrc) return video.currentSrc;
    }
    for (const video of videos) {
      const source = video.querySelector("source[src]");
      if (source && source.src) return source.src;
    }
    for (const link of document.querySelectorAll("a[href]")) {
      if (MEDIA_EXT.test(link.href)) return link.href;
    }
    return null;
  }

  return best();
})();