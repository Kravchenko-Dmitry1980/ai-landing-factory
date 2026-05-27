#Requires -Version 5.1
<#
.SYNOPSIS
  HTTP smoke for frontend (no Playwright).
#>
[CmdletBinding()]
param(
    [string]$FrontendUrl = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$PortsFile = Join-Path $RootDir ".runtime\ports.json"

if (-not $FrontendUrl) {
    $FrontendUrl = "http://localhost:3000"
    if (Test-Path $PortsFile) {
        try {
            $ports = Get-Content -Path $PortsFile -Raw -Encoding UTF8 | ConvertFrom-Json
            if ($ports.frontend_url) {
                $FrontendUrl = [string]$ports.frontend_url
            }
        }
        catch { }
    }
}

function Test-UrlStatus {
    param(
        [string]$Url,
        [string]$Label
    )
    try {
        $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 30
        if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 400) {
            Write-Host "OK: $Label HTTP $($resp.StatusCode) $Url"
            return $true
        }
        Write-Host "FAIL: $Label HTTP $($resp.StatusCode) $Url" -ForegroundColor Red
        return $false
    }
    catch {
        Write-Host "FAIL: $Label $Url - $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

$ok = $true
if (-not (Test-UrlStatus -Url $FrontendUrl -Label "frontend root")) {
    $ok = $false
}

# Routes may redirect or return shell HTML — 200/3xx acceptable for smoke.
$editorUrl = ($FrontendUrl.TrimEnd("/")) + "/editor"
if (-not (Test-UrlStatus -Url $editorUrl -Label "frontend /editor")) {
    Write-Host "WARN: /editor not reachable (may need project id in app router)" -ForegroundColor Yellow
}

$previewUrl = ($FrontendUrl.TrimEnd("/")) + "/preview"
if (-not (Test-UrlStatus -Url $previewUrl -Label "frontend /preview")) {
    Write-Host "WARN: /preview not reachable" -ForegroundColor Yellow
}

if (-not $ok) { exit 1 }
exit 0
