import os
import time
import pyautogui
import pytesseract
from PIL import Image

# Configuración de Tesseract OCR
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\jose.cespedes\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

# Configuraciones de seguridad de pyautogui
pyautogui.FAILSAFE = True
# PAUSE: Tiempo de espera (en segundos) después de CADA comando de pyautogui (click, press, etc.)
pyautogui.PAUSE = 0.5 

def buscar_y_clickear(ruta_imagen, sector_region=None, confidencialidad=0.9, timeout=10, mover_hacia_abajo=False, wait_only=False):
    """
    Busca una imagen en la pantalla (opcionalmente dentro de una región).
    Retorna True si la encontró y (opcionalmente) le hizo click, False si se acabó el tiempo.
    """
    if not os.path.exists(ruta_imagen):
        print(f"ERROR: No se encuentra la imagen: {ruta_imagen}")
        return False

    inicio = time.time()
    
    while time.time() - inicio < timeout:
        try:
            # Buscar en pantalla completa o en una región específica
            ubicacion = pyautogui.locateCenterOnScreen(
                ruta_imagen, 
                region=sector_region, 
                confidence=confidencialidad,
                grayscale=True
            )
            
            if ubicacion:
                # Asegurar que las coordenadas sean tipos int nativos de Python y no np.int64
                ubicacion = (int(ubicacion[0]), int(ubicacion[1]))
                # Si solo queremos esperar a que aparezca o cambie de estado visual
                if wait_only:
                    print(f"Imagen detectada: {ruta_imagen}")
                    return ubicacion
                
                print(f"Click en: {ruta_imagen} en {ubicacion}")
                
                # Mover el mouse a la ubicación y hacer click
                # duration: Segundos que tarda el puntero en desplazarse hasta el objetivo
                pyautogui.moveTo(ubicacion[0], ubicacion[1], duration=0.2)
                pyautogui.click()
                
                if mover_hacia_abajo:
                    print("Presionando FLECHA ABAJO para pasar al siguiente registro.")
                    # Pequeña pausa antes de bajar para asegurar que el click registró el foco
                    time.sleep(0.3)
                    pyautogui.press('down')
                    
                return ubicacion
                
        except pyautogui.ImageNotFoundException:
            pass # pyautogui en versiones recientes lanza excepción si no encuentra la imagen
        except Exception as e:
            print(f"Error durante la búsqueda de imagen: {e}")
            
        # Velocidad de escaneo: cuánto tiempo esperar entre cada intento de buscar la imagen
        time.sleep(0.5) 
        
    print(f"Timeout: No se pudo encontrar {ruta_imagen} en {timeout} segundos.")
    return False

def buscar_estado_checkbox(ruta_obj_inicial, ruta_obj_final, sector_region, timeout=30):
    """
    Espera hasta que el objeto en el Sector A cambie al estado final especificado.
    """
    inicio = time.time()
    print(f"Esperando a que aparezca {ruta_obj_final}...")
    
    while time.time() - inicio < timeout:
        try:
             # Buscar la imagen objetivo
             ubicacion = pyautogui.locateCenterOnScreen(
                ruta_obj_final, 
                region=sector_region, 
                confidence=0.9,
                grayscale=True
             )
             if ubicacion:
                 print("Cambio de estado detectado correctamente.")
                 return True
        except pyautogui.ImageNotFoundException:
             pass
             
        time.sleep(0.5)
        
    print("Timeout esperando cambio de estado en el checkbox.")
    return False

def esperar_resultado_registro(ruta_obj_exito, ruta_obj_error, sector_region, timeout=300):
    """
    Espera hasta 5 minutos (configurable) verificando si aparece el check de éxito o el cartel de error.
    Retorna 'exito' si se registra bien, 'error' si salta un error, o None por timeout.
    """
    inicio = time.time()
    print(f"Esperando resultado (hasta {timeout/60:.1f} minutos)...")
    
    ultimo_mensaje = inicio
    while time.time() - inicio < timeout:
        # Imprimir progreso cada 30 segundos
        if time.time() - ultimo_mensaje > 30:
            print(f"... sigo esperando. Han pasado {int(time.time() - inicio)} segundos.")
            ultimo_mensaje = time.time()
            
        try:
             # Primero buscar el éxito
             ubi_exito = pyautogui.locateCenterOnScreen(
                ruta_obj_exito, 
                region=sector_region, 
                confidence=0.9,
                grayscale=True
             )
             if ubi_exito:
                 print("-> ¡Registro en AX completado exitosamente!")
                 return 'exito'
        except pyautogui.ImageNotFoundException:
             pass

        try:
             # Segundo buscar el error (pantalla completa o sector de error)
             ubi_error = pyautogui.locateCenterOnScreen(
                ruta_obj_error, 
                confidence=0.9,
                grayscale=True
             )
             if ubi_error:
                 print("-> ¡Apareció un Error de Registro de AX!")
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
    # Ajuste fino basado en debug_ocr_pos1.png:
    # El ID empieza unos 270px a la izquierda del centro del checkbox.
    # r1 era (cx - 320, cy - 12, 300, 30). El número está centrado en ese tramo.
    region_texto = (int(cx) - 275, int(cy) - 13, 110, 28)
    
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
        print(f"Error en OCR: {e}")
        return "ERROR_LECTURA"

