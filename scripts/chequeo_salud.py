#!/usr/bin/env python3
"""Chequeo de salud del Bot AX Contable — "¿está trabajando bien?" en un comando.

POR QUÉ EXISTE (incidente 2026-10-09):
    El bot registró 12 errores en una jornada y el log de texto (``bot_ax.log``)
    llevaba un día congelado. Nadie lo supo hasta revisar archivos a mano al día
    siguiente. Ese mismo día, a las 15:24, el bot murió por el fail-safe de PyAutoGUI
    (el mouse llegó a una esquina de la pantalla) y el chequeo informaba "OK"
    simplemente porque no había sesión abierta. Antes de esto, responder "¿está
    trabajando bien el bot?" exigía abrir el log, contar líneas y compararlos con los
    registros.

QUÉ REVISA (solo lectura, nunca toca al bot ni la pantalla):
    1. SESION_TERMINADA_POR_ERROR — la última sesión cerró con crash (fail-safe) o
       timeout extremo: el operador debe enterarse sin abrir archivos.
    2. TELEMETRIA_CONGELADA — el bot está activo pero ``logs/bot_ax.log`` se quedó
       atrás respecto de ``logs/events.jsonl`` (síntoma exacto del incidente).
    3. SIN_ACTIVIDAD — hay una sesión abierta y no llegan eventos nuevos más allá del
       umbral que corresponde al punto del ciclo (ver ``umbral_sin_actividad``).
    4. TASA_ERROR_ALTA — los errores de hoy superan ``UMBRAL_TASA_ERROR_PCT``.
    5. CONFIG_INVALIDA — ``config_sectores.json`` o ``blacklist.json`` ilegibles.
    6. SIN_EVIDENCIA — no hay ni telemetría ni log (nada que analizar).

DECISIÓN DE DISEÑO: este script valida la configuración por su cuenta (no importa
``src.core.config``). Un chequeo de salud que depende del código del "paciente" puede
fallar justo cuando más se lo necesita; aquí se prioriza ser autónomo. Sí reutiliza el
LECTOR de telemetría de ``scripts/observer_analyze.py`` (una sola definición del
formato ``events.jsonl``).

Uso:
    python scripts/chequeo_salud.py              # informe legible
    python scripts/chequeo_salud.py --json       # salida JSON
    python scripts/chequeo_salud.py --estricto   # exit 1 si hay alertas (para CI/cron)
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

# La raíz (para src/) y scripts/ (para observer_analyze) deben ser importables
_RAIZ: Path = Path(__file__).resolve().parent.parent
_SCRIPTS: Path = Path(__file__).resolve().parent
for _ruta in (str(_RAIZ), str(_SCRIPTS)):
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)

from observer_analyze import (  # noqa: E402
    leer_eventos,
    resumir_lista_eventos,
    ultimo_timestamp_eventos,
)

# ──────────────────────────────────────────────────────────────
# Umbrales (ajustables en un solo lugar)
# ──────────────────────────────────────────────────────────────

# Minutos sin eventos con una sesión abierta para considerar que el bot se colgó
UMBRAL_SIN_EVENTOS_MIN: int = 15
# Minutos que el log de texto puede ir por detrás de la telemetría antes de alertar
UMBRAL_LOG_ATRASADO_MIN: int = 10
# Porcentaje de errores del día a partir del cual se alerta
UMBRAL_TASA_ERROR_PCT: float = 25.0
# Eventos de la telemetría que marcan el inicio y el fin de una sesión
EVENTO_INICIO: str = "bot_start"
EVENTO_FIN: str = "bot_stop"
# Motivos de cierre de sesión que NO son normales (user_esc y no_more_diarios sí lo son)
RAZONES_ANOMALAS: set[str] = {"error", "timeout_extremo"}
# Horas hacia atrás en las que una caída todavía se considera reciente
UMBRAL_CAIDA_HORAS: int = 24
# Evento que registra el aborto por fail-safe de PyAutoGUI
EVENTO_CAIDA: str = "failsafe_triggered"
# El bot espera el resultado de AX sin emitir eventos de telemetría (solo escribe en
# el log de texto) y esa espera puede durar hasta 60 min: aplicar el umbral normal de
# 15 min produce falsos SIN_ACTIVIDAD en los registros lentos.
UMBRAL_ESPERA_RESULTADO_MIN: int = 65
# Último evento que indica que el bot quedó esperando el resultado de AX
EVENTOS_EN_ESPERA: set[str] = {"confirm_click"}


# ──────────────────────────────────────────────────────────────
# Utilidades de lectura
# ──────────────────────────────────────────────────────────────

def leer_lineas_log(ruta: Path) -> list[str]:
    """Lee el log de texto del bot.

    Args:
        ruta (Path): Ruta de ``logs/bot_ax.log``.

    Returns:
        list[str]: Líneas del log (vacío si el archivo no existe).
    """
    if not Path(ruta).exists():
        return []
    return Path(ruta).read_text(encoding="utf-8", errors="replace").splitlines()


def ultimo_timestamp_log(lineas_log: list[str]) -> Optional[datetime]:
    """Extrae la marca de tiempo más reciente **del contenido** del log de texto.

    Se lee el contenido y no la fecha de modificación del archivo a propósito: la
    fecha de modificación cambia ante cualquier escritura (por ejemplo una prueba
    manual) aunque el bot haya dejado de escribir sus propias trazas. Comparar el
    contenido es lo que detecta de verdad el log congelado.

    Args:
        lineas_log (list[str]): Líneas del log.

    Returns:
        Optional[datetime]: Marca más reciente, o ``None`` si no hay ninguna.
    """
    marca: Optional[datetime] = None
    for linea in lineas_log:
        fragmento = linea.strip()
        if not fragmento.startswith("[") or "]" not in fragmento:
            continue
        candidato = fragmento[1:fragmento.index("]")]
        try:
            momento = datetime.strptime(candidato, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
        if marca is None or momento > marca:
            marca = momento
    return marca


def validar_json_sectores(ruta: Path) -> tuple[bool, str]:
    """Valida de forma autónoma la estructura de ``config_sectores.json``.

    Args:
        ruta (Path): Ruta del archivo de configuración.

    Returns:
        tuple[bool, str]: (es_válida, detalle del problema o "ok").
    """
    if not Path(ruta).exists():
        return False, f"no existe {ruta.name}"
    try:
        datos: Any = json.loads(Path(ruta).read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return False, f"{ruta.name} no es JSON válido: {error}"
    if not isinstance(datos, dict):
        return False, f"{ruta.name} no contiene un objeto JSON"
    for clave in ("sector_a", "sector_b"):
        valor = datos.get(clave)
        if not isinstance(valor, (list, tuple)) or len(valor) != 4:
            return False, f"{clave} debe ser una lista de 4 números [x, y, w, h]"
        if not all(isinstance(numero, (int, float)) for numero in valor):
            return False, f"{clave} contiene valores no numéricos"
    return True, "ok"


def validar_blacklist(ruta: Path) -> tuple[bool, str]:
    """Valida que ``blacklist.json`` sea una lista JSON legible.

    Args:
        ruta (Path): Ruta del archivo de lista negra.

    Returns:
        tuple[bool, str]: (es_válida, detalle del problema o "ok").
    """
    if not Path(ruta).exists():
        return True, "no existe (se creará en el primer error)"
    try:
        datos: Any = json.loads(Path(ruta).read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return False, f"blacklist.json no es JSON válido: {error}"
    if not isinstance(datos, list):
        return False, "blacklist.json debe contener una lista de IDs"
    return True, "ok"


def _parsear_ts(ts: Any) -> Optional[datetime]:
    """Convierte un timestamp ISO-8601 de la telemetría en ``datetime``.

    Args:
        ts (Any): Marca de tiempo del evento.

    Returns:
        Optional[datetime]: La marca convertida, o ``None`` si es inválida.
    """
    try:
        return datetime.fromisoformat(str(ts))
    except (ValueError, TypeError):
        return None


def _sesion_activa(eventos: list[dict]) -> bool:
    """Indica si la última marca de sesión es un inicio sin cierre.

    Args:
        eventos (list[dict]): Eventos de la telemetría.

    Returns:
        bool: ``True`` si hay un ``bot_start`` posterior al último ``bot_stop``.
    """
    ultimo: str = ""
    for evento in eventos:
        tipo = str(evento.get("event", ""))
        if tipo in (EVENTO_INICIO, EVENTO_FIN):
            ultimo = tipo
    return ultimo == EVENTO_INICIO


def analizar_ultima_sesion(eventos: list[dict]) -> dict:
    """Analiza cómo terminó la última sesión del bot.

    POR QUÉ: el 2026-10-09 el bot murió a las 15:24 por el fail-safe de PyAutoGUI
    (el mouse llegó a una esquina de la pantalla) y el operador no se enteró: la
    sesión quedó cerrada con ``reason="error"`` y, como no había sesión abierta, el
    chequeo informaba "OK". Una caída no puede depender de que alguien abra el log.

    Args:
        eventos (list[dict]): Eventos de la telemetría (en orden de aparición).

    Returns:
        dict: ``cerrada`` (bool), ``razon`` (motivo del ``bot_stop``), ``marca_cierre``
        (datetime o None), ``caida`` (marca del último fail-safe de la sesión) y
        ``ultimo_diario`` (último ID asociado a un evento de la sesión).
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


