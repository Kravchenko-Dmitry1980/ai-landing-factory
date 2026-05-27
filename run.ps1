#Requires -Version 5.1
<#
.SYNOPSIS
  One-command setup and dev start for AI Landing Factory.

.EXAMPLE
  .\run.ps1

.EXAMPLE
  .\run.ps1 -SkipInstall

.EXAMPLE
  .\run.ps1 -Clean

.EXAMPLE
  .\run.ps1 -Advanced

.EXAMPLE
  .\run.ps1 -Help
#>
[CmdletBinding()]
param(
    [switch]$Clean,
    [switch]$SkipInstall,
    [switch]$Advanced,
    [switch]$Help
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Clear-ProxyEnv {
    $env:NO_PROXY = "*"
    $env:no_proxy = "*"
    $env:PIP_NO_PROXY = "*"

    Remove-Item Env:HTTP_PROXY -ErrorAction SilentlyContinue
    Remove-Item Env:HTTPS_PROXY -ErrorAction SilentlyContinue
    Remove-Item Env:ALL_PROXY -ErrorAction SilentlyContinue
    Remove-Item Env:http_proxy -ErrorAction SilentlyContinue
    Remove-Item Env:https_proxy -ErrorAction SilentlyContinue
    Remove-Item Env:all_proxy -ErrorAction SilentlyContinue
}

function Invoke-PipSafe {
    param(
        [Parameter(Mandatory = $true)]
        [string[]] $PipArgs
    )

    Clear-ProxyEnv

    & $PythonExe -m pip @PipArgs

    if ($LASTEXITCODE -ne 0) {
        Write-Host "pip command failed." -ForegroundColor Red
        Write-Host "Possible cause: Windows system proxy/SOCKS settings." -ForegroundColor Yellow
        Write-Host "run.ps1 clears proxy env, but pip may still see system proxy." -ForegroundColor Yellow
        Write-Host "Try disabling system proxy/VPN temporarily or run:" -ForegroundColor Yellow
        Write-Host '$env:NO_PROXY="*"; $env:PIP_NO_PROXY="*"' -ForegroundColor Yellow
        exit $LASTEXITCODE
    }
}

function Write-Info([string]$Message) {
    Write-Host $Message
}

function Write-Err([string]$Message) {
    Write-Host $Message -ForegroundColor Red
}

function Show-Help {
    Write-Info "AI Landing Factory - run.ps1"
    Write-Info ""
    Write-Info "Usage:"
    Write-Info "  .\run.ps1              Setup (if needed) and start dev servers"
    Write-Info "  .\run.ps1 -SkipInstall Start without pip/npm install"
    Write-Info "  .\run.ps1 -Clean       Stop dev and clear .runtime, then start"
    Write-Info "  .\run.ps1 -Advanced    Print advanced mode instructions (does not edit .env)"
    Write-Info "  .\run.ps1 -Help        Show this help"
    Write-Info ""
    Write-Info "Default product mode: simple (OCR/VLM off)."
    Write-Info "Stop dev: .\scripts\stop_dev.ps1"
}

if ($Help) {
    Show-Help
    exit 0
}

Clear-ProxyEnv

$RootDir = $PSScriptRoot
$BackendDir = Join-Path $RootDir "backend"
$FrontendDir = Join-Path $RootDir "frontend"
$VenvDir = Join-Path $RootDir ".venv"
$PythonExe = Join-Path $VenvDir "Scripts\python.exe"
$EnvPath = Join-Path $BackendDir ".env"
$EnvExample = Join-Path $BackendDir ".env.example"
$StartDev = Join-Path $RootDir "scripts\start_dev.ps1"
$StopDev = Join-Path $RootDir "scripts\stop_dev.ps1"
$RuntimeDir = Join-Path $RootDir ".runtime"
$PortsFile = Join-Path $RuntimeDir "ports.json"

Write-Info "AI Landing Factory - one-command run"
Write-Info "Root: $RootDir"
Write-Info ""

if ($Advanced) {
    Write-Info "Advanced mode is optional and not enabled by default."
    Write-Info "To enable manually, edit backend\.env:"
    Write-Info "  PRODUCT_MODE=advanced"
    Write-Info "  OCR_ENABLED=true"
    Write-Info "  VLM_ENABLED=true"
    Write-Info "  ADVANCED_VISUAL_PIPELINE=true"
    Write-Info "  ENABLE_ADVANCED_DIAGNOSTICS=true"
    Write-Info ""
    Write-Info "OCR runtime setup (developer only):"
    Write-Info "  .\scripts\setup_ocr_runtime.ps1 -InstallBasic"
    Write-Info ""
    exit 0
}

$pyCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pyCmd) {
    $pyCmd = Get-Command py -ErrorAction SilentlyContinue
}
if (-not $pyCmd) {
    Write-Err "Python not found. Install Python 3.12+ and add to PATH."
    exit 1
}

$npmCmd = Get-Command npm.cmd -ErrorAction SilentlyContinue
if (-not $npmCmd) {
    Write-Err "npm not found. Install Node.js 20+ and add to PATH."
    exit 1
}

