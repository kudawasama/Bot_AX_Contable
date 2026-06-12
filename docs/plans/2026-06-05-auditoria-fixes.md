# Plan de Implementación — Fixes de Auditoría Bot AX Contable

> **Para Hermes:** Implementar tarea por tarea, verificando cada fix con ejecución real (no simulación). Usar `ast.parse()` para validación de sintaxis. Hacer commit después de cada tarea completada.

**Goal:** Corregir los bugs bloqueantes (P0) y de alta prioridad (P1) detectados en la auditoría del 2026-06-05, mejorando la fiabilidad, eficiencia y mantenibilidad del bot.

**Architecture:** Modificaciones incrementales sobre el código existente sin reescribir la arquitectura. Cada fix es independiente y verificable. Se prioriza no romper el comportamiento actual mientras se corrigen los defectos.

**Tech Stack:** Python 3.12, PyAutoGUI, Tesseract OCR, Tkinter — el mismo stack del proyecto.

---

## 🗺️ Resumen de Fases

| Fase | Prioridad | Tareas | Archivos afectados | Tiempo estimado |
|------|-----------|--------|-------------------|-----------------|
| 1 | 🔴 P0 | 5 tareas | `config.py`, `bot_main.py`, `vision.py` | 30 min |
| 2 | 🟡 P1 | 4 tareas | `bot_main.py`, `vision.py`, `config_sectores.json`, `.bat` | 25 min |
| 3 | 🟢 P2 | 4 tareas | `bot_main.py`, `app_gui.py`, nuevo `logger.py`, `tests/` | 45 min |

---

## FASE 1: 🔴 Bloqueantes (P0) — Estabilizar el bot

---

### Tarea 1.1: Arreglar rutas relativas con `__file__` (Bug B3)

**Objective:** Hacer que las rutas a imágenes patrón funcionen sin importar desde qué directorio se ejecute el bot.

**Files:**
- Modify: `config.py:6-22`

**Step 1: Reemplazar rutas relativas por rutas absolutas basadas en `__file__`**

Abrir `config.py` y modificar:

```python
# ANTES (línea 6-22):
CONFIG_FILE = "config_sectores.json"
PATRONES_DIR = "patrones"

CHK_VACIO = os.path.join(PATRONES_DIR, "checkbox_vacio.png")
BTN_MENU = os.path.join(PATRONES_DIR, "btn_registrar_menu.png")
BTN_CONFIRM = os.path.join(PATRONES_DIR, "btn_registrar_confirm.png")
CHK_MARCADO = os.path.join(PATRONES_DIR, "check_usuario_marcado.png")
IMG_ERROR = os.path.join(PATRONES_DIR, "Error_Registro.png")
BTN_ABAJO = os.path.join(PATRONES_DIR, "Avanzar_Abajo.png")
IMG_FORMULARIOS = os.path.join(PATRONES_DIR, "Formularios_Abiertos.png")

# DESPUÉS:
import os
import json
import sys

# Directorio base: donde está este archivo (config.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_DIR, "config_sectores.json")
PATRONES_DIR = os.path.join(BASE_DIR, "patrones")

CHK_VACIO = os.path.join(PATRONES_DIR, "checkbox_vacio.png")
BTN_MENU = os.path.join(PATRONES_DIR, "btn_registrar_menu.png")
BTN_CONFIRM = os.path.join(PATRONES_DIR, "btn_registrar_confirm.png")
CHK_MARCADO = os.path.join(PATRONES_DIR, "check_usuario_marcado.png")
IMG_ERROR = os.path.join(PATRONES_DIR, "Error_Registro.png")
BTN_ABAJO = os.path.join(PATRONES_DIR, "Avanzar_Abajo.png")
IMG_FORMULARIOS = os.path.join(PATRONES_DIR, "Formularios_Abiertos.png")
```

**Step 2: Verificar sintaxis**

```bash
cd "H:\Mi unidad\Desarrollo y Proyectos\GitHub\Bot_AX_Contable"
python -c "import ast; ast.parse(open('config.py', encoding='utf-8').read()); print('OK')"
```

