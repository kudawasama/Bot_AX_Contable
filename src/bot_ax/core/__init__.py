"""
Core — submódulos del núcleo del bot.

No se importan módulos pesados aquí para evitar import circular
(core.logger → core.__init__ → core.engine → vision.detector → core.logger).
Importar directamente desde los submódulos:
    from bot_ax.core.engine import run_bot
    from bot_ax.core.logger import get_logger
"""
