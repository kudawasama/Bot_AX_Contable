"""
Valores por defecto del Bot AX Contable.

Centraliza todos los defaults numéricos para facilitar ajustes.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class OCRDefaults:
    """Valores por defecto para OCR y regiones."""
    offset_x: int = -275
    offset_y: int = -13
    offset_w: int = 110
    offset_h: int = 28

    @property
    def offset(self) -> tuple:
        return (self.offset_x, self.offset_y, self.offset_w, self.offset_h)


@dataclass(frozen=True)
class VisionDefaults:
    """Valores por defecto para template matching."""
    confianza_alta: float = 0.9
    confianza_media: float = 0.8
    confianza_baja: float = 0.7
    confianza_scroll_sector: float = 0.7
    confianza_scroll_full: float = 0.65
    timeout_normal: int = 30
    timeout_resultado: int = 3600  # 60 min
    scroll_intentos: int = 4
    scroll_clicks: int = 5


@dataclass(frozen=True)
class LogDefaults:
    """Valores por defecto para logging."""
    max_bytes: int = 5 * 1024 * 1024  # 5 MB
    backup_count: int = 3


# Instancias globales (importar directamente)
OCR = OCRDefaults()
VISION = VisionDefaults()
LOG = LogDefaults()
