#Requires -Version 5.1
<#
.SYNOPSIS
  Port availability helpers for dev launcher (Windows).
#>

function Test-PortFree {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Port
    )

    $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($connections) {
        return $false
    }

    $hosts = @(
        [System.Net.IPAddress]::Loopback,
        [System.Net.IPAddress]::IPv6Loopback
    )

    foreach ($hostAddr in $hosts) {
        $listener = $null
        try {
            $listener = [System.Net.Sockets.TcpListener]::new($hostAddr, $Port)
            $listener.Start()
        }
        catch {
            return $false
        }
        finally {
            if ($null -ne $listener) {
                try { $listener.Stop() } catch { }
            }
        }
    }

    return $true
}

function Get-PortProcessInfo {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Port
    )

    $rows = [System.Collections.Generic.List[object]]::new()
    $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if (-not $connections) {
        return @()
    }

    foreach ($conn in @($connections)) {
        $processId = [int]$conn.OwningProcess
        if ($processId -le 0) { continue }

        $proc = Get-Process -Id $processId -ErrorAction SilentlyContinue
        $processName = "?"
        $processPath = ""

        if ($null -ne $proc) {
            $processName = [string]$proc.ProcessName
            try {
                if ($proc.Path) {
                    $processPath = [string]$proc.Path
                }
            }
            catch {
                $processPath = ""
            }
        }

        $rows.Add([PSCustomObject]@{
                Port        = $Port
                PID         = $processId
                ProcessName = $processName
                Path        = $processPath
            })
    }

    return $rows.ToArray()
}

function Get-OccupiedPortsInRange {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Start,
        [Parameter(Mandatory = $true)]
        [int]$End
    )

    if ($Start -gt $End) {
        throw "Invalid port range: $Start..$End"
    }

    $rows = [System.Collections.Generic.List[object]]::new()
    $seen = @{}

    for ($port = $Start; $port -le $End; $port++) {
        if (Test-PortFree -Port $port) {
            continue
        }

        foreach ($info in (Get-PortProcessInfo -Port $port)) {
            $key = "{0}:{1}" -f $info.Port, $info.PID
            if ($seen.ContainsKey($key)) { continue }
            $seen[$key] = $true
            $rows.Add($info)
        }
    }

    return $rows.ToArray()
}

function Write-PortRangeDiagnostics {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Start,
        [Parameter(Mandatory = $true)]
        [int]$End,
        [string]$Label = "port"
    )

    $occupied = Get-OccupiedPortsInRange -Start $Start -End $End
    if (-not $occupied -or $occupied.Count -eq 0) {
        Write-Host "  (net slushateley v diapazone ${Start}-${End}; bind nedostupen - prover'te firewall ili rezervaciyu portov)"
        return
    }

    $occupied |
        Sort-Object Port, PID |
        Format-Table -AutoSize Port, PID, ProcessName, Path |
        Out-String -Width 200 |
        ForEach-Object { Write-Host $_ }
}

function Write-PortUnavailableHelp {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ServiceLabel,
        [Parameter(Mandatory = $true)]
        [int]$Start,
        [Parameter(Mandatory = $true)]
        [int]$End
    )

    Write-Host ""
    Write-Host "Не найден свободный $ServiceLabel порт в диапазоне ${Start}-${End}." -ForegroundColor Red
    Write-Host ""
    Write-Host "Занятые порты в этом диапазоне ($ServiceLabel):"
    Write-PortRangeDiagnostics -Start $Start -End $End -Label $ServiceLabel
    Write-Host "Что делать:" -ForegroundColor Yellow
    Write-Host "  1. Попробуйте .\scripts\stop_dev.ps1 (останавливает только процессы, запущенные start_dev.ps1)."
    Write-Host "  2. Или закройте процессы из таблицы вручную (Диспетчер задач / taskkill по PID)."
    Write-Host "  3. Или укажите другой диапазон, например:"
    Write-Host "     .\scripts\start_dev.ps1 -BackendPortStart 8060 -BackendPortEnd 8090 -FrontendPortStart 3060 -FrontendPortEnd 3090"
    Write-Host ""
    Write-Host "Чужие процессы скрипт не останавливает автоматически." -ForegroundColor DarkYellow
}

function Find-FreePort {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Start,
        [Parameter(Mandatory = $true)]
        [int]$End
    )

    if ($Start -gt $End) {
        throw "Invalid port range: $Start..$End"
    }

    for ($port = $Start; $port -le $End; $port++) {
        if (Test-PortFree -Port $port) {
            return $port
        }
    }

    return $null
}

function Build-DevCorsOrigins {
    param(
        [int]$Start = 3000,
        [int]$End = 3050
    )

    $origins = [System.Collections.Generic.List[string]]::new()
    for ($port = $Start; $port -le $End; $port++) {
        $origins.Add("http://localhost:$port")
        $origins.Add("http://127.0.0.1:$port")
    }
    return ($origins -join ",")
}

function Test-CorsPreflight {
    param(
        [string]$BackendUrl,
        [string]$Origin,
        [int]$TimeoutSec = 8
    )

    try {
        $response = Invoke-WebRequest `
            -Uri "$BackendUrl/api/v1/projects" `
            -Method Options `
            -Headers @{
                Origin                         = $Origin
                "Access-Control-Request-Method" = "POST"
            } `
            -UseBasicParsing `
            -TimeoutSec $TimeoutSec
        return @{
            Ok           = $true
            Status       = [int]$response.StatusCode
            AllowOrigin  = [string]$response.Headers["Access-Control-Allow-Origin"]
            Error        = ""
        }
    }
    catch {
        $status = 0
        $allowOrigin = ""
        if ($null -ne $_.Exception.Response) {
            try { $status = [int]$_.Exception.Response.StatusCode.value__ } catch { }
            try { $allowOrigin = [string]$_.Exception.Response.Headers["Access-Control-Allow-Origin"] } catch { }
        }
        return @{
            Ok           = $false
            Status       = $status
            AllowOrigin  = $allowOrigin
            Error        = $_.Exception.Message
        }
    }
}

function Test-ProcessRunning {
    param(
        [Parameter(Mandatory = $true)]
        [int]$ProcessId
    )

    if ($ProcessId -le 0) { return $false }
    return $null -ne (Get-Process -Id $ProcessId -ErrorAction SilentlyContinue)
}

function Wait-HttpReady {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Url,
        [int]$TimeoutSec = 60,
        [int]$IntervalSec = 2
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5 -Method Get
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                return @{
                    Ok     = $true
                    Status = [int]$response.StatusCode
                    Error  = ""
                }
            }
        }
        catch {
            $status = 0
            if ($null -ne $_.Exception.Response) {
                try { $status = [int]$_.Exception.Response.StatusCode.value__ } catch { }
            }
            if ($status -ge 200 -and $status -lt 500) {
                return @{
                    Ok     = $true
                    Status = $status
                    Error  = ""
                }
            }
        }

        Start-Sleep -Seconds $IntervalSec
    }

    return @{
        Ok     = $false
        Status = 0
        Error  = "timeout after ${TimeoutSec}s"
    }
}
