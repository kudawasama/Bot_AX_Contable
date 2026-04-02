# Lanzador PowerShell Bot AX Contable {Cotano_}
Write-Host "--- Lanzador PowerShell Bot AX ---" -ForegroundColor Cyan

# Asegurar que estamos en la carpeta correcta
Set-Location $PSScriptRoot

# 0. Limpieza de entorno corrupto (Si se creo en Linux/Bash)
if (Test-Path ".venv\bin") {
    Write-Host "[!] Detectado entorno virtual incompatible (Linux-style). Reconstruyendo para Windows..." -ForegroundColor Yellow
    Remove-Item -Path ".venv" -Recurse -Force -ErrorAction SilentlyContinue
}

# 1. Tesseract
if (-not (Test-Path "bin\tesseract\tesseract.exe")) {
    Write-Host "[!] Instalando componentes basicos (Tesseract)..." -ForegroundColor Yellow
    & .\install_prereqs.ps1
}

# 2. Localizar Python 3.12 (Ruta de usuario detectada)
$PyPath = "$env:LocalAppData\Programs\Python\Python312\python.exe"
if (-not (Test-Path $PyPath)) {
    # Intenta buscar en otras versiones si la 3.12 no esta exactamente ahi
    $PyFolder = Get-ChildItem "$env:LocalAppData\Programs\Python" -Name | Select-Object -First 1
    if ($PyFolder) {
        $PyPath = "$env:LocalAppData\Programs\Python\$PyFolder\python.exe"
    } else {
        $PyPath = "python.exe"
    }
}

# 3. Entorno Virtual
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "[!] Creando entorno .venv aislado..." -ForegroundColor Yellow
    & $PyPath -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] No se pudo crear el entorno virtual con: $PyPath" -ForegroundColor Red
        Read-Host "Presiona Enter para cerrar"
        exit
    }
}

# 4. Dependencias
Write-Host "[i] Verificando dependencias..."
& .\.venv\Scripts\pip.exe install -r requirements.txt

# 5. Ejecutar Bot
Write-Host "[OK] Iniciando Bot..." -ForegroundColor Green
& .\.venv\Scripts\python.exe app_gui.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] El bot ha terminado con un codigo de error: $LASTEXITCODE" -ForegroundColor Red
    Read-Host "Presiona Enter para cerrar"
}
