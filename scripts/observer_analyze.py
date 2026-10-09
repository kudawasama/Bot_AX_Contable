#!/usr/bin/env python3
"""
Observer Analyzer — Fase A del loop de aprendizaje del Bot AX Contable.

Analiza la evidencia observable (registros, blacklist, log de ejecución, capturas)
SIN tocar el bot en runtime. Produce un diagnóstico estructurado con:
  - Métricas de la sesión
  - Patrones de error detectados
  - Correlación con el código fuente
  - Propuestas de mejora accionables

Uso:
    python scripts/observer_analyze.py
    python scripts/observer_analyze.py --log logs/bot_ax.log --registro registro_2026-06-17.txt
"""

import os
import re
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter, defaultdict

# Raíz del proyecto (scripts/ -> raíz)
BASE_DIR = Path(__file__).resolve().parent.parent


# ──────────────────────────────────────────────────────────────
# 1. LECTORES DE EVIDENCIA
# ──────────────────────────────────────────────────────────────

def leer_registros(directorio: Path, ruta_especifica: str | None = None) -> list[dict]:
    """Lee los ``registro_*.txt`` y devuelve las entradas parseadas.

    CORRECCIÓN (bug): la opción ``--registro`` se aceptaba en la línea de comandos
    pero ``main()`` nunca la pasaba a esta función, así que el analizador leía siempre
    todos los ``registro_*.txt`` del proyecto y el filtro del operador no servía de nada.

    Args:
        directorio (Path): Raíz del proyecto (búsqueda por defecto).
        ruta_especifica (str | None): Archivo ``registro_*.txt`` o carpeta que los
            contiene. Es lo que recibe la opción ``--registro``.

    Returns:
        list[dict]: Entradas con fecha, hora, ID bruto/normalizado, resultado y archivo.
    """
    entradas = []
    patron = re.compile(
        r'\[(\d{2}:\d{2}:\d{2})\]\s+Diario:\s+(.+?)\s+-\s+Resultado:\s+(\w+)'
    )
    if ruta_especifica:
        ruta = Path(ruta_especifica)
        archivos = sorted(ruta.glob("registro_*.txt")) if ruta.is_dir() else [ruta]
    else:
        archivos = sorted(directorio.glob("registro_*.txt"))
    for archivo in archivos:
        if not archivo.exists():
            continue
        fecha_str = archivo.stem.replace("registro_", "")
        texto = archivo.read_text(encoding="utf-8")
        for linea in texto.splitlines():
            m = patron.match(linea.strip())
            if m:
                hora, id_bruto, resultado = m.groups()
                entradas.append({
                    "fecha": fecha_str,
                    "hora": hora,
                    "id_bruto": id_bruto,
                    "id_normalizado": normalizar_id(id_bruto),
                    "resultado": resultado,
                    "archivo": archivo.name,
                })
    return entradas


def normalizar_id(id_bruto: str) -> str:
    """Normaliza ID igual que el bot: extrae 6+ dígitos."""
    digitos = re.findall(r'\d{6,}', id_bruto)
    return digitos[0] if digitos else id_bruto.strip().upper()


