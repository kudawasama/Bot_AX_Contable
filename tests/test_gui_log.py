"""Pruebas de B5: las trazas del motor deben llegar también al archivo de log.

``run_bot`` entrega sus mensajes por ``log_callback``. Si ese callback solo los encola para
la consola de la GUI, el módulo ``logging`` nunca los ve y ``logs/bot_ax.log`` queda ciego a
las trazas de arranque y de cada ciclo (justo lo que ocurrió el 2026-10-13: la primera línea
de la sesión en el archivo era del primer ciclo y faltaba toda la configuración inicial).
"""

import queue

import pytest

from src.ui import gui_classic, gui_gemini


class _RegistradorFalso:
    """Sustituto del logger que anota lo que se le pide."""

    def __init__(self) -> None:
        self.mensajes = []

    def info(self, mensaje: str) -> None:
        self.mensajes.append(mensaje)


class _ObjetoMinimo:
    """El callback bajo prueba no necesita la ventana de Tkinter."""


class _GuiGeminiMinima:
    """Versión sin ventana que sí necesita su cola de consola."""

    def __init__(self) -> None:
        self.log_queue = queue.Queue()


@pytest.fixture
def registrador(monkeypatch):
    """Reemplaza el logger de ambas GUI por el registrador falso."""
    falso = _RegistradorFalso()
    monkeypatch.setattr(gui_classic, "logger", falso)
    monkeypatch.setattr(gui_gemini, "logger", falso)
    return falso


class TestTrazasDelMotorVanAlLog:
    """El callback del motor debe pasar por el logger."""

    def test_gui_classic_emite_por_el_logger(self, registrador):
        gui_classic.BotAXGui.log(_ObjetoMinimo(), "Iniciando Bot AX Contable...")

        assert registrador.mensajes == ["Iniciando Bot AX Contable..."]

    def test_gui_classic_conserva_los_marcadores_de_resultado(self, registrador):
        """La GUI cuenta éxitos y errores buscando '[RESULT:OK]' en el texto: debe sobrevivir."""
        gui_classic.BotAXGui.log(
            _ObjetoMinimo(), "[RESULT:OK] -> Registro de 00337505 completado."
        )

        assert "[RESULT:OK]" in registrador.mensajes[0]
        assert "[RESULT:ERROR]" not in registrador.mensajes[0]

    def test_gui_gemini_emite_al_logger_y_a_su_consola(self, registrador):
        """Gemini no monta QueueLogHandler: debe hacer las dos cosas."""
        gui = _GuiGeminiMinima()

        gui_gemini.BotAXRegistroGui._log(gui, "Iniciando Bot AX Contable...")

        assert registrador.mensajes == ["Iniciando Bot AX Contable..."]
        assert gui.log_queue.get_nowait() == "Iniciando Bot AX Contable..."
