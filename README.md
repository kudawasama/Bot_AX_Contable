# Bot AX Contable - Guía Rápida

## 🚀 Instalación Rápida en Otro PC

### 1️⃣ Instalar Python
- Descarga **Python 3.11 o 3.12 (64-bit)** desde: https://www.python.org/downloads/windows/
- Evita mezclar con la Microsoft Store si te da conflictos; usa el instalador de python.org.
- **IMPORTANTE**: Marca ✅ "Add Python to PATH" durante la instalación.
- Si `python` no funciona pero tienes varias versiones: `py -3.11 setup_env.py` o crea `python_cmd.local.txt` (ver `python_cmd.local.txt.example`).

### 2️⃣ Instalar Tesseract-OCR
- Descarga desde: https://github.com/UB-Mannheim/tesseract/wiki
- Ejecuta: `tesseract-ocr-w64-setup-v5.x.exe`
- Ruta por defecto o carpeta personalizada: si no está en PATH, crea **`tesseract_path.local.txt`** con una sola línea con la ruta a `tesseract.exe` (plantilla: `tesseract_path.local.txt.example`).

### 3️⃣ Instalar Dependencias
En la carpeta del Bot:
```cmd
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

### 4️⃣ Ejecutar el Bot (recomendado: un solo clic)
- Haz doble clic en **`Lanzar_Bot_Universal.bat`**.
  - Ejecuta **`install_prereqs.ps1`**: intenta instalar **Python 3.12** y **Tesseract** si faltan — primero con **winget**; si no hay winget o falla, **descarga** los instaladores oficiales y los lanza en silencio (hace falta **Internet**).
  - Luego **`pip`** instala **Pillow, OpenCV** y el resto del `requirements.txt` cuando haga falta.
  - Detalle y errores: carpeta `logs\install_prereqs.log`.
  - Para **no** instalar nada del sistema (solo usar lo que ya tengas): variable de entorno **`BOT_AX_NO_AUTO=1`** (o **`BOT_AX_NO_WINGET=1`**, mismo efecto).
- Opción manual: `python app_gui.py` desde la carpeta del proyecto.

---

## 📋 Archivos Importantes

| Archivo | Descripción |
|---------|-------------|
| `Lanzar_Bot_Universal.bat` | Un clic: prerequisitos + pip + arranque del bot |
| `install_prereqs.ps1` | Instala Python y Tesseract si faltan (winget o descarga) |
| `requirements.txt` | Dependencias de Python |
| `setup_env.py` | Verifica que todo esté instalado |
| `tesseract_util.py` | Localiza Tesseract (`tesseract_path.local.txt`, `TESSERACT_CMD`, PATH…) |
| `*.local.txt.example` | Plantillas para ruta de Python / Tesseract en PCs difíciles |
| `INSTALACION.md` | Guía completa de instalación |
| `app_gui.py` | Interfaz gráfica del bot |

---

## ❓ Solucionar Problemas

### Python no se reconoce
- Desinstala Python completamente
- Vuelve a instalar marcando "Add Python to PATH"
- Reinicia tu PC

### Tesseract no se encuentra
- Archivo **`tesseract_path.local.txt`**: una línea con la ruta completa a `tesseract.exe` (copia desde `tesseract_path.local.txt.example`).
- O variable **`TESSERACT_CMD`**, o instalar en `C:\Program Files\Tesseract-OCR\` con PATH.

### Pillow, OpenCV o errores al instalar paquetes
- Ejecuta antes: `python -m pip install --upgrade pip setuptools wheel`
- Luego: `python -m pip install -r requirements.txt` desde la carpeta del bot.
- Asegúrate de usar **Python 3.10–3.12** de 64 bits, no una mezcla de instalaciones.

### Módulos no encontrados
1. Carpeta del Bot: `cd C:\ruta\del\Bot\`
2. `python -m pip install -r requirements.txt`

---

## 📞 Verificar Instalación

Ejecuta este script para verificar que todo está correcto:
```cmd
python setup_env.py
```

---

**Ver la guía completa en: [INSTALACION.md](INSTALACION.md)**
