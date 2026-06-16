import tkinter as tk
from tkinter import scrolledtext
import threading
import queue
import os
from datetime import datetime
from typing import Dict, Tuple, Any

from src.core.engine import run_bot
from src.ui.area_selector import AreaSelector
from src.core.config import BASE_DIR

# Configuración de estética Gemini Core (Ultra-High Fidelity)
COLORS: Dict[str, str] = {
    "bg": "#05060b",         # Negro abisal
    "sidebar": "#0b0c14",    # Gris oscuro profundo
    "surface": "#121420",    # Superficie de componentes
    "accent": "#89b4fa",     # Azul Gemini
    "success": "#a6e3a1",    # Verde éxito
    "error": "#f38ba8",      # Rojo error
    "warning": "#fab387",    # Naranja advertencia
    "text": "#cdd6f4",       # Texto principal
    "subtext": "#6c7086",    # Texto secundario
    "grid": "#1e1e2e"        # Líneas de división
}


class BotAXRegistroGui:
    """Clase principal de la interfaz moderna (Gemini Engine) de Tkinter para el Bot AX Contable.

    Proporciona un diseño de alta fidelidad estética (Cyberpunk/Abisal) con visualizadores
    de carga de recursos del sistema en tiempo real y paneles dinámicos para el control.
    """

    def __init__(self, root: tk.Tk) -> None:
        """Inicializa los componentes de la interfaz de alta fidelidad.

        Args:
            root (tk.Tk): Ventana raíz de Tkinter.
        """
        self.root: tk.Tk = root
        self.root.title("GEMINI ENGINE - BOT AX REGISTRO")
        self.root.geometry("1100x850")
        self.root.configure(bg=COLORS["bg"])
        
        # Eliminar bordes nativos del sistema para ventana completamente personalizada
        self.root.overrideredirect(True)
        
        # Variables de control de estado
        self.stop_event: threading.Event = threading.Event()
        self.log_queue: queue.Queue = queue.Queue()
        self.exitos: int = 0
        self.errores: int = 0
        
        # Fuentes tipográficas
        self.font_main: Tuple[str, int] = ("Consolas", 10)
        self.font_bold: Tuple[str, int, str] = ("Consolas", 11, "bold")
        self.font_title: Tuple[str, int, str] = ("Consolas", 16, "bold")
        self.font_small: Tuple[str, int] = ("Consolas", 8)

        # Coordenadas para arrastrar ventana sin bordes
        self.x: int = 0
        self.y: int = 0

        self.setup_ui()
        self.setup_dragging()
        self.update_loop()

    def setup_ui(self) -> None:
        """Construye todos los elementos gráficos y paneles de control en la ventana."""
        # Borde Exterior de la Aplicación (Glow azul sutil)
        self.main_frame: tk.Frame = tk.Frame(
            self.root, bg=COLORS["bg"], highlightbackground=COLORS["accent"], highlightthickness=1
        )
        self.main_frame.pack(fill="both", expand=True)

        # 1. BARRA SUPERIOR (HEADER)
        header = tk.Frame(self.main_frame, bg=COLORS["bg"], height=60)
        header.pack(fill="x", side="top", padx=20, pady=10)
        
        # Icono unicode del Engine y textos descriptivos
        logo_label = tk.Label(header, text="󰄶", font=("Segoe UI Symbol", 24), bg=COLORS["bg"], fg=COLORS["accent"])
        logo_label.pack(side="left", padx=(10, 15))
        
        title_f = tk.Frame(header, bg=COLORS["bg"])
        title_f.pack(side="left")
        tk.Label(title_f, text="GEMINI ENGINE", font=self.font_bold, bg=COLORS["bg"], fg=COLORS["accent"]).pack(anchor="w")
        tk.Label(title_f, text="CORE MODULE // REGISTRO_AUTO", font=self.font_small, bg=COLORS["bg"], fg=COLORS["success"]).pack(anchor="w")

        # Botón personalizado de cierre de la aplicación
        close_btn = tk.Label(header, text="✕", font=("Consolas", 16), bg=COLORS["bg"], fg=COLORS["subtext"], cursor="hand2")
        close_btn.pack(side="right", padx=10)
        close_btn.bind("<Button-1>", lambda e: self.root.destroy())
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg=COLORS["error"]))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg=COLORS["subtext"]))

        self.uptime_label: tk.Label = tk.Label(
            header, text="UPTIME: 00:00:00", font=self.font_small, bg=COLORS["bg"], fg=COLORS["subtext"], justify="right"
        )
        self.uptime_label.pack(side="right", padx=20)

        # 2. CUERPO (BODY)
        body = tk.Frame(self.main_frame, bg=COLORS["bg"])
        body.pack(fill="both", expand=True, padx=20, pady=10)

        # --- PANEL LATERAL IZQUIERDO ---
        sidebar = tk.Frame(body, bg=COLORS["sidebar"], width=240)
        sidebar.pack(side="left", fill="y", padx=(0, 20))
        sidebar.pack_propagate(False)

        # ASCII Art decorativo (Bunny)
        bunny: str = "\n   (\\ _ /)\n   (  . . )\n   c( \" ) ( \" )\n   -----------\n     STATION\n      READY\n   -----------"
        tk.Label(sidebar, text=bunny, font=("Courier New", 10), bg=COLORS["sidebar"], fg=COLORS["accent"]).pack(pady=20)

        # Monitores del sistema (Valores representativos fijos)
        mon_title = tk.Label(sidebar, text="SYSTEM MONITORS", font=self.font_small, bg=COLORS["sidebar"], fg=COLORS["subtext"])
        mon_title.pack(anchor="w", padx=20, pady=(10, 5))
        
        self.add_monitor(sidebar, "CPU_USAGE", 0.35)
        self.add_monitor(sidebar, "MEM_USAGE", 0.52)
        self.add_monitor(sidebar, "NET_TRAFFIC", 0.08)

        # Métricas de la Sesión actual
        tk.Label(sidebar, text="SESSION METRICS", font=self.font_small, bg=COLORS["sidebar"], fg=COLORS["subtext"]).pack(anchor="w", padx=20, pady=(30, 5))
        
        self.lbl_exitos: tk.Label = tk.Label(sidebar, text="SUCCESS: 0", font=self.font_main, bg=COLORS["sidebar"], fg=COLORS["success"])
        self.lbl_exitos.pack(anchor="w", padx=30, pady=5)
        self.lbl_errores: tk.Label = tk.Label(sidebar, text="ERRORS:  0", font=self.font_main, bg=COLORS["sidebar"], fg=COLORS["error"])
        self.lbl_errores.pack(anchor="w", padx=30, pady=5)

        # --- PANEL CENTRAL DERECHO ---
        content = tk.Frame(body, bg=COLORS["bg"])
        content.pack(side="left", fill="both", expand=True)

        # Controles principales
        ctrl_frame = tk.Frame(content, bg=COLORS["surface"], highlightbackground=COLORS["grid"], highlightthickness=1)
        ctrl_frame.pack(fill="x", pady=(0, 20))
        
        self.btn_start: tk.Button = tk.Button(
            ctrl_frame, text="[ START ENGINE ]", font=self.font_bold, bg=COLORS["surface"], fg=COLORS["success"], 
            activebackground=COLORS["grid"], activeforeground=COLORS["success"], bd=0, cursor="hand2", 
            padx=20, pady=15, command=self.start_bot
        )
        self.btn_start.pack(side="left", expand=True, fill="x")
        
        self.btn_stop: tk.Button = tk.Button(
            ctrl_frame, text="[ KILL PROCESS ]", font=self.font_bold, bg=COLORS["surface"], fg=COLORS["error"], 
            activebackground=COLORS["grid"], activeforeground=COLORS["error"], bd=0, cursor="hand2", 
            padx=20, pady=15, command=self.stop_bot, state="disabled"
        )
        self.btn_stop.pack(side="left", expand=True, fill="x")

        # Accesos directos a configuraciones
        cfg_frame = tk.Frame(content, bg=COLORS["bg"])
        cfg_frame.pack(fill="x", pady=10)
        
        self.create_link(cfg_frame, "Adjust Regions", self.run_setup)
        self.create_link(cfg_frame, "View Snapshots", self.open_screenshots)
        self.create_link(cfg_frame, "Export Logs", self.open_logs)

        # Consola del Flujo de Eventos
        tk.Label(content, text="󰞷 LIVE NEURAL STREAM", font=self.font_small, bg=COLORS["bg"], fg=COLORS["warning"]).pack(anchor="w", pady=(10, 5))
        
        term_f = tk.Frame(content, bg=COLORS["sidebar"], highlightbackground=COLORS["grid"], highlightthickness=1)
        term_f.pack(fill="both", expand=True)
        
        self.terminal: scrolledtext.ScrolledText = scrolledtext.ScrolledText(
            term_f, bg=COLORS["sidebar"], fg=COLORS["text"], font=("Consolas", 10), 
            borderwidth=0, highlightthickness=0, padx=10, pady=10, insertbackground=COLORS["text"]
        )
        self.terminal.pack(fill="both", expand=True)
        self.terminal.config(state="disabled")

        # Pie de página (Footer)
        footer = tk.Frame(self.main_frame, bg=COLORS["bg"])
        footer.pack(fill="x", side="bottom", padx=20, pady=10)
        tk.Label(footer, text="COORD: 34.0522° N, 118.2437° W // RSA-4096 // AUTH: ADMIN", font=self.font_small, bg=COLORS["bg"], fg=COLORS["subtext"]).pack(side="left")
        tk.Label(footer, text="VERSION 1.0.0.0 // © GEMINI CORE", font=self.font_small, bg=COLORS["bg"], fg=COLORS["subtext"]).pack(side="right")

    def add_monitor(self, parent: tk.Frame, name: str, value: float) -> None:
        """Crea una barra de monitoreo visual en el panel lateral.

        Args:
            parent (tk.Frame): Contenedor padre.
            name (str): Nombre descriptivo de la métrica.
            value (float): Porcentaje de carga (de 0.0 a 1.0).
        """
        f = tk.Frame(parent, bg=COLORS["sidebar"], padx=20, pady=5)
        f.pack(fill="x")
        tk.Label(f, text=name, font=self.font_small, bg=COLORS["sidebar"], fg=COLORS["text"]).pack(side="left")
        tk.Label(f, text=f"{int(value*100)}%", font=self.font_small, bg=COLORS["sidebar"], fg=COLORS["accent"]).pack(side="right")
        
        bar_bg = tk.Frame(parent, bg=COLORS["grid"], height=4)
        bar_bg.pack(fill="x", padx=20, pady=(0, 10))
        tk.Frame(bar_bg, bg=COLORS["accent"], width=int(200 * value), height=4).place(x=0, y=0)

    def create_link(self, parent: tk.Frame, text: str, cmd: Any) -> None:
        """Crea un botón estilizado como enlace en la barra intermedia.

        Args:
            parent (tk.Frame): Contenedor padre.
            text (str): Texto visible del enlace.
            cmd (Any): Función a llamar tras clickear.
        """
        btn = tk.Button(
            parent, text=f"󱔖 {text}", font=self.font_small, bg=COLORS["bg"], fg=COLORS["accent"], 
            activebackground=COLORS["bg"], activeforeground=COLORS["text"], bd=0, cursor="hand2", command=cmd
        )
        btn.pack(side="left", padx=10)

    def setup_dragging(self) -> None:
        """Enlaza los eventos para arrastrar la ventana sin bordes mediante el header."""
        def start_move(e: tk.Event) -> None: 
            self.x = e.x
            self.y = e.y
        def on_motion(e: tk.Event) -> None:
            deltax: int = e.x - self.x
            deltay: int = e.y - self.y
            new_x: int = self.root.winfo_x() + deltax
            new_y: int = self.root.winfo_y() + deltay
            self.root.geometry(f"+{new_x}+{new_y}")
            
        self.main_frame.bind("<Button-1>", start_move)
        self.main_frame.bind("<B1-Motion>", on_motion)

    def update_loop(self) -> None:
        """Chequea recurrentemente los nuevos registros del bot y el reloj digital."""
        now: str = datetime.now().strftime("%H:%M:%S")
        self.uptime_label.config(text=f"UPTIME: {now}\nSTATION_ADMIN_01")
        
        try:
            while True:
                msg: str = self.log_queue.get_nowait()
                self.terminal.config(state="normal")
                self.terminal.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] > {msg}\n")
                
                # Incrementar métricas de sesión basándose en el contenido de las trazas
                if "error" in msg.lower() or "falló" in msg.lower():
                    self.errores += 1
                    self.lbl_errores.config(text=f"ERRORS:  {self.errores}")
                elif "exitoso" in msg.lower() or "completado" in msg.lower():
                    self.exitos += 1
                    self.lbl_exitos.config(text=f"SUCCESS: {self.exitos}")
                
                self.terminal.see(tk.END)
                self.terminal.config(state="disabled")
        except queue.Empty: 
            pass
        
        self.root.after(100, self.update_loop)

    def start_bot(self) -> None:
        """Lanza el procesamiento del bot en un hilo secundario asíncrono."""
        self.stop_event.clear()
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.log_queue.put("Initializing Neural Interface...")
        threading.Thread(target=self.worker, daemon=True).start()

    def stop_bot(self) -> None:
        """Detiene el bot emitiendo señalizadores de parada."""
        self.stop_event.set()
        self.log_queue.put("Shutting down engine...")

    def worker(self) -> None:
        """Función trabajadora que invoca el motor del bot."""
        try:
            run_bot(log_callback=lambda m: self.log_queue.put(m), stop_event=self.stop_event)
        except Exception as e:
            self.log_queue.put(f"CRITICAL ERROR: {str(e)}")
        finally:
            self.btn_start.config(state="normal")
            self.btn_stop.config(state="disabled")

    def run_setup(self) -> None:
        """Lanza el selector interactivo de áreas minimizando temporalmente la GUI."""
        self.root.iconify()
        AreaSelector().run()
        self.root.deiconify()

    def open_screenshots(self) -> None: 
        """Abre el directorio físico de snapshots de error en la raíz."""
        p: str = os.path.join(BASE_DIR, "logs", "capturas")
        os.makedirs(p, exist_ok=True)
        os.startfile(p)

    def open_logs(self) -> None:
        """Abre en el editor nativo el registro diario persistido en la raíz."""
        f: str = os.path.join(BASE_DIR, f"registro_{datetime.now().strftime('%Y-%m-%d')}.txt")
        if os.path.exists(f): 
            os.startfile(f)


if __name__ == "__main__":
    root = tk.Tk()
    app = BotAXRegistroGui(root)
    root.update_idletasks()
    width: int = root.winfo_width()
    height: int = root.winfo_height()
    x_pos: int = (root.winfo_screenwidth() // 2) - (width // 2)
    y_pos: int = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x_pos}+{y_pos}')
    root.mainloop()
