"""
Fixtures compartidos para tests del Bot AX Contable.

Uso: pytest tests/ -v
"""

import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture(autouse=True)
def add_src_to_path():
    """Asegura que src/ esté en sys.path para todos los tests."""
    import sys
    import os
    _src = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
    if _src not in sys.path:
        sys.path.insert(0, _src)
    yield


@pytest.fixture
def mock_pyautogui():
    """
    Mock global de pyautogui para tests unitarios de visión.

    Úsalo en tests que importan módulos que dependen de pyautogui:
        def test_algo(mock_pyautogui):
            from bot_ax.vision.detector import buscar_y_clickear
            ...
    """
    with patch("bot_ax.vision.detector.pyautogui") as mock:
        mock.locateCenterOnScreen.return_value = (100, 100)
        mock.locateAllOnScreen.return_value = []
        mock.center.return_value = MagicMock(x=100, y=100)
        mock.size.return_value = (1920, 1080)
        mock.ImageNotFoundException = type("ImageNotFound", (Exception,), {})
        yield mock


@pytest.fixture
def mock_pytesseract():
    """
    Mock de pytesseract para tests de OCR.
    """
    with patch("bot_ax.vision.ocr.pytesseract") as mock:
        mock.image_to_string.return_value = "IS00327946iat"
        yield mock
