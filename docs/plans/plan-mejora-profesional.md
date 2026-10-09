# Plan de Mejoramiento Profesional — Bot AX Contable

> **Versión:** 1.0  
> **Fecha:** 2026-07-13  
> **Objetivo:** Profesionalizar la infraestructura, calidad de código, testing, resiliencia y DX del proyecto.

---

## Tabla de Contenidos

1. [Fase 0: Fundación del Proyecto](#fase-0-fundación-del-proyecto-pyprojecttoml--entorno)
2. [Fase 1: Infraestructura y Portabilidad](#fase-1-infraestructura-y-portabilidad)
3. [Fase 2: Refactor del Core — Calidad de Código](#fase-2-refactor-del-core--calidad-de-código)
4. [Fase 3: Testing Integral](#fase-3-testing-integral)
5. [Fase 4: Resiliencia y Monitoreo](#fase-4-resiliencia-y-monitoreo)
6. [Fase 5: Configuración y Seguridad](#fase-5-configuración-y-seguridad)
7. [Fase 6: DevOps y Developer Experience](#fase-6-devops-y-developer-experience)
8. [Fase 7: Performance](#fase-7-performance)
9. [Resumen de Archivos](#resumen-de-archivos)
10. [Roadmap Temporal](#roadmap-temporal)

---

## Fase 0: Fundación del Proyecto (pyproject.toml + entorno)

**Objetivo:** Profesionalizar la base del proyecto con empaquetado estándar, dependencias explícitas y tooling unificado.  
**Racionalidad:** Un proyecto Python profesional necesita un `pyproject.toml` como fuente única de verdad. Hoy hay `requirements-dev.txt`, `.githooks/` shell, sin tipado estático ni linter configurado. Esto causa fricción a nuevos desarrolladores y ausencia de guardrails.

### Tarea 0.1 — Crear `pyproject.toml`

```python
"""Configuración del proyecto Bot AX Contable.

Define la estructura del paquete, metadatos, dependencias y herramientas
de calidad (linter, formateador, type checker). Centraliza en un único
archivo la declaración del proyecto siguiendo PEP 621.

Elimina la multiplicidad de archivos sueltos (requirements-dev.txt,
.githooks/, configs dispersas) y unifica bajo pyproject.toml todo el
ecosistema de desarrollo.
"""
```

| # | Subtarea | Descripción |
|---|----------|-------------|
| 0.1.1 | `[project]` | name="bot-ax-contable", version dinámica desde `src/core/version.py`, authors, description, requires-python=">=3.11" |
| 0.1.2 | `[project.dependencies]` | pyautogui, pytesseract, Pillow, keyboard, python-dotenv, pydantic |
| 0.1.3 | `[project.optional-dependencies]` | dev = ["pytest", "pytest-cov", "ruff", "mypy", "pre-commit"] |
| 0.1.4 | `[tool.ruff]` | target-version = "py311", select = ["E", "F", "I", "N", "W", "UP"], ignore = ["E501"] |
| 0.1.5 | `[tool.mypy]` | python_version = "3.11", strict = true, exclude = ["tests/"] |
| 0.1.6 | `[tool.pytest.ini_options]` | testpaths = ["tests"], addopts = "-v --cov=src --cov-report=term-missing" |
| 0.1.7 | `[tool.coverage.run]` | source = ["src"], branch = true |
| 0.1.8 | `[tool.coverage.report]` | fail_under = 80, show_missing = true |

**Archivos afectados:** `pyproject.toml` (nuevo), eliminar `requirements-dev.txt`.

### Tarea 0.2 — Crear `requirements.txt`

| # | Subtarea | Descripción |
|---|----------|-------------|
| 0.2.1 | Generar desde `pyproject.toml` | `pip install -e . && pip freeze > requirements.txt` |
| 0.2.2 | Marcar secciones | Comentarios `# PRODUCTION` y `# DEVELOPMENT` |

**Archivos afectados:** `requirements.txt` (nuevo).

### Tarea 0.3 — Variables de entorno + `.env.example`

| # | Subtarea | Descripción |
|---|----------|-------------|
| 0.3.1 | Migrar `TESSERACT_CMD` a env var | Leer con `os.getenv("TESSERACT_CMD")` con fallback en `defaults.py` |
| 0.3.2 | Agregar `BOT_AX_LOG_LEVEL` | `INFO` por defecto, `DEBUG` para troubleshooting |
| 0.3.3 | Agregar `BOT_AX_ENV` | `development` o `production`, determina perfil de config |
| 0.3.4 | Crear `.env.example` | Con valores de ejemplo comentados |
| 0.3.5 | Integrar `python-dotenv` | `dotenv.load_dotenv()` al inicio de `config.py` |

**Archivos afectados:** `.env.example` (nuevo), `src/core/config.py`.

### Tarea 0.4 — Pre-commit moderno

| # | Subtarea | Descripción |
|---|----------|-------------|
| 0.4.1 | `.pre-commit-config.yaml` | repos: ruff, ruff-format, mypy, trailing-whitespace, check-json, check-yaml, end-of-file-fixer |
| 0.4.2 | Eliminar `.githooks/pre-commit` | Reemplazar hook shell por pre-commit gestionado con `pre-commit install` |
| 0.4.3 | Agregar a Makefile | `make install: pre-commit install` |

**Archivos afectados:** `.pre-commit-config.yaml` (nuevo), eliminar `.githooks/`.

---

## Fase 1: Infraestructura y Portabilidad

**Objetivo:** Eliminar dependencias del entorno local (unidad H: de Google Drive, ruta de usuario hardcodeada) y containerizar para ejecución predecible.  
**Racionalidad:** El proyecto hoy depende de una ruta absoluta `H:\...` (Google Drive), una ruta de Tesseract con el nombre de usuario quemado y Python 3.12 en una ubicación fija. Esto hace imposible la ejecución en otra máquina sin editar archivos. Docker resuelve esto.

### Tarea 1.1 — `Dockerfile`

```dockerfile
# Imagen Docker para Bot AX Contable.
#
# Proposito: Proveer un entorno reproducible para ejecutar el bot
# sin depender de rutas locales, unidades de red o versiones de
# Python/Tesseract del host. Toda la configuracion sensible se
# inyecta via variables de entorno.

FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-spa \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV TESSERACT_CMD=/usr/bin/tesseract
ENV BOT_AX_ENV=production

ENTRYPOINT ["python", "-m", "src.ui.gui_classic"]
```

| # | Subtarea | Descripción |
|---|----------|-------------|
| 1.1.1 | Base image | `python:3.12-slim` con Tesseract OCR y dependencias gráficas |
| 1.1.2 | Multi-stage (opcional) | Build stage para compilar dependencias, runtime stage mínimo |
| 1.1.3 | Entrypoint | Por defecto lanza GUI clásica, sobreescribible via CMD |

**Archivos afectados:** `Dockerfile` (nuevo).

### Tarea 1.2 — `docker-compose.yml`

```yaml
# Orquestacion de servicios para Bot AX Contable.
#
# Define el servicio principal del bot con montajes para persistir
# configuracion, patrones visuales, logs y capturas de error.

services:
  bot-ax:
    build: .
    container_name: bot-ax-contable
    environment:
      - TESSERACT_CMD=/usr/bin/tesseract
      - BOT_AX_ENV=${BOT_AX_ENV:-production}
      - BOT_AX_LOG_LEVEL=${BOT_AX_LOG_LEVEL:-INFO}
    volumes:
      - ./config_sectores.json:/app/config_sectores.json
      - ./blacklist.json:/app/blacklist.json
      - ./patrones:/app/patrones:ro
      - ./logs:/app/logs
      - ./registros:/app/registros
    network_mode: host
```

| # | Subtarea | Descripción |
|---|----------|-------------|
| 1.2.1 | Servicio `bot-ax` | Build desde Dockerfile, volúmenes para datos persistentes |
| 1.2.2 | Perfiles | `docker compose --profile dev up` (modo interactivo) vs `production` (headless) |
| 1.2.3 | `network_mode: host` | Necesario para que PyAutoGUI acceda a la pantalla del host |

**Archivos afectados:** `docker-compose.yml` (nuevo).

### Tarea 1.3 — CI/CD (GitHub Actions)

```yaml
# Workflow de integracion continua para Bot AX Contable.
#
# Ejecuta analisis estatico (ruff), verificacion de tipos (mypy)
# y pruebas unitarias (pytest) en cada push y PR.
# Garantiza que ningun cambio rompa la base antes de llegar a produccion.

name: CI
on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -e ".[dev]"
      - run: ruff check src/
      - run: mypy src/
      - run: pytest --cov --cov-fail-under=80
```

| # | Subtarea | Descripción |
|---|----------|-------------|
| 1.3.1 | `ci.yml` | Lint → typecheck → test → coverage en push y PR |
| 1.3.2 | `tag.yml` | Auto-tag semver al hacer merge a main |

**Archivos afectados:** `.github/workflows/ci.yml`, `.github/workflows/tag.yml`.

### Tarea 1.4 — Desacoplar rutas de los `.bat`

```batch
@echo off
title Bot AX Contable - Lanzador
:: Usar %~dp0 para obtener la raiz del proyecto independientemente
:: de la unidad de red donde este montado (H:, G:, etc.)
cd /d "%~dp0"
if errorlevel 1 (
    echo ERROR: No se pudo acceder a la carpeta del proyecto.
    pause
    exit /b 1
)
```

| # | Subtarea | Descripción |
|---|----------|-------------|
| 1.4.1 | Reemplazar `H:\...` por `%~dp0` | El batch funciona desde cualquier unidad |
| 1.4.2 | Detectar Python automáticamente | Usar `where python` en vez de ruta fija |

**Archivos afectados:** `Lanzar_Bot.bat`, `Lanzar_Bot_Registro.bat`.

---

## Fase 2: Refactor del Core — Calidad de Código

**Objetivo:** Eliminar duplicación de resolución de rutas en 3 archivos distintos, desacoplar el monolito `engine.py` (449 líneas) en clases con responsabilidad única, y tipar correctamente todo el código.  
**Racionalidad:** `engine.py` mezcla carga de config, blacklist, scroll, procesamiento de diarios, safety check, logging y manejo de errores. Es imposible testear unitariamente. `config.py`, `logger.py` y `event_log.py` resuelven `BASE_DIR` con el mismo cálculo duplicado.

### Tarea 2.1 — Unificar resolución de rutas

```python
"""Resolución centralizada de rutas del proyecto Bot AX Contable.

PROBLEMA ORIGINAL:
    config.py, logger.py y event_log.py calculan BASE_DIR por separado,
    cada uno con su propia funcion os.path.dirname(...). Esto:
    1. Duplica logica fragil (si se mueve un archivo, los otros fallan)
    2. Dificulta cambiar la estructura de directorios
    3. Impide centralizar validaciones (ej: que patrones/ exista)

SOLUCION:
    Un unico modulo _paths.py que expone funciones puras de resolucion.
    Todos los demas modulos importan desde aqui.
"""

from pathlib import Path
from typing import Final

# Directorio de este archivo: src/core/
_CORE_DIR: Final[Path] = Path(__file__).resolve().parent

# Raiz del proyecto: src/core/ -> src/ -> raiz
PROJECT_ROOT: Final[Path] = _CORE_DIR.parent.parent

# Directorios derivados
PATRONES_DIR: Final[Path] = PROJECT_ROOT / "patrones"
LOGS_DIR: Final[Path] = PROJECT_ROOT / "logs"
CAPTURAS_DIR: Final[Path] = LOGS_DIR / "capturas"
CONFIG_FILE: Final[Path] = PROJECT_ROOT / "config_sectores.json"
BLACKLIST_FILE: Final[Path] = PROJECT_ROOT / "blacklist.json"
```

| # | Subtarea | Descripción |
|---|----------|-------------|
| 2.1.1 | Crear `src/core/_paths.py` | Paths con `pathlib`, tipado `Final` |
| 2.1.2 | Refactor `config.py` | Importar `PATRONES_DIR`, `CONFIG_FILE` desde `_paths` |
| 2.1.3 | Refactor `logger.py` | Importar `LOGS_DIR` desde `_paths` |
| 2.1.4 | Refactor `event_log.py` | Importar `_EVENTS_FILE` path desde `_paths` |
| 2.1.5 | Refactor `vision.py` | Usar `CAPTURAS_DIR` desde `_paths` |

**Archivos afectados:** `src/core/_paths.py` (nuevo), `src/core/config.py`, `src/core/logger.py`, `src/core/event_log.py`, `src/services/vision.py`.

### Tarea 2.2 — Extraer `ScrollManager`

```python
"""Gestor de scroll para el Sector C del Bot AX Contable.

Aislar la logica de scroll del ciclo principal es necesario porque:
1. El scroll tiene su propio ciclo de reintentos (3 intentos max)
2. Tiene dos modos de operacion (boton vs fallback clic/tecla)
3. Requiere limpiar la cache de posiciones procesadas tras cada scroll
4. Es un punto frecuente de fallo (el boton Avanzar_Abajo.png
   se detecta con confianza 0.7, lo que causa falsos negativos)

Al separarlo, podemos testear unitariamente cada modo de scroll
y ajustar las confianzas sin tocar el ciclo principal.
"""

import time
import pyautogui as gui
from typing import Optional, Tuple
from src.core.config import BTN_ABAJO
from src.core.event_log import event_log


class ScrollManager:
    """Gestiona la operacion de scroll en el Sector C.

    Attributes:
        sector_scroll: Region donde buscar el boton de scroll [x, y, w, h].
        max_intentos: Numero maximo de intentos de scroll (default: 3).
        click_por_intento: Veces que se hace clic en el boton (default: 1).
    """

    def __init__(
        self,
        sector_scroll: Optional[Tuple[int, int, int, int]] = None,
        max_intentos: int = 3,
        clicks_por_intento: int = 1,
    ) -> None:
        self.sector_scroll = sector_scroll
        self.max_intentos = max_intentos
        self.clicks_por_intento = clicks_por_intento

    def realizar_scroll(self, intento: int) -> str:
        """Ejecuta un scroll, primero con boton, luego fallback.

        Args:
            intento: Numero de intento actual (1-indexado).

        Returns:
            str: Metodo usado ("boton", "click", "pgdn") o "fallo".

        Raises:
            No lanza excepciones; captura errores internamente y
            retorna el resultado como string para que el llamador
            decida como proceder.
        """
        # Intento principal: buscar boton en sector
        try:
            pos = gui.locateCenterOnScreen(
                BTN_ABAJO,
                region=self.sector_scroll,
                confidence=0.7,
                grayscale=True
            )
            if pos:
                self._click_boton(pos)
                return "boton"
        except Exception:
            pass

        # Fallback 1: clic + scroll en el borde del Sector A
        try:
            self._fallback_click_scroll()
            return "click"
        except Exception:
            pass

        # Fallback 2: tecla Page Down
        gui.press("pgdn")
        return "pgdn"

    def _click_boton(self, pos: Tuple[int, int]) -> None:
        """Hace clic en el boton de scroll encontrado."""
        gui.moveTo(pos[0], pos[1], duration=0.2)
        for _ in range(self.clicks_por_intento):
            gui.click()
            time.sleep(0.1)
        time.sleep(1.5)

    def _fallback_click_scroll(self) -> None:
        """Realiza scroll mediante clic + rueda en el borde inferior del sector."""
        # Si no hay sector_scroll, no podemos hacer click en el borde
        if not self.sector_scroll:
            raise RuntimeError("No hay sector_scroll definido")
        gui.moveTo(
            self.sector_scroll[0] + self.sector_scroll[2] // 2,
            self.sector_scroll[1] + self.sector_scroll[3] - 10,
        )
        gui.click()
        time.sleep(0.2)
        gui.scroll(-10)
```

| # | Subtarea | Descripción |
|---|----------|-------------|
| 2.2.1 | Crear `src/core/scroll.py` | Clase `ScrollManager` con métodos `realizar_scroll()`, `_click_boton()`, `_fallback_click_scroll()` |
| 2.2.2 | Actualizar `engine.py` | Reemplazar bloque de scroll inline por `ScrollManager` |

**Archivos afectados:** `src/core/scroll.py` (nuevo), `src/core/engine.py`.

### Tarea 2.3 — Extraer `DiarioProcessor`

```python
"""Procesador individual de diarios contables.

Encapsula el flujo completo de registrar UN diario:
    checkbox -> menu Registrar -> confirmar -> esperar resultado

SEPARACIÓN DE RESPONSABILIDADES:
    Antes: engine.py hacia todo (buscar checkbox, click menu,
    esperar, decidir resultado) en el mismo bucle while.

    Ahora: DiarioProcessor recibe coordenadas de un checkbox y
    ejecuta el pipeline completo, retornando un resultado
    estandarizado ("exito", "error", "cancelado", "timeout").

BENEFICIO:
    Podemos testear el pipeline completo sin ejecutar el bot real,
    simplemente mockeando pyautogui y pytesseract.
"""

from typing import Optional, Tuple
from src.services.vision import (
    buscar_y_clickear,
    esperar_resultado_registro,
    leer_id_diario,
    normalizar_id_diario,
    capturar_pantalla_error,
)
from src.core.config import BTN_MENU, BTN_CONFIRM, CHK_MARCADO, IMG_ERROR


class DiarioProcessor:
    """Procesa un diario desde su checkbox hasta el resultado.

    Attributes:
        sector_b: Region del menu contextual [x, y, w, h].
        sector_a: Region de checkboxes [x, y, w, h] (para esperar resultado).
    """

    def __init__(
        self,
        sector_b: Optional[Tuple[int, int, int, int]] = None,
        sector_a: Optional[Tuple[int, int, int, int]] = None,
    ) -> None:
        self.sector_b = sector_b
        self.sector_a = sector_a

    def procesar(
        self,
        coord_checkbox: Tuple[int, int],
        stop_event=None,
    ) -> Tuple[str, str]:
        """Ejecuta el pipeline completo para un diario.

        Args:
            coord_checkbox: Centro (x, y) del checkbox a procesar.
            stop_event: Evento de detencion externa.

        Returns:
            Tuple[str, str]: (resultado, id_normalizado)
                resultado en ("exito", "error", "cancelado", "timeout_menu", "timeout_confirm").
        """
        id_bruto = leer_id_diario(coord_checkbox)
        id_normalizado = normalizar_id_diario(id_bruto)

        # Click en checkbox
        gui.moveTo(coord_checkbox[0], coord_checkbox[1], duration=0.5)
        gui.click()
        time.sleep(1)

        # Menu Registrar
        encontrado = buscar_y_clickear(BTN_MENU, self.sector_b, timeout=30, stop_event=stop_event)
        if not encontrado:
            return ("timeout_menu", id_normalizado)

        # Confirmar
        encontrado = buscar_y_clickear(BTN_CONFIRM, timeout=20, confidence=0.8, stop_event=stop_event)
        if not encontrado:
            return ("timeout_confirm", id_normalizado)

        # Esperar resultado
        resultado = esperar_resultado_registro(
            CHK_MARCADO, IMG_ERROR, self.sector_a,
            timeout=3600, stop_event=stop_event
        )
        return (resultado or "timeout", id_normalizado)
```

| # | Subtarea | Descripción |
|---|----------|-------------|
| 2.3.1 | Crear `src/core/processor.py` | Clase `DiarioProcessor` con método `procesar()` |
| 2.3.2 | Mover `registrar_log()` | Función helper de logging de resultados |

**Archivos afectados:** `src/core/processor.py` (nuevo), `src/core/engine.py`.

### Tarea 2.4 — Extraer `BlacklistManager`

```python
"""Gestor de lista negra de diarios con error.

PROBLEMA ORIGINAL:
    La blacklist se maneja como una lista de strings en engine.py,
    con carga/serializacion inline. Si dos hilos acceden (aunque hoy
    no los hay), hay race conditions. No hay metodo para limpiar
    o verificar pertenencia de forma limpia.

SOLUCION:
    Clase dedicada con interfaz clara (load, add, contains, remove, clear)
    y lock thread-safe para futuro uso concurrente.
"""

import json
import threading
from typing import List, Optional
from src.core._paths import BLACKLIST_FILE


class BlacklistManager:
    """Gestiona la lista negra de IDs de diarios con error persistente.

    Thread-safe: usa un lock RLock para operaciones de lectura/escritura.

    Usage:
        bl = BlacklistManager()
        bl.load()
        if not bl.contains("00327946"):
            bl.add("00327946")
        bl.save()
    """

    def __init__(self, filepath: Optional[str] = None) -> None:
        self._filepath = filepath or str(BLACKLIST_FILE)
        self._items: List[str] = []
        self._lock = threading.RLock()

    def load(self) -> None:
        """Carga la blacklist desde el archivo JSON.

        Si el archivo no existe o esta corrupto, inicializa lista vacia.
        Nunca lanza excepciones para no interrumpir el bot.
        """
        # ... implementation
```

| # | Subtarea | Descripción |
|---|----------|-------------|
| 2.4.1 | Crear `src/core/blacklist.py` | Clase con load, add, contains, remove, clear, save |
| 2.4.2 | Thread-safe | RLock para operaciones concurrentes |

**Archivos afectados:** `src/core/blacklist.py` (nuevo), `src/core/engine.py`.

### Tarea 2.5 — Extraer `SafetyGuard`

```python
"""Guardia de seguridad que monitorea formularios abiertos en AX.

Ejecuta en un hilo separado verificando periodicamente si aparece
el patron Formularios_Abiertos.png en pantalla. Si se detecta,
detiene el bot inmediatamente para evitar operaciones sobre datos
inconsistentes.

Esto es CRITICO porque:
    - Si un formulario queda abierto de una sesion anterior,
      los clicks del bot pueden caer en el lugar equivocado
    - Puede registrar asientos en el periodo contable incorrecto
    - Es una validacion de seguridad exigida por la operacion
"""

import threading
import time
import pyautogui as gui
from src.core.config import IMG_FORMULARIOS
from src.core.event_log import event_log


class SafetyGuard:
    """Monitor de seguridad para formularios abiertos."""

    def __init__(self, stop_event: threading.Event, check_interval: float = 2.0):
        self.stop_event = stop_event
        self.check_interval = check_interval
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Inicia el monitoreo en un hilo daemon."""
        self._thread = threading.Thread(target=self._monitor, daemon=True)
        self._thread.start()

    def _monitor(self) -> None:
        """Bucle de verificacion periodica."""
        while not self.stop_event.is_set():
            try:
                if gui.locateOnScreen(IMG_FORMULARIOS, confidence=0.8, grayscale=True):
                    event_log("formulario_abierto_detectado")
                    self.stop_event.set()
                    break
            except Exception:
                pass
            time.sleep(self.check_interval)
```

| # | Subtarea | Descripción |
|---|----------|-------------|
| 2.5.1 | Crear `src/core/safety.py` | Clase `SafetyGuard` con hilo daemon |
| 2.5.2 | Integrar en Orchestrator | Iniciar al comenzar el ciclo |

**Archivos afectados:** `src/core/safety.py` (nuevo), `src/core/engine.py`.

### Tarea 2.6 — Refactor `engine.py` → `Orchestrator`

```python
"""Orquestador principal del ciclo de vida del Bot AX Contable.

RESPONSABILIDAD UNICA:
    Coordinar las sub-operaciones (scroll, procesamiento, blacklist,
    safety) sin implementar ninguna de ellas.

ANTES (engine.py, 449 lineas):
    - Cargaba config
    - Manejaba blacklist
    - Hacia scroll
    - Procesaba diarios
    - Verificaba safety
    - Escribia logs
    - Todo en un unico bucle while con if anidados

DESPUES (Orchestrator + ScrollManager + DiarioProcessor + ...):
    - Orchestrator.run() delega cada preocupacion en su clase
    - Cada clase es testeable independientemente
    - El ciclo principal se lee como una secuencia de pasos claros
"""


class Orchestrator:
    """Coordina el ciclo completo de registro de diarios."""

    def __init__(
        self,
        scroll_manager: ScrollManager,
        diario_processor: DiarioProcessor,
        blacklist: BlacklistManager,
        safety_guard: SafetyGuard,
        log_callback=None,
        stop_event=None,
        pause_event=None,
    ):
        # ... dependency injection

    def run(self) -> bool:
        """Ejecuta el ciclo principal.

        Returns:
            bool: True si finalizo normalmente, False si error critico.
        """
        # 1. Validar pre-requisitos (Tesseract, sectores)
        # 2. Cargar config y blacklist
        # 3. Iniciar SafetyGuard
        # 4. Bucle: buscar checkbox -> procesar -> scroll
        # 5. Retornar resultado
```

| # | Subtarea | Descripción |
|---|----------|-------------|
| 2.6.1 | Crear `src/core/orchestrator.py` | Clase `Orchestrator` con inyección de dependencias |
| 2.6.2 | Reducir `engine.py` | Fachada que construye dependencias y llama a `Orchestrator.run()` |
| 2.6.3 | `run_bot()` permanece | Como API pública para las GUIs, pero ahora es delegación simple |

**Archivos afectados:** `src/core/orchestrator.py` (nuevo), `src/core/engine.py`.

---

## Fase 3: Testing Integral

**Objetivo:** Pasar de ~30% a 80%+ de cobertura, eliminar hacks de mockeo (`BOT_AX_TEST_MODE`, `types.ModuleType`).  
**Racionalidad:** Los tests actuales usan un hack frágil (`os.environ["BOT_AX_TEST_MODE"] = "1"` + `vision.pyautogui = types.ModuleType(...)`) que no escala. No hay tests del core (`engine.py`), solo de `config.py` y `normalizar_id_diario()`.

### Tarea 3.1 — `conftest.py` con fixtures

```python
"""Fixtures compartidos para todos los tests del Bot AX Contable.

Proporciona:
    - tmp_config: crea config_sectores.json temporal con datos validos
    - tmp_blacklist: crea blacklist.json temporal
    - mock_pyautogui: parchea todas las funciones de pyautogui usadas
    - mock_tesseract: parchea pytesseract.image_to_string

USO EN LUGAR DEL HACK ANTERIOR:
    En vez de hacer:
        os.environ["BOT_AX_TEST_MODE"] = "1"
        import types
        vision.pyautogui = types.ModuleType("pyautogui")

    Ahora se hace:
        @pytest.mark.usefixtures("mock_pyautogui")
        def test_algo():
            ...
"""

import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def mock_pyautogui():
    """Parchea todas las funciones de pyautogui usadas por el bot.

    Esto evita que los tests muevan el mouse real o hagan capturas
    de pantalla durante la ejecucion de pruebas unitarias.
    """
    patcher = patch("pyautogui.locateCenterOnScreen", return_value=(100, 100))
    patcher.start()
    yield
    patcher.stop()
```

| # | Subtarea | Descripción |
|---|----------|-------------|
| 3.1.1 | `tmp_config` fixture | Crea archivo temporal, yield ruta, cleanup automático |
| 3.1.2 | `tmp_blacklist` fixture | Ídem con blacklist.json |
| 3.1.3 | `mock_pyautogui` fixture | `unittest.mock.patch` para `locateCenterOnScreen`, `locateOnScreen`, `locateAllOnScreen`, `screenshot`, `click`, `moveTo`, `press`, `scroll` |
| 3.1.4 | `mock_tesseract` fixture | `pytesseract.image_to_string` → retorna ID falso |

**Archivos afectados:** `tests/conftest.py` (nuevo).

### Tarea 3.2 — Refactor `test_vision.py`

| # | Subtarea | Descripción |
|---|----------|-------------|
| 3.2.1 | Eliminar `BOT_AX_TEST_MODE` | Remover parche de entorno y `types.ModuleType` |
| 3.2.2 | Usar `mock_pyautogui` | Decorar tests con la fixture |
| 3.2.3 | Agregar tests de `capturar_pantalla_error()` | Verificar que guarda archivo en directorio correcto |
| 3.2.4 | Agregar tests de `buscar_y_clickear()` | Verificar timeout, coordenadas correctas, wait_only |

**Archivos afectados:** `tests/test_vision.py`.

### Tarea 3.3 — Tests para `_paths.py`

| # | Subtarea | Descripción |
|---|----------|-------------|
| 3.3.1 | `test_project_root()` | Verificar que apunta a raíz del repo |
| 3.3.2 | `test_patrones_dir_exists()` | Verificar que `patrones/` existe |
| 3.3.3 | `test_rutas_son_absolutas()` | Todos los paths retornados son absolutos |

**Archivos afectados:** `tests/test_paths.py` (nuevo).

### Tarea 3.4 — Tests para `ScrollManager`

```python
"""Tests unitarios para ScrollManager.

Escenarios:
    1. Boton encontrado en sector → scroll via clic en boton
    2. Boton NO encontrado en sector → fallback click + rueda
    3. Sin sector_scroll definido → fallback pgdn
    4. Maximo de intentos agotado → retorna False
"""

class TestScrollManager:
    def test_scroll_con_boton(self, mock_pyautogui):
        """Verifica que usa el boton cuando esta disponible."""
        with patch("pyautogui.locateCenterOnScreen", return_value=(200, 500)):
            sm = ScrollManager(sector_scroll=(0, 0, 100, 100))
            resultado = sm.realizar_scroll(1)
            assert resultado == "boton"

    def test_scroll_fallback_click(self, mock_pyautogui):
        """Verifica fallback a click+rueda cuando no hay boton."""
        with patch("pyautogui.locateCenterOnScreen", return_value=None):
            sm = ScrollManager(sector_scroll=(0, 0, 100, 100))
            resultado = sm.realizar_scroll(1)
            assert resultado in ("click", "pgdn")
```

| # | Subtarea | Descripción |
|---|----------|-------------|
| 3.4.1 | `test_scroll_con_boton()` | Mock locateCenterOnScreen → coordenadas válidas |
| 3.4.2 | `test_scroll_fallback()` | Mock locateCenterOnScreen → None |
| 3.4.3 | `test_scroll_sin_sector()` | ScrollManager sin sector → fallback pgdn |
| 3.4.4 | `test_scroll_cache_clear()` | Verificar que limpiar caché tras scroll no falla |

**Archivos afectados:** `tests/test_scroll.py` (nuevo).

### Tarea 3.5 — Tests para `BlacklistManager`

| # | Subtarea | Descripción |
|---|----------|-------------|
| 3.5.1 | `test_load_empty()` | Archivo inexistente → lista vacía |
| 3.5.2 | `test_load_with_data()` | Archivo con 3 IDs → lista con 3 IDs |
| 3.5.3 | `test_add_and_persist()` | Agregar ID → verificar en disco |
| 3.5.4 | `test_contains()` | Verificar pertenencia |
| 3.5.5 | `test_remove()` | Eliminar ID → ya no está en lista |
| 3.5.6 | `test_clear()` | Limpiar → lista vacía y archivo limpio |
| 3.5.7 | `test_corrupt_json()` | JSON malformado → lista vacía sin crash |
| 3.5.8 | `test_thread_safety()` | 2 hilos agregando concurrentemente → sin race conditions |

**Archivos afectados:** `tests/test_blacklist.py` (nuevo).

### Tarea 3.6 — Tests para `Orchestrator` (integración)

```python
"""Tests de integracion para el ciclo completo del Orchestrator.

SIMULACION DE CICLO REAL:
    Mockeamos pyautogui y pytesseract para simular:
    - Exito: checkbox → menu → confirmar → pop-up exito
    - Error AX: checkbox → menu → confirmar → pop-up error
    - Timeout menu: checkbox → NO encuentra menu
    - Cancelacion: stop_event activado durante el ciclo

    Cada test verifica no solo el resultado final sino tambien
    que se llamaron los metodos correctos de event_log.
"""

class TestOrchestrator:
    def test_ciclo_exitoso(self, mock_pyautogui, mock_tesseract, tmp_config):
        """Simula un ciclo completo exitoso."""
        orchestrator = Orchestrator(...)
        resultado = orchestrator.run()
        assert resultado is True

    def test_ciclo_con_error(self, mock_pyautogui, mock_tesseract, tmp_config):
        """Simula un error de registro en AX."""
        # Configurar mock para que esperar_resultado_registro retorne "error"
        ...
        assert "00327946" in blacklist._items

    def test_cancelacion_por_stop_event(self):
        """Verifica que el bot responde a stop_event."""
        stop_event = threading.Event()
        # ... iniciar bot en thread
        stop_event.set()
        # ... verificar que se detiene en < 2 segundos
```

| # | Subtarea | Descripción |
|---|----------|-------------|
| 3.6.1 | `test_ciclo_exitoso()` | Pipeline completo con éxito |
| 3.6.2 | `test_ciclo_error_ax()` | Error → blacklist actualizada |
| 3.6.3 | `test_timeout_menu()` | Menu no encontrado → error controlado |
| 3.6.4 | `test_cancelacion_por_esc()` | Stop event → detención limpia |
| 3.6.5 | `test_formularios_abiertos()` | SafetyGuard detecta → bot se detiene |

**Archivos afectados:** `tests/test_orchestrator.py` (nuevo).

### Tarea 3.7 — Configuración de cobertura en `pyproject.toml`

| # | Subtarea | Descripción |
|---|----------|-------------|
| 3.7.1 | `[tool.coverage.run]` | `source = ["src"]`, `branch = true`, `omit = ["src/ui/*"]` (GUI difícil de testear) |
| 3.7.2 | `[tool.coverage.report]` | `fail_under = 80`, `show_missing = true`, `exclude_lines = ["pragma: no cover", "if __name__ == \"__main__\""]` |

---

## Fase 4: Resiliencia y Monitoreo

**Objetivo:** Que el bot no solo registre errores, sino que alerte y se recupere automáticamente cuando sea posible.  
**Racionalidad:** Hoy `event_log` escribe a `events.jsonl` silenciosamente. Si el bot falla a las 3 AM, no hay manera de saberlo hasta la mañana siguiente. Un sistema de alertas permite reacción inmediata.

### Tarea 4.1 — Sistema de alertas en `event_log`

```python
"""Sistema de notificaciones para eventos criticos del Bot AX Contable.

ARQUITECTURA:
    Se extiende event_log() con un patron Observer:
    - Cualquier modulo puede registrarse como alerter via
      event_log.register_alerter(callback)
    - Cuando ocurre un evento critico, se notifica a todos los alerters
    - Alerters built-in: ConsoleAlerter (stderr), SlackAlerter (webhook)

    Esto permite en el futuro agregar Telegram, email, SMS sin
    modificar el core del bot.
"""

from typing import Callable, List


class EventLogger:
    """Logger de eventos con soporte de alerters."""

    def __init__(self):
        self._alerters: List[Callable] = []

    def register_alerter(self, callback: Callable) -> None:
        """Registra un callback para eventos criticos.

        El callback recibe el dict del evento. Debe ser rápido
        y nunca lanzar excepciones.
        """
        self._alerters.append(callback)

    def __call__(self, event_type: str, **fields) -> None:
        """Registra un evento y notifica a alerters si es critico."""
        # ... escribir JSONL (logica existente) ...
        if event_type in ("result_error", "failsafe_triggered", "timeout_extremo"):
            for alerter in self._alerters:
                try:
                    alerter({"event": event_type, **fields})
                except Exception:
                    pass
```

| # | Subtarea | Descripción |
|---|----------|-------------|
| 4.1.1 | Refactor `event_log` | Convertir a clase `EventLogger` con registro de alerters |
| 4.1.2 | `ConsoleAlerter` | Escribe a stderr con timestamp |
| 4.1.3 | `SlackAlerter` | Envía webhook a Slack (opcional, desactivado por defecto) |
| 4.1.4 | Eventos críticos | Definir lista: `result_error`, `failsafe_triggered`, `timeout_extremo`, `formulario_abierto_detectado` |

**Archivos afectados:** `src/core/event_log.py`, `src/core/alerters.py` (nuevo).

### Tarea 4.2 — Heartbeat en `events.jsonl`

| # | Subtarea | Descripción |
|---|----------|-------------|
| 4.2.1 | Hilo heartbeat | Emitir `bot_heartbeat` cada 60s con timestamp, ciclo actual, memoria usada |
| 4.2.2 | Detectar stalled bot | Observer watchdog alerta si no hay heartbeat en > 120s |

**Archivos afectados:** `src/core/engine.py`, `src/core/orchestrator.py`.

### Tarea 4.3 — Política de retención de capturas

```python
def capturar_pantalla_error(id_diario: str = "global") -> Optional[str]:
    """Captura snapshot de pantalla en error, con retencion maxima.

    GESTION DE RETENCION:
        Mantiene un maximo de 50 capturas. Cuando se excede,
        elimina las mas antiguas. Esto evita que el directorio
        logs/capturas/ crezca sin control en ejecuciones largas.

    Args:
        id_diario: Identificador para nombrar el archivo.

    Returns:
        Ruta de la captura guardada, o None si falla.
    """
    from src.core._paths import CAPTURAS_DIR

    # Rotacion: max 50 archivos
    _rotar_capturas(CAPTURAS_DIR, max_files=50)
    # ... resto de la logica existente ...


def _rotar_capturas(directory: Path, max_files: int = 50) -> None:
    """Elimina capturas mas antiguas si se excede el maximo."""
    files = sorted(directory.glob("error_*.png"), key=lambda f: f.stat().st_mtime)
    while len(files) > max_files:
        files[0].unlink(missing_ok=True)
        files = files[1:]
```

| # | Subtarea | Descripción |
|---|----------|-------------|
| 4.3.1 | Añadir `_rotar_capturas()` | Función de limpieza FIFO |
| 4.3.2 | Llamar antes de guardar | En `capturar_pantalla_error()` |

**Archivos afectados:** `src/services/vision.py`.

### Tarea 4.4 — Daemonizar `observer_watch.py`

| # | Subtarea | Descripción |
|---|----------|-------------|
| 4.4.1 | Flag `--daemon` | Corre en background con `pythonw.exe` en Windows |
| 4.4.2 | Flag `--notify` | Notificaciones toast con `win10toast` en errores |
| 4.4.3 | Flag `--webhook` | Envía resumen a URL configurable |

**Archivos afectados:** `scripts/observer_watch.py`.

---

## Fase 5: Configuración y Seguridad

**Objetivo:** Validar configuración tempranamente con schema, eliminar secretos del código fuente, y soportar múltiples entornos.  
**Racionalidad:** `cargar_configuracion()` valida manualmente con condicionales. Cualquier campo nuevo requiere modificar la función. Pydantic da validación automática con mensajes de error claros.

### Tarea 5.1 — Validación con Pydantic

```python
"""Modelos de configuracion validados con Pydantic.

PROBLEMA ORIGINAL:
    cargar_configuracion() valida con if anidados:
        if not isinstance(val, (list, tuple)) or len(val) != 4:
            print("ERROR: 'key' debe ser una lista de 4 numeros")
    Esto es fragil, verboso y no da mensajes de error utiles.

SOLUCION:
    Modelos Pydantic con validacion automatica:
    - SectoresConfig: valida x>=0, y>=0, w>0, h>0
    - OCRConfig: valida offset dentro de rangos razonables
    - Config: modelo completo que agrupa todo
"""

from pydantic import BaseModel, Field, model_validator
from typing import Optional


class SectorRegion(BaseModel):
    """Region rectangular en pantalla.

    Attributes:
        x: Coordenada X del borde superior izquierdo (>= 0).
        y: Coordenada Y del borde superior izquierdo (>= 0).
        w: Ancho en pixeles (> 0).
        h: Alto en pixeles (> 0).
    """
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    w: int = Field(gt=0)
    h: int = Field(gt=0)


class SectoresConfig(BaseModel):
    sector_a: SectorRegion
    sector_b: SectorRegion
    sector_scroll: Optional[SectorRegion] = None
    ocr_region_offset: Optional[tuple[int, int, int, int]] = None
```

| # | Subtarea | Descripción |
|---|----------|-------------|
| 5.1.1 | Definir modelos Pydantic | `SectorRegion`, `SectoresConfig`, `OCRConfig` |
| 5.1.2 | Refactor `cargar_configuracion()` | Usar `SectoresConfig.model_validate()` |
| 5.1.3 | Mensajes de error | Traducir errores de validación a español para el usuario |

**Archivos afectados:** `src/core/config.py`, `pyproject.toml` (dep: pydantic).

### Tarea 5.2 — Secretos en `.env`

| # | Subtarea | Descripción |
|---|----------|-------------|
| 5.2.1 | Variables sensibles | `TESSERACT_CMD`, `SLACK_WEBHOOK_URL`, `BOT_AX_LOG_LEVEL`, `BOT_AX_ENV` |
| 5.2.2 | `dotenv.load_dotenv()` | Ejecutar al inicio de `config.py` antes de cualquier uso |
| 5.2.3 | `.env` en `.gitignore` | Asegurar que `.env` no se commitée |

**Archivos afectados:** `src/core/config.py`, `.gitignore`.

### Tarea 5.3 — Perfiles de configuración

| # | Subtarea | Descripción |
|---|----------|-------------|
| 5.3.1 | `config_sectores.{env}.json` | Cargar según `BOT_AX_ENV` |
| 5.3.2 | Fallback | Si no existe archivo de perfil, cargar `config_sectores.json` base |

**Archivos afectados:** `src/core/config.py`.

---

## Fase 6: DevOps y Developer Experience

**Objetivo:** Estandarizar comandos con Makefile, automatizar hooks pre-commit, generar changelog automático.  
**Racionalidad:** Cada desarrollador hoy tiene que recordar comandos ad-hoc. No hay `make test`, `make lint`. El changelog se mantiene manualmente en README.

### Tarea 6.1 — `Makefile`

```makefile
# Makefile para Bot AX Contable
# ==============================
# Comandos estandarizados para desarrollo diario.
#
# USO:
#   make install    - Instala dependencias y hooks
#   make lint       - Ejecuta ruff (linter)
#   make format     - Formatea codigo con ruff
#   make typecheck  - Verifica tipos con mypy
#   make test       - Ejecuta tests con cobertura
#   make clean      - Limpia artefactos (__pycache__, .pyc)
#   make docker-build - Construye imagen Docker
#   make docker-run   - Ejecuta contenedor

.PHONY: install lint format typecheck test clean

install:
	pip install -e ".[dev]"
	pre-commit install

lint:
	ruff check src/ tests/ scripts/

format:
	ruff format src/ tests/ scripts/

typecheck:
	mypy src/

test:
	pytest --cov --cov-report=term-missing

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

docker-build:
	docker compose build

docker-run:
	docker compose up
```

| # | Subtarea | Descripción |
|---|----------|-------------|
| 6.1.1 | Crear `Makefile` | Targets: install, lint, format, typecheck, test, clean, docker |
| 6.1.2 | Documentar en README | Tabla de comandos make |

**Archivos afectados:** `Makefile` (nuevo).

### Tarea 6.2 — `CHANGELOG.md`

| # | Subtarea | Descripción |
|---|----------|-------------|
| 6.2.1 | Crear `CHANGELOG.md` | Formato keep-a-changelog con secciones: Added, Changed, Fixed, Removed |
| 6.2.2 | Migrar historial del README | Mover entradas históricas al changelog |

**Archivos afectados:** `CHANGELOG.md` (nuevo), `README.md`.

### Tarea 6.3 — Logging JSON estructurado

```python
class JSONFormatter(logging.Formatter):
    """Formatea logs como JSON para ingestion en sistemas de monitoreo.

    Cuando BOT_AX_LOG_FORMAT=json, cada linea de bot_ax.log sera
    un objeto JSON con timestamp ISO-8601, nivel, modulo y mensaje.
    Esto permite ingestion directa en Elasticsearch, Grafana Loki,
    o cualquier sistema de logs estructurados.
    """

    def format(self, record: logging.LogRecord) -> str:
        return json.dumps({
            "ts": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage(),
        }, ensure_ascii=False)
```

| # | Subtarea | Descripción |
|---|----------|-------------|
| 6.3.1 | Agregar `JSONFormatter` | `src/core/logger.py` |
| 6.3.2 | Detectar `BOT_AX_LOG_FORMAT` | Si es `json`, usar `JSONFormatter`; si no, usar formato texto actual |

**Archivos afectados:** `src/core/logger.py`.

---

## Fase 7: Performance

**Objetivo:** Reducir latencia en operaciones repetitivas (OCR) y hacer reintentos inteligentes.  
**Racionalidad:** En una sesión larga (cientos de diarios), el OCR se ejecuta sobre los mismos IDs múltiples veces si hay scroll. El timeout de 3600 segundos fijo para todos los resultados no distingue entre operaciones rápidas y lentas.

### Tarea 7.1 — Caché LRU para OCR

```python
from functools import lru_cache


def leer_id_diario(coord_checkbox: Tuple[int, int]) -> str:
    """Extrae el ID del diario con cache.

    CACHE LRU:
        Almacena los ultimos 128 IDs leidos por coordenada.
        Esto evita re-procesar OCR cuando el scroll devuelve
        las mismas filas a la vista.

    IMPORTANTE:
        La cache se limpia cuando se hace scroll (las coordenadas
        fisicas cambian), por lo que no hay riesgo de datos
        desactualizados.
    """
    return _leer_id_diario_impl(coord_checkbox)


@lru_cache(maxsize=128)
def _leer_id_diario_impl(coord: Tuple[int, int]) -> str:
    """Implementacion real con cache."""
    # ... logica original ...
```

| # | Subtarea | Descripción |
|---|----------|-------------|
| 7.1.1 | Refactor `leer_id_diario()` | Split en wrapper público + función interna `@lru_cache` |
| 7.1.2 | Limpiar caché en scroll | `_leer_id_diario_impl.cache_clear()` en `ScrollManager` |

**Archivos afectados:** `src/services/vision.py`.

### Tarea 7.2 — Timeouts configurables

| # | Subtarea | Descripción |
|---|----------|-------------|
| 7.2.1 | Agregar campos a defaults.py | `timeout_menu`, `timeout_confirm`, `timeout_resultado` |
| 7.2.2 | Configuración en JSON | Leer timeouts desde `config_sectores.json` si existen |
| 7.2.3 | Usar en `DiarioProcessor` | Timeout individual para cada paso del pipeline |

**Archivos afectados:** `src/bot_ax/config/defaults.py`, `src/core/config.py`, `src/core/processor.py`.

### Tarea 7.3 — Backoff exponencial en reintentos

```python
def _esperar_backoff(intento: int, base: float = 0.5) -> None:
    """Espera con backoff exponencial entre reintentos.

    Args:
        intento: Numero de intento actual (0-indexado).
        base: Tiempo base en segundos.

    Formula: base * (2 ** intento) + jitter aleatorio de 10%.

    Ejemplo:
        Intento 0: 0.5s
        Intento 1: 1.0s
        Intento 2: 2.0s
        Intento 3: 4.0s
    """
    import random
    tiempo = base * (2 ** intento)
    jitter = tiempo * 0.1 * random.random()
    time.sleep(tiempo + jitter)
```

| # | Subtarea | Descripción |
|---|----------|-------------|
| 7.3.1 | Crear helper `_esperar_backoff()` | En `src/core/scroll.py` y reutilizable |
| 7.3.2 | Usar en `ScrollManager` | Entre intentos de scroll |
| 7.3.3 | Usar en `buscar_y_clickear()` | Entre ciclos de búsqueda de patrón |

**Archivos afectados:** `src/core/scroll.py`, `src/services/vision.py`.

---

## Resumen de Archivos

### Archivos nuevos (21)

| Archivo | Fase | Propósito |
|---------|------|-----------|
| `pyproject.toml` | 0 | Empaquetado + tooling unificado |
| `requirements.txt` | 0 | Dependencias congeladas |
| `.env.example` | 0 | Plantilla de variables de entorno |
| `.pre-commit-config.yaml` | 0 | Hooks automáticos de calidad |
| `Dockerfile` | 1 | Containerización |
| `docker-compose.yml` | 1 | Orquestación de servicios Docker |
| `.github/workflows/ci.yml` | 1 | CI: lint + typecheck + test + coverage |
| `.github/workflows/tag.yml` | 1 | Auto-tagging semver |
| `src/core/_paths.py` | 2 | Resolución centralizada de rutas |
| `src/core/scroll.py` | 2 | Gestor de scroll |
| `src/core/processor.py` | 2 | Procesador individual de diarios |
| `src/core/blacklist.py` | 2 | Gestor de lista negra |
| `src/core/safety.py` | 2 | Guardia de seguridad (formularios) |
| `src/core/orchestrator.py` | 2 | Orquestador del ciclo principal |
| `src/core/alerters.py` | 4 | Sistema de notificaciones |
| `tests/conftest.py` | 3 | Fixtures compartidos para tests |
| `tests/test_paths.py` | 3 | Tests de resolución de rutas |
| `tests/test_scroll.py` | 3 | Tests unitarios de scroll |
| `tests/test_blacklist.py` | 3 | Tests de blacklist manager |
| `tests/test_orchestrator.py` | 3 | Tests de integración del ciclo |
| `Makefile` | 6 | Task runner para desarrollo |
| `CHANGELOG.md` | 6 | Historial de cambios |

### Archivos a modificar (15)

| Archivo | Fase | Cambio principal |
|---------|------|------------------|
| `src/core/config.py` | 0, 2, 5 | Migrar a env vars, usar `_paths`, validación Pydantic |
| `src/core/logger.py` | 2, 6 | Usar `_paths`, agregar `JSONFormatter` |
| `src/core/event_log.py` | 2, 4 | Usar `_paths`, refactor a clase con alerters |
| `src/core/engine.py` | 2 | Reducir a fachada que delega en Orchestrator |
| `src/services/vision.py` | 2, 4, 7 | Usar `_paths`, rotación capturas, caché LRU |
| `src/core/version.py` | 0 | Compatible con `pyproject.toml` dynamic version |
| `src/bot_ax/config/defaults.py` | 7 | Agregar timeouts configurables |
| `Lanzar_Bot.bat` | 1 | Usar `%~dp0`, detectar Python dinámicamente |
| `Lanzar_Bot_Registro.bat` | 1 | Ídem |
| `tests/test_config.py` | 3 | Usar fixtures de conftest |
| `tests/test_vision.py` | 3 | Eliminar hacks, usar mocks de conftest |
| `scripts/observer_watch.py` | 4 | Flags `--daemon`, `--notify`, `--webhook` |
| `.gitignore` | 5 | Agregar `.env` |
| `README.md` | 6 | Mover changelog a `CHANGELOG.md`, agregar tabla de comandos make |

### Archivos a eliminar (2)

| Archivo | Fase | Razón |
|---------|------|-------|
| `requirements-dev.txt` | 0 | Reemplazado por `pyproject.toml` `[project.optional-dependencies] dev` |
| `.githooks/` | 0 | Reemplazado por `.pre-commit-config.yaml` |

---

## Roadmap Temporal

```
Sprint 1 (Fundación)
├── Fase 0: pyproject.toml + .env + pre-commit
├── Fase 1: Docker + CI/CD
└── Fase 6: Makefile + CHANGELOG

Sprint 2 (Calidad Interna)
├── Fase 2: _paths.py + extract ScrollManager + BlacklistManager
└── Fase 3: conftest.py + tests de scroll + blacklist

Sprint 3 (Core + Testing)
├── Fase 2: DiarioProcessor + SafetyGuard + Orchestrator
└── Fase 3: tests de integración + cobertura 80%

Sprint 4 (Resiliencia + Performance)
├── Fase 4: Alerters + Heartbeat + Retención capturas
├── Fase 5: Pydantic validation + perfiles
└── Fase 7: Caché OCR + Backoff + Timeouts
```

---

*Fin del plan. Cada fase y tarea incluye el razonamiento (docstring argumentativo) que justifica por qué se hace, qué problema resuelve y cómo beneficia al proyecto a largo plazo.*
