# Auditoría de Proyecto — Bot AX Contable

> **Fecha:** 2026-06-12
> **Versión auditada:** v-00.01.44
> **Analista:** José Céspedes — Casino Express / Lo Águila

---

## 1. Resumen Ejecutivo

El proyecto **Bot AX Contable** es un bot de automatización para **Microsoft Dynamics AX** que registra diarios contables mediante reconocimiento de imágenes (template matching con PyAutoGUI) y OCR (Tesseract). El código es funcional y ha evolucionado orgánicamente desde una versión más antigua (v2.0) hasta la actual arquitectura modular plana.

**Estado general:** ✅ Funcional pero con deuda técnica significativa. El bot cumple su propósito pero la estructura del proyecto no es escalable, mantenible ni profesional.

| Aspecto | Evaluación |
|---------|-----------|
| Funcionalidad | ✅ Cumple objetivo |
| Estabilidad | 🟡 Media — depende de entorno visual |
| Mantenibilidad | 🔴 Baja — código plano, mezcla de responsabilidades |
| Testeabilidad | 🟡 Media — tests limitados |
| Escalabilidad | 🔴 Baja — sin estructura de paquete |
| Documentación | 🟡 Media — README completo pero sin docs técnicos |
| CI/CD | 🟡 Parcial (GitHub Actions OpenCode) |
| Versionado | ✅ Funcional con auto-bump |

---

## 2. Estructura Actual del Proyecto

```
Bot_AX_Contable/                    # 2,357 líneas Python total
├── bot_main.py          (331 lns)  # 🟡 Ciclo principal del bot
├── vision.py            (288 lns)  # 🔴 Monolito: OCR + matching + IDs + screenshots + helpers
├── app_gui.py           (758 lns)  # 🟢 GUI moderna (Tkinter)
├── bot_ax_registro.py   (244 lns)  # 🔴 GUI legacy/duplicada (Gemini Engine)
├── config.py            (102 lns)  # 🟡 Constantes + carga JSON + validación Tesseract
├── logger.py            (72 lns)   # 🟢 Logging estructurado
├── _version.py          (40 lns)   # 🟢 Versión y git SHA
├── bump_version.py      (62 lns)   # 🟢 Auto-bump
├── setup_areas.py       (83 lns)   # 🟢 Selector visual de sectores
├── test_ocr.py          (10 lns)   # 🟢 Verificación Tesseract
├── debug_ocr.py         (39 lns)   # 🔴 Debug tool (raíz)
├── debug_pantalla.py    (24 lns)   # 🔴 Debug tool (raíz)
├── diagnose_vision.py   (38 lns)   # 🔴 Debug tool (raíz)
├── patrones/            (14 PNGs)  # 🟢 Imágenes patrón
├── tests/
│   ├── test_config.py   (143 lns)  # 🟢 Tests de configuración
│   └── test_vision.py   (57 lns)   # 🟡 Tests con hacks de importación
├── .githooks/pre-commit (33 lns)   # 🟢 Auto-bump hook
├── .github/workflows/   (32 lns)   # 🟡 CI OpenCode
├── config_sectores.json            # Config sectores
├── blacklist.json                  # Diarios con error
├── requirements.txt                # Dependencias
├── README.md                       # Documentación
└── logs/                           # Logs + capturas de error (15MB)
```

---

## 3. Hallazgos Detallados

### 🔴 CRÍTICOS (deben corregirse)

| ID | Hallazgo | Archivo | Impacto |
|----|----------|---------|---------|
| A1 | **GUI duplicada legacy** — `bot_ax_registro.py` es una versión alternativa con `overrideredirect(True)` y datos falsos (CPU_USAGE, MEM_USAGE con valores hardcodeados). Compite con `app_gui.py`. | `bot_ax_registro.py` | Confusión, código muerto, 244 líneas inservibles |
| A2 | **3 debug scripts en raíz** — `debug_ocr.py`, `debug_pantalla.py`, `diagnose_vision.py` contaminan el directorio principal. Solo se usan 1 vez durante setup. | Raíz del proyecto | Contaminación del namespace, ruido |
| A3 | **`__pycache__` en tracking** — Los `.pyc` aparecen en `git status` modificados. El `.gitignore` los ignora para nuevos pero los que ya están trackeados persisten. | — | Contaminación de repo |
| A4 | **Sin `pyproject.toml`** — No hay metadata de proyecto, ni entry points, ni dependencias declaradas formalmente. Solo `requirements.txt`. | — | Imposible `pip install -e .`, sin distribución |
| A5 | **Sin `.gitignore` completo** — Faltan exclusiones para `*.log`, `registro_*.txt` (está), `logs/capturas/`, `config_sectores.json` (no debería estar ignorado si es necesario para el setup). | `.gitignore` | Archivos generados pueden trackearse |

### 🟡 IMPORTANTES

