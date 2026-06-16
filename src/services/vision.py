import os
import time
import pyautogui
import pytesseract
import re
from PIL import Image
from datetime import datetime
from typing import Optional, Tuple, Dict, Union, Any
import threading

from src.core.config import TESSERACT_CMD
from src.core.logger import get_logger

logger = get_logger()

# Nombres cortos de imágenes de patrones para formateo de trazas en consola
NOMBRES_IMAGENES: Dict[str, str] = {
    "btn_registrar_menu.png": "Menu",
    "btn_registrar_confirm.png": "Confirmar",
    "checkbox_vacio.png": "Checkbox",
    "check_usuario_marcado.png": "Check-Marcado",
    "Error_Registro.png": "Error-Ventana",
    "Avanzar_Abajo.png": "Scroll",
    "Formularios_Abiertos.png": "FormAbierto",
    "msg_exito_asiento_1.png": "Exito-Ventana",
    "btn_cerrar_info.png": "Cerrar",
}


def nombre_corto(ruta: str) -> str:
    """Devuelve el nombre corto de un archivo de patrón para simplificar logs.

    Args:
        ruta (str): Ruta completa o nombre del archivo patrón.

    Returns:
        str: Nombre descriptivo asignado o el nombre base del archivo.
    """
    base: str = os.path.basename(ruta)
    return NOMBRES_IMAGENES.get(base, base)


# Establecer ruta del binario de Tesseract OCR
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

# Configurar el retardo por comando nativo de PyAutoGUI
pyautogui.PAUSE = 0.1 


def buscar_y_clickear(
    ruta_imagen: str, 
    sector_region: Optional[Tuple[int, int, int, int]] = None, 
    confidencialidad: float = 0.8, 
    timeout: int = 10, 
    mover_hacia_abajo: bool = False, 
    wait_only: bool = False, 
    stop_event: Optional[threading.Event] = None
) -> Union[Tuple[int, int], bool]:
    """Busca una plantilla de imagen en pantalla y realiza un clic.

    Busca de forma prioritaria en la región especificada y realiza un fallback
    a pantalla completa si no la encuentra.

    Args:
        ruta_imagen (str): Ruta al archivo de imagen patrón.
        sector_region (Optional[Tuple[int, int, int, int]]): Región (x, y, w, h) de búsqueda acotada.
        confidencialidad (float): Confianza mínima de similitud (0.0 a 1.0).
        timeout (int): Tiempo máximo de espera en segundos.
        mover_hacia_abajo (bool): Si es True, presiona la tecla de flecha hacia abajo tras hacer clic.
        wait_only (bool): Si es True, solo localiza el elemento y retorna coordenadas sin clickear.
        stop_event (Optional[threading.Event]): Evento para interrumpir la espera.

    Returns:
        Union[Tuple[int, int], bool]: Coordenadas (x, y) de detección, o False si falla o se cancela.
    """
    if not os.path.exists(ruta_imagen):
        logger.error(f"No se encuentra la imagen: {ruta_imagen}")
        return False

    inicio: float = time.time()
    
    while time.time() - inicio < timeout:
        if stop_event and stop_event.is_set():
            return False
            
        try:
            ubicacion: Any = None
            if sector_region:
                # Validar que la región sea más grande que la imagen a buscar
                try:
                    img = Image.open(ruta_imagen)
                    iw, ih = img.size
                    if iw > sector_region[2] or ih > sector_region[3]:
                        logger.warning(
                            f"Region {sector_region} muy pequeña para {nombre_corto(ruta_imagen)} ({iw}x{ih}). "
                            f"Buscando en pantalla completa."
                        )
                    else:
                        try:
                            ubicacion = pyautogui.locateCenterOnScreen(
                                ruta_imagen, 
                                region=sector_region, 
                                confidence=confidencialidad,
                                grayscale=True
                            )
                        except pyautogui.ImageNotFoundException:
                            pass
                except Exception:
                    # Fallback robusto ante error de lectura
                    try:
                        ubicacion = pyautogui.locateCenterOnScreen(
                            ruta_imagen, 
                            region=sector_region, 
                            confidence=confidencialidad,
                            grayscale=True
                        )
                    except pyautogui.ImageNotFoundException:
                        pass
            
            # Si no se encontró en la región o no se especificó, buscar en pantalla completa
            if not ubicacion:
                try:
                    ubicacion = pyautogui.locateCenterOnScreen(
                        ruta_imagen, 
                        confidence=max(0.7, confidencialidad - 0.1),
                        grayscale=True
                    )
                    if ubicacion and sector_region:
                        logger.warning(f"{nombre_corto(ruta_imagen)} fuera de sector B")
                except pyautogui.ImageNotFoundException:
                    pass

            if ubicacion:
                coords: Tuple[int, int] = (int(ubicacion[0]), int(ubicacion[1]))
                if wait_only:
                    logger.info(f"Detectado: {nombre_corto(ruta_imagen)}")
                    return coords
                
                logger.info(f"Click: {nombre_corto(ruta_imagen)} @ ({coords[0]},{coords[1]})")
                
                # Desplazar mouse y clickear de manera inmediata
                pyautogui.moveTo(coords[0], coords[1])
                pyautogui.click()
                
                if mover_hacia_abajo:
                    logger.info("Presionando FLECHA ABAJO para pasar al siguiente registro.")
                    time.sleep(0.3)
                    pyautogui.press('down')
                    
                return coords
                
        except pyautogui.ImageNotFoundException:
            pass
        except Exception as e:
            logger.error(f"Error durante la búsqueda de imagen: {e}")
            
        time.sleep(0.5) 
        
    logger.warning(f"Timeout: {nombre_corto(ruta_imagen)} no encontrado ({timeout}s).")
    return False


