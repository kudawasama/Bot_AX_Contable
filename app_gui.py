import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
import threading
import queue
import sys
import os
from datetime import datetime

# Importaciones locales del Bot
from bot_main import run_bot
from setup_areas import AreaSelector
from license_manager import check_license, get_hwid, generate_key
from path_utils import get_external_path, get_resource_path
from shortcut_manager import create_desktop_shortcut
from updater_manager import check_for_updates, apply_update

class QueueLogger:
    """Clase para redirigir el stdout/stderr a la cola de logs de la GUI."""
    def __init__(self, log_queue):
        self.log_queue = log_queue
    def write(self, message):
        if message.strip():
            self.log_queue.put(message.strip())
    def flush(self): pass

class BotAXGui:
    """Interfaz principal del Bot AX Contable."""
    def __init__(self, root):
        self.root = root
        self.root.title("Bot AX Contable v1.00.00")
        
        # Paleta de colores Catppuccin Mocha
        self.bg_color = "#1e1e2e"    # Fondo
        self.fg_color = "#cdd6f4"    # Texto
        self.pink = "#f5c2e7"
        self.peach = "#fab387"
        self.blue = "#89b4fa"
        self.green = "#a6e3a1"
        self.red = "#f38ba8"
        self.teal = "#94e2d5"
        self.yellow = "#f9e2af"
        self.mauve = "#cba6f7"
        self.overlay0 = "#6c7086"
        self.surface0 = "#313244"
        self.sky = "#89dceb"
        
        self.root.configure(bg=self.bg_color)
        
        self.bot_thread = None
        self.stop_event = threading.Event()
        self.log_queue = queue.Queue()
        self.diarios_exitosos = 0
        self.diarios_errores = 0
        
        # Redireccionamiento de salida a la terminal de la GUI
        sys.stdout = QueueLogger(self.log_queue)
        sys.stderr = sys.stdout
        
        self.setup_ui()
        self.check_queue()
        
        # Tareas automáticas iniciales: Acceso directo y Actualizaciones
        self.root.after(1000, self.initial_background_tasks)

    def initial_background_tasks(self):
        """Ejecuta tareas de fondo al iniciar la aplicación."""
        # Crear acceso directo si no existe
        create_desktop_shortcut()
        
        # Buscar actualizaciones discretamente
        threading.Thread(target=self.check_updates_silent, daemon=True).start()

    def check_updates_silent(self):
        """Busca actualizaciones sin bloquear la interfaz."""
        try:
            update_available, remote_version, download_url = check_for_updates()
            if update_available:
                self.root.after(0, lambda: self.prompt_update(remote_version, download_url))
        except Exception: pass

    def prompt_update(self, version, url):
        """Pregunta al usuario si desea actualizar."""
        if messagebox.askyesno("Actualización Disponible", 
                               f"Una nueva versión ({version}) está disponible.\n¿Deseas descargarla y actualizar ahora?"):
            self.log(f"Iniciando actualización a v{version}...")
            if not apply_update(url):
                messagebox.showerror("Error", "No se pudo descargar la actualización.")

    def setup_ui(self):
        """Configura los elementos visuales de la interfaz."""
        self.font_mono = ("Consolas", 9)
        self.font_mono_bold = ("Consolas", 10, "bold")
        
        # CONTENEDOR PRINCIPAL
        self.main_container = tk.Frame(self.root, bg=self.bg_color)
        self.main_container.pack(fill="both", expand=True, padx=15, pady=15)

        # --- BARRA SUPERIOR (TOP PILLS) ---
        top_bar = tk.Frame(self.main_container, bg=self.bg_color)
        top_bar.pack(fill="x", pady=(0, 20))
        
        self.add_pill(top_bar, " 󰄶  monnos ", self.pink, self.bg_color)
        self.add_pill(top_bar, " ~ ", self.peach, self.bg_color)
        self.add_pill(top_bar, f" 󰥔  {datetime.now().strftime('%H:%M')} ", self.blue, self.bg_color)
        tk.Label(top_bar, text=" > bot_ax --run", bg=self.bg_color, fg=self.fg_color, font=self.font_mono).pack(side="left", padx=5)

        # --- CUERPO ---
        body = tk.Frame(self.main_container, bg=self.bg_color)
        body.pack(fill="both", expand=True)

        # Mascotita ASCII (Lado Izquierdo)
        left_side = tk.Frame(body, bg=self.bg_color, width=180)
        left_side.pack(side="left", fill="y", padx=(0, 20))
        
        ascii_art = """
   (\\_/)
   ( •.•)
   c(\" )(\" )
   
   -------
    SYSTEM
    READY
   -------
        """
        tk.Label(left_side, text=ascii_art, bg=self.bg_color, fg=self.pink, font=("Courier", 11), justify="center").pack(pady=40)

        # Contenido de Bloques (Lado Derecho)
        right_content = tk.Frame(body, bg=self.bg_color)
        right_content.pack(side="left", fill="both", expand=True)

        # Bloque 1: CONTROLADOR
        ctrl_frame = self.create_styled_box(right_content, " fastfetch - 1.00.00 ", self.red)
        btn_box = tk.Frame(ctrl_frame, bg=self.bg_color)
        btn_box.pack(fill="x", pady=5)
        
        self.btn_start = self.add_action_btn(btn_box, "[ START ENGINE ]", self.green, self.start_bot)
        self.btn_stop = self.add_action_btn(btn_box, "[ KILL PROCESS ]", self.red, self.stop_bot, state="disabled")

        # Bloque 2: CONFIGURACIÓN
        cfg_frame = self.create_styled_box(right_content, " Hardware / Config ", self.teal)
        self.add_info_line(cfg_frame, "Region Setup", "Update coordinates", self.sky, self.run_setup)
        self.add_info_line(cfg_frame, "Visual Logs", "Open screenshots", self.sky, self.open_screenshots)
        self.add_info_line(cfg_frame, "Text Logs", "Review history", self.sky, self.open_logs)

        # Bloque 3: TERMINAL EN VIVO
        term_frame = self.create_styled_box(right_content, " Live Terminal ", self.yellow)
        self.log_widget = scrolledtext.ScrolledText(term_frame, bg=self.bg_color, fg=self.fg_color, font=self.font_mono, 
                                                 borderwidth=0, highlightthickness=0, height=10, insertbackground=self.fg_color)
        self.log_widget.pack(fill="both", expand=True, padx=5, pady=5)
        self.log_widget.config(state="disabled")

        # Bloque 4: ESTADÍSTICAS
        stats_frame = self.create_styled_box(right_content, " Session Stats ", self.mauve)
        self.lbl_exito = tk.Label(stats_frame, text="Journals Success ........ 0", bg=self.bg_color, fg=self.green, font=self.font_mono)
        self.lbl_exito.pack(anchor="w", padx=10)
        self.lbl_error = tk.Label(stats_frame, text="Critical Errors ......... 0", bg=self.bg_color, fg=self.red, font=self.font_mono)
        self.lbl_error.pack(anchor="w", padx=10)

        # Pie de página
        footer = tk.Frame(self.main_container, bg=self.bg_color)
        footer.pack(fill="x", side="bottom", pady=(10, 0))
        tk.Label(footer, text="v1.00.00", bg=self.bg_color, fg=self.overlay0, font=("Consolas", 7)).pack(side="left")
        tk.Label(footer, text="Created by: Cotano_", bg=self.bg_color, fg=self.mauve, font=("Consolas", 7, "italic")).pack(side="left")

    def add_pill(self, parent, text, color, bg):
        p = tk.Label(parent, text=text, bg=color, fg=bg, font=self.font_mono_bold, padx=10, pady=2)
        p.pack(side="left", padx=2)

    def create_styled_box(self, parent, title, color):
        f = tk.LabelFrame(parent, text=title, bg=self.bg_color, fg=color, font=self.font_mono_bold, 
                         labelanchor="n", borderwidth=1, relief="solid", padx=10, pady=5)
        f.pack(fill="x", pady=(0, 10))
        return f

    def add_action_btn(self, parent, text, color, cmd, state="normal"):
        b = tk.Button(parent, text=text, bg=self.bg_color, fg=color, font=self.font_mono_bold, 
                    borderwidth=0, activebackground=self.surface0, activeforeground=color, 
                    cursor="hand2", command=cmd, state=state)
        b.pack(side="left", expand=True)
        return b

    def add_info_line(self, parent, label, value, color, cmd):
        f = tk.Frame(parent, bg=self.bg_color)
        f.pack(fill="x")
        tk.Label(f, text=f"{label:.<15}", bg=self.bg_color, fg=self.fg_color, font=self.font_mono).pack(side="left")
        b = tk.Button(f, text=value, bg=self.bg_color, fg=color, font=self.font_mono, borderwidth=0, 
                     activebackground=self.surface0, activeforeground=color, cursor="hand2", command=cmd)
        b.pack(side="left")

    def log(self, message):
        self.log_queue.put(message)

    def check_queue(self):
        """Revisa la cola de mensajes para actualizar la terminal en la GUI."""
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self.log_widget.config(state="normal")
                ts = datetime.now().strftime("%H:%M:%S")
                indicator = "::"
                if "exitoso" in msg.lower() or "completado" in msg.lower(): indicator = "OK"
                elif "error" in msg.lower() or "timeout" in msg.lower(): indicator = "!!"
                
                self.log_widget.insert(tk.END, f"[{ts}] {indicator} {msg}\n")
                self.log_widget.see(tk.END)
                self.log_widget.config(state="disabled")
                
                if "completado" in msg.lower() or "exitoso" in msg.lower():
                    self.diarios_exitosos += 1
                    self.lbl_exito.config(text=f"Journals Success ........ {self.diarios_exitosos}")
                elif "error" in msg.lower() or "timeout" in msg.lower():
                    if "ignorado" not in msg.lower():
                        self.diarios_errores += 1
                        self.lbl_error.config(text=f"Critical Errors ......... {self.diarios_errores}")
        except queue.Empty: pass
        self.root.after(100, self.check_queue)

    def start_bot(self):
        """Inicia la ejecución del hilo del bot."""
        if self.bot_thread and self.bot_thread.is_alive(): return
        self.stop_event.clear()
        self.log("Encendiendo motores...")
        self.btn_start.config(state="disabled", fg=self.overlay0)
        self.btn_stop.config(state="normal", fg=self.red)
        self.bot_thread = threading.Thread(target=self.run_bot_thread, daemon=True)
        self.bot_thread.start()

    def stop_bot(self):
        """Solicita la detención del bot."""
        self.stop_event.set()
        self.log("Señal SIGKILL enviada al proceso del bot.")
        self.btn_stop.config(state="disabled", fg=self.overlay0)

    def run_bot_thread(self):
        """Ejecuta el bot en un hilo separado."""
        try: run_bot(log_callback=self.log, stop_event=self.stop_event)
        finally:
            self.btn_start.after(0, lambda: self.btn_start.config(state="normal", fg=self.green))
            self.btn_stop.after(0, lambda: self.btn_stop.config(state="disabled", fg=self.overlay0))

    def run_setup(self):
        """Abre el selector de regiones para calibración."""
        if self.bot_thread and self.bot_thread.is_alive(): return
        AreaSelector().run()

    def open_screenshots(self):
        """Abre la carpeta de capturas de error."""
        path = get_external_path(os.path.join("logs", "capturas"))
        if not os.path.exists(path): os.makedirs(path)
        os.startfile(path)

    def open_logs(self):
        """Abre el archivo de log de texto del día actual."""
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        nombre_archivo = get_external_path(f"registro_{fecha_hoy}.txt")
        if os.path.exists(nombre_archivo): os.startfile(nombre_archivo)

