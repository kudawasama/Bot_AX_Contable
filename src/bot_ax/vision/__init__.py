"""
Visión — submódulos de reconocimiento visual.

No se importan módulos pesados aquí para evitar dependencias circulares
y permitir tests unitarios sin pytesseract/pyautogui instalados.

Importar directamente desde los submódulos:
    from bot_ax.vision.detector import buscar_y_clickear
    from bot_ax.vision.ocr import leer_id_diario
    from bot_ax.vision.ids import normalizar_id_diario
    from bot_ax.vision.captura import capturar_pantalla_error
"""