def leer_blacklist(directorio: Path) -> list[str]:
    """Lee blacklist.json."""
    ruta = directorio / "blacklist.json"
    if not ruta.exists():
        return []
    try:
        data = json.loads(ruta.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def leer_log(directorio: Path, ruta_especifica: str = None) -> list[str]:
    """Lee el log de ejecución. Usa logs/bot_ax.log por defecto."""
    if ruta_especifica:
        ruta = Path(ruta_especifica)
    else:
        ruta = directorio / "logs" / "bot_ax.log"
    if not ruta.exists():
        return []
    return ruta.read_text(encoding="utf-8", errors="replace").splitlines()


def listar_capturas(directorio: Path) -> list[str]:
    """Lista archivos de capturas de error."""
    carpeta = directorio / "logs" / "capturas"
    if not carpeta.exists():
        return []
    return sorted([f.name for f in carpeta.glob("*.png")])


# ──────────────────────────────────────────────────────────────
# 1c. LECTURA DE TELEMETRÍA ESTRUCTURADA (logs/events.jsonl)
# ──────────────────────────────────────────────────────────────
#
# POR QUÉ: el analizador se apoyaba solo en ``logs/bot_ax.log``, escrito por un
# handler con descriptor abierto. Entre el 2026-10-08 10:52 y el 2026-10-09 11:53
# ese descriptor quedó huérfano (Google Drive reemplazó el archivo) y el log dejó
# de crecer: el analizador siguió reportando datos viejos sin avisar, mientras
# ``logs/events.jsonl`` —escrito con open/append/close por evento— estaba al día.
# Desde la v-00.13.02 el log de texto está blindado, pero la telemetría
# estructurada debe ser fuente de primera clase: es a prueba de fallos y más
# precisa que hacer regex sobre texto libre.

_EVENTS_FILE: str = "events.jsonl"


def ruta_eventos(directorio: Path) -> Path:
    """Devuelve la ruta de ``logs/events.jsonl`` dentro del proyecto.

    Args:
        directorio (Path): Raíz del proyecto.

    Returns:
        Path: Ruta del archivo de telemetría estructurada.
    """
    return directorio / "logs" / _EVENTS_FILE


def leer_eventos(ruta: Path) -> list[dict]:
    """Lee la telemetría estructurada de ``logs/events.jsonl``.

    Cada línea es un objeto JSON independiente (``{"ts": ..., "event": ...}``).
    Las líneas vacías o corruptas (escritura interrumpida a medio vuelo) se
    ignoran: un archivo parcialmente escrito nunca debe romper el análisis.

    Args:
        ruta (Path): Ruta del archivo JSONL.

    Returns:
        list[dict]: Eventos válidos, en orden de aparición.
    """
    if not Path(ruta).exists():
        return []
    eventos: list[dict] = []
    with open(ruta, "r", encoding="utf-8", errors="replace") as archivo:
        for linea in archivo:
            linea = linea.strip()
            if not linea:
                continue
            try:
                evento = json.loads(linea)
            except json.JSONDecodeError:
                continue
            if isinstance(evento, dict):
                eventos.append(evento)
    return eventos


def ultima_fecha_eventos(eventos: list[dict]) -> str:
    """Devuelve la fecha (``YYYY-MM-DD``) del evento más reciente.

    Args:
        eventos (list[dict]): Eventos de la telemetría.

    Returns:
        str: Fecha más reciente, o cadena vacía si no hay eventos con timestamp.
    """
    fechas = [str(e.get("ts", ""))[:10] for e in eventos if e.get("ts")]
    return max(fechas) if fechas else ""


def _parsear_timestamp_evento(ts: str) -> datetime | None:
    """Convierte un timestamp ISO-8601 de la telemetría en ``datetime``.

    Args:
        ts (str): Marca de tiempo del evento (``2026-10-09T14:56:39.666522``).

    Returns:
        datetime | None: La marca convertida, o ``None`` si es inválida.
    """
    try:
        return datetime.fromisoformat(str(ts))
    except (ValueError, TypeError):
        return None


def ultimo_timestamp_eventos(eventos: list[dict]) -> datetime | None:
    """Devuelve la marca de tiempo más reciente de la telemetría.

    Args:
        eventos (list[dict]): Eventos de la telemetría estructurada.

    Returns:
        datetime | None: La marca más reciente, o ``None`` si no hay ninguna.
    """
    marcas = [
        marca for marca in (
            _parsear_timestamp_evento(str(evento.get("ts", ""))) for evento in eventos
        ) if marca is not None
    ]
    return max(marcas) if marcas else None


def ultimo_timestamp_log(lineas_log: list[str]) -> datetime | None:
    """Devuelve la marca de tiempo más reciente del log de texto.

    Las líneas con timestamp malformado (solo fecha, sin hora) se ignoran para no
    falsear la comparación con la telemetría.

    Args:
        lineas_log (list[str]): Líneas del log de texto.

    Returns:
        datetime | None: La marca más reciente, o ``None`` si no hay ninguna.
    """
    marcas: list[datetime] = []
    for linea in lineas_log:
        parsed = parsear_linea_log(linea)
        if not parsed:
            continue
        try:
            marcas.append(
                datetime.strptime(f"{parsed['fecha']} {parsed['hora']}", "%Y-%m-%d %H:%M:%S")
            )
        except ValueError:
            continue
    return max(marcas) if marcas else None


def telemetria_mas_nueva_que_log(lineas_log: list[str], eventos: list[dict]) -> bool:
    """Indica si la telemetría tiene actividad posterior al log de texto.

    Es la señal exacta del incidente 2026-10-08/09 (log congelado mientras los
    eventos avanzaban). Cuando devuelve ``True``, los patrones basados en
    ``bot_ax.log`` son parciales y deben leerse con esa advertencia.

    POR QUÉ SE COMPARA POR MARCA DE TIEMPO Y NO POR FECHA: el 2026-10-09 el log
    estaba congelado desde las 10:52 del día anterior, pero bastaba una sola
    escritura del mismo día (por ejemplo una verificación manual) para que la
    comparación por FECHA dictaminara "al día" y el aviso nunca apareciera.
    Comparando marcas de tiempo se detecta el desfase real.

    Args:
        lineas_log (list[str]): Líneas del log de texto.
        eventos (list[dict]): Eventos de la telemetría estructurada.

    Returns:
        bool: ``True`` si la telemetría es más reciente que el log.
    """
    marca_eventos = ultimo_timestamp_eventos(eventos)
    if marca_eventos is None:
        return False
    marca_log = ultimo_timestamp_log(lineas_log)
    return marca_log is None or marca_eventos > marca_log


def resumir_lista_eventos(eventos: list[dict]) -> dict:
    """Resume una lista de eventos (núcleo puro, sin acceso a disco).

    Args:
        eventos (list[dict]): Eventos ya parseados de ``events.jsonl``.

    Returns:
        dict: Contadores por tipo, éxitos, errores, IDs con error, timeouts,
        fallbacks de Sector B, última fecha y desglose por sesión (fecha).
    """
    por_tipo: Counter = Counter()
    ids_error: list[str] = []
    sesiones: dict[str, dict[str, int]] = defaultdict(lambda: {"exitos": 0, "errores": 0})
    timeouts = 0
    fallbacks = 0

    for evento in eventos:
        tipo = str(evento.get("event", ""))
        por_tipo[tipo] += 1
        if tipo == "result_exito":
            sesiones[str(evento.get("ts", ""))[:10]]["exitos"] += 1
        elif tipo == "result_error":
            sesiones[str(evento.get("ts", ""))[:10]]["errores"] += 1
            identificador = evento.get("id_normalizado")
            if identificador:
                ids_error.append(str(identificador))
        elif tipo in ("timeout_menu", "timeout_confirm", "result_timeout"):
            timeouts += 1
        elif tipo == "sector_b_fallback":
            fallbacks += 1

    return {
        "total_eventos": len(eventos),
        "por_tipo": dict(por_tipo),
        "exitos": por_tipo.get("result_exito", 0),
        "errores": por_tipo.get("result_error", 0),
        "ids_error": ids_error,
        "ids_error_unicos": len(set(ids_error)),
        "timeouts": timeouts,
        "fallbacks_sector_b": fallbacks,
        "ultima_fecha": ultima_fecha_eventos(eventos),
        "sesiones": {fecha: dict(valores) for fecha, valores in sorted(sesiones.items())},
        "log_desactualizado": False,
    }


def resumir_eventos(ruta: Path) -> dict:
    """Lee y resume ``logs/events.jsonl`` (telemetría estructurada).

    Args:
        ruta (Path): Ruta del archivo JSONL de eventos.

    Returns:
        dict: Igual que :func:`resumir_lista_eventos`.
    """
    return resumir_lista_eventos(leer_eventos(ruta))


# ──────────────────────────────────────────────────────────────
# 1b. UTILIDADES DE PARSING DE LÍNEAS DE LOG
# ──────────────────────────────────────────────────────────────

# Patrones de timestamp del log:
#   - Formato completo:  [2026-06-05 11:59:12]
#   - Formato malformado (solo fecha, sin hora):  [2026-06-12]
_PATRON_TS_COMPLETO = re.compile(
    r'^\[(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})\]\s+\[(\w+)\]\s+(.*)$'
)
_PATRON_TS_FECHA = re.compile(
    r'^\[(\d{4}-\d{2}-\d{2})\]\s+\[(\w+)\]\s+(.*)$'
)


def parsear_linea_log(linea: str) -> dict | None:
    """Parsea una línea del log y devuelve dict con timestamp, nivel, mensaje.

    Maneja dos formatos de timestamp:
      - Completo: [2026-06-05 11:59:12] [WARNING] mensaje
      - Solo fecha: [2026-06-12] [WARNING] mensaje  (malformado, sin hora)

    Devuelve None si la línea no matchea ningún formato conocido.
    """
    linea = linea.rstrip('\r\n')
    m = _PATRON_TS_COMPLETO.match(linea)
    if m:
        fecha, hora, nivel, mensaje = m.groups()
        return {
            "fecha": fecha,
            "hora": hora,
            "timestamp": f"{fecha} {hora}",
            "nivel": nivel,
            "mensaje": mensaje,
        }
    m = _PATRON_TS_FECHA.match(linea)
    if m:
        fecha, nivel, mensaje = m.groups()
        return {
            "fecha": fecha,
            "hora": "00:00:00",  # hora desconocida, usar medianoche como fallback
            "timestamp": fecha,  # sin hora
            "nivel": nivel,
            "mensaje": mensaje,
        }
    return None


def normalizar_elemento(texto: str) -> str:
    """Normaliza un nombre de elemento: extrae el basename de un path o devuelve el texto limpio.

    Ejemplos:
      'H:\\...\\patrones\\btn_registrar_confirm.png' -> 'btn_registrar_confirm.png'
      'Confirmar' -> 'Confirmar'
      'btn_registrar_confirm.png' -> 'btn_registrar_confirm.png'
    """
    # Si contiene separadores de path (\\ o /), extraer el basename
    if '\\' in texto or '/' in texto:
        # Normalizar separadores y tomar última parte
        normalizado = texto.replace('\\', '/').rstrip('/')
        partes = normalizado.rsplit('/', 1)
        return partes[-1] if partes else texto
    return texto


# ──────────────────────────────────────────────────────────────
# 2. DETECTORES DE PATRONES
# ──────────────────────────────────────────────────────────────

def detectar_ruido_ocr(entradas: list[dict]) -> dict:
    """Detecta inconsistencias en la lectura OCR de IDs."""
    # Agrupar por ID normalizado y ver cuántas variantes brutas hay
    variantes: dict[str, set[str]] = defaultdict(set)
    for e in entradas:
        variantes[e["id_normalizado"]].add(e["id_bruto"])

    # IDs con múltiples lecturas diferentes
    inestables = {
        k: list(v) for k, v in variantes.items() if len(v) > 1
    }

    # Análisis de prefijos/sufijos basura
    prefijos = Counter()
    sufijos = Counter()
    for e in entradas:
        idb = e["id_bruto"]
        # Prefijo: caracteres antes del primer dígito
        m = re.match(r'^([^\d]*)', idb)
        if m and m.group(1):
            prefijos[m.group(1)] += 1
        # Sufijo: caracteres después del último dígito
        m = re.search(r'([^0-9]*)$', idb)
        if m and m.group(1):
            sufijos[m.group(1)] += 1

    # Casos donde la normalización falla (no hay 6+ dígitos)
    sin_digitos = [
        e for e in entradas
        if e["id_normalizado"] == e["id_bruto"].strip().upper()
        and not re.search(r'\d{6,}', e["id_bruto"])
    ]

    return {
        "ids_con_lectura_inestable": len(inestables),
        "ejemplos_inestables": dict(list(inestables.items())[:5]),
        "prefijos_basura_mas_frecuentes": prefijos.most_common(5),
        "sufijos_basura_mas_frecuentes": sufijos.most_common(5),
        "ids_sin_digitos_suficientes": len(sin_digitos),
        "ejemplos_sin_digitos": [e["id_bruto"] for e in sin_digitos[:5]],
    }


def detectar_errores_agrupados(entradas: list[dict]) -> list[dict]:
    """Detecta ráfagas de errores concentrados en tiempo."""
    errores = sorted(
        [e for e in entradas if e["resultado"] == "ERROR"],
        key=lambda x: (x["fecha"], x["hora"])
    )
    if not errores:
        return []

    clusters = []
    actual = [errores[0]]
    for prev, curr in zip(errores, errores[1:]):
        # Si están en la misma fecha y a menos de 2 minutos
        if prev["fecha"] == curr["fecha"]:
            t_prev = datetime.strptime(prev["hora"], "%H:%M:%S")
            t_curr = datetime.strptime(curr["hora"], "%H:%M:%S")
            if (t_curr - t_prev) <= timedelta(minutes=2):
                actual.append(curr)
                continue
        if len(actual) >= 2:
            clusters.append({
                "fecha": actual[0]["fecha"],
                "hora_inicio": actual[0]["hora"],
                "hora_fin": actual[-1]["hora"],
                "cantidad": len(actual),
                "ids": [e["id_normalizado"] for e in actual],
            })
        actual = [curr]
    if len(actual) >= 2:
        clusters.append({
            "fecha": actual[0]["fecha"],
            "hora_inicio": actual[0]["hora"],
            "hora_fin": actual[-1]["hora"],
            "cantidad": len(actual),
            "ids": [e["id_normalizado"] for e in actual],
        })
    return clusters


# --- Patrones de detección de eventos del log ---

# FUERA SECTOR B — 3 formatos históricos:
#   viejo:      "<PATH> detectado FUERA del sector. Actualizar coordenadas."
#   intermedio: "btn_registrar_menu.png fuera de sector B - redefinir area"
#   actual:     "Menu fuera de sector B"
_PATRON_FUERA_SECTOR = re.compile(
    r'(?:fuera de sector B|detectado FUERA del sector)',
    re.IGNORECASE
)

# TIMEOUTS — 3 formatos históricos:
#   viejo:      "Timeout: No se pudo encontrar <PATH> en 20 segundos."
#   intermedio: "Timeout: btn_registrar_confirm.png no encontrado (20s)."
#   actual:     "Timeout: Confirmar no encontrado (20s)."
# Grupo 1 = segundos en formato (Ns), grupo 2 = segundos en formato "en N segundos"
_PATRON_TIMEOUT = re.compile(
    r'Timeout:.*?(?:'
    r'no encontrado.*?\((\d+)s\)'       # formatos intermedio y actual: (20s)
    r'|'
    r'no se pudo encontrar.*?en (\d+) segundos'  # formato viejo: en 20 segundos
    r')',
    re.IGNORECASE
)
# Para extraer el elemento del timeout
_PATRON_TIMEOUT_ELEMENTO_VIEJO = re.compile(
    r'Timeout:\s*No se pudo encontrar\s+(.+?)\s+en \d+ segundos',
    re.IGNORECASE
)
_PATRON_TIMEOUT_ELEMENTO_NUEVO = re.compile(
    r'Timeout:\s*(.+?)\s+no encontrado\s*\(\d+s\)',
    re.IGNORECASE
)

# ERROR AX — 2 formatos históricos (nivel [WARNING] en ambos):
#   viejo:  "-> Apareció un Error de Registro de AX!"
#   actual: "-> ERROR de Registro AX!"
_PATRON_ERROR_AX = re.compile(
    r'(?:Apareció un\s+)?Error de Registro(?:\s+AX|\s+de\s+AX)!',
    re.IGNORECASE
)

# ERRORES [ERROR] — crashes de fail-safe de PyAutoGUI
#   "[ERROR] Error durante la búsqueda de imagen: PyAutoGUI fail-safe triggered..."
_PATRON_ERROR_FAILSAFE = re.compile(
    r'Error durante la b.*?squeda de imagen.*?fail-safe',
    re.IGNORECASE
)

# ÉXITO — 3 formatos históricos (nivel [INFO]):
#   viejo:  "-> Registro en AX completado exitosamente! (checkbox)"
#   viejo:  "-> Registro en AX completado exitosamente! (pop-up)"
#   actual: "-> EXITO! (pop-up confirmado)"
_PATRON_EXITO = re.compile(
    r'(?:EXITO!|completado exitosamente)',
    re.IGNORECASE
)

# CLICS DE MENÚ — 3 formatos históricos:
#   viejo:      "Click en: <PATH>\\btn_registrar_menu.png en (1284, 104)"
#   intermedio: "Click: btn_registrar_menu.png @ (1284,104)"
#   actual:     "Click: Menu @ (1284,104)"
_PATRON_CLICK_MENU = re.compile(
    r'Click(?:\s+en)?:\s+'
    r'(?:.*?[\\/])?'           # opcional path antes del nombre
    r'(?:btn_registrar_menu\.png|Menu)'
    r'\s*(?:@|en)\s*\(',
    re.IGNORECASE
)

# WARNING de "Region muy pequeña" — se emite junto con "fuera de sector B"
# No es un fallback por sí mismo; es un síntoma del mismo evento.
_PATRON_REGION_PEQUENA = re.compile(
    r'Region.*?muy peque.*?Buscando en pantalla completa',
    re.IGNORECASE
)


def detectar_fallback_sector_b(lineas_log: list[str]) -> dict:
    """Cuenta cuántas veces el bot cae al fallback de pantalla completa.

    Bug corregido (ratio_fallback_pct > 100%):
    El contador anterior sumaba TODAS las líneas "fuera de sector B" como
    fallbacks, pero cada clic del menú puede generar MÚLTIPLES warnings:
      1. "Region muy pequeña para ... Buscando en pantalla completa."
      2. "fuera de sector B" (o "detectado FUERA del sector")
    Ambas líneas describen el MISMO evento de fallback. Contar las dos
    infla el numerador.

    Corrección: contar eventos de fallback únicos usando el patrón
    "Region muy pequeña ... Buscando en pantalla completa" como indicador
    de fallback real (es el que dice explícitamente "Buscando en pantalla
    completa"), y NO contar las líneas "fuera de sector B" como fallbacks
    separados. Las líneas "fuera de sector B" son warnings de diagnóstico
    que acompañan al fallback pero no son eventos adicionales.

    Además, contar TODOS los formatos históricos de "Click de menú":
      - "Click en: <PATH>\\btn_registrar_menu.png en (x, y)"  (viejo)
      - "Click: btn_registrar_menu.png @ (x,y)"               (intermedio)
      - "Click: Menu @ (x,y)"                                 (actual)
    """
    total_clics_menu = 0
    fallbacks = 0
    timeouts_menu = 0
    warnings_fuera_sector = 0  # informativo, no se usa en el ratio

    for linea in lineas_log:
        # Contar clics de menú (todos los formatos)
        if _PATRON_CLICK_MENU.search(linea):
            total_clics_menu += 1
        # Contar fallbacks reales: "Region muy pequeña ... Buscando en pantalla completa"
        if _PATRON_REGION_PEQUENA.search(linea):
            fallbacks += 1
        # Contar warnings de fuera de sector (informativo)
        if _PATRON_FUERA_SECTOR.search(linea):
            warnings_fuera_sector += 1
        # Timeouts de menú: "Timeout: ... Menu no encontrado ..."
        if re.search(r'Timeout:.*Menu.*no encontrado', linea, re.IGNORECASE):
            timeouts_menu += 1

    ratio = (fallbacks / total_clics_menu * 100) if total_clics_menu else 0
    return {
        "total_clics_menu": total_clics_menu,
        "fallbacks_pantalla_completa": fallbacks,
        "warnings_fuera_sector_b": warnings_fuera_sector,
        "ratio_fallback_pct": round(ratio, 1),
        "timeouts_menu": timeouts_menu,
        "diagnostico": (
            "Sector B mal calibrado" if ratio > 80
            else "Sector B aceptable" if ratio < 20
            else "Sector B con fallbacks frecuentes"
        ),
    }


def detectar_gaps_blacklist(entradas: list[dict], blacklist: list[str]) -> dict:
    """Detecta IDs que dieron ERROR pero no están en la blacklist."""
    ids_error = {e["id_normalizado"] for e in entradas if e["resultado"] == "ERROR"}
    bl_set = set(blacklist)
    no_en_blacklist = ids_error - bl_set
    en_blacklist_sin_error = bl_set - ids_error
    return {
        "errores_no_en_blacklist": sorted(no_en_blacklist),
        "blacklist_sin_error_reciente": sorted(en_blacklist_sin_error),
        "cobertura_blacklist_pct": round(
            len(ids_error & bl_set) / len(ids_error) * 100 if ids_error else 0, 1
        ),
    }


def analizar_blacklist(entradas: list[dict], blacklist: list[str], eventos: list[dict]) -> dict:
    """Compara la lista negra con el histórico de errores y con la última sesión.

    POR QUÉ: el reporte mostraba "cobertura 5,8%" sin explicar que ``blacklist.json``
    se vacía con los botones *Clear Errors* / *Reiniciar* de la GUI. El número se leía
    como un fallo del bot cuando en realidad era una lista reiniciada. La telemetría
    estructurada conserva **todos** los errores históricos, así que permite separar dos
    preguntas distintas:

        - "¿qué errores de la última sesión ya están en la lista?" (cobertura útil), y
        - "¿qué IDs fallaron alguna vez y nunca se saltaron?" (histórico real).

    Args:
        entradas (list[dict]): Entradas de los ``registro_*.txt``.
        blacklist (list[str]): IDs presentes hoy en ``blacklist.json``.
        eventos (list[dict]): Eventos de ``logs/events.jsonl``.

    Returns:
        dict: ``blacklist_total``, ``errores_historicos_unicos``, ``nunca_en_blacklist``,
        ``reintentados`` (ID → cantidad de **días distintos** con error),
        ``ultima_sesion_fecha``, ``ultima_sesion_errores``,
        ``cobertura_ultima_sesion_pct`` y ``nota``.
    """
    # Días distintos por ID: un diario que falló una sola vez aparece en el registro
    # del día Y en la telemetría, así que sumar las dos fuentes lo contaría como
    # "reintentado" sin serlo. Lo que define un reintento real es volver a fallar
    # otro día.
    dias_por_id: dict[str, set[str]] = defaultdict(set)
    for entrada in entradas:
        if entrada["resultado"] == "ERROR":
            dias_por_id[entrada["id_normalizado"]].add(str(entrada.get("fecha", "")))
    for evento in eventos:
        if str(evento.get("event", "")) == "result_error" and evento.get("id_normalizado"):
            dias_por_id[str(evento["id_normalizado"])].add(str(evento.get("ts", ""))[:10])

    historico: set[str] = set(dias_por_id)
    reintentados: dict[str, int] = {}
    for identificador, dias in sorted(dias_por_id.items()):
        dias_con_fecha = {dia for dia in dias if dia}
        if len(dias_con_fecha) > 1:
            reintentados[identificador] = len(dias_con_fecha)

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
        "nunca_en_blacklist": sorted(historico - set(blacklist)),
        "reintentados": reintentados,
        "ultima_sesion_fecha": ultima_fecha,
        "ultima_sesion_errores": len(ids_ultima),
        "cobertura_ultima_sesion_pct": (
            round(len(en_lista) / len(ids_ultima) * 100, 1) if ids_ultima else 0
        ),
        "nota": (
            "blacklist.json se vacía con Clear Errors / Reiniciar: úsala como lista negra "
            "de la sesión. El histórico de errores vive en logs/events.jsonl."
        ),
    }


