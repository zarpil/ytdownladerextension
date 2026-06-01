import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import subprocess
import sys
import os
import re
import platform
import webbrowser
import io
import traceback


def ensure_ytdlp():
    try:
        import yt_dlp
        return True
    except ImportError:
        return False


# ════════════════════════════════════════════════════════════════════════════
BG       = "#1a0a10"
SURFACE  = "#2b1020"
SURFACE2 = "#341525"
ACCENT1  = "#ff5fa0"
ACCENT2  = "#ff8ec4"
MUTED    = "#7a3555"
TEXT     = "#ffe6f2"
SUBTEXT  = "#c084a0"
BAR_BG   = "#3d1428"
BAR_FG   = "#ff5fa0"
INFO_BG  = "#2a0e1e"
LOG_BG   = "#110208"
LOG_OK   = "#ff79b0"
LOG_ERR  = "#ff3d78"
LOG_INFO = "#c084a0"

BROWSERS    = ["chrome", "firefox", "edge", "opera", "brave", "safari", "chromium", "vivaldi"]
_os         = platform.system()
DEF_BROWSER = "firefox" if _os == "Linux" else ("safari" if _os == "Darwin" else "chrome")


# ════════════════════════════════════════════════════════════════════════════
class HelpWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("¿Cómo exportar las cookies? 🍪")
        self.geometry("560x460")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.grab_set()

        tk.Label(self, text="Exportar cookies de YouTube",
                 font=("Georgia", 16, "bold"), fg=ACCENT1, bg=BG).pack(pady=(20, 4))
        tk.Label(self,
                 text="Chrome/Edge en Windows cifran las cookies y yt-dlp no puede leerlas.\n"
                      "Usa una extensión del navegador para exportarlas como archivo .txt:",
                 font=("Georgia", 9), fg=SUBTEXT, bg=BG, justify="center", wraplength=500
                 ).pack(pady=(0, 12))

        steps = [
            ("1", "Instala la extensión",
             "\"Get cookies.txt LOCALLY\" en Chrome/Edge  •  \"cookies.txt\" en Firefox"),
            ("2", "Abre YouTube con sesión iniciada",
             "Ve a youtube.com y asegúrate de estar logueado en tu cuenta."),
            ("3", "Exporta desde la extensión",
             "Icono de la extensión → Export / Download cookies → guarda el .txt"),
            ("4", "Carga el archivo en el downloader",
             "Elige modo \"Archivo .txt\", pulsa \"Elegir .txt…\" y selecciónalo."),
        ]
        for num, title, desc in steps:
            row = tk.Frame(self, bg=SURFACE2)
            row.pack(fill="x", padx=28, pady=4)
            row.configure(highlightbackground=MUTED, highlightthickness=1)
            tk.Label(row, text=num, font=("Georgia", 18, "bold"),
                     fg=ACCENT1, bg=SURFACE2, width=3).pack(side="left", padx=(10, 0), pady=8)
            col = tk.Frame(row, bg=SURFACE2)
            col.pack(side="left", padx=10, pady=7, fill="x", expand=True)
            tk.Label(col, text=title, font=("Georgia", 10, "bold"),
                     fg=ACCENT2, bg=SURFACE2, anchor="w").pack(anchor="w")
            tk.Label(col, text=desc, font=("Georgia", 8), fg=TEXT,
                     bg=SURFACE2, anchor="w", justify="left", wraplength=420).pack(anchor="w")

        btn_row = tk.Frame(self, bg=BG)
        btn_row.pack(pady=16)
        tk.Button(btn_row, text="🔗 Chrome/Edge extension",
                  command=lambda: webbrowser.open(
                      "https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc"),
                  font=("Georgia", 9), fg=BG, bg=ACCENT1,
                  activeforeground=BG, activebackground=ACCENT2,
                  relief="flat", bd=0, padx=14, pady=7, cursor="hand2").pack(side="left", padx=8)
        tk.Button(btn_row, text="🔗 Firefox addon",
                  command=lambda: webbrowser.open(
                      "https://addons.mozilla.org/firefox/addon/cookies-txt/"),
                  font=("Georgia", 9), fg=TEXT, bg=MUTED,
                  activeforeground=BG, activebackground=ACCENT2,
                  relief="flat", bd=0, padx=14, pady=7, cursor="hand2").pack(side="left", padx=8)
        tk.Button(btn_row, text="Cerrar", command=self.destroy,
                  font=("Georgia", 9), fg=SUBTEXT, bg=SURFACE2,
                  activeforeground=TEXT, activebackground=MUTED,
                  relief="flat", bd=0, padx=14, pady=7, cursor="hand2").pack(side="left", padx=8)


