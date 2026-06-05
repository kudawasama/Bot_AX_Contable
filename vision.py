import os
import time
import pyautogui
import pytesseract
from PIL import Image
from datetime import datetime
from config import TESSERACT_CMD

from logger import get_logger
logger = get_logger()

pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

# PAUSE: Tiempo de espera mínimo después de comandos de pyautogui
pyautogui.PAUSE = 0.1 

def buscar_y_clickear(ruta_imagen, sector_region=None, confidencialidad=0.8, timeout=10, mover_hacia_abajo=False, wait_only=False, stop_event=None):
    """
    Busca una imagen y clickea. Retorna True si la encontró.
    stop_event: Si se activa, termina la búsqueda inmediatamente.
    """
    if not os.path.exists(ruta_imagen):
        logger.error(f"No se encuentra la imagen: {ruta_imagen}")
        return False

    inicio = time.time()
    
    while time.time() - inicio < timeout:
        if stop_event and stop_event.is_set():
            return False
            
        try:
            # Primero intentar en la región específica si existe
            ubicacion = None
            if sector_region:
                # Verificar que la región sea más grande que la imagen a buscar
                try:
                    img = Image.open(ruta_imagen)
                    iw, ih = img.size
                    if iw > sector_region[2] or ih > sector_region[3]:
                        logger.warning(f"Region {sector_region} muy pequeña para {os.path.basename(ruta_imagen)} ({iw}x{ih}). Buscando en pantalla completa.")
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
                    # Si falla la lectura de la imagen, intentar la región de todos modos
                    try:
                        ubicacion = pyautogui.locateCenterOnScreen(
                            ruta_imagen, 
                            region=sector_region, 
                            confidence=confidencialidad,
                            grayscale=True
                        )
                    except pyautogui.ImageNotFoundException:
                        pass
            
            # Si no se encontró en la región o no había región, intentar pantalla completa
            if not ubicacion:
                try:
                    ubicacion = pyautogui.locateCenterOnScreen(
                        ruta_imagen, 
                        confidence=max(0.7, confidencialidad - 0.1), # Reducir un poco más la confianza para el fallback
                        grayscale=True
                    )
                    if ubicacion and sector_region:
                        logger.warning(f"{ruta_imagen} detectado FUERA del sector. Actualizar coordenadas.")
                except pyautogui.ImageNotFoundException:
                    pass

            if ubicacion:
                # Asegurar que las coordenadas sean tipos int nativos
                ubicacion = (int(ubicacion[0]), int(ubicacion[1]))
                # Si solo queremos esperar a que aparezca o cambie de estado visual
                if wait_only:
                    logger.info(f"Imagen detectada: {ruta_imagen}")
                    return ubicacion
                
                logger.info(f"Click en: {ruta_imagen} en {ubicacion}")
                
                # Mover el mouse a la ubicación de forma instantánea
                pyautogui.moveTo(ubicacion[0], ubicacion[1])
                pyautogui.click()
                
                if mover_hacia_abajo:
                    logger.info("Presionando FLECHA ABAJO para pasar al siguiente registro.")
                    # Pequeña pausa antes de bajar para asegurar que el click registró el foco
                    time.sleep(0.3)
                    pyautogui.press('down')
                    
                return ubicacion
                
        except pyautogui.ImageNotFoundException:
            pass # pyautogui en versiones recientes lanza excepción si no encuentra la imagen
        except Exception as e:
            logger.error(f"Error durante la búsqueda de imagen: {e}")
            
        # Velocidad de escaneo: cuánto tiempo esperar entre cada intento de buscar la imagen
        time.sleep(0.5) 
        
    logger.warning(f"Timeout: No se pudo encontrar {ruta_imagen} en {timeout} segundos.")
    return False

def buscar_estado_checkbox(ruta_obj_inicial, ruta_obj_final, sector_region, timeout=30, stop_event=None):
    """
    Espera hasta que el objeto en el Sector A cambie al estado final.
    """
    inicio = time.time()
    logger.info(f"Esperando a que aparezca {ruta_obj_final}...")
    
    while time.time() - inicio < timeout:
        if stop_event and stop_event.is_set():
            return False
            
        try:
             # Buscar la imagen objetivo
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