def detectar_timeouts(lineas_log: list[str]) -> list[dict]:
    """Extrae eventos de timeout del log.

    Detecta los 3 formatos históricos:
      viejo:      "Timeout: No se pudo encontrar <PATH> en 20 segundos."
      intermedio: "Timeout: btn_registrar_confirm.png no encontrado (20s)."
      actual:     "Timeout: Confirmar no encontrado (20s)."

    Normaliza el elemento: extrae el basename si hay path absoluto.
    Maneja timestamps malformados (solo fecha sin hora).
    """
    timeouts = []
    for linea in lineas_log:
        parsed = parsear_linea_log(linea)
        if not parsed:
            continue
        msg = parsed["mensaje"]
        if not msg.startswith("Timeout:"):
            continue
        m = _PATRON_TIMEOUT.search(msg)
        if not m:
            continue
        segundos_str = m.group(1) or m.group(2)
        segundos = int(segundos_str) if segundos_str else 0

        # Extraer elemento
        elemento = "?"
        m_elem = _PATRON_TIMEOUT_ELEMENTO_VIEJO.search(msg)
        if m_elem:
            elemento = normalizar_elemento(m_elem.group(1).strip())
        else:
            m_elem = _PATRON_TIMEOUT_ELEMENTO_NUEVO.search(msg)
            if m_elem:
                elemento = normalizar_elemento(m_elem.group(1).strip())

        timeouts.append({
            "timestamp": parsed["timestamp"],
            "elemento": elemento,
            "segundos": segundos,
        })
    return timeouts


