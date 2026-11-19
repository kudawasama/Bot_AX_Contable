"""Pruebas de la ampliación del recorte antes del OCR del ID de diario.

POR QUÉ (v-00.42.00): el 2026-11-19 el bot se saltó los diarios ``00342437``,
``00342438`` y ``00342439`` —consecutivos— porque ``leer_id_diario`` recibía cadena
vacía de Tesseract aunque la casilla tenía el ID. La corrección es ampliar el recorte
x2 antes del OCR. Estas pruebas fijan ese comportamiento y, sobre todo, comprueban que
el candado de validación **no** se relaja al cambiar la imagen.

Ninguna prueba toca el escritorio ni invoca Tesseract real: ``tests/conftest.py``
inyecta dobles inertes de ``pyautogui`` y ``pytesseract``.
"""

from typing import Tuple

import pytest
from PIL import Image

from src.core.config import obtener_offset_ocr
from src.services import vision


def _region_id() -> Tuple[int, int]:
    """Devuelve (ancho, alto) de la región que se recorta para leer el ID.

    Se lee de la configuración real para que la prueba siga siendo válida si algún
    día se recalibra ``ocr_region_offset``.
    """
    _, _, ancho, alto = obtener_offset_ocr()
    return int(ancho), int(alto)


def _preparar_pantalla(mock_pyautogui, tamano: Tuple[int, int]) -> None:
    """Hace que ``pyautogui.screenshot`` devuelva una imagen PIL real del tamaño pedido."""
    mock_pyautogui.screenshot.return_value = Image.new("RGB", tamano, color="white")


# ──────────────────────────────────────────────────────────────
# 1. La ampliación llega a Tesseract
# ──────────────────────────────────────────────────────────────
def test_el_recorte_del_id_se_amplia_antes_del_ocr(mock_pyautogui, mock_tesseract) -> None:
    """La imagen que recibe Tesseract debe medir ``ESCALA_OCR`` veces la región."""
    ancho, alto = _region_id()
    _preparar_pantalla(mock_pyautogui, (ancho, alto))
    mock_tesseract.image_to_string.return_value = "00342437"

    vision.leer_id_diario((296, 602))

    assert mock_tesseract.image_to_string.called, "no se llamó al OCR"
    imagen_recibida: Image.Image = mock_tesseract.image_to_string.call_args[0][0]
    assert imagen_recibida.size == (ancho * vision.ESCALA_OCR, alto * vision.ESCALA_OCR)
    assert imagen_recibida.mode == "L", "el OCR debe recibir escala de grises"


def test_escalar_para_ocr_amplia_los_dos_ejes() -> None:
    """``_escalar_para_ocr`` duplica ancho y alto manteniendo el modo de color."""
    original: Image.Image = Image.new("L", (110, 28), color=0)

    ampliada: Image.Image = vision._escalar_para_ocr(original)

    assert ampliada.size == (220, 56)
    assert ampliada.mode == "L"


@pytest.mark.parametrize("factor", [1, 0, -3])
def test_escalar_para_ocr_con_factor_no_ampliable_no_cambia_nada(factor: int) -> None:
    """Un factor <= 1 devuelve la imagen original: nunca se reduce el recorte."""
    original: Image.Image = Image.new("L", (110, 28), color=0)

    assert vision._escalar_para_ocr(original, factor) is original


# ──────────────────────────────────────────────────────────────
# 2. El candado de validación sigue intacto
# ──────────────────────────────────────────────────────────────
def test_un_id_de_ocho_digitos_se_devuelve(mock_pyautogui, mock_tesseract) -> None:
    """Un único número de 8 dígitos es un ID válido."""
    _preparar_pantalla(mock_pyautogui, _region_id())
    mock_tesseract.image_to_string.return_value = "| 00342438 Die\n"

    assert vision.leer_id_diario((296, 602)) == "00342438"


def test_siete_digitos_sigue_siendo_error_lectura(mock_pyautogui, mock_tesseract) -> None:
    """Ampliar la imagen no debe aceptar lecturas incompletas."""
    _preparar_pantalla(mock_pyautogui, _region_id())
    mock_tesseract.image_to_string.return_value = "0034243"

    assert vision.leer_id_diario((296, 602)) == "ERROR_LECTURA"


def test_dos_ids_distintos_sigue_siendo_error_lectura(mock_pyautogui, mock_tesseract) -> None:
    """Dos números válidos distintos son lectura corrida: no se acepta ninguno."""
    _preparar_pantalla(mock_pyautogui, _region_id())
    mock_tesseract.image_to_string.return_value = "00342437 00342438"

    assert vision.leer_id_diario((296, 602)) == "ERROR_LECTURA"


def test_texto_vacio_sigue_siendo_error_lectura(mock_pyautogui, mock_tesseract) -> None:
    """Si el OCR no devuelve nada, se sigue saltando la casilla (nunca se inventa)."""
    _preparar_pantalla(mock_pyautogui, _region_id())
    mock_tesseract.image_to_string.return_value = ""

    assert vision.leer_id_diario((296, 295)) == "ERROR_LECTURA"