if ($Clean) {
    if (Test-Path $StopDev) {
        Write-Info "Stopping previous dev session..."
        & $StopDev
    }
    if (Test-Path $RuntimeDir) {
        Write-Info "Clearing .runtime..."
        Remove-Item -Path $RuntimeDir -Recurse -Force -ErrorAction SilentlyContinue
    }
    Write-Info ""
}

Clear-ProxyEnv

if (-not (Test-Path $VenvDir)) {
    Write-Info "Creating virtual environment..."
    if ($pyCmd.Name -eq "py") {
        & py -3.12 -m venv $VenvDir
    }
    else {
        & python -m venv $VenvDir
    }
}

if (-not (Test-Path $PythonExe)) {
    Write-Err "venv Python missing: $PythonExe"
    exit 1
}

if (-not $SkipInstall) {
    Write-Info "Checking Python proxy settings..."
    $proxyOutput = & $PythonExe -c "import os, urllib.request; os.environ['NO_PROXY']='*'; print(urllib.request.getproxies())" 2>&1
    Write-Info $proxyOutput
    if ($proxyOutput -match 'socks|http|https') {
        Write-Host "Warning: Python reports system proxy settings (SOCKS/HTTP)." -ForegroundColor Yellow
        Write-Host "Continuing with cleared env vars and direct PyPI index." -ForegroundColor Yellow
    }

    Clear-ProxyEnv
    Write-Info "Upgrading pip..."
    Invoke-PipSafe @("install", "--upgrade", "pip", "--no-cache-dir", "-i", "https://pypi.org/simple")

    Clear-ProxyEnv
    Write-Info "Installing backend requirements..."
    Invoke-PipSafe @("install", "-r", "backend\requirements.txt", "--no-cache-dir", "-i", "https://pypi.org/simple")

    $nodeModules = Join-Path $FrontendDir "node_modules"
    if (-not (Test-Path $nodeModules)) {
        Write-Info "Installing frontend dependencies..."
        Push-Location $FrontendDir
        try {
            & npm.cmd install
            if ($LASTEXITCODE -ne 0) {
                Write-Err "npm install failed."
                exit 1
            }
        }
        finally {
            Pop-Location
        }
    }
    else {
        Write-Info "Frontend node_modules present - skip npm install."
    }
}

if (-not (Test-Path $EnvPath)) {
    if (-not (Test-Path $EnvExample)) {
        Write-Err "Missing backend\.env.example"
        exit 1
    }
    Write-Info "Creating backend\.env from .env.example..."
    Copy-Item -Path $EnvExample -Destination $EnvPath
}

# Ensure simple product defaults when keys are absent (do not overwrite existing .env).
$envLines = @()
if (Test-Path $EnvPath) {
    $envLines = Get-Content -Path $EnvPath -Encoding UTF8
}
$existingKeys = @{}
foreach ($line in $envLines) {
    $t = $line.Trim()
    if (-not $t -or $t.StartsWith("#") -or $t -notmatch "=") { continue }
    $existingKeys[$t.Split("=", 2)[0].Trim()] = $true
}
$simpleDefaults = [ordered]@{
    PRODUCT_MODE                   = "simple"
    OCR_ENABLED                    = "false"
    VLM_ENABLED                    = "false"
    ADVANCED_VISUAL_PIPELINE       = "false"
    ENABLE_ADVANCED_DIAGNOSTICS    = "false"
    CHECK_ADVANCED                 = "false"
}
$appended = @()
foreach ($key in $simpleDefaults.Keys) {
    if (-not $existingKeys.ContainsKey($key)) {
        $appended += "$key=$($simpleDefaults[$key])"
    }
}
if ($appended.Count -gt 0) {
    $block = @("", "# Product simple mode (Stage P.1)") + $appended
    Add-Content -Path $EnvPath -Value ($block -join "`n") -Encoding UTF8
    Write-Info "Appended product mode defaults to backend\.env"
}

Clear-ProxyEnv

Write-Info ""
Write-Info "Starting dev servers..."
& $StartDev
$startCode = $LASTEXITCODE
if ($startCode -ne 0) {
    exit $startCode
}

$frontendUrl = "http://localhost:3000"
$backendUrl = "http://127.0.0.1:8001"
$editorUrl = $frontendUrl

if (Test-Path $PortsFile) {
    try {
        $ports = Get-Content -Path $PortsFile -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($ports.frontend_url) { $frontendUrl = [string]$ports.frontend_url }
        if ($ports.backend_url) { $backendUrl = [string]$ports.backend_url }
        $editorUrl = $frontendUrl
    }
    catch {
        Write-Info "Could not read ports file - using default URLs."
    }
}

Write-Info ""
Write-Info "=================================================="
Write-Info "AI Landing Factory is ready"
Write-Info "=================================================="
Write-Info "Frontend:  $frontendUrl"
Write-Info "Backend:   $backendUrl"
Write-Info "Editor:    $editorUrl"
Write-Info ""
Write-Info "Upload PPTX/DOCX/TXT/PDF, edit sections, export HTML."
Write-Info ""
Write-Info "Stop:"
Write-Info "  .\scripts\stop_dev.ps1"
Write-Info ""
Write-Info "Simple QA:"
Write-Info "  .\scripts\smoke_simple_product.ps1"
Write-Info "  .\scripts\uat_fresh_clone_check.ps1"
Write-Info "  .\scripts\check_all.ps1 -Simple"

exit 0