def detectar_errores_ax(lineas_log: list[str]) -> list[dict]:
    """Extrae eventos de 'Error de Registro de AX' del log.

    Detecta los 2 formatos históricos (ambos con nivel [WARNING]):
      viejo:  "-> Apareció un Error de Registro de AX!"
      actual: "-> ERROR de Registro AX!"

    Maneja timestamps malformados (solo fecha sin hora).
    """
    errores = []
    for linea in lineas_log:
        parsed = parsear_linea_log(linea)
        if not parsed:
            continue
        if _PATRON_ERROR_AX.search(parsed["mensaje"]):
            errores.append({
                "timestamp": parsed["timestamp"],
                "nivel": parsed["nivel"],
                "mensaje": parsed["mensaje"],
            })
    return errores


def detectar_errores_failsafe(lineas_log: list[str]) -> list[dict]:
    """Extrae errores [ERROR] de crash de fail-safe de PyAutoGUI.

    Formato: "[ERROR] Error durante la búsqueda de imagen: PyAutoGUI fail-safe triggered..."
    Maneja timestamps malformados (solo fecha sin hora).
    """
    errores = []
    for linea in lineas_log:
        parsed = parsear_linea_log(linea)
        if not parsed:
            continue
        # Solo nivel [ERROR]
        if parsed["nivel"] != "ERROR":
            continue
        if _PATRON_ERROR_FAILSAFE.search(parsed["mensaje"]):
            errores.append({
                "timestamp": parsed["timestamp"],
                "mensaje": parsed["mensaje"][:120],
            })
    return errores


