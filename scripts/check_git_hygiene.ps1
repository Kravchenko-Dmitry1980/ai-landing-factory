#Requires -Version 5.1
<#
.SYNOPSIS
  Git hygiene checks for release (no logs, binaries, secrets in index).

.EXAMPLE
  .\scripts\check_git_hygiene.ps1
#>
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Push-Location $RootDir
try {
    $failed = $false

    function Fail-Check([string]$Message, [string[]]$Files) {
        script:failed = $true
        Write-Host "FAIL: $Message" -ForegroundColor Red
        foreach ($f in $Files) {
            Write-Host "  $f"
        }
    }

    Write-Host "== Git hygiene ==" -ForegroundColor Cyan

    $logsTracked = @(git ls-files logs 2>$null)
    if ($logsTracked.Count -gt 0) {
        Fail-Check "logs/ must not be tracked" $logsTracked
    }
    else {
        Write-Host "OK: no logs tracked"
    }

    $binaryCorpus = @(git ls-files test_corpus | Where-Object { $_ -match '\.(pptx|ppt|docx|doc|pdf|xlsx|xls|zip)$' })
    if ($binaryCorpus.Count -gt 0) {
        Fail-Check "binary originals must not be in test_corpus index" $binaryCorpus
    }
    else {
        Write-Host "OK: no binary test_corpus originals tracked"
    }

    $envTracked = @(git ls-files | Where-Object { $_ -match '(^|/)\.env($|\.)' -and $_ -notmatch '\.example$' })
    if ($envTracked.Count -gt 0) {
        Fail-Check ".env files must not be tracked" $envTracked
    }
    else {
        Write-Host "OK: no .env tracked"
    }

    $vendorTracked = @(git ls-files | Where-Object { $_ -match '(^|/)\.venv/|(^|/)node_modules/' })
    if ($vendorTracked.Count -gt 0) {
        Fail-Check ".venv/node_modules must not be tracked" $vendorTracked
    }
    else {
        Write-Host "OK: no .venv/node_modules tracked"
    }

    $backendData = @(git ls-files backend/data)
    if ($backendData.Count -gt 0) {
        Fail-Check "backend/data must not be tracked (runtime only)" $backendData
    }
    else {
        Write-Host "OK: no backend/data tracked"
    }

    Write-Host ""
    if ($failed) {
        Write-Host "GIT HYGIENE: FAIL" -ForegroundColor Red
        exit 1
    }
    Write-Host "GIT HYGIENE: PASS" -ForegroundColor Green
    exit 0
}
finally {
    Pop-Location
}
