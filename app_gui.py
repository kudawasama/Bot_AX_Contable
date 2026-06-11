import tkinter as tk
from tkinter import scrolledtext
import threading
import queue
import sys
import os
import time
from datetime import datetime
from bot_main import run_bot
from setup_areas import AreaSelector
from logger import get_logger, QueueLogHandler
from _version import VERSION_TAG, get_git_short_sha

logger = get_logger()


class BotAXGui:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Bot AX Contable  {VERSION_TAG}")
        self.root.configure(bg="#0d1117")
        self.root.minsize(1000, 680)

        # ---- palette ----
        self.c = {
            "bg":       "#0d1117",
            "card":     "#161b22",
            "hover":    "#1c2330",
            "border":   "#30363d",
            "accent":   "#58a6ff",
            "accent2":  "#8b5cf6",
            "green":    "#3fb950",
            "red":      "#f85149",
            "amber":    "#d29922",
            "text":     "#e6edf3",
            "subtext":  "#8b949e",
            "muted":    "#484f58",
        }

        # ---- fonts ----
        self.f = {
            "h1":    ("Segoe UI Variable Display Semib", 22),
            "h2":    ("Segoe UI Variable Display Semib", 14),
            "h3":    ("Segoe UI Semibold", 11),
            "body":  ("Segoe UI", 10),
            "mono":  ("Cascadia Code", 9),
            "monob": ("Cascadia Code", 10, "bold"),
            "clock": ("Cascadia Code", 15, "bold"),
            "sm":    ("Segoe UI", 8),
        }

        # ---- state ----
        self.bot_thread = None
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.log_queue = queue.Queue()
        self.ok_count = 0
        self.err_count = 0
        self.cycle = 0
        self._session_start = None
        self._session_paused = 0.0

        # Conectar logging estructurado a la GUI
        queue_handler = QueueLogHandler(self.log_queue)
        logger.addHandler(queue_handler)

        self._build()
        self._center_window(1080, 720)
        self._animate_clock()
        self.check_queue()

    # ============================================================
    #  WINDOW
    # ============================================================

    def _center_window(self, w, h):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    # ============================================================
    #  LAYOUT
    # ============================================================

    def _build(self):
        # outer padding frame
        pad = tk.Frame(self.root, bg=self.c["bg"])
        pad.pack(fill="both", expand=True, padx=24, pady=20)

        # ---- HEADER ----
        header = tk.Frame(pad, bg=self.c["bg"], height=56)
        header.pack(fill="x", pady=(0, 20))
        header.pack_propagate(False)

        # brand + versión + commit
        brand = tk.Frame(header, bg=self.c["bg"])
        brand.pack(side="left")

        self._dot = tk.Canvas(brand, bg=self.c["bg"], width=10, height=10,
                              highlightthickness=0)
        self._dot.pack(side="left", padx=(0, 10))
        self._dot_idle = self._dot.create_oval(2, 2, 8, 8,
                                               fill=self.c["muted"], outline="")

        tk.Label(brand, text="Bot AX Contable", font=self.f["h2"],
                 bg=self.c["bg"], fg=self.c["text"]).pack(side="left")
        self._lbl_header_version = tk.Label(brand, text=f" {VERSION_TAG}", font=self.f["sm"],
                 bg=self.c["bg"], fg=self.c["subtext"])
        self._lbl_header_version.pack(side="left", padx=4)

        sha = get_git_short_sha()
        if sha:
            self._lbl_header_sha = tk.Label(brand, text=f"@{sha}", font=self.f["sm"],
                     bg=self.c["bg"], fg=self.c["muted"])
            self._lbl_header_sha.pack(side="left", padx=2)

        # clock
        clock_frame = tk.Frame(header, bg=self.c["card"])
        clock_frame.pack(side="right")
        tk.Frame(clock_frame, bg=self.c["border"], width=1,
                 height=28).pack(side="left", padx=10, fill="y")
        self.clock_lbl = tk.Label(clock_frame, text="00:00:00",
                                  font=self.f["clock"], bg=self.c["card"],
                                  fg=self.c["accent"])
        self.clock_lbl.pack(side="left", padx=12, pady=6)
        tk.Label(clock_frame, text="LOCAL", font=self.f["sm"],
                 bg=self.c["card"], fg=self.c["subtext"]).pack(
            side="left", padx=(0, 12))

        # ---- BODY ----
        body = tk.Frame(pad, bg=self.c["bg"])
        body.pack(fill="both", expand=True)

        # columns
        body.grid_columnconfigure(0, minsize=220)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        self._left_panel(body)
        self._right_panel(body)

        # ---- FOOTER ----
        footer = tk.Frame(pad, bg=self.c["bg"], height=24)
        footer.pack(fill="x", side="bottom", pady=(14, 0))
        footer.pack_propagate(False)

        left_tags = [
            ("RSA-4096", self.c["subtext"]),
        ]
        self._lbl_footer_version = self._ftag(VERSION_TAG, self.c["accent"], footer)
        self._fsep(footer)
        for txt, clr in left_tags:
            self._ftag(txt, clr, footer)
            self._fsep(footer)

        sha = get_git_short_sha()
        self._lbl_footer_sha = None
        if sha:
            self._lbl_footer_sha = self._ftag(f"@{sha}", self.c["subtext"], footer)
            self._fsep(footer)

        # sync button (right side)
        self._lbl_sync = tk.Label(
            footer, text="↻", font=self.f["sm"],
            bg=self.c["bg"], fg=self.c["muted"],
            cursor="hand2",
        )
        self._lbl_sync.pack(side="right", padx=(0, 2))
        self._lbl_sync.bind("<Button-1>", lambda e: self._do_sync())
        self._lbl_sync.bind(
            "<Enter>", lambda e: self._lbl_sync.config(fg=self.c["accent"]))
        self._lbl_sync.bind(
            "<Leave>", lambda e: self._lbl_sync.config(fg=self.c["muted"]))

        tk.Label(footer, text="Cotano_", font=self.f["sm"],
                 bg=self.c["bg"], fg=self.c["muted"]).pack(side="right")

    # ----------------------------------------------------------
    #  LEFT  PANEL
    # ----------------------------------------------------------

    def _left_panel(self, parent):
        left = tk.Frame(parent, bg=self.c["bg"])
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 18))

        # card: STATUS
        s = self._card(left)
        tk.Label(s, text="STATUS", font=self.f["h3"],
                 bg=self.c["card"], fg=self.c["accent"]).pack(
            anchor="w", padx=16, pady=(14, 8))

        self._lbl_engine = self._status_row(s, "Engine",  "IDLE",       self.c["subtext"])
        self._lbl_session = self._status_row(s, "Session", "00:00:00",   self.c["subtext"])
        self._lbl_node = self._status_row(s, "Node",    "ACTIVE",     self.c["green"])

        # card: METRICS
        m = self._card(left)
        tk.Label(m, text="METRICS", font=self.f["h3"],
                 bg=self.c["card"], fg=self.c["accent2"]).pack(
            anchor="w", padx=16, pady=(14, 8))

        # ---- success ----
        row_ok = tk.Frame(m, bg=self.c["card"])
        row_ok.pack(fill="x", padx=16, pady=2)
        tk.Label(row_ok, text="Success", font=self.f["body"],
                 bg=self.c["card"], fg=self.c["text"]).pack(side="left")
        self.lbl_ok = tk.Label(row_ok, text="0", font=self.f["monob"],
                               bg=self.c["card"], fg=self.c["green"])
        self.lbl_ok.pack(side="right")

        self._progress(m, self.c["green"], "bar_ok")

        # ---- errors ----
        row_err = tk.Frame(m, bg=self.c["card"])
        row_err.pack(fill="x", padx=16, pady=(10, 2))
        tk.Label(row_err, text="Errors", font=self.f["body"],
                 bg=self.c["card"], fg=self.c["text"]).pack(side="left")
        self.lbl_err = tk.Label(row_err, text="0", font=self.f["monob"],
                                bg=self.c["card"], fg=self.c["red"])
        self.lbl_err.pack(side="right")

        self._progress(m, self.c["red"], "bar_err")

        # ---- cycle ----
        row_cy = tk.Frame(m, bg=self.c["card"])
        row_cy.pack(fill="x", padx=16, pady=(10, 2))
        tk.Label(row_cy, text="Cycle", font=self.f["body"],
                 bg=self.c["card"], fg=self.c["text"]).pack(side="left")
        self.lbl_cy = tk.Label(row_cy, text="0", font=self.f["monob"],
                               bg=self.c["card"], fg=self.c["amber"])
        self.lbl_cy.pack(side="right")

        self._progress(m, self.c["amber"], "bar_cy")

        # card: ACTIONS
        a = self._card(left)
        tk.Label(a, text="ACTIONS", font=self.f["h3"],
                 bg=self.c["card"], fg=self.c["text"]).pack(
            anchor="w", padx=16, pady=(14, 8))

        self._action_btn(a, "Adjust Regions",   self.run_setup)
        self._action_btn(a, "View Snapshots",   self.open_screenshots)
        self._action_btn(a, "Export Logs",      self.open_logs)
        self._action_btn(a, "Clear Errors",     self.clear_errors)

    # ----------------------------------------------------------
    #  RIGHT PANEL
    # ----------------------------------------------------------

    def _right_panel(self, parent):
        right = tk.Frame(parent, bg=self.c["bg"])
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        # ---- ENGINE CONTROL ----
        ctrl_card = self._card(right)
        ctrl_inner = tk.Frame(ctrl_card, bg=self.c["card"])
        ctrl_inner.pack(fill="x", padx=16, pady=(14, 16))

        tk.Label(ctrl_inner, text="ENGINE CONTROL", font=self.f["h3"],
                 bg=self.c["card"], fg=self.c["accent"]).pack(
            anchor="w", pady=(0, 10))

        btn_row = tk.Frame(ctrl_inner, bg=self.c["card"])
        btn_row.pack(fill="x")

        self.btn_start = self._ctrl_btn(
            btn_row, "Start Engine",  self.c["green"], self.start_bot)
        self.btn_start.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.btn_stop = self._ctrl_btn(
            btn_row, "Stop Engine",   self.c["red"],   self.stop_bot,
            disabled=True)
        self.btn_stop.pack(side="left", fill="x", expand=True, padx=(6, 0))

        # segunda fila: pause
        pause_row = tk.Frame(ctrl_inner, bg=self.c["card"])
        pause_row.pack(fill="x", pady=(8, 0))
        self.btn_pause = self._ctrl_btn(
            pause_row, "⏸ Pause",  self.c["amber"], self.toggle_pause,
            disabled=True)
        self.btn_pause.pack(side="left", fill="x", expand=True)

        # ---- NEURAL STREAM ----
        stream_card = self._card(right)
        stream_inner = tk.Frame(stream_card, bg=self.c["card"])
        stream_inner.pack(fill="both", expand=True, padx=16, pady=(14, 14))
        stream_inner.grid_rowconfigure(1, weight=1)
        stream_inner.grid_columnconfigure(0, weight=1)

        # header row: label + toolbar
        head_frame = tk.Frame(stream_inner, bg=self.c["card"])
        head_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        head_frame.grid_columnconfigure(0, weight=1)

        tk.Label(head_frame, text="LIVE STREAM", font=self.f["h3"],
                 bg=self.c["card"], fg=self.c["amber"]).pack(side="left")

        # toolbar buttons (right side)
        self._log_btn("📋", "Mostrar solo errores", self._show_errors, head_frame)
        self._log_btn("✕S", "Eliminar seleccionadas", self._delete_selected, head_frame)
        self._log_btn("✕A", "Limpiar todo el log", self._clear_log, head_frame)

        self.log_widget = scrolledtext.ScrolledText(
            stream_inner, bg="#0d1117", fg=self.c["text"],
            font=self.f["mono"], insertbackground=self.c["accent"],
            borderwidth=0, highlightthickness=0,
            padx=14, pady=10, height=16)
        self.log_widget.grid(row=1, column=0, sticky="nsew")
        self.log_widget.config(state="disabled")

        self.log_widget.tag_config("ok", foreground=self.c["green"])
        self.log_widget.tag_config("err", foreground=self.c["red"])
        self.log_widget.tag_config("warn", foreground=self.c["amber"])
        self.log_widget.tag_config("info", foreground=self.c["accent"])
        self.log_widget.tag_config("err_sel", background="#3d1010",
                                   foreground=self.c["red"])

        # Click derecho → menú contextual sobre errores
        self._err_menu = tk.Menu(self.log_widget, tearoff=0,
                                 bg=self.c["card"], fg=self.c["text"],
                                 activebackground=self.c["hover"],
                                 activeforeground=self.c["accent"],
                                 font=self.f["body"])
        self._err_menu.add_command(label="🗑 Borrar esta línea",
                                   command=self._delete_clicked_err)
        self._err_menu.add_command(label="📋 Borrar solo errores",
                                   command=self._delete_all_errs)
        self.log_widget.bind("<Button-3>", self._show_err_menu)

    # ============================================================
    #  COMPONENTS
    # ============================================================

    def _card(self, parent):
        """Returns inner frame of a card with 1px colored border."""
        outer = tk.Frame(parent, bg=self.c["border"], bd=0)
        outer.pack(fill="x", pady=(0, 14))
        inner = tk.Frame(outer, bg=self.c["card"], bd=0)
        inner.pack(fill="both", padx=1, pady=1)
        return inner

    def _ftag(self, text, color, parent):
        """Footer tag label."""
        lbl = tk.Label(parent, text=f"  {text}  ", font=self.f["sm"],
                       bg=self.c["bg"], fg=color)
        lbl.pack(side="left")
        return lbl

    def _fsep(self, parent):
        """Footer separator."""
        tk.Label(parent, text="|", font=self.f["sm"],
                 bg=self.c["bg"], fg=self.c["border"]).pack(side="left")

    def _status_row(self, parent, label, value, color):
        f = tk.Frame(parent, bg=self.c["card"])
        f.pack(fill="x", padx=16, pady=1)
        tk.Label(f, text=label, font=self.f["body"],
                 bg=self.c["card"], fg=self.c["subtext"]).pack(side="left")
        lbl = tk.Label(f, text=value, font=self.f["body"],
                       bg=self.c["card"], fg=color)
        lbl.pack(side="right")
        return lbl

    def _log_btn(self, text, tooltip, cmd, parent):
        """Pequeño botón para toolbar del log."""
        btn = tk.Label(parent, text=text, font=self.f["sm"],
                       bg=self.c["card"], fg=self.c["subtext"],
                       cursor="hand2", padx=4)
        btn.pack(side="right", padx=(2, 0))
        btn.bind("<Button-1>", lambda e: cmd())
        btn.bind("<Enter>", lambda e: btn.config(fg=self.c["accent"]))
        btn.bind("<Leave>", lambda e: btn.config(fg=self.c["subtext"]))

    def _progress(self, parent, color, tag_name):
        c = tk.Canvas(parent, bg=self.c["hover"], height=3,
                      highlightthickness=0)
        c.pack(fill="x", padx=16, pady=(1, 2))
        setattr(self, tag_name, c)
        setattr(self, f"{tag_name}_rect",
                c.create_rectangle(0, 0, 0, 3, fill=color, outline=""))

    def _action_btn(self, parent, text, cmd):
        f = tk.Frame(parent, bg=self.c["card"], cursor="hand2")
        f.pack(fill="x", padx=10, pady=0)

        tk.Label(f, text=f"    {text}", font=self.f["body"],
                 bg=self.c["card"], fg=self.c["subtext"]).pack(
            anchor="w", padx=6, pady=5)

        def _enter(e):
            f.config(bg=self.c["hover"])
            try:
                e.widget.config(bg=self.c["hover"], fg=self.c["accent"])
            except tk.TclError:
                pass  # Frame no soporta fg

        def _leave(e):
            f.config(bg=self.c["card"])
            try:
                e.widget.config(bg=self.c["card"], fg=self.c["subtext"])
            except tk.TclError:
                pass  # Frame no soporta fg

        for child in f.winfo_children():
            child.bind("<Button-1>", lambda e, c=cmd: c())
            child.bind("<Enter>", _enter)
            child.bind("<Leave>", _leave)
        f.bind("<Button-1>", lambda e, c=cmd: c())
        f.bind("<Enter>", _enter)
        f.bind("<Leave>", _leave)

    def _ctrl_btn(self, parent, text, color, cmd, disabled=False):
        btn = tk.Label(parent, text=text, font=self.f["h3"],
                       bg=self.c["card"], fg=color if not disabled else self.c["muted"],
                       cursor="hand2", padx=28, pady=12,
                       highlightbackground=self.c["border"],
                       highlightthickness=1)
        btn.bind("<Button-1>", lambda e: cmd())
        btn.bind("<Enter>",
                 lambda e: btn.config(bg=self.c["hover"]))
        btn.bind("<Leave>",
                 lambda e: btn.config(bg=self.c["card"]))
        if disabled:
            btn.config(state="disabled")
        return btn

    # ============================================================
    #  ANIMATIONS
    # ============================================================

    def _animate_clock(self):
        self.clock_lbl.config(text=datetime.now().strftime("%H:%M:%S"))
        # Actualizar sesión en vivo si el engine está corriendo
        if self._session_start is not None and not self.pause_event.is_set():
            elapsed = time.time() - self._session_start - self._session_paused
            h, r = divmod(int(elapsed), 3600)
            m, s = divmod(r, 60)
            self._lbl_session.config(text=f"{h:02d}:{m:02d}:{s:02d}")
        self.root.after(1000, self._animate_clock)

    def _pulse(self, active):
        color = self.c["accent"] if active else self.c["muted"]
        self._dot.itemconfig(self._dot_idle, fill=color)

    def _update_bar(self, canvas, rect, value, total):
        pct = min(value / max(total, 1), 1.0)
        w = int(canvas.winfo_width() or 190)
        canvas.coords(rect, 0, 0, int(w * pct), 3)

    # ============================================================
    #  LOGIC
    # ============================================================

    def log(self, message):
        self.log_queue.put(message)

    def check_queue(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self.log_widget.config(state="normal")
                ts = datetime.now().strftime("%H:%M:%S")

                tag = None
                sym = " . "
                if "[RESULT:OK]" in msg:
                    sym, tag = " + ", "ok"
                elif "[RESULT:ERROR]" in msg:
                    sym, tag = " ! ", "err"

                start = self.log_widget.index("end-1c")
                self.log_widget.insert(tk.END, f"[{ts}]{sym}{msg}\n")
                if tag:
                    end = self.log_widget.index("end-1c")
                    self.log_widget.tag_add(tag, start, end)
                self.log_widget.see(tk.END)
                self.log_widget.config(state="disabled")

                if "[RESULT:OK]" in msg:
                    self.ok_count += 1
                    self.lbl_ok.config(text=str(self.ok_count))
                elif "[RESULT:ERROR]" in msg:
                    self.err_count += 1
                    self.lbl_err.config(text=str(self.err_count))

                if "Iniciando Ciclo" in msg:
                    try:
                        n = int(msg.split("Ciclo")[1].split("---")[0].strip())
                        self.cycle = n
                        self.lbl_cy.config(text=str(n))
                    except Exception:
                        pass

                total = max(self.ok_count + self.err_count, 1)
                self._update_bar(self.bar_ok, self.bar_ok_rect,
                                 self.ok_count, total)
                self._update_bar(self.bar_err, self.bar_err_rect,
                                 self.err_count, total)
                self._update_bar(self.bar_cy, self.bar_cy_rect,
                                 self.cycle, max(self.cycle, 1))
        except queue.Empty:
            pass
        self.root.after(100, self.check_queue)

    def start_bot(self):
        if self.bot_thread and self.bot_thread.is_alive():
            return
        self.stop_event.clear()
        self.pause_event.clear()
        # Status en vivo
        self._session_start = time.time()
        self._session_paused = 0.0
        self._lbl_engine.config(text="RUNNING", fg=self.c["green"])
        self._lbl_session.config(text="00:00:00", fg=self.c["accent"])
        self.log("Engine starting ...")
        self.btn_start.config(state="disabled", fg=self.c["muted"])
        self.btn_stop.config(state="normal", fg=self.c["red"])
        self.btn_pause.config(state="normal", fg=self.c["amber"], text="⏸ Pause")
        self._pulse(True)
        self.bot_thread = threading.Thread(
            target=self.run_bot_thread, daemon=True)
        self.bot_thread.start()

    def stop_bot(self):
        self.stop_event.set()
        self.pause_event.clear()  # salir de pausa si estaba
        self.log("Stopping engine ...")
        self._lbl_engine.config(text="IDLE", fg=self.c["subtext"])
        self._lbl_session.config(text="00:00:00", fg=self.c["subtext"])
        self._session_start = None
        self._session_paused = 0.0
        self.btn_stop.config(state="disabled", fg=self.c["muted"])
        self.btn_pause.config(state="disabled", fg=self.c["muted"], text="⏸ Pause")
        self._pulse(False)

    def toggle_pause(self):
        if self.pause_event.is_set():
            self.pause_event.clear()
            self._lbl_engine.config(text="RUNNING", fg=self.c["green"])
            self.log("▶ Reanudando ...")
            self.btn_pause.config(text="⏸ Pause", fg=self.c["amber"])
        else:
            self.pause_event.set()
            self._lbl_engine.config(text="PAUSED", fg=self.c["amber"])
            self.log("⏸ Pausado — el bot esperará al reanudar")
            self.btn_pause.config(text="▶ Resume", fg=self.c["green"])

    def clear_errors(self):
        """Resetea contadores y borra blacklist.json."""
        self.ok_count = 0
        self.err_count = 0
        self.cycle = 0
        self.lbl_ok.config(text="0")
        self.lbl_err.config(text="0")
        self.lbl_cy.config(text="0")
        self._update_bar(self.bar_ok, self.bar_ok_rect, 0, 0)
        self._update_bar(self.bar_err, self.bar_err_rect, 0, 0)
        self._update_bar(self.bar_cy, self.bar_cy_rect, 0, 0)
        # Borrar blacklist
        bl = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blacklist.json")
        if os.path.exists(bl):
            os.remove(bl)
            self.log("🗑 Blacklist borrada.")
        self.log("🧹 Contadores reseteados.")
        # También scrollear a los errores en el log
        self._show_errors()

    # ── Log interactivo ──────────────────────────────────────

    def _get_err_lines(self):
        """Retorna lista ordenada de números de línea con tag 'err'."""
        ranges = self.log_widget.tag_ranges("err")
        return sorted(set(int(str(r).split(".")[0]) for r in ranges))

    def _show_errors(self):
        """Scrollea al primer error y resalta todos."""
        lines = self._get_err_lines()
        if not lines:
            self.log("📋 No hay errores en el log.")
            return
        self.log_widget.config(state="normal")
        for ln in lines:
            self.log_widget.tag_add("err_sel", f"{ln}.0", f"{ln}.end")
        self.log_widget.see(f"{lines[0]}.0")
        self.log_widget.config(state="disabled")
        self.log(f"📋 {len(lines)} error(es) resaltado(s).")

    def _delete_selected(self):
        """Borra las líneas resaltadas (con tag err_sel)."""
        lines = self._get_err_lines()
        if not lines:
            return
        self.log_widget.config(state="normal")
        # Se eliminan por el tag "err" para cubrir líneas completas
        for ln in reversed(lines):
            self.log_widget.delete(f"{ln}.0", f"{ln+1}.0")
        self.log_widget.config(state="disabled")
        self.log(f"✕ {len(lines)} error(es) eliminado(s) del log.")

    def _clear_log(self):
        """Limpia TODO el log widget."""
        self.log_widget.config(state="normal")
        self.log_widget.delete("1.0", tk.END)
        self.log_widget.config(state="disabled")

    def _show_err_menu(self, event):
        """Menú contextual con click derecho sobre una línea de error."""
        index = self.log_widget.index(f"@{event.x},{event.y}")
        line = int(index.split(".")[0])
        tags = self.log_widget.tag_names(f"{line}.0")
        if "err" in tags:
            self._err_menu.line = line
            self._err_menu.tk_popup(event.x_root, event.y_root)
        return "break"

    def _delete_clicked_err(self):
        """Borra la línea donde se hizo click derecho."""
        line = getattr(self._err_menu, "line", None)
        if line is None:
            return
        self.log_widget.config(state="normal")
        self.log_widget.delete(f"{line}.0", f"{line+1}.0")
        self.log_widget.config(state="disabled")
        self.log(f"🗑 Línea {line} eliminada.")

    def _delete_all_errs(self):
        """Borra todas las líneas con tag err del widget."""
        lines = self._get_err_lines()
        if not lines:
            return
        self.log_widget.config(state="normal")
        for ln in reversed(lines):
            self.log_widget.delete(f"{ln}.0", f"{ln+1}.0")
        self.log_widget.config(state="disabled")
        self.log("🗑 Todos los errores eliminados del log.")

    def _do_sync(self):
        """Pull latest code from git in a background thread."""
        if getattr(self, "_syncing", False):
            return
        self._syncing = True
        self._lbl_sync.config(fg=self.c["amber"])
        self.log("↻ Syncing: pulling latest code ...")
        threading.Thread(target=self._sync_thread, daemon=True).start()

    def _sync_thread(self):
        import subprocess
        repo = os.path.dirname(os.path.abspath(__file__))
        try:
            result = subprocess.run(
                ["git", "pull", "--ff-only"],
                capture_output=True, text=True, cwd=repo, timeout=60,
            )
            output = (result.stdout + result.stderr).strip()
        except subprocess.TimeoutExpired:
            output = "Timeout: git pull tardó más de 60s"
        except Exception as e:
            output = f"Error: {e}"

        self.root.after(0, lambda: self._sync_done(output))

    def _sync_done(self, output):
        self._syncing = False
        self._lbl_sync.config(fg=self.c["muted"])
        self.log(f"↻ Sync result: {output}")

        # Refresh version info
        import importlib
        import _version as vmod
        importlib.reload(vmod)
        vtag = vmod.VERSION_TAG
        sha = vmod.get_git_short_sha()

        # Update window title
        self.root.title(f"Bot AX Contable  {vtag}")

        # Update header + footer labels
        self._lbl_header_version.config(text=f" {vtag} ")
        if hasattr(self, "_lbl_header_sha") and self._lbl_header_sha:
            self._lbl_header_sha.config(text=f"@{sha}")
        self._lbl_footer_version.config(text=f"  {vtag}  ")
        if self._lbl_footer_sha:
            self._lbl_footer_sha.config(text=f"  @{sha}  ")

        self.log(f"↻ Version actualizada: {vtag} @{sha}")

    def run_bot_thread(self):
        try:
            run_bot(log_callback=self.log, stop_event=self.stop_event,
                    pause_event=self.pause_event)
        finally:
            self.pause_event.clear()
            self.root.after(0, lambda: self._lbl_engine.config(
                text="IDLE", fg=self.c["subtext"]))
            self.root.after(0, lambda: self._lbl_session.config(
                text="00:00:00", fg=self.c["subtext"]))
            self._session_start = None
            self._session_paused = 0.0
            self.root.after(0, lambda: self.btn_start.config(
                state="normal", fg=self.c["green"]))
            self.root.after(0, lambda: self.btn_stop.config(
                state="disabled", fg=self.c["muted"]))
            self.root.after(0, lambda: self.btn_pause.config(
                state="disabled", fg=self.c["muted"], text="⏸ Pause"))
            self.root.after(0, lambda: self._pulse(False))

    def run_setup(self):
        if self.bot_thread and self.bot_thread.is_alive():
            return
        self.root.iconify()
        AreaSelector().run()
        self.root.deiconify()

    def open_screenshots(self):
        path = os.path.join("logs", "capturas")
        if not os.path.exists(path):
            os.makedirs(path)
        os.startfile(path)

    def open_logs(self):
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        name = f"registro_{fecha_hoy}.txt"
        if os.path.exists(name):
            os.startfile(name)


if __name__ == "__main__":
    root = tk.Tk()
    app = BotAXGui(root)
    root.mainloop()
