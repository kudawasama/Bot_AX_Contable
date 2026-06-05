"""
Módulo de logging para Bot AX Contable.

Proporciona logging estructurado con rotación de archivos
y soporte para integración con la GUI.
"""
import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
LOG_FILE = os.path.join(LOG_DIR, "bot_ax.log")

# Formato: [2026-06-05 13:04:08] [INFO] mensaje
LOG_FORMAT = "[%(asctime)s] [%(levelname)s] %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_logger = None


def get_logger(name="bot_ax"):
    """
    Obtiene o crea el logger global de la aplicación.
    
    Configura un RotatingFileHandler (máx 5MB, 3 backups, UTF-8).
    """
    global _logger
    if _logger is not None:
        return _logger
    
    os.makedirs(LOG_DIR, exist_ok=True)
    
    _logger = logging.getLogger(name)
    _logger.setLevel(logging.DEBUG)
    
    # Evitar duplicados si se llama múltiples veces
    if _logger.handlers:
        return _logger
    
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    
    # Archivo rotativo
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    _logger.addHandler(file_handler)
    
    return _logger


class QueueLogHandler(logging.Handler):
    """
    Handler de logging que encola mensajes para la GUI.
    
    Úsalo en app_gui.py para reemplazar sys.stdout hack:
        queue_handler = QueueLogHandler(log_queue)
        logging.getLogger("bot_ax").addHandler(queue_handler)
    """
    
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue
        self.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT))
    
    def emit(self, record):
        try:
            msg = self.format(record)
            self.log_queue.put(msg)
        except Exception:
            self.handleError(record)
