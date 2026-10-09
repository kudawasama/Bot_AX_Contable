# Plan de Implementación — Fase 2 · Lote A (cierre): alertas de caída, métrica honesta y utilidades

> **Proyecto:** Bot_AX_Contable
> **Fecha:** 2026-10-09
> **Base:** `main` = `64b6e03` · versión **v-00.20.01** · suite **38/38** · CI en verde
> **Plan paraguas:** [`plan-implementacion-fase2.md`](plan-implementacion-fase2.md) (lotes A–D)
> **Estado del lote A:** `A1` ✅ · `A3` ✅ · este documento cierra `A2`, `A4` y los dos
> extras descubiertos durante la implementación.
> **Reglas inmutables:** `docs/manual_proceso_bot.md` · **Protocolo de trabajo:** `AGENTS.md`

---

## 1. Objetivo

Cerrar la observabilidad de una jornada de trabajo: que **cualquier** anomalía real
(caída del bot, log congelado, bot colgado, tasa de error alta, configuración rota)
produzca una señal clara y sin falsos positivos, y que el operador pueda consultarla
en un doble clic.

**Meta medible:** ante un incidente como el del 2026-10-09 (caída por FAIL-SAFE a las
15:24), el operador lo detecta en menos de un minuto **sin abrir archivos**, y el
chequeo nunca grita en falso durante los registros largos normales.

---

## 2. Contexto y supuestos (hechos verificados)

| Hecho | Evidencia |
|---|---|
| **El arreglo del logger quedó verificado en producción** | tras reiniciar el bot (16:11), `logs/bot_ax.log` volvió a crecer con trazas reales (`Click: Confirmar`, `Esperando resultado`, `...esperando (121s)`); 9 líneas del 2026-10-09 |
| El chequeo de salud distingue bien los dos escenarios | con el log congelado: `TELEMETRIA_CONGELADA` + `exit 1` (245,8 min de atraso, con los archivos reales); con el bot sano: `OK`, `Log de texto al día: True` |
| **El bot se cayó por FAIL-SAFE el 2026-10-09 a las 15:24:20** | `failsafe_triggered` + `bot_stop reason="error"`; "mouse moving to a corner of the screen". Los 2 diarios previos: EXITOSO |
| **Ninguna alerta cubre esa caída** | con el bot detenido, el chequeo informaba `OK` (no había sesión abierta). Hueco real |
| **Falso positivo potencial ya visible en la corrida real** | durante la espera del resultado de AX el bot **no emite eventos** (solo escribe en el log de texto): con el umbral fijo de 15 min, `SIN_ACTIVIDAD` saltaría en registros que tardan más de 15 min |
| Bug pre-existente en el analizador | `--registro` se acepta pero se ignora: `main()` llama `leer_registros(BASE_DIR)` sin pasar el argumento |
| Hoy: 63 OK / 14 ERR (81,8%) | `registro_2026-10-09.txt` |

**Supuestos**
1. Las 5 tareas de este plan **no tocan el runtime del bot**: son `scripts/`, `tests/`,
   documentación, un `.bat` nuevo y CI. Se pueden ejecutar con el bot trabajando.
2. No se modifica `Lanzar_Bot.bat` ni `Lanzar_Bot_Registro.bat` (v-00.14.01).
3. El bot puede estar corriendo: la suite es hermética y no toca la pantalla.

---

## 3. Reglas de trabajo (heredadas del plan paraguas)

1. Rama por lote: `feat/fase2-a-cierre`. Integrar con avance normal
   (`git push origin HEAD:main`), nunca con `-f`.
2. **TDD**: primero la prueba que falla, luego el código mínimo, luego verde.
3. **Commit + push por tarea** (Conventional Commits en español).
4. Antes de cada commit: `pytest` 100% verde; `ruff` sin errores nuevos en los archivos tocados.
5. Al cerrar el lote: `ctxmap refresh .` + commit del contexto y actualización del
   estado en el plan paraguas y en `CHANGELOG.md`.
6. Intérprete: `"%LOCALAPPDATA%\Programs\Python\Python312\python.exe"`.
7. Ninguna tarea de este plan altera el comportamiento del bot. Si al implementar
   aparece la tentación de tocar `engine.py`/`vision.py`, se detiene y se propone aparte.

---

## 4. Alcance

| Tarea | Contenido | Riesgo | Archivos |
|---|---|---|---|
| **T1** | Alerta `SESION_TERMINADA_POR_ERROR` (cierra el hueco de la caída del 9-oct) | Nulo | `scripts/chequeo_salud.py`, `tests/test_chequeo_salud.py` |
| **T2** | Arreglar `--registro` ignorado en el analizador | Nulo | `scripts/observer_analyze.py`, `tests/test_observer_analyze.py` |
| **T3** | Evitar el falso `SIN_ACTIVIDAD` durante la espera del resultado de AX | Nulo | `scripts/chequeo_salud.py`, `tests/test_chequeo_salud.py` |
| **T4** | Métrica de lista negra honesta (A2 del plan paraguas) | Nulo | `scripts/observer_analyze.py`, `tests/test_observer_analyze.py` |
| **T5** | Utilidad local (`Chequear_Salud_Bot.bat`), README y humo en CI (A4 reformulado) | Nulo | `.bat` nuevo, `README.md`, `.github/workflows/ci.yml` |

