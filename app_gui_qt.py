import sys
import os
import threading
import queue
import time
from datetime import datetime

try:
    from PyQt6 import QtWidgets, QtCore, QtGui
except Exception:
    # If PyQt6 not available, fallback to existing tkinter GUI
    print('PyQt6 no disponible. Ejecutando `app_gui.py` como fallback.')
    os.execv(sys.executable, [sys.executable, os.path.join(os.path.dirname(__file__), 'app_gui.py')])

try:
    import qdarktheme
    QDT_AVAILABLE = True
except Exception:
    QDT_AVAILABLE = False

from bot_main import run_bot
from setup_areas import AreaSelector


class QueueLogger:
    def __init__(self, q):
        self.q = q
    def write(self, msg):
        if msg and msg.strip():
            self.q.put(msg.strip())
    def flush(self):
        pass


class BotThread(threading.Thread):
    def __init__(self, log_callback, stop_event):
        super().__init__(daemon=True)
        self.log_callback = log_callback
        self.stop_event = stop_event
    def run(self):
        try:
            run_bot(log_callback=self.log_callback, stop_event=self.stop_event)
        except Exception as e:
            self.log_callback(f'Error en bot: {e}')


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Bot AX Contable — v2 (PyQt6)')
        self.resize(1100, 760)

        if QDT_AVAILABLE:
            qdarktheme.setup_theme('dark')

        self.log_q = queue.Queue()
        self.logger = QueueLogger(self.log_q)
        sys.stdout = self.logger
        sys.stderr = self.logger

        self.stop_event = threading.Event()
        self.bot_thread = None

        self._build_ui()

        # Poll timer for logs and uptime
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self._on_tick)
        self.timer.start(200)
        self.start_time = None

    def _build_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QHBoxLayout(central)

        # Sidebar
        sidebar = QtWidgets.QFrame()
        sidebar.setFixedWidth(240)
        sb_layout = QtWidgets.QVBoxLayout(sidebar)
        app_label = QtWidgets.QLabel('Bot AX Contable')
        font = QtGui.QFont('Segoe UI', 12, QtGui.QFont.Weight.Bold)
        app_label.setFont(font)
        sb_layout.addWidget(app_label)
        sb_layout.addSpacing(6)

        btn_estado = QtWidgets.QPushButton('Estado')
        btn_logs = QtWidgets.QPushButton('Registro / Logs')
        btn_cfg = QtWidgets.QPushButton('Configuración')
        for b in (btn_estado, btn_logs, btn_cfg):
            b.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
            sb_layout.addWidget(b)

        sb_layout.addStretch()
        btn_caps = QtWidgets.QPushButton('Abrir capturas')
        btn_caps.clicked.connect(self.open_screenshots)
        sb_layout.addWidget(btn_caps)
        btn_revlogs = QtWidgets.QPushButton('Revisar logs')
        btn_revlogs.clicked.connect(self.open_logs)
        sb_layout.addWidget(btn_revlogs)

        layout.addWidget(sidebar)

        # Main area
        main_area = QtWidgets.QVBoxLayout()

        # Header with controls
        header = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel('Bot AX Contable')
        title.setFont(QtGui.QFont('Segoe UI', 16, QtGui.QFont.Weight.Bold))
        header.addWidget(title)
        header.addStretch()
        self.btn_start = QtWidgets.QPushButton('START ENGINE')
        self.btn_start.setStyleSheet('padding:8px 14px; background:#2dd4bf; color:#042028; border-radius:6px;')
        self.btn_start.clicked.connect(self.start_bot)
        header.addWidget(self.btn_start)
        self.btn_stop = QtWidgets.QPushButton('STOP')
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet('padding:8px 14px; background:#ef4444; color:white; border-radius:6px;')
        self.btn_stop.clicked.connect(self.stop_bot)
        header.addWidget(self.btn_stop)
        main_area.addLayout(header)

        # Cards
        cards = QtWidgets.QHBoxLayout()
        card_uptime = QtWidgets.QFrame()
        cu_layout = QtWidgets.QVBoxLayout(card_uptime)
        cu_label = QtWidgets.QLabel('Uptime')
        cu_label.setFont(QtGui.QFont('Segoe UI', 10, QtGui.QFont.Weight.Bold))
        cu_layout.addWidget(cu_label)
        self.uptime_value = QtWidgets.QLabel('00:00:00')
        cu_layout.addWidget(self.uptime_value)
        cards.addWidget(card_uptime)

        self.progress = QtWidgets.QProgressBar()
        self.progress.setValue(0)
        self.progress.setFixedHeight(18)
        cards.addWidget(self.progress)
        main_area.addLayout(cards)

        # Config actions
        cfg_layout = QtWidgets.QHBoxLayout()
        btn_region = QtWidgets.QPushButton('Region Setup')
        btn_region.clicked.connect(self.run_setup)
        cfg_layout.addWidget(btn_region)
        main_area.addLayout(cfg_layout)

        # Logs area
        self.log_edit = QtWidgets.QPlainTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setStyleSheet('background:#071321; color:#e6eef8; font-family: Consolas, monospace;')
        self.log_edit.setMinimumHeight(320)
        main_area.addWidget(self.log_edit)

        # Stats
        stats = QtWidgets.QHBoxLayout()
        self.lbl_exito = QtWidgets.QLabel('Journals Success: 0')
        self.lbl_error = QtWidgets.QLabel('Critical Errors: 0')
        stats.addWidget(self.lbl_exito)
        stats.addWidget(self.lbl_error)
        stats.addStretch()
        main_area.addLayout(stats)

        layout.addLayout(main_area)

    def _on_tick(self):
        # drain log queue
        updated = False
        try:
            while True:
                msg = self.log_q.get_nowait()
                ts = datetime.now().strftime('%H:%M:%S')
                indicator = '::'
                low = msg.lower()
                if 'exitoso' in low or 'completado' in low:
                    indicator = 'OK'
                    self._inc_success()
                elif 'error' in low or 'timeout' in low:
                    indicator = '!!'
                    if 'ignorado' not in low:
                        self._inc_error()
                self.log_edit.appendPlainText(f'[{ts}] {indicator} {msg}')
                updated = True
        except queue.Empty:
            pass

        if self.start_time:
            delta = int(time.time() - self.start_time)
            h = delta // 3600
            m = (delta % 3600) // 60
            s = delta % 60
            self.uptime_value.setText(f'{h:02d}:{m:02d}:{s:02d}')

        if updated:
            # auto scroll
            cursor = self.log_edit.textCursor()
            cursor.movePosition(QtGui.QTextCursor.MoveOperation.End)
            self.log_edit.setTextCursor(cursor)

    def _inc_success(self):
        txt = self.lbl_exito.text()
        n = int(txt.split(':')[-1].strip())
        n += 1
        self.lbl_exito.setText(f'Journals Success: {n}')

    def _inc_error(self):
        txt = self.lbl_error.text()
        n = int(txt.split(':')[-1].strip())
        n += 1
        self.lbl_error.setText(f'Critical Errors: {n}')

    def log(self, message):
        self.log_q.put(message)

    def start_bot(self):
        if self.bot_thread and self.bot_thread.is_alive():
            return
        self.stop_event.clear()
        self.start_time = time.time()
        self.log('Booting system...')
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.bot_thread = BotThread(log_callback=self.log, stop_event=self.stop_event)
        self.bot_thread.start()

    def stop_bot(self):
        self.stop_event.set()
        self.log('SIGKILL sent to bot process.')
        self.btn_stop.setEnabled(False)
        self.btn_start.setEnabled(True)

    def run_setup(self):
        # run AreaSelector in a background thread to avoid blocking
        def _run():
            try:
                AreaSelector().run()
            except Exception as e:
                self.log(f'Error en AreaSelector: {e}')
        threading.Thread(target=_run, daemon=True).start()

    def open_screenshots(self):
        path = os.path.join('logs', 'capturas')
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        os.startfile(path)

    def open_logs(self):
        fecha_hoy = datetime.now().strftime('%Y-%m-%d')
        nombre_archivo = f'registro_{fecha_hoy}.txt'
        if os.path.exists(nombre_archivo):
            os.startfile(nombre_archivo)
        else:
            self.log('No existe archivo de logs para hoy.')

    def closeEvent(self, event):
        # ensure bot stops on exit
        try:
            self.stop_event.set()
        except Exception:
            pass
        event.accept()


def main():
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
