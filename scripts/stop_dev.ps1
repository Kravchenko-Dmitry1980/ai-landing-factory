#Requires -Version 5.1
<#
.SYNOPSIS
  Stop dev processes started by start_dev.ps1 (saved PIDs only).

.EXAMPLE
  .\scripts\stop_dev.ps1
#>
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"

try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
}
catch { }

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$ProcessesFile = Join-Path $RootDir ".runtime\dev_processes.json"

function Stop-SavedProcess {
    param(
        [string]$Label,
        [int]$ProcessId
    )

    if ($ProcessId -le 0) {
        Write-Warning "$Label PID not recorded - skip."
        return
    }

    $proc = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if ($null -eq $proc) {
        Write-Warning "$Label PID $ProcessId already stopped."
        return
    }

    try {
        & taskkill.exe /PID $ProcessId /T /F | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Stopped $Label PID $ProcessId"
        }
        else {
            Stop-Process -Id $ProcessId -Force -ErrorAction Stop
            Write-Host "Stopped $Label PID $ProcessId"
        }
    }
    catch {
        Write-Warning "Could not stop $Label PID ${ProcessId}: $($_.Exception.Message)"
    }
}

if (-not (Test-Path $ProcessesFile)) {
    Write-Warning "No dev session found: $ProcessesFile"
    Write-Host "Nothing to stop."
    exit 0
}

try {
    $data = Get-Content -Path $ProcessesFile -Raw -Encoding UTF8 | ConvertFrom-Json
}
catch {
    Write-Warning "Could not read $ProcessesFile : $($_.Exception.Message)"
    exit 1
}

Write-Host "Stopping dev processes from $ProcessesFile"
Write-Host ""

Stop-SavedProcess -Label "backend" -ProcessId ([int]$data.backend_pid)
Stop-SavedProcess -Label "frontend" -ProcessId ([int]$data.frontend_pid)

Write-Host ""
Write-Host "Done."

exit 0