> **Estado (2026-10-09):**
> - **T1** ✅ alerta `SESION_TERMINADA_POR_ERROR` (5 pruebas + demo con los datos reales
>   de la caída de las 15:24).
> - **T2** ✅ opción `--registro` funcional (2 pruebas + verificación con el registro real).
> - **T3** ✅ umbral de espera de 65 min (3 pruebas + chequeo en vivo).
> - **T4** ✅ métrica de lista negra honesta (4 pruebas + corrección del doble conteo de
>   fuentes: 116 → 16 reintentos reales).
> - **T5** ✅ `Chequear_Salud_Bot.bat` probado de verdad, README con la tabla de alertas y
>   humo del chequeo en CI.
> - **Lote A cerrado.** Suite: 53/53 · CI en verde.
> - Los lotes **B** (runtime, requiere bot detenido), **C** (higiene del repo) y **D**
>   (fuera de alcance) del plan paraguas siguen sin iniciar.

**Fuera de alcance (con motivo)**
- **B2 heartbeat**: elimina de raíz el problema de "no hay eventos durante la espera",
  pero toca `engine.py` (runtime) → ventana de mantenimiento, según el plan paraguas.
  T3 es el parche honesto mientras tanto (sin tocar al bot).
- **Lote C** (rama legado, `pyproject.toml`, lint) y **Lote B**: siguen en el plan paraguas.
- **Desactivar el FAIL-SAFE**: ver la decisión abierta en la sección 8. No se cambia nada.

---

## 5. Tareas

### T1 — Alerta `SESION_TERMINADA_POR_ERROR`

**Objetivo:** que una sesión que terminó mal (crash o timeout extremo) se reporte al
operador, en vez de quedar invisible cuando el bot ya no está corriendo.

**Archivos**
- Modificar: `scripts/chequeo_salud.py` (agregar constantes + 2 funciones + 1 alerta + salida)
- Modificar: `tests/test_chequeo_salud.py`

**Paso 1 — Pruebas que fallan** (agregar a `tests/test_chequeo_salud.py`)

```python
class TestCaidasDeSesion:
    """Pruebas de la detección de sesiones que terminaron mal."""

    def test_detecta_caida_por_failsafe_con_el_ultimo_diario(self, tmp_path: Path):
        """Caso real 2026-10-09 15:24: el bot murió por el fail-safe de PyAutoGUI."""
        raiz = _preparar_raiz(tmp_path)
        _escribir_log(raiz, ["[2026-10-09 15:24:19] [INFO] Click: Menu @ (1284,104)"])
        _escribir_eventos(raiz, [
            {"ts": "2026-10-09T15:23:00", "event": "bot_start"},
            {"ts": "2026-10-09T15:24:19", "event": "checkbox_found", "id_normalizado": "00337616"},
            {"ts": "2026-10-09T15:24:19", "event": "failsafe_triggered", "detalle_error": "corner"},
            {"ts": "2026-10-09T15:24:20", "event": "bot_stop", "reason": "error"},
        ])

        resultado = chequeo_salud.chequeo(raiz, ahora=AHORA)

        assert "SESION_TERMINADA_POR_ERROR" in _codigos(resultado)
        assert resultado["caida_reciente"] is True
        assert resultado["ultima_sesion"]["razon"] == "error"
        assert resultado["ultima_sesion"]["ultimo_diario"] == "00337616"

    def test_sesion_cerrada_por_el_usuario_no_alerta(self, tmp_path: Path):
        """ESC del operador es un cierre normal, no un error."""
        raiz = _preparar_raiz(tmp_path)
        _escribir_log(raiz, ["[2026-10-09 14:59:00] [INFO] linea"])
        _escribir_eventos(raiz, [
            {"ts": "2026-10-09T14:50:00", "event": "bot_start"},
            {"ts": "2026-10-09T14:59:00", "event": "bot_stop", "reason": "user_esc"},
            {"ts": "2026-10-09T14:59:30", "event": "confirm_click"},
        ])

        resultado = chequeo_salud.chequeo(raiz, ahora=AHORA)

        assert "SESION_TERMINADA_POR_ERROR" not in _codigos(resultado)
        assert resultado["caida_reciente"] is False

    def test_fin_normal_sin_mas_diarios_no_alerta(self, tmp_path: Path):
        """'no_more_diarios' es el final esperado del trabajo del día."""
        raiz = _preparar_raiz(tmp_path)
        _escribir_log(raiz, ["[2026-10-09 14:59:00] [INFO] linea"])
        _escribir_eventos(raiz, [
            {"ts": "2026-10-09T14:00:00", "event": "bot_start"},
            {"ts": "2026-10-09T14:59:00", "event": "bot_stop", "reason": "no_more_diarios"},
            {"ts": "2026-10-09T14:59:30", "event": "confirm_click"},
        ])

        resultado = chequeo_salud.chequeo(raiz, ahora=AHORA)

        assert "SESION_TERMINADA_POR_ERROR" not in _codigos(resultado)

    def test_caida_antigua_no_alerta_pero_se_informa(self, tmp_path: Path):
        """Una caída de hace más de 24 h no deja el chequeo en rojo para siempre."""
        raiz = _preparar_raiz(tmp_path)
        _escribir_log(raiz, ["[2026-10-09 14:59:00] [INFO] linea"])
        _escribir_eventos(raiz, [
            {"ts": "2026-10-07T15:24:19", "event": "failsafe_triggered"},
            {"ts": "2026-10-07T15:24:20", "event": "bot_stop", "reason": "error"},
            {"ts": "2026-10-09T14:59:30", "event": "confirm_click"},
        ])

        resultado = chequeo_salud.chequeo(raiz, ahora=AHORA)

        assert "SESION_TERMINADA_POR_ERROR" not in _codigos(resultado)
        assert resultado["ultima_sesion"]["razon"] == "error"   # se informa igual
```

