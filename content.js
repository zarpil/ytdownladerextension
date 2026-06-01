// ══════════════════════════════════════════════════
//  content.js  –  YT Downloader ✦
//  Inyectado en páginas de YouTube
// ══════════════════════════════════════════════════

// Escucha mensajes del popup/background para devolver
// metadatos de la página actual de YouTube.
chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg.action === 'getPageInfo') {
    sendResponse({
      url:   window.location.href,
      title: document.title
    });
  }
});
