# YT Downloader ✦ — Extensión Chrome

**Descarga videos y audios de YouTube directamente desde el navegador, usando las cookies de tu sesión activa.**

![Captura de pantalla de la extensión](https://i.imgur.com/ahZf560.png)

---

## ✨ Características

- 🚀 Descarga en la mejor calidad disponible
- 🍪 Usa cookies de tu sesión de Chrome (no hace falta exportarlas manualmente)
- 🎞️ Soporte para formatos MP4, MP3 y WEBM
- 📊 Barra de progreso y logs en tiempo real
- 🔒 Funciona de forma local, tus datos nunca salen de tu PC

---

## 📁 Estructura del proyecto

```
extension/
├── manifest.json                   ← Manifest V3 de la extensión
├── popup.html                      ← Interfaz de usuario
├── popup.css                       ← Estilos (tema dark pink)
├── popup.js                        ← Lógica del popup
├── background.js                   ← Service Worker (gestiona cookies y Native Messaging)
├── content.js                      ← Script inyectado en YouTube
├── v2.py                           ← App de escritorio alternativa (Tkinter)
├── icons/
│   ├── icon16.png
│   ├── icon48.png
│   └── icon128.png
└── native_host/
    ├── ytdl_host.py                ← Host nativo (usa yt-dlp)
    ├── run_host.bat                ← Wrapper para el host
    ├── com.ytdownloader.host.json  ← Manifest del host nativo
    ├── install_host.bat            ← Instalador del host (Windows)
    └── install.ps1                 ← Lógica de instalación PowerShell
```

---

## 🛠️ Instalación (Windows)

### 1️⃣ Cargar la extensión en Chrome

1. Abre Chrome y navega a `chrome://extensions`
2. Activa el **"Modo desarrollador"** (arriba a la derecha)
3. Haz clic en **"Cargar descomprimida"**
4. Selecciona la carpeta raíz del proyecto (`extension/`)
5. Copia el **ID de la extensión** que aparece (ej: `abcdefghijklmnopqrstuvwxyzabcdef`)

### 2️⃣ Configurar el host nativo

1. Abre el archivo `native_host/com.ytdownloader.host.json`
2. Asegúrate de que el Extension ID en `allowed_origins` sea el mismo que el de tu extensión
3. Guarda los cambios

### 3️⃣ Instalar el host nativo

1. Haz **doble clic** en `native_host/install_host.bat` (necesitas permisos de usuario)
2. El script se encargará automáticamente de:
   - Detectar Python
   - Instalar dependencias (`yt-dlp`)
   - Registrar el host en el Registro de Windows

### 4️⃣ ¡Listo!

1. Abre la extensión haciendo clic en su ícono en la barra de Chrome
2. El badge del host debe aparecer en **verde** con `✔ host v1.0.0`
3. Si iniciaste sesión en YouTube, el contador de cookies debería ser > 0

---

## 📋 Prerrequisitos

| Requisito | Versión mínima |
|-----------|----------------|
| Python | 3.8+ |
| pip | Incluido con Python |
| Node.js | 16+ (para resolver el "n challenge" de YouTube) |
| FFmpeg | Opcional (solo para extraer audio a MP3) |

### Instalar Node.js
Descarga desde [nodejs.org](https://nodejs.org/) y sigue las instrucciones de instalación.

### Instalar FFmpeg (para MP3)
1. Descarga FFmpeg desde [ffmpeg.org](https://ffmpeg.org/download.html)
2. Descomprime el archivo
3. Añade la carpeta `bin` al **PATH de Windows**

---

## 🎬 Cómo usar la extensión

1. Abre YouTube y busca el video que quieres descargar (o pega el link directamente)
2. Abre la extensión desde la barra de herramientas de Chrome
3. Elige el formato (MP4, MP3 o WEBM)
4. Si quieres, elige una calidad máxima
5. Haz clic en **⬇️ Descargar**
6. El video se descargará automáticamente a tu carpeta de **Descargas**

---

## 🔧 Solución de problemas

| Síntoma | Solución |
|---------|---------|
| `✘ host no instalado` | Asegúrate de haber ejecutado `install_host.bat` y que el Extension ID es correcto |
| `n challenge solving failed` | Asegúrate de tener Node.js instalado |
| `No se encontraron cookies` | Inicia sesión en youtube.com con Chrome |
| `FFmpeg no encontrado` | Instala FFmpeg y añádelo al PATH |
| Descarga lenta | Depende de tu conexión y los servidores de YouTube |
| Error al iniciar el host | Asegúrate de tener Python 3.8+ y las dependencias instaladas |

---

## 💻 Cómo funciona internamente

```
     Popup (HTML/JS)
          │
          ▼ chrome.runtime.sendMessage()
Background Service Worker
          │
          ▼ chrome.runtime.connectNative()
   Native Host (ytdl_host.py)
          │
          ▼ yt-dlp (con Node.js para JS challenges)
       ~/Downloads/video.mp4
```

1. La extensión lee las cookies de tu sesión activa de YouTube
2. Se envía la URL y las cookies al host nativo
3. El host usa `yt-dlp` (con Node.js para resolver el "n challenge") para descargar el video
4. ¡El video se guarda en tu carpeta de Descargas!

---

## 📝 Notas importantes

- Este proyecto es solo para fines educativos y personales
- Asegúrate de respetar los derechos de autor de los videos que descargues
- La extensión funciona mejor si tienes iniciada sesión en YouTube

---

## 🙌 Créditos

- `yt-dlp`: Proyecto open-source para descargar videos de YouTube
- Íconos y diseño inspirados en la comunidad

---

Made with ❤️