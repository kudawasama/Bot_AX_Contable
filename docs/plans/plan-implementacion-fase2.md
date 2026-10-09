# Plan de Implementación — Fase 2: Observabilidad, Datos y Calidad

> **Proyecto:** Bot_AX_Contable
> **Fecha:** 2026-10-09
> **Base:** `main` = `d2eae61` · versión **v-00.15.00** · suite **23/23** · CI en verde
> **Autor del plan:** Hermes Agent (análisis del repo + diagnóstico de la sesión del 2026-10-09)
> **Documentos relacionados:** `docs/plans/plan-implementacion-mejoras.md` (C-1…C-9, R-1…R-6),
> `docs/plans/plan-mejora-profesional.md` (fases 0–7 originales), `docs/manual_proceso_bot.md`
> (reglas inmutables), `AGENTS.md` (protocolo de trabajo)

---

## 1. Objetivo

Cerrar las brechas de **observabilidad, calidad de datos y automatización** que quedaron
visibles durante el incidente del 2026-10-09 —cuando el bot registró 12 errores en una
jornada sin que existiera ninguna herramienta que lo detectara— **sin alterar el
comportamiento del bot en producción**.

**Meta medible:** que ante cualquier sesión anómala (tasa de error alta, caída del bot,
pérdida de telemetría) exista evidencia automática suficiente para diagnosticarla en menos
de 5 minutos, y que el repositorio esté limpio de configuración ambigua.

---

## 2. Contexto y supuestos (hechos verificados)

| Hecho | Evidencia |
|---|---|
| El bot está **en producción y en uso diario** | proceso `pythonw -m src.ui.gui_classic` (PID 14472 desde el 8-oct), 59 OK / 12 ERR el 2026-10-09 |
| La telemetría estructurada **sí** funciona | `logs/events.jsonl` con 148+ eventos del 2026-10-09 |
| El log de texto estuvo **muerto** entre el 8-oct 10:52 y el 9-oct 11:53 | `logs/bot_ax.log` congelado; corregido con `ArchivoRotativoRobusto` (v-00.13.02) |
| El analizador **solo** lee `logs/bot_ax.log` | `scripts/observer_analyze.py`: patrones de errores AX/timeouts/fallbacks terminan el 2026-10-08 |
| La suite es **hermética** (se puede correr con el bot activo) | `tests/conftest.py` inyecta dobles inertes de `pyautogui`/`pytesseract`; 23/23 con el bot corriendo |
| Existe una **rama legado** con otro árbol | `refactor/estructura-profesional` (408a02b), 14 commits fuera de `main` |
| Ruff reporta **208 avisos** | 44 `UP006` + 25 `UP045` + 20 `UP035` chocan con el estándar `List/Dict/Optional` de `AGENTS.md`; 24 `F541`, 14 `I001`, 7 `F401` son corregibles |
| ctxmap pide LICENSE, pyproject.toml y Makefile | salida de `ctxmap refresh .` (readiness) |

**Supuestos de trabajo**
1. El bot puede seguir corriendo durante los lotes A y C; el **lote B exige tenerlo detenido**
   y una sesión de prueba real antes de dar por buena la tarea.
2. Nadie más edita este repo en paralelo (verificar `git status` antes de cada tarea).
3. La calibración (`config_sectores.json`) y `blacklist.json` siguen siendo datos vivos:
   el plan **no** los modifica.

---

## 3. Reglas de trabajo (obligatorias, no negociables)

1. **No tocar el punto de entrada diario** (`Lanzar_Bot.bat`, `Lanzar_Bot_Registro.bat`).
   Se revirtieron a propósito en v-00.14.01: cualquier cambio ahí requiere ventana de
   mantenimiento y prueba con el bot detenido.
2. Una rama por lote: `feat/fase2-a-observabilidad`, `fix/fase2-b-runtime`, …
   Nunca commitear directo en `main`; integrar con avance normal (`git push origin HEAD:main`).
3. **TDD siempre**: primero la prueba que falla, luego el código mínimo, luego verde.
4. **Commit + push por tarea** (Conventional Commits en español). Respaldo constante.
5. Fijar la versión a mano y dejarla *staged* en los commits de código, para que el bump
   no dependa del hook (regla del hook: añadir/eliminar archivos = minor; solo modificar = patch).
