# Plan de Reestructuración — Bot AX Contable

> **Objetivo:** Convertir el proyecto flat actual en una estructura profesional, escalable y ordenada
> **Estrategia:** Por fases, sin romper funcionalidad existente hasta el final

---

## Visión de la Estructura Final

```
bot-ax-contable/
├── pyproject.toml                  # 🆕 Metadata, dependencias, entry points
├── README.md                       # 📝 Actualizado
├── LICENSE                         # 🆕 Archivo de licencia
├── .gitignore                      # 📝 Expandido
├── .githooks/
│   └── pre-commit                  # 📝 Auto-bump (sin cambios)
│
├── src/
│   └── bot_ax/                     # 🆕 Paquete principal (nuevo)
│       ├── __init__.py             # 🆕 Versión, auto-descubrimiento
│       ├── __main__.py             # 🆕 Entry point: `python -m bot_ax`
│       ├── _version.py             # 📦 Version info
│       │
│       ├── core/                   # 🆕 Núcleo del bot
│       │   ├── __init__.py
│       │   ├── engine.py           # 📦 run_bot() — extraído de bot_main.py
│       │   ├── registrador.py      # 🆕 registrar_log() + registro diario
│       │   └── blacklist.py        # 🆕 Gestión de blacklist (carga/guarda)
│       │
│       ├── vision/                 # 🆕 Separación de responsabilidades visuales
│       │   ├── __init__.py
│       │   ├── detector.py         # 📦 Template matching (buscar_y_clickear, etc.)
│       │   ├── ocr.py              # 📦 OCR Tesseract (leer_id_diario, offset)
│       │   ├── ids.py              # 📦 Normalización de IDs
│       │   └── captura.py          # 📦 Captura de pantalla (capturar_pantalla_error)
│       │
│       ├── config/                 # 🆕 Configuración separada
│       │   ├── __init__.py
│       │   ├── settings.py         # 📦 Constantes, rutas, validación Tesseract
│       │   ├── sectores.py         # 📦 Carga/guarda config_sectores.json
│       │   └── defaults.py         # 🆕 Valores por defecto y fallbacks
│       │
│       └── ui/                     # 🆕 Interfaces de usuario
│           ├── __init__.py
│           ├── app_gui.py          # 📦 GUI moderna (Tkinter) — refactorizada
│           ├── components/         # 🆕 Componentes reutilizables
│           │   ├── __init__.py
│           │   ├── cards.py        # 🆕 StatusCard, MetricsCard, etc.
│           │   ├── stream.py       # 🆕 Log stream widget
│           │   └── controls.py     # 🆕 Engine control buttons
│           └── setup_areas.py      # 📦 Selector visual de sectores
│
├── scripts/                        # 🆕 Scripts de utilidad (no en raíz)
│   ├── check_ocr.py                # 📦 test_ocr.py
│   ├── debug_ocr.py                # 📦 debug_ocr.py
│   ├── debug_pantalla.py           # 📦 debug_pantalla.py
│   └── diagnose_vision.py          # 📦 diagnose_vision.py
│
├── tests/                          # 📝 Tests mejorados
│   ├── __init__.py
│   ├── conftest.py                 # 🆕 Fixtures compartidos
│   ├── test_config.py             # 📝 Actualizado
│   ├── test_vision_ids.py         # 📝 Separado de test_vision.py
│   ├── test_vision_detector.py    # 🆕 Tests para template matching (mockeado)
│   ├── test_engine.py             # 🆕 Tests para run_bot (mockeado)
│   └── test_blacklist.py          # 🆕 Tests para blacklist
│
├── patrones/                       # 📦 Imágenes patrón (sin cambios)
│   └── *.png
│
├── config_sectores.json.default    # 📦 Config de ejemplo
├── config_sectores.json            # 📦 Config local (ignorada por git)
├── blacklist.json                  # 📦 Auto-generado (ignorado por git)
│
├── logs/                           # 📦 Logs y capturas (ignorados por git)
│   ├── bot_ax.log
│   └── capturas/
│
└── docs/                           # 📝 Documentación expandida
    ├── auditoria-proyecto.md       # 🆕 Esta auditoría
    ├── plan-restructuracion.md     # 🆕 Este plan
    └── guia-rapida.md             # 🆕 Guía de inicio rápido / troubleshooting
```

