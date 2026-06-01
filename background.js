// ══════════════════════════════════════════════════
//  background.js  –  Service Worker  –  YT Downloader ✦
//  Gestiona Native Messaging y cookies de YouTube
// ══════════════════════════════════════════════════

console.log('[YT Downloader Background] Service Worker iniciado correctamente');
const NATIVE_HOST = 'com.ytdownloader.host';

// ── Cookie helpers ────────────────────────────────

/**
 * Obtiene TODAS las cookies de los dominios de YouTube
 * y las convierte al formato Netscape que yt-dlp entiende.
 */
async function getYouTubeCookies() {
  const domains = [
    'youtube.com', '.youtube.com',
    'www.youtube.com', 'accounts.google.com',
    '.google.com', 'google.com'
  ];

  const seen   = new Set();
  const result = [];

  for (const domain of domains) {
    let cookies = [];
    try {
      cookies = await chrome.cookies.getAll({ domain });
    } catch (_) { continue; }

    for (const c of cookies) {
      const key = `${c.domain}|${c.name}`;
      if (seen.has(key)) continue;
      seen.add(key);

      // Netscape format: domain  includeSubdomains  path  secure  expiry  name  value
      const includeSubdomains = c.domain.startsWith('.') ? 'TRUE' : 'FALSE';
      const secure = c.secure ? 'TRUE' : 'FALSE';
      const expiry = c.expirationDate ? Math.floor(c.expirationDate) : 0;
      result.push(
        `${c.domain}\t${includeSubdomains}\t${c.path}\t${secure}\t${expiry}\t${c.name}\t${c.value}`
      );
    }
  }
  return result;
}

/**
 * Número de cookies de YouTube (para el indicador del popup).
 */
async function getYouTubeCookieCount() {
  const cookies = await chrome.cookies.getAll({ domain: 'youtube.com' });
  return cookies.length;
}

// ── Simple ping/response messages ────────────────
chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  console.log('[YT Downloader Background] Mensaje recibido:', msg);
  if (msg.action === 'ping') {
    console.log('[YT Downloader Background] Iniciando ping a host nativo:', NATIVE_HOST);
    // Try a quick native host ping
    let port;
    try {
      port = chrome.runtime.connectNative(NATIVE_HOST);
      console.log('[YT Downloader Background] Conexión a host creada exitosamente');
    } catch (e) {
      console.error('[YT Downloader Background] Error al conectar al host:', e);
      sendResponse({ ok: false, error: e.message });
      return true;
    }

    const timeout = setTimeout(() => {
      console.error('[YT Downloader Background] Timeout esperando respuesta del host');
      try { port.disconnect(); } catch (_) {}
      sendResponse({ ok: false, error: 'timeout' });
    }, 5000);

    port.onMessage.addListener((resp) => {
      console.log('[YT Downloader Background] Respuesta del host recibida:', resp);
      clearTimeout(timeout);
      try { port.disconnect(); } catch (_) {}
      if (resp.type === 'pong') {
        sendResponse({ ok: true, version: resp.version || '1.0' });
      } else {
        sendResponse({ ok: false, error: 'unexpected response' });
      }
    });

    port.onDisconnect.addListener(() => {
      console.error('[YT Downloader Background] Host desconectado');
      clearTimeout(timeout);
      const err = chrome.runtime.lastError?.message || 'desconectado';
      console.error('[YT Downloader Background] Chrome.runtime.lastError:', chrome.runtime.lastError);
      sendResponse({ ok: false, error: err });
    });

    console.log('[YT Downloader Background] Enviando mensaje ping al host');
    port.postMessage({ action: 'ping' });
    return true; // async response
  }

  if (msg.action === 'getCookieCount') {
    getYouTubeCookieCount()
      .then(count => sendResponse({ count }))
      .catch(e    => sendResponse({ count: 0, error: e.message }));
    return true;
  }
});

// ── Long-lived port for download streaming ────────
chrome.runtime.onConnect.addListener((popupPort) => {
  if (popupPort.name !== 'download') return;

  let nativePort = null;
  let cancelled  = false;

  function send(msg) {
    try { popupPort.postMessage(msg); } catch (_) {}
  }

  popupPort.onMessage.addListener(async (msg) => {
    if (msg.action !== 'download') return;

    // 1. Collect YouTube cookies
    let cookieLines = [];
    if (msg.cookieMode === 'browser') {
      try {
        cookieLines = await getYouTubeCookies();
        send({ type: 'log', level: 'ok',
               msg: `🍪 ${cookieLines.length} cookies de YouTube enviadas al host.` });
      } catch (e) {
        send({ type: 'log', level: 'warn',
               msg: `⚠ No se pudieron leer cookies: ${e.message}` });
      }
    }

    // 2. Open native host port
    try {
      nativePort = chrome.runtime.connectNative(NATIVE_HOST);
    } catch (e) {
      send({ type: 'done', success: false,
             error: `Host nativo no encontrado. Instala native_host/install_host.bat\n${e.message}` });
      return;
    }

    nativePort.onMessage.addListener((resp) => {
      if (cancelled) return;
      switch (resp.type) {
        case 'log':
          send({ type: 'log', level: resp.level || 'info', msg: resp.msg });
          break;
        case 'title':
          send({ type: 'title', title: resp.title });
          break;
        case 'progress':
          send({ type: 'progress', pct: resp.pct, speed: resp.speed, eta: resp.eta });
          break;
        case 'done':
          send({ type: 'done', success: resp.success, error: resp.error || '' });
          try { nativePort.disconnect(); } catch (_) {}
          break;
        default:
          // ignore unknowns
      }
    });

    nativePort.onDisconnect.addListener(() => {
      if (cancelled) return;
      const err = chrome.runtime.lastError?.message || 'Host desconectado';
      send({ type: 'done', success: false, error: err });
    });

    // 3. Send download command with cookies
    nativePort.postMessage({
      action:   'download',
      url:      msg.url,
      format:   msg.format,
      quality:  msg.quality,
      cookies:  cookieLines   // array of Netscape-format lines
    });
  });

  popupPort.onDisconnect.addListener(() => {
    // Popup closed or cancelled — kill host download
    cancelled = true;
    if (nativePort) {
      try {
        nativePort.postMessage({ action: 'cancel' });
        nativePort.disconnect();
      } catch (_) {}
      nativePort = null;
    }
  });
});
