// ══════════════════════════════════════════════════
//  popup.js  –  YT Downloader ✦
// ══════════════════════════════════════════════════

// ── DOM refs ──────────────────────────────────────
const urlInput       = document.getElementById('urlInput');
const clearUrlBtn    = document.getElementById('clearUrl');
const pasteUrlBtn    = document.getElementById('pasteUrl');
const downloadBtn    = document.getElementById('downloadBtn');
const downloadBtnIcon= document.getElementById('downloadBtnIcon');
const downloadBtnText= document.getElementById('downloadBtnText');
const progressWrap   = document.getElementById('progressWrap');
const progressBar    = document.getElementById('progressBar');
const progressGlow   = document.getElementById('progressGlow');
const progressStats  = document.getElementById('progressStats');
const statusText     = document.getElementById('statusText');
const logBox         = document.getElementById('logBox');
const logFrame       = document.getElementById('logFrame');
const clearLogBtn    = document.getElementById('clearLog');
const hostStatus     = document.getElementById('hostStatus');
const cookieStatus   = document.getElementById('cookieStatus');
const cookieStatusText = document.getElementById('cookieStatusText');
const helpModal      = document.getElementById('helpModal');
const helpCookiesBtn = document.getElementById('helpCookies');
const helpCloseBtn   = document.getElementById('helpClose');

let isBusy = false;
let downloadPort = null;

// ── Logging ────────────────────────────────────────
function log(msg, level = 'info') {
  const span = document.createElement('span');
  span.className = `log-${level}`;
  span.textContent = msg + '\n';
  logBox.appendChild(span);
  logFrame.scrollTop = logFrame.scrollHeight;
}

function clearLog() {
  logBox.innerHTML = '';
}

// ── Status helpers ────────────────────────────────
function setStatus(msg) {
  statusText.textContent = msg;
}

function setProgress(pct, statsMsg) {
  progressBar.style.width  = `${pct}%`;
  progressGlow.style.width = `${pct}%`;
  if (statsMsg) progressStats.textContent = statsMsg;
}

function setBusy(busy) {
  isBusy = busy;
  downloadBtn.disabled = busy;
  if (busy) {
    downloadBtnIcon.textContent = '⏳';
    downloadBtnText.textContent = 'Descargando…';
    progressWrap.style.display = 'block';
  } else {
    downloadBtnIcon.textContent = '⬇';
    downloadBtnText.textContent = 'Descargar';
  }
}

// ── Cookie status indicator ───────────────────────
function setCookieStatus(state, msg) {
  cookieStatus.className = `cookie-status ${state}`;
  cookieStatusText.textContent = msg;
}

// ── Host status badge ─────────────────────────────
function setHostBadge(state, msg) {
  hostStatus.className = `host-badge ${state}`;
  hostStatus.textContent = msg;
}

// ── Check native host ─────────────────────────────
async function checkHost() {
  try {
    const resp = await chrome.runtime.sendMessage({ action: 'ping' });
    if (resp && resp.ok) {
      setHostBadge('ok', `✔ host v${resp.version || '1.0'}`);
      log('✔ Host nativo conectado correctamente.', 'ok');
    } else {
      throw new Error(resp?.error || 'Sin respuesta');
    }
  } catch (e) {
    setHostBadge('err', '✘ host no instalado');
    log('✘ Host nativo no encontrado. Ejecuta install_host.bat', 'err');
    log('  → carpeta: extensión/native_host/install_host.bat', 'info');
  }
}

// ── Check YouTube cookies ─────────────────────────
async function checkCookies() {
  setCookieStatus('loading', 'Verificando cookies de YouTube…');
  try {
    const resp = await chrome.runtime.sendMessage({ action: 'getCookieCount' });
    if (resp && resp.count > 0) {
      setCookieStatus('ok', `✔ ${resp.count} cookies de YouTube encontradas (sesión activa)`);
    } else {
      setCookieStatus('warn', '⚠ No se encontraron cookies — inicia sesión en YouTube');
    }
  } catch (e) {
    setCookieStatus('err', '✘ Error leyendo cookies: ' + e.message);
  }
}

// ── Get current tab URL ───────────────────────────
async function getCurrentYouTubeUrl() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab && tab.url && /youtube\.com|youtu\.be/.test(tab.url)) {
      return tab.url;
    }
  } catch (_) {}
  return null;
}

// ── Validate YouTube URL ──────────────────────────
function isValidYtUrl(url) {
  return /^https?:\/\/(www\.)?(youtube\.com\/watch|youtu\.be\/|youtube\.com\/shorts\/)/.test(url.trim());
}