Expected: `OK`

**Step 3: Commit**

```bash
git add config.py
git commit -m "fix: usar __file__ para rutas absolutas en config.py (B3)"
```

---

### Tarea 1.2: Ampliar región de detección de éxito (Bug B2)

**Objective:** Evitar timeouts de 60 minutos por región de búsqueda demasiado pequeña. Usar el Sector A completo para buscar el check marcado en vez de 40×40 px.

**Files:**
- Modify: `bot_main.py:177-187`

**Step 1: Cambiar la región de éxito en `bot_main.py`**

```python
# ANTES (línea 177-187):
            # Paso D: Esperar resultado
            px, py = punto_click_a
            region_especifica_checkbox = (int(px)-20, int(py)-20, 40, 40)
            time.sleep(2)
            
            resultado = esperar_resultado_registro(
                ruta_obj_exito=CHK_MARCADO,
                ruta_obj_error=IMG_ERROR,
                sector_region=region_especifica_checkbox,
                timeout=3600,
                stop_event=stop_event
            )

# DESPUÉS:
            # Paso D: Esperar resultado
            px, py = punto_click_a
            time.sleep(2)
            
            # Usar el Sector A completo para detectar el check marcado (evita falsos negativos por región pequeña)
            resultado = esperar_resultado_registro(
                ruta_obj_exito=CHK_MARCADO,
                ruta_obj_error=IMG_ERROR,
                sector_region=sector_a,
                timeout=3600,
                stop_event=stop_event
            )
```

**Step 2: Verificar sintaxis**

```bash
python -c "import ast; ast.parse(open('bot_main.py', encoding='utf-8').read()); print('OK')"
```

Expected: `OK`

**Step 3: Commit**

```bash
git add bot_main.py
git commit -m "fix: usar sector_a completo para detectar éxito en vez de región 40x40 (B2)"
```

---

### Tarea 1.3: Normalizar IDs de diario para lista negra efectiva (Bug B1)

**Objective:** Hacer que la lista negra funcione correctamente a pesar de las variaciones de OCR. Extraer el núcleo numérico del ID y comparar ignorando mayúsculas/minúsculas y prefijos erróneos.

**Files:**
- Modify: `vision.py` (agregar función `normalizar_id_diario`)
- Modify: `bot_main.py:96-109` y `bot_main.py:199-201`

**Step 1: Agregar función de normalización en `vision.py`**

Al final de `vision.py`, agregar:

```python
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
    """
    digitos = re.findall(r'\d{6,}', id_ocr)
    if digitos:
        return digitos[0]
    # Fallback: limpiar y devolver tal cual en mayúsculas
    return id_ocr.strip().upper()
```

**Step 2: Verificar sintaxis de `vision.py`**

```bash
python -c "import ast; ast.parse(open('vision.py', encoding='utf-8').read()); print('OK')"
```

Expected: `OK`

**Step 3: Modificar `bot_main.py` para usar IDs normalizados**

Cambiar la importación:

```python
# ANTES (línea 4):
from vision import buscar_y_clickear, buscar_estado_checkbox, esperar_resultado_registro, leer_id_diario, capturar_pantalla_error

# DESPUÉS:
from vision import buscar_y_clickear, buscar_estado_checkbox, esperar_resultado_registro, leer_id_diario, capturar_pantalla_error, normalizar_id_diario
```

Cambiar la lógica de blacklist (líneas 96-109):

```python
# ANTES:
                for i, loc in enumerate(todas_vacias):
                    centro = gui.center(loc)
                    coord = (int(centro.x), int(centro.y))
                    identificador = leer_id_diario(coord)
                    
                    if identificador in diarios_con_error:
                        if intentos_scroll == 0:
                            log(f"  -> Ignorando {identificador} (lista negra).")
                        continue
                    
                    casilla_objetivo = coord
                    id_actual = identificador
                    break

# DESPUÉS:
                for i, loc in enumerate(todas_vacias):
                    centro = gui.center(loc)
                    coord = (int(centro.x), int(centro.y))
                    identificador = leer_id_diario(coord)
                    id_normalizado = normalizar_id_diario(identificador)
                    
                    # Usar ID normalizado para comparar con la lista negra
                    if id_normalizado in diarios_con_error:
                        if intentos_scroll == 0:
                            log(f"  -> Ignorando {identificador} (lista negra, normalizado: {id_normalizado}).")
                        continue
                    
                    casilla_objetivo = coord
                    id_actual = identificador
                    break
```

