# install.ps1 - Instalador del host nativo YT Downloader
# Usa el wrapper BAT para evitar problemas con WindowsApps Python

Write-Host ""
Write-Host "  YT Downloader ✦ -- Instalador Host Nativo" -ForegroundColor Magenta
Write-Host "  ===========================================" -ForegroundColor DarkMagenta
Write-Host ""

# ── 1. Encontrar Python real desde el registro ────────────────────────────────
Write-Host "[1/4] Buscando Python..." -ForegroundColor Cyan
$pythonExe = $null

$regPaths = @(
    "HKCU:\Software\Python\PythonCore\*\InstallPath",
    "HKLM:\Software\Python\PythonCore\*\InstallPath",
    "HKLM:\Software\Wow6432Node\Python\PythonCore\*\InstallPath"
);
foreach ($regPath in $regPaths) {
    if ($pythonExe) { break }
    try {
        foreach ($entry in @(Get-ItemProperty $regPath -ErrorAction Stop)) {
            $exe = $entry.ExecutablePath
            if ($exe -and (Test-Path $exe) -and (Get-Item $exe -ErrorAction SilentlyContinue).Length -gt 1000) {
                $pythonExe = $exe
                Write-Host "  OK (registro): $pythonExe" -ForegroundColor Green
                break
            }
        }
    } catch {}
}

if (-not $pythonExe) {
    $candidates = @(
        "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "C:\Python313\python.exe", "C:\Python312\python.exe"
    );
    foreach ($c in $candidates) {
        if (Test-Path $c) { $pythonExe = $c; Write-Host "  OK (fallback): $c" -ForegroundColor Green; break }
    }
}

if (-not $pythonExe) {
    Write-Host "  ERROR: Python no encontrado. Instala desde https://python.org" -ForegroundColor Red
    Read-Host "Pulsa Enter para salir"; exit 1
}

# ── 2. Instalar dependencias ─────────────────────────────────────────────────
Write-Host ""
Write-Host "[2/4] Instalando dependencias (yt-dlp)..." -ForegroundColor Cyan
& $pythonExe -m pip install --quiet --upgrade yt-dlp
if ($LASTEXITCODE -eq 0) { Write-Host "  OK." -ForegroundColor Green }
else { Write-Host "  AVISO: pip fallo." -ForegroundColor Yellow }

# ── 3. Preservar Extension ID del JSON actual ────────────────────────────────
Write-Host ""
Write-Host "[3/4] Configurando manifest..." -ForegroundColor Cyan

$hostDir    = $PSScriptRoot
$wrapperPath = Join-Path $hostDir 'run_host.bat'
$jsonPath   = Join-Path $hostDir 'com.ytdownloader.host.json'

$existingId = "PLACEHOLDER_EXTENSION_ID"
if (Test-Path $jsonPath) {
    $raw = Get-Content $jsonPath -Raw -ErrorAction SilentlyContinue
    if ($raw -match 'chrome-extension://([a-z0-9]{32})/') {
        $existingId = $Matches[1]
        Write-Host "  Extension ID preservado: $existingId" -ForegroundColor Green
    } else {
        Write-Host "  Extension ID pendiente de configurar." -ForegroundColor Yellow
    }
}

# ── 4. Escribir manifest y registrar ────────────────────────────────────────
Write-Host ""
Write-Host "[4/4] Finalizando instalación..." -ForegroundColor Cyan

# Escribir manifest usando el wrapper BAT
$manifestData = @{
    name = "com.ytdownloader.host"
    description = "YT Downloader native messaging host - yt-dlp bridge"
    path = $wrapperPath
    type = "stdio"
    allowed_origins = @("chrome-extension://${existingId}/")
}
$manifestData | ConvertTo-Json -Depth 10 | Set-Content -Path $jsonPath -Encoding UTF8

Write-Host "  Manifest escrito correctamente." -ForegroundColor Green

# Registrar en Chrome y Edge
reg add "HKCU:\Software\Google\Chrome\NativeMessagingHosts\com.ytdownloader.host" `
    /ve /t REG_SZ /d $jsonPath /f | Out-Null
reg add "HKCU:\Software\Microsoft\Edge\NativeMessagingHosts\com.ytdownloader.host" `
    /ve /t REG_SZ /d $jsonPath /f | Out-Null
Write-Host "  Registro actualizado para Chrome y Edge." -ForegroundColor Green

# ── Resultado final ─────────────────────────────────────────────────────────
Write-Host ""
if ($existingId -eq "PLACEHOLDER_EXTENSION_ID") {
    Write-Host "  ⚠️ PENDIENTE: configura el Extension ID." -ForegroundColor Yellow
    Write-Host "  1. Abre chrome://extensions y copia el ID de la extensión (32 caracteres)"
    Write-Host "  2. Edita el archivo com.ytdownloader.host.json"
    Write-Host "  3. Reemplaza PLACEHOLDER_EXTENSION_ID por tu ID real"
    Write-Host "  4. Vuelve a ejecutar install_host.bat"
} else {
    Write-Host "  ✦ ¡INSTALACIÓN COMPLETA! ✦" -ForegroundColor Green
    Write-Host "  Extension ID: $existingId"
    Write-Host ""
    Write-Host "  Ahora recarga la extensión en chrome://extensions y ¡ya puedes usarla!"
}

Write-Host ""
Write-Host "Archivo manifest final:" -ForegroundColor DarkGray
Get-Content $jsonPath
Write-Host ""