6. Antes de cada commit: `pytest` 23/23 + `ruff` sin errores nuevos en los archivos tocados.
7. Al cerrar cada lote: `ctxmap refresh .` y commit del contexto.
8. **Nunca** ejecutar `scripts/debug_*.py`, `scripts/diagnose_vision.py` ni `scripts/test_ocr.py`
   con el bot en ejecución.
9. Antes de proponer un cambio de comportamiento: responder las 3 preguntas del alma
   (¿por qué existe? ¿para qué sirve? ¿qué cumple?) y respetar `docs/manual_proceso_bot.md`.

**Intérprete:** siempre Python 3.12 del bot.
`"%LOCALAPPDATA%\Programs\Python\Python312\python.exe" -m pytest -q`

---

## 4. Resumen de lotes

| Lote | Contenido | Riesgo para el bot | Requiere bot detenido |
|------|-----------|--------------------|-----------------------|
| **A** | Observabilidad y automatización (scripts, docs, herramientas de desarrollo) | Nulo | No |
| **B** | Robustez en tiempo de ejecución (OCR, heartbeat, retención de capturas) | Medio | Sí |
| **C** | Higiene del repositorio (rama legado, `pyproject.toml`, lint, LICENSE) | Nulo | No |
| **D** | Fuera de alcance por ahora (refactor mayor, Docker, portabilidad `.bat`) | Alto | — |

Orden recomendado: **A → C → B**. Empezar por lo que reduce el riesgo futuro sin tocar al bot.

---

## 5. LOTE A — Observabilidad y automatización (riesgo nulo)

### Tarea A1: El analizador lee también `logs/events.jsonl`

**Objetivo:** que `observer_analyze.py` deje de depender del log de texto y no pueda volver
a quedar ciego.

**Archivos**
- Modificar: `scripts/observer_analyze.py` (hoy ~750 líneas, alta complejidad)
- Crear: `tests/test_observer_analyze.py`
- Referencia del esquema: `logs/events.jsonl` (`{"ts": ISO-8601, "event": "...", ...}`)

**Paso 0 — Inspección obligatoria (5 min)**
Leer el archivo antes de tocar nada y anotar: nombres exactos de las funciones de parseo,
estructura del diccionario `reporte` y dónde se imprimen las secciones.
`read_file scripts/observer_analyze.py` (en 2 lecturas por tamaño).

**Paso 1 — Prueba que falla**

```python
# tests/test_observer_analyze.py
"""Pruebas de la lectura de eventos estructurados del observador."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import observer_analyze  # noqa: E402


def _escribir_eventos(destino: Path, eventos: list[dict]) -> None:
    destino.write_text(
        "\n".join(json.dumps(e, ensure_ascii=False) for e in eventos),
        encoding="utf-8",
    )


def test_resumen_de_eventos_cuenta_exitos_y_errores(tmp_path: Path):
    archivo = tmp_path / "events.jsonl"
    _escribir_eventos(archivo, [
        {"ts": "2026-10-09T10:00:00", "event": "result_exito", "id_normalizado": "00337505"},
        {"ts": "2026-10-09T10:05:00", "event": "result_error", "id_normalizado": "00337501"},
        {"ts": "2026-10-09T10:06:00", "event": "result_error", "id_normalizado": "00337504"},
    ])
    resumen = observer_analyze.resumir_eventos(archivo)
    assert resumen["exitos"] == 1
    assert resumen["errores"] == 2
    assert resumen["ids_error"] == ["00337501", "00337504"]
```

**Paso 2 — Verificar que falla**
`python -m pytest tests/test_observer_analyze.py -v` → FAIL: `AttributeError: module ... has no attribute 'resumir_eventos'`

**Paso 3 — Implementación mínima** (en `scripts/observer_analyze.py`, sección nueva al final del archivo, antes del `main`)