Cambiar cómo se agrega a la lista negra (líneas 199-201):

```python
# ANTES:
                 log(f"[RESULT:ERROR] Se detectó un Error en {id_actual}. A la lista negra.")
                 capturar_pantalla_error(id_actual)
                 registrar_log(id_actual, "ERROR")
                 diarios_con_error.append(id_actual)

# DESPUÉS:
                 log(f"[RESULT:ERROR] Se detectó un Error en {id_actual}. A la lista negra.")
                 capturar_pantalla_error(id_actual)
                 registrar_log(id_actual, "ERROR")
                 diarios_con_error.append(normalizar_id_diario(id_actual))
```

**Step 4: Verificar sintaxis de `bot_main.py`**

```bash
python -c "import ast; ast.parse(open('bot_main.py', encoding='utf-8').read()); print('OK')"
```

Expected: `OK`

**Step 5: Commit**

```bash
git add vision.py bot_main.py
git commit -m "fix: normalizar IDs de diario para que la lista negra funcione con variaciones OCR (B1)"
```

---

### Tarea 1.4: Validar Tesseract al inicio del bot (Bug B6)

**Objective:** Verificar que el binario de Tesseract existe ANTES de empezar a procesar diarios. Dar un mensaje claro si no se encuentra.

**Files:**
- Modify: `config.py` (agregar función `validar_tesseract`)
- Modify: `bot_main.py:36-40` (llamar validación al iniciar)

**Step 1: Agregar validación en `config.py`**

Al final de `config.py`, agregar:

```python
def validar_tesseract():
    """Verifica que Tesseract OCR esté instalado y accesible."""
    if not os.path.exists(TESSERACT_CMD):
        raise FileNotFoundError(
            f"Tesseract OCR no encontrado en: {TESSERACT_CMD}\n"
            f"Instálalo desde https://github.com/UB-Mannheim/tesseract/wiki "
            f"o configura la variable de entorno TESSERACT_CMD con la ruta correcta."
        )
    return True
```

**Step 2: Llamar validación en `bot_main.py`**

```python
# ANTES (línea 31-40):
    def log(msg):
        log_callback(msg)
        
    log("Iniciando Bot AX Contable...")
    
    # 1. Cargar la configuración de los sectores
    sectores = cargar_configuracion()

# DESPUÉS:
    def log(msg):
        log_callback(msg)
        
    log("Iniciando Bot AX Contable...")
    
    # 0. Validar que Tesseract esté disponible
    from config import validar_tesseract
    try:
        validar_tesseract()
        log("Tesseract OCR verificado.")
    except FileNotFoundError as e:
        log(f"ERROR CRÍTICO: {e}")
        return False
    
    # 1. Cargar la configuración de los sectores
    sectores = cargar_configuracion()
```

**Step 3: Verificar sintaxis**

```bash
python -c "import ast; ast.parse(open('config.py', encoding='utf-8').read()); print('OK')"
python -c "import ast; ast.parse(open('bot_main.py', encoding='utf-8').read()); print('OK')"
```

Expected: `OK` para ambos.

**Step 4: Commit**

```bash
git add config.py bot_main.py
git commit -m "fix: validar Tesseract OCR al iniciar el bot (B6)"
```

---

## FASE 2: 🟡 Alta Prioridad (P1) — Eficiencia y robustez

---

### Tarea 2.1: Persistir lista negra en archivo JSON (Bug B7)

**Objective:** Guardar los IDs normalizados de diarios con error en un archivo `blacklist.json` para que sobrevivan a reinicios del bot. Cargarlos al iniciar.

