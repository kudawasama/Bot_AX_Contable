"""Módulo de logging para Bot AX Contable.

Proporciona logging estructurado con rotación de archivos
y soporte para integración de colas con la interfaz gráfica.
"""
import logging
import os
import queue
from logging.handlers import RotatingFileHandler
from typing import Optional

# Directorio de este archivo: src/core/
CORE_DIR: str = os.path.dirname(os.path.abspath(__file__))

# Directorio raíz del proyecto (dos niveles arriba: src/core/ -> src/ -> raíz)
BASE_DIR: str = os.path.dirname(os.path.dirname(CORE_DIR))

# Directorio de logs en la raíz
LOG_DIR: str = os.path.join(BASE_DIR, "logs")
LOG_FILE: str = os.path.join(LOG_DIR, "bot_ax.log")

# Formato estándar de logs
LOG_FORMAT: str = "[%(asctime)s] [%(levelname)s] %(message)s"
LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"

_logger: Optional[logging.Logger] = None


def get_logger(name: str = "bot_ax") -> logging.Logger:
    """Obtiene o crea la instancia global del logger de la aplicación.

    Configura un RotatingFileHandler (máx 5MB, con 3 backups codificados en UTF-8).

    Args:
        name (str): Nombre identificador del logger.

    Returns:
        logging.Logger: Instancia del logger configurada.
    """
    global _logger
    if _logger is not None:
        return _logger
    
    os.makedirs(LOG_DIR, exist_ok=True)
    
    _logger = logging.getLogger(name)
    _logger.setLevel(logging.DEBUG)
    
    # Evitar handlers duplicados si se invoca múltiples veces
    if _logger.handlers:
        return _logger
    
    formatter: logging.Formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    
    # Manejador de archivo rotativo para persistir trazas
    file_handler: RotatingFileHandler = RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    _logger.addHandler(file_handler)
    
    return _logger


class QueueLogHandler(logging.Handler):
    """Handler de logging personalizado que redirige los registros a una cola de eventos.

    Diseñado para interceptar los mensajes del bot y renderizarlos en tiempo real
    en la consola integrada de la interfaz gráfica de usuario.
    """
    
    def __init__(self, log_queue: queue.Queue) -> None:
        """Inicializa el handler vinculando la cola de eventos.

        Args:
            log_queue (queue.Queue): Cola donde se encolarán los mensajes formateados.
        """
        super().__init__()
        self.log_queue: queue.Queue = log_queue
        self.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT))
    
    def emit(self, record: logging.LogRecord) -> None:
        """Formatea el registro y lo coloca en la cola.

        Args:
            record (logging.LogRecord): Registro de log a encolar.
        """
        try:
            msg: str = self.format(record)
            self.log_queue.put(msg)
        except Exception:
            self.handleError(record)
