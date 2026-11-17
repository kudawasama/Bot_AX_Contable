# Changelog — Bot AX Contable

Todos los cambios relevantes de este proyecto. El formato sigue
[Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el versionado es
`v-{major:02d}.{minor:02d}.{patch:02d}` (pre-alpha: major fijo en `00`).

---

## [v-00.40.01] — 2026-11-17 (calibración real de sectores)

### Corregido
- **La calibración versionada no era la que el bot usa en producción.** El 2026-11-17 a las
  14:37 se recalibró la pantalla (1366x768) y el cambio quedó sin commitear en la copia de
  trabajo: un clon nuevo habría arrancado con la calibración anterior.
  - `sector_a`: `[59, 232, 276, 454]` (antes `[61, 242, 255, 444]`)
  - `sector_b`: `[1104, 87, 251, 36]` (antes `[1108, 99, 236, 36]`)
  - `sector_scroll`: `[343, 650, 39, 41]` (antes `[335, 671, 35, 24]`)
  - `ocr_region_offset`: sin cambios

---

## [v-00.40.00] — 2026-11-17 (el fin de ciclo ya se detecta: avisos del Infolog)

### Corregido
- **El bot no detectaba que el ciclo había terminado.** Síntoma: con el aviso de AX ya en
  pantalla, el motor seguía en `Esperando resultado (timeout: 60min)` y no arrancaba el
  ciclo siguiente (sesión `000358`, 14:37:51, detenida a mano).
  **Causa raíz:** el fin de ciclo se decidía comparando capturas del Infolog **completo**
  (`msg_exito_asiento_1.png` 340x162 y `Error_Registro.png` 341x101). Esas capturas
  incluyen texto que **cambia en cada registro**: la hora del mensaje
  (`Mensaje (14:38:40)`) y el número de asientos (`... en el diario: 7`). Medido con el
  aviso real en pantalla: **0.690** y **0.312** de similitud, contra umbrales de **0.8** y
  **0.9**. El bot sólo veía el aviso cuando el número de asientos y la hora coincidían con
  los de la captura de referencia.
  **Solución:** dos recortes de **texto fijo**, sin hora ni conteos, y un clasificador
  (`clasificar_aviso_resultado`) que los compara con la misma métrica que usa el resto del
  módulo:
  - `patrones/infolog_error.png` — «Uno o más errores de DETENCIÓN críticos…» → `error`
  - `patrones/infolog_exito.png` — «Número de asientos registrados en el diario:» (sin los
    dígitos) → `exito`
  El error se evalúa **primero**: si el Infolog mezcla avisos, un error nunca pasa por éxito
  (marcaría como registrado un diario que falló). Los patrones anteriores se conservan como
  respaldo, así que la lógica previa sigue disponible si aparece un aviso distinto.
- **`.gitignore`/telemetría: `sector_b_fallback` ya no miente.** Se registraba «Menu fuera de
  sector B» aunque el punto encontrado estuviera **dentro** del sector (la búsqueda regional
  no alcanzaba el umbral y la de pantalla completa sí). Ahora sólo cuenta como fallback si
  el punto cae realmente fuera del sector.

### Añadido
- `requirements.txt`: **`opencv-python` y `numpy` fijados.** PyAutoGUI los necesita para el
  parámetro `confidence=`, que el bot usa en **todas** sus búsquedas, pero no los declara
  como dependencia: en un PC recién formateado el bot habría fallado en la primera búsqueda.
- `tests/test_aviso_resultado.py` (6 pruebas): éxito, error, **prioridad del error**,
  pantalla sin aviso, imagen sin varianza y límite de tamaño de los patrones (un patrón
  grande reintroduce el fallo original).

### Verificación
- **77/77 pruebas** · `ruff: All checks passed!` · clasificación probada **en vivo** contra
  el aviso real que estaba en pantalla (sólo lectura): devuelve `exito`, y el mismo aviso
  hace que los patrones antiguos se queden en 0.690 / 0.312.

---

## [v-00.39.00] — 2026-11-16 (C-6: lanzadores `.bat` portables + calibración versionada)

### Corregido
- **C-6 — `Lanzar_Bot.bat` y `Lanzar_Bot_Registro.bat` ya no dependen de `H:`.** Fijaban la
  unidad de Google Drive y la ruta `Python312\pythonw.exe`. Ahora la raíz es la carpeta del
  propio `.bat` (`%~dp0`) y el intérprete se resuelve en `Python313/312/311` y, si no, en el
  `PATH` descartando el stub de `WindowsApps` (que abre la Store en vez de Python).
  Se aplicó ahora —y no en v-00.14.01, donde se revirtió a propósito— porque el PC se
  formatea y el clon deja de estar en `H:`.
- **`config_sectores.json` con la calibración real.** Hasta ahora la que usaba producción
  vivía **sin commitear** en la copia de `H:` (y se habría perdido al formatear): `sector_a`
  61,242,255,444 · `sector_b` 1108,99,236,36 · `sector_scroll` 335,671,35,24.
- **`sector_b` pasa de 28 a 36 px de alto.** `btn_registrar_menu.png` mide 148x32: una región
  más baja que el patrón hace que el bot la ignore y busque en toda la pantalla. La telemetría
  acumula **799 `sector_b_fallback`**, que es exactamente ese camino.

### Verificación
- 71/71 pruebas · `ruff: All checks passed!` · `test_ocr.py` OK (Tesseract 5.4.0) · imports de
  las dos GUI OK · los tres sectores dentro de 1366x768 y todos los patrones caben en su región
  (checkbox 21x17 en 255x444, botón 148x32 en 236x36, scroll 16x15 en 35x24).
- Los lanzadores se probaron **sin abrir la GUI** (sonda que imprime raíz, `pythonw` resuelto e
  import del módulo): raíz correcta, `pythonw.exe` de Python 3.12 e `IMPORT=OK` en los dos.

### Notas
- Los `.bat` conservan CRLF (requisito de `cmd.exe`) y no se probaron en una sesión real de
  registro; conviene un arranque de prueba antes de la jornada.

---

## [v-00.38.01] — 2026-11-16 (Fase 2 · Lote B integrado en `main`)

### Añadido
- El lote B pasa de la rama `feat/fase2-b-runtime` a `main`: **B1/B1b** (validación del ID de
  AX de 8 dígitos antes de usarlo), **B2** (heartbeat cada 60 s en la telemetría), **B3**
  (retención de capturas de error, máx. 50 FIFO), **B5** (las trazas del motor llegan a
  `logs/bot_ax.log` en las dos GUI) y las 18 pruebas nuevas que los cubren.
  Con esto, un clon de `main` en un PC nuevo ya trae el bot completo y al día.

### Verificación de la condición de integración
- El lote B exigía una sesión real (1 éxito, 1 error esperado y el scroll) antes de fusionar.
  La evidencia está en producción (`logs/events.jsonl` de la copia de `H:`): entre el
  **2026-10-19** y el **2026-11-16** conviven 384 `bot_heartbeat` (B2) con 1.703
  `result_exito`, 175 `result_error_ax`, 1.211 `scroll_performed` y 1 `id_ilegible`
  (B1 rechazando una lectura defectuosa en lugar de registrar el diario equivocado).

### Notas
- Conflicto del CHANGELOG resuelto conservando íntegras las entradas v-00.34.00 y v-00.37.00.
- Los saltos 00.38.00/00.38.01 de la rama no tenían entrada propia (C-8 sigue pendiente).

---

## [v-00.37.00] — 2026-10-13 (Fase 2 · Lote B: robustez en runtime — integrado el 2026-11-16)

> **Integrado a `main` el 2026-11-16 (v-00.38.01).** La regla del lote exigía una sesión real
> de validación (mínimo 3 diarios: 1 éxito, 1 error esperado y el scroll) antes de fusionar;
> se cumplió con creces en producción sobre la rama `feat/fase2-b-runtime` (ver v-00.38.01).

### Corregido
- **B1 + B1b — el ID de AX se valida antes de usarlo.** `leer_id_diario` devolvía texto arbitrario
  del OCR y el motor procesaba el diario con ese identificador: **un dígito mal leído hacía
  registrar y listar como error un diario distinto del real**. Ahora exige UN único número de 8
  dígitos (con límites para no cortar una lectura corrida de 9) y devuelve `ERROR_LECTURA` en
  cualquier otro caso; el motor entonces **salta la casilla** (no la clickea), guarda captura y
  registra `id_ilegible` en la telemetría.
- **B5 — las trazas del motor ya llegan a `logs/bot_ax.log`.** Causa raíz: el motor entrega sus
  mensajes por `log_callback` y la GUI clásica los encolaba **directamente** para su consola, sin
  pasar por `logging`; al archivo solo llegaban las líneas que `vision.py` escribe con
  `logger.info/warning`. Resultado: un fallo temprano de la sesión no dejaba rastro en texto.
  Arreglado en las DOS GUI (la alternativa además ni importaba el logger).

### Añadido
- **B2 — latido (`bot_heartbeat`) cada 60 s** en la telemetría: permite distinguir «el bot está
  esperando el resultado de AX» de «el bot se colgó» sin mirar la pantalla. Hilo daemon cortado en
  un `finally`, así que ninguna salida deja hilos huérfanos. Una línea por minuto como máximo.
- **B3 — retención de capturas (máx 50, FIFO).** `logs/capturas/` tenía 363 archivos (~0,5 MB cada
  uno) dentro de Google Drive; ahora se conservan las 50 más recientes.

### Verificación
- Suite **71/71** (18 pruebas nuevas: 8 de B1/B1b, 5 de B3, 2 de B2, 3 de B5) · `ruff: All checks
  passed!` · los dobles inertes de `tests/conftest.py` garantizan que ninguna prueba mueva el
  mouse ni capture la pantalla.
---

## [v-00.34.00] — 2026-11-16 (C-5: `test_ocr.py` resuelve Tesseract igual que el bot)

### Corregido
- **`scripts/test_ocr.py`**: llamaba a `pytesseract` sin fijar `tesseract_cmd`, por lo que
  dependía del `PATH` y reportaba `FAILED: Tesseract engine not found` aunque el motor
  estuviera instalado (verificado: 5.4.0 en la ruta que ya usa `src.core.config`).
  Además terminaba con código 0 tras fallar, así que no servía como comprobación.
  Ahora resuelve `TESSERACT_CMD` con fallback a `shutil.which`, informa la ruta usada y
  devuelve código 1 si el motor falta o no responde.

### Añadido
- `.gitignore`: `.pytest_cache/` y `.ruff_cache/`, que se generan en cada corrida de
  verificación y no son artefactos del bot. No se modifica la nota que documenta que
  `config_sectores.json` **sí** se versiona (C-7/R-6) ni el seguimiento de `.context-map/`.

### Notas
- No se toca la versión declarada en `src/core/version.py` (ya estaba en `00.34.00`):
  esta entrada documenta ese salto, que había quedado sin CHANGELOG (C-8 sigue pendiente).
- No se tocan los lanzadores `.bat`: C-6 sigue revertido a propósito.

---

## [v-00.33.00] — 2026-10-13 (C-3: definir el LICENSE)

### Añadido
- **`LICENSE`**: aviso de titularidad y uso interno ("todos los derechos reservados"). No es una
  licencia de código abierto ni concede permisos de reutilización: deja **por escrito** lo que ya
  regía por defecto y responde al pedido de `ctxmap`. Se descartaron MIT/Apache a propósito: es
  una herramienta interna, no un proyecto para compartir.

### Notas
- El aviso jurídico no cambia nada más que el propio archivo `LICENSE`: no afecta la ejecución
  del bot ni el contenido del repositorio.

---

## [v-00.31.00] — 2026-10-13 (C-4: eliminar el código muerto `src/bot_ax/`)

### Eliminado
- **`src/bot_ax/`** (C-4, desbloqueado al archivar la rama legado): contenía un solo archivo
  versionado, `config/defaults.py`, que **ningún módulo importa** (verificado: 0 referencias a
  `src.bot_ax` en `src/`, `tests/` y `scripts/`; los lanzadores invocan `src.ui.gui_classic` y
  `src.ui.gui_gemini`), más 35 `.pyc` sueltos de compilaciones antiguas.
- Referencias al módulo actualizadas: el árbol del `README.md` y el `norecursedirs` de
  `pyproject.toml`.

### Verificación
- Suite **53/53** · los 8 módulos de `src/` importan sin error.

---

## [v-00.28.00] — 2026-10-13 (archivo de la rama legado)

### Cambiado
- **Rama legado eliminada** (`refactor/estructura-profesional`, local y remota, 2026-10-13)
  tras publicar y verificar la etiqueta anotada `legacy/estructura-profesional-plana`.
  Comprobado **antes** de borrar: `git merge-base --is-ancestor` confirma que la rama está
  contenida en la etiqueta y `git ls-remote` que la etiqueta está publicada en GitHub → la
  historia no se pierde. Eso desbloqueó C-4, ejecutado en el mismo cierre.
- `docs/estructura_proyecto.md`: la nota de ramas ya refleja que no queda ninguna rama que
  parezca una línea de desarrollo activa.

### Notas
- **LICENSE**: se documenta por qué sigue pendiente. Un `LICENSE` es el texto que dice qué
  puede hacer legalmente un tercero con el código. Si no existe, el repositorio queda por
  defecto como "todos los derechos reservados": nadie puede reutilizarlo sin permiso, que es
  lo deseable para una herramienta interna. Es una decisión del operador, no un requisito
  técnico: no afecta en nada la ejecución del bot.

---

## [v-00.26.00] — 2026-10-13 (Fase 2 · Lote C: higiene del repositorio)

### Añadido
- **`pyproject.toml`** con la configuración de las herramientas (pytest, ruff, coverage) y
  **sin** `[project]`/`[build-system]` a propósito: el bot se ejecuta desde el repositorio y
  agregar metadatos de paquete cambiaría su modelo de ejecución en producción.
  El ruleset de ruff es explícito (E, F, I, W) y excluye a conciencia las reglas que chocan
  con los estándares del proyecto: `UP006/UP035/UP045` (prohibirían `List`/`Dict`/`Optional`,
  que AGENTS.md exige), `BLE001/S110` (prohibirían el `except` ciego deliberado del fail-safe)
  y `DTZ` (exigirían timezone en una app de escritorio local).

### Cambiado
- **El lint del CI pasó de informe a puerta obligatoria**: se quitó `--exit-zero` y
  `continue-on-error`. Si un cambio introduce un aviso, el pipeline se pone rojo.
- **Documentación de ramas** en `docs/estructura_proyecto.md`: `main` es producción; el árbol
  plano anterior al refactor quedó preservado en la etiqueta anotada publicada
  `legacy/estructura-profesional-plana` (2026-06-12, 15 commits fuera de `main`).

### Limpiado
- **236 avisos de ruff → 0**, en tres etapas verificadas por separado:
  1. `tests/` y `scripts/`: 57 avisos (espacios, orden de imports, imports sin uso, f-strings).
  2. `src/` solo espacios (W291/W293): 132 avisos, con la prueba de que `git diff -w` queda
     **vacío** — es decir, cero cambios de lógica.
  3. `src/` orden de imports e imports sin uso: 10 avisos.
- **Hallazgo (código muerto):** `buscar_estado_checkbox` está definida en
  `src/services/vision.py:167` y **no la llama nadie**; `engine.py` la importaba sin usarla.
  Se quitó el import; la función queda a decisión del operador (no se borra por iniciativa).
- **Respaldo de la recalibración de sectores del 13-oct** (ajustada por el operador en la GUI):
  estaba sin commitear; se versionó tal cual, sin modificar sus valores.

### Notas
- **Makefile descartado:** no hay `make` en el entorno (Windows/git-bash) y no se entrega un
  artefacto que no se pueda probar. Los comandos canónicos ya están en el README, `AGENTS.md`
  y `Chequear_Salud_Bot.bat`.
- **LICENSE pendiente:** es una decisión del usuario; no se inventó una licencia.

### Verificación
- Suite **53/53** tras cada etapa · `ruff: All checks passed!` · los 8 módulos de `src/`
  importan sin error · `compileall` limpio · CI en verde.

---

## [v-00.23.00] — 2026-10-09 (Fase 2 · Lote A cierre: T2, T4 y T5)

### Corregido
- **La opción `--registro` del analizador ya no se ignora (T2).** Se aceptaba en la línea
  de comandos pero `main()` nunca la pasaba a `leer_registros()`, así que el analizador
  leía siempre todos los `registro_*.txt` del proyecto y el filtro del operador no servía.
  Ahora acepta un archivo puntual o una carpeta. Verificado con el registro real: 82
  registros del día en lugar de todo el histórico.
- **La métrica de lista negra distingue la sesión del histórico (T4).** El reporte mostraba
  "cobertura 5,8%" sin explicar que `blacklist.json` se vacía con *Clear Errors* /
  *Reiniciar*, y el número se leía como un fallo del bot. Ahora muestra dos preguntas
  separadas: cobertura de la **última sesión** (14 errores, 100% ya en la lista el
  2026-10-09) e **histórico** (129 IDs con error alguna vez · 114 nunca en la lista ·
  16 reintentados), con una nota explicativa.
  *Hallazgo durante la implementación:* el primer cálculo sumaba las dos fuentes
  (registro + telemetría) y marcaba **116 de 129** IDs como "reintentados" — un diario que
  falla una vez queda en ambos archivos. Corregido a **días distintos con error**, con
  prueba de regresión. Los 16 restantes son reintentos reales: diarios que volvieron a
  fallar otro día, es decir los que la lista negra no retuvo entre jornadas.

### Añadido
- **`Chequear_Salud_Bot.bat` (T5)**: doble clic para ver el informe de salud. Es de solo
  lectura (no toca al bot ni la pantalla) y no reemplaza ni modifica los lanzadores.
  Probado realmente ejecutándolo con la entrada estándar cerrada.
- **README**: sección "¿Está trabajando bien el bot?" con los comandos y la tabla de las
  6 alertas; el `.bat` figura en la estructura del proyecto.
- **CI**: paso de humo que ejecuta `chequeo_salud.py --json` para que la herramienta no se
  rompa en silencio (en CI no hay `logs/`, así que solo verifica que arranca y responde).

### Verificación
- 6 pruebas nuevas (2 de T2, 4 de T4) → suite completa **53/53**.
- T2 y T4 verificados con los datos reales del proyecto; el `.bat` probado de verdad.

---

## [v-00.21.01] — 2026-10-09 (Fase 2 · Lote A cierre: T1 y T3)

### Añadido
- **Alerta `SESION_TERMINADA_POR_ERROR` (T1).** El 2026-10-09 el bot murió a las 15:24
  por el fail-safe de PyAutoGUI (mouse en una esquina) y el chequeo informaba `OK`
  simplemente porque no había sesión abierta: una caída dependía de que alguien abriera
  el log. Ahora `analizar_ultima_sesion()` reporta motivo, hora, la marca del fail-safe y
  el último diario visto, distingue el cierre normal (`user_esc`, `no_more_diarios`) y
  usa una ventana de 24 h para no dejar el chequeo en rojo para siempre.

### Corregido
- **Falso `SIN_ACTIVIDAD` durante la espera del resultado de AX (T3).** Durante esa espera
  el bot **no emite eventos** (solo escribe en `bot_ax.log`) y puede durar 60 min, así que
  el umbral fijo de 15 min habría alertado en falso en cualquier registro lento.
  `umbral_sin_actividad()` aplica 65 min cuando el último evento dejó al bot esperando el
  resultado y 15 min en cualquier otro punto del ciclo; el informe muestra el umbral usado
  y el JSON lo expone en `umbral_actividad_min`.

### Notas
- Se ajustó la prueba `test_detecta_sin_actividad_con_sesion_abierta`: usaba un
  `confirm_click` como "evento cualquiera", que con la regla nueva significa "esperando
  resultado". Ahora usa `checkbox_found`, que es lo que la prueba verificaba.

### Verificación
- 8 pruebas nuevas → suite completa **46/46**.
- Demo con los **datos reales** del repo recortados en el crash: la alerta aparece con
  motivo `error`, hora 15:24, fail-safe 15:24:19 y último diario `00337616`, con `exit 1`
  bajo `--estricto`.
- En vivo, con el bot esperando resultado: `OK` con umbral 65 min (sin falso positivo).

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