def esperar_resultado_registro(ruta_obj_exito, ruta_obj_error, sector_region, timeout=300, stop_event=None):
    """
    Espera hasta que aparezca el check de éxito o el cartel de error.
    stop_event: Atiende la parada inmediata de la UI.
    """
    inicio = time.time()
    logger.info(f"Esperando resultado (hasta {timeout/60:.1f} minutos)...")
    
    ultimo_mensaje = inicio
    while time.time() - inicio < timeout:
        if stop_event and stop_event.is_set():
            return 'cancelado'
            
        # Imprimir progreso cada 30 segundos
        if time.time() - ultimo_mensaje > 30:
            logger.info(f"... sigo esperando. Han pasado {int(time.time() - inicio)} segundos.")
            ultimo_mensaje = time.time()
            # Mover el mouse 1 píxel para evitar bloqueo de pantalla por inactividad
            try:
                pyautogui.moveRel(1, 0)
                pyautogui.moveRel(-1, 0)
            except Exception:
                pass
            
        try:
             # Primero buscar el éxito (checkbox marcado en Sector A)
             ubi_exito = pyautogui.locateCenterOnScreen(
                ruta_obj_exito, 
                region=sector_region, 
                confidence=0.8,
                grayscale=True
             )
             if ubi_exito:
                 logger.info("-> Registro en AX completado exitosamente! (checkbox)")
                 return 'exito'
        except pyautogui.ImageNotFoundException:
             pass
        
        # Segundo: buscar pop-up de éxito en pantalla completa
        # (ventana que aparece "frente a todo" cuando el registro finaliza)
        try:
             from config import MSG_EXITO_ASIENTO
             ubi_popup = pyautogui.locateCenterOnScreen(
                MSG_EXITO_ASIENTO,
                confidence=0.8,
                grayscale=True
             )
             if ubi_popup:
                 logger.info("-> Registro en AX completado exitosamente! (pop-up)")
                 # Cerrar el pop-up con una sola tecla ESC
                 pyautogui.press('esc')
                 time.sleep(0.5)
                 return 'exito'
        except pyautogui.ImageNotFoundException:
             pass

        try:
             # Tercero: buscar el error (pantalla completa)
             ubi_error = pyautogui.locateCenterOnScreen(
                ruta_obj_error, 
                confidence=0.9,
                grayscale=True
             )
             if ubi_error:
                 logger.warning("-> Apareció un Error de Registro de AX!")
                 return 'error'
        except pyautogui.ImageNotFoundException:
             pass
             
        time.sleep(1) # Revisar 1 vez por segundo
        
    return None

def leer_id_diario(coord_checkbox):
    """
    Toma una captura pequeña a la derecha del checkbox para leer el número de diario.
    """
    cx, cy = coord_checkbox
    # Offset definido en config_sectores.json (ocr_region_offset)
    from config import obtener_offset_ocr
    ox, oy, ow, oh = obtener_offset_ocr()
    region_texto = (int(cx) + ox, int(cy) + oy, ow, oh)
    
    try:
        # Captura la zona en escala de grises para mejor lectura
        screenshot = pyautogui.screenshot(region=region_texto)
        # Opcional: Guardar debug si el usuario lo necesita
        # screenshot.save("last_ocr_capture.png")
        
        screenshot = screenshot.convert('L') # Escala de grises
        
        # Procesar con OCR (modo 7: una sola línea de texto)
        texto = pytesseract.image_to_string(screenshot, config='--psm 7').strip()
        # Limpieza básica de caracteres no deseados
        texto = "".join(c for c in texto if c.isalnum() or c == '-')
        
        return texto if texto else "DESCONOCIDO"
    except Exception as e:
        logger.error(f"Error en OCR: {e}")
        return "ERROR_LECTURA"

def capturar_pantalla_error(id_diario="global"):
    """
    Captura una imagen de la pantalla completa y la guarda en la carpeta de capturas.
    """
    try:
        carpeta_capturas = os.path.join("logs", "capturas")
        if not os.path.exists(carpeta_capturas):
            os.makedirs(carpeta_capturas)
            
        ahora = datetime.now()
        timestamp = ahora.strftime("%Y-%m-%d_%H%M%S")
        nombre_archivo = f"error_{id_diario}_{timestamp}.png"
        ruta_completa = os.path.join(carpeta_capturas, nombre_archivo)
        
        screenshot = pyautogui.screenshot()
        screenshot.save(ruta_completa)
        logger.info(f"Captura de pantalla guardada en: {ruta_completa}")
        return ruta_completa
    except Exception as e:
        logger.error(f"No se pudo realizar la captura de pantalla: {e}")
        return None


import re

def normalizar_id_diario(id_ocr):
    """
    Normaliza un ID de diario leído por OCR a su forma canónica.
    
    Extrae la parte numérica central (ignorando prefijos como IS/iS/1S/VS/vS
    y sufijos como iat/Diat/iar/Diar/Diai/Dial) y la devuelve en mayúsculas.
    
    Ejemplos:
        'IS00327946iat' -> '00327946'
        'iS00327946Diai' -> '00327946'
        '1S00326946Diat' -> '00326946'
        'VS00325150Dia' -> '00325150'
        '00327946' -> '00327946'
    """
    digitos = re.findall(r'\d{6,}', id_ocr)
    if digitos:
        return digitos[0]
    # Fallback: limpiar y devolver tal cual en mayúsculas
    return id_ocr.strip().upper()