**Paso 2 — Verificar que fallan**
`python -m pytest tests/test_chequeo_salud.py -k Caidas -v`
Esperado: FAIL — `KeyError: 'caida_reciente'` / alerta inexistente.

**Paso 3 — Implementación** (en `scripts/chequeo_salud.py`)

Agregar a la zona de umbrales:

```python
# Motivos de cierre de sesión que NO son normales (user_esc y no_more_diarios sí lo son)
RAZONES_ANOMALAS: set[str] = {"error", "timeout_extremo"}
# Horas hacia atrás en las que una caída todavía se considera reciente
UMBRAL_CAIDA_HORAS: int = 24
# Evento que registra el aborto por fail-safe de PyAutoGUI
EVENTO_CAIDA: str = "failsafe_triggered"
```

Agregar (antes de `_sesion_activa`):

```python
def _parsear_ts(ts: Any) -> Optional[datetime]:
    """Convierte un timestamp ISO-8601 en ``datetime`` (o ``None`` si es inválido)."""
    try:
        return datetime.fromisoformat(str(ts))
    except (ValueError, TypeError):
        return None


def analizar_ultima_sesion(eventos: list[dict]) -> dict:
    """Analiza cómo terminó la última sesión del bot.

    POR QUÉ: el 2026-10-09 el bot murió a las 15:24 por el fail-safe de PyAutoGUI
    (mouse en una esquina de la pantalla) y el operador no se enteró: la sesión quedó
    cerrada con ``reason="error"`` y, como no había sesión abierta, el chequeo
    informaba "OK". Una caída no puede depender de que alguien abra el log.

    Args:
        eventos (list[dict]): Eventos de la telemetría (en orden de aparición).

    Returns:
        dict: ``cerrada``, ``razon``, ``marca_cierre``, ``caida`` (marca del último
        fail-safe de la sesión) y ``ultimo_diario`` (último ID visto).
    """
    ultimo_inicio: int = -1
    for indice, evento in enumerate(eventos):
        if str(evento.get("event", "")) == EVENTO_INICIO:
            ultimo_inicio = indice
    sesion: list[dict] = eventos[ultimo_inicio:] if ultimo_inicio >= 0 else list(eventos)

    razon: str = ""
    marca_cierre: Optional[datetime] = None
    for evento in sesion:
        if str(evento.get("event", "")) == EVENTO_FIN:
            razon = str(evento.get("reason", ""))
            marca_cierre = _parsear_ts(evento.get("ts"))

    caida: Optional[datetime] = None
    for evento in reversed(sesion):
        if str(evento.get("event", "")) == EVENTO_CAIDA:
            caida = _parsear_ts(evento.get("ts"))
            break

    ultimo_diario: Optional[str] = None
    for evento in reversed(sesion):
        identificador = evento.get("id_normalizado")
        if identificador:
            ultimo_diario = str(identificador)
            break

    return {
        "cerrada": bool(razon),
        "razon": razon,
        "marca_cierre": marca_cierre,
        "caida": caida,
        "ultimo_diario": ultimo_diario,
    }
```

Dentro de `chequeo()`, después de calcular `activa`:

```python
    ultima_sesion = analizar_ultima_sesion(eventos)
    caida_reciente: bool = False
    marca_caida = ultima_sesion["marca_cierre"] or ultima_sesion["caida"]
    if (
        ultima_sesion["cerrada"]
        and ultima_sesion["razon"] in RAZONES_ANOMALAS
        and marca_caida is not None
    ):
        caida_reciente = (momento - marca_caida) <= timedelta(hours=UMBRAL_CAIDA_HORAS)
```

Y entre las alertas (después de `SIN_EVIDENCIA`):

```python
    if caida_reciente:
        detalle = (
            f"La última sesión terminó con razón '{ultima_sesion['razon']}'"
            f" ({marca_caida.strftime('%Y-%m-%d %H:%M')})"
        )
        if ultima_sesion["caida"] is not None:
            detalle += (
                "; se abortó por el FAIL-SAFE de PyAutoGUI"
                f" ({ultima_sesion['caida'].strftime('%H:%M:%S')}) — revisar si alguien"
                " movió el mouse a una esquina de la pantalla"
            )
        if ultima_sesion["ultimo_diario"]:
            detalle += f". Último diario visto: {ultima_sesion['ultimo_diario']}"
        alertas.append({"codigo": "SESION_TERMINADA_POR_ERROR", "detalle": detalle})
```

Agregar al `return` de `chequeo()` (con las marcas ya convertidas a texto para que el
`--json` sea serializable) y una línea al informe legible:

```python
        "caida_reciente": caida_reciente,
        "ultima_sesion": {
            "cerrada": ultima_sesion["cerrada"],
            "razon": ultima_sesion["razon"],
            "marca_cierre": marca_caida.isoformat() if marca_caida else None,
            "failsafe": ultima_sesion["caida"].isoformat() if ultima_sesion["caida"] else None,
            "ultimo_diario": ultima_sesion["ultimo_diario"],
        },
```

En `imprimir_resultado()`, después de la línea de tasa:

