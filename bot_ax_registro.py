import tkinter as tk
from tkinter import scrolledtext
import threading
import queue
import os
from datetime import datetime
from bot_main import run_bot
from setup_areas import AreaSelector

# Configuración de estetica Gemini Core (Ultra-High Fidelity)
COLORS = {
    "bg": "#05060b",         # Negro abisal
    "sidebar": "#0b0c14",    # Gris oscuro profundo
    "surface": "#121420",    # Superficie de componentes
    "accent": "#89b4fa",     # Azul Gemini
    "success": "#a6e3a1",    # Verde exito
    "error": "#f38ba8",      # Rojo error
    "warning": "#fab387",    # Naranja advertencia
    "text": "#cdd6f4",       # Texto principal
    "subtext": "#6c7086",    # Texto secundario
    "grid": "#1e1e2e"        # Lineas de division
}

class BotAXRegistroGui:
    def __init__(self, root):
        self.root = root
        self.root.title("GEMINI ENGINE - BOT AX REGISTRO")
        self.root.geometry("1100x850")
        self.root.configure(bg=COLORS["bg"])
        
        # Opcional: Hacerla sin bordes nativos pero con controles personalizados
        # Si causó problemas de "congelamiento", mantendremos el marco pero ocultaremos la decoracion si es posible
        # o simplemente haremos que el contenido sea tan impactante que el marco no importe.
        # Intentaré una ventana sin bordes más robusta:
        self.root.overrideredirect(True)
        
        # Variables de estado
        self.stop_event = threading.Event()
        self.log_queue = queue.Queue()
        self.exitos = 0
        self.errores = 0
        
        # Fuentes
        self.font_main = ("Consolas", 10)
        self.font_bold = ("Consolas", 11, "bold")
        self.font_title = ("Consolas", 16, "bold")
        self.font_small = ("Consolas", 8)

        self.setup_ui()
        self.setup_dragging()
        self.update_loop()

    def setup_ui(self):
        # --- Borde Exterior de la Aplicación (Glow simple) ---
        self.main_frame = tk.Frame(self.root, bg=COLORS["bg"], highlightbackground=COLORS["accent"], highlightthickness=1)
        self.main_frame.pack(fill="both", expand=True)

        # 1. BARRA SUPERIOR (HEADER)
        header = tk.Frame(self.main_frame, bg=COLORS["bg"], height=60)
        header.pack(fill="x", side="top", padx=20, pady=10)
        
        # Logo & Titulo
        logo_label = tk.Label(header, text="󰄶", font=("Segoe UI Symbol", 24), bg=COLORS["bg"], fg=COLORS["accent"])
        logo_label.pack(side="left", padx=(10, 15))
        
        title_f = tk.Frame(header, bg=COLORS["bg"])
        title_f.pack(side="left")
        tk.Label(title_f, text="GEMINI ENGINE", font=self.font_bold, bg=COLORS["bg"], fg=COLORS["accent"]).pack(anchor="w")
        tk.Label(title_f, text="CORE MODULE // REGISTRO_AUTO", font=self.font_small, bg=COLORS["bg"], fg=COLORS["success"]).pack(anchor="w")

        # Botones de Ventana
        close_btn = tk.Label(header, text="✕", font=("Consolas", 16), bg=COLORS["bg"], fg=COLORS["subtext"], cursor="hand2")
        close_btn.pack(side="right", padx=10)
        close_btn.bind("<Button-1>", lambda e: self.root.destroy())
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg=COLORS["error"]))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg=COLORS["subtext"]))

        self.uptime_label = tk.Label(header, text="UPTIME: 00:00:00", font=self.font_small, bg=COLORS["bg"], fg=COLORS["subtext"], justify="right")
        self.uptime_label.pack(side="right", padx=20)

        # 2. CUERPO (BODY)
        body = tk.Frame(self.main_frame, bg=COLORS["bg"])
        body.pack(fill="both", expand=True, padx=20, pady=10)

        # --- SIDEBAR (IZQUIERDA) ---
        sidebar = tk.Frame(body, bg=COLORS["sidebar"], width=240)
        sidebar.pack(side="left", fill="y", padx=(0, 20))
        sidebar.pack_propagate(False)

        # ASCII Art Bunny (Centrado)
        bunny = "\n   (\\ _ /)\n   (  . . )\n   c( \" ) ( \" )\n   -----------\n     STATION\n      READY\n   -----------"
        tk.Label(sidebar, text=bunny, font=("Courier New", 10), bg=COLORS["sidebar"], fg=COLORS["accent"]).pack(pady=20)

        # System Monitors
        mon_title = tk.Label(sidebar, text="SYSTEM MONITORS", font=self.font_small, bg=COLORS["sidebar"], fg=COLORS["subtext"])
        mon_title.pack(anchor="w", padx=20, pady=(10, 5))
        
        self.add_monitor(sidebar, "CPU_USAGE", 0.35)
        self.add_monitor(sidebar, "MEM_USAGE", 0.52)
        self.add_monitor(sidebar, "NET_TRAFFIC", 0.08)

        # Session Stats
        tk.Label(sidebar, text="SESSION METRICS", font=self.font_small, bg=COLORS["sidebar"], fg=COLORS["subtext"]).pack(anchor="w", padx=20, pady=(30, 5))
        
        self.lbl_exitos = tk.Label(sidebar, text="SUCCESS: 0", font=self.font_main, bg=COLORS["sidebar"], fg=COLORS["success"])
        self.lbl_exitos.pack(anchor="w", padx=30, pady=5)
        self.lbl_errores = tk.Label(sidebar, text="ERRORS:  0", font=self.font_main, bg=COLORS["sidebar"], fg=COLORS["error"])
        self.lbl_errores.pack(anchor="w", padx=30, pady=5)

        # --- CONTENIDO (DERECHA) ---
        content = tk.Frame(body, bg=COLORS["bg"])
        content.pack(side="left", fill="both", expand=True)

        # Engine Control
        ctrl_frame = tk.Frame(content, bg=COLORS["surface"], highlightbackground=COLORS["grid"], highlightthickness=1)
        ctrl_frame.pack(fill="x", pady=(0, 20))
        
        self.btn_start = tk.Button(ctrl_frame, text="[ START ENGINE ]", font=self.font_bold, bg=COLORS["surface"], fg=COLORS["success"], 
                                 activebackground=COLORS["grid"], activeforeground=COLORS["success"], bd=0, cursor="hand2", 
                                 padx=20, pady=15, command=self.start_bot)
        self.btn_start.pack(side="left", expand=True, fill="x")
        
        self.btn_stop = tk.Button(ctrl_frame, text="[ KILL PROCESS ]", font=self.font_bold, bg=COLORS["surface"], fg=COLORS["error"], 
                                activebackground=COLORS["grid"], activeforeground=COLORS["error"], bd=0, cursor="hand2", 
                                padx=20, pady=15, command=self.stop_bot, state="disabled")
        self.btn_stop.pack(side="left", expand=True, fill="x")

        # Config Links
        cfg_frame = tk.Frame(content, bg=COLORS["bg"])
        cfg_frame.pack(fill="x", pady=10)
        
        self.create_link(cfg_frame, "Adjust Regions", self.run_setup)
        self.create_link(cfg_frame, "View Snapshots", self.open_screenshots)
        self.create_link(cfg_frame, "Export Logs", self.open_logs)

        # Live Terminal
        tk.Label(content, text="󰞷 LIVE NEURAL STREAM", font=self.font_small, bg=COLORS["bg"], fg=COLORS["warning"]).pack(anchor="w", pady=(10, 5))
        
        term_f = tk.Frame(content, bg=COLORS["sidebar"], highlightbackground=COLORS["grid"], highlightthickness=1)
        term_f.pack(fill="both", expand=True)
        
        self.terminal = scrolledtext.ScrolledText(term_f, bg=COLORS["sidebar"], fg=COLORS["text"], font=("Consolas", 10), 
                                                borderwidth=0, highlightthickness=0, padx=10, pady=10, insertbackground=COLORS["text"])
        self.terminal.pack(fill="both", expand=True)
        self.terminal.config(state="disabled")

        # Footer
        footer = tk.Frame(self.main_frame, bg=COLORS["bg"])
        footer.pack(fill="x", side="bottom", padx=20, pady=10)
        tk.Label(footer, text="COORD: 34.0522° N, 118.2437° W // RSA-4096 // AUTH: ADMIN", font=self.font_small, bg=COLORS["bg"], fg=COLORS["subtext"]).pack(side="left")
        tk.Label(footer, text="VERSION 1.0.0.0 // © GEMINI CORE", font=self.font_small, bg=COLORS["bg"], fg=COLORS["subtext"]).pack(side="right")

    def add_monitor(self, parent, name, value):
        f = tk.Frame(parent, bg=COLORS["sidebar"], padx=20, pady=5)
        f.pack(fill="x")
        tk.Label(f, text=name, font=self.font_small, bg=COLORS["sidebar"], fg=COLORS["text"]).pack(side="left")
        tk.Label(f, text=f"{int(value*100)}%", font=self.font_small, bg=COLORS["sidebar"], fg=COLORS["accent"]).pack(side="right")
        
        bar_bg = tk.Frame(parent, bg=COLORS["grid"], height=4)
        bar_bg.pack(fill="x", padx=20, pady=(0, 10))
        tk.Frame(bar_bg, bg=COLORS["accent"], width=int(200 * value), height=4).place(x=0, y=0)

    def create_link(self, parent, text, cmd):
        btn = tk.Button(parent, text=f"󱔖 {text}", font=self.font_small, bg=COLORS["bg"], fg=COLORS["accent"], 
                       activebackground=COLORS["bg"], activeforeground=COLORS["text"], bd=0, cursor="hand2", command=cmd)
        btn.pack(side="left", padx=10)

    def setup_dragging(self):
        def start_move(e): self.x = e.x; self.y = e.y
        def stop_move(e): self.x = None; self.y = None
        def on_motion(e):
            deltax = e.x - self.x
            deltay = e.y - self.y
            x = self.root.winfo_x() + deltax
            y = self.root.winfo_y() + deltay
            self.root.geometry(f"+{x}+{y}")
        self.main_frame.bind("<Button-1>", start_move)
        self.main_frame.bind("<B1-Motion>", on_motion)

    def update_loop(self):
        # Update Uptime
        now = datetime.now().strftime("%H:%M:%S")
        self.uptime_label.config(text=f"UPTIME: {now}\nSTATION_ADMIN_01")
        
        # Check Logs
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self.terminal.config(state="normal")
                self.terminal.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] > {msg}\n")
                
                if "error" in msg.lower() or "falló" in msg.lower():
                    self.errores += 1
                    self.lbl_errores.config(text=f"ERRORS:  {self.errores}")
                elif "exitoso" in msg.lower() or "completado" in msg.lower():
                    self.exitos += 1
                    self.lbl_exitos.config(text=f"SUCCESS: {self.exitos}")
                
                self.terminal.see(tk.END)
                self.terminal.config(state="disabled")
        except queue.Empty: pass
        
        self.root.after(100, self.update_loop)

    def start_bot(self):
        self.stop_event.clear()
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.log_queue.put("Initializing Neural Interface...")
        threading.Thread(target=self.worker, daemon=True).start()

    def stop_bot(self):
        self.stop_event.set()
        self.log_queue.put("Shutting down engine...")

    def worker(self):
        try:
            run_bot(log_callback=lambda m: self.log_queue.put(m), stop_event=self.stop_event)
        except Exception as e:
            self.log_queue.put(f"CRITICAL ERROR: {str(e)}")
        finally:
            self.btn_start.config(state="normal")
            self.btn_stop.config(state="disabled")

    def run_setup(self): AreaSelector().run()
    def open_screenshots(self): 
        p = os.path.join("logs", "capturas")
        if os.path.exists(p): os.startfile(p)
    def open_logs(self):
        f = f"registro_{datetime.now().strftime('%Y-%m-%d')}.txt"
        if os.path.exists(f): os.startfile(f)

if __name__ == "__main__":
    root = tk.Tk()
    app = BotAXRegistroGui(root)
    # Centrar ventana
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    root.mainloop()
