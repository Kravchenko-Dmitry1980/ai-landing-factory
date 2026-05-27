#Requires -Version 5.1
<#
.SYNOPSIS
  Friendly one-command dev launcher with auto port selection.

.EXAMPLE
  .\scripts\start_dev.ps1

.EXAMPLE
  .\scripts\start_dev.ps1 -BackendPortStart 8001 -BackendPortEnd 8050 -FrontendPortStart 3000 -FrontendPortEnd 3050
#>
[CmdletBinding()]
param(
    [int]$BackendPortStart = 8001,
    [int]$BackendPortEnd = 8050,
    [int]$FrontendPortStart = 3000,
    [int]$FrontendPortEnd = 3050
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
}
catch { }

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$BackendDir = Join-Path $RootDir "backend"
$FrontendDir = Join-Path $RootDir "frontend"
$RuntimeDir = Join-Path $RootDir ".runtime"
$LogDir = Join-Path $RootDir "logs\dev"
$PortsFile = Join-Path $RuntimeDir "ports.json"
$ProcessesFile = Join-Path $RuntimeDir "dev_processes.json"
$UvicornExe = Join-Path $RootDir ".venv\Scripts\uvicorn.exe"
$BackendMain = Join-Path $BackendDir "app\main.py"
$EnvLocalPath = Join-Path $FrontendDir ".env.local"

. (Join-Path $PSScriptRoot "lib\ports.ps1")

function Write-Info([string]$Message) {
    Write-Host $Message
}

function Write-Fail([string]$Message) {
    Write-Host $Message -ForegroundColor Red
}

function Ensure-Directories {
    New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null
    New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
}

function Test-Prerequisites {
    if (-not (Test-Path $BackendDir)) {
        Write-Fail "Не найдена папка backend: $BackendDir"
        exit 1
    }

    if (-not (Test-Path $BackendMain)) {
        Write-Fail "Не найден backend/app/main.py"
        exit 1
    }

    if (-not (Test-Path $FrontendDir)) {
        Write-Fail "Не найдена папка frontend: $FrontendDir"
        exit 1
    }

    if (-not (Test-Path $UvicornExe)) {
        Write-Fail @"
Не найдено виртуальное окружение .venv.
Сначала выполните:
python -m venv .venv
.\.venv\Scripts\pip.exe install -r backend\requirements.txt
"@
        exit 1
    }

    $npmCmd = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if (-not $npmCmd) {
        Write-Fail "npm не найден в PATH. Установите Node.js 20+."
        exit 1
    }
}

function Write-FrontendEnvLocal {
    param(
        [int]$BackendPort
    )

    $content = "NEXT_PUBLIC_API_URL=http://127.0.0.1:$BackendPort/api/v1`n"
    Set-Content -Path $EnvLocalPath -Value $content -Encoding UTF8 -NoNewline
}

function Write-JsonFileNoBom {
    param(
        [string]$Path,
        [string]$Json
    )
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($Path, $Json, $utf8NoBom)
}

function Write-PortsJson {
    param(
        [int]$BackendPort,
        [int]$FrontendPort,
        [string]$CorsOrigins,
        [int]$BackendPortStart = 8001,
        [int]$BackendPortEnd = 8050,
        [int]$FrontendPortStart = 3000,
        [int]$FrontendPortEnd = 3050
    )

    $payload = [ordered]@{
        backend_port        = $BackendPort
        frontend_port       = $FrontendPort
        backend_port_start  = $BackendPortStart
        backend_port_end    = $BackendPortEnd
        frontend_port_start = $FrontendPortStart
        frontend_port_end   = $FrontendPortEnd
        backend_url         = "http://127.0.0.1:$BackendPort"
        frontend_url        = "http://localhost:$FrontendPort"
        cors_origins        = $CorsOrigins
        updated_at          = (Get-Date).ToString("o")
    }

    Write-JsonFileNoBom -Path $PortsFile -Json ($payload | ConvertTo-Json)
}

function Write-ProcessesJson {
    param(
        [int]$BackendPid,
        [int]$FrontendPid,
        [string]$BackendUrl,
        [string]$FrontendUrl
    )

    $payload = [ordered]@{
        backend_pid  = $BackendPid
        frontend_pid = $FrontendPid
        backend_url  = $BackendUrl
        frontend_url = $FrontendUrl
        created_at   = (Get-Date).ToString("o")
    }

    Write-JsonFileNoBom -Path $ProcessesFile -Json ($payload | ConvertTo-Json)
}

function Test-ProcessStarted {
    param(
        [System.Diagnostics.Process]$Process,
        [string]$LogPath,
        [string]$Label
    )

    Start-Sleep -Seconds 2

    if ($Process.HasExited) {
        Write-Fail "$Label failed to start (exit code $($Process.ExitCode))."
        Write-Fail "Log: $LogPath"
        exit 1
    }

    if (-not (Test-ProcessRunning -ProcessId $Process.Id)) {
        Write-Fail "$Label failed to start (PID $($Process.Id) not found)."
        Write-Fail "Log: $LogPath"
        exit 1
    }
}

# --- Main ---
Write-Info "AI Landing Factory - dev launcher"
Write-Info "Root: $RootDir"
Write-Info ""

Ensure-Directories
Test-Prerequisites

if ($BackendPortStart -gt $BackendPortEnd) {
    Write-Fail "BackendPortStart ($BackendPortStart) must be <= BackendPortEnd ($BackendPortEnd)."
    exit 1
}
if ($FrontendPortStart -gt $FrontendPortEnd) {
    Write-Fail "FrontendPortStart ($FrontendPortStart) must be <= FrontendPortEnd ($FrontendPortEnd)."
    exit 1
}