```python
    sesion_previa = resultado["ultima_sesion"]
    if sesion_previa["cerrada"]:
        print(f"  Última sesión cerrada: {sesion_previa['razon']}"
              f" ({sesion_previa['marca_cierre'] or 'sin marca'})")
```

**Paso 4 — Verificar que pasan**
`python -m pytest tests/test_chequeo_salud.py -v` → 11 pruebas PASS.

**Paso 5 — Verificación con los datos reales de hoy**
`python scripts/chequeo_salud.py` → debe informar `Última sesión cerrada: error` y, si
la caída fue hace menos de 24 h, alertar `SESION_TERMINADA_POR_ERROR` con el diario
`00337616`. **Ojo:** si para entonces el bot ya cerró una sesión correcta, la alerta no
aparece (es lo deseado: el sistema reporta la ÚLTIMA sesión).

**Paso 6 — Commit**
```bash
git add scripts/chequeo_salud.py tests/test_chequeo_salud.py
git commit -m "feat: alerta de sesion terminada por error (crash o timeout extremo)"
```

**Criterio de aceptación:** 4 pruebas verdes; con los eventos reales del 2026-10-09 el
chequeo nombra la caída, la hora del fail-safe y el último diario visto.

---

### T2 — Arreglar la opción `--registro` ignorada

**Objetivo:** que `--registro` haga lo que promete (analizar un registro puntual) en vez
de leer siempre todos los `registro_*.txt` del proyecto.

**Archivos**
- Modificar: `scripts/observer_analyze.py:33-54` (`leer_registros`) y `main()` (~línea 940)
- Modificar: `tests/test_observer_analyze.py`

**Paso 1 — Pruebas que fallan**

```python
class TestLecturaDeRegistros:
    """Pruebas del lector de registro_*.txt (incluye el arreglo de --registro)."""

    def test_lee_solo_el_registro_indicado(self, tmp_path: Path):
        """--registro debe limitar la lectura a ese archivo (antes se ignoraba)."""
        (tmp_path / "registro_2026-10-08.txt").write_text(
            "[09:00:00] Diario: W00337501Diat - Resultado: ERROR\n", encoding="utf-8")
        (tmp_path / "registro_2026-10-09.txt").write_text(
            "[10:00:00] Diario: W00337505Diat - Resultado: EXITOSO\n", encoding="utf-8")

        entradas = observer_analyze.leer_registros(
            tmp_path, str(tmp_path / "registro_2026-10-09.txt")
        )

        assert len(entradas) == 1
        assert entradas[0]["id_normalizado"] == "00337505"
        assert entradas[0]["fecha"] == "2026-10-09"

    def test_sin_argumento_lee_todos(self, tmp_path: Path):
        """Sin --registro se mantiene el comportamiento histórico."""
        (tmp_path / "registro_2026-10-08.txt").write_text(
            "[09:00:00] Diario: W00337501Diat - Resultado: ERROR\n", encoding="utf-8")
        (tmp_path / "registro_2026-10-09.txt").write_text(
            "[10:00:00] Diario: W00337505Diat - Resultado: EXITOSO\n", encoding="utf-8")

        entradas = observer_analyze.leer_registros(tmp_path)

        assert len(entradas) == 2
```

**Paso 2 — Verificar que fallan**
`python -m pytest tests/test_observer_analyze.py -k LecturaDeRegistros -v`
Esperado: FAIL — `TypeError: leer_registros() takes 1 positional argument but 2 were given`.

**Paso 3 — Implementación**

```python
def leer_registros(directorio: Path, ruta_especifica: Optional[str] = None) -> list[dict]:
    """Lee los ``registro_*.txt`` y devuelve las entradas parseadas.

    CORRECCIÓN: la opción ``--registro`` se aceptaba en la línea de comandos pero se
    ignoraba (``main()`` nunca la pasaba a esta función), así que el analizador leía
    siempre todos los registros del proyecto. Ahora acepta un archivo puntual o una
    carpeta.

    Args:
        directorio (Path): Raíz del proyecto (búsqueda por defecto).
        ruta_especifica (Optional[str]): Archivo ``registro_*.txt`` o carpeta que los
            contiene. Es lo que recibe ``--registro``.

    Returns:
        list[dict]: Entradas con fecha, hora, ID bruto/normalizado y resultado.
    """
    if ruta_especifica:
        ruta = Path(ruta_especifica)
        archivos = sorted(ruta.glob("registro_*.txt")) if ruta.is_dir() else [ruta]
    else:
        archivos = sorted(directorio.glob("registro_*.txt"))
    entradas = []
    patron = re.compile(
        r'\[(\d{2}:\d{2}:\d{2})\]\s+Diario:\s+(.+?)\s+-\s+Resultado:\s+(\w+)'
    )
    for archivo in archivos:
        if not archivo.exists():
            continue
        fecha_str = archivo.stem.replace("registro_", "")
        ...  # (el resto queda igual)
```
> Requiere `Optional` en el import de `typing` (el archivo hoy no lo importa: usar
> `from typing import Optional` junto a los imports existentes).

Y en `main()`:
```python
    entradas = leer_registros(BASE_DIR, args.registro)
```

**Paso 4 — Verificar que pasan:** `python -m pytest tests/test_observer_analyze.py -v` → 10 PASS.