```python
def resumir_eventos(ruta: Path) -> dict:
    """Resume ``logs/events.jsonl`` (telemetría estructurada, a prueba de fallos).

    POR QUÉ: el analizador se apoyaba solo en ``logs/bot_ax.log``, un archivo de
    texto que puede quedar congelado (incidente 2026-10-08/09). ``events.jsonl``
    se escribe con *open/append/close* por evento, así que siempre está al día.

    Args:
        ruta (Path): Ruta del archivo JSONL de eventos.

    Returns:
        dict: Contadores por tipo de evento, éxitos, errores, IDs con error,
        timeouts y fallbacks de Sector B.
    """
    resumen: dict = {
        "total_eventos": 0,
        "por_tipo": {},
        "exitos": 0,
        "errores": 0,
        "ids_error": [],
        "timeouts": 0,
        "fallbacks_sector_b": 0,
    }
    if not Path(ruta).exists():
        return resumen

    with open(ruta, "r", encoding="utf-8") as archivo:
        for linea in archivo:
            linea = linea.strip()
            if not linea:
                continue
            try:
                evento = json.loads(linea)
            except json.JSONDecodeError:
                continue
            tipo = evento.get("event", "")
            resumen["total_eventos"] += 1
            resumen["por_tipo"][tipo] = resumen["por_tipo"].get(tipo, 0) + 1
            if tipo == "result_exito":
                resumen["exitos"] += 1
            elif tipo == "result_error":
                resumen["errores"] += 1
                identificador = evento.get("id_normalizado")
                if identificador:
                    resumen["ids_error"].append(identificador)
            elif tipo in ("timeout_menu", "timeout_confirm", "result_timeout"):
                resumen["timeouts"] += 1
            elif tipo == "sector_b_fallback":
                resumen["fallbacks_sector_b"] += 1
    return resumen
```

**Paso 4 — Verificar que pasa**
`python -m pytest tests/test_observer_analyze.py -v` → PASS (1 prueba)

**Paso 5 — Conectar al reporte** (misma tarea, cambio pequeño): en la función principal,
después de las métricas globales, imprimir

```
📊 TELEMETRÍA ESTRUCTURADA (events.jsonl)
  Eventos totales: N  |  Éxitos: X  |  Errores: Y
  Timeouts: Z  |  Fallbacks Sector B: W
  IDs con error (última sesión): [...]
```

y usar `resumir_eventos` como **fuente principal** cuando `bot_ax.log` tenga fecha más
antigua que `events.jsonl` (comparar `st_mtime`). Añadir prueba:
`test_reporta_telemetria_cuando_el_log_esta_congelado` (crear un `bot_ax.log` viejo y un
`events.jsonl` nuevo en `tmp_path`; el resumen debe provenir del JSONL).

**Paso 6 — Verificación end-to-end (real)**
`python scripts/observer_analyze.py` → la sección nueva debe mostrar **los errores de HOY**
(12 al cierre del 2026-10-09), no los del 8-oct.

**Paso 7 — Commit**
```bash
git add scripts/observer_analyze.py tests/test_observer_analyze.py
git commit -m "feat: el analizador lee la telemetria estructurada events.jsonl"
```
Push a la rama del lote. (Sin bump manual: solo modifica + añade prueba → minor automático;
si se quiere determinismo, fijar `version.py` antes.)

**Criterio de aceptación:** `observer_analyze.py` reporta la actividad del 2026-10-09 aun
con `bot_ax.log` congelado; 100% de la suite en verde; ninguna escritura a disco desde el script.

---

### Tarea A2: métrica de lista negra honesta (histórica y de sesión)

**Objetivo:** dejar de reportar "cobertura de blacklist 5,8%" sin explicar que la lista se
borra con el botón *Clear Errors* / *Reiniciar*. Hoy el número se lee como un fallo del bot
y no lo es.

**Archivos:** `scripts/observer_analyze.py`, `tests/test_observer_analyze.py`

**Pasos**
1. Prueba que falla: `resumir_eventos` debe devolver `ids_error_reintentados`
   (IDs con más de un `result_error` en el histórico) y `errores_totales_historicos`.
2. Implementar contando `result_error` por ID con `collections.Counter`.
3. Imprimir dos líneas separadas:
   - `Cobertura actual de blacklist.json: X de Y errores históricos` + nota
     `(la lista se vacía con Clear Errors / Reiniciar; usar events.jsonl como histórico)`.
   - `Errores históricos únicos: N | nunca en blacklist: M | reintentados: K`.
