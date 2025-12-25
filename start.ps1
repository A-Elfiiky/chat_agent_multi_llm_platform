#!/usr/bin/env pwsh
# Copilot Platform Startup Script
# This script starts all microservices in the background

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  Copilot Platform - Starting..." -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check if already running
$existingBackend = Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -like "*scripts*run_local.py*"}
$existingFrontend = Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -like "*http.server*3000*"}

$backendProcess = $null
$frontendProcess = $null

if ($existingBackend) {
    $backendProcess = $existingBackend | Select-Object -First 1
    Write-Host "Reusing existing backend process (PID $($backendProcess.Id))." -ForegroundColor Yellow
} else {
    Write-Host "Starting backend services..." -ForegroundColor Green
    Write-Host ""
    $pythonExe = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
    if (-not (Test-Path $pythonExe)) {
        $pythonExe = "python"
    }
    $backendProcess = Start-Process -FilePath $pythonExe -ArgumentList "scripts/run_local.py" -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -PassThru
}

if ($existingFrontend) {
    $frontendProcess = $existingFrontend | Select-Object -First 1
    Write-Host "Reusing existing frontend server (PID $($frontendProcess.Id))." -ForegroundColor Yellow
}

# Start the platform (if backend was fresh start, give it time)
if (-not $existingBackend) {
    Write-Host "Waiting for services to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 8
} else {
    Write-Host "Checking backend health..." -ForegroundColor Yellow
}

# Check if services are running
$running = $false
$attempts = 0
$maxAttempts = 10

while (-not $running -and $attempts -lt $maxAttempts) {
    try {
        $null = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction Stop
        $running = $true
    } catch {
        $attempts++
        Start-Sleep -Seconds 1
    }
}

if ($running) {
    # Ensure frontend static server running
    $frontendPort = 3000
    if (-not $frontendProcess) {
        Write-Host "Starting frontend server on http://localhost:$frontendPort ..." -ForegroundColor Cyan
        try {
            $frontendProcess = Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -NoProfile -Command `"cd '$PSScriptRoot'; python -m http.server $frontendPort`"" -WindowStyle Hidden -PassThru
            Start-Sleep -Seconds 2
        } catch {
            Write-Host "Failed to start frontend server: $_" -ForegroundColor Red
            if ($backendProcess -and !$backendProcess.HasExited -and -not $existingBackend) {
                Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
            }
            exit 1
        }
    }

    $backendPid = if ($backendProcess) { $backendProcess.Id } else { $null }
    $frontendPid = if ($frontendProcess) { $frontendProcess.Id } else { $null }
    $processInfo = [pscustomobject]@{
        backend  = if ($backendPid) { [pscustomobject]@{ pid = $backendPid; command = 'python run_local.py' } } else { $null }
        frontend = if ($frontendPid) { [pscustomobject]@{ pid = $frontendPid; command = "python -m http.server $frontendPort" } } else { $null }
        created  = (Get-Date).ToString('s')
    }
    $processFile = Join-Path $PSScriptRoot ".platform-processes.json"
    $processInfo | ConvertTo-Json | Set-Content -Path $processFile -Encoding UTF8

    Write-Host ""
    Write-Host "Platform is running!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Services:" -ForegroundColor Cyan
    Write-Host "  - Gateway API        -> http://localhost:8000" -ForegroundColor White
    Write-Host "  - Chat Orchestrator  -> http://localhost:8002" -ForegroundColor White
    Write-Host "  - Ingestion Service  -> http://localhost:8001" -ForegroundColor White
    Write-Host "  - Voice Orchestrator -> http://localhost:8004" -ForegroundColor White
    Write-Host "  - Email Worker       -> Running in background" -ForegroundColor White
    Write-Host ""
    Write-Host "Quick Access:" -ForegroundColor Cyan
    Write-Host "  - API Documentation  -> http://localhost:8000/docs" -ForegroundColor White
    Write-Host "  - Frontend Server    -> http://localhost:3000" -ForegroundColor White
    Write-Host "  - Control Center     -> http://localhost:3000/clients/admin-console/control-center.html" -ForegroundColor White
    Write-Host "  - Welcome Page       -> http://localhost:3000/index.html" -ForegroundColor White
    Write-Host "  - Web Chat Widget    -> http://localhost:3000/clients/web-widget/index.html" -ForegroundColor White
    Write-Host ""
    Write-Host "Hint: To stop the platform, run: " -NoNewline -ForegroundColor Yellow
    Write-Host ".\stop.ps1" -ForegroundColor Cyan
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "Failed to start services!" -ForegroundColor Red
    Write-Host "   Check the terminal for errors." -ForegroundColor Yellow
    Write-Host ""
    exit 1
}