**Paso 5 — Verificación real**
`python scripts/observer_analyze.py --registro registro_2026-10-09.txt --json` → el JSON
debe contener solo las entradas del 9-oct (63 + 14 = 77 registros hoy).

**Paso 6 — Commit:** `fix: la opcion --registro del analizador ya no se ignora`

---

### T3 — Evitar el falso `SIN_ACTIVIDAD` durante la espera del resultado

**Objetivo:** que el chequeo no grite "sin actividad" mientras el bot espera
legítimamente el resultado de AX (hasta 60 minutos) sin emitir eventos.

**Archivos:** `scripts/chequeo_salud.py`, `tests/test_chequeo_salud.py`

**Paso 1 — Pruebas que fallan**

```python
class TestEsperaDeResultado:
    """Pruebas del umbral de inactividad según el momento del ciclo."""

    def test_no_alerta_durante_la_espera_del_resultado(self, tmp_path: Path):
        """Tras 'confirmar' el bot espera el resultado: 30 min sin eventos es normal."""
        raiz = _preparar_raiz(tmp_path)
        _escribir_log(raiz, ["[2026-10-09 14:30:00] [INFO] ...esperando (1500s)"])
        _escribir_eventos(raiz, [
            {"ts": "2026-10-09T14:29:00", "event": "bot_start"},
            {"ts": "2026-10-09T14:30:00", "event": "confirm_click"},
        ])

        resultado = chequeo_salud.chequeo(raiz, ahora=AHORA)

        assert "SIN_ACTIVIDAD" not in _codigos(resultado)
        assert "TELEMETRIA_CONGELADA" not in _codigos(resultado)

    def test_alerta_al_pasar_la_espera_maxima(self, tmp_path: Path):
        """Más allá de la espera máxima (65 min) sí es anómalo."""
        raiz = _preparar_raiz(tmp_path)
        _escribir_log(raiz, ["[2026-10-09 13:50:00] [INFO] ...esperando (600s)"])
        _escribir_eventos(raiz, [
            {"ts": "2026-10-09T13:50:00", "event": "bot_start"},
            {"ts": "2026-10-09T13:54:00", "event": "confirm_click"},
        ])

        resultado = chequeo_salud.chequeo(raiz, ahora=AHORA)

        assert "SIN_ACTIVIDAD" in _codigos(resultado)

    def test_umbral_normal_de_15_min_sigue_vigente(self, tmp_path: Path):
        """En cualquier otro punto del ciclo, 15 min sin eventos es anómalo."""
        raiz = _preparar_raiz(tmp_path)
        _escribir_log(raiz, ["[2026-10-09 14:40:00] [INFO] Click: Menu @ (1284,104)"])
        _escribir_eventos(raiz, [
            {"ts": "2026-10-09T14:00:00", "event": "bot_start"},
            {"ts": "2026-10-09T14:40:00", "event": "checkbox_found", "id_normalizado": "00337505"},
        ])

        resultado = chequeo_salud.chequeo(raiz, ahora=AHORA)

        assert "SIN_ACTIVIDAD" in _codigos(resultado)
```

**Paso 2 — Verificar que fallan:** `python -m pytest tests/test_chequeo_salud.py -k Espera -v`
Esperado: FAIL en la primera (hoy alertaría a los 30 min).

**Paso 3 — Implementación**

```python
# El bot espera el resultado de AX sin emitir eventos (solo escribe en el log de
# texto): esa espera puede durar hasta 60 min, así que un umbral fijo de 15 min
# produce falsos SIN_ACTIVIDAD en registros lentos.
UMBRAL_ESPERA_RESULTADO_MIN: int = 65
# Último evento que indica que el bot quedó esperando el resultado de AX
EVENTOS_EN_ESPERA: set[str] = {"confirm_click"}


def umbral_sin_actividad(eventos: list[dict]) -> int:
    """Minutos sin eventos antes de alertar, según el punto del ciclo.

    Args:
        eventos (list[dict]): Eventos de la telemetría.

    Returns:
        int: ``UMBRAL_ESPERA_RESULTADO_MIN`` si el último evento dejó al bot
        esperando el resultado de AX; ``UMBRAL_SIN_EVENTOS_MIN`` en cualquier otro caso.
    """
    if not eventos:
        return UMBRAL_SIN_EVENTOS_MIN
    if str(eventos[-1].get("event", "")) in EVENTOS_EN_ESPERA:
        return UMBRAL_ESPERA_RESULTADO_MIN
    return UMBRAL_SIN_EVENTOS_MIN
```

En `chequeo()`, reemplazar los usos del umbral fijo:

```python
    umbral_actividad = umbral_sin_actividad(eventos)
    ...
    actividad_reciente: bool = activa or (
        ultimo_evento_min is not None and ultimo_evento_min <= umbral_actividad
    )
    ...
    if activa and ultimo_evento_min is not None and ultimo_evento_min > umbral_actividad:
        alertas.append({
            "codigo": "SIN_ACTIVIDAD",
            "detalle": (
                f"Sesión abierta sin eventos hace {ultimo_evento_min} min "
                f"(umbral: {umbral_actividad})."
            ),
        })
```
Y agregar `"umbral_actividad_min": umbral_actividad` al `return` (queda visible en `--json`).

**Paso 4 — Verificar que pasan:** 14 pruebas del archivo PASS.
**Paso 5 — Verificación real:** `python scripts/chequeo_salud.py` con el bot esperando un
resultado: `Último evento: N min atrás` pero **sin** alerta hasta 65 min.
**Paso 6 — Commit:** `fix: el chequeo no alerta durante la espera normal del resultado de AX`