def show_activation_window(hwid):
    """Muestra la ventana de activación de licencia."""
    act_root = tk.Tk()
    act_root.title("Activación Requerida - Bot AX Contable")
    act_root.configure(bg="#1e1e2e")
    w, h = 500, 320
    x, y = (act_root.winfo_screenwidth()/2) - (w/2), (act_root.winfo_screenheight()/2) - (h/2)
    act_root.geometry('%dx%d+%d+%d' % (w, h, x, y))
    act_root.resizable(False, False)

    tk.Label(act_root, text="SISTEMA BLOQUEADO", bg="#1e1e2e", fg="#f38ba8", font=("Consolas", 14, "bold")).pack(pady=20)
    
    tk.Label(act_root, text=f"Tu ID de Hardware (HWID):", bg="#1e1e2e", fg="#cdd6f4", font=("Consolas", 10)).pack()
    hwid_entry = tk.Entry(act_root, bg="#313244", fg="#a6e3a1", font=("Consolas", 10), justify="center", width=40)
    hwid_entry.insert(0, hwid)
    hwid_entry.config(state="readonly")
    hwid_entry.pack(pady=5)
    
    tk.Label(act_root, text="Ingresa tu Llave de Activación:", bg="#1e1e2e", fg="#cdd6f4", font=("Consolas", 10)).pack(pady=(15, 5))
    key_entry = tk.Entry(act_root, bg="#313244", fg="#cdd6f4", font=("Consolas", 11), justify="center", width=40)
    key_entry.pack(pady=5)
    key_entry.focus_set()

    def try_activate():
        key = key_entry.get().strip()
        if key == generate_key(hwid):
            ruta_llave = get_external_path("license.key")
            with open(ruta_llave, "w") as f:
                f.write(key)
            messagebox.showinfo("Activación Exitosa", "¡Bot activado! Ya puedes usar la aplicación.")
            act_root.destroy()
        else:
            messagebox.showerror("Error", "Llave inválida. Contacta con soporte.")

    tk.Button(act_root, text="[ ACTIVAR AHORA ]", bg="#313244", fg="#a6e3a1", font=("Consolas", 10, "bold"), 
              command=try_activate, borderwidth=0, padx=20, pady=10).pack(pady=20)

    act_root.mainloop()

if __name__ == "__main__":
    # Verificación de licencia antes de arrancar la GUI principal
    valida, hwid_actual = check_license()
    if not valida:
        show_activation_window(hwid_actual)
        # Re-verificar después de cerrar la ventana de activación
        valida, _ = check_license()
        if not valida: sys.exit(0)

    root = tk.Tk()
    w, h = 950, 750
    x, y = (root.winfo_screenwidth()/2) - (w/2), (root.winfo_screenheight()/2) - (h/2)
    root.geometry('%dx%d+%d+%d' % (w, h, x, y))
    app = BotAXGui(root)
    root.mainloop()