| ID | Hallazgo | Archivo | Impacto |
|----|----------|---------|---------|
| B1 | **Monolito `vision.py`** — 288 líneas con 7 responsabilidades: OCR, template matching, click automation, screenshot capture, ID normalization, wait loops, logging. Sin separación de concerns. | `vision.py` | Difícil testear, modificar o reutilizar |
| B2 | **Config como módulo de constantes** — `config.py` mezcla: rutas de patrones, carga/validación JSON, validación Tesseract, offset OCR. Podría separarse en `settings.py` + `constants.py`. | `config.py` | Acoplamiento fuerte |
| B3 | **Test con monkey-patching frágil** — `test_vision.py` requiere `os.environ["BOT_AX_TEST_MODE"]=1` y reemplaza `vision.pyautogui` con un módulo vacío. Muy frágil. | `tests/test_vision.py` | Tests pueden romperse fácilmente |
| B4 | **Sin manejo de errores unificado** — Algunos lugares usan `try/except Exception: pass`, otros `try/except específico`, otros no manejan errores. Inconsistente. | Varios | Bugs silenciosos difíciles de diagnosticar |
| B5 | **Hardcode Tesseract path** — `config.py:15` tiene ruta hardcodeada a `C:\Users\jose.cespedes\...`. La variable de entorno `TESSERACT_CMD` es el override pero no hay documentación clara. | `config.py` | Portabilidad limitada |
| B6 | **El módulo `keyboard` es opcional pero frágil** — `HAS_KEYBOARD` flag chequea si `import keyboard` funciona, pero solo se usa para ESC en modo CLI. Sin él, `stop_event` es obligatorio. | `bot_main.py` | Comportamiento inconsistente entre modos |

### 🟢 MENORES / COSMÉTICOS

| ID | Hallazgo | Archivo |
|----|----------|---------|
| C1 | `registro_log()` en `bot_main.py` escribe a archivo TXT plano. Podría usar el logger estructurado. | `bot_main.py` |
| C2 | `setup_areas.py` importa `guardar_configuracion` pero el `__main__` llama `app.run()` sin verificar entorno. | `setup_areas.py` |
| C3 | `bump_version.py` usa `Path(__file__).parent` mientras el resto del proyecto usa `os.path.dirname(os.path.abspath(__file__))`. Inconsistencia de estilo. | `bump_version.py` |
| C4 | Nombres de variables en inglés/español mezclados (`intentos_scroll`, `casilla_objetivo`, `stop_event`, `log_queue`). | Varios |
| C5 | `app_gui.py` (758 líneas) es la clase más grande. Se beneficiaría de dividirse en componentes (panel izquierdo, stream panel, engine control). | `app_gui.py` |

---

## 4. Métricas del Código

| Archivo | Líneas | Funciones | Clases | Complejidad |
|---------|--------|-----------|-------|-------------|
| `app_gui.py` | 758 | 30+ métodos | 1 clase | Alta (métodos muy largos) |
| `bot_main.py` | 331 | 1 func + 1 helper | 0 | Media (función run_bot muy larga) |
| `vision.py` | 288 | 7 funciones | 0 | Alta (monolito) |
| `bot_ax_registro.py` | 244 | 10+ métodos | 1 clase | Media (legacy) |
| `tests/test_config.py` | 143 | 7 tests | 2 clases | Baja |
| `config.py` | 102 | 4 funciones | 0 | Baja |
| `setup_areas.py` | 83 | 6 métodos | 1 clase | Baja |
| `logger.py` | 72 | 2 funciones | 1 clase | Baja |
| `bump_version.py` | 62 | 3 funciones | 0 | Baja |
| `tests/test_vision.py` | 57 | 9 tests | 1 clase | Baja |
| `_version.py` | 40 | 1 función | 0 | Muy baja |
| `debug_ocr.py` | 39 | 1 función | 0 | Muy baja |
| `diagnose_vision.py` | 38 | 1 función | 0 | Muy baja |
| `debug_pantalla.py` | 24 | 1 función | 0 | Muy baja |
| `test_ocr.py` | 10 | 0 | 0 | Muy baja |
| **Total** | **2,357** | | | |

---

## 5. Dependencias (requirements.txt)

| Paquete | Propósito | Alternativa moderna |
|---------|-----------|-------------------|
| `pyautogui>=0.9.54` | Automatización GUI (template matching, clicks) | ✅ Esencial |
| `pytesseract>=0.3.10` | OCR para leer IDs de diario | ✅ Esencial |
| `pillow>=10.0.0` | Procesamiento de imágenes | ✅ Esencial |
| `keyboard>=0.13.5` | Detección de tecla ESC | 🟡 Alternativa: `pynput` o `tkinter bind` |

> ⚠️ **Nota:** `keyboard` solo se usa para detener el bot con ESC desde terminal. La GUI usa `stop_event` (threading.Event).

---

## 6. Análisis de Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Tesseract no instalado/ruta incorrecta | Media | Alto | Validación al inicio (ya implementada) |
| Región de sectores cambia (resize AX) | Alta | Alto | Setup visual guiado |
| Pop-up de error no detectado | Media | Alto (timeout 60min) | Timeout configurable |
| `keyboard` falla en modo CLI | Baja | Medio (ESC no funciona) | Fallback a stop_event |
| `__pycache__` trackeado | Alta (existente) | Bajo | Ruido en git status |
| GUI alternativa (bot_ax_registro) usada por error | Baja | Medio | Botón Stop podría no funcionar (sin pause_event) |

---

## 7. Conclusión

El Bot AX Contable es **funcional y cumple su propósito** en el contexto de Casino Express / Lo Águila. Sin embargo, la estructura actual es la de un proyecto que creció orgánicamente sin una arquitectura profesional planificada adelantada. Los problemas principales son:

1. **Código plano y sin paquete** — Todo en la raíz, sin `pyproject.toml`
2. **GUI legacy duplicada** — `bot_ax_registro.py` debe eliminarse o fusionarse
3. **Monolito `vision.py`** — Muchas responsabilidades mezcladas
4. **Debug scripts en raíz** — Contaminan el directorio del proyecto
5. **Sin estructura de paquete Python** — No instalable con `pip install -e .`
