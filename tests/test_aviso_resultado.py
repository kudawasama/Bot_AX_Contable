"""Pruebas de la clasificación del aviso de fin de ciclo (Infolog de AX).

POR QUÉ EXISTEN (incidente 2026-11-17):
    El bot no detectaba que el ciclo había terminado. La causa no era el tiempo de espera:
    era que los patrones usados (``msg_exito_asiento_1.png`` y ``Error_Registro.png``) son
    capturas del Infolog **completo**, e incluyen texto que cambia en cada registro —la hora
    del mensaje y el número de asientos—. Con el aviso real en pantalla la similitud medida
    fue 0.69 y 0.31 contra umbrales de 0.8 y 0.9, así que el bot esperaba hasta el timeout
    de 60 minutos.

    Ahora se comparan recortes de texto fijo. Estas pruebas fijan ese contrato: éxito,
    error, prioridad del error y ausencia de aviso.

    Son pruebas de solo lectura: reciben la imagen como argumento, nunca capturan la
    pantalla ni mueven el mouse.
"""
from typing import Optional

import cv2
import numpy as np

from src.core.config import INFOLOG_ERROR, INFOLOG_EXITO
from src.services.vision import clasificar_aviso_resultado

ALTO_PANTALLA: int = 768
ANCHO_PANTALLA: int = 1366


def _pantalla_neutra() -> np.ndarray:
    """Fondo gris con textura leve (una imagen lisa daría correlación indefinida)."""
    fondo = np.full((ALTO_PANTALLA, ANCHO_PANTALLA), 128, dtype=np.uint8)
    ruido = np.random.default_rng(0).integers(-6, 7, fondo.shape)
    return np.clip(fondo.astype(int) + ruido, 0, 255).astype(np.uint8)


def _pegar(pantalla: np.ndarray, ruta_patron: str, x: int, y: int) -> np.ndarray:
    """Copia el patrón tal cual sobre la pantalla, en la posición indicada."""
    patron = cv2.imread(ruta_patron, cv2.IMREAD_GRAYSCALE)
    assert patron is not None, f"no se pudo leer el patrón {ruta_patron}"
    alto, ancho = patron.shape[:2]
    pantalla[y:y + alto, x:x + ancho] = patron
    return pantalla


def _clasificar(pantalla: Optional[np.ndarray] = None) -> Optional[str]:
    return clasificar_aviso_resultado(pantalla)


def test_aviso_de_exito_se_reconoce() -> None:
    """El texto fijo de éxito ('Número de asientos registrados...') da 'exito'."""
    pantalla = _pegar(_pantalla_neutra(), INFOLOG_EXITO, 400, 300)
    assert _clasificar(pantalla) == 'exito'


def test_aviso_de_error_se_reconoce() -> None:
    """El texto fijo de error ('Uno o más errores de DETENCIÓN...') da 'error'."""
    pantalla = _pegar(_pantalla_neutra(), INFOLOG_ERROR, 400, 300)
    assert _clasificar(pantalla) == 'error'


def test_el_error_tiene_prioridad_sobre_el_exito() -> None:
    """Si el Infolog mezcla avisos, un error NO puede pasar por éxito.

    Es la salvaguarda que evita marcar como registrado un diario que falló.
    """
    pantalla = _pegar(_pantalla_neutra(), INFOLOG_EXITO, 200, 200)
    pantalla = _pegar(pantalla, INFOLOG_ERROR, 600, 400)
    assert _clasificar(pantalla) == 'error'


def test_sin_aviso_devuelve_none() -> None:
    """Una pantalla sin avisos no debe inventar un resultado."""
    assert _clasificar(_pantalla_neutra()) is None


def test_imagen_vacia_no_rompe() -> None:
    """Una imagen negra (sin varianza) tampoco debe levantar excepción."""
    assert _clasificar(np.zeros((ALTO_PANTALLA, ANCHO_PANTALLA), dtype=np.uint8)) is None


def test_patrones_de_aviso_existen_y_son_pequenos() -> None:
    """Los patrones de aviso son recortes de texto fijo, no ventanas completas.

    Un patrón grande vuelve a introducir texto variable (hora, número de asientos) y
    reintroduce el fallo original; por eso se fija un límite de tamaño.
    """
    for ruta in (INFOLOG_EXITO, INFOLOG_ERROR):
        imagen = cv2.imread(ruta, cv2.IMREAD_GRAYSCALE)
        assert imagen is not None, f"falta el patrón {ruta}"
        alto, ancho = imagen.shape[:2]
        assert alto <= 60 and ancho <= 330, f"{ruta} es demasiado grande: {ancho}x{alto}"