def buscar_estado_checkbox(
    ruta_obj_inicial: str, 
    ruta_obj_final: str, 
    sector_region: Tuple[int, int, int, int], 
    timeout: int = 30, 
    stop_event: Optional[threading.Event] = None
) -> bool:
    """Espera a que un checkbox cambie visualmente a un estado final (marcado).

    Args:
        ruta_obj_inicial (str): Patrón de origen.
        ruta_obj_final (str): Patrón objetivo.
        sector_region (Tuple[int, int, int, int]): Región de búsqueda del checkbox.
        timeout (int): Límite de tiempo en segundos.
        stop_event (Optional[threading.Event]): Señalizador para interrumpir.

    Returns:
        bool: True si cambia de estado, False si expira el tiempo.
    """
    inicio: float = time.time()
    logger.info(f"Esperando a que aparezca {nombre_corto(ruta_obj_final)}...")
    
    while time.time() - inicio < timeout:
        if stop_event and stop_event.is_set():
            return False
            
        try:
             ubicacion = pyautogui.locateCenterOnScreen(
                ruta_obj_final, 
                region=sector_region, 
                confidence=0.8,
                grayscale=True
             )
             if ubicacion:
                 logger.info("Cambio de estado detectado correctamente.")
                 return True
        except pyautogui.ImageNotFoundException:
             pass
             
        time.sleep(0.5)
        
    logger.warning("Timeout esperando cambio de estado en el checkbox.")
    return False


def esperar_resultado_registro(
    ruta_obj_exito: str, 
    ruta_obj_error: str, 
    sector_region: Tuple[int, int, int, int], 
    timeout: int = 300, 
    stop_event: Optional[threading.Event] = None
) -> Optional[str]:
    """Monitorea la pantalla hasta detectar éxito o un pop-up de error de registro en AX.

    Args:
        ruta_obj_exito (str): Patrón de éxito (no utilizado directamente en la lógica interna).
        ruta_obj_error (str): Patrón visual de la ventana de error.
        sector_region (Tuple[int, int, int, int]): Región del Sector A.
        timeout (int): Límite de espera en segundos (hasta 1 hora).
        stop_event (Optional[threading.Event]): Interrupción de la interfaz.

    Returns:
        Optional[str]: 'exito', 'error', 'cancelado' o None si ocurre timeout.
    """
    inicio: float = time.time()
    logger.info(f"Esperando resultado (timeout: {timeout/60:.0f}min)...")
    
    ultimo_mensaje: float = inicio
    while time.time() - inicio < timeout:
        if stop_event and stop_event.is_set():
            return 'cancelado'
            
        # Loguear progreso cada 30 segundos
        if time.time() - ultimo_mensaje > 30:
            logger.info(f"...esperando ({int(time.time() - inicio)}s)")
            ultimo_mensaje = time.time()
            # Desplazar mouse sutilmente para prevenir bloqueo o suspensión
            try:
                pyautogui.moveRel(1, 0)
                pyautogui.moveRel(-1, 0)
            except Exception:
                pass
            
        # 1. Buscar ventana modal de éxito en toda la pantalla
        try:
             from src.core.config import MSG_EXITO_ASIENTO
             ubi_popup = pyautogui.locateCenterOnScreen(
                MSG_EXITO_ASIENTO,
                confidence=0.8,
                grayscale=True
             )
             if ubi_popup:
                 logger.info("-> EXITO! (pop-up confirmado)")
                 pyautogui.press('esc')
                 time.sleep(0.3)
                 pyautogui.press('enter')
                 time.sleep(0.5)
                 return 'exito'
        except pyautogui.ImageNotFoundException:
             pass
        
        # 2. Buscar ventana de error en pantalla completa
        try:
             ubi_error = pyautogui.locateCenterOnScreen(
                ruta_obj_error, 
                confidence=0.9,
                grayscale=True
             )
             if ubi_error:
                 logger.warning("-> ERROR de Registro AX!")
                 return 'error'
        except pyautogui.ImageNotFoundException:
             pass
             
        time.sleep(1)
        
    return None