4. Verificación: el reporte muestra los IDs de hoy y explica la diferencia.
5. Commit: `fix: la metrica de blacklist distingue historico de sesion`.

**Criterio de aceptación:** el número deja de ser ambiguo; se puede responder "¿cuántos
diarios fallaron alguna vez y nunca se saltaron?" en una línea.

---

### Tarea A3: protocolo de chequeo de salud del bot (script de 1 comando)

**Objetivo:** responder "¿el bot está trabajando bien ahora mismo?" con un comando, sin
abrir el log a mano (esto es lo que faltó durante el incidente).

**Archivos**
- Crear: `scripts/chequeo_salud.py`
- Crear: `tests/test_chequeo_salud.py`

**Comportamiento esperado (interfaz)**
```py
def chequeo(directorio_raiz: Path, ahora: datetime | None = None) -> dict:
    """Devuelve el estado del bot: {proceso_vivo, log_al_dia, eventos_al_dia,
    ultimo_evento_min, tasa_exito_hoy, alertas: [...], ok: bool}."""
```
Reglas:
1. `logs/bot_ax.log` con `st_mtime` de más de 10 min **mientras hay un `bot_start` sin
   `bot_stop`** ⇒ alerta `TELEMETRIA_CONGELADA` (el síntoma exacto del 2026-10-09).
2. Sin eventos en los últimos 15 min con el bot activo ⇒ alerta `SIN_ACTIVIDAD`.
3. Tasa de error del día > 25% ⇒ alerta `TASA_ERROR_ALTA` (hoy fue 17%).
4. `blacklist.json` ilegible o `config_sectores.json` inválido ⇒ alerta `CONFIG_INVALIDA`.

**Pasos:** prueba primero con archivos temporales (`tmp_path`) simulando cada alerta →
implementar → `python scripts/chequeo_salud.py` contra el repo real → commit
`feat: chequeo de salud del bot en un comando`.

**Criterio de aceptación:** con el repo real devuelve `ok: true` y la tasa del día;
con `bot_ax.log` envejecido a mano en una copia temporal, detecta `TELEMETRIA_CONGELADA`.

---

### Tarea A4: automatizar el chequeo en GitHub Actions (informativo)

**Objetivo:** tener la foto diaria del repo (tests + salud) sin depender de ejecutar nada a mano.

**Archivos:** `.github/workflows/salud.yml` (nuevo), reutilizando el patrón de `ci.yml`
(runner `windows-latest`, Python 3.12, `requirements.txt` + `requirements-dev.txt`).

**Pasos**
1. Job `salud` que ejecute `python scripts/chequeo_salud.py || true` y publique la salida.
2. Job `contexto` que ejecute `ctxmap check .` y publique el readiness (sin bloquear).
3. Verificar con `gh run list` que el workflow corre y queda en verde; corregir sintaxis
   hasta lograrlo (no se declara hecho sin un run verde real).
4. Commit: `ci: chequeo de salud y readiness en la nube`.

**Criterio de aceptación:** dos runs verdes en `gh run list`; `continue-on-error` en todo
lo que aún no es bloqueante.

---

## 6. LOTE C — Higiene del repositorio (riesgo nulo)

### Tarea C1: resolver la rama legado `refactor/estructura-profesional`

**Objetivo:** que nadie más confunda el árbol viejo con producción, sin borrar historia.

**Pasos**
1. `git log --oneline refactor/estructura-profesional | head -20` y `git diff --stat main refactor/estructura-profesional | tail -5` para documentar qué contiene (árbol plano: `app_gui.py`, `bot_main.py`, `vision.py`, `src/bot_ax/ui/`).
2. Crear etiqueta anotada: `git tag -a legacy/estructura-profesional-plana 408a02b -m "..."`.
3. `git push origin legacy/estructura-profesional-plana`.
4. Añadir a `docs/estructura_proyecto.md` una nota: "el árbol plano vive en la etiqueta …; no usar".
5. **Solo con OK explícito del usuario:** borrar la rama local y remota.
6. Commit + push de la documentación.

