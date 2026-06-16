# Arquitectura y Estructura del Proyecto — Bot AX Contable

Este documento describe la estructura modular del proyecto tras la reestructuración completa realizada para asegurar su mantenibilidad, legibilidad, escalabilidad y apego a los principios de diseño de software profesional (SRP).

---

## Vista General de la Estructura

El proyecto se divide en módulos lógicos bajo el directorio `src/`, y utilitarios auxiliares de depuración y versionado bajo el directorio `scripts/`. La raíz se mantiene limpia y libre de archivos temporales.

```
Bot_AX_Contable/
│
├── config_sectores.json       # Configuración calibrada de las coordenadas de sectores
├── blacklist.json             # Lista negra persistente de diarios con error de registro
│
├── Lanzar_Bot.bat             # Lanzador clásico de Windows (Tkinter)
├── Lanzar_Bot_Registro.bat    # Lanzador moderno Gemini Engine (Tkinter Glow)
│
├── patrones/                  # Plantillas de imágenes patrón (PNG) utilizadas por OpenCV
│   ├── checkbox_vacio.png
│   ├── check_usuario_marcado.png
│   ├── btn_registrar_menu.png
│   ├── btn_registrar_confirm.png
│   ├── Error_Registro.png
│   ├── Avanzar_Abajo.png
│   └── msg_exito_asiento_1.png
│
├── src/                       # Código fuente de la aplicación
│   ├── __init__.py
│   │
│   ├── core/                  # Núcleo del bot y lógica de ejecución central
│   │   ├── __init__.py
│   │   ├── config.py          # Rutas, constantes y gestor de configuración física
│   │   ├── logger.py          # Logger estructurado con rotación de archivos
│   │   ├── version.py         # Control de versión dinámica y estado Git
│   │   └── engine.py          # Motor de automatización y bucle del bot
│   │
│   ├── services/              # Lógica de negocio de visión e integración
│   │   ├── __init__.py
│   │   └── vision.py          # Envoltura de PyAutoGUI, OpenCV y Tesseract OCR
│   │
│   └── ui/                    # Interfaces de usuario
│       ├── __init__.py
│       ├── area_selector.py   # Ventana de Tkinter para calibración de sectores
│       ├── gui_classic.py     # GUI de Tkinter clásica (GitHub style)
│       └── gui_gemini.py      # GUI de Tkinter abisal Gemini Engine
│
└── scripts/                   # Scripts de diagnóstico y utilidades de automatización
    ├── debug_ocr.py           # Depuración de captura OCR lateral derecha
    ├── debug_pantalla.py      # Diagnóstico de resolución e información de monitores
    ├── diagnose_vision.py     # Diagnóstico de existencia y detección de patrones
    ├── test_ocr.py            # Test simple del motor Tesseract OCR
    └── bump_version.py        # Script para autoincremento de versión en Git
```

---

## Responsabilidades de los Módulos (`src/`)