---

## Fase 1: Foundation (Día 1)

### 1.1 Crear `pyproject.toml`

```toml
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "bot-ax-contable"
version = "0.1.44"
description = "Bot de automatización para Microsoft Dynamics AX — registro de diarios contables"
readme = "README.md"
license = {text = "MIT"}
authors = [
    {name = "José Céspedes", email = "jose.cespedes@casinoexpress.cl"}
]
requires-python = ">=3.10"
dependencies = [
    "pyautogui>=0.9.54",
    "pytesseract>=0.3.10",
    "pillow>=10.0.0",
    "keyboard>=0.13.5",
]

[project.scripts]
bot-ax = "bot_ax.__main__:main"

[tool.setuptools.packages.find]
where = ["src"]
```

### 1.2 Crear estructura de directorios

```bash
mkdir -p src/bot_ax/{core,vision,config,ui/components}
mkdir -p scripts
mkdir -p tests
```

### 1.3 Migrar módulos uno a uno (sin romper imports viejos)

Cada módulo nuevo conserva compatibilidad hacia atrás hasta que toda la migración esté completa.

---

## Fase 2: Migración de Código (Días 2-4)

### 2.1 `bot_ax/config/` — Separar configuración

| Archivo nuevo | Contenido | Origen |
|--------------|-----------|--------|
| `config/settings.py` | Constantes: rutas de patrones, TESSERACT_CMD, validar_tesseract() | `config.py` (mitad) |
| `config/sectores.py` | cargar_configuracion(), guardar_configuracion(), obtener_offset_ocr() | `config.py` (mitad) |
| `config/defaults.py` | Valores por defecto: offset OCR, confianzas, timeouts | Nuevo |

**Cambios:** `config.py` se convierte en un wrapper que re-exporta todo para compatibilidad.

### 2.2 `bot_ax/vision/` — Separar responsabilidades visuales

| Archivo nuevo | Contenido | Origen |
|--------------|-----------|--------|
| `vision/detector.py` | buscar_y_clickear(), buscar_estado_checkbox(), esperar_resultado_registro() | `vision.py` (mitad) |
| `vision/ocr.py` | leer_id_diario(), Tesseract config | `vision.py` (mitad) |
| `vision/ids.py` | normalizar_id_diario() + constantes NOMBRES_IMAGENES | `vision.py` (mitad) |
| `vision/captura.py` | capturar_pantalla_error() | `vision.py` (mitad) |

**Cambios:** `vision.py` se convierte en un wrapper que re-exporta.

### 2.3 `bot_ax/core/` — Extraer lógica del bot

| Archivo nuevo | Contenido | Origen |
|--------------|-----------|--------|
| `core/engine.py` | run_bot() | `bot_main.py` |
| `core/registrador.py` | registrar_log() | `bot_main.py` (helper) |
| `core/blacklist.py` | cargar_blacklist(), guardar_blacklist() | `bot_main.py` (lógica dispersa) |

### 2.4 `bot_ax/ui/` — Refactorizar GUI

| Archivo nuevo | Contenido | Origen |
|--------------|-----------|--------|
| `ui/app_gui.py` | BotAXGui (refactorizada en componentes) | `app_gui.py` |
| `ui/components/cards.py` | StatusCard, MetricsCard | `app_gui.py` (extraído) |
| `ui/components/stream.py` | LogStreamWidget | `app_gui.py` (extraído) |
| `ui/components/controls.py` | EngineControlBar | `app_gui.py` (extraído) |
| `ui/setup_areas.py` | AreaSelector | `setup_areas.py` |

---

## Fase 3: Limpieza y Eliminación (Día 5)

### 3.1 Eliminar código legacy

