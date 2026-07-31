# Plan de Implementación — Mejoras, Riesgos y Correcciones

> **Rama:** `docs/plan-implementacion-mejoras`
> **Versión:** 1.0
> **Fecha:** 2026-07-31
> **Base:** análisis de ContextMap (readiness 50/100), inspección de código fuente y `PLAN_MEJORA_PROFESIONAL.md`.

---

## 1. Resumen Ejecutivo

Este plan ordena, prioriza y convierte en tareas accionables los hallazgos del análisis del
proyecto **Bot AX Contable**. Se divide en tres categorías:

1. **Correcciones inmediatas** — bugs y deudas técnicas concretas que rompen la base hoy.
2. **Riesgos mitigables** — puntos de fragilidad identificados por ContextMap y por inspección.
3. **Mejoras estructurales** — profesionalización de la infraestructura (fases 0–7).

Cada tarea incluye: **objetivo**, **archivos afectados**, **criterio de aceptación** y
**verificación obligatoria** (pytest, ctxmap scan/build, readiness).

---

## 2. Correcciones Inmediatas (Prioridad Alta)

Estos defectos existen **hoy** y deben resolverse primero porque rompen o degradan el
desarrollo diario.

### C-1. Suite de tests rota — `tests/test_vision.py` no importa `vision`

- **Hallazgo:** `pytest --collect-only` falla con `ModuleNotFoundError: No module named 'vision'`.
  El test hace `import vision` (estructura antigua), pero el módulo real vive en
  `src/services/vision.py` desde el refactor `2aad23d`.
- **Impacto:** el protocolo de verificación obligatorio de AGENTS.md (`python -m pytest`)
  está roto en un 100% de la suite.
- **Acción:**
  1. Cambiar `import vision` → `from src.services.vision import normalizar_id_diario`.
  2. Eliminar el hack `os.environ["BOT_AX_TEST_MODE"]` y el mock `types.ModuleType`
     (ver C-3 / T-3.1).
  3. Ajustar el `sys.path.insert` para que apunte a la raíz del repo.
- **Archivos:** `tests/test_vision.py`
- **Aceptación:** `python -m pytest` pasa 100% (los 9 tests de config + 10 de visión).

### C-2. Import duplicado en `src/services/vision.py`

- **Hallazgo:** líneas 13–14:
  ```python
  from src.core.event_log import event_log
  from src.core.event_log import event_log
  ```
  Import duplicado (probable artefacto de merge).
- **Acción:** eliminar la línea duplicada.
- **Archivos:** `src/services/vision.py`
- **Aceptación:** `ruff check src/services/vision.py` sin errores de import.

### C-3. Hack de mockeo en tests (`BOT_AX_TEST_MODE` + `types.ModuleType`)

- **Hallazgo:** `tests/test_vision.py` mockea `pyautogui` sustituyendo el módulo a mano.
  Esto es frágil, no escala y no cubre los demás módulos.
- **Acción:** reemplazar por fixtures `unittest.mock.patch` en `tests/conftest.py`
  (ver T-3.1).
- **Archivos:** `tests/test_vision.py`, `tests/conftest.py` (nuevo)
- **Aceptación:** los tests no dependen de variables de entorno ni mutación de módulos.

### C-4. Directorio fantasma `src/bot_ax/` con solo `defaults.py` y `.pyc` huérfanos

- **Hallazgo:** `src/bot_ax/` contiene únicamente `config/defaults.py` (real) y
  35 archivos `.pyc` de módulos que ya no existen (`engine`, `registrador`,
  `blacklist`, `detector`, `ids`, `ocr`, etc.) tras el refactor.
- **Acción:**
  1. Mover `src/bot_ax/config/defaults.py` → `src/core/defaults.py` (o fusionar en
     `config.py`).
  2. Eliminar `src/bot_ax/` completo.
- **Archivos:** `src/bot_ax/` (eliminar), `src/core/defaults.py` (nuevo)
- **Aceptación:** no queda ningún `.pyc` huérfano en el repo (verificar con
  `git status --short`).

### C-5. Ruta de Tesseract hardcodeada con nombre de usuario

- **Hallazgo:** `src/core/config.py:20`:
  ```python
  r"C:\Users\jose.cespedes\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
  ```
  Rompe la ejecución en otra máquina / otro usuario.
- **Acción:** migrar a variable de entorno `TESSERACT_CMD` con fallback y documento
  en `.env.example` (ver T-0.3).
- **Archivos:** `src/core/config.py`, `.env.example` (nuevo)
- **Aceptación:** en otra máquina solo se configura `.env` (o env var), sin editar código.

