"""Pruebas del chequeo de salud del bot (``scripts/chequeo_salud.py``).

Motivo: el 2026-10-09 el bot registró 12 errores y el log de texto llevaba un día
congelado, y no existía ninguna forma de saberlo sin abrir archivos a mano. Estas
pruebas fijan el contrato del chequeo: detectar telemetría congelada, falta de
actividad, tasa de error alta y configuración inválida.

Ejecutar con: ``python -m pytest tests/test_chequeo_salud.py -v``
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import chequeo_salud  # noqa: E402

AHORA = datetime(2026, 10, 9, 15, 0, 0)


def _preparar_raiz(tmp_path: Path) -> Path:
    """Crea la estructura mínima del proyecto (logs/ + config válida).

    Args:
        tmp_path (Path): Directorio temporal de la prueba.

    Returns:
        Path: Raíz simulada del proyecto.
    """
    (tmp_path / "logs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "config_sectores.json").write_text(
        json.dumps({
            "sector_a": [39, 236, 300, 451],
            "sector_b": [1081, 82, 283, 47],
            "sector_scroll": [342, 658, 37, 28],
        }),
        encoding="utf-8",
    )
    (tmp_path / "blacklist.json").write_text("[]", encoding="utf-8")
    return tmp_path


def _escribir_eventos(raiz: Path, eventos: list[dict]) -> None:
    """Escribe la telemetría simulada en logs/events.jsonl."""
    lineas = "\n".join(json.dumps(evento, ensure_ascii=False) for evento in eventos)
    (raiz / "logs" / "events.jsonl").write_text(lineas + "\n", encoding="utf-8")


def _escribir_log(raiz: Path, lineas: list[str]) -> None:
    """Escribe el log de texto simulado en logs/bot_ax.log."""
    (raiz / "logs" / "bot_ax.log").write_text("\n".join(lineas) + "\n", encoding="utf-8")


def _codigos(resultado: dict) -> set[str]:
    """Devuelve el conjunto de códigos de alerta del resultado."""
    return {alerta["codigo"] for alerta in resultado["alertas"]}


class TestAlertasDeSalud:
    """Pruebas de las reglas de alerta del chequeo."""

    def test_sesion_sana_no_genera_alertas(self, tmp_path: Path):
        """Sesión activa, log al día y tasa de error baja ⇒ ok=True."""
        raiz = _preparar_raiz(tmp_path)
        _escribir_log(raiz, [f"[2026-10-09 14:59:30] [INFO] Click: Menu @ (1284,104)"])
        _escribir_eventos(raiz, [
            {"ts": "2026-10-09T14:59:40", "event": "bot_start"},
            {"ts": "2026-10-09T14:59:50", "event": "confirm_click"},
            {"ts": "2026-10-09T14:59:55", "event": "result_exito", "id_normalizado": "00337505"},
        ])

        resultado = chequeo_salud.chequeo(raiz, ahora=AHORA)

        assert resultado["ok"] is True
        assert resultado["alertas"] == []
        assert resultado["sesion_activa"] is True

    def test_detecta_telemetria_congelada(self, tmp_path: Path):
        """El log de texto quedó atrás pero el bot sigue trabajando (incidente real)."""
        raiz = _preparar_raiz(tmp_path)
        _escribir_log(raiz, ["[2026-10-09 11:53:10] [INFO] linea vieja del log"])
        _escribir_eventos(raiz, [
            {"ts": "2026-10-09T14:00:00", "event": "bot_start"},
            {"ts": "2026-10-09T14:59:40", "event": "result_exito", "id_normalizado": "00337505"},
        ])

        resultado = chequeo_salud.chequeo(raiz, ahora=AHORA)

        assert "TELEMETRIA_CONGELADA" in _codigos(resultado)
        assert resultado["ok"] is False
        assert resultado["log_al_dia"] is False

    def test_detecta_sin_actividad_con_sesion_abierta(self, tmp_path: Path):
        """Sesión iniciada sin cierre y sin eventos en 15+ minutos ⇒ SIN_ACTIVIDAD."""
        raiz = _preparar_raiz(tmp_path)
        _escribir_log(raiz, ["[2026-10-09 14:10:00] [INFO] Click: Menu @ (1284,104)"])
        _escribir_eventos(raiz, [
            {"ts": "2026-10-09T14:10:00", "event": "bot_start"},
            {"ts": "2026-10-09T14:11:00", "event": "confirm_click"},
        ])

        resultado = chequeo_salud.chequeo(raiz, ahora=AHORA)

        assert "SIN_ACTIVIDAD" in _codigos(resultado)
        assert resultado["ultimo_evento_min"] == 49.0

    def test_detecta_tasa_de_error_alta(self, tmp_path: Path):
        """Más de 25% de errores en el día ⇒ TASA_ERROR_ALTA."""
        raiz = _preparar_raiz(tmp_path)
        _escribir_log(raiz, ["[2026-10-09 14:59:00] [INFO] Click: Menu @ (1284,104)"])
        eventos: list[dict] = [{"ts": "2026-10-09T14:00:00", "event": "bot_start"}]
        for indice in range(6):
            eventos.append({"ts": f"2026-10-09T14:3{indice}:00", "event": "result_exito", "id_normalizado": f"0033750{indice}"})
        for indice in range(4):
            eventos.append({"ts": f"2026-10-09T14:5{indice}:00", "event": "result_error", "id_normalizado": f"0033760{indice}"})
        eventos.append({"ts": "2026-10-09T14:59:55", "event": "confirm_click"})
        _escribir_eventos(raiz, eventos)

        resultado = chequeo_salud.chequeo(raiz, ahora=AHORA)

        assert "TASA_ERROR_ALTA" in _codigos(resultado)
        assert resultado["tasa_exito_hoy"] == 60.0

    def test_config_invalida_por_json_roto(self, tmp_path: Path):
        """Un config_sectores.json corrupto debe alertarse, no provocar un crash."""
        raiz = _preparar_raiz(tmp_path)
        (raiz / "config_sectores.json").write_text("{esto no es json", encoding="utf-8")
        _escribir_log(raiz, ["[2026-10-09 14:59:00] [INFO] linea"])
        _escribir_eventos(raiz, [{"ts": "2026-10-09T14:59:40", "event": "confirm_click"}])

        resultado = chequeo_salud.chequeo(raiz, ahora=AHORA)

        assert "CONFIG_INVALIDA" in _codigos(resultado)
        assert resultado["ok"] is False

    def test_sin_evidencia_reporta_sin_eventos(self, tmp_path: Path):
        """Sin telemetría ni log, el chequeo informa en vez de asumir que todo va bien."""
        raiz = _preparar_raiz(tmp_path)

        resultado = chequeo_salud.chequeo(raiz, ahora=AHORA)

        assert "SIN_EVIDENCIA" in _codigos(resultado)
        assert resultado["ok"] is False

    def test_hoy_sin_actividad_no_alerta_tasa(self, tmp_path: Path):
        """Sin registros hoy no se puede calcular tasa: no debe alertar por ella."""
        raiz = _preparar_raiz(tmp_path)
        _escribir_log(raiz, ["[2026-10-09 14:59:00] [INFO] linea"])
        _escribir_eventos(raiz, [
            {"ts": "2026-10-09T14:59:40", "event": "bot_start"},
            {"ts": "2026-10-09T14:59:45", "event": "checkbox_found", "id_normalizado": "00337505"},
        ])

        resultado = chequeo_salud.chequeo(raiz, ahora=AHORA)

        assert "TASA_ERROR_ALTA" not in _codigos(resultado)
        assert resultado["tasa_exito_hoy"] is None