**Files:**
- Modify: `bot_main.py:56` y `bot_main.py:197-202`
- Create: `blacklist.json` (auto-generado)

**Step 1: Agregar carga/guardado de blacklist en `bot_main.py`**

Al inicio de `run_bot()`, después de la carga de sectores (línea 43), agregar:

```python
    # 1.5. Cargar lista negra persistente
    blacklist_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blacklist.json")
    diarios_con_error = []
    if os.path.exists(blacklist_file):
        try:
            with open(blacklist_file, "r") as f:
                diarios_con_error = json.load(f)
            log(f"Lista negra cargada: {len(diarios_con_error)} diarios con error previo.")
        except Exception:
            diarios_con_error = []
```

Agregar el import de `json` y `os` al inicio de `bot_main.py`:

```python
# ANTES (línea 1):
import sys

# DESPUÉS:
import sys
import json
import os
```

Donde se agrega a la lista negra (línea ~200), agregar guardado:

```python
# DESPUÉS de diarios_con_error.append(...):
                 diarios_con_error.append(normalizar_id_diario(id_actual))
                 # Guardar lista negra actualizada
                 try:
                     with open(blacklist_file, "w") as f:
                         json.dump(diarios_con_error, f)
                 except Exception:
                     pass
```

Nota: `blacklist_file` ya está definida arriba en la misma función.

**Step 2: Agregar `blacklist.json` a `.gitignore`**

```bash
# En .gitignore, agregar:
echo "blacklist.json" >> .gitignore
```

**Step 3: Verificar sintaxis**

```bash
python -c "import ast; ast.parse(open('bot_main.py', encoding='utf-8').read()); print('OK')"
```

Expected: `OK`

**Step 4: Commit**

```bash
git add bot_main.py .gitignore
git commit -m "fix: persistir lista negra en blacklist.json entre reinicios (B7)"
```

---

### Tarea 2.2: Mover OCR después del filtro por posición (Bug B4)

**Objective:** Evitar OCR innecesario. Cachear posiciones de pantalla ya visitadas para no volver a hacer OCR en checkboxes ya procesados.

**Files:**
- Modify: `bot_main.py:56-57` y `bot_main.py:89-109`

**Step 1: Agregar caché de posiciones procesadas**

Después de `diarios_con_error = []` (o donde esté definido), agregar:

```python
    posiciones_procesadas = set()  # Cache de coordenadas (x, y) ya procesadas
```

**Step 2: Modificar el loop de búsqueda de checkboxes**

```python
# ANTES (líneas 89-109):
                try:
                    todas_vacias = list(gui.locateAllOnScreen(CHK_VACIO, region=sector_a, confidence=0.9, grayscale=True))
                    todas_vacias.sort(key=lambda loc: loc.top)
                except Exception:
                    todas_vacias = []

                casilla_objetivo = None
                id_actual = "DESCONOCIDO"

                for i, loc in enumerate(todas_vacias):
                    centro = gui.center(loc)
                    coord = (int(centro.x), int(centro.y))
                    identificador = leer_id_diario(coord)
                    id_normalizado = normalizar_id_diario(identificador)
                    
                    if id_normalizado in diarios_con_error:
                        if intentos_scroll == 0:
                            log(f"  -> Ignorando {identificador} (lista negra, normalizado: {id_normalizado}).")
                        continue
                    
                    casilla_objetivo = coord
                    id_actual = identificador
                    break

# DESPUÉS:
                try:
                    todas_vacias = list(gui.locateAllOnScreen(CHK_VACIO, region=sector_a, confidence=0.9, grayscale=True))
                    todas_vacias.sort(key=lambda loc: loc.top)
                except Exception:
                    todas_vacias = []

                casilla_objetivo = None
                id_actual = "DESCONOCIDO"

                for i, loc in enumerate(todas_vacias):
                    centro = gui.center(loc)
                    coord = (int(centro.x), int(centro.y))
                    coord_redondeada = (coord[0] // 5 * 5, coord[1] // 5 * 5)  # tolerancia de 5px
                    
                    # Saltar si ya procesamos esta posición
                    if coord_redondeada in posiciones_procesadas:
                        continue
                    
                    identificador = leer_id_diario(coord)
                    id_normalizado = normalizar_id_diario(identificador)
                    
                    # Marcar posición como visitada
                    posiciones_procesadas.add(coord_redondeada)
                    
                    if id_normalizado in diarios_con_error:
                        if intentos_scroll == 0:
                            log(f"  -> Ignorando {identificador} (lista negra, normalizado: {id_normalizado}).")
                        continue
                    
                    casilla_objetivo = coord
                    id_actual = identificador
                    break
```

