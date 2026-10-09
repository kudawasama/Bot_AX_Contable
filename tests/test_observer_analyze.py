"""Pruebas de la lectura de telemetría estructurada del observador.

Contexto (incidente 2026-10-08/09): ``scripts/observer_analyze.py`` se apoyaba
solo en ``logs/bot_ax.log``. Cuando ese archivo quedó congelado, el analizador
siguió reportando datos viejos sin avisar, mientras ``logs/events.jsonl`` estaba
al día. Estas pruebas fijan el contrato nuevo: la telemetría estructurada es una
fuente de primera clase y el reporte avisa cuando el log está atrasado.

Ejecutar con: ``python -m pytest tests/test_observer_analyze.py -v``
"""

import json
import sys
from pathlib import Path

import pytest

# El analizador vive en scripts/ (no es un paquete importable): se agrega al path.
SCRIPTS_DIR: Path = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import observer_analyze  # noqa: E402


def _escribir_eventos(destino: Path, eventos: list[dict]) -> Path:
    """Escribe una lista de eventos como JSONL.

    Args:
        destino (Path): Archivo de destino.
        eventos (list[dict]): Eventos a serializar.

    Returns:
        Path: La ruta escrita.
    """
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(
        "\n".join(json.dumps(evento, ensure_ascii=False) for evento in eventos) + "\n",
        encoding="utf-8",
    )
    return destino


class TestResumenDeEventos:
    """Pruebas de resumir_eventos()/resumir_lista_eventos()."""

    def test_resumen_de_eventos_cuenta_exitos_y_errores(self, tmp_path: Path):
        """Cuenta éxitos, errores e IDs con error desde la telemetría."""
        archivo: Path = _escribir_eventos(tmp_path / "events.jsonl", [
            {"ts": "2026-10-09T10:00:00", "event": "bot_start"},
            {"ts": "2026-10-09T10:00:01", "event": "result_exito", "id_normalizado": "00337505"},
            {"ts": "2026-10-09T10:05:00", "event": "result_error", "id_normalizado": "00337501"},
            {"ts": "2026-10-09T10:06:00", "event": "result_error", "id_normalizado": "00337504"},
            {"ts": "2026-10-09T10:06:30", "event": "sector_b_fallback", "elemento": "Menu"},
            {"ts": "2026-10-09T10:06:40", "event": "timeout_menu", "segundos": 30},
        ])

        resumen: dict = observer_analyze.resumir_eventos(archivo)

        assert resumen["total_eventos"] == 6
        assert resumen["exitos"] == 1
        assert resumen["errores"] == 2
        assert resumen["ids_error"] == ["00337501", "00337504"]
        assert resumen["ids_error_unicos"] == 2
        assert resumen["fallbacks_sector_b"] == 1
        assert resumen["timeouts"] == 1
        assert resumen["ultima_fecha"] == "2026-10-09"
        assert resumen["sesiones"]["2026-10-09"] == {"exitos": 1, "errores": 2}

    def test_resumen_ignora_lineas_corruptas(self, tmp_path: Path):
        """Una línea JSON inválida (escritura interrumpida) no rompe el análisis."""
        archivo: Path = tmp_path / "events.jsonl"
        archivo.write_text(
            '{"ts": "2026-10-09T10:00:00", "event": "result_exito"}\n'
            '{"ts": "2026-10-09T10:00:0\n'
            '\n'
            '{"ts": "2026-10-09T10:01:00", "event": "result_error", "id_normalizado": "00337501"}\n',
            encoding="utf-8",
        )

        resumen: dict = observer_analyze.resumir_eventos(archivo)

        assert resumen["total_eventos"] == 2
        assert resumen["exitos"] == 1
        assert resumen["errores"] == 1

    def test_resumen_de_archivo_inexistente_es_vacio(self, tmp_path: Path):
        """Sin archivo de eventos, el resumen queda en cero (nunca lanza)."""
        resumen: dict = observer_analyze.resumir_eventos(tmp_path / "no_existe.jsonl")

        assert resumen["total_eventos"] == 0
        assert resumen["exitos"] == 0
        assert resumen["errores"] == 0
        assert resumen["ultima_fecha"] == ""


class TestDeteccionDeLogDesactualizado:
    """Pruebas de la señal que delata el incidente del log congelado."""

    def test_detecta_telemetria_mas_nueva_que_el_log(self, tmp_path: Path):
        """Con log viejo y eventos nuevos, debe reportarse desactualizado."""
        lineas_log: list[str] = [
            "[2026-10-08 10:52:09] [INFO] -> EXITO! (pop-up confirmado)",
        ]
        eventos: list[dict] = [
            {"ts": "2026-10-09T11:00:00", "event": "result_exito"},
        ]

        assert observer_analyze.telemetria_mas_nueva_que_log(lineas_log, eventos) is True

    def test_log_al_dia_no_se_marca_desactualizado(self):
        """Con el log al día (misma fecha), no se marca desactualizado."""
        lineas_log: list[str] = [
            "[2026-10-09 11:00:05] [INFO] -> EXITO! (pop-up confirmado)",
        ]
        eventos: list[dict] = [
            {"ts": "2026-10-09T11:00:00", "event": "result_exito"},
        ]

        assert observer_analyze.telemetria_mas_nueva_que_log(lineas_log, eventos) is False

    def test_detecta_desfase_del_mismo_dia_por_marca_de_tiempo(self):
        """Regresión: mismo día pero el log horas atrás → debe marcarse desactualizado.

        Caso real del 2026-10-09: el log tenía una línea escrita a las 11:53 (una
        verificación manual del arreglo) mientras el bot seguía registrando hasta
        las 14:56. Comparando solo por FECHA, el aviso no aparecía nunca y el
        analizador volvía a reportar datos incompletos sin decir nada.
        """
        lineas_log: list[str] = [
            "[2026-10-09 11:53:10] [INFO] Verificacion manual del logger",
        ]
        eventos: list[dict] = [
            {"ts": "2026-10-09T14:56:39.666522", "event": "confirm_click"},
        ]

        assert observer_analyze.telemetria_mas_nueva_que_log(lineas_log, eventos) is True


class TestReporteConTelemetria:
    """Pruebas de la integración de la telemetría en el reporte."""

    def test_reporte_incluye_telemetria_y_marca_log_desactualizado(self):
        """generar_reporte() debe exponer la telemetría estructurada."""
        eventos: list[dict] = [
            {"ts": "2026-10-09T11:00:00", "event": "result_exito", "id_normalizado": "00337505"},
            {"ts": "2026-10-09T11:05:00", "event": "result_error", "id_normalizado": "00337501"},
        ]
        lineas_log: list[str] = [
            "[2026-10-08 10:52:09] [INFO] -> EXITO! (pop-up confirmado)",
        ]

        reporte: dict = observer_analyze.generar_reporte(
            entradas=[], blacklist=[], lineas_log=lineas_log, capturas=[], eventos=eventos
        )

        telemetria = reporte["patrones"]["telemetria_estructurada"]
        assert telemetria["exitos"] == 1
        assert telemetria["errores"] == 1
        assert telemetria["log_desactualizado"] is True
        assert reporte["metricas_globales"]["eventos_total"] == 2

    def test_reportes_sin_eventos_siguen_funcionando(self):
        """Sin telemetría (repo antiguo) el reporte no cambia de forma."""
        reporte: dict = observer_analyze.generar_reporte(
            entradas=[], blacklist=[], lineas_log=[], capturas=[]
        )

        assert reporte["patrones"]["telemetria_estructurada"]["total_eventos"] == 0
        assert reporte["patrones"]["telemetria_estructurada"]["log_desactualizado"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
