#!/usr/bin/env python3
"""
Observer Watchdog — vigilancia en vivo del Bot AX Contable.

Lee events.jsonl y reporta SOLO cuando hay algo importante:
  - Bot arrancó
  - Error/crash/timeout detectado
  - Bot terminó (resumen)

Si el bot no está corriendo o todo va bien → silencio total (stdout vacío).

Mantiene estado en logs/.watchdog_state.json para no re-reportar eventos.
"""

import os
import json
from pathlib import Path
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).resolve().parent.parent
EVENTS_FILE = BASE_DIR / "logs" / "events.jsonl"
STATE_FILE = BASE_DIR / "logs" / ".watchdog_state.json"

# Eventos que generan alerta inmediata
ALERT_EVENTS = {
    "result_error",
    "result_timeout",
    "failsafe_triggered",
    "timeout_menu",
    "timeout_confirm",
    "formulario_abierto_detectado",
}

# Tiempo máximo sin eventos para considerar que el bot no está corriendo
STALE_THRESHOLD_MIN = 5


def cargar_estado() -> dict:
    """Carga el estado del watchdog (última posición leída en events.jsonl)."""
    if not STATE_FILE.exists():
        return {"last_pos": 0, "bot_activo": False, "eventos_reportados": []}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"last_pos": 0, "bot_activo": False, "eventos_reportados": []}


def guardar_estado(estado: dict) -> None:
    """Guarda el estado del watchdog."""
    try:
        STATE_FILE.write_text(json.dumps(estado, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def leer_nuevos_eventos(last_pos: int) -> list[dict]:
    """Lee eventos nuevos desde la última posición."""
    if not EVENTS_FILE.exists():
        return []
    try:
        size = EVENTS_FILE.stat().st_size
        if size < last_pos:
            # El archivo fue truncado/rotado, empezar desde 0
            last_pos = 0
        with open(EVENTS_FILE, "r", encoding="utf-8") as f:
            f.seek(last_pos)
            eventos = []
            for linea in f:
                linea = linea.strip()
                if not linea:
                    continue
                try:
                    eventos.append(json.loads(linea))
                except json.JSONDecodeError:
                    continue
            nueva_pos = f.tell()
        return eventos, nueva_pos
    except Exception:
        return [], last_pos


def parsear_ts(ts_str: str) -> datetime:
    """Parsea timestamp ISO-8601."""
    try:
        return datetime.fromisoformat(ts_str)
    except Exception:
        return datetime.now()


def main():
    estado = cargar_estado()
    eventos, nueva_pos = leer_nuevos_eventos(estado["last_pos"])
    estado["last_pos"] = nueva_pos

    if not eventos:
        # No hay eventos nuevos
        # Verificar si el bot estaba activo pero ya no hay actividad
        if estado.get("bot_activo", False):
            # Verificar si el último evento fue hace mucho
            # (el bot_stop debería haber llegado, pero por si acaso)
            pass
        guardar_estado(estado)
        return  # Silencio

    alertas = []
    resumen = None
    bot_start_detectado = False
    bot_stop_detectado = False

    for ev in eventos:
        event_type = ev.get("event", "")
        ts = ev.get("ts", "")

        if event_type == "bot_start":
            bot_start_detectado = True
            estado["bot_activo"] = True
            estado["eventos_reportados"] = []
            bl_count = ev.get("blacklist_count", 0)
            alertas.append(f"🟢 BOT INICIADO — Vigilando. Blacklist: {bl_count} diarios.")

        elif event_type == "bot_stop":
            bot_stop_detectado = True
            estado["bot_activo"] = False
            reason = ev.get("reason", "desconocido")
            iconos = {
                "user_esc": "🛑",
                "formularios_abiertos": "⚠️",
                "no_more_diarios": "✅",
                "timeout_extremo": "🚨",
                "error": "🚨",
            }
            icono = iconos.get(reason, "🛑")
            alertas.append(f"{icono} BOT DETENIDO — Razón: {reason}")

        elif event_type in ALERT_EVENTS:
            # No re-reportar el mismo evento
            ev_id = f"{ts}_{event_type}_{ev.get('id_normalizado', '')}"
            if ev_id not in estado.get("eventos_reportados", []):
                estado.setdefault("eventos_reportados", []).append(ev_id)

                if event_type == "result_error":
                    eid = ev.get("id_normalizado", "?")
                    alertas.append(f"🔴 ERROR AX — Diario {eid} falló en registro.")

                elif event_type == "result_timeout":
                    eid = ev.get("id_normalizado", "?")
                    segs = ev.get("segundos_esperados", 0)
                    alertas.append(f"🚨 TIMEOUT extremo — Diario {eid} tras {segs}s. Bot se detiene.")

                elif event_type == "failsafe_triggered":
                    alertas.append(f"🚨 CRASH FAIL-SAFE — PyAutoGUI se crasheó. Mouse en esquina.")

                elif event_type == "timeout_menu":
                    segs = ev.get("segundos", 0)
                    alertas.append(f"⚠️ TIMEOUT menú — No se encontró botón Registrar tras {segs}s.")

                elif event_type == "timeout_confirm":
                    segs = ev.get("segundos", 0)
                    alertas.append(f"⚠️ TIMEOUT confirmar — No se encontró Confirmar tras {segs}s.")

                elif event_type == "formulario_abierto_detectado":
                    alertas.append(f"⚠️ SEGURIDAD — Formularios abiertos detectados. Bot se detiene.")

    # Si el bot terminó, generar resumen de la sesión
    if bot_stop_detectado:
        # Leer todos los eventos de la sesión para el resumen
        todos_eventos = []
        try:
            with open(EVENTS_FILE, "r", encoding="utf-8") as f:
                for linea in f:
                    try:
                        todos_eventos.append(json.loads(linea.strip()))
                    except Exception:
                        continue
        except Exception:
            pass

        # Contar resultados de la sesión
        exitos = sum(1 for e in todos_eventos if e.get("event") == "result_exito")
        errores = sum(1 for e in todos_eventos if e.get("event") == "result_error")
        timeouts = sum(1 for e in todos_eventos if e.get("event") in ("timeout_menu", "timeout_confirm"))
        crashes = sum(1 for e in todos_eventos if e.get("event") == "failsafe_triggered")
        fallbacks = sum(1 for e in todos_eventos if e.get("event") == "sector_b_fallback")
        total = exitos + errores

        tasa = round(exitos / total * 100, 1) if total else 0

        resumen = (
            f"\n📊 RESUMEN DE SESIÓN\n"
            f"  Total procesados: {total}\n"
            f"  Éxitos: {exitos}  |  Errores: {errores}  |  Tasa: {tasa}%\n"
            f"  Timeouts: {timeouts}  |  Crashes: {crashes}\n"
            f"  Fallbacks sector B: {fallbacks}\n"
        )
        if errores > 0 or crashes > 0:
            resumen += f"\n⚠️ Hay {errores + crashes} problema(s) que requieren atención.\n"
            resumen += f"Corre: python scripts/observer_analyze.py para diagnóstico completo.\n"

    guardar_estado(estado)

    # Output: solo si hay algo que reportar
    if alertas or resumen:
        for a in alertas:
            print(a)
        if resumen:
            print(resumen)
    # Si no hay nada → stdout vacío → cron se queda callado
    # (silencio: no molesta al usuario)


if __name__ == "__main__":
    main()
