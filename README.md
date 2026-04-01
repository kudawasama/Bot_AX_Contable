# Bot AX Contable - Guía Rápida

## 🚀 Instalación Rápida en Otro PC

### 1️⃣ Instalar Python
- Descarga desde: https://www.python.org/downloads/ (Python 3.10+)
- **IMPORTANTE**: Marca ✅ "Add Python to PATH" durante la instalación
- Reinicia tu PC

### 2️⃣ Instalar Tesseract-OCR
- Descarga desde: https://github.com/UB-Mannheim/tesseract/wiki
- Ejecuta: `tesseract-ocr-w64-setup-v5.x.exe`
- Instala en la ruta por defecto: `C:\Program Files\Tesseract-OCR\`

### 3️⃣ Instalar Dependencias
Abre **Símbolo del sistema** en la carpeta del Bot y ejecuta:
```cmd
pip install -r requirements.txt
```

### 4️⃣ Ejecutar el Bot
- **Opción A**: Haz doble clic en `Lanzar_Bot_Universal.bat`
- **Opción B**: Ejecuta `python app_gui.py` en símbolo del sistema

---

## 📋 Archivos Importantes

| Archivo | Descripción |
|---------|-------------|
| `Lanzar_Bot_Universal.bat` | Ejecuta el bot (nuevo, más flexible) |
| `requirements.txt` | Dependencias de Python |
| `setup_env.py` | Verifica que todo esté instalado |
| `INSTALACION.md` | Guía completa de instalación |
| `app_gui.py` | Interfaz gráfica del bot |

---

## ❓ Solucionar Problemas

### Python no se reconoce
- Desinstala Python completamente
- Vuelve a instalar marcando "Add Python to PATH"
- Reinicia tu PC

### Tesseract no se encuentra
- Instala Tesseract desde https://github.com/UB-Mannheim/tesseract/wiki
- Usa la ruta por defecto

### Módulos no encontrados
1. Abre **Símbolo del sistema**
2. Navega a la carpeta del Bot: `cd C:\ruta\del\Bot\`
3. Ejecuta: `pip install -r requirements.txt`

---

## 📞 Verificar Instalación

Ejecuta este script para verificar que todo está correcto:
```cmd
python setup_env.py
```

---

**Ver la guía completa en: [INSTALACION.md](INSTALACION.md)**