def detectar_exitos_log(lineas_log: list[str]) -> list[dict]:
    """Extrae eventos de éxito del log (no solo de registro_*.txt).

    Detecta los 3 formatos históricos (todos con nivel [INFO]):
      viejo:  "-> Registro en AX completado exitosamente! (checkbox)"
      viejo:  "-> Registro en AX completado exitosamente! (pop-up)"
      actual: "-> EXITO! (pop-up confirmado)"

    Maneja timestamps malformados (solo fecha sin hora).
    """
    exitos = []
    for linea in lineas_log:
        parsed = parsear_linea_log(linea)
        if not parsed:
            continue
        if _PATRON_EXITO.search(parsed["mensaje"]):
            # Extraer el tipo de confirmación si está presente
            tipo = "desconocido"
            m = re.search(r'\(([^)]+)\)', parsed["mensaje"])
            if m:
                tipo = m.group(1).strip()
            exitos.append({
                "timestamp": parsed["timestamp"],
                "tipo": tipo,
            })
    return exitos


def detectar_capturas_sin_match(capturas: list[str], entradas: list[dict]) -> list[str]:
    """Capturas de error que no corresponden a ningún ID en los registros."""
    ids_en_registros = {e["id_bruto"] for e in entradas}
    huerfanas = []
    for cap in capturas:
        # extraer ID del nombre: error_<id>_<timestamp>.png
        m = re.match(r'error_(.+?)_\d{4}-\d{2}-\d{2}', cap)
        if m:
            id_cap = m.group(1)
            if id_cap not in ids_en_registros:
                huerfanas.append(cap)
    return huerfanas


