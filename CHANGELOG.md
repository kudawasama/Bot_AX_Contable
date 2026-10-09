# Changelog — Bot AX Contable

Todos los cambios relevantes de este proyecto. El formato sigue
[Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el versionado es
`v-{major:02d}.{minor:02d}.{patch:02d}` (pre-alpha: major fijo en `00`).

---

## [v-00.20.00] — 2026-10-09 (Fase 2 · Lote A: observabilidad)

### Añadido
- **El analizador lee la telemetría estructurada (A1).** `scripts/observer_analyze.py`
  incorpora `leer_eventos`, `resumir_eventos`, `ultimo_timestamp_eventos/` `log` y
  `telemetria_mas_nueva_que_log`; el reporte suma la sección
  *TELEMETRÍA ESTRUCTURADA* (éxitos, errores, timeouts, fallbacks, IDs con error y
  sesiones por fecha) y **avisa cuando `bot_ax.log` quedó atrás** respecto de
  `logs/events.jsonl` — el síntoma exacto del incidente del 8–9 de octubre.
  `generar_reporte()` acepta `eventos` de forma opcional (compatibilidad total) y hay
  una opción nueva `--eventos`.
  *Hallazgo durante la implementación:* la primera versión comparaba por **fecha** y no
  detectaba el desfase (bastaba una línea del mismo día para que el log pareciera al día);
  se corrigió a comparación por **marca de tiempo**, con prueba de regresión.
- **Chequeo de salud en un comando (A3).** `scripts/chequeo_salud.py` responde
  "¿está trabajando bien el bot?" con cinco alertas: `TELEMETRIA_CONGELADA`,
  `SIN_ACTIVIDAD`, `TASA_ERROR_ALTA`, `CONFIG_INVALIDA` y `SIN_EVIDENCIA`.
  Opciones `--json`, `--raiz` y `--estricto` (código de salida 1 para cron/CI).
  Diseño: valida la configuración por su cuenta (un chequeo de salud no debe depender
  del código del "paciente") y compara el **contenido** del log, no su fecha de
  modificación.
- **Pruebas:** `tests/test_observer_analyze.py` (8) y `tests/test_chequeo_salud.py` (7).
  Suite total: **38/38**.

### Verificación
- Analizador end-to-end contra el repo real: reporta la sesión en curso
  (2026-10-09) y activa el aviso de log desactualizado.
- Chequeo de salud contra los archivos reales copiados a un temporal con una sesión
  simulada activa: detectó **245,8 min** de atraso del log y devolvió `exit 1`.
- CI (GitHub Actions, runner Windows): `pruebas` y `lint` en verde.

---

## [v-00.14.01] — 2026-10-09

### Cambiado
- **Lanzadores devueltos a su forma original (C-6 se pospone).** El bot está en
  producción y `Lanzar_Bot.bat` / `Lanzar_Bot_Registro.bat` son el punto de entrada
  que el operador ejecuta a diario: no se cambia eso mientras el bot está trabajando.
  La versión portable (`%~dp0` + `where pythonw`) quedó implementada, verificada y
  descrita en la tarea **C-6** del plan; para reaplicarla basta revertir el commit que
  la revirtió. Los dos archivos volvieron byte por byte a su contenido anterior
  (hashes idénticos al commit `3ef8880`, comprobado).
- **Se mantienen** la portabilidad de Tesseract (C-5) y el handler
  `ArchivoRotativoRobusto` (v-00.13.02): ninguno altera el comportamiento verificado
  en la máquina de producción.

### Corregido
- `README.md`: la descripción de los lanzadores vuelve a corresponder con lo que
  realmente hacen (comprueban la unidad `H:` y usan la ruta fija de Python 3.12).

---

## [v-00.13.02] — 2026-10-09

### Corregido
- **Pérdida silenciosa de las trazas del bot (`logs/bot_ax.log`).**
  - *Síntoma:* desde el **2026-10-08 10:52** el archivo no recibió ni una línea
    nueva, mientras el bot siguió trabajando: hoy (2026-10-09) la sesión dejó 148
    eventos en `logs/events.jsonl`, 23 ciclos y 6 errores en
    `registro_2026-10-09.txt`, pero **cero** líneas en `bot_ax.log`.
  - *Causa:* `RotatingFileHandler` mantiene un descriptor abierto durante toda la
    ejecución; los logs viven en Google Drive (unidad H:) y, al reemplazarse o
    re-sincronizarse el archivo, el descriptor queda huérfano y las escrituras se
    pierden sin rastro (el bot corre con `pythonw`, sin stderr donde avisar).
  - *Efecto:* `scripts/observer_analyze.py` quedó ciego para todo lo posterior al
    8 de octubre (sus patrones de errores AX, timeouts y fallbacks terminan ahí);
    solo veía las sesiones por los `registro_*.txt`.
  - *Solución:* nuevo handler `ArchivoRotativoRobusto` en `src/core/logger.py`:
    mismo formato y misma rotación (5 MB, 3 backups), pero abre el archivo en modo
    *append* en cada emisión, así que un archivo reemplazado en disco se vuelve a
    crear siempre. Nunca lanza excepciones (un log perdido no puede detener el bot).
  - *Verificación:* `tests/test_logger.py` (5 pruebas, incluida la regresión
    "el archivo se reemplaza en disco → la siguiente traza sí se escribe") y prueba
    contra la ruta real de Google Drive (dos líneas nuevas el 2026-10-09 11:53).

---

## [v-00.13.00] — 2026-10-09 (sesión de profesionalización)

### Corregido
- **Suite de pruebas restaurada (C-1/C-3).** `tests/test_vision.py` y
  `tests/test_config.py` importaban módulos de la estructura previa al refactor
  (`import vision`, `import config`), por lo que `pytest` fallaba al 100% en la
  colección y el protocolo de verificación obligatorio de `AGENTS.md` era
  inservible. Ahora se ejecutan **18/18 pruebas en verde**.
- **Import duplicado de `event_log` en `src/services/vision.py` (C-2).**
- **Portabilidad de Tesseract y lanzadores (C-5/C-6).**
  - `src/core/config.py`: `TESSERACT_CMD` se resuelve con `_resolver_tesseract()`:
    variable de entorno → ruta histórica del usuario → rutas típicas de Windows →
    `shutil.which`. En la máquina de producción resuelve exactamente la misma ruta
    (verificado) y ya no depende del nombre del usuario.
  - `Lanzar_Bot.bat` / `Lanzar_Bot_Registro.bat`: la raíz del proyecto es `%~dp0`
    (funciona en cualquier unidad/PC) y el intérprete se resuelve
    (`pythonw` de Python 3.12 → `where pythonw` del PATH) en vez de estar quemado.
    Verificado con una copia de prueba invocada desde fuera del repositorio.
    **⚠️ REVERTIDO en v-00.14.01** por decisión de estabilidad (C-6 queda pendiente):
    los lanzadores volvieron a su forma original.
- **`config_sectores.json` versionado (C-7/R-6).** La calibración real en uso
  (`sector_a` 300px, `sector_b` 283px, `sector_scroll` 37px) llevaba meses
  modificada sin commit y sin respaldo: ahora está en el repositorio. Se quitó de
  `.gitignore` (decisión documentada) y se mantiene `blacklist.json` fuera del
  control de versiones por ser estado de ejecución.

### Añadido
- **`tests/conftest.py`**: dobles inertes de `pyautogui` y `pytesseract`
  inyectados en `sys.modules` antes de importar el código del bot. Reemplaza el
  hack `BOT_AX_TEST_MODE` + `types.ModuleType` y garantiza que la suite nunca
  mueva el mouse ni capture la pantalla (se puede correr con el bot en marcha).
- **`requirements.txt`**: dependencias de producción con versiones verificadas
  (el README las pedía pero el archivo no existía).
- **`CHANGELOG.md`** (este archivo).
- **`.github/workflows/ci.yml`**: verificación automática en cada push y PR
  (suite pytest en un runner Windows con las dependencias reales; paso de ruff
  informativo, todavía sin bloquear). Cierra el riesgo R-4: la suite estuvo rota
  semanas sin que nadie lo notara porque no había CI.

### Cambiado
- **Gobernanza de contexto dentro del repositorio**: `AGENTS.md`, `.context-map/`
  (brief, vault de Obsidian, skill) y `.hermes/` eran memoria viva del proyecto y
  solo existían en local, sin respaldo.
- **`PLAN_MEJORA_PROFESIONAL.md`** se movió de la raíz a
  `docs/plans/plan-mejora-profesional.md` (regla de raíz limpia de `AGENTS.md`).
- **`README.md`**: estructura real del proyecto (`src/…`), comandos correctos
  (`python -m src.ui.gui_classic`, `python -m src.ui.area_selector`,
  `python scripts/…`), confianzas reales (0.85 en checkboxes), flujo de scroll
  real (3 intentos × 1 clic, solo Sector C, fallback clic+rueda → `PgDn`), tabla
  de versionado real (el hook bumpea por archivos añadidos/eliminados, no por el
  tipo de commit) y logs reales (`logs/events.jsonl`).

### Notas de respaldo
- `main` y `docs/plan-implementacion-mejoras` quedaron sincronizadas con `origin`.

---

## [v-00.09.00] — 2026-07-31
### Añadido
- `docs/plans/plan-implementacion-mejoras.md`: plan accionable derivado del
  análisis de ContextMap (readiness 50/100) — correcciones C-1…C-9, riesgos
  R-1…R-6 y fases 0–7.
- Se incorporó el plan profesional de mejora como insumo
  (`docs/plans/plan-mejora-profesional.md`).

---

## [v-00.08.01] — 2026-07-13
### Corregido
- Movimiento sutil del mouse cada 12 s (y espera activa de 2 s antes de esperar el
  resultado) para evitar la suspensión del notebook durante los registros largos.

---

## [v-00.08.00] — 2026-06-22
### Añadido
- `scripts/observer_watch.py`: vigilancia en vivo del bot por cron (lee
  `logs/events.jsonl` de forma incremental y solo habla cuando hay algo que
  reportar; silencio total si el bot no corre o todo va bien).

---

## [v-00.07.00] — 2026-06-22
### Añadido
- `scripts/observer_analyze.py`: análisis post-ejecución de logs, registros,
  blacklist y capturas (detecta los formatos históricos de log).
- `src/core/event_log.py`: registro de eventos estructurados en
  `logs/events.jsonl` (16 tipos de evento). El bot quedó instrumentado sin
  cambiar su lógica.

---

## [v-00.05.01] — 2026-06-16
### Cambiado
- Reestructuración modular del proyecto bajo `src/` (`src/core`, `src/services`,
  `src/ui`), ordenamiento de los scripts auxiliares y corrección del foco no
  destructivo en Dynamics AX.
- Se documentó la especificación del proceso y el manual operativo inmutable
  (`docs/manual_proceso_bot.md`).

---

## Anterior (v2.0 y v-00.01.x)
- Versión original con dos interfaces gráficas (clásica y alternativa).
- v-00.01.39: rutas absolutas, blacklist normalizada, región de éxito ampliada,
  validación de Tesseract, caché de posiciones, OCR externalizado, logging
  estructurado, tests unitarios y README.
- v-00.01.40+: auto-bump de versión por commit, log comprimido, botón Reiniciar,
  cierre de pop-ups de éxito/error con `ESC`.