**Step 3: Verificar sintaxis**

```bash
python -c "import ast; ast.parse(open('bot_main.py', encoding='utf-8').read()); print('OK')"
```

Expected: `OK`

**Step 4: Commit**

```bash
git add bot_main.py
git commit -m "perf: cachear posiciones procesadas para evitar OCR redundante (B4)"
```

---

### Tarea 2.3: Externalizar coordenadas OCR a `config_sectores.json` (Bug B5)

**Objective:** Mover las coordenadas hardcodeadas de la región OCR a la configuración, permitiendo ajustarlas sin modificar código.

**Files:**
- Modify: `config_sectores.json`
- Modify: `config.py`
- Modify: `vision.py:200-201`

**Step 1: Agregar la región OCR a `config_sectores.json`**

```json
{
    "sector_a": [16, 193, 325, 488],
    "sector_b": [1152, 87, 208, 35],
    "sector_scroll": [349, 645, 33, 23],
    "ocr_region_offset": [-275, -13, 110, 28]
}
```

**Step 2: Exponer la configuración OCR en `config.py`**

```python
# Agregar en config.py, después de CHK_VACIO...IMG_FORMULARIOS:
def obtener_offset_ocr(config=None):
    """Obtiene el offset de la región OCR desde la configuración, con fallback."""
    if config is None:
        config = cargar_configuracion()
    if config and "ocr_region_offset" in config:
        return tuple(config["ocr_region_offset"])
    # Fallback a valores hardcodeados
    return (-275, -13, 110, 28)
```

**Step 3: Usar la configuración en `vision.py`**

```python
# ANTES (línea 200-201):
    region_texto = (int(cx) - 275, int(cy) - 13, 110, 28)

# DESPUÉS:
    from config import obtener_offset_ocr
    ox, oy, ow, oh = obtener_offset_ocr()
    region_texto = (int(cx) + ox, int(cy) + oy, ow, oh)
```

**Step 4: Actualizar `debug_ocr.py` para que también use la config**

En `debug_ocr.py`, reemplazar los valores hardcodeados con `obtener_offset_ocr()` para mantener consistencia.

**Step 5: Verificar sintaxis**

```bash
python -c "import ast; ast.parse(open('vision.py', encoding='utf-8').read()); print('OK')"
python -c "import ast; ast.parse(open('config.py', encoding='utf-8').read()); print('OK')"
```

Expected: `OK` para ambos.

**Step 6: Commit**

```bash
git add config_sectores.json config.py vision.py debug_ocr.py
git commit -m "refactor: externalizar coordenadas OCR a config_sectores.json (B5)"
```

---

### Tarea 2.4: Arreglar silent failure en `.bat` files (Bug B8)

**Objective:** Mostrar mensajes de error si la unidad H: no está disponible o el directorio del proyecto no existe.

**Files:**
- Modify: `Lanzar_Bot.bat`
- Modify: `Lanzar_Bot_Registro.bat`

**Step 1: Mejorar `Lanzar_Bot.bat`**