**Criterio de aceptación:** la historia queda preservada en una etiqueta y documentada; no
queda ninguna rama que parezca una línea de desarrollo activa.

**Riesgo:** `git push --delete` es irreversible en remoto → requiere confirmación aparte.

---

### Tarea C2: `pyproject.toml` solo con configuración de herramientas (sin tocar el runtime)

**Objetivo:** unificar la configuración de pytest/ruff/cobertura sin cambiar cómo se ejecuta el bot.

**Archivos:** `pyproject.toml` (nuevo)

**Contenido propuesto (deliberadamente SIN `[project]` ni build backend: no se instala nada,
el bot sigue corriendo con `python -m src.ui.gui_classic`)**

```toml
# Configuración de herramientas de desarrollo para Bot AX Contable.
# IMPORTANTE: este archivo NO declara empaquetado ([project]/[build-system]) a
# propósito: el bot se ejecuta desde el repositorio (python -m src.ui.gui_classic)
# y no debe instalarse como paquete. Solo centraliza linters y pruebas.

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q"
norecursedirs = ["logs", "patrones", "docs", ".context-map", "src/bot_ax"]

[tool.ruff]
target-version = "py312"
line-length = 120

[tool.ruff.lint]
# Ruleset conservador y EXPLÍCITO. Se excluyen a propósito las reglas que chocan
# con el estándar de AGENTS.md (List/Dict/Optional) y con la filosofía fail-safe
# del bot:
#   UP006/UP035/UP045/UP007 → prohibirían List/Dict/Optional (estándar del proyecto)
#   BLE001/S110             → prohibirían el except ciego deliberado del bot
#   DTZ005/DTZ007           → exigirían timezone en apps de escritorio locales
select = ["E", "F", "I", "W"]
ignore = ["E501"]

[tool.coverage.run]
source = ["src"]
omit = ["src/ui/*", "src/bot_ax/*"]
```

**Pasos**
1. Crear el archivo.
2. `python -m pytest` → 23/23 (verificar que pytest toma la config nueva).
3. `python -m ruff check src/ tests/ scripts/` → contar avisos antes/después (esperado: bajan
   de 208 a ~45-60, al quedar fuera `UP*`, `BLE001`, `S110`, `DTZ*`).
4. Commit: `chore: pyproject.toml con configuracion de pytest, ruff y cobertura`.

**Criterio de aceptación:** pytest sigue pasando 23/23; el bot no cambia de comportamiento
(verificar con `python -c "from src.core.engine import run_bot"`); ruff deja de exigir lo
que el proyecto prohíbe.

---

### Tarea C3: limpiar los avisos de lint que son deuda real

**Objetivo:** dejar ruff sin avisos de la categoría segura (`F`, `I`) para poder convertirlo
en puerta obligatoria del CI.

**Orden (un archivo por commit, de menor a mayor riesgo)**
1. `tests/` y `scripts/` (no afectan al bot): `F401` imports sin usar, `F541` f-strings sin
   placeholders, `F841` variable sin usar, `I001` imports desordenados.
2. `src/services/vision.py` y `src/core/*.py`: solo los `F401`/`I001`; **cada cambio**
   con `pytest` + un chequeo de import.
3. `src/ui/*`: al final (más grande y sin pruebas).

**Comandos por iteración**
```bash
python -m ruff check src/ tests/ scripts/ --statistics
python -m ruff check <archivo> --fix          # solo fixes seguros (revisar el diff)
python -m pytest -q                           # debe seguir 23/23
git diff --stat                               # revisar antes de commitear
```

**Regla:** nunca `--unsafe-fixes`; nunca tocar lógica en este lote (si aparece un aviso que
exige cambiar comportamiento, se documenta y se pospone al lote B).

**Criterio de aceptación:** `ruff check` sin avisos de `F` ni `I`; suite 23/23; y entonces
quitar `--exit-zero` de `.github/workflows/ci.yml` para que el lint pase a ser obligatorio.

---

### Tarea C4: completar lo que pide ctxmap

- `Makefile` (nuevo) con objetivos: `install`, `test`, `lint`, `typecheck` (opcional),
  `contexto` (= `ctxmap refresh .`), `salud` (= `python scripts/chequeo_salud.py`).
  **No incluir el lanzador del bot**: eso se ejecuta con doble clic, nunca desde `make`.
