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

def leer_registros(directorio: Path) -> list[dict]:
    """Lee todos los registro_*.txt y devuelve lista de entradas parseadas."""
    entradas = []
    patron = re.compile(
        r'\[(\d{2}:\d{2}:\d{2})\]\s+Diario:\s+(.+?)\s+-\s+Resultado:\s+(\w+)'
    )
    for archivo in sorted(directorio.glob("registro_*.txt")):
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

def generar_reporte(entradas, blacklist, lineas_log, capturas) -> dict:
    total = len(entradas)
    exitos = sum(1 for e in entradas if e["resultado"] == "EXITOSO")
    errores = sum(1 for e in entradas if e["resultado"] == "ERROR")
    tasa_exito = round(exitos / total * 100, 1) if total else 0

    # Éxitos detectados desde el log
    exitos_log = detectar_exitos_log(lineas_log)

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
            "timeouts": detectar_timeouts(lineas_log),
            "errores_ax": detectar_errores_ax(lineas_log),
            "errores_failsafe": detectar_errores_failsafe(lineas_log),
            "exitos_log": exitos_log,
            "capturas_huerfanas": detectar_capturas_sin_match(capturas, entradas),
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

    print(f"\n📅 SESIONES POR FECHA")
    for fecha, datos in reporte["sesiones_por_fecha"].items():
        total_dia = datos["exitos"] + datos["errores"]
        tasa = round(datos["exitos"] / total_dia * 100, 1) if total_dia else 0
        print(f"  {fecha}: {datos['exitos']} OK, {datos['errores']} ERR (tasa: {tasa}%)")

    p = reporte["patrones"]

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
    print(f"  Cobertura: {bl['cobertura_blacklist_pct']}%")
    if bl["errores_no_en_blacklist"]:
        print(f"  ERRORES no en blacklist: {bl['errores_no_en_blacklist']}")
    if bl["blacklist_sin_error_reciente"]:
        print(f"  Blacklist sin error reciente: {bl['blacklist_sin_error_reciente']}")

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
    args = parser.parse_args()

    entradas = leer_registros(BASE_DIR)
    blacklist = leer_blacklist(BASE_DIR)
    lineas_log = leer_log(BASE_DIR, args.log)
    capturas = listar_capturas(BASE_DIR)

    if not entradas and not lineas_log:
        print("No se encontró evidencia para analizar.")
        return

    reporte = generar_reporte(entradas, blacklist, lineas_log, capturas)

    if args.json:
        print(json.dumps(reporte, ensure_ascii=False, indent=2))
    else:
        imprimir_reporte(reporte)


if __name__ == "__main__":
    main()
