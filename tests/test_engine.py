"""Pruebas del ciclo del motor (``src/core/engine.py``).

Se apoyan en los dobles inertes de ``tests/conftest.py``: no mueven el mouse, no capturan
la pantalla y no escriben en los archivos reales del proyecto (telemetría, registro de
resultados y capturas quedan monkeypatcheados).
"""

import threading
import time

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


class TestHeartbeat:
    """B2: el latido permite distinguir «trabajando» de «colgado» sin mirar la pantalla."""

    def test_emite_latidos_periodicos_y_se_detiene(self, monkeypatch):
        latidos = []
        monkeypatch.setattr(
            engine, "event_log", lambda tipo, **datos: latidos.append({"event": tipo, **datos})
        )

        detener = threading.Event()
        hilo = engine.iniciar_heartbeat(detener, intervalo=0.05)

        time.sleep(0.2)
        detener.set()
        hilo.join(timeout=1)

        assert len(latidos) >= 2, "debe latir varias veces mientras la sesión vive"
        assert all(latido["event"] == "bot_heartbeat" for latido in latidos)
        assert not hilo.is_alive(), "tras bot_stop el latido no debe quedar huérfano"

    def test_el_latido_es_un_hilo_daemon(self, monkeypatch):
        """Un hilo no-daemon impediría cerrar la aplicación si el cierre falla."""
        monkeypatch.setattr(engine, "event_log", lambda *_args, **_kwargs: None)
        detener = threading.Event()
        hilo = engine.iniciar_heartbeat(detener, intervalo=10)
        detener.set()
        try:
            assert hilo.daemon is True
        finally:
            hilo.join(timeout=1)