def umbral_sin_actividad(eventos: list[dict]) -> int:
    """Minutos sin eventos antes de alertar, según el punto del ciclo del bot.

    El bot espera el resultado de AX **sin emitir eventos de telemetría** (solo escribe
    en ``bot_ax.log``), y esa espera puede ser de hasta 60 minutos. Aplicarle el umbral
    normal de 15 minutos produce falsos ``SIN_ACTIVIDAD`` en cualquier registro lento.

    Args:
        eventos (list[dict]): Eventos de la telemetría.

    Returns:
        int: ``UMBRAL_ESPERA_RESULTADO_MIN`` si el último evento dejó al bot esperando
        el resultado de AX; ``UMBRAL_SIN_EVENTOS_MIN`` en cualquier otro caso.
    """
    if not eventos:
        return UMBRAL_SIN_EVENTOS_MIN
    if str(eventos[-1].get("event", "")) in EVENTOS_EN_ESPERA:
        return UMBRAL_ESPERA_RESULTADO_MIN
    return UMBRAL_SIN_EVENTOS_MIN


# ──────────────────────────────────────────────────────────────
# Chequeo principal
# ──────────────────────────────────────────────────────────────

def chequeo(raiz: Path, ahora: Optional[datetime] = None) -> dict:
    """Evalúa la salud del bot a partir de su evidencia observable.

    Args:
        raiz (Path): Raíz del proyecto (donde viven ``logs/`` y las configuraciones).
        ahora (Optional[datetime]): Momento de referencia (útil para pruebas).

    Returns:
        dict: Estado con ``ok``, ``alertas``, ``sesion_activa``, ``log_al_dia``,
        ``eventos_al_dia``, ``ultimo_evento_min``, ``tasa_exito_hoy``,
        ``caida_reciente``, ``ultima_sesion`` y métricas informativas del día.
    """
    raiz = Path(raiz)
    momento: datetime = ahora or datetime.now()

    eventos: list[dict] = leer_eventos(raiz / "logs" / "events.jsonl")
    lineas_log: list[str] = leer_lineas_log(raiz / "logs" / "bot_ax.log")

    marca_eventos: Optional[datetime] = ultimo_timestamp_eventos(eventos)
    marca_log: Optional[datetime] = ultimo_timestamp_log(lineas_log)

    ultimo_evento_min: Optional[float] = None
    if marca_eventos is not None:
        ultimo_evento_min = round((momento - marca_eventos).total_seconds() / 60, 1)

    umbral_actividad: int = umbral_sin_actividad(eventos)
    activa: bool = _sesion_activa(eventos)
    actividad_reciente: bool = activa or (
        ultimo_evento_min is not None and ultimo_evento_min <= umbral_actividad
    )

    minutos_atraso_log: Optional[float] = None
    if marca_eventos is not None and marca_log is not None:
        minutos_atraso_log = round((marca_eventos - marca_log).total_seconds() / 60, 1)
    log_al_dia: bool = (
        minutos_atraso_log is not None and minutos_atraso_log <= UMBRAL_LOG_ATRASADO_MIN
    )

    resumen = resumir_lista_eventos(eventos)
    fecha_hoy: str = momento.strftime("%Y-%m-%d")
    hoy: dict = resumen["sesiones"].get(fecha_hoy, {})
    exitos_hoy: int = int(hoy.get("exitos", 0))
    errores_hoy: int = int(hoy.get("errores", 0))
    registros_hoy: int = exitos_hoy + errores_hoy
    tasa_exito_hoy: Optional[float] = (
        round(exitos_hoy / registros_hoy * 100, 1) if registros_hoy else None
    )

    # ¿Cómo terminó la última sesión? (una caída debe reportarse, no quedar invisible)
    ultima_sesion = analizar_ultima_sesion(eventos)
    marca_caida: Optional[datetime] = ultima_sesion["marca_cierre"] or ultima_sesion["caida"]
    caida_reciente: bool = False
    if (
        ultima_sesion["cerrada"]
        and ultima_sesion["razon"] in RAZONES_ANOMALAS
        and marca_caida is not None
    ):
        caida_reciente = (momento - marca_caida) <= timedelta(hours=UMBRAL_CAIDA_HORAS)

    valida_config, detalle_config = validar_json_sectores(raiz / "config_sectores.json")
    valida_blacklist, detalle_blacklist = validar_blacklist(raiz / "blacklist.json")

    alertas: list[dict] = []

    if not eventos and not lineas_log:
        alertas.append({
            "codigo": "SIN_EVIDENCIA",
            "detalle": "No hay telemetría (logs/events.jsonl) ni log (logs/bot_ax.log).",
        })

    if caida_reciente and marca_caida is not None:
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

    if eventos and actividad_reciente and not log_al_dia:
        alertas.append({
            "codigo": "TELEMETRIA_CONGELADA",
            "detalle": (
                f"El bot está activo pero bot_ax.log va {minutos_atraso_log} min por "
                f"detrás de la telemetría (último log: "
                f"{marca_log.strftime('%Y-%m-%d %H:%M') if marca_log else 'sin líneas'})."
            ),
        })

    if activa and ultimo_evento_min is not None and ultimo_evento_min > umbral_actividad:
        alertas.append({
            "codigo": "SIN_ACTIVIDAD",
            "detalle": (
                f"Sesión abierta sin eventos hace {ultimo_evento_min} min "
                f"(umbral: {umbral_actividad})."
            ),
        })

    if tasa_exito_hoy is not None and (100 - tasa_exito_hoy) > UMBRAL_TASA_ERROR_PCT:
        alertas.append({
            "codigo": "TASA_ERROR_ALTA",
            "detalle": (
                f"Errores de hoy: {round(100 - tasa_exito_hoy, 1)}% "
                f"({errores_hoy} de {registros_hoy}; umbral: {UMBRAL_TASA_ERROR_PCT}%)."
            ),
        })

    if not valida_config or not valida_blacklist:
        detalles = [d for d in (detalle_config, detalle_blacklist) if d != "ok"]
        alertas.append({
            "codigo": "CONFIG_INVALIDA",
            "detalle": " | ".join(detalles),
        })

    return {
        "momento_chequeo": momento.isoformat(),
        "ok": not alertas,
        "alertas": alertas,
        "sesion_activa": activa,
        "actividad_reciente": actividad_reciente,
        "log_al_dia": log_al_dia,
        "eventos_al_dia": (
            ultimo_evento_min is not None and ultimo_evento_min <= umbral_actividad
        ),
        "umbral_actividad_min": umbral_actividad,
        "ultimo_evento_min": ultimo_evento_min,
        "minutos_atraso_log": minutos_atraso_log,
        "caida_reciente": caida_reciente,
        "ultima_sesion": {
            "cerrada": ultima_sesion["cerrada"],
            "razon": ultima_sesion["razon"],
            "marca_cierre": (
                ultima_sesion["marca_cierre"].isoformat()
                if ultima_sesion["marca_cierre"] else None
            ),
            "failsafe": (
                ultima_sesion["caida"].isoformat() if ultima_sesion["caida"] else None
            ),
            "ultimo_diario": ultima_sesion["ultimo_diario"],
        },
        "exitos_hoy": exitos_hoy,
        "errores_hoy": errores_hoy,
        "registros_hoy": registros_hoy,
        "tasa_exito_hoy": tasa_exito_hoy,
        "eventos_total": resumen["total_eventos"],
        "config_valida": valida_config,
        "blacklist_valida": valida_blacklist,
    }


