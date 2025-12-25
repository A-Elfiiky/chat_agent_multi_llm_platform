#!/usr/bin/env pwsh
# Copilot Platform Status Script
# This script checks the status of all services

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  Copilot Platform - Status Check" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check each service
$services = @(
    @{Name="Gateway API"; Port=8000; URL="http://localhost:8000/health"},
    @{Name="Ingestion Service"; Port=8001; URL="http://localhost:8001/health"},
    @{Name="Chat Orchestrator"; Port=8002; URL="http://localhost:8002/health"},
    @{Name="Voice Orchestrator"; Port=8004; URL="http://localhost:8004/health"}
)

$allRunning = $true

foreach ($service in $services) {
    Write-Host "$($service.Name) (Port $($service.Port)): " -NoNewline
    
    try {
        $response = Invoke-RestMethod -Uri $service.URL -TimeoutSec 2 -ErrorAction Stop
        Write-Host "✅ Running" -ForegroundColor Green
    } catch {
        Write-Host "❌ Stopped" -ForegroundColor Red
        $allRunning = $false
    }
}

# Check for Email Worker process
Write-Host "Email Worker: " -NoNewline
$emailWorker = Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -like "*email-responder*worker.py*"}
if ($emailWorker) {
    Write-Host "✅ Running" -ForegroundColor Green
} else {
    Write-Host "❌ Stopped" -ForegroundColor Red
    $allRunning = $false
}

Write-Host ""

if ($allRunning) {
    Write-Host "🎉 All services are operational!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Quick Links:" -ForegroundColor Cyan
    Write-Host "  • API Docs: " -NoNewline; Write-Host "http://localhost:8000/docs" -ForegroundColor Blue
    Write-Host "  • Web Chat: " -NoNewline; Write-Host "clients/web-widget/index.html" -ForegroundColor Blue
    Write-Host "  • Admin Console: " -NoNewline; Write-Host "clients/admin-console/index.html" -ForegroundColor Blue
    Write-Host ""
} else {
    Write-Host "⚠️  Some services are not running." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "💡 To start all services, run: " -NoNewline -ForegroundColor Yellow
    Write-Host ".\start.ps1" -ForegroundColor Cyan
    Write-Host ""
}

# Show Python processes
$pythonCount = (Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*uvicorn*" -or 
    $_.CommandLine -like "*run_local.py*" -or 
    $_.CommandLine -like "*worker.py*"
}).Count

Write-Host "Active Python processes: $pythonCount" -ForegroundColor Gray
Write-Host ""