- `LICENSE` — **requiere decisión del usuario** (repo privado corporativo). Opciones: sin
  licencia (todos los derechos reservados, recomendado para código interno), MIT, o
  propietaria. No inventar titularidad.
- `README.md`: sección corta "Comandos de desarrollo" con la tabla de `make`.

**Criterio de aceptación:** `ctxmap refresh .` deja de listar `Makefile/Justfile` como
faltante; el readiness reportado sube respecto de la línea base.

---

## 7. LOTE B — Robustez en tiempo de ejecución (SÍ toca al bot)

> **Regla del lote:** cada tarea se implementa y prueba en rama, con el bot **detenido**;
> la validación final es una sesión real de registro observada (mínimo 3 diarios: 1 éxito,
> 1 error esperado y el scroll). Ninguna tarea del lote B se integra a `main` sin esa sesión.

### Tarea B1: validar el ID leído por OCR antes de usarlo

**Problema:** 17 IDs históricos se leen de forma inestable (`W00330819Diai` vs `Diar`).
Hoy el normalizador toma el primer bloque de ≥6 dígitos: si el OCR se equivoca en un dígito,
el bot registra y **lista negra** un ID distinto del real. Los IDs de AX son de **8 dígitos**.

**Archivos**
- Modificar: `src/services/vision.py` (`leer_id_diario`, ~línea 294)
- Prueba: `tests/test_vision.py` (usar `mock_tesseract` de `tests/conftest.py`)

**Paso 1 — Prueba que falla**
```python
def test_lectura_invalida_se_marca_como_error(mock_tesseract):
    mock_tesseract.image_to_string.return_value = "W00ab919Diat"   # basura
    assert leer_id_diario((100, 100)) == "ERROR_LECTURA"

def test_lectura_de_7_digitos_no_es_valida(mock_tesseract):
    mock_tesseract.image_to_string.return_value = "W0337501Diat"
    assert leer_id_diario((100, 100)) == "ERROR_LECTURA"
```

**Paso 2 — Verificar que falla** → hoy devuelve `"00ab919Diat"` / `"0337501"`.

**Paso 3 — Implementación**
```python
# Requiere añadir List al import de typing en src/services/vision.py
PATRON_ID_AX: re.Pattern = re.compile(r"\d{8}")   # módulo, junto a NOMBRES_IMAGENES

def leer_id_diario(coord_checkbox: Tuple[int, int]) -> str:
    """... (docstring existente) ...
    Añadido: el ID de AX tiene exactamente 8 dígitos; si la lectura no encaja en el
    patrón (o hay más de una coincidencia distinta) se devuelve "ERROR_LECTURA" para
    que el diario NO se procese con un identificador dudoso (riesgo: registrar y
    listar un ID equivocado)."""
    # ... captura y OCR como hoy ...
    coincidencias: List[str] = PATRON_ID_AX.findall(texto)
    if len(set(coincidencias)) == 1 and len(coincidencias[0]) == 8:
        return coincidencias[0]
    logger.warning(f"OCR dudoso en {coord_checkbox}: {texto!r}")
    return "ERROR_LECTURA"
```
**Ojo:** `engine.py` ya trata `ERROR_LECTURA` como ID y lo mete en la lista negra tras un
error — revisar que ese flujo siga siendo aceptable (tarea B1b: si el ID es ilegible,
**saltar** el diario y avisar, en vez de clickear el checkbox).

**Paso 4 — Verificar:** `pytest tests/test_vision.py -v` → PASS (12 pruebas).
**Paso 5 — Commit:** `fix: valida que el ID de AX tenga 8 digitos antes de usarlo`.
**Paso 6 — Sesión de prueba real** con el bot: confirmar que no se salta diarios válidos
(los IDs reales son 8 dígitos: `00337505`).

**Criterio de aceptación:** 0 IDs dudosos procesados en la sesión de prueba; ningún diario
válido marcado como ilegible.

---

### Tarea B2: heartbeat en `events.jsonl`

**Objetivo:** distinguir "el bot está trabajando" de "el bot se colgó" sin mirar la pantalla.