# ════════════════════════════════════════════════════════════════════════════
class YTDownloader(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("YT Downloader ✦")
        self.geometry("720x780")
        self.resizable(False, False)
        self.configure(bg=BG)

        self.save_path      = tk.StringVar(value=os.path.expanduser("~/Downloads"))
        self.url_var        = tk.StringVar()
        self.status         = tk.StringVar(value="Pega un link de YouTube y pulsa Descargar ✦")
        self.progress       = tk.DoubleVar(value=0.0)
        self.is_busy        = False
        self.cookie_mode    = tk.StringVar(value="file")
        self.cookie_browser = tk.StringVar(value=DEF_BROWSER)
        self.cookie_file    = tk.StringVar(value="")

        self._build_ui()
        self._update_cookie_ui()
        self._check_dep()

    # ── dep check ────────────────────────────────────────────────────────────
    def _check_dep(self):
        # 1) yt-dlp
        if not ensure_ytdlp():
            self.log("⚙ Instalando yt-dlp…", "info")
            self.update()
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "yt-dlp", "--quiet"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.log("✔ yt-dlp instalado.", "ok")
            except Exception as e:
                self.log(f"✘ No se pudo instalar yt-dlp: {e}", "err")
                return

        # 2) curl_cffi — resuelve el "n challenge" de YouTube sin Node.js
        try:
            import curl_cffi  # noqa
            self.log("✔ curl_cffi OK (n-challenge resuelto).", "ok")
        except ImportError:
            self.log("⚙ Instalando curl_cffi (necesario para YouTube)…", "info")
            self.status.set("⚙  Instalando dependencias…")
            self.update()
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "curl_cffi", "--quiet"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.log("✔ curl_cffi instalado. ¡Listo!", "ok")
                self.status.set("✔  Listo para descargar ✦")
            except Exception as e:
                self.log(f"⚠ curl_cffi no instalado: {e}", "info")
                self.log("  Ejecuta manualmente: pip install curl_cffi", "info")

    # ── logging helper ───────────────────────────────────────────────────────
    def log(self, msg, kind="info"):
        """Append a line to the log console (thread-safe via after)."""
        color = {"ok": LOG_OK, "err": LOG_ERR, "info": LOG_INFO}.get(kind, LOG_INFO)
        def _insert():
            self.log_box.config(state="normal")
            self.log_box.insert("end", msg.rstrip() + "\n", kind)
            self.log_box.see("end")
            self.log_box.config(state="disabled")
        self.after(0, _insert)

    # ── UI ───────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # HEADER
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", pady=(20, 0))
        tk.Label(hdr, text="✦  YT Downloader  ✦",
                 font=("Georgia", 24, "bold"), fg=ACCENT1, bg=BG).pack()
        tk.Label(hdr, text="Descarga videos en la mejor calidad disponible",
                 font=("Georgia", 10, "italic"), fg=SUBTEXT, bg=BG).pack(pady=(2, 0))

        tk.Frame(self, bg=MUTED, height=1).pack(fill="x", padx=40, pady=10)

        # CARD
        card = tk.Frame(self, bg=SURFACE, bd=0)
        card.pack(fill="x", padx=40, ipady=12)
        card.configure(highlightbackground=MUTED, highlightthickness=1)

        # URL
        tk.Label(card, text="🔗  URL de YouTube", font=("Georgia", 10, "bold"),
                 fg=ACCENT2, bg=SURFACE).pack(anchor="w", padx=24, pady=(14, 4))
        uf = tk.Frame(card, bg=SURFACE)
        uf.pack(fill="x", padx=24)
        self.url_entry = tk.Entry(uf, textvariable=self.url_var,
                                   font=("Consolas", 11), fg=TEXT, bg=BAR_BG,
                                   insertbackground=ACCENT1, relief="flat", bd=0,
                                   highlightthickness=1, highlightbackground=MUTED,
                                   highlightcolor=ACCENT1)
        self.url_entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 8))
        tk.Button(uf, text="✕", command=self._clear_url,
                  font=("Arial", 10), fg=SUBTEXT, bg=BAR_BG,
                  activeforeground=ACCENT1, activebackground=BAR_BG,
                  relief="flat", bd=0, padx=10, cursor="hand2").pack(side="left", ipady=8)

        # CARPETA
        tk.Label(card, text="📁  Carpeta de destino", font=("Georgia", 10, "bold"),
                 fg=ACCENT2, bg=SURFACE).pack(anchor="w", padx=24, pady=(12, 4))
        ff = tk.Frame(card, bg=SURFACE)
        ff.pack(fill="x", padx=24)
        tk.Entry(ff, textvariable=self.save_path,
                 font=("Consolas", 10), fg=SUBTEXT, bg=BAR_BG,
                 insertbackground=ACCENT1, relief="flat", bd=0,
                 highlightthickness=1, highlightbackground=MUTED, highlightcolor=ACCENT1,
                 state="readonly").pack(side="left", fill="x", expand=True, ipady=7, padx=(0, 8))
        tk.Button(ff, text="Explorar…", command=self._choose_folder,
                  font=("Georgia", 9), fg=TEXT, bg=MUTED,
                  activeforeground=BG, activebackground=ACCENT1,
                  relief="flat", bd=0, padx=14, cursor="hand2").pack(side="left", ipady=3)

        # COOKIES
        tk.Frame(card, bg=MUTED, height=1).pack(fill="x", padx=24, pady=(12, 0))
        chdr = tk.Frame(card, bg=SURFACE)
        chdr.pack(fill="x", padx=24, pady=(8, 6))
        tk.Label(chdr, text="🍪  Cookies (anti-bot)",
                 font=("Georgia", 10, "bold"), fg=ACCENT2, bg=SURFACE).pack(side="left")
        tk.Button(chdr, text=" ? ", command=lambda: HelpWindow(self),
                  font=("Georgia", 8, "bold"), fg=BG, bg=ACCENT1,
                  activeforeground=BG, activebackground=ACCENT2,
                  relief="flat", bd=0, padx=6, pady=1, cursor="hand2").pack(side="left", padx=8)

        rr = tk.Frame(card, bg=SURFACE)
        rr.pack(fill="x", padx=24)
        for val, lbl in [("file",    "📄 Archivo .txt  ← recomendado en Windows"),
                          ("browser", "🌐 Desde navegador"),
                          ("none",    "🚫 Sin cookies")]:
            tk.Radiobutton(rr, text=lbl, variable=self.cookie_mode, value=val,
                           command=self._update_cookie_ui,
                           font=("Georgia", 9), fg=TEXT, bg=SURFACE,
                           selectcolor=BAR_BG, activebackground=SURFACE,
                           activeforeground=ACCENT1).pack(side="left", padx=(0, 14))

        # sub-panel: archivo
        self.file_frame = tk.Frame(card, bg=SURFACE)
        tk.Entry(self.file_frame, textvariable=self.cookie_file,
                 font=("Consolas", 9), fg=SUBTEXT, bg=BAR_BG,
                 insertbackground=ACCENT1, relief="flat", bd=0,
                 highlightthickness=1, highlightbackground=MUTED, highlightcolor=ACCENT1,
                 state="readonly").pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 8))
        tk.Button(self.file_frame, text="Elegir .txt…", command=self._choose_cookie_file,
                  font=("Georgia", 9), fg=TEXT, bg=MUTED,
                  activeforeground=BG, activebackground=ACCENT1,
                  relief="flat", bd=0, padx=12, cursor="hand2").pack(side="left", ipady=2)
        tk.Button(self.file_frame, text="¿Cómo exportarlas?",
                  command=lambda: HelpWindow(self),
                  font=("Georgia", 8, "italic"), fg=ACCENT1, bg=SURFACE,
                  activeforeground=ACCENT2, activebackground=SURFACE,
                  relief="flat", bd=0, padx=8, cursor="hand2").pack(side="left", padx=(6, 0))

        # sub-panel: navegador
        self.browser_frame = tk.Frame(card, bg=SURFACE)
        tk.Label(self.browser_frame, text="Navegador:", font=("Georgia", 9),
                 fg=SUBTEXT, bg=SURFACE).pack(side="left", padx=(0, 8))
        bm = tk.OptionMenu(self.browser_frame, self.cookie_browser, *BROWSERS)
        bm.config(font=("Georgia", 9), fg=TEXT, bg=BAR_BG,
                  activeforeground=ACCENT1, activebackground=BAR_BG,
                  highlightthickness=0, relief="flat", bd=0)
        bm["menu"].config(bg=BAR_BG, fg=TEXT, activebackground=MUTED)
        bm.pack(side="left")
        tk.Label(self.browser_frame,
                 text="  (puede fallar en Windows — usa Archivo .txt si da error)",
                 font=("Georgia", 8, "italic"), fg=MUTED, bg=SURFACE).pack(side="left")

        # info box Windows
        self.info_box = tk.Frame(card, bg=INFO_BG)
        self.info_box.configure(highlightbackground=MUTED, highlightthickness=1)
        tk.Label(self.info_box,
                 text="ℹ  Chrome/Edge en Windows bloquean acceso a su BD de cookies (DPAPI).\n"
                      "   Cierra el navegador completamente, o usa el modo Archivo .txt.",
                 font=("Georgia", 8), fg=ACCENT2, bg=INFO_BG,
                 justify="left", wraplength=600).pack(padx=12, pady=7, anchor="w")

        tk.Frame(card, bg=MUTED, height=1).pack(fill="x", padx=24, pady=(10, 0))

        # FORMATO
        fmt_row = tk.Frame(card, bg=SURFACE)
        fmt_row.pack(fill="x", padx=24, pady=(10, 0))
        tk.Label(fmt_row, text="🎞  Formato:", font=("Georgia", 10, "bold"),
                 fg=ACCENT2, bg=SURFACE).pack(side="left", padx=(0, 10))
        self.fmt_var = tk.StringVar(value="mp4")
        for val, lbl in [("mp4", "MP4 (video)"), ("mp3", "MP3 (audio)"), ("webm", "WebM")]:
            tk.Radiobutton(fmt_row, text=lbl, variable=self.fmt_var, value=val,
                           font=("Georgia", 9), fg=TEXT, bg=SURFACE,
                           selectcolor=BAR_BG, activebackground=SURFACE,
                           activeforeground=ACCENT1).pack(side="left", padx=6)

        # BOTÓN
        self.dl_btn = tk.Button(card, text="⬇  Descargar",
                                 command=self._start_download,
                                 font=("Georgia", 13, "bold"), fg=BG, bg=ACCENT1,
                                 activeforeground=BG, activebackground=ACCENT2,
                                 relief="flat", bd=0, padx=30, pady=9, cursor="hand2")
        self.dl_btn.pack(pady=(14, 5))

        # PROGRESS
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Pink.Horizontal.TProgressbar",
                         troughcolor=BAR_BG, background=BAR_FG,
                         lightcolor=ACCENT2, darkcolor=ACCENT1, bordercolor=BAR_BG)
        ttk.Progressbar(card, variable=self.progress, maximum=100,
                         style="Pink.Horizontal.TProgressbar",
                         length=630).pack(padx=24, pady=(2, 0))

        tk.Label(card, textvariable=self.status,
                 font=("Georgia", 9, "italic"), fg=SUBTEXT, bg=SURFACE,
                 wraplength=630, justify="center").pack(pady=(5, 10))

        # ── LOG CONSOLE ──────────────────────────────────────────────────────
        tk.Frame(self, bg=MUTED, height=1).pack(fill="x", padx=40, pady=(10, 0))

        log_hdr = tk.Frame(self, bg=BG)
        log_hdr.pack(fill="x", padx=40, pady=(6, 2))
        tk.Label(log_hdr, text="📋  Consola de logs",
                 font=("Georgia", 9, "bold"), fg=MUTED, bg=BG).pack(side="left")
        tk.Button(log_hdr, text="Limpiar", command=self._clear_log,
                  font=("Georgia", 8), fg=MUTED, bg=BG,
                  activeforeground=TEXT, activebackground=BG,
                  relief="flat", bd=0, cursor="hand2").pack(side="right")

        log_frame = tk.Frame(self, bg=LOG_BG)
        log_frame.pack(fill="both", padx=40, pady=(0, 0), expand=True)
        log_frame.configure(highlightbackground=MUTED, highlightthickness=1)

        self.log_box = tk.Text(log_frame, height=9,
                                font=("Consolas", 8), bg=LOG_BG, fg=LOG_INFO,
                                insertbackground=ACCENT1, relief="flat", bd=0,
                                state="disabled", wrap="word")
        self.log_box.tag_config("ok",   foreground=LOG_OK)
        self.log_box.tag_config("err",  foreground=LOG_ERR)
        self.log_box.tag_config("info", foreground=LOG_INFO)

        sb = tk.Scrollbar(log_frame, command=self.log_box.yview,
                          bg=BAR_BG, troughcolor=LOG_BG,
                          activebackground=MUTED, relief="flat", bd=0)
        self.log_box.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.log_box.pack(side="left", fill="both", expand=True, padx=6, pady=6)

        # FOOTER
        tk.Frame(self, bg=MUTED, height=1).pack(fill="x", padx=40, pady=(8, 0))
        tk.Label(self, text="made by @p0u",
                 font=("Georgia", 8, "italic"), fg=MUTED, bg=BG).pack(pady=(5, 8))

    # ── cookie UI ────────────────────────────────────────────────────────────
    def _update_cookie_ui(self):
        mode = self.cookie_mode.get()
        self.file_frame.pack_forget()
        self.browser_frame.pack_forget()
        self.info_box.pack_forget()
        if mode == "file":
            self.file_frame.pack(fill="x", padx=24, pady=(6, 0))
        elif mode == "browser":
            self.browser_frame.pack(fill="x", padx=24, pady=(6, 0))
            if _os == "Windows":
                self.info_box.pack(fill="x", padx=24, pady=(6, 0))

    def _choose_cookie_file(self):
        path = filedialog.askopenfilename(
            title="Selecciona el archivo de cookies",
            filetypes=[("Netscape cookies", "*.txt"), ("Todos", "*.*")])
        if path:
            self.cookie_file.set(path)
            self.log(f"🍪 Cookies cargadas: {path}", "ok")

    def _clear_url(self):
        self.url_var.set("")
        self.url_entry.focus_set()

    def _clear_log(self):
        self.log_box.config(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.config(state="disabled")

    def _choose_folder(self):
        path = filedialog.askdirectory(initialdir=self.save_path.get())
        if path:
            self.save_path.set(path)

    # ── download ─────────────────────────────────────────────────────────────
    def _start_download(self):
        if self.is_busy:
            return
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("URL vacía", "Por favor pega un enlace de YouTube.")
            return
        if not re.search(r"(youtube\.com|youtu\.be)", url):
            messagebox.showwarning("URL inválida", "No parece un link de YouTube válido.")
            return
        if self.cookie_mode.get() == "file" and not self.cookie_file.get():
            messagebox.showwarning("Cookies",
                                   "Selecciona un archivo .txt o pulsa '¿Cómo exportarlas?'.")
            return

        self._clear_log()
        self.log(f"▶ URL: {url}", "info")
        mode = self.cookie_mode.get()
        if mode == "file":
            self.log(f"🍪 Usando cookies: {self.cookie_file.get()}", "info")
        elif mode == "browser":
            self.log(f"🌐 Usando cookies de navegador: {self.cookie_browser.get()}", "info")
        else:
            self.log("🚫 Sin cookies (puede fallar en videos restringidos)", "info")

        self.is_busy = True
        self.dl_btn.config(state="disabled", text="⏳  Descargando…")
        self.progress.set(0)
        self.status.set("Iniciando descarga…")
        threading.Thread(target=self._download_worker, args=(url,), daemon=True).start()

    # ── yt-dlp logger que redirige a nuestro log widget ──────────────────────
    def _make_logger(self):
        app = self
        class YTLogger:
            def debug(self, msg):
                if msg.startswith("[debug]"):
                    return  # demasiado verboso, ocultar debug interno
                clean = re.sub(r"\x1b\[[0-9;]*m", "", msg).strip()
                if clean:
                    app.log(clean, "info")
            def info(self, msg):
                clean = re.sub(r"\x1b\[[0-9;]*m", "", msg).strip()
                if clean:
                    app.log(clean, "info")
            def warning(self, msg):
                clean = re.sub(r"\x1b\[[0-9;]*m", "", msg).strip()
                if clean:
                    app.log(f"⚠ {clean}", "info")
            def error(self, msg):
                clean = re.sub(r"\x1b\[[0-9;]*m", "", msg).strip()
                if clean:
                    app.log(f"✘ {clean}", "err")
        return YTLogger()

    def _auth_opts(self):
        opts = {
            "quiet": False,
            "no_warnings": False,
            "logger": self._make_logger(),
            # curl_cffi impersonation — solves YouTube's n-challenge without Node.js
            "impersonate": "chrome",
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"),
            },
        }
        mode = self.cookie_mode.get()
        if mode == "browser":
            opts["cookiesfrombrowser"] = (self.cookie_browser.get(),)
        elif mode == "file" and self.cookie_file.get():
            opts["cookiefile"] = self.cookie_file.get()
        return opts

    def _download_worker(self, url):
        try:
            import yt_dlp
        except ImportError:
            self.log("✘ yt-dlp no encontrado. Ejecuta: pip install yt-dlp", "err")
            self._done(False, "yt-dlp no instalado.")
            return

        fmt     = self.fmt_var.get()
        out_dir = self.save_path.get()

        try:
            # ── Step 1: get real format list ─────────────────────────────────
            self.log("🔍 Obteniendo información del vídeo…", "info")
            self.status.set("🔍  Obteniendo información…")

            with yt_dlp.YoutubeDL({**self._auth_opts(), "skip_download": True}) as ydl:
                info = ydl.extract_info(url, download=False)

            title   = info.get("title", "video")
            formats = info.get("formats", [])
            self.log(f"✔ Título: {title}", "ok")
            self.log(f"   Formatos disponibles ({len(formats)}):", "info")
            for f in formats[-6:]:  # show last 6 (usually best quality ones)
                fid  = f.get("format_id", "?")
                ext  = f.get("ext", "?")
                h    = f.get("height") or "—"
                abr  = f.get("abr")
                vcodec = f.get("vcodec", "none")
                acodec = f.get("acodec", "none")
                if vcodec not in (None, "none", ""):
                    self.log(f"   [{fid}] {ext} {h}p  vcodec={vcodec}", "info")
                else:
                    self.log(f"   [{fid}] {ext} audio {abr}kbps  acodec={acodec}", "info")

            # ── Step 2: pick best format from real list ───────────────────────
            format_str = self._pick_format(formats, fmt)
            self.log(f"✔ Formato elegido: {format_str}", "ok")
            self.status.set(f"⬇  Descargando: {title[:55]}…")

            # ── Step 3: download ──────────────────────────────────────────────
            dl_opts = {
                **self._auth_opts(),
                "format": format_str,
                "outtmpl": os.path.join(out_dir, "%(title)s.%(ext)s"),
                "progress_hooks": [self._progress_hook],
            }
            if fmt == "mp4":
                dl_opts["merge_output_format"] = "mp4"
            elif fmt == "mp3":
                dl_opts["postprocessors"] = [{"key": "FFmpegExtractAudio",
                                               "preferredcodec": "mp3",
                                               "preferredquality": "320"}]

            with yt_dlp.YoutubeDL(dl_opts) as ydl:
                ydl.download([url])

            self._done(True, "")

        except Exception as e:
            full = traceback.format_exc()
            for line in full.splitlines():
                self.log(line, "err")
            err = str(e)
            if "Sign in" in err or "bot" in err.lower():
                err = "YouTube requiere autenticación. Actualiza o vuelve a exportar las cookies."
            elif "DPAPI" in err or "cookie database" in err or "Could not copy" in err:
                err = ("No se puede leer cookies del navegador.\n"
                       "① Cierra el navegador completamente (bandeja incluida).\n"
                       "② O usa modo Archivo .txt → pulsa '¿Cómo exportarlas?'.")
            self._done(False, err)

    def _pick_format(self, formats, want):
        """Choose the best real format_id from the available list."""
        if not formats:
            self.log("⚠ Lista de formatos vacía, usando 'best'", "info")
            return "best"

        if want == "mp3":
            audio = [f for f in formats
                     if f.get("vcodec") in (None, "none", "")
                     and f.get("acodec") not in (None, "none", "")]
            if audio:
                best = max(audio, key=lambda f: f.get("abr") or 0)
                return best["format_id"]
            return "bestaudio"

        video = [f for f in formats if f.get("vcodec") not in (None, "none", "")]
        audio = [f for f in formats
                 if f.get("vcodec") in (None, "none", "")
                 and f.get("acodec") not in (None, "none", "")]

        if not video:
            self.log("⚠ Sin streams de vídeo, usando 'best'", "info")
            return "best"

        ext = want
        vid_pref = [f for f in video if f.get("ext") == ext]
        best_vid = max(vid_pref or video,
                       key=lambda f: (f.get("height") or 0, f.get("tbr") or 0))

        if audio:
            aud_pref = ([f for f in audio if f.get("ext") in ("m4a", "aac")]
                        if ext == "mp4"
                        else [f for f in audio if f.get("ext") == "webm"])
            best_aud = max(aud_pref or audio, key=lambda f: f.get("abr") or 0)
            return f"{best_vid['format_id']}+{best_aud['format_id']}"

        return best_vid["format_id"]

    def _progress_hook(self, d):
        if d["status"] == "downloading":
            raw = d.get("_percent_str", "0%").strip()
            pct_str = re.sub(r"\x1b\[[0-9;]*m", "", raw).replace("%", "").strip()
            try:
                pct = float(pct_str)
            except ValueError:
                pct = 0.0
            speed = re.sub(r"\x1b\[[0-9;]*m", "", d.get("_speed_str", "—").strip())
            eta   = re.sub(r"\x1b\[[0-9;]*m", "", d.get("_eta_str",   "—").strip())
            self.progress.set(pct)
            self.status.set(f"⬇  {pct:.1f}%   •   {speed}   •   ETA {eta}")
        elif d["status"] == "finished":
            fname = os.path.basename(d.get("filename", ""))
            self.log(f"✔ Archivo guardado: {fname}", "ok")
            self.progress.set(99)
            self.status.set("⚙  Procesando…")

    def _done(self, success, error_msg):
        self.is_busy = False
        if success:
            self.progress.set(100)
            self.status.set(f"✔  ¡Completado! Guardado en: {self.save_path.get()}")
            self.log("✔ ¡Descarga completada!", "ok")
        else:
            self.progress.set(0)
            self.status.set(f"✘  {error_msg[:180]}")
            self.log(f"✘ {error_msg}", "err")
        self.dl_btn.config(state="normal", text="⬇  Descargar")


if __name__ == "__main__":
    app = YTDownloader()
    app.mainloop()