### C-6. Lanzadores `.bat` con rutas fijas `H:\...` y `Python312\pythonw.exe`

- **Hallazgo:** `Lanzar_Bot.bat` y `Lanzar_Bot_Registro.bat` hardcodean la unidad
  `H:\` (Google Drive) y la ruta de Python 3.12.
- **Acción:** reemplazar por `%~dp0` para la raíz del proyecto y `where python` para
  resolver el intérprete (ver T-1.4).
- **Archivos:** `Lanzar_Bot.bat`, `Lanzar_Bot_Registro.bat`
- **Aceptación:** los `.bat` funcionan montados en cualquier unidad y con cualquier
  Python 3.11+ en `PATH`.

### C-7. `config_sectores.json` modificado sin commitear

- **Hallazgo:** el working tree tiene cambios en `config_sectores.json` (sectores
  recalibrados: `sector_a` de 33px → 297px de ancho, etc.) sin commit.
- **Acción:** decidir si es calibración de producción (commit en `main` vía PR) o
  ajuste local (quedarse en `.gitignore`). **No commitear por defecto.**
- **Archivos:** `config_sectores.json`
- **Aceptación:** el archivo se mantiene fuera del control de versiones o se commitea
  explícitamente con decisión documentada.

### C-8. `.githooks/pre-commit` con encoding roto y lógica frágil de bump

- **Hallazgo:** el hook shell contiene caracteres corruptos (`segǧn`, `��"`) y mezcla
  bump minor/patch según `ADDED`/`DELETED`, lo que puede inflar la versión
  (la versión actual ya es `00.08.01`).
- **Acción:** reemplazar por `.pre-commit-config.yaml` gestionado (ver T-0.4) y
  centralizar el bump en `bump_version.py`.
- **Archivos:** `.githooks/` (eliminar), `.pre-commit-config.yaml` (nuevo)
- **Aceptación:** `pre-commit run --all-files` funciona y el bump de versión es
  determinista.

### C-9. README desactualizado respecto a la estructura real

- **Hallazgo:** el README referencia módulos en la raíz que ya no existen
  (`app_gui.py`, `bot_main.py`, `vision.py`, `config.py`), pero ahora viven en `src/`.
- **Acción:** actualizar la sección "Estructura del proyecto", el "Uso" y el
  "Solución de problemas" con rutas `src/...`. Mover historial a `CHANGELOG.md`
  (ver T-6.2).
- **Archivos:** `README.md`, `CHANGELOG.md` (nuevo)
- **Aceptación:** el README refleja la estructura real y los comandos de uso.

---

## 3. Riesgos Identificados y Mitigación

### R-1. Archivos de alta complejidad (ContextMap)

- **Hallazgo:** `scripts/observer_analyze.py` (647 líneas), `src/ui/gui_classic.py`
  (605), `src/core/engine.py` (424), `src/services/vision.py` (327). Son las zonas de
  mayor riesgo de regresión.
- **Mitigación:** refactor incremental por SRP (ver Fase 2). Prioridad de lectura y
  cobertura de tests sobre estos 4 archivos.

### R-2. `engine.py` monolítico (424 líneas)

- **Hallazgo:** mezcla carga de config, blacklist, scroll, procesamiento de diarios,
  safety check, logging y manejo de errores. Es el riesgo funcional #1 del bot.
- **Mitigación:** extraer `ScrollManager`, `DiarioProcessor`, `BlacklistManager`,
  `SafetyGuard` y reducir `engine.py` a fachada del `Orchestrator`
  (ver T-2.2 → T-2.6).

### R-3. Resolución de rutas duplicada en 3 módulos

- **Hallazgo:** `config.py`, `logger.py` y `event_log.py` calculan `BASE_DIR` con el
  mismo patrón por separado (riesgo de drift si se mueve un archivo).
- **Mitigación:** crear `src/core/_paths.py` como fuente única (ver T-2.1).

### R-4. Sin CI → regresiones no detectadas

- **Hallazgo:** la suite ya está rota (`C-1`) y no hay CI que la haya bloqueado.
- **Mitigación:** GitHub Actions con ruff + mypy + pytest (ver T-1.3).

### R-5. Baja cobertura de tests

- **Hallazgo:** solo existen `tests/test_config.py` (9 tests) y `tests/test_vision.py`
  (10 tests). No hay tests de `engine.py`, `logger.py`, `event_log.py` ni GUIs.
- **Mitigación:** conftest con fixtures, tests de core (Fase 3), meta de cobertura ≥80%
  sobre `src/core/` y `src/services/` (excluyendo `src/ui/`).