// ── Download handler ──────────────────────────────
async function startDownload() {
  if (isBusy) return;

  const url = urlInput.value.trim();
  if (!url) {
    setStatus('⚠ Pega una URL de YouTube primero.');
    urlInput.focus();
    return;
  }
  if (!isValidYtUrl(url)) {
    setStatus('✘ No parece un link de YouTube válido.');
    return;
  }

  const format  = document.querySelector('input[name="format"]:checked')?.value || 'mp4';
  const quality = document.getElementById('qualitySelect').value;
  const cookieMode = document.querySelector('input[name="cookieMode"]:checked')?.value || 'browser';

  clearLog();
  setBusy(true);
  setProgress(0, 'Iniciando…');
  setStatus('Iniciando descarga…');
  log(`▶ URL: ${url}`, 'info');
  log(`🎞 Formato: ${format.toUpperCase()}  |  Calidad: ${quality}`, 'info');
  log(cookieMode === 'browser'
    ? '🍪 Usando cookies del navegador (automático)'
    : '🚫 Sin cookies', 'info');

  try {
    // Open a long-lived port with the background for streaming progress
    downloadPort = chrome.runtime.connect({ name: 'download' });

    downloadPort.onMessage.addListener((msg) => {
      switch (msg.type) {
        case 'log':
          log(msg.msg, msg.level || 'info');
          break;
        case 'progress':
          setProgress(msg.pct, `⬇ ${msg.pct.toFixed(1)}%  •  ${msg.speed}  •  ETA ${msg.eta}`);
          setStatus(`⬇ Descargando… ${msg.pct.toFixed(1)}%`);
          break;
        case 'done':
          if (msg.success) {
            setProgress(100, '✔ Completado');
            setStatus(`✔ ¡Descarga completada! Guardado en Descargas.`);
            log('✔ ¡Descarga completada con éxito!', 'ok');
          } else {
            setProgress(0, '');
            setStatus(`✘ ${msg.error}`);
            log(`✘ ${msg.error}`, 'err');
          }
          setBusy(false);
          downloadPort.disconnect();
          downloadPort = null;
          // Refresh cookie status after download
          checkCookies();
          break;
        case 'title':
          setStatus(`⬇ Descargando: ${msg.title.substring(0, 50)}…`);
          log(`✔ Título: ${msg.title}`, 'ok');
          break;
      }
    });

    downloadPort.onDisconnect.addListener(() => {
      if (isBusy) {
        setBusy(false);
        setStatus('✘ Conexión con el host interrumpida.');
        log('✘ El host nativo se desconectó inesperadamente.', 'err');
      }
      downloadPort = null;
    });

    // Send download command
    downloadPort.postMessage({
      action: 'download',
      url,
      format,
      quality,
      cookieMode
    });

  } catch (e) {
    setBusy(false);
    setStatus(`✘ Error: ${e.message}`);
    log(`✘ ${e.message}`, 'err');
  }
}

// ── Event Listeners ───────────────────────────────
clearUrlBtn.addEventListener('click', () => {
  urlInput.value = '';
  urlInput.focus();
});

pasteUrlBtn.addEventListener('click', async () => {
  const ytUrl = await getCurrentYouTubeUrl();
  if (ytUrl) {
    urlInput.value = ytUrl;
    log(`📋 URL capturada: ${ytUrl}`, 'info');
  } else {
    try {
      const text = await navigator.clipboard.readText();
      if (text && isValidYtUrl(text)) {
        urlInput.value = text.trim();
        log(`📋 URL del portapapeles: ${text.trim()}`, 'info');
      } else {
        setStatus('⚠ La pestaña activa no es YouTube. Pega la URL manualmente.');
      }
    } catch (_) {
      setStatus('⚠ Ve a YouTube y pulsa este botón para capturar la URL.');
    }
  }
});

downloadBtn.addEventListener('click', startDownload);

urlInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') startDownload();
});

clearLogBtn.addEventListener('click', clearLog);

helpCookiesBtn.addEventListener('click', () => {
  helpModal.style.display = 'flex';
});

helpCloseBtn.addEventListener('click', () => {
  helpModal.style.display = 'none';
});

helpModal.addEventListener('click', (e) => {
  if (e.target === helpModal) helpModal.style.display = 'none';
});

// Format radio — hide quality when MP3 selected
document.querySelectorAll('input[name="format"]').forEach(r => {
  r.addEventListener('change', () => {
    const qualRow = document.getElementById('qualitySelect').closest('.select-row');
    const label   = qualRow.previousElementSibling;
    const isAudio = r.value === 'mp3';
    qualRow.style.opacity = isAudio ? '0.35' : '1';
    label.style.opacity   = isAudio ? '0.35' : '1';
    document.getElementById('qualitySelect').disabled = isAudio;
  });
});

// ── Init ──────────────────────────────────────────
(async () => {
  // Try to auto-fill URL from active tab
  const ytUrl = await getCurrentYouTubeUrl();
  if (ytUrl) {
    urlInput.value = ytUrl;
  }

  // Check host and cookies in parallel
  await Promise.all([checkHost(), checkCookies()]);

  log('✦ YT Downloader listo. Pega una URL y descarga.', 'info');
})();
