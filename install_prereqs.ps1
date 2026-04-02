#Requires -Version 5.1
<#
  Instala Python 3.10+ y Tesseract si no están (winget, o descarga + instalación silenciosa).
  Llamado desde Lanzar_Bot_Universal.bat. Requiere red la primera vez.
#>

param(
    [switch]$SkipPython,
    [switch]$SkipTesseract
)

$ErrorActionPreference = 'Continue'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogDir = Join-Path $ScriptDir 'logs'
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }
$LogFile = Join-Path $LogDir 'install_prereqs.log'

function Write-Log([string]$Message) {
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $Message"
    Add-Content -Path $LogFile -Value $line -Encoding UTF8
    Write-Host $Message
}

try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
} catch {}

function Update-EnvPath {
    $m = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $u = [Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = "$m;$u"
}

function Resolve-PythonPath {
    param([string]$Cmd)
    $Cmd = $Cmd.Trim()
    try {
        if ($Cmd -match '^\s*py\s+-') {
            $out = & py --list-paths 2>$null
            if ($out) {
                foreach ($ln in $out) {
                    $ln = $ln.Trim()
                    if ($ln -match '\s+-3\.1[0-9]' -and $ln -match '^([A-Z]:\\.+python\.exe)') {
                        $p = $Matches[1]
                        if (Test-Path $p) { return $p }
                    }
                }
            }
        }
        $out = & $Cmd -c "import sys; print(sys.executable)" 2>$null
        if ($out -and (Test-Path $out.Trim())) { return $out.Trim() }
    } catch {}
    return $null
}

function Save-PythonLocal {
    param([string]$Cmd)
    $resolved = Resolve-PythonPath $Cmd
    if (-not $resolved) { return $false }
    $f = Join-Path $ScriptDir 'python_cmd.local.txt'
    [System.IO.File]::WriteAllText($f, $resolved, [System.Text.Encoding]::UTF8)
    return $true
}

function Save-TesseractLocal {
    param([string]$Path)
    $f = Join-Path $ScriptDir 'tesseract_path.local.txt'
    [System.IO.File]::WriteAllText($f, $Path, [System.Text.Encoding]::UTF8)
    return $true
}

function Test-PythonOk {
    param([Parameter(Mandatory)][string]$Invoke)
    $Invoke = $Invoke.Trim()
    try {
        if ($Invoke -match '^\s*py\s+-') {
            $tok = @($Invoke.Trim() -split '\s+')
            if ($tok.Length -ge 2) {
                & $tok[0] $tok[1] -c "import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 10) else 1)" 2>$null
                return ($LASTEXITCODE -eq 0)
            }
            return $false
        }
        & $Invoke -c "import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 10) else 1)" 2>$null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

function Get-PythonCommand {
    Update-EnvPath
    $local = Join-Path $ScriptDir 'python_cmd.local.txt'
    if (Test-Path $local) {
        $line = (Get-Content $local -Encoding UTF8 -TotalCount 1).Trim().Trim('"')
        if ($line -and -not $line.StartsWith('#') -and (Test-Path $line)) {
            if (Test-PythonOk $line) { return $line }
        }
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        if (Test-PythonOk 'python') { return 'python' }
    }
    if (Get-Command py -ErrorAction SilentlyContinue) {
        foreach ($v in @('12', '11', '10')) {
            & py "-3.$v" -c "import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 10) else 1)" 2>$null
            if ($LASTEXITCODE -eq 0) { return "py -3.$v" }
        }
    }
    foreach ($p in @(
            "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
            "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
            "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
            'C:\Program Files\Python312\python.exe'
        )) {
        if (Test-Path $p) {
            if (Test-PythonOk $p) { return $p }
        }
    }
    return $null
}

function Get-TesseractPath {
    $f = Join-Path $ScriptDir 'tesseract_path.local.txt'
    if (Test-Path $f) {
        foreach ($raw in Get-Content $f -Encoding UTF8) {
            $line = $raw.Trim().Trim('"')
            if (-not $line -or $line.StartsWith('#')) { continue }
            if (Test-Path $line) { return $line }
        }
    }
    $e = $env:TESSERACT_CMD
    if ($e) {
        $e = $e.Trim().Trim('"')
        if (Test-Path $e) { return $e }
    }
    foreach ($p in @(
            (Join-Path $ScriptDir 'bin\tesseract\tesseract.exe'),
            'C:\Program Files\Tesseract-OCR\tesseract.exe',
            'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'
        )) {
        if (Test-Path $p) { return $p }
    }
    $regPaths = @(
        'HKLM:\SOFTWARE\Tesseract-OCR',
        'HKLM:\SOFTWARE\WOW6432Node\Tesseract-OCR',
        'HKCU:\SOFTWARE\Tesseract-OCR',
        'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*',
        'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*',
        'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*'
    )
    foreach ($regPath in $regPaths) {
        try {
            $items = Get-ItemProperty -Path $regPath -ErrorAction SilentlyContinue
            if ($items) {
                foreach ($item in @($items)) {
                    $installDir = $item.InstallLocation
                    if ($installDir -and (Test-Path $installDir)) {
                        $candidate = Join-Path $installDir 'tesseract.exe'
                        if (Test-Path $candidate) { return $candidate }
                    }
                    $dispName = $item.DisplayName
                    if ($dispName -and $dispName -match 'Tesseract') {
                        $candidate = Join-Path (Split-Path $regPath -Parent) 'tesseract.exe'
                    }
                }
            }
        } catch {}
    }
    $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
    if ($userPath) {
        foreach ($dir in $userPath -split ';') {
            $d = $dir.Trim().Trim('"')
            if (-not $d) { continue }
            $candidate = Join-Path $d 'tesseract.exe'
            if (Test-Path $candidate) { return $candidate }
        }
    }
    $machinePath = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    if ($machinePath) {
        foreach ($dir in $machinePath -split ';') {
            $d = $dir.Trim().Trim('"')
            if (-not $d) { continue }
            $candidate = Join-Path $d 'tesseract.exe'
            if (Test-Path $candidate) { return $candidate }
        }
    }
    $cmd = Get-Command tesseract -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $where = & cmd /c 'where tesseract.exe' 2>$null
    if ($where) {
        foreach ($line in $where) {
            $l = $line.Trim()
            if ($l -and (Test-Path $l)) { return $l }
        }
    }
    return $null
}

function Get-WingetPath {
    $w = Get-Command winget -ErrorAction SilentlyContinue
    if ($w) { return $w.Source }
    return $null
}

function Install-PythonWinget {
    $exe = Get-WingetPath
    if (-not $exe) { return $false }
    Write-Log '[Auto] Instalando Python 3.12 con winget...'
    $p = Start-Process -FilePath $exe -ArgumentList @(
        'install', '-e', '--id', 'Python.Python.3.12',
        '--accept-package-agreements', '--accept-source-agreements', '--disable-interactivity'
    ) -Wait -PassThru -NoNewWindow
    return ($p.ExitCode -eq 0)
}

$PythonFtpVersions = @('3.12.8', '3.12.7', '3.12.6', '3.11.9')

function Install-PythonDownload {
    foreach ($ver in $PythonFtpVersions) {
        $url = "https://www.python.org/ftp/python/$ver/python-$ver-amd64.exe"
        $dst = Join-Path $env:TEMP "python-$ver-amd64.exe"
        Write-Log "[Auto] Descargando Python $ver..."
        try {
            Invoke-WebRequest -Uri $url -OutFile $dst -UseBasicParsing -MaximumRedirection 5
        } catch {
            Write-Log "Fallo URL $url : $_"
            continue
        }
        if (-not (Test-Path $dst) -or ((Get-Item $dst).Length -lt 5MB)) {
            Write-Log 'Archivo descargado invalido, probando otra version...'
            Remove-Item $dst -Force -ErrorAction SilentlyContinue
            continue
        }
        Write-Log '[Auto] Instalador Python (silencioso, usuario actual, PATH usuario)...'
        $arg = @(
            '/quiet', 'InstallAllUsers=0', 'PrependPath=1',
            'Include_test=0', 'Include_doc=0', 'Include_dev=0'
        )
        $proc = Start-Process -FilePath $dst -ArgumentList $arg -Wait -PassThru
        Remove-Item $dst -Force -ErrorAction SilentlyContinue
        $code = $proc.ExitCode
        if ($code -eq 0 -or $code -eq 3010) {
            Update-EnvPath
            Start-Sleep -Seconds 3
            return $true
        }
        Write-Log "Instalador Python codigo salida: $code"
    }
    return $false
}

function Install-TesseractWinget {
    $exe = Get-WingetPath
    if (-not $exe) { return $false }
    Write-Log '[Auto] Instalando Tesseract con winget...'
    $p = Start-Process -FilePath $exe -ArgumentList @(
        'install', '-e', '--id', 'UB-Mannheim.TesseractOCR',
        '--accept-package-agreements', '--accept-source-agreements', '--disable-interactivity'
    ) -Wait -PassThru -NoNewWindow
    return ($p.ExitCode -eq 0)
}

$TesseractDownloadUrl = 'https://github.com/UB-Mannheim/tesseract/releases/download/v5.4.0.20240606/tesseract-ocr-w64-setup-5.4.0.20240606.exe'

function Install-TesseractDownload {
    $dst = Join-Path $env:TEMP 'tesseract-ocr-w64-setup.exe'
    Write-Log '[Auto] Descargando Tesseract (UB-Mannheim)...'
    try {
        Invoke-WebRequest -Uri $TesseractDownloadUrl -OutFile $dst -UseBasicParsing -MaximumRedirection 5
    } catch {
        Write-Log "Fallo descarga: $_"
        return $false
    }
    if (-not (Test-Path $dst) -or ((Get-Item $dst).Length -lt 5MB)) {
        Write-Log 'Descarga Tesseract invalida.'
        return $false
    }
    Write-Log "[Auto] Ejecutando instalador Tesseract en carpeta local: $LocalTessDir"
    if (-not (Test-Path $LocalTessDir)) { New-Item -ItemType Directory -Path $LocalTessDir -Force | Out-Null }
    
    foreach ($argset in @(
            @('/VERYSILENT', '/NORESTART', "/DIR=$LocalTessDir"),
            @('/SILENT', '/NORESTART', "/DIR=$LocalTessDir"),
            @('/S', "/D=$LocalTessDir")
        )) {
        $null = Start-Process -FilePath $dst -ArgumentList $argset -Wait -PassThru
        Update-EnvPath
        Start-Sleep -Seconds 3
        if (Get-TesseractPath) {
            Remove-Item $dst -Force -ErrorAction SilentlyContinue
            return $true
        }
    }
    Remove-Item $dst -Force -ErrorAction SilentlyContinue
    return $false
}

$LocalTessDir = Join-Path $ScriptDir 'bin\tesseract'

Write-Log '--- Inicio install_prereqs.ps1 ---'

if (-not $SkipPython) {
    Update-EnvPath
    $py = Get-PythonCommand
    if (-not $py) {
        Write-Log 'Python 3.10+ no encontrado. Instalando...'
        $done = $false
        if (Get-WingetPath) { $done = Install-PythonWinget }
        if (-not $done) {
            Write-Log 'Usando descarga desde python.org (sin winget o winget fallo)...'
            $done = Install-PythonDownload
        }
        Update-EnvPath
        $py = Get-PythonCommand
        if (-not $py) {
            Write-Log 'ERROR: No hay Python 3.10+ tras instalar. Revisa red y permisos.'
            exit 1
        }
    }
    Write-Log "Python OK: $py"
    if (-not (Test-Path (Join-Path $ScriptDir 'python_cmd.local.txt'))) {
        Save-PythonLocal $py | Out-Null
    }
}

if (-not $SkipTesseract) {
    Update-EnvPath
    $ts = Get-TesseractPath
    if (-not $ts) {
        Write-Log 'Tesseract no encontrado. Instalando...'
        $done = $false
        if (Get-WingetPath) {
            $done = Install-TesseractWinget
            if ($done) {
                Write-Log 'Esperando que la instalacion de Tesseract se complete...'
                Start-Sleep -Seconds 10
                Update-EnvPath
                $ts = Get-TesseractPath
            }
        }
        if (-not $ts) {
            Write-Log 'Descargando e instalando Tesseract (respaldo)...'
            $null = Install-TesseractDownload
            Update-EnvPath
            $ts = Get-TesseractPath
        }
        if (-not $ts) {
            Write-Log 'Busqueda exhaustiva en el sistema...'
            $searchDirs = @(
                'C:\Program Files\Tesseract-OCR',
                'C:\Program Files (x86)\Tesseract-OCR',
                "$env:LOCALAPPDATA\Tesseract-OCR",
                "$env:ProgramFiles\Tesseract-OCR",
                "${env:ProgramFiles(x86)}\Tesseract-OCR"
            )
            foreach ($dir in $searchDirs) {
                if (Test-Path $dir) {
                    $found = Get-ChildItem -Path $dir -Filter 'tesseract.exe' -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
                    if ($found) {
                        $ts = $found.FullName
                        break
                    }
                }
            }
        }
        if (-not $ts) {
            Write-Log 'Busqueda exhaustiva en el sistema...'
            $searchDirs = @(
                'C:\Program Files\Tesseract-OCR',
                'C:\Program Files (x86)\Tesseract-OCR',
                "$env:LOCALAPPDATA\Tesseract-OCR",
                "$env:ProgramFiles\Tesseract-OCR",
                "${env:ProgramFiles(x86)}\Tesseract-OCR"
            )
            foreach ($dir in $searchDirs) {
                if (Test-Path $dir) {
                    $found = Get-ChildItem -Path $dir -Filter 'tesseract.exe' -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
                    if ($found) {
                        $ts = $found.FullName
                        break
                    }
                }
            }
        }
        if (-not $ts) {
            Write-Log ''
            Write-Log '============================================================'
            Write-Log '  No se pudo detectar Tesseract automaticamente.'
            Write-Log '  Instala Tesseract manualmente y luego ingresa la ruta'
            Write-Log '  del ejecutable tesseract.exe cuando se te solicite.'
            Write-Log '============================================================'
            Write-Log ''
            while (-not $ts) {
                $inputPath = Read-Host 'Ingresa la ruta completa de tesseract.exe (o "salir" para cancelar)'
                $inputPath = $inputPath.Trim().Trim('"')
                if ($inputPath -eq 'salir') { exit 1 }
                if (-not $inputPath) {
                    Write-Log 'La ruta no puede estar vacia. Intenta de nuevo.'
                    continue
                }
                if (Test-Path $inputPath) {
                    if ((Split-Path $inputPath -Leaf) -eq 'tesseract.exe') {
                        $ts = $inputPath
                        Write-Log "Ruta aceptada: $ts"
                    } else {
                        Write-Log 'El archivo debe llamarse tesseract.exe. Intenta de nuevo.'
                    }
                } else {
                    Write-Log 'Archivo no encontrado. Verifica la ruta e intenta de nuevo.'
                }
            }
        }
    }
    Write-Log "Tesseract OK: $ts"
    Save-TesseractLocal $ts | Out-Null
}

Write-Log 'Prerrequisitos listos.'
exit 0