# ──────────────────────────────────────────────────────────────
# 3. REPORTE
# ──────────────────────────────────────────────────────────────

def generar_reporte(entradas, blacklist, lineas_log, capturas, eventos=None) -> dict:
    """Genera el reporte consolidado del análisis.

    Args:
        entradas: Entradas parseadas de los ``registro_*.txt``.
        blacklist: IDs presentes en ``blacklist.json``.
        lineas_log: Líneas de ``logs/bot_ax.log``.
        capturas: Nombres de las capturas de error.
        eventos: Eventos de ``logs/events.jsonl`` (telemetría estructurada).
            Es opcional: sin este argumento el reporte se comporta igual que antes
            (compatibilidad con llamadas existentes).

    Returns:
        dict: Reporte con métricas globales, sesiones por fecha y patrones.
    """
    total = len(entradas)
    exitos = sum(1 for e in entradas if e["resultado"] == "EXITOSO")
    errores = sum(1 for e in entradas if e["resultado"] == "ERROR")
    tasa_exito = round(exitos / total * 100, 1) if total else 0

    # Éxitos detectados desde el log
    exitos_log = detectar_exitos_log(lineas_log)

    # Telemetría estructurada: fuente a prueba de fallos (open/append/close por
    # evento). Se marca con ``log_desactualizado`` cuando el log de texto quedó
    # atrás, que es exactamente el incidente del 2026-10-08/09.
    eventos = eventos or []
    telemetria = resumir_lista_eventos(eventos)
    telemetria["log_desactualizado"] = telemetria_mas_nueva_que_log(lineas_log, eventos)

    # Sesiones por fecha
    sesiones = defaultdict(lambda: {"exitos": 0, "errores": 0})
    for e in entradas:
        if e["resultado"] == "EXITOSO":
            sesiones[e["fecha"]]["exitos"] += 1
        else:
            sesiones[e["fecha"]]["errores"] += 1

    return {
        "timestamp_analisis": datetime.now().isoformat(),
        "metricas_globales": {
            "total_registros": total,
            "exitos": exitos,
            "errores": errores,
            "tasa_exito_pct": tasa_exito,
            "exitos_detectados_log": len(exitos_log),
            "blacklist_total": len(blacklist),
            "capturas_total": len(capturas),
            "eventos_total": telemetria["total_eventos"],
            "eventos_exitos": telemetria["exitos"],
            "eventos_errores": telemetria["errores"],
            "log_desactualizado": telemetria["log_desactualizado"],
        },
        "sesiones_por_fecha": {
            f: {"exitos": v["exitos"], "errores": v["errores"]}
            for f, v in sorted(sesiones.items())
        },
        "patrones": {
            "ruido_ocr": detectar_ruido_ocr(entradas),
            "errores_agrupados": detectar_errores_agrupados(entradas),
            "fallback_sector_b": detectar_fallback_sector_b(lineas_log),
            "gaps_blacklist": detectar_gaps_blacklist(entradas, blacklist),
            "analisis_blacklist": analizar_blacklist(entradas, blacklist, eventos),
            "timeouts": detectar_timeouts(lineas_log),
            "errores_ax": detectar_errores_ax(lineas_log),
            "errores_failsafe": detectar_errores_failsafe(lineas_log),
            "exitos_log": exitos_log,
            "capturas_huerfanas": detectar_capturas_sin_match(capturas, entradas),
            "telemetria_estructurada": telemetria,
        },
    }


