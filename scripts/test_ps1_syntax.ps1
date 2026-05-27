#Requires -Version 5.1
<#
.SYNOPSIS
  Parse-check PowerShell entry scripts (no execution).
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$scripts = @(
    (Join-Path $RootDir "run.ps1"),
    (Join-Path $RootDir "scripts\smoke_simple_product.ps1"),
    (Join-Path $RootDir "scripts\check_all.ps1"),
    (Join-Path $RootDir "scripts\start_dev.ps1")
)

$failed = 0
foreach ($path in $scripts) {
    if (-not (Test-Path $path)) {
        Write-Host "MISSING: $path"
        $failed++
        continue
    }
    $tokens = $null
    $errors = $null
    $null = [System.Management.Automation.Language.Parser]::ParseFile(
        $path,
        [ref]$tokens,
        [ref]$errors
    )
    if ($errors -and $errors.Count -gt 0) {
        Write-Host "FAIL: $path"
        foreach ($err in $errors) {
            Write-Host "  $($err.Message)"
        }
        $failed++
    }
    else {
        Write-Host "OK: $path"
    }
}

$checkAllPath = Join-Path $RootDir "scripts\check_all.ps1"
if (Test-Path $checkAllPath) {
    $checkAllText = Get-Content -Path $checkAllPath -Raw -Encoding UTF8
    $contractChecks = @(
        @{ Name = "check_all defines -Simple switch"; Pattern = '\[switch\]\$Simple' },
        @{ Name = "Simple skips OCR smoke by default"; Pattern = '\$RunOcrSmoke = \$false' },
        @{ Name = "Simple skips VLM contract smoke"; Pattern = '\$SkipVlmContractSmoke = \$true' },
        @{ Name = "University export uses offline smoke"; Pattern = 'scripts\\smoke_university_export\.py", "--offline"' }
    )
    foreach ($check in $contractChecks) {
        if ($checkAllText -match $check.Pattern) {
            Write-Host ("OK: {0}" -f $check.Name)
        }
        else {
            Write-Host ("FAIL: {0}" -f $check.Name)
            $failed++
        }
    }
}

if ($failed -gt 0) {
    exit 1
}
Write-Host "PS1 syntax: PASS"
exit 0
