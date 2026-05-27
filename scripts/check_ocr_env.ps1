#Requires -Version 5.1
<#
.SYNOPSIS
  Check OCR runtime environment for AI Landing Factory.

.EXAMPLE
  .\scripts\check_ocr_env.ps1

.EXAMPLE
  .\scripts\check_ocr_env.ps1 -RequireOcr

.EXAMPLE
  .\scripts\check_ocr_env.ps1 -Json -TestImage

.EXAMPLE
  .\scripts\check_ocr_env.ps1 -TestPptx "path\deck.pptx" -Slides 25
#>
[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$RequireOcr,
    [switch]$TestImage,
    [string]$TestPptx = "",
    [string]$Slides = ""
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

$argsList = @("$BackendDir\scripts\check_ocr_env.py")
if ($Json) { $argsList += "--json" }
if ($RequireOcr) { $argsList += "--require-ocr" }
if ($TestImage) { $argsList += "--test-image" }
if ($TestPptx) { $argsList += @("--test-pptx", $TestPptx) }
if ($Slides) { $argsList += @("--slides", $Slides) }

Push-Location $BackendDir
try {
    & $PythonExe @argsList
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
