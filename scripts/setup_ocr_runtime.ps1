#Requires -Version 5.1
<#
.SYNOPSIS
  Setup OCR runtime dependencies for AI Landing Factory.

.EXAMPLE
  .\scripts\setup_ocr_runtime.ps1

.EXAMPLE
  .\scripts\setup_ocr_runtime.ps1 -WriteEnv

.EXAMPLE
  .\scripts\setup_ocr_runtime.ps1 -InstallBasic -InstallPaddle

.EXAMPLE
  .\scripts\setup_ocr_runtime.ps1 -All
#>
[CmdletBinding()]
param(
    [switch]$InstallBasic,
    [switch]$InstallPaddle,
    [switch]$InstallTesseractPython,
    [switch]$InstallEasyOCR,
    [switch]$InstallSurya,
    [switch]$WriteEnv,
    [switch]$All
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
$PythonExe = Join-Path $RootDir ".venv\Scripts\python.exe"

if (-not (Test-Path $PythonExe)) {
    Write-Error "Python venv not found: $PythonExe"
    exit 1
}

$argsList = @("$BackendDir\scripts\setup_ocr_runtime.py")
if ($InstallBasic) { $argsList += "--install-basic" }
if ($InstallPaddle) { $argsList += "--install-paddle" }
if ($InstallTesseractPython) { $argsList += "--install-tesseract-python" }
if ($InstallEasyOCR) { $argsList += "--install-easyocr" }
if ($InstallSurya) { $argsList += "--install-surya" }
if ($WriteEnv) { $argsList += "--write-env" }
if ($All) { $argsList += "--all" }

Push-Location $BackendDir
try {
    & $PythonExe @argsList
    $code = $LASTEXITCODE
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "Next step:"
Write-Host "  .\scripts\check_ocr_env.ps1"
Write-Host ""
Write-Host "If PaddleOCR init OK but inference fails, try env flags before re-check:"
Write-Host '  $env:FLAGS_use_mkldnn="0"'
Write-Host '  $env:FLAGS_enable_pir_api="0"'
Write-Host "  cd backend"
Write-Host "  ..\.venv\Scripts\python.exe scripts\warmup_ocr_models.py --engine paddleocr"
Write-Host ""
Write-Host "Or install Tesseract OCR for Windows as fallback."
Write-Host ""
Write-Host "Benchmark OCR engines:"
Write-Host "  cd backend"
Write-Host "  ..\.venv\Scripts\python.exe scripts\benchmark_ocr_engines.py --file path\to\deck.pptx --slides 25"

exit $code