**Criterio de aceptación:** los tres escenarios de prueba verdes y ningún falso positivo
en una sesión real con un registro lento (>= 15 min).

---

### T4 — Métrica de lista negra honesta (A2)

**Objetivo:** reemplazar el "cobertura 5,8%" (que se lee como fallo del bot) por dos
números claros: cobertura de la **última sesión** y **histórico** desde la telemetría.

**Archivos:** `scripts/observer_analyze.py`, `tests/test_observer_analyze.py`

**Paso 1 — Pruebas que fallan**

```python
class TestAnalisisBlacklist:
    """Pruebas de la métrica de lista negra (sesión vs histórico)."""

    def test_historico_detecta_reintentos(self):
        """Un mismo ID con dos errores históricos queda marcado como reintentado."""
        eventos = [
            {"ts": "2026-10-08T10:00:00", "event": "result_error", "id_normalizado": "00337501"},
            {"ts": "2026-10-09T10:00:00", "event": "result_error", "id_normalizado": "00337501"},
            {"ts": "2026-10-09T10:05:00", "event": "result_error", "id_normalizado": "00337504"},
        ]

        analisis = observer_analyze.analizar_blacklist([], ["00337501"], eventos)

        assert analisis["errores_historicos_unicos"] == 2
        assert analisis["reintentados"] == {"00337501": 2}
        assert analisis["nunca_en_blacklist"] == ["00337504"]

    def test_cobertura_de_la_ultima_sesion(self):
        """La cobertura útil es la de la última sesión, no la del histórico completo."""
        eventos = [
            {"ts": "2026-10-08T10:00:00", "event": "result_error", "id_normalizado": "00337501"},
            {"ts": "2026-10-09T11:00:00", "event": "result_error", "id_normalizado": "00337511"},
            {"ts": "2026-10-09T11:05:00", "event": "result_error", "id_normalizado": "00337519"},
            {"ts": "2026-10-09T11:05:30", "event": "blacklist_updated", "id_added": "00337519"},
        ]

        analisis = observer_analyze.analizar_blacklist([], ["00337501", "00337519"], eventos)

        assert analisis["ultima_sesion_fecha"] == "2026-10-09"
        assert analisis["ultima_sesion_errores"] == 2
        assert analisis["cobertura_ultima_sesion_pct"] == 50.0

    def test_sin_datos_devuelve_ceros(self):
        """Sin registros ni telemetría no debe romper ni inventar porcentajes."""
        analisis = observer_analyze.analizar_blacklist([], [], [])

        assert analisis["errores_historicos_unicos"] == 0
        assert analisis["cobertura_ultima_sesion_pct"] == 0
        assert analisis["reintentados"] == {}
```

**Paso 2 — Verificar que fallan** (`AttributeError: ... has no attribute 'analizar_blacklist'`).

**Paso 3 — Implementación**

```python
def analizar_blacklist(entradas: list[dict], blacklist: list[str], eventos: list[dict]) -> dict:
    """Compara la lista negra con el histórico de errores y con la última sesión.

    POR QUÉ: el reporte mostraba "cobertura 5,8%" sin explicar que ``blacklist.json``
    se vacía con los botones *Clear Errors* / *Reiniciar* de la GUI. El número se leía
    como un fallo del bot cuando era una lista reiniciada. La telemetría estructurada
    conserva todos los errores históricos, así que permite separar dos preguntas:
    "¿qué errores de la última sesión están en la lista?" (cobertura útil) y "¿qué IDs
    fallaron alguna vez y nunca se saltaron?" (histórico).

    Args:
        entradas (list[dict]): Entradas de los ``registro_*.txt``.
        blacklist (list[str]): IDs presentes hoy en ``blacklist.json``.
        eventos (list[dict]): Eventos de ``logs/events.jsonl``.

    Returns:
        dict: Histórico único, IDs nunca en la lista, reintentos y cobertura de la
        última sesión con datos.
    """
    historico = Counter(
        [e["id_normalizado"] for e in entradas if e["resultado"] == "ERROR"]
        + [
            str(evento.get("id_normalizado"))
            for evento in eventos
            if str(evento.get("event", "")) == "result_error" and evento.get("id_normalizado")
        ]
    )
    por_fecha: dict[str, set[str]] = defaultdict(set)
    for evento in eventos:
        if str(evento.get("event", "")) == "result_error" and evento.get("id_normalizado"):
            por_fecha[str(evento.get("ts", ""))[:10]].add(str(evento["id_normalizado"]))

    ultima_fecha = max(por_fecha) if por_fecha else ""
    ids_ultima = por_fecha.get(ultima_fecha, set())
    en_lista = ids_ultima & set(blacklist)

    return {
        "blacklist_total": len(blacklist),
        "errores_historicos_unicos": len(historico),
        "nunca_en_blacklist": sorted(set(historico) - set(blacklist)),
        "reintentados": {k: v for k, v in historico.items() if v > 1},
        "ultima_sesion_fecha": ultima_fecha,
        "ultima_sesion_errores": len(ids_ultima),
        "cobertura_ultima_sesion_pct": round(len(en_lista) / len(ids_ultima) * 100, 1) if ids_ultima else 0,
        "nota": (
            "blacklist.json se vacía con Clear Errors / Reiniciar: úsala como lista negra "
            "de la sesión. El histórico de errores vive en logs/events.jsonl."
        ),
    }
```

