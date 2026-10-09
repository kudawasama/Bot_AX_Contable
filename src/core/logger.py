"""Módulo de logging para Bot AX Contable.

Proporciona logging estructurado con rotación de archivos
y soporte para integración de colas con la interfaz gráfica.
"""
import logging
import os
import queue
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

# Límites de rotación del archivo de log
LOG_MAX_BYTES: int = 5 * 1024 * 1024
LOG_BACKUP_COUNT: int = 3

_logger: Optional[logging.Logger] = None


class ArchivoRotativoRobusto(logging.Handler):
    """Handler de archivo que nunca pierde escrituras si el archivo cambia en disco.

    MOTIVO (incidente detectado el 2026-10-09):
        ``RotatingFileHandler`` mantiene un descriptor abierto durante toda la
        ejecución. En este proyecto ``logs/`` vive en Google Drive (unidad H:) y,
        si el archivo se reemplaza o se re-sincroniza con el bot en marcha, el
        descriptor queda apuntando al archivo viejo y **todas** las escrituras
        siguientes se pierden sin dejar rastro (el bot corre con ``pythonw``, sin
        stderr, así que ``logging`` tampoco puede avisar por consola).

        Evidencia del incidente: desde el 2026-10-08 10:52 no se escribió ni una
        línea nueva en ``logs/bot_ax.log``, mientras que ``logs/events.jsonl`` y
        ``registro_YYYY-MM-DD.txt`` —que abren y cierran el archivo en cada
        escritura— siguieron funcionando con normalidad. Efecto: el analizador
        post-ejecución (``scripts/observer_analyze.py``) quedó ciego para todas
        las sesiones posteriores (ni timeouts, ni errores AX, ni fallbacks).

    SOLUCIÓN:
        Se conserva el mismo formato y la misma rotación por tamaño (5 MB, 3
        backups), pero el archivo se abre en modo *append* en cada emisión: si el
        archivo fue reemplazado en disco, se vuelve a crear. Nunca lanza
        excepciones: perder una línea de log jamás debe detener el bot.
    """

    def __init__(
        self,
        ruta: str,
        max_bytes: int = LOG_MAX_BYTES,
        backup_count: int = LOG_BACKUP_COUNT,
    ) -> None:
        """Inicializa el handler.

        Args:
            ruta (str): Ruta absoluta del archivo de log a escribir.
            max_bytes (int): Tamaño máximo del archivo antes de rotar.
            backup_count (int): Cantidad de archivos de respaldo a conservar.
        """
        super().__init__()
        self.ruta: str = ruta
        self.max_bytes: int = max_bytes
        self.backup_count: int = backup_count
        self._directorio_verificado: bool = False

    def _asegurar_directorio(self) -> None:
        """Crea el directorio de logs si aún no existe (una sola vez por corrida)."""
        if not self._directorio_verificado:
            directorio: str = os.path.dirname(self.ruta)
            if directorio:
                os.makedirs(directorio, exist_ok=True)
            self._directorio_verificado = True

    def _rotar_si_corresponde(self) -> None:
        """Rota el archivo cuando supera ``max_bytes`` (``bot_ax.log.1``, ``.2``, ...)."""
        if not os.path.exists(self.ruta):
            return
        if os.path.getsize(self.ruta) < self.max_bytes:
            return
        for indice in range(self.backup_count - 1, 0, -1):
            origen: str = f"{self.ruta}.{indice}"
            destino: str = f"{self.ruta}.{indice + 1}"
            if os.path.exists(origen):
                os.replace(origen, destino)
        os.replace(self.ruta, f"{self.ruta}.1")

    def emit(self, record: logging.LogRecord) -> None:
        """Escribe el registro en disco abriendo el archivo en cada emisión.

        Args:
            record (logging.LogRecord): Registro de log a persistir.
        """
        try:
            self._asegurar_directorio()
            self._rotar_si_corresponde()
            with open(self.ruta, "a", encoding="utf-8") as archivo:
                archivo.write(self.format(record) + "\n")
        except Exception:
            # Silencioso por diseño: el bot nunca debe caerse por un log perdido.
            pass


def get_logger(name: str = "bot_ax") -> logging.Logger:
    """Obtiene o crea la instancia global del logger de la aplicación.

    Configura un ``ArchivoRotativoRobusto`` (máx 5 MB, con 3 backups, UTF-8),
    que abre el archivo en cada escritura para no perder trazas si el archivo
    se reemplaza en disco (ver el docstring del handler).

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
    file_handler: ArchivoRotativoRobusto = ArchivoRotativoRobusto(
        LOG_FILE, max_bytes=LOG_MAX_BYTES, backup_count=LOG_BACKUP_COUNT
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