def imprimir_reporte(reporte: dict) -> None:
    """Imprime el reporte en consola con formato legible."""
    print("=" * 70)
    print("  OBSERVER ANALYZER — Bot AX Contable")
    print(f"  Análisis: {reporte['timestamp_analisis']}")
    print("=" * 70)

    mg = reporte["metricas_globales"]
    print(f"\n📊 MÉTRICAS GLOBALES")
    print(f"  Registros totales: {mg['total_registros']}")
    print(f"  Éxitos: {mg['exitos']}  |  Errores: {mg['errores']}")
    print(f"  Tasa de éxito: {mg['tasa_exito_pct']}%")
    print(f"  Éxitos detectados en log: {mg['exitos_detectados_log']}")
    print(f"  Blacklist: {mg['blacklist_total']} diarios")
    print(f"  Capturas: {mg['capturas_total']}")
    print(f"  Eventos estructurados: {mg['eventos_total']}")

    print(f"\n📅 SESIONES POR FECHA")
    for fecha, datos in reporte["sesiones_por_fecha"].items():
        total_dia = datos["exitos"] + datos["errores"]
        tasa = round(datos["exitos"] / total_dia * 100, 1) if total_dia else 0
        print(f"  {fecha}: {datos['exitos']} OK, {datos['errores']} ERR (tasa: {tasa}%)")

    p = reporte["patrones"]

    # Telemetría estructurada: fuente principal cuando el log de texto está atrás
    telem = p["telemetria_estructurada"]
    print(f"\n📡 TELEMETRÍA ESTRUCTURADA (logs/events.jsonl)")
    print(f"  Eventos: {telem['total_eventos']}  |  Éxitos: {telem['exitos']}  |  Errores: {telem['errores']}")
    print(f"  Timeouts: {telem['timeouts']}  |  Fallbacks Sector B: {telem['fallbacks_sector_b']}")
    print(f"  Última actividad registrada: {telem['ultima_fecha'] or '(sin datos)'}")
    if telem["ids_error"]:
        print(f"  IDs con error ({telem['ids_error_unicos']} únicos): {telem['ids_error'][-10:]}")
    if telem["sesiones"]:
        print(f"  Sesiones registradas: {telem['sesiones']}")
    if telem["log_desactualizado"]:
        print(f"  ⚠️  El log de texto (bot_ax.log) está DESACTUALIZADO respecto de la telemetría:")
        print(f"      los patrones que dependen de él son PARCIALES. Causa histórica conocida:")
        print(f"      handler con descriptor abierto sobre Google Drive (corregido en v-00.13.02;")
        print(f"      el arreglo se aplica al reiniciar el bot).")

    print(f"\n🔍 PATRÓN: RUIDO OCR")
    r = p["ruido_ocr"]
    print(f"  IDs con lectura inestable: {r['ids_con_lectura_inestable']}")
    if r["ejemplos_inestables"]:
        print(f"  Ejemplos:")
        for k, v in r["ejemplos_inestables"].items():
            print(f"    {k} → leído como: {v}")
    print(f"  Prefijos basura: {r['prefijos_basura_mas_frecuentes']}")
    print(f"  Sufijos basura: {r['sufijos_basura_mas_frecuentes']}")
    print(f"  IDs sin dígitos suficientes: {r['ids_sin_digitos_suficientes']}")
    if r["ejemplos_sin_digitos"]:
        print(f"    Ejemplos: {r['ejemplos_sin_digitos']}")

    print(f"\n🔍 PATRÓN: ERRORES AGRUPADOS")
    clusters = p["errores_agrupados"]
    if clusters:
        for c in clusters:
            print(f"  {c['fecha']} {c['hora_inicio']}→{c['hora_fin']}: "
                  f"{c['cantidad']} errores seguidos — IDs: {c['ids']}")
    else:
        print(f"  No se detectaron ráfagas de errores.")

    print(f"\n🔍 PATRÓN: SECTOR B (FALLBACK)")
    fb = p["fallback_sector_b"]
    print(f"  Clics de menú: {fb['total_clics_menu']}")
    print(f"  Fallbacks a pantalla completa: {fb['fallbacks_pantalla_completa']}")
    print(f"  Warnings 'fuera de sector B': {fb['warnings_fuera_sector_b']}")
    print(f"  Ratio de fallback: {fb['ratio_fallback_pct']}%")
    print(f"  Timeouts de menú: {fb['timeouts_menu']}")
    print(f"  Diagnóstico: {fb['diagnostico']}")

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

    print(f"\n🔍 PATRÓN: TIMEOUTS")
    tos = p["timeouts"]
    if tos:
        print(f"  {len(tos)} timeout(s) detectados:")
        # Agrupar por elemento para resumen
        por_elemento = Counter(t["elemento"] for t in tos)
        for elem, count in por_elemento.most_common():
            print(f"    {elem}: {count}x")
        print(f"  Detalle (primeros 10):")
        for t in tos[:10]:
            print(f"    {t['timestamp']} — {t['elemento']} ({t['segundos']}s)")
        if len(tos) > 10:
            print(f"    ... y {len(tos) - 10} más")
    else:
        print(f"  Sin timeouts detectados.")

    print(f"\n🔍 PATRÓN: ERRORES DE REGISTRO AX")
    errs_ax = p["errores_ax"]
    if errs_ax:
        print(f"  {len(errs_ax)} error(es) de registro AX detectados:")
        # Agrupar por fecha
        por_fecha = Counter(e["timestamp"][:10] for e in errs_ax)
        for fecha, count in sorted(por_fecha.items()):
            print(f"    {fecha}: {count}x")
        print(f"  Detalle (primeros 10):")
        for e in errs_ax[:10]:
            print(f"    {e['timestamp']} [{e['nivel']}] {e['mensaje']}")
        if len(errs_ax) > 10:
            print(f"    ... y {len(errs_ax) - 10} más")
    else:
        print(f"  Sin errores de registro AX detectados.")

    print(f"\n🔍 PATRÓN: CRASHES FAIL-SAFE [ERROR]")
    errs_fs = p["errores_failsafe"]
    if errs_fs:
        print(f"  {len(errs_fs)} crash(es) de fail-safe detectados:")
        for e in errs_fs:
            print(f"    {e['timestamp']} — {e['mensaje']}")
    else:
        print(f"  Sin crashes de fail-safe detectados.")

    print(f"\n🔍 PATRÓN: ÉXITOS DETECTADOS EN LOG")
    exits = p["exitos_log"]
    if exits:
        print(f"  {len(exits)} éxito(s) detectados en log:")
        # Agrupar por fecha
        por_fecha = Counter(e["timestamp"][:10] for e in exits)
        for fecha, count in sorted(por_fecha.items()):
            print(f"    {fecha}: {count}x")
        # Agrupar por tipo
        por_tipo = Counter(e["tipo"] for e in exits)
        print(f"  Por tipo de confirmación:")
        for tipo, count in por_tipo.most_common():
            print(f"    {tipo}: {count}x")
    else:
        print(f"  Sin éxitos detectados en log.")

    print(f"\n🔍 PATRÓN: CAPTURAS HUÉRFANAS")
    huerfanas = p["capturas_huerfanas"]
    if huerfanas:
        print(f"  {len(huerfanas)} captura(s) sin match en registros:")
        for h in huerfanas:
            print(f"    {h}")
    else:
        print(f"  Todas las capturas tienen correspondencia en registros.")

    print("\n" + "=" * 70)
    print("  Fin del análisis")
    print("=" * 70)