En `generar_reporte()`: agregar `"analisis_blacklist": analizar_blacklist(entradas, blacklist, eventos)`
dentro de `"patrones"` (junto a `gaps_blacklist`, que se mantiene por compatibilidad).

En `imprimir_reporte()`, reemplazar el contenido de la sección `COBERTURA BLACKLIST`:

```python
    print(f"\n🔍 PATRÓN: COBERTURA BLACKLIST")
    bl = p["gaps_blacklist"]
    ab = p["analisis_blacklist"]
    print(f"  Lista negra actual: {ab['blacklist_total']} diarios")
    print(f"  Última sesión ({ab['ultima_sesion_fecha'] or 'sin datos'}): "
          f"{ab['ultima_sesion_errores']} errores, "
          f"{ab['cobertura_ultima_sesion_pct']}% ya en la lista")
    print(f"  Histórico: {ab['errores_historicos_unicos']} IDs con error alguna vez · "
          f"{len(ab['nunca_en_blacklist'])} nunca en la lista · "
          f"{len(ab['reintentados'])} reintentados")
    if ab["reintentados"]:
        print(f"    Reintentados (ID: cantidad): {ab['reintentados']}")
    print(f"  Nota: {ab['nota']}")
    if bl["cobertura_blacklist_pct"]:
        print(f"  (referencia histórica sobre registros: {bl['cobertura_blacklist_pct']}%)")
```

**Paso 4 — Verificar que pasan:** 13 pruebas del archivo PASS.
**Paso 5 — Verificación real:** `python scripts/observer_analyze.py` → la sección debe
mostrar los números de hoy (14 errores en la última sesión, cuántos ya en la lista, y los
IDs reintentados del histórico) y la nota explicativa.
**Paso 6 — Commit:** `fix: la cobertura de blacklist distingue la sesion del historico`

**Criterio de aceptación:** el reporte responde en una línea "¿cuántos errores de hoy
están en la lista?" y "¿cuántos IDs fallaron alguna vez sin estar en la lista?".

---

### T5 — Utilidad local, README y humo en CI (A4 reformulado)

**Objetivo:** que el operador pueda consultar la salud con un doble clic, y que las
herramientas nuevas no se rompan en silencio.

**Hallazgo que motiva el cambio de A4:** un workflow en la nube aporta poco aquí (en CI
no existen `logs/` ni `registro_*.txt`, que están en `.gitignore`, así que el chequeo
solo puede probar que el script **funciona**, no evaluar salud real). El valor está en
lo local.

**Paso 1 — Crear `Chequear_Salud_Bot.bat`** (raíz del proyecto; NO reemplaza ni toca los
lanzadores existentes)

```bat
@echo off
title Bot AX Contable - Chequeo de salud
:: Raiz = carpeta de este .bat (funciona en cualquier unidad, igual que la utilidad
:: de salud no toca el runtime del bot: solo lee archivos)
cd /d "%~dp0"
if not exist "scripts\chequeo_salud.py" (
    echo ERROR: no se encontro scripts\chequeo_salud.py en %~dp0
    pause
    exit /b 1
)
set "PY="
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not defined PY for /f "delims=" %%i in ('where python 2^>nul') do if not defined PY set "PY=%%i"
if not defined PY (
    echo ERROR: No se encontro Python. Instala Python 3.11+ o agregalo al PATH.
    pause
    exit /b 1
)
set PYTHONPATH=%cd%
"%PY%" scripts\chequeo_salud.py
echo.
pause
```

**Paso 2 — Probar el `.bat` de verdad**
`cmd.exe /c "Chequear_Salud_Bot.bat" < /dev/null` (el `< /dev/null` responde al `pause`).
Esperado: el informe completo del chequeo y salida limpia.
> No se usa el truco de "copia con echo" del plan anterior: este `.bat` es de **solo
> lectura** (no lanza el bot), así que ejecutarlo no tiene riesgo.

**Paso 3 — README.md**: en "Estructura del proyecto" agregar `Chequear_Salud_Bot.bat`, y
después de la sección de Uso agregar:

```markdown
## 🩺 ¿Está trabajando bien el bot?

```bash
python scripts/chequeo_salud.py            # informe legible
python scripts/chequeo_salud.py --json     # para scripts
python scripts/chequeo_salud.py --estricto # exit 1 si hay alertas (cron/CI)
```

O doble clic en `Chequear_Salud_Bot.bat`. Alertas posibles:

| Alerta | Qué significa |
|--------|---------------|
| `SESION_TERMINADA_POR_ERROR` | La última sesión murió (crash de PyAutoGUI o timeout extremo) |
| `TELEMETRIA_CONGELADA` | El bot está activo pero `logs/bot_ax.log` quedó atrás |
| `SIN_ACTIVIDAD` | Sesión abierta sin eventos más allá de lo normal |
| `TASA_ERROR_ALTA` | Más de 25% de errores hoy |
| `CONFIG_INVALIDA` | `config_sectores.json` o `blacklist.json` ilegibles |
| `SIN_EVIDENCIA` | No hay telemetría ni log que analizar |
```

**Paso 4 — `.github/workflows/ci.yml`**: agregar a `jobs.pruebas.steps`, después de la
suite:

```yaml
      - name: Humo del chequeo de salud
        # En CI no existen logs/ ni registro_*.txt (están en .gitignore): el objetivo
        # es verificar que la herramienta arranca y devuelve JSON válido, no evaluar salud.
        run: python scripts/chequeo_salud.py --json
```