Write-Info "Port ranges: backend ${BackendPortStart}-${BackendPortEnd}, frontend ${FrontendPortStart}-${FrontendPortEnd}"
Write-Info ""

$backendPort = Find-FreePort -Start $BackendPortStart -End $BackendPortEnd
if ($null -eq $backendPort) {
    Write-PortUnavailableHelp -ServiceLabel "backend" -Start $BackendPortStart -End $BackendPortEnd
    exit 1
}

$frontendPort = Find-FreePort -Start $FrontendPortStart -End $FrontendPortEnd
if ($null -eq $frontendPort) {
    Write-PortUnavailableHelp -ServiceLabel "frontend" -Start $FrontendPortStart -End $FrontendPortEnd
    exit 1
}

$backendUrl = "http://127.0.0.1:$backendPort"
$frontendUrl = "http://localhost:$frontendPort"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backendLog = Join-Path $LogDir "backend_$timestamp.log"
$backendLogErr = Join-Path $LogDir "backend_$timestamp.err.log"
$frontendLog = Join-Path $LogDir "frontend_$timestamp.log"
$frontendLogErr = Join-Path $LogDir "frontend_$timestamp.err.log"

Write-Info "Backend:  $backendUrl"
Write-Info "Frontend: $frontendUrl"
Write-Info ""

Write-FrontendEnvLocal -BackendPort $backendPort

$corsOrigins = Build-DevCorsOrigins -Start $FrontendPortStart -End $FrontendPortEnd
Write-PortsJson -BackendPort $backendPort -FrontendPort $frontendPort -CorsOrigins $corsOrigins `
    -BackendPortStart $BackendPortStart -BackendPortEnd $BackendPortEnd `
    -FrontendPortStart $FrontendPortStart -FrontendPortEnd $FrontendPortEnd

$npmExe = (Get-Command npm.cmd).Source

Write-Info "CORS:     synced for localhost/127.0.0.1 ports $FrontendPortStart-$FrontendPortEnd"
Write-Info "          active frontend origin: http://localhost:$frontendPort"
Write-Info ""

Write-Info "Starting backend..."
$previousCorsEnv = $env:BACKEND_CORS_ORIGINS
$env:BACKEND_CORS_ORIGINS = $corsOrigins
try {
    $backendProc = Start-Process `
        -FilePath $UvicornExe `
        -ArgumentList @(
            "app.main:app",
            "--reload",
            "--host", "127.0.0.1",
            "--port", "$backendPort"
        ) `
        -WorkingDirectory $BackendDir `
        -RedirectStandardOutput $backendLog `
        -RedirectStandardError $backendLogErr `
        -PassThru `
        -WindowStyle Hidden
}
finally {
    if ($null -ne $previousCorsEnv) {
        $env:BACKEND_CORS_ORIGINS = $previousCorsEnv
    }
    else {
        Remove-Item Env:BACKEND_CORS_ORIGINS -ErrorAction SilentlyContinue
    }
}

Test-ProcessStarted -Process $backendProc -LogPath $backendLog -Label "Backend"

Write-Info "Starting frontend..."
$frontendProc = Start-Process `
    -FilePath $npmExe `
    -ArgumentList @("run", "dev:port", "--", "--port", "$frontendPort") `
    -WorkingDirectory $FrontendDir `
    -RedirectStandardOutput $frontendLog `
    -RedirectStandardError $frontendLogErr `
    -PassThru `
    -WindowStyle Hidden

Test-ProcessStarted -Process $frontendProc -LogPath $frontendLog -Label "Frontend"

Write-ProcessesJson `
    -BackendPid $backendProc.Id `
    -FrontendPid $frontendProc.Id `
    -BackendUrl $backendUrl `
    -FrontendUrl $frontendUrl

Write-Info ""
Write-Info "Waiting for backend health (timeout 60s)..."
$backendHealthUrl = "$backendUrl/api/v1/projects/privacy"
$backendHealth = Wait-HttpReady -Url $backendHealthUrl -TimeoutSec 60

if (-not $backendHealth.Ok) {
    Write-Fail "Backend health FAIL: $backendHealthUrl"
    Write-Fail "Лог: $backendLog"
    exit 1
}

Write-Info "Backend health OK (HTTP $($backendHealth.Status))"

$corsProbe = Test-CorsPreflight -BackendUrl $backendUrl -Origin $frontendUrl
if ($corsProbe.Ok -and $corsProbe.AllowOrigin -eq $frontendUrl) {
    Write-Info "CORS preflight OK for $frontendUrl"
}
else {
    Write-Fail "CORS preflight FAIL for origin $frontendUrl (HTTP $($corsProbe.Status))"
    if ($corsProbe.Error) { Write-Fail "  $($corsProbe.Error)" }
    Write-Fail "Лог backend: $backendLog"
    exit 1
}

Write-Info "Waiting for frontend health (timeout 60s)..."
$frontendHealth = Wait-HttpReady -Url $frontendUrl -TimeoutSec 60

if (-not $frontendHealth.Ok) {
    Write-Fail "Frontend health FAIL: $frontendUrl"
    Write-Fail "Лог: $frontendLog"
    exit 1
}

Write-Info "Frontend health OK (HTTP $($frontendHealth.Status))"
Write-Info ""
Write-Info "AI Landing Factory is running."
Write-Info ""
Write-Info "Frontend:"
Write-Info $frontendUrl
Write-Info ""
Write-Info "Backend:"
Write-Info $backendUrl
Write-Info ""
Write-Info "Откройте:"
Write-Info $frontendUrl
Write-Info ""
Write-Info "QA:"
Write-Info ".\scripts\check_all.ps1"
Write-Info ""
Write-Info "Logs:"
Write-Info "  Backend:  $backendLog"
Write-Info "  Frontend: $frontendLog"
Write-Info "  Ports:    $PortsFile"

exit 0