# ──────────────────────────────────────────────────────────────
# 4. ENTRY POINT
# ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Observer Analyzer — diagnóstico post-ejecución del Bot AX Contable"
    )
    parser.add_argument(
        "--log", default=None,
        help="Ruta específica del log (default: logs/bot_ax.log)"
    )
    parser.add_argument(
        "--registro", default=None,
        help="Ruta específica de registro (default: todos los registro_*.txt)"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output en formato JSON en lugar de texto"
    )
    parser.add_argument(
        "--eventos", default=None,
        help="Ruta específica de la telemetría (default: logs/events.jsonl)"
    )
    args = parser.parse_args()

    entradas = leer_registros(BASE_DIR, args.registro)
    blacklist = leer_blacklist(BASE_DIR)
    lineas_log = leer_log(BASE_DIR, args.log)
    capturas = listar_capturas(BASE_DIR)
    ruta_telem = Path(args.eventos) if args.eventos else ruta_eventos(BASE_DIR)
    eventos = leer_eventos(ruta_telem)

    if not entradas and not lineas_log and not eventos:
        print("No se encontró evidencia para analizar.")
        return

    reporte = generar_reporte(entradas, blacklist, lineas_log, capturas, eventos)

    if args.json:
        print(json.dumps(reporte, ensure_ascii=False, indent=2))
    else:
        imprimir_reporte(reporte)


if __name__ == "__main__":
    main()