**Paso 5 — Verificar:** `gh run list --limit 3` con el run en verde tras el push;
`README.md` renderizado correcto (revisar el archivo, no el render de GitHub).

**Paso 6 — Commit:**
```bash
git add Chequear_Salud_Bot.bat README.md .github/workflows/ci.yml
git commit -m "feat: utilidad Chequear_Salud_Bot.bat, README y humo del chequeo en CI"
```

**Criterio de aceptación:** el `.bat` muestra el informe en un doble clic; el README
documenta las 6 alertas; CI verde con el paso nuevo.

---

## 6. Verificación pendiente al próximo arranque del bot (checklist)

Estas dos cosas dependen del bot, no del código de este plan:

- [x] **`logs/bot_ax.log` vuelve a crecer** — verificado tras el reinicio del 2026-10-09
  16:11 (trazas reales de `Confirmar`, `Esperando resultado`, `...esperando (121s)`).
- [ ] **El chequeo no da falsos positivos en un registro largo real** (espera de AX
  superior a 15 min): después de T3, con el bot trabajando, `python scripts/chequeo_salud.py`
  debe decir `Estado general: OK`.

---

## 7. Indicadores de éxito

| Métrica | Antes | Después de este plan |
|---|---|---|
| Alertas del chequeo | 5 | 6 (incluye caída de sesión) |
| Caída del bot detectada sin abrir archivos | No | Sí, con hora, motivo y último diario |
| Falsos positivos en esperas de 15–60 min | 1 (garantizado) | 0 |
| `--registro` del analizador | Ignorado | Funcional |
| "Cobertura de blacklist" | Un porcentaje ambiguo | Cobertura de sesión + histórico + nota |
| Pruebas de la suite | 38 | ~53 |
| Consulta de salud del operador | Abrir archivos a mano | Doble clic en `Chequear_Salud_Bot.bat` |

---

## 8. Decisión abierta: el FAIL-SAFE de PyAutoGUI

El bot no define `pyautogui.FAILSAFE`, así que usa el valor por defecto (`True`): si el
mouse llega a una esquina de la pantalla, la siguiente acción de PyAutoGUI aborta. El
2026-10-09 a las 15:24 eso terminó la sesión (razón `error`, registrada en
`events.jsonl` y ahora también en el chequeo).

| Opción | Efecto | Recomendación |
|---|---|---|
| **A) Dejarlo como está** + alerta de T1 | El operador conserva un botón de pánico (mover el mouse a la esquina detiene el bot); las caídas ahora se reportan | ✅ **Recomendada** |
| B) `pyautogui.FAILSAFE = False` | Evita la caída, pero pierde el aborto de emergencia y puede dejar al bot haciendo clics sin control | ❌ No recomendada |
| C) Reubicar el mouse al empezar cada ciclo | No resuelve el caso real (que alguien mueva el mouse **durante** la espera) y agrega movimiento innecesario | ❌ No aporta |

**Decisión: no se cambia nada en este plan.** Se documenta aquí para que la elección
quede registrada y no se "arregle" por accidente en el futuro.

---

## 9. Riesgos y mitigaciones

| Riesgo | Prob. | Impacto | Mitigación |
|---|---|---|---|
| Romper una herramienta que ya está en verde | Baja | Medio | TDD por tarea + suite completa antes de cada commit + CI |
| Alerta `SESION_TERMINADA_POR_ERROR` molesta tras una caída vieja | Media | Bajo | Ventana de 24 h (`UMBRAL_CAIDA_HORAS`) y prueba que la cubre |
| El umbral de espera (65 min) tapa un cuelgue real | Baja | Medio | `umbral_actividad_min` queda visible en el JSON; B2 (heartbeat) lo resuelve de raíz |
| Duplicar el análisis de blacklist (dos secciones) | Media | Bajo | La sección nueva es la principal; la histórica queda como referencia etiquetada |
| Tocar el runtime por entusiasmo | Baja | Alto | Regla 7: cualquier cosa que toque `engine.py`/`vision.py` sale de este plan |

---

## 10. Rollback

```bash
# Una tarea
git revert <sha> --no-edit

# El lote completo (volver a la base de este plan)
git revert --no-commit 64b6e03..HEAD && git commit -m "revert: lote A (cierre)"

# Base segura
# main = 64b6e03 · v-00.20.01 · suite 38/38 · CI verde
```
Nunca `git reset --hard` ni `git push --force` sobre `main`.

---

## 11. Orden de ejecución sugerido

```
1. T1  alerta de caída          ← cierra el hueco encontrado en vivo hoy
2. T3  umbral de espera         ← elimina el falso positivo ya visible
3. T2  --registro               ← arreglo puntual del analizador
4. T4  blacklist honesta        ← cierra A2 del plan paraguas
5. T5  utilidad + README + CI   ← cierra A4 reformulado
6. ctxmap refresh + estado en el plan paraguas + push a main
```

Cada tarea es independiente: si algo se pospone, las anteriores siguen siendo válidas.

---

*Fin del plan. Ninguna tarea modifica el comportamiento del bot en ejecución: todo el
trabajo vive en `scripts/`, `tests/`, documentación, un `.bat` nuevo de solo lectura y CI.
Las reglas inmutables de `docs/manual_proceso_bot.md` no se tocan.*