### R-6. `config_sectores.json` / `blacklist.json` en `.gitignore` pero trackeados

- **Hallazgo:** están en `.gitignore` **y** en el índice de Git. El `gitignore` no surte
  efecto sobre archivos ya trackeados, generando confusión sobre qué commitear.
- **Mitigación:** decidir el modelo (configuración versionada vs local) y limpiar
  `.gitignore` acorde. Verificar con `git ls-files | grep -E "config_sectores|blacklist"`.

---

## 4. Mejoras por Fases (roadmap de implementación)

### Fase 0 — Fundación del Proyecto

| Tarea | Descripción | Archivos |
|-------|-------------|----------|
| T-0.1 | Crear `pyproject.toml` (PEP 621, `[project]`, `[tool.ruff]`, `[tool.mypy]`, `[tool.pytest.ini_options]`, `[tool.coverage]`) | `pyproject.toml` |
| T-0.2 | Generar `requirements.txt` desde pyproject | `requirements.txt` |
| T-0.3 | Variables de entorno + `.env.example` (`TESSERACT_CMD`, `BOT_AX_LOG_LEVEL`, `BOT_AX_ENV`) + `python-dotenv` | `.env.example`, `src/core/config.py` |
| T-0.4 | `.pre-commit-config.yaml` moderno (ruff, ruff-format, mypy, trailing-whitespace, check-json, check-yaml, end-of-file-fixer) y eliminar `.githooks/` | `.pre-commit-config.yaml` |

### Fase 1 — Infraestructura y Portabilidad

| Tarea | Descripción | Archivos |
|-------|-------------|----------|
| T-1.1 | `Dockerfile` reproducible (python:3.12-slim + tesseract + libgl) | `Dockerfile` |
| T-1.2 | `docker-compose.yml` con volúmenes persistentes | `docker-compose.yml` |
| T-1.3 | CI/CD GitHub Actions: ruff → mypy → pytest → coverage ≥80% | `.github/workflows/ci.yml`, `tag.yml` |
| T-1.4 | Desacoplar `.bat`: `%~dp0` + `where python` | `Lanzar_Bot.bat`, `Lanzar_Bot_Registro.bat` |

### Fase 2 — Refactor del Core (Calidad de Código)

| Tarea | Descripción | Archivos |
|-------|-------------|----------|
| T-2.1 | Crear `src/core/_paths.py` y refactorizar `config.py`, `logger.py`, `event_log.py`, `vision.py` para usarlo | `_paths.py` (nuevo), 4 módulos |
| T-2.2 | Extraer `ScrollManager` | `src/core/scroll.py` (nuevo) |
| T-2.3 | Extraer `DiarioProcessor` | `src/core/processor.py` (nuevo) |
| T-2.4 | Extraer `BlacklistManager` (thread-safe) | `src/core/blacklist.py` (nuevo) |
| T-2.5 | Extraer `SafetyGuard` (hilo daemon) | `src/core/safety.py` (nuevo) |
| T-2.6 | Crear `Orchestrator` y reducir `engine.py` a fachada | `src/core/orchestrator.py` (nuevo), `engine.py` |

**Restricción inmutable:** el refactor **no** puede alterar la lógica de las 6 reglas
del manual (`docs/manual_proceso_bot.md`): foco dirigido no destructivo, barrera de
último marcado, caché de posiciones, limpieza tras scroll, blacklist y confianza 0.85.

### Fase 3 — Testing Integral

| Tarea | Descripción | Archivos |
|-------|-------------|----------|
| T-3.1 | `tests/conftest.py` con fixtures (`tmp_config`, `tmp_blacklist`, `mock_pyautogui`, `mock_tesseract`) | `tests/conftest.py` (nuevo) |
| T-3.2 | Refactor `tests/test_vision.py` (eliminar hacks, cubrir `capturar_pantalla_error`, `buscar_y_clickear`) | `tests/test_vision.py` |
| T-3.3 | Tests de `_paths.py` | `tests/test_paths.py` (nuevo) |
| T-3.4 | Tests de `ScrollManager` | `tests/test_scroll.py` (nuevo) |
| T-3.5 | Tests de `BlacklistManager` (incl. thread-safety, JSON corrupto) | `tests/test_blacklist.py` (nuevo) |
| T-3.6 | Tests de integración del `Orchestrator` (éxito, error AX, timeout, cancelación, formularios) | `tests/test_orchestrator.py` (nuevo) |

### Fase 4 — Resiliencia y Monitoreo