**Archivos:** `src/core/engine.py` (bucle principal, ~línea 169), `scripts/observer_watch.py`
y/o `scripts/chequeo_salud.py` (tarea A3)

**Diseño:** hilo daemon que emite `event_log("bot_heartbeat", ciclo=ciclo, esperando=bool)`
cada 60 s; el chequeo de salud alerta si no hay heartbeat en >180 s **y** no hay `bot_stop`.
`event_log` ya es fail-safe y no altera la lógica.

**Pasos:** prueba unitaria del hilo (con `event_log` monkeypatcheado y un `stop_event`) →
implementar → verificar que el `bot_stop` corta el hilo (no dejar hilos huérfanos) →
commit `feat: heartbeat del bot en la telemetria estructurada` → sesión real.

**Criterio de aceptación:** durante una espera larga aparecen heartbeats cada ~60 s; el
archivo `events.jsonl` no crece sin control (una línea por minuto como máximo).

---

### Tarea B3: retención de capturas (máx 50, FIFO)

**Objetivo:** `logs/capturas/` ya tiene 363 capturas; el disco (H:) no es infinito.

**Archivos:** `src/services/vision.py` (`capturar_pantalla_error`, ~línea 324), prueba en `tests/test_vision.py`

**Implementación**
```python
# Requiere añadir: from pathlib import Path y List al import de typing en src/services/vision.py
def _rotar_capturas(directorio: Path, max_archivos: int = 50) -> None:
    """Elimina las capturas de error más antiguas cuando se supera el máximo.

    POR QUÉ: cada error guarda una captura de pantalla completa (≈0,5 MB). Tras
    meses de operación el directorio acumula cientos de archivos en Google Drive.
    Se conservan las ``max_archivos`` más recientes (FIFO por fecha de modificación).
    """
    archivos: List[Path] = sorted(
        directorio.glob("error_*.png"), key=lambda f: f.stat().st_mtime
    )
    while len(archivos) > max_archivos:
        archivos.pop(0).unlink(missing_ok=True)
```
**Prueba:** crear 55 archivos en `tmp_path` → tras llamar, quedan 50 y los 5 más antiguos
no están. **Commit:** `feat: retencion de capturas de error (max 50 FIFO)`.
**Criterio de aceptación:** la carpeta real queda en ≤50 tras la siguiente sesión de prueba.

---

### Tarea B4: diagnóstico cuando el log se reabre (opcional, solo si el usuario lo pide)

Registrar en `events.jsonl` (`logger_reopen`) cada vez que `ArchivoRotativoRobusto` tenga que
recrear el archivo (el archivo ya no está en disco entre dos escrituras). Sirve para saber
**cuántas veces** se pierde el handle por Google Drive. Coste: una comprobación
`os.path.exists` por línea (despreciable). Se implementa solo con bot detenido y prueba real.

---

## 8. LOTE D — Fuera de alcance (y por qué)

| Propuesta del plan antiguo | Decisión | Motivo |
|---|---|---|
| Refactor a `Orchestrator` + `ScrollManager` + `DiarioProcessor` + `BlacklistManager` (Fase 2, T-2.2…T-2.6) | **Pospuesto** | `engine.py` funciona y es el archivo de mayor riesgo; no hay pruebas de integración que respalden el refactor. Se retoma cuando existan las de B1/B2/B3 y una sesión de prueba reproducible. |
| `Dockerfile` + `docker-compose` (Fase 1, T-1.1/1.2) | **Descartado** | El bot necesita el escritorio real de Windows (PyAutoGUI, foco, mouse, Tesseract y Dynamics AX). Contenerizarlo no aporta y rompe el supuesto básico. |
| Validación con Pydantic (Fase 5, T-5.1) | **Pospuesto** | `cargar_configuracion()` valida lo esencial; añadir dependencia y reescribir la carga toca la ruta crítica de arranque sin urgencia. |
| Portabilidad de los `.bat` (C-6, T-1.4) | **Pospuesto a propósito** (v-00.14.01) | Es el punto de entrada diario del operador; se cambia solo en una ventana de mantenimiento con el bot detenido. |
| Eliminar `src/bot_ax/` (C-4) | **Depende de C1** | Su contenido se solapa con la rama legado: no tocar hasta archivar esa rama. |
| Reemplazar el hook de pre-commit por `pre-commit` moderno (C-8) | **Pospuesto** | Solo afecta a git, no al bot; el bump ya se puede hacer determinista fijando la versión a mano. |

