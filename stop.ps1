#!/usr/bin/env pwsh
# Copilot Platform Stop Script
# This script stops all running microservices

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  Copilot Platform - Stopping..." -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Stop processes recorded from last start
$processFile = Join-Path $PSScriptRoot ".platform-processes.json"
$stopped = 0

if (Test-Path $processFile) {
    try {
        $processInfo = Get-Content $processFile -Encoding UTF8 | ConvertFrom-Json -ErrorAction Stop
        foreach ($entryName in 'backend','frontend') {
            $entry = $processInfo.$entryName
            if ($entry -and $entry.pid) {
                $processId = [int]$entry.pid
                $proc = Get-Process -Id $processId -ErrorAction SilentlyContinue
                if ($proc) {
                    Write-Host "   Stopping $entryName process (PID $processId)..." -ForegroundColor Gray
                    Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
                    $stopped++
                }
            }
        }
    } catch {
    Write-Host "[WARN] Could not read process file: $_" -ForegroundColor Yellow
    }

    Remove-Item $processFile -ErrorAction SilentlyContinue
}

# Stop individual service processes tracked by run_local.py
$servicePidFile = Join-Path $PSScriptRoot ".service-pids.json"
if (Test-Path $servicePidFile) {
    try {
        $serviceInfo = Get-Content $servicePidFile -Encoding UTF8 | ConvertFrom-Json -ErrorAction Stop
        $serviceList = @()
        if ($serviceInfo -and $serviceInfo.services) {
            $serviceList = $serviceInfo.services
        } elseif ($serviceInfo -is [System.Collections.IEnumerable]) {
            $serviceList = $serviceInfo
        }

        foreach ($service in $serviceList) {
            if ($service -and $service.pid) {
                $serviceId = [int]$service.pid
                $proc = Get-Process -Id $serviceId -ErrorAction SilentlyContinue
                if ($proc) {
                    $serviceName = if ($service.name) { $service.name } else { "service" }
                    Write-Host "   Stopping $serviceName (PID $serviceId)..." -ForegroundColor Gray
                    Stop-Process -Id $serviceId -Force -ErrorAction SilentlyContinue
                    $stopped++
                }
            }
        }
    } catch {
        Write-Host "[WARN] Could not read service pid file: $_" -ForegroundColor Yellow
    }

    Remove-Item $servicePidFile -ErrorAction SilentlyContinue
}

# Additional sweep for any lingering python processes from platform
$pythonProcesses = @()
try {
    $pythonProcesses = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" -ErrorAction SilentlyContinue | Where-Object {
        $cmdLine = $_.CommandLine
        $cmdLine -and (
            $cmdLine -like "*uvicorn*" -or
            $cmdLine -like "*run_local.py*" -or
            $cmdLine -like "*services*chat-orchestrator*" -or
            $cmdLine -like "*services*gateway-api*" -or
            $cmdLine -like "*services*ingestion-indexer*" -or
            $cmdLine -like "*services*voice-orchestrator*" -or
            $cmdLine -like "*services*email-responder*worker.py*" -or
            $cmdLine -like "*http.server*3000*"
        )
    }
} catch {
    Write-Host "[WARN] Could not enumerate python processes via CIM: $_" -ForegroundColor Yellow
}

if ($pythonProcesses) {
    Write-Host "Stopping services..." -ForegroundColor Yellow
    Write-Host ""
    
    foreach ($process in $pythonProcesses) {
        try {
            $processId = [int]$process.ProcessId
            if (-not $processId) { continue }
            Write-Host "   Stopping process $processId..." -ForegroundColor Gray
            Stop-Process -Id $processId -Force -ErrorAction Stop
            $stopped++
        } catch {
            Write-Host "   [WARN] Could not stop process $($process.ProcessId)" -ForegroundColor Yellow
        }
    }

    Start-Sleep -Seconds 2
}

if ($stopped -gt 0) {
    Write-Host ""
    Write-Host "Stopped $stopped process(es)" -ForegroundColor Green
    Write-Host ""
    Write-Host "Hint: To start again, run: " -NoNewline -ForegroundColor Yellow
    Write-Host ".\start.ps1" -ForegroundColor Cyan
    Write-Host ""
} else {
    Write-Host "No running services found." -ForegroundColor Blue
    Write-Host ""
    Write-Host "Hint: To start the platform, run: " -NoNewline -ForegroundColor Yellow
    Write-Host ".\start.ps1" -ForegroundColor Cyan
    Write-Host ""
}