| Tarea | Descripción | Archivos |
|-------|-------------|----------|
| T-4.1 | `EventLogger` con alerters (Observer: ConsoleAlerter, SlackAlerter opcional) | `src/core/event_log.py`, `src/core/alerters.py` (nuevo) |
| T-4.2 | Heartbeat cada 60s en `events.jsonl` + watchdog de stall | `src/core/engine.py`, `orchestrator.py` |
| T-4.3 | Retención de capturas (máx 50, FIFO) en `capturar_pantalla_error()` | `src/services/vision.py` |
| T-4.4 | Flags `--daemon`, `--notify`, `--webhook` en `observer_watch.py` | `scripts/observer_watch.py` |

### Fase 5 — Configuración y Seguridad

| Tarea | Descripción | Archivos |
|-------|-------------|----------|
| T-5.1 | Validación Pydantic (`SectorRegion`, `SectoresConfig`, `OCRConfig`) | `src/core/config.py` |
| T-5.2 | Secretos en `.env` (webhook Slack, Tesseract) y `.env` en `.gitignore` | `src/core/config.py`, `.gitignore` |
| T-5.3 | Perfiles de config por `BOT_AX_ENV` (`config_sectores.{env}.json`) | `src/core/config.py` |

### Fase 6 — DevOps y DX

| Tarea | Descripción | Archivos |
|-------|-------------|----------|
| T-6.1 | `Makefile` (install, lint, format, typecheck, test, clean, docker) | `Makefile` (nuevo) |
| T-6.2 | `CHANGELOG.md` (keep-a-changelog) y migrar historial del README | `CHANGELOG.md` (nuevo), `README.md` |
| T-6.3 | `JSONFormatter` para logging estructurado (`BOT_AX_LOG_FORMAT=json`) | `src/core/logger.py` |

### Fase 7 — Performance

| Tarea | Descripción | Archivos |
|-------|-------------|----------|
| T-7.1 | Caché LRU para `leer_id_diario()` + limpieza en scroll | `src/services/vision.py`, `src/core/scroll.py` |
| T-7.2 | Timeouts configurables (`timeout_menu`, `timeout_confirm`, `timeout_resultado`) | `src/core/defaults.py`, `config.py`, `processor.py` |
| T-7.3 | Backoff exponencial en reintentos | `src/core/scroll.py`, `src/services/vision.py` |

---

## 5. Orden de Ejecución Sugerido

```
Sprint 1 (Fundación + Correcciones)
├── C-1..C-9 (correcciones inmediatas)      ← bloquear antes de nada más
├── Fase 0 (pyproject.toml, .env, pre-commit)
└── Fase 6 parcial (CHANGELOG.md)

Sprint 2 (Calidad Interna)
├── Fase 2 parcial (_paths.py + ScrollManager + BlacklistManager)
└── Fase 3 parcial (conftest.py + test_scroll + test_blacklist)

Sprint 3 (Core + Testing)
├── Fase 2 (DiarioProcessor + SafetyGuard + Orchestrator)
└── Fase 3 (tests de integración + cobertura ≥80%)

Sprint 4 (Resiliencia + Infra)
├── Fase 1 (Docker + CI/CD)
├── Fase 4 (alerters + heartbeat + retención)
└── Fase 5 + 7 (Pydantic + perfiles + caché OCR + backoff)
```

---

## 6. Criterios de Verificación por Hito

Tras cada hito completado ejecutar (obligatorio según AGENTS.md):

```bash
# 1. Suite de pruebas unitarias (debe pasar 100%)
python -m pytest

# 2. Linter y type checker (si se adoptaron)
ruff check src/ tests/ scripts/
mypy src/

# 3. Escaneo del mapa de contexto
python -m context_map.cli scan .

# 4. Reconstrucción del Vault y el Brief
python -m context_map.cli build --clean --brief

# 5. Auditoría de readiness (objetivo: pasar de 50 → 80+)
python -m context_map.cli check .
```

---

## 7. Indicadores de Éxito

| Métrica | Antes | Después |
|---------|-------|---------|
| Readiness (ctxmap check) | 50/100 | ≥80/100 |
| `python -m pytest` | ROTO (1 error de import) | 100% passing |
| Cobertura de tests | ~0% (core sin tests) | ≥80% (src/core + src/services) |
| Archivos >400 líneas | 4 | ≤1 (observer_analyze.py pendiente de refactor) |
| Dependencia de ruta `H:\` | 2 `.bat` + 1 `config.py` | 0 |
| Secretos/rutas de usuario en código | `jose.cespedes` en Tesseract | 0 (env vars) |

---

*Fin del plan. Generado a partir del análisis de ContextMap + inspección de código.
La implementación debe respetar el manual inmutable (`docs/manual_proceso_bot.md`).*
