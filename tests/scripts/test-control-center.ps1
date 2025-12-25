#!/usr/bin/env pwsh
# Quick Test Script - Start backend and open Control Center

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  Control Center - Quick Test" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Stop any existing Python processes
Write-Host "Cleaning up existing processes..." -ForegroundColor Yellow
Stop-Process -Name python -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Start backend services
Write-Host "Starting backend services..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -NoProfile -Command `"cd '$PSScriptRoot'; python run_local.py`"" -WindowStyle Minimized

# Wait for services to start
Write-Host "Waiting for services to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 8

# Check if services are running
$running = $false
$attempts = 0
$maxAttempts = 10

Write-Host "Checking service health..." -ForegroundColor Yellow
while (-not $running -and $attempts -lt $maxAttempts) {
    try {
        $null = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction Stop
        $running = $true
        Write-Host "Backend is ready!" -ForegroundColor Green
    } catch {
        $attempts++
        Write-Host "." -NoNewline -ForegroundColor Yellow
        Start-Sleep -Seconds 1
    }
}

Write-Host ""
Write-Host ""

if ($running) {
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host "  Services Running Successfully!" -ForegroundColor Green
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Backend Services:" -ForegroundColor Cyan
    Write-Host "  Gateway API:        http://localhost:8000" -ForegroundColor White
    Write-Host "  Chat Orchestrator:  http://localhost:8002" -ForegroundColor White
    Write-Host "  Ingestion Service:  http://localhost:8001" -ForegroundColor White
    Write-Host "  Voice Orchestrator: http://localhost:8004" -ForegroundColor White
    Write-Host ""
    # Start static frontend server (port 3000)
    $frontendPort = 3000
    Write-Host "Starting frontend server on http://localhost:$frontendPort ..." -ForegroundColor Cyan
    Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -NoProfile -Command `"cd '$PSScriptRoot'; python -m http.server $frontendPort`"" -WindowStyle Minimized

    # Give server moment to start
    Start-Sleep -Seconds 2

    Write-Host "Opening Control Center in browser..." -ForegroundColor Cyan
    Write-Host ""

    $controlCenterUrl = "http://localhost:$frontendPort/clients/admin-console/control-center.html"
    Start-Process $controlCenterUrl
    
    Write-Host "Control Center opened!" -ForegroundColor Green
    Write-Host ""
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host "  What to Test:" -ForegroundColor Yellow
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1. Dashboard - View real-time stats" -ForegroundColor White
    Write-Host "2. Analytics - Check metrics and charts" -ForegroundColor White
    Write-Host "3. Voice & Calling - View Twilio integration" -ForegroundColor White
    Write-Host "4. Integrations - See all connected services" -ForegroundColor White
    Write-Host "5. Click sidebar items to navigate" -ForegroundColor White
    Write-Host ""
    Write-Host "Press F12 in browser to see console logs" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "To stop backend: " -NoNewline -ForegroundColor Yellow
    Write-Host '.\stop.ps1' -ForegroundColor Cyan
    Write-Host "To stop frontend server: close the extra PowerShell window labeled 'python -m http.server'" -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "=========================================" -ForegroundColor Red
    Write-Host "  Failed to Start Services" -ForegroundColor Red
    Write-Host "=========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "  1. Check if Python is installed: python --version" -ForegroundColor White
    Write-Host "  2. Check if dependencies are installed" -ForegroundColor White
    Write-Host "  3. Look for errors in the terminal" -ForegroundColor White
    Write-Host ""
    Write-Host "You can still open Control Center manually:" -ForegroundColor Cyan
    Write-Host "  clients\admin-console\control-center.html" -ForegroundColor Yellow
    Write-Host ""
}