def leer_id_diario(coord_checkbox: Tuple[int, int]) -> str:
    """Extrae mediante Tesseract OCR el identificador de diario a la derecha del checkbox.

    Args:
        coord_checkbox (Tuple[int, int]): Centro (x, y) de la casilla de origen.

    Returns:
        str: Texto del identificador decodificado u indicador de error.
    """
    cx, cy = coord_checkbox
    from src.core.config import obtener_offset_ocr
    ox, oy, ow, oh = obtener_offset_ocr()
    region_texto: Tuple[int, int, int, int] = (int(cx) + ox, int(cy) + oy, ow, oh)
    
    try:
        # Captura de pantalla en la sección derecha del checkbox
        screenshot = pyautogui.screenshot(region=region_texto)
        screenshot = screenshot.convert('L')  # Convertir a escala de grises
        
        # Modo 7 de Tesseract: tratar la imagen como una línea de texto
        texto: str = pytesseract.image_to_string(screenshot, config='--psm 7').strip()
        # Filtrar caracteres de texto alfanuméricos y guiones
        texto = "".join(c for c in texto if c.isalnum() or c == '-')
        
        return texto if texto else "DESCONOCIDO"
    except Exception as e:
        logger.error(f"Error en OCR: {e}")
        return "ERROR_LECTURA"


def capturar_pantalla_error(id_diario: str = "global") -> Optional[str]:
    """Captura una snapshot de la pantalla completa ante fallas críticas y la guarda.

    Args:
        id_diario (str): Identificador del diario asociado a la captura.

    Returns:
        Optional[str]: Ruta completa del archivo PNG guardado, o None si falla.
    """
    try:
        # Ruta de destino de capturas bajo logs/capturas/ en la raíz del proyecto
        from src.core.config import BASE_DIR
        carpeta_capturas: str = os.path.join(BASE_DIR, "logs", "capturas")
        os.makedirs(carpeta_capturas, exist_ok=True)
            
        ahora: datetime = datetime.now()
        timestamp: str = ahora.strftime("%Y-%m-%d_%H%M%S")
        nombre_archivo: str = f"error_{id_diario}_{timestamp}.png"
        ruta_completa: str = os.path.join(carpeta_capturas, nombre_archivo)
        
        screenshot = pyautogui.screenshot()
        screenshot.save(ruta_completa)
        logger.info(f"Captura de pantalla guardada en: {ruta_completa}")
        return ruta_completa
    except Exception as e:
        logger.error(f"No se pudo realizar la captura de pantalla: {e}")
        return None


def normalizar_id_diario(id_ocr: str) -> str:
    """Extrae y normaliza el ID de diario leído por OCR a su forma canónica (dígitos).

    Args:
        id_ocr (str): Texto en bruto decodificado por OCR.

    Returns:
        str: ID numérico normalizado de al menos 6 dígitos, o el texto limpio.
    """
    digitos = re.findall(r'\d{6,}', id_ocr)
    if digitos:
        return digitos[0]
    return id_ocr.strip().upper()
