r# Guía de Instalación - Bot AX Contable

## Requisitos Previos

1. **Windows 10/11** (64-bit recomendado)
2. **Python 3.8 o superior**
3. **Tesseract-OCR**

---

## Paso 1: Instalar Python

### Opción A: Instalación Estándar (Recomendado)

1. Descarga Python desde: https://www.python.org/downloads/
2. Elige la versión **3.10 o superior** para Windows
3. **MUY IMPORTANTE**: Durante la instalación, marca la opción:
   - ✅ **"Add Python to PATH"** (abajo a la izquierda)
4. Completa la instalación

### Verificar instalación de Python

Abre **Símbolo del sistema (cmd)** y escribe:
```cmd
python --version
```

Deberías ver algo como: `Python 3.10.x`

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
   - Selecciona la ruta de instalación por defecto: `C:\Program Files\Tesseract-OCR\`
   - Completa la instalación

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
3. Instala las dependencias:
   ```cmd
   pip install -r requirements.txt
   ```

Esto instalará todas las librerías necesarias.

---

## Paso 5: Ejecutar el Bot

### Opción A: Usar el Lanzador Automático (Recomendado)

1. Busca el archivo: **Lanzar_Bot_Universal.bat**
2. Haz doble clic para ejecutar

El script:
- Verificará que Python esté instalado
- Instalará dependencias si faltan
- Buscará Tesseract-OCR
- Iniciará el Bot

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

### Error: "No se encuentra tesseract.exe"
- Instala Tesseract-OCR desde: https://github.com/UB-Mannheim/tesseract/wiki
- Usa la ruta de instalación por defecto

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
├── config_sectores.json (se crea al configurar áreas)
├── vision.py
├── requirements.txt
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
