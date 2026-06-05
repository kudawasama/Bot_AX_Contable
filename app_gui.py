import tkinter as tk
from tkinter import scrolledtext
import threading
import queue
import sys
import os
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
        self.log_queue = queue.Queue()
        self.ok_count = 0
        self.err_count = 0
        self.cycle = 0

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
        tk.Label(brand, text=f" {VERSION_TAG}", font=self.f["sm"],
                 bg=self.c["bg"], fg=self.c["subtext"]).pack(side="left", padx=4)

        sha = get_git_short_sha()
        if sha:
            tk.Label(brand, text=f"@{sha}", font=self.f["sm"],
                     bg=self.c["bg"], fg=self.c["muted"]).pack(side="left", padx=2)

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
            (VERSION_TAG, self.c["accent"]),
            ("RSA-4096", self.c["subtext"]),
        ]
        for txt, clr in left_tags:
            tk.Label(footer, text=f"  {txt}  ", font=self.f["sm"],
                     bg=self.c["bg"], fg=clr).pack(side="left")
            tk.Label(footer, text="|", font=self.f["sm"],
                     bg=self.c["bg"], fg=self.c["border"]).pack(side="left")

        sha = get_git_short_sha()
        if sha:
            tk.Label(footer, text=f"  @{sha}  ", font=self.f["sm"],
                     bg=self.c["bg"], fg=self.c["subtext"]).pack(side="left")
            tk.Label(footer, text="|", font=self.f["sm"],
                     bg=self.c["bg"], fg=self.c["border"]).pack(side="left")

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

        self._status_row(s, "Engine",  "IDLE",       self.c["subtext"])
        self._status_row(s, "Session", "00:00:00",   self.c["subtext"])
        self._status_row(s, "Node",    "ACTIVE",     self.c["green"])

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

        # ---- NEURAL STREAM ----
        stream_card = self._card(right)
        stream_inner = tk.Frame(stream_card, bg=self.c["card"])
        stream_inner.pack(fill="both", expand=True, padx=16, pady=(14, 14))
        stream_inner.grid_rowconfigure(0, weight=1)
        stream_inner.grid_columnconfigure(0, weight=1)

        tk.Label(stream_inner, text="LIVE STREAM", font=self.f["h3"],
                 bg=self.c["card"], fg=self.c["amber"]).grid(
            row=0, column=0, sticky="w", pady=(0, 8))

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

    def _status_row(self, parent, label, value, color):
        f = tk.Frame(parent, bg=self.c["card"])
        f.pack(fill="x", padx=16, pady=1)
        tk.Label(f, text=label, font=self.f["body"],
                 bg=self.c["card"], fg=self.c["subtext"]).pack(side="left")
        tk.Label(f, text=value, font=self.f["body"],
                 bg=self.c["card"], fg=color).pack(side="right")

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
        self.log("Engine starting ...")
        self.btn_start.config(state="disabled", fg=self.c["muted"])
        self.btn_stop.config(state="normal", fg=self.c["red"])
        self._pulse(True)
        self.bot_thread = threading.Thread(
            target=self.run_bot_thread, daemon=True)
        self.bot_thread.start()

    def stop_bot(self):
        self.stop_event.set()
        self.log("Stopping engine ...")
        self.btn_stop.config(state="disabled", fg=self.c["muted"])
        self._pulse(False)

    def run_bot_thread(self):
        try:
            run_bot(log_callback=self.log, stop_event=self.stop_event)
        finally:
            self.root.after(0, lambda: self.btn_start.config(
                state="normal", fg=self.c["green"]))
            self.root.after(0, lambda: self.btn_stop.config(
                state="disabled", fg=self.c["muted"]))
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
