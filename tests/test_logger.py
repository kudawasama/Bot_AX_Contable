"""Tests del logging con rotación (``src/core/logger.py``).

Motivo: incidente detectado el 2026-10-09. Desde el 2026-10-08 10:52 no se
escribió ni una línea en ``logs/bot_ax.log`` aunque el bot siguió trabajando: el
``RotatingFileHandler`` mantenía un descriptor abierto y, al reemplazarse el
archivo en disco (Google Drive), todas las trazas se perdían en silencio. La
prueba ``test_reabre_el_archivo_si_fue_reemplazado`` es la regresión de ese bug.

Ejecutar con: ``python -m pytest tests/test_logger.py -v``
"""

import logging
from pathlib import Path

from src.core import logger as modulo_logger


def _crear_logger_de_prueba(destino: Path, max_bytes: int = 1024 * 1024) -> logging.Logger:
    """Crea un logger aislado que escribe en ``destino`` usando el handler real.

    Args:
        destino (Path): Archivo de log de la prueba.
        max_bytes (int): Umbral de rotación a usar.

    Returns:
        logging.Logger: Logger independiente (sin propagación).
    """
    log: logging.Logger = logging.getLogger(f"prueba_{destino.name}")
    log.handlers = []
    log.propagate = False
    log.setLevel(logging.DEBUG)

    handler: modulo_logger.ArchivoRotativoRobusto = modulo_logger.ArchivoRotativoRobusto(
        str(destino), max_bytes=max_bytes, backup_count=3
    )
    handler.setFormatter(
        logging.Formatter(modulo_logger.LOG_FORMAT, datefmt=modulo_logger.LOG_DATE_FORMAT)
    )
    log.addHandler(handler)
    return log


class TestArchivoRotativoRobusto:
    """Pruebas del handler de archivo resistente a reemplazos en disco."""

    def test_escribe_la_linea_en_el_archivo(self, tmp_path: Path):
        """Un registro se persiste en el archivo indicado."""
        archivo: Path = tmp_path / "bot_ax.log"
        log: logging.Logger = _crear_logger_de_prueba(archivo)

        log.info("primera linea")

        assert "primera linea" in archivo.read_text(encoding="utf-8")

    def test_reabre_el_archivo_si_fue_reemplazado(self, tmp_path: Path):
        """Regresión 2026-10-09: si el archivo se reemplaza en disco, se debe reabrir.

        Antes del arreglo, el descriptor huérfano hacía que las trazas nuevas se
        perdieran para siempre y el archivo quedara congelado en la última línea.
        """
        archivo: Path = tmp_path / "bot_ax.log"
        log: logging.Logger = _crear_logger_de_prueba(archivo)

        log.info("antes del reemplazo")
        archivo.unlink()  # simula a Google Drive reemplazando el archivo
        log.info("despues del reemplazo")

        contenido: str = archivo.read_text(encoding="utf-8")
        assert "antes del reemplazo" not in contenido
        assert "despues del reemplazo" in contenido

    def test_rota_al_superar_el_tamano(self, tmp_path: Path):
        """Al superar el tamaño máximo se genera el respaldo ``bot_ax.log.1``."""
        archivo: Path = tmp_path / "bot_ax.log"
        log: logging.Logger = _crear_logger_de_prueba(archivo, max_bytes=200)

        for indice in range(20):
            log.info("linea %d de relleno para forzar la rotacion del archivo", indice)

        assert archivo.exists()
        assert (tmp_path / "bot_ax.log.1").exists()

    def test_no_lanza_excepciones_si_no_puede_escribir(self, tmp_path: Path):
        """Si la ruta es inválida, el handler falla en silencio (nunca rompe el bot)."""
        bloqueador: Path = tmp_path / "archivo.txt"
        bloqueador.write_text("no soy un directorio", encoding="utf-8")

        log: logging.Logger = _crear_logger_de_prueba(bloqueador / "sub" / "bot_ax.log")
        log.info("esto no debe lanzar excepciones")


class TestGetLogger:
    """Pruebas de la configuración del logger global."""

    def test_get_logger_usa_el_handler_robusto(self, tmp_path: Path, monkeypatch):
        """``get_logger()`` debe configurar el handler resistente y registrar."""
        destino: Path = tmp_path / "bot_ax.log"
        monkeypatch.setattr(modulo_logger, "LOG_FILE", str(destino))
        monkeypatch.setattr(modulo_logger, "LOG_DIR", str(tmp_path))
        monkeypatch.setattr(modulo_logger, "_logger", None)

        nativo: logging.Logger = logging.getLogger("bot_ax")
        handlers_previos = list(nativo.handlers)
        nativo.handlers = []
        try:
            log: logging.Logger = modulo_logger.get_logger()
            assert any(
                isinstance(handler, modulo_logger.ArchivoRotativoRobusto)
                for handler in log.handlers
            )
            log.info("mensaje de prueba")
            assert "mensaje de prueba" in destino.read_text(encoding="utf-8")
        finally:
            nativo.handlers = handlers_previos
