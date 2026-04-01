# Guía de Instalación - Bot AX Contable

## Requisitos Previos

1. **Windows 10/11** (64-bit recomendado)
2. **Python 3.10, 3.11 o 3.12** (64-bit desde [python.org](https://www.python.org/downloads/windows/); 3.13 puede dar problemas con alguna librería)
3. **Tesseract-OCR**

---

## Paso 1: Instalar Python

### Opción A: Instalación Estándar (Recomendado)

1. Descarga Python desde: https://www.python.org/downloads/
2. Elige **Python 3.11 o 3.12** (64-bit) para Windows — evita mezclar con la app de Microsoft Store si ves errores raros
3. **MUY IMPORTANTE**: Durante la instalación, marca la opción:
   - ✅ **"Add Python to PATH"** (abajo a la izquierda)
4. Completa la instalación

### Verificar instalación de Python

Abre **Símbolo del sistema (cmd)** y escribe:
```cmd
python --version
```

Deberías ver algo como: `Python 3.11.x`. Si no hay `python` en el PATH pero existe el lanzador `py`, prueba `py -3.11 --version`.

### Si tienes varias versiones de Python

- Desde la carpeta del bot: `py -3.11 setup_env.py` o `py -3.12 setup_env.py`.
- O crea **`python_cmd.local.txt`** con **una sola línea**: la ruta completa a `python.exe` (plantilla: `python_cmd.local.txt.example`). El archivo `Lanzar_Bot_Universal.bat` lo usa automáticamente.

---

## Paso 2: Descargar el Bot

1. Descarga los archivos del Bot AX Contable
2. Crea una carpeta en tu PC (ej: `C:\Bot_AX_Contable\`)
3. Extrae todos los archivos en esa carpeta

---

## Paso 3: Instalar Tesseract-OCR

Tesseract es necesario para el reconocimiento de texto (OCR) en la pantalla.

### Pasos:

1. Descarga el instalador desde:
   https://github.com/UB-Mannheim/tesseract/wiki

2. Busca y descarga: **tesseract-ocr-w64-setup-v5.x.exe** (para Windows 64-bit)

3. Ejecuta el instalador y sigue estos pasos:
   - Acepta los términos de licencia
   - Ruta por defecto recomendada: `C:\Program Files\Tesseract-OCR\`, o otra carpeta si la necesitas
   - Si el instalador ofrece añadir Tesseract al **PATH**, conviene marcarlo
   - Completa la instalación

### Tesseract en una carpeta que no es la habitual

Crea en la carpeta del bot el archivo **`tesseract_path.local.txt`** con **una sola línea** (sin comillas): la ruta completa a `tesseract.exe`, por ejemplo `D:\Herramientas\Tesseract-OCR\tesseract.exe`. Puedes partir de `tesseract_path.local.txt.example`. El bot lo lee antes que la variable de entorno.

### Verificar instalación de Tesseract

Abre **Símbolo del sistema (cmd)** y escribe:
```cmd
tesseract --version
```

Deberías ver información de versión de Tesseract.

---

## Paso 4: Instalar Dependencias de Python

1. Abre **Símbolo del sistema (cmd)**
2. Navega a la carpeta del Bot:
   ```cmd
   cd C:\Bot_AX_Contable\
   ```
3. Actualiza el instalador de paquetes (evita fallos con **Pillow** u OpenCV por `pip` antiguo):
   ```cmd
   python -m pip install --upgrade pip setuptools wheel
   ```
4. Instala las dependencias:
   ```cmd
   python -m pip install -r requirements.txt
   ```

Esto instalará todas las librerías necesarias (incluye Pillow y OpenCV headless).

---

## Paso 5: Ejecutar el Bot

### Opción A: Usar el Lanzador Automático (Recomendado)

1. Busca el archivo: **Lanzar_Bot_Universal.bat**
2. Haz doble clic para ejecutar

El script ejecuta **`install_prereqs.ps1`** y luego **pip**:
- **Python 3.10+**: si no está, prueba **winget** (`Python.Python.3.12`); si no hay winget o falla, **descarga** el instalador desde **python.org** y lo instala en modo silencioso (usuario actual, PATH de usuario).
- **Tesseract**: si no está, prueba **winget** (`UB-Mannheim.TesseractOCR`); si falla, **descarga** el instalador desde **GitHub** (UB-Mannheim) y lo ejecuta en silencio.
- **Pillow, OpenCV, etc.**: `pip install -r requirements.txt` cuando falte algún paquete.
- Hace falta **conexión a Internet** la primera vez. Puede pedir **permisos de administrador** según el instalador.
- Log: `logs\install_prereqs.log`. Para no tocar el sistema: **`BOT_AX_NO_AUTO=1`** (o `BOT_AX_NO_WINGET=1`).
- Inicia el Bot.

### Opción B: Línea de Comando

Abre **Símbolo del sistema (cmd)** en la carpeta del Bot y escribe:
```cmd
python app_gui.py
```

---

## Primer Inicio: Configurar Áreas

Cuando ejecutes el Bot por primera vez:

1. Aparecerá un dialog pidiéndote que selecciones áreas
2. Debes tener **AX Contable abierto** en la pantalla
3. Selecciona las áreas según las instrucciones

---

## Solución de Problemas

### Error: "Python no está instalado"
- Descarga Python desde python.org
- **Importante**: Marca "Add Python to PATH" durante la instalación
- Reinicia tu PC

### Error al instalar Pillow u otro paquete (rueda .whl / versión)

- Ejecuta en la carpeta del bot: `python -m pip install --upgrade pip setuptools wheel`
- Vuelve a ejecutar: `python -m pip install -r requirements.txt`
- Usa **solo una** instalación principal de Python (por ejemplo 3.11 x64), no mezcles con la Microsoft Store

### Error: "No se encuentra tesseract.exe"
- Instala Tesseract-OCR desde: https://github.com/UB-Mannheim/tesseract/wiki
- Usa la ruta de instalación por defecto o marca la opción de añadir Tesseract al PATH del sistema
- Si lo instalaste en una carpeta personalizada, crea una variable de entorno de usuario o de sistema llamada `TESSERACT_CMD` con la ruta completa al archivo `tesseract.exe` (por ejemplo `D:\Apps\Tesseract-OCR\tesseract.exe`)

### Error relacionado con OpenCV o `confidence`
- El bot usa reconocimiento de imagen con umbral de confianza (`confidence`), que depende de OpenCV
- Ejecuta `pip install -r requirements.txt` para instalar `opencv-python-headless` incluido en el proyecto

### Error: "Módulo no encontrado" (ModuleNotFoundError)
- Ejecuta: `pip install -r requirements.txt`
- Verifica que estés en la carpeta correcta del Bot

### El Bot se cierra sin errores
- Revisa los archivos de log en la carpeta `logs/`
- Asegúrate de que los archivos en `patrones/` existen
- Verifica que `config_sectores.json` está configurado

### Las imágenes no se encuentran correctamente
- La carpeta `patrones/` debe estar en el mismo directorio que `app_gui.py`
- Verifica que los archivos PNG existen en `patrones/`

---

## Estructura de Carpetas Requerida

```
Bot_AX_Contable/
├── app_gui.py
├── bot_main.py
├── config.py
├── tesseract_util.py
├── tesseract_path.local.txt (opcional, no versionar; ruta a tesseract.exe)
├── python_cmd.local.txt (opcional; ruta a python.exe si hace falta)
├── config_sectores.json (se crea al configurar áreas)
├── vision.py
├── requirements.txt
├── install_prereqs.ps1
├── Lanzar_Bot_Universal.bat
├── patrones/
│   ├── checkbox_vacio.png
│   ├── btn_registrar_menu.png
│   └── ... (otros archivos PNG)
└── logs/
    └── capturas/
```

---

## Contacto/Soporte

Si encuentras problemas no listados aquí:
1. Verifica que tienes Python 3.8+
2. Verifica que Tesseract-OCR está instalado
3. Revisa los logs en la carpeta `logs/`

---

**Última actualización:** abril 2026
