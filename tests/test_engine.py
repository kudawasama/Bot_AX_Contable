"""Pruebas del ciclo del motor (``src/core/engine.py``).

Se apoyan en los dobles inertes de ``tests/conftest.py``: no mueven el mouse, no capturan
la pantalla y no escriben en los archivos reales del proyecto (telemetría, registro de
resultados y capturas quedan monkeypatcheados).
"""

import threading

from src.core import engine


def _preparar_ciclo(monkeypatch, mock_pyautogui):
    """Deja ``run_bot`` ejecutable sin efectos reales y devuelve lo observado."""
    eventos = []
    registros = []

    monkeypatch.setattr(engine, "event_log", lambda tipo, **datos: eventos.append({"event": tipo, **datos}))
    monkeypatch.setattr(engine, "registrar_log", lambda identificador, resultado: registros.append((identificador, resultado)))
    monkeypatch.setattr(engine, "capturar_pantalla_error", lambda nombre="global": f"falso/{nombre}.png")
    monkeypatch.setattr(engine.time, "sleep", lambda _segundos: None)
    return eventos, registros, mock_pyautogui


class _Caja:
    """Casilla falsa que imita lo que devuelve ``pyautogui.locateAllOnScreen``."""

    top = 100
    left = 10


class _Punto:
    x = 100
    y = 200


class TestIdIlegibleNoSeProcesa:
    """B1b: un ID ilegible se salta; nunca se procesa con un valor dudoso."""

    def test_no_marca_ni_registra_una_casilla_con_id_ilegible(self, monkeypatch, mock_pyautogui):
        eventos, registros, gui = _preparar_ciclo(monkeypatch, mock_pyautogui)

        # El motor ignora las casillas que no están debajo de la última marcada, así que
        # el doble debe distinguir el patrón: para "marcado" no hay nada, para "vacío" hay
        # una casilla (con `y` mayor que 0).
        def _por_patron(patron, **_kwargs):
            return [] if patron == engine.CHK_MARCADO else [_Caja()]

        gui.locateAllOnScreen.side_effect = _por_patron
        gui.center.return_value = _Punto()
        monkeypatch.setattr(engine, "leer_id_diario", lambda _coord: "ERROR_LECTURA")
        monkeypatch.setattr(engine, "normalizar_id_diario", lambda _texto: "ERROR_LECTURA")

        engine.run_bot(log_callback=lambda _mensaje: None, stop_event=threading.Event())

        tipos = [evento["event"] for evento in eventos]
        assert "id_ilegible" in tipos, "debe dejar constancia del ID ilegible"
        assert "checkbox_found" not in tipos, "no debe dar por encontrado un diario ilegible"
        assert registros == [], "no debe registrar ningún diario"