```batch
@echo off
title Bot AX Contable - Lanzador
:: Verificar que la unidad H: existe
if not exist "H:\" (
    echo ERROR: La unidad H: no esta disponible. Conecta Google Drive.
    pause
    exit /b 1
)
:: Entrar a la carpeta del proyecto
cd /d "H:\Mi unidad\Desarrollo y Proyectos\GitHub\Bot_AX_Contable"
if errorlevel 1 (
    echo ERROR: No se pudo acceder a la carpeta del proyecto.
    echo Ruta: H:\Mi unidad\Desarrollo y Proyectos\GitHub\Bot_AX_Contable
    pause
    exit /b 1
)
:: Verificar que el script existe
if not exist "app_gui.py" (
    echo ERROR: No se encontro app_gui.py en la carpeta actual.
    pause
    exit /b 1
)
:: Ejecutar la interfaz grafica
start "" "%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe" app_gui.py
exit
```

**Step 2: Mejorar `Lanzar_Bot_Registro.bat`** (misma lógica pero con `bot_ax_registro.py`)

```batch
@echo off
title Bot AX Registro - Lanzador Gemini Engine
if not exist "H:\" (
    echo ERROR: La unidad H: no esta disponible. Conecta Google Drive.
    pause
    exit /b 1
)
cd /d "H:\Mi unidad\Desarrollo y Proyectos\GitHub\Bot_AX_Contable"
if errorlevel 1 (
    echo ERROR: No se pudo acceder a la carpeta del proyecto.
    pause
    exit /b 1
)
if not exist "bot_ax_registro.py" (
    echo ERROR: No se encontro bot_ax_registro.py
    pause
    exit /b 1
)
start "" "%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe" bot_ax_registro.py
exit
```

**Step 3: Commit**

```bash
git add Lanzar_Bot.bat Lanzar_Bot_Registro.bat
git commit -m "fix: agregar verificaciones de error en .bat files (B8)"
```

---

## FASE 3: 🟢 Media Prioridad (P2) — Calidad y mantenibilidad

---

### Tarea 3.1: Reemplazar `print()` con módulo `logging`

**Objective:** Implementar logging estructurado con niveles, timestamps, y rotación de archivos. Mantener compatibilidad con los callbacks de las GUIs.

**Files:**
- Create: `logger.py`
- Modify: `bot_main.py` (cambiar `print` por `log`)
- Modify: `vision.py` (cambiar `print` por `logging`)
- Modify: `app_gui.py` (eliminar `sys.stdout` hack)

**Step 1: Crear `logger.py`**

```python
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

def setup_logger(name="bot_ax", log_dir="logs"):
    """Configura y devuelve un logger con salida a archivo rotativo y consola."""
    os.makedirs(log_dir, exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Evitar duplicados si se llama múltiples veces
    if logger.handlers:
        return logger
    
    # Formato: [2026-06-05 13:04:08] [INFO] mensaje
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Archivo rotativo (máx 5MB, 3 backups)
    log_file = os.path.join(log_dir, "bot_ax.log")
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5*1024*1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Consola (solo INFO+)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

# Logger global
logger = setup_logger()
```

**Step 2: Reemplazar `print()` en `vision.py`**

```python
# Agregar al inicio de vision.py:
from logger import logger

# Reemplazar todos los print() por logger.info/warning/error:
# print(f"ERROR: ...")  -> logger.error(...)
# print(f"AVISO: ...")   -> logger.warning(...)
# print(f"Click en: ...") -> logger.debug(...)
# print("-> ...")        -> logger.info(...)
```

**Step 3: Adaptar `app_gui.py` para capturar logs**

Eliminar las líneas que secuestran `sys.stdout`/`sys.stderr` y en su lugar agregar un `logging.Handler` personalizado que encole los mensajes al `log_queue`:

```python
import logging

class QueueLogHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue
    
    def emit(self, record):
        msg = self.format(record)
        self.log_queue.put(msg)
```

Configurarlo en `__init__` de `BotAXGui`:

```python
# Reemplazar las líneas sys.stdout = QueueLogger(...) con:
queue_handler = QueueLogHandler(self.log_queue)
queue_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logging.getLogger("bot_ax").addHandler(queue_handler)
```

**Step 4: Verificar sintaxis**

```bash
python -c "import ast; ast.parse(open('logger.py', encoding='utf-8').read()); print('OK')"
```

Expected: `OK`

**Step 5: Commit**

