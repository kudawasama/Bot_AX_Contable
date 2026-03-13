import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
import threading
import queue
import os
import sys
import subprocess
from bot_main import run_bot
from setup_areas import AreaSelector

class QueueLogger:
    """Redirects stdout/stderr to the log queue."""
    def __init__(self, queue):
        self.queue = queue
    def write(self, message):
        if message.strip():
            self.queue.put(message.strip())
    def flush(self):
        pass

class BotAXGui:
    def __init__(self, root):
        self.root = root
        self.root.title("Bot AX Contable v2.0")
        self.root.geometry("800x600")
        self.root.configure(bg="#2c3e50")
        
        # Variables de estado
        self.bot_thread = None
        self.stop_event = threading.Event()
        self.log_queue = queue.Queue()
        self.diarios_exitosos = 0
        self.diarios_errores = 0
        
        # Redireccionar salida estándar a la cola de logs
        self.stdout_redirector = QueueLogger(self.log_queue)
        sys.stdout = self.stdout_redirector
        sys.stderr = self.stdout_redirector
        
        self.setup_ui()
        self.check_queue()

    def setup_ui(self):
        # Estilo
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", padding=6, relief="flat", background="#34495e", foreground="white")
        style.map("TButton", background=[('active', '#1abc9c')])

        # Header
        header = tk.Frame(self.root, bg="#1abc9c", height=60)
        header.pack(fill="x")
        tk.Label(header, text="BOT AX CONTABLE", bg="#1abc9c", fg="white", font=("Helvetica", 18, "bold")).pack(pady=10)

        # Panel Principal
        main_frame = tk.Frame(self.root, bg="#2c3e50")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Columna Izquierda: Controles y Stats
        left_panel = tk.Frame(main_frame, bg="#2c3e50", width=250)
        left_panel.pack(side="left", fill="y", padx=(0, 20))

        # Botones
        tk.Label(left_panel, text="Panel de Control", bg="#2c3e50", fg="#ecf0f1", font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(0, 10))
        
        self.btn_start = tk.Button(left_panel, text="▶ INICIAR BOT", bg="#27ae60", fg="white", font=("Helvetica", 10, "bold"), command=self.start_bot, height=2, width=20)
        self.btn_start.pack(pady=5)

        self.btn_stop = tk.Button(left_panel, text="■ DETENER (ESC)", bg="#c0392b", fg="white", font=("Helvetica", 10, "bold"), command=self.stop_bot, height=2, width=20, state="disabled")
        self.btn_stop.pack(pady=5)

        tk.Button(left_panel, text="⚙ Configurar Sectores", bg="#2980b9", fg="white", command=self.run_setup, width=20).pack(pady=(20, 5))
        tk.Button(left_panel, text="📷 Ver Capturas", bg="#8e44ad", fg="white", command=self.open_screenshots, width=20).pack(pady=5)
        tk.Button(left_panel, text="📄 Ver Logs TXT", bg="#7f8c8d", fg="white", command=self.open_logs, width=20).pack(pady=5)

        # Estadísticas
        tk.Frame(left_panel, height=2, bg="#34495e").pack(fill="x", pady=20)
        tk.Label(left_panel, text="Estadísticas Hoy", bg="#2c3e50", fg="#ecf0f1", font=("Helvetica", 12, "bold")).pack(anchor="w")
        
        self.lbl_exito = tk.Label(left_panel, text="Exitosos: 0", bg="#2c3e50", fg="#2ecc71", font=("Helvetica", 11))
        self.lbl_exito.pack(anchor="w", pady=5)
        
        self.lbl_error = tk.Label(left_panel, text="Errores: 0", bg="#2c3e50", fg="#e74c3c", font=("Helvetica", 11))
        self.lbl_error.pack(anchor="w", pady=5)

        # Columna Derecha: Log Monitor
        right_panel = tk.Frame(main_frame, bg="#2c3e50")
        right_panel.pack(side="right", fill="both", expand=True)

        tk.Label(right_panel, text="Consola de Eventos", bg="#2c3e50", fg="#ecf0f1", font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(0, 10))
        self.log_widget = scrolledtext.ScrolledText(right_panel, bg="#1e272e", fg="#d2dae2", font=("Consolas", 10), state="disabled")
        self.log_widget.pack(fill="both", expand=True)

    def log(self, message):
        self.log_queue.put(message)

    def check_queue(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self.log_widget.config(state="normal")
                self.log_widget.insert(tk.END, msg + "\n")
                self.log_widget.see(tk.END)
                self.log_widget.config(state="disabled")
                
                # Actualizar contadores si detectamos palabras clave
                if "completado" in msg.lower() or "exitoso" in msg.lower():
                    self.diarios_exitosos += 1
                    self.lbl_exito.config(text=f"Exitosos: {self.diarios_exitosos}")
                elif "error" in msg.lower() or "timeout" in msg.lower():
                    if "ignorado" not in msg.lower(): # No contar como error si solo ignoramos de lista negra
                        self.diarios_errores += 1
                        self.lbl_error.config(text=f"Errores: {self.diarios_errores}")
                
        except queue.Empty:
            pass
        self.root.after(100, self.check_queue)

    def start_bot(self):
        if self.bot_thread and self.bot_thread.is_alive():
            return
            
        self.stop_event.clear()
        self.log("--- INICIANDO SISTEMA ---")
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        
        self.bot_thread = threading.Thread(target=self.run_bot_thread, daemon=True)
        self.bot_thread.start()

    def stop_bot(self):
        self.stop_event.set()
        self.log("Solicitando detención...")
        self.btn_stop.config(state="disabled")

    def run_bot_thread(self):
        try:
            run_bot(log_callback=self.log, stop_event=self.stop_event)
        finally:
            self.btn_start.after(0, lambda: self.btn_start.config(state="normal"))
            self.btn_stop.after(0, lambda: self.btn_stop.config(state="disabled"))

    def run_setup(self):
        if self.bot_thread and self.bot_thread.is_alive():
            messagebox.showwarning("Aviso", "Detén el bot antes de configurar sectores.")
            return
        
        messagebox.showinfo("Instrucciones", "El selector se abrirá. Selecciona los 3 sectores (A, B y C) con el mouse.")
        def launch_setup():
            try:
                # Usar la clase AreaSelector de setup_areas
                app = AreaSelector()
                app.run()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir el selector: {e}")
        
        # Ejecutar en hilo separado para no bloquear la UI si es necesario, 
        # aunque Tkinter sobre Tkinter puede ser complejo.
        launch_setup()

    def open_screenshots(self):
        path = os.path.join("logs", "capturas")
        if not os.path.exists(path):
            os.makedirs(path)
        os.startfile(path)

    def open_logs(self):
        # Abrir el log más reciente (hoy)
        from datetime import datetime
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        nombre_archivo = f"registro_{fecha_hoy}.txt"
        if os.path.exists(nombre_archivo):
            os.startfile(nombre_archivo)
        else:
            messagebox.showinfo("INFO", "No hay registros creados hoy todavía.")

if __name__ == "__main__":
    root = tk.Tk()
    app = BotAXGui(root)
    root.mainloop()
