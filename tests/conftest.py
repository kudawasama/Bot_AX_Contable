"""Fixtures compartidos para la suite de pruebas del Bot AX Contable.

Problema que resuelve (hallazgos C-1 y C-3 del plan de implementación):
    ``tests/test_vision.py`` hacía ``import vision`` (estructura previa al
    refactor modular) y ``tests/test_config.py`` hacía ``import config``, por
    lo que la colección de pytest fallaba al 100% y el protocolo de
    verificación obligatorio de ``AGENTS.md`` (``python -m pytest``) quedaba
    inservible.

Solución:
    * Se agrega la raíz del proyecto a ``sys.path`` una sola vez.
    * Se inyectan módulos falsos de ``pyautogui`` y ``pytesseract`` en
      ``sys.modules`` **antes** de que cualquier prueba importe
      ``src.services.vision``. Esto reemplaza el hack frágil
      ``BOT_AX_TEST_MODE`` + ``types.ModuleType`` y garantiza que la suite
      jamás mueva el mouse real, capture la pantalla ni invoque Tesseract
      (crítico: el bot puede estar en ejecución mientras se corren los tests).

Uso::

    def test_algo(mock_pyautogui, tmp_config):
        ...
"""

import json
import sys
import types
from collections import namedtuple
from pathlib import Path
from typing import Any, Dict, Iterator, Tuple
from unittest.mock import MagicMock

import pytest

# ──────────────────────────────────────────────────────────────
# 1. Raíz del proyecto en sys.path (permite importar src.*)
# ──────────────────────────────────────────────────────────────
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ──────────────────────────────────────────────────────────────
# 2. Módulos falsos (inyectados antes de importar el código del bot)
# ──────────────────────────────────────────────────────────────
Punto: type = namedtuple("Punto", ["x", "y"])


class _ImageNotFoundException(Exception):
    """Reemplazo de ``pyautogui.ImageNotFoundException`` (debe ser Exception)."""


class _FailSafeException(Exception):
    """Reemplazo de ``pyautogui.FailSafeException`` (debe ser Exception)."""


def _crear_pyautogui_falso() -> types.ModuleType:
    """Construye un ``pyautogui`` inerte para los tests.

    Todas las funciones de interacción devuelven valores neutros (``None`` o
    listas vacías) y no producen efectos sobre el escritorio.

    Returns:
        types.ModuleType: Módulo sustituto compatible con el usado por
        ``src/services/vision.py`` y ``src/core/engine.py``.
    """
    modulo: types.ModuleType = types.ModuleType("pyautogui")
    modulo.PAUSE = 0.0
    modulo.FAILSAFE = False
    modulo.ImageNotFoundException = _ImageNotFoundException
    modulo.FailSafeException = _FailSafeException
    modulo.locateCenterOnScreen = MagicMock(return_value=None)
    modulo.locateOnScreen = MagicMock(return_value=None)
    modulo.locateAllOnScreen = MagicMock(return_value=[])
    modulo.center = MagicMock(return_value=Punto(0, 0))
    modulo.screenshot = MagicMock()
    modulo.size = MagicMock(return_value=(1920, 1080))
    modulo.click = MagicMock()
    modulo.moveTo = MagicMock()
    modulo.moveRel = MagicMock()
    modulo.press = MagicMock()
    modulo.scroll = MagicMock()
    return modulo


def _crear_pytesseract_falso() -> types.ModuleType:
    """Construye un ``pytesseract`` inerte (no invoca el binario real)."""
    modulo: types.ModuleType = types.ModuleType("pytesseract")
    modulo.pytesseract = types.SimpleNamespace(tesseract_cmd="tesseract-falso")
    modulo.image_to_string = MagicMock(return_value="")
    return modulo


if "pyautogui" not in sys.modules:
    sys.modules["pyautogui"] = _crear_pyautogui_falso()
if "pytesseract" not in sys.modules:
    sys.modules["pytesseract"] = _crear_pytesseract_falso()


# ──────────────────────────────────────────────────────────────
# 3. Fixtures públicas
# ──────────────────────────────────────────────────────────────
@pytest.fixture
def mock_pyautogui() -> Iterator[types.ModuleType]:
    """Expone el módulo ``pyautogui`` falso y limpia sus mocks al terminar.

    Yields:
        types.ModuleType: El módulo falso ya registrado en ``sys.modules``.
    """
    modulo: types.ModuleType = sys.modules["pyautogui"]
    yield modulo
    for nombre in ("locateCenterOnScreen", "locateOnScreen", "locateAllOnScreen",
                   "center", "screenshot", "click", "moveTo", "moveRel",
                   "press", "scroll"):
        getattr(modulo, nombre).reset_mock()
    modulo.locateCenterOnScreen.return_value = None
    modulo.locateOnScreen.return_value = None
    modulo.locateAllOnScreen.return_value = []
    modulo.center.return_value = Punto(0, 0)


@pytest.fixture
def mock_tesseract() -> Iterator[types.ModuleType]:
    """Expone el módulo ``pytesseract`` falso.

    Yields:
        types.ModuleType: El módulo falso ya registrado en ``sys.modules``.
    """
    modulo: types.ModuleType = sys.modules["pytesseract"]
    yield modulo
    modulo.image_to_string.reset_mock()
    modulo.image_to_string.return_value = ""


@pytest.fixture
def tmp_config(tmp_path: Path) -> Iterator[Tuple[Path, Dict[str, Any]]]:
    """Crea un ``config_sectores.json`` temporal con sectores válidos.

    Args:
        tmp_path: Directorio temporal provisto por pytest.

    Yields:
        Tuple[Path, Dict[str, Any]]: Ruta del archivo y su contenido.
    """
    datos: Dict[str, Any] = {
        "sector_a": [10, 20, 100, 200],
        "sector_b": [30, 40, 50, 60],
        "sector_scroll": [5, 5, 20, 20],
        "ocr_region_offset": [-275, -13, 110, 28],
    }
    archivo: Path = tmp_path / "config_sectores.json"
    archivo.write_text(json.dumps(datos), encoding="utf-8")
    yield archivo, datos


@pytest.fixture
def tmp_blacklist(tmp_path: Path) -> Iterator[Path]:
    """Crea un ``blacklist.json`` temporal con dos diarios en lista negra.

    Args:
        tmp_path: Directorio temporal provisto por pytest.

    Yields:
        Path: Ruta del archivo de lista negra.
    """
    archivo: Path = tmp_path / "blacklist.json"
    archivo.write_text(json.dumps(["00327946", "00326946"]), encoding="utf-8")
    yield archivo