```bash
git add logger.py vision.py app_gui.py
git commit -m "refactor: reemplazar print() con logging estructurado (P2)"
```

---

### Tarea 3.2: Agregar validación de `config_sectores.json`

**Objective:** Validar que el archivo de configuración tenga el formato correcto y coordenadas dentro de la pantalla.

**Files:**
- Modify: `config.py` (función `cargar_configuracion`)

**Step 1: Mejorar `cargar_configuracion()`**

```python
def cargar_configuracion():
    """Carga y valida la configuracion de sectores desde JSON."""
    if not os.path.exists(CONFIG_FILE):
        return None
    
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: {CONFIG_FILE} no es un JSON válido: {e}")
        return None
    
    # Validar que existen los 3 sectores requeridos
    for key in ["sector_a", "sector_b"]:
        if key not in config:
            print(f"ERROR: Falta '{key}' en {CONFIG_FILE}")
            return None
        val = config[key]
        if not isinstance(val, list) or len(val) != 4:
            print(f"ERROR: '{key}' debe ser una lista de 4 números [x, y, w, h]")
            return None
        if not all(isinstance(n, (int, float)) for n in val):
            print(f"ERROR: '{key}' contiene valores no numéricos")
            return None
    
    return config
```

**Step 2: Verificar sintaxis**

```bash
python -c "import ast; ast.parse(open('config.py', encoding='utf-8').read()); print('OK')"
```

Expected: `OK`

**Step 3: Commit**

```bash
git add config.py
git commit -m "feat: agregar validación de config_sectores.json (P2)"
```

---

### Tarea 3.3: Crear tests unitarios básicos

**Objective:** Agregar tests para las funciones puras (normalización, validación de config, rutas).

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/test_vision.py`
- Create: `tests/test_config.py`

**Step 1: Crear `tests/test_vision.py`**

```python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vision import normalizar_id_diario

def test_normalizar_id_basico():
    assert normalizar_id_diario("IS00327946iat") == "00327946"

def test_normalizar_id_minuscula():
    assert normalizar_id_diario("iS00327946Diai") == "00327946"

def test_normalizar_id_prefijo_1():
    assert normalizar_id_diario("1S00326946Diat") == "00326946"

def test_normalizar_id_prefijo_VS():
    assert normalizar_id_diario("VS00325150Dia") == "00325150"

def test_normalizar_id_solo_digitos():
    assert normalizar_id_diario("00327946") == "00327946"

def test_normalizar_id_vacio():
    result = normalizar_id_diario("DESCONOCIDO")
    assert result == "DESCONOCIDO"

def test_normalizar_id_sin_digitos():
    result = normalizar_id_diario("ERROR_LECTURA")
    assert result == "ERROR_LECTURA"
```

**Step 2: Crear `tests/test_config.py`**

```python
import sys
import os
import json
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config

def test_validar_config_valida():
    data = {"sector_a": [0, 0, 100, 100], "sector_b": [10, 10, 50, 50]}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        temp_path = f.name
    try:
        original = config.CONFIG_FILE
        config.CONFIG_FILE = temp_path
        result = config.cargar_configuracion()
        assert result == data
    finally:
        config.CONFIG_FILE = original
        os.unlink(temp_path)

def test_validar_config_falta_sector():
    data = {"sector_a": [0, 0, 100, 100]}  # falta sector_b
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        temp_path = f.name
    try:
        original = config.CONFIG_FILE
        config.CONFIG_FILE = temp_path
        result = config.cargar_configuracion()
        assert result is None
    finally:
        config.CONFIG_FILE = original
        os.unlink(temp_path)

def test_validar_config_json_invalido():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write("esto no es json{{{")
        temp_path = f.name
    try:
        original = config.CONFIG_FILE
        config.CONFIG_FILE = temp_path
        result = config.cargar_configuracion()
        assert result is None
    finally:
        config.CONFIG_FILE = original
        os.unlink(temp_path)