### 1. `src/core/` (Núcleo)
* **[config.py](file:///h:/Mi%20unidad/Desarrollo%20y%20Proyectos/GitHub/Bot_AX_Contable/src/core/config.py)**: Define las rutas absolutas físicas de almacenamiento basándose en la raíz del proyecto. Expone las constantes de imágenes patrón y las funciones para cargar/guardar la configuración de sectores (`config_sectores.json`).
* **[logger.py](file:///h:/Mi%20unidad/Desarrollo%20y%20Proyectos/GitHub/Bot_AX_Contable/src/core/logger.py)**: Inicializa un logger con rotación automática de archivos (máximo 5MB por archivo, hasta 3 archivos de respaldo codificados en UTF-8) en la carpeta `/logs`. Proporciona un handler personalizado para redirigir trazas de eventos a la GUI mediante colas de hilos (`queue.Queue`).
* **[version.py](file:///h:/Mi%20unidad/Desarrollo%20y%20Proyectos/GitHub/Bot_AX_Contable/src/core/version.py)**: Fuente única de verdad sobre la versión del bot. Invoca comandos subprocess de Git para extraer el SHA corto del último commit y detectar si hay cambios no confirmados (dirty tree).
* **[engine.py](file:///h:/Mi%20unidad/Desarrollo%20y%20Proyectos/GitHub/Bot_AX_Contable/src/core/engine.py)**: Contiene la lógica síncrona principal de automatización (`run_bot`). Ejecuta la toma de decisiones basada en los resultados de visión artificial, realiza el control de flujo (pausa/parada), aplica margen de seguridad a las coordenadas del Sector A, y filtra los diarios ya procesados utilizando las coordenadas de los checkboxes marcados.

### 2. `src/services/` (Servicios)
* **[vision.py](file:///h:/Mi%20unidad/Desarrollo%20y%20Proyectos/GitHub/Bot_AX_Contable/src/services/vision.py)**: Agrupa el procesamiento de imágenes con OpenCV (búsqueda de patrones mediante `matchTemplate`), manipulación de periféricos con PyAutoGUI (clicks, movimientos del mouse, envío de teclas) y decodificación de caracteres con Tesseract OCR (`pytesseract`).

### 3. `src/ui/` (Presentación)
* **[area_selector.py](file:///h:/Mi%20unidad/Desarrollo%20y%20Proyectos/GitHub/Bot_AX_Contable/src/ui/area_selector.py)**: Despliega una capa negra semitransparente sobre la pantalla completa. Permite arrastrar el ratón para capturar y delimitar en caliente las coordenadas de las tres áreas del bot.
* **[gui_classic.py](file:///h:/Mi%20unidad/Desarrollo%20y%20Proyectos/GitHub/Bot_AX_Contable/src/ui/gui_classic.py)**: Panel clásico estilo GitHub con barras de progreso y consola con resaltado de sintaxis de logs interactiva (clic derecho sobre errores para eliminarlos del flujo).
* **[gui_gemini.py](file:///h:/Mi%20unidad/Desarrollo%20y%20Proyectos/GitHub/Bot_AX_Contable/src/ui/gui_gemini.py)**: Panel moderno "Gemini Engine" con estética abisal, conejito ASCII decorativo e indicadores simulados de uso del sistema.


---

## Consideraciones Críticas de Diseño e Interacción

### 1. Control del Foco No Destructivo (Dynamics AX)
* **Regla de Interacción:** El bot no realiza clics ciegos de foco (por ejemplo, en la parte superior de la tabla de registros en el Sector A). Dynamics AX interpreta los clics en registros procesados como una acción para alternar el marcado o limpiar las selecciones existentes, lo cual corrompe el estado del bucle.
* **Solución de Foco Dirigido:** La ventana de Dynamics AX recupera el foco de pantalla de manera segura y natural en el instante en que el bot realiza el movimiento de cursor y clic directamente sobre la coordenada de la `casilla_objetivo` vacía a procesar en el ciclo en curso. Esto minimiza el viaje del puntero del mouse y protege la integridad de los checks ya completados.

---

## Ejecución del Proyecto

Debido a que las interfaces gráficas se encuentran dentro del paquete modular `src.ui`, para ejecutarlas correctamente desde la terminal se debe incluir la raíz del repositorio en el path de Python (`PYTHONPATH`) e invocarlas como módulos usando la opción `-m`.

Los scripts lanzadores `.bat` ya implementan esta lógica de manera automática:

### Lanzar Interfaz Gemini Engine (Predeterminada)
Hacer doble clic en `Lanzar_Bot_Registro.bat`. Equivale a ejecutar en PowerShell:
```powershell
set PYTHONPATH=.
python -m src.ui.gui_gemini
```

### Lanzar Interfaz Clásica
Hacer doble clic en `Lanzar_Bot.bat`. Equivale a ejecutar en PowerShell:
```powershell
set PYTHONPATH=.
python -m src.ui.gui_classic
```

---

## Diagnóstico y Depuración (`scripts/`)

* **`diagnose_vision.py`**: Comprueba la resolución nativa de tu pantalla primaria y realiza un escaneo completo de prueba buscando las imágenes patrón `checkbox_vacio.png` y `btn_registrar_menu.png` con la confianza de la app (`0.85`).
* **`debug_ocr.py`**: Localiza el primer checkbox vacío en pantalla y toma tres capturas rectangulares a su derecha aplicando diferentes offsets y anchos para comprobar visualmente en cuál de ellas se puede leer con mayor nitidez el ID de diario.
* **`debug_pantalla.py`**: Toma una captura completa en la raíz (`vista_principal.png`) y detalla información sobre tus monitores en pantalla.
* **`test_ocr.py`**: Comprueba que la variable de entorno o la ruta a Tesseract OCR en el equipo resuelva con éxito imprimiendo la versión del software de OCR.
* **`bump_version.py`**: Incrementa automáticamente la versión en `src/core/version.py`. Soporta incremento del tipo `patch`, `minor` y `major`.