def imprimir_resultado(resultado: dict) -> None:
    """Imprime el resultado del chequeo de forma legible.

    Args:
        resultado (dict): Resultado devuelto por :func:`chequeo`.
    """
    print("=" * 70)
    print("  CHEQUEO DE SALUD — Bot AX Contable")
    print(f"  Momento: {resultado['momento_chequeo']}")
    print("=" * 70)

    estado = "OK" if resultado["ok"] else "CON ALERTAS"
    print(f"\n  Estado general: {estado}")
    print(f"  Sesión activa: {resultado['sesion_activa']}"
          f"  |  Actividad reciente: {resultado['actividad_reciente']}"
          f"  (umbral {resultado['umbral_actividad_min']} min)")
    print(f"  Log de texto al día: {resultado['log_al_dia']}"
          f"  |  Telemetría al día: {resultado['eventos_al_dia']}")
    ultimo = resultado["ultimo_evento_min"]
    print(f"  Último evento: {ultimo if ultimo is not None else 'sin datos'} min atrás")
    tasa = resultado["tasa_exito_hoy"]
    print(f"  Hoy: {resultado['exitos_hoy']} OK / {resultado['errores_hoy']} ERR"
          f"  |  Tasa de éxito: {tasa if tasa is not None else 'sin registros'}%")

    sesion_previa = resultado["ultima_sesion"]
    if sesion_previa["cerrada"]:
        print(f"  Última sesión cerrada: {sesion_previa['razon']}"
              f" ({sesion_previa['marca_cierre'] or 'sin marca'})")

    if resultado["alertas"]:
        print(f"\n  ALERTAS ({len(resultado['alertas'])})")
        for alerta in resultado["alertas"]:
            print(f"    [{alerta['codigo']}] {alerta['detalle']}")
    else:
        print("\n  Sin alertas.")

    print("\n" + "=" * 70)


def main() -> int:
    """Punto de entrada del chequeo.

    Returns:
        int: ``0`` si todo está bien o si se pidió solo informar; ``1`` con
        ``--estricto`` cuando hay alertas (útil para cron y CI).
    """
    parser = argparse.ArgumentParser(
        description="Chequeo de salud del Bot AX Contable (solo lectura)"
    )
    parser.add_argument("--raiz", default=str(_RAIZ), help="Raíz del proyecto")
    parser.add_argument("--json", action="store_true", help="Salida en formato JSON")
    parser.add_argument(
        "--estricto", action="store_true",
        help="Devuelve código de salida 1 si hay alertas",
    )
    args = parser.parse_args()

    resultado = chequeo(Path(args.raiz))

    if args.json:
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
    else:
        imprimir_resultado(resultado)

    if args.estricto and not resultado["ok"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