```

**Step 3: Ejecutar tests**

```bash
cd "H:\Mi unidad\Desarrollo y Proyectos\GitHub\Bot_AX_Contable"
python -m pytest tests/ -v
```

Expected: 10 passed

**Step 4: Commit**

```bash
git add tests/
git commit -m "test: agregar tests unitarios para normalización y validación de config (P2)"
```

---

### Tarea 3.4: Crear `README.md`

**Objective:** Documentar el proyecto para nuevos desarrolladores y usuarios.

**Files:**
- Create: `README.md`

**Step 1: Crear README.md**

```markdown
# Bot AX Contable

Bot de automatización para Microsoft Dynamics AX que registra diarios contables automáticamente mediante reconocimiento de imágenes y OCR.

## Requisitos

- **Python 3.12**
- **Tesseract OCR** (instalado desde [UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki))
- Dependencias Python: `pip install -r requirements.txt`

## Instalación

1. Clonar el repositorio:  
   `git clone <repo-url> Bot_AX_Contable`

2. Instalar dependencias:  
   `pip install -r requirements.txt`

3. Instalar Tesseract OCR y configurar la variable de entorno `TESSERACT_CMD` si la ruta por defecto no coincide.

4. Configurar sectores de pantalla:  
   `python setup_areas.py`

## Uso

### Interfaz gráfica (recomendado)

```bash
python app_gui.py
```

O doble clic en `Lanzar_Bot.bat`

### Verificar instalación

```bash
python test_ocr.py        # Verifica Tesseract
python diagnose_vision.py  # Verifica patrones de imagen
```

## Estructura del proyecto

```
Bot_AX_Contable/
├── bot_main.py          # Núcleo del bot (ciclo principal)
├── vision.py            # OCR + reconocimiento de imágenes
├── config.py            # Configuración y validación
├── logger.py            # Logging estructurado
├── app_gui.py           # Interfaz gráfica moderna (Tkinter)
├── setup_areas.py       # Herramienta para definir sectores
├── patrones/            # Imágenes patrón para template matching
├── config_sectores.json # Coordenadas de sectores de pantalla
├── tests/               # Tests unitarios
├── logs/                # Logs y capturas de error
└── blacklist.json       # Diarios con error (auto-generado)
```

## Funcionamiento

1. El bot busca checkboxes vacíos en la ventana de AX (Sector A)
2. Lee el ID del diario con OCR (Tesseract)
3. Ignora diarios previamente fallidos (lista negra persistente)
4. Hace clic en "Registrar" → Confirma
5. Espera el resultado (éxito: check marcado, error: popup)
6. Registra el resultado y continúa con el siguiente

## Solución de problemas

- **"Tesseract no encontrado"**: Verificar `TESSERACT_CMD` en variables de entorno
- **"Sectores no definidos"**: Ejecutar `python setup_areas.py`
- **"No encuentra checkboxes"**: Verificar que AX está visible y los patrones coinciden con la resolución actual
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: agregar README.md con instrucciones de instalación y uso"
```

---

## ✅ Resumen final de commits

| Fase | Commits | Archivos |
|------|---------|----------|
| 1 (P0) | 4 commits | `config.py`, `bot_main.py`, `vision.py` |
| 2 (P1) | 4 commits | `bot_main.py`, `config.py`, `config_sectores.json`, `vision.py`, `debug_ocr.py`, `.bat` files |
| 3 (P2) | 4 commits | `logger.py` (nuevo), `vision.py`, `app_gui.py`, `config.py`, `tests/` (nuevo), `README.md` (nuevo) |
| **Total** | **12 commits** | **~15 archivos** |

---

## ⚠️ Notas importantes

- **No modificar la lógica de registro de AX**: Los cambios son solo en la capa de detección y control del bot. El flujo de interacción con AX permanece igual.
- **`blacklist.json` se auto-genera**: Se agrega a `.gitignore` para no versionar datos de producción.
- **Los tests requieren `pytest`**: Si no está instalado, ejecutar `pip install pytest` antes de la Fase 3.
- **Rollback fácil**: Cada commit es atómico y revierte un solo fix. Usar `git revert <commit>` si algún cambio causa problemas.
