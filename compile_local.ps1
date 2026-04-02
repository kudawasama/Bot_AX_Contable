# Script de Compilacion Local - Bot AX Contable
$SourceDir = $PSScriptRoot
$BuildDir = "$env:USERPROFILE\Bot_AX_Build_Temp"

Write-Host "--- Iniciando Compilacion Local (C:) ---" -ForegroundColor Cyan

# 1. Preparar Carpeta Local
if (Test-Path $BuildDir) { Remove-Item -Path $BuildDir -Recurse -Force }
New-Item -Path $BuildDir -ItemType Directory | Out-Null

# 2. Copiar Archivos Fuente (Ignorar .venv de H:)
Write-Host "[1/5] Sincronizando archivos a C:..."
Copy-Item "$SourceDir\*.py" -Destination $BuildDir
Copy-Item "$SourceDir\requirements.txt" -Destination $BuildDir
if (Test-Path "$SourceDir\patrones") { Copy-Item "$SourceDir\patrones" -Destination $BuildDir -Recurse }
if (Test-Path "$SourceDir\icon.png") { Copy-Item "$SourceDir\icon.png" -Destination $BuildDir }

Set-Location $BuildDir

# 3. Recrear Entorno Local (Mas rapido y sin errores de I/O)
Write-Host "[2/5] Creando entorno de construccion local..."
$PyPath = "$env:LocalAppData\Programs\Python\Python312\python.exe"
& $PyPath -m venv .venv
& .\.venv\Scripts\pip.exe install -r requirements.txt --quiet

# 4. Ejecutar Compilacion
Write-Host "[3/5] Compilando con Nuitka (Esto tardara unos minutos)..."
& .\.venv\Scripts\python.exe -m nuitka `
    --standalone `
    --onefile `
    --windows-disable-console `
    --plugin-enable=tk-inter `
    --include-package=pyautogui,pytesseract,cv2,requests `
    --include-data-dir=patrones=patrones `
    --output-dir=dist `
    --output-filename=Bot_AX_Contable.exe `
    --assume-yes-for-downloads `
    app_gui.py

# 5. Mover Resultado de Vuelta
if (Test-Path "dist\Bot_AX_Contable.exe") {
    Write-Host "[4/5] Compilacion EXITOSA. Moviendo archivo a H:..." -ForegroundColor Green
    if (-not (Test-Path "$SourceDir\dist")) { New-Item -Path "$SourceDir\dist" -ItemType Directory | Out-Null }
    Move-Item -Path "dist\Bot_AX_Contable.exe" -Destination "$SourceDir\dist\Bot_AX_Contable.exe" -Force
} else {
    Write-Host "[ERROR] El compilador no genero el archivo .exe" -ForegroundColor Red
    Read-Host "Presiona Enter para revisar el error."
    exit 1
}

# 6. Limpieza
Write-Host "[5/5] Limpiando archivos temporales..."
Set-Location $SourceDir
# Remove-Item $BuildDir -Recurse -Force # Opcional: comentar si quieres depurar

Write-Host "=========================================="
Write-Host "  LISTO: dist/Bot_AX_Contable.exe generado."
Write-Host "=========================================="
