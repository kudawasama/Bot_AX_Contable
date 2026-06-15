import tkinter as tk
from tkinter import scrolledtext, font
from tkinter import ttk
import threading
import queue
import sys
import os
from datetime import datetime
from bot_main import run_bot
from setup_areas import AreaSelector

class QueueLogger:
    def __init__(self, log_queue):
        self.log_queue = log_queue
    def write(self, message):
        if message.strip():
            self.log_queue.put(message.strip())
    def flush(self): pass

class BotAXGui:
    def __init__(self, root):
        self.root = root
        self.root.title("Bot AX Contable — v1.00.00")
        
        # Paleta moderna y corporativa
        self.bg_color = "#0f1720"    # Fondo profundo
        self.panel = "#0b1220"
        self.card = "#0f1728"
        self.fg_color = "#e6eef8"    # Texto claro
        self.accent = "#2dd4bf"      # acento teal
        self.warn = "#f59e0b"        # amarillo
        self.danger = "#ef4444"
        self.muted = "#94a3b8"
        
        self.root.configure(bg=self.bg_color)
        
        self.bot_thread = None
        self.stop_event = threading.Event()
        self.log_queue = queue.Queue()
        self.diarios_exitosos = 0
        self.diarios_errores = 0
        
        sys.stdout = QueueLogger(self.log_queue)
        sys.stderr = sys.stdout
        
        self.setup_styles()
        self.setup_ui()
        self.check_queue()

    def setup_styles(self):
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass
        style.configure('TFrame', background=self.bg_color)
        style.configure('Card.TFrame', background=self.card, relief='flat')
        style.configure('Header.TLabel', background=self.bg_color, foreground=self.fg_color, font=('Segoe UI', 14, 'bold'))
        style.configure('Sub.TLabel', background=self.bg_color, foreground=self.muted, font=('Segoe UI', 9))
        style.configure('Accent.TButton', background=self.accent, foreground=self.bg_color, font=('Segoe UI', 10, 'bold'))
        style.map('Accent.TButton', background=[('active', self.accent)])
        style.configure('Danger.TButton', background=self.danger, foreground='white')
        style.configure('Stat.TLabel', background=self.card, foreground=self.fg_color, font=('Segoe UI', 11, 'bold'))

    def setup_ui(self):
        self.font_mono = ("Consolas", 10)
        self.font_ui = ('Segoe UI', 10)

        # CONTENEDOR PRINCIPAL
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill="both", expand=True, padx=18, pady=18)

        # Layout: Header, body (sidebar + content), footer

        # --- HEADER ---
        header = ttk.Frame(self.main_container)
        header.pack(fill='x', pady=(0, 14))
        ttk.Label(header, text='Bot AX Contable', style='Header.TLabel').pack(side='left')
        ttk.Label(header, text='v1.00.00', style='Sub.TLabel').pack(side='left', padx=(8,0))
        ttk.Label(header, text=f'  •  {datetime.now().strftime("%Y-%m-%d %H:%M")}', style='Sub.TLabel').pack(side='left', padx=8)
        
        # Right controls (start/stop)
        ctrl_right = ttk.Frame(header)
        ctrl_right.pack(side='right')
        self.btn_start = ttk.Button(ctrl_right, text='START ENGINE', style='Accent.TButton', command=self.start_bot)
        self.btn_start.pack(side='left', padx=6)
        self.btn_stop = ttk.Button(ctrl_right, text='STOP', style='Danger.TButton', command=self.stop_bot)
        self.btn_stop.pack(side='left')
        self.btn_stop.state(['disabled'])

        # --- BODY ---
        body = ttk.Frame(self.main_container)
        body.pack(fill='both', expand=True)

        # Sidebar
        sidebar = ttk.Frame(body, width=220, style='TFrame')
        sidebar.pack(side='left', fill='y', padx=(0,12))
        ttk.Label(sidebar, text='Navegación', style='Sub.TLabel').pack(anchor='nw', pady=(2,8))
        ttk.Button(sidebar, text='Estado', command=lambda: None).pack(fill='x', pady=4)
        ttk.Button(sidebar, text='Registro / Logs', command=lambda: None).pack(fill='x', pady=4)
        ttk.Button(sidebar, text='Configuración', command=lambda: None).pack(fill='x', pady=4)
        ttk.Separator(sidebar, orient='horizontal').pack(fill='x', pady=8)
        ttk.Button(sidebar, text='Abrir capturas', command=self.open_screenshots).pack(fill='x', pady=2)
        ttk.Button(sidebar, text='Revisar logs', command=self.open_logs).pack(fill='x', pady=2)

        # Content area
        right_content = ttk.Frame(body)
        right_content.pack(side='left', fill='both', expand=True)

        # Top cards: stats and controls
        cards = ttk.Frame(right_content)
        cards.pack(fill='x', pady=(0,10))

        stat_frame = ttk.Frame(cards, style='Card.TFrame')
        stat_frame.pack(side='left', fill='both', expand=True, padx=(0,8))
        ttk.Label(stat_frame, text='Uptime', style='Stat.TLabel').pack(anchor='w', padx=12, pady=(8,2))
        self.uptime_label = ttk.Label(stat_frame, text='00:00:00', style='Sub.TLabel')
        self.uptime_label.pack(anchor='w', padx=12, pady=(0,8))

        actions_frame = ttk.Frame(cards)
        actions_frame.pack(side='left', fill='x')
        self.progress = ttk.Progressbar(actions_frame, orient='horizontal', length=220, mode='determinate')
        self.progress.pack(padx=6, pady=6)

        # Config quick actions
        cfg_frame = ttk.LabelFrame(right_content, text='Hardware / Config', padding=8)
        cfg_frame.pack(fill='x', pady=(0,10))
        ttk.Button(cfg_frame, text='Region Setup', command=self.run_setup).pack(side='left', padx=6, pady=4)
        ttk.Button(cfg_frame, text='Abrir capturas', command=self.open_screenshots).pack(side='left', padx=6, pady=4)
        ttk.Button(cfg_frame, text='Abrir logs', command=self.open_logs).pack(side='left', padx=6, pady=4)

        # Terminal / Logs
        term_frame = ttk.LabelFrame(right_content, text='Live Terminal', padding=6)
        term_frame.pack(fill='both', expand=True)
        self.log_widget = scrolledtext.ScrolledText(term_frame, bg='#071321', fg=self.fg_color, font=self.font_mono, 
                             borderwidth=0, highlightthickness=0, height=12, insertbackground=self.fg_color)
        self.log_widget.pack(fill='both', expand=True, padx=4, pady=4)
        self.log_widget.config(state='disabled')

        # Session stats
        stats_frame = ttk.Frame(right_content)
        stats_frame.pack(fill='x', pady=(8,0))
        self.lbl_exito = ttk.Label(stats_frame, text='Journals Success: 0', style='Sub.TLabel')
        self.lbl_exito.pack(side='left', padx=6)
        self.lbl_error = ttk.Label(stats_frame, text='Critical Errors: 0', style='Sub.TLabel')
        self.lbl_error.pack(side='left', padx=6)

        # --- FOOTER ---
        footer = ttk.Frame(self.main_container)
        footer.pack(fill='x', side='bottom', pady=(10,0))
        ttk.Label(footer, text='Created by: Cotano_', style='Sub.TLabel').pack(side='left')

    def add_pill(self, parent, text, color, bg):
        p = tk.Label(parent, text=text, bg=color, fg=bg, font=self.font_mono)
        p.pack(side='left', padx=2)

    def create_styled_box(self, parent, title, color):
        f = tk.LabelFrame(parent, text=title, bg=self.bg_color)
        f.pack(fill='x', pady=(0,10))
        return f

    def add_action_btn(self, parent, text, color, cmd, state="normal"):
        b = ttk.Button(parent, text=text, command=cmd)
        if state != 'normal': b.state(['disabled'])
        b.pack(side='left', expand=True, padx=6)
        return b

    def add_info_line(self, parent, label, value, color, cmd):
        f = ttk.Frame(parent)
        f.pack(fill='x', pady=2)
        ttk.Label(f, text=label, style='Sub.TLabel').pack(side='left')
        ttk.Button(f, text=value, command=cmd).pack(side='left', padx=8)

    def log(self, message):
        self.log_queue.put(message)

    def check_queue(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self.log_widget.config(state='normal')
                ts = datetime.now().strftime('%H:%M:%S')
                indicator = '::'
                if 'exitoso' in msg.lower() or 'completado' in msg.lower():
                    indicator = 'OK'
                elif 'error' in msg.lower() or 'timeout' in msg.lower():
                    indicator = '!!'

                self.log_widget.insert(tk.END, f'[{ts}] {indicator} {msg}\n')
                self.log_widget.see(tk.END)
                self.log_widget.config(state='disabled')

                if 'completado' in msg.lower() or 'exitoso' in msg.lower():
                    self.diarios_exitosos += 1
                    self.lbl_exito.config(text=f'Journals Success: {self.diarios_exitosos}')
                elif 'error' in msg.lower() or 'timeout' in msg.lower():
                    if 'ignorado' not in msg.lower():
                        self.diarios_errores += 1
                        self.lbl_error.config(text=f'Critical Errors: {self.diarios_errores}')
        except queue.Empty: pass
        self.root.after(100, self.check_queue)

    def start_bot(self):
        if self.bot_thread and self.bot_thread.is_alive():
            return
        self.stop_event.clear()
        self.log('Booting system...')
        try:
            self.btn_start.state(['disabled'])
            self.btn_stop.state(['!disabled'])
        except Exception:
            pass
        self.bot_thread = threading.Thread(target=self.run_bot_thread, daemon=True)
        self.bot_thread.start()

    def stop_bot(self):
        self.stop_event.set()
        self.log("SIGKILL sent to bot process.")
        try:
            self.btn_stop.state(['disabled'])
            self.btn_start.state(['!disabled'])
        except Exception:
            pass

    def run_bot_thread(self):
        try: run_bot(log_callback=self.log, stop_event=self.stop_event)
        finally:
            try:
                self.btn_start.after(0, lambda: self.btn_start.state(['!disabled']))
                self.btn_stop.after(0, lambda: self.btn_stop.state(['disabled']))
            except Exception:
                pass

    def run_setup(self):
        if self.bot_thread and self.bot_thread.is_alive(): return
        AreaSelector().run()

    def open_screenshots(self):
        path = os.path.join("logs", "capturas")
        if not os.path.exists(path): os.makedirs(path)
        os.startfile(path)

    def open_logs(self):
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        nombre_archivo = f"registro_{fecha_hoy}.txt"
        if os.path.exists(nombre_archivo): os.startfile(nombre_archivo)

if __name__ == "__main__":
    root = tk.Tk()
    w, h = 950, 750
    x, y = (root.winfo_screenwidth()/2) - (w/2), (root.winfo_screenheight()/2) - (h/2)
    root.geometry('%dx%d+%d+%d' % (w, h, x, y))
    app = BotAXGui(root)
    root.mainloop()