---

## 9. Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Romper el registro en producción (lote B) | Media | Alto | Rama + prueba unitaria + **sesión real observada** antes de integrar; rollback documentado por tarea |
| Cambiar el punto de entrada diario | Baja | Alto | Prohibido en este plan (regla 1) |
| Pérdida de telemetría (como el 2026-10-09) | Baja (ya corregida) | Medio | Tareas A1/A3 la detectan automáticamente |
| Ruido del `git blame` por refactors de lint | Media | Bajo | Lint solo toca imports/f-strings, en commits aislados por archivo |
| Borrado irreversible de la rama legado | Baja | Medio | Etiqueta anotada primero; `git push --delete` solo con confirmación explícita |
| Cambios de terceros en paralelo (otra sesión/IDE) | Media | Medio | `git status` + `git fetch` antes de cada tarea; rama corta y merge rápido |

---

## 10. Criterios de aceptación globales (fin de la Fase 2)

1. `python -m pytest` → todas las pruebas en verde (mínimo 23 + las nuevas de A1, A3, B1, B3).
2. `python scripts/observer_analyze.py` reporta la actividad **del día en curso** aunque
   `bot_ax.log` esté congelado, y usa `events.jsonl` como fuente principal.
3. `python scripts/chequeo_salud.py` responde con un veredicto claro y detecta
   `TELEMETRIA_CONGELADA` en un escenario simulado.
4. `ruff check src/ tests/ scripts/` sin avisos de `F` ni `I`, y sin los `--exit-zero` en CI.
5. CI en verde en `main` (jobs de pruebas, salud y contexto).
6. `ctxmap refresh .` sin faltantes salvo `LICENSE` (decisión del usuario).
7. El bot registró al menos una sesión real completa después del lote B sin regresiones:
   misma tasa de éxito o mejor, sin IDs equivocados y con capturas retenidas.
8. `docs/plans/plan-implementacion-mejoras.md` actualizado con el estado real de C-1…C-9.

---

## 11. Rollback (por si algo sale mal)

```bash
# Una tarea concreta
git revert <sha> --no-edit            # deshace el commit dejando historia clara

# Un archivo concreto a su versión anterior
git checkout <sha-previo> -- src/services/vision.py

# Todo un lote (volver a la línea base de este plan)
git revert --no-commit <sha1>^..<shaN> && git commit -m "revert: lote X"

# Línea base segura de la Fase 2
# main = d2eae61 · v-00.15.00 · 23/23 pruebas · CI verde
```

Nunca usar `git reset --hard` ni `git push --force` en `main`: la historia del bot es la
única evidencia de lo que hizo cada día.

---

## 12. Orden de ejecución sugerido

```
Semana 1 (sin tocar al bot)
  A1 analizador + events.jsonl      → el proyecto deja de ser ciego
  A3 chequeo de salud               → "¿está trabajando bien?" en 1 comando
  C2 pyproject (ruff/pytest)        → deuda de lint acotada
  C1 rama legado (etiqueta + docs)  → repo sin bifurcaciones fantasma

Semana 2 (preparación del lote B)
  A2 métrica de blacklist           → números honestos
  A4 workflow de salud              → vigilancia en la nube
  C3 lint seguro por archivo        → CI con puerta real
  C4 Makefile (+ decisión de LICENSE)

Ventana de mantenimiento (bot detenido)
  B1 validación de ID por OCR       → evita registrar/blacklistear IDs equivocados
  B3 retención de capturas          → controla el disco
  B2 heartbeat                      → detecta cuelgues
  Sesión real de prueba + integración a main
```

---

*Fin del plan. Cada tarea incluye el porqué (docstring argumentativo), los archivos exactos,
la verificación y el commit. Las reglas inmutables del bot (`docs/manual_proceso_bot.md`)
no se modifican en ninguna tarea de este plan.*