| Archivo | Acción | Motivo |
|---------|--------|--------|
| `bot_ax_registro.py` | ❌ Eliminar | GUI duplicada con `overrideredirect(True)` y datos falsos |
| `bot_main.py` | ❌ Eliminar | Migrado a `core/engine.py` |
| `vision.py` | ❌ Eliminar | Migrado a `vision/` |
| `config.py` | ❌ Eliminar | Migrado a `config/` |
| `logger.py` | ❌ Eliminar | Migrado a `config/settings.py` |
| `setup_areas.py` | ❌ Eliminar | Migrado a `ui/setup_areas.py` |
| `bump_version.py` | ❌ Eliminar | Migrado a `scripts/bump_version.py` |
| `test_ocr.py` | ❌ Eliminar | Migrado a `scripts/check_ocr.py` |
| `debug_ocr.py` | ❌ Eliminar | Migrado a `scripts/debug_ocr.py` |
| `debug_pantalla.py` | ❌ Eliminar | Migrado a `scripts/debug_pantalla.py` |
| `diagnose_vision.py` | ❌ Eliminar | Migrado a `scripts/diagnose_vision.py` |

### 3.2 Actualizar entry points

```python
# __main__.py
from bot_ax.ui.app_gui import main

if __name__ == "__main__":
    main()
```

### 3.3 Actualizar .gitignore

```
# Python
__pycache__/
*.pyc
*.pyo
*.egg-info/
dist/
build/

# IDE
.vscode/
.idea/

# Bot AX
logs/
registro_*.txt
registro_procesamiento.txt
blacklist.json
config_sectores.json

# Debug/Diagnóstico
*.png
!patrones/*.png
crash_log.txt
error.txt
diag_output*.txt
```

---

## Fase 4: Mejoras Post-Migración (Días 6-8)

### 4.1 Tests robustos

```python
# tests/conftest.py
import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_pyautogui():
    """Mock global de pyautogui para tests unitarios."""
    with patch("bot_ax.vision.detector.pyautogui") as mock:
        mock.locateCenterOnScreen.return_value = (100, 100)
        mock.locateAllOnScreen.return_value = []
        yield mock
```

### 4.2 Entry points CLI

```python
# __main__.py
import sys
from bot_ax.ui.app_gui import run_gui
from bot_ax.core.engine import run_bot

def main():
    if "--cli" in sys.argv:
        run_bot()
    else:
        run_gui()

if __name__ == "__main__":
    main()
```

### 4.3 Automatizar setup

```python
# scripts/setup.py
"""
Script único de setup:
1. Verifica Tesseract
2. Crea directorios necesarios
3. Guía al usuario para configurar sectores
4. Verifica patrones de imagen
"""
```

---

## Calendario de Implementación

| Fase | Días | Dependencias | Riesgo |
|------|------|-------------|--------|
| **F1:** Foundation + `pyproject.toml` | 1 | Ninguna | 🟢 Bajo |
| **F2:** Migración de código (4 submódulos) | 3-4 | F1 | 🟡 Medio — requiere regression testing |
| **F3:** Limpieza y eliminación | 1 | F2 completa | 🟡 Medio — compatibilidad backwards |
| **F4:** Mejoras (tests, CLI, setup) | 3 | F3 | 🟢 Bajo |

---

## Estrategia de Migración (Sin Riesgo)

Para minimizar riesgo, la migración sigue este proceso para cada módulo:

```
1. Crear nuevo módulo en src/bot_ax/<submodulo>/ 
2. Copiar lógica existente (sin cambios funcionales)
3. Crear wrapper en archivo legacy que re-exporte desde el nuevo módulo
4. Ejecutar tests existentes para verificar que nada se rompió
5. Repetir hasta que todos los módulos legacy sean solo wrappers
6. Eliminar archivos legacy (los wrappers)
```

Esto permite **commits incrementales** donde el código siempre es funcional.

---

## Beneficios Esperados

| Antes | Después |
|-------|---------|
| 16 archivos .py en la raíz | 5 archivos en la raíz |
| Sin estructura de paquete | `pip install -e .` funciona |
| `bot_ax_registro.py` legacy | Eliminado |
| `vision.py` monolito (288 lns) | 4 módulos especializados (~70 lns c/u) |
| Tests frágiles (monkey-patching) | Tests robustos (pytest fixtures) |
| Sin entry points CLI | `bot-ax` comando global |
| Sin pyproject.toml | Metadata completa del proyecto |
| `__pycache__` trackeado | Limpio en `.gitignore` |
| Sin guías de troubleshooting | Documentación expandida |
